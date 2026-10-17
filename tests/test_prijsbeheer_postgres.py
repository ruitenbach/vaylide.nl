"""Gelijktijdige prijswijzigingen op een echte PostgreSQL-database (catalog/prijsbeheer.voer_door).

Slaat over zolang de database geen PostgreSQL is (SQLite kent geen rijvergrendeling, dus daar zegt een gelijktijdigheidstest niets).
Draai alleen op een geïsoleerde testdatabase, nooit op de productiedatabase:
    DATABASE_URL=postgres://gebruiker@127.0.0.1:5432/vaylide_test .venv/bin/python manage.py test tests.test_prijsbeheer_postgres
Django maakt zelf een aparte database 'test_<naam>' aan en ruimt die op.

Wat ze bewaken: N beheerders voeren tegelijk een wijziging door met dezelfde stempel: precies één slaagt, de rest krijgt de melding dat er intussen
iets is gewijzigd, en er is precies één logboekset bij; twee wijzigingen van verschillende cellen met een verse stempel lopen na elkaar goed;
een bestelling die tegelijk met een prijswijziging start, krijgt het oude of het nieuwe bedrag, nooit iets ertussenin."""
import threading
import unittest

from django.db import connection, connections
from django.test import TransactionTestCase, override_settings

from accounts.models import User
from catalog import prijsbeheer
from catalog.models import PriceChangeSet, PriceRule
from orders.models import Order, Payment
from orders.services import start_checkout

from .helpers import VaylideTestCase
from .test_prijsstructuur import vul


@unittest.skipUnless(connection.vendor == "postgresql", "Alleen zinvol op PostgreSQL")
@override_settings(PRICING_V2=True, PRICES_ADMIN=True)
class GelijktijdigePrijswijziging(TransactionTestCase):
    serialized_rollback = True

    def setUp(self):
        from beheer import rollen

        rollen.ensure_roles()
        if not PriceRule.objects.exists():     # zekerheid naast serialized_rollback: de startstand opnieuw neerzetten
            import importlib
            from django.apps import apps

            importlib.import_module("catalog.migrations.0008_prijsbeheer_startstand").vul(apps, None)
        self.eigenaar = User.objects.create_superuser(email="eigenaar@example.com", password="Een-lang-wachtwoord-2026")

    def parallel(self, taken):
        resultaten, drempel = [], threading.Barrier(len(taken))

        def werk(taak):
            try:
                drempel.wait(timeout=10)
                resultaten.append(("ok", taak()))
            except Exception as exc:    # noqa: BLE001 - we tellen de uitkomsten
                resultaten.append(("fout", exc))
            finally:
                connections.close_all()

        threads = [threading.Thread(target=werk, args=(t,)) for t in taken]
        [t.start() for t in threads]
        [t.join(30) for t in threads]
        return resultaten

    def test_vijf_gelijktijdige_wijzigingen_met_dezelfde_stempel_slagen_precies_een_keer(self):
        stempel = prijsbeheer.stempel()
        bedragen = [5495, 5395, 5295, 5195, 5095]
        taken = [lambda b=b: prijsbeheer.voer_door(self.eigenaar, {("bruiloft", "luxe"): b}, reden=f"Gelijktijdig {b}", stempel_in=stempel) for b in bedragen]
        uitkomst = self.parallel(taken)
        geslaagd = [u for u in uitkomst if u[0] == "ok"]
        mislukt = [u for u in uitkomst if u[0] == "fout"]
        self.assertEqual(len(geslaagd), 1, uitkomst)
        self.assertEqual(len(mislukt), 4)
        for _, exc in mislukt:
            self.assertIsInstance(exc, prijsbeheer.PrijsFout)
            self.assertIn("intussen", exc.fouten[""])
        self.assertEqual(PriceChangeSet.objects.exclude(kind="seed").count(), 1)
        self.assertEqual(PriceRule.objects.get(rij="bruiloft", tier="luxe").price_cents, geslaagd[0][1].changes.get().new_cents)

    def test_wijzigingen_van_verschillende_cellen_met_een_verse_stempel_gaan_na_elkaar_goed(self):
        prijsbeheer.voer_door(self.eigenaar, {("bruiloft", "luxe"): 5495}, reden="Een", stempel_in=prijsbeheer.stempel())
        prijsbeheer.voer_door(self.eigenaar, {("bruiloft", "basis"): 2795}, reden="Twee", stempel_in=prijsbeheer.stempel())
        self.assertEqual((prijsbeheer.lees("bruiloft", "luxe"), prijsbeheer.lees("bruiloft", "basis")), (5495, 2795))
        self.assertEqual(PriceChangeSet.objects.exclude(kind="seed").count(), 2)

    def test_een_bestelling_tegelijk_met_een_wijziging_krijgt_het_oude_of_het_nieuwe_bedrag(self):
        helper = VaylideTestCase("complete_content")
        klant = User.objects.create_user(email="klant@example.com")
        from invitations.services import create_draft, save_draft
        from catalog.models import Template

        inv = create_draft(occasion="bruiloft", template=Template.objects.get(slug="liefde-op-papier"), owner=klant)
        inv = vul(save_draft(inv, expected_rev=None, content=helper.complete_content(inv), user=klant), klant)
        stempel = prijsbeheer.stempel()
        taken = [
            lambda: prijsbeheer.voer_door(self.eigenaar, {("bruiloft", "luxe"): 5495}, reden="Tegelijk", stempel_in=stempel),
            lambda: start_checkout(inv, user=klant, package_code="", optional_codes=[], terms_accepted=True),
        ]
        uitkomst = self.parallel(taken)
        self.assertEqual([u[0] for u in uitkomst].count("ok"), 2, uitkomst)
        order = Order.objects.get()
        self.assertIn(order.total_cents, (5995, 5495))
        self.assertEqual(Payment.objects.get().amount_cents, order.total_cents)
        self.assertEqual(sum(l.total_cents for l in order.lines.all()), order.total_cents)

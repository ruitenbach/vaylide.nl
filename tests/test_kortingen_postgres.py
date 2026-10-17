"""Gelijktijdigheid bij kortingscodes met een gebruikslimiet, op een echte PostgreSQL-database.

Deze tests slaan over zolang de database geen PostgreSQL is (SQLite kent geen rijvergrendeling, dus daar zegt een gelijktijdigheidstest niets).
Draai ze alleen op een geïsoleerde testdatabase, nooit op de productiedatabase:
    DATABASE_URL=postgres://gebruiker@127.0.0.1:5432/vaylide_test .venv/bin/python manage.py test tests.test_kortingen_postgres
Django maakt zelf een aparte database 'test_<naam>' aan en ruimt die op.

Wat ze bewaken:
- een code met maximaal 1 gebruik en N klanten die tegelijk bestellen: precies één bestelling krijgt de korting, de rest een duidelijke melding;
- dezelfde klant met twee kaarten tegelijk en maximaal 1 gebruik per klant: één korting;
- een maximum van K bij N > K tegelijk: nooit meer dan K gereserveerd;
- een code en een aanbieding tegelijk (de aanbieding is voordeliger): de code wordt niet verbruikt;
- dubbele bevestiging van dezelfde betaling (webhook en terugkeer tegelijk) telt één keer."""
import threading
import unittest
from datetime import timedelta

from django.db import connection, connections
from django.test import TransactionTestCase, override_settings
from django.utils import timezone

from accounts.models import User
from catalog.models import Template
from invitations.services import create_draft, save_draft
from kortingen import services as k
from kortingen.models import DiscountCode, DiscountRedemption, Offer
from orders.models import Order, Payment
from orders.services import CheckoutError, start_checkout, sync_payment

from .helpers import VaylideTestCase, future_date

POSTGRES = connection.vendor == "postgresql"


@unittest.skipUnless(POSTGRES, "Alleen op PostgreSQL (zie de uitleg bovenaan dit bestand).")
class Gelijktijdig(TransactionTestCase):
    def setUp(self):
        o = override_settings(PRICING_V2=True, DISCOUNTS_ENABLED=True, OFFERS_ENABLED=True, TEST_MODE=True, PAYMENT_PROVIDER="test",
                              JOBS_RUN_INLINE=True, BASE_URL="https://vaylide.test")
        o.enable()
        self.addCleanup(o.disable)
        from catalog.seed import ensure_catalog

        ensure_catalog()    # een TransactionTestCase leegt de tabellen na elke test, dus de catalogus steeds opnieuw inlezen
        self.template = Template.objects.get(slug="liefde-op-papier")

    def klant_met_kaart(self, n, owner=None):
        user = owner or User.objects.create_user(email=f"klant{n}@example.com")
        if owner is None:
            user.email_verified_at = timezone.now()
            user.save()
        inv = create_draft(occasion="bruiloft", template=self.template, owner=user)
        content = VaylideTestCase.complete_content(self, inv)
        return user, save_draft(inv, expected_rev=None, content=content, user=user)

    def tegelijk(self, taken):
        """Start alle taken op hetzelfde moment (elk in een eigen thread met een eigen databaseverbinding). Geeft per taak 'ok' of de foutmelding."""
        poort = threading.Barrier(len(taken))
        uitkomst = [None] * len(taken)

        def werk(i, taak):
            try:
                poort.wait(timeout=20)
                uitkomst[i] = ("ok", taak())
            except CheckoutError as exc:
                uitkomst[i] = ("fout", str(exc))
            except Exception as exc:    # noqa: BLE001 - een onverwachte fout hoort in de uitkomst te komen, niet de test te laten hangen
                uitkomst[i] = ("crash", repr(exc))
            finally:
                connections.close_all()

        threads = [threading.Thread(target=werk, args=(i, t)) for i, t in enumerate(taken)]
        [t.start() for t in threads]
        [t.join(timeout=60) for t in threads]
        return uitkomst

    def bestel(self, user, inv, code):
        return lambda: start_checkout(inv, user=user, package_code="luxe", optional_codes=[], terms_accepted=True, delivery_consent=True,
                                      service_consent=True, discount_code=code)

    def test_laatste_plek_gaat_naar_precies_een_klant(self):
        code = DiscountCode.objects.create(code="LAATSTE", kind="percent", percent=10, max_redemptions=1)
        paren = [self.klant_met_kaart(i) for i in range(8)]
        uitkomst = self.tegelijk([self.bestel(u, i, "LAATSTE") for u, i in paren])
        self.assertEqual([u[0] for u in uitkomst].count("crash"), 0, uitkomst)
        self.assertEqual([u[0] for u in uitkomst].count("ok"), 1, uitkomst)
        for soort, tekst in uitkomst:
            if soort == "fout":
                self.assertIn("niet meer beschikbaar", tekst)
        self.assertEqual(k.active_redemptions(code), 1)
        self.assertEqual(DiscountRedemption.objects.filter(code=code).count(), 1)
        self.assertEqual(Order.objects.filter(discount_code=code).count(), 1)

    def test_maximum_van_drie_bij_acht_klanten_tegelijk(self):
        code = DiscountCode.objects.create(code="DRIE", kind="percent", percent=10, max_redemptions=3)
        paren = [self.klant_met_kaart(i) for i in range(8)]
        uitkomst = self.tegelijk([self.bestel(u, i, "DRIE") for u, i in paren])
        self.assertEqual([u[0] for u in uitkomst].count("crash"), 0, uitkomst)
        self.assertEqual([u[0] for u in uitkomst].count("ok"), 3, uitkomst)
        self.assertEqual(k.active_redemptions(code), 3)

    def test_een_klant_twee_kaarten_tegelijk_met_maximum_een_per_klant(self):
        code = DiscountCode.objects.create(code="EENKEER", kind="percent", percent=10, max_per_customer=1)
        user, inv1 = self.klant_met_kaart(0)
        _, inv2 = self.klant_met_kaart(1, owner=user)
        uitkomst = self.tegelijk([self.bestel(user, inv1, "EENKEER"), self.bestel(user, inv2, "EENKEER")])
        self.assertEqual([u[0] for u in uitkomst].count("crash"), 0, uitkomst)
        self.assertEqual([u[0] for u in uitkomst].count("ok"), 1, uitkomst)
        self.assertEqual(k.customer_uses(code, user), 1)

    def test_code_en_voordeligere_aanbieding_tegelijk_verbruikt_de_code_niet(self):
        now = timezone.now()
        Offer.objects.create(name="Groot", kind="percent", percent=40, starts_at=now - timedelta(days=1), ends_at=now + timedelta(days=5), whole_collection=True)
        code = DiscountCode.objects.create(code="KLEINER", kind="percent", percent=10, max_redemptions=1)
        paren = [self.klant_met_kaart(i) for i in range(5)]
        uitkomst = self.tegelijk([self.bestel(u, i, "KLEINER") for u, i in paren])
        self.assertEqual([u[0] for u in uitkomst].count("ok"), 5, uitkomst)
        self.assertEqual(DiscountRedemption.objects.filter(code=code).count(), 0)
        self.assertEqual(Order.objects.exclude(discount_offer=None).count(), 5)

    def test_dubbele_bevestiging_van_dezelfde_betaling_telt_een_keer(self):
        code = DiscountCode.objects.create(code="DUBBEL", kind="percent", percent=10, max_redemptions=1)
        user, inv = self.klant_met_kaart(0)
        payment = start_checkout(inv, user=user, package_code="luxe", optional_codes=[], terms_accepted=True, delivery_consent=True, service_consent=True,
                                 discount_code="DUBBEL")
        payment.test_remote_status = Payment.Status.PAID
        payment.save(update_fields=["test_remote_status"])
        uitkomst = self.tegelijk([lambda: sync_payment(payment, source="webhook"), lambda: sync_payment(payment, source="webhook"),
                                  lambda: sync_payment(payment, source="terugkeer")])
        self.assertEqual([u[0] for u in uitkomst].count("crash"), 0, uitkomst)
        red = DiscountRedemption.objects.get(code=code)
        self.assertEqual(red.state, DiscountRedemption.State.REDEEMED)
        self.assertEqual(Order.objects.get(pk=payment.order_id).status, Order.Status.PAID)
        self.assertEqual(k.active_redemptions(code), 1)


@unittest.skipUnless(POSTGRES, "Alleen op PostgreSQL (zie de uitleg bovenaan dit bestand).")
class TerugdraaiVeilig(VaylideTestCase):
    """Oudere code (zonder de kortingsvelden) moet nog bestellingen kunnen aanmaken in een database met de kortingsmigraties.

    De verplichte kolommen van orders_order die de kortingen toevoegen hebben daarom een standaardwaarde in de database zelf
    (migratie orders/0006). Zonder die waarde geeft een INSERT van oudere code een NOT NULL-fout."""

    def test_verplichte_kortingskolommen_hebben_databasestandaard(self):
        with connection.cursor() as cur:
            cur.execute(
                "select column_name, column_default from information_schema.columns "
                "where table_name = 'orders_order' and is_nullable = 'NO' and column_default is null "
                "and column_name in ('discount_cents', 'discount_code_text', 'discount_offer_text')"
            )
            zonder = [r[0] for r in cur.fetchall()]
        self.assertEqual(zonder, [])

    def test_insert_zonder_kortingsvelden_slaagt(self):
        klant = User.objects.create_user(email="terugdraai@example.test", password="x" * 12)
        with connection.cursor() as cur:
            cur.execute(
                "insert into orders_order (uid, number, kind, invitation_title, package_code, package_name, features, "
                "max_gallery_photos, availability_months, total_cents, currency, status, fulfilment_status, fulfilment_note, "
                "test_mode, created_at, updated_at, customer_id, delivery_consent_text, terms_version, service_consent_text) "
                "select gen_random_uuid(), 'OUD-1', 'invitation', '', '', '', '[]', 0, 0, 1995, 'EUR', 'pending', 'none', '', "
                "true, now(), now(), %s, '', '', ''",
                [klant.pk],
            )
        order = Order.objects.get(number="OUD-1")
        self.assertEqual((order.discount_cents, order.discount_code_text, order.discount_offer_text), (0, "", ""))

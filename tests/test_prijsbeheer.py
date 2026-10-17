"""Prijzenbeheer (catalog/prijsbeheer.py, Beheer → Prijzen en acties, settings.PRICES_ADMIN).

Wat deze tests bewaken:
- de startstand in de database is een exacte kopie van de 27 bedragen in de code, en de vlag staat standaard uit (dan geldt alleen de code);
- met de vlag aan komt elk bedrag uit de database en werkt een wijziging door in collectie, ontwerppagina, Studio, bestelling, betaling, Mollie-bedrag, bon en mail;
- een ontbrekend of ongeldig databasebedrag maakt de kaart niet bestelbaar (nooit een stille terugval op de code-prijs, nooit een bestelling);
- bestaande bestellingen en openstaande betalingen houden hun bedrag; wie midden in het bestellen zit, krijgt een melding;
- validatie, bevestiging, logboek en terugdraaien; verplichte reden; gelijktijdige wijzigingen;
- rechten (Eigenaar, Hoofdbeheerder, Beheerder, klant) aan de serverzijde, en bescherming van eigenaarsaccounts;
- het btw-tarief wordt op nieuwe bestellingen vastgelegd; kortingscodes rekenen over de nieuwe prijs; er wordt geen aanbieding geactiveerd."""
import importlib
import json
from io import StringIO
from unittest import mock

from django.contrib import admin
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.test import Client, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from accounts.models import User
from beheer import rollen
from catalog import prijsbeheer, prijzen
from catalog.models import PriceChange, PriceChangeSet, PriceRule, Template
from kortingen.models import DiscountCode, Offer, PriceStand
from orders.models import Order, OrderLine, Payment
from orders.pricing import PricingError, build_quote
from orders.services import PriceChanged, create_payment, start_checkout
from processing.models import OutboundEmail

from .helpers import VaylideTestCase
from .test_mollie_testmodus import FakeMollie, _Response
from .test_prijsstructuur import TABEL_EIGENAAR, vul

BRUILOFT_LUXE = ("bruiloft", "luxe")


class PrijsbeheerBasis(VaylideTestCase):
    """Prijsstructuur en prijsbeheer aan; elke test begint met de startstand uit de migratie (de testtransactie draait terug)."""

    beheer_aan = True

    def setUp(self):
        super().setUp()
        for opties in (dict(PRICING_V2=True, PRICES_ADMIN=self.beheer_aan),):
            o = override_settings(**opties)
            o.enable()
            self.addCleanup(o.disable)
        rollen.ensure_roles()
        self.eigenaar = self.make_staff("eigenaar@example.com")
        self.hoofd = self.maak_staff("hoofd@example.com", groep=rollen.HOOFDBEHEERDER)
        self.gewoon = self.maak_staff("gewoon@example.com")

    def maak_staff(self, email, groep=None):
        user = User.objects.create_user(email=email, password="Een-lang-wachtwoord-2026")
        user.is_staff = True
        user.save()
        if groep:
            user.groups.add(Group.objects.get(name=groep))
        return user

    def als(self, user):
        c = Client()
        c.force_login(user)
        return c

    def wijzig(self, wijzigingen, user=None, reden="Test"):
        """Een volledige wijziging via het logboek-pad van de service (zoals de bevestigingsstap dat doet)."""
        invoer = {cel: c for cel, c in wijzigingen.items()}
        return prijsbeheer.voer_door(user or self.eigenaar, invoer, reden=reden, stempel_in=prijsbeheer.stempel())


class StartstandEnVlag(VaylideTestCase):
    def test_de_vlag_staat_standaard_uit(self):
        self.assertFalse(importlib.import_module("config.settings").PRICES_ADMIN)

    def test_de_startstand_is_een_exacte_kopie_van_de_27_bedragen_in_de_code(self):
        self.assertEqual(PriceRule.objects.count(), 27)
        for rij, bedragen in prijzen.PRIJZEN.items():
            for tier, cents in zip(prijzen.TIERS, bedragen):
                self.assertEqual(PriceRule.objects.get(rij=rij, tier=tier).price_cents, cents, (rij, tier))
        self.assertEqual(prijsbeheer.verschillen_met_code(), [])

    def test_de_ingevroren_kopie_in_de_migratie_is_gelijk_aan_de_code_en_aan_de_tabel_van_de_eigenaar(self):
        migratie = importlib.import_module("catalog.migrations.0008_prijsbeheer_startstand")
        self.assertEqual(migratie.STARTSTAND, {k: tuple(v) for k, v in prijzen.PRIJZEN.items()})
        self.assertEqual(migratie.STARTSTAND, TABEL_EIGENAAR)

    def test_er_is_een_startstand_in_het_logboek(self):
        seed = PriceChangeSet.objects.get(kind="seed")
        self.assertEqual(seed.changes.count(), 27)
        self.assertTrue(all(c.old_cents is None for c in seed.changes.all()))

    def test_met_de_vlag_uit_geldt_alleen_de_code_ook_als_de_database_afwijkt(self):
        PriceRule.objects.filter(rij="bruiloft", tier="luxe").update(price_cents=5495)
        with override_settings(PRICING_V2=True, PRICES_ADMIN=False):
            t = Template.objects.get(slug="liefde-op-papier")
            self.assertEqual(prijzen.prijs_cents(t, "bruiloft"), 5995)
            self.assertFalse(prijsbeheer.enabled())

    def test_rollen_worden_aangemaakt_maar_aan_niemand_toegekend(self):
        rollen.ensure_roles()
        self.assertEqual(set(Group.objects.values_list("name", flat=True)) & {rollen.EIGENAAR, rollen.HOOFDBEHEERDER}, {rollen.EIGENAAR, rollen.HOOFDBEHEERDER})
        for g in Group.objects.filter(name__in=[rollen.EIGENAAR, rollen.HOOFDBEHEERDER]):
            self.assertEqual(g.user_set.count(), 0, g.name)

    def test_er_is_geen_aanbieding_geactiveerd(self):
        self.assertEqual(Offer.objects.count(), 0)
        self.assertFalse(importlib.import_module("config.settings").OFFERS_ENABLED)


class CentraleLeesfunctie(PrijsbeheerBasis):
    def test_database_en_code_geven_voor_elke_combinatie_hetzelfde_bedrag(self):
        verschillen = []
        with prijsbeheer.cache_scope():
            for t in Template.objects.filter(is_active=True):
                for occasion in t.occasions:
                    for soort in ("", "wenskaart"):
                        with override_settings(PRICES_ADMIN=False):
                            code = prijzen.prijs_cents(t, occasion, soort)
                        if code != prijzen.prijs_cents(t, occasion, soort):
                            verschillen.append((t.slug, occasion, soort))
        self.assertEqual(verschillen, [])

    def test_een_wijziging_werkt_door_in_alle_prijsfuncties(self):
        self.wijzig({BRUILOFT_LUXE: 5495})
        t = Template.objects.get(slug="liefde-op-papier")
        self.assertEqual(prijzen.prijs_cents(t, "bruiloft"), 5495)
        self.assertEqual(prijzen.prijs_info(t, "bruiloft")["display"], "€ 54,95")
        self.assertEqual(dict(prijzen.beschikbaar("bruiloft"))["luxe"], 5495)
        self.assertIn("€ 54,95", prijzen.zin("bruiloft"))
        self.assertEqual(build_quote({}, None, None, template_version=t.current_version, occasion="bruiloft").total_cents, 5495)

    def test_verloving_en_jubileum_gebruiken_dezelfde_prijsrij(self):
        t = Template.objects.get(slug="aurora-nocturne")
        self.assertEqual(prijzen.categorie("verloving"), prijzen.categorie("jubileum"))
        self.wijzig({("jubileum_verloving", "special"): 7500})
        self.assertEqual(prijzen.prijs_cents(t, "jubileum"), 7500)
        self.assertEqual(prijzen.prijs_cents(t, "verloving") if "verloving" in t.occasions else 7500, 7500)

    def test_een_ontbrekend_bedrag_maakt_de_kaart_niet_bestelbaar_zonder_terugval(self):
        PriceRule.objects.filter(rij="bruiloft", tier="luxe").delete()
        t = Template.objects.get(slug="liefde-op-papier")
        self.assertIsNone(prijzen.prijs_cents(t, "bruiloft"))
        self.assertIsNone(prijzen.prijs_info(t, "bruiloft"))
        with self.assertRaises(PricingError):
            build_quote({}, None, None, template_version=t.current_version, occasion="bruiloft")
        self.assertNotIn("luxe", dict(prijzen.beschikbaar("bruiloft")))
        self.assertTrue(prijsbeheer.problemen())

    def test_een_ongeldig_bedrag_wordt_nooit_gebruikt(self):
        t = Template.objects.get(slug="liefde-op-papier")
        for slecht in (0, 99, 50001, -5, "x", None, True, 59.95):
            with mock.patch.object(prijsbeheer, "regels", return_value={BRUILOFT_LUXE: slecht}):
                self.assertIsNone(prijsbeheer.lees("bruiloft", "luxe"), slecht)
                self.assertIsNone(prijzen.prijs_cents(t, "bruiloft"), slecht)

    def test_zonder_geldige_prijs_ontstaat_er_geen_bestelling_en_geen_betaling(self):
        owner = self.make_customer()
        inv = vul(self.make_invitation(owner=owner, template="liefde-op-papier", occasion="bruiloft"), owner)
        PriceRule.objects.filter(rij="bruiloft", tier="luxe").delete()
        with self.assertRaises(PricingError):
            start_checkout(inv, user=owner, package_code="", optional_codes=[], terms_accepted=True)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)

    def test_publieke_pagina_s_blijven_werken_bij_een_ontbrekend_bedrag(self):
        PriceRule.objects.filter(rij="bruiloft", tier="luxe").delete()
        c = Client()
        for url in ("/ontwerpen/", "/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft", "/prijzen/", "/"):
            self.assertEqual(c.get(url).status_code, 200, url)
        self.assertNotIn("Luxe € 59,95", c.get("/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft").content.decode())

    def test_de_prijstabel_wordt_hoogstens_een_keer_per_verzoek_gelezen(self):
        c = Client()
        for url in ("/ontwerpen/", "/prijzen/", "/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft"):
            with CaptureQueriesContext(connection) as q:
                c.get(url)
            lezen = [x for x in q.captured_queries if 'FROM "catalog_pricerule"' in x["sql"]]
            self.assertLessEqual(len(lezen), 1, url)

    def test_de_cache_blijft_niet_hangen_tussen_verzoeken(self):
        c = Client()
        self.assertIn("Luxe € 59,95", c.get("/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft").content.decode())
        self.wijzig({BRUILOFT_LUXE: 5495})
        html = c.get("/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft").content.decode()
        self.assertIn("Luxe € 54,95", html)
        self.assertNotIn("Luxe € 59,95", html)


class DoorwerkenEnBestellen(PrijsbeheerBasis):
    def test_een_nieuwe_prijs_staat_overal_gelijk_van_collectie_tot_bevestigingsmail(self):
        self.wijzig({BRUILOFT_LUXE: 5495})
        anon = Client()
        self.assertIn("Luxe € 54,95", anon.get("/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft").content.decode())
        self.assertIn("€ 54,95", anon.get("/prijzen/").content.decode())
        owner = self.make_customer()
        inv = vul(self.make_invitation(owner=owner, template="liefde-op-papier", occasion="bruiloft"), owner)
        c = self.als(owner)
        self.assertIn("Luxe € 54,95", c.get(reverse("studio:start") + "?gelegenheid=bruiloft").content.decode())
        bestellen = c.get(reverse("studio:step", args=[inv.uid, "bestellen"])).content.decode()
        self.assertIn("€ 54,95", bestellen)
        self.assertIn('name="verwacht" value="5495"', bestellen)
        payment = self.pay(inv, owner)
        order = Order.objects.get(invitation=inv)
        self.assertEqual((order.total_cents, payment.amount_cents), (5495, 5495))
        self.assertEqual([l.total_cents for l in order.lines.all()], [5495])
        self.assertIn("€ 54,95", c.get(reverse("orders:status", args=[order.uid])).content.decode())
        mail = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        self.assertIn("€ 54,95", mail.body_text)
        self.assertNotIn("59,95", mail.body_text)

    def test_mollie_krijgt_exact_het_nieuwe_bedrag(self):
        self.wijzig({BRUILOFT_LUXE: 5495, ("bruiloft", "basis"): 2750})
        gevonden = {}

        class Echo(FakeMollie):
            def __call__(self, request, timeout=0):
                if request.get_method() == "POST":
                    gevonden["bedrag"] = json.loads(request.data.decode())["amount"]
                    gevonden["n"] = gevonden.get("n", 0) + 1
                    ref = f"tr_prijsbeheer{gevonden['n']}"
                    return _Response({"id": ref, "_links": {"checkout": {"href": f"https://www.mollie.com/checkout/test-mode?id={ref}"}}})
                return _Response({"id": f"tr_prijsbeheer{gevonden['n']}", "status": self.status, "amount": gevonden["bedrag"], "method": "ideal", "paidAt": "2026-10-17T10:00:00+00:00"})

        echo = Echo()
        for slug, waarde, cents in (("liefde-op-papier", "54.95", 5495), ("monogram", "27.50", 2750)):
            owner = self.make_customer(f"{slug}@example.com")
            inv = vul(self.make_invitation(owner=owner, template=slug, occasion="bruiloft"), owner)
            with override_settings(PAYMENT_PROVIDER="mollie", MOLLIE_API_KEY="test_nagebootst", BASE_URL="https://vaylide.onrender.com"), \
                    mock.patch("orders.providers.urllib.request.urlopen", side_effect=echo):
                echo.status = "open"
                with self.captureOnCommitCallbacks(execute=True):
                    payment = start_checkout(inv, user=owner, package_code="", optional_codes=[], terms_accepted=True)
                self.assertEqual(gevonden["bedrag"], {"currency": "EUR", "value": waarde})
                self.assertEqual((payment.amount_cents, payment.order.total_cents), (cents, cents))
                echo.status = "paid"
                from orders.services import sync_payment

                with self.captureOnCommitCallbacks(execute=True):
                    sync_payment(payment, source="webhook")
                payment.order.refresh_from_db()
                self.assertEqual(payment.order.status, Order.Status.PAID)       # het Mollie-bedrag kwam overeen met de bestelling

    def test_bestaande_bestellingen_en_openstaande_betalingen_houden_hun_bedrag(self):
        betaald_klant, open_klant = self.make_customer("betaald@example.com"), self.make_customer("open@example.com")
        inv1 = vul(self.make_invitation(owner=betaald_klant, template="liefde-op-papier", occasion="bruiloft"), betaald_klant)
        self.pay(inv1, betaald_klant)
        inv2 = vul(self.make_invitation(owner=open_klant, template="liefde-op-papier", occasion="bruiloft"), open_klant)
        with self.captureOnCommitCallbacks(execute=True):
            open_betaling = start_checkout(inv2, user=open_klant, package_code="", optional_codes=[], terms_accepted=True)
        betaald, open_order = Order.objects.get(invitation=inv1), Order.objects.get(invitation=inv2)
        self.wijzig({BRUILOFT_LUXE: 6995})
        betaald.refresh_from_db()
        open_order.refresh_from_db()
        self.assertEqual((betaald.total_cents, open_order.total_cents), (5995, 5995))
        self.assertEqual([l.total_cents for l in open_order.lines.all()], [5995])
        open_betaling.refresh_from_db()
        self.assertEqual(open_betaling.amount_cents, 5995)
        nieuwe_poging = create_payment(open_order)       # "Betaling hervatten" na een mislukte poging gebruikt het vastgelegde bedrag
        self.assertEqual(nieuwe_poging.amount_cents, 5995)
        self.assertEqual(self.als(open_klant).get(reverse("orders:status", args=[open_order.uid])).status_code, 200)

    def test_een_klant_midden_in_het_bestellen_krijgt_een_melding_en_er_wordt_niets_besteld(self):
        owner = self.make_customer()
        inv = vul(self.make_invitation(owner=owner, template="liefde-op-papier", occasion="bruiloft"), owner)
        self.wijzig({BRUILOFT_LUXE: 6495})
        with self.assertRaises(PriceChanged):
            start_checkout(inv, user=owner, package_code="", optional_codes=[], terms_accepted=True, expected_total_cents=5995)
        self.assertEqual(Order.objects.count(), 0)
        payment = start_checkout(inv, user=owner, package_code="", optional_codes=[], terms_accepted=True, expected_total_cents=6495)
        self.assertEqual(payment.amount_cents, 6495)

    def test_kortingscode_rekent_over_de_nieuwe_prijs(self):
        DiscountCode.objects.create(code="TIEN", kind="percent", percent=10)
        self.wijzig({BRUILOFT_LUXE: 5000})
        owner = self.make_customer()
        inv = vul(self.make_invitation(owner=owner, template="liefde-op-papier", occasion="bruiloft"), owner)
        with override_settings(DISCOUNTS_ENABLED=True), self.captureOnCommitCallbacks(execute=True):
            payment = start_checkout(inv, user=owner, package_code="", optional_codes=[], terms_accepted=True, discount_code="TIEN")
        order = payment.order
        self.assertEqual((order.subtotal_cents, order.discount_cents, order.total_cents, payment.amount_cents), (5000, 500, 4500, 4500))

    def test_het_btw_tarief_wordt_op_nieuwe_bestellingen_vastgelegd(self):
        owner = self.make_customer()
        inv = vul(self.make_invitation(owner=owner, template="liefde-op-papier", occasion="bruiloft"), owner)
        self.pay(inv, owner)
        self.assertEqual(Order.objects.get(invitation=inv).vat_rate_percent, 21)
        owner2 = self.make_customer("twee@example.com")
        inv2 = vul(self.make_invitation(owner=owner2, template="liefde-op-papier", occasion="bruiloft"), owner2)
        with override_settings(VAT_RATE_PERCENT=9):
            self.pay(inv2, owner2)
        self.assertEqual(Order.objects.get(invitation=inv2).vat_rate_percent, 9)

    def test_een_bestelling_van_voor_het_btwveld_blijft_ongemoeid(self):
        owner = self.make_customer()
        oud = Order.objects.create(number="VL26-99999", customer=owner, total_cents=3995, vat_rate_percent=None)
        oud.refresh_from_db()
        self.assertIsNone(oud.vat_rate_percent)
        with override_settings(VAT_RATE_PERCENT=9):
            order = Order.objects.get(pk=oud.pk)
            self.assertIsNone(order.vat_rate_percent)


class Validatie(PrijsbeheerBasis):
    def test_euro_invoer(self):
        for tekst, cents in (("29,95", 2995), ("29.95", 2995), ("€ 29,95", 2995), ("30", 3000), ("30,5", 3050), (" 1,00 ", 100), ("500", 50000)):
            self.assertEqual(prijsbeheer.parse_euro(tekst), cents, tekst)
        for slecht in ("", "abc", "29,955", "-5", "1e3", "NaN", "29,", ",95", "29,95,1", "€", "1 000"):
            with self.assertRaises(ValueError, msg=slecht):
                prijsbeheer.parse_euro(slecht)

    def test_grenzen(self):
        for tekst, ok in (("0,99", False), ("1,00", True), ("0", False)):
            self.assertEqual(prijsbeheer.beoordeel({("kerst", "basis"): tekst}).ok, ok, tekst)
        for tekst, ok in (("500,00", True), ("500,01", False), ("2995", False), ("5000", False)):
            self.assertEqual(prijsbeheer.beoordeel({("bruiloft", "special"): tekst}).ok, ok, tekst)

    def test_luxe_mag_niet_goedkoper_zijn_dan_basis_en_special_niet_dan_luxe(self):
        self.assertFalse(prijsbeheer.beoordeel({("bruiloft", "luxe"): "20,00"}).ok)       # basis is 29,95
        self.assertFalse(prijsbeheer.beoordeel({("bruiloft", "special"): "50,00"}).ok)     # luxe is 59,95
        self.assertTrue(prijsbeheer.beoordeel({("bruiloft", "special"): "90,00"}).ok)

    def test_een_grote_sprong_moet_apart_bevestigd_worden(self):
        special = ("bruiloft", "special")
        b = prijsbeheer.beoordeel({special: "135,00"})
        self.assertTrue(b.ok and b.grote_sprong)
        with self.assertRaises(prijsbeheer.PrijsFout):
            self.wijzig({special: 13500})
        prijsbeheer.voer_door(self.eigenaar, {special: 13500}, reden="Test", stempel_in=prijsbeheer.stempel(), grote_sprong_bevestigd=True)
        self.assertEqual(prijsbeheer.lees("bruiloft", "special"), 13500)
        self.assertFalse(prijsbeheer.beoordeel({BRUILOFT_LUXE: "62,00"}).grote_sprong)

    def test_zonder_verschil_wordt_er_niets_opgeslagen(self):
        aantal = PriceChangeSet.objects.count()
        with self.assertRaises(prijsbeheer.PrijsFout):
            self.wijzig({BRUILOFT_LUXE: 5995})
        self.assertEqual(PriceChangeSet.objects.count(), aantal)

    def test_een_reden_is_verplicht(self):
        for reden in ("", "  ", "ab"):
            with self.assertRaises(prijsbeheer.PrijsFout, msg=reden):
                self.wijzig({BRUILOFT_LUXE: 5495}, reden=reden)
        with self.assertRaises(prijsbeheer.PrijsFout):
            self.wijzig({BRUILOFT_LUXE: 5495}, reden="x" * 301)
        self.assertEqual(prijsbeheer.lees("bruiloft", "luxe"), 5995)

    def test_een_verouderd_formulier_wordt_geweigerd(self):
        stempel = prijsbeheer.stempel()
        self.wijzig({BRUILOFT_LUXE: 5495})
        with self.assertRaises(prijsbeheer.PrijsFout) as ctx:
            prijsbeheer.voer_door(self.eigenaar, {BRUILOFT_LUXE: 5295}, reden="Te laat", stempel_in=stempel)
        self.assertIn("intussen", ctx.exception.fouten[""])
        self.assertEqual(prijsbeheer.lees("bruiloft", "luxe"), 5495)

    def test_zonder_prijsbeheer_wordt_er_niet_gewijzigd(self):
        with override_settings(PRICES_ADMIN=False):
            with self.assertRaises(prijsbeheer.PrijsFout):
                self.wijzig({BRUILOFT_LUXE: 5495})
        self.assertEqual(PriceRule.objects.get(rij="bruiloft", tier="luxe").price_cents, 5995)


class LogboekEnTerugdraaien(PrijsbeheerBasis):
    def test_een_wijziging_legt_wie_wanneer_oud_nieuw_en_reden_vast(self):
        zet = self.wijzig({BRUILOFT_LUXE: 5495, ("bruiloft", "special"): 8495}, user=self.hoofd, reden="Seizoensprijs")
        self.assertEqual((zet.user, zet.kind, zet.reason), (self.hoofd, "wijziging", "Seizoensprijs"))
        regels = {(c.rij, c.tier): (c.old_cents, c.new_cents) for c in zet.changes.all()}
        self.assertEqual(regels, {BRUILOFT_LUXE: (5995, 5495), ("bruiloft", "special"): (8995, 8495)})
        self.assertEqual(PriceRule.objects.get(rij="bruiloft", tier="luxe").updated_by, self.hoofd)

    def test_de_prijshistorie_loopt_niet_achter_op_de_prijs(self):
        zet = self.wijzig({BRUILOFT_LUXE: 5495})
        stand = PriceStand.objects.get(key="liefde-op-papier:bruiloft", until__isnull=True)
        self.assertEqual((stand.price_cents, stand.since), (5495, zet.created_at))
        self.assertTrue(PriceStand.objects.filter(key="liefde-op-papier:bruiloft", price_cents=5995, until__isnull=False).exists())

    def test_terugdraaien_is_een_nieuwe_geregistreerde_wijziging(self):
        zet = self.wijzig({BRUILOFT_LUXE: 5495})
        c = self.als(self.hoofd)
        r = c.post(reverse("beheer:prices_revert", args=[zet.pk]), {"cel": ["p_bruiloft_luxe"], "reden": "Toch niet", "begrepen": "1", "stempel": prijsbeheer.stempel()})
        self.assertRedirects(r, reverse("beheer:prices"))
        self.assertEqual(prijsbeheer.lees("bruiloft", "luxe"), 5995)
        terug = PriceChangeSet.objects.first()
        self.assertEqual((terug.kind, terug.reverts, terug.user, terug.reason), ("terugdraaien", zet, self.hoofd, "Toch niet"))
        self.assertEqual(PriceChangeSet.objects.get(pk=zet.pk).changes.get().new_cents, 5495)       # het oude logboek blijft zoals het was
        again = c.post(reverse("beheer:prices_revert", args=[zet.pk]), {"cel": ["p_bruiloft_luxe"], "reden": "Nog eens", "begrepen": "1", "stempel": prijsbeheer.stempel()})
        self.assertRedirects(again, reverse("beheer:prices_log"))         # niet nog een keer

    def test_terugdraaien_vraagt_een_reden_en_laat_een_latere_wijziging_staan_tenzij_aangevinkt(self):
        zet = self.wijzig({BRUILOFT_LUXE: 5495})
        self.wijzig({BRUILOFT_LUXE: 5295})
        c = self.als(self.eigenaar)
        pagina = c.get(reverse("beheer:prices_revert", args=[zet.pk])).content.decode()
        self.assertIn("intussen gewijzigd", pagina)
        self.assertNotIn("checked", pagina.split('name="cel"')[1].split(">")[0])
        zonder = c.post(reverse("beheer:prices_revert", args=[zet.pk]), {"cel": ["p_bruiloft_luxe"], "reden": "", "begrepen": "1", "stempel": prijsbeheer.stempel()})
        self.assertEqual(zonder.status_code, 400)
        self.assertEqual(prijsbeheer.lees("bruiloft", "luxe"), 5295)

    def test_de_startstand_en_een_terugdraaiing_kunnen_niet_nog_eens_teruggedraaid_worden(self):
        seed = PriceChangeSet.objects.get(kind="seed")
        self.assertRedirects(self.als(self.eigenaar).get(reverse("beheer:prices_revert", args=[seed.pk])), reverse("beheer:prices_log"))

    def test_het_logboek_toont_de_wijziging(self):
        self.wijzig({BRUILOFT_LUXE: 5495}, reden="Seizoensprijs")
        html = self.als(self.gewoon).get(reverse("beheer:prices_log")).content.decode()
        for tekst in ("Seizoensprijs", "eigenaar@example.com", "€ 59,95 → <strong>€ 54,95</strong>", "Startstand"):
            self.assertIn(tekst, html)
        self.assertNotIn("Draai terug", html)          # een gewone beheerder mag niet terugdraaien


class BeheerSchermen(PrijsbeheerBasis):
    def post_wijziging(self, c, waarden, stempel=None):
        basis = {f"p_{r}_{t}": f"{prijsbeheer.lees(r, t) // 100},{prijsbeheer.lees(r, t) % 100:02d}" for r, t in prijsbeheer.alle_cellen()}
        basis.update(waarden)
        basis["stempel"] = prijsbeheer.stempel() if stempel is None else stempel
        return c.post(reverse("beheer:prices_edit"), basis)

    def test_de_pagina_toont_de_27_bedragen_en_de_nieuwe_naam(self):
        html = self.als(self.eigenaar).get(reverse("beheer:prices")).content.decode()
        for tekst in ("Wenskaart buiten Kerst", "Trouwuitnodiging", "€ 29,95", "€ 59,95", "€ 89,95", "€ 24,95", "€ 69,00", "€ 9,95", "€ 39,95"):
            self.assertIn(tekst, html)
        self.assertNotIn("Bedankkaart", html)
        self.assertIn("Verloving én Jubileum", html)
        self.assertIn("geen ontwerp, niet te koop", html)
        self.assertIn("Prijzen wijzigen", html)

    def test_eerst_een_bevestiging_met_oud_en_nieuw_en_nog_niets_opgeslagen(self):
        r = self.post_wijziging(self.als(self.eigenaar), {"p_bruiloft_luxe": "54,95"})
        html = r.content.decode()
        self.assertEqual(r.status_code, 200)
        for tekst in ("Controleer je wijziging", "€ 59,95", "<strong>€ 54,95</strong>", "− € 5,00", "(8,3%)", "€ 10,40 → € 9,54", "Bestaande bestellingen en openstaande betalingen houden hun bedrag",
                      'name="p_bruiloft_luxe" value="54,95"', "verplicht"):
            self.assertIn(tekst, html)
        self.assertEqual(prijsbeheer.lees("bruiloft", "luxe"), 5995)
        self.assertEqual(PriceChangeSet.objects.exclude(kind="seed").count(), 0)

    def test_doorvoeren_vraagt_reden_en_vinkje_en_slaat_dan_op(self):
        c = self.als(self.eigenaar)
        data = {"p_bruiloft_luxe": "54,95", "stempel": prijsbeheer.stempel()}
        zonder_reden = c.post(reverse("beheer:prices_confirm"), {**data, "reden": "", "begrepen": "1"})
        self.assertEqual(zonder_reden.status_code, 400)
        zonder_vinkje = c.post(reverse("beheer:prices_confirm"), {**data, "reden": "Test"})
        self.assertEqual(zonder_vinkje.status_code, 400)
        self.assertEqual(prijsbeheer.lees("bruiloft", "luxe"), 5995)
        ok = c.post(reverse("beheer:prices_confirm"), {**data, "reden": "Seizoensprijs", "begrepen": "1"})
        self.assertRedirects(ok, reverse("beheer:prices"))
        self.assertEqual(prijsbeheer.lees("bruiloft", "luxe"), 5495)
        self.assertEqual(PriceChangeSet.objects.first().reason, "Seizoensprijs")

    def test_ongeldige_invoer_geeft_een_duidelijke_melding_bij_het_veld(self):
        r = self.post_wijziging(self.als(self.eigenaar), {"p_bruiloft_luxe": "abc", "p_kerst_luxe": "0,50", "p_zakelijk_special": "20,00"})
        html = r.content.decode()
        self.assertEqual(r.status_code, 400)
        for tekst in ("Vul een bedrag in met maximaal twee decimalen", "Een prijs ligt tussen € 1,00 en € 500,00", "Special kan niet goedkoper zijn dan Luxe"):
            self.assertIn(tekst, html)
        self.assertIn('value="abc"', html)
        self.assertEqual(prijsbeheer.lees("bruiloft", "luxe"), 5995)

    def test_een_verouderd_formulier_stuurt_terug_naar_de_nieuwe_stand(self):
        c = self.als(self.eigenaar)
        oud = prijsbeheer.stempel()
        self.wijzig({BRUILOFT_LUXE: 5495})
        r = self.post_wijziging(c, {"p_bruiloft_luxe": "50,00"}, stempel=oud)
        self.assertRedirects(r, reverse("beheer:prices_edit"))

    def test_de_bevestiging_noemt_de_geraakte_kortingscodes(self):
        DiscountCode.objects.create(code="TROUW", kind="percent", percent=10, occasions=["bruiloft"])
        DiscountCode.objects.create(code="KERST5", kind="percent", percent=5, occasions=["kerst"])
        html = self.post_wijziging(self.als(self.eigenaar), {"p_bruiloft_luxe": "54,95"}).content.decode()
        self.assertIn("TROUW", html.split("Dit raakt")[2] if "Dit raakt 1 actieve" in html else html)
        self.assertIn("Dit raakt 1 actieve of geplande kortingscode", html)
        self.assertNotIn("KERST5", html)

    def test_wijzigen_kan_niet_als_prijsbeheer_uit_staat(self):
        with override_settings(PRICES_ADMIN=False):
            c = self.als(self.eigenaar)
            html = c.get(reverse("beheer:prices")).content.decode()
            self.assertIn("Prijsbeheer staat uit", html)
            self.assertNotIn("Prijzen wijzigen</a>", html)
            self.assertRedirects(c.get(reverse("beheer:prices_edit")), reverse("beheer:prices"))

    def test_een_ontbrekend_bedrag_wordt_bovenaan_gemeld(self):
        PriceRule.objects.filter(rij="bruiloft", tier="luxe").delete()
        for url in (reverse("beheer:prices"), reverse("beheer:orders")):
            html = self.als(self.eigenaar).get(url).content.decode()
            self.assertIn("ontbreekt of is ongeldig", html, url)
        self.assertIn("niet te bestellen", self.als(self.eigenaar).get(reverse("beheer:prices")).content.decode())

    def test_de_oude_pakkettenpagina_blijft_werken_en_belooft_niets_meer(self):
        html = self.als(self.eigenaar).get(reverse("beheer:pricing")).content.decode()
        self.assertIn("Actieve prijsstructuur", html)
        self.assertIn("€ 59,95", html)
        self.wijzig({BRUILOFT_LUXE: 5495})
        self.assertIn("€ 54,95", self.als(self.eigenaar).get(reverse("beheer:pricing")).content.decode())


class Rechten(PrijsbeheerBasis):
    URLS_LEZEN = ("beheer:prices", "beheer:prices_log")

    def test_anoniem_en_klant_komen_er_niet_in(self):
        klant = self.make_customer()
        for naam in self.URLS_LEZEN + ("beheer:prices_edit",):
            self.assertEqual(Client().get(reverse(naam)).status_code, 302, naam)
            self.assertEqual(self.als(klant).get(reverse(naam)).status_code, 404, naam)
        for naam in ("beheer:prices_confirm",):
            self.assertEqual(self.als(klant).post(reverse(naam), {}).status_code, 404, naam)
            self.assertEqual(Client().post(reverse(naam), {}).status_code, 302, naam)
        self.assertEqual(Order.objects.count() + PriceChangeSet.objects.exclude(kind="seed").count(), 0)

    def test_een_gewone_beheerder_mag_alleen_bekijken(self):
        c = self.als(self.gewoon)
        for naam in self.URLS_LEZEN:
            self.assertEqual(c.get(reverse(naam)).status_code, 200, naam)
        self.assertNotIn("Prijzen wijzigen", c.get(reverse("beheer:prices")).content.decode())
        zet = self.wijzig({BRUILOFT_LUXE: 5495})
        self.assertEqual(c.get(reverse("beheer:prices_edit")).status_code, 403)
        self.assertEqual(c.post(reverse("beheer:prices_edit"), {"p_bruiloft_luxe": "50,00", "stempel": prijsbeheer.stempel()}).status_code, 403)
        self.assertEqual(c.post(reverse("beheer:prices_confirm"), {"p_bruiloft_luxe": "50,00", "reden": "Hack", "begrepen": "1", "stempel": prijsbeheer.stempel()}).status_code, 403)
        self.assertEqual(c.get(reverse("beheer:prices_revert", args=[zet.pk])).status_code, 403)
        self.assertEqual(c.post(reverse("beheer:prices_revert", args=[zet.pk]), {"cel": ["p_bruiloft_luxe"], "reden": "Hack", "begrepen": "1"}).status_code, 403)
        self.assertEqual(prijsbeheer.lees("bruiloft", "luxe"), 5495)
        with self.assertRaises(PermissionError):
            prijsbeheer.voer_door(self.gewoon, {BRUILOFT_LUXE: 5000}, reden="Hack", stempel_in=prijsbeheer.stempel())

    def test_een_hoofdbeheerder_mag_bekijken_wijzigen_en_terugdraaien(self):
        c = self.als(self.hoofd)
        self.assertEqual(c.get(reverse("beheer:prices_edit")).status_code, 200)
        ok = c.post(reverse("beheer:prices_confirm"), {"p_bruiloft_luxe": "54,95", "reden": "Hoofdbeheerder", "begrepen": "1", "stempel": prijsbeheer.stempel()})
        self.assertRedirects(ok, reverse("beheer:prices"))
        self.assertEqual(prijsbeheer.lees("bruiloft", "luxe"), 5495)
        zet = PriceChangeSet.objects.first()
        self.assertEqual(c.get(reverse("beheer:prices_revert", args=[zet.pk])).status_code, 200)

    def test_de_eigenaar_mag_alles(self):
        c = self.als(self.eigenaar)
        self.assertEqual(c.get(reverse("beheer:prices_edit")).status_code, 200)
        self.assertEqual(rollen.rol(self.eigenaar), rollen.EIGENAAR)
        self.assertEqual(rollen.rol(self.hoofd), rollen.HOOFDBEHEERDER)
        self.assertEqual(rollen.rol(self.gewoon), "Beheerder")

    def test_een_uitgeschakeld_account_heeft_geen_rechten(self):
        self.hoofd.is_active = False
        self.hoofd.save()
        self.assertFalse(rollen.mag_prijzen_wijzigen(self.hoofd))
        self.assertFalse(rollen.mag_prijzen_bekijken(self.hoofd))

    def test_een_groepslid_zonder_is_staff_heeft_geen_toegang(self):
        user = User.objects.create_user(email="geengroepstaff@example.com")
        user.groups.add(Group.objects.get(name=rollen.HOOFDBEHEERDER))
        self.assertFalse(rollen.mag_prijzen_wijzigen(user))
        self.assertEqual(self.als(user).get(reverse("beheer:prices_edit")).status_code, 404)


class EigenaarsaccountBeschermd(PrijsbeheerBasis):
    def test_een_eigenaarsaccount_wordt_alleen_door_zichzelf_gewijzigd(self):
        tweede_eigenaar = self.make_staff("eigenaar2@example.com")
        self.assertTrue(rollen.mag_account_wijzigen(self.eigenaar, self.eigenaar))
        for actor in (self.hoofd, self.gewoon, tweede_eigenaar):
            self.assertFalse(rollen.mag_account_wijzigen(actor, self.eigenaar), actor.email)
        self.assertFalse(rollen.mag_account_wijzigen(None, self.eigenaar))
        self.assertFalse(rollen.mag_account_wijzigen(self.gewoon, self.hoofd))       # een gewone beheerder wijzigt geen andere medewerker
        self.assertTrue(rollen.mag_account_wijzigen(self.eigenaar, self.hoofd))

    def test_een_eigenaar_via_de_groep_is_ook_beschermd(self):
        via_groep = self.maak_staff("groep@example.com", groep=rollen.EIGENAAR)
        self.assertTrue(rollen.is_eigenaar(via_groep))
        self.assertFalse(rollen.mag_account_wijzigen(self.hoofd, via_groep))

    def test_geen_beheerscherm_kan_een_medewerker_openen_bewerken_of_anonimiseren(self):
        c = self.als(self.eigenaar)
        for medewerker in (self.eigenaar, self.hoofd, self.gewoon):
            self.assertEqual(c.get(reverse("beheer:customer", args=[medewerker.pk])).status_code, 404)
            self.assertEqual(c.post(reverse("beheer:customer", args=[medewerker.pk]), {"actie": "anonimiseer"}).status_code, 404)
        self.assertTrue(User.objects.filter(pk=self.eigenaar.pk, anonymized_at__isnull=True).exists())

    def test_anonimiseren_weigert_een_medewerkers_en_eigenaarsaccount(self):
        from core.privacy import anonymize_user

        for medewerker in (self.eigenaar, self.hoofd, self.gewoon):
            with self.assertRaises(ValueError):
                anonymize_user(medewerker)

    def test_gebruikers_en_groepen_zijn_niet_te_bewerken_in_het_noodbeheer(self):
        geregistreerd = {m.__name__ for m in admin.site._registry}
        self.assertFalse(geregistreerd & {"User", "Permission"})
        for medewerker in (self.hoofd, self.gewoon):       # Groep staat wel in het noodbeheer, maar alleen een superuser heeft daar rechten
            self.assertFalse(medewerker.has_perm("auth.change_group") or medewerker.has_perm("auth.add_group") or medewerker.has_perm("accounts.change_user"))

    def test_wijs_rol_toe_doet_niets_zonder_bevestiging_en_wijzigt_geen_eigenaar(self):
        uit = StringIO()
        call_command("wijs_rol_toe", "gewoon@example.com", "hoofdbeheerder", stdout=uit)
        self.assertIn("--bevestig", uit.getvalue())
        self.assertFalse(self.gewoon.groups.exists())
        with self.assertRaises(CommandError):
            call_command("wijs_rol_toe", "eigenaar@example.com", "hoofdbeheerder", "--bevestig")
        with self.assertRaises(CommandError):
            call_command("wijs_rol_toe", "gewoon@example.com", "eigenaar", "--bevestig")        # eigenaarsrechten vragen een afzonderlijk akkoord
        self.assertFalse(self.gewoon.groups.exists())
        with self.assertRaises(CommandError):
            call_command("wijs_rol_toe", "bestaat-niet@example.com", "hoofdbeheerder", "--bevestig")
        self.assertFalse(User.objects.filter(email="bestaat-niet@example.com").exists())
        call_command("wijs_rol_toe", "gewoon@example.com", "hoofdbeheerder", "--bevestig", stdout=StringIO())
        self.assertEqual(rollen.rol(self.gewoon), rollen.HOOFDBEHEERDER)

    def test_controleer_rechten_is_alleen_lezen_en_toont_geen_geheimen(self):
        uit = StringIO()
        vooraf = list(User.objects.values_list("pk", "is_staff", "is_superuser", "password"))
        call_command("controleer_rechten", stdout=uit)
        tekst = uit.getvalue()
        self.assertIn("eigenaar@example.com: rol Eigenaar", tekst)
        self.assertIn("hoofd@example.com: rol Hoofdbeheerder", tekst)
        self.assertNotIn("pbkdf2", tekst)
        self.assertEqual(vooraf, list(User.objects.values_list("pk", "is_staff", "is_superuser", "password")))


class Controlecommando(PrijsbeheerBasis):
    def test_controleer_prijsbron_slaagt_op_de_startstand_en_faalt_bij_een_afwijking(self):
        uit = StringIO()
        call_command("controleer_prijsbron", stdout=uit)
        self.assertIn("Alles klopt", uit.getvalue())
        self.assertIn("27 van 27 gelijk", uit.getvalue())
        PriceRule.objects.filter(rij="bruiloft", tier="luxe").update(price_cents=5495)
        with self.assertRaises(SystemExit):
            call_command("controleer_prijsbron", stdout=StringIO(), stderr=StringIO())

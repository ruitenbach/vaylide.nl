"""De nieuwe prijsstructuur (Basis, Luxe, Special per ontwerp en gelegenheid; catalog/prijzen.py, settings.PRICING_V2).

Wat deze tests bewaken:
- de prijstabel van de eigenaar staat er letterlijk in, en elk ontwerp heeft een indeling;
- het bedrag op de ontwerppagina, in het voorbeeld, in Bestellen, op de bestelling, op de betaling en bij Mollie is altijd hetzelfde;
- er zijn geen automatische toeslagen: wat je kunt personaliseren zit in de prijs;
- bestaande, betaalde bestellingen veranderen niet;
- een concept van vóór de invoering ziet het nieuwe bedrag expliciet vóór betaling;
- staat de schakelaar uit, dan werkt alles zoals voorheen (dat bewaken de bestaande tests).
Het controleren van de teksten op de hele site (geen Essentieel/Compleet meer) draait alleen als het proces met VIERLIEF_PRICING_V2=1 is gestart."""
import json
import re
import unittest
from unittest import mock

from django.conf import settings
from django.test import Client, override_settings
from django.urls import reverse

from catalog import prijzen
from catalog.models import Template, format_euro
from catalog.prijzen import BASIS, LUXE, SPECIAL
from invitations.content import required_features
from invitations.services import create_draft
from orders.models import Order, OrderLine, Payment
from orders.pricing import PricingError, build_quote, compare_packages
from orders.providers import MollieProvider
from orders.services import start_checkout

from .helpers import VaylideTestCase
from .test_mollie_testmodus import FakeMollie, _Response

# De tabel van de eigenaar (15 oktober 2026), in centen, incl. btw: (Basis, Luxe, Special)
TABEL_EIGENAAR = {
    "kerst": (995, 2495, 4995), "verjaardag": (1995, 3495, 5995), "zakelijk": (1495, 2995, 4995), "babyshower": (1995, 3495, 5995),
    "geboorte": (1995, 3495, 5995), "savethedate": (1995, 3995, 6900), "bruiloft": (2995, 5995, 8995), "jubileum_verloving": (1995, 3995, 6900),
    "bedank": (995, 1995, 3995),
}
V2 = override_settings(PRICING_V2=True)


def ontwerp(slug):
    return Template.objects.get(slug=slug)


def vul(inv, owner):
    """Een compleet concept voor elke gelegenheid: de verplichte naamvelden van die gelegenheid krijgen een waarde."""
    from catalog.occasions import occasion_config
    from invitations.services import save_draft

    content = dict(inv.draft_content)
    content["names"] = {veld[0]: "Test" for veld in occasion_config(inv.occasion)["name_fields"] if veld[2]}
    return save_draft(inv, expected_rev=None, content=content, user=owner)


class NieuwePrijzen(VaylideTestCase):
    """VaylideTestCase zet de schakelaar uit (de bestaande tests gelden voor de oude structuur); deze klasse zet hem per test weer aan."""

    def setUp(self):
        super().setUp()
        aan = override_settings(PRICING_V2=True)
        aan.enable()
        self.addCleanup(aan.disable)


class IndelingEnTabel(VaylideTestCase):
    def test_de_prijstabel_is_precies_die_van_de_eigenaar(self):
        self.assertEqual(prijzen.PRIJZEN, TABEL_EIGENAAR)

    def test_elk_ontwerp_heeft_een_indeling_en_alleen_bestaande_ontwerpen(self):
        slugs = set(Template.objects.values_list("slug", flat=True))
        self.assertEqual(set(prijzen.INDELING), slugs, "elk ontwerp in de catalogus heeft precies één indeling (en niets anders)")
        tellers = {t: sum(1 for i in prijzen.INDELING.values() if i == t) for t in prijzen.TIERS}
        self.assertEqual(tellers, {BASIS: 32, LUXE: 14, SPECIAL: 10})

    def test_elke_special_vlag_is_een_special_of_bewust_luxe(self):
        vlag = {t.slug for t in Template.objects.filter(special=True)}
        niet_special = {s for s in vlag if prijzen.INDELING[s] != SPECIAL}
        self.assertEqual(niet_special, {"golden-noel"}, "alleen Golden Noël heeft de vlag maar is bewust Luxe (kwaliteitscontrole 15 oktober)")

    def test_alle_indelingen_staan_12_maanden_online(self):
        """Besluit van de eigenaar (15 oktober 2026): voor Basis, Luxe en Special 12 maanden online, ook voor een wenskaart."""
        self.assertEqual(prijzen.MAANDEN_ONLINE, {BASIS: 12, LUXE: 12, SPECIAL: 12})
        for t in Template.objects.all():
            for occasion in t.occasions:
                for soort in ("", "wenskaart"):
                    self.assertEqual(prijzen.prijs_info(t, occasion, soort)["maanden"], 12)
                    self.assertEqual(prijzen.tier_package(t, occasion, soort).availability_months, 12)
        self.assertEqual(prijzen.looptijd_zin("Een kaart"), "Een kaart staat 12 maanden online")

    def test_gelegenheden_en_rijen(self):
        self.assertEqual(prijzen.categorie("kerst", ""), "kerst")
        self.assertEqual(prijzen.categorie("kerst", "wenskaart"), "kerst")
        self.assertEqual(prijzen.categorie("bruiloft", ""), "bruiloft")
        self.assertEqual(prijzen.categorie("verloving", ""), "jubileum_verloving")
        self.assertEqual(prijzen.categorie("jubileum", ""), "jubileum_verloving")
        self.assertEqual(prijzen.categorie("babyshower", ""), "babyshower")
        for occasion in ("bruiloft", "verloving", "verjaardag", "jubileum", "babyshower", "zakelijk"):
            self.assertEqual(prijzen.categorie(occasion, "wenskaart"), "bedank")
        self.assertIsNone(prijzen.categorie("onbekend", ""))

    def test_een_ontwerp_in_meerdere_gelegenheden_krijgt_per_gelegenheid_de_juiste_prijs(self):
        luxe = ontwerp("liefde-op-papier")
        self.assertEqual(prijzen.tier(luxe), LUXE)
        verwacht = {"bruiloft": 5995, "verloving": 3995, "jubileum": 3995, "verjaardag": 3495, "babyshower": 3495}
        for occasion, cents in verwacht.items():
            self.assertEqual(prijzen.prijs_cents(luxe, occasion), cents, occasion)
            self.assertEqual(prijzen.prijs_cents(luxe, occasion, "wenskaart"), 1995)
        self.assertEqual(prijzen.prijs_info(luxe, "bruiloft")["label"], "Luxe € 59,95")

    def test_prijsweergave_altijd_twee_decimalen_in_de_nieuwe_structuur(self):
        with override_settings(PRICING_V2=False):
            self.assertEqual(format_euro(6900), "€ 69")
        with V2:
            self.assertEqual(format_euro(6900), "€ 69,00")
            self.assertEqual(format_euro(995), "€ 9,95")
            self.assertEqual(format_euro(12345), "€ 123,45")

    def test_zonder_ontwerp_in_een_indeling_wordt_die_prijs_niet_getoond(self):
        kerst = dict(prijzen.beschikbaar("kerst"))
        self.assertNotIn(BASIS, kerst, "Kerst heeft nu geen zichtbaar Basis-ontwerp: de prijs van € 9,95 wordt niet getoond")
        self.assertEqual(kerst[LUXE], 2495)
        self.assertEqual(kerst[SPECIAL], 4995)
        with V2:
            self.assertNotIn("€ 9,95", prijzen.zin("kerst"))
            self.assertIn("€ 24,95 (Luxe)", prijzen.zin("kerst"))
        for rij in ("geboorte", "savethedate"):
            self.assertEqual(prijzen.beschikbaar(rij), [], "gelegenheden zonder ontwerpen blijven niet selecteerbaar")


class Berekening(NieuwePrijzen):
    def test_elke_combinatie_geeft_een_regel_met_het_bedrag_uit_de_tabel(self):
        gecontroleerd = 0
        for t in Template.objects.all():
            for occasion in t.occasions:
                for soort in ("", "wenskaart"):
                    rij = prijzen.categorie(occasion, soort)
                    verwacht = TABEL_EIGENAAR[rij][prijzen.TIERS.index(prijzen.INDELING[t.slug])]
                    content = {"soort": soort} if soort else {}
                    quote = build_quote(content, None, None, template_version=t.current_version, occasion=occasion)
                    self.assertEqual(quote.total_cents, verwacht, (t.slug, occasion, soort))
                    self.assertEqual(len(quote.lines), 1, "één regel, geen toeslagen")
                    self.assertEqual(quote.total_display, prijzen.prijs_info(t, occasion, soort)["display"], "getoond bedrag = offerte")
                    self.assertEqual(compare_packages(content, [], t.current_version, occasion)[0].total_cents, verwacht)
                    gecontroleerd += 1
        self.assertGreater(gecontroleerd, 200)

    def test_geen_automatische_toeslagen_voor_personalisatie(self):
        owner = self.make_customer()
        for slug, occasion, cents in (("winterlicht", "kerst", 2495), ("liefde-op-papier", "bruiloft", 5995), ("monogram", "bruiloft", 2995), ("balzaal", "bruiloft", 8995)):
            inv = self.make_invitation(owner=owner, template=slug, occasion=occasion)
            content = dict(inv.draft_content)
            content["sections"] = {**content.get("sections", {}), "story": True, "gallery": True, "music": True, "rsvp": True}
            content["story"] = {"title": "Ons verhaal", "text": "Zo begon het."}
            content["photos"] = {**content.get("photos", {}), "gallery": [{"asset": "x"}]}
            content["music"] = {"asset": "y", "title": "Ons nummer"}
            content["rsvp"] = {**content.get("rsvp", {}), "questions": [{"field": "vervoer", "label": "Hoe kom je?", "type": "text"}]}
            self.assertEqual(required_features(content), {"story", "gallery", "music", "extra_questions"})
            quote = build_quote(content, None, None, template_version=inv.template_version, occasion=occasion)
            self.assertEqual(quote.total_cents, cents, slug)
            self.assertEqual([l.total_cents for l in quote.lines], [cents])

    def test_een_special_kost_precies_de_special_prijs_zonder_meerprijs(self):
        quote = build_quote({}, None, None, template_version=ontwerp("kerstbol").current_version, occasion="kerst")
        self.assertEqual((quote.total_cents, quote.package.code), (4995, "special"))
        quote = build_quote({}, None, None, template_version=ontwerp("aurora-nocturne").current_version, occasion="jubileum")
        self.assertEqual(quote.total_cents, 6900)

    def test_eigen_gezichten_blijven_een_aparte_uitgeschakelde_optie(self):
        content = {"style": {"paar_eigen": True}}
        with self.assertRaises(PricingError):
            build_quote(content, None, None, template_version=ontwerp("balzaal").current_version, occasion="bruiloft")

    def test_zonder_prijs_geen_bestelling(self):
        with self.assertRaises(PricingError):
            build_quote({}, None, None, template_version=ontwerp("winterlicht").current_version, occasion="bruiloft")   # een kerstontwerp is geen bruiloftsontwerp
        with self.assertRaises(PricingError):
            build_quote({}, None, None, template_version=ontwerp("monogram").current_version, occasion="onbekend")


class BestellenEnBetalen(NieuwePrijzen):
    def test_de_bestelling_legt_een_regel_een_bedrag_en_de_duur_vast(self):
        owner = self.make_customer()
        gevallen = [("monogram", "bruiloft", 2995, BASIS, 12), ("liefde-op-papier", "verjaardag", 3495, LUXE, 12), ("kerststad", "kerst", 4995, SPECIAL, 12)]
        for i, (slug, occasion, cents, indeling, maanden) in enumerate(gevallen):
            klant = self.make_customer(f"klant{i}@example.com")
            inv = vul(self.make_invitation(owner=klant, template=slug, occasion=occasion), klant)
            payment = self.pay(inv, klant, package="essentieel", extras=["muziek"])   # een meegestuurd pakket of optie telt niet
            order = Order.objects.get(invitation=inv)
            self.assertEqual(order.total_cents, cents)
            self.assertEqual(payment.amount_cents, cents)
            self.assertEqual([l.total_cents for l in order.lines.all()], [cents])
            self.assertEqual(sum(l.total_cents for l in order.lines.all()), order.total_cents)
            self.assertEqual((order.package_code, order.availability_months), (indeling, maanden))
            self.assertEqual(order.status, Order.Status.PAID)
            self.assertIn(prijzen.TIER_NAAM[indeling], order.lines.first().description)
            self.assertIn(Template.objects.get(slug=slug).name, order.lines.first().description)
            # online tot en met: zoveel kalendermaanden na de bevestigde betaling
            self.assertIsNotNone(order.ends_at)
            self.assertEqual((order.ends_at.year * 12 + order.ends_at.month) - (order.paid_at.year * 12 + order.paid_at.month), maanden)
            inv.refresh_from_db()
            self.assertEqual(sorted(inv.features), sorted(set(prijzen.ALLE_FUNCTIES) | ({"special"} if indeling == SPECIAL else set())))

    def test_de_nieuwe_kerstkaarten_met_film_zijn_luxe_en_te_bestellen_en_te_publiceren(self):
        # Kerstmarkt, Kerstpaleis, Kerstcoupé en Kerstbal: Luxe, € 24,95, 12 maanden, via dezelfde ene bron; geen toeslag of pakketkeuze.
        for i, slug in enumerate(("kerstmarkt", "kerstpaleis", "kerstcoupe", "kerstbal")):
            klant = self.make_customer(f"film{i}@example.com")
            inv = vul(self.make_invitation(owner=klant, template=slug, occasion="kerst"), klant)
            c = Client()
            c.force_login(klant)
            html = c.get(reverse("studio:step", args=[inv.uid, "bestellen"])).content.decode()
            self.assertIn("€ 24,95", html, slug)
            self.assertIn("12 maanden online", html, slug)
            for tekst in ("Upgrade", "Extra opties", "Essentieel", "Compleet"):
                self.assertNotIn(tekst, html, f"{slug}: {tekst}")
            payment = self.pay(inv, klant)
            order = Order.objects.get(invitation=inv)
            self.assertEqual((order.total_cents, payment.amount_cents, order.package_code, order.availability_months), (2495, 2495, LUXE, 12), slug)
            inv.refresh_from_db()
            self.assertTrue(inv.is_published, slug)
            self.assertEqual(c.get(reverse("orders:status", args=[order.uid])).status_code, 200, slug)

    def test_zwanenhart_is_special_en_kost_voor_een_trouwkaart_89_95(self):
        # Zwanenhart: Special, trouwkaart € 89,95 (bestaand bedrag in de tabel), 12 maanden; geen toeslag of pakketkeuze.
        klant = self.make_customer("zwanenhart@example.com")
        inv = vul(self.make_invitation(owner=klant, template="zwanenhart", occasion="bruiloft"), klant)
        c = Client()
        c.force_login(klant)
        html = c.get(reverse("studio:step", args=[inv.uid, "bestellen"])).content.decode()
        self.assertIn("€ 89,95", html)
        self.assertIn("12 maanden online", html)
        for tekst in ("Upgrade", "Extra opties", "Essentieel", "Compleet"):
            self.assertNotIn(tekst, html, tekst)
        payment = self.pay(inv, klant)
        order = Order.objects.get(invitation=inv)
        self.assertEqual((order.total_cents, payment.amount_cents, order.package_code, order.availability_months), (8995, 8995, SPECIAL, 12))
        inv.refresh_from_db()
        self.assertTrue(inv.is_published)
        self.assertEqual(prijzen.INDELING["zwanenhart"], SPECIAL)

    def test_zwanenhart_houdt_de_bestaande_special_prijzen_per_gelegenheid(self):
        # Bruiloft € 89,95, verloving en jubileum € 69,00, allemaal Special en 12 maanden; geen nieuw prijspunt in de tabel.
        verwacht = {"bruiloft": 8995, "verloving": 6900, "jubileum": 6900}
        for gelegenheid, cents in verwacht.items():
            info = prijzen.prijs_info(ontwerp("zwanenhart"), gelegenheid)
            self.assertEqual((info["tier"], info["cents"], info["maanden"]), (SPECIAL, cents, 12), gelegenheid)

    def test_wenskaart_krijgt_de_prijs_uit_dezelfde_tabel(self):
        owner = self.make_customer()
        from invitations.services import save_draft
        for occasion, slug, cents, code in (("bruiloft", "liefde-op-papier", 1995, "luxe-wenskaart"), ("kerst", "winterlicht", 2495, "luxe-wenskaart"), ("bruiloft", "monogram", 995, "basis-wenskaart")):
            inv = create_draft(occasion=occasion, template=ontwerp(slug), owner=owner, soort="wenskaart")
            content = dict(inv.draft_content)
            content["welcome_text"] = "Gefeliciteerd!"
            content["names"] = {"partner_1": "Anna", "partner_2": "Bram"} if occasion == "bruiloft" else content["names"]
            inv = save_draft(inv, expected_rev=None, content=content, user=owner)
            inv = vul(inv, owner) if occasion == "kerst" else inv
            self.pay(inv, owner)
            order = Order.objects.get(invitation=inv)
            self.assertEqual((order.total_cents, order.package_code), (cents, code), (slug, occasion))
            self.assertTrue(prijzen.is_wenskaart_code(order.package_code))

    def test_mollie_krijgt_exact_het_getoonde_bedrag(self):
        gevonden = {}

        class Echo(FakeMollie):
            def __call__(self, request, timeout=0):
                if request.get_method() == "POST":
                    gevonden["bedrag"] = json.loads(request.data.decode())["amount"]
                    gevonden["n"] = gevonden.get("n", 0) + 1
                    ref = f"tr_prijs{gevonden['n']}"
                    return _Response({"id": ref, "_links": {"checkout": {"href": f"https://www.mollie.com/checkout/test-mode?id={ref}"}}})
                return _Response({"id": f"tr_prijs{gevonden['n']}", "status": self.status, "amount": gevonden["bedrag"], "method": "ideal", "paidAt": "2026-10-15T10:00:00+00:00"})

        echo = Echo()
        for slug, occasion, cents, waarde in (("aurora-nocturne", "jubileum", 6900, "69.00"), ("monogram", "bruiloft", 2995, "29.95"), ("kerstbol", "kerst", 4995, "49.95")):
            owner = self.make_customer(f"{slug}@example.com")
            inv = vul(self.make_invitation(owner=owner, template=slug, occasion=occasion), owner)
            with override_settings(PAYMENT_PROVIDER="mollie", MOLLIE_API_KEY="test_nagebootst", BASE_URL="https://vaylide.onrender.com"), \
                    mock.patch("orders.providers.urllib.request.urlopen", side_effect=echo):
                echo.status = "open"
                with self.captureOnCommitCallbacks(execute=True):
                    payment = start_checkout(inv, user=owner, package_code="", optional_codes=[], terms_accepted=True)
                self.assertEqual(gevonden["bedrag"], {"currency": "EUR", "value": waarde})
                self.assertEqual(payment.amount_cents, cents)
                self.assertEqual(payment.order.total_cents, cents)
                echo.status = "paid"
                with self.captureOnCommitCallbacks(execute=True):
                    from orders.services import sync_payment
                    sync_payment(payment, source="webhook")
                payment.refresh_from_db()
                payment.order.refresh_from_db()
                self.assertEqual((payment.status, payment.order.status), (Payment.Status.PAID, Order.Status.PAID))

    def test_een_afwijkend_bedrag_bij_mollie_publiceert_niet(self):
        owner = self.make_customer()
        inv = self.make_invitation(owner=owner, template="monogram", occasion="bruiloft")
        with self.captureOnCommitCallbacks(execute=True):
            payment = start_checkout(inv, user=owner, package_code="", optional_codes=[], terms_accepted=True)
        from orders.providers import RemoteStatus
        from orders.services import apply_remote_status
        with self.captureOnCommitCallbacks(execute=True):
            apply_remote_status(payment, RemoteStatus(status=Payment.Status.PAID, amount_cents=3900, currency="EUR", method="ideal"), source="webhook")
        payment.refresh_from_db()
        order = Order.objects.get(pk=payment.order_id)
        self.assertNotEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.fulfilment_status, Order.Fulfilment.ATTENTION)


class BestaandeBestellingen(VaylideTestCase):
    def test_een_betaalde_bestelling_uit_de_oude_structuur_blijft_exact_zoals_hij_was(self):
        owner = self.make_customer()
        inv = self.make_invitation(owner=owner, template="liefde-op-papier", occasion="bruiloft")
        with override_settings(PRICING_V2=False):      # de oude structuur: Compleet en een extra optie
            self.pay(inv, owner, package="compleet", extras=["langer-online"])
        order = Order.objects.get(invitation=inv)
        voor = (order.total_cents, order.package_code, order.package_name, order.availability_months, sorted(order.features),
                [(l.code, l.description, l.unit_price_cents, l.total_cents) for l in order.lines.all()], order.ends_at)
        pagina_voor = Client().get(reverse("orders:status", args=[order.uid])).status_code
        with V2:
            na = Order.objects.get(pk=order.pk)
            self.assertEqual(voor, (na.total_cents, na.package_code, na.package_name, na.availability_months, sorted(na.features),
                                    [(l.code, l.description, l.unit_price_cents, l.total_cents) for l in na.lines.all()], na.ends_at))
            self.assertEqual(na.total_display, "€ 81,00")      # 69 + 12, nu met twee decimalen weergegeven; het bedrag zelf is niet veranderd
            self.assertEqual(Payment.objects.get(order=na).amount_cents, na.total_cents)
        self.assertIn(pagina_voor, (200, 302, 404))

    def test_een_nieuw_ordertotaal_raakt_oude_bestellingen_niet(self):
        owner = self.make_customer()
        oud = self.make_invitation(owner=owner, template="liefde-op-papier", occasion="bruiloft")
        with override_settings(PRICING_V2=False):
            self.pay(oud, owner, package="essentieel")
        oude_order = Order.objects.get(invitation=oud)
        with V2:
            nieuw = self.make_invitation(owner=self.make_customer("nieuw@example.com"), template="liefde-op-papier", occasion="bruiloft")
            self.pay(nieuw, nieuw.owner)
        oude_order.refresh_from_db()
        self.assertEqual(oude_order.total_cents, 3900)
        self.assertEqual(Order.objects.get(invitation=nieuw).total_cents, 5995)


    def test_de_editor_belooft_een_oude_klant_geen_onderdelen_die_niet_in_zijn_bestelling_zitten(self):
        """Een kaart die in de oude structuur is besteld (Essentieel) houdt zijn eigen voorwaarden: ook met de nieuwe prijzen aan staat er in de editor
        niet 'Inbegrepen' bij onderdelen die hij niet kocht. Een nieuwe of nog niet bestelde kaart ziet wel 'Inbegrepen'."""
        owner = self.make_customer()
        oud = self.make_invitation(owner=owner, template="liefde-op-papier", occasion="bruiloft")
        with override_settings(PRICING_V2=False):
            self.pay(oud, owner, package="essentieel")
        nieuw = self.make_invitation(owner=owner, template="liefde-op-papier", occasion="bruiloft")
        c = Client()
        c.force_login(owner)
        with V2:
            tekst_oud = c.get(reverse("studio:step", args=[oud.uid, "fotos"])).content.decode()
            tekst_nieuw = c.get(reverse("studio:step", args=[nieuw.uid, "fotos"])).content.decode()
        self.assertNotIn("Inbegrepen", tekst_oud)
        self.assertNotIn("Dit zit in de prijs van je kaart", tekst_oud)
        self.assertIn("Inbegrepen", tekst_nieuw)


    def _editorteksten(self, client, inv):
        """Wat de editor over de onderdelen belooft: de labels en de uitleg bij eigen muziek, per stap."""
        teksten = {}
        for stap in ("fotos", "aanmelden", "stijl"):
            html = client.get(reverse("studio:step", args=[inv.uid, stap])).content.decode()
            teksten[stap] = (re.findall(r'<span class="badge">([^<]*)</span>', html), re.findall(r'class="info__tekst"[^>]*>([^<]*)<', html))
        return teksten

    def _oude_bestelling_blijft_gelijk(self, inv, owner, code):
        order = Order.objects.get(invitation=inv)
        inv.refresh_from_db()
        voor = (order.total_cents, order.package_code, order.package_name, order.availability_months, sorted(order.features), order.ends_at,
                sorted(inv.features or []), [(l.code, l.unit_price_cents, l.total_cents) for l in order.lines.all()])
        c = Client()
        c.force_login(owner)
        editor_voor = self._editorteksten(c, inv)
        with V2:
            order.refresh_from_db()
            inv.refresh_from_db()
            na = (order.total_cents, order.package_code, order.package_name, order.availability_months, sorted(order.features), order.ends_at,
                  sorted(inv.features or []), [(l.code, l.unit_price_cents, l.total_cents) for l in order.lines.all()])
            editor_na = self._editorteksten(c, inv)
        self.assertEqual(voor, na, "functies, rechten, prijs en looptijd van de bestelling zijn niet veranderd")
        self.assertEqual(order.package_code, code)
        self.assertEqual(editor_voor, editor_na, "de editor zegt met de nieuwe prijzen aan hetzelfde als daarvoor")
        for stap, (labels, uitleg) in editor_na.items():
            self.assertNotIn("Inbegrepen", labels, stap)
            self.assertFalse(any("zit in de prijs van je kaart" in u for u in uitleg), stap)
        return voor, editor_na

    def test_een_bestaande_compleet_bestelling_behoudt_functies_rechten_en_looptijd(self):
        owner = self.make_customer()
        inv = self.make_invitation(owner=owner, template="liefde-op-papier", occasion="bruiloft")
        with override_settings(PRICING_V2=False):
            self.pay(inv, owner, package="compleet")
        inv.package_code = "compleet"
        inv.save(update_fields=["package_code"])
        voor, editor = self._oude_bestelling_blijft_gelijk(inv, owner, "compleet")
        self.assertTrue(any(labels for labels, _ in editor.values()), "de editor toont labels (de controle is niet leeg)")
        self.assertEqual(voor[3], 12, "Compleet blijft 12 maanden online")
        self.assertTrue({"gallery", "music", "story", "extra_questions"} <= set(voor[4]), "de functies van Compleet blijven bestaan")
        c = Client()
        c.force_login(owner)
        with V2:
            self.assertIn("In Compleet", c.get(reverse("studio:step", args=[inv.uid, "fotos"])).content.decode())

    def test_een_bestaande_wenskaart_behoudt_functies_rechten_en_looptijd(self):
        from invitations.services import save_draft

        owner = self.make_customer()
        inv = create_draft(occasion="bruiloft", template=ontwerp("liefde-op-papier"), owner=owner, soort="wenskaart")
        content = dict(inv.draft_content)
        content["welcome_text"] = "Gefeliciteerd!"
        content["names"] = {"partner_1": "Anna", "partner_2": "Bram"}
        inv = save_draft(inv, expected_rev=None, content=content, user=owner)
        with override_settings(PRICING_V2=False):
            self.pay(inv, owner)
        order = Order.objects.get(invitation=inv)
        self.assertFalse(order.package_code.startswith(("basis", "luxe", "special")), "dit is een wenskaart uit de oude structuur")
        voor, _ = self._oude_bestelling_blijft_gelijk(inv, owner, order.package_code)
        self.assertEqual(voor[3], 6, "een oude wenskaart blijft 6 maanden online")
        self.assertFalse({"gallery", "music", "story", "extra_questions"} & set(voor[4]), "een wenskaart kreeg geen extra functies")


class Pagina(NieuwePrijzen):
    def test_ontwerppagina_toont_indeling_en_prijs_per_gelegenheid(self):
        c = Client()
        html = c.get("/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft").content.decode()
        self.assertIn("Luxe € 59,95", html)
        self.assertIn("12 maanden online", html)
        self.assertIn('data-prijs-wenskaart="Luxe € 19,95"', html)
        html = c.get("/ontwerpen/liefde-op-papier/?gelegenheid=verjaardag").content.decode()
        self.assertIn("Luxe € 34,95", html)
        html = c.get("/ontwerpen/monogram/?gelegenheid=bruiloft").content.decode()
        self.assertIn("Basis € 29,95", html)
        self.assertIn("12 maanden online", html)
        self.assertNotIn("6 maanden", html)

    def test_prijzenpagina_toont_alleen_wat_echt_te_kiezen_is(self):
        html = Client().get("/prijzen/").content.decode()
        for tekst in ("Kerstkaart / nieuwjaarswens", "Trouwuitnodiging", "€ 89,95", "€ 24,95", "€ 69,00", "€ 19,95"):
            self.assertIn(tekst, html)
        kerstrij = re.search(r"<tr><th[^>]*>Kerstkaart / nieuwjaarswens.*?</tr>", html.replace("\n", ""))
        self.assertIsNotNone(kerstrij)
        self.assertNotIn("9,95", kerstrij.group(0).replace("49,95", "").replace("€ 24,95", ""), "Kerst Basis bestaat niet (geen ontwerp) en wordt niet getoond")
        self.assertNotIn("Essentieel", html)
        self.assertNotIn("Compleet", html)
        self.assertNotIn("Geboortekaart", html)
        self.assertNotIn("Save the date", html)

    def test_studio_toont_per_kaart_de_prijs(self):
        c = Client()
        html = c.get(reverse("studio:start") + "?gelegenheid=kerst").content.decode()
        self.assertIn("Luxe € 24,95", html)
        self.assertIn("Special € 49,95", html)

    def test_bestellen_toont_een_regel_geen_pakketkeuze_en_geen_extra_opties(self):
        owner = self.make_customer()
        inv = vul(self.make_invitation(owner=owner, template="winterlicht", occasion="kerst"), owner)
        c = Client()
        c.force_login(owner)
        html = c.get(reverse("studio:step", args=[inv.uid, "bestellen"])).content.decode()
        self.assertIn("€ 24,95", html)
        self.assertIn("Jouw kaart", html)
        for tekst in ("Upgrade", "Extra opties", "Los bij te kopen", "Essentieel", "Compleet", "Liever "):
            self.assertNotIn(tekst, html, tekst)
        self.assertIn("12 maanden online", html)
        self.assertNotIn("data-prijs-bijgewerkt", html)

    def test_een_concept_van_voor_de_invoering_ziet_de_nieuwe_prijs_expliciet(self):
        owner = self.make_customer()
        inv = vul(self.make_invitation(owner=owner, template="winterlicht", occasion="kerst"), owner)
        inv.package_code = "essentieel"
        inv.save(update_fields=["package_code"])
        c = Client()
        c.force_login(owner)
        with override_settings(PRICING_V2_SINCE="2099-01-01T00:00:00+00:00"):
            html = c.get(reverse("studio:step", args=[inv.uid, "bestellen"])).content.decode()
        self.assertIn("data-prijs-bijgewerkt", html)
        self.assertIn("De prijs van dit ontwerp is bijgewerkt", html)
        self.assertIn("Eerder zag je Essentieel € 39,00", html)
        self.assertIn("Luxe: € 24,95", html)
        with override_settings(PRICING_V2_SINCE="2000-01-01T00:00:00+00:00"):
            self.assertNotIn("data-prijs-bijgewerkt", c.get(reverse("studio:step", args=[inv.uid, "bestellen"])).content.decode())
        with override_settings(PRICING_V2_SINCE=""):
            self.assertNotIn("data-prijs-bijgewerkt", c.get(reverse("studio:step", args=[inv.uid, "bestellen"])).content.decode())

    def test_beheer_toont_dat_de_nieuwe_structuur_actief_is(self):
        staff = self.make_staff()
        c = Client()
        c.force_login(staff)
        html = c.get(reverse("beheer:pricing")).content.decode()
        self.assertIn("Actieve prijsstructuur", html)
        self.assertIn("worden voor nieuwe bestellingen niet gebruikt", html)


@override_settings(PRICING_V2=False)
class UitStaatAlsVoorheen(VaylideTestCase):
    def test_zonder_schakelaar_geen_nieuwe_elementen(self):
        html = Client().get("/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft").content.decode()
        self.assertNotIn("data-prijs-tekst", html)
        html = Client().get("/prijzen/").content.decode()
        self.assertIn("Essentieel", html)
        self.assertNotIn("Prijs per soort kaart", html)

    @unittest.skipIf(settings.PRICING_V2, "de teksten zijn in dit proces al vervangen")
    def test_zinnen_die_de_nieuwe_structuur_vervangt_bestaan_nog_in_de_teksten(self):
        """Bewaakt dat core/content.py niet ongemerkt uit de pas loopt met de vervangingen voor de nieuwe structuur."""
        from core import content

        alle = set()

        def loop(obj):
            if isinstance(obj, str):
                alle.add(obj)
            elif isinstance(obj, (list, tuple)):
                for x in obj:
                    loop(x)
            elif isinstance(obj, dict):
                for v in obj.values():
                    loop(v)

        for naam in dir(content):
            if naam.isupper():
                loop(getattr(content, naam))
        ontbreekt = [k[:70] for k in content._v2_vervangingen() if k not in alle]
        self.assertEqual(ontbreekt, [], "deze zinnen staan niet meer (ongewijzigd) in core/content.py: werk _v2_vervangingen bij")


@unittest.skipUnless(settings.PRICING_V2, "alleen als het proces met VIERLIEF_PRICING_V2=1 is gestart (de teksten worden bij het laden van de site aangepast)")
class TekstenOpDeHeleSite(NieuwePrijzen):
    PAGINAS = ["/", "/prijzen/", "/ontwerpen/", "/zo-werkt-het/", "/veelgestelde-vragen/", "/inspiratie/", "/digitale-trouwkaarten/", "/digitale-kerstkaarten/",
               "/digitale-verjaardagsuitnodigingen/", "/digitale-zakelijke-uitnodigingen/", "/digitale-uitnodiging-maken/",
               "/ontwerpen/winterlicht/?gelegenheid=kerst", "/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft", "/ontwerpen/kerstbol/?gelegenheid=kerst", "/maken/?gelegenheid=bruiloft"]

    def test_geen_pakketten_meer_en_overal_twee_decimalen(self):
        c = Client()
        for pad in self.PAGINAS:
            r = c.get(pad)
            self.assertEqual(r.status_code, 200, pad)
            html = r.content.decode()
            zichtbaar = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S)
            self.assertNotRegex(zichtbaar, r"\bEssentieel\b|\bCompleet\b", pad)   # (de voorwaarden en de privacyverklaring staan hier bewust niet bij)
            self.assertNotIn("extra optie", zichtbaar.lower(), pad)
            self.assertNotIn("{prijszin}", html, pad)
            self.assertNotIn("{vanaf", html, pad)
            fout = re.findall(r"€\s?\d+(?:\.\d{3})*(?!\d|,\d{2})", re.sub(r"<[^>]+>", " ", zichtbaar))
            self.assertEqual(fout, [], f"bedragen zonder twee decimalen op {pad}")

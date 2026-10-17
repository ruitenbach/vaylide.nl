"""Automatische aanbiedingen (app kortingen, settings.OFFERS_ENABLED) en de prijshistorie achter een doorgestreepte prijs.

Wat deze tests bewaken:
- standaard uit: dan verandert er nergens iets (kaart, ontwerppagina, offerte, bestelling, Beheer), ook niet als de kortingscodes wel aan staan;
- de twee schakelaars (codes, aanbiedingen) werken onafhankelijk van elkaar;
- één rekenpad: wat kaart, ontwerppagina, Studio-keuze, bon, bestelling, betaling, Mollie en mail tonen is dezelfde actieprijs, voor elk ontwerp en elke gelegenheid;
- de vaste Basis/Luxe/Special-prijzen blijven ongemoeid;
- aanbiedingen stapelen niet met elkaar en niet met een kortingscode: de voordeligste geldt, en de klant krijgt te horen welke;
- een aanbieding die tijdens het bestellen start of verloopt leidt nooit stilletjes tot een ander betaalbedrag;
- een doorgestreepte referentieprijs staat er alleen als de prijshistorie de voorgaande 30 dagen aantoonbaar dekt; bij twijfel alleen de actieprijs;
- bestaande bestellingen veranderen niet."""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.db import IntegrityError, transaction
from django.test import Client, override_settings
from django.utils import timezone

from catalog import prijzen
from catalog.models import Template, format_euro
from kortingen import aanbiedingen as a
from kortingen import services as k
from kortingen.models import DiscountCode, DiscountRedemption, Offer, PriceStand
from orders.models import Order, Payment
from orders.pricing import build_quote
from orders.providers import MollieProvider
from orders.services import CheckoutError, PriceChanged, start_checkout
from processing.models import OutboundEmail

from .helpers import VaylideTestCase

SLUG = "liefde-op-papier"
GELEGENHEID = "bruiloft"


def maak_aanbieding(naam="Herfst", *, kind="percent", percent=20, amount=None, start=None, einde=None, hele=True, templates=(), **kw) -> Offer:
    now = timezone.now()
    offer = Offer.objects.create(
        name=naam, kind=kind, percent=percent if kind == "percent" else None, amount_cents=amount if kind == "fixed" else None,
        starts_at=start or now - timedelta(days=1), ends_at=einde or now + timedelta(days=10), whole_collection=hele, **kw)
    if templates:
        offer.templates.set(templates)
    return offer


class Basis(VaylideTestCase):
    aanbiedingen = True
    codes = False

    def setUp(self):
        super().setUp()
        o = override_settings(PRICING_V2=True, OFFERS_ENABLED=self.aanbiedingen, DISCOUNTS_ENABLED=self.codes, TEST_MODE=True)
        o.enable()
        self.addCleanup(o.disable)
        self.klant = self.make_customer("klant@example.com")
        self.inv = self.make_invitation(owner=self.klant, template=SLUG, occasion=GELEGENHEID)
        self.template = Template.objects.get(slug=SLUG)
        self.gewoon = prijzen.prijs_cents(self.template, GELEGENHEID)

    def bestel(self, inv=None, code="", verwacht=None):
        with self.captureOnCommitCallbacks(execute=True):
            return start_checkout(inv or self.inv, user=self.klant, package_code="luxe", optional_codes=[], terms_accepted=True,
                                  delivery_consent=True, service_consent=True, discount_code=code, expected_total_cents=verwacht)

    def zet_historie(self, dagen=45, cents=None):
        """Maakt de prijshistorie van het testontwerp `dagen` dagen oud."""
        PriceStand.objects.all().delete()
        PriceStand.objects.create(key=a.history_key(self.template, GELEGENHEID), price_cents=cents or self.gewoon, since=timezone.now() - timedelta(days=dagen))


class StandaardUit(Basis):
    aanbiedingen = False

    def test_zonder_schakelaar_geen_aanbieding_in_offerte_kaart_of_beheer(self):
        maak_aanbieding()
        self.assertIsNone(a.beste(self.template, GELEGENHEID))
        quote = build_quote(self.inv.draft_content, None, None, template_version=self.inv.template_version, occasion=GELEGENHEID)
        self.assertEqual(quote.total_cents, self.gewoon)
        self.assertIsNone(quote.offer)
        self.assertEqual(len(quote.lines), 1)
        for url in (f"/ontwerpen/?gelegenheid={GELEGENHEID}", f"/ontwerpen/{SLUG}/", "/"):
            self.assertNotContains(Client().get(url), "Aanbieding")
        staff = Client()
        staff.force_login(self.make_staff() if hasattr(self, "make_staff") else self.klant)
        self.assertEqual(staff.get("/beheer/aanbiedingen/").status_code in (302, 403, 404), True)

    def test_bestelling_zonder_schakelaar_betaalt_de_gewone_prijs(self):
        maak_aanbieding()
        payment = self.bestel()
        self.assertEqual(payment.order.total_cents, self.gewoon)
        self.assertEqual(payment.order.discount_cents, 0)
        self.assertIsNone(payment.order.discount_offer)

    def test_codes_aan_en_aanbiedingen_uit_blijft_zonder_aanbieding(self):
        maak_aanbieding()
        with override_settings(DISCOUNTS_ENABLED=True):
            DiscountCode.objects.create(code="ZOMER10", kind="percent", percent=10)
            order = self.bestel(code="ZOMER10").order
        self.assertEqual(order.discount_cents, (self.gewoon * 10 + 50) // 100)
        self.assertIsNone(order.discount_offer)
        self.assertEqual(order.discount_code_text, "ZOMER10")


class Bereik(Basis):
    def test_hele_collectie_percentage(self):
        res = a.beste(self.template, GELEGENHEID)
        maak_aanbieding(percent=20)
        res = a.beste(self.template, GELEGENHEID)
        self.assertEqual(res.discount_cents, (self.gewoon * 20 + 50) // 100)
        self.assertEqual(res.price_cents, self.gewoon - res.discount_cents)

    def test_vast_bedrag_en_ondergrens(self):
        maak_aanbieding(kind="fixed", amount=500)
        self.assertEqual(a.beste(self.template, GELEGENHEID).discount_cents, 500)
        Offer.objects.all().delete()
        maak_aanbieding(kind="fixed", amount=10 ** 7)
        res = a.beste(self.template, GELEGENHEID)
        self.assertEqual(res.price_cents, 100)      # nooit onder € 1,00

    def test_alleen_gekozen_ontwerpen(self):
        ander = next(t for t in Template.objects.exclude(pk=self.template.pk) if GELEGENHEID in t.occasions and prijzen.prijs_cents(t, GELEGENHEID) is not None)
        maak_aanbieding(hele=False, templates=[ander])
        self.assertIsNone(a.beste(self.template, GELEGENHEID))
        self.assertIsNotNone(a.beste(ander, GELEGENHEID))

    def test_gelegenheid_en_indeling(self):
        maak_aanbieding(occasions=["verjaardag"])
        self.assertIsNone(a.beste(self.template, GELEGENHEID))
        Offer.objects.all().delete()
        maak_aanbieding(tiers=["special"] if prijzen.tier(self.template) != "special" else ["basis"])
        self.assertIsNone(a.beste(self.template, GELEGENHEID))
        Offer.objects.all().delete()
        maak_aanbieding(tiers=[prijzen.tier(self.template)])
        self.assertIsNotNone(a.beste(self.template, GELEGENHEID))

    def test_nog_niet_gestart_verlopen_en_uitgezet(self):
        now = timezone.now()
        maak_aanbieding("later", start=now + timedelta(days=1), einde=now + timedelta(days=5))
        maak_aanbieding("voorbij", start=now - timedelta(days=9), einde=now - timedelta(seconds=1))
        maak_aanbieding("uit", is_active=False)
        self.assertIsNone(a.beste(self.template, GELEGENHEID))

    def test_voordeligste_aanbieding_wint_geen_stapeling(self):
        maak_aanbieding("klein", percent=10)
        groot = maak_aanbieding("groot", percent=30)
        res = a.beste(self.template, GELEGENHEID)
        self.assertEqual(res.offer, groot)
        quote = build_quote(self.inv.draft_content, None, None, template_version=self.inv.template_version, occasion=GELEGENHEID)
        self.assertEqual(len([l for l in quote.lines if l.is_offer]), 1)
        self.assertEqual(quote.total_cents, res.price_cents)

    def test_einddatum_is_verplicht_en_na_het_begin(self):
        now = timezone.now()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Offer.objects.create(name="x", kind="percent", percent=10, starts_at=now, ends_at=None, whole_collection=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Offer.objects.create(name="x", kind="percent", percent=10, starts_at=now, ends_at=now - timedelta(days=1), whole_collection=True)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Offer.objects.create(name="x", kind="percent", percent=100, starts_at=now, ends_at=now + timedelta(days=1), whole_collection=True)

    def test_geen_aanbieding_in_de_oude_prijsstructuur(self):
        maak_aanbieding()
        with override_settings(PRICING_V2=False):
            self.assertIsNone(a.beste(self.template, GELEGENHEID))


class EenRekenpad(Basis):
    def test_bestelling_betaling_mollie_regels_en_mail_hebben_hetzelfde_bedrag(self):
        res_offer = maak_aanbieding(percent=20)
        verstuurd = {}

        def nep(self_, methode, pad, body=None):
            verstuurd.update(body or {})
            return {"id": "tr_1", "_links": {"checkout": {"href": "https://pay.example/1"}}}

        with override_settings(PAYMENT_PROVIDER="mollie", MOLLIE_API_KEY="test_x"):
            with mock.patch.object(MollieProvider, "_request", nep):
                payment = self.bestel()
        order = payment.order
        korting = (self.gewoon * 20 + 50) // 100
        self.assertEqual(order.subtotal_cents, self.gewoon)
        self.assertEqual(order.discount_cents, korting)
        self.assertEqual(order.total_cents, self.gewoon - korting)
        self.assertEqual(order.discount_offer, res_offer)
        self.assertEqual(order.discount_offer_text, "Herfst")
        self.assertIsNone(order.discount_code)
        self.assertEqual(sum(l.total_cents for l in order.lines.all()), order.total_cents)
        self.assertEqual(payment.amount_cents, order.total_cents)
        self.assertEqual(verstuurd["amount"]["value"], f"{Decimal(order.total_cents) / 100:.2f}")
        regel = order.lines.get(code=f"korting:aanbieding:{res_offer.pk}")
        self.assertEqual(regel.description, "Aanbieding Herfst")
        self.assertFalse(DiscountRedemption.objects.filter(order=order).exists())      # een aanbieding heeft geen gebruiksteller

    def test_bevestigingsmail_en_bon(self):
        maak_aanbieding(percent=20)
        payment = self.bestel()
        self.provider_says(payment, Payment.Status.PAID)
        order = Order.objects.get(pk=payment.order_id)
        mail = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        for tekst in (mail.body_text, mail.body_html):
            self.assertIn("Aanbieding Herfst", tekst)
            self.assertIn(order.total_display, tekst)
            self.assertIn(format_euro(order.subtotal_cents), tekst)
        c = Client()
        c.force_login(self.klant)
        self.assertContains(c.get(f"/bestelling/{order.uid}/"), "Aanbieding Herfst")

    def test_weergave_is_gelijk_aan_de_offerte_voor_alle_ontwerpen_gelegenheden_en_soorten(self):
        maak_aanbieding(percent=15)
        kleine = maak_aanbieding("vast", kind="fixed", amount=250, hele=False, templates=list(Template.objects.all()[:5]))
        telling = 0
        for template in Template.objects.filter(is_active=True, current_version__isnull=False).select_related("current_version"):
            for occasion in template.occasions:
                for soort in ("", "wenskaart"):
                    info = a.prijs(template, occasion, soort)
                    if info is None:
                        continue
                    content = {"soort": soort} if soort else {}
                    quote = build_quote(content, None, None, template_version=template.current_version, occasion=occasion)
                    self.assertEqual(info["nu_cents"], quote.total_cents, (template.slug, occasion, soort))
                    self.assertEqual(info["cents"], quote.subtotal_cents, (template.slug, occasion, soort))
                    telling += 1
        self.assertGreater(telling, 50)
        self.assertTrue(kleine.pk)

    def test_vaste_prijzen_blijven_ongemoeid(self):
        before = {(r, t): prijzen.PRIJZEN[r][t] for r in prijzen.PRIJZEN for t in range(3)}
        maak_aanbieding(percent=50)
        a.beste(self.template, GELEGENHEID)
        self.assertEqual(before, {(r, t): prijzen.PRIJZEN[r][t] for r in prijzen.PRIJZEN for t in range(3)})
        self.assertEqual(prijzen.prijs_cents(self.template, GELEGENHEID), self.gewoon)


class AanbiedingEnCode(Basis):
    codes = True

    def setUp(self):
        super().setUp()
        self.c = Client()
        self.c.force_login(self.klant)
        self.url = f"/maken/{self.inv.uid}/bestellen/"

    def post(self, **extra):
        data = {"package": "luxe", "terms": "on", "direct_leveren": "on", "online_dienst": "on"}
        data.update(extra)
        return self.c.post(self.url, data)

    def test_code_voordeliger_vervangt_de_aanbieding(self):
        maak_aanbieding(percent=10)
        DiscountCode.objects.create(code="GROOT", kind="percent", percent=30)
        order = self.bestel(code="GROOT").order
        self.assertEqual(order.discount_cents, (self.gewoon * 30 + 50) // 100)
        self.assertEqual(order.discount_code_text, "GROOT")
        self.assertIsNone(order.discount_offer)
        self.assertEqual([l.code for l in order.lines.all() if l.total_cents < 0], ["korting:GROOT"])
        self.assertEqual(order.redemption.state, "reserved")

    def test_aanbieding_voordeliger_gebruikt_de_code_niet(self):
        offer = maak_aanbieding(percent=30)
        DiscountCode.objects.create(code="KLEIN", kind="percent", percent=10)
        order = self.bestel(code="KLEIN").order
        self.assertEqual(order.discount_offer, offer)
        self.assertEqual(order.discount_cents, (self.gewoon * 30 + 50) // 100)
        self.assertEqual(order.discount_code_text, "")
        self.assertFalse(DiscountRedemption.objects.filter(order=order).exists())    # de code is niet verbruikt

    def test_gelijk_wint_de_aanbieding(self):
        offer = maak_aanbieding(percent=20)
        DiscountCode.objects.create(code="GELIJK", kind="percent", percent=20)
        order = self.bestel(code="GELIJK").order
        self.assertEqual(order.discount_offer, offer)
        self.assertEqual(DiscountRedemption.objects.count(), 0)

    def test_bestelstap_zegt_welke_korting_gebruikt_wordt(self):
        maak_aanbieding(percent=30)
        DiscountCode.objects.create(code="KLEIN", kind="percent", percent=10)
        antwoord = self.post(actie="code-toepassen", kortingscode="KLEIN")
        self.assertContains(antwoord, "Aanbieding Herfst")
        self.assertContains(antwoord, "voordeliger dan je code")
        gewoon = (self.gewoon * 70 + 50) // 100
        self.assertContains(antwoord, f"Bestellen en betalen {format_euro(self.gewoon - (self.gewoon * 30 + 50) // 100)}")
        DiscountCode.objects.create(code="GROOT", kind="percent", percent=50)
        antwoord = self.post(actie="code-toepassen", kortingscode="GROOT")
        self.assertContains(antwoord, "Kortingscode GROOT")
        self.assertNotContains(antwoord, "Aanbieding Herfst</td>")
        self.assertContains(antwoord, "voordeliger dan de aanbieding Herfst")
        self.assertTrue(gewoon)

    def test_bon_met_aanbieding_toont_codeveld_en_geen_verwijderknop_voor_de_aanbieding(self):
        maak_aanbieding(percent=20)
        page = self.c.get(self.url)
        self.assertContains(page, "Aanbieding Herfst")
        self.assertContains(page, "Heb je een kortingscode?")
        self.assertNotContains(page, "code-verwijderen")

    def test_aanbieding_werkt_ook_met_codes_uit(self):
        maak_aanbieding(percent=20)
        with override_settings(DISCOUNTS_ENABLED=False):
            page = self.c.get(self.url)
            self.assertContains(page, "Aanbieding Herfst")
            self.assertNotContains(page, "Heb je een kortingscode?")
            self.assertEqual(self.bestel().order.discount_cents, (self.gewoon * 20 + 50) // 100)


class VerlopenTijdensBestellen(Basis):
    def setUp(self):
        super().setUp()
        self.c = Client()
        self.c.force_login(self.klant)
        self.url = f"/maken/{self.inv.uid}/bestellen/"

    def post(self, verwacht, **extra):
        data = {"package": "luxe", "terms": "on", "direct_leveren": "on", "online_dienst": "on", "actie": "betalen", "verwacht": str(verwacht)}
        data.update(extra)
        return self.c.post(self.url, data)

    def test_pagina_bevat_het_verwachte_bedrag(self):
        offer = maak_aanbieding(percent=20)
        res = a.beste(self.template, GELEGENHEID)
        self.assertContains(self.c.get(self.url), f'name="verwacht" value="{res.price_cents}"')
        self.assertTrue(offer.pk)

    def test_verlopen_aanbieding_geeft_een_melding_en_geen_bestelling(self):
        offer = maak_aanbieding(percent=20)
        verwacht = a.beste(self.template, GELEGENHEID).price_cents
        offer.ends_at = timezone.now() - timedelta(seconds=1)
        offer.save()
        antwoord = self.post(verwacht)
        self.assertContains(antwoord, "Het bedrag is gewijzigd")
        self.assertContains(antwoord, format_euro(verwacht))
        self.assertContains(antwoord, f'name="verwacht" value="{self.gewoon}"')
        self.assertFalse(Order.objects.filter(invitation=self.inv).exists())
        self.assertFalse(Payment.objects.exists())

    def test_na_bevestigen_van_het_nieuwe_bedrag_lukt_bestellen(self):
        offer = maak_aanbieding(percent=20)
        verwacht = a.beste(self.template, GELEGENHEID).price_cents
        Offer.objects.filter(pk=offer.pk).update(ends_at=timezone.now() - timedelta(seconds=1))
        self.post(verwacht)
        antwoord = self.post(self.gewoon)
        self.assertEqual(antwoord.status_code, 302)
        self.assertEqual(Order.objects.get(invitation=self.inv).total_cents, self.gewoon)

    def test_net_gestarte_aanbieding_wordt_ook_niet_stilletjes_toegepast(self):
        verwacht = self.gewoon
        maak_aanbieding(percent=20)
        antwoord = self.post(verwacht)
        self.assertContains(antwoord, "Het bedrag is gewijzigd")
        self.assertFalse(Order.objects.filter(invitation=self.inv).exists())

    def test_start_checkout_weigert_zelf_ook(self):
        offer = maak_aanbieding(percent=20)
        verwacht = a.beste(self.template, GELEGENHEID).price_cents
        Offer.objects.filter(pk=offer.pk).update(ends_at=timezone.now() - timedelta(seconds=1))
        with self.assertRaises(PriceChanged):
            self.bestel(verwacht=verwacht)
        self.assertFalse(Order.objects.filter(invitation=self.inv).exists())

    def test_zonder_verwacht_veld_blijft_het_oude_gedrag(self):
        self.assertEqual(self.bestel().order.total_cents, self.gewoon)

    def test_bestaande_bestelling_houdt_zijn_bedrag_als_de_aanbieding_daarna_verloopt(self):
        offer = maak_aanbieding(percent=20)
        order = self.bestel().order
        totaal = order.total_cents
        Offer.objects.filter(pk=offer.pk).update(ends_at=timezone.now() - timedelta(days=1))
        order.refresh_from_db()
        self.assertEqual(order.total_cents, totaal)
        self.assertLess(totaal, self.gewoon)


class Prijshistorie(Basis):
    def test_sync_is_idempotent_en_legt_wijzigingen_vast(self):
        PriceStand.objects.all().delete()
        eerste = a.sync_history()
        self.assertGreater(eerste, 50)
        self.assertEqual(a.sync_history(), 0)
        key = a.history_key(self.template, GELEGENHEID)
        with mock.patch.dict(prijzen.PRIJZEN, {"bruiloft": (1, 2, 3)}):
            with mock.patch.object(prijzen, "prijs_cents", lambda t, o, s="": 4321 if a.history_key(t, o, s) == key else None):
                self.assertEqual(a.sync_history(), 1)
        rows = list(PriceStand.objects.filter(key=key).order_by("since"))
        self.assertEqual(len(rows), 2)
        self.assertIsNotNone(rows[0].until)
        self.assertIsNone(rows[1].until)
        self.assertEqual(rows[1].price_cents, 4321)

    def test_geen_referentie_zonder_dekkende_historie(self):
        self.zet_historie(dagen=10)
        maak_aanbieding(start=timezone.now() - timedelta(days=1))
        res = a.beste(self.template, GELEGENHEID)
        self.assertIsNone(res.reference_cents)
        self.assertIn("prijshistorie begint pas", res.reference_reason)

    def test_geen_referentie_zonder_enige_historie(self):
        PriceStand.objects.all().delete()
        maak_aanbieding()
        self.assertIsNone(a.beste(self.template, GELEGENHEID).reference_cents)

    def test_referentie_met_dekkende_historie_is_de_gewone_prijs(self):
        self.zet_historie(dagen=60)
        maak_aanbieding(start=timezone.now() - timedelta(days=1))
        res = a.beste(self.template, GELEGENHEID)
        self.assertEqual(res.reference_cents, self.gewoon)
        self.assertGreater(res.reference_cents, res.price_cents)

    def test_referentie_is_de_laagste_prijs_van_de_voorgaande_periode(self):
        PriceStand.objects.all().delete()
        key = a.history_key(self.template, GELEGENHEID)
        now = timezone.now()
        PriceStand.objects.create(key=key, price_cents=self.gewoon - 300, since=now - timedelta(days=60), until=now - timedelta(days=20))
        PriceStand.objects.create(key=key, price_cents=self.gewoon, since=now - timedelta(days=20))
        maak_aanbieding(start=now - timedelta(days=1), percent=20)
        self.assertEqual(a.beste(self.template, GELEGENHEID).reference_cents, self.gewoon - 300)

    def test_referentie_vervalt_als_de_lage_prijs_even_laag_is_als_de_actieprijs(self):
        PriceStand.objects.all().delete()
        key = a.history_key(self.template, GELEGENHEID)
        now = timezone.now()
        PriceStand.objects.create(key=key, price_cents=100, since=now - timedelta(days=60), until=now - timedelta(days=20))
        PriceStand.objects.create(key=key, price_cents=self.gewoon, since=now - timedelta(days=20))
        maak_aanbieding(start=now - timedelta(days=1), percent=20)
        self.assertIsNone(a.beste(self.template, GELEGENHEID).reference_cents)

    def test_een_eerdere_aanbieding_verlaagt_de_referentie_van_de_volgende(self):
        self.zet_historie(dagen=90)
        now = timezone.now()
        maak_aanbieding("eerste", percent=30, start=now - timedelta(days=15), einde=now - timedelta(days=3))
        tweede = maak_aanbieding("tweede", percent=20, start=now - timedelta(days=1))
        res = a.beste(self.template, GELEGENHEID)
        self.assertEqual(res.offer, tweede)
        self.assertIsNone(res.reference_cents)      # de prijs van de eerste aanbieding was al lager dan deze actieprijs

    def test_een_eerdere_kleinere_aanbieding_geeft_een_lagere_referentie_dan_de_gewone_prijs(self):
        self.zet_historie(dagen=90)
        now = timezone.now()
        maak_aanbieding("eerste", percent=10, start=now - timedelta(days=15), einde=now - timedelta(days=3))
        maak_aanbieding("tweede", percent=30, start=now - timedelta(days=1))
        res = a.beste(self.template, GELEGENHEID)
        self.assertEqual(res.reference_cents, self.gewoon - (self.gewoon * 10 + 50) // 100)

    def test_achterlopende_historie_geeft_geen_referentie(self):
        self.zet_historie(dagen=90, cents=self.gewoon + 500)
        maak_aanbieding()
        self.assertIsNone(a.beste(self.template, GELEGENHEID).reference_cents)

    def test_doorgestreepte_prijs_uitzetten(self):
        self.zet_historie(dagen=60)
        maak_aanbieding(show_reference=False)
        self.assertIsNone(a.beste(self.template, GELEGENHEID).reference_cents)

    def test_geen_automatische_wachttijd_voor_een_nieuw_ontwerp_alleen_de_historie_beslist(self):
        # Een ontwerp zonder (dekkende) historie krijgt wel de aanbieding en actieprijs, alleen geen doorgestreepte prijs.
        PriceStand.objects.all().delete()
        maak_aanbieding()
        res = a.beste(self.template, GELEGENHEID)
        self.assertIsNotNone(res)
        self.assertIsNone(res.reference_cents)


class Weergave(Basis):
    def test_kaart_toont_chip_en_actieprijs_zonder_referentie(self):
        PriceStand.objects.all().delete()
        maak_aanbieding(percent=20)
        res = a.beste(self.template, GELEGENHEID)
        page = Client().get(f"/ontwerpen/?gelegenheid={GELEGENHEID}")
        self.assertContains(page, "design-card__aanbod")
        self.assertContains(page, "Aanbieding")
        self.assertContains(page, res.price_display)
        self.assertNotContains(page, "prijs-oud")
        self.assertNotContains(page, "SALE")

    def test_kaart_en_ontwerppagina_met_referentie(self):
        self.zet_historie(dagen=60)
        maak_aanbieding(percent=20)
        res = a.beste(self.template, GELEGENHEID)
        page = Client().get(f"/ontwerpen/?gelegenheid={GELEGENHEID}")
        self.assertContains(page, f'<s class="prijs-oud"><span class="visually-hidden">Was </span>{res.reference_display}</s>')
        detail = Client().get(f"/ontwerpen/{SLUG}/?gelegenheid={GELEGENHEID}")
        self.assertContains(detail, "detail-prijs--aanbieding")
        self.assertContains(detail, res.reference_display)
        self.assertContains(detail, res.price_display)
        self.assertContains(detail, "Aanbieding t/m")
        self.assertContains(detail, 'data-prijs-variant="wenskaart" hidden')

    def test_einddatum_staat_niet_op_de_kaart(self):
        offer = maak_aanbieding(percent=20)
        page = Client().get(f"/ontwerpen/?gelegenheid={GELEGENHEID}")
        self.assertNotContains(page, "t/m")

    def test_ontwerppagina_zonder_aanbieding_blijft_zoals_voorheen(self):
        detail = Client().get(f"/ontwerpen/{SLUG}/?gelegenheid={GELEGENHEID}")
        self.assertContains(detail, "data-prijs-tekst")
        self.assertNotContains(detail, "detail-prijs--aanbieding")

    def test_studio_kaartkeuze_toont_actieprijs(self):
        PriceStand.objects.all().delete()
        maak_aanbieding(percent=20)
        res = a.beste(self.template, GELEGENHEID)
        c = Client()
        c.force_login(self.klant)
        page = c.get(f"/maken/?gelegenheid={GELEGENHEID}")
        self.assertContains(page, res.price_display)
        self.assertContains(page, "prijs-aanbieding")


class BeheerAanbiedingen(Basis):
    def setUp(self):
        super().setUp()
        self.staff = self.make_customer("eigenaar@example.com")
        self.staff.is_staff = True
        self.staff.save()
        self.c = Client()
        self.c.force_login(self.staff)

    def formulier(self, **extra):
        now = timezone.localdate()
        data = {"name": "Winter", "kind": "percent", "percent": "15", "starts_on": now.isoformat(), "ends_on": (now + timedelta(days=7)).isoformat(),
                "scope": "collectie", "show_reference": "on", "is_active": "on"}
        data.update(extra)
        return data

    def test_alleen_voor_beheerders_en_404_met_schakelaar_uit(self):
        self.assertEqual(Client().get("/beheer/aanbiedingen/").status_code, 302)
        klant = Client()
        klant.force_login(self.klant)
        self.assertIn(klant.get("/beheer/aanbiedingen/").status_code, (302, 403, 404))
        self.assertEqual(self.c.get("/beheer/aanbiedingen/").status_code, 200)
        with override_settings(OFFERS_ENABLED=False):
            self.assertEqual(self.c.get("/beheer/aanbiedingen/").status_code, 404)
            self.assertEqual(self.c.post("/beheer/aanbiedingen/nieuw/", self.formulier()).status_code, 404)
        self.assertEqual(Offer.objects.count(), 0)

    def test_aanmaken_met_verplichte_einddatum(self):
        antwoord = self.c.post("/beheer/aanbiedingen/nieuw/", self.formulier(ends_on=""))
        self.assertEqual(antwoord.status_code, 200)
        self.assertEqual(Offer.objects.count(), 0)
        antwoord = self.c.post("/beheer/aanbiedingen/nieuw/", self.formulier())
        self.assertEqual(antwoord.status_code, 302)
        offer = Offer.objects.get()
        self.assertTrue(offer.whole_collection)
        self.assertGreater(offer.ends_at, offer.starts_at)

    def test_validatie_percentage_ontwerpen_en_einddatum(self):
        for extra in ({"percent": "100"}, {"percent": "0"}, {"scope": "ontwerpen"}, {"ends_on": (timezone.localdate() - timedelta(days=1)).isoformat()},
                      {"kind": "fixed", "amount": ""}):
            self.assertEqual(self.c.post("/beheer/aanbiedingen/nieuw/", self.formulier(**extra)).status_code, 200, extra)
        self.assertEqual(Offer.objects.count(), 0)

    def test_gestarte_aanbieding_is_vergrendeld_maar_einddatum_kan_wijzigen(self):
        offer = maak_aanbieding(percent=20)
        nieuw = (timezone.localdate() + timedelta(days=30)).isoformat()
        self.c.post(f"/beheer/aanbiedingen/{offer.pk}/", self.formulier(percent="50", ends_on=nieuw, name="Nieuw"))
        offer.refresh_from_db()
        self.assertEqual(offer.percent, 20)         # vergrendeld
        self.assertEqual(offer.name, "Nieuw")
        self.assertEqual(timezone.localtime(offer.ends_at).date().isoformat(), nieuw)

    def test_nu_stoppen_laat_bestaande_bestellingen_ongemoeid(self):
        offer = maak_aanbieding(percent=20)
        order = self.bestel().order
        totaal = order.total_cents
        self.assertEqual(self.c.post(f"/beheer/aanbiedingen/{offer.pk}/stoppen/").status_code, 302)
        self.assertIsNone(a.beste(self.template, GELEGENHEID))
        order.refresh_from_db()
        self.assertEqual(order.total_cents, totaal)
        self.assertEqual(self.c.get(f"/beheer/bestellingen/{order.uid}/").status_code, 200)
        self.assertContains(self.c.get(f"/beheer/bestellingen/{order.uid}/"), "Aanbieding")

    def test_overzicht_en_bewerkpagina_tonen_het_referentie_overzicht(self):
        self.zet_historie(dagen=60)
        offer = maak_aanbieding(percent=20, hele=False, templates=[self.template], occasions=[GELEGENHEID])
        page = self.c.get(f"/beheer/aanbiedingen/{offer.pk}/")
        self.assertContains(page, "mag een doorgestreepte referentieprijs worden getoond")
        self.assertContains(self.c.get("/beheer/aanbiedingen/"), "Winter" if False else offer.name)

    def test_beide_tabbladen_alleen_met_hun_eigen_schakelaar(self):
        with override_settings(DISCOUNTS_ENABLED=False):
            self.assertNotContains(self.c.get("/beheer/aanbiedingen/"), "Kortingscodes</a>")
            self.assertEqual(self.c.get("/beheer/kortingscodes/").status_code, 404)
        with override_settings(DISCOUNTS_ENABLED=True):
            self.assertContains(self.c.get("/beheer/aanbiedingen/"), "Kortingscodes</a>")

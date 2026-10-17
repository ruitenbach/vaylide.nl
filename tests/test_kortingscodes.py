"""Kortingscodes (app kortingen, settings.DISCOUNTS_ENABLED).

Wat deze tests bewaken:
- de korting wordt aan de serverzijde berekend; bestelling, regels, betaling, Mollie-bedrag, bon en mail hebben exact hetzelfde bedrag;
- het te betalen bedrag wordt nooit negatief en nooit lager dan het minimum van € 1,00; geen 100%;
- verlopen, nog niet geldige, onbekende, uitgezette en opgebruikte codes, en codes buiten hun bereik, worden met een duidelijke melding geweigerd;
- reserveren, definitief maken en vrijgeven (mislukt, verlopen, vervangen); een gebruikte code blijft meetellen na een terugbetaling;
- historische bestellingen en alles zonder code blijven ongewijzigd, ook met de schakelaar aan;
- staat de schakelaar uit (standaard), dan bestaat de functie niet: geen invoerveld, geen Beheeronderdeel, een code wordt niet geaccepteerd.
Alles draait voor de oude pakketten (PRICING_V2 uit) én voor Basis/Luxe/Special (aan)."""
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.db import IntegrityError, transaction
from django.test import Client, override_settings
from django.utils import timezone

from accounts.models import User
from catalog.models import Template, format_euro
from kortingen import services as k
from kortingen.models import DiscountCode, DiscountRedemption, normalize_code
from orders.models import Order, OrderLine, Payment, PaymentEvent
from orders.providers import MollieProvider
from orders.services import CheckoutError, apply_remote_status, create_payment, start_checkout
from orders.providers import RemoteStatus
from processing.models import OutboundEmail

from .helpers import VaylideTestCase

AAN = dict(DISCOUNTS_ENABLED=True)


def maak_code(code="ZOMER10", **kw) -> DiscountCode:
    kw.setdefault("kind", DiscountCode.Kind.PERCENT)
    if kw["kind"] == DiscountCode.Kind.PERCENT:
        kw.setdefault("percent", 10)
    return DiscountCode.objects.create(code=code, **kw)


class KortingBasis(VaylideTestCase):
    v2 = False

    def setUp(self):
        super().setUp()
        for opties in (dict(DISCOUNTS_ENABLED=True, PRICING_V2=self.v2),):
            o = override_settings(**opties)
            o.enable()
            self.addCleanup(o.disable)
        self.klant = self.make_customer("klant@example.com")
        self.inv = self.make_invitation(owner=self.klant)

    def bestel(self, code="ZOMER10", inv=None, user=None):
        with self.captureOnCommitCallbacks(execute=True):
            return start_checkout(inv or self.inv, user=user or self.klant, package_code="essentieel", optional_codes=[], terms_accepted=True,
                                  delivery_consent=True, service_consent=True, discount_code=code)

    @property
    def pakket(self):
        return "luxe" if self.v2 else "essentieel"

    def basisprijs(self):
        with self.captureOnCommitCallbacks(execute=True):
            zonder = start_checkout(self.inv, user=self.klant, package_code="essentieel", optional_codes=[], terms_accepted=True)
        cents = zonder.order.total_cents
        zonder.order.delete()
        return cents


class Berekening(KortingBasis):
    def sub(self, code, subtotal, **kw):
        return k.check_code(code, subtotal_cents=subtotal, template_version=self.inv.template_version, occasion=self.inv.occasion, **kw)

    def test_procent_rondt_af_op_hele_centen_halve_naar_boven(self):
        self.assertEqual(self.sub(maak_code(percent=10), 999).discount_cents, 100)    # 99,9
        self.assertEqual(self.sub(maak_code("TWEE", percent=15), 995).discount_cents, 149)   # 149,25
        self.assertEqual(self.sub(maak_code("DRIE", percent=50), 995).discount_cents, 498)   # 497,5

    def test_vast_bedrag_en_nooit_meer_dan_het_bedrag(self):
        code = maak_code(kind="fixed", amount_cents=500, percent=None)
        self.assertEqual(self.sub(code, 3000).discount_cents, 500)
        groot = maak_code("GROOT", kind="fixed", amount_cents=100000, percent=None)
        result = self.sub(groot, 3000)
        self.assertEqual(3000 - result.discount_cents, 100)    # het minimum € 1,00
        self.assertTrue(result.capped)
        self.assertIn("minimaal € 1,00", result.note)

    def test_nooit_onder_het_minimum_ook_niet_bij_90_procent(self):
        result = self.sub(maak_code(percent=90), 995)
        self.assertEqual(995 - result.discount_cents, 100)
        self.assertTrue(result.capped)
        for subtotal in (1, 50, 100):
            with self.assertRaises(k.DiscountError) as ctx:
                self.sub(maak_code(f"X{subtotal}", percent=10), subtotal)
            self.assertEqual(ctx.exception.reason, "ondergrens")

    def test_geen_gratis_codes_in_de_database_en_niet_via_het_formulier(self):
        for percent in (0, 91, 100):
            with self.assertRaises(IntegrityError), transaction.atomic():
                DiscountCode.objects.create(code=f"P{percent}", kind="percent", percent=percent)
        with self.assertRaises(IntegrityError), transaction.atomic():
            DiscountCode.objects.create(code="NUL", kind="fixed", amount_cents=0)

    def test_het_minimum_komt_uit_de_instelling(self):
        with override_settings(DISCOUNT_MIN_TOTAL_CENTS=500):
            self.assertEqual(995 - self.sub(maak_code(percent=90), 995).discount_cents, 500)

    def test_btw_deel_is_proportioneel_en_klopt_op_centen(self):
        self.assertEqual(k.vat_part_cents(12100), 2100)
        self.assertEqual(k.vat_part_cents(2495), 433)     # 2495 × 21 / 121 = 433,0
        self.assertEqual(k.vat_part_cents(2245), 390)     # 389,6 afgerond
        self.assertEqual(k.vat_part_cents(100, 0), 0)
        # de korting verlaagt het btw-deel naar rato
        voor, na = k.vat_part_cents(2495), k.vat_part_cents(2495 - 250)
        self.assertLess(na, voor)


class Controles(KortingBasis):
    def toets(self, code, subtotal=3000, **kw):
        return k.evaluate(code, subtotal_cents=subtotal, template_version=self.inv.template_version, occasion=self.inv.occasion, **kw)

    def fout(self, code, **kw):
        with self.assertRaises(k.DiscountError) as ctx:
            self.toets(code, **kw)
        return ctx.exception

    def test_onbekend_en_hoofdletters_spaties_streepjes(self):
        maak_code("ZOMER10")
        self.assertEqual(self.fout("NIETBESTAAND").reason, "onbekend")
        self.assertEqual(self.fout("   ").reason, "onbekend")
        for invoer in ("zomer10", " ZOMER 10 ", "zomer-10"):
            self.assertEqual(self.toets(invoer).code.code, "ZOMER10")
        self.assertEqual(normalize_code("a-b c"), "ABC")

    def test_uitgezet_nog_niet_geldig_en_verlopen_met_datum(self):
        maak_code("UIT", is_active=False)
        self.assertEqual(self.fout("UIT").reason, "uitgezet")
        maak_code("LATER", starts_at=timezone.now() + timedelta(days=3))
        self.assertEqual(self.fout("LATER").reason, "nog_niet")
        self.assertIn("geldig vanaf", self.fout("LATER").message)
        maak_code("OUD", ends_at=timezone.now() - timedelta(days=1))
        fout = self.fout("OUD")
        self.assertEqual(fout.reason, "verlopen")
        self.assertIn("Deze code is verlopen op", fout.message)

    def test_einddatum_geldt_tot_het_einde_van_die_dag(self):
        dag = timezone.localdate()
        maak_code("VANDAAG", ends_at=k.end_of_day(dag))
        self.assertEqual(self.toets("VANDAAG").code.code, "VANDAAG")
        maak_code("GISTEREN", ends_at=k.end_of_day(dag - timedelta(days=1)))
        self.assertEqual(self.fout("GISTEREN").reason, "verlopen")

    def test_bereik_gelegenheid_indeling_en_ontwerp(self):
        maak_code("KERST", occasions=["kerst"])
        self.assertEqual(self.fout("KERST").reason, "bereik")        # dit concept is een bruiloft
        maak_code("BRUILOFT", occasions=["bruiloft"])
        self.toets("BRUILOFT")
        maak_code("BASIS", tiers=["basis"])
        self.assertEqual(self.fout("BASIS").reason, "bereik")        # liefde-op-papier is Luxe
        maak_code("LUXE", tiers=["luxe"])
        self.toets("LUXE")
        eigen = maak_code("DEZE")
        eigen.templates.add(self.inv.template_version.template)
        self.toets("DEZE")
        ander = maak_code("ANDER")
        ander.templates.add(Template.objects.exclude(pk=self.inv.template_version.template_id).first())
        self.assertEqual(self.fout("ANDER").reason, "bereik")
        gemengd = maak_code("BEIDE", occasions=["bruiloft"], tiers=["basis"])
        self.assertEqual(self.fout("BEIDE").reason, "bereik")        # alle gekozen beperkingen moeten kloppen

    def test_minimum_bestelbedrag(self):
        maak_code("MIN", min_order_cents=5000)
        self.assertEqual(self.fout("MIN", subtotal=3000).reason, "minimum")
        self.assertEqual(self.toets("MIN", subtotal=6000).discount_cents, 600)

    def test_opgebruikt_telt_gebruikt_en_geldig_gereserveerd_maar_geen_verlopen_reservering(self):
        code = maak_code("EEN", max_redemptions=1)
        payment = self.bestel("EEN")
        self.assertEqual(self.fout("EEN").reason, "opgebruikt")
        DiscountRedemption.objects.filter(order=payment.order).update(reserved_until=timezone.now() - timedelta(minutes=1))
        self.assertEqual(self.toets("EEN").code, code)     # verlopen reservering telt niet meer mee

    def test_zonder_klant_wordt_alleen_de_klantcontrole_overgeslagen(self):
        maak_code("ANON")
        self.assertEqual(self.toets("ANON", customer=None).code.code, "ANON")


class Bestellen(KortingBasis):
    def test_bedrag_regels_betaling_en_mollie_zijn_exact_gelijk(self):
        basis = self.basisprijs()
        maak_code("ZOMER10")
        with override_settings(PAYMENT_PROVIDER="mollie", MOLLIE_API_KEY="test_abc", BASE_URL="https://vaylide.test"):
            verstuurd = {}

            def nep(self_, method, path, body=None):
                verstuurd.update(body or {})
                return {"id": "tr_1", "_links": {"checkout": {"href": "https://pay.example/1"}}}

            with mock.patch.object(MollieProvider, "_request", nep):
                payment = self.bestel("ZOMER10")
        order = payment.order
        verwacht_korting = (basis * 10 + 50) // 100
        self.assertEqual(order.discount_cents, verwacht_korting)
        self.assertEqual(order.subtotal_cents, basis)
        self.assertEqual(order.total_cents, basis - verwacht_korting)
        self.assertEqual(order.discount_code_text, "ZOMER10")
        self.assertEqual(sum(l.total_cents for l in order.lines.all()), order.total_cents)
        self.assertEqual(payment.amount_cents, order.total_cents)
        self.assertEqual(verstuurd["amount"]["value"], f"{Decimal(order.total_cents) / 100:.2f}")
        regel = order.lines.get(code="korting:ZOMER10")
        self.assertEqual(regel.total_cents, -verwacht_korting)
        self.assertEqual(regel.description, "Kortingscode ZOMER10")
        self.assertTrue(regel.total_display.startswith("− "))

    def test_prijzen_blijven_gelijk_alleen_het_bestelbedrag_verandert(self):
        basis = self.basisprijs()
        maak_code("ZOMER10")
        payment = self.bestel("ZOMER10")
        niet_korting = [l for l in payment.order.lines.all() if not l.code.startswith("korting:")]
        self.assertEqual(sum(l.total_cents for l in niet_korting), basis)

    def test_met_schakelaar_uit_wordt_een_code_niet_geaccepteerd_en_gebeurt_er_niets(self):
        maak_code("ZOMER10")
        with override_settings(DISCOUNTS_ENABLED=False):
            with self.assertRaises(CheckoutError) as ctx:
                self.bestel("ZOMER10")
        self.assertIn("niet beschikbaar", str(ctx.exception))
        self.assertFalse(Order.objects.filter(invitation=self.inv).exists())

    def test_bestellen_zonder_code_is_ongewijzigd_met_de_schakelaar_aan(self):
        payment = self.bestel(code="")
        order = payment.order
        self.assertEqual((order.discount_cents, order.subtotal_cents, order.discount_code_id, order.discount_code_text), (0, None, None, ""))
        self.assertFalse(DiscountRedemption.objects.exists())
        self.assertFalse(order.lines.filter(code__startswith="korting:").exists())

    def test_ongeldige_code_maakt_geen_bestelling_en_laat_oude_open_bestelling_staan(self):
        eerste = self.bestel(code="")
        with self.assertRaises(CheckoutError):
            self.bestel("BESTAATNIET")
        eerste.order.refresh_from_db()
        self.assertEqual(eerste.order.status, Order.Status.PENDING)    # de mislukte poging draaide terug
        self.assertEqual(Order.objects.filter(invitation=self.inv).count(), 1)

    def test_bedrag_wordt_nooit_uit_de_browser_gehaald(self):
        maak_code("ZOMER10")
        c = Client()
        c.force_login(self.klant)
        c.post(f"/maken/{self.inv.uid}/bestellen/", {"actie": "code-toepassen", "kortingscode": "ZOMER10"})
        response = c.post(f"/maken/{self.inv.uid}/bestellen/", {"actie": "betalen", "package": self.pakket, "terms": "on", "direct_leveren": "on",
                                                              "online_dienst": "on", "total": "1", "discount": "99999", "kortingscode": "ZOMER10"})
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(invitation=self.inv)
        self.assertEqual(order.discount_cents, (order.subtotal_cents * 10 + 50) // 100)
        self.assertGreater(order.total_cents, 100)

    def test_een_ingreep_in_de_regels_stopt_de_betaling_voor_mollie(self):
        maak_code("ZOMER10")
        order = self.bestel("ZOMER10").order
        line = order.lines.get(code="korting:ZOMER10")
        line.total_cents = line.unit_price_cents = -1
        line.save()
        with self.assertRaises(CheckoutError):
            create_payment(order)
        self.assertEqual(order.payments.count(), 1)    # alleen de eerste, geen tweede poging


class Reserveren(KortingBasis):
    def provider_zegt(self, payment, status):
        return self.provider_says(payment, status)

    def test_gereserveerd_bij_bestellen_en_definitief_bij_betaling(self):
        maak_code("ZOMER10", max_redemptions=5)
        payment = self.bestel()
        red = DiscountRedemption.objects.get(order=payment.order)
        self.assertEqual(red.state, "reserved")
        self.assertEqual(red.amount_cents, payment.order.discount_cents)
        self.provider_zegt(payment, Payment.Status.PAID)
        red.refresh_from_db()
        self.assertEqual((red.state, red.reserved_until is None), ("redeemed", True))
        self.assertEqual(red.redeemed_at is not None, True)

    def test_herhaalde_melding_telt_niet_dubbel(self):
        maak_code("ZOMER10", max_redemptions=5)
        payment = self.bestel()
        self.provider_zegt(payment, Payment.Status.PAID)
        self.provider_zegt(payment, Payment.Status.PAID)
        payment.refresh_from_db()
        self.assertEqual(DiscountRedemption.objects.count(), 1)
        self.assertEqual(k.active_redemptions(DiscountCode.objects.get()), 1)
        self.assertEqual(Order.objects.get().status, "paid")

    def test_betaling_mislukt_geeft_de_code_vrij_en_een_nieuwe_poging_reserveert_opnieuw(self):
        code = maak_code("EEN", max_redemptions=1)
        payment = self.bestel("EEN")
        self.provider_zegt(payment, Payment.Status.FAILED)
        red = DiscountRedemption.objects.get()
        self.assertEqual(red.state, "released")
        self.assertEqual(k.active_redemptions(code), 0)
        # een andere klant kan hem nu gebruiken, de eigenaar van de mislukte bestelling hoeft niet opnieuw in te typen bij 'opnieuw betalen'
        order = payment.order
        order.refresh_from_db()
        nieuwe = create_payment(order)
        red.refresh_from_db()
        self.assertEqual(red.state, "reserved")
        self.assertEqual(nieuwe.amount_cents, order.total_cents)
        self.provider_zegt(nieuwe, Payment.Status.PAID)
        red.refresh_from_db()
        self.assertEqual(red.state, "redeemed")

    def test_opnieuw_betalen_kan_niet_als_de_code_intussen_is_opgebruikt(self):
        maak_code("EEN", max_redemptions=1)
        payment = self.bestel("EEN")
        self.provider_zegt(payment, Payment.Status.EXPIRED)
        andere = self.make_customer("ander@example.com")
        inv2 = self.make_invitation(owner=andere)
        self.bestel("EEN", inv=inv2, user=andere)       # neemt de vrijgekomen plek
        order = payment.order
        order.refresh_from_db()
        with self.assertRaises(CheckoutError) as ctx:
            create_payment(order)
        self.assertIn("bestel opnieuw", str(ctx.exception))
        self.assertEqual(order.payments.count(), 1)     # geen nieuwe betaling aangemaakt

    def test_geannuleerde_betaling_houdt_de_reservering_vast_tot_die_verloopt(self):
        code = maak_code("EEN", max_redemptions=1)
        payment = self.bestel("EEN")
        self.provider_zegt(payment, Payment.Status.CANCELED)
        self.assertEqual(DiscountRedemption.objects.get().state, "reserved")
        DiscountRedemption.objects.update(reserved_until=timezone.now() - timedelta(minutes=1))
        self.assertEqual(k.active_redemptions(code), 0)

    def test_nieuwe_bestelling_voor_dezelfde_kaart_vervangt_de_oude_en_geeft_de_code_vrij(self):
        maak_code("ZOMER10", max_redemptions=1)
        eerste = self.bestel()
        tweede = self.bestel()      # dezelfde klant, dezelfde kaart: geen 'opgebruikt' door de eigen vorige poging
        eerste.order.refresh_from_db()
        self.assertEqual(eerste.order.status, Order.Status.CANCELLED)
        self.assertEqual(DiscountRedemption.objects.get(order=eerste.order).state, "released")
        self.assertEqual(DiscountRedemption.objects.get(order=tweede.order).state, "reserved")
        self.assertEqual(k.active_redemptions(DiscountCode.objects.get()), 1)

    def test_geen_dubbele_reservering_op_de_laatste_plek(self):
        maak_code("EEN", max_redemptions=1)
        self.bestel("EEN")
        andere = self.make_customer("ander@example.com")
        inv2 = self.make_invitation(owner=andere)
        with self.assertRaises(CheckoutError) as ctx:
            self.bestel("EEN", inv=inv2, user=andere)
        self.assertIn("niet meer beschikbaar", str(ctx.exception))
        self.assertEqual(DiscountRedemption.objects.count(), 1)
        self.assertFalse(Order.objects.filter(invitation=inv2).exists())

    def test_maximum_wordt_nooit_overschreden_door_reserveringen_en_gebruiken_samen(self):
        maak_code("DRIE", max_redemptions=3)
        gelukt = 0
        for i in range(6):
            klant = self.make_customer(f"k{i}@example.com")
            inv = self.make_invitation(owner=klant)
            try:
                payment = self.bestel("DRIE", inv=inv, user=klant)
            except CheckoutError:
                continue
            gelukt += 1
            if i % 2 == 0:
                self.provider_zegt(payment, Payment.Status.PAID)
        self.assertEqual(gelukt, 3)
        self.assertEqual(k.active_redemptions(DiscountCode.objects.get()), 3)

    def test_late_betaling_na_verlopen_reservering_blijft_staan_maar_wordt_vastgelegd(self):
        maak_code("EEN", max_redemptions=1)
        eerste = self.bestel("EEN")
        DiscountRedemption.objects.filter(order=eerste.order).update(reserved_until=timezone.now() - timedelta(minutes=1))
        andere = self.make_customer("ander@example.com")
        inv2 = self.make_invitation(owner=andere)
        tweede = self.bestel("EEN", inv=inv2, user=andere)
        self.provider_zegt(tweede, Payment.Status.PAID)
        self.provider_zegt(eerste, Payment.Status.PAID)     # betaalde toch nog, na het verlopen van de reservering
        red = DiscountRedemption.objects.get(order=eerste.order)
        self.assertEqual(red.state, "redeemed")
        self.assertIn("maximum aantal keer overschreden", red.note)
        eerste.order.refresh_from_db()
        self.assertEqual(eerste.order.status, "paid")      # de klant die betaald heeft, krijgt zijn kaart
        event = PaymentEvent.objects.filter(payment=eerste).order_by("-id").first()
        self.assertIn("Let op", event.outcome)

    def test_betaling_van_een_vervangen_bestelling_wordt_alsnog_gebruikt(self):
        maak_code("ZOMER10", max_redemptions=3)
        eerste = self.bestel()
        self.bestel()      # vervangt de eerste
        self.provider_zegt(eerste, Payment.Status.PAID)
        self.assertEqual(DiscountRedemption.objects.get(order=eerste.order).state, "redeemed")

    def test_afwijkend_bedrag_bij_de_provider_publiceert_niet_en_gebruikt_de_code_niet(self):
        maak_code("ZOMER10")
        payment = self.bestel()
        remote = RemoteStatus(status=Payment.Status.PAID, amount_cents=payment.order.subtotal_cents, currency="EUR", method="ideal", paid_at=timezone.now())
        apply_remote_status(payment, remote, source="webhook")
        payment.order.refresh_from_db()
        self.assertEqual(payment.order.fulfilment_status, Order.Fulfilment.ATTENTION)
        self.assertNotEqual(payment.order.status, Order.Status.PAID)
        self.assertEqual(DiscountRedemption.objects.get().state, "reserved")


class PerKlant(KortingBasis):
    def bestel_voor(self, email, code="ZOMER10"):
        klant = self.make_customer(email)
        inv = self.make_invitation(owner=klant)
        return self.bestel(code, inv=inv, user=klant)

    def test_standaard_een_keer_per_klant(self):
        maak_code("ZOMER10")
        self.provider_says(self.bestel(), Payment.Status.PAID)
        inv2 = self.make_invitation(owner=self.klant)
        with self.assertRaises(CheckoutError) as ctx:
            self.bestel(inv=inv2)
        self.assertEqual(str(ctx.exception), "Je hebt deze code al gebruikt.")

    def test_instelbaar_meerdere_keren_per_klant(self):
        maak_code("TWEE", max_per_customer=2)
        self.provider_says(self.bestel("TWEE"), Payment.Status.PAID)
        inv2 = self.make_invitation(owner=self.klant)
        self.provider_says(self.bestel("TWEE", inv=inv2), Payment.Status.PAID)
        inv3 = self.make_invitation(owner=self.klant)
        with self.assertRaises(CheckoutError):
            self.bestel("TWEE", inv=inv3)

    def test_zelfde_adres_met_plusje_of_gmail_puntjes_telt_als_dezelfde_klant(self):
        maak_code("ZOMER10")
        self.bestel_voor("jan.jansen@gmail.com")
        for anders in ("janjansen@gmail.com", "Jan.Jansen+kerst@googlemail.com", "JANJANSEN+x@gmail.com"):
            with self.assertRaises(CheckoutError, msg=anders):
                self.bestel_voor(anders)

    def test_ander_adres_is_een_andere_klant_en_dat_is_geen_waterdichte_fraudepreventie(self):
        maak_code("ZOMER10")
        self.bestel_voor("anna@example.com")
        self.bestel_voor("anna.2@example.com")       # een echt ander adres lukt: de controle is zo sterk als het e-mailadres
        self.assertEqual(DiscountRedemption.objects.count(), 2)

    def test_sleutel_bevat_het_adres_niet(self):
        self.assertNotIn("klant", k.customer_key("klant@example.com"))
        self.assertEqual(k.customer_key("A+b@Example.com"), k.customer_key("a@example.com"))


class Terugbetaling(KortingBasis):
    def setUp(self):
        super().setUp()
        self.staff = self.make_staff()
        self.c = Client()
        self.c.force_login(self.staff)

    def betaald(self, code="ZOMER10"):
        maak_code(code, max_redemptions=2)
        payment = self.bestel(code)
        self.provider_says(payment, Payment.Status.PAID)
        return Order.objects.get(pk=payment.order_id)

    def test_terugbetaald_telt_de_code_nog_steeds_mee(self):
        order = self.betaald()
        self.c.post(f"/beheer/bestellingen/{order.uid}/", {"actie": "status", "status": "refunded"})
        order.refresh_from_db()
        self.assertEqual(order.status, "refunded")
        self.assertEqual(DiscountRedemption.objects.get().state, "redeemed")
        self.assertEqual(k.active_redemptions(DiscountCode.objects.get()), 1)
        self.assertEqual(order.total_cents, order.subtotal_cents - order.discount_cents)     # terug te betalen = werkelijk betaald

    def test_alleen_een_beheerder_kan_vrijgeven_met_reden_en_het_wordt_vastgelegd(self):
        order = self.betaald()
        url = f"/beheer/bestellingen/{order.uid}/"
        klant = Client()
        klant.force_login(self.klant)
        klant.post(url, {"actie": "kortingscode-vrijgeven", "reden": "ik wil het"})
        self.assertEqual(DiscountRedemption.objects.get().state, "redeemed")
        self.c.post(url, {"actie": "kortingscode-vrijgeven", "reden": "  "})
        self.assertEqual(DiscountRedemption.objects.get().state, "redeemed")      # reden verplicht
        self.c.post(url, {"actie": "kortingscode-vrijgeven", "reden": "Terugbetaling, klant mag opnieuw"})
        red = DiscountRedemption.objects.get()
        self.assertEqual((red.state, red.released_by), ("released", self.staff))
        self.assertEqual(red.released_reason, "Terugbetaling, klant mag opnieuw")
        self.assertIsNotNone(red.released_at)
        gebeurtenis = PaymentEvent.objects.filter(source="beheer").first()
        self.assertIn("vrijgegeven door eigenaar@example.com", gebeurtenis.outcome)
        self.assertEqual(k.active_redemptions(DiscountCode.objects.get()), 0)

    def test_annuleren_in_beheer_geeft_een_gereserveerde_code_vrij_maar_een_gebruikte_niet(self):
        maak_code("EEN", max_redemptions=5)
        open_ = self.bestel("EEN").order
        self.c.post(f"/beheer/bestellingen/{open_.uid}/", {"actie": "status", "status": "cancelled"})
        self.assertEqual(DiscountRedemption.objects.get(order=open_).state, "released")
        order = self.betaald("ZOMER10")
        self.c.post(f"/beheer/bestellingen/{order.uid}/", {"actie": "status", "status": "cancelled"})
        self.assertEqual(DiscountRedemption.objects.get(order=order).state, "redeemed")


class HistorischeBestellingen(KortingBasis):
    def test_bestaande_bestelling_blijft_leesbaar_en_ongewijzigd(self):
        order = Order.objects.create(number="VL26-90001", customer=self.klant, invitation=self.inv, total_cents=3900, status="paid", package_name="Essentieel")
        OrderLine.objects.create(order=order, code="pakket:essentieel", description="Pakket Essentieel", unit_price_cents=3900, total_cents=3900)
        order.refresh_from_db()
        self.assertEqual((order.discount_cents, order.subtotal_cents, order.discount_code_text), (0, None, ""))
        staff = self.make_staff()
        c = Client()
        c.force_login(staff)
        page = c.get(f"/beheer/bestellingen/{order.uid}/")
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, "Bedrag voor korting")
        klant = Client()
        klant.force_login(self.klant)
        self.assertContains(klant.get(f"/bestelling/{order.uid}/"), "Pakket Essentieel")

    def test_een_code_die_later_wordt_uitgezet_laat_de_bestelling_intact(self):
        code = maak_code("ZOMER10")
        payment = self.bestel()
        self.provider_says(payment, Payment.Status.PAID)
        code.is_active = False
        code.save()
        order = Order.objects.get(pk=payment.order_id)
        self.assertEqual(order.discount_code_text, "ZOMER10")
        self.assertEqual(order.status, "paid")
        with self.assertRaises(Exception):
            code.delete()      # een code met gebruik kan niet verdwijnen (PROTECT)

    def test_formattering_van_negatieve_bedragen_raakt_gewone_bedragen_niet(self):
        self.assertEqual(format_euro(-250), "− € 2,50")
        self.assertEqual(format_euro(2495), "€ 24,95")
        self.assertEqual(format_euro(0), "€ 0")


class Mail(KortingBasis):
    def test_bevestigingsmail_toont_prijs_korting_en_totaal_exact_gelijk_aan_de_bestelling(self):
        maak_code("ZOMER10")
        payment = self.bestel()
        self.provider_says(payment, Payment.Status.PAID)
        order = Order.objects.get(pk=payment.order_id)
        mail = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        for tekst in (mail.body_text, mail.body_html):
            self.assertIn("Kortingscode ZOMER10", tekst)
            self.assertIn(format_euro(-order.discount_cents), tekst)
            self.assertIn(order.total_display, tekst)
            self.assertIn(format_euro(order.subtotal_cents), tekst)

    def test_bon_en_status_pagina_tonen_de_korting(self):
        maak_code("ZOMER10")
        payment = self.bestel()
        self.provider_says(payment, Payment.Status.PAID)
        c = Client()
        c.force_login(self.klant)
        page = c.get(f"/bestelling/{payment.order.uid}/")
        self.assertContains(page, "Kortingscode ZOMER10")
        self.assertContains(page, payment.order.total_display)


class Bestelstap(KortingBasis):
    def setUp(self):
        super().setUp()
        self.c = Client()
        self.c.force_login(self.klant)
        self.url = f"/maken/{self.inv.uid}/bestellen/"

    def post(self, **extra):
        data = {"package": self.pakket, "terms": "on", "direct_leveren": "on", "online_dienst": "on"}
        data.update(extra)
        return self.c.post(self.url, data)

    def test_schakelaar_uit_geen_invoerveld_en_een_gepost_veld_doet_niets(self):
        maak_code("ZOMER10")
        with override_settings(DISCOUNTS_ENABLED=False):
            page = self.c.get(self.url)
            self.assertNotContains(page, "Heb je een kortingscode?")
            self.assertNotContains(page, 'name="kortingscode"')
            antwoord = self.post(actie="code-toepassen", kortingscode="ZOMER10")
            self.assertNotContains(antwoord, "Kortingscode")
            self.post(actie="betalen", kortingscode="ZOMER10")
            order = Order.objects.get(invitation=self.inv)
            self.assertEqual(order.discount_cents, 0)

    def test_bescheiden_regel_zonder_extra_stap_en_werkt_zonder_javascript(self):
        page = self.c.get(self.url)
        self.assertContains(page, "Heb je een kortingscode?")
        self.assertContains(page, '<details class="korting">')       # dicht tot de klant hem opent; een gewoon formulier, geen script nodig
        self.assertContains(page, 'name="kortingscode"')
        self.assertNotContains(page, "korting-banner")

    def test_code_toepassen_toont_prijs_korting_en_nieuw_totaal(self):
        maak_code("ZOMER10")
        basis = self.basisprijs()
        antwoord = self.post(actie="code-toepassen", kortingscode="zomer10")
        korting = (basis * 10 + 50) // 100
        self.assertContains(antwoord, format_euro(basis))
        self.assertContains(antwoord, "Kortingscode ZOMER10")
        self.assertContains(antwoord, format_euro(-korting))
        self.assertContains(antwoord, f"Bestellen en betalen {format_euro(basis - korting)}")
        self.assertNotContains(antwoord, "Heb je een kortingscode?")     # toegepast: de regel in het overzicht heeft een 'Verwijderen'
        self.assertEqual(Order.objects.filter(invitation=self.inv).count(), 0)    # alleen tonen, nog geen bestelling
        # een nieuwe weergave onthoudt de code (sessie)
        self.assertContains(self.c.get(self.url), "Kortingscode ZOMER10")

    def test_verwijderen_zet_de_oorspronkelijke_prijs_terug(self):
        maak_code("ZOMER10")
        basis = self.basisprijs()
        self.post(actie="code-toepassen", kortingscode="ZOMER10")
        antwoord = self.post(actie="code-verwijderen")
        self.assertNotContains(antwoord, "Kortingscode ZOMER10")
        self.assertContains(antwoord, f"Bestellen en betalen {format_euro(basis)}")

    def test_duidelijke_meldingen(self):
        maak_code("OUD", ends_at=timezone.now() - timedelta(days=2))
        maak_code("EEN", max_redemptions=1)
        self.bestel("EEN", inv=self.make_invitation(owner=self.make_customer("x@example.com")), user=User.objects.get(email="x@example.com"))
        maak_code("KERST", occasions=["kerst"])
        verwacht = {"BESTAATNIET": "Deze code kennen we niet. Controleer de spelling.", "OUD": "Deze code is verlopen op",
                    "EEN": "Deze code is helaas niet meer beschikbaar.", "KERST": "Deze code geldt niet voor deze gelegenheid."}
        for code, tekst in verwacht.items():
            antwoord = self.post(actie="code-toepassen", kortingscode=code)
            self.assertContains(antwoord, tekst)
            self.assertContains(antwoord, 'role="alert"')
            self.assertNotContains(antwoord, "Kortingscode " + code)
        self.assertContains(self.post(actie="code-toepassen", kortingscode=""), "Vul een kortingscode in.")

    def test_bestellen_met_de_code_rekent_het_nieuwe_bedrag_af(self):
        maak_code("ZOMER10")
        self.post(actie="code-toepassen", kortingscode="ZOMER10")
        antwoord = self.post(actie="betalen")
        self.assertEqual(antwoord.status_code, 302)
        order = Order.objects.get(invitation=self.inv)
        self.assertGreater(order.discount_cents, 0)
        self.assertEqual(order.latest_payment.amount_cents, order.total_cents)

    def test_ingetikte_maar_niet_toegepaste_code_laat_eerst_het_nieuwe_bedrag_zien(self):
        maak_code("ZOMER10")
        antwoord = self.post(actie="betalen", kortingscode="ZOMER10")
        self.assertEqual(antwoord.status_code, 200)
        self.assertContains(antwoord, "Je kortingscode is toegepast. Controleer het bedrag")
        self.assertFalse(Order.objects.filter(invitation=self.inv).exists())
        self.assertEqual(self.post(actie="betalen").status_code, 302)

    def test_code_die_tussen_toepassen_en_betalen_opraakt_wordt_niet_betaald(self):
        code = maak_code("EEN", max_redemptions=1)
        self.post(actie="code-toepassen", kortingscode="EEN")
        andere = self.make_customer("ander@example.com")
        self.bestel("EEN", inv=self.make_invitation(owner=andere), user=andere)
        antwoord = self.post(actie="betalen")
        self.assertEqual(antwoord.status_code, 200)
        self.assertContains(antwoord, "helaas niet meer beschikbaar")
        self.assertFalse(Order.objects.filter(invitation=self.inv).exists())

    def test_te_veel_pogingen_worden_afgeremd(self):
        for _ in range(10):
            self.post(actie="code-toepassen", kortingscode="RADEN")
        antwoord = self.post(actie="code-toepassen", kortingscode="RADEN")
        self.assertContains(antwoord, "te vaak geprobeerd")

    def test_een_ander_concept_ziet_de_code_van_dit_concept_niet(self):
        maak_code("ZOMER10")
        self.post(actie="code-toepassen", kortingscode="ZOMER10")
        ander = self.make_invitation(owner=self.klant)
        page = self.c.get(f"/maken/{ander.uid}/bestellen/")
        self.assertNotContains(page, "Kortingscode ZOMER10")

    def test_code_in_de_link_vult_alleen_het_veld_in(self):
        maak_code("ZOMER10")
        page = self.c.get(self.url + "?code=ZOMER10")
        self.assertContains(page, 'value="ZOMER10"')
        self.assertNotContains(page, "Kortingscode ZOMER10")

    def basisprijs(self):
        return super().basisprijs()


class BeheerKortingscodes(KortingBasis):
    def setUp(self):
        super().setUp()
        self.staff = self.make_staff()
        self.c = Client()
        self.c.force_login(self.staff)

    def nieuw(self, **extra):
        data = {"code": "HERFST15", "kind": "percent", "percent": "15", "max_per_customer": "1", "is_active": "on"}
        data.update(extra)
        return self.c.post("/beheer/kortingscodes/nieuw/", data)

    def test_aanmaken_met_alle_opties(self):
        antwoord = self.nieuw(max_redemptions="50", starts_on="2026-11-01", ends_on="2026-12-31", occasions=["kerst", "bruiloft"], tiers=["luxe"],
                              min_order="20", note="Najaarsactie")
        self.assertEqual(antwoord.status_code, 302)
        code = DiscountCode.objects.get()
        self.assertEqual((code.code, code.code_norm, code.percent, code.max_redemptions, code.max_per_customer), ("HERFST15", "HERFST15", 15, 50, 1))
        self.assertEqual((code.occasions, code.tiers, code.min_order_cents), (["kerst", "bruiloft"], ["luxe"], 2000))
        self.assertEqual(timezone.localtime(code.starts_at).date().isoformat(), "2026-11-01")
        eind = timezone.localtime(code.ends_at)
        self.assertEqual((eind.date().isoformat(), eind.hour, eind.minute), ("2026-12-31", 23, 59))

    def test_vast_bedrag_en_willekeurige_code(self):
        self.nieuw(code="", kind="fixed", percent="", amount="5,00")
        code = DiscountCode.objects.get()
        self.assertEqual((code.kind, code.amount_cents, code.percent), ("fixed", 500, None))
        self.assertEqual(len(code.code), 8)
        self.assertFalse(set(code.code) & set("01OIL"))

    def test_geen_gratis_of_onzinnige_waarden_via_het_formulier(self):
        for waarde in ("0", "91", "100"):
            self.nieuw(code=f"X{waarde}", percent=waarde)
        self.nieuw(code="VAST", kind="fixed", percent="", amount="")
        self.nieuw(code="OMGEKEERD", starts_on="2026-12-31", ends_on="2026-11-01")
        self.nieuw(code="KORT", percent="10", max_redemptions="0")
        self.assertEqual(DiscountCode.objects.count(), 0)

    def test_dubbele_code_en_te_korte_code(self):
        self.nieuw()
        self.nieuw(code="herfst-15")
        self.nieuw(code="AB")
        self.assertEqual(DiscountCode.objects.count(), 1)

    def test_na_gebruik_vergrendeld_behalve_periode_maximum_en_uitzetten(self):
        code = maak_code("ZOMER10", max_redemptions=10)
        self.bestel("ZOMER10")
        self.c.post(f"/beheer/kortingscodes/{code.pk}/", {"code": "ANDERS", "kind": "percent", "percent": "50", "max_per_customer": "1",
                                                           "max_redemptions": "20", "is_active": "", "occasions": ["kerst"]})
        code.refresh_from_db()
        self.assertEqual((code.code, code.percent, code.occasions), ("ZOMER10", 10, []))
        self.assertEqual((code.max_redemptions, code.is_active), (20, False))
        self.c.post(f"/beheer/kortingscodes/{code.pk}/", {"kind": "percent", "percent": "10", "max_per_customer": "1", "max_redemptions": "0", "is_active": "on"})
        code.refresh_from_db()
        self.assertEqual(code.max_redemptions, 20)       # niet lager dan wat er al gebruikt of gereserveerd is

    def test_overzicht_en_detail_met_gebruik(self):
        maak_code("ZOMER10", max_redemptions=10)
        payment = self.bestel()
        lijst = self.c.get("/beheer/kortingscodes/")
        self.assertContains(lijst, "ZOMER10")
        self.assertContains(lijst, "actief")
        detail = self.c.get(f"/beheer/kortingscodes/{DiscountCode.objects.get().pk}/")
        self.assertContains(detail, payment.order.number)
        self.assertContains(detail, "Gereserveerd")

    def test_status_opgebruikt_verlopen_gepland(self):
        eind = maak_code("OUD", ends_at=timezone.now() - timedelta(days=1))
        gepland = maak_code("LATER", starts_at=timezone.now() + timedelta(days=1))
        self.assertEqual((eind.status(), gepland.status()), ("verlopen", "gepland"))
        eenmalig = maak_code("EEN", max_redemptions=1)
        self.bestel("EEN")
        self.assertEqual(eenmalig.status(), "opgebruikt")

    def test_alleen_voor_beheerders_en_verborgen_met_schakelaar_uit(self):
        anon = Client()
        self.assertEqual(anon.get("/beheer/kortingscodes/").status_code, 302)
        klant = Client()
        klant.force_login(self.klant)
        self.assertIn(klant.get("/beheer/kortingscodes/").status_code, (302, 403, 404))
        self.assertContains(self.c.get("/beheer/"), "Kortingen")
        with override_settings(DISCOUNTS_ENABLED=False):
            self.assertEqual(self.c.get("/beheer/kortingscodes/").status_code, 404)
            self.assertEqual(self.c.post("/beheer/kortingscodes/nieuw/", {"code": "X1234", "kind": "percent", "percent": "10", "max_per_customer": "1"}).status_code, 404)
            self.assertNotContains(self.c.get("/beheer/"), "Kortingscodes")
        self.assertEqual(DiscountCode.objects.count(), 0)

    def test_bestelling_in_beheer_toont_korting_en_btw(self):
        maak_code("ZOMER10")
        payment = self.bestel()
        page = self.c.get(f"/beheer/bestellingen/{payment.order.uid}/")
        self.assertContains(page, "Bedrag voor korting")
        self.assertContains(page, "Waarvan btw (21%)")
        self.assertContains(page, format_euro(k.vat_part_cents(payment.order.total_cents)))


class BestaandeFunctiesBlijven(KortingBasis):
    def test_offerte_zonder_code_is_identiek(self):
        from orders.pricing import build_quote

        offerte = build_quote(self.inv.draft_content, None if self.v2 else __import__("catalog.models", fromlist=["Package"]).Package.objects.get(code="essentieel"),
                              template_version=self.inv.template_version, occasion=self.inv.occasion)
        self.assertEqual(offerte.discount_cents, 0)
        self.assertEqual(offerte.subtotal_cents, offerte.total_cents)
        self.assertFalse(offerte.has_discount)
        self.assertFalse(any(l.is_discount for l in offerte.lines))


def _v2(klasse):
    """Dezelfde tests voor de nieuwe prijsstructuur (Basis, Luxe, Special)."""
    return type(f"{klasse.__name__}V2", (klasse,), {"v2": True, "__module__": klasse.__module__})


Berekening_V2 = _v2(Berekening)
Bestellen_V2 = _v2(Bestellen)
Reserveren_V2 = _v2(Reserveren)
Bestelstap_V2 = _v2(Bestelstap)
Mail_V2 = _v2(Mail)
Terugbetaling_V2 = _v2(Terugbetaling)
BestaandeFunctiesBlijven_V2 = _v2(BestaandeFunctiesBlijven)

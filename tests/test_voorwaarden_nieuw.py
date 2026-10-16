"""Voorwaarden 16 oktober 2026 (nieuwe prijsstructuur): aparte versie naast 29 september, de juiste versie bij elke bestelling, onbevestigde
bedrijfsgegevens als invulveld, de conceptmelding, en de privacyverklaring met de nieuwe looptijd."""
from django.test import Client, override_settings

from core import voorwaarden
from orders.models import Order, Payment
from processing.models import OutboundEmail

from .helpers import VaylideTestCase

V2 = override_settings(PRICING_V2=True)
ALLES_BEVESTIGD = {"kvk": True, "btw": True, "adres": True, "email": True}


class VersiesTests(VaylideTestCase):
    def test_beide_versies_bestaan_en_de_schakelaar_bepaalt_welke_nu_geldt(self):
        self.assertIn("2026-09-29", voorwaarden.VERSIONS)
        self.assertIn("2026-10-16", voorwaarden.VERSIONS)
        self.assertEqual(voorwaarden.current(), "2026-09-29")
        with V2:
            self.assertEqual(voorwaarden.current(), "2026-10-16")
            self.assertEqual(voorwaarden.version_info()["version"], "2026-10-16")
        self.assertEqual(voorwaarden.version_info("2026-09-29")["version"], "2026-09-29")

    def test_de_oude_versie_blijft_ongewijzigd_bereikbaar(self):
        for pad in ("/voorwaarden/versie/2026-09-29/", "/voorwaarden/pdf/2026-09-29/", "/voorwaarden/download/2026-09-29/"):
            self.assertEqual(Client().get(pad).status_code, 200, pad)
        with V2:
            tekst = Client().get("/voorwaarden/versie/2026-09-29/").content.decode()
        self.assertIn("Bij Essentieel blijven de digitale kaart", tekst)
        self.assertIn("Bij Compleet geldt een beschikbaarheidsduur van 12 maanden", tekst)
        self.assertNotIn("Basis, Luxe en Special", tekst)
        self.assertNotIn("activeringsdatum", tekst)
        # De oude tekst toont de bedrijfsgegevens zoals altijd (geen invulvelden voor KvK of e-mail).
        self.assertIn("94261423", tekst)

    def test_de_nieuwe_versie_beschrijft_basis_luxe_special_12_maanden_zonder_toeslagen(self):
        tekst = Client().get("/voorwaarden/versie/2026-10-16/").content.decode()
        for zin in ("Basis, Luxe of Special", "Bij Basis, Luxe en Special blijven de digitale kaart", "12 maanden vanaf de aankoopdatum",
                    "komen er geen toeslagen of extra opties bij", "kosten niets extra: daarvoor rekenen wij geen toeslagen",
                    "blijven het pakket, de prijs, de einddatum en de voorwaarden van die bestelling gelden",
                    "6 maanden bij Essentieel, 12 maanden bij Compleet en 6 maanden bij een wenskaart"):
            self.assertIn(zin, tekst, zin)
        self.assertNotIn("Bij Essentieel blijven de digitale kaart en de inbegrepen online functies 6 maanden vanaf de aankoopdatum beschikbaar", tekst)
        self.assertNotIn("eventuele extra opties", tekst)
        self.assertEqual(Client().get("/voorwaarden/pdf/2026-10-16/").status_code, 200)
        self.assertEqual(Client().get("/voorwaarden/download/2026-10-16/").status_code, 200)

    def test_de_conceptmelding_blijft_staan_tot_de_definitieve_tekst_is_goedgekeurd(self):
        self.assertEqual(voorwaarden.VERSIONS["2026-10-16"]["status"], "Concept")
        tekst = Client().get("/voorwaarden/versie/2026-10-16/").content.decode()
        self.assertIn("Deze voorwaarden zijn een concept", tekst)

    def test_onbevestigde_bedrijfsgegevens_en_de_activeringsdatum_zijn_invulvelden(self):
        pagina = Client().get("/voorwaarden/versie/2026-10-16/").content.decode()
        tekst = pagina[pagina.index('id="artikel-1"'):pagina.index("<footer")]          # de footer van de site toont de bedrijfsgegevens zoals altijd
        for veld in ("[KvK-nummer]", "[contact-e-mailadres]", "[vestigingsadres]", "[activeringsdatum van de nieuwe prijzen]"):
            self.assertIn(f'<mark class="invulveld">{veld}</mark>', tekst, veld)
        # Een standaardwaarde uit de code is geen bewijs: de waarden staan er niet als feit.
        self.assertNotIn("94261423", tekst)
        self.assertNotIn(self.settings_email(), tekst)

    def settings_email(self):
        from django.conf import settings

        return settings.CONTACT_EMAIL

    def test_bevestigde_bedrijfsgegevens_verschijnen_als_tekst(self):
        with override_settings(COMPANY_CONFIRMED=ALLES_BEVESTIGD, COMPANY_LEGAL_NAME="Voorbeeld Studio (eenmanszaak)"):
            tekst = Client().get("/voorwaarden/versie/2026-10-16/").content.decode()
        self.assertIn("94261423", tekst)
        self.assertIn("Voorbeeld Studio (eenmanszaak)", tekst)
        self.assertNotIn("[KvK-nummer]", tekst)
        self.assertNotIn("[contact-e-mailadres]", tekst)
        # De activeringsdatum blijft open tot de eigenaar hem vastlegt.
        self.assertIn("[activeringsdatum van de nieuwe prijzen]", tekst)


class BestellenTests(VaylideTestCase):
    def test_bestellen_toont_en_legt_de_nieuwe_versie_vast_en_de_oude_bestelling_houdt_de_oude(self):
        klant = self.make_customer()
        oud = self.make_invitation(owner=klant)
        self.pay(oud, klant)
        nieuw = self.make_invitation(owner=klant)
        with V2:
            client = Client()
            client.force_login(klant)
            pagina = client.get(f"/maken/{nieuw.uid}/bestellen/").content.decode()
            self.assertIn("Versie 16 oktober 2026", pagina)
            self.assertIn("/voorwaarden/pdf/2026-10-16/", pagina)
            self.pay(nieuw, klant)
        self.assertEqual(Order.objects.get(invitation=oud).terms_version, "2026-09-29")
        bestelling = Order.objects.get(invitation=nieuw)
        self.assertEqual(bestelling.terms_version, "2026-10-16")
        self.assertEqual(bestelling.total_cents, 5995)

    def test_de_bestelbevestiging_bevat_de_versie_van_de_bestelling_en_oude_versies_blijven_bewaard(self):
        from core.voorwaarden_pdf import render_pdf
        from processing.emails import terms_attachment

        klant = self.make_customer()
        oud = self.make_invitation(owner=klant)
        self.pay(oud, klant)
        nieuw = self.make_invitation(owner=klant)
        with V2:
            payment = self.pay(nieuw, klant)
        mail_nieuw = OutboundEmail.objects.get(order=payment.order, kind="order_confirmation")
        mail_oud = OutboundEmail.objects.get(order=Order.objects.get(invitation=oud), kind="order_confirmation")
        self.assertEqual(mail_nieuw.attach_terms_version, "2026-10-16")
        self.assertIn("Versie: 16 oktober 2026", mail_nieuw.body_text)
        self.assertEqual(mail_oud.attach_terms_version, "2026-09-29")
        self.assertIn("Versie: 29 september 2026", mail_oud.body_text)
        naam, inhoud, _ = terms_attachment("2026-10-16")
        self.assertEqual(naam, "algemene-voorwaarden-vaylide-2026-10-16.pdf")
        self.assertTrue(inhoud.startswith(b"%PDF-"))
        self.assertIn(b"Basis, Luxe en Special", render_pdf("2026-10-16", compress=False))
        # Ook de oude versie blijft als pdf beschikbaar.
        self.assertIn(b"Essentieel", render_pdf("2026-09-29", compress=False))
        self.assertEqual(Payment.objects.get(order=payment.order).status, Payment.Status.PAID)


class PrivacyTests(VaylideTestCase):
    def page(self):
        return Client().get("/privacy/").content.decode()

    def test_zonder_de_nieuwe_prijzen_blijft_de_tekst_over_de_looptijd_zoals_hij_was(self):
        html = self.page()
        self.assertIn("Je kaart staat online met Essentieel 6 maanden en met Compleet 12 maanden", html)
        self.assertNotIn("Je kaart staat 12 maanden online", html)

    def test_met_de_nieuwe_prijzen_staat_er_12_maanden_en_de_overgangsregel(self):
        with V2:
            html = self.page()
        self.assertIn("Je kaart staat 12 maanden online, vanaf de bevestigde betaling.", html)
        self.assertIn("6 maanden bij Essentieel, 12 maanden bij Compleet en 6 maanden bij een wenskaart", html)
        self.assertIn("[activeringsdatum van de nieuwe prijzen]", html)
        self.assertIn("de indeling (Basis, Luxe of Special)", html)

    def test_bewaartermijnen_volgen_de_werkelijke_opruiming_na_de_einddatum(self):
        html = self.page()
        self.assertIn("na de einddatum van de looptijd", html)
        self.assertNotIn("nadat de uitnodiging offline ging", html)
        self.assertNotIn("90 dagen nadat de kaart offline ging", html)

    def test_de_extra_sessieopslag_van_het_samenstellen_staat_in_de_cookietabel(self):
        html = self.page()
        self.assertIn("vierlief-studio-eigen-muziek", html)
        self.assertIn("vaylide-auto-start", html)

    def test_een_niet_bevestigde_maildienst_en_adres_zijn_invulvelden(self):
        with override_settings(EMAIL_MODE="smtp", PRIVACY_EMAIL_PROVIDER="Vimexx B.V. (Nederland)", PRIVACY_EMAIL_PROVIDER_CONFIRMED=False):
            html = self.page()
        self.assertIn("[naam en land aanbieder]", html)
        self.assertIn("[contact-e-mailadres]", html)
        self.assertNotIn("Vimexx", html)
        with override_settings(EMAIL_MODE="smtp", PRIVACY_EMAIL_PROVIDER="Vimexx B.V. (Nederland)", PRIVACY_EMAIL_PROVIDER_CONFIRMED=True):
            self.assertIn("Vimexx", self.page())

    def test_alleen_actieve_diensten_staan_in_de_verklaring(self):
        html = self.page()
        for niet_actief in ("Microsoft Clarity", "Google Analytics", "Anthropic PBC", "Mollie B.V."):
            if niet_actief in ("Microsoft Clarity", "Google Analytics"):
                self.assertNotIn(f"<td data-label=\"Partij\">{niet_actief}", html)
            else:
                self.assertNotIn(niet_actief, html)


class DefinitiefMakenTests(VaylideTestCase):
    """De eigenaar maakt de teksten definitief met omgevingsvariabelen; er is daarvoor geen codewijziging nodig en niets wordt vooraf als definitief getoond."""

    def pagina(self, pad):
        return Client().get(pad).content.decode()

    def test_standaard_blijven_de_nieuwe_teksten_een_concept_met_open_activeringsdatum(self):
        self.assertEqual(voorwaarden.version_info("2026-10-16")["status"], "Concept")
        tekst = self.pagina("/voorwaarden/versie/2026-10-16/")
        self.assertIn("Deze voorwaarden zijn een concept", tekst)
        self.assertIn("[activeringsdatum van de nieuwe prijzen]", tekst)
        privacy = self.pagina("/privacy/")
        self.assertIn("Concept · bijgewerkt op", privacy)

    @override_settings(TEXTS_DEFINITIVE=True, PRICING_V2_ACTIVATION="2026-11-01", COMPANY_CONFIRMED=ALLES_BEVESTIGD)
    def test_met_de_bevestigingen_van_de_eigenaar_vervallen_concept_en_invulveld(self):
        self.assertEqual(voorwaarden.version_info("2026-10-16")["status"], "Definitief")
        tekst = self.pagina("/voorwaarden/versie/2026-10-16/")
        self.assertNotIn("Deze voorwaarden zijn een concept", tekst)
        self.assertNotIn("[activeringsdatum van de nieuwe prijzen]", tekst)
        self.assertIn("1 november 2026", tekst)
        with V2:
            privacy = self.pagina("/privacy/")
        self.assertNotIn("Concept", privacy.split("<main")[1][:600])
        self.assertIn("1 november 2026", privacy)
        # De oude versie blijft een ongewijzigd stuk tekst, ook met de nieuwe bevestigingen.
        self.assertNotIn("1 november 2026", self.pagina("/voorwaarden/versie/2026-09-29/"))

    @override_settings(PRICING_V2_ACTIVATION="morgen")
    def test_een_ongeldige_activeringsdatum_telt_niet_als_bevestigd(self):
        self.assertIsNone(voorwaarden.activation_date())
        self.assertIn("[activeringsdatum van de nieuwe prijzen]", self.pagina("/voorwaarden/versie/2026-10-16/"))


class LiveGuardNieuwePrijzenTests(VaylideTestCase):
    """De prijsschakelaar kan in live-modus niet aan zonder bevestigde bedrijfsgegevens, activeringsdatum en goedgekeurde teksten."""

    def test_zonder_de_nieuwe_prijzen_verandert_er_niets_aan_de_open_punten(self):
        from core import privacyverklaring as pv

        self.assertEqual(pv.nieuwe_prijzen_open_points(), [])

    @V2
    @override_settings(COMPANY_CONFIRMED={"kvk": False, "btw": True, "adres": False, "email": True}, PRICING_V2_ACTIVATION="", TEXTS_DEFINITIVE=False)
    def test_met_de_nieuwe_prijzen_staan_alle_openstaande_bevestigingen_in_de_lijst(self):
        from core import privacyverklaring as pv

        punten = " | ".join(pv.nieuwe_prijzen_open_points())
        for deel in ("KvK-nummer", "vestigingsadres", "activeringsdatum", "VIERLIEF_TEKSTEN_DEFINITIEF"):
            self.assertIn(deel, punten)
        self.assertNotIn("btw-id", punten)

    @V2
    @override_settings(TEST_MODE=False, PRICING_V2_ACTIVATION="", TEXTS_DEFINITIVE=False)
    def test_live_weigert_de_nieuwe_prijzen_zolang_er_iets_openstaat(self):
        from core import privacyverklaring as pv

        self.assertEqual([f.id for f in pv.check_privacy_statement()], ["vaylide.E001"])

    @V2
    @override_settings(TEST_MODE=False, COMPANY_LEGAL_NAME="Voorbeeld", COMPANY_ADDRESS="Straat 1|1234 AB Plaats", EMAIL_MODE="smtp", ANTHROPIC_API_KEY="",
                       PRIVACY_EMAIL_PROVIDER="Voorbeeld Mail B.V. (Nederland)", PRIVACY_EMAIL_PROVIDER_CONFIRMED=True, COMPANY_CONFIRMED=ALLES_BEVESTIGD,
                       PRICING_V2_ACTIVATION="2026-11-01", TEXTS_DEFINITIVE=True)
    def test_live_laat_de_nieuwe_prijzen_toe_als_alles_bevestigd_is(self):
        from unittest import mock

        from core import privacyverklaring as pv

        with mock.patch.dict(pv.BESLUITEN, {key: "Vastgesteld door de eigenaar." for key in pv.BESLUITEN}):
            self.assertEqual(pv.check_privacy_statement(), [])


class BestaandeKlantenTests(VaylideTestCase):
    """Bestaande bestellingen behouden hun prijs, einddatum, voorwaardenversie en rechten, wat er ook met de prijsschakelaar gebeurt."""

    @staticmethod
    def vastgelegd(order):
        order.refresh_from_db()
        return (order.total_cents, order.terms_version, order.availability_months, order.package_code, sorted(order.features or []),
                order.terms_accepted_at, order.delivery_consent_text, order.service_consent_text)

    def test_een_bestelling_van_voor_de_nieuwe_prijzen_blijft_ongewijzigd_bij_aan_en_uitzetten(self):
        klant = self.make_customer()
        oud = self.make_invitation(owner=klant)
        self.pay(oud, klant)
        order = Order.objects.get(invitation=oud)
        voor = self.vastgelegd(order)
        self.assertEqual(order.terms_version, "2026-09-29")
        with V2:
            self.assertEqual(self.vastgelegd(order), voor)
            # De oude voorwaarden blijven voor deze klant bereikbaar, ook als pdf, en de bevestigingsmail blijft op de oude versie.
            for pad in ("/voorwaarden/versie/2026-09-29/", "/voorwaarden/pdf/2026-09-29/"):
                self.assertEqual(Client().get(pad).status_code, 200, pad)
        self.assertEqual(self.vastgelegd(order), voor)
        mail = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        self.assertEqual(mail.attach_terms_version, "2026-09-29")

    def test_een_bestelling_onder_de_nieuwe_prijzen_blijft_bij_terugdraaien_van_de_schakelaar_ongewijzigd(self):
        klant = self.make_customer()
        nieuw = self.make_invitation(owner=klant)
        with V2:
            payment = self.pay(nieuw, klant)
        order = Order.objects.get(pk=payment.order_id)
        voor = self.vastgelegd(order)
        self.assertEqual(order.terms_version, "2026-10-16")
        self.assertEqual(order.total_cents, 5995)
        # Schakelaar terug: de bestelling houdt prijs, einddatum en de versie waarmee de klant akkoord ging; die versie blijft bereikbaar.
        self.assertEqual(self.vastgelegd(order), voor)
        for pad in ("/voorwaarden/versie/2026-10-16/", "/voorwaarden/pdf/2026-10-16/", "/voorwaarden/download/2026-10-16/"):
            self.assertEqual(Client().get(pad).status_code, 200, pad)
        self.assertEqual(Payment.objects.get(order=order).status, Payment.Status.PAID)
        self.assertEqual(OutboundEmail.objects.get(order=order, kind="order_confirmation").attach_terms_version, "2026-10-16")
        # Nieuwe bestellingen krijgen met de schakelaar uit weer de oude versie; de eerdere bestelling blijft zoals ze was.
        weer = self.make_invitation(owner=klant)
        tweede = self.pay(weer, klant)
        self.assertEqual(Order.objects.get(pk=tweede.order_id).terms_version, "2026-09-29")
        self.assertEqual(self.vastgelegd(order), voor)


class EerdereVersieLabelTests(VaylideTestCase):
    """Het label boven de voorwaarden van 29 september: alleen presentatie, geen 'Concept' meer; tekst en versie blijven ongewijzigd."""

    def teksten(self):
        from core.voorwaarden_pdf import render_pdf

        client = Client()
        return {
            "pagina": client.get("/voorwaarden/versie/2026-09-29/").content.decode(),
            "download": client.get("/voorwaarden/download/2026-09-29/").content.decode(),
            "pdf": render_pdf("2026-09-29", compress=False),
        }

    def test_met_de_nieuwe_prijzen_heet_de_oude_versie_eerdere_versie_zonder_conceptmelding(self):
        with V2:
            self.assertEqual(voorwaarden.version_info("2026-09-29")["status"], "Eerdere versie")
            teksten = self.teksten()
        self.assertIn("Eerdere versie · versie 29 september 2026", teksten["pagina"])
        self.assertIn("Eerdere versie · versie 29 september 2026", teksten["download"])
        self.assertIn(b"Eerdere versie", teksten["pdf"])
        for naam in ("pagina", "download"):
            self.assertNotIn("Concept", teksten[naam], naam)
            self.assertNotIn("niet juridisch beoordeeld", teksten[naam], naam)
        self.assertNotIn(b"Concept", teksten["pdf"])
        self.assertNotIn(b"niet juridisch", teksten["pdf"])

    def test_zolang_de_oude_versie_nog_geldt_staat_er_geldende_versie(self):
        self.assertEqual(voorwaarden.version_info("2026-09-29")["status"], "Geldende versie")
        self.assertIn("Geldende versie · versie 29 september 2026", self.teksten()["pagina"])

    def test_tekst_en_versienummer_van_de_oude_versie_blijven_gelijk(self):
        self.assertEqual(voorwaarden.CURRENT, "2026-09-29")
        self.assertEqual(voorwaarden.VERSIONS["2026-09-29"]["template"], "core/voorwaarden/2026-09-29.html")
        self.assertIn(b"Essentieel", self.teksten()["pdf"])

    @override_settings(TEXTS_DEFINITIVE=False)
    def test_de_nieuwe_voorwaarden_blijven_een_concept_zolang_de_eigenaar_ze_niet_definitief_maakt(self):
        self.assertEqual(voorwaarden.version_info("2026-10-16")["status"], "Concept")

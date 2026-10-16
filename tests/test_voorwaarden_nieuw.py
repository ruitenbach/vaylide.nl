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

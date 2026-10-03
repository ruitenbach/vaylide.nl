"""De bestelbevestiging: de aangeleverde klanttekst staat erin, de toestemming (tijdstip en letterlijke tekst) en de versie van de voorwaarden komen uit
de bestelling zelf, en de bedrijfsgegevens zijn ongewijzigd."""
from django.test import override_settings
from django.utils import timezone

from core.company import as_text
from orders.models import Order, Payment
from orders.services import start_checkout
from processing.emails import send_order_confirmation
from processing.models import OutboundEmail

from .helpers import VaylideTestCase

SMTP = dict(EMAIL_MODE="smtp", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")

TEKSTEN = (
    "Je bestelling is bevestigd",
    "Bedankt voor je bestelling bij VAYLIDE. Je betaling is ontvangen en je digitale uitnodiging staat voor je klaar.",
    "Directe levering en bedenktijd",
    "Je hebt bij het afronden van je bestelling uitdrukkelijk gevraagd om de levering van je digitale kaart direct te laten beginnen, "
    "voordat de wettelijke bedenktijd is verstreken.",
    "Je hebt daarbij bevestigd dat je begrijpt dat je herroepingsrecht voor de digitale kaart vervalt zodra de levering is begonnen.",
    "Toestemming gegeven op:",
    "Online beschikbaarheid",
    "Je digitale uitnodiging wordt via VAYLIDE online beschikbaar gesteld volgens de afspraken die bij je bestelling en in de algemene voorwaarden staan.",
    "Algemene voorwaarden",
    "Op je bestelling zijn de algemene voorwaarden van toepassing die golden op het moment waarop je de bestelling hebt geplaatst.",
    "De bijbehorende versie van de algemene voorwaarden is als pdf bij deze e-mail gevoegd.",
    "Herroepingsrecht",
    "Voor de digitale kaart waarvoor je hierboven toestemming hebt gegeven voor directe levering, vervalt het herroepingsrecht zodra de levering is begonnen.",
    "Voor eventuele andere onderdelen van je bestelling waarop het herroepingsrecht nog van toepassing is, gelden de voorwaarden zoals beschreven in de algemene voorwaarden.",
    "Heb je hierover een vraag? Neem dan contact met ons op via het bestaande contactadres in deze e-mail.",
)


class BevestigingsmailTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer("koper@example.com")
        self.inv = self.make_invitation(owner=self.customer)

    def betaal(self):
        with override_settings(**SMTP):
            with self.captureOnCommitCallbacks(execute=True):
                payment = start_checkout(self.inv, user=self.customer, package_code="essentieel", optional_codes=[], terms_accepted=True,
                                         delivery_consent=True)
            self.provider_says(payment, Payment.Status.PAID)
        return Order.objects.get(invitation=self.inv, status=Order.Status.PAID)

    def opnieuw(self, order):
        """De mail opnieuw laten maken uit de (gewijzigde) bestelling."""
        OutboundEmail.objects.filter(order=order, kind="order_confirmation").delete()
        return send_order_confirmation(order)

    def test_de_aangeleverde_teksten_staan_erin_in_html_en_platte_tekst(self):
        mail = OutboundEmail.objects.get(order=self.betaal(), kind="order_confirmation")
        for tekst in TEKSTEN:
            self.assertIn(tekst, mail.body_html, tekst)
            self.assertIn(tekst, mail.body_text, tekst)
        self.assertNotIn("Herroepen kan binnen de bedenktijd", mail.body_html)
        self.assertNotIn("Levering en voorwaarden", mail.body_html)

    def test_toestemming_en_tijdstip_komen_uit_de_bestelling(self):
        order = self.betaal()
        order.delivery_consent_text = "TESTTEKST-uit-de-bestelling: ik wil direct leveren."
        order.delivery_consent_at = timezone.make_aware(timezone.datetime(2026, 10, 5, 14, 37))
        order.save(update_fields=["delivery_consent_text", "delivery_consent_at"])
        mail = self.opnieuw(order)
        for body in (mail.body_html, mail.body_text):
            self.assertIn("TESTTEKST-uit-de-bestelling: ik wil direct leveren.", body)
            self.assertIn("5 oktober 2026 14:37", body)

    def test_zonder_vastgelegde_toestemming_geen_bewering_over_toestemming(self):
        order = self.betaal()
        order.delivery_consent_at = None
        order.delivery_consent_text = ""
        order.save(update_fields=["delivery_consent_at", "delivery_consent_text"])
        mail = self.opnieuw(order)
        self.assertNotIn("Directe levering en bedenktijd", mail.body_html)
        self.assertNotIn("Toestemming gegeven op", mail.body_text)

    def test_versie_komt_uit_de_bestelling_en_zonder_het_woord_concept(self):
        order = self.betaal()
        self.assertEqual(order.terms_version, "2026-09-29")
        mail = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        self.assertIn("29 september 2026", mail.body_html)
        self.assertIn("Versie: 29 september 2026", mail.body_text)
        self.assertNotIn("concept", mail.body_html.lower())
        self.assertNotIn("concept", mail.body_text.lower())
        self.assertEqual(mail.attach_terms_version, "2026-09-29")

    def test_zonder_opgeslagen_versie_geen_verzonnen_versie_en_geen_bijlage(self):
        order = self.betaal()
        order.terms_version = ""
        order.save(update_fields=["terms_version"])
        mail = self.opnieuw(order)
        self.assertEqual(mail.attach_terms_version, "")
        self.assertNotIn("Algemene voorwaarden</h2>", mail.body_html)
        self.assertNotIn("Versie:", mail.body_text)

    def test_online_beschikbaarheid_alleen_bij_een_bestelling_met_online_periode(self):
        order = self.betaal()
        order.availability_months = 0
        order.save(update_fields=["availability_months"])
        mail = self.opnieuw(order)
        self.assertNotIn("Online beschikbaarheid", mail.body_html)
        self.assertNotIn("herroepingsrecht voor de online", mail.body_html.lower())     # nergens een bewering over de online dienst
        self.assertNotIn("online dienst", mail.body_html.lower().replace("online vayl", ""))

    def test_bedrijfsgegevens_en_dynamische_gegevens_ongewijzigd(self):
        order = self.betaal()
        mail = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        self.assertIn(as_text().splitlines()[0], mail.body_text)
        for regel in as_text().splitlines():
            self.assertIn(regel, mail.body_text)
        for dynamisch in (order.number, order.total_display, "Online tot en met", "Aankoopdatum"):
            self.assertIn(dynamisch, mail.body_html)
        self.assertIn("/account/", mail.body_html)                          # knop naar Mijn VAYLIDE
        self.assertIn("Hier de overeenkomst ontbinden", mail.body_html)     # de herroepingsfunctie blijft bereikbaar

    def test_aanhef_met_voornaam_of_zonder(self):
        order = self.betaal()
        self.assertIn("Hoi,", self.opnieuw(order).body_text)
        self.customer.name = "Zoë Jansen"
        self.customer.save(update_fields=["name"])
        order.refresh_from_db()
        mail = self.opnieuw(order)
        self.assertIn("Hoi Zoë,", mail.body_text)
        self.assertIn("Hoi Zoë,", mail.body_html)

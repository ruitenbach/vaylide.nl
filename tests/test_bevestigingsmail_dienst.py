"""De bestelbevestiging toont ook het vastgelegde verzoek om de online dienst direct te starten (artikel 9.3), met tijdstip en letterlijke tekst uit
de bestelling zelf. Bestellingen zonder dat verzoek (oudere bestellingen) krijgen geen kopje en geen fout."""
from django.test import override_settings
from django.utils import timezone

from core.voorwaarden import DELIVERY_CONSENT, SERVICE_CONSENT
from orders.models import Order, Payment
from orders.services import start_checkout
from processing.emails import send_order_confirmation
from processing.models import OutboundEmail

from .helpers import VaylideTestCase

SMTP = dict(EMAIL_MODE="smtp", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
KOP = "Start van de online dienst"


class DienstToestemmingInBevestigingTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer("koper@example.com")
        self.inv = self.make_invitation(owner=self.customer)

    def betaal(self, **toestemming):
        with override_settings(**SMTP):
            with self.captureOnCommitCallbacks(execute=True):
                payment = start_checkout(self.inv, user=self.customer, package_code="essentieel", optional_codes=[], terms_accepted=True, **toestemming)
            self.provider_says(payment, Payment.Status.PAID)
        return Order.objects.get(invitation=self.inv, status=Order.Status.PAID)

    def opnieuw(self, order):
        OutboundEmail.objects.filter(order=order, kind="order_confirmation").delete()
        return send_order_confirmation(order)

    def test_beide_toestemmingen_staan_met_tijdstip_en_exacte_tekst_in_html_en_tekst(self):
        order = self.betaal(delivery_consent=True, service_consent=True)
        order.service_consent_at = timezone.make_aware(timezone.datetime(2026, 10, 5, 14, 37))
        order.save(update_fields=["service_consent_at"])
        mail = self.opnieuw(order)
        for body in (mail.body_html, mail.body_text):
            self.assertIn(KOP, body)
            self.assertIn("5 oktober 2026 14:37", body)
            self.assertIn(DELIVERY_CONSENT, body.replace("&rdquo;", "").replace("&ldquo;", ""))
            self.assertIn(SERVICE_CONSENT, body)
            self.assertIn("Directe levering en bedenktijd", body)

    def test_de_tekst_komt_uit_de_bestelling_en_niet_uit_de_code(self):
        order = self.betaal(delivery_consent=True, service_consent=True)
        order.service_consent_text = "TESTTEKST-dienst-uit-de-bestelling."
        order.save(update_fields=["service_consent_text"])
        mail = self.opnieuw(order)
        for body in (mail.body_html, mail.body_text):
            self.assertIn("TESTTEKST-dienst-uit-de-bestelling.", body)
            self.assertNotIn(SERVICE_CONSENT, body)

    def test_het_dienstblok_staat_tussen_directe_levering_en_online_beschikbaarheid(self):
        mail = OutboundEmail.objects.get(order=self.betaal(delivery_consent=True, service_consent=True), kind="order_confirmation")
        for body in (mail.body_html, mail.body_text):
            self.assertLess(body.index("Directe levering en bedenktijd"), body.index(KOP))
            self.assertLess(body.index(KOP), body.index("Online beschikbaarheid"))

    def test_bestelling_zonder_dienstverzoek_geeft_geen_kopje_en_geen_fout(self):
        order = self.betaal(delivery_consent=True)
        self.assertIsNone(order.service_consent_at)
        mail = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        for body in (mail.body_html, mail.body_text):
            self.assertNotIn(KOP, body)
            self.assertNotIn("Vastgelegd verzoek", body)
            self.assertIn("Directe levering en bedenktijd", body)
            self.assertIn("Herroepingsrecht", body)

    def test_bestelling_zonder_enige_toestemming_geeft_geen_fout(self):
        order = self.betaal()
        order.delivery_consent_at = None
        order.delivery_consent_text = ""
        order.service_consent_at = None
        order.service_consent_text = ""
        order.save(update_fields=["delivery_consent_at", "delivery_consent_text", "service_consent_at", "service_consent_text"])
        mail = self.opnieuw(order)
        for body in (mail.body_html, mail.body_text):
            self.assertNotIn(KOP, body)
            self.assertNotIn("Directe levering en bedenktijd", body)
            self.assertIn("Je bestelling is bevestigd", body)

    def test_voorwaarden_pdf_blijft_bijgevoegd(self):
        order = self.betaal(delivery_consent=True, service_consent=True)
        mail = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        self.assertTrue(mail.attach_terms_version)

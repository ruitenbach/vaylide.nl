"""Mollie in testmodus (testsleutel, geen echt geld): alleen een door Mollie bevestigde betaling telt,
dubbele meldingen zijn veilig, de webhook werkt achter het wachtwoord van de testversie en een
live-sleutel wordt in testmodus geweigerd. De Mollie-API is hier nagebootst."""
import json
import os
import subprocess
import sys
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.test import Client, override_settings

from invitations.models import Invitation
from orders.models import Order, Payment, PaymentEvent
from orders.providers import MollieProvider, ProviderError
from orders.services import CheckoutError, start_checkout
from processing.models import Job

from .helpers import VaylideTestCase


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeMollie:
    """Houdt per betaling de status 'bij Mollie' bij, zoals de testpagina van Mollie die zet."""

    def __init__(self):
        self.status = "open"
        self.calls = []

    def __call__(self, request, timeout=0):
        self.calls.append((request.get_method(), request.full_url))
        if request.get_method() == "POST":
            ref = "tr_testmodus" + str(sum(1 for m, _ in self.calls if m == "POST"))
            return _Response({"id": ref, "_links": {"checkout": {"href": f"https://www.mollie.com/checkout/test-mode?id={ref}"}}})
        return _Response({"id": "tr_testmodus1", "status": self.status, "amount": {"value": "39.00", "currency": "EUR"},
                          "method": "ideal" if self.status == "paid" else None,
                          "paidAt": "2026-09-29T10:00:00+00:00" if self.status == "paid" else None})


class MollieTestModeTests(VaylideTestCase):
    def setUp(self):
        # Na de standaardinstellingen van VaylideTestCase (die zetten de testprovider).
        mollie = override_settings(PAYMENT_PROVIDER="mollie", MOLLIE_API_KEY="test_nagebootst", BASE_URL="https://vaylide.onrender.com",
                                   PREVIEW_PASSWORD="lang-en-geheim-wachtwoord", PREVIEW_USER="voorbeeld")
        mollie.enable()
        self.addCleanup(mollie.disable)
        cache.clear()
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer)
        self.mollie = FakeMollie()
        patcher = mock.patch("orders.providers.urllib.request.urlopen", side_effect=self.mollie)
        patcher.start()
        self.addCleanup(patcher.stop)

    def checkout(self):
        with self.captureOnCommitCallbacks(execute=True):
            return start_checkout(self.inv, user=self.customer, package_code="essentieel", optional_codes=[], terms_accepted=True)

    def webhook(self, ref="tr_testmodus1"):
        # Zonder wachtwoord, zoals Mollie hem stuurt.
        with self.captureOnCommitCallbacks(execute=True):
            return Client().post("/webhooks/betaling/mollie/", {"id": ref})

    def test_checkout_sends_https_webhook_and_redirects_to_mollie(self):
        payment = self.checkout()
        self.assertTrue(payment.checkout_url.startswith("https://www.mollie.com/checkout/"))
        self.assertEqual(payment.provider, "mollie")
        self.assertEqual(payment.status, Payment.Status.OPEN)
        self.assertEqual(self.mollie.calls[0][0], "POST")
        self.assertTrue(payment.order.test_mode)

    def test_paid_only_after_mollie_confirms_and_duplicates_are_safe(self):
        payment = self.checkout()
        # Mollie meldt 'open': nog niets betaald of gepubliceerd.
        self.assertEqual(self.webhook().status_code, 200)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.OPEN)
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.status, Invitation.Status.DRAFT)
        # Mollie bevestigt de betaling; daarna nog drie dubbele meldingen.
        self.mollie.status = "paid"
        for _ in range(4):
            self.assertEqual(self.webhook().status_code, 200)
        payment.refresh_from_db()
        order = Order.objects.get(pk=payment.order_id)
        self.inv.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(self.inv.status, Invitation.Status.LIVE)
        self.assertEqual(Job.objects.filter(kind="fulfil_order").count(), 1)
        self.assertEqual(PaymentEvent.objects.filter(payment=payment, outcome__startswith="Al verwerkt").count(), 3)
        # Elke melding vroeg de status zelf bij Mollie op.
        self.assertEqual(sum(1 for method, _ in self.mollie.calls if method == "GET"), 5)

    def test_cancelled_payment_does_not_publish_and_can_be_retried(self):
        payment = self.checkout()
        self.mollie.status = "canceled"
        self.webhook()
        payment.refresh_from_db()
        order = Order.objects.get(pk=payment.order_id)
        self.inv.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.CANCELED)
        self.assertNotEqual(order.status, Order.Status.PAID)
        self.assertEqual(self.inv.status, Invitation.Status.DRAFT)
        self.assertEqual(Job.objects.filter(kind="fulfil_order").count(), 0)
        client = Client(HTTP_AUTHORIZATION="Basic dm9vcmJlZWxkOmxhbmctZW4tZ2VoZWltLXdhY2h0d29vcmQ=")
        client.force_login(self.customer)
        self.assertEqual(client.get(f"/bestelling/{order.uid}/status.json").json()["phase"], "cancelled")
        retry = client.post(f"/bestelling/{order.uid}/opnieuw-betalen/")
        self.assertEqual(retry.status_code, 302)
        self.assertTrue(retry["Location"].startswith("https://www.mollie.com/checkout/"))

    def test_webhook_passes_the_preview_password_but_pages_do_not(self):
        self.checkout()
        self.assertEqual(self.webhook().status_code, 200)
        self.assertEqual(Client().get("/").status_code, 401)
        self.assertEqual(Client().get("/betalen/test/tst_x/").status_code, 401)

    def test_fake_status_in_webhook_is_ignored(self):
        payment = self.checkout()
        with self.captureOnCommitCallbacks(execute=True):
            Client().post("/webhooks/betaling/mollie/", {"id": "tr_testmodus1", "status": "paid"})
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.OPEN)

    def test_banner_says_mollie_test_payments(self):
        client = Client(HTTP_AUTHORIZATION="Basic dm9vcmJlZWxkOmxhbmctZW4tZ2VoZWltLXdhY2h0d29vcmQ=")
        self.assertContains(client.get("/"), "Mollie-testbetalingen, er wordt niets afgeschreven")


class LiveKeyBlockedTests(VaylideTestCase):
    def test_provider_refuses_live_key_in_test_mode(self):
        live = override_settings(PAYMENT_PROVIDER="mollie", MOLLIE_API_KEY="live_niet_in_testmodus")
        live.enable()
        self.addCleanup(live.disable)
        self.assertTrue(settings.TEST_MODE)
        with self.assertRaises(ProviderError):
            MollieProvider()
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        with mock.patch("orders.providers.urllib.request.urlopen") as urlopen:
            with self.assertRaises(CheckoutError):
                start_checkout(inv, user=customer, package_code="essentieel", optional_codes=[], terms_accepted=True)
            urlopen.assert_not_called()

    def test_site_does_not_start_with_live_key_in_test_mode(self):
        env = {**os.environ, "VIERLIEF_MODE": "test", "VIERLIEF_PAYMENT_PROVIDER": "mollie", "MOLLIE_API_KEY": "live_x",
               "DJANGO_SETTINGS_MODULE": "config.settings"}
        result = subprocess.run([sys.executable, "-c", "import django; django.setup()"], env=env, cwd=settings.BASE_DIR,
                                capture_output=True, text=True, timeout=60)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Mollie-testsleutel", result.stderr)

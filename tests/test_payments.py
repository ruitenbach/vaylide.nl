"""Controle 1: betalingen, herhaalde meldingen en de Mollie-koppeling (met gesimuleerde API)."""
import json
from unittest import mock

from django.test import Client, override_settings

from invitations.models import Invitation
from orders.models import Order, Payment, PaymentEvent
from orders.providers import MollieProvider, RemoteStatus
from orders.services import apply_remote_status, start_checkout
from processing.models import Job, OutboundEmail

from .helpers import VaylideTestCase


class PaymentOutcomeTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer)
        self.client_c = Client()
        self.client_c.force_login(self.customer)

    def checkout(self, package="essentieel"):
        with self.captureOnCommitCallbacks(execute=True):
            return start_checkout(self.inv, user=self.customer, package_code=package, optional_codes=[], terms_accepted=True)

    def test_cancelled_payment_keeps_design_and_allows_retry(self):
        payment = self.checkout()
        self.provider_says(payment, Payment.Status.CANCELED)
        order = payment.order
        order.refresh_from_db()
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.status, Invitation.Status.DRAFT)
        self.assertEqual(order.status, Order.Status.PENDING)
        page = self.client_c.get(f"/bestelling/{order.uid}/")
        self.assertContains(page, "Betaling afgebroken")
        response = self.client_c.post(f"/bestelling/{order.uid}/opnieuw-betalen/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(order.payments.count(), 2)
        retry = order.latest_payment
        self.provider_says(retry, Payment.Status.PAID)
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.status, Invitation.Status.LIVE)

    def test_failed_and_expired_payments_do_not_publish(self):
        payment = self.checkout()
        self.provider_says(payment, Payment.Status.FAILED)
        payment.order.refresh_from_db()
        self.assertEqual(payment.order.status, Order.Status.FAILED)
        self.assertContains(self.client_c.get(f"/bestelling/{payment.order.uid}/"), "Betaling niet gelukt")
        second = self.checkout()
        self.provider_says(second, Payment.Status.EXPIRED)
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.status, Invitation.Status.DRAFT)
        self.assertFalse(Job.objects.filter(kind="fulfil_order").exists())

    def test_return_page_alone_never_publishes(self):
        payment = self.checkout()
        for _ in range(3):
            self.client_c.get(f"/bestelling/{payment.order.uid}/")
            self.client_c.get(f"/bestelling/{payment.order.uid}/status.json")
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.status, Invitation.Status.DRAFT)
        self.assertEqual(Payment.objects.get(pk=payment.pk).status, Payment.Status.OPEN)

    def test_repeated_webhooks_do_not_duplicate_anything(self):
        payment = self.checkout()
        payment.test_remote_status = Payment.Status.PAID
        payment.save()
        anon = Client()
        for _ in range(4):
            with self.captureOnCommitCallbacks(execute=True):
                response = anon.post("/webhooks/betaling/test/", {"id": payment.provider_ref})
            self.assertEqual(response.status_code, 200)
        self.assertEqual(Job.objects.filter(kind="fulfil_order").count(), 1)
        self.assertEqual(OutboundEmail.objects.filter(kind="order_confirmation").count(), 1)
        self.assertEqual(OutboundEmail.objects.filter(kind="invitation_live").count(), 1)
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.versions.filter(published_at__isnull=False).count(), 1)
        self.assertEqual(PaymentEvent.objects.filter(payment=payment).count(), 4)
        self.assertEqual(PaymentEvent.objects.filter(payment=payment, outcome__startswith="Al verwerkt").count(), 3)
        first_until = self.inv.available_until
        # Nog een melding na afloop verandert de beschikbaarheid niet.
        with self.captureOnCommitCallbacks(execute=True):
            anon.post("/webhooks/betaling/test/", {"id": payment.provider_ref})
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.available_until, first_until)

    def test_webhook_cannot_fake_a_payment(self):
        payment = self.checkout()
        with self.captureOnCommitCallbacks(execute=True):
            Client().post("/webhooks/betaling/test/", {"id": payment.provider_ref, "status": "paid"})
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.OPEN)
        self.assertEqual(Client().post("/webhooks/betaling/test/", {"id": "tst_onbekend"}).status_code, 200)
        self.assertEqual(Client().post("/webhooks/betaling/mollie/", {"id": "tr_x"}).status_code, 404)

    def test_amount_mismatch_is_not_published(self):
        payment = self.checkout()
        with self.captureOnCommitCallbacks(execute=True):
            apply_remote_status(payment, RemoteStatus(status=Payment.Status.PAID, amount_cents=100), source="webhook")
        payment.order.refresh_from_db()
        self.inv.refresh_from_db()
        self.assertEqual(payment.order.fulfilment_status, Order.Fulfilment.ATTENTION)
        self.assertEqual(self.inv.status, Invitation.Status.DRAFT)
        self.assertTrue(OutboundEmail.objects.filter(kind="owner_order_attention").exists())

    def test_old_payment_paid_after_new_checkout_is_flagged_as_duplicate(self):
        first = self.checkout()
        second = self.checkout()  # klant begon opnieuw; eerste bestelling vervalt
        first.order.refresh_from_db()
        self.assertEqual(first.order.status, Order.Status.CANCELLED)
        self.provider_says(second, Payment.Status.PAID)
        self.provider_says(first, Payment.Status.PAID)  # toch nog betaald in het oude tabblad
        first.order.refresh_from_db()
        self.assertEqual(first.order.status, Order.Status.PAID)
        self.assertEqual(first.order.fulfilment_status, Order.Fulfilment.ATTENTION)
        self.assertIn("Dubbele betaling", first.order.fulfilment_note)

    def test_already_paid_invitation_cannot_be_ordered_again(self):
        self.pay(self.inv, self.customer)
        response = self.client_c.post(f"/maken/{self.inv.uid}/bestellen/", {"actie": "betalen", "package": "essentieel", "terms": "on", "direct_leveren": "on"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)

    def test_manual_status_change_is_logged(self):
        payment = self.checkout()
        staff_user = self.make_staff()
        staff = Client()
        staff.force_login(staff_user)
        order = payment.order
        staff.post(f"/beheer/bestellingen/{order.uid}/", {"actie": "status", "status": "cancelled"})
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        event = PaymentEvent.objects.get(payment=payment, source="beheer")
        self.assertIn("handmatig", event.outcome)
        self.assertIn(staff_user.email, event.outcome)
        # Een klant kan dit niet.
        self.assertEqual(self.client_c.post(f"/beheer/bestellingen/{order.uid}/", {"actie": "status", "status": "paid"}).status_code, 404)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)

    def test_test_checkout_unavailable_outside_test_mode(self):
        payment = self.checkout()
        with override_settings(TEST_MODE=False):
            self.assertEqual(Client().get(f"/betalen/test/{payment.provider_ref}/").status_code, 404)


class _FakeResponse:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class MollieProviderTests(VaylideTestCase):
    def setUp(self):
        mollie = override_settings(PAYMENT_PROVIDER="mollie", MOLLIE_API_KEY="test_dummy_sleutel")
        mollie.enable()
        self.addCleanup(mollie.disable)

    def test_create_and_webhook_fetch_status_server_side(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        requests = []

        def fake_urlopen(request, timeout=0):
            requests.append(request)
            if request.get_method() == "POST":
                body = json.loads(request.data.decode())
                self.assertEqual(body["amount"], {"currency": "EUR", "value": "39.00"})
                self.assertTrue(body["webhookUrl"].endswith("/webhooks/betaling/mollie/"))
                return _FakeResponse({"id": "tr_test123", "_links": {"checkout": {"href": "https://www.mollie.com/checkout/test"}}})
            return _FakeResponse({"id": "tr_test123", "status": "paid", "amount": {"value": "39.00", "currency": "EUR"}, "method": "ideal", "paidAt": "2026-09-26T10:00:00+00:00"})

        with mock.patch("orders.providers.urllib.request.urlopen", side_effect=fake_urlopen):
            with self.captureOnCommitCallbacks(execute=True):
                payment = start_checkout(inv, user=customer, package_code="essentieel", optional_codes=[], terms_accepted=True)
            self.assertEqual(payment.checkout_url, "https://www.mollie.com/checkout/test")
            self.assertEqual(requests[0].headers["Authorization"], "Bearer test_dummy_sleutel")
            with self.captureOnCommitCallbacks(execute=True):
                response = Client().post("/webhooks/betaling/mollie/", {"id": "tr_test123"})
        self.assertEqual(response.status_code, 200)
        payment.refresh_from_db()
        inv.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.PAID)
        self.assertEqual(payment.method, "ideal")
        self.assertEqual(inv.status, Invitation.Status.LIVE)
        self.assertEqual(requests[-1].get_method(), "GET")

    def test_provider_outage_returns_error_so_mollie_retries(self):
        import urllib.error

        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        with mock.patch("orders.providers.urllib.request.urlopen",
                        return_value=_FakeResponse({"id": "tr_x", "_links": {"checkout": {"href": "https://www.mollie.com/checkout/x"}}})):
            payment = start_checkout(inv, user=customer, package_code="essentieel", optional_codes=[], terms_accepted=True)
        with mock.patch("orders.providers.urllib.request.urlopen", side_effect=urllib.error.URLError("down")):
            response = Client().post("/webhooks/betaling/mollie/", {"id": "tr_x"})
        self.assertEqual(response.status_code, 503)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.OPEN)

    def test_mollie_status_mapping(self):
        provider = MollieProvider(api_key="test_x")
        payment = Payment(provider_ref="tr_1", amount_cents=100)
        for remote, expected in [("open", "open"), ("pending", "pending"), ("authorized", "pending"), ("canceled", "canceled"), ("expired", "expired"), ("failed", "failed")]:
            with mock.patch("orders.providers.urllib.request.urlopen", return_value=_FakeResponse({"status": remote, "amount": {"value": "1.00", "currency": "EUR"}})):
                self.assertEqual(provider.fetch(payment).status, expected)

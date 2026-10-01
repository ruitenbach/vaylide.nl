"""Controle van de automatische orderverwerking (30 september 2026): vertraagde meldingen, open betalingen, onderbreking
en herhaling, looptijd per pakket, verlopen, en de grenzen van e-mailbezorging. Zie docs/AUTOMATISERING.md."""
from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import Client, override_settings
from django.utils import timezone

from core.privacy import apply_retention
from invitations.availability import end_of_availability
from invitations.models import Invitation, InvitationVersion
from orders.models import Order, Payment
from orders.providers import RemoteStatus
from orders.services import apply_remote_status, start_checkout, sync_payment
from orders.stuck import stuck_orders
from processing.jobs import process_due, run_job
from processing.models import Job, OutboundEmail

from .helpers import VaylideTestCase


class AutomationTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer)

    def checkout(self, package="essentieel", extras=None):
        with self.captureOnCommitCallbacks(execute=True):
            return start_checkout(self.inv, user=self.customer, package_code=package, optional_codes=extras or [],
                                  terms_accepted=True, delivery_consent=True)

    def webhook(self, payment, status, *, paid_at=None):
        with self.captureOnCommitCallbacks(execute=True):
            return apply_remote_status(payment, RemoteStatus(status=status, amount_cents=payment.amount_cents, currency="EUR",
                                                             method="ideal", paid_at=paid_at), source="webhook")

    def test_normal_order_needs_no_button(self):
        """Betalen → (webhook) → publiceren → e-mails, zonder enige handeling in het beheer."""
        payment = self.checkout()
        self.webhook(payment, Payment.Status.PAID)
        order = Order.objects.get(pk=payment.order_id)
        self.inv.refresh_from_db()
        self.assertEqual((order.status, order.fulfilment_status), (Order.Status.PAID, Order.Fulfilment.DONE))
        self.assertTrue(self.inv.is_publicly_visible)
        self.assertEqual(Client().get(self.inv.public_path).status_code, 200)
        kinds = sorted(OutboundEmail.objects.filter(order=order).values_list("kind", flat=True))
        self.assertEqual(kinds, ["invitation_live", "order_confirmation"])
        self.assertFalse(Job.objects.exclude(status=Job.Status.DONE).exists())
        self.assertEqual(stuck_orders(), [])

    def test_customer_closes_window_and_webhook_arrives_late(self):
        payment = self.checkout()  # klant komt nooit terug op de bedankpagina
        paid_at = timezone.now() - timedelta(hours=5)
        self.webhook(payment, Payment.Status.PAID, paid_at=paid_at)
        order = Order.objects.get(pk=payment.order_id)
        self.assertEqual(order.fulfilment_status, Order.Fulfilment.DONE)
        # De einddatum telt vanaf de betaling bij Mollie, niet vanaf het (late) moment van de melding.
        self.assertEqual(order.paid_at, paid_at)
        self.assertEqual(order.ends_at, end_of_availability(paid_at, 6))
        # Een herhaalde, nog latere melding verandert niets.
        self.webhook(payment, Payment.Status.PAID, paid_at=timezone.now())
        order.refresh_from_db()
        self.assertEqual(order.ends_at, end_of_availability(paid_at, 6))
        self.assertEqual(InvitationVersion.objects.filter(invitation=self.inv).count(), 1)

    def test_open_and_pending_payments_do_not_publish(self):
        payment = self.checkout()
        for status in (Payment.Status.OPEN, Payment.Status.PENDING):
            self.webhook(payment, status)
            self.inv.refresh_from_db()
            self.assertEqual(self.inv.status, Invitation.Status.DRAFT)
            self.assertEqual(Order.objects.get(pk=payment.order_id).status, Order.Status.PENDING)
        # Zonder webhook en zonder terugkeer blijft een open betaling open; ze staat (bewust) niet bij vastgelopen
        # bestellingen, want er is niets betaald. Zie docs/AUTOMATISERING.md: er is geen periodieke controle bij Mollie.
        self.assertEqual(stuck_orders(), [])

    def test_customer_return_checks_status_server_side(self):
        payment = self.checkout()
        Payment.objects.filter(pk=payment.pk).update(test_remote_status=Payment.Status.PAID)
        c = Client()
        c.force_login(self.customer)
        with self.captureOnCommitCallbacks(execute=True):
            page = c.get(f"/bestelling/{payment.order.uid}/")
        self.assertEqual(page.status_code, 200)
        self.inv.refresh_from_db()
        self.assertTrue(self.inv.is_publicly_visible)

    def test_interruption_after_payment_is_picked_up_later_without_shifting_the_end(self):
        payment = self.checkout()
        paid_at = timezone.now() - timedelta(days=1)
        # De server stopt direct na het vastleggen van de betaling: de taak staat klaar maar liep niet.
        with mock.patch("processing.jobs.run_job"):
            self.webhook(payment, Payment.Status.PAID, paid_at=paid_at)
        order = Order.objects.get(pk=payment.order_id)
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.fulfilment_status, Order.Fulfilment.NONE)
        self.assertEqual([o.pk for o, _ in stuck_orders()], [order.pk])  # zichtbaar in beheer na 15 minuten
        # De geplande taak (cron) pakt hem op; een dag later telt nog steeds vanaf de betaling.
        with self.captureOnCommitCallbacks(execute=True):
            process_due()
        with self.captureOnCommitCallbacks(execute=True):
            process_due()
        order.refresh_from_db()
        self.assertEqual(order.fulfilment_status, Order.Fulfilment.DONE)
        self.assertEqual(order.ends_at, end_of_availability(paid_at, 6))
        self.assertEqual(OutboundEmail.objects.filter(order=order, kind="invitation_live").count(), 1)

    def test_rerunning_a_finished_fulfilment_job_changes_nothing(self):
        payment = self.checkout()
        self.webhook(payment, Payment.Status.PAID)
        order = Order.objects.get(pk=payment.order_id)
        ends = order.ends_at
        job = Job.objects.get(kind="fulfil_order")
        Job.objects.filter(pk=job.pk).update(status=Job.Status.PENDING)
        with self.captureOnCommitCallbacks(execute=True):
            run_job(job.pk)
        order.refresh_from_db()
        self.assertEqual(order.ends_at, ends)
        self.assertEqual(InvitationVersion.objects.filter(invitation=self.inv).count(), 1)
        self.assertEqual(OutboundEmail.objects.filter(order=order).count(), 2)
        self.assertEqual(Order.objects.filter(invitation=self.inv).count(), 1)

    def test_compleet_is_twelve_months_and_extension_adds_twelve(self):
        payment = self.checkout(package="compleet", extras=["langer-online"])
        paid_at = timezone.now()
        self.webhook(payment, Payment.Status.PAID, paid_at=paid_at)
        order = Order.objects.get(pk=payment.order_id)
        self.assertEqual(order.availability_months, 24)
        self.assertEqual(order.ends_at, end_of_availability(paid_at, 24))

    def test_after_the_end_the_card_is_offline_even_before_the_nightly_job(self):
        payment = self.checkout()
        self.webhook(payment, Payment.Status.PAID)
        self.inv.refresh_from_db()
        Invitation.objects.filter(pk=self.inv.pk).update(available_until=timezone.now() - timedelta(minutes=1))
        self.assertNotEqual(Client().get(self.inv.public_path).status_code, 200)
        apply_retention()
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.status, Invitation.Status.EXPIRED)

    @override_settings(EMAIL_MODE="smtp", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend", JOBS_RUN_INLINE=False)
    def test_email_is_at_least_once_not_exactly_once(self):
        """Als het versturen lukt maar het vastleggen daarna mislukt, stuurt de herhaling hem opnieuw."""
        mail.outbox = []
        payment = self.checkout()
        self.webhook(payment, Payment.Status.PAID)
        process_due()  # publiceren; de e-mails staan daarna klaar maar zijn nog niet verstuurd
        email = OutboundEmail.objects.get(kind="order_confirmation")
        job = Job.objects.get(unique_key=f"email:{email.pk}")
        original_save = OutboundEmail.save
        calls = {"n": 0}

        def flaky_save(obj, *args, **kwargs):
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("database even weg na het versturen")
            return original_save(obj, *args, **kwargs)

        sent_before = len(mail.outbox)
        with mock.patch.object(OutboundEmail, "save", flaky_save):
            run_job(job.pk)
        Job.objects.filter(pk=job.pk).update(run_after=timezone.now() - timedelta(seconds=1))
        run_job(job.pk)
        confirmations = [m for m in mail.outbox[sent_before:] if "Bevestiging van je bestelling" in m.subject]
        self.assertEqual(len(confirmations), 2)

    @override_settings(EMAIL_MODE="smtp", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_buyer_mail_has_link_access_and_qr(self):
        mail.outbox = []
        payment = self.checkout()
        self.webhook(payment, Payment.Status.PAID)
        self.inv.refresh_from_db()
        live = [m for m in mail.outbox if "staat online" in m.subject]
        self.assertEqual(len(live), 1)
        body = live[0].body
        self.assertIn(f"/account/uitnodiging/{self.inv.uid}/", body)
        self.assertEqual(live[0].attachments, [])  # geen losse bijlage meer: de QR-code staat in de HTML
        self.assertIn("qr-code-uitnodiging.png", live[0].message().as_string())
        self.assertEqual(live[0].to, [self.customer.email])

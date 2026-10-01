"""Controle 1: mislukte publicatie en e-mail, automatisch en handmatig opnieuw proberen."""
from datetime import timedelta
from unittest import mock

from django.core.cache import cache
from django.test import Client
from django.utils import timezone

from invitations.models import Invitation
from orders.models import Order
from processing.emails import set_fault
from processing.jobs import process_due, retry
from processing.models import Job, OutboundEmail

from .helpers import VaylideTestCase


class FailedPublicationTests(VaylideTestCase):
    def setUp(self):
        cache.clear()
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer)
        self.c = Client()
        self.c.force_login(self.customer)

    def test_publication_failure_keeps_paid_order_and_recovers(self):
        set_fault("publish", 1)
        payment = self.pay(self.inv, self.customer)
        order = payment.order
        order.refresh_from_db()
        job = Job.objects.get(kind="fulfil_order")
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(job.status, Job.Status.FAILED)
        self.assertIn("Gesimuleerde storing", job.last_error)
        self.assertEqual(order.fulfilment_status, Order.Fulfilment.PROCESSING)
        self.assertEqual(Invitation.objects.get(pk=self.inv.pk).status, Invitation.Status.DRAFT)
        # De klant ziet een begrijpelijke status (betaald, wordt verwerkt).
        page = self.c.get(f"/bestelling/{order.uid}/")
        self.assertContains(page, "Betaling ontvangen")
        # Bevestiging is al verstuurd, want betaling is binnen.
        self.assertTrue(OutboundEmail.objects.filter(kind="order_confirmation", order=order).exists())

        # Automatische herhaling (cron/worker) na de wachttijd.
        Job.objects.filter(pk=job.pk).update(run_after=timezone.now() - timedelta(seconds=1))
        with self.captureOnCommitCallbacks(execute=True):
            process_due()
        job.refresh_from_db()
        order.refresh_from_db()
        self.inv.refresh_from_db()
        self.assertEqual(job.status, Job.Status.DONE)
        self.assertEqual(order.fulfilment_status, Order.Fulfilment.DONE)
        self.assertEqual(self.inv.status, Invitation.Status.LIVE)
        self.assertContains(self.c.get(f"/bestelling/{order.uid}/"), self.inv.public_url)
        self.assertEqual(OutboundEmail.objects.filter(kind="order_confirmation").count(), 1)

    def test_repeated_failures_become_visible_to_owner(self):
        set_fault("publish", 20)
        payment = self.pay(self.inv, self.customer)
        job = Job.objects.get(kind="fulfil_order")
        for _ in range(job.max_attempts):
            Job.objects.filter(pk=job.pk).update(run_after=timezone.now() - timedelta(seconds=1))
            with self.captureOnCommitCallbacks(execute=True):
                process_due()
        job.refresh_from_db()
        payment.order.refresh_from_db()
        self.assertEqual(job.status, Job.Status.DEAD)
        self.assertEqual(payment.order.fulfilment_status, Order.Fulfilment.ATTENTION)
        self.assertTrue(OutboundEmail.objects.filter(kind="owner_failure").exists())
        self.assertContains(self.c.get(f"/bestelling/{payment.order.uid}/"), "het VAYLIDE-team is ingeschakeld")
        # Eigenaar ziet het in het beheer en start handmatig opnieuw.
        set_fault("publish", 0)
        staff = self.make_staff()
        admin = Client()
        admin.force_login(staff)
        dashboard = admin.get("/beheer/")
        self.assertContains(dashboard, "mislukte verwerkingen")
        with self.captureOnCommitCallbacks(execute=True):
            admin.post(f"/beheer/bestellingen/{payment.order.uid}/", {"actie": "opnieuw-verwerken"})
        self.inv.refresh_from_db()
        payment.order.refresh_from_db()
        self.assertEqual(self.inv.status, Invitation.Status.LIVE)
        self.assertEqual(payment.order.fulfilment_status, Order.Fulfilment.DONE)


class FailedEmailTests(VaylideTestCase):
    def setUp(self):
        cache.clear()

    def test_email_failure_does_not_block_publication(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        set_fault("email", 5)
        payment = self.pay(inv, customer)
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invitation.Status.LIVE)
        failed = OutboundEmail.objects.filter(status=OutboundEmail.Status.FAILED)
        self.assertTrue(failed.exists())
        c = Client()
        c.force_login(customer)
        page = c.get(f"/bestelling/{payment.order.uid}/")
        self.assertContains(page, inv.public_url)  # link beschikbaar ondanks mislukte e-mail
        self.assertContains(page, "wordt opnieuw geprobeerd")
        # Later lukt de verzending alsnog.
        set_fault("email", 0)
        Job.objects.filter(kind="send_email").update(run_after=timezone.now() - timedelta(seconds=1))
        with self.captureOnCommitCallbacks(execute=True):
            process_due()
        self.assertFalse(OutboundEmail.objects.filter(status=OutboundEmail.Status.FAILED).exists())
        self.assertEqual(OutboundEmail.objects.filter(kind="invitation_live").count(), 1)

    def test_smtp_errors_are_recorded_and_retried(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        with self.settings(EMAIL_MODE="smtp", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
            with mock.patch("django.core.mail.message.EmailMessage.send", side_effect=ConnectionRefusedError("smtp down")):
                self.pay(inv, customer)
            live = OutboundEmail.objects.get(kind="invitation_live")
            self.assertEqual(live.status, OutboundEmail.Status.FAILED)
            self.assertIn("smtp down", live.last_error)
            job = Job.objects.get(unique_key=f"email:{live.pk}")
            with self.captureOnCommitCallbacks(execute=True):
                retry(job)
            live.refresh_from_db()
            self.assertEqual(live.status, OutboundEmail.Status.SENT)
            from django.core import mail

            sent = [m for m in mail.outbox if m.subject.endswith("Je uitnodiging staat online")]
            self.assertEqual(len(sent), 1)
            self.assertIn("cid:qr-uitnodiging", sent[0].alternatives[0][0])  # QR-code staat in de mail zelf

"""Verwerking na een bevestigde betaling: publiceren, levering aan de koper als aparte taak, veilige herhalingen
en het overzicht van vastgelopen bestellingen in het beheer. Betaling en e-mail zijn nagebootst (testmodus)."""
from datetime import timedelta

from django.test import Client
from django.utils import timezone

from invitations.models import Invitation
from orders.models import Order
from orders.stuck import restart, stuck_orders
from processing.emails import set_fault
from processing.jobs import process_due, run_job
from processing.models import Job, OutboundEmail

from .helpers import VaylideTestCase


class DeliveryTests(VaylideTestCase):
    def test_publish_and_delivery_are_separate_jobs(self):
        inv = self.published()
        order = inv.orders.get()
        self.assertEqual(Job.objects.filter(kind="fulfil_order", order=order, status=Job.Status.DONE).count(), 1)
        self.assertEqual(Job.objects.filter(kind="deliver_order", order=order, status=Job.Status.DONE).count(), 1)
        self.assertEqual(OutboundEmail.objects.filter(kind="invitation_live", order=order).count(), 1)
        self.assertEqual(inv.status, Invitation.Status.LIVE)

    def test_interruption_after_publishing_still_delivers_exactly_once(self):
        inv = self.published()
        order = inv.orders.get()
        # Bootst een onderbreking na te publiceren na: de levering en de e-mail zijn weg.
        OutboundEmail.objects.filter(order=order).delete()
        Job.objects.filter(kind__in=["deliver_order", "send_email"], order=order).delete()
        fulfil = Job.objects.get(kind="fulfil_order", order=order)
        for _ in range(3):
            fulfil.status = Job.Status.PENDING
            fulfil.save()
            with self.captureOnCommitCallbacks(execute=True):
                run_job(fulfil.pk)
        self.assertEqual(Job.objects.filter(kind="deliver_order", order=order).count(), 1)
        self.assertEqual(OutboundEmail.objects.filter(kind="invitation_live", order=order).count(), 1)
        inv.refresh_from_db()
        self.assertEqual(inv.versions.filter(published_at__isnull=False).count(), 1)

    def test_email_failure_is_retried_without_duplicates(self):
        set_fault("email", 2)
        inv = self.published()
        order = inv.orders.get()
        live = OutboundEmail.objects.get(kind="invitation_live", order=order)
        self.assertNotIn(live.status, (OutboundEmail.Status.SENT, OutboundEmail.Status.TEST))
        Job.objects.filter(status=Job.Status.FAILED).update(run_after=timezone.now())
        with self.captureOnCommitCallbacks(execute=True):
            process_due()
        live.refresh_from_db()
        self.assertIn(live.status, (OutboundEmail.Status.SENT, OutboundEmail.Status.TEST))
        self.assertEqual(OutboundEmail.objects.filter(kind="invitation_live", order=order).count(), 1)


class StuckOrdersTests(VaylideTestCase):
    def test_paid_but_not_published_shows_up_and_can_be_restarted(self):
        set_fault("publish", 1)
        inv = self.published()
        order = inv.orders.get()
        self.assertNotEqual(order.fulfilment_status, Order.Fulfilment.DONE)
        Order.objects.filter(pk=order.pk).update(paid_at=timezone.now() - timedelta(minutes=30))
        self.assertIn(order.pk, [o.pk for o, _ in stuck_orders()])
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(restart(Order.objects.get(pk=order.pk)), "Verwerking opnieuw gestart.")
        order.refresh_from_db()
        inv.refresh_from_db()
        self.assertEqual(order.fulfilment_status, Order.Fulfilment.DONE)
        self.assertEqual(inv.status, Invitation.Status.LIVE)
        self.assertEqual(stuck_orders(), [])
        self.assertEqual(OutboundEmail.objects.filter(kind="invitation_live", order=order).count(), 1)

    def test_published_but_not_delivered_shows_up(self):
        inv = self.published()
        order = inv.orders.get()
        Order.objects.filter(pk=order.pk).update(paid_at=timezone.now() - timedelta(minutes=30))
        OutboundEmail.objects.filter(kind="invitation_live", order=order).update(status=OutboundEmail.Status.FAILED)
        reasons = dict((o.pk, r) for o, r in stuck_orders())
        self.assertIn("link en QR-code", reasons[order.pk])

    def test_beheer_shows_the_overview_and_restarts(self):
        set_fault("publish", 1)
        inv = self.published()
        order = inv.orders.get()
        Order.objects.filter(pk=order.pk).update(paid_at=timezone.now() - timedelta(minutes=30))
        staff = Client()
        staff.force_login(self.make_staff())
        page = staff.get("/beheer/verwerking/")
        self.assertContains(page, "Vastgelopen bestellingen")
        self.assertContains(page, order.number)
        self.assertContains(staff.get("/beheer/"), "vastgelopen bestellingen")
        with self.captureOnCommitCallbacks(execute=True):
            response = staff.post("/beheer/verwerking/", {"actie": "bestelling-opnieuw", "bestelling": str(order.uid)}, follow=True)
        self.assertContains(response, "Verwerking opnieuw gestart.")
        self.assertContains(staff.get("/beheer/verwerking/"), "Geen vastgelopen bestellingen.")
        # Een klant kan dit niet.
        customer = Client()
        customer.force_login(self.make_customer("ander@example.com"))
        self.assertIn(customer.post("/beheer/verwerking/", {"actie": "bestelling-opnieuw", "bestelling": str(order.uid)}).status_code, (302, 403, 404))


class ErrorPageTests(VaylideTestCase):
    def test_own_404_page(self):
        response = Client().get("/bestaat-echt-niet/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Pagina niet gevonden", status_code=404)
        self.assertContains(response, "Vaylide", status_code=404)


class LayoutRegressionTests(VaylideTestCase):
    def test_design_detail_value_column_cannot_widen_the_page(self):
        from django.conf import settings

        css = (settings.BASE_DIR / "static/css/vierlief.css").read_text(encoding="utf-8")
        self.assertIn(".meta-list > div { grid-template-columns: 8.5rem minmax(0, 1fr); }", css)
        self.assertIn(".detail-grid > * { min-width: 0; }", css)

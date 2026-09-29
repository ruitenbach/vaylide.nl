"""De onthulling na een geslaagde betaling: alleen bij een gepubliceerde uitnodiging, met delen en QR-code."""
from django.conf import settings
from django.test import Client

from orders.models import Order

from .helpers import VaylideTestCase


class RevealTests(VaylideTestCase):
    def test_paid_order_gets_the_show(self):
        customer = self.make_customer()
        inv = self.published(owner=customer)
        client = Client()
        client.force_login(customer)
        order = Order.objects.get(invitation=inv)
        page = client.get(f"/bestelling/{order.uid}/")
        self.assertContains(page, "Gefeliciteerd!")
        self.assertContains(page, "js/onthulling.js")
        self.assertContains(page, "css/onthulling.css")
        self.assertContains(page, "https://wa.me/?text=")
        self.assertContains(page, f"/account/uitnodiging/{inv.uid}/qr.svg")
        self.assertContains(page, inv.public_url)

    def test_unpaid_order_has_no_show(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        from orders.services import start_checkout

        with self.captureOnCommitCallbacks(execute=True):
            payment = start_checkout(inv, user=customer, package_code="essentieel", optional_codes=[], terms_accepted=True)
        client = Client()
        client.force_login(customer)
        page = client.get(f"/bestelling/{payment.order.uid}/")
        self.assertNotContains(page, "Gefeliciteerd!")
        self.assertNotContains(page, "onthulling.js")

    def test_show_respects_reduced_motion(self):
        js = (settings.BASE_DIR / "static/js/onthulling.js").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: reduce", js)
        css = (settings.BASE_DIR / "static/css/onthulling.css").read_text(encoding="utf-8")
        # alle animaties van de show hangen aan .is-spelen (alleen gezet door het script als beweging mag)
        for line in css.splitlines():
            if "animation:" in line:
                self.assertIn(".is-spelen", line, line)

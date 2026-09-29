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
        # daaronder: de tijdlijn en de bon
        self.assertContains(page, "Zo is je bestelling verwerkt")
        self.assertContains(page, 'class="bestel-bon"')
        self.assertContains(page, order.total_display)
        self.assertContains(page, "Alle bestellingen in Mijn VAYLIDE")

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


class BrandMarkAndFlipTests(VaylideTestCase):
    def test_every_invitation_carries_the_v_monogram(self):
        from django.template.loader import render_to_string

        from catalog.models import Template
        from invitations.demo import demo_content
        from invitations.render import RenderOptions, build_view

        for slug in ("liefde-op-papier", "middernacht", "winterlicht", "ballonfeest"):
            t = Template.objects.get(slug=slug)
            occasion = t.current_version.manifest["occasions"][0]
            view = build_view(occasion=occasion, content=demo_content(slug, occasion), overrides={}, template_version=t.current_version,
                              options=RenderOptions(mode="demo"))
            html = render_to_string(t.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
            self.assertIn("img/merk/vaylide-v.webp", html, slug)
        self.assertTrue((settings.BASE_DIR / "static/img/merk/vaylide-v.webp").is_file())

    def test_celebration_uses_the_soft_envelope(self):
        customer = self.make_customer()
        inv = self.published(owner=customer)
        client = Client()
        client.force_login(customer)
        page = client.get(f"/bestelling/{Order.objects.get(invitation=inv).uid}/").content.decode()
        self.assertIn('class="zenv is-open" data-envelop', page)  # eindstand open (zonder JavaScript en bij minder beweging)
        self.assertIn("img/merk/vaylide-logo.webp", page)  # het hele logo op de envelop
        self.assertNotIn("zenv__knop", page)

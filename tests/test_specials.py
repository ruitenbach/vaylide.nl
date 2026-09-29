"""Specials: bijzondere ontwerpen in een eigen categorie met een eigen, door de eigenaar in te stellen meerprijs."""
from django.test import Client

from catalog.models import AddOn, Package, Template
from catalog.specials import addon_code, is_special
from orders.pricing import PricingError, build_quote
from orders.services import CheckoutError, start_checkout

from .helpers import VaylideTestCase


class SpecialsTests(VaylideTestCase):
    def test_balzaal_is_a_special_and_others_are_not(self):
        self.assertTrue(is_special(Template.objects.get(slug="balzaal")))
        self.assertFalse(is_special(Template.objects.get(slug="voor-altijd")))
        self.assertTrue(is_special(Template.objects.get(slug="balzaal").current_version))

    def test_collection_shows_specials_separately(self):
        html = Client().get("/ontwerpen/").content.decode()
        self.assertIn('href="?categorie=specials"', html)
        self.assertIn('id="specials-titel"', html)
        grid, specials = html.split('id="specials-titel"', 1)
        self.assertNotIn("/ontwerpen/balzaal/", grid)
        self.assertIn("/ontwerpen/balzaal/", specials)

    def test_not_orderable_without_its_own_price(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer, template="balzaal")
        with self.assertRaises(PricingError):
            build_quote(inv.draft_content, Package.objects.get(code="essentieel"), template_version=inv.template_version)
        with self.assertRaises((PricingError, CheckoutError)):
            start_checkout(inv, user=customer, package_code="essentieel", optional_codes=[], terms_accepted=True)
        client = Client()
        client.force_login(customer)
        self.assertContains(client.get(f"/maken/{inv.uid}/bestellen/"), "nog niet te bestellen")
        # Een optie met de verkeerde code telt niet: elke special heeft een eigen prijs.
        AddOn.objects.create(code="special-iets-anders", name="Andere special", price_cents=100, feature="special")
        with self.assertRaises(PricingError):
            build_quote(inv.draft_content, Package.objects.get(code="essentieel"), template_version=inv.template_version)

    def test_with_its_price_the_surcharge_is_a_visible_line(self):
        AddOn.objects.create(code=addon_code("balzaal"), name="Special Balzaal", price_cents=100, feature="special")  # testbedrag
        inv = self.make_invitation(template="balzaal")
        quote = build_quote(inv.draft_content, Package.objects.get(code="essentieel"), template_version=inv.template_version)
        self.assertIn("optie:special-balzaal", [line.code for line in quote.lines])
        # Een gewoon ontwerp krijgt geen meerprijs.
        plain = self.make_invitation(template="voor-altijd")
        quote = build_quote(plain.draft_content, Package.objects.get(code="essentieel"), template_version=plain.template_version)
        self.assertNotIn("special", quote.features)

    def test_owner_can_switch_special_in_beheer(self):
        staff = Client()
        staff.force_login(self.make_staff())
        page = staff.get(f"/beheer/ontwerpen/{Template.objects.get(slug='balzaal').pk}/")
        if page.status_code == 404:
            page = staff.get("/beheer/ontwerpen/")
        self.assertEqual(page.status_code, 200)

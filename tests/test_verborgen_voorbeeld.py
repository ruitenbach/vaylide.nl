"""Verborgen ontwerpen (niet zichtbaar in de collectie, zoals Rozenboog en Kerstmagie) zijn alleen voor ingelogde beheerders
(`is_staff`) als voorbeeld te bekijken. Voor iedereen anders blijft het een 404. Het ontwerp blijft buiten de collectie, de
ontwerppagina en de bestelroute, en het voorbeeld voor beheerders wordt nergens bewaard (Cache-Control: private, no-store)."""
from django.test import Client

from catalog.models import Template
from invitations.models import Invitation

from .helpers import VaylideTestCase

VERBORGEN = ("rozenboog", "kerstmagie")


class VerborgenVoorbeeldTests(VaylideTestCase):
    def setUp(self):
        for slug in VERBORGEN:
            self.assertFalse(Template.objects.get(slug=slug).is_active, f"{slug} hoort verborgen te zijn")
        self.staff = self.make_staff()
        self.customer = self.make_customer()

    def client_for(self, user=None):
        client = Client()
        if user is not None:
            client.force_login(user)
        return client

    def test_anonymous_visitors_get_a_404(self):
        for slug in VERBORGEN:
            self.assertEqual(self.client_for().get(f"/voorbeeld/{slug}/").status_code, 404, slug)
            self.assertEqual(self.client_for().get(f"/voorbeeld/{slug}/agenda.ics").status_code, 404, slug)

    def test_customers_get_a_404(self):
        for slug in VERBORGEN:
            client = self.client_for(self.customer)
            self.assertEqual(client.get(f"/voorbeeld/{slug}/").status_code, 404, slug)
            self.assertEqual(client.get(f"/voorbeeld/{slug}/agenda.ics").status_code, 404, slug)

    def test_a_logged_in_user_without_staff_rights_gets_a_404(self):
        self.assertFalse(self.customer.is_staff)
        self.assertEqual(self.client_for(self.customer).get("/voorbeeld/rozenboog/?gelegenheid=bruiloft").status_code, 404)

    def test_staff_can_open_the_preview_and_the_calendar_file(self):
        for slug, occasion in (("rozenboog", "bruiloft"), ("kerstmagie", "kerst")):
            client = self.client_for(self.staff)
            page = client.get(f"/voorbeeld/{slug}/", {"gelegenheid": occasion})
            self.assertEqual(page.status_code, 200, slug)
            ics = client.get(f"/voorbeeld/{slug}/agenda.ics", {"gelegenheid": occasion})
            self.assertEqual(ics.status_code, 200, slug)

    def test_the_staff_preview_is_never_cached(self):
        for slug, occasion in (("rozenboog", "bruiloft"), ("kerstmagie", "kerst")):
            client = self.client_for(self.staff)
            for url in (f"/voorbeeld/{slug}/", f"/voorbeeld/{slug}/agenda.ics"):
                response = client.get(url, {"gelegenheid": occasion})
                self.assertEqual(response["Cache-Control"], "private, no-store", url)

    def test_hidden_designs_stay_out_of_the_collection_and_the_order_route_for_staff_too(self):
        client = self.client_for(self.staff)
        collection = client.get("/ontwerpen/")
        for slug in VERBORGEN:
            self.assertNotContains(collection, f"/ontwerpen/{slug}/")
            self.assertEqual(client.get(f"/ontwerpen/{slug}/").status_code, 404, slug)
        self.assertNotContains(client.get("/maken/?gelegenheid=bruiloft"), "Rozenboog")
        before = Invitation.objects.count()
        client.post("/maken/", {"occasion": "bruiloft", "template": "rozenboog"})
        self.assertEqual(Invitation.objects.count(), before)
        for slug in VERBORGEN:
            self.assertFalse(Template.objects.get(slug=slug).is_active, f"{slug} is niet geactiveerd")

    def test_active_designs_behave_as_before(self):
        self.assertTrue(Template.objects.get(slug="rozentuin").is_active)
        for user in (None, self.customer, self.staff):
            client = self.client_for(user)
            page = client.get("/voorbeeld/rozentuin/")
            self.assertEqual(page.status_code, 200)
            self.assertNotIn("no-store", page.get("Cache-Control", ""))
            self.assertEqual(client.get("/voorbeeld/rozentuin/agenda.ics").status_code, 200)

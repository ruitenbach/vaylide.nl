"""Nieuwsbrief: een eigen vinkje bij bestellen (standaard uit), aan- en afmelden in Mijn VAYLIDE en de lijst in het beheer."""
from django.test import Client

from accounts.models import User

from .helpers import VaylideTestCase


class NewsletterTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.client = Client()
        self.client.force_login(self.customer)

    def checkout(self, **extra):
        inv = self.make_invitation(owner=self.customer)
        data = {"actie": "betalen", "package": "essentieel", "terms": "on"}
        data.update(extra)
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(f"/maken/{inv.uid}/bestellen/", data)

    def test_checkbox_is_separate_and_unchecked(self):
        inv = self.make_invitation(owner=self.customer)
        html = self.client.get(f"/maken/{inv.uid}/bestellen/").content.decode()
        box = html[html.index('name="nieuwsbrief"') - 60:html.index('name="nieuwsbrief"') + 60]
        self.assertNotIn("checked", box)
        self.assertIn("Afmelden kan altijd", html)

    def test_ticking_the_box_records_consent(self):
        self.checkout(nieuwsbrief="on")
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.newsletter)
        self.assertIsNotNone(self.customer.newsletter_since)
        self.assertIn("nieuwsbrief", self.customer.newsletter_consent)

    def test_terms_alone_is_no_consent(self):
        self.checkout()
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.newsletter)

    def test_unsubscribe_in_account(self):
        self.checkout(nieuwsbrief="on")
        self.client.post("/account/gegevens/", {"actie": "nieuwsbrief", "nieuwsbrief": "nee"})
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.newsletter)
        self.client.post("/account/gegevens/", {"actie": "nieuwsbrief", "nieuwsbrief": "ja"})
        self.customer.refresh_from_db()
        self.assertTrue(self.customer.newsletter)

    def test_owner_sees_the_list(self):
        self.checkout(nieuwsbrief="on")
        User.objects.create_user(email="geen@example.com")
        staff = Client()
        staff.force_login(self.make_staff())
        page = staff.get("/beheer/klanten/?nieuwsbrief=1").content.decode()
        self.assertIn(self.customer.email, page)
        self.assertNotIn("geen@example.com", page)
        csv = staff.get("/beheer/klanten/nieuwsbrief.csv").content.decode("utf-8-sig")
        self.assertIn(self.customer.email, csv)
        self.assertNotIn("geen@example.com", csv)
        self.assertEqual(Client().get("/beheer/klanten/nieuwsbrief.csv").status_code, 302)

    def test_deleting_the_account_removes_consent(self):
        from core.privacy import anonymize_user

        self.checkout(nieuwsbrief="on")
        anonymize_user(self.customer)
        self.customer.refresh_from_db()
        self.assertFalse(self.customer.newsletter)

"""Controle 1: aanmelden door gasten (deadline, limieten, dubbel tikken, wijzigen)."""
from datetime import timedelta

from django.core.cache import cache
from django.test import Client
from django.utils import timezone

from invitations.models import GuestResponse
from invitations.services import publish_draft, save_draft
from invitations.vragen import vraag

from .helpers import VaylideTestCase


class RsvpTests(VaylideTestCase):
    def setUp(self):
        cache.clear()
        self.owner = self.make_customer()
        self.inv = self.published(owner=self.owner)

    def change_published(self, **changes):
        content = dict(self.inv.draft_content)
        for key, value in changes.items():
            if key == "rsvp":
                content["rsvp"] = dict(content["rsvp"], **value)
            else:
                content[key] = value
        self.inv = save_draft(self.inv, expected_rev=None, content=content, user=self.owner)
        publish_draft(self.inv, user=self.owner, source="customer", expected_rev=None)
        self.inv.refresh_from_db()

    def test_double_tap_creates_single_response(self):
        guest = Client()
        first = self.rsvp(guest, self.inv, token="zelfde-formulier-token-1", name="Kees")
        second = self.rsvp(guest, self.inv, token="zelfde-formulier-token-1", name="Kees")
        self.assertTrue(first.json()["ok"])
        self.assertTrue(second.json()["ok"])
        self.assertEqual(GuestResponse.objects.filter(invitation=self.inv).count(), 1)

    def test_party_size_limit_and_validation(self):
        guest = Client()
        response = self.rsvp(guest, self.inv, name="Te veel", party_size="5")
        self.assertEqual(response.status_code, 400)
        self.assertIn("party_size", response.json()["errors"])
        response = self.rsvp(guest, self.inv, name="", attending="misschien")
        errors = response.json()["errors"]
        self.assertIn("name", errors)
        self.assertIn("attending", errors)
        self.assertFalse(GuestResponse.objects.exists())

    def test_not_attending_counts_zero_persons(self):
        self.rsvp(Client(), self.inv, name="Afwezig", attending="nee", party_size="2")
        response = GuestResponse.objects.get()
        self.assertEqual(response.persons, 0)
        self.assertFalse(response.attending)

    def test_deadline_closes_form_server_side(self):
        self.change_published(rsvp={"deadline": (timezone.localdate() - timedelta(days=1)).isoformat()})
        page = Client().get(self.inv.public_path)
        self.assertContains(page, "Aanmelden kon tot en met")
        response = self.rsvp(Client(), self.inv, token="na-de-deadline-token-1", name="Te laat")
        self.assertEqual(response.status_code, 409)
        self.assertFalse(GuestResponse.objects.exists())

    def test_capacity_limit(self):
        self.change_published(rsvp={"capacity": 3})
        self.assertTrue(self.rsvp(Client(), self.inv, name="A", party_size="2").json()["ok"])
        response = self.rsvp(Client(), self.inv, name="B", party_size="2")
        self.assertEqual(response.status_code, 400)
        self.assertIn("nog plek voor 1 persoon", response.json()["errors"]["party_size"])
        self.assertTrue(self.rsvp(Client(), self.inv, name="C", party_size="1").json()["ok"])
        page = Client().get(self.inv.public_path)
        self.assertContains(page, "maximale aantal aanmeldingen is bereikt")

    def test_past_event_closes_rsvp(self):
        content = dict(self.inv.draft_content, date=(timezone.localdate() - timedelta(days=3)).isoformat())
        content["rsvp"] = dict(content["rsvp"], deadline=(timezone.localdate() - timedelta(days=10)).isoformat())
        self.inv = save_draft(self.inv, expected_rev=None, content=content, user=self.owner)
        publish_draft(self.inv, user=self.owner, source="customer", expected_rev=None)
        page = Client().get(self.inv.public_path)
        self.assertContains(page, "Deze dag vond plaats op")
        self.assertContains(page, "al plaatsgevonden")
        self.assertNotContains(page, 'data-countdown="')

    def test_guest_can_change_and_delete_own_answer(self):
        guest = Client()
        edit_url = self.rsvp(guest, self.inv, name="Wim", attending="ja", party_size="1").json()["edit_url"]
        page = guest.get(self.inv.public_path)
        self.assertContains(page, "Je hebt al geantwoord")
        response = guest.post(edit_url, {"name": "Wim", "attending": "nee"})
        self.assertEqual(response.status_code, 302)
        answer = GuestResponse.objects.get()
        self.assertFalse(answer.attending)
        self.assertEqual(answer.edit_count, 1)
        guest.post(edit_url, {"actie": "verwijderen"})
        self.assertFalse(GuestResponse.objects.exists())

    def test_spam_protection(self):
        guest = Client()
        response = self.rsvp(guest, self.inv, website="http://spam.example")
        self.assertEqual(response.status_code, 400)
        page = guest.get(self.inv.public_path)
        import re

        token = re.search(r'name="client_token" value="([^"]+)"', page.content.decode()).group(1)
        from core.utils import signed_timestamp

        too_fast = guest.post(f"/u/{self.inv.slug}/aanmelden/", {"client_token": token, "form_ts": signed_timestamp(), "name": "Bot", "attending": "ja"},
                              HTTP_ACCEPT="application/json")
        self.assertEqual(too_fast.status_code, 400)
        forged = guest.post(f"/u/{self.inv.slug}/aanmelden/", {"client_token": token, "form_ts": "vervalst", "name": "Bot", "attending": "ja"},
                            HTTP_ACCEPT="application/json")
        self.assertEqual(forged.status_code, 400)
        self.assertFalse(GuestResponse.objects.exists())

    def test_rate_limit_per_device(self):
        guest = Client()
        codes = [self.rsvp(guest, self.inv, token=f"token-nummer-{i:04d}-xx", name=f"G{i}").status_code for i in range(17)]
        self.assertIn(429, codes)

    def test_extra_questions_only_when_entitled(self):
        content = dict(self.inv.draft_content)
        content["rsvp"] = dict(content["rsvp"], questions=[vraag("vervoer", formal=False, required=True)])
        self.inv = save_draft(self.inv, expected_rev=None, content=content, user=self.owner)
        publish_draft(self.inv, user=self.owner, source="customer", expected_rev=None)
        # Essentieel bevat geen extra vragen: niet tonen en niet verplichten.
        page = Client().get(self.inv.public_path)
        self.assertNotContains(page, "Hoe kom je?")
        self.assertTrue(self.rsvp(Client(), self.inv, name="Zonder vraag").json()["ok"])

    def test_extra_questions_with_compleet(self):
        owner = self.make_customer("compleet@example.com")
        content_q = [vraag("liedje", formal=False, required=True), vraag("vervoer", formal=False)]
        inv = self.make_invitation(owner=owner)
        content = dict(inv.draft_content)
        content["rsvp"] = dict(content["rsvp"], questions=content_q)
        inv = save_draft(inv, expected_rev=None, content=content, user=owner)
        self.pay(inv, owner, package="compleet")
        inv.refresh_from_db()
        page = Client().get(inv.public_path)
        self.assertContains(page, "Welk nummer mag niet ontbreken?")
        missing = self.rsvp(Client(), inv, name="Z")
        self.assertIn("q_liedje", missing.json()["errors"])
        bad_choice = self.rsvp(Client(), inv, name="Z", q_liedje="Dancing Queen", q_vervoer="Per helikopter")
        self.assertIn("q_vervoer", bad_choice.json()["errors"])
        ok = self.rsvp(Client(), inv, name="Z", q_liedje="Dancing Queen", q_vervoer="Met de auto")
        self.assertTrue(ok.json()["ok"])
        answer = GuestResponse.objects.get(invitation=inv)
        self.assertEqual([a["value"] for a in answer.answers], ["Dancing Queen", "Met de auto"])

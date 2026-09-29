"""Pakket kiezen bij de start, labels in de editor, 'Jouw pakket' met upgrade bij Bestellen, de controle als
checklist, doorgaan als gast en een zichtbaar inloggen."""
from django.test import Client

from invitations.models import Invitation

from .helpers import VaylideTestCase


class PackageFlowTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.client = Client()
        self.client.force_login(self.customer)

    def invitation(self, package_code):
        inv = self.make_invitation(owner=self.customer)
        inv.package_code = package_code
        inv.save(update_fields=["package_code"])
        return inv

    def test_package_is_chosen_at_the_start(self):
        page = self.client.get("/maken/?gelegenheid=bruiloft")
        self.assertContains(page, 'name="pakket" value="essentieel"')
        self.assertContains(page, 'name="pakket" value="compleet"')
        self.client.post("/maken/", {"occasion": "bruiloft", "template": "liefde-op-papier", "pakket": "compleet"})
        self.assertEqual(Invitation.objects.latest("created_at").package_code, "compleet")

    def test_unknown_package_at_the_start_is_ignored(self):
        self.client.post("/maken/", {"occasion": "bruiloft", "template": "liefde-op-papier", "pakket": "gratis"})
        self.assertEqual(Invitation.objects.latest("created_at").package_code, "")

    def test_editor_labels_follow_the_package(self):
        compleet = self.invitation("compleet")
        self.assertContains(self.client.get(f"/maken/{compleet.uid}/fotos/"), "In Compleet")
        essentieel = self.invitation("essentieel")
        page = self.client.get(f"/maken/{essentieel.uid}/fotos/")
        self.assertContains(page, "Extra optie · € 9")  # muziek, prijs uit Beheer
        self.assertNotContains(page, "Compleet of extra optie")

    def test_essentieel_shows_upgrade_and_loose_extras(self):
        inv = self.invitation("essentieel")
        page = self.client.get(f"/maken/{inv.uid}/bestellen/")
        self.assertContains(page, "Jouw keuze")
        self.assertContains(page, "Upgraden naar Compleet")
        self.assertContains(page, "+ € 30")
        self.assertContains(page, "Los bij te kopen bij Essentieel")
        self.assertContains(page, "Muziek")

    def test_upgrade_is_remembered_and_compleet_only_offers_real_extras(self):
        inv = self.invitation("essentieel")
        page = self.client.post(f"/maken/{inv.uid}/bestellen/", {"actie": "herberekenen", "package": "essentieel", "wissel": "compleet"})
        inv.refresh_from_db()
        self.assertEqual(inv.package_code, "compleet")
        self.assertNotContains(page, "Upgraden naar")
        self.assertNotContains(page, "Los bij te kopen")
        self.assertContains(page, "Liever Essentieel")
        self.assertContains(page, "Langer online")  # een echte extra blijft kiesbaar
        self.assertNotContains(page, 'name="extras" value="muziek"')  # muziek zit al in Compleet

    def test_checklist_on_checkout(self):
        inv = self.invitation("essentieel")
        content = dict(inv.draft_content)
        content["rsvp"] = dict(content["rsvp"], enabled=True, deadline="")
        from invitations.services import save_draft

        save_draft(inv, expected_rev=None, content=content, user=self.customer)
        page = self.client.get(f"/maken/{inv.uid}/bestellen/")
        self.assertContains(page, "voordat je kunt bestellen")
        self.assertContains(page, "controle__item--nodig")
        complete = self.invitation("essentieel")
        self.assertContains(self.client.get(f"/maken/{complete.uid}/bestellen/"), "Alles is compleet")


class GuestAndLoginTests(VaylideTestCase):
    def test_start_as_guest_or_log_in(self):
        page = Client().get("/maken/?gelegenheid=bruiloft")
        self.assertContains(page, "Doorgaan als gast")
        self.assertContains(page, "Log eerst in")

    def test_header_shows_login_text(self):
        self.assertContains(Client().get("/"), 'class="site-header__account" href="/inloggen/" aria-label="Inloggen"')
        client = Client()
        client.force_login(self.make_customer())
        self.assertContains(client.get("/"), "<span>Mijn VAYLIDE</span>")

    def test_portal_offers_checkout_for_drafts(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        client = Client()
        client.force_login(customer)
        self.assertContains(client.get("/account/"), f'href="/maken/{inv.uid}/bestellen/">Afrekenen</a>')

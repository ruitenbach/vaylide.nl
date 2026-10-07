"""Controle 1: wijzigen na publicatie, versies herstellen, conflicten en ontwerpversies."""
from django.test import Client

from catalog.models import Template, TemplateVersion
from invitations.models import Source
from invitations.services import DraftConflict, restore_version, save_draft

from .helpers import VaylideTestCase


class EditAfterPublicationTests(VaylideTestCase):
    def setUp(self):
        self.owner = self.make_customer()
        self.inv = self.published(owner=self.owner)
        self.c = Client()
        self.c.force_login(self.owner)

    def test_changes_go_live_on_same_link_only_after_publishing(self):
        slug = self.inv.slug
        self.c.post(f"/maken/{self.inv.uid}/gegevens/", {
            "rev": self.inv.draft_rev, "actie": "opslaan", "name_partner_1": "Anna", "name_partner_2": "Bram",
            "date": self.inv.draft_content["date"], "start_time": "16:00", "timezone": "Europe/Amsterdam",
            "venue_name": "Nieuwe Locatie", "address": "Laan 2"})
        self.inv.refresh_from_db()
        self.assertTrue(self.inv.has_unpublished_changes)
        self.assertNotContains(Client().get(self.inv.public_path), "Nieuwe Locatie")
        response = self.c.post(f"/maken/{self.inv.uid}/publiceren/", {"rev": self.inv.draft_rev})
        self.assertEqual(response.status_code, 302)
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.slug, slug)
        self.assertContains(Client().get(f"/u/{slug}/"), "Nieuwe Locatie")
        self.assertEqual(self.inv.versions.count(), 2)

    def test_publish_is_not_blocked_when_data_removed(self):
        content = dict(self.inv.draft_content, venue_name="")      # niets is verplicht: een leeggemaakt veld verdwijnt gewoon van de kaart
        self.inv = save_draft(self.inv, expected_rev=None, content=content, user=self.owner)
        response = self.c.post(f"/maken/{self.inv.uid}/publiceren/", {"rev": self.inv.draft_rev}, follow=True)
        self.assertNotContains(response, "Nog niet compleet")
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.versions.count(), 2)

class ConflictTests(VaylideTestCase):
    def setUp(self):
        self.owner = self.make_customer()
        self.inv = self.published(owner=self.owner)
        self.customer = Client()
        self.customer.force_login(self.owner)
        self.staff = Client()
        self.staff.force_login(self.make_staff())

    def test_admin_edit_is_not_silently_overwritten_by_stale_customer_form(self):
        stale_rev = self.inv.draft_rev
        # Beheerder past handmatig de welkomsttekst aan.
        self.staff.post(f"/maken/{self.inv.uid}/gegevens/", {
            "rev": stale_rev, "actie": "opslaan", "name_partner_1": "Anna", "name_partner_2": "Bram",
            "date": self.inv.draft_content["date"], "start_time": "14:00", "timezone": "Europe/Amsterdam",
            "venue_name": "Kasteel Test", "address": "Teststraat 1", "welcome_text": "Handmatig door het team verbeterd."})
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_updated_source, Source.ADMIN)
        # Klant verstuurt een formulier dat nog op de oude stand was gebaseerd.
        response = self.customer.post(f"/maken/{self.inv.uid}/gegevens/", {
            "rev": stale_rev, "actie": "volgende", "name_partner_1": "Anna", "name_partner_2": "Bram",
            "date": self.inv.draft_content["date"], "start_time": "14:00", "timezone": "Europe/Amsterdam",
            "venue_name": "Kasteel Test", "address": "Teststraat 1", "welcome_text": "Oude tekst van de klant."})
        self.assertContains(response, "deze uitnodiging is intussen gewijzigd")
        self.assertContains(response, "Het VAYLIDE-team")
        self.assertContains(response, "Welkomsttekst")
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["welcome_text"], "Handmatig door het team verbeterd.")
        # Bewust opnieuw opslaan (met de nieuwe revisie uit het formulier) werkt wel.
        new_rev = self.inv.draft_rev
        self.customer.post(f"/maken/{self.inv.uid}/gegevens/", {
            "rev": new_rev, "actie": "opslaan", "name_partner_1": "Anna", "name_partner_2": "Bram",
            "date": self.inv.draft_content["date"], "start_time": "14:00", "timezone": "Europe/Amsterdam",
            "venue_name": "Kasteel Test", "address": "Teststraat 1", "welcome_text": "Bewuste keuze van de klant."})
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["welcome_text"], "Bewuste keuze van de klant.")

    def test_locked_fields_cannot_be_changed_by_customer(self):
        self.inv = save_draft(self.inv, expected_rev=None, overrides={"locked_fields": ["welcome_text"]}, user=None, source=Source.ADMIN)
        original = self.inv.draft_content["welcome_text"]
        self.customer.post(f"/maken/{self.inv.uid}/gegevens/", {
            "rev": self.inv.draft_rev, "actie": "opslaan", "name_partner_1": "Anna", "name_partner_2": "Bram",
            "date": self.inv.draft_content["date"], "start_time": "14:00", "timezone": "Europe/Amsterdam",
            "venue_name": "Kasteel Test", "welcome_text": "Geprobeerd te overschrijven"})
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["welcome_text"], original)

    def test_stale_publish_is_refused(self):
        stale = self.inv.draft_rev
        save_draft(self.inv, expected_rev=None, content=dict(self.inv.draft_content, closing_text="Nieuw"), user=None, source=Source.ADMIN)
        response = self.customer.post(f"/maken/{self.inv.uid}/publiceren/", {"rev": stale}, follow=True)
        self.assertContains(response, "intussen nieuwe wijzigingen")

    def test_service_level_conflict(self):
        with self.assertRaises(DraftConflict):
            save_draft(self.inv, expected_rev=self.inv.draft_rev - 1, content=self.inv.draft_content, user=self.owner)


class RestoreTests(VaylideTestCase):
    def test_restore_keeps_current_draft_as_version_and_can_publish(self):
        owner = self.make_customer()
        inv = self.published(owner=owner)
        v1 = inv.published_version
        inv = save_draft(inv, expected_rev=None, content=dict(inv.draft_content, venue_name="Fout adres"), user=owner)
        staff = Client()
        staff.force_login(self.make_staff())
        staff.post(f"/beheer/uitnodigingen/{inv.uid}/", {"actie": "publiceren", "rev": inv.draft_rev})
        inv.refresh_from_db()
        self.assertContains(Client().get(inv.public_path), "Fout adres")
        staff.post(f"/beheer/uitnodigingen/{inv.uid}/", {"actie": "herstellen", "versie": v1.pk, "rev": inv.draft_rev, "direct_publiceren": "1"})
        inv.refresh_from_db()
        self.assertContains(Client().get(inv.public_path), "Kasteel Test")
        self.assertEqual(inv.published_version.source, Source.RESTORE)
        self.assertGreaterEqual(inv.versions.count(), 3)

    def test_restore_with_stale_revision_conflicts(self):
        owner = self.make_customer()
        inv = self.published(owner=owner)
        with self.assertRaises(DraftConflict):
            restore_version(inv, inv.published_version, user=owner, source=Source.CUSTOMER, expected_rev=inv.draft_rev + 5)


class TemplateVersionPinningTests(VaylideTestCase):
    def test_new_template_version_does_not_change_existing_invitation(self):
        owner = self.make_customer()
        inv = self.published(owner=owner)
        template = Template.objects.get(slug="liefde-op-papier")
        v1 = template.current_version
        manifest = dict(v1.manifest, version=2)
        v2 = TemplateVersion.objects.create(template=template, number=2, renderer=v1.renderer, manifest=manifest)
        template.current_version = v2
        template.save()
        inv.refresh_from_db()
        self.assertEqual(inv.template_version_id, v1.pk)
        self.assertEqual(inv.published_version.template_version_id, v1.pk)
        # Nieuwe uitnodigingen krijgen wel v2.
        fresh = self.make_invitation(owner=owner)
        self.assertEqual(fresh.template_version_id, v2.pk)
        # Overzetten gebeurt bewust in het concept en gaat pas live na publiceren.
        staff = Client()
        staff.force_login(self.make_staff())
        staff.post(f"/beheer/uitnodigingen/{inv.uid}/", {"actie": "ontwerpversie", "versie": v2.pk, "rev": inv.draft_rev})
        inv.refresh_from_db()
        self.assertEqual(inv.template_version_id, v2.pk)
        self.assertEqual(inv.published_version.template_version_id, v1.pk)

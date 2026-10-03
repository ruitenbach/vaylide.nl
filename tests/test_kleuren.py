"""Kleurvarianten kiezen: op de ontwerppagina, bij het starten van een ontwerp en in de stap Stijl."""
from django.test import Client

from catalog.models import Template
from invitations.models import Invitation

from .helpers import VaylideTestCase, toon_verborgen_ontwerpen

KERST = ["aan-tafel", "middernacht", "gloria", "winterlicht", "kerstman", "sneeuwpop"]


class DesignPageColourTests(VaylideTestCase):
    def test_every_colour_is_a_link_and_changes_the_example(self):
        for template in Template.objects.filter(is_active=True, current_version__isnull=False):
            keys = [p["key"] for p in template.current_version.palettes]
            for key in keys:
                response = Client().get(f"/ontwerpen/{template.slug}/", {"kleur": key})
                html = response.content.decode()
                self.assertEqual(response.status_code, 200, template.slug)
                self.assertEqual(html.count("data-palette-link"), len(keys), template.slug)
                self.assertRegex(html, rf'data-kleur="{key}"[^>]*aria-current="true"', f"{template.slug}/{key}")
                self.assertRegex(html, rf'<iframe src="[^"]*kleur={key}[^"]*embed=1"', f"{template.slug}/{key}")  # voorbeeld in de telefoon
                self.assertRegex(html, rf'href="/maken/[^"]*kleur={key}[^"]*" data-kleur-link', f"{template.slug}/{key}")  # startknop

    def test_unknown_colour_falls_back_to_the_default(self):
        response = Client().get("/ontwerpen/gloria/", {"kleur": "<script>"})
        self.assertRegex(response.content.decode(), r'data-kleur="hemelsblauw"[^>]*aria-current="true"')
        self.assertContains(response, "<span data-kleur-naam>Hemelsblauw</span>")
        self.assertNotContains(response, "<script>&")

    def test_every_colour_renders_in_the_example(self):
        toon_verborgen_ontwerpen()
        for slug in KERST:
            for palette in Template.objects.get(slug=slug).current_version.palettes:
                html = Client().get(f"/voorbeeld/{slug}/", {"kleur": palette["key"]}).content.decode()
                self.assertIn(f'data-palette="{palette["key"]}"', html, slug)


class StartWithColourTests(VaylideTestCase):
    def test_chosen_colour_is_kept_when_starting(self):
        response = Client().get("/maken/", {"ontwerp": "gloria", "gelegenheid": "kerst", "kleur": "nachtgoud"})
        self.assertContains(response, 'name="kleur" value="nachtgoud"')
        c = Client()
        response = c.post("/maken/", {"occasion": "kerst", "template": "gloria", "kleur": "nachtgoud"})
        inv = Invitation.objects.get(uid=response["Location"].split("/")[2])
        self.assertEqual(inv.draft_content["style"]["palette"], "nachtgoud")

    def test_colour_of_another_design_falls_back(self):
        c = Client()
        response = c.post("/maken/", {"occasion": "kerst", "template": "middernacht", "kleur": "nachtgoud"})
        inv = Invitation.objects.get(uid=response["Location"].split("/")[2])
        self.assertEqual(inv.draft_content["style"]["palette"], "champagne")

    def test_style_step_changes_colour_of_new_christmas_designs(self):
        owner = self.make_customer()
        for slug in KERST:
            inv = self.make_invitation(owner=owner, template=slug, occasion="kerst")
            c = Client()
            c.force_login(owner)
            for palette in Template.objects.get(slug=slug).current_version.palettes[1:]:
                inv.refresh_from_db()
                c.post(f"/maken/{inv.uid}/stijl/", {"rev": inv.draft_rev, "actie": "opslaan", "palette": palette["key"], "opening": "on"})
                inv.refresh_from_db()
                self.assertEqual(inv.draft_content["style"]["palette"], palette["key"], slug)
                preview = c.get(f"/maken/{inv.uid}/voorbeeld/weergave/")
                self.assertContains(preview, f'data-palette="{palette["key"]}"', msg_prefix=slug)

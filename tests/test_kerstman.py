"""Kerstkaarten Ho ho ho (zwaaiende kerstman) en Sneeuwpret (zwaaiende sneeuwpop), elk in vier kleuren."""
from django.test import Client

from catalog.models import Template

from .helpers import VaylideTestCase, toon_verborgen_ontwerpen


class KerstmanTests(VaylideTestCase):
    def test_design_is_a_christmas_card_in_four_colours(self):
        template = Template.objects.get(slug="kerstman")
        manifest = template.current_version.manifest
        self.assertEqual(manifest["occasions"], ["kerst"])
        self.assertEqual(manifest["atelier"]["ornament"], "kerstman")
        self.assertEqual([p["key"] for p in manifest["palettes"]], ["kerstrood", "sneeuwwit", "dennengroen", "nachtblauw"])

    def test_example_shows_santa_in_every_colour(self):
        toon_verborgen_ontwerpen()
        for kleur in ("kerstrood", "sneeuwwit", "dennengroen", "nachtblauw"):
            response = Client().get(f"/voorbeeld/kerstman/?kleur={kleur}")
            self.assertEqual(response.status_code, 200, kleur)
            self.assertContains(response, "a-orn__svg--kerstman")
            self.assertContains(response, 'content="noindex')

    def test_listed_with_christmas_designs(self):
        # Ho ho ho en Sneeuwpret zijn C (catalog/collectie.py): niet in de collectie, wel technisch aanwezig.
        response = Client().get("/ontwerpen/?gelegenheid=kerst")
        self.assertContains(response, "Winterlicht")
        self.assertNotContains(response, "Ho ho ho")
        self.assertNotContains(response, "Sneeuwpret")
        toon_verborgen_ontwerpen()          # zet de eigenaar ze in Beheer weer aan, dan staan ze er meteen weer
        response = Client().get("/ontwerpen/?gelegenheid=kerst")
        self.assertContains(response, "Ho ho ho")
        self.assertContains(response, "Sneeuwpret")


class SneeuwpopTests(VaylideTestCase):
    KLEUREN = ["ijsblauw", "zilverwit", "mint", "poolnacht"]

    def test_design_is_a_christmas_card_in_four_colours(self):
        manifest = Template.objects.get(slug="sneeuwpop").current_version.manifest
        self.assertEqual(manifest["occasions"], ["kerst"])
        self.assertEqual(manifest["atelier"]["ornament"], "sneeuwpop")
        self.assertEqual([p["key"] for p in manifest["palettes"]], self.KLEUREN)

    def test_snowman_waves_only_with_motion_on(self):
        toon_verborgen_ontwerpen()
        for kleur in self.KLEUREN:
            response = Client().get(f"/voorbeeld/sneeuwpop/?kleur={kleur}")
            self.assertEqual(response.status_code, 200, kleur)
            self.assertContains(response, "a-orn__svg--sneeuwpop")
            # Geen verlopen met id's: de tekening staat meerdere keren op de pagina (ook op de verborgen voorkant).
            self.assertNotContains(response, 'url(#sp-')
        css = (Template.objects.get(slug="sneeuwpop").current_version.manifest and
               open("designs/sneeuwpop/v1/style.css", encoding="utf-8").read())
        self.assertIn(".fx-motion .sp-arm { animation: sp-zwaai", css)
        self.assertIn("animation-play-state: var(--fx-play, running)", css)

"""Gouden licht: de envelop waar het licht doorheen breekt (eigen ontwerp met vier kleurvarianten)."""
import importlib.util
import json
import re
from pathlib import Path

from django.conf import settings
from django.test import Client, TestCase

from catalog.atelier import contrast
from catalog.effects import effects_errors
from catalog.models import Template

ROOT = Path(settings.BASE_DIR)
DESIGN = ROOT / "designs" / "gouden-licht" / "v1"


def manifest():
    return json.loads((DESIGN / "manifest.json").read_text(encoding="utf-8"))


class GoudenLichtDesignTests(TestCase):
    def test_manifest_and_effects_are_valid(self):
        data = manifest()
        self.assertEqual(data["slug"], "gouden-licht")
        self.assertEqual(len(data["palettes"]), 4)
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertTrue(Template.objects.filter(slug="gouden-licht", is_active=True).exists())

    def test_text_colors_are_readable_in_every_palette(self):
        for pal in manifest()["palettes"]:
            v = pal["vars"]
            pairs = [
                ("tekst op papier", v["--gl-ink"], v["--gl-paper"]),
                ("tekst op kaart", v["--gl-ink"], v["--gl-card"]),
                ("zachte tekst op papier", v["--gl-muted"], v["--gl-paper"]),
                ("zachte tekst op kaart", v["--gl-muted"], v["--gl-card"]),
                ("accent op papier", v["--gl-accent"], v["--gl-paper"]),
                ("accent op kaart", v["--gl-accent"], v["--gl-card"]),
                ("accent op zacht vlak", v["--gl-accent"], v["--gl-soft"]),
                ("initialen op zegel", v["--gl-seal-ink"], v["--gl-seal"]),
                ("hint op donker scherm", v["--gl-gold-2"], v["--gl-stage"]),
                ("goud op donker scherm", v["--gl-gold"], v["--gl-stage-2"]),
            ]
            for name, fg, bg in pairs:
                self.assertGreaterEqual(contrast(fg, bg), 4.5, f"{pal['key']}: {name} {fg} op {bg}")

    def test_every_palette_and_occasion_renders_the_envelope(self):
        for occasion in manifest()["occasions"]:
            for pal in manifest()["palettes"]:
                response = Client().get("/voorbeeld/gouden-licht/", {"gelegenheid": occasion, "kleur": pal["key"]})
                self.assertEqual(response.status_code, 200, (occasion, pal["key"]))
                html = response.content.decode()
                # De opening: zegel als knop met een vaste naam, ook zonder JavaScript een gewone link.
                self.assertRegex(html, r'<a href="#uitnodiging" class="gl-seal fx-pulse" data-open data-fx-origin data-mono="[^"]+" aria-label="Open de uitnodiging"></a>')
                self.assertIn("data-cover", html)
                self.assertIn('id="gl-bloemen"', html)
                self.assertEqual(html.count("gl-flap gl-flap--"), 4)
                self.assertIn("Tik op het zegel om te openen", html)
                # De decoratie staat verborgen voor schermlezers; de envelop is geen inhoud.
                self.assertIn('<div class="gl-env" aria-hidden="true">', html)
                # Geen inline scripts naast het vaste startscript (CSP).
                self.assertEqual(len(re.findall(r"<script>", html)), 1, (occasion, pal["key"]))
                self.assertIn(f'data-palette="{pal["key"]}"', html)

    def test_monogram_and_names_come_from_the_invitation(self):
        html = Client().get("/voorbeeld/gouden-licht/", {"gelegenheid": "bruiloft"}).content.decode()
        self.assertIn('data-mono="S&amp;D"', html)
        self.assertIn("Sanne", html)

    def test_design_page_is_listed_on_the_website(self):
        self.assertContains(Client().get("/ontwerpen/gouden-licht/"), "Gouden licht")
        self.assertContains(Client().get("/zoeken/", {"q": "Gouden licht"}), "/ontwerpen/gouden-licht/")


class GoudenLichtStyleTests(TestCase):
    """De vaste afspraken voor beweging (zie CLAUDE.md en docs/HANDLEIDING.md onder 'Effecten')."""

    def css(self):
        return (DESIGN / "style.css").read_text(encoding="utf-8")

    def test_endless_animations_sit_under_fx_motion_and_follow_the_pause_button(self):
        blocks = re.findall(r"([^{}]+)\{([^{}]*animation:[^{}]*infinite[^{}]*)\}", self.css())
        self.assertGreaterEqual(len(blocks), 3)
        for selector, body in blocks:
            self.assertIn(".fx-motion", selector, selector)
            self.assertIn("animation-play-state: var(--fx-play, running)", body, selector)

    def test_opening_has_a_calm_variant(self):
        css = self.css()
        self.assertIn(".is-opening-reduced .gl-cover { animation: none; opacity: 0;", css)
        # Alle bewegende delen van het openen slaan de rustige variant over.
        for part in ("gl-flap--t", "gl-light__core", "gl-light__rays", "gl-flood", "gl-seal"):
            self.assertRegex(css, rf"\.is-opening:not\(\.is-opening-reduced\) \.{part}\b", part)

    def test_template_has_no_leftovers_of_the_design_it_was_copied_from(self):
        for name in ("invitation.html", "style.css"):
            text = (DESIGN / name).read_text(encoding="utf-8")
            self.assertNotRegex(text, r"\blp-|--lp-", name)

    def test_flowers_file_is_what_the_generator_makes(self):
        spec = importlib.util.spec_from_file_location("maak_bloemen", ROOT / "tools" / "gouden-licht" / "maak_bloemen.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual((DESIGN / "bloemen.html").read_text(encoding="utf-8"), module.build())

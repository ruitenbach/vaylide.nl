"""Aan tafel: warme uitnodiging voor het kerstdiner, met een plaatskaartje op tafel, kaarsen, vier kleuren en eigen muziek."""
import re

from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client

from catalog.atelier import contrast
from catalog.effects import effects_errors
from catalog.models import Template
from invitations.demo import DESIGN_IMAGES, demo_content
from invitations.render import RenderOptions, build_view

from .helpers import VaylideTestCase

KLEUREN = ["haardvuur", "dennengroen", "kaarslicht", "tartan"]


class AanTafelTests(VaylideTestCase):
    def manifest(self):
        return Template.objects.get(slug="aan-tafel").current_version.manifest

    def test_four_readable_colour_variants(self):
        data = self.manifest()
        self.assertEqual(data["occasions"], ["kerst"])
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertEqual([p["key"] for p in data["palettes"]], KLEUREN)
        pairs = [("ink", "bg"), ("ink", "bg-2"), ("muted", "bg"), ("muted", "bg-2"), ("accent", "bg"), ("accent", "bg-2"),
                 ("accent-ink", "accent"), ("card-ink", "card"), ("cover-ink", "page")]
        for palette in data["palettes"]:
            c = {k[5:]: v for k, v in palette["vars"].items() if k.startswith("--at-")}
            for fg, bg in pairs:
                self.assertGreaterEqual(contrast(c[fg], c[bg]), 4.5, f"{palette['key']}: {fg} op {bg}")
        self.assertEqual(len(DESIGN_IMAGES["aan-tafel"]), 5)

    def test_demo_has_place_card_opening_and_music(self):
        for kleur in KLEUREN:
            response = Client().get(f"/voorbeeld/aan-tafel/?kleur={kleur}")
            self.assertEqual(response.status_code, 200, kleur)
            html = response.content.decode()
            self.assertIn('class="at-kaartje"', html)
            self.assertIn("Een plaats aan tafel", html)
            self.assertGreaterEqual(html.count('class="at-kaars '), 7)
            self.assertIn("Menu", html)
            self.assertIn('href="#uitnodiging"', html)  # opent ook zonder JavaScript
            self.assertIn('data-music-synth="we-wish-you"', html)
            self.assertIn("Openen met muziek", html)
            self.assertNotIn("autoplay", html)
            self.assertIn('name="robots" content="noindex', html)
            # Geen verlopen met id's in de tekeningen: onderdelen staan soms meer dan eens op de pagina.
            self.assertNotIn('url(#', html)
            self.assertEqual(len(re.findall(r"<script>", html)), 1)

    def test_music_arrangement_is_defined(self):
        js = (settings.BASE_DIR / "invitations/static/invitations/invite.js").read_text(encoding="utf-8")
        self.assertIn('"we-wish-you": (function', js)
        self.assertIn("function createArrangement(tune)", js)
        for inst in ("piano", "pizz", "bellen", "strijkers"):
            self.assertIn(f'inst: "{inst}"', js)

    def test_motion_only_with_motion_on(self):
        css = (settings.BASE_DIR / "designs/aan-tafel/v1/style.css").read_text(encoding="utf-8")
        for rule in re.findall(r"^[^@\n][^{\n]*\{[^}\n]*animation:[^}\n]*infinite[^}\n]*\}", css, flags=re.M):
            self.assertIn(".fx-motion", rule, rule)
            self.assertIn("animation-play-state: var(--fx-play, running)", rule, rule)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)

    def test_couple_and_long_names_render(self):
        template = Template.objects.get(slug="aan-tafel")
        content = demo_content("aan-tafel", "bruiloft")
        content["names"] = {"partner_1": "Maximiliaan-Alexander van den Boogaard", "partner_2": "Ernestina"}
        view = build_view(occasion="bruiloft", content=content, overrides={}, template_version=template.current_version,
                          options=RenderOptions(mode="demo"))
        html = render_to_string(template.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
        self.assertIn("at-names__amp", html)
        self.assertIn(f"at-names--{view['names_size']}", html)
        self.assertIn("Maximiliaan-Alexander", html)

    def test_drawings_are_made_by_the_tool(self):
        for name in ("_slinger.html", "_takje.html"):
            text = (settings.BASE_DIR / "designs/aan-tafel/v1" / name).read_text(encoding="utf-8")
            self.assertIn("tools/aan_tafel/maak_tekeningen.py", text)
            self.assertNotIn("url(#", text)

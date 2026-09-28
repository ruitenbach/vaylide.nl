"""Voor altijd: bruiloftsontwerp met een ringdoosje als opening, vier kleuren en de Canon in D."""
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

KLEUREN = ["salie", "bordeaux", "nachtblauw", "poederroze"]


class VoorAltijdTests(VaylideTestCase):
    def manifest(self):
        return Template.objects.get(slug="voor-altijd").current_version.manifest

    def test_four_readable_colour_variants(self):
        data = self.manifest()
        self.assertEqual(data["occasions"][0], "bruiloft")
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertEqual([p["key"] for p in data["palettes"]], KLEUREN)
        pairs = [("ink", "bg"), ("ink", "bg-2"), ("muted", "bg"), ("muted", "bg-2"), ("accent", "bg"), ("accent", "bg-2"),
                 ("gold-2", "bg"), ("gold-2", "bg-2"), ("accent-ink", "accent"), ("cover-ink", "page")]
        for palette in data["palettes"]:
            c = {k[5:]: v for k, v in palette["vars"].items() if k.startswith("--va-")}
            for fg, bg in pairs:
                self.assertGreaterEqual(contrast(c[fg], c[bg]), 4.5, f"{palette['key']}: {fg} op {bg}")
        self.assertEqual(len(DESIGN_IMAGES["voor-altijd"]), 5)

    def test_demo_has_ring_box_opening_and_canon(self):
        for kleur in KLEUREN:
            response = Client().get(f"/voorbeeld/voor-altijd/?kleur={kleur}")
            self.assertEqual(response.status_code, 200, kleur)
            html = response.content.decode()
            self.assertIn('class="va-doos"', html)
            self.assertIn('href="#uitnodiging"', html)  # opent ook zonder JavaScript
            self.assertEqual(html.count('class="va-ringen__svg"'), 2)  # in het doosje en bij de afsluiting
            self.assertIn('class="va-krans__svg"', html)
            self.assertIn('data-music-synth="canon"', html)
            self.assertNotIn("autoplay", html)
            self.assertIn('name="robots" content="noindex', html)
            self.assertNotIn("url(#", html)
            self.assertEqual(len(re.findall(r"<script>", html)), 1)

    def test_music_arrangement_is_defined(self):
        js = (settings.BASE_DIR / "invitations/static/invitations/invite.js").read_text(encoding="utf-8")
        self.assertIn('"canon": (function', js)
        self.assertIn("viool: function", js)
        for inst in ("harp", "strijkers", "viool"):
            self.assertIn(f'inst: "{inst}"', js)

    def test_motion_only_with_motion_on(self):
        css = (settings.BASE_DIR / "designs/voor-altijd/v1/style.css").read_text(encoding="utf-8")
        for rule in re.findall(r"^[^@\n][^{\n]*\{[^}\n]*animation:[^}\n]*infinite[^}\n]*\}", css, flags=re.M):
            self.assertIn(".fx-motion", rule, rule)
            self.assertIn("animation-play-state: var(--fx-play, running)", rule, rule)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)

    def test_every_occasion_renders_with_long_names(self):
        template = Template.objects.get(slug="voor-altijd")
        for occasion in ("bruiloft", "verloving", "jubileum"):
            content = demo_content("voor-altijd", occasion)
            view = build_view(occasion=occasion, content=content, overrides={}, template_version=template.current_version,
                              options=RenderOptions(mode="demo"))
            html = render_to_string(template.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
            self.assertIn(f"va-names--{view['names_size']}", html, occasion)
        content = demo_content("voor-altijd", "bruiloft")
        content["names"] = {"partner_1": "Maximiliaan-Alexander van den Boogaard", "partner_2": "Ernestina"}
        view = build_view(occasion="bruiloft", content=content, overrides={}, template_version=template.current_version,
                          options=RenderOptions(mode="demo"))
        html = render_to_string(template.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
        self.assertIn("va-names__amp", html)
        self.assertIn("Maximiliaan-Alexander", html)

    def test_drawings_are_made_by_the_tool(self):
        for name in ("_krans.html", "_takje.html", "_ringen.html"):
            text = (settings.BASE_DIR / "designs/voor-altijd/v1" / name).read_text(encoding="utf-8")
            self.assertIn("tools/voor_altijd/maak_tekeningen.py", text)
            self.assertNotIn("url(#", text)

    def test_listed_first_for_weddings(self):
        response = Client().get("/ontwerpen/?gelegenheid=bruiloft")
        self.assertEqual(response.context["cards"][0]["template"].slug, "voor-altijd")

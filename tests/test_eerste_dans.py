"""Eerste dans: bruiloftsontwerp met paleisdeuren en een lakzegel, een balzaal en een getekend bruidspaar dat danst."""
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

KLEUREN = ["hemelsblauw", "champagne", "salie", "poederroze"]


class EersteDansTests(VaylideTestCase):
    def manifest(self):
        return Template.objects.get(slug="eerste-dans").current_version.manifest

    def test_four_readable_colour_variants(self):
        data = self.manifest()
        self.assertEqual(data["occasions"][0], "bruiloft")
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertEqual([p["key"] for p in data["palettes"]], KLEUREN)
        pairs = [("ink", "bg"), ("ink", "bg-2"), ("muted", "bg"), ("muted", "bg-2"), ("accent", "bg"), ("accent", "bg-2"),
                 ("gold-2", "bg"), ("gold-2", "bg-2"), ("accent-ink", "accent"), ("cover-ink", "door"), ("cover-ink", "page"), ("muted", "door")]
        for palette in data["palettes"]:
            c = {k[5:]: v for k, v in palette["vars"].items() if k.startswith("--ed-")}
            for fg, bg in pairs:
                self.assertGreaterEqual(contrast(c[fg], c[bg]), 4.5, f"{palette['key']}: {fg} op {bg}")
        self.assertEqual(len(DESIGN_IMAGES["eerste-dans"]), 5)

    def test_demo_has_palace_doors_seal_and_the_couple(self):
        for kleur in KLEUREN:
            response = Client().get(f"/voorbeeld/eerste-dans/?kleur={kleur}")
            self.assertEqual(response.status_code, 200, kleur)
            html = response.content.decode()
            self.assertIn('class="ed-deuren"', html)
            self.assertIn('class="ed-zegel fx-pulse"', html)
            self.assertIn('href="#uitnodiging"', html)  # opent ook zonder JavaScript
            self.assertEqual(html.count('class="ed-paar__svg"'), 1)
            self.assertIn('class="ed-bruid"', html)
            self.assertIn('class="ed-bruidegom"', html)
            self.assertEqual(html.count('class="ed-kroon__svg"'), 2)  # in de zaal en bij de afsluiting
            self.assertIn('class="ed-slinger__svg"', html)
            self.assertIn('data-music-synth="canon"', html)
            self.assertNotIn("autoplay", html)
            self.assertNotIn("url(#", html)
            self.assertNotIn("{#", html)
            self.assertIn('name="robots" content="noindex', html)
            self.assertEqual(len(re.findall(r"<script>", html)), 1)

    def test_couple_has_white_dress_black_suit_and_blond_hair(self):
        paar = (settings.BASE_DIR / "designs/eerste-dans/v1/_paar.html").read_text(encoding="utf-8")
        bruid = paar[paar.index('class="ed-bruid"'):]
        bruidegom = paar[paar.index('class="ed-bruidegom"'):paar.index('class="ed-bruid"')]
        self.assertIn('fill="#FFFFFF"', bruid)   # witte jurk en sluier
        self.assertIn('fill="#E4BD72"', bruid)   # blond haar
        self.assertIn('fill="#202027"', bruidegom)  # zwart jasje
        self.assertIn('fill="#1B1B20"', bruidegom)  # zwarte broek

    def test_motion_only_with_motion_on(self):
        css = (settings.BASE_DIR / "designs/eerste-dans/v1/style.css").read_text(encoding="utf-8")
        rules = re.findall(r"^[^@\n][^{\n]*\{[^}\n]*animation:[^}\n]*infinite[^}\n]*\}", css, flags=re.M)
        self.assertGreaterEqual(len(rules), 5)
        for rule in rules:
            self.assertIn(".fx-motion", rule, rule)
            self.assertIn("animation-play-state: var(--fx-play, running)", rule, rule)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)

    def test_every_occasion_renders_with_long_names(self):
        template = Template.objects.get(slug="eerste-dans")
        for occasion in ("bruiloft", "verloving"):
            content = demo_content("eerste-dans", occasion)
            view = build_view(occasion=occasion, content=content, overrides={}, template_version=template.current_version,
                              options=RenderOptions(mode="demo"))
            html = render_to_string(template.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
            self.assertIn(f"ed-names--{view['names_size']}", html, occasion)
        content = demo_content("eerste-dans", "bruiloft")
        content["names"] = {"partner_1": "Maximiliaan-Alexander van den Boogaard", "partner_2": "Ernestina"}
        view = build_view(occasion="bruiloft", content=content, overrides={}, template_version=template.current_version,
                          options=RenderOptions(mode="demo"))
        html = render_to_string(template.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
        self.assertIn("ed-names__amp", html)
        self.assertIn("Maximiliaan-Alexander", html)

    def test_seal_follows_the_package(self):
        template = Template.objects.get(slug="eerste-dans")
        content = demo_content("eerste-dans", "bruiloft")
        for features, personal in (([], False), (["zegel"], True)):
            view = build_view(occasion="bruiloft", content=content, overrides={}, template_version=template.current_version,
                              options=RenderOptions(mode="demo", features=features))
            html = render_to_string(template.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
            cover = html[html.index('class="ed-zegel'):html.index("ed-cover__onder")]
            self.assertEqual("seal-motief" not in cover, personal)
            self.assertEqual(f"--ed-seal:{view['seal_std']['base']}" in cover, not personal)

    def test_drawings_are_made_by_the_tool(self):
        for name in ("_paar.html", "_kroonluchter.html", "_slinger.html"):
            text = (settings.BASE_DIR / "designs/eerste-dans/v1" / name).read_text(encoding="utf-8")
            self.assertIn("tools/eerste_dans/maak_tekeningen.py", text)
            self.assertNotIn("url(#", text)

    def test_in_the_collection_for_weddings(self):
        response = Client().get("/ontwerpen/?gelegenheid=bruiloft")
        slugs = [c["template"].slug for c in response.context["cards"]]
        self.assertEqual(slugs[0], "eerste-dans")                                      # het nieuwst toegevoegde gewone bruiloftsontwerp staat vooraan (added_at)
        self.assertLess(slugs.index("eerste-dans"), slugs.index("liefde-op-papier"))
        self.assertContains(Client().get("/ontwerpen/eerste-dans/"), "Paleisdeuren met lakzegel")

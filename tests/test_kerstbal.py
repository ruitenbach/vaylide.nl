"""Kerstbal: de kerstkaart bij het filmpje van een rood-gouden kerstbal (de bal gaat open en de kaart komt eruit)."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import Client

from catalog.atelier import contrast
from catalog.effects import effects_errors
from catalog.models import Template
from core.csp import BOOT_SCRIPT
from invitations.demo import DEFAULT_DEMO_OCCASION, DESIGN_IMAGES, demo_content
from invitations.render import RenderOptions, build_view

from .helpers import VaylideTestCase
from .test_kerst import greeting_only

AMS = ZoneInfo("Europe/Amsterdam")
FOLDER = settings.BASE_DIR / "designs" / "kerstbal" / "v1"


def read(name: str) -> str:
    return (FOLDER / name).read_text(encoding="utf-8")


class KerstbalDesignTests(VaylideTestCase):
    def manifest(self):
        return json.loads(read("manifest.json"))

    def render(self, occasion="kerst", content=None, now=None, headline=""):
        template = Template.objects.get(slug="kerstbal")
        content = content or demo_content("kerstbal", occasion)
        if headline:
            content["headline"] = headline
        v = build_view(occasion=occasion, content=content, overrides={}, template_version=template.current_version,
                       options=RenderOptions(mode="demo", now=now, music_synth=True))
        return v, render_to_string("kerstbal/v1/invitation.html", {"v": v, "rsvp_form": {}})

    def test_manifest_palette_effects_and_readable_colours(self):
        data = self.manifest()
        self.assertEqual(data["occasions"], ["kerst"])
        self.assertEqual(DEFAULT_DEMO_OCCASION["kerstbal"], "kerst")
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertEqual([p["key"] for p in data["palettes"]], ["kerstrood"])
        c = {k[5:]: v for k, v in data["palettes"][0]["vars"].items() if k.startswith("--kb-")}
        for fg, bg in (("ink", "card"), ("ink", "card-2"), ("muted", "card"), ("gold", "card"), ("line", "card"), ("btn-ink", "btn"), ("ink", "field")):
            self.assertGreaterEqual(contrast(c[fg], c[bg]), 4.5, f"{fg} op {bg}")

    def test_film_and_images_are_there_and_light(self):
        img = FOLDER / "img"
        for name in ("kerstbal.mp4", "kerstbal.webm"):
            self.assertTrue((img / name).is_file(), name)
            self.assertLess((img / name).stat().st_size, 1024 * 1024, name)
        self.assertTrue(finders.find("designs/kerstbal/v1/img/poster.webp"))
        self.assertTrue(finders.find("img/designs/kerstbal.webp"))
        for name in DESIGN_IMAGES["kerstbal"]:
            self.assertTrue(finders.find(f"img/demo/{name}.webp") and finders.find(f"img/demo/{name}-1000.webp"), name)

    def test_demo_page_has_the_whole_card(self):
        response = Client().get("/voorbeeld/kerstbal/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        for fragment in (
            'class="cover kb-cover" data-cover', 'class="kb-ball fx-pulse" data-open', "Tik op de kerstbal", "Warme kerstgroeten",
            "designs/kerstbal/v1/img/kerstbal.webm", "designs/kerstbal/v1/img/kerstbal.mp4", "Familie Van Dijk",
            "Sanne, Daan, Lotte en Siem", "Programma", "Locatie", "Ben jij erbij?", "data-rsvp", 'data-music-synth="stille-nacht"',
            "Digitale kerstkaart gemaakt met",
        ):
            self.assertIn(fragment, html)
        self.assertEqual(html.count("<script>"), 1)
        self.assertIn(f"<script>{BOOT_SCRIPT}</script>", html)
        self.assertNotIn("<style", html)
        self.assertNotIn("kaart.invalid", html)
        self.assertLess(html.index("designs/kerstbal/v1/kerstbal.js"), html.index("invitations/invite.js"))

    def test_film_is_silent_decorative_and_starts_only_after_a_tap(self):
        html = read("invitation.html")
        video = html.split("<video", 1)[1].split("</video>", 1)[0]
        for part in ("muted", "playsinline", "poster=", "kerstbal.webm", "kerstbal.mp4"):
            self.assertIn(part, video)
        self.assertNotIn("controls", video)
        self.assertNotIn("autoplay", video)
        script = read("kerstbal.js")
        # Het gedeelde invite.js blijft ongemoeid: dit ontwerp start de film zelf, na de tik.
        for part in ("invite:opening", "reduceMotion", "fx-paused", "cover-video-failed"):
            self.assertIn(part, script)

    def test_motion_follows_the_house_rules(self):
        css = read("style.css")
        self.assertNotRegex(css, r"(?m)^\.kb-cover \{[^}]*display")
        for line in css.splitlines():
            if "infinite" in line and "animation:" in line:
                self.assertIn("animation-play-state: var(--fx-play, running)", line, line)
        self.assertNotIn("data:font", css)
        self.assertNotIn("<", css)

    def test_greeting_without_dinner(self):
        content = greeting_only(demo_content("kerstbal", "kerst"))
        v, html = self.render(content=content, now=datetime(2026, 10, 15, 12, tzinfo=AMS))
        self.assertFalse(v["has_event"])
        self.assertNotIn("kb-date__day", html)
        self.assertNotIn("Ben jij erbij?", html)

    def test_preview_without_sender_has_no_loose_name(self):
        content = demo_content("kerstbal", "kerst")
        content["names"] = {"family": "", "members": ""}
        _, html = self.render(content=content)
        self.assertNotIn('class="kb-cover__title', html)
        self.assertNotIn('class="kb-card__names', html)

    def test_other_occasions_keep_working(self):
        _, html = self.render(occasion="bruiloft")
        self.assertNotIn("Warme kerstgroeten", html)


class KerstbalV2Tests(VaylideTestCase):
    """v2: dezelfde film en vormgeving; alleen de timing aan het einde van de opening is bijgesteld (geen donker, leeg moment)."""
    V1 = settings.BASE_DIR / "designs" / "kerstbal" / "v1"
    V2 = settings.BASE_DIR / "designs" / "kerstbal" / "v2"

    def test_film_and_images_are_the_same_as_v1(self):
        for name in ("kerstbal.mp4", "kerstbal.webm", "poster.webp"):
            self.assertEqual((self.V1 / "img" / name).read_bytes(), (self.V2 / "img" / name).read_bytes(), name)

    def test_manifest_is_version_two_with_the_same_design(self):
        m1 = json.loads((self.V1 / "manifest.json").read_text(encoding="utf-8"))
        m2 = json.loads((self.V2 / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(m2["version"], 2)
        for key in m1:
            if key not in ("version", "changelog"):
                self.assertEqual(m1[key], m2[key], key)

    def test_v2_only_changes_the_timing_of_the_opening(self):
        new = (self.V2 / "style.css").read_text(encoding="utf-8")
        old = (self.V1 / "style.css").read_text(encoding="utf-8")
        self.assertIn("kb-card-in 2.9s", new)
        self.assertIn("kb-card-fly 1.2s", new)
        self.assertIn("kb-cover-out .6s ease 5.2s", new)
        self.assertTrue(any("@keyframes kb-sheet-in" in line and "to { opacity: 1" in line for line in new.splitlines()))
        # de rest van de vormgeving is gelijk aan v1: zonder de bijgestelde regels blijft er niets over dat verschilt
        drop = ("Kerstbal v", "De kaart komt uit de bal", "animation: kb-card-in", "kb-cover-out", "kb-sheet-in", "/* v2:")
        keep = lambda text: [line for line in text.splitlines() if not any(d in line for d in drop)]
        self.assertEqual(keep(old), keep(new))

    def test_v2_points_only_to_its_own_files_and_renders(self):
        html = (self.V2 / "invitation.html").read_text(encoding="utf-8")
        self.assertNotIn("kerstbal/v1/", html)
        self.assertIn("kerstbal/v2/img/kerstbal.webm", html)
        v1_html = (self.V1 / "invitation.html").read_text(encoding="utf-8").replace("v1", "v2")
        self.assertEqual(v1_html.replace('data-duration="4100"', 'data-duration="5900"').replace('data-fx-intro="3500"', 'data-fx-intro="5200"'), html)
        template = Template.objects.get(slug="kerstbal")
        version = template.versions.get(number=2)
        v = build_view(occasion="kerst", content=demo_content("kerstbal", "kerst"), overrides={}, template_version=version,
                       options=RenderOptions(mode="demo", music_synth=True))
        out = render_to_string("kerstbal/v2/invitation.html", {"v": v, "rsvp_form": {}})
        self.assertIn("kb-sheet", out)

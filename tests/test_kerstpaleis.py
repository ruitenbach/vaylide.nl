"""Kerstpaleis: de kerstkaart bij het filmpje van de eigenaar (de deuren van een besneeuwd paleis gaan open)."""
import json
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import Client

from catalog import prijzen
from catalog.atelier import contrast
from catalog.effects import effects_errors
from catalog.models import Template
from core.csp import BOOT_SCRIPT
from invitations.demo import DEFAULT_DEMO_OCCASION, DESIGN_IMAGES, demo_content
from invitations.render import RenderOptions, build_view

from .helpers import VaylideTestCase
from .test_kerst import greeting_only

AMS = ZoneInfo("Europe/Amsterdam")
FOLDER = settings.BASE_DIR / "designs" / "kerstpaleis" / "v1"
PALETTES = ["kerstrood", "dennengroen", "nachtblauw"]


def read(name: str) -> str:
    return (FOLDER / name).read_text(encoding="utf-8")


class KerstpaleisDesignTests(VaylideTestCase):
    def manifest(self):
        return json.loads(read("manifest.json"))

    def render(self, occasion="kerst", content=None, now=None, headline=""):
        template = Template.objects.get(slug="kerstpaleis")
        content = content or demo_content("kerstpaleis", occasion)
        if headline:
            content["headline"] = headline
        v = build_view(occasion=occasion, content=content, overrides={}, template_version=template.current_version,
                       options=RenderOptions(mode="demo", now=now, music_synth=True))
        return v, render_to_string("kerstpaleis/v1/invitation.html", {"v": v, "rsvp_form": {}})

    def test_manifest_palettes_effects_and_readable_colours(self):
        data = self.manifest()
        self.assertEqual(data["occasions"], ["kerst"])
        self.assertEqual(DEFAULT_DEMO_OCCASION["kerstpaleis"], "kerst")
        self.assertEqual(data["opening"], "film")
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertEqual([p["key"] for p in data["palettes"]], PALETTES)
        pairs = [("ink", "paper"), ("ink", "paper-2"), ("muted", "paper"), ("muted", "paper-2"), ("accent", "paper"),
                 ("accent", "paper-2"), ("accent-ink", "accent"), ("gold-2", "paper"), ("gold-2", "paper-2"),
                 ("gold", "velvet-2"), ("gold", "page")]
        for palette in data["palettes"]:
            c = {k[5:]: v for k, v in palette["vars"].items() if k.startswith("--kp-")}
            for fg, bg in pairs:
                self.assertGreaterEqual(contrast(c[fg], c[bg]), 4.5, f"{palette['key']}: {fg} op {bg}")

    def test_price_is_luxe_and_follows_the_existing_structure(self):
        template = Template.objects.get(slug="kerstpaleis")
        info = prijzen.prijs_info(template, "kerst")
        self.assertEqual((info["tier"], info["cents"], info["maanden"]), ("luxe", 2495, 12))

    def test_film_and_images_are_there_and_light(self):
        img = FOLDER / "img"
        for name in ("kerstpaleis.mp4", "kerstpaleis.webm"):
            self.assertTrue((img / name).is_file(), name)
            self.assertLess((img / name).stat().st_size, 1024 * 1024, name)
        for name in ("poster.webp", "velours.webp", "lijst.webp", "fleur.webp", "scheiding.webp", "sier-boven.webp", "sier-onder.webp"):
            self.assertTrue(finders.find(f"designs/kerstpaleis/v1/img/{name}"), name)
        self.assertTrue(finders.find("img/designs/kerstpaleis.webp"))
        self.assertEqual(len(DESIGN_IMAGES["kerstpaleis"]), 5)
        for name in DESIGN_IMAGES["kerstpaleis"]:
            self.assertTrue(finders.find(f"img/demo/{name}.webp") and finders.find(f"img/demo/{name}-1000.webp"), name)

    def test_demo_page_has_the_whole_card(self):
        for palette in PALETTES:
            response = Client().get("/voorbeeld/kerstpaleis/", {"kleur": palette})
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertIn(f'data-palette="{palette}"', html)
            for fragment in (
                'class="cover kp-cover" data-cover', 'href="#uitnodiging" class="kp-open fx-pulse" data-open', "Open de deuren",
                "Een kerstgroet voor jou", "Openen met muziek", "designs/kerstpaleis/v1/img/kerstpaleis.webm",
                "designs/kerstpaleis/v1/img/kerstpaleis.mp4", "Fijne", "kerstdagen", "en een schitterend nieuwjaar",
                "Familie Van Dijk", "Sanne, Daan, Lotte en Siem", 'data-fx-slot="hero"', 'data-fx-slot="cover"',
                "De avond", "Programma", "Aftellen", "Waar", "Schuif je aan?", "data-rsvp", 'data-music-synth="stille-nacht"',
                "Digitale kerstkaart gemaakt met",
            ):
                self.assertIn(fragment, html)
            # Alleen het vaste startscript met een hash in de CSP, geen eigen inline scripts of stijlblokken.
            self.assertEqual(html.count("<script>"), 1)
            self.assertIn(f"<script>{BOOT_SCRIPT}</script>", html)
            self.assertNotIn("<style", html)
            # De voorbeeldkaart van de collega had een eigen kleurkiezer en nepformulier: die zijn van het platform.
            self.assertNotIn("data-pv-kleur", html)

    def test_film_is_silent_decorative_and_starts_only_after_a_tap(self):
        html = read("invitation.html")
        video = html.split("<video", 1)[1].split("</video>", 1)[0]
        for part in ("data-kp-film", "muted", "playsinline", 'preload="auto"', "poster=", "kerstpaleis.webm", "kerstpaleis.mp4"):
            self.assertIn(part, video)
        self.assertNotIn("controls", video)
        self.assertNotIn("autoplay", video)
        self.assertIn('<div class="kp-film" aria-hidden="true">', html)
        self.assertTrue(finders.find("designs/kerstpaleis/v1/kerstpaleis.js"))
        script = read("kerstpaleis.js")
        for part in ("invite:opening", "reduceMotion", "fx-paused", "kp-cover--playing"):
            self.assertIn(part, script)

    def test_motion_follows_the_house_rules(self):
        css = read("style.css")
        self.assertNotRegex(css, r"(?m)^\.kp-cover \{[^}]*display")
        for line in css.splitlines():
            if "infinite" in line and "animation:" in line:
                self.assertIn("animation-play-state: var(--fx-play, running)", line, line)
        self.assertIn('data-duration="4450"', read("invitation.html"))

    def test_greeting_without_dinner(self):
        content = greeting_only(demo_content("kerstpaleis", "kerst"))
        v, html = self.render(content=content, now=datetime(2026, 10, 15, 12, tzinfo=AMS))
        self.assertFalse(v["has_event"])
        self.assertIn("en een schitterend nieuwjaar", html)
        self.assertNotIn("De avond", html)
        self.assertNotIn("Schuif je aan?", html)

    def test_own_headline_replaces_the_greeting(self):
        _, html = self.render(headline="Prettige feestdagen")
        self.assertIn("Prettige feestdagen", html)
        self.assertNotIn("<span>kerstdagen</span>", html)

    def test_long_sender_gets_smaller_letters(self):
        content = demo_content("kerstpaleis", "kerst")
        content["names"]["family"] = "Familie Van den Heuvel-Oosterbroek"
        v, html = self.render(content=content)
        self.assertEqual(v["names_size"], "xlong")
        self.assertIn("kp-from__name--xlong", html)

    def test_preview_without_sender_has_no_empty_name(self):
        content = demo_content("kerstpaleis", "kerst")
        content["names"] = {"family": "", "members": ""}
        _, html = self.render(content=content)
        self.assertNotIn('class="kp-from__name', html)
        self.assertNotIn("van Kerst", html)

    def test_other_occasions_keep_working(self):
        _, html = self.render(occasion="bruiloft")
        self.assertIn("Een uitnodiging voor jou", html)
        self.assertNotIn("Een kerstgroet", html)
        self.assertNotIn("Fijne", html.split('class="kp-body"', 1)[0].split("kp-hero", 1)[1])


class NieuweKerstkaartenPrijsTests(VaylideTestCase):
    def test_kerstmarkt_kerstpaleis_en_kerstcoupe_zijn_luxe_voor_24_95(self):
        # Besluit van de eigenaar (15 oktober 2026): alle vier Luxe, € 24,95 incl. btw, via de bestaande prijsstructuur.
        for slug in ("kerstmarkt", "kerstpaleis", "kerstcoupe", "kerstbal"):
            info = prijzen.prijs_info(Template.objects.get(slug=slug), "kerst")
            self.assertEqual((info["tier"], info["cents"], info["display"]), ("luxe", 2495, "€ 24,95"), slug)

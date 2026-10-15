"""Kerstcoupé: de kerstkaart bij het filmpje van de eigenaar (de gordijnen van een treincoupé gaan open)."""
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import Client

from catalog.atelier import contrast
from catalog.effects import effect_summary, effects_errors
from catalog.models import Template
from core.csp import BOOT_SCRIPT
from invitations.demo import DEFAULT_DEMO_OCCASION, DESIGN_IMAGES, demo_content
from invitations.render import RenderOptions, build_view

from .helpers import VaylideTestCase
from .test_kerst import greeting_only

AMS = ZoneInfo("Europe/Amsterdam")
FOLDER = settings.BASE_DIR / "designs" / "kerstcoupe" / "v1"
PALETTES = ["fluweel", "sneeuwnacht", "mahonie"]


def read(name: str) -> str:
    return (FOLDER / name).read_text(encoding="utf-8")


class KerstcoupeDesignTests(VaylideTestCase):
    def manifest(self):
        return json.loads(read("manifest.json"))

    def render(self, occasion="kerst", content=None, now=None, headline=""):
        template = Template.objects.get(slug="kerstcoupe")
        content = content or demo_content("kerstcoupe", occasion)
        if headline:
            content["headline"] = headline
        v = build_view(occasion=occasion, content=content, overrides={}, template_version=template.current_version,
                       options=RenderOptions(mode="demo", now=now, music_synth=True))
        return v, render_to_string("kerstcoupe/v1/invitation.html", {"v": v, "rsvp_form": {}})

    def test_manifest_palettes_effects_and_readable_colours(self):
        data = self.manifest()
        self.assertEqual(data["occasions"], ["kerst"])
        self.assertEqual(DEFAULT_DEMO_OCCASION["kerstcoupe"], "kerst")
        self.assertEqual(data["opening"], "film")
        self.assertEqual(data["kaartbeeld"], "raam")
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertEqual(effect_summary(data["effects"]), "Zacht vallende sneeuw.")
        self.assertEqual([p["key"] for p in data["palettes"]], PALETTES)
        # Tekst op het papier, op de donkere pagina en de knoppen: minstens 4,5:1.
        pairs = [("ink", "paper"), ("ink", "paper-2"), ("muted", "paper"), ("muted", "paper-2"), ("accent", "paper"),
                 ("accent", "paper-2"), ("accent-ink", "accent"), ("gold-2", "paper"), ("gold-2", "paper-2"),
                 ("page-ink", "page"), ("page-ink", "page-2"), ("page-muted", "page"), ("page-muted", "page-2"),
                 ("gold", "page"), ("gold", "page-2")]
        for palette in data["palettes"]:
            c = {k[5:]: v for k, v in palette["vars"].items() if k.startswith("--kc-")}
            for fg, bg in pairs:
                self.assertGreaterEqual(contrast(c[fg], c[bg]), 4.5, f"{palette['key']}: {fg} op {bg}")

    def test_film_and_images_are_there_and_light(self):
        img = FOLDER / "img"
        # Het filmpje: alleen het stuk waarin de gordijnen opengaan (zonder de tekst uit het filmpje), elk onder 1 MB.
        for name in ("coupe.mp4", "coupe.webm"):
            self.assertTrue((img / name).is_file(), name)
            self.assertLess((img / name).stat().st_size, 1024 * 1024, name)
        # Eerste en laatste beeld (opening en kop), de zachte achtergrond voor brede schermen en de tafel van het slot.
        for name in ("dicht.webp", "open.webp", "dicht-zacht.webp", "open-zacht.webp", "tafel.webp"):
            self.assertTrue(finders.find(f"designs/kerstcoupe/v1/img/{name}"), name)
        self.assertLess(sum((img / n).stat().st_size for n in ("dicht.webp", "dicht-zacht.webp")), 100 * 1024)
        self.assertTrue(finders.find("img/designs/kerstcoupe.webp"))
        self.assertEqual(len(DESIGN_IMAGES["kerstcoupe"]), 5)
        for name in DESIGN_IMAGES["kerstcoupe"]:
            self.assertTrue(finders.find(f"img/demo/{name}.webp") and finders.find(f"img/demo/{name}-1000.webp"), name)

    def test_demo_page_has_the_whole_card(self):
        for palette in PALETTES:
            response = Client().get("/voorbeeld/kerstcoupe/", {"kleur": palette})
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertIn(f'data-palette="{palette}"', html)
            for fragment in (
                'class="cover kc-cover" data-cover', 'href="#uitnodiging" class="kc-open fx-pulse" data-open',
                "Een kerstgroet voor jou", "van Familie Van Dijk", "Open de gordijnen", "Openen met muziek",
                "designs/kerstcoupe/v1/img/coupe.webm", "designs/kerstcoupe/v1/img/coupe.mp4", "img/dicht.webp", "img/open.webp",
                "Fijne kerstdagen", "en een schitterend", "nieuwjaar",
                '<h1 class="kc-names kc-names--long fx-names">Familie Van Dijk</h1>', "Sanne, Daan, Lotte en Siem",
                'class="fx-slot kc-glass" data-fx-slot="hero"', 'class="fx-slot kc-glass" data-fx-slot="cover"',
                "kc-steam", "data-tekst-op-beeld", "data-kc-fit",
                "Gereserveerd", "Dinerkaart", "Het programma", "kc-menu__dots", "Bestemming", "Reserveer je plaats",
                "Uitzicht onderweg", "img/tafel.webp", 'data-music-synth="stille-nacht"', 'data-fx-sfeer="sneeuw"',
                "Digitale kerstkaart gemaakt met",
            ):
                self.assertIn(fragment, html)
            # Geen eigen inline scripts of stijlblokken: alleen het vaste startscript met een hash in de CSP.
            self.assertEqual(html.count("<script>"), 1)
            self.assertIn(f"<script>{BOOT_SCRIPT}</script>", html)
            self.assertNotIn("<style", html)

    def test_film_is_silent_decorative_and_starts_only_after_a_tap(self):
        html = read("invitation.html")
        video = html.split("<video", 1)[1].split("</video>", 1)[0]
        for part in ("data-kc-film", "muted", "playsinline", 'preload="auto"', "poster=", "coupe.webm", "coupe.mp4"):
            self.assertIn(part, video)
        self.assertNotIn("controls", video)
        self.assertNotIn("autoplay", video)
        self.assertIn('<div class="kc-stage" aria-hidden="true">', html)
        # Het script moet vóór invite.js draaien: het zet de tijden van de opening voordat invite.js ze leest.
        page = Client().get("/voorbeeld/kerstcoupe/").content.decode()
        self.assertLess(page.index("designs/kerstcoupe/v1/kerstcoupe.js"), page.index("invitations/invite.js"))
        self.assertTrue(finders.find("designs/kerstcoupe/v1/kerstcoupe.js"))
        script = read("kerstcoupe.js")
        for part in ("prefers-reduced-motion", "fx-paused", "kc-cover--speelt", "data-duration", "data-fx-intro", "--kc-out",
                     "attempt.catch(fade)", '"--kc-bar"', '"--kc-fit"',
                     # Nog niet geladen (iPhone): 0,8 seconde wachten op het filmpje, en bij haperen de overvloeier.
                     "film.readyState < 4", "}, 800);", 'film.addEventListener("waiting"'):
            self.assertIn(part, script)
        # Het open raam ligt boven het filmpje, zodat de overvloeier ook over een blijven hangen filmpje gaat.
        self.assertLess(html.index("<video"), html.index('class="kc-frame__open"'))

    def test_motion_follows_the_house_rules(self):
        css = read("style.css")
        # Zonder JavaScript geen openingsscherm (invite-base.css), ook niet door de eigen opmaak.
        self.assertIn(".js .kc-cover { display: block;", css)
        self.assertNotRegex(css, r"(?m)^\.kc-cover \{[^}]*display")
        # Zonder filmpje een overvloeier; die is de standaard, het filmpje een verbetering.
        self.assertIn(".is-opening .kc-cover:not(.kc-cover--speelt) .kc-frame__open { animation: kc-in", css)
        self.assertIn('data-duration="2700" data-fx-intro="2100"', read("invitation.html"))
        # Alles wat doorloopt staat onder .fx-motion en luistert naar de knop Beweging.
        for line in css.splitlines():
            if "infinite" in line and "animation:" in line:
                self.assertTrue(line.startswith(".fx-motion"), line)
                self.assertIn("animation-play-state: var(--fx-play, running)", line, line)
        # Het schrijven is klaar voordat effects.js de intro afrondt (fx-done na 4,2 s).
        timings = {"kc-greet": (0.15, 1.5), "kc-wish": (1.45, 1.05), "kc-wish--last": (2.3, 0.85)}
        for name, (at, duration) in timings.items():
            self.assertIn(f".{name} {{ --kc-at: {at}s; --kc-dur: {duration}s; }}".replace("0.", "."), css)
            self.assertLessEqual(at + duration, 4.2)
        self.assertIn("animation: kc-letters 1s var(--fx-ease) 3s both;", css)

    def test_same_frame_for_opening_and_hero(self):
        # De opening en de kop gebruiken hetzelfde beeldvak: het laatste filmbeeld gaat naadloos over in de kop.
        css = read("style.css")
        self.assertIn(".kc-stage {\n  position: absolute; top: 0; left: 50%; height: 100%; aspect-ratio: 9 / 16;", css)
        # Opening en kop rekenen met dezelfde schermhoogte (ook als een telefoon de adresbalk in- en uitschuift).
        same = "height: calc(100vh - var(--kc-bar, 0px)); height: max(calc(100svh - var(--kc-bar, 0px)), 600px);"
        self.assertIn(".kc-cover > .kc-backdrop, .kc-cover > .kc-stage { top: var(--kc-bar, 0px); " + same, css)
        self.assertIn(".kc-hero { position: relative; " + same, css)
        self.assertIn("width: max(100cqw, 56.25cqh); height: max(100cqh, 177.78cqw);", css)
        html = read("invitation.html")
        self.assertEqual(html.count('<div class="kc-frame"'), 2)

    def test_greeting_without_dinner(self):
        content = greeting_only(demo_content("kerstcoupe", "kerst"))
        v, html = self.render(content=content, now=datetime(2026, 10, 15, 12, tzinfo=AMS))
        self.assertFalse(v["has_event"])
        self.assertIn("Fijne kerstdagen", html)
        self.assertIn("Aftellen naar kerst", html)
        self.assertNotIn("Gereserveerd", html)
        self.assertNotIn("Reserveer je plaats", html)
        self.assertNotIn("Bestemming", html)

    def test_own_headline_replaces_the_greeting(self):
        _, html = self.render(headline="Prettige feestdagen")
        self.assertIn('<p class="kc-greet kc-write">Prettige feestdagen</p>', html)
        self.assertNotIn("en een schitterend</p>", html.split('class="kc-body"', 1)[0])

    def test_long_sender_gets_smaller_letters(self):
        content = demo_content("kerstcoupe", "kerst")
        content["names"]["family"] = "Familie Van den Heuvel-Oosterbroek"
        v, html = self.render(content=content)
        self.assertEqual(v["names_size"], "xlong")
        self.assertIn("kc-names--xlong", html)
        self.assertIn("van Familie Van den Heuvel-Oosterbroek", html)

    def test_preview_without_sender_has_no_loose_van(self):
        # Bij het samenstellen, voordat de afzender is ingevuld: geen "van Kerst" op het tafelkaartje.
        content = demo_content("kerstcoupe", "kerst")
        content["names"] = {"family": "", "members": ""}
        _, html = self.render(content=content)
        self.assertNotIn("van Kerst", html)
        self.assertNotIn('class="kc-place__from"', html)

    def test_other_occasions_keep_working(self):
        # In Beheer kan het ontwerp ook voor een andere gelegenheid worden aangezet, bijvoorbeeld een winterbruiloft.
        v, html = self.render(occasion="bruiloft")
        self.assertIn("Een uitnodiging voor jou", html)
        self.assertIn('<span class="kc-names__amp" aria-label="en">&amp;</span>', html)
        self.assertIn(v["tagline"], html)
        self.assertNotIn("Fijne kerstdagen", html)
        self.assertNotIn("Een kerstgroet", html)
        self.assertIsNone(re.search(r"Digitale kerstkaart", html))

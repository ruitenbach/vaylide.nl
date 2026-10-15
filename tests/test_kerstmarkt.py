"""Kerstmarkt: de kerstkaart bij het filmpje van de eigenaar (vanuit een reuzenrad over een kerstmarkt; een kaart met een
ster verschijnt, komt naar voren en klapt open)."""
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
FOLDER = settings.BASE_DIR / "designs" / "kerstmarkt" / "v1"
PALETTES = ["avondblauw", "gondelrood", "dennengroen"]


def read(name: str) -> str:
    return (FOLDER / name).read_text(encoding="utf-8")


class KerstmarktDesignTests(VaylideTestCase):
    def manifest(self):
        return json.loads(read("manifest.json"))

    def render(self, occasion="kerst", content=None, now=None, headline="", opening=True):
        template = Template.objects.get(slug="kerstmarkt")
        content = content or demo_content("kerstmarkt", occasion)
        if headline:
            content["headline"] = headline
        content.setdefault("style", {})["opening"] = opening
        v = build_view(occasion=occasion, content=content, overrides={}, template_version=template.current_version,
                       options=RenderOptions(mode="demo", now=now, music_synth=True))
        return v, render_to_string("kerstmarkt/v1/invitation.html", {"v": v, "rsvp_form": {}})

    def test_manifest_palettes_effects_and_readable_colours(self):
        data = self.manifest()
        self.assertEqual(data["occasions"], ["kerst"])
        self.assertEqual(DEFAULT_DEMO_OCCASION["kerstmarkt"], "kerst")
        self.assertEqual(data["opening"], "film")
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertEqual(effect_summary(data["effects"]), "Zacht vallende sneeuw.")
        # Geen knal van effects.js (die vliegt over de tekst): het sterrenstof komt achter de kaart vandaan (style.css).
        self.assertEqual(data["effects"]["knal"], "geen")
        self.assertEqual([p["key"] for p in data["palettes"]], PALETTES)
        # Tekst op het papier, op de donkere pagina en de knoppen: minstens 4,5:1.
        pairs = [("ink", "paper"), ("ink", "paper-2"), ("muted", "paper"), ("muted", "paper-2"), ("accent", "paper"),
                 ("accent", "paper-2"), ("accent-ink", "accent"), ("gold-2", "paper"), ("gold-2", "paper-2"),
                 ("page-ink", "page"), ("page-ink", "page-2"), ("page-muted", "page"), ("page-muted", "page-2"),
                 ("gold", "page"), ("gold", "page-2")]
        for palette in data["palettes"]:
            c = {k[5:]: v for k, v in palette["vars"].items() if k.startswith("--km-")}
            for fg, bg in pairs:
                self.assertGreaterEqual(contrast(c[fg], c[bg]), 4.5, f"{palette['key']}: {fg} op {bg}")

    def test_film_and_images_are_there_and_light(self):
        img = FOLDER / "img"
        # Het filmpje: het begin tot de kaart met de ster er staat (5,5 s), elk onder 1 MB.
        for name in ("markt.mp4", "markt.webm"):
            self.assertTrue((img / name).is_file(), name)
            self.assertLess((img / name).stat().st_size, 1024 * 1024, name)
        # Eerste en laatste beeld (opening en kop), de vage randen, het slot, de gouden rand en het medaillon.
        for name in ("begin.webp", "kaart.webp", "begin-zacht.webp", "kaart-zacht.webp", "slot.webp", "rand.svg", "medaille.svg"):
            self.assertTrue(finders.find(f"designs/kerstmarkt/v1/img/{name}"), name)
        # Wat het openingsscherm meteen laadt (zonder het filmpje): niet meer dan 200 KB aan beelden.
        self.assertLess(sum((img / n).stat().st_size for n in ("begin.webp", "begin-zacht.webp")), 200 * 1024)
        self.assertTrue(finders.find("img/designs/kerstmarkt.webp"))
        self.assertEqual(len(DESIGN_IMAGES["kerstmarkt"]), 5)
        for name in DESIGN_IMAGES["kerstmarkt"]:
            self.assertTrue(finders.find(f"img/demo/{name}.webp") and finders.find(f"img/demo/{name}-1000.webp"), name)

    def test_demo_page_has_the_whole_card(self):
        for palette in PALETTES:
            response = Client().get("/voorbeeld/kerstmarkt/", {"kleur": palette})
            self.assertEqual(response.status_code, 200)
            html = response.content.decode()
            self.assertIn(f'data-palette="{palette}"', html)
            for fragment in (
                'class="cover km-cover" data-cover data-duration="5050" data-fx-intro="4550"',
                'href="#uitnodiging" class="km-open fx-pulse" data-open data-fx-origin>Open de kerstkaart</a>',
                "Een kerstgroet voor jou", "van Familie Van Dijk", "Openen met muziek",
                "designs/kerstmarkt/v1/img/markt.webm", "designs/kerstmarkt/v1/img/markt.mp4", "img/begin.webp", "img/kaart.webp",
                '<span class="km-write">Fijne</span> <span class="km-write km-write--2">kerstdagen</span>',
                "en een gelukkig nieuwjaar",
                '<h1 class="km-names km-names--long fx-names">Familie Van Dijk</h1>', "Sanne, Daan, Lotte en Siem",
                'class="fx-slot km-snow" data-fx-slot="hero"', 'class="fx-slot km-snow" data-fx-slot="cover"',
                "data-km-card", "data-km-frame", "data-km-fit", 'class="km-doors" aria-hidden="true"', "km-star__shape",
                "Jouw kaartje", "Het programma", "km-lights__bulb", "Hier vind je ons", "Kom je ook?", "Ons jaar in beeld",
                "Goed om te weten", "img/slot.webp", "Bekijk de opening nog een keer",
                'data-music-synth="stille-nacht"', 'data-fx-sfeer="sneeuw"', "Digitale kerstkaart gemaakt met",
            ):
                self.assertIn(fragment, html)
            # Geen eigen inline scripts of stijlblokken: alleen het vaste startscript met een hash in de CSP.
            self.assertEqual(html.count("<script>"), 1)
            self.assertIn(f"<script>{BOOT_SCRIPT}</script>", html)
            self.assertNotIn("<style", html)

    def test_film_is_silent_decorative_and_starts_only_after_a_tap(self):
        html = read("invitation.html")
        video = html.split("<video", 1)[1].split("</video>", 1)[0]
        for part in ("data-km-film", "muted", "playsinline", 'preload="auto"', "poster=", "markt.webm", "markt.mp4"):
            self.assertIn(part, video)
        self.assertNotIn("controls", video)
        self.assertNotIn("autoplay", video)
        self.assertIn('<div class="km-stage" aria-hidden="true">', html)
        # Het eindbeeld ligt boven het filmpje, zodat de terugval ook over een blijven hangen filmpje gaat.
        self.assertLess(html.index("<video"), html.index('class="km-frame__end"'))
        # Het script moet vóór invite.js draaien: het start het filmpje voordat invite.js de opening begint.
        page = Client().get("/voorbeeld/kerstmarkt/").content.decode()
        self.assertLess(page.index("designs/kerstmarkt/v1/kerstmarkt.js"), page.index("invitations/invite.js"))
        self.assertTrue(finders.find("designs/kerstmarkt/v1/kerstmarkt.js"))
        script = read("kerstmarkt.js")
        for part in ("prefers-reduced-motion", "fx-paused", "km-cover--speelt", "km-cover--film", "km-cover--snel",
                     "attempt.catch(fade)", "playbackRate", "}, 800);", 'film.addEventListener("waiting"', '"--km-bar"',
                     '"--km-fit"', '"--km-van"', "matrix3d(", '"--km-cut"', 'sessionStorage.removeItem("vierlief-open:" + location.pathname)'):
            self.assertIn(part, script)

    def test_timings_of_film_cover_and_card_fit_together(self):
        script, css, html = read("kerstmarkt.js"), read("style.css"), read("invitation.html")
        # Het filmpje is klaar als het openingsscherm vervaagt; dan begint ook de kop (fx-start), en een halve seconde
        # later verdwijnt het openingsscherm (data-duration).
        self.assertIn("var FADE_AT = 4550;", script)
        self.assertIn('data-duration="5050" data-fx-intro="4550"', html)
        self.assertIn("animation: km-out .45s ease var(--km-out, 4.55s) forwards;", css)
        # Alles van de kaartopening is klaar voordat effects.js de intro afrondt (fx-done na 4,2 s).
        for line in css.splitlines():
            if "fx-start:not(.fx-done)" in line and "animation:" in line:
                duration, delay = re.search(r"animation: [\w-]+ ([\d.]+)s [^;]*?([\d.]+)s", line).groups()
                self.assertLessEqual(float(duration) + float(delay), 4.2, line)
        for name, at, dur in re.findall(r"\.(km-write(?:--\d)?) \{ --km-at: ([\d.]+)s; --km-dur: ([\d.]+)s; \}", css):
            self.assertLessEqual(float(at) + float(dur), 4.2, name)
        self.assertEqual(len(re.findall(r"--km-at: ", css)), 3)

    def test_card_starts_on_the_card_from_the_film(self):
        css, script = read("style.css"), read("kerstmarkt.js")
        # De kaart heeft de verhouding van de kaart in het filmpje (3 bij 5), en draait om zijn linkerbovenhoek.
        self.assertIn("position: absolute; z-index: 1; left: 20%; top: 22.2%; width: 60%; aspect-ratio: 3 / 5;", css)
        self.assertIn("container-type: inline-size; transform-origin: 0 0;", css)
        # De vier hoeken van de kaart in het laatste filmbeeld (720 × 1280), en een benadering zonder script.
        corners = json.loads(re.search(r"var FILM_CARD = (\[.*?\]);", script).group(1))
        self.assertEqual(len(corners), 4)
        for x, y in corners:
            self.assertTrue(0 < x < 720 and 0 < y < 1280)
        self.assertIn("transform: var(--km-van, translate(37.3%, 17.9%) scale(.559));", css)
        # Opening en kop gebruiken hetzelfde beeldvak, en rekenen met dezelfde schermhoogte.
        same = "height: calc(100vh - var(--km-bar, 0px)); height: max(calc(100svh - var(--km-bar, 0px)), 600px);"
        self.assertIn(".km-cover > .km-backdrop, .km-cover > .km-stage { top: var(--km-bar, 0px); " + same, css)
        self.assertIn(".km-hero { position: relative; " + same, css)
        self.assertIn("width: max(100cqw, 56.25cqh); height: max(100cqh, 177.78cqw);", css)
        self.assertEqual(read("invitation.html").count('<div class="km-frame"'), 2)

    def test_motion_follows_the_house_rules(self):
        css, html = read("style.css"), read("invitation.html")
        # Zonder JavaScript geen openingsscherm (invite-base.css), ook niet door de eigen opmaak.
        self.assertIn(".js .km-cover { display: block;", css)
        self.assertNotRegex(css, r"(?m)^\.km-cover \{[^}]*display")
        # Zonder filmpje een lichtstreep en een overvloeier; die is de standaard, het filmpje een verbetering.
        self.assertIn(".is-opening .km-cover:not(.km-cover--speelt) .km-frame__end { animation: km-in", css)
        # De deurtjes bestaan alleen in beweging: zonder beweging (of zonder script) staat de kaart meteen open.
        self.assertIn(".km-doors { display: none;", css)
        self.assertIn(".fx-motion:is(.has-cover, .is-opening, .fx-start:not(.fx-done)) .km-doors { display: block; }", css)
        # Alles wat doorloopt staat onder .fx-motion en luistert naar de knop Beweging.
        for line in css.splitlines():
            if "infinite" in line and "animation:" in line:
                self.assertTrue(line.startswith(".fx-motion"), line)
                self.assertIn("var(--fx-play, running)", line, line)
        # Deeltjes achter de tekst: het sterrenstof staat in het beeld vóór de kaart (dus erachter).
        frame = html.split('<div class="km-frame" data-km-frame>', 1)[1]
        self.assertLess(frame.index('class="km-dust"'), frame.index('class="km-card"'))
        self.assertLess(frame.index('data-fx-slot="hero"'), frame.index('class="km-card"'))
        # Geen flitsen: de ster licht één keer zacht op.
        self.assertNotIn("flash", css)

    def test_greeting_without_dinner(self):
        content = greeting_only(demo_content("kerstmarkt", "kerst"))
        v, html = self.render(content=content, now=datetime(2026, 10, 15, 12, tzinfo=AMS))
        self.assertFalse(v["has_event"])
        self.assertIn("Fijne", html)
        self.assertIn("Aftellen naar kerst", html)
        for absent in ("Jouw kaartje", "Kom je ook?", "Hier vind je ons"):
            self.assertNotIn(absent, html)

    def test_own_headline_replaces_the_greeting(self):
        _, html = self.render(headline="Prettige feestdagen")
        self.assertIn('<p class="km-greet km-greet--own"><span class="km-write">Prettige feestdagen</span></p>', html)
        self.assertNotIn("en een gelukkig nieuwjaar</span>", html.split('class="km-body"', 1)[0])

    def test_long_sender_gets_smaller_letters(self):
        content = demo_content("kerstmarkt", "kerst")
        content["names"]["family"] = "Familie Van den Heuvel-Oosterbroek"
        v, html = self.render(content=content)
        self.assertEqual(v["names_size"], "xlong")
        self.assertIn("km-names--xlong", html)
        self.assertIn("van Familie Van den Heuvel-Oosterbroek", html)
        self.assertIn('<p class="km-end__from">Familie Van den Heuvel-Oosterbroek</p>', html)

    def test_preview_without_sender_has_no_loose_van(self):
        # Bij het samenstellen, voordat de afzender is ingevuld: geen "van Kerst" op het kaartje.
        content = demo_content("kerstmarkt", "kerst")
        content["names"] = {"family": "", "members": ""}
        _, html = self.render(content=content)
        self.assertNotIn("van Kerst", html)
        self.assertNotIn('class="km-ticket__from"', html)

    def test_closing_with_star_market_and_replay(self):
        _, html = self.render()
        end = html.split('class="km-sec km-end"', 1)[1]
        for part in ("km-end__star", "Fijne kerstdagen", "en een gelukkig nieuwjaar", "Familie Van Dijk", "img/slot.webp",
                     "km-market__lights"):
            self.assertIn(part, end)
        # De knop voor de opening werkt alleen met JavaScript (het script haalt 'hidden' weg) en alleen met een opening.
        self.assertIn('<p class="km-again" data-km-again hidden>', end)
        _, without = self.render(opening=False)
        self.assertNotIn("data-km-again", without)
        self.assertNotIn("km-cover", without)

    def test_other_occasions_keep_working(self):
        # In Beheer kan het ontwerp ook voor een andere gelegenheid worden aangezet, bijvoorbeeld een winterbruiloft.
        v, html = self.render(occasion="bruiloft")
        self.assertIn("Een uitnodiging voor jou", html)
        self.assertIn("Open de uitnodiging", html)
        self.assertIn('<span class="km-names__amp" aria-label="en">&amp;</span>', html)
        self.assertIn(v["tagline"], html)
        self.assertNotIn("Fijne kerstdagen", html)
        self.assertNotIn("Een kerstgroet", html)
        self.assertIsNone(re.search(r"Digitale kerstkaart", html))

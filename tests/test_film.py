"""Opening als film (Rozenboog): manifest, bestanden, weergave, contrast en het gedrag in de scripts.

Het afspelen zelf (tik, film, vervagen, 'Overslaan', 'Beweging', 'minder beweging', een film die niet laadt,
zonder JavaScript) is in een browser gecontroleerd; zie docs/CONTROLES.md onder "Ronde 8".
Rozenboog staat verborgen voor klanten (manifest: "hidden") tot de rechten op de film zijn bevestigd; de
testklassen zetten het ontwerp daarom eerst zichtbaar, behalve de test die juist de verborgen stand controleert.
"""
import copy
import json
import re
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client, TestCase
from PIL import Image

from catalog.atelier import contrast
from catalog.models import Template
from catalog.seed import DesignError, film_errors, validate_manifest
from invitations.demo import demo_content
from invitations.render import RenderOptions, build_view
from invitations.models import GuestResponse
from .helpers import VaylideTestCase

STATIC_JS = Path(settings.BASE_DIR) / "invitations" / "static" / "invitations"
ARCH = Path(settings.BASE_DIR) / "designs" / "rozenboog" / "v1"


def manifest():
    return json.loads((ARCH / "manifest.json").read_text(encoding="utf-8"))


def render_arch(content=None, occasion="bruiloft"):
    version = Template.objects.get(slug="rozenboog").current_version
    content = content or demo_content("rozenboog", occasion)
    view = build_view(occasion=occasion, content=content, overrides={}, template_version=version, options=RenderOptions(mode="demo"))
    return view, render_to_string(version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})


class VisibleDesignTestCase(TestCase):
    def setUp(self):
        Template.objects.filter(slug="rozenboog").update(is_active=True)


class HiddenUntilRightsTests(TestCase):
    def test_new_design_is_hidden_for_customers(self):
        template = Template.objects.get(slug="rozenboog")
        self.assertTrue(manifest().get("hidden"))
        self.assertFalse(template.is_active)
        self.assertEqual(Client().get("/voorbeeld/rozenboog/").status_code, 404)
        self.assertEqual(Client().get("/ontwerpen/rozenboog/").status_code, 404)
        self.assertNotContains(Client().get("/ontwerpen/"), "rozenboog")
        # Andere ontwerpen blijven gewoon zichtbaar.
        self.assertTrue(Template.objects.get(slug="rozentuin").is_active)
        self.assertEqual(Client().get("/voorbeeld/rozentuin/").status_code, 200)

    def test_hidden_design_cannot_be_ordered(self):
        from invitations.models import Invitation
        before = Invitation.objects.count()
        response = Client().post("/maken/", {"occasion": "bruiloft", "template": "rozenboog"})
        self.assertEqual(response.status_code, 200)  # formulier opnieuw, met een foutmelding
        self.assertEqual(Invitation.objects.count(), before)
        self.assertNotContains(Client().get("/maken/?gelegenheid=bruiloft"), "Rozenboog")

    def test_owner_can_make_it_visible(self):
        Template.objects.filter(slug="rozenboog").update(is_active=True)
        self.assertEqual(Client().get("/voorbeeld/rozenboog/").status_code, 200)


class FilmManifestTests(TestCase):
    def test_film_files_exist_and_fit_the_same_frame(self):
        data = manifest()
        self.assertEqual(film_errors(ARCH, data["film"]), [])
        # Poster (eerste beeld) en eindbeeld (laatste beeld) hebben de maat van de film.
        for key in ("poster", "end"):
            with Image.open(ARCH / data["film"][key]) as image:
                self.assertEqual(image.size, (720, 1280), key)
        # Licht genoeg voor een telefoon.
        self.assertLess((ARCH / data["film"]["src"]).stat().st_size, 3 * 1024 * 1024)
        self.assertLess((ARCH / data["film"]["webm"]).stat().st_size, 3 * 1024 * 1024)

    def test_missing_or_misplaced_film_files_are_refused(self):
        path = ARCH / "manifest.json"
        for film, message in [
            (dict(manifest()["film"], src="ontbreekt.mp4"), "film.src: ontbreekt.mp4 ontbreekt"),
            (dict(manifest()["film"], poster="../liefde-op-papier/v1/manifest.json"), "film.poster moet een bestandsnaam"),
            (dict(manifest()["film"], src="opening.mov"), "film.src moet een bestandsnaam"),
            ({"src": "opening.mp4"}, "film.poster ontbreekt"),
            ("opening.mp4", "'film' moet een blok"),
        ]:
            with self.assertRaisesMessage(DesignError, message):
                validate_manifest(path, dict(manifest(), film=film))
        # WebM is optioneel.
        without_webm = dict(manifest()["film"])
        del without_webm["webm"]
        self.assertEqual(film_errors(ARCH, without_webm), [])

    def test_designs_without_film_are_unchanged(self):
        self.assertEqual(Template.objects.get(slug="liefde-op-papier").current_version.film, {})


class FilmScriptTests(TestCase):
    """De scripts horen bij de film te passen; het gedrag zelf is in de browser gecontroleerd."""

    def test_invite_script_plays_and_reveals(self):
        js = (STATIC_JS / "invite.js").read_text(encoding="utf-8")
        for needle in ("[data-cover-film]", "[data-film-target]", "invite:reveal", "[data-cover-skip]",
                       "film.NETWORK_NO_SOURCE", 'film.preload = "auto"', 'html.classList.contains("inv-embed")', "hashchange", "document.fonts.ready", "ResizeObserver", "is-aligned"):
            self.assertIn(needle, js)

    def test_effects_wait_for_the_film(self):
        js = (STATIC_JS / "effects.js").read_text(encoding="utf-8")
        self.assertIn('document.addEventListener("invite:reveal"', js)
        self.assertIn("if (event.detail && event.detail.film) return;", js)


class FilmDesignsTests(TestCase):
    """Alle ontwerpen met een film: bestanden in orde, beelden zo groot als de film, licht genoeg voor een telefoon."""

    def test_every_film_design(self):
        found = []
        for manifest_path in sorted((Path(settings.BASE_DIR) / "designs").glob("*/v*/manifest.json")):
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            if "film" not in data:
                continue
            folder = manifest_path.parent
            found.append(data["slug"])
            self.assertEqual(film_errors(folder, data["film"]), [], data["slug"])
            self.assertEqual(data.get("opening"), "film", data["slug"])
            for key in ("poster", "end"):
                with Image.open(folder / data["film"][key]) as image:
                    self.assertEqual(image.size, (720, 1280), (data["slug"], key))
            for key in ("src", "webm"):
                if key not in data["film"]:      # de WebM-reserve is optioneel (de vijf filmkaarten van docs/INTROKAARTEN.md hebben alleen een MP4)
                    continue
                self.assertLess((folder / data["film"][key]).stat().st_size, 3 * 1024 * 1024, (data["slug"], key))
        self.assertEqual(found, ["bloesemmeer", "bloesemwaaier", "gouden-poort", "kerstsprookje", "rozenboog", "zijden-gordijn"])


class RozenboogTests(VisibleDesignTestCase):
    def test_version_gives_static_paths(self):
        film = Template.objects.get(slug="rozenboog").current_version.film
        self.assertEqual(film, {"src": "designs/rozenboog/v1/opening.mp4", "webm": "designs/rozenboog/v1/opening.webm",
                                "poster": "designs/rozenboog/v1/rozen.webp", "end": "designs/rozenboog/v1/boog.webp"})

    def test_demo_page_has_the_film_opening(self):
        response = Client().get("/voorbeeld/rozenboog/")
        self.assertEqual(response.status_code, 200)
        html = response.content.decode()
        self.assertIn('<meta name="robots" content="noindex, nofollow, noarchive">', html)
        video = re.search(r"<video[^>]*data-cover-film[^>]*>", html).group(0)
        # preload="none": niets van de film ophalen tot invite.js het laden aanzet (niet bij 'minder beweging').
        for attribute in ("muted", "playsinline", 'preload="none"', 'aria-hidden="true"', 'tabindex="-1"',
                          'poster="/static/designs/rozenboog/v1/rozen.webp"'):
            self.assertIn(attribute, video)
        self.assertNotIn("autoplay", video)
        self.assertNotIn("controls", video)
        self.assertLess(html.index('src="/static/designs/rozenboog/v1/opening.mp4" type=\'video/mp4; codecs="avc1.64001F"\''),
                        html.index('src="/static/designs/rozenboog/v1/opening.webm" type=\'video/webm; codecs="vp9"\''))
        # De openknop is een zichtbare knop; de naam is de tekst die erop staat (label in naam).
        self.assertIn('<a href="#uitnodiging" class="rb-open fx-pulse" data-open data-fx-origin>Open de uitnodiging</a>', html)
        self.assertIn('<button type="button" class="rb-skip" data-cover-skip hidden>Overslaan</button>', html)
        self.assertIn("data-film-frame", html)
        self.assertIn('class="rb-frame rb-frame--hero" data-film-target style="background-image: url(\'/static/designs/rozenboog/v1/boog.webp\')"', html)
        self.assertIn("data-fx-reveal-origin", html)
        self.assertNotIn("{#", html)
        self.assertEqual(len(re.findall(r"<script>", html)), 1)

    def test_every_occasion_renders(self):
        for occasion in Template.objects.get(slug="rozenboog").occasions:
            response = Client().get("/voorbeeld/rozenboog/", {"gelegenheid": occasion})
            self.assertEqual(response.status_code, 200, occasion)
            self.assertContains(response, "rb-sky", msg_prefix=occasion)
            self.assertContains(response, "rb-card", msg_prefix=occasion)

    def test_without_opening_the_hero_still_shows(self):
        content = copy.deepcopy(demo_content("rozenboog", "bruiloft"))
        content["style"]["opening"] = False
        view, html = render_arch(content)
        self.assertFalse(view["opening_enabled"])
        self.assertNotIn("<video", html)
        self.assertNotIn("data-cover", html)
        self.assertIn("url('/static/designs/rozenboog/v1/boog.webp')", html)
        self.assertIn("Sanne", html)

    def test_long_texts_get_the_dense_variant(self):
        content = copy.deepcopy(demo_content("rozenboog", "bruiloft"))
        content["names"].update({"partner_1": "Anne-Wilhelmina Charlotte Maria van Oldenbarnevelt-Hoogeveen",
                                 "partner_2": "Maximiliaan Alexander Frederik de Vries van der Wetering"})
        content["venue_name"] = "Kasteel de Haar, de grote feestzaal in het koetshuis aan de achterzijde van het landgoed"
        view, html = render_arch(content)
        self.assertEqual(view["names_size"], "xlong")
        self.assertIn("rb-sky rb-sky--dense", html)
        self.assertIn("rb-card rb-card--dense", html)
        self.assertIn("rb-names rb-names--xlong", html)
        self.assertIn("rb-label__names rb-label__names--xlong", html)
        _, short = render_arch()
        self.assertNotIn("--dense", short)

    def test_card_only_with_something_to_show(self):
        content = copy.deepcopy(demo_content("rozenboog", "bruiloft"))
        content.update({"date": "", "start_time": "", "end_time": "", "venue_name": ""})
        _, html = render_arch(content)
        self.assertNotIn('class="rb-card', html)
        self.assertIn("rb-sky", html)

    def test_design_on_the_website(self):
        page = Client().get("/ontwerpen/rozenboog/")
        self.assertContains(page, "<dt>Opening</dt><dd>Rozen die opengaan naar een rozenboog (film)</dd>")
        self.assertContains(page, "Dwarrelende bloemblaadjes en bij het openen een regen van bloemblaadjes.")
        self.assertTrue((Path(settings.BASE_DIR) / "static" / "img" / "designs" / "rozenboog.webp").exists())

    def test_text_colors_have_enough_contrast(self):
        c = manifest()["palettes"][0]["vars"]
        css = (ARCH / "style.css").read_text(encoding="utf-8")
        # Onder de tekst ligt een sluier van 94% dekkend (--rb-veil) over het vervaagde eindbeeld. Op het donkerst
        # denkbare beeld eronder (#3C280A) wordt dat #E5D5BE; zo ligt de ondergrens voor de tekst.
        self.assertIn("--rb-veil: 240, 224, 205;", css)
        self.assertIn("background: rgba(var(--rb-veil), .94);", css)
        veil = "#E5D5BE"
        # Achter de namen in de lucht, op de echte beeldpunten gemeten (docs/CONTROLES.md, ronde 8): op zijn
        # donkerst #A69E9D (de berghelling, met de gloed erover), achter de kopregel #E3D1BA.
        pairs = [
            (c["--rb-ink"], veil), (c["--rb-muted"], veil), (c["--rb-accent"], veil),
            (c["--rb-ink"], c["--rb-paper"]), (c["--rb-muted"], c["--rb-paper"]), (c["--rb-accent"], c["--rb-paper"]),
            ("#FFFFFF", c["--rb-accent"]),
            (c["--rb-sky-ink"], "#A69E9D"), (c["--rb-sky-ink"], "#E3D1BA"), (c["--rb-sky-muted"], "#E3D1BA"),
        ]
        for fg, bg in pairs:
            self.assertGreaterEqual(contrast(fg, bg), 4.5, (fg, bg))
        # Het openingslabel is crème glas (voor 90% dekkend).
        self.assertIn("--rb-glass: rgba(255, 250, 242, .9);", css)
        glass = "#E6E1DA"
        for fg in (c["--rb-ink"], c["--rb-muted"], c["--rb-accent"]):
            self.assertGreaterEqual(contrast(fg, glass), 4.5, fg)

    def test_particles_stay_behind_the_text(self):
        css = (ARCH / "style.css").read_text(encoding="utf-8")
        self.assertIn("html.inv-rozenboog .fx-burst { z-index: 0; }", css)
        self.assertEqual(manifest()["effects"]["viering"], "blaadjes")
        # Witte blaadjes: een donkere --fx-bg, zodat effects.js ze niet grijs maakt.
        self.assertIn("--fx-bg: #3A2A20;", css)


class RozenboogLiveInvitationTests(VaylideTestCase):
    """Een echte (betaalde) uitnodiging in Rozenboog: personalisatie, aftelling, agenda, route en aanmelden werken."""

    def setUp(self):
        Template.objects.filter(slug="rozenboog").update(is_active=True)

    def test_published_invitation_works(self):
        invitation = self.published(template="rozenboog")
        page = Client().get(f"/u/{invitation.slug}/")
        self.assertEqual(page.status_code, 200)
        html = page.content.decode()
        self.assertIn("rb-hero", html)
        self.assertIn("data-cover-film", html)
        self.assertIn('class="cd', html)  # aftelling
        self.assertIn("Google Agenda", html)
        self.assertIn("Route plannen", html)
        self.assertIn('id="aanmelden"', html)
        self.assertIn('<meta name="robots" content="noindex, nofollow, noarchive">', html)
        # De voorbeeldstills (uit de film) staan alleen in het voorbeeld, niet in een echte uitnodiging.
        self.assertNotIn("rb-gallery__grid--stills", html)
        self.assertEqual(Client().get(f"/u/{invitation.slug}/agenda.ics").status_code, 200)

    def test_guest_can_answer(self):
        invitation = self.published(template="rozenboog")
        response = self.rsvp(Client(), invitation, name="Mila Test")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(GuestResponse.objects.filter(invitation=invitation).count(), 1)

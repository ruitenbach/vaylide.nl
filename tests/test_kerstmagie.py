"""Kerstmagie: winterkaart met een openingsfilm die pas na een tik in het midden start."""
import json
import re
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import Client, TestCase

from catalog.atelier import contrast
from catalog.effects import effect_summary, effects_errors
from catalog.models import Template

DESIGN = Path(settings.BASE_DIR) / "designs" / "kerstmagie" / "v1"
MEDIA = DESIGN / "media"


def manifest():
    return json.loads((DESIGN / "manifest.json").read_text(encoding="utf-8"))


class KerstmagieDesignTests(TestCase):
    def test_manifest_is_valid_and_registered(self):
        data = manifest()
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertEqual(data["effects"]["sfeer"], "sneeuw")
        self.assertGreaterEqual(len(data["palettes"]), 3)
        template = Template.objects.get(slug="kerstmagie")
        self.assertEqual(template.current_version.manifest["opening"], "film")
        self.assertIn("dwarrelende sneeuw", effect_summary(data["effects"]))

    def test_every_colour_variant_is_readable(self):
        for pal in manifest()["palettes"]:
            v = pal["vars"]
            for text in ("--kl-ink", "--kl-muted", "--kl-gold", "--kl-gold-2"):
                for background in ("--kl-bg", "--kl-bg-2"):
                    self.assertGreaterEqual(contrast(v[text], v[background]), 4.5, f"{pal['key']} {text} op {background}")
            # Tekst op de gouden knoppen (--inv-accent-contrast in style.css).
            self.assertGreaterEqual(contrast("#101826", v["--kl-gold"]), 4.5, pal["key"])

    def test_media_files_exist_and_stay_light(self):
        for name, limit in (("intro.mp4", 3_500_000), ("intro.webm", 3_500_000), ("poster.webp", 300_000), ("dorp.webp", 400_000),
                            ("trein.webp", 150_000), ("plein.webp", 150_000), ("sneeuwvlok.webp", 200_000)):
            path = MEDIA / name
            self.assertTrue(path.exists(), name)
            self.assertLess(path.stat().st_size, limit, name)
            self.assertTrue(finders.find(f"designs/kerstmagie/v1/media/{name}"), name)


class KerstmagieRenderTests(TestCase):
    def render(self, occasion):
        response = Client().get("/voorbeeld/kerstmagie/", {"gelegenheid": occasion})
        self.assertEqual(response.status_code, 200, occasion)
        return response.content.decode()

    def test_renders_for_every_occasion_with_the_film_cover(self):
        for occasion in manifest()["occasions"]:
            html = self.render(occasion)
            self.assertIn("data-kl-play", html, occasion)
            self.assertIn("kl-hero__img", html, occasion)
            self.assertIn("/static/designs/kerstmagie/v1/intro.js", html, occasion)
            self.assertIn('data-fx-sfeer="sneeuw"', html, occasion)
            # Geen inline scripts naast het vaste startscript (CSP).
            self.assertEqual(len(re.findall(r"<script>", html)), 1, occasion)

    def test_film_waits_for_a_tap(self):
        """Geen autoplay en nog geen bronbestand: intro.js laadt de film pas als het openingsscherm getoond wordt."""
        html = self.render("bruiloft")
        video = re.search(r"<video\b[^>]*>", html).group(0)
        self.assertNotIn("autoplay", video)
        self.assertNotIn(" src=", video)
        self.assertIn("muted", video)
        self.assertIn("playsinline", video)
        self.assertIn("data-src-mp4=", video)
        self.assertIn("data-src-webm=", video)
        # De tik start de film; het gewone openen (data-open) zit alleen op 'Overslaan' en op een verborgen knop.
        play = re.search(r"<button\b[^>]*data-kl-play[^>]*>", html).group(0)
        self.assertNotIn("data-open", play)
        self.assertEqual(len(re.findall(r"<button\b[^>]*data-open", html)), 2)

    def test_intro_script_falls_back_to_opening_the_card(self):
        script = (DESIGN / "intro.js").read_text(encoding="utf-8")
        for needle in ("ended", "error", "catch(open)", "invite:opening", "fx-paused", "prefers-reduced-motion"):
            self.assertIn(needle, script, needle)

    def test_cover_is_closed_for_other_designs(self):
        html = Client().get("/voorbeeld/avondgoud/").content.decode()
        self.assertNotIn("kerstmagie", html)

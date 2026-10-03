"""Midnight Émeraude: trouwontwerp met een filmische opening, gebouwd met GSAP (lokaal meegeleverd in static/vendor/gsap/)."""
import json
import os
import re

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import Client

from catalog.atelier import contrast
from catalog.models import Template
from core.csp import BOOT_SCRIPT

from .helpers import VaylideTestCase

ONTWERP = settings.BASE_DIR / "designs" / "midnight-emeraude" / "v1"


class MidnightEmeraudeTests(VaylideTestCase):
    def manifest(self):
        return json.loads((ONTWERP / "manifest.json").read_text(encoding="utf-8"))

    def test_is_een_trouwontwerp(self):
        template = Template.objects.get(slug="midnight-emeraude")
        self.assertEqual(template.occasions, ["bruiloft", "verloving"])
        self.assertTrue(template.special)   # sinds de collectie (catalog/collectie.py) een special

    def test_tekstkleuren_hebben_genoeg_contrast(self):
        for palette in self.manifest()["palettes"]:
            v = palette["vars"]
            for bg in (v["--me-papier"], v["--me-ivoor"], v["--me-ivoor-2"]):
                for ink in (v["--me-ink"], v["--me-muted"], v["--me-goud-ink"], v["--me-accent-tekst"]):
                    self.assertGreaterEqual(contrast(ink, bg), 4.5, f"{palette['key']}: {ink} op {bg}")
            self.assertGreaterEqual(contrast(v["--me-accent-ink"], v["--me-accent"]), 4.5, palette["key"])
            for bg in (v["--me-nacht"], v["--me-nacht-2"]):
                for ink in (v["--me-n-ink"], v["--me-n-muted"], v["--me-n-goud"]):
                    self.assertGreaterEqual(contrast(ink, bg), 4.5, f"{palette['key']} nacht: {ink} op {bg}")

    def test_geen_roze_of_roségoud_in_de_kleuren(self):
        """De kleurwereld is smaragd of middernacht met champagnegoud en ivoor: geen roze of roségoud in de paletten."""
        for palette in self.manifest()["palettes"]:
            for naam, kleur in palette["vars"].items():
                if not kleur.startswith("#") or len(kleur) != 7:
                    continue
                r, g, b = (int(kleur[i:i + 2], 16) for i in (1, 3, 5))
                self.assertFalse(r > g + 40 and r > b + 25 and b > g, f"{palette['key']} {naam} {kleur} is roze")

    def test_voorbeeld_heeft_envelop_scene_en_hoofdstukken(self):
        for palette in ("emeraude", "midnight"):
            response = Client().get("/voorbeeld/midnight-emeraude/", {"kleur": palette, "gelegenheid": "bruiloft"})
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'data-palette="{palette}"', response.content.decode())
        html = Client().get("/voorbeeld/midnight-emeraude/", {"gelegenheid": "bruiloft"}).content.decode()
        for fragment in (
            'class="vx vx--midnight-emeraude vx--trouw"',          # de nieuwe smaragdgroene envelop uit de collectie
            'href="#uitnodiging" class="vx-seal-hit" data-vx-open data-open data-fx-origin',
            'data-cover data-duration="5000"',
            "me-l--lucht", "me-l--wereld", "me-l--kristal", "me-l--voor-l", "me-l--voor-r",   # de lagen van de scène
            "img/wereld-donker.webp", "img/wereld-licht.webp", "img/ring.webp", "img/kristallen.webp", "img/stralen.webp",
            "me-open__v", "img/merk-v.webp", "me-ringw", "me-naam__in", "me-lint", "me-draad__pad", "me-venster", "me-prog__lijn", "me-slot__ring",
            "vendor/gsap/gsap.min.js", "vendor/gsap/ScrollTrigger.min.js", "vendor/gsap/MotionPathPlugin.min.js", "vendor/gsap/SplitText.min.js",
            "designs/midnight-emeraude/v1/midnight-emeraude.js", "Ben je erbij?",
        ):
            self.assertIn(fragment, html)
        self.assertNotIn("js/envelop-collectie.js", html, "de envelop wordt hier door GSAP bestuurd, niet door het collectie-script")
        self.assertEqual(html.count("<script>"), 1)
        self.assertIn(f"<script>{BOOT_SCRIPT}</script>", html)
        self.assertNotIn("<style", html)
        self.assertNotIn("#}", html)

    def test_gsap_wordt_alleen_door_dit_ontwerp_geladen(self):
        for slug in ("rose-royale", "golden-noel", "balzaal", "winterlicht"):
            response = Client().get(f"/voorbeeld/{slug}/")
            if response.status_code == 200:
                self.assertNotIn("vendor/gsap", response.content.decode(), slug)

    def test_gsap_bestanden_zijn_lokaal_aanwezig(self):
        for naam in ("gsap", "ScrollTrigger", "MotionPathPlugin", "SplitText"):
            self.assertTrue(finders.find(f"vendor/gsap/{naam}.min.js"), naam)
        readme = (settings.BASE_DIR / "static" / "vendor" / "gsap" / "README.md").read_text(encoding="utf-8")
        self.assertIn("3.15", readme)

    def test_rustige_eindstand_en_opruimen_staan_in_het_script(self):
        """Bij 'minder beweging' bouwt het script niets; alles zit in een context die kan worden teruggedraaid."""
        js = (ONTWERP / "midnight-emeraude.js").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: no-preference", js)
        self.assertIn("gsap.matchMedia", js)
        self.assertIn("gsap.context", js)
        self.assertIn(".revert()", js)
        self.assertIn("fx-paused", js)
        self.assertIn("addPause", js)        # één master-timeline met een wachtpunt op de tik
        self.assertIn("motionPath", js)
        self.assertIn("ScrollTrigger", js)
        self.assertIn("SplitText", js)
        # onzichtbaar opwarmen van de zwaarste momenten vóór de intro (voorkomt haperen bij het eerste tekenen), met een bijna-ondoorzichtig vlak
        self.assertIn("me:opwarmen-klaar", js)
        self.assertIn("me-warm", js)
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.me-warm \{[^}]*opacity: \.995")   # niet 1: een volledig ondoorzichtig vlak laat de browser de lagen eronder overslaan

    def test_stylesheet_heeft_geen_css_animaties_behalve_het_vangnet(self):
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        self.assertEqual(sorted(re.findall(r"@keyframes\s+([\w-]+)", css)), sorted(["me-vangnet", "me-open-weg"]))   # alleen vangnetten
        self.assertNotIn("transition:", css.replace("transition: none", ""))

    def test_alle_beelden_bestaan_en_zijn_licht(self):
        html = Client().get("/voorbeeld/midnight-emeraude/", {"gelegenheid": "bruiloft"}).content.decode()
        namen = set(re.findall(r"designs/midnight-emeraude/v1/img/([a-z-]+\.webp)", html))
        self.assertGreaterEqual(len(namen), 9)
        totaal = 0
        for naam in namen:
            pad = finders.find(f"designs{os.sep}midnight-emeraude/v1/img/{naam}")
            self.assertTrue(pad, naam)
            totaal += os.path.getsize(pad)
        self.assertLess(totaal, 1_000_000, "de beelden samen zijn te zwaar voor een telefoon")

"""Rosé Royale: trouwontwerp met de Rose Blush-envelop als opening en een rozentuin in de schemering."""
import json
import os

from django.conf import settings
from django.test import Client

from catalog.atelier import contrast
from catalog.models import Template
from core.csp import BOOT_SCRIPT

from .helpers import VaylideTestCase


class RoseRoyaleTests(VaylideTestCase):
    def manifest(self):
        return json.loads((settings.BASE_DIR / "designs" / "rose-royale" / "v1" / "manifest.json").read_text(encoding="utf-8"))

    def test_is_een_trouwontwerp(self):
        template = Template.objects.get(slug="rose-royale")
        self.assertEqual(template.occasions, ["bruiloft", "verloving"])
        self.assertFalse(template.special)

    def test_tekstkleuren_hebben_genoeg_contrast(self):
        for palette in self.manifest()["palettes"]:
            v = palette["vars"]
            for bg in (v["--rr-paper"], v["--rr-page"], v["--rr-page-2"]):
                for ink in (v["--rr-ink"], v["--rr-muted"], v["--rr-rose-ink"]):
                    self.assertGreaterEqual(contrast(ink, bg), 4.5, f"{palette['key']}: {ink} op {bg}")
            self.assertGreaterEqual(contrast(v["--rr-accent-ink"], v["--rr-accent"]), 4.5, palette["key"])
            for bg in (v["--rr-dusk"], v["--rr-dusk-2"]):
                for ink in (v["--rr-dusk-ink"], v["--rr-dusk-muted"], v["--rr-dusk-gold"]):
                    self.assertGreaterEqual(contrast(ink, bg), 4.5, f"{palette['key']} avond: {ink} op {bg}")
            self.assertGreaterEqual(contrast(v["--fx-shine"], v["--rr-paper"]), 3, palette["key"])

    def test_voorbeeld_heeft_envelop_scene_en_hoofdstukken(self):
        for palette in ("blush", "ivoor"):
            response = Client().get("/voorbeeld/rose-royale/", {"kleur": palette, "gelegenheid": "bruiloft"})
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'data-palette="{palette}"', response.content.decode())
        html = Client().get("/voorbeeld/rose-royale/", {"gelegenheid": "bruiloft"}).content.decode()
        for fragment in (
            'class="vx vx--rose-blush vx--trouw"',                # de Rose Blush-envelop uit de collectie
            'href="#uitnodiging" class="vx-seal-hit" data-vx-open data-open data-fx-origin',
            'data-cover data-duration="4600"',
            # de scène in lagen (beelden uit tools/rose_royale/maak_beelden.py), met het hartsculptuur als hero-object
            "rr-diepte--lucht", "rr-diepte--oranjerie", "rr-diepte--boog", "rr-diepte--voor",
            "img/oranjerie-donker.webp", "img/oranjerie-licht.webp", "img/boog.webp", "img/hart.webp", "img/stralen.webp",
            "img/voor-links.webp", "img/rozen-links.webp",
            "rr-lint", "rr-cartouche", "rr-medaillon", "rr-sec--avond", "rr-venster", "rr-programma__knop", "rr-slot",
            "designs/rose-royale/v1/rose-royale.js", "Ben je erbij?",
        ):
            self.assertIn(fragment, html)
        self.assertEqual(html.count("<script>"), 1)
        self.assertIn(f"<script>{BOOT_SCRIPT}</script>", html)
        self.assertNotIn("<style", html)
        self.assertNotIn("#}", html)

    def test_alle_beelden_bestaan_en_zijn_licht(self):
        """De pagina verwijst alleen naar beelden die er zijn, en de hele set blijft klein (snel laden op een telefoon)."""
        import re
        from django.contrib.staticfiles import finders
        html = Client().get("/voorbeeld/rose-royale/", {"gelegenheid": "bruiloft"}).content.decode()
        namen = set(re.findall(r"designs/rose-royale/v1/img/([a-z-]+\.webp)", html))
        self.assertGreaterEqual(len(namen), 10)
        totaal = 0
        for naam in namen:
            pad = finders.find(f"designs{os.sep}rose-royale/v1/img/{naam}")
            self.assertTrue(pad, naam)
            totaal += os.path.getsize(pad)
        self.assertLess(totaal, 1_000_000, "de beelden samen zijn te zwaar voor een telefoon")

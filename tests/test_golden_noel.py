"""Golden Noël: kerstspecial met de envelop uit de VAYLIDE Envelope Collection als opening."""
import json

from django.conf import settings
from django.test import Client

from catalog.atelier import contrast
from catalog.models import Template
from catalog.specials import special_addon
from core.csp import BOOT_SCRIPT

from .helpers import VaylideTestCase


class GoldenNoelTests(VaylideTestCase):
    def manifest(self):
        return json.loads((settings.BASE_DIR / "designs" / "golden-noel" / "v1" / "manifest.json").read_text(encoding="utf-8"))

    def test_is_een_kerstspecial_zonder_verzonnen_prijs(self):
        template = Template.objects.get(slug="golden-noel")
        self.assertTrue(template.special)
        self.assertEqual(template.occasions, ["kerst"])
        # Zonder meerprijs in Beheer → Prijzen is een special niet te bestellen: er staat bewust geen prijs klaar.
        self.assertIsNone(special_addon(template))

    def test_tekstkleuren_hebben_genoeg_contrast(self):
        for palette in self.manifest()["palettes"]:
            v = palette["vars"]
            for bg in (v["--gn-card"], v["--gn-card-2"]):
                for ink in (v["--gn-ink"], v["--gn-muted"], v["--gn-gold-ink"]):
                    self.assertGreaterEqual(contrast(ink, bg), 4.5, f"{palette['key']}: {ink} op {bg}")
            self.assertGreaterEqual(contrast(v["--gn-accent-ink"], v["--gn-accent"]), 4.5, palette["key"])
            self.assertGreaterEqual(contrast(v["--fx-shine"], v["--gn-card"]), 3, palette["key"])
            # Avondhoofdstukken: lichte tekst en goud op donker kaarslicht.
            for bg in (v["--gn-night"], v["--gn-night-2"]):
                for ink in (v["--gn-night-ink"], v["--gn-night-muted"], v["--gn-night-gold"]):
                    self.assertGreaterEqual(contrast(ink, bg), 4.5, f"{palette['key']} avond: {ink} op {bg}")

    def test_voorbeeld_heeft_envelop_en_kaart(self):
        for palette in ("ivoor", "champagne"):
            response = Client().get("/voorbeeld/golden-noel/", {"kleur": palette, "gelegenheid": "kerst"})
            self.assertEqual(response.status_code, 200)
            self.assertIn(f'data-palette="{palette}"', response.content.decode())
        html = Client().get("/voorbeeld/golden-noel/", {"gelegenheid": "kerst"}).content.decode()
        for fragment in (
            'class="vx vx--golden-noel vx--kerst"',              # de envelop uit de collectie
            'href="#uitnodiging" class="vx-seal-hit" data-vx-open data-open data-fx-origin',  # opent ook zonder JavaScript
            "vx-sealpart--top", "vx-flap__in", "img/envelop/voering-golden-noel.svg",
            "js/envelop-collectie.js", "css/envelop-collectie.css",
            'data-cover data-duration="4500"',
            "gn-boog", "gn-ballen", "gn-licht__kern", "gn-kaars", "gn-sec--avond", "gn-sec__top", "gn-hoek",
            "designs/golden-noel/v1/golden-noel.js", "Familie Van Dijk", "Fijne feestdagen", "Schuif je aan?",
        ):
            self.assertIn(fragment, html)
        self.assertEqual(html.count("<script>"), 1)
        self.assertIn(f"<script>{BOOT_SCRIPT}</script>", html)
        self.assertNotIn("<style", html)
        self.assertNotIn("#}", html)

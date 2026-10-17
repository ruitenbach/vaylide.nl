"""De vijf filmkaarten (Zijden gordijn, Bloesemmeer, Bloesemwaaier, Kerstsprookje, Gouden poort): een openingsfilm van de eigenaar, verborgen (groep C) tot de
rechten bevestigd zijn, Luxe, en alleen voor beheerders als voorbeeld te bekijken. Opbouw gelijk aan Rozenboog; gegenereerd door tools/introkaarten."""
import json
import re
from pathlib import Path

from django.conf import settings
from django.test import Client

from catalog import collectie, prijzen
from catalog.atelier import contrast
from catalog.effects import effects_errors
from catalog.models import Template
from catalog.occasions import OCCASIONS

from .helpers import VaylideTestCase

KAARTEN = {  # slug: gelegenheid van het voorbeeld
    "zijden-gordijn": "bruiloft", "bloesemmeer": "verjaardag", "bloesemwaaier": "bruiloft", "kerstsprookje": "kerst", "gouden-poort": "bruiloft",
}
MEDIA_LIMIETEN = {"opening.mp4": 3_500_000, "poster.webp": 300_000, "end.webp": 300_000, "band.webp": 150_000,
                  **{f"cut-{n}.webp": 120_000 for n in "abcd"}, **{f"gal-{n}.webp": 100_000 for n in "1234"}}


def ontwerp(slug) -> Path:
    return Path(settings.BASE_DIR) / "designs" / slug / "v1"


def manifest(slug) -> dict:
    return json.loads((ontwerp(slug) / "manifest.json").read_text(encoding="utf-8"))


class IntrokaartOntwerpTests(VaylideTestCase):
    def test_manifesten_zijn_geldig_en_de_kaarten_staan_verborgen_en_in_luxe(self):
        for slug in KAARTEN:
            data = manifest(slug)
            self.assertEqual(effects_errors(data["effects"]), [], slug)
            self.assertEqual(data["opening"], "film", slug)
            self.assertEqual(data["envelope_mode"], "built_in", slug)
            self.assertTrue(set(data["occasions"]) <= set(OCCASIONS), slug)
            self.assertFalse(data.get("special", False), slug)
            self.assertEqual(collectie.groep(slug), "C", f"{slug} is verborgen tot de rechten bevestigd zijn")
            self.assertEqual(prijzen.INDELING[slug], prijzen.LUXE, slug)
            template = Template.objects.get(slug=slug)
            self.assertFalse(template.is_active, slug)
            self.assertEqual(template.current_version.film["src"].rsplit("/", 1)[-1], "opening.mp4", slug)

    def test_de_kaarten_zijn_per_gelegenheid_te_koop_met_de_bestaande_luxe_prijs(self):
        # Geen nieuwe prijs: de Luxe-cel van de gelegenheid, en alleen voor de gelegenheden uit het manifest.
        for slug, gelegenheid in KAARTEN.items():
            info = prijzen.prijs_info(Template.objects.get(slug=slug), gelegenheid)
            self.assertEqual(info["tier"], prijzen.LUXE, slug)
            self.assertEqual(info["cents"], prijzen.PRIJZEN[prijzen.GELEGENHEID_RIJ[gelegenheid]][1], slug)
        self.assertIsNone(prijzen.prijs_info(Template.objects.get(slug="kerstsprookje"), "bruiloft"))

    def test_media_bestaat_en_is_licht_genoeg_voor_een_telefoon(self):
        for slug in KAARTEN:
            for naam, limiet in MEDIA_LIMIETEN.items():
                pad = ontwerp(slug) / naam
                self.assertTrue(pad.exists(), f"{slug}/{naam}")
                self.assertLess(pad.stat().st_size, limiet, f"{slug}/{naam}")
            kaartbeeld = Path(settings.BASE_DIR) / "static" / "img" / "designs" / f"{slug}.webp"
            self.assertTrue(kaartbeeld.exists(), slug)

    def test_de_film_heeft_geen_geluidsspoor(self):
        for slug in KAARTEN:
            self.assertIn(b"ftyp", (ontwerp(slug) / "opening.mp4").read_bytes()[:64], slug)
            self.assertNotIn(b"soun", (ontwerp(slug) / "opening.mp4").read_bytes()[:200_000], f"{slug}: geen geluidsspoor")

    def test_alle_tekstkleuren_zijn_leesbaar(self):
        for slug in KAARTEN:
            v = manifest(slug)["palettes"][0]["vars"]
            for achtergrond in ("--fk-page", "--fk-paper", "--fk-paper-2"):
                for tekst in ("--fk-ink", "--fk-muted", "--fk-accent"):
                    self.assertGreaterEqual(contrast(v[tekst], v[achtergrond]), 4.5, f"{slug}: {tekst} op {achtergrond}")
            # Kleine gouden lijnen en cijfers van de datum op de sluier onder de film (groot, dus 3:1).
            self.assertGreaterEqual(contrast(v["--fk-gold-line"], v["--fk-paper"]), 3.0, f"{slug}: gouden lijn")
            # Tekst op de knop en op de kleine, getekende kleuren.
            self.assertGreaterEqual(contrast(v["--fk-accent-ink"], v["--fk-accent"]), 4.5, f"{slug}: knoptekst")
            self.assertGreaterEqual(contrast(v["--fk-field-ink"], v["--fk-field-bg"]), 7, f"{slug}: invulveld")
            # De namen in de lucht staan boven een zachte gloed.
            gloed = "#%02X%02X%02X" % tuple(int(n) for n in v["--fk-glow"].split(","))
            self.assertGreaterEqual(contrast(v["--fk-sky-ink"], gloed), 7, f"{slug}: namen op de gloed")
            self.assertGreaterEqual(contrast(v["--fk-sky-muted"], gloed), 4.5, f"{slug}: kleine kopregel op de gloed")


class IntrokaartWeergaveTests(VaylideTestCase):
    def setUp(self):
        self.staff = self.make_staff()
        self.klant = self.make_customer()

    def voorbeeld(self, slug, gebruiker=None):
        client = Client()
        if gebruiker is not None:
            client.force_login(gebruiker)
        return client.get(f"/voorbeeld/{slug}/", {"gelegenheid": KAARTEN[slug]})

    def test_verborgen_voor_bezoekers_en_klanten(self):
        for slug in KAARTEN:
            self.assertEqual(self.voorbeeld(slug).status_code, 404, slug)
            self.assertEqual(self.voorbeeld(slug, self.klant).status_code, 404, slug)

    def test_beheerders_zien_de_kaart_met_film_namen_en_de_gedeelde_onderdelen(self):
        for slug in KAARTEN:
            antwoord = self.voorbeeld(slug, self.staff)
            self.assertEqual(antwoord.status_code, 200, slug)
            html = antwoord.content.decode()
            for fragment in ("data-cover-film", "data-film-target", "fk-hero", "fk-sky", "fk-card", 'id="aanmelden"', "data-countdown"):
                self.assertIn(fragment, html, f"{slug}: {fragment}")
            self.assertRegex(html, r'<video[^>]*\bmuted\b[^>]*\bplaysinline\b', slug)
            self.assertNotRegex(html, r'<video[^>]*\bautoplay\b', slug)
            self.assertIn(f"inv-{slug}", html)
            paden = set(re.findall(r'(?:src|srcset|href|poster)="/static/([^"\s]+)"', html))
            for pad in paden:
                if pad.startswith(f"designs/{slug}/"):
                    self.assertTrue((Path(settings.BASE_DIR) / pad).exists(), pad)

    def test_geen_inline_script_of_style_blokken_csp(self):
        for slug in KAARTEN:
            html = self.voorbeeld(slug, self.staff).content.decode()
            self.assertFalse(re.search(r"<style[\s>]", html), slug)
            inline = [m for m in re.findall(r"<script([^>]*)>", html) if "src=" not in m]
            self.assertLessEqual(len(inline), 1, slug)

    def test_de_kop_toont_het_laatste_beeld_van_de_film(self):
        for slug in KAARTEN:
            data = manifest(slug)
            self.assertEqual(data["film"]["end"], "end.webp", slug)
            html = self.voorbeeld(slug, self.staff).content.decode()
            self.assertIn("end.webp", html, slug)

    def test_de_stijl_gebruikt_alleen_eigen_kleuren_uit_het_manifest(self):
        for slug in KAARTEN:
            css = (ontwerp(slug) / "style.css").read_text(encoding="utf-8")
            gebruikt = set(re.findall(r"var\((--fk-[a-z0-9-]+)", css))
            beschikbaar = set(manifest(slug)["palettes"][0]["vars"]) | {"--fk-surround", "--fk-grain", "--fk-glass", "--fk-sky-l", "--fk-sky-r", "--fk-sky-t", "--fk-sky-h"}
            self.assertEqual(gebruikt - beschikbaar, set(), slug)
            self.assertNotRegex(css, r"__[A-Z]+__", slug)

"""Moments, stap 2: de demonstratie van de gastpagina. Achter de vlag, alleen in testmodus, zonder formulier of opslag."""
import re
from pathlib import Path

from django.conf import settings
from django.test import TestCase, override_settings
from django.utils import translation

from moments import limits
from moments.demo import demo_event

URL = "/moments/demo/"
AAN = dict(MOMENTS_ENABLED=True, TEST_MODE=True)


class ToegangTests(TestCase):
    def test_standaard_niet_bereikbaar(self):
        self.assertEqual(self.client.get(URL, secure=True).status_code, 404)

    def test_vlag_aan_maar_live_modus_blijft_dicht(self):
        with override_settings(MOMENTS_ENABLED=True, TEST_MODE=False):
            self.assertEqual(self.client.get(URL, secure=True).status_code, 404)

    def test_testmodus_zonder_vlag_blijft_dicht(self):
        with override_settings(MOMENTS_ENABLED=False, TEST_MODE=True):
            self.assertEqual(self.client.get(URL, secure=True).status_code, 404)

    def test_alleen_lezen(self):
        with override_settings(**AAN):
            self.assertEqual(self.client.post(URL, secure=True).status_code, 405)

    def test_andere_adressen_bestaan_niet(self):
        with override_settings(**AAN):
            for pad in ("/moments/", "/moments/abc/", "/moments/demo/upload/"):
                self.assertEqual(self.client.get(pad, secure=True).status_code, 404, pad)


@override_settings(**AAN)
class PaginaTests(TestCase):
    def setUp(self):
        self.response = self.client.get(URL, secure=True)
        self.html = self.response.content.decode()

    def test_inhoud(self):
        self.assertEqual(self.response.status_code, 200)
        for tekst in ("Anna &amp; Bram", "Maak een foto", "Uit galerij", "Twee korte videoboodschappen", "Optioneel",
                      "Welke wens heb je voor Anna en Bram?", "Wat is jouw mooiste herinnering", "alleen jij ziet wat je zelf deelt",
                      "Demonstratie", "Video 1 van 2 · Een wens", "Video 2 van 2 · Een herinnering"):
            self.assertIn(tekst, self.html)
        self.assertIn("0 van 15", self.html)
        self.assertIn("Hooguit 30 seconden", self.html)
        self.assertNotIn("Kasteel", self.html)       # geen verzonnen locatie
        self.assertNotIn("Hun verhaal", self.html)   # besluit 25 oktober: niet toevoegen
        self.assertLessEqual(self.html.count("mm-thumb--example"), 3)   # hoogstens drie voorbeeldplaatsen

    def test_geen_zoekmachines_geen_opslag_in_cache(self):
        self.assertIn("noindex", self.html)
        self.assertIn("noindex", self.response["X-Robots-Tag"])
        self.assertEqual(self.response["Referrer-Policy"], "no-referrer")
        self.assertIn("no-store", self.response["Cache-Control"])

    def test_geen_formulier_en_geen_verzending(self):
        self.assertNotIn("<form", self.html)
        self.assertNotRegex(self.html, r'action="')
        self.assertNotIn("csrf", self.html.lower())

    def test_strenge_csp_geen_inline_code(self):
        csp = self.response["Content-Security-Policy"]
        self.assertIn("style-src 'self'", csp)
        self.assertNotIn("<style", self.html)
        scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", self.html, flags=re.S)
        self.assertEqual(scripts, ['document.documentElement.classList.add("js");'])
        self.assertNotRegex(self.html, r"\son(click|change|load)=")

    def test_toegankelijk_opgebouwd(self):
        self.assertIn('<html lang="nl"', self.html)
        self.assertEqual(self.html.count("<h1"), 1)
        self.assertIn('class="skip-link"', self.html)
        self.assertIn('role="status"', self.html)
        # elke bestandskeuze heeft een label dat ernaar verwijst
        for ident in re.findall(r'<input class="mm-file" id="([^"]+)"', self.html):
            self.assertIn(f'for="{ident}"', self.html, ident)
        self.assertEqual(len(re.findall(r'type="file"', self.html)), 6)

    def test_camera_en_galerij_zijn_te_kiezen(self):
        self.assertIn('accept="image/*" capture="environment"', self.html)
        self.assertRegex(self.html, r'accept="image/\*" multiple')
        self.assertIn('accept="video/*" capture="user"', self.html)

    def test_gebruikt_het_logo_ongewijzigd_en_geen_externe_bronnen(self):
        self.assertIn("vaylide-logo.webp", self.html)
        self.assertNotRegex(self.html, r'(src|href)="https?://')

    def test_stijl_licht_en_zonder_vaste_balk(self):
        css = (Path(settings.BASE_DIR) / "moments" / "static" / "moments" / "moments.css").read_text()
        self.assertNotRegex(css, r"position:\s*(fixed|sticky)")      # geen vaste uploadbalk, geen vaste zijkolom
        self.assertNotIn("Pinyon", css)                              # twee lettertypes: Playfair Display en DM Sans
        self.assertNotIn("outline-offset: 6px", css)                 # geen dubbele gouden kaders
        self.assertEqual(len(demo_event()["examples"]), 3)

    def test_geen_externe_of_vrije_afbeeldingen_in_de_demo(self):
        self.assertEqual(re.findall(r'<img[^>]*src="([^"]+)"', self.html), ["/static/img/merk/vaylide-logo.webp"])  # alleen het logo; fotoplaatsen zijn vlakken


@override_settings(**AAN)
class VertalingTests(TestCase):
    def test_taal_komt_in_de_pagina(self):
        with translation.override("id"):
            html = self.client.get(URL, secure=True).content.decode()
        self.assertIn('<html lang="id"', html)

    def test_alle_teksten_voor_javascript_staan_als_data(self):
        html = self.client.get(URL, secure=True).content.decode()
        js = (Path(settings.BASE_DIR) / "moments" / "static" / "moments" / "moments.js").read_text()
        for naam in set(re.findall(r"\bd\.(txt\w+)", js)):
            kebab = re.sub(r"([A-Z])", lambda m: "-" + m.group(1).lower(), naam)
            self.assertIn(f"data-{kebab}=", html, naam)

    def test_pakketwaarden_komen_uit_de_configuratie(self):
        event = demo_event("signature")
        self.assertEqual((event["photos_max"], event["video_seconds"]), (25, 60))
        self.assertEqual(limits.PACKAGES["classic"]["photos_per_guest"], 15)
        self.assertEqual(limits.PACKAGES["classic"]["video_seconds"], 30)


class Stap1BlijftIntactTests(TestCase):
    def test_enige_route_is_de_demonstratie(self):
        from django.urls import get_resolver

        moments = [p for p in get_resolver().url_patterns if "moments" in p.pattern.regex.pattern]
        self.assertEqual(len(moments), 1)
        namen = [u.name for u in moments[0].url_patterns]
        self.assertEqual(namen, ["demo_guest"])

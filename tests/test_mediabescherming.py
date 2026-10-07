"""Bescherming van eigen media: hotlinken, losse beschermscript en videokenmerken.

Dit test wat technisch haalbaar is: geen insluiting op een andere website, geen downloadknop, geen link naar masterbestanden.
Kopiëren door een bezoeker zelf (netwerkverkeer, schermopname) kan niet worden voorkomen en wordt hier ook niet beweerd.
"""
import re
from pathlib import Path

from django.conf import settings
from django.test import Client, override_settings

from .helpers import VaylideTestCase

BEELD = "/static/img/designs/kerstkaart.webp"
VIDEO = "/static/designs/kerstkaart/v1/media/opening.mp4"
BUITEN_SCHOT = ("/static/img/merk/vaylide-logo.png", "/static/img/mail/feest-achtergrond.jpg", "/static/img/og-vaylide.jpg", "/static/js/site.js")


class HotlinkTests(VaylideTestCase):
    def test_vreemde_referer_krijgt_403_op_beeld_en_video(self):
        for pad in (BEELD, VIDEO, "/static/img/site/tegel-kerst.webp", "/static/img/demo/rozen.webp"):
            response = Client().get(pad, HTTP_REFERER="https://een-andere-site.example/pagina")
            self.assertEqual(response.status_code, 403, pad)
            self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_onderdrukte_referer_maar_cross_site_ingesloten_beeld_krijgt_403(self):
        for dest in ("image", "video", "iframe"):
            response = Client().get(BEELD, HTTP_SEC_FETCH_SITE="cross-site", HTTP_SEC_FETCH_DEST=dest)
            self.assertEqual(response.status_code, 403, dest)

    def test_eigen_pagina_zonder_referer_en_deelkaarten_blijven_werken(self):
        for extra in ({}, {"HTTP_REFERER": "http://testserver/ontwerpen/"}, {"HTTP_REFERER": f"{settings.BASE_URL}/"},
                      {"HTTP_REFERER": "http://localhost:8000/ontwerpen/"}, {"HTTP_REFERER": "http://127.0.0.1:8000/"},
                      {"HTTP_SEC_FETCH_SITE": "same-origin", "HTTP_SEC_FETCH_DEST": "image"},
                      {"HTTP_SEC_FETCH_SITE": "cross-site", "HTTP_SEC_FETCH_DEST": "document"},   # iemand opent het beeld via een link
                      {"HTTP_SEC_FETCH_SITE": "none", "HTTP_SEC_FETCH_DEST": "document"}):
            for pad in (BEELD, VIDEO):
                self.assertNotEqual(Client().get(pad, **extra).status_code, 403, (pad, extra))

    def test_logo_mailafbeeldingen_en_deelbeeld_zijn_niet_afgeschermd(self):
        for pad in BUITEN_SCHOT:
            self.assertNotEqual(Client().get(pad, HTTP_REFERER="https://outlook.live.com/").status_code, 403, pad)

    def test_andere_paden_dan_media_worden_niet_geraakt(self):
        for pad in ("/", "/ontwerpen/", "/static/designs/kerstkaart/v1/style.css"):
            self.assertNotEqual(Client().get(pad, HTTP_REFERER="https://een-andere-site.example/").status_code, 403, pad)

    @override_settings(ALLOWED_HOSTS=["vaylide.nl", "www.vaylide.nl", "testserver"], BASE_URL="https://vaylide.nl")
    def test_ook_het_adres_met_en_zonder_www_telt_als_eigen(self):
        for referer in ("https://vaylide.nl/", "https://www.vaylide.nl/ontwerpen/kerstkaart/"):
            self.assertNotEqual(Client().get(BEELD, HTTP_REFERER=referer).status_code, 403, referer)
        self.assertEqual(Client().get(BEELD, HTTP_REFERER="https://vaylide.nl.nep-site.example/").status_code, 403)

    def test_toegestaan_verzoek_krijgt_cross_origin_resource_policy_als_het_bestand_er_is(self):
        response = Client().get(BEELD)
        if response.status_code < 400:
            self.assertEqual(response.headers.get("Cross-Origin-Resource-Policy"), "same-site")


class PaginaTests(VaylideTestCase):
    SCRIPT = "js/media-bescherming"

    def test_script_staat_op_site_en_uitnodigingen(self):
        for pad in ("/", "/ontwerpen/", "/ontwerpen/kerstkaart/", "/voorbeeld/kerstkaart/?gelegenheid=kerst", "/voorbeeld/gouden-avond/", "/voorbeeld/kerstbol/?gelegenheid=kerst", "/voorbeeld/kerststad/?gelegenheid=kerst"):
            html = Client().get(pad).content.decode()
            self.assertIn(self.SCRIPT, html, pad)

    def test_script_blijft_klein_en_blokkeert_geen_tekstselectie(self):
        js = (Path(settings.BASE_DIR) / "static/js/media-bescherming.js").read_text(encoding="utf-8")
        self.assertIn("contextmenu", js)
        self.assertIn("dragstart", js)
        code = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
        for verboden in ("selectstart", "copy", "cut", "keydown", "keyup", "devtools", "beforeprint"):
            self.assertNotIn(verboden, code, verboden)

    def test_elke_video_zonder_downloadknop_en_zonder_eigen_bediening(self):
        gevonden = 0
        for pad in ("/voorbeeld/kerstkaart/?gelegenheid=kerst", "/voorbeeld/kerstbol/?gelegenheid=kerst", "/voorbeeld/kerststad/?gelegenheid=kerst", "/voorbeeld/gouden-avond/"):
            html = Client().get(pad).content.decode()
            for tag in re.findall(r"<video\b[^>]*>", html):
                gevonden += 1
                self.assertIn('controlslist="nodownload', tag, pad)
                self.assertIn("disablepictureinpicture", tag, pad)
                self.assertNotRegex(tag, r"\scontrols\b", pad)
        self.assertGreaterEqual(gevonden, 4)

    def test_geen_template_linkt_naar_een_beeld_of_video_om_te_downloaden(self):
        patroon = re.compile(r"<a\b[^>]*href=\"[^\"]*(?:\.(?:webp|jpe?g|png|mp4|webm)\b|\{% static [^%]*(?:media|img/designs)[^%]*%\})[^\"]*\"", re.I)
        for sjabloon in Path(settings.BASE_DIR).glob("**/*.html"):
            if any(deel in sjabloon.parts for deel in ("staticfiles", "node_modules", ".venv", "voorvertoning-hero")):
                continue
            tekst = sjabloon.read_text(encoding="utf-8", errors="ignore")
            self.assertIsNone(patroon.search(tekst), sjabloon)
            self.assertNotRegex(tekst, r"<(?:img|video|source)\b[^>]*\bdownload\b", str(sjabloon))

"""Strandboog (special): een ringdoosje dat opengaat op een filmscène (bloemenboog aan zee, bloemenmeisje, duiven); daarna de namen, de datum en de gewone uitnodiging
met aftellen, programma, locatie en aanmelden. De bestaande Gouden Avond en Balzaal blijven ongewijzigd."""
import json
import re

from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client

from catalog.atelier import contrast
from catalog.effects import effects_errors
from catalog.models import Template
from catalog.specials import special_addon
from invitations.demo import demo_content
from invitations.render import RenderOptions, build_view

from .helpers import VaylideTestCase

ONTWERP = settings.BASE_DIR / "designs" / "strandboog" / "v1"
DEMO = "/voorbeeld/strandboog/?gelegenheid=bruiloft"


def _render(content):
    version = Template.objects.get(slug="strandboog").current_version
    view = build_view(occasion="bruiloft", content=content, overrides={}, template_version=version, options=RenderOptions(mode="demo"))
    return render_to_string(version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})


class StrandboogOntwerpTests(VaylideTestCase):
    def manifest(self):
        return json.loads((ONTWERP / "manifest.json").read_text(encoding="utf-8"))

    def test_is_een_zelfstandige_special_en_zonder_prijs_niet_te_bestellen(self):
        template = Template.objects.get(slug="strandboog")
        self.assertTrue(template.special)
        self.assertIsNone(special_addon(template), "zonder meerprijs is een special niet te bestellen (er komt nooit een verzonnen prijs)")
        self.assertEqual(template.occasions, ["bruiloft", "verloving"])
        for ander in ("gouden-avond", "balzaal"):
            self.assertNotEqual(template.pk, Template.objects.get(slug=ander).pk)

    def test_staat_onder_specials_en_niet_tussen_de_gewone_kaarten(self):
        pagina = Client().get("/ontwerpen/").content.decode()
        speciaal = pagina[pagina.index("Specials"):] if "Specials" in pagina else ""
        self.assertIn("/ontwerpen/strandboog/", speciaal)
        gewoon = pagina[:pagina.index("Specials")] if "Specials" in pagina else pagina
        self.assertNotIn("/ontwerpen/strandboog/", gewoon)
        self.assertEqual(Client().get("/ontwerpen/strandboog/").status_code, 200)

    def test_manifest_effecten_en_tekstkleuren(self):
        data = self.manifest()
        self.assertEqual(effects_errors(data["effects"]), [])
        for palet in data["palettes"]:
            v = palet["vars"]
            for bg in (v["--sb-bg"], v["--sb-bg-2"]):
                for ink in (v["--sb-ink"], v["--sb-muted"], v["--sb-accent"], v["--sb-gold-2"]):
                    self.assertGreaterEqual(contrast(ink, bg), 4.5, f"{palet['key']}: {ink} op {bg}")
            self.assertGreaterEqual(contrast(v["--sb-accent-ink"], v["--sb-accent"]), 4.5)
            # de donkere avondbanden met licht ivoor en goud
            for tekst in ("#FBF1DE", "#E7DAC2", "#F2D79E"):
                for avond in (v["--sb-avond"], v["--sb-avond-2"]):
                    self.assertGreaterEqual(contrast(tekst, avond), 7, f"{tekst} op {avond}")
            # de perzikkleurige aftelband met donkere tekst
            for perzik in ("#FCE7C4", "#F3C58C", "#F8DDB0"):
                self.assertGreaterEqual(contrast("#3A2410", perzik), 7, f"#3A2410 op {perzik}")
                self.assertGreaterEqual(contrast("#4A2E10", perzik), 7, f"#4A2E10 op {perzik}")

    def test_media_bestaat_en_is_licht_genoeg_voor_een_telefoon(self):
        media = ONTWERP / "media"
        for naam in ("strandboog.mp4", "poster.jpg", "poster-eind.jpg", "zee.webp", "duif.webp", "bloemen.webp"):
            self.assertTrue((media / naam).exists(), naam)
        self.assertLess((media / "strandboog.mp4").stat().st_size, 3_000_000, "de webversie (720x1280, 18 s, zonder geluid) hoort rond 2 MB te zijn")
        for naam in ("poster.jpg", "poster-eind.jpg"):
            self.assertLess((media / naam).stat().st_size, 200_000, naam)
        for naam in ("zee.webp", "duif.webp", "bloemen.webp"):
            self.assertLess((media / naam).stat().st_size, 100_000, naam)

    def test_geen_woord_van_het_oude_merk_in_de_beelden_alleen_de_v(self):
        # De film is bewerkt: van "VAVLUE" staat alleen de V nog in beeld (zie docs/STRANDBOOG.md). Het script en de tekst noemen geen ander merk.
        bron = (ONTWERP / "invitation.html").read_text(encoding="utf-8") + (ONTWERP / "strandboog.js").read_text(encoding="utf-8")
        self.assertNotRegex(bron, r"(?i)value|vavlue")


class StrandboogWeergaveTests(VaylideTestCase):
    def test_demo_toont_doosje_overslaan_film_en_de_gedeelde_onderdelen(self):
        html = Client().get(DEMO).content.decode()
        for fragment in ("sb-hero", "data-sb-opening", "data-sb-open", "Tik om het doosje te openen", "data-sb-skip", "Opening overslaan",
                         "data-sb-video", "sb-eind", "data-sb-replay", 'role="status"'):
            self.assertIn(fragment, html, fragment)
        self.assertIn("Sanne", html)                       # namen uit de studiogegevens
        self.assertIn('id="aanmelden"', html)              # het bestaande aanmeldformulier, geen tweede RSVP-systeem
        self.assertIn("data-countdown", html)
        self.assertIn("data-music-toggle", html)
        self.assertNotIn("data-cover", html, "de opening zit in de kop; invite.js heeft geen eigen openingsscherm nodig")

    def test_knop_en_film_zijn_toegankelijk_en_de_video_start_alleen_na_een_tik(self):
        html = Client().get(DEMO).content.decode()
        self.assertIn('aria-label="Open het ringdoosje en speel de scène af"', html)
        self.assertRegex(html, r'<video[^>]*\bmuted\b[^>]*\bplaysinline\b')
        self.assertNotRegex(html, r'<video[^>]*\bautoplay\b')
        self.assertNotRegex(html, r'<video[^>]*\bloop\b')
        self.assertIn("aria-label=\"Een ringdoosje gaat open", html)
        self.assertRegex(html, r'<img class="sb-eind"[^>]*alt=""')   # het eindbeeld is decoratief

    def test_opening_uit_geeft_direct_het_eindbeeld_zonder_knop(self):
        content = demo_content("strandboog", "bruiloft")
        content.setdefault("style", {})["opening"] = False
        html = _render(content)
        self.assertIn("sb-klaar", html)
        self.assertNotIn("data-sb-open", html)
        self.assertNotIn("data-sb-opening", html)

    def test_mediabestanden_en_script_bestaan_en_worden_geladen(self):
        html = Client().get(DEMO).content.decode()
        paden = set(re.findall(r'(?:src|srcset|href)="/static/([^"\s]+)"', html))
        self.assertTrue(any(p.endswith("strandboog.js") for p in paden))
        self.assertTrue(any(p.endswith("media/strandboog.mp4") for p in paden))
        self.assertTrue(any(p.endswith("media/poster.jpg") for p in paden))
        self.assertTrue(any(p.endswith("media/poster-eind.jpg") for p in paden))
        for pad in paden:
            if pad.startswith("designs/strandboog/"):
                self.assertTrue((settings.BASE_DIR / pad).exists(), pad)

    def test_geen_inline_script_of_style_blokken_csp(self):
        html = Client().get(DEMO).content.decode()
        self.assertFalse(re.search(r"<style[\s>]", html), "inline <style> is niet toegestaan door de CSP")
        inline = [m for m in re.findall(r"<script([^>]*)>", html) if "src=" not in m]
        self.assertLessEqual(len(inline), 1, "alleen het startscript uit core/csp.py mag inline zijn")

    def test_de_uitnodiging_eronder_toont_klantgegevens_en_de_banden(self):
        html = Client().get(DEMO).content.decode()
        for fragment in ("sb-avond", "sb-zon-band", "sb-venster", "sb-tijdlijn", "sb-card", "sb-hoeken"):
            self.assertIn(fragment, html, fragment)
        self.assertIn("Mila", html)                          # contactpersoon uit de studiogegevens
        self.assertIn("De Oranjerie", html)                  # locatie uit de studiogegevens

    def test_andere_specials_zijn_onaangeroerd(self):
        balzaal = Client().get("/voorbeeld/balzaal/?gelegenheid=bruiloft").content.decode()
        self.assertIn("bz-cover", balzaal)
        self.assertNotIn("sb-hero", balzaal)
        gouden = Client().get("/voorbeeld/gouden-avond/?gelegenheid=bruiloft").content.decode()
        self.assertIn("bc-hero", gouden)
        self.assertNotIn("sb-hero", gouden)


class StrandboogBewegingTests(VaylideTestCase):
    """De film speelt alleen na een tik, nooit vanzelf opnieuw; minder beweging en 'beweging stilzetten' zijn rustig; overslaan werkt altijd."""

    def js(self):
        return (ONTWERP / "strandboog.js").read_text(encoding="utf-8")

    def css(self):
        return (ONTWERP / "style.css").read_text(encoding="utf-8")

    def test_video_wordt_niet_automatisch_herhaald_of_gestart(self):
        js = self.js()
        self.assertIn('video.addEventListener("ended"', js)
        self.assertNotIn("video.loop", js)
        self.assertNotIn("autoplay", js)
        self.assertIn('open.addEventListener("click", begin)', js)

    def test_minder_beweging_en_stilgezette_beweging_geven_direct_het_eindbeeld(self):
        css, js = self.css(), self.js()
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertIn("fx-paused", js)
        self.assertIn("if (direct_open || gezien() || rustig()) { direct(); return; }", js)

    def test_overslaan_zet_de_film_stil_en_toont_het_eindbeeld(self):
        js = self.js()
        blok = js[js.index("function overslaanNu()"):js.index("function opnieuw()")]
        self.assertIn("rewind()", blok)
        self.assertIn("afronden(true)", blok)
        self.assertIn("function rewind() { if (!video) return; video.pause();", js)

    def test_de_pagina_komt_vrij_als_de_namen_verschijnen_en_zonder_script_staat_alles_er(self):
        js, css = self.js(), self.css()
        self.assertIn("vergrendel(false)", js[js.index("function tekstTonen()"):js.index("function speel()")])
        self.assertIn("html:not(.js) .sb-hero", css)       # zonder JavaScript: eindbeeld, namen en inhoud
        self.assertIn("var TEKST_OP = 13.7", js)

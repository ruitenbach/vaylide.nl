"""Gouden Avond (special): balzaaldeuren met een sleutel, daarachter de dansvideo; daarna de gewone uitnodiging met aftellen, programma, locatie en aanmelden.
De bestaande Balzaal blijft ongewijzigd (tests/test_balzaal.py)."""
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

ONTWERP = settings.BASE_DIR / "designs" / "gouden-avond" / "v1"
DEMO = "/voorbeeld/gouden-avond/?gelegenheid=bruiloft"


def _render(content):
    version = Template.objects.get(slug="gouden-avond").current_version
    view = build_view(occasion="bruiloft", content=content, overrides={}, template_version=version, options=RenderOptions(mode="demo"))
    return render_to_string(version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})


class GoudenAvondOntwerpTests(VaylideTestCase):
    def manifest(self):
        return json.loads((ONTWERP / "manifest.json").read_text(encoding="utf-8"))

    def test_is_een_zelfstandige_special_en_zonder_prijs_niet_te_bestellen(self):
        template = Template.objects.get(slug="gouden-avond")
        self.assertTrue(template.special)
        self.assertIsNone(special_addon(template), "zonder meerprijs is een special niet te bestellen (er komt nooit een verzonnen prijs)")
        self.assertEqual(template.occasions, ["bruiloft", "verloving"])
        balzaal = Template.objects.get(slug="balzaal")
        self.assertNotEqual(template.pk, balzaal.pk)
        self.assertTrue(balzaal.special)

    def test_staat_onder_specials_en_niet_tussen_de_gewone_kaarten(self):
        pagina = Client().get("/ontwerpen/").content.decode()
        speciaal = pagina[pagina.index("Specials"):] if "Specials" in pagina else ""
        self.assertIn("/ontwerpen/gouden-avond/", speciaal)
        self.assertIn("/ontwerpen/balzaal/", speciaal)
        gewoon = pagina[:pagina.index("Specials")] if "Specials" in pagina else pagina
        self.assertNotIn("/ontwerpen/gouden-avond/", gewoon)

    def test_manifest_effecten_en_tekstkleuren(self):
        data = self.manifest()
        self.assertEqual(effects_errors(data["effects"]), [])
        for palet in data["palettes"]:
            v = palet["vars"]
            for bg in (v["--bc-bg"], v["--bc-bg-2"]):
                for ink in (v["--bc-ink"], v["--bc-muted"], v["--bc-accent"], v["--bc-gold-2"]):
                    self.assertGreaterEqual(contrast(ink, bg), 4.5, f"{palet['key']}: {ink} op {bg}")
            self.assertGreaterEqual(contrast(v["--bc-accent-ink"], v["--bc-accent"]), 4.5)
            # de donkere banden (nacht) met licht goud en ivoor, en de gouden aftelband met donkere tekst
            for tekst in ("#F6ECD4", "#E0D2AE", "#EBD08F"):
                for nacht in (v["--bc-nacht"], v["--bc-nacht-2"]):
                    self.assertGreaterEqual(contrast(tekst, nacht), 7, f"{tekst} op {nacht}")
            for goud in ("#F6E7BC", "#E3C37F", "#F2DCA4"):
                self.assertGreaterEqual(contrast("#2F2108", goud), 7, f"#2F2108 op {goud}")

    def test_media_bestaat_en_is_licht_genoeg_voor_een_telefoon(self):
        video, poster = ONTWERP / "media" / "dans.mp4", ONTWERP / "media" / "poster.jpg"
        self.assertTrue(video.exists() and poster.exists())
        self.assertLess(video.stat().st_size, 2_000_000, "de webversie (720x1280) hoort rond 1,2 MB te zijn; het 15 MB-masterbestand staat niet in de repository")
        self.assertLess(poster.stat().st_size, 400_000)


class GoudenAvondWeergaveTests(VaylideTestCase):
    def test_demo_toont_deuren_sleutel_overslaan_en_de_gedeelde_onderdelen(self):
        html = Client().get(DEMO).content.decode()
        for fragment in ("bc-hero", "data-bc-opening", "data-bc-sleutel", "bc-door--l", "bc-door--r", "data-bc-skip", "Opening overslaan",
                         "data-bc-video", "data-bc-replay", 'role="status"'):
            self.assertIn(fragment, html, fragment)
        self.assertIn("Sanne", html)                       # namen uit de studiogegevens
        self.assertIn('id="aanmelden"', html)              # het bestaande aanmeldformulier, geen tweede RSVP-systeem
        self.assertIn("data-countdown", html)
        self.assertIn("data-music-toggle", html)
        self.assertNotIn("data-cover", html, "de opening zit in de kop; invite.js heeft geen eigen openingsscherm nodig")

    def test_sleutel_en_deuren_zijn_toegankelijk_benoemd(self):
        html = Client().get(DEMO).content.decode()
        self.assertIn('aria-label="Open de balzaaldeuren met de sleutel"', html)
        self.assertEqual(len(re.findall(r'class="bc-door [^"]*" aria-hidden="true"', html)), 2)
        self.assertRegex(html, r'<video[^>]*\bmuted\b[^>]*\bplaysinline\b')
        self.assertNotRegex(html, r'<video[^>]*\bautoplay\b')       # het script start de video na het openen
        self.assertNotRegex(html, r'<video[^>]*\bloop\b')           # speelt niet automatisch opnieuw af

    def test_opening_uit_geeft_direct_de_open_scene_zonder_sleutel(self):
        content = demo_content("gouden-avond", "bruiloft")
        content.setdefault("style", {})["opening"] = False
        html = _render(content)
        self.assertIn("bc-klaar", html)
        self.assertNotIn("data-bc-sleutel", html)
        self.assertNotIn("data-bc-skip", html)
        self.assertNotIn("data-bc-opening", html)

    def test_mediabestanden_en_script_bestaan_en_worden_geladen(self):
        html = Client().get(DEMO).content.decode()
        paden = set(re.findall(r'(?:src|srcset|href)="/static/([^"\s]+)"', html))
        self.assertTrue(any(p.endswith("gouden-avond.js") for p in paden))
        self.assertTrue(any(p.endswith("media/dans.mp4") for p in paden))
        self.assertTrue(any(p.endswith("media/poster.jpg") for p in paden))
        for pad in paden:
            if pad.startswith("designs/gouden-avond/"):
                self.assertTrue((settings.BASE_DIR / pad).exists(), pad)

    def test_geen_inline_script_of_style_blokken_csp(self):
        html = Client().get(DEMO).content.decode()
        self.assertFalse(re.search(r"<style[\s>]", html), "inline <style> is niet toegestaan door de CSP")
        inline = [m for m in re.findall(r"<script([^>]*)>", html) if "src=" not in m]
        self.assertLessEqual(len(inline), 1, "alleen het startscript uit core/csp.py mag inline zijn")

    def test_de_uitnodiging_eronder_is_rijk_opgemaakt_en_blijft_klantgegevens_tonen(self):
        html = Client().get(DEMO).content.decode()
        for fragment in ("bc-nacht", "bc-goud", "bc-stralen", "bc-boogvenster", "bc-folie", "bc-hoeken", "bc-tijdlijn", "bc-card", "bc-flank"):
            self.assertIn(fragment, html, fragment)
        for beeld in ("kroonluchter", "boog", "vloer", "waas"):
            self.assertTrue((ONTWERP / "media" / f"{beeld}.webp").exists(), beeld)
        self.assertIn("Mila", html)                          # contactpersoon uit de studiogegevens
        self.assertIn("De Oranjerie", html)                  # locatie uit de studiogegevens

    def test_bestaande_balzaal_is_onaangeroerd(self):
        html = Client().get("/voorbeeld/balzaal/?gelegenheid=bruiloft").content.decode()
        self.assertIn("bz-cover", html)
        self.assertNotIn("bc-hero", html)
        self.assertRegex(html, r'data-duration="\d+"')   # de eigen opening van Balzaal blijft staan (de duur is niet van Gouden Avond)


class GoudenAvondBewegingTests(VaylideTestCase):
    """Wat de eigenaar nadrukkelijk wil: hartjes en confetti spreiden uit en vervagen, ze vallen niet; 145 deeltjes alleen tijdens het feest; minder beweging is rustig."""

    def js(self):
        return (ONTWERP / "gouden-avond.js").read_text(encoding="utf-8")

    def css(self):
        return (ONTWERP / "style.css").read_text(encoding="utf-8")

    def test_deeltjes_gaan_omhoog_en_naar_buiten_en_nooit_naar_beneden(self):
        js, css = self.js(), self.css()
        self.assertIn('setProperty("--dy", -hoogte', js)
        self.assertIn('setProperty("--endy", (-hoogte - 12)', js)
        keyframes = re.search(r"@keyframes bc-uitspreiden \{(.*?)\n\}", css, re.S).group(1)
        self.assertIn("translate(var(--endx), var(--endy))", keyframes)
        self.assertNotRegex(keyframes, r"translate\(\s*[^)]*,\s*[1-9]")      # geen vaste, positieve (neerwaartse) verplaatsing
        self.assertNotIn("translateY", keyframes)
        self.assertIn("opacity: 0; transform: translate(var(--endx)", keyframes)  # vervagen aan het eind

    def test_145_deeltjes_alleen_tijdens_het_feest_en_daarna_opgeruimd(self):
        js = self.js()
        self.assertIn("i < 145", js)
        self.assertIn('feest.textContent = ""', js)
        self.assertIn("later(stopFeest, 7800)", js)
        self.assertIn("pagehide", js)

    def test_overslaan_stopt_alle_timers_en_het_feest(self):
        js = self.js()
        blok = js[js.index("function overslaanNu()"):js.index("function opnieuw()")]
        for aanroep in ("stopTimers()", "stopFeest()", "video.pause()"):
            self.assertIn(aanroep, blok)

    def test_minder_beweging_geen_overgangen_en_geen_automatisch_feest(self):
        css, js = self.css(), self.js()
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertIn("function startFeest() {\n    if (!feest || feestAan || rustig()) return;", js)
        self.assertIn("fx-paused", js)                 # de knop Beweging van de uitnodiging

    def test_video_wordt_niet_automatisch_herhaald(self):
        js = self.js()
        self.assertIn('video.addEventListener("ended"', js)
        self.assertNotIn("video.loop", js)

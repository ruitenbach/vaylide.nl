"""Kerstbol (special, kerst): een gesloten kerstcadeau, één video met een sneeuwbol en daarna een kerstkaart in smaragd en goud.
De kaart toont alleen wat de klant heeft ingevuld; datum, programma, locatie, aftellen en aanmelden alleen bij een kerstdiner (een datum)."""
import json
import re

from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client

from catalog import collectie
from catalog.atelier import contrast
from catalog.effects import effects_errors
from catalog.models import Template
from catalog.specials import special_addon
from invitations.demo import demo_content
from invitations.render import RenderOptions, build_view

from .helpers import VaylideTestCase

ONTWERP = settings.BASE_DIR / "designs" / "kerstbol" / "v1"
DEMO = "/voorbeeld/kerstbol/?gelegenheid=kerst"


def _render(content=None, **view_wijzigingen):
    version = Template.objects.get(slug="kerstbol").current_version
    content = content if content is not None else demo_content("kerstbol", "kerst")
    view = build_view(occasion="kerst", content=content, overrides={}, template_version=version, options=RenderOptions(mode="demo"))
    view.update(view_wijzigingen)
    return render_to_string(version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})


class KerstbolOntwerpTests(VaylideTestCase):
    def manifest(self):
        return json.loads((ONTWERP / "manifest.json").read_text(encoding="utf-8"))

    def test_is_een_special_voor_kerst_met_eigen_opening_en_zonder_prijs_niet_te_bestellen(self):
        template = Template.objects.get(slug="kerstbol")
        self.assertTrue(template.special)
        self.assertIsNone(special_addon(template), "zonder meerprijs is een special niet te bestellen (er komt nooit een verzonnen prijs)")
        self.assertEqual(template.occasions, ["kerst"])
        self.assertEqual(self.manifest()["envelope_mode"], "built_in")
        self.assertEqual(collectie.groep("kerstbol"), "A")
        self.assertIn("kerstbol", collectie.SPECIALS)

    def test_staat_onder_specials_en_niet_tussen_de_gewone_kaarten(self):
        pagina = Client().get("/ontwerpen/", {"gelegenheid": "kerst"}).content.decode()
        self.assertIn("Specials", pagina)
        speciaal = pagina[pagina.index("Specials"):]
        self.assertIn("/ontwerpen/kerstbol/", speciaal)
        self.assertNotIn("/ontwerpen/kerstbol/", pagina[:pagina.index("Specials")])

    def test_effecten_en_tekstkleuren(self):
        data = self.manifest()
        self.assertEqual(effects_errors(data["effects"]), [])
        v = data["palettes"][0]["vars"]
        for achtergrond in (v["--kb-bos"], v["--kb-bos-2"], v["--kb-nacht"]):
            for tekst in (v["--kb-creme"], v["--kb-creme-2"], v["--kb-goud-lt"]):
                self.assertGreaterEqual(contrast(tekst, achtergrond), 7, f"{tekst} op {achtergrond}")
            self.assertGreaterEqual(contrast(v["--kb-goud"], achtergrond), 4.5, f"goud op {achtergrond}")
        for rood in (v["--kb-rood"], v["--kb-rood-2"]):
            for tekst in (v["--kb-creme"], v["--kb-creme-2"], v["--kb-goud-lt"]):
                self.assertGreaterEqual(contrast(tekst, rood), 7, f"{tekst} op {rood}")
        for papier in (v["--kb-papier"], v["--kb-papier-2"]):
            for tekst in (v["--kb-ink"], v["--kb-ink-2"], v["--kb-accent"]):
                self.assertGreaterEqual(contrast(tekst, papier), 4.5, f"{tekst} op {papier}")

    def test_media_is_licht_en_aanwezig_en_er_is_een_kaartbeeld(self):
        media = ONTWERP / "media"
        for naam, maximum in (("opening.mp4", 2_000_000), ("poster.webp", 400_000), ("eind.webp", 300_000), ("raam.webp", 150_000), ("bol.webp", 150_000)):
            bestand = media / naam
            self.assertTrue(bestand.exists(), naam)
            self.assertLess(bestand.stat().st_size, maximum, naam)
        self.assertGreater((settings.BASE_DIR / "static/img/designs/kerstbol.webp").stat().st_size, 10_000)
        self.assertFalse((media / "opening-master.mp4").exists(), "het masterbestand van 16 MB hoort niet in de repository")


class KerstbolWeergaveTests(VaylideTestCase):
    def test_demo_toont_cadeau_video_skip_en_de_groet_uit_de_studiogegevens(self):
        html = Client().get(DEMO).content.decode()
        for fragment in ("kb-hero", "data-kb-opening", "data-kb-open", 'aria-label="Tik om je kerstcadeau te openen"', "TIK OM JE KERSTCADEAU TE OPENEN",
                         "data-kb-video", "data-kb-skip", "Opening overslaan", "data-kb-replay", 'role="status"', "data-kb-scroll"):
            self.assertIn(fragment, html, fragment)
        self.assertIn("Familie Van Dijk", html)             # afzender uit de studiovelden
        self.assertIn("wenst je fijne feestdagen", html)    # tagline uit de studiovelden
        self.assertNotIn("data-cover", html)

    def test_video_is_stil_speelt_niet_vanzelf_en_herhaalt_niet(self):
        html = Client().get(DEMO).content.decode()
        video = re.search(r"<video[^>]*>", html).group(0)
        for woord in ("muted", "playsinline", 'preload="metadata"', "poster="):
            self.assertIn(woord, video)
        for woord in ("autoplay", "loop"):
            self.assertNotRegex(video, rf"\b{woord}\b")
        self.assertEqual(html.count("<video"), 1, "één video, hergebruikt voor opnieuw beleven")
        self.assertNotIn("data:video", html)
        self.assertNotIn("vendor/gsap", html)

    def test_prototypeteksten_zijn_alleen_een_terugval_als_het_studioveld_leeg_is(self):
        html = _render(content=demo_content("kerstbol", "kerst"), kicker="", tagline="", names=[""])
        for fallback in ("Een magische kerst gewenst", "Fijne feestdagen", "Vol warmte, liefde en bijzondere momenten."):
            self.assertIn(fallback, html)
        gevuld = _render()
        for fallback in ("Een magische kerst gewenst", "Vol warmte, liefde en bijzondere momenten."):
            self.assertNotIn(fallback, gevuld, "studiovelden zijn altijd leidend")

    def test_zonder_datum_geen_kerstdiner_programma_locatie_aftellen_of_aanmelden(self):
        content = demo_content("kerstbol", "kerst")
        content["date"] = ""
        html = _render(content=content)
        for weg in ('id="aanmelden"', "data-countdown", "kb-datum", "kb-programma", "kb-plaats", "kb-aftellen", "Kerstdiner"):
            self.assertNotIn(weg, html, weg)
        self.assertIn("kb-brief", html)                     # de persoonlijke tekst blijft
        self.assertIn("kb-afsluiting", html)

    def test_met_datum_komen_kerstdiner_programma_aftellen_locatie_en_aanmelden_erbij(self):
        html = Client().get(DEMO).content.decode()
        for erbij in ('id="aanmelden"', "data-countdown", "kb-datum", "kb-programma", "kb-plaats", "kb-aftellen", "Kerstdiner"):
            self.assertIn(erbij, html, erbij)

    def test_zonder_ingevulde_teksten_geen_lege_banden_en_niets_verzonnen(self):
        content = demo_content("kerstbol", "kerst")
        content.update({"welcome_text": "", "story": {}, "photos": {}, "date": "", "closing_text": ""})
        html = _render(content=content)
        for weg in ("kb-brief", "kb-jaar", "kb-momenten", "Ons jaar", "Momenten"):
            self.assertNotIn(weg, html, weg)

    def test_opening_uit_geeft_direct_het_eindbeeld_zonder_cadeauknop(self):
        content = demo_content("kerstbol", "kerst")
        content.setdefault("style", {})["opening"] = False
        html = _render(content=content)
        self.assertIn("kb-eind kb-finished kb-klaar", html)
        for weg in ("data-kb-open", "data-kb-skip", "data-kb-opening"):
            self.assertNotIn(weg, html)

    def test_geen_inline_script_of_style_blokken_csp_en_alle_bestanden_bestaan(self):
        html = Client().get(DEMO).content.decode()
        self.assertFalse(re.search(r"<style[\s>]", html))
        self.assertLessEqual(len([m for m in re.findall(r"<script([^>]*)>", html) if "src=" not in m]), 1)
        paden = set(re.findall(r'(?:src|srcset|href)="/static/([^"\s]+)"', html))
        self.assertTrue(any(p.endswith("kerstbol.js") for p in paden))
        for pad in paden:
            if pad.startswith("designs/kerstbol/"):
                self.assertTrue((settings.BASE_DIR / pad).exists(), pad)


class KerstbolBewegingTests(VaylideTestCase):
    def js(self):
        return (ONTWERP / "kerstbol.js").read_text(encoding="utf-8")

    def css(self):
        return (ONTWERP / "style.css").read_text(encoding="utf-8")

    def test_fonkelingen_zijn_40_gouden_en_55_kristallen_met_de_omslag_op_6_5_s(self):
        js = self.js()
        self.assertIn("FASE_TWEE = 6.5", js)
        self.assertIn("glinten(0, 40)", js)
        self.assertIn("glinten(40, 95)", js)

    def test_fonkelingen_vallen_niet_en_hebben_geen_zwaar_filter_per_deeltje(self):
        css = self.css()
        for keyframes in re.findall(r"@keyframes kb-(?:goud|kristal) \{(.*?)\n?\}\s*(?=\n|$)", css, re.S):
            self.assertNotRegex(keyframes, r"translateY\(\s*[1-9]")
        self.assertNotRegex(css, r"\.kb-glint[^{]*\{[^}]*filter\s*:")

    def test_overslaan_stopt_timers_video_en_deeltjes_en_alles_wordt_opgeruimd(self):
        js = self.js()
        toon = js[js.index("function toonEind("):js.index("function einde()")]
        for aanroep in ("stopTimers()", "wisGlinten()", "video.pause()"):
            self.assertIn(aanroep, toon)
        self.assertIn('"pagehide"', js)
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertIn("fx-paused", js)

    def test_video_wordt_niet_zwaar_of_dubbel_geladen(self):
        js = self.js()
        self.assertIn("saveData", js)                       # niet voorladen bij Data-besparing
        self.assertNotIn("video.loop", js)
        self.assertEqual(js.count("document.createElement(\"video\")"), 0)

"""Kerstkaart (special, kerst): een chocoladehuis met een gouden deurklopper, drie klopjes, één video en daarna een kerstkaart in nachtblauw, chocolade en rood-wit snoep.
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

ONTWERP = settings.BASE_DIR / "designs" / "kerstkaart" / "v1"
DEMO = "/voorbeeld/kerstkaart/?gelegenheid=kerst"


def _render(content=None, **view_wijzigingen):
    version = Template.objects.get(slug="kerstkaart").current_version
    content = content if content is not None else demo_content("kerstkaart", "kerst")
    view = build_view(occasion="kerst", content=content, overrides={}, template_version=version, options=RenderOptions(mode="demo"))
    view.update(view_wijzigingen)
    return render_to_string(version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})


class KerstkaartOntwerpTests(VaylideTestCase):
    def manifest(self):
        return json.loads((ONTWERP / "manifest.json").read_text(encoding="utf-8"))

    def test_is_een_special_voor_kerst_met_eigen_opening_en_zonder_prijs_niet_te_bestellen(self):
        template = Template.objects.get(slug="kerstkaart")
        self.assertTrue(template.special)
        self.assertIsNone(special_addon(template), "zonder meerprijs is een special niet te bestellen (er komt nooit een verzonnen prijs)")
        self.assertEqual(template.occasions, ["kerst"])
        self.assertEqual(self.manifest()["envelope_mode"], "built_in")
        self.assertEqual(collectie.groep("kerstkaart"), "A")
        self.assertIn("kerstkaart", collectie.SPECIALS)

    def test_effecten_en_tekstkleuren(self):
        data = self.manifest()
        self.assertEqual(effects_errors(data["effects"]), [])
        v = data["palettes"][0]["vars"]
        for achtergrond in (v["--kk-nacht"], v["--kk-nacht-2"], v["--kk-choco"], v["--kk-choco-2"]):
            for tekst in (v["--kk-sneeuw"], v["--kk-ijs"], v["--kk-goud-lt"], v["--kk-room"]):
                self.assertGreaterEqual(contrast(tekst, achtergrond), 7, f"{tekst} op {achtergrond}")
            self.assertGreaterEqual(contrast(v["--kk-goud"], achtergrond), 4.5, f"goud op {achtergrond}")
        for papier in (v["--kk-room"], v["--kk-room-2"]):
            for tekst in (v["--kk-ink"], v["--kk-ink-2"], v["--kk-accent"]):
                self.assertGreaterEqual(contrast(tekst, papier), 4.5, f"{tekst} op {papier}")

    def test_media_is_licht_en_aanwezig_en_er_is_een_kaartbeeld(self):
        media = ONTWERP / "media"
        for naam, maximum in (("opening.mp4", 3_000_000), ("poster.webp", 300_000), ("eind.webp", 300_000), ("klopper-plaat.webp", 20_000), ("klopper-ring.webp", 20_000),
                              ("maan.webp", 100_000), ("lolly.webp", 100_000), ("nacht.webp", 150_000), ("dorp.webp", 150_000)):
            bestand = media / naam
            self.assertTrue(bestand.exists(), naam)
            self.assertLess(bestand.stat().st_size, maximum, naam)
        self.assertGreater((settings.BASE_DIR / "static/img/designs/kerstkaart.webp").stat().st_size, 10_000)


class KerstkaartWeergaveTests(VaylideTestCase):
    def test_demo_toont_klopper_video_skip_en_de_groet_uit_de_studiogegevens(self):
        html = Client().get(DEMO).content.decode()
        for fragment in ("kk-hero", "data-kk-opening", "data-kk-open", 'aria-label="Klop op de deur om je kerstkaart te openen"', "Tik op de deurklopper",
                         "data-kk-deur", "klopper-plaat.webp", "klopper-ring.webp", "data-kk-video", "data-kk-skip", "Opening overslaan", "data-kk-replay", 'role="status"', "data-kk-scroll"):
            self.assertIn(fragment, html, fragment)
        self.assertIn("Familie Van Dijk", html)             # afzender uit de studiovelden
        self.assertIn("wenst je fijne feestdagen", html)    # tagline uit de studiovelden
        self.assertNotIn("data-cover", html)

    def test_video_is_stil_speelt_niet_vanzelf_en_herhaalt_niet(self):
        html = Client().get(DEMO).content.decode()
        video = re.search(r"<video[^>]*>", html).group(0)
        for woord in ("muted", "playsinline", "preload="):
            self.assertIn(woord, video)
        for woord in ("autoplay", "loop"):
            self.assertNotRegex(video, rf"\b{woord}\b")
        self.assertEqual(html.count("<video"), 1, "één video, hergebruikt voor opnieuw beleven")
        self.assertNotIn("data:video", html)
        self.assertNotIn("vendor/gsap", html)

    def test_prototypeteksten_zijn_alleen_een_terugval_als_het_studioveld_leeg_is(self):
        html = _render(content=demo_content("kerstkaart", "kerst"), kicker="", tagline="", names=[""])
        for fallback in ("Een warme kerst gewenst", "Fijne feestdagen", "Vol warmte, licht en lekkers."):
            self.assertIn(fallback, html)
        gevuld = _render()
        for fallback in ("Een warme kerst gewenst", "Vol warmte, licht en lekkers."):
            self.assertNotIn(fallback, gevuld, "studiovelden zijn altijd leidend")

    def test_zonder_datum_geen_kerstdiner_programma_locatie_aftellen_of_aanmelden(self):
        content = demo_content("kerstkaart", "kerst")
        content["date"] = ""
        html = _render(content=content)
        for weg in ('id="aanmelden"', "data-countdown", "kk-datum", "kk-programma", "kk-plaats", "kk-aftellen", "Kerstdiner"):
            self.assertNotIn(weg, html, weg)
        self.assertIn("kk-brief", html)                     # de persoonlijke tekst blijft
        self.assertIn("kk-afsluiting", html)

    def test_met_datum_komen_kerstdiner_programma_aftellen_locatie_en_aanmelden_erbij(self):
        html = Client().get(DEMO).content.decode()
        for erbij in ('id="aanmelden"', "data-countdown", "kk-datum", "kk-programma", "kk-plaats", "kk-aftellen", "Kerstdiner"):
            self.assertIn(erbij, html, erbij)

    def test_zonder_ingevulde_teksten_geen_lege_banden_en_niets_verzonnen(self):
        content = demo_content("kerstkaart", "kerst")
        content.update({"welcome_text": "", "story": {}, "photos": {}, "date": "", "closing_text": ""})
        html = _render(content=content)
        for weg in ("kk-brief", "kk-jaar", "kk-momenten", "Ons jaar", "Momenten"):
            self.assertNotIn(weg, html, weg)

    def test_opening_uit_geeft_direct_het_eindbeeld_zonder_klopper(self):
        content = demo_content("kerstkaart", "kerst")
        content.setdefault("style", {})["opening"] = False
        html = _render(content=content)
        self.assertIn("kk-eind kk-finished kk-klaar", html)
        for weg in ("data-kk-open", "data-kk-skip", "data-kk-opening", "data-kk-deur"):
            self.assertNotIn(weg, html)

    def test_geen_inline_script_of_style_blokken_csp_en_alle_bestanden_bestaan(self):
        html = Client().get(DEMO).content.decode()
        self.assertFalse(re.search(r"<style[\s>]", html))
        self.assertLessEqual(len([m for m in re.findall(r"<script([^>]*)>", html) if "src=" not in m]), 1)
        paden = set(re.findall(r'(?:src|srcset|href)="/static/([^"\s]+)"', html))
        self.assertTrue(any(p.endswith("kerstkaart.js") for p in paden))
        for pad in paden:
            if pad.startswith("designs/kerstkaart/"):
                self.assertTrue((settings.BASE_DIR / pad).exists(), pad)


class KerstkaartBewegingTests(VaylideTestCase):
    def js(self):
        return (ONTWERP / "kerstkaart.js").read_text(encoding="utf-8")

    def css(self):
        return (ONTWERP / "style.css").read_text(encoding="utf-8")

    def test_drie_klopjes_en_de_video_start_pas_daarna(self):
        js = self.js()
        self.assertIn("KLOP_TIJDEN = [0, 430, 800]", js)
        self.assertIn("klopKlopKlop(speel)", js)
        self.assertNotIn("video.loop", js)
        self.assertNotIn("autoplay", js)

    def test_het_klopgeluid_is_gesynthetiseerd_en_alleen_na_een_tik(self):
        js = self.js()
        self.assertIn("AudioContext", js)
        self.assertNotIn(".mp3", js)
        geluid = js[js.index("function geluid()"):js.index("function sluitGeluid()")]
        self.assertIn("rustig()", geluid)                   # niet bij 'minder beweging'

    def test_overslaan_stopt_timers_video_geluid_en_vonken_en_alles_wordt_opgeruimd(self):
        js = self.js()
        toon = js[js.index("function toonEind("):js.index("function einde()")]
        for aanroep in ("stopTimers()", "wisVonken()", "sluitGeluid()", "video.pause()"):
            self.assertIn(aanroep, toon)
        self.assertIn('"pagehide"', js)
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertIn("fx-paused", js)
        self.assertIn("saveData", js)                       # niet voorladen bij Data-besparing

    def test_de_klopper_beweegt_met_transformaties_en_valt_niet_terug_op_zware_filters(self):
        css = self.css()
        self.assertIn("@keyframes kk-ringklop", css)
        self.assertNotRegex(css, r"\.kk-vonk[^{]*\{[^}]*filter\s*:")

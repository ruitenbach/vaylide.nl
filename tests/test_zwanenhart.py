"""Zwanenhart (special, nieuw in kaartlab): de aangeleverde envelopvideo en zwanenvideo, samengevoegd tot één film (de envelop opent, het licht gaat over in twee
zwanen die een hart vormen), als opening na een tik; daarna de namen, de datum en de gewone uitnodiging met aftellen, programma, locatie en aanmelden.
Opbouw gelijk aan Witte Roos. Bestaande ontwerpen blijven ongewijzigd."""
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

ONTWERP = settings.BASE_DIR / "designs" / "zwanenhart" / "v1"
DEMO = "/voorbeeld/zwanenhart/?gelegenheid=bruiloft"


def _render(content):
    version = Template.objects.get(slug="zwanenhart").current_version
    view = build_view(occasion="bruiloft", content=content, overrides={}, template_version=version, options=RenderOptions(mode="demo"))
    return render_to_string(version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})


class ZwanenhartOntwerpTests(VaylideTestCase):
    def manifest(self):
        return json.loads((ONTWERP / "manifest.json").read_text(encoding="utf-8"))

    def test_is_een_special_voor_bruiloft_verloving_en_jubileum_en_zonder_prijs_niet_te_bestellen(self):
        template = Template.objects.get(slug="zwanenhart")
        self.assertTrue(template.special)
        self.assertEqual(template.occasions, ["bruiloft", "verloving", "jubileum"])
        self.assertIsNone(special_addon(template), "de meerprijs bepaalt de prijzenchat; zonder prijs is een special niet te bestellen")

    def test_manifest_effecten_en_tekstkleuren(self):
        data = self.manifest()
        self.assertEqual(effects_errors(data["effects"]), [])
        for palet in data["palettes"]:
            v = palet["vars"]
            for bg in (v["--zh-bg"], v["--zh-bg-2"]):
                for ink in (v["--zh-ink"], v["--zh-muted"], v["--zh-accent"], v["--zh-gold-2"]):
                    self.assertGreaterEqual(contrast(ink, bg), 4.5, f"{ink} op {bg}")
            self.assertGreaterEqual(contrast(v["--zh-accent-ink"], v["--zh-accent"]), 4.5)
            for tekst in ("#FBF8F2", "#E9DFCF"):
                for donker in (v["--zh-schaduw"], v["--zh-schaduw-2"]):
                    self.assertGreaterEqual(contrast(tekst, donker), 7, f"{tekst} op {donker}")

    def test_media_bestaat_en_is_licht_genoeg_voor_een_telefoon(self):
        media = ONTWERP / "media"
        beelden = ("bloesem.webp", "zwanen.webp", "water.webp", "papier.webp", "waas-envelop.webp", "waas-zwanen.webp")
        for naam in ("zwanenhart.mp4", "poster.jpg", "poster-eind.jpg") + beelden:
            self.assertTrue((media / naam).exists(), naam)
        self.assertLess((media / "zwanenhart.mp4").stat().st_size, 2_500_000, "de samengevoegde film (720x1280, 6,5 s, zonder geluid)")
        for naam in ("poster.jpg", "poster-eind.jpg"):
            self.assertLess((media / naam).stat().st_size, 200_000, naam)
        for naam in beelden:
            self.assertLess((media / naam).stat().st_size, 100_000, naam)

    def test_geen_logo_of_merknaam_in_de_opening(self):
        # zoals bij Witte Roos: geen VAYLIDE-logo of merknaam in de kop (alleen het vaste merkteken onderaan)
        kop = (ONTWERP / "invitation.html").read_text(encoding="utf-8").split('<main', 1)[0]
        self.assertNotRegex(kop, r"(?i)vaylide")


class ZwanenhartWeergaveTests(VaylideTestCase):
    def test_demo_toont_poster_tikknop_overslaan_film_en_de_gedeelde_onderdelen(self):
        html = Client().get(DEMO).content.decode()
        for fragment in ("zh-hero", "data-zh-opening", "data-zh-open", "Tik om de envelop te openen", "data-zh-skip", "Opening overslaan",
                         "data-zh-video", "zh-eind", 'role="status"'):
            self.assertIn(fragment, html, fragment)
        self.assertIn("Sanne", html)
        self.assertIn('id="aanmelden"', html)              # het bestaande aanmeldformulier
        self.assertIn("data-countdown", html)
        self.assertIn("data-music-toggle", html)
        self.assertNotIn("data-cover", html, "de opening zit in de kop; invite.js heeft geen eigen openingsscherm nodig")

    def test_knop_en_film_zijn_toegankelijk_en_de_video_start_alleen_na_een_tik(self):
        html = Client().get(DEMO).content.decode()
        self.assertIn('aria-label="Tik om de envelop te openen en speel de opening af"', html)
        self.assertRegex(html, r'<video[^>]*\bmuted\b[^>]*\bplaysinline\b')
        self.assertNotRegex(html, r'<video[^>]*\bautoplay\b')
        self.assertNotRegex(html, r'<video[^>]*\bloop\b')
        self.assertRegex(html, r'<img class="zh-eind"[^>]*alt=""')

    def test_opening_uit_geeft_direct_het_eindbeeld_zonder_knop(self):
        content = demo_content("zwanenhart", "bruiloft")
        content.setdefault("style", {})["opening"] = False
        html = _render(content)
        self.assertIn("zh-klaar", html)
        self.assertNotIn("data-zh-open", html)
        self.assertNotIn("data-zh-opening", html)

    def test_mediabestanden_en_script_bestaan_en_worden_geladen(self):
        html = Client().get(DEMO).content.decode()
        paden = set(re.findall(r'(?:src|srcset|href|poster)="/static/([^"\s]+)"', html))
        for eind in ("zwanenhart.js", "media/zwanenhart.mp4", "media/poster.jpg", "media/poster-eind.jpg"):
            self.assertTrue(any(p.endswith(eind) for p in paden), eind)
        for pad in paden:
            if pad.startswith("designs/zwanenhart/"):
                self.assertTrue((settings.BASE_DIR / pad).exists(), pad)

    def test_geen_inline_script_of_style_blokken_csp(self):
        html = Client().get(DEMO).content.decode()
        self.assertFalse(re.search(r"<style[\s>]", html))
        inline = [m for m in re.findall(r"<script([^>]*)>", html) if "src=" not in m]
        self.assertLessEqual(len(inline), 1)

    def test_de_uitnodiging_eronder_toont_klantgegevens_en_de_banden(self):
        html = Client().get(DEMO).content.decode()
        for fragment in ("zh-schaduw", "zh-kaarslicht", "zh-venster", "zh-tijdlijn", "zh-card", "zh-boogfoto"):
            self.assertIn(fragment, html, fragment)
        self.assertIn("Mila", html)
        self.assertIn("De Oranjerie", html)

    def test_andere_specials_zijn_onaangeroerd(self):
        for slug, klasse in (("strandboog", "sb-hero"), ("gouden-avond", "bc-hero"), ("balzaal", "bz-cover")):
            html = Client().get(f"/voorbeeld/{slug}/?gelegenheid=bruiloft").content.decode()
            self.assertIn(klasse, html)
            self.assertNotIn("zh-hero", html)


class ZwanenhartBewegingTests(VaylideTestCase):
    def js(self):
        return (ONTWERP / "zwanenhart.js").read_text(encoding="utf-8")

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

    def test_terugval_als_de_film_niet_kan_spelen(self):
        js = self.js()
        self.assertIn("belofte.then(null, terugval)", js)                 # afspelen geweigerd
        self.assertIn('video.addEventListener("error", terugval)', js)    # film laadt niet
        self.assertIn("window.setTimeout(terugval, STARTTIJD)", js)        # film start niet op tijd
        self.assertIn("De film kan hier niet worden afgespeeld", js)

    def test_de_pagina_komt_vrij_als_de_namen_verschijnen_en_zonder_script_staat_alles_er(self):
        js, css = self.js(), self.css()
        self.assertIn("vergrendel(false)", js[js.index("function tekstTonen()"):js.index("function terugval()")])
        self.assertIn("html:not(.js) .zh-hero", css)
        self.assertIn("var TEKST_OP = 5.8", js)
        self.assertIn("if (bezig) { tekstTonen(); afronden(true); }", js)   # vonken ook als de laatste timeupdate vóór TEKST_OP viel


class ZwanenhartLevenTests(VaylideTestCase):
    """Leven zoals bij Witte Roos: glitter, vonken bij de namen, fonkelingen op het zegel en het water, avondzon en glans; alles decoratief en stil te zetten."""

    def test_effecten_in_het_manifest(self):
        effects = json.loads((ONTWERP / "manifest.json").read_text(encoding="utf-8"))["effects"]
        self.assertEqual((effects["sfeer"], effects["knal"], effects["namen"]), ("glitter", "vonken", "folie"))
        self.assertIn("tik", effects["extra"])

    def test_effectlagen_zijn_decoratief_en_staan_in_kop_en_banden(self):
        html = Client().get(DEMO).content.decode()
        self.assertIn('data-fx-sfeer="glitter"', html)
        self.assertIn('data-fx-knal="vonken"', html)
        self.assertIn('<div class="fx-slot zh-fx" data-fx-slot="hero" aria-hidden="true">', html)
        self.assertGreaterEqual(html.count('data-fx-slot="band" aria-hidden="true"'), 5)
        self.assertIn('<div class="zh-beeld" aria-hidden="true">', html)
        self.assertIn('<div class="zh-fonkel zh-fonkel--envelop">', html)
        self.assertIn('<div class="zh-fonkel zh-fonkel--meer">', html)
        self.assertIn('<div class="zh-lichtjes" aria-hidden="true">', html)
        self.assertEqual(html.count('class="fx-shimmer"'), 2)

    def test_alles_beweegt_alleen_onder_fx_motion_en_volgt_de_knop_beweging(self):
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        deel = css[css.index("leven in de kaart"):]
        for regel in re.findall(r"[^{}]*\{[^{}]*animation:[^;]*infinite[^}]*\}", deel):
            self.assertIn(".fx-motion", regel, regel.strip()[:80])
            self.assertIn("var(--fx-play, running)", regel, regel.strip()[:80])

    def test_de_vonken_komen_met_de_namen_en_niet_bij_minder_beweging(self):
        js = (ONTWERP / "zwanenhart.js").read_text(encoding="utf-8")
        blok = js[js.index("function vonken()"):js.index("function tekstTonen()")]
        self.assertIn("if (rustig()", blok)
        self.assertIn('new CustomEvent("invite:opening")', blok)
        self.assertIn("vonken();", js[js.index("function tekstTonen()"):js.index("function terugval()")])


class ZwanenhartFilmTests(VaylideTestCase):
    def test_de_film_is_staand_kort_en_zonder_geluid(self):
        # 720x1280 H.264 met +faststart: het moov-blok staat vooraan, zodat de film snel start op een telefoon
        data = (ONTWERP / "media" / "zwanenhart.mp4").read_bytes()
        self.assertLess(data.find(b"moov"), data.find(b"mdat"))
        self.assertNotIn(b"soun", data[: data.find(b"mdat")], "geen geluidsspoor")

    def test_desktop_achtergrond_volgt_de_film(self):
        html = Client().get(DEMO).content.decode()
        self.assertIn("zh-waas--envelop", html)
        self.assertIn("zh-waas--zwanen", html)
        css = (ONTWERP / "style.css").read_text(encoding="utf-8")
        self.assertIn(":is(.zh-tekst, .zh-klaar, html:not(.js) .zh-hero) .zh-waas--zwanen { opacity: 1; }", css)


class ZwanenhartLiggendEnLangeNamenTests(VaylideTestCase):
    """Twee gerichte fixes: de openingsknop op een liggende telefoon en zeer lange namen die niet over de zwanen heen vallen."""

    def _namen(self, partner_1, partner_2):
        content = demo_content("zwanenhart", "bruiloft")
        content["names"] = {"partner_1": partner_1, "partner_2": partner_2}
        html = _render(content)
        return re.search(r'<h1 class="([^"]+)" id="zh-namen"', html).group(1)

    def test_de_klasse_van_de_namen_volgt_de_lengte(self):
        self.assertEqual(self._namen("Sanne", "Daan"), "zh-names zh-names--normal")
        self.assertEqual(self._namen("Alexandra Maria", "Sebastiaan"), "zh-names zh-names--long")
        self.assertEqual(self._namen("Zoë d'Artagnan", "Max de Ridder van der Heijden-Smit"), "zh-names zh-names--xlong")

    def test_lange_namen_worden_kleiner_en_gewone_namen_blijven_zoals_ze_waren(self):
        css = (ONTWERP / "style.css").read_text()
        self.assertRegex(css, r"\.zh-caption \.zh-names--xlong \{ font-size: clamp\(")
        self.assertNotRegex(css, r"\.zh-caption \.zh-names--normal")

    def test_liggende_telefoon_past_de_opening_op_het_scherm_en_zet_de_namen_boven_de_zwanen(self):
        css = (ONTWERP / "style.css").read_text()
        blok = css[css.index("@media (orientation: landscape) and (max-height: 520px)"):]
        blok = blok[:blok.index("/* breder dan staand")]
        self.assertIn(".zh-hero { min-height: 0; }", blok)       # geen vaste minimumhoogte die de knop onder de rand duwt
        self.assertIn(".zh-open { bottom: max(10px, env(safe-area-inset-bottom))", blok)
        self.assertIn("grid-template-rows: auto auto 1fr auto auto", blok)   # namen bovenin, datum en knoppen onderin


class ZwanenhartVoorbeeldOpOntwerppaginaTests(VaylideTestCase):
    def test_het_voorbeeld_op_de_ontwerppagina_begint_met_de_gesloten_envelop(self):
        """Het voorbeeld op de ontwerppagina is een iframe met ?embed=1. De opening mag daar niet worden overgeslagen: alleen een link naar de aanmelding,
        de live kaart in de Studio en de bedankpagina (data-direct-open) tonen direct het eindbeeld."""
        html = Client().get(DEMO + "&embed=1").content.decode()
        self.assertIn("data-zh-opening", html)
        self.assertIn("data-zh-open", html)
        self.assertNotIn("data-direct-open", html)
        js = (ONTWERP / "zwanenhart.js").read_text()
        regel = js[js.index("var direct_open"):js.index("if (direct_open")]
        self.assertNotIn("inv-embed", regel)
        self.assertIn("data-direct-open", regel)

    def test_het_gouden_lakzegel_is_ook_aan_te_tikken_en_de_knop_blijft_het_toegankelijke_pad(self):
        html = Client().get(DEMO).content.decode()
        self.assertIn('data-zh-zegel aria-hidden="true"', html)       # extra tikvlak op het zegel; de knop eronder blijft voor toetsenbord en schermlezer
        self.assertIn("data-zh-open", html)
        js = (ONTWERP / "zwanenhart.js").read_text()
        self.assertIn('q("[data-zh-zegel]")', js)
        css = (ONTWERP / "style.css").read_text()
        self.assertIn(".zh-gate .zh-zegelknop { display: block; }", css)    # alleen op het eerste beeld, niet daarna

    def test_op_lage_schermen_blijft_onderaan_ruimte_voor_beweging_en_muziek(self):
        css = (ONTWERP / "style.css").read_text()
        blok = css[css.index("@media (max-height: 620px) {\n  .zh-heading"):]
        blok = blok[:blok.index("\n}\n")]
        self.assertIn("padding-bottom: max(64px", blok)

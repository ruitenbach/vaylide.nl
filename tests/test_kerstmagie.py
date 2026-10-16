"""Kerstmagie: kerstkaart met een openingsfilm die pas na een tik in het midden start, in de bestaande kerstcollectie en prijsstructuur."""
import json
import re
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from catalog import collectie, prijzen
from catalog.atelier import contrast
from catalog.effects import effect_summary, effects_errors
from catalog.occasions import OCCASIONS
from catalog.models import Template
from orders.models import Order

from .helpers import VaylideTestCase
from .test_prijsstructuur import vul

DESIGN = Path(settings.BASE_DIR) / "designs" / "kerstmagie" / "v1"
MEDIA = DESIGN / "media"


def manifest():
    return json.loads((DESIGN / "manifest.json").read_text(encoding="utf-8"))


class KerstmagieDesignTests(TestCase):
    def test_manifest_is_valid_and_registered(self):
        data = manifest()
        self.assertEqual(effects_errors(data["effects"]), [])
        self.assertEqual(data["effects"]["sfeer"], "sneeuw")
        self.assertGreaterEqual(len(data["palettes"]), 3)
        template = Template.objects.get(slug="kerstmagie")
        self.assertEqual(template.current_version.manifest["opening"], "film")
        self.assertIn("vallende sneeuw", effect_summary(data["effects"]))

    def test_every_colour_variant_is_readable(self):
        for pal in manifest()["palettes"]:
            v = pal["vars"]
            for text in ("--kl-ink", "--kl-muted", "--kl-gold", "--kl-gold-2"):
                for background in ("--kl-bg", "--kl-bg-2"):
                    self.assertGreaterEqual(contrast(v[text], v[background]), 4.5, f"{pal['key']} {text} op {background}")
            # Tekst op de gouden knoppen (--inv-accent-contrast in style.css).
            self.assertGreaterEqual(contrast("#101826", v["--kl-gold"]), 4.5, pal["key"])

    def test_media_files_exist_and_stay_light(self):
        for name, limit in (("intro.mp4", 3_500_000), ("intro.webm", 3_500_000), ("poster.webp", 300_000), ("dorp.webp", 400_000),
                            ("trein.webp", 150_000), ("plein.webp", 150_000), ("sneeuwvlok.webp", 200_000), ("pano.webp", 120_000),
                            ("gloed.webp", 200_000), ("tussen.webp", 150_000), ("rivier.webp", 100_000), ("water.webp", 100_000)):
            path = MEDIA / name
            self.assertTrue(path.exists(), name)
            self.assertLess(path.stat().st_size, limit, name)
            self.assertTrue(finders.find(f"designs/kerstmagie/v1/media/{name}"), name)


class KerstmagieRenderTests(TestCase):
    def render(self, occasion):
        response = Client().get("/voorbeeld/kerstmagie/", {"gelegenheid": occasion})
        self.assertEqual(response.status_code, 200, occasion)
        return response.content.decode()

    def test_renders_for_every_occasion_with_the_film_cover(self):
        for occasion in manifest()["occasions"]:
            html = self.render(occasion)
            self.assertIn("data-kl-play", html, occasion)
            self.assertIn("kl-hero__img", html, occasion)
            self.assertIn("/static/designs/kerstmagie/v1/intro.js", html, occasion)
            self.assertIn('data-fx-sfeer="sneeuw"', html, occasion)
            # Geen inline scripts naast het vaste startscript (CSP).
            self.assertEqual(len(re.findall(r"<script>", html)), 1, occasion)

    def test_film_waits_for_a_tap(self):
        """Geen autoplay en nog geen bronbestand: intro.js laadt de film pas als het openingsscherm getoond wordt."""
        html = self.render("bruiloft")
        video = re.search(r"<video\b[^>]*>", html).group(0)
        self.assertNotIn("autoplay", video)
        self.assertNotIn(" src=", video)
        self.assertIn("muted", video)
        self.assertIn("playsinline", video)
        self.assertIn("data-src-mp4=", video)
        self.assertIn("data-src-webm=", video)
        # De tik start de film; het gewone openen (data-open) zit alleen op 'Overslaan' en op een verborgen knop.
        play = re.search(r"<button\b[^>]*data-kl-play[^>]*>", html).group(0)
        self.assertNotIn("data-open", play)
        self.assertEqual(len(re.findall(r"<button\b[^>]*data-open", html)), 2)

    def test_intro_script_falls_back_to_opening_the_card(self):
        script = (DESIGN / "intro.js").read_text(encoding="utf-8")
        for needle in ("ended", "error", "catch(open)", "invite:opening", "fx-paused", "prefers-reduced-motion"):
            self.assertIn(needle, script, needle)

    def test_cover_is_closed_for_other_designs(self):
        html = Client().get("/voorbeeld/avondgoud/").content.decode()
        self.assertNotIn("kerstmagie", html)


class KerstmagieKoppelingTests(VaylideTestCase):
    """Kerstmagie hoort alleen bij de bestaande gelegenheid Kerst, staat in de collectie en valt onder de bestaande prijsstructuur."""

    def test_alleen_de_bestaande_gelegenheid_kerst(self):
        data = manifest()
        self.assertEqual(data["occasions"], ["kerst"])
        self.assertIn("kerst", OCCASIONS)
        self.assertEqual(Template.objects.get(slug="kerstmagie").occasions, ["kerst"])
        # Dezelfde koppeling als de andere kerstontwerpen met eigen film.
        for slug in ("kerstmarkt", "kerstpaleis", "kerstcoupe", "kerstbal"):
            other = json.loads((Path(settings.BASE_DIR) / "designs" / slug / "v1" / "manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(other["occasions"], data["occasions"], slug)
            self.assertEqual(other["envelope_mode"], data["envelope_mode"], slug)
            self.assertEqual(other["opening"], data["opening"], slug)

    def test_staat_in_de_kerstcollectie_en_niet_bij_andere_gelegenheden(self):
        kerst = [c["template"].slug for c in Client().get("/ontwerpen/", {"gelegenheid": "kerst"}).context["cards"]]
        self.assertIn("kerstmagie", kerst)
        for occasion in ("bruiloft", "verloving", "verjaardag", "jubileum", "zakelijk", "babyshower"):
            slugs = [c["template"].slug for c in Client().get("/ontwerpen/", {"gelegenheid": occasion}).context["cards"]]
            self.assertNotIn("kerstmagie", slugs, occasion)
        self.assertEqual(collectie.groep("kerstmagie"), "B")
        self.assertTrue(collectie.zichtbaar("kerstmagie"))

    def test_valt_onder_de_bestaande_prijsstructuur_zonder_nieuwe_prijzen(self):
        self.assertEqual(prijzen.INDELING["kerstmagie"], prijzen.LUXE)
        self.assertEqual(prijzen.INDELING["kerstmagie"], prijzen.INDELING["kerstmarkt"])
        with override_settings(PRICING_V2=True):
            template = Template.objects.get(slug="kerstmagie")
            info = prijzen.prijs_info(template, "kerst")
            self.assertEqual((info["naam"], info["cents"], info["maanden"], info["rij"]), ("Luxe", 2495, 12, "kerst"))
            # Alleen te koop als kerstkaart: voor andere gelegenheden bestaat geen prijs.
            for occasion in ("bruiloft", "verloving", "verjaardag", "jubileum", "zakelijk", "babyshower"):
                self.assertIsNone(prijzen.prijs_cents(template, occasion), occasion)
        # De prijstabel zelf is niet veranderd.
        self.assertEqual(prijzen.PRIJZEN["kerst"], (995, 2495, 4995))

    def test_bestellen_en_publiceren_kost_het_bestaande_luxe_kerstbedrag(self):
        with override_settings(PRICING_V2=True):
            klant = self.make_customer("kerstmagie@example.com")
            inv = vul(self.make_invitation(owner=klant, template="kerstmagie", occasion="kerst"), klant)
            c = Client()
            c.force_login(klant)
            html = c.get(reverse("studio:step", args=[inv.uid, "bestellen"])).content.decode()
            self.assertIn("€ 24,95", html)
            self.assertIn("12 maanden online", html)
            for tekst in ("Upgrade", "Extra opties", "Essentieel", "Compleet"):
                self.assertNotIn(tekst, html, tekst)
            payment = self.pay(inv, klant)
            order = Order.objects.get(invitation=inv)
            self.assertEqual((order.total_cents, payment.amount_cents, order.package_code, order.availability_months), (2495, 2495, prijzen.LUXE, 12))
            inv.refresh_from_db()
            self.assertTrue(inv.is_published)


class KerstmagieHelderheidTests(TestCase):
    """Het ijskristal op het openingsscherm houdt de helderheid van de film: geen donkere sluier en geen filter op de film zelf."""

    def css(self):
        return (DESIGN / "style.css").read_text(encoding="utf-8")

    def test_geen_donkere_sluier_over_het_openingsbeeld(self):
        html = Client().get("/voorbeeld/kerstmagie/", {"gelegenheid": "kerst"}).content.decode()
        self.assertNotIn("kl-cover__shade", html)
        self.assertNotIn("kl-cover__shade", self.css())

    def test_geen_filter_op_de_film_of_het_eerste_beeld(self):
        css = self.css()
        for selector in (".kl-video", ".kl-stage__poster"):
            blocks = re.findall(re.escape(selector) + r"[^{}]*\{([^}]*)\}", css)
            self.assertTrue(blocks, selector)
            for block in blocks:
                self.assertNotIn("filter", block.replace("backdrop-filter", ""), selector)
                self.assertNotIn("mix-blend", block, selector)

    def test_vervaagde_achtergrond_dekt_de_hele_breedte(self):
        """Een algemene regel img { max-width: 100% } hield de achtergrond op 100% in plaats van 116%: rechts bleef een donkere strook."""
        css = self.css()
        self.assertRegex(css, r"\.kl-stage__backdrop \{[^}]*max-width: none")
        self.assertRegex(css, r"\.kl-hero__back \{[^}]*max-width: none")

    def test_tekst_op_het_openingsscherm_staat_in_een_plaquette_en_de_knop_in_het_midden(self):
        html = Client().get("/voorbeeld/kerstmagie/", {"gelegenheid": "kerst"}).content.decode()
        text = re.search(r'<div class="kl-cover__text"[^>]*>(.*?)</div>', html, re.S).group(1)
        for part in ("kl-cover__kicker", "kl-cover__title", "kl-cover__hint"):
            self.assertIn(part, text)
        self.assertRegex(self.css(), r"\.kl-play \{[^}]*grid-row: 2")
        self.assertRegex(self.css(), r"\.kl-cover__text \{[^}]*grid-row: 3")

    def test_monogram_gebruikt_een_lichte_sluier(self):
        self.assertIn("rgba(240, 248, 255", self.css().split(".kl-closing__mono::after")[1].split("}")[0])

    def test_tekst_op_de_film_wordt_op_de_echte_pixels_gemeten(self):
        html = Client().get("/voorbeeld/kerstmagie/", {"gelegenheid": "kerst"}).content.decode()
        self.assertRegex(html, r'<div class="kl-cover__text" data-tekst-op-beeld>')
        self.assertTrue((Path(settings.BASE_DIR) / "e2e" / "kerstmagie-contrast.cjs").exists())


class KerstmagieKaartTests(TestCase):
    """De rijkere kaart: beelden uit de film, sneeuw met diepte tijdens het scrollen en de datum onder een ijslaag."""

    def html(self):
        return Client().get("/voorbeeld/kerstmagie/", {"gelegenheid": "kerst"}).content.decode()

    def test_scripts_staan_in_de_juiste_volgorde_zonder_inline_script(self):
        html = self.html()
        vooraf, effects = html.index("kerstmagie/v1/vooraf.js"), html.index("invitations/effects.js")
        self.assertLess(vooraf, effects, "vooraf.js moet vóór effects.js lopen")
        for name in ("snow.js", "kras.js", "intro.js"):
            self.assertIn(f"/static/designs/kerstmagie/v1/{name}", html)
        self.assertEqual(len(re.findall(r"<script>", html)), 1)   # alleen het vaste startscript (CSP)

    def test_de_datum_staat_in_de_pagina_en_krijgt_pas_met_script_een_ijslaag(self):
        html = self.html()
        block = re.search(r'<div class="kl-date[^"]*"[^>]*data-kl-date[^>]*>(.*?)</div>', html, re.S).group(1)
        self.assertIn("kl-date__day", block)
        self.assertNotIn("kl-frost", html)   # de ijslaag wordt door kras.js gemaakt, niet door de server

    def test_beelden_uit_de_film_en_alle_bestaande_onderdelen(self):
        html = self.html()
        for name in ("pano", "gloed", "trein", "plein", "tussen", "rivier", "water"):
            self.assertIn(f"media/{name}.webp", html, name)
        for part in ("kl-countdown", "kl-location", "Route plannen", "kl-rsvp", 'id="aanmelden"', "kl-program", "kl-contact", "kl-closing", "kl-arch"):
            self.assertIn(part, html, part)
        self.assertNotIn("kl-band", html)

    def test_sneeuw_en_ijslaag_hebben_de_uitwegen(self):
        snow = (DESIGN / "snow.js").read_text(encoding="utf-8")
        for needle in ("fx-motion", "fx-paused", "visibilitychange", "devicePixelRatio", "scroll"):
            self.assertIn(needle, snow, needle)
        kras = (DESIGN / "kras.js").read_text(encoding="utf-8")
        for needle in ("fx-motion", "sessionStorage", "Onthul de datum", "pointerdown", "catch (error)", "kl-frost"):
            self.assertIn(needle, kras, needle)
        css = (DESIGN / "style.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.fx \.inv-main \{ z-index: auto; \}")
        self.assertRegex(css, r"\.kl-snow \{[^}]*z-index: 3")
        self.assertRegex(css, r"\.kl-layer, \.kl-section \{[^}]*z-index: 4")
        self.assertIn("prefers-reduced-motion", css.split(".kl-frost {")[1])

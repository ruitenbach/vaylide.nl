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
                            ("trein.webp", 150_000), ("plein.webp", 150_000), ("sneeuwvlok.webp", 200_000)):
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

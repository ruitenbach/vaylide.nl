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
MEDIA_LIMIETEN = {"opening.mp4": 3_500_000, "opening.webm": 3 * 1024 * 1024 - 1, "poster.webp": 300_000, "end.webp": 300_000, "band.webp": 150_000,
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
            self.assertEqual(template.current_version.film["webm"].rsplit("/", 1)[-1], "opening.webm", f"{slug}: reserve voor browsers zonder H.264")

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
            beschikbaar = set(manifest(slug)["palettes"][0]["vars"]) | {"--fk-surround", "--fk-grain", "--fk-glass", "--fk-sky-l", "--fk-sky-r", "--fk-sky-t", "--fk-sky-h", "--fk-dz"}
            self.assertEqual(gebruikt - beschikbaar, set(), slug)
            self.assertNotRegex(css, r"__[A-Z]+__", slug)


class IntrokaartNietOpenbaarTests(VaylideTestCase):
    """Eindcontrole: de vijf kaarten komen nergens openbaar voor en zijn niet te bestellen; beheerders kunnen alleen het voorbeeld bekijken."""

    def setUp(self):
        self.staff = self.make_staff()
        self.klant = self.make_customer()

    def clients(self):
        for gebruiker in (None, self.klant, self.staff):
            client = Client()
            if gebruiker is not None:
                client.force_login(gebruiker)
            yield gebruiker, client

    def test_niet_in_de_collectie_de_ontwerppagina_de_zoekresultaten_en_de_sitemap(self):
        for gebruiker, client in self.clients():
            collectie_pagina = client.get("/ontwerpen/").content.decode()
            sitemap = client.get("/sitemap.xml").content.decode()
            for slug, gelegenheid in KAARTEN.items():
                self.assertNotIn(f"/ontwerpen/{slug}/", collectie_pagina, slug)
                self.assertNotIn(slug, sitemap, slug)
                self.assertEqual(client.get(f"/ontwerpen/{slug}/").status_code, 404, slug)
                zoek = client.get("/zoeken/", {"q": Template.objects.get(slug=slug).name}).content.decode()
                self.assertNotIn(f"/ontwerpen/{slug}/", zoek, slug)
                self.assertNotIn(f"/voorbeeld/{slug}/", zoek, slug)

    def test_niet_te_kiezen_in_de_bestelroute_ook_niet_voor_beheerders(self):
        from invitations.models import Invitation

        for gebruiker, client in self.clients():
            voor = Invitation.objects.count()
            for slug, gelegenheid in KAARTEN.items():
                self.assertNotContains(client.get("/maken/", {"gelegenheid": gelegenheid}), Template.objects.get(slug=slug).name, msg_prefix=slug)
                client.post("/maken/", {"occasion": gelegenheid, "template": slug})
            self.assertEqual(Invitation.objects.count(), voor, f"er is een uitnodiging aangemaakt op een verborgen kaart ({gebruiker})")

    def test_voorbeeld_alleen_voor_beheerders_en_nooit_gecachet(self):
        for slug, gelegenheid in KAARTEN.items():
            for gebruiker, client in self.clients():
                antwoord = client.get(f"/voorbeeld/{slug}/", {"gelegenheid": gelegenheid})
                if gebruiker is self.staff:
                    self.assertEqual(antwoord.status_code, 200, slug)
                    self.assertEqual(antwoord["Cache-Control"], "private, no-store", slug)
                else:
                    self.assertEqual(antwoord.status_code, 404, f"{slug} ({gebruiker})")


class PremiumLaagTests(VaylideTestCase):
    """Premium laag (18 oktober 2026): Bloesemmeer met de hand (voorbeeld), de andere vier met tools/introkaarten/premium_laag.py.
    Alleen decoratief, alleen onder .fx-motion, achter de tekst."""

    GENERATOR = ("zijden-gordijn", "bloesemwaaier", "kerstsprookje", "gouden-poort")

    def bestanden(self, slug):
        return ((ontwerp(slug) / "invitation.html").read_text(encoding="utf-8"), (ontwerp(slug) / "style.css").read_text(encoding="utf-8"))

    def test_alle_vijf_hebben_de_laag_en_de_scrollreactie(self):
        for slug in KAARTEN:
            html, css = self.bestanden(slug)
            self.assertIn('<div class="fk-fx" aria-hidden="true">', html, slug)
            self.assertIn('<div class="fx-slot" data-fx-slot="page" aria-hidden="true">', html, f"{slug}: eigen deeltjeslaag in de kop")
            self.assertIn(".fk-water", css, slug)
            self.assertIn("scrollwind", manifest(slug)["effects"]["extra"], slug)
            self.assertNotIn("tabindex", html[html.index("fk-fx"):html.index("fk-sky")], slug)

    def test_de_laag_is_decoratief_en_staat_achter_de_tekst(self):
        for slug in KAARTEN:
            _, css = self.bestanden(slug)
            premium = css[css.index("Premium laag"):]
            self.assertIn(".fk-fx { display: none; }", premium, slug)
            self.assertIn(".fx-motion .fk-fx { display: block;", premium, slug)
            self.assertIn("pointer-events: none", premium, slug)
            # 'animation' zet de speelstand terug: een laatste regel zet hem voor alle lagen (ook ::before) opnieuw, zodat de pauzeknop werkt.
            self.assertRegex(premium, r"\.fx-motion \.fk-fx[^{]*\{[^}]*animation-play-state: var\(--fx-play, running\);", slug)
            # Geen zware technieken op bewegende lagen.
            self.assertNotIn("mix-blend-mode", premium, slug)
            self.assertNotIn("filter:", premium, slug)

    def test_eigen_identiteit_per_kaart_geen_rozen_of_bloesem_bij_kerst_en_spaarzaam_bij_de_poort(self):
        sfeer = {slug: manifest(slug)["effects"]["sfeer"] for slug in KAARTEN}
        self.assertEqual(sfeer["kerstsprookje"], "sneeuw")
        self.assertEqual(sfeer["bloesemmeer"], sfeer["bloesemwaaier"], "bloesemkaarten")
        self.assertEqual({sfeer["zijden-gordijn"], sfeer["gouden-poort"]}, {"blaadjes"})
        dichtheid = {}
        for slug in self.GENERATOR:
            m = re.search(r"--fx-density: ([\d.]+)", self.bestanden(slug)[1])
            self.assertIsNotNone(m, slug)
            dichtheid[slug] = float(m.group(1))
        self.assertLessEqual(dichtheid["gouden-poort"], 0.2, "heel spaarzame blaadjes")
        self.assertLessEqual(dichtheid["zijden-gordijn"], 0.35, "enkele rozenblaadjes")
        self.assertEqual(len(set(dichtheid.values())), 4, "elke kaart heeft een eigen dichtheid")
        # De lichtplekken verschillen per kaart (eigen beeld).
        plekken = {slug: re.findall(r'class="fk-glow" style="--x:([\d.]+)%;--y:([\d.]+)%', self.bestanden(slug)[0]) for slug in self.GENERATOR}
        self.assertEqual(len({tuple(v) for v in plekken.values()}), 4)
        self.assertIn("fk-sheen", self.bestanden("gouden-poort")[0], "architectuur: lichtbaan over de bogen")
        self.assertNotIn("fk-sheen", self.bestanden("zijden-gordijn")[0])

    def test_de_generator_is_herhaalbaar(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location("premium_laag", Path(settings.BASE_DIR) / "tools" / "introkaarten" / "premium_laag.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for slug in self.GENERATOR:
            k = dict(module.KAARTEN[slug], slug=slug)
            html, css = self.bestanden(slug)
            self.assertIn(module.html_blok(k).strip(), html, slug)
            self.assertIn(module.css_blok(k).strip(), css, slug)
            self.assertEqual(html.count(module.BEGIN_HTML), 1, slug)
            self.assertEqual(css.count(module.BEGIN_CSS), 1, slug)

    def test_de_kaarten_blijven_verborgen(self):
        for slug in KAARTEN:
            self.assertEqual(collectie.groep(slug), "C", slug)
            self.assertFalse(Template.objects.get(slug=slug).is_active, slug)


class KnopRuimteTests(VaylideTestCase):
    """De pauze- en muziekknop zweven in de hoeken; de plaatsregel in de kop blijft daartussen (alleen op smalle schermen)."""

    ONTWERPEN = {"zijden-gordijn": "fk", "bloesemmeer": "fk", "bloesemwaaier": "fk", "kerstsprookje": "fk", "gouden-poort": "fk", "rozenboog": "rb"}

    def test_de_plaatsregel_blijft_tussen_de_knoppen(self):
        for slug, voorvoegsel in self.ONTWERPEN.items():
            css = (Path(settings.BASE_DIR) / "designs" / slug / "v1" / "style.css").read_text(encoding="utf-8")
            self.assertEqual(css.count("/* knop-ruimte begin */"), 1, slug)
            self.assertIn("@media (max-width: 480px) { .%s-meta { padding-inline: 4.25rem; } }" % voorvoegsel, css, slug)

    def test_het_sjabloon_heeft_dezelfde_regel(self):
        css = (Path(settings.BASE_DIR) / "tools" / "introkaarten" / "sjabloon" / "style.css").read_text(encoding="utf-8")
        self.assertEqual(css.count("/* knop-ruimte begin */"), 1)
        self.assertIn(".fk-meta { padding-inline: 4.25rem; }", css)

"""Aurora Nocturne: de special met een filmische opening (designs/aurora-nocturne/v1).

Deze tests bewaken de afspraken uit het ontwerp: een special met eigen samenvatting, alle beelden aanwezig en licht, één stofcanvas,
geen losse lampjes als elementen, alleen het vaste inline script (CSP), beweging alleen onder .fx-motion en een kop die de gegevens van de
uitnodiging toont. Het beoordelen van de film zelf gebeurt met e2e/aurora_nocturne.cjs.
"""
import json
import re
from pathlib import Path

from django.conf import settings
from django.test import Client, TestCase

from catalog.effects import effect_card_label, effect_summary
from catalog.models import Template

DIR = Path(settings.BASE_DIR) / "designs" / "aurora-nocturne" / "v1"
STATIC = Path(settings.BASE_DIR) / "static"
LICHTKAARTEN = ["entree", "zij", "kroon", "lampjes", "kaarsen"]
PALETTEN = ["nacht", "parel", "roze", "salie"]


def manifest():
    return json.loads((DIR / "manifest.json").read_text(encoding="utf-8"))


class AuroraManifestTests(TestCase):
    def test_is_a_special_for_weddings_and_engagements(self):
        data = manifest()
        self.assertEqual(data["slug"], "aurora-nocturne")
        self.assertTrue(data["special"])
        self.assertEqual(data["envelope_mode"], "built_in")
        self.assertTrue({"bruiloft", "verloving"} <= set(data["occasions"]))
        template = Template.objects.get(slug="aurora-nocturne")
        self.assertTrue(template.special)

    def test_has_own_summary_instead_of_particles(self):
        effects = manifest()["effects"]
        self.assertEqual((effects["sfeer"], effects["knal"]), ("geen", "geen"))   # geen deeltjes-canvassen van het platform
        self.assertTrue(effect_summary(effects).endswith("."))
        self.assertEqual(effect_card_label(effects), "filmische opening")
        # Bestaande ontwerpen veranderen niet: zonder eigen tekst geldt de oude regel.
        self.assertEqual(effect_summary({"sfeer": "geen", "knal": "geen", "viering": "geen", "namen": "zacht", "onthul": "zacht"}), "")

    def test_listed_under_specials_only(self):
        client = Client()
        self.assertContains(client.get("/ontwerpen/", {"categorie": "specials"}), "Aurora Nocturne")


class AuroraAssetTests(TestCase):
    def test_all_images_exist_and_stay_light(self):
        namen = ["lucht", "aurora-a", "aurora-b", "ver", "mist", "paviljoen", "voor-l", "voor-r", "hoek", "slinger"] + [f"licht-{k}" for k in LICHTKAARTEN]
        self.assertTrue((DIR / "img" / "korrel.webp").exists())
        for palet in PALETTEN:
            totaal = 0
            for naam in namen:
                pad = DIR / "img" / palet / f"{naam}.webp"
                self.assertTrue(pad.exists(), f"{palet}/{naam}")
                totaal += pad.stat().st_size
            # Een bezoeker laadt maar één set: die blijft samen met de korrel onder 1 MB.
            self.assertLess(totaal + (DIR / "img" / "korrel.webp").stat().st_size, 1_000_000, f"de beelden van {palet} horen onder 1 MB te blijven")

    def test_gsap_is_shipped_with_the_project(self):
        for naam in ("gsap.min.js", "ScrollTrigger.min.js"):
            self.assertTrue((STATIC / "vendor" / "gsap" / naam).exists(), naam)

    def test_does_not_borrow_files_from_winterlicht(self):
        for naam in ("invitation.html", "style.css", "aurora-nocturne.js"):
            self.assertNotIn("winterlicht", (DIR / naam).read_text(encoding="utf-8").lower(), naam)


class AuroraRenderTests(TestCase):
    def setUp(self):
        self.html = Client().get("/voorbeeld/aurora-nocturne/", {"gelegenheid": "bruiloft"}).content.decode()

    def test_cover_and_hero_layers(self):
        self.assertIn('data-cover', self.html)
        self.assertIn('data-duration="3000"', self.html)
        self.assertIn("Open uitnodiging", self.html)
        self.assertIn("vendor/gsap/gsap.min.js", self.html)
        self.assertIn("aurora-nocturne/v1/aurora-nocturne.js", self.html)
        for naam in LICHTKAARTEN:
            self.assertIn(f"an-licht--{naam}", self.html)
        for laag in ("lucht", "ver", "mist-a", "pav", "mist-b", "voor-l", "voor-r"):
            self.assertIn(f"an-l--{laag}", self.html)

    def test_only_one_canvas_and_no_lamp_elements(self):
        self.assertEqual(len(re.findall(r"<canvas\b", self.html)), 1)
        self.assertNotIn('data-fx-slot="cover"', self.html)
        self.assertEqual(len(re.findall(r'class="an-licht ', self.html)), len(LICHTKAARTEN))   # vijf lichtkaarten, geen tientallen lampjes

    def test_csp_one_inline_script_and_no_inline_style_blocks(self):
        self.assertEqual(len(re.findall(r"<script>", self.html)), 1)
        self.assertEqual(len(re.findall(r"<style\b", self.html)), 0)

    def test_hero_shows_the_invitation_data_and_stays_private(self):
        self.assertIn("an-namen", self.html)
        self.assertIn("Sanne", self.html)
        self.assertIn("Daan", self.html)
        self.assertIn('name="robots" content="noindex', self.html)

    def test_every_class_used_by_the_script_exists_in_the_template(self):
        js = (DIR / "aurora-nocturne.js").read_text(encoding="utf-8")
        html = (DIR / "invitation.html").read_text(encoding="utf-8")
        dynamisch = {"an-gsap", "an-rust", "an-weg"}
        for naam in set(re.findall(r'"[^"\n]*?\.(an-[a-z0-9_-]+)', js)):
            if naam in dynamisch:
                continue
            self.assertIn(naam, html, f"{naam} komt in het script voor maar niet in het sjabloon")

    def test_ambient_loops_only_with_motion_on(self):
        css = (DIR / "style.css").read_text(encoding="utf-8")
        for regel in css.splitlines():
            if "animation:" in regel and "!important" not in regel and "@keyframes" not in regel:
                self.assertIn(".fx-motion", regel, regel.strip()[:80])
        self.assertIn("animation-play-state: var(--fx-play, running)", css)

    def test_direct_open_and_reduced_motion_have_static_end_state(self):
        css = (DIR / "style.css").read_text(encoding="utf-8")
        # De lichtkaarten en de tekst zijn zonder script gewoon zichtbaar: in de opmaak staat nergens opacity: 0 op de eindstand.
        self.assertNotRegex(css, r"\.an-licht[^{]*\{[^}]*opacity:\s*0\s*;")
        self.assertNotRegex(css, r"\.an-naam[^{]*\{[^}]*opacity:\s*0\s*;")
        self.assertIn("prefers-reduced-motion", css)


def _luminantie(hex_kleur):
    r, g, b = (int(hex_kleur.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    def f(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _contrast(a, b):
    hoog, laag = sorted((_luminantie(a), _luminantie(b)), reverse=True)
    return (hoog + 0.05) / (laag + 0.05)


class AuroraPaletteTests(TestCase):
    def test_four_palettes_night_first_and_three_light(self):
        sleutels = [p["key"] for p in manifest()["palettes"]]
        self.assertEqual(sleutels, PALETTEN)

    def test_light_palettes_keep_text_readable(self):
        for palet in manifest()["palettes"][1:]:
            v = palet["vars"]
            paren = [("--an-ivoor", "--an-nacht-2"), ("--an-muted", "--an-nacht-2"), ("--an-goud", "--an-nacht-2"), ("--an-goud-2", "--an-nacht-2"),
                     ("--an-goud-ink", "--an-goud"), ("--an-ivoor", "--an-vlak"), ("--an-goud", "--an-vlak"), ("--an-goud-2", "--an-dek-1"),
                     ("--an-muted", "--an-dek-1"), ("--an-muted", "--an-vlak2"), ("--an-goud-2", "--an-vlak2")]
            for tekst, vlak in paren:
                self.assertGreaterEqual(_contrast(v[tekst], v[vlak]), 4.5, f"{palet['key']}: {tekst} op {vlak}")

    def test_every_palette_draws_its_own_scene(self):
        for palet in PALETTEN:
            html = Client().get("/voorbeeld/aurora-nocturne/", {"gelegenheid": "bruiloft", "kleur": palet}).content.decode()
            self.assertIn(f"aurora-nocturne/v1/img/{palet}/lucht.webp", html, palet)
            self.assertIn(f"aurora-nocturne/v1/img/{palet}/paviljoen.webp", html, palet)

    def test_every_color_used_by_the_stylesheet_is_defined_by_all_palettes(self):
        css = (DIR / "style.css").read_text(encoding="utf-8")
        gebruikt = set(re.findall(r"var\((--an-[a-z0-9-]+)", css))
        zelf = set(re.findall(r"(--an-[a-z0-9-]+)\s*:", css))   # in de opmaak zelf gezet (lettertypen)
        for palet in manifest()["palettes"][1:]:
            ontbreekt = {n for n in gebruikt - zelf if n not in palet["vars"]}
            # Variabelen met een terugvalwaarde in de opmaak (de nachtwaarde) hoeven niet overal te staan, behalve de kleuren die licht moeten zijn.
            kleur_nodig = {n for n in ontbreekt if re.search(r"var\(" + re.escape(n) + r"\s*\)", css)}
            self.assertFalse(kleur_nodig, f"{palet['key']} mist {sorted(kleur_nodig)}")


class AuroraVersieringTests(TestCase):
    """De rijke omlijsting: bloemenhoeken, bogen en waaier op het openingsscherm, hoeken en lampionnen in de kop, sierlijsten in de rest."""

    def setUp(self):
        self.html = Client().get("/voorbeeld/aurora-nocturne/", {"gelegenheid": "bruiloft", "kleur": "roze"}).content.decode()

    def test_cover_has_decor_and_a_smaller_envelope(self):
        for klasse in ("an-decor", "an-stralen", "an-bogen", "an-hoek--lb", "an-hoek--ro", "an-uitn", "an-dag"):
            self.assertIn(klasse, self.html, klasse)
        self.assertEqual(self.html.count("roze/hoek.webp"), 4 + 2 + 2 + 2)   # vier op het openingsscherm, twee in de kop, twee bij de datum, twee bij de afsluiting
        css = (DIR / "style.css").read_text(encoding="utf-8")
        breedte = int(re.search(r"--w: clamp\((\d+)px, min\((\d+)vw, (\d+)svh \* \.75\), (\d+)px\)", css).group(4))
        self.assertLessEqual(breedte, 220, "de envelop blijft klein ten opzichte van het scherm")

    def test_decor_is_hidden_from_assistive_technology(self):
        self.assertRegex(self.html, r'<div class="an-decor" aria-hidden="true">')
        self.assertRegex(self.html, r'<div class="an-hoeken" aria-hidden="true">')

    def test_body_sections_use_the_rich_layout(self):
        for klasse in ("an-datumboog", "an-programma", "an-sier", "an-paviljoen-icoon", "an-slinger", "an-kaart-wrap"):
            self.assertIn(klasse, self.html, klasse)

    def test_lanterns_only_rise_in_the_hero(self):
        js = (DIR / "aurora-nocturne.js").read_text(encoding="utf-8")
        self.assertIn('classList.contains("an-stofhaven")', js)
        self.assertIn("--an-lampion", js)
        for palet in manifest()["palettes"]:
            self.assertIn("--an-lampion", palet["vars"], palet["key"])

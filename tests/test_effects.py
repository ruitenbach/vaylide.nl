"""Effecten op de uitnodigingen: keuzes per ontwerp, weergave, pauzeknop, contrast en website."""
import copy
import json
import re
from pathlib import Path

from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client, TestCase

from catalog.atelier import contrast
from catalog.effects import EFFECT_OPTIONS, effect_card_label, effect_summary, effect_view, effects_errors, shine_color
from catalog.models import Template
from catalog.seed import DesignError, validate_manifest
from invitations.demo import demo_content
from invitations.render import RenderOptions, build_view


def manifests():
    root = Path(settings.BASE_DIR) / "designs"
    return {p.parent.parent.name: json.loads(p.read_text(encoding="utf-8")) for p in sorted(root.glob("*/v1/manifest.json"))}


class EffectChoicesTests(TestCase):
    def test_every_design_has_valid_effects(self):
        found = manifests()
        self.assertEqual(len(found), 34)
        for slug, data in found.items():
            self.assertIn("effects", data, slug)
            self.assertEqual(effects_errors(data["effects"]), [], slug)

    def test_unknown_effect_is_refused_when_reading_designs(self):
        self.assertTrue(effects_errors({"sfeer": "vuurwerk", "knal": "geen", "viering": "geen", "namen": "zacht", "onthul": "omhoog"}))
        self.assertTrue(effects_errors({"sfeer": "geen", "knal": "geen", "viering": "geen", "namen": "zacht", "onthul": "omhoog", "extra": ["knipper"]}))
        self.assertTrue(effects_errors("blaadjes"))
        path = Path(settings.BASE_DIR) / "designs" / "rozentuin" / "v1" / "manifest.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["effects"] = dict(data["effects"], knal="vuurwerk")
        with self.assertRaises(DesignError):
            validate_manifest(path, data)

    def test_view_settings_become_classes_and_attributes(self):
        view = effect_view({"sfeer": "sterren", "knal": "sterren", "viering": "sterren", "namen": "folie", "onthul": "zoom",
                            "extra": ["kenburns", "tik"]})
        self.assertEqual(view["sfeer"], "sterren")
        self.assertTrue(view["tik"])
        self.assertEqual(view["classes"], "fx fx-namen-folie fx-onthul-zoom fx-kenburns")
        self.assertEqual(effect_view(None), {})
        self.assertEqual(effect_view({"sfeer": "onbekend"}), {})

    def test_same_options_for_burst_and_celebration(self):
        self.assertEqual(EFFECT_OPTIONS["knal"], EFFECT_OPTIONS["viering"])
        self.assertIn("geen", EFFECT_OPTIONS["sfeer"])


class EffectRenderTests(TestCase):
    def render(self, slug, occasion=None):
        template = Template.objects.get(slug=slug)
        occasion = occasion or template.occasions[0]
        return Client().get(f"/voorbeeld/{slug}/", {"gelegenheid": occasion})

    def test_demo_pages_load_the_effects_and_the_pause_button(self):
        for slug in ("rozentuin", "gatsby", "confetti", "liefde-op-papier", "avondgoud", "puur-moment"):
            response = self.render(slug)
            html = response.content.decode()
            effects = manifests()[slug]["effects"]
            self.assertIn(f'data-fx-sfeer="{effects["sfeer"]}"', html, slug)
            self.assertIn(f'data-fx-knal="{effects["knal"]}"', html, slug)
            self.assertIn("/static/invitations/effects.css", html, slug)
            self.assertIn("/static/invitations/effects.js", html, slug)
            self.assertIn('data-fx-slot="page"', html, slug)
            self.assertIn('data-fx-slot="cover"', html, slug)
            # De knop staat verborgen tot het script draait, en heeft een vaste naam met een aan/uit-stand.
            self.assertRegex(html, r'<button type="button" class="fx-toggle" data-fx-toggle aria-pressed="false" hidden>', slug)
            self.assertIn("Beweging<span class=\"visually-hidden\"> stilzetten</span>", html, slug)
            # Geen inline scripts naast het vaste startscript (CSP).
            self.assertEqual(len(re.findall(r"<script>", html)), 1, slug)

    def test_every_design_renders_with_its_effects(self):
        for template in Template.objects.all():
            response = self.render(template.slug)
            self.assertEqual(response.status_code, 200, template.slug)
            self.assertContains(response, 'class="fx-toggle"', msg_prefix=template.slug)
            self.assertContains(response, "data-fx-origin", msg_prefix=template.slug)

    def test_design_without_effects_block_renders_without_effects(self):
        template = Template.objects.get(slug="rozentuin")
        version = template.current_version
        version.manifest = copy.deepcopy(version.manifest)
        del version.manifest["effects"]
        view = build_view(occasion="bruiloft", content=demo_content("rozentuin", "bruiloft"), overrides={},
                          template_version=version, options=RenderOptions(mode="demo"))
        self.assertEqual(view["effects"], {})
        html = render_to_string(version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
        self.assertNotIn("effects.js", html)
        self.assertNotIn("fx-toggle", html)
        self.assertNotIn("data-fx-sfeer", html)

    def test_avondgoud_no_longer_loads_its_own_script(self):
        html = self.render("avondgoud").content.decode()
        self.assertNotIn("sparkle.js", html)
        self.assertFalse((Path(settings.BASE_DIR) / "designs" / "avondgoud" / "v1" / "sparkle.js").exists())


class ShineContrastTests(TestCase):
    """De lichtstreep over de namen ('folie') houdt minstens 3:1 contrast (grote tekst)."""

    def test_shine_color_keeps_contrast(self):
        cases = [("#1D1B16", "#FAF6EC", "#7E5F27"), ("#F3EBDD", "#121212", "#D4B36A"), ("#931A2E", "#FBF3F3", "#931A2E"),
                 ("#26211D", "#FBF8F2", "#8E6A3B"), ("#EEF8FF", "#07121F", "#37E2FF")]
        for fg, bg, accent in cases:
            self.assertGreaterEqual(contrast(shine_color(fg, bg, accent), bg), 3.2, (fg, bg))

    def test_folie_designs_have_a_shine_with_enough_contrast(self):
        from tools.atelier.ontwerpen import names_colors
        from tools.atelier.specs import DESIGNS

        checked = 0
        for spec in DESIGNS:
            if spec.get("effects", {}).get("namen") != "folie":
                continue
            data = manifests()[spec["slug"]]
            for pal_spec, pal in zip(spec["palettes"], data["palettes"]):
                fg, bg = names_colors(spec, pal_spec["colors"])
                shine = pal["vars"]["--fx-shine"]
                self.assertGreaterEqual(contrast(shine, bg), 3.0, f"{spec['slug']} {pal['key']}")
                checked += 1
        self.assertGreater(checked, 20)
        # Avondgoud: goud op de donkere achtergrond.
        for pal in manifests()["avondgoud"]["palettes"]:
            self.assertGreaterEqual(contrast(pal["vars"]["--ag-gold"], pal["vars"]["--ag-bg"]), 3.0, pal["key"])


class EffectWebsiteTests(TestCase):
    def test_design_page_describes_the_effects(self):
        response = Client().get("/ontwerpen/rozentuin/")
        self.assertContains(response, "<dt>Effecten</dt>")
        self.assertContains(response, "Dwarrelende bloemblaadjes en bij het openen een regen van bloemblaadjes.")
        self.assertContains(response, "Gasten kunnen de beweging met één tik stilzetten.")

    def test_cards_mention_the_effect(self):
        response = Client().get("/ontwerpen/")
        self.assertContains(response, "Envelop met lakzegel · bloemblaadjes")
        # Niet twee keer hetzelfde woord op een kaart.
        self.assertContains(response, '<span class="design-card__meta">Confetti</span>')
        self.assertNotContains(response, "Confetti · confetti")
        self.assertNotContains(response, "Sterrenhemel · sterrenhemel")

    def test_summaries_for_all_designs(self):
        for slug, data in manifests().items():
            text = effect_summary(data["effects"])
            self.assertTrue(text.endswith("."), slug)
            self.assertTrue(text[0].isupper(), slug)
            self.assertTrue(effect_card_label(data["effects"]), slug)
        self.assertEqual(effect_summary({"sfeer": "geen", "knal": "flits", "viering": "geen", "namen": "zacht", "onthul": "omhoog"}),
                         "Bij het openen een cameraflits.")


class CadeauTests(TestCase):
    """De cadeau-opening (Stipjes, Glitter & goud, Regenboog) en het effect 'cadeautjes'."""

    def test_gift_designs_render_the_gift_opening(self):
        for slug in ("stipjes", "glitter", "regenboog"):
            template = Template.objects.get(slug=slug)
            html = Client().get(f"/voorbeeld/{slug}/", {"gelegenheid": template.occasions[0]}).content.decode()
            self.assertIn("a-cover--cadeau", html, slug)
            self.assertIn('data-fx-knal="cadeautjes"', html, slug)
            self.assertIn(">Pak het cadeau uit</a>", html, slug)
            # De doos zelf opent ook bij een tik, maar is geen extra tabstop en wordt niet voorgelezen.
            box = re.search(r'<div class="a-box[^"]*"[^>]*>', html).group(0)
            self.assertIn("data-open", box, slug)
            self.assertIn('aria-hidden="true"', box, slug)
            self.assertNotIn("href", box, slug)
            self.assertNotIn("tabindex", box, slug)
            self.assertIn("data-fx-origin", html, slug)

    def test_gift_options_and_texts(self):
        self.assertIn("cadeautjes", EFFECT_OPTIONS["sfeer"])
        self.assertIn("cadeautjes", EFFECT_OPTIONS["knal"])
        self.assertEqual(effect_summary({"sfeer": "cadeautjes", "knal": "cadeautjes", "viering": "cadeautjes", "namen": "pop", "onthul": "zoom"}),
                         "Vallende cadeautjes en bij het openen een plof en een fontein van cadeautjes.")
        self.assertEqual(manifests()["stipjes"]["opening_label"], "Cadeau om uit te pakken")
        self.assertEqual(manifests()["ballonfeest"]["effects"]["viering"], "cadeautjes")

    def test_collection_card_shows_the_gift(self):
        response = Client().get("/ontwerpen/")
        self.assertContains(response, "Cadeau om uit te pakken · cadeautjes")

"""Balzaal: envelop met lakzegel, de balzaal als beeldlagen (zaal, bruidspaar, bloemen) en de haarkleurkeuze.
De haarkleurkeuze verschijnt pas als alle negen combinaties als beeld bestaan (catalog/paar.py)."""
import re
from unittest import mock

from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client

from catalog import paar
from catalog.atelier import contrast
from catalog.effects import effects_errors
from catalog.models import Template
from invitations.demo import DESIGN_IMAGES, demo_content
from invitations.render import RenderOptions, build_view
from invitations.services import save_draft

from .helpers import VaylideTestCase

IMG = settings.BASE_DIR / "designs/balzaal/v1/img"


def _render(content, features=None, occasion="bruiloft"):
    version = Template.objects.get(slug="balzaal").current_version
    options = RenderOptions(mode="demo") if features is None else RenderOptions(mode="demo", features=features)
    view = build_view(occasion=occasion, content=content, overrides={}, template_version=version, options=options)
    return view, render_to_string(version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})


class BalzaalDesignTests(VaylideTestCase):
    def version(self):
        return Template.objects.get(slug="balzaal").current_version

    def test_manifest_colours_and_effects(self):
        data = self.version().manifest
        self.assertEqual(data["occasions"], ["bruiloft", "verloving"])
        self.assertEqual(effects_errors(data["effects"]), [])
        pairs = [("ink", "bg"), ("ink", "bg-2"), ("muted", "bg"), ("muted", "bg-2"), ("accent", "bg"), ("accent", "bg-2"),
                 ("gold-2", "bg"), ("gold-2", "bg-2"), ("accent-ink", "accent"), ("env-ink", "env"), ("env-ink", "page")]
        for palette in data["palettes"]:
            c = {k[5:]: v for k, v in palette["vars"].items() if k.startswith("--bz-")}
            for fg, bg in pairs:
                self.assertGreaterEqual(contrast(c[fg], c[bg]), 4.5, f"{palette['key']}: {fg} op {bg}")
            self.assertGreaterEqual(contrast(c["seal-ink"], c["seal-2"]), 3)
        self.assertEqual(len(DESIGN_IMAGES["balzaal"]), 5)

    def test_images_are_optimised_and_keep_transparency(self):
        from PIL import Image

        for name, limit in (("balzaal.webp", 260), ("balzaal-600.webp", 130), ("paar-bruin-blond.webp", 160),
                            ("paar-bruin-blond-560.webp", 80), ("bloemen.webp", 260), ("bloemen-600.webp", 130)):
            path = IMG / name
            self.assertLess(path.stat().st_size / 1024, limit, name)
        for name in ("paar-bruin-blond.webp", "bloemen.webp"):
            with Image.open(IMG / name) as im:
                self.assertEqual(im.mode, "RGBA", name)
                self.assertEqual(im.getchannel("A").getextrema()[0], 0, name)  # echt doorzichtig
        with Image.open(IMG / "balzaal.webp") as im:
            self.assertAlmostEqual(im.width / im.height, 941 / 1672, places=3)  # niet uitgerekt

    def test_demo_layers_text_and_envelope(self):
        for kleur in ("ivoor", "hemelsblauw"):
            html = Client().get(f"/voorbeeld/balzaal/?kleur={kleur}").content.decode()
            self.assertIn('class="bz-env"', html)
            self.assertIn('class="bz-zegel fx-pulse"', html)
            self.assertIn('href="#uitnodiging"', html)  # opent ook zonder JavaScript
            self.assertIn("designs/balzaal/v1/img/balzaal-600.webp", html)
            self.assertIn("designs/balzaal/v1/img/paar-bruin-blond-560.webp", html)
            self.assertIn("designs/balzaal/v1/img/bloemen-600.webp", html)
            self.assertIn('data-paar="bruin-blond"', html)
            self.assertIn("fictieve personen", html)
            self.assertIn("designs/balzaal/v1/balzaal.js", html)
            self.assertNotIn("url(#", html)
            self.assertNotIn("{#", html)
            self.assertEqual(len(re.findall(r"<script>", html)), 1)

    def test_names_date_and_venue_are_real_text(self):
        content = demo_content("balzaal", "bruiloft")
        content["names"] = {"partner_1": "Lieke", "partner_2": "Thijs"}
        content["venue_name"] = "Kasteel Testhof"
        view, html = _render(content)
        hero = html[html.index('class="bz-hero"'):html.index('class="bz-body"')]
        self.assertIn("Lieke", hero)
        self.assertIn("Thijs", hero)
        self.assertIn("Kasteel Testhof", hero)
        self.assertIn(view["date_numeric"], hero)
        self.assertIn('id="aanmelden"', html)

    def test_seal_follows_the_package(self):
        content = demo_content("balzaal", "bruiloft")
        for features, personal in (([], False), (["zegel"], True)):
            view, html = _render(content, features)
            cover = html[html.index('class="bz-zegel'):html.index("bz-cover__onder")]
            self.assertEqual("seal-motief" not in cover, personal)

    def test_motion_only_with_motion_on(self):
        css = (settings.BASE_DIR / "designs/balzaal/v1/style.css").read_text(encoding="utf-8")
        rules = re.findall(r"^[^@\n][^{\n]*\{[^}\n]*animation:[^}\n]*infinite[^}\n]*\}", css, flags=re.M)
        self.assertGreaterEqual(len(rules), 3)
        for rule in rules:
            self.assertIn(".fx-motion", rule, rule)
            self.assertIn("animation-play-state: var(--fx-play, running)", rule, rule)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        js = (settings.BASE_DIR / "designs/balzaal/v1/balzaal.js").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: reduce", js)

    def test_in_the_collection_under_specials(self):
        response = Client().get("/ontwerpen/?gelegenheid=bruiloft")
        self.assertNotIn("balzaal", [c["template"].slug for c in response.context["cards"]])  # niet tussen de gewone kaarten
        self.assertIn("balzaal", [c["template"].slug for c in response.context["special_cards"]])
        specials = Client().get("/ontwerpen/?categorie=specials")
        self.assertEqual(specials.context["cards"], [])
        self.assertContains(specials, 'class="design-card__special"')
        self.assertContains(Client().get("/ontwerpen/balzaal/"), "Envelop met lakzegel")


class HairColourTests(VaylideTestCase):
    def version(self):
        return Template.objects.get(slug="balzaal").current_version

    def test_choice_hidden_until_all_nine_images_exist(self):
        version = self.version()
        self.assertFalse(paar.choice_enabled(version))
        self.assertEqual(len(paar.missing(version)), 8)
        self.assertNotIn(("bruin", "blond"), paar.missing(version))
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer, template="balzaal")
        client = Client()
        client.force_login(customer)
        page = client.get(f"/maken/{inv.uid}/stijl/")
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, "Haarkleur man")

    def test_with_all_images_the_choice_works_and_is_saved(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer, template="balzaal")
        client = Client()
        client.force_login(customer)
        with mock.patch("catalog.paar._exists", return_value=True):
            page = client.get(f"/maken/{inv.uid}/stijl/")
            self.assertContains(page, "Haarkleur man")
            self.assertContains(page, "Haarkleur vrouw")
            html = page.content.decode()
            self.assertRegex(html, r'name="haar_man" value="bruin"[^>]*checked')   # standaard: man bruin
            self.assertRegex(html, r'name="haar_vrouw" value="blond"[^>]*checked')  # standaard: vrouw blond
            data = {"palette": "ivoor", "opening": "on", "haar_man": "zwart", "haar_vrouw": "bruin", "rev": inv.draft_rev, "actie": "volgende"}
            client.post(f"/maken/{inv.uid}/stijl/", data)
            inv.refresh_from_db()
            self.assertEqual(inv.draft_content["style"]["haar"], {"man": "zwart", "vrouw": "bruin"})
            view, html = _render(inv.draft_content)
            self.assertIn('data-paar="zwart-bruin"', html)
            self.assertIn("scene-zwart-bruin-600.webp", html)
        # Zonder de beelden valt het ontwerp terug op het standaardpaar; de keuze blijft wel bewaard.
        view, html = _render(inv.draft_content)
        self.assertIn('data-paar="bruin-blond"', html)
        self.assertEqual(inv.draft_content["style"]["haar"], {"man": "zwart", "vrouw": "bruin"})

    def test_unknown_colour_falls_back_to_default(self):
        content = demo_content("balzaal", "bruiloft")
        content["style"]["haar"] = {"man": "paars", "vrouw": "<script>"}
        with mock.patch("catalog.paar._exists", return_value=True):
            view, html = _render(content)
        self.assertEqual((view["paar"]["man"], view["paar"]["vrouw"]), ("bruin", "blond"))

    def test_other_designs_have_no_couple_layer(self):
        version = Template.objects.get(slug="liefde-op-papier").current_version
        self.assertIsNone(paar.view(version, {}))
        self.assertFalse(paar.choice_enabled(version))


class HairChoiceSurvivesSaveTests(VaylideTestCase):
    def test_saving_other_steps_keeps_the_choice(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer, template="balzaal")
        content = dict(inv.draft_content)
        content["style"] = dict(content["style"], haar={"man": "blond", "vrouw": "zwart"})
        inv = save_draft(inv, expected_rev=inv.draft_rev, content=content, user=customer)
        content = dict(inv.draft_content)
        content["welcome_text"] = "Andere tekst"
        inv = save_draft(inv, expected_rev=inv.draft_rev, content=content, user=customer)
        self.assertEqual(inv.draft_content["style"]["haar"], {"man": "blond", "vrouw": "zwart"})

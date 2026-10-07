"""Atelier-ontwerpen: 30 ontwerpen (5 per gelegenheid) met geldige opbouw, leesbare kleuren en een werkend voorbeeld."""
import json
from collections import Counter

from django.conf import settings
from django.contrib.staticfiles import finders
from django.template.loader import render_to_string
from django.test import Client

from catalog.atelier import OPENING_LABELS, atelier_errors, palette_colors, palette_problems
from catalog.models import Template
from catalog.occasions import OCCASIONS
from invitations.demo import DESIGN_IMAGES, demo_content
from invitations.render import RenderOptions, build_view

from invitations.models import Invitation

from .helpers import VaylideTestCase, future_date, toon_verborgen_ontwerpen

LONG_NAMES = {
    "bruiloft": {"partner_1": "Maximiliaan-Alexander van den Boogaard", "partner_2": "Ernestina"},
    "verloving": {"partner_1": "Maximiliaan-Alexander van den Boogaard", "partner_2": "Ernestina"},
    "verjaardag": {"person_name": "Maximiliaan-Alexander van den Boogaard", "age": "50"},
    "jubileum": {"honorees": "Maximiliaan-Alexander & Ernestina van den Boogaard", "years": "25"},
    "babyshower": {"parents": "Maximiliaan-Alexander & Ernestina", "baby_name": ""},
    "zakelijk": {"event_title": "Internationale relatiedag voor partners", "organization": "Voorbeeld BV", "years": ""},
    "kerst": {"family": "Familie Maximiliaan-Alexander van den Boogaard", "members": ""},
}


def atelier_manifests():
    for path in sorted((settings.BASE_DIR / "designs").glob("*/v*/manifest.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if "atelier" in data:
            yield path, data


class AtelierCollectionTests(VaylideTestCase):
    def test_thirty_designs_five_per_occasion(self):
        toon_verborgen_ontwerpen()
        manifests = [data for _, data in atelier_manifests()]
        self.assertEqual(len(manifests), 32)
        primary = Counter(data["occasions"][0] for data in manifests)
        # Kerst heeft een eigen, volledig ontworpen kaart (Winterlicht) en twee Atelier-ontwerpen (Ho ho ho, Sneeuwpret).
        self.assertEqual(primary, Counter({occasion: (2 if occasion == "kerst" else 5) for occasion in OCCASIONS}))
        # Allemaal ingelezen, zichtbaar en met de Atelier-opbouw als huidige versie.
        for data in manifests:
            template = Template.objects.get(slug=data["slug"])
            self.assertTrue(template.is_active, data["slug"])
            self.assertEqual(template.current_version.manifest["atelier"], data["atelier"])
            self.assertEqual(template.current_version.template_path, f"{data['slug']}/v1/invitation.html")

    def test_manifests_are_complete_and_colours_readable(self):
        for path, data in atelier_manifests():
            slug = data["slug"]
            self.assertEqual(atelier_errors(data["atelier"]), [], slug)
            self.assertEqual(data["opening_label"], OPENING_LABELS[data["atelier"]["opening"]], slug)
            self.assertIn('{% extends "_atelier/v1/base.html" %}', (path.parent / "invitation.html").read_text(encoding="utf-8"), slug)
            self.assertGreaterEqual(len(data["palettes"]), 3, slug)
            for palette in data["palettes"]:
                self.assertEqual(palette_problems(palette_colors(palette), data["atelier"]), [], f"{slug}/{palette['key']}")
            # Eigen kaartbeeld voor de collectie en eigen voorbeeldbeelden.
            self.assertTrue(finders.find(f"img/designs/{slug}.webp"), slug)
            self.assertEqual(len(DESIGN_IMAGES[slug]), 5, slug)
            for name in DESIGN_IMAGES[slug]:
                self.assertTrue(finders.find(f"img/demo/{name}.webp") and finders.find(f"img/demo/{name}-1000.webp"), name)

    def test_contrast_check_catches_unreadable_colours(self):
        colours = {"bg": "#FFFFFF", "surface": "#FFFFFF", "ink": "#222222", "muted": "#BBBBBB", "accent": "#8E6A3B", "accent_ink": "#FFFFFF"}
        problems = palette_problems(colours)
        self.assertEqual(len(problems), 2)
        self.assertIn("gedempte tekst op achtergrond", problems[0])


class AtelierRenderTests(VaylideTestCase):
    def test_every_design_renders_for_each_occasion_and_colour(self):
        toon_verborgen_ontwerpen()
        for template in Template.objects.filter(current_version__manifest__has_key="atelier"):
            atelier = template.current_version.manifest["atelier"]
            for occasion in template.occasions:
                response = Client().get(f"/voorbeeld/{template.slug}/", {"gelegenheid": occasion})
                self.assertEqual(response.status_code, 200, f"{template.slug}/{occasion}")
                html = response.content.decode()
                self.assertIn(f"a-cover--{atelier['opening']}", html)
                self.assertIn(f"a-hero-{atelier['hero']}", html)
                self.assertIn("designs/_atelier/v1/atelier.css", html)
                self.assertIn(f"designs/{template.slug}/v1/style.css", html)
                self.assertIn('id="uitnodiging"', html)
            last = template.current_version.palettes[-1]
            response = Client().get(f"/voorbeeld/{template.slug}/", {"kleur": last["key"]})
            first_var, first_value = next(iter(last["vars"].items()))
            self.assertContains(response, f"{first_var}:{first_value};", msg_prefix=template.slug)

    def test_long_names_get_smaller_type_in_every_design(self):
        for template in Template.objects.filter(current_version__manifest__has_key="atelier"):
            occasion = template.occasions[0]
            content = demo_content(template.slug, occasion)
            content["names"] = LONG_NAMES[occasion]
            view = build_view(occasion=occasion, content=content, overrides={}, template_version=template.current_version,
                              options=RenderOptions(mode="demo"))
            self.assertEqual(view["names_size"], "xlong", template.slug)
            html = render_to_string(template.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
            self.assertIn("a-names--xlong", html, template.slug)
            self.assertIn("Maximiliaan-Alexander" if occasion != "zakelijk" else "Internationale relatiedag", html, template.slug)

    def test_long_single_word_gets_the_smallest_type(self):
        template = Template.objects.get(slug="gala")
        content = demo_content("gala", "zakelijk")
        content["names"]["event_title"] = "Nieuwjaarsreceptie"  # 18 tekens, kan niet afbreken
        view = build_view(occasion="zakelijk", content=content, overrides={}, template_version=template.current_version,
                          options=RenderOptions(mode="demo"))
        self.assertEqual(view["names_size"], "xlong")
        html = render_to_string(template.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
        self.assertIn("a-cover__title a-cover__title--xlong", html)
        self.assertIn("a-names a-names--xlong", html)

    def test_number_design_shows_age_or_years(self):
        toon_verborgen_ontwerpen()
        cases = [("confetti", "verjaardag", "30"), ("lauwerkrans", "jubileum", "40"), ("mijlpaal", "zakelijk", "10")]
        for slug, occasion, number in cases:
            response = Client().get(f"/voorbeeld/{slug}/", {"gelegenheid": occasion})
            self.assertContains(response, f'<p class="a-number fx-shimmer" aria-hidden="true">{number}</p>', html=False, msg_prefix=slug)
        # Zonder getal: de initialen in plaats van een leeg vlak.
        template = Template.objects.get(slug="mijlpaal")
        content = demo_content("mijlpaal", "zakelijk")
        content["names"]["years"] = ""
        view = build_view(occasion="zakelijk", content=content, overrides={}, template_version=template.current_version,
                          options=RenderOptions(mode="demo"))
        self.assertEqual(view["number"], "")
        html = render_to_string(template.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
        self.assertIn("a-number a-number--mono", html)

    def test_business_event_can_have_number_of_years(self):
        owner = self.make_customer()
        client = Client()
        client.force_login(owner)
        inv = self.make_invitation(owner=owner, template="mijlpaal", occasion="zakelijk", complete=False)
        page = client.get(f"/maken/{inv.uid}/gegevens/")
        self.assertContains(page, 'name="name_years"')
        response = client.post(f"/maken/{inv.uid}/gegevens/", {"rev": inv.draft_rev, "name_event_title": "Jubileumborrel",
                                                               "name_organization": "Voorbeeld BV", "name_years": "twaalf"})
        self.assertContains(response, "Vul een getal in.")


class AtelierJourneyTests(VaylideTestCase):
    def test_compose_preview_pay_and_publish_with_a_new_design(self):
        owner = self.make_customer()
        c = Client()
        c.force_login(owner)
        response = c.post("/maken/", {"occasion": "verjaardag", "template": "neon"})
        uid = response["Location"].split("/")[2]
        inv = Invitation.objects.get(uid=uid)
        response = c.post(f"/maken/{uid}/gegevens/", {
            "rev": inv.draft_rev, "actie": "volgende", "name_person_name": "Lotte", "name_age": "30",
            "date": future_date(150), "start_time": "20:00", "end_time": "01:00", "timezone": "Europe/Amsterdam",
            "venue_name": "De Loods", "address": "Kade 2\nUtrecht", "welcome_text": "Kom je ook?",
        })
        self.assertRedirects(response, f"/maken/{uid}/programma/", fetch_redirect_response=False)
        for step in ("programma", "aanmelden", "fotos", "stijl", "voorbeeld", "bestellen"):
            self.assertEqual(c.get(f"/maken/{uid}/{step}/").status_code, 200, step)
        inv.refresh_from_db()
        c.post(f"/maken/{uid}/aanmelden/", {"rev": inv.draft_rev, "actie": "volgende", "enabled": "on", "deadline": future_date(100),
                                            "max_party_size": "2"})
        inv.refresh_from_db()
        c.post(f"/maken/{uid}/stijl/", {"rev": inv.draft_rev, "actie": "volgende", "palette": "blauw", "opening": "on", "s_countdown": "on"})
        preview = c.get(f"/maken/{uid}/voorbeeld/weergave/")
        self.assertContains(preview, "a-cover--sluier")
        self.assertContains(preview, '<p class="a-number fx-shimmer" aria-hidden="true">30</p>', html=False)
        self.assertContains(preview, "--a-accent:")
        inv.refresh_from_db()
        self.pay(inv, owner)
        inv.refresh_from_db()
        page = Client().get(inv.public_path)
        self.assertEqual(page.status_code, 200)
        self.assertContains(page, "designs/neon/v1/style.css")
        self.assertContains(page, "Lotte")
        self.assertContains(page, 'data-palette="blauw"')


class AtelierSiteTests(VaylideTestCase):
    def test_home_features_three_designs_and_the_count(self):
        response = Client().get("/")
        count = Template.objects.filter(is_active=True, current_version__isnull=False).count()
        self.assertEqual(response.content.decode().count('class="design-card"'), 3)
        self.assertContains(response, f"Kies uit {count} ontwerpen")
        # Alleen lichte ontwerpen op de homepage (geen donkere voorbeeldkaarten), de kerstkaart eerst.
        for slug in ("winterlicht", "liefde-op-papier", "confetti"):
            self.assertContains(response, f"/ontwerpen/{slug}/")

    def test_collection_filter_toont_alleen_ontwerpen_voor_de_gelegenheid(self):
        response = Client().get("/ontwerpen/", {"gelegenheid": "verjaardag"})
        cards = response.context["cards"]
        self.assertTrue(cards)
        self.assertTrue(all("verjaardag" in c["template"].occasions for c in cards))      # de volgorde (nieuwste eerst) staat in tests/test_flow_eenvoudig.py

    def test_design_detail_suggests_three_designs_for_the_same_occasion(self):
        response = Client().get("/ontwerpen/confetti/", {"gelegenheid": "verjaardag"})
        others = [c["template"] for c in response.context["others"]]
        self.assertEqual(len(others), 3)
        self.assertNotIn("confetti", [t.slug for t in others])
        self.assertTrue(all(t.supports("verjaardag") for t in others))
        self.assertContains(response, "Meer voor verjaardag")
        self.assertContains(response, "/ontwerpen/?gelegenheid=verjaardag")

    def test_design_step_filters_designs_by_occasion(self):
        owner = self.make_customer()
        client = Client()
        client.force_login(owner)
        inv = self.make_invitation(owner=owner)
        html = client.get(f"/maken/{inv.uid}/ontwerp/").content.decode()
        self.assertIn('class="chip-link is-current"', html)                    # de gelegenheid, met de andere gelegenheden als keuze
        self.assertIn('value="eucalyptus"', html)                             # een bruiloftsontwerp
        self.assertNotIn('value="confetti"', html)                            # een verjaardagsontwerp hoort niet bij deze gelegenheid
        verjaardag = client.get(f"/maken/{inv.uid}/ontwerp/?gelegenheid=verjaardag").content.decode()
        self.assertIn('value="confetti"', verjaardag)
        self.assertNotIn('value="eucalyptus"', verjaardag)

    def test_search_finds_new_designs(self):
        self.assertContains(Client().get("/zoeken/", {"q": "neon"}), "/ontwerpen/neon/")

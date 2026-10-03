"""Nieuwe vormgeving van de website (2026): envelop en gouden kaart in de kop, kerstpodium, vragen op de homepage,
prijzen met vaste prijs of op aanvraag, en het lakzegel: standaard (rood of groen) of persoonlijk (Compleet)."""
from django.conf import settings
from django.template.loader import render_to_string
from django.test import Client
from django.utils.html import escape

from catalog.models import Package, Template
from invitations.demo import demo_content
from invitations.render import RenderOptions, build_view, seal_color

from .helpers import VaylideTestCase


def _render(slug, palette, features):
    template = Template.objects.get(slug=slug)
    occasion = template.occasions[0]
    content = demo_content(slug, occasion, palette)
    view = build_view(occasion=occasion, content=content, overrides={}, template_version=template.current_version,
                      options=RenderOptions(mode="demo", features=features))
    html = render_to_string(template.current_version.template_path, {"v": view, "rsvp_form": {"client_token": "x", "form_ts": ""}})
    return view, html


class HomeTests(VaylideTestCase):
    def test_envelope_opens_with_a_button_and_links_to_the_demo(self):
        html = Client().get("/").content.decode()
        self.assertIn('class="zenv" data-envelop', html)
        self.assertIn('class="zenv__knop" aria-expanded="false" aria-controls="envelop-kaart"', html)
        self.assertIn('id="envelop-kaart"', html)
        self.assertIn("img/merk/vaylide-logo.webp", html)  # het hele logo op de envelop
        self.assertIn("/voorbeeld/liefde-op-papier/?gelegenheid=bruiloft&amp;kleur=salie", html)
        self.assertIn('class="goudkaart"', html)
        js = (settings.BASE_DIR / "static/js/hero3d.js").read_text(encoding="utf-8")
        # Openen werkt ook bij 'minder beweging': de knop wordt gekoppeld voordat het script stopt.
        self.assertLess(js.index("[data-envelop]"), js.index("if (reduce) return;"))
        self.assertIn('setAttribute("aria-expanded"', js)

    def test_no_dark_example_cards_on_home(self):
        html = Client().get("/").content.decode()
        for dark in ("sterrennacht", "middernacht", "feature-panel__bg", "tile--wide"):
            self.assertNotIn(dark, html)
        self.assertIn("feature-panel--licht", html)

    def test_christmas_podium_steps_and_faq(self):
        html = Client().get("/").content.decode()
        self.assertIn('class="kerstpodium" aria-labelledby="kerst-titel" data-sparkles', html)
        for slug in ("winterlicht", "gloria", "golden-noel"):
            self.assertIn(f"/ontwerpen/{slug}/", html)
        for slug in ("kerstman", "sneeuwpop"):          # C: voorlopig niet in de collectie, dus ook niet op het kerstpodium
            self.assertNotIn(f"/ontwerpen/{slug}/", html)
        self.assertEqual(html.count('class="stapkaart"'), 4)
        self.assertIn('class="section home-faq"', html)
        self.assertGreaterEqual(html.count('class="faq-item"'), 6)
        for word in ("hoe betaal ik", "nog iets aanpassen", "hoe deel ik", "aanmeldingen zien"):
            self.assertIn(word, html.lower())
        # Het vragenblok staat vlak voor de voettekst.
        self.assertLess(html.index("home-faq"), html.index("site-footer"))

    def test_confetti_card_has_confetti(self):
        html = Client().get("/").content.decode()
        self.assertIn('class="design-card__confetti"', html)

    def test_footer_has_a_static_flower(self):
        html = Client().get("/prijzen/").content.decode()
        self.assertIn('class="site-footer__bloem"', html)
        footer = html[html.index('<footer class="site-footer">'):]
        self.assertNotIn("<canvas", footer)
        self.assertNotIn("<script", footer.split("</footer>")[0])


class PagesTests(VaylideTestCase):
    def test_pages_share_the_new_page_head(self):
        for url in ("/zo-werkt-het/", "/prijzen/", "/inspiratie/", "/over-ons/"):
            html = Client().get(url).content.decode()
            self.assertIn('class="paginakop" data-sparkles', html, url)
            self.assertIn("js/hero3d.js", html, url)

    def test_how_page_groups_what_guests_get(self):
        html = Client().get("/zo-werkt-het/").content.decode()
        self.assertEqual(html.count('class="gastgroep"'), 3)
        self.assertEqual(html.count('class="stapkaart"'), 6)
        for title in ("Openen en beleven", "Alles bij de hand", "Reageren en delen"):
            self.assertIn(title, html)

    def test_pricing_shows_fixed_prices_and_on_request(self):
        html = Client().get("/prijzen/").content.decode()
        self.assertEqual(html.count("prijskaart__soort--vast"), Package.objects.filter(is_active=True).count())
        self.assertIn("prijskaart__soort--aanvraag", html)
        self.assertIn("Standaard lakzegel", html)
        self.assertIn("Persoonlijk zegel", html)
        self.assertIn("Je bedrijfslogo op het zegel?", html)
        self.assertIn("/contact/?onderwerp=maatwerk", html)
        # De prijzen zelf zijn niet veranderd.
        self.assertEqual(Package.objects.get(code="essentieel").price_cents, 3900)
        self.assertEqual(Package.objects.get(code="compleet").price_cents, 6900)


class SealTests(VaylideTestCase):
    def test_every_package_includes_the_personal_seal(self):
        # Keuze van de eigenaar (september 2026): envelop en lakzegel naar keuze voor alle pakketten.
        self.assertIn("zegel", Package.objects.get(code="compleet").features)
        self.assertIn("zegel", Package.objects.get(code="essentieel").features)
        self.assertIn("Envelop en lakzegel naar keuze, met jullie initialen of eigen logo", Package.objects.get(code="essentieel").highlights)
        self.assertNotIn("Persoonlijk zegel met jullie initialen", Package.objects.get(code="compleet").highlights)

    def test_seal_colour_follows_the_palette(self):
        self.assertEqual(seal_color("salie"), "groen")
        self.assertEqual(seal_color("dennengroen"), "groen")
        self.assertEqual(seal_color("blush"), "rood")
        self.assertEqual(seal_color("gouden"), "rood")

    def test_standard_seal_has_no_initials(self):
        for slug, palette in (("liefde-op-papier", "blush"), ("lauwerkrans", ""), ("winterlicht", "")):
            view, html = _render(slug, palette, ["story"])
            self.assertFalse(view["seal_personal"])
            self.assertRegex(html, r'class="(seal-motief|wl-seal__motief)"', slug)
            self.assertIn(f"seal:{view['seal_std']['base']}", html, slug)
            view2, html2 = _render(slug, palette, ["story", "zegel"])
            self.assertTrue(view2["seal_personal"])
            self.assertNotIn("{#", html + html2)  # geen commentaar als zichtbare tekst
            self.assertNotIn("(--wl-seal*)", html + html2)
            self.assertNotRegex(html2, r'class="(seal-motief|wl-seal__motief)"', slug)
            self.assertIn(escape(view2["monogram"]), html2, slug)

    def test_green_palette_gets_a_green_standard_seal(self):
        view, html = _render("liefde-op-papier", "salie", [])
        self.assertEqual(view["seal_color"], "groen")
        self.assertIn("--lp-seal:#2C5A3C", html)

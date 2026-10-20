"""Homepage: de kaart in de kop in 3D met sterretjes (static/js/hero3d.js)."""
from django.conf import settings
from django.test import Client

from .helpers import VaylideTestCase


class Home3DTests(VaylideTestCase):
    def test_hero_has_3d_card_and_sparkles(self):
        html = Client().get("/").content.decode()
        self.assertIn('data-hero3d', html)
        self.assertIn('<div class="hero__wereld" aria-hidden="true">', html)
        self.assertIn('<canvas class="hero__sparkles"></canvas>', html)
        self.assertIn('class="card-stage"', html)
        self.assertIn("js/hero3d.js", html)
        # De vaste teksten van de eigenaar blijven staan, en de kaart linkt nog naar het werkende voorbeeld.
        self.assertIn("Een bijzondere dag verdient een", html)
        self.assertIn("Bekijk de ontwerpen", html)
        self.assertIn("Maak jouw uitnodiging", html)
        self.assertIn("/voorbeeld/kerstkaart/", html)  # 'Bekijk het voorbeeld' opent de filmische kerstkaart

    def test_motion_respects_reduced_motion(self):
        js = (settings.BASE_DIR / "static/js/hero3d.js").read_text(encoding="utf-8")
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertIn("IntersectionObserver", js)  # stopt als de kop uit beeld is
        css = (settings.BASE_DIR / "static/css/vierlief.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"@media \(prefers-reduced-motion: no-preference\) \{\s*\.card-stage \{ animation: card-zweef")


class HeroVoorbeeldknopRozenboogTests(VaylideTestCase):
    """De kaart in de hero is de Rozenboog; de knop opent dezelfde kaart zodra die actief is."""

    def test_knop_opent_rozenboog_als_die_actief_is(self):
        from catalog.models import Template
        Template.objects.filter(slug="rozenboog").update(is_active=True)
        html = Client().get("/").content.decode()
        self.assertIn("kaart-rozenboog", html)
        self.assertIn('href="/voorbeeld/rozenboog/?gelegenheid=bruiloft"', html)
        self.assertEqual(Client().get("/voorbeeld/rozenboog/?gelegenheid=bruiloft").status_code, 200)

    def test_knop_valt_terug_als_rozenboog_niet_actief_is(self):
        from catalog.models import Template
        Template.objects.filter(slug="rozenboog").update(is_active=False)
        html = Client().get("/").content.decode()
        self.assertNotIn("/voorbeeld/rozenboog/", html)
        self.assertIn("/voorbeeld/kerstkaart/", html)

from django.contrib.staticfiles import finders
from django.test import TestCase


class MaatwerkBeeldTests(TestCase):
    def test_homepage_toont_het_op_maat_blok_met_een_aparte_mobiele_variant(self):
        html = self.client.get("/").content.decode()
        self.assertIn("Jullie verhaal verdient<br> <em>iets bijzonders</em>", html)
        self.assertIn("Vertel jullie wens", html)
        self.assertIn("écht van jullie", html)
        self.assertIn('<source media="(max-width: 720px)"', html)
        for naam in ("op-maat-gouden-avond.webp", "op-maat-gouden-avond-700.webp", "op-maat-gouden-avond-mobiel.webp"):
            self.assertIn(f"img/site/{naam}", html)
            self.assertIsNotNone(finders.find(f"img/site/{naam}"), naam)

    def test_knop_gaat_naar_de_contactpagina_voor_maatwerk(self):
        html = self.client.get("/").content.decode()
        self.assertIn("/contact/?onderwerp=maatwerk", html)

    def test_het_op_maat_blok_toont_de_kaart_gouden_avond(self):
        html = self.client.get("/").content.decode()
        self.assertIn("Gouden Avond", html[html.index('id="uniek-titel"'):])
        self.assertIn("geopende envelop", html[html.index('id="uniek-titel"'):])
        self.assertNotIn("img/site/op-maat.webp", html)


class TelefoonBloesemmeerTests(TestCase):
    def test_de_telefoon_toont_bloesemmeer(self):
        html = self.client.get("/").content.decode()
        self.assertIn("img/site/telefoon-bloesemmeer.webp", html)
        self.assertNotIn("img/site/telefoon-voorbeeld.webp", html)
        self.assertIsNotNone(finders.find("img/site/telefoon-bloesemmeer.webp"))

    def test_is_bloesemmeer_actief_dan_laadt_de_telefoon_het_werkende_voorbeeld_en_is_het_beeld_de_terugval(self):
        from catalog.models import Template

        Template.objects.filter(slug="bloesemmeer").update(is_active=True)
        html = self.client.get("/").content.decode()
        self.assertIn('data-lazy-frame="/voorbeeld/bloesemmeer/?embed=1"', html)
        self.assertIn("img/site/telefoon-bloesemmeer.webp", html)
        self.assertEqual(self.client.get("/voorbeeld/bloesemmeer/").status_code, 200)

    def test_zolang_bloesemmeer_verborgen_is_geen_werkend_voorbeeld_en_geen_link_naar_een_404(self):
        html = self.client.get("/").content.decode()
        self.assertNotIn("/voorbeeld/bloesemmeer/", html)
        self.assertEqual(self.client.get("/voorbeeld/bloesemmeer/").status_code, 404)

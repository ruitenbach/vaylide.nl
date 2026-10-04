from django.contrib.staticfiles import finders
from django.test import TestCase


class MaatwerkBeeldTests(TestCase):
    def test_homepage_toont_het_op_maat_blok_met_een_aparte_mobiele_variant(self):
        html = self.client.get("/").content.decode()
        self.assertIn("Jullie verhaal verdient iets bijzonders", html)
        self.assertIn("Vertel jullie wens", html)
        self.assertIn("écht van jullie", html)
        self.assertIn('<source media="(max-width: 720px)"', html)
        for naam in ("op-maat.webp", "op-maat-700.webp", "op-maat-mobiel.webp"):
            self.assertIn(f"img/site/{naam}", html)
            self.assertIsNotNone(finders.find(f"img/site/{naam}"), naam)

    def test_knop_gaat_naar_de_contactpagina_voor_maatwerk(self):
        html = self.client.get("/").content.decode()
        self.assertIn("/contact/?onderwerp=maatwerk", html)

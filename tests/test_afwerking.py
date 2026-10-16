from pathlib import Path

from django.test import SimpleTestCase

from catalog import prijzen

ROOT = Path(__file__).resolve().parent.parent


class AfwerkingTests(SimpleTestCase):
    def test_prijslabel_heeft_geen_streepje_tussen_indeling_en_prijs(self):
        for naam in prijzen.TIER_NAAM.values():
            self.assertNotIn(f"{naam} —", Path(ROOT / "catalog/prijzen.py").read_text())

    def test_scrollaanwijzing_van_de_kerstkaarten_is_rustig_en_zonder_lees_verder(self):
        for slug in ("kerstmarkt", "kerstcoupe", "kerstpaleis"):
            html = (ROOT / f"designs/{slug}/v1/invitation.html").read_text()
            self.assertNotIn("Lees verder", html, slug)
            self.assertIn("Scroll naar beneden", html, slug)
            self.assertIn('href="#', html)

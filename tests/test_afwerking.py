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


from django.test import TestCase, override_settings

from catalog.models import Template


@override_settings(PRICING_V2=True)
class PrijzenpaginaTests(TestCase):
    def test_knoppen_leiden_naar_ontwerpen_van_die_indeling(self):
        html = self.client.get("/prijzen/").content.decode()
        self.assertNotIn("Uitgelicht", html)
        for tier in prijzen.TIERS:
            if any(prijzen.tier(t) == tier for t in Template.objects.filter(is_active=True)):
                self.assertIn(f"/ontwerpen/?indeling={tier}", html)

    def test_collectie_filtert_op_indeling_en_negeert_onzin(self):
        for tier in prijzen.TIERS:
            html = self.client.get(f"/ontwerpen/?indeling={tier}").content.decode()
            for t in Template.objects.filter(is_active=True):
                if prijzen.tier(t) != tier:
                    self.assertNotIn(f"/ontwerpen/{t.slug}/", html, (tier, t.slug))
        self.assertEqual(self.client.get("/ontwerpen/?indeling=onzin").status_code, 200)

    @override_settings(PRICING_V2=False)
    def test_zonder_nieuwe_prijsstructuur_is_er_geen_indelingsfilter(self):
        self.assertNotIn("Je ziet de ontwerpen met de indeling", self.client.get("/ontwerpen/?indeling=luxe").content.decode())

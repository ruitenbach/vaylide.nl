"""De mobiele bestelroute van de kerstpagina en de ontwerppagina.

Wat deze tests bewaken:
- de echte bestelknop 'Maak jullie kerstkaart' is de gouden hoofdknop in de kop; 'Bekijk de kerstkaarten' is de tweede knop;
- de bestelroute zelf verandert niet: dezelfde link naar Samenstellen, zonder soort (de wenskaart-standaard is bewust niet doorgevoerd, zie docs/CONTROLES.md);
- op de ontwerppagina blijven prijs, knop en alle keuzes aanwezig (alleen de volgorde op een telefoon is anders, via CSS);
- de cookiebanner houdt twee gelijkwaardige knoppen."""
import re

from django.test import Client, override_settings

from .helpers import VaylideTestCase

CSS = open("static/css/vierlief.css", encoding="utf-8").read()


class KerstKopTests(VaylideTestCase):
    def kop(self):
        html = Client().get("/digitale-kerstkaarten/").content.decode()
        return re.search(r'<div class="btn-row btn-row--center">(.*?)</div>', html, re.S).group(1)

    def test_de_bestelknop_is_de_gouden_hoofdknop(self):
        knoppen = re.findall(r'<a class="(btn [^"]*)" href="([^"]*)">(.*?)</a>', self.kop(), re.S)
        self.assertEqual(len(knoppen), 2)
        (klasse1, href1, tekst1), (klasse2, href2, tekst2) = knoppen
        self.assertIn("btn--goud", klasse1)
        self.assertEqual(href1, "/maken/?gelegenheid=kerst")
        self.assertIn("Maak jullie kerstkaart", tekst1)
        self.assertIn("btn--secondary", klasse2)
        self.assertEqual(href2, "#kerstontwerpen")
        self.assertIn("Bekijk de kerstkaarten", tekst2)

    def test_de_bestelroute_blijft_ongewijzigd_zonder_vaste_kaartsoort(self):
        html = Client().get("/digitale-kerstkaarten/").content.decode()
        self.assertNotIn("soort=", html, "de kerstpagina stuurt niet naar een vaste soort kaart: de wenskaart-standaard is tegengehouden")
        self.assertIn('href="/maken/?gelegenheid=kerst"', html)


class OntwerppaginaTests(VaylideTestCase):
    @override_settings(PRICING_V2=True)
    def test_prijs_knop_en_keuzes_zijn_er_nog_en_de_volgorde_op_mobiel_komt_uit_css(self):
        html = Client().get("/ontwerpen/winterlicht/?gelegenheid=kerst").content.decode()
        for deel in ('class="detail-prijs"', "Kies dit ontwerp", "Open het voorbeeld", 'class="meta-list"', "Soort kaart", "Kleur", 'class="occasion-picker"'):
            self.assertIn(deel, html, deel)
        self.assertLess(html.index("Kies dit ontwerp"), html.index("</section>"))
        self.assertRegex(CSS, r"@media \(max-width: 899px\) \{\s*\.detail-text \{ display: flex; flex-direction: column; \}")
        for regel in (".detail-text > .detail-prijs { order: 1", ".detail-text > .btn-row { order: 2", ".detail-text > .lead { order: 3"):
            self.assertIn(regel, CSS)


class CookiebannerTests(VaylideTestCase):
    @override_settings(CLARITY_ID="abc123test")
    def test_accepteren_en_weigeren_blijven_gelijkwaardig(self):
        html = Client().get("/digitale-kerstkaarten/").content.decode()
        knoppen = re.findall(r'<button type="button" class="([^"]*)" data-toestemming-keuze="(ja|nee)"', html)
        self.assertEqual(sorted(k[1] for k in knoppen), ["ja", "nee"])
        self.assertEqual(len({k[0] for k in knoppen}), 1, "beide knoppen hebben dezelfde opmaak")

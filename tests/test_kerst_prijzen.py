"""De kerstpagina en de kerstcollectie tonen de echte prijs (catalog.prijzen) en het label Special volgt de indeling van het ontwerp.

Wat deze tests bewaken:
- het bedrag staat nergens in de pagina's als vaste tekst: het komt uit dezelfde plek als de ontwerppagina en Bestellen;
- zonder nieuwe prijsstructuur verschijnt er geen prijs en geldt de oude vlag voor het label Special, zoals voorheen;
- Golden Noël (Luxe) draagt geen Special-label meer; Kerstbol, Kerststad en Kerstkaart (Special) wel;
- andere gelegenheden en de homepage tonen geen extra prijs op hun kaarten."""
import re

from django.test import Client, override_settings

from catalog import prijzen
from catalog.models import format_euro

from .helpers import VaylideTestCase

V2 = override_settings(PRICING_V2=True)
KAART = re.compile(r'<article class="design-card">(.*?)</article>', re.S)


def kaarten(html):
    """{naam: html van de kaart}, uit de kaarten op een pagina."""
    uit = {}
    for blok in KAART.findall(html):
        naam = re.search(r'<span class="design-card__name">(.*?)</span>\s*(?:<span class="design-card__name"|$)', blok, re.S)
        tekst = re.search(r'<span class="design-card__name">(.*?)</span>\s*<span class="design-card__meta"', blok, re.S)
        sleutel = re.sub(r"<[^>]+>", " ", (tekst or naam).group(1)) if (tekst or naam) else blok[:40]
        uit[" ".join(sleutel.split())] = blok
    return uit


class KerstprijzenTests(VaylideTestCase):
    @V2
    def test_kerstkaarten_tonen_hun_prijs_uit_de_catalogus(self):
        html = Client().get("/digitale-kerstkaarten/").content.decode()
        gezien = kaarten(html)
        self.assertTrue(gezien)
        verwacht = {"Winterlicht": "Luxe", "Gloria": "Luxe", "Middernacht": "Luxe", "Kerststad": "Special", "Kerstbol": "Special"}
        for naam, tier in verwacht.items():
            sleutel = next(k for k in gezien if k.endswith(naam))
            cents = prijzen.cel_cents("kerst", tier.lower())
            self.assertIn(f'<span class="design-card__tier">{tier}</span> {format_euro(cents)}', gezien[sleutel], naam)

    @V2
    def test_vanafregel_en_uitleg_komen_uit_de_prijsfuncties(self):
        html = Client().get("/digitale-kerstkaarten/").content.decode()
        luxe, special = format_euro(prijzen.cel_cents("kerst", "luxe")), format_euro(prijzen.cel_cents("kerst", "special"))
        self.assertRegex(html, rf'class="kerst-vanaf">Vanaf <strong>{re.escape(luxe)}</strong>')
        self.assertIn(f"<strong>Luxe {luxe}</strong>: {prijzen.BESCHRIJVING['luxe']}", html)
        self.assertIn(f"<strong>Special {special}</strong>: {prijzen.BESCHRIJVING['special']}", html)
        self.assertNotIn("Basis €", html.split('class="kerst-legenda"')[1].split("</ul>")[0], "Basis bestaat niet bij Kerst")

    def test_de_prijs_volgt_een_aangepaste_prijs_en_staat_niet_vast_in_de_tekst(self):
        with V2, override_settings(PRICES_ADMIN=False):
            from unittest import mock
            with mock.patch.object(prijzen, "cel_cents", side_effect=lambda rij, ind: {"luxe": 2695, "special": 5195}.get(ind, 995)):
                html = Client().get("/digitale-kerstkaarten/").content.decode()
        self.assertIn("€ 26,95", html)
        self.assertIn("€ 51,95", html)
        self.assertNotIn("€ 24,95", html.split('id="kerstontwerpen"')[1].split("</section>")[0])

    @override_settings(PRICING_V2=False)
    def test_zonder_nieuwe_prijsstructuur_geen_prijs_op_de_kaarten(self):
        html = Client().get("/digitale-kerstkaarten/").content.decode()
        self.assertNotIn("design-card__tier", html)
        self.assertNotIn("kerst-vanaf", html)
        self.assertNotIn("kerst-legenda", html)

    @V2
    def test_golden_noel_is_luxe_en_krijgt_geen_special_label(self):
        gezien = kaarten(Client().get("/digitale-kerstkaarten/").content.decode())
        golden = gezien[next(k for k in gezien if k.endswith("Golden Noël"))]
        self.assertNotIn("design-card__special", golden)
        for naam in ("Kerstbol", "Kerststad", "Kerstkaart"):
            kaart = gezien[next(k for k in gezien if k.endswith(naam))]
            self.assertIn("design-card__special", kaart, naam)

    @override_settings(PRICING_V2=False)
    def test_zonder_nieuwe_prijsstructuur_geldt_de_oude_vlag(self):
        gezien = kaarten(Client().get("/digitale-kerstkaarten/").content.decode())
        golden = gezien[next(k for k in gezien if k.endswith("Golden Noël"))]
        self.assertIn("design-card__special", golden)

    @V2
    def test_kerstcollectie_toont_prijzen_maar_andere_gelegenheden_en_homepage_niet(self):
        self.assertIn("design-card__tier", Client().get("/ontwerpen/?gelegenheid=kerst").content.decode())
        for pad in ("/", "/ontwerpen/", "/ontwerpen/?gelegenheid=bruiloft", "/digitale-trouwkaarten/", "/digitale-verjaardagsuitnodigingen/"):
            self.assertNotIn("design-card__tier", Client().get(pad).content.decode(), pad)

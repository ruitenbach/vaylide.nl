"""Vindbaarheid (SEO): titels, beschrijvingen, canonical, Open Graph, Twitter, gestructureerde gegevens, sitemap, robots en noindex.

Alleen feiten die op de website staan: geen reviews, beoordelingen, prijzen of bedrijfsgegevens in de gestructureerde gegevens.
"""
import base64
import json
import re

from django.conf import settings
from django.test import Client, override_settings

from catalog.models import Template
from catalog.occasions import OCCASION_LABELS
from core import seo

from .helpers import VaylideTestCase


def kop(html: str) -> str:
    return html.split("</head>")[0]


def meta(html: str, naam: str, soort: str = "name") -> str:
    m = re.search(rf'<meta {soort}="{re.escape(naam)}" content="(.*?)"', kop(html), re.S)
    return m.group(1) if m else ""


def json_ld(html: str) -> list[dict]:
    return [json.loads(b) for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', kop(html), re.S)]


def canonical(html: str) -> str:
    m = re.search(r'<link rel="canonical" href="(.*?)"', kop(html))
    return m.group(1) if m else ""


def titel(html: str) -> str:
    return re.search(r"<title>(.*?)</title>", kop(html), re.S).group(1)


class HomepageSeoTests(VaylideTestCase):
    def setUp(self):
        self.html = Client().get("/").content.decode()

    def test_titel_beschrijving_en_canonical(self):
        self.assertEqual(titel(self.html), "Digitale uitnodigingen die je beleeft · VAYLIDE")
        beschrijving = meta(self.html, "description")
        self.assertGreaterEqual(len(beschrijving), 70)
        self.assertLessEqual(len(beschrijving), 160)
        for woord in ("bruiloft", "verjaardag", "kerst", "zakelijke"):
            self.assertIn(woord, beschrijving)
        self.assertEqual(canonical(self.html), f"{settings.BASE_URL}/")

    def test_open_graph_en_twitter(self):
        self.assertEqual(meta(self.html, "og:url", "property"), f"{settings.BASE_URL}/")
        self.assertEqual(meta(self.html, "og:locale", "property"), "nl_NL")
        self.assertEqual(meta(self.html, "og:title", "property"), "VAYLIDE · digitale uitnodigingen die je beleeft")
        self.assertEqual(meta(self.html, "og:description", "property"), meta(self.html, "description"))
        self.assertTrue(meta(self.html, "og:image", "property").startswith(settings.BASE_URL + "/static/img/og-vaylide"))
        self.assertEqual((meta(self.html, "og:image:width", "property"), meta(self.html, "og:image:height", "property")), ("1200", "630"))
        self.assertEqual(meta(self.html, "twitter:card"), "summary_large_image")

    def test_gestructureerde_gegevens_zonder_verzonnen_feiten(self):
        blokken = json_ld(self.html)
        self.assertEqual({b["@type"] for b in blokken}, {"Organization", "WebSite"})
        organisatie = [b for b in blokken if b["@type"] == "Organization"][0]
        self.assertEqual(organisatie["name"], "VAYLIDE")
        self.assertTrue(organisatie["logo"].startswith(settings.BASE_URL + "/static/img/merk/vaylide-logo"))
        self.assertEqual(set(organisatie), {"@context", "@type", "@id", "name", "url", "logo", "sameAs"})   # geen adres, telefoon, kvk of beoordelingen
        self.assertEqual(organisatie["sameAs"], ["https://www.instagram.com/vaylidenl/", "https://www.facebook.com/profile.php?id=61594950397795",
                                                 "https://www.tiktok.com/@vaylidenl", "https://www.linkedin.com/company/vaylide/"])
        tekst = json.dumps(blokken)
        for woord in ("aggregateRating", "Review", "Offer", "price", "address", "telephone", "vatID"):
            self.assertNotIn(woord, tekst)


class GelegenheidspaginaSeoTests(VaylideTestCase):
    def test_elke_gelegenheid_heeft_een_eigen_pagina_met_eigen_canonical(self):
        for sleutel in OCCASION_LABELS:
            self.assertIn(sleutel, seo.OCCASION_SEO)
            html = Client().get("/ontwerpen/", {"gelegenheid": sleutel}).content.decode()
            titel_tekst, beschrijving = seo.OCCASION_SEO[sleutel]
            self.assertEqual(titel(html), f"{titel_tekst} · VAYLIDE", sleutel)
            self.assertLessEqual(len(titel(html)), 70, sleutel)
            self.assertEqual(meta(html, "description"), beschrijving, sleutel)
            self.assertGreaterEqual(len(beschrijving), 70, sleutel)
            self.assertLessEqual(len(beschrijving), 160, sleutel)
            self.assertEqual(canonical(html), f"{settings.BASE_URL}/ontwerpen/?gelegenheid={sleutel}", sleutel)
            self.assertEqual(meta(html, "og:url", "property"), canonical(html), sleutel)
            kruimels = [b for b in json_ld(html) if b["@type"] == "BreadcrumbList"][0]
            self.assertEqual([i["name"] for i in kruimels["itemListElement"]], ["Home", "Collectie", f"Ontwerpen voor {OCCASION_LABELS[sleutel].lower()}"], sleutel)

    def test_de_collectie_zonder_gelegenheid_en_een_onbekende_gelegenheid(self):
        for query in ({}, {"gelegenheid": "onzin"}, {"categorie": "specials"}):
            html = Client().get("/ontwerpen/", query).content.decode()
            self.assertEqual(canonical(html), f"{settings.BASE_URL}/ontwerpen/", query)
            self.assertEqual(titel(html), "Collectie digitale uitnodigingen · VAYLIDE", query)
        self.assertNotIn("onzin", Client().get("/sitemap.xml").content.decode())


class OntwerppaginaSeoTests(VaylideTestCase):
    def test_elke_zichtbare_ontwerppagina_heeft_titel_beschrijving_afbeelding_en_kruimelpad(self):
        for template in Template.objects.filter(is_active=True, current_version__isnull=False):
            html = Client().get(f"/ontwerpen/{template.slug}/").content.decode()
            beschrijving = meta(html, "description")
            self.assertGreaterEqual(len(beschrijving), 70, template.slug)
            self.assertLessEqual(len(beschrijving), 160, template.slug)
            self.assertLessEqual(len(titel(html)), 70, template.slug)
            self.assertEqual(canonical(html), f"{settings.BASE_URL}/ontwerpen/{template.slug}/", template.slug)
            self.assertTrue(meta(html, "og:image", "property").startswith(f"{settings.BASE_URL}/static/img/designs/{template.slug}"), template.slug)
            self.assertEqual(meta(html, "twitter:card"), "summary", template.slug)
            kruimels = [b for b in json_ld(html) if b["@type"] == "BreadcrumbList"][0]
            self.assertEqual([i["name"] for i in kruimels["itemListElement"]], ["Home", "Collectie", template.name], template.slug)

    def test_kerstkaart_en_kerstbol(self):
        for slug, naam in (("kerstkaart", "Kerstkaart"), ("kerstbol", "Kerstbol")):
            html = Client().get(f"/ontwerpen/{slug}/", {"gelegenheid": "kerst", "kleur": "nacht"}).content.decode()
            self.assertEqual(titel(html), f"{naam}, digitale kerstkaart · VAYLIDE")
            self.assertIn("Digitale kerstkaart van VAYLIDE.", meta(html, "description"))
            self.assertEqual(meta(html, "og:description", "property"), meta(html, "description"))
            self.assertEqual(canonical(html), f"{settings.BASE_URL}/ontwerpen/{slug}/")   # kleur en gelegenheid in de link veranderen de canonical niet

    def test_een_gewone_ontwerppagina_spreekt_van_een_uitnodiging(self):
        html = Client().get("/ontwerpen/avondgoud/").content.decode()
        self.assertEqual(titel(html), "Avondgoud, digitale uitnodiging · VAYLIDE")


class SitemapRobotsEnNoindexTests(VaylideTestCase):
    def test_sitemap_bevat_publieke_pagina_s_en_gelegenheden_maar_niets_privés(self):
        sitemap = Client().get("/sitemap.xml").content.decode()
        for pad in ("/", "/ontwerpen/", "/ontwerpen/?gelegenheid=kerst", "/ontwerpen/?gelegenheid=bruiloft", "/ontwerpen/kerstkaart/", "/ontwerpen/kerstbol/", "/ontwerpen/gouden-avond/",
                    "/prijzen/", "/zo-werkt-het/"):
            self.assertIn(f"<loc>{settings.BASE_URL}{pad}</loc>", sitemap, pad)
        for pad in ("/voorbeeld/", "/u/", "/maken/", "/account/", "/inloggen/", "/zoeken/", "/voorwaarden/versie/", "/beheer/", "kerstman"):
            self.assertNotIn(pad, sitemap, pad)

    def test_robots_laat_publiek_toe_en_sluit_privé_delen_uit(self):
        robots = Client().get("/robots.txt").content.decode()
        self.assertNotIn("Disallow: /\n", robots)
        for pad in ("/u/", "/voorbeeld/", "/account/", "/maken/", "/bestelling/", "/betalen/", "/inloggen/"):
            self.assertIn(f"Disallow: {pad}", robots)
        self.assertIn(f"Sitemap: {settings.BASE_URL}/sitemap.xml", robots)
        self.assertNotIn(settings.ADMIN_URL.strip("/"), robots)

    def test_publieke_pagina_s_zijn_indexeerbaar_en_privépagina_s_niet(self):
        for pad in ("/", "/ontwerpen/", "/ontwerpen/kerstkaart/", "/prijzen/", "/contact/", "/voorwaarden/"):
            response = Client().get(pad)
            self.assertIsNone(response.headers.get("X-Robots-Tag"), pad)
            self.assertNotIn('name="robots"', kop(response.content.decode()), pad)
        for pad in ("/inloggen/", "/voorbeeld/kerstkaart/?gelegenheid=kerst", "/voorwaarden/versie/2026-09-29/", "/voorwaarden/pdf/2026-09-29/"):
            self.assertIn("noindex", Client().get(pad).headers.get("X-Robots-Tag", ""), pad)
        self.assertIn('content="noindex, follow"', Client().get("/zoeken/", {"q": "bruiloft"}).content.decode())

    @override_settings(PREVIEW_PASSWORD="lang-en-geheim-wachtwoord", PREVIEW_USER="voorbeeld")
    def test_een_afgeschermde_testversie_is_nergens_indexeerbaar(self):
        auth = {"HTTP_AUTHORIZATION": "Basic " + base64.b64encode(b"voorbeeld:lang-en-geheim-wachtwoord").decode()}
        for pad in ("/", "/ontwerpen/", "/ontwerpen/kerstkaart/", "/prijzen/"):
            response = Client().get(pad, **auth)
            self.assertEqual(response.status_code, 200, pad)
            self.assertIn("noindex", response.headers.get("X-Robots-Tag", ""), pad)
            self.assertEqual(Client().get(pad).status_code, 401, pad)   # zonder wachtwoord ziet een zoekmachine niets
        self.assertEqual(Client().get("/robots.txt", **auth).content.decode(), "User-agent: *\nDisallow: /\n")

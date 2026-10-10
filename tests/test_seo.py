"""Vindbaarheid (SEO): titels, beschrijvingen, canonical, Open Graph, Twitter, gestructureerde gegevens, sitemap, robots en noindex.

Alleen feiten die op de website staan: geen reviews, beoordelingen, prijzen of bedrijfsgegevens in de gestructureerde gegevens.
"""
import base64
import html as html_lib
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
            # Het bruiloftfilter werkt gewoon, maar zijn canonical is de landingspagina Digitale trouwkaarten.
            hubs = {"bruiloft": "/digitale-trouwkaarten/", "kerst": "/digitale-kerstkaarten/", "verjaardag": "/digitale-verjaardagsuitnodigingen/", "zakelijk": "/digitale-zakelijke-uitnodigingen/"}
            verwacht = f"{settings.BASE_URL}{hubs[sleutel]}" if sleutel in hubs else f"{settings.BASE_URL}/ontwerpen/?gelegenheid={sleutel}"
            self.assertEqual(canonical(html), verwacht, sleutel)
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
        self.assertNotIn("?gelegenheid=bruiloft", sitemap)          # het bruiloft- en het kerstfilter staan niet in de sitemap: de landingspagina's zijn hun vervanger
        self.assertNotIn("?gelegenheid=kerst", sitemap)
        self.assertNotIn("?gelegenheid=verjaardag", sitemap)
        self.assertNotIn("?gelegenheid=zakelijk", sitemap)
        for pad in ("/", "/ontwerpen/", "/digitale-uitnodiging-maken/", "/digitale-trouwkaarten/", "/digitale-kerstkaarten/", "/digitale-verjaardagsuitnodigingen/", "/digitale-zakelijke-uitnodigingen/", "/ontwerpen/?gelegenheid=jubileum", "/ontwerpen/kerstkaart/", "/ontwerpen/kerstbol/", "/ontwerpen/gouden-avond/",
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


class TrouwkaartenHubTests(VaylideTestCase):
    """/digitale-trouwkaarten/: de landingspagina voor de bruiloft, met het bruiloftfilter als gewone UI."""

    def setUp(self):
        self.response = Client().get("/digitale-trouwkaarten/")
        self.html = self.response.content.decode()

    def test_pagina_is_indexeerbaar_met_eigen_titel_beschrijving_h1_en_self_canonical(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertNotIn("X-Robots-Tag", self.response.headers)
        self.assertEqual(meta(self.html, "robots"), "")
        self.assertEqual(titel(self.html), "Digitale trouwkaart maken | Luxe online trouwuitnodiging · VAYLIDE")
        self.assertEqual(meta(self.html, "description"), "Maak een digitale trouwkaart die echt tot leven komt. Met interactieve opening, RSVP, programma, locatie en eenvoudig delen via WhatsApp of QR-code.")
        self.assertEqual(canonical(self.html), f"{settings.BASE_URL}/digitale-trouwkaarten/")
        self.assertEqual(meta(self.html, "og:url", "property"), canonical(self.html))
        self.assertEqual(re.findall(r"<h1[^>]*>(.*?)</h1>", self.html, re.S), ["Digitale trouwkaarten die je gasten <em>echt beleven</em>"])

    def test_gestructureerde_gegevens_zijn_geldig_en_de_faq_staat_zichtbaar_op_de_pagina(self):
        blokken = {b["@type"]: b for b in json_ld(self.html)}
        self.assertEqual([i["name"] for i in blokken["BreadcrumbList"]["itemListElement"]], ["Home", "Digitale trouwkaarten"])
        self.assertEqual(blokken["BreadcrumbList"]["itemListElement"][1]["item"], f"{settings.BASE_URL}/digitale-trouwkaarten/")
        vragen = blokken["FAQPage"]["mainEntity"]
        self.assertGreaterEqual(len(vragen), 5)
        zichtbaar = html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", self.html)))
        for v in vragen:
            self.assertEqual(v["@type"], "Question")
            self.assertEqual(v["acceptedAnswer"]["@type"], "Answer")
            self.assertIn(v["name"], zichtbaar)
            self.assertIn(v["acceptedAnswer"]["text"], zichtbaar)

    def test_de_pagina_linkt_naar_collectie_prijzen_uitleg_vragen_en_trouwontwerpen(self):
        for pad in ("/ontwerpen/?gelegenheid=bruiloft", "/prijzen/", "/zo-werkt-het/", "/veelgestelde-vragen/", "/ontwerpen/balzaal/?gelegenheid=bruiloft"):
            self.assertIn(f'href="{pad}"', self.html, pad)

    def test_sitemap_heeft_de_pagina_en_het_bruiloftfilter_blijft_gewoon_werken(self):
        sitemap = Client().get("/sitemap.xml").content.decode()
        self.assertIn(f"<loc>{settings.BASE_URL}/digitale-trouwkaarten/</loc>", sitemap)
        self.assertNotIn("gelegenheid=bruiloft", sitemap)
        for gelegenheid in ("verloving", "jubileum", "babyshower"):
            self.assertIn(f"gelegenheid={gelegenheid}</loc>", sitemap, gelegenheid)
        filter_pagina = Client().get("/ontwerpen/?gelegenheid=bruiloft")
        self.assertEqual(filter_pagina.status_code, 200)
        self.assertIn("Ontwerpen voor bruiloft", filter_pagina.content.decode())

    def test_de_homepage_en_trouwontwerpen_linken_naar_de_pagina(self):
        home = Client().get("/").content.decode()
        self.assertIn('<a href="/digitale-trouwkaarten/">digitale trouwkaarten</a>', home)
        trouw = Client().get("/ontwerpen/balzaal/").content.decode()
        self.assertIn('href="/digitale-trouwkaarten/"', trouw)
        zonder = Client().get("/ontwerpen/kerstbol/").content.decode()          # geen bruiloftontwerp: geen verwijzing
        self.assertNotIn('href="/digitale-trouwkaarten/"', zonder)


class KerstkaartenHubTests(VaylideTestCase):
    """/digitale-kerstkaarten/: de landingspagina voor Kerst, met het kerstfilter als gewone UI."""

    def setUp(self):
        self.response = Client().get("/digitale-kerstkaarten/")
        self.html = self.response.content.decode()

    def test_pagina_is_indexeerbaar_met_eigen_titel_beschrijving_h1_en_self_canonical(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertNotIn("X-Robots-Tag", self.response.headers)
        self.assertEqual(meta(self.html, "robots"), "")
        self.assertEqual(titel(self.html), "Digitale kerstkaart maken | Luxe online kerstkaart · VAYLIDE")
        beschrijving = "Maak een digitale kerstkaart die echt tot leven komt. Met animatie, een bijzondere opening en eenvoudig delen via WhatsApp, link of QR-code."
        self.assertEqual(meta(self.html, "description"), beschrijving)
        self.assertNotIn("muziek", beschrijving.lower())          # muziek zit niet op elke kerstkaart: niet algemeen beloven
        self.assertEqual(canonical(self.html), f"{settings.BASE_URL}/digitale-kerstkaarten/")
        self.assertEqual(meta(self.html, "og:url", "property"), canonical(self.html))
        self.assertEqual(re.findall(r"<h1[^>]*>(.*?)</h1>", self.html, re.S), ["Digitale kerstkaarten die echt <em>tot leven</em> komen"])

    def test_gestructureerde_gegevens_zijn_geldig_en_de_faq_staat_zichtbaar_op_de_pagina(self):
        blokken = {b["@type"]: b for b in json_ld(self.html)}
        self.assertEqual([i["name"] for i in blokken["BreadcrumbList"]["itemListElement"]], ["Home", "Digitale kerstkaarten"])
        self.assertEqual(blokken["BreadcrumbList"]["itemListElement"][1]["item"], f"{settings.BASE_URL}/digitale-kerstkaarten/")
        vragen = blokken["FAQPage"]["mainEntity"]
        self.assertGreaterEqual(len(vragen), 8)
        zichtbaar = html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", self.html)))
        for v in vragen:
            self.assertEqual(v["@type"], "Question")
            self.assertEqual(v["acceptedAnswer"]["@type"], "Answer")
            self.assertIn(v["name"], zichtbaar)
            self.assertIn(v["acceptedAnswer"]["text"], zichtbaar)

    def test_de_pagina_linkt_naar_collectie_prijzen_uitleg_vragen_en_kerstontwerpen(self):
        for pad in ("/ontwerpen/?gelegenheid=kerst", "/prijzen/", "/zo-werkt-het/", "/veelgestelde-vragen/", "/ontwerpen/winterlicht/?gelegenheid=kerst"):
            self.assertIn(f'href="{pad}"', self.html, pad)

    def test_het_kerstfilter_werkt_gewoon_en_wijst_naar_de_pagina(self):
        filter_pagina = Client().get("/ontwerpen/?gelegenheid=kerst")
        self.assertEqual(filter_pagina.status_code, 200)
        self.assertIn("Ontwerpen voor kerst", filter_pagina.content.decode())
        self.assertEqual(canonical(filter_pagina.content.decode()), f"{settings.BASE_URL}/digitale-kerstkaarten/")
        sitemap = Client().get("/sitemap.xml").content.decode()
        self.assertIn(f"<loc>{settings.BASE_URL}/digitale-kerstkaarten/</loc>", sitemap)
        self.assertNotIn("gelegenheid=kerst", sitemap)
        self.assertIn(f"<loc>{settings.BASE_URL}/digitale-trouwkaarten/</loc>", sitemap)      # de andere pagina blijft

    def test_de_homepage_en_kerstontwerpen_linken_naar_de_pagina(self):
        home = Client().get("/").content.decode()
        self.assertIn('<a href="/digitale-kerstkaarten/">digitale kerstkaarten</a>', home)
        kerst = Client().get("/ontwerpen/winterlicht/").content.decode()
        self.assertIn('href="/digitale-kerstkaarten/"', kerst)
        zonder = Client().get("/ontwerpen/balzaal/").content.decode()          # geen kerstontwerp: geen verwijzing
        self.assertNotIn('href="/digitale-kerstkaarten/"', zonder)


class VerjaardagHubTests(VaylideTestCase):
    """/digitale-verjaardagsuitnodigingen/: de landingspagina voor de verjaardag, met het verjaardagsfilter als gewone UI."""

    def setUp(self):
        self.response = Client().get("/digitale-verjaardagsuitnodigingen/")
        self.html = self.response.content.decode()

    def test_pagina_is_indexeerbaar_met_eigen_titel_beschrijving_h1_en_self_canonical(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertNotIn("X-Robots-Tag", self.response.headers)
        self.assertEqual(meta(self.html, "robots"), "")
        self.assertEqual(titel(self.html), "Digitale verjaardagsuitnodiging maken · VAYLIDE")
        self.assertEqual(meta(self.html, "description"), "Maak een digitale verjaardagsuitnodiging die echt tot leven komt. Voeg datum, locatie, RSVP en persoonlijke details toe en deel eenvoudig via WhatsApp.")
        self.assertEqual(canonical(self.html), f"{settings.BASE_URL}/digitale-verjaardagsuitnodigingen/")
        self.assertEqual(meta(self.html, "og:url", "property"), canonical(self.html))
        self.assertEqual(re.findall(r"<h1[^>]*>(.*?)</h1>", self.html, re.S), ["Digitale verjaardagsuitnodigingen die bij <em>jouw feest</em> passen"])

    def test_gestructureerde_gegevens_zijn_geldig_en_de_faq_staat_zichtbaar_op_de_pagina(self):
        blokken = {b["@type"]: b for b in json_ld(self.html)}
        self.assertEqual([i["name"] for i in blokken["BreadcrumbList"]["itemListElement"]], ["Home", "Digitale verjaardagsuitnodigingen"])
        self.assertEqual(blokken["BreadcrumbList"]["itemListElement"][1]["item"], f"{settings.BASE_URL}/digitale-verjaardagsuitnodigingen/")
        vragen = blokken["FAQPage"]["mainEntity"]
        self.assertGreaterEqual(len(vragen), 8)
        zichtbaar = html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", self.html)))
        for v in vragen:
            self.assertEqual(v["@type"], "Question")
            self.assertEqual(v["acceptedAnswer"]["@type"], "Answer")
            self.assertIn(v["name"], zichtbaar)
            self.assertIn(v["acceptedAnswer"]["text"], zichtbaar)

    def test_de_pagina_linkt_naar_collectie_prijzen_uitleg_vragen_en_verjaardagsontwerpen(self):
        for pad in ("/ontwerpen/?gelegenheid=verjaardag", "/prijzen/", "/zo-werkt-het/", "/veelgestelde-vragen/", "/ontwerpen/glitter/?gelegenheid=verjaardag"):
            self.assertIn(f'href="{pad}"', self.html, pad)

    def test_het_verjaardagsfilter_werkt_gewoon_en_wijst_naar_de_pagina(self):
        filter_pagina = Client().get("/ontwerpen/?gelegenheid=verjaardag")
        self.assertEqual(filter_pagina.status_code, 200)
        self.assertIn("Ontwerpen voor verjaardag", filter_pagina.content.decode())
        self.assertEqual(canonical(filter_pagina.content.decode()), f"{settings.BASE_URL}/digitale-verjaardagsuitnodigingen/")
        sitemap = Client().get("/sitemap.xml").content.decode()
        self.assertIn(f"<loc>{settings.BASE_URL}/digitale-verjaardagsuitnodigingen/</loc>", sitemap)
        self.assertNotIn("gelegenheid=verjaardag", sitemap)
        for andere in ("/digitale-trouwkaarten/", "/digitale-kerstkaarten/"):
            self.assertIn(f"<loc>{settings.BASE_URL}{andere}</loc>", sitemap)

    def test_de_homepage_en_ontwerpen_linken_naar_de_pagina(self):
        home = Client().get("/").content.decode()
        self.assertIn('<a href="/digitale-verjaardagsuitnodigingen/">digitale verjaardagsuitnodigingen</a>', home)
        glitter = Client().get("/ontwerpen/glitter/").content.decode()
        self.assertIn('href="/digitale-verjaardagsuitnodigingen/"', glitter)
        zonder = Client().get("/ontwerpen/winterlicht/").content.decode()          # geen verjaardagsontwerp: geen verwijzing
        self.assertNotIn('href="/digitale-verjaardagsuitnodigingen/"', zonder)

    def test_een_ontwerp_voor_meer_gelegenheden_noemt_alle_bijpassende_pagina_s_in_een_regel(self):
        html = Client().get("/ontwerpen/tropisch/").content.decode()          # bruiloft en verjaardag
        regel = re.search(r'<p class="trouw-verwijzing container">(.*?)</p>', html, re.S).group(1)
        self.assertIn('<a href="/digitale-trouwkaarten/">digitale trouwkaarten</a>, <a href="/digitale-verjaardagsuitnodigingen/">digitale verjaardagsuitnodigingen</a> en <a href="/digitale-zakelijke-uitnodigingen/">digitale zakelijke uitnodigingen</a>', regel)


class ZakelijkHubTests(VaylideTestCase):
    """/digitale-zakelijke-uitnodigingen/: de landingspagina voor zakelijke evenementen, met het zakelijke filter als gewone UI."""

    def setUp(self):
        self.response = Client().get("/digitale-zakelijke-uitnodigingen/")
        self.html = self.response.content.decode()

    def test_pagina_is_indexeerbaar_met_eigen_titel_beschrijving_h1_en_self_canonical(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertNotIn("X-Robots-Tag", self.response.headers)
        self.assertEqual(meta(self.html, "robots"), "")
        self.assertEqual(titel(self.html), "Digitale zakelijke uitnodiging maken · VAYLIDE")
        self.assertEqual(meta(self.html, "description"), "Maak een digitale zakelijke uitnodiging voor een opening, bedrijfsfeest, jubileum of event. Met RSVP, programma, locatie en eenvoudig delen via link of QR-code.")
        self.assertEqual(canonical(self.html), f"{settings.BASE_URL}/digitale-zakelijke-uitnodigingen/")
        self.assertEqual(meta(self.html, "og:url", "property"), canonical(self.html))
        self.assertEqual(re.findall(r"<h1[^>]*>(.*?)</h1>", self.html, re.S), ["Digitale zakelijke uitnodigingen met een <em>professionele</em> uitstraling"])

    def test_gestructureerde_gegevens_zijn_geldig_en_de_faq_staat_zichtbaar_op_de_pagina(self):
        blokken = {b["@type"]: b for b in json_ld(self.html)}
        self.assertEqual([i["name"] for i in blokken["BreadcrumbList"]["itemListElement"]], ["Home", "Digitale zakelijke uitnodigingen"])
        self.assertEqual(blokken["BreadcrumbList"]["itemListElement"][1]["item"], f"{settings.BASE_URL}/digitale-zakelijke-uitnodigingen/")
        vragen = blokken["FAQPage"]["mainEntity"]
        self.assertGreaterEqual(len(vragen), 9)
        zichtbaar = html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", self.html)))
        for v in vragen:
            self.assertEqual(v["@type"], "Question")
            self.assertEqual(v["acceptedAnswer"]["@type"], "Answer")
            self.assertIn(v["name"], zichtbaar)
            self.assertIn(v["acceptedAnswer"]["text"], zichtbaar)

    def test_de_pagina_linkt_naar_collectie_prijzen_uitleg_vragen_en_zakelijke_ontwerpen(self):
        for pad in ("/ontwerpen/?gelegenheid=zakelijk", "/prijzen/", "/zo-werkt-het/", "/veelgestelde-vragen/", "/ontwerpen/gala/?gelegenheid=zakelijk"):
            self.assertIn(f'href="{pad}"', self.html, pad)

    def test_het_zakelijke_filter_werkt_gewoon_en_wijst_naar_de_pagina(self):
        filter_pagina = Client().get("/ontwerpen/?gelegenheid=zakelijk")
        self.assertEqual(filter_pagina.status_code, 200)
        self.assertIn("Ontwerpen voor zakelijk", filter_pagina.content.decode())
        self.assertEqual(canonical(filter_pagina.content.decode()), f"{settings.BASE_URL}/digitale-zakelijke-uitnodigingen/")
        sitemap = Client().get("/sitemap.xml").content.decode()
        self.assertIn(f"<loc>{settings.BASE_URL}/digitale-zakelijke-uitnodigingen/</loc>", sitemap)
        self.assertNotIn("gelegenheid=zakelijk", sitemap)
        for andere in ("/digitale-trouwkaarten/", "/digitale-kerstkaarten/", "/digitale-verjaardagsuitnodigingen/"):
            self.assertIn(f"<loc>{settings.BASE_URL}{andere}</loc>", sitemap)

    def test_de_homepage_en_zakelijke_ontwerpen_linken_naar_de_pagina(self):
        home = Client().get("/").content.decode()
        self.assertIn('<a href="/digitale-zakelijke-uitnodigingen/">digitale zakelijke uitnodigingen</a>', home)
        gala = Client().get("/ontwerpen/gala/").content.decode()
        self.assertIn('href="/digitale-zakelijke-uitnodigingen/"', gala)
        zonder = Client().get("/ontwerpen/winterlicht/").content.decode()          # geen zakelijk ontwerp: geen verwijzing
        self.assertNotIn('href="/digitale-zakelijke-uitnodigingen/"', zonder)

    def test_de_combinatieregel_noemt_alleen_de_hubs_van_het_ontwerp(self):
        def regel(slug):
            html = Client().get(f"/ontwerpen/{slug}/").content.decode()
            return re.findall(r'href="(/digitale-[a-z-]+/)"', re.search(r'<p class="trouw-verwijzing container">(.*?)</p>', html, re.S).group(1))

        self.assertEqual(regel("strak"), ["/digitale-zakelijke-uitnodigingen/"])                         # zakelijk en jubileum
        self.assertEqual(regel("gala"), ["/digitale-trouwkaarten/", "/digitale-zakelijke-uitnodigingen/"])      # zakelijk, bruiloft, jubileum
        self.assertEqual(regel("glitter"), ["/digitale-verjaardagsuitnodigingen/", "/digitale-zakelijke-uitnodigingen/"])
        self.assertEqual(regel("avondgoud"), ["/digitale-trouwkaarten/", "/digitale-verjaardagsuitnodigingen/", "/digitale-zakelijke-uitnodigingen/"])
        self.assertEqual(regel("winterlicht"), ["/digitale-kerstkaarten/"])


class UitnodigingMakenHubTests(VaylideTestCase):
    """/digitale-uitnodiging-maken/: de brede instappagina met routes naar de vier landingspagina's."""

    def setUp(self):
        self.response = Client().get("/digitale-uitnodiging-maken/")
        self.html = self.response.content.decode()

    def test_pagina_is_indexeerbaar_met_eigen_titel_beschrijving_h1_en_self_canonical(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertNotIn("X-Robots-Tag", self.response.headers)
        self.assertEqual(meta(self.html, "robots"), "")
        self.assertEqual(titel(self.html), "Digitale uitnodiging maken | Online uitnodiging · VAYLIDE")
        self.assertEqual(meta(self.html, "description"), "Maak eenvoudig een digitale uitnodiging met een bijzondere opening, RSVP, datum, locatie en persoonlijke details. Deel via WhatsApp, link of QR-code.")
        self.assertEqual(canonical(self.html), f"{settings.BASE_URL}/digitale-uitnodiging-maken/")
        self.assertEqual(meta(self.html, "og:url", "property"), canonical(self.html))
        self.assertEqual(re.findall(r"<h1[^>]*>(.*?)</h1>", self.html, re.S), ["Digitale uitnodiging maken die echt <em>tot leven</em> komt"])

    def test_gestructureerde_gegevens_zijn_geldig_en_de_faq_staat_zichtbaar_op_de_pagina(self):
        blokken = {b["@type"]: b for b in json_ld(self.html)}
        self.assertEqual([i["name"] for i in blokken["BreadcrumbList"]["itemListElement"]], ["Home", "Digitale uitnodiging maken"])
        vragen = blokken["FAQPage"]["mainEntity"]
        self.assertGreaterEqual(len(vragen), 10)
        zichtbaar = html_lib.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", self.html)))
        for v in vragen:
            self.assertIn(v["name"], zichtbaar)
            self.assertIn(v["acceptedAnswer"]["text"], zichtbaar)

    def test_de_pagina_linkt_naar_de_vier_hubs_collectie_prijzen_uitleg_en_vragen(self):
        for pad in ("/digitale-trouwkaarten/", "/digitale-verjaardagsuitnodigingen/", "/digitale-kerstkaarten/", "/digitale-zakelijke-uitnodigingen/",
                    "/ontwerpen/", "/prijzen/", "/zo-werkt-het/", "/veelgestelde-vragen/"):
            self.assertIn(f'href="{pad}"', self.html, pad)

    def test_sitemap_homepage_uitleg_en_collectie_linken_naar_de_pagina_zonder_hun_canonical_te_wijzigen(self):
        sitemap = Client().get("/sitemap.xml").content.decode()
        self.assertIn(f"<loc>{settings.BASE_URL}/digitale-uitnodiging-maken/</loc>", sitemap)
        anker = '<a href="/digitale-uitnodiging-maken/">digitale uitnodiging maken</a>'
        for pad, canoniek in (("/", "/"), ("/zo-werkt-het/", "/zo-werkt-het/"), ("/ontwerpen/", "/ontwerpen/")):
            html = Client().get(pad).content.decode()
            self.assertIn(anker, html, pad)
            self.assertEqual(canonical(html), f"{settings.BASE_URL}{canoniek}", pad)
        self.assertEqual(titel(Client().get("/").content.decode()), "Digitale uitnodigingen die je beleeft · VAYLIDE")


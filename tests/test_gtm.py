"""Google Analytics 4 via Google Tag Manager (core/analytics.py, static/js/toestemming.js, docs/GTM.md): alleen na toestemming, alleen op de pagina's waar het mag,
zonder iets van wat een klant of gast invult, met vaste gebeurtenissen uit bestaande routes en toestanden. Zonder VIERLIEF_GTM_ID verandert er niets."""
import html as htmllib
import json
import re
from unittest import mock

from django.conf import settings
from django.test import Client, override_settings

from core import analytics, privacyverklaring as pv
from orders.models import Order

from .helpers import VaylideTestCase

GTM = "GTM-TESTID1"
UID = "0f0f0f0f-0000-0000-0000-000000000000"
JS = (settings.BASE_DIR / "static" / "js" / "toestemming.js").read_text(encoding="utf-8")


def csp(response):
    return response["Content-Security-Policy"]


def events(html: str) -> list[dict]:
    m = re.search(r'data-gtm-events="([^"]*)"', html)
    return json.loads(htmllib.unescape(m.group(1))) if m else []


class ZonderGtmTests(VaylideTestCase):
    def test_zonder_id_niets_van_google(self):
        for adres in ("/", "/ontwerpen/", "/digitale-trouwkaarten/", "/digitale-kerstkaarten/", "/maken/?gelegenheid=bruiloft", "/privacy/"):
            r = Client().get(adres)
            html = r.content.decode()
            self.assertNotIn("data-gtm", html, adres)
            self.assertNotIn("googletagmanager", html + csp(r), adres)
            self.assertNotIn("google-analytics", csp(r), adres)
        self.assertNotIn(pv.LABELS["google"], pv.open_points())
        self.assertNotIn("Google Analytics", Client().get("/privacy/").content.decode())

    def test_zonder_id_komt_er_niets_in_de_sessie(self):
        c = Client()
        c.get("/ontwerpen/")
        self.assertNotIn(analytics.SESSIE_EVENTS, c.session)
        self.assertNotIn(analytics.SESSIE_GEZIEN, c.session)


@override_settings(GTM_ID=GTM, ANALYTICS_OMGEVING="staging")
class PaginaRegelsTests(VaylideTestCase):
    def test_gtm_mag_op_dezelfde_paginas_als_clarity_en_op_de_bevestiging_van_een_bestelling(self):
        mag = ["/", "/ontwerpen/", "/ontwerpen/kerststad/", "/inspiratie/", "/prijzen/", "/maken/", f"/maken/{UID}/gegevens/", f"/maken/{UID}/bestellen/",
               f"/bestelling/{UID}/"]
        nooit = ["/u/sanne-en-daan-abc/", "/account/", "/inloggen/", "/beheer/", f"/{settings.ADMIN_URL}", "/betalen/test/1/", "/bestelling/1/",
                 f"/bestelling/{UID}/status.json", f"/bestelling/{UID}/opnieuw-betalen/", "/voorbeeld/kerststad/", f"/maken/{UID}/voorbeeld/weergave/",
                 f"/maken/{UID}/voorbeeld/live/", "/maken/x/media/y/groot/", "/contact/", "/privacy/", "/zo-werkt-het/"]
        for pad in mag:
            self.assertTrue(analytics.gtm_op_pagina(pad), pad)
        for pad in nooit:
            self.assertFalse(analytics.gtm_op_pagina(pad), pad)

    def test_banner_script_en_csp_alleen_waar_het_mag_en_geen_script_in_de_pagina(self):
        r = Client().get("/ontwerpen/")
        html = r.content.decode()
        self.assertIn(f'data-gtm-id="{GTM}" data-gtm-hier="1" data-gtm-omgeving="staging" data-gtm-debug="1"', html)
        self.assertEqual(html.count("js/toestemming.js"), 1)
        self.assertNotIn("googletagmanager.com", html)                                    # het script staat nergens in de pagina: alleen het script na Accepteren
        self.assertIn("script-src 'self'", csp(r))
        self.assertIn("https://www.googletagmanager.com", csp(r))
        self.assertIn("connect-src 'self' https://www.googletagmanager.com https://*.google-analytics.com https://*.analytics.google.com", csp(r))
        for adres in ("/contact/", "/inloggen/", "/privacy/"):
            r = Client().get(adres)
            self.assertIn('data-gtm-hier="0"', r.content.decode(), adres)
            self.assertNotIn("googletagmanager", csp(r), adres)
            self.assertNotIn("google-analytics", csp(r), adres)

    @override_settings(ANALYTICS_OMGEVING="productie")
    def test_productie_meet_niet_als_testverkeer(self):
        html = Client().get("/ontwerpen/").content.decode()
        self.assertIn('data-gtm-omgeving="productie"', html)
        self.assertNotIn("data-gtm-debug", html)

    @override_settings(CLARITY_ID="abcdefghij")
    def test_een_toestemmingsvraag_voor_beide_en_clarity_blijft_zoals_het_was(self):
        r = Client().get("/ontwerpen/")
        html = r.content.decode()
        self.assertIn("Microsoft Clarity en Google Analytics", html)
        self.assertIn('data-clarity-id="abcdefghij" data-clarity-hier="1"', html)
        self.assertIn("clarity.ms", csp(r))
        self.assertIn("googletagmanager.com", csp(r))
        # Op de bevestiging van een bestelling draait Google (voor één gebeurtenis) maar Clarity nooit.
        r = Client().get(f"/bestelling/{UID}/")
        self.assertNotIn("clarity.ms", csp(r))

    def test_alleen_google_toont_de_vraag_zonder_clarity_te_noemen(self):
        html = Client().get("/").content.decode()
        self.assertIn("Met Google Analytics meten we", html)
        self.assertNotIn("Clarity", html.split('id="toestemming-tekst"')[1].split("</p>")[0])


@override_settings(GTM_ID=GTM, ANALYTICS_OMGEVING="staging")
class SchoneGegevensTests(VaylideTestCase):
    def test_paginalocatie_zonder_id_s_en_zonder_ongekeurde_query(self):
        c = Client()
        r = c.post("/maken/", {"occasion": "bruiloft", "template": "liefde-op-papier", "soort": "uitnodiging"})
        gegevens = r["Location"]
        uid = re.search(r"/maken/([0-9a-f-]{36})/", gegevens).group(1)
        html = c.get(f"{gegevens}?naam=Zwaluwstaart&gelegenheid=bruiloft&ontwerp=ja-woord&email=a@b.nl").content.decode()
        self.assertIn(f'data-gtm-url="{settings.BASE_URL}/maken/:id/gegevens/?gelegenheid=bruiloft&amp;ontwerp=ja-woord"', html)
        self.assertNotIn(uid, html.split('data-gtm-url="')[1].split('"')[0])
        self.assertNotIn("Zwaluwstaart", html)
        self.assertNotIn("a@b.nl", html)

    def test_query_met_vreemde_waarden_valt_weg(self):
        html = Client().get("/ontwerpen/?gelegenheid=<script>&ontwerp=Ja Woord&q=sanne").content.decode()
        self.assertIn(f'data-gtm-url="{settings.BASE_URL}/ontwerpen/"', html)

    def test_collectie_geeft_view_collection_elke_keer_en_zonder_parameters(self):
        for _ in range(2):
            self.assertEqual(events(Client().get("/ontwerpen/").content.decode()), [{"event": "view_collection"}])
        self.assertEqual(events(Client().get("/").content.decode()), [])


@override_settings(GTM_ID=GTM, ANALYTICS_OMGEVING="staging")
class StudioEnBestelEventsTests(VaylideTestCase):
    def start(self, c, ontwerp="liefde-op-papier", occasion="bruiloft"):
        r = c.post("/maken/", {"occasion": occasion, "template": ontwerp, "soort": "uitnodiging"})
        self.assertEqual(r.status_code, 302, r.content[:200])
        return r["Location"]

    def test_select_design_start_studio_en_reach_checkout_elk_een_keer_met_alleen_openbare_waarden(self):
        c = Client()
        gegevens = self.start(c)
        html = c.get(gegevens).content.decode()
        gebeurd = events(html)
        self.assertEqual([e["event"] for e in gebeurd], ["select_design", "start_studio"])
        for e in gebeurd:
            self.assertEqual({k: v for k, v in e.items() if k != "event"}, {"design": "liefde-op-papier", "occasion": "bruiloft"})
        # opnieuw laden of heen en weer: niet nog eens
        self.assertEqual(events(c.get(gegevens).content.decode()), [])
        bestellen = gegevens.replace("/gegevens/", "/bestellen/")
        first = events(c.get(bestellen).content.decode())
        self.assertEqual([e["event"] for e in first], ["reach_checkout"])
        self.assertEqual(first[0]["design"], "liefde-op-papier")
        self.assertEqual(events(c.get(bestellen).content.decode()), [])

    def test_een_ander_concept_krijgt_zijn_eigen_start_studio(self):
        c = Client()
        self.start(c)
        andere = self.start(c, ontwerp="avondgoud", occasion="verjaardag")
        gebeurd = events(c.get(andere).content.decode())
        self.assertIn("start_studio", [e["event"] for e in gebeurd])

    def test_gebeurtenissen_wachten_op_een_pagina_waar_meten_mag_en_lekken_niet_naar_andere_pagina_s(self):
        c = Client()
        gegevens = self.start(c)
        c.get("/contact/")                                         # hier mag niets: de wachtrij blijft staan
        self.assertTrue(c.session.get(analytics.SESSIE_EVENTS))
        self.assertNotIn("data-gtm-events", c.get("/contact/").content.decode())
        self.assertEqual([e["event"] for e in events(c.get(gegevens).content.decode())], ["select_design", "start_studio"])

    def test_geen_gebeurtenis_in_de_html_met_namen_of_teksten(self):
        c = Client()
        gegevens = self.start(c)
        uid = re.search(r"/maken/([0-9a-f-]{36})/", gegevens).group(1)
        from invitations.models import Invitation

        inv = Invitation.objects.get(uid=uid)
        inv.draft_content = {**(inv.draft_content or {}), "names": {"person_1": "Zwaluwstaart", "person_2": "Kievit"}}
        inv.save()
        html = c.get(gegevens).content.decode()
        for sleutel in ("data-gtm-url", "data-gtm-events"):
            waarde = html.split(sleutel + '="')[1].split('"')[0]
            self.assertNotIn("Zwaluwstaart", waarde)
            self.assertNotIn(uid, waarde)

    def test_purchase_success_alleen_bij_een_betaalde_bestelling_en_een_keer(self):
        klant = self.make_customer()
        inv = self.make_invitation(owner=klant)
        c = Client()
        c.force_login(klant)
        self.pay(inv, klant)
        order = Order.objects.get()
        self.assertEqual(order.status, Order.Status.PAID)
        html = c.get(f"/bestelling/{order.uid}/").content.decode()
        e = events(html)
        self.assertEqual(len(e), 1)
        self.assertEqual(e[0], {"event": "purchase_success", "design": inv.template_version.template.slug, "occasion": inv.occasion,
                                "package": order.package_code, "value": round(order.total_cents / 100, 2), "currency": "EUR"})
        # Google krijgt op de bevestiging een vaste titel en geen verwijzer: de zichtbare titel heeft het bestelnummer, de verwijzer kan een betaalreferentie hebben.
        self.assertIn(order.number, html.split("<title>")[1].split("</title>")[0])
        self.assertIn(f'data-gtm-titel="{analytics.BESTELLING_TITEL}"', html)
        self.assertIn('data-gtm-ref-leeg="1"', html)
        for waarde in ("data-gtm-url", "data-gtm-titel", "data-gtm-events"):
            deel = html.split(waarde + '="')[1].split('"')[0]
            self.assertNotIn(order.number, deel)
            self.assertNotIn(str(order.uid), deel)
        self.assertNotIn(str(order.uid), html.split('data-gtm-url="')[1].split('"')[0])
        self.assertNotIn(order.number, html.split('data-gtm-events="')[1].split('"')[0] if "data-gtm-events" in html else "")
        self.assertEqual(events(c.get(f"/bestelling/{order.uid}/").content.decode()), [])      # herladen telt niet nog een keer

    def test_andere_paginas_houden_hun_eigen_titel_en_verwijzer(self):
        html = Client().get("/ontwerpen/").content.decode()
        self.assertNotIn("data-gtm-titel", html)
        self.assertNotIn("data-gtm-ref-leeg", html)

    def test_geen_purchase_success_zolang_de_provider_niet_heeft_bevestigd(self):
        klant = self.make_customer()
        inv = self.make_invitation(owner=klant)
        c = Client()
        c.force_login(klant)
        from orders.services import start_checkout

        with self.captureOnCommitCallbacks(execute=True):
            start_checkout(inv, user=klant, package_code="essentieel", optional_codes=[], terms_accepted=True)
        order = Order.objects.get()
        self.assertNotEqual(order.status, Order.Status.PAID)
        self.assertEqual(events(c.get(f"/bestelling/{order.uid}/").content.decode()), [])
        self.assertNotIn(analytics.SESSIE_EVENTS, c.session)


class ToestemmingScriptTests(VaylideTestCase):
    def test_google_laadt_alleen_na_toestemming_een_keer_en_eerst_de_toestemming(self):
        blok = JS[JS.index("function laadGtm()"):JS.index("function toon(")]
        self.assertIn("if (!gtmId || !gtmHier || window.__vaylideGtm) return;", blok)
        self.assertLess(blok.index('gtag("consent", "default"'), blok.index("document.head.appendChild(s)"))      # toestemming vóór het laden
        self.assertIn('ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied", analytics_storage: "granted"', blok)
        self.assertLess(blok.index("dl.push(gegevens)"), blok.index("document.head.appendChild(s)"))
        self.assertLess(blok.index("document.head.appendChild(s)"), blok.index("JSON.parse(ruw)"))                   # gebeurtenissen na de start van de container
        self.assertEqual(JS.count("laadGtm();"), 2)                                       # alleen bij een bewaard 'ja' en bij Accepteren
        self.assertIn('if (nu === "ja") { laadClarity(); laadGtm(); }', JS)
        self.assertNotIn("window.dataLayer = window.dataLayer || [];\n  var banner", JS)  # geen dataLayer vóór de toestemming

    def test_geen_gegevens_van_de_bezoeker_in_de_datalaag(self):
        blok = JS[JS.index("function schoneVerwijzer()"):JS.index("function toon(")]
        for verboden in ("document.title", "location.search", "location.href", ".value", "innerText", "textContent", "document.cookie"):
            self.assertNotIn(verboden, blok, verboden)
        self.assertIn("replace(UUID, \":id\")", blok)                                      # de verwijzer zonder id's, zonder query
        self.assertIn("u.origin + u.pathname", blok)
        self.assertIn('data-gtm-ref-leeg', blok)
        self.assertIn('gegevens.pagina_titel = banner.getAttribute("data-gtm-titel")', blok)

    def test_intrekken_sluit_eerst_het_verkeer_dan_denied_dan_cookies_dan_herladen(self):
        klik = JS[JS.index("// Weigeren of intrekken"):JS.index('document.querySelectorAll("[data-cookie-instellingen]")')]
        volgorde = [klik.index(x) for x in ("sluitVerkeer();", "stopGtm();", "wisGoogleCookies();\n        location", "location.reload();")]
        self.assertEqual(volgorde, sorted(volgorde))
        self.assertIn('analytics_storage: "denied"', JS[JS.index("function stopGtm()"):JS.index("function laadClarity()")])
        self.assertIn("img-src 'self' data: blob:", JS)
        self.assertIn("/^(_ga|_gid|_gat|_gcl_|_gac_)/", JS)

    def test_intrekken_sluit_ook_de_verzendkanalen_van_google_voor_alles_andere(self):
        klik = JS[JS.index("// Weigeren of intrekken"):JS.index('document.querySelectorAll("[data-cookie-instellingen]")')]
        # De eerste handeling na de klik: Google en alle verkeer dicht, vóór cookies, consent update en herladen.
        self.assertLess(klik.index("sluitGoogle(); sluitVerkeer();"), klik.index("wisClarityCookies();"))
        self.assertLess(klik.index("sluitGoogle(); sluitVerkeer();"), klik.index("stopGtm();"))
        # De bewaking staat vóór het laden van Google Tag Manager en dekt beacon, fetch, XHR, beeldjes en scripts.
        laad = JS[JS.index("function laadGtm()"):JS.index("function toon(")]
        self.assertLess(laad.index("bewaakGoogle();"), laad.index("document.head.appendChild(s)"))
        bewaking = JS[JS.index("function bewaakGoogle()"):JS.index("function schoneVerwijzer()")]
        for kanaal in ("navigator.sendBeacon", "window.fetch", "XMLHttpRequest.prototype.send", 'HTMLImageElement.prototype, "src"', "Element.prototype.setAttribute", "Node.prototype.appendChild", "Node.prototype.insertBefore"):
            self.assertIn(kanaal, bewaking, kanaal)
        self.assertGreaterEqual(bewaking.count("dicht() &&"), 7)
        for host in ("google-analytics", "analytics\\.google\\.com", "googletagmanager"):
            self.assertIn(host, JS)
        self.assertIn("window.__vaylideGoogleDicht = true", JS)
        # Zonder toestemming past het script niets aan: de bewaking staat alleen in laadGtm.
        self.assertEqual(JS.count("bewaakGoogle();"), 1)

    def test_zonder_keuze_of_na_weigeren_wordt_er_niets_geladen(self):
        eind = JS[JS.index("var nu = keuze();"):]
        self.assertIn('if (nu === "ja") { laadClarity(); laadGtm(); }', eind)
        self.assertIn('else if (nu === "nee") { wisClarityCookies(); wisGoogleCookies(); }', eind)


@override_settings(GTM_ID=GTM, ANALYTICS_OMGEVING="staging")
class PrivacyverklaringTests(VaylideTestCase):
    def test_goedgekeurde_tekst_cookies_en_geen_conceptmarkering(self):
        html = Client().get("/privacy/").content.decode()
        self.assertIn("Google Analytics 4 en Google Tag Manager", html)
        self.assertTrue(pv.GOOGLE_TEKST_GOEDGEKEURD)
        self.assertNotIn("De tekst over Google Analytics en Google Tag Manager hieronder is een concept", html)
        self.assertIn("Voor gebruikers in de EU/EER registreert of bewaart Google Analytics het afzonderlijke IP-adres niet.", html)
        self.assertNotIn("Google slaat je IP-adres niet op", html)
        self.assertIn("2 maanden en gegevens die aan het willekeurige bezoekers-id in de cookie zijn gekoppeld 14 maanden", html)       # zoals in GA4 ingesteld
        self.assertIn("je foto's, de antwoorden van gasten en je bestelnummer", html)                                                  # waar zolang titel en verwijzer schoon zijn
        for cookie in ("<code>_ga</code>", "<code>vaylide_analytics</code>"):
            self.assertIn(cookie, html)
        self.assertNotIn(pv.LABELS["google"], pv.open_points())
        self.assertIn("Google Ireland Limited", html)
        self.assertNotIn("Wij gebruiken geen advertentie-, analyse- of volgcookies", html)

    def test_zonder_goedkeuring_blijft_het_een_concept_en_een_open_punt(self):
        with mock.patch.object(pv, "GOOGLE_TEKST_GOEDGEKEURD", False):
            html = Client().get("/privacy/").content.decode()
            self.assertIn("De tekst over Google Analytics en Google Tag Manager hieronder is een concept", html)
            self.assertIn(pv.LABELS["google"], pv.open_points())

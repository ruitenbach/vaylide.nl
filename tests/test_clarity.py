"""Microsoft Clarity: alleen met een ingesteld project-id, alleen na toestemming (consentv2), alleen op publieke pagina's en de Studio,
gevoelige inhoud afgeschermd, en live niet zonder goedgekeurde privacytekst. Zie docs/CLARITY.md."""
import re
from pathlib import Path

from django.conf import settings
from django.test import Client, override_settings

from core import privacyverklaring as pv
from core.analytics import clarity_op_pagina

from .helpers import VaylideTestCase

ID = "yuemn2aqz1"
JS = (Path(settings.BASE_DIR) / "static/js/toestemming.js").read_text(encoding="utf-8")
JS_CODE = re.sub(r"/\*.*?\*/", "", JS, flags=re.S)


def csp(response):
    return response["Content-Security-Policy"]


class ZonderClarityTests(VaylideTestCase):
    def test_zonder_id_niets_van_clarity(self):
        for adres in ("/", "/ontwerpen/", "/maken/?gelegenheid=bruiloft", "/privacy/"):
            r = Client().get(adres)
            html = r.content.decode()
            self.assertNotIn("toestemming.js", html, adres)
            self.assertNotIn("data-toestemming", html, adres)
            self.assertNotIn("data-cookie-instellingen", html, adres)
            self.assertNotIn("clarity.ms", csp(r), adres)
        privacy = Client().get("/privacy/").content.decode()
        self.assertIn("Wij gebruiken geen advertentie-, analyse- of volgcookies", privacy)
        self.assertNotIn("Microsoft Clarity", privacy)
        self.assertNotIn(pv.LABELS["clarity"], pv.open_points())


@override_settings(CLARITY_ID=ID)
class PaginaRegelsTests(VaylideTestCase):
    def test_clarity_mag_alleen_op_publieke_paginas_en_de_studio(self):
        mag = ["/", "/ontwerpen/", "/ontwerpen/kerststad/", "/ontwerpen/?gelegenheid=kerst".split("?")[0], "/inspiratie/", "/prijzen/",
               "/maken/", "/maken/0f0f0f0f-0000-0000-0000-000000000000/gegevens/", "/maken/0f0f0f0f-0000-0000-0000-000000000000/voorbeeld/",
               "/maken/0f0f0f0f-0000-0000-0000-000000000000/bestellen/"]
        nooit = ["/u/sanne-en-daan-abc/", "/account/", "/account/uitnodiging/x/gasten/", "/inloggen/", "/beheer/", f"/{settings.ADMIN_URL}",
                 "/betalen/test/1/", "/bestelling/1/", "/voorbeeld/kerststad/", "/maken/0f0f0f0f-0000-0000-0000-000000000000/voorbeeld/weergave/",
                 "/maken/0f0f0f0f-0000-0000-0000-000000000000/voorbeeld/live/", "/maken/x/media/y/groot/", "/contact/", "/zo-werkt-het/"]
        for pad in mag:
            self.assertTrue(clarity_op_pagina(pad), pad)
        for pad in nooit:
            self.assertFalse(clarity_op_pagina(pad), pad)

    def test_script_banner_en_csp_alleen_waar_het_mag(self):
        for adres in ("/", "/ontwerpen/", "/ontwerpen/kerststad/", "/inspiratie/", "/prijzen/", "/maken/?gelegenheid=bruiloft"):
            r = Client().get(adres)
            html = r.content.decode()
            self.assertEqual(r.status_code, 200, adres)
            self.assertEqual(html.count("js/toestemming.js"), 1, adres)                 # één keer
            self.assertIn(f'data-clarity-id="{ID}" data-clarity-hier="1"', html, adres)
            self.assertIn("https://www.clarity.ms https://*.clarity.ms", csp(r), adres)
            self.assertIn("connect-src 'self' https://*.clarity.ms https://c.bing.com", csp(r), adres)
            self.assertIn("img-src 'self' data: blob: https://*.clarity.ms https://c.bing.com", csp(r), adres)
            self.assertIn("data-cookie-instellingen", html, adres)
            self.assertNotIn("clarity.ms/tag", html, adres)                              # het script zelf staat nergens in de pagina
        # Op andere pagina's van de site: wel de link Cookie-instellingen (keuze wijzigen), maar Clarity draait er niet en de CSP blijft dicht.
        for adres in ("/contact/", "/inloggen/", "/privacy/"):
            r = Client().get(adres)
            self.assertIn('data-clarity-hier="0"', r.content.decode(), adres)
            self.assertNotIn("clarity.ms", csp(r), adres)

    def test_uitnodigingen_mijn_vaylide_en_beheer_blijven_dicht(self):
        owner = self.make_customer()
        inv = self.published(owner=owner)
        r = Client().get(inv.public_path)
        self.assertNotIn("clarity", r.content.decode().lower())
        self.assertNotIn("clarity.ms", csp(r))
        c = Client()
        c.force_login(owner)
        for adres in ("/account/", f"/account/uitnodiging/{inv.uid}/gasten/"):
            r = c.get(adres)
            self.assertEqual(r.status_code, 200, adres)
            self.assertIn('data-clarity-hier="0"', r.content.decode(), adres)
            self.assertNotIn("clarity.ms", csp(r), adres)
        staff = Client()
        staff.force_login(self.make_staff())
        r = staff.get("/beheer/")
        self.assertNotIn("clarity.ms", csp(r))
        self.assertNotIn('data-clarity-hier="1"', r.content.decode())


@override_settings(CLARITY_ID=ID)
class AfschermenTests(VaylideTestCase):
    def test_alles_van_een_concept_in_de_studio_is_afgeschermd(self):
        owner = self.make_customer()
        inv = self.make_invitation(owner=owner)
        c = Client()
        c.force_login(owner)
        for stap in ("gegevens", "programma", "aanmelden", "fotos", "stijl", "voorbeeld", "bestellen"):
            html = c.get(f"/maken/{inv.uid}/{stap}/").content.decode()
            masker = html.index('data-clarity-mask="True"')
            # Alles vanaf het afgeschermde blok: alle formulieren, velden, de live kaart en de voorvertoning staan erbinnen.
            for teken in ("<form", "<input", "<textarea", "<iframe"):
                eerste = html.find(teken, html.index("<main"))
                if eerste >= 0:
                    self.assertGreater(eerste, masker, f"{stap}: {teken} staat vóór het afgeschermde blok")
            self.assertNotIn("Anna", html[: masker])                                    # geen namen buiten het afgeschermde blok
            if stap == "gegevens":
                self.assertIn("Anna", html[masker:], stap)                               # (de naam staat wel in het formulier zelf)

    def test_startpagina_schermt_eerdere_concepten_en_het_eigen_e_mailadres_af(self):
        owner = self.make_customer("persoonlijk@example.com")
        self.make_invitation(owner=owner)
        c = Client()
        c.force_login(owner)
        html = c.get("/maken/", {"gelegenheid": "bruiloft"}).content.decode()
        self.assertRegex(html, r'<div class="resume-box" data-clarity-mask="True">')
        blok = html[html.index('class="kies__account small muted" data-clarity-mask="True"') - 5:]
        self.assertIn("persoonlijk@example.com", blok[:400])

    def test_het_script_schermt_bij_het_laden_ook_alle_invoer_en_frames_af(self):
        self.assertIn('querySelectorAll("form, input, textarea, select, iframe, [data-gevoelig], .flash-wrap")', JS_CODE)
        self.assertIn('setAttribute("data-clarity-mask", "True")', JS_CODE)
        self.assertLess(JS_CODE.index("maskeer();"), JS_CODE.index('s.src = "https://www.clarity.ms/tag/"'))


class ToestemmingScriptTests(VaylideTestCase):
    def test_consentv2_bij_accepteren_en_intrekken_en_nooit_de_oude_api(self):
        self.assertIn('window.clarity("consentv2", { ad_Storage: "denied", analytics_Storage: "granted" });', JS_CODE)
        self.assertIn('window.clarity("consentv2", { ad_Storage: "denied", analytics_Storage: "denied" });', JS_CODE)
        self.assertNotRegex(JS_CODE, r'clarity\(\s*["\']consent["\']')                 # niet de oude consent-API
        # Toestemming gaat vóór het laden van het script in de wachtrij.
        self.assertLess(JS_CODE.index('analytics_Storage: "granted"'), JS_CODE.index("document.head.appendChild(s)"))

    def test_eenmaal_laden_async_en_alleen_met_toestemming_op_een_toegestane_pagina(self):
        self.assertIn("if (!id || !hier || window.__vaylideClarity) return;", JS_CODE)
        self.assertIn("s.async = true;", JS_CODE)
        self.assertIn('if (nu === "ja") laadClarity();', JS_CODE)
        self.assertEqual(JS_CODE.count("laadClarity();"), 2)                          # alleen bij een bewaard 'ja' en bij Accepteren
        self.assertIn('Max-Age=" + JAAR', JS_CODE)
        self.assertIn("var JAAR = 365 * 24 * 60 * 60;", JS_CODE)
        self.assertIn('["_clck", "_clsk"]', JS_CODE)
        self.assertIn("location.reload()", JS_CODE)

    @override_settings(CLARITY_ID=ID)
    def test_banner_heeft_twee_gelijkwaardige_knoppen(self):
        html = Client().get("/").content.decode()
        knoppen = re.findall(r'<button type="button" class="([^"]+)" data-toestemming-keuze="(ja|nee)"', html)
        self.assertEqual([k[1] for k in knoppen], ["ja", "nee"])
        self.assertEqual(knoppen[0][0], knoppen[1][0])                                  # zelfde opmaak
        self.assertIn(">Accepteren</button>", html)
        self.assertIn(">Weigeren</button>", html)
        self.assertRegex(html, r'<section class="toestemming" data-toestemming[^>]*hidden>')   # verschijnt pas via het script


@override_settings(CLARITY_ID=ID)
class PrivacyTekstTests(VaylideTestCase):
    def test_concepttekst_staat_klaar_en_is_een_open_besluit(self):
        html = Client().get("/privacy/").content.decode()
        for nodig in ("Microsoft Clarity", "sessieopnames", "klikken", "scrollen", "gebruiksgegevens", "<code>_clck</code>", "<code>_clsk</code>",
                      "Microsoft Azure", "datacenters van Microsoft in de Verenigde Staten", "toestemming altijd intrekken", "Cookie-instellingen",
                      "https://privacy.microsoft.com/privacystatement", "vaylide_analytics", "Concept, juridisch nog te beoordelen"):
            self.assertIn(nodig, html, nodig)
        self.assertNotIn("Wij gebruiken geen advertentie-, analyse- of volgcookies", html)
        self.assertIn("Microsoft Corporation (Verenigde Staten)", html)                 # bij de partijen en de doorgifte
        self.assertIn(pv.LABELS["clarity"], pv.open_points())

    def test_live_start_niet_met_clarity_zolang_de_tekst_open_staat(self):
        with override_settings(TEST_MODE=False):
            fouten = pv.check_privacy_statement()
        self.assertTrue(fouten)
        self.assertIn(pv.LABELS["clarity"], fouten[0].msg)

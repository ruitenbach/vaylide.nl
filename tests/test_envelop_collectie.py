"""VAYLIDE Envelope Collection: de envelop-engine (catalog/envelop_collectie.py) en de ontwerpstudio (alleen lokaal)."""
import re

from django.test import SimpleTestCase, TestCase, override_settings

from catalog import envelop_collectie


class EnvelopConfigTests(SimpleTestCase):
    def test_elke_stijl_verwijst_naar_een_bestaand_zegel(self):
        for code, s in envelop_collectie.STIJLEN.items():
            self.assertIn(s["zegel"], envelop_collectie.ZEGELS, code)
            self.assertIn(s["lijn"], ("trouw", "kerst"), code)
            self.assertIn(s["flap"]["soort"], ("blind", "print"), code)

    def test_onbekende_stijl_en_zegel_geven_de_standaard(self):
        env = envelop_collectie.envelop("x", "bestaat-niet", "ook-niet")
        self.assertEqual(env["stijl"], envelop_collectie.STANDAARD)
        self.assertEqual(env["zegel_code"], envelop_collectie.STIJLEN[envelop_collectie.STANDAARD]["zegel"])

    def test_zegel_los_te_kiezen_en_monogram_kort(self):
        env = envelop_collectie.envelop("x", "signature", "evergreen", monogram="ABCDEFG")
        self.assertEqual(env["zegel_code"], "evergreen")
        self.assertIn("--vx-wax:", env["zegel_stijl"])
        self.assertEqual(env["teken"], "monogram")
        self.assertEqual(env["monogram"], "ABCD")


class MonogramOpmaakTests(SimpleTestCase):
    def test_met_ampersand_twee_grote_letters_en_een_klein_teken(self):
        self.assertEqual(envelop_collectie.monogram_opmaak("S&D"), {"links": "S", "rechts": "D", "maat": "a2"})
        self.assertEqual(envelop_collectie.monogram_opmaak("AB&CD")["maat"], "a3")

    def test_lettermaat_volgt_het_aantal_letters(self):
        maten = {tekst: envelop_collectie.monogram_opmaak(tekst)["maat"] for tekst in ("V", "AB", "FAM", "ABCD", "ABCDEF")}
        self.assertEqual(maten, {"V": "m1", "AB": "m2", "FAM": "m3", "ABCD": "m4", "ABCDEF": "m4"})

    def test_losse_of_lege_ampersand_blijft_gewone_tekst(self):
        self.assertEqual(envelop_collectie.monogram_opmaak("&D"), {"links": "D", "rechts": "", "maat": "m1"})
        self.assertEqual(envelop_collectie.monogram_opmaak("")["maat"], "m1")

    def test_envelop_geeft_de_opmaak_mee(self):
        env = envelop_collectie.envelop("x", "signature", monogram="S&D")
        self.assertEqual(env["mono"]["rechts"], "D")


class WasStructuurTests(SimpleTestCase):
    def test_elk_materiaal_heeft_geldige_waarden(self):
        for code, z in envelop_collectie.ZEGELS.items():
            was = envelop_collectie.was_structuur(z)
            self.assertTrue(0 <= float(was["korrel"]) <= 0.02, code)
            self.assertTrue(0 <= float(was["vlek"]) <= 0.4, code)
            self.assertAlmostEqual(float(was["vlek_offset"]), -float(was["vlek"]) / 2, places=6, msg=code)

    def test_lichte_materialen_hebben_zachtere_vlekken(self):
        standaard = float(envelop_collectie.was_structuur({})["vlek"])
        for code in ("sage-botanical", "noisette-gold"):
            self.assertLess(float(envelop_collectie.was_structuur(envelop_collectie.ZEGELS[code])["vlek"]), standaard, code)

    def test_envelop_geeft_de_waarden_per_zegel(self):
        env = envelop_collectie.envelop("x", "signature", "sage-botanical")
        self.assertEqual(env["was"]["vlek"], "0.15")


class EnvelopLabTests(TestCase):
    @override_settings(DEBUG=False)
    def test_niet_bereikbaar_op_de_live_site(self):
        self.assertEqual(self.client.get("/lab/enveloppen/").status_code, 404)

    @override_settings(DEBUG=True)
    def test_alle_stijlen_met_dezelfde_lagen(self):
        for code, s in envelop_collectie.STIJLEN.items():
            html = self.client.get(f"/lab/enveloppen/?stijl={code}").content.decode()
            self.assertIn(f'class="vx vx--{code} vx--{s["lijn"]}"', html)
            # Lagen van de engine: voering achter en in de flap, kaart, voorvakken, flap met twee kanten, zegel in twee helften.
            for laag in ("vx-liner--back", "vx-card__paper", "vx-pocket", "vx-flap__out", "vx-flap__in", 'class="vx-liner"',
                         "vx-sealpart--top", "vx-sealpart--base", "vx-seal-crack", "vx-flapcast", 'class="vx-relief'):
                self.assertIn(laag, html, f"{code}: {laag}")
            self.assertIn(f"img/envelop/{s['voering']}", html)
            self.assertIn('aria-label="Verbreek het zegel en open de envelop"', html)
            self.assertIn("noindex", html)
            self.assertNotIn("<style", html)
            self.assertNotIn("#}", html)  # meerregelig {# #}-commentaar zou als tekst op de envelop verschijnen
            # Getallen in SVG-attributen nooit met een komma (Nederlandse notatie van Django is geen geldige SVG).
            self.assertIsNone(re.search(r'\s(?:cx|cy|rx|ry|x|y|width|height)="-?\d+,\d', html), code)
            if s["flap"]["soort"] == "print":
                self.assertIn('class="vx-deco"', html)

    @override_settings(DEBUG=True)
    def test_logo_v_en_initialen(self):
        html = self.client.get("/lab/enveloppen/?stijl=signature").content.decode()
        self.assertIn("img/merk/vaylide-v.png", html)
        html = self.client.get("/lab/enveloppen/?stijl=xx&monogram=<b>X</b>").content.decode()
        self.assertIn('class="vx vx--signature vx--trouw"', html)
        self.assertNotIn("<b>", html)
        self.assertIn("vx-seal__mono", html)

    @override_settings(DEBUG=True)
    def test_wasoppervlak_zonder_grove_hoogteruis(self):
        # Grove ruis in de 8 bits hoogtekaart gaf hoogtelijnen en compressievlekken; nu fijne korrel + zachte lichtvlekken.
        html = self.client.get("/lab/enveloppen/?stijl=midnight-emeraude").content.decode()
        self.assertNotIn('baseFrequency=".18"', html)
        self.assertIn('baseFrequency=".85"', html)  # fijne korrel in de hoogte
        self.assertIn('result="dm"', html)  # lichtvlekken in de belichting
        self.assertIsNone(re.search(r'k[34]="-?\d+,\d', html))  # geen komma als decimaalteken in de filterwaarden


class SignatureIvoryGsapTests(TestCase):
    """Signature Ivory heeft een eigen, lichte GSAP-opening (static/js/envelop-signature.js); de andere stijlen blijven op de klassieke engine."""

    def lab(self, stijl):
        with override_settings(DEBUG=True):
            return self.client.get(f"/lab/enveloppen/?stijl={stijl}").content.decode()

    def test_alleen_signature_laadt_gsap_en_in_de_goede_volgorde(self):
        html = self.lab("signature")
        gsap, eigen, klassiek = (html.index(x) for x in ("vendor/gsap/gsap.min.js", "js/envelop-signature.js", "js/envelop-collectie.js"))
        self.assertLess(gsap, eigen)
        self.assertLess(eigen, klassiek, "het GSAP-script moet vóór de klassieke engine draaien om de envelop over te nemen")
        for stijl in ("royal-evergreen", "rose-blush", "golden-noel", "midnight-emeraude"):
            self.assertNotIn("gsap", self.lab(stijl), stijl)

    def test_eigen_botanisch_reliefbeeld_met_hoogteverschillen(self):
        html = self.lab("signature")
        self.assertEqual(envelop_collectie.STIJLEN["signature"]["flap"]["fragment"], "partials/envelop/_flap_signature.svg")
        for klasse in ("vx-h1", "vx-h2", "vx-h3", "vx-lo"):
            self.assertIn(klasse, html)
        # zachter en dieper licht voor Signature; alle andere stijlen houden de standaard
        self.assertIn('stdDeviation="2.3"', html)
        self.assertIn('surfaceScale="3.2"', html)
        andere = self.lab("rose-blush")
        self.assertIn('stdDeviation="2.1"', andere)
        self.assertIn('surfaceScale="3"', andere)
        self.assertNotIn("vx-h1", andere)

    def test_script_neemt_over_en_ruimt_op(self):
        from django.conf import settings
        js = (settings.BASE_DIR / "static" / "js" / "envelop-signature.js").read_text(encoding="utf-8")
        for onderdeel in ("data-vx-gsap", "vx:opened", "vxReset", "fx-paused", "prefers-reduced-motion", "vx:opwarmen-klaar", "IntersectionObserver", "gsap.timeline"):
            self.assertIn(onderdeel, js)
        klassiek = (settings.BASE_DIR / "static" / "js" / "envelop-collectie.js").read_text(encoding="utf-8")
        self.assertGreaterEqual(klassiek.count("data-vx-gsap"), 2)   # laat een envelop met GSAP met rust, ook via een knop buiten de envelop
        css = (settings.BASE_DIR / "static" / "css" / "envelop-collectie.css").read_text(encoding="utf-8")
        self.assertIn(".vx[data-vx-gsap]", css)
        self.assertRegex(css, r"\.vx\[data-vx-gsap\], \.vx\[data-vx-gsap\] \* \{ transition: none !important; \}")

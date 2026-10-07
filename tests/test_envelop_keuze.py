"""De Envelope Collection als keuze in de Studio: een envelop en een zegel als losse presentatielaag om een ontwerp (stap Envelop & zegel)."""
import copy

from django.contrib.staticfiles import finders
from django.test import Client, SimpleTestCase

from catalog import envelop_collectie as ec
from catalog.models import Template
from invitations.content import default_content, normalize_content
from invitations.services import save_draft

from .helpers import VaylideTestCase


class _Ontwerp:
    def __init__(self, slug, manifest=None):
        self.manifest = manifest or {}
        self.template = type("T", (), {"slug": slug})()


class RegistryTests(SimpleTestCase):
    def test_modus_manifest_wint_dan_de_tabel_dan_built_in(self):
        self.assertEqual(ec.modus(_Ontwerp("puur-moment")), "optional")
        self.assertEqual(ec.modus(_Ontwerp("puur-moment", {"envelope_mode": "none"})), "none")
        self.assertEqual(ec.modus(_Ontwerp("nieuw-ontwerp", {"envelope_mode": "optional"})), "optional")
        self.assertEqual(ec.modus(_Ontwerp("ballonfeest")), "built_in")          # elk ander ontwerp: de eigen opening blijft
        self.assertEqual(ec.modus(_Ontwerp("puur-moment", {"envelope_mode": "onzin"})), "optional")   # onbekende waarde: terug naar de tabel

    def test_enveloppen_per_gelegenheid_alleen_uitgewerkte(self):
        self.assertEqual(list(ec.beschikbaar("bruiloft")), ["signature", "rose-blush", "midnight-emeraude"])
        self.assertEqual(list(ec.beschikbaar("kerst")), ["royal-evergreen", "golden-noel"])
        for gelegenheid in ("bruiloft", "kerst", "verjaardag", "zakelijk"):
            self.assertNotIn("sage", ec.beschikbaar(gelegenheid))
            self.assertNotIn("noisette", ec.beschikbaar(gelegenheid))

    def test_zegels_en_voorbeeldbeelden_bestaan(self):
        for code in ec.STIJLEN:
            if not ec.STIJLEN[code]["klaar"]:
                continue
            zegels = ec.zegels_voor(code)
            self.assertEqual(zegels[0], ec.standaard_zegel(code))
            self.assertTrue(set(zegels) <= set(ec.ZEGELS), code)
            self.assertTrue(finders.find(f"img/envelop/voorbeeld/{code}.webp"), f"voorbeeld van {code}")
            self.assertIn(ec.KEUZE[code]["beweging"], ("gsap", "klassiek"))
        for code in ec.ZEGELS:
            self.assertTrue(finders.find(f"img/envelop/zegel/{code}.webp"), f"zegel {code}")

    def test_leeg_of_onbekend_geeft_het_gedrag_van_vroeger(self):
        ontwerp = _Ontwerp("puur-moment")
        zonder = {"style": {"envelop": {}}}
        self.assertIsNone(ec.gekozen(zonder, "bruiloft", ontwerp))
        self.assertIsNone(ec.gekozen({"style": {"envelop": {"collectie": {"envelop": "bestaat-niet"}}}}, "bruiloft", ontwerp))
        self.assertIsNone(ec.gekozen({"style": {"envelop": {"collectie": {"envelop": "royal-evergreen"}}}}, "bruiloft", ontwerp), "past niet bij de gelegenheid")
        self.assertIsNone(ec.gekozen({"style": {"envelop": {"collectie": {"envelop": "signature"}}}}, "bruiloft", _Ontwerp("midnight-emeraude", {"envelope_mode": "built_in"})))
        self.assertFalse(ec.geen_envelop(zonder, ontwerp))
        self.assertTrue(ec.geen_envelop({"style": {"envelop": {"collectie": {"envelop": "geen"}}}}, ontwerp))
        self.assertFalse(ec.geen_envelop({"style": {"envelop": {"collectie": {"envelop": "geen"}}}}, _Ontwerp("ballonfeest")))

    def test_onpassend_zegel_wordt_het_standaardzegel_en_initialen(self):
        keuze = {"style": {"envelop": {"collectie": {"envelop": "signature", "zegel": "evergreen", "teken": "initialen", "initialen": "SD"}}}}
        gekozen = ec.gekozen(keuze, "bruiloft", _Ontwerp("puur-moment"))
        self.assertEqual((gekozen["stijl"], gekozen["zegel"], gekozen["beweging"], gekozen["monogram"]), ("signature", "champagne-monogram", "gsap", "SD"))

    def test_schema_bewaart_de_keuze_en_oude_inhoud_heeft_hem_leeg(self):
        self.assertEqual(default_content("bruiloft")["style"]["envelop"]["collectie"], {"envelop": "", "zegel": "", "teken": "standaard", "initialen": ""})
        oud = default_content("bruiloft")
        oud["style"]["envelop"].pop("collectie")
        self.assertEqual(normalize_content(oud, "bruiloft")["style"]["envelop"]["collectie"]["envelop"], "")
        nieuw = default_content("bruiloft")
        nieuw["style"]["envelop"]["collectie"] = {"envelop": "rose-blush", "zegel": "rose-floral", "teken": "standaard", "initialen": ""}
        self.assertEqual(normalize_content(nieuw, "bruiloft")["style"]["envelop"]["collectie"]["envelop"], "rose-blush")


class StudioEnvelopTests(VaylideTestCase):
    OPTIONEEL = "puur-moment"        # envelope_mode optional (catalog/envelop_collectie.py)
    INGEBOUWD = "midnight-emeraude"  # eigen opening, geen generieke envelop

    def setUp(self):
        self.customer = self.make_customer()
        self.client = Client()
        self.client.force_login(self.customer)

    def draft(self, template=None):
        return self.make_invitation(owner=self.customer, template=template or self.OPTIONEEL)

    def post_envelop(self, inv, **data):
        inv.refresh_from_db()
        payload = {"rev": inv.draft_rev, "actie": "opslaan", "envelop": "", "teken": "standaard"}
        payload.update(data)
        return self.client.post(f"/maken/{inv.uid}/envelop/", payload)

    def keuze(self, inv):
        inv.refresh_from_db()
        return ec.keuze_van(inv.draft_content)

    def test_start_gaat_na_elk_ontwerp_direct_naar_de_gegevens_en_de_envelop_is_een_onderdeel(self):
        for slug in (self.OPTIONEEL, "ballonfeest", self.INGEBOUWD):
            template = Template.objects.get(slug=slug)
            occasion = "bruiloft" if template.supports("bruiloft") else template.occasions[0]
            reactie = self.client.post("/maken/", {"occasion": occasion, "template": slug})
            self.assertEqual(reactie.status_code, 302, slug)
            self.assertTrue(reactie.url.endswith("/gegevens/"), (slug, reactie.url))
            pagina = self.client.get(reactie.url).content.decode()
            self.assertEqual("/envelop/" in pagina, slug == self.OPTIONEEL, slug)     # Envelop & zegel staat alleen in de balk bij een optioneel ontwerp

    def test_stap_toont_echte_voorbeelden_en_alleen_passende_zegels(self):
        inv = self.draft()
        pagina = self.client.get(f"/maken/{inv.uid}/envelop/")
        self.assertContains(pagina, "Envelop &amp; zegel")
        for naam in ("VAYLIDE Signature Ivory", "Rose Blush", "Midnight Émeraude", "Geen envelop", "Opening van het ontwerp"):
            self.assertContains(pagina, naam)
        self.assertNotContains(pagina, "Golden Noël")        # kerst
        for code in ("signature", "rose-blush", "midnight-emeraude"):
            self.assertContains(pagina, f"img/envelop/voorbeeld/{code}.webp")
        self.assertContains(pagina, "data-envelop-kiezer")
        self.assertContains(pagina, f'data-live-update="/maken/{inv.uid}/voorbeeld/live/envelop/"')
        html = pagina.content.decode()
        self.assertRegex(html, r'name="envelop" value="" checked')
        self.assertRegex(html, r'id="zegel" data-zegel-blok hidden')     # niets gekozen: het zegelblok is dicht

    def test_stap_staat_in_de_voortgang_alleen_bij_optionele_ontwerpen(self):
        optioneel = self.client.get(f"/maken/{self.draft().uid}/gegevens/").content.decode()
        self.assertIn("Envelop &amp; zegel", optioneel)
        ingebouwd = self.client.get(f"/maken/{self.draft(self.INGEBOUWD).uid}/gegevens/").content.decode()
        self.assertNotIn("Envelop &amp; zegel", ingebouwd)

    def test_ingebouwd_ontwerp_slaat_de_stap_over(self):
        inv = self.draft(self.INGEBOUWD)
        reactie = self.client.get(f"/maken/{inv.uid}/envelop/")
        self.assertEqual(reactie.status_code, 302)
        self.assertTrue(reactie.url.endswith("/stijl/"))      # de eerstvolgende stap na het (overgeslagen) onderdeel

    def test_kiezen_wisselen_en_niets_kwijt(self):
        inv = self.draft()
        namen = copy.deepcopy(inv.draft_content["names"])
        self.assertEqual(self.post_envelop(inv, envelop="signature", zegel="noisette-gold").status_code, 302)
        self.assertEqual(self.keuze(inv), {"envelop": "signature", "zegel": "noisette-gold", "teken": "standaard", "initialen": ""})
        # wisselen van envelop: een niet passend zegel wordt het standaardzegel van die envelop
        self.post_envelop(inv, envelop="midnight-emeraude", zegel="sage-botanical")
        self.assertEqual(self.keuze(inv)["envelop"], "midnight-emeraude")
        self.assertEqual(self.keuze(inv)["zegel"], "champagne-monogram")
        # wisselen van zegel
        self.post_envelop(inv, envelop="midnight-emeraude", zegel="noisette-gold")
        self.assertEqual(self.keuze(inv)["zegel"], "noisette-gold")
        # geen envelop, en terug naar de opening van het ontwerp
        self.post_envelop(inv, envelop="geen")
        self.assertEqual(self.keuze(inv)["envelop"], "geen")
        self.assertEqual(self.keuze(inv)["zegel"], "")
        self.post_envelop(inv, envelop="")
        self.assertEqual(self.keuze(inv)["envelop"], "")
        inv.refresh_from_db()
        self.assertTrue(inv.draft_content["style"]["opening"])
        self.assertEqual(inv.draft_content["names"], namen)          # de gegevens van de klant blijven
        # een envelop van een andere gelegenheid of een onbekende wordt niet bewaard
        self.assertEqual(self.post_envelop(inv, envelop="golden-noel").status_code, 200)
        self.assertEqual(self.post_envelop(inv, envelop="bestaat-niet").status_code, 200)
        self.assertEqual(self.keuze(inv)["envelop"], "")

    def test_initialen_en_andere_stijlkeuzes_blijven(self):
        inv = self.draft()
        content = dict(inv.draft_content)
        content["style"] = dict(content["style"])
        content["style"]["envelop"] = dict(content["style"]["envelop"], kleur="salie", zegel_kleur="goud")
        save_draft(inv, expected_rev=None, content=content, user=self.customer)
        self.post_envelop(inv, envelop="signature", zegel="champagne-monogram", teken="initialen", initialen="S&D<b>")
        inv.refresh_from_db()
        keuze = inv.draft_content["style"]["envelop"]
        self.assertEqual((keuze["kleur"], keuze["zegel_kleur"]), ("salie", "goud"))
        self.assertEqual(keuze["collectie"]["initialen"], "S&Db")
        self.assertEqual(keuze["collectie"]["teken"], "initialen")

    def test_stijlstap_toont_de_openingsschakelaar_niet_meer_en_laat_de_keuze_ongemoeid(self):
        inv = self.draft()
        pagina = self.client.get(f"/maken/{inv.uid}/stijl/").content.decode()
        self.assertNotIn('name="opening"', pagina)
        self.assertIn("Envelop &amp; zegel", pagina)
        self.post_envelop(inv, envelop="geen")
        inv.refresh_from_db()
        self.client.post(f"/maken/{inv.uid}/stijl/", {"rev": inv.draft_rev, "actie": "opslaan", "palette": inv.template_version.default_palette_key})
        self.assertEqual(self.keuze(inv)["envelop"], "geen")
        # een ontwerp zonder de keuze houdt zijn eigen schakelaar
        ander = self.make_invitation(owner=self.customer, template="ballonfeest", occasion="verjaardag")
        self.assertIn('name="opening"', self.client.get(f"/maken/{ander.uid}/stijl/").content.decode())

    def test_live_voorbeeld_wisselt_zonder_opslaan_en_toont_de_dichte_envelop(self):
        inv = self.draft()
        reactie = self.client.post(f"/maken/{inv.uid}/voorbeeld/live/envelop/", {"envelop": "signature", "zegel": "noisette-gold", "teken": "standaard"})
        self.assertTrue(reactie.json()["ok"])
        self.assertEqual(self.keuze(inv)["envelop"], "", "het live voorbeeld bewaart niets")
        html = self.client.get(reactie.json()["url"]).content.decode()
        self.assertIn('data-live="envelop"', html)
        self.assertIn("vx vx--signature", html)
        self.assertIn("--vx-wax: #D2B275", html)           # het gekozen zegel (Noisette Gold)
        andere = self.client.post(f"/maken/{inv.uid}/voorbeeld/live/envelop/", {"envelop": "rose-blush", "zegel": "rose-floral", "teken": "standaard"}).json()
        self.assertIn("vx--rose-blush", self.client.get(andere["url"]).content.decode())


class GastWeergaveTests(VaylideTestCase):
    def gast(self, template, collectie=None):
        owner = self.make_customer()
        if collectie is None:
            inv = self.make_invitation(owner=owner, template=template)
        else:
            inv = self.make_invitation(owner=owner, template=template, style={"envelop": {"collectie": collectie}})
        self.pay(inv, owner)
        inv.refresh_from_db()
        reactie = Client().get(f"/u/{inv.slug}/")
        self.assertEqual(reactie.status_code, 200)
        return reactie.content.decode()

    def test_zonder_keuze_blijft_alles_zoals_het_was(self):
        html = self.gast("puur-moment")
        self.assertIn("data-cover", html)
        self.assertNotRegex(html, r'class="[^"]*vxc')   # de klasse, niet toevallige letters in een slug
        self.assertNotIn("envelop-collectie", html)

    def test_gekozen_envelop_met_gsap_voor_signature(self):
        html = self.gast("puur-moment", {"envelop": "signature", "zegel": "noisette-gold", "teken": "standaard", "initialen": ""})
        self.assertIn("vxc vxc--licht", html)
        self.assertIn('data-duration="3900"', html)
        self.assertIn("vx vx--signature", html)
        self.assertIn('href="#uitnodiging" class="vx-seal-hit" data-vx-open data-open data-fx-origin', html)   # zonder JavaScript opent de kaart ook
        self.assertEqual(html.count("vendor/gsap/gsap.min.js"), 1, "GSAP maar een keer")
        self.assertLess(html.index("js/envelop-signature.js"), html.index("js/envelop-collectie.js"))
        self.assertIn("data-has-cover", html)
        self.assertIn('id="uitnodiging"', html)
        self.assertEqual(html.count("<script>"), 1)     # alleen het startscript met hash (CSP)
        self.assertNotIn("<style", html)

    def test_klassieke_envelop_zonder_gsap(self):
        html = self.gast("puur-moment", {"envelop": "midnight-emeraude", "zegel": "champagne-monogram", "teken": "standaard", "initialen": ""})
        self.assertIn("vxc vxc--donker", html)
        self.assertIn("vx vx--midnight-emeraude", html)
        self.assertIn('data-duration="4600"', html)
        self.assertNotIn("vendor/gsap", html)
        self.assertIn("js/envelop-collectie.js", html)

    def test_geen_envelop_is_direct_de_uitnodiging(self):
        html = self.gast("puur-moment", {"envelop": "geen", "zegel": "", "teken": "standaard", "initialen": ""})
        self.assertNotIn("data-cover", html)
        self.assertNotIn("data-has-cover", html)
        self.assertNotRegex(html, r'class="[^"]*vxc')   # de klasse, niet toevallige letters in een slug
        self.assertIn('id="uitnodiging"', html)

    def test_ingebouwd_ontwerp_krijgt_geen_tweede_envelop(self):
        html = self.gast("midnight-emeraude", {"envelop": "signature", "zegel": "noisette-gold", "teken": "standaard", "initialen": ""})
        self.assertNotRegex(html, r'class="[^"]*vxc')   # de klasse, niet toevallige letters in een slug
        self.assertIn("me-cover", html)
        self.assertEqual(html.count("vx vx--"), 1)

    def test_initialen_op_het_zegel(self):
        html = self.gast("puur-moment", {"envelop": "signature", "zegel": "champagne-monogram", "teken": "initialen", "initialen": "A&B"})
        self.assertIn("vx-seal__mono", html)
        # Met een & staat dat teken kleiner tussen twee grote letters (eigen tspan), nooit als ongeëscapete tekst.
        self.assertIn("<tspan>A</tspan><tspan class=\"vx-seal__amp\">&amp;</tspan><tspan>B</tspan>", html)
        self.assertIn("vx-seal__mono--a2", html)

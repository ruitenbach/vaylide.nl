"""Uitleg en eerlijke keuzes rond de envelop: de envelop is alleen de opening, een ontwerp met een eigen opening zegt dat, en de Studio toont
nooit een keuze (envelop- of zegelkleur, logo) die bij dat ontwerp niets verandert."""
import re
from pathlib import Path

from django.conf import settings
from django.test import Client, SimpleTestCase

from catalog import envelop
from catalog import envelop_collectie as ec

from .helpers import VaylideTestCase

DESIGNS = Path(settings.BASE_DIR) / "designs"


class _Ontwerp:
    def __init__(self, slug, manifest=None):
        self.manifest = manifest or {}
        self.template = type("T", (), {"slug": slug})()


class ZegelkeuzesTests(SimpleTestCase):
    def test_midnight_alleen_initialen(self):
        k = envelop.zegelkeuzes(_Ontwerp("midnight-emeraude", {"opening": "envelop"}))
        self.assertEqual((k["env_kleur"], k["zegel_kleur"], k["inhoud"], k["logo"], k["initialen"], k["vast"]), (False, False, False, False, True, True))

    def test_rose_royale_en_golden_noel_hebben_geen_werkende_zegelkeuzes(self):
        for slug in ("rose-royale", "golden-noel"):
            k = envelop.zegelkeuzes(_Ontwerp(slug, {"opening": "envelop"}))
            self.assertFalse(any(v for key, v in k.items() if key != "vast"), slug)

    def test_klassieke_envelop_houdt_alles(self):
        k = envelop.zegelkeuzes(_Ontwerp("balzaal", {"opening": "envelop"}))
        self.assertEqual((k["env_kleur"], k["zegel_kleur"], k["inhoud"], k["logo"], k["initialen"]), (True,) * 5)
        z = envelop.zegelkeuzes(_Ontwerp("eerste-dans", {"opening": "paleisdeuren"}))     # zegel, geen envelop
        self.assertEqual((z["env_kleur"], z["zegel_kleur"], z["initialen"]), (False, True, True))

    def test_ontwerp_zonder_zegel_heeft_niets(self):
        k = envelop.zegelkeuzes(_Ontwerp("ballonfeest", {"opening": "ballonnen"}))
        self.assertFalse(any(v for key, v in k.items() if key != "vast"))

    def test_elk_ontwerp_met_de_envelope_collection_staat_in_de_lijst(self):
        """Een nieuw ontwerp dat zelf {% vx_envelop %} gebruikt, moet hier beslissen welke oude keuzes er werken."""
        gebruikt = {p.parent.parent.name for p in DESIGNS.glob("*/v1/invitation.html") if "{% vx_envelop " in p.read_text(encoding="utf-8")}
        self.assertEqual(gebruikt, set(envelop.COLLECTIE_INGEBOUWD))
        for slug in gebruikt:
            self.assertEqual(ec.modus(_Ontwerp(slug, {"envelope_mode": "built_in"})), "built_in")


class UitlegEnKeuzesTests(VaylideTestCase):
    OPTIONEEL = "puur-moment"
    INGEBOUWD = "midnight-emeraude"

    def setUp(self):
        self.customer = self.make_customer()
        self.client = Client()
        self.client.force_login(self.customer)

    def draft(self, template, occasion=None):
        return self.make_invitation(owner=self.customer, template=template, **({"occasion": occasion} if occasion else {}))

    def get(self, inv, stap):
        return self.client.get(f"/maken/{inv.uid}/{stap}/").content.decode()

    # --- stap Envelop & zegel
    def test_uitleg_bovenaan_en_ondertitel_met_de_naam_van_het_ontwerp(self):
        html = self.get(self.draft(self.OPTIONEEL), "envelop")
        self.assertIn("Hoe openen je gasten de kaart?", html)
        self.assertIn("De eigen opening van Puur moment", html)
        self.assertNotIn("Doorschijnend vel", html)          # interne omschrijving uit het manifest
        self.assertIn("Gasten zien direct je uitnodiging.", html)

    def test_initialen_uitleg_gaat_alleen_over_het_zegel(self):
        html = self.get(self.draft(self.OPTIONEEL), "envelop")
        self.assertIn("Laat leeg om de initialen voor het zegel uit jullie namen te gebruiken.", html)
        self.assertNotIn("Leeg: we maken ze uit jullie namen", html)
        self.assertIn("Hoogstens 4 tekens", html)             # het zegel toont er 4
        self.assertRegex(html, r'name="initialen"[^>]*maxlength="4"')

    def test_initialen_worden_op_vier_tekens_bewaard(self):
        inv = self.draft(self.OPTIONEEL)
        self.client.post(f"/maken/{inv.uid}/envelop/", {"rev": inv.draft_rev, "actie": "opslaan", "envelop": "signature", "zegel": "champagne-monogram",
                                                       "teken": "initialen", "initialen": "ABCDE"})
        inv.refresh_from_db()
        self.assertEqual(ec.keuze_van(inv.draft_content)["initialen"], "ABCD")

    def test_enveloppen_die_als_ontwerp_bestaan_krijgen_envelop_achter_hun_naam(self):
        bruiloft = self.get(self.draft(self.OPTIONEEL), "envelop")
        self.assertIn("Midnight Émeraude envelop", bruiloft)
        self.assertIn("VAYLIDE Signature Ivory", bruiloft)
        self.assertNotIn("Signature Ivory envelop", bruiloft)
        self.assertNotIn("Rose Blush envelop", bruiloft)       # geen ontwerp met die naam
        kerst = self.get(self.make_invitation(owner=self.customer, template="aan-tafel", occasion="kerst"), "stijl")   # kerst: eigen opening, zie hieronder
        self.assertIn("Eigen opening", kerst)
        # de codes en stijlnamen blijven zoals ze zijn
        self.assertEqual(ec.STIJLEN["midnight-emeraude"]["naam"], "Midnight Émeraude")
        self.assertIn('value="midnight-emeraude"', bruiloft)

    # --- ontwerp met een eigen opening
    def test_ingebouwd_ontwerp_zegt_dat_het_een_eigen_opening_heeft(self):
        html = self.get(self.draft(self.INGEBOUWD), "stijl")
        self.assertIn("Eigen opening: ", html)
        self.assertIn("Smaragdgroene envelop met gouden zegel, met een filmische opening", html)
        self.assertNotIn("Envelope Collection", html)         # geen jargon
        self.assertNotIn("Envelop &amp; zegel</a>", self.get(self.draft(self.INGEBOUWD), "gegevens"))   # en geen onderdeel Envelop & zegel in de balk

    def test_optioneel_ontwerp_met_envelopstap_zegt_dat_niet(self):
        self.assertNotIn("Eigen opening", self.get(self.draft(self.OPTIONEEL), "stijl"))
        self.assertIn("Envelop &amp; zegel</a>", self.get(self.draft(self.OPTIONEEL), "gegevens"))   # het onderdeel staat wel in de balk

    def test_stijlstap_ingebouwd_toont_alleen_wat_werkt(self):
        html = self.get(self.draft(self.INGEBOUWD), "stijl")
        self.assertIn('name="initialen"', html)
        self.assertIn("Initialen op het zegel", html)
        self.assertIn("Alleen de initialen kies je zelf", html)
        for dood in ('name="env_kleur"', 'name="zegel_kleur"', 'name="zegel"', 'name="zegel_logo"', "Kleur van de envelop", "Kleur van het lakzegel", "Eigen logo"):
            self.assertNotIn(dood, html, dood)
        self.assertIn("Eigen opening", html)
        self.assertIn('name="opening"', html)                 # de schakelaar voor de opening werkt wel
        self.assertNotIn("(Envelope Collection)", html)

    def test_stijlstap_rose_royale_en_golden_noel_tonen_geen_zegelpaneel(self):
        for slug, occasion in (("rose-royale", "bruiloft"), ("golden-noel", "kerst")):
            html = self.get(self.draft(slug, occasion), "stijl")
            self.assertNotIn('id="envelop"', html, slug)
            self.assertNotIn('name="initialen"', html, slug)
            self.assertIn("Eigen opening", html, slug)

    def test_stijlstap_klassieke_envelop_houdt_alle_keuzes(self):
        html = self.get(self.draft("balzaal"), "stijl")
        for naam in ('name="env_kleur"', 'name="zegel_kleur"', 'name="zegel"', 'name="initialen"', 'name="zegel_logo"'):
            self.assertIn(naam, html, naam)
        self.assertIn("Hoogstens 5 tekens", html)             # de klassieke zegels tonen er 5

    def test_oude_kleurkeuzes_bij_ingebouwd_ontwerp_worden_niet_meer_aangepast(self):
        inv = self.draft(self.INGEBOUWD)
        inv.refresh_from_db()
        self.client.post(f"/maken/{inv.uid}/stijl/", {"rev": inv.draft_rev, "actie": "opslaan", "palette": inv.template_version.default_palette_key,
                                                      "opening": "on", "env_kleur": "ivoor", "zegel_kleur": "rood", "initialen": "S&D"})
        inv.refresh_from_db()
        keuze = inv.draft_content["style"]["envelop"]
        self.assertEqual((keuze["kleur"], keuze["zegel_kleur"], keuze["initialen"]), ("", "", "S&D"))

    def test_midnight_toont_de_initialen_uit_de_stijlstap_op_het_zegel(self):
        inv = self.draft(self.INGEBOUWD)
        inv.refresh_from_db()
        self.client.post(f"/maken/{inv.uid}/stijl/", {"rev": inv.draft_rev, "actie": "opslaan", "palette": inv.template_version.default_palette_key,
                                                      "opening": "on", "initialen": "XY"})
        html = self.client.get(f"/maken/{inv.uid}/voorbeeld/weergave/").content.decode()
        self.assertRegex(html, r'vx-seal__mono[^>]*>XY<')


class ZegelnamenEnAanpasLijstTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.client = Client()
        self.client.force_login(self.customer)

    def draft(self, template, occasion=None):
        return self.make_invitation(owner=self.customer, template=template, **({"occasion": occasion} if occasion else {}))

    def test_zegels_heten_voor_de_klant_naar_materiaal_en_teken(self):
        html = self.client.get(f"/maken/{self.draft('puur-moment').uid}/envelop/").content.decode()
        for naam, regel in (("Champagnegoud", "Met de V"), ("Saliegroen", "Met de V"), ("Warm goud", "Met de V"), ("Roségoud", "Met een roos")):
            self.assertIn(f"<strong>{naam}</strong><span class=\"small muted\">{regel}</span>", html, naam)
        for intern in ("Champagne Monogram", "Sage Botanical", "Noisette Gold", "Rose Floral"):
            self.assertNotIn(intern, html, intern)
        self.assertIn('value="champagne-monogram"', html)          # de codes blijven
        kerst = self.client.get(f"/maken/{self.draft('aan-tafel', 'kerst').uid}/gegevens/")
        self.assertEqual(kerst.status_code, 200)

    def test_dennengroen_zegel_bij_kerst(self):
        from studio.forms import ZEGEL_KEUZENAMEN

        self.assertEqual(ZEGEL_KEUZENAMEN["evergreen"], ("Dennengroen", "Met de V in een krans"))
        self.assertEqual(set(ZEGEL_KEUZENAMEN), set(ec.ZEGELS))     # elk zegel heeft een klantnaam

    def test_voorbeeld_en_mijn_vaylide_bieden_envelop_en_zegel_aan_bij_optional(self):
        inv = self.draft("puur-moment")
        voorbeeld = self.client.get(f"/maken/{inv.uid}/voorbeeld/").content.decode()
        self.assertIn(f'href="/maken/{inv.uid}/envelop/">Envelop &amp; zegel</a>', voorbeeld)
        mijn = self.client.get(f"/account/uitnodiging/{inv.uid}/").content.decode()
        self.assertIn(f'href="/maken/{inv.uid}/envelop/">Envelop en zegel</a>', mijn)

    def test_geen_misleidende_link_bij_built_in(self):
        for slug in ("midnight-emeraude", "ballonfeest"):
            inv = self.draft(slug, "verjaardag" if slug == "ballonfeest" else None)
            voorbeeld = self.client.get(f"/maken/{inv.uid}/voorbeeld/").content.decode()
            mijn = self.client.get(f"/account/uitnodiging/{inv.uid}/").content.decode()
            self.assertNotIn(f"/maken/{inv.uid}/envelop/", voorbeeld, slug)
            self.assertNotIn(f"/maken/{inv.uid}/envelop/", mijn, slug)

    def test_link_naar_envelopstap_toont_de_bewaarde_keuze(self):
        inv = self.draft("puur-moment")
        inv.refresh_from_db()
        self.client.post(f"/maken/{inv.uid}/envelop/", {"rev": inv.draft_rev, "actie": "opslaan", "envelop": "rose-blush", "zegel": "rose-floral",
                                                       "teken": "initialen", "initialen": "S&D"})
        html = self.client.get(f"/maken/{inv.uid}/envelop/").content.decode()
        self.assertRegex(html, r'name="envelop" value="rose-blush"[^>]*checked')
        self.assertRegex(html, r'name="initialen"[^>]*value="S&amp;D"')

"""De vereenvoudigde route: Kies kaart → Personaliseer → Controleer → Bestel. Een tik op een kaart bewaart de keuze en gaat direct door,
alle velden zijn optioneel, wisselen van onderdeel bewaart wat er staat en nieuwe ontwerpen staan vooraan."""
import re
from datetime import timedelta

from django.test import Client
from django.utils import timezone

from catalog.models import Template
from catalog.occasions import OCCASION_CHOICES, by_occasion
from invitations.models import Invitation
from invitations.services import create_draft, save_draft
from studio.steps import FASEN, PERSONALISEER, next_step, progress, substeps

from .helpers import VaylideTestCase, future_date


def kop_tekst(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


class KiesKaartTests(VaylideTestCase):
    def setUp(self):
        self.c = Client()

    def test_elke_kaart_is_een_verzendknop_en_een_tik_gaat_direct_naar_personaliseren(self):
        pagina = self.c.get("/maken/", {"gelegenheid": "verjaardag"}).content.decode()
        self.assertIn('name="template" value="confetti"', pagina)
        self.assertNotIn('name="pakket"', pagina)                     # geen pakketkeuze meer vóór het personaliseren
        self.assertNotIn('type="radio" name="template"', pagina)      # geen keuzerondjes met een aparte knop onderaan
        reactie = self.c.post("/maken/", {"occasion": "verjaardag", "template": "confetti"})
        self.assertEqual(reactie.status_code, 302)
        self.assertRegex(reactie.url, r"^/maken/[0-9a-f-]{36}/gegevens/$")
        inv = Invitation.objects.get()
        self.assertEqual(inv.template_version.template.slug, "confetti")
        self.assertEqual(inv.occasion, "verjaardag")

    def test_een_vooraf_gekozen_kaart_staat_vast_en_de_collectie_is_ingeklapt(self):
        pagina = self.c.get("/maken/", {"gelegenheid": "bruiloft", "ontwerp": "liefde-op-papier"}).content.decode()
        self.assertIn("Gekozen ontwerp", pagina)
        self.assertIn("Liefde op papier", pagina)
        self.assertIn("Verder met personaliseren", pagina)
        self.assertIn('<details class="kies-ander">', pagina)
        self.assertIn("<summary>Wijzigen</summary>", pagina)
        self.assertNotRegex(pagina, r'<details class="kies-ander" open')
        # De knop voor de gekozen kaart staat vóór de lijst met andere kaarten.
        self.assertLess(pagina.index('class="btn btn--primary btn--lg kaart-gekozen__cta"'), pagina.index('class="kaart-grid"'))

    def test_zonder_gelegenheid_staan_er_alleen_gelegenheden_en_geen_kaarten(self):
        pagina = self.c.get("/maken/").content.decode()
        for _key, label in OCCASION_CHOICES:
            self.assertIn(f">{label}</a>", pagina)
        self.assertNotIn('class="kaart-grid"', pagina)

    def test_een_ontwerp_dat_niet_bij_de_gelegenheid_past_wordt_niet_gekozen(self):
        reactie = self.c.post("/maken/", {"occasion": "kerst", "template": "eucalyptus"})
        self.assertEqual(reactie.status_code, 200)
        self.assertFalse(Invitation.objects.exists())

    def test_ander_ontwerp_kiezen_bewaart_de_invoer_en_gaat_terug_naar_waar_je_was(self):
        # (anoniem: de sessie van deze client kent het concept)
        self.c.post("/maken/", {"occasion": "bruiloft", "template": "liefde-op-papier"})
        mijn = Invitation.objects.latest("created_at")
        mijn = save_draft(mijn, expected_rev=None, content={**mijn.draft_content, "names": {"partner_1": "Sanne", "partner_2": ""}, "venue_name": "De Oranjerie"}, user=None)
        pagina = self.c.get(f"/maken/{mijn.uid}/ontwerp/?terug=programma").content.decode()
        self.assertIn('name="terug" value="programma"', pagina)
        self.assertIn('aria-current="true"', pagina)                                   # het huidige ontwerp is aangegeven
        reactie = self.c.post(f"/maken/{mijn.uid}/ontwerp/", {"rev": mijn.draft_rev, "occasion": "bruiloft", "template": "eucalyptus", "terug": "programma"})
        self.assertEqual(reactie.status_code, 302)
        self.assertTrue(reactie.url.endswith("/programma/"), reactie.url)
        mijn.refresh_from_db()
        self.assertEqual(mijn.template_version.template.slug, "eucalyptus")
        self.assertEqual(mijn.draft_content["names"]["partner_1"], "Sanne")
        self.assertEqual(mijn.draft_content["venue_name"], "De Oranjerie")
        onbekend = self.c.post(f"/maken/{mijn.uid}/ontwerp/", {"rev": mijn.draft_rev, "occasion": "bruiloft", "template": "liefde-op-papier", "terug": "bestellen"})
        self.assertTrue(onbekend.url.endswith("/gegevens/"), onbekend.url)             # een ongeldige terugweg valt terug op de gegevens


class VoortgangTests(VaylideTestCase):
    def test_vier_fasen_met_de_juiste_stand(self):
        self.assertEqual([f[1] for f in FASEN], ["Kies kaart", "Personaliseer", "Controleer", "Bestel"])
        stand = {s: [p["state"] for p in progress(s)] for s in ("ontwerp", "gegevens", "stijl", "voorbeeld", "bestellen")}
        self.assertEqual(stand["ontwerp"], ["current", "todo", "todo", "todo"])
        self.assertEqual(stand["gegevens"], ["done", "current", "todo", "todo"])
        self.assertEqual(stand["stijl"], ["done", "current", "todo", "todo"])      # alle onderdelen horen bij fase 2
        self.assertEqual(stand["voorbeeld"], ["done", "done", "current", "todo"])
        self.assertEqual(stand["bestellen"], ["done", "done", "done", "current"])
        self.assertEqual([p["label"] for p in progress("voorbeeld", paid=True)], ["Kies kaart", "Personaliseer", "Controleer"])

    def test_praktische_info_is_een_enkel_onderdeel(self):
        labels = [s["label"] for s in substeps("gegevens")]
        self.assertEqual(labels, ["Gegevens", "Praktische info", "Aanmelden", "Foto's & verhaal", "Envelop & zegel", "Stijl"])
        self.assertEqual(substeps("voorbeeld"), [])                                   # buiten fase 2 geen balk
        self.assertEqual(next_step("ontwerp"), "gegevens")
        self.assertEqual(next_step("stijl"), "voorbeeld")

    def test_nergens_in_de_studio_staat_praktische_informatie_dubbel(self):
        owner = self.make_customer()
        inv = self.make_invitation(owner=owner)
        c = Client()
        c.force_login(owner)
        for stap in PERSONALISEER + ["voorbeeld"]:
            pagina = c.get(f"/maken/{inv.uid}/{stap}/")
            if pagina.status_code != 200:
                continue
            tekst = kop_tekst(pagina.content.decode())
            self.assertNotIn("Praktische informatie", tekst, stap)
            self.assertLessEqual(tekst.count("Praktische info"), 3, stap)               # de balk, de kop en hoogstens een verwijzing


class WisselenEnDoorgaanTests(VaylideTestCase):
    def setUp(self):
        self.owner = self.make_customer()
        self.inv = create_draft(occasion="verjaardag", template=Template.objects.get(slug="confetti"), owner=self.owner)
        self.c = Client()
        self.c.force_login(self.owner)

    def post(self, stap, **data):
        self.inv.refresh_from_db()
        return self.c.post(f"/maken/{self.inv.uid}/{stap}/", {"rev": self.inv.draft_rev, "timezone": "Europe/Amsterdam", **data})

    def test_wisselen_van_onderdeel_bewaart_eerst_wat_er_staat(self):
        reactie = self.post("gegevens", actie="ga", naar="aanmelden", name_person_name="Lotte", venue_name="Het Park")
        self.assertEqual(reactie.status_code, 302)
        self.assertTrue(reactie.url.endswith("/aanmelden/"), reactie.url)
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["names"]["person_name"], "Lotte")
        self.assertEqual(self.inv.draft_content["venue_name"], "Het Park")
        # Terug naar Gegevens: de invoer staat er nog.
        pagina = self.c.get(f"/maken/{self.inv.uid}/gegevens/").content.decode()
        self.assertIn('value="Lotte"', pagina)
        self.assertIn('value="Het Park"', pagina)

    def test_wisselen_naar_een_onbekend_of_overgeslagen_onderdeel_blijft_op_de_pagina(self):
        for naar in ("bestaat-niet", "gelegenheid", "gegevens"):
            reactie = self.post("gegevens", actie="ga", naar=naar, name_person_name="Lotte")
            self.assertEqual(reactie.status_code, 302, naar)
            self.assertTrue(reactie.url.endswith("/gegevens/"), (naar, reactie.url))
        wens = create_draft(occasion="verjaardag", template=Template.objects.get(slug="confetti"), owner=self.owner, soort="wenskaart")
        reactie = self.c.post(f"/maken/{wens.uid}/gegevens/", {"rev": wens.draft_rev, "actie": "ga", "naar": "aanmelden", "timezone": "Europe/Amsterdam"})
        self.assertTrue(reactie.url.endswith("/gegevens/"), reactie.url)               # een wenskaart heeft geen Aanmelden

    def test_wisselen_met_een_fout_veld_bewaart_niets_en_toont_de_fout(self):
        reactie = self.post("gegevens", actie="ga", naar="aanmelden", date="31-02-2027")
        self.assertEqual(reactie.status_code, 200)
        self.assertContains(reactie, "Vul een geldige datum in.")

    def test_bekijk_mijn_kaart_en_verder_naar_controle(self):
        self.assertTrue(self.post("gegevens", actie="controle").url.endswith("/voorbeeld/"))
        self.assertTrue(self.post("stijl", actie="volgende", palette=self.inv.template_version.default_palette_key).url.endswith("/voorbeeld/"))
        pagina = self.c.get(f"/maken/{self.inv.uid}/gegevens/").content.decode()
        self.assertIn("Bekijk mijn kaart", pagina)
        self.assertIn("Volgende: Praktische info", pagina)
        stijl = self.c.get(f"/maken/{self.inv.uid}/stijl/").content.decode()
        self.assertIn("Verder naar controle", stijl)
        self.assertNotIn("Bekijk mijn kaart", stijl)

    def test_alle_velden_leeg_door_alle_onderdelen_heen(self):
        stap = "gegevens"
        gezien = []
        while stap != "voorbeeld" and len(gezien) < 10:
            gezien.append(stap)
            reactie = self.post(stap, actie="volgende", palette=self.inv.template_version.default_palette_key)
            self.assertEqual(reactie.status_code, 302, stap)
            stap = reactie.url.rstrip("/").split("/")[-1]
        self.assertEqual(stap, "voorbeeld")
        self.assertEqual(gezien[0], "gegevens")
        self.assertIn("aanmelden", gezien)

    def test_programma_dresscode_en_contact_staan_aan_zodra_ze_zijn_ingevuld(self):
        content = dict(self.inv.draft_content)
        content["sections"] = {**content["sections"], "program": False, "dresscode": False, "practical": False, "contact": False, "closing": False}
        save_draft(self.inv, expected_rev=None, content=content, user=self.owner)
        self.post("programma", actie="opslaan", p0_title="Taart", p0_time="15:00", dresscode_text="Feestelijk", k0_title="Parkeren", k0_text="Voor de deur",
                  contact_name="Sanne", closing_text="Tot dan!")
        self.inv.refresh_from_db()
        for sleutel in ("program", "dresscode", "practical", "contact", "closing"):
            self.assertTrue(self.inv.draft_content["sections"][sleutel], sleutel)
        stijl = self.c.get(f"/maken/{self.inv.uid}/stijl/").content.decode()
        for sleutel in ("program", "dresscode", "practical", "contact", "closing"):
            self.assertNotIn(f'name="s_{sleutel}"', stijl, sleutel)                    # geen tweede plek om hetzelfde te kiezen

    def test_stijl_bewaart_de_extras_en_laat_de_inhoud_met_rust(self):
        self.post("programma", actie="opslaan", p0_title="Taart", p0_time="15:00")
        self.post("stijl", actie="opslaan", palette=self.inv.template_version.default_palette_key, s_countdown="on")
        self.inv.refresh_from_db()
        self.assertTrue(self.inv.draft_content["sections"]["program"])
        self.assertTrue(self.inv.draft_content["sections"]["countdown"])
        self.assertEqual(self.inv.draft_content["program"][0]["title"], "Taart")


class LegeKaartTests(VaylideTestCase):
    def test_elk_ontwerp_toont_een_lege_kaart_netjes(self):
        """Zonder namen, datum, plaats en programma: geen fout, geen 'None' en geen lege kop op de kaart."""
        owner = self.make_customer()
        c = Client()
        c.force_login(owner)
        problemen = []
        for template in Template.objects.filter(is_active=True, current_version__isnull=False):
            occasion = template.occasions[0]
            inv = create_draft(occasion=occasion, template=template, owner=owner)
            reactie = c.get(f"/maken/{inv.uid}/voorbeeld/weergave/")
            if reactie.status_code != 200:
                problemen.append((template.slug, reactie.status_code))
                continue
            html = reactie.content.decode()
            if re.search(r"<h[1-6][^>]*>\s*</h[1-6]>", html) or re.search(r">\s*(None|undefined|null)\s*<", html):
                problemen.append((template.slug, "lege kop of tekstrest"))
        self.assertEqual(problemen, [])


    def test_zonder_naam_leest_de_regel_onder_de_namen_nog_als_een_zin(self):
        owner = self.make_customer()
        c = Client()
        c.force_login(owner)
        for occasion, slug, fout, goed in (
            ("bruiloft", "liefde-op-papier", "Bruiloft nodigen je", "Je bent van harte uitgenodigd"),
            ("verjaardag", "confetti", "Verjaardag nodigt je", "Je bent uitgenodigd voor een feestje"),
            ("babyshower", "maanlicht", "Babyshower nodigt je", "Je bent uitgenodigd voor een babyshower"),
        ):
            inv = create_draft(occasion=occasion, template=Template.objects.get(slug=slug), owner=owner)
            html = kop_tekst(c.get(f"/maken/{inv.uid}/voorbeeld/weergave/").content.decode())
            self.assertIn(goed, html, occasion)
            self.assertNotIn(fout, html, occasion)
        # Met een naam blijft de bekende zin staan.
        inv = create_draft(occasion="verjaardag", template=Template.objects.get(slug="confetti"), owner=owner)
        content = {**inv.draft_content, "names": {"person_name": "Lotte", "age": ""}}
        save_draft(inv, expected_rev=None, content=content, user=owner)
        html = kop_tekst(c.get(f"/maken/{inv.uid}/voorbeeld/weergave/").content.decode())
        self.assertIn("Lotte", html)
        self.assertNotIn("Je bent uitgenodigd voor een feestje", html)


class NieuwsteOntwerpenEerstTests(VaylideTestCase):
    def maak(self, slug, dagen_geleden):
        t = Template.objects.get(slug=slug)
        Template.objects.filter(pk=t.pk).update(created_at=timezone.now() - timedelta(days=dagen_geleden))
        return Template.objects.get(slug=slug)

    def test_een_nieuw_ontwerp_staat_vooraan_binnen_de_gelegenheid(self):
        oud = self.maak("liefde-op-papier", 400)
        nieuw = self.maak("eucalyptus", 1)
        midden = self.maak("avondgoud", 40)
        volgorde = [t.slug for t in by_occasion([oud, nieuw, midden], "bruiloft")]
        self.assertEqual(volgorde, ["eucalyptus", "avondgoud", "liefde-op-papier"])
        self.assertEqual([t.slug for t in by_occasion([oud, nieuw, midden], "")], ["eucalyptus", "avondgoud", "liefde-op-papier"])

    def test_zelfde_dag_valt_terug_op_de_vaste_volgorde(self):
        a = self.maak("avondgoud", 5)
        b = self.maak("puur-moment", 5)
        verwacht = sorted([a, b], key=lambda t: (t.sort_order, t.name))
        self.assertEqual(by_occasion([b, a], "bruiloft"), verwacht)

    def test_voor_de_gelegenheid_gemaakte_ontwerpen_gaan_voor_op_nieuwere_van_een_andere_gelegenheid(self):
        eigen = self.maak("eucalyptus", 300)             # gemaakt voor bruiloft
        vreemd = self.maak("confetti", 1)                # eerst voor verjaardag, wel nieuw
        vreemd_bruiloft = Template.objects.get(pk=vreemd.pk)
        volgorde = by_occasion([vreemd_bruiloft, eigen], "bruiloft")
        self.assertEqual(volgorde[0].slug, "eucalyptus")

    def test_de_collectiepagina_en_de_startpagina_tonen_het_nieuwste_eerst_en_alleen_actieve_ontwerpen(self):
        Template.objects.update(created_at=timezone.now() - timedelta(days=100))
        self.maak("liefde-op-papier", 500)
        nieuw = self.maak("avondgoud", 0)
        Template.objects.filter(slug="puur-moment").update(created_at=timezone.now() + timedelta(days=1), is_active=False)   # nieuwer, maar niet gepubliceerd
        c = Client()
        for adres in ("/ontwerpen/?gelegenheid=bruiloft", "/maken/?gelegenheid=bruiloft"):
            html = c.get(adres).content.decode()
            self.assertNotIn("puur-moment", html, adres)
            kaarten = re.findall(r'/(?:ontwerpen|voorbeeld)/([a-z0-9-]+)/', html) if "ontwerpen" in adres else re.findall(r'name="template" value="([a-z0-9-]+)"', html)
            kaarten = list(dict.fromkeys(kaarten))
            self.assertIn(nieuw.slug, kaarten, adres)
            if "ontwerpen" not in adres:
                self.assertEqual(kaarten[0], nieuw.slug, adres)                         # in de keuze staat het nieuwste vooraan
                self.assertLess(kaarten.index(nieuw.slug), kaarten.index("liefde-op-papier"), adres)


class CollectieVolgordeTests(VaylideTestCase):
    """Specials eerst, daarna de gewone ontwerpen, overal het nieuwst toegevoegde eerst; één sorteermethode voor de hele collectie."""

    def zet(self, slug, dagen_geleden, uren=0):
        Template.objects.filter(slug=slug).update(created_at=timezone.now() - timedelta(days=dagen_geleden, hours=uren))

    def volgorde(self, **filter):
        from core.views import _design_cards  # noqa: F401  (de pagina gebruikt dezelfde kaarten)

        antwoord = Client().get("/ontwerpen/", filter)
        self.assertEqual(antwoord.status_code, 200)
        return [c["template"].slug for c in antwoord.context["special_cards"]], [c["template"].slug for c in antwoord.context["cards"]]

    def test_specials_eerst_en_een_nieuw_special_staat_op_plek_1(self):
        Template.objects.update(created_at=timezone.now() - timedelta(days=200))
        self.zet("balzaal", 30)
        self.zet("kerststad", 5)
        specials, gewoon = self.volgorde()
        self.assertEqual(specials[:2], ["kerststad", "balzaal"])
        # Een nieuw toegevoegd Special (hier: een bestaand Special dat nu 'nieuw' wordt) staat links boven, op plek 1.
        self.zet("aurora-nocturne", 0)
        specials, gewoon = self.volgorde()
        self.assertEqual(specials[0], "aurora-nocturne")
        # De gewone ontwerpen staan er los van, ook van nieuw naar oud.
        self.zet("avondgoud", 1)
        specials, gewoon = self.volgorde()
        self.assertEqual(gewoon[0], "avondgoud")
        self.assertFalse(set(specials) & set(gewoon))

    def test_op_de_pagina_staan_de_specials_boven_de_gewone_ontwerpen_in_dezelfde_volgorde_voor_telefoon_en_computer(self):
        Template.objects.update(created_at=timezone.now() - timedelta(days=200))
        self.zet("midnight-emeraude", 2)
        self.zet("puur-moment", 1)
        html = Client().get("/ontwerpen/").content.decode()
        eerste_special = html.index('/ontwerpen/midnight-emeraude/')
        eerste_gewoon = html.index('/ontwerpen/puur-moment/')
        self.assertLess(eerste_special, eerste_gewoon)                              # in de bron (en dus op een telefoon): Specials bovenaan
        self.assertLess(html.index('class="specials"'), html.index('<h2 class="specials__vervolg">'))
        self.assertLess(html.index('<h2 class="specials__vervolg">'), eerste_gewoon)

    def test_filters_blijven_werken_en_er_verdwijnt_niets(self):
        alles_s, alles_g = self.volgorde()
        self.assertEqual(len(alles_s) + len(alles_g), Template.objects.filter(is_active=True, current_version__isnull=False).count())
        s, g = self.volgorde(gelegenheid="kerst")
        self.assertTrue(all("kerst" in Template.objects.get(slug=x).occasions for x in s + g))
        only_s, only_g = self.volgorde(categorie="specials")
        self.assertEqual(only_g, [])
        self.assertEqual(only_s, alles_s)
        inactief = Template.objects.get(slug="puur-moment")
        Template.objects.filter(pk=inactief.pk).update(is_active=False)
        s, g = self.volgorde()
        self.assertNotIn("puur-moment", s + g)                                       # alleen gepubliceerde ontwerpen
        self.assertEqual(Client().get("/inspiratie/").status_code, 200)

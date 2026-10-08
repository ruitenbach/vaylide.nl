"""Eén Studio-traject = één concept: een ontwerp kiezen maakt het concept, een ander ontwerp kiezen (Wijzigen of opnieuw op de startpagina) werkt
hetzelfde concept bij zolang er nog niets is ingevuld, en pas een echt nieuw traject maakt een nieuw concept. Dat houdt de limiet van 40 conceptstarts per uur redelijk."""
from django.core.cache import cache
from django.test import Client

from invitations.models import Invitation

from .helpers import VaylideTestCase

ONTWERPEN = ["liefde-op-papier", "eucalyptus", "avondgoud", "puur-moment", "pampas", "rozentuin"]


class ConceptHergebruikTests(VaylideTestCase):
    def setUp(self):
        cache.clear()
        self.c = Client()

    def kies(self, slug, client=None, **extra):
        return (client or self.c).post("/maken/", {"occasion": "bruiloft", "template": slug, **extra})

    def uid(self, reactie):
        return reactie["Location"].split("/")[2]

    def test_een_ontwerp_kiezen_maakt_een_concept(self):
        reactie = self.kies(ONTWERPEN[0])
        self.assertRegex(reactie["Location"], r"^/maken/[0-9a-f-]{36}/gegevens/$")
        self.assertEqual(Invitation.objects.count(), 1)

    def test_vijf_keer_ander_ontwerp_via_wijzigen_blijft_hetzelfde_concept_met_dezelfde_gegevens(self):
        uid = self.uid(self.kies(ONTWERPEN[0]))
        inv = Invitation.objects.get(uid=uid)
        self.c.post(f"/maken/{uid}/gegevens/", {"rev": inv.draft_rev, "actie": "opslaan", "name_partner_1": "Sanne", "venue_name": "De Oranjerie", "timezone": "Europe/Amsterdam"})
        for slug in ONTWERPEN[1:6]:
            inv.refresh_from_db()
            reactie = self.c.post(f"/maken/{uid}/ontwerp/", {"rev": inv.draft_rev, "occasion": "bruiloft", "template": slug, "terug": "gegevens"})
            self.assertTrue(reactie["Location"].startswith(f"/maken/{uid}/"), reactie["Location"])
        self.assertEqual(Invitation.objects.count(), 1)
        inv.refresh_from_db()
        self.assertEqual(inv.template_version.template.slug, ONTWERPEN[5])
        self.assertEqual(inv.draft_content["names"]["partner_1"], "Sanne")
        self.assertEqual(inv.draft_content["venue_name"], "De Oranjerie")

    def test_vijf_keer_opnieuw_een_ontwerp_kiezen_op_de_startpagina_werkt_hetzelfde_concept_bij(self):
        uid = self.uid(self.kies(ONTWERPEN[0]))
        for slug in ONTWERPEN[1:6]:
            reactie = self.kies(slug)
            self.assertEqual(self.uid(reactie), uid)               # hetzelfde concept
        self.assertEqual(Invitation.objects.count(), 1)
        inv = Invitation.objects.get(uid=uid)
        self.assertEqual(inv.template_version.template.slug, ONTWERPEN[5])

    def test_wijzigen_en_opnieuw_kiezen_door_elkaar_blijft_een_concept(self):
        uid = self.uid(self.kies(ONTWERPEN[0]))
        inv = Invitation.objects.get(uid=uid)
        self.c.post(f"/maken/{uid}/ontwerp/", {"rev": inv.draft_rev, "occasion": "bruiloft", "template": ONTWERPEN[1]})
        self.assertEqual(self.uid(self.kies(ONTWERPEN[2])), uid)
        inv.refresh_from_db()
        self.c.post(f"/maken/{uid}/ontwerp/", {"rev": inv.draft_rev, "occasion": "bruiloft", "template": ONTWERPEN[3]})
        self.assertEqual(self.uid(self.kies(ONTWERPEN[4])), uid)
        self.assertEqual(Invitation.objects.count(), 1)

    def test_herladen_blijft_hetzelfde_concept(self):
        uid = self.uid(self.kies(ONTWERPEN[0]))
        for _ in range(3):
            self.assertEqual(self.c.get(f"/maken/{uid}/gegevens/").status_code, 200)       # herladen van de pagina
            self.c.get("/maken/", {"gelegenheid": "bruiloft"})                              # en de startpagina bekijken maakt niets
        self.assertEqual(Invitation.objects.count(), 1)

    def test_na_invoer_maakt_een_nieuwe_keuze_op_de_startpagina_een_nieuw_concept(self):
        uid = self.uid(self.kies(ONTWERPEN[0]))
        inv = Invitation.objects.get(uid=uid)
        self.c.post(f"/maken/{uid}/gegevens/", {"rev": inv.draft_rev, "actie": "opslaan", "name_partner_1": "Sanne", "timezone": "Europe/Amsterdam"})
        tweede = self.uid(self.kies(ONTWERPEN[1]))
        self.assertNotEqual(tweede, uid)                       # er stond al iets in: dit is een nieuw traject
        self.assertEqual(Invitation.objects.count(), 2)
        self.assertEqual(Invitation.objects.get(uid=uid).draft_content["names"]["partner_1"], "Sanne")      # het eerste concept blijft intact
        self.assertEqual(self.uid(self.kies(ONTWERPEN[2])), tweede)                                           # en het tweede is nu het lopende traject

    def test_een_ander_apparaat_of_klant_start_een_los_concept(self):
        uid = self.uid(self.kies(ONTWERPEN[0]))
        ander = Client()
        self.assertNotEqual(self.uid(self.kies(ONTWERPEN[0], client=ander)), uid)
        self.assertEqual(Invitation.objects.count(), 2)
        klant = self.make_customer()
        ingelogd = Client()
        ingelogd.force_login(klant)
        derde = self.uid(self.kies(ONTWERPEN[0], client=ingelogd))
        self.assertEqual(self.uid(self.kies(ONTWERPEN[1], client=ingelogd)), derde)
        self.assertEqual(Invitation.objects.count(), 3)
        self.assertEqual(Invitation.objects.get(uid=derde).owner, klant)

    def test_wenskaart_en_uitnodiging_blijven_kloppen_bij_opnieuw_kiezen(self):
        uid = self.uid(self.kies(ONTWERPEN[0], soort="wenskaart", pakket="compleet"))
        inv = Invitation.objects.get(uid=uid)
        self.assertEqual((inv.draft_content["soort"], inv.package_code), ("wenskaart", ""))      # een wenskaart heeft geen pakket
        self.assertEqual(self.uid(self.kies(ONTWERPEN[1], soort="uitnodiging", pakket="compleet")), uid)
        inv.refresh_from_db()
        self.assertEqual((inv.draft_content["soort"], inv.package_code), ("uitnodiging", "compleet"))
        self.assertEqual(self.uid(self.kies(ONTWERPEN[2], soort="wenskaart")), uid)
        inv.refresh_from_db()
        self.assertEqual((inv.draft_content["soort"], inv.package_code), ("wenskaart", ""))
        self.assertEqual(Invitation.objects.count(), 1)

    def test_gelegenheid_en_kleur_volgen_de_nieuwe_keuze(self):
        uid = self.uid(self.c.post("/maken/", {"occasion": "bruiloft", "template": "liefde-op-papier"}))
        reactie = self.c.post("/maken/", {"occasion": "verjaardag", "template": "confetti"})
        self.assertEqual(self.uid(reactie), uid)
        inv = Invitation.objects.get(uid=uid)
        self.assertEqual((inv.occasion, inv.template_version.template.slug), ("verjaardag", "confetti"))
        self.assertEqual(inv.draft_content["style"]["palette"], inv.template_version.default_palette_key)

    def test_bestellen_blijft_werken_na_ontwerpwissels(self):
        uid = self.uid(self.kies(ONTWERPEN[0]))
        for slug in ONTWERPEN[1:4]:
            self.kies(slug)
        pagina = self.c.get(f"/maken/{uid}/bestellen/")
        self.assertEqual(pagina.status_code, 200)
        self.assertContains(pagina, "Bestellen")
        self.assertContains(self.c.get(f"/maken/{uid}/voorbeeld/"), "Verder naar bestellen")

    def test_betaald_of_vergrendeld_concept_wordt_nooit_hergebruikt(self):
        klant = self.make_customer()
        c = Client()
        c.force_login(klant)
        uid = self.uid(self.kies(ONTWERPEN[0], client=c))
        inv = Invitation.objects.get(uid=uid)
        inv.customer_locked = True
        inv.save(update_fields=["customer_locked"])
        self.assertNotEqual(self.uid(self.kies(ONTWERPEN[1], client=c)), uid)

    def test_de_limiet_van_40_conceptstarts_per_uur_geldt_voor_nieuwe_concepten_en_niet_voor_een_ontwerpwissel(self):
        gestart = 0
        for _ in range(40):
            reactie = self.kies(ONTWERPEN[0], client=Client())              # 40 aparte trajecten vanaf hetzelfde adres
            gestart += reactie["Location"].startswith("/maken/") and "/gegevens/" in reactie["Location"]
        self.assertEqual(gestart, 40)
        geweigerd = self.kies(ONTWERPEN[0], client=Client())
        self.assertEqual(geweigerd["Location"], "/maken/")                  # de 41e nieuwe start wordt geweigerd
        self.assertEqual(Invitation.objects.count(), 40)
        # Een ontwerpwissel in een lopend traject maakt geen nieuw concept en telt dus niet mee, ook niet boven de limiet.
        cache.clear()
        eigen = Client()
        uid = self.uid(self.kies(ONTWERPEN[0], client=eigen))
        for i in range(60):
            self.assertEqual(self.uid(self.kies(ONTWERPEN[i % 5 + 1], client=eigen)), uid)
        self.assertEqual(Invitation.objects.count(), 41)

"""Aanmelden met een aantal personen, van de gast tot het overzicht van de maker: 'Met hoeveel personen kom je?' wordt
opgeslagen, hoort bij de juiste aanmelding en staat in het gastenoverzicht, de samenvatting en de csv."""
from django.core.cache import cache
from django.test import Client

from invitations.models import GuestResponse
from invitations.services import publish_draft, save_draft

from .helpers import VaylideTestCase


class RsvpAantalPersonenTests(VaylideTestCase):
    def setUp(self):
        cache.clear()
        self.owner = self.make_customer()
        self.inv = self.published(owner=self.owner)
        content = dict(self.inv.draft_content)
        content["rsvp"] = dict(content["rsvp"], max_party_size=4)
        self.inv = save_draft(self.inv, expected_rev=None, content=content, user=self.owner)
        publish_draft(self.inv, user=self.owner, source="customer", expected_rev=None)
        self.inv.refresh_from_db()
        self.maker = Client()
        self.maker.force_login(self.owner)

    def test_de_gast_ziet_de_vraag_en_het_aantal_wordt_correct_opgeslagen(self):
        pagina = Client().get(self.inv.public_path).content.decode()
        self.assertIn("Met hoeveel personen kom je?", pagina)
        self.assertIn("maximaal 4", pagina)
        for aantal in range(1, 5):
            self.assertIn(f'<option value="{aantal}"', pagina)
        self.assertNotIn('<option value="5"', pagina)
        antwoord = self.rsvp(Client(), self.inv, name="Familie Visser", attending="ja", party_size="3")
        self.assertTrue(antwoord.json()["ok"], antwoord.content)
        self.assertIn("Aangemeld met 3 personen.", antwoord.json()["message"])       # de bevestiging noemt het aantal
        alleen = self.rsvp(Client(), self.inv, name="Zonder Gezelschap", attending="ja", party_size="1").json()
        self.assertNotIn("Aangemeld met", alleen["message"])
        aanmelding = GuestResponse.objects.get(invitation=self.inv, name="Familie Visser")
        self.assertEqual((aanmelding.name, aanmelding.attending, aanmelding.party_size, aanmelding.persons), ("Familie Visser", True, 3, 3))

    def test_het_aantal_hoort_bij_de_eigen_aanmelding_en_telt_op_in_het_overzicht(self):
        self.rsvp(Client(), self.inv, name="Anna", attending="ja", party_size="2")
        self.rsvp(Client(), self.inv, name="Bram", attending="ja", party_size="4")
        self.rsvp(Client(), self.inv, name="Carla", attending="nee", party_size="3")         # afwezig telt nooit mee
        self.rsvp(Client(), self.inv, name="Daan", attending="ja", party_size="1")
        per_naam = {r.name: (r.attending, r.party_size) for r in GuestResponse.objects.filter(invitation=self.inv)}
        self.assertEqual(per_naam["Anna"], (True, 2))
        self.assertEqual(per_naam["Bram"], (True, 4))
        self.assertEqual(per_naam["Carla"][0], False)
        self.assertEqual(per_naam["Daan"], (True, 1))
        overzicht = self.maker.get(f"/account/uitnodiging/{self.inv.uid}/gasten/")
        self.assertEqual(overzicht.status_code, 200)
        self.assertEqual(overzicht.context["stats"]["yes"], 3)
        self.assertEqual(overzicht.context["stats"]["persons"], 7)        # 2 + 4 + 1
        html = overzicht.content.decode()
        self.assertRegex(html, r'data-label="Naam"><strong>Bram</strong></td>\s*<td data-label="Aanwezig">ja</td>\s*<td data-label="Personen" class="num">4</td>')
        self.assertRegex(html, r'data-label="Naam"><strong>Carla</strong></td>\s*<td data-label="Aanwezig">nee</td>\s*<td data-label="Personen" class="num">0</td>')
        samenvatting = self.maker.get(f"/account/uitnodiging/{self.inv.uid}/").content.decode()
        self.assertIn("Aanwezig · 4 personen", samenvatting)
        self.assertIn("Aanwezig · 1 persoon", samenvatting)

    def test_csv_voor_de_maker_bevat_het_aantal_personen(self):
        self.rsvp(Client(), self.inv, name="Elif", attending="ja", party_size="3")
        csv_tekst = self.maker.get(f"/account/uitnodiging/{self.inv.uid}/gasten/export.csv").content.decode("utf-8-sig")
        kop, rij = csv_tekst.splitlines()[:2]
        self.assertIn("Aantal personen", kop)
        self.assertEqual(rij.split(";")[:3], ["Elif", "ja", "3"])

    def test_gast_wijzigt_het_aantal_via_de_eigen_link(self):
        gast = Client()
        edit_url = self.rsvp(gast, self.inv, name="Fenna", attending="ja", party_size="2").json()["edit_url"]
        pagina = gast.get(edit_url).content.decode()
        self.assertIn("Met hoeveel personen kom je?", pagina)
        antwoord = gast.post(edit_url, {"name": "Fenna", "attending": "ja", "party_size": "4"})
        self.assertEqual(antwoord.status_code, 302)
        aanmelding = GuestResponse.objects.get(invitation=self.inv)
        self.assertEqual(aanmelding.party_size, 4)
        self.assertEqual(aanmelding.edit_count, 1)
        overzicht = self.maker.get(f"/account/uitnodiging/{self.inv.uid}/gasten/")
        self.assertEqual(overzicht.context["stats"]["persons"], 4)

    def test_te_veel_personen_en_een_vreemde_maker_zien_niets(self):
        antwoord = self.rsvp(Client(), self.inv, name="Gijs", attending="ja", party_size="9")
        self.assertEqual(antwoord.status_code, 400)
        self.assertIn("party_size", antwoord.json()["errors"])
        self.assertFalse(GuestResponse.objects.exists())
        self.rsvp(Client(), self.inv, name="Hanna", attending="ja", party_size="2")
        vreemd = Client()
        vreemd.force_login(self.make_customer("ander@example.com"))
        self.assertEqual(vreemd.get(f"/account/uitnodiging/{self.inv.uid}/gasten/").status_code, 404)    # gasten en aantallen zijn alleen voor de maker
        self.assertEqual(Client().get(f"/account/uitnodiging/{self.inv.uid}/gasten/").status_code, 302)  # en alleen na inloggen

    def test_zonder_maximum_boven_een_vraagt_de_kaart_geen_aantal(self):
        content = dict(self.inv.draft_content)
        content["rsvp"] = dict(content["rsvp"], max_party_size=1)
        self.inv = save_draft(self.inv, expected_rev=None, content=content, user=self.owner)
        publish_draft(self.inv, user=self.owner, source="customer", expected_rev=None)
        self.assertNotIn("Met hoeveel personen kom je?", Client().get(self.inv.public_path).content.decode())
        self.rsvp(Client(), self.inv, name="Iris", attending="ja", party_size="3")
        self.assertEqual(GuestResponse.objects.get().party_size, 1)         # een gast die alleen zichzelf aanmeldt telt als één

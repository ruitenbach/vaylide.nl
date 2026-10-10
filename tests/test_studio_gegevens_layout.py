"""Studio, stap Gegevens: naamvelden, één naam bij een wenskaart en een rustige live kaart zonder mee te bewegen met de muis."""
from pathlib import Path

from django.conf import settings
from django.test import Client

from catalog.models import Template
from invitations.content import normalize_content, publish_issues
from invitations.services import create_draft, save_draft

from .helpers import VaylideTestCase, future_date

CSS = (Path(settings.BASE_DIR) / "static/css/app.css").read_text(encoding="utf-8")
LIVE_JS = (Path(settings.BASE_DIR) / "invitations/static/invitations/live.js").read_text(encoding="utf-8")


def post(c, inv, **extra):
    data = {"rev": inv.draft_rev, "actie": "volgende", "timezone": "Europe/Amsterdam", "welcome_text": "Hoi!"}
    data.update(extra)
    return c.post(f"/maken/{inv.uid}/gegevens/", data)


class PartnerTweeTests(VaylideTestCase):
    def setUp(self):
        self.owner = self.make_customer()
        self.c = Client()
        self.c.force_login(self.owner)

    def draft(self, soort="", occasion="bruiloft", template="liefde-op-papier"):
        return create_draft(occasion=occasion, template=Template.objects.get(slug=template), owner=self.owner, soort=soort)

    def test_beide_naamvelden_hebben_dezelfde_structuur_en_zijn_optioneel(self):
        inv = self.draft()
        html = self.c.get(f"/maken/{inv.uid}/gegevens/").content.decode()
        for naam in ("name_partner_1", "name_partner_2"):
            blok = html.split(f'name="{naam}"')[1][:300]
            self.assertNotIn('data-required="1"', blok, naam)
        for nummer in ("1", "2"):
            self.assertIn(f'for="id_name_partner_{nummer}"', html)
        self.assertNotIn('class="req"', html)           # nergens een verplicht-sterretje

    def test_uitnodiging_zonder_namen_kan_door_en_bewaart_niets_vervelends(self):
        inv = self.draft()
        response = post(self.c, inv, name_partner_1="Anna", date=future_date(60), start_time="14:00", venue_name="Kasteel")
        self.assertEqual(response.status_code, 302)     # partner 2 mag leeg blijven
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["names"], {"partner_1": "Anna", "partner_2": ""})
        inv.refresh_from_db()
        response = post(self.c, inv)                    # en helemaal leeg doorgaan kan ook
        self.assertEqual(response.status_code, 302)

    def test_wenskaart_heeft_aan_een_naam_genoeg(self):
        inv = self.draft("wenskaart")
        html = self.c.get(f"/maken/{inv.uid}/gegevens/").content.decode()
        self.assertIn('name="name_partner_1"', html)
        self.assertRegex(html.split('name="name_partner_2"')[1][:260], r'data-required=""')
        response = post(self.c, inv, soort="wenskaart", name_partner_1="Anna")
        self.assertEqual(response.status_code, 302)
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["names"]["partner_1"], "Anna")
        self.assertEqual(inv.draft_content["names"]["partner_2"], "")
        self.assertEqual([i for i in publish_issues(inv.draft_content, "bruiloft", first_publication=True) if i.blocking], [])

    def test_bij_een_wenskaart_is_de_eerste_naam_nodig_om_te_bestellen_maar_opslaan_blokkeert_niet(self):
        inv = self.draft("wenskaart")
        response = post(self.c, inv, soort="wenskaart", name_partner_2="Bram")
        self.assertEqual(response.status_code, 302)
        inv.refresh_from_db()
        self.assertEqual([i.field for i in publish_issues(inv.draft_content, "bruiloft", first_publication=True) if i.blocking], ["partner_1"])

    def test_wisselen_van_wenskaart_naar_uitnodiging_vraagt_niets_meer(self):
        inv = self.draft("wenskaart")
        response = post(self.c, inv, soort="uitnodiging", name_partner_1="Anna", date=future_date(60), start_time="14:00", venue_name="Kasteel")
        self.assertEqual(response.status_code, 302)
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["soort"], "uitnodiging")

    def test_partner_twee_wordt_opgeslagen_bewaard_en_komt_in_de_live_preview(self):
        inv = self.draft()
        post(self.c, inv, actie="opslaan", name_partner_1="Anna", name_partner_2="Bram")
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["names"], {"partner_1": "Anna", "partner_2": "Bram"})
        html = self.c.get(f"/maken/{inv.uid}/gegevens/").content.decode()
        self.assertIn('value="Bram"', html)
        frame = self.c.get(f"/maken/{inv.uid}/voorbeeld/live/?deel=gegevens").content.decode()
        self.assertIn("Anna", frame)
        self.assertIn("Bram", frame)

    def test_een_naam_op_een_wenskaart_rendert_zonder_gat(self):
        inv = self.draft("wenskaart")
        post(self.c, inv, actie="opslaan", soort="wenskaart", name_partner_1="Anna")
        frame = self.c.get(f"/maken/{inv.uid}/voorbeeld/live/?deel=gegevens").content.decode()
        self.assertIn("Anna", frame)
        self.assertNotIn("Anna &amp; ", frame)
        self.assertNotIn("Anna & ", frame)

    def test_andere_gelegenheden_hebben_ook_geen_verplichte_velden(self):
        for occasion, template, veld in (("verjaardag", "avondgoud", "name_person_name"), ("kerst", "winterlicht", "name_family")):
            inv = self.draft("wenskaart", occasion, template)
            self.assertEqual(post(self.c, inv, soort="wenskaart").status_code, 302, occasion)
            inv.refresh_from_db()
            self.assertEqual(post(self.c, inv, soort="wenskaart", **{veld: "Naam"}).status_code, 302, occasion)

class LayoutEnLiveKaartTests(VaylideTestCase):
    def test_velden_naast_elkaar_staan_op_dezelfde_rijen(self):
        self.assertIn("grid-template-rows: subgrid", CSS)
        self.assertIn(".studio-form .form-row > .field > .hint { grid-row: 2; }", CSS)
        self.assertIn(".studio-form .form-row { align-items: start; }", CSS)

    def test_telefoonframe_staat_vast(self):
        self.assertNotIn("live-zweef", CSS)                      # geen zwevende beweging meer
        self.assertNotIn(".live-kaart__card.is-updating { transform", CSS)
        self.assertIn("scrollbar-gutter: stable", CSS)

    def test_live_kaart_negeert_de_muis_maar_het_voorbeeld_niet(self):
        self.assertIn('window.addEventListener("pointermove", negeerAanwijzer, true)', LIVE_JS)
        self.assertIn('window.addEventListener("mousemove", negeerAanwijzer, true)', LIVE_JS)
        self.assertNotIn("pointerdown", LIVE_JS.split("negeerAanwijzer")[1][:400])      # tikken en klikken blijven werken
        owner = self.make_customer()
        inv = create_draft(occasion="bruiloft", template=Template.objects.get(slug="liefde-op-papier"), owner=owner)
        c = Client()
        c.force_login(owner)
        self.assertIn("invitations/live.js", c.get(f"/maken/{inv.uid}/voorbeeld/live/?deel=gegevens").content.decode())
        self.assertNotIn("invitations/live.js", c.get(f"/maken/{inv.uid}/voorbeeld/weergave/").content.decode())
        self.assertNotIn("invitations/live.js", Client().get("/voorbeeld/liefde-op-papier/").content.decode())

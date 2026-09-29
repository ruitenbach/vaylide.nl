"""Aanmelden zonder gevoelige gegevens (optie A, 30 september 2026): alleen vaste, neutrale extra vragen, een vaste
toelichtingsvraag met uitleg, oude eigen vragen blijven staan, en een rapport dat alleen telt."""
import io
from unittest import mock

from django.core.management import call_command
from django.test import Client

from catalog.models import AddOn
from invitations.content import default_content
from invitations.models import GuestResponse
from invitations.services import save_draft
from invitations.vragen import HINT_GEVOELIG, VRAGEN, eigen_vragen, is_vast, vraag
from studio.forms import RsvpSettingsForm

from .helpers import VaylideTestCase, future_date

OUDE_VRAAG = {"id": "q1", "label": "Heb je dieetwensen of allergieën?", "type": "text", "options": [], "required": False}


class FixedListTests(VaylideTestCase):
    def test_fixed_questions_are_neutral(self):
        woorden = ("dieet", "allergi", "medisch", "gezond", "geloof", "religi", "halal", "vega")
        for v in VRAGEN:
            tekst = " ".join([v["label"], v["label_u"], *v["options"]]).lower()
            self.assertFalse(any(w in tekst for w in woorden), v["key"])
            self.assertTrue(is_vast(vraag(v["key"], formal=False)))
            self.assertTrue(is_vast(vraag(v["key"], formal=True)))

    def test_changed_label_or_options_is_not_fixed(self):
        q = vraag("vervoer", formal=False)
        self.assertFalse(is_vast(dict(q, label="Wat eet je niet?")))
        self.assertFalse(is_vast(dict(q, options=["Vis", "Vega", "Halal"])))
        self.assertEqual(eigen_vragen([q, OUDE_VRAAG]), [OUDE_VRAAG])

    def test_new_invitations_ask_only_name_attendance_and_party_size(self):
        content = default_content("bruiloft")
        self.assertFalse(content["rsvp"]["ask_remark"])
        self.assertEqual(content["rsvp"]["questions"], [])
        self.assertEqual(default_content("zakelijk")["rsvp"]["remark_label"], "Wilt u nog iets laten weten?")

    def test_no_sensitive_examples_on_the_site(self):
        for url in ("/", "/prijzen/", "/zo-werkt-het/", "/voorbeeld/liefde-op-papier/", "/voorbeeld/aan-tafel/"):
            html = Client().get(url).content.decode().lower()
            self.assertNotIn("dieetwens", html, url)
            self.assertNotIn("allergieën?", html, url)
        self.assertNotIn("dieet", AddOn.objects.get(code="extra-vragen").description.lower())


class StudioTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer)
        self.c = Client()
        self.c.force_login(self.customer)

    def post(self, **data):
        self.inv.refresh_from_db()
        payload = {"rev": self.inv.draft_rev, "actie": "opslaan", "enabled": "on", "deadline": future_date(10), "max_party_size": "2"}
        payload.update(data)
        response = self.c.post(f"/maken/{self.inv.uid}/aanmelden/", payload)
        self.inv.refresh_from_db()
        return response

    def test_page_offers_only_fixed_questions(self):
        html = self.c.get(f"/maken/{self.inv.uid}/aanmelden/").content.decode()
        self.assertIn('name="vraag_vervoer"', html)
        self.assertNotIn('name="q0_label"', html)
        self.assertNotIn('name="remark_label"', html)
        self.assertNotIn("dieetwensen", html)

    def test_free_text_from_a_crafted_post_is_ignored(self):
        self.post(vraag_vervoer="on", verplicht_vervoer="on", q0_label="Welke medicijnen gebruik je?", q0_type="text",
                  remark_label="Heb je allergieën?", ask_remark="on")
        rsvp = self.inv.draft_content["rsvp"]
        self.assertEqual(rsvp["questions"], [vraag("vervoer", formal=False, required=True)])
        self.assertEqual(rsvp["remark_label"], "Wil je nog iets laten weten?")
        self.assertTrue(rsvp["ask_remark"])

    def test_formal_occasion_uses_u(self):
        form = RsvpSettingsForm({"enabled": "on", "deadline": future_date(10), "max_party_size": "2", "vraag_parkeren": "on"},
                                content=dict(self.inv.draft_content), occasion="zakelijk")
        self.assertTrue(form.is_valid(), form.errors)
        content = form.apply(dict(self.inv.draft_content))
        self.assertEqual(content["rsvp"]["questions"][0]["label"], "Heeft u een parkeerplek nodig?")
        self.assertEqual(content["rsvp"]["remark_label"], "Wilt u nog iets laten weten?")

    def test_old_own_questions_are_kept_until_removed(self):
        content = dict(self.inv.draft_content)
        content["rsvp"] = dict(content["rsvp"], questions=[OUDE_VRAAG], remark_label="Wat eet je liever niet?")
        save_draft(self.inv, expected_rev=None, content=content, user=self.customer)
        page = self.c.get(f"/maken/{self.inv.uid}/aanmelden/")
        self.assertContains(page, "Eigen vragen van eerder")
        self.assertContains(page, "Eigen vraag bij de toelichting")
        self.post(vraag_liedje="on")  # opslaan zonder weghalen: niets van de klant stil veranderd
        rsvp = self.inv.draft_content["rsvp"]
        self.assertIn(OUDE_VRAAG, rsvp["questions"])
        self.assertEqual(rsvp["remark_label"], "Wat eet je liever niet?")
        self.post(vraag_liedje="on", oud_0_weg="on", remark_standaard="on")
        rsvp = self.inv.draft_content["rsvp"]
        self.assertEqual(rsvp["questions"], [vraag("liedje", formal=False)])
        self.assertEqual(rsvp["remark_label"], "Wil je nog iets laten weten?")

    def test_old_questions_count_towards_the_maximum(self):
        content = dict(self.inv.draft_content)
        content["rsvp"] = dict(content["rsvp"], questions=[OUDE_VRAAG])
        save_draft(self.inv, expected_rev=None, content=content, user=self.customer)
        response = self.post(**{f"vraag_{v['key']}": "on" for v in VRAGEN[:5]})
        self.assertContains(response, "Kies maximaal 5 extra vragen.")


class GuestFlowTests(VaylideTestCase):
    def publish_with(self, *, questions, ask_remark=False, max_party=3, package="compleet"):
        owner = self.make_customer("org@example.com")
        inv = self.make_invitation(owner=owner)
        content = dict(inv.draft_content)
        content["rsvp"] = dict(content["rsvp"], questions=questions, ask_remark=ask_remark, max_party_size=max_party)
        inv = save_draft(inv, expected_rev=None, content=content, user=owner)
        self.pay(inv, owner, package=package)
        inv.refresh_from_db()
        return inv, owner

    def test_default_form_has_no_free_text(self):
        inv, _ = self.publish_with(questions=[])
        html = Client().get(inv.public_path).content.decode()
        self.assertNotIn('name="remark"', html)
        self.assertNotIn(HINT_GEVOELIG, html)
        self.assertIn('name="party_size"', html)

    def test_free_text_fields_carry_the_hint(self):
        inv, _ = self.publish_with(questions=[vraag("liedje", formal=False)], ask_remark=True)
        html = Client().get(inv.public_path).content.decode()
        self.assertEqual(html.count(HINT_GEVOELIG), 2)  # open vraag en toelichting
        self.assertIn('aria-describedby="rsvp-remark-hint"', html)

    def test_attend_decline_party_size_and_server_validation(self):
        inv, owner = self.publish_with(questions=[vraag("vervoer", formal=False, required=True)])
        guest = Client()
        self.assertIn("q_vervoer", self.rsvp(guest, inv, name="A").json()["errors"])  # verplicht
        self.assertIn("q_vervoer", self.rsvp(guest, inv, name="A", q_vervoer="Halal menu").json()["errors"])  # niet in de lijst
        self.assertIn("party_size", self.rsvp(guest, inv, name="A", q_vervoer="Met de auto", party_size="4").json()["errors"])
        self.assertTrue(self.rsvp(Client(), inv, name="Anna", q_vervoer="Met de auto", party_size="2", q_extra="stiekem").json()["ok"])
        self.assertTrue(self.rsvp(Client(), inv, name="Bram", attending="nee").json()["ok"])
        anna = GuestResponse.objects.get(invitation=inv, name="Anna")
        self.assertEqual(anna.party_size, 2)
        self.assertEqual(anna.answers, [{"id": "vervoer", "label": "Hoe kom je?", "value": "Met de auto"}])
        bram = GuestResponse.objects.get(invitation=inv, name="Bram")
        self.assertFalse(bram.attending)
        self.assertEqual(bram.answers, [])
        # De organisator ziet de vraag en het antwoord, ook in de export.
        c = Client()
        c.force_login(owner)
        page = c.get(f"/account/uitnodiging/{inv.uid}/gasten/")
        self.assertContains(page, "Hoe kom je?")
        self.assertContains(page, "Met de auto")
        csv_text = c.get(f"/account/uitnodiging/{inv.uid}/gasten/export.csv").content.decode("utf-8-sig")
        self.assertIn("Naam;Aanwezig;Aantal personen;Hoe kom je?;Toelichting", csv_text)
        self.assertIn("Anna;ja;2;Met de auto;", csv_text)

    def test_published_invitation_with_old_question_keeps_working(self):
        inv, owner = self.publish_with(questions=[OUDE_VRAAG])
        html = Client().get(inv.public_path).content.decode()
        self.assertIn("Heb je dieetwensen of allergieën?", html)  # gepubliceerd blijft zoals het was
        self.assertIn(HINT_GEVOELIG, html)  # wel met de uitleg bij het vrije veld
        self.assertTrue(self.rsvp(Client(), inv, name="C", q_q1="-").json()["ok"])
        c = Client()
        c.force_login(owner)
        self.assertIn("Heb je dieetwensen of allergieën?", c.get(f"/account/uitnodiging/{inv.uid}/gasten/export.csv").content.decode("utf-8-sig"))


class ReportTests(VaylideTestCase):
    def test_report_counts_without_showing_content(self):
        owner = self.make_customer("org@example.com")
        inv = self.make_invitation(owner=owner)
        content = dict(inv.draft_content)
        content["rsvp"] = dict(content["rsvp"], questions=[OUDE_VRAAG, vraag("vervoer", formal=False)], ask_remark=True,
                               remark_label="Welk geloof heb je?")
        inv = save_draft(inv, expected_rev=None, content=content, user=owner)
        self.pay(inv, owner, package="compleet")
        inv.refresh_from_db()
        self.rsvp(Client(), inv, name="Geheime Gast", q_q1="Pinda-allergie", remark="Iets persoonlijks")
        out = io.StringIO()
        call_command("rsvp_vragen_rapport", stdout=out)
        text = out.getvalue()
        for secret in ("dieetwensen", "Geheime Gast", "Pinda", "persoonlijks", "geloof heb", inv.slug):
            self.assertNotIn(secret, text)
        import json

        data = json.loads(text)
        self.assertEqual(data["met_eigen_vragen"]["gepubliceerd"], 1)
        self.assertEqual(data["eigen_vragen"]["totaal"], 1)
        self.assertEqual(data["eigen_vragen_per_risico"]["gezondheid of dieet"], 1)
        self.assertEqual(data["met_eigen_toelichtingsvraag"]["met_risicowoord"], 1)
        self.assertEqual(data["aanmeldingen"]["met_antwoord_op_risicovraag"], 1)
        self.assertEqual(data["aanmeldingen"]["met_ingevulde_toelichting"], 1)

    def test_report_changes_nothing(self):
        with mock.patch("invitations.models.Invitation.save") as save, mock.patch("invitations.models.GuestResponse.save") as gsave:
            call_command("rsvp_vragen_rapport", stdout=io.StringIO())
        save.assert_not_called()
        gsave.assert_not_called()


class NoCopiesTests(VaylideTestCase):
    def test_rsvp_answers_are_hidden_from_error_reports(self):
        from django.test import RequestFactory
        from django.views.debug import SafeExceptionReporterFilter

        from invitations import views

        for view in (views.rsvp_submit, views.rsvp_edit):
            request = RequestFactory().post("/u/x/aanmelden/", {"name": "Gast", "remark": "iets gevoeligs"})
            request.sensitive_post_parameters = "__ALL__"  # wat de decorator zet
            self.assertTrue(hasattr(view, "__wrapped__"))
            cleaned = SafeExceptionReporterFilter().get_post_parameters(request)
            self.assertNotEqual(cleaned["remark"], "iets gevoeligs")

    def test_decorator_is_applied(self):
        import inspect

        from invitations import views

        for name in ("rsvp_submit", "rsvp_edit"):
            source = inspect.getsource(getattr(views, name))
            self.assertIn("@sensitive_post_parameters()", source)

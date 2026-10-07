"""Controle 1: de volledige klantreis en het bewaren/hervatten van voortgang."""

from django.test import Client

from accounts.models import LoginCode
from invitations.content import publish_issues
from invitations.models import Invitation
from invitations.services import save_draft
from orders.models import Order
from processing.models import OutboundEmail

from .helpers import VaylideTestCase, future_date, jpeg_file


class FullJourneyTests(VaylideTestCase):
    def test_design_to_guest_response_seen_by_customer(self):
        c = Client()
        # 1-2. Gelegenheid en ontwerp kiezen.
        response = c.post("/maken/", {"occasion": "bruiloft", "template": "avondgoud"})
        self.assertEqual(response.status_code, 302)
        uid = response["Location"].split("/")[2]
        inv = Invitation.objects.get(uid=uid)
        self.assertIsNone(inv.owner)

        # 3. Gegevens invullen.
        response = c.post(f"/maken/{uid}/gegevens/", {
            "rev": inv.draft_rev, "actie": "volgende", "name_partner_1": "Sanne", "name_partner_2": "Daan",
            "date": future_date(150), "start_time": "14:00", "end_time": "23:30", "timezone": "Europe/Amsterdam",
            "venue_name": "De Oranjerie", "address": "Laan 1\nUtrecht", "welcome_text": "Welkom!",
        })
        self.assertRedirects(response, f"/maken/{uid}/programma/", fetch_redirect_response=False)
        inv.refresh_from_db()
        self.assertEqual(inv.title, "Sanne & Daan")

        # Programma en aanmelden.
        c.post(f"/maken/{uid}/programma/", {"rev": inv.draft_rev, "actie": "volgende", "p0_time": "14:00", "p0_title": "Ceremonie"})
        inv.refresh_from_db()
        c.post(f"/maken/{uid}/aanmelden/", {"rev": inv.draft_rev, "actie": "volgende", "enabled": "on", "deadline": future_date(100),
                                            "max_party_size": "3", "ask_remark": "on"})
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["rsvp"]["max_party_size"], 3)

        # 4. Foto uploaden en positioneren.
        response = c.post(f"/maken/{uid}/upload/", {"fotos": jpeg_file()}, HTTP_ACCEPT="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        asset_uid = response.json()["created"][0]["uid"]
        inv.refresh_from_db()
        c.post(f"/maken/{uid}/fotos/", {"rev": inv.draft_rev, "actie": "volgende", "hero": asset_uid,
                                        f"x_{asset_uid}": "30", f"y_{asset_uid}": "60", f"z_{asset_uid}": "110", "music_asset": ""})
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["photos"]["hero"], {"asset": asset_uid, "x": 30, "y": 60, "zoom": 1.1})

        # 5. Stijl en 6. voorbeeld.
        c.post(f"/maken/{uid}/stijl/", {"rev": inv.draft_rev, "actie": "volgende", "palette": "smaragd", "opening": "on", "s_countdown": "on", "s_program": "on"})
        preview = c.get(f"/maken/{uid}/voorbeeld/weergave/")
        self.assertContains(preview, "Sanne")
        self.assertContains(preview, "Voorbeeld")
        self.assertEqual(preview["X-Frame-Options"], "SAMEORIGIN")

        # Account/verificatie is nodig om te betalen.
        response = c.post(f"/maken/{uid}/bestellen/", {"actie": "betalen", "package": "essentieel", "terms": "on", "direct_leveren": "on", "online_dienst": "on"})
        self.assertContains(response, "Bevestig eerst je e-mailadres")
        self.assertFalse(Order.objects.exists())

        c.post("/inloggen/", {"email": "Sanne@Example.com", "next": f"/maken/{uid}/bestellen/", "doel": "bewaren"})
        code = c.session["vierlief_test_code"]["code"]
        response = c.post("/inloggen/code/", {"code": code})
        self.assertRedirects(response, f"/maken/{uid}/bestellen/", fetch_redirect_response=False)
        inv.refresh_from_db()
        self.assertEqual(inv.owner.email, "sanne@example.com")

        # 8-9. Controleren en (test)betalen: het bedrag komt van de server.
        response = c.post(f"/maken/{uid}/bestellen/", {"actie": "betalen", "package": "essentieel", "terms": "on", "direct_leveren": "on", "online_dienst": "on", "total": "1"})
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.total_cents, 3900)
        checkout = response["Location"]
        self.assertTrue(checkout.startswith("/betalen/test/"))

        # De bedankpagina publiceert niets zolang de provider niet heeft bevestigd.
        response = c.get(f"/bestelling/{order.uid}/")
        self.assertContains(response, "We wachten op de bevestiging")
        inv.refresh_from_db()
        self.assertEqual(inv.status, Invitation.Status.DRAFT)

        with self.captureOnCommitCallbacks(execute=True):
            response = c.post(checkout, {"uitkomst": "betaald"})
        self.assertRedirects(response, f"/bestelling/{order.uid}/", fetch_redirect_response=False)

        # 10. Automatisch gepubliceerd met link, e-mails en klantomgeving.
        inv.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertEqual(order.fulfilment_status, Order.Fulfilment.DONE)
        self.assertEqual(inv.status, Invitation.Status.LIVE)
        self.assertTrue(inv.slug.startswith("sanne-en-daan-"))
        self.assertIsNotNone(inv.available_until)
        kinds = set(OutboundEmail.objects.filter(order=order).values_list("kind", flat=True))
        self.assertEqual(kinds, {"order_confirmation", "invitation_live"})
        status = c.get(f"/bestelling/{order.uid}/")
        self.assertContains(status, inv.public_url)
        portal = c.get(f"/account/uitnodiging/{inv.uid}/")
        self.assertContains(portal, inv.public_url)
        self.assertEqual(c.get(f"/account/uitnodiging/{inv.uid}/qr.png").status_code, 200)

        # Gast meldt zich aan zonder account.
        guest = Client()
        page = guest.get(inv.public_path)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page["X-Robots-Tag"], "noindex, nofollow, noarchive")
        response = self.rsvp(guest, inv, name="Oma Truus", attending="ja", party_size="2", remark="We komen graag!")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertTrue(response.json()["ok"])

        # Klant ziet het antwoord.
        guests = c.get(f"/account/uitnodiging/{inv.uid}/gasten/")
        self.assertContains(guests, "Oma Truus")
        csv_export = c.get(f"/account/uitnodiging/{inv.uid}/gasten/export.csv").content.decode("utf-8-sig")
        self.assertIn("Oma Truus;ja;2", csv_export)

    def test_no_js_rsvp_redirects_to_own_answer_page(self):
        inv = self.published()
        guest = Client()
        response = self.rsvp(guest, inv, json=False, name="Piet", attending="nee")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/antwoord/", response["Location"])
        page = guest.get(response["Location"])
        self.assertContains(page, "Je antwoord is opgeslagen")


class ResumeProgressTests(VaylideTestCase):
    def test_anonymous_draft_survives_and_is_claimed_after_verification(self):
        c = Client()
        uid = c.post("/maken/", {"occasion": "verjaardag", "template": "puur-moment"})["Location"].split("/")[2]
        inv = Invitation.objects.get(uid=uid)
        c.post(f"/maken/{uid}/gegevens/", {"rev": inv.draft_rev, "actie": "opslaan", "name_person_name": "Lotte", "name_age": "30"})
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["names"]["person_name"], "Lotte")
        # 'Opslaan en later verder' zonder account leidt naar e-mailverificatie.
        response = c.post(f"/maken/{uid}/gegevens/", {"rev": inv.draft_rev, "actie": "opslaan", "name_person_name": "Lotte"})
        self.assertIn("/inloggen/?doel=bewaren", response["Location"])
        c.post("/inloggen/", {"email": "lotte@example.com", "doel": "bewaren", "next": f"/maken/{uid}/gegevens/"})
        c.post("/inloggen/code/", {"code": c.session["vierlief_test_code"]["code"]})
        inv.refresh_from_db()
        self.assertEqual(inv.owner.email, "lotte@example.com")
        self.assertTrue(OutboundEmail.objects.filter(kind="draft_saved", to="lotte@example.com").exists())

        # Later, op een ander apparaat: inloggen en verder gaan waar je was.
        other = Client()
        self.assertEqual(other.get(f"/maken/{uid}/gegevens/").status_code, 302)  # eerst inloggen
        other.post("/inloggen/", {"email": "lotte@example.com"})
        other.post("/inloggen/code/", {"code": other.session["vierlief_test_code"]["code"]})
        home = other.get("/account/")
        self.assertContains(home, "Lotte")
        resume = other.get(f"/maken/{uid}/")
        self.assertEqual(resume.status_code, 302)
        self.assertIn(f"/maken/{uid}/", resume["Location"])

    def test_login_link_requires_click_and_is_single_use(self):
        c = Client()
        code, plain, token = LoginCode.issue("link@example.com")
        page = c.get(f"/inloggen/link/{token}/")
        self.assertContains(page, "Inloggen")  # GET logt nog niet in (e-mailscanners)
        self.assertNotIn("_auth_user_id", c.session)
        c.post(f"/inloggen/link/{token}/")
        self.assertIn("_auth_user_id", c.session)
        second = Client().post(f"/inloggen/link/{token}/")
        self.assertEqual(second.status_code, 400)

    def test_wrong_code_is_rejected_and_attempts_limited(self):
        c = Client()
        c.post("/inloggen/", {"email": "x@example.com"})
        real = c.session["vierlief_test_code"]["code"]
        wrong = "000000" if real != "000000" else "111111"
        for _ in range(5):
            response = c.post("/inloggen/code/", {"code": wrong})
            self.assertContains(response, "klopt niet")
        # Na 5 foute pogingen werkt ook de juiste code niet meer.
        response = c.post("/inloggen/code/", {"code": real})
        self.assertContains(response, "klopt niet")
        self.assertNotIn("_auth_user_id", c.session)


class InvalidInputTests(VaylideTestCase):
    def setUp(self):
        self.c = Client()
        uid = self.c.post("/maken/", {"occasion": "bruiloft", "template": "liefde-op-papier"})["Location"].split("/")[2]
        self.inv = Invitation.objects.get(uid=uid)

    def post(self, step, data):
        self.inv.refresh_from_db()
        return self.c.post(f"/maken/{self.inv.uid}/{step}/", {"rev": self.inv.draft_rev, "actie": "volgende", **data})

    def test_leeg_gelaten_velden_blokkeren_niet_en_invoer_blijft_bewaard(self):
        response = self.post("gegevens", {"name_partner_1": "Anna", "timezone": "Europe/Amsterdam"})
        self.assertEqual(response.status_code, 302)     # niets is verplicht: door naar het volgende onderdeel
        self.assertTrue(response["Location"].endswith("/programma/"))
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["names"]["partner_1"], "Anna")
        self.assertEqual(self.inv.draft_content["date"], "")
        tips = [i for i in publish_issues(self.inv.draft_content, "bruiloft", first_publication=True)]
        self.assertTrue(tips and not any(i.blocking for i in tips))     # ontbrekende gegevens zijn alleen een tip

    def test_invalid_formats_are_rejected(self):
        response = self.post("gegevens", {"name_partner_1": "A", "name_partner_2": "B", "date": "31-02-2027", "start_time": "25:99",
                                          "timezone": "Mars/Base", "venue_name": "X", "route_url": "javascript:alert(1)"})
        self.assertContains(response, "Vul een geldige datum in.")
        self.assertContains(response, "Vul een geldige tijd in")
        self.assertContains(response, "Vul een volledige link in")
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["date"], "")

    def test_date_too_far_and_end_without_start(self):
        response = self.post("gegevens", {"name_partner_1": "A", "name_partner_2": "B", "date": "2099-01-01", "end_time": "23:00",
                                          "timezone": "Europe/Amsterdam", "venue_name": "X"})
        self.assertContains(response, "binnen vijf jaar")
        self.assertContains(response, "Vul ook een begintijd in.")

    def test_program_row_needs_title_and_phone_must_be_valid(self):
        response = self.post("programma", {"p0_time": "14:00", "p0_title": "", "contact_phone": "bel me maar", "contact_email": "geen-mail"})
        self.assertContains(response, "Geef dit onderdeel een naam")
        self.assertContains(response, "Vul een geldig telefoonnummer in.")
        self.assertContains(response, "Vul een geldig e-mailadres in.")

    def test_rsvp_deadline_after_event_is_rejected(self):
        uid = self.c.post("/maken/", {"occasion": "verjaardag", "template": "confetti"})["Location"].split("/")[2]
        self.inv = Invitation.objects.get(uid=uid)
        self.post("gegevens", {"name_person_name": "A", "date": future_date(30), "start_time": "14:00",
                               "timezone": "Europe/Amsterdam", "venue_name": "X"})
        response = self.post("aanmelden", {"enabled": "on", "deadline": future_date(60), "max_party_size": "2"})
        self.assertContains(response, "op of vóór de datum")
        response = self.post("aanmelden", {"enabled": "on", "deadline": future_date(10), "max_party_size": "99"})
        self.assertContains(response, "Maximaal 10.")

    def test_bij_een_bruiloft_bestaat_de_aanmelddeadline_niet_meer(self):
        self.post("gegevens", {"name_partner_1": "A", "name_partner_2": "B", "date": future_date(30), "start_time": "14:00",
                               "timezone": "Europe/Amsterdam", "venue_name": "X"})
        page = self.c.get(f"/maken/{self.inv.uid}/aanmelden/").content.decode()
        self.assertNotIn("id_deadline", page)
        response = self.post("aanmelden", {"enabled": "on", "deadline": future_date(60), "max_party_size": "3"})
        self.assertEqual(response.status_code, 302)     # een meegestuurde deadline telt niet mee
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["rsvp"]["deadline"], "")
        self.assertEqual(self.inv.draft_content["rsvp"]["max_party_size"], 3)
        self.assertEqual([i for i in publish_issues(self.inv.draft_content, "bruiloft", first_publication=True) if i.blocking], [])

    def test_at_most_five_fixed_questions(self):
        data = {"enabled": "on", "deadline": future_date(10), "max_party_size": "2"}
        data.update({f"vraag_{key}": "on" for key in ("vervoer", "parkeren", "overnachten", "pendel", "aankomst", "liedje")})
        response = self.post("aanmelden", data)
        self.assertContains(response, "Kies maximaal 5 extra vragen.")

    def test_checkout_rejects_incomplete_invitation_and_unknown_package(self):
        customer = self.make_customer("inc@example.com")
        self.inv.owner = customer
        self.inv.save()
        self.c.force_login(customer)
        # Een leeg ontwerp mag besteld worden (niets is verplicht); een datum in het verleden niet.
        self.inv.refresh_from_db()
        content = dict(self.inv.draft_content, date="2020-01-01", start_time="12:00", venue_name="Oud")
        save_draft(self.inv, expected_rev=None, content=content, user=customer)
        response = self.c.post(f"/maken/{self.inv.uid}/bestellen/", {"actie": "betalen", "package": "essentieel", "terms": "on", "direct_leveren": "on", "online_dienst": "on"})
        self.assertContains(response, "niet klaar om te bestellen")
        self.assertFalse(Order.objects.exists())
        complete = self.make_invitation(owner=customer)
        response = self.c.post(f"/maken/{complete.uid}/bestellen/", {"actie": "betalen", "package": "gratis-alles", "terms": "on", "direct_leveren": "on", "online_dienst": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Order.objects.exists())
        response = self.c.post(f"/maken/{complete.uid}/bestellen/", {"actie": "betalen", "package": "essentieel"})
        self.assertContains(response, "akkoord met de algemene voorwaarden")
        self.assertFalse(Order.objects.exists())
        # Het vinkje noemt de versie van de voorwaarden, zonder het woord "concept".
        page = self.c.get(f"/maken/{complete.uid}/bestellen/").content.decode()
        label = page.split('class="check terms-check"', 1)[1].split("</label>", 1)[0]
        self.assertIn("Versie 29 september 2026", label)
        self.assertNotIn("concept", label.lower())


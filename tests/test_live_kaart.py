"""De live kaart naast de invulstappen: toont wat de klant invult (ook nog niet opgeslagen) en waar de foto's komen."""
from django.test import Client

from invitations.models import Invitation

from .helpers import VaylideTestCase, future_date, jpeg_file


class LivePhoneTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer)
        self.client = Client()
        self.client.force_login(self.customer)
        self.base = f"/maken/{self.inv.uid}"

    def details(self, **extra):
        data = {"rev": self.inv.draft_rev, "name_partner_1": "Sanne", "name_partner_2": "Daan", "date": future_date(150),
                "start_time": "14:00", "end_time": "23:30", "timezone": "Europe/Amsterdam", "venue_name": "De Oranjerie",
                "address": "Laan 1\nUtrecht", "welcome_text": "Welkom!"}
        data.update(extra)
        return data

    def test_form_steps_show_the_phone(self):
        for step in ("gegevens", "programma", "aanmelden", "fotos", "stijl"):
            page = self.client.get(f"{self.base}/{step}/").content.decode()
            self.assertIn("data-live-update=\"" + f"{self.base}/voorbeeld/live/{step}/", page, step)
            self.assertIn(f'src="{self.base}/voorbeeld/live/?deel={step}"', page, step)
            self.assertNotIn("{#", page, step)  # geen commentaar als tekst op de pagina
        self.assertNotIn("data-live-update", self.client.get(f"{self.base}/voorbeeld/").content.decode())

    def test_live_frame_opens_directly_without_banner(self):
        response = self.client.get(f"{self.base}/voorbeeld/live/?deel=fotos")
        self.assertEqual(response["X-Frame-Options"], "SAMEORIGIN")
        html = response.content.decode()
        self.assertIn('data-live="fotos"', html)
        self.assertIn("inv-embed", html)
        self.assertIn("invitations/live.js", html)
        self.assertIn("Anna", html)
        # een onbekend deel valt terug op de hele kaart
        self.assertIn('data-live="kaart"', self.client.get(f"{self.base}/voorbeeld/live/?deel=<b>").content.decode())

    def test_guests_never_get_the_live_script(self):
        html = self.client.get(f"{self.base}/voorbeeld/weergave/").content.decode()
        self.assertNotIn("live.js", html)
        self.assertNotIn("data-live", html)

    def test_typing_updates_the_phone_without_saving(self):
        response = self.client.post(f"{self.base}/voorbeeld/live/gegevens/", self.details(), HTTP_ACCEPT="application/json")
        self.assertTrue(response.json()["ok"])
        url = response.json()["url"]
        self.assertIn("concept=1", url)
        self.assertIn("Sanne", self.client.get(url).content.decode())
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["names"]["partner_1"], "Anna")  # niets opgeslagen
        # zonder ?concept=1 (bij het laden van de pagina) de opgeslagen versie
        self.assertNotIn("Sanne", self.client.get(f"{self.base}/voorbeeld/live/?deel=gegevens").content.decode())

    def test_a_stale_concept_is_ignored_after_saving(self):
        url = self.client.post(f"{self.base}/voorbeeld/live/gegevens/", self.details()).json()["url"]
        self.client.post(f"{self.base}/gegevens/", self.details(actie="opslaan", name_partner_1="Lotte"))
        html = self.client.get(url).content.decode()
        self.assertIn("Lotte", html)
        self.assertNotIn("Sanne", html)

    def test_photos_are_marked_as_hero_and_gallery(self):
        uids = [self.client.post(f"{self.base}/upload/", {"fotos": jpeg_file(name=f"f{i}.jpg")}, HTTP_ACCEPT="application/json").json()["created"][0]["uid"]
                for i in range(2)]
        self.inv.refresh_from_db()
        data = {"rev": self.inv.draft_rev, "hero": uids[0], f"g_{uids[1]}": "on", "music_asset": ""}
        for uid in uids:
            data.update({f"x_{uid}": "50", f"y_{uid}": "50", f"z_{uid}": "100"})
        response = self.client.post(f"{self.base}/voorbeeld/live/fotos/", data)
        self.assertTrue(response.json()["ok"], response.content)
        html = self.client.get(response.json()["url"]).content.decode()
        self.assertIn('data-foto="hoofdfoto"', html)
        self.assertIn('data-foto="galerij"', html)

    def test_photo_step_explains_where_things_go(self):
        page = self.client.get(f"{self.base}/fotos/")
        self.assertContains(page, "Waar komt wat op je kaart?")
        self.assertContains(page, "Hoofdfoto")
        self.assertContains(page, "Fotogalerij")

    def test_other_customers_get_404(self):
        other = Client()
        other.force_login(self.make_customer("ander@example.com"))
        self.assertEqual(other.get(f"{self.base}/voorbeeld/live/?deel=fotos").status_code, 404)
        self.assertEqual(other.post(f"{self.base}/voorbeeld/live/gegevens/", self.details()).status_code, 404)
        self.assertEqual(Invitation.objects.get(pk=self.inv.pk).draft_rev, self.inv.draft_rev)

    def test_unknown_step_is_404_and_get_is_refused(self):
        self.assertEqual(self.client.post(f"{self.base}/voorbeeld/live/bestellen/", {}).status_code, 404)
        self.assertEqual(self.client.get(f"{self.base}/voorbeeld/live/gegevens/").status_code, 405)

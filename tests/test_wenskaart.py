"""Uitnodiging of wenskaart: per kaart te kiezen bij Kerst (in het samenstellen, op de ontwerppagina en in het voorbeeld)."""
from django.test import Client

from invitations.content import card_kind, event_expected, publish_issues
from invitations.demo import demo_content
from invitations.models import Invitation

from .helpers import VaylideTestCase, future_date

KERST = ["aan-tafel", "middernacht", "gloria", "winterlicht", "kerstman", "sneeuwpop"]


class CardKindTests(VaylideTestCase):
    def test_explicit_choice_wins_over_filled_in_details(self):
        content = demo_content("aan-tafel", "kerst")
        self.assertEqual(card_kind(content, "kerst"), "uitnodiging")
        content["soort"] = "wenskaart"
        self.assertEqual(card_kind(content, "kerst"), "wenskaart")
        self.assertFalse(event_expected(content, "kerst"))
        # Andere gelegenheden kennen geen wenskaart.
        self.assertEqual(card_kind({"soort": "wenskaart"}, "bruiloft"), "uitnodiging")

    def test_greeting_card_can_be_published_without_event_even_with_old_details(self):
        content = demo_content("aan-tafel", "kerst")
        content["soort"] = "wenskaart"
        content["date"] = "2020-01-01"  # een oude datum blijft bewaard, maar telt niet mee
        self.assertEqual([i for i in publish_issues(content, "kerst", first_publication=True) if i.blocking], [])

    def test_invitation_needs_date_and_venue(self):
        content = demo_content("aan-tafel", "kerst")
        content.update({"soort": "uitnodiging", "date": "", "start_time": "", "venue_name": ""})
        fields = {i.field for i in publish_issues(content, "kerst", first_publication=True) if i.blocking}
        self.assertTrue({"date", "start_time", "venue_name"} <= fields)


class StudioChoiceTests(VaylideTestCase):
    def start(self, **extra):
        c = Client()
        response = c.post("/maken/", {"occasion": "kerst", "template": "aan-tafel", **extra})
        return c, Invitation.objects.get(uid=response["Location"].split("/")[2])

    def test_choice_is_shown_and_saved(self):
        c, inv = self.start(soort="uitnodiging")
        page = c.get(f"/maken/{inv.uid}/gegevens/")
        self.assertContains(page, "Wat voor kaart wordt het?")
        self.assertContains(page, 'name="soort" value="uitnodiging" checked')
        self.assertContains(page, "data-alleen-uitnodiging")
        # Wenskaart: datum en locatie mogen leeg; wat er al stond blijft bewaard.
        response = c.post(f"/maken/{inv.uid}/gegevens/", {
            "rev": inv.draft_rev, "actie": "volgende", "soort": "wenskaart", "name_family": "Familie Jansen",
            "date": future_date(60), "timezone": "Europe/Amsterdam",
        })
        self.assertRedirects(response, f"/maken/{inv.uid}/programma/", fetch_redirect_response=False)
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["soort"], "wenskaart")
        self.assertEqual(inv.draft_content["date"], future_date(60))
        self.assertContains(c.get(f"/maken/{inv.uid}/programma/"), "Je maakt een wenskaart")
        self.assertRedirects(c.get(f"/maken/{inv.uid}/aanmelden/"), f"/maken/{inv.uid}/fotos/", fetch_redirect_response=False)
        preview = c.get(f"/maken/{inv.uid}/voorbeeld/weergave/").content.decode()
        self.assertIn("Een kerstgroet voor jou", preview)
        self.assertNotIn('class="at-plaats"', preview)  # geen datumkaartje
        self.assertNotIn('id="aanmelden"', preview)

    def test_invitation_asks_for_date_time_and_venue(self):
        c, inv = self.start()
        response = c.post(f"/maken/{inv.uid}/gegevens/", {
            "rev": inv.draft_rev, "actie": "volgende", "soort": "uitnodiging", "name_family": "Familie Jansen", "timezone": "Europe/Amsterdam",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Vul de datum in.")
        self.assertContains(response, "Vul de naam van de locatie in.")

    def test_start_keeps_the_choice_from_the_design_page(self):
        response = Client().get("/maken/", {"ontwerp": "aan-tafel", "gelegenheid": "kerst", "soort": "wenskaart"})
        self.assertContains(response, 'name="soort" value="wenskaart"')
        _, inv = self.start(soort="wenskaart")
        self.assertEqual(inv.draft_content["soort"], "wenskaart")
        _, inv = self.start(soort="iets-anders")
        self.assertEqual(inv.draft_content["soort"], "")


class DesignPageAndDemoTests(VaylideTestCase):
    def test_toggle_on_christmas_designs_only(self):
        for slug in KERST:
            html = Client().get(f"/ontwerpen/{slug}/", {"soort": "wenskaart"}).content.decode()
            self.assertIn('data-soort="wenskaart" aria-current="true"', html, slug)
            self.assertRegex(html, r'<iframe src="[^"]*soort=wenskaart', slug)
            self.assertRegex(html, r'href="/maken/[^"]*soort=wenskaart[^"]*" data-kleur-link', slug)
        self.assertNotContains(Client().get("/ontwerpen/liefde-op-papier/"), "data-soort-link")

    def test_demo_as_greeting_card(self):
        for slug in KERST:
            html = Client().get(f"/voorbeeld/{slug}/", {"soort": "wenskaart"}).content.decode()
            self.assertNotIn('id="aanmelden"', html, slug)
            self.assertNotIn("Bij ons thuis (voorbeeld)", html, slug)
            self.assertIn("gelukkig nieuw jaar", html.replace("prachtig nieuw jaar", "gelukkig nieuw jaar"), slug)
        at = Client().get("/voorbeeld/aan-tafel/", {"soort": "wenskaart"}).content.decode()
        self.assertIn("Fijne feestdagen</span>", at)
        self.assertIn("Kerstgroet</p>", at)
        self.assertIn("Voorbeeldwenskaart", at)
        self.assertIn("soort=wenskaart\">Maak jouw wenskaart", at)
        mn = Client().get("/voorbeeld/middernacht/", {"soort": "wenskaart"}).content.decode()
        self.assertIn("Een kerstgroet voor jou", mn)
        self.assertNotIn("toegangskaart", mn)
        # Als uitnodiging blijft alles zoals het was.
        self.assertContains(Client().get("/voorbeeld/aan-tafel/"), "Een plaats aan tafel")


class GreetingOnlyTests(VaylideTestCase):
    """Een wenskaart is alleen een kerstwens: geen dresscode, 'Goed om te weten' of 'Vragen'."""

    def filled(self, soort):
        content = demo_content("aan-tafel", "kerst")
        content["soort"] = soort
        content["dresscode"] = {"text": "Iets roods", "colors": ["#AA0000"]}
        content["practical"] = [{"title": "Parkeren", "text": "Voor de deur."}]
        content["contact"] = {"name": "Sanne", "phone": "", "email": "sanne@example.com", "note": "Vragen? Laat het weten."}
        for key in ("dresscode", "practical", "contact"):
            content["sections"][key] = True
        return content

    def view(self, soort):
        from catalog.models import Template
        from invitations.render import RenderOptions, build_view
        version = Template.objects.get(slug="aan-tafel").current_version
        return build_view(occasion="kerst", content=self.filled(soort), overrides={}, template_version=version,
                          options=RenderOptions(mode="demo"))

    def test_greeting_card_hides_dresscode_practical_and_contact(self):
        show = self.view("wenskaart")["show"]
        for key in ("dresscode", "practical", "contact", "program", "rsvp", "location"):
            self.assertFalse(show[key], key)

    def test_invitation_keeps_them(self):
        show = self.view("uitnodiging")["show"]
        for key in ("dresscode", "practical", "contact", "location"):
            self.assertTrue(show[key], key)

    def test_demo_greeting_card_has_no_questions_or_practical(self):
        for slug in KERST:
            html = Client().get(f"/voorbeeld/{slug}/", {"soort": "wenskaart"}).content.decode()
            self.assertNotIn("Vragen?", html, slug)
            self.assertNotIn("Goed om te weten", html, slug)
            self.assertNotIn("sanne@example.com", html, slug)
        self.assertContains(Client().get("/voorbeeld/aan-tafel/"), "Vragen?")

    def test_studio_steps_for_a_greeting_card(self):
        owner = self.make_customer()
        inv = self.make_invitation(owner=owner, template="aan-tafel", occasion="kerst")
        content = self.filled("wenskaart")
        inv.draft_content = content
        inv.save()
        c = Client()
        c.force_login(owner)
        page = c.get(f"/maken/{inv.uid}/programma/").content.decode()
        self.assertIn("Je afsluitende wens", page)
        self.assertNotIn("blok-dresscode", page)
        self.assertNotIn(">Aanmelden<", page.split("studio-progress")[1] if "studio-progress" in page else page)
        self.assertIn("Afsluiting", page)
        # Opslaan bewaart de wens en laat programma, dresscode en contact ongemoeid (voor als het toch een uitnodiging wordt).
        inv.refresh_from_db()
        response = c.post(f"/maken/{inv.uid}/programma/", {"rev": inv.draft_rev, "actie": "volgende", "closing_text": "Fijne feestdagen!"})
        self.assertRedirects(response, f"/maken/{inv.uid}/fotos/", fetch_redirect_response=False)
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["closing_text"], "Fijne feestdagen!")
        self.assertEqual(inv.draft_content["dresscode"]["text"], "Iets roods")
        self.assertEqual(inv.draft_content["contact"]["name"], "Sanne")
        self.assertTrue(inv.draft_content["program"])
        # In de stap Stijl verdwijnen de schakelaars voor wat een wenskaart niet toont; hun stand blijft bewaard.
        stijl = c.get(f"/maken/{inv.uid}/stijl/").content.decode()
        for key in ("program", "dresscode", "practical", "contact"):
            self.assertNotIn(f'name="s_{key}"', stijl, key)
        self.assertIn('name="s_closing"', stijl)
        inv.refresh_from_db()
        palette = inv.draft_content["style"]["palette"]
        c.post(f"/maken/{inv.uid}/stijl/", {"rev": inv.draft_rev, "actie": "opslaan", "palette": palette, "opening": "on", "s_closing": "on"})
        inv.refresh_from_db()
        self.assertTrue(inv.draft_content["sections"]["dresscode"])
        self.assertTrue(inv.draft_content["sections"]["contact"])

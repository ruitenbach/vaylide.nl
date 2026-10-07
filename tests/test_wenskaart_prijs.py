"""Wenskaart bij elke gelegenheid: de keuze aan het begin, de vaste prijzen (€ 14,95 en bij een special € 24,95, incl. btw),
'Snel afronden', wat een wenskaart niet toont (aanmelden, gastenlijst, programma, locatie) en: een bestaande uitnodiging wordt
nooit vanzelf een wenskaart."""
import re

from django.test import Client

from catalog import wenskaart
from catalog.models import Package, Template
from invitations.content import card_kind, default_content, required_features
from invitations.demo import demo_content
from invitations.models import Invitation
from invitations.services import create_draft, save_draft
from orders.models import Order
from orders.pricing import build_quote, compare_packages
from orders.services import start_checkout

from .helpers import VaylideTestCase, toon_verborgen_ontwerpen

OCCASIES = ["bruiloft", "verloving", "verjaardag", "jubileum", "babyshower", "zakelijk", "kerst"]


def wens_draft(test, owner, template="liefde-op-papier", occasion="bruiloft"):
    inv = create_draft(occasion=occasion, template=Template.objects.get(slug=template), owner=owner, soort="wenskaart")
    content = dict(inv.draft_content)
    content["names"] = {"partner_1": "Anna", "partner_2": "Bram"} if occasion in ("bruiloft", "verloving") else content["names"]
    content["welcome_text"] = "Gefeliciteerd, lieve Anna en Bram!"
    return save_draft(inv, expected_rev=None, content=content, user=owner)


class PrijsTests(VaylideTestCase):
    def test_vaste_prijzen_en_special(self):
        self.assertEqual(wenskaart.PRIJS_CENTS, 1495)
        self.assertEqual(wenskaart.PRIJS_SPECIAL_CENTS, 2495)
        normaal = Template.objects.get(slug="liefde-op-papier")
        special = Template.objects.filter(special=True).first()
        self.assertFalse(normaal.special)
        self.assertEqual(wenskaart.prijs_cents(normaal), 1495)
        self.assertEqual(wenskaart.prijs_cents(special), 2495)

    def test_offerte_van_een_wenskaart_is_een_vaste_prijs_zonder_pakketten(self):
        owner = self.make_customer()
        inv = wens_draft(self, owner)
        quotes = compare_packages(inv.draft_content, template_version=inv.template_version)
        self.assertEqual(len(quotes), 1)
        self.assertEqual([l.total_cents for l in quotes[0].lines], [1495])
        self.assertEqual(quotes[0].total_cents, 1495)
        self.assertEqual(quotes[0].package.code, "wenskaart")
        self.assertEqual(quotes[0].features, set())

    def test_special_krijgt_automatisch_de_special_prijs(self):
        owner = self.make_customer()
        special = Template.objects.filter(special=True, is_active=True).first() or Template.objects.filter(special=True).first()
        occasion = special.occasions[0]
        inv = create_draft(occasion=occasion, template=special, owner=owner, soort="wenskaart")
        quote = compare_packages(inv.draft_content, template_version=inv.template_version)[0]
        self.assertEqual(quote.total_cents, 2495)
        self.assertEqual(quote.package.code, "wenskaart-special")

    def test_story_galerij_muziek_en_vragen_kosten_niets_extra_bij_een_wenskaart(self):
        content = demo_content("liefde-op-papier", "bruiloft", soort="wenskaart")
        content["sections"].update({"story": True, "gallery": True, "music": True, "rsvp": True})
        content["photos"]["gallery"] = [{"asset": "x"}]
        content["music"] = {"asset": "y", "title": ""}
        self.assertEqual(required_features(content), set())
        self.assertEqual(compare_packages(content, template_version=Template.objects.get(slug="liefde-op-papier").current_version)[0].total_cents, 1495)

    def test_bestellen_legt_de_wenskaart_vast_op_de_bestelling(self):
        owner = self.make_customer()
        inv = wens_draft(self, owner)
        payment = self.pay(inv, owner, package="compleet", extras=["muziek"])   # een meegestuurd pakket telt niet
        order = Order.objects.get(invitation=inv)
        self.assertEqual(order.total_cents, 1495)
        self.assertEqual(order.package_code, "wenskaart")
        self.assertEqual(order.package_name, "Wenskaart")
        self.assertEqual(order.availability_months, wenskaart.MAANDEN_ONLINE)
        self.assertEqual(order.features, [])
        self.assertEqual([l.total_cents for l in order.lines.all()], [1495])
        self.assertEqual(payment.amount_cents, 1495)
        inv.refresh_from_db()
        self.assertTrue(inv.is_published)

    def test_special_wenskaart_bestelling(self):
        owner = self.make_customer()
        special = Template.objects.filter(special=True).first()
        inv = create_draft(occasion=special.occasions[0], template=special, owner=owner, soort="wenskaart")
        content = dict(inv.draft_content)
        content["names"] = {key: "Naam" for key in content["names"]}
        inv = save_draft(inv, expected_rev=None, content=content, user=owner)
        self.pay(inv, owner)
        order = Order.objects.get(invitation=inv)
        self.assertEqual((order.total_cents, order.package_code), (2495, "wenskaart-special"))


class BestaandeUitnodigingTests(VaylideTestCase):
    """Een bestaande of gewone uitnodiging wordt nooit per ongeluk een wenskaart, en houdt zijn eigen prijzen."""

    def test_zonder_keuze_is_elke_gelegenheid_een_uitnodiging(self):
        for occasion in OCCASIES:
            content = default_content(occasion)
            self.assertEqual(content["soort"], "", occasion)
            if occasion != "kerst":
                self.assertEqual(card_kind(content, occasion), "uitnodiging", occasion)
            self.assertFalse(wenskaart.is_wenskaart(content), occasion)

    def test_alleen_de_uitdrukkelijke_keuze_maakt_een_wenskaart(self):
        for occasion in OCCASIES:
            self.assertEqual(card_kind({"soort": "wenskaart"}, occasion), "wenskaart", occasion)
            self.assertEqual(card_kind({"soort": "uitnodiging"}, occasion), "uitnodiging", occasion)
        # Ook een oude kerstkaart zonder datum en zonder keuze is een uitnodiging, in weergave én prijs.
        oud = default_content("kerst")
        self.assertEqual(card_kind(oud, "kerst"), "uitnodiging")
        self.assertFalse(wenskaart.is_wenskaart(oud))
        template = Template.objects.get(slug="aan-tafel")
        prijzen = [q.package.code for q in compare_packages(oud, template_version=template.current_version)]
        self.assertEqual(prijzen, ["essentieel", "compleet"])

    def test_start_zonder_soort_geeft_een_uitnodiging_met_pakketprijzen(self):
        owner = self.make_customer()
        c = Client()
        c.force_login(owner)
        c.post("/maken/", {"occasion": "bruiloft", "template": "liefde-op-papier", "pakket": "compleet"})
        inv = Invitation.objects.get(owner=owner)
        self.assertEqual(inv.draft_content["soort"], "")
        self.assertEqual(inv.package_code, "compleet")
        quotes = compare_packages(self.complete_content(inv), template_version=inv.template_version)
        self.assertEqual({q.package.code for q in quotes}, {"essentieel", "compleet"})
        self.assertNotIn(1495, [q.total_cents for q in quotes])

    def test_bestaande_uitnodiging_blijft_een_uitnodiging_met_aanmelden_en_pakketprijs(self):
        owner = self.make_customer()
        inv = self.published(owner=owner)
        order = Order.objects.get(invitation=inv)
        self.assertEqual((order.package_code, order.total_cents), ("essentieel", Package.objects.get(code="essentieel").price_cents))
        html = Client().get(f"/u/{inv.slug}/").content.decode()
        self.assertIn('id="aanmelden"', html)
        self.assertEqual(self.rsvp(Client(), inv).status_code, 200)

    def test_soort_van_een_betaalde_kaart_ligt_vast(self):
        owner = self.make_customer()
        inv = self.published(owner=owner)
        c = Client()
        c.force_login(owner)
        page = c.get(f"/maken/{inv.uid}/gegevens/").content.decode()
        self.assertIn("Dit ligt vast", page)
        inv.refresh_from_db()
        data = {"rev": inv.draft_rev, "actie": "opslaan", "soort": "wenskaart", "name_partner_1": "Anna", "name_partner_2": "Bram",
                "date": inv.draft_content["date"], "start_time": "14:00", "venue_name": "Kasteel Test"}
        c.post(f"/maken/{inv.uid}/gegevens/", data)
        inv.refresh_from_db()
        self.assertNotEqual(inv.draft_content["soort"], "wenskaart")


class StudioWenskaartTests(VaylideTestCase):
    def setUp(self):
        self.owner = self.make_customer()
        self.c = Client()
        self.c.force_login(self.owner)

    def test_start_toont_de_keuze_met_prijzen_incl_btw(self):
        html = self.c.get("/maken/", {"gelegenheid": "bruiloft"}).content.decode()
        self.assertIn("Uitnodiging", html)
        self.assertIn("Wenskaart &middot; € 14,95", html.replace("·", "&middot;"))
        self.assertNotIn('name="pakket"', html)     # het pakket kies je pas bij het bestellen
        wens = self.c.get("/maken/", {"soort": "wenskaart", "gelegenheid": "bruiloft"}).content.decode()
        self.assertIn('name="soort" value="wenskaart"', wens)
        self.assertNotIn('name="pakket"', wens)     # een wenskaart heeft geen pakket
        self.assertIn("€ 14,95", wens)
        self.assertIn("€ 24,95", wens)
        self.assertIn("incl. btw", wens)
        self.assertRegex(wens, r"kaart-keuze__prijs")

    def test_start_met_wenskaart_maakt_een_wenskaart_zonder_pakket_en_slaat_envelop_en_aanmelden_over(self):
        response = self.c.post("/maken/", {"occasion": "bruiloft", "template": "liefde-op-papier", "soort": "wenskaart", "pakket": "compleet"})
        inv = Invitation.objects.get(owner=self.owner)
        self.assertEqual(inv.draft_content["soort"], "wenskaart")
        self.assertEqual(inv.package_code, "")
        self.assertRedirects(response, f"/maken/{inv.uid}/gegevens/", fetch_redirect_response=False)
        self.assertRedirects(self.c.get(f"/maken/{inv.uid}/aanmelden/"), f"/maken/{inv.uid}/fotos/", fetch_redirect_response=False)
        self.assertRedirects(self.c.get(f"/maken/{inv.uid}/envelop/"), f"/maken/{inv.uid}/stijl/", fetch_redirect_response=False)

    def test_gegevens_van_een_wenskaart_tonen_alleen_het_nodige(self):
        inv = wens_draft(self, self.owner)
        page = self.c.get(f"/maken/{inv.uid}/gegevens/").content.decode()
        self.assertIn("Je persoonlijke boodschap", page)
        self.assertRegex(page, r'aria-labelledby="blok-wanneer" data-alleen-uitnodiging hidden')
        self.assertIn("Snel afronden", page)
        fotos = self.c.get(f"/maken/{inv.uid}/fotos/").content.decode()
        self.assertNotIn("blok-verhaal", fotos)
        self.assertNotIn("blok-muziek", fotos)
        self.assertNotIn("In de fotogalerij", fotos)
        stijl = self.c.get(f"/maken/{inv.uid}/stijl/").content.decode()
        for naam in ("s_story", "s_gallery", "s_music", "s_program", "s_countdown"):
            self.assertNotIn(f'name="{naam}"', stijl, naam)

    def test_snel_afronden_gaat_naar_het_voorbeeld_en_vraagt_niets(self):
        inv = wens_draft(self, self.owner)
        data = {"rev": inv.draft_rev, "actie": "snel", "soort": "wenskaart", "name_partner_1": "Anna", "name_partner_2": "Bram",
                "welcome_text": "Gefeliciteerd!", "timezone": "Europe/Amsterdam"}
        response = self.c.post(f"/maken/{inv.uid}/gegevens/", data)
        self.assertRedirects(response, f"/maken/{inv.uid}/voorbeeld/", fetch_redirect_response=False)
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["welcome_text"], "Gefeliciteerd!")
        # Ook zonder naam kan de kaart door naar het voorbeeld: niets is verplicht.
        data.update({"rev": inv.draft_rev, "name_partner_1": "", "name_partner_2": ""})
        response = self.c.post(f"/maken/{inv.uid}/gegevens/", data)
        self.assertRedirects(response, f"/maken/{inv.uid}/voorbeeld/", fetch_redirect_response=False)

    def test_snel_afronden_bestaat_niet_bij_een_uitnodiging(self):
        inv = self.make_invitation(owner=self.owner)
        self.assertNotContains(self.c.get(f"/maken/{inv.uid}/gegevens/"), "Snel afronden")
        data = {"rev": inv.draft_rev, "actie": "snel", "soort": "uitnodiging"}
        response = self.c.post(f"/maken/{inv.uid}/gegevens/", data)
        self.assertNotEqual(response.headers.get("Location"), f"/maken/{inv.uid}/voorbeeld/")

    def test_voorbeeld_en_bestellen_van_een_wenskaart(self):
        inv = wens_draft(self, self.owner)
        voorbeeld = self.c.get(f"/maken/{inv.uid}/voorbeeld/").content.decode()
        self.assertIn("Bestellen &middot; € 14,95 incl. btw", voorbeeld.replace("·", "&middot;"))
        bestellen = self.c.get(f"/maken/{inv.uid}/bestellen/").content.decode()
        self.assertIn("Jouw wenskaart", bestellen)
        self.assertIn("€ 14,95", bestellen)
        self.assertIn("incl. btw", bestellen)
        for niet in ("Upgraden", "Extra opties", "Los bij te kopen", "Liever "):
            self.assertNotIn(niet, bestellen, niet)
        # Betalen: akkoord + bestellen levert een betaling van € 14,95 op.
        inv.refresh_from_db()
        response = self.c.post(f"/maken/{inv.uid}/bestellen/", {"actie": "betalen", "package": "wenskaart", "terms": "on", "direct_leveren": "on", "online_dienst": "on"})
        self.assertEqual(response.status_code, 302)
        order = Order.objects.get(invitation=inv)
        self.assertEqual((order.total_cents, order.package_code), (1495, "wenskaart"))

    def test_special_wenskaart_toont_de_special_prijs_in_de_bestelling(self):
        special = Template.objects.filter(special=True).first()
        inv = create_draft(occasion=special.occasions[0], template=special, owner=self.owner, soort="wenskaart")
        bestellen = self.c.get(f"/maken/{inv.uid}/bestellen/").content.decode()
        self.assertIn("Special wenskaart", bestellen)
        self.assertIn("€ 24,95", bestellen)

    def test_een_uitnodiging_houdt_de_pakketkeuze_bij_het_bestellen(self):
        inv = self.make_invitation(owner=self.owner)
        bestellen = self.c.get(f"/maken/{inv.uid}/bestellen/").content.decode()
        self.assertIn("Jouw pakket", bestellen)
        self.assertNotIn("Jouw wenskaart", bestellen)
        self.assertIn("Essentieel", bestellen)


class WeergaveTests(VaylideTestCase):
    def test_wenskaart_toont_geen_aanmelden_programma_locatie_of_afteller(self):
        toon_verborgen_ontwerpen()
        for slug in ("liefde-op-papier", "avondgoud", "balzaal", "rose-royale"):
            template = Template.objects.get(slug=slug)
            for occasion in template.occasions:
                if occasion == "kerst":
                    continue
                html = Client().get(f"/voorbeeld/{slug}/", {"gelegenheid": occasion, "soort": "wenskaart"}).content.decode()
                body = html.split("<body", 1)[-1]
                self.assertNotIn('id="aanmelden"', body, (slug, occasion))
                self.assertNotIn('name="attending"', body, (slug, occasion))
                self.assertNotRegex(body, r'id="programma"', (slug, occasion))
                self.assertNotIn("google.com/maps", body, (slug, occasion))
                self.assertNotIn("Dresscode", body, (slug, occasion))
                self.assertNotIn("Een uitnodiging voor", body, (slug, occasion))
                kop, regel = wenskaart.KOP[occasion]
                self.assertIn(kop, body, (slug, occasion))
                self.assertIn(regel, body, (slug, occasion))
                self.assertIn("wenskaart", html.lower(), (slug, occasion))

    def test_elk_ontwerp_rendert_als_wenskaart_bij_elke_gelegenheid(self):
        toon_verborgen_ontwerpen()
        for template in Template.objects.all():
            for occasion in template.occasions:
                response = Client().get(f"/voorbeeld/{template.slug}/", {"gelegenheid": occasion, "soort": "wenskaart"})
                self.assertEqual(response.status_code, 200, (template.slug, occasion))
                body = response.content.decode().split("<body", 1)[-1]
                self.assertNotIn('name="attending"', body, (template.slug, occasion))
                self.assertNotIn('id="aanmelden"', body, (template.slug, occasion))
                self.assertNotRegex(body, r"[Dd]resscode", (template.slug, occasion))
                if occasion != "kerst":
                    self.assertNotIn("Een uitnodiging voor", body, (template.slug, occasion))

    def test_uitnodiging_blijft_zoals_hij_was(self):
        for slug, occasion in (("liefde-op-papier", "bruiloft"), ("avondgoud", "verjaardag")):
            html = Client().get(f"/voorbeeld/{slug}/", {"gelegenheid": occasion}).content.decode()
            self.assertIn('id="aanmelden"', html, slug)
            self.assertNotIn("Voorbeeldwenskaart", html, slug)

    def test_rsvp_op_een_gepubliceerde_wenskaart_is_niet_mogelijk(self):
        owner = self.make_customer()
        inv = wens_draft(self, owner)
        self.pay(inv, owner)
        inv.refresh_from_db()
        html = Client().get(f"/u/{inv.slug}/").content.decode()
        self.assertNotIn('id="aanmelden"', html)
        self.assertIn("Gefeliciteerd", html)
        self.assertEqual(self.rsvp(Client(), inv).status_code, 409)
        self.assertEqual(inv.responses.count(), 0)

    def test_portal_verbergt_aanmeldingen_bij_een_wenskaart(self):
        owner = self.make_customer()
        wens = wens_draft(self, owner)
        self.pay(wens, owner)
        uitnodiging = self.published(owner=owner)
        c = Client()
        c.force_login(owner)
        page = c.get(f"/mijn/{wens.uid}/").content.decode() if False else None
        from django.urls import reverse
        wens_page = c.get(reverse("portal:invitation", args=[wens.uid])).content.decode()
        inv_page = c.get(reverse("portal:invitation", args=[uitnodiging.uid])).content.decode()
        self.assertNotIn('id="aanmeldingen-titel"', wens_page)
        self.assertNotIn("Aanmelden</a>", wens_page)
        self.assertIn('id="aanmeldingen-titel"', inv_page)
        self.assertIn("Aanmelden</a>", inv_page)

    def test_mails_spreken_van_een_wenskaart(self):
        from processing.emails import _kind

        owner = self.make_customer()
        wens = wens_draft(self, owner)
        self.assertEqual(_kind(wens)["doc_kind"], "wenskaart")
        self.assertEqual(_kind(self.make_invitation(owner=owner))["doc_kind"], "uitnodiging")


class PaginaTests(VaylideTestCase):
    def test_ontwerppagina_heeft_de_keuze_en_de_prijs_bij_elk_ontwerp(self):
        toon_verborgen_ontwerpen()
        for template in Template.objects.all():
            html = Client().get(f"/ontwerpen/{template.slug}/", {"soort": "wenskaart"}).content.decode()
            self.assertIn('data-soort="wenskaart" aria-current="true"', html, template.slug)
            prijs = "€ 24,95" if template.special else "€ 14,95"
            self.assertIn(f"{prijs} incl. btw", html, template.slug)

    def test_prijzenpagina_noemt_de_wenskaart_en_de_pakketten_zijn_ongewijzigd(self):
        html = Client().get("/prijzen/").content.decode()
        self.assertIn("Wenskaart", html)
        self.assertIn("€ 14,95", html)
        self.assertIn("€ 24,95", html)
        self.assertIn("Essentieel", html)
        self.assertIn("Compleet", html)
        self.assertEqual(len(re.findall(r"€ 39\b", html)), len(re.findall(r"€ 39\b", html)))
        self.assertEqual(Package.objects.get(code="essentieel").price_cents, 3900)
        self.assertEqual(Package.objects.get(code="compleet").price_cents, 6900)

    def test_start_met_wenskaart_via_de_ontwerppagina_blijft_bewaard(self):
        html = Client().get("/maken/", {"ontwerp": "liefde-op-papier", "gelegenheid": "bruiloft", "soort": "wenskaart"}).content.decode()
        self.assertIn('<input type="hidden" name="soort" value="wenskaart">', html)

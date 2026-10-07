"""Regressie: een kaart is alleen een wenskaart bij een uitdrukkelijk gekozen en opgeslagen soort = "wenskaart".

Geen datum, geen locatie, de gelegenheid Kerst of ontbrekende eventgegevens maken van een kaart nooit een wenskaart. Bestaande kaarten
zonder `soort` blijven volledig uitnodiging: in weergave, formulieren, prijs, aanmelden en mails."""
import inspect

from django.test import Client

from catalog import wenskaart
from catalog.models import Package, Template
from invitations import content as inhoud
from invitations.content import card_kind, default_content, event_expected, normalize_content, publish_issues
from invitations.models import Invitation
from invitations.render import RenderOptions, build_view
from invitations.services import create_draft, save_draft
from orders.models import Order
from orders.pricing import compare_packages

from .helpers import VaylideTestCase, future_date


def kerst_zonder_datum(owner, template="winterlicht", **extra):
    """Een kerstkaart zoals die vroeger werd gemaakt: geen datum, geen locatie en geen `soort`."""
    inv = create_draft(occasion="kerst", template=Template.objects.get(slug=template), owner=owner)
    content = dict(inv.draft_content)
    content["names"] = {"family": "Familie Jansen", "members": "Eva, Tom en Noor"}
    content["welcome_text"] = "Lieve allemaal, fijne feestdagen!"
    content.update(extra)
    inv = save_draft(inv, expected_rev=None, content=content, user=owner)
    assert "soort" not in inv.draft_content or inv.draft_content["soort"] == ""
    return inv


class GeenAutomatischeDetectieTests(VaylideTestCase):
    def test_er_bestaat_geen_afleiding_meer_uit_eventgegevens(self):
        self.assertFalse(hasattr(inhoud, "has_event_details"))
        bron = inspect.getsource(card_kind)
        for woord in ("has_event", "date", "venue", "address", "event_optional"):
            self.assertNotIn(woord, bron, woord)

    def test_card_kind_alleen_op_de_expliciete_keuze(self):
        for occasion in ("bruiloft", "verloving", "verjaardag", "jubileum", "babyshower", "zakelijk", "kerst"):
            leeg = default_content(occasion)
            self.assertEqual(card_kind(leeg, occasion), "uitnodiging", occasion)             # niets ingevuld
            self.assertEqual(card_kind({**leeg, "date": future_date(30), "venue_name": "X"}, occasion), "uitnodiging", occasion)
            self.assertEqual(card_kind({k: v for k, v in leeg.items() if k != "soort"}, occasion), "uitnodiging", occasion)   # oud concept
            self.assertEqual(card_kind({**leeg, "soort": "uitnodiging"}, occasion), "uitnodiging", occasion)
            self.assertEqual(card_kind({**leeg, "soort": "onzin"}, occasion), "uitnodiging", occasion)
            self.assertEqual(card_kind({**leeg, "soort": "wenskaart"}, occasion), "wenskaart", occasion)
            self.assertEqual(card_kind({**leeg, "soort": "wenskaart", "date": future_date(30)}, occasion), "wenskaart", occasion)

    def test_normalize_zet_nooit_een_soort(self):
        for occasion in ("kerst", "bruiloft"):
            oud = default_content(occasion)
            del oud["soort"]
            self.assertNotEqual(normalize_content(oud, occasion).get("soort"), "wenskaart", occasion)


class OudeKerstkaartTests(VaylideTestCase):
    """1. Een oude kerstkaart zonder datum en zonder `soort` is een uitnodiging."""

    def test_weergave_is_een_uitnodiging(self):
        owner = self.make_customer()
        inv = kerst_zonder_datum(owner)
        content = normalize_content(inv.draft_content, "kerst")
        self.assertEqual(card_kind(content, "kerst"), "uitnodiging")
        self.assertTrue(event_expected(content, "kerst"))
        view = build_view(occasion="kerst", content=content, overrides={}, template_version=inv.template_version, options=RenderOptions(mode="preview"))
        self.assertEqual(view["card_kind"], "uitnodiging")
        self.assertTrue(view["has_event"])
        self.assertEqual(view["doc_kind"], "kerstkaart")
        self.assertNotIn("wenskaart", view["page_title"])

    def test_prijs_is_een_pakketprijs_en_geen_wenskaartprijs(self):
        owner = self.make_customer()
        inv = kerst_zonder_datum(owner)
        quotes = compare_packages(inv.draft_content, template_version=inv.template_version)
        self.assertEqual([q.package.code for q in quotes], ["essentieel", "compleet"])
        self.assertNotIn(wenskaart.PRIJS_CENTS, [q.total_cents for q in quotes])

    def test_studio_behandelt_hem_als_uitnodiging(self):
        owner = self.make_customer()
        inv = kerst_zonder_datum(owner)
        c = Client()
        c.force_login(owner)
        gegevens = c.get(f"/maken/{inv.uid}/gegevens/").content.decode()
        self.assertNotIn('name="soort" value="wenskaart" checked', gegevens)
        self.assertNotIn("Snel afronden", gegevens)
        self.assertNotIn("aria-labelledby=\"blok-wanneer\" data-alleen-uitnodiging hidden", gegevens)
        self.assertEqual(c.get(f"/maken/{inv.uid}/aanmelden/").status_code, 200)                  # Aanmelden valt niet weg
        self.assertEqual(c.get(f"/maken/{inv.uid}/envelop/").status_code in (200, 302), True)
        # Datum, begintijd en locatie zijn niet verplicht, maar leeg laten maakt er ook geen wenskaart van.
        response = c.post(f"/maken/{inv.uid}/gegevens/", {
            "rev": inv.draft_rev, "actie": "volgende", "name_family": "Familie Jansen", "timezone": "Europe/Amsterdam"})
        self.assertEqual(response.status_code, 302)
        inv.refresh_from_db()
        self.assertNotEqual(inv.draft_content.get("soort"), "wenskaart")

    def test_opslaan_zonder_keuze_maakt_er_geen_wenskaart_van(self):
        owner = self.make_customer()
        inv = kerst_zonder_datum(owner)
        c = Client()
        c.force_login(owner)
        c.post(f"/maken/{inv.uid}/gegevens/", {
            "rev": inv.draft_rev, "actie": "opslaan", "name_family": "Familie Jansen", "timezone": "Europe/Amsterdam"})
        inv.refresh_from_db()
        self.assertNotEqual(inv.draft_content.get("soort"), "wenskaart")

    def test_publicatie_geeft_tips_voor_datum_en_locatie(self):
        owner = self.make_customer()
        inv = kerst_zonder_datum(owner)
        issues = publish_issues(inv.draft_content, "kerst", first_publication=True)
        self.assertTrue({"date", "start_time", "venue_name"} <= {i.field for i in issues})
        self.assertFalse(any(i.blocking for i in issues))

    def test_voorbeeld_en_openbaar_tonen_aanmelden(self):
        owner = self.make_customer()
        inv = kerst_zonder_datum(owner, date=future_date(60), start_time="17:00", venue_name="Bij ons thuis")
        c = Client()
        c.force_login(owner)
        frame = c.get(f"/maken/{inv.uid}/voorbeeld/weergave/").content.decode()
        self.assertNotIn("Voorbeeldwenskaart", frame)
        self.assertNotIn("Een wenskaart voor", frame)


class NieuweKerstWenskaartTests(VaylideTestCase):
    """2. Een nieuwe kerstkaart met soort = wenskaart: € 14,95, bij een special € 24,95."""

    def test_normaal_en_special_prijs(self):
        owner = self.make_customer()
        normaal = create_draft(occasion="kerst", template=Template.objects.get(slug="winterlicht"), owner=owner, soort="wenskaart")
        self.assertEqual(normaal.draft_content["soort"], "wenskaart")
        quotes = compare_packages(normaal.draft_content, template_version=normaal.template_version)
        self.assertEqual([(q.package.code, q.total_cents) for q in quotes], [("wenskaart", 1495)])
        speciale = list(Template.objects.filter(special=True))
        special = next((t for t in speciale if "kerst" in t.occasions), speciale[0])
        sp = create_draft(occasion=special.occasions[0], template=special, owner=owner, soort="wenskaart")
        quotes = compare_packages(sp.draft_content, template_version=sp.template_version)
        self.assertEqual([(q.package.code, q.total_cents) for q in quotes], [("wenskaart-special", 2495)])

    def test_weergave_en_bestelling(self):
        owner = self.make_customer()
        inv = create_draft(occasion="kerst", template=Template.objects.get(slug="winterlicht"), owner=owner, soort="wenskaart")
        content = dict(inv.draft_content)
        content["names"] = {"family": "Familie Jansen", "members": ""}
        inv = save_draft(inv, expected_rev=None, content=content, user=owner)
        view = build_view(occasion="kerst", content=normalize_content(inv.draft_content, "kerst"), overrides={},
                          template_version=inv.template_version, options=RenderOptions(mode="preview"))
        self.assertEqual(view["card_kind"], "wenskaart")
        self.assertFalse(view["has_event"])
        self.assertFalse(view["show"]["rsvp"])
        self.pay(inv, owner)
        order = Order.objects.get(invitation=inv)
        self.assertEqual((order.package_code, order.total_cents), ("wenskaart", 1495))


class BestaandeBetaaldeUitnodigingTests(VaylideTestCase):
    """3. Een bestaande betaalde uitnodiging houdt pakketprijs en RSVP."""

    def test_pakketprijs_en_rsvp_blijven_intact(self):
        owner = self.make_customer()
        inv = self.published(owner=owner)
        order = Order.objects.get(invitation=inv)
        self.assertEqual((order.package_code, order.total_cents), ("essentieel", Package.objects.get(code="essentieel").price_cents))
        self.assertEqual(card_kind(inv.published_version.content, inv.occasion), "uitnodiging")
        html = Client().get(f"/u/{inv.slug}/").content.decode()
        self.assertIn('id="aanmelden"', html)
        response = self.rsvp(Client(), inv)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(inv.responses.count(), 1)

    def test_betaalde_kerstuitnodiging_zonder_soort_blijft_uitnodiging(self):
        owner = self.make_customer()
        inv = create_draft(occasion="kerst", template=Template.objects.get(slug="winterlicht"), owner=owner)
        content = dict(inv.draft_content)
        content.update({"names": {"family": "Familie Jansen", "members": ""}, "date": future_date(60), "start_time": "17:00", "venue_name": "Thuis"})
        content["rsvp"] = dict(content["rsvp"], deadline=future_date(40))
        inv = save_draft(inv, expected_rev=None, content=content, user=owner)
        self.pay(inv, owner)
        inv.refresh_from_db()
        self.assertEqual(Order.objects.get(invitation=inv).package_code, "essentieel")
        self.assertIn('id="aanmelden"', Client().get(f"/u/{inv.slug}/").content.decode())


class BetaaldeWenskaartVastTests(VaylideTestCase):
    """4. Een betaalde wenskaart kan niet terugvallen naar een uitnodiging."""

    def betaalde_wenskaart(self, owner):
        inv = create_draft(occasion="kerst", template=Template.objects.get(slug="winterlicht"), owner=owner, soort="wenskaart")
        content = dict(inv.draft_content)
        content["names"] = {"family": "Familie Jansen", "members": ""}
        inv = save_draft(inv, expected_rev=None, content=content, user=owner)
        self.pay(inv, owner)
        inv.refresh_from_db()
        return inv

    def test_formulier_kan_de_soort_niet_meer_wijzigen(self):
        owner = self.make_customer()
        inv = self.betaalde_wenskaart(owner)
        c = Client()
        c.force_login(owner)
        pagina = c.get(f"/maken/{inv.uid}/gegevens/").content.decode()
        self.assertIn("Dit ligt vast", pagina)
        self.assertIn("disabled", pagina.split('name="soort" value="uitnodiging"')[1][:200])
        for soort in ("uitnodiging", ""):
            c.post(f"/maken/{inv.uid}/gegevens/", {"rev": inv.draft_rev, "actie": "opslaan", "soort": soort, "name_family": "Familie Jansen",
                                                   "date": future_date(30), "start_time": "17:00", "venue_name": "Thuis", "timezone": "Europe/Amsterdam"})
            inv.refresh_from_db()
            self.assertEqual(inv.draft_content["soort"], "wenskaart", soort)

    def test_gepubliceerde_kaart_en_prijs_blijven_wenskaart(self):
        owner = self.make_customer()
        inv = self.betaalde_wenskaart(owner)
        html = Client().get(f"/u/{inv.slug}/").content.decode()
        self.assertNotIn('id="aanmelden"', html)
        self.assertEqual(self.rsvp(Client(), inv).status_code, 409)
        self.assertEqual(inv.published_version.content["soort"], "wenskaart")
        self.assertEqual(Order.objects.get(invitation=inv).total_cents, 1495)

    def test_ook_het_ontwerp_wisselen_laat_de_soort_staan(self):
        owner = self.make_customer()
        inv = self.betaalde_wenskaart(owner)
        c = Client()
        c.force_login(owner)
        c.post(f"/maken/{inv.uid}/ontwerp/", {"rev": inv.draft_rev, "occasion": "kerst", "template": "gloria"})
        inv.refresh_from_db()
        self.assertEqual(inv.draft_content["soort"], "wenskaart")

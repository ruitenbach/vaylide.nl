"""Reparaties na de audit van 10 oktober 2026: geen tweede keuzescherm, geen lege kaart bestellen, de gekozen kaart in het besteloverzicht,
de zin over specials die klopt met de prijs, de iconen op de hoofdmap en de mobiele verbeteringen."""
from django.test import Client

from catalog.models import AddOn, Template
from catalog.specials import special_prijszin
from invitations.content import default_content, publish_issues
from invitations.models import Invitation
from orders.services import CheckoutError, start_checkout

from .helpers import VaylideTestCase, future_date


def blokkerend(content, occasion, first=True):
    return [(i.field, i.blocking) for i in publish_issues(content, occasion, first_publication=first) if i.blocking]


def vul(occasion, namen=None, datum=True, soort="uitnodiging"):
    content = default_content(occasion)
    content["names"] = dict(namen or {})
    content["soort"] = "wenskaart" if soort == "wenskaart" else ""
    if datum:
        content.update({"date": future_date(90), "start_time": "14:00", "venue_name": "Zaal", "address": "Straat 1"})
    return content


class BestelControleTests(VaylideTestCase):
    """Wat een kaart minstens nodig heeft, hangt af van gelegenheid en soort (niet blind voor alle kaarten dezelfde namen en datum)."""

    def test_een_lege_kaart_blokkeert_per_gelegenheid_op_de_eerste_naam_en_de_datum(self):
        eerste = {"bruiloft": "partner_1", "verloving": "partner_1", "verjaardag": "person_name", "jubileum": "honorees",
                  "babyshower": "parents", "zakelijk": "event_title"}
        for occasion, naam in eerste.items():
            velden = [veld for veld, _ in blokkerend(vul(occasion, datum=False), occasion)]
            self.assertIn(naam, velden, occasion)
            self.assertIn("date", velden, occasion)

    def test_de_tweede_naam_en_tijd_en_locatie_blijven_tips(self):
        content = vul("bruiloft", {"partner_1": "Anna"}, datum=False)
        content["date"] = future_date(90)
        problemen = publish_issues(content, "bruiloft", first_publication=True)
        self.assertEqual([i.field for i in problemen if i.blocking], [])
        self.assertIn("partner_2", [i.field for i in problemen if not i.blocking])
        self.assertIn("start_time", [i.field for i in problemen if not i.blocking])
        zakelijk = vul("zakelijk", {"event_title": "Lancering"})
        self.assertEqual(blokkerend(zakelijk, "zakelijk"), [])      # de organisatie is een tip, de naam van het evenement is nodig

    def test_bij_kerst_is_de_datum_niet_nodig_maar_de_afzender_wel(self):
        leeg = blokkerend(vul("kerst", datum=False), "kerst")
        self.assertEqual([veld for veld, _ in leeg], ["family"])
        self.assertEqual(blokkerend(vul("kerst", {"family": "Familie Jansen"}, datum=False), "kerst"), [])

    def test_een_wenskaart_heeft_alleen_een_naam_nodig_en_geen_datum(self):
        for occasion, naam in (("bruiloft", "partner_1"), ("verjaardag", "person_name"), ("kerst", "family")):
            self.assertEqual([veld for veld, _ in blokkerend(vul(occasion, datum=False, soort="wenskaart"), occasion)], [naam], occasion)
            self.assertEqual(blokkerend(vul(occasion, {naam: "Sanne"}, datum=False, soort="wenskaart"), occasion), [], occasion)

    def test_bij_het_aanpassen_van_een_gepubliceerde_kaart_komen_er_geen_nieuwe_blokkades(self):
        self.assertEqual(blokkerend(vul("verjaardag", datum=False), "verjaardag", first=False), [])

    def test_bestellen_met_een_lege_kaart_wordt_geweigerd_en_met_een_gevulde_kaart_kan_het(self):
        klant = self.make_customer()
        inv = self.make_invitation(owner=klant, template="avondgoud", occasion="verjaardag", complete=False)
        client = Client()
        client.force_login(klant)
        pagina = client.get(f"/maken/{inv.uid}/bestellen/").content.decode()
        self.assertIn("voordat je kunt bestellen", pagina)
        self.assertIn("is nog leeg: vul dit in voordat je bestelt", pagina)
        with self.assertRaises(CheckoutError):
            start_checkout(inv, user=klant, package_code="essentieel", optional_codes=[], terms_accepted=True)
        antwoord = client.post(f"/maken/{inv.uid}/bestellen/", {"actie": "betalen", "package": "essentieel", "terms": "on", "direct_leveren": "on", "online_dienst": "on"})
        self.assertContains(antwoord, "nog niet klaar om te bestellen")
        self.assertEqual(inv.orders.count(), 0)
        content = vul("verjaardag", {"person_name": "Lotte"})
        from invitations.services import save_draft

        inv = save_draft(inv, expected_rev=inv.draft_rev, content=content, user=klant)
        with self.captureOnCommitCallbacks(execute=True):
            betaling = start_checkout(inv, user=klant, package_code="essentieel", optional_codes=[], terms_accepted=True)
        self.assertEqual(betaling.order.invitation_id, inv.id)


class StartTests(VaylideTestCase):
    def test_de_automatische_start_blokkeert_dezelfde_kaart_niet_meer_een_tweede_keer(self):
        js = open("static/js/studio.js", encoding="utf-8").read()
        self.assertIn('nav.type === "back_forward"', js)
        self.assertIn('"reload"', js)
        # De oude sessiesleutel is alleen nog een terugval voor browsers zonder Navigation Timing.
        voor, na = js.split('nav.type === "back_forward"', 1)
        self.assertNotIn("sessionStorage", voor.split("Kies kaart: vanaf een ontwerppagina", 1)[1])

    def test_de_startpagina_van_een_ontwerppagina_start_direct_en_noemt_bestaande_concepten_bij_het_ontwerp(self):
        klant = self.make_customer()
        inv = self.make_invitation(owner=klant, template="avondgoud", occasion="verjaardag", complete=False)
        client = Client()
        client.force_login(klant)
        html = client.get("/maken/", {"ontwerp": "balzaal", "gelegenheid": "bruiloft", "kleur": "ivoor", "soort": "uitnodiging", "direct": "1"}).content.decode()
        self.assertIn("data-auto-start", html)
        self.assertIn("Avondgoud", html.split("resume-list", 1)[1].split("</ul>", 1)[0])
        self.assertNotIn("Naamloos ontwerp", html)
        self.assertEqual(Invitation.objects.filter(owner=klant).count(), 1)

    def test_een_concept_met_een_bestelling_krijgt_nooit_stilzwijgend_een_ander_ontwerp(self):
        klant = self.make_customer()
        client = Client()
        client.force_login(klant)
        # Een nieuwe kaartkeuze in een lopend traject werkt het onaangeroerde concept bij ...
        eerste = client.post("/maken/", {"occasion": "verjaardag", "template": "avondgoud", "kleur": "", "soort": "uitnodiging"})
        inv = Invitation.objects.get(owner=klant)
        self.assertEqual(eerste.status_code, 302)
        tweede = client.post("/maken/", {"occasion": "verjaardag", "template": "zuiden", "kleur": "", "soort": "uitnodiging"})
        self.assertEqual(tweede.status_code, 302)
        inv.refresh_from_db()
        self.assertEqual(inv.template_version.template.slug, "zuiden")
        self.assertEqual(Invitation.objects.filter(owner=klant).count(), 1)
        # ... maar zodra er een bestelling bij hoort, blijft dat concept zoals het is en komt er een nieuw concept.
        from orders.models import Order

        Order.objects.create(customer=klant, invitation=inv, kind=Order.Kind.INVITATION, status=Order.Status.FAILED, number="VL26-99999", total_cents=3900)
        derde = client.post("/maken/", {"occasion": "verjaardag", "template": "polaroid", "kleur": "", "soort": "uitnodiging"})
        self.assertEqual(derde.status_code, 302)
        inv.refresh_from_db()
        self.assertEqual(inv.template_version.template.slug, "zuiden")
        self.assertEqual(Invitation.objects.filter(owner=klant).count(), 2)


class OverzichtTests(VaylideTestCase):
    def test_het_besteloverzicht_toont_de_gekozen_kaart(self):
        klant = self.make_customer()
        inv = self.make_invitation(owner=klant, template="balzaal", occasion="bruiloft")
        client = Client()
        client.force_login(klant)
        html = client.get(f"/maken/{inv.uid}/bestellen/").content.decode()
        kaart = html.split("data-bestel-kaart", 1)[1].split("</div>", 2)[0:2]
        tekst = " ".join(kaart)
        self.assertIn("Balzaal", tekst)
        self.assertIn("Special", tekst)
        self.assertIn("Bruiloft", tekst)
        self.assertIn("Uitnodiging", tekst)
        self.assertIn(f"/maken/{inv.uid}/ontwerp/", html)
        gewoon = self.make_invitation(owner=klant, template="avondgoud", occasion="verjaardag", **{"names": {"person_name": "Lotte"}})
        html = client.get(f"/maken/{gewoon.uid}/bestellen/").content.decode()
        deel = html.split("data-bestel-kaart", 1)[1].split("</a>", 1)[0]
        self.assertIn("Avondgoud", deel)
        self.assertNotIn("Special", deel)


class SpecialPrijsTekstTests(VaylideTestCase):
    def test_de_zin_volgt_de_ingestelde_meerprijzen(self):
        specials = list(Template.objects.filter(special=True, is_active=True))
        self.assertTrue(specials)
        AddOn.objects.filter(feature="special").delete()
        self.assertIn("niets extra", special_prijszin())
        AddOn.objects.create(code=f"special-{specials[0].slug}", name="Meerprijs", price_cents=500, feature="special")
        self.assertTrue(special_prijszin().startswith("Sommige specials"))
        for t in specials:
            AddOn.objects.get_or_create(code=f"special-{t.slug}", defaults={"name": "Meerprijs", "price_cents": 500, "feature": "special"})
        self.assertEqual(special_prijszin(), "Een special heeft een eigen meerprijs, die je vóór het afrekenen ziet.")

    def test_collectie_trouwpagina_en_faq_gebruiken_dezelfde_zin(self):
        AddOn.objects.filter(feature="special").delete()
        zin = special_prijszin()
        client = Client()
        for pad in ("/ontwerpen/", "/digitale-trouwkaarten/", "/digitale-uitnodiging-maken/"):
            html = client.get(pad).content.decode()
            self.assertIn(zin, html, pad)
            self.assertNotIn("Specials hebben een eigen meerprijs", html, pad)
        AddOn.objects.create(code="special-balzaal", name="Meerprijs", price_cents=500, feature="special")
        self.assertIn("Sommige specials hebben een eigen meerprijs", client.get("/ontwerpen/").content.decode())


class IconenEnZinTests(VaylideTestCase):
    def test_de_iconen_op_de_hoofdmap_bestaan(self):
        client = Client()
        ico = client.get("/favicon.ico")
        self.assertEqual(ico.status_code, 200)
        self.assertEqual(ico["Content-Type"], "image/x-icon")
        self.assertTrue(b"".join(ico.streaming_content).startswith(b"\x00\x00\x01\x00"))
        for pad in ("/apple-touch-icon.png", "/apple-touch-icon-precomposed.png"):
            antwoord = client.get(pad)
            self.assertEqual(antwoord.status_code, 200, pad)
            self.assertEqual(antwoord["Content-Type"], "image/png", pad)
            self.assertTrue(b"".join(antwoord.streaming_content).startswith(b"\x89PNG"), pad)

    def test_de_zin_op_de_collectiepagina_loopt_goed_en_houdt_het_anker(self):
        html = Client().get("/ontwerpen/").content.decode()
        self.assertIn('<a href="/digitale-uitnodiging-maken/">Lees stap voor stap hoe je een digitale uitnodiging maakt.</a>', html)
        self.assertNotIn("maken kunt", html)

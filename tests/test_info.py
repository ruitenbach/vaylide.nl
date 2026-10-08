"""Info-knop (i) in de Studio en bij Bestellen: één component (templates/partials/info.html, static/js/info.js), korte vaste
productteksten, prijzen en looptijden uit Beheer (dezelfde bron als de rekening), geen klantgegevens in de knop of het paneel."""
import re
from pathlib import Path

from django.conf import settings
from django.test import Client

from catalog.models import AddOn, Package
from studio import pakket

from .helpers import VaylideTestCase

JS = (Path(settings.BASE_DIR) / "static/js/info.js").read_text(encoding="utf-8")
JS_CODE = re.sub(r"/\*.*?\*/", "", JS, flags=re.S)


def componenten(html):
    """Alle info-componenten op een pagina: (knop-html, paneel-html)."""
    return re.findall(r'<span class="info" data-info>\s*(<button[^>]*data-info-knop>).*?(<span class="info__paneel".*?</span>\s*</span>)', html, re.S)


class InfoTests(VaylideTestCase):
    def setUp(self):
        self.owner = self.make_customer()
        self.c = Client()
        self.c.force_login(self.owner)

    def stap(self, inv, naam):
        response = self.c.get(f"/maken/{inv.uid}/{naam}/")
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_component_is_een_echte_knop_met_een_gekoppeld_paneel(self):
        html = self.stap(self.make_invitation(owner=self.owner), "aanmelden")
        (knop, paneel), = componenten(html)
        self.assertIn('type="button"', knop)                                  # nooit een submit
        self.assertIn('aria-expanded="false"', knop)
        self.assertIn('aria-haspopup="dialog"', knop)
        self.assertIn('aria-controls="info-aanmelden"', knop)
        self.assertIn('popovertarget="info-aanmelden"', knop)
        self.assertIn('aria-label="Uitleg: Hoe werkt aanmelden?"', knop)
        self.assertNotIn("title=", knop)                                       # geen browser-tooltip
        self.assertIn('id="info-aanmelden" popover role="dialog"', paneel)
        self.assertIn('aria-labelledby="info-aanmelden-titel"', paneel)
        self.assertIn('aria-describedby="info-aanmelden-tekst"', paneel)
        self.assertIn('aria-label="Sluiten"', paneel)
        self.assertIn('popovertargetaction="hide"', paneel)
        # Naast de kop, niet erin: de uitleg hoort niet bij de naam van de kop.
        self.assertRegex(html, r'<div class="met-info">\s*<h2 class="studio-block__title" id="blok-rsvp">Gasten laten aanmelden</h2>\s*<span class="info"')
        self.assertEqual(html.count("js/info.js"), 1)

    def test_aanmelden_tekst(self):
        html = self.stap(self.make_invitation(owner=self.owner), "aanmelden")
        self.assertIn("Hoe werkt aanmelden?", html)
        self.assertIn("Gasten kunnen via de uitnodiging aangeven of ze wel of niet komen en met hoeveel personen. Hun reactie komt "
                      "automatisch in Mijn VAYLIDE terecht, zodat je alle aanmeldingen op één plek kunt bekijken.", html)

    def test_geen_klantgegevens_in_knop_of_paneel(self):
        inv = self.make_invitation(owner=self.owner, venue_name="Geheime Plek", welcome_text="Geheime welkomsttekst")
        for naam in ("aanmelden", "fotos", "bestellen"):
            for knop, paneel in componenten(self.stap(inv, naam)):
                for geheim in ("Anna", "Bram", "Geheime", "Teststraat", "Utrecht", str(inv.uid), self.owner.email):
                    self.assertNotIn(geheim, knop + paneel, naam)
                self.assertFalse(re.findall(r'data-(?!info)[a-z-]+="', knop + paneel), naam)    # geen eigen data-attributen met waarden

    def test_studio_masking_blijft_staan(self):
        html = self.stap(self.make_invitation(owner=self.owner), "aanmelden")
        self.assertIn('data-clarity-mask="True"', html[:html.index('data-info')])           # het info-component zit binnen de afgeschermde Studio

    def test_looptijd_uit_de_pakketten_in_beheer(self):
        inv = self.make_invitation(owner=self.owner)
        self.assertIn("Met Essentieel blijft je kaart 6 maanden online. Met Compleet 12 maanden, gerekend vanaf de bevestigde betaling.",
                      self.stap(inv, "bestellen"))
        Package.objects.filter(code="compleet").update(availability_months=18)                  # komt uit Beheer, niet uit de tekst
        self.assertIn("Met Compleet 18 maanden, gerekend vanaf de bevestigde betaling.", self.stap(inv, "bestellen"))

    def test_looptijd_bij_een_wenskaart(self):
        inv = self.make_invitation(owner=self.owner, soort="wenskaart")
        html = self.stap(inv, "bestellen")
        self.assertRegex(html, r"Je wenskaart blijft \d+ maanden online, gerekend vanaf de bevestigde betaling\.")
        self.assertNotIn("Met Essentieel blijft", html)

    def test_na_betaling(self):
        html = self.stap(self.make_invitation(owner=self.owner), "bestellen")
        self.assertIn("Wat gebeurt er na betaling?", html)
        self.assertIn("Na een geslaagde betaling wordt je kaart geactiveerd. Daarna kun je de uitnodiging delen en reacties beheren "
                      "vanuit Mijn VAYLIDE.", html)
        self.assertEqual(len(componenten(html)), 2)                                              # looptijd en na betaling
        wens = self.stap(self.make_invitation(owner=self.owner, soort="wenskaart"), "bestellen")
        self.assertIn("Daarna kun je de kaart delen vanuit Mijn VAYLIDE.", wens)
        self.assertNotIn("reacties beheren", wens)

    def test_muziek_met_de_prijs_uit_beheer(self):
        inv = self.make_invitation(owner=self.owner)
        inv.package_code = "essentieel"
        inv.save(update_fields=["package_code"])
        html = self.stap(inv, "fotos")
        self.assertIn("Upload je eigen nummer voor deze kaart. Deze toevoeging kost € 9.", html)
        self.assertNotIn("Muziek die al onderdeel is van een ontwerp", html)                    # dit ontwerp heeft geen eigen track
        AddOn.objects.filter(code="muziek").update(price_cents=1100)
        self.assertIn("Deze toevoeging kost € 11.", self.stap(inv, "fotos"))
        inv.package_code = "compleet"
        inv.save(update_fields=["package_code"])
        self.assertIn("In Compleet zit dit erbij, zonder extra kosten.", self.stap(inv, "fotos"))

    def test_muziek_tekst_bij_een_ontwerp_met_eigen_muziek(self):
        essentieel = Package.objects.get(code="essentieel")
        self.assertEqual(pakket.muziek_uitleg(essentieel, ontwerp_muziek=True),
                         "Upload je eigen nummer voor deze kaart. Deze toevoeging kost € 9. "
                         "Muziek die al onderdeel is van een ontwerp kost niets extra.")
        AddOn.objects.filter(feature="music").update(is_active=False)
        self.assertEqual(pakket.muziek_uitleg(essentieel, ontwerp_muziek=True), "")               # niet te koop: geen uitleg

    def test_geen_info_bij_gewone_velden(self):
        inv = self.make_invitation(owner=self.owner)
        for naam in ("programma", "stijl"):
            self.assertNotIn("data-info-knop", self.stap(inv, naam), naam)
        gegevens = self.stap(inv, "gegevens")
        self.assertEqual(gegevens.count("data-info-knop"), 1)                                   # alleen bij Uitnodiging of wenskaart
        self.assertEqual(self.stap(inv, "aanmelden").count("data-info-knop"), 1)                 # niet bij Aantal personen

    def test_uitnodiging_of_wenskaart(self):
        inv = self.make_invitation(owner=self.owner)
        html = self.stap(inv, "gegevens")
        (knop, paneel), = componenten(html)
        self.assertIn('aria-label="Uitleg: Uitnodiging of wenskaart?"', knop)
        self.assertIn("Kies Uitnodiging als je gasten wilt uitnodigen voor een moment met datum, locatie en eventueel aanmelden. "
                      "Kies Wenskaart als je alleen een persoonlijke kaart wilt versturen, zonder datum, locatie of aanmeldingen, "
                      "voor een vaste prijs van € 14,95. Je ziet daarna alleen de stappen die bij je keuze horen. "
                      "Na het bestellen ligt je keuze vast.", paneel)
        # Naast de uitklapregel, niet erin (een knop in een summary is voor schermlezers onbetrouwbaar).
        self.assertRegex(html, r'<div class="met-info met-info--keuze">\s*<details class="studio-more" data-soort-keuze>')
        self.assertRegex(html, r'</details>\s*<span class="info" data-info>')
        summary = re.search(r"<summary>.*?</summary>", html[html.index("data-soort-keuze"):], re.S).group(0)
        self.assertNotIn("data-info", summary)

    def test_uitnodiging_of_wenskaart_zonder_prijs_bij_kerst(self):
        tekst = pakket.soort_uitleg(None)                                                          # zoals de keuze zelf bij kerst
        self.assertNotIn("vaste prijs", tekst)
        self.assertIn("zonder datum, locatie of aanmeldingen. Je ziet daarna", tekst)
        self.assertTrue(tekst.endswith("Na het bestellen ligt je keuze vast."))

    def test_script_leest_of_wijzigt_geen_formulieren(self):
        self.assertNotIn(".value", JS_CODE)
        self.assertNotIn("submit", JS_CODE)
        self.assertNotIn("dataset", JS_CODE)
        self.assertNotIn("clarity", JS_CODE.lower())
        self.assertNotIn("fetch(", JS_CODE)

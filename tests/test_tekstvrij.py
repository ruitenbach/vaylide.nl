"""Twee kleine correcties van 16 oktober 2026: geen 'Voorlopige prijzen' op de prijzenpagina, en bij Kerstpaleis en Kerstbal blijft de tekst vrij van de
deeltjes van het openen en vieren (invitations/static/invitations/tekstvrij.js)."""
from pathlib import Path

from django.conf import settings
from django.test import Client

from core.models import SiteConfig

from .helpers import VaylideTestCase


class PrijzenpaginaTests(VaylideTestCase):
    def test_de_prijzenpagina_toont_geen_voorlopige_prijzen_meer_ook_als_de_instelling_aanstaat(self):
        config = SiteConfig.get()
        config.prices_provisional = True
        config.save()
        tekst = Client().get("/prijzen/").content.decode()
        self.assertNotIn("Voorlopige prijzen", tekst)
        self.assertIn("Eén keer betalen", tekst)  # de pagina zelf en de prijzen blijven staan


class TekstVrijTests(VaylideTestCase):
    def test_kerstpaleis_en_kerstbal_laden_het_tekstvrij_script_en_andere_ontwerpen_niet(self):
        for slug in ("kerstpaleis", "kerstbal"):
            tekst = Client().get(f"/voorbeeld/{slug}/").content.decode()
            self.assertIn("invitations/tekstvrij", tekst, slug)
        for slug in ("kerstmarkt", "zwanenhart"):
            self.assertNotIn("tekstvrij", Client().get(f"/voorbeeld/{slug}/").content.decode(), slug)

    def test_het_script_bestaat_en_raakt_de_gedeelde_effecten_niet_aan(self):
        script = Path(settings.BASE_DIR) / "invitations" / "static" / "invitations" / "tekstvrij.js"
        inhoud = script.read_text(encoding="utf-8")
        self.assertIn(".fx-burst", inhoud)
        self.assertIn("clipPath", inhoud)
        effects = (script.parent / "effects.js").read_text(encoding="utf-8")
        self.assertNotIn("tekstvrij", effects)

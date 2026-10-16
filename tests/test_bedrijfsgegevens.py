from django.test import TestCase, override_settings


@override_settings(COMPANY_KVK="11111111", COMPANY_VAT="NL000000000B01")
class BedrijfsgegevensTests(TestCase):
    """Een standaardwaarde uit de code is geen bewijs: KvK en btw-id staan buiten de juridische teksten alleen als de eigenaar ze bevestigde."""

    ONBEVESTIGD = {"kvk": False, "btw": False, "adres": True, "email": True}
    BEVESTIGD = {"kvk": True, "btw": True, "adres": True, "email": True}

    def test_onbevestigd_staan_ze_niet_in_voettekst_contactpagina_en_bestelmail(self):
        from core.company import as_text

        with override_settings(COMPANY_CONFIRMED=self.ONBEVESTIGD):
            for pad in ("/", "/prijzen/", "/contact/"):
                html = self.client.get(pad).content.decode()
                self.assertNotIn("11111111", html, pad)
                self.assertNotIn("NL000000000B01", html, pad)
            self.assertIn("[KvK-nummer]", self.client.get("/contact/").content.decode())
            tekst = as_text()
            self.assertNotIn("11111111", tekst)
            self.assertNotIn("NL000000000B01", tekst)
            self.assertIn("[KvK-nummer]", tekst)

    def test_bevestigd_staan_ze_er_wel(self):
        from core.company import as_text

        with override_settings(COMPANY_CONFIRMED=self.BEVESTIGD):
            html = self.client.get("/").content.decode()
            self.assertIn("KvK 11111111", html)
            self.assertIn("btw-id NL000000000B01", html)
            contact = self.client.get("/contact/").content.decode()
            self.assertIn("11111111", contact)
            self.assertIn("NL000000000B01", contact)
            self.assertIn("KvK-nummer: 11111111", as_text())

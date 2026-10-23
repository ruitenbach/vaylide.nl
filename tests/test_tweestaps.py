"""Tweestapsverificatie (TOTP + herstelcodes) voor Beheer en Django-admin."""
from io import StringIO
from unittest import mock

from cryptography.fernet import Fernet
from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, override_settings
from django.urls import reverse

from accounts import tweestaps
from accounts.models import RecoveryCode, TwoFactor, User

from .helpers import VaylideTestCase

PASSWORD = "Een-lang-wachtwoord-2026"
STAP = 1_000_000          # vaste "tijd" in de tests (periode van 30 seconden)
ADMIN = f"/{settings.ADMIN_URL}"


@override_settings(TWOFA_KEYS=[Fernet.generate_key().decode()], TWOFA_REQUIRED=False)
class TweestapsBase(VaylideTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.staff = self.make_staff()
        self.stap = STAP
        patcher = mock.patch("accounts.tweestaps.huidige_stap", side_effect=lambda: self.stap)
        patcher.start()
        self.addCleanup(patcher.stop)

    def login(self, client=None):
        client = client or Client()
        response = client.post("/beheer/inloggen/", {"username": self.staff.email, "password": PASSWORD})
        self.assertEqual(response.status_code, 302)
        return client

    def code(self, geheim, stap=None):
        return tweestaps._code(geheim, self.stap if stap is None else stap)

    def schakel_in(self, client=None):
        """Zet 2FA aan via de schermen; geeft (client, geheim, herstelcodes) terug."""
        client = self.login(client)
        client.get("/beheer/2fa/instellen/")
        geheim = tweestaps.ontsleutel(client.session[tweestaps.SESSION_PENDING])
        response = client.post("/beheer/2fa/instellen/", {"code": self.code(geheim)})
        self.assertEqual(response.status_code, 200)
        return client, geheim, response.context["codes"]

    def inloggen_met_code(self, geheim, stap_erbij=1):
        """Nieuwe sessie: wachtwoord, daarna de code van een volgende periode (een eerdere code is al gebruikt)."""
        self.stap += stap_erbij
        client = self.login()
        response = client.post("/beheer/2fa/controle/", {"code": self.code(geheim)})
        return client, response


class TotpTests(TweestapsBase):
    def test_rfc6238_testvector(self):
        # RFC 6238, bijlage B: geheim "12345678901234567890", tijd 59 s (periode 1), SHA-1, laatste 6 cijfers van 94287082.
        import base64
        geheim = base64.b32encode(b"12345678901234567890").decode()
        self.assertEqual(tweestaps._code(geheim, 1), "287082")

    def test_code_van_vorige_en_volgende_periode_telt_en_verder_weg_niet(self):
        geheim = tweestaps.nieuw_geheim()
        self.assertEqual(tweestaps.passende_stap(geheim, self.code(geheim, self.stap - 1)), self.stap - 1)
        self.assertEqual(tweestaps.passende_stap(geheim, self.code(geheim, self.stap + 1)), self.stap + 1)
        self.assertIsNone(tweestaps.passende_stap(geheim, self.code(geheim, self.stap - 2)))
        self.assertIsNone(tweestaps.passende_stap(geheim, "12345"))
        self.assertIsNone(tweestaps.passende_stap(geheim, "abcdef"))


class OpslagTests(TweestapsBase):
    def test_geheim_versleuteld_en_herstelcodes_gehasht(self):
        _, geheim, codes = self.schakel_in()
        tf = TwoFactor.objects.get(user=self.staff)
        self.assertNotIn(geheim, tf.secret_enc)
        self.assertEqual(tweestaps.ontsleutel(tf.secret_enc), geheim)
        self.assertEqual(len(codes), 10)
        opgeslagen = set(RecoveryCode.objects.values_list("code_hash", flat=True))
        self.assertEqual(len(opgeslagen), 10)
        for code in codes:
            self.assertNotIn(code, opgeslagen)
            self.assertNotIn(code.replace("-", ""), opgeslagen)
            self.assertEqual(len(code.replace("-", "")), 12)

    def test_sleutel_vervangen_met_oude_sleutel_erbij_blijft_werken(self):
        oud = settings.TWOFA_KEYS[0]
        token = tweestaps.versleutel("GEHEIM")
        with override_settings(TWOFA_KEYS=[Fernet.generate_key().decode(), oud]):
            self.assertEqual(tweestaps.ontsleutel(token), "GEHEIM")
        with override_settings(TWOFA_KEYS=[Fernet.generate_key().decode()]):
            with self.assertRaises(Exception):
                tweestaps.ontsleutel(token)

    def test_zonder_sleutel_kan_niets_worden_ingesteld(self):
        with override_settings(TWOFA_KEYS=[]):
            client = self.login()
            response = client.get("/beheer/2fa/instellen/")
            self.assertContains(response, "VIERLIEF_2FA_SLEUTEL")
            response = client.post("/beheer/2fa/instellen/", {"code": "123456"})
            self.assertFalse(TwoFactor.objects.exists())
            self.assertEqual(client.get("/beheer/").status_code, 200)       # inloggen met wachtwoord blijft werken


class SleutelProbleemTests(TweestapsBase):
    def test_ontbrekende_of_verkeerde_sleutel_laat_niemand_door_en_geeft_geen_serverfout(self):
        _, geheim, codes = self.schakel_in()
        self.stap += 1
        for keys in ([], [Fernet.generate_key().decode()]):
            with override_settings(TWOFA_KEYS=keys):
                client = self.login()
                for invoer in (self.code(geheim), codes[0]):
                    response = client.post("/beheer/2fa/controle/", {"code": invoer})
                    self.assertEqual(response.status_code, 503)
                    self.assertContains(response, "VIERLIEF_2FA_SLEUTEL", status_code=503)
                    self.assertEqual(client.get("/beheer/").status_code, 302)       # geen onveilige terugval naar alleen wachtwoord
                    self.assertEqual(client.get(ADMIN).status_code, 302)
        self.assertEqual(tweestaps.herstelcodes_over(self.staff), 10)               # niets is verbruikt
        # met de juiste sleutel terug werkt alles weer
        client = self.login()
        self.assertEqual(client.post("/beheer/2fa/controle/", {"code": self.code(geheim)}).status_code, 302)

    def test_reset_werkt_zonder_sleutel(self):
        self.schakel_in()
        with override_settings(TWOFA_KEYS=[]):
            call_command("reset_2fa", self.staff.email, "--bevestig", stdout=StringIO())
        self.assertFalse(TwoFactor.objects.exists())


class ActiverenTests(TweestapsBase):
    def test_pas_na_juiste_eerste_code_aan(self):
        client = self.login()
        client.get("/beheer/2fa/instellen/")
        response = client.post("/beheer/2fa/instellen/", {"code": "000000"})
        self.assertContains(response, "klopt niet")
        self.assertFalse(TwoFactor.objects.exists())
        self.assertFalse(RecoveryCode.objects.exists())
        self.assertEqual(client.get("/beheer/").status_code, 200)

    def test_qr_alleen_tijdens_instellen_en_niet_cachebaar(self):
        client = self.login()
        self.assertEqual(client.get("/beheer/2fa/qr.svg").status_code, 404)
        client.get("/beheer/2fa/instellen/")
        response = client.get("/beheer/2fa/qr.svg")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(Client().get("/beheer/2fa/qr.svg").status_code, 302)

    def test_na_activeren_is_sessie_geverifieerd_en_codes_worden_niet_opnieuw_getoond(self):
        client, geheim, codes = self.schakel_in()
        self.assertEqual(client.get("/beheer/").status_code, 200)
        response = client.get("/beheer/2fa/")
        self.assertNotContains(response, codes[0])
        self.assertContains(response, "10</strong> herstelcode")

    def test_klant_heeft_geen_toegang_tot_de_schermen(self):
        self.make_customer()
        klant = Client()
        klant.force_login(User.objects.get(email="klant@example.com"))
        for pad in ("/beheer/2fa/", "/beheer/2fa/instellen/", "/beheer/2fa/controle/", "/beheer/2fa/qr.svg"):
            self.assertEqual(klant.get(pad).status_code, 404, pad)


class PoortTests(TweestapsBase):
    def test_zonder_2fa_en_niet_verplicht_verandert_er_niets(self):
        client = self.login()
        self.assertEqual(client.get("/beheer/").status_code, 200)
        self.assertEqual(client.get(ADMIN).status_code, 200)

    def test_na_wachtwoord_is_een_code_nodig_voor_beheer_en_admin(self):
        _, geheim, _ = self.schakel_in()
        client = self.login(Client())
        for pad in ("/beheer/", "/beheer/bestellingen/", "/beheer/klanten/nieuwsbrief.csv", ADMIN, f"{ADMIN}accounts/user/"):
            response = client.get(pad)
            self.assertEqual(response.status_code, 302, pad)
            self.assertTrue(response["Location"].startswith("/beheer/2fa/controle/"), pad)
        self.assertEqual(client.post("/beheer/prijzen-en-acties/wijzigen/", {}).status_code, 302)

    def test_zonder_code_is_de_medewerker_overal_anoniem(self):
        from orders.models import Order

        order = Order.objects.filter(invitation=self.published()).first()
        client, geheim, _ = self.schakel_in()
        self.assertEqual(client.get(f"/bestelling/{order.uid}/").status_code, 200)       # medewerker met code: mag een klantbestelling zien
        client = self.login(Client())
        self.assertFalse(client.get("/").context["user"].is_authenticated)
        self.assertNotEqual(client.get(f"/bestelling/{order.uid}/").status_code, 200)    # zonder code: niet
        self.assertEqual(client.get("/account/").status_code, 302)

    def test_controlepagina_lekt_geen_beheergegevens(self):
        _, geheim, _ = self.schakel_in()
        client = self.login(Client())
        response = client.get("/beheer/2fa/controle/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Bestellingen")
        self.assertNotContains(response, "Beveiliging")

    def test_met_juiste_code_toegang_tot_beide_ingangen(self):
        _, geheim, _ = self.schakel_in()
        client, response = self.inloggen_met_code(geheim)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.get("/beheer/").status_code, 200)
        self.assertEqual(client.get(ADMIN).status_code, 200)

    def test_next_wordt_gerespecteerd_en_externe_next_niet(self):
        _, geheim, _ = self.schakel_in()
        self.stap += 1
        client = self.login()
        response = client.post("/beheer/2fa/controle/", {"code": self.code(geheim), "next": "https://evil.example/"})
        self.assertEqual(response["Location"], "/beheer/")
        self.stap += 1
        client = self.login()
        response = client.post("/beheer/2fa/controle/", {"code": self.code(geheim), "next": ADMIN})
        self.assertEqual(response["Location"], ADMIN)

    def test_adminlogin_met_wachtwoord_geeft_geen_toegang_zonder_code(self):
        _, geheim, _ = self.schakel_in()
        client = Client()
        response = client.post(f"{ADMIN}login/", {"username": self.staff.email, "password": PASSWORD, "next": ADMIN})
        self.assertEqual(response.status_code, 302)
        response = client.get(ADMIN)
        self.assertTrue(response["Location"].startswith("/beheer/2fa/controle/"))

    def test_bestaande_sessie_van_voor_het_aanzetten_vraagt_nu_een_code(self):
        oude_sessie = self.login()
        self.assertEqual(oude_sessie.get("/beheer/").status_code, 200)
        self.schakel_in(Client())
        response = oude_sessie.get("/beheer/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response["Location"].startswith("/beheer/2fa/controle/"))

    def test_opnieuw_inloggen_met_wachtwoord_wist_de_bevestiging(self):
        client, geheim, _ = self.schakel_in()
        self.assertEqual(client.get("/beheer/").status_code, 200)
        client.post("/beheer/inloggen/", {"username": self.staff.email, "password": PASSWORD})
        self.assertEqual(client.get("/beheer/").status_code, 302)

    def test_geknoeide_sessiewaarde_helpt_niet(self):
        _, geheim, _ = self.schakel_in()
        client = self.login(Client())
        sessie = client.session
        sessie[tweestaps.SESSION_KEY] = "x" * 64
        sessie.save()
        self.assertEqual(client.get("/beheer/").status_code, 302)

    def test_uitloggen_werkt_zonder_code(self):
        _, geheim, _ = self.schakel_in()
        client = self.login(Client())
        client.post(reverse("accounts:logout"))
        self.assertEqual(client.get("/beheer/").status_code, 302)
        self.assertIn("/beheer/inloggen/", client.get("/beheer/")["Location"])

    def test_verplicht_stuurt_medewerker_zonder_2fa_naar_instellen(self):
        with override_settings(TWOFA_REQUIRED=True):
            client = self.login()
            for pad in ("/beheer/", ADMIN):
                response = client.get(pad)
                self.assertEqual(response.status_code, 302, pad)
                self.assertTrue(response["Location"].startswith("/beheer/2fa/instellen/"), pad)
            self.assertFalse(client.get("/").context["user"].is_authenticated)
            # na instellen weer toegang
            client.get("/beheer/2fa/instellen/")
            geheim = tweestaps.ontsleutel(client.session[tweestaps.SESSION_PENDING])
            client.post("/beheer/2fa/instellen/", {"code": self.code(geheim)})
            self.assertEqual(client.get("/beheer/").status_code, 200)

    def test_klanten_en_gasten_merken_niets(self):
        _, geheim, _ = self.schakel_in()
        klant = Client()
        klant.force_login(self.make_customer())
        self.assertEqual(klant.get("/account/").status_code, 200)
        self.assertEqual(Client().get("/").status_code, 200)
        self.assertEqual(klant.get("/beheer/").status_code, 404)


class CodeControleTests(TweestapsBase):
    def test_zelfde_code_werkt_niet_twee_keer(self):
        _, geheim, _ = self.schakel_in()
        self.stap += 1
        eerste = self.login()
        gebruikt = self.code(geheim)
        self.assertEqual(eerste.post("/beheer/2fa/controle/", {"code": gebruikt}).status_code, 302)
        tweede = self.login()
        response = tweede.post("/beheer/2fa/controle/", {"code": gebruikt})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "klopt niet of is al gebruikt")
        self.assertEqual(tweede.get("/beheer/").status_code, 302)

    def test_code_van_eerdere_periode_na_een_nieuwere_werkt_niet(self):
        _, geheim, _ = self.schakel_in()
        self.stap += 2
        client = self.login()
        client.post("/beheer/2fa/controle/", {"code": self.code(geheim)})
        oudere = self.code(geheim, self.stap - 1)
        andere = self.login()
        self.assertEqual(andere.post("/beheer/2fa/controle/", {"code": oudere}).status_code, 200)

    def test_na_vijf_foute_codes_is_ook_de_juiste_code_geblokkeerd(self):
        _, geheim, _ = self.schakel_in()
        self.stap += 1
        client = self.login()
        for _ in range(tweestaps.USER_FAILURES):
            self.assertEqual(client.post("/beheer/2fa/controle/", {"code": "000000"}).status_code, 200)
        response = client.post("/beheer/2fa/controle/", {"code": self.code(geheim)})
        self.assertEqual(response.status_code, 429)
        self.assertContains(response, "Te veel pogingen", status_code=429)
        self.assertEqual(client.get("/beheer/").status_code, 302)

    def test_teller_van_codes_raakt_de_wachtwoordblokkade_niet(self):
        _, geheim, _ = self.schakel_in()
        self.stap += 1
        client = self.login()
        for _ in range(tweestaps.USER_FAILURES + 1):
            client.post("/beheer/2fa/controle/", {"code": "000000"})
        # Wachtwoord inloggen blijft mogelijk (de code-teller bereikt een aanvaller zonder wachtwoord nooit).
        self.assertEqual(Client().post("/beheer/inloggen/", {"username": self.staff.email, "password": PASSWORD}).status_code, 302)

    def test_zonder_wachtwoord_is_de_codestap_onbereikbaar(self):
        _, geheim, _ = self.schakel_in()
        anoniem = Client()
        response = anoniem.post("/beheer/2fa/controle/", {"code": self.code(geheim)})
        self.assertEqual(response.status_code, 302)
        self.assertIn("/beheer/inloggen/", response["Location"])

    def test_herstelcode_werkt_een_keer(self):
        _, geheim, codes = self.schakel_in()
        client = self.login()
        response = client.post("/beheer/2fa/controle/", {"code": codes[0].upper()})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(client.get("/beheer/").status_code, 200)
        self.assertEqual(tweestaps.herstelcodes_over(self.staff), 9)
        opnieuw = self.login()
        self.assertEqual(opnieuw.post("/beheer/2fa/controle/", {"code": codes[0]}).status_code, 200)
        self.assertEqual(opnieuw.get("/beheer/").status_code, 302)

    def test_herstelcode_zonder_streepjes_en_met_spaties(self):
        _, geheim, codes = self.schakel_in()
        client = self.login()
        response = client.post("/beheer/2fa/controle/", {"code": " " + codes[3].replace("-", " ") + " "})
        self.assertEqual(response.status_code, 302)

    def test_foute_herstelcode_telt_mee_in_de_begrenzing(self):
        _, geheim, codes = self.schakel_in()
        client = self.login()
        for _ in range(tweestaps.USER_FAILURES):
            client.post("/beheer/2fa/controle/", {"code": "aaaa-bbbb-cccc"})
        self.assertEqual(client.post("/beheer/2fa/controle/", {"code": codes[0]}).status_code, 429)

    def test_herstelcodes_van_een_ander_account_werken_niet(self):
        _, geheim, codes = self.schakel_in()
        ander = User.objects.create_superuser(email="ander@example.com", password=PASSWORD)
        client = Client()
        client.post("/beheer/inloggen/", {"username": ander.email, "password": PASSWORD})
        ander_geheim = tweestaps.nieuw_geheim()
        TwoFactor.objects.create(user=ander, secret_enc=tweestaps.versleutel(ander_geheim), confirmed_at=ander.date_joined)
        self.assertEqual(client.post("/beheer/2fa/controle/", {"code": codes[0]}).status_code, 200)


class BeherenTests(TweestapsBase):
    def test_nieuwe_herstelcodes_vragen_een_verse_code_en_vervangen_de_oude(self):
        client, geheim, codes = self.schakel_in()
        response = client.post("/beheer/2fa/", {"actie": "nieuwe_codes", "code": "000000"})
        self.assertContains(response, "klopt niet")
        self.stap += 1
        response = client.post("/beheer/2fa/", {"actie": "nieuwe_codes", "code": self.code(geheim)})
        nieuwe = response.context["codes"]
        self.assertEqual(len(nieuwe), 10)
        self.assertFalse(set(nieuwe) & set(codes))
        self.assertEqual(RecoveryCode.objects.count(), 10)
        sessie = self.login()
        self.assertEqual(sessie.post("/beheer/2fa/controle/", {"code": codes[0]}).status_code, 200)

    def test_uitzetten_vraagt_een_code_en_kan_niet_als_verplicht(self):
        client, geheim, _ = self.schakel_in()
        self.stap += 1
        with override_settings(TWOFA_REQUIRED=True):
            self.assertEqual(client.post("/beheer/2fa/", {"actie": "uitzetten", "code": self.code(geheim)}).status_code, 404)
        self.assertTrue(TwoFactor.objects.exists())
        client.post("/beheer/2fa/", {"actie": "uitzetten", "code": "000000"})
        self.assertTrue(TwoFactor.objects.exists())
        client.post("/beheer/2fa/", {"actie": "uitzetten", "code": self.code(geheim)})
        self.assertFalse(TwoFactor.objects.exists())
        self.assertFalse(RecoveryCode.objects.exists())

    def test_beheren_zonder_bevestigde_sessie_stuurt_naar_de_code(self):
        _, geheim, _ = self.schakel_in()
        client = self.login(Client())
        self.assertTrue(client.post("/beheer/2fa/", {"actie": "uitzetten", "code": "1"})["Location"].startswith("/beheer/2fa/controle/"))
        self.assertTrue(TwoFactor.objects.exists())


class NoodprocedureTests(TweestapsBase):
    def run_cmd(self, *args):
        out = StringIO()
        call_command("reset_2fa", *args, stdout=out)
        return out.getvalue()

    def test_zonder_bevestig_gebeurt_er_niets(self):
        self.schakel_in()
        self.assertIn("--bevestig", self.run_cmd(self.staff.email))
        self.assertTrue(TwoFactor.objects.exists())

    def test_reset_verwijdert_2fa_codes_en_sessies_van_alleen_dat_account(self):
        client, geheim, _ = self.schakel_in()
        ander = User.objects.create_superuser(email="ander@example.com", password=PASSWORD)
        anders_client = Client()
        anders_client.post("/beheer/inloggen/", {"username": ander.email, "password": PASSWORD})
        self.run_cmd(self.staff.email.upper(), "--bevestig")
        self.assertFalse(TwoFactor.objects.exists())
        self.assertFalse(RecoveryCode.objects.exists())
        self.assertEqual(client.get("/beheer/").status_code, 302)           # sessie beëindigd
        self.assertEqual(anders_client.get("/beheer/").status_code, 200)    # andere sessies blijven
        self.assertEqual(self.login().get("/beheer/").status_code, 200)     # wachtwoord volstaat weer (2FA niet verplicht)
        self.assertTrue(User.objects.get(pk=self.staff.pk).is_superuser)

    def test_geen_klantaccount_of_onbekend_adres(self):
        self.make_customer()
        with self.assertRaises(CommandError):
            self.run_cmd("klant@example.com", "--bevestig")
        with self.assertRaises(CommandError):
            self.run_cmd("bestaat-niet@example.com", "--bevestig")

    def test_reset_bij_verplicht_dwingt_opnieuw_instellen(self):
        self.schakel_in()
        self.run_cmd(self.staff.email, "--bevestig")
        with override_settings(TWOFA_REQUIRED=True):
            client = self.login()
            self.assertTrue(client.get("/beheer/")["Location"].startswith("/beheer/2fa/instellen/"))


class SysteemcontroleTests(VaylideTestCase):
    def test_check_meldt_verplicht_zonder_sleutel_en_ongeldige_sleutel(self):
        from core.checks import tweestaps_sleutel

        with override_settings(TWOFA_KEYS=[], TWOFA_REQUIRED=True):
            self.assertEqual([m.id for m in tweestaps_sleutel(None)], ["vaylide.E004"])
        with override_settings(TWOFA_KEYS=["geen-sleutel"], TWOFA_REQUIRED=False):
            self.assertEqual([m.id for m in tweestaps_sleutel(None)], ["vaylide.E003"])
        with override_settings(TWOFA_KEYS=[Fernet.generate_key().decode()], TWOFA_REQUIRED=True):
            self.assertEqual(tweestaps_sleutel(None), [])
        with override_settings(TWOFA_KEYS=[], TWOFA_REQUIRED=False):
            self.assertEqual(tweestaps_sleutel(None), [])

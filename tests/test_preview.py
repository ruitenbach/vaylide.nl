"""Optioneel wachtwoord voor de hele site (VIERLIEF_PREVIEW_PASSWORD), voor een testversie die online staat."""
import base64

from django.core.cache import cache
from django.test import Client, override_settings

from .helpers import VaylideTestCase


def basic(user: str, password: str) -> dict:
    return {"HTTP_AUTHORIZATION": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()}


class PreviewPasswordTests(VaylideTestCase):
    def setUp(self):
        cache.clear()

    def test_off_by_default(self):
        self.assertEqual(Client().get("/").status_code, 200)

    @override_settings(PREVIEW_PASSWORD="lang-en-geheim-wachtwoord", PREVIEW_USER="voorbeeld")
    def test_pages_need_the_password(self):
        for url in ("/", "/ontwerpen/", "/voorbeeld/stipjes/", "/inloggen/", "/beheer/inloggen/"):
            response = Client().get(url)
            self.assertEqual(response.status_code, 401, url)
            self.assertTrue(response["WWW-Authenticate"].startswith("Basic "), url)
            self.assertNotIn("VAYLIDE", response.content.decode(), url)
        self.assertEqual(Client().get("/", **basic("voorbeeld", "fout")).status_code, 401)
        self.assertEqual(Client().get("/", **basic("iemand", "lang-en-geheim-wachtwoord")).status_code, 401)
        self.assertEqual(Client().get("/", HTTP_AUTHORIZATION="Basic !!geen-base64!!").status_code, 401)
        ok = Client().get("/", **basic("voorbeeld", "lang-en-geheim-wachtwoord"))
        self.assertEqual(ok.status_code, 200)
        self.assertContains(ok, "VAYLIDE")

    @override_settings(PREVIEW_PASSWORD="lang-en-geheim-wachtwoord")
    def test_health_check_and_cron_stay_reachable(self):
        self.assertEqual(Client().get("/healthz").status_code, 200)
        cron = Client().post("/intern/taken/")
        self.assertNotIn("WWW-Authenticate", cron)

    @override_settings(PREVIEW_PASSWORD="lang-en-geheim-wachtwoord")
    def test_too_many_wrong_attempts_are_slowed_down(self):
        client = Client()
        codes = [client.get("/", **basic("voorbeeld", f"poging-{i}")).status_code for i in range(32)]
        self.assertEqual(codes[:30], [401] * 30)
        self.assertEqual(codes[-1], 429)

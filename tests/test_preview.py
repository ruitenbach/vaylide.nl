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

    @override_settings(PREVIEW_PASSWORD="lang-en-geheim-wachtwoord", PREVIEW_OPEN_PUBLIC=True)
    def test_only_information_pages_open_for_a_website_review(self):
        from django.conf import settings

        public = ("/", "/ontwerpen/", "/ontwerpen/stipjes/", "/zo-werkt-het/", "/prijzen/", "/veelgestelde-vragen/",
                  "/over-ons/", "/contact/", "/privacy/", "/voorwaarden/", "/voorwaarden/pdf/2026-09-29/", "/herroepen/",
                  "/voorbeeld/stipjes/", "/zoeken/?q=bruiloft")
        for url in public:
            response = Client().get(url)
            self.assertIn(response.status_code, (200, 302), url)
            self.assertEqual(response["X-Robots-Tag"], "noindex, nofollow, noarchive", url)
            html = response.content.decode(errors="ignore")
            self.assertNotIn(settings.ADMIN_URL.strip("/"), html, url)
            self.assertNotIn('href="/beheer/', html, url)
            self.assertNotIn("test-code", html, url)
        self.assertIn("Testomgeving", Client().get("/").content.decode())
        invitation = self.published()
        order = invitation.orders.first()
        protected = ("/inloggen/", "/inloggen/code/", "/maken/", "/account/", "/beheer/", "/beheer/inloggen/",
                     f"/{settings.ADMIN_URL}", f"/u/{invitation.slug}/", f"/bestelling/{order.uid}/", "/betalen/test/x/")
        for url in protected:
            self.assertEqual(Client().get(url).status_code, 401, url)
        for url in ("/contact/", "/herroepen/", "/zoeken/"):
            self.assertEqual(Client().post(url, {"name": "x"}).status_code, 401, url)
        robots = Client().get("/robots.txt").content.decode()
        self.assertEqual(robots, "User-agent: *\nDisallow: /\n")
        # Zonder slot-slash: doorsturen naar de open pagina (zoals een controlerobot ze opvraagt), niet 401.
        for url in ("/prijzen", "/ontwerpen", "/zo-werkt-het", "/inspiratie"):
            response = Client().get(url)
            self.assertEqual(response.status_code, 301, url)
            self.assertEqual(response["Location"], url + "/", url)
        for url in ("/maken", "/account", "/beheer", "/inloggen"):
            self.assertEqual(Client().get(url).status_code, 401, url)

    def test_robots_does_not_reveal_the_admin_path(self):
        from django.conf import settings

        self.assertNotIn(settings.ADMIN_URL.strip("/"), Client().get("/robots.txt").content.decode())

    @override_settings(PREVIEW_PASSWORD="lang-en-geheim-wachtwoord")
    def test_too_many_wrong_attempts_are_slowed_down(self):
        client = Client()
        codes = [client.get("/", **basic("voorbeeld", f"poging-{i}")).status_code for i in range(32)]
        self.assertEqual(codes[:30], [401] * 30)
        self.assertEqual(codes[-1], 429)

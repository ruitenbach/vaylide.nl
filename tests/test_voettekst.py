"""Voettekst: betaalmethoden (uit Mollie of de instelling) en links naar Instagram en TikTok (alleen als ingevuld)."""
import json
from unittest import mock

from django.core.cache import cache
from django.test import Client, override_settings

from core.models import SiteConfig
from orders.methods import available_methods

from .helpers import VaylideTestCase


class _Response:
    def __init__(self, payload):
        self.payload = json.dumps(payload).encode()

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class PaymentMethodsTests(VaylideTestCase):
    def setUp(self):
        cache.clear()

    def test_footer_shows_ideal_and_paypal_by_default(self):
        html = Client().get("/").content.decode()
        footer = html[html.index('<footer class="site-footer">'):]
        self.assertIn("Veilig betalen met", footer)
        self.assertIn('alt="iDEAL"', footer)
        self.assertIn("img/betalen/ideal.webp", footer)
        self.assertIn('alt="PayPal"', footer)
        self.assertIn("img/betalen/paypal.webp", footer)
        self.assertLess(footer.index("iDEAL"), footer.index("PayPal"))

    def test_with_mollie_only_the_enabled_methods_are_shown(self):
        mollie = override_settings(PAYMENT_PROVIDER="mollie", MOLLIE_API_KEY="test_nagebootst")
        mollie.enable()
        self.addCleanup(mollie.disable)
        answer = {"_embedded": {"methods": [{"id": "paypal"}, {"id": "ideal"}, {"id": "applepay"}, {"id": "creditcard"}, {"id": "klarna"}, {"id": "riverty"}]}}
        with mock.patch("orders.providers.urllib.request.urlopen", return_value=_Response(answer)) as urlopen:
            # Alleen wat de eigenaar wil tonen (iDEAL, creditcard, PayPal), ook als er in Mollie meer aanstaat.
            self.assertEqual([m["label"] for m in available_methods()], ["iDEAL", "PayPal", "Creditcard"])
            available_methods()  # uit de cache
            self.assertEqual(urlopen.call_count, 1)
            self.assertIn("/methods", urlopen.call_args[0][0].full_url)

    def test_mollie_outage_falls_back_to_the_setting(self):
        import urllib.error

        mollie = override_settings(PAYMENT_PROVIDER="mollie", MOLLIE_API_KEY="test_nagebootst", PAYMENT_METHODS=["ideal", "paypal"])
        mollie.enable()
        self.addCleanup(mollie.disable)
        with mock.patch("orders.providers.urllib.request.urlopen", side_effect=urllib.error.URLError("weg")):
            self.assertEqual([m["id"] for m in available_methods()], ["ideal", "paypal"])
            self.assertEqual(Client().get("/").status_code, 200)


class SocialLinksTests(VaylideTestCase):
    def test_instagram_of_vaylide_is_set_by_default(self):
        html = Client().get("/").content.decode()
        self.assertIn('href="https://www.instagram.com/vaylidenl/"', html)
        self.assertNotIn("utm_source", html)

    def test_no_icons_without_a_link(self):
        config = SiteConfig.get()
        config.instagram_url = ""
        config.save()
        html = Client().get("/").content.decode()
        self.assertNotIn("sociale-links", html)

    def test_instagram_and_tiktok_icons_when_filled_in(self):
        config = SiteConfig.get()
        config.instagram_url = "https://www.instagram.com/voorbeeldaccount/"
        config.tiktok_url = "https://www.tiktok.com/@voorbeeldaccount"
        config.save()
        html = Client().get("/prijzen/").content.decode()
        self.assertIn('href="https://www.instagram.com/voorbeeldaccount/"', html)
        self.assertIn('aria-label="VAYLIDE op Instagram"', html)
        self.assertIn('href="https://www.tiktok.com/@voorbeeldaccount"', html)
        self.assertIn('aria-label="VAYLIDE op TikTok"', html)
        self.assertIn('rel="noopener me"', html)

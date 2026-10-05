"""Voettekst: betaalmethoden (uit Mollie of de instelling) en de links naar de officiële profielen (Instagram, Facebook, TikTok, LinkedIn)."""
import json
import re
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
            # Ook een oudere bewaarde lijst (van vóór de keuze van de eigenaar) toont alleen de toegestane methoden.
            from django.core.cache import cache

            cache.set("betaalmethoden:v2:test_", [{"id": "ideal"}, {"id": "klarna"}, {"id": "paybybank"}, {"id": "creditcard"}], 60)
            self.assertEqual([m["id"] for m in available_methods()], ["ideal", "creditcard"])
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
    URLS = [
        ("Instagram", "https://www.instagram.com/vaylidenl/"),
        ("Facebook", "https://www.facebook.com/profile.php?id=61594950397795"),
        ("TikTok", "https://www.tiktok.com/@vaylidenl"),
        ("LinkedIn", "https://www.linkedin.com/company/vaylide/"),
    ]

    def test_voettekst_toont_de_vier_officiele_profielen_in_vaste_volgorde(self):
        for pad in ("/", "/prijzen/"):
            html = Client().get(pad).content.decode()
            blok = html.split('class="sociale-links"')[1].split("</ul>")[0]
            links = re.findall(r'<a href="([^"]+)"[^>]*>', blok)
            self.assertEqual(links, [url for _naam, url in self.URLS], pad)
            self.assertNotIn("utm_", blok)

    def test_elke_link_opent_in_een_nieuw_tabblad_veilig_en_met_duidelijk_label(self):
        html = Client().get("/").content.decode()
        for naam, url in self.URLS:
            tag = re.search(rf'<a href="{re.escape(url)}"[^>]*>', html).group(0)
            self.assertIn('target="_blank"', tag, naam)
            self.assertIn('rel="noopener noreferrer"', tag, naam)
            self.assertIn(f'aria-label="VAYLIDE op {naam} (opent in een nieuw tabblad)"', tag, naam)

    def test_beheer_instellingen_veranderen_de_officiele_links_niet(self):
        config = SiteConfig.get()
        config.instagram_url = "https://www.instagram.com/ergens-anders/"
        config.tiktok_url = ""
        config.save()
        html = Client().get("/").content.decode()
        self.assertIn('href="https://www.instagram.com/vaylidenl/"', html)
        self.assertIn('href="https://www.tiktok.com/@vaylidenl"', html)
        self.assertNotIn("ergens-anders", html)

    def test_zelfde_lijst_staat_in_de_gestructureerde_gegevens(self):
        from core import seo, social

        self.assertEqual(seo.organization()["sameAs"], [url for _naam, url in self.URLS])
        self.assertEqual(social.same_as(), [l["url"] for l in social.social_links()])

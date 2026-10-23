"""Cloudflare-bewuste IP-herkenning: de bezoeker staat één plaats links van het Cloudflare-adres dat Render achteraan zet."""
from django.core.cache import cache
from django.test import Client, override_settings

from core import ipinfo
from core.utils import ip_fingerprint, reliable_ip_fingerprint

from .helpers import VaylideTestCase, old_form_ts
from .test_beveiliging_fase1 import make_request

CF = "104.16.0.5"          # gepubliceerd Cloudflare-bereik


@override_settings(TRUSTED_PROXY_HOPS=1)
class CloudflareKetenTests(VaylideTestCase):
    def setUp(self):
        cache.clear()
        ipinfo._warned_at.clear()

    def test_visitor_is_found_left_of_cloudflare(self):
        r = make_request(f"81.107.0.5, {CF}")
        self.assertEqual(ipinfo.client_ip(r), "81.107.0.5")
        self.assertTrue(ipinfo.assess(r).reliable)

    def test_forged_entries_further_left_never_count(self):
        r = make_request(f"6.6.6.6, 7.7.7.7, 81.107.0.5, {CF}")
        self.assertEqual(ipinfo.client_ip(r), "81.107.0.5")

    def test_direct_to_origin_with_forged_cloudflare_entry_does_not_help(self):
        # Zonder Cloudflare voegt Render het echte adres rechts toe: een vervalst Cloudflare-adres links telt niet.
        r = make_request(f"{CF}, 81.107.0.9")
        self.assertEqual(ipinfo.client_ip(r), "81.107.0.9")
        self.assertTrue(ipinfo.assess(r).reliable)

    def test_direct_to_origin_with_forged_visitor_is_not_used(self):
        r = make_request("6.6.6.6, 81.107.0.9")
        self.assertEqual(ipinfo.client_ip(r), "81.107.0.9")

    def test_cloudflare_with_nothing_left_stays_unreliable(self):
        r = make_request(CF)
        self.assertFalse(ipinfo.assess(r).reliable)
        self.assertEqual(ipinfo.assess(r).reason, "cloudflare")

    def test_cloudflare_left_of_cloudflare_is_unreliable(self):
        r = make_request(f"172.71.10.1, {CF}")
        self.assertFalse(ipinfo.assess(r).reliable)

    def test_private_visitor_entry_is_unreliable(self):
        self.assertFalse(ipinfo.assess(make_request(f"10.1.2.3, {CF}")).reliable)

    def test_garbage_visitor_entry_is_unreliable_and_falls_back(self):
        r = make_request(f"geen-ip, {CF}", remote="10.0.0.1")
        self.assertFalse(ipinfo.assess(r).reliable)

    def test_forged_headers_still_ignored(self):
        r = make_request(f"81.107.0.5, {CF}", cf_connecting_ip="9.9.9.9", true_client_ip="8.8.8.8", x_real_ip="7.7.7.7")
        self.assertEqual(ipinfo.client_ip(r), "81.107.0.5")

    def test_different_visitors_get_different_fingerprints(self):
        a = ip_fingerprint(make_request(f"81.107.0.5, {CF}"))
        b = ip_fingerprint(make_request(f"81.107.0.6, {CF}"))
        self.assertNotEqual(a, b)
        self.assertIsNotNone(reliable_ip_fingerprint(make_request(f"81.107.0.5, {CF}")))

    def test_twenty_guests_behind_one_cloudflare_address_are_not_blocked(self):
        inv = self.published()
        codes = []
        for i in range(20):
            c = Client()
            xff = f"81.107.1.{i + 1}, {CF}"
            page = c.get(f"/u/{inv.slug}/", HTTP_X_FORWARDED_FOR=xff)
            import re
            m = re.search(r'name="client_token" value="([^"]+)"', page.content.decode())
            r = c.post(f"/u/{inv.slug}/aanmelden/", {"client_token": m.group(1), "form_ts": old_form_ts(), "name": f"Gast {i}",
                                                     "attending": "ja", "party_size": "1"}, HTTP_ACCEPT="application/json", HTTP_X_FORWARDED_FOR=xff)
            codes.append(r.status_code)
        self.assertEqual(codes, [200] * 20)

    def test_one_visitor_is_still_limited_after_15(self):
        inv = self.published()
        codes = []
        xff = f"81.107.1.77, {CF}"
        for i in range(18):
            c = Client()
            page = c.get(f"/u/{inv.slug}/", HTTP_X_FORWARDED_FOR=xff)
            import re
            m = re.search(r'name="client_token" value="([^"]+)"', page.content.decode())
            r = c.post(f"/u/{inv.slug}/aanmelden/", {"client_token": m.group(1), "form_ts": old_form_ts(), "name": f"Bot {i}",
                                                     "attending": "ja", "party_size": "1"}, HTTP_ACCEPT="application/json", HTTP_X_FORWARDED_FOR=xff)
            codes.append(r.status_code)
        self.assertEqual(codes[:15], [200] * 15)
        self.assertEqual(set(codes[15:]), {429})


@override_settings(TRUSTED_PROXY_HOPS=1)
class AanvalTests(VaylideTestCase):
    """Een bezoeker kan met zelf meegestuurde headers niet kiezen welk adres de limieten zien."""

    def setUp(self):
        cache.clear()
        ipinfo._warned_at.clear()

    def test_fingerprint_does_not_change_with_forged_left_entries(self):
        real = ip_fingerprint(make_request(f"81.107.0.5, {CF}"))
        for forged in ("6.6.6.6, ", "10.1.2.3, ", f"{CF}, ", "geen-ip, ", "1.1.1.1, 2.2.2.2, 3.3.3.3, ", ", "):
            self.assertEqual(ip_fingerprint(make_request(f"{forged}81.107.0.5, {CF}")), real, forged)

    def test_own_cloudflare_proxy_is_not_trusted_as_a_visitor(self):
        # Een bezoeker die via een eigen Cloudflare-proxy komt: Render ziet een Cloudflare-adres als verbinding, dus
        # staat er links van Render-Cloudflare weer een Cloudflare-adres. Dat telt niet als bezoeker.
        r = make_request(f"6.6.6.6, 172.71.10.1, {CF}")
        status = ipinfo.assess(r)
        self.assertFalse(status.reliable)
        self.assertEqual(status.reason, "cloudflare")
        self.assertIsNone(reliable_ip_fingerprint(r))

    def test_forged_visitor_headers_are_never_a_source(self):
        r = make_request(f"81.107.0.5, {CF}", cf_connecting_ip="6.6.6.6", true_client_ip="6.6.6.6", x_real_ip="6.6.6.6", forwarded="for=6.6.6.6")
        self.assertEqual(ipinfo.client_ip(r), "81.107.0.5")

    def test_without_proxy_chain_nothing_is_trusted(self):
        for xff in (None, "", "6.6.6.6"):
            with override_settings(TRUSTED_PROXY_HOPS=1):
                status = ipinfo.assess(make_request(xff, remote="10.0.0.1"))
            self.assertTrue(status.reliable if xff == "6.6.6.6" else not status.reliable, xff)

    def test_rsvp_limit_holds_when_one_visitor_forges_the_left_side(self):
        inv = self.published()
        codes = []
        import re
        for i in range(18):
            c = Client()
            xff = f"{i + 1}.{i + 1}.{i + 1}.{i + 1}, 81.107.0.5, {CF}"
            page = c.get(f"/u/{inv.slug}/", HTTP_X_FORWARDED_FOR=xff)
            m = re.search(r'name="client_token" value="([^"]+)"', page.content.decode())
            r = c.post(f"/u/{inv.slug}/aanmelden/", {"client_token": m.group(1), "form_ts": old_form_ts(), "name": f"Bot {i}",
                                                     "attending": "ja", "party_size": "1"}, HTTP_ACCEPT="application/json", HTTP_X_FORWARDED_FOR=xff)
            codes.append(r.status_code)
        self.assertEqual(codes[:15], [200] * 15)
        self.assertEqual(set(codes[15:]), {429})

    def test_preview_wall_limit_holds_when_the_left_side_is_forged(self):
        with override_settings(PREVIEW_PASSWORD="geheim"):
            codes = [Client().get("/", HTTP_X_FORWARDED_FOR=f"{i + 1}.9.9.9, 81.107.0.5, {CF}").status_code for i in range(34)]
            other = Client().get("/", HTTP_X_FORWARDED_FOR=f"81.107.0.77, {CF}").status_code
        self.assertEqual(codes[:30], [401] * 30)
        self.assertEqual(set(codes[30:]), {429})
        self.assertEqual(other, 401)      # een andere bezoeker achter hetzelfde Cloudflare-adres is niet geblokkeerd

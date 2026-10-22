"""Beveiliging fase 1: veilige standaardmodus, raden van links, wachtwoord raden en client-IP."""
import os
import subprocess
import sys
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest
from django.test import Client, override_settings

from core.utils import client_ip, ip_fingerprint

from .helpers import VaylideTestCase

BASE = Path(settings.BASE_DIR)


def run_settings(env_extra: dict, *, drop=("VIERLIEF_MODE",)) -> subprocess.CompletedProcess:
    """Laadt de instellingen in een apart proces met een schone omgeving (zonder .env)."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("VIERLIEF_", "RENDER", "DJANGO_"))}
    env.update({"VIERLIEF_SKIP_DOTENV": "1", "VIERLIEF_ALLOW_DEV_SECRET": "true", "PYTHONPATH": str(BASE)})
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-c", "import config.settings as s; print('MODE=' + s.VIERLIEF_MODE, 'TEST=' + str(s.TEST_MODE))"],
        env=env, cwd=BASE, capture_output=True, text=True,
    )


class ModeDefaultTests(VaylideTestCase):
    def test_missing_mode_locally_stays_test(self):
        result = run_settings({})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("TEST=True", result.stdout)

    def test_missing_mode_on_render_refuses_to_start(self):
        result = run_settings({"RENDER": "true"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("VIERLIEF_MODE ontbreekt", result.stderr)

    def test_missing_mode_with_https_base_url_refuses_to_start(self):
        result = run_settings({"VIERLIEF_BASE_URL": "https://www.vaylide.nl"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("VIERLIEF_MODE ontbreekt", result.stderr)

    def test_explicit_test_mode_on_render_still_starts(self):
        result = run_settings({"RENDER": "true", "VIERLIEF_MODE": "test"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("TEST=True", result.stdout)

    def test_invalid_or_empty_mode_refuses_to_start(self):
        for value in ("", "prod", "Livee"):
            result = run_settings({"VIERLIEF_MODE": value})
            self.assertNotEqual(result.returncode, 0, value)

    def test_live_still_requires_real_providers(self):
        result = run_settings({"VIERLIEF_MODE": "live", "RENDER": "true"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Live-modus", result.stderr)


class SlugProbingTests(VaylideTestCase):
    def setUp(self):
        cache.clear()
        self.owner = self.make_customer()
        self.inv = self.published(owner=self.owner)

    def probe(self, client, n, **extra):
        return [client.get(f"/u/geenbestaand-{i:08d}/", **extra).status_code for i in range(n)]

    def test_existing_links_keep_working_and_do_not_count(self):
        c = Client()
        for _ in range(100):
            self.assertEqual(c.get(self.inv.public_path).status_code, 200)
        # De bestaande link telt niet mee: onbekende adressen kunnen nog steeds 404 geven.
        self.assertEqual(c.get("/u/onbekend-12345678/").status_code, 404)

    def test_many_misses_get_429_then_valid_link_is_also_held_back(self):
        c = Client()
        codes = self.probe(c, 65)
        self.assertEqual(set(codes[:60]), {404})
        self.assertEqual(set(codes[60:]), {429})
        blocked = c.get(self.inv.public_path)
        self.assertEqual(blocked.status_code, 429)
        self.assertIn("Retry-After", blocked)
        self.assertEqual(c.get(f"/u/{self.inv.slug}/agenda.ics").status_code, 429)

    def test_other_visitor_is_not_blocked(self):
        self.probe(Client(), 70, REMOTE_ADDR="198.51.100.1")
        other = Client()
        self.assertEqual(other.get(self.inv.public_path, REMOTE_ADDR="198.51.100.2").status_code, 200)

    def test_shared_ip_guests_with_valid_and_expired_links_are_never_blocked(self):
        # 300 gasten op één netwerk met een bestaande link, en 100 met een offline gehaalde (410): geen misser.
        offline = self.published(owner=self.make_customer("ander@example.com"))
        offline.status = offline.Status.OFFLINE
        offline.save()
        c = Client()
        for _ in range(300):
            self.assertEqual(c.get(self.inv.public_path).status_code, 200)
        for _ in range(100):
            self.assertEqual(c.get(offline.public_path).status_code, 410)
        self.assertEqual(c.get(self.inv.public_path).status_code, 200)

    def test_shared_ip_with_a_few_typos_is_fine(self):
        c = Client()
        self.assertEqual(set(self.probe(c, 20)), {404})
        self.assertEqual(c.get(self.inv.public_path).status_code, 200)

    def test_block_ends_with_the_window(self):
        c = Client()
        self.probe(c, 65)
        cache.clear()  # nabootsing van het verstrijken van het venster
        self.assertEqual(c.get(self.inv.public_path).status_code, 200)

    def test_rsvp_post_to_unknown_slug_counts_and_json_gets_429(self):
        c = Client()
        for i in range(60):
            c.post(f"/u/nope-{i:08d}/aanmelden/", {}, HTTP_ACCEPT="application/json")
        r = c.post(f"/u/nope-x/aanmelden/", {}, HTTP_ACCEPT="application/json")
        self.assertEqual(r.status_code, 429)
        self.assertFalse(r.json()["ok"])

    def test_existing_qr_urls_unchanged(self):
        self.assertRegex(self.inv.public_url, r"^https://vaylide\.test/u/[a-z0-9-]+-[a-z2-9]{8}/$")

    def test_spoofed_forwarded_for_does_not_reset_the_limit(self):
        with override_settings(TRUSTED_PROXY_HOPS=1):
            c = Client()
            for i in range(65):
                c.get(f"/u/geenbestaand-{i:08d}/", HTTP_X_FORWARDED_FOR=f"10.1.1.{i % 250}, 203.0.113.7")
            r = c.get(self.inv.public_path, HTTP_X_FORWARDED_FOR="10.9.9.9, 203.0.113.7")
            self.assertEqual(r.status_code, 429)


class StaffBruteForceTests(VaylideTestCase):
    PASSWORD = "Een-lang-wachtwoord-2026"

    def setUp(self):
        cache.clear()
        self.staff = self.make_staff("eigenaar@example.com", self.PASSWORD)

    def beheer_login(self, c, password, email="eigenaar@example.com", **extra):
        return c.post("/beheer/inloggen/", {"username": email, "password": password}, **extra)

    def admin_login(self, c, password, email="eigenaar@example.com", **extra):
        return c.post(f"/{settings.ADMIN_URL}login/", {"username": email, "password": password, "next": f"/{settings.ADMIN_URL}"}, **extra)

    def test_correct_password_works_after_a_few_failures(self):
        for login in (self.beheer_login, self.admin_login):
            cache.clear()
            c = Client()
            for _ in range(3):
                login(c, "fout-wachtwoord-1")
            self.assertEqual(login(c, self.PASSWORD).status_code, 302, login.__name__)

    def test_beheer_blocks_after_ten_failures_even_with_right_password(self):
        c = Client()
        for _ in range(10):
            self.assertEqual(self.beheer_login(c, "fout-wachtwoord-1").status_code, 200)
        r = self.beheer_login(c, self.PASSWORD)
        self.assertEqual(r.status_code, 429)
        self.assertNotIn("_auth_user_id", c.session)

    def test_admin_blocks_after_ten_failures_even_with_right_password(self):
        c = Client()
        for _ in range(10):
            self.assertEqual(self.admin_login(c, "fout-wachtwoord-1").status_code, 200)
        r = self.admin_login(c, self.PASSWORD)
        self.assertEqual(r.status_code, 429)
        self.assertIn("Retry-After", r)
        self.assertNotIn("_auth_user_id", c.session)

    def test_blocks_are_shared_between_admin_and_beheer(self):
        c = Client()
        for _ in range(10):
            self.admin_login(c, "fout-wachtwoord-1")
        self.assertEqual(self.beheer_login(c, self.PASSWORD).status_code, 429)

    def test_distributed_attack_on_one_account_is_stopped_per_account(self):
        with override_settings(TRUSTED_PROXY_HOPS=1):
            for i in range(10):
                self.beheer_login(Client(), "fout-wachtwoord-1", HTTP_X_FORWARDED_FOR=f"203.0.113.{i + 1}")
            r = self.beheer_login(Client(), self.PASSWORD, HTTP_X_FORWARDED_FOR="203.0.113.200")
            self.assertEqual(r.status_code, 429)

    def test_attacker_on_one_ip_does_not_lock_other_accounts_from_other_ips(self):
        other = self.make_staff("tweede@example.com", self.PASSWORD)
        with override_settings(TRUSTED_PROXY_HOPS=1):
            for i in range(10):
                self.beheer_login(Client(), "fout-1", email="eigenaar@example.com", HTTP_X_FORWARDED_FOR=f"203.0.113.{i + 1}")
            r = self.beheer_login(Client(), self.PASSWORD, email=other.email, HTTP_X_FORWARDED_FOR="198.51.100.9")
            self.assertEqual(r.status_code, 302)

    def test_success_resets_the_account_counter(self):
        c = Client()
        for _ in range(8):
            self.beheer_login(c, "fout-wachtwoord-1")
        self.assertEqual(self.beheer_login(Client(), self.PASSWORD).status_code, 302)
        # Na de geslaagde inlog staat de teller van het account weer op nul (die van het IP niet).
        from core import bruteforce
        self.assertFalse(bruteforce.is_blocked(HttpRequest(), "eigenaar@example.com"))

    def test_customer_login_with_code_is_not_affected(self):
        c = Client()
        for _ in range(12):
            self.beheer_login(c, "fout-wachtwoord-1")
        r = c.post("/inloggen/", {"email": "klant@example.com"})
        self.assertEqual(r.status_code, 302)

    def test_username_with_odd_input_does_not_crash(self):
        c = Client()
        self.assertEqual(self.beheer_login(c, "x", email="A" * 5000).status_code, 200)
        self.assertEqual(c.post("/beheer/inloggen/", {}).status_code, 200)


class ClientIpTests(VaylideTestCase):
    def req(self, xff=None, remote="10.0.0.1"):
        r = HttpRequest()
        r.META["REMOTE_ADDR"] = remote
        if xff is not None:
            r.META["HTTP_X_FORWARDED_FOR"] = xff
        return r

    @override_settings(TRUSTED_PROXY_HOPS=0)
    def test_hops_zero_ignores_forwarded_header(self):
        self.assertEqual(client_ip(self.req("1.2.3.4")), "10.0.0.1")

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_hops_one_takes_the_last_entry_and_ignores_forged_ones(self):
        self.assertEqual(client_ip(self.req("6.6.6.6, 7.7.7.7, 203.0.113.5")), "203.0.113.5")

    @override_settings(TRUSTED_PROXY_HOPS=2)
    def test_hops_two_takes_second_from_right(self):
        self.assertEqual(client_ip(self.req("6.6.6.6, 203.0.113.5, 172.16.0.9")), "203.0.113.5")

    @override_settings(TRUSTED_PROXY_HOPS=2)
    def test_too_short_chain_falls_back_to_remote_addr(self):
        self.assertEqual(client_ip(self.req("203.0.113.5")), "10.0.0.1")

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_invalid_values_are_ignored(self):
        for junk in ("niet-een-ip", "<script>", "999.1.1.1", "", " , ", "1.2.3.4/24"):
            self.assertEqual(client_ip(self.req(junk)), "10.0.0.1", junk)

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_ports_and_brackets_and_mapped_ipv6(self):
        self.assertEqual(client_ip(self.req("203.0.113.5:4711")), "203.0.113.5")
        self.assertEqual(client_ip(self.req("[2001:db8::1]:443")), "2001:db8::1")
        self.assertEqual(client_ip(self.req("::ffff:203.0.113.5")), "203.0.113.5")

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_no_header_falls_back(self):
        self.assertEqual(client_ip(self.req()), "10.0.0.1")

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_ipv6_same_64_network_shares_a_limit_bucket(self):
        a = ip_fingerprint(self.req("2001:db8:1:2::1"))
        b = ip_fingerprint(self.req("2001:db8:1:2:ffff::9"))
        c = ip_fingerprint(self.req("2001:db8:1:3::1"))
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_different_ipv4_addresses_have_different_buckets(self):
        self.assertNotEqual(ip_fingerprint(self.req("203.0.113.5")), ip_fingerprint(self.req("203.0.113.6")))

    def test_beheer_settings_page_shows_own_ip_for_staff_only(self):
        staff = self.make_staff("eigenaar@example.com")
        c = Client()
        c.force_login(staff)
        with override_settings(TRUSTED_PROXY_HOPS=1):
            page = c.get("/beheer/instellingen/", HTTP_X_FORWARDED_FOR="6.6.6.6, 203.0.113.77")
        self.assertContains(page, "203.0.113.77")
        self.assertNotContains(page, "6.6.6.6")

    def test_check_warns_on_render_without_hops(self):
        from core.checks import proxy_hops
        with mock.patch.dict(os.environ, {"RENDER": "true"}), override_settings(TRUSTED_PROXY_HOPS=0):
            self.assertEqual([w.id for w in proxy_hops(None)], ["vaylide.W002"])
        with mock.patch.dict(os.environ, {"RENDER": "true"}), override_settings(TRUSTED_PROXY_HOPS=1):
            self.assertEqual(proxy_hops(None), [])

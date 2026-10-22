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


@override_settings(LINK_BLOCK_ENABLED=True)
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
        self.probe(Client(), 70, REMOTE_ADDR="145.5.6.1")
        other = Client()
        self.assertEqual(other.get(self.inv.public_path, REMOTE_ADDR="145.5.6.2").status_code, 200)

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
                c.get(f"/u/geenbestaand-{i:08d}/", HTTP_X_FORWARDED_FOR=f"10.1.1.{i % 250}, 81.107.0.7")
            r = c.get(self.inv.public_path, HTTP_X_FORWARDED_FOR="10.9.9.9, 81.107.0.7")
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
                self.beheer_login(Client(), "fout-wachtwoord-1", HTTP_X_FORWARDED_FOR=f"81.107.0.{i + 1}")
            r = self.beheer_login(Client(), self.PASSWORD, HTTP_X_FORWARDED_FOR="81.107.0.200")
            self.assertEqual(r.status_code, 429)

    def test_attacker_on_one_ip_does_not_lock_other_accounts_from_other_ips(self):
        other = self.make_staff("tweede@example.com", self.PASSWORD)
        with override_settings(TRUSTED_PROXY_HOPS=1):
            for i in range(10):
                self.beheer_login(Client(), "fout-1", email="eigenaar@example.com", HTTP_X_FORWARDED_FOR=f"81.107.0.{i + 1}")
            r = self.beheer_login(Client(), self.PASSWORD, email=other.email, HTTP_X_FORWARDED_FOR="145.5.6.9")
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
        self.assertEqual(client_ip(self.req("6.6.6.6, 7.7.7.7, 81.107.0.5")), "81.107.0.5")

    @override_settings(TRUSTED_PROXY_HOPS=2)
    def test_hops_two_takes_second_from_right(self):
        self.assertEqual(client_ip(self.req("6.6.6.6, 81.107.0.5, 172.16.0.9")), "81.107.0.5")

    @override_settings(TRUSTED_PROXY_HOPS=2)
    def test_too_short_chain_falls_back_to_remote_addr(self):
        self.assertEqual(client_ip(self.req("81.107.0.5")), "10.0.0.1")

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_invalid_values_are_ignored(self):
        for junk in ("niet-een-ip", "<script>", "999.1.1.1", "", " , ", "1.2.3.4/24"):
            self.assertEqual(client_ip(self.req(junk)), "10.0.0.1", junk)

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_ports_and_brackets_and_mapped_ipv6(self):
        self.assertEqual(client_ip(self.req("81.107.0.5:4711")), "81.107.0.5")
        self.assertEqual(client_ip(self.req("[2001:db8::1]:443")), "2001:db8::1")
        self.assertEqual(client_ip(self.req("::ffff:81.107.0.5")), "81.107.0.5")

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
        self.assertNotEqual(ip_fingerprint(self.req("81.107.0.5")), ip_fingerprint(self.req("81.107.0.6")))

    def test_beheer_settings_page_shows_status_but_no_full_ip(self):
        staff = self.make_staff("eigenaar@example.com")
        c = Client()
        c.force_login(staff)
        with override_settings(TRUSTED_PROXY_HOPS=1):
            page = c.get("/beheer/instellingen/", HTTP_X_FORWARDED_FOR="6.6.6.6, 81.107.0.77")
        self.assertContains(page, "Betrouwbaar")
        self.assertNotContains(page, "81.107.0.77")
        self.assertNotContains(page, "6.6.6.6")

    def test_check_warns_on_render_without_hops(self):
        from core.checks import proxy_hops
        with mock.patch.dict(os.environ, {"RENDER": "true"}), override_settings(TRUSTED_PROXY_HOPS=0):
            self.assertEqual([w.id for w in proxy_hops(None)], ["vaylide.W002"])
        with mock.patch.dict(os.environ, {"RENDER": "true"}), override_settings(TRUSTED_PROXY_HOPS=1):
            self.assertEqual(proxy_hops(None), [])


# ---------------------------------------------------------------------------------------------------------------------
# Stap 1: onbetrouwbaar IP, meting, melding bij veel onbekende links, blokkade standaard uit
# ---------------------------------------------------------------------------------------------------------------------
from django.core import mail  # noqa: E402
from django.test import RequestFactory  # noqa: E402

from core import ipinfo  # noqa: E402
from core.utils import reliable_ip_fingerprint  # noqa: E402
from invitations import alarm  # noqa: E402
from processing.models import OutboundEmail  # noqa: E402


def make_request(xff=None, remote="10.0.0.1", **headers):
    r = HttpRequest()
    r.META["REMOTE_ADDR"] = remote
    if xff is not None:
        r.META["HTTP_X_FORWARDED_FOR"] = xff
    for name, value in headers.items():
        r.META["HTTP_" + name.upper()] = value
    return r


class AssessTests(VaylideTestCase):
    def setUp(self):
        cache.clear()
        ipinfo._warned_at.clear()

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_public_visitor_is_reliable(self):
        self.assertTrue(ipinfo.assess(make_request("6.6.6.6, 81.107.0.5")).reliable)

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_private_or_internal_address_is_unreliable(self):
        for chosen in ("10.1.2.3", "172.16.0.9", "192.168.1.1", "127.0.0.1", "169.254.1.1"):
            status = ipinfo.assess(make_request(f"81.107.0.5, {chosen}"))
            self.assertFalse(status.reliable, chosen)
            self.assertEqual(status.reason, "niet-openbaar")

    @override_settings(TRUSTED_PROXY_HOPS=2)
    def test_cloudflare_address_is_unreliable(self):
        status = ipinfo.assess(make_request("81.107.0.5, 172.71.10.1, 10.1.2.3"))
        self.assertFalse(status.reliable)
        self.assertEqual(status.reason, "cloudflare")

    @override_settings(TRUSTED_PROXY_HOPS=3)
    def test_chain_shorter_than_setting_is_unreliable(self):
        status = ipinfo.assess(make_request("81.107.0.5"))
        self.assertEqual((status.reliable, status.reason), (False, "keten-te-kort"))
        self.assertFalse(ipinfo.assess(make_request()).reliable)

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_invalid_value_is_unreliable(self):
        self.assertEqual(ipinfo.assess(make_request("81.107.0.5, niet-een-ip")).reason, "ongeldig")

    def test_hops_zero_is_reliable_locally_but_not_on_render(self):
        with override_settings(TRUSTED_PROXY_HOPS=0):
            self.assertTrue(ipinfo.assess(make_request(remote="127.0.0.1")).reliable)
            with mock.patch.dict(os.environ, {"RENDER": "true"}):
                status = ipinfo.assess(make_request("81.107.0.5"))
        self.assertEqual((status.reliable, status.reason), (False, "geen-proxyinstelling"))

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_spoofed_headers_do_not_change_the_choice(self):
        base = ipinfo.assess(make_request("81.107.0.5"))
        spoofed = ipinfo.assess(make_request(
            "1.1.1.1, 2.2.2.2, 81.107.0.5", cf_connecting_ip="9.9.9.9", true_client_ip="8.8.8.8", x_real_ip="7.7.7.7"))
        self.assertEqual(base, spoofed)

    @override_settings(TRUSTED_PROXY_HOPS=5)
    def test_too_high_value_picking_a_visitor_chosen_entry_is_flagged_when_private(self):
        # Bezoeker kiest zelf een privé-adres: de tripwire slaat aan, het adres wordt niet gebruikt.
        status = ipinfo.assess(make_request("10.9.9.9, 1.1.1.1, 2.2.2.2, 3.3.3.3, 4.4.4.4"))
        self.assertFalse(status.reliable)

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_unreliable_fingerprint_is_none(self):
        self.assertIsNone(reliable_ip_fingerprint(make_request("81.107.0.5, 10.1.2.3")))
        self.assertIsNotNone(reliable_ip_fingerprint(make_request("81.107.0.5")))

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_warning_is_logged_at_most_once_per_hour(self):
        with self.assertLogs("core.ipinfo", level="WARNING") as logs:
            for _ in range(500):
                ipinfo.warn_if_unreliable(make_request("81.107.0.5, 10.1.2.3"))
        self.assertEqual(len(logs.records), 1)
        self.assertNotIn("81.107", logs.output[0])
        self.assertNotIn("10.1.2.3", logs.output[0])


class MeasureTests(VaylideTestCase):
    def setUp(self):
        cache.clear()
        self.staff = self.make_staff("eigenaar@example.com")
        self.chain = "9.9.9.9, 81.107.0.5, 172.71.10.1, 10.1.2.3"

    def page(self, client=None, **extra):
        c = client or Client()
        if client is None:
            c.force_login(self.staff)
        return c.get("/beheer/instellingen/", HTTP_X_FORWARDED_FOR=self.chain, HTTP_CF_CONNECTING_IP="81.107.0.5", **extra)

    def test_measurement_is_off_by_default(self):
        page = self.page()
        self.assertNotContains(page, "plaats 1 van rechts")

    @override_settings(IP_MEASURE=True, TEST_MODE=True, TRUSTED_PROXY_HOPS=3)
    def test_measurement_shows_kinds_and_masked_addresses_only(self):
        page = self.page()
        self.assertContains(page, "plaats 1 van rechts")
        self.assertContains(page, "cloudflare")
        self.assertContains(page, "81.107.x.x")
        for full in ("81.107.0.5", "172.71.10.1", "10.1.2.3", "9.9.9.9"):
            self.assertNotContains(page, full)

    @override_settings(IP_MEASURE=True, TEST_MODE=False)
    def test_measurement_is_ignored_in_live_mode(self):
        self.assertNotContains(self.page(), "plaats 1 van rechts")

    @override_settings(IP_MEASURE=True, TEST_MODE=True)
    def test_measurement_is_staff_only(self):
        anonymous = Client().get("/beheer/instellingen/", HTTP_X_FORWARDED_FOR=self.chain)
        self.assertNotEqual(anonymous.status_code, 200)
        self.assertNotContains(anonymous, "plaats 1 van rechts", status_code=anonymous.status_code)
        customer = Client()
        customer.force_login(self.make_customer("klant@example.com"))
        r = customer.get("/beheer/instellingen/", HTTP_X_FORWARDED_FOR=self.chain)
        self.assertNotEqual(r.status_code, 200)

    def test_mask_formats(self):
        self.assertEqual(ipinfo.mask_ip("81.107.0.5"), "81.107.x.x")
        self.assertEqual(ipinfo.mask_ip("2001:db8:1:2::9"), "2001:0db8::x")
        self.assertEqual(ipinfo.mask_ip("rommel"), "ongeldig")

    def test_measure_does_not_write_anything(self):
        with self.assertNumQueries(0):
            with override_settings(TRUSTED_PROXY_HOPS=2):
                ipinfo.measure(make_request(self.chain))


class LinkBlockDefaultTests(VaylideTestCase):
    def setUp(self):
        cache.clear()
        alarm._alarmed_window = None
        self.inv = self.published(owner=self.make_customer())

    def test_blocking_is_off_by_default(self):
        self.assertFalse(settings.LINK_BLOCK_ENABLED)
        self.assertFalse(settings.IP_MEASURE)
        c = Client()
        codes = {c.get(f"/u/geenbestaand-{i:08d}/").status_code for i in range(90)}
        self.assertEqual(codes, {404})
        self.assertEqual(c.get(self.inv.public_path).status_code, 200)

    @override_settings(LINK_BLOCK_ENABLED=True, TRUSTED_PROXY_HOPS=1)
    def test_blocking_enabled_but_ip_unreliable_does_not_block_anyone(self):
        c = Client()
        for i in range(90):
            c.get(f"/u/geenbestaand-{i:08d}/", HTTP_X_FORWARDED_FOR="81.107.0.5, 10.1.2.3")
        r = c.get(self.inv.public_path, HTTP_X_FORWARDED_FOR="81.107.0.5, 10.1.2.3")
        self.assertEqual(r.status_code, 200)

    @override_settings(LINK_BLOCK_ENABLED=True, TRUSTED_PROXY_HOPS=0)
    def test_blocking_on_render_without_proxy_setting_blocks_nobody(self):
        with mock.patch.dict(os.environ, {"RENDER": "true"}):
            c = Client()
            for i in range(90):
                c.get(f"/u/geenbestaand-{i:08d}/")
            self.assertEqual(c.get(self.inv.public_path).status_code, 200)

    @override_settings(LINK_BLOCK_ENABLED=True, TRUSTED_PROXY_HOPS=1)
    def test_blocking_enabled_and_reliable_blocks_only_the_prober(self):
        prober = Client()
        for i in range(65):
            prober.get(f"/u/geenbestaand-{i:08d}/", HTTP_X_FORWARDED_FOR="1.1.1.1, 81.107.0.5")
        self.assertEqual(prober.get(self.inv.public_path, HTTP_X_FORWARDED_FOR="1.1.1.1, 81.107.0.5").status_code, 429)
        self.assertEqual(Client().get(self.inv.public_path, HTTP_X_FORWARDED_FOR="145.5.6.9").status_code, 200)


class LinkAlarmTests(VaylideTestCase):
    def setUp(self):
        cache.clear()
        alarm._alarmed_window = None
        self.inv = self.published(owner=self.make_customer())

    def flood(self, n, **extra):
        c = Client()
        return [c.get(f"/u/geenbestaand-{i:08d}/", **extra).status_code for i in range(n)]

    def test_normal_use_gives_no_alarm(self):
        with self.assertNoLogs("invitations.alarm", level="WARNING"):
            self.flood(30)
        self.assertEqual(OutboundEmail.objects.filter(kind="owner_link_alarm").count(), 0)

    def test_flood_gives_one_log_and_one_mail_and_never_blocks(self):
        with self.assertLogs("invitations.alarm", level="WARNING") as logs:
            codes = self.flood(400)
        self.assertEqual(set(codes), {404})
        self.assertEqual(len(logs.records), 1)
        self.assertEqual(OutboundEmail.objects.filter(kind="owner_link_alarm").count(), 1)
        self.assertEqual(Client().get(self.inv.public_path).status_code, 200)

    def test_flood_from_many_addresses_still_gives_one_mail(self):
        with self.assertLogs("invitations.alarm", level="WARNING"):
            for i in range(400):
                Client().get(f"/u/geenbestaand-{i:08d}/", HTTP_X_FORWARDED_FOR=f"{i % 200 + 1}.5.5.5")
        self.assertEqual(OutboundEmail.objects.filter(kind="owner_link_alarm").count(), 1)

    def test_second_window_does_not_send_a_second_mail_within_the_period(self):
        with self.assertLogs("invitations.alarm", level="WARNING"):
            self.flood(150)
        cache.clear()
        alarm._alarmed_window = None
        with self.assertLogs("invitations.alarm", level="WARNING"):
            self.flood(150)
        self.assertEqual(OutboundEmail.objects.filter(kind="owner_link_alarm").count(), 1)

    def test_alarm_contains_no_addresses_or_links(self):
        with self.assertLogs("invitations.alarm", level="WARNING") as logs:
            self.flood(150, HTTP_X_FORWARDED_FOR="81.107.0.5")
        self.assertNotIn("81.107", logs.output[0])
        body = OutboundEmail.objects.get(kind="owner_link_alarm").body_text
        self.assertNotIn("geenbestaand", body)
        self.assertNotIn("81.107", body)

    def test_failing_mail_never_breaks_the_page(self):
        with mock.patch("processing.emails.queue_email", side_effect=RuntimeError("kapot")):
            with self.assertLogs("invitations.alarm", level="ERROR"):
                codes = self.flood(150)
        self.assertEqual(set(codes), {404})

    def test_expired_links_do_not_count(self):
        offline = self.published(owner=self.make_customer("ander@example.com"))
        offline.status = offline.Status.OFFLINE
        offline.save()
        c = Client()
        with self.assertNoLogs("invitations.alarm", level="WARNING"):
            for _ in range(300):
                self.assertEqual(c.get(offline.public_path).status_code, 410)


class StaffLoginUnreliableIpTests(VaylideTestCase):
    PASSWORD = "Een-lang-wachtwoord-2026"

    def setUp(self):
        cache.clear()
        self.staff = self.make_staff("eigenaar@example.com", self.PASSWORD)

    def login(self, password, email="eigenaar@example.com", **extra):
        return Client().post("/beheer/inloggen/", {"username": email, "password": password}, **extra)

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_account_counter_still_protects_when_ip_is_unreliable(self):
        unreliable = {"HTTP_X_FORWARDED_FOR": "81.107.0.5, 10.1.2.3"}
        for _ in range(10):
            self.login("fout", **unreliable)
        r = self.login(self.PASSWORD, **unreliable)
        self.assertEqual(r.status_code, 429)

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_unreliable_ip_is_not_one_shared_bucket_for_all_accounts(self):
        unreliable = {"HTTP_X_FORWARDED_FOR": "81.107.0.5, 10.1.2.3"}
        other = self.make_staff("tweede@example.com", self.PASSWORD)
        for _ in range(12):
            self.login("fout", email="eigenaar@example.com", **unreliable)
        r = self.login(self.PASSWORD, email=other.email, **unreliable)
        self.assertNotEqual(r.status_code, 429)

    @override_settings(TRUSTED_PROXY_HOPS=1)
    def test_reliable_ip_still_blocks_per_ip(self):
        ok = {"HTTP_X_FORWARDED_FOR": "1.1.1.1, 81.107.0.5"}
        other = self.make_staff("tweede@example.com", self.PASSWORD)
        for i in range(10):
            self.login("fout", email=f"onbekend{i}@example.com", **ok)
        self.assertEqual(self.login(self.PASSWORD, email=other.email, **ok).status_code, 429)

    @override_settings(TRUSTED_PROXY_HOPS=0)
    def test_missing_proxy_setting_on_render_keeps_account_protection(self):
        with mock.patch.dict(os.environ, {"RENDER": "true"}):
            for _ in range(10):
                self.login("fout")
            self.assertEqual(self.login(self.PASSWORD).status_code, 429)

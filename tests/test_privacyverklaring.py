"""Privacyverklaring: feiten uit de inrichting, alleen actieve aanbieders, links bij formulieren en de controle vóór livegang."""
from datetime import timedelta
from unittest import mock

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.test import Client, override_settings
from django.utils import timezone

from core import privacyverklaring as pv
from core.privacy import apply_retention

from .helpers import VaylideTestCase

ALLES_BESLOTEN = {key: "Vastgesteld door de eigenaar." for key in pv.BESLUITEN}


class StatementTests(VaylideTestCase):
    def page(self):
        return Client().get("/privacy/").content.decode()

    def test_all_sections_and_facts(self):
        html = self.page()
        for kop in ("1. Wie verantwoordelijk is", "4. Uitnodigingen, aanmeldingen en de organisator", "8. Verwerking buiten",
                    "9. Hoe lang wij gegevens bewaren", "10. Cookies en opslag in je browser", "13. Geautomatiseerde besluiten"):
            self.assertIn(kop, html)
        for cookie in ("vierlief_sessie", "vierlief_csrf", "vierlief_antwoord", "vierlief-beweging"):
            self.assertIn(cookie, html)
        self.assertIn("Render Services, Inc.", html)
        self.assertIn("autoriteitpersoonsgegevens.nl", html)
        self.assertIn(settings.CONTACT_EMAIL, html)
        self.assertNotIn("juridisch goedgekeurd", html.lower())
        self.assertNotIn("100%", html)

    def test_retention_values_come_from_the_settings(self):
        from core.models import SiteConfig

        config = SiteConfig.get()
        html = self.page()
        self.assertIn(f"{config.guest_data_retention_days} dagen nadat de uitnodiging offline ging", html)
        self.assertIn(f"{config.unpaid_draft_retention_days} dagen na de laatste wijziging", html)

    def test_open_decisions_are_visible_on_the_test_version(self):
        html = self.page()
        self.assertIn('class="invulveld"', html)
        self.assertIn("Nog vast te stellen:", html)

    def test_payment_provider_only_when_active(self):
        self.assertNotIn("Mollie B.V.", self.page())  # testbetaling: geen Mollie
        with override_settings(PAYMENT_PROVIDER="mollie"):
            self.assertIn("Mollie B.V.", self.page())

    def test_ai_provider_only_with_a_key(self):
        with override_settings(ANTHROPIC_API_KEY="", AI_ENABLED=True):
            html = self.page()
            self.assertNotIn("Anthropic PBC", html)
            self.assertIn("Er gaan geen gegevens naar een AI-aanbieder", html)
        with override_settings(ANTHROPIC_API_KEY="sk-test", AI_ENABLED=True, PRIVACY_AI_AFSPRAKEN=""):
            html = self.page()
            self.assertIn("Anthropic PBC", html)
            self.assertIn(pv.LABELS["ai_afspraken"], pv.open_points())

    def test_email_provider_needs_a_name(self):
        with override_settings(EMAIL_MODE="smtp", PRIVACY_EMAIL_PROVIDER=""):
            self.assertIn(pv.LABELS["email_aanbieder"], pv.open_points())
            self.assertIn("[naam en land aanbieder]", self.page())
        with override_settings(EMAIL_MODE="smtp", PRIVACY_EMAIL_PROVIDER="Voorbeeld Mail B.V. (Nederland)"):
            self.assertNotIn(pv.LABELS["email_aanbieder"], pv.open_points())
            self.assertIn("Voorbeeld Mail B.V.", self.page())

    def test_faces_feature_is_described_as_off(self):
        self.assertFalse(settings.FACES_ENABLED)
        self.assertIn("staat uit", self.page())
        with override_settings(FACES_ENABLED=True):
            self.assertIn(pv.LABELS["gezichten"], pv.open_points())


class LiveGuardTests(VaylideTestCase):
    def test_no_error_in_test_mode(self):
        self.assertEqual(pv.check_privacy_statement(), [])

    @override_settings(TEST_MODE=False)
    def test_live_refuses_open_points(self):
        errors = pv.check_privacy_statement()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, "vaylide.E001")

    @override_settings(TEST_MODE=False, COMPANY_LEGAL_NAME="Voorbeeld", COMPANY_ADDRESS="Straat 1|1234 AB Plaats",
                       EMAIL_MODE="smtp", PRIVACY_EMAIL_PROVIDER="Voorbeeld Mail B.V. (Nederland)", ANTHROPIC_API_KEY="")
    def test_live_passes_when_everything_is_decided(self):
        with mock.patch.dict(pv.BESLUITEN, ALLES_BESLOTEN):
            self.assertEqual(pv.open_points(), [])
            self.assertEqual(pv.check_privacy_statement(), [])
            html = Client().get("/privacy/").content.decode()
        self.assertNotIn('class="invulveld"', html)
        self.assertNotIn("Nog vast te stellen", html)


class LinkTests(VaylideTestCase):
    def test_footer_login_contact_and_withdraw(self):
        for url in ("/", "/inloggen/", "/contact/", "/herroepen/"):
            response = Client().get(url)
            self.assertContains(response, 'href="/privacy/', msg_prefix=url)

    def test_studio_photos_checkout_and_wish(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        client = Client()
        client.force_login(customer)
        self.assertContains(client.get(f"/maken/{inv.uid}/fotos/"), 'href="/privacy/#fotos"')
        checkout = client.get(f"/maken/{inv.uid}/bestellen/")
        self.assertContains(checkout, 'href="/privacy/"')
        # nieuwsbrief: apart vinkje dat standaard uit staat
        self.assertContains(checkout, 'name="nieuwsbrief" value="on">')
        self.assertContains(client.get("/account/wensen/nieuw/"), 'href="/privacy/"')

    def test_rsvp_form_links_to_the_guest_section(self):
        inv = self.published()
        html = Client().get(f"/u/{inv.slug}/").content.decode()
        self.assertIn('href="/privacy/#gasten"', html)
        self.assertNotIn("Alleen de organisator ziet je antwoord", html)

    def test_ai_help_says_where_text_goes(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        client = Client()
        client.force_login(customer)
        with override_settings(ANTHROPIC_API_KEY=""):
            self.assertContains(client.get(f"/maken/{inv.uid}/gegevens/"), "er gaat niets naar een AI-dienst")
        with override_settings(ANTHROPIC_API_KEY="sk-test", AI_ENABLED=True):
            self.assertContains(client.get(f"/maken/{inv.uid}/gegevens/"), "gaan daarvoor naar Anthropic (Claude)")


class FactsMatchTheCodeTests(VaylideTestCase):
    def test_cookie_lifetimes(self):
        self.assertEqual(settings.SESSION_COOKIE_AGE, 30 * 24 * 3600)
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.CSRF_COOKIE_AGE, 31449600)  # 1 jaar (standaard van Django)
        inv = self.published()
        client = Client()
        response = self.rsvp(client, inv, json=False)
        cookie = response.cookies.get("vierlief_antwoord")
        self.assertIsNotNone(cookie)
        self.assertEqual(int(cookie["max-age"]), 365 * 24 * 3600)
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["path"], f"/u/{inv.slug}/")

    def test_mollie_receives_no_customer_details(self):
        from orders.providers import MollieProvider

        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        with self.captureOnCommitCallbacks(execute=True):
            from orders.services import start_checkout

            payment = start_checkout(inv, user=customer, package_code="essentieel", optional_codes=[], terms_accepted=True)
        sent = {}

        def fake_request(self, method, path, body=None):
            sent.update(body or {})
            return {"id": "tr_test", "_links": {"checkout": {"href": "https://example.test/pay"}}}

        with mock.patch.object(MollieProvider, "_request", fake_request), override_settings(MOLLIE_API_KEY="test_voorbeeld"):
            MollieProvider().create(payment, description="VAYLIDE X", return_url="https://x/terug", webhook_url="https://x/hook")
        self.assertEqual(set(sent), {"amount", "description", "redirectUrl", "locale", "metadata", "webhookUrl"})
        self.assertNotIn(customer.email, str(sent))
        self.assertNotIn(inv.draft_content.get("names", {}).get("partner1", "@@"), str(sent))

    def test_face_detection_stores_no_face_features(self):
        from invitations.models import MediaAsset

        fields = {f.name for f in MediaAsset._meta.get_fields()}
        self.assertTrue({"focus_x", "focus_y", "faces"} <= fields)
        self.assertFalse(any("embedding" in f or "template" in f or "kenmerk" in f for f in fields))


class RetentionCleanupTests(VaylideTestCase):
    def test_expired_sessions_and_cache_rows_are_removed(self):
        now = timezone.now()
        Session.objects.create(session_key="oud" * 8, session_data="x", expire_date=now - timedelta(days=1))
        Session.objects.create(session_key="nieuw" * 6, session_data="x", expire_date=now + timedelta(days=1))
        cache.set("rl:test-verlopen", 1, 1)
        cache.set("rl:test-geldig", 1, 3600)
        report = apply_retention(now=now + timedelta(seconds=5))
        self.assertEqual(report["verwijderde_sessies"], 1)
        self.assertGreaterEqual(report["verwijderde_cachewaarden"], 1)
        self.assertTrue(Session.objects.filter(session_key="nieuw" * 6).exists())
        self.assertEqual(cache.get("rl:test-geldig"), 1)

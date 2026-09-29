"""Algemene voorwaarden (concept 29 september 2026): looptijd vanaf de bevestigde betaling, toestemmingen bij het
bestellen, de bewaarbare bestelbevestiging, bedrijfsgegevens met invulvelden en de herroepingsfunctie."""
import os
import subprocess
import sys
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.test import Client, override_settings
from django.utils import timezone

from invitations.availability import add_months, end_of_availability
from orders.models import Order, Payment, Withdrawal
from processing.models import OutboundEmail

from .helpers import VaylideTestCase, future_date, old_form_ts

NL = ZoneInfo("Europe/Amsterdam")


class AvailabilityDateTests(VaylideTestCase):
    def test_calendar_months(self):
        self.assertEqual(add_months(date(2026, 9, 29), 6), date(2027, 3, 29))
        self.assertEqual(add_months(date(2026, 9, 29), 12), date(2027, 9, 29))
        self.assertEqual(add_months(date(2026, 12, 15), 1), date(2027, 1, 15))

    def test_end_of_month_and_leap_years(self):
        self.assertEqual(add_months(date(2027, 1, 31), 1), date(2027, 2, 28))
        self.assertEqual(add_months(date(2028, 1, 31), 1), date(2028, 2, 29))  # schrikkeljaar
        self.assertEqual(add_months(date(2027, 8, 31), 6), date(2028, 2, 29))
        self.assertEqual(add_months(date(2028, 2, 29), 12), date(2029, 2, 28))
        self.assertEqual(add_months(date(2026, 3, 31), 6), date(2026, 9, 30))

    def test_online_until_the_end_of_that_day_in_dutch_time(self):
        paid = datetime(2026, 9, 29, 22, 30, tzinfo=ZoneInfo("UTC"))  # 30 september 00:30 in Nederland
        end = end_of_availability(paid, 6)
        self.assertEqual((end.date(), end.hour, end.minute), (date(2027, 3, 30), 23, 59))
        self.assertEqual(end.tzinfo, NL)


class PurchaseDateTests(VaylideTestCase):
    def test_end_date_counts_from_the_confirmed_payment_and_is_fixed_once(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer, date=future_date(400))
        payment = self.pay(inv, customer)
        order = Order.objects.get(pk=payment.order_id)
        expected = end_of_availability(order.paid_at, order.availability_months)
        self.assertEqual(order.ends_at, expected)
        inv.refresh_from_db()
        self.assertEqual(inv.available_until, expected)
        # een herhaalde melding van de betaalprovider verandert niets
        self.provider_says(payment, Payment.Status.PAID)
        order.refresh_from_db()
        inv.refresh_from_db()
        self.assertEqual((order.ends_at, inv.available_until), (expected, expected))

    def test_later_publishing_does_not_move_the_end_date(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        self.pay(inv, customer)
        inv.refresh_from_db()
        before = inv.available_until
        from invitations.services import publish_draft

        from invitations.models import Source

        publish_draft(inv, user=customer, source=Source.CUSTOMER, expected_rev=None)
        inv.refresh_from_db()
        self.assertEqual(inv.available_until, before)

    def test_existing_orders_keep_their_promised_date(self):
        # Een bestelling van vóór deze wijziging (zonder ends_at) krijgt niet met terugwerkende kracht een andere datum.
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        self.pay(inv, customer)
        promised = timezone.now() + timedelta(days=400)
        inv.refresh_from_db()
        type(inv).objects.filter(pk=inv.pk).update(available_until=promised)
        Order.objects.filter(invitation=inv).update(ends_at=None)
        payment = Payment.objects.filter(order__invitation=inv).first()
        self.provider_says(payment, Payment.Status.PAID)
        inv.refresh_from_db()
        self.assertEqual(inv.available_until, promised)


class CheckoutConsentTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.client = Client()
        self.client.force_login(self.customer)

    def post(self, inv, **extra):
        data = {"actie": "betalen", "package": "essentieel", "terms": "on"}
        data.update(extra)
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(f"/maken/{inv.uid}/bestellen/", data)

    def test_two_separate_unticked_boxes(self):
        inv = self.make_invitation(owner=self.customer)
        html = self.client.get(f"/maken/{inv.uid}/bestellen/").content.decode()
        for name in ('name="terms"', 'name="direct_leveren"'):
            box = html[html.index(name) - 80:html.index(name) + 60]
            self.assertNotIn("checked", box, name)
        self.assertIn("versie 29 september 2026", html)
        self.assertIn("/voorwaarden/download/2026-09-29/", html)

    def test_immediate_delivery_needs_its_own_consent(self):
        inv = self.make_invitation(owner=self.customer)
        response = self.post(inv)
        self.assertContains(response, "direct na je betaling mogen leveren")
        self.assertFalse(Order.objects.filter(invitation=inv).exists())

    def test_consent_and_terms_version_are_recorded(self):
        inv = self.make_invitation(owner=self.customer)
        self.post(inv, direct_leveren="on")
        order = Order.objects.get(invitation=inv)
        self.assertEqual(order.terms_version, "2026-09-29")
        self.assertIsNotNone(order.delivery_consent_at)
        self.assertIn("herroepingsrecht", order.delivery_consent_text)

    def test_warning_when_the_period_ends_before_the_event(self):
        inv = self.make_invitation(owner=self.customer, date=future_date(300))  # Essentieel: 6 maanden
        page = self.client.get(f"/maken/{inv.uid}/bestellen/?package=essentieel")
        self.assertContains(page, "na het einde van de online periode")
        self.assertContains(page, "vanaf de aankoopdatum")


class ConfirmationTests(VaylideTestCase):
    def test_confirmation_is_complete_and_carries_the_terms(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        from orders.services import start_checkout

        with self.captureOnCommitCallbacks(execute=True):
            payment = start_checkout(inv, user=customer, package_code="essentieel", optional_codes=[], terms_accepted=True, delivery_consent=True)
        self.provider_says(payment, Payment.Status.PAID)
        order = Order.objects.get(pk=payment.order_id)
        email = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        for text in ("Pakket: Essentieel", "Aankoopdatum:", "Online tot en met:", "herroepingsrecht", "versie 29 september 2026",
                     "KvK-nummer: 94261423", settings.CONTACT_EMAIL, "/herroepen/"):
            self.assertIn(text, email.body_text, text)
        self.assertEqual(email.attach_terms_version, "2026-09-29")
        from processing.emails import terms_attachment

        name, content, mime = terms_attachment("2026-09-29")
        self.assertEqual((name, mime), ("algemene-voorwaarden-vaylide-2026-09-29.html", "text/html"))
        self.assertIn("Beschikbaarheidsduur", content)
        # de bedankpagina toont de einddatum en de versie van de voorwaarden
        client = Client()
        client.force_login(customer)
        page = client.get(f"/bestelling/{order.uid}/")
        self.assertContains(page, "Online tot en met")
        self.assertContains(page, "/voorwaarden/versie/2026-09-29/")


class TermsAndCompanyPageTests(VaylideTestCase):
    @override_settings(COMPANY_LEGAL_NAME="", COMPANY_ADDRESS="")
    def test_missing_company_data_are_visible_placeholders(self):
        html = Client().get("/voorwaarden/").content.decode()
        self.assertIn('<mark class="invulveld">[juridische naam onderneming en rechtsvorm]</mark>', html)
        self.assertIn('<mark class="invulveld">[vestigingsadres]</mark>', html)
        self.assertIn("Nog niet ingevuld", html)
        self.assertIn("94261423", html)
        self.assertIn("16. Toepasselijk recht", html)
        self.assertIn("Modelformulier voor herroeping", html)

    @override_settings(COMPANY_LEGAL_NAME="Voorbeeld Holding B.V.", COMPANY_ADDRESS="Voorbeeldstraat 1|1234 AB Voorbeeldstad")
    def test_filled_in_company_data(self):
        html = Client().get("/voorwaarden/").content.decode()
        self.assertIn("handelsnaam van Voorbeeld Holding B.V.", html)
        self.assertNotIn("invulveld", html.split("<main", 1)[1].split("Nog niet ingevuld")[0] if "Nog niet ingevuld" in html else "")
        contact = Client().get("/contact/").content.decode()
        self.assertIn("Voorbeeldstraat 1<br>1234 AB Voorbeeldstad", contact)

    def test_download_and_versions(self):
        response = Client().get("/voorwaarden/download/2026-09-29/")
        self.assertEqual(response["Content-Disposition"], 'attachment; filename="algemene-voorwaarden-vaylide-2026-09-29.html"')
        self.assertContains(response, "Algemene voorwaarden")
        self.assertEqual(Client().get("/voorwaarden/versie/2026-09-29/").status_code, 200)
        self.assertEqual(Client().get("/voorwaarden/versie/1999-01-01/").status_code, 404)

    def test_contact_and_company_page_in_the_footer(self):
        home = Client().get("/").content.decode()
        self.assertIn(">Contact &amp; bedrijfsgegevens</a>", home)
        self.assertIn(">Hier de overeenkomst ontbinden</a>", home)
        contact = Client().get("/contact/").content.decode()
        for text in ("Bedrijfsgegevens", "Handelsnaam", "VAYLIDE", "94261423", "NL212227221B02", settings.CONTACT_EMAIL):
            self.assertIn(text, contact)
        self.assertNotIn("Telefoon", contact)  # geen telefoonnummer (keuze van de eigenaar)

    def test_live_mode_refuses_to_start_without_company_data(self):
        env = dict(os.environ, VIERLIEF_MODE="live", DJANGO_DEBUG="false", DJANGO_SECRET_KEY="x" * 60, DJANGO_ALLOWED_HOSTS="vaylide.nl",
                   VIERLIEF_BASE_URL="https://vaylide.nl", VIERLIEF_PAYMENT_PROVIDER="mollie", MOLLIE_API_KEY="live_nep_voor_de_test",
                   VIERLIEF_EMAIL_MODE="smtp", SMTP_HOST="smtp.voorbeeld.nl", SMTP_USER="a", SMTP_PASS="b",
                   VIERLIEF_JURIDISCHE_NAAM="", VIERLIEF_ADRES="")
        result = subprocess.run([sys.executable, "manage.py", "check"], cwd=settings.BASE_DIR, env=env, capture_output=True, text=True, timeout=120)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("VIERLIEF_JURIDISCHE_NAAM", result.stderr)


class WithdrawalTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer)
        self.payment = self.pay(self.inv, self.customer)
        self.order = Order.objects.get(pk=self.payment.order_id)

    def submit(self, **extra):
        data = {"name": "Anna Klant", "email": self.customer.email, "order_number": self.order.number.lower(), "form_ts": old_form_ts()}
        data.update(extra)
        with self.captureOnCommitCallbacks(execute=True):
            return Client().post("/herroepen/", data)

    def test_form_is_reachable_with_clear_labels(self):
        page = Client().get("/herroepen/")
        self.assertContains(page, "Hier de overeenkomst ontbinden")
        self.assertContains(page, "Ontbinding bevestigen")

    def test_withdrawal_is_registered_and_confirmed(self):
        response = self.submit(note="Toch niet nodig")
        w = Withdrawal.objects.get()
        self.assertRedirects(response, f"/herroepen/ontvangen/{w.uid}/", fetch_redirect_response=False)
        self.assertEqual(w.order, self.order)  # gekoppeld via bestelnummer en e-mailadres
        receipt = OutboundEmail.objects.get(kind="herroeping_ontvangen")
        self.assertEqual(receipt.to, self.customer.email)
        self.assertIn(timezone.localtime(w.created_at).strftime("%H:%M"), receipt.body_text)
        self.assertIn("Toch niet nodig", receipt.body_text)
        self.assertTrue(OutboundEmail.objects.filter(kind="owner_herroeping").exists())
        done = Client().get(f"/herroepen/ontvangen/{w.uid}/")
        self.assertContains(done, "We hebben je herroeping ontvangen")
        # geen financiële verwerking: de bestelling blijft zoals ze is
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)

    def test_wrong_email_is_registered_but_not_linked(self):
        self.submit(email="iemand@anders.nl")
        self.assertIsNone(Withdrawal.objects.get().order)

    def test_needs_order_number_or_product_and_blocks_bots(self):
        self.assertContains(self.submit(order_number=""), "Vul je bestelnummer in")
        self.submit(website="spam")
        self.assertFalse(Withdrawal.objects.exists())

    def test_owner_handles_it_in_beheer(self):
        self.submit()
        w = Withdrawal.objects.get()
        self.assertEqual(Client().get("/beheer/herroepingen/").status_code, 302)
        staff = Client()
        staff.force_login(self.make_staff())
        self.assertContains(staff.get("/beheer/herroepingen/"), w.name)
        staff.post("/beheer/herroepingen/", {"id": w.pk, "notitie": "Terugbetaald in Mollie"})
        w.refresh_from_db()
        self.assertIsNotNone(w.handled_at)

    def test_prefilled_from_an_order_for_the_customer(self):
        client = Client()
        client.force_login(self.customer)
        page = client.get(f"/herroepen/?bestelling={self.order.uid}")
        self.assertContains(page, f'value="{self.order.number}"')

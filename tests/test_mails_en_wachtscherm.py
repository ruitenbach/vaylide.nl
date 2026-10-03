"""Nieuwe mails (luxe opmaak, QR-code ín de mail, voorwaarden als pdf-bijlage) en het betaalwachtscherm (hervatten,
minder vaak controleren, geen regel per ongewijzigde status, open/geannuleerd/verlopen/mislukt/betaald apart)."""
import email
import re
from datetime import timedelta
from unittest import mock

from django.core import mail
from django.test import Client, override_settings
from django.utils import timezone

from orders.models import Order, Payment, PaymentEvent
from orders.providers import TestProvider
from orders.services import CheckoutError, start_checkout, sync_payment
from processing.emails import build_message
from processing.models import OutboundEmail

from .helpers import VaylideTestCase

SMTP = dict(EMAIL_MODE="smtp", EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
LANGE_NAAM = "Zoë d'Artagnan-Van den Broek & Émile O'Neill <script>alert(1)</script>"


def parts(msg):
    """(content-type, disposition, bestandsnaam, content-id) van alle delen, in volgorde."""
    return [(p.get_content_type(), p.get_content_disposition(), p.get_filename(), p.get("Content-ID")) for p in msg.walk()]


class MailTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer("koper@example.com")
        self.inv = self.make_invitation(owner=self.customer, names={"partner_1": "Zoë d'Artagnan", "partner_2": "Émile O'Neill"})

    def paid_order(self, extras=None, package="essentieel"):
        with override_settings(**SMTP):
            with self.captureOnCommitCallbacks(execute=True):
                payment = start_checkout(self.inv, user=self.customer, package_code=package, optional_codes=extras or [],
                                         terms_accepted=True, delivery_consent=True)
            self.provider_says(payment, Payment.Status.PAID)
        self.inv.refresh_from_db()
        return Order.objects.get(invitation=self.inv, status=Order.Status.PAID)

    def test_delivery_mail_puts_the_qr_code_inside_the_html(self):
        order = self.paid_order()
        live = OutboundEmail.objects.get(order=order, kind="invitation_live")
        msg = email.message_from_string(build_message(live).message().as_string())
        structure = parts(msg)
        self.assertEqual(msg.get_content_type(), "multipart/alternative")
        self.assertEqual([s[0] for s in structure], ["multipart/alternative", "text/plain", "multipart/related", "text/html", "image/png"])
        image = structure[-1]
        self.assertEqual((image[1], image[2], image[3]), ("inline", "qr-code-uitnodiging.png", "<qr-uitnodiging>"))
        self.assertNotIn("attachment", [s[1] for s in structure])  # geen losse bijlage die Outlook bovenaan toont

    def test_confirmation_carries_the_terms_pdf_and_no_images(self):
        order = self.paid_order()
        confirmation = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        msg = email.message_from_string(build_message(confirmation).message().as_string())
        structure = parts(msg)
        self.assertEqual(msg.get_content_type(), "multipart/mixed")
        pdf = [s for s in structure if s[0] == "application/pdf"]
        self.assertEqual(pdf, [("application/pdf", "attachment", "algemene-voorwaarden-vaylide-2026-09-29.pdf", None)])
        self.assertFalse([s for s in structure if s[0].startswith("image/")])
        payload = [p for p in msg.walk() if p.get_content_type() == "application/pdf"][0].get_payload(decode=True)
        self.assertTrue(payload.startswith(b"%PDF-"))

    def test_the_mails_are_really_sent_like_that(self):
        order = self.paid_order()
        sent = {m.subject: m for m in mail.outbox if order.number in m.subject or "staat online" in m.subject}
        confirmation = next(m for s, m in sent.items() if "Bevestiging van je bestelling" in s)
        live = next(m for s, m in sent.items() if "staat online" in s)
        self.assertEqual([a[0] for a in confirmation.attachments], ["algemene-voorwaarden-vaylide-2026-09-29.pdf"])
        self.assertEqual(live.attachments, [])
        self.assertIn("qr-code-uitnodiging.png", live.message().as_string())

    def test_delivery_mail_layout_and_links(self):
        order = self.paid_order()
        live = OutboundEmail.objects.get(order=order, kind="invitation_live")
        html = live.body_html
        for text in ("Je uitnodiging is klaar", "Bekijk je uitnodiging", "Deel jouw bijzondere moment", "QR-code downloaden",
                     "Beheer je uitnodiging", "Online tot en met", "Privacyverklaring", "Zoë d&#x27;Artagnan &amp; Émile O&#x27;Neill"):
            self.assertIn(text, html)
        self.assertIn('src="cid:qr-uitnodiging"', html)
        self.assertIn(f'href="{self.inv.public_url}"', html)
        self.assertIn(f"/account/uitnodiging/{self.inv.uid}/qr.png?download=1", html)
        self.assertIn("font-size:16px", html)
        self.assertNotIn("<script", html)
        # De accountadressen staan alleen achter knoppen of links, niet als zichtbare tekst.
        portal = f"/account/uitnodiging/{self.inv.uid}/"
        visible = re.sub(r"<[^>]+>", " ", html)
        self.assertNotIn(portal, visible)
        # Platte tekst blijft volledig en bruikbaar.
        self.assertIn(self.inv.public_url, live.body_text)
        self.assertIn("qr.png?download=1", live.body_text)

    def test_confirmation_overview(self):
        order = self.paid_order(extras=["langer-online"])
        confirmation = OutboundEmail.objects.get(order=order, kind="order_confirmation")
        html = confirmation.body_html
        for text in ("Bedankt voor je bestelling", order.number, "Ontwerp", "Liefde op papier", "Pakket", "Essentieel", "Extra opties",
                     "Langer online", "Aankoopdatum", "Online tot en met", order.total_display, "als pdf bij deze e-mail gevoegd",
                     "Hier de overeenkomst ontbinden", "Directe levering en bedenktijd", "KvK-nummer"):
            self.assertIn(text, html)
        self.assertIn("Ontwerp: Liefde op papier", confirmation.body_text)
        self.assertIn("als pdf bij deze e-mail gevoegd", confirmation.body_text)
        self.assertNotIn("<script", html)

    def test_customer_input_is_escaped_once(self):
        self.inv.title = LANGE_NAAM
        self.inv.save(update_fields=["title"])
        order = self.paid_order()
        for mail_obj in OutboundEmail.objects.filter(order=order):
            self.assertNotIn("<script>alert", mail_obj.body_html)
            self.assertNotIn("&amp;amp;", mail_obj.body_html)
            self.assertNotIn("&amp;#x27;", mail_obj.body_html)
            self.assertIn("word-break:break-word", mail_obj.body_html)
        live = OutboundEmail.objects.get(order=order, kind="invitation_live")
        self.assertIn("&lt;script&gt;", live.body_html)
        self.assertIn(LANGE_NAAM, live.body_text)  # platte tekst: letterlijk (geen HTML)

    def test_other_mails_use_the_same_look(self):
        from processing.emails import send_login_code

        with override_settings(EMAIL_MODE="smtp"):
            msg = send_login_code("koper@example.com", "123456", "/inloggen/link/x/")
        self.assertIn("vaylide-logo.png", msg.body_html)
        self.assertIn("font-size:16px", msg.body_html)
        self.assertIn("Testversie van VAYLIDE", msg.body_html)

    def test_qr_download_stays_protected(self):
        self.paid_order()
        url = f"/account/uitnodiging/{self.inv.uid}/qr.png?download=1"
        self.assertEqual(Client().get(url).status_code, 302)  # eerst inloggen
        other = Client()
        other.force_login(self.make_customer("ander@example.com"))
        self.assertEqual(other.get(url).status_code, 404)
        owner = Client()
        owner.force_login(self.customer)
        self.assertEqual(owner.get(url)["Content-Type"], "image/png")


class TermsPdfTests(VaylideTestCase):
    def test_pdf_can_be_opened_and_saved_before_paying(self):
        response = Client().get("/voorwaarden/pdf/2026-09-29/")
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn('inline; filename="algemene-voorwaarden-vaylide-2026-09-29.pdf"', response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF-"))
        self.assertEqual(Client().get("/voorwaarden/pdf/1999-01-01/").status_code, 404)
        self.assertContains(Client().get("/voorwaarden/"), "/voorwaarden/pdf/2026-09-29/")

    def test_pdf_holds_the_whole_version_and_the_order_number(self):
        from core.voorwaarden_pdf import render_pdf

        pdf = render_pdf("2026-09-29", order_number="VL26-12345", compress=False)
        for text in (b"Algemene voorwaarden", b"29 september 2026", b"VL26-12345", b"Modelformulier voor herroeping", b"pagina 1 van"):
            self.assertIn(text, pdf)

    def test_an_order_keeps_its_own_version(self):
        from core import voorwaarden

        customer = self.make_customer()
        inv = self.make_invitation(owner=customer)
        newer = {"template": "core/voorwaarden/2026-09-29.html", "date": timezone.datetime(2099, 1, 1).date(), "status": "Definitief"}
        with override_settings(**SMTP):
            self.pay(inv, customer)  # besteld onder 2026-09-29
        order = Order.objects.get(invitation=inv)
        with mock.patch.dict(voorwaarden.VERSIONS, {"2099-01-01": newer}), mock.patch.object(voorwaarden, "CURRENT", "2099-01-01"):
            msg = build_message(OutboundEmail.objects.get(order=order, kind="order_confirmation")).message()
        names = [p.get_filename() for p in msg.walk() if p.get_filename()]
        self.assertEqual(names, ["algemene-voorwaarden-vaylide-2026-09-29.pdf"])

    def test_guests_get_no_order_terms_or_account_links(self):
        customer = self.make_customer()
        inv = self.published(owner=customer)
        html = Client().get(inv.public_path).content.decode()
        self.assertNotIn("/voorwaarden/pdf/", html)
        self.assertNotIn("/bestelling/", html)
        self.assertNotIn(f"/account/uitnodiging/{inv.uid}", html)
        self.assertIn('href="/privacy/#gasten"', html)


class WaitingScreenTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer)
        self.c = Client()
        self.c.force_login(self.customer)
        with self.captureOnCommitCallbacks(execute=True):
            self.payment = start_checkout(self.inv, user=self.customer, package_code="essentieel", optional_codes=[],
                                          terms_accepted=True, delivery_consent=True)
        self.order = self.payment.order

    def remote(self, status):
        Payment.objects.filter(pk=self.payment.pk).update(test_remote_status=status)

    def age(self, seconds):
        Payment.objects.filter(pk=self.payment.pk).update(created_at=timezone.now() - timedelta(seconds=seconds))

    def test_unchanged_status_writes_no_event_but_changes_and_webhooks_do(self):
        for _ in range(3):
            sync_payment(Payment.objects.get(pk=self.payment.pk), source="terugkeer")
        self.assertEqual(PaymentEvent.objects.filter(payment=self.payment).count(), 0)
        self.remote(Payment.Status.PENDING)
        sync_payment(Payment.objects.get(pk=self.payment.pk), source="terugkeer")
        sync_payment(Payment.objects.get(pk=self.payment.pk), source="webhook")  # ook ongewijzigd: melding blijft zichtbaar
        events = list(PaymentEvent.objects.filter(payment=self.payment).values_list("source", "remote_status"))
        self.assertEqual(sorted(events), [("terugkeer", "pending"), ("webhook", "pending")])

    def test_polling_asks_the_provider_at_most_every_ten_seconds(self):
        with mock.patch.object(TestProvider, "fetch", wraps=TestProvider().fetch) as fetch:
            for _ in range(5):
                self.c.get(f"/bestelling/{self.order.uid}/status.json")
        self.assertEqual(fetch.call_count, 1)

    def test_resume_button_appears_after_a_minute_for_an_open_payment(self):
        page = self.c.get(f"/bestelling/{self.order.uid}/").content.decode()
        self.assertIn("Betaling hervatten", page)
        self.assertRegex(page, r"data-resume\s+hidden")
        self.assertIn('data-resume-after="', page)
        self.age(120)
        page = self.c.get(f"/bestelling/{self.order.uid}/").content.decode()
        self.assertNotRegex(page, r"data-resume\s+hidden")
        self.assertTrue(self.c.get(f"/bestelling/{self.order.uid}/status.json").json()["can_resume"])

    def test_resume_goes_back_to_the_same_open_payment(self):
        self.age(120)
        response = self.c.post(f"/bestelling/{self.order.uid}/opnieuw-betalen/")
        self.assertRedirects(response, self.payment.checkout_url, fetch_redirect_response=False)
        self.assertEqual(Payment.objects.filter(order=self.order).count(), 1)

    def test_resume_checks_first_and_finds_a_late_payment(self):
        self.remote(Payment.Status.PAID)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.c.post(f"/bestelling/{self.order.uid}/opnieuw-betalen/")
        self.assertRedirects(response, f"/bestelling/{self.order.uid}/", fetch_redirect_response=False)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(Payment.objects.filter(order=self.order).count(), 1)

    def test_bank_pending_gets_no_second_payment(self):
        self.remote(Payment.Status.PENDING)
        self.c.post(f"/bestelling/{self.order.uid}/opnieuw-betalen/")
        self.assertEqual(Payment.objects.filter(order=self.order).count(), 1)
        self.assertContains(self.c.get(f"/bestelling/{self.order.uid}/"), "Je bank verwerkt de betaling")

    def test_each_final_status_has_its_own_screen_and_a_new_attempt(self):
        for status, title in ((Payment.Status.CANCELED, "Betaling afgebroken"), (Payment.Status.EXPIRED, "Betaling verlopen"),
                              (Payment.Status.FAILED, "Betaling niet gelukt")):
            payment = Payment.objects.filter(order=self.order).order_by("-created_at").first()
            Payment.objects.filter(pk=payment.pk).update(test_remote_status=status)
            sync_payment(Payment.objects.get(pk=payment.pk), source="webhook")
            page = self.c.get(f"/bestelling/{self.order.uid}/")
            self.assertContains(page, title)
            self.assertContains(page, "Opnieuw betalen")
            before = Payment.objects.filter(order=self.order).count()
            response = self.c.post(f"/bestelling/{self.order.uid}/opnieuw-betalen/")
            self.assertEqual(Payment.objects.filter(order=self.order).count(), before + 1)  # pas nu een nieuwe poging
            new = Payment.objects.filter(order=self.order).order_by("-created_at").first()
            self.assertRedirects(response, new.checkout_url, fetch_redirect_response=False)
        self.assertEqual(Order.objects.get(pk=self.order.pk).fulfilment_status, Order.Fulfilment.NONE)  # nooit gepubliceerd

    def test_new_checkout_first_checks_the_open_payment(self):
        self.remote(Payment.Status.PAID)
        with self.captureOnCommitCallbacks(execute=True), self.assertRaises(CheckoutError):
            start_checkout(self.inv, user=self.customer, package_code="essentieel", optional_codes=[], terms_accepted=True,
                           delivery_consent=True)
        self.assertEqual(Order.objects.filter(invitation=self.inv).count(), 1)
        self.assertEqual(Order.objects.get(pk=self.order.pk).status, Order.Status.PAID)

    def test_webhook_after_resume_still_publishes_once(self):
        self.age(120)
        self.c.post(f"/bestelling/{self.order.uid}/opnieuw-betalen/")
        self.remote(Payment.Status.PAID)
        for _ in range(3):
            with self.captureOnCommitCallbacks(execute=True):
                sync_payment(Payment.objects.get(pk=self.payment.pk), source="webhook")
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.versions.count(), 1)
        self.assertEqual(OutboundEmail.objects.filter(order=self.order, kind="invitation_live").count(), 1)

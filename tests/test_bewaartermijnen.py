"""Vestigingsadres alleen waar nodig, en de nachtelijke bewaartermijnen uit de beslislijst (B1 tot en met B6).

De financiële administratie (bestelling, regels, betalingen) blijft staan; inhoud, bijlagen en correspondentie niet.
"""
from datetime import timedelta

from django.core.files.base import ContentFile
from django.test import Client
from django.utils import timezone

from accounts.models import User
from core.models import ContactMessage
from core.privacy import apply_retention
from invitations.models import Invitation
from orders.models import Order, Payment, Withdrawal
from processing.models import OutboundEmail
from wishes.models import CustomRequest, RequestAttachment, RequestMessage

from .helpers import VaylideTestCase

ADRES = "Händellaan 73"


class AddressTests(VaylideTestCase):
    def test_address_on_contact_page_and_in_the_terms_and_pdf(self):
        self.assertIn("Händellaan 73<br>8031 EG Zwolle", Client().get("/contact/").content.decode())
        terms = Client().get("/voorwaarden/").content.decode()
        self.assertIn("Händellaan 73, 8031 EG Zwolle", terms.split('id="modelformulier"', 1)[1])
        from core.voorwaarden_pdf import render_pdf

        # De ä staat in de pdf als WinAnsi-teken (octaal 344).
        self.assertIn(rb"H\344ndellaan 73, 8031 EG Zwolle", render_pdf("2026-09-29", compress=False))

    def test_not_on_the_homepage_invitation_or_in_mails(self):
        self.assertNotIn(ADRES, Client().get("/").content.decode())
        invitation = self.published()
        self.assertNotIn(ADRES, Client().get(f"/u/{invitation.slug}/").content.decode())
        mails = OutboundEmail.objects.filter(kind__in=["order_confirmation", "invitation_live"])
        self.assertEqual(mails.count(), 2)
        for mail in mails:
            self.assertNotIn(ADRES, mail.body_text + mail.body_html, mail.kind)
        confirmation = mails.get(kind="order_confirmation")
        self.assertIn("Vestigingsadres: zie Contact & bedrijfsgegevens", confirmation.body_text)
        self.assertTrue(confirmation.attach_terms_version)  # het adres staat in de pdf-bijlage met de voorwaarden


class OpenPointsTests(VaylideTestCase):
    def test_nothing_open_with_legal_name_and_smtp(self):
        from django.test import override_settings

        from core.privacyverklaring import open_points

        with override_settings(COMPANY_LEGAL_NAME="G.M.Bootsman Consultancy (eenmanszaak)", EMAIL_MODE="smtp"):
            self.assertEqual(open_points(), [])
        html = Client().get("/privacy/").content.decode()
        self.assertIn("7 dagen", html)


class CardRetentionTests(VaylideTestCase):
    def test_card_and_photos_go_90_days_after_offline_but_the_order_stays(self):
        invitation = self.published()
        order = Order.objects.get(invitation=invitation)
        now = timezone.now()
        Invitation.objects.filter(pk=invitation.pk).update(status=Invitation.Status.OFFLINE, available_until=now - timedelta(days=60))
        self.assertEqual(apply_retention(now=now)["verwijderde_kaarten"], 0)
        self.assertTrue(Invitation.objects.filter(pk=invitation.pk).exists())

        report = apply_retention(now=now + timedelta(days=31))
        self.assertEqual(report["verwijderde_kaarten"], 1)
        self.assertFalse(Invitation.objects.filter(pk=invitation.pk).exists())
        order.refresh_from_db()
        self.assertIsNone(order.invitation_id)
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertTrue(order.lines.exists())
        self.assertTrue(Payment.objects.filter(order=order).exists())

    def test_live_card_is_kept(self):
        invitation = self.published()
        apply_retention(now=timezone.now() + timedelta(days=30))
        self.assertTrue(Invitation.objects.filter(pk=invitation.pk).exists())


class AccountRetentionTests(VaylideTestCase):
    def setUp(self):
        self.now = timezone.now()
        self.user = self.make_customer("slapend@example.com")
        User.objects.filter(pk=self.user.pk).update(date_joined=self.now - timedelta(days=701), last_login=None)

    def warnings(self):
        return OutboundEmail.objects.filter(kind="account_opruimen")

    def test_warning_first_then_anonymized_30_days_later(self):
        report = apply_retention(now=self.now)
        self.assertEqual(report["account_waarschuwingen"], 1)
        mail = self.warnings().get()
        self.assertEqual(mail.to, "slapend@example.com")
        self.assertIn("over 30 dagen", mail.body_text)
        self.assertEqual(apply_retention(now=self.now + timedelta(days=1))["account_waarschuwingen"], 0)  # maar één keer

        OutboundEmail.objects.filter(pk=mail.pk).update(created_at=self.now)
        report = apply_retention(now=self.now + timedelta(days=31))
        self.assertEqual(report["geanonimiseerde_accounts"], 1)
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.anonymized_at)
        self.assertNotIn("slapend", self.user.email)

    def test_logging_in_after_the_warning_keeps_the_account(self):
        apply_retention(now=self.now)
        User.objects.filter(pk=self.user.pk).update(last_login=self.now + timedelta(days=2))
        report = apply_retention(now=self.now + timedelta(days=31))
        self.assertEqual(report["geanonimiseerde_accounts"], 0)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.anonymized_at)

    def test_accounts_with_cards_open_wishes_or_staff_are_left_alone(self):
        self.make_invitation(owner=self.user)
        other = self.make_customer("wens@example.com")
        CustomRequest.objects.create(customer=other, subject="Wens", description="x")
        staff = self.make_staff()
        User.objects.filter(pk__in=[other.pk, staff.pk]).update(date_joined=self.now - timedelta(days=800), last_login=None)
        report = apply_retention(now=self.now + timedelta(days=100))
        self.assertEqual(report["account_waarschuwingen"], 0)
        self.assertEqual(report["geanonimiseerde_accounts"], 0)

    def test_recent_account_is_not_warned(self):
        User.objects.filter(pk=self.user.pk).update(date_joined=self.now, last_login=self.now)
        self.assertEqual(apply_retention(now=self.now)["account_waarschuwingen"], 0)


class CorrespondenceRetentionTests(VaylideTestCase):
    def test_contact_messages_after_12_months(self):
        old = ContactMessage.objects.create(name="A", email="a@example.com", message="oud")
        new = ContactMessage.objects.create(name="B", email="b@example.com", message="nieuw")
        ContactMessage.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=366))
        self.assertEqual(apply_retention()["verwijderde_contactberichten"], 1)
        self.assertEqual(list(ContactMessage.objects.values_list("pk", flat=True)), [new.pk])

    def test_finished_wishes_with_messages_and_attachments_after_12_months(self):
        customer = self.make_customer()
        done = CustomRequest.objects.create(customer=customer, subject="Klaar", description="x", status=CustomRequest.Status.DONE)
        RequestMessage.objects.create(request=done, author=customer, body="bericht")
        attachment = RequestAttachment.objects.create(request=done, uploaded_by=customer)
        attachment.file.save("bijlage.txt", ContentFile(b"inhoud"))
        path = attachment.file.name
        open_req = CustomRequest.objects.create(customer=customer, subject="Open", description="x")
        CustomRequest.objects.filter(pk__in=[done.pk, open_req.pk]).update(updated_at=timezone.now() - timedelta(days=400))

        self.assertEqual(apply_retention()["verwijderde_wensen"], 1)
        self.assertFalse(CustomRequest.objects.filter(pk=done.pk).exists())
        self.assertFalse(RequestMessage.objects.filter(request_id=done.pk).exists())
        self.assertFalse(attachment.file.storage.exists(path))
        self.assertTrue(CustomRequest.objects.filter(pk=open_req.pk).exists())

    def test_withdrawals_after_7_years(self):
        old = Withdrawal.objects.create(name="A", email="a@example.com")
        recent = Withdrawal.objects.create(name="B", email="b@example.com")
        Withdrawal.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=7 * 365 + 3))
        Withdrawal.objects.filter(pk=recent.pk).update(created_at=timezone.now() - timedelta(days=6 * 365))
        self.assertEqual(apply_retention()["verwijderde_herroepingen"], 1)
        self.assertEqual(list(Withdrawal.objects.values_list("pk", flat=True)), [recent.pk])

    def test_email_copies_lose_content_and_address_after_90_days(self):
        def mail(status, days):
            m = OutboundEmail.objects.create(to="k@example.com", subject="Je bestelling", body_text="tekst", body_html="<p>x</p>",
                                             status=status, kind="order_confirmation", unique_key=f"m-{status}-{days}")
            OutboundEmail.objects.filter(pk=m.pk).update(created_at=timezone.now() - timedelta(days=days))
            return m

        old, queued, recent = mail("sent", 91), mail("queued", 91), mail("sent", 10)
        self.assertEqual(apply_retention()["opgeschoonde_emails"], 1)
        old.refresh_from_db()
        self.assertEqual((old.to, old.body_text, old.body_html), ("", "", ""))
        self.assertEqual((old.kind, old.status, old.unique_key), ("order_confirmation", "sent", "m-sent-91"))
        for m in (queued, recent):
            m.refresh_from_db()
            self.assertEqual(m.to, "k@example.com")

        from processing.emails import handle_send_email

        failed = mail("failed", 91)
        apply_retention()
        handle_send_email(type("Job", (), {"payload": {"email_id": failed.pk}})())
        failed.refresh_from_db()
        self.assertEqual(failed.attempts, 0)  # opgeschoond: niets meer versturen

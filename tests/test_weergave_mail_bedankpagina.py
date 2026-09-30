"""Weergave na de Render-test (30 september 2026): testmelding volgens de echte e-mailmodus, geen dubbele escaping in
e-mails (wel veilig tegen HTML-invoer), en de echte kaart op de bedankpagina in plaats van een voorbeeld."""
from django.test import Client, override_settings

from accounts.models import LoginCode
from catalog.assets import design_image_url
from processing.emails import queue_email
from processing.models import OutboundEmail

from .helpers import VaylideTestCase

NAMEN = {"partner_1": "Glen", "partner_2": "Lisa’s Zoë & Chloé"}


class EmailTextTests(VaylideTestCase):
    def mail(self, title):
        inv = self.make_invitation(owner=self.make_customer())
        inv.title = title
        return queue_email(to="klant@example.com", subject="Test", template="invitation_live",
                           context={"invitation": inv, "order": None, "portal": "https://x/", "doc_kind": "uitnodiging",
                                    "title_prep": "voor"})

    def test_ampersand_apostrophe_and_accents_are_not_double_escaped(self):
        email = self.mail("Glen & Lisa's Café Zoë")
        self.assertIn("voor Glen & Lisa's Café Zoë staat online", email.body_text)  # platte tekst: letterlijk
        self.assertNotIn("&amp;", email.body_text)
        self.assertIn("Glen &amp; Lisa&#x27;s Café Zoë", email.body_html)  # HTML: precies één keer geëscapet
        self.assertNotIn("&amp;amp;", email.body_html)

    def test_html_in_names_stays_harmless_in_the_html_mail(self):
        email = self.mail('<script>alert(1)</script><a href="x">')
        self.assertNotIn("<script>", email.body_html)
        self.assertNotIn('<a href="x">', email.body_html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", email.body_html)

    def test_order_mails_with_real_names(self):
        customer = self.make_customer("glen@example.com")
        inv = self.make_invitation(owner=customer, names=NAMEN)
        self.pay(inv, customer)
        for email in OutboundEmail.objects.filter(order__invitation=inv):
            self.assertNotIn("&amp;", email.body_text, email.kind)
            self.assertNotIn("&#x27;", email.body_text, email.kind)
            self.assertNotIn("&amp;amp;", email.body_html, email.kind)
        live = OutboundEmail.objects.get(kind="invitation_live", order__invitation=inv)
        self.assertIn("Glen & Lisa’s Zoë & Chloé", live.body_text)


class TestNoticeTests(VaylideTestCase):
    def notice_for(self, **settings):
        with override_settings(**settings):
            return queue_email(to="a@example.com", subject="X", template="login_code",
                               context={"code": "123456", "link": "https://x/", "purpose": "login"}).body_html

    def test_outbox_says_not_sent(self):
        html = self.notice_for(EMAIL_MODE="outbox")
        self.assertIn("deze e-mail is niet echt verzonden", html)

    def test_smtp_in_test_mode_does_not_claim_it_was_not_sent(self):
        html = self.notice_for(EMAIL_MODE="smtp")
        self.assertNotIn("niet echt verzonden", html)
        self.assertIn("testversie van VAYLIDE", html)

    def test_login_page_shows_code_only_when_mails_are_not_sent(self):
        for mode, zichtbaar in (("outbox", True), ("smtp", False)):
            with override_settings(EMAIL_MODE=mode, EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend"):
                c = Client()
                c.post("/inloggen/", {"email": f"{mode}@example.com"})
                html = c.get("/inloggen/code/").content.decode()
                self.assertEqual('class="test-code"' in html, zichtbaar, mode)
                self.assertEqual("niet verzonden" in html, zichtbaar, mode)
                self.assertTrue(LoginCode.objects.filter(email=f"{mode}@example.com").exists())

    def test_withdrawal_page_follows_the_mail_mode(self):
        from orders.models import Withdrawal

        w = Withdrawal.objects.create(name="Glen", email="glen@example.com", product="Kaart")
        with override_settings(EMAIL_MODE="smtp"):
            html = Client().get(f"/herroepen/ontvangen/{w.uid}/").content.decode()
        self.assertNotIn("niet echt verstuurd", html)
        self.assertIn("per e-mail verstuurd naar glen@example.com", html)


class ThankYouCardTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer("glen@example.com")
        self.inv = self.make_invitation(owner=self.customer, names=NAMEN)
        payment = self.pay(self.inv, self.customer)
        self.inv.refresh_from_db()
        self.order = payment.order
        self.c = Client()
        self.c.force_login(self.customer)

    def test_thank_you_page_shows_the_real_card_not_an_example(self):
        html = self.c.get(f"/bestelling/{self.order.uid}/").content.decode()
        self.assertIn(f'src="/u/{self.inv.slug}/?embed=1&amp;open=1"', html)
        self.assertNotIn("Sanne", html)
        self.assertNotIn(design_image_url(self.inv.template_version.template.slug), html)  # geen voorbeeldbeeld
        self.assertIn("Glen &amp; Lisa’s Zoë &amp; Chloé", html)

    def test_the_card_frame_shows_the_real_names_and_may_only_be_framed_by_us(self):
        embed = self.c.get(f"/u/{self.inv.slug}/?embed=1")
        self.assertEqual(embed["X-Frame-Options"], "SAMEORIGIN")
        self.assertIn("frame-ancestors 'self'", embed["Content-Security-Policy"])
        html = embed.content.decode()
        self.assertIn("inv-embed", html)
        self.assertIn("data-direct-open", self.c.get(f"/u/{self.inv.slug}/?embed=1&open=1").content.decode())
        self.assertNotIn("data-direct-open", html)  # zonder open=1 (en voor gasten) blijft het openingsscherm
        self.assertIn("Lisa’s Zoë &amp; Chloé", html)
        self.assertNotIn("&amp;amp;", html)
        normal = Client().get(f"/u/{self.inv.slug}/")
        self.assertEqual(normal["X-Frame-Options"], "DENY")
        self.assertIn("frame-ancestors 'none'", normal["Content-Security-Policy"])

    def test_other_invitations_are_not_shown(self):
        other = self.make_invitation(owner=self.make_customer("ander@example.com"))
        html = self.c.get(f"/bestelling/{self.order.uid}/").content.decode()
        self.assertNotIn(str(other.uid), html)

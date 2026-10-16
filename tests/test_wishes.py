"""Controle 1: extra wensen aanvragen en behandelen."""
from django.test import Client

from orders.models import Order, Payment
from processing.models import OutboundEmail
from wishes.models import CustomRequest

from .helpers import VaylideTestCase, jpeg_file


class WishFlowTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.inv = self.published(owner=self.customer)
        self.c = Client()
        self.c.force_login(self.customer)
        self.staff = Client()
        self.staff.force_login(self.make_staff())

    def create(self, **extra):
        data = {"invitation": str(self.inv.uid), "subject": "Engelse versie", "description": "Kan de uitnodiging ook in het Engels?"}
        data.update(extra)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.c.post("/account/wensen/nieuw/", data)
        self.assertEqual(response.status_code, 302, getattr(response, "content", b"")[:500])
        return CustomRequest.objects.get()

    def test_receipt_only_and_internal_assessment(self):
        req = self.create(attachment=jpeg_file(name="voorbeeld.jpg"))
        self.assertEqual(req.status, CustomRequest.Status.RECEIVED)
        self.assertEqual(req.invitation, self.inv)
        self.assertEqual(req.attachments.count(), 1)
        receipt = OutboundEmail.objects.get(kind="wish_received")
        self.assertNotIn("€", receipt.body_text)  # geen prijs of toezegging
        self.assertIn("ontvangen", receipt.body_text)
        self.assertTrue(OutboundEmail.objects.filter(kind="owner_wish").exists())
        req.refresh_from_db()
        self.assertEqual(req.ai_source, "test")
        self.assertEqual(req.ai_fit, "custom")  # 'Engels' → maatwerk
        # De klant ziet de interne inschatting niet.
        page = self.c.get(f"/account/wensen/{req.uid}/")
        self.assertNotContains(page, req.ai_approach)
        self.assertNotContains(page, "Inschatting")
        # De eigenaar wel.
        self.assertContains(self.staff.get(f"/beheer/wensen/{req.uid}/"), "Interne inschatting")

    def test_paid_proposal_accept_pay_and_execute(self):
        req = self.create()
        self.staff.post(f"/beheer/wensen/{req.uid}/", {"actie": "voorstel", "text": "We maken een tweetalige versie.", "price": "35.00"})
        req.refresh_from_db()
        self.assertEqual(req.status, CustomRequest.Status.PROPOSAL)
        self.assertEqual(req.proposal_price_cents, 3500)
        self.assertTrue(OutboundEmail.objects.filter(kind="wish_update").exists())
        response = self.c.post(f"/account/wensen/{req.uid}/", {"actie": "akkoord", "terms": "on"})
        self.assertEqual(response.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, CustomRequest.Status.AWAITING_PAYMENT)
        order = Order.objects.get(kind=Order.Kind.CUSTOM)
        self.assertEqual(order.total_cents, 3500)
        payment = order.latest_payment
        self.provider_says(payment, Payment.Status.PAID)
        req.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(req.status, CustomRequest.Status.EXECUTING)
        self.assertEqual(order.fulfilment_status, Order.Fulfilment.DONE)
        self.staff.post(f"/beheer/wensen/{req.uid}/", {"actie": "status", "status": "done", "note": "Klaar!"})
        req.refresh_from_db()
        self.assertEqual(req.status, CustomRequest.Status.DONE)

    def test_een_maatwerkbestelling_legt_de_geldende_voorwaardenversie_vast(self):
        """Artikel 16: voor je bestelling geldt de versie die gold bij het akkoord. Dat geldt ook voor maatwerk, en een latere nieuwe versie raakt de bestelling niet."""
        from unittest import mock

        from core.voorwaarden import CURRENT

        req = self.create()
        self.staff.post(f"/beheer/wensen/{req.uid}/", {"actie": "voorstel", "text": "We maken een tweetalige versie.", "price": "35.00"})
        self.assertEqual(self.c.post(f"/account/wensen/{req.uid}/", {"actie": "akkoord", "terms": "on"}).status_code, 302)
        order = Order.objects.get(kind=Order.Kind.CUSTOM)
        self.assertEqual(order.terms_version, CURRENT)
        with mock.patch("core.voorwaarden.CURRENT", "2099-01-01"):
            order.refresh_from_db()
            self.assertEqual(order.terms_version, CURRENT, "een nieuwere versie verandert de vastgelegde versie van een bestaande bestelling niet")

    def test_free_proposal_starts_after_agreement(self):
        req = self.create()
        self.staff.post(f"/beheer/wensen/{req.uid}/", {"actie": "voorstel", "text": "Dat kan kosteloos.", "price": ""})
        self.c.post(f"/account/wensen/{req.uid}/", {"actie": "akkoord", "terms": "on"})
        req.refresh_from_db()
        self.assertEqual(req.status, CustomRequest.Status.EXECUTING)
        self.assertFalse(Order.objects.filter(kind=Order.Kind.CUSTOM).exists())

    def test_internal_notes_stay_internal_and_messages_flow(self):
        req = self.create()
        self.staff.post(f"/beheer/wensen/{req.uid}/", {"actie": "bericht", "body": "Interne gedachte", "internal": "on"})
        self.staff.post(f"/beheer/wensen/{req.uid}/", {"actie": "bericht", "body": "Wil je een voorbeeld sturen?"})
        page = self.c.get(f"/account/wensen/{req.uid}/")
        self.assertNotContains(page, "Interne gedachte")
        self.assertContains(page, "Wil je een voorbeeld sturen?")
        self.c.post(f"/account/wensen/{req.uid}/", {"body": "Zie bijlage", "attachment": jpeg_file(name="voorbeeld2.jpg")})
        self.assertEqual(req.messages.filter(from_staff=False).count(), 1)
        self.assertEqual(req.attachments.count(), 1)

    def test_invalid_attachment_is_refused(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        bad = SimpleUploadedFile("script.exe", b"MZ\x90\x00 dit is geen pdf", content_type="application/pdf")
        response = self.c.post("/account/wensen/nieuw/", {"subject": "Test", "description": "Een langere omschrijving.", "attachment": bad})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "bestandstype wordt niet ondersteund")
        self.assertFalse(CustomRequest.objects.exists())

    def test_anonymous_help_request_requires_login(self):
        response = Client().get("/account/wensen/nieuw/")
        self.assertIn("/inloggen/", response["Location"])


    def test_akkoord_met_een_voorstel_vraagt_om_de_voorwaarden(self):
        """Ook bij maatwerk kan de klant de geldende voorwaarden lezen en moet hij ze accepteren vóór het akkoord; zonder vinkje gebeurt er niets."""
        req = self.create()
        self.staff.post(f"/beheer/wensen/{req.uid}/", {"actie": "voorstel", "text": "We maken een tweetalige versie.", "price": "35.00"})
        pagina = self.c.get(f"/account/wensen/{req.uid}/")
        self.assertContains(pagina, 'name="terms"')
        self.assertContains(pagina, "/voorwaarden/pdf/")
        antwoord = self.c.post(f"/account/wensen/{req.uid}/", {"actie": "akkoord"})
        self.assertContains(antwoord, "Ga akkoord met de algemene voorwaarden")
        req.refresh_from_db()
        self.assertEqual(req.status, CustomRequest.Status.PROPOSAL)
        self.assertFalse(Order.objects.filter(kind=Order.Kind.CUSTOM).exists())

    def test_maatwerk_met_de_nieuwe_prijsstructuur_legt_de_nieuwe_voorwaardenversie_vast(self):
        from django.test import override_settings

        req = self.create()
        self.staff.post(f"/beheer/wensen/{req.uid}/", {"actie": "voorstel", "text": "Extra.", "price": "35.00"})
        with override_settings(PRICING_V2=True):
            self.assertContains(self.c.get(f"/account/wensen/{req.uid}/"), "16 oktober 2026")
            self.c.post(f"/account/wensen/{req.uid}/", {"actie": "akkoord", "terms": "on"})
        self.assertEqual(Order.objects.get(kind=Order.Kind.CUSTOM).terms_version, "2026-10-16")
        self.assertTrue(req.messages.filter(body__contains="algemene voorwaarden (versie 16-10-2026)").exists())

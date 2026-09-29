"""Onze eigen gezichten (Balzaal): standaard uit; met de functie aan (testbewerking of nagebootste Gemini-API) de hele
stroom: uploaden met toestemming, voorbeeld maken, goedkeuren, betalen, publiceren en opruimen. Fictieve testfoto's."""
import base64
import io
import json
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings
from PIL import Image

from catalog.models import AddOn
from gezichten import services
from gezichten.models import FaceRequest
from gezichten.provider import FaceProviderError, GeminiProvider
from invitations.models import MediaAsset
from orders.pricing import build_quote
from catalog.models import Package
from processing.models import Job

from .helpers import VaylideTestCase


def foto(name="gezicht.jpg", color=(200, 160, 140), size=(600, 800)):
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, "JPEG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


AAN = dict(FACES_ENABLED=True, FACES_PROVIDER="test")


class FacesOffByDefaultTests(VaylideTestCase):
    def test_hidden_without_flag_api_and_price(self):
        customer = self.make_customer()
        inv = self.make_invitation(owner=customer, template="balzaal")
        client = Client()
        client.force_login(customer)
        self.assertNotContains(client.get(f"/maken/{inv.uid}/stijl/"), "Onze eigen gezichten")
        self.assertEqual(client.get(f"/maken/{inv.uid}/gezichten/").status_code, 404)
        # Met de functie aan maar zonder prijs (extra optie) nog steeds niet zichtbaar.
        with override_settings(**AAN):
            self.assertFalse(services.feature_available(inv))
            self.assertEqual(client.get(f"/maken/{inv.uid}/gezichten/").status_code, 404)
        # Met Gemini maar zonder sleutel ook niet.
        AddOn.objects.create(code="gezichten", name="Eigen gezichten", description="", price_cents=100, feature="gezichten")
        with override_settings(FACES_ENABLED=True, FACES_PROVIDER="gemini", GEMINI_API_KEY=""):
            self.assertFalse(services.feature_available(inv))

    def test_not_for_designs_without_a_couple(self):
        AddOn.objects.create(code="gezichten", name="Eigen gezichten", description="", price_cents=100, feature="gezichten")
        with override_settings(**AAN):
            self.assertFalse(services.feature_available(self.make_invitation(template="liefde-op-papier")))


@override_settings(**AAN)
class FacesFlowTests(VaylideTestCase):
    def setUp(self):
        # Alleen een testbedrag; de echte prijs bepaalt de eigenaar.
        AddOn.objects.create(code="gezichten", name="Eigen gezichten", description="", price_cents=100, feature="gezichten")
        AddOn.objects.create(code="special-balzaal", name="Special Balzaal", description="", price_cents=100, feature="special")
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer, template="balzaal")
        self.client = Client()
        self.client.force_login(self.customer)
        self.url = f"/maken/{self.inv.uid}/gezichten/"

    def upload(self, consent=True, **files):
        data = {"actie": "uploaden", **files}
        if consent:
            data["toestemming"] = "ja"
        return self.client.post(self.url, data, follow=True)

    def make(self):
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(self.url, {"actie": "maken"}, follow=True)

    def test_consent_valid_files_and_both_photos_required(self):
        page = self.client.get(self.url)
        self.assertContains(page, "toestemming geven")
        self.assertContains(page, "Exacte gelijkenis kunnen we niet garanderen")
        self.assertContains(self.upload(consent=False, foto_vrouw=foto()), "Bevestig eerst")
        self.assertFalse(FaceRequest.objects.exists())
        nep = SimpleUploadedFile("nep.jpg", b"geen foto", content_type="image/jpeg")
        self.assertContains(self.upload(foto_vrouw=nep), "geen geldige foto")
        self.upload(foto_vrouw=foto())
        self.assertContains(self.make(), "Upload een foto van allebei")
        self.assertEqual(FaceRequest.objects.get().attempts_used, 0)

    def test_generate_approve_pay_publish_and_lock(self):
        self.upload(foto_vrouw=foto("vrouw.jpg"), foto_man=foto("man.jpg", (120, 90, 70)))
        req = FaceRequest.objects.get()
        self.assertTrue(req.consent_at)
        self.assertIn("toestemming", req.consent_text)
        self.make()
        req.refresh_from_db()
        self.assertEqual(req.status, FaceRequest.Status.READY)
        self.assertEqual((req.attempts_used, req.provider), (1, "test"))
        self.assertContains(self.client.get(self.url), "Dit voorbeeld goedkeuren")
        # Alleen de eigenaar ziet de foto's en het voorbeeld.
        for soort in ("vrouw", "man", "voorbeeld"):
            self.assertEqual(self.client.get(f"{self.url}beeld/{soort}/").status_code, 200)
            self.assertEqual(Client().get(f"{self.url}beeld/{soort}/").status_code, 404)
            other = Client()
            other.force_login(self.make_customer(f"ander-{soort}@example.com"))
            self.assertEqual(other.get(f"{self.url}beeld/{soort}/").status_code, 404)
        self.assertEqual(Client().get(self.url).status_code, 404)
        # Dezelfde taak nog eens uitvoeren maakt geen tweede voorbeeld (geen dubbele kosten).
        job = Job.objects.get(kind="generate_faces")
        with mock.patch("gezichten.provider.TestProvider.generate") as gen:
            services.handle_generate(job)
            gen.assert_not_called()
        # Goedkeuren: de afbeelding komt als 'scene' bij de uitnodiging en op de kaart.
        self.client.post(self.url, {"actie": "goedkeuren"})
        self.inv.refresh_from_db()
        eigen = self.inv.draft_content["style"]["paar_eigen"]
        asset = MediaAsset.objects.get(uid=eigen)
        self.assertEqual(asset.kind, MediaAsset.Kind.SCENE)
        preview = self.client.get(f"/maken/{self.inv.uid}/voorbeeld/weergave/").content.decode()
        self.assertIn('data-paar="eigen"', preview)
        self.assertNotIn("paar-bruin-blond-560.webp", preview)
        # Bij het afrekenen telt de extra optie mee.
        quote = build_quote(self.inv.draft_content, Package.objects.get(code="essentieel"), [], template_version=self.inv.template_version)
        self.assertIn("gezichten", quote.features)
        self.assertIn("optie:gezichten", [line.code for line in quote.lines])
        # Betalen en publiceren: precies deze goedgekeurde versie, zonder opnieuw te genereren.
        with mock.patch("gezichten.provider.TestProvider.generate") as gen:
            self.pay(self.inv, self.customer)
            gen.assert_not_called()
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.published_version.content["style"]["paar_eigen"], eigen)
        public = Client().get(self.inv.public_path)
        self.assertContains(public, f"/u/{self.inv.slug}/media/{eigen}/middel/")
        self.assertEqual(Client().get(f"/u/{self.inv.slug}/media/{eigen}/groot/").status_code, 200)
        # Daarna ligt het vast.
        self.assertContains(self.client.get(self.url), "Het bruidspaar ligt vast")
        with self.assertRaises(services.FaceError):
            services.start_generation(self.inv)
        # De nachtelijke opschoning haalt de losse foto's weg; de goedgekeurde versie blijft.
        from core.privacy import apply_retention

        report = apply_retention()
        self.assertEqual(report["opgeschoonde_gezichtfotos"], 1)
        req.refresh_from_db()
        self.assertFalse(req.photo_bride or req.photo_groom or req.result)
        self.assertEqual(Client().get(f"/u/{self.inv.slug}/media/{eigen}/groot/").status_code, 200)

    def test_attempts_are_limited_and_failures_do_not_count(self):
        self.upload(foto_vrouw=foto(), foto_man=foto())
        with mock.patch("gezichten.provider.TestProvider.generate", side_effect=FaceProviderError("Deze foto's konden niet worden gebruikt.")):
            self.make()
        req = FaceRequest.objects.get()
        self.assertEqual(req.status, FaceRequest.Status.FAILED)
        self.assertEqual(req.attempts_used, 0)  # mislukt: poging telt niet
        self.assertContains(self.client.get(self.url), "konden niet worden gebruikt")
        self.upload(foto_vrouw=foto())  # nieuwe foto: weer klaar voor een poging
        for _ in range(3):
            self.make()
        req.refresh_from_db()
        self.assertEqual((req.attempts_used, req.attempts_left), (3, 0))
        self.assertContains(self.make(), "alle pogingen gebruikt")
        self.assertEqual(Job.objects.filter(kind="generate_faces").count(), 4)

    def test_busy_api_is_retried_once_then_reported(self):
        self.upload(foto_vrouw=foto(), foto_man=foto())
        with mock.patch("gezichten.provider.TestProvider.generate", side_effect=FaceProviderError("even druk", retryable=True)):
            self.make()
            job = Job.objects.get(kind="generate_faces")
            self.assertEqual(job.status, Job.Status.FAILED)  # wordt later nog één keer geprobeerd
            from processing.jobs import retry

            retry(job)
        req = FaceRequest.objects.get()
        self.assertEqual(req.status, FaceRequest.Status.FAILED)
        self.assertEqual(req.attempts_used, 0)

    def test_remove_deletes_photos_and_the_own_version(self):
        self.upload(foto_vrouw=foto(), foto_man=foto())
        self.make()
        self.client.post(self.url, {"actie": "goedkeuren"})
        req = FaceRequest.objects.get()
        paths = [req.photo_bride.path, req.photo_groom.path, req.result.path]
        self.client.post(self.url, {"actie": "verwijderen"})
        import os

        self.assertFalse(any(os.path.exists(p) for p in paths))
        self.assertFalse(FaceRequest.objects.exists())
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["style"]["paar_eigen"], "")
        self.assertFalse(MediaAsset.objects.filter(invitation=self.inv, kind=MediaAsset.Kind.SCENE).exists())

    def test_faked_reference_is_not_accepted(self):
        from invitations.services import save_draft

        other = self.make_invitation(owner=self.make_customer("x@example.com"), template="balzaal")
        stranger = MediaAsset.objects.create(invitation=other, kind=MediaAsset.Kind.SCENE, content_type="image/webp")
        content = dict(self.inv.draft_content)
        content["style"] = dict(content["style"], paar_eigen=str(stranger.uid))
        inv = save_draft(self.inv, expected_rev=self.inv.draft_rev, content=content, user=self.customer)
        self.assertEqual(inv.draft_content["style"]["paar_eigen"], "")


class GeminiProviderTests(VaylideTestCase):
    def _response(self, payload):
        class R:
            def read(self_inner):
                return json.dumps(payload).encode()

            def __enter__(self_inner):
                return self_inner

            def __exit__(self_inner, *a):
                return False
        return R()

    def scene(self):
        buffer = io.BytesIO()
        Image.new("RGB", (941, 1672), (240, 230, 220)).save(buffer, "PNG")
        return buffer.getvalue()

    @override_settings(GEMINI_API_KEY="nagebootste-sleutel", FACES_MODEL="gemini-3-pro-image")
    def test_request_uses_server_key_and_returns_the_image(self):
        png = io.BytesIO()
        Image.new("RGB", (900, 1600), (10, 20, 30)).save(png, "PNG")
        answer = {"output_image": {"mime_type": "image/png", "data": base64.b64encode(png.getvalue()).decode()}}
        with mock.patch("gezichten.provider.urllib.request.urlopen", return_value=self._response(answer)) as urlopen, \
                self.assertLogs("gezichten", level="WARNING") as logs:
            import logging

            logging.getLogger("gezichten").warning("controle")
            image = GeminiProvider().generate(self.scene(), foto().read(), foto().read())
        request = urlopen.call_args[0][0]
        self.assertEqual(request.headers["X-goog-api-key"], "nagebootste-sleutel")
        body = json.loads(request.data)
        self.assertEqual(body["model"], "gemini-3-pro-image")
        self.assertEqual(sum(1 for p in body["input"] if p["type"] == "image"), 3)
        self.assertIn("bright white", body["input"][0]["text"])
        self.assertNotIn("nagebootste-sleutel", request.full_url)
        self.assertNotIn("nagebootste-sleutel", " ".join(logs.output))
        with Image.open(io.BytesIO(image)) as img:
            self.assertEqual(img.size, (900, 1600))

    @override_settings(GEMINI_API_KEY="nagebootste-sleutel")
    def test_errors_become_friendly_messages(self):
        import urllib.error

        busy = urllib.error.HTTPError("u", 503, "druk", {}, io.BytesIO(b"{}"))
        with mock.patch("gezichten.provider.urllib.request.urlopen", side_effect=busy):
            with self.assertRaises(FaceProviderError) as ctx:
                GeminiProvider().generate(self.scene(), foto().read(), foto().read())
        self.assertTrue(ctx.exception.retryable)
        bad = urllib.error.HTTPError("u", 400, "fout", {}, io.BytesIO(b"{}"))
        with mock.patch("gezichten.provider.urllib.request.urlopen", side_effect=bad):
            with self.assertRaises(FaceProviderError) as ctx:
                GeminiProvider().generate(self.scene(), foto().read(), foto().read())
        self.assertFalse(ctx.exception.retryable)
        with mock.patch("gezichten.provider.urllib.request.urlopen", return_value=self._response({"output": []})):
            with self.assertRaises(FaceProviderError):
                GeminiProvider().generate(self.scene(), foto().read(), foto().read())

    @override_settings(GEMINI_API_KEY="")
    def test_no_key_no_provider(self):
        with self.assertRaises(FaceProviderError):
            GeminiProvider()

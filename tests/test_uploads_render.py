"""Controle 1 en 2: uploads, weergave (lange namen, ontbrekende gegevens, tijdzones),
prijsberekening, bewaartermijnen en beveiligingsheaders."""
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.utils import timezone
from PIL import Image

from catalog.models import Package, Template
from catalog.occasions import OCCASION_CHOICES
from core.privacy import apply_retention
from invitations.content import event_times
from invitations.ics import build_ics
from invitations.models import GuestResponse, Invitation, MediaAsset
from invitations.render import RenderOptions, build_view
from invitations.services import save_draft
from orders.pricing import build_quote, compare_packages, recommended

from .helpers import VaylideTestCase, jpeg_file, toon_verborgen_ontwerpen


class UploadTests(VaylideTestCase):
    def setUp(self):
        self.c = Client()
        uid = self.c.post("/maken/", {"occasion": "bruiloft", "template": "liefde-op-papier"})["Location"].split("/")[2]
        self.inv = Invitation.objects.get(uid=uid)

    def upload(self, **files):
        return self.c.post(f"/maken/{self.inv.uid}/upload/", files, HTTP_ACCEPT="application/json")

    def test_exif_and_gps_are_removed_and_sizes_created(self):
        response = self.upload(fotos=jpeg_file(2400, 1600, exif_gps=True))
        self.assertEqual(response.status_code, 200)
        asset = MediaAsset.objects.get()
        with asset.file.open("rb") as handle:
            image = Image.open(handle)
            self.assertEqual(image.format, "WEBP")
            self.assertFalse(image.getexif())
            self.assertLessEqual(max(image.size), 2000)
        self.assertTrue(asset.file_medium.name and asset.file_thumb.name)
        self.assertEqual((asset.width, asset.height), (2400, 1600))
        self.assertEqual(asset.orientation, "liggend")

    def test_wrong_type_too_small_and_fake_images_are_refused(self):
        pdf = SimpleUploadedFile("brief.pdf", b"%PDF-1.4 niet een foto", content_type="application/pdf")
        fake = SimpleUploadedFile("foto.jpg", b"dit is geen jpeg", content_type="image/jpeg")
        response = self.upload(fotos=[pdf, fake, jpeg_file(200, 200, name="klein.jpg")])
        errors = " ".join(response.json()["errors"])
        self.assertIn("brief.pdf: dit bestandstype wordt niet ondersteund", errors)
        self.assertIn("foto.jpg: Dit bestand is geen geldige foto", errors)
        self.assertIn("te klein", errors)
        self.assertFalse(MediaAsset.objects.exists())

    def test_size_limit(self):
        with self.settings(UPLOAD_LIMITS={**self.settings_limits(), "photo_max_bytes": 1000}):
            response = self.upload(fotos=jpeg_file(1200, 900))
        self.assertIn("te groot", " ".join(response.json()["errors"]))

    def settings_limits(self):
        from django.conf import settings

        return dict(settings.UPLOAD_LIMITS)

    def test_audio_validation(self):
        mp3 = SimpleUploadedFile("lied.mp3", b"ID3\x03\x00\x00\x00" + b"\x00" * 200, content_type="audio/mpeg")
        fake = SimpleUploadedFile("lied2.mp3", b"<html>geen muziek</html>", content_type="audio/mpeg")
        self.assertEqual(self.upload(muziek=mp3).status_code, 200)
        self.assertIn("niet ondersteund", " ".join(self.upload(muziek=fake).json()["errors"]))
        self.assertEqual(MediaAsset.objects.filter(kind="audio").count(), 1)

    def test_request_size_limit(self):
        from core.middleware import RequestSizeLimitMiddleware
        from django.test import RequestFactory

        with self.settings(VIERLIEF_MAX_REQUEST_BYTES=100):
            middleware = RequestSizeLimitMiddleware(lambda r: None)
            request = RequestFactory().post("/maken/", data="x" * 500, content_type="text/plain")
            self.assertEqual(middleware(request).status_code, 413)


class RenderTests(VaylideTestCase):
    def view_for(self, invitation, **opts):
        options = RenderOptions(mode="live", features=opts.pop("features", []), **opts)
        return build_view(occasion=invitation.occasion, content=invitation.draft_content, overrides={},
                          template_version=invitation.template_version, options=options)

    def test_long_names_get_smaller_type_and_render_everywhere(self):
        long_a = "Maximiliaan-Alexander van den Boogaard"
        for slug in ["liefde-op-papier", "avondgoud", "puur-moment"]:
            inv = self.make_invitation(template=slug, names={"partner_1": long_a, "partner_2": "Ernestina"})
            view = self.view_for(inv)
            self.assertEqual(view["names_size"], "xlong")
            owner = self.make_customer(f"{slug}@example.com")
            inv.owner = owner
            inv.save()
            self.pay(inv, owner)
            inv.refresh_from_db()
            page = Client().get(inv.public_path)
            self.assertContains(page, long_a)
            self.assertContains(page, "names--xlong")

    def test_empty_optional_sections_are_hidden(self):
        inv = self.make_invitation(program=[], practical=[], dresscode={"text": "", "colors": []}, closing_text="",
                                   contact={"name": "", "phone": "", "email": "", "note": ""}, welcome_text="")
        view = self.view_for(inv)
        for key in ("program", "practical", "dresscode", "contact", "closing", "gallery", "story", "music"):
            self.assertFalse(view["show"][key], key)
        self.assertTrue(view["show"]["location"])
        owner = self.make_customer()
        inv.owner = owner
        inv.save()
        self.pay(inv, owner)
        inv.refresh_from_db()
        page = Client().get(inv.public_path).content.decode()
        self.assertNotIn(">Programma<", page)
        self.assertNotIn(">Dresscode<", page)
        self.assertIn("Kasteel Test", page)

    def test_paid_features_hidden_without_entitlement(self):
        inv = self.make_invitation(story={"title": "Ons verhaal", "text": "Het begon in Parijs."})
        content = dict(inv.draft_content)
        content["sections"] = dict(content["sections"], story=True)
        inv = save_draft(inv, expected_rev=None, content=content)
        self.assertFalse(self.view_for(inv, features=[])["show"]["story"])
        self.assertTrue(self.view_for(inv, features=["story"])["show"]["story"])

    def test_timezone_is_respected(self):
        inv = self.make_invitation(date="2027-01-15", start_time="18:00", timezone="America/Curacao")
        times = event_times(inv.draft_content)
        self.assertEqual(times.start.utcoffset(), timedelta(hours=-4))
        view = self.view_for(inv)
        self.assertTrue(view["start_iso"].endswith("-04:00"))
        self.assertEqual(view["tz_label"], "Curaçao")
        ics = build_ics(uid="x", title="Test", start=times.start, end=times.end, location="Willemstad", description="", url="")
        self.assertIn("DTSTART:20270115T220000Z", ics)
        self.assertIn("\r\n", ics)
        # Na middernacht eindigen telt door naar de volgende dag.
        late = self.make_invitation(start_time="21:00", end_time="02:00")
        t = event_times(late.draft_content)
        self.assertGreater(t.end, t.start)

    def test_all_demos_render_for_all_occasions(self):
        toon_verborgen_ontwerpen()
        for template in Template.objects.all():
            for occasion, _ in OCCASION_CHOICES:
                response = Client().get(f"/voorbeeld/{template.slug}/?gelegenheid={occasion}")
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Voorbeelduitnodiging")
                self.assertContains(response, "Dit is een voorbeeld")

    def test_no_js_fallback_and_music_requires_action(self):
        response = Client().get("/voorbeeld/liefde-op-papier/")
        html = response.content.decode()
        self.assertIn('href="#uitnodiging"', html)  # opening werkt ook zonder script
        self.assertNotIn("autoplay", html)
        self.assertIn("data-music-toggle", html)


class SecurityHeaderTests(VaylideTestCase):
    def test_csp_and_private_headers(self):
        response = Client().get("/")
        self.assertIn("default-src 'self'", response["Content-Security-Policy"])
        self.assertIn("frame-ancestors 'none'", response["Content-Security-Policy"])
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertNotIn("X-Robots-Tag", response)
        demo = Client().get("/voorbeeld/avondgoud/")
        self.assertEqual(demo["X-Robots-Tag"], "noindex, nofollow, noarchive")
        self.assertIn("frame-ancestors 'self'", demo["Content-Security-Policy"])
        account = Client().get("/inloggen/")
        self.assertEqual(account["Cache-Control"], "private, no-store")
        robots = Client().get("/robots.txt").content.decode()
        self.assertIn("Disallow: /u/", robots)
        self.assertIn("Disallow: /beheer/", robots)


class PricingTests(VaylideTestCase):
    def test_required_addons_and_recommendation(self):
        inv = self.make_invitation()
        content = dict(inv.draft_content)
        content["sections"] = dict(content["sections"], story=True, music=True)
        content["story"] = {"title": "Ons verhaal", "text": "Tekst"}
        content["music"] = {"asset": "x", "title": ""}  # alleen voor de berekening
        essentieel = Package.objects.get(code="essentieel")
        quote = build_quote(content, essentieel)
        codes = [line.code for line in quote.lines]
        self.assertIn("optie:muziek", codes)
        self.assertIn("optie:verhaal", codes)
        self.assertEqual(quote.total_cents, 3900 + 900 + 600)
        quotes = compare_packages(content)
        self.assertEqual(recommended(quotes).package.code, "essentieel")  # 54 < 69
        content["sections"]["gallery"] = True
        content["photos"] = {"hero": None, "gallery": [{"asset": "y"}]}
        content["rsvp"] = dict(content["rsvp"], questions=[{"id": "q1", "label": "?", "type": "text"}])
        self.assertEqual(recommended(compare_packages(content)).package.code, "compleet")  # 39+9+6+12+6=72 > 69

    def test_price_changes_do_not_affect_existing_orders(self):
        owner = self.make_customer()
        inv = self.published(owner=owner)
        order = inv.orders.get()
        Package.objects.filter(code="essentieel").update(price_cents=9900)
        order.refresh_from_db()
        self.assertEqual(order.total_cents, 3900)

    def test_extend_option_adds_months(self):
        inv = self.make_invitation()
        quote = build_quote(inv.draft_content, Package.objects.get(code="essentieel"), ["langer-online"])
        self.assertEqual(quote.availability_months, 18)
        from orders.pricing import PricingError

        with self.assertRaises(PricingError):
            build_quote(inv.draft_content, Package.objects.get(code="essentieel"), ["gratis"])


class RetentionTests(VaylideTestCase):
    def test_expiry_and_guest_data_removal(self):
        owner = self.make_customer()
        inv = self.published(owner=owner)
        GuestResponse.objects.create(invitation=inv, client_token="r" * 20, name="Oud", attending=True, party_size=1, edit_token_hash="e" * 64)
        Invitation.objects.filter(pk=inv.pk).update(available_until=timezone.now() - timedelta(days=1))
        report = apply_retention()
        inv.refresh_from_db()
        self.assertEqual(report["verlopen_uitnodigingen"], 1)
        self.assertEqual(inv.status, Invitation.Status.EXPIRED)
        self.assertEqual(Client().get(inv.public_path).status_code, 410)
        self.assertTrue(GuestResponse.objects.exists())  # nog binnen bewaartermijn
        Invitation.objects.filter(pk=inv.pk).update(available_until=timezone.now() - timedelta(days=200))
        apply_retention()
        self.assertFalse(GuestResponse.objects.exists())

    def test_anonymous_drafts_are_cleaned_up(self):
        inv = self.make_invitation(owner=None)
        Invitation.objects.filter(pk=inv.pk).update(updated_at=timezone.now() - timedelta(days=45))
        apply_retention()
        self.assertFalse(Invitation.objects.filter(pk=inv.pk).exists())

    def test_customer_can_delete_account(self):
        owner = self.make_customer("weg@example.com")
        inv = self.published(owner=owner)
        c = Client()
        c.force_login(owner)
        c.post("/account/gegevens/", {"actie": "verwijderen", "bevestig": "verwijderen"})
        owner.refresh_from_db()
        self.assertTrue(owner.email.startswith("verwijderd-"))
        self.assertFalse(owner.is_active)
        self.assertFalse(Invitation.objects.filter(pk=inv.pk).exists())
        self.assertEqual(owner.orders.count(), 1)  # boekhouding blijft
        self.assertEqual(owner.orders.get().invitation_title, "")  # zonder namen
        from processing.models import OutboundEmail

        self.assertFalse(OutboundEmail.objects.filter(to="weg@example.com").exists())
        self.assertFalse(OutboundEmail.objects.filter(body_text__contains="Anna").exists())


class NewDesignTests(VaylideTestCase):
    def test_design_without_cover_image_uses_placeholder(self):
        from catalog.assets import design_image_path
        from catalog.models import TemplateVersion

        base = Template.objects.get(slug="liefde-op-papier").current_version
        template = Template.objects.create(slug="nieuw-ontwerp-test", name="Nieuw ontwerp test", occasions=["bruiloft"], sort_order=99)
        version = TemplateVersion.objects.create(template=template, number=1, renderer=base.renderer, manifest=dict(base.manifest, slug="nieuw-ontwerp-test"))
        template.current_version = version
        template.save()
        self.assertEqual(design_image_path("nieuw-ontwerp-test"), "img/designs/_standaard.webp")
        self.assertEqual(design_image_path("liefde-op-papier"), "img/designs/liefde-op-papier.webp")
        for url in ["/ontwerpen/", "/ontwerpen/?gelegenheid=bruiloft", "/maken/?gelegenheid=bruiloft"]:
            response = Client().get(url)
            self.assertContains(response, "Nieuw ontwerp test", msg_prefix=url)
            self.assertContains(response, "img/designs/_standaard.webp", msg_prefix=url)


class DesignManifestValidationTests(VaylideTestCase):
    def make_folder(self, root, slug="nieuw", version="v1", files=("invitation.html", "style.css")):
        from pathlib import Path

        folder = Path(root) / slug / version
        folder.mkdir(parents=True)
        for name in files:
            (folder / name).write_text("")
        return folder / "manifest.json"

    def test_clear_errors_for_incomplete_design(self):
        import tempfile

        from catalog.seed import DesignError, validate_manifest

        good = {"slug": "nieuw", "version": 1, "name": "Nieuw", "occasions": ["bruiloft"],
                "palettes": [{"key": "a", "name": "A", "vars": {"--x": "#fff"}}]}
        with tempfile.TemporaryDirectory() as root:
            path = self.make_folder(root)
            validate_manifest(path, good)  # geen fout
            for bad, fragment in [
                (dict(good, name=""), "mist: name"),
                (dict(good, slug="anders"), "gelijk zijn aan de mapnaam"),
                (dict(good, version=2), "hoort bij map v2"),
                (dict(good, occasions=["feest"]), "onbekende gelegenheid"),
                (dict(good, palettes=[{"key": "a"}]), "'key', 'name' en 'vars'"),
            ]:
                with self.assertRaisesMessage(DesignError, fragment):
                    validate_manifest(path, bad)
        with tempfile.TemporaryDirectory() as root:
            path = self.make_folder(root, files=("invitation.html",))
            with self.assertRaisesMessage(DesignError, "style.css ontbreekt"):
                validate_manifest(path, good)

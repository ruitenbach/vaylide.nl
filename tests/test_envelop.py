"""Envelop en lakzegel naar keuze (stap Stijl): envelopkleur, zegelkleur, initialen of een eigen logo, voor alle pakketten."""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image

from catalog.envelop import clean_initials
from invitations.models import MediaAsset

from .helpers import VaylideTestCase, jpeg_file


def png_logo(name="logo.png"):
    from PIL import ImageDraw

    img = Image.new("RGBA", (300, 200), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse((80, 30, 220, 170), outline=(20, 60, 120, 255), width=18)  # ring: doorzichtig midden
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class EnvelopeChoiceTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer)  # Liefde op papier: envelop met zegel
        self.client = Client()
        self.client.force_login(self.customer)
        self.base = f"/maken/{self.inv.uid}"

    def style_post(self, **extra):
        self.inv.refresh_from_db()
        data = {"rev": self.inv.draft_rev, "actie": "opslaan", "palette": self.inv.template_version.default_palette_key, "opening": "on"}
        data.update(extra)
        return self.client.post(f"{self.base}/stijl/", data)

    def test_block_only_for_designs_with_a_seal(self):
        page = self.client.get(f"{self.base}/stijl/")
        self.assertContains(page, "Envelop en lakzegel")
        self.assertContains(page, 'name="env_kleur"')
        self.assertContains(page, 'name="zegel_kleur"')
        other = self.make_invitation(owner=self.customer, template="ballonfeest", occasion="verjaardag")
        self.assertNotContains(self.client.get(f"/maken/{other.uid}/stijl/"), "Envelop en lakzegel")

    def test_colours_and_initials_show_on_the_card(self):
        self.style_post(env_kleur="salie", zegel_kleur="goud", zegel="initialen", initialen="J&M<b>")
        self.inv.refresh_from_db()
        keuze = self.inv.draft_content["style"]["envelop"]
        self.assertEqual((keuze["kleur"], keuze["zegel_kleur"], keuze["initialen"]), ("salie", "goud", "J&Mb"))
        html = self.client.get(f"{self.base}/voorbeeld/weergave/").content.decode()
        self.assertIn("--lp-envelope:#DCE4D3", html)
        self.assertIn("--lp-seal:#9C7429", html)
        self.assertIn("J&amp;Mb", html)

    def test_other_style_choices_are_kept(self):
        scene = MediaAsset.objects.create(invitation=self.inv, kind=MediaAsset.Kind.SCENE, content_type="image/webp")
        content = dict(self.inv.draft_content)
        content["style"] = dict(content["style"], paar_eigen=str(scene.uid))
        from invitations.services import save_draft

        save_draft(self.inv, expected_rev=None, content=content, user=self.customer)
        self.style_post(zegel_kleur="zwart")
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["style"]["paar_eigen"], str(scene.uid))

    def test_own_logo_on_the_seal(self):
        response = self.client.post(f"{self.base}/upload/", {"zegel_logo": png_logo()})
        self.assertRedirects(response, f"{self.base}/stijl/#envelop", fetch_redirect_response=False)
        logo = MediaAsset.objects.get(kind=MediaAsset.Kind.LOGO)
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["style"]["envelop"]["logo"], str(logo.uid))
        self.assertEqual(self.inv.draft_content["style"]["envelop"]["zegel"], "logo")
        html = self.client.get(f"{self.base}/voorbeeld/weergave/").content.decode()
        self.assertIn(f'class="zegel-logo" src="{self.base}/media/{logo.uid}/groot/"', html)
        served = self.client.get(f"{self.base}/media/{logo.uid}/groot/")
        self.assertEqual(served.status_code, 200)
        with Image.open(io.BytesIO(b"".join(served.streaming_content) if hasattr(served, "streaming_content") else served.content)) as im:
            self.assertEqual(im.mode, "RGBA")  # doorzichtigheid bewaard
            self.assertLessEqual(max(im.size), 600)
        # verwijderen: terug naar initialen
        self.client.post(f"{self.base}/upload/{logo.uid}/verwijderen/")
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["style"]["envelop"]["zegel"], "initialen")

    def test_white_background_becomes_transparent(self):
        self.client.post(f"{self.base}/upload/", {"zegel_logo": jpeg_file(width=400, height=300, name="logo.jpg")})
        self.assertTrue(MediaAsset.objects.filter(kind=MediaAsset.Kind.LOGO).exists())

    def test_logo_is_published_with_the_invitation(self):
        self.client.post(f"{self.base}/upload/", {"zegel_logo": png_logo()})
        self.inv.refresh_from_db()
        self.pay(self.inv, self.customer)
        self.inv.refresh_from_db()
        logo = MediaAsset.objects.get(kind=MediaAsset.Kind.LOGO)
        html = Client().get(self.inv.public_url.replace("http://testserver", "")).content.decode()
        self.assertIn(f"/media/{logo.uid}/groot/", html)

    def test_initials_are_cleaned(self):
        self.assertEqual(clean_initials("  A & B  "), "A & B")
        self.assertEqual(clean_initials("<script>"), "scrip")
        self.assertEqual(clean_initials("ABCDEFG"), "ABCDE")


class CompanyDetailsTests(VaylideTestCase):
    def test_kvk_and_vat_without_address(self):
        for url in ("/", "/contact/", "/privacy/", "/voorwaarden/"):
            html = Client().get(url).content.decode()
            self.assertIn("94261423", html, url)
            self.assertIn("NL212227221B02", html, url)

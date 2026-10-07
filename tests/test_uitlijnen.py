"""Automatisch uitlijnen van foto's (gezichten met YuNet) en een automatisch gekozen hoofdfoto na het uploaden."""
import io

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from PIL import Image

from invitations.focus import MODEL, detect
from invitations.models import MediaAsset

from .helpers import VaylideTestCase, jpeg_file

SCENE = settings.BASE_DIR / "designs/balzaal/v1/img/scene-bruin-blond.webp"  # fictief bruidspaar
BALLONNEN = settings.BASE_DIR / "static/img/demo/ballonnen.webp"  # geen mensen


def couple_jpeg(name="paar.jpg"):
    buffer = io.BytesIO()
    with Image.open(SCENE) as im:
        im.convert("RGB").save(buffer, "JPEG", quality=90)
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/jpeg")


class FocusDetectionTests(VaylideTestCase):
    def test_model_is_present(self):
        self.assertTrue(MODEL.is_file())

    def test_finds_both_faces_of_the_couple(self):
        with Image.open(SCENE) as im:
            focus = detect(im)
        self.assertEqual(focus.faces, 2)
        self.assertTrue(30 <= focus.x <= 45, focus)  # tussen de twee gezichten, links van het midden
        self.assertTrue(38 <= focus.y <= 50, focus)

    def test_no_faces_in_a_photo_without_people(self):
        with Image.open(BALLONNEN) as im:
            focus = detect(im)
        self.assertEqual(focus.faces, 0)
        self.assertTrue(20 <= focus.x <= 80 and 20 <= focus.y <= 80)


class AutoPlacementTests(VaylideTestCase):
    def setUp(self):
        self.customer = self.make_customer()
        self.inv = self.make_invitation(owner=self.customer)
        self.client = Client()
        self.client.force_login(self.customer)
        self.base = f"/maken/{self.inv.uid}"

    def upload(self, *files):
        return self.client.post(f"{self.base}/upload/", {"fotos": list(files)}, HTTP_ACCEPT="application/json")

    def test_upload_aligns_and_picks_the_couple_as_hero(self):
        self.assertEqual(self.upload(jpeg_file(name="landschap.jpg"), couple_jpeg()).status_code, 200)
        couple = MediaAsset.objects.get(original_name="paar.jpg")
        self.assertEqual(couple.faces, 2)
        self.inv.refresh_from_db()
        hero = self.inv.draft_content["photos"]["hero"]
        self.assertEqual(hero["asset"], str(couple.uid))  # de foto met het paar, niet de eerste
        self.assertEqual((hero["x"], hero["y"]), (couple.focus_x, couple.focus_y))
        self.assertEqual(self.inv.draft_content["photos"]["gallery"], [])  # de galerij (extra optie) niet vanzelf
        page = self.client.get(f"{self.base}/fotos/")
        self.assertContains(page, "staat als hoofdfoto op je kaart, uitgelijnd op de gezichten")
        self.assertContains(page, "2 gezichten gevonden")
        self.assertContains(page, f'data-auto-x="{couple.focus_x}"')

    def test_an_existing_hero_is_never_replaced(self):
        self.upload(jpeg_file(name="eerste.jpg"))
        self.inv.refresh_from_db()
        first = self.inv.draft_content["photos"]["hero"]["asset"]
        self.upload(couple_jpeg())
        self.inv.refresh_from_db()
        self.assertEqual(self.inv.draft_content["photos"]["hero"]["asset"], first)

    def test_new_photo_starts_at_its_automatic_point(self):
        self.upload(jpeg_file(name="eerste.jpg"), couple_jpeg())
        couple = MediaAsset.objects.get(original_name="paar.jpg")
        page = self.client.get(f"{self.base}/fotos/").content.decode()
        self.assertIn(f'name="x_{couple.uid}" value="{couple.focus_x}"', page)

    def test_older_photos_are_aligned_when_the_step_opens(self):
        self.upload(couple_jpeg())
        MediaAsset.objects.update(focus_x=None, focus_y=None, faces=None)
        self.client.get(f"{self.base}/fotos/")
        asset = MediaAsset.objects.get()
        self.assertEqual(asset.faces, 2)
        self.assertIsNotNone(asset.focus_x)

    def test_drag_hint_and_no_js_sliders(self):
        self.upload(couple_jpeg())
        page = self.client.get(f"{self.base}/fotos/")
        self.assertContains(page, "Sleep een foto of zoom in")
        self.assertContains(page, "data-focus-xy")  # zonder JavaScript blijven de schuifbalken werken
        self.assertContains(page, "Automatisch uitlijnen")

"""Eigen foto's en MP3-muziek toevoegen werkt bij elk actief ontwerp: uploaden, kiezen als hoofdfoto, galerijfoto of muziek en terugzien op de kaart.
De homepage noemt dit als voordeel (core.content.HERO_CHECKS); deze test bewaakt dat de belofte voor alle ontwerpen klopt."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from catalog.models import Template

from .helpers import VaylideTestCase, jpeg_file


class EigenFotosTests(VaylideTestCase):
    def test_elk_actief_ontwerp_toont_hoofdfoto_en_galerijfoto(self):
        owner = self.make_customer()
        client = Client()
        client.force_login(owner)
        gecontroleerd = []
        for template in Template.objects.filter(is_active=True, current_version__isnull=False).order_by("slug"):
            occasion = template.occasions[0]
            inv = self.make_invitation(owner=owner, template=template.slug, occasion=occasion)
            base = f"/maken/{inv.uid}"
            uids = [client.post(f"{base}/upload/", {"fotos": jpeg_file(name=f"f{i}.jpg")}, HTTP_ACCEPT="application/json").json()["created"][0]["uid"]
                    for i in range(2)]
            mp3 = SimpleUploadedFile("lied.mp3", b"ID3\x03\x00\x00\x00" + b"\x00" * 200, content_type="audio/mpeg")
            muziek = client.post(f"{base}/upload/", {"muziek": mp3}, HTTP_ACCEPT="application/json").json()["created"][0]["uid"]
            inv.refresh_from_db()
            data = {"rev": inv.draft_rev, "hero": uids[0], f"g_{uids[1]}": "on", "music_source": "custom", "music_asset": muziek, "music_rights": "on"}
            for uid in uids:
                data.update({f"x_{uid}": "50", f"y_{uid}": "50", f"z_{uid}": "100"})
            response = client.post(f"{base}/voorbeeld/live/fotos/", data)
            self.assertTrue(response.json()["ok"], f"{template.slug}: {response.content[:400]}")
            html = client.get(response.json()["url"]).content.decode()
            self.assertIn('data-foto="hoofdfoto"', html, f"{template.slug}: hoofdfoto ontbreekt")
            self.assertIn('data-foto="galerij"', html, f"{template.slug}: galerijfoto ontbreekt")
            self.assertIn(muziek, html, f"{template.slug}: eigen muziek ontbreekt")
            gecontroleerd.append(template.slug)
        self.assertGreaterEqual(len(gecontroleerd), 30)

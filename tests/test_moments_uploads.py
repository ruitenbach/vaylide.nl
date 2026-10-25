"""Moments, stap 3A: gastsessie, uploadreservering, controle, verwerking en toegang. Alleen met lokale testopslag in een tijdelijke map."""
import base64
import io
import json
import re
import shutil
import tempfile
import uuid
from datetime import timedelta
from pathlib import Path
from unittest import mock

from django.core.cache import cache
from django.core.management import call_command
from django.test import Client, override_settings
from django.utils import timezone
from PIL import Image

from moments import limits, photos, services
from moments.models import Album, GuestToken, Submission
from moments.storage import S3Storage, StorageNotReady, get_storage
from tests.helpers import VaylideTestCase, jpeg_file


ORIGIN = "https://testserver"
LOS_OUD = "moments/00000000-0000-0000-0000-000000000000/orig/" + "a" * 32 + ".jpg"
LOS_NIEUW = "moments/00000000-0000-0000-0000-000000000000/orig/" + "b" * 32 + ".jpg"


def jpeg_bytes(color=(180, 140, 150), size=(1200, 900), gps=False) -> bytes:
    if gps:
        return jpeg_file(*size, exif_gps=True).getvalue()
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, "JPEG")
    return out.getvalue()


def png_bytes(size=(200, 200)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", size, (10, 90, 40)).save(out, "PNG")
    return out.getvalue()


class UploadTestCase(VaylideTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()
        self.dir = tempfile.mkdtemp(prefix="moments-test-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        overrides = override_settings(MOMENTS_ENABLED=True, TEST_MODE=True, MOMENTS_STORAGE="lokaal", MOMENTS_LOCAL_DIR=Path(self.dir))
        overrides.enable()
        self.addCleanup(overrides.disable)
        self.owner = self.make_customer("eigenaar-uploads@example.com")
        self.invitation = self.published(owner=self.owner)
        self.album = Album.objects.create(invitation=self.invitation, status=Album.Status.OPEN)
        self.storage = get_storage()

    # --- hulpmiddelen ---
    def guest(self, album=None):
        """Een gast met eigen browser (cookies) via het echte adres, inclusief CSRF-controle."""
        client = Client(enforce_csrf_checks=True)
        client.get("/moments/demo/", secure=True)
        album = album or self.album
        csrf = self._csrf(client)
        response = client.post(f"/moments/api/start/{album.public_code}/", secure=True, HTTP_X_CSRFTOKEN=csrf, HTTP_ORIGIN=ORIGIN)
        self.assertEqual(response.status_code, 200, response.content)
        return client

    def _csrf(self, client):
        from django.middleware.csrf import _get_new_csrf_string, _mask_cipher_secret

        if "vierlief_csrf" not in client.cookies:
            secret = _get_new_csrf_string()
            client.cookies["vierlief_csrf"] = secret
        value = client.cookies["vierlief_csrf"].value
        return _mask_cipher_secret(value) if len(value) == 32 else value

    def post(self, client, url, data=None):
        return client.post(url, data=json.dumps(data or {}), content_type="application/json", secure=True, HTTP_X_CSRFTOKEN=self._csrf(client), HTTP_ORIGIN=ORIGIN)

    def reserve(self, client, data: bytes, ctype="image/jpeg", client_id=None):
        return self.post(client, "/moments/api/uploads/", {"client_id": str(client_id or uuid.uuid4()), "type": ctype, "grootte": len(data)})

    def put(self, client, response, data: bytes, ctype="image/jpeg"):
        target = response.json()["upload"]
        return client.put(target["url"], data=data, content_type=ctype, secure=True)

    def upload_ok(self, client, data=None, **kw):
        data = data or jpeg_bytes(color=tuple(uuid.uuid4().bytes[:3]))
        res = self.reserve(client, data, **kw)
        self.assertIn(res.status_code, (200, 201), res.content)
        self.assertEqual(self.put(client, res, data).status_code, 204)
        done = self.post(client, f"/moments/api/uploads/{res.json()['id']}/klaar/")
        return res.json()["id"], done

    def sub(self, uid):
        return Submission.objects.get(uid=uid)

    def process_all(self):
        n = 0
        while services.process_next_photo(self.storage):
            n += 1
        return n


class SessieTests(UploadTestCase):
    def test_start_zet_beveiligde_cookie_en_maakt_een_gast(self):
        client = self.guest()
        cookie = client.cookies["moments_gast"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["path"], "/moments/")
        self.assertTrue(cookie["secure"])
        self.assertEqual(GuestToken.objects.filter(album=self.album).count(), 1)
        self.assertFalse(GuestToken.objects.filter(token_hash=cookie.value).exists())  # alleen de hash staat in de database

    def test_tweede_start_met_cookie_maakt_geen_nieuwe_identiteit(self):
        client = self.guest()
        for _ in range(3):
            res = self.post(client, f"/moments/api/start/{self.album.public_code}/")
            self.assertEqual(res.status_code, 200)
            self.assertFalse(res.json()["nieuw"])
        self.assertEqual(GuestToken.objects.count(), 1)

    def test_scannen_maakt_geen_gast(self):
        Client().get(f"/moments/api/start/{self.album.public_code}/", secure=True)  # GET: niet toegestaan
        self.assertEqual(GuestToken.objects.count(), 0)

    def test_csrf_is_verplicht(self):
        res = Client(enforce_csrf_checks=True).post(f"/moments/api/start/{self.album.public_code}/", secure=True)
        self.assertEqual(res.status_code, 403)
        self.assertEqual(GuestToken.objects.count(), 0)

    def test_onbekende_code_geeft_404(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.post(client, "/moments/api/start/bestaatniet/").status_code, 404)

    def test_publieke_code_is_onraadbaar_en_roteerbaar(self):
        self.assertGreaterEqual(len(self.album.public_code), 13)  # 80 bit
        other = Album.objects.create(invitation=self.published(owner=self.make_customer("x@example.com")))
        self.assertNotEqual(other.public_code, self.album.public_code)
        oud = self.album.public_code
        services.rotate_public_code(self.album)
        self.assertNotEqual(self.album.public_code, oud)
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(self.post(client, f"/moments/api/start/{oud}/").status_code, 404)

    def test_pauze_nieuwe_gasten_en_gesloten_album(self):
        self.album.accepting_new_guests = False
        self.album.save()
        res = self.post(Client(enforce_csrf_checks=True), f"/moments/api/start/{self.album.public_code}/")
        self.assertEqual((res.status_code, res.json()["fout"]), (409, "geen_nieuwe_gasten"))
        self.album.accepting_new_guests = True
        self.album.status = Album.Status.CLOSED
        self.album.save()
        res = self.post(Client(enforce_csrf_checks=True), f"/moments/api/start/{self.album.public_code}/")
        self.assertEqual((res.status_code, res.json()["fout"]), (409, "album_dicht"))

    def test_emmer_is_300_met_120_per_minuut(self):
        self.assertEqual((limits.SIGNUP_BUCKET_CAPACITY, limits.SIGNUP_BUCKET_REFILL_PER_MIN), (300, 120))

    def test_driehonderd_sessiestarts_gaan_door_en_de_301e_wacht(self):
        start = timezone.now()
        with mock.patch("moments.services.timezone.now", return_value=start):  # vaste klok: precies de emmer, zonder aanvulling tijdens de test
            for i in range(300):
                token, raw = services.start_guest_session(self.album.public_code)
                self.assertIsNotNone(raw, i)
            with self.assertRaises(services.SubmissionRefused) as ctx:
                services.start_guest_session(self.album.public_code)
        self.assertEqual(ctx.exception.code, "even_wachten")
        self.assertLessEqual(ctx.exception.retry_after, 3)  # 120 per minuut: hooguit enkele seconden wachten
        self.assertEqual(GuestToken.objects.count(), 300)
        # Na 30 seconden zijn er 60 plekken bij (120 per minuut), na een minuut 120 (niet meer dan de emmer groot is).
        Album.objects.filter(pk=self.album.pk).update(signup_refilled_at=start)
        for n, expected in ((30, 60), (60, 120)):
            Album.objects.filter(pk=self.album.pk).update(signup_tokens=0, signup_refilled_at=start)
            granted = 0
            later = start + timedelta(seconds=n)
            while True:
                try:
                    services.take_signup_slot(self.album.pk, now=later)
                    granted += 1
                except services.SubmissionRefused:
                    break
            self.assertEqual(granted, expected)

    def test_driehonderd_sessiestarts_via_http_en_de_301e_krijgt_429(self):
        statuses = []
        with mock.patch("moments.services.timezone.now", return_value=timezone.now()):
            for _ in range(301):
                client = Client(enforce_csrf_checks=True)
                statuses.append(self.post(client, f"/moments/api/start/{self.album.public_code}/").status_code)
        self.assertEqual(statuses.count(200), 300)
        self.assertEqual(statuses[-1], 429)

    def test_emmer_op_albumniveau_geeft_even_geduld_en_vult_aan(self):
        with mock.patch("moments.services.timezone.now", return_value=timezone.now()):
            for _ in range(limits.SIGNUP_BUCKET_CAPACITY):
                services.start_guest_session(self.album.public_code)
            with self.assertRaises(services.SubmissionRefused) as ctx:
                services.start_guest_session(self.album.public_code)
        self.assertEqual(ctx.exception.code, "even_wachten")
        self.assertGreaterEqual(ctx.exception.retry_after, 1)
        self.album.refresh_from_db()
        later = timezone.now() + timedelta(minutes=2)
        services.take_signup_slot(self.album.pk, now=later)  # na twee minuten zijn er weer plekken

    def test_emmer_via_http_geeft_429_met_retry_after(self):
        Album.objects.filter(pk=self.album.pk).update(signup_tokens=0, signup_refilled_at=timezone.now())
        res = self.post(Client(enforce_csrf_checks=True), f"/moments/api/start/{self.album.public_code}/")
        self.assertEqual(res.status_code, 429)
        self.assertTrue(res["Retry-After"].isdigit())

    def test_netwerk_blokkeert_geen_gasten(self):
        # Dertig gasten achter één adres (zaal-wifi) komen er allemaal in: het netwerk is alleen een signaal.
        for _ in range(30):
            client = Client(enforce_csrf_checks=True, REMOTE_ADDR="203.0.113.7")
            self.assertEqual(self.post(client, f"/moments/api/start/{self.album.public_code}/").status_code, 200)
        self.assertEqual(GuestToken.objects.count(), 30)

    def test_netwerkvingerafdruk_is_een_hash_en_wordt_gewist(self):
        client = Client(enforce_csrf_checks=True, REMOTE_ADDR="203.0.113.9")
        self.post(client, f"/moments/api/start/{self.album.public_code}/")
        for token in GuestToken.objects.all():
            self.assertNotIn("203.0.113.9", token.network_hash)
        GuestToken.objects.update(network_hash="x" * 24)
        GuestToken.objects.update(created_at=timezone.now() - timedelta(days=31))
        self.assertEqual(services.purge_network_hashes(), 1)
        self.assertFalse(GuestToken.objects.exclude(network_hash="").exists())

    def test_verlopen_ingetrokken_en_vreemd_token_werken_niet(self):
        client = self.guest()
        token = GuestToken.objects.get()
        token.expires_at = timezone.now() - timedelta(seconds=1)
        token.save()
        self.assertEqual(client.get("/moments/api/uploads/", secure=True).status_code, 401)
        token.expires_at = None
        token.revoked_at = timezone.now()
        token.save()
        self.assertEqual(client.get("/moments/api/uploads/", secure=True).status_code, 401)
        client.cookies["moments_gast"] = "verzonnen"
        self.assertEqual(client.get("/moments/api/uploads/", secure=True).status_code, 401)
        self.assertEqual(Client().get("/moments/api/uploads/", secure=True).status_code, 401)

    def test_verlopen_token_mag_niet_reserveren(self):
        client = self.guest()
        GuestToken.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.reserve(client, jpeg_bytes()).status_code, 401)
        self.assertEqual(Submission.objects.count(), 0)

    def test_alle_adressen_bestaan_niet_met_vlag_uit(self):
        client = self.guest()
        uid = uuid.uuid4()
        with override_settings(MOMENTS_ENABLED=False):
            for method, url in [
                ("post", f"/moments/api/start/{self.album.public_code}/"),
                ("get", "/moments/api/uploads/"),
                ("post", "/moments/api/uploads/"),
                ("get", f"/moments/api/uploads/{uid}/"),
                ("post", f"/moments/api/uploads/{uid}/klaar/"),
                ("get", f"/moments/api/uploads/{uid}/bestand/"),
                ("put", "/moments/api/test-opslag/abc/"),
            ]:
                res = getattr(client, method)(url, secure=True)
                self.assertEqual(res.status_code, 404, url)


class ReserveringTests(UploadTestCase):
    def test_reservering_geeft_uploaddoel_zonder_geheimen(self):
        client = self.guest()
        data = jpeg_bytes()
        res = self.reserve(client, data)
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertEqual(body["status"], "uploaden")
        self.assertEqual(body["upload"]["method"], "PUT")
        self.assertNotIn("original_key", json.dumps(body))
        self.assertNotIn(self.storage.root.as_posix(), json.dumps(body))
        sub = self.sub(body["id"])
        self.assertEqual(sub.reserved_bytes, limits.PHOTO_MAX_STORED_BYTES)
        self.assertRegex(sub.original_key, r"^moments/[0-9a-f-]{36}/orig/[0-9a-f]{32}\.jpg$")  # willekeurige naam, geen naam van de gast

    def test_dubbel_verzoek_met_zelfde_client_id_telt_niet_dubbel(self):
        client = self.guest()
        data = jpeg_bytes()
        cid = uuid.uuid4()
        a = self.reserve(client, data, client_id=cid)
        b = self.reserve(client, data, client_id=cid)
        self.assertEqual(a.json()["id"], b.json()["id"])
        self.assertEqual(Submission.objects.count(), 1)

    def test_plafond_per_gast(self):
        client = self.guest()
        Album.objects.filter(pk=self.album.pk).update(max_per_guest=2)
        for _ in range(2):
            self.assertEqual(self.upload_ok(client)[1].status_code, 200)
        res = self.reserve(client, jpeg_bytes())
        self.assertEqual((res.status_code, res.json()["fout"]), (409, "plafond_gast"))
        self.assertTrue(res.json()["bericht"])
        other = self.guest()  # een andere gast heeft een eigen plafond
        self.assertEqual(self.reserve(other, jpeg_bytes()).status_code, 201)

    def test_plafond_per_album(self):
        Album.objects.filter(pk=self.album.pk).update(max_per_album=2)
        a, b = self.guest(), self.guest()
        self.assertEqual(self.reserve(a, jpeg_bytes()).status_code, 201)
        self.assertEqual(self.reserve(b, jpeg_bytes()).status_code, 201)
        res = self.reserve(self.guest(), jpeg_bytes())
        self.assertEqual((res.status_code, res.json()["fout"]), (409, "plafond_album"))

    def test_bytesplafond_is_afgeleid_van_de_aantallen(self):
        self.assertEqual(self.album.bytes_cap, self.album.album_limit * limits.PHOTO_MAX_STORED_BYTES)
        self.assertEqual(limits.DEFAULT_MAX_PER_ALBUM * limits.PHOTO_MAX_STORED_BYTES, 1875 * 8 * 1024 * 1024)
        Album.objects.filter(pk=self.album.pk).update(max_per_album=3)
        with mock.patch.object(limits, "PHOTO_MAX_STORED_BYTES", 8):  # een gast kan nooit meer reserveren dan de aantallen zeggen
            self.assertEqual(Album.objects.get(pk=self.album.pk).bytes_cap, 24)

    def test_maximaal_drie_gelijktijdige_uploads(self):
        client = self.guest()
        for _ in range(3):
            self.assertEqual(self.reserve(client, jpeg_bytes()).status_code, 201)
        res = self.reserve(client, jpeg_bytes())
        self.assertEqual((res.status_code, res.json()["fout"]), (429, "tempo"))
        self.assertIn("Retry-After", res)

    def test_uploadstarts_per_tien_minuten(self):
        client = self.guest()
        with mock.patch.object(limits, "MAX_STARTS_PER_10_MIN", 2), mock.patch.object(limits, "MAX_CONCURRENT_UPLOADS", 99):
            self.assertEqual(self.reserve(client, jpeg_bytes()).status_code, 201)
            self.assertEqual(self.reserve(client, jpeg_bytes()).status_code, 201)
            self.assertEqual(self.reserve(client, jpeg_bytes()).status_code, 429)

    def test_overschrijding_van_de_technische_gastengrens_weigert_geen_upload(self):
        Album.objects.filter(pk=self.album.pk).update(max_guests=2)
        a, b, c = self.guest(), self.guest(), self.guest()
        self.assertEqual(self.upload_ok(a)[1].status_code, 200)
        self.assertEqual(self.upload_ok(b)[1].status_code, 200)
        self.assertIsNone(Album.objects.get(pk=self.album.pk).guest_warning_at)
        self.assertEqual(self.reserve(c, jpeg_bytes()).status_code, 201)  # een derde gast boven de grens van 2 mag gewoon uploaden
        self.assertEqual(self.upload_ok(c)[1].status_code, 200)
        self.assertIsNotNone(Album.objects.get(pk=self.album.pk).guest_warning_at)  # alleen intern vastgelegd
        self.assertEqual(self.reserve(a, jpeg_bytes()).status_code, 201)

    def test_waarschuwing_wordt_gelogd_en_maar_een_keer_gezet(self):
        Album.objects.filter(pk=self.album.pk).update(max_guests=1)
        a, b, c = self.guest(), self.guest(), self.guest()
        self.upload_ok(a)
        with self.assertLogs("vaylide.moments", level="WARNING") as logs:
            self.upload_ok(b)
        first = Album.objects.get(pk=self.album.pk).guest_warning_at
        self.assertIn("alleen een waarschuwing", logs.output[0])
        self.upload_ok(c)
        self.assertEqual(Album.objects.get(pk=self.album.pk).guest_warning_at, first)

    def _vul_actieve_gasten(self, n):
        GuestToken.objects.bulk_create([GuestToken(album=self.album, token_hash=f"h{i:060d}", first_upload_at=timezone.now()) for i in range(n)])

    def test_classic_200_actieve_sessies_waarschuwing_zonder_weigering(self):
        self.assertEqual(limits.DEFAULT_MAX_GUESTS, 200)
        self.assertEqual(self.album.guest_warning_threshold, 200)
        self._vul_actieve_gasten(200)
        self.assertIsNone(Album.objects.get(pk=self.album.pk).guest_warning_at)  # precies op de grens: nog niets
        res = self.reserve(self.guest(), jpeg_bytes())  # de 201e actieve gast
        self.assertEqual(res.status_code, 201, res.content)
        self.assertIsNotNone(Album.objects.get(pk=self.album.pk).guest_warning_at)
        self.assertEqual(self.upload_ok(self.guest())[1].status_code, 200)  # en de 202e

    def test_signature_400_actieve_sessies_waarschuwing_zonder_weigering(self):
        Album.objects.filter(pk=self.album.pk).update(max_guests=limits.SIGNATURE_MAX_GUESTS, max_per_album=6250, max_per_guest=25)
        self.album.refresh_from_db()
        self.assertEqual(self.album.guest_warning_threshold, 400)
        self._vul_actieve_gasten(399)
        self.assertEqual(self.reserve(self.guest(), jpeg_bytes()).status_code, 201)  # de 400e: nog onder of op de grens
        self.assertIsNone(Album.objects.get(pk=self.album.pk).guest_warning_at)
        self.assertEqual(self.reserve(self.guest(), jpeg_bytes()).status_code, 201)  # de 401e
        self.assertIsNotNone(Album.objects.get(pk=self.album.pk).guest_warning_at)
        self.assertEqual(self.upload_ok(self.guest())[1].status_code, 200)

    def test_foto_en_albumplafonds_blijven_gelden_ook_boven_de_gastengrens(self):
        Album.objects.filter(pk=self.album.pk).update(max_guests=1, max_per_album=2, max_per_guest=1)
        a, b, c = self.guest(), self.guest(), self.guest()
        self.assertEqual(self.upload_ok(a)[1].status_code, 200)
        self.assertEqual(self.reserve(a, jpeg_bytes()).json()["fout"], "plafond_gast")
        self.assertEqual(self.upload_ok(b)[1].status_code, 200)
        self.assertEqual(self.reserve(c, jpeg_bytes()).json()["fout"], "plafond_album")

    def test_sessies_zonder_upload_tellen_niet_mee_als_actieve_gast(self):
        Album.objects.filter(pk=self.album.pk).update(max_guests=1)
        for _ in range(5):
            self.guest()  # scanners en bots die alleen een sessie openen
        self.assertEqual(self.upload_ok(self.guest())[1].status_code, 200)
        self.assertIsNone(Album.objects.get(pk=self.album.pk).guest_warning_at)

    def test_type_en_grootte_worden_vooraf_geweigerd(self):
        client = self.guest()
        for ctype, size, code in [
            ("application/pdf", 5000, "type"), ("image/heic", 5000, "type"), ("image/svg+xml", 5000, "type"), ("", 5000, "type"),
            ("image/jpeg", 10, "te_klein"), ("image/jpeg", limits.PHOTO_MAX_INPUT_BYTES + 1, "te_groot"), ("image/jpeg", "groot", "te_klein"),
        ]:
            res = self.post(client, "/moments/api/uploads/", {"client_id": str(uuid.uuid4()), "type": ctype, "grootte": size})
            self.assertEqual(res.json()["fout"], code, (ctype, size))
        res = self.post(client, "/moments/api/uploads/", {"client_id": "geen-uuid", "type": "image/jpeg", "grootte": 5000})
        self.assertEqual(res.json()["fout"], "ongeldig")
        res = client.post("/moments/api/uploads/", data="geen json", content_type="application/json", secure=True, HTTP_X_CSRFTOKEN=self._csrf(client), HTTP_ORIGIN=ORIGIN)
        self.assertEqual(res.json()["fout"], "ongeldig")
        res = client.post("/moments/api/uploads/", data="x" * 5000, content_type="application/json", secure=True, HTTP_X_CSRFTOKEN=self._csrf(client), HTTP_ORIGIN=ORIGIN)
        self.assertEqual(res.json()["fout"], "ongeldig")
        self.assertEqual(Submission.objects.count(), 0)

    def test_verlopen_reservering_komt_vrij_zonder_opruimtaak(self):
        client = self.guest()
        Album.objects.filter(pk=self.album.pk).update(max_per_guest=1)
        res = self.reserve(client, jpeg_bytes())
        self.assertEqual(self.reserve(client, jpeg_bytes()).status_code, 409)
        Submission.objects.update(reservation_expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.reserve(client, jpeg_bytes()).status_code, 201)  # telt niet meer mee, ook zonder opruimen
        self.assertEqual(res.status_code, 201)

    def test_gesloten_album_weigert_reserveringen(self):
        client = self.guest()
        Album.objects.filter(pk=self.album.pk).update(status=Album.Status.CLOSED)
        res = self.reserve(client, jpeg_bytes())
        self.assertEqual((res.status_code, res.json()["fout"]), (409, "album_dicht"))

    def test_zonder_opslag_wordt_netjes_geweigerd_en_niets_lokaal_bewaard(self):
        client = self.guest()
        with override_settings(TEST_MODE=False):  # live: lokale opslag bestaat niet
            res = self.reserve(client, jpeg_bytes())
        self.assertEqual((res.status_code, res.json()["fout"]), (503, "opslag_niet_klaar"))
        self.assertEqual(Submission.objects.count(), 0)
        with override_settings(MOMENTS_STORAGE="s3", MOMENTS_S3_BUCKET=""):
            self.assertEqual(self.reserve(client, jpeg_bytes()).status_code, 503)


class UploadStroomTests(UploadTestCase):
    def test_hele_stroom_van_reservering_tot_albummaster(self):
        client = self.guest()
        original = jpeg_bytes(gps=True, size=(3000, 2000))
        res = self.reserve(client, original)
        self.assertEqual(self.put(client, res, original).status_code, 204)
        uid = res.json()["id"]
        done = self.post(client, f"/moments/api/uploads/{uid}/klaar/")
        self.assertEqual(done.json()["status"], "ontvangen")
        self.assertEqual(self.process_all(), 1)
        sub = self.sub(uid)
        self.assertEqual(sub.status, "klaar")
        self.assertEqual(sub.original_key, "")
        self.assertEqual(self.storage.size(sub.storage_key) or 0, sub.size_bytes)
        master = Image.open(io.BytesIO(self.storage.read(sub.storage_key)))
        self.assertEqual(master.format, "JPEG")
        self.assertFalse(master.getexif(), "metadata (zoals locatie) moet weg zijn")
        self.assertNotIn(b"TestCamera", self.storage.read(sub.storage_key))
        self.assertEqual(client.get(f"/moments/api/uploads/{uid}/", secure=True).json()["status"], "klaar")
        file = client.get(f"/moments/api/uploads/{uid}/bestand/", secure=True)
        self.assertEqual((file.status_code, file["Content-Type"]), (200, "image/jpeg"))
        self.assertIn("no-store", file["Cache-Control"])
        self.assertEqual(b"".join(file.streaming_content), self.storage.read(sub.storage_key))

    def test_master_is_hoogstens_6000_px(self):
        big = io.BytesIO()
        Image.new("RGB", (6500, 800), (200, 100, 50)).save(big, "JPEG", quality=60)
        master = Image.open(io.BytesIO(photos.make_master(big.getvalue())))
        self.assertEqual(max(master.size), limits.ALBUM_MASTER_MAX_EDGE_PX)

    def test_dubbel_klaar_melden_verwerkt_niet_dubbel(self):
        client = self.guest()
        uid, first = self.upload_ok(client)
        again = self.post(client, f"/moments/api/uploads/{uid}/klaar/")
        self.assertEqual((first.json()["status"], again.json()["status"]), ("ontvangen", "ontvangen"))
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(self.process_all(), 1)
        self.assertEqual(self.process_all(), 0)
        late = self.post(client, f"/moments/api/uploads/{uid}/klaar/")
        self.assertEqual(late.json()["status"], "klaar")
        self.assertEqual(self.sub(uid).attempts, 1)
        self.assertEqual(len([k for k, _ in self.storage.keys("moments/")]), 1)  # alleen de master; het origineel is weg

    def test_dezelfde_foto_twee_keer_wordt_geweigerd(self):
        client = self.guest()
        data = jpeg_bytes(color=(1, 2, 3))
        self.assertEqual(self.upload_ok(client, data)[1].json()["status"], "ontvangen")
        uid, second = self.upload_ok(client, data)
        self.assertEqual((second.json()["status"], second.json()["fout"]), ("mislukt", "dubbel"))
        self.assertEqual(len([k for k, _ in self.storage.keys("moments/")]), 1)  # het dubbele origineel is meteen verwijderd

    def test_dezelfde_foto_van_twee_gasten_mag_wel(self):
        data = jpeg_bytes(color=(9, 9, 9))
        self.assertEqual(self.upload_ok(self.guest(), data)[1].json()["status"], "ontvangen")
        self.assertEqual(self.upload_ok(self.guest(), data)[1].json()["status"], "ontvangen")

    def test_verkeerd_type_wordt_gecontroleerd_op_de_inhoud(self):
        client = self.guest()
        fake = png_bytes() + b"\x00" * 2000
        uid, done = self.upload_ok(client, fake, ctype="image/jpeg")
        self.assertEqual((done.json()["status"], done.json()["fout"]), ("mislukt", "type"))
        uid2, done2 = self.upload_ok(client, b"%PDF-1.4 " + b"a" * 3000, ctype="image/jpeg")
        self.assertEqual(done2.json()["fout"], "type")
        self.assertEqual([k for k, _ in self.storage.keys("moments/")], [])  # niets blijft staan

    def test_beschadigde_en_afgekapte_foto_wordt_geweigerd(self):
        client = self.guest()
        data = jpeg_bytes(size=(1500, 1500))
        uid, done = self.upload_ok(client, data[:1500])  # de kop klopt; de rest ontbreekt
        self.assertEqual(done.json()["status"], "ontvangen")
        self.process_all()  # de verwerking leest de hele foto en ziet dat die afgekapt is
        self.assertEqual((self.sub(uid).status, self.sub(uid).failure_code), ("mislukt", "onleesbaar"))
        self.assertEqual([k for k, _ in self.storage.keys("moments/")], [])

    def test_te_veel_pixels_wordt_geweigerd(self):
        client = self.guest()
        with mock.patch.object(limits, "PHOTO_MAX_PIXELS", 10_000):
            _, done = self.upload_ok(client, jpeg_bytes(size=(1200, 900)))
        self.assertEqual(done.json()["fout"], "te_groot")

    def test_script_in_bestand_wordt_nooit_uitgevoerd_of_bewaard(self):
        client = self.guest()
        evil = b"\xff\xd8\xff\xe0" + b"<script>alert(1)</script>" * 100
        _, done = self.upload_ok(client, evil)
        self.assertEqual(done.json()["status"], "mislukt")

    def test_klaar_melden_zonder_upload_wacht_en_telt_niet_dubbel(self):
        client = self.guest()
        res = self.reserve(client, jpeg_bytes())
        uid = res.json()["id"]
        done = self.post(client, f"/moments/api/uploads/{uid}/klaar/")
        self.assertEqual((done.status_code, done.json()["fout"]), (409, "nog_niet_ontvangen"))
        self.assertEqual(self.sub(uid).status, "uploaden")

    def test_verlopen_upload_faalt_en_ruimt_op(self):
        client = self.guest()
        data = jpeg_bytes()
        res = self.reserve(client, data)
        self.assertEqual(self.put(client, res, data).status_code, 204)
        Submission.objects.update(reservation_expires_at=timezone.now() - timedelta(seconds=1))
        done = self.post(client, f"/moments/api/uploads/{res.json()['id']}/klaar/")
        self.assertEqual((done.json()["status"], done.json()["fout"]), ("mislukt", "verlopen"))
        self.assertEqual([k for k, _ in self.storage.keys("moments/")], [])

    def test_upload_naar_verlopen_of_vreemd_adres_wordt_geweigerd(self):
        client = self.guest()
        data = jpeg_bytes()
        res = self.reserve(client, data)
        target = res.json()["upload"]["url"]
        self.assertEqual(client.put(target[:-3] + "xyz/", data=data, content_type="image/jpeg", secure=True).status_code, 404)  # geknoeid
        self.assertEqual(client.put(target, data=data, content_type="image/png", secure=True).status_code, 415)  # ander type dan gereserveerd
        Submission.objects.update(reservation_expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(client.put(target, data=data, content_type="image/jpeg", secure=True).status_code, 404)
        self.assertEqual([k for k, _ in self.storage.keys("moments/")], [])

    def test_te_grote_upload_wordt_afgekapt(self):
        client = self.guest()
        data = jpeg_bytes()
        res = self.reserve(client, data)
        with mock.patch.object(limits, "PHOTO_MAX_INPUT_BYTES", 500):
            target = self.storage.upload_target(self.sub(res.json()["id"]).original_key, "image/jpeg", 500)
            self.assertEqual(client.put(target["url"], data=data, content_type="image/jpeg", secure=True).status_code, 413)
        self.assertEqual([k for k, _ in self.storage.keys("moments/")], [])

    def test_testopslag_bestaat_niet_buiten_testmodus(self):
        client = self.guest()
        data = jpeg_bytes()
        res = self.reserve(client, data)
        with override_settings(TEST_MODE=False):
            self.assertEqual(client.put(res.json()["upload"]["url"], data=data, content_type="image/jpeg", secure=True).status_code, 404)

    def test_falende_upload_telt_niet_mee_en_opnieuw_proberen_kan(self):
        client = self.guest()
        Album.objects.filter(pk=self.album.pk).update(max_per_guest=1)
        _, bad = self.upload_ok(client, b"\xff\xd8\xff" + b"x" * 3000)
        self.assertEqual(bad.json()["status"], "mislukt")
        _, good = self.upload_ok(client)
        self.assertEqual(good.json()["status"], "ontvangen")
        self.assertEqual(self.reserve(client, jpeg_bytes()).json()["fout"], "plafond_gast")

    def test_opslag_valt_uit_tijdens_verwerking_probeert_opnieuw_en_faalt_daarna(self):
        client = self.guest()
        uid, _ = self.upload_ok(client)
        with mock.patch.object(photos, "make_master", side_effect=OSError("opslag weg")):
            for expected in ("ontvangen", "ontvangen", "mislukt"):
                services.process_next_photo(self.storage)
                self.assertEqual(self.sub(uid).status, expected)
        self.assertEqual(self.sub(uid).failure_code, "verwerking")
        self.assertEqual(self.sub(uid).reserved_bytes, 0)

    def test_vastgelopen_verwerking_gaat_terug_in_de_wachtrij(self):
        client = self.guest()
        uid, _ = self.upload_ok(client)
        Submission.objects.filter(uid=uid).update(status="verwerken", processing_started_at=timezone.now() - timedelta(minutes=30), attempts=1)
        self.assertEqual(services.reset_stale_processing(), 1)
        self.assertEqual(self.process_all(), 1)
        self.assertEqual(self.sub(uid).status, "klaar")


class ToegangTests(UploadTestCase):
    def test_gast_ziet_alleen_eigen_uploads(self):
        a, b = self.guest(), self.guest()
        uid_a, _ = self.upload_ok(a)
        uid_b, _ = self.upload_ok(b)
        self.process_all()
        self.assertEqual([i["id"] for i in a.get("/moments/api/uploads/", secure=True).json()["inzendingen"]], [uid_a])
        self.assertEqual([i["id"] for i in b.get("/moments/api/uploads/", secure=True).json()["inzendingen"]], [uid_b])

    def test_andermans_upload_geeft_404_op_elk_adres(self):
        a, b = self.guest(), self.guest()
        uid, _ = self.upload_ok(a)
        self.process_all()
        for method, url in [("get", f"/moments/api/uploads/{uid}/"), ("get", f"/moments/api/uploads/{uid}/bestand/")]:
            self.assertEqual(getattr(b, method)(url, secure=True).status_code, 404, url)
        self.assertEqual(self.post(b, f"/moments/api/uploads/{uid}/klaar/").status_code, 404)
        self.assertEqual(self.sub(uid).status, "klaar")  # niet aangeraakt
        self.assertEqual(b.get(f"/moments/api/uploads/{uuid.uuid4()}/", secure=True).status_code, 404)  # bestaat niet: zelfde antwoord

    def test_token_van_ander_album_ziet_niets_en_kan_niet_reserveren_hier(self):
        other = Album.objects.create(invitation=self.published(owner=self.make_customer("ander-album@example.com")), status=Album.Status.OPEN)
        a = self.guest()
        uid, _ = self.upload_ok(a)
        b = self.guest(other)
        self.assertEqual(b.get(f"/moments/api/uploads/{uid}/", secure=True).status_code, 404)
        self.assertEqual(b.get("/moments/api/uploads/", secure=True).json()["inzendingen"], [])
        sub = Submission.objects.get(uid=uid)
        self.assertEqual(sub.album_id, self.album.pk)

    def test_ingetrokken_sessie_verliest_toegang_tot_eigen_bestanden(self):
        a = self.guest()
        uid, _ = self.upload_ok(a)
        self.process_all()
        services.revoke_token(GuestToken.objects.get())
        self.assertEqual(a.get(f"/moments/api/uploads/{uid}/bestand/", secure=True).status_code, 401)

    def test_bestand_is_pas_beschikbaar_als_het_klaar_is(self):
        a = self.guest()
        uid, _ = self.upload_ok(a)
        self.assertEqual(a.get(f"/moments/api/uploads/{uid}/bestand/", secure=True).status_code, 404)

    def test_antwoorden_zijn_niet_te_cachen_en_niet_te_indexeren(self):
        a = self.guest()
        res = a.get("/moments/api/uploads/", secure=True)
        self.assertIn("no-store", res["Cache-Control"])
        self.assertIn("noindex", res["X-Robots-Tag"])
        self.assertEqual(res["Referrer-Policy"], "no-referrer")

    def test_zonder_cookie_geen_toegang(self):
        a = self.guest()
        uid, _ = self.upload_ok(a)
        anon = Client(enforce_csrf_checks=True)
        self.assertEqual(anon.get(f"/moments/api/uploads/{uid}/", secure=True).status_code, 401)
        self.assertEqual(self.post(anon, "/moments/api/uploads/", {}).status_code, 401)


class OnderhoudTests(UploadTestCase):
    def test_verlopen_reserveringen_en_losse_objecten_worden_opgeruimd(self):
        client = self.guest()
        data = jpeg_bytes()
        res = self.reserve(client, data)
        self.put(client, res, data)
        Submission.objects.update(reservation_expires_at=timezone.now() - timedelta(minutes=1))
        self.assertEqual(services.expire_reservations(self.storage), 1)
        self.assertEqual(self.sub(res.json()["id"]).status, "mislukt")
        self.storage.write(LOS_OUD, b"x" * 10)
        self.storage.write(LOS_NIEUW, b"x" * 10)
        import os
        old = timezone.now().timestamp() - 48 * 3600
        os.utime(Path(self.dir) / LOS_OUD, (old, old))
        self.storage.write("moments/vreemd/bestand.txt", b"x")  # geen sleutel van ons: blijft altijd staan
        os.utime(Path(self.dir) / "moments/vreemd/bestand.txt", (old, old))
        self.assertEqual(services.cleanup_orphans(self.storage), 1)
        self.assertIsNone(self.storage.size(LOS_OUD))
        self.assertEqual(self.storage.size("moments/vreemd/bestand.txt"), 1)
        self.assertEqual(self.storage.size(LOS_NIEUW), 10)  # jong: mogelijk een lopende upload

    def test_opruimen_laat_bestanden_met_een_databaseregel_staan(self):
        client = self.guest()
        uid, _ = self.upload_ok(client)
        self.process_all()
        import os
        old = timezone.now().timestamp() - 72 * 3600
        for key, _ in list(self.storage.keys("moments/")):
            os.utime(Path(self.dir) / key, (old, old))
        self.assertEqual(services.cleanup_orphans(self.storage), 0)
        self.assertTrue(self.storage.size(self.sub(uid).storage_key))

    def test_onderhoudscommando(self):
        client = self.guest()
        uid, _ = self.upload_ok(client)
        out = io.StringIO()
        call_command("moments_onderhoud", stdout=out)
        self.assertEqual(self.sub(uid).status, "klaar")
        with override_settings(MOMENTS_ENABLED=False):
            out = io.StringIO()
            call_command("moments_onderhoud", stdout=out)
            self.assertIn("uit", out.getvalue())


class S3Tests(UploadTestCase):
    def storage_s3(self):
        return S3Storage("moments-test-bucket", "https://s3.example.test", "nl-ams", "AKIATEST", "geheim-test")

    def test_ondertekende_post_dwingt_grootte_en_type_af(self):
        target = self.storage_s3().upload_target("moments/x/orig/a.jpg", "image/jpeg", 1000)
        self.assertEqual(target["method"], "POST")
        self.assertTrue(target["url"].startswith("https://s3.example.test"))
        policy = json.loads(base64.b64decode(target["fields"]["policy"]))
        self.assertIn(["content-length-range", 1, 1000], policy["conditions"])
        self.assertIn({"Content-Type": "image/jpeg"}, policy["conditions"])
        self.assertNotIn("geheim-test", json.dumps(target))

    def test_download_link_is_kort_en_ondertekend(self):
        url = self.storage_s3().download_url("moments/x/master/a.jpg")
        self.assertIn("X-Amz-Expires=300", url)
        self.assertIn("X-Amz-Signature=", url)

    def test_s3_zonder_instellingen_of_met_backupbucket_wordt_geweigerd(self):
        with override_settings(MOMENTS_STORAGE="s3", MOMENTS_S3_BUCKET="", MOMENTS_S3_ACCESS_KEY="", MOMENTS_S3_SECRET_KEY=""):
            with self.assertRaises(StorageNotReady):
                get_storage()
        with override_settings(MOMENTS_STORAGE="s3", MOMENTS_S3_BUCKET="back-ups", MOMENTS_S3_ACCESS_KEY="a", MOMENTS_S3_SECRET_KEY="b", BACKUP_S3_BUCKET="back-ups"):
            with self.assertRaises(StorageNotReady):
                get_storage()
        with override_settings(MOMENTS_STORAGE="onzin"):
            with self.assertRaises(StorageNotReady):
                get_storage()

    def test_s3_download_wordt_een_redirect_naar_korte_link(self):
        a = self.guest()
        uid, _ = self.upload_ok(a)
        self.process_all()
        with mock.patch("moments.api.get_storage", return_value=self.storage_s3()):
            res = a.get(f"/moments/api/uploads/{uid}/bestand/", secure=True)
        self.assertEqual(res.status_code, 302)
        self.assertIn("X-Amz-Expires=300", res["Location"])


class ScheidingTests(VaylideTestCase):
    def test_fotoverwerking_raakt_betaalverwerking_niet_aan(self):
        root = Path(__file__).resolve().parent.parent / "moments"
        verboden = re.compile(r"^\s*(from|import)\s+(processing|orders|kortingen|wishes|portal|payments|\w*mollie\w*)\b", re.I | re.M)
        for path in root.rglob("*.py"):
            if "migrations" in path.parts:
                continue
            self.assertIsNone(verboden.search(path.read_text()), path.name)

    def test_geen_bestaande_tabel_verwijst_naar_uploads(self):
        for sub in Submission._meta.get_fields():
            related = getattr(sub, "related_model", None)
            if related is not None and not isinstance(related, str):
                self.assertIn(related._meta.app_label, {"moments", "invitations"})


class FallbackTests(VaylideTestCase):
    def test_zeer_korrelige_foto_wordt_kleiner_in_plaats_van_geweigerd(self):
        import os

        noisy = Image.frombytes("RGB", (1000, 1000), os.urandom(3_000_000))
        out = io.BytesIO()
        noisy.save(out, "JPEG", quality=95)
        with mock.patch.object(limits, "PHOTO_MAX_STORED_BYTES", 300_000):
            master = photos.make_master(out.getvalue())
        self.assertLessEqual(len(master), 300_000)
        self.assertLess(Image.open(io.BytesIO(master)).width, 1000)


import threading  # noqa: E402

from django.db import connection, connections  # noqa: E402
from django.test import TransactionTestCase  # noqa: E402


class PostgresBasis(TransactionTestCase):
    """Echte gelijktijdigheid kan alleen op PostgreSQL (SQLite vergrendelt rijen niet). Elders wordt deze klasse overgeslagen.
    Draaien: DATABASE_URL=postgres://... python manage.py test tests.test_moments_uploads.GelijktijdigheidTests"""

    def setUp(self):
        if connection.vendor != "postgresql":
            self.skipTest("alleen op PostgreSQL")
        cache.clear()
        self.dir = tempfile.mkdtemp(prefix="moments-test-")
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        o = override_settings(MOMENTS_ENABLED=True, TEST_MODE=True, MOMENTS_STORAGE="lokaal", MOMENTS_LOCAL_DIR=Path(self.dir))
        o.enable()
        self.addCleanup(o.disable)
        from tests.helpers import VaylideTestCase as Base

        base = Base("run")
        base.setUp = lambda: None
        owner = Base.make_customer(base, "gelijktijdig@example.com")
        invitation = Base.published(base, owner=owner)
        self.album = Album.objects.create(invitation=invitation, status=Album.Status.OPEN, max_per_album=3, max_per_guest=2)
        self.storage = get_storage()

    def race(self, jobs):
        results, barrier = [], threading.Barrier(len(jobs))

        def run(job):
            try:
                barrier.wait()
                results.append(job())
            except services.SubmissionRefused as exc:
                results.append(exc.code)
            except Exception as exc:  # noqa: BLE001
                results.append(repr(exc))
            finally:
                connections.close_all()

        threads = [threading.Thread(target=run, args=(j,)) for j in jobs]
        [t.start() for t in threads]
        [t.join() for t in threads]
        return results

    def reserve(self, token, cid=None):
        return lambda: services.reserve_photo_upload(token, client_id=cid or uuid.uuid4(), content_type="image/jpeg", size_bytes=5000, storage=self.storage)[0].uid


class GelijktijdigheidTests(PostgresBasis):
    def test_albumplafond_houdt_bij_tegelijk_reserveren(self):
        tokens = [services.issue_token(self.album)[0] for _ in range(10)]
        results = self.race([self.reserve(t) for t in tokens])
        ok = [r for r in results if isinstance(r, uuid.UUID)]
        self.assertEqual(len(ok), 3, results)
        self.assertEqual(Submission.objects.count(), 3)
        self.assertTrue(all(r == "plafond_album" for r in results if not isinstance(r, uuid.UUID)), results)

    def test_gastplafond_houdt_bij_tegelijk_reserveren(self):
        Album.objects.filter(pk=self.album.pk).update(max_per_album=100)
        token = services.issue_token(self.album)[0]
        results = self.race([self.reserve(token) for _ in range(8)])
        self.assertEqual(len([r for r in results if isinstance(r, uuid.UUID)]), 2, results)
        self.assertEqual(Submission.objects.filter(guest_token=token).count(), 2)

    def test_hetzelfde_client_id_tegelijk_geeft_een_inzending(self):
        Album.objects.filter(pk=self.album.pk).update(max_per_album=100, max_per_guest=50)
        token = services.issue_token(self.album)[0]
        cid = uuid.uuid4()
        results = self.race([self.reserve(token, cid) for _ in range(8)])
        self.assertEqual(Submission.objects.filter(guest_token=token, client_id=cid).count(), 1)
        self.assertEqual(len({r for r in results if isinstance(r, uuid.UUID)}), 1, results)

    def test_dubbel_klaar_melden_tegelijk_verwerkt_een_keer(self):
        Album.objects.filter(pk=self.album.pk).update(max_per_album=100, max_per_guest=50)
        token = services.issue_token(self.album)[0]
        data = jpeg_bytes()
        sub, target = services.reserve_photo_upload(token, client_id=uuid.uuid4(), content_type="image/jpeg", size_bytes=len(data), storage=self.storage)
        self.storage.write(sub.original_key, data)
        reads = []
        real_read = self.storage.read
        self.storage.read = lambda *a, **k: (reads.append(1), real_read(*a, **k))[1]
        results = self.race([lambda: services.complete_photo_upload(token, sub.uid, self.storage).status for _ in range(6)])
        self.assertEqual(len(reads), 1, "het object wordt maar één keer gecontroleerd")
        self.assertTrue(set(results) <= {"ontvangen", "uploaden"}, results)  # een gelijktijdige melding ziet de lopende controle
        self.assertEqual(Submission.objects.get(pk=sub.pk).status, "ontvangen")
        done = self.race([lambda: getattr(services.process_next_photo(self.storage), "status", None) for _ in range(4)])
        self.assertEqual(Submission.objects.get(pk=sub.pk).status, "klaar")
        self.assertEqual(Submission.objects.get(pk=sub.pk).attempts, 1)
        self.assertEqual(len([k for k, _ in self.storage.keys("moments/")]), 1, done)


class SpyStorage:
    """Omhult de lokale opslag: noteert of een aanroep binnen een databasetransactie valt, en kan storingen en vertragingen nabootsen."""

    def __init__(self, inner, base_depth):
        self.inner, self.base, self.calls, self.fail, self.hooks = inner, base_depth, [], {}, {}
        self.name = inner.name

    def _spy(self, name, *args, **kwargs):
        self.calls.append((name, len(connection.savepoint_ids) - self.base))
        hook = self.hooks.get(name)
        if hook:
            hook()
        exc = self.fail.get(name)
        if exc:
            raise exc
        return getattr(self.inner, name)(*args, **kwargs)

    def __getattr__(self, name):
        if name in {"upload_target", "write", "size", "read", "delete", "keys", "download_url", "open"}:
            return lambda *a, **k: self._spy(name, *a, **k)
        raise AttributeError(name)

    def in_transaction(self):
        return [c for c in self.calls if c[1] > 0]


class OpslagBuitenTransactieTests(UploadTestCase):
    def setUp(self):
        super().setUp()
        self.spy = SpyStorage(self.storage, len(connection.savepoint_ids))
        self.token = services.issue_token(self.album)[0]

    def reserve_one(self, data=None, **kw):
        data = data or jpeg_bytes(color=tuple(uuid.uuid4().bytes[:3]))
        sub, target = services.reserve_photo_upload(self.token, client_id=uuid.uuid4(), content_type="image/jpeg", size_bytes=len(data), storage=self.spy, **kw)
        return sub, data

    def upload(self, sub, data):
        self.storage.write(sub.original_key, data)

    def test_geen_enkele_opslagaanroep_binnen_een_transactie(self):
        sub, data = self.reserve_one()
        self.upload(sub, data)
        services.complete_photo_upload(self.token, sub.uid, self.spy)
        services.process_next_photo(self.spy)
        sub2, data2 = self.reserve_one()
        self.upload(sub2, data2)
        Submission.objects.filter(pk=sub2.pk).update(reservation_expires_at=timezone.now() - timedelta(seconds=1))
        services.expire_reservations(self.spy)
        bad, baddata = self.reserve_one(), b"\xff\xd8\xff" + b"x" * 3000
        self.upload(bad[0], baddata)
        services.complete_photo_upload(self.token, bad[0].uid, self.spy)  # mislukt: verwijderen van het origineel
        services.cleanup_orphans(self.spy)
        names = {c[0] for c in self.spy.calls}
        self.assertTrue({"upload_target", "size", "read", "write", "delete", "keys"} <= names, names)
        self.assertEqual(self.spy.in_transaction(), [])

    def test_time_out_bij_het_opvragen_behoudt_de_reservering(self):
        sub, data = self.reserve_one()
        self.upload(sub, data)
        self.spy.fail["size"] = TimeoutError("opslag traag")
        with self.assertRaises(services.SubmissionRefused) as ctx:
            services.complete_photo_upload(self.token, sub.uid, self.spy)
        self.assertEqual(ctx.exception.code, "opslag_niet_klaar")
        sub.refresh_from_db()
        self.assertEqual((sub.status, sub.processing_started_at), ("uploaden", None))
        self.assertEqual(sub.reserved_bytes, limits.PHOTO_MAX_STORED_BYTES)
        self.spy.fail.clear()
        self.assertEqual(services.complete_photo_upload(self.token, sub.uid, self.spy).status, "ontvangen")  # opnieuw melden lukt

    def test_time_out_tijdens_het_lezen_behoudt_de_reservering(self):
        sub, data = self.reserve_one()
        self.upload(sub, data)
        self.spy.fail["read"] = TimeoutError("lezen afgebroken")
        with self.assertRaises(services.SubmissionRefused):
            services.complete_photo_upload(self.token, sub.uid, self.spy)
        sub.refresh_from_db()
        self.assertEqual((sub.status, sub.processing_started_at, sub.failure_code), ("uploaden", None, ""))
        self.assertIsNotNone(self.storage.size(sub.original_key))  # het origineel is niet weggegooid door een storing

    def test_opslagfout_via_http_geeft_503_en_geen_foute_status(self):
        client = self.guest()
        data = jpeg_bytes()
        res = self.reserve(client, data)
        self.put(client, res, data)
        boom = mock.Mock(wraps=self.storage)
        boom.size.side_effect = ConnectionError("netwerk weg")
        with mock.patch("moments.api.get_storage", return_value=boom):
            done = self.post(client, f"/moments/api/uploads/{res.json()['id']}/klaar/")
        self.assertEqual((done.status_code, done.json()["fout"]), (503, "opslag_niet_klaar"))
        self.assertEqual(self.sub(res.json()["id"]).status, "uploaden")
        self.assertEqual(self.post(client, f"/moments/api/uploads/{res.json()['id']}/klaar/").json()["status"], "ontvangen")

    def test_tweede_melding_tijdens_lopende_controle_leest_niet_opnieuw(self):
        sub, data = self.reserve_one()
        self.upload(sub, data)
        Submission.objects.filter(pk=sub.pk).update(processing_started_at=timezone.now())
        again = services.complete_photo_upload(self.token, sub.uid, self.spy)
        self.assertEqual(again.status, "uploaden")
        self.assertEqual([c for c in self.spy.calls if c[0] in {"size", "read"}], [])

    def test_vervallen_claim_wordt_overgenomen(self):
        sub, data = self.reserve_one()
        self.upload(sub, data)
        Submission.objects.filter(pk=sub.pk).update(processing_started_at=timezone.now() - timedelta(seconds=limits.VALIDATE_CLAIM_SECONDS + 5))
        self.assertEqual(services.complete_photo_upload(self.token, sub.uid, self.spy).status, "ontvangen")

    def test_opruimtaak_laat_een_lopende_controle_met_rust(self):
        sub, data = self.reserve_one()
        self.upload(sub, data)
        Submission.objects.filter(pk=sub.pk).update(reservation_expires_at=timezone.now() + timedelta(seconds=1))
        self.spy.hooks["read"] = lambda: (
            Submission.objects.filter(pk=sub.pk).update(reservation_expires_at=timezone.now() - timedelta(seconds=5)),
            self.assertEqual(services.expire_reservations(self.spy), 0),
        )
        self.assertEqual(services.complete_photo_upload(self.token, sub.uid, self.spy).status, "ontvangen")

    def test_overgenomen_uitslag_wordt_niet_overschreven(self):
        sub, data = self.reserve_one()
        self.upload(sub, data)
        self.spy.hooks["read"] = lambda: Submission.objects.filter(pk=sub.pk).update(status="verwijderd", processing_started_at=None)
        res = services.complete_photo_upload(self.token, sub.uid, self.spy)
        self.assertEqual(res.status, "verwijderd")
        self.assertEqual(Submission.objects.get(pk=sub.pk).status, "verwijderd")

    def test_herhaald_verzoek_met_zelfde_client_id_verbruikt_geen_tempo(self):
        data = jpeg_bytes()
        cid = uuid.uuid4()
        with mock.patch.object(limits, "MAX_STARTS_PER_10_MIN", 2):
            for _ in range(10):
                services.reserve_photo_upload(self.token, client_id=cid, content_type="image/jpeg", size_bytes=len(data), storage=self.spy)
        self.assertEqual(Submission.objects.filter(guest_token=self.token).count(), 1)

    def test_schrijven_van_de_master_faalt_origineel_blijft_en_daarna_mislukt(self):
        sub, data = self.reserve_one()
        self.upload(sub, data)
        services.complete_photo_upload(self.token, sub.uid, self.spy)
        self.spy.fail["write"] = OSError("schijf vol")
        for expected in ("ontvangen", "ontvangen", "mislukt"):
            services.process_next_photo(self.spy)
            sub.refresh_from_db()
            self.assertEqual(sub.status, expected)
            if expected == "ontvangen":
                self.assertIsNotNone(self.storage.size(sub.original_key))  # niets kwijt bij een storing
        self.assertEqual((sub.failure_code, sub.reserved_bytes, sub.original_key), ("verwerking", 0, ""))

    def test_mislukte_verwijdering_blijft_niet_voor_altijd_bekend(self):
        sub, _ = self.reserve_one()
        self.storage.write(sub.original_key, b"\xff\xd8\xff" + b"x" * 3000)
        key = sub.original_key
        self.spy.fail["delete"] = OSError("verwijderen mislukt")
        self.assertEqual(services.complete_photo_upload(self.token, sub.uid, self.spy).status, "mislukt")
        self.spy.fail.clear()
        self.assertIsNotNone(self.storage.size(key))  # restant staat er nog
        import os

        old = timezone.now().timestamp() - 48 * 3600
        os.utime(Path(self.dir) / key, (old, old))
        self.assertEqual(services.cleanup_orphans(self.storage), 1)  # de sleutel stond niet meer in de database: opruimen vindt hem
        self.assertIsNone(self.storage.size(key))

    def test_master_geschreven_maar_database_wint_niet_laat_geen_wees_achter(self):
        sub, data = self.reserve_one()
        self.upload(sub, data)
        services.complete_photo_upload(self.token, sub.uid, self.spy)
        self.spy.hooks["write"] = lambda: Submission.objects.filter(pk=sub.pk).update(status="verwijderd")  # iemand anders verwijdert tijdens het verwerken
        services.process_next_photo(self.spy)
        self.assertEqual(Submission.objects.get(pk=sub.pk).status, "verwijderd")
        self.assertEqual([k for k, _ in self.storage.keys("moments/") if "/master/" in k], [])


class BytesTests(UploadTestCase):
    def test_grote_originelen_vullen_het_album_niet_ten_onrechte(self):
        """Regressie: een ontvangen origineel van 20 MB telde als 20 MB tegen het plafond, terwijl de master hoogstens 8 MB wordt."""
        MB = 1024 * 1024
        Album.objects.filter(pk=self.album.pk).update(max_per_album=3)
        album = Album.objects.get(pk=self.album.pk)
        token = services.issue_token(album)[0]
        for _ in range(2):
            Submission.objects.create(
                album=album, guest_token=token, kind="foto", status="ontvangen", client_id=uuid.uuid4(), content_type="image/jpeg",
                size_bytes=20 * MB, original_bytes=20 * MB, reserved_bytes=limits.PHOTO_MAX_STORED_BYTES, original_key="moments/x/orig/y",
            )
        info = services.album_storage(album)
        self.assertEqual(info["reserved"], 2 * limits.PHOTO_MAX_STORED_BYTES)
        self.assertEqual(info["originals"], 40 * MB)
        self.assertEqual(info["committed"], 16 * MB)  # niet 40 MB
        self.assertLess(info["committed"] + limits.PHOTO_MAX_STORED_BYTES, album.bytes_cap + 1)
        client = self.guest()
        self.assertEqual(self.reserve(client, jpeg_bytes()).status_code, 201)  # de derde foto past

    def test_klare_masters_tellen_met_hun_werkelijke_omvang(self):
        client = self.guest()
        self.upload_ok(client, jpeg_bytes(size=(800, 600)))
        info_before = services.album_storage(self.album)
        self.assertEqual(info_before["reserved"], limits.PHOTO_MAX_STORED_BYTES)
        self.assertEqual(info_before["masters"], 0)
        self.process_all()
        info = services.album_storage(self.album)
        sub = Submission.objects.get()
        self.assertEqual((info["reserved"], info["masters"], info["originals"]), (0, sub.master_bytes, 0))
        self.assertEqual(sub.master_bytes, self.storage.size(sub.storage_key))
        self.assertLess(info["committed"], limits.PHOTO_MAX_STORED_BYTES)

    def test_mislukte_en_verlopen_posten_tellen_niet_mee(self):
        client = self.guest()
        _, bad = self.upload_ok(client, b"\xff\xd8\xff" + b"x" * 3000)
        self.assertEqual(bad.json()["status"], "mislukt")
        res = self.reserve(client, jpeg_bytes())
        Submission.objects.filter(uid=res.json()["id"]).update(reservation_expires_at=timezone.now() - timedelta(seconds=1))
        info = services.album_storage(self.album)
        self.assertEqual((info["reserved"], info["masters"], info["originals"]), (0, 0, 0))

    def test_bytesplafond_blokkeert_alleen_als_gereserveerd_plus_masters_te_veel_is(self):
        client = self.guest()
        with mock.patch.object(Album, "bytes_cap", new=limits.PHOTO_MAX_STORED_BYTES * 2 - 1):
            self.assertEqual(self.reserve(client, jpeg_bytes()).status_code, 201)
            res = self.reserve(client, jpeg_bytes())
        self.assertEqual((res.status_code, res.json()["fout"]), (409, "plafond_album"))


class S3BeschermingTests(UploadTestCase):
    GOED = dict(MOMENTS_STORAGE="s3", MOMENTS_S3_BUCKET="vaylide-moments-test", MOMENTS_S3_ACCESS_KEY="AKIAMOMENTS", MOMENTS_S3_SECRET_KEY="geheim-moments",
                MOMENTS_S3_ENDPOINT="https://s3.example.test", MOMENTS_S3_REGION="nl-ams", BACKUP_S3_BUCKET="vaylide-backups",
                BACKUP_S3_ACCESS_KEY="AKIABACKUP", BACKUP_S3_SECRET_KEY="geheim-backup", MOMENTS_S3_PRODUCTION_OK=False)

    def check(self, **extra):
        with override_settings(**{**self.GOED, **extra}):
            return get_storage()

    def refused(self, **extra):
        with self.assertRaises(StorageNotReady):
            self.check(**extra)

    def test_een_aparte_testbucket_in_testmodus_is_toegestaan(self):
        self.assertIsInstance(self.check(), S3Storage)

    def test_back_upbucket_en_back_upsleutels_worden_geweigerd(self):
        self.refused(MOMENTS_S3_BUCKET="vaylide-backups")
        self.refused(MOMENTS_S3_BUCKET="  VAYLIDE-Backups ")
        self.refused(MOMENTS_S3_ACCESS_KEY="AKIABACKUP")
        self.refused(MOMENTS_S3_SECRET_KEY="geheim-backup")
        self.refused(BACKUP_S3_BUCKET="vaylide-moments-test")

    def test_in_testmodus_alleen_een_bucket_met_test_in_de_naam(self):
        self.refused(MOMENTS_S3_BUCKET="vaylide-moments")
        self.refused(MOMENTS_S3_BUCKET="vaylide-productie")

    def test_live_vraagt_uitdrukkelijk_akkoord_en_geen_testbucket(self):
        self.refused(TEST_MODE=False, MOMENTS_S3_BUCKET="vaylide-moments")  # geen akkoord van de eigenaar
        self.refused(TEST_MODE=False, MOMENTS_S3_PRODUCTION_OK=True)  # akkoord, maar een testbucket in live
        self.assertIsInstance(self.check(TEST_MODE=False, MOMENTS_S3_PRODUCTION_OK=True, MOMENTS_S3_BUCKET="vaylide-moments"), S3Storage)

    def test_onvolledige_instellingen_en_standaard_zijn_veilig(self):
        self.refused(MOMENTS_S3_ACCESS_KEY="")
        self.refused(MOMENTS_S3_SECRET_KEY="")
        self.refused(MOMENTS_S3_BUCKET="")
        from django.conf import settings

        self.assertFalse(getattr(settings, "MOMENTS_S3_PRODUCTION_OK", False))
        self.assertEqual(settings.MOMENTS_STORAGE, "lokaal")

    def test_via_http_geeft_een_geweigerde_opslag_een_503_en_geen_inzending(self):
        client = self.guest()
        with override_settings(**{**self.GOED, "MOMENTS_S3_BUCKET": "vaylide-backups"}):
            res = self.reserve(client, jpeg_bytes())
        self.assertEqual((res.status_code, res.json()["fout"]), (503, "opslag_niet_klaar"))
        self.assertEqual(Submission.objects.count(), 0)

    def test_onderhoud_wijst_een_gevaarlijke_opslag_af(self):
        with override_settings(**{**self.GOED, "MOMENTS_S3_ACCESS_KEY": "AKIABACKUP"}):
            from django.core.management.base import CommandError

            with self.assertRaises(CommandError):
                call_command("moments_onderhoud", stdout=io.StringIO())

    def test_opruimen_raakt_alleen_eigen_sleutels(self):
        fake = mock.Mock()
        fake.keys.return_value = [("moments/ander/bestand.txt", 0), ("backups/vaylide/db.enc", 0), ("moments/00000000-0000-0000-0000-000000000000/orig/" + "c" * 32 + ".jpg", 0)]
        self.assertEqual(services.cleanup_orphans(fake), 1)
        fake.delete.assert_called_once_with("moments/00000000-0000-0000-0000-000000000000/orig/" + "c" * 32 + ".jpg")


class GelijktijdigeSessiestartsTests(PostgresBasis):
    def test_driehonderd_vrijwel_gelijktijdige_starts_en_extra_starts_worden_netjes_geweigerd(self):
        import time

        jobs = [lambda: services.start_guest_session(self.album.public_code)[0].pk for _ in range(320)]
        # 320 starts in golven van 20 tegelijk (PostgreSQL staat standaard 100 verbindingen toe)
        results, begin = [], time.time()
        for i in range(0, len(jobs), 20):
            results += self.race(jobs[i:i + 20])
        elapsed = time.time() - begin
        ok = [r for r in results if isinstance(r, int)]
        refused = [r for r in results if not isinstance(r, int)]
        self.assertGreaterEqual(len(ok), 300, results)
        self.assertLessEqual(len(ok), 300 + int(elapsed * limits.SIGNUP_BUCKET_REFILL_PER_MIN / 60) + 2)  # niet meer dan emmer plus aanvulling
        self.assertTrue(all(r == "even_wachten" for r in refused), refused)  # nooit een andere fout of crash
        self.assertEqual(GuestToken.objects.filter(album=self.album).count(), len(ok))  # elke gelukte start is precies een gast


class GelijktijdigheidVerloopTests(PostgresBasis):
    """Voortzetting op PostgreSQL: melden en opruimen van verlopen reserveringen tegelijk, en tegelijk verwerken."""

    def test_melden_en_opruimen_tegelijk_geeft_een_consistente_uitslag(self):
        Album.objects.filter(pk=self.album.pk).update(max_per_album=100, max_per_guest=50)
        token = services.issue_token(self.album)[0]
        data = jpeg_bytes()
        outcomes = set()
        for _ in range(5):
            sub, _target = services.reserve_photo_upload(token, client_id=uuid.uuid4(), content_type="image/jpeg", size_bytes=len(data), storage=self.storage)
            self.storage.write(sub.original_key, data)
            Submission.objects.filter(pk=sub.pk).update(reservation_expires_at=timezone.now() + timedelta(milliseconds=50))
            import time

            time.sleep(0.1)
            self.race([lambda: services.complete_photo_upload(token, sub.uid, self.storage), lambda: services.expire_reservations(self.storage)])
            final = Submission.objects.get(pk=sub.pk)
            outcomes.add(final.status)
            self.assertIn(final.status, {"mislukt", "ontvangen"})
            if final.status == "mislukt":
                self.assertEqual((final.failure_code, final.reserved_bytes, final.original_key), ("verlopen", 0, ""))
            else:
                self.assertTrue(final.original_key and self.storage.size(final.original_key))
        self.assertTrue(outcomes)

    def test_twee_verwerkers_tegelijk_verwerken_elke_foto_een_keer(self):
        Album.objects.filter(pk=self.album.pk).update(max_per_album=100, max_per_guest=50)
        token = services.issue_token(self.album)[0]
        ids = []
        for i in range(4):
            data = jpeg_bytes(color=(i * 60, 5, 200 - i * 40))
            sub, _t = services.reserve_photo_upload(token, client_id=uuid.uuid4(), content_type="image/jpeg", size_bytes=len(data), storage=self.storage)
            self.storage.write(sub.original_key, data)
            services.complete_photo_upload(token, sub.uid, self.storage)
            ids.append(sub.pk)

        def worker():
            n = 0
            while services.process_next_photo(self.storage):
                n += 1
            return n

        done = self.race([worker, worker, worker])
        self.assertEqual(sum(r for r in done if isinstance(r, int)), 4, done)
        self.assertEqual(set(Submission.objects.filter(pk__in=ids).values_list("status", flat=True)), {"klaar"})
        self.assertEqual(set(Submission.objects.filter(pk__in=ids).values_list("attempts", flat=True)), {1})
        self.assertEqual(len([k for k, _ in self.storage.keys("moments/")]), 4)

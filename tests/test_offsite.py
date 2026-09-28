"""Tweede back-uplocatie: versleutelde kopie naar S3-compatibele opslag (hier nagebootst)."""
import shutil
import tempfile
from io import StringIO
from pathlib import Path
from unittest import mock

from cryptography.fernet import Fernet
from django.core.management import CommandError, call_command
from django.test import override_settings

from core.offsite import OffsiteError, configured, copy_offsite, decrypt_file, encrypt_file, upload
from processing.models import OutboundEmail

from .helpers import VaylideTestCase

KEY = Fernet.generate_key().decode()
S3 = dict(BACKUP_S3_BUCKET="vaylide-backup", BACKUP_S3_ACCESS_KEY="toegang", BACKUP_S3_SECRET_KEY="geheim",
          BACKUP_S3_ENDPOINT="https://opslag.example.eu", BACKUP_S3_REGION="eu-central", BACKUP_S3_PREFIX="vaylide",
          BACKUP_ENCRYPTION_KEY=KEY)


class OffsiteTests(VaylideTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.src = self.tmp / "vaylide-20261224-020000.tar.gz"
        self.src.write_bytes(b"gegevens " * 700_000)  # groter dan een blok van 4 MB

    def test_off_until_everything_is_filled_in(self):
        self.assertFalse(configured())
        self.assertEqual(copy_offsite(self.src), "niet ingesteld")
        with override_settings(**{**S3, "BACKUP_ENCRYPTION_KEY": ""}):
            self.assertFalse(configured())

    @override_settings(**S3)
    def test_encrypt_and_decrypt_round_trip(self):
        enc = encrypt_file(self.src, self.tmp / "x.enc")
        self.assertNotIn(b"gegevens gegevens", enc.read_bytes()[:2000])
        out = decrypt_file(enc, self.tmp / "terug.tar.gz")
        self.assertEqual(out.read_bytes(), self.src.read_bytes())
        with override_settings(BACKUP_ENCRYPTION_KEY=Fernet.generate_key().decode()):
            with self.assertRaises(OffsiteError):
                decrypt_file(enc, self.tmp / "fout.tar.gz")

    @override_settings(**S3)
    def test_upload_sends_only_the_encrypted_file(self):
        client = mock.Mock()
        with mock.patch("boto3.client", return_value=client) as factory:
            key = upload(self.src)
        self.assertEqual(key, "vaylide/vaylide-20261224-020000.tar.gz.enc")
        self.assertEqual(factory.call_args.kwargs["endpoint_url"], "https://opslag.example.eu")
        sent_path, bucket, sent_key = client.upload_file.call_args.args
        self.assertEqual((bucket, sent_key), ("vaylide-backup", key))
        self.assertTrue(sent_path.endswith(".enc"))
        self.assertFalse(Path(sent_path).exists())  # tijdelijk bestand opgeruimd

    @override_settings(**S3)
    def test_failure_notifies_owner_but_does_not_raise(self):
        client = mock.Mock()
        client.upload_file.side_effect = RuntimeError("geen verbinding")
        with mock.patch("boto3.client", return_value=client):
            with self.captureOnCommitCallbacks(execute=True):
                self.assertEqual(copy_offsite(self.src), "mislukt")
        self.assertTrue(OutboundEmail.objects.filter(unique_key=f"offsite-fail:{self.src.name}").exists())

    def test_commands(self):
        out = StringIO()
        call_command("backup", "--nieuwe-sleutel", stdout=out)
        Fernet(out.getvalue().splitlines()[0].encode())  # geldige sleutel
        with self.assertRaises(CommandError):
            call_command("backup", "--offsite", stdout=StringIO())

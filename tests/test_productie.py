"""Voorbereiding op productie: moeilijk te raden links, back-up en herstel, en de geplande taak."""
import re
import shutil
import tempfile
from pathlib import Path

from django.core.management import CommandError, call_command
from django.test import Client, override_settings

from accounts.models import User
from core.backup import make_backup, restore_backup
from invitations.models import Invitation
from invitations.services import assign_slug

from .helpers import VaylideTestCase


class SlugTests(VaylideTestCase):
    def test_link_has_eight_random_characters_after_the_title(self):
        inv = Invitation(title="Anna & Bram")
        slug = assign_slug(inv)
        self.assertRegex(slug, r"^anna-en-bram-[a-z2-9]{8}$")
        self.assertIsNone(re.search(r"[ilo01]", slug.rsplit("-", 1)[1]))


class BackupTests(VaylideTestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.uploads = self.tmp / "uploads"
        (self.uploads / "a").mkdir(parents=True)
        (self.uploads / "a" / "foto.txt").write_text("foto")

    def test_backup_contains_data_and_uploads_and_restores(self):
        with override_settings(DATA_DIR=self.tmp, MEDIA_ROOT=self.uploads):
            User.objects.create(email="klant@vierlief.test")
            path = make_backup(keep=2)
            self.assertTrue(path.name.startswith("vaylide-") and path.name.endswith(".tar.gz"))
            # Herstel weigert een database die niet leeg is.
            with self.assertRaises(CommandError):
                call_command("restore_backup", str(path), "--ja")
            User.objects.all().delete()
            shutil.rmtree(self.uploads)
            info = restore_backup(path)
            self.assertIn("gemaakt", info)
            self.assertTrue(User.objects.filter(email="klant@vierlief.test").exists())
            self.assertEqual((self.uploads / "a" / "foto.txt").read_text(), "foto")

    def test_old_backups_are_pruned(self):
        with override_settings(DATA_DIR=self.tmp, MEDIA_ROOT=self.uploads):
            backups = self.tmp / "backups"
            backups.mkdir()
            for stamp in ("20200101-000000", "20200102-000000", "20200103-000000"):
                (backups / f"vaylide-{stamp}.tar.gz").write_bytes(b"")
            newest = make_backup(keep=2)
            self.assertEqual(sorted(p.name for p in backups.glob("*.tar.gz")), ["vaylide-20200103-000000.tar.gz", newest.name])

    def test_restore_checks_file_and_confirmation(self):
        with self.assertRaises(CommandError):
            call_command("restore_backup", str(self.tmp / "bestaat-niet.tar.gz"), "--ja")
        (self.tmp / "b.tar.gz").write_bytes(b"")
        with self.assertRaises(CommandError):
            call_command("restore_backup", str(self.tmp / "b.tar.gz"))


class CronTests(VaylideTestCase):
    def test_cron_needs_token_and_can_make_a_backup(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        with override_settings(JOBS_CRON_TOKEN="geheim-token", DATA_DIR=tmp, MEDIA_ROOT=tmp / "uploads"):
            self.assertEqual(Client().post("/intern/taken/").status_code, 404)
            self.assertEqual(Client().post("/intern/taken/", HTTP_AUTHORIZATION="Bearer fout").status_code, 404)
            ok = Client().post("/intern/taken/?backup=1", HTTP_AUTHORIZATION="Bearer geheim-token")
            self.assertEqual(ok.status_code, 200)
            self.assertIn("backup: vaylide-", ok.content.decode())
            self.assertEqual(len(list((tmp / "backups").glob("*.tar.gz"))), 1)

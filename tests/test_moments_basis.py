"""Moments, stap 1: datamodel, feature-vlag, tokens, plafonds en zichtbaarheid. Er zijn nog geen pagina's of uploads."""
from datetime import timedelta
from io import StringIO

from django.apps import apps
from django.core.management import call_command
from django.http import Http404
from django.test import RequestFactory, TestCase, override_settings
from django.urls import get_resolver
from django.utils import timezone

from moments import limits, services
from moments.flags import moments_enabled, require_moments
from moments.models import Album, GuestToken, Submission
from tests.helpers import VaylideTestCase

AAN = dict(MOMENTS_ENABLED=True)


class VlagTests(TestCase):
    def test_standaard_uit(self):
        # Onafhankelijk van de omgeving: de ingebouwde standaard en het gedrag zonder vlag, ook als de testrun de vlag aanzet.
        import os
        from pathlib import Path
        from unittest import mock

        from django.conf import settings

        from config.settings import env_bool

        bron = (Path(settings.BASE_DIR) / "config" / "settings.py").read_text()
        self.assertIn('MOMENTS_ENABLED = env_bool("VIERLIEF_MOMENTS_ENABLED", False)', bron)
        with mock.patch.dict(os.environ):
            os.environ.pop("VIERLIEF_MOMENTS_ENABLED", None)
            self.assertFalse(env_bool("VIERLIEF_MOMENTS_ENABLED", False))
        with override_settings(MOMENTS_ENABLED=False):
            self.assertFalse(moments_enabled())

    def test_view_bestaat_niet_als_vlag_uit(self):
        @require_moments
        def view(request):
            return "ok"

        request = RequestFactory().get("/")
        with override_settings(MOMENTS_ENABLED=False):
            with self.assertRaises(Http404):
                view(request)
        with override_settings(**AAN):
            self.assertEqual(view(request), "ok")

    def test_alleen_de_moments_routes(self):
        # Eén ingang in de hoofd-urls ('moments/'); de adressen daaronder staan in moments/urls.py.
        namen = [p.pattern.regex.pattern for p in get_resolver().url_patterns if "moments" in p.pattern.regex.pattern.lower()]
        self.assertEqual(len(namen), 1)

    def test_migraties_zijn_compleet(self):
        out = StringIO()
        call_command("makemigrations", "--check", "--dry-run", stdout=out)

    def test_bestaande_apps_verwijzen_niet_naar_moments(self):
        for model in apps.get_models():
            if model._meta.app_label == "moments":
                continue
            for field in model._meta.get_fields():
                if field.auto_created:
                    continue  # omgekeerde relatie vanuit moments: geen kolom in de bestaande tabel
                related = getattr(field, "related_model", None)
                if related is not None and not isinstance(related, str):
                    self.assertNotEqual(related._meta.app_label, "moments", f"{model.__name__}.{field.name}")


class MomentsTestCase(VaylideTestCase):
    def setUp(self):
        super().setUp()
        self.owner = self.make_customer("eigenaar-moments@example.com")
        self.invitation = self.published(owner=self.owner)
        self.album = Album.objects.create(invitation=self.invitation, status=Album.Status.OPEN)

    def token(self, album=None, **kwargs):
        return services.issue_token(album or self.album, **kwargs)


@override_settings(**AAN)
class TokenTests(MomentsTestCase):
    def test_alleen_hash_wordt_bewaard(self):
        token, raw = self.token(label="Oma")
        self.assertNotIn(raw, token.token_hash)
        self.assertFalse(GuestToken.objects.filter(token_hash=raw).exists())
        self.assertEqual(len(token.token_hash), 64)
        self.assertGreaterEqual(len(raw), 30)

    def test_tokens_zijn_uniek(self):
        _, a = self.token()
        _, b = self.token()
        self.assertNotEqual(a, b)

    def test_oplossen(self):
        token, raw = self.token()
        self.assertEqual(services.resolve_token(raw), token)
        self.assertIsNone(services.resolve_token(raw + "x"))
        self.assertIsNone(services.resolve_token(""))
        self.assertIsNone(services.resolve_token("a" * 500))

    def test_ingetrokken_en_verlopen(self):
        token, raw = self.token()
        services.revoke_token(token)
        self.assertIsNone(services.resolve_token(raw))
        _, raw2 = self.token(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertIsNone(services.resolve_token(raw2))

    def test_vlag_uit_lost_niets_op(self):
        _, raw = self.token()
        with override_settings(MOMENTS_ENABLED=False):
            self.assertIsNone(services.resolve_token(raw))


@override_settings(**AAN)
class PlafondTests(MomentsTestCase):
    def test_standaardwaarden_en_hard_plafond(self):
        self.assertEqual(self.album.guest_limit, limits.DEFAULT_MAX_PER_GUEST)
        self.assertEqual(self.album.album_limit, limits.DEFAULT_MAX_PER_ALBUM)
        self.album.max_per_guest = 10_000
        self.album.max_per_album = 10_000_000
        self.assertEqual(self.album.guest_limit, limits.HARD_MAX_PER_GUEST)
        self.assertEqual(self.album.album_limit, limits.HARD_MAX_PER_ALBUM)

    def test_albummaster_eis_staat_vast(self):
        self.assertEqual(limits.ALBUM_MASTER_MAX_EDGE_PX, 6000)

    def test_plafond_per_gast(self):
        self.album.max_per_guest = 2
        self.album.save()
        token, _ = self.token()
        other, _ = self.token()
        services.create_submission(token)
        services.create_submission(token)
        with self.assertRaises(services.SubmissionRefused) as ctx:
            services.create_submission(token)
        self.assertEqual(ctx.exception.code, "plafond_gast")
        services.create_submission(other)  # een andere gast heeft een eigen plafond

    def test_plafond_per_evenement(self):
        self.album.max_per_album = 2
        self.album.save()
        a, _ = self.token()
        b, _ = self.token()
        services.create_submission(a)
        services.create_submission(b)
        with self.assertRaises(services.SubmissionRefused) as ctx:
            services.create_submission(a)
        self.assertEqual(ctx.exception.code, "plafond_album")

    def test_afgewezen_inzending_telt_niet_mee(self):
        self.album.max_per_guest = 1
        self.album.save()
        token, _ = self.token()
        first = services.create_submission(token)
        first.status = Submission.Status.REJECTED
        first.save()
        services.create_submission(token)

    def test_gesloten_album_en_venster(self):
        token, _ = self.token()
        self.album.status = Album.Status.CLOSED
        self.album.save()
        with self.assertRaises(services.SubmissionRefused):
            services.create_submission(token)
        self.album.status = Album.Status.OPEN
        self.album.opens_at = timezone.now() + timedelta(hours=1)
        self.album.save()
        with self.assertRaises(services.SubmissionRefused):
            services.create_submission(token)
        self.album.opens_at = None
        self.album.closes_at = timezone.now() - timedelta(minutes=1)
        self.album.save()
        with self.assertRaises(services.SubmissionRefused):
            services.create_submission(token)

    def test_ingetrokken_token_mag_niet_meer_insturen(self):
        token, _ = self.token()
        services.revoke_token(token)
        with self.assertRaises(services.SubmissionRefused) as ctx:
            services.create_submission(token)
        self.assertEqual(ctx.exception.code, "token")

    def test_vlag_uit_weigert_inzending(self):
        token, _ = self.token()
        with override_settings(MOMENTS_ENABLED=False):
            with self.assertRaises(services.SubmissionRefused) as ctx:
                services.create_submission(token)
        self.assertEqual(ctx.exception.code, "uit")
        self.assertEqual(Submission.objects.count(), 0)


@override_settings(**AAN)
class ZichtbaarheidTests(MomentsTestCase):
    def test_gast_ziet_alleen_eigen_inzendingen(self):
        a, _ = self.token()
        b, _ = self.token()
        mine = services.create_submission(a)
        theirs = services.create_submission(b)
        self.assertEqual(list(services.submissions_visible_to_guest(a)), [mine])
        self.assertEqual(list(services.submissions_visible_to_guest(b)), [theirs])
        self.assertEqual(limits.GUEST_VISIBILITY, "own")

    def test_token_van_ander_album_ziet_niets_van_dit_album(self):
        other_inv = self.published(owner=self.make_customer("ander@example.com"))
        other_album = Album.objects.create(invitation=other_inv, status=Album.Status.OPEN)
        a, _ = self.token()
        b, _ = self.token(other_album)
        services.create_submission(a)
        self.assertEqual(services.submissions_visible_to_guest(b).count(), 0)

    def test_verwijderde_en_ingetrokken_zichtbaar_niet(self):
        a, _ = self.token()
        sub = services.create_submission(a)
        sub.status = Submission.Status.REMOVED
        sub.save()
        self.assertEqual(services.submissions_visible_to_guest(a).count(), 0)
        sub.status = Submission.Status.RECEIVED
        sub.save()
        services.revoke_token(a)
        self.assertEqual(services.submissions_visible_to_guest(a).count(), 0)

    def test_klant_ziet_alleen_eigen_albums(self):
        other = self.make_customer("ander2@example.com")
        other_inv = self.published(owner=other)
        other_album = Album.objects.create(invitation=other_inv)
        self.assertEqual(list(services.albums_for_user(self.owner)), [self.album])
        self.assertEqual(list(services.albums_for_user(other)), [other_album])
        from django.contrib.auth.models import AnonymousUser

        self.assertEqual(services.albums_for_user(AnonymousUser()).count(), 0)


class BasisTests(MomentsTestCase):
    def test_taal_en_valuta_standaard(self):
        self.assertEqual((self.album.language, self.album.currency), ("nl", "EUR"))

    def test_een_album_per_uitnodiging(self):
        from django.db import IntegrityError, transaction

        with self.assertRaises(IntegrityError), transaction.atomic():
            Album.objects.create(invitation=self.invitation)

    def test_bestandspad_is_onraadbaar_en_privé(self):
        token, _ = self.token()
        with override_settings(**AAN):
            sub = services.create_submission(token)
        pad1 = Submission._meta.get_field("file").upload_to(sub, "../../Foto.JPG")
        pad2 = Submission._meta.get_field("file").upload_to(sub, "foto.jpg")
        self.assertTrue(pad1.startswith(f"moments/{self.album.uid}/"))
        self.assertNotIn("..", pad1)
        self.assertNotIn("Foto", pad1)
        self.assertNotEqual(pad1, pad2)

    def test_geen_moments_adres_met_vlag_uit(self):
        with override_settings(MOMENTS_ENABLED=False):
            self.assertEqual(self.client.get("/moments/", secure=True).status_code, 404)
            self.assertEqual(self.client.get("/moments/abc/", secure=True).status_code, 404)

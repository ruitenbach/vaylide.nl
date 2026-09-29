"""Gedeelde hulpmiddelen voor de tests van Vaylide."""
from __future__ import annotations

import io
import re
import shutil
import tempfile
import time
from datetime import timedelta

from django.conf import settings
from django.core import signing
from django.test import TestCase, override_settings
from django.utils import timezone
from PIL import Image

from accounts.models import User
from catalog.models import Template
from core.utils import FORM_TS_SALT
from invitations.models import Invitation
from invitations.services import create_draft, save_draft
from orders.models import Payment
from orders.services import start_checkout, sync_payment


def future_date(days=120):
    return (timezone.localdate() + timedelta(days=days)).isoformat()


def old_form_ts(seconds=30) -> str:
    return signing.TimestampSigner(salt=FORM_TS_SALT).sign(str(int(time.time()) - seconds))


def jpeg_file(width=1200, height=900, name="foto.jpg", exif_gps=False, fmt="JPEG"):
    image = Image.new("RGB", (width, height), (180, 140, 150))
    buffer = io.BytesIO()
    kwargs = {}
    if exif_gps:
        exif = Image.Exif()
        exif[0x010F] = "TestCamera"  # Make
        gps = {1: "N", 2: (52.0, 5.0, 0.0), 3: "E", 4: (4.0, 53.0, 0.0)}
        exif[0x8825] = gps
        kwargs["exif"] = exif.tobytes()
    image.save(buffer, fmt, **kwargs)
    buffer.seek(0)
    buffer.name = name
    return buffer


class VaylideTestCase(TestCase):
    """Basis: aparte uploadmap, testmodus en hulpfuncties."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_dir = tempfile.mkdtemp(prefix="vaylide-test-")
        cls._settings = override_settings(
            MEDIA_ROOT=cls._media_dir,
            TEST_MODE=True,
            EMAIL_MODE="outbox",
            PAYMENT_PROVIDER="test",
            JOBS_RUN_INLINE=True,
            FACES_BACKGROUND=False,
            ANTHROPIC_API_KEY="",
            BASE_URL="https://vaylide.test",
            # Tests mogen niet afhangen van een eerdere collectstatic (manifest).
            STORAGES={**settings.STORAGES, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}},
        )
        cls._settings.enable()

    @classmethod
    def tearDownClass(cls):
        cls._settings.disable()
        shutil.rmtree(cls._media_dir, ignore_errors=True)
        super().tearDownClass()

    # --- gegevens -----------------------------------------------------------
    def make_customer(self, email="klant@example.com") -> User:
        user = User.objects.create_user(email=email)
        user.email_verified_at = timezone.now()
        user.save()
        return user

    def make_staff(self, email="eigenaar@example.com", password="Een-lang-wachtwoord-2026") -> User:
        return User.objects.create_superuser(email=email, password=password)

    def complete_content(self, invitation: Invitation, **overrides) -> dict:
        content = dict(invitation.draft_content)
        content["names"] = {"partner_1": "Anna", "partner_2": "Bram"}
        content.update(
            {
                "date": future_date(120),
                "start_time": "14:00",
                "end_time": "23:00",
                "timezone": "Europe/Amsterdam",
                "venue_name": "Kasteel Test",
                "address": "Teststraat 1\n1234 AB Utrecht",
                "welcome_text": "Welkom op onze bruiloft.",
            }
        )
        content["rsvp"] = dict(content["rsvp"], deadline=future_date(90), max_party_size=2)
        content["program"] = [{"time": "14:00", "title": "Ceremonie", "description": ""}]
        content.update(overrides)
        return content

    def make_invitation(self, owner=None, template="liefde-op-papier", occasion="bruiloft", complete=True, **overrides) -> Invitation:
        invitation = create_draft(occasion=occasion, template=Template.objects.get(slug=template), owner=owner)
        if complete:
            invitation = save_draft(invitation, expected_rev=None, content=self.complete_content(invitation, **overrides), user=owner)
        return invitation

    def pay(self, invitation: Invitation, customer, package="essentieel", extras=None) -> Payment:
        with self.captureOnCommitCallbacks(execute=True):
            payment = start_checkout(invitation, user=customer, package_code=package, optional_codes=extras or [], terms_accepted=True)
        self.provider_says(payment, Payment.Status.PAID)
        invitation.refresh_from_db()
        return payment

    def provider_says(self, payment: Payment, status: str, *, source="webhook") -> Payment:
        payment.refresh_from_db()
        payment.test_remote_status = status
        payment.save(update_fields=["test_remote_status"])
        with self.captureOnCommitCallbacks(execute=True):
            sync_payment(payment, source=source)
        payment.refresh_from_db()
        return payment

    def published(self, owner=None, **kwargs) -> Invitation:
        owner = owner or self.make_customer()
        invitation = self.make_invitation(owner=owner, **kwargs)
        self.pay(invitation, owner)
        invitation.refresh_from_db()
        return invitation

    # --- gasten ----------------------------------------------------------------
    def rsvp(self, client, invitation, *, token=None, json=True, **data):
        page = client.get(f"/u/{invitation.slug}/")
        match = re.search(r'name="client_token" value="([^"]+)"', page.content.decode())
        payload = {
            "client_token": token or (match.group(1) if match else "handmatig-token-123456"),
            "form_ts": old_form_ts(),
            "name": "Gast",
            "attending": "ja",
            "party_size": "1",
        }
        payload.update(data)
        headers = {"HTTP_ACCEPT": "application/json"} if json else {}
        return client.post(f"/u/{invitation.slug}/aanmelden/", payload, **headers)

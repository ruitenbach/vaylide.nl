"""Testgegevens voor e2e/rsvp_personen.cjs (alleen in testmodus): een betaalde, online bruiloftsuitnodiging met aanmelden voor maximaal 4 personen.

Gebruik (schrijft JSON naar stdout):
    .venv/bin/python e2e/rsvp_setup.py > /tmp/rsvp.json
"""
import json
import os
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.db import transaction  # noqa: E402
from django.utils import timezone  # noqa: E402

from accounts.models import User  # noqa: E402
from catalog.models import Template  # noqa: E402
from invitations.services import create_draft, save_draft  # noqa: E402
from orders.models import Payment  # noqa: E402
from orders.services import start_checkout, sync_payment  # noqa: E402

if not settings.TEST_MODE:
    raise SystemExit("Alleen in testmodus gebruiken (VIERLIEF_MODE=test).")

run = timezone.now().strftime("%Y%m%d%H%M%S")
owner = User.objects.create_user(email=f"rsvp-{run}@vaylide.test")
owner.email_verified_at = timezone.now()
owner.save()
inv = create_draft(occasion="bruiloft", template=Template.objects.get(slug="liefde-op-papier"), owner=owner)
content = dict(inv.draft_content)
today = timezone.localdate()
content["names"] = {"partner_1": "Sanne", "partner_2": "Daan"}
content.update({"date": (today + timedelta(days=90)).isoformat(), "start_time": "14:00", "timezone": "Europe/Amsterdam", "venue_name": "De Oranjerie",
                "address": "Teststraat 1\n1234 AB Utrecht", "welcome_text": "Welkom bij onze bruiloft."})
content["rsvp"] = dict(content["rsvp"], deadline="", max_party_size=4)
inv = save_draft(inv, expected_rev=None, content=content, user=owner)
with transaction.atomic():
    payment = start_checkout(inv, user=owner, package_code="essentieel", optional_codes=[], terms_accepted=True)
payment.test_remote_status = Payment.Status.PAID
payment.save()
sync_payment(payment, source="webhook")
from processing.jobs import process_due  # noqa: E402

process_due()
inv.refresh_from_db()
print(json.dumps({"slug": inv.slug, "uid": str(inv.uid), "email": owner.email, "public_path": inv.public_path}))

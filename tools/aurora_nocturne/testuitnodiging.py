"""Maakt een TESTUITNODIGING van Aurora Nocturne met de voorbeeldgegevens van de eigenaar, om de kop te beoordelen.

Gebruik (alleen lokaal, in testmodus; gebruikt de ontwikkeldatabase):
    .venv/bin/python tools/aurora_nocturne/testuitnodiging.py
Schrijft het pad van de uitnodiging, bijvoorbeeld /u/<code>/. Alles is fictief en valt onder controle@vierlief.test.
"""
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.db import transaction  # noqa: E402
from django.utils import timezone  # noqa: E402

from accounts.models import User  # noqa: E402
from catalog.models import Template  # noqa: E402
from invitations.models import Invitation  # noqa: E402
from invitations.services import create_draft, save_draft  # noqa: E402
from orders.models import Payment  # noqa: E402
from orders.services import start_checkout, sync_payment  # noqa: E402

if not settings.TEST_MODE:
    raise SystemExit("Alleen in testmodus gebruiken (VIERLIEF_MODE=test).")

owner, _ = User.objects.get_or_create(email="controle@vierlief.test")
owner.email_verified_at = timezone.now()
owner.save()
Invitation.objects.filter(owner=owner, draft_content__names__partner_1="Sophie").delete()
template = Template.objects.get(slug="aurora-nocturne")
inv = create_draft(occasion="bruiloft", template=template, owner=owner)
content = dict(inv.draft_content)
content["headline"] = "Een bijzondere avond"
content["names"] = {"partner_1": "Sophie", "partner_2": "Daniël"}
content.update({
    "date": date(2027, 6, 14).isoformat(), "start_time": "18:30", "end_time": "01:00", "timezone": "Europe/Amsterdam",
    "venue_name": "Het Glazen Paviljoen (testlocatie)", "address": "Meerlaan 1\n1234 AB Voorbeeldstad",
    "welcome_text": "Lieve familie en vrienden,\n\nwe vieren onze avond graag met jullie, bij kaarslicht aan het water.",
    "program": [{"time": "18:30", "title": "Ontvangst", "description": "Met champagne in het paviljoen."}, {"time": "19:30", "title": "Diner", "description": ""}, {"time": "22:00", "title": "Dansen", "description": ""}],
    "dresscode": {"text": "Black tie", "colors": ["#0A1730", "#D9C38C", "#F3ECDC"]},
    "closing_text": "We zien jullie graag.",
})
content["rsvp"] = dict(content["rsvp"], deadline=date(2027, 5, 14).isoformat(), max_party_size=4)
inv = save_draft(inv, expected_rev=None, content=content, user=owner)
with transaction.atomic():
    payment = start_checkout(inv, user=owner, package_code="compleet", optional_codes=[], terms_accepted=True)
payment.test_remote_status = Payment.Status.PAID
payment.save()
sync_payment(payment, source="webhook")
from processing.jobs import process_due  # noqa: E402

process_due()
inv.refresh_from_db()
print(inv.public_path)

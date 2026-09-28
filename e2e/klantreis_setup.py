"""Testgegevens voor de controle van de hele klantreis (e2e/klantreis.cjs). Alleen in testmodus.

Maakt twee fictieve klanten (A en B) met elk een compleet, nog onbetaald ontwerp, en een beheerder met een
willekeurig wachtwoord. Schrijft alles als JSON naar stdout (het wachtwoord hoort niet in Git):
    .venv/bin/python e2e/klantreis_setup.py > /tmp/klantreis.json
"""
import json
import os
import secrets
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.utils import timezone  # noqa: E402

from accounts.models import User  # noqa: E402
from catalog.models import Template  # noqa: E402
from invitations.services import create_draft, save_draft  # noqa: E402

if not settings.TEST_MODE:
    raise SystemExit("Alleen in testmodus gebruiken (VIERLIEF_MODE=test).")

run = timezone.now().strftime("%Y%m%d%H%M%S")
today = timezone.localdate()


def customer(tag):
    user = User.objects.create_user(email=f"klantreis-{tag}-{run}@vaylide.test")
    user.email_verified_at = timezone.now()
    user.save()
    return user


def draft(owner, template, occasion, names):
    inv = create_draft(occasion=occasion, template=Template.objects.get(slug=template), owner=owner)
    content = dict(inv.draft_content)
    content["names"] = names
    content.update({
        "date": (today + timedelta(days=120)).isoformat(), "start_time": "14:00", "end_time": "22:00", "timezone": "Europe/Amsterdam",
        "venue_name": "Testlocatie De Klantreis", "address": "Teststraat 1\n1234 AB Utrecht", "welcome_text": "Welkom, dit is een test.",
    })
    content["rsvp"] = dict(content["rsvp"], deadline=(today + timedelta(days=90)).isoformat(), max_party_size=2)
    content["program"] = [{"time": "14:00", "title": "Ontvangst", "description": ""}]
    return save_draft(inv, expected_rev=None, content=content, user=owner)


a, b = customer("a"), customer("b")
paid_inv = draft(a, "liefde-op-papier", "bruiloft", {"partner_1": "Test", "partner_2": "Klantreis"})
cancel_inv = draft(a, "winterlicht", "kerst", {"family": "Familie Klantreis"})
b_inv = draft(b, "confetti", "verjaardag", {"person_name": "Kim", "age": "30"})
password = secrets.token_urlsafe(18)
staff = User.objects.create_superuser(email=f"klantreis-beheer-{run}@vaylide.test", password=password)
print(json.dumps({
    "a": a.email, "b": b.email, "staff": staff.email, "staff_password": password,
    "paid": str(paid_inv.uid), "cancel": str(cancel_inv.uid), "b_inv": str(b_inv.uid),
}))

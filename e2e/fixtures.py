"""Maakt herkenbare TESTGEGEVENS voor de visuele controles (Controle 2).

Gebruik (alleen lokaal/testomgeving):
    .venv/bin/python e2e/fixtures.py > /tmp/fixtures.json
Maakt per ontwerp: lange namen + verschillende fotoformaten, minimale gegevens,
een verstreken evenement en lange woorden in de titel (zoals "Nieuwjaarsreceptie"). Alles valt onder het klantaccount
controle@vierlief.test en is fictief.
"""
import io
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
from PIL import Image  # noqa: E402

from accounts.models import User  # noqa: E402
from catalog.models import Template  # noqa: E402
from invitations.images import process_photo  # noqa: E402
from invitations.models import GuestResponse, Invitation, MediaAsset  # noqa: E402
from invitations.services import create_draft, save_draft  # noqa: E402
from invitations.vragen import vraag  # noqa: E402
from orders.models import Payment  # noqa: E402
from orders.services import start_checkout, sync_payment  # noqa: E402

if not settings.TEST_MODE:
    raise SystemExit("Alleen in testmodus gebruiken (VIERLIEF_MODE=test).")
DEMO = Path(settings.BASE_DIR) / "static" / "img" / "demo"


def photo(invitation, name, size=None):
    src = Image.open(DEMO / f"{name}.webp").convert("RGB")
    if size:
        src = src.resize(size)
    buffer = io.BytesIO()
    src.save(buffer, "JPEG", quality=85)
    buffer.seek(0)
    buffer.name = f"{name}.jpg"
    buffer.size = buffer.getbuffer().nbytes
    processed = process_photo(buffer)
    asset = MediaAsset(invitation=invitation, kind="photo", original_name=f"{name}.jpg", content_type="image/webp",
                       size_bytes=processed.size_bytes, width=processed.width, height=processed.height)
    asset.file.save("groot.webp", processed.large, save=False)
    asset.file_medium.save("middel.webp", processed.medium, save=False)
    asset.file_thumb.save("klein.webp", processed.thumb, save=False)
    asset.save()
    return str(asset.uid)


def publish(invitation, owner, package="compleet"):
    with transaction.atomic():
        payment = start_checkout(invitation, user=owner, package_code=package, optional_codes=[], terms_accepted=True)
    payment.test_remote_status = Payment.Status.PAID
    payment.save()
    sync_payment(payment, source="webhook")
    from processing.jobs import process_due

    process_due()
    invitation.refresh_from_db()
    return invitation


LONG_WORDS = {
    "bruiloft": {"partner_1": "Maximiliaan", "partner_2": "Wilhelmina-Charlotte"},
    "verloving": {"partner_1": "Maximiliaan", "partner_2": "Wilhelmina-Charlotte"},
    "verjaardag": {"person_name": "Wilhelmina-Charlotte", "age": "100"},
    "jubileum": {"honorees": "Familie Vandenbroucke-Hoogeveen", "years": "125"},
    "babyshower": {"parents": "Anne-Wilhelmina & Maximiliaan", "baby_name": ""},
    "zakelijk": {"event_title": "Nieuwjaarsreceptie", "organization": "Internationale Handelsvereniging", "years": "100"},
    "kerst": {"family": "Familie Vandenbroucke-Hoogeveen", "members": "Wilhelmina-Charlotte, Maximiliaan en de kleine Alexander"},
}

owner, _ = User.objects.get_or_create(email="controle@vierlief.test")
owner.email_verified_at = timezone.now()
owner.save()
Invitation.objects.filter(owner=owner).delete()
out = {}
today = timezone.localdate()
for template in Template.objects.all():
    slug = template.slug
    # 1. Lange namen, veel programma, fotoformaten staand/liggend/panorama/vierkant.
    inv = create_draft(occasion="bruiloft", template=template, owner=owner)
    content = dict(inv.draft_content)
    hero = photo(inv, "duinen-staand")
    gallery = [photo(inv, "zee-horizon"), photo(inv, "duinen-ochtend", (2400, 800)), photo(inv, "kaarslicht"), photo(inv, "waterverf-lavendel")]
    content.update({
        "names": {"partner_1": "Maximiliaan-Alexander", "partner_2": "Anne-Wilhelmina Charlotte"},
        "date": (today + timedelta(days=200)).isoformat(), "start_time": "13:15", "end_time": "01:30", "timezone": "Europe/Amsterdam",
        "venue_name": "Kasteel Heerlijkheid van de Lange Laan en Omstreken (testlocatie)",
        "address": "Een hele lange straatnaam die maar doorgaat 123-bis\n9999 ZZ Plaatsnaam aan de Rivier",
        "welcome_text": "Dit is een testuitnodiging met bewust lange teksten.\n\nZo controleren we dat niets over de rand loopt, ook niet op een smalle telefoon van 360 pixels breed.",
        "story": {"title": "Ons verhaal", "text": "Een verhaal van meerdere alinea's.\n\nTweede alinea met nog wat meer tekst om de opmaak te testen."},
        "program": [{"time": f"{h:02d}:00", "title": f"Programmaonderdeel met een lange naam nummer {i + 1}", "description": "Met een toelichting die ook wat langer is."} for i, h in enumerate(range(13, 24))],
        "dresscode": {"text": "Feestelijk", "colors": ["#1E2320", "#C9A96E", "#F4EBDD", "#8A2E3E", "#5F6F5C", "#E9D5C9"]},
        "practical": [{"title": "Parkeren", "text": "Volg de borden."}, {"title": "Kinderen", "text": "Van harte welkom."}],
        "contact": {"name": "Ceremoniemeester met een heel lange naam", "phone": "+31 20 000 0000", "email": "een.heel.lang.adres@voorbeeld-domein.test", "note": ""},
        "closing_text": "Tot dan, we kijken ernaar uit!",
    })
    content["photos"] = {"hero": {"asset": hero, "x": 50, "y": 35, "zoom": 1.2},
                         "gallery": [{"asset": g, "x": 50, "y": 50, "zoom": 1, "caption": "Onderschrift"} for g in gallery]}
    content["sections"] = dict(content["sections"], story=True, gallery=True)
    content["rsvp"] = dict(content["rsvp"], deadline=(today + timedelta(days=150)).isoformat(), max_party_size=4,
                           questions=[vraag("liedje", formal=False)])
    inv = save_draft(inv, expected_rev=None, content=content, user=owner)
    inv = publish(inv, owner)
    out[f"{slug}:lang"] = inv.public_path

    # 2. Minimale gegevens: geen foto, geen optionele onderdelen.
    inv = create_draft(occasion="zakelijk" if template.supports("zakelijk") else "verjaardag", template=template, owner=owner)
    content = dict(inv.draft_content)
    if inv.occasion == "zakelijk":
        content["names"] = {"event_title": "Jaarafsluiting", "organization": "Testbedrijf"}
    else:
        content["names"] = {"person_name": "Kim", "age": ""}
    content.update({"date": (today + timedelta(days=40)).isoformat(), "start_time": "17:00", "venue_name": "Testlocatie", "address": ""})
    content["rsvp"] = dict(content["rsvp"], deadline=(today + timedelta(days=30)).isoformat(), max_party_size=1)
    inv = save_draft(inv, expected_rev=None, content=content, user=owner)
    inv = publish(inv, owner, package="essentieel")
    out[f"{slug}:minimaal"] = inv.public_path

    # 3. Verstreken evenement.
    inv = create_draft(occasion="jubileum", template=template, owner=owner)
    content = dict(inv.draft_content)
    content["names"] = {"honorees": "Ria & Kees", "years": "40"}
    content.update({"date": (today + timedelta(days=20)).isoformat(), "start_time": "15:00", "venue_name": "Zaal De Test", "address": "Plein 1\nTestdorp"})
    content["rsvp"] = dict(content["rsvp"], deadline=(today + timedelta(days=10)).isoformat())
    inv = save_draft(inv, expected_rev=None, content=content, user=owner)
    inv = publish(inv, owner, package="essentieel")
    GuestResponse.objects.create(invitation=inv, client_token="fixture-token-00001", name="Testgast", attending=True, party_size=2, edit_token_hash=os.urandom(16).hex() * 2)
    # Datum achteraf naar het verleden verplaatsen (als 'na afloop').
    content = dict(inv.draft_content, date=(today - timedelta(days=5)).isoformat())
    content["rsvp"] = dict(content["rsvp"], deadline=(today - timedelta(days=12)).isoformat())
    inv = save_draft(inv, expected_rev=None, content=content, user=owner)
    from invitations.services import publish_draft

    publish_draft(inv, user=owner, source="system", expected_rev=None)
    out[f"{slug}:verstreken"] = inv.public_path

    # 4. Lange woorden in de titel, voor de gelegenheid waarvoor het ontwerp is gemaakt.
    occasion = template.occasions[0] if template.occasions else "bruiloft"
    inv = create_draft(occasion=occasion, template=template, owner=owner)
    content = dict(inv.draft_content)
    content["names"] = LONG_WORDS[occasion]
    content.update({"date": (today + timedelta(days=60)).isoformat(), "start_time": "19:30", "venue_name": "Testlocatie", "address": ""})
    content["rsvp"] = dict(content["rsvp"], deadline=(today + timedelta(days=45)).isoformat(), max_party_size=2)
    inv = save_draft(inv, expected_rev=None, content=content, user=owner)
    inv = publish(inv, owner, package="essentieel")
    out[f"{slug}:woord"] = inv.public_path

    # 5. Kerst: alleen een kerstgroet, zonder datum, locatie of aanmelden (de afteller telt af naar kerst).
    if template.supports("kerst"):
        inv = create_draft(occasion="kerst", template=template, owner=owner)
        content = dict(inv.draft_content)
        content["names"] = {"family": "Familie Jansen", "members": "Eva, Tom en Noor"}
        content.update({"date": "", "start_time": "", "end_time": "", "venue_name": "", "address": "",
                        "welcome_text": "Lieve allemaal,\n\nwe wensen jullie warme kerstdagen en een gezond nieuwjaar!",
                        "closing_text": "Liefs, Eva, Tom en Noor"})
        content["sections"] = dict(content["sections"], rsvp=False)
        inv = save_draft(inv, expected_rev=None, content=content, user=owner)
        inv = publish(inv, owner, package="essentieel")
        out[f"{slug}:kerstgroet"] = inv.public_path

print(json.dumps(out, indent=2))

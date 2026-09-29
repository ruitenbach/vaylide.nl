"""Eigen gezichten: uploaden met toestemming, een voorbeeld laten maken (als taak), goedkeuren en verwijderen.

Regels:
- Alleen zichtbaar als de functie aan staat, de beeld-API is ingesteld, het ontwerp een bruidspaar heeft en er een
  actieve extra optie 'gezichten' met een prijs is (de eigenaar bepaalt die prijs).
- Een beperkt aantal pogingen per uitnodiging. Een poging telt zodra hij start; bij een fout aan onze of de API-kant
  komt hij terug. Elke poging is één taak met een unieke sleutel: herhalen maakt geen tweede generatie of kosten.
- Na betaling ligt het vast: geen nieuwe voorbeelden en geen andere goedkeuring meer. Gepubliceerd wordt precies de
  goedgekeurde afbeelding uit de bestelling; er wordt na het afrekenen nooit opnieuw gegenereerd.
"""
from __future__ import annotations

import io
import logging
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from PIL import Image

from catalog import paar
from catalog.models import AddOn
from invitations.images import UploadError, process_photo
from invitations.models import Invitation, MediaAsset
from processing.jobs import enqueue

from .models import FaceRequest
from .provider import FaceProviderError, configured, get_provider

log = logging.getLogger(__name__)

CONSENT_TEXT = (
    "Ik bevestig dat de personen op deze foto's toestemming geven om hun foto te uploaden en te laten bewerken tot een "
    "persoonlijke versie van het bruidspaar op deze uitnodiging, en dat ik die toestemming kan aantonen."
)
ALLOW_SINGLE = False  # Pas aanzetten als getest is dat de API één persoon betrouwbaar laat staan.


class FaceError(ValueError):
    """Begrijpelijke melding voor de klant."""


def feature_available(invitation: Invitation) -> bool:
    return bool(
        settings.FACES_ENABLED
        and configured()
        and paar.config(invitation.template_version)
        and AddOn.objects.filter(is_active=True, feature="gezichten").exists()
    )


def is_locked(invitation: Invitation) -> bool:
    from orders.services import invitation_is_paid

    return invitation_is_paid(invitation)


def get_request(invitation: Invitation) -> FaceRequest | None:
    return FaceRequest.objects.filter(invitation=invitation).first()


# ------------------------------------------------------------------ uploaden

def save_photos(invitation: Invitation, user, *, bride=None, groom=None, consent: bool) -> FaceRequest:
    if not consent:
        raise FaceError("Bevestig eerst dat de personen op de foto's toestemming geven.")
    if not bride and not groom:
        raise FaceError("Kies minstens één foto.")
    if is_locked(invitation):
        raise FaceError("Deze uitnodiging is al betaald; het bruidspaar ligt vast.")
    processed = {}
    for key, uploaded in (("photo_bride", bride), ("photo_groom", groom)):
        if not uploaded:
            continue
        if uploaded.size > settings.FACES_MAX_BYTES:
            raise FaceError("Deze foto is te groot. Het maximum is 10 MB.")
        try:
            processed[key] = process_photo(uploaded)  # controleert type, verwijdert EXIF (ook GPS), slaat opnieuw op
        except UploadError as exc:
            raise FaceError(str(exc)) from exc
    with transaction.atomic():
        req, _ = FaceRequest.objects.select_for_update().get_or_create(invitation=invitation, defaults={"created_by": user})
        for key, photo in processed.items():
            old = getattr(req, key)
            if old and old.name:
                old.storage.delete(old.name)
            getattr(req, key).save("foto.webp", photo.medium, save=False)
        req.consent_at = timezone.now()
        req.consent_text = CONSENT_TEXT
        if req.status == FaceRequest.Status.FAILED:
            req.status = FaceRequest.Status.NEW
            req.error = ""
        req.save()
    return req


# ------------------------------------------------------------------ een voorbeeld maken

@lru_cache(maxsize=4)
def _scene_bytes(renderer: str) -> bytes:
    """De scène voor de API: de zaal met het standaardpaar, in dezelfde verhouding als de kaart (941×1672)."""
    base = Path(settings.BASE_DIR) / "designs" / renderer / "img"
    with Image.open(base / "balzaal.webp") as zaal, Image.open(base / "paar-bruin-blond.webp") as koppel:
        scene = zaal.convert("RGBA")
        h = round(scene.height * .60)
        w = round(koppel.width * h / koppel.height)
        koppel = koppel.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
        scene.alpha_composite(koppel, ((scene.width - w) // 2, round(scene.height * (1 - .032)) - h))
        buffer = io.BytesIO()
        scene.convert("RGB").save(buffer, "PNG")
        return buffer.getvalue()


HAARKLEUREN = ("zwart", "bruin", "blond")


def _hair_choice(invitation: Invitation, hair: dict | None) -> tuple[str, str]:
    """Gekozen haarkleur (man, vrouw): uit het formulier, anders de bewaarde keuze, anders de standaard."""
    man, vrouw = paar.selection(invitation.template_version, invitation.draft_content)
    saved = ((invitation.draft_content.get("style") or {}).get("haar")) or {}
    hair = hair or {}
    man = hair.get("man") if hair.get("man") in HAARKLEUREN else (saved.get("man") if saved.get("man") in HAARKLEUREN else man)
    vrouw = hair.get("vrouw") if hair.get("vrouw") in HAARKLEUREN else (saved.get("vrouw") if saved.get("vrouw") in HAARKLEUREN else vrouw)
    return man, vrouw


def start_generation(invitation: Invitation, hair: dict | None = None) -> FaceRequest:
    if not feature_available(invitation):
        raise FaceError("Eigen gezichten zijn op dit moment niet beschikbaar.")
    if is_locked(invitation):
        raise FaceError("Deze uitnodiging is al betaald; het bruidspaar ligt vast.")
    with transaction.atomic():
        req = FaceRequest.objects.select_for_update().filter(invitation=invitation).first()
        if req is None or not req.consent_at:
            raise FaceError("Upload eerst de foto's en bevestig de toestemming.")
        if not (req.photo_bride and req.photo_groom) and not ALLOW_SINGLE:
            raise FaceError("Upload een foto van allebei. Met één foto kunnen we het resultaat nog niet goed genoeg garanderen.")
        if req.status == FaceRequest.Status.BUSY:
            return req
        if req.attempts_left <= 0:
            raise FaceError("Je hebt alle pogingen gebruikt. Neem contact met ons op als je nog een poging wilt.")
        req.hair_man, req.hair_woman = _hair_choice(invitation, hair)
        req.attempts_used += 1
        req.runs += 1
        req.status = FaceRequest.Status.BUSY
        req.error = ""
        req.save()
        run = req.runs
        job = enqueue("generate_faces", {"request_id": req.pk, "run": run}, unique_key=f"faces:{req.pk}:{run}",
                      invitation=invitation, max_attempts=2, run_inline=not settings.FACES_BACKGROUND)
        if settings.FACES_BACKGROUND:
            transaction.on_commit(lambda: _run_in_background(job.pk))
    return req


def _run_in_background(job_id: int) -> None:
    import threading

    from django.db import close_old_connections
    from processing.jobs import run_job

    def work():
        try:
            run_job(job_id)
        finally:
            close_old_connections()

    threading.Thread(target=work, name=f"gezichten-{job_id}", daemon=True).start()


def _read(field) -> bytes | None:
    if not field or not field.name:
        return None
    with field.open("rb") as fh:
        return fh.read()


def handle_generate(job) -> None:
    """Taak: één poging. Idempotent: een herhaalde taak voor dezelfde poging doet niets meer."""
    req = FaceRequest.objects.select_related("invitation__template_version").get(pk=job.payload["request_id"])
    run = int(job.payload["run"])
    if req.status != FaceRequest.Status.BUSY or req.result_attempt >= run or req.runs != run:
        return
    try:
        provider = get_provider()
        image = provider.generate(_scene_bytes(req.invitation.template_version.renderer), _read(req.photo_bride), _read(req.photo_groom),
                                  hair={"man": req.hair_man, "vrouw": req.hair_woman})
    except FaceProviderError as exc:
        final = not exc.retryable or job.attempts + 1 >= job.max_attempts
        if not final:
            raise  # de takenwachtrij probeert het later nog één keer
        _fail(req, str(exc))
        return
    try:
        with Image.open(io.BytesIO(image)) as img:
            img = img.convert("RGB")
            img.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
            buffer = io.BytesIO()
            img.save(buffer, "WEBP", quality=90)
    except (OSError, ValueError):
        _fail(req, "Er kwam geen bruikbaar voorbeeld terug. Probeer het opnieuw.")
        return
    with transaction.atomic():
        req = FaceRequest.objects.select_for_update().get(pk=req.pk)
        if req.result and req.result.name:
            req.result.storage.delete(req.result.name)
        req.result.save("voorbeeld.webp", ContentFile(buffer.getvalue()), save=False)
        req.result_attempt = run
        req.status = FaceRequest.Status.READY
        req.provider = provider.code
        req.model_name = getattr(provider, "model", "")[:60]
        req.save()


def _fail(req: FaceRequest, message: str) -> None:
    with transaction.atomic():
        req = FaceRequest.objects.select_for_update().get(pk=req.pk)
        req.status = FaceRequest.Status.FAILED
        req.error = message[:300]
        # Mislukt aan onze of de API-kant: de poging telt niet mee.
        req.attempts_used = max(0, req.attempts_used - 1)
        req.save()


# ------------------------------------------------------------------ goedkeuren en verwijderen

def approve(invitation: Invitation, user) -> FaceRequest:
    from invitations.services import save_draft

    if is_locked(invitation):
        raise FaceError("Deze uitnodiging is al betaald; het bruidspaar ligt vast.")
    req = get_request(invitation)
    if req is None or req.status != FaceRequest.Status.READY or not req.result:
        raise FaceError("Er is nog geen voorbeeld om goed te keuren.")
    with req.result.open("rb") as fh:
        data = fh.read()
    buffer = io.BytesIO(data)
    buffer.name = "eigen-paar.webp"
    buffer.size = len(data)
    photo = process_photo(buffer)
    asset = MediaAsset(invitation=invitation, kind=MediaAsset.Kind.SCENE, original_name="eigen bruidspaar", content_type="image/webp",
                       size_bytes=photo.size_bytes, width=photo.width, height=photo.height, uploaded_by=user)
    asset.file.save("groot.webp", photo.large, save=False)
    asset.file_medium.save("middel.webp", photo.medium, save=False)
    asset.file_thumb.save("klein.webp", photo.thumb, save=False)
    asset.save()
    content = dict(invitation.draft_content)
    old = (content.get("style") or {}).get("paar_eigen")
    # De haarkleur van het goedgekeurde beeld wordt ook de bewaarde keuze: keuze en beeld horen altijd samen.
    haar = {"man": req.hair_man, "vrouw": req.hair_woman} if req.hair_man and req.hair_woman else (content.get("style") or {}).get("haar")
    content["style"] = dict(content.get("style") or {}, paar_eigen=str(asset.uid), haar=haar)
    save_draft(invitation, expected_rev=invitation.draft_rev, content=content, user=user)
    _delete_unused_scene(invitation, old)
    req.approved_asset = asset
    req.status = FaceRequest.Status.APPROVED
    req.save(update_fields=["approved_asset", "status", "updated_at"])
    return req


def _delete_unused_scene(invitation: Invitation, uid) -> None:
    """Een oude eigen versie weg, tenzij de gepubliceerde uitnodiging hem nog gebruikt."""
    from invitations.content import referenced_assets

    if not uid:
        return
    published = invitation.published_version.content if invitation.published_version_id else {}
    if str(uid) in referenced_assets(published):
        return
    for asset in MediaAsset.objects.filter(invitation=invitation, kind=MediaAsset.Kind.SCENE, uid=uid):
        asset.delete()


def remove(invitation: Invitation, user) -> None:
    """Verwijdert de foto's en voorbeelden. Is het nog niet betaald, dan ook de eigen versie op de kaart."""
    from invitations.services import save_draft

    req = get_request(invitation)
    if req is not None:
        req.delete_files()
        if not is_locked(invitation):
            content = dict(invitation.draft_content)
            old = (content.get("style") or {}).get("paar_eigen")
            if old:
                content["style"] = dict(content.get("style") or {}, paar_eigen="")
                save_draft(invitation, expected_rev=invitation.draft_rev, content=content, user=user)
                _delete_unused_scene(invitation, old)
            req.delete()
        else:
            req.consent_at = None
            req.save()

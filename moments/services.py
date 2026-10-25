"""Regels van Moments: tokens, plafonds en wat wie mag zien. Alles hier is serverzijdig en zonder weergave."""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import timedelta

from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.utils import timezone

from core.utils import new_token, rate_limit, token_digest

from . import limits, photos
from .flags import moments_enabled
from .models import Album, GuestToken, Submission
from .storage import new_key


class SubmissionRefused(Exception):
    """Een inzending mag niet. `code` is een korte vaste aanduiding; de tekst voor de gast bepaalt een latere stap."""

    def __init__(self, code: str, retry_after: int | None = None):
        super().__init__(code)
        self.code = code
        self.retry_after = retry_after


def albums_for_user(user):
    """Alleen de albums bij uitnodigingen van deze klant."""
    if not getattr(user, "is_authenticated", False):
        return Album.objects.none()
    return Album.objects.filter(invitation__owner=user)


def issue_token(album: Album, label: str = "", expires_at=None) -> tuple[GuestToken, str]:
    """Maakt een gasttoken. De leesbare token wordt alleen hier teruggegeven en niet bewaard."""
    raw = new_token(24)
    token = GuestToken.objects.create(album=album, token_hash=token_digest(raw), label=label[:120], expires_at=expires_at)
    return token, raw


def resolve_token(raw: str) -> GuestToken | None:
    """Zoekt de actieve gasttoken bij een ontvangen waarde. Geeft None bij vlag uit, onbekend, ingetrokken of verlopen."""
    if not moments_enabled() or not raw or len(raw) > 128:
        return None
    token = GuestToken.objects.select_related("album").filter(token_hash=token_digest(raw)).first()
    if token is None or not token.is_active():
        return None
    return token


def revoke_token(token: GuestToken) -> None:
    if token.revoked_at is None:
        token.revoked_at = timezone.now()
        token.save(update_fields=["revoked_at"])


def _counted(qs, now=None):
    """Wat meetelt tegen een plafond: niet afgewezen, verwijderd of mislukt, en geen verlopen reservering."""
    now = now or timezone.now()
    qs = qs.exclude(status__in=[Submission.Status.REJECTED, Submission.Status.REMOVED, Submission.Status.FAILED])
    return qs.exclude(status=Submission.Status.UPLOADING, reservation_expires_at__lte=now)


def create_submission(token: GuestToken, *, kind: str = Submission.Kind.PHOTO, caption: str = "", content_type: str = "", size_bytes: int = 0) -> Submission:
    """Legt een inzending vast, na controle van vlag, token, album en de plafonds per gast en per evenement."""
    if not moments_enabled():
        raise SubmissionRefused("uit")
    with transaction.atomic():
        # Het album vergrendelen zodat twee gelijktijdige inzendingen het plafond niet samen overschrijden.
        album = Album.objects.select_for_update().get(pk=token.album_id)
        token = GuestToken.objects.get(pk=token.pk, album=album)
        if not token.is_active():
            raise SubmissionRefused("token")
        if not album.accepts_submissions():
            raise SubmissionRefused("album_dicht")
        if _counted(Submission.objects.filter(album=album)).count() >= album.album_limit:
            raise SubmissionRefused("plafond_album")
        if _counted(Submission.objects.filter(guest_token=token)).count() >= album.guest_limit:
            raise SubmissionRefused("plafond_gast")
        return Submission.objects.create(
            album=album, guest_token=token, kind=kind, caption=caption[:200], content_type=content_type[:60], size_bytes=max(0, size_bytes)
        )


def submissions_visible_to_guest(token: GuestToken):
    """Een gast ziet alleen zijn of haar eigen inzendingen, nooit die van andere gasten."""
    if not token.is_active():
        return Submission.objects.none()
    return Submission.objects.filter(guest_token=token, album=token.album).exclude(status=Submission.Status.REMOVED)


# ======================================================================================
# Stap 3A: gastsessie, uploadreservering, controle en verwerking van foto's.
# Alles hier is serverzijdig. Geen koppeling met bestellingen, Mollie of `processing/`.
# ======================================================================================

def rotate_public_code(album: Album) -> str:
    """Nieuwe publieke code (bijvoorbeeld na lekken van de QR). Bestaande gastsessies blijven werken."""
    album.public_code = secrets.token_urlsafe(10)
    album.save(update_fields=["public_code", "updated_at"])
    return album.public_code


def take_signup_slot(album_id: int, now=None) -> None:
    """Emmer voor nieuwe sessies per album (60 vooraf, 30 per minuut erbij). Bewust op het album, niet op het netwerk:
    een zaal-wifi deelt één adres. Een lege emmer geeft 'even geduld', nooit een blokkade. Aanroepen binnen een transactie op het album."""
    now = now or timezone.now()
    album = Album.objects.select_for_update().get(pk=album_id)
    tokens = album.signup_tokens
    if album.signup_refilled_at:
        minutes = (now - album.signup_refilled_at).total_seconds() / 60
        tokens = min(float(limits.SIGNUP_BUCKET_CAPACITY), tokens + max(0.0, minutes) * limits.SIGNUP_BUCKET_REFILL_PER_MIN)
    if tokens < 1:
        wait = int(max(1, (1 - tokens) / limits.SIGNUP_BUCKET_REFILL_PER_MIN * 60)) + 1
        raise SubmissionRefused("even_wachten", retry_after=wait)
    album.signup_tokens = tokens - 1
    album.signup_refilled_at = now
    album.save(update_fields=["signup_tokens", "signup_refilled_at"])


def start_guest_session(public_code: str, *, network_hash: str = "", existing: GuestToken | None = None) -> tuple[GuestToken, str | None]:
    """Maakt een gastsessie bij de publieke code. Heeft de bezoeker al een geldige sessie voor dit album, dan komt er geen nieuwe identiteit bij.
    Geeft (token, leesbare token); de leesbare token is None bij een bestaande sessie en wordt nooit bewaard."""
    if not moments_enabled():
        raise SubmissionRefused("uit")
    code = (public_code or "")[:24]
    album = Album.objects.filter(public_code=code).first() if code else None
    if album is None:
        raise SubmissionRefused("onbekend")
    if existing is not None and existing.album_id == album.pk and existing.is_active():
        return existing, None
    with transaction.atomic():
        album = Album.objects.select_for_update().get(pk=album.pk)
        if not album.accepting_new_guests:
            raise SubmissionRefused("geen_nieuwe_gasten")
        if not album.accepts_submissions():
            raise SubmissionRefused("album_dicht")
        take_signup_slot(album.pk)
        expires = album.closes_at + timedelta(days=30 * limits.RETENTION_MONTHS) if album.closes_at else None
        raw = new_token(24)
        token = GuestToken.objects.create(album=album, token_hash=token_digest(raw), expires_at=expires, network_hash=network_hash[:64], last_seen_at=timezone.now())
    return token, raw


def _active_guest_count(album: Album, now) -> int:
    live = Q(submissions__status=Submission.Status.UPLOADING, submissions__reservation_expires_at__gt=now)
    return GuestToken.objects.filter(album=album, revoked_at__isnull=True).filter(Q(first_upload_at__isnull=False) | live).distinct().count()


def _reserved_or_stored_bytes(album: Album, now) -> int:
    live = _counted(Submission.objects.filter(album=album), now)
    stored = live.exclude(status=Submission.Status.UPLOADING).aggregate(t=Sum("size_bytes"))["t"] or 0
    reserved = live.filter(status=Submission.Status.UPLOADING).aggregate(t=Sum("reserved_bytes"))["t"] or 0
    return stored + reserved


def reserve_photo_upload(token: GuestToken, *, client_id, content_type: str, size_bytes: int, storage) -> tuple[Submission, dict | None]:
    """Reserveert een plek vóór het uploaden. Weigeren gebeurt dus vooraf, onder albumvergrendeling, niet na het uploaden.
    Hetzelfde `client_id` geeft dezelfde reservering terug (dubbel verzoek of herhaalde poging) en telt niet dubbel.
    Geeft (inzending, uploaddoel); het doel is None als de reservering al afgehandeld is."""
    if not moments_enabled():
        raise SubmissionRefused("uit")
    try:
        client_id = uuid.UUID(str(client_id))
    except (ValueError, TypeError, AttributeError):
        raise SubmissionRefused("ongeldig")
    ext = limits.PHOTO_TYPES.get((content_type or "").lower())
    if ext is None:
        raise SubmissionRefused("type")
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < limits.PHOTO_MIN_BYTES:
        raise SubmissionRefused("te_klein")
    if size_bytes > limits.PHOTO_MAX_INPUT_BYTES:
        raise SubmissionRefused("te_groot")
    now = timezone.now()
    with transaction.atomic():
        album = Album.objects.select_for_update().get(pk=token.album_id)
        token = GuestToken.objects.get(pk=token.pk, album=album)
        if not token.is_active(now):
            raise SubmissionRefused("token")
        existing = Submission.objects.filter(guest_token=token, client_id=client_id).first()
        if existing is not None:
            target = None
            if existing.status == Submission.Status.UPLOADING and existing.reservation_expires_at and existing.reservation_expires_at > now:
                target = storage.upload_target(existing.original_key, existing.content_type, limits.PHOTO_MAX_INPUT_BYTES, _seconds_left(existing, now))
            return existing, target
        if not album.accepts_submissions(now):
            raise SubmissionRefused("album_dicht")
        if not rate_limit(f"moments-start:{token.pk}", limits.MAX_STARTS_PER_10_MIN, 600):
            raise SubmissionRefused("tempo", retry_after=60)
        own = _counted(Submission.objects.filter(guest_token=token), now)
        if own.filter(status=Submission.Status.UPLOADING).count() >= limits.MAX_CONCURRENT_UPLOADS:
            raise SubmissionRefused("tempo", retry_after=15)
        if own.filter(kind=Submission.Kind.PHOTO).count() >= album.guest_limit:
            raise SubmissionRefused("plafond_gast")
        if _counted(Submission.objects.filter(album=album), now).filter(kind=Submission.Kind.PHOTO).count() >= album.album_limit:
            raise SubmissionRefused("plafond_album")
        if _reserved_or_stored_bytes(album, now) + limits.PHOTO_MAX_STORED_BYTES > album.bytes_cap:
            raise SubmissionRefused("plafond_album")
        if token.first_upload_at is None and not own.exists() and _active_guest_count(album, now) >= album.guest_cap:
            raise SubmissionRefused("max_gasten")
        key = new_key(album.uid, "orig", ext)
        try:
            with transaction.atomic():
                sub = Submission.objects.create(
                    album=album, guest_token=token, kind=Submission.Kind.PHOTO, status=Submission.Status.UPLOADING, client_id=client_id,
                    content_type=content_type.lower(), size_bytes=size_bytes, reserved_bytes=limits.PHOTO_MAX_STORED_BYTES, original_key=key,
                    reservation_expires_at=now + timedelta(minutes=limits.RESERVATION_MINUTES),
                )
        except IntegrityError:  # twee gelijktijdige verzoeken met hetzelfde client_id: de tweede krijgt de eerste
            raise SubmissionRefused("tempo", retry_after=1)
        GuestToken.objects.filter(pk=token.pk).update(last_seen_at=now)
    return sub, storage.upload_target(key, sub.content_type, limits.PHOTO_MAX_INPUT_BYTES, limits.RESERVATION_MINUTES * 60)


def _seconds_left(sub: Submission, now) -> int:
    return max(60, int((sub.reservation_expires_at - now).total_seconds()))


def _discard(storage, *keys) -> None:
    for key in keys:
        if key:
            try:
                storage.delete(key)
            except Exception:  # opruimen mag nooit de afhandeling breken; het nachtelijke opruimen vangt restanten op
                pass


def _fail(sub: Submission, code: str, storage) -> Submission:
    sub.status = Submission.Status.FAILED
    sub.failure_code = code
    sub.reserved_bytes = 0
    sub.completed_at = timezone.now()
    sub.save(update_fields=["status", "failure_code", "reserved_bytes", "completed_at"])
    _discard(storage, sub.original_key)
    return sub


def complete_photo_upload(token: GuestToken, submission_uid, storage) -> Submission | None:
    """De gast meldt dat het uploaden klaar is. De server controleert zelf het object: grootte, echt type, leesbaarheid, afmetingen en dubbele inhoud.
    Een tweede melding verandert niets (geen dubbele verwerking). Geeft None als de inzending niet van deze gast is."""
    if not moments_enabled():
        raise SubmissionRefused("uit")
    now = timezone.now()
    with transaction.atomic():
        sub = Submission.objects.select_for_update().filter(uid=submission_uid, guest_token=token, album=token.album).first()
        if sub is None:
            return None
        if sub.status != Submission.Status.UPLOADING:
            return sub
        if not token.is_active(now):
            raise SubmissionRefused("token")
        if sub.reservation_expires_at and sub.reservation_expires_at <= now:
            return _fail(sub, "verlopen", storage)
        size = storage.size(sub.original_key)
        if size is None:
            raise SubmissionRefused("nog_niet_ontvangen")
        if size < limits.PHOTO_MIN_BYTES:
            return _fail(sub, "te_klein", storage)
        if size > limits.PHOTO_MAX_INPUT_BYTES:
            return _fail(sub, "te_groot", storage)
        data = storage.read(sub.original_key, limits.PHOTO_MAX_INPUT_BYTES + 1)
        if len(data) != size:
            return _fail(sub, "onleesbaar", storage)
        try:
            photos.inspect(data, sub.content_type)
        except photos.PhotoRejected as exc:
            return _fail(sub, exc.code, storage)
        digest = hashlib.sha256(data).hexdigest()
        if _counted(Submission.objects.filter(guest_token=token, sha256=digest), now).exclude(pk=sub.pk).exists():
            return _fail(sub, "dubbel", storage)
        sub.status = Submission.Status.RECEIVED
        sub.size_bytes = size
        sub.sha256 = digest
        sub.completed_at = now
        sub.save(update_fields=["status", "size_bytes", "sha256", "completed_at"])
        GuestToken.objects.filter(pk=token.pk, first_upload_at__isnull=True).update(first_upload_at=now)
        return sub


def process_next_photo(storage, now=None) -> Submission | None:
    """Verwerkt één ontvangen foto tot albummaster. Eigen wachtrij (de tabel zelf), los van `processing/`. Veilig om tegelijk uit te voeren."""
    now = now or timezone.now()
    reset_stale_processing(now)
    with transaction.atomic():
        sub = Submission.objects.select_for_update(skip_locked=True).filter(status=Submission.Status.RECEIVED, kind=Submission.Kind.PHOTO).order_by("completed_at", "pk").first()
        if sub is None:
            return None
        sub.status = Submission.Status.PROCESSING
        sub.attempts += 1
        sub.processing_started_at = now
        sub.save(update_fields=["status", "attempts", "processing_started_at"])
    master_key = ""
    try:
        data = storage.read(sub.original_key, limits.PHOTO_MAX_INPUT_BYTES + 1)
        master = photos.make_master(data)
        master_key = new_key(sub.album.uid, "master", "jpg")
        storage.write(master_key, master)
    except photos.PhotoRejected as exc:
        return _fail(Submission.objects.get(pk=sub.pk), exc.code, storage)
    except Exception:  # noqa: BLE001 - tijdelijke storing van opslag of geheugen: opnieuw proberen, daarna mislukt
        _discard(storage, master_key)
        sub = Submission.objects.get(pk=sub.pk)
        if sub.attempts >= limits.PROCESS_MAX_ATTEMPTS:
            return _fail(sub, "verwerking", storage)
        sub.status = Submission.Status.RECEIVED
        sub.save(update_fields=["status"])
        return sub
    with transaction.atomic():
        sub = Submission.objects.select_for_update().get(pk=sub.pk)
        if sub.status != Submission.Status.PROCESSING:  # iemand anders was ons voor: onze kopie weg
            _discard(storage, master_key)
            return sub
        old = sub.original_key
        sub.status = Submission.Status.READY
        sub.storage_key = master_key
        sub.original_key = ""
        sub.content_type = "image/jpeg"
        sub.size_bytes = len(master)
        sub.reserved_bytes = 0
        sub.save(update_fields=["status", "storage_key", "original_key", "content_type", "size_bytes", "reserved_bytes"])
    _discard(storage, old)
    return sub


def reset_stale_processing(now=None) -> int:
    """Een verwerking die blijft hangen (proces gestopt) gaat terug in de wachtrij, of faalt na drie pogingen."""
    now = now or timezone.now()
    stale = Submission.objects.filter(status=Submission.Status.PROCESSING, processing_started_at__lt=now - timedelta(minutes=limits.PROCESS_STALE_MINUTES))
    n = stale.filter(attempts__lt=limits.PROCESS_MAX_ATTEMPTS).update(status=Submission.Status.RECEIVED)
    stale.filter(attempts__gte=limits.PROCESS_MAX_ATTEMPTS).update(status=Submission.Status.FAILED, failure_code="verwerking", reserved_bytes=0)
    return n


def expire_reservations(storage, now=None) -> int:
    """Verlopen reserveringen komen vrij (aantal en bytes) en het halve bestand verdwijnt. Het tellen negeert ze sowieso al."""
    now = now or timezone.now()
    count = 0
    for sub in Submission.objects.filter(status=Submission.Status.UPLOADING, reservation_expires_at__lte=now):
        with transaction.atomic():
            sub = Submission.objects.select_for_update().get(pk=sub.pk)
            if sub.status == Submission.Status.UPLOADING:
                _fail(sub, "verlopen", storage)
                count += 1
    return count


def cleanup_orphans(storage, now=None, older_than_hours: int = 24) -> int:
    """Objecten zonder databaseregel die ouder zijn dan 24 uur worden verwijderd (afgebroken uploads, mislukte verwerking)."""
    now = now or timezone.now()
    cutoff = now.timestamp() - older_than_hours * 3600
    known = set(Submission.objects.exclude(storage_key="").values_list("storage_key", flat=True)) | set(
        Submission.objects.exclude(original_key="").values_list("original_key", flat=True)
    )
    removed = 0
    for key, mtime in list(storage.keys("moments/")):
        if key not in known and mtime < cutoff:
            storage.delete(key)
            removed += 1
    return removed


def purge_network_hashes(now=None) -> int:
    now = now or timezone.now()
    return GuestToken.objects.exclude(network_hash="").filter(created_at__lt=now - timedelta(days=limits.NETWORK_HASH_RETENTION_DAYS)).update(network_hash="")


def guest_submission(token: GuestToken, uid) -> Submission | None:
    """Alleen een eigen inzending; die van een andere gast of een ander album bestaat voor deze gast niet."""
    return submissions_visible_to_guest(token).filter(uid=uid).first()

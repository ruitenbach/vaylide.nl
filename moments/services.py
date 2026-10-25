"""Regels van Moments: tokens, plafonds en wat wie mag zien. Alles hier is serverzijdig en zonder weergave."""
from __future__ import annotations

from django.db import transaction
from django.utils import timezone

from core.utils import new_token, token_digest

from .flags import moments_enabled
from .models import Album, GuestToken, Submission


class SubmissionRefused(Exception):
    """Een inzending mag niet. `code` is een korte vaste aanduiding; de tekst voor de gast bepaalt een latere stap."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


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


def _counted(qs):
    return qs.exclude(status__in=[Submission.Status.REJECTED, Submission.Status.REMOVED])


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

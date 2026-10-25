"""Moments: gasten delen foto's en video's van een evenement in een album bij een uitnodiging.

Stap 1 (technische basis): alleen het datamodel en de regels eromheen. Er zijn nog geen uploads, betalingen of
videoverwerking. Bestanden staan, zodra ze er zijn, in een eigen, niet-openbare map (zie `private_path`).
Taal en valuta staan al per album vastgelegd, zodat meertaligheid en andere valuta's later geen ombouw vragen.
"""
from __future__ import annotations

import secrets
import uuid

from django.db import models
from django.utils import timezone

from . import limits


def private_path(instance, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    ext = "".join(ch for ch in ext if ch.isalnum())[:5] or "bin"
    return f"moments/{instance.album.uid}/{secrets.token_hex(16)}.{ext}"


class Album(models.Model):
    """Het album van één evenement, gekoppeld aan één uitnodiging (en dus aan de klant die die uitnodiging bezit)."""

    class Status(models.TextChoices):
        DRAFT = "concept", "Concept"
        OPEN = "open", "Open voor inzendingen"
        CLOSED = "gesloten", "Gesloten"
        ARCHIVED = "gearchiveerd", "Gearchiveerd"

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invitation = models.OneToOneField("invitations.Invitation", on_delete=models.CASCADE, related_name="moments_album")
    title = models.CharField("titel", max_length=120, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    opens_at = models.DateTimeField(null=True, blank=True)
    closes_at = models.DateTimeField(null=True, blank=True)
    # Plafonds. Leeg = standaardwaarde uit moments/limits.py; een ingestelde waarde wordt nooit boven het harde plafond gebruikt.
    max_per_guest = models.PositiveSmallIntegerField(null=True, blank=True)
    max_per_album = models.PositiveIntegerField(null=True, blank=True)
    # Gasttoegang. De publieke code staat in de QR: geheim is hij niet, hij geeft alleen de kans een gast te worden.
    public_code = models.CharField(max_length=24, unique=True, null=True, blank=True, editable=False)
    max_guests = models.PositiveSmallIntegerField(null=True, blank=True)
    accepting_new_guests = models.BooleanField(default=True)
    # Emmer voor nieuwe gastsessies op albumniveau (zie services.take_signup_slot).
    signup_tokens = models.FloatField(default=limits.SIGNUP_BUCKET_CAPACITY)
    signup_refilled_at = models.DateTimeField(null=True, blank=True)
    # Voorbereid voor later, nog zonder werking.
    language = models.CharField(max_length=8, default="nl")
    currency = models.CharField(max_length=3, default="EUR")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "album"
        verbose_name_plural = "albums"

    def __str__(self) -> str:
        return self.title or f"Album van {self.invitation}"

    def save(self, *args, **kwargs):
        if not self.public_code:
            self.public_code = secrets.token_urlsafe(10)  # 80 bit: onraadbaar, en roteerbaar via services.rotate_public_code
        super().save(*args, **kwargs)

    @property
    def guest_limit(self) -> int:
        return min(self.max_per_guest or limits.DEFAULT_MAX_PER_GUEST, limits.HARD_MAX_PER_GUEST)

    @property
    def album_limit(self) -> int:
        return min(self.max_per_album or limits.DEFAULT_MAX_PER_ALBUM, limits.HARD_MAX_PER_ALBUM)

    @property
    def guest_cap(self) -> int:
        return min(self.max_guests or limits.DEFAULT_MAX_GUESTS, limits.HARD_MAX_GUESTS)

    @property
    def bytes_cap(self) -> int:
        """Afgeleid van de aantallen: alle toegestane foto's op de maximale bewaarde omvang. Een vangnet, nooit een tweede regel."""
        return self.album_limit * limits.PHOTO_MAX_STORED_BYTES

    def accepts_submissions(self, now=None) -> bool:
        now = now or timezone.now()
        if self.status != self.Status.OPEN:
            return False
        if self.opens_at and now < self.opens_at:
            return False
        if self.closes_at and now >= self.closes_at:
            return False
        return True


class GuestToken(models.Model):
    """Persoonlijke toegang van een gast tot het album. Alleen een afgeleide waarde (hash) wordt bewaard, nooit de token zelf."""

    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="tokens")
    token_hash = models.CharField(max_length=64, unique=True)
    label = models.CharField("naam of omschrijving", max_length=120, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    # Pas gevuld bij de eerste echte upload: dan telt de gast mee als actieve gast.
    first_upload_at = models.DateTimeField(null=True, blank=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    # Alleen een gehashte netwerkvingerafdruk, hooguit 30 dagen bewaard, alleen voor misbruikonderzoek.
    network_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        verbose_name = "gasttoken"
        verbose_name_plural = "gasttokens"

    def __str__(self) -> str:
        return self.label or f"Gast {self.pk}"

    def is_active(self, now=None) -> bool:
        now = now or timezone.now()
        if self.revoked_at:
            return False
        return not (self.expires_at and now >= self.expires_at)


class Submission(models.Model):
    """Een inzending (foto of video) van een gast. Stap 3A voegt de uploadreservering toe (zie services.reserve_photo_upload)."""

    class Kind(models.TextChoices):
        PHOTO = "foto", "Foto"
        VIDEO = "video", "Video"

    class Status(models.TextChoices):
        UPLOADING = "uploaden", "Wordt geüpload"
        RECEIVED = "ontvangen", "Ontvangen"
        PROCESSING = "verwerken", "Wordt verwerkt"
        READY = "klaar", "Klaar"
        FAILED = "mislukt", "Mislukt"
        APPROVED = "goedgekeurd", "Goedgekeurd"
        REJECTED = "afgewezen", "Afgewezen"
        REMOVED = "verwijderd", "Verwijderd"

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name="submissions")
    guest_token = models.ForeignKey(GuestToken, on_delete=models.CASCADE, related_name="submissions")
    kind = models.CharField(max_length=5, choices=Kind.choices, default=Kind.PHOTO)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RECEIVED)
    file = models.FileField(upload_to=private_path, max_length=255, blank=True)
    content_type = models.CharField(max_length=60, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    caption = models.CharField("bijschrift", max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Uploadreservering (stap 3A). `client_id` maakt een herhaald verzoek onschadelijk.
    client_id = models.UUIDField(null=True, blank=True)
    storage_key = models.CharField(max_length=200, blank=True)
    original_key = models.CharField(max_length=200, blank=True)
    reserved_bytes = models.PositiveBigIntegerField(default=0)
    reservation_expires_at = models.DateTimeField(null=True, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    failure_code = models.CharField(max_length=30, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    processing_started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "inzending"
        verbose_name_plural = "inzendingen"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["album", "status"]), models.Index(fields=["guest_token", "status"])]
        constraints = [
            models.UniqueConstraint(fields=["guest_token", "client_id"], condition=models.Q(client_id__isnull=False), name="moments_uniek_client_id"),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.uid}"

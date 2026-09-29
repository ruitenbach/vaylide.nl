"""Uitnodigingen, versies, uploads en gastaanmeldingen.

Klantinhoud (`draft_content` en versies) staat los van de ontwerpbestanden.
Iedere uitnodiging verwijst naar een vaste ontwerpversie, zodat een nieuwe
ontwerpversie bestaande uitnodigingen niet onverwacht verandert.
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from catalog.occasions import OCCASION_CHOICES


class Source(models.TextChoices):
    CUSTOMER = "customer", "Klant"
    ADMIN = "admin", "VAYLIDE-team"
    SYSTEM = "system", "Systeem"
    RESTORE = "restore", "Hersteld"


class Invitation(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Concept"
        PAID = "paid", "Betaald, wordt verwerkt"
        LIVE = "live", "Online"
        OFFLINE = "offline", "Offline gehaald"
        EXPIRED = "expired", "Verlopen"

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="klant",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="invitations",
    )
    occasion = models.CharField("gelegenheid", max_length=20, choices=OCCASION_CHOICES)
    template_version = models.ForeignKey(
        "catalog.TemplateVersion", verbose_name="ontwerpversie (concept)", on_delete=models.PROTECT, related_name="+"
    )
    title = models.CharField("titel", max_length=200, blank=True)
    slug = models.SlugField("link", max_length=90, unique=True, null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)

    draft_content = models.JSONField(default=dict)
    draft_overrides = models.JSONField(default=dict, blank=True)
    draft_rev = models.PositiveIntegerField(default=1)
    draft_updated_at = models.DateTimeField(default=timezone.now)
    draft_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    draft_updated_source = models.CharField(max_length=12, choices=Source.choices, default=Source.CUSTOMER)
    draft_base_version = models.ForeignKey(
        "InvitationVersion", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    published_version = models.ForeignKey(
        "InvitationVersion", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    first_published_at = models.DateTimeField(null=True, blank=True)
    last_published_at = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField("online tot", null=True, blank=True)

    # Het pakket dat de klant bij de start koos (te wijzigen bij Bestellen); de rechten volgen pas na betaling.
    package_code = models.CharField("gekozen pakket", max_length=40, blank=True)

    # Rechten na betaling (uit pakket en extra opties).
    features = models.JSONField(default=list, blank=True)
    max_gallery_photos = models.PositiveSmallIntegerField(default=0)

    customer_locked = models.BooleanField("klant mag tijdelijk niet wijzigen", default=False)
    lock_reason = models.CharField("reden", max_length=200, blank=True)
    wizard_step = models.CharField(max_length=30, blank=True)

    # Afgeleid van de gepubliceerde versie (voor controles en overzichten).
    event_start = models.DateTimeField(null=True, blank=True)
    rsvp_deadline = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "uitnodiging"
        verbose_name_plural = "uitnodigingen"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title or f"Uitnodiging {str(self.uid)[:8]}"

    @property
    def public_path(self) -> str:
        return f"/u/{self.slug}/" if self.slug else ""

    @property
    def public_url(self) -> str:
        return f"{settings.BASE_URL}{self.public_path}" if self.slug else ""

    @property
    def is_published(self) -> bool:
        return self.published_version_id is not None

    @property
    def is_publicly_visible(self) -> bool:
        if self.status != self.Status.LIVE or not self.published_version_id:
            return False
        return self.available_until is None or self.available_until > timezone.now()

    @property
    def has_unpublished_changes(self) -> bool:
        if not self.published_version_id:
            return False
        pv = self.published_version
        return (
            pv.content != self.draft_content
            or pv.overrides != self.draft_overrides
            or pv.template_version_id != self.template_version_id
        )

    def has_feature(self, key: str) -> bool:
        return key in (self.features or [])


class InvitationVersion(models.Model):
    """Onveranderlijke momentopname van de inhoud (bij publiceren, herstellen of bestellen)."""

    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField()
    content = models.JSONField()
    overrides = models.JSONField(default=dict, blank=True)
    template_version = models.ForeignKey("catalog.TemplateVersion", on_delete=models.PROTECT, related_name="+")
    source = models.CharField(max_length=12, choices=Source.choices)
    note = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "versie"
        verbose_name_plural = "versies"
        ordering = ["-number"]
        constraints = [
            models.UniqueConstraint(fields=["invitation", "number"], name="uniq_invitation_version")
        ]

    def __str__(self) -> str:
        return f"Versie {self.number}"


def asset_upload_path(instance: "MediaAsset", filename: str) -> str:
    return f"uitnodigingen/{instance.invitation.uid}/{instance.uid}/{filename}"


class MediaAsset(models.Model):
    class Kind(models.TextChoices):
        PHOTO = "photo", "Foto"
        AUDIO = "audio", "Muziek"
        SCENE = "scene", "Eigen bruidspaar"  # goedgekeurde afbeelding uit gezichten/ (niet bij de foto's)
        LOGO = "logo", "Logo op het zegel"  # eigen (bedrijfs)logo op het lakzegel, met doorzichtigheid

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE, related_name="assets")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    file = models.FileField(upload_to=asset_upload_path, max_length=255)
    file_medium = models.FileField(upload_to=asset_upload_path, max_length=255, blank=True)
    file_thumb = models.FileField(upload_to=asset_upload_path, max_length=255, blank=True)
    original_name = models.CharField(max_length=200, blank=True)
    content_type = models.CharField(max_length=60)
    size_bytes = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    # Automatisch uitlijnen (invitations/focus.py): middelpunt in procenten en het aantal gevonden gezichten.
    focus_x = models.PositiveSmallIntegerField(null=True, blank=True)
    focus_y = models.PositiveSmallIntegerField(null=True, blank=True)
    faces = models.PositiveSmallIntegerField(null=True, blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "upload"
        verbose_name_plural = "uploads"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} {self.original_name}"

    @property
    def auto_x(self) -> int:
        return 50 if self.focus_x is None else self.focus_x

    @property
    def auto_y(self) -> int:
        return 50 if self.focus_y is None else self.focus_y

    def analyse(self, save: bool = True) -> None:
        """Middelpunt bepalen voor een foto van vóór het automatisch uitlijnen."""
        from .focus import detect_file

        source = self.file_medium or self.file
        try:
            with source.open("rb") as fh:
                focus = detect_file(fh)
        except (OSError, ValueError):
            focus = None
        self.focus_x, self.focus_y, self.faces = (focus.x, focus.y, focus.faces) if focus else (50, 50, 0)
        if save:
            self.save(update_fields=["focus_x", "focus_y", "faces"])

    @property
    def orientation(self) -> str:
        if not self.width or not self.height:
            return "onbekend"
        ratio = self.width / self.height
        if ratio > 1.15:
            return "liggend"
        if ratio < 0.87:
            return "staand"
        return "vierkant"

    def delete_files(self) -> None:
        for field in (self.file, self.file_medium, self.file_thumb):
            if field and field.name:
                field.storage.delete(field.name)


class GuestResponse(models.Model):
    """Aanmelding van een gast. Gasten hebben geen account nodig."""

    invitation = models.ForeignKey(Invitation, on_delete=models.CASCADE, related_name="responses")
    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    client_token = models.CharField(max_length=64)
    name = models.CharField("naam", max_length=120)
    attending = models.BooleanField("aanwezig")
    party_size = models.PositiveSmallIntegerField("aantal personen", default=1)
    answers = models.JSONField(default=list, blank=True)
    remark = models.TextField("toelichting", blank=True, max_length=1000)
    edit_token_hash = models.CharField(max_length=64, unique=True)
    edit_count = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "aanmelding"
        verbose_name_plural = "aanmeldingen"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["invitation", "client_token"], name="uniq_response_client_token")
        ]

    def __str__(self) -> str:
        return f"{self.name} ({'aanwezig' if self.attending else 'afwezig'})"

    @property
    def persons(self) -> int:
        return self.party_size if self.attending else 0

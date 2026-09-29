"""Eigen gezichten op het bruidspaar (Balzaal): de foto's van de klant, de toestemming en het voorbeeld.

De foto's en voorbeelden staan in een eigen, niet-openbare map (gezichten/) en zijn alleen via een view te zien voor
de eigenaar van de uitnodiging en het Vaylide-team. Pas na goedkeuring komt één afbeelding als upload (soort 'scene')
bij de uitnodiging; alleen die kan (na betaling) op de openbare kaart staan.
"""
from __future__ import annotations

import secrets
import uuid

from django.conf import settings
from django.db import models


def private_path(instance, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "webp"
    return f"gezichten/{instance.invitation.uid}/{secrets.token_hex(12)}.{ext}"


class FaceRequest(models.Model):
    class Status(models.TextChoices):
        NEW = "nieuw", "Nog geen voorbeeld"
        BUSY = "bezig", "Voorbeeld wordt gemaakt"
        READY = "klaar", "Voorbeeld klaar om te bekijken"
        APPROVED = "goedgekeurd", "Goedgekeurd"
        FAILED = "mislukt", "Mislukt"

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    invitation = models.OneToOneField("invitations.Invitation", on_delete=models.CASCADE, related_name="face_request")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    consent_at = models.DateTimeField(null=True, blank=True)
    consent_text = models.TextField(blank=True)
    photo_bride = models.FileField(upload_to=private_path, max_length=255, blank=True)
    photo_groom = models.FileField(upload_to=private_path, max_length=255, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW)
    attempts_used = models.PositiveSmallIntegerField(default=0)
    # Loopt altijd op (ook als een mislukte poging niet meetelt): elke run is één taak met een eigen unieke sleutel.
    runs = models.PositiveIntegerField(default=0)
    extra_attempts = models.PositiveSmallIntegerField(default=0, help_text="Extra pogingen, alleen door het beheer toe te kennen.")
    result = models.FileField(upload_to=private_path, max_length=255, blank=True)
    # Haarkleur waarmee het voorbeeld is gemaakt (zwart, bruin of blond); het goedgekeurde beeld hoort bij deze keuze.
    hair_man = models.CharField(max_length=10, blank=True)
    hair_woman = models.CharField(max_length=10, blank=True)
    result_attempt = models.PositiveSmallIntegerField(default=0)
    approved_asset = models.ForeignKey("invitations.MediaAsset", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    error = models.CharField(max_length=300, blank=True)
    provider = models.CharField(max_length=20, blank=True)
    model_name = models.CharField(max_length=60, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "eigen gezichten"
        verbose_name_plural = "eigen gezichten"

    def __str__(self) -> str:
        return f"Eigen gezichten voor {self.invitation}"

    @property
    def attempts_allowed(self) -> int:
        return settings.FACES_FREE_ATTEMPTS + self.extra_attempts

    @property
    def attempts_left(self) -> int:
        return max(0, self.attempts_allowed - self.attempts_used)

    def delete_files(self, *, uploads: bool = True, result: bool = True) -> None:
        fields = (["photo_bride", "photo_groom"] if uploads else []) + (["result"] if result else [])
        for name in fields:
            field = getattr(self, name)
            if field and field.name:
                field.storage.delete(field.name)
                setattr(self, name, "")


from django.db.models.signals import post_delete  # noqa: E402
from django.dispatch import receiver  # noqa: E402


@receiver(post_delete, sender=FaceRequest)
def _delete_files(sender, instance: FaceRequest, **kwargs) -> None:
    """Ook bij het verwijderen van een uitnodiging of account: de foto's en voorbeelden van schijf."""
    instance.delete_files()

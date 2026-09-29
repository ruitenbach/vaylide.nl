"""Verwerkingstaken en uitgaande e-mail.

Taken hebben een unieke sleutel, zodat herhaalde betalingsmeldingen nooit tot
dubbele publicaties of e-mails leiden. Mislukte taken worden met oplopende
wachttijd opnieuw geprobeerd en zijn zichtbaar in de beheeromgeving.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils import timezone


class Job(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Wacht"
        RUNNING = "running", "Bezig"
        DONE = "done", "Klaar"
        FAILED = "failed", "Mislukt, wordt opnieuw geprobeerd"
        DEAD = "dead", "Mislukt, handmatige actie nodig"

    kind = models.CharField(max_length=40)
    payload = models.JSONField(default=dict, blank=True)
    unique_key = models.CharField(max_length=160, unique=True, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempts = models.PositiveSmallIntegerField(default=0)
    max_attempts = models.PositiveSmallIntegerField(default=6)
    run_after = models.DateTimeField(default=timezone.now)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs")
    invitation = models.ForeignKey(
        "invitations.Invitation", null=True, blank=True, on_delete=models.SET_NULL, related_name="jobs"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "verwerkingstaak"
        verbose_name_plural = "verwerkingstaken"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "run_after"])]

    def __str__(self) -> str:
        return f"{self.kind} #{self.pk}"

    @property
    def label(self) -> str:
        return JOB_LABELS.get(self.kind, self.kind)


JOB_LABELS = {
    "fulfil_order": "Bestelling verwerken en publiceren",
    "deliver_order": "Link en QR-code aan de koper leveren",
    "generate_faces": "Voorbeeld met eigen gezichten maken (beeld-API)",
    "fulfil_custom_order": "Maatwerkbetaling verwerken",
    "send_email": "E-mail versturen",
    "assess_request": "Aanvraag laten samenvatten (AI)",
}


class OutboundEmail(models.Model):
    class Status(models.TextChoices):
        QUEUED = "queued", "In wachtrij"
        SENT = "sent", "Verzonden"
        TEST = "test", "Testmodus: bewaard, niet verzonden"
        FAILED = "failed", "Mislukt"

    unique_key = models.CharField(max_length=160, unique=True, null=True, blank=True)
    kind = models.CharField(max_length=40, blank=True)
    to = models.EmailField()
    subject = models.CharField(max_length=200)
    body_text = models.TextField()
    body_html = models.TextField(blank=True)
    attach_qr_for = models.ForeignKey(
        "invitations.Invitation", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.QUEUED)
    attempts = models.PositiveSmallIntegerField(default=0)
    last_error = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.SET_NULL, related_name="emails")
    invitation = models.ForeignKey(
        "invitations.Invitation", null=True, blank=True, on_delete=models.SET_NULL, related_name="emails"
    )
    custom_request = models.ForeignKey(
        "wishes.CustomRequest", null=True, blank=True, on_delete=models.SET_NULL, related_name="emails"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "uitgaande e-mail"
        verbose_name_plural = "uitgaande e-mails"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.subject} → {self.to}"

    @property
    def delivered(self) -> bool:
        return self.status in (self.Status.SENT, self.Status.TEST)

"""Bestellingen en betalingen.

Het totaalbedrag wordt altijd aan de serverzijde berekend (zie orders.pricing).
Publicatie gebeurt uitsluitend na een serverzijdige betalingsbevestiging
(webhook of serverzijdige statuscontrole bij de betaalprovider).
"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone

from catalog.models import format_euro


class Order(models.Model):
    class Kind(models.TextChoices):
        INVITATION = "invitation", "Uitnodiging"
        CUSTOM = "custom", "Maatwerk"

    class Status(models.TextChoices):
        PENDING = "pending", "Wacht op betaling"
        PAID = "paid", "Betaald"
        CANCELLED = "cancelled", "Geannuleerd"
        FAILED = "failed", "Betaling mislukt"
        EXPIRED = "expired", "Verlopen"
        REFUNDED = "refunded", "Terugbetaald"

    class Fulfilment(models.TextChoices):
        NONE = "none", "Nog niet gestart"
        PROCESSING = "processing", "Wordt verwerkt"
        DONE = "done", "Afgerond"
        ATTENTION = "attention", "Aandacht nodig"

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    number = models.CharField("bestelnummer", max_length=24, unique=True)
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.INVITATION)
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name="klant", on_delete=models.PROTECT, related_name="orders"
    )
    invitation = models.ForeignKey(
        "invitations.Invitation", null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
    )
    invitation_title = models.CharField(max_length=200, blank=True)
    version_to_publish = models.ForeignKey(
        "invitations.InvitationVersion", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    custom_request = models.ForeignKey(
        "wishes.CustomRequest", null=True, blank=True, on_delete=models.SET_NULL, related_name="orders"
    )
    package_code = models.CharField(max_length=50, blank=True)
    package_name = models.CharField(max_length=80, blank=True)
    features = models.JSONField(default=list, blank=True)
    max_gallery_photos = models.PositiveSmallIntegerField(default=0)
    availability_months = models.PositiveSmallIntegerField(default=0)
    total_cents = models.PositiveIntegerField("totaal (centen)")
    currency = models.CharField(max_length=3, default="EUR")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    fulfilment_status = models.CharField(
        "verwerking", max_length=12, choices=Fulfilment.choices, default=Fulfilment.NONE
    )
    fulfilment_note = models.TextField(blank=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    # Bij het bestellen vastgelegd (algemene voorwaarden, artikelen 6 en 9): welke versie van de voorwaarden, en de
    # afzonderlijke toestemming voor directe levering met de erkenning over het herroepingsrecht (letterlijke tekst).
    terms_version = models.CharField("versie voorwaarden", max_length=20, blank=True)
    delivery_consent_at = models.DateTimeField("toestemming directe levering", null=True, blank=True)
    delivery_consent_text = models.TextField("tekst toestemming", blank=True)
    # Het verzoek om de online beschikbaarheid (de dienst) direct te starten, tijdens de bedenktijd (artikel 9.3): tijdstip en letterlijke tekst.
    service_consent_at = models.DateTimeField("verzoek start online dienst", null=True, blank=True)
    service_consent_text = models.TextField("tekst verzoek start online dienst", blank=True)
    # Online tot en met (einde van die dag). Eén keer vastgelegd bij de eerste bevestigde betaling.
    ends_at = models.DateTimeField("online tot en met", null=True, blank=True)
    test_mode = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "bestelling"
        verbose_name_plural = "bestellingen"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.number

    @property
    def total_display(self) -> str:
        return format_euro(self.total_cents)

    @property
    def latest_payment(self) -> "Payment | None":
        return self.payments.order_by("-created_at").first()

    @classmethod
    def next_number(cls) -> str:
        year = timezone.now().strftime("%y")
        prefix = f"VL{year}-"
        with transaction.atomic():
            last = (
                cls.objects.select_for_update()
                .filter(number__startswith=prefix)
                .order_by("-number")
                .values_list("number", flat=True)
                .first()
            )
            seq = int(last.split("-")[1]) + 1 if last else 1
        return f"{prefix}{seq:05d}"


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    code = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    quantity = models.PositiveSmallIntegerField(default=1)
    unit_price_cents = models.PositiveIntegerField()
    total_cents = models.PositiveIntegerField()

    class Meta:
        verbose_name = "bestelregel"
        verbose_name_plural = "bestelregels"
        ordering = ["id"]

    @property
    def total_display(self) -> str:
        return format_euro(self.total_cents)


class Withdrawal(models.Model):
    """Een herroeping via de herroepingsfunctie op de site (voorwaarden, artikel 10). Alleen registratie en
    ontvangstbevestiging: terugbetalen gebeurt handmatig in Mollie, na beoordeling door de eigenaar."""

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.ForeignKey(Order, null=True, blank=True, on_delete=models.SET_NULL, related_name="withdrawals")
    name = models.CharField("naam", max_length=120)
    email = models.EmailField("e-mailadres")
    order_number = models.CharField("bestelnummer", max_length=40, blank=True)
    product = models.CharField("product of dienst", max_length=200, blank=True)
    order_date = models.CharField("besteldatum", max_length=40, blank=True)
    note = models.TextField("toelichting", blank=True)
    created_at = models.DateTimeField("ontvangen op", auto_now_add=True)
    handled_at = models.DateTimeField("afgehandeld op", null=True, blank=True)
    handled_note = models.TextField("notitie afhandeling", blank=True)

    class Meta:
        verbose_name = "herroeping"
        verbose_name_plural = "herroepingen"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Herroeping {self.order_number or self.email}"


class Payment(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        PENDING = "pending", "In behandeling"
        PAID = "paid", "Betaald"
        FAILED = "failed", "Mislukt"
        CANCELED = "canceled", "Geannuleerd"
        EXPIRED = "expired", "Verlopen"

    FINAL = {Status.PAID, Status.FAILED, Status.CANCELED, Status.EXPIRED}

    uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    provider = models.CharField(max_length=20)
    provider_ref = models.CharField(max_length=80, blank=True)
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="EUR")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    method = models.CharField(max_length=40, blank=True)
    checkout_url = models.URLField(max_length=600, blank=True)
    # Alleen voor de testprovider: de gesimuleerde status "bij de provider".
    test_remote_status = models.CharField(max_length=10, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "betaling"
        verbose_name_plural = "betalingen"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_ref"],
                condition=~models.Q(provider_ref=""),
                name="uniq_payment_provider_ref",
            )
        ]

    def __str__(self) -> str:
        return f"{self.provider}:{self.provider_ref or self.uid}"


class PaymentEvent(models.Model):
    """Logboek van betalingsmeldingen (webhooks en statuscontroles)."""

    payment = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL, related_name="events")
    provider = models.CharField(max_length=20)
    provider_ref = models.CharField(max_length=80, blank=True)
    source = models.CharField(max_length=20, default="webhook")
    remote_status = models.CharField(max_length=20, blank=True)
    outcome = models.CharField(max_length=200, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "betalingsmelding"
        verbose_name_plural = "betalingsmeldingen"
        ordering = ["-received_at"]

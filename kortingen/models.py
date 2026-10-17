"""Kortingscodes en hun gebruik.

Een code verlaagt alleen het definitieve bestelbedrag (zie kortingen.services). Het gebruik wordt per bestelling vastgelegd in een
DiscountRedemption: eerst gereserveerd (bij het aanmaken van de bestelling), definitief bij de bevestigde betaling, of vrijgegeven.
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone

from catalog.models import format_euro


def normalize_code(value: str) -> str:
    """Hoofdletterongevoelig, zonder spaties en streepjes: 'zomer-10' en 'ZOMER 10' zijn dezelfde code."""
    return "".join(ch for ch in (value or "").upper() if ch.isalnum())


class DiscountCode(models.Model):
    class Kind(models.TextChoices):
        PERCENT = "percent", "Percentage"
        FIXED = "fixed", "Vast bedrag"

    code = models.CharField("code", max_length=40, help_text="Zoals de klant hem ziet, bijvoorbeeld ZOMER10.")
    code_norm = models.CharField(max_length=40, unique=True, editable=False)
    kind = models.CharField("soort", max_length=8, choices=Kind.choices, default=Kind.PERCENT)
    percent = models.PositiveSmallIntegerField("percentage", null=True, blank=True, help_text="Tussen 1 en 90.")
    amount_cents = models.PositiveIntegerField("bedrag (centen)", null=True, blank=True)
    starts_at = models.DateTimeField("geldig vanaf", null=True, blank=True)
    ends_at = models.DateTimeField("geldig tot en met", null=True, blank=True, help_text="Geldt tot het einde van deze dag.")
    max_redemptions = models.PositiveIntegerField("maximaal aantal keer te gebruiken", null=True, blank=True, help_text="Leeg = onbeperkt.")
    max_per_customer = models.PositiveSmallIntegerField("maximaal per klant", default=1, help_text="Hoe vaak één klant de code mag gebruiken.")
    min_order_cents = models.PositiveIntegerField("minimaal bestelbedrag (centen)", default=0)
    occasions = models.JSONField("gelegenheden", default=list, blank=True)
    tiers = models.JSONField("indelingen", default=list, blank=True)
    templates = models.ManyToManyField("catalog.Template", verbose_name="ontwerpen", blank=True, related_name="discount_codes")
    is_active = models.BooleanField("actief", default=True)
    note = models.CharField("interne notitie", max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "kortingscode"
        verbose_name_plural = "kortingscodes"
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=(Q(kind="percent", percent__gte=1, percent__lte=90) | Q(kind="fixed", amount_cents__gte=1)),
                name="kortingscode_waarde_geldig",
            ),
        ]

    def __str__(self) -> str:
        return self.code

    def save(self, *args, **kwargs):
        self.code = (self.code or "").strip().upper()
        self.code_norm = normalize_code(self.code)
        super().save(*args, **kwargs)

    @property
    def value_display(self) -> str:
        return f"{self.percent}%" if self.kind == self.Kind.PERCENT else format_euro(self.amount_cents or 0)

    @property
    def has_redemptions(self) -> bool:
        return self.redemptions.exists()

    def status(self, now=None) -> str:
        """gepland, actief, verlopen, opgebruikt of uitgezet (voor het overzicht in Beheer)."""
        from .services import active_redemptions

        now = now or timezone.now()
        if not self.is_active:
            return "uitgezet"
        if self.starts_at and now < self.starts_at:
            return "gepland"
        if self.ends_at and now > self.ends_at:
            return "verlopen"
        if self.max_redemptions is not None and active_redemptions(self, now=now) >= self.max_redemptions:
            return "opgebruikt"
        return "actief"


class DiscountRedemption(models.Model):
    class State(models.TextChoices):
        RESERVED = "reserved", "Gereserveerd"
        REDEEMED = "redeemed", "Gebruikt"
        RELEASED = "released", "Vrijgegeven"

    code = models.ForeignKey(DiscountCode, on_delete=models.PROTECT, related_name="redemptions")
    order = models.OneToOneField("orders.Order", on_delete=models.CASCADE, related_name="redemption")
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="discount_redemptions")
    # Afgeleide sleutel van het genormaliseerde e-mailadres (niet omkeerbaar): vangt een tweede account met hetzelfde adres met plusje of puntjes.
    customer_key = models.CharField(max_length=64, db_index=True)
    amount_cents = models.PositiveIntegerField()
    state = models.CharField(max_length=10, choices=State.choices, default=State.RESERVED)
    reserved_until = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    redeemed_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    released_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    released_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = "gebruik van kortingscode"
        verbose_name_plural = "gebruik van kortingscodes"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.code} · {self.order.number}"

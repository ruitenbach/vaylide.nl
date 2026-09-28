"""Algemene instellingen en contactberichten."""
from __future__ import annotations

from django.conf import settings
from django.db import models


class SiteConfig(models.Model):
    """Centrale instellingen die de eigenaar zonder code kan aanpassen (één rij)."""

    prices_provisional = models.BooleanField(
        "prijzen als voorlopig tonen", default=True, help_text="Toont 'Voorlopige prijzen' op de prijzenpagina."
    )
    guest_data_retention_days = models.PositiveIntegerField(
        "gastgegevens bewaren (dagen na einde beschikbaarheid)", default=90
    )
    anonymous_draft_retention_days = models.PositiveIntegerField(
        "ontwerpen zonder account bewaren (dagen)", default=30
    )
    unpaid_draft_retention_days = models.PositiveIntegerField(
        "onbetaalde concepten van klanten bewaren (dagen)", default=365
    )
    default_max_party_size = models.PositiveSmallIntegerField("standaard max. personen per aanmelding", default=2)
    support_response_text = models.CharField(
        "tekst over reactietijd",
        max_length=160,
        blank=True,
        help_text="Alleen invullen als je deze belofte echt kunt waarmaken, bijv. 'We reageren binnen 2 werkdagen.'",
    )
    instagram_url = models.URLField("Instagram-pagina", blank=True, default="https://www.instagram.com/vaylidenl/", help_text="Volledige link, bijv. https://www.instagram.com/vaylide/. Leeg = geen icoon in de voettekst.")
    tiktok_url = models.URLField("TikTok-pagina", blank=True, help_text="Volledige link, bijv. https://www.tiktok.com/@vaylide. Leeg = geen icoon in de voettekst.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "instellingen"
        verbose_name_plural = "instellingen"

    def __str__(self) -> str:
        return "Vaylide-instellingen"

    @classmethod
    def get(cls) -> "SiteConfig":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class ContactMessage(models.Model):
    TOPICS = [
        ("vraag", "Algemene vraag"),
        ("bestelling", "Vraag over een bestelling"),
        ("maatwerk", "Bijzondere wens of maatwerk"),
        ("zakelijk", "Zakelijke samenwerking"),
    ]

    name = models.CharField("naam", max_length=120)
    email = models.EmailField("e-mailadres")
    topic = models.CharField("onderwerp", max_length=20, choices=TOPICS, default="vraag")
    message = models.TextField("bericht", max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    handled_at = models.DateTimeField(null=True, blank=True)
    handled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

    class Meta:
        verbose_name = "contactbericht"
        verbose_name_plural = "contactberichten"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name}: {self.get_topic_display()}"

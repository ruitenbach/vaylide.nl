"""Catalogus: ontwerpen (templates) met versies, pakketten en extra opties.

Prijzen, pakketten, opties en beschikbaarheidsduur zijn centraal instelbaar in de
beheeromgeving. Bedragen worden in centen opgeslagen.
"""
from __future__ import annotations

from django.db import models
from django.utils import timezone

from .occasions import OCCASION_CHOICES


def format_euro(cents: int | None) -> str:
    if cents is None:
        return "—"
    euros, rest = divmod(int(cents), 100)
    whole = f"{euros:,}".replace(",", ".")
    return f"€ {whole},{rest:02d}" if rest else f"€ {whole}"


class Template(models.Model):
    slug = models.SlugField("code", unique=True)
    name = models.CharField("naam", max_length=80)
    tagline = models.CharField("korte omschrijving", max_length=160, blank=True)
    description = models.TextField("beschrijving", blank=True)
    style_notes = models.CharField("stijlrichting", max_length=160, blank=True)
    occasions = models.JSONField("gelegenheden", default=list)
    is_active = models.BooleanField("zichtbaar en bestelbaar", default=True)
    sort_order = models.PositiveIntegerField("volgorde", default=0)
    special = models.BooleanField(
        "special", default=False,
        help_text="Bijzonder ontwerp: staat onder Specials, niet tussen de gewone kaarten, en heeft een eigen meerprijs "
                  "(extra optie met functie 'special' en code special-<code>). Zonder die optie is het niet te bestellen.",
    )
    current_version = models.ForeignKey(
        "TemplateVersion",
        verbose_name="versie voor nieuwe uitnodigingen",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "ontwerp"
        verbose_name_plural = "ontwerpen"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def occasion_labels(self) -> list[str]:
        labels = dict(OCCASION_CHOICES)
        return [labels[o] for o in self.occasions if o in labels]

    def supports(self, occasion: str) -> bool:
        return occasion in (self.occasions or [])


class TemplateVersion(models.Model):
    """Een vastgezette versie van een ontwerp.

    Een uitnodiging verwijst altijd naar één versie. Een nieuwe versie verandert
    bestaande uitnodigingen dus niet; overstappen gebeurt alleen bewust.
    """

    template = models.ForeignKey(Template, on_delete=models.CASCADE, related_name="versions")
    number = models.PositiveIntegerField("versie")
    renderer = models.CharField("map", max_length=120, help_text="Bijv. liefde-op-papier/v1")
    manifest = models.JSONField(default=dict)
    changelog = models.TextField("wijzigingen", blank=True)
    released_at = models.DateTimeField("uitgebracht", default=timezone.now)

    class Meta:
        verbose_name = "ontwerpversie"
        verbose_name_plural = "ontwerpversies"
        ordering = ["template", "-number"]
        constraints = [
            models.UniqueConstraint(fields=["template", "number"], name="uniq_template_version")
        ]

    def __str__(self) -> str:
        return f"{self.template.name} v{self.number}"

    @property
    def template_path(self) -> str:
        return f"{self.renderer}/invitation.html"

    @property
    def stylesheet(self) -> str:
        return f"designs/{self.renderer}/style.css"

    @property
    def palettes(self) -> list[dict]:
        return self.manifest.get("palettes", [])

    def palette(self, key: str | None) -> dict:
        palettes = self.palettes
        for palette in palettes:
            if palette.get("key") == key:
                return palette
        return palettes[0] if palettes else {"key": "standaard", "name": "Standaard", "vars": {}}

    @property
    def default_palette_key(self) -> str:
        return self.palette(None).get("key", "standaard")


class Package(models.Model):
    code = models.SlugField("code", unique=True)
    name = models.CharField("naam", max_length=60)
    description = models.CharField("omschrijving", max_length=240, blank=True)
    price_cents = models.PositiveIntegerField("prijs (centen)")
    availability_months = models.PositiveSmallIntegerField("maanden online", default=12)
    features = models.JSONField("inbegrepen functies", default=list, blank=True)
    max_gallery_photos = models.PositiveSmallIntegerField("max. foto's in galerij", default=0)
    highlights = models.JSONField("punten op de prijzenpagina", default=list, blank=True)
    is_active = models.BooleanField("actief", default=True)
    is_featured = models.BooleanField("uitgelicht", default=False)
    sort_order = models.PositiveIntegerField("volgorde", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "pakket"
        verbose_name_plural = "pakketten"
        ordering = ["sort_order", "price_cents"]

    def __str__(self) -> str:
        return self.name

    @property
    def price_display(self) -> str:
        return format_euro(self.price_cents)


class AddOn(models.Model):
    code = models.SlugField("code", unique=True)
    name = models.CharField("naam", max_length=60)
    description = models.CharField("omschrijving", max_length=240, blank=True)
    price_cents = models.PositiveIntegerField("prijs (centen)")
    feature = models.CharField(
        "ontgrendelt functie", max_length=40, blank=True, help_text="Bijv. music, gallery, story"
    )
    extra_months = models.PositiveSmallIntegerField("extra maanden online", default=0)
    gallery_photos = models.PositiveSmallIntegerField("foto's in galerij", default=0)
    is_active = models.BooleanField("actief", default=True)
    sort_order = models.PositiveIntegerField("volgorde", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "extra optie"
        verbose_name_plural = "extra opties"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def price_display(self) -> str:
        return format_euro(self.price_cents)

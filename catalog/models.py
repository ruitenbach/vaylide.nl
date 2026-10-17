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
    if cents < 0:    # een kortingsregel op de bon: '− € 2,50'
        return "\u2212 " + format_euro(-cents)
    euros, rest = divmod(int(cents), 100)
    whole = f"{euros:,}".replace(",", ".")
    from django.conf import settings

    # In de nieuwe prijsstructuur altijd twee decimalen (€ 69,00); anders zoals voorheen (hele euro's zonder ,00).
    if getattr(settings, "PRICING_V2", False):
        return f"€ {whole},{rest:02d}"
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
    def film(self) -> dict:
        """Opening als film (blok 'film' in het manifest): paden voor {% static %}, of leeg zonder film."""
        film = self.manifest.get("film") or {}
        if not film.get("src"):
            return {}
        base = f"designs/{self.renderer}/"
        return {key: base + film[key] for key in ("src", "webm", "poster", "end") if film.get(key)}

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


# ---------------------------------------------------------------- prijsbeheer (Beheer → Prijzen en acties; catalog/prijsbeheer.py)

class PriceRule(models.Model):
    """De geldende prijs van één cel in de prijstabel: prijsrij × indeling (Basis, Luxe of Special), in centen, inclusief btw.
    Wordt alleen gelezen als settings.PRICES_ADMIN aan staat (VIERLIEF_PRIJZENBEHEER); anders gelden de bedragen uit catalog/prijzen.py."""

    rij = models.CharField("prijsrij", max_length=30)
    tier = models.CharField("indeling", max_length=10)
    price_cents = models.PositiveIntegerField("prijs (centen, incl. btw)")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        verbose_name = "verkoopprijs"
        verbose_name_plural = "verkoopprijzen"
        ordering = ["rij", "tier"]
        constraints = [
            models.UniqueConstraint(fields=["rij", "tier"], name="uniq_prijsregel_rij_tier"),
            models.CheckConstraint(condition=models.Q(price_cents__gte=100, price_cents__lte=50000), name="prijsregel_binnen_grenzen"),
        ]

    def __str__(self) -> str:
        return f"{self.rij}/{self.tier} {format_euro(self.price_cents)}"


class PriceChangeSet(models.Model):
    """Eén doorgevoerde prijswijziging (of de startstand, of een terugdraaiing). Alleen toevoegen: sets worden nooit bewerkt of verwijderd."""

    class Kind(models.TextChoices):
        SEED = "seed", "Startstand"
        CHANGE = "wijziging", "Wijziging"
        REVERT = "terugdraaien", "Terugdraaiing"

    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    reason = models.CharField("reden", max_length=300, blank=True)
    reverts = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="reverted_by")

    class Meta:
        verbose_name = "prijswijziging"
        verbose_name_plural = "prijswijzigingen"
        ordering = ["-id"]
        permissions = [
            ("prijzen_wijzigen", "Mag verkoopprijzen wijzigen"),
            ("prijzen_terugdraaien", "Mag een prijswijziging terugdraaien"),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} #{self.pk}"


class PriceChange(models.Model):
    """Eén cel van een wijziging: oud en nieuw bedrag (oud is leeg bij de startstand)."""

    change_set = models.ForeignKey(PriceChangeSet, on_delete=models.PROTECT, related_name="changes")
    rij = models.CharField(max_length=30)
    tier = models.CharField(max_length=10)
    old_cents = models.PositiveIntegerField(null=True, blank=True)
    new_cents = models.PositiveIntegerField()

    class Meta:
        verbose_name = "gewijzigde prijs"
        verbose_name_plural = "gewijzigde prijzen"
        ordering = ["id"]

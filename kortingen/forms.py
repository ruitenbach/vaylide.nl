import secrets
from decimal import Decimal

from django import forms
from django.utils import timezone

from catalog.models import Template
from catalog.occasions import OCCASION_CHOICES
from catalog.prijzen import TIER_NAAM, TIERS

from .models import DiscountCode, normalize_code
from .services import active_redemptions, end_of_day, start_of_day

# Zonder tekens die op elkaar lijken (0/O, 1/I/L).
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
LOCKED_AFTER_USE = ("code", "kind", "percent", "amount", "occasions", "tiers", "templates")


def random_code() -> str:
    for _ in range(20):
        code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(8))
        if not DiscountCode.objects.filter(code_norm=code).exists():
            return code
    raise RuntimeError("Geen vrije code gevonden.")


class DiscountCodeForm(forms.ModelForm):
    amount = forms.DecimalField(label="Bedrag (€)", required=False, localize=True, min_value=Decimal("0.01"), max_digits=8, decimal_places=2,
                                help_text="Alleen bij 'Vast bedrag'.")
    starts_on = forms.DateField(label="Geldig vanaf", required=False, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"))
    ends_on = forms.DateField(label="Geldig tot en met", required=False, widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
                              help_text="De code werkt tot het einde van deze dag.")
    min_order = forms.DecimalField(label="Minimaal bestelbedrag (€)", required=False, localize=True, min_value=0, max_digits=8, decimal_places=2,
                                   help_text="Leeg = geen minimum. Het bedrag voor korting.")
    occasions = forms.MultipleChoiceField(label="Alleen voor deze gelegenheden", required=False, choices=OCCASION_CHOICES,
                                          widget=forms.CheckboxSelectMultiple, help_text="Niets aangevinkt = alle gelegenheden.")
    tiers = forms.MultipleChoiceField(label="Alleen voor deze indelingen", required=False, choices=[(t, TIER_NAAM[t]) for t in TIERS],
                                      widget=forms.CheckboxSelectMultiple, help_text="Niets aangevinkt = Basis, Luxe en Special.")
    templates = forms.ModelMultipleChoiceField(label="Alleen voor deze ontwerpen", required=False, queryset=Template.objects.none(),
                                               widget=forms.CheckboxSelectMultiple, help_text="Niets aangevinkt = de hele collectie. Is er meer dan één soort beperking gekozen, dan moet een kaart aan alle voldoen.")

    class Meta:
        model = DiscountCode
        fields = ["code", "kind", "percent", "max_redemptions", "max_per_customer", "is_active", "note"]
        labels = {"percent": "Percentage (1 tot en met 90)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["templates"].queryset = Template.objects.order_by("name")
        self.fields["code"].required = False
        self.fields["code"].help_text = "Leeg laten = een willekeurige code maken. Hoofdletters, cijfers en streepjes."
        self.fields["max_per_customer"].min_value = 1
        self.fields["max_per_customer"].help_text = "Standaard 1. Controle op het account en op het e-mailadres (zonder plusje); een heel ander e-mailadres is een andere klant."
        self.used = bool(self.instance.pk and self.instance.redemptions.exists())
        if self.instance.pk:
            i = self.instance
            self.initial.update({
                "amount": Decimal(i.amount_cents) / 100 if i.amount_cents else None,
                "starts_on": timezone.localtime(i.starts_at).date() if i.starts_at else None,
                "ends_on": timezone.localtime(i.ends_at).date() if i.ends_at else None,
                "min_order": Decimal(i.min_order_cents) / 100 if i.min_order_cents else None,
                "occasions": i.occasions, "tiers": i.tiers, "templates": i.templates.all(),
            })
        if self.used:
            for name in LOCKED_AFTER_USE:
                self.fields[name].disabled = True
                self.fields[name].help_text = "Vergrendeld: deze code is al gebruikt. Maak een nieuwe code voor een andere korting."

    def clean_code(self):
        code = (self.cleaned_data.get("code") or "").strip()
        if not code:
            return "" if self.instance.pk else random_code()
        norm = normalize_code(code)
        if len(norm) < 4:
            raise forms.ValidationError("Gebruik minstens 4 letters of cijfers.")
        clash = DiscountCode.objects.filter(code_norm=norm).exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError("Deze code bestaat al.")
        return code

    def clean(self):
        data = super().clean()
        kind = data.get("kind")
        if kind == DiscountCode.Kind.PERCENT:
            percent = data.get("percent")
            if percent is None or not 1 <= percent <= 90:
                self.add_error("percent", "Kies een percentage van 1 tot en met 90. Een gratis bestelling is niet mogelijk.")
        elif kind == DiscountCode.Kind.FIXED:
            if not data.get("amount"):
                self.add_error("amount", "Vul het bedrag van de korting in.")
        start, end = data.get("starts_on"), data.get("ends_on")
        if start and end and end < start:
            self.add_error("ends_on", "De einddatum ligt voor de begindatum.")
        limit = data.get("max_redemptions")
        if self.instance.pk and limit is not None and limit < active_redemptions(self.instance):
            self.add_error("max_redemptions", f"Er zijn al {active_redemptions(self.instance)} gebruiken of reserveringen; kies een hoger maximum.")
        if limit is not None and limit < 1:
            self.add_error("max_redemptions", "Leeg laten of minstens 1.")
        return data

    def save(self, commit=True):
        obj = super().save(commit=False)
        d = self.cleaned_data
        if not self.used:
            if obj.kind == DiscountCode.Kind.PERCENT:
                obj.amount_cents = None
            else:
                obj.percent = None
                obj.amount_cents = int(round(d["amount"] * 100))
            obj.occasions = list(d.get("occasions") or [])
            obj.tiers = list(d.get("tiers") or [])
        if not obj.code:
            obj.code = self.instance.code
        obj.starts_at = start_of_day(d["starts_on"]) if d.get("starts_on") else None
        obj.ends_at = end_of_day(d["ends_on"]) if d.get("ends_on") else None
        obj.min_order_cents = int(round((d.get("min_order") or 0) * 100))
        obj.save()
        if not self.used:
            obj.templates.set(d.get("templates") or [])
        return obj

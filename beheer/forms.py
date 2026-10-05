from django import forms

from catalog.features import FEATURES
from catalog.models import AddOn, Package, Template
from catalog.occasions import OCCASION_CHOICES
from core.models import SiteConfig
from invitations.content import HEX_COLOR, SECTION_LABELS

LOCKABLE_FIELDS = [
    ("names", "Namen"),
    ("headline", "Kopregel"),
    ("welcome_text", "Welkomsttekst"),
    ("venue_name", "Locatie"),
    ("address", "Adres"),
]


class OverridesForm(forms.Form):
    headline = forms.CharField(label="Kopregel (overschrijft klanttekst)", max_length=80, required=False)
    notice = forms.CharField(label="Mededeling bovenaan de uitnodiging", max_length=300, required=False,
                             widget=forms.Textarea(attrs={"rows": 2}))
    hide_sections = forms.MultipleChoiceField(label="Onderdelen verbergen", required=False,
                                              choices=[(k, v) for k, v in SECTION_LABELS.items() if k != "location"],
                                              widget=forms.CheckboxSelectMultiple)
    accent = forms.CharField(label="Afwijkende accentkleur (optioneel)", max_length=7, required=False,
                             help_text="Hexcode, bijv. #6E1F31. Laat leeg voor de kleur van de gekozen variant.")
    locked_fields = forms.MultipleChoiceField(label="Velden vergrendelen voor de klant", required=False, choices=LOCKABLE_FIELDS,
                                              widget=forms.CheckboxSelectMultiple,
                                              help_text="Gebruik dit na een handmatige aanpassing, zodat de klant die niet per ongeluk overschrijft.")
    internal_note = forms.CharField(label="Interne notitie", max_length=1000, required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def clean_accent(self):
        value = (self.cleaned_data.get("accent") or "").strip()
        if value and not HEX_COLOR.match(value):
            raise forms.ValidationError("Gebruik een hexcode zoals #6E1F31.")
        return value

    @classmethod
    def initial_from(cls, overrides: dict) -> dict:
        css = overrides.get("css_vars") or {}
        accent = next(iter(css.values()), "") if css else ""
        return {
            "headline": overrides.get("headline", ""),
            "notice": overrides.get("notice", ""),
            "hide_sections": overrides.get("hide_sections", []),
            "accent": accent,
            "locked_fields": overrides.get("locked_fields", []),
            "internal_note": overrides.get("internal_note", ""),
        }

    def to_overrides(self, template_version) -> dict:
        d = self.cleaned_data
        overrides = {
            "headline": d.get("headline", "").strip(),
            "notice": d.get("notice", "").strip(),
            "hide_sections": d.get("hide_sections") or [],
            "locked_fields": d.get("locked_fields") or [],
            "internal_note": d.get("internal_note", "").strip(),
        }
        accent = d.get("accent")
        if accent:
            palette_vars = (template_version.palette(None).get("vars") or {}).keys()
            accent_var = next((v for v in palette_vars if v.endswith("-accent") or v.endswith("-gold")), None)
            if accent_var:
                overrides["css_vars"] = {accent_var: accent}
        return {k: v for k, v in overrides.items() if v}


class TemplateForm(forms.ModelForm):
    occasions = forms.MultipleChoiceField(label="Gelegenheden", choices=OCCASION_CHOICES, widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Template
        fields = ["name", "tagline", "description", "style_notes", "occasions", "is_active", "special", "sort_order", "current_version"]
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["current_version"].queryset = self.instance.versions.all() if self.instance.pk else self.fields["current_version"].queryset.none()
        self.fields["current_version"].required = True


class PackageForm(forms.ModelForm):
    price = forms.DecimalField(label="Prijs (€)", min_value=0, max_digits=8, decimal_places=2)
    features = forms.MultipleChoiceField(label="Inbegrepen functies", required=False, choices=list(FEATURES.items()),
                                         widget=forms.CheckboxSelectMultiple)
    highlights_text = forms.CharField(label="Punten op de prijzenpagina (één per regel)", required=False,
                                      widget=forms.Textarea(attrs={"rows": 6}))

    class Meta:
        model = Package
        fields = ["code", "name", "description", "availability_months", "max_gallery_photos", "is_active", "is_featured", "sort_order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["price"] = self.instance.price_cents / 100
            self.initial["features"] = self.instance.features
            self.initial["highlights_text"] = "\n".join(self.instance.highlights or [])

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.price_cents = int(round(self.cleaned_data["price"] * 100))
        obj.features = self.cleaned_data.get("features") or []
        obj.highlights = [line.strip() for line in (self.cleaned_data.get("highlights_text") or "").splitlines() if line.strip()]
        if commit:
            obj.save()
        return obj


class AddOnForm(forms.ModelForm):
    price = forms.DecimalField(label="Prijs (€)", min_value=0, max_digits=8, decimal_places=2)
    feature = forms.ChoiceField(label="Ontgrendelt functie", required=False, choices=[("", "—")] + list(FEATURES.items()))

    class Meta:
        model = AddOn
        fields = ["code", "name", "description", "feature", "extra_months", "gallery_photos", "is_active", "sort_order"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial["price"] = self.instance.price_cents / 100

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.price_cents = int(round(self.cleaned_data["price"] * 100))
        if commit:
            obj.save()
        return obj


class SiteConfigForm(forms.ModelForm):
    class Meta:
        model = SiteConfig
        fields = ["prices_provisional", "support_response_text", "default_max_party_size", "guest_data_retention_days",
                  "anonymous_draft_retention_days", "unpaid_draft_retention_days"]


class ExtendForm(forms.Form):
    months = forms.IntegerField(label="Aantal maanden verlengen", min_value=1, max_value=60)

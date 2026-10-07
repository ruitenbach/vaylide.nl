"""Formulieren per stap. Elk formulier leest uit en schrijft naar het inhoudsdocument.

Velden zijn formeel optioneel, zodat 'Opslaan en later verder' altijd werkt.
Bij 'Volgende' controleert `missing()` of de verplichte gegevens van de stap
compleet zijn; ingevulde gegevens worden dan toch bewaard.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from django import forms
from django.utils import timezone

from catalog import envelop, envelop_collectie, paar
from catalog.models import Template
from catalog.occasions import OCCASION_CHOICES, occasion_config
from invitations import vragen
from invitations.content import (
    MAX_PRACTICAL_ITEMS,
    MAX_PROGRAM_ITEMS,
    MAX_QUESTIONS,
    SOORTEN,
    TIMEZONES,
    card_kind,
    parse_date,
)

# Zegels in de keuzelijst van de Studio: wat de klant ziet is het materiaal en wat er op staat, geen merk- of ontwerpnaam
# (Champagne Monogram, Noisette Gold, ...). Alleen de zichtbare labels; de codes en de namen in de registry blijven zoals ze zijn.
ZEGEL_KEUZENAMEN = {
    "champagne-monogram": ("Champagnegoud", "Met de V"),
    "noisette-gold": ("Warm goud", "Met de V"),
    "sage-botanical": ("Saliegroen", "Met de V"),
    "rose-floral": ("Roségoud", "Met een roos"),
    "evergreen": ("Dennengroen", "Met de V in een krans"),
}

# Zegels uit de Envelope Collection tonen hoogstens zoveel tekens (catalog/envelop_collectie.py: monogram[:4]); de klassieke zegels 5.
INITIALEN_COLLECTIE = 4
PHONE_RE = re.compile(r"^[+()\d\s.-]{6,30}$")
DATE_WIDGET = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
TIME_WIDGET = forms.TimeInput(attrs={"type": "time"}, format="%H:%M")


class StepForm(forms.Form):
    """Basis: velden uit `locked` zijn alleen-lezen (handmatig aangepast door Vaylide)."""

    field_paths: dict[str, str] = {}

    def __init__(self, *args, content: dict, occasion: str, locked: list[str] | None = None, **kwargs):
        self.content = content
        self.occasion = occasion
        self.locked = set(locked or [])
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if self.field_paths.get(name) in self.locked or name in self.locked:
                field.disabled = True
                field.help_text = "Handmatig aangepast door het VAYLIDE-team. Neem contact op om dit te wijzigen."

    def missing(self) -> dict[str, str]:
        return {}


def _s(value) -> str:
    return "" if value is None else str(value).strip()


class DesignForm(forms.Form):
    occasion = forms.ChoiceField(label="Gelegenheid", choices=OCCASION_CHOICES, widget=forms.RadioSelect)
    template = forms.ChoiceField(label="Ontwerp", widget=forms.RadioSelect)

    def __init__(self, *args, templates, **kwargs):
        self.templates = {t.slug: t for t in templates}
        super().__init__(*args, **kwargs)
        self.fields["template"].choices = [(t.slug, t.name) for t in templates]

    def clean(self):
        data = super().clean()
        template = self.templates.get(data.get("template"))
        if template and data.get("occasion") and not template.supports(data["occasion"]):
            self.add_error("template", "Dit ontwerp is niet beschikbaar voor deze gelegenheid. Kies een ander ontwerp.")
        data["template_obj"] = template
        return data


class DetailsForm(StepForm):
    field_paths = {"headline": "headline", "welcome_text": "welcome_text", "venue_name": "venue_name", "address": "address"}

    headline = forms.CharField(label="Eigen kopregel (optioneel)", max_length=80, required=False)
    date = forms.DateField(label="Datum", required=False, widget=DATE_WIDGET,
                           error_messages={"invalid": "Vul een geldige datum in."})
    start_time = forms.TimeField(label="Begintijd", required=False, widget=TIME_WIDGET,
                                 error_messages={"invalid": "Vul een geldige tijd in, bijvoorbeeld 14:00."})
    end_time = forms.TimeField(label="Eindtijd (optioneel)", required=False, widget=TIME_WIDGET,
                               error_messages={"invalid": "Vul een geldige tijd in, bijvoorbeeld 23:30."})
    timezone = forms.ChoiceField(label="Tijdzone", choices=TIMEZONES, initial="Europe/Amsterdam", required=False,
                                 help_text="De tijden op de uitnodiging en de afteller gebruiken deze tijdzone.")
    venue_name = forms.CharField(label="Naam van de locatie", max_length=120, required=False)
    address = forms.CharField(label="Adres", max_length=300, required=False,
                              widget=forms.Textarea(attrs={"rows": 3, "autocomplete": "street-address"}),
                              help_text="Straat en huisnummer, postcode en plaats. Wordt gebruikt voor de routeknop.")
    route_url = forms.URLField(label="Eigen routelink (optioneel)", max_length=500, required=False, assume_scheme="https",
                               help_text="Bijvoorbeeld een link naar een specifieke ingang. Laat leeg om automatisch een routelink te maken.",
                               error_messages={"invalid": "Vul een volledige link in die begint met https://"})
    welcome_text = forms.CharField(label="Welkomsttekst", max_length=1500, required=False,
                                   widget=forms.Textarea(attrs={"rows": 5, "data-ai-field": "welcome_text"}),
                                   help_text="Een persoonlijke tekst bovenaan je uitnodiging.")

    def __init__(self, *args, soort_vergrendeld: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = occasion_config(self.occasion)
        self.event_optional = bool(cfg.get("event_optional"))
        if self.event_optional:
            self.fields["venue_name"].help_text = "Bijvoorbeeld 'Bij ons thuis' of de naam van het restaurant."
        # Uitnodiging (met datum, locatie en aanmelden) of wenskaart (alleen een groet), bij elke gelegenheid. Na betaling ligt de keuze
        # vast: het is een ander product met een andere prijs.
        self.fields["soort"] = forms.ChoiceField(
            label="Wat voor kaart wordt het?", choices=[(s, s) for s in SOORTEN], required=False, widget=forms.RadioSelect,
            disabled=soort_vergrendeld)
        self.initial["soort"] = card_kind(self.content, self.occasion)
        self.soort_vergrendeld = soort_vergrendeld
        self.name_keys = []
        new_fields = {}
        # Bij een wenskaart is één naam genoeg: alleen het eerste verplichte naamveld blijft verplicht (bij een bruiloft Naam partner 1; een
        # wenskaart voor één persoon hoeft geen tweede naam). Een uitnodiging vraagt alle verplichte namen, zoals altijd.
        self.wenskaart = self._soort_nu() == "wenskaart"
        for key, label, required, max_len, help_text in cfg["name_fields"]:
            name = f"name_{key}"
            required = False    # alle velden zijn optioneel: de klant bepaalt zelf wat er op de kaart komt
            self.name_keys.append((name, key, label, required))
            if key in ("age", "years"):
                field = forms.IntegerField(label=label, required=False, min_value=1, max_value=150, help_text=help_text,
                                           error_messages={"invalid": "Vul een getal in.", "min_value": "Vul een getal vanaf 1 in.",
                                                           "max_value": "Vul een realistisch getal in."})
            else:
                field = forms.CharField(label=label, required=False, max_length=max_len, help_text=help_text)
            field.widget.attrs["data-required"] = ""
            if "names" in self.locked:
                field.disabled = True
            new_fields[name] = field
        # Namen eerst.
        self.fields = {**new_fields, **self.fields}
        self.fields["headline"].help_text = f"Laat leeg voor: '{cfg['default_headline']}'."
        c = self.content
        if not self.is_bound:
            for name, key, *_ in self.name_keys:
                self.initial[name] = (c.get("names") or {}).get(key, "")
            for key in ("headline", "venue_name", "address", "route_url", "welcome_text"):
                self.initial[key] = c.get(key, "")
            self.initial["date"] = parse_date(c.get("date"))
            self.initial["start_time"] = c.get("start_time") or None
            self.initial["end_time"] = c.get("end_time") or None
            self.initial["timezone"] = c.get("timezone") or "Europe/Amsterdam"

    def _soort_nu(self) -> str:
        """De soort kaart waar dit formulier nu over gaat: de keuze in het verzonden formulier (als die kan wijzigen), anders de opgeslagen."""
        if self.is_bound and "soort" in self.fields and not self.fields["soort"].disabled and self.data.get("soort") in SOORTEN:
            return self.data.get("soort")
        return card_kind(self.content, self.occasion)

    def clean_date(self):
        value = self.cleaned_data.get("date")
        if value:
            today = timezone.localdate()
            if value < today - timedelta(days=365 * 2):
                raise forms.ValidationError("Deze datum ligt ver in het verleden. Controleer het jaartal.")
            if value > today + timedelta(days=365 * 5):
                raise forms.ValidationError("Kies een datum binnen vijf jaar.")
        return value

    def clean(self):
        data = super().clean()
        if data.get("end_time") and not data.get("start_time"):
            self.add_error("start_time", "Vul ook een begintijd in.")
        return data

    def apply(self, content: dict) -> dict:
        d = self.cleaned_data
        names = dict(content.get("names") or {})
        for name, key, *_ in self.name_keys:
            if name in d and not self.fields[name].disabled:
                names[key] = _s(d.get(name))
        content["names"] = names
        for key in ("headline", "venue_name", "address", "route_url", "welcome_text"):
            if not self.fields[key].disabled:
                content[key] = _s(d.get(key))
        content["date"] = d["date"].isoformat() if d.get("date") else ""
        content["start_time"] = d["start_time"].strftime("%H:%M") if d.get("start_time") else ""
        content["end_time"] = d["end_time"].strftime("%H:%M") if d.get("end_time") else ""
        content["timezone"] = d.get("timezone") or "Europe/Amsterdam"
        if not self.fields["soort"].disabled:
            if d.get("soort") in SOORTEN:
                content["soort"] = d["soort"]
        return content

    def missing(self) -> dict[str, str]:
        """Niets is verplicht: een leeg veld laat het bijbehorende onderdeel gewoon van de kaart weg."""
        return {}


class ProgramForm(StepForm):
    dresscode_text = forms.CharField(label="Dresscode (optioneel)", max_length=400, required=False,
                                     widget=forms.Textarea(attrs={"rows": 2}), help_text="Bijvoorbeeld: zomers chic, black tie of 'kom zoals je bent'.")
    contact_name = forms.CharField(label="Naam contactpersoon", max_length=80, required=False,
                                   help_text="Bijvoorbeeld de ceremoniemeester. Deze gegevens zijn zichtbaar voor iedereen met de link.")
    contact_phone = forms.CharField(label="Telefoon (optioneel)", max_length=30, required=False,
                                    widget=forms.TextInput(attrs={"type": "tel", "autocomplete": "tel"}))
    contact_email = forms.EmailField(label="E-mail (optioneel)", required=False,
                                     error_messages={"invalid": "Vul een geldig e-mailadres in."})
    contact_note = forms.CharField(label="Toelichting (optioneel)", max_length=200, required=False)
    closing_text = forms.CharField(label="Afsluitende tekst (optioneel)", max_length=400, required=False,
                                   widget=forms.Textarea(attrs={"rows": 2, "data-ai-field": "closing_text"}),
                                   help_text="Bijvoorbeeld: 'We kijken ernaar uit. Tot dan!'")

    COLOR_SLOTS = 4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        c = self.content
        # Wenskaart: alleen de afsluitende tekst; programma, dresscode, praktisch en contact blijven ongewijzigd bewaard.
        self.only_closing = card_kind(c, self.occasion) == "wenskaart"
        if self.only_closing:
            self.fields["closing_text"].label = "Afsluitende wens (optioneel)"
            self.fields["closing_text"].help_text = "Bijvoorbeeld: 'Fijne feestdagen en alvast een gelukkig nieuwjaar!'"
        program = list(c.get("program") or [])
        practical = list(c.get("practical") or [])
        self.program_rows = min(MAX_PROGRAM_ITEMS, max(len(program) + 2, 4))
        self.practical_rows = min(MAX_PRACTICAL_ITEMS, max(len(practical) + 1, 3))
        if self.is_bound:
            self.program_rows = min(MAX_PROGRAM_ITEMS, max(self.program_rows, self._bound_rows("p", "title")))
            self.practical_rows = min(MAX_PRACTICAL_ITEMS, max(self.practical_rows, self._bound_rows("k", "title")))
        for i in range(self.program_rows):
            self.fields[f"p{i}_time"] = forms.TimeField(label="Tijd", required=False, widget=TIME_WIDGET,
                                                        error_messages={"invalid": "Ongeldige tijd."})
            self.fields[f"p{i}_title"] = forms.CharField(label="Onderdeel", max_length=80, required=False)
            self.fields[f"p{i}_description"] = forms.CharField(label="Toelichting (optioneel)", max_length=300, required=False)
        for i in range(self.practical_rows):
            self.fields[f"k{i}_title"] = forms.CharField(label="Kopje", max_length=60, required=False)
            self.fields[f"k{i}_text"] = forms.CharField(label="Tekst", max_length=600, required=False,
                                                        widget=forms.Textarea(attrs={"rows": 2}))
        for i in range(self.COLOR_SLOTS):
            self.fields[f"dc{i}_use"] = forms.BooleanField(label="Toon kleur", required=False)
            self.fields[f"dc{i}_color"] = forms.CharField(required=False, max_length=7,
                                                          widget=forms.TextInput(attrs={"type": "color", "aria-label": f"Kleur {i + 1}"}))
        if not self.is_bound:
            for i, item in enumerate(program[: self.program_rows]):
                self.initial[f"p{i}_time"] = item.get("time") or None
                self.initial[f"p{i}_title"] = item.get("title", "")
                self.initial[f"p{i}_description"] = item.get("description", "")
            for i, item in enumerate(practical[: self.practical_rows]):
                self.initial[f"k{i}_title"] = item.get("title", "")
                self.initial[f"k{i}_text"] = item.get("text", "")
            colors = (c.get("dresscode") or {}).get("colors") or []
            defaults = ["#E9D5C9", "#C9A2A0", "#A7B8A0", "#F4EBDD"]
            for i in range(self.COLOR_SLOTS):
                self.initial[f"dc{i}_use"] = i < len(colors)
                self.initial[f"dc{i}_color"] = colors[i] if i < len(colors) else defaults[i]
            self.initial["dresscode_text"] = (c.get("dresscode") or {}).get("text", "")
            contact = c.get("contact") or {}
            self.initial["contact_name"] = contact.get("name", "")
            self.initial["contact_phone"] = contact.get("phone", "")
            self.initial["contact_email"] = contact.get("email", "")
            self.initial["contact_note"] = contact.get("note", "")
            self.initial["closing_text"] = c.get("closing_text", "")

    def _bound_rows(self, prefix, suffix) -> int:
        highest = -1
        pattern = re.compile(rf"^{prefix}(\d+)_{suffix}$")
        for key in self.data.keys():
            m = pattern.match(key)
            if m:
                highest = max(highest, int(m.group(1)))
        return highest + 1

    def _ingevuld(self, *namen) -> bool:
        return any(self[naam].value() for naam in namen if naam in self.fields)

    @property
    def programma_open(self) -> bool:
        return self._ingevuld(*[f"p{i}_{k}" for i in range(self.program_rows) for k in ("title", "time", "description")])

    @property
    def dresscode_open(self) -> bool:
        return self._ingevuld("dresscode_text") or any(self[f"dc{i}_use"].value() for i in range(self.COLOR_SLOTS))

    @property
    def tips_open(self) -> bool:
        return self._ingevuld(*[f"k{i}_{k}" for i in range(self.practical_rows) for k in ("title", "text")])

    @property
    def contact_open(self) -> bool:
        return self._ingevuld("contact_name", "contact_phone", "contact_email", "contact_note")

    @property
    def program_fields(self):
        return [(self[f"p{i}_time"], self[f"p{i}_title"], self[f"p{i}_description"]) for i in range(self.program_rows)]

    @property
    def practical_fields(self):
        return [(self[f"k{i}_title"], self[f"k{i}_text"]) for i in range(self.practical_rows)]

    @property
    def color_fields(self):
        return [(self[f"dc{i}_use"], self[f"dc{i}_color"]) for i in range(self.COLOR_SLOTS)]

    def clean(self):
        data = super().clean()
        for i in range(self.program_rows):
            if (data.get(f"p{i}_time") or _s(data.get(f"p{i}_description"))) and not _s(data.get(f"p{i}_title")):
                self.add_error(f"p{i}_title", "Geef dit onderdeel een naam, of maak de rij leeg.")
        for i in range(self.practical_rows):
            if _s(data.get(f"k{i}_text")) and not _s(data.get(f"k{i}_title")):
                self.add_error(f"k{i}_title", "Geef dit kopje een naam.")
        for i in range(self.COLOR_SLOTS):
            color = _s(data.get(f"dc{i}_color"))
            if data.get(f"dc{i}_use") and not re.match(r"^#[0-9a-fA-F]{6}$", color):
                self.add_error(f"dc{i}_color", "Kies een geldige kleur.")
        phone = _s(data.get("contact_phone"))
        if phone and not PHONE_RE.match(phone):
            self.add_error("contact_phone", "Vul een geldig telefoonnummer in.")
        return data

    def apply(self, content: dict) -> dict:
        d = self.cleaned_data
        sections = content.setdefault("sections", {})
        sections["closing"] = True    # ingevuld = zichtbaar, leeg = weg; een eerdere schakelaar bij Stijl bestaat niet meer
        if self.only_closing:
            content["closing_text"] = _s(d.get("closing_text"))
            return content
        sections.update({key: True for key in ("program", "dresscode", "practical", "contact")})
        program = []
        for i in range(self.program_rows):
            title = _s(d.get(f"p{i}_title"))
            if title:
                t = d.get(f"p{i}_time")
                program.append({"time": t.strftime("%H:%M") if t else "", "title": title,
                                "description": _s(d.get(f"p{i}_description"))})
        program.sort(key=lambda item: (item["time"] == "", item["time"]))
        content["program"] = program
        content["practical"] = [
            {"title": _s(d.get(f"k{i}_title")), "text": _s(d.get(f"k{i}_text"))}
            for i in range(self.practical_rows)
            if _s(d.get(f"k{i}_title"))
        ]
        colors = [_s(d.get(f"dc{i}_color")).upper() for i in range(self.COLOR_SLOTS) if d.get(f"dc{i}_use")]
        content["dresscode"] = {"text": _s(d.get("dresscode_text")), "colors": colors}
        content["contact"] = {
            "name": _s(d.get("contact_name")),
            "phone": _s(d.get("contact_phone")),
            "email": _s(d.get("contact_email")),
            "note": _s(d.get("contact_note")),
        }
        content["closing_text"] = _s(d.get("closing_text"))
        return content


class RsvpSettingsForm(StepForm):
    """Aanmelden: standaard alleen naam, aanwezigheid en aantal personen. Extra vragen alleen uit de vaste lijst
    (invitations/vragen.py); geen eigen vraagteksten of antwoordopties, zodat er geen gevoelige gegevens worden
    uitgevraagd. Oude eigen vragen blijven staan tot de organisator ze weghaalt."""

    enabled = forms.BooleanField(label="Gasten kunnen zich aanmelden", required=False)
    deadline = forms.DateField(label="Aanmelden kan tot en met (optioneel)", required=False, widget=DATE_WIDGET,
                               error_messages={"invalid": "Vul een geldige datum in."})
    max_party_size = forms.IntegerField(label="Personen per aanmelding (maximaal)", min_value=1, max_value=10, initial=2, required=False,
                                        help_text="Gasten kiezen met hoeveel personen ze komen, inclusief zichzelf. 1 = alleen de gast zelf.",
                                        error_messages={"min_value": "Minimaal 1.", "max_value": "Maximaal 10.", "invalid": "Vul een getal in."})
    capacity = forms.IntegerField(label="Maximaal aantal gasten in totaal", min_value=1, max_value=5000, required=False,
                                  help_text="Is dit aantal bereikt, dan sluit het aanmelden vanzelf.",
                                  error_messages={"min_value": "Minimaal 1.", "invalid": "Vul een getal in."})
    ask_remark = forms.BooleanField(label="Gasten kunnen een korte toelichting meesturen", required=False)
    remark_standaard = forms.BooleanField(label="Gebruik de standaardvraag bij de toelichting", required=False)
    max_vragen = MAX_QUESTIONS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rsvp = self.content.get("rsvp") or {}
        questions = [q for q in rsvp.get("questions") or [] if isinstance(q, dict)]
        self.formal = bool(occasion_config(self.occasion).get("formal"))
        self.oude_vragen = vragen.eigen_vragen(questions)
        self.oude_toelichting = (rsvp.get("remark_label") or "").strip() if vragen.eigen_toelichting(rsvp) else ""
        chosen = {q.get("id"): q for q in questions if vragen.is_vast(q)}
        for v in vragen.VRAGEN:
            self.fields[f"vraag_{v['key']}"] = forms.BooleanField(
                label=v["label_u"] if self.formal else v["label"], required=False, help_text=v["uitleg"])
            self.fields[f"verplicht_{v['key']}"] = forms.BooleanField(label="Verplicht", required=False)
        for i, _q in enumerate(self.oude_vragen):
            self.fields[f"oud_{i}_weg"] = forms.BooleanField(label="Deze vraag weghalen", required=False)
        # Bij een bruiloft vragen we geen aanmeldperiode: het onderdeel 'Aanmelden tot en met' hoort niet meer bij het personaliseren.
        self.zonder_deadline = self.occasion == "bruiloft"
        if self.zonder_deadline:
            del self.fields["deadline"]
        if not self.is_bound:
            self.initial["enabled"] = bool((self.content.get("sections") or {}).get("rsvp"))
            self.initial["deadline"] = parse_date(rsvp.get("deadline"))
            self.initial["max_party_size"] = rsvp.get("max_party_size") or 2
            self.initial["capacity"] = rsvp.get("capacity")
            self.initial["ask_remark"] = bool(rsvp.get("ask_remark", False))
            for key, q in chosen.items():
                self.initial[f"vraag_{key}"] = True
                self.initial[f"verplicht_{key}"] = bool(q.get("required"))

    @property
    def vragen_open(self) -> bool:
        return any(self[f"vraag_{v['key']}"].value() for v in vragen.VRAGEN) or bool(self.oude_vragen)

    @property
    def question_fields(self):
        return [(self[f"vraag_{v['key']}"], self[f"verplicht_{v['key']}"], v) for v in vragen.VRAGEN]

    @property
    def old_question_fields(self):
        return [(q, self[f"oud_{i}_weg"]) for i, q in enumerate(self.oude_vragen)]

    def _kept_old(self, d) -> list[dict]:
        return [q for i, q in enumerate(self.oude_vragen) if not d.get(f"oud_{i}_weg")]

    def clean(self):
        data = super().clean()
        event_day = parse_date(self.content.get("date"))
        deadline = data.get("deadline")
        if deadline and event_day and deadline > event_day:
            self.add_error("deadline", "De deadline moet op of vóór de datum van het evenement liggen.")
        total = sum(1 for v in vragen.VRAGEN if data.get(f"vraag_{v['key']}")) + len(self._kept_old(data))
        if total > MAX_QUESTIONS:
            self.add_error(None, f"Kies maximaal {MAX_QUESTIONS} extra vragen.")
        return data

    def apply(self, content: dict) -> dict:
        d = self.cleaned_data
        content.setdefault("sections", {})["rsvp"] = bool(d.get("enabled"))
        old = content.get("rsvp") or {}
        questions = [vragen.vraag(v["key"], formal=self.formal, required=bool(d.get(f"verplicht_{v['key']}")))
                     for v in vragen.VRAGEN if d.get(f"vraag_{v['key']}")]
        questions += self._kept_old(d)  # oude eigen vragen: alleen weghalen, niet wijzigen (zie docs/PRIVACY.md)
        standaard = vragen.TOELICHTING_LABEL_U if self.formal else vragen.TOELICHTING_LABEL
        remark_label = self.oude_toelichting if self.oude_toelichting and not d.get("remark_standaard") else standaard
        content["rsvp"] = {
            "deadline": "" if self.zonder_deadline else (d["deadline"].isoformat() if d.get("deadline") else ""),
            "max_party_size": d.get("max_party_size") or 2,    # leeg gelaten: de standaard, twee personen
            "capacity": d.get("capacity"),
            "ask_remark": bool(d.get("ask_remark")),
            "remark_label": remark_label,
            "questions": questions,
        }
        return content

    def missing(self) -> dict[str, str]:
        return {}   # ook een aanmelddeadline is optioneel


class PhotosForm(StepForm):
    hero = forms.ChoiceField(label="Hoofdfoto", required=False, widget=forms.RadioSelect)
    story_title = forms.CharField(label="Titel van het verhaal", max_length=60, required=False)
    story_text = forms.CharField(label="Jullie verhaal (optioneel)", max_length=2000, required=False,
                                 widget=forms.Textarea(attrs={"rows": 6, "data-ai-field": "story"}))
    music_asset = forms.ChoiceField(label="Muziek", required=False, widget=forms.RadioSelect)
    music_source = forms.ChoiceField(label="Muziek", required=False, widget=forms.RadioSelect,
                                     choices=[("design", "Muziek van dit ontwerp"), ("none", "Geen muziek"), ("custom", "Eigen muziek uploaden")])
    music_title = forms.CharField(label="Titel en artiest (optioneel)", max_length=80, required=False)
    music_rights = forms.BooleanField(label="Ik heb toestemming om deze muziek op mijn uitnodiging te gebruiken", required=False)

    def __init__(self, *args, photos, audio, ontwerp_muziek=None, **kwargs):
        self.photos = list(photos)
        self.audio = list(audio)
        self.ontwerp_muziek = ontwerp_muziek if isinstance(ontwerp_muziek, dict) and ontwerp_muziek.get("src") else None   # de track van het ontwerp (manifest "music"), of None
        super().__init__(*args, **kwargs)
        c = self.content
        # Een wenskaart heeft alleen een hoofdfoto: geen galerij, verhaal of muziek (die blijven ongewijzigd bewaard).
        self.wenskaart = c.get("soort") == "wenskaart"
        self.fields["hero"].choices = [("", "Geen hoofdfoto")] + [(str(p.uid), p.original_name or "Foto") for p in self.photos]
        self.fields["music_asset"].choices = ([] if self.ontwerp_muziek else [("", "Geen muziek")]) + [(str(a.uid), a.original_name or "Muziek") for a in self.audio]
        if not self.ontwerp_muziek:
            del self.fields["music_source"]       # een ontwerp zonder eigen track houdt de muziekstap zoals die was
        hero = (c.get("photos") or {}).get("hero") or {}
        gallery = {str(g.get("asset")): g for g in (c.get("photos") or {}).get("gallery") or [] if isinstance(g, dict)}
        for p in self.photos:
            uid = str(p.uid)
            ref = hero if str(hero.get("asset")) == uid else gallery.get(uid, {})
            self.fields[f"g_{uid}"] = forms.BooleanField(label="In de fotogalerij", required=False)
            self.fields[f"x_{uid}"] = forms.IntegerField(label="Horizontaal", min_value=0, max_value=100, required=False,
                                                         widget=forms.NumberInput(attrs={"type": "range", "step": 1}))
            self.fields[f"y_{uid}"] = forms.IntegerField(label="Verticaal", min_value=0, max_value=100, required=False,
                                                         widget=forms.NumberInput(attrs={"type": "range", "step": 1}))
            self.fields[f"z_{uid}"] = forms.IntegerField(label="Inzoomen", min_value=100, max_value=250, required=False,
                                                         widget=forms.NumberInput(attrs={"type": "range", "step": 5}))
            self.fields[f"c_{uid}"] = forms.CharField(label="Onderschrift (optioneel)", max_length=140, required=False)
            if not self.is_bound:
                self.initial[f"g_{uid}"] = uid in gallery
                self.initial[f"x_{uid}"] = int(float(ref["x"])) if ref.get("x") is not None else p.auto_x
                self.initial[f"y_{uid}"] = int(float(ref["y"])) if ref.get("y") is not None else p.auto_y
                self.initial[f"z_{uid}"] = int(float(ref.get("zoom", 1) or 1) * 100)
                self.initial[f"c_{uid}"] = gallery.get(uid, {}).get("caption", "")
        if not self.is_bound:
            self.initial["hero"] = str(hero.get("asset") or "") or (str(self.photos[0].uid) if self.photos else "")
            story = c.get("story") or {}
            self.initial["story_title"] = story.get("title", "")
            self.initial["story_text"] = story.get("text", "")
            music = c.get("music") or {}
            self.initial["music_asset"] = str(music.get("asset") or "") or (str(self.audio[0].uid) if self.ontwerp_muziek and self.audio else "")
            self.initial["music_title"] = music.get("title", "")
            self.initial["music_rights"] = bool(music.get("asset")) and music.get("source") in ("custom", "")
            if self.ontwerp_muziek:
                self.initial["music_source"] = music.get("source") or ("custom" if music.get("asset") else "none")   # alleen om te tonen wat er nu geldt; opgeslagen wordt wat de klant kiest

    def photo_rows(self):
        rows = []
        for p in self.photos:
            uid = str(p.uid)
            rows.append({"asset": p, "uid": uid, "gallery": self[f"g_{uid}"], "x": self[f"x_{uid}"], "y": self[f"y_{uid}"],
                         "zoom": self[f"z_{uid}"], "caption": self[f"c_{uid}"]})
        return rows

    def clean(self):
        data = super().clean()
        if self.ontwerp_muziek and "music_source" in self.fields:
            bron = data.get("music_source") or ""
            if bron not in ("design", "none", "custom"):
                self.add_error("music_source", "Kies welke muziek je wilt.")
            elif bron == "custom":
                if not data.get("music_asset"):
                    self.add_error("music_asset", "Upload een muziekbestand en kies het hier, of kies een andere optie.")
                elif not data.get("music_rights"):
                    self.add_error("music_rights", "Bevestig dat je deze muziek mag gebruiken, of kies een andere optie.")
            return data
        if data.get("music_asset") and not data.get("music_rights"):
            self.add_error("music_rights", "Bevestig dat je deze muziek mag gebruiken, of kies 'Geen muziek'.")
        return data

    def _ref(self, uid: str) -> dict:
        d = self.cleaned_data
        x = d.get(f"x_{uid}")
        y = d.get(f"y_{uid}")
        z = d.get(f"z_{uid}")
        return {"asset": uid, "x": 50 if x is None else x, "y": 50 if y is None else y, "zoom": round((z or 100) / 100, 2)}

    def apply(self, content: dict) -> dict:
        d = self.cleaned_data
        hero_uid = d.get("hero") or ""
        if self.wenskaart:
            content.setdefault("photos", {"hero": None, "gallery": []})["hero"] = self._ref(hero_uid) if hero_uid else None
            return content
        gallery = []
        for p in self.photos:
            uid = str(p.uid)
            if d.get(f"g_{uid}"):
                ref = self._ref(uid)
                ref["caption"] = _s(d.get(f"c_{uid}"))
                gallery.append(ref)
        content["photos"] = {"hero": self._ref(hero_uid) if hero_uid else None, "gallery": gallery}
        content["story"] = {"title": _s(d.get("story_title")) or occasion_config(self.occasion)["story_title"],
                            "text": _s(d.get("story_text"))}
        if gallery:
            content.setdefault("sections", {})["gallery"] = True
        if self.ontwerp_muziek:
            # Ontwerp met een eigen track: de bron wordt expliciet bewaard. Eerder geüploade klantmuziek blijft bij "design" en "none" gewoon bewaard (en gratis, want ze speelt dan niet).
            bron = d.get("music_source") or ""
            oud = content.get("music") or {}
            asset = (d.get("music_asset") or None) if bron == "custom" else (oud.get("asset") or None)
            content["music"] = {"asset": asset, "title": _s(d.get("music_title")) if bron == "custom" else (oud.get("title") or ""), "source": bron}
            content.setdefault("sections", {})["music"] = bron == "design" or (bron == "custom" and bool(asset))
        else:
            music_uid = d.get("music_asset") or ""
            oud_bron = (content.get("music") or {}).get("source") or ""
            content["music"] = {"asset": music_uid or None, "title": _s(d.get("music_title")), "source": oud_bron if oud_bron == "custom" and music_uid else ""}
            content.setdefault("sections", {})["music"] = bool(music_uid)
        if content["story"]["text"]:
            content["sections"]["story"] = True
        return content


class EnvelopeForm(StepForm):
    """Envelop & zegel: de Envelope Collection als losse presentatielaag om het ontwerp (catalog/envelop_collectie.py).
    Opgeslagen in style.envelop.collectie; de andere keuzes in style.envelop (kleur, logo) en de rest van het document blijven bewaard.
    Een zegel dat niet bij de gekozen envelop hoort, wordt vervangen door het standaardzegel van die envelop."""

    envelop = forms.ChoiceField(label="Envelop", widget=forms.RadioSelect, required=False)
    zegel = forms.ChoiceField(label="Zegel", widget=forms.RadioSelect, required=False)
    teken = forms.ChoiceField(label="Op het zegel", widget=forms.RadioSelect, required=False,
                              choices=[("standaard", "Het teken van het zegel"), ("initialen", "Jullie initialen")])
    initialen = forms.CharField(label="Initialen op het zegel", max_length=20, required=False,
                                help_text=f"Hoogstens {INITIALEN_COLLECTIE} tekens, bijvoorbeeld S&D. Laat leeg om de initialen voor het zegel uit jullie namen te gebruiken.")

    def __init__(self, *args, template_version, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_version = template_version
        self.fields["initialen"].widget.attrs["maxlength"] = INITIALEN_COLLECTIE    # het zegel toont er niet meer
        self.stijlen = envelop_collectie.beschikbaar(self.occasion)
        self.fields["envelop"].choices = [(envelop_collectie.ONTWERP, "Opening van het ontwerp"), (envelop_collectie.GEEN, "Geen envelop")] + [
            (code, s["naam"]) for code, s in self.stijlen.items()]
        self.fields["zegel"].choices = [(code, z["naam"]) for code, z in envelop_collectie.ZEGELS.items()]
        if not self.is_bound:
            keuze = envelop_collectie.keuze_van(self.content)
            style = self.content.get("style") or {}
            code = keuze["envelop"]
            if code == envelop_collectie.ONTWERP and not style.get("opening", True):
                code = envelop_collectie.GEEN      # een oudere keuze om de openingsanimatie uit te zetten blijft 'geen opening'
            if code not in (envelop_collectie.ONTWERP, envelop_collectie.GEEN) and code not in self.stijlen:
                code = envelop_collectie.ONTWERP
            zegel = keuze["zegel"] if code in self.stijlen and keuze["zegel"] in envelop_collectie.zegels_voor(code) else (
                envelop_collectie.standaard_zegel(code) if code in self.stijlen else "")
            self.initial.update({"envelop": code, "zegel": zegel, "teken": keuze["teken"], "initialen": keuze["initialen"]})

    def clean_initialen(self):
        return envelop.clean_initials(self.cleaned_data.get("initialen"))[:INITIALEN_COLLECTIE].strip()

    def _keuzenaam(self, naam: str) -> str:
        """In de keuzelijst: heet een envelop net als een ontwerp (Midnight Émeraude, Golden Noël), dan komt er 'envelop' achter,
        zodat de klant ze niet verwart. Alleen de zichtbare naam in deze lijst; de stijlnaam en de codes blijven zoals ze zijn."""
        if not hasattr(self, "_ontwerpnamen"):
            self._ontwerpnamen = set(Template.objects.filter(is_active=True).values_list("name", flat=True))
        return f"{naam} envelop" if naam in self._ontwerpnamen else naam

    def opties(self) -> list[dict]:
        """Voor het sjabloon: elke envelop met voorbeeld, tekst en zijn passende zegels."""
        gekozen = self["envelop"].value() or ""
        uit = []
        for code, s in self.stijlen.items():
            uit.append({"code": code, "naam": self._keuzenaam(s["naam"]), "tekst": s["tekst"], "voorbeeld": f"img/envelop/voorbeeld/{code}.webp",
                        "beweging": envelop_collectie.KEUZE[code]["beweging"], "gekozen": gekozen == code,
                        "zegels": envelop_collectie.zegels_voor(code), "standaard": envelop_collectie.standaard_zegel(code)})
        return uit

    def zegel_opties(self) -> list[dict]:
        gekozen_envelop = self["envelop"].value() or ""
        passend = envelop_collectie.zegels_voor(gekozen_envelop) if gekozen_envelop in self.stijlen else []
        keuze = self["zegel"].value() or ""
        uit = []
        for code, z in envelop_collectie.ZEGELS.items():
            welke = [c for c in self.stijlen if code in envelop_collectie.zegels_voor(c)]
            if not welke:
                continue
            naam, regel = ZEGEL_KEUZENAMEN.get(code, (z["naam"], z["materiaal"]))
            uit.append({"code": code, "naam": naam, "materiaal": regel, "voorbeeld": f"img/envelop/zegel/{code}.webp",
                        "envelopen": " ".join(welke), "zichtbaar": code in passend, "gekozen": keuze == code})
        return uit

    def zegel_zichtbaar(self) -> bool:
        return (self["envelop"].value() or "") in self.stijlen

    def ontwerp_opening(self) -> str:
        """Ondertitel bij 'Opening van het ontwerp': de naam van het gekozen ontwerp, geen technische omschrijving."""
        return f"De eigen opening van {self.template_version.template.name}"

    def apply(self, content: dict) -> dict:
        d = self.cleaned_data
        code = d.get("envelop") or envelop_collectie.ONTWERP
        if code not in (envelop_collectie.ONTWERP, envelop_collectie.GEEN) and code not in self.stijlen:
            code = envelop_collectie.ONTWERP
        zegel = d.get("zegel") or ""
        if code in self.stijlen:
            if zegel not in envelop_collectie.zegels_voor(code):
                zegel = envelop_collectie.standaard_zegel(code)
        else:
            zegel = ""
        style = dict(content.get("style") or {})
        keuze = envelop.choice(content)     # de oudere keuzes (kleur, logo) blijven bewaard
        keuze["collectie"] = {"envelop": code, "zegel": zegel, "teken": d.get("teken") or "standaard", "initialen": d.get("initialen") or ""}
        style["envelop"] = keuze
        if code != envelop_collectie.GEEN:
            style["opening"] = True       # wie een envelop (of de opening van het ontwerp) kiest, wil een opening
        content["style"] = style
        return content


class StyleForm(StepForm):
    palette = forms.ChoiceField(label="Kleurvariant", widget=forms.RadioSelect)
    opening = forms.BooleanField(label="Openingsanimatie tonen", required=False,
                                 help_text="Zonder animatie zien gasten direct de inhoud.")
    # Alleen de extra's. Programma, dresscode, praktische info, contact en afsluiting staan bij 'Praktische info': ingevuld = zichtbaar, leeg = weg.
    SECTION_FIELDS = [
        ("countdown", "Afteller"),
        ("story", "Persoonlijk verhaal"),
        ("gallery", "Fotogalerij"),
        ("music", "Muziek"),
    ]

    # Onderdelen die bij een wenskaart niet getoond worden: hun schakelaar verdwijnt en de stand blijft bewaard.
    WENSKAART_HIDDEN = frozenset({"program", "dresscode", "practical", "contact"})

    def __init__(self, *args, template_version, **kwargs):
        super().__init__(*args, **kwargs)
        self.template_version = template_version
        self.hidden_sections = self.WENSKAART_HIDDEN if card_kind(self.content, self.occasion) == "wenskaart" else frozenset()
        if self.content.get("soort") == "wenskaart":
            # Een wenskaart met de vaste prijs: ook geen verhaal, galerij of muziek, en buiten Kerst geen afteller (er is geen datum).
            self.hidden_sections = self.hidden_sections | {"story", "gallery", "music"}
            if not occasion_config(self.occasion).get("event_optional"):
                self.hidden_sections = self.hidden_sections | {"countdown"}
        self.fields["palette"].choices = [(p["key"], p["name"]) for p in template_version.palettes]
        # Bij een ontwerp met de keuze uit de Envelope Collection staat de opening bij Envelop & zegel ('geen envelop' = geen opening).
        self.opening_hier = not (envelop_collectie.modus(template_version) == "optional" and envelop_collectie.beschikbaar(self.occasion))
        if not self.opening_hier:
            del self.fields["opening"]
        for key, label in self.SECTION_FIELDS:
            self.fields[f"s_{key}"] = forms.BooleanField(label=label, required=False)
        # Haarkleur van het bruidspaar (Balzaal): alleen als alle combinaties als beeld bestaan (catalog/paar.py).
        self.hair_enabled = paar.choice_enabled(template_version)
        if self.hair_enabled:
            kleuren = [(k, paar.HAARKLEUR_LABELS.get(k, k.capitalize())) for k in paar.config(template_version)["haarkleuren"]]
            self.fields["haar_man"] = forms.ChoiceField(label="Haarkleur man", choices=kleuren, widget=forms.RadioSelect)
            self.fields["haar_vrouw"] = forms.ChoiceField(label="Haarkleur vrouw", choices=kleuren, widget=forms.RadioSelect)
        # Envelop en lakzegel naar keuze (catalog/envelop.py), alleen bij ontwerpen met een zegel.
        # Alleen keuzes tonen die bij dit ontwerp echt iets veranderen (catalog/envelop.py: zegelkeuzes). Bij een ontwerp dat zelf de
        # Envelope Collection gebruikt zijn envelop- en zegelkleur vast; dan blijft hoogstens het veld voor de initialen over.
        self.keuzes = envelop.zegelkeuzes(template_version)
        self.has_seal = any(v for k, v in self.keuzes.items() if k != "vast")
        self.has_envelope = self.keuzes["env_kleur"]
        if self.keuzes["env_kleur"]:
            self.fields["env_kleur"] = forms.ChoiceField(label="Kleur van de envelop", required=False, widget=forms.RadioSelect,
                                                         choices=[("", "Zoals het ontwerp")] + [(k, v[0]) for k, v in envelop.ENVELOP_KLEUREN.items()])
        if self.keuzes["zegel_kleur"]:
            self.fields["zegel_kleur"] = forms.ChoiceField(label="Kleur van het lakzegel", required=False, widget=forms.RadioSelect,
                                                           choices=[("", "Zoals het ontwerp")] + [(k, v[0]) for k, v in envelop.ZEGEL_KLEUREN.items()])
        if self.keuzes["inhoud"]:
            self.fields["zegel"] = forms.ChoiceField(label="Op het zegel", widget=forms.RadioSelect, required=False,
                                                     choices=list(envelop.ZEGEL_INHOUD.items()))
        if self.keuzes["initialen"]:
            hoogstens = INITIALEN_COLLECTIE if self.keuzes["vast"] else 5
            self.fields["initialen"] = forms.CharField(
                label="Initialen op het zegel", max_length=20, required=False,
                help_text=f"Hoogstens {hoogstens} tekens, bijvoorbeeld S&D. Laat leeg om de initialen voor het zegel uit jullie namen te gebruiken.")
            self.fields["initialen"].widget.attrs["maxlength"] = hoogstens
        if not self.is_bound:
            style = self.content.get("style") or {}
            if self.has_seal:
                keuze = envelop.choice(self.content)
                self.initial.update({"env_kleur": keuze["kleur"], "zegel_kleur": keuze["zegel_kleur"],
                                     "zegel": keuze["zegel"] or "initialen", "initialen": keuze["initialen"]})
            self.initial["palette"] = style.get("palette") or template_version.default_palette_key
            if self.opening_hier:
                self.initial["opening"] = bool(style.get("opening", True))
            for key, _ in self.SECTION_FIELDS:
                self.initial[f"s_{key}"] = bool((self.content.get("sections") or {}).get(key))
            if self.hair_enabled:
                man, vrouw = paar.selection(template_version, self.content)
                self.initial["haar_man"], self.initial["haar_vrouw"] = man, vrouw

    def palette_options(self):
        return [(p, self["palette"]) for p in self.template_version.palettes]

    def section_fields(self):
        return [(key, self[f"s_{key}"]) for key, _ in self.SECTION_FIELDS if key not in self.hidden_sections]

    def apply(self, content: dict) -> dict:
        d = self.cleaned_data
        haar = dict((content.get("style") or {}).get("haar") or {})
        if self.hair_enabled:
            haar = {"man": d["haar_man"], "vrouw": d["haar_vrouw"]}
        # Een eerder gekozen haarkleur blijft bewaard, ook als de keuze (tijdelijk) niet getoond wordt.
        style = dict(content.get("style") or {})  # andere keuzes (eigen gezichten, logo) blijven bewaard
        style.update({"palette": d["palette"], "haar": haar})
        if self.opening_hier:
            style["opening"] = bool(d.get("opening"))
        if self.has_seal:
            # Alleen de keuzes die dit ontwerp toont worden overschreven; een eerdere stand van de rest blijft bewaard.
            keuze = envelop.choice(content)
            if "zegel_kleur" in self.fields:
                keuze["zegel_kleur"] = d.get("zegel_kleur") or ""
            if "zegel" in self.fields:
                keuze["zegel"] = d.get("zegel") or "initialen"
            if "initialen" in self.fields:
                keuze["initialen"] = envelop.clean_initials(d.get("initialen"))[: INITIALEN_COLLECTIE if self.keuzes["vast"] else 5].strip()
            if "env_kleur" in self.fields:
                keuze["kleur"] = d.get("env_kleur") or ""
            style["envelop"] = keuze
        content["style"] = style
        sections = content.setdefault("sections", {})
        for key, _ in self.SECTION_FIELDS:
            if key not in self.hidden_sections:
                sections[key] = bool(d.get(f"s_{key}"))
        return content


class CheckoutForm(forms.Form):
    package = forms.ChoiceField(label="Pakket", widget=forms.RadioSelect)
    extras = forms.MultipleChoiceField(label="Extra opties", required=False, widget=forms.CheckboxSelectMultiple)
    terms = forms.BooleanField(label="Ik ga akkoord met de voorwaarden", required=False)
    nieuwsbrief = forms.BooleanField(required=False)  # los van de voorwaarden, standaard uit
    direct_leveren = forms.BooleanField(required=False)  # afzonderlijke toestemming digitale kaart (voorwaarden, artikel 9.2)
    online_dienst = forms.BooleanField(required=False)   # afzonderlijk verzoek om de online beschikbaarheid direct te starten (artikel 9.3)

    def __init__(self, *args, packages, optional, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["package"].choices = [(p.code, p.name) for p in packages]
        self.fields["extras"].choices = [(a.code, a.name) for a in optional]

    def clean_terms(self):
        if not self.cleaned_data.get("terms"):
            raise forms.ValidationError("Ga akkoord met de algemene voorwaarden om te kunnen bestellen.")
        return True

    def clean_direct_leveren(self):
        if not self.cleaned_data.get("direct_leveren"):
            raise forms.ValidationError("Geef toestemming voor directe levering van je digitale kaart; anders kunnen we je kaart niet direct na je betaling beschikbaar maken.")
        return True

    def clean_online_dienst(self):
        if not self.cleaned_data.get("online_dienst"):
            raise forms.ValidationError("Geef aan dat de online beschikbaarheid direct mag starten; anders kunnen we je uitnodiging niet direct na je betaling online zetten.")
        return True


FORM_CLASSES = {
    "envelop": EnvelopeForm,
    "gegevens": DetailsForm,
    "programma": ProgramForm,
    "aanmelden": RsvpSettingsForm,
    "fotos": PhotosForm,
    "stijl": StyleForm,
}


def today() -> date:
    return timezone.localdate()

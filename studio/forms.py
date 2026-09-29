"""Formulieren per stap. Elk formulier leest uit en schrijft naar het inhoudsdocument.

Velden zijn formeel optioneel, zodat 'Opslaan en later verder' altijd werkt.
Bij 'Volgende' controleert `missing()` of de verplichte gegevens van de stap
compleet zijn; ingevulde gegevens worden dan toch bewaard.
"""
from __future__ import annotations

import re
import secrets
from datetime import date, timedelta

from django import forms
from django.utils import timezone

from catalog import envelop, paar
from catalog.occasions import OCCASION_CHOICES, occasion_config
from invitations.content import (
    MAX_PRACTICAL_ITEMS,
    MAX_PROGRAM_ITEMS,
    MAX_QUESTIONS,
    QUESTION_TYPES,
    SOORTEN,
    TIMEZONES,
    card_kind,
    event_expected,
    parse_date,
)

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cfg = occasion_config(self.occasion)
        self.event_optional = bool(cfg.get("event_optional"))
        if self.event_optional:
            self.fields["venue_name"].help_text = "Bijvoorbeeld 'Bij ons thuis' of de naam van het restaurant."
            # Uitnodiging (met datum, locatie en aanmelden) of wenskaart (alleen een groet).
            self.fields["soort"] = forms.ChoiceField(
                label="Wat voor kaart wordt het?", choices=[(s, s) for s in SOORTEN], required=False, widget=forms.RadioSelect)
            if not self.is_bound:
                self.initial["soort"] = card_kind(self.content, self.occasion)
        self.name_keys = []
        new_fields = {}
        for key, label, required, max_len, help_text in cfg["name_fields"]:
            name = f"name_{key}"
            self.name_keys.append((name, key, label, required))
            if key in ("age", "years"):
                field = forms.IntegerField(label=label, required=False, min_value=1, max_value=150, help_text=help_text,
                                           error_messages={"invalid": "Vul een getal in.", "min_value": "Vul een getal vanaf 1 in.",
                                                           "max_value": "Vul een realistisch getal in."})
            else:
                field = forms.CharField(label=label, required=False, max_length=max_len, help_text=help_text)
            field.widget.attrs["data-required"] = "1" if required else ""
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
        if self.event_optional:
            content["soort"] = d.get("soort") if d.get("soort") in SOORTEN else card_kind(content, self.occasion)
        return content

    def missing(self) -> dict[str, str]:
        d = self.cleaned_data
        errors = {}
        for name, key, label, required in self.name_keys:
            if required and not _s(d.get(name)):
                errors[name] = f"Vul '{label.lower()}' in."
        # Bij een kerstkaart is het evenement optioneel: een wenskaart heeft geen datum of locatie nodig.
        # Zonder keuze (oudere formulieren) geldt: leeg laten is een wenskaart.
        if self.event_optional:
            soort = d.get("soort")
            if soort == "wenskaart":
                return errors
            if soort != "uitnodiging" and not any(_s(d.get(k)) for k in ("date", "start_time", "end_time", "venue_name", "address")):
                return errors
        if not d.get("date"):
            errors["date"] = "Vul de datum in."
        if not d.get("start_time"):
            errors["start_time"] = "Vul de begintijd in."
        if not _s(d.get("venue_name")):
            errors["venue_name"] = "Vul de naam van de locatie in."
        return errors


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
        if self.only_closing:
            content["closing_text"] = _s(d.get("closing_text"))
            return content
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
    enabled = forms.BooleanField(label="Gasten kunnen zich aanmelden via de uitnodiging", required=False)
    deadline = forms.DateField(label="Aanmelden kan tot en met", required=False, widget=DATE_WIDGET,
                               error_messages={"invalid": "Vul een geldige datum in."})
    max_party_size = forms.IntegerField(label="Maximaal aantal personen per aanmelding", min_value=1, max_value=10, initial=2,
                                        help_text="Inclusief de gast zelf. Kies 1 als iedere gast alleen zichzelf aanmeldt.",
                                        error_messages={"min_value": "Minimaal 1.", "max_value": "Maximaal 10.", "invalid": "Vul een getal in."})
    capacity = forms.IntegerField(label="Maximaal aantal gasten in totaal (optioneel)", min_value=1, max_value=5000, required=False,
                                  help_text="Als dit aantal is bereikt, sluit het aanmelden automatisch.",
                                  error_messages={"min_value": "Minimaal 1.", "invalid": "Vul een getal in."})
    ask_remark = forms.BooleanField(label="Gasten kunnen een toelichting meesturen", required=False)
    remark_label = forms.CharField(label="Vraag bij de toelichting", max_length=120, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        c = self.content
        rsvp = c.get("rsvp") or {}
        questions = list(rsvp.get("questions") or [])
        self.question_rows = MAX_QUESTIONS
        for i in range(self.question_rows):
            self.fields[f"q{i}_id"] = forms.CharField(required=False, widget=forms.HiddenInput, max_length=12)
            self.fields[f"q{i}_label"] = forms.CharField(label="Vraag", max_length=140, required=False)
            self.fields[f"q{i}_type"] = forms.ChoiceField(label="Soort antwoord", choices=QUESTION_TYPES, required=False)
            self.fields[f"q{i}_options"] = forms.CharField(label="Keuzes (gescheiden door komma's)", max_length=300, required=False)
            self.fields[f"q{i}_required"] = forms.BooleanField(label="Verplicht", required=False)
        if not self.is_bound:
            self.initial["enabled"] = bool((c.get("sections") or {}).get("rsvp"))
            self.initial["deadline"] = parse_date(rsvp.get("deadline"))
            self.initial["max_party_size"] = rsvp.get("max_party_size") or 2
            self.initial["capacity"] = rsvp.get("capacity")
            self.initial["ask_remark"] = bool(rsvp.get("ask_remark", True))
            self.initial["remark_label"] = rsvp.get("remark_label") or "Wil je nog iets laten weten?"
            for i, q in enumerate(questions[: self.question_rows]):
                self.initial[f"q{i}_id"] = q.get("id", "")
                self.initial[f"q{i}_label"] = q.get("label", "")
                self.initial[f"q{i}_type"] = q.get("type", "text")
                self.initial[f"q{i}_options"] = ", ".join(q.get("options") or [])
                self.initial[f"q{i}_required"] = bool(q.get("required"))

    @property
    def question_fields(self):
        return [
            (self[f"q{i}_id"], self[f"q{i}_label"], self[f"q{i}_type"], self[f"q{i}_options"], self[f"q{i}_required"])
            for i in range(self.question_rows)
        ]

    def clean(self):
        data = super().clean()
        event_day = parse_date(self.content.get("date"))
        deadline = data.get("deadline")
        if deadline and event_day and deadline > event_day:
            self.add_error("deadline", "De deadline moet op of vóór de datum van het evenement liggen.")
        for i in range(self.question_rows):
            label = _s(data.get(f"q{i}_label"))
            qtype = data.get(f"q{i}_type") or "text"
            options = [o.strip() for o in _s(data.get(f"q{i}_options")).split(",") if o.strip()]
            if label and qtype == "choice" and len(options) < 2:
                self.add_error(f"q{i}_options", "Geef minimaal twee keuzes, gescheiden door komma's.")
        return data

    def apply(self, content: dict) -> dict:
        d = self.cleaned_data
        content.setdefault("sections", {})["rsvp"] = bool(d.get("enabled"))
        questions = []
        for i in range(self.question_rows):
            label = _s(d.get(f"q{i}_label"))
            if not label:
                continue
            qid = re.sub(r"[^a-z0-9]", "", _s(d.get(f"q{i}_id")).lower())[:12] or "q" + secrets.token_hex(3)
            qtype = d.get(f"q{i}_type") or "text"
            options = [o.strip()[:60] for o in _s(d.get(f"q{i}_options")).split(",") if o.strip()][:8]
            questions.append({"id": qid, "label": label, "type": qtype, "options": options if qtype == "choice" else [],
                              "required": bool(d.get(f"q{i}_required"))})
        content["rsvp"] = {
            "deadline": d["deadline"].isoformat() if d.get("deadline") else "",
            "max_party_size": d.get("max_party_size") or 1,
            "capacity": d.get("capacity"),
            "ask_remark": bool(d.get("ask_remark")),
            "remark_label": _s(d.get("remark_label")) or "Wil je nog iets laten weten?",
            "questions": questions,
        }
        return content

    def missing(self) -> dict[str, str]:
        d = self.cleaned_data
        # Een kerstkaart zonder evenement toont geen aanmelden; dan is ook geen deadline nodig.
        if d.get("enabled") and not d.get("deadline") and event_expected(self.content, self.occasion):
            return {"deadline": "Kies tot wanneer gasten zich kunnen aanmelden."}
        return {}


class PhotosForm(StepForm):
    hero = forms.ChoiceField(label="Hoofdfoto", required=False, widget=forms.RadioSelect)
    story_title = forms.CharField(label="Titel van het verhaal", max_length=60, required=False)
    story_text = forms.CharField(label="Jullie verhaal (optioneel)", max_length=2000, required=False,
                                 widget=forms.Textarea(attrs={"rows": 6, "data-ai-field": "story"}))
    music_asset = forms.ChoiceField(label="Muziek", required=False, widget=forms.RadioSelect)
    music_title = forms.CharField(label="Titel en artiest (optioneel)", max_length=80, required=False)
    music_rights = forms.BooleanField(label="Ik heb toestemming om deze muziek op mijn uitnodiging te gebruiken", required=False)

    def __init__(self, *args, photos, audio, **kwargs):
        self.photos = list(photos)
        self.audio = list(audio)
        super().__init__(*args, **kwargs)
        c = self.content
        self.fields["hero"].choices = [("", "Geen hoofdfoto")] + [(str(p.uid), p.original_name or "Foto") for p in self.photos]
        self.fields["music_asset"].choices = [("", "Geen muziek")] + [(str(a.uid), a.original_name or "Muziek") for a in self.audio]
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
            self.initial["music_asset"] = str(music.get("asset") or "")
            self.initial["music_title"] = music.get("title", "")
            self.initial["music_rights"] = bool(music.get("asset"))

    def photo_rows(self):
        rows = []
        for p in self.photos:
            uid = str(p.uid)
            rows.append({"asset": p, "uid": uid, "gallery": self[f"g_{uid}"], "x": self[f"x_{uid}"], "y": self[f"y_{uid}"],
                         "zoom": self[f"z_{uid}"], "caption": self[f"c_{uid}"]})
        return rows

    def clean(self):
        data = super().clean()
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
        music_uid = d.get("music_asset") or ""
        content["music"] = {"asset": music_uid or None, "title": _s(d.get("music_title"))}
        content.setdefault("sections", {})["music"] = bool(music_uid)
        if content["story"]["text"]:
            content["sections"]["story"] = True
        return content


class StyleForm(StepForm):
    palette = forms.ChoiceField(label="Kleurvariant", widget=forms.RadioSelect)
    opening = forms.BooleanField(label="Openingsanimatie tonen", required=False,
                                 help_text="Gasten openen de uitnodiging met een tik. Zonder animatie zien ze direct de inhoud.")
    SECTION_FIELDS = [
        ("countdown", "Afteller"),
        ("program", "Programma"),
        ("dresscode", "Dresscode"),
        ("practical", "Praktische informatie"),
        ("contact", "Contactpersoon"),
        ("closing", "Afsluitende tekst"),
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
        self.fields["palette"].choices = [(p["key"], p["name"]) for p in template_version.palettes]
        for key, label in self.SECTION_FIELDS:
            self.fields[f"s_{key}"] = forms.BooleanField(label=label, required=False)
        # Haarkleur van het bruidspaar (Balzaal): alleen als alle combinaties als beeld bestaan (catalog/paar.py).
        self.hair_enabled = paar.choice_enabled(template_version)
        if self.hair_enabled:
            kleuren = [(k, paar.HAARKLEUR_LABELS.get(k, k.capitalize())) for k in paar.config(template_version)["haarkleuren"]]
            self.fields["haar_man"] = forms.ChoiceField(label="Haarkleur man", choices=kleuren, widget=forms.RadioSelect)
            self.fields["haar_vrouw"] = forms.ChoiceField(label="Haarkleur vrouw", choices=kleuren, widget=forms.RadioSelect)
        # Envelop en lakzegel naar keuze (catalog/envelop.py), alleen bij ontwerpen met een zegel.
        self.has_seal = envelop.has_seal(template_version)
        self.has_envelope = envelop.has_envelope(template_version)
        if self.has_envelope:
            self.fields["env_kleur"] = forms.ChoiceField(label="Kleur van de envelop", required=False, widget=forms.RadioSelect,
                                                         choices=[("", "Zoals het ontwerp")] + [(k, v[0]) for k, v in envelop.ENVELOP_KLEUREN.items()])
        if self.has_seal:
            self.fields["zegel_kleur"] = forms.ChoiceField(label="Kleur van het lakzegel", required=False, widget=forms.RadioSelect,
                                                           choices=[("", "Zoals het ontwerp")] + [(k, v[0]) for k, v in envelop.ZEGEL_KLEUREN.items()])
            self.fields["zegel"] = forms.ChoiceField(label="Op het zegel", widget=forms.RadioSelect, required=False,
                                                     choices=list(envelop.ZEGEL_INHOUD.items()))
            self.fields["initialen"] = forms.CharField(label="Initialen op het zegel", max_length=20, required=False,
                                                       help_text="Hoogstens 5 tekens, bijvoorbeeld S&D. Leeg: we maken ze uit jullie namen.")
        if not self.is_bound:
            style = self.content.get("style") or {}
            if self.has_seal:
                keuze = envelop.choice(self.content)
                self.initial.update({"env_kleur": keuze["kleur"], "zegel_kleur": keuze["zegel_kleur"],
                                     "zegel": keuze["zegel"] or "initialen", "initialen": keuze["initialen"]})
            self.initial["palette"] = style.get("palette") or template_version.default_palette_key
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
        style.update({"palette": d["palette"], "opening": bool(d.get("opening")), "haar": haar})
        if self.has_seal:
            keuze = envelop.choice(content)
            keuze.update({"zegel_kleur": d.get("zegel_kleur") or "", "zegel": d.get("zegel") or "initialen",
                          "initialen": envelop.clean_initials(d.get("initialen"))})
            if self.has_envelope:
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
    direct_leveren = forms.BooleanField(required=False)  # afzonderlijke toestemming (voorwaarden, artikel 9.2)

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
            raise forms.ValidationError("Geef aan dat we direct na je betaling mogen leveren; anders kunnen we je kaart niet direct publiceren.")
        return True


FORM_CLASSES = {
    "gegevens": DetailsForm,
    "programma": ProgramForm,
    "aanmelden": RsvpSettingsForm,
    "fotos": PhotosForm,
    "stijl": StyleForm,
}


def today() -> date:
    return timezone.localdate()

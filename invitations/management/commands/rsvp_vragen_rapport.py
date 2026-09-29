"""Telt welke bestaande uitnodigingen nog eigen vragen of een eigen toelichtingsvraag hebben (van vóór de vaste lijst).

Alleen aantallen: geen vraagteksten, namen, antwoorden of links. Verandert niets. Draai vóór de livegang ook op de
server met echte gegevens (op Render: Shell → python manage.py rsvp_vragen_rapport). Zie docs/PRIVACY.md.

Het risico wordt bepaald aan de hand van trefwoorden in de vraagteksten en antwoordopties van de organisator. De
antwoorden van gasten worden niet doorzocht; wel wordt geteld hoeveel aanmeldingen een antwoord of toelichting bevatten.
"""
import json
import re

from django.core.management.base import BaseCommand

from invitations.models import GuestResponse, Invitation
from invitations.vragen import eigen_toelichting, eigen_vragen

TREFWOORDEN = {
    "gezondheid of dieet": r"dieet|allergi|gluten|lactose|noten|pinda|vega|veganis|medisch|medicijn|gezondheid|zwanger|diabet|suiker|intoleran",
    "geloof of levensovertuiging": r"geloof|religi|halal|koosjer|kosher|kerk|moskee|synago|gebed|ramadan|vasten",
    "toegankelijkheid of beperking": r"rolstoel|beperking|toegankelijk|slechthorend|slechtziend|mobiliteit|invalide",
}


def _categorie(text: str) -> list[str]:
    text = (text or "").lower()
    return [naam for naam, patroon in TREFWOORDEN.items() if re.search(patroon, text)]


class Command(BaseCommand):
    help = "Telt oude eigen aanmeldvragen en het risico daarvan (alleen aantallen, verandert niets)."

    def handle(self, *args, **options):
        rapport = {
            "uitnodigingen": Invitation.objects.count(),
            "met_eigen_vragen": {"concept": 0, "gepubliceerd": 0},
            "eigen_vragen": {"totaal": 0, "open": 0, "ja_nee": 0, "keuze": 0, "verplicht": 0},
            "eigen_vragen_per_risico": {naam: 0 for naam in TREFWOORDEN},
            "met_eigen_toelichtingsvraag": {"concept": 0, "gepubliceerd": 0, "met_risicowoord": 0},
            "gepubliceerd_per_status": {},
            "aanmeldingen": {"totaal": GuestResponse.objects.count(), "met_antwoord_op_eigen_vraag": 0,
                             "met_antwoord_op_risicovraag": 0, "met_ingevulde_toelichting": 0},
        }
        risico_ids: dict[int, set] = {}
        eigen_ids: dict[int, set] = {}
        for inv in Invitation.objects.select_related("published_version"):
            bronnen = [("concept", inv.draft_content or {})]
            if inv.published_version:
                bronnen.append(("gepubliceerd", inv.published_version.content or {}))
            for soort, content in bronnen:
                rsvp = content.get("rsvp") or {}
                oud = eigen_vragen(rsvp.get("questions"))
                if oud:
                    rapport["met_eigen_vragen"][soort] += 1
                    if soort == "gepubliceerd":
                        per_status = rapport["gepubliceerd_per_status"]
                        per_status[inv.status] = per_status.get(inv.status, 0) + 1
                if eigen_toelichting(rsvp):
                    rapport["met_eigen_toelichtingsvraag"][soort] += 1
                    if soort == "gepubliceerd" and _categorie(rsvp.get("remark_label")):
                        rapport["met_eigen_toelichtingsvraag"]["met_risicowoord"] += 1
                if soort != "gepubliceerd":
                    continue
                for q in oud:
                    stats = rapport["eigen_vragen"]
                    stats["totaal"] += 1
                    stats[{"yesno": "ja_nee", "choice": "keuze"}.get(q.get("type"), "open")] += 1
                    stats["verplicht"] += bool(q.get("required"))
                    eigen_ids.setdefault(inv.pk, set()).add(q.get("id"))
                    categorieen = _categorie(" ".join([str(q.get("label") or "")] + [str(o) for o in q.get("options") or []]))
                    for naam in categorieen:
                        rapport["eigen_vragen_per_risico"][naam] += 1
                    if categorieen:
                        risico_ids.setdefault(inv.pk, set()).add(q.get("id"))
        stats = rapport["aanmeldingen"]
        for response in GuestResponse.objects.only("invitation_id", "answers", "remark").iterator():
            gegeven = {a.get("id") for a in response.answers or [] if a.get("value")}
            if gegeven & eigen_ids.get(response.invitation_id, set()):
                stats["met_antwoord_op_eigen_vraag"] += 1
            if gegeven & risico_ids.get(response.invitation_id, set()):
                stats["met_antwoord_op_risicovraag"] += 1
            if (response.remark or "").strip():
                stats["met_ingevulde_toelichting"] += 1
        self.stdout.write(json.dumps(rapport, indent=2, ensure_ascii=False))

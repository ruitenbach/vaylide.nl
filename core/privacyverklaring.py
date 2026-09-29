"""De privacyverklaring: feiten uit de inrichting, besluiten van de eigenaar en een controle vóór livegang.

Niets verzonnen. Aanbieders staan alleen in de verklaring als de koppeling echt is ingesteld (zie `suppliers`).
Besluiten die de eigenaar (met een jurist) nog moet nemen staan in BESLUITEN met de waarde None: op de afgeschermde
testversie verschijnen ze als geel invulveld, en in live-modus weigert `manage.py check` (en dus `migrate` bij het
starten op Render) zolang er nog iets open staat. Zie docs/PRIVACY.md.
"""
from __future__ import annotations

from datetime import date

from django.conf import settings
from django.core import checks

VERSION = date(2026, 9, 30)

# Door de eigenaar vast te stellen. None = nog open (invulveld op de testversie, blokkeert live).
# Voorstellen met onderbouwing: docs/PRIVACY.md, onder "Besluiten".
BESLUITEN: dict[str, str | None] = {
    # Rol en grondslag bij gastgegevens (onderdeel 4), apart voor particuliere en zakelijke organisatoren.
    "rol_gasten": None,
    # Grondslag voor gegevens van anderen in de kaartinhoud (namen, foto's, contactpersoon).
    "grondslag_kaartinhoud": None,
    # Wat mag een organisator vragen met eigen vragen (bijv. dieetwensen of allergieën = mogelijk gezondheidsgegevens)?
    "gevoelige_vragen": None,
    # Bewaartermijnen die de code nog niet uitvoert.
    "bewaar_account": None,
    "bewaar_gekochte_kaarten": None,
    "bewaar_contact": None,
    "bewaar_herroepingen": None,
    "bewaar_wensen": None,
    "bewaar_emails": None,
    "bewaar_logs": None,
}

LABELS = {
    "rol_gasten": "rol en grondslag bij gastgegevens",
    "grondslag_kaartinhoud": "grondslag voor gegevens van anderen op de kaart",
    "gevoelige_vragen": "beleid voor gevoelige eigen vragen bij aanmelden",
    "bewaar_account": "bewaartermijn accounts",
    "bewaar_gekochte_kaarten": "bewaartermijn gekochte kaarten en foto's na de looptijd",
    "bewaar_contact": "bewaartermijn contactberichten",
    "bewaar_herroepingen": "bewaartermijn herroepingen",
    "bewaar_wensen": "bewaartermijn extra wensen (maatwerk)",
    "bewaar_emails": "bewaartermijn verstuurde e-mails",
    "bewaar_logs": "bewaartermijn logbestanden bij de hostingpartij",
    "email_aanbieder": "e-maildienst (naam en vestigingsland; kies een aanbieder in de EER of vul onderdeel 8 aan)",
    "backup_aanbieder": "aanbieder tweede back-uplocatie (naam en vestigingsland; in de EER of onderdeel 8 aanvullen)",
    "ai_afspraken": "afspraken met Anthropic (verwerkersovereenkomst en doorgifte buiten de EER)",
    "gezichten": "de functie eigen gezichten staat aan, maar de gegevensverwerking is niet beoordeeld",
}


def ai_active() -> bool:
    from .ai import ai_configured

    return ai_configured()


def email_active() -> bool:
    return settings.EMAIL_MODE == "smtp"


def backup_offsite_active() -> bool:
    from .offsite import configured

    return configured()


def suppliers() -> list[dict]:
    """Alleen partijen die met de huidige instellingen echt persoonsgegevens ontvangen."""
    rows = [{
        "naam": "Render Services, Inc. (Verenigde Staten)",
        "dienst": "Hosting van de website, de database, de opslag van foto's en bestanden en de back-ups op de server",
        "gegevens": "Alle gegevens in deze verklaring, want die staan op de servers. De server en de database staan in "
                    "de regio Frankfurt (Duitsland).",
        "rol": "Verwerker",
        "doorgifte": "Render is een Amerikaans bedrijf. Volgens de verwerkersovereenkomst van Render gelden de "
                     "EU-standaardcontractbepalingen en/of het EU-VS Data Privacy Framework.",
    }]
    if settings.PAYMENT_PROVIDER == "mollie":
        rows.append({
            "naam": "Mollie B.V. (Nederland)",
            "dienst": "Betalingen",
            "gegevens": "Bedrag, bestelnummer en een interne betaalcode. Je betaalgegevens (zoals je bank, kaart of "
                        "PayPal-account) vul je bij Mollie in; die krijgen wij niet te zien, behalve de gekozen "
                        "betaalmethode en de uitkomst.",
            "rol": "Zelfstandig verwerkingsverantwoordelijke voor de betaling (volgens Mollie)",
            "doorgifte": "",
        })
    if email_active():
        rows.append({
            "naam": settings.PRIVACY_EMAIL_PROVIDER or None,
            "dienst": "Versturen van inlogcodes, bestelbevestigingen en andere servicemails",
            "gegevens": "Je e-mailadres en de inhoud van het bericht.",
            "rol": "Verwerker",
            "doorgifte": "",
        })
    if backup_offsite_active():
        rows.append({
            "naam": settings.PRIVACY_BACKUP_PROVIDER or None,
            "dienst": "Tweede back-uplocatie",
            "gegevens": "Een versleutelde kopie van de database en de geüploade bestanden. De sleutel om die kopie te "
                        "openen heeft de aanbieder niet.",
            "rol": "Verwerker",
            "doorgifte": "",
        })
    if ai_active():
        rows.append({
            "naam": "Anthropic PBC (Verenigde Staten)",
            "dienst": "Tekstvoorstellen (alleen als je daar zelf om vraagt) en een interne samenvatting van extra wensen",
            "gegevens": "Wat je voor het voorstel invult en de gegevens van je kaart die daarvoor nodig zijn (zoals "
                        "namen, datum en locatie), of het onderwerp en de omschrijving van je extra wens. Geen foto's of "
                        "bijlagen.",
            "rol": "Verwerker",
            "doorgifte": settings.PRIVACY_AI_AFSPRAKEN or None,
        })
    return rows


def cookies() -> list[dict]:
    return [
        {"naam": "vierlief_sessie", "soort": "Cookie", "doel": "Houdt je ingelogd en bewaart je ontwerp tijdens het maken.",
         "duur": "30 dagen"},
        {"naam": "vierlief_csrf", "soort": "Cookie", "doel": "Beveiliging: controleert dat een formulier echt van onze site komt.",
         "duur": "1 jaar"},
        {"naam": "vierlief_antwoord", "soort": "Cookie (alleen op de uitnodiging waarop je reageerde)",
         "doel": "Zodat je je eigen antwoord later kunt terugzien, wijzigen of verwijderen.", "duur": "1 jaar"},
        {"naam": "vierlief-open:…", "soort": "Sessieopslag in je browser",
         "doel": "Onthoudt dat je de envelop van een uitnodiging al opende, zodat je die niet steeds opnieuw ziet.",
         "duur": "Tot je het tabblad sluit"},
        {"naam": "vierlief-beweging", "soort": "Lokale opslag in je browser",
         "doel": "Onthoudt of je bewegende effecten op een uitnodiging hebt uitgezet. Alleen als je daarop tikt.",
         "duur": "Tot je het wist of weer aanzet"},
    ]


def open_points() -> list[str]:
    """Wat er nog ontbreekt voordat de verklaring gepubliceerd mag worden."""
    from .company import company

    points = [LABELS[key] for key, value in BESLUITEN.items() if not value]
    points += company()["ontbreekt"]
    if email_active() and not settings.PRIVACY_EMAIL_PROVIDER:
        points.append(LABELS["email_aanbieder"])
    if backup_offsite_active() and not settings.PRIVACY_BACKUP_PROVIDER:
        points.append(LABELS["backup_aanbieder"])
    if ai_active() and not settings.PRIVACY_AI_AFSPRAKEN:
        points.append(LABELS["ai_afspraken"])
    if settings.FACES_ENABLED:
        points.append(LABELS["gezichten"])
    return points


@checks.register(checks.Tags.compatibility)
def check_privacy_statement(app_configs=None, **kwargs):
    """Live-modus: geen privacyverklaring met invulvelden of onbeoordeelde functies."""
    if settings.TEST_MODE:
        return []
    missing = open_points()
    if not missing:
        return []
    return [checks.Error(
        "De privacyverklaring is nog niet af: " + "; ".join(missing) + ".",
        hint="Vul de besluiten in core/privacyverklaring.py en de instellingen in (zie docs/PRIVACY.md).",
        id="vaylide.E001",
    )]

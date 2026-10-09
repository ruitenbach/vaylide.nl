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
    # Besloten door de eigenaar op 01-10-2026 (beslislijst A1, voorstel overgenomen; juridische toets staat nog open).
    "rol_gasten": "De organisator bepaalt of gasten zich kunnen aanmelden, welke vragen uit onze vaste lijst worden gesteld "
                  "en wat er met de antwoorden gebeurt. Wij bewaren en tonen de antwoorden alleen voor de organisator en "
                  "gebruiken ze niet voor eigen doelen. Daarvoor werken wij als verwerker voor de organisator. Organiseert "
                  "iemand een feest in de privésfeer, dan geldt de AVG vaak niet voor die organisator zelf, maar wel voor "
                  "ons; wij houden ons dan aan dezelfde verplichtingen. Voor onze eigen doelen, zoals het beveiligen van de "
                  "site en het tegengaan van misbruik, zijn wij zelf verantwoordelijk.",
    # A2 (01-10-2026).
    "grondslag_kaartinhoud": "Wij verwerken deze inhoud als verwerker voor jou, zoals bij aanmeldingen (onderdeel 4). Jij "
                             "zorgt dat je de gegevens en foto's van anderen op je kaart mag gebruiken (artikel 12 van de "
                             "algemene voorwaarden).",
    # Besloten door de eigenaar op 30-09-2026 (optie A): alleen vaste, neutrale extra vragen (invitations/vragen.py).
    "gevoelige_vragen": "Extra vragen kiest de organisator uit onze vaste lijst met neutrale vragen, zoals over vervoer of "
                        "overnachten. Via VAYLIDE wordt niet gevraagd naar gezondheid, allergieën, geloof of andere "
                        "gevoelige gegevens, en bij open tekstvelden staat dat je die daar ook niet moet invullen.",
    # Bewaartermijnen B1 tot en met B6 (01-10-2026), uitgevoerd door apply_retention in core/privacy.py. De financiële
    # administratie (bestelling, regels, betalingen) blijft 7 jaar; inhoud, bijlagen en correspondentie niet.
    "bewaar_account": "Gebruik je je account 24 maanden niet en heb je geen kaarten meer bij ons, dan verwijderen wij je "
                      "naam en e-mailadres. Je krijgt 30 dagen van tevoren een e-mail; log je in, dan blijft je account "
                      "bestaan (automatisch).",
    "bewaar_gekochte_kaarten": "90 dagen nadat de kaart offline ging verwijderd, met foto's, muziek en andere inhoud "
                               "(automatisch). De bestelling zelf blijft bewaard voor de administratie.",
    "bewaar_contact": "12 maanden na ontvangst verwijderd (automatisch)",
    "bewaar_herroepingen": "7 jaar, net als de bestelgegevens waar ze bij horen; daarna verwijderd (automatisch)",
    "bewaar_wensen": "12 maanden na afronden verwijderd, met berichten en bijlagen (automatisch). Leidde de wens tot een "
                     "betaling, dan blijven alleen de bestel- en betaalgegevens 7 jaar bewaard.",
    "bewaar_emails": "90 dagen; daarna verwijderen wij de inhoud en het adres van de kopie (automatisch)",
    # B7 (01-10-2026): Render bewaart logs 7 dagen bij het Hobby-abonnement van de werkruimte (render.com/docs/logging:
    # Hobby 7, Pro 14, Scale/Enterprise 30 dagen). Ander abonnement? Pas deze termijn dan aan.
    "bewaar_logs": "7 dagen bij onze hostingpartij Render; daarna verwijdert Render ze automatisch",
}

# Microsoft Clarity (bezoekersanalyse, alleen na toestemming). Staat hier iets op None, dan is de tekst een open juridisch besluit: de
# testversie toont hem als concept met een gele markering en in live-modus start de site niet met VIERLIEF_CLARITY_ID.
# Rol en bewaartermijn zijn ingevuld uit de officiële FAQ van Clarity (learn.microsoft.com/clarity/faq, bijgewerkt 21-09-2026): "Clarity is
# GDPR-compliant as a data controller"; "Clarity retains recordings for 30 days ... Favorite recordings and randomly selected sample of
# recordings are retained for up to 9 months"; "You can access heat maps for up to 9 months"; "Labels can be retained for up to 9 months".
# De bewaartermijn staat als volledige zinnen in onderdeel 9 en 10. Verandert de tekst inhoudelijk, zet "goedgekeurd" dan weer op None
# tot de nieuwe tekst is beoordeeld.
CLARITY_BESLUITEN: dict[str, str | None] = {
    "goedgekeurd": "Goedgekeurd door de eigenaar op 08-10-2026",
    "rol_microsoft": "Zelfstandig verwerkingsverantwoordelijke (volgens Microsoft)",
    "bewaartermijn": "Microsoft Clarity bewaart afspeelgegevens van sessieopnames 30 dagen. Klikgegevens en heatmapgegevens worden tot "
                     "9 maanden bewaard. Gelabelde of als favoriet gemarkeerde sessies en een willekeurig gekozen steekproef van "
                     "sessieopnames worden tot 9 maanden bewaard. Dit zijn de termijnen volgens Microsoft.",
}
CLARITY_TEKST_GOEDGEKEURD = all(CLARITY_BESLUITEN.values())

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
    "clarity": "tekst over Microsoft Clarity (bezoekersanalyse, cookies, doorgifte naar de VS) juridisch beoordelen en goedkeuren",
    "google": "tekst over Google Analytics 4 en Google Tag Manager (bezoekersanalyse, cookies, doorgifte naar de VS) juridisch beoordelen en goedkeuren",
}


def ai_active() -> bool:
    from .ai import ai_configured

    return ai_configured()


def email_active() -> bool:
    return settings.EMAIL_MODE == "smtp"


def clarity_active() -> bool:
    return bool(settings.CLARITY_ID)


def google_active() -> bool:
    return bool(settings.GTM_ID)


# Google Analytics 4 via Google Tag Manager (alleen na toestemming). In live-modus start de site niet met VIERLIEF_GTM_ID zolang dit niet True is.
# Goedgekeurd door de eigenaar op 10-10-2026 (de tekst in privacy.html over Google Analytics en Google Tag Manager, met IP-adres en bewaartermijn zoals in GA4 ingesteld).
# Verandert die tekst inhoudelijk, zet dit dan weer op False.
GOOGLE_TEKST_GOEDGEKEURD = True


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
    if clarity_active():
        rows.append({
            "naam": "Microsoft Ireland Operations Limited (Ierland) en Microsoft Corporation (Verenigde Staten)",
            "dienst": "Bezoekersanalyse met Microsoft Clarity, alleen als je daar toestemming voor geeft",
            "gegevens": "Gebruiksgegevens van je bezoek: je IP-adres en de globale locatie die Microsoft daaruit afleidt, welke pagina's "
                        "je bekijkt (met het volledige adres en de titel), de opbouw van de pagina met willekeurige codes van je ontwerp en "
                        "foto's, klikken, scrollen, muisbewegingen en hoe je navigeert, je apparaat en browser, een opname van het bezoek "
                        "en een willekeurig bezoekers- en sessie-id. Wat je invult en wat op je kaart staat, wordt afgeschermd en gaat "
                        "niet naar Microsoft.",
            "rol": CLARITY_BESLUITEN["rol_microsoft"],      # goedgekeurd 08-10-2026 (CLARITY_BESLUITEN)
            "doorgifte": "Microsoft bewaart de gegevens van Clarity in Microsoft Azure. Voor gebruikers in de EU is Microsoft Ireland "
                         "Operations Limited (Ierland) de contractpartij; die geeft gegevens met EU-standaardcontractbepalingen door aan "
                         "Microsoft Corporation in de Verenigde Staten.",
        })
    if google_active():
        rows.append({
            "naam": "Google Ireland Limited (Ierland) en Google LLC (Verenigde Staten)",
            "dienst": "Bezoekersanalyse met Google Analytics 4 via Google Tag Manager, alleen als je daar toestemming voor geeft",
            "gegevens": "Gebruiksgegevens van je bezoek: je IP-adres (dat Google Analytics tijdens de verwerking gebruikt om onder meer globale locatiegegevens af te leiden; voor gebruikers in de EU/EER registreert of bewaart Google Analytics het afzonderlijke IP-adres niet), welke pagina's je bekijkt "
                        "(met het adres zonder de codes van je ontwerp of bestelling), hoe diep je scrolt, op welke uitgaande links je klikt, "
                        "je apparaat, browser en globale locatie, de pagina waar je vandaan komt en een willekeurig bezoekers-id in een cookie. "
                        "Bij vijf stappen van het samenstellen en bestellen sturen we ook het gekozen ontwerp, de gelegenheid, het pakket en "
                        "het bedrag mee. Namen, e-mailadressen, telefoonnummers, adressen, teksten van je kaart en gegevens van gasten gaan "
                        "nooit mee.",
            "rol": "Verwerker (volgens de gegevensverwerkingsvoorwaarden van Google Analytics)",
            "doorgifte": "Google verwerkt de gegevens van Google Analytics onder meer in de Verenigde Staten, buiten de Europese Economische "
                         "Ruimte, op basis van de afspraken in de gegevensverwerkingsvoorwaarden van Google. Wij geven Google geen toestemming "
                         "voor advertenties en delen geen gegevens met andere Google-producten.",
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
    ] + (ANALYSE_KEUZE_COOKIE if clarity_active() or google_active() else []) + (CLARITY_COOKIES if clarity_active() else []) + (GOOGLE_COOKIES if google_active() else [])


ANALYSE_KEUZE_COOKIE = [
    {"naam": "vaylide_analytics", "soort": "Cookie (noodzakelijk)",
     "doel": "Onthoudt of je toestemming gaf voor de bezoekersanalyse (Microsoft Clarity en/of Google Analytics), zodat we het niet steeds opnieuw vragen.",
     "duur": "12 maanden"},
]

GOOGLE_COOKIES = [
    {"naam": "_ga", "soort": "Cookie van Google Analytics (alleen na toestemming, op deze site)",
     "doel": "Een willekeurig id, zodat Google Analytics je bezoeken aan deze site aan elkaar kan koppelen.", "duur": "2 jaar"},
    {"naam": "_ga_…", "soort": "Cookie van Google Analytics (alleen na toestemming, op deze site)",
     "doel": "Bewaart de status van je huidige sessie (het deel na de streepjes hoort bij onze meetcode).", "duur": "2 jaar"},
]

CLARITY_COOKIES = [
    {"naam": "_clck", "soort": "Cookie van Microsoft Clarity (alleen na toestemming)",
     "doel": "Een willekeurig id, zodat Clarity je bezoeken aan deze site aan elkaar kan koppelen.", "duur": "1 jaar"},
    {"naam": "_clsk", "soort": "Cookie van Microsoft Clarity (alleen na toestemming)",
     "doel": "Koppelt de pagina's van één bezoek aan elkaar tot één opname.", "duur": "1 dag"},
    {"naam": "MUID, CLID, ANONCHK, MR, SM", "soort": "Cookies van Microsoft op clarity.ms of bing.com (alleen na toestemming)",
     "doel": "Zet Microsoft zelf, onder meer om browsers te herkennen. Wij geven geen toestemming voor advertenties (ad_Storage: denied).",
     "duur": "Volgens Microsoft"},
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
    if clarity_active() and not CLARITY_TEKST_GOEDGEKEURD:
        points.append(LABELS["clarity"])
    if google_active() and not GOOGLE_TEKST_GOEDGEKEURD:
        points.append(LABELS["google"])
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

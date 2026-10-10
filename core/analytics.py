"""Bezoekersanalyse met Microsoft Clarity en Google Analytics 4 (via Google Tag Manager): alleen na toestemming, alleen op publieke pagina's
en de Studio.

Clarity staat aan of uit via `VIERLIEF_CLARITY_ID`, Google Tag Manager via `VIERLIEF_GTM_ID` (leeg = uit: geen script, geen uitzondering in de
Content-Security-Policy). Het laden zelf, de toestemming (één keuze voor beide) en het intrekken staan in static/js/toestemming.js; de keuze staat
in de noodzakelijke cookie `vaylide_analytics` (12 maanden). Zie docs/CLARITY.md en docs/GTM.md.

Voor GA4 gaat er nooit iets mee van wat een klant of gast invult. De site geeft alleen een schone paginalocatie (id's in het pad vervangen door
`:id`, geen query behalve gelegenheid en ontwerp) en een paar vaste gebeurtenissen met openbare waarden (ontwerp, gelegenheid, pakket, bedrag).
"""
from __future__ import annotations

import json
import re
from urllib.parse import parse_qsl, urlencode

from django.conf import settings

TOESTEMMING_COOKIE = "vaylide_analytics"
CLARITY_ID_PATROON = re.compile(r"^[a-z0-9]{6,20}$")

# De domeinen die Clarity nodig heeft (learn.microsoft.com/clarity/setup-and-installation/clarity-csp): het script komt van
# www.clarity.ms en scripts.clarity.ms, de gegevens gaan naar [a-z].clarity.ms en Microsoft synchroniseert via c.bing.com.
CLARITY_SCRIPT = ("https://www.clarity.ms", "https://*.clarity.ms")
CLARITY_VERBINDING = ("https://*.clarity.ms", "https://c.bing.com")
CLARITY_BEELD = ("https://*.clarity.ms", "https://c.bing.com")

# Waar Clarity mag draaien: homepage, Collectie en ontwerppagina's, Inspiratie, prijzen, de landingspagina's Digitale uitnodiging maken, Digitale trouwkaarten, Digitale kerstkaarten, Digitale verjaardagsuitnodigingen en Digitale zakelijke uitnodigingen en de Studio tot en met Bestellen.
_EXACT = {"/", "/inspiratie/", "/prijzen/", "/digitale-trouwkaarten/", "/digitale-kerstkaarten/", "/digitale-verjaardagsuitnodigingen/", "/digitale-zakelijke-uitnodigingen/", "/digitale-uitnodiging-maken/"}
_PREFIX = ("/ontwerpen/", "/maken/")
# Nooit, ook niet als een pad hierboven past: uitnodigingen van klanten, Mijn VAYLIDE en gastenlijsten, inloggen, beheer, betalen,
# en de losse voorvertoningen van een kaart (de voorbeelden van ontwerpen en, in de Studio, de kaart in het frame met namen en teksten).
# De stap Controleer (/maken/<id>/voorbeeld/) hoort wel bij de Studio; het frame met de kaart erin niet.
_NOOIT = ("/u/", "/account/", "/inloggen/", "/beheer/", "/betalen/", "/bestelling/", "/voorbeeld/")


def clarity_actief() -> bool:
    return bool(settings.CLARITY_ID)


def clarity_op_pagina(path: str) -> bool:
    """Mag Clarity op deze pagina draaien (als de bezoeker toestemming gaf)?"""
    if not clarity_actief():
        return False
    admin = f"/{settings.ADMIN_URL}".rstrip("/") + "/"
    if path.startswith(_NOOIT) or path.startswith(admin) or "/voorbeeld/weergave/" in path or "/voorbeeld/live/" in path or "/media/" in path:
        return False
    return path in _EXACT or path.startswith(_PREFIX)


def csp_bronnen(path: str) -> dict[str, tuple[str, ...]]:
    """Extra bronnen voor de Content-Security-Policy, alleen waar Clarity of Google Tag Manager mag draaien."""
    bronnen: dict[str, tuple[str, ...]] = {}

    def voeg_toe(extra: dict[str, tuple[str, ...]]) -> None:
        for richtlijn, hosts in extra.items():
            bronnen[richtlijn] = tuple(dict.fromkeys(bronnen.get(richtlijn, ()) + hosts))

    if clarity_op_pagina(path):
        voeg_toe({"script-src": CLARITY_SCRIPT, "connect-src": CLARITY_VERBINDING, "img-src": CLARITY_BEELD})
    if gtm_op_pagina(path):
        voeg_toe({"script-src": GTM_SCRIPT, "connect-src": GTM_VERBINDING, "img-src": GTM_BEELD})
    return bronnen


# ---------------------------------------------------------------------------------------------------------------------------------
# Google Analytics 4 via Google Tag Manager

GTM_SCRIPT = ("https://www.googletagmanager.com",)
GTM_VERBINDING = ("https://www.googletagmanager.com", "https://*.google-analytics.com", "https://*.analytics.google.com")
GTM_BEELD = ("https://www.googletagmanager.com", "https://*.google-analytics.com")

UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
# Uit de query gaat alleen mee wat een vaste, openbare keuze is.
_QUERY_TOEGESTAAN = {"gelegenheid": re.compile(r"^[a-z-]{3,24}$"), "ontwerp": re.compile(r"^[a-z0-9-]{2,40}$")}
# Op de bevestiging van een bestelling (/bestelling/<id>/) draait Clarity nooit, maar de GA4-gebeurtenis purchase_success hoort daar. Er gaat geen
# order- of klantgegeven mee: de pagina wordt gemeld als /bestelling/:id/ met een vaste titel en zonder verwijzer, en de gebeurtenis heeft alleen ontwerp, gelegenheid, pakket, bedrag en valuta.
_BESTELLING = re.compile(r"^/bestelling/[0-9a-fA-F-]{36}/$")
# De zichtbare titel van de bevestiging bevat het bestelnummer; Google krijgt daar een vaste titel en geen verwijzer (die kan een betaalreferentie bevatten).
BESTELLING_TITEL = "Bestelling bevestigd · VAYLIDE"
SESSIE_EVENTS = "gtm_events"
SESSIE_GEZIEN = "gtm_gezien"


def gtm_actief() -> bool:
    return bool(settings.GTM_ID)


def _pad_toegestaan(path: str) -> bool:
    admin = f"/{settings.ADMIN_URL}".rstrip("/") + "/"
    if path.startswith(_NOOIT) and not _BESTELLING.match(path):
        return False
    if path.startswith(admin) or "/voorbeeld/weergave/" in path or "/voorbeeld/live/" in path or "/media/" in path:
        return False
    return path in _EXACT or path.startswith(_PREFIX) or bool(_BESTELLING.match(path))


def gtm_op_pagina(path: str) -> bool:
    """Mag Google Tag Manager op deze pagina draaien (als de bezoeker toestemming gaf)?"""
    return gtm_actief() and _pad_toegestaan(path)


def analyse_op_pagina(path: str) -> bool:
    """Zou er op deze pagina iets gemeten mogen worden (Clarity of Google)? Bepaalt of de toestemmingsvraag hier verschijnt."""
    return clarity_op_pagina(path) or gtm_op_pagina(path)


def schone_pad(path: str) -> str:
    """Het pad zonder id's: /maken/<uuid>/gegevens/ wordt /maken/:id/gegevens/."""
    return UUID.sub(":id", path)


def schone_url(request) -> str:
    """De paginalocatie voor GA4: eigen adres, pad zonder id's, en alleen de vaste query-keuzes."""
    toegestaan = [(k, v) for k, v in parse_qsl(request.META.get("QUERY_STRING", ""), keep_blank_values=False)
                  if k in _QUERY_TOEGESTAAN and _QUERY_TOEGESTAAN[k].match(v)]
    query = "?" + urlencode(toegestaan) if toegestaan else ""
    return f"{settings.BASE_URL}{schone_pad(request.path)}{query}"


def zet_gebeurtenis_in_wachtrij(request, naam: str, eenmalig_sleutel: str = "", **parameters) -> None:
    """Zet een GA4-gebeurtenis klaar voor de eerstvolgende pagina waar de meting mag (daar toont de site hem aan de browser, die hem na toestemming
    doorgeeft). Met `eenmalig_sleutel` gaat hij per sessie maar één keer. Doet niets als Google Tag Manager niet is ingesteld."""
    if not gtm_actief() or not hasattr(request, "session"):
        return
    if eenmalig_sleutel:
        gezien = request.session.get(SESSIE_GEZIEN, [])
        if eenmalig_sleutel in gezien:
            return
        request.session[SESSIE_GEZIEN] = (gezien + [eenmalig_sleutel])[-40:]
    wachtrij = request.session.get(SESSIE_EVENTS, [])
    wachtrij.append({"event": naam, **{k: v for k, v in parameters.items() if v not in ("", None)}})
    request.session[SESSIE_EVENTS] = wachtrij[-8:]


def neem_gebeurtenissen_uit_wachtrij(request) -> list[dict]:
    if not hasattr(request, "session") or request.method != "GET" or not gtm_op_pagina(request.path):
        return []
    wachtrij = request.session.pop(SESSIE_EVENTS, [])
    return wachtrij if isinstance(wachtrij, list) else []


def pagina_gebeurtenis(request) -> list[dict]:
    """Gebeurtenissen die direct uit de route volgen (geen sessie nodig): de Collectie bekijken."""
    match = getattr(request, "resolver_match", None)
    if match and match.view_name == "core:designs" and request.method == "GET":
        return [{"event": "view_collection"}]
    return []


def studiostap_bekeken(request, inv, stap: str) -> None:
    """Studio: de eerste keer in Personaliseren (start_studio) en de eerste keer bij Bestellen (reach_checkout), per concept en sessie."""
    if stap not in ("gegevens", "bestellen") or request.method != "GET":
        return
    ontwerp = inv.template_version.template.slug if inv.template_version_id else ""
    if stap == "gegevens":
        zet_gebeurtenis_in_wachtrij(request, "start_studio", f"start_studio:{inv.uid}", design=ontwerp, occasion=inv.occasion)
    else:
        zet_gebeurtenis_in_wachtrij(request, "reach_checkout", f"reach_checkout:{inv.uid}", design=ontwerp, occasion=inv.occasion, package=inv.package_code)


def bestelling_betaald(request, order) -> None:
    """Bevestigingspagina van een bestelling: alleen als de bestelling echt betaald is (de status komt van de betaalprovider), één keer per sessie."""
    from orders.models import Order

    if order.status != Order.Status.PAID:
        return
    inv = order.invitation
    ontwerp = inv.template_version.template.slug if inv and inv.template_version_id else ""
    zet_gebeurtenis_in_wachtrij(request, "purchase_success", f"purchase_success:{order.uid}", design=ontwerp, occasion=inv.occasion if inv else "",
                                package=order.package_code, value=round(order.total_cents / 100, 2), currency="EUR")


def gtm_context(request) -> dict | None:
    """De gegevens voor de toestemmingsbalk en het laden van Google Tag Manager (templates/partials/toestemming.html, static/js/toestemming.js)."""
    if not gtm_actief():
        return None
    hier = gtm_op_pagina(request.path)
    bevestiging = bool(_BESTELLING.match(request.path))
    gebeurtenissen = (pagina_gebeurtenis(request) + neem_gebeurtenissen_uit_wachtrij(request)) if hier else []
    return {
        "id": settings.GTM_ID, "hier": hier, "omgeving": settings.ANALYTICS_OMGEVING, "debug": settings.ANALYTICS_OMGEVING != "productie",
        "url": schone_url(request) if hier else "", "titel": BESTELLING_TITEL if bevestiging else "", "ref_leeg": bevestiging, "events": json.dumps(gebeurtenissen, separators=(",", ":")) if gebeurtenissen else "",
    }

"""Beheer → Prijzen en acties: de verkoopprijzen bekijken, wijzigen (met bevestiging), het logboek en terugdraaien.

Alle rechten worden aan de serverzijde gecontroleerd (beheer.rollen); een knop verbergen is alleen netheid. Zie docs/PRIJZENBEHEER.md."""
from __future__ import annotations

import logging

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from catalog import prijsbeheer, prijzen
from catalog.models import PriceChangeSet
from kortingen.services import eur

from . import rollen
from .views import staff_required

log = logging.getLogger("vaylide.prijzen")


def _eisen(request, test):
    if not test(request.user):
        log.warning("Prijsbeheer: geweigerd voor %s op %s", getattr(request.user, "pk", None), request.path)
        raise PermissionDenied


def _context(request, **extra) -> dict:
    return {
        "prijsbeheer_aan": prijsbeheer.enabled(),
        "kan_wijzigen": rollen.mag_prijzen_wijzigen(request.user),
        "kan_terugdraaien": rollen.mag_prijzen_terugdraaien(request.user),
        "rol": rollen.rol(request.user),
        "btw_tarief": settings.VAT_RATE_PERCENT,
        **extra,
    }


def _centen(c):
    return eur(c) if c is not None else "ontbreekt"


def _rijen_voor_weergave(raster):
    uit = []
    for r in raster:
        uit.append({"rij": r, "cellen": [{"cel": c, "tekst": _centen(c.cents), "naam": prijzen.TIER_NAAM[c.tier]} for c in r.cellen]})
    return uit


@staff_required
def prices(request):
    _eisen(request, rollen.mag_prijzen_bekijken)
    laatste = PriceChangeSet.objects.select_related("user").exclude(kind=PriceChangeSet.Kind.SEED).first()
    start = PriceChangeSet.objects.filter(kind=PriceChangeSet.Kind.SEED).first()
    raster = prijsbeheer.raster()
    return render(request, "beheer/prices.html", _context(
        request, actief="prijzen", rijen=_rijen_voor_weergave(raster), problemen=prijsbeheer.problemen(), laatste=laatste, start=start,
        verschillen=prijsbeheer.verschillen_met_code(),
        v2=prijzen.actief(), codes_aan=settings.DISCOUNTS_ENABLED, aanbod_aan=settings.OFFERS_ENABLED,
        zonder_ontwerp=[f"{r.label}" for r in raster if all(c.ontwerpen == 0 for c in r.cellen)],
    ))


def _int(waarde, standaard=-1) -> int:
    try:
        return int(waarde)
    except (TypeError, ValueError):
        return standaard


def _invoer_uit_post(post) -> dict:
    return {(rij, tier): post.get(f"p_{rij}_{tier}", "") for rij, tier in prijsbeheer.alle_cellen() if f"p_{rij}_{tier}" in post}


def _formulier(request, waarden=None, fouten=None, melding=""):
    raster = prijsbeheer.raster()
    rijen = []
    for r in raster:
        cellen = []
        for c in r.cellen:
            waarde = (waarden or {}).get(c.sleutel, c.euro_invoer)
            cellen.append({"cel": c, "naam": prijzen.TIER_NAAM[c.tier], "waarde": waarde, "fout": (fouten or {}).get(c.sleutel, "")})
        rijen.append({"rij": r, "cellen": cellen})
    return render(request, "beheer/prices_edit.html", _context(
        request, actief="prijzen", rijen=rijen, stempel=prijsbeheer.stempel(), fouten=fouten or {}, melding=melding,
        min_euro=eur(prijsbeheer.MIN_CENTS), max_euro=eur(prijsbeheer.MAX_CENTS)), status=400 if fouten else 200)


def _bevestig_tabel(nieuw: dict, oud: dict) -> list[dict]:
    uit = []
    for (rij, tier), cents in nieuw.items():
        voor = oud.get((rij, tier))
        verschil = cents - voor if voor is not None else None
        uit.append({
            "label": prijsbeheer.BEHEER_LABEL[rij], "tier_naam": prijzen.TIER_NAAM[tier], "sleutel": f"p_{rij}_{tier}",
            "oud": _centen(voor), "nieuw": eur(cents), "cents": cents, "invoer": f"{cents // 100},{cents % 100:02d}",
            "verschil": ("+ " if verschil and verschil > 0 else "− ") + eur(abs(verschil)) if verschil else "",
            "procent": f"{abs(verschil) * 100 / voor:.1f}".replace(".", ",") + "%" if verschil and voor else "",
            "omhoog": bool(verschil and verschil > 0),
            "btw_oud": eur(prijsbeheer.btw_regel(voor)["btw"]) if voor else "—", "btw_nieuw": eur(prijsbeheer.btw_regel(cents)["btw"]),
            "excl_nieuw": eur(prijsbeheer.btw_regel(cents)["excl"]),
            "gedeeld": rij == "jubileum_verloving", "geldt_voor": prijsbeheer.GELDT_VOOR[rij],
        })
    return uit


def _bevestig_pagina(request, b, *, fouten=None, revert=None, reden="", status=200):
    imp = prijsbeheer.impact(b.nieuw)
    waarschuwingen = list(b.waarschuwingen) + prijsbeheer.verhoging_voor_aanbieding(b.nieuw, b.oud)
    return render(request, "beheer/prices_confirm.html", _context(
        request, actief="prijzen", tabel=_bevestig_tabel(b.nieuw, b.oud), stempel=prijsbeheer.stempel(), waarschuwingen=waarschuwingen,
        grote_sprong=b.grote_sprong, ontwerpen_totaal=sum(imp["ontwerpen"].values()), codes=imp["codes"], aanbiedingen=imp["aanbiedingen"],
        fouten=fouten or {}, reden=reden, revert=revert), status=status)


@staff_required
@require_http_methods(["GET", "POST"])
def prices_edit(request):
    _eisen(request, rollen.mag_prijzen_wijzigen)
    if not prijsbeheer.enabled():
        messages.error(request, "Prijsbeheer staat uit in deze omgeving. Wijzigen kan pas als VIERLIEF_PRIJZENBEHEER aan staat.")
        return redirect("beheer:prices")
    if request.method == "GET":
        return _formulier(request)
    invoer = _invoer_uit_post(request.POST)
    waarden = {f"p_{r}_{t}": v for (r, t), v in invoer.items()}
    if request.POST.get("stempel") != str(prijsbeheer.stempel()):
        messages.error(request, "Er is intussen een andere prijswijziging doorgevoerd. Dit is de nieuwe stand; vul je wijziging opnieuw in.")
        return redirect("beheer:prices_edit")
    b = prijsbeheer.beoordeel(invoer)
    if not b.ok:
        return _formulier(request, waarden, b.fouten, "Controleer de gemarkeerde velden.")
    if not b.nieuw:
        return _formulier(request, waarden, None, "Er is niets gewijzigd.")
    return _bevestig_pagina(request, b)


@staff_required
@require_POST
def prices_confirm(request):
    _eisen(request, rollen.mag_prijzen_wijzigen)
    invoer = _invoer_uit_post(request.POST)
    reden = request.POST.get("reden", "")
    try:
        if request.POST.get("begrepen") != "1":
            raise prijsbeheer.PrijsFout({"begrepen": "Vink aan dat je begrijpt dat dit direct geldt voor nieuwe bestellingen."})
        zet = prijsbeheer.voer_door(request.user, invoer, reden=reden, stempel_in=_int(request.POST.get("stempel")),
                                    grote_sprong_bevestigd=request.POST.get("grote_sprong") == "1")
    except prijsbeheer.PrijsFout as exc:
        if "intussen" in exc.fouten.get("", ""):
            messages.error(request, exc.fouten[""])
            return redirect("beheer:prices_edit")
        return _bevestig_pagina(request, prijsbeheer.beoordeel(invoer), fouten=exc.fouten, reden=reden, status=400)
    aantal = zet.changes.count()
    messages.success(request, f"Prijzen doorgevoerd ({aantal} bedrag{'en' if aantal != 1 else ''}). Bestaande bestellingen en openstaande betalingen houden hun bedrag.")
    return redirect("beheer:prices")


@staff_required
def prices_log(request):
    _eisen(request, rollen.mag_prijzen_bekijken)
    sets = PriceChangeSet.objects.select_related("user", "reverts").prefetch_related("changes", "reverted_by").order_by("-id")
    pagina = Paginator(sets, 20).get_page(request.GET.get("pagina"))
    regels = []
    for s in pagina:
        cellen = [{"label": prijsbeheer.BEHEER_LABEL.get(c.rij, c.rij), "tier": prijzen.TIER_NAAM.get(c.tier, c.tier), "oud": _centen(c.old_cents) if c.old_cents is not None else "—",
                   "nieuw": eur(c.new_cents)} for c in s.changes.all()]
        regels.append({"set": s, "cellen": cellen, "teruggedraaid": s.reverted_by.exists(),
                       "kan_terug": s.kind == PriceChangeSet.Kind.CHANGE and not s.reverted_by.exists() and rollen.mag_prijzen_terugdraaien(request.user) and prijsbeheer.enabled()})
    return render(request, "beheer/prices_log.html", _context(request, actief="logboek", regels=regels, pagina=pagina))


@staff_required
@require_http_methods(["GET", "POST"])
def prices_revert(request, pk):
    _eisen(request, rollen.mag_prijzen_terugdraaien)
    zet = get_object_or_404(PriceChangeSet, pk=pk)
    if zet.kind != PriceChangeSet.Kind.CHANGE or zet.reverted_by.exists() or not prijsbeheer.enabled():
        messages.error(request, "Deze wijziging kan niet (meer) worden teruggedraaid.")
        return redirect("beheer:prices_log")
    voorstel = prijsbeheer.terugdraai_voorstel(zet)
    if request.method == "POST":
        gekozen = set(request.POST.getlist("cel"))
    else:
        gekozen = {v["sleutel"] for v in voorstel if v["nog_zoals_gezet"]}
    for v in voorstel:
        v["gekozen"] = v["sleutel"] in gekozen
        v["huidig_tekst"], v["terug_tekst"], v["gezet_tekst"] = _centen(v["huidig"]), eur(v["terug_naar"]), eur(v["gezet"])
    invoer = {(v["rij"], v["tier"]): v["terug_naar"] for v in voorstel if v["gekozen"]}
    fouten, reden = {}, request.POST.get("reden", "")
    if request.method == "POST":
        if not invoer:
            fouten[""] = "Kies minstens één bedrag om terug te draaien."
        elif request.POST.get("begrepen") != "1":
            fouten["begrepen"] = "Vink aan dat je begrijpt dat dit direct geldt voor nieuwe bestellingen."
        else:
            try:
                prijsbeheer.voer_door(request.user, invoer, reden=reden, stempel_in=_int(request.POST.get("stempel")),
                                      kind=PriceChangeSet.Kind.REVERT, reverts=zet, grote_sprong_bevestigd=request.POST.get("grote_sprong") == "1")
            except prijsbeheer.PrijsFout as exc:
                fouten = exc.fouten
            else:
                messages.success(request, "De wijziging is teruggedraaid als nieuwe, geregistreerde wijziging. Bestaande bestellingen houden hun bedrag.")
                return redirect("beheer:prices")
    b = prijsbeheer.beoordeel(invoer) if invoer else None
    tabel = _bevestig_tabel(b.nieuw, b.oud) if b else []
    imp = prijsbeheer.impact(b.nieuw) if b else {"codes": [], "aanbiedingen": []}
    return render(request, "beheer/prices_revert.html", _context(
        request, actief="logboek", zet=zet, voorstel=voorstel, tabel=tabel, fouten=fouten, reden=reden, stempel=prijsbeheer.stempel(),
        codes=imp["codes"], aanbiedingen=imp["aanbiedingen"], waarschuwingen=(b.waarschuwingen if b else []), grote_sprong=bool(b and b.grote_sprong)),
        status=400 if fouten else 200)

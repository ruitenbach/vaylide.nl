"""Schermen voor tweestapsverificatie in Beheer (ook de ingang voor Django-admin): code invoeren, instellen en beheren."""
from __future__ import annotations

import functools

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache

from accounts import tweestaps
from accounts.models import TwoFactor
from accounts.services import safe_next


def _staff(view):
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse("beheer:login"))
        if not request.user.is_staff:
            raise Http404()
        return never_cache(view)(request, *args, **kwargs)

    return wrapper


def _volgende(request, default=None) -> str:
    return safe_next(request, request.POST.get("next") or request.GET.get("next") or "", default or reverse("beheer:dashboard"))


def _sleutelprobleem(request):
    """De sleutel ontbreekt of past niet bij de opgeslagen geheimen. We controleren dan niets en laten niemand door (geen terugval)."""
    response = render(request, "beheer/tweestaps_sleutel.html")
    response.status_code = 503
    return response


def _geblokkeerd_antwoord(request, template, context):
    context["error"] = tweestaps.BLOCK_MESSAGE
    response = render(request, template, context)
    response.status_code = 429
    return response


@_staff
def controle(request):
    tf = tweestaps.van(request.user)
    next_url = _volgende(request)
    if tf is None:
        return redirect(reverse("beheer:tweestaps_instellen") + "?next=" + next_url if settings.TWOFA_REQUIRED else next_url)
    if tweestaps.is_geverifieerd(request, tf):
        return redirect(next_url)
    context = {"next": next_url}
    if request.method == "POST":
        if tweestaps.geblokkeerd(request, request.user):
            return _geblokkeerd_antwoord(request, "beheer/tweestaps_controle.html", context)
        try:
            soort = tweestaps.controleer_invoer(tf, request.POST.get("code", ""))
        except tweestaps.sleutelfouten():
            return _sleutelprobleem(request)
        if soort:
            tweestaps.registreer_succes(request.user)
            tweestaps.markeer_geverifieerd(request, tf)
            if soort == "herstel":
                over = tweestaps.herstelcodes_over(request.user)
                messages.warning(request, f"Je bent ingelogd met een herstelcode. Er zijn er nog {over} over. Maak nieuwe codes bij Beveiliging als het er weinig zijn.")
            return redirect(next_url)
        tweestaps.registreer_mislukking(request, request.user)
        context["error"] = "Deze code klopt niet of is al gebruikt."
    return render(request, "beheer/tweestaps_controle.html", context)


@_staff
def instellen(request):
    if tweestaps.van(request.user) is not None:
        return redirect(reverse("beheer:tweestaps"))
    next_url = _volgende(request)
    context = {"next": next_url, "verplicht": settings.TWOFA_REQUIRED}
    if not tweestaps.beschikbaar():
        context["niet_beschikbaar"] = True
        return render(request, "beheer/tweestaps_instellen.html", context)
    token = request.session.get(tweestaps.SESSION_PENDING)
    geheim = None
    if token:
        try:
            geheim = tweestaps.ontsleutel(token)
        except Exception:      # sleutel gewisseld of token beschadigd: opnieuw beginnen
            geheim = None
    if geheim is None:
        geheim = tweestaps.nieuw_geheim()
        request.session[tweestaps.SESSION_PENDING] = tweestaps.versleutel(geheim)
    if request.method == "POST":
        if tweestaps.geblokkeerd(request, request.user):
            return _geblokkeerd_antwoord(request, "beheer/tweestaps_instellen.html", {**context, "geheim": tweestaps.groepeer(geheim)})
        stap = tweestaps.passende_stap(geheim, request.POST.get("code", ""))
        if stap is None:
            tweestaps.registreer_mislukking(request, request.user)
            context["error"] = "Deze code klopt niet. Controleer de tijd van je telefoon en probeer de nieuwe code."
        else:
            tf, _ = TwoFactor.objects.update_or_create(
                user=request.user,
                defaults={"secret_enc": tweestaps.versleutel(geheim), "confirmed_at": timezone.now(), "last_used_step": stap},
            )
            request.session.pop(tweestaps.SESSION_PENDING, None)
            tweestaps.registreer_succes(request.user)
            codes = tweestaps.maak_herstelcodes(request.user)
            tweestaps.markeer_geverifieerd(request, tf)
            return render(request, "beheer/tweestaps_codes.html", {"codes": codes, "next": next_url, "nieuw": True})
    context["geheim"] = tweestaps.groepeer(geheim)
    return render(request, "beheer/tweestaps_instellen.html", context)


@_staff
def qr(request):
    token = request.session.get(tweestaps.SESSION_PENDING)
    if not token or tweestaps.van(request.user) is not None or not tweestaps.beschikbaar():
        raise Http404()
    try:
        geheim = tweestaps.ontsleutel(token)
    except Exception:
        raise Http404()
    response = HttpResponse(tweestaps.qr_svg(tweestaps.provisioning_uri(request.user.email, geheim)), content_type="image/svg+xml")
    response["Cache-Control"] = "no-store"
    return response


@_staff
def beheren(request):
    """Overzicht, nieuwe herstelcodes en uitzetten. Beide acties vragen opnieuw om een code."""
    tf = tweestaps.van(request.user)
    if tf is None:
        return redirect(reverse("beheer:tweestaps_instellen"))
    if not tweestaps.is_geverifieerd(request, tf):
        return redirect(reverse("beheer:tweestaps_controle") + "?next=" + reverse("beheer:tweestaps"))
    context = {"over": tweestaps.herstelcodes_over(request.user), "verplicht": settings.TWOFA_REQUIRED}
    if request.method == "POST":
        actie = request.POST.get("actie")
        if actie not in ("nieuwe_codes", "uitzetten") or (actie == "uitzetten" and settings.TWOFA_REQUIRED):
            raise Http404()
        if tweestaps.geblokkeerd(request, request.user):
            return _geblokkeerd_antwoord(request, "beheer/tweestaps.html", context)
        try:
            geldig = tweestaps.controleer_invoer(tf, request.POST.get("code", ""))
        except tweestaps.sleutelfouten():
            return _sleutelprobleem(request)
        if not geldig:
            tweestaps.registreer_mislukking(request, request.user)
            context["error"] = "Deze code klopt niet of is al gebruikt. Wacht op een nieuwe code van je app en probeer opnieuw."
            return render(request, "beheer/tweestaps.html", context)
        tweestaps.registreer_succes(request.user)
        if actie == "nieuwe_codes":
            codes = tweestaps.maak_herstelcodes(request.user)
            return render(request, "beheer/tweestaps_codes.html", {"codes": codes, "next": reverse("beheer:tweestaps"), "nieuw": False})
        tf.delete()
        tweestaps.RecoveryCode.objects.filter(user=request.user).delete()
        request.session.pop(tweestaps.SESSION_KEY, None)
        messages.success(request, "Tweestapsverificatie staat uit voor dit account.")
        return redirect(reverse("beheer:dashboard"))
    return render(request, "beheer/tweestaps.html", context)

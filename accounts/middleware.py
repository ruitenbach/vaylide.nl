"""De poort voor tweestapsverificatie van medewerkers.

Een medewerker (is_staff) telt pas als ingelogd zodra de tweede stap is gedaan:
- heeft het account 2FA, dan moet deze sessie een code of herstelcode hebben ingevoerd;
- heeft het account geen 2FA en is 2FA verplicht (VIERLIEF_2FA_VERPLICHT), dan moet het eerst worden ingesteld;
- is 2FA niet verplicht en niet ingesteld, dan verandert er niets.
Tot die tijd is `request.user` op elke URL anoniem (ook voor losse beheerroutes buiten /beheer/, zoals bestellingen
en gezichten), en worden Beheer en Django-admin doorgestuurd naar de code- of instelpagina.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode

from . import tweestaps

BEHEER = "/beheer/"
TWEESTAPS_PREFIX = "/beheer/2fa/"
BEHEER_LOGIN = "/beheer/inloggen/"


def _admin_prefix() -> str:
    return f"/{settings.ADMIN_URL}"


class TwoFactorGateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tweestaps_ok = True
        user = request.user
        if user.is_authenticated and user.is_staff:
            status = tweestaps.toegang(request)
            if status != "ok":
                request.tweestaps_ok = False
                path = request.path_info
                admin = _admin_prefix()
                if path.startswith(TWEESTAPS_PREFIX):
                    return self.get_response(request)       # code- en instelpagina's werken met het echte account
                if path.startswith(BEHEER) or path.startswith(admin):
                    if path in (BEHEER_LOGIN, f"{admin}login/", f"{admin}logout/"):
                        request.user = AnonymousUser()
                        return self.get_response(request)
                    target = reverse("beheer:tweestaps_controle" if status == "controle" else "beheer:tweestaps_instellen")
                    if request.method in ("GET", "HEAD"):
                        target += "?" + urlencode({"next": request.get_full_path()})
                    return redirect(target)
                request.user = AnonymousUser()
        return self.get_response(request)

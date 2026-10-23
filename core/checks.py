"""Systeemcontroles voor de beveiliging (zichtbaar bij `manage.py check`)."""
import os

from django.conf import settings
from django.core.checks import Warning, register


@register()
def proxy_hops(app_configs, **kwargs):
    on_render = bool(os.environ.get("RENDER"))
    hops = settings.TRUSTED_PROXY_HOPS
    problems = []
    if hops < 0:
        problems.append(Warning("VIERLIEF_TRUSTED_PROXY_HOPS mag niet negatief zijn.", id="vaylide.W001"))
    if on_render and hops == 0:
        problems.append(
            Warning(
                "VIERLIEF_TRUSTED_PROXY_HOPS staat op 0 op Render: alle bezoekers delen dan één IP-adres in de limieten.",
                hint="Controleer in Beheer → Instellingen welke waarde je eigen IP-adres laat zien.",
                id="vaylide.W002",
            )
        )
    return problems


@register()
def tweestaps_sleutel(app_configs, **kwargs):
    from django.core.checks import Error

    if getattr(settings, "TWOFA_KEYS", None):
        try:
            from accounts import tweestaps

            tweestaps._fernet()
        except Exception:
            return [Error("VIERLIEF_2FA_SLEUTEL is geen geldige Fernet-sleutel.", hint="Maak er een met: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"", id="vaylide.E003")]
        return []
    if getattr(settings, "TWOFA_REQUIRED", False):
        return [Error("VIERLIEF_2FA_VERPLICHT staat aan, maar VIERLIEF_2FA_SLEUTEL ontbreekt: niemand kan 2FA instellen.", id="vaylide.E004")]
    return []

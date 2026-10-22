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

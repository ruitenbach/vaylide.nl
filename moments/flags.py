"""De feature-vlag van Moments. Standaard UIT (VIERLIEF_MOMENTS_ENABLED): dan doet de app niets voor bezoekers."""
from __future__ import annotations

from functools import wraps

from django.conf import settings
from django.http import Http404


def moments_enabled() -> bool:
    return bool(getattr(settings, "MOMENTS_ENABLED", False))


def moments_demo_enabled() -> bool:
    """De demonstratiepagina bestaat alleen met de vlag aan én in testmodus: nooit op een live omgeving."""
    return moments_enabled() and bool(getattr(settings, "TEST_MODE", False))


def require_moments(view):
    """Voor views van latere stappen: bij een uitgeschakelde vlag bestaat de pagina niet (404), ook niet voor medewerkers."""

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not moments_enabled():
            raise Http404()
        return view(request, *args, **kwargs)

    return wrapper

from __future__ import annotations

from django.http import Http404
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from .demo import demo_event
from .flags import moments_demo_enabled


@require_GET
@never_cache
def demo_guest(request):
    """Gastpagina met demonstratiegegevens. Geen formulier, geen opslag, geen verzoek naar de server bij het kiezen van bestanden."""
    if not moments_demo_enabled():
        raise Http404()
    response = render(request, "moments/guest.html", {"event": demo_event()})
    response["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response["Referrer-Policy"] = "no-referrer"
    return response

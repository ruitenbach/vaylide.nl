"""Pagina 'Onze eigen gezichten' in de editor, de voortgang en de privé-beelden.

Alleen voor de ingelogde eigenaar van de uitnodiging (en het Vaylide-team). Anderen krijgen 404, ook bij een geldig id.
"""
from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods

from core.utils import rate_limit
from invitations.access import get_accessible_invitation

from . import services
from .models import FaceRequest


def _owner_invitation(request, uid):
    inv = get_accessible_invitation(request, uid)
    if not request.user.is_authenticated or (inv.owner_id != request.user.id and not request.user.is_staff):
        raise Http404()
    return inv


@require_http_methods(["GET", "POST"])
def page(request, uid):
    from studio.views import _context

    inv = _owner_invitation(request, uid)
    req = services.get_request(inv)
    available = services.feature_available(inv)
    if not available and req is None:
        raise Http404()
    if request.method == "POST":
        action = request.POST.get("actie")
        try:
            if action == "uploaden":
                if not available:
                    raise services.FaceError("Eigen gezichten zijn op dit moment niet beschikbaar.")
                if not rate_limit(f"gezichten-upload:{inv.pk}", 20, 3600):
                    raise services.FaceError("Je hebt veel foto's geüpload. Probeer het over een uur opnieuw.")
                services.save_photos(inv, request.user, bride=request.FILES.get("foto_vrouw"), groom=request.FILES.get("foto_man"),
                                     consent=request.POST.get("toestemming") == "ja")
                messages.success(request, "Foto's opgeslagen.")
            elif action == "maken":
                services.start_generation(inv, hair={"man": request.POST.get("haar_man"), "vrouw": request.POST.get("haar_vrouw")})
            elif action == "goedkeuren":
                services.approve(inv, request.user)
                messages.success(request, "Goedgekeurd. Deze versie staat nu op je uitnodiging.")
            elif action == "verwijderen":
                services.remove(inv, request.user)
                messages.success(request, "Je foto's en voorbeelden zijn verwijderd.")
            else:
                raise services.FaceError("Onbekende actie.")
        except services.FaceError as exc:
            messages.error(request, str(exc))
        return redirect("gezichten:page", uid=inv.uid)
    return render(request, "gezichten/gezichten.html", _context(
        request, inv, "stijl", req=req, available=available, locked=services.is_locked(inv),
        consent_text=services.CONSENT_TEXT, allow_single=services.ALLOW_SINGLE, demo=settings.FACES_PROVIDER == "test",
        haarkleuren=[(k, k.capitalize()) for k in services.HAARKLEUREN], haar_gekozen=_gekozen_haar(inv, req),
    ))


def _gekozen_haar(inv, req) -> dict:
    if req is not None and req.hair_man and req.hair_woman:
        return {"man": req.hair_man, "vrouw": req.hair_woman}
    man, vrouw = services._hair_choice(inv, None)
    return {"man": man, "vrouw": vrouw}


@require_GET
def status(request, uid):
    inv = _owner_invitation(request, uid)
    req = services.get_request(inv)
    if req is None:
        raise Http404()
    return JsonResponse({"status": req.status, "label": req.get_status_display(), "attempts_left": req.attempts_left,
                         "error": req.error, "has_result": bool(req.result)})


@require_GET
def image(request, uid, soort):
    inv = _owner_invitation(request, uid)
    req = services.get_request(inv)
    field = {"vrouw": "photo_bride", "man": "photo_groom", "voorbeeld": "result"}.get(soort)
    if req is None or field is None:
        raise Http404()
    file = getattr(req, field)
    if not file or not file.name or not file.storage.exists(file.name):
        raise Http404()
    response = FileResponse(file.open("rb"), content_type="image/webp")
    response["Cache-Control"] = "private, no-store"
    return response

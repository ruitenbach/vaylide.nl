"""JSON-koppelingen voor gasten (stap 3A). Geen pagina's: de gastpagina blijft een demonstratie tot een volgende stap.

Regels die overal gelden:
- Vlag uit = 404 (de adressen bestaan dan niet).
- Een gast werkt met een eigen, geheime token in een HttpOnly-cookie; alle gegevens worden op die token gefilterd.
  Een inzending van een andere gast (of van een ander album) geeft 404, nooit 403.
- Alle schrijvende verzoeken hebben CSRF-bescherming; niets is te cachen of te indexeren.
"""
from __future__ import annotations

import json
from functools import wraps

from django.conf import settings
from django.core import signing
from django.http import FileResponse, Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from core.utils import reliable_ip_fingerprint

from . import limits, services
from .flags import moments_enabled
from .models import Submission
from .services import SubmissionRefused
from .storage import UPLOAD_SALT, StorageNotReady, get_storage

COOKIE = "moments_gast"
MAX_JSON_BYTES = 4096

# (statuscode, tekst voor de gast). Vaste codes; de teksten zijn vertaalbaar en bevatten geen techniek.
REFUSALS = {
    "uit": (404, ""),
    "onbekend": (404, ""),
    "token": (401, _("Je sessie is niet meer geldig. Open de link of QR-code opnieuw.")),
    "geen_sessie": (401, _("Open eerst de link of QR-code van het evenement.")),
    "album_dicht": (409, _("Dit album neemt geen foto's meer aan.")),
    "geen_nieuwe_gasten": (409, _("Er kunnen nu geen nieuwe gasten meedoen. Vraag het aan de organisator.")),
    "plafond_gast": (409, _("Je hebt het maximum aantal foto's bereikt.")),
    "plafond_album": (409, _("Dit album is vol. Vraag het aan de organisator.")),
    "even_wachten": (429, _("Het is even druk. Probeer het over een minuut opnieuw.")),
    "tempo": (429, _("Even rustig aan. Probeer het zo opnieuw.")),
    "type": (415, _("Dit bestand is geen foto die we kunnen gebruiken. Kies een JPEG, PNG of WebP.")),
    "te_klein": (400, _("Dit bestand is te klein om een foto te zijn.")),
    "te_groot": (413, _("Deze foto is te groot. Kies een kleinere.")),
    "ongeldig": (400, _("Dat verzoek klopt niet.")),
    "nog_niet_ontvangen": (409, _("De foto is nog niet helemaal aangekomen. Probeer het zo opnieuw.")),
    "opslag_niet_klaar": (503, _("Uploaden is nu niet beschikbaar. Probeer het later opnieuw.")),
}
FAILURES = {
    "verlopen": _("Het uploaden duurde te lang. Probeer het opnieuw."),
    "te_klein": REFUSALS["te_klein"][1],
    "te_groot": REFUSALS["te_groot"][1],
    "type": REFUSALS["type"][1],
    "onleesbaar": _("We kunnen deze foto niet lezen. Probeer een andere."),
    "dubbel": _("Deze foto heb je al gekozen."),
    "verwerking": _("Er ging iets mis bij het verwerken. Probeer het opnieuw."),
}


def _json(data: dict, status: int = 200) -> JsonResponse:
    response = JsonResponse(data, status=status)
    response["X-Robots-Tag"] = "noindex, nofollow, noarchive"
    response["Referrer-Policy"] = "no-referrer"
    return response


def _refused(exc: SubmissionRefused) -> HttpResponse:
    status, text = REFUSALS.get(exc.code, (400, _("Dat verzoek klopt niet.")))
    if status == 404:
        raise Http404()
    response = _json({"fout": exc.code, "bericht": str(text)}, status)
    if exc.retry_after:
        response["Retry-After"] = str(exc.retry_after)
    return response


def moments_view(view):
    """Vlag uit = de pagina bestaat niet (ook geen CSRF-melding die het adres verraadt). Daarna CSRF-controle en nooit cachen."""
    protected = csrf_protect(view)

    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not moments_enabled():
            raise Http404()
        return protected(request, *args, **kwargs)

    return csrf_exempt(never_cache(wrapper))  # de middleware slaat over; csrf_protect hierboven doet de controle na de vlag


def _token(request):
    return services.resolve_token(request.COOKIES.get(COOKIE, ""))


def _body(request) -> dict:
    if len(request.body or b"") > MAX_JSON_BYTES:
        raise SubmissionRefused("ongeldig")
    try:
        data = json.loads(request.body or b"{}")
    except ValueError:
        raise SubmissionRefused("ongeldig")
    if not isinstance(data, dict):
        raise SubmissionRefused("ongeldig")
    return data


def _storage():
    try:
        return get_storage()
    except StorageNotReady:
        raise SubmissionRefused("opslag_niet_klaar")


def _describe(sub: Submission) -> dict:
    out = {"id": str(sub.uid), "status": sub.status, "soort": sub.kind, "aangemaakt": sub.created_at.isoformat()}
    if sub.status == Submission.Status.FAILED:
        out["fout"] = sub.failure_code
        out["bericht"] = str(FAILURES.get(sub.failure_code, FAILURES["verwerking"]))
    return out


@require_POST
@moments_view
def start_session(request, code):
    try:
        token, raw = services.start_guest_session(code, network_hash=reliable_ip_fingerprint(request) or "", existing=_token(request))
    except SubmissionRefused as exc:
        return _refused(exc)
    response = _json({"gast": True, "nieuw": raw is not None, "maximaal_foto": token.album.guest_limit})
    if raw:
        max_age = 60 * 60 * 24 * 30 * limits.RETENTION_MONTHS
        response.set_cookie(COOKIE, raw, max_age=max_age, path="/moments/", httponly=True, secure=request.is_secure(), samesite="Lax")
    return response


@require_http_methods(["GET", "POST"])
@moments_view
def uploads(request):
    token = _token(request)
    if token is None:
        return _refused(SubmissionRefused("geen_sessie"))
    if request.method == "GET":
        return _json({"inzendingen": [_describe(s) for s in services.submissions_visible_to_guest(token).order_by("-created_at")[:200]]})
    try:
        data = _body(request)
        storage = _storage()
        size = data.get("grootte")
        sub, target = services.reserve_photo_upload(token, client_id=data.get("client_id"), content_type=str(data.get("type", "")), size_bytes=size, storage=storage)
    except SubmissionRefused as exc:
        return _refused(exc)
    out = _describe(sub)
    out["upload"] = target
    return _json(out, 201 if target else 200)


@require_GET
@moments_view
def upload_status(request, uid):
    token = _token(request)
    if token is None:
        return _refused(SubmissionRefused("geen_sessie"))
    sub = services.guest_submission(token, uid)
    if sub is None:
        raise Http404()
    return _json(_describe(sub))


@require_POST
@moments_view
def upload_complete(request, uid):
    token = _token(request)
    if token is None:
        return _refused(SubmissionRefused("geen_sessie"))
    try:
        sub = services.complete_photo_upload(token, uid, _storage())
    except SubmissionRefused as exc:
        return _refused(exc)
    if sub is None:
        raise Http404()
    return _json(_describe(sub))


@require_GET
@moments_view
def upload_file(request, uid):
    """Alleen de eigen, verwerkte foto. Nooit een openbaar adres: S3 krijgt een link van 5 minuten, lokaal streamt de server."""
    token = _token(request)
    if token is None:
        return _refused(SubmissionRefused("geen_sessie"))
    sub = services.guest_submission(token, uid)
    if sub is None or sub.status != Submission.Status.READY or not sub.storage_key:
        raise Http404()
    storage = _storage_or_404()
    url = storage.download_url(sub.storage_key)
    if url:
        return HttpResponseRedirect(url)
    response = FileResponse(storage.open(sub.storage_key), content_type="image/jpeg")
    response["Content-Disposition"] = "inline"
    response["X-Content-Type-Options"] = "nosniff"
    response["Cache-Control"] = "private, no-store"
    return response


def _storage_or_404():
    try:
        return get_storage()
    except StorageNotReady:
        raise Http404()


@csrf_exempt
@require_http_methods(["PUT"])
def test_storage_upload(request, signed):
    """Doel van het 'directe upload'-adres in de testomgeving (lokale opslag). De ondertekening is hier de toegang: geen cookie, geen CSRF.
    Bestaat alleen in testmodus met de vlag aan, en alleen voor een lopende reservering."""
    if not (moments_enabled() and settings.TEST_MODE):
        raise Http404()
    try:
        info = signing.loads(signed, salt=UPLOAD_SALT, max_age=limits.RESERVATION_MINUTES * 60)
    except signing.BadSignature:
        raise Http404()
    from django.utils import timezone

    if not Submission.objects.filter(original_key=info["k"], status=Submission.Status.UPLOADING, reservation_expires_at__gt=timezone.now()).exists():
        raise Http404()
    storage = _storage_or_404()
    if getattr(storage, "name", "") != "lokaal":
        raise Http404()
    try:
        length = int(request.META.get("CONTENT_LENGTH") or -1)
    except ValueError:
        length = -1
    if length < 1:
        return HttpResponse(status=411)
    if length > info["m"]:
        return HttpResponse(status=413)
    if (request.META.get("CONTENT_TYPE") or "").split(";")[0].strip().lower() != info["t"]:
        return HttpResponse(status=415)
    data = request.read(info["m"] + 1)
    if len(data) > info["m"] or len(data) != length:
        return HttpResponse(status=413)
    storage.write(info["k"], data)
    return HttpResponse(status=204)

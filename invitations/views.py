"""Publieke uitnodigingen, voorbeelden, aanmelden, agenda en beveiligde media."""
from __future__ import annotations

import mimetypes
import os
import re

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST

from catalog.models import Template
from core.utils import form_age_seconds, ip_fingerprint, rate_limit, signed_timestamp, new_token, wants_json

from .content import event_times, referenced_assets
from .demo import DEFAULT_DEMO_OCCASION, demo_content
from .ics import build_ics
from .models import Invitation, MediaAsset
from .render import PathResolver, RenderOptions, build_view
from .rsvp import attending_persons, find_by_edit_token, submit_response, update_response

RSVP_COOKIE = "vierlief_antwoord"
VARIANT_FIELDS = {"groot": "file", "middel": "file_medium", "klein": "file_thumb", "audio": "file"}


# ---------------------------------------------------------------- voorbeelden

def _demo_setup(request, slug):
    template = get_object_or_404(Template.objects.select_related("current_version"), slug=slug, is_active=True)
    version = template.current_version
    if version is None:
        raise Http404("Geen ontwerpversie")
    occasion = request.GET.get("gelegenheid", "")
    if occasion not in template.occasions:
        occasion = DEFAULT_DEMO_OCCASION.get(slug, "")
        if occasion not in template.occasions:
            occasion = template.occasions[0]
    palette = request.GET.get("kleur", "")
    if palette not in [p.get("key") for p in version.palettes]:
        palette = version.default_palette_key
    return template, version, occasion, palette


@xframe_options_sameorigin
def demo(request, slug):
    template, version, occasion, palette = _demo_setup(request, slug)
    soort = request.GET.get("soort", "")
    content = demo_content(slug, occasion, palette, soort=soort)
    query = f"?gelegenheid={occasion}&kleur={palette}" + (f"&soort={content['soort']}" if content.get("soort") else "")
    options = RenderOptions(
        mode="demo",
        music_synth=True,
        share_url=f"{settings.BASE_URL}{reverse('invitations:demo', args=[slug])}{query}",
        ics_url=f"{reverse('invitations:demo_ics', args=[slug])}{query}",
        embed=request.GET.get("embed") == "1",
    )
    view = build_view(occasion=occasion, content=content, overrides={}, template_version=version, options=options)
    return render(request, version.template_path, {"v": view, "rsvp_form": {"client_token": "voorbeeld-formulier-0000", "form_ts": ""}})


def demo_ics(request, slug):
    template, version, occasion, palette = _demo_setup(request, slug)
    content = demo_content(slug, occasion, palette)
    return _ics_response(content, uid=f"voorbeeld-{slug}", title=f"Voorbeeld: {template.name}", url=settings.BASE_URL)


# ------------------------------------------------------------ live uitnodiging

def _live_invitation(slug) -> Invitation | None:
    return (
        Invitation.objects.select_related("published_version__template_version__template")
        .filter(slug=slug)
        .first()
    )


def _unavailable(request, status=410):
    return render(request, "invitations/unavailable.html", status=status)


def _asset_map(invitation: Invitation, content: dict) -> dict:
    uids = referenced_assets(content)
    if not uids:
        return {}
    return {str(a.uid): a for a in MediaAsset.objects.filter(invitation=invitation, uid__in=uids)}


def _capacity(content: dict) -> int | None:
    try:
        value = (content.get("rsvp") or {}).get("capacity")
        return int(value) if value not in (None, "", 0, "0") else None
    except (TypeError, ValueError):
        return None


def live_view(request, invitation: Invitation, *, existing=None, embed: bool = False, direct_open: bool = False) -> dict:
    version = invitation.published_version
    content = version.content
    capacity = _capacity(content)
    options = RenderOptions(
        mode="live",
        features=list(invitation.features or []),
        max_gallery_photos=invitation.max_gallery_photos,
        resolver=PathResolver(f"/u/{invitation.slug}/media", _asset_map(invitation, content)),
        share_url=invitation.public_url,
        ics_url=reverse("invitations:ics", args=[invitation.slug]),
        rsvp_action=reverse("invitations:rsvp", args=[invitation.slug]),
        responses_count_persons=attending_persons(invitation) if capacity else 0,
        existing_response=existing,
        embed=embed,
        direct_open=direct_open,
    )
    view = build_view(
        occasion=invitation.occasion,
        content=content,
        overrides=version.overrides,
        template_version=version.template_version,
        options=options,
    )
    view["capacity"] = capacity
    return view


def _existing_response(request, invitation):
    token = request.COOKIES.get(RSVP_COOKIE, "")
    if not token:
        return None, ""
    response = find_by_edit_token(invitation, token)
    return response, token


def _fresh_rsvp_form(values=None, errors=None, existing_token=""):
    form = {"client_token": new_token(18), "form_ts": signed_timestamp(), "values": values or {}, "errors": errors or {}}
    return form


def public_invitation(request, slug):
    invitation = _live_invitation(slug)
    if invitation is None or not invitation.published_version_id:
        return _unavailable(request, status=404)
    if not invitation.is_publicly_visible:
        return _unavailable(request)
    existing, token = _existing_response(request, invitation)
    # ?embed=1: de echte kaart klein in een kader op onze eigen site (de bedankpagina na betaling). Alleen dan mag
    # framen, en alleen door dezelfde site (X-Frame-Options SAMEORIGIN, CSP frame-ancestors 'self').
    embed = request.GET.get("embed") == "1"
    view = live_view(request, invitation, existing=existing, embed=embed, direct_open=embed and request.GET.get("open") == "1")
    rsvp_form = _fresh_rsvp_form()
    if existing:
        rsvp_form["existing_edit_url"] = reverse("invitations:rsvp_edit", args=[slug, token])
    template = invitation.published_version.template_version.template_path
    response = render(request, template, {"v": view, "rsvp_form": rsvp_form})
    if embed:
        response["X-Frame-Options"] = "SAMEORIGIN"
    return response


def _set_rsvp_cookie(response, invitation, token):
    response.set_cookie(
        RSVP_COOKIE,
        token,
        max_age=365 * 24 * 3600,
        path=f"/u/{invitation.slug}/",
        httponly=True,
        samesite="Lax",
        secure=not settings.DEBUG and settings.BASE_URL.startswith("https://"),
    )


def _success_texts(view, result):
    first = result.response.name.split(" ")[0]
    formal = view.get("formal")
    if result.response.attending:
        message = (
            "Fijn dat u erbij bent! Uw antwoord is opgeslagen." if formal else "Wat fijn dat je erbij bent! Je antwoord is opgeslagen."
        )
    else:
        message = (
            "Jammer dat u er niet bij kunt zijn. Uw antwoord is opgeslagen."
            if formal
            else "Jammer dat je er niet bij kunt zijn. Je antwoord is opgeslagen."
        )
    return f"Bedankt, {first}!", message


@sensitive_post_parameters()  # antwoorden van gasten nooit in foutmeldingen (mails aan de eigenaar)
@require_POST
def rsvp_submit(request, slug):
    invitation = _live_invitation(slug)
    if invitation is None or not invitation.is_publicly_visible:
        if wants_json(request):
            return JsonResponse({"ok": False, "message": "Deze uitnodiging is niet (meer) beschikbaar."}, status=410)
        return _unavailable(request)
    view = live_view(request, invitation)

    def fail(message, errors=None, values=None, status=400):
        if wants_json(request):
            return JsonResponse({"ok": False, "message": message, "errors": errors or {}}, status=status)
        errors = dict(errors or {})
        errors.setdefault("algemeen", message)
        form = _fresh_rsvp_form(values=values or {}, errors=errors)
        return render(request, invitation.published_version.template_version.template_path,
                      {"v": view, "rsvp_form": form}, status=status)

    if not view["rsvp"]["open"]:
        reason = view["rsvp"]["closed_reason"]
        message = {
            "deadline": f"Aanmelden kon tot en met {view['rsvp']['deadline_display']}.",
            "past": "Deze dag heeft al plaatsgevonden.",
            "full": "Het maximale aantal aanmeldingen is bereikt.",
        }.get(reason, "Aanmelden is niet mogelijk.")
        return fail(message, status=409)
    if request.POST.get("website"):
        return fail("Je antwoord kon niet worden verwerkt.")
    age = form_age_seconds(request.POST.get("form_ts", ""))
    if age is None:
        return fail("Het formulier is verlopen. Vernieuw de pagina en probeer het opnieuw.", values=request.POST)
    if age < 2:
        return fail("Dat ging wel erg snel. Controleer je antwoord en probeer het nog eens.", values=request.POST)
    ip = ip_fingerprint(request)
    if not rate_limit(f"rsvp:{invitation.pk}:{ip}", 15, 3600) or not rate_limit(f"rsvp-inv:{invitation.pk}", 600, 3600):
        return fail("Er zijn te veel aanmeldingen verstuurd vanaf dit apparaat. Probeer het later opnieuw.", status=429)

    result = submit_response(invitation, request.POST, view, capacity=view.get("capacity"))
    if not result.ok:
        return fail("Controleer de gemarkeerde velden.", errors=result.errors, values=result.values)

    edit_url = reverse("invitations:rsvp_edit", args=[slug, result.edit_token])
    title, message = _success_texts(view, result)
    if wants_json(request):
        response = JsonResponse({"ok": True, "title": title, "message": message, "edit_url": edit_url})
    else:
        response = redirect(f"{edit_url}?opgeslagen=1")
    _set_rsvp_cookie(response, invitation, result.edit_token)
    return response


@sensitive_post_parameters()
@require_http_methods(["GET", "POST"])
def rsvp_edit(request, slug, token):
    invitation = _live_invitation(slug)
    if invitation is None or not invitation.is_publicly_visible:
        return _unavailable(request)
    guest = find_by_edit_token(invitation, token)
    if guest is None:
        raise Http404("Antwoord niet gevonden")
    view = live_view(request, invitation)
    errors, values = {}, None
    deleted = False
    saved = request.GET.get("opgeslagen") == "1"
    if request.method == "POST":
        if request.POST.get("actie") == "verwijderen":
            guest.delete()
            deleted = True
        elif not view["rsvp"]["open"]:
            errors["algemeen"] = "Wijzigen is niet meer mogelijk: aanmelden is gesloten."
        else:
            if not rate_limit(f"rsvp-edit:{invitation.pk}:{ip_fingerprint(request)}", 30, 3600):
                errors["algemeen"] = "Te veel pogingen. Probeer het later opnieuw."
            else:
                result = update_response(guest, request.POST, view, capacity=view.get("capacity"))
                if result.ok:
                    return redirect(f"{reverse('invitations:rsvp_edit', args=[slug, token])}?opgeslagen=1")
                errors, values = result.errors, result.values
    if values is None and not deleted:
        values = {"name": guest.name, "attending": "ja" if guest.attending else "nee",
                  "party_size": str(guest.party_size or 1), "remark": guest.remark}
        for answer in guest.answers or []:
            values[f"q_{answer.get('id')}"] = answer.get("value", "")
    response = render(
        request,
        "invitations/rsvp_edit.html",
        {
            "v": view,
            "guest": guest,
            "deleted": deleted,
            "saved": saved and not errors,
            "rsvp_form": {"values": values or {}, "errors": errors, "client_token": "", "form_ts": ""},
            "invitation_url": invitation.public_path,
        },
        status=400 if errors else 200,
    )
    if deleted:
        response.delete_cookie(RSVP_COOKIE, path=f"/u/{invitation.slug}/")
    return response


def public_ics(request, slug):
    invitation = _live_invitation(slug)
    if invitation is None or not invitation.is_publicly_visible:
        return _unavailable(request)
    content = invitation.published_version.content
    return _ics_response(content, uid=str(invitation.uid), title=invitation.title or "Uitnodiging", url=invitation.public_url)


def _ics_response(content, *, uid, title, url):
    times = event_times(content)
    if not times.start:
        raise Http404("Geen datum")
    location = ", ".join(filter(None, [content.get("venue_name", "")] + (content.get("address") or "").splitlines()))
    body = build_ics(
        uid=uid,
        title=title,
        start=times.start,
        end=times.end,
        location=location,
        description=f"Uitnodiging: {url}" if url else "",
        url=url,
    )
    response = HttpResponse(body, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="uitnodiging.ics"'
    return response


# ------------------------------------------------------------------- media

RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)$")


def serve_asset(request, asset: MediaAsset, variant: str, *, cache_seconds=3600):
    field_name = VARIANT_FIELDS.get(variant)
    if field_name is None:
        raise Http404()
    if variant == "audio" and asset.kind != MediaAsset.Kind.AUDIO:
        raise Http404()
    if variant != "audio" and asset.kind not in (MediaAsset.Kind.PHOTO, MediaAsset.Kind.SCENE, MediaAsset.Kind.LOGO):
        raise Http404()
    field = getattr(asset, field_name)
    if not field or not field.name or not field.storage.exists(field.name):
        raise Http404()
    content_type = asset.content_type if variant == "audio" else "image/webp"
    path = field.path
    size = os.path.getsize(path)
    range_header = request.headers.get("Range", "")
    match = RANGE_RE.match(range_header.strip()) if range_header else None
    if match and variant == "audio":
        start_s, end_s = match.groups()
        if start_s == "" and end_s == "":
            match = None
        else:
            if start_s == "":
                length = int(end_s)
                start, end = max(0, size - length), size - 1
            else:
                start = int(start_s)
                end = int(end_s) if end_s else size - 1
            if start >= size or start > end:
                response = HttpResponse(status=416)
                response["Content-Range"] = f"bytes */{size}"
                return response
            end = min(end, size - 1)
            handle = open(path, "rb")
            handle.seek(start)
            remaining = end - start + 1

            def chunks():
                left = remaining
                try:
                    while left > 0:
                        data = handle.read(min(65536, left))
                        if not data:
                            break
                        left -= len(data)
                        yield data
                finally:
                    handle.close()

            response = StreamingHttpResponse(chunks(), status=206, content_type=content_type)
            response["Content-Range"] = f"bytes {start}-{end}/{size}"
            response["Content-Length"] = str(remaining)
            response["Accept-Ranges"] = "bytes"
            response["Cache-Control"] = f"private, max-age={cache_seconds}"
            return response
    response = FileResponse(open(path, "rb"), content_type=content_type)
    response["Accept-Ranges"] = "bytes"
    response["Cache-Control"] = f"private, max-age={cache_seconds}"
    response["Content-Disposition"] = "inline"
    return response


def public_media(request, slug, asset_uid, variant):
    invitation = _live_invitation(slug)
    if invitation is None or not invitation.is_publicly_visible:
        raise Http404()
    if str(asset_uid) not in referenced_assets(invitation.published_version.content):
        raise Http404()
    asset = get_object_or_404(MediaAsset, invitation=invitation, uid=asset_uid)
    return serve_asset(request, asset, variant)


mimetypes.add_type("image/webp", ".webp")

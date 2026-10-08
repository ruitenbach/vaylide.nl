"""Samenstellen: gelegenheid en ontwerp kiezen, gegevens invullen, foto's, voorbeeld en bestellen."""
from __future__ import annotations

import copy
import re

from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_http_methods, require_POST

from catalog.models import Package, Template, format_euro
from catalog.occasions import OCCASION_CHOICES, OCCASION_LABELS, collectie_volgorde, occasion_config
from catalog import envelop_collectie
from catalog.envelop import choice as envelop_choice
from catalog import wenskaart
from catalog.specials import is_special, special_addon
from studio import pakket
from core.ai import AIUnavailable, suggest_text
from core.utils import ip_fingerprint, rate_limit, wants_json
from invitations.access import can_access, get_accessible_invitation, remember_draft, session_drafts
from invitations.content import SECTION_LABELS, SOORTEN, card_kind, muziek_bij_ontwerp, normalize_content, publish_issues, referenced_assets
from invitations.images import UploadError, process_logo, process_photo, sniff_audio
from invitations.models import Invitation, MediaAsset, Source
from invitations.render import PathResolver, RenderOptions, build_view
from invitations.services import (
    DraftConflict,
    PublishBlocked,
    create_draft,
    publish_draft,
    referenced_by_any_version,
    save_draft,
)
from invitations.views import serve_asset
from orders.pricing import PricingError, compare_packages, optional_addons, recommended
from orders.services import CheckoutError, invitation_is_paid, start_checkout

from .forms import FORM_CLASSES, CheckoutForm, DesignForm
from .steps import (ENVELOP_SKIP, PERSONALISEER, STEP_KEYS, STEP_LABELS, WENSKAART_LABELS, WENSKAART_SKIP, heeft_envelopstap, next_step,
                    previous_step, progress, substeps)

MAX_PHOTOS_PER_INVITATION = 30


def _active_templates():
    return list(Template.objects.filter(is_active=True, current_version__isnull=False).select_related("current_version"))


def _source(request) -> str:
    return Source.ADMIN if request.user.is_authenticated and request.user.is_staff else Source.CUSTOMER


def _content(inv: Invitation) -> dict:
    palette = (inv.draft_content.get("style") or {}).get("palette") or inv.template_version.default_palette_key
    return normalize_content(inv.draft_content, inv.occasion, palette)


def _locked(request, inv: Invitation) -> list[str]:
    if request.user.is_authenticated and request.user.is_staff:
        return []
    return list((inv.draft_overrides or {}).get("locked_fields") or [])


def _wenskaart(inv: Invitation, content: dict | None = None) -> bool:
    return card_kind(content if content is not None else _content(inv), inv.occasion) == "wenskaart"


def _envelop_stap(inv: Invitation) -> bool:
    """De stap Envelop & zegel bestaat alleen bij een ontwerp met de keuze uit de Envelope Collection (envelope_mode optional)."""
    return heeft_envelopstap(inv)


def _skip(inv: Invitation, content: dict | None = None):
    skip = set(WENSKAART_SKIP) if _wenskaart(inv, content) else set()
    if not _envelop_stap(inv):
        skip |= ENVELOP_SKIP
    return frozenset(skip)


def _eigen_opening(inv: Invitation) -> dict | None:
    """Heeft dit ontwerp een eigen opening (en dus geen stap Envelop & zegel)? Dan een korte uitleg voor de klant, met de opening zoals
    de klant die kent (zonder technische toevoeging als '(Envelope Collection)')."""
    if _envelop_stap(inv):
        return None
    label = re.sub(r"\s*\(Envelope Collection\)", "", (inv.template_version.manifest or {}).get("opening_label") or "").strip()
    return {"label": label}


def _na_ontwerp(inv: Invitation) -> str:
    """Na het kiezen van een ontwerp gaat de klant direct door naar het invullen van de gegevens. De envelop is een onderdeel van
    Personaliseer, voor wie die zelf wil kiezen."""
    return "gegevens"


def _ga_doel(naar: str, inv: Invitation, content: dict, huidig: str) -> str:
    """Waar de klant na het wisselen van onderdeel heen gaat: een stap die bij deze kaart hoort, anders niets."""
    if naar not in STEP_KEYS or naar == "gelegenheid" or naar == huidig:
        return ""
    if naar in _skip(inv, content):
        return ""
    if naar == "bestellen" and invitation_is_paid(inv):
        return ""
    return naar


def _ga_url(inv: Invitation, doel: str, huidig: str) -> str:
    url = reverse("studio:step", args=[inv.uid, doel])
    return f"{url}?terug={huidig}" if doel == "ontwerp" and huidig in PERSONALISEER else url


def _terug(request, inv: Invitation, default: str) -> str:
    """De stap waar 'Wijzigen' vandaan kwam (?terug=...) en waar de klant na het kiezen van een ander ontwerp naar terugkeert."""
    wens = request.POST.get("terug") or request.GET.get("terug") or ""
    return wens if wens in PERSONALISEER and wens not in _skip(inv) else default


def _knoppen(step: str, paid: bool, skip, labels) -> dict:
    """De vervolgknop van de fase: 'Volgende: <onderdeel>' en bij het laatste onderdeel 'Verder naar controle'. Daarnaast, tussendoor, 'Bekijk mijn kaart'."""
    volgende = next_step(step, paid=paid, skip=skip)
    namen = {**STEP_LABELS, **(labels or {})}
    laatste = volgende not in PERSONALISEER
    return {
        "volgende_stap": volgende,
        "volgende_tekst": "Verder naar controle" if laatste else f"Volgende: {namen.get(volgende, '')}",
        "controle_knop": step in PERSONALISEER and not laatste,
    }


def _context(request, inv: Invitation, step: str, **extra) -> dict:
    paid = invitation_is_paid(inv)
    wens = _wenskaart(inv)
    labels = WENSKAART_LABELS if wens else None
    items = progress(step, paid=paid, skip=_skip(inv), labels=labels)
    current = next((i for i in items if i["state"] == "current"), items[0])
    ctx = {
        "inv": inv,
        "step": step,
        "step_label": (WENSKAART_LABELS if wens else {}).get(step, STEP_LABELS.get(step, "")),
        "wenskaart": wens,
        "snel_afronden": wens and not paid,
        "wenskaart_vast": wenskaart.is_wenskaart(inv.draft_content),
        "wenskaart_prijs": format_euro(wenskaart.prijs_cents(inv.template_version)),
        "progress": items,
        "progress_current": current,
        "progress_pct": round(100 * current["number"] / len(items)),
        "substeps": substeps(step, skip=_skip(inv), labels=labels),
        **_knoppen(step, paid, _skip(inv), labels),
        "gekozen_ontwerp": inv.template_version.template,
        "paid": paid,
        "occasion_label": OCCASION_LABELS.get(inv.occasion, ""),
        "is_staff_edit": request.user.is_authenticated and request.user.is_staff,
        "anonymous": inv.owner_id is None,
        "save_url": f"{reverse('accounts:login')}?doel=bewaren&next={reverse('studio:step', args=[inv.uid, step])}",
        "step_labels": STEP_LABELS,
    }
    if step in ("fotos", "stijl", "aanmelden"):
        ctx["feature_badges"] = pakket.feature_badges(pakket.chosen_package(inv))
    if step in ("gegevens", "stijl"):
        ctx["eigen_opening"] = _eigen_opening(inv)
    ctx.update(extra)
    return ctx


# ------------------------------------------------------------------ starten

ACTIEF_CONCEPT = "vierlief_actief_concept"


def _onthoud_actief(request, inv: Invitation) -> None:
    """Het concept van het lopende Studio-traject, met de versie (`draft_rev`) waarop het nog onaangeroerd is: er is alleen een ontwerp gekozen, nog niets ingevuld."""
    request.session[ACTIEF_CONCEPT] = {"uid": str(inv.uid), "rev": inv.draft_rev}


def _onaangeroerd_concept(request) -> Invitation | None:
    """Het concept van dit Studio-traject als de klant er nog niets in heeft ingevuld (hij koos alleen een ontwerp). Dan werkt een nieuwe kaartkeuze dat concept bij,
    in plaats van een nieuw concept te maken: terug naar de keuze en een ander ontwerp aantikken levert dus nooit een tweede concept op."""
    actief = request.session.get(ACTIEF_CONCEPT) or {}
    try:
        inv = Invitation.objects.select_related("template_version__template").filter(uid=actief.get("uid")).first()
    except (ValueError, ValidationError):
        return None
    if inv is None or inv.draft_rev != actief.get("rev") or inv.status != Invitation.Status.DRAFT:
        return None
    if not can_access(request, inv) or inv.customer_locked or invitation_is_paid(inv):
        return None
    return inv


@require_http_methods(["GET", "POST"])
def start(request):
    templates = _active_templates()
    occasion = request.GET.get("gelegenheid") or request.POST.get("occasion") or ""
    if occasion not in OCCASION_LABELS:
        occasion = ""
    chosen = request.GET.get("ontwerp") or request.POST.get("template") or ""
    if request.method == "POST":
        form = DesignForm(request.POST, templates=templates)
        if form.is_valid():
            inv = _werk_onaangeroerd_concept_bij(request, form)
            if inv is not None:
                return redirect("studio:step", uid=inv.uid, step=_na_ontwerp(inv))
            if not rate_limit(f"start:{ip_fingerprint(request)}", 40, 3600):
                messages.error(request, "Je hebt veel ontwerpen gestart. Probeer het later opnieuw.")
                return redirect("studio:start")
            owner = request.user if request.user.is_authenticated and not request.user.is_staff else None
            inv = create_draft(occasion=form.cleaned_data["occasion"], template=form.cleaned_data["template_obj"], owner=owner,
                               palette=request.POST.get("kleur", "")[:40], soort=request.POST.get("soort", "")[:20])
            _onthoud_actief(request, inv)
            package_code = request.POST.get("pakket", "")
            # Een wenskaart heeft geen pakket: de prijs staat vast (catalog/wenskaart.py).
            if not _wenskaart(inv) and package_code in {p.code for p in pakket.active_packages()}:
                inv.package_code = package_code
                inv.save(update_fields=["package_code"])
            remember_draft(request, inv)
            return redirect("studio:step", uid=inv.uid, step=_na_ontwerp(inv))
    else:
        form = DesignForm(initial={"occasion": occasion, "template": chosen}, templates=templates)
    shown = collectie_volgorde([t for t in templates if not occasion or t.supports(occasion)])
    if chosen and occasion and chosen not in [t.slug for t in shown]:
        chosen = ""
    soort = request.GET.get("soort") or request.POST.get("soort") or ""
    soort = soort if soort in ("uitnodiging", "wenskaart") else ""
    wens_start = soort == "wenskaart"
    existing = []
    if request.user.is_authenticated and not request.user.is_staff:
        existing = list(Invitation.objects.filter(owner=request.user, status=Invitation.Status.DRAFT).order_by("-updated_at")[:3])
    else:
        existing = list(Invitation.objects.filter(uid__in=session_drafts(request), owner__isnull=True).order_by("-updated_at")[:3])
    return render(
        request,
        "studio/start.html",
        {
            "form": form,
            "occasions": [(key, label) for key, label in OCCASION_CHOICES],
            "occasion": occasion,
            "occasion_label": OCCASION_LABELS.get(occasion, ""),
            "templates": shown,
            "chosen": chosen,
            "chosen_template": next((t for t in shown if t.slug == chosen), None),
            # Vanaf een ontwerppagina ("Kies dit ontwerp") start de kaart direct: de keuze staat vast en de klant komt meteen bij Personaliseren.
            "direct": request.method == "GET" and request.GET.get("direct") == "1",
            "kleur": (request.GET.get("kleur") or request.POST.get("kleur") or "")[:40],
            "soort": soort,
            "wenskaart": wens_start,
            "wenskaart_prijs": format_euro(wenskaart.PRIJS_CENTS),
            "wenskaart_prijs_special": format_euro(wenskaart.PRIJS_SPECIAL_CENTS),
            "special_slugs": [t.slug for t in shown if t.special],
            "existing": existing,
            "login_url": f"{reverse('accounts:login')}?next={request.get_full_path()}",
            "progress": progress("ontwerp"),
            "progress_current": {"number": 1, "label": "Kies kaart"},
            "progress_pct": 25,
        },
    )


def _werk_onaangeroerd_concept_bij(request, form) -> Invitation | None:
    """Een nieuwe kaartkeuze in een lopend traject waarin nog niets is ingevuld: hetzelfde concept krijgt het nieuwe ontwerp (en de gekozen gelegenheid, soort en kleur)."""
    inv = _onaangeroerd_concept(request)
    if inv is None:
        return None
    template = form.cleaned_data["template_obj"]
    occasion = form.cleaned_data["occasion"]
    version = template.current_version
    soort = request.POST.get("soort", "")[:20]
    keys = [p.get("key") for p in version.palettes]
    kleur = request.POST.get("kleur", "")[:40]
    content = normalize_content(_content(inv), occasion)
    content["soort"] = soort if soort in SOORTEN else ""
    content["style"]["palette"] = kleur if kleur in keys else version.default_palette_key
    muziek_bij_ontwerp(content, version.manifest)
    try:
        inv = save_draft(inv, expected_rev=inv.draft_rev, content=content, template_version=version, occasion=occasion,
                         user=request.user, source=_source(request), step="gegevens")
    except DraftConflict:
        return None
    package_code = request.POST.get("pakket", "")
    if not _wenskaart(inv) and package_code in {p.code for p in pakket.active_packages()}:
        inv.package_code = package_code
        inv.save(update_fields=["package_code"])
    elif _wenskaart(inv) and inv.package_code:
        inv.package_code = ""
        inv.save(update_fields=["package_code"])
    _onthoud_actief(request, inv)
    return inv


def resume(request, uid):
    inv = get_accessible_invitation(request, uid) if not _needs_login(request, uid) else None
    if inv is None:
        return redirect(f"{reverse('accounts:login')}?next={request.path}")
    if invitation_is_paid(inv) and not (request.user.is_authenticated and request.user.is_staff):
        return redirect("portal:invitation", uid=inv.uid)
    step = inv.wizard_step if inv.wizard_step in FORM_CLASSES or inv.wizard_step in ("voorbeeld", "bestellen", "ontwerp") else "gegevens"
    return redirect("studio:step", uid=inv.uid, step=step)


def _needs_login(request, uid) -> bool:
    inv = Invitation.objects.filter(uid=uid).only("owner_id").first()
    return bool(inv and inv.owner_id and not request.user.is_authenticated)


# -------------------------------------------------------------- stappen

@require_http_methods(["GET", "POST"])
def step(request, uid, step):
    if _needs_login(request, uid):
        return redirect(f"{reverse('accounts:login')}?next={request.path}")
    inv = get_accessible_invitation(request, uid)
    if step == "ontwerp":
        return design_step(request, inv)
    if step == "voorbeeld":
        return preview_step(request, inv)
    if step == "bestellen":
        return checkout_step(request, inv)
    form_class = FORM_CLASSES.get(step)
    if form_class is None:
        raise Http404()
    if inv.customer_locked and not (request.user.is_authenticated and request.user.is_staff):
        return render(request, "studio/locked.html", _context(request, inv, step))

    content = _content(inv)
    # Een stap die bij deze kaart niet hoort (Aanmelden bij een wenskaart): door naar de volgende.
    if step in _skip(inv, content):
        return redirect("studio:step", uid=inv.uid, step=next_step(step, paid=invitation_is_paid(inv), skip=_skip(inv, content)))
    extra_kwargs = _form_kwargs(inv, step)
    photos, audio = extra_kwargs.get("photos", []), extra_kwargs.get("audio", [])
    conflict = None
    rev = inv.draft_rev
    if request.method == "POST":
        form = form_class(request.POST, content=content, occasion=inv.occasion, locked=_locked(request, inv), **extra_kwargs)
        action = request.POST.get("actie", "volgende")
        try:
            posted_rev = int(request.POST.get("rev", "0"))
        except ValueError:
            posted_rev = 0
        if form.is_valid():
            new_content = form.apply(copy.deepcopy(content))
            # 'Snel afronden' (alleen bij een wenskaart): bewaar wat er staat en ga direct naar het voorbeeld.
            snel = action == "snel" and card_kind(new_content, inv.occasion) == "wenskaart" and not invitation_is_paid(inv)
            verder = action in ("volgende", "controle") or snel
            # 'ga': de klant wisselt van onderdeel (balk, voortgang of Wijzigen): bewaar wat er staat en ga daarheen.
            ga = action == "ga" and _ga_doel(request.POST.get("naar", ""), inv, new_content, step)
            missing = form.missing() if verder else {}
            paid = invitation_is_paid(inv)
            if snel or action == "controle":
                volgende = "voorbeeld"
            elif ga:
                volgende = ga
            else:
                volgende = next_step(step, paid=paid, skip=_skip(inv, new_content))
            target = volgende if (verder or ga) and not missing else step
            try:
                inv = save_draft(inv, expected_rev=posted_rev, content=new_content, user=request.user, source=_source(request),
                                 step=target if (verder or ga) and not missing else None)
            except DraftConflict as exc:
                conflict = _conflict_info(exc.invitation, new_content, step)
                rev = exc.invitation.draft_rev
            else:
                if missing:
                    for field, message in missing.items():
                        form.add_error(field, message)
                    messages.warning(request, "Je gegevens zijn bewaard. Vul de gemarkeerde velden nog in om verder te gaan.")
                    rev = inv.draft_rev
                elif action == "opslaan":
                    if inv.owner_id is None:
                        return redirect(f"{reverse('accounts:login')}?doel=bewaren&next={reverse('studio:step', args=[inv.uid, step])}")
                    messages.success(request, "Opgeslagen. Je vindt je ontwerp terug in Mijn VAYLIDE.")
                    return redirect("studio:step", uid=inv.uid, step=step)
                elif action == "vorige":
                    return redirect("studio:step", uid=inv.uid, step=previous_step(step, skip=_skip(inv, new_content)))
                elif ga:
                    return redirect(_ga_url(inv, ga, step))
                else:
                    return redirect("studio:step", uid=inv.uid, step=target)
        else:
            rev = posted_rev or inv.draft_rev
    else:
        form = form_class(content=content, occasion=inv.occasion, locked=_locked(request, inv), **extra_kwargs)
    faces_link, faces_status = False, ""
    zegel_logo = None
    if step == "stijl":
        logo_uid = envelop_choice(content).get("logo") or ""
        zegel_logo = inv.assets.filter(kind=MediaAsset.Kind.LOGO, uid=logo_uid).first() if logo_uid else None
    if step == "stijl" and request.user.is_authenticated and (inv.owner_id == request.user.id or request.user.is_staff):
        from gezichten import services as gezichten

        face_req = gezichten.get_request(inv)
        faces_link = gezichten.feature_available(inv) or face_req is not None
        faces_status = face_req.get_status_display().lower() if face_req else ""

    return render(
        request,
        f"studio/step_{step}.html",
        _context(
            request,
            inv,
            step,
            form=form,
            rev=rev,
            conflict=conflict,
            photos=photos,
            audio=audio,
            faces_link=faces_link,
            zegel_logo=zegel_logo,
            faces_status=faces_status,
            content=content,
            cfg=occasion_config(inv.occasion),
            ai_available=True,
            upload_limits=settings.UPLOAD_LIMITS,
            section_labels=SECTION_LABELS,
            features=set(inv.features or []),
            live_url=f"{reverse('studio:live_frame', args=[inv.uid])}?deel={step}",
            live_update_url=reverse("studio:live_update", args=[inv.uid, step]),
        ),
    )


def _terms_info() -> dict:
    from core.voorwaarden import version_info

    return version_info()


def _consent_texts() -> dict:
    """De teksten bij het bestellen (core/voorwaarden.py): precies wat ook letterlijk op de bestelling wordt vastgelegd."""
    from core.voorwaarden import CHECKOUT_UITLEG, DELIVERY_CONSENT, SERVICE_CONSENT, TERMS_CONSENT

    return {"uitleg_tekst": CHECKOUT_UITLEG, "terms_tekst": TERMS_CONSENT, "levering_tekst": DELIVERY_CONSENT, "dienst_tekst": SERVICE_CONSENT}


def _availability_hint(content: dict, quote) -> dict | None:
    """Tot wanneer de kaart online staat als je vandaag betaalt, en of dat vóór de evenementdatum eindigt."""
    if not quote:
        return None
    from datetime import date as date_cls

    from invitations.availability import end_of_availability

    end = end_of_availability(timezone.now(), quote.availability_months)
    event = None
    try:
        event = date_cls.fromisoformat(str(content.get("date") or "")[:10])
    except ValueError:
        event = None
    return {"end": end, "event": event, "before_event": bool(event and end.date() < event)}


def _newsletter_text() -> str:
    from accounts.newsletter import CONSENT_TEXT

    return CONSENT_TEXT


def _form_kwargs(inv: Invitation, step: str) -> dict:
    if step == "fotos":
        photos = list(inv.assets.filter(kind=MediaAsset.Kind.PHOTO))
        for photo in [p for p in photos if p.focus_x is None][:24]:
            photo.analyse()
        return {"photos": photos,
                "audio": list(inv.assets.filter(kind=MediaAsset.Kind.AUDIO)),
                "ontwerp_muziek": (inv.template_version.manifest or {}).get("music")}
    if step in ("stijl", "envelop"):
        return {"template_version": inv.template_version}
    if step == "gegevens":
        return {"soort_vergrendeld": invitation_is_paid(inv)}
    return {}


def _conflict_info(latest: Invitation, mine: dict, step: str) -> dict:
    keys = {
        "gegevens": ["names", "headline", "date", "start_time", "end_time", "timezone", "venue_name", "address", "route_url", "welcome_text"],
        "programma": ["program", "dresscode", "practical", "contact", "closing_text"],
        "aanmelden": ["rsvp"],
        "fotos": ["photos", "story", "music"],
        "stijl": ["style", "sections"],
        "envelop": ["style"],
    }.get(step, [])
    labels = {
        "names": "Namen", "headline": "Kopregel", "date": "Datum", "start_time": "Begintijd", "end_time": "Eindtijd",
        "timezone": "Tijdzone", "venue_name": "Locatie", "address": "Adres", "route_url": "Routelink",
        "welcome_text": "Welkomsttekst", "program": "Programma", "dresscode": "Dresscode", "practical": "Praktische informatie",
        "contact": "Contactpersoon", "closing_text": "Afsluitende tekst", "rsvp": "Aanmeldinstellingen", "photos": "Foto's",
        "story": "Verhaal", "music": "Muziek", "style": "Stijl", "sections": "Onderdelen",
    }
    latest_content = latest.draft_content
    differing = [labels.get(k, k) for k in keys if latest_content.get(k) != mine.get(k)]
    return {
        "by": latest.get_draft_updated_source_display(),
        "by_admin": latest.draft_updated_source == Source.ADMIN,
        "at": latest.draft_updated_at,
        "fields": differing,
    }


def design_step(request, inv: Invitation):
    """Een ander ontwerp kiezen ('Wijzigen'): een tik op een kaart bewaart de keuze en brengt de klant terug waar hij was."""
    templates = _active_templates()
    paid = invitation_is_paid(inv)
    terug = _terug(request, inv, _na_ontwerp(inv))
    if request.method == "POST":
        form = DesignForm(request.POST, templates=templates)
        try:
            posted_rev = int(request.POST.get("rev", "0"))
        except ValueError:
            posted_rev = 0
        if form.is_valid():
            actief = request.session.get(ACTIEF_CONCEPT) or {}
            onaangeroerd = actief.get("uid") == str(inv.uid) and actief.get("rev") == inv.draft_rev     # nog niets ingevuld
            template = form.cleaned_data["template_obj"]
            occasion = form.cleaned_data["occasion"]
            version = inv.template_version if template.pk == inv.template_version.template_id else template.current_version
            content = normalize_content(_content(inv), occasion)
            if version.pk != inv.template_version_id:
                content["style"]["palette"] = version.default_palette_key
                muziek_bij_ontwerp(content, version.manifest)   # een nieuw ontwerp met een eigen track begint met die muziek; een keuze voor een track die het nieuwe ontwerp niet heeft vervalt
            try:
                inv = save_draft(inv, expected_rev=posted_rev, content=content, template_version=version, occasion=occasion,
                                 user=request.user, source=_source(request), step="gegevens")

            except DraftConflict:
                messages.error(request, "Deze uitnodiging is intussen gewijzigd. Bekijk de nieuwste versie en kies opnieuw.")
                return redirect("studio:step", uid=inv.uid, step="ontwerp")
            if onaangeroerd:
                _onthoud_actief(request, inv)     # een ontwerpwissel is geen invoer: een nieuwe keuze op de startpagina werkt dit concept nog steeds bij
            return redirect("studio:step", uid=inv.uid, step=_terug(request, inv, _na_ontwerp(inv)))
    else:
        form = DesignForm(initial={"occasion": inv.occasion, "template": inv.template_version.template.slug}, templates=templates)
    occasion = request.GET.get("gelegenheid") or request.POST.get("occasion") or inv.occasion
    if occasion not in OCCASION_LABELS:
        occasion = inv.occasion
    return render(
        request,
        "studio/step_ontwerp.html",
        _context(request, inv, "ontwerp", form=form, rev=inv.draft_rev, templates=collectie_volgorde([t for t in templates if t.supports(occasion)]),
                 occasions=OCCASION_CHOICES, occasion=occasion, occasion_label=OCCASION_LABELS.get(occasion, ""), paid=paid, terug=terug if terug in PERSONALISEER else ""),
    )


# ---------------------------------------------------------------- voorbeeld

def _preview_options(inv: Invitation, content: dict) -> RenderOptions:
    uids = referenced_assets(content)
    assets = {str(a.uid): a for a in MediaAsset.objects.filter(invitation=inv, uid__in=uids)}
    paid = invitation_is_paid(inv)
    return RenderOptions(
        mode="preview",
        features=list(inv.features) if paid else ["story", "gallery", "music", "extra_questions", "zegel"],
        max_gallery_photos=inv.max_gallery_photos if paid else 12,
        resolver=PathResolver(f"/maken/{inv.uid}/media", assets),
        share_url=inv.public_url,
        studio=True,
    )


def preview_step(request, inv: Invitation):
    content = _content(inv)
    issues = publish_issues(content, inv.occasion, first_publication=not inv.is_published)
    blocking = [i for i in issues if i.blocking]
    paid = invitation_is_paid(inv)
    unpaid_features = []
    if paid:
        from invitations.content import required_features
        from catalog.features import feature_label

        unpaid_features = [feature_label(f) for f in sorted(required_features(content) - set(inv.features or []))]
    return render(
        request,
        "studio/step_voorbeeld.html",
        _context(request, inv, "voorbeeld", issues=issues, blocking=blocking, rev=inv.draft_rev,
                 frame_url=reverse("studio:preview_frame", args=[inv.uid]), unpaid_features=unpaid_features,
                 has_changes=inv.has_unpublished_changes, envelop_stap=_envelop_stap(inv),
                 aanpassen=substeps("gegevens", skip=_skip(inv, content), labels=WENSKAART_LABELS if _wenskaart(inv, content) else None)),
    )


@xframe_options_sameorigin
def preview_frame(request, uid):
    inv = get_accessible_invitation(request, uid)
    content = _content(inv)
    options = _preview_options(inv, content)
    options.kader = request.GET.get("kader") == "1"
    view = build_view(occasion=inv.occasion, content=content, overrides=inv.draft_overrides, template_version=inv.template_version, options=options)
    return render(request, inv.template_version.template_path, {"v": view, "rsvp_form": {"client_token": "voorbeeld-formulier-0000", "form_ts": ""}})


LIVE_PARTS = {"envelop", "gegevens", "programma", "aanmelden", "fotos", "stijl"}


def _live_key(inv: Invitation) -> str:
    return f"vierlief-live:{inv.uid}"


@require_POST
def live_update(request, uid, step):
    """Neemt wat de klant nu invult (nog niet opgeslagen) over in de live kaart. Slaat niets op in de uitnodiging:
    het concept staat alleen in de eigen sessie en is alleen via ?concept=1 zichtbaar voor deze bezoeker."""
    inv = get_accessible_invitation(request, uid)
    form_class = FORM_CLASSES.get(step)
    if form_class is None:
        raise Http404()
    if not rate_limit(f"live:{inv.pk}", 600, 3600):
        return JsonResponse({"ok": False}, status=429)
    content = _content(inv)
    form = form_class(request.POST, content=content, occasion=inv.occasion, locked=_locked(request, inv), **_form_kwargs(inv, step))
    if not form.is_valid():
        return JsonResponse({"ok": False})
    request.session[_live_key(inv)] = {"rev": inv.draft_rev, "content": form.apply(copy.deepcopy(content))}
    return JsonResponse({"ok": True, "url": f"{reverse('studio:live_frame', args=[inv.uid])}?deel={step}&concept=1"})


@xframe_options_sameorigin
def live_frame(request, uid):
    """De live kaart naast de invulstappen: meteen open, zonder testbalk, met de foto's gemarkeerd."""
    inv = get_accessible_invitation(request, uid)
    content = _content(inv)
    draft = request.session.get(_live_key(inv)) if request.GET.get("concept") else None
    if draft and draft.get("rev") == inv.draft_rev:
        content = normalize_content(draft["content"], inv.occasion)
    part = request.GET.get("deel", "")
    options = _preview_options(inv, content)
    options.embed = True
    options.live = part if part in LIVE_PARTS else "kaart"
    view = build_view(occasion=inv.occasion, content=content, overrides=inv.draft_overrides, template_version=inv.template_version, options=options)
    return render(request, inv.template_version.template_path, {"v": view, "rsvp_form": {"client_token": "voorbeeld-formulier-0000", "form_ts": ""}})


def media(request, uid, asset_uid, variant):
    inv = get_accessible_invitation(request, uid)
    asset = get_object_or_404(MediaAsset, invitation=inv, uid=asset_uid)
    return serve_asset(request, asset, variant, cache_seconds=300)


# ---------------------------------------------------------------- uploads

@require_POST
def upload(request, uid):
    inv = get_accessible_invitation(request, uid)
    if inv.customer_locked and not request.user.is_staff:
        raise Http404()
    errors, created = [], []
    if not rate_limit(f"upload:{inv.pk}", 80, 3600):
        errors.append("Je hebt veel bestanden geüpload. Probeer het over een uur opnieuw.")
    else:
        photos = request.FILES.getlist("fotos")
        existing = inv.assets.filter(kind=MediaAsset.Kind.PHOTO).count()
        for uploaded in photos:
            name = (uploaded.name or "foto")[:120]
            if existing + len(created) >= MAX_PHOTOS_PER_INVITATION:
                errors.append(f"{name}: je kunt maximaal {MAX_PHOTOS_PER_INVITATION} foto's uploaden. Verwijder eerst foto's die je niet gebruikt.")
                continue
            if uploaded.content_type not in settings.UPLOAD_LIMITS["photo_types"] and not name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                errors.append(f"{name}: dit bestandstype wordt niet ondersteund. Gebruik JPG, PNG of WebP.")
                continue
            try:
                processed = process_photo(uploaded)
            except UploadError as exc:
                errors.append(f"{name}: {exc}")
                continue
            focus = processed.focus
            asset = MediaAsset(invitation=inv, kind=MediaAsset.Kind.PHOTO, original_name=name, content_type="image/webp",
                               size_bytes=processed.size_bytes, width=processed.width, height=processed.height,
                               focus_x=focus.x if focus else 50, focus_y=focus.y if focus else 50,
                               faces=focus.faces if focus else 0,
                               uploaded_by=request.user if request.user.is_authenticated else None)
            asset.file.save("groot.webp", processed.large, save=False)
            asset.file_medium.save("middel.webp", processed.medium, save=False)
            asset.file_thumb.save("klein.webp", processed.thumb, save=False)
            asset.save()
            created.append(asset)
        logo = request.FILES.get("zegel_logo")
        if logo:
            try:
                processed = process_logo(logo)
            except UploadError as exc:
                errors.append(f"{(logo.name or 'logo')[:120]}: {exc}")
            else:
                asset = MediaAsset(invitation=inv, kind=MediaAsset.Kind.LOGO, original_name=(logo.name or "logo")[:120], content_type="image/webp",
                                   size_bytes=processed.size_bytes, width=processed.width, height=processed.height,
                                   uploaded_by=request.user if request.user.is_authenticated else None)
                asset.file.save("logo.webp", processed.large, save=False)
                asset.save()
                created.append(asset)
                content = _content(inv)
                content["style"].setdefault("envelop", {}).update({"logo": str(asset.uid), "zegel": "logo"})
                save_draft(inv, expected_rev=None, content=content, user=request.user, source=_source(request))
                messages.success(request, "Je logo staat op het lakzegel.")
                return redirect(f"{reverse('studio:step', args=[inv.uid, 'stijl'])}#envelop")
        music = request.FILES.get("muziek")
        if music:
            try:
                content_type = sniff_audio(music)
            except UploadError as exc:
                errors.append(f"{(music.name or 'muziek')[:120]}: {exc}")
            else:
                ext = ".m4a" if content_type == "audio/mp4" else ".mp3"
                asset = MediaAsset(invitation=inv, kind=MediaAsset.Kind.AUDIO, original_name=(music.name or "muziek")[:120],
                                   content_type=content_type, size_bytes=music.size,
                                   uploaded_by=request.user if request.user.is_authenticated else None)
                asset.file.save(f"muziek{ext}", music, save=False)
                asset.save()
                created.append(asset)
        if not photos and not music and not logo:
            errors.append("Kies eerst een bestand.")
    placed = _auto_hero(request, inv, [a for a in created if a.kind == MediaAsset.Kind.PHOTO])
    if placed:
        messages.success(request, placed)
    if wants_json(request):
        return JsonResponse(
            {
                "ok": bool(created) and not errors,
                "created": [
                    {"uid": str(a.uid), "kind": a.kind, "name": a.original_name,
                     "thumb": reverse("studio:media", args=[inv.uid, a.uid, "klein"]) if a.kind == "photo" else ""}
                    for a in created
                ],
                "errors": errors,
            },
            status=200 if created or not errors else 400,
        )
    for error in errors:
        messages.error(request, error)
    if created:
        messages.success(request, f"{len(created)} bestand(en) geüpload.")
    return redirect(f"{reverse('studio:step', args=[inv.uid, 'fotos'])}#uploads")


def _auto_hero(request, inv: Invitation, new_photos: list) -> str:
    """Nog geen hoofdfoto? Dan kiezen we er zelf een uit de nieuwe foto's: het liefst een foto van jullie tweeën,
    uitgelijnd op de gezichten. De galerij vullen we niet vanzelf (dat is een extra optie met een prijs)."""
    if not new_photos:
        return ""
    content = _content(inv)
    if (content.get("photos") or {}).get("hero"):
        return ""
    rank = {2: 3, 1: 2}
    best = max(enumerate(new_photos), key=lambda item: (rank.get(item[1].faces or 0, 1 if item[1].faces else 0), -item[0]))[1]
    content["photos"]["hero"] = {"asset": str(best.uid), "x": best.auto_x, "y": best.auto_y, "zoom": 1.0}
    try:
        save_draft(inv, expected_rev=None, content=content, user=request.user, source=_source(request))
    except DraftConflict:
        return ""
    who = {0: "", 1: ", uitgelijnd op het gezicht"}.get(best.faces or 0, ", uitgelijnd op de gezichten")
    return f"{best.original_name or 'Je foto'} staat als hoofdfoto op je kaart{who}. Je kunt dit hieronder altijd aanpassen."


@require_POST
def delete_asset(request, uid, asset_uid):
    inv = get_accessible_invitation(request, uid)
    asset = get_object_or_404(MediaAsset, invitation=inv, uid=asset_uid)
    uid_str = str(asset.uid)
    content = _content(inv)
    photos = content.get("photos") or {}
    if (photos.get("hero") or {}).get("asset") == uid_str:
        photos["hero"] = None
    photos["gallery"] = [g for g in photos.get("gallery") or [] if str(g.get("asset")) != uid_str]
    if (content.get("music") or {}).get("asset") == uid_str:
        content["music"]["asset"] = None
        content["sections"]["music"] = False
    keuze = (content.get("style") or {}).get("envelop") or {}
    if keuze.get("logo") == uid_str:  # logo van het zegel: terug naar initialen
        keuze.update({"logo": "", "zegel": "initialen"})
    save_draft(inv, expected_rev=None, content=content, user=request.user, source=_source(request))
    inv.refresh_from_db()
    still_used = uid_str in referenced_by_any_version(inv)
    if still_used:
        messages.info(request, "Het bestand is uit je concept gehaald. Het blijft bewaard omdat een eerdere of gepubliceerde versie het nog gebruikt.")
    else:
        with transaction.atomic():
            asset.delete_files()
            asset.delete()
        messages.success(request, "Het bestand is verwijderd.")
    if asset.kind == MediaAsset.Kind.LOGO:
        return redirect(f"{reverse('studio:step', args=[inv.uid, 'stijl'])}#envelop")
    return redirect(f"{reverse('studio:step', args=[inv.uid, 'fotos'])}#uploads")


# ------------------------------------------------------------ AI-tekst

@require_POST
def ai_text(request, uid):
    inv = get_accessible_invitation(request, uid)
    if not rate_limit(f"ai:{inv.pk}", 25, 3600) or not rate_limit(f"ai-ip:{ip_fingerprint(request)}", 60, 3600):
        return JsonResponse({"ok": False, "message": "Je hebt veel voorstellen gevraagd. Probeer het later opnieuw."}, status=429)
    field = request.POST.get("field", "")
    if field not in ("welcome_text", "story", "closing_text"):
        return JsonResponse({"ok": False, "message": "Onbekend tekstveld."}, status=400)
    try:
        result = suggest_text(
            field=field,
            occasion=inv.occasion,
            content=_content(inv),
            tone=request.POST.get("tone", "warm"),
            notes=(request.POST.get("notes") or "")[:500],
            current=(request.POST.get("current") or "")[:2000],
        )
    except AIUnavailable as exc:
        return JsonResponse({"ok": False, "message": str(exc)}, status=503)
    return JsonResponse({"ok": True, "suggestion": result.text, "source": result.source, "notice": result.notice})


# ---------------------------------------------------------------- publiceren

@require_POST
def publish(request, uid):
    inv = get_accessible_invitation(request, uid)
    if not invitation_is_paid(inv):
        messages.error(request, "Rond eerst je bestelling af; daarna wordt je uitnodiging automatisch gepubliceerd.")
        return redirect("studio:step", uid=inv.uid, step="bestellen")
    if inv.customer_locked and not request.user.is_staff:
        messages.error(request, "Het VAYLIDE-team werkt op dit moment aan je uitnodiging. Publiceren kan zodra dat klaar is.")
        return redirect("portal:invitation", uid=inv.uid)
    try:
        posted_rev = int(request.POST.get("rev", "0"))
    except ValueError:
        posted_rev = 0
    try:
        version = publish_draft(inv, user=request.user, source=_source(request), expected_rev=posted_rev)
    except DraftConflict:
        messages.error(request, "Er zijn intussen nieuwe wijzigingen opgeslagen (bijvoorbeeld door het VAYLIDE-team of in een ander venster). Bekijk het voorbeeld opnieuw en publiceer daarna.")
        return redirect("studio:step", uid=inv.uid, step="voorbeeld")
    except PublishBlocked as exc:
        messages.error(request, "Nog niet compleet: " + " ".join(i.message for i in exc.issues))
        return redirect("studio:step", uid=inv.uid, step="voorbeeld")
    messages.success(request, f"Je wijzigingen staan online (versie {version.number}). De link blijft hetzelfde.")
    if request.user.is_staff:
        return redirect("beheer:invitation", uid=inv.uid)
    return redirect("portal:invitation", uid=inv.uid)


# ---------------------------------------------------------------- bestellen

def checkout_step(request, inv: Invitation):
    if invitation_is_paid(inv):
        return redirect("portal:invitation", uid=inv.uid)
    content = _content(inv)
    issues = [i for i in publish_issues(content, inv.occasion, first_publication=True) if i.blocking]
    wens = wenskaart.is_wenskaart(content)    # een wenskaart (uitdrukkelijk gekozen): één vaste prijs, geen pakketten, upgrade of extra opties
    packages = [] if wens else list(Package.objects.filter(is_active=True))
    optional = [] if wens else optional_addons()
    selected_extras = request.POST.getlist("extras") if request.method == "POST" else request.GET.getlist("extras")
    selected_extras = [code for code in selected_extras if code in {a.code for a in optional}]
    try:
        quotes = compare_packages(content, selected_extras, template_version=inv.template_version)
    except PricingError as exc:
        quotes = []
        messages.error(request, str(exc))
    best = recommended(quotes)
    codes = {q.package.code for q in quotes}
    chosen = next((c for c in (request.POST.get("wissel"), request.POST.get("package"), request.GET.get("package"), inv.package_code)
                   if c and c in codes), best.package.code if best else "")
    quote = next((q for q in quotes if q.package.code == chosen), best)
    owner_here = request.user.is_authenticated and inv.owner_id == request.user.id
    if quote and not wens and quote.package.code != inv.package_code and (owner_here or inv.owner_id is None):
        inv.package_code = quote.package.code  # een upgrade of ander pakket onthouden
        inv.save(update_fields=["package_code"])
    upgrade = downgrade = None
    if quote and not wens:
        target = pakket.upgrade_target(quote.package, packages)
        upgrade_quote = next((q for q in quotes if target and q.package.code == target.code), None)
        if upgrade_quote:
            upgrade = {"quote": upgrade_quote, "diff_cents": upgrade_quote.total_cents - quote.total_cents,
                       "gains": [h for h in (upgrade_quote.package.highlights or []) if not h.lower().startswith("alles uit")]}
            upgrade["diff_display"] = format_euro(abs(upgrade["diff_cents"]))
        smaller = [q for q in quotes if q.package.price_cents < quote.package.price_cents]
        downgrade = max(smaller, key=lambda q: q.package.price_cents) if smaller else None
    form = CheckoutForm(request.POST or None, packages=[q.package for q in quotes] if wens else packages, optional=optional,
                        initial={"package": chosen, "extras": selected_extras})
    error = ""
    if request.method == "POST" and request.POST.get("actie") == "betalen":
        if not request.user.is_authenticated or inv.owner_id != request.user.id:
            error = "Bevestig eerst je e-mailadres om te kunnen bestellen."
        elif issues:
            error = "Je kaart is nog niet klaar om te bestellen. Bekijk de punten hieronder."
        elif form.is_valid():
            if form.cleaned_data.get("nieuwsbrief"):
                from accounts.newsletter import subscribe

                subscribe(request.user)
            try:
                payment = start_checkout(inv, user=request.user, package_code=form.cleaned_data["package"],
                                         optional_codes=form.cleaned_data.get("extras") or [], terms_accepted=True,
                                         delivery_consent=True, service_consent=True)
            except (CheckoutError, PricingError) as exc:
                error = str(exc)
            else:
                return redirect(payment.checkout_url)
    return render(
        request,
        "studio/step_bestellen.html",
        _context(request, inv, "bestellen", form=form, quotes=quotes, quote=quote, best=best, optional=optional,
                 selected_extras=selected_extras, issues=issues, error=error, test_payments=settings.PAYMENT_PROVIDER == "test",
                 upgrade=upgrade, downgrade=downgrade, nieuwsbrief_tekst=_newsletter_text(),
                 voorwaarden=_terms_info(), **_consent_texts(), looptijd=_availability_hint({**content, "date": ""} if wens else content, quote), losse_extras=pakket.extras_for(quote.package, quote) if quote and not wens else [],
                 login_url=f"{reverse('accounts:login')}?doel=bewaren&next={reverse('studio:step', args=[inv.uid, 'bestellen'])}"),
    )

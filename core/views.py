"""Commerciële website: home, ontwerpen, uitleg, prijzen, vragen, contact en juridische pagina's."""
from __future__ import annotations

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from catalog.assets import design_image_url
from catalog.models import AddOn, Package, Template
from catalog.occasions import OCCASION_CHOICES, OCCASION_LABELS, by_occasion, occasion_config
from catalog.effects import effect_card_label, effect_summary
from invitations.demo import DEFAULT_DEMO_OCCASION

from .content import (ABOUT_POINTS, FAQ, FEATURE_GROUPS, FEATURES, HERO_CHECKS, HOME_DESIGNS, HOME_FAQ_EXTRA, HOME_FAQ_QUESTIONS,
                      HOME_FEATURES, HOME_KERST, OCCASION_TILE_NOTES, OCCASION_TILES, STEPS, STEPS_SHORT, TEXT_SAMPLES, TIPS, VALUES)
from .forms import ContactForm
from .models import ContactMessage, SiteConfig
from .utils import form_age_seconds, ip_fingerprint, rate_limit, signed_timestamp


def _designs():
    return list(Template.objects.filter(is_active=True, current_version__isnull=False).select_related("current_version"))


def _design_cards(designs, occasion=""):
    cards = []
    for template in designs:
        version = template.current_version
        query = f"?gelegenheid={occasion}" if occasion in template.occasions else ""
        cards.append(
            {
                "template": template,
                "opening_label": version.manifest.get("opening_label", ""),
                "effect_label": effect_card_label(version.manifest.get("effects"), version.manifest.get("opening_label", "")),
                "detail_url": reverse("core:design_detail", args=[template.slug]) + query,
                "image": design_image_url(template.slug),
            }
        )
    return cards


def home(request):
    designs = _designs()
    by_slug = {d.slug: d for d in designs}
    featured = [by_slug[s] for s in HOME_DESIGNS if s in by_slug]
    featured += [d for d in designs if d not in featured][: max(0, 3 - len(featured))]
    cheapest = Package.objects.filter(is_active=True).order_by("price_cents").first()
    # Kerstpodium: lichte kerstontwerpen met hun kaartbeeld.
    kerst = [by_slug[s] for s in HOME_KERST if s in by_slug]
    faq_by_question = dict(FAQ)
    home_faq = [(q, faq_by_question[q]) for q in HOME_FAQ_QUESTIONS if q in faq_by_question] + list(HOME_FAQ_EXTRA)
    return render(
        request,
        "core/home.html",
        {
            "kerst_cards": _design_cards(kerst),
            "kerst_note": OCCASION_TILE_NOTES.get("kerst", ""),
            "home_faq": home_faq,
            "cards": _design_cards(featured[:3]),
            "design_count": len(designs),
            "checks": HERO_CHECKS,
            "tiles": OCCASION_TILES,
            "steps": STEPS_SHORT,
            "features": HOME_FEATURES,
            "from_price": cheapest.price_display if cheapest else "",
            "config": SiteConfig.get(),
        },
    )


def designs(request):
    occasion = request.GET.get("gelegenheid", "")
    if occasion not in OCCASION_LABELS:
        occasion = ""
    only_specials = request.GET.get("categorie") == "specials"
    all_designs = [d for d in _designs() if not occasion or occasion in d.occasions]
    # Specials staan apart: nooit tussen de gewone kaarten, wel in een eigen blok en onder de keuze Specials.
    specials = by_occasion([d for d in all_designs if d.special], occasion)
    shown = [] if only_specials else by_occasion([d for d in all_designs if not d.special], occasion)
    return render(
        request,
        "core/designs.html",
        {
            "only_specials": only_specials,
            "special_cards": _design_cards(specials, occasion),
            "cards": _design_cards(shown, occasion),
            "occasions": OCCASION_CHOICES,
            "occasion": occasion,
            "occasion_label": OCCASION_LABELS.get(occasion, ""),
        },
    )


def design_detail(request, slug):
    template = get_object_or_404(Template.objects.select_related("current_version"), slug=slug, is_active=True)
    if template.current_version is None:
        raise Http404()
    version = template.current_version
    occasion = request.GET.get("gelegenheid", "")
    if occasion not in template.occasions:
        occasion = DEFAULT_DEMO_OCCASION.get(slug, template.occasions[0])
    # Gekozen kleurvariant: werkt als gewone link (ook zonder JavaScript); site.js wisselt het voorbeeld zonder herladen.
    palette_keys = [p.get("key") for p in version.palettes]
    kleur = request.GET.get("kleur", "")
    if kleur not in palette_keys:
        kleur = version.default_palette_key
    # Uitnodiging of wenskaart: alleen bij gelegenheden waar het evenement optioneel is (Kerst).
    soorten = []
    soort = ""
    if occasion_config(occasion).get("event_optional"):
        soort = request.GET.get("soort", "")
        if soort not in ("uitnodiging", "wenskaart"):
            soort = "uitnodiging"
        soorten = [
            {"key": key, "label": label, "url": f"?gelegenheid={occasion}&kleur={kleur}&soort={key}", "current": key == soort}
            for key, label in (("uitnodiging", "Uitnodiging"), ("wenskaart", "Wenskaart"))
        ]
    extra = f"&soort={soort}" if soort else ""
    palettes = [
        {**p, "url": f"?gelegenheid={occasion}&kleur={p.get('key')}{extra}", "current": p.get("key") == kleur}
        for p in version.palettes
    ]
    return render(
        request,
        "core/design_detail.html",
        {
            "template": template,
            "version": version,
            "occasion": occasion,
            "kleur": kleur,
            "palettes": palettes,
            "soort": soort,
            "soorten": soorten,
            "occasion_choices": [(k, OCCASION_LABELS[k]) for k in template.occasions if k in OCCASION_LABELS],
            "demo_url": f"{reverse('invitations:demo', args=[slug])}?gelegenheid={occasion}&kleur={kleur}{extra}",
            "start_url": f"{reverse('studio:start')}?ontwerp={slug}&gelegenheid={occasion}&kleur={kleur}{extra}",
            "others": _design_cards([t for t in by_occasion(_designs(), occasion) if t.pk != template.pk and t.supports(occasion)][:3], occasion),
            "occasion_label": OCCASION_LABELS.get(occasion, ""),
            "effects_text": effect_summary(version.manifest.get("effects")),
        },
    )


def how(request):
    by_icon = {icon: (icon, title, text) for icon, title, text in FEATURES}
    groups = [(title, intro, [by_icon[i] for i in icons if i in by_icon]) for title, intro, icons in FEATURE_GROUPS]
    return render(request, "core/how.html", {"steps": STEPS, "feature_groups": groups})


def pricing(request):
    return render(
        request,
        "core/pricing.html",
        {
            "packages": Package.objects.filter(is_active=True),
            "addons": AddOn.objects.filter(is_active=True),
            "config": SiteConfig.get(),
        },
    )


def faq(request):
    return render(request, "core/faq.html", {"faq": FAQ})


def inspiration(request):
    labels = dict(OCCASION_TILES)
    samples = sorted(TEXT_SAMPLES, key=lambda s: list(labels).index(s[0]) if s[0] in labels else 99)
    return render(request, "core/inspiration.html", {"samples": samples, "tips": TIPS})


def about(request):
    return render(request, "core/about.html", {"values": VALUES, "points": ABOUT_POINTS})


def search(request):
    from .search import MAX_QUERY, search_site

    query = (request.GET.get("q") or "").strip()[:MAX_QUERY]
    return render(request, "core/search.html", {"query": query, "results": search_site(query) if query else []})


@require_http_methods(["GET", "POST"])
def contact(request):
    config = SiteConfig.get()
    if request.method == "POST":
        form = ContactForm(request.POST)
        age = form_age_seconds(request.POST.get("form_ts", ""))
        allowed = rate_limit(f"contact:{ip_fingerprint(request)}", 5, 3600)
        if request.POST.get("website") or age is None or age < 3:
            form.add_error(None, "Je bericht kon niet worden verzonden. Vernieuw de pagina en probeer het opnieuw.")
        elif not allowed:
            form.add_error(None, "Je hebt al een aantal berichten gestuurd. Probeer het later opnieuw.")
        if form.is_valid():
            msg = ContactMessage.objects.create(**form.cleaned_data)
            from processing.emails import notify_owner_contact, send_contact_receipt

            notify_owner_contact(msg)
            send_contact_receipt(msg)
            messages.success(request, "Bedankt! Je bericht is ontvangen. Je krijgt een bevestiging per e-mail.")
            return redirect("core:contact")
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {"email": request.user.email, "name": request.user.name}
        if request.GET.get("onderwerp") in dict(ContactMessage.TOPICS):
            initial["topic"] = request.GET["onderwerp"]
        form = ContactForm(initial=initial)
    return render(request, "core/contact.html", {"form": form, "form_ts": signed_timestamp(), "config": config})


def privacy(request):
    from django.conf import settings as dj_settings

    from . import privacyverklaring as pv
    from .company import company

    return render(request, "core/privacy.html", {
        "config": SiteConfig.get(), "b": company(), "versie": pv.VERSION, "besluit": pv.BESLUITEN,
        "open_punten": pv.open_points(), "aanbieders": pv.suppliers(), "cookies": pv.cookies(),
        "ai_actief": pv.ai_active(), "email_actief": pv.email_active(), "backup_actief": pv.backup_offsite_active(),
        "gezichten_actief": dj_settings.FACES_ENABLED,
    })


def _terms_context(version: str) -> dict:
    from django.conf import settings as dj_settings
    from django.urls import reverse

    from .company import company
    from .voorwaarden import CURRENT, VERSIONS, version_info

    if version not in VERSIONS:
        raise Http404()
    base = dj_settings.BASE_URL.rstrip("/")
    links = {"contact": base + reverse("core:contact"), "privacy": base + reverse("core:privacy"),
             "herroepen": base + reverse("orders:withdraw"), "terms": base + reverse("core:terms_version", args=[version])}
    return {"terms": version_info(version), "is_current": version == CURRENT, "b": company(), "links": links, "config": SiteConfig.get()}


def terms(request):
    from .voorwaarden import CURRENT

    return render(request, "core/terms.html", _terms_context(CURRENT))


def terms_version(request, version):
    return render(request, "core/terms.html", _terms_context(version))


def terms_download(request, version):
    from django.template.loader import render_to_string

    from .voorwaarden import filename

    response = HttpResponse(render_to_string("core/terms_download.html", _terms_context(version)), content_type="text/html; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename(version)}"'
    return response


def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /u/",
        "Disallow: /voorbeeld/",
        "Disallow: /account/",
        "Disallow: /beheer/",
        "Disallow: /maken/",
        "Disallow: /bestelling/",
        "Disallow: /betalen/",
        "Disallow: /inloggen/",
        f"Disallow: /{settings.ADMIN_URL}",
        "",
        f"Sitemap: {settings.BASE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    paths = [
        reverse("core:home"),
        reverse("core:designs"),
        reverse("core:how"),
        reverse("core:pricing"),
        reverse("core:faq"),
        reverse("core:inspiration"),
        reverse("core:about"),
        reverse("core:contact"),
        reverse("core:privacy"),
        reverse("core:terms"),
    ] + [reverse("core:design_detail", args=[t.slug]) for t in _designs()]
    urls = "".join(f"<url><loc>{settings.BASE_URL}{p}</loc></url>" for p in paths)
    body = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return HttpResponse(body, content_type="application/xml")


def healthz(request):
    return HttpResponse("ok", content_type="text/plain")


def not_found(request, exception=None):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    # Zonder request-context: werkt ook als de fout in de database of een contextprocessor zit.
    from django.http import HttpResponseServerError
    from django.template import loader

    return HttpResponseServerError(loader.get_template("errors/500.html").render())


def csrf_failure(request, reason=""):
    return render(request, "errors/csrf.html", status=403)


@csrf_exempt
@require_http_methods(["POST"])
def cron_jobs(request):
    """Voor hosts zonder worker: een externe cron roept dit elke minuut aan (met token)."""
    import hmac

    from processing.jobs import process_due

    from .privacy import apply_retention

    token = settings.JOBS_CRON_TOKEN
    given = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not token or not hmac.compare_digest(token, given):
        raise Http404()
    done = process_due()
    report = apply_retention() if request.GET.get("retentie") == "1" else {}
    backup = ""
    if request.GET.get("backup") == "1":
        from .backup import make_backup
        from .offsite import copy_offsite

        made = make_backup()
        backup = f"{made.name} (tweede locatie: {copy_offsite(made)})"
    return HttpResponse(f"taken: {done}; retentie: {report}; backup: {backup}", content_type="text/plain")

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
from catalog import wenskaart
from catalog.models import AddOn, Package, Template, format_euro
from catalog.specials import is_special, special_prijszin
from catalog.occasions import OCCASION_CHOICES, OCCASION_LABELS, collectie_volgorde, occasion_config
from catalog.effects import effect_card_label, effect_summary
from invitations.demo import DEFAULT_DEMO_OCCASION

from . import seo
from .content import (ABOUT_POINTS, FAQ, FEATURE_GROUPS, FEATURES, HERO_CHECKS, HOME_DESIGNS, HOME_FAQ_EXTRA, HOME_FAQ_QUESTIONS,
                      HOME_FEATURES, HOME_KERST, OCCASION_TILE_NOTES, OCCASION_TILES, STEPS, STEPS_SHORT, TEXT_SAMPLES, TIPS, UM_DELEN_GEBRUIK, UM_FAQ, UM_KOP, UM_MEER, UM_ROUTES, UM_STAPPEN, UM_VOORBEELDEN, UM_WAAROM, ZAKELIJK_DELEN, ZAKELIJK_DEMO, ZAKELIJK_FAQ, ZAKELIJK_KOP, ZAKELIJK_MOMENTEN, ZAKELIJK_ONDERDELEN, ZAKELIJK_ONTWERPEN, KERST_BELEVING, KERST_DELEN, VERJAARDAG_BELEVING, VERJAARDAG_DELEN, VERJAARDAG_DEEL_ONTWERP, VERJAARDAG_FAQ, VERJAARDAG_KOP, VERJAARDAG_ONTWERPEN, VERJAARDAG_SOORTEN, KERST_FAMILIE, KERST_FAQ, KERST_KOP, KERST_ONTWERPEN, KERST_ZAKELIJK, TROUW_FAQ, TROUW_KOP,
                      TROUW_UITGELICHT, TROUW_VOORDELEN, VALUES)
from .forms import ContactForm
from .models import ContactMessage, SiteConfig
from .utils import form_age_seconds, ip_fingerprint, rate_limit, signed_timestamp


# Gelegenheden met een eigen SEO-landingspagina: het filter ?gelegenheid=<sleutel> werkt gewoon in de site, maar zijn canonical is die pagina en
# hij staat niet in de sitemap (de pagina staat er wel in).
GELEGENHEID_HUBS = {"bruiloft": "core:wedding_cards", "kerst": "core:christmas_cards", "verjaardag": "core:birthday_invitations", "zakelijk": "core:business_invitations"}
# Op een ontwerppagina: een verwijzing naar de landingspagina('s) van de gelegenheden waar het ontwerp bij hoort: (gelegenheid, tekst van de link).
HUB_LINKS = (("bruiloft", "digitale trouwkaarten"), ("verjaardag", "digitale verjaardagsuitnodigingen"), ("kerst", "digitale kerstkaarten"), ("zakelijk", "digitale zakelijke uitnodigingen"))


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
            "jsonld": [seo.organization(), seo.website()],
        },
    )


def wedding_cards(request):
    """SEO-landingspagina /digitale-trouwkaarten/: echte trouwontwerpen uit de collectie, uitleg, prijzen en vragen."""
    wedding = [d for d in _designs() if "bruiloft" in d.occasions]
    by_slug = {d.slug: d for d in wedding}
    kop = [by_slug[s] for s in TROUW_KOP if s in by_slug]
    featured = [by_slug[s] for s in TROUW_UITGELICHT if s in by_slug]
    packages = list(Package.objects.filter(is_active=True))
    prices = {p.code: p.price_display for p in packages}
    faq = [(q, a.format(essentieel=prices.get("essentieel", ""), compleet=prices.get("compleet", ""), special_zin=special_prijszin())) for q, a in TROUW_FAQ]
    cheapest = min(packages, key=lambda p: p.price_cents) if packages else None
    path = reverse("core:wedding_cards")
    return render(
        request,
        "core/trouwkaarten.html",
        {
            "kop_cards": _design_cards(kop, "bruiloft"),
            "cards": _design_cards(featured, "bruiloft"),
            "wedding_count": len(wedding),
            "benefits": TROUW_VOORDELEN,
            "features": HOME_FEATURES,
            "steps": STEPS_SHORT,
            "packages": packages,
            "faq": faq,
            "from_price": cheapest.price_display if cheapest else "",
            "config": SiteConfig.get(),
            "jsonld": [seo.breadcrumbs([("Home", "/"), ("Digitale trouwkaarten", path)]), seo.faq_page(faq)],
        },
    )


def christmas_cards(request):
    """SEO-landingspagina /digitale-kerstkaarten/: echte kerstontwerpen uit de collectie, beleving, familie en zakelijk, delen, stappen en vragen."""
    kerst = [d for d in _designs() if "kerst" in d.occasions]
    by_slug = {d.slug: d for d in kerst}

    def kies(slugs):
        return [by_slug[s] for s in slugs if s in by_slug]

    packages = {p.code: p.price_display for p in Package.objects.filter(is_active=True)}
    antwoorden = dict(wens=format_euro(wenskaart.PRIJS_CENTS), wens_special=format_euro(wenskaart.PRIJS_SPECIAL_CENTS),
                      essentieel=packages.get("essentieel", ""), compleet=packages.get("compleet", ""))
    faq = [(q, a.format(**antwoorden)) for q, a in KERST_FAQ]
    familie = _design_cards(kies([KERST_FAMILIE]), "kerst")
    path = reverse("core:christmas_cards")
    return render(
        request,
        "core/kerstkaarten.html",
        {
            "kop_cards": _design_cards(kies(KERST_KOP), "kerst"),
            "cards": _design_cards(kies(KERST_ONTWERPEN), "kerst"),
            "familie_card": familie[0] if familie else None,
            "zakelijk_cards": _design_cards(kies(KERST_ZAKELIJK), "kerst"),
            "kerst_count": len(kerst),
            "beleving": KERST_BELEVING,
            "delen": KERST_DELEN,
            "steps": [
                ("kaarten", "Kies een ontwerp", "Uit onze kerstcollectie, van klassiek goud tot een gesloten cadeau met sneeuwbol."),
                ("potlood", "Personaliseer", "Afzender, boodschap en eventueel een foto. Bij een uitnodiging ook datum, programma en locatie."),
                ("oog", "Bekijk het voorbeeld", "Zie direct hoe jouw kaart opent en beweegt, op telefoon en computer."),
                ("versturen", "Deel de kaart", "Na je betaling een eigen link en QR-code, om te delen via WhatsApp of e-mail."),
            ],
            "wens_prijs": antwoorden["wens"],
            "wens_prijs_special": antwoorden["wens_special"],
            "essentieel_prijs": antwoorden["essentieel"],
            "faq": faq,
            "config": SiteConfig.get(),
            "jsonld": [seo.breadcrumbs([("Home", "/"), ("Digitale kerstkaarten", path)]), seo.faq_page(faq)],
        },
    )


def birthday_invitations(request):
    """SEO-landingspagina /digitale-verjaardagsuitnodigingen/: echte verjaardagsontwerpen uit de collectie, soorten verjaardagen, RSVP, delen, stappen en vragen."""
    verjaardag = [d for d in _designs() if "verjaardag" in d.occasions]
    by_slug = {d.slug: d for d in verjaardag}

    def kies(slugs):
        return [by_slug[s] for s in slugs if s in by_slug]

    packages = {p.code: p.price_display for p in Package.objects.filter(is_active=True)}
    faq = [(q, a.format(essentieel=packages.get("essentieel", ""), compleet=packages.get("compleet", ""))) for q, a in VERJAARDAG_FAQ]
    soorten = []
    for slug, titel, tekst in VERJAARDAG_SOORTEN:
        kaart = _design_cards(kies([slug]), "verjaardag")
        if kaart:
            soorten.append({"titel": titel, "tekst": tekst, "card": kaart[0]})
    deel = _design_cards(kies([VERJAARDAG_DEEL_ONTWERP]), "verjaardag")
    path = reverse("core:birthday_invitations")
    return render(
        request,
        "core/verjaardagsuitnodigingen.html",
        {
            "kop_cards": _design_cards(kies(VERJAARDAG_KOP), "verjaardag"),
            "cards": _design_cards(kies(VERJAARDAG_ONTWERPEN), "verjaardag"),
            "soorten": soorten,
            "deel_card": deel[0] if deel else None,
            "verjaardag_count": len(verjaardag),
            "beleving": VERJAARDAG_BELEVING,
            "delen": VERJAARDAG_DELEN,
            "steps": [
                ("kaarten", "Kies een ontwerp", "Uit onze verjaardagscollectie, van feestelijk en modern tot ingetogen en luxe."),
                ("potlood", "Personaliseer", "Naam van de jarige, leeftijd, datum, tijd, locatie, een foto en je eigen tekst."),
                ("oog", "Bekijk het voorbeeld", "Zie direct hoe jouw uitnodiging opent en eruitziet, op telefoon en computer."),
                ("versturen", "Deel met je gasten", "Na je betaling een eigen link en QR-code, om te delen via WhatsApp of e-mail."),
            ],
            "essentieel_prijs": packages.get("essentieel", ""),
            "compleet_prijs": packages.get("compleet", ""),
            "faq": faq,
            "config": SiteConfig.get(),
            "jsonld": [seo.breadcrumbs([("Home", "/"), ("Digitale verjaardagsuitnodigingen", path)]), seo.faq_page(faq)],
        },
    )


def business_invitations(request):
    """SEO-landingspagina /digitale-zakelijke-uitnodigingen/: zakelijke ontwerpen uit de collectie, zakelijke momenten, aanmelden, delen, branding, stappen en vragen."""
    zakelijk = [d for d in _designs() if "zakelijk" in d.occasions]
    by_slug = {d.slug: d for d in zakelijk}

    def kies(slugs):
        return [by_slug[s] for s in slugs if s in by_slug]

    packages = {p.code: p.price_display for p in Package.objects.filter(is_active=True)}
    faq = [(q, a.format(essentieel=packages.get("essentieel", ""), compleet=packages.get("compleet", ""))) for q, a in ZAKELIJK_FAQ]
    path = reverse("core:business_invitations")
    return render(
        request,
        "core/zakelijke_uitnodigingen.html",
        {
            "kop_cards": _design_cards(kies(ZAKELIJK_KOP), "zakelijk"),
            "cards": _design_cards(kies(ZAKELIJK_ONTWERPEN), "zakelijk"),
            "zakelijk_count": len(zakelijk),
            "demo_slug": ZAKELIJK_DEMO if ZAKELIJK_DEMO in by_slug else "",
            "momenten": ZAKELIJK_MOMENTEN,
            "onderdelen": ZAKELIJK_ONDERDELEN,
            "delen": ZAKELIJK_DELEN,
            "steps": [
                ("Kies een ontwerp", "Uit onze zakelijke collectie, van ingetogen tot feestelijk."),
                ("Vul de gegevens in", "Naam van het evenement, organisatie, datum, tijd, locatie, programma en contactpersoon."),
                ("Bekijk het voorbeeld", "Zie direct hoe jouw uitnodiging opent en eruitziet, op telefoon en computer."),
                ("Bestel", "Je betaalt eenmalig, pas als je tevreden bent. Daarna wordt de uitnodiging gepubliceerd."),
                ("Deel met je genodigden", "Via de link of QR-code, in je eigen e-mail, intranet of WhatsApp."),
            ],
            "essentieel_prijs": packages.get("essentieel", ""),
            "compleet_prijs": packages.get("compleet", ""),
            "faq": faq,
            "config": SiteConfig.get(),
            "jsonld": [seo.breadcrumbs([("Home", "/"), ("Digitale zakelijke uitnodigingen", path)]), seo.faq_page(faq)],
        },
    )


def make_invitation(request):
    """SEO-landingspagina /digitale-uitnodiging-maken/: de brede instappagina met routes naar de landingspagina's per gelegenheid."""
    ontwerpen = {d.slug: d for d in _designs()}

    def kaart(slug, gelegenheid):
        return _design_cards([ontwerpen[slug]], gelegenheid)[0] if slug in ontwerpen else None

    packages = {p.code: p.price_display for p in Package.objects.filter(is_active=True)}
    prijzen = dict(essentieel=packages.get("essentieel", ""), compleet=packages.get("compleet", ""), wens=format_euro(wenskaart.PRIJS_CENTS), special_zin=special_prijszin())
    faq = [(q, a.format(**prijzen)) for q, a in UM_FAQ]
    kop = [{"label": label, "card": kaart(slug, key)} for key, label, slug in UM_KOP if slug in ontwerpen]
    routes = [{"label": label, "url": reverse(hub), "card": kaart(slug, key), "tekst": tekst} for key, label, hub, slug, tekst in UM_ROUTES if slug in ontwerpen]
    alle = {"bruiloft": "Alle trouwontwerpen", "verjaardag": "Alle verjaardagsontwerpen", "kerst": "Alle kerstontwerpen", "zakelijk": "Alle zakelijke ontwerpen"}
    voorbeelden = [{"label": label, "alle": alle[key], "url": reverse(hub), "cards": [c for c in (kaart(s, key) for s in slugs) if c]} for key, label, hub, slugs in UM_VOORBEELDEN]
    path = reverse("core:make_invitation")
    return render(
        request,
        "core/uitnodiging_maken.html",
        {
            "kop": kop,
            "routes": routes,
            "meer": UM_MEER,
            "demo_slug": "avondgoud" if "avondgoud" in ontwerpen else "",
            "stappen": UM_STAPPEN,
            "delen": UM_DELEN_GEBRUIK,
            "voorbeelden": voorbeelden,
            "waarom": [(t, x.format(**prijzen)) for t, x in UM_WAAROM],
            "design_count": len(ontwerpen),
            "faq": faq,
            "essentieel_prijs": prijzen["essentieel"],
            "compleet_prijs": prijzen["compleet"],
            "config": SiteConfig.get(),
            "jsonld": [seo.breadcrumbs([("Home", "/"), ("Digitale uitnodiging maken", path)]), seo.faq_page(faq)],
        },
    )


def designs(request):
    occasion = request.GET.get("gelegenheid", "")
    if occasion not in OCCASION_LABELS:
        occasion = ""
    only_specials = request.GET.get("categorie") == "specials"
    all_designs = [d for d in _designs() if not occasion or occasion in d.occasions]
    # Specials staan apart: nooit tussen de gewone kaarten, wel in een eigen blok en onder de keuze Specials.
    ordered = collectie_volgorde(all_designs)    # Specials eerst, daarna de gewone ontwerpen; overal het nieuwste eerst
    specials = [d for d in ordered if d.special]
    shown = [] if only_specials else [d for d in ordered if not d.special]
    list_path = reverse("core:designs")
    crumbs = [("Home", "/"), ("Collectie", list_path)]
    seo_title = seo_description = ""
    if occasion:
        # Elke gelegenheid is een eigen pagina met eigen titel en beschrijving, dus ook een eigen canonical.
        list_path = f"{list_path}?gelegenheid={occasion}"
        seo_title, seo_description = seo.OCCASION_SEO[occasion]
        crumbs.append((f"Ontwerpen voor {OCCASION_LABELS[occasion].lower()}", list_path))
        if occasion in GELEGENHEID_HUBS:
            list_path = reverse(GELEGENHEID_HUBS[occasion])  # de canonical van dit filter is zijn landingspagina (Digitale trouwkaarten, Digitale kerstkaarten)
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
            "canonical_path": list_path,
            "seo_title": seo_title,
            "seo_description": seo_description,
            "jsonld": [seo.breadcrumbs(crumbs)],
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
    # Uitnodiging of wenskaart, bij elke gelegenheid: het voorbeeld toont de kaart als uitnodiging of als wenskaart.
    soort = request.GET.get("soort", "")
    if soort not in ("uitnodiging", "wenskaart"):
        soort = "uitnodiging"
    soorten = [
        {"key": key, "label": label, "url": f"?gelegenheid={occasion}&kleur={kleur}&soort={key}", "current": key == soort}
        for key, label in (("uitnodiging", "Uitnodiging"), ("wenskaart", "Wenskaart"))
    ]
    wenskaart_prijs = format_euro(wenskaart.prijs_cents(template))
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
            "wenskaart_prijs": wenskaart_prijs,
            "wenskaart_special": is_special(template),
            "occasion_choices": [(k, OCCASION_LABELS[k]) for k in template.occasions if k in OCCASION_LABELS],
            "demo_url": f"{reverse('invitations:demo', args=[slug])}?gelegenheid={occasion}&kleur={kleur}{extra}",
            "start_url": f"{reverse('studio:start')}?ontwerp={slug}&gelegenheid={occasion}&kleur={kleur}{extra}&direct=1",
            "others": _design_cards(collectie_volgorde([t for t in _designs() if t.pk != template.pk and t.supports(occasion)])[:3], occasion),
            "hub_links": [(tekst, reverse(GELEGENHEID_HUBS[key])) for key, tekst in HUB_LINKS if key in template.occasions],
            "occasion_label": OCCASION_LABELS.get(occasion, ""),
            "effects_text": effect_summary(version.manifest.get("effects")),
            "image_url": seo.absolute(design_image_url(slug)),
            "seo_kind": "kerstkaart" if template.occasions == ["kerst"] else "uitnodiging",
            "seo_description": seo.design_description(template.tagline, "kerstkaart" if template.occasions == ["kerst"] else "uitnodiging"),
            "jsonld": [seo.breadcrumbs([("Home", "/"), ("Collectie", reverse("core:designs")), (template.name, reverse("core:design_detail", args=[slug]))])],
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
            "wenskaart_prijs": format_euro(wenskaart.PRIJS_CENTS),
            "wenskaart_prijs_special": format_euro(wenskaart.PRIJS_SPECIAL_CENTS),
            "wenskaart_punten": wenskaart.HIGHLIGHTS,
        },
    )


def faq(request):
    return render(request, "core/faq.html", {"faq": FAQ})


def inspiration(request):
    labels = dict(OCCASION_TILES)
    samples = sorted(TEXT_SAMPLES, key=lambda s: list(labels).index(s[0]) if s[0] in labels else 99)
    # Bovenaan de ontwerpen, met dezelfde kaarten en dezelfde volgorde als de Collectie: Specials eerst, overal het nieuwste eerst.
    ordered = collectie_volgorde(_designs())
    return render(request, "core/inspiration.html", {
        "samples": samples, "tips": TIPS,
        "special_cards": _design_cards([d for d in ordered if d.special]),
        "nieuwste_cards": _design_cards([d for d in ordered if not d.special][:6]),
    })


def about(request):
    return render(request, "core/about.html", {"values": VALUES, "points": ABOUT_POINTS})


def search(request):
    from .search import MAX_QUERY, search_site

    query = (request.GET.get("q") or "").strip()[:MAX_QUERY]
    return render(request, "core/search.html", {"query": query, "results": search_site(query) if query else []})


@require_http_methods(["GET", "HEAD", "POST"])  # HEAD: controlerobots (zoals die van Mollie) vragen soms alleen de kop op
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
        "clarity_actief": pv.clarity_active(), "clarity_goedgekeurd": pv.CLARITY_TEKST_GOEDGEKEURD, "clarity_besluit": pv.CLARITY_BESLUITEN,
        "google_actief": pv.google_active(), "google_goedgekeurd": pv.GOOGLE_TEKST_GOEDGEKEURD,
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


def terms_pdf(request, version):
    """De voorwaarden als pdf om te lezen en op te slaan (in de browser geopend; opslaan via de pdf-lezer)."""
    from .voorwaarden import VERSIONS, pdf_filename
    from .voorwaarden_pdf import render_pdf

    if version not in VERSIONS:
        raise Http404()
    response = HttpResponse(render_pdf(version), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{pdf_filename(version)}"'
    return response


def _root_icoon(naam: str, content_type: str):
    """Een tabblad- of homescreen-icoon op het adres dat browsers en programma's zelf proberen (/favicon.ico, /apple-touch-icon.png).
    De pagina's verwijzen met een eigen, versie-adres naar dezelfde bestanden; dit voorkomt alleen een 404 op de hoofdmap."""
    from django.contrib.staticfiles import finders
    from django.http import FileResponse

    pad = finders.find(f"img/{naam}")
    if not pad:
        raise Http404
    return FileResponse(open(pad, "rb"), content_type=content_type, headers={"Cache-Control": "public, max-age=86400"})


def favicon(request):
    return _root_icoon("favicon.ico", "image/x-icon")


def apple_touch_icon(request):
    return _root_icoon("apple-touch-icon.png", "image/png")


def robots_txt(request):
    # Het pad van het systeembeheer staat hier bewust niet: dat moet moeilijk te raden blijven (het krijgt wel noindex).
    if settings.PREVIEW_PASSWORD:
        # Afgeschermde testversie: niets indexeren, ook niet als de informatiepagina's tijdelijk open staan.
        return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain; charset=utf-8")
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
        "",
        f"Sitemap: {settings.BASE_URL}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    paths = [
        reverse("core:home"),
        reverse("core:designs"),
        reverse("core:make_invitation"),
        reverse("core:how"),
        reverse("core:pricing"),
        reverse("core:faq"),
        reverse("core:inspiration"),
        reverse("core:about"),
        reverse("core:contact"),
        reverse("core:privacy"),
        reverse("core:terms"),
    ]
    designs_list = _designs()
    # Elke gelegenheid met ontwerpen is een eigen pagina (eigen titel, beschrijving en canonical).
    # De landingspagina's (Digitale trouwkaarten, Digitale kerstkaarten) staan in de sitemap, hun gelegenheidsfilter niet (zie GELEGENHEID_HUBS).
    paths += [reverse(hub) for hub in GELEGENHEID_HUBS.values()]
    paths += [f"{reverse('core:designs')}?gelegenheid={key}" for key, _label in OCCASION_CHOICES
              if key not in GELEGENHEID_HUBS and any(key in d.occasions for d in designs_list)]
    paths += [reverse("core:design_detail", args=[t.slug]) for t in designs_list]
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


def envelop_lab(request):
    """Ontwerpstudio voor de envelopcollectie (catalog/envelop_collectie.py). Alleen met DEBUG (lokaal); nooit bereikbaar
    op de live site. ?stijl= kiest de envelop, ?zegel= een ander zegel, ?monogram= initialen in plaats van de V."""
    if not settings.DEBUG:
        raise Http404
    from catalog import envelop_collectie

    lijn = "kerst" if request.GET.get("lijn") == "kerst" else ""
    env = envelop_collectie.envelop("lab", request.GET.get("stijl") or ("royal-evergreen" if lijn else None),
                                    request.GET.get("zegel"), request.GET.get("monogram", ""),
                                    kicker="Wij gaan trouwen", title="Sanne & Daan", date="12 · 06 · 2027")
    if env["s"]["lijn"] == "kerst":
        env.update(kicker="Kerstgroet", title="Familie de Vries", date="December 2026")
    return render(request, "core/envelop_lab.html", {"env": env, "stijlen": envelop_collectie.STIJLEN})

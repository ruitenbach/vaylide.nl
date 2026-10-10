"""Specials: bijzondere ontwerpen (zoals Balzaal) in een eigen categorie, met een eigen, apart in te stellen meerprijs.

Een ontwerp is een special als in de catalogus 'special' aan staat (Beheer → Ontwerpen; bij een nieuw ontwerp uit
"special": true in het manifest). Het staat dan niet tussen de gewone kaarten maar onder Specials. De meerprijs is een extra optie in Beheer → Prijzen met functie 'special' en code 'special-<ontwerpcode>'
(bijv. special-balzaal). Zolang die optie er niet is, is de special niet te bestellen: er komt nooit een verzonnen prijs.
"""
from __future__ import annotations


def is_special(template_or_version) -> bool:
    template = getattr(template_or_version, "template", None) or template_or_version
    return bool(getattr(template, "special", False))


def addon_code(slug: str) -> str:
    return f"special-{slug}"


def special_addon(template):
    from .models import AddOn

    return AddOn.objects.filter(is_active=True, feature="special", code=addon_code(template.slug)).first()


def special_prijszin() -> str:
    """Eén zin over wat een special extra kost, passend bij wat er in Beheer → Prijzen is ingesteld (nooit een verzonnen prijs).
    Alle teksten op de site die iets over de prijs van specials zeggen, gebruiken deze zin, zodat tekst en berekende prijs overeenkomen."""
    from .models import AddOn, Template

    slugs = list(Template.objects.filter(special=True, is_active=True).values_list("slug", flat=True))
    if not slugs:
        return ""
    met = set(AddOn.objects.filter(is_active=True, feature="special", code__in=[addon_code(s) for s in slugs]).values_list("code", flat=True))
    aantal = sum(1 for s in slugs if addon_code(s) in met)
    if aantal == len(slugs):
        return "Een special heeft een eigen meerprijs, die je vóór het afrekenen ziet."
    if aantal == 0:
        return "Bij een uitnodiging kost een special op dit moment niets extra: je betaalt de prijs van je pakket."
    return "Sommige specials hebben een eigen meerprijs, die je vóór het afrekenen ziet; bij de andere betaal je de prijs van je pakket."


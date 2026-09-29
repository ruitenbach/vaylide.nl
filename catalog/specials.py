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

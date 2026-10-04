"""Kleine templatehulpmiddelen voor Vaylide."""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from catalog.assets import design_image_url
from core.csp import BOOT_SCRIPT
from core.icons import ICONS
from core.seo import render_json_ld
from catalog.models import format_euro

register = template.Library()


@register.simple_tag
def design_image(slug):
    """URL van de voorbeeldafbeelding van een ontwerp (met standaardafbeelding als terugval)."""
    return design_image_url(slug)


@register.filter
def get_item(mapping, key):
    try:
        return mapping.get(key, "")
    except AttributeError:
        return ""


@register.filter
def euro(cents):
    return format_euro(cents)


@register.filter
def initial(value):
    value = str(value or "").strip()
    return value[:1].upper() if value else ""


@register.simple_tag
def boot_script():
    """Inline startscript; de hash staat in de Content-Security-Policy (core/csp.py)."""
    return mark_safe(f"<script>{BOOT_SCRIPT}</script>")


@register.simple_tag
def icon(name, size=24, css_class=""):
    """Inline lijnicoon uit core/icons.py (decoratief: verborgen voor schermlezers)."""
    paths = ICONS.get(name)
    if paths is None:
        return ""
    classes = f"icon {css_class}".strip()
    return format_html(
        '<svg class="{}" viewBox="0 0 24 24" width="{}" height="{}" aria-hidden="true" focusable="false" fill="none" '
        'stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">{}</svg>',
        classes, size, size, mark_safe(paths),
    )


@register.filter
def invul(value, placeholder):
    """De waarde, of een herkenbaar invulveld als die ontbreekt (alleen de testversie; live start niet zonder)."""
    from django.utils.html import format_html

    if value:
        return value
    return format_html('<mark class="invulveld">{}</mark>', placeholder)


@register.filter
def json_ld(data):
    """Zet een dict om naar een JSON-LD-gegevensblok (zie core/seo.py)."""
    return render_json_ld(data)

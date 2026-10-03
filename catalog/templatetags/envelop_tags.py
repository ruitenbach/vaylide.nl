"""Sjabloontag om een envelop uit de VAYLIDE Envelope Collection in een ontwerp te zetten (als openingsscherm).

Gebruik: {% load envelop_tags %}{% vx_envelop "golden-noel" kicker=... title=... date=... as env %}
         {% include "partials/envelop/collectie.html" %}
"""
from django import template

from catalog import envelop_collectie

register = template.Library()


@register.simple_tag
def vx_envelop(stijl, uid="inv", zegel="", monogram="", kicker="", title="", date="", link="#uitnodiging"):
    return envelop_collectie.envelop(uid, stijl, zegel or None, monogram or "", kicker=kicker, title=title, date=date, link=link)

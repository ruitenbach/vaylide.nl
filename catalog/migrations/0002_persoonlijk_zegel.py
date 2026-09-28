"""Persoonlijk zegel: initialen op het lakzegel horen bij Compleet; Essentieel krijgt een standaard lakzegel.

Past alleen pakketten aan die nog de standaardteksten hebben (wijzigingen van de eigenaar blijven staan).
Prijzen veranderen niet.
"""
from django.db import migrations

OUD_ESSENTIEEL = "Openingsanimatie met persoonlijk zegel"
NIEUW_ESSENTIEEL = "Openingsanimatie met standaard lakzegel (rood of groen)"
NIEUW_COMPLEET = "Persoonlijk zegel met jullie initialen"


def voeg_toe(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    for p in Package.objects.filter(code="essentieel"):
        if OUD_ESSENTIEEL in (p.highlights or []):
            p.highlights = [NIEUW_ESSENTIEEL if h == OUD_ESSENTIEEL else h for h in p.highlights]
            p.save(update_fields=["highlights"])
    for p in Package.objects.filter(code="compleet"):
        changed = []
        if "zegel" not in (p.features or []):
            p.features = list(p.features or []) + ["zegel"]
            changed.append("features")
        highlights = list(p.highlights or [])
        if NIEUW_COMPLEET not in highlights:
            pos = 1 if highlights and highlights[0] == "Alles uit Essentieel" else len(highlights)
            highlights.insert(pos, NIEUW_COMPLEET)
            p.highlights = highlights
            changed.append("highlights")
        if changed:
            p.save(update_fields=changed)


def terug(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    for p in Package.objects.filter(code="essentieel"):
        if NIEUW_ESSENTIEEL in (p.highlights or []):
            p.highlights = [OUD_ESSENTIEEL if h == NIEUW_ESSENTIEEL else h for h in p.highlights]
            p.save(update_fields=["highlights"])
    for p in Package.objects.filter(code="compleet"):
        p.features = [f for f in (p.features or []) if f != "zegel"]
        p.highlights = [h for h in (p.highlights or []) if h != NIEUW_COMPLEET]
        p.save(update_fields=["features", "highlights"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0001_initial")]
    operations = [migrations.RunPython(voeg_toe, terug)]

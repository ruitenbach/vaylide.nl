"""Envelop en lakzegel naar keuze voor alle pakketten (keuze van de eigenaar, september 2026): Essentieel krijgt
ook het persoonlijk zegel. Past alleen de standaardteksten aan (wijzigingen van de eigenaar blijven staan).
Prijzen veranderen niet. Al betaalde uitnodigingen houden hun eigen rechten.
"""
from django.db import migrations

OUD_ESSENTIEEL = "Openingsanimatie met standaard lakzegel (rood of groen)"
NIEUW_ESSENTIEEL = "Envelop en lakzegel naar keuze, met jullie initialen of eigen logo"
OUD_COMPLEET = "Persoonlijk zegel met jullie initialen"


def voeg_toe(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    for p in Package.objects.filter(code="essentieel"):
        fields = []
        if "zegel" not in (p.features or []):
            p.features = list(p.features or []) + ["zegel"]
            fields.append("features")
        if OUD_ESSENTIEEL in (p.highlights or []):
            p.highlights = [NIEUW_ESSENTIEEL if h == OUD_ESSENTIEEL else h for h in p.highlights]
            fields.append("highlights")
        if fields:
            p.save(update_fields=fields)
    for p in Package.objects.filter(code="compleet"):
        if OUD_COMPLEET in (p.highlights or []):
            p.highlights = [h for h in p.highlights if h != OUD_COMPLEET]
            p.save(update_fields=["highlights"])


def terug(apps, schema_editor):
    Package = apps.get_model("catalog", "Package")
    for p in Package.objects.filter(code="essentieel"):
        p.features = [f for f in (p.features or []) if f != "zegel"]
        p.highlights = [OUD_ESSENTIEEL if h == NIEUW_ESSENTIEEL else h for h in (p.highlights or [])]
        p.save(update_fields=["features", "highlights"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_special")]
    operations = [migrations.RunPython(voeg_toe, terug)]

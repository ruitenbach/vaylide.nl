"""Eenmalige afstemming van bestaande databases met de officiële collectie (catalog/collectie.py).

C-ontwerpen worden niet verwijderd maar op 'niet zichtbaar' gezet, Midnight Émeraude en Rosé Royale worden specials en een
paar ontwerpen krijgen een eigen volgorde. Daarna beslist Beheer weer. Nieuwe databases hebben nog geen ontwerpen op dit moment;
die krijgen de waarden via de manifesten en catalog/seed.py.
"""
from django.db import migrations


def pas_collectie_toe(apps, schema_editor):
    from catalog.collectie import pas_toe

    pas_toe(apps.get_model("catalog", "Template"))


class Migration(migrations.Migration):
    dependencies = [("catalog", "0005_vaste_vragen")]
    operations = [migrations.RunPython(pas_collectie_toe, migrations.RunPython.noop)]

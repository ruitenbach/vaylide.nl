"""Extra vragen bij aanmelden alleen uit een vaste lijst (keuze van de eigenaar, 30 september 2026: geen gevoelige
gegevens uitvragen). Past alleen de standaardomschrijving van de extra optie aan; een door de eigenaar gewijzigde tekst
blijft staan. Prijzen en al betaalde bestellingen veranderen niet.
"""
from django.db import migrations

OUD = "Tot 5 eigen vragen, bijvoorbeeld over dieetwensen."
NIEUW = "Tot 5 extra vragen uit een vaste lijst, bijvoorbeeld over vervoer of overnachten."


def vervang(apps, schema_editor, van=OUD, naar=NIEUW):
    AddOn = apps.get_model("catalog", "AddOn")
    AddOn.objects.filter(code="extra-vragen", description=van).update(description=naar)


def terug(apps, schema_editor):
    vervang(apps, schema_editor, van=NIEUW, naar=OUD)


class Migration(migrations.Migration):
    dependencies = [("catalog", "0004_zegel_voor_iedereen")]
    operations = [migrations.RunPython(vervang, terug)]

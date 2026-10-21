"""Twee velden op het ontwerp voor de homepage-carrousel (uitlichten ja/nee en de volgorde).

Alleen toevoegen: bestaande ontwerpen krijgen de standaardwaarden (niet uitgelicht, volgorde 100). Er wordt geen bestaand veld gelezen of veranderd.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0008_prijsbeheer_startstand")]

    operations = [
        migrations.AddField(
            model_name="template",
            name="homepage_uitgelicht",
            field=models.BooleanField(
                default=False, verbose_name="uitlichten op homepage",
                help_text="Toont dit ontwerp in de draaibare kaartencarrousel bovenaan de homepage. Alleen zichtbare Luxe- en Special-ontwerpen verschijnen er echt in.",
            ),
        ),
        migrations.AddField(
            model_name="template",
            name="homepage_volgorde",
            field=models.PositiveIntegerField(
                default=100, verbose_name="volgorde op homepage",
                help_text="Lage nummers eerst. De eerste kaart staat bij het openen in het midden.",
            ),
        ),
    ]

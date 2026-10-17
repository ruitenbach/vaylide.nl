"""De startstand van het prijsbeheer: precies de 27 bedragen die op dit moment in de code staan (catalog/prijzen.py, PRIJZEN, 15 oktober 2026).

Bewust een ingevroren kopie en geen import uit de app: een latere codewijziging mag deze migratie niet stilletjes veranderen. Een test vergelijkt de kopie met
catalog.prijzen.PRIJZEN, zodat een afwijking meteen opvalt. Idempotent: een bestaande regel wordt nooit overschreven."""
from django.db import migrations

STARTSTAND = {
    "kerst": (995, 2495, 4995),
    "verjaardag": (1995, 3495, 5995),
    "zakelijk": (1495, 2995, 4995),
    "babyshower": (1995, 3495, 5995),
    "bruiloft": (2995, 5995, 8995),
    "jubileum_verloving": (1995, 3995, 6900),
    "bedank": (995, 1995, 3995),
    "geboorte": (1995, 3495, 5995),
    "savethedate": (1995, 3995, 6900),
}
TIERS = ("basis", "luxe", "special")


def vul(apps, schema_editor):
    PriceRule = apps.get_model("catalog", "PriceRule")
    PriceChangeSet = apps.get_model("catalog", "PriceChangeSet")
    PriceChange = apps.get_model("catalog", "PriceChange")
    nieuw = []
    for rij, bedragen in STARTSTAND.items():
        for tier, cents in zip(TIERS, bedragen):
            _, gemaakt = PriceRule.objects.get_or_create(rij=rij, tier=tier, defaults={"price_cents": cents})
            if gemaakt:
                nieuw.append((rij, tier, cents))
    if nieuw:
        zet = PriceChangeSet.objects.create(kind="seed", reason="Startstand, overgenomen uit de code (catalog/prijzen.py)")
        PriceChange.objects.bulk_create([PriceChange(change_set=zet, rij=r, tier=t, old_cents=None, new_cents=c) for r, t, c in nieuw])


def leeg(apps, schema_editor):
    apps.get_model("catalog", "PriceChange").objects.all().delete()
    apps.get_model("catalog", "PriceChangeSet").objects.all().delete()
    apps.get_model("catalog", "PriceRule").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0007_prijsbeheer")]
    operations = [migrations.RunPython(vul, leeg)]

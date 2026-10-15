"""Controleert de nieuwe prijsstructuur zonder iets te schrijven: de instellingen van de omgeving, de indeling van elk ontwerp en of het getoonde bedrag
(prijs_info) overal gelijk is aan de offerte (build_quote), voor elk ontwerp, elke gelegenheid en elke kaartsoort.

Gebruik (op staging, na het aanzetten van VIERLIEF_PRICING_V2): python manage.py controleer_prijzen
Met --tabel krijg je alle ontwerpen met hun prijzen per gelegenheid. Het commando verandert niets in de database; de exitcode is 1 bij een afwijking."""
from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand

from catalog import prijzen
from catalog.models import Template, format_euro
from orders.pricing import PricingError, build_quote


class Command(BaseCommand):
    help = "Controleert de nieuwe prijsstructuur (alleen lezen)."

    def add_arguments(self, parser):
        parser.add_argument("--tabel", action="store_true", help="Toon alle ontwerpen met hun prijzen per gelegenheid.")

    def handle(self, *args, **opts):
        out = self.stdout.write
        out(f"Omgeving: modus {'test' if settings.TEST_MODE else 'live'}, betaalprovider {settings.PAYMENT_PROVIDER}")
        out(f"VIERLIEF_PRICING_V2 = {prijzen.actief()}   (nieuwe prijzen {'ACTIEF' if prijzen.actief() else 'UIT: de oude pakketten gelden'})")
        out(f"VIERLIEF_PRICING_V2_SINCE = {settings.PRICING_V2_SINCE or '(niet gezet: oude concepten krijgen geen melding over de bijgewerkte prijs)'}")
        fouten = []
        zonder_indeling = [t.slug for t in Template.objects.all() if prijzen.tier(t) is None]
        if zonder_indeling:
            fouten.append(f"Ontwerpen zonder indeling (niet te bestellen): {', '.join(zonder_indeling)}")
        onbekend = sorted(set(prijzen.INDELING) - set(Template.objects.values_list("slug", flat=True)))
        if onbekend:
            out(f"Let op: indeling voor ontwerpen die niet in de catalogus staan: {', '.join(onbekend)}")
        tellers = {t: 0 for t in prijzen.TIERS}
        gecontroleerd = 0
        # De controle rekent met de nieuwe structuur, ook als de schakelaar op deze omgeving nog uit staat.
        from django.test.utils import override_settings

        with override_settings(PRICING_V2=True):
            for t in Template.objects.filter(is_active=True).order_by("sort_order", "slug"):
                indeling = prijzen.tier(t)
                if indeling is None:
                    continue
                tellers[indeling] += 1
                regel = []
                for occasion in t.occasions:
                    for soort in ("", "wenskaart"):
                        info = prijzen.prijs_info(t, occasion, soort)
                        content = {"soort": soort} if soort else {}
                        try:
                            quote = build_quote(content, None, None, template_version=t.current_version, occasion=occasion)
                        except PricingError as exc:
                            fouten.append(f"{t.slug} / {occasion} / {soort or 'uitnodiging'}: geen offerte ({exc})")
                            continue
                        gecontroleerd += 1
                        if info is None or quote.total_cents != info["cents"] or len(quote.lines) != 1 or quote.total_display != info["display"]:
                            fouten.append(f"{t.slug} / {occasion} / {soort or 'uitnodiging'}: getoond {info and info['display']} maar offerte {quote.total_display} ({len(quote.lines)} regels)")
                        regel.append(f"{occasion}{'*' if soort else ''} {format_euro(quote.total_cents)}")
                if opts["tabel"]:
                    out(f"{t.slug:20s} {prijzen.TIER_NAAM[indeling]:8s} " + " | ".join(regel))
        out(f"Zichtbare ontwerpen: Basis {tellers[prijzen.BASIS]}, Luxe {tellers[prijzen.LUXE]}, Special {tellers[prijzen.SPECIAL]} (* = wenskaart)")
        out(f"Combinaties gecontroleerd (ontwerp x gelegenheid x kaartsoort): {gecontroleerd}")
        for rij in ("kerst", "verjaardag", "zakelijk", "babyshower", "bruiloft", "jubileum_verloving", "bedank"):
            with override_settings(PRICING_V2=True):
                beschikbaar = ", ".join(f"{prijzen.TIER_NAAM[i]} {format_euro(c)}" for i, c in prijzen.beschikbaar(rij)) or "(geen ontwerp)"
            out(f"  {prijzen.CATEGORIE_LABEL[rij]:32s} {beschikbaar}")
        if fouten:
            for f in fouten:
                self.stderr.write("AFWIJKING: " + f)
            raise SystemExit(1)
        out("Alles klopt: getoond bedrag = offerte, één regel per kaart, geen toeslagen.")

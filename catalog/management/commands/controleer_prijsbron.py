"""Vergelijkt de prijzen in de database (catalog.PriceRule) met de code (catalog/prijzen.py, PRIJZEN) en controleert dat elke kaart overal hetzelfde bedrag geeft.

Alleen lezen. Draai dit op staging vóór VIERLIEF_PRIJZENBEHEER aan gaat: python manage.py controleer_prijsbron
Controleert (1) of alle 27 bedragen in de database gelijk zijn aan de code, (2) voor elk ontwerp, elke gelegenheid en elke kaartsoort of het bedrag met
databaseprijzen gelijk is aan het bedrag met de code-prijzen en aan de offerte (build_quote). Exitcode 1 bij een afwijking."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.test.utils import override_settings

from catalog import prijsbeheer, prijzen
from catalog.models import Template
from orders.pricing import PricingError, build_quote


class Command(BaseCommand):
    help = "Vergelijkt de prijzen in de database met de code (alleen lezen)."

    def handle(self, *args, **opts):
        out = self.stdout.write
        fouten = []
        verschil = prijsbeheer.verschillen_met_code()
        out(f"Bedragen in de database: {len(prijsbeheer.alle_cellen()) - len(verschil)} van {len(prijsbeheer.alle_cellen())} gelijk aan de code.")
        fouten += [f"Afwijking: {v}" for v in verschil]
        gecontroleerd = 0
        with prijsbeheer.cache_scope():
            for t in Template.objects.filter(is_active=True).order_by("slug"):
                for occasion in t.occasions or []:
                    for soort in ("", "wenskaart"):
                        with override_settings(PRICING_V2=True, PRICES_ADMIN=False):
                            code = prijzen.prijs_cents(t, occasion, soort)
                        with override_settings(PRICING_V2=True, PRICES_ADMIN=True):
                            prijsbeheer.invalidate()
                            db = prijzen.prijs_cents(t, occasion, soort)
                            content = {"soort": soort} if soort else {}
                            try:
                                offerte = build_quote(content, None, None, template_version=t.current_version, occasion=occasion).subtotal_cents
                            except PricingError:
                                offerte = None
                        gecontroleerd += 1
                        if not (code == db == offerte):
                            fouten.append(f"{t.slug} / {occasion} / {soort or 'uitnodiging'}: code {code}, database {db}, offerte {offerte}")
        out(f"Combinaties gecontroleerd (ontwerp x gelegenheid x kaartsoort): {gecontroleerd}")
        if fouten:
            for f in fouten:
                self.stderr.write(f)
            raise SystemExit(1)
        out("Alles klopt: de database geeft voor elke combinatie hetzelfde bedrag als de code en de offerte.")

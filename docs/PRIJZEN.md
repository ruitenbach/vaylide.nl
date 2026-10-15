# Prijsstructuur: Basis, Luxe en Special

Sinds oktober 2026 kent VAYLIDE een nieuwe prijsstructuur naast de oude (pakketten Essentieel en Compleet). Ze staat achter een schakelaar per omgeving en is **standaard uit**.

## Hoe het werkt

- Elk ontwerp heeft **één vaste indeling**: Basis, Luxe of Special (`catalog/prijzen.py`, `INDELING`).
- De **gelegenheid** (en bij een wenskaart de kaartsoort) bepaalt de prijsrij (`PRIJZEN`, `categorie()`). Het bedrag is `PRIJZEN[rij][indeling]`, in centen, inclusief btw.
- Eén functie, `prijzen.prijs_info(ontwerp, gelegenheid, soort)`, levert indeling, bedrag, label ("Luxe — € 34,95") en looptijd. De ontwerppagina, de keuzepagina, het voorbeeld, Bestellen, de offerte (`orders.pricing.build_tier_quote`), de bestelling, de betaling en de bevestiging gebruiken uitsluitend die ene bron. Een test (`tests/test_prijsstructuur.py`) controleert voor elk ontwerp, elke gelegenheid en elke kaartsoort dat getoond bedrag = offerte = één regel.
- **Geen toeslagen.** Alles wat je kunt personaliseren (verhaal, galerij tot 12 foto's, eigen muziek, extra vragen, persoonlijk zegel) zit in elke indeling. Er zijn geen pakketkeuze, upgrade of extra opties bij Bestellen. Alleen "eigen gezichten" (Balzaal) blijft een aparte, nu uitgeschakelde optie en blokkeert het bestellen zolang ze niet bestaat.
- **Online-duur**: voor alle drie de indelingen **12 maanden**, ook voor een wenskaart (besluit van de eigenaar, 15 oktober 2026; `MAANDEN_ONLINE`, één getal per indeling). De duur wordt op de bestelling vastgelegd (`availability_months`) en omgezet in `ends_at` zoals voorheen (`invitations/availability.py`); bestaande bestellingen (Essentieel 6, Compleet 12, wenskaart 6) behouden hun eigen duur. Alle teksten over de duur komen uit `prijzen.looptijd_zin()`.
- **Weergave**: met de schakelaar aan altijd twee decimalen (`€ 69,00`), via `catalog.models.format_euro`.

## De prijzen (incl. btw)

| Soort kaart | Basis | Luxe | Special |
|---|---:|---:|---:|
| Kerstkaart / nieuwjaarswens (`kerst`) | 9,95 | 24,95 | 49,95 |
| Verjaardagsuitnodiging | 19,95 | 34,95 | 59,95 |
| Zakelijk evenement | 14,95 | 29,95 | 49,95 |
| Babyshower / gender reveal | 19,95 | 34,95 | 59,95 |
| Geboortekaart (nog geen gelegenheid) | 19,95 | 34,95 | 59,95 |
| Save the date (nog geen gelegenheid) | 19,95 | 39,95 | 69,00 |
| Trouwuitnodiging (`bruiloft`) | 29,95 | 59,95 | 89,95 |
| Jubileum / verlovingsfeest (`jubileum`, `verloving`) | 19,95 | 39,95 | 69,00 |
| Bedankkaart / felicitatie (wenskaart buiten Kerst, `bedank`) | 9,95 | 19,95 | 39,95 |

Een prijs wordt alleen getoond als er een zichtbaar ontwerp is dat erbij hoort (`prijzen.beschikbaar`). Kerst Basis bestaat daardoor nu niet, en gelegenheden zonder ontwerpen (Geboortekaart, Save the date) zijn niet te kiezen. Een ontwerp is alleen te koop voor gelegenheden waar het bij hoort (`Template.occasions`).

## De indeling per ontwerp

Criteria: **Special** = cinematisch of zeer uitgebreid (eigen film, 3D- of illustratiescène met meerdere lagen en eigen muziek); **Luxe** = eigen ontworpen scène of opening met eigen animaties; **Basis** = standaardopening op de gedeelde atelier-basis. Aantallen: 9 Special, 14 Luxe, 32 Basis (Luxe inclusief Kerstmarkt, Kerstpaleis, Kerstcoupé en Kerstbal: eigen film, op besluit van de eigenaar van 15 oktober 2026 bewust Luxe, € 24,95). De Special-vlag in de catalogus is niet de indeling: Golden Noël heeft de vlag maar is Luxe (een elegante enveloppe zonder eigen scène; kwaliteitscontrole 15 oktober 2026).

**Nieuw ontwerp?** Voeg bij `INDELING` een regel toe; zonder indeling is het ontwerp niet te bestellen (`tests/test_prijsstructuur.py` bewaakt dat elk ontwerp precies één indeling heeft).

## De schakelaar

| Variabele | Betekenis |
|---|---|
| `VIERLIEF_PRICING_V2=1` | nieuwe structuur aan (standaard uit: alles werkt als voorheen) |
| `VIERLIEF_PRICING_V2_SINCE=<ISO-tijd met tijdzone>` | concepten die vóór dit moment zijn gemaakt, tonen bij Bestellen expliciet "De prijs van dit ontwerp is bijgewerkt", met het eerder getoonde bedrag als dat bekend is |

Terugdraaien: zet `VIERLIEF_PRICING_V2` uit (of verwijder de variabele) en laat de dienst herstarten. De oude pakketten en opties zijn nooit aangepast of verwijderd. Bestaande bestellingen veranderen in geen van beide richtingen: bedrag, regels, pakket, looptijd en betaling staan vast op de bestelling.

## Controleren

- `python manage.py controleer_prijzen [--tabel]` (alleen lezen): omgeving, schakelaar, indeling, en voor elk zichtbaar ontwerp x gelegenheid x soort dat getoond bedrag = offerte; exitcode 1 bij een afwijking.
- Tests: `python manage.py test tests` (schakelaar uit: de bestaande tests gelden voor de oude structuur) en `VIERLIEF_PRICING_V2=1 python manage.py test tests.test_prijsstructuur` (ook de controle op alle teksten van de site). De bestaande tests draaien standaard met de schakelaar uit (`tests/helpers.py`).

## Wat bewust niet is aangepast

De algemene voorwaarden (artikel 6: Essentieel 6 en Compleet 12 maanden) en de privacyverklaring noemen de oude pakketten en duren nog; de aangepaste volledige teksten (12 maanden voor alle kaarten, met overgangsregel voor bestaande bestellingen) staan als concept in `docs/concept-juridisch/` (door de eigenaar als concept goedgekeurd op 15 oktober 2026, nog niet juridisch beoordeeld) en worden pas na de livegangbeslissing als nieuwe versie van de voorwaarden doorgevoerd (`core/voorwaarden.py`). Daar staat ook welke bedrijfsgegevens de eigenaar nog moet bevestigen. Een handmatige correctieronde bij Special wordt niet beloofd. Geen nieuwe gelegenheden of ontwerpen. Beheer → Prijzen toont bij een actieve schakelaar alleen de nieuwe structuur (lezen); de oude pakketten daar gelden dan niet voor nieuwe bestellingen.

## Bestaande bestellingen en concepten

- Een bestelling legt bij het starten van de betaling vast: pakket, prijs, maanden online, het moment van akkoord en de versie van de voorwaarden (`terms_version`, ook bij maatwerk). Een latere wijziging van prijzen, schakelaar of voorwaarden raakt die bestelling niet; de einddatum staat vast in `ends_at`.
- Een concept zonder bestelling valt na het aanzetten van de schakelaar onder de nieuwe prijzen en voorwaarden, ook als het ooit met Essentieel of Compleet is begonnen.
- De editor toont alleen voor kaarten die nieuw of in de nieuwe structuur besteld zijn "Inbegrepen" (`studio.pakket.nieuwe_prijsstructuur`); een kaart uit de oude structuur houdt de teksten van zijn eigen pakket. Tests: `tests/test_prijsstructuur.py`, klasse `BestaandeBestellingen`.

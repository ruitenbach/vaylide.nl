# Kortingscodes

Stand: 17 oktober 2026. Gebouwd op een lokale branch, **niet gepusht, niet op staging, niet op productie**. De schakelaar staat standaard uit.

## In het kort

Een klant kan bij Bestellen een kortingscode invullen. De korting is een negatieve regel in de offerte (`orders/pricing.py`, `kortingen/services.py`). Bestelling, betaling, Mollie-bedrag, bon, status en bevestigingsmail lezen allemaal uit die offerte en hebben dus altijd hetzelfde bedrag. De prijzen van Basis, Luxe en Special (en de oude pakketten) veranderen niet.

## Aanzetten

`VIERLIEF_KORTINGSCODES=1` in de omgeving. Uit (standaard) betekent: geen invoerveld, geen onderdeel "Kortingscodes" in Beheer, en een meegestuurde code wordt niet geaccepteerd. Bestaande bestellingen met een code blijven werken als de schakelaar later weer uitgaat. De migraties (`kortingen.0001`, `orders.0004`) zijn alleen toevoegingen en lopen mee met `migrate`; ze veranderen geen bestaande gegevens.

| Instelling | Standaard | Betekenis |
|---|---|---|
| `VIERLIEF_KORTINGSCODES` | uit | De functie aan of uit. |
| `VIERLIEF_KORTING_MINIMUM_CENTEN` | 100 | Het te betalen bedrag wordt nooit lager dan € 1,00. |
| `VIERLIEF_KORTING_RESERVERING_MINUTEN` | 120 | Zo lang telt een nog niet betaalde reservering mee voor het maximum. |
| `VIERLIEF_BTW_PERCENTAGE` | 21 | Alleen voor het tonen van het btw-deel in Beheer. |

## Regels (besluiten van de eigenaar, 17 oktober 2026)

- Geen 100%-codes: percentage 1 tot en met 90 (ook in de database afgedwongen); een vast bedrag wordt afgetopt zodat het totaal minimaal € 1,00 blijft.
- Eén code per bestelling, niet te combineren of te stapelen.
- Standaard één gebruik per klant, instelbaar per code. De controle kijkt naar het account en naar een niet-omkeerbare sleutel van het e-mailadres (kleine letters, zonder plusje, bij Gmail zonder puntjes). Dat vangt de eenvoudigste omwegen. **Het is geen waterdichte fraudepreventie**: wie een ander e-mailadres gebruikt, is een andere klant.
- Bij een terugbetaling blijft de code als gebruikt meetellen. Alleen een beheerder kan hem vrijgeven (Beheer → Bestelling → Kortingscode → "Weer beschikbaar maken"), met verplichte reden; naam, tijdstip en reden staan bij het gebruik en in het logboek van de bestelling.
- De korting geldt op het bedrag inclusief btw; het btw-deel volgt proportioneel (totaal × 21 / 121, op centen afgerond). Beheer toont dat bij een bestelling met korting. **De boekhoudkundige verwerking moet vóór productie bevestigd worden.**

## Hoe een code gaat

1. Controle (`kortingen.services.check_code`): actief, begin- en einddatum (de einddatum geldt tot het einde van die dag), bereik (gelegenheid, indeling, ontwerp; als er meer soorten beperking zijn gekozen moeten ze allemaal kloppen), minimum bestelbedrag, maximum aantal keer, maximum per klant, ondergrens.
2. Reserveren: bij het aanmaken van de bestelling (`orders.services.start_checkout`), in dezelfde vergrendelde transactie, na een nieuwe controle. Twee klanten op de laatste plek: de tweede krijgt "niet meer beschikbaar".
3. Definitief: bij de eerste bevestigde betaling (`apply_remote_status`).
4. Vrijgegeven: bij een mislukte of verlopen betaling, een vervangende bestelling voor dezelfde kaart, of annuleren in Beheer. Een geannuleerde (afgebroken) betaling houdt de reservering vast tot die na 120 minuten vervalt. Bij "Opnieuw betalen" wordt de reservering verlengd of opnieuw gemaakt; lukt dat niet meer, dan volgt geen betaling en een duidelijke melding.
5. Vlak voor Mollie (`create_payment`) controleert de code dat de som van de regels, het ordertotaal en het betaalbedrag gelijk zijn, positief, en niet onder het minimum. Daarnaast vergelijkt `apply_remote_status` het bedrag bij Mollie met de betaling (bestond al).

Bekende rand: betaalt een klant ná het verlopen van de reservering en is de plek intussen aan een ander gegeven, dan blijft de korting staan (de klant betaalde dat bedrag) en staat bij het gebruik en in het betalingslogboek "maximum aantal keer overschreden". Dat kan alleen als iemand meer dan 2 uur na het starten van de betaling afrekent.

## Klantreis

Zie de bestelstap: onder het overzicht staat een bescheiden tekstregel "Heb je een kortingscode?". Aantikken opent een smal veld met "Toepassen" (een gewone `<details>`, werkt zonder JavaScript, geen extra pagina of stap). Na toepassen staan in dezelfde tabel de oorspronkelijke prijs, een regel "Kortingscode ZOMER10 − € 3,50" met een tekstlink "Verwijderen", en het nieuwe totaal; de knop zegt "Bestellen en betalen € …". Fouten staan bij het veld: onbekend, verlopen (met datum), nog niet geldig (met datum), niet meer beschikbaar, niet voor deze gelegenheid of dit ontwerp, al gebruikt, ondergrens. Een code die niet is toegepast maar wel is ingetikt, wordt bij "Bestellen en betalen" eerst toegepast en laat het nieuwe bedrag zien (er wordt niet meteen betaald). Vervalt een toegepaste code vóór het betalen, dan wordt er niet stilletjes tegen de volle prijs afgerekend. Een link met `?code=…` vult alleen het veld in. Pogingen: 10 per kwartier per bezoeker.

## Beheer

Beheer → Kortingscodes (alleen met de schakelaar aan): overzicht met status (gepland, actief, verlopen, opgebruikt, uitgezet), aanmaken en wijzigen (percentage of vast bedrag, periode, maximum, maximum per klant, minimum bestelbedrag, gelegenheden, indelingen, ontwerpen; een leeg codeveld maakt een willekeurige code zonder verwarrende tekens), en per code de bestellingen die hem gebruikten. Na het eerste gebruik zijn code, soort, waarde en bereik vergrendeld; uitzetten, periode en maximum kunnen nog. Een code verdwijnt nooit (alleen uitzetten).

## Niet gedaan

Geen stapelen, geen tegoeden, geen automatische acties, geen gratis bestellingen, niets op staging of productie.

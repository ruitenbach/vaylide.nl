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

## Btw

Besluit van de eigenaar (17 oktober 2026): de onderneming doet **niet** mee aan de kleineondernemersregeling (KOR). Er wordt 21% btw gerekend (`VIERLIEF_BTW_PERCENTAGE`, standaard 21) en alle consumentenprijzen zijn inclusief btw. De verkoopprijzen zijn niet gewijzigd.

Hoe de code ermee omgaat (nagelopen):
- De korting is een negatieve regel op het bedrag inclusief btw. Het ordertotaal is de som van de regels, en dat bedrag gaat ongewijzigd naar Mollie (`orders/services.py::_check_discounted_order`, `orders/providers.py`).
- Het btw-deel wordt berekend over het werkelijk betaalde bedrag (`kortingen/services.py::vat_part_cents`, halve centen naar boven). Voorbeeld: € 59,95 met 30% korting is € 41,96 betaald, daarvan € 7,28 btw (zonder korting € 10,40).
- Alleen Beheer toont het btw-deel, en alleen bij een bestelling met korting. Er is geen factuurfunctie; bevestigingsmail en bon zijn geen factuur.
- Bestellingen van vóór de kortingen houden hun bedrag: `discount_cents` is 0 en `subtotal_cents` leeg, en de migraties passen geen bestaand bedrag aan.

Fiscale onzekerheden (voor de boekhouder, niet door de code te beantwoorden):
1. Is 21% juist voor een digitale uitnodiging die een consument online afneemt? Voor klanten in andere EU-landen gelden regels voor digitale diensten aan consumenten (btw van het land van de klant, met een drempel en het OSS-loket). Nu wordt altijd 21% gerekend.
2. Is "korting op het bedrag inclusief btw, btw-deel proportioneel" de juiste boeking?
3. Facturen: welke gegevens moeten bij een bestelling met korting op de factuur of bon, en wie levert die aan klanten (zakelijke klanten vragen er vaak om)?
4. Afronding per bestelling op hele centen: akkoord?
5. Terugbetaling na een code: het betaalde bedrag wordt terugbetaald, niet de brutoprijs. Akkoord?

## Hoe een code gaat

1. Controle (`kortingen.services.check_code`): actief, begin- en einddatum (de einddatum geldt tot het einde van die dag), bereik (gelegenheid, indeling, ontwerp; als er meer soorten beperking zijn gekozen moeten ze allemaal kloppen), minimum bestelbedrag, maximum aantal keer, maximum per klant, ondergrens.
2. Reserveren: bij het aanmaken van de bestelling (`orders.services.start_checkout`), in dezelfde vergrendelde transactie, na een nieuwe controle. Twee klanten op de laatste plek: de tweede krijgt "niet meer beschikbaar".
3. Definitief: bij de eerste bevestigde betaling (`apply_remote_status`).
4. Vrijgegeven: bij een mislukte of verlopen betaling, een vervangende bestelling voor dezelfde kaart, of annuleren in Beheer. Een geannuleerde (afgebroken) betaling houdt de reservering vast tot die na 120 minuten vervalt. Bij "Opnieuw betalen" wordt de reservering verlengd of opnieuw gemaakt; lukt dat niet meer, dan volgt geen betaling en een duidelijke melding.
5. Vlak voor Mollie (`create_payment`) controleert de code dat de som van de regels, het ordertotaal en het betaalbedrag gelijk zijn, positief, en niet onder het minimum. Daarnaast vergelijkt `apply_remote_status` het bedrag bij Mollie met de betaling (bestond al).

Bekende rand: betaalt een klant ná het verlopen van de reservering en is de plek intussen aan een ander gegeven, dan blijft de korting staan (de klant betaalde dat bedrag) en staat bij het gebruik en in het betalingslogboek "maximum aantal keer overschreden". Dat kan alleen als iemand meer dan 2 uur na het starten van de betaling afrekent.

**Besluit van de eigenaar (17 oktober 2026): dit gedrag blijft zoals het is.** Een late, alsnog geslaagde betaling kan het ingestelde maximum aantal keer (`max_redemptions`) of het maximum per klant dus **overschrijden**. De klant die betaald heeft houdt zijn korting en krijgt zijn kaart; er wordt niets teruggedraaid en niet geweigerd. De overschrijding staat zichtbaar in het gebruik van de code (notitie "Betaling na verlopen reservering; maximum aantal keer overschreden.") en in het betalingslogboek ("Let op: …"). Praktisch gevolg: een code met bijvoorbeeld 10 plekken kan in zeldzame gevallen 11 keer gebruikt zijn. Het gedrag veranderen (de late betaling toch weigeren of terugbetalen) kan alleen met een afzonderlijk akkoord van de eigenaar. Getest in `test_late_betaling_na_verlopen_reservering_blijft_staan_maar_wordt_vastgelegd`.

## Klantreis

Zie de bestelstap: onder het overzicht staat een bescheiden tekstregel "Heb je een kortingscode?". Aantikken opent een smal veld met "Toepassen" (een gewone `<details>`, werkt zonder JavaScript, geen extra pagina of stap). Na toepassen staan in dezelfde tabel de oorspronkelijke prijs, een regel "Kortingscode ZOMER10 − € 3,50" met een tekstlink "Verwijderen", en het nieuwe totaal; de knop zegt "Bestellen en betalen € …". Fouten staan bij het veld: onbekend, verlopen (met datum), nog niet geldig (met datum), niet meer beschikbaar, niet voor deze gelegenheid of dit ontwerp, al gebruikt, ondergrens. Een code die niet is toegepast maar wel is ingetikt, wordt bij "Bestellen en betalen" eerst toegepast en laat het nieuwe bedrag zien (er wordt niet meteen betaald). Vervalt een toegepaste code vóór het betalen, dan wordt er niet stilletjes tegen de volle prijs afgerekend. Een link met `?code=…` vult alleen het veld in. Pogingen: 10 per kwartier per bezoeker.

## Beheer

Beheer → Kortingscodes (alleen met de schakelaar aan): overzicht met status (gepland, actief, verlopen, opgebruikt, uitgezet), aanmaken en wijzigen (percentage of vast bedrag, periode, maximum, maximum per klant, minimum bestelbedrag, gelegenheden, indelingen, ontwerpen; een leeg codeveld maakt een willekeurige code zonder verwarrende tekens), en per code de bestellingen die hem gebruikten. Na het eerste gebruik zijn code, soort, waarde en bereik vergrendeld; uitzetten, periode en maximum kunnen nog. Een code verdwijnt nooit (alleen uitzetten).

In het formulier heeft elke lijst met selectievakjes (gelegenheden, indelingen, ontwerpen) de knoppen "Alles aanvinken" en "Alles uitvinken". Ze werken alleen binnen hun eigen lijst, verschijnen alleen met JavaScript en veranderen de filterlogica niet.

## Niet gedaan

Geen stapelen, geen tegoeden, geen automatische acties, geen gratis bestellingen, niets op staging of productie.

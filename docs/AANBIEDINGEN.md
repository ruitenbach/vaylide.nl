# Automatische aanbiedingen en centraal kortingsbeheer

Stand: 17 oktober 2026. Gebouwd op de lokale branch `claude/kortingen-aanbiedingen` (bovenop de kortingscodes, `f1161ac`), **niet gepusht, niet op staging, niet op productie**. Beide schakelaars staan standaard uit.

## In het kort

Beheer → Kortingen heeft twee tabbladen: **Kortingscodes** (zie `docs/KORTINGSCODES.md`) en **Automatische aanbiedingen**. Een aanbieding geldt zonder code voor één of meer ontwerpen of de hele collectie, met een verplichte einddatum. Eén rekenpad: de aanbieding is een negatieve regel in de offerte (`orders/pricing.py` → `kortingen/aanbiedingen.py`), net als een kortingscode. Collectiekaart, ontwerppagina, Studio, bon, bestelling, betaling, Mollie-bedrag, status en mail lezen daardoor dezelfde actieprijs. De vaste Basis-, Luxe- en Special-prijzen (`catalog/prijzen.py`) veranderen niet.

## Aanzetten (twee onafhankelijke schakelaars)

| Instelling | Standaard | Betekenis |
|---|---|---|
| `VIERLIEF_KORTINGSCODES` | uit | Kortingscodes (bestond al). |
| `VIERLIEF_AANBIEDINGEN` | uit | Automatische aanbiedingen. Werkt alleen met `VIERLIEF_PRICING_V2`. |
| `VIERLIEF_AANBIEDING_REFERENTIE_DAGEN` | 30 | Lengte van de referentieperiode voor een doorgestreepte prijs. |

Uit betekent: geen aanbieding in offerte, kaart of pagina, geen Beheeronderdeel (404). De migraties (`kortingen.0002`, `orders.0005`) zijn alleen toevoegingen. Bestaande bestellingen blijven ongewijzigd.

## Besluiten van de eigenaar (17 oktober 2026)

- Code en aanbieding stapelen niet: alleen de voordeligste geldt (bij gelijk de aanbieding, zodat er geen code verbruikt wordt). De klant krijgt in de bestelstap te horen welke wordt gebruikt. Aanbiedingen onderling stapelen ook niet. Een code die niet gebruikt wordt, wordt niet gereserveerd.
- De einddatum is verplicht (ook in de database). Een percentage is 1 tot en met 90; het te betalen bedrag blijft minimaal € 1,00.
- Einddatum: niet op de collectiekaart, subtiel ("Aanbieding t/m 29 oktober") op de ontwerppagina.
- Geen banners of SALE-elementen: alleen een klein prijskaartje-icoon met "Aanbieding" en de actieprijs.
- Verlopen of gestarte aanbieding tijdens het bestellen: de bon bevat een verborgen veld `verwacht` met het getoonde bedrag. Wijkt het bedrag bij "Bestellen en betalen" af, dan volgt een melding met oud en nieuw bedrag, er wordt niets besteld of betaald, en de klant bevestigt het nieuwe bedrag met een nieuwe klik (`PriceChanged` in `orders/services.py`). Een bestelling die al is aangemaakt behoudt zijn bedrag.

## Doorgestreepte referentieprijs

Een doorgestreepte prijs staat er alleen als de prijshistorie (`PriceStand`, gevuld bij `migrate` en met `manage.py sync_prijshistorie`) aantoont dat de referentie klopt:

- referentie = de laagste prijs in de 30 dagen vóór de start van de aanbieding, óók als dat een eerdere aanbieding was (zo kan een tweede aanbieding geen schijnkorting tonen);
- de historie moet die hele periode dekken en de huidige stand moet de huidige prijs zijn;
- de referentie moet hoger zijn dan de actieprijs;
- per aanbieding is de doorgestreepte prijs uit te zetten; Beheer toont bij de aanbieding bij hoeveel kaarten hij mag en waarom niet bij de rest.

Bij twijfel (geen of te korte historie, achterlopende stand) staat er alleen de actieprijs. Er is **geen** automatische wachttijd van 30 dagen voor een nieuw ontwerp: een nieuw ontwerp mag de aanbieding en de actieprijs direct krijgen, alleen zonder doorgestreepte prijs zolang er geen dekkende historie is. Ook de uitzonderingen (product korter dan 30 dagen op de markt, progressieve verlagingen) zijn bewust **niet** ingebouwd, omdat de definitieve tekst en de toepasbaarheid op digitale kaarten niet zijn bevestigd.

Let op bij livegang: de historie begint pas op de dag van de eerste `migrate` met deze code. Wil de eigenaar eerder bewijsbaar geldende prijzen vastleggen, dan kan dat alleen met bewijs: `sync_prijshistorie --sinds JJJJ-MM-DD`.

Bronnen van het onderzoek: ACM (https://www.acm.nl/nl/publicaties/acm-wil-eerlijke-kortingen-om-consumenten-te-beschermen-tegen-misleiding), ACM-leidraad prijsweergave (https://www.technieknederland.nl/media/porpendu/acm-leidraad-prijsweergave-en-vergelijkingen.pdf), boetebesluit JYSK (https://acm.nl/system/files/documents/boetebesluit-jysk.pdf); regels: Besluit prijsaanduiding producten art. 5a, Prijzenwet, Omnibusrichtlijn 2019/2161.

## Voorwaarden voor productie (open)

1. **Juridische verificatie** van de referentieregels: gelden ze voor digitale diensten zoals deze kaarten, welke uitzonderingen zijn toepasbaar, en volstaat de gekozen berekening.
2. **Btw-verwerking** (zie `docs/KORTINGSCODES.md`): korting op het bedrag incl. btw, btw-deel proportioneel; boekhouder bevestigt.
3. Schakelaars alleen aan met uitdrukkelijk akkoord van de eigenaar.

## Waar zit wat

`kortingen/models.py` (`Offer`, `PriceStand`), `kortingen/aanbiedingen.py` (bereik, beste aanbieding, referentie, offerte, weergave), `kortingen/services.py` (`toepassen`: voordeligste van code en aanbieding), `kortingen/forms.py` (`OfferForm`), Beheer `beheer/views.py` (`offers`, `offer_edit`, `offer_stop`), kaart `templates/partials/design_card.html`, ontwerppagina `core/templates/core/design_detail.html`, Studio `studio/views.py` (`_prijzen_per_ontwerp`, `_korting_stap`, `_verwacht`). Tests: `tests/test_aanbiedingen.py`. `manage.py controleer_prijzen` controleert ook actieprijs = offerte.

## Voor een veilige stagingtest

1. Eerst `bbaa615` (of de actuele opvolger) in de branch mergen op een testbranch en de volledige suite draaien (de proefmerge was conflictvrij).
2. Een echte Mollie-**testsleutel** (`test_...`) via de omgeving en `e2e/mollie_kortingen.py` draaien (code, aanbieding, beide); dit is nog niet gedaan.
3. De volledige suite en `tests/test_kortingen_postgres.py` op de PostgreSQL-database van staging (een eigen testdatabase, nooit productie).
4. `migrate` draaien en `manage.py sync_prijshistorie` controleren; schakelaars alleen op staging aanzetten.
5. De juridische vragen (zie hierboven) beantwoorden vóór activering op productie.

### Terugzetten van de code na de kortingsmigraties

De kortingsmigraties (`kortingen` 0001 en 0002, `orders` 0004 tot en met 0006) voegen alleen toe. Code terugzetten verwijdert niets uit de database; de database terugzetten is een afzonderlijke handeling.

- **Code terug** (zonder de migraties terug te draaien): oudere code kent de nieuwe kolommen niet. De verplichte kolommen van `orders_order` (`discount_cents`, `discount_code_text`, `discount_offer_text`) hebben daarom een standaardwaarde in de database zelf (migratie `orders/0006`, `db_default`). Zonder die waarde gaf elke nieuwe bestelling met oudere code een NOT NULL-fout. De overige nieuwe kolommen mogen leeg zijn en de nieuwe tabellen schrijft oudere code niet.
- **Database terug:** `manage.py migrate orders 0003` en `manage.py migrate kortingen zero` (verwijdert de nieuwe kolommen en tabellen met de gegevens erin), of een herstel naar het tijdstip van vóór de uitrol.
- Bewaakt door `tests/test_kortingen_postgres.py` (`TerugdraaiVeilig`).

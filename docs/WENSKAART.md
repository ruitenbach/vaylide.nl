# Wenskaart (6 oktober 2026)

Naast de uitnodiging kiest de klant aan het begin voor een **wenskaart**: alleen een persoonlijke groet, zonder evenement.
Alles hieronder staat in de code; de pakketten en opties van de uitnodigingen zijn niet aangeraakt.

## Prijzen (incl. btw)

| Kaart | Prijs |
|---|---|
| Wenskaart | € 14,95 |
| Wenskaart in een special-ontwerp (`Template.special`) | € 24,95 |

- De prijzen staan in `catalog/wenskaart.py` (`PRIJS_CENTS`, `PRIJS_SPECIAL_CENTS`), niet in Beheer → Pakketten. Eén vaste prijs: geen pakketten, upgrade, extra opties of meerprijs voor een special.
- Online periode: `MAANDEN_ONLINE = 6` (zoals Essentieel; aanname, aan te passen op één plek).
- Overal "incl. btw": startpagina, ontwerppagina, prijzenpagina, voorbeeld, bestellen (`orders/pricing.py::build_wenskaart_quote`, bestelcode `wenskaart` of `wenskaart-special`).

## Wanneer is een kaart een wenskaart

Alleen op de **uitdrukkelijke, opgeslagen keuze** van de klant (`content["soort"] == "wenskaart"`), bij elke gelegenheid. `invitations.content.card_kind()` en `catalog.wenskaart.is_wenskaart()` volgen dezelfde regel en leiden niets af: geen datum, geen locatie, de gelegenheid Kerst of lege eventgegevens maken van een kaart nooit een wenskaart.
Elke bestaande kaart zonder `soort` (ook een oude kerstkaart zonder datum) is volledig een uitnodiging: weergave, formulieren (datum, tijd en locatie verplicht), aanmelden, prijs en mails.
Na betaling ligt de keuze vast (de radioknoppen in Gegevens zijn dan uitgeschakeld en worden niet verwerkt).

## De flow

1. **Keuze aan het begin** (`/maken/`): "Wat wil je maken? Uitnodiging | Wenskaart", met de prijzen. Ook via de ontwerppagina (`?soort=wenskaart`, de schakelaar staat nu bij elk ontwerp) en de prijzenpagina. Bij een wenskaart verdwijnt de pakketkeuze; bij elk ontwerp staat de prijs.
2. **Stappen**: Ontwerp → Gegevens (naam, persoonlijke boodschap) → Afsluiting → Foto → Stijl → Voorbeeld → Bestellen. Overgeslagen: Envelop & zegel en Aanmelden (`studio/steps.py::WENSKAART_SKIP`).
3. **Snel afronden**: op elke stap een knop naast Volgende die bewaart en direct naar het voorbeeld gaat; alleen de naam is verplicht.
4. **Voorbeeld → Betalen → Delen**: de knop toont de prijs; Bestellen toont één kaart met de vaste prijs; na de betaling de gewone onthulling met link en QR-code.

## Wat een wenskaart niet toont

Aanmelden (en dus geen gastenlijst), programma, locatie en route, dresscode, praktische informatie, contactpersoon, verhaal, fotogalerij en muziek. Buiten Kerst ook geen afteller.
De kop en regel per gelegenheid ("Gefeliciteerd · met jullie bruiloft", …) staan in `catalog/wenskaart.py::KOP`; de teksten zijn een voorstel van de bouwer. Aanmelden op een gepubliceerde wenskaart wordt geweigerd (409). Mijn VAYLIDE verbergt het aanmeldingenblok en de bijbehorende stappen.

## Controle

`tests/test_wenskaart_regressie.py` (geen automatische detectie, oude kerstkaart, nieuwe kerst-wenskaart, betaalde uitnodiging, betaalde wenskaart blijft vast) en `tests/test_wenskaart_prijs.py` (prijzen, special, bestelling, bestaande uitnodiging blijft uitnodiging, studio-flow, Snel afronden, weergave van elk ontwerp als wenskaart, portal, mails, pagina's).

# Controle: kan VAYLIDE een bestelling volledig automatisch verwerken? (30 september 2026)

Gebaseerd op de code (branch `claude/privacyverklaring`), de configuratie (`render.yaml`, `config/settings.py`), de
uitgevoerde tests en wat van buitenaf op de testsite te zien is. **Niets gepusht of gedeployd, geen instellingen
gewijzigd, geen betaling gedaan.**

## Welke omgeving is wat

| Omgeving | Stand | Hoe vastgesteld |
|---|---|---|
| Lokale code | Branch `claude/privacyverklaring`: 3 commits vóór op de testsite (voorwaarden, privacy, aanmelden) | `git log` |
| Testsite op Render | Commit **`c24a888`** (voettekst met creditcard) | **Afgeleid.** De statische bestanden zijn zonder wachtwoord te openen. `creditcard.webp` uit `c24a888` bestaat (2076 bytes), en `vierlief.css` en `app.css` zijn gelijk aan `c24a888` maar verschillen van alle latere lokale commits. Het Render-dashboard heb ik niet gezien. |
| Testmodus en Mollie-testsleutel op Render | Test | **Afgeleid.** De eigenaar zag de testpagina van Mollie. In testmodus weigert de site een live-sleutel. De Mollie-webhook antwoordt (400 zonder id). |
| Lokale tests | Betaling, e-mail en AI nagebootst (`PAYMENT_PROVIDER=test`, outbox, geen AI-sleutel) | `.env` (alleen namen gecontroleerd, geen waarden) |
| Echte Mollie-testbetaling | Eerder door de eigenaar op Render gedaan, op een oudere versie: 1× geslaagd (kaart online), 1× mislukt | Mededeling eigenaar. **Niet vastgesteld** of die via de webhook of via de terugkeer is verwerkt. |
| Echte e-mailbezorging | **Nergens.** Render staat in testmodus en bewaart e-mails alleen (outbox). Er is geen SMTP-aanbieder. | Code en `render.yaml`; op Render **niet geverifieerd** |

## Stappen van de klantreis

| Onderdeel | Automatisch? | Waar getest? | Resultaat | Nog nodig |
|---|---|---|---|---|
| 1. Ontwerp en pakket kiezen | Ja | Lokaal: unit en klantreis (Chromium, 390 en 1366 px) | Werkt | — |
| 2. Namen, datum, locatie, foto's en opties opslaan | Ja | Lokaal: unit en klantreis | Werkt | — |
| 3. Voorvertoning toont de opgeslagen keuzes | Ja | Lokaal: unit en klantreis | Werkt | — |
| 4. Betalen via Mollie | Ja, op de betaalpagina van Mollie | Lokaal: Mollie-API nagebootst. Render: echte testbetaling door de eigenaar (oudere versie). | Werkt in testmodus. **Live-sleutel nooit gebruikt.** | Live-sleutel en live-modus, en één echte testbetaling op de nieuwe versie |
| 5. Server controleert bij Mollie: status, bedrag, valuta en bestelling | Ja. Bij een melding haalt de server de status zelf op bij Mollie. Een afwijkend bedrag wordt niet gepubliceerd en gaat naar de eigenaar. | Lokaal: unit (nep-melding, afwijkend bedrag) | Werkt | — |
| 6. Alleen na een bevestigde betaling samenstellen en publiceren | Ja. De vastgezette versie van het ontwerp wordt gepubliceerd; de bedankpagina publiceert niets. | Lokaal: unit en klantreis | Werkt | — |
| 7. Link en QR-code | Ja | Lokaal: unit en klantreis (QR downloaden) | Werkt | — |
| 8a. Kaart in Mijn VAYLIDE | Ja | Lokaal: klantreis | Werkt | — |
| 8b. E-mails aan de koper (bevestiging met voorwaarden, en "staat online" met link naar Mijn VAYLIDE en de QR-code als bijlage) | Ja, als taken | Lokaal: unit met nagebootste SMTP (locmem); op Render alleen outbox | Inhoud klopt. **Nooit echt bezorgd.** | SMTP kiezen, SPF/DKIM/DMARC, en een echte ontvangsttest |
| 9. Gasten openen de kaart en melden zich aan | Ja | Lokaal: unit en klantreis (aanmelden en afmelden) | Werkt | — |
| 10. Aanmeldingen zien en exporteren (CSV) | Ja | Lokaal: unit en klantreis | Werkt | — |
| 11. Looptijd: Essentieel 6, Compleet 12, "Langer online" +12 maanden, vanaf de betaling bij Mollie | Ja. Eén keer vastgelegd; een late of herhaalde melding verschuift niets. | Lokaal: unit (ook een melding die 5 uur te laat komt, en herhaling een dag later) | Werkt | De maanden staan per pakket in de database en zijn instelbaar. Controleer ze in het beheer op Render. |
| 12. Na afloop | Ja. De kaart is direct na de einddatum niet meer bereikbaar (elke keer gecontroleerd). 's Nachts: status Verlopen, en aanmeldingen 90 dagen later weg. | Lokaal: unit | Werkt lokaal | Nachtelijke taak op Render **niet geverifieerd** |

**Er hoeft bij een gewone bestelling nergens op een knop gedrukt te worden** (getest in `test_normal_order_needs_no_button`).
De hele keten is:
1. betaling;
2. melding (of de terugkeer van de klant);
3. publiceren;
4. de twee e-mails.

Alles draait direct in hetzelfde verzoek, zonder handeling in het beheer.

## Soorten bestellingen

| Soort | Wat VAYLIDE doet | Zelfstandig geleverd? |
|---|---|---|
| **Gewone kaart** | Vult de gegevens van de klant in een bestaand ontwerp in (template en inhoud). Er wordt geen nieuw ontwerp gemaakt en er komt geen AI aan te pas. | **Ja** |
| **Betaalde extra opties** (muziek, fotogalerij, verhaal, extra vragen, langer online) | Na betaling komen de onderdelen vrij op de uitnodiging; langer online telt maanden op | **Ja** |
| **Specials** (Balzaal) | Zelfde stroom als een gewone kaart, met eigen ontwerpbestanden. Nu dezelfde prijs als het pakket. | **Ja** |
| **AI-tekstvoorstellen** | Alleen op verzoek, gratis, en het voorstel komt pas op de kaart als de klant het overneemt. Met `ANTHROPIC_API_KEY` via Claude; zonder sleutel vaste voorbeeldteksten. | Geen bestelling. **Fout gevonden:** zonder sleutel staat er ook in live-modus "Voorbeeldtekst uit de testmodus". Zie de voorstellen. |
| **Eigen gezichten** (Gemini) | Staat uit en is verborgen (getest). Wordt niet aangeboden. | **Nee.** Niet leverbaar; niet aanzetten zonder DPIA. |
| **Maatwerk en extra wensen** | De klant krijgt alleen een ontvangstbevestiging. De eigenaar beoordeelt, maakt een voorstel met prijs, en de klant accepteert en betaalt. Daarna gaat de status automatisch naar "In uitvoering". **Het werk zelf is handwerk.** | **Nee, bewust menselijke beoordeling** |

## Fouten en herstel

| Situatie | Wat er automatisch gebeurt | Getest |
|---|---|---|
| Afgebroken, mislukte of verlopen betaling | Niet gepubliceerd; het ontwerp blijft bewaard; opnieuw betalen kan | Unit, klantreis |
| Open of "pending" betaling | Niet gepubliceerd; wacht op Mollie | Unit (nieuw) |
| Dubbele webhook | Genegeerd; geen tweede publicatie of e-mail | Unit |
| Vertraagde webhook (klant sloot het venster) | Wordt alsnog gepubliceerd; de einddatum telt vanaf de betaling | Unit (nieuw) |
| Klant keert terug vóór de webhook | De server vraagt de status zelf op bij Mollie | Unit (nieuw) |
| Onderbreking tussen betaling en publicatie | Taak blijft staan; de geplande taak pakt hem op. Na 15 minuten zichtbaar bij "vastgelopen" in het beheer. | Unit (nieuw) |
| Publiceren mislukt | Automatisch opnieuw: na 1 min, 5 min, 15 min, 1 uur, 3 uur en 12 uur (6 pogingen). Daarna "aandacht nodig" en een melding aan de eigenaar. | Unit |
| E-mail mislukt | Publicatie gaat door; de e-mail wordt later opnieuw geprobeerd | Unit |
| Mollie tijdelijk onbereikbaar bij de melding | De site antwoordt 503. Volgens Mollie probeert Mollie het 10 keer opnieuw, tot 26 uur lang. | Unit |
| Oude betaling na een nieuwe bestelling toch betaald | Als de nieuwe ook betaald wordt: "dubbele betaling", naar de eigenaar | Unit |
| Vastgelopen taak opnieuw uitvoeren | Geen tweede bestelling, publicatie of e-mail, en geen verschoven einddatum | Unit (nieuw) |

**Dubbele e-mails zijn mogelijk.** Een e-mail wordt "minstens één keer" verstuurd, niet gegarandeerd precies één keer.
Mislukt het vastleggen nadat de mailserver hem al had aangenomen (of valt de server precies daartussen uit), dan
stuurt de herhaling hem nog een keer. Dit is aangetoond in `test_email_is_at_least_once_not_exactly_once`.

## Gevonden fouten en risico's, met voorstel

1. **Geen periodieke controle van open betalingen.** Komt de webhook 26 uur lang niet aan en keert de klant niet terug,
   dan blijft een betaalde bestelling op "wacht op betaling" staan. Ze staat dan niet bij "vastgelopen" en er gaat geen
   melding uit.
   - *Voorstel:* laat de geplande taak open betalingen van 10 minuten tot 48 uur oud bij Mollie nacontroleren, en toon
     "betaling langer dan 1 uur open" in het beheer.
2. **Zware verwerking binnen de webhook.** Publiceren, de QR-code en twee e-mails (elk met een SMTP-time-out van 20 s)
   gebeuren in het webhookverzoek. Mollie wacht maar 15 seconden. Bij een trage mailserver ziet Mollie een fout en
   herhaalt de melding. Dat is onschadelijk door de unieke sleutels, maar onnodig.
   - *Voorstel:* in de webhook alleen de betaling vastleggen en de verwerking direct daarna of via een worker laten
     draaien.
3. **AI-teksthulp zonder sleutel in live-modus** toont "Voorbeeldtekst uit de testmodus".
   - *Voorstel:* de knop in live-modus verbergen zonder sleutel, of de tekst aanpassen naar "voorbeeldtekst".
4. **Oude, onbetaalde bestelling die later toch betaald wordt:** die publiceert de versie van dat moment. Latere
   wijzigingen van de klant zijn dan niet mee gepubliceerd.
   - *Voorstel:* bij een betaalde vervangen bestelling de nieuwste versie publiceren, of de eigenaar laten beslissen.
5. **Handwerk dat blijft:**
   - terugbetalen (dubbele betaling, herroeping, afwijkend bedrag), in het Mollie-dashboard;
   - maatwerk uitvoeren.

## Render: niet geverifieerd, met één controle per punt

| Wat | Status | Controle voor de eigenaar |
|---|---|---|
| Welke commit draait | Afgeleid: `c24a888` | Render → dienst `vaylide` → Events: de laatste "Deploy live" moet `c24a888` noemen |
| Geplande taak (herhalingen, 's nachts opruimen, back-ups, status Verlopen) | **Niet geverifieerd** | Render → `vaylide-taken` → Logs: elke 15 minuten een regel die begint met `taken:` |
| Achtergrondverwerking | Er is geen aparte worker: taken draaien direct in het verzoek, en herhalingen alleen via de geplande taak | Zie hierboven |
| Vastgelopen bestellingen in het beheer | Gebouwd en lokaal getest | Beheer → Verwerking |
| Melding aan de eigenaar | Alleen als e-mail. In testmodus wordt die alleen bewaard, niet verstuurd. **Er komt nu dus geen melding aan.** | Beheer → Verwerking → e-mails |
| SMTP actief | **Niet geverifieerd.** Volgens `render.yaml` en de testmodus: nee. | Render → `vaylide` → Environment: staat `VIERLIEF_EMAIL_MODE` of `SMTP_HOST` erin? |
| Webhook van Mollie komt aan | **Niet geverifieerd** | Beheer → Bestellingen → de geslaagde testbestelling → de betaalmeldingen: staat er een regel met bron "webhook"? |

## Blokkades vóór de eerste betalende klant

1. **E-mail:**
   - een SMTP-aanbieder kiezen en instellen, met SPF, DKIM en DMARC;
   - een echte ontvangsttest van de bevestiging en de "staat online"-mail.
   - Zonder SMTP start de live-modus niet eens.
2. **Live-modus:** de live Mollie-sleutel, een https-adres, de juridische naam en het vestigingsadres, en de
   privacybesluiten. De site weigert live te starten zolang die ontbreken.
3. **De lokale branches** (voorwaarden, privacy, aanmelden) pushen en deployen, na akkoord van de eigenaar.
4. **Nachtelijke taak op Render** bevestigen: herhalingen, het einde van de looptijd, bewaartermijnen, back-ups.
5. **Eén echte Mollie-testbetaling op de gedeployde nieuwe versie**, met een melding met bron "webhook".
6. **Keuze over de AI-teksthulp** in live-modus (punt 3 hierboven).
7. **Aanbevolen, niet blokkerend:** open betalingen nacontroleren (punt 1) en een lichtere webhook (punt 2).

## Bronnen

- [Mollie: Webhooks](https://docs.mollie.com/reference/webhooks): 10 pogingen, tot 26 uur; alleen 200 OK telt; time-out
  van 15 seconden.

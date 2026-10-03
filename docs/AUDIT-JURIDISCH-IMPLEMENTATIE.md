# Juridische implementatie-audit (3 oktober 2026)

Alleen onderzoek. Er zijn geen teksten, voorwaarden, mails of functionaliteit gewijzigd. `docs/CONCEPT-ARTIKEL-9-10.md` blijft uitsluitend concept en
`core/templates/core/voorwaarden/2026-09-29.html` is niet aangepast. Dit is geen juridisch oordeel.

## 1. Herroepingsfunctie

**Wat er is**
- `/herroepen/` (`orders/views.py`, `withdraw`), zonder account bruikbaar, met de teksten "Hier de overeenkomst ontbinden" en "Ontbinding bevestigen".
- Identificatie: bestelnummer of een omschrijving van product of dienst (een van beide verplicht), naam en e-mailadres; besteldatum en toelichting zijn optioneel. Een ingelogde klant krijgt de velden vooraf ingevuld (via `?bestelling=`).
- Direct na indienen: bevestigingspagina met datum, tijd en ingevulde gegevens, en een ontvangstbevestiging per e-mail (`herroeping_ontvangen.txt`). De eigenaar krijgt een melding en er is een lijst in het beheer (Herroepingen).
- Geen eindtijd: de functie wordt niet uitgeschakeld na de bedenktijd.
- Bereikbaar via: footer van de hoofdsite, contactpagina, bevestigingsmail, voorwaarden (artikel 10) en het besteloverzicht na betaling.
- Bescherming: honeypot, formulier-tijdstempel (minimaal 2 seconden), 10 verzoeken per uur per IP.

**Wat ontbreekt of afwijkt**
- Geen link in de studio (stappen en Bestellen) en niet in Mijn VAYLIDE (portal).
- Geen keuze of de klant de digitale kaart, de online dienst of beide herroept (alleen vrije tekst "product of dienst").
- Afhandelen en terugbetalen is handwerk; er wordt niets automatisch offline gehaald.
- De anti-misbruikcontrole kan een snelle klant of een gedeeld IP-adres onterecht afwijzen.
- Ingangsdatum: `docs/VOORWAARDEN.md` noemt 19 juni 2026; de opdrachtgever noemt 25 juni 2026. Niet geverifieerd; de jurist moet dit bevestigen.

## 2. Wat de klant krijgt (feiten)

Beide pakketten
- Eén gepersonaliseerde uitnodiging (ontwerp, kleur, envelop en zegel, tekst, foto, afteller, programma, locatie), met aanmelden (RSVP), gastenlijst met CSV-export, delen, eigen link, QR-code en agenda-knop.
- Na betaling wordt één versie gepubliceerd op `/u/<code>/`; daarna volgt een mail met link en QR-code.
- Wijzigingen na aankoop: publiceren op dezelfde link zolang de uitnodiging online staat (`studio:publish`, vereist een betaalde bestelling).

| | Essentieel (€ 39) | Compleet (€ 69) |
|---|---|---|
| Online beschikbaar | 6 maanden | 12 maanden |
| Persoonlijk zegel | ja | ja |
| Verhaal, fotogalerij (12), muziek, extra vragen | niet inbegrepen | inbegrepen |

Extra's: "Langer online" (+12 maanden) € 12; muziek, galerij, verhaal en extra vragen zijn los bij te boeken.

Bewaren en bekijken
- Te downloaden door de klant: QR-code (PNG of SVG), gastenlijst (CSV). Gasten kunnen een agenda-bestand (.ics) downloaden.
- Niet te downloaden: de kaart zelf (geen pdf, afbeelding of bestand) en de eigen foto's en teksten. De kaart wordt alleen bekeken via de VAYLIDE-servers.
- Na de einddatum is de kaart niet meer bereikbaar (status "Verlopen").

Niet nagegaan: meldingen aan de klant bij nieuwe aanmeldingen.

## 3. Prijsverdeling

- Technisch bestaat alleen een pakketprijs per pakket plus losse opties; er is geen apart bedrag voor "digitale kaart".
- Wel: "Langer online" kost € 12 voor 12 maanden, en de pakketprijs stijgt met zowel de duur als de functies.
- De digitale kaart is zonder de online beschikbaarheid voor de klant niet bruikbaar (geen eigen kopie), en kaart en online beschikbaarheid beginnen op één technisch moment: het publiceren na de bevestigde betaling.
- Gevolg: een zelfstandige, verdedigbare scheiding is niet vanzelfsprekend. Geen bedragen toegewezen; eerst de classificatie laten beoordelen.

## 4. Checkout (feiten)

- De exacte teksten van beide toestemmingen en beide tijdstippen worden opgeslagen bij het aanmaken van de bestelling, vóór de betaling.
- De kaart wordt pas gepubliceerd nadat de betaling is bevestigd (`orders/fulfilment.py`, alleen bij status betaald).
- Afdwingen gebeurt alleen in het formulier (`CheckoutForm`). `start_checkout` en de verwerking na betaling controleren niet of de toestemmingen zijn vastgelegd; een bestelling zonder toestemming kan dus ontstaan via een andere route (nu zo in tests en `e2e/fixtures.py`).
- Het VAYLIDE-team kan via het beheer een uitnodiging publiceren zonder betalingscontrole.
- De bevestigingsmail wordt in de wachtrij gezet vóór het publiceren; de publicatie wacht niet tot de mail daadwerkelijk is verstuurd.

## 5. Bevestigingsmail

Vastgelegd: de uiteindelijke versie moet ook het opgeslagen verzoek om de online dienst direct te starten bevestigen (`Order.service_consent_at` en `service_consent_text`). Voorstel in `docs/CONCEPT-ARTIKEL-9-10.md`. De mail is niet gewijzigd.

## 6. Onzeker voor de jurist

- Is de kaart (webpagina op onze server, zonder eigen kopie) digitale inhoud of onderdeel van één dienst?
- Is een scheiding tussen kaart en online beschikbaarheid in prijs en regels verdedigbaar?
- Moet de herroepingsfunctie ook vanuit de studio en Mijn VAYLIDE bereikbaar zijn, en per onderdeel (kaart of dienst) kunnen worden ingediend?
- Klopt de ingangsdatum van de verplichte herroepingsfunctie (19 of 25 juni 2026)?

## Mogelijke vervolgstappen (nog niet gedaan)

1. Link naar de herroepingsfunctie in de studio en Mijn VAYLIDE; keuze kaart, dienst of beide in het formulier.
2. Toestemmingen ook afdwingen in `start_checkout` en vóór publicatie.
3. Bevestigingsmail uitbreiden met het verzoek voor de online dienst, nadat artikel 9 en 10 zijn vastgesteld.

# Beslislijst privacy (1 oktober 2026)

## Stand na je besluit van 1 oktober 2026

Je nam de voorstellen over, met één aanpassing: **de noodzakelijke financiële administratie staat apart** van bijlagen en
correspondentie. Bestelling, bestelregels en betalingen blijven 7 jaar; wensen met hun berichten en bijlagen gaan na 12
maanden weg, ook als er een bestelling uit voortkwam (B4).

- **Verwerkt:** A1, A2 (teksten in de privacyverklaring), A4 en D2 (in `docs/VERWERKERSOVEREENKOMST.md`), B1 tot en met B6
  (nachtelijke opruimtaken in `core/privacy.py`, tests in `tests/test_bewaartermijnen.py`), C1 (Vimexx als standaard), C2
  en C4 (ongewijzigd).
- **B7 ook verwerkt:** 7 dagen (Hobby-abonnement bij Render, volgens render.com/docs/logging).
- **Nog open:** A3 (verwerkersvoorwaarden als bijlage bij het
  bestellen: pas inbouwen na de juridische toets), C3 (optioneel), D1 en D3.
- **Juridische toets** blijft aanbevolen voor A1, A2, A3, A4, B5 en D1.

De tabellen hieronder zijn het oorspronkelijke voorstel.

Alleen de vragen die nog open staan, met per vraag mijn voorstel en wat jij beslist. Al besloten en niet meer in deze lijst:
- **Aanmelden zonder gevoelige gegevens** (optie A, 30 september): alleen vaste, neutrale extra vragen. Optie B
  (dieet/allergie) staat geparkeerd.
- **Geen cookiebanner:** alleen functionele cookies en browseropslag.
- **AI-tekstvoorstellen en "eigen gezichten"** staan uit.

Vul in de kolom **Jouw besluit** in: **Ja** (voorstel overnemen), **Anders: …** of **Later**. Daarna verwerk ik alles in
één keer: de teksten in `core/privacyverklaring.py` en, waar nodig, opruimtaken in de code. Verplicht vóór livegang zijn
de punten met **(blokkeert live)**: zolang die open staan, weigert de site in live-modus te starten.

**Juridisch** in de laatste kolom betekent: laat dit beoordelen door een jurist voordat je het definitief maakt.

## A. Rollen en grondslagen

| # | Vraag | Mijn voorstel | Jouw besluit | Juridisch |
|---|---|---|---|---|
| A1 | **Rol bij gastgegevens** (aanmeldingen) **(blokkeert live)** | VAYLIDE is verwerker voor de organisator. Bij een privéfeest geldt de AVG vaak niet voor de organisator zelf, maar VAYLIDE houdt zich aan dezelfde verwerkersplichten. Voor eigen doelen (beveiliging, misbruik tegengaan) is VAYLIDE zelf verantwoordelijk. De tekst staat nu als "[Voorstel]" in onderdeel 4 van de privacyverklaring. | | **Ja**: verwerker of gezamenlijk verantwoordelijk? (VAYLIDE bepaalt de vaste vragen en de bewaartermijn) |
| A2 | **Grondslag voor gegevens van anderen op de kaart** (namen, foto's, contactpersoon) **(blokkeert live)** | VAYLIDE verwerkt de kaartinhoud als verwerker voor de klant. De klant zorgt dat hij de gegevens en foto's van anderen mag gebruiken (artikel 12 van de voorwaarden). | | **Ja** |
| A3 | **Verwerkersafspraken met organisatoren** | Een vaste bijlage "Verwerkersvoorwaarden" bij de algemene voorwaarden, voor alle klanten, geaccepteerd bij het bestellen. Voor zakelijke klanten op verzoek ook een ondertekende versie. Concept: `docs/VERWERKERSOVEREENKOMST.md`. | | **Ja**: mag dit via de algemene voorwaarden, ook voor consumenten? |
| A4 | **Meldtermijn datalek aan de organisator** (in de verwerkersvoorwaarden) | Zonder onredelijke vertraging, en uiterlijk binnen 48 uur nadat VAYLIDE het lek ontdekt | | **Ja** |

## B. Bewaartermijnen (alle zeven blokkeerden live)

Nu al automatisch, en dus geen besluit meer nodig:
- inlogcodes: na 2 dagen weg;
- ontwerpen zonder bevestigd e-mailadres: na 30 dagen;
- onbestelde ontwerpen: na 365 dagen;
- aanmeldingen: 90 dagen nadat de kaart offline ging;
- sessies en verlopen cache.

| # | Gegevens | Mijn voorstel | Jouw besluit | Juridisch |
|---|---|---|---|---|
| B1 | Gekochte kaarten, foto's en muziek na de looptijd | 90 dagen na het einde van de looptijd verwijderen (zelfde moment als de aanmeldingen). De bestelling zelf blijft voor de administratie. | | Nee |
| B2 | Accounts | Account zonder kaarten en zonder activiteit na 24 maanden anonimiseren, met 30 dagen vooraf een e-mail | | Nee |
| B3 | Contactberichten | 12 maanden na het laatste bericht | | Nee |
| B4 | Extra wensen (maatwerk) en bijlagen | 12 maanden na afronden als er niet besteld is; anders bewaren zoals bestelgegevens (7 jaar) | **Anders:** 12 maanden na afronden, altijd; alleen de bestel- en betaalgegevens blijven 7 jaar | Nee |
| B5 | Herroepingen | Bewaren zolang de bijbehorende bestelgegevens (7 jaar) | | **Ja**: kan korter? |
| B6 | Kopie van verstuurde e-mails (in Beheer) | 90 dagen | | Nee |
| B7 | Logbestanden bij Render | De termijn van Render overnemen. **Eerst nakijken:** Render → vaylide → Logs, welke bewaartermijn je abonnement heeft. Geef die termijn hier door. | | Nee |

Voor B1 tot en met B4 en B6 bouw ik na je besluit een nachtelijke opruimtaak, met tests. Er wordt niets verwijderd
zonder dat jij hebt besloten.

## C. Aanbieders

| # | Vraag | Mijn voorstel | Jouw besluit | Juridisch |
|---|---|---|---|---|
| C1 | **E-maildienst** **(blokkeert live)** | **Vimexx** is de actieve e-mailprovider (SMTP via mail.zxcs.nl). Zet in Render bij de dienst vaylide de variabele `VIERLIEF_EMAIL_AANBIEDER` op **`Vimexx B.V. (Nederland)`**. Controleer zelf de exacte bedrijfsnaam in je contract of op [de verwerkersovereenkomst van Vimexx](https://www.vimexx.nl/Verwerkersovereenkomst-Vimexx-14-05-2018.pdf). Volgens Vimexx hoort die overeenkomst automatisch bij je abonnement, en staan de servers in Ede en Dronten (Nederland). | | Nee (wel zelf even controleren) |
| C2 | Contactadres voor privacyvragen | Voorlopig **info@vantorstudio.nl** (staat zo op de site). Later eventueel een adres op vaylide.nl. | | Nee |
| C3 | Tweede back-uplocatie | Aanbevolen, niet verplicht. Een S3-opslag in de EU, met een bewaarregel van 30 dagen. Kies je dit, geef dan de naam van de aanbieder door. | | Nee |
| C4 | AI-tekstvoorstellen (Anthropic) bij de livegang | **Uit laten.** Dan is er geen doorgifte naar de VS en geen extra overeenkomst nodig. | | Alleen als je hem aan wilt |

## D. Werkwijze

| # | Vraag | Mijn voorstel | Jouw besluit | Juridisch |
|---|---|---|---|---|
| D1 | De 6 vaste aanmeldvragen (vervoer, parkeren, overnachten, geregeld vervoer, wanneer je erbij bent, liedje) | Zo goedkeuren | | **Ja**: kort laten meekijken of ze neutraal genoeg zijn |
| D2 | Reactietermijn bij onverwachte gevoelige gegevens in een antwoord | Binnen 5 werkdagen reageren; uitvoeren binnen de wettelijke maand | | Nee |
| D3 | Oude eigen aanmeldvragen op de testsite | Draai in de Render-shell `python manage.py rsvp_vragen_rapport`. Dat toont alleen aantallen; stuur me de uitkomst. Staat er 0, dan is dit afgerond. | | Nee |

## Wat je daarnaast nog nodig hebt voor de privacyverklaring

- **Juridische naam:** G.M.Bootsman Consultancy (eenmanszaak), volgens KvK, staat in Render (`VIERLIEF_JURIDISCHE_NAAM`).
  Het vestigingsadres (Händellaan 73, 8031 EG Zwolle) staat alleen op Contact & bedrijfsgegevens en in de voorwaarden.
- **Na je besluiten:** ik verwerk ze lokaal, laat alle tests draaien en stuur je de bijgewerkte verklaring. Publiceren
  gebeurt pas na je akkoord.

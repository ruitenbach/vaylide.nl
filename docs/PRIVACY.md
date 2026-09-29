# Privacyverklaring verwerken (concept 30 september 2026)

Werk op de **lokale branch `claude/privacyverklaring`**, gemaakt vanaf `claude/algemene-voorwaarden`. Niet gepusht en
niet gemerged. De branch `claude/kerstkaarten-website-design-51mn9k` gaat automatisch naar Render; publiceren gebeurt pas
na akkoord van de eigenaar.

De tekst is een **concept**. Hij is niet juridisch beoordeeld en de site zegt dat ook zo.

## Wat er gebouwd is

| Onderdeel | Waar |
|---|---|
| Volledige verklaring in 14 onderdelen, op basis van de concepttekst en de werkelijke inrichting | `core/templates/core/privacy.html` |
| Feiten op één plek: versie, aanbieders (alleen als de koppeling echt aan staat), cookies en browseropslag, open besluiten | `core/privacyverklaring.py` |
| **Controle vóór livegang:** in live-modus geeft `manage.py check` de fout `vaylide.E001` zolang er een besluit of aanbieder ontbreekt. Op Render stopt de start daardoor bij `migrate`. Een verklaring met invulvelden kan dus niet live. | `core/privacyverklaring.py` (`check_privacy_statement`), `core/apps.py` |
| Invulvelden, alleen zichtbaar op de afgeschermde testversie, met bovenaan een lijst van wat nog ontbreekt | filter `invul` |
| Nieuwe instellingen voor de namen van aanbieders die nog gekozen moeten worden | `config/settings.py`: `VIERLIEF_EMAIL_AANBIEDER`, `VIERLIEF_BACKUP_AANBIEDER`, `VIERLIEF_AI_AFSPRAKEN` |
| Opruimen van verlopen sessies en verlopen cachewaarden (onder andere de verkorte IP-codes), elke nacht | `core/privacy.py` (`apply_retention`) |
| Links naar de verklaring bij de formulieren | zie hieronder |
| Tabellen op een smal scherm als kaartjes | `static/css/vierlief.css` (`.table-stapel`) |
| Tests (18) | `tests/test_privacyverklaring.py` |

### Links naar de verklaring

Nergens is een verplicht vinkje "akkoord met de privacyverklaring" toegevoegd: de verklaring is informatie, geen
toestemming.

| Plek | Link |
|---|---|
| Footer (alle websitepagina's) en studio-footer | Bestond al |
| Inloggen en account maken | Nieuw |
| Bestellen (onder de vinkjes) | Nieuw. Het nieuwsbriefvinkje blijft apart en staat standaard uit. |
| Foto's uploaden | Nieuw, met uitleg over het lokaal uitlijnen op gezichten |
| Aanmeldformulier op elke uitnodiging | Nieuw, naar `#gasten`. De oude tekst "Alleen de organisator ziet je antwoord" is vervangen, omdat die niet helemaal klopte. |
| Extra wens aanvragen (met bijlagen) | Nieuw |
| Tekstvoorstel (AI-hulp) | Nieuw. Met een AI-sleutel staat er dat de gegevens naar Anthropic gaan, buiten de EU; zonder sleutel staat er dat er vaste teksten komen. |
| Contactformulier, herroepen | Bestond al |
| Eigen gezichten | Tekst bestond al; de functie staat uit |

Voorbeeldlinks (lokaal, testmodus):
- `http://127.0.0.1:8000/privacy/`
- `http://127.0.0.1:8000/privacy/#gasten`
- `http://127.0.0.1:8000/inloggen/`
- `http://127.0.0.1:8000/voorbeeld/aan-tafel/` (aanmeldformulier)

## Geverifieerde verwerkingen

Gecontroleerd in de code, zonder echte klantgegevens te bekijken.

| Verwerking | Gegevens | Bron in de code | Bewaren |
|---|---|---|---|
| Account en inloggen | E-mail, naam (optioneel), inlogcode als hash (20 min geldig, max. 5 pogingen), nieuwsbrief (ja/nee, tekst, tijdstip) | `accounts/models.py`, `accounts/newsletter.py` | Inlogcodes na 2 dagen weg. Accounts: **geen termijn**. |
| Ontwerpen en kaartinhoud | Namen, datum, tijd, locatie en adres, programma, teksten, contactpersoon (naam, telefoon, e-mail), foto's, muziek, logo | `invitations/models.py`, `studio/forms.py` | Ontwerpen zonder bevestigd e-mailadres na 30 dagen weg, onbestelde ontwerpen in een account na 365 dagen. Gekochte kaarten: **geen termijn**. |
| Gezichten detecteren | Middelpunt van de uitsnede (`focus_x`, `focus_y`) en het aantal gezichten. Geen gezichtskenmerken. | `invitations/focus.py` (YuNet, lokaal) | Zolang de foto bestaat |
| Bestelling en betaling | Bestelnummer, pakket, regels, bedragen, status, methode, Mollie-id, betaalmeldingen, versie van de voorwaarden, toestemming directe levering | `orders/models.py` | Blijft bewaard; bij het verwijderen van een account zonder naam, e-mail en kaarttitel |
| Naar Mollie | Alleen bedrag, omschrijving `VAYLIDE <bestelnummer>`, adressen voor terugkeer en melding, en metadata (bestelnummer en betaalcode). Geen e-mail of naam. | `orders/providers.py` (getest) | Bij Mollie |
| Aanmeldingen | Naam, komt ja/nee, aantal; als de organisator dat kiest ook antwoorden op vaste extra vragen en een toelichting (standaard uit). Oude uitnodigingen kunnen eigen vragen hebben. Versleutelde wijzigcode. | `invitations/models.py` (`GuestResponse`) | 90 dagen nadat de uitnodiging offline ging (instelbaar in beheer) |
| Contact | Naam, e-mail, onderwerp, bericht | `core/models.py` | **Geen termijn** |
| Herroeping | Naam, e-mail, bestelgegevens, toelichting, tijdstip | `orders/models.py` (`Withdrawal`) | **Geen termijn** |
| Extra wensen | Onderwerp, omschrijving, berichten, bijlagen, AI-samenvatting | `wishes/models.py` | **Geen termijn** (wel weg bij verwijderen account) |
| Uitgaande e-mail | Aan, onderwerp, tekst (ook van inlogmails met de code) | `processing/models.py` (`OutboundEmail`) | **Geen termijn** (wel weg bij verwijderen account) |
| Misbruik beperken | HMAC-hash van het IP-adres (24 tekens) in de cache | `core/utils.py` | Hoogstens een uur geldig, nu ook 's nachts opgeruimd |
| Sessies | Inlogstatus, ontwerp in de maak, live-voorbeeld | Django-sessies in de database | 30 dagen, nu ook 's nachts opgeruimd |
| Logbestanden | Gunicorn-toegangslog (tijd, pagina, verwijzer, browser; IP is waarschijnlijk dat van de proxy) en de logs van Render | `render.yaml`, `config/settings.py` | Bij Render, **termijn onbekend** |
| Foutmeldingen | Bij een serverfout een mail aan de eigenaar met de gegevens van het verzoek (Django verbergt cookies en geheimen; ingevulde formuliervelden kunnen erin staan) | `config/settings.py` | Alleen met SMTP; in de mailbox van de eigenaar |
| Back-ups | Database (zonder sessies) en alle uploads | `core/backup.py` | Elke nacht; de laatste 14 blijven bewaard. Versleutelde tweede locatie alleen als die is ingesteld. |

## Aanbieders

| Aanbieder | Status | Bewijs |
|---|---|---|
| **Render** (hosting, database, schijf) | **Actief.** Regio Frankfurt. | `render.yaml`; de testsite draait op `vaylide.onrender.com`. Render: verwerkersovereenkomst met EU-standaardcontractbepalingen en het Data Privacy Framework ([render.com/dpa](https://render.com/dpa)). |
| **Mollie** (betalingen) | **Actief in testmodus** (testsleutel). De live-sleutel is volgens de eigenaar klaar, maar niet ingesteld. | Webhook eerder gecontroleerd. Mollie ziet zichzelf als zelfstandig verantwoordelijke ([mollie.com/legal/privacy](https://www.mollie.com/legal/privacy)). |
| **E-maildienst (SMTP)** | **Niet actief.** Testmodus bewaart e-mails alleen (outbox). Er is nog geen aanbieder gekozen; info@vantorstudio.nl is alleen het contactadres. | `EMAIL_MODE`. Live start niet zonder SMTP. |
| **Tweede back-uplocatie (S3)** | **Alleen code.** Niet ingesteld (lokaal gecontroleerd; op Render niet te zien). | `core/offsite.py` |
| **Anthropic** (tekstvoorstellen, samenvatting van wensen) | **Alleen actief met `ANTHROPIC_API_KEY`.** Of die op Render staat, heb ik niet kunnen zien. Controleer het bij Beheer → een extra wens (daar staat "Zet ANTHROPIC_API_KEY…" als de sleutel ontbreekt). | `core/ai.py`. Volgens Anthropic: API-gegevens worden niet gebruikt voor training en binnen 30 dagen verwijderd ([privacy.claude.com](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)). De verklaring noemt dat **niet**, omdat de afspraken (verwerkersovereenkomst) niet zijn gecontroleerd. |
| **Google Gemini** (eigen gezichten) | **Uit** (`VIERLIEF_FACES_ENABLED` staat standaard uit en niet in `render.yaml`). Niet aangezet. | `gezichten/` |
| Foutmonitoring (zoals Sentry) | **Geen.** | `requirements.txt` |
| Lettertypen, video, analyse, social embeds | **Geen.** Lettertypen zijn eigen bestanden; de CSP staat alleen de eigen site toe. | Browsercontrole hieronder |
| Google Maps, Google Agenda, WhatsApp, Instagram | **Alleen links.** Er wordt niets geladen voordat iemand klikt. | Browsercontrole |

## Cookies en browseropslag (gecontroleerd in de browser)

Getest op de homepage, `/ontwerpen/`, `/contact/`, `/privacy/`, `/maken/` en de voorbeelduitnodiging `/voorbeeld/aan-tafel/`
(envelop geopend, beweging uit- en weer aangezet):

- **Verzoeken:** alleen naar de eigen site. Er is geen tracking, dus er valt niets vóór of na toestemming te blokkeren. Een
  cookiebanner is daarom niet nodig; de verklaring noemt wel alle cookies en opslag (de Autoriteit Persoonsgegevens (AP) zegt
  dat functionele cookies zonder toestemming mogen, als je bezoekers informeert).
- **`vierlief_csrf`:** 1 jaar, alleen op pagina's met een formulier.
- **`vierlief_sessie`:** 30 dagen, HttpOnly, pas bij inloggen of een ontwerp.
- **`vierlief_antwoord`:** 1 jaar, HttpOnly, alleen op het pad van die ene uitnodiging (getest).
- **localStorage `vierlief-beweging`:** alleen na een tik op "Beweging"; weg als je het weer aanzet.
- **sessionStorage `vierlief-open:<pad>`:** alleen op een echte uitnodiging (niet in de voorbeeldweergave).

## Aanmelden zonder gevoelige gegevens ("optie A", besloten op 30 september 2026)

| Wat | Hoe | Waar |
|---|---|---|
| **Standaard alleen naam, aanwezigheid en aantal personen** | Bij nieuwe uitnodigingen staat de toelichting uit en zijn er geen extra vragen | `invitations/content.py` (`default_content`) |
| **Aantal personen** | Blijft: nodig voor de catering en de totale capaciteit. Met "maximaal 1" verschijnt het veld niet. | Bestond al |
| **Toelichting** | Blijft beschikbaar, maar staat standaard uit. Nodig voor praktische meldingen ("ik kom later"). De vraagtekst ligt vast: een eigen tekst ("Heb je allergieën?") is niet meer mogelijk. | `studio/forms.py` (`RsvpSettingsForm`) |
| **Extra vragen alleen uit een vaste lijst** | 6 neutrale vragen: vervoer, parkeerplek, overnachten, geregeld vervoer, wanneer je erbij bent, en een liedje. Tekst en antwoordopties liggen vast (ook in u-vorm), dus een organisator kan via de antwoordopties niet alsnog iets gevoeligs vragen. | `invitations/vragen.py` |
| **Uitleg bij elk vrij tekstveld** | "Vermeld hier geen medische informatie, allergieën, religieuze gegevens of andere gevoelige persoonsgegevens." Bij de toelichting en bij de open vraag (liedje), gekoppeld met `aria-describedby`. Ook op de pagina waar een gast een antwoord wijzigt. | `invitations/templates/invitations/partials/rsvp.html`, `rsvp_edit.html` |
| **Controle op de server** | Het studioformulier bouwt vragen alleen uit de vaste lijst. Een zelfgemaakt verzoek met een eigen vraagtekst of toelichtingstekst wordt genegeerd (getest). Antwoorden buiten de opties, ontbrekende verplichte antwoorden en een te groot aantal personen worden geweigerd. Onbekende velden worden niet opgeslagen. | `studio/forms.py`, `invitations/rsvp.py` |
| **Voorbeelden aangepast** | Weg: "dieetwensen" en "allergieën" in de websitetekst, de omschrijving van de extra optie (met migratie `catalog/0005`; een door de eigenaar gewijzigde tekst blijft staan), de voorbeeldkaarten en de testgegevens | `core/content.py`, `catalog/seed.py`, `invitations/demo.py`, `e2e/fixtures.py` |
| **Geen kopieën in foutmeldingen** | Aanmeldformulieren zijn gemarkeerd met `sensitive_post_parameters`: ingevulde antwoorden komen niet in foutmails aan de eigenaar | `invitations/views.py` |
| **Geen AI of externe controle** | Er is geen inhoudsanalyse toegevoegd. De rapportopdracht hieronder leest alleen vraagteksten van organisatoren, niet de antwoorden van gasten. | — |

## Bestaande uitnodigingen

**Niets van klanten is veranderd of verwijderd.**
- Gepubliceerde uitnodigingen bewaren hun eigen kopie van de vragen en blijven werken zoals ze waren. Alleen de uitleg
  bij vrije tekstvelden verschijnt nu ook daar.
- Een concept met een oude eigen vraag of eigen toelichtingsvraag toont die in de studio onder "Eigen vragen van eerder".
  De organisator kan zo'n vraag alleen nog weghalen, niet wijzigen. Opslaan zonder weghalen laat alles staan (getest).

**Tellen zonder inhoud te tonen:** `python manage.py rsvp_vragen_rapport`
- Het resultaat bevat alleen aantallen: uitnodigingen met oude eigen vragen (concept en gepubliceerd), de soort vraag,
  verplichte vragen, en trefwoordcategorieën in de vraagtekst (gezondheid of dieet, geloof, toegankelijkheid).
- Ook geteld: eigen toelichtingsvragen, aanmeldingen met een antwoord op zo'n vraag en ingevulde toelichtingen.
- Er komen geen vraagteksten, namen, antwoorden of links in het resultaat (getest).

**Lokaal (testgegevens):**
- 70 uitnodigingen, 12 aanmeldingen;
- 0 oude eigen vragen en 0 eigen toelichtingsvragen;
- 0 aanmeldingen met een risicoantwoord of een ingevulde toelichting.

**Op de testsite (Render) niet gecontroleerd:** daar kan ik niet bij. **Open punt vóór livegang:** draai de opdracht daar
(Render → Shell). Staan er gepubliceerde uitnodigingen met een oude eigen vraag die de vaste lijst omzeilt, beslis dan
per geval met de organisator:
- weghalen en opnieuw publiceren;
- laten staan tot de uitnodiging verloopt;
- of de antwoorden eerder verwijderen.

Het rapport geeft alleen aan dat er een risico is. Het oordeel blijft handwerk.

## Rolverdeling per verwerking (beoordeling, geen juridisch oordeel)

Getoetst aan wie feitelijk het doel en de essentiële middelen bepaalt. Essentiële middelen zijn volgens de EDPB:
- welke gegevens;
- hoe lang;
- wie er toegang heeft;
- van wie.

| Verwerking | Wie bepaalt wat | Voorlopige rol VAYLIDE | Grondslag |
|---|---|---|---|
| Klantaccounts, bestellingen, betalingen, administratie | VAYLIDE: doel en middelen | **Verwerkingsverantwoordelijke** | Overeenkomst en wettelijke plicht |
| Kaartinhoud (namen, foto's, contactpersoon) | Organisator: wat erop staat en aan wie de link gaat. VAYLIDE: vorm en looptijd van de dienst. | **Verwerker** voor de organisator, mits geen eigen gebruik | Voor de organisator: meestal gerechtvaardigd belang, of de huishoudelijke uitzondering |
| Aanmeldingen en gastenlijst | Organisator: aanmelden aan of uit, welke vaste vragen, maximum, deadline, gebruik van de antwoorden. VAYLIDE: de vaste lijst en de standaardbewaartermijn. | **Verwerker**, met voorbehoud (zie hieronder) | Voor de organisator. De overeenkomst met de koper is **geen** grondslag voor gegevens van gasten. |
| Beveiliging en misbruikpreventie (IP-code, limieten, spamveld, logs) | VAYLIDE | **Verwerkingsverantwoordelijke** | Gerechtvaardigd belang |
| Back-ups en herstel | VAYLIDE, als beveiligingsmaatregel | Als verwerker (art. 32) voor kaart- en gastgegevens; verantwoordelijke voor eigen gegevens | — |
| Ondersteuning | Op verzoek van de organisator of de gast | Verwerker; zelf verantwoordelijk bij een beveiligingsincident | — |
| Eigen gebruik van gastgegevens | **Gebeurt niet:** geen marketing, analyse of AI op aanmeldingen | Zou VAYLIDE verantwoordelijke maken (art. 28 lid 10) en een eigen grondslag vergen | — |

**Particulier tegenover zakelijk:**
- Bij een **particuliere** organisator geldt vaak de huishoudelijke uitzondering (art. 2 lid 2 sub c AVG). De AVG geldt
  dan niet voor die organisator. Dat maakt VAYLIDE **niet automatisch verwerkingsverantwoordelijke**:
  - de EDPB schrijft dat de AVG blijft gelden voor de dienstverlener "acting as a processor and providing the means",
    en dat die dan alle verplichtingen uit art. 28 moet naleven (EDPB Opinion 7/2024, punt 19 en 20, en overweging 18);
  - niet elk gebruik door een particulier valt onder de uitzondering (zelfde punt 19), bijvoorbeeld een vereniging of een
    zzp'er.
- Bij een **zakelijke** organisator is die organisatie verwerkingsverantwoordelijke. VAYLIDE is verwerker, en er is een
  overeenkomst volgens art. 28 lid 3 nodig. De AP zegt ook: wie gegevens voor eigen doelen of buiten de opdracht
  verwerkt, is voor dat deel zelf verantwoordelijke.

**Voorbehoud:** VAYLIDE bepaalt zelf een deel van de essentiële middelen: de vaste vragen, de velden en de
standaardbewaartermijn van 90 dagen.
- Een verwerker mag een vooraf ingerichte dienst aanbieden, als de verantwoordelijke die inrichting actief aanvaardt en om
  aanpassing kan vragen (EDPB Guidelines 07/2020, punt 30 en 84).
- Bij platforms en standaardtools kan ook **gezamenlijke verantwoordelijkheid** ontstaan (punt 64 tot 67).
- De rol als verwerker is dus verdedigbaar, mits:
  - de verwerkersvoorwaarden de inrichting beschrijven en de organisator die aanvaardt;
  - VAYLIDE de gegevens niet voor eigen doelen gebruikt;
  - instructies van de organisator (zoals eerder verwijderen) worden gevolgd.
- **Juridisch te beoordelen.**

**Wat dit betekent:**
- Een voorstel voor verwerkersvoorwaarden voor alle organisatoren staat in `docs/VERWERKERSOVEREENKOMST.md`.
- In de privacyverklaring staat de rol als "[Voorstel, juridisch te beoordelen]". Het besluit `rol_gasten` blijft open,
  dus live starten wordt geweigerd tot het is ingevuld.

## Procedure bij onverwachte gevoelige gegevens

Ook met vaste vragen kan iemand in de toelichting of het liedjesveld iets gevoeligs zetten. De uitleg bij het veld
verkleint dat risico, maar neemt de verantwoordelijkheid niet weg.

1. **Wie beoordeelt:**
   - alleen de eigenaar van VAYLIDE (de enige met toegang tot de database);
   - geen andere personen, geen AI-dienst en geen automatische controle van antwoorden.
2. **Hoe VAYLIDE het merkt:**
   - via een melding van een gast of de organisator, of toevallig bij ondersteuning;
   - VAYLIDE doorzoekt antwoorden niet uit zichzelf.
3. **Toegang beperken:**
   - het beheer toont geen aanmeldingen;
   - kijk alleen naar het ene antwoord waar het om gaat;
   - verwijs in e-mail, notities en tickets naar de uitnodiging en de aanmelding (de code), nooit naar de inhoud;
   - maak geen kopieën, schermafbeeldingen of exports;
   - foutmails bevatten geen aanmeldgegevens (gebouwd).
4. **Maatregel:**
   - **De gast vraagt het zelf:** wijzen op de persoonlijke link (zelf wijzigen of verwijderen). Lukt dat niet, dan de
     organisator vragen de aanmelding te verwijderen, of, na instructie, de inhoud van dat ene veld wissen.
   - **VAYLIDE ziet het zelf:** de organisator informeren (zonder de inhoud te herhalen) en voorstellen het te laten
     verwijderen. VAYLIDE is verwerker, dus verwijderen gebeurt in overleg met of op instructie van de organisator.
     Uitzondering: direct gevaar of een beveiligingsincident.
   - **Een oude eigen vraag vraagt naar gevoelige gegevens:** met de organisator de vraag weghalen en opnieuw publiceren,
     en afspreken wat er met de gegeven antwoorden gebeurt.
   - **Gevoelige gegevens zijn bij de verkeerde persoon beland:** behandelen als mogelijk datalek (art. 33 en 34 AVG) en
     de organisator direct informeren.
5. **Termijnen:**
   - **[Termijn vaststellen]** voor reactie en uitvoering. Verzoeken van gasten vallen voor de organisator onder de
     wettelijke termijn van een maand.
   - Wat verwijderd is, kan nog in back-ups staan tot die zijn vervangen (nu 14 nachten). Bij terugzetten opnieuw
     verwijderen.
6. **Vastleggen:** datum, soort melding, genomen maatregel en wie is geïnformeerd. Niet de gevoelige inhoud zelf.
7. **Nog niet gebouwd (voorstel):** een beheerfunctie om één veld van één aanmelding te wissen, met registratie zonder de
   inhoud. Nu kan de organisator alleen de hele aanmelding verwijderen, en de eigenaar alleen via de database.

## Geparkeerd: "optie B" (dieet, allergieën en gezondheid)

Niet gebouwd en niet aangezet. Een latere functie voor dieetwensen of allergieën vraagt eerst een eigen beoordeling van:
- een passende grondslag (art. 6) **én** een uitzondering voor bijzondere persoonsgegevens (art. 9 lid 2, bijvoorbeeld
  uitdrukkelijke toestemming);
- duidelijke informatie vooraf, bij het veld zelf;
- beperkte toegang (alleen wie het nodig heeft) en een aparte, korte bewaartermijn;
- een werkende procedure om de toestemming in te trekken en de gegevens te verwijderen;
- een nieuwe DPIA-afweging.

Een algemeen privacyvinkje of akkoord met de voorwaarden is daarvoor onvoldoende. Let bij zakelijke evenementen op de
afhankelijkheid tussen werkgever en werknemer: toestemming is daar zelden vrij.

## Foto's en AI

- **Gezichten detecteren voor de uitsnede (actief):**
  - YuNet draait lokaal op de server (OpenCV) en geeft alleen posities van gezichten.
  - Er wordt geen template gemaakt, niets vergeleken en niemand geïdentificeerd.
  - Opgeslagen: middelpunt en aantal (getest: er is geen veld voor kenmerken).
  - Dit is **gezichtsdetectie, geen biometrische identificatie**. Biometrische gegevens zijn gegevens die door een
    specifieke technische verwerking unieke identificatie mogelijk maken (AP, "Biometrie").
- **Externe beeldbewerking:** alleen "eigen gezichten" (Gemini). Die staat uit en is niet aangezet.
  - Daarbij gaan foto's van gezichten naar Google.
  - Vóór aanzetten nodig: een DPIA, een verwerkersovereenkomst, afspraken over doorgifte en training, en uitleg vooraf.
  - De verklaring meldt dat de functie uit staat. Zet iemand hem aan, dan blokkeert de controle de livegang.
- **AI-tekstvoorstellen (Anthropic):**
  - Alleen tekst, alleen op verzoek van de klant, en het voorstel wordt pas gebruikt na overnemen.
  - Er gaan geen foto's of bijlagen mee (gecontroleerd in `core/ai.py` en `wishes/services.py`).
  - Buiten de EER (VS). Nodig: de afspraken met Anthropic controleren en vastleggen in `VIERLIEF_AI_AFSPRAKEN`.
- **DPIA-beoordeling:** gemaakt met de lijst van de AP en de 9 EDPB-criteria (vuistregel: 2 of meer = DPIA).
  - **Gezichtsdetectie:** hoogstens 1 criterium (nieuwe technologie). Geen biometrische identificatie, niet grootschalig.
    **Niet verplicht**; leg de onderbouwing vast.
  - **Aanmeldingen:** met de vaste vragenlijst (optie A) worden geen gevoelige gegevens uitgevraagd. Het gaat om kleine
    aantallen per uitnodiging. **Niet verplicht.** Opnieuw beoordelen als de aantallen groot worden, als optie B ooit wordt
    gebouwd, of als oude eigen vragen op de testsite toch gevoelige gegevens blijken te vragen.
  - **Anthropic:** 1 criterium (nieuwe technologie), gewone gegevens. **Niet verplicht.**
  - **Eigen gezichten:** foto's van gezichten, mogelijk kinderen, generatieve AI buiten de EER; 2 of meer criteria. **DPIA
    vóór aanzetten.**
  - Dit oordeel moet een jurist bevestigen.

## Bewaartermijnen: wat er gebeurt en voorstellen

**Wat de code elke nacht doet** (`apply_retention`, via de geplande taak `vaylide-taken` in `render.yaml`):
- uitnodigingen na de looptijd op "Verlopen" zetten;
- aanmeldingen verwijderen 90 dagen nadat de uitnodiging offline ging;
- ontwerpen zonder bevestigd e-mailadres verwijderen na 30 dagen;
- onbestelde ontwerpen in een account verwijderen na 365 dagen;
- foto's van eigen gezichten opruimen;
- inlogcodes verwijderen na 2 dagen;
- **nieuw:** verlopen sessies en cachewaarden verwijderen.

**Controleer in Render of die geplande taak echt bestaat en draait.** Dat heb ik niet kunnen zien.

**De 365 dagen voor onbestelde ontwerpen:** die termijn wordt uitgevoerd en klopt met de tekst. Inhoudelijk is hij te
verdedigen: een klant kan een jaar vooruit werken aan een bruiloftskaart. Kies je korter, pas dan de waarde aan in Beheer
→ Instellingen.

**Voorstellen** (niet ingevoerd; besluit per sleutel in `BESLUITEN`):

| Sleutel | Voorstel | Waarom |
|---|---|---|
| `bewaar_gekochte_kaarten` | Inhoud en foto's 90 dagen na het einde van de looptijd verwijderen; de bestelling blijft | Zelfde moment als de aanmeldingen. Er blijft ruimte voor "Langer online" en voor een export door de klant. |
| `bewaar_account` | Account zonder ontwerpen en zonder activiteit na 24 maanden anonimiseren, met een e-mail vooraf | Voorkomt accounts die nergens meer voor nodig zijn; de bestelgegevens blijven voor de administratie. |
| `bewaar_contact` | 12 maanden na het laatste bericht | Genoeg om terugkerende vragen te volgen |
| `bewaar_wensen` | 12 maanden na afronden als er niet besteld is; anders als bestelgegevens | Idem |
| `bewaar_herroepingen` | Zolang de bijbehorende bestelgegevens (7 jaar), of korter na juridisch advies | Het is bewijs van de afhandeling |
| `bewaar_emails` | 90 dagen | Om bezorgproblemen te onderzoeken. De bestelbevestiging heeft de klant zelf. |
| `bewaar_logs` | De termijn van Render overnemen (na te kijken in het Render-dashboard) | Niet zelf in te stellen |
| Tweede back-uplocatie | 30 dagen via een bewaarregel bij de aanbieder (staat al in `docs/BACKUP.md`) | Alleen als die locatie wordt gebruikt |

Ook voor de nieuwsbrief: het bewijs van de toestemming blijft bewaard tot het afmelden. Voorstel: daarna de tekst nog 1 jaar
als bewijs bewaren en dan wissen. Nu wist `anonymize_user` het alleen bij het verwijderen van het account.

## Verschillen tussen de tekst en de techniek

- **Oude tekst bij het aanmeldformulier:** "Alleen de organisator ziet je antwoord". Technisch kan VAYLIDE bij de
  database, en de tekst gaf geen link. Vervangen.
- **Oude tekst bij de AI-hulp:** "er wordt niets opgeslagen zonder jouw akkoord". Dat ging over de kaart, niet over
  Anthropic. Vervangen, met de aanbieder erbij als AI aan staat.
- **De concepttekst noemt factuurgegevens:** VAYLIDE maakt geen facturen en heeft geen factuurgegevens. Weggelaten.
- **De concepttekst noemt contactgegevens van gasten:** die worden niet gevraagd. Weggelaten.
- **Concept onderdeel 4, "bij de uitnodiging moet duidelijk zijn wie de organisator is":** een contactpersoon is
  optioneel. De naam op de kaart is meestal genoeg; dit wordt niet afgedwongen.
- **Verwijderde gegevens in back-ups:** die kunnen tot 14 dagen in een back-up blijven staan. Dat staat in de tekst.
  Terugzetten zonder opnieuw te verwijderen is handwerk (`core/backup.py`); maak er een vaste stap van.
- **Foutmails:** die kunnen ingevulde formuliervelden bevatten. Voor de aanmeldformulieren is dat nu uitgezet
  (`sensitive_post_parameters`); voor contact, herroepen en extra wensen nog niet (voorstel: ook daar).
- **Wijzigcode in de adresbalk:** de persoonlijke link om een antwoord te wijzigen bevat de code in het pad, dus die komt
  in de toegangslogs van de server en van Render. Dat geeft toegang tot één antwoord. Voorstel: de code uit het logformaat
  weglaten, of een kortere geldigheid.
- **Oude eigen vragen:** uitnodigingen van vóór 30 september 2026 kunnen nog een eigen vraag bevatten. De privacyverklaring
  zegt dat. Zie "Bestaande uitnodigingen".
- **Export van eigen inhoud:** alleen de gastenlijst kan geëxporteerd worden, niet de foto's en teksten. Dat raakt het recht
  op overdracht.
- **Gevolg van de controle bij livegang:** in live-modus mag geen besluit meer open staan. Dat is bewust streng.

## Nog nodig van de eigenaar

1. **Juridische naam en vestigingsadres** (al nodig voor de voorwaarden).
2. **Besluiten in `core/privacyverklaring.py` → `BESLUITEN`:** vul per sleutel de definitieve zin in, na juridisch advies.
3. **E-maildienst:** kies er een, bij voorkeur in de EER, en zet `VIERLIEF_EMAIL_AANBIEDER`, bijvoorbeeld
   `Naam B.V. (Nederland)`. Staat hij buiten de EER, vul dan onderdeel 8 aan.
4. **Tweede back-uplocatie:** gebruik je die, zet dan `VIERLIEF_BACKUP_AANBIEDER`.
5. **AI:** wil je tekstvoorstellen via Anthropic, controleer en teken dan de verwerkersovereenkomst en zet
   `VIERLIEF_AI_AFSPRAKEN` (de doorgifte-afspraken in één zin). Anders geen `ANTHROPIC_API_KEY` op Render.
6. **Render controleren:** of de geplande taak draait, hoe lang logs bewaard worden, en of `ANTHROPIC_API_KEY` gezet is.
7. **Verwerkersvoorwaarden voor alle organisatoren:** zie `docs/VERWERKERSOVEREENKOMST.md`.
8. **Oude eigen vragen op de testsite:** draai `python manage.py rsvp_vragen_rapport` in de Render-shell en beslis per
   geval (zie "Bestaande uitnodigingen").
9. **De vaste vragenlijst:** controleer de 6 vragen en antwoordopties in `invitations/vragen.py`. Nieuwe vragen alleen na
   beoordeling.
10. **Procedure bij onverwachte gevoelige gegevens:** de reactietermijn vaststellen, en besluiten of er een beheerfunctie
   komt om één veld te wissen.
11. **Privacy-e-mailadres:** nu info@vantorstudio.nl (voorlopig).

## Juridisch te beoordelen

1. **Rolverdeling per verwerking:** is VAYLIDE verwerker voor kaartinhoud en aanmeldingen, ook al bepaalt VAYLIDE de vaste
   vragen en de standaardbewaartermijn, of is er gezamenlijke verantwoordelijkheid? Dezelfde vraag bij particulieren
   onder de huishoudelijke uitzondering (EDPB Opinion 7/2024, punt 19 en 20).
2. **Verwerkersvoorwaarden:** kunnen die in de algemene voorwaarden worden opgenomen voor alle organisatoren, ook
   consumenten? En welke meldtermijn bij datalekken?
3. **De vaste vragenlijst:** is die neutraal genoeg? Bijvoorbeeld: kan "Wanneer ben je erbij?" of "geregeld vervoer"
   iets gevoeligs onthullen?
4. **Oude eigen vragen op gepubliceerde uitnodigingen:** mag VAYLIDE als verwerker zo'n vraag laten staan tot het einde
   van de looptijd, of moet er ingegrepen worden?
5. **Grondslag voor gegevens van anderen op de kaart:** foto's, namen, contactpersoon.
6. **DPIA-oordeel:** geen verplichte DPIA voor wat nu actief is; wel een DPIA vóór eigen gezichten.
7. **De voorgestelde bewaartermijnen.**
8. **Doorgifte naar de VS:** Render (DPF of standaardcontractbepalingen) en, als het aan staat, Anthropic.
9. **Mollie als zelfstandig verantwoordelijke:** klopt de omschrijving in onderdeel 7?
10. **Zonder cookiebanner:** alleen functionele cookies en opslag, zoals in onderdeel 10.
11. **De reactietermijn en de tekst over identiteitscontrole** in onderdeel 12.

## Getest

Zie `docs/CONTROLES.md`, onder "Privacyverklaring".

## Bronnen (geraadpleegd op 30 september 2026)

- [AP: Recht op informatie, en wat in een privacyverklaring moet](https://www.autoriteitpersoonsgegevens.nl/themas/basis-avg/privacyrechten-avg/recht-op-informatie)
- [AP: Data protection impact assessment (DPIA), met de 9 criteria](https://www.autoriteitpersoonsgegevens.nl/themas/basis-avg/praktisch-avg/data-protection-impact-assessment-dpia)
- [AP: Lijst verplichte DPIA](https://www.autoriteitpersoonsgegevens.nl/documenten/lijst-verplichte-dpia)
- [AP: Biometrie](https://autoriteitpersoonsgegevens.nl/nl/onderwerpen/identificatie/biometrie)
- [AP: Cookies](https://autoriteitpersoonsgegevens.nl/nl/onderwerpen/internet-telefoon-tv-en-post/cookies)
- [AP: Gezondheid](https://www.autoriteitpersoonsgegevens.nl/nl/onderwerpen/gezondheid)
- [AP: Verantwoordelijke en verwerker](https://autoriteitpersoonsgegevens.nl/themas/basis-avg/avg-algemeen/verantwoordelijke-en-verwerker)
- [EDPB Opinion 7/2024 (EU Cloud Service Data Protection, Auditor-criteria), punt 17 tot 20 over de huishoudelijke uitzondering](https://www.edpb.europa.eu/system/files/2024-04/edpb_opinion_202407_opiniononauditorcertificationcriteria_en.pdf)
- [EDPB Guidelines 07/2020 over verwerkingsverantwoordelijke en verwerker (versie 2.1), punt 30, 40, 64 tot 67 en 84](https://www.edpb.europa.eu/system/files/2023-10/EDPB_guidelines_202007_controllerprocessor_final_en.pdf)
- [Render: Data Processing Addendum](https://render.com/dpa)
- [Mollie: Privacy](https://www.mollie.com/legal/privacy)
- [Anthropic Privacy Center: bewaartermijn API-gegevens](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)

De bronnen van leveranciers zijn geen officiële bronnen. Het contract zelf (de verwerkersovereenkomst) geldt.

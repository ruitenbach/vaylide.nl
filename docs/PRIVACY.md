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
| Aanmeldingen | Naam, komt ja/nee, aantal, antwoorden op eigen vragen, toelichting, versleutelde wijzigcode | `invitations/models.py` (`GuestResponse`) | 90 dagen nadat de uitnodiging offline ging (instelbaar in beheer) |
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

## Rol bij gastgegevens (beoordeling, geen juridisch oordeel)

- **Particuliere organisator** (bruiloft, verjaardag, kerst):
  - De organisator valt waarschijnlijk onder de uitzondering voor huishoudelijk gebruik (art. 2 lid 2 sub c AVG).
  - Volgens overweging 18 AVG blijft de AVG wel gelden voor wie de middelen levert. Dat is VAYLIDE.
  - VAYLIDE bepaalt hoe de aanmeldingen worden opgeslagen, beveiligd en verwijderd. Voor die verwerking is VAYLIDE dan
    waarschijnlijk **zelf verwerkingsverantwoordelijke**.
  - Mogelijke grondslag: gerechtvaardigd belang, namelijk gasten laten reageren op een uitnodiging die ze ontvingen.
  - De overeenkomst met de koper is **geen** grondslag voor gastgegevens: de gast is geen partij bij die overeenkomst.
- **Zakelijke organisator** (gelegenheid "Zakelijk evenement", organisatie als afzender):
  - De organisatie bepaalt het doel. Zij is waarschijnlijk **verwerkingsverantwoordelijke** en VAYLIDE **verwerker**.
  - Dan is een **verwerkersovereenkomst nodig** (art. 28 AVG). Die bestaat nu niet.
  - Een voorstel staat in `docs/VERWERKERSOVEREENKOMST.md`. De verklaring vervangt die overeenkomst niet.
- **Wat gasten nu bij het formulier krijgen:**
  - een korte tekst en een link naar onderdeel 4 van de verklaring;
  - de naam van de organisator staat meestal op de kaart;
  - een contactpersoon is optioneel.
- **Besluit nodig:** `rol_gasten` in `core/privacyverklaring.py`.

## Gevoelige gegevens bij het aanmelden

- **Wat er is:**
  - Er zijn **geen vaste velden** naar gezondheid, religie of toegankelijkheid; er is niets toegevoegd.
  - Wel kan de organisator tot 5 **eigen vragen** stellen, en die ook verplicht maken.
- **Wat VAYLIDE zelf suggereert:** "dieetwensen of allergieën", in `core/content.py:144`, `catalog/seed.py:69` (omschrijving
  extra optie), `invitations/demo.py` (voorbeeldkaarten) en `e2e/fixtures.py`.
  - Allergieën zijn gezondheidsgegevens.
  - Dieetwensen kunnen iets zeggen over gezondheid of geloof.
  - Dat zijn bijzondere persoonsgegevens (art. 9 AVG). Een algemeen akkoord met de verklaring is daarvoor niet genoeg.
- **Voorstel (besluit `gevoelige_vragen`), kies een van deze:**
  - **a)** De voorbeelden aanpassen naar iets neutraals, zoals vervoer of een liedje voor de playlist. Bij het maken van een
    eigen vraag de tip geven om niet naar gezondheid, geloof of andere gevoelige gegevens te vragen.
  - **b)** Als dieetwensen of allergieën mogelijk moeten blijven:
    - zo'n vraag altijd optioneel maken;
    - er een aparte, niet vooraf aangevinkte uitdrukkelijke toestemming bij vragen;
    - uitleggen wie het ziet en wanneer het wordt verwijderd;
    - de bewaartermijn kort houden.
  - Dit is **niet** in de code veranderd, want het is een productkeuze.

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
  - **Aanmeldingen:** alleen met gevoelige eigen vragen 1 criterium (gevoelige gegevens). Het gaat om kleine aantallen per
    uitnodiging. Nu **niet verplicht**. Opnieuw beoordelen als de aantallen groot worden of als optie b wordt gekozen.
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
- **Foutmails:** die kunnen ingevulde formuliervelden bevatten, zoals antwoorden van gasten.
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
7. **Verwerkersovereenkomst voor zakelijke klanten:** zie `docs/VERWERKERSOVEREENKOMST.md`.
8. **Privacy-e-mailadres:** nu info@vantorstudio.nl (voorlopig).

## Juridisch te beoordelen

1. **Rol en grondslag bij gastgegevens:** particulier tegenover zakelijk, en of gerechtvaardigd belang past.
2. **Eigen vragen met mogelijke gezondheidsgegevens:** optie a of b hierboven.
3. **Grondslag voor gegevens van anderen op de kaart:** foto's, namen, contactpersoon.
4. **DPIA-oordeel:** geen verplichte DPIA voor wat nu actief is; wel een DPIA vóór eigen gezichten.
5. **De voorgestelde bewaartermijnen.**
6. **Doorgifte naar de VS:** Render (DPF of standaardcontractbepalingen) en, als het aan staat, Anthropic.
7. **Mollie als zelfstandig verantwoordelijke:** klopt de omschrijving in onderdeel 7?
8. **Zonder cookiebanner:** alleen functionele cookies en opslag, zoals in onderdeel 10.
9. **De reactietermijn en de tekst over identiteitscontrole** in onderdeel 12.

## Getest

Zie `docs/CONTROLES.md`, onder "Privacyverklaring".

## Bronnen (geraadpleegd op 30 september 2026)

- [AP: Recht op informatie, en wat in een privacyverklaring moet](https://www.autoriteitpersoonsgegevens.nl/themas/basis-avg/privacyrechten-avg/recht-op-informatie)
- [AP: Data protection impact assessment (DPIA), met de 9 criteria](https://www.autoriteitpersoonsgegevens.nl/themas/basis-avg/praktisch-avg/data-protection-impact-assessment-dpia)
- [AP: Lijst verplichte DPIA](https://www.autoriteitpersoonsgegevens.nl/documenten/lijst-verplichte-dpia)
- [AP: Biometrie](https://autoriteitpersoonsgegevens.nl/nl/onderwerpen/identificatie/biometrie)
- [AP: Cookies](https://autoriteitpersoonsgegevens.nl/nl/onderwerpen/internet-telefoon-tv-en-post/cookies)
- [AP: Gezondheid](https://www.autoriteitpersoonsgegevens.nl/nl/onderwerpen/gezondheid)
- [Render: Data Processing Addendum](https://render.com/dpa)
- [Mollie: Privacy](https://www.mollie.com/legal/privacy)
- [Anthropic Privacy Center: bewaartermijn API-gegevens](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data)

De bronnen van leveranciers zijn geen officiële bronnen. Het contract zelf (de verwerkersovereenkomst) geldt.

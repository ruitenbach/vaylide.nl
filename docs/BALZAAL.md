# Balzaal (ontwerp `balzaal`)

Een bruiloftsontwerp (ook voor verloving) met aangeleverde beelden als lagen: de balzaal (achtergrond), het bruidspaar
(transparant, ervoor) en de bloemen (transparant, voorgrond). De personen zijn fictieve voorbeeldpersonen. De kaart
opent vanuit een ivoren envelop met een lakzegel (standaardzegel of persoonlijk zegel, volgens het pakket). Daarna
verschijnen zaal, paar, bloemen en namen rustig, met warm licht en een subtiele diepte (`balzaal.js`, alleen met een muis).
Alle tekst (namen, datum, tijd, locatie, teksten, aanmelden) is echte tekst; niets staat vast in de afbeeldingen.

## Bestanden

| Bestand | Wat |
|---|---|
| `designs/balzaal/v1/invitation.html`, `style.css`, `balzaal.js`, `manifest.json` | het ontwerp |
| `designs/balzaal/v1/img/balzaal.webp` (941×1672) en `-600` | de zaal (uit `01-balzaal.png`) |
| `designs/balzaal/v1/img/paar-bruin-blond.webp` (900 breed) en `-560` | het standaardpaar: man bruin haar, vrouw blond (uit `02-bruidspaar.png`, bijgesneden tot de zichtbare pixels) |
| `designs/balzaal/v1/img/bloemen.webp` (941×1672) en `-600` | de bloemen (uit `03-bloemen.png`) |
| `catalog/paar.py` | welk paar getoond wordt en of de haarkleurkeuze aan kan |

De beelden zijn omgezet naar WebP met behoud van transparantie en verhouding (niet uitgerekt). Op een telefoon laadt de
kaart samen ongeveer 250 kB aan beelden.

## Special

Balzaal staat onder **Specials** (eigen blok en keuze op de collectiepagina, label "Special" op de kaart), niet tussen de
gewone kaarten. Een special heeft een eigen meerprijs: een extra optie in Beheer → Prijzen met functie `special` en code
`special-balzaal`. **Die is er nog niet**: tot de eigenaar de prijs instelt, is Balzaal niet te bestellen (de bestelpagina
zegt dat eerlijk). Een ontwerp special maken of niet: Beheer → Ontwerpen → "special".

## Haarkleur kiezen (voorbereid, nog niet zichtbaar)

In de editor (stap Stijl) komen twee keuzes: **Haarkleur man** en **Haarkleur vrouw**, elk zwart, bruin of blond
(standaard man bruin, vrouw blond). De keuze wordt bewaard (`style.haar`) en blijft staan bij latere wijzigingen.
**De keuze verschijnt pas als alle negen combinaties bestaan**; tot die tijd ziet iedereen het standaardpaar.
Geen kleurfilter (dat verkleurt ook huid en kleding).

De acht ontbrekende combinaties worden hele scènes (zaal met paar, 941×1672): `img/scene-<man>-<vrouw>.webp` en
`-600.webp`. Maken met de beeld-API (Gemini, ca. $0,14 per beeld, samen ca. $1,12 plus nieuwe pogingen):

    python tools/balzaal/maak_haarvarianten.py --schatting
    python tools/balzaal/maak_haarvarianten.py --alle        # GEMINI_API_KEY in de omgeving

Bekijk de beelden vóór je ze in Git zet. Ontbrekend: zwart-zwart, zwart-bruin, zwart-blond, bruin-zwart, bruin-bruin,
blond-zwart, blond-bruin, blond-blond. Aanwezig: bruin-blond (het aangeleverde paar).

## De dans (voorbereid, nog geen video)

De aangeleverde beelden bevatten geen beweging; een CSS-beweging van de foto is geen dans en is bewust niet gebouwd.
De dans wordt een korte video (8 seconden, 9:16) gemaakt met **Google Veo 3.1 (image-to-video)** vanaf de scène: het
paar danst en de bruid maakt één pirouette. Op de kaart:

- Er is een videolaag met poster (de stilstaande scène) en een knop om de dans af te spelen of te pauzeren.
- De video speelt na het openen, geluid uit, en herhaalt rustig.
- Bij 'minder beweging', bij stilgezette beweging en zonder JavaScript blijft de stilstaande scène staan.
- Zonder videobestand is er geen dans en geen knop.
- Met eigen gezichten wordt de dans van het voorbeeldpaar niet getoond.

Maken (kost geld per poging; alleen een gelukte video wordt berekend):

    python tools/balzaal/maak_dansvideo.py --schatting
    python tools/balzaal/maak_dansvideo.py --proef                     # Veo Fast 720p, ca. $0,80, naar data/balzaal-proef/
    python tools/balzaal/maak_dansvideo.py --model standaard --resolutie 1080p --definitief   # ca. $3,20

| Veo 3.1 | per seconde | 8 seconden |
|---|---|---|
| Lite 720p / 1080p | $0,05 / $0,08 | $0,40 / $0,64 |
| Fast 720p / 1080p | $0,10 / $0,12 | $0,80 / $0,96 |
| Standaard 720p–1080p | $0,40 | $3,20 |

Reken op meerdere pogingen voor een mooie draai (bijv. 3–6 proefscènes: $2,40–$19). Per haarkleur een eigen video:
9 × 1 geslaagde video ≈ $7–29, plus pogingen. Een dans met **eigen gezichten** zou per klant een extra video vragen
(≈ $0,80–3,20 per poging); dat is niet gebouwd.

Voor mobiel: `ffmpeg` (gratis) verkleint de video tot ~2 MB (het script doet dat als ffmpeg aanwezig is).

## Getest

Zie `docs/CONTROLES.md` onder "Balzaal".

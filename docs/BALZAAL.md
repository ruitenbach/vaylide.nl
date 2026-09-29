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

## Haarkleur kiezen (voorbereid, nog niet zichtbaar)

In de editor (stap Stijl) komen twee keuzes: **Haarkleur man** en **Haarkleur vrouw**, elk zwart, bruin of blond. De
standaard is man bruin, vrouw blond. De keuze wordt bewaard in de uitnodiging (`style.haar`) en blijft staan als de klant
later iets anders aanpast.

**De keuze verschijnt pas als alle negen combinaties als beeld bestaan.** Tot die tijd ziet iedereen het standaardpaar.
Een kleurfilter is bewust niet gebruikt (dat verkleurt ook huid en kleding).

Nog te maken: acht beelden (steeds in twee formaten), met dezelfde houding, gezichten, kleding, belichting en uitsnede als
`paar-bruin-blond.webp`. De jurk blijft helder wit en de smoking zwart:

| man \ vrouw | zwart | bruin | blond |
|---|---|---|---|
| **zwart** | `paar-zwart-zwart` | `paar-zwart-bruin` | `paar-zwart-blond` |
| **bruin** | `paar-bruin-zwart` | `paar-bruin-bruin` | ✓ (aanwezig) |
| **blond** | `paar-blond-zwart` | `paar-blond-bruin` | `paar-blond-blond` |

Per combinatie: `paar-<man>-<vrouw>.webp` (900 px breed) en `paar-<man>-<vrouw>-560.webp` (560 px breed), transparant,
zelfde uitsnede als het standaardpaar. Zet ze in `designs/balzaal/v1/img/`; zodra alle negen er zijn, verschijnt de
keuze vanzelf (test: `tests/test_balzaal.py`).

## Getest

Zie `docs/CONTROLES.md` onder "Balzaal".

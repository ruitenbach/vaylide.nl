# <Naam van het ontwerp>

> Kopieer dit bestand naar `docs/designs/<slug>.md` en vul het in. Laat een onderdeel dat nog niet bekend is leeg met "nog niet bepaald"; verzin niets.
> Eén bestand per ontwerp. Dit document is de vaste bron: wat hier staat, is leidend boven losse ChatGPT- of Claude-sessies.

## 1. Naam

<De naam zoals klanten die zien, bijvoorbeeld "Gouden Avond".>

## 2. Slug

`<slug>`   (de map `designs/<slug>/v1/`, de demo-URL `/voorbeeld/<slug>/`, de code in het manifest)

## 3. Categorie

<Bijvoorbeeld: Special / gewone kaart · gelegenheid(en): bruiloft, kerst, ... · pakket of meerprijs, indien bekend.>

## 4. Status

<Kies één en zet de datum erbij: idee · concept goedgekeurd · in aanbouw · lokaal klaar, ter beoordeling · op staging · current (live) · gearchiveerd.>
<Staat het ontwerp als `current` of alleen als losse versie? Op welke branch staat het werk?>

## 5. Concept / verhaal

<Waar gaat het ontwerp over, voor wie, welke sfeer en welk gevoel? Kort en concreet.>

## 6. Opening / animatie

<Wat ziet de gast, stap voor stap, met tijden. Wat is de beweging (CSS, GSAP, video)? Wat is de eigen bediening (overslaan, opnieuw beleven, geluid)? Wat gebeurt er bij 'minder beweging'?>

## 7. Pagina na de opening

<Opbouw van de uitnodiging: welke banden of secties, in welke volgorde, met welke gedeelde onderdelen (aftellen, programma, locatie, aanmelden, enz.). Hoe sluit het aan op de klantomgeving, personalisatie en RSVP?>

## 8. Assets en waar ze staan

| Asset | Pad in de repository | Herkomst | Opmerking |
|---|---|---|---|
| | `designs/<slug>/v1/...` | | |

<Wat staat bewust niet in Git (te grote bestanden, masters) en waar staat het dan?>

## 9. Externe AI/video-output

<Per stuk output: welke tool of dienst, welke prompt of instructie, welke instellingen, datum, welk bestand het opleverde, wat is goedgekeurd en wat is verworpen. Bewaar prompts hier of in `tools/design-references/<slug>/`.>

## 10. Technische bouwinstructies

<Hoe wordt het gebouwd: bestanden (`manifest.json`, `invitation.html`, `style.css`, script), registratie (`sync_designs`), eventuele vaste regels (CSP, geen inline script of stijl, GSAP-gebruik), prestatie-eisen, toegankelijkheid, wat expliciet niet mag (bijvoorbeeld deeltjes die vallen).>

## 11. Wat al afgerond is

- <afgerond onderdeel, met datum>

## 12. Wat nog moet gebeuren

- [ ] <openstaand punt>

## 13. Besluiten die niet opnieuw ter discussie hoeven

- <besluit, met datum en wie het nam, en waarom>

## 14. Laatste relevante commit

`<hash>` op branch `<branch>` (<datum>): <korte omschrijving>

## 15. Volgende stap

<Precies één concrete volgende stap, met wie of wat daarop wacht.>

# Kerstmarkt, Kerstpaleis, Kerstcoupé en Kerstbal

Vier nieuwe kerstkaarten met een eigen film als opening, overgenomen van een collega (15 oktober 2026). Alle vier staan op de ontwikkelbranch `claude/kerstontwerpen-integratie` (lokaal, niet gepusht) en zijn **Luxe, € 24,95 inclusief btw, 12 maanden online** (besluit van de eigenaar). De prijsstructuur zelf is niet aangepast: alleen vier regels in `INDELING` (`catalog/prijzen.py`).

| Kaart | Opening | Kleuren | Herkomst |
|---|---|---|---|
| Kerstmarkt (`kerstmarkt`) | Film vanuit een reuzenrad; kaart met ster klapt open | Avondblauw, Gondelrood, Dennengroen | zip Kerstmarkt: alleen `designs/kerstmarkt`, kaartbeeld, test, tool en e2e (de rest van die oudere sitekopie is niet overgenomen) |
| Kerstpaleis (`kerstpaleis`) | Film: de deuren van een paleis gaan open | Kerstrood, Dennengroen, Nachtblauw | losse voorbeeldkaart, omgezet naar een ontwerp met de gewone velden; de voorbeeldbalk, kleurkiezer en nep-aanmelding zijn vervallen |
| Kerstcoupé (`kerstcoupe`) | Film: fluwelen gordijnen gaan open op een bergdorp | Rood fluweel, Sneeuwnacht, Mahonie | patch, **niet toegepast** (paste niet op deze basis): de nieuwe bestanden zijn overgenomen en de regels in gedeelde bestanden met de hand toegevoegd |
| Kerstbal (`kerstbal`) | Film: een kerstbal gaat open, de kaart komt eruit | Kerstrood | losse voorbeeldpagina, omgezet naar een ontwerp. Eén kleur: de pagina noemt een tweede ("ivoor") maar bevat die niet, dus die is niet verzonnen |

## Wat er gewijzigd is buiten de ontwerpmappen

- `catalog/prijzen.py`: vier regels bij Luxe. `catalog/collectie.py`: de vier in groep B. `invitations/demo.py`: voorbeeldbeelden en gelegenheid.
- Tests: aantallen in `test_effects`, `test_collectie`, `test_prijsstructuur`; volgorde van de kerstlijst in `test_kerst` en `test_middernacht` (nieuwste eerst: de vier staan nu voor Gloria). Nieuw: `test_kerstmarkt`, `test_kerstpaleis`, `test_kerstcoupe`, `test_kerstbal` en een bestel- en publicatietest in `test_prijsstructuur`.
- Het gedeelde `invite.js` is niet aangepast. Kerstbal start zijn film met een eigen script (`designs/kerstbal/v1/kerstbal.js`).
- Volgorde: de vier hebben `sort_order` 41, 42, 43 en 44 en dezelfde `added_at`; omdat de collectie "nieuwste eerst" toont, staan ze bovenaan de kerstlijst. Wil je dat niet, dan kan `added_at` in de manifesten oudere tijden krijgen.

## Rechten

De films lijken met AI gemaakt. De zips zeggen dat het eigen materiaal is; de eigenaar bevestigt dat.

## Kerstbal v2 (15 oktober 2026): vloeiende overgang

In v1 bleef de kaart onzichtbaar tot het einde van de opening (4,1 s): de animatie `kb-sheet-in` had alleen een beginstand (`from`), dus de eindstand was de dekking 0 uit `.fx-motion:is(.has-cover, .is-opening) .kb-sheet`. Tussen ± 3,5 en 4,1 s bleef er een bijna leeg donker scherm over (laagste gemiddelde helderheid ± 16). In `designs/kerstbal/v2/style.css` staat daarom één regel anders: `kb-sheet-in` heeft een eindstand (`to { opacity: 1; transform: none; }`), zodat de kaart onder het wegvervagende omslag opkomt. Film, beelden, HTML (op de paden na), script, kleuren en alle andere timing zijn gelijk aan v1. Een test (`KerstbalV2Tests`) bewaakt dat. Welke versie nieuwe klanten krijgen kiest de eigenaar in Beheer (v1 blijft staan).

Opvolging (15 oktober 2026): de kaart sprong er te snel uit. In v2 komt de kaart nu in 2,9 s uit de bal (was 1,5 s) en in 1,2 s naar je toe (was 0,6 s), met zachtere versnelling; de opening duurt daardoor 5,9 s (`data-duration`, `data-fx-intro`) en het omslag vervaagt vanaf 5,2 s. Alleen timing in CSS en die twee attributen; de film is niet aangeraakt. Top van de schaalsnelheid: uit de bal ± 2,4 naar ± 0,85 per seconde, naar je toe ± 2,0 naar ± 0,7.

Gekozen versie voor nieuwe klanten: komt een nieuw ontwerp meteen met meer versies binnen (zoals Kerstbal v1 en v2), dan kiest `catalog/seed.py` (`sync_designs`) de nieuwste. Bij een bestaand ontwerp verandert er niets; daar kiest de beheerder de versie (Beheer, Ontwerpen). Kerstbal v1 blijft als versie staan; een bestelling legt de versie vast waarop ze is gemaakt.

## Tekst vrij van confetti en sneeuwvlokken (16 oktober 2026)
Bij Kerstpaleis (v1) en Kerstbal (v2) lagen de deeltjes van het openen en vieren (de `.fx-burst`-laag van `effects.js`, die boven de pagina ligt) soms over de tekst. Beide ontwerpen laden nu `invitations/static/invitations/tekstvrij.js`: dat knipt de laag rond de zichtbare tekst weg (met een marge van 5 px, tien keer per seconde bijgewerkt). De effecten zelf, hun instellingen in het manifest en de ontwerpen zijn niet veranderd; de gedeelde `effects.js` en `effects.css` ook niet. Andere ontwerpen laden het script niet. Beide versies stonden nog niet op productie. Controle: `tests/test_tekstvrij.py` (script geladen) en een visuele vergelijking met en zonder script op 390 px.

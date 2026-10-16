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

## Kerstmagie (16 oktober 2026): kerstkaart met een openingsfilm van de eigenaar

Een vijfde kerstontwerp met een film, in `designs/kerstmagie/v1/`. De film (staand, 10 seconden, zonder geluid) opent met een sneeuwkristal in close-up dat overgaat in een kerstdorp met een stoomtrein. Een tik in het midden start hem, nooit vanzelf; daarna gaat hij over in de kerstkaart, die op het laatste beeld van de film begint. Stukken uit de film keren terug in de kaart: het eindbeeld achter de kop, de trein en het plein als zachte beeldstroken tussen de onderdelen, het sneeuwkristal op het monogram.

**Productindeling (gelijk aan Kerstmarkt, Kerstpaleis, Kerstcoupé en Kerstbal):**
- gelegenheid: alleen de bestaande gelegenheid **Kerst** (`occasions: ["kerst"]`). Er is geen gelegenheid bijgekomen en er staan geen andere gelegenheden (Bruiloft, Verloving, Verjaardag, Jubileum, Zakelijk) meer in het manifest. Een kerstborrel van een bedrijf is een kerstkaart met een programma en past dus binnen Kerst;
- `envelope_mode: built_in` (de eigen filmopening; geen stap Envelop & zegel), `opening: film`, sneeuw als sfeer (bestaand effect);
- collectie: groep B in `catalog/collectie.py`, naast de vier andere kerstfilmontwerpen; `sort_order` 47 (uniek), `added_at` 16 oktober 2026 (dus bovenaan bij 'nieuwste eerst' in de kerstcollectie);
- prijs: indeling **Luxe** in `catalog/prijzen.py`, zoals de vier andere kerstfilmontwerpen: kerstkaart Luxe € 24,95, 12 maanden online. Geen nieuwe prijs, geen toeslag, geen pakketkeuze; de prijstabel is niet aangeraakt. Ontwerp en prijs zijn alleen voor Kerst te koop (voor andere gelegenheden bestaat geen prijs). De indeling Luxe is een keuze naar analogie met de vier films; de eigenaar bevestigt hem of kiest Special (dan € 49,95 en de specials-vlag);
- voorbeeld: `/voorbeeld/kerstmagie/` opent als kerstkaart (`DEFAULT_DEMO_OCCASION` in `invitations/demo.py`), met de kerstbeelden van de andere kerstontwerpen.

**Bestanden:** `intro.js` (gedrag), `media/` (mp4, webm-reserve, stills), kaartbeeld `static/img/designs/kerstmagie.webp`; de media zijn opnieuw te maken met `tools/kerstmagie/maak_media.py`. De film wordt pas geladen als de pagina klaar is en niet bij een directe link naar de aanmelding of 'databesparing'. Bij 'minder beweging' of de knop Beweging op stil opent een tik direct, met een knop **Bekijk eerst de film**. Start de film niet, dan opent de kaart gewoon.

**Rechten:** de film is door de eigenaar aangeleverd; de eigenaar bevestigt de rechten, zoals bij de andere films.

**Nog te doen:** de teksten in `intro.js` en het openingsscherm zeggen op enkele plekken (onzichtbare knoppen en schermlezertekst) 'uitnodiging' waar bij Kerst 'kerstkaart' hoort; dat is bewust niet aangepast bij het rechtzetten van de koppeling.

## Kerstmagie: helderder openingsscherm (16 oktober 2026)

Het ijskristal op het openingsscherm was te donker. De bronfilm is helder (gemiddeld 47% helderheid, de kristalarmen ruim 90%) en mijn mp4 en webm zijn daarin gelijk. Het donker kwam van een donkere sluier die ik zelf over het openingsscherm had gelegd voor de leesbaarheid van de tekst (het scherm haalde 25% in plaats van 47 tot 49%), en op brede schermen van een te donkere vervaagde achtergrond.

Wat is veranderd (alleen `designs/kerstmagie/v1/style.css` en `invitation.html`; de film, de bronbeelden en de stills zijn niet aangeraakt, en er is geen filter op de film):
- de donkere sluier is weg; het kristal behoudt zijn eigen helderheid (49% op het scherm);
- de afspeelknop is een ijswitte matglazen knop met een donkerblauwe driehoek;
- kopregel, naam en aanwijzing staan samen in één rustige matglazen plaquette onder de knop, in donkerblauwe letters; de kopregel is daarvoor van boven de knop naar de plaquette verplaatst. De knop blijft precies in het midden van het scherm;
- de vervaagde achtergrond is lichter. Een donkere strook rechts op brede schermen kwam doordat de algemene regel `img { max-width: 100% }` de achtergrond op 100% in plaats van 116% hield; `max-width: none` lost dat op, ook bij de achtergrond van de kop;
- het sneeuwkristal op het monogram aan het eind heeft een lichte in plaats van donkere sluier, met een donkerblauwe letter.

Contrast: de tekst op het openingsscherm staat op de film en valt onder `data-tekst-op-beeld`. `e2e/kerstmagie-contrast.cjs` meet hem op de echte pixels (slechtste pixel 5,2:1, eis 4,5:1).

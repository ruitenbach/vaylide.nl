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
- collectie: **groep C** in `catalog/collectie.py` (verborgen, niet bestelbaar) tot de rechten op de film zijn bevestigd; `sort_order` 47 (uniek), `added_at` 16 oktober 2026. Het ontwerp is wel aanwezig: bij de eerste synchronisatie (`post_migrate`/`sync_designs`) wordt `is_active` onwaar gezet, en daarna wijzigt synchroniseren dat niet (een keuze in Beheer blijft). Zichtbaar maken kan pas na bevestiging van de rechten: verplaats `kerstmagie` van C naar B in `catalog/collectie.py` (voor nieuwe databases) en zet in Beheer → Ontwerpen 'Zichtbaar en bestelbaar' aan (voor bestaande databases, zoals staging); pas dan ook de aantallen in `test_collectie` en de kerstlijst in `test_kerst` en `test_kerstmagie` aan. Verborgen betekent ook: geen ontwerppagina, geen voorbeeld (`/voorbeeld/kerstmagie/` geeft 404), geen zoekresultaat en niet te kiezen in de bestelroute. Om de kaart zelf te bekijken (e2e-scripts): zet hem alleen in een lokale of testdatabase aan, nooit op staging of productie zonder akkoord van de eigenaar;
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

## Kerstmagie: rijkere kaart, sneeuw met diepte en een datum onder ijs (16 oktober 2026, lokaal)

De kaart na de film is gelaagder geworden, met uitsluitend beelden uit de bestaande film (`tools/kerstmagie/maak_media.py` maakt ze opnieuw): het eindbeeld als kop (op desktop groter en met warm meegloeiende zijkanten), een panorama van bergen en viaduct, het kristal met gloed en de trein met stoom in dunne gouden boogvensters naast de brief en het programma, het water met lichtjes als achtergrond van de locatie, en een drieluik (plein, kristal dat dorp wordt, rivier) voor de afsluiting. De kop heeft kopregel met lijntjes, een groter naam, één kristal-ornament en een datumblok in één regel. Alle onderdelen blijven: aftelling, agenda, locatie en route, programma, dresscode, aanmelden, contact, foto's en personalisatie.

- **Sneeuw** (`snow.js`, vooraf gezet door `vooraf.js`): drie lagen (kleine verre sneeuw, zachte vlokken, een paar vage voorgrondvlokken), een enkel kristal, lichte wind. Tijdens het scrollen bewegen de lagen verschillend mee (diepte). Op het openingsscherm en op de kaart. De sneeuw ligt boven de beelden en onder de tekst (z-index 3, tekst 4; `.fx .inv-main` krijgt daarvoor `z-index: auto`, de kop heeft geen eigen stapelvlak). Volgt de knop **Beweging** (stilzetten laat het beeld staan) en 'minder beweging' (geen sneeuw). Zuinig: sprites één keer getekend, resolutie begrensd, op een telefoon hoogstens 40 beelden per seconde en 38 vlokken, stil bij een verborgen tabblad. De sfeer in het manifest blijft `sneeuw` (labels en beschrijving), maar `vooraf.js` zet `data-fx-sfeer` op `geen` voordat `effects.js` het leest, zodat de gedeelde engine niet dubbel tekent. De engine zelf is niet veranderd.
- **Datum onder ijs** (`kras.js`): een ijslaag (een stukje van het sneeuwkristal uit de film) over het datumblok, die je met een veeg of tik wegkrast; na ongeveer de helft smelt de rest. De datum staat altijd in de pagina (ook voor schermlezers). Uitwegen: de knop **Onthul de datum** (ook met toetsenbord), geen ijslaag bij geen JavaScript, bij minder beweging, als de knop Beweging op stil staat (of later wordt gezet), als het tekenen niet lukt of als de datum in deze sessie al onthuld is (`sessionStorage`). Tekst op het ijs: `data-tekst-op-beeld`, gemeten op de echte pixels.
- **Controle**: `e2e/kerstmagie-kaart.cjs` (sneeuw, ijslaag en uitwegen, belasting). `e2e/effecten.cjs` kent ontwerpen met een eigen sneeuwlaag (`.kl-snow`) en meet dan die canvassen; voor andere ontwerpen is er niets veranderd.
- Bewust niet verborgen: de datum staat ook in de locatiekaart en in de agenda-knoppen.

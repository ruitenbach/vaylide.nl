# Gouden Avond (ontwerp `gouden-avond`)

Een nieuw, zelfstandig bruiloftsontwerp (ook voor verloving) onder **Specials**, naast de bestaande Balzaal (die ongewijzigd is, inclusief de
optimalisatie uit commit `2d0a7af`). Twee ivoor-gouden balzaaldeuren met rijk ornamentwerk en een losse messing sleutel; de sleutel lijnt uit,
het getande uiteinde verdwijnt in het slot en hij draait om; de deuren slaan langzaam open op een filmscène van een dansend bruidspaar, terwijl
champagnegouden en ivoren hartjes, confetti en kleine lichtpuntjes uitspreiden en vervagen. Daarna staan de namen en de datum in beeld en loopt de
uitnodiging door als "een nacht in de balzaal" (zie onder) met de gedeelde onderdelen: aftellen, programma, locatie, dresscode, aanmelden. Herkomst: het goedgekeurde prototype
`Vaylide-Balzaal-Claude-overdracht.zip` (4 oktober 2026; niet in Git, de uitgepakte map `overdracht-balzaal-cinematic/` staat in `.git/info/exclude`).

## Bestanden

| Bestand | Wat |
|---|---|
| `designs/gouden-avond/v1/manifest.json` | special, palet `ivoor`, effecten (sfeer goudstof, geen knal, viering harten), onderdelen |
| `designs/gouden-avond/v1/invitation.html` | de kop (deuren, sleutel, video, feestlaag, knoppen) en daaronder de uitnodiging; namen, datum, locatie en programma komen uit de bestaande studiogegevens (automatisch ge-escaped door Django) |
| `designs/gouden-avond/v1/style.css` | deuren, sleutel, scène, feest, de uitnodiging eronder (een kopie van de Balzaal-onderdelen onder `bc-`) |
| `designs/gouden-avond/v1/gouden-avond.js` | timing van de opening, overslaan, opnieuw beleven, video, feest |
| `designs/gouden-avond/v1/media/dans.mp4` | de dansvideo, 720 × 1280, ±5 s, zonder geluid, ±1,2 MB (`balzaal-web.mp4` uit het pakket) |
| `designs/gouden-avond/v1/media/poster.jpg` | poster (ook voor 'minder beweging' en tot de video speelt) |
| `designs/gouden-avond/v1/media/kroonluchter.webp`, `boog.webp`, `vloer.webp`, `waas.webp` | uitsneden uit de poster (kroonluchter, zonsondergang door de boog, vloer met bloemen en kaarsen, een vooraf vervaagd waasje) voor de achtergronden van de banden; geen nieuwe afbeeldingen |
| `invitations/demo.py` | standaard gelegenheid en voorbeeldfoto's voor het voorbeeld |
| `tests/test_gouden_avond.py` | regressietests (zie onder) |

Het masterbestand (`balzaal-master.mp4`, 1080 × 1912, 15 MB) staat niet in de repository: te groot en niet nodig voor weergave. Het blijft in het
overdrachtspakket. Er is geen nieuwe AI-video gemaakt en de video is niet verlengd.

## Hoe de opening werkt

Opening, kop en feest zijn **één scène in de kop** (geen openingsscherm van `invite.js`): de deuren onthullen dezelfde video die daarna de kop
is, dus er is geen tweede video of overgang tussen twee lagen. Het script zet klassen op `.bc-hero` op de tijden van het prototype (ms na de tik
op de sleutel): 0 uitlijnen, 850 het getande uiteinde gaat het slot in (de tanden worden weggeknipt), 1350 omdraaien, 2200 sleutel weg, 2500
deuren open (3,9 s, 3D-scharnieren), 2900 feest, 3050 dans, 6500 namen en datum. De beweging zelf (deuren, sleutel, deeltjes) staat in de CSS op
`transform` en `opacity`. Vormen, kleuren, de 3D-scharnieren en de timing zijn die van het prototype.

Voor de kwaliteit op een telefoon is er, zonder het uiterlijk te veranderen, het volgende anders dan in het prototype:

- De 145 deeltjes bestaan alleen tijdens het feest (opgebouwd tijdens het omdraaien van de sleutel, onzichtbaar; verwijderd na 7,8 s, bij overslaan,
  bij opnieuw beleven en bij het verlaten van de pagina). Ze starten in vijf porties over vijf beelden (29 per beeld) in plaats van alle 145 tegelijk.
- Geen `will-change` op de 145 deeltjes en geen `drop-shadow` per hartje of confettistuk (1 px, 27 % bruin, nauwelijks zichtbaar): dat maakte 145
  gefilterde lagen en kostte 45 fps in plaats van 60. De fonkelende lichtpuntjes houden hun gloed.
- De dansvideo wordt achter de gesloten deuren kort opgewarmd (spelen en direct pauzeren) zodat de start op 3,05 s geen haperend beeld kost;
  `preload="metadata"` tot de opening begint, dan `auto`. De poster staat vooraf in de `<head>` (`preload`).
- Hartjes en confetti vallen niet: ze krijgen alleen een omhoog en naar buiten gerichte verplaatsing (`--dy` en `--endy` zijn negatief) en
  vervagen. Er zijn geen vallende sterren; de lichtpuntjes fonkelen op hun plek. `tests/test_gouden_avond.py` bewaakt dit.

## De uitnodiging eronder: een nacht in de balzaal (4 oktober 2026, op verzoek "uitbundiger en spectaculairder")

De opening en de scène zelf zijn niet veranderd. Wel is de rest van de pagina veel rijker dan de eerste (gedeelde) Balzaal-opmaak:

- **Ritme:** donkere "nacht"-banden (espresso met goud) wisselen af met ivoren banden en één gouden band voor het aftellen. Op de nachtbanden staan
  de kroonluchter, de boog en de vloer uit de scène als donkere, zachtjes meebewegende achtergrond (GSAP ScrollTrigger, ±6 %, alleen met beweging).
- **Goudfolie:** koppen, de datum en de tijden zijn goudfolie met een langzame glans (alleen in beeld); een langzaam draaiende stralenkrans (150 s per
  rondje) achter de intro, de datum, het aftellen, het aanmelden en de afsluiting. Beide pauzeren buiten beeld (`bc-zichtbaar`, IntersectionObserver).
- **De datum:** een gouden boogvenster met de zonsondergang uit de scène en een enorm cijfer van goudfolie.
- **Welkom:** de foto in een boog met een dubbel gouden lijstje en hoekornamenten (op een breed scherm naast de tekst).
- **Programma:** een gouden lijn met gloeiende ruiten, grote tijden; op een breed scherm links en rechts om en om.
- **Aftellen:** ronde, donkere medaillons met een gouden rand op een gouden band met stralen.
- **Aanmelden:** de bestaande aanmeldkaart (`partials/rsvp.html`, ongewijzigd) in een ivoren kaart met gouden hoeken, op de donkere vloer.
- **Momenten:** vier foto's in gouden bogen, om en om verschoven.
- **Kop op een breed scherm:** een waas in de kleuren van de scène, een gloed en stralenkrans achter de deuren, en de twee namen groot naast de deuren zodra ze
  in beeld komen (vanaf 1100 px breed; op een telefoon staan de namen in de scène).
- Alle teksten komen uit de studiogegevens; er is niets vast in de afbeeldingen.

## Overslaan, opnieuw beleven, toegankelijkheid

- **Opening overslaan** (rechtsboven, 44 px hoog, ook `data-open` zoals bij de andere openingen): stopt alle timers, het feest en de video, zet de
  scène op het eindbeeld (poster, namen, datum) en zet de scroll en de inhoud vrij. Focus gaat naar *Bekijk de uitnodiging*. Er is een
  `role="status"`-melding ("De sleutel draait in het slot", "De deuren gaan open", "Opening overgeslagen. De uitnodiging is geopend…").
- Tijdens de opening is de pagina niet scrolbaar en de inhoud eronder `inert`; daarna komt dat vrij. De sleutel is een echte knop (Tab, Enter, spatie).
- **Opnieuw beleven** zet de scène helemaal terug (deuren dicht, deeltjes weg, video op 0, scroll vergrendeld). Als de video niet automatisch mocht
  starten, of na overslaan, of bij 'minder beweging', staat op die plek **Speel de scène af ▷**.
- **Minder beweging** (of de knop Beweging stilgezet, ook tijdens de opening): geen deuren, sleutel, deeltjes of fonkelende lichtpuntjes; direct de
  open scène met poster en een knop om de dans af te spelen. De video speelt nooit vanzelf opnieuw af (`ended` pauzeert) en heeft `muted playsinline`.
- Dezelfde sessie, een aanmeldlink (`#aanmelden`), de editor (`data-live`) en de kleine kaart op de bedankpagina (`inv-embed`) tonen direct de open scène.
- Staat de opening uit (Studio, stap Stijl: *Openingsanimatie tonen*), dan rendert de server de open scène zonder sleutel.
- Zonder JavaScript staat de open scène er ook (poster, namen, datum, alle inhoud).
- Het kroontje boven de lijst toont de initialen van het paar (niet de V van het logo; het logo blijft ongewijzigd, zie CLAUDE.md regel 12). De tekst
  "VAYLIDE" boven de deuren uit het prototype is weggelaten om dezelfde reden.

## Leesbaarheid

Tekst over de video: de verloop-laag onder de tekst is donkerder dan in het prototype (0 → 74 % → 86 %), zodat ook de bovenste regel ("Wij gaan
trouwen") boven 5,9 : 1 blijft tegen de lichtste pixel erachter (gemeten op poster en video, 360 / 390 / 1366 px; `e2e/gouden_avond_contrast.cjs`).
Het kroontje is lichter met donkere tekst (6 : 1). `e2e/toegankelijkheid.cjs` (axe en contrast) vindt niets, ook niet in de donkere en gouden banden (lichte tekst op
#1D140A ≥ 7 : 1, donkere tekst op de gouden band ≥ 7 : 1, getest in `tests/test_gouden_avond.py`). Achter de video staat een donkere vervangkleur (#3b2c16);
de pixelmeting hierboven is de echte meting over de video.

## Prijs en bestellen

Een special heeft een eigen meerprijs (Beheer → Prijzen, functie `special`, code `special-gouden-avond`). **Die is er niet**: tot de eigenaar
hem instelt is het ontwerp niet te bestellen (de bestelpagina zegt dat eerlijk). Lokaal is voor de klantreis tijdelijk een testbedrag van € 1 gebruikt
en daarna verwijderd.

## Getest

Zie `docs/CONTROLES.md` onder "Gouden Avond". Scripts: `e2e/gouden_avond.cjs` (schermafbeeldingen per stap), `e2e/gouden_avond_functies.cjs`
(gedrag, 31 controles), `e2e/gouden_avond_fps.cjs` (beeldsnelheid, `CPU=4` voor een zwakke telefoon), `e2e/gouden_avond_flits.cjs` (geen zwarte
flits), `e2e/gouden_avond_contrast.cjs` en `e2e/klantreis.cjs` met `KLANTREIS_ONTWERP=gouden-avond` (en een tijdelijke special-prijs).

## Een v2 maken

Wijzig een uitgebrachte versie niet. Verlengen of vervangen van de video, andere tijden of kleuren: `designs/gouden-avond/v2/`.

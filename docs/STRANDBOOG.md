# Strandboog (ontwerp `strandboog`)

Een nieuw, zelfstandig bruiloftsontwerp (ook voor verloving) onder **Specials**, naast Balzaal en Gouden Avond (beide ongewijzigd). Je ziet eerst een
gesloten ringdoosje op een poster. De gast tikt op **Tik om het doosje te openen**: het doosje gaat open met twee ringen, daarna staat er een bloemenboog
aan zee in het avondlicht, een bloemenmeisje strooit blaadjes en duiven vliegen op naar de zon. Als de boog weer in beeld is (13,7 s) verschijnen de
namen en de datum en komt de pagina vrij; daarna loopt de uitnodiging door met de gedeelde onderdelen (aftellen, programma, locatie, dresscode,
aanmelden). Herkomst: de wenskaartvideo uit `Downloads\Maak-een-romantische-luxe-trouwvideo-vo.mp4` (gegenereerd, fictieve personen), bewerkt zoals hieronder.

Status: **op staging (10 oktober 2026), niet op productie.** Er is geen prijs; een special zonder meerprijs is niet te bestellen (zie `catalog/specials.py`).

## Bestanden

| Bestand | Wat |
|---|---|
| `designs/strandboog/v1/manifest.json` | special, palet `zonsondergang`, effecten (sfeer zonnestofjes, geen knal, viering bloemblaadjes), onderdelen |
| `designs/strandboog/v1/invitation.html` | de kop (poster, film, eindbeeld, namen, knoppen) en daaronder de uitnodiging; alle teksten komen uit de studiogegevens (automatisch ge-escaped) |
| `designs/strandboog/v1/style.css` | kop en de bandenopmaak (zand, avond, perzik) |
| `designs/strandboog/v1/strandboog.js` | de opening (tik, film, namen op 13,7 s, overslaan, opnieuw beleven), achtergrondfoto's die iets meebewegen |
| `designs/strandboog/v1/media/strandboog.mp4` | de film, 720 × 1280, 18,04 s, 24 fps, zonder geluid, ±2 MB (H.264, `+faststart`) |
| `designs/strandboog/v1/media/poster.jpg`, `poster-eind.jpg` | eerste beeld (gesloten doosje) en laatste beeld (boog met de V) |
| `designs/strandboog/v1/media/zee.webp`, `duif.webp`, `bloemen.webp` | uitsneden uit beelden van dezelfde film, als achtergrond van de banden (geen nieuwe afbeeldingen) |
| `static/img/designs/strandboog.webp` | kaartbeeld voor het overzicht van de collectie (uitsnede van het eindbeeld, 800 × 1000) |
| `invitations/demo.py` | gelegenheid en voorbeeldfoto's voor het voorbeeld |
| `tests/test_strandboog.py` | regressietests; `tests/test_effects.py` telt nu 48 ontwerpen |
| `e2e/strandboog_functies.cjs` | gedrag en breedtes in een echte browser (zie "Controles") |

## Presentatie van de opening (rand tot rand, 9 oktober 2026)

De openingsscène is **full-bleed**: de kop vult de viewport (`100vw × 100svh`, onder de eventuele voorbeeldbalk), de film en de poster zijn `object-fit: cover` met `object-position: 50% 44%`
(op een breed scherm 50% 36%, zodat doosje en boog in het midden blijven), zonder kader, afgeronde randen, marge of kaartvorm. De knop *Tik om het doosje te openen* is een subtiele, doorschijnende
overlay op de poster; namen, datum en knoppen staan over het beeld met alleen een zachte schaduw onder de tekst en een lichte schaduw bovenaan (geen laag over de hele film). De onderrand van de
kop loopt zacht over in de kleur van de eerste band zodra de pagina vrijkomt. De oude kaartversiering (rand, zon, namen naast de boog) is niet meer zichtbaar. Film, timing (13,7 s) en inhoud zijn niet veranderd.
Het stijlbestand van vóór deze wijziging staat niet in Git (alles is nog niet gecommit).

## De film en wat eraan bewerkt is

De bron had in beeld een **tekst in de scène** ("VA V LUE", met een grote V) op het deksel van het doosje en in de bloemenboog. Op verzoek van de eigenaar
(9 oktober 2026) is alleen de **V** laten staan en zijn "VA" en "LUE" per beeld weggehaald (beeldvolgen op de V, het omringende beeld opgevuld, ook in de
doorlopende overgangen; zie "Bekende kleine punten"). De bewerkte film is niet in Git; in Git staat alleen de webversie.

**De V in de film is een gewone schreefletter in de scène, niet het VAYLIDE-logo** en niet de V uit het logo. Het logo blijft ongewijzigd (CLAUDE.md regel 12);
het logo of de V uit het logo is nergens in dit ontwerp gebruikt of hertekend. Beslis zelf of een losse V in de film acceptabel is of dat een klant er
liever de eigen voorletter zou zien; dat vraagt een nieuwe film.

## In de collectie

Op de staging-lijn staat Strandboog in groep A en onder `SPECIALS` in `catalog/collectie.py`, met `sort_order` 12 (uniek) en `added_at` in het manifest; `tests/test_collectie.py` en `tests/test_effects.py` tellen nu 51 ontwerpen (A 16).

## Hoe de opening werkt

Opening, kop en namen zijn **één scène in de kop** (geen openingsscherm van `invite.js`): de poster van het doosje is het eerste beeld van dezelfde film
die daarna de kop is. Het script (`strandboog.js`) zet klassen op `.sb-hero`:

| Klas | Betekenis |
|---|---|
| `sb-gate` | poster met de knop; de pagina is vergrendeld (`html.sb-bezig`, inhoud `inert`) |
| `sb-speelt` | de film speelt (na een tik); `sb-tekst` komt erbij zodra de film op 13,7 s is: namen zichtbaar en de pagina komt vrij |
| `sb-klaar` | eindbeeld (`poster-eind.jpg`, gelijk aan het laatste beeld van de film) met de namen; knop *Opnieuw beleven* of *Speel de scène af* |

- De film start **alleen na een tik** (`muted playsinline`, geen `autoplay`, geen `loop`) en speelt nooit vanzelf opnieuw. Als de browser het afspelen weigert of de film niet laadt, gaat het script
  direct naar het eindbeeld (de pagina blijft bruikbaar).
- **Opening overslaan** (rechtsboven, 44 px, ook `data-open`): zet de film stil op het begin en toont het eindbeeld; focus gaat naar *Bekijk de uitnodiging*.
- **Minder beweging**, de knop *Beweging* stilgezet (ook tijdens de opening), een aanmeldlink (`#aanmelden`), de editor (`data-live`), de kleine kaart op de bedankpagina (`inv-embed`) en een
  tweede bezoek in dezelfde sessie tonen direct het eindbeeld met de namen. Zonder JavaScript staat het eindbeeld er ook.
- Staat de opening uit (Studio, stap Stijl: *Openingsanimatie tonen*), dan rendert de server direct het eindbeeld zonder knop.
- Alles wat beweegt staat onder `.fx-motion` of is alleen een lichte gloed van de knop; bij `prefers-reduced-motion` zijn alle overgangen en animaties uit.

## De uitnodiging eronder

Zandbanden (ivoor en licht perzik), donkere avondbanden met foto's uit dezelfde scène (duif, zee, bloemen; donker gemaakt voor leesbaarheid, ze schuiven met GSAP ±6 % mee als er beweging is),
een perzikkleurige aftelband met ronde medaillons, een boogvenster voor de datum, ringen als scheidingsteken, de gedeelde aanmeldkaart (`partials/rsvp.html`, ongewijzigd) in een ivoren kaart
op de avondband. Lettertypen: Cormorant Garamond (koppen en tekst), DM Sans (kleine letters) — de bestaande bestanden uit `static/fonts/`.

## Controles (echt uitgevoerd op 9 oktober 2026)

- `manage.py test tests.test_strandboog tests.test_effects tests.test_specials tests.test_atelier tests.test_gouden_avond`: slaagt (zie `docs/CONTROLES.md` voor het totaal).
- `e2e/toegankelijkheid.cjs ... strandboog`: axe-core (WCAG 2.0/2.1 A en AA) en contrast, dicht en geopend: geen bevindingen.
- `e2e/strandboog_functies.cjs` in Chrome 22 van 22 controles: eerste bezoek vergrendeld, tikken start de film, namen op 13,7 s en pagina vrij, einde zonder herhaling, opnieuw beleven, overslaan met focus, toetsenbord, terugkerende bezoeker, aanmeldlink, minder beweging, geweigerde `play()`, zonder JavaScript, 360/390/768/1366 px zonder horizontale scroll.
- Handmatig in de browser: poster, film (met versnelde weergave tot het einde), namen en alle banden op 375 en 1366 px bekeken.

## Bekende kleine punten

- De film is gegenereerd: personen en dieren zijn fictief; het voorbeeld zegt dat (aria-label van de video). Er is geen geluid.
- Rond 13,9–14,2 s (de overgang van de duiven naar de boog) is een stukje vleugel in de film iets zachter door het bewerken; op het deksel van het doosje is de rand van het deksel op
  twee of drie beeldjes iets onregelmatig. Dat staat in de film zelf, niet in de code.
- De dev-server (`runserver`) ondersteunt geen *Range*-verzoeken: terugspoelen in de film werkt daar alleen naar het begin. Het script spoelt alleen terug naar 0.
- Kaartbeeld voor het overzicht: een uitsnede van het eindbeeld; `e2e/make_design_images.cjs` kan later een gelijkwaardig beeld maken.

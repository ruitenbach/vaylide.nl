# Homepage: 3D-kaartencarrousel

Stand: gebouwd op branch `claude/homepage-carrousel` (vanaf productie, commit 6733220). Niet gemerged, niet uitgerold, niets geactiveerd.

## Wat het is
Een draaibare 3D-carrousel met uitgelichte Luxe- en Special-ontwerpen uit alle gelegenheden, voor de bestaande homepage-achtergrond (inclusief de fonkelingen). Kop, knoppen, kleuren en lettertypen zijn ongewijzigd.

- Een klik op een zijkaart selecteert die kaart. Een klik op de middelste kaart of op "Bekijk dit ontwerp" opent de bestaande ontwerppagina `/ontwerpen/<slug>/` met de werkende voorvertoning en de bestelknop.
- Slepen met de muis, vegen met de vinger (verticaal scrollen blijft gewoon), pijltjestoetsen, Home en End, en vorige/volgende-knoppen.
- Zonder JavaScript of zonder 3D: een horizontale rij kaarten met scroll-snap.
- 'Minder beweging': geen zweven en geen aanzet-beweging; alleen de tekst "Veeg voor meer ontwerpen".

## Beheren
Beheer, Ontwerpen, een ontwerp bewerken: vink "uitlichten op homepage" aan en geef een volgorde (laag eerst; de eerste kaart staat in het midden). De ontwerpenlijst heeft een kolom "Homepage" en meldt of de carrousel aanstaat.

Een ontwerp verschijnt alleen als het actief is, een huidige versie heeft en Luxe of Special is. Een uitgelicht ontwerp dat niet geschikt is wordt overgeslagen en Beheer waarschuwt daarvoor. Bij minder dan vijf geschikte ontwerpen blijft de huidige homepage (envelop) staan. Er is geen bovengrens.

## Database
Migratie `catalog/0009_homepage_uitgelicht`: alleen twee nieuwe kolommen op `Template` (`homepage_uitgelicht`, standaard onwaar; `homepage_volgorde`, standaard 100). Bestaande ontwerpgegevens veranderen niet (getest op een kopie met 63 ontwerpen en 64 versies).

Terugdraaien: draai de migratie terug (`migrate catalog 0008`) tegelijk met het terugzetten van de code, niet los van elkaar.

## Voorstel eerste selectie (niets geactiveerd)
Volgorde 10 tot 120, gemengd over gelegenheden en licht/donker:
1. Rosé Royale (rose-royale), 2. Winterlicht (winterlicht), 3. Zwanenhart (zwanenhart), 4. Puur moment (puur-moment), 5. Aurora Nocturne (aurora-nocturne), 6. Liefde op papier (liefde-op-papier), 7. Kerstbol (kerstbol), 8. Balzaal (balzaal), 9. Avondgoud (avondgoud), 10. Strandboog (strandboog), 11. Midnight Émeraude (midnight-emeraude), 12. Gouden Avond (gouden-avond).
Controleer bij het activeren eerst in Beheer dat ze op de doelomgeving Luxe of Special zijn en actief.

## Staging
Staging (`vaylide-staging`) volgt nu `claude/envelop-collectie`. Om de carrousel daar te zien moet in Render de branch naar `claude/homepage-carrousel` of er moet een aparte staging-dienst komen. Na het uitrollen draait `migrate` automatisch; daarna de ontwerpen uitlichten in Beheer. Dit is nog niet gedaan.

## Nog te doen vóór productie
Controle op een echte iPhone (Safari) en een Android-telefoon. Chromium-metingen zijn geen echt apparaat.

## Kop en indeling (21 oktober 2026, akkoord van de eigenaar)
- Kop: "Bijzondere momenten verdienen een *bijzondere* uitnodiging." Alleen "bijzondere" staat in Pinyon Script (`static/fonts/pinyon-script-latin-400-normal.woff2`, OFL-licentie ernaast), op een eigen regel in het warme goud van de huisstijl; de rest in de serif. Pinyon Script is een tijdelijk alternatief voor Cochocib Script Latin Pro: dat lettertype ontbreekt en er is geen weblicentiebewijs. Bij levering van de webfont en licentie wordt alleen het lettertype vervangen.
- Boven de kaarten staat één knop, "Maak jouw uitnodiging". "Bekijk dit ontwerp" en "Ontdek de collectie" staan bij de geselecteerde kaart.
- Vanaf 1200 px breed staat links de kop met knop en rechts de carrousel (grid in `static/css/vierlief.css`); daaronder staat de tekst boven de kaarten.
- Teller "01 / 12" (`.cv__teller`) in plaats van bolletjes; de pijlen, toetsen en het vegen blijven de bediening. De kaartmaat en spreiding in `static/js/carrousel.js` zijn op deze breedte afgestemd.
- Vijf voordelen onder de carrousel, de derde is "Eigen foto's en muziek toevoegen".

## Voordelenrij (22 oktober 2026)
Op desktop (vanaf 1200 px) staat de rij met vijf voordelen over de volledige hero-breedte (`grid-column: 1 / -1`) en is als geheel gecentreerd, niet meer onder het linker tekstblok. Gecontroleerd op 390, 768, 1200, 1366 en 1920 px: geen horizontale scroll, elke regel exact gecentreerd.

## Krachtiger linker kop (22 oktober 2026)
Tekst ongewijzigd. Desktop: kolom `clamp(24rem, 33vw, 30rem)` (was 21rem), kop `clamp(2.3rem, 3.1vw, 3.1rem)` (was ~2.1rem), "bijzondere" 1.7em in Pinyon Script. Mobiel: kop `clamp(1.95rem, 8.9vw, 2.3rem)`, de regel "Bijzondere momenten" blijft op één regel (gecontroleerd op 360 en 390 px). Entree (`hero-kop-in`, alleen zonder 'minder beweging'): fade, 1,1 rem omhoog en scale .985→1; eyebrow, kop, "bijzondere" en knop komen na elkaar (0,1 / 0,3 / 0,75 / 1,05 s).

## Mobiele bediening (22 oktober 2026)
Tot 767 px staat de bediening onder de kaarten in een vast raster (breedte max. 19 rem, gecentreerd): naam, ondertitel, hint, 'Bekijk dit ontwerp' (46 px), 'Ontdek de collectie' (44 px), en op één regel de pijltjes (44 px) met de teller, daaronder 'Maak jouw uitnodiging' op dezelfde breedte. Alleen CSS (`.cv__acties` is `display: contents`); de markup, desktop en de 3D-kaarten zijn niet gewijzigd. De teller telt het werkelijke aantal kaarten (`N`). Gecontroleerd op 360, 390 en 430 px: geen horizontale scroll, pijltjes wisselen de kaart en teller, de links gaan naar het ontwerp, de collectie en `/maken/`.

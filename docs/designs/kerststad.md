# Kerststad

> Ingevuld op 7 oktober 2026 op basis van de opdracht van de eigenaar en de definitief goedgekeurde video. Wat niet is aangeleverd staat als "nog niet bepaald"; er is niets bijverzonnen.

## 1. Naam

Kerststad

> Werknaam, afgeleid van de opdracht ("kerststad-video"). De eigenaar kan hem nog wijzigen; dat is een aanpassing van `name` in het manifest.

## 2. Slug

`kerststad`   (de map `designs/kerststad/v1/`, de demo-URL `/voorbeeld/kerststad/?gelegenheid=kerst`)

## 3. Categorie

Special · gelegenheid: kerst · groep A van de collectie (`sort_order` 11). Er is **geen meerprijs bedacht**: zonder optie `special-kerststad` in Beheer → Prijzen geldt de pakketprijs (de bestaande Special-terugval). Als **Wenskaart** geldt de bestaande speciale prijs van **€ 24,95 incl. btw** (`catalog/wenskaart.py`).

## 4. Status

**Lokaal klaar, ter beoordeling (7 oktober 2026).** Niet gecommit, niet gepusht, niet op staging, niet live. Geen production-deploy zonder uitdrukkelijk akkoord.

## 5. Concept / verhaal

Een levende peperkoek-kerststad. Je begint extreem dichtbij op de ronde gouden badge met de VAYLIDE-V op een peperkoeken brug; de camera trekt terug langs de peperkoekfiguurtjes naar een besneeuwd dorp met kerk, verlichte kerstboom, marktkraampjes en schaatsers, tot het nacht is. De kaart eronder blijft in die wereld: nachtblauw, warm lantaarnlicht, peperkoek, glazuur, rood-witte zuurstokken en goud.

## 6. Opening / animatie

1. **Gesloten stand**: het eerste beeld van de video (de badge, extreem ingezoomd). De V is het klikpunt: een zachte lichtring met twee langzame golven vanuit de V en de tekst "TIK OP DE V OM TE OPENEN". Geen aparte envelop (`envelope_mode: built_in`).
2. **Eén tik** speelt de volledige video één keer, van 0 s tot het einde (20,04 s). De gast hoeft nergens meer op te klikken; "Opening overslaan" staat rechtsboven.
3. **Levende eindloop (aparte clip, 9 oktober 2026)**: de laatste scène staat ook als losse, kleine clip (`loop.mp4` mobiel 1,1 MB, `loop-desktop.mp4` 3,8 MB; 3,54 s = de film vanaf **16,5 s** tot het einde, zelfde resolutie, fps en CRF als de opening, eerste beeld een keyframe, geen geluid, faststart). Bij 16,5 s gaat de opening in 0,8 s over in clip A (dezelfde beelden, dus zonder zichtbare naad); de opening eronder wordt daarna stilgezet. Daarna draaien twee exemplaren van de clip (A en B): een kwart seconde voor het eind van het ene komt het andere, dat al op zijn eerste beeld klaarstaat, met een kruisverloop van 0,8 s eroverheen (het binnenkomende exemplaar ligt boven het huidige, dus er is geen doorzichtig tussenmoment); het weggevallen exemplaar springt achter de schermen terug naar het begin. **Er wordt dan niet meer in de grote openingsvideo teruggesprongen** (dat gaf een haperingen van 0,5 tot 1 s). Een wissel komt elke 2,6 s. De groet verschijnt als de film uit is (clip A bij zijn eind).
   **Terugval (10 oktober 2026):** de clips zijn een extraatje bovenop de oude, op staging bewezen werking (tik op de V, opening, eindloop door te springen naar `lusStart`). Alle loopcode loopt via `veilig()` en start met `play()`; lukt het starten van clip A niet binnen 4 s (te traag, afgebroken, niet toegestaan, niet ondersteund), dan doet de kaart gewoon wat hij deed vóór de clips: de opening speelt uit en de eindloop is de sprong terug met een kruisverloop (`spring()`), bij overslaan en een tweede bezoek na het laden van de grote video. De eerste versie (`306336c`) wachtte op een `canplay` van clips die in sommige browsers (iOS) pas na `play()` laden, en riep de loopcode onbeschermd aan in `speel()`.
4. **Overslaan, tweede bezoek en opnieuw beleven**: overslaan en een tweede bezoek laden alleen de kleine clip (de grote opening wordt niet meer binnengehaald); het eindbeeld lost op in clip A. "Opnieuw beleven" stopt de clips en zet de kaart terug in de gesloten stand.
5. **Nooit opnieuw vanzelf**: de opening start niet meer vanzelf. Bij een tweede bezoek in dezelfde sessie (zelfde sleutel als `invite.js`) is de opening overgeslagen en loopt alleen de eindloop. "Opnieuw beleven" zet de kaart terug in de gesloten stand; de gast moet opnieuw tikken.
6. **Rustig**: bij 'minder beweging' of stilgezette beweging, in de Studio (behalve bij de stappen Stijl en Envelop) en zonder JavaScript staat het eindbeeld met de groet; een knop speelt de opening eenmalig af, zonder lus. De lus pauzeert buiten beeld en in een verborgen tabblad. Kan de server geen Range-verzoeken (video niet te "seeken"), dan valt de kaart terug op het eindbeeld in plaats van opnieuw bij 0 s te beginnen.

### Waarom de loop bij 16,5 s begint

De camera blijft tot het einde langzaam omhoog en naar achteren bewegen, dus het laatste beeld lijkt nooit precies op het eerste van de clip; het kruisverloop van 0,8 s verbergt die sprong. Gemeten (gemiddeld verschil per beeldpunt, 0–255, tussen de laatste 0,8 s van de clip en de eerste 0,8 s): liggend 20,4 bij een start van 16,0 s, 19,3 bij 16,5 s, 17,7 bij 17,0 s, 11,9 bij 18,0 s; staand 24,7, 22,8, 21,1 en 15,2. Later beginnen geeft een rustiger overgang maar een kortere clip (een wissel elke 1,25 s bij 18,0 s); 16,5 s is het compromis (clip van 3,54 s, een wissel elke 2,6 s). `--loop-start` in `tools/kerststad/maak_media.py` en `data-ks-lus` / `data-ks-lus-desktop` in `invitation.html` moeten gelijk blijven (de tests bewaken dat).

### Muziek (9 oktober 2026)

Kerststad heeft een eigen track, **"O dennenboom (avondlicht)"** (`media/muziek.mp3`, 87,3 s, 1,3 MB, stereo): een eigen VAYLIDE-arrangement van de publieke-domeinmelodie "O Tannenbaum" (traditioneel, tekst Ernst Anschütz 1824; noten uit de publieke notatie op Wikipedia). Alles is door `tools/kerststad/maak_muziek.py` gesynthetiseerd: geen opname, geen sample, geen ander arrangement, geen zang. G-groot, 3/4, 66 BPM, 32 maten in vier rondes van "A B": intiem (celesta, zachte piano) → het dorp (strijkers en cello erbij) → de stad ontwaakt (vollere strijkers, celesta-glans, zachte belletjes) → de bruisende kerstnacht (rijkste moment) en daarna weer tot rust. De lus is circulair: de galm loopt rond het eind naar het begin, de laatste maat (G) is de eerste, en de opmaat van de melodie staat aan het eind van de lus. Gemeten in Chrome: drie opeenvolgende naden zonder stilte of klik. Volume 0,45 met een zachte inzet van 2 s; nooit autoplay, alleen via de bestaande muziekknop. (De eerdere eigen compositie "Kerststad (avondlicht)" van 8 oktober is vervangen.)

Koppeling: in het manifest van een ontwerp staat `"music": {"src", "title", "volume"}`. Ontwerpen zonder die sleutel veranderen niet. De track speelt in het voorbeeld van het ontwerp en in een uitnodiging waarvan de klant "muziek van het ontwerp" koos (`content.music.ontwerp`); eigen muziek van de klant gaat altijd voor. De Studio heeft die keuze nog niet (zie `docs/MUZIEK.md`).

## 7. Pagina na de opening

Alleen wat de klant heeft ingevuld (bestaande Studio-velden, niets verzonnen):

- **Kerstgroet**: een peperkoekplaat met glazuurrand, de gouden V-badge uit de video, de foto in een ring van zuurstok, de persoonlijke tekst.
- **Ons jaar** (verhaal), **Momenten** (galerij als peperkoekjes met een lintje aan een draad).
- Alleen bij een **kerstdiner (een datum)**: datum als gouden munt (zoals de badge), programma op een zuurstok met peperkoekmannetjes, aftellen als verlichte ramen, locatie, aanmelden op een glazuurwit kaartje met een rand van zuurstok.
- Dresscode (snoepjes), "Goed om te weten", contact: alleen als ingevuld.
- Afsluiting met naam in goudfolie, de afsluitende tekst en deelknoppen. Lichtsnoeren, sneeuw (gedeeld effect `sneeuw`) en achtergronden uit dezelfde video verbinden de banden.
- Als **Wenskaart** (`soort = "wenskaart"`): alleen kop, groet en afsluiting; geen datum, programma, locatie, aanmelden, verhaal, galerij of muziek.

## 8. Assets en waar ze staan

| Asset | Pad in de repository | Herkomst | Opmerking |
|---|---|---|---|
| Video (staand) | `designs/kerststad/v1/media/opening.mp4` | goedgekeurde 9:16-video, web-klaar gemaakt | H.264 8-bit, 720×1280, 24 fps, 20,04 s, ±5,4 MB, zonder geluid, sleutelframe op 16,0 s; niet visueel bewerkt; speelt alleen nog tot de overgang naar de loopclip |
| Video (liggend) | `designs/kerststad/v1/media/opening-desktop.mp4` | goedgekeurde 16:9-video (`kerststad-desktop-16x9.mp4.mp4`), web-klaar gemaakt | H.264 High, yuv420p, 1920×1080 (bronresolutie), 24 fps, 20,04 s, CRF 19, faststart, ±17,7 MB, zonder geluid, sleutelframe op 16,0 s; geen extra filters of tweede resize |
| Loopclips | `.../media/loop.mp4`, `loop-desktop.mp4` | de laatste scène (vanaf 16,5 s) uit dezelfde bronnen | H.264 yuv420p, 3,54 s, 24 fps, keyframe op het eerste beeld, faststart, geen geluid; 720×1280 CRF 23 (1,1 MB) en 1920×1080 CRF 19 (3,8 MB) |
| Poster en eindbeeld (liggend) | `.../media/poster-desktop.webp`, `eind-desktop.webp` | eerste en laatste beeld van de liggende video | 1920×1080 |
| Poster | `.../media/poster.webp` | eerste beeld van de video | de gesloten stand en het voorbeeldframe |
| Eindbeeld | `.../media/eind.webp` | laatste beeld van de video | rustige stand en terugval |
| Badge | `.../media/badge.webp` | uitsnede van het eerste beeld | de officiële VAYLIDE-V in de ronde badge |
| Achtergronden | `.../media/dorp-kerk.webp`, `dorp-ijs.webp`, `dorp-brug.webp` | uitsneden uit latere beelden | donker gemaakt achter de banden |
| Kaartbeeld | `static/img/designs/kerststad.webp` | uitsnede van het laatste beeld (4:5) | ontwerpkaart in de collectie |

**Niet in Git**: de bronnen: de staande video van 71 MB (HEVC 10-bit, 1080×1920) en de liggende van 78 MB (HEVC 10-bit, 1920×1080). Hij staat bij de eigenaar (`Create-one-continuous-premium-vertical-C.mp4`). `tools/kerststad/maak_media.py` maakt alle bovenstaande bestanden uit die bron.

## 9. Externe AI/video-output

De video is door de eigenaar buiten dit project gegenereerd en definitief goedgekeurd; prompt en tool zijn nog niet bepaald (aan te leveren voor `tools/design-references/kerststad/`). De video wordt **niet opnieuw gegenereerd** en niet visueel aangepast; alleen de technische web-encode is gedaan.

## 10. Technische bouwinstructies

- Bestanden: `manifest.json`, `invitation.html`, `_lichtjes.html`, `style.css`, `kerststad.js` in `designs/kerststad/v1/`; registratie met `manage.py sync_designs` (gebeurt ook bij `migrate`).
- Eén `<video>` (muted, playsinline, `preload="metadata"`, geen `controls`, `loop` of `autoplay`), één canvas voor het kruisverloop en één voor de zijgloed op een breed scherm. `data-ks-lus="16"` op de video is de enige plek voor `LUS_START`.
- Media-bescherming: geen eigen werk nodig; `media-bescherming.js` en de hotlinkblokkade dekken `/static/designs/` en de video-attributen. De canvassen hebben `pointer-events: none`, dus rechtsklik raakt altijd de beschermde video.
- CSP: geen inline `<style>` of `<script>`; alleen stijlattributen met variabelen. Hostingvereiste: Range-verzoeken voor statische bestanden (WhiteNoise doet dat; `runserver` zonder `--nostatic` niet).
- Toegankelijkheid: knop met `aria-label`, `role="status"`, focus naar "Naar de kaart" na de opening, de inhoud is `inert` zolang de opening speelt.

## 11. Wat al afgerond is

- 7 oktober 2026: media, ontwerp, script, opmaak, collectie (A, special), tests (`tests/test_kerststad.py`), lokale controle op 390 en 1366 px.

## 12. Wat nog moet gebeuren

- [ ] Beoordeling door de eigenaar (kaart en lus).
- [ ] Naam bevestigen (Kerststad).
- [ ] Prompt/tool van de video vastleggen onder `tools/design-references/kerststad/`.

## 13. Besluiten die niet opnieuw ter discussie hoeven

- De video is definitief en wordt niet aangepast of opnieuw gegenereerd (eigenaar, 6 oktober 2026).
- De V in de badge is het klikpunt; geen aparte envelop (eigenaar, 6 oktober 2026).
- Eén keer volledig afspelen, daarna een levende eindloop; de opening start nooit meer vanzelf (eigenaar, 6 oktober 2026).
- Special; als Wenskaart € 24,95 incl. btw (eigenaar, 6 oktober 2026).

## 14. Laatste relevante commit

Nog niet gecommit.

## 15. Volgende stap

De eigenaar bekijkt de kaart lokaal en geeft akkoord of wijzigingen; daarna één commit en staging.

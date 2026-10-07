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
3. **Levende eindloop**: na het einde loopt de laatste scène door van **`LUS_START` = 16,0 s** tot het einde en weer terug, zolang de kaart in beeld is. Sneeuw, twinkelende lichtjes, schaatsers en markt blijven zo bewegen. De groet verschijnt na het einde van de video.
4. **De sprong aan het eind van de lus** is een zacht kruisverloop van 1,4 s: het laatste beeld wordt als stilstaand beeld op een canvas gezet, de video springt naar 16,0 s en dat beeld lost op. De video zelf wordt niet bewerkt.
5. **Nooit opnieuw vanzelf**: de opening start niet meer vanzelf. Bij een tweede bezoek in dezelfde sessie (zelfde sleutel als `invite.js`) is de opening overgeslagen en loopt alleen de eindloop. "Opnieuw beleven" zet de kaart terug in de gesloten stand; de gast moet opnieuw tikken.
6. **Rustig**: bij 'minder beweging' of stilgezette beweging, in de Studio (behalve bij de stappen Stijl en Envelop) en zonder JavaScript staat het eindbeeld met de groet; een knop speelt de opening eenmalig af, zonder lus. De lus pauzeert buiten beeld en in een verborgen tabblad. Kan de server geen Range-verzoeken (video niet te "seeken"), dan valt de kaart terug op het eindbeeld in plaats van opnieuw bij 0 s te beginnen.

### Waarom `LUS_START` 16,0 s

De camera blijft tot het einde langzaam omhoog en naar achteren bewegen; het laatste beeld lijkt dus nooit precies op een eerder beeld. Gemeten (gemiddeld verschil per beeldpunt tussen het laatste beeld en een kandidaat-startpunt, 0–255): 15 s = 34, 16 s = 32, 17 s = 29, 18 s = 25,5, 19 s = 18. Een correctie van de beeldkadrering (homografie) brengt het verschil bij 16 s van 34 naar 19, maar de scène heeft echte parallax, dus dat is niet gebruikt. 16,0 s geeft een lus van ongeveer 4 s ("ongeveer de laatste vijf seconden") met een zichtbaar maar zacht kruisverloop. Een later startpunt (bijvoorbeeld 17,5 s) maakt de naad minder zichtbaar maar de lus korter (2,5 s). In de video staat op 16,0 s een sleutelframe, zodat de sprong exact is.

### Liggende en staande video (8 oktober 2026)

Brede schermen (verhouding vanaf 6:5) krijgen de echte 16:9-video, telefoons en staande tablets de 9:16-video; het script kiest de bron vóór het afspelen en wisselt niet midden in een opening. Beide
video's zijn de goedgekeurde beelden zelf, zonder kunstmatige lagen erbovenop. Een eerder geprobeerde overlay (een VAYLIDE-V op de gevel en zelfgetekende bewegende figuurtjes, 7 en 8 oktober) is
op verzoek van de eigenaar weer verwijderd: de originele video is visueel leidend. De liggende video heeft sinds 8 oktober de volle bronresolutie (1920×1080, H.264, CRF 19, ±17,7 MB, SSIM 0,989 en
PSNR 45,3 dB ten opzichte van de HEVC-bron); de staande video (720×1280, ±5,4 MB) is ongewijzigd.

### Muziek (9 oktober 2026)

Kerststad heeft een eigen track, **"Kerststad (avondlicht)"** (`media/muziek.mp3`, 87 s, 1,4 MB, stereo): eigen compositie, door `tools/kerststad/maak_muziek.py` gesynthetiseerd (geen samples, geen bestaand lied, geen zang), dus vrij van rechten. D-groot, 66 BPM; celesta, zachte piano, strijkers, cello en kerstbelletjes. De opbouw volgt de film: rustig dorp (maat 1 tot 8) → de stad ontwaakt (9 tot 16) → bruisende kerstnacht (17 tot 22) → weer tot rust (23 en 24). De lus is circulair opgebouwd (ook de galm), dus de herhaling hoort naadloos te zijn; een mp3 kan in sommige browsers een paar honderdsten seconde stilte geven. Volume 0,45 met een zachte inzet van 2 s; nooit autoplay, alleen via de bestaande muziekknop.

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
| Video (staand) | `designs/kerststad/v1/media/opening.mp4` | goedgekeurde 9:16-video, web-klaar gemaakt | H.264 8-bit, 720×1280, 24 fps, 20,04 s, ±5,4 MB, zonder geluid, sleutelframe op 16,0 s; niet visueel bewerkt |
| Video (liggend) | `designs/kerststad/v1/media/opening-desktop.mp4` | goedgekeurde 16:9-video (`kerststad-desktop-16x9.mp4.mp4`), web-klaar gemaakt | H.264 High, yuv420p, 1920×1080 (bronresolutie), 24 fps, 20,04 s, CRF 19, faststart, ±17,7 MB, zonder geluid, sleutelframe op 16,0 s; geen extra filters of tweede resize |
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

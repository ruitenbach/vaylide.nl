# Kerstbol

> Ingevuld op 4 oktober 2026 op basis van de aanlevering van de eigenaar en bijgewerkt op 4 oktober 2026 met wat daadwerkelijk in het overdrachtspakket (`Vaylide-Kerst-Sneeuwbol-Claude-overdracht.zip`) en in `Vaylide-Kerst-Sneeuwbol-opening.html` is aangetroffen. Wat niet is aangeleverd staat als "nog niet bepaald"; er is niets bijverzonnen. Feiten uit de bestanden zijn gemerkt met hun bron.

## 1. Naam

Kerstbol

> De naamkeuze is definitief: **Kerstbol**, slug `kerstbol`. Het overdrachtspakket spreekt nog van "Kerstmagie Sneeuwbol" / `kerstmagie-sneeuwbol`; die naam wordt **niet** gebruikt.

## 2. Slug

`kerstbol`

## 3. Categorie

Kerst (het pakket zegt: "gebruik de bestaande categorie Kerst").

## 4. Status

On hold / interactieve preview bestaat, nog niet als definitieve VAYLIDE-kaart ingebouwd. Het pakket bevat een door de gebruiker goedgekeurd standalone prototype, nog geen Django-integratie. (Stand 4 oktober 2026.)

## 5. Concept / verhaal

De uitnodiging begint als een realistisch gesloten kerstcadeau. In het cadeau zit een sneeuwbol die tijdens de opening uit de doos omhoogkomt. De doos, sneeuwbol en kerstkamer/omgeving moeten visueel bij elkaar horen zodat de opening als één doorlopende scène voelt.

Uit het pakket (`CLAUDE-OPDRACHT.md`): een realistisch gesloten **rood cadeau met gouden satijnen lint** in een **smaragdgroene kerstkamer**. In de video is die kamer te zien met een hoog boograam met uitzicht op een besneeuwd dorp, kerstbomen en een glimmende vloer met lichtjes.

## 6. Opening / animatie

Definitieve basis:

1. Het beginbeeld is een realistisch gesloten cadeau.
2. De kijker ziet: "Tik om je kerstcadeau te openen".
3. Na klik/tik komt het lint los.
4. Het deksel opent.
5. Een sneeuwbol stijgt uit de doos omhoog.
6. De scène gaat over naar het gekozen eindbeeld / de sneeuwbolwereld.

Sparkles:

- vóór het openen: warm gouden fonkelingen rond het cadeau;
- ná het openen: fijnere witgouden glinsteringen rond de sneeuwbol.

De fonkelingen vóór en na de opening moeten bewust verschillend aanvoelen.

**Wat het goedgekeurde prototype uit het pakket (`preview-standalone.html` en `preview-assets.html`) doet:**

- Eén **doorlopende, realistische video** (geen getekend SVG-cadeau, geen losse CSS-animatie ter vervanging): de strik gaat volledig los, het lint glijdt weg, een kaal rood deksel opent, een sneeuwbol met verlichte kerstboom komt uit de doos, rendieren en slee verschijnen buiten het raam. Duur 10,04 s; de video stopt op het eindbeeld. De strik mag niet op het geopende deksel blijven zitten.
- Globaal tijdpad (uit een steekproef van één beeld per seconde): ±2 s strik los; ±3 s lint ligt los rond de doos; ±4 tot 5 s deksel gaat omhoog en opzij; ±6 tot 9 s sneeuwbol stijgt en staat op een gouden voet; rendieren en slee zijn vanaf ±4 s zichtbaar buiten het raam, goed te zien vanaf ±6 s; eindbeeld: geopende doos met sneeuwbol.
- Geen autoplay vóór de klik; het cadeau zelf is klikbaar (transparante knop over het cadeau, `aria-label` "Tik om je kerstcadeau te openen") en de afspeelstart komt rechtstreeks uit het klikgebaar. Onder in beeld staat de hint "TIK OM JE KERSTCADEAU TE OPENEN".
- Twee verschillende overlay-effecten (95 lichtpuntjes in totaal): 40 warme gouden fonkelingen rond het gesloten cadeau en in de eerste fase; vanaf 6,5 s in de video schakelt het script over op 55 fijne witgouden kristalglinsteringen rond de sneeuwbol. Lichtpuntjes fonkelen en vervagen; **geen vallende confetti of blaadjes**.
- Na het einde van de video verschijnt een bijschrift met de tekst "Een magische kerst gewenst", "Fijne feestdagen", "Vol warmte, liefde en bijzondere momenten.", een regel "Liefs, jullie namen" (in het prototype uit de queryparameter `?names=`) en de knop "Opnieuw beleven ↻".
- Afspeelblokkade of laadfout: er verschijnt een knop "Speel de opening af ▷"; bij een laadfout de tekst "Video laden mislukt — probeer opnieuw".
- 'Minder beweging': de lichtpuntjes worden verborgen en overgangen staan uit.

**Wat het pakket vraagt dat in het prototype nog niet zit:** een rustige knop "Opening overslaan" (die direct het eindbeeld en de groet toont, zo nodig met een lokaal opgeslagen eindposter uit het masterbestand), een duidelijke afspeelmogelijkheid zonder autoplay bij 'minder beweging', correcte focus/tabindex/aria-status, onzichtbare knoppen en bijschriften ook ontoegankelijk zolang ze niet zichtbaar zijn, voorfase-fonkelingen uit zodra fase twee begint, opruimen van listeners/timers en herstel van alle fases bij opnieuw beleven.

## 7. Pagina na de opening

Nog niet bepaald. De sneeuwbol/opening moet uiteindelijk onderdeel worden van een volledige VAYLIDE-uitnodiging.

Uit het pakket: de persoonlijke groet wordt na het einde van de video getoond; titel/kerstgroet en namen/afzender komen uit de bestaande studio-personalisatie; RSVP alleen wanneer het bestaande kerstkaarttype dat ondersteunt; geen trouwprogramma, trouwdatum of countdown forceren op deze kerstgroet. De opbouw van de pagina zelf: nog niet bepaald.

## 8. Assets en waar ze staan

**In de repository (draagbare referentiebronnen, geen definitieve product-assets), `tools/design-references/kerstbol/`:**

| Pad | Wat | Grootte |
|---|---|---|
| `tools/design-references/kerstbol/CLAUDE-OPDRACHT.md` | de opdracht uit het pakket (ongewijzigd) | 5 700 bytes |
| `tools/design-references/kerstbol/preview-standalone.html` | het goedgekeurde prototype (zelfstandig, offline) | 2 753 203 bytes |
| `tools/design-references/kerstbol/kerst-gesloten.webp` | startposter, 1520 × 2688 | 355 590 bytes |
| `tools/design-references/kerstbol/kerst-opening-web.mp4` | de goedgekeurde opening, 720 × 1280, 10,04 s, zonder audio | 1 704 604 bytes |
| `tools/design-references/kerstbol/README.md` | herkomst, checksums en wat bewust ontbreekt | |

Een toekomstige sessie kan het prototype dus openen met `tools/design-references/kerstbol/preview-standalone.html` en de video afspelen zonder de Downloads-map van de eigenaar. Bewust niet in de repository: het ZIP zelf, `kerst-opening-master.mp4` (16,7 MB) en `preview-assets.html`.

**Lokaal bij de eigenaar (bronnen, niet in Git).** Gezocht en onderzocht op 4 oktober 2026; het pakket is voor het onderzoek uitgepakt naar een tijdelijke werkmap buiten de repository.

| Asset | Locatie | Specificaties | Opmerking |
|---|---|---|---|
| `Vaylide-Kerst-Sneeuwbol-Claude-overdracht.zip` (lokale masterbron) | `C:\Users\j-rui\Downloads\` | 20 860 827 bytes, 6 bestanden | Bevat ook `kerst-opening-master.mp4` en `preview-assets.html`. Inhoud hieronder. |
| ↳ `CLAUDE-OPDRACHT.md` | in het ZIP, `Vaylide-Kerst-Sneeuwbol/` | 5 700 bytes | Opdracht en instructies voor Claude Code (geen AI-prompts voor beeld of video). |
| ↳ `preview-standalone.html` | in het ZIP | 2 753 203 bytes | Het goedgekeurde prototype, zelfstandig (poster en video als base64 ingebed). |
| ↳ `preview-assets.html` | in het ZIP | 6 284 bytes | Hetzelfde prototype met losse mediapaden (`assets/...`). Het script is identiek aan dat in `preview-standalone.html`. |
| ↳ `assets/kerst-gesloten.webp` | in het ZIP | 355 590 bytes, 1520 × 2688 px, RGB | Gesloten cadeau; startposter. |
| ↳ `assets/kerst-opening-web.mp4` | in het ZIP | 1 704 604 bytes, 720 × 1280, 24 fps, 241 beelden, 10,04 s, H.264, geen audiospoor | Geoptimaliseerde webvideo. Dezelfde video zit ingebed in `preview-standalone.html`. |
| ↳ `assets/kerst-opening-master.mp4` | in het ZIP | 16 709 608 bytes, 1080 × 1912, 24 fps, 241 beelden, 10,04 s, H.264, geen audiospoor | Originele gegenereerde video, voor eventuele transcodering. |
| `Vaylide-Kerst-Sneeuwbol-opening.html` | `C:\Users\j-rui\Downloads\` | 3 042 514 bytes | **Andere variant dan de HTML in het ZIP**, zie onder. |

De tijdelijke uitgepakte kopie staat buiten de repository (de werkmap van deze sessie) en hoeft niet bewaard te worden; het ZIP in Downloads is de bron.

## 9. Externe AI/video-output

Er is een interactieve preview gemaakt van: cadeau → lint los → deksel open → sneeuwbol omhoog. Welke tool of prompt daarvoor is gebruikt, staat niet in het pakket en is niet aangeleverd: nog niet bepaald. Het pakket zegt wel: de video is "gegenereerd" (het masterbestand is de "originele gegenereerde video"), en het noemt Higgsfield-credits: **genereer geen nieuwe AI-beelden of -video's, gebruik geen Higgsfield-credits en verleng of regenereer de video niet; de gebruiker wil voortaan eerst idee, beeld en beweging bespreken en pas na expliciet akkoord credits besteden; ook retries en varianten vereisen overleg.** Gebruik de goedgekeurde assets uit het pakket.

## 10. Technische bouwinstructies

Nog niet definitief bepaald. Wel behouden:

- klik/tik als start;
- geen automatische opening;
- cadeau, sneeuwbol en kamer moeten tijdens de overgang visueel aansluiten;
- gouden fonkeling vóór het openen;
- subtielere witgouden sparkle na het openen;
- geschikt maken voor mobiel en desktop wanneer de definitieve VAYLIDE-versie gebouwd wordt.

**Techniek van het goedgekeurde prototype (aangetroffen in het ZIP):** één HTML-bestand met ingebedde CSS en JavaScript, zonder externe bibliotheken en zonder externe verwijzingen (het werkt offline). Beweging is een HTML5-`<video>` (`muted playsinline preload="auto"`, poster) met daaroverheen CSS-overgangen voor bijschrift en knoppen en 95 lichtpuntjes (`<i>`-elementen die het script aanmaakt; plaatsing in een gouden-hoekspiraal rond het cadeau en later rond de bol; CSS-keyframes `gold-glint` en `crystal-glint`, oneindig herhalend, verborgen bij 'minder beweging'). Geen canvas, GSAP of 3D. De fase-wissel loopt via `timeupdate` (`afterglow` vanaf 6,5 s) en de klassen `playing` en `finished`. Het beeldvlak is een 9:16-kader (`width: min(94vw, 460px, ...)`) op een groen verloop (#102b23). Kleuren in het prototype: donkergroen (#102b23, #31533a), goud (#bc9a63, #f5c775), crème (#f7e7c7).

**Instructies uit `CLAUDE-OPDRACHT.md` voor de integratie** (samengevat): eigen nieuw zelfstandig kerstontwerp op een aparte branch; bestaande ontwerpen behouden; bestaande designregistratie, CSP, studio, bestellen/testbetaling, opgeslagen kaarten en delen gebruiken; inline CSS/JS splitsen; geen base64-media in productie en geen externe generatie-CDN als runtimebron; klantinhoud escapen (queryparameters en placeholders uit het prototype zijn geen productiebron); echte toegankelijke knop met bruikbaar touchdoel; afspeelstart rechtstreeks uit het klikgebaar, `muted`/`playsinline`, duidelijke handmatige fallback; geen automatisch herhalen; tests op 360, 390, 768 en 1366 px en de hele klantreis; staging alleen na controle van de bedoelde testsite en branch; geen productiepublicatie zonder expliciet akkoord.

**Het losse bestand `Vaylide-Kerst-Sneeuwbol-opening.html` (Downloads) is een andere variant dan het goedgekeurde prototype in het ZIP.** Titel "Vaylide · Kerstmagie". Het bevat een in SVG getekend rood cadeau met CSS-animatie (strik, lint en deksel gaan los), een stilstaande sneeuwbol-afbeelding die omhoog komt (1520 × 2688, ook als poster), daarna een ingebedde video van 5,04 s (720 × 1280, 24 fps, H.264, 1 487 388 bytes) waarin de doos al open is en de strik op het geopende deksel ligt, 30 stofdeeltjes, een knop "Opening overslaan" en "Opnieuw beleven", en een tijdpad via timers (0 s losmaken, 0,9 s openen, 1,45 s bol komt op, 4,3 s video, 8,4 s klaar). Het werkt zelfstandig en offline (3 base64-media, geen externe verzoeken; getest in een browser zonder netwerk: geen fouten, de video speelt tot het einde, geen horizontale scroll op 390 px). De video en poster zijn niet dezelfde bestanden als in het ZIP. Het ZIP noemt `preview-standalone.html` (in het ZIP) als het goedgekeurde prototype en verbiedt een getekend SVG-cadeau en een strik op het geopende deksel. Dit losse bestand is daarom hoogstens een eerdere iteratie (niet bevestigd) en geen bron om 1-op-1 te volgen.

## 11. Wat al afgerond is

- basisconcept;
- cadeau als beginbeeld;
- interactieve opening;
- lint/deksel/sneeuwbol-sequence;
- onderscheid tussen sparkle vóór en na;
- HTML-preview;
- een door de gebruiker goedgekeurd standalone prototype met de goedgekeurde video (webversie en master) en poster (alles in het overdrachtspakket).

## 12. Wat nog moet gebeuren

- [x] bestaande preview/assets terugvinden (HTML-preview en het overdrachtspakket zijn gevonden en onderzocht; het cadeau-beginbeeld is `kerst-gesloten.webp`);
- [ ] definitieve pagina na de opening bepalen;
- [ ] VAYLIDE-integratie (zie de instructies hierboven), inclusief "Opening overslaan", 'minder beweging', focus/aria en opruimen van timers en listeners;
- [ ] bepalen hoe de sneeuwbol overgaat naar de eigenlijke uitnodiging;
- [ ] een lokaal opgeslagen eindposter uit het masterbestand (alleen als dat nodig is voor "Opening overslaan");
- [ ] responsive/motion/performance later testen.

## 13. Besluiten die niet opnieuw ter discussie hoeven

- naam `Kerstbol`, slug `kerstbol` (niet `kerstmagie-sneeuwbol`);
- start met een gesloten cadeau;
- de tekst is "Tik om je kerstcadeau te openen";
- het lint komt los;
- het deksel opent;
- de sneeuwbol stijgt omhoog;
- warm gouden fonkelingen vóór de opening;
- fijnere witgouden fonkelingen rond de sneeuwbol ná de opening;
- cadeau, sneeuwbol en omgeving vormen één consistente scène;
- (uit het pakket) één doorlopende realistische video, geen getekend SVG-cadeau; de strik blijft niet op het geopende deksel; geen autoplay vóór de klik; geen vallende confetti of blaadjes; geen nieuwe AI-beelden of -video's en geen credits zonder expliciet akkoord.

## 14. Laatste relevante commit

Nog niet bepaald / nog niet in Git aangetroffen.

## 15. Volgende stap

Beslis (door de eigenaar) over de pagina na de opening; daarna kan de integratie in VAYLIDE gebouwd worden op basis van `tools/design-references/kerstbol/` (`preview-standalone.html`, de webvideo en de poster). Nog niets gebouwd.

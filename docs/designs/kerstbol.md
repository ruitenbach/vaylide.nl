# Kerstbol

> Ingevuld op 4 oktober 2026 op basis van de aanlevering van de eigenaar en bijgewerkt op 4 oktober 2026 met wat daadwerkelijk in het overdrachtspakket (`Vaylide-Kerst-Sneeuwbol-Claude-overdracht.zip`) en in `Vaylide-Kerst-Sneeuwbol-opening.html` is aangetroffen. Wat niet is aangeleverd staat als "nog niet bepaald"; er is niets bijverzonnen. Feiten uit de bestanden zijn gemerkt met hun bron.

## 1. Naam

Kerstbol

> De naamkeuze is definitief: **Kerstbol**, slug `kerstbol`. Het overdrachtspakket spreekt nog van "Kerstmagie Sneeuwbol" / `kerstmagie-sneeuwbol`; die naam wordt **niet** gebruikt.

## 2. Slug

`kerstbol`

## 3. Categorie

Kerst, en een **Special** (besluit van de eigenaar, 4 oktober 2026): hij staat onder Specials, in groep A van de collectie (`sort_order` 7, direct na Golden Noël). Er is **geen meerprijs bedacht**: zolang er geen optie `special-kerstbol` in Beheer → Prijzen bestaat, kost Kerstbol gewoon de prijs van het gekozen pakket en is hij dus bestelbaar (de bestaande Special-terugval, net als bij de andere Specials).

## 4. Status

**Gebouwd** (4 oktober 2026): Kerstbol is als echte VAYLIDE-kaart gebouwd in `designs/kerstbol/v1/` en gecommit op de lokale werkbranch `claude/kerstbol` (vanaf `8c429a7`). Hij is een **Special** (categorie Kerst, groep A van de collectie). De **prijs voor `special-kerstbol` is nog niet bepaald**: zolang er geen optie `special-kerstbol` in Beheer → Prijzen staat, kost Kerstbol gewoon de prijs van het gekozen pakket en is hij dus bestelbaar (de bestaande Special-terugval, net als bij de andere Specials). Niet gepusht, niet op staging, niet current/live.

**Vastgelegde keuzes (eigenaar, 4 oktober 2026):**

- **Desktop toont de verticale video bewust volledig, over de volle hoogte, met dynamische zijgloed.** Op een breed scherm wordt de video niet bijgesneden tot volledige breedte: de eigenaar wil geen belangrijke delen van het cadeau, de opening of de sneeuwbol verliezen. Aan weerszijden staat een gloed die uit de video zelf wordt getekend. Op een telefoon loopt de video van rand tot rand.
- **De goedgekeurde opening is inhoudelijk afgerond en moet niet meer worden gewijzigd** (gesloten cadeau, tik, lint los, deksel open, sneeuwbol omhoog, gouden en witgouden fonkelingen, één video). Technische verbeteringen of een v2 alleen na uitdrukkelijk akkoord van de eigenaar.
- "Uitbundig" betekent hoogwaardig, gelaagd en bijzonder; iedere kaart houdt een eigen identiteit (zie de ontwerpregel in `docs/designs/README.md`).

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

**Zoals gebouwd (4 oktober 2026, besluit van de eigenaar):** de kaart na de video gaat door in dezelfde wereld (diep smaragdgroen, warm champagnegoud, zachte lichtpuntjes en sneeuw, geen witte kaart direct na de opening) en toont alleen wat de klant heeft ingevuld:

- de persoonlijke kerstgroet (champagnekleurige brief met gouden hoeken; de foto van de klant **in een sneeuwbol** met een gouden voet en zachte sneeuw);
- "Ons jaar" (de studiotitel) met een groot citaat op de achtergrond van het raam met het dorp, "Momenten" als **kerstballen aan een draad** (de foto's van de klant) en de persoonlijke tekst;
- een luxe afsluiting met de afzender in goudfolie, de namen eronder, de afsluitende tekst van de klant en de deelknoppen;
- de uitbundige laag eromheen (op verzoek van de eigenaar, 4 oktober 2026): banden in diep smaragd, **bordeaux** (programma, aanmelden) en één **champagnegouden band** (aftellen); goudfolie met een langzame glans op koppen en cijfers; draaiende stralenkransen; **lichtsnoeren** met twinkelende lampjes; gouden hoeken; achtergronden die uit dezelfde goedgekeurde video zijn gesneden (het raam met het dorp, de sneeuwbol) en bij het scrollen zacht meebewegen (alleen met CSS scroll-gedreven animatie, geen JavaScript);
- alleen **bij een kerstdiner (een ingevulde datum)**: datum, programma, aftellen, locatie en aanmelden. Zonder datum verdwijnen die onderdelen, ook het aftellen.
- Dresscode, "Goed om te weten" en contact verschijnen alleen als de klant ze heeft ingevuld.
- Er wordt geen inhoud verzonnen; vaste woorden in de kaart zijn alleen kopjes ("Momenten", "Kerstdiner", "Het programma", "Locatie", "Kom je ook?").

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


**In het product (`designs/kerstbol/v1/`, gebouwd op 4 oktober 2026):**

| Pad | Wat | Grootte |
|---|---|---|
| `designs/kerstbol/v1/media/opening.mp4` | de goedgekeurde webvideo (uit `tools/design-references/kerstbol/kerst-opening-web.mp4`, ongewijzigd) | 1 704 604 bytes |
| `designs/kerstbol/v1/media/poster.webp` | gesloten cadeau, 1080 breed, uit `kerst-gesloten.webp` | 262 772 bytes |
| `designs/kerstbol/v1/media/eind.webp` | eindposter: het laatste beeld van dezelfde video | 178 598 bytes |
| `static/img/designs/kerstbol.webp` | kaartbeeld voor de collectie (800 × 1000), uit dat eindbeeld | 143 436 bytes |
| `designs/kerstbol/v1/media/raam.webp` | uitsnede van het raam met het dorp (achtergrond van "Ons jaar", locatie en afsluiting) | 59 044 bytes |
| `designs/kerstbol/v1/media/bol.webp` | uitsnede van de sneeuwbol (achtergrond van het datumsmedaillon) | 48 476 bytes |
| `designs/kerstbol/v1/{manifest.json, invitation.html, style.css, kerstbol.js, _slinger.html}` | het ontwerp | |

Er is geen nieuw AI-beeld of -video gemaakt. Het masterbestand (16,7 MB) is niet gebruikt.

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

**Zoals gebouwd (4 oktober 2026):**

- Opening, kop en feest zijn één scène (`.kb-hero`) met een eigen script, net als Gouden Avond: geen openingsscherm van `invite.js`, geen tweede video, geen GSAP.
- **De video is beeldvullend** (op verzoek van de eigenaar): geen klein kader meer. Op een telefoon loopt hij van rand tot rand; op een breder scherm staat hij over de volle hoogte met aan weerszijden een gloed die uit de video zelf wordt getekend (een canvas van 32 × 57 pixels, ±15 keer per seconde, alleen op een breed scherm en alleen terwijl de video speelt). De video wordt niet bijgesneden: het hele beeld blijft zichtbaar. `envelope_mode` is `built_in` (geen extra envelop ervoor).
- Eén `<video>` (stil, `playsinline`, `preload="metadata"`, poster); een echte knop over het cadeau start hem rechtstreeks vanuit de tik; de video herhaalt niet. De video wordt pas voorgeladen (`preload="auto"`) als de pagina rustig is of de gast het cadeau aanraakt, niet bij Data-besparing of 2G.
- Fonkelingen: 40 gouden (vóór en in de eerste fase), vanaf 6,5 s in de video 55 witgouden kristallen; ze worden pas aangemaakt als ze nodig zijn en daarna verwijderd. Vallen niet. Het prototype gebruikte een `drop-shadow` per deeltje; dat is een lichte `box-shadow` geworden.
- Bediening: **Opening overslaan** (toont direct het eindbeeld met de groet, zonder te wachten op de video), **Opnieuw beleven**, **Speel de opening af** (bij minder beweging, stilgezette beweging, opening al gezien in dezelfde sessie, geblokkeerde autoplay of een laadfout), een statusmelding voor schermlezers en toetsenbordbediening met focus op "Naar de kaart" na afloop. Tijdens de opening is de pagina niet scrolbaar en de rest van de kaart `inert`.
- Teksten: studiovelden zijn altijd leidend (afzender, kop, tagline, namen eronder). De prototypeteksten zijn alleen een terugval als het veld leeg is ("Een magische kerst gewenst", "Fijne feestdagen", "Vol warmte, liefde en bijzondere momenten.").
- De collectie: `catalog/collectie.py` (A en Specials, `sort_order` 7), tests aangepast (aantal ontwerpen 47), `tests/test_kerstbol.py`, `e2e/kerstbol.cjs`.

## 11. Wat al afgerond is

- basisconcept;
- cadeau als beginbeeld;
- interactieve opening;
- lint/deksel/sneeuwbol-sequence;
- onderscheid tussen sparkle vóór en na;
- HTML-preview;
- een door de gebruiker goedgekeurd standalone prototype met de goedgekeurde video (webversie en master) en poster (alles in het overdrachtspakket);
- de echte VAYLIDE-kaart `kerstbol` (lokaal, ter beoordeling): opening, overslaan, minder beweging, kaart met brief, "Ons jaar", momenten en afsluiting, het kerstdiner alleen bij een datum, collectie-registratie en tests (4 oktober 2026).

## 12. Wat nog moet gebeuren

- [x] bestaande preview/assets terugvinden (HTML-preview en het overdrachtspakket zijn gevonden en onderzocht; het cadeau-beginbeeld is `kerst-gesloten.webp`);
- [x] pagina na de opening: gebouwd volgens het besluit van de eigenaar (4 oktober 2026), nog te beoordelen;
- [x] VAYLIDE-integratie, inclusief "Opening overslaan", 'minder beweging', focus/aria en opruimen van timers en listeners (lokaal gebouwd);
- [x] overgang van de sneeuwbol naar de kaart: groet over het eindbeeld, daarna "Naar de kaart";
- [x] eindposter: het laatste beeld van de webvideo (`media/eind.webp`);
- [ ] eigenaar beoordeelt de lokale preview; daarna commit, staging en een prijs voor de Special (Beheer → Prijzen, `special-kerstbol`);
- [ ] responsive/motion/performance later testen.

## 13. Besluiten die niet opnieuw ter discussie hoeven

- naam `Kerstbol`, slug `kerstbol` (niet `kerstmagie-sneeuwbol`);
- Kerstbol is een Special (categorie Kerst); geen prijs of meerprijs zelf bedenken;
- de kaart na de opening is rijk in dezelfde wereld (smaragd, champagnegoud, lichtpunten, sneeuw), geen standaard witte kaart; datum, locatie, programma, aanmelden en aftellen alleen bij een kerstdiner; geen verzonnen inhoud;
- studiovelden zijn altijd leidend, de prototypeteksten alleen als terugval;
- eindposter en kaartbeeld komen uit de goedgekeurde video; geen nieuwe AI-beelden;
- geen GSAP alleen om GSAP te gebruiken;
- desktop toont de verticale video volledig over de volle hoogte met dynamische zijgloed (niet croppen tot volledige breedte);
- de goedgekeurde opening wordt inhoudelijk niet meer gewijzigd;
- de prijs voor `special-kerstbol` is nog niet bepaald; er wordt geen prijs bedacht;
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

Het commit "Kerstbol: nieuwe Special met een beeldvullende cadeau-opening en een kerstkaart in smaragd, bordeaux en goud" is het eerste commit op de lokale branch `claude/kerstbol` na `8c429a7` (`git log claude/kerstbol`). Niet gepusht.

## 15. Volgende stap

De eigenaar bepaalt de prijs voor `special-kerstbol` (Beheer → Prijzen) en geeft aan wanneer de branch `claude/kerstbol` naar de remote mag en of er een stagingtest komt. Tot die tijd: niet pushen, niet deployen, niet current maken.

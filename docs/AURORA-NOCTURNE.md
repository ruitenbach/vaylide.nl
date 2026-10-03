# Aurora Nocturne (special, versie 1): alleen de kop

Stand 3 oktober 2026. Een special voor bruiloft, verloving en jubileum (`designs/aurora-nocturne/v1/`, slug `aurora-nocturne`, `"special": true`).
Nu af: **de kop** (openingsscherm, envelop, zegel, lichtportaal, paviljoenscène, namen, rustscène). De rest van de uitnodiging (datum, programma,
aanmelden enz.) staat er wel en werkt, maar is bewust sober en nog niet uitgewerkt: eerst de kop beoordelen.

## Wat de gast ziet (tijd 0 = de tik; scène 1 speelt vooraf vanzelf)

| Tijd | Scène | Wat |
|---|---|---|
| vóór de tik | 1 Duisternis | Bijna zwart scherm. De nachtblauwe envelop (fluweelkorrel, champagnegouden rand, zegel met monogram) komt uit het donker doordat licht over het papier glijdt. Fijn stof. Alleen "Open uitnodiging". |
| 0 - 0,85 s | 2 Het zegel | Het zegel drukt in, een gouden lichtlijn loopt door het reliëf, een minieme reflectie, lichte spanning. Dan breekt het langs een scheur (de bovenste helft zit aan de klep, de onderste aan de envelop); brokjes goud vallen weg. Geen explosie. |
| 0,75 - 2,5 s | 3 Envelop | Een aurora-achtige lichtlijn loopt vanuit het midden langs de vouw. Eén klep met massa: komt zwaar los, zwaait naar de camera, valt over en komt tot rust. Schaduw onder de klep trekt weg, binnenin gaat licht aan en valt op de voering, de klep werpt een schaduw. |
| 1,5 - 3,0 s | 4 Lichtportaal | Een smalle spleet licht in de open envelop groeit tot een boogvenster (een gat in het donker via `clip-path`) terwijl de camera de envelop in schuift. Erachter ligt de wereld, nog onder een sluier van licht. Het scherm gaat weg op 3,0 s (`data-duration`). |
| 1,5 - 4,8 s | Camera | De camera trekt 3 tot 5% terug; vijf dieptelagen schalen net iets anders (zeer subtiele parallax). |
| 2,75 - 3,9 s | Lichtmoment | Cascade: entree, zijramen, kroonluchter, lampjes, kaarsen. |
| 3,05 - 5,6 s | Tekst | Pas daarna: kicker, Sophie, "kleine rust", &, Daniël, datum, tagline. Masker, tracking, opacity en een paar pixels beweging; geen typemachine. |
| vanaf ±5,6 s | Rust | Langzaam noorderlicht, mist, kaarsvlammen, af en toe een stofje. |

## Opbouw

- **Beelden**: eigen tekeningen met code (`tools/aurora_nocturne/art.js` en `render.cjs`, Chromium canvas), geen foto's of AI-beelden. Lagen per kleurvariant in `img/<variant>/`: `lucht`, `aurora-a/b`, `ver` (heuvels, bos, meer), `mist`, `paviljoen`, vijf lichtkaarten `licht-*` (alleen het licht zelf is zichtbaar), `voor-l/r`, `hoek` en `slinger` (bloemen); `img/korrel.webp` (fluweel) is voor alle varianten gelijk. Een bezoeker laadt één set: ±0,95 MB.
- **Kleurvarianten** (palettes in het manifest, elk met een eigen set beelden): `nacht` (Nachtblauw & champagne, het origineel), `parel` (Parelmoer & champagne: ijsblauw en parelwit met een zweem champagne), `roze` (Rozenmorgen: dageraad met mauve heuvels) en `saliemist` → sleutel `salie` (Saliemist: zeeglas en zacht groen). De drie lichte varianten zijn eigen tekeningen, geen filter over de nachtbeelden: sluierwolken in plaats van sterren, pastellinten in plaats van noorderlicht, een lichte mist en een donker, slank frame (grafiet, pruim, bosgroen). Het sjabloon kiest de map met `v.palette_key`. Alle kleuren van de pagina, de envelop (ivoor papier, gouden zegel) en het openingsscherm komen uit variabelen (`--an-…`) van het palet; de stofdeeltjes lezen `--an-stof` en `--an-stof-2`. Tekstkleuren in alle varianten minstens 4,5:1 (bewaakt in `tests/test_aurora_nocturne.py`).
- **Omlijsting (uitbundig)**: het openingsscherm is een volle compositie rond een kleinere, lagere envelop (±140 px breed op een telefoon, hoogstens 220 px; verhouding 1 : 1,12): vier bloemenhoeken (`img/<variant>/hoek.webp`, één tekening die gespiegeld wordt), drie bogen die zich tekenen, een waaier van lichtstralen die traag draait, sterretjes en vonkjes, "Je bent uitgenodigd" met de kop van de uitnodiging erboven en de datum eronder. De namen staan er bewust niet: die verschijnen pas in de kop. Bij het openen verdwijnt de versiering mee met het portaal (de bloemen schuiven naar de camera toe). De kop heeft bloemen in de bovenhoeken, een waaier van licht achter het paviljoen en opstijgende lampionnen (in het stofcanvas getekend, alleen in de kop). De rest van de uitnodiging heeft een boog met het grote datumgetal, een tijdlijn voor het programma, aftelbogen, een paviljoen-icoon bij de locatie, een slinger (`slinger.webp`) boven het welkom en boven het aanmeldformulier, en sierlijsten tussen de onderdelen. Alles wat beweegt, beweegt alleen met beweging aan.
- **Geen 60 lampjes**: de lampen zijn vijf doorzichtige lichtkaarten waarvan alleen de opacity verandert (cascade met GSAP). Geen `mix-blend-mode`.
- **GSAP** (`static/vendor/gsap/`: `gsap` en `ScrollTrigger`): één master-timeline `film` in `aurora-nocturne.js`, in `gsap.context` en `gsap.matchMedia`. Het portaal is `clip-path: path(evenodd, …)` die per beeld wordt bijgewerkt, plus een rand van licht (drie SVG-lijnen).
- **Rust**: één stofcanvas (16 beelden per seconde, een handvol deeltjes) dat van het openingsscherm naar de kop verhuist, en zes CSS-lussen op losse lagen. De langzame lussen lopen in stappen (`steps()`), zodat de browser de grote lagen maar een paar keer per seconde opnieuw samenstelt. Alles onder `.fx-motion`; pauze zodra de kop uit beeld is.
- **Reduced motion / Beweging uit / geen GSAP**: de uitnodiging opent in 0,25 s; alles staat in de eindstand (lampen aan, tekst zichtbaar, geen stof).
- **Direct openen** (al geopend in deze sessie, of `#aanmelden`): korte versie zonder envelop, de wereld komt in ±2,5 s tot rust.
- **Maten**: één samenstelling met `object-fit: cover` voor lucht en heuvels; het paviljoen is een eigen vlak dat onderaan staat. Een kleine meting (`pasPaviljoenAan`) houdt de torenspits onder de laatste tekstregel; vanaf beeldverhouding 5:4 staan de namen op één regel.
- **Platform**: manifest met `special: true`, `envelope_mode: built_in` en effects `sfeer`/`knal`: `geen` (dus geen deeltjes-canvassen van het platform). Twee kleine, achterwaarts compatibele toevoegingen in `catalog/effects.py`: een ontwerp zonder deeltjes kan `samenvatting` en `kaartlabel` in het effects-blok zetten (voor de ontwerppagina en de kaart). Bestaande ontwerpen veranderen niet.
- **Prijs**: als special is hij pas te bestellen als in Beheer → Prijzen de optie `special-aurora-nocturne` (functie `special`) bestaat. Er is geen prijs bedacht.

## Beelden opnieuw maken

```bash
node tools/aurora_nocturne/render.cjs            # alle vier de varianten naar designs/aurora-nocturne/v1/img/<variant>/
node tools/aurora_nocturne/render.cjs parel      # alleen één variant (nacht, parel, roze of salie)
node tools/aurora_nocturne/render.cjs alles preview   # alleen voorbeeldbeelden (donker en verlicht) naar /tmp/aurora-preview
# Een nieuwe variant: kleuren in THEMES in art.js, palet met alle --an-variabelen in manifest.json, en de sleutel in PALETTEN in de test.
.venv/bin/python tools/aurora_nocturne/testuitnodiging.py   # lokale testuitnodiging "Sophie & Daniël", 14 juni 2027
node e2e/aurora_nocturne.cjs http://127.0.0.1:8000 /u/<code>/ /tmp/aurora-controle    # tijdlijn, fps, console, overflow, reduced motion
```

Een uitgebrachte versie niet wijzigen: aanpassingen komen in `designs/aurora-nocturne/v2/`.

## Nog te doen (bewust niet gedaan)

- De secties onder de kop uitwerken in dezelfde stijl (datum, programma, locatie, dresscode, aanmelden, aftellen).
- Controle op echte telefoons en in Safari/Firefox, en met een schermlezer. De fps hieronder komen uit headless Chromium zonder GPU.
- `e2e/toegankelijkheid.cjs` (axe) voor dit ontwerp in alle vier de varianten (de contrastverhoudingen van de tekstkleuren zijn wel getest, de tekst op de beelden van de kop niet met axe).
- Kaartafbeelding (`static/img/designs/aurora-nocturne.webp`) is een schermopname van de kop; opnieuw maken als de kop verandert.

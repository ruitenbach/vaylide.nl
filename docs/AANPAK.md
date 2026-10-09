# Aanpak, keuzes en aannames

## Doel

Een complete eerste versie van Vaylide (eerst de werknaam Vierlief) waarin standaardbestellingen zelfstandig verlopen: van ontwerp kiezen tot een gepubliceerde uitnodiging met aanmeldingen. De eigenaar grijpt alleen in bij extra wensen, vragen en storingen.

## Uitgangssituatie

Vaylide is een nieuw, zelfstandig project met een eigen repository. Er was nog geen bestaande techniek om op voort te bouwen, dus de keuze hieronder is gemaakt voor een platform met een database, betalingen, accounts en uploads.

## Techniekkeuze

**Python met Django 5.2 LTS** (ondersteund tot april 2028):

- Pagina's worden op de server opgebouwd. Ze laden snel op telefoons en werken ook zonder zware JavaScript. De uitnodiging blijft leesbaar als scripts of animaties niet laden.
- Django heeft ingebouwde beveiliging (CSRF, sessies, wachtwoorden, clickjacking), een volwassen database-laag met migraties en een noodbeheer (Django admin).
- Geen aparte build-stap of frontend-framework. Dat houdt het onderhoud eenvoudig.
- SQLite voor ontwikkeling en kleine installaties; PostgreSQL voor productie. De tests zijn op beide gedraaid.
- Verder: WhiteNoise (statische bestanden), Pillow (fotoverwerking), segno (QR-codes), gunicorn (webserver) en de officiële Anthropic-SDK voor de optionele AI-hulp.

## Opbouw in het kort

- **Ontwerpen en inhoud zijn gescheiden.** Een ontwerp is een map `designs/<code>/v<N>/` met een manifest, een HTML-template en een stylesheet. De gegevens van een evenement staan los daarvan in de database, als gestructureerde inhoud. Er wordt per bestelling geen website gebouwd.
- **Ontwerpversies zijn vastgezet.** Iedere uitnodiging verwijst naar één vaste ontwerpversie. Een nieuwe versie verandert bestaande uitnodigingen dus niet. Overstappen gebeurt alleen bewust, in het concept, en gaat pas live na publiceren.
- **Concept en gepubliceerde versie zijn gescheiden.** Wijzigingen gaan pas live na publiceren, op dezelfde link. Elke publicatie is een bewaarde versie die hersteld kan worden.
- **Conflicten worden gemeld.** Elk opslaan controleert of het concept intussen door een ander is gewijzigd (door de klant of het team). Zo ja, dan wordt niets overschreven: de klant ziet wat er veranderd is en kiest zelf. Beheer kan velden ook vergrendelen.
- **Verwerking na betaling via een takenwachtrij.** Publiceren en e-mailen zijn taken met een unieke sleutel. Herhaalde betalingsmeldingen leveren dus geen dubbele publicaties of e-mails op. Mislukte taken worden automatisch opnieuw geprobeerd en daarna aan de eigenaar gemeld.
- **Vormgeving naar de voorbeeldfoto van de eigenaar**: warm crème, goud en diep bosgroen, Playfair Display voor koppen en DM Sans voor tekst, zachte panelen met ronde hoeken en dunne gouden lijniconen. Eén duidelijke knop per blok en korte teksten. De website, het samenstellen, Mijn Vaylide en het beheer delen één stijlblad met dezelfde kleuren en lettertypen. Zie "Nieuwe vormgeving" hieronder.
- **Snel**: pagina's worden op de server opgebouwd, tekst wordt gecomprimeerd, statische bestanden krijgen een versiekenmerk en lange cachetijd, en foto's komen in passende formaten.
- **Externe diensten zitten achter een eigen koppeling**, met een herkenbare testvariant: de betaalprovider (test of Mollie), e-mail (bewaren of SMTP) en AI (vaste teksten of Claude).

## De tien stappen uit de opdracht

| Opdracht | In Vaylide |
|---|---|
| 1. Gelegenheid kiezen | `/maken/`: bruiloft, verloving, verjaardag, jubileum, babyshower of zakelijk |
| 2. Ontwerp kiezen en uitproberen | Stap *Ontwerp*, met werkende voorbeelden per ontwerp en per gelegenheid |
| 3. Evenementgegevens invullen | Stappen *Gegevens*, *Programma & info* en *Aanmelden*; alleen vragen die bij de gelegenheid passen |
| 4. Foto's uploaden | Stap *Foto's & verhaal*: uitsnede kiezen (focuspunt en zoom) per foto, eventueel muziek |
| 5. Kleuren, secties en opties | Stap *Stijl & onderdelen*: kleurvariant, opening, onderdelen aan/uit |
| 6. Persoonlijk voorbeeld | Stap *Voorbeeld*: telefoon-, computer- en volledige weergave |
| 7. Fouten corrigeren | Het voorbeeld toont een controlelijst met directe links naar de stap waar iets ontbreekt |
| 8. Bestelling en totaalprijs | Stap *Bestellen*: pakket, automatisch benodigde opties, totaal aan de serverzijde berekend |
| 9. Betalen | Testbetaalpagina (nu) of Mollie (na aansluiten) |
| 10. Publicatie en klantomgeving | Statuspagina met de link, e-mail met link en QR-code, en in *Mijn Vaylide* de link, de QR-code (PNG en SVG) en de aanmeldingen |

Een voortgangsindicator toont steeds waar de klant is. Zonder account wordt het ontwerp in de sessie bewaard. Met **Opslaan en later verder** krijgt de klant een inlogcode per e-mail en staat het concept daarna in *Mijn Vaylide*. Bij bestellen is een geverifieerd e-mailadres nodig; dat wordt op dat moment duidelijk gemeld.

## Aannames

Deze keuzes zijn gemaakt om door te kunnen bouwen. Alle zijn aan te passen.

- **Naam en domein:** eerst de werknaam "Vierlief", daarna kort "Vaylia"; sinds ronde 6 heet het merk "Vaylide" (zie "Ronde 6: Vaylide"). Het adres van de site is instelbaar (`VIERLIEF_BASE_URL`); het domein van de eigenaar is `vaylide.com`.
- **Taal:** alleen Nederlands in deze versie.
- **Prijzen (voorlopig, incl. btw):** *Essentieel* € 39 (6 maanden online) en *Compleet* € 69 (12 maanden, met verhaal, fotogalerij tot 12 foto's, muziek en extra vragen). Losse opties: muziek € 9, fotogalerij € 12, verhaal € 6, extra vragen € 6 en 12 maanden langer online € 12. Op de site staat "Voorlopige prijzen". Alles is instelbaar in Beheer.
- **Inloggen klanten:** met een eenmalige code per e-mail, zonder wachtwoord. De code is 20 minuten geldig, met maximaal 5 pogingen. Zo is het e-mailadres meteen geverifieerd en zijn er geen vergeten wachtwoorden. **Beheerders** loggen in met e-mail en wachtwoord op `/beheer/inloggen/`.
- **Gasten:** geen account. Er wordt alleen gevraagd naar naam, aanwezig of afwezig, aantal personen en de vragen die de klant zelf toevoegt (met Compleet of de optie). Standaard mogen gasten met maximaal 2 personen komen, per uitnodiging instelbaar.
- **Beschikbaarheid:** een uitnodiging staat online vanaf de eerste publicatie, zo lang als het pakket aangeeft (verlengbaar). Daarna gaat hij automatisch offline.
- **Bewaartermijnen (instelbaar):** gastgegevens 90 dagen na het einde van de beschikbaarheid; ontwerpen zonder account 30 dagen; onbetaalde concepten van klanten 365 dagen; inlogcodes 2 dagen.
- **Betalen:** via Mollie, omdat die in Nederland iDEAL en andere methoden via één koppeling aanbiedt. Welke methoden beschikbaar zijn, bepaal je in je Mollie-account.
- **Muziek:** de klant uploadt een eigen MP3- of M4A-bestand en bevestigt de rechten. De muziek start nooit vanzelf. In de voorbeelden klinkt een eenvoudige, zelf gegenereerde melodie (geen bestaande muziek).
- **Beelden en lettertypen:** de voorbeeldfoto's in de uitnodigingen zijn eigen abstracte afbeeldingen (`tools/generate_demo_images.py`). De sfeerbeelden, merkbeelden en tegels van de website zijn ook eigen werk (`tools/merkbeelden/`): getekende sfeerbeelden en schermafbeeldingen van de echte voorbeelduitnodigingen. Er zijn geen stockfoto's of foto's van echte mensen gebruikt. De lettertypen zijn open source (OFL) en staan op de eigen server, zodat er geen verzoeken naar Google Fonts gaan.
- **Juridische teksten:** privacyverklaring en voorwaarden zijn gemarkeerd als concept en moeten nog juridisch worden gecontroleerd en aangevuld met bedrijfsgegevens.
- **AI:** optioneel. Het standaardproces werkt volledig zonder AI. De AI-hulp gebruikt alleen wat de klant invulde en verzint geen gegevens; de klant beslist zelf over elk tekstvoorstel. Bij extra wensen maakt AI alleen een interne inschatting voor de eigenaar, zonder toezeggingen. De klant krijgt alleen een ontvangstbevestiging.

## Nieuwe vormgeving (voorbeeldfoto)

De eigenaar leverde een voorbeeldfoto van de gewenste website (kop, hero met foto en zwevende kaart, tegels per gelegenheid, "Zo werkt het" in vier stappen, een donker blok "Meer dan een uitnodiging", populaire ontwerpen, een review en "Liever iets unieks?"). De website volgt die opbouw, kleuren en letters. Bewust anders:

| In de voorbeeldfoto | In Vaylide | Waarom |
|---|---|---|
| Kop "Bijzondere momenten verdienen een bijzondere uitnodiging" | "Een bijzondere dag verdient een *bijzondere* uitnodiging." in dezelfde opmaak | Deze kop en de knoppen "Bekijk de ontwerpen" en "Maak jouw uitnodiging" zijn vastgelegd in de opdracht |
| Foto's van een bruidspaar, ringen, ballonnen, een vrouw met laptop | Eigen sfeerbeelden (gouden licht, groen, papier) en schermafbeeldingen van de echte voorbeelduitnodigingen | De foto's uit de voorbeeldfoto zijn niet los beschikbaar, te klein en de rechten zijn onbekend. Alle beelden zijn te vervangen door eigen foto's met dezelfde bestandsnaam (zie `tools/merkbeelden/README.md`) |
| Knop "Bekijk video" | Knop "Bekijk de ontwerpen"; de afspeelknop op de kaart opent het werkende voorbeeld | Er is geen video |
| Review met vijf sterren ("Sanne & Tim") | Weggelaten | Geen verzonnen reviews |
| "Populaire ontwerpen", hartjes om te bewaren | "Onze ontwerpen", zonder hartjes | Er zijn geen cijfers over populariteit en geen bewaarlijst |
| "Direct online", "Unieke ontwerpen" | "Automatisch online", "Stijlvolle ontwerpen" | Publiceren gebeurt pas na een bevestigde betaling; meerdere klanten kunnen hetzelfde ontwerp kiezen |
| Tegel "Evenement" | Tegel "Verloving" | Vaylide heeft deze zes gelegenheden: bruiloft, verloving, verjaardag, jubileum, babyshower en zakelijk |
| Kenmerken "Cadeautip", "Foto's & video's", "Persoonlijk design" | "Programma", "Foto's", "Kleurkeuze" | Alleen wat echt kan: praktische info (zoals een cadeautip) kan wel, maar video niet, en per ontwerp kies je uit drie of vier kleurvarianten |
| "Wij helpen je graag verder" | "We bekijken hem persoonlijk en je krijgt eerst een voorstel" | Geen toezegging over maatwerk zonder akkoord van de eigenaar |
| Menu-items Inspiratie en Over ons, zoeken en winkeltas | Nieuwe pagina's Inspiratie (voorbeeldteksten en tips) en Over ons (zonder verzonnen verhaal of cijfers), een zoekpagina, en de tas opent Mijn Vaylide | Zo werkt elk onderdeel uit de kop echt |

## Uitbreiding: 30 nieuwe ontwerpen

Op verzoek van de eigenaar ("een stuk of 30, met verschillende designs, verdeeld over de categorieën") zijn er 30 ontwerpen bijgekomen: **vijf per gelegenheid**. Samen met de eerste drie zijn het er 33.

**Aanpak.** Dertig losse ontwerpen met elk eigen HTML zouden lastig te onderhouden zijn en de kans op fouten in toegankelijkheid vergroten. Daarom delen ze één opbouw, **Atelier** (`designs/_atelier/v1/`), met tien openingen (sinds ronde 5 elf), negen koppen, zes soorten secties, vijf kopstijlen, vijf naamstijlen, vijf datumstijlen, vijf fotovormen, zeven achtergrondstructuren en twintig versieringen. Elk ontwerp is een eigen combinatie daarvan met eigen letters en kleuren, en soms eigen accenten in `style.css`. De beschrijving van alle 30 staat in `tools/atelier/specs.py`; `tools/atelier/ontwerpen.py` schrijft daaruit de ontwerpmappen. Zo blijven gedrag en toegankelijkheid (minder beweging, toetsenbord, vangnet zonder script) voor alle ontwerpen gelijk, en is een nieuw ontwerp een kwestie van kiezen en kleuren (zie `docs/HANDLEIDING.md`).

| Gelegenheid | Ontwerp | Opening | Stijl | Ook geschikt voor |
|---|---|---|---|---|
| Bruiloft | Eucalyptus | Vouwkaart | Salie, zacht papier, sierlijke letters | verloving, jubileum |
|  | Gatsby | Gordijn | Zwart en goud, art deco, strakke hoofdletters | jubileum, zakelijk evenement |
|  | Rozentuin | Envelop met zegel | Zacht roze, bloemen, sierlijk handschrift | verloving, babyshower |
|  | Lijnenspel | Zachte sluier | Zwart-wit, grote letters, veel witruimte | verloving, zakelijk evenement |
|  | Zuiden | Cadeaulint | Terracotta en oker, zon, linnen | verjaardag, jubileum |
| Verloving | Ja-woord | Cadeaulint | Champagne, monogram, ringen | bruiloft |
|  | Polaroid | Polaroid | Kraftpapier, polaroids, handschrift | verjaardag, jubileum |
|  | Onder de sterren | Sterrenhemel | Middernachtblauw, sterren, maan | bruiloft, jubileum |
|  | Pampas | Zachte sluier | Zand, pampasgras, linnen | bruiloft, babyshower |
|  | Monogram | Schuifpaneel | Marine, strak, genummerd | bruiloft, zakelijk evenement |
| Verjaardag | Confetti | Confetti | Kleurrijk, confetti, groot getal | babyshower, zakelijk evenement |
|  | Neonnacht | Zachte sluier | Donker, neonlicht, gloeiende letters | zakelijk evenement |
|  | Ballonfeest | Ballonnen | Pastel, ballonnen, ronde vormen | babyshower |
|  | Glitter & goud | Cadeau (was: gordijn) | Zwart en goud, fonkeling, glamour | jubileum, zakelijk evenement |
|  | Tropisch | Vouwkaart | Jungle, palmbladeren, zomer | bruiloft, zakelijk evenement |
| Jubileum | Lauwerkrans | Envelop met zegel | Goud en ivoor, lauwerkrans, klassiek | bruiloft, verjaardag |
|  | Zilveren feest | Gordijn | Zilver, kader, ingetogen chic | bruiloft |
|  | Gouden jaren | Vouwkaart | Ivoor en goud, groot getal, sierlijk | verjaardag |
|  | Door de jaren | Polaroid | Sepia, typemachine, tijdlijn | verjaardag, zakelijk evenement |
|  | Robijn | Cadeaulint | Robijnrood, ringen, cursief | bruiloft, verjaardag |
| Babyshower | Wolkje | Ballonnen | Zachtblauw, wolkjes, rond | verjaardag |
|  | Maanlicht | Sterrenhemel | Nachtblauw of lavendel, maan, sterren | verloving |
|  | Regenboog | Cadeau (was: zachte sluier) | Aardetinten, regenboog, zacht | verjaardag |
|  | Lentebloesem | Envelop met zegel | Bloesem, kader, handschrift | bruiloft, verloving |
|  | Stipjes | Cadeau (was: confetti) | Stippen, kleurband, speels | verjaardag |
| Zakelijk evenement | Strak zakelijk | Schuifpaneel | Marine, strak, professioneel | jubileum |
|  | Gala | Gordijn | Zwart en champagne, fluweel, avond | bruiloft, jubileum |
|  | Congres | Schuifpaneel | Blauw, tijdlijn, overzichtelijk | jubileum |
|  | Borrel | Vouwkaart | Koraal, golven, ontspannen | verjaardag |
|  | Mijlpaal | Cadeaulint | Grafiet en goud, groot getal, krachtig | jubileum |

**Keuzes en aannames:**

- Elk ontwerp is gemaakt voor één gelegenheid (die bepaalt de volgorde in de collectie en het standaardvoorbeeld) en is ook te kiezen voor één of twee andere, waar de stijl dat toelaat.
- **Drie kleurvarianten** per ontwerp (de eerste drie ontwerpen hebben er vier). Alle 90 varianten zijn gecontroleerd op contrast: tekst minimaal 4,5:1 op elke achtergrond, ook op het openingsscherm. Dat gebeurt bij het schrijven van een ontwerp en in de tests.
- **Letters**: 23 extra open-source lettertypen (OFL, licenties in `static/fonts/`), op de eigen server. Een ontwerp laadt alleen zijn eigen letters. Sierletters die klein slecht lezen (zoals Italiana en Abril Fatface) worden alleen groot gebruikt; ondertitel, welkomsttekst en cijfers krijgen dan een rustiger letter.
- **Voorbeeldbeelden**: 15 nieuwe eigen, getekende illustraties (sterrenhemel, confetti, palmbladeren, zijde, stadslicht, enzovoort) in dezelfde stijl als de bestaande, zodat de voorbeelden per ontwerp verschillen. Geen stockfoto's.
- **Kaartbeelden** in de collectie tonen bij de nieuwe ontwerpen de geopende uitnodiging (daar zitten kop en versiering), bij de eerste drie het openingsscherm.
- **Zakelijk evenement** heeft een extra, optioneel veld "Aantal jaar", zodat een ontwerp als Mijlpaal bij een bedrijfsjubileum het getal groot kan tonen. Zonder getal tonen zulke ontwerpen de initialen.
- **Website**: de homepage licht drie ontwerpen uit (`HOME_DESIGNS` in `core/content.py`) en noemt het aantal, en de tegels per gelegenheid tonen een nieuw ontwerp voor die gelegenheid; de collectie zet bij een filter eerst de ontwerpen die voor die gelegenheid zijn gemaakt; een ontwerppagina toont drie andere ontwerpen voor dezelfde gelegenheid; bij het samenstellen worden de ontwerpen op de gekozen gelegenheid gefilterd.
- Net als de eerste drie zijn deze ontwerpen **niet vergeleken met de referentiesites of de schermopname** (zie hieronder).

## Ronde 5: effecten en beweging

De vraag van de eigenaar: "al die kaarten die we nu hebben op het platform echt zo speciaal mogelijk maken, met effecten en bewegende dingen: echt eyecatchers, zodat je er een wilt hebben."

**Aanpak.** Eén gedeelde effectenlaag voor alle 33 ontwerpen (`invitations/static/invitations/effects.js` en `effects.css`), waaruit elk ontwerp in zijn manifest een eigen combinatie kiest (`effects`, keuzes in `catalog/effects.py`, uitleg in `docs/HANDLEIDING.md` onder "Effecten"). Zo gelden toegankelijkheid, snelheid en de knop om beweging stil te zetten overal hetzelfde. Er zijn geen externe bibliotheken of diensten bij gekomen.

- **Sfeer**: zwevende deeltjes op het openingsscherm en achter de tekst, getekend op een canvas. 23 soorten: bloemblaadjes, bloesem, blaadjes, lauwerblaadjes, pluimen, confetti, hartjes, ballonnen met touwtjes, zeepbellen met een regenboogrand, champagnebubbels, zachte lichtjes, stippen, stofjes, zonnestofjes, neonvormen, lijnvormen, wolkjes, goudstof, glitter, een sterrenhemel met vallende sterren, een netwerk, een lichtgolf over een puntjesraster en filmkorrel met krasjes. De deeltjes nemen de kleuren van de gekozen kleurvariant over.
- **Knal** op het moment dat de uitnodiging opengaat, vanuit het zegel, de strik of de knop: onder meer een regen van bloemblaadjes, twee confettikanonnen, vonken met glanzende confetti, sterrenstof, een wolk hartjes, een lucht vol ballonnen, stralende lichtlijnen, een champagneknal en een cameraflits.
- **Feestje na aanmelden**: als een gast "Ja, ik kom" invult, volgt een uitbarsting in de stijl van het ontwerp. In het voorbeeld is dat ook te zien; de melding zegt daar nog steeds duidelijk dat het antwoord niet is opgeslagen.
- **Openingen**: de envelop zweeft en het zegel pulseert, bij openen breekt het zegel en komt er licht uit de envelop; de vouwkaart gluurt af en toe open; het gordijn ademt en achter het doek wacht een spotlicht; de strik wiebelt en over het lint glijdt een glans; de sluier drijft; de maan gloeit; het schuifpaneel krijgt een lichtstreep en een pijltje dat de weg wijst; de polaroid zweeft. Avondgoud krijgt een lichtbundel door de kier van de deuren en een glans die rond het medaillon loopt, Puur moment een lichtstreep over het doorschijnende vel.
- **Cadeau** (nieuwe opening, op verzoek van de eigenaar: "En ik wil dat het mooi uitpakt. En flop, cadeautjes. Um, bedenk het maar. Ik wil dat erin hebben."; "flop" is gelezen als "plof"): een ingepakte doos in de kleuren van het ontwerp, met stippen, glitter of strepen op het papier. In rust springt de doos af en toe even op, alsof er iets in zit, en wiebelt de strik. Bij het openen schudt de doos, gaat de strik los, springt het deksel er met een plof af, komt er licht uit de doos en vliegen de cadeautjes er in een fontein uit, met confetti en glinsters. Ook het nieuwe effect **cadeautjes** is los te kiezen: als sfeer (vallende cadeautjes), bij het openen en als feestje na aanmelden. Glitter & goud, Regenboog en Stipjes openen nu als cadeau; Stipjes heeft ook vallende cadeautjes als sfeer, en bij Ballonfeest volgen na "Ja, ik kom" cadeautjes.
- **Kop na het openen**: de onderdelen verschijnen na elkaar, al terwijl het openingsscherm vervaagt. De versiering tekent zichzelf, de namen komen uit de mist, worden "geschreven", springen tevoorschijn of gaan aan als neon; bij goud en zilver glijdt er af en toe een lichtstreep over de namen (folie). Een groot getal telt op (30, 40, 10), foto's openen in een cirkel of boog en zoomen daarna heel langzaam in.
- **Scrollen**: secties verschijnen op vijf manieren (omhoog, uit de mist, zoom, kanteling, afwisselend links en rechts); onderdelen binnen een sectie komen na elkaar, lijnen bij koppen en de tijdlijn tekenen zich, de cijfers van de afteller klappen om.
- **Website**: de kaarten in de collectie kantelen mee met de muis, er glijdt een glansstreep over bij aanwijzen en één keer als ze in beeld komen, en onder elke kaart staat de sfeer ("Envelop met zegel · bloemblaadjes"). Op de ontwerppagina staat een zin over de effecten. De kaartbeelden zijn opnieuw gemaakt en tonen de effecten.

Per ontwerp:

| Ontwerp | Sfeer | Bij het openen | Na aanmelden | Namen | Extra |
|---|---|---|---|---|---|
| Liefde op papier | Bloemblaadjes | Bloemblaadjes | Hartjes | geschreven | inzoomende foto's, kantelen met de muis, vonkje bij een tik |
| Avondgoud | Goudstof | Vonken en glanzende confetti | Vonken en glanzende confetti | folieglans | lichtstralen, inzoomende foto's, kantelen met de muis |
| Puur moment | Zachte lichtjes | Zachte lichtjes | Zachte lichtjes | uit de mist | inzoomende foto's |
| Eucalyptus | Blaadjes | Opwaaiende blaadjes | Opwaaiende blaadjes | geschreven | inzoomende foto's, kantelen met de muis |
| Gatsby | Goudstof | Vonken en glanzende confetti | Vonken en glanzende confetti | folieglans | lichtstralen, kantelen met de muis |
| Rozentuin | Bloemblaadjes | Bloemblaadjes | Hartjes | geschreven | inzoomende foto's, kantelen met de muis, vonkje bij een tik |
| Lijnenspel | Stofjes in het licht | Lichtlijnen | Lichtlijnen | uit de mist | inzoomende foto's |
| Zuiden | Zonnestofjes | Bloemblaadjes | Bloemblaadjes | uit de mist | lichtstralen, inzoomende foto's, kantelen met de muis |
| Ja-woord | Champagnebubbels | Champagneknal | Hartjes | folieglans | kantelen met de muis, vonkje bij een tik |
| Polaroid | Hartjes | Flits | Hartjes | geschreven | vonkje bij een tik |
| Onder de sterren | Sterrenhemel | Sterrenstof | Sterrenstof | uit de mist | inzoomende foto's |
| Pampas | Pluimen | Opwaaiende pluimen | Opwaaiende pluimen | uit de mist | inzoomende foto's, bewegende kleurvlekken |
| Monogram | Lijnvormen | Lichtlijnen | Vonken en glanzende confetti | uit de mist | – |
| Confetti | Confetti | Confettikanonnen | Confettikanonnen | springt tevoorschijn | vonkje bij een tik |
| Neonnacht | Neonvormen | Neonvonken | Neonvonken | neon gaat aan | vonkje bij een tik |
| Ballonfeest | Ballonnen | Ballonnen | Cadeautjes | springt tevoorschijn | vonkje bij een tik |
| Glitter & goud | Glitter | Cadeautjes (uit het cadeau) | Vonken en glanzende confetti | folieglans | discolicht, vonkje bij een tik |
| Tropisch | Bloemblaadjes | Bloemblaadjes | Confetti | uit de mist | inzoomende foto's, kantelen met de muis |
| Lauwerkrans | Lauwerblaadjes | Vonken en glanzende confetti | Vonken en glanzende confetti | folieglans | kantelen met de muis |
| Zilveren feest | Goudstof | Vonken en glanzende confetti | Vonken en glanzende confetti | folieglans | lichtstralen, kantelen met de muis |
| Gouden jaren | Goudstof | Vonken en glanzende confetti | Vonken en glanzende confetti | folieglans | lichtstralen, kantelen met de muis |
| Door de jaren | Filmkorrel | Flits | Confetti | uit de mist | inzoomende foto's |
| Robijn | Bloemblaadjes | Hartjes | Hartjes | folieglans | kantelen met de muis, vonkje bij een tik |
| Wolkje | Wolkjes | Zeepbellen | Zeepbellen | springt tevoorschijn | vonkje bij een tik |
| Maanlicht | Sterrenhemel | Sterrenstof | Sterrenstof | uit de mist | vonkje bij een tik |
| Regenboog | Zeepbellen | Cadeautjes (uit het cadeau) | Cadeautjes | uit de mist | bewegende kleurvlekken, vonkje bij een tik |
| Lentebloesem | Bloesem | Bloesem | Bloesem | geschreven | inzoomende foto's, kantelen met de muis, vonkje bij een tik |
| Stipjes | Cadeautjes | Cadeautjes (uit het cadeau) | Cadeautjes | springt tevoorschijn | vonkje bij een tik |
| Strak zakelijk | Lichtgolf | Lichtlijnen | Lichtlijnen | uit de mist | – |
| Gala | Goudstof | Vonken en glanzende confetti | Vonken en glanzende confetti | folieglans | lichtstralen, inzoomende foto's, kantelen met de muis |
| Congres | Netwerk | Uitwaaierend netwerk | Lichtlijnen | uit de mist | – |
| Borrel | Champagnebubbels | Champagneknal | Champagneknal | springt tevoorschijn | kantelen met de muis, vonkje bij een tik |
| Mijlpaal | Goudstof | Confettikanonnen | Vonken en glanzende confetti | folieglans | lichtstralen |

**Keuzes en aannames:**

- **Aangepast in versie 1, geen versie 2.** De regel is dat een ontwerp via een nieuwe versie verandert, zodat bestaande uitnodigingen niet onverwacht wijzigen. Vaylide staat nog in testmodus en er bestaan geen echte uitnodigingen; de handleiding staat in dat geval toe dat een versie wordt bijgewerkt (`sync_designs --update-manifest`). Een tweede versie van alle 33 ontwerpen zou de eigenaar alleen extra werk in Beheer geven. **Na de livegang** gaan zulke wijzigingen wel via een nieuwe versie. Wie een bestaande ontwikkeldatabase heeft, draait eenmalig `python manage.py sync_designs --update-manifest`.
- **Beweging stilzetten (WCAG 2.2.2).** Beweging die vanzelf start en langer dan vijf seconden doorgaat, moet te pauzeren zijn. Daarom staat er links onder een knop **Beweging** (ook op het openingsscherm), een schakelknop met een vaste naam. Hij zet de deeltjes, alle doorlopende animaties en de afteller stil, en de keuze wordt op dat apparaat onthouden (alleen in de browser, niet op de server). Bij "minder beweging" in het systeem beweegt er niets en is de knop niet nodig.
- **Geen flitsen.** De cameraflits is één enkele flits; neon hapert bij het aangaan hoogstens twee keer in een seconde, ruim onder de grens van drie per seconde.
- **Leesbaarheid.** Deeltjes staan achter de tekst, nooit erover, en achter lopende tekst iets zachter dan op het openingsscherm. De lichtstreep bij folie heeft per kleurvariant een eigen kleur met minstens 3:1 contrast (de namen zijn grote tekst); de tests controleren dat. De inhoud hangt nooit af van een effect: zonder script, met minder beweging of met de knop uit is alles direct zichtbaar.
- **Snelheid.** Deeltjes worden één keer als klein plaatje getekend en daarna alleen verplaatst. Rustig zwevende deeltjes tekenen 30 beelden per seconde (de knal en het feestje 60), achter de tekst op een iets lagere resolutie dan op het openingsscherm. Het tekenen stopt als het vlak niet in beeld is, als het tabblad op de achtergrond staat en als de beweging uit staat; op eenvoudige toestellen (weinig rekenkernen of geheugen) en bij haperend beeld worden het vanzelf minder deeltjes. Gloed wordt vooraf getekend, niet per beeld berekend. Het script is ongeveer 19 kB (gecomprimeerd) en laadt pas na de pagina. Metingen staan in `docs/CONTROLES.md` onder "Belasting door de effecten".
- **Kantelen met de muis** alleen op een computer met muis; op een telefoon zweven de voorwerpen zacht. Een vonkje bij een tik alleen bij speelse ontwerpen, niet bij de zakelijke.
- **Avondgoud** had een eigen script voor fonkelend goud; dat is vervangen door de gedeelde effectenlaag.
- **Liefde op papier**: het zegel is zo aangepast dat de initialen erop beter leesbaar zijn (was een aandachtspunt uit ronde 4).
- Ook deze ronde is **niet vergeleken met de referentiesites of de schermopname** (zie hieronder).
- **Stijlvoorbeeld voor de website**: aan het eind van deze ronde stuurde de eigenaar een schermopname (19 seconden) van een websitesjabloon, "Mariana" van Scrolltide, als voorbeeld voor de indeling van de website. De opname is beeld voor beeld bekeken (het geluid niet); de pagina van de sjabloon zelf was in deze werkomgeving geblokkeerd. Na overleg is besloten **de website te laten zoals hij is**.

## Ronde 6: Vaylide

De eigenaar vroeg eerst: "vierlief moet worden aangepast naar Vaylia met een nieuw logo", met een afbeelding van het logo: een gouden V met een lint en een takje, daaronder VAYLIA en de regel "Your moments starts here.". Op het voorstel om het logo op te splitsen en de Engelse regel weg te laten, antwoordde de eigenaar: "Dat wil ik niet. Ik wil de logo zoals ik hem nu stuur." Kort daarna volgde een nieuw logo met een nieuwe naam: "Dit is het nieuwe logo met de nieuwe naam." Het logo is hetzelfde, met VAYLIDE als naam. De site heet daarom nu **Vaylide**; de tussenstap Vaylia staat nog in de git-geschiedenis.

- **Het logo zoals aangeleverd.** De V, VAYLIDE en de regel eronder staan samen, in dezelfde kleuren en verhoudingen: in de kop en voet van de website, bij het samenstellen, in de klantomgeving, het beheer en de foutpagina's, bovenaan de e-mails en in de deelafbeelding. Alleen de lege crèmekleurige achtergrond is doorzichtig gemaakt en de lege rand eromheen weggesneden. Op de achtergrondkleur van het origineel is het resultaat gelijk aan het origineel: het grootste verschil is 14 van de 255 kleurstappen, bij een paar honderd losse ruispuntjes van de compressie, ver van het logo, die zijn weggelaten. Hoogte: 72 pixels in de kop (58 op een telefoon), 120 in de voet, 52 bij het samenstellen en in het beheer, 90 in de e-mails. Het bronbestand en het script staan in `tools/logo/`.
- **Iconen.** Het tabblad-icoon is de V uit het logo op de crèmekleur van het origineel (32 en 48 pixels, 192 voor Android), omdat het hele logo op dat formaat niet leesbaar is. Het icoon voor het beginscherm van een iPhone of iPad (180 pixels) toont het hele logo. Het hartlogo uit ronde 3 is weg; alleen op het zegel van de deelafbeelding voor uitnodigingen en op de standaardafbeelding voor nieuwe ontwerpen staat het hartje nog als versiering.
- **De naam.** Overal waar bezoekers, klanten, gasten of de eigenaar de naam zien, staat nu Vaylide: paginatitels, teksten, "Mijn Vaylide", de e-mails en hun afzendernaam, de regel onder de uitnodigingen ("Digitale uitnodiging gemaakt met Vaylide"), agenda-bestanden, de omschrijving bij de betaling, het beheer, het noodbeheer en de opdrachten voor de AI-hulp. Het e-mailadres in testmodus is `hallo@vaylide.test`.
- **Bewust gebleven: technische namen die bezoekers niet zien.** De instellingen `VIERLIEF_…`, de namen van cookies (`vierlief_sessie`, `vierlief_csrf`, `vierlief_antwoord`), sessie- en opslagsleutels (zoals `vierlief-beweging`), de cachetabel, het databasebestand `data/vierlief.sqlite3`, het stijlbestand `static/css/vierlief.css` en de testaccounts (`controle@vierlief.test`). Omzetten raakt de configuratie van elke installatie en laat bestaande sessies en keuzes van gasten vervallen; het staat als open punt in `docs/OVERDRACHT.md`.
- **Een nieuwe migratie.** De naam "Vaylide-team" in de keuzelijst bij versies staat in een nieuwe migratie (`invitations/migrations/0002_merknaam.py`); de eerste migratie is niet aangepast. De tabellen veranderen niet. (Voor de tussenstap Vaylia heette die migratie even `0002_merknaam_vaylia`; hij is hernoemd omdat er nog nergens een installatie van bestaat.)
- **Domein.** De eigenaar vroeg ook om de site "meteen online op mijn nieuwe domeinnaam. Van deze vaylinde.com". Het domein werd daar met een n geschreven, het logo zegt Vaylide zonder n; op de vraag welke spelling klopt, antwoordde de eigenaar: "domein naam is vaylide.com". `.env.example` en het stappenplan gebruiken `vaylide.com`. Online zetten kon vanuit de werkomgeving niet: daarvoor zijn een hostingaccount (een betaalde dienst, de keuze van de eigenaar) en toegang tot de DNS-instellingen van het domein nodig. Het stappenplan staat in `docs/ONLINE.md`.
- **Wachtwoord voor een testversie online.** In testmodus staat de inlogcode op het scherm, zodat je zonder e-mail kunt proberen. Online zou dat betekenen dat iedereen met elk e-mailadres kan inloggen. Daarom is er een optioneel wachtwoord voor de hele site (`VIERLIEF_PREVIEW_PASSWORD`, het inlogvenster van de browser), standaard uit. De controle door de hosting (`/healthz`), de openbare opmaak en beelden, de taken voor een externe cron en de meldingen van de betaalprovider blijven zonder wachtwoord bereikbaar; na 30 foute pogingen in vijf minuten volgt een pauze.
- **Online zetten: voorstel Render.** Op de vraag om de site online te zetten antwoordde de eigenaar met "ja dat is goed doe maar". Een repository aanmaken lukte vanuit de werkomgeving niet (GitHub gaf geen toestemming), en een hostingaccount afsluiten kan alleen de eigenaar. Daarom staat de aanbevolen route klaar: `render.yaml` voor Render (servers in Frankfurt, een blijvende schijf voor foto's, PostgreSQL, testmodus met wachtwoord), met de stappen in `docs/ONLINE.md`. De app herkent het tijdelijke Render-adres (`RENDER_EXTERNAL_HOSTNAME`), zodat de site werkt voordat het domein is gekoppeld. Een klok voor het opnieuw proberen van taken en de bewaartermijnen komt er pas bij voor live; voor de testversie lopen taken direct na een testbetaling.
- **Eigen repository.** De eigenaar maakte `bootsman075-ops/vaylide.nl` aan, openbaar; op de vraag of dat zo mocht blijven, koos de eigenaar "Openbaar is goed". Vóór het versturen is de hele geschiedenis doorzocht op wachtwoorden en sleutels (niets gevonden). De eerste commit van de repository (een README van één regel) is samengevoegd; er is niets overschreven.
- **De website zelf** is verder niet veranderd.

## Ronde 7: Gouden licht

De eigenaar stuurde de schermopname `Envelop.mp4` (14 seconden, een telefoon met een envelop die opengaat) en vroeg: "Kan je deze envelop namaken? Voor een intro van een kaart?" Het resultaat is een nieuw volledig eigen ontwerp, **Gouden licht** (`designs/gouden-licht/v1/`), met vier kleurvarianten (Bordeaux, Nachtblauw, Smaragd, Aubergine, steeds met goud).

**Wat ik in de opname zag.** Ik heb de opname bekeken aan de hand van stilstaande beelden: twee per seconde als overzicht, en acht beelden op de belangrijke momenten (rust, glans, lichtdoorbraak, overspoeling, kaart). Het geluid heb ik niet kunnen beluisteren; de opname heeft een geluidsspoor, maar daar is niets van overgenomen.

1. Een diepe bordeauxrode envelop met vier kleppen die in het midden samenkomen, reliëfbloemen in dezelfde kleur en een blozend lakzegel met initialen.
2. De bloemen lichten goud op, als een glans die over het oppervlak gaat.
3. Na een tik tilt de bovenklep op (de binnenkant is zacht roze) en de andere kleppen wijken een heel klein stukje. Door de naad onder het zegel breekt warm licht met stralen, en de bloemen krijgen een gouden rand.
4. Het licht overspoelt het scherm. Daarin verschijnen de namen en de kaart.

**Wat ik gemaakt heb.**

- **Eigen tekeningen.** De bloemen (rozen, bladeren, knoppen) zijn zelf getekend uit krommen door `tools/gouden-licht/maak_bloemen.py`; er is niets uit de opname of van elders overgenomen. De uitkomst staat in `designs/gouden-licht/v1/bloemen.html` en een test controleert dat het bestand precies is wat het script maakt.
- **Opbouw.** Vier kleppen in een gedeelde tekening van 500 x 800, zodat de bloemen met hun klep meebewegen. Per klep vier lagen: schaduw en rand (het reliëf), een lichtstreep die af en toe over de bloemen glijdt, en de gouden gloed bij het openen. Het licht is een gloeiend midden met stralen (een kegelverloop), de overspoeling een zich verbredende lichtcirkel die overgaat in het papier van de uitnodiging.
- **Tijdlijn bij een tik** (3,6 s): 0,25 s bovenklep omhoog; 0,5 s de bloemen lichten op; 0,6 s het licht breekt door; 0,7 s de kleppen wijken; 1,2 s de knal (vonken, uit het bestaande effectenscript) vanuit het zegel; 1,8 s het zegel vervaagt; 2,2 s het licht overspoelt het scherm; 2,8 s de namen verschijnen; 3,0 s het openingsscherm vervaagt.
- **Uitnodiging zelf.** Na het licht staat een zachte ivoren kaart met bordeaux, ink en goud, in dezelfde opbouw als Liefde op papier (handgeschreven namen, boog met foto, programma, aanmelden), voor bruiloft, verloving, jubileum en verjaardag.
- **Beweging volgens de vaste regels.** Het zegel ademt, de lichtstreep glijdt over de bloemen en de envelop zweeft zacht, alleen onder `.fx-motion` en met `animation-play-state: var(--fx-play, running)`; bij 'minder beweging' of na een tik op **Beweging** opent de uitnodiging rustig binnen een kwart seconde. Er is één knal en geen flits: het licht groeit geleidelijk.

**Bewust anders dan de opname.**

- De opname is een volledig scherm op een telefoon; de envelop is hier een staande envelop (5 : 8) in het midden van het scherm, zodat hij ook op een computerscherm goed staat.
- De kaart na het licht is een eigen, zachte ivoren kaart zonder de boog en zwanen uit de opname. Dat waren illustraties van het voorbeeld in de opname en horen niet bij Vaylide.
- Het zegel is een geometrisch lakzegel met de initialen als ingedrukt midden (zoals bij Liefde op papier), geen nagemaakt reliëf.
- De knal bij het openen valt op het moment dat het licht doorbreekt (1,2 s). `e2e/effecten.cjs` wacht daarom nu op de waarde van `data-fx-delay` in plaats van een vaste 650 ms.

**Technische keuzes.**

- De initialen in het zegel zijn gegenereerde inhoud (`data-mono`, `::before`) en geen tekst in de knop, zodat de knop alleen "Open de uitnodiging" heet (axe-regel `label-content-name-mismatch`; dezelfde melding komt bij Liefde op papier voor in de variant Bordeaux & goud). `::after` is bezet door de pulsring uit `effects.css`.
- `designs/_atelier/v1/` is niet aangeraakt: dit is een eigen ontwerp in een eigen map. Een tweede ontwerp met hetzelfde mechanisme is dus een kopie, geen aanpassing van gedeelde onderdelen.
- Het ontwerp staat op volgorde 15 (tussen Liefde op papier en Avondgoud); dat is aan te passen in Beheer → Ontwerpen.

## Referenties en schermopname

Hier staat eerlijk wat wel en niet is bekeken.

- **Websites** (webgencyinvitations.com, /order en /thesacredgarden, template3.tilda.ws) en de **twee Instagram-reels**: in deze werkomgeving geblokkeerd door het netwerkbeleid (403 bij de proxy). Aan het begin geprobeerd en aan het eind opnieuw, met hetzelfde resultaat. **Ik heb deze pagina's niet gezien.** Via een zoekmachine kwamen alleen korte samenvattingen van zoekresultaten binnen: Webgency biedt kant-en-klare ontwerpen die met eigen kleuren, foto's en tekst worden aangepast, naast maatwerk, en "The Sacred Garden" is een van die ontwerpen. Dat is tweedehands informatie; details, teksten en prijzen van Webgency zijn niet gebruikt.
- **Schermopname** `Envelop.mp4` (ronde 7): wel ontvangen en beeld voor beeld bekeken; zie "Ronde 7: Gouden licht". De eerdere schermopname `Referentie_Vierlief_3_Voorbeelden.mp4` (drie voorbeelden): niet ontvangen in deze sessie. Er was geen bijlage en het bestand staat nergens op de schijf. Begin- en eindtijden, openingsanimaties, overgangen en timing van de drie filmpjes zijn dus **niet** geanalyseerd.
- **Gevolg:** de drie ontwerpen volgen de eigen richtingen uit de opdracht en zijn **nog niet vergeleken met de opname of de referentiesites**:

| Ontwerp | Richting | Opening |
|---|---|---|
| Liefde op papier | Romantisch en zacht: handgeschreven namen, fijne lijntekeningen, zachte kleuren | Envelop met persoonlijk lakzegel (initialen); na een tik opent de klep en schuift de kaart naar buiten |
| Avondgoud | Donker, feestelijk en elegant: champagnegouden lijnen, medaillon, fonkelend licht | Gouden dubbele deur die openzwaait |
| Puur moment | Rustig en modern: veel witruimte, grote foto, strakke letters, genummerde onderdelen | Doorschijnend vel dat omhoog schuift, waarna de foto scherp wordt |

Elk van deze drie ontwerpen heeft vier kleurvarianten, werkt voor meerdere gelegenheden en is volledig bruikbaar zonder animatie. Er is ondersteuning voor minder beweging, voor bediening met het toetsenbord, en een vangnet dat de uitnodiging na 7 seconden toont als het script niet laadt.

**Bewuste afwijkingen en onbekende onderdelen.** Omdat de referenties niet te bekijken waren, is niet vast te stellen waar Vaylide ervan afwijkt. Onbekend zijn onder meer: de exacte timing en volgorde van de openingsanimaties in de filmpjes, welke effecten alleen in de montage zitten, de volledige vragenlijst en bestelstappen van Webgency, en het gedrag van muziek en formulieren in de voorbeelden.

**Vervolgstap:** sta de domeinen toe in de netwerkinstellingen van de omgeving en stuur de schermopname opnieuw mee, bijvoorbeeld als bestand in de repository. Dan volgt een vergelijkingsronde per filmpje: tijden, opening, overgangen en interacties. Aanpassingen komen als nieuwe ontwerpversie (`v2`), zodat bestaande uitnodigingen niet veranderen.

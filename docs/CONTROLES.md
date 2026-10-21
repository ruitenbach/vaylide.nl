# Uitgevoerde controles

Hier staan alleen controles die echt zijn uitgevoerd, met hoe en met welk resultaat. Wat niet gecontroleerd kon worden, staat onderaan.

## Controle 1: volledige werking

**160 geautomatiseerde tests** (`python manage.py test tests`), laatst gedraaid op de definitieve code van ronde 7 (kerstkaarten), alle geslaagd:

- lokaal op SQLite;
- op PostgreSQL 16 (lokale database) in ronde 5, toen met 132 tests, op de stand vlak vóór de laatste kleine wijziging van die ronde (kaarten zonder dubbel woord, zoals "Confetti · confetti"). Die wijziging, ronde 6 en ronde 7 zijn alleen op SQLite getest;
- in de Docker-image (Python 3.11), na een build vanaf nul: in ronde 2 (toen 92 tests). Daarna is de image niet opnieuw gebouwd; er zijn geen afhankelijkheden of instellingen veranderd, en het datamodel alleen in ronde 7 met een migratie die de keuzelijst van de gelegenheid uitbreidt met Kerst (de nieuwe ontwerpen en de effecten zijn bestanden, en het extra veld "Aantal jaar" staat in de bestaande inhoud van een uitnodiging).

| Uit de opdracht | Test(s) |
|---|---|
| Ontwerp → gegevens → upload → voorbeeld → testbetaling → publicatie → link → gast meldt zich aan → klant ziet het antwoord | `test_flow.FullJourneyTests.test_design_to_guest_response_seen_by_customer` (ook de gast-aanmelding zonder JavaScript) |
| Voortgang bewaren en hervatten | `ResumeProgressTests`: concept zonder account blijft bewaard en wordt na verificatie aan het account gekoppeld; de inloglink werkt maar één keer en pas na een klik; foute codes worden geweigerd en het aantal pogingen is beperkt |
| Ongeldige formulierinvoer | `InvalidInputTests`: verplichte velden (invoer blijft staan), ongeldige formaten, datum te ver weg, eindtijd zonder begintijd, programmaregels, telefoonnummer, aanmelddeadline na het evenement, keuzevraag met te weinig opties, onvolledige bestelling, onbekend pakket |
| Afgebroken en mislukte betaling | `test_cancelled_payment_keeps_design_and_allows_retry`, `test_failed_and_expired_payments_do_not_publish`, `test_return_page_alone_never_publishes` |
| Herhaalde betalingsmelding | `test_repeated_webhooks_do_not_duplicate_anything` (geen dubbele bestelling, publicatie of e-mail); ook: een vervalste melding (`test_webhook_cannot_fake_a_payment`), een afwijkend bedrag, een dubbele betaling, en de Mollie-koppeling met een gesimuleerde API |
| Mislukte publicatie en e-mail | `test_processing`: de betaalde bestelling blijft staan, de status is zichtbaar, het herstel gaat automatisch, de eigenaar krijgt een melding na herhaald falen, en een mislukte e-mail blokkeert de publicatie niet (de link staat al in Mijn Vaylide) |
| Wijzigen na publicatie | `EditAfterPublicationTests`: pas live na publiceren, op dezelfde link; publiceren wordt geblokkeerd als verplichte gegevens ontbreken |
| Extra wensen | `test_wishes`: alleen een ontvangstbevestiging (zonder prijs of toezegging), een interne inschatting die de klant niet ziet, een voorstel met en zonder prijs, akkoord, betaling, in uitvoering, afgerond, interne notities, ongeldige bijlagen |
| Afgeschermde toegang tussen klanten | `CustomerIsolationTests`: overal een 404 bij een uitnodiging van een ander, ook bij uploaden en publiceren |
| Onbevoegde toegang tot gastenlijsten en uploads | `GuestPrivacyTests` en `MediaAccessTests`: een gast ziet geen andere antwoorden, een wijzigingslink opent alleen het eigen antwoord, alleen foto's van gepubliceerde uitnodigingen zijn zichtbaar, offline betekent alles dicht |
| 30 nieuwe ontwerpen (ronde 4) | `test_atelier`: 30 ontwerpen, vijf per gelegenheid, allemaal ingelezen en zichtbaar; geldige keuzes; contrast van alle 90 kleurvarianten (minimaal 4,5:1); eigen kaart- en voorbeeldbeelden; weergave voor elke gelegenheid en in elke kleur; lange namen en lange woorden krijgen kleinere letters; het grote getal (leeftijd of aantal jaren) en de terugval op initialen; aantal jaren bij zakelijke evenementen; de hele reis samenstellen → voorbeeld → betalen → gepubliceerde uitnodiging met een nieuw ontwerp; homepage, collectie, ontwerppagina, samenstellen en zoeken |
| Effecten (ronde 5) | `test_effects`: alle 33 ontwerpen hebben geldige effecten; een onbekend effect wordt geweigerd bij het inlezen van een ontwerp; de instellingen worden klassen en kenmerken op de pagina; elk voorbeeld laadt de effecten en de knop **Beweging** (verborgen tot het script draait), zonder extra inline scripts (CSP); een ontwerp zonder effecten werkt gewoon; Avondgoud laadt zijn oude eigen script niet meer; de glans over de namen houdt minstens 3:1 contrast in alle kleurvarianten; de ontwerppagina en de kaarten beschrijven de effecten; de cadeau-opening bij Stipjes, Glitter & goud en Regenboog (de doos opent ook bij een tik, maar is geen extra tabstop en wordt niet voorgelezen), het effect cadeautjes en de tekst op de kaart |
| Merk Vaylide (ronde 6) | `BrandTests` in `test_site`: het logo staat in de kop met "Vaylide" als tekst voor schermlezers en als naam van de link; de iconen en de deelafbeelding bestaan en worden gebruikt, het oude hartlogo is weg; op 14 pagina's (website, inloggen, samenstellen, een voorbeeld en de 404) staat nergens meer "Vierlief" of "Vaylia"; een e-mail begint met het logo en noemt alleen Vaylide |
| Wachtwoord voor een testversie online (ronde 6) | `test_preview`: standaard uit; aan vraagt elke pagina het wachtwoord (401 met het inlogvenster van de browser, zonder inhoud van de site); een fout wachtwoord, een andere gebruikersnaam of een kapotte kop wordt geweigerd; met het goede wachtwoord verschijnt de site; `/healthz` en de taken voor een externe cron blijven bereikbaar; na 30 foute pogingen volgt 429 |
| Kerstkaarten (ronde 7) | `test_kerst` (21 tests): de gelegenheid Kerst overal beschikbaar (samenstellen, collectie, zoeken, homepage en Inspiratie, met de brede tegel) en zonder openstaande migraties; het zegel (Familie Van Dijk wordt D, Sanne & Daan wordt S&D); het nieuwe jaar en de afteller naar eerste kerstdag (van juli tot en met kerstavond); een tekeningetje per programmaonderdeel; een kerstkaart met kerstdiner, een kerstgroet zonder evenement (geen datum, locatie, agenda of aanmelden) en het ontwerp bij andere gelegenheden; de regels bij publiceren; het samenstellen zonder datum, locatie of deadline, en met een half ingevuld evenement wel; een betaalde, gepubliceerde kerstgroet met "kerstkaart" in de paginatitel, de e-mails en de bestelstatus; Winterlicht: kleurvarianten met contrast, alle beelden, het voorbeeld in alle kleuren zonder extra inline scripts of stijlen, de kop onder de voorbeeldbalk, de tekst in het kerstraam die bij veel tekst kleiner wordt, de lichtjes die stilstaan als niemand ze ziet, de lichte envelop (kleine reliëfbeelden, goud pas na het laden); andere voorbeelden houden hun eigen muziek; het effect sneeuw |
| Versieherstel en conflicten | `ConflictTests`, `RestoreTests`, `TemplateVersionPinningTests`: een aanpassing door het team wordt niet stil overschreven, vergrendelde velden blijven staan, publiceren met een verouderde stand wordt geweigerd, een nieuwe ontwerpversie verandert bestaande uitnodigingen niet |

Verder getest: aanmeldingen (dubbel tikken geeft één antwoord, limieten, deadline, capaciteit, verstreken datum, wijzigen en verwijderen, spambescherming, rate limiting, extra vragen per pakket), uploads (EXIF en GPS verwijderd, verkeerde of te kleine bestanden, maximale grootte, audio, te grote verzoeken), weergave (lange namen, lege onderdelen verborgen, tijdzones, alle voorbeelden voor alle gelegenheden, werkt zonder JavaScript), beveiligingsheaders, prijsberekening, bewaartermijnen en accountverwijdering, foutpagina's, handmatige statuswijziging (met logboek), een ontwerp zonder voorbeeldafbeelding, de controle van ontwerpmanifesten, de snelheidsmaatregelen (inline startscript met CSP-hash, compressie van tekst maar niet van beelden of deelverzoeken, een vast aantal databasevragen in Mijn Vaylide), en de nieuwe pagina's: Inspiratie, Over ons en Zoeken. Zoeken vindt vragen, ontwerpen en pagina's, negeert hoofdletters en accenten, kort lange zoektermen in, toont invoer veilig (geen HTML) en staat op `noindex`. Een test controleert dat namen, locaties, e-mailadressen, gastnamen en links van echte uitnodigingen nooit in de resultaten verschijnen.

Daarnaast zijn de klantreis en het beheer tijdens de bouw doorlopen met scripts: publiceren, versies, herstellen, voorstellen en e-mails.

## Controle 2: vormgeving en gebruik

### Hoe

- Een productie-achtige server: `DEBUG` uit, gunicorn, statische bestanden met versiekenmerk (WhiteNoise), testmodus voor betalen en e-mail.
- Chromium via Playwright op **360×740, 390×844, 768×1024 en 1366×900** pixels (`e2e/controle2.cjs`), in ronde 5 in twee of drie runs tegelijk, in ronde 4 in vier parallelle runs, één per schermformaat. De run op 390 pixels liep eerst vast bij het inloggen: de vier runs vroegen tegelijk een inlogcode aan voor hetzelfde testaccount, waarbij een nieuwe code de vorige ongeldig maakt. Het script probeert het inloggen nu opnieuw; de run op 390 pixels is daarna in zijn geheel herhaald.
- Per schermformaat **204 pagina's** (816 in totaal): alle websitepagina's (ook Inspiratie, Over ons en Zoeken met en zonder resultaten), de 404, alle 33 voorbeelden (geopend), 132 testuitnodigingen (vier per ontwerp), de klantomgeving, alle stappen van het samenstellen en de beheeromgeving.
- Testuitnodigingen per ontwerp (`e2e/fixtures.py`):
  - **lang**: zeer lange namen, een lange locatie, adres en contactgegevens, 11 programmaonderdelen, foto's in liggend, staand en vierkant formaat, extra vragen;
  - **minimaal**: geen foto's en geen optionele onderdelen;
  - **verstreken**: een datum in het verleden;
  - **woord** (nieuw): lange woorden in de titel voor de gelegenheid waarvoor het ontwerp is gemaakt, zoals "Nieuwjaarsreceptie", en een getal van drie cijfers.
- Per pagina: een schermafbeelding, horizontaal scrollen, zichtbare onderdelen die buiten beeld steken, tekst die buiten beeld loopt (ook als een omringend vak hem afsnijdt; nieuw in ronde 4), fouten in de browserconsole en mislukte verzoeken. Bewust scrollbare tabellen, menu's en de veegrij met ontwerpen, bijgesneden foto's en tekst die alleen voor schermlezers is, tellen niet mee.
- In ronde 6 liepen de vier schermformaten tegelijk. Alle controles van ronde 6 zijn eerst gedaan op de tussenstap met de naam Vaylia en daarna opnieuw op de definitieve stand met Vaylide; hieronder staan de uitkomsten van Vaylide (bij Vaylia waren ze gelijk: geen bevindingen). De browsercontroles liepen op de stand vlak vóór het optionele wachtwoord voor een testversie en de herkenning van het Render-adres; die staan standaard uit en veranderen niets aan de pagina's.
- Na de laatste twee snelheidsverbeteringen van ronde 5 (discolicht van Glitter & goud, tekenvlakken niet meer bij elk beeld meten; zie "Gevonden en opgelost") zijn de tests, de effectencontrole en Lighthouse voor Glitter & goud opnieuw gedraaid. De browsercontrole, de toegankelijkheidscontrole en de belastingmeting hieronder zijn van de stand vlak daarvoor.
- Sinds ronde 5 staan de effecten tijdens de controles gewoon aan. De controles wachten tot de opening, de entree van de kop en andere eenmalige animaties klaar zijn; doorlopende effecten (zwevende deeltjes, glans) lopen door.

### Resultaat

Ronde 7 (kerstkaarten), op de productie-achtige server (gunicorn, `DEBUG` uit, WhiteNoise, testmodus; lokaal zonder https-omleiding):

- **840 pagina's zonder bevindingen** (210 per schermformaat, op 360, 390, 768 en 1366 pixels breed, vier runs tegelijk): alle websitepagina's (ook de homepage en Inspiratie met de brede kersttegel), alle 34 voorbeelden (geopend), 137 testuitnodigingen (vier per ontwerp, plus een kerstgroet zonder evenement bij Winterlicht), de klantomgeving, het samenstellen en het beheer. Geen horizontaal scrollen, niets buiten beeld, geen afgesneden tekst, geen consolefouten, geen mislukte verzoeken. Deze run liep op de stand vóór de laatste aanpassingen aan Winterlicht (tekst in het kerstraam, lichtjes, lichtere envelop; zie "Gevonden en opgelost"). Winterlicht is daarna op de definitieve stand opnieuw gecontroleerd (`ONTWERPEN=winterlicht`): het voorbeeld en de vijf testuitnodigingen op alle vier schermformaten, **24 pagina's zonder bevindingen**.
- **272 van 272 gedragscontroles geslaagd** (acht per ontwerp, alle 34 ontwerpen): minder beweging (de uitnodiging opent binnen 285 tot 328 ms, zonder lopende animaties), toetsenbord, muziek, het vangnet zonder script, de melding over de tijdzone en de weergave zonder JavaScript. Winterlicht op de definitieve stand opnieuw: 8 van 8.
- **Effecten** (`e2e/effecten.cjs`, op de definitieve stand): **272 van 272 controles geslaagd**, acht per ontwerp voor alle 34 ontwerpen: deeltjes op het openingsscherm, de knal bij het openen (bij Winterlicht sneeuwvlokjes en gouden sterretjes), de sfeer achter de tekst na het openen, het feestje na "Ja, ik kom", geen consolefouten, stilzetten met **Beweging**, de keuze onthouden, en 'minder beweging'.
- **Toegankelijkheid van alle ontwerpen** (`e2e/toegankelijkheid.cjs`, axe-core 4 met WCAG 2.0/2.1 A en AA, plus de contrastcontrole): **212 pagina's**, alle 34 ontwerpen in alle 106 kleurvarianten, dicht en geopend. **0 axe-overtredingen.** Contrast: 0 bevindingen bij de 33 andere ontwerpen. Bij Winterlicht meldde de controle eerst drie pagina's, omdat hij de tekst op de envelop en in het kerstraam vergeleek met de donkere paginakleur: het papier (losse kleppen) en de tekening (een apart beeld) ziet hij niet. Na de aanpassing (de papierkleur ook op de envelop zelf, en `data-tekst-op-beeld` op de tekst in het kerstraam) gaven de 8 pagina's van Winterlicht op de definitieve stand **0 bevindingen**.
- **Tekst op de tekening** (`e2e/kerstraam.cjs`, nieuw): het contrast van elke regel in het kerstraam tegen de 2% slechtste pixels van de tekening erachter, in alle vier kleuren op alle vier schermformaten, met de lichtjes op volle sterkte. Alles haalt de eis; het krapst is de kleine regel bovenaan in Kaarslicht met **5,3:1** (eis 4,5:1). De namen halen minstens 6,4:1 (eis 3:1), de namen eronder 6,5:1 en de wens 5,5:1.
- **Toegankelijkheid van de gewijzigde websitepagina's** (axe, eenmalig script): de homepage, Inspiratie, de collectie met het filter Kerst, de ontwerppagina van Winterlicht, zoeken op "kerst", het begin van het samenstellen en de stappen Gegevens en Aanmelden van een nieuwe kerstkaart, op 390 en 1366 pixels: **16 pagina's, 0 overtredingen**. De volledige set van 199 pagina's uit ronde 4 tot en met 6 is deze ronde niet opnieuw gedraaid.
- **Tekst in het kerstraam bij veel tekst**: alle vijf testuitnodigingen en het voorbeeld op 360, 390 en 1366 pixels, met en zonder 'minder beweging': de tekst blijft boven het kerkje (onderkant hoogstens 48,1% van de tekening). Alleen bij de testuitnodigingen met een heel lange naam wordt de tekst kleiner (tot 79% van de gewone maat).
- **Gewicht van het voorbeeld** (overgedragen bytes op telefoonformaat met pixelverhouding 2, Chromium zonder netwerkvertraging): Winterlicht **807 KB** voor het eerste beeld, eerst 1057 KB; Liefde op papier, Avondgoud en Rozentuin 195 tot 256 KB. Winterlicht is dus drie tot vier keer zo zwaar: de envelop met reliëf en het getekende kerstraam zijn beelden. In deze meting laadt Chromium 'lui' geladen beelden tot ongeveer 3000 pixels onder beeld (het huisje en de eerste foto, samen 160 KB); op een telefoon met 4G gebeurt dat pas bij het scrollen. Lighthouse is deze ronde niet gedraaid.
- **Met het oog bekeken**:
  - de envelop dicht en tijdens het openen (de gouden golf in Hulst), in alle vier kleuren;
  - het kerstraam in alle vier kleuren op 360 en 390 pixels;
  - de hele kaart van boven naar beneden (Kaarslicht) en de testuitnodigingen met lange namen, lange woorden en een kerstgroet;
  - de kraskaartjes voor, tijdens en na het krassen;
  - de brede tegel en het kaartbeeld;
  - de reliëf- en goudbeelden vóór en na het kleiner maken, op dubbele pixeldichtheid: geen zichtbaar verschil (het huisje gaf wel zichtbare banden en is niet kleiner gemaakt);
  - de voorvertoning zonder server in alle vier kleuren.

Ronde 6 (merk Vaylide), op de definitieve code en de productie-achtige server:

- **816 pagina's zonder bevindingen** (204 per schermformaat, op 360, 390, 768 en 1366 pixels breed): geen horizontaal scrollen, niets buiten beeld, geen afgesneden tekst, geen consolefouten, geen mislukte verzoeken. Het logo staat op elke websitepagina, bij het samenstellen, in de klantomgeving en in het beheer.
- **264 van 264 gedragscontroles geslaagd** (acht per ontwerp, alle 33 ontwerpen): minder beweging (de uitnodiging opent binnen 282 tot 299 ms, zonder lopende animaties), toetsenbord, muziek, het vangnet zonder script, de melding over de tijdzone en de weergave zonder JavaScript.
- **Toegankelijkheid van de website**: axe-core (WCAG 2.0/2.1, A en AA) op **199 pagina's** (dezelfde set als in ronde 4 en 5: websitepagina's, voorbeelden, alle testuitnodigingen, de klantomgeving, het samenstellen en het beheer): **0 overtredingen**. Contrast van tekst op kleurverlopen en beelden op **172 pagina's**: **0 onder 4,5:1** (3:1 voor grote tekst).
- **Render-instellingen** (`render.yaml`, lokaal nagebootst, geen server gestart): de blueprint is geldige YAML; de bouwstap (statische bestanden) werkt in een schone kopie; met dezelfde omgevingsvariabelen als in de blueprint slaagt de migratie op een lege PostgreSQL 16-database (33 ontwerpen ingelezen) en geeft `check --deploy` alleen W005 en W021. Verzoeken binnen het programma, zoals achter de proxy van Render: `/healthz` 200 zonder wachtwoord; de site 401 zonder en 200 met wachtwoord, op het Render-adres en op www.vaylide.com, met de testbalk; een onbekend domein 400; http wordt 301 naar https; het logo 200 zonder wachtwoord; het noodbeheer alleen op het geheime pad. Op Render zelf is niets getest.
- **Met het oog bekeken** (Vaylide): de kop op 360, 390, 768 en 1366 pixels breed (het logo is 58 pixels hoog op een telefoon en 72 op een tablet of computer) en de voet (120 pixels); het samenstellen en het inloggen voor het beheer op de computer en de 404 op de telefoon; de schermafbeeldingen uit de browsercontrole van 16 websitepagina's op 360 pixels en van de klantomgeving, het samenstellen en het beheer op 390 pixels, als overzicht; een e-mail met het logo; de nieuwe deelafbeelding; de iconen vergroot op een donkere tabbladbalk; het vrijstaande logo op drie lichte achtergronden (de crèmekleur van het origineel, de kleur van de voet en wit), waar het eruitziet als het origineel. Bij de tussenstap Vaylia is het logo ook op donkergroen bekeken: daar worden de lichte glans en de hoogtelichten deels doorzichtig. Daarom staat het logo alleen op lichte achtergronden.
- **Het logo naast het origineel**: op de achtergrondkleur van het origineel wijkt het vrijstaande logo hoogstens 14 van de 255 kleurstappen af, bij 735 van de 1,57 miljoen beeldpunten: de weggelaten ruispuntjes van de compressie.
- **De oude naam**: in de code, de sjablonen en de teksten staat "Vierlief" alleen nog in technische namen (zie `docs/AANPAK.md` onder "Ronde 6: Vaylide") en "Vaylia" nergens meer. De 187 pagina's van de voorvertoning bevatten geen van beide namen; alle links daarin werken.

Ronde 5 (effecten), op de definitieve code en de productie-achtige server:

- **816 pagina's zonder bevindingen** (204 per schermformaat, op de definitieve stand met de cadeau-opening): geen horizontaal scrollen, niets buiten beeld, geen afgesneden tekst, geen consolefouten, geen mislukte verzoeken. Daarvoor, op de stand zonder cadeau-opening, gaven alle vier schermformaten al hetzelfde resultaat.
- **264 van 264 gedragscontroles geslaagd**, voor alle 33 ontwerpen (acht per ontwerp; bij de cadeau-opening komt Tab eerst op de knop "Pak het cadeau uit"):
  - minder beweging: de uitnodiging opent binnen ongeveer 0,3 seconde (284 tot 311 ms), zonder lopende animaties;
  - toetsenbord: de openknop is met Tab bereikbaar; na openen staat de focus op de kop en is de inhoud bedienbaar;
  - muziek start pas na een tik en is te pauzeren;
  - laadt het script niet, dan verdwijnt het openingsscherm vanzelf (vangnet);
  - in een andere tijdzone verschijnt de melding "tijd in Nederland";
  - zonder JavaScript zijn de kop en het aanmeldformulier direct zichtbaar.
- **Effecten** (`e2e/effecten.cjs`): **264 van 264 controles geslaagd**, acht per ontwerp, voor alle 33 ontwerpen op 390×844 (ook de cadeau-opening: de cadeautjes vliegen eruit, en na aanmelden volgen cadeautjes bij Ballonfeest, Regenboog en Stipjes):
  - de deeltjes tekenen op het openingsscherm en de knop **Beweging** is zichtbaar;
  - de knal bij het openen tekent (voor alle 33 is een knal ingesteld);
  - na het openen is de kop zichtbaar en loopt de sfeer achter de tekst;
  - het feestje na "Ja, ik kom" in het voorbeeldformulier, met de melding dat het antwoord niet is opgeslagen;
  - geen fouten in de browserconsole;
  - **Beweging stilzetten**: de knop staat op "ingedrukt", er zijn geen actieve tekenvlakken en geen doorlopende animaties meer, en het beeld verandert niet meer;
  - de keuze blijft bewaard na herladen, en de beweging gaat weer aan met dezelfde knop;
  - **minder beweging** in het systeem: geen beweging, geen knop, geen knal, geen lopende animaties na het openen, en de kop is direct zichtbaar.
- **Toegankelijkheid van alle ontwerpen** (`e2e/toegankelijkheid.cjs`): axe-core 4.13 (WCAG 2.0/2.1, A en AA) en de contrastcontrole op **204 pagina's**: alle 33 ontwerpen in alle 102 kleurvarianten, dicht en geopend, met de effecten aan. **0 overtredingen en 0 contrastproblemen**, ook bij de drie ontwerpen met de cadeau-opening en nu ook bij het lakzegel van Liefde op papier. De glans in de letters (folie) telt als tekstkleur: elke kleur van het verloop moet genoeg contrast hebben met de echte achtergrond.
- **Toegankelijkheid van de website**: axe-core op **199 pagina's** (dezelfde set als in ronde 4: websitepagina's, voorbeelden, alle testuitnodigingen, de klantomgeving, het samenstellen en het beheer): **0 overtredingen**. Contrast van tekst op kleurverlopen en beelden op 172 pagina's: **0 onder 4,5:1** (3:1 voor grote tekst). De glans in de letters (folie) telt ook hier als tekstkleur; eerder meldde deze controle die ten onrechte als 1:1.
- **Met het oog bekeken**: alle 33 ontwerpen op telefoonformaat (390 pixels) als reeks schermafbeeldingen: dicht, op vier tot acht momenten tijdens en na het openen, en na het scrollen; Avondgoud, Gatsby en Rozentuin ook op computerformaat (1366 pixels); de stilgezette stand na een tik op **Beweging**; het nieuwe lakzegel van Liefde op papier (twee kleuren met het oog, alle vier in de contrastcontrole); de kaarten in de collectie, stil en met de muis erop, en een ontwerppagina met de beschrijving van de effecten. Alle 33 geopende voorbeelden op één overzicht. De cadeau-opening: dicht in alle negen kleurvarianten, op 360 en 1366 pixels, en het uitpakken als reeks van tien momenten bij Stipjes, Regenboog en Glitter & goud (in twee kleuren); het feestje met cadeautjes na aanmelden (Ballonfeest) en de kleine cadeautjes bij een tik. Puur moment na het openen op 360, 390 en 1366 pixels. Wat daarbij opviel, staat hieronder bij "Gevonden en opgelost".

Ronde 4 (30 nieuwe ontwerpen):

- **816 pagina's zonder bevindingen** en **264 van 264 gedragscontroles** (minder beweging: hoogstens 302 ms).
- **Toegankelijkheid van alle ontwerpen** (`e2e/toegankelijkheid.cjs`, ronde 4): axe-core 4.13 (WCAG 2.0/2.1, A en AA) en de contrastcontrole op **204 pagina's**: alle 33 ontwerpen in alle 102 kleurvarianten, dicht en geopend. Op het openingsscherm telt ook decoratieve tekst mee die voor schermlezers verborgen is. **0 overtredingen en 0 contrastproblemen in de 30 nieuwe ontwerpen.** Bij Liefde op papier (ronde 1) haalt de decoratieve monogram op het lakzegel 3,0 tot 4,3:1 in drie van de vier kleuren. WCAG stelt geen eis aan puur decoratieve tekst (de knop zelf heet "Open de uitnodiging"). Opgelost in ronde 5.
- **Toegankelijkheid van de website** (ronde 4): axe-core op **199 pagina's**: 19 websitepagina's (waaronder de collectie met het filter op verjaardag, de ontwerppagina van Confetti en het samenstellen voor een babyshower), de eerste 12 kleurvarianten dicht en geopend, 132 testuitnodigingen (alle 33 ontwerpen met vier soorten gegevens: lang, minimaal, verstreken en een lang woord), de klantomgeving, alle stappen van het samenstellen en het beheer. **0 overtredingen.** Contrast van tekst op kleurverlopen en beelden op 172 pagina's: **0 onder 4,5:1** (3:1 voor grote tekst). Voor de tekst op het doorschijnende vel van Puur moment is ook het slechtste geval berekend (een volledig zwarte foto onder een licht vel, of een witte onder het donkere vel): minimaal 5,3:1 in alle vier kleurvarianten. In ronde 3 waren dit 73 en 46 pagina's, met dezelfde uitkomst.
- **Met het oog bekeken** (ronde 4): alle 30 nieuwe ontwerpen dicht, tijdens het openen, geopend op de telefoon (hele pagina) en op de computer; de kaartbeelden van de collectie; de homepage, collectie, een ontwerppagina en het samenstellen; testuitnodigingen met lange namen op 360 pixels. Wat daarbij opviel, staat hieronder bij "Gevonden en opgelost".
- **Lange woorden** (ronde 4): alle 30 nieuwe ontwerpen in al hun gelegenheden (77 combinaties) met een lang woord als titel of naam, op 360, 320 en 270 pixels breed (de telefoon op de ontwerppagina): geen tekst buiten beeld.
- Eerdere rondes: de schermafbeeldingen op 360 pixels zijn met het oog bekeken (lange uitnodigingen, website, samenstellen, klantomgeving, beheer en foutpagina's), en de homepage is op 390 en 1440 pixels naast de voorbeeldfoto gelegd. Het live voorbeeld op de homepage laadt pas bij het scrollen; zonder JavaScript staat er een leesbare link naar het voorbeeld.

### Snelheid (Lighthouse 12, telefoon met trage mobiele verbinding)

Gemeten op de productie-achtige server. Ronde 6 (merk Vaylide), dezelfde acht pagina's, na alle andere controles en zonder iets ernaast:

| Pagina | Prestaties | Eerste inhoud | Grootste element | Verspringen | Gewicht |
|---|---|---|---|---|---|
| Homepage | 99 | 0,8 s | 2,0 s | 0 | 242 KB |
| Collectie (alle 33 ontwerpen) | 100 | 0,8 s | 1,8 s | 0 | 166 KB |
| Ontwerppagina Confetti (met live voorbeeld) | 100 | 0,9 s | 1,7 s | 0 | 279 KB |
| Voorbeelden Rozentuin / Neonnacht / Avondgoud | 98 / 100 / 99 | 1,1–1,7 s | 1,7–2,3 s | ≤ 0,003 | 117–219 KB |
| Voorbeeld Stipjes (cadeau-opening) | 100 | 1,1 s | 1,8 s | 0 | 139 KB |
| Voorbeeld Glitter & goud (cadeau-opening) | 99 | 1,4 s | 2,0 s | 0 | 149 KB |

Toegankelijkheid en goede praktijken: 100 op alle acht pagina's. De websitepagina's zijn ongeveer 28 KB zwaarder dan in ronde 5 door het logo (een WebP-beeld in plaats van een getekend hartje). Bij de tussenstap Vaylia gaf de ontwerppagina van Confetti bij de eerste meting 99, met het grootste element na 2,2 s; twee nieuwe metingen gaven toen 100 en 1,7 s. De voorbeelden scoren 63 op vindbaarheid omdat ze bewust niet in zoekmachines komen (`noindex`).

Ronde 5 (met de effecten en de cadeau-opening), acht pagina's:

| Pagina | Prestaties | Eerste inhoud | Grootste element | Verspringen | Gewicht |
|---|---|---|---|---|---|
| Homepage | 99 | 0,8 s | 2,0 s | 0 | 214 KB |
| Collectie (alle 33 ontwerpen) | 100 | 0,8 s | 1,6 s | 0 | 138 KB |
| Ontwerppagina Confetti (met live voorbeeld) | 100 | 0,9 s | 1,6 s | 0 | 251 KB |
| Voorbeelden Rozentuin / Neonnacht / Avondgoud | 98 / 100 / 99 | 1,1–1,7 s | 1,7–2,3 s | ≤ 0,003 | 116–217 KB |
| Voorbeeld Stipjes (cadeau-opening) | 99 | 1,3 s | 1,8 s | 0 | 137 KB |
| Voorbeeld Glitter & goud (cadeau-opening) | 100 / 99 / 100 (drie metingen) | 1,4–1,5 s | 1,7–2,1 s | 0 | 148 KB |

Het voorbeeld van Glitter & goud scoorde eerst 76 tot 83, met 640 tot 1100 ms blokkeertijd tijdens het laden (zie "Gevonden en opgelost"); na de oplossing drie keer opnieuw gemeten: 100, 99 en 100, met 4 tot 63 ms blokkeertijd. De andere zeven pagina's zijn gemeten vóór die oplossing, die alleen werk weghaalt.

Ronde 4 (met de 30 nieuwe ontwerpen):

| Pagina | Prestaties | Eerste inhoud | Grootste element | Verspringen | Gewicht |
|---|---|---|---|---|---|
| Homepage | 99 | 0,8 s | 2,0 s | 0 | 214 KB |
| Collectie (alle 33 ontwerpen) | 100 | 0,8 s | 1,5 s | 0 | 138 KB |
| Collectie, filter verjaardag | 100 | 0,8 s | 1,7 s | 0 | 158 KB |
| Ontwerppagina Confetti (met live voorbeeld) | 100 | 0,8 s | 1,4 s | 0 | 224 KB |
| Voorbeelden Confetti / Gala / Ja-woord | 100 / 100 / 99 | 0,9–1,5 s | 1,7–2,0 s | ≤ 0,003 | 109–149 KB |
| Voorbeelden Rozentuin / Onder de sterren / Tropisch | 98 / 99 / 99 | 1,4–1,7 s | 1,8–2,1 s | ≤ 0,005 | 142–189 KB |

Ronde 3 (nieuwe vormgeving):

| Pagina | Prestaties | Eerste inhoud | Grootste element | Verspringen | Gewicht |
|---|---|---|---|---|---|
| Homepage | 99 | 0,8 s | 2,0 s | 0 | 198 KB |
| Collectie (ontwerpen) | 100 | 0,8 s | 1,5 s | 0 | 136 KB |
| Prijzen | 100 | 0,8 s | 1,4 s | 0 | 90 KB |
| Inspiratie | 99 | 1,1 s | 2,1 s | 0 | 171 KB |
| Samenstellen | 99 | 0,9 s | 1,7 s | 0,05 | 129 KB |
| Liefde op papier / Avondgoud / Puur moment (voorbeeld) | 99 / 99 / 100 | 1,2–1,7 s | 1,7–2,0 s | ≤ 0,01 | 102–169 KB |
| Gepubliceerde uitnodiging | 99 | 1,4 s | 2,0 s | 0 | 171 KB |

Toegankelijkheid en beste praktijken scoren 100 op alle gemeten pagina's, vindbaarheid 100 op de websitepagina's. De lagere vindbaarheidsscore van uitnodigingen, voorbeelden en het samenstellen is bewust: die pagina's staan op `noindex`. Een Atelier-ontwerp laadt de gedeelde opmaak (sinds ronde 5 64 KB, gecomprimeerd 13 KB; was 44 en 9 KB), een eigen stylesheet van ongeveer 1 KB en alleen de eigen lettertypen. Alle uitnodigingen laden sinds ronde 5 ook de opmaak van de effecten (14 KB, gecomprimeerd 4 KB) en het effectenscript (76 KB, gecomprimeerd 19 KB); dat script wacht tot de pagina er staat. De collectie laadt de kaartbeelden pas als ze in beeld komen, dus 33 ontwerpen maken de pagina nauwelijks zwaarder.

### Belasting door de effecten

Gemeten met `CHECKS=0 PERF=1 node e2e/effecten.cjs` op de productie-achtige server, zonder andere controles ernaast: Chromium zonder grafische kaart (het tekenen gebeurt in software), telefoonformaat 390×844 met pixelverhouding 2 en een vier keer vertraagde processor. Per ontwerp drie seconden op het openingsscherm en drie seconden vanaf zes seconden na het openen. Rekentijd is hoeveel milliseconden per seconde de browser bezig is; bij 1000 komt hij nergens anders meer aan toe.

| Alle 33 ontwerpen | Openingsscherm | Na het openen |
|---|---|---|
| Eerste versie van de effecten | 335 tot 678 ms per s | 362 tot 1000 ms per s; Neonnacht haalde 1 beeld per seconde |
| Definitieve stand (ronde 5) | 313 tot 539 ms per s | 251 tot 513 ms per s |
| Beelden per seconde, definitieve stand | 59 tot 61 | 59 tot 60 |
| Ronde 7: de 33 andere ontwerpen | 197 tot 360 ms per s | 166 tot 404 ms per s |
| Ronde 7: Winterlicht | 451 ms per s | 603 ms per s |
| Beelden per seconde, ronde 7 (alle 34) | 57 tot 60 | 60 |

Winterlicht is het zwaarste ontwerp: de sneeuw op de pagina en in het kerstraam, 60 lichtjes met een eigen animatie en het ademende kerstraam. Onder de dichte envelop en buiten beeld staan de lichtjes stil; bij 'minder beweging' of met de knop **Beweging** beweegt er niets. Of het op een echt ouder toestel soepel loopt, is niet getest (zie "Niet gecontroleerd"). De meting van ronde 7 liep op de definitieve stand, zonder andere controles ernaast.

Met de beweging stilgezet (knop **Beweging**) is de rekentijd na het openen ongeveer 1 ms per seconde; met beweging 270 tot 380 ms (gemeten bij Rozentuin, Gala, Neonnacht, Puur moment en Glitter & goud). Op een echte telefoon tekent de grafische kaart mee, dus dit is een ongunstige benadering en geen meting op een echt toestel (zie "Niet gecontroleerd").

### Gevonden en opgelost

Ronde 7 (kerstkaarten):

| Bevinding | Oplossing |
|---|---|
| Na een wijziging in het muziekscript opende de kerstkaart meteen, zonder envelop: het script stopte door een melodie die werd gebruikt voordat hij bestond, en het vangnet deed de rest | Melodieën staan bovenaan het script; de opening werkt weer en de gedragscontroles slagen |
| De gouden golf door het reliëf was te snel om te zien | Langzamer (1,9 s), met een bredere band en een zachte nagloed; de kleppen gaan later open, zodat de golf eerst te zien is |
| Krassen haalde de goudfolie maar deels weg: elke streek gebruikte de halfdoorzichtige verf van het tekenen | Wegkrassen met dekkende verf: waar je krast, is de folie in één keer weg |
| De tekst op de envelop brak op een telefoon lelijk af | Kortere tekst ("Een kerstgroet voor jou") en letters die meeschalen |
| Het kerstraam vulde op een telefoon niet het hele scherm | De maximale hoogte geldt alleen op een computer |
| In de donkere kleuren stond de kerstster achter de wens ("wenst je fijne feestdagen") | Ster links van het kerkje, onder de tekst; kortere linten aan de strik; de tekst staat hoger en compacter |
| In het voorbeeld duwde de voorbeeldbalk "Scroll verder" onder de rand van het scherm | De kop is precies zo hoog als het scherm min de balk |
| Op 360 pixels breed paste "Familie Van Dijk" net op één regel en raakte de naam de lantaarns; bij een gepubliceerde kaart (zonder voorbeeldbalk) gold dat ook voor "Familie Jansen" | De bovenste regels zijn smaller; zulke namen breken netjes over twee regels |
| De kleine regel bovenaan ("Warme kerstgroeten van") kwam op een paar pixels van de slinger; de nieuwe meting van tekst op de tekening (`e2e/kerstraam.cjs`) gaf daar 1,4:1 in de lichte kleuren | Iets kleinere letters met minder ruimte ertussen, en de tekst een fractie lager: nu minstens 5,3:1 |
| Een testuitnodiging met een heel lange familienaam en veel namen eronder: de wens liep over het kerkje in het kerstraam | De tekst in het kerstraam wordt dan iets kleiner (`winterlicht.js`), zodat hij altijd boven het kerkje blijft; kleine letters niet onder 10 pixels. Zonder script blijft alles op de gewone maat |
| Die aanpassing mat eerst verkeerd bij 'minder beweging': het platform geeft dan elke overgang 0,01 ms, en zo lang gaf de browser nog de oude maat terug | Geen overgangen in deze tekst; de meting klopt nu met en zonder 'minder beweging' |
| De lichtjes bleven bewegen onder de dichte envelop en als de kop uit beeld was | Ze staan dan stil |
| De e-mails zeiden "je uitnodiging voor Familie Van Dijk" | "Je kerstkaart van Familie Van Dijk" (ook in het onderwerp en op de bestelstatus) |
| De tegel en het kaartbeeld van Winterlicht waren gemaakt vóór de laatste aanpassingen | Opnieuw gemaakt |

Ronde 5 (effecten):

| Bevinding | Oplossing |
|---|---|
| Neonnacht liep na het openen vast op een trage processor (1 beeld per seconde): de neonvonken kregen per beeld een schaduwgloed | Gloed als brede, zachte lijn eronder; nu 60 beelden per seconde (zie "Belasting door de effecten") |
| De zwevende deeltjes kostten op een vier keer vertraagde processor na het openen 362 tot 1000 ms rekentijd per seconde | 30 beelden per seconde voor rustig zwevende deeltjes (de knal blijft 60), lagere tekenresolutie achter de tekst, minder deeltjes op eenvoudige toestellen: nu 251 tot 513 ms bij alle 33 ontwerpen (zie "Belasting door de effecten") |
| Het openingsscherm kantelde soms zonder dat de muis bewoog (de browser stuurt na een opmaakwijziging een "nep"-beweging) | Alleen echte muisbewegingen tellen |
| Deeltjes waren onzichtbaar op een openingsscherm in de accentkleur (Congres) | Een kleur die bijna gelijk is aan de achtergrond wordt automatisch lichter of donkerder |
| Liefde op papier: blaadjes konden over de kleine teksten van het openingsscherm vallen | De tekst ligt boven de deeltjes |
| Liefde op papier: de initialen op het lakzegel haalden 3,0 tot 4,3:1 (aandachtspunt uit ronde 4) | De initialen staan in het vlakke, ingedrukte midden van het zegel: 0 contrastbevindingen in alle vier kleuren |
| Tussen het vervagen van het openingsscherm en de entree van de kop zat een leeg moment | De kop begint al terwijl het scherm vervaagt |
| Avondgoud: de lichtbundel tussen de deuren had harde randen | Zachte lichtbundel die breder wordt |
| Hartjes werden bruin in de champagnekleur, pampaspluimen grijs, lauwerbladeren leken muntjes, zeepbellen waren nauwelijks zichtbaar, het puntjesraster was druk achter de tekst | Warmere tinten, eigen lauwerblaadjes, duidelijkere bellen, rustiger raster achter tekst |
| De browsercontroles klikten op een zwevende knop (Playwright wacht op stilstand) en keurden de kop soms tijdens de entree | Klikken zonder op stilstand te wachten, en wachten tot de entree klaar is |
| De contrastcontrole zag het glansverloop in de letters (folie) als achtergrond en meldde 1:1 | De controle behandelt zo'n verloop als tekstkleur: elke kleur ervan moet genoeg contrast hebben met de echte achtergrond |
| axe mat bij vier geopende voorbeelden het secondencijfer van de afteller terwijl het omklapte (dan even half doorzichtig) | Het cijfer klapt om zonder te vervagen en is op elk moment volledig leesbaar |
| De controles keken soms al voordat onderdelen die na elkaar invloeien helemaal zichtbaar waren (lange testuitnodigingen) | De controles wachten tot alle eenmalige animaties klaar zijn |
| Puur moment: na het openen stond de naam op een telefoon half onder de rand van het scherm en deels onder de nieuwe knop **Beweging** | De foto bovenaan is op lage schermen iets minder hoog, zodat de namen in het eerste beeld vrij staan |
| Het feestje na "Ja, ik kom" in de voorbeelden kwam uit de bovenkant van het formulier, vaak net buiten beeld | Het komt nu uit de verstuurknop |
| Cadeau-opening (eerste versie): het deksel vloog over de namen, de plof had twee losse kringen en pastelkleurige cadeautjes werden kaki | Het deksel vliegt opzij weg, één korte kring, cadeautjes in tinten van de accentkleur, wit en goud |
| Lighthouse: het voorbeeld van Glitter & goud scoorde 76 tot 83, met één lange taak van 0,7 s tijdens het laden. Oorzaak: het discolicht (acht kleurverlopen over een draaiend vlak van 170% van het scherm, voor acht stipjes licht) en het effectenscript dat bij elk beeld de maat van zijn tekenvlakken opvroeg, waardoor de browser steeds de opmaak opnieuw moest berekenen | Het discolicht bestaat nu uit twee kleine, herhalende patronen van lichtstipjes op een kleiner vlak; tekenvlakken worden alleen opnieuw gemeten als hun maat verandert. Daarna 99 tot 100, met 4 tot 63 ms blokkeertijd (drie metingen) |
| De effectencontrole telde de getekende punten op een verkleind beeld (96 bij 96 punten). Bij Lijnenspel, met weinig en heel fijne stofjes, kwam dat na het openen één keer uit op 0, terwijl er op ware grootte ruim 100 punten getekend waren (drie keer nagemeten) | De controle telt nu op ware grootte; daarna opnieuw 264 van 264 |

Ronde 4 (30 nieuwe ontwerpen):

| Bevinding | Oplossing |
|---|---|
| Cadeaulint: het lint liep dwars over de namen op het openingsscherm | Namen op een kaartje dat over het lint ligt |
| Envelop: de namen waren half zichtbaar tussen klep en voorkant | Klep en voorkant sluiten naadloos; de namen staan op de voorkant van de envelop, ook bij lange namen (twee regels) |
| Schuifpaneel: het paneel bedekte maar een deel van het scherm (een basisregel was sterker) | Paneel over het hele scherm |
| Polaroid: een vlak grijs vlak | Een donker, nog niet ontwikkeld beeld dat bij het openen oplicht |
| Koppen met lijnen braken op telefoons onnodig af ("Goed om te / weten") | Eerst worden de lijnen korter, pas daarna breekt de tekst |
| Sierletters (Italiana, Abril Fatface) lazen slecht in kleine tekst en cijfers | Rustiger letter voor ondertitel, welkomsttekst, datum en afteller |
| Stippen en confetti op de achtergrond liepen door de tekst | Lichter en kleiner |
| Alle ontwerpen toonden dezelfde voorbeeldfoto | 15 nieuwe eigen illustraties, per ontwerp gekozen |
| Mijlpaal (zakelijk) toonde een losse letter in plaats van een getal | Optioneel veld "Aantal jaar" bij zakelijke evenementen |
| Een lang woord in de titel (zoals "Nieuwjaarsreceptie") liep buiten beeld, ook in de telefoon op de ontwerppagina; de browsercontrole zag dat niet, omdat de pagina zulke tekst afsnijdt | Kleinere letter bij lange woorden en als laatste redmiddel afbreken; de browsercontrole meet nu ook afgesneden tekst, en elk ontwerp heeft een testuitnodiging met lange woorden |
| De homepage toonde alle ontwerpen onder elkaar | Drie uitgelichte ontwerpen en het aantal |
| Op de homepage-afbeeldingen (kaart en drie tegels) stond een focusrand rond de namen | Opnieuw gemaakt zonder focus; de tegels tonen nu ontwerpen die voor die gelegenheid zijn gemaakt |

Eerdere rondes:

| Bevinding | Oplossing |
|---|---|
| Nieuwe homepage: het cursieve lettertype in de kop laadde te laat, waardoor de knoppen versprongen (CLS 0,13) | Lettertype vooraf geladen: 0 |
| Nieuwe homepage: het live voorbeeld in het groene blok laadde meteen mee (366 KB, 125 ms blokkering) | Afbeelding als voorvertoning; het voorbeeld laadt pas vlak voordat het in beeld komt (198 KB, 0 ms) |
| Zonder JavaScript was de link in de telefoon onleesbaar (lichte tekst op lichte knop) | Donkere tekst |
| Op telefoons liep de tekst in het groene blok over de bloemen in de achtergrond | Donkere laag onder de tekst |
| Op "Zo werkt het" zakte de omschrijving van een kenmerk weg in hoge rijen | Rijen lijnen bovenaan uit |
| Samenstellen: stappen die nog niet bereikbaar zijn, stonden in een grotere letter | Alle stappen gelijk opgemaakt |
| Mijn Vaylide deed per uitnodiging aparte databasevragen (23 vragen bij 9 uitnodigingen) | Eén vraag voor alle uitnodigingen (5 in totaal, ongeacht het aantal) |
| Voorbeeldfoto's werden op telefoons in volle grootte geladen | Versies van 1000 pixels (4–13 KB in plaats van 9–80 KB) |
| Het startscript van de uitnodigingen blokkeerde de eerste weergave | Inline, toegestaan via een vaste hash in de CSP |
| HTML werd ongecomprimeerd verstuurd | Tekst wordt gecomprimeerd; beelden en deelverzoeken niet |
| Ontwerpenpagina sloeg een kopniveau over (Lighthouse) | Ontwerpkaarten zonder losse koppen |
| Kaarten onder "Andere ontwerpen" rekten uit tot halve breedte; de knop in "Op maat" werd uitgerekt | Vaste kolombreedte; knop onderaan zonder uitrekken |
| Tabbladen in Mijn Vaylide vielen op 360 px buiten beeld | Over de volle breedte verdeeld op smalle schermen |
| Stap Foto's schoof op 360 en 390 px 64–94 px te breed (het uploadveld) | Breedte van het uploadveld begrensd |
| Ontbrekende deelafbeeldingen en app-icoon zouden in productie een foutpagina geven | Afbeeldingen gemaakt in de huisstijl |
| Een nieuw ontwerp zonder voorbeeldafbeelding zou in productie een foutpagina geven | Neutrale standaardafbeelding als terugval |
| Statische bestanden waren in de Docker-container niet leesbaar voor het webproces | Vaste bestandsrechten voor statische bestanden; opnieuw getest in Docker |
| In het sierlettertype leken 1 en 0 op I en O ("I antwoorden") | Gewone cijfers op de site en in alle uitnodigingen |
| "1 antwoorden", "1 personen" | Enkelvoud en meervoud |
| Avondgoud: los scheidingsteken tussen tijd en locatie op de telefoon | Tijd en locatie onder elkaar op smalle schermen |
| Puur moment: gaten in de fotogalerij bij gemengde formaten | Galerij vult open plekken op |
| Puur moment: het kleine label op het doorschijnende vel kon bij een zeer donkere foto te weinig contrast hebben (berekend 3:1) | Label in de hoofdtekstkleur (minimaal 5,3:1) |
| "Automatisch bewaard" klopte niet (bewaren gebeurt per stap) | "Bewaard bij elke stap" |
| Kleurkiezers bij de dresscode hadden geen label (axe) | Labels toegevoegd |
| 404-pagina: veel lege ruimte, geen knop | Compacte kaart met knop naar de homepage |
| Foutpagina (500) kon zelf mislukken bij een databasestoring | Wordt nu zonder databasegegevens opgebouwd |
| Bij accountverwijdering bleven namen in bestellingen en bewaarde e-mails staan | Worden nu ook verwijderd |
| Ruimte onder het menu in Mijn Vaylide; lege toelichting zonder tekst | Afstand toegevoegd; toont nu "—" |

In eerdere rondes al opgelost: overlappende knop in de mobiele kop, de testbalk onder de camera-uitsparing in de telefoondemo, onduidelijke deadlinetekst, een te brede muziekknop op telefoons, het onthullen en fonkelen in Avondgoud, en de stappenweergave op de homepage.

### Productie-achtige controles

- `python manage.py check --deploy` met productie-instellingen (opnieuw in ronde 5): alleen de bewuste meldingen W005 en W021. `makemigrations --check`: geen wijzigingen in het datamodel.
- Docker (vorige ronde): de image bouwt vanaf nul, start met migraties op een leeg volume, laadt de ontwerpen, draait als gewone gebruiker (uid 10001), serveert statische bestanden en de eigen 404, en de onderhoudscommando's werken.

## Ronde 7: Rozenboog (verborgen ontwerp met een film als opening)

Alles uitgevoerd op 16 oktober 2026, in Chromium (Playwright), op SQLite, in testmodus.

- **Tests**: `python manage.py test tests`: 159 tests, alle geslaagd (139 bestaand, 20 nieuw in `tests/test_film.py`). `makemigrations --check`: geen wijzigingen. Nieuw: het manifest en de bestanden van de film, de weergave van het voorbeeld, alle gelegenheden, lange teksten, zonder opening, het contrast van de tekstkleuren, blaadjes achter de tekst, een echte (betaalde) uitnodiging met aftelling, agenda (.ics), route en aanmelden, en dat Rozenboog verborgen is: de voorbeeld- en ontwerppagina geven 404, het staat niet in de collectie en kan niet worden besteld (`/maken/`).
- **Rozenboog in de browser** (390 en 1366 pixels breed, ook 360 voor overloop): gesloten rozenwand, de film, het eindbeeld met namen en datum, en de hele pagina. axe-core 4 (WCAG 2.0/2.1 A en AA), dicht en open op 360, 390 en 1366: 0 bevindingen. Geen horizontaal scrollen, geen consolefouten of mislukte verzoeken. Na het aanmelden vallen bloemblaadjes achter de tekst. Zonder JavaScript en bij 'minder beweging' is de uitnodiging bruikbaar.
- **Bestaande ontwerpen vergeleken met de code van vóór deze ronde** (twee servers naast elkaar, 33 ontwerpen op 390 en 1366 pixels, met 'minder beweging'): het openingsscherm is bij alle 66 pagina's pixel voor pixel gelijk; de geopende hele pagina verschilt bij alle 66 alleen in de lopende aftelling (seconden en minuten); er zijn geen consolefouten. Daarmee is zichtbaar dat de gedeelde bestanden de bestaande ontwerpen niet veranderen. Niet vergeleken: het gedrag zelf van de effecten en het 'Direct naar de uitnodiging' op andere ontwerpen dan met de tests.
- **Niet gedaan in deze ronde**: Safari/iPhone, Android, Firefox, schermlezers, Lighthouse, het afspelen van de MP4 (Chromium speelt hier de WebM), een volledige herhaling van `e2e/controle2.cjs` en `e2e/effecten.cjs` over alle ontwerpen.

## Niet gecontroleerd

- **Echte apparaten en andere browsers**: alleen Chromium is gebruikt, op telefoon- en computerformaat. Safari/WebKit (iPhone) en Firefox zijn niet getest. Test vóór de lancering op echte iPhones en Android-telefoons.
- **Schermlezers** (VoiceOver, TalkBack): niet getest. Wel de automatische axe-controle en de toetsenbordbediening.
- **Geluid**: dat muziek pas na een tik start en te pauzeren is, is gecontroleerd; het geluid zelf is niet beluisterd.
- **Echte koppelingen**: Mollie, SMTP en de Claude-API zijn alleen met gesimuleerde antwoorden getest.
- **Weergave van e-mails** in mailprogramma's en de linkvoorvertoning in WhatsApp.
- **Belasting en snelheid** onder veel gelijktijdige bezoekers.
- **Vergelijking met de referenties en de schermopname**: niet mogelijk; zie `docs/AANPAK.md`.
- **Nieuwe vormgeving**: de voorbeeldfoto is als richting gebruikt, niet pixel voor pixel nagemaakt. Afwijkingen en de redenen staan in `docs/AANPAK.md`. De Docker-image is na deze ronde niet opnieuw gebouwd.
- **Effecten (ronde 5)**: alleen in Chromium, op een server zonder grafische kaart (het tekenen gebeurt dan in software) en met een vier keer vertraagde processor als benadering van een eenvoudige telefoon. Niet getest: echte telefoons (vooral oudere Android-toestellen, en iPhones met Safari), Firefox, het batterijverbruik, en hoe schermlezers de knop **Beweging** voorlezen. De beweging is beoordeeld op reeksen schermafbeeldingen (tot acht momenten per opening), niet als vloeiend bewegend beeld op een echt scherm. Of het geheel mooi en opvallend genoeg is, is aan de eigenaar.
- **Merk Vaylide (ronde 6)**: het logo, de iconen en de e-mail zijn alleen in Chromium bekeken. Niet bekeken: het logo in echte mailprogramma's (Outlook, Gmail, Apple Mail), het tabblad-icoon in Safari en Firefox, het icoon op het beginscherm van een echte iPhone en de linkvoorvertoning met de nieuwe deelafbeelding in WhatsApp. Of de naam Vaylide vrij is als merk, is niet gecontroleerd; het domein `vaylide.com` is nog nergens aan gekoppeld (zie `docs/LIVEGANG.md`).
- **Online (ronde 6)**: de site staat nog nergens online; er is geen hosting of domein gekoppeld (zie `docs/ONLINE.md`). Het wachtwoord voor een testversie is getest met de testclient van Django, niet achter de proxy van een echte hosting.
- **Kerstkaarten (ronde 7)**: alles alleen in Chromium, op een server zonder grafische kaart. Niet getest: Safari op een iPhone (daar vooral de gouden golf, die een nieuwere CSS-techniek gebruikt, en het krassen met de vinger), Firefox, een echt ouder Android-toestel en schermlezers. De muziek ("Stille nacht" als speeldoosje) is gecontroleerd op starten en pauzeren, niet beluisterd. De beweging is beoordeeld op schermafbeeldingen, niet als bewegend beeld. De schermopname van de eigenaar is bekeken als losse beelden; het geluid ervan niet. Of het resultaat het gewenste warme kerstgevoel geeft, is aan de eigenaar.
- **Nieuwe ontwerpen (ronde 4)**: de openingen zijn alleen in Chromium bekeken (dicht, tijdens het openen en geopend), niet in Safari of Firefox en niet op echte telefoons. De voorbeelden gebruiken eigen illustraties; met echte foto's zijn ze alleen via de testuitnodigingen bekeken (met dezelfde illustraties als foto). De 90 kleurvarianten zijn automatisch gecontroleerd (contrast en axe), niet allemaal met het oog.

## Zelf herhalen

```bash
# Functioneel
.venv/bin/python manage.py test tests

# Visueel (Playwright met Chromium nodig; alleen in testmodus)
.venv/bin/python e2e/fixtures.py > /tmp/fixtures.json          # maakt de testuitnodigingen (vier per ontwerp)
.venv/bin/python manage.py createsuperuser                        # beheerder: controle-beheer@vierlief.test
node e2e/controle2.cjs http://127.0.0.1:8000 /tmp/fixtures.json /tmp/controle2 '<wachtwoord beheerder>'

# Sneller: vier runs tegelijk, één per schermformaat (gedragscontroles in één ervan)
VIEWPORTS=360 CHECKS=0 SHOTS=viewport node e2e/controle2.cjs … &
VIEWPORTS=390 SHOTS=viewport node e2e/controle2.cjs … &         # enzovoort voor 768 en 1366
# Na een wijziging aan één ontwerp: alleen de voorbeelden, testuitnodigingen en gedragscontroles daarvan
ONTWERPEN=winterlicht node e2e/controle2.cjs …

# Toegankelijkheid en contrast van alle ontwerpen in alle kleuren (eenmalig: npm install --no-save axe-core@4)
node e2e/toegankelijkheid.cjs http://127.0.0.1:8000 /tmp/toegankelijkheid.json [code ...]

# Effecten: deeltjes, knal, feestje, knop Beweging en 'minder beweging' (acht controles per ontwerp)
node e2e/effecten.cjs http://127.0.0.1:8000 /tmp/effecten [code ...]
# Alleen de belasting meten (vier keer vertraagde processor); draai dit zonder andere controles ernaast
CHECKS=0 PERF=1 node e2e/effecten.cjs http://127.0.0.1:8000 /tmp/effecten-belasting

# Envelopcollectie (ontwerpfase; de studio /lab/enveloppen/ bestaat alleen met DEBUG aan, dus op de ontwikkelserver)
STIJLEN=signature node e2e/enveloppen.cjs http://127.0.0.1:8000 /tmp/enveloppen
```

Het rapport en de schermafbeeldingen komen in de uitvoermap (`rapport.json` of `rapport-<schermformaat>.json`, en per schermformaat een map met afbeeldingen). Gebruik bij de controles een server met `DEBUG` uit (zoals gunicorn); de ontwikkelserver toont bij een 404 een eigen foutpagina.

## Trouwontwerp Rosé Royale (2 oktober 2026, lokale branch, nog niet live)

**V2 (visuele herwerking, 2 oktober 2026):** beelden met diepte als eenmalig gerenderde WebP (`tools/rose_royale/maak_beelden.py`: rozen met licht per blad, roségouden boog en hartsculptuur als metaal, oranjerie met glas, fontein, lantaarns en pad, lichtstralen), samengesteld in lagen met eigen beweging; opening als korte film (envelop, camera rijdt de tuin in, licht in de oranjerie, namen). Opnieuw gedraaid: `e2e/rose_royale.cjs` en `e2e/rose_royale_kaart.cjs`: geen problemen; `e2e/toegankelijkheid.cjs rose-royale`: 0 bevindingen; 480 tests geslaagd (met een test dat alle beelden bestaan en samen onder 1 MB blijven; nu ongeveer 0,7 MB). Prestaties (Chromium zonder grafische kaart, pixelverhouding 2): 60 beelden per seconde op 390 en op 1366. Alleen in Chromium bekeken.

- Eigen ontwerp (alleen visuele richting uit een voorbeeld van een ander bedrijf; geen code, beelden of composities overgenomen). Opening: de Rose Blush-envelop; daarna een rozentuin in de schemering met een oranjerie, spiegeling, roségouden boog, sterren en maan, rozen vooraan, en één doorlopende kaart (medaillon, programma, boogvenster, aanmelden, slot).
- `e2e/rose_royale.cjs` (360/390/768/1366 en 'minder beweging') en `e2e/rose_royale_kaart.cjs` (beide kleurvarianten, 390 en 1366): geen problemen. `e2e/toegankelijkheid.cjs rose-royale`: 0 bevindingen (eerst contrastbevindingen op het medaillon, het lint en de lucht; opgelost). 479 tests geslaagd (met `tests/test_rose_royale.py`; de telling in `test_effects.py` is 44 ontwerpen).
- Prestaties gemeten (Chromium zonder grafische kaart, pixelverhouding 2, doorlopend na het openen): 60 beelden per seconde op 390 breed en 54 op 1366. Eerst 22 en 9: de schaduwen op grote lagen, het fonkelen van de sterren en een gloed per raam waren te zwaar en zijn vervangen. De sterren staan nu stil en de glans langs de boog komt één keer.
- Alleen in Chromium bekeken. Safari op een iPhone is nog niet gecontroleerd.

## Trouwontwerp Midnight Émeraude met GSAP (2 oktober 2026, lokale branch, nog niet live)

Eigen ontwerp om GSAP eerlijk te kunnen vergelijken met de huidige aanpak (CSS en kleine scripts). Smaragd of middernachtblauw, champagnegoud, ivoor; geen roze. Nieuwe envelopstijl `midnight-emeraude` in de Envelope Collection (alleen kleurtokens en een voering; de engine is niet aangepast, behalve dat de kaarttekst `data-tekst-op-beeld` kreeg voor de contrastcontrole). Alle beelden zijn eigen tekeningen, eenmalig gerenderd naar WebP (`tools/midnight_emeraude/`, samen ongeveer 0,65 MB).

- GSAP 3.15.0 (officiële npm-package) staat lokaal in `static/vendor/gsap/` (gsap, ScrollTrigger, MotionPathPlugin, SplitText) en wordt alleen door dit ontwerp geladen (CSP: alleen eigen scripts). Licentie ('no charge', bekeken op 2 oktober 2026) staat in `static/vendor/gsap/README.md`; Vaylide is geen tool waarmee klanten zonder code animaties bouwen. Er zijn geen accountgegevens gebruikt of opgeslagen.
- Alle beweging staat in `designs/midnight-emeraude/v1/midnight-emeraude.js`. De stylesheet heeft geen CSS-animaties, op één vangnet na (de envelop verschijnt na 3 s ook als het script niet laadt). Bij 'minder beweging' bouwt het script niets (`gsap.matchMedia`); bij de knop Beweging wordt alles teruggedraaid (`context.revert()`). Zonder GSAP werkt de pagina ook: tik op het zegel en de uitnodiging opent.
- Getest: `tests/test_midnight_emeraude.py` (9 tests: contrast van beide kleurvarianten, geen roze in de paletten, de lagen en GSAP-bestanden in de pagina, GSAP alleen in dit ontwerp, geen CSS-animaties, beelden aanwezig en licht); 489 tests geslaagd; `tests/test_effects.py` telt nu 45 ontwerpen.
- `e2e/midnight_emeraude.cjs`: opening op vaste tijdstippen van de master-timeline, het scrollen door alle hoofdstukken, geen consolefouten, geen horizontale scroll, alle onthullingen zichtbaar na scrollen, en 'minder beweging' zonder film. Geslaagd op 360, 390, 768 en 1366 (en kleurvariant middernacht op 390 en 1366). `e2e/toegankelijkheid.cjs midnight-emeraude`: 0 bevindingen in beide kleurvarianten, dicht en geopend (eerst: contrast van het merkteken onderaan en de kicker, `aria-label` op alinea's door SplitText en de kaarttekst in de envelop; alle opgelost).
- **Polijstronde (2 oktober 2026):** opening ongeveer 7,6 s na de tik (intro vóór de tik ruim 3 s); camerarit met een scherpe kopie van de kaart in plaats van een opgerekte textuur (tekst en rand blijven scherp), op een staand scherm tot de kaart ruim de breedte vult; nieuwe champagne-pioenen en doorzichtige kristalprisma's (`tools/midnight_emeraude/maak_beelden.py`), zachter licht en een lichte vignettering; aanwijzerparallax per laag (alleen met een muis); rustiger onthullingen bij het scrollen; kleinere voorgrond op een staande tablet; namen iets kleiner op smalle schermen. Het deeltjesvlak van de hele pagina is uit (het lag achter ondoorzichtige lagen). Opnieuw gecontroleerd: 489 tests, `e2e/midnight_emeraude.cjs` op 360, 390, 768 en 1366 (en middernacht op 390 en 1366, en 'minder beweging'): geen consolefouten, geen horizontale scroll; `e2e/toegankelijkheid.cjs midnight-emeraude`: 0 bevindingen.
- Beeldsnelheid (`e2e/midnight_emeraude_fps.cjs`, Chromium met de grafische kaart van deze computer; de computer was bij deze metingen trager dan bij de eerste, daarom is de oude versie in dezelfde sessie als vergelijking gemeten): 1366 breed opening 51 (oude versie 50 en 51), scrollen 53 (oude versie 44 en 51), rust 60. 390 breed opening 55 tot 56, scrollen 55 tot 56, rust 60. Met 4x vertraagde processor op 390: opening 47,5 (oud 49,5), scrollen 35 (oud 31). Software-renderer (geen grafische kaart, worst case): 390 breed opening 56, scrollen 58; 1366 breed opening 41, scrollen 52. Hapering zit vooral in losse beelden (maximaal 130 tot 280 ms bij het eerste tekenen van de kop).
- **Haperingen (derde ronde, 3 oktober 2026; gereedschap: `e2e/midnight_emeraude_hitches.cjs` en `e2e/midnight_emeraude_trace.cjs`):** de losse haperingen van 130 tot 500 ms kwamen niet van JavaScript, lettertypen, GSAP of SplitText (die samen ongeveer 130 ms hoofdthread bij het laden kosten, zonder haperend beeld), maar van de grafische kaart: de eerste keer dat Chrome iets rastert en uploadt (de filters in de envelop ongeveer 1,2 s, de binnenkant van de flap 100 tot 190 ms, de kop en de grote kaart 60 tot 120 ms). Daarnaast tekende een wissel van laagvolgorde (de flap gaat achter de kaart) en een bewegende schaduw binnen de flap de filters opnieuw. Opgelost zonder iets aan het uiterlijk te veranderen: (1) de tijdlijn loopt vóór de intro onzichtbaar langs de vier zwaarste momenten onder een vlak van opacity .995 (niet 1: een ondoorzichtig vlak laat de browser de lagen eronder juist overslaan) en gaat dan terug naar het begin; (2) de onderdelen die van volgorde wisselen kregen een eigen laag; (3) de schaduw binnen de flap wordt niet meer geanimeerd; (4) de kop blijft zichtbaar onder het openingsscherm; (5) het opnieuw meten van de scrollhoofdstukken wacht tot de film klaar is. Prijs: de intro begint op een koude pagina ongeveer 2 tot 2,5 s later (op een 4x vertraagde processor 3,5 tot 4 s). Die tijd is geen donker scherm maar een bewust openingsmoment (zie hieronder). De haperingen zijn daarheen verplaatst. Bij een tik tijdens het opwarmen stopt het opwarmen en begint de opening meteen.
- **Openingsmoment tijdens het opwarmen (3 oktober 2026):** vanaf het eerste beeld staat er een klein Vaylide-merkteken (de V uit het logo: dezelfde vorm, lichtval en details, op verzoek van de eigenaar op 3 oktober 2026 in champagnegoud in plaats van koper-roségoud, zodat er in de smaragd-kleurwereld geen roze associatie ontstaat; `tools/midnight_emeraude/maak_merk.py`, het logo zelf in `static/img/merk/` blijft onaangeroerd) in een zachte champagne gloed boven een dun gouden lijntje waar een lichtpuntje langs glijdt. Het staat er meteen (CSS, vóór het script), beweegt alleen zacht (GSAP, bevriest niet zichtbaar als de grafische kaart even stilstaat), en gaat daarna in 0,8 s over in de bestaande intro. Geen loader, spinner, percentage of tekst. Alleen zichtbaar als er een openingsscherm is en beweging aan staat (niet bij een al geopende kaart, 'minder beweging' of zonder JavaScript); als het script wegblijft verdwijnt het na 3,5 s vanzelf. Het vlak dat het opwarmen afdekt ligt boven de lichtvonk (die lekte eerst bij het opwarmen door). Zichtbare duur gemeten (mark van het eerste beeld tot het begin van de intro): 1366 breed ongeveer 2,0 s, 390 breed ongeveer 1,9 tot 2,0 s, 390 met 4x vertraagde processor 2,1 tot 2,5 s (3,5 tot 3,7 s na het laden). Het streven (1 tot 1,5 s op desktop, 2 s op mobiel) is niet gehaald: de grafische kaart heeft ruim 1,3 s nodig voor de envelop met zijn filters en het laden zelf duurt ongeveer 0,5 s; korter opwarmen gaf haperingen terug (getest: één stap minder, vroeger beginnen met rasteren). Eerdere metingen in deze sessie waren vervuild door een achtergebleven testproces; de cijfers hieronder en hierboven voor de derde ronde zijn daarna opnieuw gemeten: 1366 opening 58,7 en 58,8 fps (grootste beeld 50 en 67 ms), 390 opening 60 en 59,7 fps (17 en 67 ms), 390 met 4x vertraagde processor 57,6 en 58,9 fps (84 en 83 ms); geen beeld boven 100 ms in de opening.
- Gemeten in dezelfde sessie, voor en na (GPU, grootste beeld / beelden boven 50 ms / boven 100 ms, tijdens de 9,5 s na de tik): 1366 breed 150 en 117 ms, 8 en 9, 1 en 1 voor; 117 en 83 ms, 3 en 4, 1 en 0 na. 390 breed 183 en 250 ms, 4 en 6, 3 en 3 voor; 83 en 83 ms, 1 en 2, 0 en 0 na. 390 met 4x vertraagde processor 217 ms, 7, 4 voor; 83 ms, 5, 0 na. Na het opwarmen is de intro 60 beelden per seconde (grootste beeld 17 tot 50 ms). Blijft staan: één beeld van 67 tot 100 ms rond 5,2 s na de tik, als invite.js het openingsscherm sluit (herberekening van de pagina; gedeeld script), en bij het scrollen op een telefoon losse beelden van 60 tot 130 ms als een hoofdstuk voor het eerst in beeld komt. De hero-paint op 1366 breed loopt rond 48 beelden per seconde door het vullen van het hele scherm op een geïntegreerde grafische kaart.
- Alleen in Chromium bekeken; Safari op een iPhone en een echte telefoon zijn nog niet gecontroleerd.

## Kerstspecial Golden Noël (2 oktober 2026, lokale branch, nog niet live)

Op verzoek van de eigenaar één doorlopende kaart gemaakt (geen losse panelen meer: hoofdstukken als banen op één vel, avondhoofdstukken als donkere baan over de hele breedte). Daarna opnieuw: `e2e/golden_noel.cjs`, `e2e/golden_noel_kaart.cjs` en `e2e/toegankelijkheid.cjs golden-noel`: geen problemen, 0 bevindingen; `tests/test_golden_noel.py` geslaagd.

Herwerkt naar de 'Winterlicht'-richting (gewelfd paneel met wintergroen en lichtjes, kerstballen, kaarsen, hoofdstukken in licht en avond, diepte bij het scrollen). Daarna opnieuw gedraaid: `e2e/golden_noel.cjs` (360/390/768/1366 en 'minder beweging') en `e2e/golden_noel_kaart.cjs` (beide kleurvarianten, 390 en 1366): geen problemen. `e2e/toegankelijkheid.cjs` voor golden-noel: eerst bevindingen in de avondhoofdstukken (achtergrond alleen als verloop; de controle zag de lichte pagina erachter), opgelost met een vaste donkere ondergrond: 0 bevindingen. 476 tests geslaagd.

- `e2e/golden_noel.cjs` op 360, 390, 768 en 1366 (aanraken en muis) en met 'minder beweging': geen problemen. Gecontroleerd: geen consolefouten, geen horizontale scroll (dicht en open), na het openen is het openingsscherm weg en staan de namen in beeld, en bij 'minder beweging' staat de uitnodiging er meteen.
- `e2e/toegankelijkheid.cjs` voor golden-noel (ivoor en champagne, dicht en open): 0 bevindingen (eerst één: kleine tekst op de kaart in de envelop 4,14:1 bij champagne; kleur donkerder gemaakt).
- `manage.py test tests`: 476 tests geslaagd (met `tests/test_golden_noel.py`; de telling in `test_effects.py` is 43 ontwerpen).
- Alleen in Chromium. Safari op een iPhone is nog niet gecontroleerd.

## Envelop-engine met Signature Ivory en Royal Evergreen (2 oktober 2026, lokale branch, ontwerpfase)

Special Rose Blush toegevoegd (naar het Canva-ontwerp, zegel Rose Floral): `STIJLEN=rose-blush node e2e/enveloppen.cjs` op 360, 390, 768 en 1366 en met 'minder beweging': geen problemen. 473 tests geslaagd.

Na het akkoord op het zegel (18,5%, grotere V, sterker reliëf): binnenkant van de flap ontworpen (voering als eigen vel, goudfolielijn, motief onder de punt), zegel duidelijker 'los' vóór de flap. Daarna opnieuw `e2e/enveloppen.cjs` op 360, 390, 768 en 1366 en met 'minder beweging': geen problemen (de controle vond eerst kommagetallen in SVG-attributen door de Nederlandse notatie; opgelost en met een test afgedekt). 473 tests geslaagd.

- `e2e/enveloppen.cjs` voor Signature Ivory en Royal Evergreen op 360, 390, 768 en 1366 (aanraken op 360/390/768, muis op 1366): geen problemen. Gecontroleerd: geen consolefouten, geen horizontale scroll (ook niet na openen), het zegel is een knop met een naam en minstens 44 px, openen met aanraken, muis en toetsenbord (focus en Enter), `vx:opened` pas na ruim 3,4 seconden, en bij 'minder beweging' binnen 0,9 seconde dezelfde eindstand zonder 3D-animatie.
- `manage.py test tests`: 473 tests geslaagd (met `tests/test_envelop_collectie.py`: configuratie, lagen per stijl, studio 404 met DEBUG uit).
- Alleen in Chromium (Playwright). Safari op een iPhone is nog niet gecontroleerd.

## Signature Ivory: GSAP-opening en afwerking (3 oktober 2026, lokale branch, ontwerpfase)

Alleen de envelop Signature Ivory (er is geen eigen uitnodigingsontwerp met hoofdstukken); de andere stijlen en de ontwerpen die de engine gebruiken (Rosé Royale, Golden Noël) zijn niet veranderd. Nieuw: `static/js/envelop-signature.js` (GSAP, neemt alleen `.vx--signature` over via `data-vx-gsap`; zonder GSAP opent de klassieke engine zoals voorheen), een eigen botanisch reliëfbeeld met hoogteverschillen (`_flap_signature.svg`, uit `tools/enveloppen/maak_ornamenten.py`, zelfde compositie), iets zachter en dieper reliëflicht voor deze stijl (parameter `relief` per stijl; de standaard blijft 2,1 en 3), een champagnefolielijntje op de kaart, een lichtpunt op het zegel en een zachte schaduw onder de opstijgende kaart (eenvoudige verlopen, geen filters), een zachte zweving, lichtstreep en met een muis een heel lichte kanteling.
- Opening ongeveer 2,9 s na de tik (klassiek 3,8 s). Onzichtbaar opwarmen vóór de envelop verschijnt: de timeline loopt langs flap open, kaart eruit en eindstand terwijl de envelop vrijwel doorzichtig is; onderdelen die van laagvolgorde wisselen hebben een eigen laag; geen klassewissels die een filter veranderen; de kaart schaalt zonder eigen laag (`force3D: false`) zodat tekst en rand scherp blijven. Bij 'minder beweging' of Beweging uit: kort vervagen en de eindstand.
- Gemeten (`e2e/envelop_fps.cjs`, grafische kaart, eerste koude keer): voorheen een hapering van 100 tot 134 ms bij het indrukken van het zegel en 70 tot 83 ms bij de flap; nu opent de envelop op 1366 en 390 breed, ook met 4x trage processor, op 60 fps met een grootste beeld van 17 ms. De koude rastering (ongeveer 1 s) zit nu vóór het verschijnen van de envelop. Rust (zweving, lichtstreep en muis): 60 fps, grootste beeld 17 tot 18 ms.
- `e2e/enveloppen.cjs` voor Signature Ivory, Royal Evergreen en Rose Blush op 360, 390, 768 en 1366 en met 'minder beweging': geen problemen (de klassieke stijlen zijn dus niet verslechterd); `e2e/rose_royale.cjs` en `e2e/golden_noel.cjs` op 390: geen problemen; axe op de studiopagina (dicht en open, 360 en 1366): geen bevindingen; 492 tests geslaagd (met `SignatureIvoryGsapTests`).
- Alleen in Chromium bekeken.

## Envelope Collection als keuze in de Studio (3 oktober 2026, lokale branch, nog niet live)

Klantflow: Ontwerp, **Envelop & zegel** (nieuwe stap, alleen bij ontwerpen met `envelope_mode` optional), Gegevens en verder, Voorbeeld, Bestellen. De envelop is een losse presentatielaag om het ontwerp: één generiek openingsscherm (`invitations/partials/envelop_cover.html`, `static/css/envelop-cover.css`) met de bestaande envelop-engine; het ontwerp zelf is niet veranderd. Keuze: geen envelop (direct de uitnodiging), de opening van het ontwerp, of één van de 5 uitgewerkte enveloppen (Signature Ivory, Rose Blush, Midnight Émeraude; bij Kerst Royal Evergreen en Golden Noël) met alleen de passende zegels (5 zegels), en op het zegel het teken of eigen initialen. Voorbeeldbeelden komen van de bestaande studio (`e2e/envelop_voorbeelden.cjs`, `tools/enveloppen/maak_voorbeelden.py`); er is geen nieuw artwork.
- Opslag zonder migratie: `draft_content.style.envelop.collectie` = `{envelop, zegel, teken, initialen}` (leeg = het gedrag van vroeger, `geen` = geen opening). Registry en capaciteit per ontwerp: `catalog/envelop_collectie.py` (`KEUZE`, `ONTWERP_MODUS`, `modus()`; `envelope_mode` in het manifest wint). `built_in` (de standaard voor elk ander ontwerp, expliciet in Rosé Royale, Golden Noël en Midnight Émeraude), `optional` (nu: Puur moment, Lijnenspel, Pampas, Eucalyptus, Monogram, Strak, Borrel, Congres, Lauwerkrans, Lentebloesem, Rozentuin) en `none`.
- Oudere uitnodigingen en bestellingen zijn niet veranderd: zonder keuze blijft de eigen opening van het ontwerp; een ingebouwd ontwerp negeert een eventuele keuze; een onbekende of niet passende keuze valt terug op het oude gedrag. De oudere envelop-keuze (kleur, initialen, logo) in de stap Stijl blijft bij ontwerpen met een eigen envelop; bij ontwerpen met de nieuwe stap staat de schakelaar voor de opening bij Envelop & zegel.
- Voor de gast: envelop, zegel breken, kaart eruit, dan de bestaande uitnodiging. Signature Ivory gebruikt de GSAP-opening (`envelop-signature.js`, met `data-vx-gsap` zodat er niet dubbel wordt geïnitialiseerd), de andere de klassieke engine. Het deeltjesvuurwerk van het ontwerp is bij een gekozen envelop uit, zodat het niet botst met de envelop. De live kaart toont bij de stap Envelop de dichte envelop en werkt zich bij zonder de pagina te verversen.
- `tests/test_envelop_keuze.py` (20 tests: registry, stap, voortgang, kiezen en wisselen, onpassend zegel, initialen, live voorbeeld, gastweergave voor optional, built_in, geen envelop en zonder keuze); `e2e/envelop_keuze.cjs` op 360, 390, 768 en 1366 en met 'minder beweging': ontwerp kiezen, envelop en zegel kiezen en wisselen (live, zonder verversen), geen envelop, opslaan en terugkomen, ingebouwd ontwerp, de opening van de gast tot en met de uitnodiging, geen horizontale scroll, geen consolefouten, zegel minstens 44 px: geen problemen; axe op de stap en de gastweergave (dicht en open, 360 en 1366): geen bevindingen; 512 tests geslaagd.
- Initialen op het zegel (3 oktober 2026): letters groter en steviger (Cormorant Garamond cursief 700 met een dunne streek in de hoogtekaart, anders verdwijnen dunne streken in de lichtberekening en lijken het vlekken), de maat volgt het aantal letters, en een `&` staat kleiner en iets hoger tussen twee grote letters (`monogram_opmaak()` in `catalog/envelop_collectie.py`, CSS `.vx-seal__mono--*`). Bekeken op groot formaat voor S&D en AB in Midnight Émeraude in de ingebouwde browser (alleen Chromium); een, drie en vier letters en 360/390 px niet apart bekeken. 516 tests geslaagd (4 nieuwe).
- Wasoppervlak van het zegel (3 oktober 2026): de grove ruis in de hoogtekaart (`baseFrequency .18`) gaf bij 8 bits hoogte contourlijnen, harde randen en vlekken die op compressie leken, vooral in de glansfilter. Nu: een heel fijne korrel in de hoogte (zet afrondingsstapjes om in korrel), zachte lichtvlekken in de belichting (`vx-wax-shade` in `collectie.html`) en geen ruis meer in de glans (`vx-wax-spec`). Scherpte van V, krans en letters is ongewijzigd (de hoogtekaart zelf is niet gewist). Materiaalwaarden in `catalog/envelop_collectie.py` (`WAS_KORREL`, `WAS_VLEK`; per zegel te overschrijven met `korrel` en `vlek`; Sage en Noisette zijn lichter en hebben zachtere vlekken). Bekeken (Chromium, ingebouwde browser): Champagne, Evergreen, Sage, Noisette en Rose op groot formaat; S&D, AB, FAM en het logo-V op 360 en 390 px, S&D op 1366 px. Niet gedaan: vergelijking op een echt toestel of op een scherm met hoge pixeldichtheid. 520 tests geslaagd.
- Afronding zegels (3 oktober 2026): alle vijf de materialen (Champagne, Evergreen, Sage, Noisette, Rose) met het logo-V of de roos en met S&D, op 390 en 1366 px bij schaalfactor 2 (Playwright-Chromium, `reducedMotion`): geen banding of contourlijnen, schone rand en glans, monogram scherp; niets meer aangepast. Niet bekeken: een echt toestel, andere browsers. Een losse export van Midnight Émeraude (zonder server te openen; maken met `python tools/voorvertoning.py <uitvoermap> midnight-emeraude`; de uitvoermap en de zip staan bewust niet in Git) is opnieuw gemaakt met de nieuwe wasfilters en het monogram S&D; zonder server geopend via `file://` (kleuren Smaragd en Middernacht, 390 en 1366 px): geen consolefouten, geen mislukte of externe verzoeken, alle lettertypes geladen, geen horizontale scroll, de envelop opent. `tools/voorvertoning.py` laat de lettertype-preload nu weg (gaf onder `file://` alleen een CORS-melding).
- Uitleg en eerlijke keuzes in de Studio (3 oktober 2026, na een klantrondgang op 390 en 1366 px): uitleg bovenaan Envelop & zegel; "De eigen opening van <ontwerp>" in plaats van het technische label; initialen-uitleg alleen over het zegel (en "hoogstens 4 tekens" bij zegels uit de collectie, zoals het zegel ze toont); enveloppen die als ontwerp bestaan heten in de keuzelijst "… envelop"; ontwerpen met een eigen opening zeggen dat in Gegevens en Stijl. Oude controls: per ontwerp uit de sjablonen nagegaan welke iets veranderen. Midnight Émeraude: envelopkleur, zegelkleur, zegelinhoud en logo deden niets en zijn weg, de initialen blijven (live, bewaard en op het zegel gecontroleerd; de schakelaar voor de opening werkt: uit = geen openingsscherm). Rosé Royale en Golden Noël: geen zegelpaneel meer. Klassieke envelopontwerpen (Balzaal, Liefde op papier, Winterlicht, Eerste dans, Lauwerkrans, Lentebloesem, Rozentuin) ongewijzigd: sjablonen gebruiken de envelop- en zegelkleur, het logo en de initialen. Opgeslagen drafts met oude, nu niet getoonde waarden blijven ongemoeid en worden genegeerd. `tests/test_envelop_stijl.py` (16 tests); 536 tests geslaagd. Niet gedaan: de uitleg in een echt toestel of met echte klanten; bij Golden Noël bepaalde het veld initialen alleen een sierletter-monogram aan het eind van de kaart, dat nu uit de namen komt.
- Polishronde Studio (3 oktober 2026): (1) zegels heten in de keuzelijst naar materiaal en teken (Champagnegoud, Warm goud, Saliegroen: "Met de V"; Roségoud: "Met een roos"; Dennengroen: "Met de V in een krans"), alleen de zichtbare labels (`ZEGEL_KEUZENAMEN` in `studio/forms.py`; codes en registry ongewijzigd). (2) Zwevende knop 'Bekijk je kaart' (360/390 px): vóór de aanpassing stond hij bij ongeveer 15 tot 45% van de scrollposities (stappen 3 tot 7) over een veld of knop en bij het typen boven het toetsenbord; nu verdwijnt hij zolang je in een veld typt en zodra de knoppen onderaan de stap in de strook komen waar hij zelf zit (`studio.js`, `data-knop-weg`; `visibility` haalt hem ook uit de tabvolgorde); open ('Sluiten') blijft hij staan. Gemeten: de knop dekt de stapknoppen nooit meer af, komt onderaan de pagina terug, en blijft over velden hangen in 1 tot 4 van 10 tot 16 posities (inherent aan een zwevende knop; tijdens het typen weg). (3) 'Envelop en zegel' staat in de aanpas-lijst bij Voorbeeld en in Mijn VAYLIDE alleen bij ontwerpen met die stap (`heeft_envelopstap()` in `studio/steps.py`); bij ingebouwde ontwerpen staat de link er niet; de link toont de bewaarde keuze (envelop, zegel, initialen) en 'terug' brengt je weer bij het voorbeeld. (4) De overgang `transition: width .3s` op `.preview-frame` (app.css, regel 135 vóór deze ronde) is gemeten met CDP (LayoutCount, LayoutDuration) en frame-tijden, met en zonder overgang, op 1366 en 390 px, bij Puur moment en Midnight Émeraude: alleen bij de knoppen Telefoon/Computer, 0,3 s per klik; op 1366 kost de overgang 15 tot 70 layouts en 34 tot 93 ms layout tegenover 1 tot 7 ms zonder overgang (de iframe herberekent de kaart elk frame), in deze softwarematig getekende testomgeving met 0 tot 2 frames boven 50 ms (hoogste 150 ms, vooral bij de eerste klik); op 390 px nauwelijks verschil. Onveranderd gelaten: geen merkbaar probleem bij normaal gebruik, en een transform-alternatief geeft niet hetzelfde beeld (de kaart in het kader moet echt op de nieuwe breedte worden opgemaakt). Vastgelegde uitzondering op de ontwerpcontrole (impeccable), op verzoek van de eigenaar, zo smal mogelijk: alleen de `transition: width .3s` op `.preview-frame` in `static/css/app.css`, als opmerking `impeccable-disable-next-line layout-transition` direct boven die regel met de reden erbij (er is bewust geen wildcard-uitzondering in `.impeccable/config.json`, want die zou elke latere layout-overgang in app.css verbergen). Reden: de overgang draait alleen als de klant zelf wisselt tussen Telefoon en Computer, de kaart moet echt op de gekozen breedte worden opgemaakt (een `transform` is functioneel niet gelijkwaardig), en gemeten kost hij op 1366 px circa 34 tot 93 ms layout tijdens de 0,3 s, op 390 px nauwelijks iets, met hooguit incidenteel 0 tot 2 frames boven 50 ms in de software-render test; geen merkbare invloed bij normaal gebruik, bewust behouden voor een correcte responsive preview. Controle: met de opmerking meldt `impeccable detect static/css/app.css` niets meer; met `--no-inline-ignores` komt precies deze regel terug. Dezelfde ronde legde de eigenaar een uitzondering vast voor `gradient-text` op `.studio-intro--bijna` (alleen in `app.css`, zie hierboven). (5) `.studio-intro--bijna h1` (gradient, alleen stap Bestellen): slechtste kleur #7A5A2E op ivoor 5,95:1 (grote tekst; grens 3:1), de andere kleur 15:1, terugval bij 'forced colors' aanwezig. axe (WCAG 2.0/2.1 A en AA, `bypassCSP`) op 360, 390 en 1366 px: Envelop, Gegevens, Stijl, Voorbeeld en Bestellen bij Puur moment, Gegevens, Stijl en Voorbeeld bij Midnight Émeraude: 0 bevindingen; geen consolefouten; geen horizontale scroll. 541 tests geslaagd (5 nieuw). Niet gedaan: echt toestel met schermtoetsenbord; de knop kan daar anders reageren dan in de emulatie.
- Envelop & zegel op een telefoon (3 oktober 2026, alleen lay-out, ≤ 640 px): twee kaarten naast elkaar, Opening/Geen envelop als kleine tegels, een laatste enkele envelop over de volle breedte, zegels in een 2-kolomsrooster met klein rond beeld, een vinkje op de gekozen kaart, kortere witruimte en de knoppen Volgende / Vorige + Opslaan compacter. Gemeten op 390 px (envelop gekozen met zegels): paginahoogte 3138 naar 1771 px, "Volgende" van 2731 naar 1428 px; zonder gekozen envelop 2454 naar 1382 px en 2047 naar 1039 px. Op 360 px 3113 naar 1814 px. Geen horizontale scroll, namen van zegels op 1 regel, desktop ongewijzigd (zegelkaarten wel 164 in plaats van 150 px breed). Een onbetrouwbare test (`"vxc"` als losse letters in de pagina) controleert nu op de klasse.
- Bevestigingsmail (3 oktober 2026): opnieuw opgebouwd met de teksten van de eigenaar (kop "Je bestelling is bevestigd", aanhef met voornaam, blokken Directe levering en bedenktijd, Online beschikbaarheid, Algemene voorwaarden en Herroepingsrecht, daarna het ongewijzigde bedrijfsblok). Toestemming (tijdstip en letterlijke tekst) komt uit `Order.delivery_consent_at` en `delivery_consent_text`, de versie uit `Order.terms_version` (geen terugval op de huidige versie meer; zonder opgeslagen versie geen versieregel en geen pdf-bijlage; het woord "concept" staat er niet meer). `tests/test_bevestigingsmail.py` (8 tests) controleert de teksten in HTML en platte tekst, dat een andere opgeslagen toestemming en datum in de mail terechtkomen, de aanhef, de versie en het bedrijfsblok. 549 tests geslaagd. Voorbeeldmail met testdata bekeken op 390 en 700 px in Chromium; niet in echte mailprogramma's.
- Checkout (3 oktober 2026): drie afzonderlijke verplichte vinkjes met de teksten van de eigenaar (voorwaarden; digitale kaart direct leveren met erkenning verlies herroepingsrecht; verzoek om de online beschikbaarheid direct te starten, zonder te beweren dat het herroepingsrecht voor die dienst vervalt), een korte uitleg met link naar artikel 9, en de knop "Bestellen en betalen € …". Beide toestemmingen worden met letterlijke tekst en tijdstip vastgelegd op de bestelling (nieuwe velden `service_consent_at` en `service_consent_text`, migratie `orders/0003`). De nieuwsbrief blijft apart, optioneel en niet aangevinkt, nu ook met een scheidingslijn. Browsertest op 390 en 1366 px (Chromium): zonder een van de drie komt er geen bestelling en verschijnt de bijbehorende melding (andere vinkjes blijven staan), axe (WCAG 2.0/2.1 A en AA) 0 bevindingen ook in de foutstaat, geen consolefouten, geen horizontale scroll. Mobiel compacter (alleen ≤ 640 px, niets ingeklapt of weggelaten): paginahoogte op 390 px 3465 naar 2666 px en de bestelknop van 3214 naar 2415 px (op 360 px 3619 naar 2778 en 3346 naar 2505); het toestemmingsblok van 879 naar 526 px. Niet gedaan: een echte betaling doorlopen in de browser (wel in de tests) en echte toestellen.
- Alleen in Chromium. De gastlink is met de voorbeeldweergave van de Studio getest (dezelfde weergave); de gastlink van een betaalde uitnodiging in `tests/test_envelop_keuze.py`.

## Envelopcollectie, benchmark Signature Ivory (2 oktober 2026, lokale branch, ontwerpfase)

Opnieuw gebouwd naar het Canva-ontwerp van de eigenaar (diepe puntflap, boeket in blinddruk, veldbloemenvoering, gouden zegel met de logo-V). Daarna dezelfde controles opnieuw gedraaid, met dezelfde uitkomst als hieronder.

- `e2e/enveloppen.cjs` voor Signature Ivory op 360, 390, 768 en 1366: geen problemen. Gecontroleerd: geen consolefouten, geen horizontale scroll, het zegel is een knop met een naam, `vx:opened` komt pas na het openen (na ruim 3 seconden), en bij 'minder beweging' staat de envelop meteen open.
- `manage.py test tests`: 470 tests geslaagd (met `tests/test_envelop_collectie.py`: de studio geeft 404 met DEBUG uit).
- Alleen in Chromium bekeken. Safari op een iPhone (mengmodi en lichtfilters in SVG) is nog niet gecontroleerd.

## Kerstontwerpen Ho ho ho, Sneeuwpret en Middernacht (28 september 2026)

Uitgevoerd op Windows met Python 3.12 en Chromium (Playwright):

- `manage.py test tests`: 176 tests, alle geslaagd.
- Contrast van alle tekstkleuren in alle kleurvarianten (minstens 4,5:1; Middernacht minstens 5:1).
- In de browser bekeken op telefoonformaat: de opening en de geopende kaart van alle drie, alle vier kleuren van Middernacht (openingsscherm en hele pagina) en Middernacht op 360 pixels breed (geen horizontaal scrollen).
- Beweging gemeten: de arm van de kerstman en de arm, sjaal en het lijf van de sneeuwpop draaien alleen met beweging aan.
- Muziek van Middernacht: na "Openen met muziek" staat de knop op spelen, zonder fouten in de console; het gemeten geluidsniveau stijgt van ongeveer 0,1 (celesta) naar 0,3 (volledig ensemble) en blijft ruim onder vervorming.

Niet gedaan: echte iPhone/Android, Safari en Firefox, schermlezers en de volledige `e2e/`-controles op alle ontwerpen.

## Kerstontwerp Gloria (28 september 2026)

- `manage.py test tests`: 182 tests, alle geslaagd.
- Contrast van de tekstkleuren in alle vier kleuren minstens 4,5:1 (tekst staat nooit op de veren: op het openingsscherm ligt hij op een eigen medaillon).
- In Chromium (Playwright) bekeken op 390 pixels breed: openingsscherm in alle vier kleuren, de kop in alle vier kleuren, de hele pagina in Kerstrood, en het openen op drie momenten (vleugels spreiden zich naar buiten en omhoog, daarna licht en de kop).
- Muziek: na "Openen met muziek" staat de knop op spelen, zonder fouten; het gemeten niveau is 0,1 tot 0,25 in het couplet en loopt in het refrein met koor op tot ongeveer 0,38, zonder vervorming.

Niet gedaan: echte telefoons, Safari en Firefox, schermlezers en de volledige `e2e/`-controles.

## Kleuren kiezen op de ontwerppagina (28 september 2026)

Probleem: op de ontwerppagina stonden de kleuren alleen als lijstje; het voorbeeld toonde altijd de eerste kleur en "Kies dit ontwerp" nam geen kleur mee. Nu is elke kleur een link (`?kleur=`), wisselt het voorbeeld in de telefoon mee zonder herladen (`static/js/site.js`) en start het samenstellen in de gekozen kleur (`create_draft(palette=…)`).

- `manage.py test tests`: 188 tests, alle geslaagd (nieuw: `tests/test_kleuren.py`, onder meer alle kleuren van alle ontwerpen op de ontwerppagina en de stap Stijl voor de vijf kerstontwerpen).
- In Chromium (Playwright) op 1280 pixels: op de ontwerppagina's van de vijf kerstontwerpen en Liefde op papier elke kleur aangeklikt; het voorbeeld in de telefoon toonde telkens die kleur en de startknop nam hem mee, zonder fouten in de console.

## Kerstdiner-ontwerp Aan tafel en nieuwe kleurkeuze (28 september 2026)

- De kleurkeuze op de ontwerppagina is nu een rij ronde kleurstalen met de naam van de gekozen kleur erboven (in plaats van pilvormige knoppen). Bekeken in Chromium op 1280 en 390 pixels; na een klik op een staal wisselt de naam en het voorbeeld.
- `manage.py test tests`: 194 tests, alle geslaagd (nieuw: `tests/test_aan_tafel.py`).
- Contrast van de tekst in alle vier kleuren van Aan tafel minstens 4,5:1, ook op het plaatskaartje en de menukaart; de tekst onderaan het openingsscherm staat op een eigen donker vlak, omdat het hout bij Kaarslicht licht is.
- In Chromium (Playwright) op 390 pixels: openingsscherm en kop in alle vier kleuren, de secties in Haardvuur en Schotse ruit, en het openen op drie momenten.
- Muziek: knop op spelen, geen fouten, niveau 0,1 tot ongeveer 0,4 zonder vervorming.

## Uitnodiging of wenskaart (28 september 2026)

- `manage.py test tests`: 202 tests, alle geslaagd (nieuw: `tests/test_wenskaart.py`: de keuze, publiceren zonder evenement, verplichte velden bij een uitnodiging, de schakelaar op de ontwerppagina en het voorbeeld als wenskaart voor alle zes kerstontwerpen).
- In Chromium (Playwright): op de ontwerppagina van Aan tafel 'Wenskaart' aangeklikt; het voorbeeld in de telefoon toonde 'Een kerstgroet voor jou' en 'Fijne feestdagen' en de startknop nam `soort=wenskaart` mee. Het voorbeeld als wenskaart op 390 pixels bekeken (geen datum, menu of aanmelden). In het samenstellen verdwijnen 'Wanneer' en 'Waar' bij het kiezen van Wenskaart. Geen fouten in de console.

## Homepage: kaart in 3D met sterretjes (28 september 2026)

- De kaart in de kop zweeft, kantelt mee met de muis (op de telefoon draait hij vanzelf), krijgt een lichtglans en een tweede kaart erachter; de achtergrondfoto schuift licht mee; gouden sterretjes rond de kaart en een glitterspoor achter de muis (`static/js/hero3d.js`, stijl in `static/css/vierlief.css`).
- `manage.py test tests`: 204 tests, alle geslaagd (nieuw: `tests/test_home3d.py`).
- In Chromium (Playwright): muisbeweging over de kop op 1366 pixels (de kaart kantelt, sterretjes zichtbaar), telefoonformaat 390 met aanraken (kaart draait vanzelf), 'minder beweging' (geen animatie en geen kanteling), en op 360, 390, 768 en 1366 pixels geen horizontaal scrollen en geen fouten in de console.

## Wenskaart zonder dresscode, praktische info en contact (28 september 2026)

- `manage.py test tests`: 208 tests, alle geslaagd (nieuw in `tests/test_wenskaart.py`: wat een wenskaart en een uitnodiging tonen, het voorbeeld van alle zes kerstontwerpen als wenskaart zonder 'Vragen?' of 'Goed om te weten', de stap Afsluiting, het overslaan van Aanmelden en het bewaren van de verborgen gegevens).
- In Chromium (Playwright) op 390 pixels: een wenskaart samengesteld (Wenskaart gekozen, afzender ingevuld); de voortgang toont 8 stappen met 'Afsluiting' en zonder 'Aanmelden', de stap Afsluiting toont alleen de afsluitende wens en 'Volgende' gaat naar Foto's. Geen fouten in de console.
- De deelbare voorvertoning is opnieuw gemaakt met de nieuwe wenskaarten.

## Bruiloftsontwerp Voor altijd (28 september 2026)

- `manage.py test tests`: 215 tests, alle geslaagd (nieuw: `tests/test_voor_altijd.py`).
- Contrast van de tekst in alle vier kleuren minstens 4,5:1.
- In Chromium (Playwright) op 390 pixels: openingsscherm en kop in alle vier kleuren, de hele pagina in Bordeaux, het openen op drie momenten (deksel open, ringen omhoog en glinstering, inzoomen); op 360 pixels voor bruiloft, verloving en jubileum geen horizontaal scrollen en geen fouten. Een tik op het midden van het doosje komt bij de openingslink aan.
- Muziek: knop op spelen, geen fouten; niveau 0,14 tot 0,21 over de eerste 32 seconden (violen vanaf ongeveer 10 seconden), zonder vervorming.

## Nieuwe vormgeving van de website en het lakzegel (29 september 2026)

- `manage.py test tests`: 227 tests, alle geslaagd (nieuw: `tests/test_vormgeving2026.py`; bijgewerkt: `test_atelier`, `test_home3d`, `test_kerst`, `test_site`).
- In Chromium (Playwright): home, Zo werkt het, Prijzen, Inspiratie en Over ons op 1366 en 390 pixels volledig gefotografeerd, zonder fouten in de console; op 360, 390, 768 en 1366 pixels geen horizontaal scrollen op deze vijf pagina's.
- Envelop in de kop: op 390 pixels met aanraken geopend (`aria-expanded` wordt `true`, de link naar het werkende voorbeeld is bovenaan en aanklikbaar); op 1366 pixels met de muis; met 'minder beweging' geopend met Enter; zonder JavaScript opent hij bij aanwijzen.
- Lakzegel: Liefde op papier, Lauwerkrans (Atelier-envelop) en Winterlicht gerenderd zonder en met de functie `zegel`: zonder een motief in rood of groen (groen bij een groene kleurvariant), met de initialen.
- Gevonden en opgelost: een commentaar over meerdere regels in `designs/winterlicht/v1/_zegel.html` verscheen als tekst op de envelop (Django-commentaar `{# #}` mag maar één regel zijn). Nu één regel, met een test.
- Niet gecontroleerd: de pagina's op `vaylide.onrender.com` zelf (afgeschermd met een wachtwoord dat ik niet heb); alleen de nieuwe statische bestanden en `/healthz` zijn daar gecontroleerd.

## Mollie-testbetalingen (29 september 2026)

- `manage.py test tests`: 235 tests, alle geslaagd (nieuw: `tests/test_mollie_testmodus.py`, met een nagebootste Mollie-API): betaling aanmaken met https-webhook, pas betaald na bevestiging door Mollie, vier meldingen geven één verwerking, afgebroken betaling publiceert niet en kan opnieuw, webhook bereikbaar achter het wachtwoord van de testversie (pagina's niet), een status in de melding wordt genegeerd, en een `live_`-sleutel wordt in testmodus geweigerd (de site start niet en bestellen roept Mollie niet aan).
- Niet gecontroleerd: een echte Mollie-testbetaling. Daarvoor is de testsleutel nodig (die zet de eigenaar zelf in Render) en inloggen op de afgeschermde testversie. De stappen staan in `docs/MOLLIE_TEST.md`.
- Voettekst (29 september 2026): `manage.py test tests` 241 tests, alle geslaagd (nieuw: `tests/test_voettekst.py`). In Chromium op 1366 en 390 pixels: betaalmethoden iDEAL en PayPal en het Instagram-icoon in de voettekst, geen fouten en geen horizontaal scrollen. Op Render: de webhook `/webhooks/betaling/mollie/` komt langs het wachtwoord (404 zolang `VIERLIEF_PAYMENT_PROVIDER` nog `test` is, geen 401).

## Voorbereiding livegang (29 september 2026)

Lokaal in testmodus (gesimuleerde betaling en e-mail). De testversie op Render is afgeschermd met een wachtwoord dat
ik niet heb; daar zijn alleen `/healthz`, de statische bestanden en de webhook (langs het wachtwoord) gecontroleerd.

- `manage.py test tests`: 258 tests, alle geslaagd. Nieuw: `test_verwerking_levering.py` (levering als aparte taak,
  herhaling na een onderbreking levert precies één keer, e-mailstoring zonder dubbele mail, vastgelopen bestellingen
  in het beheer, eigen 404-pagina), `test_offsite.py` (versleutelde tweede back-uplocatie) en `test_ai_koppeling.py`
  (AI-aanroep nagebootst). Bijgewerkt: de hersteltest in `test_productie.py` gebruikt nu een verse catalogus.
- **Klantreis in de browser** (`e2e/klantreis.cjs`, Chromium, op 390 en 1366 pixels, elk 37/37 geslaagd):
  - inloggen met code;
  - alle stappen van het samenstellen, en gegevens opslaan;
  - een foto uploaden, en een nepbestand dat met een melding wordt geweigerd;
  - bestellen en betalen, publicatie, en de link op de statuspagina;
  - een gast opent de uitnodiging en meldt zich aan; het antwoord staat in Mijn Vaylide en in de CSV-export;
  - een afgebroken betaling publiceert niet, het ontwerp blijft bewaard, en opnieuw betalen lukt;
  - een andere klant krijgt 404 op vijf adressen van klant A, zonder login volgt doorsturen naar inloggen, en een
    klant komt niet in het beheer;
  - de beheerder logt in en opent vier beheerpagina's;
  - geen JavaScript-fouten.

  Met `DEBUG` aan toont de ontwikkelserver bij een 404 Django's eigen pagina; de Vaylide-404 is met een test gecontroleerd.
- **Hersteltest**: een back-up van de lokale testdatabase is teruggezet in een lege, nieuwe database met een eigen
  uploadmap.
  - Daarbij gevonden en opgelost: herstellen mislukte, omdat `migrate` de catalogus al met eigen nummers vult. De
    catalogus wordt nu eerst leeggemaakt; de test bootst dit na.
  - Na herstel waren de aantallen gelijk: 16 gebruikers, 18 uitnodigingen (7 online), 2 aanmeldingen, 8 bestellingen,
    11 betalingen, 5 bestanden (geen ontbrekend) en 22 e-mails.
  - De openbare uitnodiging (200), de gastenlijst van de eigenaar met het antwoord van de gast en het fotobestand
    werkten.
- **Breedtes**: 18 pagina's op 360, 390, 768 en 1366 pixels (72 weergaven).
  - Gevonden en opgelost: de ontwerppagina van de kerstontwerpen scrolde op 360 en 390 pixels zijwaarts (426 pixels
    breed; de schakelaar Uitnodiging/Wenskaart paste niet naast het label).
  - Daarna geen horizontaal scrollen, geen foutstatus en geen fouten in de console.
- `manage.py check --deploy` (met `DEBUG` uit en een lange geheime sleutel): alleen de bewuste meldingen W005 en W021.
- DNS van `vaylide.nl` opgevraagd (alleen gelezen, niets gewijzigd): zie `docs/DOMEIN.md`.
- Niet gecontroleerd:
  - de pagina's en de bestelroute op de Render-testversie zelf (wachtwoord);
  - een echte Mollie-testbetaling (sleutel);
  - echte e-mailbezorging (SMTP);
  - de AI met een echte sleutel;
  - een upload naar een echte tweede back-uplocatie (nog geen aanbieder gekozen).

## Bruiloftsontwerp Eerste dans (29 september 2026)

Een eigen ontwerp, geïnspireerd op een voorbeeldvideo van de eigenaar (geen kopie). Paleisdeuren met een lakzegel
(standaard- of persoonlijk zegel volgens het pakket), een balzaal met kroonluchter en bloemenslinger, en een getekend
bruidspaar: een blonde bruid in een witte jurk met sluier en een bruidegom in een zwart pak.

- `manage.py test tests`: 266 tests, alle geslaagd (nieuw: `tests/test_eerste_dans.py`).
- Contrast van de tekst in alle vier kleuren minstens 4,5:1, en de initialen op het zegel minstens 3:1.
- `e2e/effecten.cjs` voor Eerste dans: 8/8 geslaagd.
  - Gevonden en opgelost: de knal kwam te laat (na 700 ms, gemeten na 650 ms). Hij start nu bij 450 ms, als het zegel breekt.
- `e2e/toegankelijkheid.cjs` voor alle vier kleuren, dicht en open: geen bevindingen.
  - Gevonden en opgelost: de initialen op het zegel hadden te weinig contrast; de lak is dieper gemaakt.
- In Chromium (Playwright):
  - openen en de hele pagina op 390 pixels in alle vier kleuren;
  - op 360, 768 en 1366 pixels geen horizontaal scrollen en geen fouten in de console.
  - Gevonden en opgelost: het paar viel onder de voorbeeldbalk weg; het past zich nu aan de beschikbare ruimte aan.
  - Gevonden en opgelost: cijfers in Cormorant lazen als letters ("1" als "I"); getallen staan nu in DM Sans.
- Kaartbeeld gemaakt met `e2e/make_design_images.cjs`.
  - Het script zet nu `--inv-banner-h: 0px`, omdat het de voorbeeldbalk verbergt.

## Balzaal: standaardkaart en haarkleur (29 september 2026)

- `manage.py test tests`: 278 tests, alle geslaagd (nieuw: `tests/test_balzaal.py`).
  - Beelden: klein genoeg, transparant, niet uitgerekt.
  - Echte tekst in de kop, zegel volgens pakket, beweging alleen met beweging aan.
  - De haarkleurkeuze is verborgen zolang er beelden ontbreken. Met alle beelden (nagebootst) wordt de keuze bewaard
    en getoond; na een andere wijziging blijft de keuze staan; onbekende waarden vallen terug op het standaardpaar.
- `e2e/effecten.cjs` voor Balzaal: 8/8.
- `e2e/toegankelijkheid.cjs` voor beide kleuren, dicht en open: geen bevindingen.
- In Chromium (Playwright):
  - openen op 390 pixels in vier momenten: envelop, zaal, paar, bloemen en namen;
  - zonder JavaScript direct leesbaar met paar en namen;
  - 'minder beweging': geen lopende animaties;
  - op 360, 390, 768 en 1366 pixels geen horizontaal scrollen en geen fouten.
  - Gevonden en opgelost: tekst onder de bloemen en de locatie achter het hoofd van de bruidegom (namen nu op één
    regel, tekst boven de bloemen); lichte strepen in de gesloten envelop.
  - Gevonden en opgelost: het kaartbeeld toonde geen paar (bevroren intro-animatie). De lagen verschijnen nu alleen
    tijdens een echte opening.
- Hele klantreis met Balzaal (`KLANTREIS_ONTWERP=balzaal e2e/klantreis.cjs`): 37/37 op 1366 en 39/39 op 390 pixels.
  - Nieuw in de controle: de QR-code downloaden, en 404 voor een andere klant.
- Niet gedaan: de haarkleurvarianten (acht beelden ontbreken, zie `docs/BALZAAL.md`).

## Balzaal: eigen gezichten (29 september 2026)

- `manage.py test tests`: 289 tests, alle geslaagd (nieuw: `tests/test_gezichten.py`, met fictieve foto's).
  - **Standaard uit:** onzichtbaar zonder functie, sleutel of prijs.
  - **Uploaden:** toestemming verplicht, nepbestand geweigerd, twee foto's nodig.
  - **Voorbeeld:** wordt gemaakt en telt als poging; een herhaalde taak maakt geen tweede beeld.
  - **Toegang:** alleen de eigenaar ziet foto's en voorbeeld.
  - **Van goedkeuren tot publiceren:** goedkeuren zet een 'scene'-upload op de kaart; de bestelling telt de extra
    optie mee; na betaling staat precies die versie op de openbare kaart, zonder nieuwe generatie; daarna ligt het vast.
  - **Opruimen:** de nachtelijke opschoning verwijdert de losse foto's.
  - **Pogingen:** zijn beperkt; een mislukte poging telt niet; bij drukte volgt één herhaling.
  - **Verwijderen:** haalt bestanden en de eigen versie weg; een verwijzing naar een upload van iemand anders wordt
    genegeerd.
  - **Gemini-koppeling (nagebootst):** sleutel alleen in de header (niet in de URL of logs), drie beelden in het
    verzoek, begrijpelijke foutmeldingen.
- In Chromium (Playwright), lokale server met `VIERLIEF_FACES_PROVIDER=test`, 12/12 geslaagd, zowel direct als met
  achtergrondverwerking:
  - de knop in Stijl, geen toestemming geweigerd, foto's opslaan;
  - voorbeeld maken, waarbij de pagina vanzelf ververst, en de pogingen tellen;
  - goedkeuren en het voorbeeld in de editor;
  - de optie in de bestelling, testbetaling, en de gast ziet de goedgekeurde versie;
  - na betaling vast, geen JavaScript-fouten.
  - Gevonden en opgelost: na een mislukte poging kreeg de nieuwe poging dezelfde taaksleutel en liep niet. Nu een
    teller die altijd oploopt.
- Niet getest: de echte Gemini-API (geen sleutel) en de kwaliteit en gelijkenis van echte bewerkingen.

## Kleurkeuze op de ontwerppagina (29 september 2026)

- De losse ronde stalen zijn vervangen door knoppen met drie kleurbolletjes en de naam van de kleurvariant; de gekozen variant heeft een donkere rand.
- `manage.py test tests`: 289 tests, alle geslaagd.
- In Chromium op 1366, 390 en 360 pixels (Middernacht, Winterlicht, Eerste dans): een andere kleur kiezen werkt zonder herladen en de knop wordt gemarkeerd; geen horizontaal scrollen en geen fouten.

## Balzaal als special, dans en haarkleur (29 september 2026)

- `manage.py test tests`: 306 tests, alle geslaagd (nieuw: `tests/test_specials.py`, `tests/test_balzaal_dans.py`).
  - **Specials:** apart op de collectiepagina; zonder eigen meerprijs niet te bestellen (ook niet via een optie met
    een andere code); met meerprijs een zichtbare regel in de bestelling.
  - **Dans:** zonder videobestand geen dans en geen knop. Met een video (nagebootst): een videolaag met poster, zonder
    autoplay in de HTML, en een knop die pas met JavaScript verschijnt.
  - **Haarkleurvariant:** gebruikt zijn eigen scène en video. Eigen gezichten tonen geen dans van het voorbeeldpaar.
  - **Veo-koppeling (nagebootst):** 9:16, sleutel alleen in de header, taak afwachten en video downloaden.
  - **Haarkleur bij eigen gezichten:** gaat mee in de opdracht en wordt bewaard bij goedkeuring; een ongeldige
    waarde valt terug op de standaard.
  - **Bewaartermijn:** 30 dagen voor onbetaalde foto's.
- In Chromium: de collectiepagina met Specials op 1366 en 390 pixels, zonder horizontaal scrollen en zonder fouten.
- Klantreis met Balzaal en een lokale testmeerprijs (daarna weer verwijderd): 39/39 op 390 pixels.
- Niet gedaan (vraagt een sleutel en akkoord op de kosten):
  - de echte dansvideo (proefscène);
  - de acht haarkleurscènes;
  - de echte Gemini-bewerking van eigen gezichten.

## Je kaart, live naast de invulstappen (29 september 2026)

- `manage.py test tests`: 315 tests, alle geslaagd (nieuw: `tests/test_live_kaart.py`).
  - De kaart staat bij alle vijf invulstappen.
  - Wat je invult verschijnt in de kaart zonder dat het wordt opgeslagen. Na opslaan wordt een verouderd concept genegeerd.
  - Hoofdfoto en galerij zijn gemarkeerd.
  - Een andere klant krijgt 404.
  - Gasten krijgen nooit het live-script.
  - Er staat geen commentaar als tekst op de pagina.
- In Chromium (lokaal) op 1366×860 en 390×844, zonder horizontaal scrollen en zonder fouten in de console:
  - Namen typen: ze staan direct op de kaart.
  - Hoofdfoto kiezen: de kaart springt naar de foto, met het label "Hoofdfoto".
  - Galerijfoto's kiezen: ze zijn gemarkeerd als "Fotogalerij".
  - Na herladen toont de kaart ook de keuzes die de browser teruggezet heeft.
  - De terug-knop van de browser krijgt er geen extra stappen bij.
  - Op 390 px: de knop "Bekijk je kaart" opent de kaart schermvullend.
- Niet gedaan:
  - de toegankelijkheidscontrole met axe op de editorpagina's;
  - Safari en echte telefoons.

## Foto's automatisch uitlijnen en verslepen (29 september 2026)

- `manage.py test tests`: 323 tests, alle geslaagd (nieuw: `tests/test_uitlijnen.py`).
  - **Gezichten herkennen:** YuNet vindt beide gezichten van het fictieve Balzaal-paar. De ballonnenfoto (geen mensen)
    geeft 0 gezichten.
  - **Na het uploaden:**
    - de foto met het paar wordt de hoofdfoto (niet de eerste foto), met het automatische middelpunt;
    - een bestaande hoofdfoto wordt nooit vervangen;
    - de galerij wordt niet vanzelf gevuld.
  - **Oudere foto's** worden bij het openen van de stap alsnog uitgelijnd.
  - **Zonder JavaScript** blijven de schuifbalken werken.
- Handmatig, met alle 28 voorbeeldbeelden van de site (`static/img/demo/`), waarvan 1 met mensen (het Balzaal-paar):
  - geen vals-positieve gezichten;
  - ongeveer 0,12 tot 0,6 seconde per foto.
  - De oudere OpenCV-methode (Haar) zag rozen en ballonnen aan voor gezichten; daarom YuNet.
- In Chromium (lokaal):
  - Twee foto's geüpload: het bruidspaar werd automatisch de hoofdfoto, met de melding erbij.
  - Met de muis gesleept:
    - verticaal van 44 naar 76 procent;
    - ingezoomd (160%) ook horizontaal.
  - De foto blijft binnen het kader. Hier zat eerst een fout: ingezoomd liep de foto over de pagina.
  - "Automatisch uitlijnen" zet de foto terug.
  - De live kaart werkt zich bij.
- Niet gedaan:
  - echte klantfoto's (alleen fictieve beelden gebruikt);
  - slepen met een vinger op een echte telefoon;
  - Safari.

## Live kaart met goudfolie, geen scrollbalk, wervende betaalpagina (29 september 2026)

- `manage.py test tests`: 326 tests, alle geslaagd.
  - Het voorbeeldkader in stap 8 laadt met `?kader=1`: geen scrollbalk, de testbalk blijft staan.
  - Op de betaalpagina staat "Je bent er bijna voor je unieke kaart!".
  - Alle doorlopende animaties van de live kaart staan onder 'prefers-reduced-motion: no-preference'.
- In Chromium (lokaal, 1100 en 1366 pixels breed) bekeken: de gouden lijst, de gloed bij het bijwerken en de betaalpagina.
- Niet gedaan: klassieke scrollbalken van Windows nagebootst. Mijn testbrowser toont zwevende scrollbalken; het
  verbergen gebeurt met dezelfde CSS die de telefoonvoorbeelden op de site al gebruiken.

## Pakket bij de start, 'Jouw pakket' met upgrade, controle als checklist (29 september 2026)

- `manage.py test tests`: 335 tests, alle geslaagd (nieuw: `tests/test_pakket.py`).
  - **Start:** het pakket kiezen wordt onthouden; een onbekend pakket wordt genegeerd.
  - **Editor:** de labels volgen het pakket ("In Compleet", of bij Essentieel "Extra optie · € 9" met de prijs uit Beheer).
  - **Bestellen bij Essentieel:** "Jouw keuze", "Upgraden naar Compleet" (+ € 30) en de losse onderdelen.
  - **Na de upgrade:**
    - het pakket blijft onthouden;
    - er is geen upgrade meer en geen losse onderdelen;
    - muziek is niet meer aan te vinken;
    - "Langer online" blijft kiesbaar.
  - **Controle:** een checklist met "Nodig", of "Alles is compleet".
  - **Account:** "Doorgaan als gast" en "Log eerst in" op de start; "Inloggen" in de kop; "Afrekenen" bij een concept
    in Mijn Vaylide.
- In Chromium (lokaal):
  - Het beginscherm met de pakketten bekeken op 1280 pixels.
  - Bestellen bekeken op 1280 en 390 pixels, zonder horizontaal scrollen.
  - Op "Upgraden naar Compleet" geklikt: het totaal werd € 69.
- `e2e/klantreis.cjs` gebruikt nu `?package=essentieel`. Het script is niet opnieuw gedraaid.

## De onthulling na betaling (29 september 2026)

- `manage.py test tests`: 338 tests, alle geslaagd (nieuw: `tests/test_onthulling.py`).
  - De show verschijnt alleen bij een gepubliceerde uitnodiging, met delen via WhatsApp, de QR-code en de link.
  - Alle animaties hangen aan `.is-spelen`. Het script zet die klasse niet bij 'minder beweging'.
- In Chromium (lokaal, testbetaling gesimuleerd) op 1280 en 390 pixels:
  - de envelop gaat open en de kaart komt omhoog;
  - confetti, vuurwerk en goudstof;
  - daarna de titel en de knoppen;
  - geen fouten in de console en geen horizontaal scrollen.
- Nog niet op Render: niet gepusht op verzoek van de eigenaar (die testte toen de Mollie-betalingen).

## V-monogram en de kaart die omdraait (29 september 2026)

- `manage.py test tests`: 340 tests, alle geslaagd.
  - Het V-monogram staat onderaan Liefde op papier, Middernacht, Winterlicht en Ballonfeest.
  - Het "Gefeliciteerd"-scherm gebruikt de draaiende kaart met het hele logo op de achterkant, zonder envelop.
- In Chromium (lokaal):
  - Het monogram bekeken op Middernacht (donker, 390 pixels).
  - Homepage op 1280 pixels: de kaart draait om van de logo-achterkant naar de uitnodiging, zonder uitsteeksels.
  - "Gefeliciteerd": de kaart komt op met de achterkant en draait om naar het ontwerp.
- Niet gedaan:
  - vloeiendheid gemeten op een echte telefoon;
  - de toegankelijkheidscontrole met axe op de homepage.

## Zachte envelop, VAYLIDE in hoofdletters, nieuwsbrief, inloggen op de telefoon (29 september 2026)

- `manage.py test tests`: 346 tests, alle geslaagd (nieuw: `tests/test_nieuwsbrief.py`).
- **Envelop** (homepage en "Gefeliciteerd"), in Chromium (lokaal) op 1280 pixels:
  - dicht: een ronde klep met lakzegel;
  - openen: het zegel verdwijnt, de klep vouwt omhoog met de gouden voering, de kaart glijdt eruit;
  - bij "Gefeliciteerd" komt de confetti op het moment dat de kaart eruit komt.
- **VAYLIDE:** in hoofdletters in alle zichtbare tekst (pagina's, e-mails, meldingen, het beheer). Commentaar en technische
  namen zijn niet aangepast.
- **Nieuwsbrief:**
  - bij het bestellen een eigen vinkje dat standaard uit staat; akkoord met de voorwaarden alleen is geen toestemming;
  - vastgelegd met datum en de tekst van de toestemming;
  - aan- en afmelden in Mijn VAYLIDE;
  - in het beheer een kolom, een filter en een CSV-lijst;
  - na het verwijderen van een account is de toestemming weg.
- **Inloggen op de telefoon (390 pixels):**
  - "Inloggen" staat rechtsboven naast het menu;
  - de hele route doorlopen: e-mailadres, de code (in testmodus op het scherm), en je komt in Mijn VAYLIDE;
  - uitloggen via Mijn VAYLIDE.
- **Betaalmethoden:** Klarna (alle varianten als één) en Riverty worden herkend. Logo's voor creditcard, Klarna en Riverty
  zijn er nog niet (zie `docs/INVULLIJST.md`).

## Envelop en lakzegel naar keuze, KvK en btw, betaalmethoden (29 september 2026)

- `manage.py test tests`: 354 tests, alle geslaagd (nieuw: `tests/test_envelop.py`).
  - **Het blok "Envelop en lakzegel":** staat alleen bij ontwerpen met een zegel.
  - **Keuzes op de kaart:** de envelopkleur, de zegelkleur en de initialen verschijnen op de kaart. Initialen worden
    opgeschoond.
  - **Eigen logo:**
    - het logo komt op het zegel, met doorzichtigheid (hoogstens 600 pixels);
    - een witte achtergrond wordt doorzichtig;
    - na betaling staat het logo ook op de gepubliceerde uitnodiging;
    - na verwijderen gaat het zegel terug naar initialen.
  - **Andere stijlkeuzes** (zoals eigen gezichten) blijven bewaard.
  - **Pakketten:** Essentieel heeft nu ook het persoonlijk zegel (migratie `catalog/0004`). Prijzen zijn niet gewijzigd.
  - **Specials:** zonder eigen meerprijs geldt de pakketprijs.
  - **Betaalmethoden:** alleen iDEAL, creditcard en PayPal, ook als er in Mollie meer aanstaat.
  - **KvK 94261423 en btw-id NL212227221B02:** in de voettekst, bij Contact, in de privacyverklaring en in de
    voorwaarden. Zonder adres.
- **In Chromium (lokaal):** envelop Salie, zegel Goud en initialen "J&M" gekozen. De live kaart toont bij de stap Stijl de
  dichte envelop en werkt zich bij.
- Envelop bijgewerkt (homepage, 1280 pixels, lokaal bekeken):
  - na het openvouwen verdwijnt de klep zacht, zodat er geen gouden punten meer naast de kaart uitsteken;
  - de binnenkant is ingetogen crème;
  - "Bekijk het voorbeeld" staat onder de envelop, niet meer over de namen;
  - sluiten gaat in omgekeerde volgorde: eerst de kaart, dan de klep.
- **Onder "Gefeliciteerd"** (`orders/_besteloverzicht.html`):
  - een tijdlijn "Zo is je bestelling verwerkt" met gouden vinkjes: op de computer naast elkaar, op smallere schermen
    onder elkaar;
  - een bon met bestelnummer, datum, betaalmethode, de onderdelen en het totaal.
  - Lokaal bekeken op 731 pixels, zonder horizontaal scrollen. De test controleert de tijdlijn en de bon.

## Totaalcontrole vóór het online zetten (29 september 2026)

- `manage.py test tests`: 354 tests, alle geslaagd. `makemigrations --check`: geen ontbrekende migraties.
- **Klantreis in Chromium** (`e2e/klantreis.cjs`, lokaal, testmodus), op 390 én 1366 pixels: **39/39** controles. Doorlopen:
  - inloggen met code, alle stappen, foto uploaden (goed en fout);
  - geslaagde betaling met publicatie en de onthulling;
  - gast meldt zich aan, antwoord en export in Mijn VAYLIDE, QR-code;
  - afgebroken betaling en opnieuw betalen;
  - toegangsrechten (andere klant 404, zonder login naar inloggen, klant niet in het beheer);
  - het beheer;
  - geen JavaScript-fouten.
  - De eerste run liep vast: het testscript zocht op de bedankpagina een kenmerk (`data-phase`) dat met de nieuwe opmaak
    wegviel. Teruggezet, daarna alles geslaagd.
- **Toegankelijkheid** (axe-core, WCAG 2.0/2.1 A en AA): **0 overtredingen** op 24 pagina's (12 pagina's op 390 en 1366
  pixels). Dat zijn: home, collectie, prijzen, contact, voorwaarden, start, Mijn VAYLIDE, gegevens, stap Stijl (envelop en
  zegel), stap Foto's, de bedankpagina (onthulling en bon), en de start zonder gelegenheid.
- **Live-modus met nep-waarden (geen echte sleutels):**
  - zonder betaalprovider weigert de site te starten;
  - in testmodus weigert hij een live-sleutel;
  - `check --deploy` geeft alleen de bewuste meldingen W005 en W021.
- **Testsite (zonder wachtwoord):**
  - `/healthz` geeft 200 en de pagina's geven 401;
  - de Mollie-webhook is bereikbaar (400 zonder id), de gesimuleerde betaling bestaat niet (404).
- Betaalmethoden op de testsite: daar stonden Klarna, Riverty en Pay by Bank nog, uit een bewaarde lijst van vóór de
  update. De bewaarde lijst wordt nu ook gefilterd, en de sleutel is vernieuwd (`v2`). Creditcard heeft nu het aangeleverde
  Mastercard-logo. Test in `tests/test_voettekst.py`.

## Algemene voorwaarden, looptijd, bevestiging en herroepingsfunctie (30 september 2026)

Lokaal op de branch `claude/algemene-voorwaarden`; niet online gezet.

- `manage.py test tests`: 376 tests, alle geslaagd (nieuw: `tests/test_voorwaarden.py`, 22 tests). Getest:
  - **Kalendermaanden:** 29 september + 6 = 29 maart; 31 januari + 1 = 28 februari (2027) of 29 februari (2028);
    31 augustus + 6 = 29 februari 2028.
  - **Einddatum:** tot het einde van de dag in Nederlandse tijd, ook als de betaling in UTC nog op de vorige dag valt.
  - **Vastleggen:** de einddatum komt van de bevestigde betaling en wordt één keer vastgelegd. Herhaalde betaalmeldingen
    en later publiceren verschuiven hem niet; een eerder beloofde datum blijft staan.
  - **Bestellen:**
    - twee losse vinkjes, beide standaard uit;
    - zonder toestemming voor directe levering geen bestelling;
    - de versie van de voorwaarden en de toestemming worden vastgelegd;
    - een waarschuwing als de online periode vóór het evenement eindigt.
  - **Bestelbevestiging:** pakket, aankoopdatum, einddatum, toestemming, versie, KvK-nummer, e-mailadres en de link om te
    herroepen, met de voorwaarden als bijlage. De bedankpagina toont de einddatum en de versie.
  - **Voorwaarden:**
    - de invulvelden zijn zichtbaar zolang de gegevens ontbreken;
    - ingevulde gegevens verschijnen op de voorwaarden en de contactpagina;
    - downloaden werkt, oude versies zijn te openen, een onbekende versie geeft 404.
  - **Contact & bedrijfsgegevens:** bereikbaar via de footer, zonder telefoonnummer.
  - **Live-modus:** de site weigert te starten zonder juridische naam en adres.
  - **Herroepingsfunctie:**
    - de juiste knopteksten;
    - registratie met koppeling via bestelnummer en e-mailadres;
    - een ontvangstbevestiging met tijdstip en een melding aan de eigenaar;
    - geen financiële wijziging;
    - een verkeerd e-mailadres wordt niet gekoppeld;
    - bots worden geweerd;
    - afhandelen in het beheer;
    - vooraf ingevuld vanuit een bestelling.
- **Klantreis in Chromium** (`e2e/klantreis.cjs`, bijgewerkt voor het tweede vinkje): 39/39 op 390 en 1366 pixels.
- **Toegankelijkheid** (axe-core, WCAG 2.0/2.1 A en AA): 0 overtredingen, onder meer op `/voorwaarden/`,
  `/voorwaarden/versie/2026-09-29/`, `/herroepen/` en `/contact/`, op 390 en 1366 pixels.
- **In de browser bekeken** (390 pixels, geen horizontaal scrollen): de voorwaarden met invulvelden en de knoppen downloaden
  en afdrukken, "Contact & bedrijfsgegevens", en de herroepingspagina.
- **Niet gedaan:**
  - een echte e-mail met de bijlage (de testomgeving gebruikt alleen de outbox);
  - afdrukken of opslaan als pdf in echte browsers;
  - een juridische toetsing.

## Privacyverklaring (30 september 2026)

Lokaal, branch `claude/privacyverklaring`, testmodus. Zonder echte klantgegevens; de klantreis gebruikt fictieve
testklanten uit `e2e/klantreis_setup.py`.

- `manage.py test tests`: 394 tests, alle geslaagd (nieuw: `tests/test_privacyverklaring.py`, 18 tests). Getest:
  - alle onderdelen en de cookies staan erin;
  - de bewaartermijnen komen uit de instellingen;
  - de invulvelden zijn zichtbaar op de testversie;
  - Mollie en Anthropic staan er alleen in als ze echt actief zijn;
  - de e-maildienst moet een naam hebben;
  - eigen gezichten staat uit, en aanzetten blokkeert de livegang;
  - de controle vóór livegang: geen fout in testmodus, fout `vaylide.E001` in live-modus, en geen fout als alles is ingevuld;
  - links in de footer, bij inloggen, contact, herroepen, foto's, bestellen, extra wens, het aanmeldformulier en de AI-hulp;
  - het nieuwsbriefvinkje staat standaard uit;
  - de levensduur van de cookies, en de aanmeldcookie is HttpOnly en hoort bij het pad van één uitnodiging;
  - Mollie krijgt geen e-mailadres of naam;
  - er zijn geen velden voor gezichtskenmerken;
  - verlopen sessies en cachewaarden worden opgeruimd, geldige blijven.
- `manage.py check` met nep-livewaarden: fout `vaylide.E001` met de lijst van open punten. Een verklaring met invulvelden
  kan dus niet live.
- **Browsercontrole cookies en opslag:**
  - pagina's: `/`, `/ontwerpen/`, `/contact/`, `/privacy/`, `/maken/` en `/voorbeeld/aan-tafel/`;
  - alle verzoeken gaan naar de eigen site;
  - geen tracking, geen iframes;
  - externe diensten (Google Agenda, Google Maps, WhatsApp) alleen als link;
  - localStorage alleen `vierlief-beweging`, na een tik op "Beweging", en weg na weer aanzetten;
  - `Set-Cookie`: alleen `vierlief_csrf` (1 jaar) op pagina's met een formulier.
- **Klantreis in Chromium** (`e2e/klantreis.cjs`): 39/39 op 390 en 1366 pixels.
- **Toegankelijkheid** (axe-core, WCAG 2.0/2.1 A en AA): 0 overtredingen op 32 pagina's (390 en 1366 pixels), onder meer
  `/privacy/`, `/inloggen/`, `/account/wensen/nieuw/`, de fotostap en drie voorbeelduitnodigingen met het aanmeldformulier.
- **In de browser bekeken** (375 pixels, geen horizontaal scrollen): de privacyverklaring; de tabellen staan op een smal
  scherm als kaartjes onder elkaar.

## Aanmelden zonder gevoelige gegevens, optie A (30 september 2026)

Lokaal, branch `claude/privacyverklaring`, testmodus, met fictieve testgegevens.

- `manage.py test tests`: 411 tests, alle geslaagd (nieuw: `tests/test_rsvp_vragen.py`, 17 tests). Getest:
  - de vaste vragen zijn neutraal, ook in de antwoordopties;
  - een aangepaste tekst of optie telt als eigen vraag;
  - nieuwe uitnodigingen: alleen naam, aanwezigheid en aantal personen;
  - geen "dieetwensen" of "allergieën" op de site en in de extra optie;
  - de studio biedt alleen vaste vragen, en een zelfgemaakt verzoek met een eigen vraagtekst of toelichtingstekst wordt
    genegeerd;
  - u-vorm bij een zakelijk evenement;
  - oude eigen vragen blijven staan tot ze worden weggehaald, en tellen mee voor het maximum;
  - standaardformulier zonder vrij tekstveld; de uitleg staat bij beide vrije velden;
  - aanmelden en afmelden;
  - controle op de server: verplichte vraag, optie buiten de lijst, te veel personen, onbekend veld;
  - weergave voor de organisator en CSV-export;
  - een gepubliceerde uitnodiging met een oude eigen vraag blijft werken;
  - het rapport toont geen inhoud en verandert niets;
  - aanmeldgegevens komen niet in foutmeldingen.
- **Klantreis in Chromium** (`e2e/klantreis.cjs`, uitgebreid): 48/48 op 390 en 1366 pixels, onder meer:
  - vaste vragen kiezen en opslaan, zonder veld voor een eigen vraagtekst;
  - Compleet betalen;
  - de uitleg twee keer in het formulier van de gast;
  - de server weigert een lege verplichte vraag en een optie buiten de lijst;
  - aanmelden met 2 personen en een antwoord;
  - een tweede gast meldt zich af;
  - de organisator ziet vraag, antwoord en afmelding;
  - CSV-regel `Gast Klantreis;ja;2;Met de auto;Dancing Queen`.
- **Toegankelijkheid** (`e2e/toegankelijkheid.cjs`): 0 bevindingen op 24 pagina's (Aan tafel, Liefde op papier en
  Winterlicht, alle kleuren, dicht en open). De volledige run over alle ontwerpen bleef lokaal na 24 minuten hangen en is
  afgebroken: **niet opnieuw uitgevoerd**.
- `manage.py rsvp_vragen_rapport` lokaal: 70 uitnodigingen, 0 oude eigen vragen, 0 eigen toelichtingsvragen. **Op
  Render niet uitgevoerd.**

## Automatische orderverwerking (30 september 2026)

Lokaal, testmodus, nagebootste betaling en e-mail. Verslag: `docs/AUTOMATISERING.md`.

- `manage.py test tests`: 421 tests, alle geslaagd (nieuw: `tests/test_automatisering.py`, 10 tests). Getest:
  - een gewone bestelling zonder handeling in het beheer;
  - een late webhook nadat de klant het venster sloot (einddatum vanaf de betaling);
  - open en pending betalingen publiceren niet;
  - bij terugkeer vraagt de server de status zelf op;
  - een onderbreking na de betaling wordt later opgepakt zonder verschoven einddatum;
  - opnieuw uitvoeren verandert niets;
  - Compleet met "Langer online" is 24 maanden;
  - na de einddatum direct offline;
  - de mail met link en QR-bijlage;
  - een e-mail kan twee keer worden verstuurd als het vastleggen na het versturen mislukt.
- **Testsite (Render)** van buitenaf:
  - `/healthz` 200;
  - statische bestanden gelijk aan commit `c24a888`.
  - **Niet geverifieerd:** Render-dashboard, geplande taak, SMTP en webhookmeldingen.

## Weergave na de Render-test: testmelding, escaping en echte kaart (30 september 2026)

Aanleiding: testbestelling VL26-00005 op Render met SMTP via Vimexx. Lokaal getest, testmodus.

- `manage.py test tests`: 431 tests, alle geslaagd (nieuw: `tests/test_weergave_mail_bedankpagina.py`, 10 tests).
  - De e-mailtests en de bedankpaginatest falen op de oude code en slagen op de nieuwe (gecontroleerd).
  - Getest:
    - `&`, apostroffen en accenten staan letterlijk in de platte tekst en precies één keer geëscapet in de HTML;
    - HTML in namen blijft onschadelijk;
    - bestelmails met echte namen;
    - de testmelding in de mail volgt de e-mailmodus (outbox of SMTP);
    - de inlogcode staat alleen op het scherm bij outbox;
    - de herroepingspagina volgt de e-mailmodus;
    - de bedankpagina toont de echte kaart (kader naar `/u/<slug>/?embed=1&open=1`), geen voorbeeldbeeld en geen andere
      namen;
    - het kader mag alleen door de eigen site worden getoond (`SAMEORIGIN`, `frame-ancestors 'self'`); gewone
      uitnodigingen blijven `DENY`.
- **Klantreis in Chromium:** 51/51 op 390 en 1366 pixels, met het bruidspaar "Zoë d'Artagnan & Klantreis". Nieuw
  gecontroleerd op de bedankpagina:
  - echte kaart met deze namen, geen "Sanne" of "Daan";
  - de pagina springt niet (scrollY 0);
  - de kaart is passend verkleind.
- Opgemerkt: na veel klantreizen achter elkaar grijpt de limiet van 12 inlogcodes per uur per IP-adres in. Dat is
  bedoeld; lokaal de cache geleegd.

## Testsite op Render na deploy van 259aa65 (30 september 2026, avond)

**Deploy:**
- fast-forward `c24a888..259aa65` naar `claude/kerstkaarten-website-design-51mn9k`;
- vooraf een verse back-up `vaylide-20260930-201056.tar.gz` (189 records, 9 uploads), gecontroleerd door de eigenaar;
- terugzetten lokaal geoefend;
- GitHub-deployment "success"; statische bestanden gelijk aan `259aa65`; `/healthz` 200.

Getest in Chrome (koppeling met de browser van de eigenaar), testmodus met Mollie-testsleutel en SMTP via Vimexx.
Fictieve bestellingen; e-mails alleen naar het eigen adres van de eigenaar.

- **Beheer → Instellingen:** Testmodus, "Mollie (testsleutel, geen echt geld)", "SMTP via mail.zxcs.nl". De testbalk
  zegt "e-mails worden echt verstuurd".
- **Inlogpagina:** geen code meer op het scherm; de code komt per mail.
- **VL26-00006** (Compleet, iDEAL, Betaald, normale terugkeer):
  - de bedankpagina toont de echte kaart "Zoë d'Artagnan & Émile O'Neill … 12 juni 2027", zonder voorbeeldnamen;
  - online tot en met 30 september 2027;
  - de QR-code (lokaal ontcijferd) en de link openen de juiste uitnodiging;
  - vaste aanmeldvragen en twee keer de uitleg bij vrije velden;
  - meldingen: `webhook · paid` ("Betaald; verwerking gestart."), daarna `terugkeer · paid` ("Al verwerkt als betaald;
    melding genegeerd.");
  - leveringsmail: "voor Zoë d'Artagnan & Émile O'Neill", zonder `&amp;`.
- **VL26-00007** (Essentieel, afgebroken):
  - "Geannuleerd" op de testpagina van Mollie brengt de klant terug naar de keuze van de betaalmethode;
  - via "Vorige pagina" terug naar de winkel: de betaling blijft "open" bij Mollie en de bestelling "wacht op betaling";
  - de uitnodiging blijft een concept met "Afrekenen"; niets gepubliceerd.
  - De wachtpagina vraagt Mollie elke ~3 s om de status (een regel per keer); er is geen knop "opnieuw betalen".
- **VL26-00008** (Essentieel, Betaald, zonder terugkeer):
  - de klant is uitgelogd vóór het betalen; de terugkeer eindigde op de inlogpagina;
  - precies één melding: `webhook · paid` om 22:48:36 met "Betaald; verwerking gestart.", geen `terugkeer`;
  - publiceren, leveren en beide mails: klaar na 1 poging, verzonden;
  - 1 versie, gepubliceerd om 22:48, online tot en met 30 maart 2027;
  - bevestigingsmail met einddatum, toestemming en voorwaardenversie. De bedrijfsgegevens tonen nog invulvelden.
- **Niet door mij te zien:** de HTML-weergave en de bijlagen (QR-code, voorwaarden) in de ontvangen mail. Die
  controleert de eigenaar in de eigen mailbox.

## Mails als "show", voorwaarden-pdf en betaalwachtscherm (1 oktober 2026)

Lokaal getest, testmodus. Niet gepusht of gedeployd.

- `manage.py test tests`: 452 tests, alle geslaagd (nieuw: `tests/test_mails_en_wachtscherm.py`, 21 tests). Getest:
  - **Opbouw van de mails:**
    - leveringsmail = alternative[tekst, related[html, QR-png inline met Content-ID]], zonder losse bijlage;
    - bestelbevestiging = mixed[alternative, voorwaarden-pdf];
    - inhoud, links, 16 px tekst, geen JavaScript;
    - accountadressen alleen achter knoppen;
    - klantinvoer precies één keer geëscapet;
    - QR-download alleen voor de ingelogde eigenaar.
  - **PDF:**
    - opent inline;
    - bevat de hele versie en het bestelnummer;
    - een bestelling houdt haar eigen versie, ook als er een nieuwere is;
    - gasten zien geen voorwaarden, bestel- of accountlinks.
  - **Wachtscherm:**
    - geen regel in het beheer bij een ongewijzigde status (wel bij wijzigingen en bij webhooks);
    - de server vraagt de provider hoogstens eens per 10 s;
    - na 60 s de knop "Betaling hervatten", die naar dezelfde open betaling gaat;
    - een late betaling wordt gevonden;
    - bij "bank verwerkt" geen tweede betaling;
    - geannuleerd, verlopen en mislukt hebben elk een eigen scherm en pas dan een nieuwe poging;
    - een nieuwe bestelling controleert eerst de open betaling;
    - de webhook na hervatten publiceert één keer.
- **`e2e/wachtscherm.cjs`:** 10/10 op 390 en 1366 px: open betaling, hervatten (zelfde betaling), afgebroken, opnieuw,
  verlopen, opnieuw, betaald en online. 9 statusverzoeken per minuut (was 31).
- **Klantreis:** 51/51 op 390 en 1366 px.
- **Mailvoorbeelden** (Chromium, 390 en 900 px): geen horizontaal scrollen; ook zonder afbeeldingen leesbaar (effen
  donkere achtergrond, alt-teksten).
- **Voorwaarden-pdf** opent in Chrome (pdf-lezer).
- **Niet gecontroleerd:** de echte weergave in Outlook en Gmail. Daarvoor is versturen vanaf de testsite nodig, na een
  deploy.

## Vestigingsadres en bewaartermijnen (1 oktober 2026)

Lokaal, branch `claude/privacyverklaring`, testmodus, met fictieve testgegevens.

- `manage.py test tests`: 464 tests, alle geslaagd (nieuw: `tests/test_bewaartermijnen.py`, 12 tests). Getest:
  - het adres Handellaan 73, 8031 EG Zwolle staat op `/contact/`, in het modelformulier van `/voorwaarden/` en in de
    voorwaarden-pdf; niet op de homepage, niet op een gepubliceerde uitnodiging en niet in de bestelbevestiging of de
    leveringsmail (die verwijzen naar Contact & bedrijfsgegevens; de pdf-bijlage bevat het adres);
  - B1: een kaart die 60 dagen offline is blijft, na 91 dagen is hij weg; de bestelling blijft betaald, met regels en
    betalingen; een live kaart blijft staan;
  - B2: eerst één waarschuwingsmail (niet dubbel), 30 dagen later anonimiseren; inloggen na de waarschuwing houdt het
    account; accounts met een kaart of een open wens en beheerders blijven ongemoeid;
  - B3, B4, B5: contactberichten na 12 maanden, afgeronde wensen met berichten en bijlage (ook het bestand) na 12 maanden,
    herroepingen na 7 jaar; een open wens en een recente herroeping blijven;
  - B6: e-mailkopieën ouder dan 90 dagen verliezen adres, onderwerp en inhoud (soort, status en sleutel blijven); een mail
    in de wachtrij en een recente mail blijven; een opgeschoonde mail wordt niet meer verstuurd.
- `open_points()` met SMTP aan: nog alleen "bewaartermijn logbestanden bij de hostingpartij" en "juridische naam en
  rechtsvorm".
- **Testsite na deploy van 8be9b49** (Render-status `success`, bekeken in Chrome): `/contact/` toont Handellaan 73 /
  8031 EG Zwolle; het modelformulier in `/voorwaarden/` toont het adres; de voorwaarden-pdf geeft 200 (application/pdf);
  `/`, `/ontwerpen/`, `/privacy/` en `/voorbeeld/aan-tafel/` bevatten het adres niet. De privacyverklaring heeft nog twee
  invulvelden: juridische naam en de logtermijn van Render; de bewaartermijnen B1 tot en met B6 en Vimexx staan erin.

## Domein, juridische naam en logtermijn (1 oktober 2026, middag)

- **Domein:** vaylide.nl en www.vaylide.nl in Render "Verified"; certificaten van Google Trust Services (geldig tot 30
  december 2026). `https://www.vaylide.nl/contact/` geeft 301 naar `https://vaylide.nl/contact/`; http geeft 301 naar
  https; `https://vaylide.nl/healthz` geeft 200, de rest vraagt het previewwachtwoord. Vertraging kwam door een oude
  cache in de nameservers van Vimexx (antwoorden op DNSSEC-vragen), door Vimexx rond 14:38 geleegd.
- **KvK-register** (kvk.nl, nummer 94261423): "G.M.Bootsman Consultancy", eenmanszaak, Händellaan 73, 8031EG Zwolle.
  Juridische naam in Render gezet; op de testsite (/contact/) zichtbaar na de herstart. Adres in de code verbeterd naar
  Händellaan (nog niet gedeployd bij deze controle).
- **Logtermijn:** Render-werkruimte op het Hobby-abonnement (Billing); volgens render.com/docs/logging 7 dagen.
- `manage.py test tests`: 465 tests, alle geslaagd.

## Informatiepagina's open voor de Mollie-controle (1 oktober 2026, middag)

- Nieuw: `VIERLIEF_PREVIEW_OPEN_PUBLIC` (`core/middleware.py`). Met het previewwachtwoord aan zijn alleen de
  informatiepagina's zonder wachtwoord te bekijken (GET/HEAD). Op een afgeschermde testversie krijgt alles noindex en
  geeft `robots.txt` "Disallow: /". `robots.txt` noemt het pad van het systeembeheer niet meer.
- `manage.py test tests`: 467 tests, alle geslaagd (nieuw in `tests/test_preview.py`: welke pagina's open zijn, dat
  inloggen, maken, Mijn VAYLIDE, `/u/`, bestelling, testbetaling, beheer, systeembeheer en POST-verzoeken 401 geven,
  geen beheerlinks of testcodes op open pagina's, en robots.txt zonder het beheerpad).
- Back-up op Render vóór de deploy: `vaylide-20261001-132944.tar.gz` (482 kB).
- Na het aanzetten (Render, 1 oktober): anonieme controle van https://vaylide.nl met 27 punten, alle goed (10
  informatiepagina's 200 met noindex en testbalk, zonder beheerlinks of testcodes; 11 afgeschermde paden en 5
  POST-verzoeken 401; robots.txt alleen "Disallow: /"). In de logs vroeg een controlerobot pagina's zonder slot-slash op
  (/prijzen) en kreeg 401; nu verbeterd: zonder slash volgt een doorverwijzing naar de open pagina (getest).
- HEAD-verzoeken (1 oktober): de preview-afscherming liet HEAD op de open pagina's al door (/, /prijzen/, /voorwaarden/
  200), maar de contactpagina en het herroepformulier gaven 405 omdat ze alleen GET/POST toestonden. Nu ook HEAD
  (zonder inhoud); afgeschermde pagina's blijven 401, ook voor HEAD, PUT, PATCH en DELETE (getest).

## Live-test en vinkje voorwaarden (1 oktober 2026, avond)

- Live end-to-end test met VL26-00002 (Essentieel tijdelijk € 0,01, daarna direct terug op € 39): webhook ontvangen,
  betaling en bestelling betaald, kaart gepubliceerd, bestelbevestiging met voorwaarden-pdf en leveringsmail met QR
  verstuurd, aanmelding van een testgast opgeslagen en zichtbaar in Mijn VAYLIDE. VL26-00001 (€ 39) door Mollie verlopen.
- Het vinkje bij bestellen noemt nu "(versie 29 september 2026)" zonder het woord "concept" (test in
  `tests/test_flow.py`); de pagina met voorwaarden en de pdf tonen de status nog. `manage.py test tests`: 467 geslaagd.

## Aurora Nocturne, de kop (3 oktober 2026)

Alleen de kop van de special is gecontroleerd; de secties eronder zijn nog niet uitgewerkt. Alles lokaal, in testmodus, met een testuitnodiging (Sophie & Daniël, 14 juni 2027; `tools/aurora_nocturne/testuitnodiging.py`).

- **Tests**: 565 tests geslaagd (13 nieuwe in `tests/test_aurora_nocturne.py`; in `tests/test_effects.py` is het aantal ontwerpen van 45 naar 46 gegaan). `manage.py check` zonder meldingen.
- **Gezien in Chromium** (Playwright, video met tijdcode per beeld en schermafbeeldingen op de kernmomenten) op 390 × 844, 768 × 1024 en 1366 × 900, plus 1366 × 768 en 360 × 740 voor de eindstand: de hele opening, het portaal, de lampencascade, de namen en de rust. Het openingsscherm sluit op ±3,0 s na de tik, alles staat op ±5,6 s stil.
- **Framesnelheid** (`e2e/aurora_nocturne.cjs`, headless Chromium **zonder GPU**, 8 kernen opgegeven; absolute waarden zijn daardoor lager dan op een echt toestel): mobiel 390 px (pixelverhouding 3) 60 fps in wachtstand, zegel/envelop, reveal en rust, 55 fps in het portaal (geen frame boven 34 ms); tablet 768 px 59 / 59 / 23 (portaal) / 57 / 54 fps; desktop 1366 px 60 / 60 / 18 (portaal) / 46 / 45 fps. Het portaal is de zwaarste fase; bij de rustfase had het noorderlicht eerst 26 fps op desktop, na de `steps()`-aanpassing en een kleiner stofcanvas 45 fps. Niet getest: echte telefoons, CPU-vertraging, andere browsers.
- **Console en netwerk**: op alle drie de formaten 0 consolefouten en 0 mislukte verzoeken. **Horizontale overflow**: 0 pixels op 390, 768, 1366 (en 360 en 1366 × 768 bij de eindstand).
- **Minder beweging**: de uitnodiging opent in ±0,33 s, geen enkele lopende animatie, lampen en tekst direct zichtbaar, geen stofcanvas. **Beweging stilgezet** (knop): opent in ±0,30 s, geen lopende animaties. **Direct openen** (`#aanmelden`): geen openingsscherm, wereld komt tot rust, geen fouten.
- **Rustscène**: 1 canvas, 6 lopende animaties, 14 beeldlagen in de kop, geen `mix-blend-mode`, geen elementen met een eigen lichtje.
- **Gevonden en opgelost**: (1) de knop Beweging hing de pagina op: `classList.add` van een klasse die er al is schrijft het attribuut opnieuw en vuurde de eigen `MutationObserver` steeds opnieuw af (nu een hulpfunctie die alleen schrijft bij een verandering, plus een vlag zodat teruggedraaide callbacks niets starten); (2) de voorste mist gaf een grijze vlek met harde rand (nu egaler, blauwer en met zachte randen); (3) in het kaartformaat 480 × 600 raakte de tagline de torenspits (nu meet een klein script hoe groot het paviljoen onder de tekst mag zijn); (4) het portaal opende te abrupt (langere, zachtere groei).
- **Niet gecontroleerd**: axe/toegankelijkheid en contrast van dit ontwerp (`e2e/toegankelijkheid.cjs`), Safari, Firefox, echte telefoons, schermlezers, het geluid ("Met muziek" gebruikt de bestaande speeldoos).

### Aurora Nocturne, drie lichte kleurvarianten (3 oktober 2026)

Parelmoer & champagne (`parel`), Rozenmorgen (`roze`) en Saliemist (`salie`), naast de nachtvariant. Elke variant heeft eigen beelden (`img/<variant>/`) en een eigen envelop, openingsscherm en pagina in lichte kleuren.

- **Tests**: 569 tests geslaagd (4 nieuwe in `tests/test_aurora_nocturne.py`: vier paletten, tekstcontrast ≥ 4,5:1 voor de lichte varianten, elke variant tekent zijn eigen scène, alle gebruikte kleurvariabelen staan in de paletten). `manage.py check` zonder meldingen.
- **Gezien in Chromium** (statische voorvertoning, Playwright, schermafbeeldingen op zes momenten van de opening) op 390 × 844 en 1366 × 800, voor alle drie de varianten: openingsscherm, zegel, envelop, portaal, onthulling en eindstand. Daarna de secties onder de kop op 390 voor alle drie (met de foto's van de eigenaar). Op 390 en 1366: 0 pixels horizontale overflow, 0 consolefouten, 0 mislukte verzoeken.
- **Framesnelheid** (headless Chromium zonder GPU, voorvertoning; zelfde methode voor alle varianten, per fase in beelden per seconde): mobiel 390 px (pixelverhouding 3) zegel en envelop 60, portaal 52 tot 57, onthulling 60, rust 60; desktop 1366 px zegel en envelop 59 tot 60, portaal 19 tot 23, onthulling 46 tot 50, rust 45 tot 47. De lichte varianten wijken niet af van de nachtvariant.
- **Contrast**: de tekstkleuren van de pagina (tekst, grijs, kopgoud, knop, kaart, openingsscherm) zijn in de test op ≥ 4,5:1 gezet; de gemeten verhoudingen liggen tussen 5,5 en 15,4. De namen en kicker in de kop staan op de lucht en zijn alleen gezien, niet met axe gemeten.
- **Niet gecontroleerd**: axe (`e2e/toegankelijkheid.cjs`) voor de nieuwe varianten, Safari, Firefox, echte telefoons, het kiezen van een variant in de studio, het geluid.

### Aurora Nocturne, kleinere envelop en uitbundige omlijsting (3 oktober 2026)

Opdracht van de eigenaar: "Envelop te groot, de layout is aardig leeg. Kan dit mooier en anders? Graag zo uitbundig mogelijk."

- **Wat er veranderd is**: de envelop is kleiner en minder hoog (op een telefoon ±140 px breed en ±160 px hoog in plaats van ±290 × 386; hoogstens 220 px breed, verhouding 1 : 1,12 in plaats van 1 : 1,34); het openingsscherm heeft vier bloemenhoeken, drie bogen, een waaier van licht, sterretjes, "Je bent uitgenodigd" en de datum; de kop heeft bloemen in de bovenhoeken, een waaier van licht achter het paviljoen en opstijgende lampionnen; de rest van de uitnodiging heeft een datumboog, een tijdlijn, aftelbogen, een slinger boven het welkom en het aanmeldformulier, een paviljoen-icoon en sierlijsten. Nieuwe beelden per kleurvariant: `hoek.webp` en `slinger.webp`.
- **Tests**: 573 tests geslaagd (4 nieuwe in `tests/test_aurora_nocturne.py`). `manage.py check` zonder meldingen. De beelden per variant blijven samen onder 1 MB (±0,95 MB).
- **Gezien in Chromium** (statische voorvertoning) op 390 × 844 en 1366 × 800: openingsscherm, zegel, envelop, portaal, onthulling en eindstand voor alle vier de varianten, plus de secties onder de kop (datum, welkom met foto, programma, aftellen, locatie, dresscode, verhaal, goed om te weten, aanmelden, afsluiting) voor Parelmoer en Rozenmorgen. 0 pixels horizontale overflow, 0 consolefouten en 0 mislukte verzoeken op beide formaten voor Parelmoer, Rozenmorgen en Saliemist; voor Nachtblauw alleen de overflow en consolefouten op beide formaten.
- **Framesnelheid** (headless Chromium zonder GPU, per fase: zegel en envelop, portaal, onthulling, rust). Mobiel 390 px (pixelverhouding 3): 60 / 55 tot 59 / 58 tot 60 / 60 voor alle vier. Desktop 1366 px: 55 tot 57 / 22 tot 27 / 40 tot 41 / 51 tot 57. De eerste versie van de omlijsting kostte op desktop ±10 fps in de rust (de draaiende lichtwaaier) en liet het portaal op 11 tot 18 fps zakken; daarom staan de waaiers nu stil (in de kop alleen de bovenste helft), blijft de camera bij het portaal tot 3× inzoomen en verdwijnt de versiering sneller. Waarden schommelen een paar beelden per seconde tussen metingen.
- **Niet gecontroleerd**: axe, Safari, Firefox, echte telefoons, schermlezer, de lichte varianten op 360, 768 en 1024 px en met `prefers-reduced-motion` na deze wijziging (alleen de testsuite), de sectie Momenten met meer dan vier foto's.

## De officiële collectie: A/B/C samengesteld (4 oktober 2026)

Branch `claude/vaylide-master-collectie`, gebouwd op `claude/aurora-nocturne`. Zie `docs/COLLECTIE.md`.

- **Tests**: 587 tests geslaagd in één volledige run (14 nieuwe in `tests/test_collectie.py`, 6 bestaande testverwachtingen bewust aangepast aan de
  indeling, 14 ontwerptests laten verborgen ontwerpen tijdelijk zichtbaar zijn). `manage.py check` zonder meldingen, `makemigrations --check`: geen wijzigingen.
- **Platform**: vergeleken met `claude/aurora-nocturne` is er geen enkel bestand in studio, orders, processing, accounts, portal, wishes, beheer,
  invitations, templates, config, de Envelope Collection, `catalog/models.py`, `catalog/specials.py` of `catalog/effects.py` gewijzigd. Wel
  gewijzigd: `catalog/seed.py` (2 regels: C-ontwerpen starten op niet zichtbaar), `catalog/collectie.py` en migratie 0006 (nieuw) en `core/content.py`
  (kerstpodium op de homepage).
- **Migratie op een bestaande database** (de ontwikkeldatabase, 46 ontwerpen, aangemaakt vóór deze ronde): 9 ontwerpen verborgen, 5 specials,
  volgorde van 46 ontwerpen zonder dubbele nummers, niets verwijderd.
- **Gezien in Chromium** (1100 px breed): collectiepagina Specials met de vijf kaartbeelden in de goede volgorde (alle vijf laden), de
  bruiloftsfilter (A vóór B), de homepage met het kerstpodium met drie kaarten. Geen horizontale overflow, geen consolefouten.
- **Bestaande uitnodiging op een verborgen ontwerp**: werkt (status 200), terwijl `/ontwerpen/<code>/` voor bezoekers 404 geeft (test).
- **Niet gecontroleerd**: de kaartbeelden van de drie nieuwe specials op telefoonformaat in de collectie, Studio en bestellen per ontwerp na deze
  wijziging (alleen via de bestaande tests), Safari en Firefox, echte telefoons.

## Gouden Avond (4 oktober 2026)

Nieuw zelfstandig special-ontwerp op een eigen branch (`claude/gouden-avond`, lokaal, niet gepusht). Zie `docs/GOUDEN-AVOND.md`. Controles in Chromium (Playwright) op 360, 390, 768 en 1366 px, tegen de lokale ontwikkelserver in testmodus.

- **Weergave:** schermafbeeldingen per stap (dicht, uitlijnen, slot, draaien, deuren, feest, video, tekst) op 360, 390, 768 en 1366 px; geen horizontale scroll; de sleutel (176 × 124 px) staat volledig binnen het scherm, ook op 360 px; de tanden verdwijnen in het slot (afbeelding bij 'slot'); geen zwarte flits bij het openen van de deuren (helderheid van het portaal elke ±40 ms gemeten, donkerste punt 127 van 255, `e2e/gouden_avond_flits.cjs`).
- **Gedrag** (`e2e/gouden_avond_functies.cjs`, 31 controles geslaagd): toetsenbord (Tab naar de sleutel, Enter, focus op *Bekijk de uitnodiging*, scrollen naar de inhoud); overslaan midden in de opening (feest en deeltjes weg, video gepauzeerd op 0, scroll en inhoud vrij, 8 s later niets meer gestart) en vóór het gebruik van de sleutel; opnieuw beleven (twee keer helemaal door); 'minder beweging' (direct de open scène, geen deuren/sleutel/deeltjes, video handmatig af te spelen); geblokkeerde autoplay (opening loopt door, knop *Speel de scène af*, daarna speelt de video); terugkerende bezoeker en `#aanmelden` (direct open); beweging stilzetten tijdens de opening; geen consolefouten.
- **Hele klantreis** (`e2e/klantreis.cjs` met `KLANTREIS_ONTWERP=gouden-avond` en een tijdelijke special-prijs van € 1 in de lokale database, daarna verwijderd): 51/51 op 390 px en 51/51 op 1366 px: ontwerp kiezen, gegevens, programma, aanmelden, foto uploaden, stijl, voorbeeld, bestellen met testbetaling, de echte kaart op de bedankpagina, gastenlink, aanmelden en afmelden, antwoorden in Mijn Vaylide, export, afgebroken betaling, rechten en beheer. Het script was verouderd (derde vinkje *online_dienst* bij het bestellen en een testfoto die kleiner dan het minimum is geworden) en is bijgewerkt; dat geldt voor elk ontwerp.
- **Beeldsnelheid** (`e2e/gouden_avond_fps.cjs`, Chromium met echte GPU, tik tot 9 s): 390 en 1366 px, normale processor: deuren (0 tot 3 s) 60 fps, grootste beeld 17 ms; feest en video (3 tot 9 s) 59,6 fps, grootste beeld 33 ms (af en toe één van 50). Processor 4× vertraagd (zwakke telefoon), 360 en 390 px: deuren 59,3 tot 59,6 fps (grootste 33 ms), feest 51 tot 55 fps (grootste 50 tot 83 ms, een paar beelden). Het ongewijzigde prototype haalde in dezelfde meting voor het feest 44 tot 45 fps (4×) en ±45 fps (1×); de winst komt uit weglaten van `will-change` en de schaduw-filter op 145 deeltjes. Niet gemeten: een echte telefoon.
- **Leesbaarheid:** tekst over de video minstens 5,9 : 1 tegen de lichtste pixel erachter (poster en video; 360, 390 en 1366 px); `e2e/toegankelijkheid.cjs`: het dichte scherm is in orde, de open stand meldt contrast over de video (het script kan niet door een video heen meten, zie `docs/GOUDEN-AVOND.md`); axe-fouten: geen.
- **Rijkere uitnodiging eronder** (4 oktober 2026, op verzoek): rondgang langs alle banden op 390 en 1366 px met schermafbeeldingen (`e2e/gouden_avond_rondgang.cjs`), geen horizontale scroll, geen consolefouten; opening opnieuw gemeten met de nieuwe achtergrondlagen: deuren 60 fps (grootste beeld 17 ms), feest 59,3 tot 59,8 fps; op 1366 px blijft aan het eind van de opening (6,6 s, namen verschijnen) één beeld van 50 tot 67 ms over (de oorzaak is niet gevonden: het verdween niet door een van de onderdelen uit te zetten); 31 gedragscontroles opnieuw geslaagd; `e2e/toegankelijkheid.cjs`: geen bevindingen.
- **Tests:** `tests/test_gouden_avond.py` (17 tests), `tests/test_effects.py` (aantal ontwerpen 47). Volledige suite: zie het eind van deze alinea.
- **Niet gedaan:** een echte telefoon of tablet, Safari en Firefox, echte Mollie-betaling, uitrol naar de testsite (staging), de bestaande Balzaal-tests buiten de volledige suite om herhalen op een apparaat.
## Kerstbol (4 oktober 2026)

Nieuwe Special (kerst) op de lokale branch `claude/kerstbol`, vanaf `8c429a7`. Zie `docs/designs/kerstbol.md`. Controles in Chromium (Playwright) tegen de lokale ontwikkelserver, op 390 en 1366 px (`e2e/kerstbol.cjs`).

- **Opening** één keer helemaal bekeken (schermafbeeldingen op 0, 1,5, 3, 4,5, 6, 7,2, 8,5, 10,3 en 12 s): gesloten cadeau met 40 gouden fonkelingen en hint, geen video vóór de tik, na de tik speelt de video, op 6,5 s zijn de gouden fonkelingen weg en staan er 55 kristallen, na afloop staat de groet in beeld, de fonkelingen zijn verwijderd, de scroll is vrij en er is geen horizontale scroll.
- **Gedrag** (54 controles geslaagd, 27 per breedte): klikdoel minstens 44 px; overslaan midden in de opening en vóór de tik; opnieuw beleven (twee keer helemaal door); toetsenbord (Tab, Enter, focus op "Naar de kaart"); minder beweging (direct het eindbeeld, handmatig afspelen zonder fonkelingen); geblokkeerde autoplay (fallbackknop, daarna speelt de video); terugkerende bezoeker en `#aanmelden`; geen consolefouten.
- **Rondgang langs de kaart** op 390 en 1366 px: brief met foto (op breed scherm twee kolommen), "Ons jaar", momenten, kerstdiner, programma, aftellen, locatie, dresscode, goed om te weten, aanmelden, vragen en afsluiting; geen horizontale scroll.
- **Beeldvullende video en uitbundigere kaart** (op verzoek van de eigenaar, zelfde dag): de video vult het scherm (390 px van rand tot rand; 1366 px over de volle hoogte met een gloed uit de video aan de zijkanten), de kaart heeft smaragd-, bordeaux- en goudbanden, goudfolie, stralenkransen, lichtsnoeren, de foto in een sneeuwbol en de momenten als kerstballen. Daarna opnieuw: 54 gedragscontroles en de rondgang op 390 en 1366 px geslaagd, geen horizontale scroll, `e2e/toegankelijkheid.cjs` zonder bevindingen.
- **Overgang einde video, groet, eerste sectie** (`e2e/kerstbol_overgang.cjs`, 390 en 1366 px): de helderheid van de video blijft in de laatste seconden tussen 74 en 75 (geen flits, geen sprong); de groet verschijnt als zachte overgang over het laatste beeld (dekking 0 naar 1 in ±0,3 s); met realistische scrollbalken (klassiek op desktop, overlay op mobiel) is de plek en breedte van kop en video vóór en na de opening identiek (geen layout-sprong); de naad tussen de warme gloed van de kop en de groene kaart was op desktop een harde rand en is nu een zachte overgang (onderrand van de kop en van de video-kolom lopen uit naar het smaragd, de eerste sectie begint zacht). In een browser zonder scrollbalken (zoals headless Chromium) lijkt de breedte 10 px te verschillen; dat is een eigenschap van die testomgeving.
- **Studio:** de stappen Gegevens, Stijl, Voorbeeld en Bestellen laden voor een Kerstbol-concept; de stap Stijl legt de eigen opening uit.
- **Tests:** `tests/test_kerstbol.py` (16 tests) en de bestaande collectie-, effecten-, specials- en envelopstijltests (92 tests geslaagd). De hele suite en een volledige performance-audit zijn op verzoek niet gedraaid.
- **Niet gedaan:** de hele klantreis met testbetaling, een echte telefoon, Safari en Firefox, beeldsnelheid op een trage telefoon. Er is geen prijs voor de Special (`special-kerstbol`): zonder die optie is het ontwerp niet te bestellen.

## Special Strandboog (staging, 10 oktober 2026)

Ringdoosje dat opengaat op een filmscène, rand tot rand (zie `docs/STRANDBOOG.md`). In de collectie als special in groep A (`sort_order` 12, 51 ontwerpen, A 16).

- Gericht gedraaid (geen volledige suite): `tests.test_strandboog`, `test_collectie`, `test_effects`, `test_specials`, `test_gouden_avond`, `test_atelier`: 82 tests geslaagd.
- Lokaal in Chrome (H.264): `e2e/strandboog_functies.cjs` 22 van 22 en `e2e/toegankelijkheid.cjs ... strandboog` 0 bevindingen, vóór het samenbrengen met de collectie. Op staging is alleen gericht gecontroleerd (zie de oplevering).
- Niet gecontroleerd: Safari op een iPhone, Firefox, een oud Android-toestel, schermlezers.

## Kerstmarkt, Kerstpaleis, Kerstcoupé en Kerstbal (15 oktober 2026, lokaal)

Zie `docs/KERSTFILMKAARTEN.md`. Uitgevoerd:

- Hele suite `manage.py test tests`: 1001 tests geslaagd (1 overgeslagen). Met `VIERLIEF_PRICING_V2=1` ook de prijstests, en `controleer_prijzen`: getoond bedrag = offerte, één regel per kaart.
- Bestelstap, betaling (testmodus) en publicatie voor alle vier: € 24,95, Luxe, 12 maanden, geen pakketkeuze of toeslag (`test_prijsstructuur`).
- Lokaal in Chromium op 360, 390, 768 en 1366 px: voorbeeldpagina laadt zonder fouten, geen horizontaal scrollen, de film speelt na de tik (WebM), de opening wordt klaar, en na scrollen zijn alle onderdelen zichtbaar. Beelden bekeken op 390 en 1366 px.
- Niet gedaan: Safari op een iPhone, Firefox, een echte Android-telefoon, `e2e/toegankelijkheid.cjs` en `e2e/effecten.cjs` voor deze vier, de kleurvarianten in de browser (alleen de contrastcontrole in de tests), en de hele klantreis in de browser met uploaden van eigen foto's.

### Kerstbal v2 (15 oktober 2026, lokaal, voor- en na-meting)

- Gemeten met Chromium op 390x844 (dekking van omslag, kaart en kaartvlak per beeld en gemiddelde helderheid per schermafbeelding): laagste helderheid in de overgang v1 ± 16, v2 ± 27; de kaart is vanaf ± 3,6 s zichtbaar onder het wegvervagende omslag. Zelfde meting met geblokkeerde video: zelfde verloop.
- Verminderde beweging (opent na ± 0,4 s), geblokkeerde video, zonder JavaScript, 360x640, 768x1024 en liggend 844x390: gelijk aan v1, geen fouten.
- Hele suite: 1005 tests geslaagd (1 overgeslagen).
- Niet gedaan: Safari op een iPhone, Firefox, een echte telefoon, `e2e/toegankelijkheid.cjs` en `e2e/effecten.cjs` opnieuw voor v2.
- Kerstbal v2, rustigere kaart (lokaal): timing gemeten per beeld (kaart, omslag, kaartvlak) op 390 px; verminderde beweging (opent na ± 0,4 s), geblokkeerde video (opent na ± 6,0 s), zonder JavaScript, 360x640, 768x1024 en liggend: geen fouten. Hele suite 1005 geslaagd. Niet gedaan: axe/effecten opnieuw, echte telefoon, Safari, Firefox.

### Zwanenhart (15 oktober 2026, lokaal, `VIERLIEF_PRICING_V2=1`)

- Hele suite: 1027 tests geslaagd (1 overgeslagen), met een bestel- en publicatietest: Special, € 89,95, 12 maanden, geen pakketkeuze of toeslag. `controleer_prijzen` klopt.
- In Chromium op 390 px (met een VP9-kopie van de film, want H.264 speelt niet af): fasen van de opening, desktop 1366 px, verminderde beweging, geblokkeerde film (eindbeeld na ± 6 s), zonder JavaScript, toetsenbord, 360x640 en 768x1024; studio-voorbeeld, bestelstap, testbetaling, publicatie en gast met extreme namen (tags worden als tekst getoond). `e2e/toegankelijkheid.cjs`: 0 bevindingen (dicht en open).
- Niet gedaan: echte telefoon, Safari, Firefox, H.264 in een browser, `e2e/effecten.cjs`, het filmpje beluisterd (is stil).

### Zwanenhart: liggende telefoon en lange namen (15 oktober 2026, lokaal, `VIERLIEF_PRICING_V2=1`)

- Chromium (VP9-kopie van de film): de openingsknop ligt helemaal binnen het scherm, is bereikbaar met `elementFromPoint`, een tik start de film en er is geen horizontaal scrollen op 844x390, 667x375, 932x430 en 740x360; staand 390x844 en desktop 1440x900 zijn ongewijzigd.
- Zeer lange namen (`Zoë d'Artagnan & Émile`, `Max "de Ridder" van der Heijden-Smit`) in het eindbeeld: staand 390x844 en 360x640 en desktop 1440x900 vallen niet over de zwanen; liggend 844x390 en 667x375 staan de namen bovenin boven de zwanen (bekeken op screenshots). De lange namen zijn in de browser met een script in de kop gezet, omdat de voorbeeldpagina vaste namen heeft; de klassen staan ook in een test.
- Niet gedaan: echte telefoon, Safari, Firefox.
- Voorbereiding staging (15 oktober 2026, lokaal, `VIERLIEF_PRICING_V2=1`, nieuwe lege database): `controleer_prijzen` klopt (Luxe 14); per ontwerp in de browser (390 px, testmodus): ontwerppagina Luxe € 24,95 · 12 maanden, voorbeeld, samenstellen met een naam met speciale tekens, voorbeeld in de studio, bestelstap (geen pakketkeuze of toeslag, € 24,95), testbetaling, publicatie, gast opent de kaart (noindex). Kerstbal wordt na het inlezen vanzelf v2; de bestelling legt v2 vast. Hele suite 1006 geslaagd. Niet gedaan: echte Mollie, e-mail, staging zelf, Safari, Firefox, echte telefoon.
### Zwanenhart: voorbeeldkader, lakzegel en knoppen (16 oktober 2026, lokaal, `VIERLIEF_PRICING_V2=1`)

- Chromium (VP9-kopie van de film), voorbeeldkader op de ontwerppagina: vóór het herstel begon het direct bij het eindbeeld; nu gesloten envelop, tik op het lakzegel (of de knop) start de film, zegel gloeit, envelop opent, zwanen, namen. Mobiel en desktop.
- Volledige pagina 390x844, 360x640, 844x390 en 1440x900: het tikvlak ligt op het zegel, wordt geraakt (`elementFromPoint`), valt binnen het scherm en een tik start de film.
- 'Speel de opening opnieuw' ligt in het kleine kader niet meer onder Beweging en Muziek (bekeken op screenshot).
- Niet gedaan: echte telefoon, Safari, Firefox.

## Voorwaarden 16 oktober 2026 en privacyverklaring (lokaal)

Uitgevoerd op de lokale branch, testmodus, SQLite: de hele testset (1051 tests, 1 overgeslagen, geslaagd) en met `VIERLIEF_PRICING_V2=1` de tests van prijsstructuur, voorwaarden, nieuwe voorwaarden, privacyverklaring en wensen (101, geslaagd). Gedekt: twee versies naast elkaar en de oude ongewijzigd; `current()` volgt de schakelaar; de juiste versie bij bestellen, de bestelling, de bevestigingsmail en de pdf; maatwerk met verplicht vinkje en vastgelegde versie; invulvelden voor onbevestigde bedrijfsgegevens en de activeringsdatum; de conceptmelding; de looptijdtekst en bewaartermijnen in de privacyverklaring; alleen actieve diensten in de verklaring. Niet uitgevoerd: een juridische beoordeling, een controle in een echte browser, en een controle op staging of productie.

### Definitief maken en terugdraaien van de prijsschakelaar (16 oktober 2026, lokaal)

Uitgevoerd: de hele testset (1064 tests, 1 overgeslagen, geslaagd) in testmodus op SQLite. Nieuw getest: concept en invulveld standaard, definitief na `VIERLIEF_TEKSTEN_DEFINITIEF` en `VIERLIEF_ACTIVERINGSDATUM`, ongeldige datum, de live-controle die de nieuwe prijzen weigert zolang er iets openstaat, en dat bestaande bestellingen (voor en onder de nieuwe prijzen) bij aan- en uitzetten van de schakelaar hun prijs, voorwaardenversie, looptijd en bevestigingsmail houden. Niet gedaan: staging of productie (niet bereikbaar vanuit deze omgeving), juridische beoordeling.

## Afwerking 16 oktober 2026 (prijsweergave en scrollaanwijzing)

Echt uitgevoerd, lokaal met `VIERLIEF_PRICING_V2=1` en Chromium (390 en 1366 pixels breed): `tests.test_afwerking` en `tests.test_prijsstructuur` slagen; de volledige set draaide met 1062 geslaagd en 2 mislukte tests in `tests.test_voorwaarden_nieuw` (invulvelden voor bedrijfsgegevens), die ook zonder deze wijziging mislukten in deze omgeving (met de `.env` uit `.env.example`). Schermafbeeldingen van de scrollaanwijzing bij Kerstmarkt, Kerstcoupé en Kerstpaleis, en van de ontwerppagina, voor en na. Niet gedaan: echte telefoon, Safari, staging.

- Het prijslabel is nu `Luxe € 24,95` (geen streepje); op de ontwerppagina staan indeling en prijs met lettertype en witruimte uit elkaar.
- De knop "Lees verder" bij Kerstmarkt, Kerstcoupé en Kerstpaleis is nu een rustige aanwijzing "Scroll naar beneden" met een dun pijltje (zelfde link naar de kaart eronder).
- Haperingen: alleen onderzocht, zie het rapport in de projectmap.

## Afronding 16 oktober 2026 (prijzenpagina en Kerstmarkt-proef)

Echt uitgevoerd (lokaal, `VIERLIEF_PRICING_V2=1`, Chromium op 390 en 1366 pixels): de volledige set tests (1066 tests; de twee tests in `test_voorwaarden_nieuw` slagen alleen als `VIERLIEF_CONTACT_EMAIL` niet in de omgeving staat, omdat een gezet adres als bevestigd telt); `e2e/kerstmarkt.cjs` na de proef (alles ok); schermopname van de overgang van Kerstmarkt v1 voor en na het weghalen van de vaste vertraging van 0,5 s (de stilstand na het filmeinde werd ruwweg gehalveerd, van ± 0,7 naar ± 0,35 s). Niet gedaan: echte telefoon, Safari, staging, axe.

Footerfix en indelingsfilter (16 oktober 2026): `tests/test_bedrijfsgegevens.py` (KvK en btw-id in footer, contactpagina en bestelmail alleen als bevestigd via `VIERLIEF_KVK` en `VIERLIEF_BTW`) en `tests/test_afwerking.py` (het collectiefilter `?indeling=` toont geen onbeschikbare of inactieve ontwerpen).

## Kerstmagie bij de gelegenheid Kerst (16 oktober 2026, experimentele branch, nog niet live)

Op de stand van `claude/vaylide-master-collectie` met alleen Kerstmagie erbij; Python 3.13, Chromium (Playwright 1.56), testmodus.

- **Tests**: 1097 tests, 1095 geslaagd. De 2 mislukte (`test_voorwaarden_nieuw`: invulvelden voor het contactadres) falen op dezelfde manier op de ongewijzigde basis met dezelfde `.env` met een ingevuld contactadres; ze hangen niet samen met Kerstmagie. Nieuw in `tests/test_kerstmagie.py`: alleen de gelegenheid Kerst (en gelijk aan de vier andere kerstfilmontwerpen in gelegenheid, `envelope_mode` en opening), in de kerstcollectie en bij geen enkele andere gelegenheid, groep B, indeling Luxe als Kerstmarkt, prijs € 24,95 / 12 maanden voor Kerst en geen prijs voor andere gelegenheden, prijstabel ongewijzigd, bestellen en publiceren via de bestaande prijsstructuur zonder toeslag, de kleurcontrasten en de gedragsafspraken van de film (geen autoplay, geen bron in de HTML, vangnetten). De bestaande aantallen in `test_collectie`, `test_effects`, `test_prijsstructuur` en `test_kerst` zijn met één ontwerp verhoogd (57 ontwerpen, 31 in groep B, 15 Luxe, Kerstmagie vooraan in de kerstcollectie).
- **Browser** (eigen gedragsscript, 18 controles, alle geslaagd; `e2e/effecten.cjs` 8 van 8; `e2e/toegankelijkheid.cjs` 6 pagina's, 0 bevindingen): zonder tik speelt de film niet, een tik in het midden start hem, Overslaan, het einde, minder beweging, de knop Beweging, een geblokkeerde film, toetsenbord en zonder JavaScript.
- **Schermafbeeldingen** voor de beoordeling: opening, filmeinde en kaart, op 1366 × 768 en 390 × 844, de voorbeeldkaart `Familie Van Dijk` (Kerst). Geen console- of CSP-meldingen en geen horizontale scrollbalk.
- **Niet gedaan**: de mp4 is niet in een browser afgespeeld (Chromium speelt hier de webm-reserve); geen iPhone of Android; geen Lighthouse; `e2e/controle2.cjs` niet gedraaid.

## Kerstmagie: helderder openingsscherm (16 oktober 2026, lokaal, niet gepusht)

- **Helderheid gemeten** (gemiddelde, Rec. 709): bronfilm 47%; mp4 gelijk; film zelf tijdens afspelen 49%; openingsscherm vóór de aanpassing 25% (mobiel) en 22% (desktop); na de aanpassing 49% en 49%.
- **Contrast op de echte pixels** (`e2e/kerstmagie-contrast.cjs`, 360×640, 390×844, 768×1024 en 1366×768): kopregel, naam en aanwijzing halen in het slechtste pixel 5,2 tot 7,4:1 (eis 4,5:1). De knop staat op elk formaat precies in het midden van het scherm (gemeten).
- **Tests**: 1103 tests, 2 mislukt; dat zijn dezelfde 2 (`test_voorwaarden_nieuw`) die ook op de ongewijzigde basis falen. Nieuw: geen sluier, geen filter op film of eerste beeld, achtergrond op volle breedte, tekst in één plaquette met de knop in het midden, lichte sluier op het monogram.
- **Browser**: gedragsscript 18 van 18; `e2e/effecten.cjs` 8 van 8; `e2e/toegankelijkheid.cjs` 6 pagina's, 0 bevindingen.
- **Met het oog**: opening en monogram op 1366×768 en 390×844. Niet bekeken: een echte telefoon of Safari (matglas via `backdrop-filter`).

## Kerstmagie: rijkere kaart, sneeuw en datum onder ijs (16 oktober 2026, lokaal, niet gepusht)

Chromium (Playwright 1.56), testmodus, mobiel 390 × 844 en desktop 1366 × 768.

- **Tests**: 1107, 2 mislukt (dezelfde 2 van `test_voorwaarden_nieuw` als op de ongewijzigde basis). Nieuw in `tests/test_kerstmagie.py`: scriptvolgorde (`vooraf.js` vóór `effects.js`, geen inline script), de datum in de pagina en de ijslaag pas via script, alle beelden uit de film en alle bestaande onderdelen aanwezig, de uitwegen in `snow.js`, `kras.js` en de lagen in `style.css`, en de gewichten van de mediabestanden.
- **`e2e/kerstmagie-kaart.cjs`** (alle geslaagd): sneeuw loopt na het openen en op 25, 50, 75 en 100% van de pagina; ligt boven de beelden en onder de tekst (het midden van de naam is het tekstelement, niet het canvas); knop Beweging zet stil (beeld blijft) en weer aan; minder beweging: geen sneeuw en geen ijslaag; zonder JavaScript en bij mislukt tekenen: datum zichtbaar; krassen (een veeg wist dat stuk, de rest blijft), smelten, onthouden per sessie, de knop **Onthul de datum** met Tab en Enter, en knop Beweging op stil; sneeuw op het openingsscherm onder de knop en daarna op de kaart; tekst op het ijs minstens 9,9:1 op echte pixels; belasting op een vier keer vertraagde processor 60 beelden per seconde, met en zonder sneeuw gelijk (op een server zonder grafische kaart).
- **Leesbaarheid op echte pixels** (zonder tekstschaduw en zonder sneeuw): kopregel, naam, wens, datum, tijd, brief, aftelling, programma, locatie, adres, dresscode en afsluiting halen op beide formaten de eis (4,5:1; 3:1 voor grote cijfers); de wens op desktop 6,3:1 als laagste.
- **Bestaande controles opnieuw**: `e2e/effecten.cjs` 8 van 8 (en 16 van 16 voor Kerstmarkt en Winterlicht, om te zien dat de aanpassing van het script daar niets verandert), `e2e/toegankelijkheid.cjs` 6 pagina's 0 bevindingen, het gedragsscript van de opening 18 van 18, `e2e/kerstmagie-contrast.cjs` (openingsscherm) in orde.
- **Niet gedaan**: een echte telefoon of Safari (matglas via `backdrop-filter`, aanraken en vegen op iOS), Lighthouse, `e2e/controle2.cjs`. Of het luxe genoeg voelt is aan de eigenaar.

### Kerstmagie verborgen (groep C), 16 oktober 2026

Kerstmagie is van groep B naar groep C verplaatst (`catalog/collectie.py`), zodat het ontwerp bij de eerste synchronisatie niet zichtbaar of bestelbaar wordt. Het ontwerp, de prijsindeling (Luxe) en alle bestanden zijn ongewijzigd.

- **Tests**: 1112 tests, 1110 geslaagd. De 2 mislukte zijn dezelfde als eerder (`test_voorwaarden_nieuw`, invulvelden voor het contactadres) en falen ook op de ongewijzigde basis. Aangepast: de aantallen in `test_collectie` (17 / 30 / 10 in A / B / C), de kerstlijst in `test_kerst` (Kerstmagie staat er niet meer in) en `test_kerstmagie`. Nieuw (`KerstmagieVerborgenTests`): groep C en na synchroniseren niet actief (ook na twee keer inlezen), geen ontwerppagina, voorbeeld, agenda-bestand of zoekresultaat (404), niet in `/ontwerpen/` bij Kerst of andere gelegenheden, niet te kiezen en niet te starten in de bestelroute (de bestaande kerstkaarten wel), prijs en de vier andere kerstfilmontwerpen onveranderd. De tests die de kaart zelf bekijken zetten hem alleen in de testdatabase aan.
- **Niet opnieuw uitgevoerd**: de e2e-controles (`e2e/kerstmagie-*.cjs`, `e2e/effecten.cjs`) en de beeldcontroles. De kaart zelf is niet veranderd; voor die scripts moet het ontwerp in de lokale database eerst worden aangezet.

## Rozenboog op de stagingbasis (16 oktober 2026)

Alleen lokaal uitgevoerd, op branch `claude/rozenboog-staging` (commit 83d6988 overgenomen op 715e9c7). Daarna overgenomen op de stand met Kerstmagie (686fc93), zie hieronder:

- `manage.py test tests`: 1106 tests. Drie tests (`test_privacyverklaring.LiveGuardTests`, twee in `test_voorwaarden_nieuw.VersiesTests`) falen op deze machine ook op de ongewijzigde stagingcommit 715e9c7 (onbevestigde bedrijfsgegevens uit de omgeving); dat staat los van Rozenboog.
- Browser (Chromium, 390 en 1366 px): sluier, film, kop, alle onderdelen en einde doorlopen met een tijdelijke, aangezette Rozenboog in een kladdatabase: geen consolefouten.
- Niet gedaan: Safari/iPhone, Android, Firefox, schermlezers, Lighthouse, de e2e-scripts op alle ontwerpen.

## Voorbeeld van verborgen ontwerpen voor beheerders (16 oktober 2026)

Lokaal uitgevoerd op `claude/rozenboog-op-kerstmagie`:

- `manage.py test tests`: 1139 tests; dezelfde 3 als eerder (bedrijfsgegevens uit de omgeving, falen ook op de ongewijzigde staging) mislukken. Nieuw: `tests/test_verborgen_voorbeeld.py` (7 tests): anoniem, klant en gebruiker zonder `is_staff` krijgen een 404 op voorbeeld en agendabestand van Rozenboog en Kerstmagie; beheerders krijgen 200 met `Cache-Control: private, no-store`; beide blijven buiten de collectie, de ontwerppagina en de bestelroute (ook voor beheerders) en blijven niet actief; een actief ontwerp werkt voor iedereen als voorheen, zonder `no-store`.
- Niet in een browser bekeken: het voorbeeld als ingelogde beheerder op staging.

## Kortingscodes (17 oktober 2026, lokaal, niet gepusht)

Uitgevoerd: `python manage.py test tests`, 1245 tests, geslaagd (waarvan 106 nieuw in `tests/test_kortingscodes.py`, elk onderdeel voor de oude pakketten én voor Basis/Luxe/Special). Gecontroleerd: berekening en afronding, ondergrens € 1,00 en geen 100%, alle foutmeldingen, bereik per gelegenheid/indeling/ontwerp, reserveren/definitief/vrijgeven bij betaald, mislukt, verlopen, afgebroken en vervangen, de laatste plek, per klant (ook plusje en Gmail-puntjes), terugbetaling en handmatig vrijgeven met reden, bedrag in Mollie-verzoek gelijk aan bestelling, mail en bon, historische bestelling ongewijzigd, schakelaar uit = geen veld/geen Beheeronderdeel/code geweigerd. Daarnaast: `makemigrations --check` zonder wijzigingen, en de migratie `orders.0004` uitgevoerd op een SQLite-database met een bestaande bestelling (die bleef ongewijzigd).

Visueel (lokale testserver in testmodus, Chromium, `VIERLIEF_KORTINGSCODES=1`, `VIERLIEF_PRICING_V2=1`): de bestelstap dicht, met een foutmelding en met een toegepaste code bekeken op 390 en 1366 px (screenshots bekeken), en op 360 en 768 px alleen gemeten op horizontaal scrollen (geen). Daarna is een kleine stijlaanpassing gedaan (Verwijderen op dezelfde regel) die niet opnieuw is bekeken.

**Niet uitgevoerd:** PostgreSQL (alleen SQLite, dus geen echte gelijktijdigheid), een echte of testbetaling bij Mollie, de toegankelijkheidscontrole (`e2e/toegankelijkheid.cjs`) en een controle met schermlezer of op echte apparaten.

## Automatische aanbiedingen en centraal kortingsbeheer (17 oktober 2026, lokaal, niet gepusht)

Uitgevoerd: `python manage.py test tests`, 1296 tests, geslaagd (waarvan 51 nieuw in `tests/test_aanbiedingen.py`); `manage.py check` en `makemigrations --check` zonder meldingen. Gecontroleerd: standaard uit (geen aanbieding in offerte, kaart, pagina, Beheer; codes aan en aanbiedingen uit blijft zonder aanbieding), bereik (collectie, ontwerpen, gelegenheid, indeling, gepland/verlopen/uitgezet), voordeligste wint, einddatum verplicht (database), ondergrens € 1,00, bestelling = offerte = betaling = Mollie-verzoek = regels = mail = bon, getoonde actieprijs = offerte voor elk ontwerp, elke gelegenheid en beide kaartsoorten, vaste prijzen ongewijzigd, code en aanbieding (code wint, aanbieding wint, gelijk = aanbieding, geen verbruikte code), bedragcontrole bij een verlopen of net gestarte aanbieding, prijshistorie (sync, referentie alleen met dekkende historie, laagste prijs in de voorgaande periode, eerdere aanbieding verlaagt de referentie, achterlopende historie, uitzetten), Beheer (rechten, validatie, vergrendeling na start, nu stoppen, bestellingen ongewijzigd).

Visueel (lokale testserver in testmodus, Chromium, beide schakelaars aan, een fictieve aanbieding van 20% en een kunstmatig verouderde prijshistorie): collectie, ontwerppagina, bestelstap en Beheer op 360, 390, 768 en 1366 px gemeten zonder horizontaal scrollen of consolefouten; ontwerppagina, bestelstap en Beheer-aanbieding op 1366 en de collectie op 390 bekeken. Niet goed bekeken: de collectiekaarten op ware grootte (de kaartafbeeldingen laadden niet in de schermafbeelding van de hele pagina), 360 en 768 alleen gemeten.

**Niet uitgevoerd:** PostgreSQL, een testbetaling bij Mollie, `e2e/toegankelijkheid.cjs`, controle met schermlezer, en juridische verificatie van de referentieregels voor digitale kaarten (voorwaarde voor productie, zie `docs/AANBIEDINGEN.md`).

### Afronding van de aanbiedingen en kortingen (17 oktober 2026, lokaal, niet gepusht)

Uitgevoerd op de ontwikkelbranch, in testmodus, met alle schakelaars alleen in het eigen testproces aan:

- **Volledige suite op SQLite:** 1296 tests geslaagd. **Volledige suite op PostgreSQL 16.15** (geïsoleerd, lokaal, `initdb` in een tijdelijke map, geen productiedatabase): 1301 tests geslaagd (de 5 extra zijn de gelijktijdigheidstests).
- **PostgreSQL-gelijktijdigheid** (`tests/test_kortingen_postgres.py`, slaat over buiten PostgreSQL): 8 klanten tegelijk op de laatste plek van een code (precies 1 krijgt de korting), maximum 3 bij 8 klanten, één klant met twee kaarten en maximum 1 per klant, code naast een voordeligere aanbieding (de code wordt niet verbruikt), en drie tegelijke bevestigingen van dezelfde betaling (telt 1 keer). Controle dat de test echt iets bewaakt: zonder de rijvergrendeling in `kortingen.services.prepare` faalden de eerste twee (8 van 8 kregen de korting); daarna teruggezet.
- **Toegankelijkheid van de kortingsonderdelen** (`e2e/toegankelijkheid_kortingen.cjs`, axe-core WCAG 2.0/2.1 A en AA plus gerichte controles, 390 en 1366 px, 23 pagina's: collectie, ontwerppagina met beide kaartsoorten, kaartkeuze, bestelstap normaal, met foutmelding en met toegepaste code, toetsenbordbediening, vijf Beheerpagina's): geen bevindingen. Gerichte controles: prijskaartje met tekst en decoratief icoon, verborgen tekst "Was" en "Nu" bij prijzen, foutmelding met `role=alert` en `aria-invalid`/`aria-describedby`, melding over de voordeligste korting als `role=status`, uitklapregel met Enter te openen en daarna met Tab te bereiken, zichtbare focusring, en dat alle afbeeldingen op de pagina echt geladen zijn.
- **Visueel met geladen afbeeldingen** (390 en 1366 px): collectie, kaartkeuze in de Studio, ontwerppagina, bestelstap en Beheer bekeken. Twee fouten gevonden en hersteld: in de Studio-kaartkeuze brak de prijs midden in het bedrag af, en in de gecentreerde Specials-sectie stond het prijskaartje links terwijl de rest gecentreerd was. Beide opnieuw bekeken op 390 en 1366 px.
- **Mollie:** `e2e/mollie_kortingen.py` (drie scenario's: code, aanbieding, beide) is geschreven en getest tegen een lokale **nepserver** (`MOLLIE_API_BASE`), niet tegen Mollie. **De Mollie-integratie is dus nog niet met een echte Mollie-testsleutel getest.**
- **Vergelijking met de productiecode `bbaa615`:** de branch bevat de commit niet; het enige verschil met de basis is dat `bbaa615` twee documentatiebestanden aanpast (rechten op de films). Een proefmerge van `bbaa615` in de branch verliep zonder conflict (afgebroken, niet vastgelegd). Tussen `bbaa615` en de branch verschilt geen bestand in `designs/`, `catalog/prijzen.py` of `orders/providers.py`; Kerstmagie en Rozenboog staan er ongewijzigd in.
- **Bestaande toegankelijkheidstest `e2e/toegankelijkheid.cjs`** (alle uitnodigingsontwerpen in alle kleuren, dicht en geopend, axe-core en contrast): 332 pagina's in twee runs (de eerste liep vast op een time-out bij Kerstmarkt toen de server tegelijk een testsuite bediende; daarna zijn de resterende ontwerpen opnieuw gedraaid), 53 met bevindingen. Alle bevindingen zitten in bestaande ontwerpen (vooral `label-content-name-mismatch` op zegel- en boekknoppen; contrast bij onder meer Kerstkaart, Kerststad, Middernacht, Aan tafel en Voor altijd). De branch wijzigt niets in `designs/` of `invitations/`, dus dit zijn bestaande punten en geen regressies; ze zijn niet hersteld (buiten de opdracht) en staan hier als open punt.

### Terugdraaiveiligheid van de kortingsmigraties (17 oktober 2026, lokaal)

Uitgevoerd op een geïsoleerde PostgreSQL 16 (eigen cluster in een tijdelijke map, geen productie- of staginggegevens), in testmodus, kortingsvlaggen uit:

- **Bevinding:** `orders_order.discount_cents`, `discount_code_text` en `discount_offer_text` waren verplicht zonder standaardwaarde in de database (Django haalt de tijdelijke standaardwaarde na het toevoegen weg). Na alleen het terugzetten van de code naar `bbaa615` mislukte het aanmaken van een nieuwe bestelling met `null value in column "discount_cents" ... violates not-null constraint`. Gecontroleerd en bevestigd in de controle zonder de correctie. De andere nieuwe kolommen van `orders_order` (`subtotal_cents`, `discount_code_id`, `discount_offer_id`) mogen leeg zijn; de nieuwe tabellen van `kortingen` worden door oudere code niet beschreven; de wijziging van `orderline.total_cents` en `unit_price_cents` naar `IntegerField` versoepelt alleen.
- **Correctie:** migratie `orders/0006_standaardwaarden_kortingskolommen` (`db_default` 0 en lege tekst), geen nieuwe functionaliteit.
- **Rollbacktest** (`bbaa615` uit een aparte werkmap, nieuwe code uit de integratiebranch, dezelfde database): oude code migreert en maakt bestelling A; nieuwe code voert de kortingsmigraties uit en maakt bestelling B; alleen de code gaat terug naar `bbaa615`: bestelling C wordt aangemaakt; A, B en C staan er allemaal met korting 0. Zonder `0006` (controle) faalt stap C. Migratie 0006 is terug- en weer vooruit te draaien en `makemigrations --check` meldt niets.
- **Tests:** twee nieuwe PostgreSQL-tests (`TerugdraaiVeilig`: de kolommen hebben een databasestandaard; een INSERT zonder kortingsvelden slaagt); zonder de correctie falen beide. Volledige suite: 1303 tests geslaagd op SQLite en op PostgreSQL 16.

### Btw-controle van persoonlijke kortingscodes (17 oktober 2026)

De eigenaar bevestigde dat de onderneming niet meedoet aan de KOR; 21% btw blijft, de verkoopprijzen zijn niet gewijzigd. Uitgevoerd:

- **Lokaal:** `tests.test_kortingscodes` (106 tests) geslaagd, waaronder de btw-afronding (`vat_part_cents`), `test_bedrag_regels_betaling_en_mollie_zijn_exact_gelijk` (regels, ordertotaal en betaalbedrag gelijk; Mollie wordt in die test met een nepserver nagebootst, niet met Mollie zelf) en `test_prijzen_blijven_gelijk_alleen_het_bestelbedrag_verandert`.
- **Op staging, alleen lezen in de database, na twee bestellingen met testbetaling (gesimuleerd, geen Mollie):** VL26-00004 (code BIGCODE30): voorbeeld € 59,95, korting € 17,99, totaal € 41,96, regels € 41,96, betaling € 41,96. VL26-00005 (aanbieding): € 59,95, korting € 11,99, totaal, regels en betaling € 47,96. De drie bestellingen van vóór de kortingen (VL26-00001 tot en met 00003) zijn ongewijzigd: € 39,00, korting 0, `subtotal_cents` leeg, betaling € 39,00. Het btw-deel (€ 7,28 bij € 41,96) is berekend met de formule, niet in Beheer bekeken omdat het beheeraccount toen al was ingetrokken.
- **Niet gedaan:** een echte Mollie-testbetaling (nog geen testsleutel op staging), en een beoordeling door de boekhouder. De open fiscale vragen staan in `docs/KORTINGSCODES.md` onder "Btw".

## Prijzenbeheer: toegankelijkheid en PostgreSQL (17 oktober 2026)

- **Toegankelijkheid van de prijzenpagina's in Beheer** (`e2e/toegankelijkheid_prijzen.cjs`, axe-core 4 met WCAG 2.0/2.1 A en AA, lokale testserver met testgegevens): overzicht, wijzigen, bevestigen, foutmelding, logboek en terugdraaien, op 360, 390, 768, 1366 en 200% zoom (683 px): **30 metingen, 0 overtredingen**, geen horizontale scroll, elk invulveld met label. Toetsenbord (Tab door alle bedienbare elementen op 390 en 1366): alles bereikbaar, elk element een naam en zichtbare focus; het bedragveld toont de focus op zijn omlijsting. Uitvoer: `/mnt/project-files/prijzenbeheer/toegankelijkheid-uitvoer.json`.
- **Gevonden en opgelost**: (1) de twee "stille" rijen (Geboortekaart, Save the date) stonden op 72% dekking, waardoor de tekst onder de 4,5:1 contrast kwam (axe: `color-contrast`, ernstig, op 360 px); de dekking is weggehaald. (2) Na een ongeldige invoer bleef de focus op de pagina zelf; de foutmelding krijgt nu de focus (`tabindex="-1" autofocus`); een test bewaakt dit.
- Niet gedaan: een schermlezer (NVDA/VoiceOver) is niet gebruikt; de labels en `aria-describedby` zijn met axe en de DOM gecontroleerd.
- **Gelijktijdige prijswijzigingen op PostgreSQL 16** (wegwerpdatabase, `tests/test_prijsbeheer_postgres.py`): 3 tests geslaagd; vijf gelijktijdige wijzigingen met dezelfde stempel geven precies één geslaagde en vier meldingen "intussen gewijzigd".

## Prijzenbeheer, fase A (17 oktober 2026, lokaal, niet gepusht)

Echt uitgevoerd op een lokale testomgeving (SQLite, testmodus, testbetaling en nagebootste Mollie-antwoorden; geen Mollie-live, geen staging, geen productie):
- `manage.py test tests`: 1364 tests, allemaal geslaagd (8 overgeslagen, zoals eerder), waarvan 60 nieuw in `tests/test_prijsbeheer.py`: startstand = 27 code-bedragen, vlag uit = code, doorwerken tot en met bon en bevestigingsmail, Mollie-bedrag, ontbrekend of ongeldig bedrag blokkeert bestellen, bestaande bestellingen en openstaande betalingen, `PriceChanged`, validatie, bevestiging, logboek, terugdraaien, rechten, bescherming van eigenaarsaccounts, btw-tarief op de bestelling, kortingscode over de nieuwe prijs.
- `manage.py controleer_prijsbron` meldt elke afwijking tussen database en code op een omgeving met een bewust afwijkende prijs (gezien op de lokale testdatabase); op de startstand slaagt het (test).
- Beheerschermen bekeken met Chromium (Playwright) op 360, 390, 768 en 1366 pixels als Eigenaar en als gewone beheerder: geen horizontale scroll, geen paginafouten behalve de bedoelde 400 op de foutmelding-pagina; de gewone beheerder krijgt 403 op de wijzigpagina.
- `e2e/toegankelijkheid.cjs` en `e2e/controle2.cjs` zijn voor deze schermen **niet** gedraaid.
- Niet gedaan: Mollie-testbetaling op staging, controle op productie, rechten van het productieaccount (alleen het commando `controleer_rechten` is klaar).

## Vijf filmkaarten (18 oktober 2026, lokaal, niet op staging)

Zijden gordijn, Bloesemmeer, Bloesemwaaier, Kerstsprookje en Gouden poort (`docs/INTROKAARTEN.md`). Echt uitgevoerd op een lokale testomgeving (SQLite, testmodus, kaarten via het beheerdersvoorbeeld):

- **Correctie vooraf:** in een eerdere versie van deze sectie stond dat het openen (tik, film, eindbeeld) was gecontroleerd. Dat klopte niet voor de film: de testbrowser (Chromium van Playwright) kan geen H.264 afspelen, en er was nog geen WebM-bron, dus de film werd stil overgeslagen en alleen het eindbeeld werd getoond. Dat is opgelost met een WebM als extra bron (`opening.webm`, MP4 blijft hoofdformaat).
- **Afspelen** (`scratchpad`-script, Chromium, alle vijf kaarten, elk 6 scenario's = 30 doorlopen, geen paginafouten, geen horizontale scroll): mobiel 390 × 844 en desktop 1366 × 768: de film start binnen 0,3 s na de tik, de videotijd bij het einde is 10 s (`ended`), de kaart gaat ca. 1 s later naar de uitnodiging (11,0 tot 11,4 s na de tik) en de bedekking is dan weg. Als `play()` wordt geweigerd (automatisch afspelen niet beschikbaar) en als de videobestanden niet laden, opent de kaart na ca. 1 s direct op het eindbeeld met de uitnodiging bruikbaar. Bij 'minder beweging' opent de kaart direct. Op een traag netwerk (1,6 Mbps, 150 ms vertraging) speelt de film zonder haperen door naar het einde. Gemeten bron in al deze runs: de WebM.
- **MP4 (H.264):** niet in een browser afgespeeld (geen H.264 in de testbrowser). Wel met `ffprobe` en `ffmpeg` gecontroleerd voor alle vijf: geldig High-profiel level 3.1, 300 beelden, volledig decodeerbaar zonder fouten, `moov` vooraan (`+faststart`), geen geluidsspoor, 1,4 tot 1,9 MB; het laatste beeld komt overeen met `end.webp`. Afspelen van de MP4 op echte telefoons (iOS Safari, Android Chrome) is niet getest.
- **Bestandsgrootte:** MP4 1,4 tot 1,9 MB; WebM 2,2 tot 2,9 MB (grens in de test 3 MiB). Het metadata-label van de bronfilms zat in eerste instantie ook in de WebM; dat is eruit gehaald (de MP4's hadden het al niet).
- **axe** (`e2e/toegankelijkheid.cjs`, dicht en geopend, per kaart): 0 bevindingen voor alle vijf en voor Rozenboog (vergelijking). Eerder vond axe onvoldoende contrast op de knop *Openen met muziek* in drie kaarten; dat is gecorrigeerd (tekstkleur `--fk-ink`).
- **Tests:** `manage.py test tests`: 1380 tests, 2 falen en 11 overgeslagen met de lokale `.env`; zonder `VIERLIEF_CONTACT_EMAIL` slagen die twee ook (`tests.test_voorwaarden_nieuw`: 27 tests OK). De twee tests in `test_voorwaarden_nieuw` (invulvelden in privacy en voorwaarden) die in een lokale omgeving falen, doen dat door de lokale `.env` (`VIERLIEF_CONTACT_EMAIL` is daar ingevuld), niet door deze kaarten: aangetoond op de stand van vóór deze wijziging (zelfde twee falen) en slagend zonder die variabele. Er is niets aan privacy of voorwaarden gewijzigd.
- **Niet geraakt:** bestaande ontwerpen, prijzen, bestellingen en betaalroute: geen bestaand ontwerpbestand, geen prijsbedrag en niets in `orders/` of de betaalkoppeling gewijzigd (alleen toevoegingen en aantallen in `catalog/collectie.py`, `catalog/prijzen.py`, `invitations/demo.py`). `tests/test_introkaarten.py` toont dat de kaarten niet in de collectie, de sitemap, de zoekresultaten en de ontwerppagina staan, dat een bestelling op een van deze kaarten niets aanmaakt (ook niet voor beheerders) en dat het voorbeeld alleen voor beheerders werkt (404 voor bezoekers en klanten, `private, no-store`).
- Gezien (schermafbeeldingen, 390 px): per kaart voor het openen, tijdens de film, direct na de film en de uitnodigingsinformatie.
- Niet gedaan: niet getest op echte telefoons, Safari of Firefox; niet op staging gezet of bekeken. Rechten: niet aantoonbaar (zie `docs/INTROKAARTEN.md`).

## Premium laag op Bloesemmeer (18 oktober 2026, lokaal, niet op staging)

Voorbeeld van licht op het water, nevel op twee dieptes, bloesemblaadjes over de kop en scrollreactie (`docs/INTROKAARTEN.md`). Echt uitgevoerd (Chromium, mobiel 390 × 844, kaart via het beheerdersvoorbeeld):
- `manage.py test tests`: 1384 tests; alleen de twee bekende falers door de lokale `.env` (`VIERLIEF_CONTACT_EMAIL`, zie hierboven). Nieuw: 3 tests voor de laag (alleen Bloesemmeer, decoratief en achter de tekst, speelstand voor alle lagen) en 1 voor `scrollwind` (alleen Bloesemmeer kiest het).
- axe (`e2e/toegankelijkheid.cjs`, dicht en open): 0 bevindingen.
- Beweging: de laag verschijnt na het openen en is weg bij 'minder beweging' en na stilzetten met de knop *Beweging*; de speelstand van alle lagen volgt `--fx-play` (gemeten: alle vier `paused`). Geen paginafouten.
- Vloeiendheid: 300 beelden tijdens scrollen met de processor 4 keer vertraagd (Playwright, geen echte telefoon): gemiddeld 16,7 ms per beeld, geen beeld boven 17 ms, met en zonder de laag vergelijkbaar. Dit zegt niets over een echte telefoon met batterij; dat is niet gemeten.
- Gezien: schermafbeeldingen voor en na, en een opname van 43 seconden (openen, kop, scrollen, terug).
- Niet gedaan: echte telefoons, Safari (scrollgestuurde diepte werkt alleen in browsers die dat kennen), Firefox; de andere vier kaarten hebben de laag niet.

## Premium laag op de andere vier kaarten (18 oktober 2026, lokaal, niet op staging)

Zijden gordijn, Bloesemwaaier, Kerstsprookje en Gouden poort (`docs/INTROKAARTEN.md`, `tools/introkaarten/premium_laag.py`). Echt uitgevoerd (Chromium, kaarten via het beheerdersvoorbeeld):
- **Vier schermbreedtes** (360 × 740, 390 × 844, 768 × 1024, 1366 × 768), na het openen: 16 doorlopen, geen horizontale scroll, geen paginafouten, laag aanwezig. Gezien: 390 px en 1366 px voor alle vier, en de hele uitnodiging op 390 px.
- **axe** (`e2e/toegankelijkheid.cjs`, dicht en open): 0 bevindingen voor alle vier.
- **Minder beweging** (emulatie): laag onzichtbaar, geen deeltjes getekend, alle vier. **Knop *Beweging*** (pauze): laag weg en deeltjes gewist, bij hervatten terug, alle vier.
- **Vloeiendheid** (processor 4 keer vertraagd, 300 beelden tijdens scrollen, Playwright): gemiddeld 16,9 tot 18,1 ms per beeld. Kerstsprookje haalde in twee van drie metingen een p95 van 33 ms (1 beeld van 300 boven 40 ms) tegen 16,8 ms zonder effecten; daarom is de dichtheid daar teruggebracht naar 0,6. Niet gemeten op een echte telefoon, en niet op batterijverbruik.
- **Tests:** `manage.py test tests`: 1386 tests, alleen de twee bekende falers door de lokale `.env`; nieuw: vijf tests voor de laag (alle vijf, decoratief en achter de tekst, eigen identiteit per kaart, generator herhaalbaar, verborgen).
- **Niet gedaan:** Safari en Firefox zijn in deze omgeving niet te testen (alleen Chromium is geïnstalleerd). Uit de code: de scrollgestuurde diepte is een `@supports`-verbetering (Chromium, nieuwe Safari); `translate`, `aspect-ratio`, `cqw` en maskers worden door Safari 16+ en Firefox 110+ ondersteund, maar dat is niet bekeken. Echte telefoons niet getest. Films niet gewijzigd.

## Knoppen en plaatsregel op mobiel (18 oktober 2026, lokaal, niet op staging)

Aanleiding: op het eerste scherm stonden de pauzeknop (links) en de muziekknop (rechts) over de regel met de plaats ("De Oranjerie (voorbeeldlocatie)"), omdat die regel net zo breed was als de ruimte tussen de knoppen. Oplossing: een kleine regel aan het eind van `style.css` van de zes kaarten (blok `knop-ruimte`, ook in `tools/introkaarten/sjabloon/style.css`): `@media (max-width: 480px)` geeft de regel met tijd en plaats `padding-inline: 4,25rem`, zodat een lange plaats over twee regels loopt tussen de knoppen. Niets anders is aangepast: films, effecten, kleuren en prijzen zijn gelijk. Rozenboog (`designs/rozenboog/v1`) is op verzoek van de eigenaar meegenomen; de kaart is verborgen en heeft geen bestaande uitnodigingen. Echt uitgevoerd (Chromium, beheerdersvoorbeeld, kaart geopend):
- **Overlap gemeten** (tekstregels tegen de knoppen, eerste scherm): voor de wijziging op 360 × 740 en 390 × 844 een overlap bij Zijden gordijn, Bloesemmeer, Bloesemwaaier, Gouden poort en Rozenboog (Kerstsprookje niet, die plaats is korter); na de wijziging 0 overlappen bij alle zes, ook op 360 × 640.
- **Leesbaarheid op 360 en 390 px**: geen tekst buiten beeld of afgekapt (de enige treffers zijn de voor schermlezers verborgen kleurnamen), geen horizontale scroll. Wel klein: de kopregel en de weekdag en maand van de datum zijn met 11,5 tot 11,9 px op 360 px net onder 12 px (hoofdletters met letterafstand, bewust zo ontworpen; niet aangepast).
- **Verticale tussenruimtes**: gemeten na doorscrollen (390 × 844): tussen de blokken 26 tot 38 px, geen onbedoelde gaten. De grote lege vlakken in eerdere overzichten ontstaan doordat de onderdelen pas verschijnen als ze in beeld scrollen (`data-reveal`); met 'minder beweging' en zonder JavaScript zijn ze meteen zichtbaar (gemeten: 0 verborgen van 15). Er is daarom niets aan de ruimte veranderd.
- **Aanmelden**: staat bij alle zes op `#aanmelden`, ongeveer 70 procent van de pagina; er is geen aparte knop of link bovenin. Dat is zo gelaten (geen nieuwe functie); mogelijk punt voor later.
- **axe** (`e2e/toegankelijkheid.cjs`, dicht en open): 0 bevindingen voor alle zes.
- **Tests:** `manage.py test tests`: 1386 tests, alleen de twee bekende falers door de lokale `.env`; nieuw: twee tests in `tests/test_introkaarten.py` (`KnopRuimteTests`).
- **Niet gedaan:** staging niet gecontroleerd (de cloudomgeving bereikt die niet), geen Safari of Firefox, geen echte telefoons.

## Link Aanmelden in de kop (18 oktober 2026, lokaal, niet op staging)

Op verzoek van de eigenaar: bij Zijden gordijn, Bloesemmeer, Bloesemwaaier, Kerstsprookje, Gouden poort en Rozenboog staat bovenin de kop een kleine, ronde link 'Aanmelden' naar `#aanmelden` (de bestaande sectie). Markup: een `<a class="fk-aanmeld fx-intro">` (bij Rozenboog `rb-aanmeld`) als laatste kind van `<header>`, alleen als `v.show.rsvp and not v.rsvp.closed_reason` (dus niet als aanmelden uit staat, de deadline voorbij is, de dag geweest is of het maximum bereikt is). Stijl: blok `aanmeld-link` onderaan `style.css` (eigen lettertype, kleuren, gouden lijn en sluier van de kaart; geen nieuwe tokens); ook in `tools/introkaarten/sjabloon`. Films, effecten en de aanmeldfunctie zijn niet aangeraakt. Echt uitgevoerd (Chromium, beheerdersvoorbeeld):
- **Pas na de film:** de link staat in de uitnodiging, die tijdens de film `inert` is; gemeten dat de link dan onzichtbaar en niet focusbaar is, en na het openen zichtbaar (alle zes).
- **Plaatsing** op 360 × 740, 390 × 844, 768 × 1024 en 1366 × 768, alle zes: 24 metingen, de link staat steeds binnen beeld en raakt geen tekst van de kop (marge 4 px). Eerst bij Gouden poort te dicht op de kopregel: daarom een slankere link (28 px hoog, het aanraakvlak is met een onzichtbare rand 44 px).
- **Toetsenbord:** eerste Tab-stop na het openen, zichtbare focusrand (2 px), Enter brengt naar de aanmeldsectie. **Minder beweging** (emulatie): link meteen zichtbaar, geen animatie, werkt hetzelfde.
- **Niet beschikbaar:** drie tests in `tests/test_introkaarten.py` (`AanmeldLinkTests`): aanwezig bij open aanmelden in de kop en wijzend naar `#aanmelden`; afwezig bij voorbije deadline en bij aanmelden uitgezet (op echte gepubliceerde uitnodigingen met het ontwerp); stijl en sjabloon aanwezig.
- **axe** (`e2e/toegankelijkheid.cjs`, dicht en open): 0 bevindingen voor alle zes. **Tests:** `manage.py test tests`: 1391 tests, alleen de twee bekende falers door de lokale `.env`. Een bestaande laagtest is aangepast om alleen de premium laag te beoordelen (niet de latere blokken).
- **Niet gedaan:** staging, Safari, Firefox en echte telefoons.

## Pakketlabel op de ontwerpkaarten (19 oktober 2026)

Het label Special stond bij sommige kaarten naast de naam en bij andere erboven, afhankelijk van de lengte van de naam. Nu staat het in de gedeelde kaartstijl (`.design-card__special` in `static/css/vierlief.css`) altijd op een eigen regel boven de naam, ook op desktop; lange namen breken af onder het label. Er bestaat in deze code alleen het label Special (geen Luxe of Basis op de kaart).

- **Uitgevoerd:** echte Chromium-screenshots voor en na op 360, 390 en 1366 px (pagina Ontwerpen, 11 specials); gemeten dat het label op alle kaarten boven de naam staat (voor: 6 van 11 naast de naam op 360 px, 9 van 11 op 390 px, alle 11 op 1366 px). Test in `tests/test_collectie.py`.
- **Niet gedaan:** Safari, Firefox en echte telefoons.

## Homepage-carrousel (21 oktober 2026, lokaal, branch `claude/homepage-carrousel`)
Echt uitgevoerd:
- `manage.py test tests`: 1421 tests; alleen de 2 bekende fouten in `tests.test_voorwaarden_nieuw` (bedrijfsgegevens uit de omgeving). Nieuw: `tests/test_homepage_carrousel.py` (22 tests): selectie en volgorde, Basis/inactief/verborgen/zonder versie overgeslagen, minder dan vijf geeft de oude hero, vaste teksten, fonkelingen, links naar bestaande ontwerppagina's, alleen-lezen veiligheid van de scripts, migratie, Beheer alleen voor beheerders.
- Migratie op een kopie met 63 ontwerpen en 64 versies: bestaande kolommen en versies identiek, nieuwe kolommen op standaardwaarde.
- Zonder uitgelichte ontwerpen is de homepage-HTML gelijk aan productie op witregels na; `/ontwerpen/`, `/prijzen/`, `/digitale-kerstkaarten/` en een ontwerppagina zijn byte-identiek.
- Chromium (Playwright) op 360, 390, 768 en 1366 breed: alle zes knoppen zichtbaar en klikbaar, geen horizontale paginascroll (ook na vegen), zijkaart selecteert, middelste kaart en knop openen `/ontwerpen/<slug>/`, toetsenbord (pijltjes, Home, End), 'minder beweging', zonder JavaScript.
- Meting op 390 breed met 4x vertraagde processor (Chromium zonder echte GPU): huidige homepage ca. 35 beelden per seconde, nieuwe homepage met stille carrousel ca. 46, met draaiende carrousel ca. 37 tot 40; LCP ca. 0,2 s en CLS 0 voor beide. Dit is geen echt apparaat.
Niet uitgevoerd: echte iPhone/Safari, Android, axe en `e2e/toegankelijkheid.cjs` op de nieuwe homepage.

## Vijfde voordeel onder de heroknoppen (21 oktober 2026, lokaal, branch `claude/homepage-carrousel`)
"Eigen foto's en muziek toevoegen" staat als derde van vijf voordelen (`HERO_CHECKS` in `core/content.py`); stijl, iconen en afstanden zijn ongewijzigd. Echt uitgevoerd:
- `tests/test_eigen_fotos_alle_ontwerpen.py`: voor elk actief ontwerp (eerste gelegenheid van het ontwerp) een foto en een MP3 uploaden via de Studio, kiezen als hoofdfoto, galerijfoto en eigen muziek, en terugzien in de live kaart. Geslaagd voor alle actieve ontwerpen. Bij ontwerpen met een eigen track (zoals Kerststad) kiest de klant "eigen muziek" en bevestigt de rechten; dat is de bestaande stap.
- `tests.test_homepage_carrousel`: vijf voordelen in de juiste volgorde.
- Chromium op 360, 390, 768 en 1366: vijf voordelen, geen item buiten beeld, geen horizontale paginascroll; 3 regels op 360 en 390, 2 op 768, 1 op 1366.

## Homepage-kop links, carrousel rechts (21 oktober 2026, lokaal, branch `claude/homepage-carrousel`)
Echt uitgevoerd:
- `tests.test_homepage_carrousel`: 25 tests, onder meer de zichtbare koptekst, Pinyon Script met eigen bestand en licentie, de teller.
- axe-core 4.10.2 (WCAG 2.0/2.1 A en AA plus best practices) op 360, 390, 768, 1199, 1200, 1366 en 1920 breed: één melding, "region" op de testbalk (niet de carrousel); geen JavaScript-fouten; Pinyon Script geladen; geen horizontale paginascroll.
- Op mobiel staat 26 px tussen "uitnodiging." en de bovenkant van de kaarten (was 11 px); de eerste kaart begint op 366 px.
Niet uitgevoerd: echte iPhone/Safari en Android.

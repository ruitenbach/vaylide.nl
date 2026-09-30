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
```

Het rapport en de schermafbeeldingen komen in de uitvoermap (`rapport.json` of `rapport-<schermformaat>.json`, en per schermformaat een map met afbeeldingen). Gebruik bij de controles een server met `DEBUG` uit (zoals gunicorn); de ontwikkelserver toont bij een 404 een eigen foutpagina.

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

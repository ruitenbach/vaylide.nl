# Uitgevoerde controles

Hier staan alleen controles die echt zijn uitgevoerd, met hoe en met welk resultaat. Wat niet gecontroleerd kon worden, staat onderaan.

## Controle 1: volledige werking

**139 geautomatiseerde tests** (`python manage.py test tests`), laatst gedraaid op de definitieve code met het merk Vaylide en het wachtwoord voor een testversie online (ronde 6), alle geslaagd:

- lokaal op SQLite;
- op PostgreSQL 16 (lokale database) in ronde 5, toen met 132 tests, op de stand vlak vóór de laatste kleine wijziging van die ronde (kaarten zonder dubbel woord, zoals "Confetti · confetti"). Die wijziging en ronde 6 zijn alleen op SQLite getest;
- in de Docker-image (Python 3.11), na een build vanaf nul: in ronde 2 (toen 92 tests). Daarna is de image niet opnieuw gebouwd; er zijn geen afhankelijkheden, instellingen of datamodellen veranderd (de nieuwe ontwerpen en de effecten zijn bestanden, en het extra veld "Aantal jaar" staat in de bestaande inhoud van een uitnodiging).

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

Met de beweging stilgezet (knop **Beweging**) is de rekentijd na het openen ongeveer 1 ms per seconde; met beweging 270 tot 380 ms (gemeten bij Rozentuin, Gala, Neonnacht, Puur moment en Glitter & goud). Op een echte telefoon tekent de grafische kaart mee, dus dit is een ongunstige benadering en geen meting op een echt toestel (zie "Niet gecontroleerd").

### Gevonden en opgelost

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

## Ronde 7: Gouden licht

Alleen wat echt is uitgevoerd, op de ontwikkelserver in testmodus, in Chromium (Playwright), voor het nieuwe ontwerp `gouden-licht`:

- **Tests**: 148 van 148 geslaagd (9 nieuwe in `tests/test_gouden_licht.py`: manifest en effecten, leesbare kleuren in alle vier de kleurvarianten (10 kleurparen, alle minstens 4,5:1), weergave van alle 16 combinaties van gelegenheid en kleur met één inline script (CSP), het zegel als gewone link met vaste naam, de afspraken voor beweging in de stylesheet (alle eindeloze animaties onder `.fx-motion` en met de pauzeknop, een rustige variant voor het openen), geen restanten van het ontwerp waaruit is gekopieerd, en dat het bloemenbestand precies is wat het script maakt). `test_effects` telt nu 34 ontwerpen.
- **Toegankelijkheid** (`e2e/toegankelijkheid.cjs`): axe-core 4 en de contrastcontrole op **8 pagina's** (vier kleuren, dicht en geopend): **0 overtredingen en 0 contrastproblemen**. Een eerste run vond twee dingen die zijn opgelost: de initialen onderaan de pagina waren te licht op het zegel (1,3:1, overgenomen kleur) en de knop kreeg een axe-melding omdat de initialen tekst in de knop waren.
- **Effecten** (`e2e/effecten.cjs`): **24 van 24 controles geslaagd** voor Gouden licht, Avondgoud en Liefde op papier (acht per ontwerp: deeltjes op het openingsscherm, knal, kop na het openen, feestje na aanmelden, geen consolefouten, stilzetten, onthouden, minder beweging). De controle van de knal wachtte een vaste 650 ms en faalde eerst voor Gouden licht, waarvan de knal bewust op 1,2 s valt; de controle leest nu `data-fx-delay`.
- **Toetsenbord en zonder JavaScript**: Tab bereikt het zegel (na de sla-over-link) en daarna de muziekknop; Enter en de spatiebalk openen de uitnodiging, de focus gaat naar de kop en het openingsscherm is weg; zonder JavaScript is het openingsscherm niet zichtbaar en staan kop en aanmelden er gewoon.
- **Met het oog bekeken**: dicht en tijdens het openen op 390 pixels (rust, glans, lichtdoorbraak, overspoeling, kop) in Bordeaux; dicht en geopend op 360 en 1366 pixels in Bordeaux; en tijdens het openen op 390 pixels in Nachtblauw, Smaragd en Aubergine. Op 768 pixels zijn beelden gemaakt maar niet bekeken. Bij 360 × 640 viel de hint onder de envelop uit beeld; de envelop is daarom kleiner gemaakt (hoogte minus 13 rem).
- **Minder beweging**: het systeem op 'minder beweging' op 390 pixels geeft een uitnodiging die direct opent (`is-open`, 700 ms na de tik), zonder fouten in de console; de pauzeknop is gedekt door de effectencontrole hierboven.

**Niet gedaan voor Gouden licht**: de volledige browsercontrole `e2e/controle2.cjs` (vier schermformaten, gedragscontroles), het snelheidsonderzoek met Lighthouse en de meting van de belasting op een vertraagde processor; ook niet getest in Safari, Firefox of op echte telefoons, en het geluid van de opname is niet beluisterd.

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

# Toegankelijkheid en contrast van alle ontwerpen in alle kleuren (eenmalig: npm install --no-save axe-core@4)
node e2e/toegankelijkheid.cjs http://127.0.0.1:8000 /tmp/toegankelijkheid.json [code ...]

# Effecten: deeltjes, knal, feestje, knop Beweging en 'minder beweging' (acht controles per ontwerp)
node e2e/effecten.cjs http://127.0.0.1:8000 /tmp/effecten [code ...]
# Alleen de belasting meten (vier keer vertraagde processor); draai dit zonder andere controles ernaast
CHECKS=0 PERF=1 node e2e/effecten.cjs http://127.0.0.1:8000 /tmp/effecten-belasting
```

Het rapport en de schermafbeeldingen komen in de uitvoermap (`rapport.json` of `rapport-<schermformaat>.json`, en per schermformaat een map met afbeeldingen). Gebruik bij de controles een server met `DEBUG` uit (zoals gunicorn); de ontwikkelserver toont bij een 404 een eigen foutpagina.

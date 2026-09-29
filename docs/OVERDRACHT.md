# Overdracht: waar staan we

Stand van 28 september 2026. Dit document is bedoeld voor wie het project overneemt, en voor de Claude die daarbij helpt.

## In het kort

Vaylide (eerst de werknaam Vierlief, daarna kort Vaylide) is een werkende eerste versie **in testmodus**. Betalingen zijn gesimuleerd, e-mails worden alleen bewaard en de AI-hulp gebruikt vaste voorbeeldteksten. Op elke pagina staat een testbalk.

Wat er staat:

- **Website**: homepage, collectie, ontwerpdetail met werkend voorbeeld, zo werkt het, prijzen, inspiratie, over ons, veelgestelde vragen, contact, zoeken, privacy en voorwaarden (de juridische teksten zijn nog concept).
- **34 uitnodigingsontwerpen**:
  - vier volledig eigen ontwerpen met elk vier kleurvarianten: Liefde op papier (envelop met lakzegel), Avondgoud (gouden dubbele deur), Puur moment (doorschijnend vel) en de kerstkaart Winterlicht (zie hieronder);
  - 30 Atelier-ontwerpen, **vijf per gelegenheid**, elk met een eigen opening (envelop, vouwkaart, gordijn, cadeaulint, sluier, confetti, ballonnen, sterrenhemel, schuifpaneel, polaroid of een cadeau om uit te pakken) en drie kleurvarianten. Ze delen één opbouw in `designs/_atelier/v1/`. Overzicht en keuzes: `docs/AANPAK.md` onder "Uitbreiding: 30 nieuwe ontwerpen"; zelf een ontwerp toevoegen: `docs/HANDLEIDING.md`.
- **Kerstkaarten** (ronde 7): de gelegenheid Kerst, met of zonder uitnodiging voor het kerstdiner, en het ontwerp **Winterlicht**: een envelop van blindgedrukt papier met een lakzegel (na een tik glanst het reliëf goud en gaat de envelop open), een getekend kerstraam met twinkelende lichtjes en sneeuw, de datum op kraskaartjes van goudfolie, een gouden programma, een afteller naar kerst en in het voorbeeld "Stille nacht" als speeldoosje. Op de homepage en bij Inspiratie staat een brede tegel "Kerst". Keuzes en wat er uit de schermopname van de eigenaar komt: `docs/AANPAK.md` onder "Ronde 7: kerstkaarten"; beheren en aanpassen: `docs/HANDLEIDING.md` onder "Kerstkaarten en Winterlicht".
- **Effecten op alle 34 uitnodigingen**: zwevende sfeer (bloemblaadjes, goudstof, een sterrenhemel, ballonnen, neon en meer), een knal op het moment dat de uitnodiging opengaat (bij de cadeau-opening springt het deksel eraf en vliegen er cadeautjes uit), een feestje als een gast zich aanmeldt, namen die verschijnen alsof ze geschreven worden of met een gouden glans, en onthullingen bij het scrollen. Elk ontwerp heeft een eigen combinatie. Met de knop **Beweging** zet een gast alles stil. Overzicht en keuzes: `docs/AANPAK.md` onder "Ronde 5"; zelf kiezen of aanpassen: `docs/HANDLEIDING.md` onder "Effecten".
- **Samenstellen in stappen**: gelegenheid, ontwerp, gegevens, programma, aanmelden, foto's, stijl, voorbeeld en bestellen. Voortgang wordt per stap bewaard, ook zonder account.
- **Bestellen en betalen**: testbetaling (of Mollie, zodra er een sleutel is). Publiceren gebeurt alleen na een serverzijdige betalingsbevestiging, via een takenwachtrij met herhalingen.
- **Gasten**: aanmelden zonder account, eigen antwoord later wijzigen, agenda, route, delen.
- **Mijn Vaylide**: uitnodigingen, aanmeldingen, gastenlijst exporteren, wijzigen en opnieuw publiceren, extra wensen.
- **Beheer**: aanvragen, bestellingen, uitnodigingen, klanten, verwerking, ontwerpen, prijzen, instellingen en contactberichten.

Gedane rondes:

1. Bouw van het hele platform.
2. Strakker en sneller: rustiger vormgeving, minder tekst, snellere pagina's.
3. Vormgeving volgens de voorbeeldfoto van de eigenaar: goud, crème en bosgroen, een hartlogo (in ronde 6 vervangen) en de pagina's Inspiratie, Over ons en Zoeken. De keuzes en afwijkingen staan in `docs/AANPAK.md` onder "Nieuwe vormgeving".
4. 30 nieuwe ontwerpen, vijf per gelegenheid, met eigen voorbeeldbeelden en kaartbeelden. De homepage licht drie ontwerpen uit, de collectie zet per gelegenheid de passende ontwerpen vooraan, en zakelijke evenementen kunnen een aantal jaren opgeven.
5. Effecten en beweging op alle 33 ontwerpen (zie hierboven), een nieuwe cadeau-opening (Glitter & goud, Regenboog en Stipjes), kaarten op de website die meebewegen en glanzen, nieuwe kaartbeelden, en het lakzegel van Liefde op papier met goed leesbare initialen.
6. Nieuw merk: **Vaylide** (eerst kort Vaylide), met het logo van de eigenaar zoals aangeleverd (de V, VAYLIDE en de regel eronder) in de kop en voet, bij het samenstellen, in het beheer, in de e-mails, op de deelafbeelding en als icoon op het beginscherm; de V uit het logo als tabblad-icoon. Overal waar mensen de naam zien, staat Vaylide. Keuzes: `docs/AANPAK.md` onder "Ronde 6: Vaylide"; het logo opnieuw maken of vervangen: `tools/logo/README.md`.
7. Kerstkaarten: de gelegenheid Kerst (ook alleen een kerstgroet, zonder datum of locatie), het ontwerp Winterlicht in vier kleuren met eigen getekende beelden, het effect sneeuw, de kersttegel op de website, en "kerstkaart" in plaats van "uitnodiging" in de e-mails en op de bestelstatus.

8. Nieuwe vormgeving van de website (29 september 2026): een 3D-wereld over de hele kop met een envelop met het logo die opengaat (tik, klik of Enter) en een gouden kaart met reliëf; boogvormige themakaarten met Kerst voorop; een warm kerstpodium met zwevende kerstkaarten; stappen als kaartjes; een licht paneel in plaats van het donkere; vragen vlak voor de voettekst; een voettekst met een stilstaand beeld van de bloem; dezelfde stijl op Zo werkt het, Prijzen, Inspiratie en Over ons (tekst van de eigenaar). Lakzegel: Essentieel krijgt een standaardzegel met een motief (rood, of groen bij een groene kleurvariant), Compleet het persoonlijk zegel met initialen (functie `zegel`, migratie `catalog/0002`). Een bedrijfslogo op het zegel is er nog niet: op aanvraag via Op maat. Prijzen zijn niet veranderd.

9. Voorbereiding livegang (29 september 2026):
   - Verwerking:
     - na publicatie volgt de levering aan de koper als aparte taak (`deliver_order`);
     - een herhaling levert precies één keer;
     - Beheer → Verwerking toont vastgelopen bestellingen met "Verwerking opnieuw starten".
   - Klantreis: in de browser gecontroleerd met `e2e/klantreis.cjs`.
   - Back-up:
     - herstel in een verse database gerepareerd en getest;
     - een versleutelde tweede back-uplocatie (S3-compatibel) is voorbereid (`docs/BACKUP.md`).
   - Juridische teksten: feitelijk aangevuld (levering, afbreken, bewaartermijn, AI bij extra wensen).
   - `docs/INVULLIJST.md`: ontbrekende feiten en teksten die juridisch beoordeeld moeten worden.
   - Domein: `vaylide.nl` voorbereid (`docs/DOMEIN.md`); de DNS is niet gewijzigd.
   - AI-model standaard `claude-opus-5-5`.

10. Bruiloftsontwerp **Eerste dans** (29 september 2026):
    - paleisdeuren met een lakzegel;
    - een balzaal met kroonluchter en een slinger van hortensia's en rozen;
    - een getekend bruidspaar dat zacht danst (blonde bruid in wit, bruidegom in een zwart pak);
    - vier kleuren (hemelsblauw, champagne, saliegroen, poederroze).

    Tekeningen: `tools/eerste_dans/maak_tekeningen.py`.

11. Ontwerp **Balzaal** (29 september 2026): aangeleverde beelden als lagen (zaal, bruidspaar, bloemen), envelop met lakzegel, warm licht en diepte. Haarkleurkeuze voorbereid, maar verborgen tot alle negen beelden er zijn. Zie `docs/BALZAAL.md`.

12. **Onze eigen gezichten** (Balzaal): upload met toestemming, voorbeeld via een beeld-API, goedkeuren vóór betaling, precies die versie na betaling. Gebouwd en getest met een nagebootste API; **staat uit** tot de eigenaar API, prijs en privacytekst bevestigt. Zie `docs/GEZICHTEN.md`.

13. **Specials** (Balzaal): eigen categorie en eigen meerprijs (nog niet ingesteld, dus nog niet te bestellen). Dans als videolaag voorbereid (Google Veo 3.1, tools/balzaal/maak_dansvideo.py) en haarkleurscènes (tools/balzaal/maak_haarvarianten.py); beide wachten op een sleutel en akkoord op de kosten. Haarkleur ook bij eigen gezichten. Zie `docs/BALZAAL.md`.

Wat getest is en hoe: `docs/CONTROLES.md`. Kort, na ronde 7: 160 tests (op SQLite), een browsercontrole op 840 pagina's (vier schermformaten, alle 34 ontwerpen, 272 gedragscontroles; Winterlicht daarna opnieuw op de definitieve stand), 272 controles van de effecten en een meting van de belasting (alle 34 ontwerpen), toegankelijkheid en contrast van alle 34 ontwerpen in alle 106 kleurvarianten, het contrast van de tekst op de tekening van het kerstraam, en axe op de gewijzigde websitepagina's. Na ronde 6: 139 tests (op SQLite; op PostgreSQL 16 in ronde 5), een browsercontrole op 816 pagina's (vier schermformaten, alle 33 ontwerpen, 264 gedragscontroles), toegankelijkheid van de website en een lokale nabootsing van de Render-instellingen met PostgreSQL. Uit ronde 5 (in ronde 6 veranderden aan de uitnodigingen alleen de naam onderaan en het tabblad-icoon): 264 controles van de effecten (ook stilzetten en 'minder beweging'), een meting van de belasting op een vertraagde processor, en toegankelijkheid en contrast van alle ontwerpen in alle kleuren.

Voorvertoning (statisch, alleen om te kijken): https://claude.ai/artifact/DYkTUBCKzn63jE8Mk9x28M

## Zo ga je verder

1. Haal het project op met `git clone https://github.com/bootsman075-ops/vaylide.nl`, of pak de zip uit (map `vaylide/`). Beide hebben de volledige git-geschiedenis.
2. Open een terminal in die map en start Claude Code (`claude`). Het bestand `CLAUDE.md` in de hoofdmap wordt automatisch gelezen, met de vaste regels van de eigenaar.
3. Geef als eerste opdracht bijvoorbeeld:

   > Lees CLAUDE.md en docs/OVERDRACHT.md. Zet de ontwikkelomgeving op volgens de README, draai de tests en vat in een paar zinnen samen wat de stand is en welke open punten er zijn. Wacht daarna op mijn opdracht.

4. Maak zelf een beheeraccount aan met `python manage.py createsuperuser`. Klanten loggen in met een code; in testmodus staat die code direct op het scherm.

## Eigen repository

Het project staat in een eigen repository, los van andere projecten: **https://github.com/bootsman075-ops/vaylide.nl** (branch `main`). De eigenaar maakte hem aan en koos voor **openbaar**: iedereen kan de code en de documentatie lezen. Er staan geen wachtwoorden of sleutels in (vóór het versturen is de hele geschiedenis daarop doorzocht). Op privé zetten kan altijd via Settings → Change repository visibility.

Een oudere kopie, nog onder de werknaam Vierlief, staat nog in de repository van Vantor Studios: de branch `claude/practical-ride-1m3pgk` bevat drie commits "Vierlief: …" met de map `vierlief/` en een regel in `.vercelignore`, verder niets. Die kopie is **verouderd**: niet gebruiken. Opruimen kan door die branch op GitHub te verwijderen; vanuit de werkomgeving lukte dat niet meer (geen toegang meer tot die repository).

## Open punten

In een logische volgorde. Punt 2 alleen met akkoord van de eigenaar.

1. **Oude kopie in Vantor opruimen**: de branch `claude/practical-ride-1m3pgk` van vantor-studios-website verwijderen (zie hierboven).
2. **Online en livegang**: de site op het eigen domein zetten, eerst als testversie met een wachtwoord (stappenplan in `docs/ONLINE.md`, aanbevolen via GitHub en Render met `render.yaml`; het domein is `vaylide.com`), daarna live met Mollie, SMTP, bedrijfsgegevens en juridisch gecontroleerde privacy en voorwaarden (checklist in `docs/LIVEGANG.md`).
3. **Eigen foto's** (optioneel): de sfeerbeelden op de website en de beelden in de voorbeelduitnodigingen zijn eigen, getekende beelden. Eigen foto's met de juiste rechten kunnen ze vervangen; zie `docs/HANDLEIDING.md` onder "Teksten en beelden van de website".
4. **Referenties vergelijken**: de referentiesites en de schermopname met drie voorbeelden zijn nooit bekeken (geblokkeerd of niet ontvangen); zie `docs/AANPAK.md`. Dat geldt ook voor de 30 nieuwe ontwerpen. Aanpassingen aan ontwerpen komen als nieuwe ontwerpversie. De schermopname voor de kerstkaarten (ronde 7) is wel bekeken, als losse beelden.
5. **Collectie kiezen** (optioneel): welke drie ontwerpen de homepage uitlicht (`HOME_DESIGNS` in `core/content.py`), en eventueel de volgorde of zichtbaarheid per ontwerp in Beheer → Ontwerpen.
6. **Testen op echte apparaten**: iPhone (Safari), Android, Firefox en met schermlezers (VoiceOver, TalkBack). Tot nu toe is alleen Chromium gebruikt. Let daarbij vooral op de effecten: soepelheid op een ouder Android-toestel en de weergave in Safari.
7. **Docker**: de image is getest in ronde 2, niet opnieuw na de nieuwe vormgeving en de nieuwe ontwerpen.
8. **Wens voor later**: de teksten van de website beheerbaar maken in Beheer (nu in `core/content.py`).
9. **Kerstkaarten beoordelen** (eigenaar): bekijk Winterlicht in alle vier kleuren (ook als voorbeeld op de website) en beslis over:
   - de teksten ("Warme kerstgroeten van", "Een kerstgroet voor jou", "Schuif je aan?");
   - of de kersttegel het hele jaar op de homepage staat of alleen in het najaar (weghalen: de zin bij `kerst` in `OCCASION_TILE_NOTES`, `core/content.py`);
   - de prijs van een kerstkaart (nu dezelfde pakketten als een uitnodiging);
   - of klanten ook het speeldoosje met "Stille nacht" mogen kiezen (nu alleen in het voorbeeld; eigen muziek kan wel).

   Keuzes en afwijkingen van de schermopname: `docs/AANPAK.md` onder "Ronde 7: kerstkaarten".
10. **Winterlicht op echte telefoons**: vooral Safari op een iPhone (de gouden golf gebruikt een nieuwere CSS-techniek; krassen met de vinger) en een ouder Android-toestel. Het voorbeeld is drie tot vier keer zo zwaar als de andere ontwerpen (zie `docs/CONTROLES.md`). Als het te traag is, kunnen de beelden kleiner voor telefoons (in een `v2`).
11. **Teksten in het bestelproces** (optioneel): de e-mails en de bestelstatus spreken van een kerstkaart; het samenstellen en Mijn Vaylide zeggen nog "uitnodiging".
12. **Bruiloftsontwerp Voor altijd** (28 september 2026): een volledig eigen ontwerp (`voor-altijd`) voor bruiloft, verloving en jubileum: een fluwelen ringdoosje op linnen dat openklapt, met twee gouden ringen op satijn; daarna een olijfkrans om het monogram, de datum in drie in elkaar grijpende ringen en het programma als gouden tijdlijn. Kleuren Saliegroen, Bordeaux, Nachtblauw en Poederroze; in het voorbeeld de Canon in D van Pachelbel. Tekeningen uit `tools/voor_altijd/maak_tekeningen.py`. Het staat vooraan in de collectie bij Bruiloft (sort_order 5).
12. **Uitnodiging of wenskaart** (28 september 2026): bij Kerst kiest de klant per kaart 'Uitnodiging' (met datum, locatie, programma en aanmelden) of 'Wenskaart' (alleen een kerstgroet, met een afteller naar kerst), in de stap Gegevens en op de ontwerppagina. Alle zes kerstontwerpen passen hun teksten aan (bijvoorbeeld 'Een kerstgroet voor jou'). Een wenskaart is alleen een kerstwens: ook de dresscode, 'Goed om te weten' en 'Vragen' (contact) worden niet getoond. In het samenstellen valt de stap Aanmelden weg en heet 'Programma & info' dan 'Afsluiting' (alleen de afsluitende wens); ingevulde programma-, dresscode- en contactgegevens blijven bewaard voor als het toch een uitnodiging wordt (`WENSKAART_SKIP` en `WENSKAART_LABELS` in `studio/steps.py`). Andere gelegenheden kennen nog geen wenskaart; uitbreiden kan via `event_optional` in `catalog/occasions.py` plus passende teksten.
13. **Meer kerstontwerpen** (optioneel): voor Kerst zijn er nu zes ontwerpen: **Aan tafel** (`aan-tafel`, volledig eigen ontwerp voor het kerstdiner: een plaatskaartje op een houten tafel tussen brandende kaarsen dat openklapt, een dennenslinger met lichtjes, een menukaart met een lint in Schotse ruit; kleuren Haardvuur, Dennengroen, Kaarslicht en Schotse ruit; in het voorbeeld 'We Wish You a Merry Christmas' als wals; tekeningen uit `tools/aan_tafel/maak_tekeningen.py`), **Gloria** (`gloria`, volledig eigen ontwerp met engelen: twee engelenvleugels liggen gevouwen over het scherm en spreiden zich na een tik op de ster; engelen met bazuinen, wolken, de datum in een ster en boogramen; kleuren Hemelsblauw, Parelmoer, Kerstrood en Nachtgoud; in het voorbeeld 'Angels We Have Heard on High' met harp, engelenkoor en celesta; tekeningen uit `tools/gloria/maak_tekeningen.py`), **Middernacht** (`middernacht`, volledig eigen ontwerp: een kerstgala voor volwassenen met een glazen kerstbal als opening waar je in duikt, art deco, goudfolie, een toegangskaart en een menukaart; kleuren Zwart & champagne, Smaragd & goud, Bordeaux & roségoud en Ivoor & goud; in het voorbeeld 'Carol of the Bells' als eigen zetting met celesta, strijkers, pizzicato en kerkklok), Winterlicht, **Sneeuwpret** (`sneeuwpop`: een zwaaiende sneeuwpop met rode sjaal en wanten tussen verlichte kerstbomen, vouwkaart, kleuren IJsblauw, Zilverwit, Mint en Poolnacht) en **Ho ho ho** (`kerstman`, sinds 28 september 2026), een Atelier-ontwerp met de kerstman als versiering, een cadeau-opening, sneeuw en vier kleuren (Kerstrood, Sneeuwwit, Dennengroen, Nachtblauw). Beschrijving in `tools/atelier/specs.py`, tekening in `designs/_atelier/v1/ornaments/kerstman.html`.
13. **Technische namen** (optioneel, liefst vóór de livegang): de instellingen heten nog `VIERLIEF_…`, net als de cookie-, sessie- en opslagnamen, de cachetabel, het databasebestand (`data/vierlief.sqlite3`), het stijlbestand `static/css/vierlief.css` en de testaccounts (`controle@vierlief.test`). Bezoekers zien die niet. Omzetten naar `VAYLIDE_…` kan in één keer, maar dan moeten ook `.env`, de documentatie en de hosting mee, en vervallen bestaande sessies en keuzes van gasten.

## Goed om te weten

- **Heb je al een eigen ontwikkeldatabase** van een eerder pakket? Draai dan eenmalig `python manage.py sync_designs --update-manifest`, zodat de ontwerpen hun effecten krijgen. Bij een nieuwe database gebeurt dit vanzelf bij `migrate`.
- In het pakket zitten geen geheimen, geen database en geen uploads. Maak `.env` aan vanuit `.env.example`. De database (SQLite) en uploads komen in `data/`.
- Prijzen staan op "Voorlopige prijzen" (Essentieel € 39, Compleet € 69) en zijn aan te passen in Beheer.
- De voorbeelduitnodigingen gebruiken fictieve namen en locaties en zijn als voorbeeld gemarkeerd.
- De lettertypen staan op de eigen server (open source, OFL); er gaan geen verzoeken naar Google Fonts.

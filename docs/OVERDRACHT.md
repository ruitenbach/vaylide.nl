# Overdracht: waar staan we

Stand van 16 oktober 2026. Dit document is bedoeld voor wie het project overneemt, en voor de Claude die daarbij helpt.

## In het kort

Vaylide (eerst de werknaam Vierlief, daarna kort Vaylide) is een werkende eerste versie **in testmodus**. Betalingen zijn gesimuleerd, e-mails worden alleen bewaard en de AI-hulp gebruikt vaste voorbeeldteksten. Op elke pagina staat een testbalk.

Wat er staat:

- **Website**: homepage, collectie, ontwerpdetail met werkend voorbeeld, zo werkt het, prijzen, inspiratie, over ons, veelgestelde vragen, contact, zoeken, privacy en voorwaarden (de juridische teksten zijn nog concept).
- **34 uitnodigingsontwerpen**:
  - drie volledig eigen ontwerpen met elk vier kleurvarianten: Liefde op papier (envelop met lakzegel), Avondgoud (gouden dubbele deur) en Puur moment (doorschijnend vel);
  - **Kerstmagie** (ronde 7): een donkere winterkaart met een openingsfilm van 10 seconden (sneeuwkristal, kerstdorp, stoomtrein) die pas start na een tik in het midden, met drie kleurvarianten en stukken uit de film in de kaart zelf. Uitleg: `docs/HANDLEIDING.md` onder "Ontwerp met een openingsfilm";
  - 30 Atelier-ontwerpen, **vijf per gelegenheid**, elk met een eigen opening (envelop, vouwkaart, gordijn, cadeaulint, sluier, confetti, ballonnen, sterrenhemel, schuifpaneel, polaroid of een cadeau om uit te pakken) en drie kleurvarianten. Ze delen één opbouw in `designs/_atelier/v1/`. Overzicht en keuzes: `docs/AANPAK.md` onder "Uitbreiding: 30 nieuwe ontwerpen"; zelf een ontwerp toevoegen: `docs/HANDLEIDING.md`.
- **Effecten op alle 34 uitnodigingen**: zwevende sfeer (bloemblaadjes, goudstof, sneeuw, een sterrenhemel, ballonnen, neon en meer), een knal op het moment dat de uitnodiging opengaat (bij de cadeau-opening springt het deksel eraf en vliegen er cadeautjes uit), een feestje als een gast zich aanmeldt, namen die verschijnen alsof ze geschreven worden of met een gouden glans, en onthullingen bij het scrollen. Elk ontwerp heeft een eigen combinatie. Met de knop **Beweging** zet een gast alles stil. Overzicht en keuzes: `docs/AANPAK.md` onder "Ronde 5"; zelf kiezen of aanpassen: `docs/HANDLEIDING.md` onder "Effecten".
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
7. Kerstmagie: een nieuw ontwerp rond de aangeleverde film (staand, 10 seconden, zonder geluid). Tik in het midden start de film; na afloop gaat hij over in de uitnodiging. Nieuw effect **sneeuw**. Keuzes: `docs/AANPAK.md` onder "Ronde 7: Kerstmagie".

Wat getest is en hoe: `docs/CONTROLES.md`. Kort, na ronde 7: 146 tests (op SQLite; op PostgreSQL 16 in ronde 5), een browsercontrole op 816 pagina's (vier schermformaten, alle 33 ontwerpen, 264 gedragscontroles), toegankelijkheid van de website en een lokale nabootsing van de Render-instellingen met PostgreSQL. Uit ronde 5 (in ronde 6 veranderden aan de uitnodigingen alleen de naam onderaan en het tabblad-icoon): 264 controles van de effecten (ook stilzetten en 'minder beweging'), een meting van de belasting op een vertraagde processor, en toegankelijkheid en contrast van alle ontwerpen in alle kleuren.

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
4. **Referenties vergelijken**: de referentiesites en de schermopname met drie voorbeelden zijn nooit bekeken (geblokkeerd of niet ontvangen); zie `docs/AANPAK.md`. Dat geldt ook voor de 30 nieuwe ontwerpen. Aanpassingen aan ontwerpen komen als nieuwe ontwerpversie.
5. **Collectie kiezen** (optioneel): welke drie ontwerpen de homepage uitlicht (`HOME_DESIGNS` in `core/content.py`), en eventueel de volgorde of zichtbaarheid per ontwerp in Beheer → Ontwerpen.
6. **Testen op echte apparaten**: iPhone (Safari), Android, Firefox en met schermlezers (VoiceOver, TalkBack). Tot nu toe is alleen Chromium gebruikt. Let daarbij vooral op de effecten: soepelheid op een ouder Android-toestel en de weergave in Safari.
7. **Docker**: de image is getest in ronde 2, niet opnieuw na de nieuwe vormgeving en de nieuwe ontwerpen.
8. **Wens voor later**: de teksten van de website beheerbaar maken in Beheer (nu in `core/content.py`).
9. **Technische namen** (optioneel, liefst vóór de livegang): de instellingen heten nog `VIERLIEF_…`, net als de cookie-, sessie- en opslagnamen, de cachetabel, het databasebestand (`data/vierlief.sqlite3`), het stijlbestand `static/css/vierlief.css` en de testaccounts (`controle@vierlief.test`). Bezoekers zien die niet. Omzetten naar `VAYLIDE_…` kan in één keer, maar dan moeten ook `.env`, de documentatie en de hosting mee, en vervallen bestaande sessies en keuzes van gasten.
10. **Kerstmagie controleren op echte apparaten** (vooral iPhone/Safari): de mp4 is niet in een browser afgespeeld (Chromium in de testomgeving speelde de webm-reserve) en de film is nooit beluisterd of bekeken op een echt scherm, dus ook niet of hij op een telefoon soepel loopt. Test ook of de film op mobiele data niet te traag laadt (2,7 MB).
11. **Gelegenheid Kerst of Feestdagen** (keuze van de eigenaar): er is geen gelegenheid voor een kerstdiner of -borrel van particulieren. Kerstmagie staat nu onder Zakelijk evenement, Bruiloft, Verloving, Verjaardag en Jubileum. Een eigen gelegenheid raakt het samenstellen, de teksten en de tegels op de homepage; dat is niet zonder akkoord gedaan.
12. **Rechten op de film**: de film is door de eigenaar aangeleverd. Controleer dat de rechten (ook van de maker van het beeld) het gebruik op de site en in uitnodigingen van klanten toestaan.

## Goed om te weten

- **Heb je al een eigen ontwikkeldatabase** van een eerder pakket? Draai dan eenmalig `python manage.py sync_designs --update-manifest`, zodat de ontwerpen hun effecten krijgen. Bij een nieuwe database gebeurt dit vanzelf bij `migrate`.
- In het pakket zitten geen geheimen, geen database en geen uploads. Maak `.env` aan vanuit `.env.example`. De database (SQLite) en uploads komen in `data/`.
- Prijzen staan op "Voorlopige prijzen" (Essentieel € 39, Compleet € 69) en zijn aan te passen in Beheer.
- De voorbeelduitnodigingen gebruiken fictieve namen en locaties en zijn als voorbeeld gemarkeerd.
- De lettertypen staan op de eigen server (open source, OFL); er gaan geen verzoeken naar Google Fonts.

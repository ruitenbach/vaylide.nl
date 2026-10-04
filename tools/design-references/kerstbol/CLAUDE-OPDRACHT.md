# Claude Code — Vaylide Kerstmagie Sneeuwbol

Voer dit uit in de bestaande Vaylide-repository. Lees eerst AGENTS.md en gebruik Development Studio Workflow. Het pakket bevat een door de gebruiker goedgekeurd standalone prototype, nog geen Django-integratie.

## Definitieve richting
Voeg een NIEUW zelfstandig kerstontwerp toe, bijvoorbeeld Kerstmagie Sneeuwbol (slug kerstmagie-sneeuwbol, controleer beschikbaarheid). Gebruik de bestaande categorie Kerst. Behoud alle bestaande ontwerpen, waaronder Balzaal en Balzaal Cinematic en de eerdere verbeteringen uit commit 2d0a7af indien aanwezig. Onderzoek de actuele branch en repositoryconventies; neem verouderde pad- of versiedetails niet aan.

De klant ziet een realistisch gesloten rood cadeau met gouden satijnen lint in een smaragdgroene kerstkamer. Het cadeau is zelf klikbaar, met de tekst Tik om je kerstcadeau te openen. Geen autoplay vóór die klik. Na klikken speelt één doorlopende realistische video af: de strik gaat volledig los, lint glijdt weg, een kaal rood deksel opent, een sneeuwbol met verlichte kerstboom komt uit de doos, rendieren en slee verschijnen buiten het raam. De video duurt ongeveer 10 seconden en stopt op het eindbeeld. De strik mag niet op het geopende deksel blijven zitten. Geen getekend SVG-cadeau, geen losse CSS-animatie ter vervanging van de goedgekeurde video.

Er zijn twee verschillende overlay-effecten: warme gouden fonkelingen rond het gesloten cadeau en tijdens de eerste fase van de opening; vanaf 6,5 seconden veranderen deze in fijne witgouden kristalglinsteringen rond de sneeuwbol. Lichtpuntjes fonkelen en vervagen, geen vallende confetti of blaadjes. De vormgeving en effecten in de meegeleverde preview zijn leidend.

## Bestanden
- preview-standalone.html: exact goedgekeurd prototype, inclusief ingebedde media.
- preview-assets.html: dezelfde preview met losse mediapaden.
- assets/kerst-gesloten.webp: gesloten cadeau, startposter.
- assets/kerst-opening-web.mp4: geoptimaliseerde stille 720 × 1280-video.
- assets/kerst-opening-master.mp4: originele gegenereerde video voor eventuele technische transcodering.

## Integratie
1. Inspecteer bestaande designregistratie, manifesten/versies, templates, CSP, klantstudio, kaartmodel, bestellen en deel-/gastenlinks. Gebruik hun conventies en bestaande veilige gegevensroutes.
2. Registreer het nieuwe kerstontwerp met eigen assets en preview. Splits inline CSS/JS uit indien nodig voor CSP. Geen base64-media in productie en geen externe generatie-CDN als verplichte runtimebron.
3. Koppel titel/kerstgroet, namen/afzender en overige ondersteunde tekstvelden aan bestaande studio-personalisatie. Escape klantinhoud correct; queryparameters en placeholders uit het prototype zijn geen productiegegevensbron.
4. Integreer bestaande bestel-/testbetalingsflow, opgeslagen kaarten en delen. RSVP alleen wanneer het bestaande kerstkaarttype dat ondersteunt; forceer geen trouwprogramma, trouwdatum of countdown op deze kerstgroet.
5. Behoud de klik op het cadeau, met een toegankelijke echte button en bruikbaar touchdoel. Begin playback rechtstreeks vanuit de user gesture. Gebruik muted/playsinline en toon een duidelijke handmatige fallback bij afspeelblokkade of laadfout.
6. Toon de persoonlijke groet na het einde van de video. Behoud het eindbeeld en Opnieuw beleven. Voeg een rustige Opening overslaan toe als productbediening, die het eindbeeld en de groet direct toont zonder te wachten op mediazoekacties. Gebruik zo nodig een lokaal opgeslagen eindposter uit het masterbestand.
7. Respecteer reduced motion: geen sparkle-animatie, geen autoplay, mogelijkheid de opening handmatig te spelen of over te slaan. Werk focus, tabindex en aria-status bij; maak onzichtbare captions/knoppen ook ontoegankelijk tot ze zichtbaar worden.
8. Beperk animatiekosten: zet voorfase-fonkelingen uit zodra fase twee start; stop sparkle-animaties na hun korte eindfase. Ruim listeners/timers op waar nodig en herstel alle fases bij replay. Prototype-effecten mogen technisch verbeterd worden zonder de goedgekeurde uitstraling te veranderen.
9. Gebruik bestaande local/static assetopslag en een passende laadstrategie, zonder de hele homepage met videodata te belasten. Geen automatisch herhalen van de video.

## Controle en overdracht
- Echte browsertests op 360, 390, 768 en 1366 px: geen horizontale scroll, cadeau klikbaar, juiste poster vóór de klik, geen video vóór user gesture, soepele opening, correct eindbeeld en leesbare groet.
- Controleer hele bestaande klantreis: ontwerp kiezen, teksten wijzigen, preview, bestellen/testbetaling, opgeslagen kerstkaart, delen/gastenlink en teruglezen van klantteksten.
- Test replay, overslaan, reduced motion, toetsenbord, focus, autoplay-blokkade en media-laadfout. Controleer CSP en laad-/animatieprestaties.
- Draai relevante bestaande tests en verplichte projectchecks. Voeg alleen betekenisvolle regressietests toe.
- Lever een lokale of afgesproken testpreview, screenshots/opname, gewijzigde bestanden en testresultaten. Vermeld beperkingen eerlijk. Dit pakket is niet reeds als productie-integratie getest.

## Grenzen
Werk eerst op een aparte branch. Geen productiepublicatie zonder expliciet akkoord van de gebruiker. Behoud bestaande betaal-/SMTP-configuratie en bestaande ontwerpen. Controleer de bedoelde testsite en branch voordat je een stagingdeployment doet.

BELANGRIJK: genereer geen nieuwe AI-beelden/video's, gebruik geen Higgsfield-credits en verleng/regeneer de video niet. De gebruiker wil voortaan eerst idee, beeld en beweging bespreken en pas na expliciet akkoord credits besteden; ook retries/varianten vereisen overleg. Gebruik de goedgekeurde assets uit dit pakket.

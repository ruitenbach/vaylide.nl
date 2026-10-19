# Beeld bij "Jullie verhaal verdient iets bijzonders" (homepage)

Bestanden: `static/img/site/op-maat.webp` (1100x800), `op-maat-700.webp` (700x509) en `op-maat-mobiel.webp` (700x640), allemaal met doorzichtige achtergrond.
De oudere `maatwerk*.webp` blijven bestaan maar worden niet meer gebruikt door `core/templates/core/home.html`.

Het beeld is geen tekening maar de echte envelop-engine van VAYLIDE (Signature Ivory, `templates/partials/envelop/collectie.html`) met een eigen kaart:

1. `maatwerk-kaart.css` zet de kaart staand, groot en op de voorgrond en bevat de opmaak van de voorbeeldkaart (gouden folie-monogram "S&D", dubbel kader met hoekdetails, fotoboog "Jouw foto", quote, label "Voorbeeld op maat"). De envelop krijgt een iets dieper champagnepapier.
2. Die opmaak wordt in de labpagina (`/lab/enveloppen/?stijl=signature&zegel=champagne-monogram&monogram=S%26D`, alleen met DEBUG) in de kaart gezet, het zegel breekt en de envelop gaat open; een schermafbeelding met doorzichtige achtergrond (`voorvertoning-op-maat/open.png`, 2x) is de basis.
3. `maatwerk-op-maat.html` (`?v=d` of `?v=m`) voegt de gloed, schaduw, de twee takjes (uit `designs/silk-reveal/v1/img/takje.webp`), een kleine voorbeeldfoto en het hangertje met koordje aan het zegel toe. De foto is de aangeleverde Balzaal-scène met het fictieve bruidspaar (`designs/balzaal/v1/img/scene-bruin-blond.webp`), in een boogvormige lijst met gouden randje, warm getint (verzadiging -16%, sepia 12%) en bewust kleiner dan de kaart; een echte foto vervangt hem door de `background`-url van `.foto` te wijzigen. Schermafbeelding van `#stage` met doorzichtige achtergrond, daarna naar WebP (kwaliteit 88, alfa 92).

Vereist: de ontwikkelserver (`manage.py runserver`, voor de lettertypen en de lab-pagina) en een tweede eenvoudige server voor de map (`python -m http.server 8765`), en Playwright of een andere browser met "negeer CSP" voor de schermafbeeldingen.

## Update 19 oktober 2026: Gouden Avond

De homepage toont in dit blok nu de kaart Gouden Avond die deels uit een geopende envelop steekt (`op-maat-gouden-avond.webp`, `-700.webp` en `-mobiel.webp`). De envelop is de echte Signature Ivory-envelop uit de Envelope Collection (papierstructuur, vouwen, voering, lakzegel met de V), niet hertekend. Maken: (1) start `DJANGO_DEBUG=true manage.py runserver`; (2) `node tools/merkbeelden/render_gouden_avond_envelop.cjs <open.png>` zet de kaartbeeld `static/img/designs/gouden-avond.webp` in de labpagina, opent de envelop en schrijft een doorzichtige PNG (2x); (3) `python tools/merkbeelden/maak_op_maat_gouden_avond.py <open.png>` schaalt dat naar de drie formaten. De oudere `op-maat*.webp` blijven staan maar worden niet meer gebruikt.

## Scène rond de envelop (19 oktober 2026, ronde 3)

`maak_op_maat_gouden_avond.py` bouwt rond de gerenderde envelop een ingetogen scène: travertijnen sokkel met slagschaduw, zachte bladschaduwen rechtsboven en fijn gipskruid links en rechts (allemaal procedureel getekend, tint-op-tint champagne/beige/ivoor). Een vleug zijde (`zijde()`) is uitgeprobeerd maar zag er als platte vlek uit en staat daarom uit (`None`). De rand links en boven vervaagt, zodat er geen naad met de kaartachtergrond zichtbaar is. Afmetingen: bureaublad 1100x1000 (en 700x636), mobiel 700x720.

## Rozen in plaats van gipskruid (19 oktober 2026, ronde 4)

Het gipskruid is vervangen door twee fotorealistische rozengroepen (ivoor, champagne, subtiel blush), door de eigenaar aangeleverd (gemaakt met een beeldgenerator, witte achtergrond). `maak_rozen_vrij.py <rozen-1.png> <rozen-2.png>` haalt ze vrij (`static/img/site/rozen-groot.webp`, `rozen-klein.webp`; vraagt scipy, alleen voor dit gereedschap). `maak_op_maat_gouden_avond.py` plaatst de grote groep linksonder (voor de envelop) en de kleine groep rechts (deels achter de envelop), met zachte contactschaduwen op de sokkel. De bladschaduwen en sokkel blijven.

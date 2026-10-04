# Beeld bij "Jullie verhaal verdient iets bijzonders" (homepage)

Bestanden: `static/img/site/op-maat.webp` (1100x800), `op-maat-700.webp` (700x509) en `op-maat-mobiel.webp` (700x640), allemaal met doorzichtige achtergrond.
De oudere `maatwerk*.webp` blijven bestaan maar worden niet meer gebruikt door `core/templates/core/home.html`.

Het beeld is geen tekening maar de echte envelop-engine van VAYLIDE (Signature Ivory, `templates/partials/envelop/collectie.html`) met een eigen kaart:

1. `maatwerk-kaart.css` zet de kaart staand, groot en op de voorgrond en bevat de opmaak van de voorbeeldkaart (gouden folie-monogram "S&D", dubbel kader met hoekdetails, fotoboog "Jouw foto", quote, label "Voorbeeld op maat"). De envelop krijgt een iets dieper champagnepapier.
2. Die opmaak wordt in de labpagina (`/lab/enveloppen/?stijl=signature&zegel=champagne-monogram&monogram=S%26D`, alleen met DEBUG) in de kaart gezet, het zegel breekt en de envelop gaat open; een schermafbeelding met doorzichtige achtergrond (`voorvertoning-op-maat/open.png`, 2x) is de basis.
3. `maatwerk-op-maat.html` (`?v=d` of `?v=m`) voegt de gloed, schaduw, de twee takjes (uit `designs/silk-reveal/v1/img/takje.webp`), een kleine voorbeeldfoto en het hangertje met koordje aan het zegel toe. De foto is de aangeleverde Balzaal-scène met het fictieve bruidspaar (`designs/balzaal/v1/img/scene-bruin-blond.webp`), in een boogvormige lijst met gouden randje, warm getint (verzadiging -16%, sepia 12%) en bewust kleiner dan de kaart; een echte foto vervangt hem door de `background`-url van `.foto` te wijzigen. Schermafbeelding van `#stage` met doorzichtige achtergrond, daarna naar WebP (kwaliteit 88, alfa 92).

Vereist: de ontwikkelserver (`manage.py runserver`, voor de lettertypen en de lab-pagina) en een tweede eenvoudige server voor de map (`python -m http.server 8765`), en Playwright of een andere browser met "negeer CSP" voor de schermafbeeldingen.

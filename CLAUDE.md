# Vaylide: werkafspraken voor Claude

Vaylide is een Django-platform (Django 5.2 LTS, Python 3.11+) waarop klanten zelf een digitale uitnodiging samenstellen, betalen en delen, met aanmelden voor gasten (RSVP), een klantomgeving (Mijn Vaylide) en een beheeromgeving voor de eigenaar. Alle teksten voor gebruikers zijn Nederlands: kort, vriendelijk en zonder jargon.

Het merk heette eerst Vierlief (werknaam) en daarna kort Vaylide. Technische namen die bezoekers niet zien zijn bewust gebleven: de instellingen `VIERLIEF_…`, cookie-, sessie- en opslagnamen (`vierlief_…`, `vierlief-…`) en `static/css/vierlief.css`. Zie `docs/OVERDRACHT.md`.

Lees bij de start eerst `docs/OVERDRACHT.md` (stand van zaken en open punten). Daarna, als het nodig is: `docs/AANPAK.md` (keuzes en aannames), `docs/HANDLEIDING.md` (beheer, ontwerpen toevoegen), `docs/CONTROLES.md` (wat getest is), `docs/ONLINE.md` (op het eigen domein zetten) en `docs/LIVEGANG.md` (nodig voor livegang).

## Commando's

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                      # zet een eigen DJANGO_SECRET_KEY; geen echte sleutels in git
.venv/bin/python manage.py migrate        # leest ook de ontwerpen in (sync_designs)
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver      # http://127.0.0.1:8000, testmodus
.venv/bin/python manage.py test tests     # 452 tests, moeten altijd slagen
```

Visuele controles (Node met Playwright en Chromium): zie "Zelf herhalen" in `docs/CONTROLES.md` (`e2e/klantreis.cjs` voor de hele klantreis, `e2e/fixtures.py`, `e2e/controle2.cjs`, `e2e/toegankelijkheid.cjs` en `e2e/effecten.cjs`). Beelden opnieuw maken: `tools/logo/README.md` (logo en iconen), `tools/merkbeelden/README.md` (website), `tools/generate_demo_images.py` (voorbeeldbeelden), `tools/winterlicht/README.md` (de kerstkaart Winterlicht), `tools/gloria/maak_tekeningen.py` (vleugels en engelen van Gloria), `tools/aan_tafel/maak_tekeningen.py` (slinger en hulst van Aan tafel), `tools/voor_altijd/maak_tekeningen.py` (krans, takje en ringen van Voor altijd), `tools/eerste_dans/maak_tekeningen.py` (bruidspaar, kroonluchter en bloemenslinger van Eerste dans), `docs/BALZAAL.md` (beeldlagen en haarkleuren van Balzaal), `docs/GEZICHTEN.md` (eigen gezichten via een beeld-API; staat uit) en `e2e/make_design_images.cjs` (kaartbeelden van de ontwerpen). Een losse voorvertoning zonder server (om te delen): `python tools/voorvertoning.py <map> [ontwerp ...]`. De 3D-wereld op de homepage (voorbeeldkaart die omdraait, gouden kaart, sterretjes, kerstpodium) en de sterretjes in de paginakoppen: `static/js/hero3d.js` (omdraaien werkt altijd; beweging stilgezet bij 'minder beweging'). Themabeelden: `tools/merkbeelden/voorbeelden.cjs`.

## Waar zit wat

| Onderdeel | Plek |
|---|---|
| Websitepagina's | `core/views.py`, `core/templates/core/`, teksten in `core/content.py`, iconen in `core/icons.py` (`{% icon "naam" %}`), zoeken in `core/search.py` |
| Kop, voet, logo, iconen | `templates/partials/` (`logo.html`, `icons.html`); de bestanden komen uit `tools/logo/maak_logo.py` |
| Huisstijl | `static/css/vierlief.css` (tokens in `:root`), app-schermen in `static/css/app.css` |
| Uitnodigingsontwerpen | `designs/<code>/v<N>/` (manifest, template, stylesheet), weergave in `invitations/`. 30 ontwerpen delen de Atelier-opbouw in `designs/_atelier/v1/`; beschrijving en generator in `tools/atelier/`, keuzes en contrastcontrole in `catalog/atelier.py`. De kerstkaart Winterlicht (`designs/winterlicht/v1/`) heeft eigen getekende beelden uit `tools/winterlicht/` |
| Gelegenheden | `catalog/occasions.py`; bij Kerst is het evenement optioneel (alleen een kerstgroet kan ook), zie `event_expected` in `invitations/content.py` |
| Effecten op uitnodigingen | `invitations/static/invitations/effects.js` en `effects.css`; keuzes per ontwerp in het manifest (`effects`), opties en websiteteksten in `catalog/effects.py` |
| Samenstellen, bestellen, betalen | `studio/`, `orders/` (testbetaling en Mollie achter één koppeling). Foto's worden bij het uploaden automatisch uitgelijnd op gezichten (`invitations/focus.py`, YuNet-model in `invitations/models_ai/`, draait lokaal). Naast de invulstappen staat 'Je kaart, live' (`studio/templates/studio/_live.html`, views `live_update`/`live_frame`; in de kaart `invitations/static/invitations/live.js`) |
| Verwerking na betaling en e-mail | `processing/` (takenwachtrij met herhalingen) |
| Klantomgeving, extra wensen, beheer | `portal/`, `wishes/`, `beheer/` |
| Beveiligingsheaders en CSP | `core/middleware.py`, `core/csp.py` |
| Privacyverklaring | `core/templates/core/privacy.html`; feiten, aanbieders, cookies en open besluiten in `core/privacyverklaring.py` (in live-modus weigert `manage.py check` zolang er iets open staat). Zie `docs/PRIVACY.md` |
| Aanmelden (RSVP) | Extra vragen alleen uit de vaste, neutrale lijst in `invitations/vragen.py` (geen eigen vraagteksten; niet uitbreiden zonder beoordeling), controle in `invitations/rsvp.py`, tellen van oude eigen vragen: `manage.py rsvp_vragen_rapport` |

## Vaste regels van de eigenaar

Niet van afwijken zonder uitdrukkelijk akkoord van de eigenaar.

1. Beveilig klant- en beheerfuncties aan de serverzijde. Geheime sleutels nooit in de browser of de broncode, alleen via omgevingsvariabelen (`.env` staat in `.gitignore`).
2. Iedere klant heeft alleen toegang tot eigen gegevens, uploads en evenementen. Een moeilijk te raden link vervangt geen toegangscontrole. Een uitnodiging van een ander geeft een 404.
3. Gasten kunnen nooit andere antwoorden of de gastenlijst bekijken of opvragen.
4. Privé-uitnodigingen en gastenlijsten komen niet in zoekmachines (`noindex`, `robots.txt`). Het zoeken op de site doorzoekt alleen openbare inhoud.
5. Ontbrekende koppelingen draaien in een herkenbare testmodus (testbalk). Presenteer browseropslag of een gesimuleerde betaling nooit als een werkende productiedienst.
6. Publiceer alleen na een geldige serverzijdige betalingsbevestiging, nooit omdat de klant op een bedankpagina komt.
7. AI zegt geen maatwerk, prijs, haalbaarheid of opleverdatum toe. Bij een extra wens krijgt de klant alleen een ontvangstbevestiging.
8. Geen verzonnen reviews, klantenaantallen of onbevestigde leveringsbeloften.
9. Sluit geen betaalde diensten af en publiceer niet naar productie zonder akkoord van de eigenaar. Configuratievoorbeelden zonder echte geheimen.
10. Claim alleen controles die echt zijn uitgevoerd, en claim nooit iets gezien te hebben wat je niet kon openen.
11. Vaste teksten op de homepage: de kop "Een bijzondere dag verdient een bijzondere uitnodiging." en de knoppen "Bekijk de ontwerpen" en "Maak jouw uitnodiging".
12. Het logo wordt gebruikt zoals de eigenaar het aanleverde: de V, VAYLIDE en de regel eronder samen, in dezelfde kleuren en verhoudingen. Niet opsplitsen, bijsnijden, hertekenen of de tekst aanpassen. Alleen het tabblad-icoon gebruikt de V uit het logo, omdat het hele logo op 16 tot 48 pixels niet leesbaar is. Uitzondering met akkoord van de eigenaar (29 september 2026): de V uit het logo staat als klein merkteken onderaan elke uitnodiging (`static/img/merk/vaylide-v.*`, uit `tools/logo/maak_logo.py`; niet hertekend of verkleurd).

## Werkwijze

- Elke nieuwe functie of wijziging krijgt een test in `tests/`; `manage.py test tests` moet slagen.
- Een uitnodigingsontwerp aanpassen gaat via een nieuwe versie (`designs/<code>/v2/`). Bestaande uitnodigingen blijven op hun eigen versie (zie `docs/HANDLEIDING.md`). Let op: `designs/_atelier/v1/` is gedeeld door 30 ontwerpen; wijzigingen daar na de livegang via `_atelier/v2`.
- Beweging en effecten: alles wat beweegt staat onder `.fx-motion` (niet bij 'minder beweging' of als de gast op 'Beweging' tikte), doorlopende animaties gebruiken `animation-play-state: var(--fx-play, running)`, deeltjes staan achter de tekst en er zijn geen flitsen (hoogstens één). Zie `docs/HANDLEIDING.md` onder "Effecten"; controleer met `e2e/effecten.cjs`.
- Nieuwe kleurvarianten: tekstkleuren minimaal 4,5:1 contrast (`palette_problems` in `catalog/atelier.py`; de tests controleren alle Atelier-kleurvarianten).
- Vormgeving: gebruik de tokens uit `static/css/vierlief.css`. Kleine tekst op een lichte achtergrond gebruikt `--accent-text` (contrast minstens 4,5:1), knoppen `--accent`.
- De Content-Security-Policy is streng: geen inline `<script>` of `<style>`-blokken (inline `style`-attributen mogen). JavaScript hoort in `static/js/`. Het enige inline script is het startscript uit `core/csp.py`, met een hash in de CSP.
- Pagina's werken ook zonder JavaScript; JavaScript is een verbetering.
- Na werk aan de vormgeving: controleer op 360, 390, 768 en 1366 pixels breed (`e2e/controle2.cjs`) en draai de toegankelijkheidscontrole (`e2e/toegankelijkheid.cjs` voor alle ontwerpen in alle kleuren). Uitleg in `docs/CONTROLES.md` onder "Zelf herhalen".
- Werk de documentatie bij bij elke wijziging. In `docs/CONTROLES.md` komen alleen controles die echt zijn uitgevoerd.

# Bescherming van eigen media

Stand 5 oktober 2026. Doel: de afbeeldingen, video's en kaartvoorbeelden van VAYLIDE zijn niet met één klik of sleepbeweging van de website te halen.
**Het is een drempel, geen slot.** Screenshots, schermopnames en het uitlezen van netwerkverkeer kunnen niet worden tegengehouden, en we beweren ook niet dat het wel kan.
Er is bewust geen "screenshotblokkade" en geen DRM gebouwd: dat werkt niet in een gewone browser en gaat ten koste van gewone bezoekers.

## Wat er gebeurt

| Laag | Waar | Wat het doet |
|---|---|---|
| Script | `static/js/media-bescherming.js`, geladen via `templates/base.html` en `invitations/.../base_invitation.html` | Geen contextmenu (rechtsklik, lang indrukken) op beschermde media, geen slepen (`dragstart`), `draggable="false"` op afbeeldingen. Bij `<video>`: `controlslist="nodownload noplaybackrate"`, `disablepictureinpicture`, `disableremoteplayback`. Nieuwe elementen die later in de pagina komen worden ook beschermd. |
| CSS | `static/css/vierlief.css`, `invitations/static/invitations/invite-base.css` | `-webkit-user-drag: none`, `-webkit-touch-callout: none` (lang indrukken op iOS) en `user-select: none` op onze beelden en video's. Een afbeelding **binnen een link** krijgt `pointer-events: none`: klik en linkmenu gaan naar de link, zonder "afbeelding opslaan". |
| Video | de vier ontwerpen met video (Kerstbol, Kerstkaart, Gouden Avond, Kerststad) | De kenmerken staan ook direct in de HTML; Balzaal krijgt ze via het script. Geen `controls`: er is geen speler met een downloadknop. |
| Hotlink | `core/middleware.py::MediaHotlinkMiddleware`, in `config/settings.py` **vóór** WhiteNoise | Een beeld of video met een Referer van een vreemde website krijgt 403. `Sec-Fetch-Site: cross-site` bij een afbeelding, video of iframe krijgt ook 403 (vangt wie de Referer onderdrukt). Eigen pagina's, geen Referer en het openen van het beeld via een link blijven werken. De goede antwoorden krijgen `Cross-Origin-Resource-Policy: same-site`. |

Beschermd zijn alleen `<img>`, `<video>` en `<svg><image>` uit `/static/` en alles binnen `[data-media-beschermd]`.
Buiten schot: alles binnen `[data-media-vrij]` en wat niet uit `/static/` komt, zoals de QR-code en foto's van klanten.
**Tekst blijft gewoon selecteerbaar en kopieerbaar**; er is geen `selectstart`-, `copy`- of toetsenbordblokkade.

### Welke bestanden vallen onder de hotlinkblokkade

Bestanden met extensie `webp`, `jpg`, `jpeg`, `png`, `gif`, `avif`, `mp4`, `webm` of `mp3` (de eigen track van een ontwerp) onder `/static/designs/`, `/static/img/designs/`, `/static/img/site/`, `/static/img/demo/` en `/static/img/envelop/`.
Het logo (`img/merk/`), de mailafbeeldingen (`img/mail/`), de deelbeelden (`og-*.jpg`), pictogrammen, CSS, scripts en lettertypen vallen er bewust buiten:
mailprogramma's in de browser (Outlook.com en dergelijke) sturen een Referer mee en zouden het logo in onze mails niet meer laten zien, en zoekmachines en deelkaarten halen deelbeelden zonder Referer op.
Een tweede domein hoort in `DJANGO_ALLOWED_HOSTS` of `VIERLIEF_BASE_URL`; die gelden als "eigen", met en zonder `www`.

## Geen masterbestanden in de interface

Er staan geen losse originelen in `static/` of `designs/`: de beelden zijn webp/jpg in webformaat (kleiner dan 600 kB) en de video's zijn korte mp4's van 1,2 tot 2,4 MB; alleen de video van Kerststad (20 s) is ±5,4 MB. De bron daarvan (71 MB) staat buiten Git.
Geen enkel sjabloon linkt naar een beeld of video om te downloaden (`tests/test_mediabescherming.py` bewaakt dat, ook voor een `download`-kenmerk op media).
De downloads die wel bestaan zijn bedoeld: de QR-code (PNG/SVG), het agendabestand (.ics) en de voorwaarden (PDF). Grote originelen en prompts blijven buiten Git (zie `docs/designs/README.md`).

## Wat nooit helemaal te blokkeren is

- **Screenshots en schermopnames**: het systeem van de bezoeker.
- **Netwerkverkeer**: wat de browser laadt, kan met de ontwikkelaarstools (of `curl`) worden opgeslagen. Een Referer is buiten een browser eenvoudig na te maken, dus de hotlinkcontrole stopt gewone insluiting op andere websites, geen gerichte download.
- **Ctrl+S, bronweergave, uitgeschakeld JavaScript**: bewust niet geblokkeerd. Dat zou gewone bezoekers hinderen en houdt niemand tegen die het echt wil.
- **Wat we zelf delen**: het deelbeeld (`og:image`) en de logo's in mails zijn bedoeld om gezien te worden.

Wat wel helpt tegen misbruik: een zichtbare herkomst (de VAYLIDE-handtekening, zie `docs/designs/README.md`), webformaten in plaats van masters en afspraken in de voorwaarden.

## Controleren

`tests/test_mediabescherming.py` (hotlink, scriptaanwezigheid, videokenmerken, geen downloadlinks). In de browser: rechtsklik op een kaartbeeld of video geeft geen menu,
rechtsklik op tekst wel; een kaart blijft aanklikbaar, een opening start en de video speelt.
Lokaal met `DJANGO_DEBUG=true` serveert `runserver` zelf de statische bestanden en komt de hotlinkcontrole er niet aan te pas: test die met `collectstatic` en `runserver --nostatic`.

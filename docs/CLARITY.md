# Microsoft Clarity (bezoekersanalyse)

Stand: 8 oktober 2026, branch `claude/clarity`. Alleen op staging; production (`render.yaml`) heeft geen Clarity-ID.

## Aan of uit

- `VIERLIEF_CLARITY_ID` (project-id, kleine letters en cijfers). Leeg = uit: geen script, geen toestemmingsbanner, geen link
  "Cookie-instellingen" en geen extra domeinen in de Content-Security-Policy. Staging: `yuemn2aqz1` (`render.staging.yaml`).
  Neemt Render de blueprint-waarde niet vanzelf over, zet hem dan in Render bij de dienst `vaylide-staging` → Environment.
- Twee projecten in Clarity, zodat testbezoeken en echte bezoekers niet door elkaar lopen: `yuemn2aqz1` (in Clarity "VAYLIDE") alleen
  voor staging en testen; `yui4h1kh8c` ("VAYLIDE Production", https://vaylide.nl) voor later op production. Beide Strict en bij
  beide staat Copilot (de AI-samenvattingen) uit, sinds 8 oktober 2026. Het production-ID staat nog nergens in Render.
- **De privacytekst over Clarity is goedgekeurd door de eigenaar op 8 oktober 2026** (`CLARITY_BESLUITEN["goedgekeurd"]` in
  `core/privacyverklaring.py`); de conceptmarkering is daarmee weg. Verandert de tekst inhoudelijk, zet de goedkeuring dan weer op `None`:
  dan is het weer een concept en start de live-modus niet met Clarity. Rol en bewaartermijn staan ingevuld uit de officiële FAQ van Clarity
  (learn.microsoft.com/clarity/faq: "GDPR-compliant as a data controller"; afspeelgegevens van opnames 30 dagen; klik- en heatmapgegevens, gelabelde en favoriete
  opnames en een willekeurige steekproef tot 9 maanden;
  opslag in Azure; EU-gebruikers contracteren met Microsoft Ireland Operations Limited, met SCC's naar Microsoft Corporation in de VS).
  Zolang daar iets leeg is, staat het in de open punten van de verklaring en weigert `manage.py check` (en dus `migrate` bij het
  starten) in live-modus. Production draait nu nog met `VIERLIEF_MODE=test`; daar is de enige rem dat er geen `VIERLIEF_CLARITY_ID` staat.

## Waar Clarity draait

`core/analytics.py: clarity_op_pagina` (één plek): homepage, Collectie en ontwerppagina's (`/ontwerpen/…`), Inspiratie, Prijzen, de pagina's Digitale uitnodiging maken (`/digitale-uitnodiging-maken/`), Digitale trouwkaarten (`/digitale-trouwkaarten/`), Digitale kerstkaarten (`/digitale-kerstkaarten/`), Digitale verjaardagsuitnodigingen (`/digitale-verjaardagsuitnodigingen/`) en Digitale zakelijke uitnodigingen (`/digitale-zakelijke-uitnodigingen/`) en de
Studio (`/maken/…`, tot en met Bestellen en de stap Controleer). Nooit: `/u/…` (uitnodigingen), `/account/` (Mijn VAYLIDE en
gastenlijsten), `/inloggen/`, `/beheer/`, de Django-admin, `/betalen/`, `/bestelling/`, de voorbeelden van ontwerpen (`/voorbeeld/…`)
en de kaart in het frame van de Studio (`…/voorbeeld/weergave/`, `…/voorbeeld/live/`). De extra CSP-domeinen gelden alleen op de pagina's
waar Clarity mag draaien: `script-src https://www.clarity.ms https://*.clarity.ms`, `connect-src https://*.clarity.ms https://c.bing.com`,
`img-src https://*.clarity.ms https://c.bing.com` (volgens learn.microsoft.com/clarity/setup-and-installation/clarity-csp).

## Toestemming

`templates/partials/toestemming.html` en `static/js/toestemming.js`. De banner verschijnt alleen op pagina's waar Clarity mag draaien en
alleen als er nog geen keuze is; Accepteren en Weigeren zijn gelijkwaardige knoppen. De keuze staat in de noodzakelijke cookie
`vaylide_analytics` (`ja` of `nee`, 12 maanden, `SameSite=Lax`, `Secure` op https). "Cookie-instellingen" onderaan elke pagina opent de
banner opnieuw.

- **Accepteren**: Clarity laadt één keer (asynchroon, `async`), met vóór het eerste gegeven
  `clarity("consentv2", {ad_Storage: "denied", analytics_Storage: "granted"})`.
- **Weigeren** of geen keuze: Clarity laadt niet. Geen script, geen Clarity-cookies, geen cookieloze meting.
- **Intrekken** (eerst ja, daarna Weigeren), als Clarity op de pagina geladen was (`stopClarity` in `toestemming.js`):
  1. een extra CSP-regel `connect-src 'self'` via een meta-tag: vanaf dat moment blokkeert de browser elk verzoek van deze pagina naar Clarity;
  2. `consentv2` met beide op `denied`: Clarity wist `_clck`/`_clsk` en stopt;
  3. de herstart die Clarity daarna zelf plant, annuleren;
  4. `_clck` en `_clsk` ook zelf wissen, dan pas de pagina opnieuw laden, zonder Clarity.

  Waarom: bij `consentv2` 'denied' doet Clarity `stop()` (met een laatste pakket via `sendBeacon`) en daarna
  `window.setTimeout(start, 250)`. Die herstart draait zonder cookies, met een nieuw bezoekers- en sessie-ID, en stuurt bij het herladen
  een eigen sessie van ongeveer een seconde (clarity-js `data/metadata.ts`, functie `consentv2`; live 0.8.72-beta). Op staging gaf dat op
  8 oktober een extra sessie van 1 seconde op /prijzen/. Na de oplossing gaat er na het intrekken niets meer naar Clarity
  (`e2e/clarity_intrekken.cjs`, met het echte script, in Chromium, Firefox en WebKit). In de console staat dan één melding dat de browser
  Clarity's laatste pakket heeft geblokkeerd; dat is de bedoeling.
  Cookies die Microsoft op zijn eigen domeinen zette (MUID e.d.) kan de site niet wissen.

## Afschermen (masking)

- In de templates `data-clarity-mask="True"`: alles van een concept in de Studio (formulieren, live kaart, voorvertoning, Controleer,
  Bestellen; `studio/templates/studio/base_studio.html`), de lijst "Verder met je ontwerp?" en het e-mailadres op de startpagina,
  meldingen bovenaan (`templates/base.html`).
- Bij het laden zet `toestemming.js` het attribuut ook op elk `form`, `input`, `textarea`, `select`, `iframe`, `[data-gevoelig]` en de
  meldingen van de pagina. Invoervelden en keuzelijsten schermt Clarity in elke stand al af.
- Zet in het Clarity-dashboard Settings → Masking op **Strict**: dan is alle tekst afgeschermd en blijven klikken, scrollen, heatmaps en
  pagina's zichtbaar. De attributen hierboven blijven gelden (een element met `data-clarity-mask` wordt nooit zichtbaar, ook niet in
  een lossere stand).
- Clarity neemt ook de kaders met de kaart in de Studio mee (live kaart en Controleer; zelfde domein). Hun inhoud is afgeschermd, maar
  hun `<title>` niet. Daarom heeft elk voorbeeld in de Studio de titel "Voorbeeld · VAYLIDE" (`invitations/render.py: STUDIO_TITEL`,
  `RenderOptions.studio`, gezet in `studio/views.py: _preview_options`). De echte uitnodiging `/u/…` (zonder Clarity) houdt de titel
  met namen. Gevonden op 8 oktober 2026 door de echte pakketten van staging uit te pakken.

## Adressen van pagina's

Clarity leest het adres zelf uit `location.href` (bij elke pagina en elk pakket) en de vorige pagina uit `document.referrer`. Alleen
queryparameters kan Clarity weglaten (de instelling `drop`); voor het pad bestaat niets. Het concept-ID in `/maken/<uuid>/…` gaat dus
mee, tenzij het echte adres verandert. Dat doen we niet. Het ID is willekeurig en geeft zonder de browsersessie of het account geen
toegang (`invitations/access.py: can_access`). Paginatitels gaan ook mee; daarin staan geen namen.

## Controleren

- Tests: `tests/test_clarity.py`. Browser: `e2e/clarity_toestemming.cjs` (onderschept clarity.ms; er gaat niets naar Microsoft).
  Met het echte script (lokale kopie, alles onderschept): `e2e/clarity_intrekken.cjs` (na Weigeren niets meer) en
  `e2e/clarity_studio_pakketten.cjs` (pakt de pakketten uit en zoekt de ingevulde testwaarden; die mogen er niet in staan).
- Clarity zet sessies uit een geautomatiseerde browser apart als bot en toont daar geen opname van. Controleer masking daarom op de
  pakketten zelf (onderscheppen en uitpakken); een opname bekijken kan alleen van een sessie die een mens doorloopt.
- Eerste sessie: open staging (met het previewwachtwoord), kies Accepteren en klik wat rond. In het Clarity-dashboard (project
  `yuemn2aqz1`) verschijnt de sessie meestal binnen een paar minuten onder Recordings; Dashboard en Heatmaps volgen later (tot ongeveer
  een uur). In de browser: Network → een verzoek naar `www.clarity.ms/tag/yuemn2aqz1` en daarna `…clarity.ms/collect`.

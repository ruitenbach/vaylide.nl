# Microsoft Clarity (bezoekersanalyse)

Stand: 8 oktober 2026, branch `claude/clarity`. Alleen op staging; production (`render.yaml`) heeft geen Clarity-ID.

## Aan of uit

- `VIERLIEF_CLARITY_ID` (project-id, kleine letters en cijfers). Leeg = uit: geen script, geen toestemmingsbanner, geen link
  "Cookie-instellingen" en geen extra domeinen in de Content-Security-Policy. Staging: `yuemn2aqz1` (`render.staging.yaml`).
  Neemt Render de blueprint-waarde niet vanzelf over, zet hem dan in Render bij de dienst `vaylide-staging` → Environment.
- **Live start niet met Clarity zolang de privacytekst een open besluit is**: `CLARITY_BESLUITEN` in `core/privacyverklaring.py`
  (goedkeuring, rol van Microsoft, bewaartermijn). Zolang daar iets leeg is, staat het in de open punten van de verklaring en weigert
  `manage.py check` (en dus `migrate` bij het starten) in live-modus.

## Waar Clarity draait

`core/analytics.py: clarity_op_pagina` (één plek): homepage, Collectie en ontwerppagina's (`/ontwerpen/…`), Inspiratie, Prijzen en de
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
- **Intrekken** (eerst ja, daarna Weigeren): als Clarity op de pagina geladen was `consentv2` met beide op `denied` (Clarity wist dan zijn
  cookies en beëindigt de sessie), daarna wissen we `_clck` en `_clsk` zelf en laadt de pagina opnieuw, zonder Clarity.
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

## Controleren

- Tests: `tests/test_clarity.py`. Browser: `e2e/clarity_toestemming.cjs` (onderschept clarity.ms; er gaat niets naar Microsoft).
- Eerste sessie: open staging (met het previewwachtwoord), kies Accepteren en klik wat rond. In het Clarity-dashboard (project
  `yuemn2aqz1`) verschijnt de sessie meestal binnen een paar minuten onder Recordings; Dashboard en Heatmaps volgen later (tot ongeveer
  een uur). In de browser: Network → een verzoek naar `www.clarity.ms/tag/yuemn2aqz1` en daarna `…clarity.ms/collect`.

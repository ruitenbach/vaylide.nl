# Google Analytics 4 via Google Tag Manager

Bezoekersanalyse van Google, **alleen na toestemming** en alleen op staging tot de eigenaar akkoord geeft voor productie. Staat naast Microsoft Clarity
(`docs/CLARITY.md`) en gebruikt dezelfde toestemming (cookie `vaylide_analytics`, banner en link *Cookie-instellingen*).

## Gegevens (10 oktober 2026)

| Wat | Waarde |
|---|---|
| Google Analytics-account / property | `VAYLIDE` (account `411400084`, property `558301519`) |
| Webstream | `VAYLIDE`, `https://vaylide.nl`, stream-ID `16098555530` |
| GA4 Measurement ID | `G-80DM1Z9L7F` |
| Tag Manager-account / container | `VAYLIDE` (account `6381649927`, container `266637518`), type Web |
| GTM Container ID | `GTM-M8N863VG` |
| Instelling in de site | omgevingsvariabele `VIERLIEF_GTM_ID=GTM-M8N863VG` (leeg of ontbrekend = uit), `VIERLIEF_ANALYTICS_OMGEVING=staging` (standaard `productie`) |

De site laadt alleen de container. Het Measurement ID staat in de container (de Google-tag), niet in de code.

## Hoe het werkt

1. **Zonder keuze of na Weigeren** gebeurt er niets: geen script, geen verzoek naar Google, geen cookie, geen datalaag (`window.dataLayer` bestaat niet).
2. **Na Accepteren** (`static/js/toestemming.js`, `laadGtm()`), één keer per pagina, in deze volgorde:
   1. `consent default`: `analytics_storage: granted`, `ad_storage`, `ad_user_data` en `ad_personalization`: `denied` (Consent Mode v2: wel meten, geen advertenties).
   2. Eén object met de schone paginalocatie (`pagina_url`), de schone verwijzer (`pagina_ref`), `omgeving` en, buiten productie, `debug: true`.
   3. `gtm.start` en het script `https://www.googletagmanager.com/gtm.js?id=GTM-…` (asynchroon).
   4. De gebeurtenissen van deze pagina (zie hieronder).
3. **Intrekken of Weigeren na eerder Accepteren:** direct een extra CSP-regel (`connect-src 'self'; img-src 'self' data: blob:`), Clarity `consentv2` denied,
   Google `consent update` denied, de Google-cookies op deze site wissen (`_ga`, `_ga_<ID>`, `_gid`, `_gat*`, `_gcl_*`, `_gac_*`) en de pagina opnieuw laden zonder Google.
   Er gaat daarna niets meer naar Google, ook niet van de pagina waarop je intrekt.

### Waar het draait (`core/analytics.py`)

Op dezelfde pagina's als Clarity (homepage, Collectie en ontwerppagina's, Inspiratie, Prijzen, Digitale uitnodiging maken, Digitale trouwkaarten, Digitale kerstkaarten, Digitale verjaardagsuitnodigingen, Digitale zakelijke uitnodigingen, de Studio tot en met Bestellen) en daarnaast op **de bevestiging van een
bestelling** (`/bestelling/<id>/`, alleen daar voor `purchase_success`; Clarity draait er nooit). Nooit op uitnodigingen (`/u/…`), Mijn VAYLIDE, inloggen, beheer,
betalen, voorbeelden van ontwerpen en kaartframes. De CSP krijgt de Google-bronnen alleen op die pagina's.

### Geen persoonsgegevens

* `page_location`: eigen adres, pad **zonder id's** (`/maken/<uuid>/gegevens/` wordt `/maken/:id/gegevens/`, `/bestelling/<uuid>/` wordt `/bestelling/:id/`) en van de query alleen
  `gelegenheid` en `ontwerp` met een vaste vorm. `page_referrer`: zonder query en binnen de site zonder id's. **De paginatitel (`dt`, `page_title`) gaat wel mee**: de Google-tag stuurt hem automatisch mee en wij sturen hem niet apart weg. De titels zijn generiek (bijvoorbeeld `Gegevens · VAYLIDE`, `Bestellen · VAYLIDE`,
  `Collectie digitale uitnodigingen · VAYLIDE`), er staat geen tekst van de klant in. **Uitzondering, opgeschoond:** de zichtbare titel van de bevestigingspagina bevat het bestelnummer; daar krijgt Google
  de vaste titel `Bestelling bevestigd · VAYLIDE` (datalaag `pagina_titel`, in de Google-tag als `page_title`) en geen verwijzer (`pagina_ref` leeg; een verwijzer van `/betalen/…` of van de betaalprovider kan een
  betaalreferentie bevatten). Er wordt verder niets uit de pagina gelezen en Enhanced Measurement staat zonder zoeken, formulieren en
  geschiedeniswijzigingen (zie hieronder).
* De gebeurtenissen hebben alleen openbare waarden: `design` (slug van het ontwerp), `occasion` (gelegenheid), `package` (pakketcode), `value` en `currency`. Geen namen, e-mail, telefoon,
  adressen, kaartteksten, RSVP-inhoud, bestelnummer of order-id.
* Studio-gebeurtenissen komen uit **serverstatus**, niet uit teksten op de pagina: de server zet ze in de sessie (`core/analytics.py`) of leidt ze af uit de route, en toont ze op
  de eerstvolgende pagina waar meten mag in `data-gtm-events`. Eenmalig per concept en sessie waar dat past.

## Gebeurtenissen

| Gebeurtenis | Wanneer | Bron in de code | Parameters |
|---|---|---|---|
| `page_view` | één keer per pagina | de Google-tag (GA4 Configuration, `send_page_view` standaard) | schone `page_location`, `page_referrer`, `environment` |
| `view_collection` | de Collectie (`/ontwerpen/`) wordt geopend, elke keer | route `core:designs` (`pagina_gebeurtenis`) | geen |
| `select_design` | een ontwerp is gekozen op *Kies kaart* (POST) | `studio.views.start` | `design`, `occasion` |
| `start_studio` | eerste keer in Personaliseren (stap Gegevens) per concept en sessie | `studio.views.step` → `studiostap_bekeken` | `design`, `occasion` |
| `reach_checkout` | eerste keer bij de stap Bestellen per concept en sessie | idem | `design`, `occasion`, `package` (als gekozen) |
| `purchase_success` | de bevestigingspagina van een **betaalde** bestelling (`order.status == paid`, bevestigd door de betaalprovider), eenmaal per bestelling en sessie | `orders.views.status` → `bestelling_betaald` | `design`, `occasion`, `package`, `value`, `currency` (EUR; GA4 stuurt dit als `cu`) |

Alle events hebben bovendien `environment` (`productie` of `staging`).

## De GTM-container

Het bestand `docs/gtm/vaylide-container.json` bevat de volledige configuratie (importeren via *Beheer → Container importeren → Samenvoegen*):

* **Variabelen** (Data Layer Variable, versie 2): `DLV pagina_url`, `DLV pagina_ref`, `DLV pagina_titel`, `DLV omgeving`, `DLV debug`, `DLV design`, `DLV occasion`, `DLV package`, `DLV value`, `DLV currency`.
* **Triggers** (Aangepaste gebeurtenis, exacte naam): `Event view_collection`, `Event select_design`, `Event start_studio`, `Event reach_checkout`, `Event purchase_success`.
* **Tags:**
  * `Google-tag G-80DM1Z9L7F` (type Google-tag): trigger *Initialization – All Pages*; configuratie `page_location = {{DLV pagina_url}}`, `page_referrer = {{DLV pagina_ref}}`,
    `page_title = {{DLV pagina_titel}}` (alleen gevuld op de bevestiging), `environment = {{DLV omgeving}}`, `debug_mode = {{DLV debug}}`. Dit stuurt de ene `page_view`.
  * Vijf tags `GA4 event <naam>` (type GA4-gebeurtenis, Measurement ID `G-80DM1Z9L7F`) met de bijbehorende trigger en parameters uit de tabel.
* Geen selectors op teksten of knoppen, geen Custom HTML-tags, geen advertentietags.

**Testverkeer.** Alles buiten productie meldt `debug_mode: true`. In GA4 zijn de gegevens daarom niet in de gewone rapporten te zien (alleen in *DebugView*) zolang het datafilter
*Testverkeer debug mode* (type Ontwikkelaarsverkeer, uitsluiten, actief; *Beheer → Gegevensfilters*) aan staat. Gebeurtenissen met `debug_mode` worden daarbij definitief niet verwerkt. Op productie staat `debug` niet aan en telt alles gewoon mee.

## Enhanced Measurement (GA4-webstream)

Aan: paginaweergaven, scrollen, uitgaande klikken, video-engagement, bestandsdownloads. **Uit** (bewust): *Zoeken op de site* (zoektermen), *Formulierinteracties* en
*Wijzigingen van de pagina op basis van de browsergeschiedenis*. De laatste zou naast onze eigen `page_view` extra weergaven geven: de site gebruikt `history.replaceState`
(kleur en soort op de ontwerppagina's).

## Privacyverklaring

`core/templates/core/privacy.html` en `core/privacyverklaring.py` bevatten de tekst over Google Analytics en Google Tag Manager (onderdelen 3, 6, 7, 9, 10) en de cookies `_ga`
en `_ga_…`; ze verschijnen alleen als `VIERLIEF_GTM_ID` is ingesteld. **De tekst is door de eigenaar goedgekeurd op 10 oktober 2026**
(`GOOGLE_TEKST_GOEDGEKEURD = True`); daarmee staat de conceptmarkering er niet meer en is het geen open punt meer voor live-modus. Verandert de tekst inhoudelijk, zet de vlag dan weer op
`False`. Bewaartermijnen volgens de GA4-instelling: gebeurtenisgegevens 2 maanden, gebruikersgegevens 14 maanden.

## Productie

`VIERLIEF_GTM_ID=GTM-M8N863VG` en `VIERLIEF_ANALYTICS_OMGEVING=productie` (let op: de code kent `productie`, niet `production`; elke andere waarde dan `productie` meet als testverkeer met `debug_mode` en valt
dan uit de rapporten) staan in het Render-dashboard van de dienst `vaylide`, net als `VIERLIEF_CLARITY_ID`.

## Controleren

* `tests/test_gtm.py`: zonder id niets; paginaregels; CSP; schone locatie; events en dedupe; `purchase_success` alleen bij betaald; het script (volgorde, intrekken); privacytekst.
* `e2e/gtm_toestemming.cjs` (Chrome): zonder keuze en na Weigeren geen verkeer; na Accepteren eenmaal laden met de juiste volgorde en schone gegevens; Studio-gebeurtenissen; intrekken;
  pagina's waar niet gemeten mag worden. Het script van Google wordt daarin nagebootst.
* Op staging met de echte container: zie `docs/CONTROLES.md`.

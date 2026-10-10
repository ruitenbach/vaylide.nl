# Vindbaarheid (SEO) van VAYLIDE

Stand 4 oktober 2026. Alles staat in `core/seo.py`, `templates/base.html` en de drie sjablonen `core/home.html`, `core/designs.html` en `core/design_detail.html`.
Tests: `tests/test_seo.py` (gericht, geen volledige suite nodig).

## Wat er is

| Onderdeel | Hoe |
|---|---|
| Titel en beschrijving | Elke publieke pagina heeft een eigen titel (met ` · VAYLIDE`) en een beschrijving van 70 tot 160 tekens. Homepage: "Digitale uitnodigingen die je beleeft". |
| Canonical | Standaard het pad zonder query. Een gelegenheidspagina (`/ontwerpen/?gelegenheid=kerst`) heeft een eigen canonical; een onbekende gelegenheid valt terug op `/ontwerpen/`; kleur- en gelegenheidsvarianten van een ontwerppagina wijzen naar de ontwerppagina zelf. |
| Open Graph en Twitter | `og:url`, `og:locale`, `og:title`, `og:description`, `og:image` (met afmetingen en alt) en `twitter:card` op elke publieke pagina. Op ontwerppagina's is de afbeelding het kaartbeeld van het ontwerp (kaart `summary`), elders het standaardbeeld (kaart `summary_large_image`). |
| Gestructureerde gegevens | `Organization` (naam, url, logo en `sameAs` met de vier officiële profielen) en `WebSite` op de homepage; `BreadcrumbList` op de collectie, de gelegenheidspagina's en de ontwerppagina's. Bewust geen reviews, beoordelingen, prijzen, adressen of andere bedrijfsgegevens. |
| Teksten per gelegenheid | `OCCASION_SEO` in `core/seo.py`, voor elke gelegenheid die ook in de catalogus staat. De zichtbare koppen op de pagina zijn niet veranderd. |
| Ontwerppagina's | Titel "{naam}, digitale uitnodiging" (kerstontwerpen: "digitale kerstkaart"), beschrijving uit de eigen ondertitel van het ontwerp (`design_description`). |
| Landingspagina Digitale trouwkaarten | `/digitale-trouwkaarten/` (`core.views.wedding_cards`, template `core/trouwkaarten.html`): eigen titel, beschrijving, H1, self-canonical, `BreadcrumbList` en `FAQPage` (dezelfde vragen staan zichtbaar op de pagina). Het filter `/ontwerpen/?gelegenheid=bruiloft` werkt gewoon in de site, maar zijn canonical is deze pagina en hij staat niet in de sitemap. Gelinkt vanaf de homepage ("digitale trouwkaarten") en vanaf elk ontwerp dat bij de bruiloft hoort. Staat in de lijst van pagina's waar Clarity en GA4 (met toestemming) mogen draaien. |
| Landingspagina Digitale kerstkaarten | `/digitale-kerstkaarten/` (`core.views.christmas_cards`, template `core/kerstkaarten.html`): zelfde opzet als Digitale trouwkaarten (self-canonical, `BreadcrumbList`, `FAQPage`), maar met een eigen warme kerststijl en eigen inhoud. Het filter `/ontwerpen/?gelegenheid=kerst` werkt gewoon, heeft deze pagina als canonical en staat niet in de sitemap. Gelinkt vanaf de homepage (kerstpodium) en vanaf elk kerstontwerp; zelfde Clarity/GA4-lijst. `GELEGENHEID_HUBS` in `core/views.py` is de ene plek voor filter naar landingspagina. |
| Landingspagina Digitale verjaardagsuitnodigingen | `/digitale-verjaardagsuitnodigingen/` (`core.views.birthday_invitations`, template `core/verjaardagsuitnodigingen.html`): eigen opzet en stijl, self-canonical, `BreadcrumbList`, `FAQPage`. Het filter `/ontwerpen/?gelegenheid=verjaardag` werkt gewoon, heeft deze pagina als canonical en staat niet in de sitemap (`GELEGENHEID_HUBS`). Gelinkt vanaf de homepage en, samen met de andere landingspagina's, vanaf elk ontwerp dat bij de gelegenheid hoort (`HUB_LINKS`); zelfde Clarity/GA4-lijst. |
| Landingspagina Digitale zakelijke uitnodigingen | `/digitale-zakelijke-uitnodigingen/` (`core.views.business_invitations`, template `core/zakelijke_uitnodigingen.html`): eigen, zakelijke opzet en stijl, self-canonical, `BreadcrumbList`, `FAQPage`. Het filter `/ontwerpen/?gelegenheid=zakelijk` werkt gewoon, heeft deze pagina als canonical en staat niet in de sitemap (`GELEGENHEID_HUBS`). Gelinkt vanaf de homepage en via de combinatieregel (`HUB_LINKS`) vanaf elk zakelijk ontwerp; zelfde Clarity/GA4-lijst. |
| Landingspagina Digitale uitnodiging maken | `/digitale-uitnodiging-maken/` (`core.views.make_invitation`, template `core/uitnodiging_maken.html`): de brede instappagina voor "digitale uitnodiging maken" met vier routes naar de landingspagina's per gelegenheid; self-canonical, `BreadcrumbList`, `FAQPage`. Staat in de sitemap en op de Clarity/GA4-lijst. Gelinkt vanaf de homepage, `/zo-werkt-het/` (één regel onder de inleiding) en `/ontwerpen/` (één regel onder de inleiding); de homepage blijft de merkpagina en `/zo-werkt-het/` de uitlegpagina, canonicals ongewijzigd. |
| Sitemap | Publieke pagina's, Digitale uitnodiging maken, de vier landingspagina's (trouw, kerst, verjaardag, zakelijk), elke andere gelegenheid met ontwerpen en elk zichtbaar ontwerp (het bruiloft-, kerst-, verjaardags- en zakelijke filter niet). Geen voorbeeld-, uitnodigings-, studio- of accountpagina's en geen verborgen (C) ontwerpen. |
| robots.txt | Production: alles open behalve de privégedeelten, met verwijzing naar de sitemap. Met een previewwachtwoord (staging): `Disallow: /`. |
| noindex | `X-Robots-Tag: noindex` op de privégedeelten (`/u/`, `/voorbeeld/`, `/account/`, `/maken/`, `/bestelling/`, `/betalen/`, `/inloggen/`, beheer) en op de kopieën van de voorwaarden (`/voorwaarden/versie|download|pdf/…`). Met een previewwachtwoord op elke pagina. Zoekresultaten: `noindex, follow`. |

## Staging versus production

Staging heeft `VIERLIEF_PREVIEW_PASSWORD`: elke pagina vraagt een wachtwoord (401), antwoordt met `noindex, nofollow, noarchive` en `robots.txt` zegt `Disallow: /`.
Production heeft dat niet en blijft indexeerbaar. De basis-url voor canonical, Open Graph en sitemap is `VIERLIEF_BASE_URL`.

## Sociale profielen (`sameAs` en voettekst)

De vier officiële profielen staan op één plek: `core/social.py` (Instagram, Facebook, TikTok, LinkedIn). De voettekst en `sameAs` in de `Organization`-gegevens lezen dezelfde lijst, dus ze kunnen niet uit elkaar lopen. Een profiel erbij of eraf: alleen daar aanpassen. Uitsluitend echte, door de eigenaar opgegeven profielen.

De iconen in de voettekst zijn de officiële merktekens in hun eigen kleuren (Instagram-gradient, Facebook-blauw, TikTok-multicolor, LinkedIn-blauw), door de eigenaar aangeleverd en alleen bijgesneden en verkleind tot 96 × 96 px (`static/img/social/`); vorm, verhouding en kleur zijn niet aangepast. Op de pagina staan ze alle vier op 28 px in de ronde VAYLIDE-knop.

## Bewust niet gedaan

Geen `lastmod` in de sitemap (geen betrouwbare wijzigingsdatum), geen `Product`/`Offer` (prijzen horen niet in gestructureerde gegevens zolang ze voorlopig zijn),
geen `contactPoint` (geen vastgelegde bedrijfsgegevens), geen zoekfunctie in `WebSite`.

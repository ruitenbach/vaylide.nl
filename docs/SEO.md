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
| Sitemap | Publieke pagina's, elke gelegenheid met ontwerpen en elk zichtbaar ontwerp. Geen voorbeeld-, uitnodigings-, studio- of accountpagina's en geen verborgen (C) ontwerpen. |
| robots.txt | Production: alles open behalve de privégedeelten, met verwijzing naar de sitemap. Met een previewwachtwoord (staging): `Disallow: /`. |
| noindex | `X-Robots-Tag: noindex` op de privégedeelten (`/u/`, `/voorbeeld/`, `/account/`, `/maken/`, `/bestelling/`, `/betalen/`, `/inloggen/`, beheer) en op de kopieën van de voorwaarden (`/voorwaarden/versie|download|pdf/…`). Met een previewwachtwoord op elke pagina. Zoekresultaten: `noindex, follow`. |

## Staging versus production

Staging heeft `VIERLIEF_PREVIEW_PASSWORD`: elke pagina vraagt een wachtwoord (401), antwoordt met `noindex, nofollow, noarchive` en `robots.txt` zegt `Disallow: /`.
Production heeft dat niet en blijft indexeerbaar. De basis-url voor canonical, Open Graph en sitemap is `VIERLIEF_BASE_URL`.

## Sociale profielen (`sameAs` en voettekst)

De vier officiële profielen staan op één plek: `core/social.py` (Instagram, Facebook, TikTok, LinkedIn). De voettekst en `sameAs` in de `Organization`-gegevens lezen dezelfde lijst, dus ze kunnen niet uit elkaar lopen. Een profiel erbij of eraf: alleen daar aanpassen. Uitsluitend echte, door de eigenaar opgegeven profielen.

## Bewust niet gedaan

Geen `lastmod` in de sitemap (geen betrouwbare wijzigingsdatum), geen `Product`/`Offer` (prijzen horen niet in gestructureerde gegevens zolang ze voorlopig zijn),
geen `contactPoint` (geen vastgelegde bedrijfsgegevens), geen zoekfunctie in `WebSite`.

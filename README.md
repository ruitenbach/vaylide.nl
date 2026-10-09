# Vaylide

*Elk bijzonder moment begint met een uitnodiging.*

Vaylide is een platform waarop klanten zelf een persoonlijke digitale uitnodiging samenstellen, bestellen en delen: voor een bruiloft, verloving, verjaardag, jubileum, babyshower of zakelijk evenement. Standaardbestellingen lopen automatisch:

ontwerp kiezen → vragen invullen → foto's uploaden → voorbeeld controleren → betalen → automatische publicatie → delen → aanmeldingen beheren.

De eigenaar grijpt alleen in bij extra wensen, vragen en storingen.

Het project heette eerst "Vierlief" (werknaam) en daarna kort "Vaylide". Sinds ronde 6 heet het merk **Vaylide**, met het logo in `tools/logo/`. Technische namen die bezoekers niet zien, zoals de instellingen `VIERLIEF_…`, zijn bewust gebleven; zie [docs/OVERDRACHT.md](docs/OVERDRACHT.md).

> **Status: eerste versie in testmodus.** Betalingen zijn gesimuleerd, e-mails worden alleen bewaard (niet verstuurd) en de AI-hulp draait zonder sleutel met vaste voorbeeldteksten. Op elke pagina staat een testbalk. Wat nodig is om live te gaan: [docs/LIVEGANG.md](docs/LIVEGANG.md).

## Documentatie

Repository: https://github.com/bootsman075-ops/vaylide.nl


| Bestand | Inhoud |
|---|---|
| [docs/OVERDRACHT.md](docs/OVERDRACHT.md) | Stand van zaken, open punten en hoe je verder bouwt (begin hier) |
| [CLAUDE.md](CLAUDE.md) | Werkafspraken en vaste regels voor Claude Code |
| [docs/AANPAK.md](docs/AANPAK.md) | Aanpak, techniekkeuze, aannames en de status van de referenties |
| [docs/HANDLEIDING.md](docs/HANDLEIDING.md) | De beheeromgeving gebruiken en ontwerpen toevoegen of aanpassen |
| [docs/CONTROLES.md](docs/CONTROLES.md) | Uitgevoerde controles (Controle 1 en 2) met resultaten |
| [docs/LIVEGANG.md](docs/LIVEGANG.md) | Aansluitingen en keuzes die nodig zijn voor livegang |
| [docs/ONLINE.md](docs/ONLINE.md) | De site op je eigen domein zetten: eerst als afgeschermde testversie, daarna live |

## Lokaal starten (testmodus)

Nodig: Python 3.11 of nieuwer.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
# Zet in .env een eigen DJANGO_SECRET_KEY, bijvoorbeeld de uitvoer van:
#   .venv/bin/python -c "import secrets; print(secrets.token_urlsafe(50))"
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser   # je beheeraccount: e-mail + wachtwoord (min. 12 tekens)
.venv/bin/python manage.py runserver
```

Op Windows gebruik je `.venv\Scripts\python` in plaats van `.venv/bin/python`.

Open daarna http://127.0.0.1:8000.

| Wat | Waar |
|---|---|
| Website | `/` |
| Ontwerpen en werkende voorbeelden | `/ontwerpen/` (34 ontwerpen), en per ontwerp `/voorbeeld/<code>/`, bijvoorbeeld `/voorbeeld/liefde-op-papier/` of `/voorbeeld/sterrennacht/` |
| Zelf een uitnodiging maken | `/maken/` |
| Mijn Vaylide (klant) | `/account/` |
| Beheer (eigenaar) | `/beheer/`, inloggen met het account uit `createsuperuser` |

In testmodus:
- Het inlogscherm voor klanten toont de inlogcode direct op het scherm (er gaat geen e-mail uit).
- Na **Bestellen** kom je op een gesimuleerde betaalpagina en kies je zelf de uitkomst: betaald, mislukt, geannuleerd of verlopen.
- Alle e-mails staan in **Beheer → Verwerking**.

## Configuratie

Alle instellingen staan in omgevingsvariabelen. Kopieer `.env.example` naar `.env`; daar staat bij elke variabele een toelichting. `.env` staat in `.gitignore`. Zet nooit echte sleutels in de broncode of in GitHub.

| Variabele | Betekenis |
|---|---|
| `VIERLIEF_MODE` | `test` (standaard) of `live`. In `live` weigert de app te starten zonder echte betaalprovider, SMTP en https-adres. |
| `DJANGO_SECRET_KEY` | Lange willekeurige geheime sleutel (verplicht buiten ontwikkelmodus). |
| `DJANGO_DEBUG` | Alleen `true` bij lokaal ontwikkelen. |
| `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` | Domeinnamen van de site. |
| `VIERLIEF_BASE_URL` | Publiek adres zonder slash aan het eind, voor links in e-mails en QR-codes. |
| `DATABASE_URL` | Standaard SQLite in `data/`. Voor productie bij voorkeur PostgreSQL. |
| `VIERLIEF_DATA_DIR`, `VIERLIEF_UPLOAD_DIR` | Map voor gegevens en uploads (moet blijvend zijn en mag niet openbaar geserveerd worden). |
| `VIERLIEF_EMAIL_MODE` + `SMTP_*` | `outbox` (alleen bewaren) of `smtp` (echt versturen). |
| `VIERLIEF_PAYMENT_PROVIDER` + `MOLLIE_API_KEY` | `test` of `mollie`. |
| `ANTHROPIC_API_KEY`, `VIERLIEF_AI_MODEL`, `VIERLIEF_AI_ENABLED` | Optionele AI-hulp. Zonder sleutel werkt alles in testmodus. |
| `VIERLIEF_JOBS_INLINE`, `VIERLIEF_CRON_TOKEN` | Achtergrondtaken (zie hieronder). |
| `VIERLIEF_TRUSTED_PROXY_HOPS` | Aantal proxy's vóór de app (voor het juiste IP-adres bij misbruikbeperking). |
| `VIERLIEF_DJANGO_ADMIN_PATH` | Pad van het noodbeheer (Django admin); kies iets dat niet makkelijk te raden is. |
| `VIERLIEF_PREVIEW_PASSWORD`, `VIERLIEF_PREVIEW_USER` | Optioneel één wachtwoord voor de hele site, zolang een testversie online staat (zie [docs/ONLINE.md](docs/ONLINE.md)). |

Prijzen, pakketten, extra opties, beschikbaarheidsduur, bewaartermijnen en ontwerpen stel je in via **Beheer**, niet via code.

## Achtergrondtaken en onderhoud

- **Verwerking na betaling** (publiceren, e-mails) start direct na de betaling. Mislukt iets, dan probeert het systeem het opnieuw na 1 min, 5 min, 15 min, 1 uur, 3 uur en 12 uur. Daarna krijgt de eigenaar een melding en kan de taak in **Beheer → Verwerking** opnieuw gestart worden. Voor die herhalingen moet er iets periodiek draaien, op één van deze twee manieren:
  - een worker: `python manage.py process_jobs --loop`
  - of een externe cron die elke minuut `POST /intern/taken/` aanroept met de header `Authorization: Bearer <VIERLIEF_CRON_TOKEN>`
- **Bewaartermijnen** (dagelijks): `python manage.py apply_retention`. Dit zet verlopen uitnodigingen offline en verwijdert oude gastgegevens, oude concepten en oude inlogcodes, volgens de termijnen in **Beheer → Instellingen**.
- **Ontwerpen inlezen** na het toevoegen van een ontwerpmap: `python manage.py sync_designs`. Dit gebeurt ook automatisch bij `migrate`.

## Tests

```bash
.venv/bin/python manage.py test tests
```

148 geautomatiseerde tests voor de volledige klantreis, betalingen, verwerking, toegang, versies, aanmeldingen, extra wensen, uploads, weergave, alle ontwerpen met hun effecten, de websitepagina's (ook zoeken), het merk (logo, iconen, geen oude naam) en het wachtwoord voor een testversie online. Ze zijn gedraaid op SQLite; op PostgreSQL 16 en in de Docker-image in een eerdere ronde. De visuele controles met Playwright staan in `e2e/`; zie [docs/CONTROLES.md](docs/CONTROLES.md).

## Installeren op een server

Vereisten: https, een blijvende map voor uploads, een worker of cron voor de verwerking, de dagelijkse bewaartermijn-taak, SMTP en een Mollie-account. PostgreSQL wordt aanbevolen; SQLite volstaat alleen bij één server met weinig verkeer.

**Docker** (getest: bouwen, starten op een leeg volume en de tests in de container):

```bash
docker build -t vaylide .
docker run -d --name vaylide -p 8000:8000 --env-file .env.productie -v vaylide-data:/data vaylide
docker run -d --name vaylide-worker --env-file .env.productie -v vaylide-data:/data vaylide \
  python manage.py process_jobs --loop
```

Plaats een reverse proxy met https vóór de container en zet `VIERLIEF_TRUSTED_PROXY_HOPS=1`. Met SQLite moeten web en worker hetzelfde volume op dezelfde machine delen.

**Platforms met een Procfile**: `Procfile` bevat `release` (migraties), `web` (gunicorn) en `worker`.

**Render**: `render.yaml` zet de site als testversie met een wachtwoord op Render (Frankfurt), met een blijvende schijf en PostgreSQL. Stappen: [docs/ONLINE.md](docs/ONLINE.md). Lokaal nagebootst, nog niet op Render zelf getest.

Controleer na installatie met `python manage.py check --deploy`. Er horen dan alleen de bewust open gelaten meldingen W005 en W021 over HSTS-subdomeinen en de preload-lijst te staan.

## Projectstructuur

| Map | Inhoud |
|---|---|
| `config/` | Instellingen en URL's |
| `core/` | Website-pagina's (teksten in `core/content.py`, iconen in `core/icons.py`, zoeken in `core/search.py`), contact, beveiligingsheaders, AI-hulp, privacy en bewaartermijnen |
| `catalog/` | Ontwerpen en ontwerpversies, pakketten, opties, gelegenheden |
| `designs/<ontwerp>/v<N>/` | De uitnodigingsontwerpen: `manifest.json`, `invitation.html`, `style.css`. De 30 Atelier-ontwerpen delen hun opbouw in `designs/_atelier/v1/` |
| `invitations/static/invitations/effects.js`, `effects.css` | De effecten op de uitnodigingen (zwevende deeltjes, knal bij openen, feestje na aanmelden, knop 'Beweging'); keuzes per ontwerp in het manifest, opties in `catalog/effects.py` |
| `invitations/` | Uitnodigingen, versies, foto's, weergave, aanmeldingen van gasten, QR, agenda |
| `studio/` | Samenstellen in stappen (de vragenlijst) |
| `orders/` | Bestellen, prijsberekening, betaalproviders (test en Mollie), verwerking na betaling |
| `processing/` | Takenwachtrij met herhalingen en de e-mails |
| `wishes/` | Extra wensen en maatwerkvoorstellen |
| `portal/` | Mijn Vaylide (klantomgeving) |
| `beheer/` | Beheeromgeving voor de eigenaar |
| `accounts/` | Klantaccounts (inlogcode per e-mail) en beheerders |
| `tests/` | Geautomatiseerde tests |
| `e2e/` | Browsercontroles en scripts voor de afbeeldingen |
| `tools/` | Maakt de eigen beelden: abstracte voorbeeldafbeeldingen en (in `tools/merkbeelden/`) de sfeer- en deelbeelden van de website; in `tools/logo/` het logo zoals aangeleverd en het script voor de logobestanden en iconen; in `tools/atelier/` de beschrijving en het script voor de Atelier-ontwerpen |

## Beveiliging in het kort

- Toegang wordt altijd aan de serverzijde gecontroleerd. Een klant ziet alleen eigen uitnodigingen, bestellingen, uploads en aanvragen. Een uitnodiging van een ander geeft een 404.
- Gasten hebben geen account nodig en kunnen alleen hun eigen antwoord wijzigen, via een persoonlijke link en cookie. Andere antwoorden of de gastenlijst zijn nergens voor hen op te vragen.
- Uploads staan niet in een openbare map. Foto's worden alleen getoond als ze bij een gepubliceerde uitnodiging horen, en EXIF- en GPS-gegevens worden verwijderd.
- Privé-pagina's hebben `noindex` en staan uitgesloten in `robots.txt`.
- CSRF-bescherming, een strikte Content-Security-Policy, veilige cookies, een maximum aantal pogingen per IP-adres (rate limiting), een honeypot en een minimale invultijd op openbare formulieren.
- Betalingen gelden alleen na een serverzijdige statuscontrole bij de provider. Herhaalde meldingen worden veilig genegeerd.

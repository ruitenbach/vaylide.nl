# Staging: één vaste online testsite voor Vaylide

Doel: elke wijziging eerst online testen op een aparte, afgeschermde omgeving, vóór ze naar de live site gaat.
De stagingomgeving staat helemaal los van de live dienst `vaylide`, de live database `vaylide-db`, live Mollie en het domein vaylide.nl.

## Opzet

| Onderdeel | Staging | Live (blijft ongemoeid) |
|---|---|---|
| Webdienst | `vaylide-staging` | `vaylide` |
| Branch | `claude/envelop-collectie` | `claude/kerstkaarten-website-design-51mn9k` |
| Database | `vaylide-staging-db` (eigen Postgres) | `vaylide-db` |
| Schijf (foto's, uploads) | `vaylide-staging-gegevens` | `vaylide-gegevens` |
| Adres | `https://vaylide-staging.onrender.com` (staat in Render) | vaylide.nl |
| Modus | `test`: gesimuleerde betaling, mails alleen in de outbox | `live` |
| Afscherming | hele site achter het previewwachtwoord | geen |
| Cron-dienst | geen (taken lopen direct bij het opslaan) | `vaylide-taken` |

Alles staat in `render.staging.yaml`. Het bestand `render.yaml` (live) is niet gewijzigd.

## Eenmalig aanmaken in het Render-dashboard

1. Open **dashboard.render.com** en log in met hetzelfde account als de live site.
2. Klik rechtsboven op **New +** en kies **Blueprint**.
3. Kies de repository **`ruitenbach/vaylide.nl`** (dezelfde als de live dienst). Staat hij er niet bij, kies dan **Configure account** en geef Render toegang tot die repository.
4. Vul in:
   - **Blueprint Name:** `vaylide-staging`
   - **Branch:** `claude/envelop-collectie`
   - **Blueprint Path:** `render.staging.yaml`
5. Klik op **Continue**. Render laat nu zien wat er wordt aangemaakt.
6. **Controleer vóór je doorgaat:** er staan precies twee nieuwe onderdelen: webdienst `vaylide-staging` en database `vaylide-staging-db`. Zie je de namen `vaylide` of `vaylide-db`, of een melding dat er bestaande onderdelen worden aangepast of dat Render er een achtervoegsel aan toevoegt: **stop**, klik niet op Apply, en laat het mij weten.
7. Vul de twee velden in die Render vraagt (zie hieronder) en klik op **Apply** (of **Deploy Blueprint**).
8. Wacht tot de dienst op **Live** staat (de eerste bouw duurt een paar minuten; er draaien automatisch de migraties op de stagingdatabase).
9. Kopieer het adres bovenaan de dienst. Is het niet `https://vaylide-staging.onrender.com`, pas dan **VIERLIEF_BASE_URL** aan (Environment, daarna **Save, rebuild, and deploy**).
10. Maak een beheeraccount: open bij de dienst **Shell** en voer `python manage.py createsuperuser` uit.

## Wat je invult en wat al in het project staat

Je vult alleen deze twee in:

| Variabele | Wat | Waarde |
|---|---|---|
| `VIERLIEF_BASE_URL` | het adres van de stagingdienst | `https://vaylide-staging.onrender.com` (of het adres dat Render toont), zonder `/` aan het eind |
| `VIERLIEF_PREVIEW_PASSWORD` | het wachtwoord voor de hele site | zelf kiezen; een wegwerpwachtwoord voor testers. De gebruikersnaam is `voorbeeld` |

Alles hieronder staat al in het bestand of wordt door Render gemaakt:

| Variabele | Waarde | Toelichting |
|---|---|---|
| `VIERLIEF_MODE` | `test` | gesimuleerde betaling, mails alleen in de outbox; de site weigert in testmodus een live Mollie-sleutel |
| `DJANGO_DEBUG` | `false` | zoals live, voor een realistische test |
| `DJANGO_SECRET_KEY` | door Render gegenereerd | eigen sleutel, niet die van live |
| `DATABASE_URL` | verwijst naar `vaylide-staging-db` | nooit naar `vaylide-db` |
| `VIERLIEF_DATA_DIR`, `VIERLIEF_UPLOAD_DIR` | `/var/data`, `/var/data/uploads` | op de eigen schijf |
| `VIERLIEF_TRUSTED_PROXY_HOPS` | `1` | zoals live achter Render |
| `VIERLIEF_PREVIEW_USER` | `voorbeeld` | bestaande previewbeveiliging |
| Toegestaan adres | automatisch | Render voegt het eigen adres toe (`RENDER_EXTERNAL_HOSTNAME`); `DJANGO_ALLOWED_HOSTS` is bewust niet gezet, dus alleen het stagingadres werkt |

Bewust niet gezet: Mollie-sleutel, SMTP, back-up, AI-sleutel en `VIERLIEF_PREVIEW_OPEN_PUBLIC`. Dus: geen echte betalingen, geen echte mails, niets openbaar.

Optioneel later (alleen als je dat wilt): `VIERLIEF_JURIDISCHE_NAAM` voor de juiste naam in de voorwaarden; en een **Mollie-testsleutel** (`test_…`) met `VIERLIEF_PAYMENT_PROVIDER=mollie`, ingevuld in het dashboard met **Save only**. Plak geheime sleutels nooit in een gesprek.

## Wat staging niet doet

- Geen cron-dienst: mislukte taken worden niet automatisch opnieuw geprobeerd en er draaien geen nachtelijke bewaartermijnen of back-ups. Voor testen is dat genoeg.
- Geen productiegegevens: de database begint leeg. De ontwerpen en pakketten worden bij de migratie automatisch ingelezen.
- Kosten: de webdienst (met schijf) en de database zijn betaalde Render-onderdelen. Kijk voor de actuele prijzen in Render.

## Dagelijks gebruik

- Elke push naar `claude/envelop-collectie` bouwt en start staging opnieuw. Nieuwe migraties draaien alleen op de stagingdatabase.
- Live verandert pas als er iets naar de live branch gaat, en dat gebeurt alleen na een uitdrukkelijk akkoord van de eigenaar.
- Wil je een andere branch testen: **Settings -> Build & Deploy -> Branch** van `vaylide-staging`.

## Controlelijst na het aanmaken

1. De site vraagt om een wachtwoord (zonder inloggen: foutmelding 401). Gebruikersnaam `voorbeeld`, het gekozen wachtwoord.
2. Homepage, een ontwerp kiezen, Envelop & zegel, voorbeeld.
3. Bestellen in testmodus: de drie vinkjes, "Bestellen en betalen", de gesimuleerde betaalpagina.
4. De bevestigingsmail staat in de outbox (beheer, onder Verwerking), niet in een echte mailbox.

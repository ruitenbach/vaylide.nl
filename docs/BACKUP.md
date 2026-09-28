# Back-up en herstel

Vaylide bewaart twee soorten gegevens die samen horen: de **database** (klanten, uitnodigingen, aanmeldingen,
bestellingen) en de **uploads** (foto's, muziek en bijlagen in `VIERLIEF_UPLOAD_DIR`). Een bruikbare back-up bevat
beide, van hetzelfde moment.

## Drie lagen

1. **Back-ups van de hosting.** Gebruik de database-back-ups en schijfkopieën van de hostingaanbieder. Bij Render
   hangt wat je krijgt (dagelijkse kopie, herstel naar een tijdstip) af van het gekozen abonnement: controleer dit in
   het dashboard vóór de livegang.
2. **Eigen back-up per nacht.** `python manage.py backup` maakt één bestand met de database (als JSON, los van
   SQLite of PostgreSQL) en alle uploads: `<VIERLIEF_DATA_DIR>/backups/vaylide-JJJJMMDD-UUMMSS.tar.gz`. De nieuwste 14
   blijven bewaard (`--keep` om dat te wijzigen). In `render.yaml` roept de geplande taak `vaylide-taken` elke nacht
   rond 02:00 UTC `/intern/taken/?retentie=1&backup=1` aan (zie `tools/cron_taken.py`).
3. **Een kopie op een andere plek (voorbereid, nog niet aangezet).** Laag 1 en 2 staan bij dezelfde aanbieder. De
   site kan elke nachtelijke back-up **versleuteld** kopiëren naar S3-compatibele opslag bij een andere aanbieder
   (`core/offsite.py`). Dat gebeurt automatisch in de nachtelijke taak zodra alles hieronder is ingevuld. Een
   mislukte kopie breekt de gewone back-up niet; je krijgt dan een e-mail.

   | Variabele | Waarde |
   |---|---|
   | `VIERLIEF_BACKUP_S3_BUCKET` | naam van de bucket (privé, zonder openbare toegang) |
   | `VIERLIEF_BACKUP_S3_ENDPOINT` | adres van de aanbieder (leeg bij AWS) |
   | `VIERLIEF_BACKUP_S3_REGION` | regio, bijv. `eu-central` (volgens de aanbieder) |
   | `VIERLIEF_BACKUP_S3_ACCESS_KEY` / `VIERLIEF_BACKUP_S3_SECRET_KEY` | een sleutelpaar met alleen schrijfrechten op die bucket |
   | `VIERLIEF_BACKUP_S3_PREFIX` | map in de bucket (standaard `vaylide`) |
   | `VIERLIEF_BACKUP_ENCRYPTION_KEY` | maak met `python manage.py backup --nieuwe-sleutel` |

   De aanbieder ziet alleen versleutelde bestanden. **Bewaar de versleutelingssleutel ook buiten de server** (bijv.
   in een wachtwoordkluis): zonder sleutel is een kopie onbruikbaar. Stel bij de aanbieder een bewaarregel in
   (bijv. 30 dagen) en, als dat kan, bescherming tegen verwijderen (object lock/versiebeheer).

   Handmatig testen: `python manage.py backup --offsite`. Herstellen uit een kopie: download het `.enc`-bestand,
   `python manage.py backup --ontsleutel kopie.tar.gz.enc vaylide.tar.gz` en daarna `restore_backup` (hieronder).

## Herstellen

Herstel altijd in een **lege** database, direct na `migrate`. Het commando weigert een database waarin al klanten staan.

```bash
python manage.py migrate
python manage.py restore_backup /pad/naar/vaylide-20261224-020000.tar.gz --ja
python manage.py createsuperuser   # als de beheerder niet in de back-up zat of een nieuw wachtwoord nodig heeft
```

`--ja` bevestigt dat de huidige uploads worden vervangen door die uit de back-up.

## Hersteltest (vóór de livegang, daarna elk kwartaal)

1. Maak een back-up op de testversie: `python manage.py backup`.
2. Zet hem terug in een lege testomgeving (lokaal of een tweede dienst) met de stappen hierboven.
3. Controleer: kun je inloggen, staat een uitnodiging er nog met foto's, en zijn de aanmeldingen er?

De tests in `tests/test_productie.py` controleren het maken, opruimen en terugzetten van een back-up (ook in een
verse database waarin `migrate` de catalogus al heeft gevuld), en de geplande taak met token; `tests/test_offsite.py`
de versleutelde kopie. Hersteltest uitgevoerd op 29 september 2026: zie `docs/CONTROLES.md`.

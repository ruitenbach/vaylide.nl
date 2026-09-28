"""Roept de takenroute van de site aan; bedoeld voor een geplande taak (cron) bij de hosting.

Elke aanroep: mislukte taken opnieuw proberen. Tussen 02:00 en 02:14 UTC ook bewaartermijnen
toepassen en een back-up maken. Nodig: VIERLIEF_CRON_URL (bijv. https://www.vaylide.com/intern/taken/)
en VIERLIEF_CRON_TOKEN (dezelfde waarde als op de webdienst). Alleen standaardbibliotheek.
"""
import datetime
import os
import sys
import urllib.request

url = os.environ["VIERLIEF_CRON_URL"]
now = datetime.datetime.now(datetime.timezone.utc)
if now.hour == 2 and now.minute < 15:
    url += "?retentie=1&backup=1"
req = urllib.request.Request(url, data=b"", method="POST", headers={"Authorization": f"Bearer {os.environ['VIERLIEF_CRON_TOKEN']}"})
try:
    with urllib.request.urlopen(req, timeout=120) as response:
        print(response.read().decode()[:500])
except Exception as exc:  # zichtbaar in het logboek van de cron; exitcode 1 = mislukt
    print(f"Mislukt: {exc}", file=sys.stderr)
    sys.exit(1)

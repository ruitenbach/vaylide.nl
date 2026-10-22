# Beveiliging: fase 1 (oktober 2026)

Uitkomst van de beveiligingsaudit van QR-codes, uitnodigingslinks en aanmelden. Dit document beschrijft wat er in fase 1 is gebouwd, hoe je het controleert en hoe je het terugdraait. Wat later volgt (Pillow, tokens in logs, bescherming tegen aanmeldspam) staat onderaan.

## Wat er is veranderd

1. **Veilige standaardmodus** (`config/settings.py`). Lokaal en in de tests blijft `VIERLIEF_MODE` standaard `test`. Op een openbare hosting is een ontbrekende `VIERLIEF_MODE` een vergissing: staat `RENDER` in de omgeving, of begint `VIERLIEF_BASE_URL` met `https://`, dan weigert de site te starten met de melding "VIERLIEF_MODE ontbreekt". Een ongeldige of lege waarde weigerde al. Inlogcodes op het scherm bestaan alleen in testmodus met e-mail in de outbox.
2. **Raden van uitnodigingslinks** (`invitations/views.py`). Alleen een link die niet bestaat telt als misser. Een bestaande link, ook een verlopen of offline gehaalde (410), telt nooit mee. Bij 60 missers per 10 minuten vanaf één adres krijgt dat adres tot het einde van die 10 minuten overal onder `/u/` een vriendelijke 429-pagina (met `Retry-After`). Bestaande links en QR-codes veranderen niet. Nieuwe uitnodigingen hebben al een achtervoegsel van 8 tekens (`invitations/services.py`).
3. **Wachtwoord raden bij Beheer en Django-admin** (`core/bruteforce.py`, `core/admin_login.py`, `beheer/views.py`). Alleen mislukte pogingen tellen, per IP-netwerk (10 per 15 minuten) én per gebruikersnaam (10 per 15 minuten). Is een teller vol, dan wordt tot het einde van het venster ook een juist wachtwoord niet aangenomen (429). Een geslaagde inlog zet de teller van die gebruikersnaam terug. Klanten loggen in met een eenmalige code en vallen hier niet onder. Beheer en admin delen de tellers.
4. **Client-IP achter Render** (`core/utils.py`, `core/checks.py`, Beheer → Instellingen). `client_ip` neemt alleen het adres dat onze eigen proxy's achteraan `X-Forwarded-For` hebben gezet (`VIERLIEF_TRUSTED_PROXY_HOPS` plaatsen van rechts). Wat de bezoeker zelf links in de header zet, wordt nooit gebruikt. Ongeldige waarden vallen terug op `REMOTE_ADDR`. Poorten, haakjes en IPv4-in-IPv6 worden genormaliseerd. Voor limieten telt een heel IPv6-/64-netwerk als één bezoeker. `manage.py check` waarschuwt als op Render de waarde 0 staat. **Beheer → Instellingen** toont "Jouw IP-adres zoals de site het ziet".

## Zo controleer je de proxy-instelling (eenmalig, op staging)

Render zet de bezoeker achteraan `X-Forwarded-For`; het aantal plaatsen hangt af van de keten voor de dienst. Dat kan niet uit de code worden afgeleid, daarom:

1. Open op staging **Beheer → Instellingen** vanaf je eigen apparaat (via mobiel internet of thuis).
2. Vergelijk "Jouw IP-adres zoals de site het ziet" met je echte publieke adres (bijvoorbeeld via een "wat is mijn IP"-pagina).
3. Gelijk: de waarde is goed. Een ander adres (bijvoorbeeld een adres van de hosting): verhoog `VIERLIEF_TRUSTED_PROXY_HOPS` met 1 en kijk opnieuw. Staat er je eigen adres bij waarde N en blijft dat zo bij N, dan is N goed. Een te hoge waarde laat een bezoeker zijn eigen adres kiezen; controleer daarom ook dat de regel "adressen in X-Forwarded-For" minstens N is.
4. Zet dezelfde waarde op productie.

## Terugdraaien

De limieten staan alleen in de cache (tabel `vierlief_cache`, sleutels `rl:…`) en veranderen geen klantgegevens. Terugdraaien kan door de wijziging terug te zetten (Render → Rollback naar de vorige deploy). Een bij vergissing geblokkeerd adres is na 10 respectievelijk 15 minuten weer vrij; direct vrijgeven kan door de rijen met sleutels die met `rl:slug-miss` of `rl:staff-fail` beginnen uit `vierlief_cache` te verwijderen.

## Later (nog niet gebouwd)

Pillow bijwerken en alleen JPEG/PNG/WebP openen, tokens uit logregels houden, en bescherming tegen automatische aanmeldspam zonder CAPTCHA voor gewone gasten.

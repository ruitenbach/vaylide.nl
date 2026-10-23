# Beveiliging: fase 1 (oktober 2026)

Uitkomst van de beveiligingsaudit van QR-codes, uitnodigingslinks en aanmelden. Dit document beschrijft wat er in fase 1 is gebouwd, hoe je het controleert en hoe je het terugdraait. Wat later volgt (Pillow, tokens in logs, bescherming tegen aanmeldspam) staat onderaan.

## Wat er is veranderd

1. **Veilige standaardmodus** (`config/settings.py`). Lokaal en in de tests blijft `VIERLIEF_MODE` standaard `test`. Op een openbare hosting is een ontbrekende `VIERLIEF_MODE` een vergissing: staat `RENDER` in de omgeving, of begint `VIERLIEF_BASE_URL` met `https://`, dan weigert de site te starten met de melding "VIERLIEF_MODE ontbreekt". Een ongeldige of lege waarde weigerde al. Inlogcodes op het scherm bestaan alleen in testmodus met e-mail in de outbox.
2. **Raden van uitnodigingslinks** (`invitations/views.py`, `invitations/alarm.py`). Alleen een link die niet bestaat telt als misser. Een bestaande link, ook een verlopen of offline gehaalde (410), telt nooit mee. Bestaande links en QR-codes veranderen niet. Nieuwe uitnodigingen hebben al een achtervoegsel van 8 tekens (`invitations/services.py`).
   - **Altijd actief, zonder IP-adres:** een globale teller. Bij meer dan 100 missers van alle bezoekers samen in 10 minuten komt er één logregel (alleen aantallen) en hooguit één e-mail aan de eigenaar per periode van 6 uur. Er wordt niets geblokkeerd. Een aanval kan dus geen stroom meldingen veroorzaken; een storing in de melding laat de pagina nooit falen.
   - **Blokkade per IP-adres: standaard UIT** (`VIERLIEF_LINKBLOKKADE`). Alleen als die op `true` staat én het adres betrouwbaar is, krijgt een adres na 60 missers per 10 minuten tot het einde van dat venster overal onder `/u/` een vriendelijke 429-pagina (met `Retry-After`). Zet dit pas aan nadat de proxyketen op staging is gemeten.
3. **Wachtwoord raden bij Beheer en Django-admin** (`core/bruteforce.py`, `core/admin_login.py`, `beheer/views.py`). Alleen mislukte pogingen tellen, per IP-netwerk (10 per 15 minuten) én per gebruikersnaam (10 per 15 minuten). Is een teller vol, dan wordt tot het einde van het venster ook een juist wachtwoord niet aangenomen (429). Een geslaagde inlog zet de teller van die gebruikersnaam terug. Klanten loggen in met een eenmalige code en vallen hier niet onder. Beheer en admin delen de tellers.
4. **Client-IP achter Render** (`core/ipinfo.py`, `core/utils.py`, `core/checks.py`, Beheer → Instellingen). `client_ip` neemt alleen het adres dat onze eigen proxy's achteraan `X-Forwarded-For` hebben gezet (`VIERLIEF_TRUSTED_PROXY_HOPS` plaatsen van rechts). Wat de bezoeker zelf links in de header zet, wordt nooit gebruikt; `CF-Connecting-IP` en dergelijke worden niet als bron gebruikt. Voor limieten telt een heel IPv6-/64-netwerk als één bezoeker.
5. **Onbetrouwbaar adres: tripwire en waarschuwing** (`core/ipinfo.py`). Een adres geldt als ONBETROUWBAAR als de instelling op Render ontbreekt (0), de keten korter is dan ingesteld, de gekozen plaats ongeldig is of een privé-, intern of Cloudflare-adres is (waarde waarschijnlijk te laag). De Cloudflare-lijst is alleen voor deze controle; raakt hij verouderd, dan valt hooguit de waarschuwing weg. Gevolgen: een limiet per IP gebruikt zo'n adres niet en wordt ook niet gedeeld door alle bezoekers; er blijft een IP-onafhankelijke ondergrens (zie de tabel hieronder). Meldingen: een logregel (zonder adressen) hooguit eens per uur per reden, een rode regel in **Beheer → Instellingen** ("Herkenning van bezoekers (IP)") en `manage.py check` (`vaylide.W002`). Er wordt nergens een volledig IP-adres getoond.
6. **Meting van de proxyketen** (`VIERLIEF_IP_METING`, standaard uit). Zie hieronder.

| Onderdeel | Adres betrouwbaar | Adres onbetrouwbaar of instelling ontbreekt |
|---|---|---|
| Onbekende links | melding; blokkade alleen als `VIERLIEF_LINKBLOKKADE=true` | alleen de globale melding, niemand geblokkeerd |
| Beheer en Django-admin | 10 mislukte pogingen per IP-netwerk én 10 per account | alleen de teller per account (10 per 15 minuten) |
| Aanmelden (RSVP) en inlogcodes voor klanten | ongewijzigd (limiet per adres en per uitnodiging) | ongewijzigd: de bestaande limieten blijven werken, maar delen dan een emmer als het adres te laag is gekozen; de limiet per uitnodiging (600 per uur), formuliertijd en honeypot blijven. Aanpassing hiervan staat in fase 2 |

6. **Tweestapsverificatie voor Beheer en Django-admin** (optioneel, nog niet in productie): zie `docs/TWEESTAPS.md`.

## Stap 1 en stap 2

- **Stap 1 (nu gebouwd, werkt zonder kennis van de proxyketen):** modusbeveiliging, bescherming tegen mislukte logins (altijd per account), waarschuwing bij onbetrouwbaar IP, meetmogelijkheid (uit), melding bij uitzonderlijk veel onbekende links, blokkade van links standaard uit.
- **Stap 2 (pas na een meting op staging):** de juiste `VIERLIEF_TRUSTED_PROXY_HOPS` vastleggen, daarna `VIERLIEF_LINKBLOKKADE=true` overwegen en de IP-limiet voor aanmelden (nu 15 per uur per adres) herzien. Wat Render met `X-Forwarded-For` doet is niet door ons gemeten; alles wat daarover in de rapporten staat komt van derden.

## Zo meet je de proxyketen (eenmalig, op staging, in testmodus)

Render zet de bezoeker ergens in `X-Forwarded-For`; het aantal plaatsen hangt af van de keten voor de dienst en kan niet uit de code worden afgeleid.

1. Zet op staging (testmodus) `VIERLIEF_IP_METING=true` en deploy. In live-modus wordt de meting genegeerd en nooit getoond.
2. Log in als beheerder en open **Beheer → Instellingen**. Onder de instellingen staat per plaats van rechts in `X-Forwarded-For` alleen de soort (`openbaar`, `privé`, `cloudflare`, `ongeldig`) en een gemaskeerd adres (`81.107.x.x`), de soort van `REMOTE_ADDR`, en of `CF-Connecting-IP`, `True-Client-IP`, `X-Real-IP` en `Forwarded` aanwezig zijn en overeenkomen met het gekozen adres. Er wordt niets opgeslagen of gelogd.
3. Herhaal het vanaf mobiel internet en thuis. Controleer ook of een zelf meegestuurde header zichtbaar links blijft staan, bijvoorbeeld: `curl -I -H "X-Forwarded-For: 192.0.2.10" -u gebruiker:wachtwoord https://<staging>/` is hier niet genoeg (de pagina is staff-only); open de pagina in een ingelogde browser met een extensie die een extra `X-Forwarded-For`-header meestuurt, of geef een ingelogde sessiecookie mee aan `curl -H "Cookie: sessionid=…" -H "X-Forwarded-For: 192.0.2.10" …`.
4. Lees af: zie je op welke plaats van rechts de bezoeker staat (soort `openbaar`, gemaskeerd adres klopt met je eigen netwerk), en staat het door jou meegestuurde adres daar links van? Dan is die plaats de waarde voor `VIERLIEF_TRUSTED_PROXY_HOPS`. Staan er privé- of Cloudflare-adressen rechts van de bezoeker, dan telt de waarde die plaatsen mee.
5. Zet de waarde, zet `VIERLIEF_IP_METING` weer uit, en controleer dat "Herkenning van bezoekers (IP)" op "Betrouwbaar" staat. Meet daarna ook op de eigen domeinnaam van productie, omdat die een andere keten kan hebben.

## Terugdraaien

De limieten staan alleen in de cache (tabel `vierlief_cache`, sleutels `rl:…`) en veranderen geen klantgegevens. Terugdraaien kan door de wijziging terug te zetten (Render → Rollback naar de vorige deploy). Een bij vergissing geblokkeerd adres is na 10 respectievelijk 15 minuten weer vrij; direct vrijgeven kan door de rijen met sleutels die met `rl:slug-miss` of `rl:staff-fail` beginnen uit `vierlief_cache` te verwijderen.

## Later (nog niet gebouwd)

Pillow bijwerken en alleen JPEG/PNG/WebP openen, tokens uit logregels houden, en bescherming tegen automatische aanmeldspam zonder CAPTCHA voor gewone gasten.

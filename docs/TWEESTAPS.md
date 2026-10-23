# Tweestapsverificatie (2FA) voor Beheer en Django-admin

Status: gebouwd op een aparte branch, **nog niet** gemerged of uitgerold. Alleen voor medewerkers (`is_staff`); klanten en gasten hebben geen 2FA en merken niets.

## Hoe het werkt
1. Inloggen met wachtwoord, zoals nu (Beheer: `/beheer/inloggen/`, Django-admin: `/<VIERLIEF_DJANGO_ADMIN_PATH>/login/`). De bestaande begrenzing op foute wachtwoorden (`core/bruteforce.py`) blijft ongewijzigd.
2. Heeft het account 2FA, dan vraagt `/beheer/2fa/controle/` om een 6-cijferige code (authenticator-app, TOTP, SHA-1, 30 s) of een herstelcode. Beide ingangen gebruiken dezelfde pagina.
3. **De poort** (`accounts/middleware.py`): een medewerker zonder bevestigde tweede stap in deze sessie telt als *niet ingelogd*, op elke URL (ook bestellingen en gezichten, die voor medewerkers openstaan). Beheer en admin sturen door naar de codepagina. Dit geldt ook voor sessies van vóór het aanzetten en voor een sessie die al eens bevestigd was en daarna opnieuw met wachtwoord inlogt (de bevestiging wordt dan gewist). De bevestiging is een HMAC aan het 2FA-record gekoppeld; na een reset of heractivering is ze ongeldig.

## Instellen (per medewerker, vrijwillig)
Ingelogd in Beheer → **Beveiliging** (of `/beheer/2fa/instellen/`): scan de QR-code, vul de eerste code in. Pas dan gaat 2FA aan, en worden 10 herstelcodes één keer getoond. Daarna kan op `/beheer/2fa/` met een verse code een nieuwe set herstelcodes worden gemaakt (de oude vervalt) of 2FA worden uitgezet (niet zolang 2FA verplicht is).

## Opslag
- TOTP-geheim: versleuteld (Fernet) met `VIERLIEF_2FA_SLEUTEL`, een eigen sleutel los van `DJANGO_SECRET_KEY`. Meerdere sleutels met een komma: de eerste versleutelt, alle ontsleutelen (rotatie). Zonder sleutel kan niemand 2FA instellen en blijft inloggen met wachtwoord werken; `manage.py check` geeft een fout bij een ongeldige sleutel (`vaylide.E003`) of bij verplicht zonder sleutel (`vaylide.E004`).
- Herstelcodes: 12 tekens (60 bit), alleen HMAC-SHA256 met een sleutel afgeleid van de 2FA-sleutel; nooit gelogd of gemaild; één keer getoond.
- Een geschreven code werkt maar één keer (`last_used_step`, atomair bijgewerkt).
- Tabellen: `accounts_twofactor`, `accounts_recoverycode` (migration `accounts/0003`, alleen nieuwe tabellen; geen bestaande tabel of kolom verandert; oudere code negeert ze).

## Begrenzing
Foute codes en herstelcodes: 5 per account en 20 per IP-netwerk per 15 minuten (daarna ook een juiste code geweigerd, 429). Deze tellers staan los van de wachtwoordtellers en zijn alleen bereikbaar na een juist wachtwoord. **Het restrisico uit stap 1 blijft**: wie het e-mailadres van de eigenaar kent, kan met 10 foute wachtwoorden het account 15 minuten laten blokkeren; 2FA verandert dat niet. Er is bewust geen vertrouwd-apparaat-cookie en geen blokkademail gebouwd.

## Sleutel per omgeving, ontbrekend of verkeerd
- `VIERLIEF_2FA_SLEUTEL` is een gewone omgevingsvariabele per dienst (niet in `render.yaml`, niet in de gedeelde groep `vaylide-taken`). Gebruik op staging en productie **twee verschillende sleutels**; ze worden nergens gedeeld of gesynchroniseerd.
- **Sleutel ontbreekt, nog geen 2FA ingesteld:** niemand kan 2FA instellen (melding op het scherm); inloggen met wachtwoord werkt zoals nu.
- **Sleutel ontbreekt of is verkeerd, terwijl een account 2FA heeft:** het codescherm geeft een duidelijke melding (HTTP 503), er wordt niets gecontroleerd, geen herstelcode verbruikt en niemand doorgelaten. Er is bewust **geen terugval** naar alleen wachtwoord. Herstel: de juiste sleutel terugzetten, of `reset_2fa` (werkt zonder sleutel).
- Een ongeldig opgemaakte sleutel meldt `manage.py check` (`vaylide.E003`). Een geldige maar onjuiste sleutel merk je pas bij de eerste codecontrole.

## Terugdraaien
De migratie voegt alleen twee tabellen toe. De vorige code kan zonder migratie-terugdraaiing weer draaien: ze negeert de tabellen. Let op: met de oude code is er geen tweede stap meer, dus alleen het wachtwoord beschermt de accounts weer. Wil je de tabellen ook weg: `migrate accounts 0002`.

## Noodprocedure (telefoon en herstelcodes kwijt)
Alleen op de server (Render-shell):
```
python manage.py reset_2fa <e-mailadres>              # toont wat er zou gebeuren
python manage.py reset_2fa <e-mailadres> --bevestig   # verwijdert 2FA + herstelcodes en beëindigt de sessies van dat account
```
Daarna inloggen met alleen het wachtwoord en opnieuw instellen. Het commando raakt alleen dat ene medewerkersaccount, nooit klanten, en logt een waarschuwing zonder codes.

## Veilig aanzetten op staging (voorstel, vraagt akkoord van de eigenaar)
1. Maak een sleutel: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` en zet hem als `VIERLIEF_2FA_SLEUTEL` op de stagingdienst (niet in git, bewaar hem ook in een wachtwoordmanager: zonder sleutel zijn de geheimen onleesbaar en is `reset_2fa` nodig).
2. Deploy de branch op staging; `migrate` maakt de twee tabellen. `VIERLIEF_2FA_VERPLICHT` blijft uit.
3. Controleer met twee browsers: in browser A met wachtwoord ingelogd blijven, in browser B 2FA instellen; browser A moet nu om een code vragen. Test herstelcode, nieuwe codes en `reset_2fa` op een testaccount, en dat `/beheer/` en de admin zonder code niet openen.
4. Pas als de eigenaar bevestigt: dezelfde sleutel naar productie, 2FA instellen, en eventueel `VIERLIEF_2FA_VERPLICHT=true`. Terugdraaien: variabele op false of `reset_2fa`; de tabellen mogen blijven staan.
5. Draai nooit tests of resets tegen productiegegevens.

## Wat niet is gedaan
Geen 2FA voor klanten/gasten, geen SMS, geen WebAuthn, geen vertrouwd-apparaat, geen blokkademail. Het aanzetten in productie is niet gebeurd.

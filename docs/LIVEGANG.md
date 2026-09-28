# Checklist voor livegang

Vaylide staat nu in testmodus. Er zijn geen betaalde diensten afgesloten en er is niets naar productie gepubliceerd. Hoe je de site op je eigen domein zet, eerst als testversie met een wachtwoord: `docs/ONLINE.md`. Hieronder staat wat nog nodig is: eerst jouw keuzes, dan de aansluitingen en de technische stappen.

## 1. Keuzes en zakelijke zaken

- [ ] **Naam en domein**: controleer of "Vaylide" beschikbaar is als merk (bijvoorbeeld bij BOIP) en bij de KVK. Het domein is `vaylide.com`; de voorbeelden in `.env.example` gebruiken dat domein. Hoe je de site op je domein zet: `docs/ONLINE.md`.
- [ ] **Logo**: zorg dat je de rechten op het logo hebt (bijvoorbeeld van wie het heeft gemaakt) voordat je het als merk vastlegt.
- [ ] **Definitieve prijzen en pakketten**: bedragen, inbegrepen functies, beschikbaarheidsduur en btw. Stel ze in via **Beheer → Prijzen** en zet in **Beheer → Instellingen** "Voorlopige prijzen" uit.
- [ ] **Facturen**: de app maakt geen btw-facturen. De bevestigingsmail is geen factuur. Kies hoe je factureert (boekhoudpakket of een koppeling) en of klanten om een factuur kunnen vragen.
- [ ] **Bedrijfsgegevens** (naam, adres, KVK, btw-nummer) in de voorwaarden, de privacyverklaring en de footer.
- [ ] **Reactietijd**: vul in **Beheer → Instellingen** alleen een reactietijd in die je echt waarmaakt.

## 2. Juridisch (laten controleren)

- [ ] **Privacyverklaring en voorwaarden** staan als concept op de site. Laat ze juridisch controleren en aanvullen.
- [ ] **Bedenktijd bij digitale inhoud**: bij bestellen vraagt de klant nu om directe publicatie na betaling. Laat beoordelen of de tekst bij het vinkje en in de voorwaarden ook moet vermelden dat de bedenktijd daardoor vervalt, en hoe.
- [ ] **Verwerkers en verwerkersovereenkomsten**: hosting, e-mailprovider, Mollie en, als je AI gebruikt, Anthropic.
- [ ] **Rolverdeling voor gastgegevens**: de klant nodigt gasten uit en Vaylide bewaart hun antwoorden. Laat vastleggen wie verwerkingsverantwoordelijke is en wat dat betekent voor de voorwaarden.
- [ ] **Bewaartermijnen** bevestigen of aanpassen in **Beheer → Instellingen**. Nu: gastgegevens 90 dagen na het einde van de beschikbaarheid, ontwerpen zonder account 30 dagen, onbetaalde concepten 365 dagen.
- [ ] **Cookies**: Vaylide gebruikt alleen functionele cookies (inlogsessie, CSRF-beveiliging, en voor gasten een cookie om het eigen antwoord te herkennen). Er is geen tracking of analytics ingebouwd. Wil je later analytics toevoegen, kijk dan opnieuw naar de cookieregels.

## 3. Aansluitingen

- [ ] **Hosting in de EU** met: https, een blijvende map voor uploads (niet openbaar), een worker of een cron-aanroep elke minuut, een dagelijkse taak `apply_retention`, en back-ups. Zie de README voor Docker en Procfile.
- [ ] **Database**: PostgreSQL met dagelijkse back-ups (`DATABASE_URL`).
- [ ] **Back-ups van uploads** (`VIERLIEF_UPLOAD_DIR`) en een **hersteltest** van database en uploads samen.
- [ ] **Mollie**:
  1. Maak een account aan en laat het verifiëren. Zet de gewenste betaalmethoden aan, zoals iDEAL.
  2. Test eerst met een testsleutel: `VIERLIEF_MODE=test`, `VIERLIEF_PAYMENT_PROVIDER=mollie` en `MOLLIE_API_KEY=test_...`. Dit gebruikt de echte Mollie-omgeving zonder echt geld; in testmodus weigert de site een `live_`-sleutel. Stappen en omgevingsvariabelen voor de testversie op Render: `docs/MOLLIE_TEST.md`.
  3. Ga daarna live met `MOLLIE_API_KEY=live_...` en `VIERLIEF_MODE=live`.

  De webhook-URL (`<VIERLIEF_BASE_URL>/webhooks/betaling/mollie/`) wordt per betaling automatisch meegegeven. De site moet daarvoor publiek bereikbaar zijn via https.
- [ ] **E-mail**: een SMTP-account bij een e-mailprovider (`VIERLIEF_EMAIL_MODE=smtp` en `SMTP_*`). Stel SPF, DKIM en DMARC in voor het afzenddomein, zodat e-mails niet in de spam belanden. Test de bezorging bij Gmail, Outlook en iCloud.
- [ ] **AI (optioneel)**: `ANTHROPIC_API_KEY`. Zonder sleutel werkt alles, met vaste voorbeeldteksten. Met sleutel gaan de teksten die een klant voor een tekstvoorstel invult, en de omschrijving van een extra wens, naar Anthropic. Noem dat in de privacyverklaring. Aan het gebruik zijn kosten verbonden. De koppeling heeft *server-side fallback* aan: weigert het model een verzoek, dan kan de API het automatisch opnieuw proberen met een ander, door Anthropic aangewezen model. Dit staat in `core/ai.py` en kan daar uit.

## 4. Technische instellingen voor productie

- [ ] `VIERLIEF_MODE=live`. De app weigert dan te starten zonder echte betaalprovider, SMTP en een https-adres. De testbalk verdwijnt.
- [ ] `DJANGO_DEBUG=false` en een nieuwe, lange `DJANGO_SECRET_KEY` (alleen in de omgevingsvariabelen van de host, niet in Git).
- [ ] `DJANGO_ALLOWED_HOSTS`, `DJANGO_CSRF_TRUSTED_ORIGINS` en `VIERLIEF_BASE_URL=https://...`.
- [ ] `VIERLIEF_TRUSTED_PROXY_HOPS`: meestal 1 achter een reverse proxy of platform-loadbalancer.
- [ ] `VIERLIEF_DJANGO_ADMIN_PATH`: een eigen, moeilijk te raden pad.
- [ ] `VIERLIEF_CRON_TOKEN` als je de cron-aanroep gebruikt in plaats van een worker.
- [ ] `python manage.py migrate`, `collectstatic` (zit in de Dockerfile) en `python manage.py createsuperuser` met een sterk wachtwoord.
- [ ] `python manage.py check --deploy`: alleen de bewuste meldingen W005 en W021 horen over te blijven.
- [ ] **Begin met een lege database.** Gebruik niet de ontwikkeldatabase met testgegevens, zoals het account `controle@vierlief.test`.
- [ ] **Foutmeldingen**: mislukte verwerking en afwijkende betalingen worden al per e-mail aan jou gemeld. Onverwachte serverfouten (500) staan nu alleen in de logs. Stel daarvoor een foutmelder in (bijvoorbeeld e-mail via `ADMINS` of een foutdienst) en een uptime-controle op `/healthz`.
- [ ] **Beveiliging van het beheer**: overweeg tweestapsverificatie voor beheerders of toegang tot `/beheer/` alleen vanaf bekende IP-adressen. Dat zit nog niet in deze versie.

## 5. Proef vóór de lancering

- [ ] Een volledige bestelling met een echte, kleine betaling in live-modus: ontwerp, betaling, publicatie, e-mail met QR-code, aanmelding van een gast en het antwoord in *Mijn Vaylide*.
- [ ] Een afgebroken betaling, en daarna alsnog betalen.
- [ ] Een extra wens met voorstel, akkoord en betaling.
- [ ] Een back-up terugzetten op een testomgeving.
- [ ] De uitnodiging openen op je eigen telefoons (iPhone en Android) en in WhatsApp delen, om de linkvoorvertoning te zien.
- [ ] Vergelijk de ontwerpen alsnog met de schermopname en de referentiesites (zie `docs/AANPAK.md`).

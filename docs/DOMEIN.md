# vaylide.nl koppelen aan Render (voorbereid, nog niet uitgevoerd)

Stand 29 september 2026: de DNS van `vaylide.nl` is **niet** gewijzigd en het wachtwoord van de testversie
staat nog aan. Dit is het stappenplan voor het moment dat de eigenaar besluit om te koppelen.

## Huidige DNS (opgevraagd op 29 september 2026)

| Naam | Type | Waarde |
|---|---|---|
| `vaylide.nl` | NS | `ns.zxcs.nl`, `ns.zxcs.be`, `ns.zxcs.eu` (DNS wordt beheerd bij Vimexx/ZXCS) |
| `vaylide.nl` | A | `185.104.28.238` (huidige webhosting) |
| `vaylide.nl` | AAAA | `2a06:2ec0:1::ffed` |
| `www.vaylide.nl` | A / AAAA | dezelfde adressen |
| | CAA | geen (dus geen beperking voor het https-certificaat) |
| | MX | geen (er is nog geen e-mail op het domein) |

## Wat al klaarstaat in de code

- `DJANGO_ALLOWED_HOSTS` in `render.yaml`: `vaylide.nl,www.vaylide.nl` (het `…onrender.com`-adres voegt Render
  zelf toe). Nieuwe blueprint-waarden worden niet altijd automatisch overgenomen: controleer in Render bij
  **Environment** dat `DJANGO_ALLOWED_HOSTS` deze twee namen bevat.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: `https://vaylide.nl,https://www.vaylide.nl,https://vaylide.onrender.com`.
- `VIERLIEF_BASE_URL` blijft tot de livegang `https://vaylide.onrender.com`, zodat links, QR-codes en de
  terugkeer na betalen blijven werken zolang de DNS nog niet is omgezet.

## Stappen bij het koppelen

1. **Render → dienst `vaylide` → Settings → Custom Domains → Add**: `vaylide.nl`. Render voegt
   `www.vaylide.nl` er zelf bij en stuurt dat door naar `vaylide.nl`.
2. Render toont daarna de records die het verwacht. **Neem die over zoals Render ze toont.** Volgens de
   documentatie van Render zijn dat:

   | Naam (bij Vimexx) | Type | Waarde |
   |---|---|---|
   | `vaylide.nl` (of `@`) | A | `216.24.57.1` |
   | `www` | CNAME | `vaylide.onrender.com` |

   Verwijder daarbij de huidige records die ernaast blijven staan: de A- en AAAA-records van `vaylide.nl`
   naar `185.104.28.238` en `2a06:2ec0:1::ffed`, en de A- en AAAA-records van `www`. Render werkt met IPv4; een
   AAAA-record dat naar de oude hosting wijst, stuurt een deel van de bezoekers naar de verkeerde server.

   Ik kon het Render-dashboard niet inzien. Wijkt wat Render toont af van deze tabel, volg dan Render.
3. Wacht tot Render bij beide namen **Verified** en **Certificate issued** toont (meestal binnen een uur,
   soms langer door de TTL van de oude records).
4. Pas in Render bij **Environment** aan en sla op (de dienst start opnieuw):
   - `VIERLIEF_BASE_URL` = `https://vaylide.nl`
   - bij de cron-dienst `vaylide-taken`: `VIERLIEF_CRON_URL` = `https://vaylide.nl/intern/taken/`
5. Controleer: `https://vaylide.nl/healthz` geeft "ok", `https://www.vaylide.nl` stuurt door naar
   `https://vaylide.nl`, en de site vraagt nog om het wachtwoord van de testversie.
6. Met Mollie: controleer na een testbetaling in het Mollie-dashboard dat de webhook naar
   `https://vaylide.nl/webhooks/betaling/mollie/` ging en status 200 kreeg.

Het wachtwoord (`VIERLIEF_PREVIEW_PASSWORD`) gaat pas uit bij de echte livegang, na de checklist in
`docs/LIVEGANG.md`.

## Let op bij Vimexx

- Staat er nu een website of e-mail op de hosting bij Vimexx (bijvoorbeeld de FOUNDUP-site), dan verdwijnt
  die van `vaylide.nl` zodra de records zijn omgezet. E-mail op `@vaylide.nl` (MX) staat hier los van en
  wordt apart ingesteld bij de keuze voor een e-mailprovider (SPF, DKIM en DMARC, zie `docs/LIVEGANG.md`).
- Zet de TTL van de A-records een dag van tevoren op 300 seconden als Vimexx dat toestaat; dan gaat het
  omzetten sneller en kun je sneller terug.

# Mollie-testbetalingen op de testversie (Render)

Zo koppel je een Mollie-**testsleutel** aan https://vaylide.onrender.com. Er gaat geen echt geld om:
in testmodus (`VIERLIEF_MODE=test`) weigert de site een `live_`-sleutel. De site start dan niet, en
bestellen lukt niet.

## Hoe de betaling werkt

1. De klant klikt op Betalen. De server maakt de betaling aan bij Mollie met het bedrag uit de bestelling,
   een terugkeeradres (`/bestelling/<id>/`) en een webhook (`<VIERLIEF_BASE_URL>/webhooks/betaling/mollie/`).
2. De klant gaat naar de (test)betaalpagina van Mollie. In testmodus kies je daar zelf de uitkomst.
3. Mollie roept de webhook aan met alleen het betaal-id. De server vraagt de status zelf op bij Mollie
   (met de sleutel). Alleen als Mollie `paid` meldt én het bedrag klopt, wordt de bestelling betaald en
   wordt de uitnodiging gepubliceerd. Een status in de melding zelf wordt genegeerd.
4. Bij terugkeer op de bestelpagina vraagt de server de status ook nog eens op (voor het geval de webhook
   later komt). De bedankpagina alleen publiceert nooit.
5. Dubbele of late meldingen: de betaling wordt vergrendeld verwerkt; een al betaalde betaling wordt niet
   opnieuw verwerkt en de publicatietaak heeft een unieke sleutel. Elke melding komt in het logboek
   (Beheer → bestelling).
6. De webhook staat buiten het wachtwoord van de testversie (`/webhooks/` is uitgezonderd), zodat Mollie hem
   kan bereiken. De rest van de site blijft afgeschermd.

## Omgevingsvariabelen in Render (dienst `vaylide` → Environment)

| Variabele | Waarde | Toelichting |
|---|---|---|
| `VIERLIEF_MODE` | `test` | Laten staan. Houdt echte betalingen uit. |
| `VIERLIEF_PAYMENT_PROVIDER` | `mollie` | Nieuw. Zonder deze regel blijft de gesimuleerde testbetaling actief. |
| `MOLLIE_API_KEY` | `test_…` | Zelf invullen in Render (Mollie-dashboard → Ontwikkelaars → API-sleutels → Test-API-sleutel). Nooit in Git of in een chat. |
| `VIERLIEF_BASE_URL` | `https://vaylide.onrender.com` | Moet https zijn: anders stuurt de site geen webhook mee en komt de klant niet goed terug. |
| `VIERLIEF_PREVIEW_PASSWORD` | (bestaand) | Laten staan. |
| `VIERLIEF_TRUSTED_PROXY_HOPS` | `1` | Staat al in de blueprint. |

Niet nodig: een webhook instellen in het Mollie-dashboard (de site geeft hem per betaling mee) of
`DJANGO_CSRF_TRUSTED_ORIGINS` voor Mollie (de webhook heeft geen CSRF nodig).

Na opslaan start Render de dienst opnieuw. Controle: de testbalk zegt dan "Mollie-testbetalingen, er wordt
niets afgeschreven", en in Beheer → Instellingen staat bij Betalingen "Mollie (testsleutel, geen echt geld)".

## Testen op Render

1. Maak een uitnodiging en ga naar Bestellen (Essentieel).
2. **Geslaagd**: kies op de Mollie-testpagina een methode en dan de uitkomst **Paid**. Terug op de
   bestelpagina: status betaald, daarna "je uitnodiging staat online". Open de link en controleer de
   uitnodiging. In Beheer → Bestellingen: status Betaald, betaalmethode, en in het logboek een regel
   "Betaald; verwerking gestart." (eventuele latere meldingen: "Al verwerkt als betaald").
3. **Afgebroken**: nieuwe uitnodiging, Bestellen, op de Mollie-testpagina **Canceled**. Terug op de
   bestelpagina: "betaling geannuleerd" met de knop om opnieuw te betalen. De uitnodiging blijft een
   concept en is niet openbaar.
4. Kijk in het Mollie-dashboard (testmodus) of beide betalingen er staan, en onder de betaling bij
   "Webhook" of de aanroep status 200 kreeg.

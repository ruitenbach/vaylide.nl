# Prijzenbeheer (Beheer → Prijzen en acties)

Fase A, 17 oktober 2026. Gebouwd op de goedgekeurde code `c056d09`, lokaal, **niet gepusht, niet uitgerold**. Standaard uit: `VIERLIEF_PRIJZENBEHEER` (settings `PRICES_ADMIN`). Werkt alleen samen met `VIERLIEF_PRICING_V2`.

## Wat het doet

De eigenaar past de verkoopprijzen (Basis, Luxe, Special per prijsrij, in euro's incl. btw) zelf aan in Beheer, zonder codewijziging of deployment. 9 prijsrijen × 3 indelingen = 27 bedragen (`catalog.PriceRule`). De indeling van een ontwerp (`INDELING`) en de gelegenheid → prijsrij (`GELEGENHEID_RIJ`) blijven in de code.

| Vlag uit (standaard) | Vlag aan |
|---|---|
| Bedragen uit `catalog/prijzen.py` (`PRIJZEN`), precies als voorheen | Bedragen uit de database |
| Pagina alleen-lezen, wijzigen kan niet | Wijzigen met bevestiging, logboek, terugdraaien |

`PRIJZEN` blijft de startstand en de referentie voor de controle; de migratie `0008_prijsbeheer_startstand` bevat een ingevroren kopie van de 27 bedragen (een test vergelijkt die met de code).

## Eén centrale prijsberekening

Alles loopt via `catalog.prijsbeheer.lees(rij, indeling)` ← `prijzen.cel_cents` ← `prijzen.prijs_cents` / `prijs_info` / `beschikbaar`. Collectie, ontwerppagina, Studio, bestelstap, de bestelling (`build_quote`), Mollie, bon en bevestigingsmail gebruiken dat ongewijzigde pad. De tabel wordt hoogstens één keer per verzoek gelezen (`PrijsCacheMiddleware`); er is geen cache over verzoeken heen.

## Veilige foutafhandeling (geen stille terugval)

Met de vlag aan geldt: een ontbrekend of ongeldig databasebedrag (geen geheel getal van € 1,00 tot € 500,00) is `None`. Die kaart is dan **niet te bestellen**: `prijs_cents`/`prijs_info` geven `None`, de offerte weigert (`PricingError`), er ontstaat geen bestelling en geen betaling. Er wordt nooit teruggevallen op de code-prijs. Beheer toont bovenaan (alle Beheerpagina's) dat er een prijs ontbreekt, en de fout komt eenmalig per verzoek in het log (`vaylide.prijzen`). Publieke pagina's blijven werken zonder prijs bij die kaart. De database zelf weigert ook bedragen buiten de grenzen (CheckConstraint).

## Bestaande bestellingen en betalingen

Bedrag, regels en Mollie-bedrag liggen bij het bestellen vast (`Order.total_cents`, `OrderLine`, `Payment.amount_cents`). Een wijziging raakt ze niet; ook "Betaling hervatten" gebruikt het vastgelegde bedrag. Wie midden in het bestellen zit, krijgt de bestaande melding `PriceChanged` (verborgen veld `verwacht`).

## Wijzigen, bevestigen, logboek, terugdraaien

1. **Prijzen wijzigen**: raster met euro-velden (komma of punt, `€` mag). Server controleert: geheel aantal centen, € 1,00 tot € 500,00, Luxe ≥ Basis en Special ≥ Luxe.
2. **Controleer wijziging**: oud → nieuw, verschil, btw-deel (zelfde berekening als bij kortingen, `kortingen.services.vat_part_cents`), aantal geraakte ontwerpen, geraakte kortingscodes en aanbiedingen, waarschuwingen (sprong > 50% vraagt een aparte bevestiging; verhoging vlak voor een geplande aanbieding). Nog niets opgeslagen.
3. **Prijzen doorvoeren**: verplichte reden (3 tot 300 tekens) en het vinkje "direct voor nieuwe bestellingen". De server controleert alles opnieuw en schrijft in één transactie de prijzen, het logboek (`PriceChangeSet` + `PriceChange`: wie, wanneer, oud, nieuw, reden) en de prijshistorie (`kortingen.PriceStand`, zodat een doorgestreepte "was"-prijs bij aanbiedingen klopt).
4. **Gelijktijdige wijzigingen**: het formulier draagt de stempel van de laatste wijziging; is er intussen iets veranderd, dan weigert de server en toont de nieuwe stand.
5. **Terugdraaien** (Logboek → Draai terug): een nieuwe, geregistreerde wijziging met verplichte reden. Cellen die intussen opnieuw zijn gewijzigd staan er wel bij maar niet aangevinkt. Het logboek wordt nooit aangepast of verwijderd; startstand en terugdraaiingen zijn zelf niet terug te draaien; een wijziging kan één keer worden teruggedraaid.

Verloving en Jubileum delen prijsrij `jubileum_verloving` (staat zo in Beheer). Prijsrij `bedank` heet in Beheer **Wenskaart buiten Kerst**; op de site blijft de naam "Bedankkaart / felicitatie". Een wenskaart bij Kerst gebruikt de rij `kerst`.

Geplande prijswijzigingen ("geldig vanaf") zijn bewust niet gebouwd (bewaren voor later).

## Rollen en rechten

Server-side, in `beheer/rollen.py`. Geen enkele rol wordt automatisch aan een bestaand account toegekend; productieaccounts zijn niet aangepast.

| Rol | Hoe | Prijzen |
|---|---|---|
| Eigenaar | superuser, of groep `Eigenaar` | bekijken, wijzigen, terugdraaien |
| Hoofdbeheerder | groep `Hoofdbeheerder` | bekijken, wijzigen, terugdraaien |
| Beheerder | `is_staff` zonder groep | alleen bekijken |
| Klant / anoniem | – | 404 / inlogpagina |

De groepen en hun rechten (`catalog.prijzen_wijzigen`, `catalog.prijzen_terugdraaien`) worden na `migrate` aangemaakt. Een rol toekennen kan alleen op de server met `python manage.py wijs_rol_toe <e-mail> hoofdbeheerder --bevestig`; de rol Eigenaar vraagt extra `--eigenaar-akkoord` (alleen met afzonderlijk akkoord van de eigenaar). Het commando wijzigt nooit een bestaand eigenaarsaccount en maakt geen accounts aan.

**Eigenaarsaccount beschermd:** `rollen.mag_account_wijzigen` laat een eigenaarsaccount alleen door zichzelf wijzigen. Er is geen scherm in Beheer dat een medewerker kan bewerken (Klanten toont alleen klantaccounts, medewerkers geven 404); `anonymize_user` weigert medewerkers en superusers; gebruikers en rechten staan niet in het noodbeheer (alleen Groep, alleen voor superusers).

**Rechten van het productieaccount controleren (alleen lezen):** `python manage.py controleer_rechten` toont per medewerker de rol, superuser of niet, groepen en of prijzen wijzigen mag. Dit is op productie nog niet uitgevoerd.

## Btw

Bedragen zijn incl. btw (`VIERLIEF_BTW_PERCENTAGE`, nu 21%, geen KOR). Nieuwe bestellingen leggen het toegepaste tarief vast in `Order.vat_rate_percent`; bestaande bestellingen blijven leeg en ongemoeid (Beheer rekent die met het instellingstarief, zoals voorheen).

## Livegang (alleen met afzonderlijk akkoord van de eigenaar)

1. Deploy met de vlag uit: geen zichtbare verandering (nieuwe tabellen vol met de startstand).
2. Op staging: `python manage.py controleer_prijsbron` (database tegenover code, ontwerp × gelegenheid × kaartsoort, ook de offerte) en `controleer_rechten`.
3. Mollie-testbetaling na een wijziging; terugdraaien en herhalen.
4. Pas dan `VIERLIEF_PRIJZENBEHEER=1`. Terugdraaien van de hele functie: vlag uit; de code-bedragen gelden weer (let op: wijzigingen uit Beheer gelden dan niet meer).

Automatische aanbiedingen blijven uit (`VIERLIEF_AANBIEDINGEN` niet gezet).

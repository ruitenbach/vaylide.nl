# Concept juridische teksten bij de nieuwe prijsstructuur

Status: **technisch toegepast op de ontwikkelbranch als versie `2026-10-16` van de voorwaarden en in de privacyverklaring (16 oktober 2026, lokaal, nog niet live en nog 'Concept'); zie `docs/VOORWAARDEN.md`.** Eerdere status: concept, niet toegepast. De eigenaar ging op 15 oktober 2026 akkoord met deze teksten als concept. Ze zijn nog niet juridisch beoordeeld.

- `voorwaarden-nieuw.md`: volledige algemene voorwaarden met de wijzigingen in artikel 3, 4, 6 en 7 (Basis, Luxe, Special, 12 maanden online, overgangsregel, geen toeslagen).
- `privacyverklaring-nieuw.md`: volledige privacyverklaring met twee gewijzigde zinnen (onderdeel 2 en 9). Gemaakt uit de site in testmodus: in productie komen er afhankelijk van de instellingen onderdelen bij (Mollie, e-maildienst, analytics, tweede back-uplocatie).

Invulvelden staan tussen haken. De activeringsdatum van de nieuwe prijzen is bewust een placeholder: die wordt bij de daadwerkelijke livegang vastgelegd.

## Zo wordt het doorgevoerd (na akkoord en juridische toets)

1. Nieuw sjabloon in `core/templates/core/voorwaarden/<datum>.html` en een regel in `VERSIONS` in `core/voorwaarden.py`; `CURRENT` wijst dan naar de nieuwe versie. De oude versie `2026-09-29` blijft staan.
2. De nieuwe versie gaat vóór of samen met `VIERLIEF_PRICING_V2` live.
3. De privacyverklaring (`core/templates/core/privacy.html`, `core/privacyverklaring.py`) krijgt de wijzigingen uit `privacyverklaring-nieuw.md`.
4. Vul de activeringsdatum in op de plekken met de placeholder.

## Bedrijfsgegevens die de eigenaar zelf moet bevestigen

De code heeft voor sommige gegevens een standaardwaarde (`config/settings.py`). Dat zijn geen bevestigde bedrijfsgegevens.

| Gegeven | Instelling | Stand |
|---|---|---|
| Juridische naam en rechtsvorm | `VIERLIEF_JURIDISCHE_NAAM` | ontbreekt, de site start in live-modus niet zonder |
| Vestigingsadres | `VIERLIEF_ADRES` | standaardwaarde in de code, te bevestigen |
| KvK-nummer | `VIERLIEF_KVK` | standaardwaarde in de code, te bevestigen |
| Btw-id | `VIERLIEF_BTW` | standaardwaarde in de code, te bevestigen |
| Contact-e-mailadres | `VIERLIEF_CONTACT_EMAIL` | standaardwaarde in de code; op Render zonder waarde in `render.yaml`, dus te bevestigen |
| Telefoonnummer | `VIERLIEF_TELEFOON` | niet ingevuld (niet verplicht) |
| E-maildienst in de privacyverklaring | `VIERLIEF_EMAIL_AANBIEDER` | standaardwaarde in de code, te bevestigen |

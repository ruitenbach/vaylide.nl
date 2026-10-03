# GSAP (GreenSock Animation Platform) 3.15.0

Bron: officiële npm-package `gsap` (https://www.npmjs.com/package/gsap), bestanden uit `dist/`, ongewijzigd:
`gsap.min.js`, `ScrollTrigger.min.js`, `MotionPathPlugin.min.js`, `SplitText.min.js`.

Licentie: "Standard 'no charge' license" (https://gsap.com/community/standard-license/), bekeken op 2 oktober 2026.
Commercieel gebruik is gratis, ook voor de plugins die vroeger alleen voor leden waren (zoals SplitText).
Niet toegestaan: gebruik in een tool waarmee gebruikers zonder code visuele animaties bouwen die concurreert met Webflow.
Vaylide valt daar niet onder: klanten vullen in een Studio alleen teksten, foto's en keuzes in; de animaties zijn vast
onderdeel van de ontwerpen. Controleer de voorwaarden opnieuw bij een grote wijziging van het product.

Gebruikt door: `designs/midnight-emeraude/` (alleen dat ontwerp laadt deze bestanden).
Bijwerken: `npm pack gsap`, uitpakken en de vier bestanden hier vervangen; draai daarna `node e2e/midnight_emeraude.cjs`.

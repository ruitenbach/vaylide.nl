// Beeld bij "Jullie verhaal verdient iets bijzonders" (homepage), stap 1: de echte Signature Ivory-envelop uit de Envelope Collection
// (envelop-engine met papierstructuur, vouwen, voering en lakzegel) in de open stand, met de echte Gouden Avond-kaart die deels uit de
// envelop steekt. Schrijft een PNG met doorzichtige achtergrond (2x). Stap 2: tools/merkbeelden/maak_op_maat_gouden_avond.py.
// Gebruik: DJANGO_DEBUG=true manage.py runserver (poort 8000), daarna: node tools/merkbeelden/render_gouden_avond_envelop.cjs <uitvoer.png>
// Playwright en Chromium nodig; bypassCSP alleen om de opmaak in de labpagina te zetten (de site zelf blijft ongewijzigd).
const { chromium } = require('playwright');
const css = `
html, body, .lab, .lab__main { background: transparent !important; }
.lab__main > *:not(.vx) { visibility: hidden; }
.vx-hint, .vx ~ *, .vx-caption, .vx > *:not(.vx-stage):not(.vx-defs) { visibility: hidden !important; }
.vx { --vx-paper: #E6D6B6; --vx-paper-hi: #F2E6CC; --vx-paper-lo: #CDB993; --vx-inside: #DDCAA4; --vx-inside-lo: #C8B38B; --vx-liner-bg: #F1E7D2; --vx-shadow: 74, 52, 22; --vx-lift: rgba(96, 68, 30, .28); }
/* diep wijnrood lakzegel (alleen voor dit beeld; de collectie zelf blijft ongewijzigd) */
.vx { --vx-wax-hi: #9E2535 !important; --vx-wax: #6B0F20 !important; --vx-wax-lo: #300510 !important; --vx-wax-spec: #E39A9A !important; --vx-wax-gloss: .8 !important; }
.vx .vx-card { left: 19% !important; right: 19% !important; top: -62% !important; height: 110.6% !important; transition: none !important; z-index: 2 !important;
  transform: rotate(-3deg) !important; transform-origin: 50% 100% !important; }
.vx .vx-card__paper, .vx .vx-card__body { display: none !important; }
.ga-kaart { position: absolute; inset: 0; background: #FCF9F3; padding: 7px; box-shadow: 0 0 0 1px rgba(160,135,90,.55), 0 14px 22px -10px rgba(60,40,15,.55), 0 3px 6px rgba(60,40,15,.25); }
.ga-kaart img { display: block; width: 100%; height: 100%; object-fit: cover; }
`;
(async () => {
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  const ctx = await b.newContext({ bypassCSP: true, viewport: { width: 1000, height: 1100 }, deviceScaleFactor: 2 });
  const p = await ctx.newPage();
  await p.goto('http://127.0.0.1:8000/lab/enveloppen/?stijl=signature&zegel=champagne-monogram', { waitUntil: 'networkidle' });
  await p.addStyleTag({ content: css });
  await p.evaluate(() => { const c = document.querySelector('.vx-card'); const d = document.createElement('div'); d.className = 'ga-kaart'; d.innerHTML = '<img src="/static/img/designs/gouden-avond.webp" alt="">'; c.appendChild(d); });
  await p.waitForTimeout(500);
  await p.locator('.vx-seal-hit').first().click({ force: true });
  await p.waitForTimeout(4500);
  const e = await p.locator('.vx-env').first().boundingBox();
  console.log(e);
  const clip = { x: e.x - 70, y: e.y - 330, width: e.width + 140, height: e.height + 330 + 90 };
  await p.screenshot({ path: process.argv[2] || 'open.png', omitBackground: true, clip });
  await b.close();
})();

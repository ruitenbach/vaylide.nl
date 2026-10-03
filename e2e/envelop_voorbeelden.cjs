// VAYLIDE Envelope Collection: voorbeeldbeelden (thumbnails) voor de keuze in de Studio, genomen van de bestaande envelopstudio (/lab/enveloppen/).
// Gebruik (vanuit de projectmap, server met DEBUG): node e2e/envelop_voorbeelden.cjs <basis-url> <uitvoermap met PNG-bestanden>
// Daarna zet `python tools/enveloppen/maak_voorbeelden.py <uitvoermap>` ze om naar static/img/envelop/voorbeeld/ en .../zegel/.
// Er wordt geen nieuw artwork gemaakt: het zijn schermafbeeldingen van de dichte envelop en van het zegel zoals ze al bestaan.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const [base, outDir] = process.argv.slice(2);
const STIJLEN = ["signature", "rose-blush", "midnight-emeraude", "royal-evergreen", "golden-noel"];
const ZEGELS = ["champagne-monogram", "evergreen", "sage-botanical", "noisette-gold", "rose-floral"];

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 760, height: 900 }, deviceScaleFactor: 2, reducedMotion: "reduce" });
  const page = await ctx.newPage();
  for (const stijl of STIJLEN) {
    await page.goto(`${base}/lab/enveloppen/?stijl=${stijl}`, { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(700);
    const env = await page.locator(".vx-env").boundingBox();
    await page.screenshot({ path: path.join(outDir, `envelop-${stijl}.png`), clip: { x: env.x - 14, y: env.y - 14, width: env.width + 28, height: env.height + 36 } });
  }
  for (const zegel of ZEGELS) {
    await page.goto(`${base}/lab/enveloppen/?stijl=signature&zegel=${zegel}`, { waitUntil: "load" });
    await page.waitForTimeout(500);
    const hit = await page.locator(".vx-seal-hit").boundingBox();
    const maat = Math.max(hit.width, hit.height) * 1.5;
    const cx = hit.x + hit.width / 2, cy = hit.y + hit.height / 2;
    await page.screenshot({ path: path.join(outDir, `zegel-${zegel}.png`), clip: { x: cx - maat / 2, y: cy - maat / 2, width: maat, height: maat } });
  }
  await browser.close();
  console.log("klaar:", fs.readdirSync(outDir).join(", "));
})();

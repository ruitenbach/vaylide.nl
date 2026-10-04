// Gouden Avond: eindbeelden van de belangrijkste banden (open scène, datum, programma, aftellen, aanmelden, afsluiting) op 390 en 1366 px.
// Gebruik: node e2e/gouden_avond_eind.cjs <basis-url> [label]  -> voorvertoning-gouden-avond/eind-<breedte>-<band>.png
const { chromium } = require("playwright"); const fs = require("fs"); const path = require("path");
const [base, label = "eind"] = process.argv.slice(2);
const uit = path.join(__dirname, "..", "voorvertoning-gouden-avond"); fs.mkdirSync(uit, { recursive: true });
(async () => {
  const b = await chromium.launch();
  for (const w of [390, 1366]) {
    const h = w < 800 ? 844 : 768;
    const ctx = await b.newContext({ viewport: { width: w, height: h } }); const p = await ctx.newPage();
    await p.goto(base + "/voorbeeld/gouden-avond/?gelegenheid=bruiloft", { waitUntil: "load" });
    await p.waitForTimeout(1200); await p.locator("[data-bc-skip]").click(); await p.waitForTimeout(2200);
    const banden = [["0-scene", null], ["1-datum", ".bc-date"], ["2-programma", ".bc-program"], ["3-aftellen", ".bc-count"], ["4-aanmelden", ".bc-rsvp"], ["5-afsluiting", ".bc-closing"]];
    for (const [naam, sel] of banden) {
      const y = sel ? await p.evaluate((s) => { const e = document.querySelector(s); return Math.max(0, e.getBoundingClientRect().top + scrollY + (innerWidth < 800 ? 40 : 60)); }, sel) : 0;
      await p.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), y); await p.waitForTimeout(1300);
      await p.screenshot({ path: path.join(uit, `${label}-${w}-${naam}.png`) });
    }
    await ctx.close();
  }
  await b.close();
})();

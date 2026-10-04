// Gouden Avond: rondgang langs de hele uitnodiging. Slaat de opening over en maakt per schermhoogte een afbeelding (voorvertoning-gouden-avond/rondgang-<breedte>-<nr>.png).
// Gebruik: node e2e/gouden_avond_rondgang.cjs <basis-url> [label]   Optioneel: VIEWPORTS=390,1366
const { chromium } = require("playwright"); const fs = require("fs"); const path = require("path");
const [base, label = "r"] = process.argv.slice(2);
const uit = path.join(__dirname, "..", "voorvertoning-gouden-avond"); fs.mkdirSync(uit, { recursive: true });
(async () => {
  const b = await chromium.launch();
  for (const w of (process.env.VIEWPORTS || "390,1366").split(",").map(Number)) {
    const h = w < 800 ? 844 : 768;
    const ctx = await b.newContext({ viewport: { width: w, height: h } }); const p = await ctx.newPage(); const fouten = [];
    p.on("pageerror", (e) => fouten.push(e.message)); p.on("console", (m) => { if (m.type() === "error") fouten.push(m.text()); });
    await p.goto(base + "/voorbeeld/gouden-avond/?gelegenheid=bruiloft", { waitUntil: "load" });
    await p.waitForTimeout(1200); await p.locator("[data-bc-skip]").click(); await p.waitForTimeout(2200);
    const hoogte = await p.evaluate(() => document.documentElement.scrollHeight);
    let n = 0;
    for (let y = 0; y < hoogte; y += h - 60) {
      await p.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), y); await p.waitForTimeout(900);
      await p.screenshot({ path: path.join(uit, `${label}-${w}-${String(n++).padStart(2, "0")}.png`) });
    }
    console.log(w, "hoogte", hoogte, "afbeeldingen", n, "breedte", await p.evaluate(() => document.documentElement.scrollWidth), "fouten", JSON.stringify(fouten));
    await ctx.close();
  }
  await b.close();
})();

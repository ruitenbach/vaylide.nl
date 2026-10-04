// Gouden Avond: de opening in een echte browser. Schermafbeeldingen op vaste momenten en controles (geen horizontale scroll, sleutel zichtbaar, geen consolefouten).
// Gebruik: node e2e/gouden_avond.cjs <basis-url> [label]   Optioneel: VIEWPORTS=360,390,768,1366  PAD=/voorbeeld/gouden-avond/?gelegenheid=bruiloft
// Schermafbeeldingen: voorvertoning-gouden-avond/<label>-<breedte>-<stap>.png (niet in Git).
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const [base, label = "run"] = process.argv.slice(2);
const breedtes = (process.env.VIEWPORTS || "390,1366").split(",").map(Number);
const hoogtes = { 360: 740, 390: 844, 768: 1024, 1366: 768 };
const pad = process.env.PAD || "/voorbeeld/gouden-avond/?gelegenheid=bruiloft";
const uit = path.join(__dirname, "..", "voorvertoning-gouden-avond");
fs.mkdirSync(uit, { recursive: true });
(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  for (const w of breedtes) {
    const ctx = await browser.newContext({ viewport: { width: w, height: hoogtes[w] || 800 }, deviceScaleFactor: 1, hasTouch: w < 800 });
    const page = await ctx.newPage();
    const fouten = [];
    page.on("pageerror", (e) => fouten.push("pageerror: " + e.message));
    page.on("console", (m) => { if (m.type() === "error") fouten.push("console: " + m.text()); });
    await page.goto(base + pad, { waitUntil: "load" });
    await page.waitForTimeout(1500);
    const shot = async (stap) => page.screenshot({ path: path.join(uit, `${label}-${w}-${stap}.png`) });
    await shot("0-dicht");
    const zicht = await page.evaluate(() => {
      const r = (s) => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return { x: Math.round(b.left), y: Math.round(b.top), w: Math.round(b.width), h: Math.round(b.height) }; };
      return { vw: innerWidth, vh: innerHeight, sleutel: r("[data-bc-sleutel]"), portaal: r("[data-bc-portal]"), scrollBreedte: document.documentElement.scrollWidth };
    });
    await page.locator("[data-bc-sleutel]").click();
    const t0 = Date.now();
    for (const [ms, stap] of [[900, "1-uitlijnen"], [1500, "2-slot"], [2300, "3-draaien"], [3000, "4-deuren"], [3700, "5-feest"], [5200, "6-video"], [7200, "7-tekst"]]) {
      await page.waitForTimeout(Math.max(0, ms - (Date.now() - t0)));
      await shot(stap);
    }
    const na = await page.evaluate(() => ({
      klaar: document.querySelector("[data-bc]").classList.contains("bc-klaar"),
      deeltjes: document.querySelectorAll(".bc-spark").length,
      bezig: document.documentElement.classList.contains("bc-bezig"),
      scrollBreedte: document.documentElement.scrollWidth,
      status: document.querySelector("[data-bc-status]").textContent,
    }));
    console.log(w, JSON.stringify({ zicht, na, fouten }));
    await ctx.close();
  }
  await browser.close();
})();

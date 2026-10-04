// Kerstkaart: de opening (klopper, drie klopjes, video, eindbeeld, groet) en de kaart eronder op 390 en 1366 px; maakt schermafbeeldingen.
// Gebruik: node e2e/kerstkaart.cjs <basis-url> [label]
const { chromium } = require("playwright"); const fs = require("fs"); const path = require("path");
const [base, label = "k"] = process.argv.slice(2);
const uit = path.join(__dirname, "..", "voorvertoning-kerstkaart"); fs.mkdirSync(uit, { recursive: true });
(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  for (const w of [390, 1366]) {
    const h = w < 800 ? 844 : 768;
    const ctx = await browser.newContext({ viewport: { width: w, height: h } }); const p = await ctx.newPage();
    const fouten = []; p.on("console", (m) => { if (m.type() === "error") fouten.push(m.text()); }); p.on("pageerror", (e) => fouten.push(String(e)));
    await p.goto(base + "/voorbeeld/kerstkaart/?gelegenheid=kerst", { waitUntil: "load" }); await p.waitForTimeout(1500);
    const shot = (n) => p.screenshot({ path: path.join(uit, `${label}-${w}-${n}.png`) });
    await shot("0-dicht");
    const open = p.locator("[data-kk-open]"); const bb = await open.boundingBox(); console.log(w, "klopper-knop", JSON.stringify(bb));
    await open.click();
    for (const [i, ms] of [[1, 200], [2, 380], [3, 460]]) { await p.waitForTimeout(ms); await shot(`1-klop${i}`); }
    await p.waitForTimeout(900);
    const t0 = Date.now(); const rijen = [];
    while (Date.now() - t0 < 16500) {
      const m = await p.evaluate(() => { const v = document.querySelector("[data-kk-video]"); return { t: +v.currentTime.toFixed(2), paused: v.paused, klasse: document.querySelector("[data-kk]").className.replace(/kk-hero ?/, "") }; });
      rijen.push(m);
      const s = Math.round(m.t);
      if (m.t > 0.3 && !p._g) p._g = {};
      if (p._g && [1, 3, 6, 9, 12, 14].includes(s) && !p._g[s]) { p._g[s] = 1; await shot(`2-video-${s}s`); }
      if (m.klasse.includes("kk-finished")) break;
      await p.waitForTimeout(250);
    }
    await p.waitForTimeout(1600);
    console.log(w, "klaar na", Date.now() - t0, "ms, laatste:", JSON.stringify(rijen[rijen.length - 1]));
    await shot("3-eind");
    const hoogte = await p.evaluate(() => document.documentElement.scrollHeight); const sw = await p.evaluate(() => document.documentElement.scrollWidth);
    console.log(w, "documenthoogte", hoogte, "breedte", sw, "overloop:", sw > w);
    let n = 0;
    for (let y = h * 0.85; y < hoogte - h * 0.2; y += h * 0.85) { await p.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), y); await p.waitForTimeout(900); await shot(`4-kaart-${String(++n).padStart(2, "0")}`); }
    console.log(w, "fouten:", JSON.stringify(fouten));
    await ctx.close();
  }
  await browser.close();
})();

// Kerstbol: de overgang einde video -> persoonlijke groet -> eerste sectie van de kaart. Meet helderheid (geen flits), de plek van de elementen (geen sprong)
// en maakt schermafbeeldingen rond het einde en op de grens tussen kop en kaart. Gebruik: node e2e/kerstbol_overgang.cjs <basis-url> [label]
const { chromium } = require("playwright"); const fs = require("fs"); const path = require("path");
const [base, label = "o"] = process.argv.slice(2);
const uit = path.join(__dirname, "..", "voorvertoning-kerstbol"); fs.mkdirSync(uit, { recursive: true });
(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  for (const w of [390, 1366]) {
    const h = w < 800 ? 844 : 768;
    const ctx = await browser.newContext({ viewport: { width: w, height: h } }); const p = await ctx.newPage();
    await p.goto(base + "/voorbeeld/kerstbol/?gelegenheid=kerst", { waitUntil: "load" }); await p.waitForTimeout(1500);
    const meet = () => p.evaluate(() => { const g = (s) => { const e = document.querySelector(s); if (!e) return null; const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]; };
      const v = document.querySelector("[data-kb-video]"); const c = document.createElement("canvas"); c.width = 24; c.height = 24; const x = c.getContext("2d"); let lum = null;
      try { x.drawImage(v, 0, 0, 24, 24); const d = x.getImageData(0, 0, 24, 24).data; let s = 0; for (let i = 0; i < d.length; i += 4) s += 0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2]; lum = Math.round(s / 576); } catch (e) {}
      return { t: +v.currentTime.toFixed(2), lum, hero: g(".kb-hero"), scene: g(".kb-scene"), bodyTop: g(".kb-body"), caption: getComputedStyle(document.querySelector("[data-kb-caption]")).opacity, sw: document.documentElement.scrollWidth, docH: document.documentElement.scrollHeight }; });
    await p.locator("[data-kb-open]").click(); const t0 = Date.now(); const rijen = [];
    while (Date.now() - t0 < 13500) { const m = await meet(); m.ms = Date.now() - t0; rijen.push(m); if (m.t > 9.1 && m.t < 9.2 && !fs.existsSync("x")) { /* geen actie */ }
      if (m.ms > 9400 && m.ms < 13500 && rijen.filter((r) => r.shot).length < 4 && rijen.length % 6 === 0) { await p.screenshot({ path: path.join(uit, `${label}-${w}-einde-${rijen.length}.png`) }); m.shot = true; }
      await p.waitForTimeout(120); }
    const na = rijen.filter((r) => r.t >= 8.8);
    const lums = na.map((r) => r.lum).filter((x) => x != null);
    const sprongen = []; for (let i = 1; i < na.length; i++) { const a = na[i - 1], b = na[i]; if (a.lum != null && b.lum != null && Math.abs(a.lum - b.lum) > 14) sprongen.push([a.t, a.lum, b.lum]); }
    const geom = new Set(na.map((r) => JSON.stringify([r.hero, r.scene, r.sw]))).size;
    const gebied = (k) => new Set(na.map((r) => JSON.stringify(r[k]))).size;
    console.log(`${w}px: helderheid vanaf 8,8 s min ${Math.min(...lums)} max ${Math.max(...lums)}, plotselinge sprongen >14: ${JSON.stringify(sprongen)}, verschillende hero/scene/breedte-maten: ${geom}, kop-hoogte-varianten ${gebied("hero")}, documenthoogte-varianten ${gebied("docH")}`);
    console.log("  groet-dekking over de tijd:", na.filter((_, i) => i % 5 === 0).map((r) => `${r.t}s:${(+r.caption).toFixed(2)}`).join(" "));
    // de grens tussen kop en kaart: scroll rustig en meet de plek van de eerste sectie; schermafbeelding op de naad
    const grens = await p.evaluate(() => Math.round(document.querySelector(".kb-hero").getBoundingClientRect().bottom + scrollY));
    for (const [n, y] of [["a-voor", grens - Math.round(h * 0.6)], ["b-naad", grens - Math.round(h * 0.35)], ["c-na", grens + 40]]) { await p.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), y); await p.waitForTimeout(1200); await p.screenshot({ path: path.join(uit, `${label}-${w}-grens-${n}.png`) }); }
    await ctx.close();
  }
  await browser.close();
})();

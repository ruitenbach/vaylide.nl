// Gouden Avond: echt gemeten contrast van de tekst over de video (axe kan niet door een video heen kijken).
// Per tekstregel: kleur van de tekst tegen de lichtste pixel (percentiel 95) achter die regel, op de poster en op een paar momenten van de video.
// Gebruik: node e2e/gouden_avond_contrast.cjs <basis-url>   (vereist PIL niet; leest de pixels in de pagina via canvas-schermafbeelding)
const { chromium } = require("playwright");
const fs = require("fs"); const path = require("path");
const [base] = process.argv.slice(2);
const lum = ([r, g, b]) => { const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
const contrast = (a, b) => { const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p); return (x + 0.05) / (y + 0.05); };
(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  for (const w of [360, 390, 1366]) {
    const ctx = await browser.newContext({ viewport: { width: w, height: w < 800 ? 780 : 768 } }); const page = await ctx.newPage();
    await page.goto(base + "/voorbeeld/gouden-avond/?gelegenheid=bruiloft", { waitUntil: "load" }); await page.waitForTimeout(1200);
    await page.locator("[data-bc-skip]").click(); await page.waitForTimeout(1500);
    const regels = await page.evaluate(() => ["bc-eyebrow", "bc-names", "bc-datum", "bc-view"].map((k) => { const e = document.querySelector("." + k); const r = e.getBoundingClientRect(); const cs = getComputedStyle(e);
      return { k, x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height), kleur: cs.color.match(/\d+/g).slice(0, 3).map(Number) }; }));
    for (const t of [0, 1.2, 2.5, 4.9]) {
      await page.evaluate(async (t) => { const v = document.querySelector("[data-bc-video]"); v.currentTime = t; await new Promise((r) => v.addEventListener("seeked", r, { once: true })); document.querySelectorAll(".bc-caption *").forEach((e) => { e.style.visibility = "hidden"; }); }, t);
      await page.waitForTimeout(500);
      const buf = await page.screenshot(); const file = path.join(__dirname, "..", "voorvertoning-gouden-avond", `contrast-${w}-${t}.png`); fs.writeFileSync(file, buf);
      const px = await page.evaluate(async (args) => {
        const img = new Image(); img.src = args.src; await img.decode(); const c = document.createElement("canvas"); c.width = img.width; c.height = img.height; const g = c.getContext("2d"); g.drawImage(img, 0, 0);
        return args.regels.map((r) => { const d = g.getImageData(Math.max(0, r.x), Math.max(0, r.y), Math.max(1, Math.min(r.w, innerWidth - r.x)), Math.max(1, r.h)).data; const ls = [];
          for (let i = 0; i < d.length; i += 4) ls.push([d[i], d[i + 1], d[i + 2]]); return { k: r.k, px: ls }; });
      }, { src: "data:image/png;base64," + buf.toString("base64"), regels });
      await page.evaluate(() => document.querySelectorAll(".bc-caption *").forEach((e) => { e.style.visibility = ""; }));
      const uit = px.map((p) => { const r = regels.find((x) => x.k === p.k); const l = p.px.map((c) => lum(c)).sort((a, b) => a - b); const p95 = l[Math.floor(l.length * 0.95)];
        const lichtste = p.px[l.indexOf(p95) >= 0 ? Math.min(p.px.length - 1, Math.floor(p.px.length * 0.95)) : 0];
        const lt = [r.kleur, [Math.round(255 * Math.pow(p95, 1 / 2.2)), Math.round(255 * Math.pow(p95, 1 / 2.2)), Math.round(255 * Math.pow(p95, 1 / 2.2))]];
        return `${p.k}: ${contrast(lt[0], lt[1]).toFixed(1)}`; });
      console.log(`${w}px t=${t}s  ${uit.join("  ")}`);
    }
    await ctx.close();
  }
  await browser.close();
})();

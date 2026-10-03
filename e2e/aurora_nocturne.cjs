// Controle van de kop van Aurora Nocturne: tijdlijn, framesnelheid per fase, console, horizontale overflow,
// 'minder beweging', stilgezette beweging en direct openen.
// Gebruik (vanuit de projectmap, server in testmodus):
//   node e2e/aurora_nocturne.cjs [http://127.0.0.1:8000] [pad naar een uitnodiging, bijv. /u/<code>/] [uitvoermap]
// Zonder pad wordt het voorbeeld /voorbeeld/aurora-nocturne/?gelegenheid=bruiloft gebruikt.
// Let op: in headless Chromium zonder GPU (softwarematige rendering) zijn de absolute fps lager dan op een echt toestel;
// de verhouding tussen de fasen en de verschillen tussen formaten zijn wel bruikbaar.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const [base = "http://127.0.0.1:8000", pad = "/voorbeeld/aurora-nocturne/?gelegenheid=bruiloft", outDir = "/tmp/aurora-controle"] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
const URL = base + pad;
const SIZES = [["mobiel-390", 390, 844, 3], ["tablet-768", 768, 1024, 2], ["desktop-1366", 1366, 900, 1]];
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function fasen(page, cdp, label, ms, actie) {
  const metrics = async () => Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map((m) => [m.name, m.value]));
  const m0 = await metrics();
  await page.evaluate(() => { window.__f.length = 0; });
  if (actie) await actie();
  await sleep(ms);
  const f = await page.evaluate(() => window.__f.slice());
  const m1 = await metrics();
  const dt = []; for (let i = 1; i < f.length; i++) dt.push(f[i] - f[i - 1]);
  const s = [...dt].sort((a, b) => a - b), avg = dt.reduce((a, b) => a + b, 0) / (dt.length || 1);
  return {
    label, fps: +(1000 / avg).toFixed(1), p95: +(s[Math.floor(s.length * 0.95)] || 0).toFixed(1), max: +(s[s.length - 1] || 0).toFixed(1),
    gt34: dt.filter((x) => x > 34).length, gt50: dt.filter((x) => x > 50).length,
    taak: +(((m1.TaskDuration - m0.TaskDuration) / (ms / 1000))).toFixed(2), script: +(((m1.ScriptDuration - m0.ScriptDuration) / (ms / 1000))).toFixed(3),
  };
}

(async () => {
  const browser = await chromium.launch();
  const out = { url: URL, formaten: {}, extra: {} };
  for (const [naam, w, h, dpr] of SIZES) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, deviceScaleFactor: dpr, isMobile: w < 600, hasTouch: w < 800 });
    const page = await ctx.newPage();
    const cdp = await ctx.newCDPSession(page);
    await cdp.send("Performance.enable");
    const fouten = [], mislukt = [];
    page.on("pageerror", (e) => fouten.push(String(e)));
    page.on("console", (m) => { if (m.type() === "error") fouten.push(m.text()); });
    page.on("response", (r) => { if (r.status() >= 400) mislukt.push(r.status() + " " + r.url()); });
    await page.addInitScript(() => {
      Object.defineProperty(navigator, "hardwareConcurrency", { get: () => 8 });
      window.__f = []; const loop = (t) => { window.__f.push(t); requestAnimationFrame(loop); }; requestAnimationFrame(loop);
    });
    await page.goto(URL, { waitUntil: "networkidle" });
    await sleep(2200);
    await page.screenshot({ path: path.join(outDir, `${naam}-1-dicht.png`) });
    const r = { fasen: [] };
    r.fasen.push(await fasen(page, cdp, "wachtstand (envelop, stof)", 2500));
    r.fasen.push(await fasen(page, cdp, "zegel + envelop (0-1,6 s)", 1600, async () => { await page.click(".an-open:not(.an-open--muziek)"); }));
    r.fasen.push(await fasen(page, cdp, "portaal (1,6-3,0 s)", 1450));
    r.fasen.push(await fasen(page, cdp, "reveal, lampen, namen (3,0-5,6 s)", 2600));
    await page.screenshot({ path: path.join(outDir, `${naam}-4-hero.png`) });
    r.fasen.push(await fasen(page, cdp, "rust (6-12 s)", 6000));
    r.fasen.push(await fasen(page, cdp, "scrollen", 3000, async () => {
      await page.evaluate(async () => { const H = document.body.scrollHeight; for (let i = 0; i <= 30; i++) { window.scrollTo(0, (H * i) / 30); await new Promise((q) => setTimeout(q, 90)); } window.scrollTo(0, 0); });
    }));
    r.overflowX = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    r.rust = await page.evaluate(() => ({
      canvassen: document.querySelectorAll("canvas").length,
      animaties: document.getAnimations().filter((a) => a.playState === "running").length,
      lagen: document.querySelectorAll(".an-hero img").length,
    }));
    r.fouten = fouten; r.mislukt = mislukt;
    out.formaten[naam] = r;
    await ctx.close();
  }

  // 'Minder beweging': de uitnodiging opent snel en er beweegt niets.
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce" });
    const page = await ctx.newPage();
    const fouten = []; page.on("pageerror", (e) => fouten.push(String(e)));
    await page.goto(URL, { waitUntil: "networkidle" });
    await sleep(600);
    const t0 = Date.now();
    await page.click(".an-open:not(.an-open--muziek)");
    await page.waitForFunction(() => document.documentElement.classList.contains("is-open"));
    const t = Date.now() - t0;
    await sleep(500);
    await page.screenshot({ path: path.join(outDir, "reduced-motion-hero.png") });
    out.extra.minderBeweging = await page.evaluate((t) => ({
      openenMs: t, lopendeAnimaties: document.getAnimations().filter((a) => a.playState === "running").length,
      lichtZichtbaar: getComputedStyle(document.querySelector(".an-licht--kroon")).opacity, tekstZichtbaar: getComputedStyle(document.querySelector(".an-naam__in")).opacity,
      stofCanvasZichtbaar: (document.querySelector(".an-stof") || {}).style ? document.querySelector(".an-stof").style.display !== "none" : null,
    }), t);
    out.extra.minderBeweging.fouten = fouten;
    await ctx.close();
  }
  // Beweging stilgezet (knop): hetzelfde gedrag.
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    await page.goto(URL, { waitUntil: "networkidle" });
    await sleep(800);
    await page.click("[data-fx-toggle]");
    await sleep(400);
    const t0 = Date.now();
    await page.click(".an-open:not(.an-open--muziek)");
    await page.waitForFunction(() => document.documentElement.classList.contains("is-open"));
    await sleep(500);
    out.extra.stilgezet = await page.evaluate((t) => ({ openenMs: t, lopendeAnimaties: document.getAnimations().filter((a) => a.playState === "running").length, kroonLicht: getComputedStyle(document.querySelector(".an-licht--kroon")).opacity }), Date.now() - t0 - 500);
    await ctx.close();
  }
  // Direct openen (al geopend in deze sessie): de wereld komt kort tot rust.
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await ctx.newPage();
    const fouten = []; page.on("pageerror", (e) => fouten.push(String(e)));
    await page.goto(URL + (URL.includes("?") ? "&" : "?") + "x=1#aanmelden", { waitUntil: "networkidle" });
    await sleep(3500);
    out.extra.direct = await page.evaluate(() => ({ coverVerborgen: !document.querySelector(".an-cover") || document.querySelector(".an-cover").hidden, kroon: getComputedStyle(document.querySelector(".an-licht--kroon")).opacity }));
    out.extra.direct.fouten = fouten;
    await ctx.close();
  }
  fs.writeFileSync(path.join(outDir, "resultaat.json"), JSON.stringify(out, null, 1));
  for (const [naam, r] of Object.entries(out.formaten)) {
    console.log(naam, "overflowX", r.overflowX, "fouten", r.fouten.length, "mislukt", r.mislukt.length, JSON.stringify(r.rust));
    r.fasen.forEach((f) => console.log("  ", f.label.padEnd(36), "fps", String(f.fps).padStart(5), "p95", String(f.p95).padStart(5), "max", String(f.max).padStart(6), ">34ms", String(f.gt34).padStart(3), ">50ms", String(f.gt50).padStart(3), "taak", f.taak, "script", f.script));
  }
  console.log(JSON.stringify(out.extra));
  await browser.close();
})();

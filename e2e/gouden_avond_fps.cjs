// Gouden Avond: beeldsnelheid tijdens de opening (van de tik op de sleutel tot 9 s erna), met aparte cijfers voor de deuren (0 tot 3 s) en het feest met video (3 tot 9 s).
// Gebruik: node e2e/gouden_avond_fps.cjs <basis-url> <label>   Optioneel: VIEWPORTS=390,1366 CPU=4 RUNS=3 CSS='<regels>' TRACE=1
const { chromium } = require("playwright");
const path = require("path");
const [base, label = "meting"] = process.argv.slice(2);
const only = (process.env.VIEWPORTS || "390,1366").split(",");
const cpu = Number(process.env.CPU || 1), runs = Number(process.env.RUNS || 1);
const vps = { "360": { width: 360, height: 740, touch: true }, "390": { width: 390, height: 844, touch: true }, "1366": { width: 1366, height: 768, touch: false } };
const meet = `(() => { const a = [], lt = []; let last = performance.now(), on = true;
  try { new PerformanceObserver((l) => l.getEntries().forEach((e) => lt.push([Math.round(e.startTime - window.__t0), Math.round(e.duration)]))).observe({ entryTypes: ["longtask"] }); } catch (e) {}
  (function loop(t) { a.push([t, t - last]); last = t; if (on) requestAnimationFrame(loop); })(performance.now());
  window.__t0 = performance.now();
  const stat = (d) => { if (!d.length) return null; const tot = d.reduce((x, y) => x + y, 0), s = d.slice().sort((x, y) => x - y);
    return { fps: +(1000 * d.length / tot).toFixed(1), p95: +s[Math.floor(s.length * .95)].toFixed(1), max: +s[s.length - 1].toFixed(1), b34: d.filter((x) => x > 34).length, b50: d.filter((x) => x > 50).length }; };
  window.__stop = () => { on = false; const f = a.slice(2).map((x) => [x[0] - window.__t0, x[1]]);
    return { deuren: stat(f.filter((x) => x[0] < 3000).map((x) => x[1])), feest: stat(f.filter((x) => x[0] >= 3000).map((x) => x[1])),
      slechtste: f.slice().sort((x, y) => y[1] - x[1]).slice(0, 4).map((x) => [Math.round(x[0]), +x[1].toFixed(1)]), longtasks: lt }; };
})()`;
(async () => {
  for (const name of only) for (let r = 1; r <= runs; r++) {
    const browser = await chromium.launch({ channel: "chromium", args: ["--use-angle=d3d11", "--enable-gpu", "--enable-gpu-rasterization", "--ignore-gpu-blocklist", "--autoplay-policy=no-user-gesture-required"] });
    const vp = vps[name];
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.touch ? 2 : 1, hasTouch: vp.touch, bypassCSP: !!process.env.CSS });
    const page = await ctx.newPage();
    page.on("pageerror", (e) => console.log("PAGEFOUT", e.message));
    if (process.env.ABORT) await page.route(new RegExp(process.env.ABORT), (r) => r.abort());
    if (cpu > 1) { const c = await ctx.newCDPSession(page); await c.send("Emulation.setCPUThrottlingRate", { rate: cpu }); }
    if (process.env.CSS) await page.addInitScript(`document.addEventListener("DOMContentLoaded", () => { const s = document.createElement("style"); s.textContent = ${JSON.stringify(process.env.CSS)}; document.head.appendChild(s); })`);
    await page.goto(`${base}/voorbeeld/gouden-avond/?gelegenheid=bruiloft`, { waitUntil: "load" });
    await page.waitForTimeout(3000);
    await page.evaluate(meet);
    const tracePad = path.join(__dirname, "..", "voorvertoning-gouden-avond", `trace-${label}-${name}-cpu${cpu}-${r}.json`);
    if (process.env.TRACE) await browser.startTracing(page, { path: tracePad, categories: ["devtools.timeline", "disabled-by-default-devtools.timeline", "blink.user_timing", "cc", "gpu"] });
    await page.locator("[data-bc-sleutel]").click();
    await page.waitForTimeout(9000);
    const res = await page.evaluate(() => window.__stop());
    if (process.env.TRACE) await browser.stopTracing();
    console.log(`${label} ${name}px CPU x${cpu} run ${r}:`, JSON.stringify(res));
    await browser.close();
  }
})();

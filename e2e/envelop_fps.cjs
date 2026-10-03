// VAYLIDE Envelope Collection: beeldsnelheid en haperingen van het openen van een envelop in de studio (alleen lokaal, DEBUG).
// Gebruik: node e2e/envelop_fps.cjs <basis-url> [stijl=signature] [1366|390]   Optioneel: CPU=4, SOFT=1, N=3 (aantal herhalingen)
// Meet per beeld (requestAnimationFrame) in drie fasen: laden (eerste 2,5 s), wachten op de tik, en het openen zelf (tot 'vx:opened' + 1 s),
// met long animation frames (welk script) om te zien of een hapering uit JavaScript of uit de grafische kaart komt.
const { chromium } = require("playwright");
const [base, stijl = "signature", vpName = "1366"] = process.argv.slice(2);
const vps = { "390": { width: 390, height: 844, dsf: 2, touch: true }, "360": { width: 360, height: 740, dsf: 2, touch: true }, "1366": { width: 1366, height: 900, dsf: 1, touch: false } };
const vp = vps[vpName];
const cpu = Number(process.env.CPU || 1);
const herhaal = Number(process.env.N || 1);
const init = () => {
  window.__f = []; window.__loaf = [];
  let last = performance.now();
  (function loop(t) { window.__f.push([t, t - last]); last = t; requestAnimationFrame(loop); })(last);
  try {
    new PerformanceObserver((l) => l.getEntries().forEach((e) => window.__loaf.push({ start: e.startTime, dur: e.duration, block: e.blockingDuration, rs: e.renderStart,
      scripts: e.scripts.map((s) => `${(s.sourceURL || "").split("/").pop()}:${s.sourceFunctionName || s.invoker || "?"} ${Math.round(s.duration)}ms`) }))).observe({ type: "long-animation-frame", buffered: true });
  } catch (e) { /* oudere Chrome */ }
};
const stat = (arr) => { if (!arr.length) return "geen beelden"; const d = arr.map((x) => x[1]); const tot = d.reduce((x, y) => x + y, 0);
  return `fps ${(1000 * d.length / tot).toFixed(1)}, grootste ${Math.max(...d).toFixed(0)} ms, >33: ${d.filter((x) => x > 33.4).length}, >50: ${d.filter((x) => x > 50).length}, >100: ${d.filter((x) => x > 100).length}, frames ${d.length}`; };
(async () => {
  const browser = await chromium.launch(process.env.SOFT ? { args: ["--ignore-gpu-blocklist"] } : { channel: "chromium", args: ["--use-angle=d3d11", "--enable-gpu", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"] });
  for (let i = 0; i < herhaal; i++) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.dsf, hasTouch: vp.touch });
    const page = await ctx.newPage();
    if (cpu > 1) { const c = await ctx.newCDPSession(page); await c.send("Emulation.setCPUThrottlingRate", { rate: cpu }); }
    await page.addInitScript(init);
    await page.goto(`${base}/lab/enveloppen/?stijl=${stijl}`, { waitUntil: "load" });
    await page.waitForTimeout(3500);
    const t0 = await page.evaluate(() => { window.__opened = 0; document.addEventListener("vx:opened", () => { window.__opened = performance.now(); }); return performance.now(); });
    const hit = page.locator(".vx-seal-hit");
    if (vp.touch) await hit.tap({ force: true }); else await hit.click({ force: true });
    await page.waitForFunction(() => window.__opened > 0, null, { timeout: 12000 });
    await page.waitForTimeout(1000);
    const r = await page.evaluate(() => ({ f: window.__f, loaf: window.__loaf, opened: window.__opened }));
    const fr = r.f.slice(3);
    const tel = (a, b) => fr.filter(([t]) => t >= a && t < b);
    console.log(`\n=== ${stijl} ${vpName}px, CPU x${cpu}${process.env.SOFT ? ", software" : ", GPU"} (opening ${((r.opened - t0) / 1000).toFixed(2)} s tot vx:opened) ===`);
    console.log("laden (0 tot 2,5 s)   :", stat(tel(0, 2500)));
    console.log("openen (tik tot +1 s)  :", stat(tel(t0, r.opened + 1000)));
    fr.filter(([t, d]) => t >= t0 && d > 50).forEach(([t, d]) => {
      const lf = r.loaf.find((e) => e.start <= t && e.start + e.dur >= t - 5);
      console.log(`   ${d.toFixed(0).padStart(4)} ms bij +${((t - t0) / 1000).toFixed(2)} s` + (lf ? `  LoAF ${lf.dur.toFixed(0)} ms, scripts: ${lf.scripts.join("; ") || "geen"}` : "  (geen script: rasteren/GPU)"));
    });
    await ctx.close();
  }
  await browser.close();
})();

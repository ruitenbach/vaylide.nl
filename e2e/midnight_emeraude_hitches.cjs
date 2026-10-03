// Midnight Émeraude: waar komen de haperingen vandaan? Meet per beeld (requestAnimationFrame), samen met 'long animation frames'
// (Chrome: welk script, hoeveel stijl/layout, hoeveel renderen) en lettertype-events, en zet de haperingen op de tijdlijn van de opening.
// Gebruik: node e2e/midnight_emeraude_hitches.cjs <basis-url> [1366|390]   Optioneel: CPU=4, SOFT=1, FULLURL=<adres>, DREMPEL=50 (ms), WARM=1 (zie script)
const { chromium } = require("playwright");
const [base, vpName = "1366"] = process.argv.slice(2);
const vps = { "390": { width: 390, height: 844, dsf: 2, touch: true }, "1366": { width: 1366, height: 768, dsf: 1, touch: false } };
const vp = vps[vpName];
const cpu = Number(process.env.CPU || 1);
const drempel = Number(process.env.DREMPEL || 50);
const init = () => {
  window.__f = []; window.__loaf = []; window.__fonts = []; window.__marks = [];
  let last = performance.now();
  (function loop(t) { window.__f.push([t, t - last]); last = t; requestAnimationFrame(loop); })(last);
  try {
    new PerformanceObserver((l) => l.getEntries().forEach((e) => window.__loaf.push({
      start: e.startTime, dur: e.duration, block: e.blockingDuration, rs: e.renderStart, sl: e.styleAndLayoutStart,
      scripts: e.scripts.map((s) => ({ f: s.sourceFunctionName || s.invoker || "", u: (s.sourceURL || "").split("/").pop(), d: Math.round(s.duration), forced: Math.round(s.forcedStyleAndLayoutDuration) })),
    }))).observe({ type: "long-animation-frame", buffered: true });
  } catch (e) { /* oudere Chrome */ }
  document.fonts.addEventListener("loadingdone", (ev) => window.__fonts.push([performance.now(), ev.fontfaces.map((f) => f.family).join("+")]));
  document.addEventListener("DOMContentLoaded", () => {
    const hero = document.getElementById("me-hero");
    if (!hero) return;
    let was = getComputedStyle(hero).visibility;
    const poll = () => { const v = getComputedStyle(hero).visibility; if (v !== was) { window.__marks.push([performance.now(), "kop " + was + " -> " + v]); was = v; } requestAnimationFrame(poll); };
    requestAnimationFrame(poll);
  });
};
(async () => {
  const browser = await chromium.launch(process.env.SOFT ? { args: ["--ignore-gpu-blocklist"] } : { channel: "chromium", args: ["--use-angle=d3d11", "--enable-gpu", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"] });
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.dsf, hasTouch: vp.touch });
  const page = await ctx.newPage();
  if (cpu > 1) { const c = await ctx.newCDPSession(page); await c.send("Emulation.setCPUThrottlingRate", { rate: cpu }); }
  await page.addInitScript(init);
  await page.goto(process.env.FULLURL || `${base}/voorbeeld/midnight-emeraude/?gelegenheid=bruiloft`, { waitUntil: "load" });
  await page.waitForFunction(() => !!(window.vaylideMidnight && window.vaylideMidnight.master), null, { timeout: 8000 });
  await page.waitForTimeout(5500);   // intro tot de tik
  const t0 = await page.evaluate(() => performance.now());
  await page.locator(".me-cover .vx-seal-hit").click({ force: true });
  await page.waitForTimeout(9500);
  // daarna scrollen
  const tScroll = await page.evaluate(() => performance.now());
  const h = await page.evaluate(() => document.body.scrollHeight - innerHeight);
  for (let y = 0; y < h; y += 90) { await page.mouse.wheel(0, 90); await page.waitForTimeout(16); }
  await page.waitForTimeout(400);
  const r = await page.evaluate(() => ({ f: window.__f, loaf: window.__loaf, fonts: window.__fonts, marks: window.__marks, perf: performance.getEntriesByType("mark").map((m) => [m.startTime, m.name]) }));
  const fase = (t) => (t < t0 ? `laden/intro (${((t - r.f[0][0]) / 1000).toFixed(1)}s na start)` : t < tScroll ? `opening +${((t - t0) / 1000).toFixed(2)}s na tik` : `scrollen`);
  const rest = r.f.slice(3);
  const tel = (a, b) => rest.filter(([t, d]) => (a === null || t >= a) && (b === null || t < b));
  const stat = (arr) => { const d = arr.map((x) => x[1]); const tot = d.reduce((x, y) => x + y, 0); return `fps ${(1000 * d.length / tot).toFixed(1)}, grootste ${Math.max(...d).toFixed(0)} ms, >50 ms: ${d.filter((x) => x > 50).length}, >100 ms: ${d.filter((x) => x > 100).length}, >33 ms: ${d.filter((x) => x > 33.4).length}, frames ${d.length}`; };
  console.log(`\n=== ${vpName}px, CPU x${cpu}${process.env.SOFT ? ", software" : ", GPU"} ===`);
  const warmEind = (r.perf.find(([, n]) => n === "me:opwarmen-klaar") || [null])[0];
  const warmBegin = (r.perf.find(([, n]) => n === "me:opwarmen-begin") || [null])[0];
  if (warmEind) {
    console.log(`opwarmen (onzichtbaar, ${((warmEind - warmBegin) / 1000).toFixed(2)} s, ${(warmEind / 1000).toFixed(2)} s na start):`, stat(tel(null, warmEind)));
    console.log("intro na opwarmen:", stat(tel(warmEind, t0)));
  } else console.log("laden en intro  :", stat(tel(null, t0)));
  console.log("opening (9,5 s) :", stat(tel(t0, tScroll)));
  console.log("eerste hero-paint (3,6 tot 5,3 s na de tik: kaart lost op, kop komt in beeld):", stat(tel(t0 + 3600, t0 + 5300)));
  console.log("scrollen        :", stat(tel(tScroll, null)));
  console.log("\nlettertypen klaar:", r.fonts.map(([t, n]) => `${((t - r.f[0][0]) / 1000).toFixed(2)}s ${n}`).join(" | "));
  console.log("eigen markeringen (s na start):", r.perf.map(([t, n]) => `${(t / 1000).toFixed(2)} ${n.replace("me:", "")}`).join(" | "));
  console.log("kop-zichtbaarheid:", r.marks.map(([t, m]) => `${fase(t)}: ${m}`).join(" | "));
  console.log(`\nbeelden langer dan ${drempel} ms:`);
  rest.filter(([, d]) => d > drempel).forEach(([t, d]) => {
    const lf = r.loaf.find((e) => e.start <= t && e.start + e.dur >= t - 5);
    console.log(`  ${d.toFixed(0).padStart(4)} ms  ${fase(t)}` + (lf ? `  | LoAF ${lf.dur.toFixed(0)} ms, blokkade ${lf.block.toFixed(0)}, stijl+layout vanaf ${(lf.sl - lf.start).toFixed(0)} ms, render vanaf ${(lf.rs - lf.start).toFixed(0)} ms, scripts: ${lf.scripts.map((s) => `${s.u}:${s.f || "?"} ${s.d}ms${s.forced ? " (forced " + s.forced + ")" : ""}`).join("; ") || "geen"}` : "  | geen LoAF (taak buiten het hoofdscript: rasteren/GPU)"));
  });
  await browser.close();
})();

// Midnight Émeraude: Chrome-trace van laden, intro en opening, om te zien welke raster-, decode- en GPU-taken de lange beelden veroorzaken.
// Gebruik: node e2e/midnight_emeraude_trace.cjs <basis-url> [1366|390]   Schrijft een samenvatting; het ruwe spoor blijft in de tijdelijke map.
const { chromium } = require("playwright");
const fs = require("fs");
const os = require("os");
const path = require("path");
const [base, vpName = "1366"] = process.argv.slice(2);
const vps = { "390": { width: 390, height: 844, dsf: 2, touch: true }, "1366": { width: 1366, height: 768, dsf: 1, touch: false } };
const vp = vps[vpName];
const drempel = Number(process.env.DREMPEL || 25);
(async () => {
  const browser = await chromium.launch({ channel: "chromium", args: ["--use-angle=d3d11", "--enable-gpu", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"] });
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.dsf, hasTouch: vp.touch });
  const page = await ctx.newPage();
  const file = path.join(os.tmpdir(), `me-trace-${vpName}.json`);
  await browser.startTracing(page, { path: file, categories: ["cc", "gpu", "viz", "blink", "blink.user_timing", "disabled-by-default-devtools.timeline", "devtools.timeline", "benchmark", "toplevel", "v8.execute"] });
  await page.goto(process.env.FULLURL || `${base}/voorbeeld/midnight-emeraude/?gelegenheid=bruiloft`, { waitUntil: "load" });
  await page.waitForFunction(() => !!(window.vaylideMidnight && window.vaylideMidnight.master), null, { timeout: 8000 });
  await page.waitForTimeout(5500);
  await page.evaluate(() => { console.timeStamp("tik"); });
  await page.locator(".me-cover .vx-seal-hit").click({ force: true });
  await page.waitForTimeout(9000);
  await browser.stopTracing();
  const spoor = JSON.parse(fs.readFileSync(file, "utf8")).traceEvents;
  const namen = {}; spoor.filter((e) => e.ph === "M" && e.name === "thread_name").forEach((e) => { namen[`${e.pid}:${e.tid}`] = e.args.name; });
  const tik = spoor.find((e) => e.name === "TimeStamp" && e.args && e.args.data && e.args.data.message === "tik");
  const t0 = tik ? tik.ts : spoor.filter((e) => e.ts).reduce((m, e) => Math.min(m, e.ts), Infinity);
  const begin = spoor.filter((e) => e.ts).reduce((m, e) => Math.min(m, e.ts), Infinity);
  const lang = spoor.filter((e) => e.ph === "X" && e.dur >= drempel * 1000 && !/RunTask$|ThreadControllerImpl|RunMainLoop|MessageLoop/.test(e.name))
    .map((e) => ({ t: (e.ts - t0) / 1e6, d: e.dur / 1000, n: e.name, th: namen[`${e.pid}:${e.tid}`] || `${e.pid}:${e.tid}`, a: e.args && (e.args.data || e.args.layer_id !== undefined ? JSON.stringify(e.args).slice(0, 110) : "") }))
    .sort((a, b) => a.t - b.t);
  console.log(`\n=== ${vpName}px: taken van minstens ${drempel} ms (tijd t.o.v. de tik; negatief = laden/intro; spoor begint bij ${((begin - t0) / 1e6).toFixed(1)}s) ===`);
  const perNaam = {};
  lang.forEach((e) => { const k = `${e.th} | ${e.n}`; (perNaam[k] = perNaam[k] || []).push(e); });
  Object.entries(perNaam).sort((a, b) => b[1].reduce((x, y) => x + y.d, 0) - a[1].reduce((x, y) => x + y.d, 0)).slice(0, 18).forEach(([k, a]) =>
    console.log(`${String(a.length).padStart(3)}x ${a.reduce((x, y) => x + y.d, 0).toFixed(0).padStart(5)} ms totaal, langste ${Math.max(...a.map((x) => x.d)).toFixed(0)} ms  ${k}`));
  const gpu = lang.filter((e) => e.n === "GPUTask");
  console.log(`\nGPU-taken (rasteren op de grafische kaart) vanaf ${drempel} ms; t < 0 is laden en intro, t > 0 is na de tik:`);
  gpu.forEach((e) => console.log(`  t=${e.t.toFixed(2).padStart(6)}s ${e.d.toFixed(0).padStart(4)} ms  geheugen ${(JSON.parse(e.a.length ? e.a + (e.a.endsWith("}") ? "" : "}}") : "{}") .data || {}).used_bytes / 1048576 || 0}`.replace(/geheugen .*/, (m) => m)));
  const main = lang.filter((e) => e.th === "CrRendererMain" && /BeginMainFrame|FunctionCall|EventDispatch|UpdateStyleAndLayout|Paint|Decode|Layerize|Commit/.test(e.n));
  console.log(`\nhoofdthread vanaf ${drempel} ms:`);
  main.forEach((e) => console.log(`  t=${e.t.toFixed(2).padStart(6)}s ${e.d.toFixed(0).padStart(4)} ms  ${e.n}`));
  await browser.close();
})();

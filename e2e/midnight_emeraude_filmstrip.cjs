// Midnight Émeraude: wat ziet een bezoeker tussen het laden en de intro? Neemt om de ~300 ms een beeld vanaf het laden en schrijft
// per beeld op of het merkmoment staat en of het opwarmen klaar is. Gebruik: node e2e/midnight_emeraude_filmstrip.cjs <basis-url> <uitvoermap> [1366|390]
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const [base, outDir, vpName = "1366"] = process.argv.slice(2);
const vps = { "390": { width: 390, height: 844, dsf: 2, touch: true }, "1366": { width: 1366, height: 768, dsf: 1, touch: false } };
const vp = vps[vpName];
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch({ channel: "chromium", args: ["--use-angle=d3d11", "--enable-gpu", "--ignore-gpu-blocklist"] });
  const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.dsf, hasTouch: vp.touch });
  const page = await ctx.newPage();
  if (Number(process.env.CPU || 1) > 1) { const c = await ctx.newCDPSession(page); await c.send("Emulation.setCPUThrottlingRate", { rate: Number(process.env.CPU) }); }
  const t0 = Date.now();
  await page.goto(`${base}/voorbeeld/midnight-emeraude/?gelegenheid=bruiloft`, { waitUntil: "commit" });
  const rij = [];
  for (let i = 0; i < 16; i++) {
    const t = Date.now() - t0;
    const st = await page.evaluate(() => { const m = document.querySelector(".me-open"); return { merk: !!(m && m.classList.contains("is-aan")), klaar: performance.getEntriesByName("me:opwarmen-klaar").length > 0, begin: performance.getEntriesByName("me:opwarmen-begin").length > 0 }; }).catch(() => ({}));
    await page.screenshot({ path: path.join(outDir, `strip-${vpName}-${String(i).padStart(2, "0")}.png`) }).catch(() => {});
    rij.push(`${(t / 1000).toFixed(2)}s merk=${st.merk} opwarmen-klaar=${st.klaar}`);
    await page.waitForTimeout(220);
  }
  console.log(rij.join("\n"));
  const mk = await page.evaluate(() => performance.getEntriesByType("mark").map((m) => `${(m.startTime / 1000).toFixed(2)} ${m.name}`).join(" | "));
  console.log(mk);
  await browser.close();
})();

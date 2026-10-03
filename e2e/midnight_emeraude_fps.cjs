// Midnight Émeraude: gemeten beeldsnelheid (fps) tijdens de opening, het scrollen door de hele uitnodiging en in rust.
// Gebruik: node e2e/midnight_emeraude_fps.cjs <basis-url>   Optioneel: VIEWPORTS=390,1366 CPU=4 (vertraging van de processor, mobiel nabootsen)
// Standaard met de echte grafische kaart (Chromium via ANGLE/D3D11); SOFT=1 gebruikt de software-renderer (veel trager, een worst case).
// Er wordt geteld met requestAnimationFrame in de pagina zelf; een frame langer dan 33 ms telt als haperend.
const { chromium } = require("playwright");
const [base] = process.argv.slice(2);
const only = (process.env.VIEWPORTS || "390,1366").split(",");
const cpu = Number(process.env.CPU || 1);
const vps = { "390": { width: 390, height: 844, touch: true }, "1366": { width: 1366, height: 768, touch: false } };
const meet = `(() => { const a = []; let last = performance.now(), on = true;
  (function loop(t) { a.push(t - last); last = t; if (on) requestAnimationFrame(loop); })(performance.now());
  window.__stop = () => { on = false; const d = a.slice(2), tot = d.reduce((x, y) => x + y, 0), s = d.slice().sort((x, y) => x - y);
    return { fps: +(1000 * d.length / tot).toFixed(1), p95ms: +s[Math.floor(s.length * .95)].toFixed(1), maxms: +s[s.length - 1].toFixed(1), haper: d.filter((x) => x > 33.4).length, frames: d.length }; };
})()`;
(async () => {
  const browser = await chromium.launch(process.env.SOFT ? { args: ["--ignore-gpu-blocklist"] } : { channel: "chromium", args: ["--use-angle=d3d11", "--enable-gpu", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"] });
  for (const name of only) {
    const vp = vps[name];
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.touch ? 2 : 1, hasTouch: vp.touch });
    const page = await ctx.newPage();
    if (cpu > 1) { const c = await ctx.newCDPSession(page); await c.send("Emulation.setCPUThrottlingRate", { rate: cpu }); }
    await page.goto(process.env.FULLURL || `${base}/voorbeeld/midnight-emeraude/?gelegenheid=bruiloft`, { waitUntil: "load" });
    await page.waitForFunction(() => !!(window.vaylideMidnight && window.vaylideMidnight.master), null, { timeout: 8000 });
    await page.evaluate(() => document.fonts.ready);
    const res = {};
    await page.evaluate(meet); await page.waitForTimeout(3500);
    res.intro = await page.evaluate(() => window.__stop());
    await page.waitForTimeout(1500);   // wacht tot de intro op de tik staat (4,4 s)
    await page.evaluate(meet);
    await page.locator(".me-cover .vx-seal-hit").click({ force: true });
    await page.waitForTimeout(9000);
    res.opening = await page.evaluate(() => window.__stop());
    await page.evaluate(meet);
    await page.waitForTimeout(3000);
    res.rust = await page.evaluate(() => window.__stop());
    await page.evaluate(meet);
    const h = await page.evaluate(() => document.body.scrollHeight - innerHeight);
    for (let y = 0, i = 0; y < h; y += 90) { await page.mouse.wheel(0, 90); await page.waitForTimeout(16); }
    await page.waitForTimeout(500);
    res.scrollen = await page.evaluate(() => window.__stop());
    console.log(`${name}px (CPU x${cpu}):`, JSON.stringify(res));
    await ctx.close();
  }
  await browser.close();
})();

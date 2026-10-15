// Kerstcoupé: de drie paden van de opening, met het filmpje vertraagd in de browser.
// - vooraf geladen: het filmpje speelt meteen;
// - pas na de tik geladen, snel (zoals een iPhone vaak doet: die laadt een filmpje meestal pas na een tik): het filmpje speelt;
// - te traag (2,5 s): na 0,8 seconde vloeit het open raam over de dichte gordijnen.
// Per pad de stand op vijf momenten, en een schermafbeelding na 2 seconden in de uitvoermap.
// Gebruik (vanuit de projectmap, server in testmodus): node e2e/coupe-opening.cjs http://127.0.0.1:8000 /tmp/coupe
const { chromium } = require("playwright");
const fs = require("fs");
const [base, out = "/tmp/coupe"] = process.argv.slice(2);
fs.mkdirSync(out, { recursive: true });
async function run(b, name, delayMs, preload) {
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 } });
  const p = await ctx.newPage();
  // Video's vertragen (en eventueel niet vooraf laden, zoals een iPhone): pas na de tik komt het filmpje.
  let tapped = false;
  await p.route(/coupe(\.[0-9a-f]+)?\.(webm|mp4)/, async (route) => {
    if (!preload && !tapped) { await new Promise((r) => { const t = setInterval(() => { if (tapped) { clearInterval(t); r(); } }, 20); }); }
    if (delayMs) await new Promise((r) => setTimeout(r, delayMs));
    route.continue();
  });
  await p.goto(`${base}/voorbeeld/kerstcoupe/`, { waitUntil: "domcontentloaded" });
  await p.waitForTimeout(preload ? 2500 : 800);
  const before = await p.evaluate(() => document.querySelector("[data-kc-film]").readyState);
  tapped = true;
  await p.click(".kc-open");
  const t0 = Date.now();
  const log = [];
  for (const t of [300, 1000, 2000, 3000, 3700]) {
    const w = t - (Date.now() - t0); if (w > 0) await p.waitForTimeout(w);
    log.push(await p.evaluate((t) => { const c = document.querySelector(".kc-cover"); const v = document.querySelector("[data-kc-film]"); const o = getComputedStyle(document.querySelector(".kc-cover .kc-frame__open")).opacity;
      return `${t}ms speelt=${c.classList.contains("kc-cover--speelt")} film=${c.classList.contains("kc-cover--film")} video=${v.currentTime.toFixed(2)}s open-beeld=${(+o).toFixed(2)}`; }, t));
    if (t === 2000) await p.screenshot({ path: `${out}/pad-${name}.png` });
  }
  await p.waitForFunction(() => document.documentElement.classList.contains("is-open"), null, { timeout: 6000 });
  console.log(`${name}: readyState voor de tik ${before}\n  ` + log.join("\n  ") + `\n  geopend na ${Date.now() - t0} ms`);
  await ctx.close();
}
(async () => {
  const b = await chromium.launch();
  await run(b, "vooraf-geladen", 0, true);
  await run(b, "na-de-tik-snel", 150, false);
  await run(b, "te-traag", 2500, false);
  await b.close();
})();

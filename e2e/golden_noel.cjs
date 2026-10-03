// Golden Noël (kerstspecial): het voorbeeld in de browser, van dichte envelop tot uitnodiging.
// Gebruik (vanuit de projectmap): node e2e/golden_noel.cjs <basis-url> <uitvoermap>   Optioneel: VIEWPORTS=390,1366
// Beelden per schermformaat: dicht, zegel los, half open, kaart uit de envelop, kaart naar voren, uitnodiging (kop) en de
// hele pagina. Controles: geen consolefouten, geen horizontale scroll, openen met aanraken/muis, het openingsscherm is
// daarna weg en de namen staan in beeld, en bij 'minder beweging' meteen de uitnodiging.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const [base, outDir] = process.argv.slice(2);
const only = (process.env.VIEWPORTS || "").split(",").filter(Boolean);
const viewports = [
  { name: "360", width: 360, height: 740, touch: true },
  { name: "390", width: 390, height: 844, touch: true },
  { name: "768", width: 768, height: 1024, touch: true },
  { name: "1366", width: 1366, height: 900, touch: false },
].filter((vp) => !only.length || only.includes(vp.name));
const URL_ = `${base}/voorbeeld/golden-noel/?gelegenheid=kerst`;
const MOMENTS = [["2-zegel-los", 650], ["3-half-open", "flap"], ["4-kaart-uit", 2900], ["5-kaart-voor", 3700], ["6-uitnodiging", 7000]];

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const problems = [];
  for (const vp of viewports) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 2, hasTouch: vp.touch });
    const page = await ctx.newPage();
    const errors = [];
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    page.on("pageerror", (e) => errors.push(String(e)));
    await page.goto(URL_, { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
    const tag = `golden-noel-${vp.name}`;
    await page.screenshot({ path: path.join(outDir, `${tag}-1-dicht.png`) });
    if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) problems.push(`${tag}: horizontale scroll (dicht)`);
    const hit = page.locator(".gn-cover .vx-seal-hit");
    const t0 = await page.evaluate(() => performance.now());
    if (vp.touch) await hit.tap({ force: true }); else await hit.click({ force: true });
    for (const [name, at] of MOMENTS) {
      if (at === "flap") {
        await page.waitForFunction(() => {
          const m = getComputedStyle(document.querySelector(".gn-cover .vx-flap")).transform;
          return m.startsWith("matrix3d") && Number(m.slice(9, -1).split(",")[5]) < 0.42;
        }, null, { polling: 10, timeout: 4000 });
      } else {
        const now = (await page.evaluate(() => performance.now())) - t0;
        if (at > now) await page.waitForTimeout(at - now);
      }
      await page.screenshot({ path: path.join(outDir, `${tag}-${name}.png`) });
    }
    const state = await page.evaluate(() => ({
      open: document.documentElement.classList.contains("is-open"),
      coverHidden: document.querySelector("[data-cover]").hidden,
      names: (() => { const r = document.querySelector(".gn-names").getBoundingClientRect(); return r.top >= 0 && r.top < innerHeight; })(),
    }));
    if (!state.open || !state.coverHidden) problems.push(`${tag}: na het openen is het openingsscherm niet weg`);
    if (!state.names) problems.push(`${tag}: de namen staan na het openen niet in beeld`);
    if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) problems.push(`${tag}: horizontale scroll (uitnodiging)`);
    await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 300) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 180)); } window.scrollTo(0, 0); });
    await page.waitForTimeout(1500);
    await page.screenshot({ path: path.join(outDir, `${tag}-7-pagina.png`), fullPage: true });
    if (errors.length) problems.push(`${tag}: ${errors.join(" | ")}`);
    await ctx.close();
  }
  // Minder beweging: de envelop vervaagt kort en de uitnodiging staat er meteen.
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce", deviceScaleFactor: 2 });
    const page = await ctx.newPage();
    await page.goto(URL_, { waitUntil: "networkidle" });
    await page.locator(".gn-cover .vx-seal-hit").click({ force: true });
    await page.waitForTimeout(700);
    if (!(await page.evaluate(() => document.documentElement.classList.contains("is-open")))) problems.push("minder beweging: uitnodiging niet meteen open");
    await page.screenshot({ path: path.join(outDir, "golden-noel-minder-beweging.png") });
    await ctx.close();
  }
  await browser.close();
  console.log(problems.length ? "PROBLEMEN:\n" + problems.join("\n") : "Geen problemen gevonden.");
  process.exit(problems.length ? 1 : 0);
})();

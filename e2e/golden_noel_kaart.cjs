// Golden Noël: beelden van de kaart zelf (na de envelop), per kleurvariant en schermformaat: kop, halverwege en aanmelden/einde.
// Gebruik (vanuit de projectmap): node e2e/golden_noel_kaart.cjs <basis-url> <uitvoermap>
// Controleert ook: geen consolefouten en geen horizontale scroll.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const [base, outDir] = process.argv.slice(2);
const viewports = [{ name: "390", width: 390, height: 844, touch: true }, { name: "1366", width: 1366, height: 900, touch: false }];

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const problems = [];
  for (const kleur of ["ivoor", "champagne"]) {
    for (const vp of viewports) {
      const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 2, hasTouch: vp.touch });
      const page = await ctx.newPage();
      const errors = [];
      page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
      page.on("pageerror", (e) => errors.push(String(e)));
      await page.goto(`${base}/voorbeeld/golden-noel/?gelegenheid=kerst&kleur=${kleur}#uitnodiging`, { waitUntil: "networkidle" });
      await page.evaluate(() => document.fonts.ready);
      // Geen vloeiend scrollen in de beelden en geen focusring van de sprong naar #uitnodiging.
      await page.evaluate(() => { document.documentElement.style.scrollBehavior = "auto"; if (document.activeElement) document.activeElement.blur(); });
      await page.waitForTimeout(2600);
      const tag = `golden-noel-${kleur}-${vp.name}`;
      await page.screenshot({ path: path.join(outDir, `${tag}-1-kop.png`) });
      // Rustig door de hele kaart scrollen, zodat alle hoofdstukken onthuld zijn.
      await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 260) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 160)); } });
      const scrollToEl = async (sel, block) => page.evaluate(([s, b]) => { const el = document.querySelector(s); if (el) el.scrollIntoView({ block: b, behavior: "instant" }); }, [sel, block]);
      await scrollToEl(".gn-program", "start");
      await page.evaluate(() => window.scrollBy(0, -70));
      await page.waitForTimeout(1600);
      await page.screenshot({ path: path.join(outDir, `${tag}-2-halverwege.png`) });
      await scrollToEl(".gn-count", "center");
      await page.waitForTimeout(1600);
      await page.screenshot({ path: path.join(outDir, `${tag}-3-avond.png`) });
      await scrollToEl("#aanmelden", "start");
      await page.evaluate(() => window.scrollBy(0, -80));
      await page.waitForTimeout(1600);
      await page.screenshot({ path: path.join(outDir, `${tag}-4-aanmelden.png`) });
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
      await page.waitForTimeout(1600);
      await page.screenshot({ path: path.join(outDir, `${tag}-5-einde.png`) });
      if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) problems.push(`${tag}: horizontale scroll`);
      if (errors.length) problems.push(`${tag}: ${errors.join(" | ")}`);
      await ctx.close();
    }
  }
  await browser.close();
  console.log(problems.length ? "PROBLEMEN:\n" + problems.join("\n") : "Geen problemen gevonden.");
  process.exit(problems.length ? 1 : 0);
})();

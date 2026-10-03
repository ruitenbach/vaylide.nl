// VAYLIDE Signature Ivory (envelop met GSAP-opening): beelden van de opening op vaste tijdstippen van de timeline.
// Gebruik: node e2e/signature_ivory.cjs <basis-url> <uitvoermap>   Optioneel: VIEWPORTS=390,1366
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
const TIJDEN = [["1-rust", null], ["2-zegel-indrukken", 0.2], ["3-zegel-breekt", 0.5], ["4-flap-open", 1.0], ["5-voering", 1.5], ["6-kaart-komt", 1.95], ["7-kaart-uit", 2.4], ["8-eindstand", 2.9]];
(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  for (const vp of viewports) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 2, hasTouch: vp.touch });
    const page = await ctx.newPage();
    await page.goto(`${base}/lab/enveloppen/?stijl=signature`, { waitUntil: "load" });
    await page.waitForFunction(() => performance.getEntriesByName("vx:opwarmen-klaar").length > 0, null, { timeout: 15000 });
    await page.waitForTimeout(1800);
    for (const [naam, t] of TIJDEN) {
      if (t !== null) await page.evaluate((x) => { document.querySelector(".vx").vxTimeline.pause().time(x); }, t);
      await page.waitForTimeout(160);
      await page.screenshot({ path: path.join(outDir, `signature-${vp.name}-${naam}.png`) });
    }
    await ctx.close();
  }
  await browser.close();
})();

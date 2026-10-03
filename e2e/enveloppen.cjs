// VAYLIDE Envelope Collection: beelden en controles van de envelopstudio (alleen lokaal, DEBUG).
// Gebruik (vanuit de projectmap): node e2e/enveloppen.cjs <basis-url> <uitvoermap>
// Optioneel: STIJLEN=signature,royal-evergreen  VIEWPORTS=360,390
// Per stijl en schermformaat: dicht, zegel van dichtbij, zegel los, half open, open met voering, kaart half uit, eindstand.
// Controles: geen consolefouten, geen horizontale scroll, het zegel is een knop met een naam, openen met muis/aanraken en
// met het toetsenbord (Enter), 'vx:opened' pas aan het eind, en bij 'minder beweging' dezelfde eindstand zonder animatie.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const [base, outDir] = process.argv.slice(2);
const only = (k) => (process.env[k] || "").split(",").filter(Boolean);
const stijlen = ["signature", "royal-evergreen", "rose-blush"].filter((s) => !only("STIJLEN").length || only("STIJLEN").includes(s));
const viewports = [
  { name: "360", width: 360, height: 740, touch: true },
  { name: "390", width: 390, height: 844, touch: true },
  { name: "768", width: 768, height: 1024, touch: true },
  { name: "1366", width: 1366, height: 900, touch: false },
].filter((vp) => !only("VIEWPORTS").length || only("VIEWPORTS").includes(vp.name));
// Momenten na het aantikken (ms), afgestemd op de stappen in static/js/envelop-collectie.js.
// "half-open" wordt niet op tijd genomen maar op de stand van de flap (ongeveer 65 graden open).
const MOMENTS = [["2b-zegel-los", 650], ["3-half-open", "flap65"], ["4-open-voering", 2000], ["5-kaart-half", 2800], ["6-eindstand", 4300]];
const END_CLASSES = ["is-cracked", "is-opening", "is-flap-back", "is-card-out", "is-card-front", "is-open"];

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const problems = [];
  for (const stijl of stijlen) {
    const url = `${base}/lab/enveloppen/?stijl=${stijl}`;
    for (const vp of viewports) {
      const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 2, hasTouch: vp.touch });
      const page = await ctx.newPage();
      const errors = [];
      page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
      page.on("pageerror", (e) => errors.push(String(e)));
      await page.goto(url, { waitUntil: "networkidle" });
      await page.evaluate(() => document.fonts.ready);
      const tag = `${stijl}-${vp.name}`;
      await page.screenshot({ path: path.join(outDir, `${tag}-1-dicht.png`) });
      const hit = page.locator(".vx-seal-hit");
      const box = await hit.boundingBox();
      const pad = box.width * 0.45;
      await page.screenshot({ path: path.join(outDir, `${tag}-2-zegel.png`),
        clip: { x: box.x - pad, y: box.y - pad, width: box.width + 2 * pad, height: box.height + 2 * pad } });
      if (box.width < 44) problems.push(`${tag}: zegel kleiner dan 44 px om op te tikken (${Math.round(box.width)})`);
      if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) problems.push(`${tag}: horizontale scroll`);
      if (!(await hit.getAttribute("aria-label"))) problems.push(`${tag}: zegel zonder naam`);

      await page.evaluate(() => { window.__opened = 0; document.addEventListener("vx:opened", () => { window.__opened = performance.now(); }); });
      const t0 = await page.evaluate(() => performance.now());
      if (vp.touch) await hit.tap({ force: true }); else await hit.click({ force: true });  // de envelop zweeft zacht
      for (const [name, at] of MOMENTS) {
        if (at === "flap65") {
          await page.waitForFunction(() => {
            const m = getComputedStyle(document.querySelector(".vx-flap")).transform;
            if (!m.startsWith("matrix3d")) return false;
            return Number(m.slice(9, -1).split(",")[5]) < 0.42;  // m22 = cos(hoek)
          }, null, { polling: 10, timeout: 4000 });
        } else {
          const now = (await page.evaluate(() => performance.now())) - t0;
          if (at > now) await page.waitForTimeout(at - now);
        }
        await page.screenshot({ path: path.join(outDir, `${tag}-${name}.png`) });
      }
      await page.waitForFunction(() => window.__opened > 0, null, { timeout: 6000 });
      const openedAfter = (await page.evaluate(() => window.__opened)) - t0;
      // Signature Ivory met GSAP (envelop-signature.js) opent in ongeveer 2,9 s; de klassieke engine in ongeveer 3,8 s.
      const gsapEnv = await page.evaluate(() => document.querySelector(".vx").hasAttribute("data-vx-gsap"));
      if (openedAfter < (gsapEnv ? 2600 : 3600)) problems.push(`${tag}: vx:opened te vroeg (${Math.round(openedAfter)} ms)`);
      if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) problems.push(`${tag}: horizontale scroll na openen`);
      if (errors.length) problems.push(`${tag}: ${errors.join(" | ")}`);
      await ctx.close();
    }
    // Toetsenbord: focus op het zegel, Enter opent.
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
      const page = await ctx.newPage();
      await page.goto(url, { waitUntil: "networkidle" });
      await page.locator(".vx-seal-hit").focus();
      const focused = await page.evaluate(() => document.activeElement && document.activeElement.classList.contains("vx-seal-hit"));
      if (!focused) problems.push(`${stijl}: zegel krijgt geen focus`);
      await page.keyboard.press("Enter");
      await page.waitForFunction(() => document.querySelector("[data-vx]").classList.contains("is-open"), null, { timeout: 6000 })
        .catch(() => problems.push(`${stijl}: openen met Enter werkt niet`));
      await ctx.close();
    }
    // Minder beweging: zelfde eindstand, snel en zonder 3D-animatie.
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce", deviceScaleFactor: 2 });
      const page = await ctx.newPage();
      await page.goto(url, { waitUntil: "networkidle" });
      await page.locator(".vx-seal-hit").click({ force: true });
      await page.waitForTimeout(900);
      const cls = await page.evaluate(() => [...document.querySelector("[data-vx]").classList]);
      const missing = END_CLASSES.filter((c) => !cls.includes(c));
      if (missing.length) problems.push(`${stijl}: bij 'minder beweging' geen eindstand na 0,9 s (mist ${missing.join(", ")})`);
      await page.screenshot({ path: path.join(outDir, `${stijl}-minder-beweging.png`) });
      await ctx.close();
    }
  }
  await browser.close();
  console.log(problems.length ? "PROBLEMEN:\n" + problems.join("\n") : "Geen problemen gevonden.");
  process.exit(problems.length ? 1 : 0);
})();

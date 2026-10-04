// Kerstkaart: de kop is precies één scherm hoog (banner als overlay), de sneeuwrand begint daarna, de groet staat over het eindbeeld.
// Gebruik: node e2e/kerstkaart_hero.cjs <basis-url> [map]
const { chromium } = require("playwright"); const fs = require("fs"); const path = require("path");
const [base, uit = "voorvertoning-kerstkaart"] = process.argv.slice(2); fs.mkdirSync(uit, { recursive: true });
(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  for (const w of [390, 1366]) {
    const h = w < 800 ? 844 : 768;
    const ctx = await browser.newContext({ viewport: { width: w, height: h } }); const p = await ctx.newPage();
    await p.goto(base + "/voorbeeld/kerstkaart/?gelegenheid=kerst", { waitUntil: "load" }); await p.waitForTimeout(1500);
    const meet = () => p.evaluate(() => { const r = (s) => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return { top: Math.round(b.top + scrollY), h: Math.round(b.height), l: Math.round(b.left), w: Math.round(b.width) }; };
      return { vh: innerHeight, banner: r(".inv-banner"), bannerPos: getComputedStyle(document.querySelector(".inv-banner")).position, hero: r(".kk-hero"), scene: r(".kk-scene"), bild: r(".kk-bild"), rand: r(".kk-rand"), brief: r(".kk-brief"), ambient: r(".kk-ambient"), skip: r(".kk-skip"), sw: document.documentElement.scrollWidth }; });
    const a = await meet(); console.log(w, "start", JSON.stringify(a));
    console.log(w, "hero == viewport:", a.hero.h === a.vh, "| hero begint op 0:", a.hero.top === 0, "| sneeuwrand onder de eerste viewport:", a.rand.top >= a.vh, "| geen horizontale overloop:", a.sw === w, "| skip onder de balk:", a.skip.top >= a.banner.top + a.banner.h);
    await p.screenshot({ path: path.join(uit, `hero-${w}-0-start.png`) });
    await p.locator("[data-kk-open]").click(); await p.waitForTimeout(16500);
    const e = await meet(); console.log(w, "eind: klasse", await p.evaluate(() => document.querySelector("[data-kk]").className.replace("kk-hero ", "")));
    await p.screenshot({ path: path.join(uit, `hero-${w}-1-eind.png`) });
    await p.evaluate(() => scrollTo({ top: innerHeight - 120, behavior: "instant" })); await p.waitForTimeout(900);
    await p.screenshot({ path: path.join(uit, `hero-${w}-2-naad.png`) });
    await ctx.close();
  }
  await browser.close();
})();

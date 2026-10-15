// Zwanenhart: gedrag van de opening (tik om de envelop te openen, overslaan, opnieuw afspelen, minder beweging, geweigerde of niet-ladende film, terugkerende bezoeker,
// zonder JavaScript) en de weergave op vier breedtes, met screenshots. Een browser met H.264 speelt de echte film (Chrome of Edge):
//   CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe" node e2e/zwanenhart_functies.cjs http://127.0.0.1:8000 [screenshotmap]
// De Chromium van Playwright speelt geen H.264. Zet dan TESTWEBM=<pad naar een webm-kopie van de film> (alleen voor de test; de site levert de mp4):
// de browser krijgt bij het opvragen van de mp4 die kopie, zodat het afspelen getest kan worden. Zonder TESTWEBM test dit script in die browser de terugval.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");
const [base, schermMap] = process.argv.slice(2);
const pad = process.env.PAD || "/voorbeeld/zwanenhart/?gelegenheid=bruiloft";
const exe = process.env.CHROME;
const webm = process.env.TESTWEBM ? fs.readFileSync(process.env.TESTWEBM) : null;
let goed = 0, fout = 0;
const check = (naam, ok, extra) => { if (ok) goed++; else fout++; console.log((ok ? "  ok  " : "  FOUT ") + naam + (ok ? "" : "  -> " + JSON.stringify(extra))); };
const stand = (page) => page.evaluate(() => {
  const h = document.querySelector("[data-zh]"), v = document.querySelector("[data-zh-video]"), o = document.querySelector("[data-zh-open]");
  return { klassen: [...h.classList].filter((c) => /^zh-(gate|laadt|speelt|tekst|klaar)$/.test(c)).sort().join(" "), bezig: document.documentElement.classList.contains("zh-bezig"),
    inert: document.querySelector(".zh-body").inert, paused: v.paused, t: +v.currentTime.toFixed(2), openUit: o ? o.disabled : null,
    status: document.querySelector("[data-zh-status]").textContent, scrollY: Math.round(scrollY),
    focus: document.activeElement && (document.activeElement.hasAttribute("data-zh-bekijk") ? "bekijk" : document.activeElement.className),
    eindZichtbaar: +getComputedStyle(document.querySelector(".zh-eind")).opacity, tekstZichtbaar: getComputedStyle(document.querySelector("[data-zh-caption]")).visibility === "visible",
    nogmaalsZichtbaar: getComputedStyle(document.querySelector("[data-zh-again]")).display !== "none" };
});
const schot = async (page, naam, vol = false) => { if (schermMap) await page.screenshot({ path: path.join(schermMap, naam + ".png"), fullPage: vol }); };

// Leven in de kaart: hoeveel punten een effectenlaag tekent, en of er nog iets beweegt.
const inkt = (page, sel) => page.evaluate((sel) => { const c = document.querySelector(sel); if (!c) return -1; const g = c.getContext("2d"); const d = g.getImageData(0, 0, c.width, c.height).data; let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 20) n++; return n; }, sel);
const leven = (page) => page.evaluate(() => ({
  fonkel: Math.max(...[...document.querySelectorAll(".zh-fonkel")].map((e) => +getComputedStyle(e).opacity)), heroFx: +getComputedStyle(document.querySelector(".zh-scene > .zh-fx")).opacity,
  lopend: document.getAnimations().filter((a) => a.playState === "running" && !(a instanceof CSSTransition)).length, motion: document.documentElement.classList.contains("fx-motion") }));

async function nieuw(browser, opties = {}, init, extra = {}) {
  const { viewport = { width: 390, height: 844 }, ...rest } = opties;
  const ctx = await browser.newContext({ viewport, hasTouch: true, deviceScaleFactor: extra.dpr || 2, ...rest });
  if (webm && !extra.geenFilm) await ctx.route(/zwanenhart\.mp4/, (r) => r.fulfill({ status: 200, contentType: "video/webm", body: webm }));
  if (extra.geenFilm) await ctx.route(/zwanenhart\.mp4/, (r) => r.abort());
  const page = await ctx.newPage(); const fouten = [];
  page.on("pageerror", (e) => fouten.push(e.message)); page.on("console", (m) => { if (m.type() === "error" && !/net::ERR_FAILED|Failed to load resource/.test(m.text())) fouten.push(m.text()); });
  if (init) await page.addInitScript(init);
  await page.goto(base + pad + (extra.hash || ""), { waitUntil: "load" }); await page.waitForTimeout(900);
  return { ctx, page, fouten };
}
const wachtOp = async (page, fn, ms = 9000) => { const eind = Date.now() + ms; while (Date.now() < eind) { if (await page.evaluate(fn)) return true; await page.waitForTimeout(100); } return false; };

(async () => {
  if (schermMap) fs.mkdirSync(schermMap, { recursive: true });
  const browser = await chromium.launch({ ...(exe ? { executablePath: exe } : {}) });

  for (const [soort, viewport, dpr] of [["mobiel", { width: 390, height: 844 }, 3], ["desktop", { width: 1440, height: 900 }, 1]]) {
    console.log(`\n=== ${soort} (${viewport.width} × ${viewport.height})`);
    console.log("1. Eerste bezoek: het eerste beeld met de knop, de pagina is vergrendeld");
    let { ctx, page, fouten } = await nieuw(browser, { viewport }, null, { dpr });
    let s = await stand(page);
    check("poster met knop, vergrendeld, inhoud inert, film staat stil", s.klassen === "zh-gate" && s.bezig && s.inert && s.paused && s.t === 0 && !s.eindZichtbaar && !s.tekstZichtbaar, s);
    check("de film laadt vooraf", await page.evaluate(() => document.querySelector("video").preload === "auto"));
    await page.waitForTimeout(1500);
    let l = await leven(page);
    const glitter = await inkt(page, ".zh-scene > .zh-fx canvas");
    check("leven op het eerste beeld: glitter tekent, sterretjes fonkelen, animaties lopen", glitter > 0 && l.fonkel === 1 && l.lopend > 5 && l.motion, { glitter, ...l });
    await schot(page, `${soort}-1-start`);

    if (webm || exe) {
      console.log("2. Tik: de film speelt, overslaan heeft de focus");
      await page.locator("[data-zh-open]").tap();
      const speelt = await wachtOp(page, () => document.querySelector("[data-zh]").classList.contains("zh-speelt"));
      await page.waitForTimeout(900);
      s = await stand(page);
      check("film speelt, knop uit, nog vergrendeld, geen namen", speelt && !s.paused && s.t > 0.3 && s.openUit === true && s.bezig && s.inert && !s.tekstZichtbaar, s);
      l = await leven(page);
      check("tijdens de film alleen de film: geen glitter of sterretjes erover", l.fonkel < 0.02 && l.heroFx < 0.02, l);
      check("Opening overslaan heeft de focus en is zichtbaar", s.focus === "zh-skip" && (await page.locator("[data-zh-skip]").isVisible()), s);
      await schot(page, `${soort}-2-envelop-opent`);
      await wachtOp(page, () => document.querySelector("video").currentTime >= 5.4);
      await schot(page, `${soort}-2b-licht-wordt-zwanen`);
      console.log("3. Op 5,8 s: de zwanen zijn bijna bij elkaar, de namen verschijnen en de pagina komt vrij");
      const tekst = await wachtOp(page, () => document.querySelector("[data-zh]").classList.contains("zh-tekst"), 14000);
      await page.waitForTimeout(300);
      const knal = await inkt(page, ".fx-burst canvas, canvas.fx-burst");
      check("bij de namen een regen van vonken en goud", knal > 0, { knal });
      await page.waitForTimeout(1000);
      s = await stand(page);
      check("namen zichtbaar, pagina vrij, film speelt nog of is net klaar", tekst && s.tekstZichtbaar && !s.bezig && !s.inert && s.t >= 5.8, s);
      await schot(page, `${soort}-3-namen`);
      console.log("4. Einde: het laatste beeld blijft staan, focus op 'Bekijk de uitnodiging'");
      const klaar = await wachtOp(page, () => document.querySelector("[data-zh]").classList.contains("zh-klaar"), 8000);
      await page.waitForTimeout(400);
      s = await stand(page);
      check("eindbeeld, geen herhaling, focus op bekijken, knop opnieuw afspelen zichtbaar", klaar && s.klassen === "zh-klaar" && s.eindZichtbaar === 1 && s.focus === "bekijk" && s.nogmaalsZichtbaar, s);
      await schot(page, `${soort}-4-eindbeeld`);
      await page.waitForTimeout(1500);
      s = await stand(page);
      check("de film speelt niet vanzelf opnieuw", s.paused && s.klassen === "zh-klaar", s);
      console.log("5. Opnieuw afspelen");
      await page.locator("[data-zh-again]").click();
      const weer = await wachtOp(page, () => document.querySelector("[data-zh]").classList.contains("zh-speelt"));
      s = await stand(page);
      check("de film speelt opnieuw vanaf het begin, pagina weer even vergrendeld", weer && !s.paused && s.bezig && s.scrollY === 0, s);
      console.log("6. Overslaan tijdens de film");
      await page.locator("[data-zh-skip]").click(); await page.waitForTimeout(300);
      s = await stand(page);
      check("overslaan geeft direct het eindbeeld met namen en een vrije pagina", s.klassen === "zh-klaar" && s.paused && s.t === 0 && !s.bezig && s.tekstZichtbaar && s.focus === "bekijk", s);
    }
    console.log("7. De uitnodiging eronder");
    await page.locator("[data-zh-skip]").click({ force: true }).catch(() => {});
    await page.evaluate(() => { document.querySelector("[data-zh]").classList.contains("zh-klaar") || document.querySelector("[data-zh-skip]").click(); });
    await page.waitForTimeout(300);
    const breedte = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
    check("geen horizontale scroll", breedte.sw <= breedte.cw, breedte);
    // alle banden in beeld laten komen (data-reveal), dan een volledige screenshot
    await page.evaluate(async () => { for (let y = 0; y < document.body.scrollHeight; y += 350) { window.scrollTo(0, y); await new Promise((r) => setTimeout(r, 160)); } window.scrollTo(0, document.body.scrollHeight); await new Promise((r) => setTimeout(r, 600)); });
    await page.waitForTimeout(1200);
    const verborgen = await page.evaluate(() => [...document.querySelectorAll("[data-reveal]:not(.is-visible)")].map((e) => e.parentElement.className));
    await page.evaluate(() => window.scrollTo(0, 0));
    check("alle banden zijn bij het scrollen in beeld gekomen", verborgen.length === 0, verborgen);
    // alleen voor de volledige screenshot: een screenshot van de hele pagina scrolt niet echt, dus wat nog onderweg is meteen tonen
    await page.evaluate(() => document.querySelectorAll("[data-reveal]").forEach((e) => e.classList.add("is-visible")));
    await page.waitForTimeout(1200);
    await schot(page, `${soort}-5-hele-uitnodiging`, true);
    check("geen fouten in de console", fouten.length === 0, fouten);
    await ctx.close();
  }

  console.log("\n8. Terugval: de browser weigert het afspelen");
  let { ctx, page, fouten } = await nieuw(browser, {}, () => { HTMLMediaElement.prototype.play = function () { return Promise.reject(new DOMException("geweigerd", "NotAllowedError")); }; });
  await page.locator("[data-zh-open]").tap(); await page.waitForTimeout(600);
  let s = await stand(page);
  check("geweigerd afspelen: direct eindbeeld met namen, pagina vrij en een melding", s.klassen === "zh-klaar" && s.eindZichtbaar === 1 && s.tekstZichtbaar && !s.bezig && /niet worden afgespeeld/.test(s.status), s);
  await ctx.close();

  console.log("9. Terugval: de film laadt niet");
  ({ ctx, page, fouten } = await nieuw(browser, {}, null, { geenFilm: true }));
  await page.locator("[data-zh-open]").tap();
  const terug = await wachtOp(page, () => document.querySelector("[data-zh]").classList.contains("zh-klaar"), 7500);
  s = await stand(page);
  check("film laadt niet: binnen 6 s het eindbeeld met namen, pagina vrij", terug && s.eindZichtbaar === 1 && s.tekstZichtbaar && !s.bezig, s);
  await schot(page, "terugval-film-laadt-niet");
  await ctx.close();

  console.log("10. Minder beweging");
  ({ ctx, page, fouten } = await nieuw(browser, { reducedMotion: "reduce" }));
  s = await stand(page);
  check("minder beweging: direct eindbeeld met namen, geen knop, pagina vrij", s.klassen === "zh-klaar" && s.eindZichtbaar === 1 && s.tekstZichtbaar && !s.bezig && !(await page.locator("[data-zh-open]").isVisible()), s);
  await page.waitForTimeout(800);
  let rust = await leven(page);
  check("minder beweging: niets beweegt, geen sterretjes", !rust.motion && rust.lopend === 0 && rust.fonkel === 0, rust);
  await ctx.close();

  console.log("10b. De knop 'Beweging' zet alles stil");
  ({ ctx, page, fouten } = await nieuw(browser, {}, null, { hash: "#uitnodiging" }));
  await page.waitForTimeout(1200);
  const voor = await leven(page);
  await page.click("[data-fx-toggle]");
  await page.waitForTimeout(800);
  rust = await leven(page);
  check("na 'Beweging' uit: alles staat stil", voor.lopend > 5 && !rust.motion && rust.lopend === 0, { voor, na: rust });
  await ctx.close();

  console.log("11. Terugkerende bezoeker en aanmeldlink");
  ({ ctx, page, fouten } = await nieuw(browser, {}, () => { try { sessionStorage.setItem("vierlief-open:" + location.pathname, "1"); } catch (e) {} }));
  s = await stand(page);
  check("al gezien in deze sessie: direct het eindbeeld", s.klassen === "zh-klaar" && !s.bezig, s);
  await ctx.close();
  ({ ctx, page, fouten } = await nieuw(browser, {}, null, { hash: "#aanmelden" }));
  s = await stand(page);
  check("aanmeldlink (#aanmelden): geen opening, pagina vrij", s.klassen === "zh-klaar" && !s.bezig && !s.inert, s);
  await ctx.close();

  console.log("12. Zonder JavaScript");
  ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false }); page = await ctx.newPage();
  await page.goto(base + pad, { waitUntil: "load" }); await page.waitForTimeout(400);
  const zonder = await page.evaluate(() => ({ eind: +getComputedStyle(document.querySelector(".zh-eind")).opacity, tekst: getComputedStyle(document.querySelector("[data-zh-caption]")).visibility,
    open: getComputedStyle(document.querySelector("[data-zh-open]")).display, skip: getComputedStyle(document.querySelector("[data-zh-skip]")).visibility }));
  check("zonder JavaScript: eindbeeld en namen, geen knoppen die niets doen", zonder.eind === 1 && zonder.tekst === "visible" && zonder.open === "none" && zonder.skip === "hidden", zonder);
  await schot(page, "zonder-javascript");
  await ctx.close();

  console.log("13. Breedtes zonder horizontale scroll");
  for (const w of [360, 390, 768, 1024, 1366]) {
    ({ ctx, page, fouten } = await nieuw(browser, { viewport: { width: w, height: w < 700 ? 800 : (w === 768 ? 1024 : 800) }, reducedMotion: "reduce" }, null, { dpr: 1 }));
    const b = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
    check(`${w} px: geen horizontale scroll`, b.sw <= b.cw, b);
    if (w === 768 || w === 1024) await schot(page, `breedte-${w}`);
    await ctx.close();
  }

  await browser.close();
  console.log(`\n${goed} goed, ${fout} fout`);
  process.exit(fout ? 1 : 0);
})();

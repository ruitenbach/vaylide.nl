// Strandboog: gedrag van de opening (tik op het doosje, overslaan, opnieuw beleven, toetsenbord, minder beweging, geblokkeerde of mislukte film, terugkerende bezoeker)
// en de weergave op vier breedtes. Een browser met H.264 is nodig om de film te laten spelen (Chrome of Edge; de Chromium van Playwright kan het niet):
//   CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe" node e2e/strandboog_functies.cjs http://127.0.0.1:8000
// Optioneel: PAD=/voorbeeld/strandboog/?gelegenheid=bruiloft
const { chromium } = require("playwright");
const [base] = process.argv.slice(2);
const pad = process.env.PAD || "/voorbeeld/strandboog/?gelegenheid=bruiloft";
const exe = process.env.CHROME;
let goed = 0, fout = 0;
const check = (naam, ok, extra) => { if (ok) goed++; else fout++; console.log((ok ? "  ok  " : "  FOUT ") + naam + (ok ? "" : "  -> " + JSON.stringify(extra))); };
const stand = (page) => page.evaluate(() => {
  const h = document.querySelector("[data-sb]"), v = document.querySelector("[data-sb-video]"), r = document.querySelector("[data-sb-v]"), o = document.querySelector("[data-sb-open]");
  return { klassen: [...h.classList].filter((c) => /^sb-(gate|speelt|tekst|klaar)$/.test(c)).sort().join(" "), bezig: document.documentElement.classList.contains("sb-bezig"),
    inert: document.querySelector(".sb-body").inert, paused: v.paused, t: +v.currentTime.toFixed(2), vZichtbaar: getComputedStyle(r).display !== "none", vRect: (() => { const b = r.getBoundingClientRect(); return [Math.round(b.left + b.width / 2), Math.round(b.top + b.height / 2), Math.round(b.width), Math.round(b.height)]; })(), openUit: o ? o.disabled : null,
    status: document.querySelector("[data-sb-status]").textContent, scrollY: Math.round(scrollY), focus: document.activeElement && (document.activeElement.hasAttribute("data-sb-bekijk") ? "bekijk" : document.activeElement.className),
    eindZichtbaar: +getComputedStyle(document.querySelector(".sb-eind")).opacity, tekstZichtbaar: getComputedStyle(document.querySelector("[data-sb-caption]")).visibility === "visible" };
});
async function nieuw(browser, opties = {}, init) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, ...opties });
  const page = await ctx.newPage(); const fouten = [];
  page.on("pageerror", (e) => fouten.push(e.message)); page.on("console", (m) => { if (m.type() === "error") fouten.push(m.text()); });
  if (init) await page.addInitScript(init);
  await page.goto(base + pad, { waitUntil: "load" }); await page.waitForTimeout(1000);
  return { ctx, page, fouten };
}
(async () => {
  const browser = await chromium.launch({ ...(exe ? { executablePath: exe } : {}), args: ["--autoplay-policy=no-user-gesture-required"] });

  console.log("1. Eerste bezoek: het doosje staat dicht, de pagina is vergrendeld");
  let { ctx, page, fouten } = await nieuw(browser);
  let s = await stand(page);
  check("poster met knop, vergrendeld en inhoud inert", s.klassen === "sb-gate" && s.bezig && s.inert && s.paused && s.t === 0 && !s.eindZichtbaar && !s.tekstZichtbaar, s);
  check("de film staat nog niet te spelen en laadt vooraf", await page.evaluate(() => document.querySelector("video").preload === "auto" && document.querySelector("video").paused));

  console.log("2. Tikken op het doosje: de film speelt, de pagina blijft vergrendeld tot de namen");
  await page.tap("[data-sb-open]"); await page.waitForTimeout(1500);
  s = await stand(page);
  check("film speelt (speelt, geen namen, knop uit)", s.klassen === "sb-speelt" && !s.paused && s.t > 0.5 && s.openUit === true && s.bezig && s.inert && !s.tekstZichtbaar, s);
  check("Opening overslaan heeft de focus en blijft zichtbaar", s.focus === "sb-skip" && (await page.locator("[data-sb-skip]").isVisible()), s);
  await page.evaluate(() => { document.querySelector("video").playbackRate = 8; });
  await page.waitForFunction(() => document.querySelector("[data-sb]").classList.contains("sb-tekst"), null, { timeout: 8000 });
  s = await stand(page);
  check("op 13,7 s: namen zichtbaar en pagina vrij terwijl de film nog loopt", s.klassen.includes("sb-tekst") && s.tekstZichtbaar && !s.bezig && !s.inert, s);
  await page.waitForFunction(() => document.querySelector("[data-sb]").classList.contains("sb-klaar"), null, { timeout: 8000 });
  s = await stand(page);
  check("na het einde: eindbeeld, namen, geen herhaling, de V is de bediening (grote onzichtbare tikvlak, geen zichtbare knop)", s.klassen === "sb-klaar" && s.paused && s.eindZichtbaar === 1 && s.tekstZichtbaar && s.vZichtbaar && s.vRect[2] >= 96 && s.vRect[3] >= 96 && !(await page.locator("[data-sb-skip]").isVisible()), s);
  check("de film herhaalt zichzelf niet", await page.evaluate(async () => { const v = document.querySelector("video"); await new Promise((r) => setTimeout(r, 1200)); return v.paused && !v.loop; }));

  console.log("3. Opnieuw beleven en overslaan");
  await page.click("[data-sb-v]"); await page.waitForTimeout(1700);
  s = await stand(page);
  check("opnieuw: film speelt, eindbeeld weg, vergrendeld, namen weg", s.klassen === "sb-speelt" && !s.paused && s.eindZichtbaar === 0 && s.bezig && !s.tekstZichtbaar, s);
  await page.click("[data-sb-skip]"); await page.waitForTimeout(500);
  s = await stand(page);
  check("overslaan: film stil op 0, eindbeeld en namen, pagina vrij, focus op Bekijk de uitnodiging", s.klassen === "sb-klaar" && s.paused && s.t === 0 && s.eindZichtbaar === 1 && !s.bezig && !s.inert && s.focus === "bekijk" && /overgeslagen/.test(s.status), s);
  await page.click("[data-sb-bekijk]"); await page.waitForTimeout(900);
  check("Bekijk de uitnodiging scrolt naar de inhoud", (await page.evaluate(() => scrollY)) > 300);
  check("geen scriptfouten of consolefouten", fouten.length === 0, fouten);
  await ctx.close();

  console.log("4. Toetsenbord");
  ({ ctx, page, fouten } = await nieuw(browser));
  await page.focus("[data-sb-open]"); await page.keyboard.press("Enter"); await page.waitForTimeout(900);
  s = await stand(page);
  check("Enter op het doosje start de film", s.klassen === "sb-speelt" && !s.paused, s);
  await page.keyboard.press("Enter"); await page.waitForTimeout(400);
  s = await stand(page);
  check("Enter op Opening overslaan (heeft de focus) zet het eindbeeld", s.klassen === "sb-klaar" && s.paused, s);
  await ctx.close();

  console.log("5. Terugkerende bezoeker en directe links");
  ({ ctx, page } = await nieuw(browser));
  await page.tap("[data-sb-open]"); await page.waitForTimeout(600); await page.click("[data-sb-skip]"); await page.waitForTimeout(300);
  await page.reload({ waitUntil: "load" }); await page.waitForTimeout(700);
  s = await stand(page);
  check("tweede keer in dezelfde sessie: direct het eindbeeld met namen, geen vergrendeling", s.klassen === "sb-klaar" && !s.bezig && !s.inert && s.eindZichtbaar === 1 && s.tekstZichtbaar && s.vZichtbaar, s);
  await ctx.close();
  ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true }); page = await ctx.newPage();
  await page.goto(base + pad + "#aanmelden", { waitUntil: "load" }); await page.waitForTimeout(900);
  check("een aanmeldlink (#aanmelden) opent direct", (await stand(page)).klassen === "sb-klaar");
  await ctx.close();

  console.log("6. Minder beweging en geblokkeerde of mislukte film");
  ({ ctx, page } = await nieuw(browser, { reducedMotion: "reduce" }));
  s = await stand(page);
  check("minder beweging: direct het eindbeeld, film stil, de V speelt de scène af", s.klassen === "sb-klaar" && s.paused && !s.bezig && s.eindZichtbaar === 1 && s.vZichtbaar, s);
  await ctx.close();
  ({ ctx, page } = await nieuw(browser, {}, () => { HTMLMediaElement.prototype.play = function () { return Promise.reject(new DOMException("blocked", "NotAllowedError")); }; }));
  await page.tap("[data-sb-open]"); await page.waitForTimeout(700);
  s = await stand(page);
  check("play() geweigerd: geen vastlopen, direct het eindbeeld en de pagina vrij", s.klassen === "sb-klaar" && !s.bezig && !s.inert && s.vZichtbaar, s);
  await ctx.close();

  console.log("7. Zonder JavaScript");
  ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false }); page = await ctx.newPage();
  await page.goto(base + pad, { waitUntil: "load" }); await page.waitForTimeout(500);
  check("eindbeeld en namen staan er, de knop om te openen niet", await page.evaluate(() => +getComputedStyle(document.querySelector(".sb-eind")).opacity === 1 && getComputedStyle(document.querySelector("[data-sb-caption]")).visibility === "visible" && getComputedStyle(document.querySelector("[data-sb-open]")).display === "none"));
  await ctx.close();

  console.log("8. Breedtes: geen horizontale scroll, de scène past in beeld");
  for (const [w, h] of [[360, 740], [390, 844], [768, 1024], [1366, 800]]) {
    ({ ctx, page } = await nieuw(browser, { viewport: { width: w, height: h } }));
    const m = await page.evaluate(() => { const b = document.querySelector(".sb-boog").getBoundingClientRect(), hero = document.querySelector(".sb-hero").getBoundingClientRect();
      return { over: document.documentElement.scrollWidth > innerWidth, boogPast: b.top >= hero.top - 1 && b.bottom <= hero.bottom + 1 && b.left >= 0 && b.right <= innerWidth, knop: document.querySelector("[data-sb-open]").getBoundingClientRect().height };
    });
    check(`${w}×${h}: geen overflow, de boog past, de knop is minstens 44 px hoog`, !m.over && m.boogPast && m.knop >= 44, m);
    await ctx.close();
  }
  await browser.close();
  console.log(`\n${goed} ok, ${fout} fout`);
  process.exit(fout ? 1 : 0);
})();

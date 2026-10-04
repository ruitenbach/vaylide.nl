// Gouden Avond: gedrag van de opening (toetsenbord, overslaan, opnieuw beleven, minder beweging, geblokkeerde autoplay, terugkerende bezoeker).
// Gebruik: node e2e/gouden_avond_functies.cjs <basis-url>   Optioneel: PAD=/voorbeeld/gouden-avond/?gelegenheid=bruiloft
const { chromium } = require("playwright");
const [base] = process.argv.slice(2);
const pad = process.env.PAD || "/voorbeeld/gouden-avond/?gelegenheid=bruiloft";
let goed = 0, fout = 0;
const check = (naam, ok, extra) => { if (ok) goed++; else fout++; console.log((ok ? "  ok  " : "  FOUT ") + naam + (ok ? "" : "  -> " + JSON.stringify(extra))); };
const stand = (page) => page.evaluate(() => {
  const h = document.querySelector("[data-bc]"), v = document.querySelector("[data-bc-video]"), r = document.querySelector("[data-bc-replay]");
  return { klaar: h.classList.contains("bc-klaar"), tekst: h.classList.contains("bc-text-visible"), opened: h.classList.contains("bc-opened"), aligning: h.classList.contains("bc-aligning"),
    deeltjes: document.querySelectorAll(".bc-spark").length, feestAan: document.querySelectorAll(".bc-spark--aan").length > 0, bezig: document.documentElement.classList.contains("bc-bezig"),
    inert: document.querySelector(".bc-body").inert, paused: v.paused, t: +v.currentTime.toFixed(2), replayTekst: r.hidden ? null : r.textContent, sleutelUit: document.querySelector("[data-bc-sleutel]").disabled,
    status: document.querySelector("[data-bc-status]").textContent, scrollY: Math.round(scrollY), focus: document.activeElement && (document.activeElement.getAttribute("data-bc-bekijk") !== null ? "bekijk" : document.activeElement.className) };
});
async function nieuw(browser, opties = {}, init) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, ...opties });
  const page = await ctx.newPage(); const fouten = [];
  page.on("pageerror", (e) => fouten.push(e.message)); page.on("console", (m) => { if (m.type() === "error") fouten.push(m.text()); });
  if (init) await page.addInitScript(init);
  await page.goto(base + pad, { waitUntil: "load" }); await page.waitForTimeout(1200);
  return { ctx, page, fouten };
}
(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });

  console.log("A. toetsenbord: Tab naar de sleutel, Enter, volledige opening, dan Bekijk de uitnodiging");
  { const { ctx, page, fouten } = await nieuw(browser);
    let s = await stand(page);
    check("vooraf: scroll vergrendeld, inhoud inert, tekst nog niet zichtbaar", s.bezig && s.inert && !s.tekst, s);
    for (let i = 0; i < 12; i++) { await page.keyboard.press("Tab"); const el = await page.evaluate(() => document.activeElement.hasAttribute("data-bc-sleutel")); if (el) break; }
    check("sleutel bereikbaar met Tab", await page.evaluate(() => document.activeElement.hasAttribute("data-bc-sleutel")));
    await page.keyboard.press("Enter"); await page.waitForTimeout(600);
    s = await stand(page); check("na Enter: sleutel uitgelijnd, status gemeld", s.aligning && /sleutel/i.test(s.status), s);
    await page.waitForTimeout(7200);
    s = await stand(page);
    check("na 7,8 s: klaar, tekst zichtbaar, scroll vrij, inhoud bruikbaar", s.klaar && s.tekst && !s.bezig && !s.inert, s);
    check("focus staat op Bekijk de uitnodiging", s.focus === "bekijk", s);
    check("video speelt of is afgelopen (geen blokkade)", s.t > 0 || !s.paused, s);
    await page.keyboard.press("Enter"); await page.waitForTimeout(1200);
    s = await stand(page); check("Enter op Bekijk de uitnodiging scrolt naar de inhoud", s.scrollY > 300, s);
    await page.waitForTimeout(4000);
    s = await stand(page); check("deeltjes na het feest verwijderd", s.deeltjes === 0 && !s.feestAan, s);
    check("geen consolefouten", fouten.length === 0, fouten); await ctx.close(); }

  console.log("B. Opening overslaan midden in de opening");
  { const { ctx, page, fouten } = await nieuw(browser);
    await page.locator("[data-bc-sleutel]").click(); await page.waitForTimeout(3300);
    let s = await stand(page); check("feest loopt (145 deeltjes) voor het overslaan", s.deeltjes === 145 && s.feestAan, s);
    await page.locator("[data-bc-skip]").click(); await page.waitForTimeout(150);
    s = await stand(page);
    check("direct klaar, feest gestopt, deeltjes weg, video gepauzeerd op 0", s.klaar && s.tekst && s.deeltjes === 0 && !s.feestAan && s.paused && s.t === 0, s);
    check("scroll vrij, inhoud bruikbaar, focus op Bekijk, status gemeld", !s.bezig && !s.inert && s.focus === "bekijk" && /overgeslagen/i.test(s.status), s);
    check("knop wordt 'Speel de scène af'", /Speel de sc/.test(s.replayTekst || ""), s);
    await page.waitForTimeout(8000);
    s = await stand(page); check("8 s later niets meer gestart (geen achterblijvende timers)", s.deeltjes === 0 && s.paused && s.t === 0, s);
    check("geen consolefouten", fouten.length === 0, fouten); await ctx.close(); }

  console.log("C. Overslaan vóór de sleutel is gebruikt");
  { const { ctx, page } = await nieuw(browser);
    await page.locator("[data-bc-skip]").click(); await page.waitForTimeout(150);
    const s = await stand(page); check("direct open scène zonder dat de sleutel nodig was", s.klaar && s.tekst && !s.bezig && s.deeltjes === 0, s); await ctx.close(); }

  console.log("D. Opnieuw beleven");
  { const { ctx, page, fouten } = await nieuw(browser);
    await page.locator("[data-bc-sleutel]").click(); await page.waitForTimeout(8500);
    let s = await stand(page); check("eerste keer klaar, knop 'Opnieuw beleven'", s.klaar && /Opnieuw/.test(s.replayTekst || ""), s);
    await page.locator("[data-bc-replay]").click(); await page.waitForTimeout(300);
    s = await stand(page);
    check("terug naar dicht: sleutel actief, scroll vergrendeld, deeltjes weg, video terug", !s.klaar && !s.opened && !s.sleutelUit && s.bezig && s.inert && s.deeltjes === 0 && s.t === 0 && s.paused, s);
    await page.locator("[data-bc-sleutel]").click(); await page.waitForTimeout(8500);
    s = await stand(page); check("tweede keer weer helemaal klaar", s.klaar && s.tekst && !s.bezig, s);
    check("geen consolefouten", fouten.length === 0, fouten); await ctx.close(); }

  console.log("E. Minder beweging");
  { const { ctx, page, fouten } = await nieuw(browser, { reducedMotion: "reduce" });
    let s = await stand(page);
    check("direct open: poster, tekst, geen deeltjes, geen vergrendeling", s.klaar && s.tekst && s.deeltjes === 0 && !s.bezig && !s.inert && s.paused, s);
    check("duidelijke bediening: 'Speel de scène af'", /Speel de sc/.test(s.replayTekst || ""), s);
    const anim = await page.evaluate(() => ({ trans: getComputedStyle(document.querySelector(".bc-door--l")).transitionDuration, key: getComputedStyle(document.querySelector("[data-bc-sleutel]")).display }));
    check("geen deurovergang, sleutel niet getoond", anim.trans === "0s" && anim.key === "none", anim);
    await page.locator("[data-bc-replay]").click(); await page.waitForTimeout(1500);
    s = await stand(page); check("video handmatig af te spelen", !s.paused || s.t > 0, s);
    check("geen consolefouten", fouten.length === 0, fouten); await ctx.close(); }

  console.log("F. Autoplay geblokkeerd");
  { const { ctx, page, fouten } = await nieuw(browser, {}, () => { window.__echt = HTMLMediaElement.prototype.play; HTMLMediaElement.prototype.play = function () { return window.__blok ? Promise.reject(new DOMException("blocked", "NotAllowedError")) : window.__echt.call(this); }; window.__blok = true; });
    await page.locator("[data-bc-sleutel]").click(); await page.waitForTimeout(8000);
    let s = await stand(page);
    check("opening loopt door tot klaar zonder fout", s.klaar && s.tekst && fouten.length === 0, { s, fouten });
    check("knop biedt 'Speel de scène af' aan", /Speel de sc/.test(s.replayTekst || "") && s.paused, s);
    await page.evaluate(() => { window.__blok = false; });
    await page.locator("[data-bc-replay]").click(); await page.waitForTimeout(1500);
    s = await stand(page); check("na een tik op de knop speelt de video", !s.paused && s.t > 0, s);
    await ctx.close(); }

  console.log("G. Terugkerende bezoeker (zelfde sessie)");
  { const { ctx, page } = await nieuw(browser);
    await page.locator("[data-bc-skip]").click(); await page.waitForTimeout(300);
    await page.reload({ waitUntil: "load" }); await page.waitForTimeout(800);
    const s = await stand(page); check("na herladen direct de open scène, geen vergrendeling", s.klaar && s.tekst && !s.bezig && !s.inert && s.deeltjes === 0, s); await ctx.close(); }

  console.log("H. Beweging stilgezet tijdens de opening");
  { const { ctx, page } = await nieuw(browser);
    await page.locator("[data-bc-sleutel]").click(); await page.waitForTimeout(3300);
    await page.locator(".fx-toggle, [data-fx-toggle]").first().click().catch(() => {}); await page.waitForTimeout(400);
    const s = await stand(page); check("stilzetten beëindigt de opening en het feest", s.klaar && s.deeltjes === 0, s); await ctx.close(); }

  console.log("I. Aanmeld-link (#aanmelden) slaat de opening over");
  { const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } }); const page = await ctx.newPage();
    await page.goto(base + pad + "#aanmelden", { waitUntil: "load" }); await page.waitForTimeout(800);
    const s = await stand(page); check("direct open, inhoud bruikbaar", s.klaar && !s.bezig && !s.inert, s); await ctx.close(); }

  await browser.close();
  console.log(`\n${goed} geslaagd, ${fout} mislukt`);
  process.exit(fout ? 1 : 0);
})();

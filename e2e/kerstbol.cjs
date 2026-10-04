// Kerstbol: de opening in een echte browser (stappen, overslaan, opnieuw beleven, minder beweging, terugkerende bezoeker) en een rondgang langs de kaart.
// Gebruik: node e2e/kerstbol.cjs <basis-url> [label]   Optioneel: VIEWPORTS=390,1366  PAD=/voorbeeld/kerstbol/?gelegenheid=kerst  KORT=1 (alleen de stappen, geen gedragstests)
// Schermafbeeldingen: voorvertoning-kerstbol/<label>-<breedte>-<stap>.png (niet in Git).
const { chromium } = require("playwright"); const fs = require("fs"); const path = require("path");
const [base, label = "k"] = process.argv.slice(2);
const pad = process.env.PAD || "/voorbeeld/kerstbol/?gelegenheid=kerst";
const uit = path.join(__dirname, "..", "voorvertoning-kerstbol"); fs.mkdirSync(uit, { recursive: true });
let goed = 0, fout = 0;
const check = (naam, ok, extra) => { if (ok) goed++; else fout++; console.log((ok ? "  ok  " : "  FOUT ") + naam + (ok ? "" : "  -> " + JSON.stringify(extra))); };
const stand = (p) => p.evaluate(() => { const h = document.querySelector("[data-kb]"), v = document.querySelector("[data-kb-video]"), r = document.querySelector("[data-kb-replay]");
  return { klassen: h.className.replace(/kb-hero\s*/, ""), glinten: document.querySelectorAll(".kb-glint").length, goud: document.querySelectorAll(".kb-glint--goud").length, kristal: document.querySelectorAll(".kb-glint--kristal").length,
    bezig: document.documentElement.classList.contains("kb-bezig"), inert: document.querySelector(".kb-body").inert, paused: v.paused, t: +v.currentTime.toFixed(1), replay: r.hidden ? null : r.textContent.trim(), status: document.querySelector("[data-kb-status]").textContent,
    scrollBreedte: document.documentElement.scrollWidth, vw: innerWidth, preload: v.preload }; });
async function nieuw(browser, w, opties = {}, init) {
  const ctx = await browser.newContext({ viewport: { width: w, height: w < 800 ? 844 : 768 }, hasTouch: w < 800, ...opties }); const p = await ctx.newPage(); const fouten = [];
  p.on("pageerror", (e) => fouten.push(e.message)); p.on("console", (m) => { if (m.type() === "error") fouten.push(m.text()); });
  if (init) await p.addInitScript(init);
  await p.goto(base + pad, { waitUntil: "load" }); await p.waitForTimeout(1500);
  return { ctx, p, fouten };
}
(async () => {
  const browser = await chromium.launch({ args: ["--autoplay-policy=no-user-gesture-required"] });
  for (const w of (process.env.VIEWPORTS || "390,1366").split(",").map(Number)) {
    console.log(`\n== ${w} px`);
    { const { ctx, p, fouten } = await nieuw(browser, w);
      const shot = (n) => p.screenshot({ path: path.join(uit, `${label}-${w}-${n}.png`) });
      let s = await stand(p);
      check("dicht: cadeau-poster, 40 gouden fonkelingen, geen video, scroll vergrendeld, inhoud inert", s.goud === 40 && s.kristal === 0 && s.paused && s.t === 0 && s.bezig && s.inert && !/kb-finished/.test(s.klassen), s);
      await shot("0-dicht");
      const zicht = await p.evaluate(() => { const b = document.querySelector("[data-kb-open]").getBoundingClientRect(); return { b: Math.round(b.width), h: Math.round(b.height) }; });
      check("klikdoel minstens 44 px", zicht.b >= 44 && zicht.h >= 44, zicht);
      await p.locator("[data-kb-open]").click(); const t0 = Date.now();
      for (const [ms, n] of [[1500, "1"], [3000, "2"], [4500, "3"], [6000, "4"], [7200, "5"], [8500, "6"], [10300, "7"], [12000, "8"]]) { await p.waitForTimeout(Math.max(0, ms - (Date.now() - t0))); await shot(n);
        if (n === "1") { s = await stand(p); check("na de tik: video speelt, nog gouden fonkelingen", !s.paused && /kb-playing/.test(s.klassen) && s.goud === 40 && s.kristal === 0, s); }
        if (n === "5") { s = await stand(p); check("na 6,5 s: gouden fonkelingen weg, 55 kristallen", s.goud === 0 && s.kristal === 55 && /kb-afterglow/.test(s.klassen), s); } }
      s = await stand(p);
      check("na afloop: groet zichtbaar, scroll vrij, fonkelingen verwijderd, geen horizontale scroll", /kb-finished/.test(s.klassen) && /kb-klaar/.test(s.klassen) && !s.bezig && !s.inert && s.glinten === 0 && s.scrollBreedte <= s.vw, s);
      check("knop 'Opnieuw beleven'", /Opnieuw beleven/.test(s.replay || ""), s);
      check("geen consolefouten", fouten.length === 0, fouten);
      await ctx.close(); }
    if (process.env.KORT) continue;

    console.log(" - overslaan midden in de opening");
    { const { ctx, p, fouten } = await nieuw(browser, w);
      await p.locator("[data-kb-open]").click(); await p.waitForTimeout(3000);
      await p.locator("[data-kb-skip]").click(); await p.waitForTimeout(250);
      let s = await stand(p);
      check("direct het eindbeeld met groet, video gestopt, fonkelingen weg, scroll vrij", /kb-eind/.test(s.klassen) && /kb-finished/.test(s.klassen) && s.paused && s.t === 0 && s.glinten === 0 && !s.bezig && !s.inert, s);
      check("status gemeld en knop 'Speel de opening af'", /overgeslagen/i.test(s.status) && /Speel de opening af/.test(s.replay || ""), s);
      await p.screenshot({ path: path.join(uit, `${label}-${w}-skip.png`) });
      await p.waitForTimeout(7000); s = await stand(p); check("7 s later niets meer gestart", s.paused && s.glinten === 0, s);
      check("geen consolefouten", fouten.length === 0, fouten); await ctx.close(); }

    console.log(" - overslaan vóór de tik");
    { const { ctx, p } = await nieuw(browser, w); await p.locator("[data-kb-skip]").click(); await p.waitForTimeout(250);
      const s = await stand(p); check("direct open", /kb-eind/.test(s.klassen) && !s.bezig && s.glinten === 0, s); await ctx.close(); }

    console.log(" - opnieuw beleven");
    { const { ctx, p, fouten } = await nieuw(browser, w);
      await p.locator("[data-kb-open]").click(); await p.waitForTimeout(11800);
      await p.locator("[data-kb-replay]").click(); await p.waitForTimeout(400);
      let s = await stand(p); check("terug naar dicht: 40 gouden, video op 0, vergrendeld", s.goud === 40 && s.kristal === 0 && s.paused && s.t === 0 && s.bezig && !/kb-finished/.test(s.klassen), s);
      await p.locator("[data-kb-open]").click(); await p.waitForTimeout(11800); s = await stand(p);
      check("tweede keer helemaal door", /kb-finished/.test(s.klassen) && s.glinten === 0 && !s.bezig, s);
      check("geen consolefouten", fouten.length === 0, fouten); await ctx.close(); }

    console.log(" - toetsenbord");
    { const { ctx, p } = await nieuw(browser, w);
      for (let i = 0; i < 6; i++) { await p.keyboard.press("Tab"); if (await p.evaluate(() => document.activeElement.hasAttribute("data-kb-open"))) break; }
      check("cadeau bereikbaar met Tab", await p.evaluate(() => document.activeElement.hasAttribute("data-kb-open")));
      await p.keyboard.press("Enter"); await p.waitForTimeout(11800); const s = await stand(p);
      check("Enter start de opening en eindigt netjes, focus op 'Naar de kaart'", /kb-finished/.test(s.klassen) && await p.evaluate(() => document.activeElement.hasAttribute("data-kb-scroll")), s); await ctx.close(); }

    console.log(" - minder beweging");
    { const { ctx, p, fouten } = await nieuw(browser, w, { reducedMotion: "reduce" });
      let s = await stand(p); check("direct het eindbeeld, geen fonkelingen, geen video, niet vergrendeld", /kb-eind/.test(s.klassen) && s.glinten === 0 && s.paused && !s.bezig && !s.inert, s);
      check("duidelijke bediening: 'Speel de opening af'", /Speel de opening af/.test(s.replay || ""), s);
      await p.screenshot({ path: path.join(uit, `${label}-${w}-rustig.png`) });
      await p.locator("[data-kb-replay]").click(); await p.waitForTimeout(11500); s = await stand(p);
      check("handmatig afspelen werkt zonder fonkelingen", /kb-finished/.test(s.klassen) && s.glinten === 0, s);
      check("geen consolefouten", fouten.length === 0, fouten); await ctx.close(); }

    console.log(" - geblokkeerde autoplay");
    { const { ctx, p } = await nieuw(browser, w, {}, () => { const echt = HTMLMediaElement.prototype.play; window.__blok = true; HTMLMediaElement.prototype.play = function () { return window.__blok ? Promise.reject(new DOMException("blocked", "NotAllowedError")) : echt.call(this); }; });
      await p.locator("[data-kb-open]").click(); await p.waitForTimeout(600);
      let zichtbaar = await p.evaluate(() => !document.querySelector("[data-kb-fallback]").hidden);
      check("fallbackknop verschijnt", zichtbaar);
      await p.evaluate(() => { window.__blok = false; }); await p.locator("[data-kb-fallback]").click(); await p.waitForTimeout(1500);
      const s = await stand(p); check("daarna speelt de video", !s.paused && /kb-playing/.test(s.klassen), s); await ctx.close(); }

    console.log(" - terugkerende bezoeker en aanmeldlink");
    { const { ctx, p } = await nieuw(browser, w); await p.locator("[data-kb-skip]").click(); await p.waitForTimeout(300);
      await p.reload({ waitUntil: "load" }); await p.waitForTimeout(800); const s = await stand(p);
      check("na herladen direct het eindbeeld", /kb-eind/.test(s.klassen) && !s.bezig && !s.inert, s);
      const c2 = await browser.newContext({ viewport: { width: w, height: 800 } }); const p2 = await c2.newPage();
      await p2.goto(base + pad + "#aanmelden", { waitUntil: "load" }); await p2.waitForTimeout(600);
      check("#aanmelden slaat de opening over", /kb-eind/.test((await stand(p2)).klassen)); await c2.close(); await ctx.close(); }

    console.log(" - rondgang langs de kaart");
    { const { ctx, p, fouten } = await nieuw(browser, w); await p.locator("[data-kb-skip]").click(); await p.waitForTimeout(800);
      const hoogte = await p.evaluate(() => document.documentElement.scrollHeight); const h = w < 800 ? 844 : 768; let n = 0;
      for (let y = 0; y < hoogte; y += h - 60) { await p.evaluate((y) => scrollTo({ top: y, behavior: "instant" }), y); await p.waitForTimeout(800); await p.screenshot({ path: path.join(uit, `${label}-${w}-kaart-${String(n++).padStart(2, "0")}.png`) }); }
      const breed = await p.evaluate(() => document.documentElement.scrollWidth > innerWidth);
      check(`rondgang (${n} schermen, hoogte ${hoogte}): geen horizontale scroll`, !breed); check("geen consolefouten", fouten.length === 0, fouten); await ctx.close(); }
  }
  await browser.close();
  console.log(`\n${goed} geslaagd, ${fout} mislukt`); process.exit(fout ? 1 : 0);
})();

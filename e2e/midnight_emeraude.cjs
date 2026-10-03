// Midnight Émeraude (GSAP-trouwontwerp): beelden van de opening en de uitnodiging, plus controles.
// Gebruik (vanuit de projectmap): node e2e/midnight_emeraude.cjs <basis-url> <uitvoermap>   Optioneel: VIEWPORTS=390,1366 PALETTE=midnight
// De opening is één GSAP-master-timeline; de beelden worden op vaste tijdstippen van die timeline genomen (window.vaylideMidnight.master),
// zodat ze op elke computer hetzelfde zijn. Controles: geen consolefouten, geen horizontale scroll, de opening eindigt met de namen in beeld,
// 'minder beweging' opent zonder film, en alle scrollhoofdstukken zijn zichtbaar nadat erdoor gescrold is.
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const [base, outDir] = process.argv.slice(2);
const only = (process.env.VIEWPORTS || "").split(",").filter(Boolean);
const palette = process.env.PALETTE || "";
const viewports = [
  { name: "360", width: 360, height: 740, touch: true },
  { name: "390", width: 390, height: 844, touch: true },
  { name: "768", width: 768, height: 1024, touch: true },
  { name: "1366", width: 1366, height: 768, touch: false },
].filter((vp) => !only.length || only.includes(vp.name));
const URL_ = `${base}/voorbeeld/midnight-emeraude/?gelegenheid=bruiloft${palette ? `&kleur=${palette}` : ""}`;
const INTRO = [["01-donker", 0.4], ["02-licht", 1.4], ["03-envelop", 2.3], ["04-zegel-glans", 2.9], ["05-wacht-op-tik", 3.3]];
const OPEN = [["06-zegel-breekt", 0.55], ["07-flap-open", 1.2], ["08-kaart-uit", 2.2], ["09-kaart-naar-voren", 2.85], ["10-camera-in", 3.3], ["11-camera-dichtbij", 3.8], ["12-kaart-lost-op", 4.2], ["13-wereld-verschijnt", 4.7]];
const HERO = [["14-ringen-en-namen", 5.8], ["15-film-klaar", 7.8]];

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  const problems = [];
  for (const vp of viewports) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: vp.width < 800 ? 2 : 1, hasTouch: vp.touch });
    const page = await ctx.newPage();
    const errors = [];
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    page.on("pageerror", (e) => errors.push(String(e)));
    await page.goto(URL_, { waitUntil: "load" });
    await page.evaluate(() => document.fonts.ready);
    const tag = `midnight-emeraude-${vp.name}${palette ? "-" + palette : ""}`;
    await page.waitForFunction(() => !!(window.vaylideMidnight && window.vaylideMidnight.master), null, { timeout: 8000 });
    // het onzichtbare opwarmen moet klaar zijn (anders loopt het door onze tijdstippen heen)
    await page.waitForFunction(() => performance.getEntriesByName("me:opwarmen-klaar").length > 0, null, { timeout: 15000 });
    const TIK = await page.evaluate(() => window.vaylideMidnight.master.labels.tik);
    // intro: de timeline loopt vanzelf; we zetten hem stil op vaste tijden
    for (const [name, t] of INTRO) {
      await page.evaluate((x) => { window.vaylideMidnight.master.pause().time(x); }, t);
      await page.waitForTimeout(120);
      await page.screenshot({ path: path.join(outDir, `${tag}-${name}.png`) });
    }
    if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) problems.push(`${tag}: horizontale scroll (opening)`);
    // tik op het zegel: de opening loopt; daarna op vaste tijden stilzetten (tijden zijn relatief aan de tik, 4,4 s in de timeline)
    const hit = page.locator(".me-cover .vx-seal-hit");
    await page.evaluate((k) => { window.vaylideMidnight.master.pause().time(k); }, TIK);
    if (vp.touch) await hit.tap({ force: true }); else await hit.click({ force: true });
    for (const [name, t] of [...OPEN, ...HERO]) {
      await page.evaluate(([x, k]) => { window.vaylideMidnight.master.pause().time(k + x); }, [t, TIK]);
      await page.waitForTimeout(140);
      await page.screenshot({ path: path.join(outDir, `${tag}-${name}.png`) });
    }
    await page.evaluate(() => { window.vaylideMidnight.master.progress(1); });
    await page.waitForFunction(() => document.documentElement.classList.contains("is-open"), null, { timeout: 9000 });
    await page.waitForTimeout(600);
    const state = await page.evaluate(() => ({
      coverHidden: document.querySelector("[data-cover]").hidden,
      names: (() => { const r = document.querySelector(".me-names").getBoundingClientRect(); return r.top >= 0 && r.bottom < innerHeight; })(),
      nameOpacity: getComputedStyle(document.querySelector(".me-naam__in")).opacity,
    }));
    if (!state.coverHidden) problems.push(`${tag}: openingsscherm blijft staan`);
    if (!state.names) problems.push(`${tag}: namen niet in beeld na de opening`);
    await page.screenshot({ path: path.join(outDir, `${tag}-16-hero-na-opening.png`) });
    // door de hele uitnodiging scrollen en beelden maken van de hoofdstukken
    const stops = await page.evaluate(() => Array.from(document.querySelectorAll(".me-sec")).map((s) => ({ cls: s.className.split(" ").find((c) => /^me-(?!sec)/.test(c)), top: s.getBoundingClientRect().top + scrollY, h: s.offsetHeight })));
    let i = 0;
    for (const s of stops) {
      i++;
      const y = Math.max(0, s.top - 40);
      await page.evaluate(async (yy) => { const step = 220; let c = scrollY; while (c < yy) { c = Math.min(yy, c + step); scrollTo(0, c); await new Promise((r) => setTimeout(r, 45)); } scrollTo(0, yy); }, y);
      await page.waitForTimeout(1900);
      await page.screenshot({ path: path.join(outDir, `${tag}-s${String(i).padStart(2, "0")}-${s.cls}.png`) });
    }
    await page.evaluate(() => scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(1800);
    await page.screenshot({ path: path.join(outDir, `${tag}-z-onderkant.png`) });
    if (await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)) problems.push(`${tag}: horizontale scroll (uitnodiging)`);
    // alles wat onthuld wordt, is nu zichtbaar
    const hidden = await page.evaluate(() => Array.from(document.querySelectorAll(".me-fade")).filter((e) => Number(getComputedStyle(e).opacity) < 0.95).length);
    if (hidden) problems.push(`${tag}: ${hidden} .me-fade-elementen niet zichtbaar na scrollen`);
    if (errors.length) problems.push(`${tag}: consolefouten: ${errors.join(" | ")}`);
    await ctx.close();
  }
  // minder beweging: geen film, direct bruikbaar
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce" });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto(URL_, { waitUntil: "load" });
  const rm = await page.evaluate(() => ({ master: !!(window.vaylideMidnight), stage: getComputedStyle(document.querySelector(".me-cover .vx-stage")).opacity }));
  if (rm.master) problems.push("minder beweging: er is toch een master-timeline gebouwd");
  await page.locator(".me-cover .vx-seal-hit").click({ force: true });
  await page.waitForFunction(() => document.documentElement.classList.contains("is-open"), null, { timeout: 3000 });
  const names = await page.evaluate(() => ({ y: document.querySelector(".me-names").getBoundingClientRect().top, o: getComputedStyle(document.querySelector(".me-naam__in")).transform }));
  await page.screenshot({ path: path.join(outDir, "midnight-emeraude-390-minder-beweging.png") });
  if (names.o !== "none") problems.push("minder beweging: namen staan niet in rust (" + names.o + ")");
  if (errors.length) problems.push("minder beweging: " + errors.join(" | "));
  await ctx.close();
  await browser.close();
  console.log(problems.length ? "PROBLEMEN:\n" + problems.join("\n") : "Alles in orde.");
  process.exit(problems.length ? 1 : 0);
})();

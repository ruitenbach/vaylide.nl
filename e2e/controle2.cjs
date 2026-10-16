// Controle 2: vormgeving en gebruik in de browser (Playwright).
// Gebruik (vanuit de projectmap): node e2e/controle2.cjs <basis-url> <fixtures.json> <uitvoermap> <beheerwachtwoord>
// Optioneel, om het werk te verdelen over parallelle runs:
//   VIEWPORTS=360,390   alleen deze schermformaten
//   CHECKS=0            geen gedragscontroles (minder beweging, toetsenbord, muziek, vangnet, tijdzone, zonder JS)
//   SHOTS=viewport      schermafbeelding van het zichtbare deel in plaats van de hele pagina (scheelt veel ruimte)
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const [base, fixturesFile, outDir, staffPassword] = process.argv.slice(2);
const fixtures = JSON.parse(fs.readFileSync(fixturesFile, "utf8"));
const onlyViewports = (process.env.VIEWPORTS || "").split(",").filter(Boolean);
const runChecks = process.env.CHECKS !== "0";
const fullShots = process.env.SHOTS !== "viewport";
const viewports = [
  { name: "360", width: 360, height: 740 },
  { name: "390", width: 390, height: 844 },
  { name: "768", width: 768, height: 1024 },
  { name: "1366", width: 1366, height: 900 },
].filter((vp) => !onlyViewports.length || onlyViewports.includes(vp.name));
// Alle ontwerpen uit designs/ (mappen die met _ beginnen zijn gedeelde onderdelen).
const designs = fs.readdirSync(path.join(process.cwd(), "designs")).filter((d) => !d.startsWith("_")).sort();
const report = { pages: [], checks: [] };

async function scrollThrough(page) {
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo({ top: y, behavior: "instant" }); await new Promise(r => setTimeout(r, 40)); }
    window.scrollTo({ top: 0, behavior: "instant" });
  });
  await page.waitForTimeout(700);
  // Wachten tot eenmalige animaties (onthullen, na elkaar invloeien) klaar zijn; doorlopende tellen niet mee.
  await page.waitForFunction(() => document.getAnimations().every((a) => a.playState !== "running" || a.effect.getTiming().iterations === Infinity), null, { timeout: 6000 }).catch(() => {});
}

async function audit(page, vp, name, url, { open = false, full = fullShots } = {}) {
  const errors = [];
  const failed = [];
  const onError = (e) => errors.push(String(e));
  const onConsole = (m) => { if (m.type() === "error") errors.push(m.text()); };
  const onResponse = (r) => { if (r.status() >= 400 && !r.url().includes("favicon")) failed.push(`${r.status()} ${r.url().replace(base, "")}`); };
  page.on("pageerror", onError); page.on("console", onConsole); page.on("response", onResponse);
  const response = await page.goto(base + url, { waitUntil: "networkidle" });
  // Na het openen wachten tot de entree van de kop klaar is (effects.js zet dan 'fx-done').
  // Na 3,3 s zijn de meeste openingen klaar; een opening als film (Rozenboog) duurt ruim 11 s.
  if (open && await page.$("[data-open]")) { await page.click("[data-open]", { force: true }); await page.waitForTimeout(3300); await page.waitForFunction(() => document.documentElement.classList.contains("is-open"), null, { timeout: 20000 }).catch(() => {}); await page.waitForFunction(() => !document.documentElement.classList.contains("fx") || document.documentElement.classList.contains("fx-done"), null, { timeout: 10000 }).catch(() => {}); await page.waitForTimeout(300); }
  await scrollThrough(page);
  const metrics = await page.evaluate(() => {
    const doc = document.documentElement;
    const overflowing = [];
    document.querySelectorAll("body *").forEach((el) => {
      const r = el.getBoundingClientRect();
      const style = getComputedStyle(el);
      if (style.position === "fixed" || r.width === 0 || style.visibility === "hidden") return;
      // Niet getoond (bijv. inhoud van een gesloten menu) telt niet mee.
      if (typeof el.checkVisibility === "function" && !el.checkVisibility()) return;
      // Bewust bijgesneden of in een eigen scrollrij (foto's met zoom, veegrij met ontwerpen) telt niet mee.
      for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
        const ox = getComputedStyle(a).overflowX;
        if (["hidden", "clip", "auto", "scroll"].includes(ox) && a.getBoundingClientRect().right <= doc.clientWidth + 1) return;
      }
      if (r.right > doc.clientWidth + 1 && !el.closest(".data-table-wrap, .beheer-nav, .preview-frame, pre")) overflowing.push(`${el.tagName.toLowerCase()}.${(el.className || "").toString().split(" ")[0]} → ${Math.round(r.right)}px`);
    });
    // Tekst die buiten beeld loopt, ook als een omringend vak hem afsnijdt (bijv. een lang woord in een titel).
    const clipped = [];
    const vw = doc.clientWidth;
    document.querySelectorAll("body *").forEach((el) => {
      if (![...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim().length > 1)) return;
      if (el.closest("[aria-hidden='true'], .visually-hidden, script, style, noscript")) return;
      if (typeof el.checkVisibility === "function" && !el.checkVisibility({ opacityProperty: true, visibilityProperty: true })) return;
      const r = el.getBoundingClientRect();
      if (r.width <= 1 || r.height <= 1) return;  // verborgen voor het oog, alleen voor schermlezers
      if (r.right <= 0 || r.left >= vw) return;  // bewust buiten beeld geplaatst (zoals het spamveld)
      for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
        const ox = getComputedStyle(a).overflowX;
        if (ox === "auto" || ox === "scroll") return;  // eigen scrollrij
      }
      // Alleen de eigen tekst meten (verborgen hulptekst voor schermlezers in een kind telt niet mee).
      let left = Infinity, right = -Infinity;
      for (const n of el.childNodes) {
        if (n.nodeType !== 3 || !n.textContent.trim()) continue;
        const range = document.createRange();
        range.selectNodeContents(n);
        for (const q of range.getClientRects()) { if (q.width) { left = Math.min(left, q.left); right = Math.max(right, q.right); } }
      }
      const t = { left, right };
      if (right > vw + 1 || left < -1) clipped.push(`${el.tagName.toLowerCase()}.${(el.className || "").toString().split(" ")[0]} "${el.textContent.trim().slice(0, 30)}" ${Math.round(t.left)}–${Math.round(t.right)}px`);
    });
    return { overflow: doc.scrollWidth - doc.clientWidth, overflowing: overflowing.slice(0, 5), clipped: clipped.slice(0, 5) };
  });
  const dir = path.join(outDir, vp.name);
  fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${name}.png`);
  await page.screenshot({ path: file, fullPage: full });
  page.off("pageerror", onError); page.off("console", onConsole); page.off("response", onResponse);
  const status = response ? response.status() : 0;
  if (name === "404" && status === 404) {
    // De 404-status van de pagina zelf is hier juist de bedoeling.
    const own = failed.indexOf(`404 ${url}`);
    if (own !== -1) failed.splice(own, 1);
    const msg = errors.findIndex((e) => e.includes("status of 404"));
    if (msg !== -1) errors.splice(msg, 1);
  }
  const entry = { viewport: vp.name, name, url, status, overflow: metrics.overflow, overflowing: metrics.overflowing, clipped: metrics.clipped, errors, failed, file };
  report.pages.push(entry);
  const flag = (entry.overflow > 0 || entry.overflowing.length || entry.clipped.length || entry.errors.length || entry.failed.length || (entry.status >= 400 && name !== "404")) ? "LET OP" : "ok";
  console.log(`${flag} [${vp.name}] ${name} status=${entry.status} overflow=${entry.overflow} errors=${entry.errors.length} failed=${entry.failed.length}${entry.clipped.length ? " tekst-buiten-beeld: " + entry.clipped.join("; ") : ""}`);
  return entry;
}

async function loginCustomer(context) {
  // Parallelle runs vragen voor hetzelfde account een code aan; een nieuwere code maakt de vorige ongeldig.
  // Daarom maximaal drie pogingen, telkens met een verse code.
  const page = await context.newPage();
  for (let attempt = 1; attempt <= 3; attempt++) {
    await page.goto(base + "/inloggen/");
    await page.fill("#id_email", "controle@vierlief.test");
    await page.click("button[type=submit]");
    const code = (await page.textContent(".test-code")).trim();
    await page.fill("#id_code", code);
    await page.click("button[type=submit]");
    try {
      await page.waitForURL("**/account/**", { timeout: 10000 });
      break;
    } catch (e) {
      if (attempt === 3) throw e;
      await page.waitForTimeout(1000 * attempt);
    }
  }
  await page.close();
}

async function loginStaff(context) {
  const page = await context.newPage();
  await page.goto(base + "/beheer/inloggen/");
  await page.fill("#id_username", "controle-beheer@vierlief.test");
  await page.fill("#id_password", staffPassword);
  await page.click("button[type=submit]");
  await page.waitForURL(base + "/beheer/");
  await page.close();
}

(async () => {
  const browser = await chromium.launch();
  const publicPages = [
    ["home", "/"], ["ontwerpen", "/ontwerpen/"], ["ontwerpen-zakelijk", "/ontwerpen/?gelegenheid=zakelijk"],
    ["ontwerp-detail", "/ontwerpen/liefde-op-papier/"], ["zo-werkt-het", "/zo-werkt-het/"], ["prijzen", "/prijzen/"],
    ["faq", "/veelgestelde-vragen/"], ["contact", "/contact/"], ["privacy", "/privacy/"], ["voorwaarden", "/voorwaarden/"],
    ["inspiratie", "/inspiratie/"], ["over-ons", "/over-ons/"], ["zoeken", "/zoeken/?q=muziek"], ["zoeken-leeg", "/zoeken/?q=zzzz"], ["inloggen", "/inloggen/"],
    ["maken", "/maken/"], ["maken-bruiloft", "/maken/?gelegenheid=bruiloft"], ["404", "/bestaat-niet/"],
  ];
  for (const vp of viewports) {
    const context = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, locale: "nl-NL", timezoneId: "Europe/Amsterdam" });
    const page = await context.newPage();
    for (const [name, url] of publicPages) await audit(page, vp, name, url);
    for (const slug of designs) {
      await page.evaluate(() => { try { sessionStorage.clear(); } catch (e) {} });
      await audit(page, vp, `demo-${slug}`, `/voorbeeld/${slug}/`, { open: true });
    }
    for (const [key, url] of Object.entries(fixtures)) {
      await page.evaluate(() => { try { sessionStorage.clear(); } catch (e) {} });
      await audit(page, vp, `u-${key.replace(":", "-")}`, url, { open: true });
    }
    // Klantomgeving en samenstellen.
    await loginCustomer(context);
    await audit(page, vp, "portal-home", "/account/");
    const firstUrl = Object.values(fixtures)[0];
    await page.goto(base + "/account/");
    const invLink = await page.getAttribute("a.item__title", "href");
    const uid = (await page.$$eval("a[href*='/account/uitnodiging/']", (as) => as.map(a => a.getAttribute("href"))))[0].split("/")[3];
    await audit(page, vp, "portal-uitnodiging", `/account/uitnodiging/${uid}/`);
    await audit(page, vp, "portal-gasten", `/account/uitnodiging/${uid}/gasten/`);
    await audit(page, vp, "portal-wensen-nieuw", "/account/wensen/nieuw/");
    await audit(page, vp, "portal-gegevens", "/account/gegevens/");
    for (const step of ["ontwerp", "gegevens", "programma", "aanmelden", "fotos", "stijl", "voorbeeld"]) {
      await audit(page, vp, `studio-${step}`, `/maken/${uid}/${step}/`);
    }
    await context.close();
    // Beheer.
    const staff = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, locale: "nl-NL", timezoneId: "Europe/Amsterdam" });
    await loginStaff(staff);
    const sp = await staff.newPage();
    for (const [name, url] of [["beheer-overzicht", "/beheer/"], ["beheer-bestellingen", "/beheer/bestellingen/"], ["beheer-uitnodigingen", "/beheer/uitnodigingen/"],
      ["beheer-uitnodiging", `/beheer/uitnodigingen/${uid}/`], ["beheer-wensen", "/beheer/wensen/?status="], ["beheer-verwerking", "/beheer/verwerking/"],
      ["beheer-prijzen", "/beheer/prijzen/"], ["beheer-ontwerpen", "/beheer/ontwerpen/"], ["beheer-instellingen", "/beheer/instellingen/"]]) {
      await audit(sp, vp, name, url);
    }
    await staff.close();
  }

  // ---- Gedragscontroles op telefoonformaat ----
  const check = (name, ok, detail) => { report.checks.push({ name, ok, detail }); console.log(`${ok ? "ok    " : "FOUT  "} ${name}: ${detail}`); };
  // Per ontwerp: minder beweging, toetsenbord, muziek, script dat niet laadt en een andere tijdzone.
  for (const slug of runChecks ? designs : []) {
    const demo = `/voorbeeld/${slug}/`;
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce" });
      const p = await ctx.newPage();
      await p.goto(base + demo, { waitUntil: "networkidle" });
      const t0 = Date.now();
      await p.click("[data-open]", { force: true });
      await p.waitForFunction(() => document.documentElement.classList.contains("is-open"), null, { timeout: 3000 });
      const ms = Date.now() - t0;
      await p.waitForTimeout(400);
      const running = await p.evaluate(() => document.getAnimations().filter((a) => a.playState === "running").length);
      check(`${slug} · Minder beweging: opening`, ms < 1000 && running === 0, `geopend na ${ms} ms, lopende animaties: ${running}`);
      await p.screenshot({ path: path.join(outDir, `check-reduced-motion-${slug}.png`) });
      await ctx.close();
    }
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
      const p = await ctx.newPage();
      await p.goto(base + demo, { waitUntil: "networkidle" });
      let onOpen = false, focused = "";
      for (let i = 0; i < 8 && !onOpen; i++) {
        await p.keyboard.press("Tab");
        onOpen = await p.evaluate(() => !!(document.activeElement && document.activeElement.hasAttribute("data-open")));
        focused = await p.evaluate(() => document.activeElement && ((document.activeElement.className || document.activeElement.tagName) + " '" + (document.activeElement.textContent || document.activeElement.getAttribute("aria-label") || "").trim().slice(0, 30) + "'"));
      }
      check(`${slug} · Toetsenbord: openknop bereikbaar met Tab`, onOpen, `focus op: ${focused}`);
      await p.keyboard.press("Enter");
      await p.waitForTimeout(3600);
      await p.waitForFunction(() => document.documentElement.classList.contains("is-open"), null, { timeout: 20000 }).catch(() => {});
      const active = await p.evaluate(() => document.activeElement.tagName + " " + (document.activeElement.textContent || "").trim().replace(/\s+/g, " ").slice(0, 30));
      const inert = await p.evaluate(() => document.getElementById("uitnodiging").inert);
      check(`${slug} · Toetsenbord: na openen focus op de kop`, active.startsWith("H1") && !inert, `focus op: ${active}, inert=${inert}`);
      const pressedBefore = await p.getAttribute("[data-music-toggle]", "aria-pressed");
      await p.click("[data-music-toggle]");
      await p.waitForTimeout(300);
      const pressedAfter = await p.getAttribute("[data-music-toggle]", "aria-pressed");
      check(`${slug} · Muziek start pas na een tik`, pressedBefore === "false" && pressedAfter === "true", `voor=${pressedBefore}, na=${pressedAfter}`);
      await p.click("[data-music-toggle]");
      const pausedLabel = await p.textContent("[data-music-label]");
      check(`${slug} · Muziek pauzeren`, pausedLabel.includes("afspelen"), `label='${pausedLabel}'`);
      await ctx.close();
    }
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
      const p = await ctx.newPage();
      await p.route("**/invitations/invite*.js", (route) => route.abort());
      await p.goto(base + demo, { waitUntil: "domcontentloaded" });
      await p.waitForTimeout(8200);
      const coverGone = await p.evaluate(() => { const c = document.querySelector("[data-cover]"); const st = getComputedStyle(c); return st.visibility === "hidden" || st.opacity === "0" || st.display === "none"; });
      check(`${slug} · Script laadt niet: vangnet toont de uitnodiging`, coverGone, `openingsscherm verdwenen=${coverGone}`);
      await p.screenshot({ path: path.join(outDir, `check-script-blocked-${slug}.png`) });
      await ctx.close();
    }
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, timezoneId: "America/New_York" });
      const p = await ctx.newPage();
      await p.goto(base + demo, { waitUntil: "networkidle" });
      const note = await p.isVisible("[data-tz-note]");
      check(`${slug} · Andere tijdzone: melding 'tijd in Nederland'`, note, `zichtbaar=${note}`);
      await ctx.close();
    }
  }
  // Zonder JavaScript: elke uitnodiging direct leesbaar (per ontwerp de variant met lange teksten).
  for (const [key, url] of Object.entries(fixtures).filter(([k]) => runChecks && k.endsWith(":lang"))) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, javaScriptEnabled: false });
    const p = await ctx.newPage();
    await p.goto(base + url, { waitUntil: "networkidle" });
    const coverVisible = await p.evaluate(() => { const c = document.querySelector("[data-cover]"); return c ? getComputedStyle(c).display !== "none" : false; });
    const h1 = await p.isVisible("h1");
    const form = await p.isVisible("form[action$='/aanmelden/']");
    check(`${key.split(":")[0]} · Zonder JavaScript direct leesbaar`, !coverVisible && h1 && form, `openingsscherm zichtbaar=${coverVisible}, kop zichtbaar=${h1}, aanmeldformulier zichtbaar=${form}`);
    await p.screenshot({ path: path.join(outDir, `check-no-js-${key.split(":")[0]}.png`), fullPage: false });
    await ctx.close();
  }
  fs.writeFileSync(path.join(outDir, onlyViewports.length || !runChecks ? `rapport-${onlyViewports.join("-") || "alle"}${runChecks ? "" : "-zonder-gedrag"}.json` : "rapport.json"), JSON.stringify(report, null, 2));
  const problems = report.pages.filter((e) => e.overflow > 0 || e.overflowing.length || e.clipped.length || e.errors.length || e.failed.length || (e.status >= 400 && e.name !== "404"));
  console.log(`\nPagina's gecontroleerd: ${report.pages.length}, met aandachtspunten: ${problems.length}, gedragscontroles: ${report.checks.filter(c => c.ok).length}/${report.checks.length} ok`);
  await browser.close();
})();

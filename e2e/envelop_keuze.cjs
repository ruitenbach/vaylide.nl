// VAYLIDE Studio: de keuze uit de Envelope Collection (stap Envelop & zegel), live wisselen, opslaan, en de opening die een gast ziet.
// Gebruik (vanuit de projectmap, server in testmodus): node e2e/envelop_keuze.cjs <basis-url> <uitvoermap>   Optioneel: VIEWPORTS=360,390,768,1366
// Controleert per schermformaat: keuze maken (envelop, zegel, geen envelop, opening van het ontwerp), wisselen zonder pagina te verversen
// (live kaart), opslaan en terugkomen, een ingebouwd ontwerp (geen stap), de opening van de gast (tikken op het zegel, kaart, uitnodiging),
// 'minder beweging', geen horizontale scroll en geen consolefouten.
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
const problems = [];
const check = (naam, ok, detail = "") => { if (!ok) problems.push(`${naam}${detail ? ": " + detail : ""}`); };

async function start(page, ontwerp, gelegenheid = "bruiloft") {
  await page.goto(`${base}/maken/?gelegenheid=${gelegenheid}&ontwerp=${ontwerp}`, { waitUntil: "load" });
  await Promise.all([page.waitForURL(/\/maken\/[0-9a-f-]+\/[a-z]+\/$/), page.locator("main button[type=submit]").first().click()]);
  return page.url().split("/maken/")[1].split("/")[0];
}

(async () => {
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await chromium.launch();
  for (const vp of viewports) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height }, deviceScaleFactor: 2, hasTouch: vp.touch });
    const page = await ctx.newPage();
    const errors = [];
    page.on("console", (m) => m.type() === "error" && errors.push(m.text()));
    page.on("pageerror", (e) => errors.push(String(e)));
    const tag = vp.name;
    const shot = (naam, opts = {}) => page.screenshot({ path: path.join(outDir, `${tag}-${naam}.png`), ...opts });
    const geenScroll = async (waar) => check(`${tag} ${waar}: horizontale scroll`, !(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)));

    // 1. ontwerp kiezen → direct naar Envelop & zegel
    const uid = await start(page, "puur-moment");
    check(`${tag}: na het kiezen van het ontwerp naar de stap Envelop`, page.url().endsWith("/envelop/"), page.url());
    await page.evaluate(() => document.fonts.ready);
    check(`${tag}: voortgang noemt Envelop & zegel`, (await page.locator(".wizard-progress__list").innerText()).includes("Envelop & zegel"));
    await geenScroll("stap");
    await shot("1-stap", { fullPage: true });

    // 2. live kaart openen (op smalle schermen zit hij achter een knop) en live wisselen tussen drie bestaande enveloppen
    const live = page.locator("details[data-live]");
    const smal = vp.width < 1100;      // smal: de live kaart ligt achter de knop 'Bekijk je kaart' en dekt dan het scherm; breed: staat naast de stappen
    const frame = () => page.frameLocator("[data-live-frame]");
    const zet = async (open) => { if (smal && (await live.evaluate((d) => d.open)) !== open) await live.locator("summary").click(); };   // breed: altijd open, geen knop
    await page.evaluate(() => { window.__ln = 0; document.querySelector("[data-live-frame]").addEventListener("load", () => { window.__ln++; }); });
    const kies = async (selector) => {      // klik een keuze; op smalle schermen daarna de live kaart openen, wachten tot hij zich bijwerkt
      const n0 = await page.evaluate(() => window.__ln);
      await zet(false);
      await page.locator(selector).click();
      await zet(true);
      await page.waitForFunction((n) => window.__ln > n, n0, { timeout: 15000 });   // de live kaart is opnieuw geladen, zonder de pagina te verversen
      await page.waitForTimeout(1100);
    };
    for (const naam of ["signature", "rose-blush", "midnight-emeraude"]) {
      await kies(`.env-kaart:has(input[value="${naam}"])`);
      check(`${tag}: live kaart toont ${naam}`, await frame().locator(`.vx.vx--${naam}`).count() === 1);
      // de live kaart zweeft (animatie): daarom zelf meten in plaats van op 'stabiel' te wachten
      const r = await page.locator("[data-live-card]").evaluate((e) => { e.scrollIntoView({ block: "center" }); const b = e.getBoundingClientRect(); return { x: Math.max(0, b.x), y: Math.max(0, b.y), width: Math.min(b.width, innerWidth), height: Math.min(b.height, innerHeight) }; });
      await shot(`2-live-${naam}`, { clip: r });
    }
    await zet(false);
    // alleen passende zegels: bij Midnight Émeraude 2 van de 4
    const zichtbaar = await page.locator(".zegel-kaart:not([hidden])").count();
    check(`${tag}: bij Midnight Émeraude alleen de passende zegels`, zichtbaar === 2, String(zichtbaar));
    await kies('.env-kaart:has(input[value="signature"])');
    await zet(false);
    check(`${tag}: bij Signature Ivory vier zegels`, (await page.locator(".zegel-kaart:not([hidden])").count()) === 4);
    await kies('.zegel-kaart:has(input[value="noisette-gold"])');
    check(`${tag}: live kaart toont het gekozen zegel`, (await frame().locator(".vx").getAttribute("style")).includes("#D2B275"));
    // zegel is groot genoeg om aan te tikken
    const hit = await frame().locator(".vx-seal-hit").evaluate((e) => { const r = e.getBoundingClientRect(); return { width: r.width }; });
    check(`${tag}: zegel minstens 44 px (${Math.round(hit.width)})`, hit.width >= 44);
    await zet(false);
    await shot("3-gekozen", { fullPage: true });

    // 3. opslaan, verder naar Gegevens, terug: de keuze staat er nog
    await Promise.all([page.waitForURL(/\/gegevens\/$/), page.locator("button[name=actie][value=volgende]").click()]);
    check(`${tag}: Volgende gaat naar Gegevens`, page.url().endsWith("/gegevens/"));
    await page.goto(`${base}/maken/${uid}/envelop/`);
    check(`${tag}: zegel bewaard`, await page.locator('input[name=zegel][value="noisette-gold"]').isChecked());
    check(`${tag}: keuze er nog na terugkomen`, await page.locator('input[name=envelop][value="signature"]').isChecked());

    // 4. de opening van de gast (het voorbeeld toont exact hetzelfde als de gastlink)
    const gast = await ctx.newPage();
    gast.on("console", (m) => m.type() === "error" && errors.push("gast: " + m.text()));
    gast.on("pageerror", (e) => errors.push("gast: " + String(e)));
    await gast.goto(`${base}/maken/${uid}/voorbeeld/weergave/`, { waitUntil: "load" });
    await gast.waitForSelector(".vxc .vx-seal-hit", { timeout: 8000 });
    await gast.waitForTimeout(vp.name === "1366" ? 3200 : 3200);   // opwarmen en verschijnen
    check(`${tag} gast: openingsscherm met envelop`, await gast.locator(".vxc.vxc--licht .vx--signature").count() === 1);
    await gast.screenshot({ path: path.join(outDir, `${tag}-4-gast-1-dicht.png`) });
    const t0 = Date.now();
    if (vp.touch) await gast.locator(".vx-seal-hit").tap({ force: true }); else await gast.locator(".vx-seal-hit").click({ force: true });
    for (const [naam, ms] of [["2-zegel", 650], ["3-flap", 1500], ["4-kaart", 2500], ["5-eind", 3500]]) {
      await gast.waitForTimeout(Math.max(0, ms - (Date.now() - t0)));
      await gast.screenshot({ path: path.join(outDir, `${tag}-4-gast-${naam}.png`) });
    }
    await gast.waitForFunction(() => document.documentElement.classList.contains("is-open"), null, { timeout: 8000 });
    await gast.waitForTimeout(500);
    check(`${tag} gast: openingsscherm weg`, await gast.locator("[data-cover]").evaluate((c) => c.hidden));
    check(`${tag} gast: uitnodiging zichtbaar`, await gast.locator("#uitnodiging").isVisible());
    check(`${tag} gast: geen horizontale scroll`, !(await gast.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)));
    await gast.screenshot({ path: path.join(outDir, `${tag}-4-gast-6-uitnodiging.png`) });
    await gast.close();

    // 5. geen envelop, en de opening van het ontwerp
    await page.goto(`${base}/maken/${uid}/envelop/`);
    await page.locator('.env-kaart:has(input[value="geen"])').click();
    await Promise.all([page.waitForURL(/\/gegevens\/$/), page.locator("button[name=actie][value=volgende]").click()]);
    const g2 = await ctx.newPage();
    await g2.goto(`${base}/maken/${uid}/voorbeeld/weergave/`, { waitUntil: "load" });
    check(`${tag}: geen envelop = direct de uitnodiging`, (await g2.locator("[data-cover]").count()) === 0 && await g2.locator("#uitnodiging").isVisible());
    await g2.close();
    await page.goto(`${base}/maken/${uid}/envelop/`);
    await page.locator('.env-kaart:has(input[value=""])').click();
    await Promise.all([page.waitForURL(/\/gegevens\/$/), page.locator("button[name=actie][value=volgende]").click()]);
    const g3 = await ctx.newPage();
    await g3.goto(`${base}/maken/${uid}/voorbeeld/weergave/`, { waitUntil: "load" });
    check(`${tag}: opening van het ontwerp blijft kunnen`, (await g3.locator("[data-cover]").count()) === 1 && (await g3.locator(".vxc").count()) === 0);
    await g3.close();

    // 6. een ontwerp met een ingebouwde opening heeft de stap niet
    const uid2 = await start(page, "midnight-emeraude");
    check(`${tag}: ingebouwd ontwerp gaat naar Gegevens`, page.url().endsWith("/gegevens/"), page.url());
    const r = await page.goto(`${base}/maken/${uid2}/envelop/`);
    check(`${tag}: ingebouwd ontwerp slaat de stap over`, page.url().endsWith("/gegevens/"), page.url());

    check(`${tag}: consolefouten`, errors.length === 0, errors.join(" | "));
    await ctx.close();
  }

  // minder beweging: de envelop opent rustig en de uitnodiging is er meteen
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce", hasTouch: true });
  const page = await ctx.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  const uid = await start(page, "puur-moment");
  await page.locator('.env-kaart:has(input[value="signature"])').click();
  await Promise.all([page.waitForURL(/\/gegevens\/$/), page.locator("button[name=actie][value=volgende]").click()]);
  const gast = await ctx.newPage();
  gast.on("pageerror", (e) => errors.push(String(e)));
  await gast.goto(`${base}/maken/${uid}/voorbeeld/weergave/`, { waitUntil: "load" });
  await gast.waitForSelector(".vxc .vx-seal-hit");
  await gast.waitForTimeout(600);
  const t0 = Date.now();
  await gast.locator(".vx-seal-hit").tap({ force: true });
  await gast.waitForFunction(() => document.documentElement.classList.contains("is-open"), null, { timeout: 6000 });
  check("minder beweging: opent snel (" + (Date.now() - t0) + " ms)", Date.now() - t0 < 2500);
  check("minder beweging: geen 3D-draai", await gast.evaluate(() => getComputedStyle(document.querySelector(".vx-flap")).animationName === "none"));
  check("minder beweging: geen fouten", errors.length === 0, errors.join(" | "));
  await gast.screenshot({ path: path.join(outDir, "minder-beweging.png") });
  await ctx.close();
  await browser.close();
  console.log(problems.length ? "PROBLEMEN:\n" + problems.join("\n") : "Geen problemen gevonden.");
  process.exit(problems.length ? 1 : 0);
})();

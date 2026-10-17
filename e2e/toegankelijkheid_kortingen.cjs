// Toegankelijkheid van kortingscodes, automatische aanbiedingen, actieprijzen en foutmeldingen (axe-core WCAG 2.0/2.1 A en AA, plus gerichte controles).
// Gebruik (server in testmodus met VIERLIEF_PRICING_V2=1 VIERLIEF_KORTINGSCODES=1 VIERLIEF_AANBIEDINGEN=1, een aanbieding en een code ZOMER10):
//   node e2e/toegankelijkheid_kortingen.cjs <basis-url> <seed.json> <uitvoer.json>
// seed.json: {"inv": "<uid van een compleet concept>", "klant": {"name","value"}, "staf": {"name","value"}} (sessiecookies van een klant en een beheerder).
const { chromium } = require("playwright");
const fs = require("fs");
const axeSrc = fs.readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");
const [base, seedFile, outFile] = process.argv.slice(2);
const seed = JSON.parse(fs.readFileSync(seedFile));
const host = new URL(base).hostname;

// Rustig doorscrollen (lazy loading) en wachten tot alle afbeeldingen echt geladen zijn; geeft de namen van afbeeldingen die niet laden.
async function laadAfbeeldingen(page) {
  const hoogte = await page.evaluate(() => document.body.scrollHeight);
  for (let y = 0; y < hoogte; y += 300) { await page.evaluate((y) => window.scrollTo(0, y), y); await page.waitForTimeout(220); }
  await page.waitForTimeout(1200);
  await page.evaluate(() => window.scrollTo(0, 0));
  return page.evaluate(() => [...document.images].filter((i) => !(i.complete && i.naturalWidth > 0)).map((i) => i.src.split("/").pop()));
}

(async () => {
  const browser = await chromium.launch();
  const resultaat = [];
  async function pagina(naam, url, who, w, voor, extra) {
    const ctx = await browser.newContext({ viewport: { width: w, height: 900 }, bypassCSP: true });
    if (who) await ctx.addCookies([{ name: seed[who].name, value: seed[who].value, domain: host, path: "/" }]);
    const page = await ctx.newPage();
    await page.goto(base + url, { waitUntil: "networkidle" });
    if (voor) await voor(page);
    const nietGeladen = await laadAfbeeldingen(page);
    await page.addScriptTag({ content: axeSrc });
    const axe = await page.evaluate(() => axe.run(document, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] } }));
    const eigen = [{ naam: `alle afbeeldingen geladen${nietGeladen.length ? " (niet: " + nietGeladen.join(", ") + ")" : ""}`, ok: nietGeladen.length === 0 }, ...(extra ? await extra(page) : [])];
    const sleutel = `${naam}-${w}`;
    const schade = axe.violations.map((v) => `${v.id} (${v.impact}) ${v.nodes.slice(0, 3).map((n) => n.target.join(" ")).join("; ")}`);
    resultaat.push({ pagina: sleutel, axe: schade, eigen: eigen.filter((e) => !e.ok).map((e) => e.naam), gecontroleerd: eigen.map((e) => `${e.ok ? "ok" : "FOUT"} ${e.naam}`) });
    console.log(`${schade.length || eigen.some((e) => !e.ok) ? "LET OP" : "ok"} ${sleutel}${schade.length ? " axe: " + schade.join(" | ") : ""}${eigen.filter((e) => !e.ok).map((e) => " eigen: " + e.naam).join("")}`);
    if (process.env.SCHERM) await page.screenshot({ path: `${process.env.SCHERM}/${sleutel}.png`, fullPage: true });
    await ctx.close();
  }
  const bestellen = `/maken/${seed.inv}/bestellen/`;
  for (const w of [390, 1366]) {
    await pagina("collectie", "/ontwerpen/?gelegenheid=bruiloft", null, w, null, async (p) => [
      { naam: "kaart heeft prijskaartje met tekst 'Aanbieding'", ok: (await p.locator(".design-card__aanbod .aanbod-chip").first().innerText()).includes("Aanbieding") },
      { naam: "doorgestreepte prijs heeft verborgen tekst 'Was'", ok: (await p.locator(".design-card__prijs s .visually-hidden").first().textContent()).includes("Was") },
      { naam: "actieprijs heeft verborgen tekst 'Nu'", ok: (await p.locator(".design-card__prijs > .visually-hidden").first().textContent()).includes("Nu") },
      { naam: "prijskaartje-icoon is decoratief (aria-hidden)", ok: (await p.locator(".aanbod-chip svg").first().getAttribute("aria-hidden")) === "true" },
    ]);
    await pagina("ontwerp", "/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft", null, w, null, async (p) => [
      { naam: "de andere kaartsoort is verborgen voor schermlezers (hidden)", ok: (await p.locator('[data-prijs-variant="wenskaart"]').getAttribute("hidden")) !== null },
      { naam: "einddatum staat als tekst", ok: (await p.locator(".detail-prijs__einde").first().innerText()).includes("Aanbieding t/m") },
    ]);
    await pagina("ontwerp-wenskaart", "/ontwerpen/liefde-op-papier/?gelegenheid=bruiloft&soort=wenskaart", null, w);
    await pagina("kaartkeuze", "/maken/?gelegenheid=bruiloft", "klant", w);
    await pagina("bestellen", bestellen, "klant", w, null, async (p) => [
      { naam: "aanbiedingsregel staat in de bon-tabel", ok: (await p.locator(".bon__korting--aanbieding").count()) === 1 },
      { naam: "kortingsveld heeft een label", ok: (await p.locator('label[for="kortingscode"]').count()) === 1 },
    ]);
    await pagina("bestellen-fout", bestellen, "klant", w, async (p) => {
      await p.locator("summary.korting__vraag").click();
      await p.fill("#kortingscode", "BESTAATNIET");
      await p.click('button[value="code-toepassen"]');
      await p.waitForLoadState("networkidle");
    }, async (p) => [
      { naam: "foutmelding heeft role=alert", ok: (await p.locator("#korting-fout").getAttribute("role")) === "alert" },
      { naam: "invoerveld is aria-invalid en verwijst naar de melding", ok: (await p.locator("#kortingscode").getAttribute("aria-invalid")) === "true" && (await p.locator("#kortingscode").getAttribute("aria-describedby")) === "korting-fout" },
      { naam: "details staat open na de fout", ok: await p.locator("details.korting").evaluate((d) => d.open) },
    ]);
    await pagina("bestellen-code-toegepast", bestellen, "klant", w, async (p) => {
      await p.locator("summary.korting__vraag").click();
      await p.fill("#kortingscode", "ZOMER10");
      await p.click('button[value="code-toepassen"]');
      await p.waitForLoadState("networkidle");
    }, async (p) => [
      { naam: "melding over voordeligste korting is een status (role=status)", ok: (await p.locator(".korting__melding").first().getAttribute("role")) === "status" },
    ]);
  }
  // Toetsenbord: de uitklapregel is met Enter te openen en het veld is daarna bereikbaar.
  {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 900 } });
    await ctx.addCookies([{ name: seed.klant.name, value: seed.klant.value, domain: host, path: "/" }]);
    const page = await ctx.newPage();
    await page.goto(base + bestellen, { waitUntil: "networkidle" });
    await page.locator("summary.korting__vraag").focus();
    const focusZichtbaar = await page.locator("summary.korting__vraag").evaluate((e) => { const s = getComputedStyle(e); return s.outlineStyle !== "none" || s.boxShadow !== "none"; });
    await page.keyboard.press("Enter");
    await page.keyboard.press("Tab");
    const opVeld = await page.evaluate(() => document.activeElement && document.activeElement.id === "kortingscode");
    resultaat.push({ pagina: "toetsenbord-bestellen-390", axe: [], eigen: [focusZichtbaar ? null : "focusring op 'Heb je een kortingscode?' niet zichtbaar", opVeld ? null : "Tab na Enter bereikt het kortingsveld niet"].filter(Boolean), gecontroleerd: [`${focusZichtbaar ? "ok" : "FOUT"} focusring`, `${opVeld ? "ok" : "FOUT"} Enter opent, Tab bereikt veld`] });
    console.log(`${focusZichtbaar && opVeld ? "ok" : "LET OP"} toetsenbord-bestellen-390 focusring=${focusZichtbaar} veld=${opVeld}`);
    await ctx.close();
  }
  for (const w of [390, 1366]) {
    await pagina("beheer-aanbiedingen", "/beheer/aanbiedingen/", "staf", w);
    await pagina("beheer-aanbieding", "/beheer/aanbiedingen/1/", "staf", w);
    await pagina("beheer-aanbieding-nieuw", "/beheer/aanbiedingen/nieuw/", "staf", w);
    await pagina("beheer-kortingscodes", "/beheer/kortingscodes/", "staf", w);
  }
  fs.writeFileSync(outFile, JSON.stringify(resultaat, null, 1));
  const slecht = resultaat.filter((r) => r.axe.length || r.eigen.length);
  console.log(`${resultaat.length} pagina's, ${slecht.length} met bevindingen`);
  await browser.close();
})();

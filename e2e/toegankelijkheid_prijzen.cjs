// Toegankelijkheid van de prijzenpagina's in Beheer (overzicht, wijzigen, bevestigen, foutmelding, logboek, terugdraaien).
// axe-core (WCAG 2.0/2.1 A en AA) op 360, 390, 768, 1366 px en op 200% zoom (683 px breed), plus toetsenbordcontrole:
// elk bedienbaar element bereikbaar met Tab, zichtbare focus, elk invulveld met een label, en de foutmelding bij een ongeldige invoer.
// Gebruik (lokale testserver met VIERLIEF_PRICING_V2=1 en VIERLIEF_PRIJZENBEHEER=1, gebruikers uit tests/fixtures of eigen testdata):
//   npm install --no-save axe-core@4
//   node e2e/toegankelijkheid_prijzen.cjs http://127.0.0.1:8765 /tmp/prijzen-a11y.json eigenaar@example.com 'wachtwoord' <id van een logboekset om terug te draaien>
const { chromium } = require("playwright");
const fs = require("fs");
const [base, outFile, email, wachtwoord, setId = "2"] = process.argv.slice(2);
const axeSrc = fs.readFileSync(require.resolve("axe-core/axe.min.js"), "utf8");
const MATEN = [["360", 360, 740, 1], ["390", 390, 844, 1], ["768", 768, 1000, 1], ["1366", 1366, 900, 1], ["zoom200", 683, 450, 2]];

async function login(page) {
  await page.goto(base + "/beheer/inloggen/", { waitUntil: "networkidle" });
  await page.fill('input[name="username"]', email);
  await page.fill('input[name="password"]', wachtwoord);
  await Promise.all([page.waitForNavigation(), page.locator("form button[type=submit]").last().click()]);
}
async function axe(page) {
  await page.evaluate(axeSrc);
  const r = await page.evaluate(() => axe.run(document, { runOnly: { type: "tag", values: ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"] } }));
  return r.violations.map((v) => ({ id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.map((n) => n.target.join(" ")).slice(0, 6) }));
}
async function toetsenbord(page) {
  // Alle bedienbare elementen in beeld; Tab door de pagina; per stop: heeft het een toegankelijke naam en is de focus zichtbaar?
  const n = await page.evaluate(() => [...document.querySelectorAll("a[href], button, input, select, textarea, summary, [tabindex]")].filter((e) => e.tabIndex >= 0 && !e.disabled && e.checkVisibility()).length);
  const problemen = [], bezocht = new Set();
  await page.evaluate(() => document.activeElement && document.activeElement.blur());
  for (let i = 0; i < n + 3; i++) {
    await page.keyboard.press("Tab");
    const s = await page.evaluate(() => {
      const e = document.activeElement;
      if (!e || e === document.body) return null;
      const cs = getComputedStyle(e);
      const svg = e.querySelector("svg[aria-label], svg title");
      const naam = (e.getAttribute("aria-label") || (e.labels && e.labels[0] && e.labels[0].textContent) || (e.textContent || '').trim() || e.value || e.title || (svg && (svg.getAttribute("aria-label") || svg.textContent)) || (e.querySelector("img[alt]") || {}).alt || "").trim();
      const outline = cs.outlineStyle !== "none" && parseFloat(cs.outlineWidth) > 0;
      const omhulsel = e.closest(".prijs-invoer");   // het bedragveld toont de focus op zijn omlijsting (rand + gouden ring)
      const schaduw = cs.boxShadow !== "none" || (omhulsel && getComputedStyle(omhulsel).boxShadow !== "none");
      const r = e.getBoundingClientRect();
      return { sel: e.tagName.toLowerCase() + (e.id ? "#" + e.id : e.name ? "[name=" + e.name + "]" : ""), naam: naam.slice(0, 40), zichtbareFocus: outline || schaduw, inBeeld: r.bottom > 0 && r.top < innerHeight + 1 };
    });
    if (!s) continue;
    bezocht.add(s.sel + "|" + s.naam);
    if (!s.naam) problemen.push({ type: "geen naam", ...s });
    if (!s.zichtbareFocus) problemen.push({ type: "geen zichtbare focus", ...s });
  }
  return { bedienbaar: n, bezocht: bezocht.size, problemen };
}

(async () => {
  const browser = await chromium.launch();
  const rapport = [];
  for (const [naam, w, h, zoom] of MATEN) {
    const ctx = await browser.newContext({ viewport: { width: w, height: h } });
    const page = await ctx.newPage();
    await login(page);
    const pad = {
      overzicht: "/beheer/prijzen-en-acties/", wijzigen: "/beheer/prijzen-en-acties/wijzigen/",
      logboek: "/beheer/prijzen-en-acties/logboek/", terugdraaien: `/beheer/prijzen-en-acties/logboek/${setId}/terugdraaien/`,
    };
    const stappen = [];
    for (const [k, p] of Object.entries(pad)) stappen.push([k, async () => { await page.goto(base + p, { waitUntil: "networkidle" }); }]);
    stappen.push(["bevestigen", async () => {
      await page.goto(base + pad.wijzigen, { waitUntil: "networkidle" });
      await page.fill("#p_bruiloft_luxe", "57,95");
      await Promise.all([page.waitForNavigation(), page.click('form.prijzen-form button[type="submit"]')]);
    }]);
    stappen.push(["foutmelding", async () => {
      await page.goto(base + pad.wijzigen, { waitUntil: "networkidle" });
      await page.fill("#p_bruiloft_luxe", "abc");
      await Promise.all([page.waitForNavigation(), page.click('form.prijzen-form button[type="submit"]')]);
    }]);
    for (const [k, doe] of stappen) {
      await doe();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      const extra = {};
      if (k === "foutmelding") {
        extra.fout = await page.evaluate(() => {
          const ongeldig = [...document.querySelectorAll("[aria-invalid=true]")].map((e) => ({ id: e.id, beschrijving: (e.getAttribute("aria-describedby") || "").split(" ").map((i) => document.getElementById(i)?.textContent.trim()).join(" ").slice(0, 80) }));
          const melding = document.querySelector("[role=alert], [role=status], .alert, .form-errors");
          return { ongeldig, melding: melding ? { rol: melding.getAttribute("role"), tekst: melding.textContent.trim().slice(0, 100) } : null, focusOp: document.activeElement.tagName + "#" + document.activeElement.id };
        });
      }
      if (naam === "1366" || naam === "390") extra.toetsenbord = await toetsenbord(page);
      const velden = await page.evaluate(() => [...document.querySelectorAll("input:not([type=hidden]), select, textarea")].filter((e) => !(e.labels && e.labels.length) && !e.getAttribute("aria-label") && !e.getAttribute("aria-labelledby")).map((e) => e.name || e.id));
      rapport.push({ maat: naam, pagina: k, overflowPx: overflow, zonderLabel: velden, axe: await axe(page), ...extra });
    }
    await ctx.close();
  }
  fs.writeFileSync(outFile, JSON.stringify(rapport, null, 1));
  const kort = rapport.map((r) => `${r.maat.padEnd(8)} ${r.pagina.padEnd(13)} axe:${r.axe.length} overflow:${r.overflowPx} zonderLabel:${r.zonderLabel.length}` + (r.toetsenbord ? ` tab:${r.toetsenbord.bezocht}/${r.toetsenbord.bedienbaar} toetsprobl:${r.toetsenbord.problemen.length}` : ""));
  console.log(kort.join("\n"));
  await browser.close();
})();

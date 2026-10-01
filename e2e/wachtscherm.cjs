// Het betaalwachtscherm in de browser (testbetaling): open betaling -> na een minuut 'Betaling hervatten' -> terug naar
// dezelfde betaling -> geannuleerd -> opnieuw -> verlopen -> opnieuw -> betaald. Telt ook hoe vaak de pagina de status vraagt.
// Gebruik: .venv/bin/python e2e/klantreis_setup.py > /tmp/k.json && node e2e/wachtscherm.cjs http://127.0.0.1:8000 /tmp/k.json uitmap 390
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const base = process.argv[2] || "http://127.0.0.1:8000";
const data = JSON.parse(fs.readFileSync(process.argv[3], "utf-8"));
const out = process.argv[4] || "wachtscherm";
const width = Number(process.argv[5] || 390);
fs.mkdirSync(out, { recursive: true });
const results = [];
const check = (name, ok, detail = "") => { results.push({ name, ok, detail }); console.log(`${ok ? "ok  " : "FOUT"} ${name}${detail ? ": " + detail : ""}`); };

(async () => {
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width, height: width < 700 ? 844 : 900 }, locale: "nl-NL" });
  const p = await ctx.newPage();
  const errors = [];
  p.on("pageerror", (e) => errors.push(e.message));
  let polls = 0;
  p.on("request", (r) => { if (r.url().includes("/status.json")) polls++; });

  await p.goto(base + "/inloggen/");
  await p.fill("#id_email", data.a);
  await p.click("main button[type=submit]");
  await p.fill("#id_code", (await p.textContent(".test-code")).trim());
  await p.click("main button[type=submit]");
  await p.waitForURL("**/account/**");

  const pay = async (outcome) => {
    await p.check(`input[name=uitkomst][value=${outcome}]`, { force: true });
    await Promise.all([p.waitForURL("**/bestelling/**"), p.click("main button[type=submit]")]);
  };

  // 1. Bestellen en de betaling open laten (klant komt terug zonder te betalen).
  await p.goto(`${base}/maken/${data.paid}/bestellen/`);
  await p.check("input[name=terms]");
  await p.check("input[name=direct_leveren]");
  await Promise.all([p.waitForURL("**/betalen/test/**"), p.click("button[name=actie][value=betalen]")]);
  const firstCheckout = p.url();
  await pay("open");
  check("Open betaling: wachtscherm", /We wachten op de bevestiging/.test(await p.textContent("main")));
  check("Hervatten nog verborgen", await p.isHidden("[data-resume]"));
  polls = 0;
  await p.waitForTimeout(62000);
  check("Na een minuut: 'Betaling hervatten' zichtbaar", await p.isVisible("[data-resume] button"));
  check("Minder vaak vragen", polls <= 12, `${polls} statusverzoeken in 62 s (was 31 bij elke 2 s)`);
  await p.screenshot({ path: path.join(out, `${width}-wachtscherm-hervatten.png`), fullPage: true });

  // 2. Hervatten: terug naar dezelfde betaling, geen nieuwe.
  await Promise.all([p.waitForURL("**/betalen/test/**"), p.click("[data-resume] button")]);
  check("Hervatten gaat naar dezelfde betaling", p.url() === firstCheckout, p.url().split("/").slice(-2).join("/"));

  // 3. Geannuleerd -> eigen scherm, opnieuw betalen maakt een nieuwe poging.
  await pay("geannuleerd");
  check("Geannuleerd: 'Betaling afgebroken'", /Betaling afgebroken/.test(await p.textContent("main")));
  await Promise.all([p.waitForURL("**/betalen/test/**"), p.click("form[action$='/opnieuw-betalen/'] button")]);
  check("Opnieuw betalen: nieuwe betaalpoging", p.url() !== firstCheckout);

  // 4. Verlopen -> eigen scherm.
  await pay("verlopen");
  check("Verlopen: 'Betaling verlopen'", /Betaling verlopen/.test(await p.textContent("main")));
  await p.screenshot({ path: path.join(out, `${width}-verlopen.png`), fullPage: true });

  // 5. Alsnog betalen -> online.
  await Promise.all([p.waitForURL("**/betalen/test/**"), p.click("form[action$='/opnieuw-betalen/'] button")]);
  await pay("betaald");
  await p.waitForTimeout(1500);
  await p.reload();
  check("Alsnog betaald: online", (await p.getAttribute("[data-phase]", "data-phase")) === "live");
  check("Geen JavaScript-fouten", errors.length === 0, errors.join(" | "));

  await browser.close();
  const failed = results.filter((r) => !r.ok).length;
  console.log(`\n${results.length - failed}/${results.length} controles ok (${width} px)`);
  process.exit(failed ? 1 : 0);
})();

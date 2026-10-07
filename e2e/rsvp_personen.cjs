// Aanmelden met een aantal personen, in een echte browser: de gast meldt zich aan en kiest 'Met hoeveel personen kom je?',
// daarna ziet de maker (ingelogd met een code) het aantal in het gastenoverzicht en in de csv.
// Gebruik: NODE_PATH=<map met playwright> node e2e/rsvp_personen.cjs <basis-url> <rsvp.json van e2e/rsvp_setup.py> [chromium|firefox|webkit]
const fs = require("fs");
const { chromium, firefox, webkit } = require("playwright");
const [BASIS, SETUP, NAAM] = [process.argv[2], process.argv[3], process.argv[4] || "chromium"];
const TYPE = { chromium, firefox, webkit }[NAAM];
const data = JSON.parse(fs.readFileSync(SETUP, "utf8").replace(/^﻿/, ""));
let fouten = 0; const ok = (n, w, e) => { if (!w) fouten++; console.log(`${w ? "OK  " : "FOUT"} ${n}${e ? " | " + e : ""}`); };

(async () => {
  const b = await TYPE.launch();
  for (const [maat, w, h] of [["390", 390, 844], ["1366", 1366, 768]]) {
    const mobiel = w < 600 && NAAM !== "firefox";
    const opt = { viewport: { width: w, height: h } }; if (mobiel) { opt.isMobile = true; opt.hasTouch = true; }
    const gast = await (await b.newContext(opt)).newPage(); const fout = [];
    gast.on("pageerror", (e) => fout.push(String(e).slice(0, 120)));
    await gast.goto(BASIS + data.public_path + "#aanmelden", { waitUntil: "load" }); await gast.waitForTimeout(2000);
    // de uitnodiging openen als er een envelop is, daarna naar het aanmeldformulier
    const open = gast.locator("[data-open]").first();
    if (await open.count() && await open.isVisible()) { await (mobiel ? open.tap() : open.click()).catch(() => {}); await gast.waitForTimeout(2500); }
    const formulier = gast.locator("[data-rsvp-form]").first();
    await formulier.scrollIntoViewIfNeeded();
    const vraag = await gast.locator("label[for=rsvp-party]").first().textContent();
    ok(`[${maat}] gast ziet 'Met hoeveel personen kom je?'`, /Met hoeveel personen kom je\?/.test(vraag), vraag.trim());
    const opties = await gast.locator("#rsvp-party option").allTextContents();
    ok(`[${maat}] keuze 1 t/m 4 (het ingestelde maximum)`, opties.join(",") === "1,2,3,4", opties.join(","));
    const naam = `Familie Test ${maat}`;
    await gast.fill("#rsvp-name", naam);
    await gast.locator("input[name=attending][value=ja]").check({ force: true });
    await gast.selectOption("#rsvp-party", "3", { force: true });
    await gast.locator("[data-rsvp-submit]").click({ force: true });
    await gast.waitForFunction(() => /bedankt|opgeslagen|ontvangen|tot dan/i.test(document.querySelector("[data-rsvp]")?.innerText || document.body.innerText), null, { timeout: 15000 }).catch(() => {});
    const na = await gast.locator("[data-rsvp]").first().innerText();
    ok(`[${maat}] gast krijgt een bevestiging met het aantal`, /met 3 personen/.test(na) && /bedankt|opgeslagen|ontvangen|geantwoord/i.test(na), na.replace(/\s+/g, " ").slice(0, 120));
    ok(`[${maat}] gast: geen JavaScript-fouten`, fout.length === 0, fout.join(" | "));
    // de maker
    const mc = await b.newContext(opt); const maker = await mc.newPage();
    await maker.goto(BASIS + "/inloggen/"); await maker.fill("#id_email", data.email); await maker.click("main button[type=submit]");
    const code = (await maker.textContent(".test-code")).trim(); await maker.fill("#id_code", code); await maker.click("main button[type=submit]");
    await maker.waitForURL("**/account/**", { timeout: 15000 });
    await maker.goto(`${BASIS}/account/uitnodiging/${data.uid}/gasten/`);
    const rij = maker.locator("tr", { hasText: naam }).first();
    const tekst = (await rij.innerText()).replace(/\s+/g, " ");
    ok(`[${maat}] maker ziet de aanmelding met 3 personen`, /ja/.test(tekst) && / 3( |$)/.test(" " + tekst + " "), tekst.slice(0, 100));
    const stat = await maker.locator(".stat").allInnerTexts();
    ok(`[${maat}] maker ziet het totaal aantal personen`, stat.some((t) => /(\d+)\s*\n?\s*personen?/i.test(t) && parseInt(t) >= 3), stat.map((t) => t.replace(/\s+/g, " ")).join(" | "));
    const csv = await (await maker.request.get(`${BASIS}/account/uitnodiging/${data.uid}/gasten/export.csv`)).text();
    ok(`[${maat}] csv bevat naam en aantal personen`, new RegExp(`${naam};ja;3`).test(csv), csv.split("\n").slice(0, 3).join(" / ").slice(0, 120));
    await mc.close(); await gast.context().close();
  }
  await b.close();
  console.log(fouten ? `\n${fouten} controle(s) FOUT` : "\nalle controles OK"); process.exit(fouten ? 1 : 0);
})().catch((e) => { console.log("TESTFOUT", String(e).slice(0, 400)); process.exit(2); });

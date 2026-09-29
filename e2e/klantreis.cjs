// De hele klantreis in de browser, in testmodus (gesimuleerde betaling en e-mail):
// inloggen met code, stappen van het samenstellen, foto uploaden (goed en fout), bestellen en betalen,
// publicatie, gast meldt zich aan, antwoord en export in Mijn Vaylide, afgebroken betaling en opnieuw betalen,
// toegangsrechten (andere klant, geen login, geen beheerder), foutpagina's en het beheer.
// Gebruik:
//   .venv/bin/python e2e/klantreis_setup.py > /tmp/klantreis.json
//   node e2e/klantreis.cjs http://127.0.0.1:8000 /tmp/klantreis.json /tmp/klantreis [390|1366]
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const base = process.argv[2] || "http://127.0.0.1:8000";
const data = JSON.parse(fs.readFileSync(process.argv[3], "utf-8"));
const out = process.argv[4] || "klantreis";
const width = Number(process.argv[5] || 390);
fs.mkdirSync(out, { recursive: true });
const results = [];
const check = (name, ok, detail = "") => { results.push({ name, ok, detail }); console.log(`${ok ? "ok  " : "FOUT"} ${name}${detail ? ": " + detail : ""}`); };
const shot = (p, name) => p.screenshot({ path: path.join(out, `${width}-${name}.png`), fullPage: true });

async function login(context, email) {
  const p = await context.newPage();
  await p.goto(base + "/inloggen/");
  await p.fill("#id_email", email);
  await p.click("main button[type=submit]");
  const code = (await p.textContent(".test-code")).trim();
  await p.fill("#id_code", code);
  await p.click("main button[type=submit]");
  await p.waitForURL("**/account/**", { timeout: 10000 });
  return p;
}

async function pay(p, uid, outcome, name) {
  await p.goto(`${base}/maken/${uid}/bestellen/?package=essentieel`);
  await p.check("input[name=terms]");
  await Promise.all([p.waitForURL("**/betalen/test/**"), p.click("button[name=actie][value=betalen]")]);
  await shot(p, `${name}-betaalpagina`);
  await p.check(`input[name=uitkomst][value=${outcome}]`, { force: true });
  await Promise.all([p.waitForURL("**/bestelling/**"), p.click("main button[type=submit]")]);
  await p.waitForTimeout(800);
  await p.reload();
  return p.getAttribute("[data-phase]", "data-phase");
}

(async () => {
  const browser = await chromium.launch();
  const errors = [];
  const ctxOpts = { viewport: { width, height: width < 700 ? 844 : 900 }, locale: "nl-NL", timezoneId: "Europe/Amsterdam" };
  const watch = (p) => {
    p.on("pageerror", (e) => errors.push(`${p.url()}: ${e.message}`));
    // 404 (bewuste controles) en 400 (nepbestand dat de server terecht weigert) horen erbij.
    p.on("console", (m) => { if (m.type() === "error" && !/status of 40[04]/.test(m.text())) errors.push(`${p.url()}: ${m.text()}`); });
  };

  // ---- Klant A: samenstellen, uploaden, betalen, publiceren ----
  const a = await browser.newContext(ctxOpts);
  const pa = await login(a, data.a);
  watch(pa);
  check("Inloggen met code (klant A)", pa.url().includes("/account/"), pa.url());
  for (const step of ["ontwerp", "gegevens", "programma", "aanmelden", "fotos", "stijl", "voorbeeld"]) {
    const r = await pa.goto(`${base}/maken/${data.paid}/${step}/`);
    check(`Stap ${step} opent`, r.status() === 200, `status ${r.status()}`);
  }
  // Gegevens opslaan via het formulier (Volgende).
  await pa.goto(`${base}/maken/${data.paid}/gegevens/`);
  await Promise.all([pa.waitForNavigation(), pa.click(".step-actions__next")]);
  check("Gegevens opslaan en door naar volgende stap", !pa.url().endsWith("/gegevens/"), pa.url());

  // Foto uploaden: een echte foto en een nepbestand.
  const jpg = path.join(out, "foto.jpg");
  const fake = path.join(out, "geen-foto.jpg");
  fs.copyFileSync(path.join(__dirname, "..", "static", "img", "site", "maatwerk-700.webp"), path.join(out, "foto.webp"));
  fs.writeFileSync(fake, "dit is geen afbeelding");
  await pa.goto(`${base}/maken/${data.paid}/fotos/`);
  // De keuze 'geen hoofdfoto' telt niet mee; alleen echte foto's.
  const photos = () => pa.$$eval("input[name=hero]", (els) => els.filter((e) => e.value).length);
  const before = await photos();
  // Uploaden begint vanzelf zodra een bestand is gekozen (studio.js).
  await pa.setInputFiles("#upload-fotos", path.join(out, "foto.webp"));
  await pa.waitForTimeout(3500);
  await pa.goto(`${base}/maken/${data.paid}/fotos/`);
  const after = await photos();
  check("Foto uploaden", after === before + 1, `keuzes voor hoofdfoto ${before} -> ${after}`);
  await pa.setInputFiles("#upload-fotos", fake);
  await pa.waitForTimeout(3500);
  const status = (await pa.textContent("[data-upload-status]").catch(() => "")) || "";
  const body = await pa.textContent("main");
  await pa.goto(`${base}/maken/${data.paid}/fotos/`);
  const afterFake = await photos();
  check("Nepbestand wordt geweigerd met een melding", afterFake === after && /niet|foto|bestand/i.test(status + body), `melding: '${status.trim().slice(0, 90)}'`);
  await shot(pa, "fotos");

  const phase = await pay(pa, data.paid, "betaald", "betaald");
  await shot(pa, "status-betaald");
  check("Geslaagde betaling: bestelling online", phase === "live", `fase ${phase}`);
  const publicUrl = await pa.getAttribute("a[href*='/u/']", "href").catch(() => null);
  check("Link naar de uitnodiging op de statuspagina", !!publicUrl, publicUrl || "geen link");
  const orderUrl = pa.url();

  // ---- Gast: opent de uitnodiging en meldt zich aan ----
  const guest = await browser.newContext(ctxOpts);
  const pg = await guest.newPage();
  watch(pg);
  if (publicUrl) {
    const r = await pg.goto(publicUrl.startsWith("http") ? publicUrl : base + publicUrl);
    check("Gast opent de uitnodiging", r.status() === 200, `status ${r.status()}`);
    await pg.click("[data-open]", { force: true }).catch(() => {});
    await pg.waitForTimeout(3500);
    await pg.fill("form[action$='/aanmelden/'] input[name=name]", "Gast Klantreis");
    await pg.check("form[action$='/aanmelden/'] input[name=attending][value=ja]", { force: true }).catch(() => {});
    await pg.waitForTimeout(3200); // formulier niet sneller dan een mens
    await pg.click("form[action$='/aanmelden/'] button[type=submit]");
    await pg.waitForTimeout(2000);
    const done = await pg.textContent("main").catch(() => "");
    check("Gast meldt zich aan", /bedankt|ontvangen|je antwoord/i.test(done || ""), (done || "").replace(/\s+/g, " ").match(/(bedankt|ontvangen|je antwoord)[^.]{0,60}/i)?.[0] || "geen bevestiging gevonden");
    await shot(pg, "gast-aangemeld");
  }

  // ---- Klant A ziet het antwoord en kan exporteren ----
  const guestsResp = await pa.goto(`${base}/account/uitnodiging/${data.paid}/gasten/`);
  const guestsText = await pa.textContent("main");
  check("Antwoord zichtbaar in Mijn Vaylide", guestsResp.status() === 200 && guestsText.includes("Gast Klantreis"), `status ${guestsResp.status()}`);
  const csv = await pa.request.get(`${base}/account/uitnodiging/${data.paid}/gasten/export.csv`);
  check("Gastenlijst exporteren (CSV)", csv.status() === 200 && (await csv.text()).includes("Gast Klantreis"), `status ${csv.status()}`);
  await shot(pa, "gasten");
  const qr = await pa.request.get(`${base}/account/uitnodiging/${data.paid}/qr.png`);
  check("QR-code downloaden", qr.status() === 200 && (qr.headers()["content-type"] || "").includes("image/png"), `status ${qr.status()}`);

  // ---- Afgebroken betaling en opnieuw betalen ----
  const phase2 = await pay(pa, data.cancel, "geannuleerd", "geannuleerd");
  await shot(pa, "status-geannuleerd");
  check("Afgebroken betaling: niet gepubliceerd", phase2 === "cancelled", `fase ${phase2}`);
  const draftPage = await pa.goto(`${base}/account/uitnodiging/${data.cancel}/`);
  check("Ontwerp blijft bewaard na afbreken", draftPage.status() === 200);
  await pa.goBack();
  const retryBtn = await pa.$("form[action*='opnieuw-betalen'] button");
  check("Knop 'opnieuw betalen' aanwezig", !!retryBtn);
  if (retryBtn) {
    await Promise.all([pa.waitForURL("**/betalen/test/**"), retryBtn.click()]);
    await pa.check("input[name=uitkomst][value=betaald]", { force: true });
    await Promise.all([pa.waitForURL("**/bestelling/**"), pa.click("main button[type=submit]")]);
    await pa.waitForTimeout(800);
    await pa.reload();
    check("Na afbreken alsnog betalen: online", (await pa.getAttribute("[data-phase]", "data-phase")) === "live");
  }

  // ---- Toegangsrechten ----
  const b = await browser.newContext(ctxOpts);
  const pb = await login(b, data.b);
  for (const url of [`/account/uitnodiging/${data.paid}/`, `/account/uitnodiging/${data.paid}/gasten/`, `/account/uitnodiging/${data.paid}/gasten/export.csv`,
    `/maken/${data.paid}/gegevens/`, `/account/uitnodiging/${data.paid}/qr.png`, orderUrl.replace(base, "")]) {
    const r = await pb.goto(base + url);
    check(`Andere klant krijgt 404: ${url.slice(0, 48)}`, r.status() === 404, `status ${r.status()}`);
  }
  const rb = await pb.goto(base + "/beheer/");
  check("Klant komt niet in het beheer", !pb.url().endsWith("/beheer/") || rb.status() >= 400, `${rb.status()} ${pb.url()}`);
  const anon = await browser.newContext(ctxOpts);
  const pn = await anon.newPage();
  for (const url of ["/account/", `/account/uitnodiging/${data.paid}/`, orderUrl.replace(base, "")]) {
    await pn.goto(base + url);
    check(`Zonder login naar inloggen: ${url.slice(0, 40)}`, pn.url().includes("/inloggen/"), pn.url());
  }
  const r404 = await pn.goto(base + "/bestaat-niet/");
  // Met DEBUG aan (ontwikkelserver) toont Django een eigen foutpagina; de Vaylide-pagina alleen met DEBUG uit.
  const own404 = (await pn.textContent("body")).includes("Vaylide");
  check("404 voor een onbekende pagina", r404.status() === 404, `status ${r404.status()}, Vaylide-foutpagina ${own404 ? "getoond" : "niet getoond (DEBUG aan?)"}`);
  await shot(pn, "404");

  // ---- Beheer ----
  const s = await browser.newContext(ctxOpts);
  const ps = await s.newPage();
  watch(ps);
  await ps.goto(base + "/beheer/inloggen/");
  await ps.fill("#id_username", data.staff);
  await ps.fill("#id_password", data.staff_password);
  await Promise.all([ps.waitForURL(base + "/beheer/"), ps.click("main button[type=submit], button[type=submit]")]);
  check("Beheerder logt in", ps.url().endsWith("/beheer/"));
  for (const [name, url] of [["bestellingen", "/beheer/bestellingen/"], ["verwerking", "/beheer/verwerking/"], ["uitnodiging", `/beheer/uitnodigingen/${data.paid}/`], ["instellingen", "/beheer/instellingen/"]]) {
    const r = await ps.goto(base + url);
    check(`Beheer ${name}`, r.status() === 200, `status ${r.status()}`);
    await shot(ps, `beheer-${name}`);
  }

  check("Geen JavaScript-fouten", errors.length === 0, errors.slice(0, 5).join(" | "));
  const failed = results.filter((r) => !r.ok);
  fs.writeFileSync(path.join(out, `rapport-${width}.json`), JSON.stringify(results, null, 2));
  console.log(`\n${results.length - failed.length}/${results.length} controles ok (${width} px)`);
  await browser.close();
  process.exit(failed.length ? 1 : 0);
})();

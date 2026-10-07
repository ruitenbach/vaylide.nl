// De vereenvoudigde bestelroute in een echte browser: Kies kaart → Personaliseer → Controleer → Bestel (zonder te betalen).
// Gebruik: NODE_PATH=<map met playwright> node e2e/flow_eenvoudig.cjs <basis-url> [chromium|firefox|webkit]
// Draait op ongeveer 390 px (telefoon) en 1366 px (desktop) en schrijft per controle OK of FOUT.
const { chromium, firefox, webkit } = require("playwright");
const BASIS = process.argv[2] || "http://127.0.0.1:8010";
const TYPE = { chromium, firefox, webkit }[process.argv[3] || "chromium"];
const GELEGENHEDEN = ["verjaardag", "bruiloft", "kerst", "babyshower", "jubileum", "verloving", "zakelijk"];
const uit = []; let fouten = 0;
const ok = (naam, waar, extra) => { if (!waar) fouten++; uit.push(`${waar ? "OK  " : "FOUT"} ${naam}${extra ? " | " + extra : ""}`); console.log(uit[uit.length - 1]); };

async function kies(page, mobiel, gelegenheid, nth = 0) {
  await page.goto(`${BASIS}/maken/?gelegenheid=${gelegenheid}`, { waitUntil: "load" });
  const kaarten = page.locator(".kaart-keuze__knop");
  const aantal = await kaarten.count();
  if (!aantal) return { aantal: 0 };
  const t0 = Date.now();
  await (mobiel && TYPE !== firefox ? kaarten.nth(nth).tap() : kaarten.nth(nth).click());
  await page.waitForURL(/\/maken\/[0-9a-f-]{36}\/gegevens\/$/, { timeout: 15000 });
  return { aantal, ms: Date.now() - t0 };
}

(async () => {
  const b = await TYPE.launch();
  for (const [maat, w, h] of [["390", 390, 844], ["1366", 1366, 768]]) {
    const mobiel = w < 600;
    const opt = { viewport: { width: w, height: h } }; if (mobiel && TYPE !== firefox) { opt.isMobile = true; opt.hasTouch = true; }
    const klik = (page, sel) => (mobiel && TYPE !== firefox ? page.locator(sel).first().tap() : page.locator(sel).first().click());
    const fout = [];
    // ---------- A. elke gelegenheid: kaart aanklikken → direct personaliseren, niets verplicht, door naar het volgende onderdeel
    for (const occ of GELEGENHEDEN) {
      const c = await b.newContext(opt); const p = await c.newPage(); p.on("pageerror", (e) => fout.push(String(e).slice(0, 120)));
      let r; try { r = await kies(p, mobiel, occ); } catch (e) { ok(`[${maat}] ${occ}: kaart aanklikken → personaliseren`, false, String(e).slice(0, 100)); await c.close(); continue; }
      if (!r.aantal) { ok(`[${maat}] ${occ}: er zijn kaarten`, false); await c.close(); continue; }
      const st = await p.evaluate(() => ({ ontwerp: (document.querySelector(".deelnav__ontwerp strong") || {}).textContent, req: document.querySelectorAll(".req").length, y: scrollY, fase: (document.querySelector(".wizard-progress [aria-current=step] .wizard-progress__label") || {}).textContent, tabs: [...document.querySelectorAll(".deelnav__balk a")].map((a) => a.textContent.trim()), sw: document.documentElement.scrollWidth + "/" + innerWidth, iw: innerWidth }));
      ok(`[${maat}] ${occ}: kaart aanklikken → direct personaliseren`, /Personaliseer/.test(st.fase) && !!st.ontwerp && st.y === 0, `${r.ms} ms, ontwerp ${st.ontwerp}, onderdelen ${st.tabs.join(" / ")}`);
      ok(`[${maat}] ${occ}: geen verplichte velden getoond, geen horizontale scroll`, st.req === 0 && st.iw === w && +st.sw.split("/")[0] <= st.iw, st.sw);
      const dubbel = st.tabs.filter((t) => /praktische/i.test(t)).length;
      ok(`[${maat}] ${occ}: 'Praktische info' maar één keer in de onderdelen`, dubbel === 1 && (await p.locator("text=/Praktische informatie/").count()) === 0, `${dubbel}x`);
      await klik(p, ".step-actions__next");
      await p.waitForURL(/\/programma\/$/, { timeout: 15000 });
      const na = await p.evaluate(() => ({ pad: location.pathname, fouten: document.querySelectorAll(".field__error, .form-errors").length }));
      ok(`[${maat}] ${occ}: leeg doorgaan naar het volgende onderdeel kan`, /\/programma\/$/.test(na.pad) && na.fouten === 0, na.pad);
      await c.close();
    }

    // ---------- B. diepe route (bruiloft, daarna verjaardag): overslaan, later invullen, wisselen, behouden, controle, bestellen
    for (const occ of ["bruiloft", "verjaardag"]) {
      const c = await b.newContext(opt); const p = await c.newPage(); p.on("pageerror", (e) => fout.push(String(e).slice(0, 120)));
      await kies(p, mobiel, occ);
      const uid = p.url().match(/maken\/([0-9a-f-]{36})\//)[1];
      const eerste = occ === "bruiloft" ? "#id_name_partner_1" : "#id_name_person_name";
      await p.fill(eerste, "Sanne");
      // Wisselen van onderdeel bewaart wat er staat.
      await klik(p, '.deelnav__balk a[data-ga="aanmelden"]');
      await p.waitForURL(/\/aanmelden\/$/, { timeout: 15000 });
      const heeftDeadline = await p.locator("#id_deadline").count();
      ok(`[${maat}] ${occ}: aanmelden ${occ === "bruiloft" ? "zonder 'tot en met'-deadline" : "met optionele deadline"}`, occ === "bruiloft" ? heeftDeadline === 0 : heeftDeadline === 1, `deadline-veld: ${heeftDeadline}`);
      await p.fill("#id_max_party_size", "4");
      await klik(p, '.deelnav__balk a[data-ga="gegevens"]');
      await p.waitForURL(/\/gegevens\/$/, { timeout: 15000 });
      ok(`[${maat}] ${occ}: invoer blijft bewaard na wisselen van onderdeel`, (await p.inputValue(eerste)) === "Sanne");
      await klik(p, '.deelnav__balk a[data-ga="aanmelden"]');
      await p.waitForURL(/\/aanmelden\/$/, { timeout: 15000 });
      ok(`[${maat}] ${occ}: ook het aantal personen is bewaard`, (await p.inputValue("#id_max_party_size")) === "4");
      // Velden overslaan en de kaart bekijken
      await klik(p, ".step-actions__controle");
      await p.waitForURL(/\/voorbeeld\/$/, { timeout: 15000 });
      const ifr = await p.locator("iframe").first().getAttribute("src");
      const html1 = await (await p.request.get(BASIS + ifr.split("?")[0])).text();
      ok(`[${maat}] ${occ}: kaart met ontbrekende velden toont de naam en geen lege kop`, /Sanne/.test(html1) && !/<h[1-6][^>]*>\s*<\/h[1-6]>/.test(html1) && !/>None<|>undefined</.test(html1));
      const tips = await p.locator(".controle__item--nodig").count();
      ok(`[${maat}] ${occ}: ontbrekende gegevens houden het bestellen niet tegen`, tips === 0 && !(await p.locator("a.btn--primary.is-disabled").count()), `blokkerende punten: ${tips}`);
      // Overgeslagen veld later toevoegen
      await klik(p, '.chip-lijst a[href$="/gegevens/"]');
      await p.waitForURL(/\/gegevens\/$/, { timeout: 15000 });
      if (occ !== "verjaardag" || true) {
        await p.fill("#id_venue_name", "De Oranjerie");
        const dag = new Date(Date.now() + 90 * 864e5).toISOString().slice(0, 10);
        await p.fill("#id_date", dag); await p.fill("#id_start_time", "15:00");
      }
      await klik(p, ".step-actions__controle");
      await p.waitForURL(/\/voorbeeld\/$/, { timeout: 15000 });
      const ifr2 = await p.locator("iframe").first().getAttribute("src");
      const html2 = await (await p.request.get(BASIS + ifr2.split("?")[0])).text();
      ok(`[${maat}] ${occ}: later toegevoegde gegevens staan op de kaart`, /De Oranjerie/.test(html2) && /Sanne/.test(html2));
      // Ander ontwerp via Wijzigen: invoer blijft, we komen terug waar we waren
      await klik(p, '.chip-lijst a[href$="/gegevens/"]'); await p.waitForURL(/\/gegevens\/$/);
      await klik(p, '.deelnav__ontwerp a');
      await p.waitForURL(/\/ontwerp\/\?terug=gegevens$/, { timeout: 15000 });
      const tweede = p.locator(".kaart-keuze__knop").nth(1);
      await (mobiel && TYPE !== firefox ? tweede.tap() : tweede.click());
      await p.waitForURL(/\/gegevens\/$/, { timeout: 15000 });
      ok(`[${maat}] ${occ}: ander ontwerp kiezen behoudt de invoer`, (await p.inputValue(eerste)) === "Sanne" && (await p.inputValue("#id_venue_name")) === "De Oranjerie");
      // Door naar controle en bestellen (niet betalen)
      await klik(p, ".step-actions__controle"); await p.waitForURL(/\/voorbeeld\/$/);
      await klik(p, "a.btn--primary"); await p.waitForURL(/\/bestellen\/$/, { timeout: 15000 });
      const bestel = await p.evaluate(() => ({ h1: (document.querySelector("h1") || {}).textContent, prijs: (document.body.innerText.match(/€\s?\d+/) || [""])[0], sw: document.documentElement.scrollWidth + "/" + innerWidth, iw: innerWidth, iw: innerWidth }));
      ok(`[${maat}] ${occ}: bestellen bereikbaar met een prijs`, /Bestellen/.test(bestel.h1) && !!bestel.prijs && bestel.iw === w, `${bestel.prijs}`);
      await c.close();
    }

    // ---------- C. live kaart naast of achter de knop
    {
      const c = await b.newContext(opt); const p = await c.newPage();
      await kies(p, mobiel, "verjaardag");
      await p.fill("#id_name_person_name", "Livetest");
      if (mobiel) { await p.locator(".live-kaart__toggle").first().evaluate((el) => el.click()); }
      await p.waitForTimeout(2500);
      const live = await p.evaluate(() => { const f = document.querySelector("[data-live-frame]"); try { return f.contentDocument.body.innerText.includes("Livetest"); } catch (e) { return "geen toegang"; } });
      ok(`[${maat}] live kaart toont wat je typt (nog vóór het opslaan)`, live === true, String(live));
      await c.close();
    }
    // ---------- D. vanaf een ontwerppagina: 'Kies dit ontwerp' start de kaart direct; 'terug' maakt geen lus
    {
      const c = await b.newContext(opt); const p = await c.newPage(); p.on("pageerror", (e) => fout.push(String(e).slice(0, 120)));
      await p.goto(`${BASIS}/ontwerpen/confetti/?gelegenheid=verjaardag`, { waitUntil: "load" });
      await klik(p, "a[data-kleur-link]");
      await p.waitForURL(/\/maken\/[0-9a-f-]{36}\/gegevens\/$/, { timeout: 15000 }).catch(() => {});
      ok(`[${maat}] ontwerppagina → Kies dit ontwerp → direct personaliseren`, /\/gegevens\/$/.test(p.url()), p.url().replace(BASIS, ""));
      const aantalVoor = await c.pages().length;
      await p.goBack({ waitUntil: "load" }).catch(() => {});
      await p.waitForTimeout(2500);
      ok(`[${maat}] 'terug' vanaf Personaliseren komt weer op de ontwerppagina (geen lus)`, /\/ontwerpen\/confetti\//.test(p.url()), p.url().replace(BASIS, ""));
      await c.close();
    }
    ok(`[${maat}] geen JavaScript-fouten`, fout.length === 0, fout.join(" | "));
  }
  await b.close();
  console.log(fouten ? `\n${fouten} controle(s) FOUT` : "\nalle controles OK");
  process.exit(fouten ? 1 : 0);
})().catch((e) => { console.log("TESTFOUT", String(e).slice(0, 400)); process.exit(2); });

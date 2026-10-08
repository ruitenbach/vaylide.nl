// Info-knop (i) in de Studio en bij Bestellen (templates/partials/info.html, static/js/info.js): openen en sluiten met muis, klik
// buiten, Escape, ×, toetsenbord en focus, maar één tegelijk open, geen submit, ingevulde waarden blijven staan, 1366 en 390 px
// (sheet onderaan, geen horizontale scroll) en prefers-reduced-motion.
// Gebruik: NODE_PATH=<playwright> node e2e/info_uitleg.cjs <basis-url> [chromium|firefox|webkit] [map voor schermafbeeldingen]
const { chromium, firefox, webkit } = require("playwright");
const BASIS = process.argv[2] || "http://127.0.0.1:8010";
const NAAM = process.argv[3] || "chromium";
const TYPE = { chromium, firefox, webkit }[NAAM];
const SHOTS = process.argv[4] || "";
let fouten = 0; const ok = (n, w, e) => { if (!w) fouten++; console.log(`${w ? "OK  " : "FOUT"} [${NAAM}] ${n}${e ? " | " + e : ""}`); };

const staat = (p, id) => p.evaluate((id) => {
  const knop = document.querySelector(`[aria-controls="info-${id}"]`); const paneel = document.getElementById(`info-${id}`);
  let open = false; try { open = paneel.matches(":popover-open"); } catch (e) { open = !paneel.hidden; }
  const r = paneel.getBoundingClientRect(), k = knop.getBoundingClientRect();
  return { open, expanded: knop.getAttribute("aria-expanded"), focusInPaneel: paneel.contains(document.activeElement), focusOpKnop: document.activeElement === knop,
           paneel: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)], knop: [Math.round(k.left), Math.round(k.top), Math.round(k.bottom)],
           overflow: document.documentElement.scrollWidth > window.innerWidth, vh: window.innerHeight, vw: document.body.clientWidth };   // zonder gereserveerde scrollbalkgoot
}, id);
const open = async (p) => p.evaluate(() => [...document.querySelectorAll("[data-info-paneel]")].filter((el) => { try { return el.matches(":popover-open"); } catch (e) { return !el.hidden; } }).length);

(async () => {
  const b = await TYPE.launch();
  const c = await b.newContext({ viewport: { width: 1366, height: 900 } });
  await c.addCookies([{ name: "vaylide_analytics", value: "nee", url: BASIS }]);   // geen toestemmingsbanner over de schermafbeeldingen
  const p = await c.newPage();
  const fout = []; p.on("pageerror", (e) => fout.push(String(e).slice(0, 140)));
  await p.goto(BASIS + "/maken/?ontwerp=liefde-op-papier&gelegenheid=bruiloft&soort=uitnodiging&direct=1", { waitUntil: "load" });
  await p.waitForURL(/\/gegevens\//, { timeout: 15000 });
  const basis = p.url().replace(/gegevens\/.*$/, "");

  // --- Aanmelden, desktop 1366 ---
  await p.goto(basis + "aanmelden/", { waitUntil: "load" });
  await p.fill('[name="max_party_size"]', "3");                       // niet opgeslagen waarde: moet blijven staan
  const adres = p.url();
  const knop = p.locator('[aria-controls="info-aanmelden"]');
  await knop.click(); await p.waitForTimeout(250);
  let s = await staat(p, "aanmelden");
  ok("klik opent het paneel, aria-expanded true, focus in het paneel", s.open && s.expanded === "true" && s.focusInPaneel, JSON.stringify(s));
  ok("desktop: compact paneel vlak bij het icoon", s.paneel[2] <= 330 && Math.abs(s.paneel[1] - s.knop[2]) <= 16 && Math.abs(s.paneel[0] - s.knop[0]) <= 40, `paneel ${s.paneel} knop ${s.knop}`);
  if (SHOTS) await p.screenshot({ path: `${SHOTS}/info-aanmelden-1366.png` });
  await p.mouse.click(1250, 850); await p.waitForTimeout(250);
  s = await staat(p, "aanmelden");
  ok("klik buiten sluit, aria-expanded false", !s.open && s.expanded === "false");
  await knop.click(); await p.waitForTimeout(200); await p.keyboard.press("Escape"); await p.waitForTimeout(250);
  s = await staat(p, "aanmelden");
  ok("Escape sluit en zet de focus terug op het info-icoon", !s.open && s.focusOpKnop, JSON.stringify(s));
  await knop.click(); await p.waitForTimeout(200); await p.locator("#info-aanmelden [data-info-sluit]").click(); await p.waitForTimeout(250);
  s = await staat(p, "aanmelden");
  ok("× sluit en zet de focus terug op het info-icoon", !s.open && s.focusOpKnop);
  await p.keyboard.press("Enter"); await p.waitForTimeout(250);      // de focus staat op de knop
  s = await staat(p, "aanmelden");
  ok("toetsenbord: Enter op de knop opent, focus in het paneel", s.open && s.focusInPaneel);
  if (NAAM === "webkit") {
    // Safari slaat knoppen standaard over met Tab (browserinstelling); daar sluit Escape vanuit het paneel.
    await p.keyboard.press("Escape"); await p.waitForTimeout(250);
  } else {
    await p.keyboard.press("Tab"); await p.waitForTimeout(100);
    const tabNaar = await p.evaluate(() => document.activeElement && document.activeElement.getAttribute("aria-label"));
    ok("toetsenbord: Tab gaat naar de sluitknop in het paneel", tabNaar === "Sluiten", tabNaar);
    await p.keyboard.press("Enter"); await p.waitForTimeout(250);
  }
  s = await staat(p, "aanmelden");
  ok("toetsenbord: sluiten vanuit het paneel, focus terug op de knop", !s.open && s.focusOpKnop);
  await p.locator("#info-aanmelden").evaluate((el) => el.hidden);    // niets
  ok("geen submit of navigatie door het info-icoon", p.url() === adres);
  ok("ingevulde waarde blijft staan", (await p.inputValue('[name="max_party_size"]')) === "3");
  // Een klik op de tekst in het paneel laat alles staan
  await knop.click(); await p.waitForTimeout(200);
  await p.locator("#info-aanmelden .info__tekst").click(); await p.waitForTimeout(150);
  s = await staat(p, "aanmelden");
  ok("klik op de uitlegtekst houdt het paneel open en verandert niets", s.open && (await p.inputValue('[name="max_party_size"]')) === "3" && p.url() === adres);
  await p.keyboard.press("Escape");

  // --- Foto's: muziek ---
  await p.goto(basis + "fotos/", { waitUntil: "load" });
  const muziek = p.locator('[aria-controls="info-muziek"]');
  ok("Foto's: info bij muziek aanwezig", (await muziek.count()) === 1);
  await muziek.click(); await p.waitForTimeout(200);
  s = await staat(p, "muziek");
  ok("Foto's: muziekuitleg opent", s.open && s.expanded === "true");
  await p.keyboard.press("Escape");

  // --- Bestellen: twee info-iconen, maar één open ---
  await p.goto(basis + "bestellen/", { waitUntil: "load" });
  await p.locator('[aria-controls="info-looptijd"]').click(); await p.waitForTimeout(200);
  await p.locator('[aria-controls="info-na-betaling"]').click(); await p.waitForTimeout(250);
  const looptijd = await staat(p, "looptijd"), na = await staat(p, "na-betaling");
  ok("twee iconen: de tweede opent, de eerste sluit (maar één tegelijk)", !looptijd.open && na.open && (await open(p)) === 1 && looptijd.expanded === "false", JSON.stringify([looptijd.open, na.open]));
  if (SHOTS) await p.screenshot({ path: `${SHOTS}/info-bestellen-1366.png` });
  ok("desktop 1366: geen horizontale scroll", !na.overflow);
  await p.keyboard.press("Escape"); await p.waitForTimeout(150);
  await p.locator('[aria-controls="info-looptijd"]').click(); await p.waitForTimeout(250);
  if (SHOTS) await p.screenshot({ path: `${SHOTS}/info-looptijd-1366.png` });
  await p.keyboard.press("Escape");

  // --- Mobiel 390 ---
  await p.setViewportSize({ width: 390, height: 844 });
  await p.goto(basis + "aanmelden/", { waitUntil: "load" });
  await p.locator('[aria-controls="info-aanmelden"]').click(); await p.waitForTimeout(350);
  s = await staat(p, "aanmelden");
  ok("390: sheet onderaan over de volle breedte, niet hoger dan 60% van het scherm", s.open && s.paneel[0] === 0 && s.paneel[2] === s.vw && Math.abs(s.paneel[1] + s.paneel[3] - s.vh) <= 1 && s.paneel[3] <= s.vh * 0.6, `${s.paneel} (breedte ${s.vw})`);
  ok("390: geen horizontale scroll", !s.overflow);
  const sluitMaat = await p.locator("#info-aanmelden [data-info-sluit]").boundingBox();
  ok("390: duidelijke sluitknop (minstens 40 px)", sluitMaat.width >= 40 && sluitMaat.height >= 40, `${Math.round(sluitMaat.width)}x${Math.round(sluitMaat.height)}`);
  if (SHOTS) await p.screenshot({ path: `${SHOTS}/info-aanmelden-390.png` });
  await p.mouse.click(195, 120); await p.waitForTimeout(300);        // tik boven de sheet
  s = await staat(p, "aanmelden");
  ok("390: tik buiten de sheet sluit", !s.open);
  await p.goto(basis + "bestellen/", { waitUntil: "load" });
  await p.locator('[aria-controls="info-na-betaling"]').click(); await p.waitForTimeout(350);
  s = await staat(p, "na-betaling");
  ok("390 Bestellen: sheet open, geen horizontale scroll", s.open && !s.overflow);
  if (SHOTS) await p.screenshot({ path: `${SHOTS}/info-bestellen-390.png` });
  await p.keyboard.press("Escape");

  // --- prefers-reduced-motion ---
  await p.emulateMedia({ reducedMotion: "reduce" });
  await p.setViewportSize({ width: 1366, height: 900 });
  await p.goto(basis + "aanmelden/", { waitUntil: "load" });
  const duur = await p.evaluate(() => getComputedStyle(document.getElementById("info-aanmelden")).transitionDuration);
  ok("prefers-reduced-motion: geen animatie (korter dan 10 ms)", duur.split(",").every((d) => parseFloat(d) < 0.01), duur);
  ok("geen JS-fouten", fout.length === 0, fout.join(" | "));
  await b.close();
  console.log(fouten ? `${fouten} FOUT` : "ALLES OK");
  process.exit(fouten ? 1 : 0);
})().catch((e) => { console.log("TESTFOUT", String(e).slice(0, 300)); process.exit(2); });

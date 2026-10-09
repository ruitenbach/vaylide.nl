// Controle van de effecten (invitations/static/invitations/effects.js), per ontwerp op telefoonformaat:
// - de deeltjes tekenen op het openingsscherm en na het openen;
// - de knal bij het openen en het feestje na aanmelden (voorbeeldformulier, 'Ja, ik kom');
// - de knop 'Beweging': stilzetten, onthouden na herladen en weer aanzetten;
// - 'minder beweging' in het systeem: niets beweegt, de knop is verborgen, de inhoud is zichtbaar;
// - geen fouten in de console.
// Met PERF=1 daarnaast een meting op een vier keer vertraagde processor: beelden per seconde en
// rekentijd per seconde, op het openingsscherm en na het openen.
// Met CHECKS=0 alleen die meting.
// Gebruik (vanuit de projectmap): node e2e/effecten.cjs <basis-url> <uitvoermap> [code ...]
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

const [base, outDir, ...only] = process.argv.slice(2);
fs.mkdirSync(outDir, { recursive: true });
const designs = fs.readdirSync(path.join(process.cwd(), "designs")).filter((d) => !d.startsWith("_") && (!only.length || only.includes(d))).sort();
const report = { checks: [], perf: [] };
const check = (name, ok, detail) => { report.checks.push({ name, ok, detail }); console.log(`${ok ? "ok    " : "FOUT  "} ${name}: ${detail}`); };

// Aantal zichtbare beeldpunten op een tekenvlak, op ware grootte geteld. (Verkleind tellen liet
// fijne, schaarse deeltjes zoals 'stofjes' soms wegvallen, terwijl ze wel getekend waren.)
async function inked(page, selector) {
  return page.evaluate((sel) => {
    const canvas = document.querySelector(sel);
    if (!canvas || !canvas.width) return -1;
    const probe = document.createElement("canvas");
    probe.width = canvas.width; probe.height = canvas.height;
    const g = probe.getContext("2d");
    g.drawImage(canvas, 0, 0);
    const data = g.getImageData(0, 0, probe.width, probe.height).data;
    let n = 0;
    for (let i = 3; i < data.length; i += 4) if (data[i] > 8) n++;
    return n;
  }, selector);
}

async function settings(page) {
  return page.evaluate(() => ({ sfeer: document.documentElement.getAttribute("data-fx-sfeer"), knal: document.documentElement.getAttribute("data-fx-knal") }));
}

(async () => {
  const browser = await chromium.launch();
  for (const slug of process.env.CHECKS === "0" ? [] : designs) {
    const demo = `${base}/voorbeeld/${slug}/`;
    // 1. Beweging aan: openingsscherm, knal, kop, feestje na aanmelden.
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
      const p = await ctx.newPage();
      const errors = [];
      p.on("pageerror", (e) => errors.push(String(e)));
      p.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
      await p.goto(demo, { waitUntil: "networkidle" });
      await p.waitForTimeout(1600);
      const fx = await settings(p);
      const coverInk = await inked(p, "[data-cover] .fx-canvas");
      const toggleVisible = await p.isVisible("[data-fx-toggle]");
      check(`${slug} · Deeltjes op het openingsscherm (${fx.sfeer})`, coverInk > 0 && toggleVisible, `getekende punten: ${coverInk}, knop 'Beweging' zichtbaar: ${toggleVisible}`);
      await p.click("[data-cover] [data-open]", { force: true });
      // De knal valt op het moment uit data-fx-delay van het openingsscherm (bij Gouden licht pas als het licht doorbreekt).
      const burstDelay = await p.evaluate(() => parseInt((document.querySelector("[data-cover]") || {}).getAttribute?.("data-fx-delay") || "0", 10));
      await p.waitForTimeout(Math.max(650, burstDelay + 450));
      const burstInk = await inked(p, ".fx-burst .fx-canvas");
      check(`${slug} · Knal bij het openen (${fx.knal})`, fx.knal === "geen" || burstInk > 0, `getekende punten: ${burstInk}`);
      await p.waitForFunction(() => document.documentElement.classList.contains("fx-done"), null, { timeout: 9000 });
      await p.waitForTimeout(600);
      const after = await p.evaluate(() => {
        const h1 = document.querySelector("h1");
        const style = h1 && getComputedStyle(h1);
        return { h1: !!h1 && style.opacity === "1" && h1.getBoundingClientRect().height > 0, pageRunning: !!document.querySelector(".fx-slot--page.is-running") };
      });
      const pageInk = await inked(p, ".fx-slot--page .fx-canvas");
      check(`${slug} · Na het openen: kop zichtbaar en sfeer loopt`, after.h1 && after.pageRunning && pageInk > 0, `kop zichtbaar: ${after.h1}, sfeer actief: ${after.pageRunning}, getekende punten: ${pageInk}`);
      await p.screenshot({ path: path.join(outDir, `effect-${slug}-open.png`) });
      // Feestje na aanmelden in het voorbeeld.
      await p.fill("#rsvp-name", "Test Gast");
      await p.check("input[name='attending'][value='ja']");
      await p.evaluate(() => document.querySelector("[data-rsvp-form]").scrollIntoView({ block: "center" }));
      await p.waitForTimeout(300);
      await p.click("[data-rsvp-submit]");
      await p.waitForTimeout(450);
      const partyInk = await inked(p, ".fx-burst .fx-canvas");
      const status = (await p.textContent("[data-rsvp-status]")) || "";
      check(`${slug} · Feestje na aanmelden`, partyInk > 0 && status.includes("voorbeeld"), `getekende punten: ${partyInk}, melding: '${status.slice(0, 40)}…'`);
      check(`${slug} · Geen fouten in de console`, errors.length === 0, errors.join(" | ") || "geen");
      await ctx.close();
    }
    // 2. Knop 'Beweging': stilzetten, onthouden, weer aanzetten.
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
      const p = await ctx.newPage();
      await p.goto(demo + "#uitnodiging", { waitUntil: "networkidle" });
      await p.waitForTimeout(1200);
      await p.click("[data-fx-toggle]");
      await p.waitForTimeout(300);
      const paused = await p.evaluate(() => ({
        pressed: document.querySelector("[data-fx-toggle]").getAttribute("aria-pressed"),
        motion: document.documentElement.classList.contains("fx-motion"),
        running: document.querySelectorAll(".fx-slot.is-running").length,
        loops: document.getAnimations().filter((a) => a.playState === "running" && a.effect && a.effect.getTiming().iterations === Infinity).length,
      }));
      const inkA = await inked(p, ".fx-slot--page .fx-canvas");
      await p.waitForTimeout(500);
      const inkB = await inked(p, ".fx-slot--page .fx-canvas");
      check(`${slug} · Beweging stilzetten`, paused.pressed === "true" && !paused.motion && paused.running === 0 && paused.loops === 0 && inkA === inkB,
        `ingedrukt: ${paused.pressed}, actieve vlakken: ${paused.running}, lopende herhalende animaties: ${paused.loops}, beeld ongewijzigd: ${inkA === inkB}`);
      await p.reload({ waitUntil: "networkidle" });
      await p.waitForTimeout(800);
      const remembered = await p.evaluate(() => document.querySelector("[data-fx-toggle]").getAttribute("aria-pressed") === "true" && document.documentElement.classList.contains("fx-paused"));
      await p.click("[data-fx-toggle]");
      await p.waitForTimeout(900);
      const resumed = await p.evaluate(() => document.documentElement.classList.contains("fx-motion") && !!document.querySelector(".fx-slot.is-running"));
      check(`${slug} · Keuze onthouden en weer aanzetten`, remembered && resumed, `onthouden: ${remembered}, weer aan: ${resumed}`);
      await ctx.close();
    }
    // 3. Minder beweging in het systeem.
    {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: "reduce" });
      const p = await ctx.newPage();
      await p.goto(demo, { waitUntil: "networkidle" });
      await p.waitForTimeout(800);
      const before = await p.evaluate(() => ({ motion: document.documentElement.classList.contains("fx-motion"), toggle: !document.querySelector("[data-fx-toggle]").hidden, running: document.querySelectorAll(".fx-slot.is-running").length }));
      await p.click("[data-cover] [data-open]", { force: true });
      await p.waitForTimeout(900);
      const after = await p.evaluate(() => ({
        burst: !!document.querySelector(".fx-burst"),
        loops: document.getAnimations().filter((a) => a.playState === "running").length,
        h1: getComputedStyle(document.querySelector("h1")).opacity === "1",
      }));
      check(`${slug} · Minder beweging: niets beweegt`, !before.motion && !before.toggle && before.running === 0 && !after.burst && after.loops === 0 && after.h1,
        `beweging: ${before.motion}, knop zichtbaar: ${before.toggle}, actieve vlakken: ${before.running}, knal: ${after.burst}, lopende animaties: ${after.loops}, kop zichtbaar: ${after.h1}`);
      await ctx.close();
    }
  }
  // 4. Belasting op een trage telefoon (optioneel).
  if (process.env.PERF === "1") {
    for (const slug of designs) {
      const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
      const p = await ctx.newPage();
      const cdp = await ctx.newCDPSession(p);
      await cdp.send("Performance.enable");
      await cdp.send("Emulation.setCPUThrottlingRate", { rate: 4 });
      await p.goto(`${base}/voorbeeld/${slug}/`, { waitUntil: "networkidle" });
      await p.waitForTimeout(1500);
      const measure = async () => {
        const m0 = Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map((m) => [m.name, m.value]));
        const frames = await p.evaluate(() => new Promise((resolve) => { let n = 0; const t0 = performance.now(); function f(t) { n++; if (t - t0 < 3000) requestAnimationFrame(f); else resolve(n / ((t - t0) / 1000)); } requestAnimationFrame(f); }));
        const m1 = Object.fromEntries((await cdp.send("Performance.getMetrics")).metrics.map((m) => [m.name, m.value]));
        const secs = m1.Timestamp - m0.Timestamp;
        return { fps: Math.round(frames), busy: Math.round(((m1.TaskDuration - m0.TaskDuration) / secs) * 1000) };
      };
      const cover = await measure();
      await p.click("[data-cover] [data-open]", { force: true });
      await p.waitForTimeout(6000);
      const page = await measure();
      report.perf.push({ slug, cover, page });
      console.log(`perf  ${slug}: openingsscherm ${cover.fps} beelden/s, ${cover.busy} ms rekentijd per s · na openen ${page.fps} beelden/s, ${page.busy} ms per s`);
      await ctx.close();
    }
  }
  fs.writeFileSync(path.join(outDir, "effecten.json"), JSON.stringify(report, null, 2));
  console.log(`\nControles: ${report.checks.filter((c) => c.ok).length}/${report.checks.length} ok`);
  await browser.close();
})();

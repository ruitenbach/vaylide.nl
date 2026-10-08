// Toestemming voor Microsoft Clarity in een echte browser: weigeren, accepteren, intrekken en afschermen. Alle verzoeken naar clarity.ms
// en bing.com worden onderschept (er gaat niets naar Microsoft); een nep-tag legt vast welke consentv2-aanroepen Clarity zou krijgen.
// Gebruik (server met VIERLIEF_CLARITY_ID): NODE_PATH=<playwright> node e2e/clarity_toestemming.cjs <basis-url> [chromium|firefox|webkit]
const { chromium, firefox, webkit } = require("playwright");
const BASIS = process.argv[2] || "http://127.0.0.1:8010";
const TYPE = { chromium, firefox, webkit }[process.argv[3] || "chromium"];
let fouten = 0; const ok = (n, w, e) => { if (!w) fouten++; console.log(`${w ? "OK  " : "FOUT"} ${n}${e ? " | " + e : ""}`); };
// Nep-tag: verwerkt de wachtrij zoals Clarity, zet de cookies die Clarity bij 'granted' zou zetten en wist ze bij 'denied'.
// Het logboek staat ook in sessionStorage: bij intrekken laadt de pagina meteen opnieuw.
const NEP_TAG = `(function(){var q=(window.clarity&&window.clarity.q)||[];window.__clarityLog=[];function f(){var a=[].slice.call(arguments);window.__clarityLog.push(JSON.stringify(a));
 try{sessionStorage.setItem("__clarityLog",(sessionStorage.getItem("__clarityLog")||"")+JSON.stringify(a)+"\\n")}catch(e){}
 if(a[0]==="consentv2"){if(a[1].analytics_Storage==="granted"){document.cookie="_clck=nep; Path=/; Max-Age=3600";document.cookie="_clsk=nep; Path=/; Max-Age=3600";}
 else{document.cookie="_clck=; Path=/; Max-Age=0";document.cookie="_clsk=; Path=/; Max-Age=0";}}}
 q.forEach(function(a){f.apply(null,a)});window.clarity=f;window.__clarityTagGeladen=(window.__clarityTagGeladen||0)+1;})();`;

(async () => {
  const b = await TYPE.launch();
  for (const [maat, w, h] of [["390", 390, 844], ["1366", 1366, 768]]) {
    const opt = { viewport: { width: w, height: h } }; if (w < 600 && TYPE !== firefox) { opt.isMobile = true; opt.hasTouch = true; }
    const nieuw = async () => {
      const c = await b.newContext(opt); const p = await c.newPage(); const verzoeken = []; const fout = [];
      await c.route(/clarity\.ms|bing\.com/, (route) => { verzoeken.push(route.request().url()); return route.fulfill({ status: 200, contentType: "application/javascript", body: NEP_TAG }); });
      p.on("pageerror", (e) => fout.push(String(e).slice(0, 120))); p.on("console", (m) => { if (m.type() === "error") fout.push(m.text().slice(0, 120)); });
      return { c, p, verzoeken, fout };
    };
    const cookies = async (c) => (await c.cookies()).map((x) => x.name);
    const klik = async (p, sel) => p.locator(sel).first().click();

    // 1. Eerste bezoek: banner, nog niets geladen. Weigeren: geen Clarity, geen cookies, ook niet op volgende pagina's.
    let { c, p, verzoeken, fout } = await nieuw();
    await p.goto(BASIS + "/", { waitUntil: "load" }); await p.waitForTimeout(600);
    ok(`[${maat}] eerste bezoek: banner zichtbaar, Clarity niet geladen`, await p.locator("[data-toestemming]").isVisible() && verzoeken.length === 0);
    const knoppen = await p.evaluate(() => [...document.querySelectorAll("[data-toestemming-keuze]")].map((k) => { const r = k.getBoundingClientRect(); const s = getComputedStyle(k); return [k.textContent.trim(), Math.round(r.width), Math.round(r.height), s.backgroundColor, s.color, s.borderColor]; }));
    ok(`[${maat}] Accepteren en Weigeren zijn gelijkwaardig`, knoppen.length === 2 && JSON.stringify(knoppen[0].slice(1)) === JSON.stringify(knoppen[1].slice(1)), knoppen.map((k) => k.slice(0, 3).join(" ")).join(" / "));
    await klik(p, '[data-toestemming-keuze="nee"]'); await p.waitForTimeout(500);
    for (const adres of ["/ontwerpen/", "/maken/?gelegenheid=bruiloft", "/prijzen/"]) { await p.goto(BASIS + adres, { waitUntil: "load" }); await p.waitForTimeout(400); }
    let ck = await cookies(c);
    ok(`[${maat}] weigeren: geen Clarity-verzoek, geen Clarity-cookies, banner weg`, verzoeken.length === 0 && !ck.includes("_clck") && !ck.includes("_clsk") && ck.includes("vaylide_analytics") && !(await p.locator("[data-toestemming]").isVisible()), `verzoeken ${verzoeken.length}, cookies ${ck.join(",")}`);
    const keuze = (await c.cookies()).find((x) => x.name === "vaylide_analytics");
    ok(`[${maat}] keuze 12 maanden bewaard`, keuze && keuze.value === "nee" && Math.round((keuze.expires * 1000 - Date.now()) / 864e5) >= 364, keuze && `${keuze.value}, ${Math.round((keuze.expires * 1000 - Date.now()) / 864e5)} dagen`);
    ok(`[${maat}] weigeren: geen JS-fouten`, fout.length === 0, fout.join(" | "));
    await c.close();

    // 2. Accepteren: Clarity laadt één keer met consentv2 analytics granted, ad denied; ook op de volgende pagina.
    ({ c, p, verzoeken, fout } = await nieuw());
    await p.goto(BASIS + "/ontwerpen/", { waitUntil: "load" }); await p.waitForTimeout(400);
    await klik(p, '[data-toestemming-keuze="ja"]'); await p.waitForTimeout(800);
    let log = await p.evaluate(() => window.__clarityLog || []);
    const tags = verzoeken.filter((u) => /www\.clarity\.ms\/tag\/yuemn2aqz1/.test(u));
    ok(`[${maat}] accepteren: tag één keer geladen voor yuemn2aqz1`, tags.length === 1 && (await p.evaluate(() => window.__clarityTagGeladen)) === 1, verzoeken.join(" "));
    ok(`[${maat}] accepteren: eerste aanroep is consentv2 met analytics granted en ad denied`, log[0] === JSON.stringify(["consentv2", { ad_Storage: "denied", analytics_Storage: "granted" }]), log.join(" "));
    await p.goto(BASIS + "/maken/?gelegenheid=verjaardag", { waitUntil: "load" }); await p.waitForTimeout(800);
    log = await p.evaluate(() => window.__clarityLog || []);
    ok(`[${maat}] volgende pagina: zonder banner opnieuw geladen met dezelfde toestemming`, !(await p.locator("[data-toestemming]").isVisible()) && log[0] === JSON.stringify(["consentv2", { ad_Storage: "denied", analytics_Storage: "granted" }]));
    // Afschermen: alle invoer, formulieren, frames en het concept in de Studio zitten binnen data-clarity-mask
    await p.locator(".kaart-keuze__knop").first().click(); await p.waitForURL(/gegevens\/$/); await p.waitForTimeout(800);
    await p.fill("#id_name_person_name", "Geheime Naam");
    const onbeschermd = await p.evaluate(() => {
      const fout = [];
      document.querySelectorAll("input, textarea, select, iframe, form").forEach((el) => { if (el.type !== "hidden" && !el.closest('[data-clarity-mask="True"]')) fout.push(el.tagName + (el.name ? "[" + el.name + "]" : "")); });
      // tekst die de klant invulde mag nergens buiten een afgeschermd blok staan
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      while (walker.nextNode()) { const n = walker.currentNode; if (/Geheime Naam/.test(n.textContent) && !n.parentElement.closest('[data-clarity-mask="True"]')) fout.push("tekst: " + n.textContent.trim().slice(0, 40)); }
      return fout;
    });
    ok(`[${maat}] Studio: alle velden, formulieren en frames afgeschermd`, onbeschermd.length === 0, onbeschermd.join(", "));
    ok(`[${maat}] Studio: concept, live kaart en voorvertoning binnen het afgeschermde blok`, await p.evaluate(() => !!document.querySelector('[data-clarity-mask="True"] .studio-live__main') && !!document.querySelector('[data-clarity-mask="True"] [data-live-frame]')));
    // Uitnodiging, Mijn VAYLIDE en inloggen: geen Clarity, ook met toestemming
    const voor = verzoeken.length;
    await p.goto(BASIS + "/inloggen/", { waitUntil: "load" }); await p.waitForTimeout(600);
    ok(`[${maat}] inloggen: geen Clarity, ook met toestemming`, verzoeken.length === voor && !(await p.evaluate(() => !!window.__clarityTagGeladen)));

    // 3. Intrekken via Cookie-instellingen: consentv2 denied, cookies weg, pagina opnieuw zonder Clarity
    await p.goto(BASIS + "/prijzen/", { waitUntil: "load" }); await p.waitForTimeout(800);
    ck = await cookies(c);
    ok(`[${maat}] met toestemming staan de Clarity-cookies er (nep-tag)`, ck.includes("_clck") && ck.includes("_clsk"), ck.join(","));
    await p.evaluate(() => { window.__voorIntrekken = true; });
    await klik(p, "[data-cookie-instellingen]");
    ok(`[${maat}] Cookie-instellingen opent de keuze opnieuw`, await p.locator("[data-toestemming]").isVisible());
    await klik(p, '[data-toestemming-keuze="nee"]');
    await p.waitForLoadState("load"); await p.waitForTimeout(1200);
    const intrekLog = (await p.evaluate(() => sessionStorage.getItem("__clarityLog") || "")).split("\n").filter(Boolean);
    ck = await cookies(c);
    const naHerladen = await p.evaluate(() => ({ herladen: !window.__voorIntrekken, geladen: !!window.__clarityTagGeladen }));
    ok(`[${maat}] intrekken: consentv2 met beide op denied`, intrekLog.includes(JSON.stringify(["consentv2", { ad_Storage: "denied", analytics_Storage: "denied" }])), intrekLog.slice(-1).join(""));
    ok(`[${maat}] intrekken: Clarity-cookies gewist, pagina opnieuw geladen zonder Clarity`, !ck.includes("_clck") && !ck.includes("_clsk") && naHerladen.herladen && !naHerladen.geladen, `cookies ${ck.join(",")}, ${JSON.stringify(naHerladen)}`);
    const tagsNa = verzoeken.length;
    await p.goto(BASIS + "/ontwerpen/", { waitUntil: "load" }); await p.waitForTimeout(600);
    ok(`[${maat}] na intrekken: geen nieuwe Clarity-verzoeken`, verzoeken.length === tagsNa);
    ok(`[${maat}] geen JS-fouten`, fout.length === 0, fout.join(" | "));
    await c.close();
  }
  await b.close();
  console.log(fouten ? `\n${fouten} controle(s) FOUT` : "\nalle controles OK"); process.exit(fouten ? 1 : 0);
})().catch((e) => { console.log("TESTFOUT", String(e).slice(0, 400)); process.exit(2); });

// Google Tag Manager / GA4 en de toestemming: wat de browser doet. Het script van Google wordt vervangen door een stukje dat alleen onthoudt dát het geladen is
// (zo testen we onze eigen code: wanneer laden, in welke volgorde, wat in de datalaag staat en dat intrekken alles stopt). Wat Google met een echte container
// doet, controleer je op staging (docs/GTM.md).
// Gebruik (server met VIERLIEF_GTM_ID=GTM-… en VIERLIEF_ANALYTICS_OMGEVING=staging):
//   CHROME="C:/Program Files/Google/Chrome/Application/chrome.exe" node e2e/gtm_toestemming.cjs http://127.0.0.1:8002
const { chromium } = require("playwright");
const [base] = process.argv.slice(2);
const GTM = process.env.GTM || "GTM-M8N863VG";
let goed = 0, fout = 0;
const check = (naam, ok, extra) => { if (ok) goed++; else fout++; console.log((ok ? "  ok  " : "  FOUT ") + naam + (ok ? "" : "  -> " + JSON.stringify(extra))); };
const GOOGLE = /googletagmanager\.com|google-analytics\.com|analytics\.google\.com/;
const UUID = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;

async function nieuw(browser) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });
  const verkeer = [], fouten = [];
  await ctx.route(GOOGLE, async (route) => {
    verkeer.push(route.request().url());
    if (/gtm\.js/.test(route.request().url())) {
      await route.fulfill({ contentType: "text/javascript", body: "window.__gtmGeladen=(window.__gtmGeladen||0)+1;window.dataLayer=window.dataLayer||[];" });
    } else await route.fulfill({ status: 204, body: "" });
  });
  const page = await ctx.newPage();
  page.on("pageerror", (e) => fouten.push(e.message));
  page.on("console", (m) => { if (m.type() === "error") fouten.push(m.text()); });
  return { ctx, page, verkeer, fouten };
}
const datalaag = (page) => page.evaluate(() => (window.dataLayer || []).map((x) => (x && x.length !== undefined && typeof x !== "string" && !Array.isArray(x) && x[0] ? Array.from(x) : x)));

(async () => {
  const browser = await chromium.launch({ ...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}) });

  console.log("1. Zonder keuze: niets van Google");
  let { ctx, page, verkeer, fouten } = await nieuw(browser);
  await page.goto(base + "/ontwerpen/", { waitUntil: "load" }); await page.waitForTimeout(1500);
  check("de vraag staat er, de datalaag bestaat niet, geen verkeer, geen cookies", (await page.locator("[data-toestemming]").isVisible()) && (await page.evaluate(() => typeof window.dataLayer)) === "undefined" && verkeer.length === 0 && (await ctx.cookies()).every((c) => !/^_g/.test(c.name)), { verkeer });
  check("de gebeurtenissen van de pagina staan in de pagina, nog niet in de browser", (await page.getAttribute("[data-toestemming]", "data-gtm-events")) === '[{"event":"view_collection"}]');

  console.log("2. Weigeren: nog steeds niets");
  await page.click('[data-toestemming-keuze="nee"]'); await page.waitForTimeout(800);
  await page.goto(base + "/ontwerpen/", { waitUntil: "load" }); await page.waitForTimeout(1000);
  check("na Weigeren geen verkeer en geen datalaag, ook niet op een volgende pagina", verkeer.length === 0 && (await page.evaluate(() => typeof window.dataLayer)) === "undefined" && !(await page.locator("[data-toestemming]").isVisible()), { verkeer });
  await ctx.close();

  console.log("3. Accepteren: één keer laden, eerst de toestemming, schone gegevens, dan de gebeurtenissen");
  ({ ctx, page, verkeer, fouten } = await nieuw(browser));
  await page.goto(base + "/ontwerpen/?gelegenheid=bruiloft&naam=Zwaluwstaart", { waitUntil: "load" }); await page.waitForTimeout(800);
  await page.click('[data-toestemming-keuze="ja"]'); await page.waitForTimeout(1200);
  const dl = await datalaag(page);
  check("gtm.js is precies één keer opgevraagd, voor de juiste container", verkeer.filter((u) => /gtm\.js/.test(u)).length === 1 && verkeer.some((u) => u.includes("id=" + GTM)), verkeer);
  check("volgorde: consent default (alleen analyse), paginagegevens, gtm.start, dan de gebeurtenis", dl.length >= 4 && dl[0][0] === "consent" && dl[0][1] === "default" && dl[0][2].analytics_storage === "granted" && dl[0][2].ad_storage === "denied" && dl[0][2].ad_user_data === "denied" && dl[0][2].ad_personalization === "denied"
        && dl[1].pagina_url && dl[2].event === "gtm.js" && dl[3].event === "view_collection", dl);
  check("de paginalocatie is schoon (alleen gelegenheid, nooit de rest van de query)", /\/ontwerpen\/\?gelegenheid=bruiloft$/.test(dl[1].pagina_url) && !/Zwaluwstaart|naam/.test(JSON.stringify(dl)), dl[1]);
  check("omgeving staging en testverkeer (debug), nog geen referrer-id's", dl[1].omgeving === "staging" && dl[1].debug === true && !UUID.test(dl[1].pagina_ref || ""), dl[1]);
  check("tweede keer klikken of opnieuw laden-aanroep laadt niet nog eens", await page.evaluate(() => window.__gtmGeladen === 1));
  check("er zijn nog geen Google-cookies (alleen de container is nagebootst)", (await ctx.cookies()).filter((c) => /^_g/.test(c.name)).length === 0);

  console.log("4. Studio en bestellen: gebeurtenissen één keer, zonder id's of invoer");
  const kies = await ctx.request.get(base + "/maken/?gelegenheid=bruiloft&ontwerp=liefde-op-papier");
  const token = (await kies.text()).match(/name="csrfmiddlewaretoken" value="([^"]+)"/)[1];
  const post = await ctx.request.post(base + "/maken/", { form: { csrfmiddlewaretoken: token, occasion: "bruiloft", template: "liefde-op-papier", soort: "uitnodiging" }, maxRedirects: 0, headers: { Referer: base + "/maken/" } });
  const gegevens = post.headers()["location"];
  check("een concept maken geeft een doorverwijzing naar de eerste stap", post.status() === 302 && /\/maken\/[0-9a-f-]{36}\/gegevens\//.test(gegevens), { status: post.status(), gegevens });
  verkeer.length = 0;
  await page.goto(new URL(gegevens, base).href + "?naam=Zwaluwstaart", { waitUntil: "load" }); await page.waitForTimeout(1500);
  let dl2 = await datalaag(page);
  const namen = dl2.filter((x) => x && x.event && !/^gtm\./.test(x.event)).map((x) => x.event);
  check("select_design en start_studio, met alleen ontwerp en gelegenheid", JSON.stringify(namen) === JSON.stringify(["select_design", "start_studio"]) && dl2.filter((x) => x.event === "start_studio")[0].design === "liefde-op-papier" && dl2.filter((x) => x.event === "start_studio")[0].occasion === "bruiloft", dl2);
  check("de paginalocatie heeft geen concept-id en geen query", /\/maken\/:id\/gegevens\/$/.test(dl2[1].pagina_url) && !UUID.test(JSON.stringify(dl2)) && !/Zwaluwstaart/.test(JSON.stringify(dl2)), dl2[1]);
  check("na toestemming laadt de volgende pagina Google automatisch, opnieuw één keer", verkeer.filter((u) => /gtm\.js/.test(u)).length === 1);
  await page.goto(new URL(gegevens, base).href, { waitUntil: "load" }); await page.waitForTimeout(800);
  dl2 = await datalaag(page);
  check("dezelfde stap nog eens: geen tweede start_studio", !dl2.some((x) => x && x.event === "start_studio"), dl2.map((x) => x.event));
  await page.goto(new URL(gegevens, base).href.replace("/gegevens/", "/bestellen/"), { waitUntil: "load" }); await page.waitForTimeout(1000);
  dl2 = await datalaag(page);
  check("Bestellen: reach_checkout (met ontwerp en gelegenheid), nog geen purchase_success", dl2.some((x) => x && x.event === "reach_checkout" && x.design === "liefde-op-papier") && !dl2.some((x) => x && x.event === "purchase_success"), dl2.map((x) => x.event));

  console.log("5. Intrekken: direct niets meer, daarna een pagina zonder Google");
  verkeer.length = 0;
  await page.evaluate(() => { window.__voor = performance.now(); });
  await page.click("[data-cookie-instellingen]").catch(() => {});
  await page.click('[data-toestemming-keuze="nee"]'); await page.waitForLoadState("load"); await page.waitForTimeout(2000);
  check("geen enkel verzoek naar Google na het intrekken (ook niet de herlaadde pagina)", verkeer.length === 0, verkeer);
  check("de herlaadde pagina heeft geen datalaag, geen Google-cookies en vraagt niet opnieuw", (await page.evaluate(() => typeof window.dataLayer)) === "undefined" && (await ctx.cookies()).every((c) => !/^_g/.test(c.name)) && !(await page.locator("[data-toestemming]").isVisible()));
  check("de keuze is nee en blijft zo", (await ctx.cookies()).some((c) => c.name === "vaylide_analytics" && c.value === "nee"));
  await page.goto(base + "/ontwerpen/", { waitUntil: "load" }); await page.waitForTimeout(1000);
  check("ook later niets van Google", verkeer.length === 0 && (await page.evaluate(() => typeof window.dataLayer)) === "undefined");
  check("geen consolefouten (laden, accepteren, studio, intrekken)", fouten.filter((f) => !/Failed to load resource.*(204|net::)/.test(f)).length === 0, fouten);
  await ctx.close();

  console.log("6. Pagina's waar niet gemeten mag worden");
  ({ ctx, page, verkeer, fouten } = await nieuw(browser));
  await ctx.addCookies([{ name: "vaylide_analytics", value: "ja", url: base }]);
  for (const pad of ["/contact/", "/inloggen/", "/privacy/", "/voorbeeld/liefde-op-papier/?gelegenheid=bruiloft"]) {
    await page.goto(base + pad, { waitUntil: "load" }); await page.waitForTimeout(700);
    check(`${pad}: ook met toestemming niets van Google`, verkeer.length === 0 && (await page.evaluate(() => typeof window.dataLayer)) === "undefined", verkeer);
  }
  await ctx.close();
  await browser.close();
  console.log(`\n${goed} ok, ${fout} fout`);
  process.exit(fout ? 1 : 0);
})();

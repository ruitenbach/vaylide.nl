/* Toestemming voor bezoekersanalyse: Microsoft Clarity en/of Google Analytics 4 via Google Tag Manager. Alleen geladen als VIERLIEF_CLARITY_ID of
   VIERLIEF_GTM_ID is ingesteld (templates/base.html). Eén keuze (Accepteren of Weigeren) geldt voor beide.
   - Zonder keuze of na Weigeren laadt er niets: geen script, geen cookies, ook geen cookieloze meting.
   - Na Accepteren laden Clarity en Google Tag Manager één keer, asynchroon. Clarity krijgt via consentv2: analytics_Storage granted, ad_Storage denied.
     Google Tag Manager krijgt vóór het laden consent default: analytics_storage granted en alle advertentiedoelen denied, daarna een schone paginalocatie
     (zonder id's, zie core/analytics.py) en de gebeurtenissen van deze pagina (start_studio enzovoort). Er gaat geen invoer van de bezoeker mee.
   - Intrekken (via Cookie-instellingen), als er al iets geladen was: eerst alle verkeer naar Clarity en Google dicht (een extra CSP-regel, de browser
     houdt zich eraan), dan Clarity consentv2 met beide op denied, de herstart die Clarity daarna zelf plant annuleren, Google consent update op denied,
     de cookies van Clarity en Google op deze site wissen, en dan pas de pagina opnieuw laden, zonder Clarity en zonder Google. Er gaat na het intrekken
     niets meer naar Microsoft of Google: geen laatste pakket, geen nieuwe sessie.
   De keuze staat in de noodzakelijke cookie vaylide_analytics (12 maanden). Zie core/analytics.py, docs/CLARITY.md en docs/GTM.md. */
(function () {
  "use strict";
  var banner = document.querySelector("[data-toestemming]");
  if (!banner) return;
  var COOKIE = "vaylide_analytics";
  var JAAR = 365 * 24 * 60 * 60;
  var id = banner.getAttribute("data-clarity-id") || "";
  var hier = banner.getAttribute("data-clarity-hier") === "1";      // mag Clarity op deze pagina draaien?
  var gtmId = banner.getAttribute("data-gtm-id") || "";
  var gtmHier = banner.getAttribute("data-gtm-hier") === "1";        // mag Google Tag Manager op deze pagina draaien?
  var vraagHier = banner.hasAttribute("data-analyse-hier") ? banner.getAttribute("data-analyse-hier") === "1" : (hier || gtmHier);
  var UUID = /[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}/g;

  function keuze() {
    var m = document.cookie.match(/(?:^|;\s*)vaylide_analytics=(ja|nee)(?:;|$)/);
    return m ? m[1] : "";
  }
  function bewaar(waarde) {
    document.cookie = COOKIE + "=" + waarde + "; Max-Age=" + JAAR + "; Path=/; SameSite=Lax" + (location.protocol === "https:" ? "; Secure" : "");
  }
  function heeft(naam) { return new RegExp("(?:^|;\\s*)" + naam.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=").test(document.cookie); }
  function wisCookies(namen) {
    // Alleen wissen wat er echt staat, eerst zonder domein, dan per domein (de cookies kunnen op het hoofddomein staan); cookies van Microsoft of Google
    // op hun eigen domeinen kan deze site niet wissen (Clarity ruimt die zelf op bij 'denied'; Google zet hier alleen cookies op deze site).
    var host = location.hostname, pogingen = [""];
    if (!/^[\d.]+$/.test(host) && host.indexOf(":") < 0) {
      var delen = host.split(".");
      for (var i = 0; i < delen.length - 1; i++) pogingen.push("." + delen.slice(i).join("."));
    }
    namen.forEach(function (naam) {
      for (var j = 0; j < pogingen.length && heeft(naam); j++) {
        document.cookie = naam + "=; Max-Age=0; Path=/" + (pogingen[j] ? "; Domain=" + pogingen[j] : "");
      }
    });
  }
  function wisClarityCookies() { wisCookies(["_clck", "_clsk"]); }
  function wisGoogleCookies() {
    // _ga, _ga_<ID>, _gid, _gat…, _gcl_… (GA4 zet alleen _ga en _ga_<ID> als de advertentiedoelen uit staan; de rest voor de zekerheid).
    var namen = document.cookie.split(";").map(function (c) { return c.split("=")[0].trim(); }).filter(function (n) { return /^(_ga|_gid|_gat|_gcl_|_gac_)/.test(n); });
    wisCookies(namen);
  }
  function maskeer() {
    // Extra zekerheid naast de attributen in de templates: alles waar een klant of gast iets in kan typen of kiezen, meldingen en kaartframes.
    document.querySelectorAll("form, input, textarea, select, iframe, [data-gevoelig], .flash-wrap").forEach(function (el) {
      el.setAttribute("data-clarity-mask", "True");
    });
  }
  function sluitVerkeer() {
    // Eén extra Content-Security-Policy op deze pagina: de browser laat daarna niets meer naar andere sites gaan (geen script, geen beacon, geen beeldje).
    var csp = document.createElement("meta");
    csp.httpEquiv = "Content-Security-Policy";
    csp.content = "connect-src 'self'; img-src 'self' data: blob:";
    document.head.appendChild(csp);
  }
  function stopClarity() {
    // Clarity stopt bij consentv2 'denied' (en wist _clck en _clsk), maar plant zelf 250 ms later een herstart zonder cookies, met een nieuw
    // bezoekers-ID (clarity-js, data/metadata.ts: consentv2), en stuurt bij het stoppen nog een laatste pakket. Daarom eerst het verkeer van
    // deze pagina dicht (sluitVerkeer), dan consentv2 'denied' en de geplande herstart annuleren.
    var plan = window.setTimeout, gepland = [];
    window.setTimeout = function () { var t = plan.apply(window, arguments); gepland.push(t); return t; };
    try { window.clarity("consentv2", { ad_Storage: "denied", analytics_Storage: "denied" }); }
    finally { window.setTimeout = plan; gepland.forEach(function (t) { window.clearTimeout(t); }); }
  }
  function stopGtm() {
    // Consent update 'denied' (Google stopt dan met opslaan en meten); het verkeer is al dicht (sluitVerkeer) en de pagina laadt direct opnieuw.
    var dl = window.dataLayer = window.dataLayer || [];
    (function () { dl.push(arguments); })("consent", "update", { analytics_storage: "denied", ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied" });
  }
  function laadClarity() {
    if (!id || !hier || window.__vaylideClarity) return;      // maximaal één keer per pagina
    window.__vaylideClarity = true;
    maskeer();
    window.clarity = window.clarity || function () { (window.clarity.q = window.clarity.q || []).push(arguments); };
    // De toestemming gaat vóór het eerste gegeven mee: Clarity verwerkt de wachtrij op volgorde.
    window.clarity("consentv2", { ad_Storage: "denied", analytics_Storage: "granted" });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.clarity.ms/tag/" + encodeURIComponent(id);
    document.head.appendChild(s);
  }
  function schoneVerwijzer() {
    // De pagina waar de bezoeker vandaan komt: zonder query, en binnen deze site zonder id's (die staan in de paden van de Studio en bestellingen).
    var r = document.referrer || "";
    if (!r) return "";
    try { var u = new URL(r); return u.origin + u.pathname.replace(UUID, ":id"); } catch (e) { return ""; }
  }
  function laadGtm() {
    if (!gtmId || !gtmHier || window.__vaylideGtm) return;    // maximaal één keer per pagina
    window.__vaylideGtm = true;
    var dl = window.dataLayer = window.dataLayer || [];
    function gtag() { dl.push(arguments); }
    // Toestemming vóór alles: alleen meten, geen advertenties (Consent Mode v2). Google Tag Manager laadt pas na het klikken op Accepteren.
    gtag("consent", "default", { ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied", analytics_storage: "granted" });
    var gegevens = { pagina_url: banner.getAttribute("data-gtm-url") || "", pagina_ref: schoneVerwijzer(), omgeving: banner.getAttribute("data-gtm-omgeving") || "" };
    if (banner.hasAttribute("data-gtm-ref-leeg")) gegevens.pagina_ref = "";            // bestelbevestiging: geen verwijzer (kan een betaalreferentie bevatten)
    if (banner.getAttribute("data-gtm-titel")) gegevens.pagina_titel = banner.getAttribute("data-gtm-titel");   // vaste titel waar de zichtbare titel een bestelnummer bevat
    if (banner.hasAttribute("data-gtm-debug")) gegevens.debug = true;   // testomgevingen meten als testverkeer (GA4 debug_mode), niet in de echte rapporten
    dl.push(gegevens);
    dl.push({ "gtm.start": new Date().getTime(), event: "gtm.js" });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtm.js?id=" + encodeURIComponent(gtmId);
    document.head.appendChild(s);
    // De vaste gebeurtenissen van deze pagina (door de server bepaald, alleen openbare waarden: ontwerp, gelegenheid, pakket, bedrag).
    var ruw = banner.getAttribute("data-gtm-events");
    if (ruw) {
      try { JSON.parse(ruw).forEach(function (gebeurtenis) { if (gebeurtenis && typeof gebeurtenis.event === "string") dl.push(gebeurtenis); }); } catch (e) { /* geen gebeurtenissen */ }
    }
  }
  function toon(open) {
    banner.hidden = !open;
    var huidige = keuze();
    banner.querySelectorAll("[data-toestemming-keuze]").forEach(function (knop) {
      knop.setAttribute("aria-pressed", knop.getAttribute("data-toestemming-keuze") === huidige ? "true" : "false");
    });
    var status = banner.querySelector("[data-toestemming-status]");
    if (status) status.textContent = huidige === "ja" ? "Je gaf toestemming." : huidige === "nee" ? "Je weigerde de meting." : "";
    if (open) { var eerste = banner.querySelector("[data-toestemming-keuze]"); if (eerste && huidige) eerste.focus({ preventScroll: true }); }
  }

  banner.querySelectorAll("[data-toestemming-keuze]").forEach(function (knop) {
    knop.addEventListener("click", function () {
      var nieuw = knop.getAttribute("data-toestemming-keuze");
      var was = keuze();
      bewaar(nieuw);
      toon(false);
      if (nieuw === "ja") { laadClarity(); laadGtm(); return; }
      // Weigeren of intrekken
      wisClarityCookies();
      wisGoogleCookies();
      var clarityAan = window.__vaylideClarity && typeof window.clarity === "function", googleAan = !!window.__vaylideGtm;
      if (clarityAan || googleAan) {
        sluitVerkeer();
        if (clarityAan) stopClarity();
        if (googleAan) stopGtm();
        wisClarityCookies();
        wisGoogleCookies();
        location.reload();                                    // pas na het stoppen: de pagina laadt opnieuw, zonder Clarity en zonder Google
      } else if (was === "ja") {
        wisClarityCookies();
        wisGoogleCookies();
      }
    });
  });
  document.querySelectorAll("[data-cookie-instellingen]").forEach(function (link) {
    link.hidden = false;
    link.addEventListener("click", function (e) { e.preventDefault(); toon(true); });
  });

  var nu = keuze();
  if (nu === "ja") { laadClarity(); laadGtm(); }
  else if (nu === "nee") { wisClarityCookies(); wisGoogleCookies(); }
  else if (vraagHier) toon(true);                           // alleen vragen waar er ook echt iets zou draaien
})();

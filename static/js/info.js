/* Info-knop (i): een korte uitleg in een popover bij een keuze. Markup: templates/partials/info.html, opmaak: vierlief.css (.info).
   De browser doet het openen en sluiten (klik buiten het paneel, Escape, ×) en houdt er maar één tegelijk open (popover "auto").
   Dit script zet het paneel bij de knop (op een smal scherm zet de CSS het onderaan als sheet), houdt aria-expanded bij, zet de
   focus op het paneel en na het sluiten terug op de knop. Zonder Popover-API: hetzelfde gedrag met hidden.
   Het script leest en wijzigt geen formuliervelden en verstuurt niets. */
(function () {
  "use strict";
  var knoppen = [].slice.call(document.querySelectorAll("[data-info-knop]"));
  if (!knoppen.length) return;
  var popoverApi = typeof HTMLElement !== "undefined" && Object.prototype.hasOwnProperty.call(HTMLElement.prototype, "popover");
  var smal = window.matchMedia("(max-width: 640px)");
  var MARGE = 12;
  // Wat iemand zelf aanklikt of aantikt (een veld, een andere knop) houdt de focus; anders gaat die na het sluiten terug naar de knop.
  var INTERACTIEF = "a[href], button, input, select, textarea, summary, [contenteditable='true'], [tabindex]:not([tabindex='-1'])";
  var open = null;                                            // { knop, paneel } van het paneel dat nu open is

  function plaats(knop, paneel) {
    paneel.style.left = "";
    paneel.style.top = "";
    if (smal.matches || !popoverApi) return;                  // telefoon: onderaan (CSS); zonder Popover-API: onder de knop (CSS)
    var r = knop.getBoundingClientRect();
    var breed = paneel.offsetWidth || Math.min(320, window.innerWidth - 2 * MARGE);
    var hoog = paneel.offsetHeight;
    var links = Math.min(Math.max(MARGE, r.left - 12), window.innerWidth - breed - MARGE);
    var boven = r.bottom + 8;
    if (hoog && boven + hoog > window.innerHeight - MARGE && r.top - 8 - hoog >= MARGE) boven = r.top - 8 - hoog;
    paneel.style.left = Math.round(links) + "px";
    paneel.style.top = Math.round(boven) + "px";
  }
  function herplaats() { if (open) plaats(open.knop, open.paneel); }

  function geopend(knop, paneel) {
    open = { knop: knop, paneel: paneel };
    knop.setAttribute("aria-expanded", "true");
    plaats(knop, paneel);
    window.addEventListener("resize", herplaats);
    window.addEventListener("scroll", herplaats, true);
    paneel.focus({ preventScroll: true });
  }
  function focusIn(paneel) {
    var actief = document.activeElement;
    return !actief || actief === document.body || paneel.contains(actief);
  }
  function gesloten(knop, paneel, focusWasBinnen) {
    knop.setAttribute("aria-expanded", "false");
    if (open && open.paneel === paneel) {
      open = null;
      window.removeEventListener("resize", herplaats);
      window.removeEventListener("scroll", herplaats, true);
    }
    // Safari zet de focus bij Escape eerst op de hoofdinhoud; die telt niet als bewuste keuze.
    var actief = document.activeElement;
    var gekozen = actief && actief !== document.body && !paneel.contains(actief) && actief.matches(INTERACTIEF);
    if ((focusWasBinnen || focusIn(paneel)) && !gekozen) knop.focus({ preventScroll: true });
  }
  function sluitZonderApi() {
    if (!open) return;
    var o = open;
    var binnen = focusIn(o.paneel);
    o.paneel.hidden = true;
    gesloten(o.knop, o.paneel, binnen);
  }

  if (!popoverApi) document.documentElement.classList.add("info-zonder-popover");
  knoppen.forEach(function (knop) {
    var paneel = document.getElementById(knop.getAttribute("aria-controls"));
    if (!paneel) return;
    // Een klik op de tekst in het paneel mag nooit een omliggend label of summary bedienen.
    paneel.addEventListener("click", function (event) {
      if (!event.target.closest("a, button")) event.preventDefault();
    });
    if (popoverApi) {
      var focusWasBinnen = false;
      paneel.addEventListener("beforetoggle", function (event) {
        if (event.newState === "open") plaats(knop, paneel);
        else focusWasBinnen = focusIn(paneel);
      });
      paneel.addEventListener("toggle", function (event) {
        if (event.newState === "open") geopend(knop, paneel);
        else gesloten(knop, paneel, focusWasBinnen);
      });
      return;
    }
    paneel.hidden = true;
    knop.addEventListener("click", function (event) {
      event.preventDefault();
      var wasOpen = open && open.paneel === paneel;
      sluitZonderApi();
      if (wasOpen) return;
      paneel.hidden = false;
      geopend(knop, paneel);
    });
    var sluit = paneel.querySelector("[data-info-sluit]");
    if (sluit) sluit.addEventListener("click", function (event) { event.preventDefault(); sluitZonderApi(); });
  });
  if (!popoverApi) {
    document.addEventListener("click", function (event) {
      if (open && !open.paneel.contains(event.target) && !open.knop.contains(event.target)) sluitZonderApi();
    });
    document.addEventListener("keydown", function (event) { if (event.key === "Escape" && open) sluitZonderApi(); });
  }
})();

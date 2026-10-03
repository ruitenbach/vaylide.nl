/* VAYLIDE Envelope Collection: openen in rustige stappen. Tik of klik op het zegel (of Enter/Spatie op de knop):
   het zegel geeft mee en vangt het licht, breekt langs de rand van de flap, de flap gaat open, de kaart komt eerst een
   stukje en dan helemaal uit de envelop en schuift naar voren. Daarna 'vx:opened' (bubbelt): pas dan mag de uitnodiging
   haar eigen animatie starten. Bij 'minder beweging': kort vervagen en meteen de eindstand (zelfde eindstand). */
(function () {
  "use strict";
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)");
  // Tijden in ms. Zegel ~0,75 s, flap 1,2 s, kaart ~1,6 s (in drie delen); samen ongeveer 3,8 s, zonder haast of stuiter.
  // Het zegel is even zichtbaar 'los' (tussen breken en flap) voordat de flap opengaat.
  var STEPS = [["is-pressed", 0], ["is-glint", 140], ["is-cracked", 430], ["is-opening", 760], ["is-flap-back", 1360],
               ["is-card-peek", 2020], ["is-card-out", 2480], ["is-card-front", 3220]];
  var DONE_AT = 3800;

  function finish(env) {
    env.classList.add("is-open");
    env.dispatchEvent(new CustomEvent("vx:opened", { bubbles: true }));
  }

  function open(env) {
    if (env.hasAttribute("data-vx-gsap")) { if (env.vxOpen) env.vxOpen(); return; }   // Signature Ivory met GSAP (envelop-signature.js) opent zichzelf
    if (env.classList.contains("is-pressed")) return;
    var timers = [];
    env._vxTimers = timers;
    // Ook rustig als de gast op een uitnodiging de beweging heeft stilgezet (knop Beweging, effects.js: html.fx-paused).
    if ((reduce && reduce.matches) || document.documentElement.classList.contains("fx-paused")) {
      // Rustig vervagen naar de eindstand: geen draaiende flap, geen schuivende kaart.
      env.classList.add("is-rm", "is-rm-hide");
      timers.push(setTimeout(function () {
        STEPS.forEach(function (s) { env.classList.add(s[0]); });
        env.classList.remove("is-rm-hide");
        finish(env);
      }, 360));
      return;
    }
    STEPS.forEach(function (s) {
      timers.push(setTimeout(function () { env.classList.add(s[0]); }, s[1]));
    });
    timers.push(setTimeout(function () { finish(env); }, DONE_AT));
  }

  function reset(env) {
    (env._vxTimers || []).forEach(clearTimeout);
    env.classList.add("is-rm");  // terug zonder animatie
    STEPS.forEach(function (s) { env.classList.remove(s[0]); });
    env.classList.remove("is-open", "is-rm-hide");
    void env.offsetWidth;
    env.classList.remove("is-rm");
    var hit = env.querySelector(".vx-seal-hit");
    if (hit) hit.focus({ preventScroll: true });
  }

  document.querySelectorAll("[data-vx]").forEach(function (env) {
    if (env.hasAttribute("data-vx-gsap")) return;   // zie envelop-signature.js: die bedient deze envelop en zet vxReset zelf
    env.querySelectorAll("[data-vx-open]").forEach(function (btn) {
      btn.addEventListener("click", function () { open(env); });
    });
    env.vxReset = function () { reset(env); };
  });

  // Knoppen buiten de envelop die hem ook openen (bijv. 'Openen met muziek' op een openingsscherm).
  document.querySelectorAll("[data-vx-open-for]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.getAttribute("data-vx-open-for"));
      if (target) open(target);
    });
  });

  // Testpagina: knoppen om opnieuw te openen.
  document.querySelectorAll("[data-vx-reset]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var target = document.getElementById(btn.getAttribute("data-vx-reset"));
      if (target && target.vxReset) target.vxReset();
    });
  });
})();

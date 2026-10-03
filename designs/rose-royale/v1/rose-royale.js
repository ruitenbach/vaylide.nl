/* Rosé Royale v1 — diepte in de kop: elke laag van de scène beweegt met een eigen snelheid bij het scrollen
   (CSS-variabele --rr-scroll) en op een computer heel licht met de muis (--rr-mx, --rr-my, van -1 tot 1). Alleen als beweging aan staat (html.fx-motion, niet fx-paused).
   Zonder dit script staat de scène gewoon stil en is alles leesbaar. */
(function () {
  "use strict";
  var root = document.documentElement;
  var hero = document.querySelector(".rr-hero");
  if (!hero) return;
  var ticking = false;
  var mx = 0, my = 0;

  function moving() {
    return root.classList.contains("fx-motion") && !root.classList.contains("fx-paused");
  }

  function update() {
    ticking = false;
    if (!moving()) {
      root.style.removeProperty("--rr-scroll");
      root.style.removeProperty("--rr-mx");
      root.style.removeProperty("--rr-my");
      return;
    }
    var y = Math.min(window.scrollY, window.innerHeight * 1.2);
    root.style.setProperty("--rr-scroll", Math.round(y) + "px");
    root.style.setProperty("--rr-mx", mx.toFixed(3));
    root.style.setProperty("--rr-my", my.toFixed(3));
  }

  function request() {
    if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
  }

  window.addEventListener("scroll", request, { passive: true });
  if (window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
    hero.addEventListener("pointermove", function (event) {
      var r = hero.getBoundingClientRect();
      mx = ((event.clientX - r.left) / r.width) * 2 - 1;
      my = ((event.clientY - r.top) / r.height) * 2 - 1;
      request();
    });
    hero.addEventListener("pointerleave", function () { mx = 0; my = 0; request(); });
  }
  // De film (de camera rijdt de tuin in, het licht gaat aan) start op het moment dat het zegel wordt aangetikt. Wie de
  // envelop al eerder opende, ziet meteen de eindstand. Bij 'minder beweging' of stilgezette beweging: geen film.
  document.addEventListener("invite:opening", function (event) {
    if (event.detail && event.detail.reduceMotion) return;
    root.classList.add("rr-film");
  });
  document.addEventListener("invite:opened", request);
  request();
})();

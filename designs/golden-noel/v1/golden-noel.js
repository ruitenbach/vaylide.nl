/* Golden Noël v1 — rustige diepte bij het scrollen: de lichtvlekken (bokeh) en de boog bewegen iets langzamer mee dan
   de pagina (CSS-variabele --gn-scroll). Alleen als beweging aan staat (effects.js zet dan html.fx-motion en zet
   --fx-play op paused als de gast op Beweging tikt). Zonder dit script staat alles gewoon stil. */
(function () {
  "use strict";
  var root = document.documentElement;
  var ticking = false;

  function update() {
    ticking = false;
    var moving = root.classList.contains("fx-motion") && !root.classList.contains("fx-paused");
    if (moving) root.style.setProperty("--gn-scroll", Math.round(window.scrollY) + "px");
    else root.style.removeProperty("--gn-scroll");
  }

  window.addEventListener("scroll", function () {
    if (!ticking) { ticking = true; window.requestAnimationFrame(update); }
  }, { passive: true });
  document.addEventListener("invite:opened", update);
  update();
})();

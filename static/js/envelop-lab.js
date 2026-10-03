/* Alleen de envelopstudio (lokaal): toont na het openen waar de uitnodiging zou beginnen. */
(function () {
  "use strict";
  var done = document.querySelector("[data-lab-done]");
  document.addEventListener("vx:opened", function () { if (done) done.classList.add("is-visible"); });
  document.querySelectorAll("[data-vx-reset]").forEach(function (btn) {
    btn.addEventListener("click", function () { if (done) done.classList.remove("is-visible"); });
  });
})();

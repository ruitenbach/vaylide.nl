/* Onze eigen gezichten: ververst de pagina zodra het voorbeeld klaar is (zonder JavaScript: vernieuw zelf). */
(function () {
  "use strict";
  var box = document.querySelector("[data-gezichten-status]");
  if (!box || box.getAttribute("data-status") !== "bezig") return;
  var url = box.getAttribute("data-gezichten-status");
  var tries = 0;
  function check() {
    tries += 1;
    fetch(url, { credentials: "same-origin", headers: { Accept: "application/json" } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (data && data.status !== "bezig") { window.location.reload(); return; }
        if (tries < 90) window.setTimeout(check, 3000);
      })
      .catch(function () { if (tries < 90) window.setTimeout(check, 5000); });
  }
  window.setTimeout(check, 3000);
})();

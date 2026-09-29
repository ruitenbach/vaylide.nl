/* Vaylide: werkt de bestelstatus bij tot de uitnodiging online staat (max. 2 minuten). */
(function () {
  "use strict";
  var box = document.querySelector("[data-order-status]");
  if (!box) return;
  var phase = box.getAttribute("data-phase");
  if (phase !== "waiting" && phase !== "processing") return;
  var url = box.getAttribute("data-order-status");
  var note = box.querySelector("[data-status-note]");
  var tries = 0;
  function check() {
    tries++;
    fetch(url, { headers: { "Accept": "application/json" }, credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.phase !== phase) { window.location.reload(); return; }
        if (tries < 60) window.setTimeout(check, 2000);
        else if (note) note.textContent = "Het duurt langer dan normaal. Vernieuw de pagina later of kijk in Mijn VAYLIDE.";
      })
      .catch(function () { if (tries < 60) window.setTimeout(check, 4000); });
  }
  window.setTimeout(check, 1500);
})();

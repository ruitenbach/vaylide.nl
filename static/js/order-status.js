/* Vaylide: werkt de bestelstatus bij, met afnemende frequentie en een einde (geen eindeloze polling). Bij een betaling
   die nog open staat verschijnt na een minuut de knop 'Betaling hervatten' (de server rekent dat ook zelf uit, dus het
   werkt ook zonder JavaScript na vernieuwen). De server vraagt de provider hoogstens eens per 10 seconden. */
(function () {
  "use strict";
  var box = document.querySelector("[data-order-status]");
  if (!box) return;
  var phase = box.getAttribute("data-phase");
  if (phase !== "waiting" && phase !== "processing") return;
  var url = box.getAttribute("data-order-status");
  var note = box.querySelector("[data-status-note]");
  var resume = box.querySelector("[data-resume]");
  var resumeAfter = parseInt(box.getAttribute("data-resume-after") || "-1", 10);
  // Samen ongeveer tien minuten: eerst vlot (de webhook komt meestal binnen seconden), daarna steeds rustiger.
  var delays = [2, 3, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 30, 45, 60, 60, 60, 60, 60, 60, 60];
  var step = 0;

  function showResume() { if (resume) resume.hidden = false; }
  if (resume && resumeAfter >= 0) window.setTimeout(showResume, resumeAfter * 1000);

  function stop() {
    if (note) note.textContent = "We controleren niet meer automatisch. Vernieuw de pagina om de actuele status te zien, of kijk later in Mijn VAYLIDE.";
    if (phase === "waiting") showResume();
  }

  function next() {
    if (step >= delays.length) { stop(); return; }
    window.setTimeout(check, delays[step++] * 1000);
  }

  function check() {
    fetch(url, { headers: { "Accept": "application/json" }, credentials: "same-origin" })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (data.phase !== phase || (data.bank_pending ? "1" : "0") !== box.getAttribute("data-bank-pending")) {
          window.location.reload();
          return;
        }
        if (data.can_resume) showResume();
        next();
      })
      .catch(next);
  }
  next();
})();

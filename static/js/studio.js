/* Vaylide samenstellen: verbeteringen bovenop werkende formulieren.
   Zonder JavaScript werkt alles ook (gewone formulieren, schuifjes en knoppen). */
(function () {
  "use strict";
  var html = document.documentElement;
  html.classList.add("js-enabled");

  // Uitnodiging of wenskaart: bij een wenskaart verdwijnen 'Wanneer' en 'Waar' (de ingevulde waarden blijven bewaard).
  document.querySelectorAll("[data-soort-keuze]").forEach(function (group) {
    var form = group.closest("form");
    function update() {
      var checked = group.querySelector("input[name=soort]:checked");
      var wens = checked && checked.value === "wenskaart";
      form.querySelectorAll("[data-alleen-uitnodiging]").forEach(function (el) { el.hidden = wens; });
    }
    group.addEventListener("change", update);
    update();
  });

  function csrfToken() {
    var input = document.querySelector("input[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  /* ---------- Herhaalbare rijen (programma, praktische info, vragen) ---------- */
  document.querySelectorAll("[data-repeat]").forEach(function (list) {
    var add = list.querySelector("[data-repeat-add]");
    if (!add) return;
    function hiddenRows() { return list.querySelectorAll("[data-repeat-row].is-empty"); }
    function sync() { add.hidden = hiddenRows().length === 0; }
    add.addEventListener("click", function () {
      var next = hiddenRows()[0];
      if (!next) return;
      next.classList.remove("is-empty");
      var input = next.querySelector("input:not([type=hidden]), textarea, select");
      if (input) input.focus();
      sync();
    });
    sync();
  });

  /* ---------- Enter in een tekstveld = 'Volgende' ---------- */
  document.querySelectorAll("form").forEach(function (form) {
    var next = form.querySelector("[data-default-action]");
    if (!next) return;
    form.addEventListener("keydown", function (event) {
      var target = event.target;
      if (event.key !== "Enter" || !target || target.tagName !== "INPUT") return;
      if (["text", "email", "tel", "url", "number", "date", "time"].indexOf(target.type) === -1) return;
      event.preventDefault();
      next.click();
    });
  });

  /* ---------- Waarschuwing bij niet-opgeslagen wijzigingen ---------- */
  document.querySelectorAll("form[data-dirty-check]").forEach(function (form) {
    var dirty = false;
    form.addEventListener("input", function () { dirty = true; });
    form.addEventListener("change", function () { dirty = true; });
    form.addEventListener("submit", function () { dirty = false; });
    window.addEventListener("beforeunload", function (event) {
      if (!dirty) return;
      event.preventDefault();
      event.returnValue = "";
    });
    form.markDirty = function () { dirty = true; };
    // Wisselen van onderdeel (balk, voortgang, Wijzigen): eerst bewaren wat er staat, daarna pas verder. Zonder wijzigingen is het een gewone link.
    document.querySelectorAll("a[data-ga]").forEach(function (link) {
      link.addEventListener("click", function (event) {
        if (!dirty || event.defaultPrevented || event.button > 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        var naar = form.querySelector("[data-ga-naar]");
        if (!naar || !form.requestSubmit) return;
        event.preventDefault();
        naar.value = link.getAttribute("data-ga");
        var actie = document.createElement("input");
        actie.type = "hidden"; actie.name = "actie"; actie.value = "ga";
        form.appendChild(actie);
        form.requestSubmit();
      });
    });
  });

  /* ---------- Kies kaart: vanaf een ontwerppagina start de gekozen kaart direct (één keer per tabblad, zodat 'terug' geen lus wordt) ---------- */
  document.querySelectorAll("form[data-auto-start]").forEach(function (form) {
    var knop = form.querySelector(".kaart-gekozen__cta");
    if (!knop) return;
    var sleutel = "vaylide-auto-start:" + window.location.search;
    try { if (window.sessionStorage.getItem(sleutel)) return; window.sessionStorage.setItem(sleutel, "1"); } catch (e) { return; }
    var wacht = form.querySelector("[data-auto-wacht]");
    if (wacht) wacht.hidden = false;
    if (form.requestSubmit) form.requestSubmit(knop); else knop.click();
  });

  /* ---------- Rijen met keuzes (gelegenheid, onderdelen): de gekozen staat in beeld ---------- */
  document.querySelectorAll(".chip-rij, .deelnav__balk ul").forEach(function (rij) {
    var nu = rij.querySelector(".is-current");
    if (nu && rij.scrollWidth > rij.clientWidth) rij.scrollLeft = Math.max(0, nu.offsetLeft - (rij.clientWidth - nu.offsetWidth) / 2);
  });

  /* ---------- Start: ontwerpen filteren op gelegenheid ---------- */
  var occasionRadios = document.querySelectorAll("[data-occasion-radio]");
  if (occasionRadios.length) {
    var filter = function () {
      var checked = document.querySelector("[data-occasion-radio]:checked");
      var occasion = checked ? checked.value : "";
      document.querySelectorAll(".design-pick[data-occasions]").forEach(function (card) {
        var fits = !occasion || card.getAttribute("data-occasions").split(" ").indexOf(occasion) !== -1;
        card.classList.toggle("is-hidden", !fits);
        var radio = card.querySelector("input[type=radio]");
        if (!fits && radio && radio.checked) radio.checked = false;
      });
    };
    occasionRadios.forEach(function (radio) { radio.addEventListener("change", filter); });
    filter();
  }

  /* ---------- Foto's uploaden met controle vooraf en voortgang ---------- */
  document.querySelectorAll("form[data-upload]").forEach(function (form) {
    var input = form.querySelector("input[type=file]");
    var status = form.querySelector("[data-upload-status]");
    var button = form.querySelector("[data-upload-submit]");
    var maxBytes = parseInt(form.getAttribute("data-max-bytes"), 10) || 12 * 1024 * 1024;
    var allowed = ["image/jpeg", "image/png", "image/webp"];
    var drop = form.querySelector(".upload-drop");
    function say(text, kind) {
      status.textContent = text;
      status.classList.toggle("is-error", kind === "error");
      status.classList.toggle("is-ok", kind === "ok");
    }
    function check() {
      var problems = [];
      Array.prototype.forEach.call(input.files || [], function (file) {
        if (allowed.indexOf(file.type) === -1 && !/\.(jpe?g|png|webp)$/i.test(file.name)) {
          problems.push(file.name + ": dit bestandstype wordt niet ondersteund (gebruik JPG, PNG of WebP).");
        } else if (file.size > maxBytes) {
          problems.push(file.name + ": te groot (" + Math.round(file.size / 1048576) + " MB, maximaal " + Math.round(maxBytes / 1048576) + " MB).");
        }
      });
      return problems;
    }
    if (drop) {
      ["dragenter", "dragover"].forEach(function (name) { drop.addEventListener(name, function (e) { e.preventDefault(); drop.classList.add("is-dragover"); }); });
      ["dragleave", "drop"].forEach(function (name) { drop.addEventListener(name, function () { drop.classList.remove("is-dragover"); }); });
      drop.addEventListener("drop", function (e) {
        e.preventDefault();
        if (e.dataTransfer && e.dataTransfer.files.length) { input.files = e.dataTransfer.files; input.dispatchEvent(new Event("change")); }
      });
    }
    input.addEventListener("change", function () {
      var problems = check();
      if (problems.length) { say(problems.join(" "), "error"); return; }
      if (input.files.length) { say(input.files.length + " bestand(en) gekozen. Bezig met uploaden…"); upload(); }
    });
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var problems = check();
      if (problems.length) { say(problems.join(" "), "error"); return; }
      if (!input.files || !input.files.length) { say("Kies eerst een of meer foto's.", "error"); return; }
      upload();
    });
    function upload() {
      var xhr = new XMLHttpRequest();
      xhr.open("POST", form.action);
      xhr.setRequestHeader("Accept", "application/json");
      xhr.setRequestHeader("X-Requested-With", "fetch");
      xhr.upload.addEventListener("progress", function (e) {
        if (e.lengthComputable) say("Uploaden… " + Math.round((e.loaded / e.total) * 100) + "%");
      });
      xhr.addEventListener("load", function () {
        var data = {};
        try { data = JSON.parse(xhr.responseText); } catch (e) { data = { errors: ["Uploaden is niet gelukt. Probeer het opnieuw."] }; }
        if (xhr.status === 413) data.errors = ["Deze bestanden zijn samen te groot. Upload er minder tegelijk."];
        if (data.errors && data.errors.length) {
          say(data.errors.join(" "), "error");
          if (data.created && data.created.length) window.setTimeout(function () { window.location.reload(); }, 2500);
          return;
        }
        say("Geüpload. De pagina wordt bijgewerkt…", "ok");
        window.location.hash = "uploads";
        window.location.reload();
      });
      xhr.addEventListener("error", function () { say("Geen verbinding. Je foto's zijn nog niet geüpload.", "error"); });
      if (button) button.disabled = true;
      xhr.send(new FormData(form));
    }
  });

  /* ---------- Uitsnede: de foto verslepen met muis of vinger (inzoomen met de schuifbalk) ----------
     De foto staat al automatisch uitgelijnd (gezichten). Slepen verschuift de foto binnen het kader, zoals op een
     telefoon. Zonder JavaScript blijven de schuifbalken Horizontaal en Verticaal gewoon werken. */
  document.querySelectorAll("[data-photo]").forEach(function (card) {
    var uid = card.getAttribute("data-uid");
    var frame = card.querySelector("[data-focus-frame]");
    var img = card.querySelector("[data-focus-img]");
    var x = card.querySelector("input[name='x_" + uid + "']");
    var y = card.querySelector("input[name='y_" + uid + "']");
    var z = card.querySelector("input[name='z_" + uid + "']");
    var auto = card.querySelector("[data-focus-auto]");
    var xy = card.querySelector("[data-focus-xy]");
    if (!frame || !x || !y) return;
    card.classList.add("is-draggable");
    if (xy) xy.hidden = true;
    frame.tabIndex = 0;
    var autoX = parseFloat(card.getAttribute("data-auto-x") || "50");
    var autoY = parseFloat(card.getAttribute("data-auto-y") || "50");

    function zoom() { return (parseFloat((z && z.value) || 100)) / 100; }
    function render() {
      var px = parseFloat(x.value || 50), py = parseFloat(y.value || 50), zm = zoom();
      img.style.objectPosition = px + "% " + py + "%";
      img.style.transformOrigin = px + "% " + py + "%";
      img.style.transform = zm > 1.001 ? "scale(" + zm + ")" : "";
      if (auto) auto.hidden = Math.round(px) === Math.round(autoX) && Math.round(py) === Math.round(autoY) && zm <= 1.001;
    }
    function changed() {
      var form = x.form;
      if (form && form.markDirty) form.markDirty();
      x.dispatchEvent(new Event("change", { bubbles: true }));  // de live kaart werkt zich bij
    }
    function set(px, py) {
      x.value = Math.round(Math.max(0, Math.min(100, px)));
      y.value = Math.round(Math.max(0, Math.min(100, py)));
      render();
    }
    // Hoeveel een procent verschuiven op het scherm is: het deel van de foto dat buiten het kader valt (met zoom).
    function overflow(rect) {
      var iw = img.naturalWidth || img.width, ih = img.naturalHeight || img.height;
      var cover = Math.max(rect.width / iw, rect.height / ih) * zoom();
      return { w: iw * cover - rect.width, h: ih * cover - rect.height };
    }

    var start = null;
    frame.addEventListener("pointerdown", function (e) {
      if (e.button !== undefined && e.button !== 0) return;
      start = { cx: e.clientX, cy: e.clientY, px: parseFloat(x.value || 50), py: parseFloat(y.value || 50), room: overflow(frame.getBoundingClientRect()) };
      frame.setPointerCapture(e.pointerId);
      frame.classList.add("is-dragging");
      e.preventDefault();
    });
    frame.addEventListener("pointermove", function (e) {
      if (!start) return;
      var dx = e.clientX - start.cx, dy = e.clientY - start.cy;
      // Naar rechts slepen = de foto schuift naar rechts = je ziet meer van de linkerkant.
      set(start.room.w > 1 ? start.px - (dx / start.room.w) * 100 : start.px,
          start.room.h > 1 ? start.py - (dy / start.room.h) * 100 : start.py);
    });
    function stop() {
      if (!start) return;
      start = null;
      frame.classList.remove("is-dragging");
      changed();
    }
    frame.addEventListener("pointerup", stop);
    frame.addEventListener("pointercancel", stop);
    frame.addEventListener("keydown", function (e) {
      var step = e.shiftKey ? 10 : 2;
      var moves = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
      if (!moves[e.key]) return;
      e.preventDefault();
      set(parseFloat(x.value || 50) + moves[e.key][0], parseFloat(y.value || 50) + moves[e.key][1]);
      changed();
    });
    if (auto) auto.addEventListener("click", function () {
      if (z) z.value = 100;
      set(autoX, autoY);
      changed();
    });
    [x, y, z].forEach(function (input) { if (input) input.addEventListener("input", render); });
    if (img.complete) render(); else img.addEventListener("load", render);
    render();
  });

  /* ---------- Tekstvoorstel (AI of testmodus) ---------- */
  document.querySelectorAll("[data-ai]").forEach(function (box) {
    box.hidden = false;
    var url = box.getAttribute("data-ai-url");
    var field = box.getAttribute("data-ai-field");
    var target = document.querySelector("[data-ai-field='" + field + "']:not([data-ai])");
    var go = box.querySelector("[data-ai-go]");
    var out = box.querySelector("[data-ai-result]");
    go.addEventListener("click", function () {
      var body = new FormData();
      body.append("field", field);
      body.append("tone", box.querySelector("[data-ai-tone]").value);
      body.append("notes", box.querySelector("[data-ai-notes]").value);
      body.append("current", target ? target.value : "");
      go.disabled = true;
      out.textContent = "Bezig met een voorstel…";
      fetch(url, { method: "POST", body: body, headers: { "X-CSRFToken": csrfToken(), "Accept": "application/json" }, credentials: "same-origin" })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          go.disabled = false;
          out.textContent = "";
          if (!data.ok) { out.textContent = data.message || "Er kon geen voorstel worden gemaakt."; return; }
          var note = document.createElement("p");
          note.className = "small muted";
          note.textContent = data.notice;
          var text = document.createElement("p");
          text.className = "ai-help__suggestion";
          text.textContent = data.suggestion;
          var use = document.createElement("button");
          use.type = "button";
          use.className = "btn btn--primary btn--sm";
          use.textContent = "Gebruik dit voorstel";
          use.addEventListener("click", function () {
            if (target) {
              target.value = data.suggestion;
              target.dispatchEvent(new Event("input", { bubbles: true }));
              target.focus();
            }
            out.textContent = "Voorstel overgenomen. Pas het gerust aan en vergeet niet op te slaan.";
          });
          out.appendChild(note);
          out.appendChild(text);
          out.appendChild(use);
        })
        .catch(function () { go.disabled = false; out.textContent = "Geen verbinding. Probeer het opnieuw."; });
    });
  });

  /* ---------- Voorbeeld: telefoon of computer ---------- */
  document.querySelectorAll("[data-preview]").forEach(function (stage) {
    var frame = stage.querySelector("[data-preview-frame]");
    stage.querySelectorAll("[data-device]").forEach(function (button) {
      button.addEventListener("click", function () {
        stage.querySelectorAll("[data-device]").forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
        button.setAttribute("aria-pressed", "true");
        frame.className = "preview-frame preview-frame--" + button.getAttribute("data-device");
      });
    });
  });

  /* ---------- Envelop & zegel: na een andere envelop alleen de zegels die erbij passen ---------- */
  document.querySelectorAll("[data-envelop-kiezer]").forEach(function (form) {
    var blok = form.querySelector("[data-zegel-blok]");
    var kaarten = form.querySelectorAll("[data-envelopen]");
    function update() {
      var gekozen = form.querySelector("input[name=envelop]:checked");
      var passend = gekozen && gekozen.getAttribute("data-zegels") ? gekozen.getAttribute("data-zegels").split(" ") : [];
      if (blok) blok.hidden = passend.length === 0;
      kaarten.forEach(function (kaart) { kaart.hidden = passend.indexOf(kaart.querySelector("input").value) < 0; });
      var nu = form.querySelector("input[name=zegel]:checked");
      if (passend.length && (!nu || passend.indexOf(nu.value) < 0)) {
        var standaard = form.querySelector("input[name=zegel][value='" + gekozen.getAttribute("data-standaard") + "']");
        if (standaard) standaard.checked = true;
      }
    }
    form.querySelectorAll("input[name=envelop]").forEach(function (radio) { radio.addEventListener("change", update); });
    update();
  });

  /* ---------- Je kaart, live naast de invulstappen: toont wat je invult, nog vóór het opslaan ---------- */
  document.querySelectorAll("[data-live]").forEach(function (box) {
    var frame = box.querySelector("[data-live-frame]");
    var card = box.querySelector("[data-live-card]");
    frame.addEventListener("load", function () { window.setTimeout(function () { card.classList.remove("is-updating"); }, 250); });
    var state = box.querySelector("[data-live-state]");
    var url = box.getAttribute("data-live-update");
    var form = document.querySelector("form.studio-form");
    var wide = window.matchMedia("(min-width: 1100px)");
    if (wide.matches) box.open = true;
    // Breed: altijd open naast de stappen. Smaller geworden: dicht, anders ligt hij over het hele scherm.
    if (wide.addEventListener) wide.addEventListener("change", function () { box.open = wide.matches; });
    // Smal scherm: de zwevende knop 'Bekijk je kaart' maakt plaats voor wat je nu gebruikt. Hij verdwijnt zolang je in een veld typt
    // (het toetsenbord) en zodra de knoppen onderaan de stap in beeld zijn, en komt daarna vanzelf terug. Open ('Sluiten') blijft hij staan.
    var weg = { veld: false, knoppen: false };
    function zetKnop() { if (box.toggleAttribute) box.toggleAttribute("data-knop-weg", weg.veld || weg.knoppen); }
    function isVeld(el) {
      return !!el && (el.tagName === "TEXTAREA" || el.tagName === "SELECT" ||
        (el.tagName === "INPUT" && ["text", "email", "tel", "url", "number", "date", "time", "search", "password"].indexOf(el.type) >= 0));
    }
    document.addEventListener("focusin", function (event) { weg.veld = isVeld(event.target); zetKnop(); });
    document.addEventListener("focusout", function () { window.setTimeout(function () { weg.veld = isVeld(document.activeElement); zetKnop(); }, 60); });
    // De knoppen onderaan: alleen weg als ze in de strook komen waar de knop zelf zit (onderste ~5 rem van het scherm), niet zodra ze in beeld zijn.
    var acties = document.querySelector(".step-actions");
    if (acties) {
      var wachtend = false;
      var controleer = function () {
        wachtend = false;
        if (window.getComputedStyle(acties).position === "sticky") { weg.knoppen = false; zetKnop(); return; }   // vaste knoppenbalk: de knop 'Bekijk je kaart' staat erboven
        var r = acties.getBoundingClientRect();
        var strook = Math.max(80, box.querySelector("summary").getBoundingClientRect().height + 28);
        weg.knoppen = r.top < window.innerHeight && r.bottom > window.innerHeight - strook;
        zetKnop();
      };
      var plan = function () { if (!wachtend) { wachtend = true; window.requestAnimationFrame(controleer); } };
      window.addEventListener("scroll", plan, { passive: true });
      window.addEventListener("resize", plan);
      controleer();
    }
    if (!form || !url || !window.fetch || !window.FormData) return;
    var timer = null, busy = false, again = false, pending = false, jump = false;
    function refresh() {
      if (!box.open) { pending = true; return; }
      if (busy) { again = true; return; }
      busy = true;
      pending = false;
      state.textContent = "· bijwerken…";
      fetch(url, { method: "POST", body: new FormData(form), credentials: "same-origin",
                   headers: { "Accept": "application/json", "X-Requested-With": "fetch" } })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          state.textContent = "";
          if (!data.ok || !data.url) return;
          // Een foto gekozen: naar de foto's springen. Anders blijft de kaart staan waar hij stond.
          var y = 0;
          try { y = Math.round(frame.contentWindow.scrollY || 0); } catch (e) { y = 0; }
          var keep = !jump && y > 0 ? "&y=" + y : "";
          jump = false;
          card.classList.add("is-updating");
          // replace(): geen extra stap in de terug-knop van de browser.
          frame.contentWindow.location.replace(data.url + keep);
        })
        .catch(function () { state.textContent = ""; })
        .then(function () { busy = false; if (again) { again = false; schedule(); } });
    }
    function schedule(event) {
      var name = event && event.target && event.target.name || "";
      if (name === "hero" || /^g_/.test(name)) jump = true;
      window.clearTimeout(timer);
      timer = window.setTimeout(refresh, 600);
    }
    form.addEventListener("input", schedule);
    form.addEventListener("change", schedule);
    box.addEventListener("toggle", function () { if (box.open && pending) refresh(); });
    // Na herladen of 'terug' zet de browser eerder ingevulde waarden terug: laat de kaart die ook tonen.
    var nav = window.performance && performance.getEntriesByType ? performance.getEntriesByType("navigation")[0] : null;
    if (nav && (nav.type === "reload" || nav.type === "back_forward")) schedule();
    window.addEventListener("pageshow", function (event) { if (event.persisted) schedule(); });
  });

  /* ---------- Muziek: de velden voor eigen muziek (bestand kiezen, uploaden, toestemming) alleen bij "Eigen muziek uploaden" ---------- */
  // Zonder JavaScript blijven ze zichtbaar. Het opslaan en de prijs veranderen hier niet: dat doet de server met de gekozen bron.
  document.querySelectorAll("[data-muziek-eigen]").forEach(function (blok) {
    var keuzes = document.querySelectorAll("input[name=music_source]");
    if (!keuzes.length) return;
    var opslagSleutel = "vierlief-studio-eigen-muziek";
    function toon() {
      var gekozen = document.querySelector("input[name=music_source]:checked");
      var eigen = !!gekozen && gekozen.value === "custom";
      blok.hidden = !eigen;
      var toelichting = document.querySelector("[data-muziek-design]");
      if (toelichting) toelichting.hidden = !gekozen || gekozen.value !== "design";
    }
    // Wie een bestand uploadt (de pagina laadt daarna opnieuw) blijft bij "Eigen muziek uploaden", ook als dat nog niet was opgeslagen.
    blok.querySelectorAll("button[form=upload-muziek-form]").forEach(function (knop) {
      knop.addEventListener("click", function () { try { window.sessionStorage.setItem(opslagSleutel, "1"); } catch (e) { /* privémodus */ } });
    });
    try {
      if (window.sessionStorage.getItem(opslagSleutel)) {
        window.sessionStorage.removeItem(opslagSleutel);
        var eigenKeuze = document.querySelector("input[name=music_source][value=custom]");
        if (eigenKeuze) eigenKeuze.checked = true;
      }
    } catch (e) { /* privémodus */ }
    keuzes.forEach(function (keuze) { keuze.addEventListener("change", toon); });
    window.addEventListener("pageshow", toon);   // na 'terug' of herladen zet de browser eerdere keuzes terug
    toon();
  });

  /* ---------- Bestellen: bedrag direct bijwerken bij een andere keuze ---------- */
  document.querySelectorAll("[data-recalc]").forEach(function (input) {
    input.addEventListener("change", function () {
      var form = input.form;
      var action = form.querySelector("[data-checkout-action]");
      if (action) action.value = "herberekenen";
      form.submit();
    });
  });
})();

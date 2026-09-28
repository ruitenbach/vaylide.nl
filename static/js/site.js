/* Vaylide website: kleine verbeteringen bovenop werkende HTML (alles werkt ook zonder JavaScript). */
(function () {
  "use strict";

  // Live voorbeeld op de homepage: wissel van ontwerp.
  document.querySelectorAll("[data-demo]").forEach(function (demo) {
    var frame = demo.querySelector("[data-demo-frame]");
    var full = demo.querySelector("[data-demo-full]");
    demo.querySelectorAll("[data-demo-src]").forEach(function (button) {
      button.addEventListener("click", function () {
        demo.querySelectorAll("[data-demo-src]").forEach(function (b) { b.setAttribute("aria-pressed", "false"); });
        button.setAttribute("aria-pressed", "true");
        var src = button.getAttribute("data-demo-src");
        if (frame) frame.src = src;
        if (full) full.href = src.replace(/[?&]embed=1/, "");
      });
    });
  });

  // Live voorbeeld pas laden als het bijna in beeld is; tot dan staat er een afbeelding.
  var lazyFrames = document.querySelectorAll("[data-lazy-frame]");
  function loadFrame(holder) {
    if (holder.querySelector("iframe")) return;
    var frame = document.createElement("iframe");
    frame.setAttribute("data-lazy", "");
    frame.title = holder.getAttribute("data-frame-title") || "";
    frame.addEventListener("load", function () { holder.classList.add("is-loaded"); });
    frame.src = holder.getAttribute("data-lazy-frame");
    holder.appendChild(frame);
  }
  if ("IntersectionObserver" in window) {
    var frameObserver = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) { loadFrame(entry.target); frameObserver.unobserve(entry.target); }
      });
    }, { rootMargin: "300px 0px" });
    lazyFrames.forEach(function (holder) { frameObserver.observe(holder); });
  } else {
    lazyFrames.forEach(loadFrame);
  }

  // Ontwerpkaarten: kantelen met de muis en één keer glanzen als ze in beeld komen (niet bij 'minder beweging').
  var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var cards = document.querySelectorAll(".design-card");
  if (!calm && cards.length) {
    if (window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches) {
      cards.forEach(function (card) {
        var link = card.querySelector(".design-card__link");
        var visual = card.querySelector(".design-card__visual");
        if (!link || !visual) return;
        link.addEventListener("pointermove", function (event) {
          var r = visual.getBoundingClientRect();
          var x = (event.clientX - r.left) / r.width - 0.5;
          var y = (event.clientY - r.top) / r.height - 0.5;
          visual.style.setProperty("--card-ry", (x * 10).toFixed(2) + "deg");
          visual.style.setProperty("--card-rx", (-y * 10).toFixed(2) + "deg");
        });
        link.addEventListener("pointerleave", function () {
          visual.style.removeProperty("--card-ry");
          visual.style.removeProperty("--card-rx");
        });
      });
    }
    if ("IntersectionObserver" in window) {
      var seen = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          var card = entry.target;
          seen.unobserve(card);
          card.classList.add("is-seen");
          window.setTimeout(function () { card.classList.remove("is-seen"); }, 2900); // lang genoeg voor de confetti
        });
      }, { threshold: 0.6 });
      cards.forEach(function (card) { seen.observe(card); });
    }
  }

  // Stapkaartjes schuiven een voor een in beeld. Zonder IntersectionObserver of bij 'minder beweging' staan ze er meteen.
  var reveal = document.querySelectorAll(".stapkaart");
  if (reveal.length) {
    if (!calm && "IntersectionObserver" in window) {
      var revealer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add("is-zichtbaar");
          revealer.unobserve(entry.target);
        });
      }, { threshold: 0.2 });
      reveal.forEach(function (el) { revealer.observe(el); });
    } else {
      reveal.forEach(function (el) { el.classList.add("is-zichtbaar"); });
    }
  }

  // Veelgestelde vragen: een link naar #vraag-3 opent die vraag.
  function openTarget() {
    var id = window.location.hash.slice(1);
    var target = id && document.getElementById(id);
    if (target && target.tagName === "DETAILS") target.open = true;
  }
  openTarget();
  window.addEventListener("hashchange", openTarget);

  // Keuzelijst die direct het formulier verstuurt.
  document.querySelectorAll("[data-autosubmit]").forEach(function (select) {
    select.addEventListener("change", function () { if (select.form) select.form.submit(); });
  });

  // Kleurvarianten en soort kaart op de ontwerppagina: het voorbeeld wisselt mee zonder de pagina te herladen.
  var kleurFrame = document.querySelector("[data-kleur-frame]");
  function zetParam(href, naam, waarde) { var u = new URL(href, window.location.href); u.searchParams.set(naam, waarde); return u.pathname + u.search + u.hash; }
  var soortTekst = { uitnodiging: "Met datum, locatie en aanmelden, bijvoorbeeld voor het kerstdiner.", wenskaart: "Alleen een kerstgroet, zonder datum, locatie of aanmelden." };
  document.querySelectorAll("[data-soort-link]").forEach(function (link) {
    link.addEventListener("click", function (event) {
      if (!kleurFrame || event.metaKey || event.ctrlKey || event.shiftKey) return;
      event.preventDefault();
      var soort = link.getAttribute("data-soort");
      kleurFrame.src = zetParam(kleurFrame.getAttribute("src"), "soort", soort);
      document.querySelectorAll("[data-kleur-link], [data-palette-link]").forEach(function (a) { a.setAttribute("href", zetParam(a.getAttribute("href"), "soort", soort)); });
      document.querySelectorAll("[data-soort-input]").forEach(function (input) { input.value = soort; });
      document.querySelectorAll("[data-soort-link]").forEach(function (other) {
        if (other === link) other.setAttribute("aria-current", "true"); else other.removeAttribute("aria-current");
      });
      var hint = document.querySelector(".segmented__hint");
      if (hint) hint.textContent = soortTekst[soort] || "";
      if (window.history && history.replaceState) history.replaceState(null, "", zetParam(window.location.href, "soort", soort));
    });
  });
  document.querySelectorAll("[data-palette-link]").forEach(function (link) {
    link.addEventListener("click", function (event) {
      if (!kleurFrame || event.metaKey || event.ctrlKey || event.shiftKey) return;
      event.preventDefault();
      var kleur = link.getAttribute("data-kleur");
      function metKleur(href) { var u = new URL(href, window.location.href); u.searchParams.set("kleur", kleur); return u.pathname + u.search + u.hash; }
      kleurFrame.src = metKleur(kleurFrame.getAttribute("src"));
      document.querySelectorAll("[data-kleur-link]").forEach(function (a) { a.setAttribute("href", metKleur(a.getAttribute("href"))); });
      document.querySelectorAll("[data-kleur-input]").forEach(function (input) { input.value = kleur; });
      document.querySelectorAll("[data-kleur-naam]").forEach(function (el) { el.textContent = link.getAttribute("data-naam") || ""; });
      document.querySelectorAll("[data-palette-link]").forEach(function (other) {
        if (other === link) other.setAttribute("aria-current", "true"); else other.removeAttribute("aria-current");
      });
      if (window.history && history.replaceState) history.replaceState(null, "", metKleur(window.location.href));
    });
  });

  // Tekstveld met link: alles selecteren bij focus.
  document.querySelectorAll("[data-select-all]").forEach(function (input) {
    input.addEventListener("focus", function () { input.select(); });
  });

  // Kopieerknoppen (klantomgeving).
  document.querySelectorAll("[data-copy-text]").forEach(function (button) {
    button.hidden = false;
    button.addEventListener("click", function () {
      var text = button.getAttribute("data-copy-text");
      var label = button.textContent;
      function done(ok) {
        button.textContent = ok ? "Gekopieerd" : "Kopiëren lukte niet";
        window.setTimeout(function () { button.textContent = label; }, 2200);
      }
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(false); });
      } else {
        var area = document.createElement("textarea");
        area.value = text; area.style.position = "fixed"; area.style.opacity = "0";
        document.body.appendChild(area); area.select();
        var ok = false;
        try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
        document.body.removeChild(area);
        done(ok);
      }
    });
  });

  // Bevestiging voor gevaarlijke acties.
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (!window.confirm(form.getAttribute("data-confirm"))) event.preventDefault();
    });
  });

  // Dubbel versturen van formulieren voorkomen.
  document.querySelectorAll("form[data-once]").forEach(function (form) {
    form.addEventListener("submit", function () {
      window.setTimeout(function () {
        form.querySelectorAll("button[type=submit]").forEach(function (b) { b.disabled = true; b.setAttribute("aria-disabled", "true"); });
      }, 0);
    });
  });
})();

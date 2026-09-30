/* Vaylide: gedrag van de uitnodigingspagina.
   Openen, onthullen, afteller, muziek (alleen na een tik), delen en aanmelden.
   Alles werkt ook zonder dit script: de inhoud blijft dan gewoon leesbaar. */
(function () {
  "use strict";

  var html = document.documentElement;
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  html.classList.add("invite-ready");

  /* Melodieën voor het speeldoosje in de voorbeelden: [midi, lengte in achtsten].
     'Stille nacht' (Franz Xaver Gruber, 1818) is publiek domein; de zetting en de klank zijn eigen synthese. */
  var MELODIES = {
    "stille-nacht": {
      eighth: 0.37,
      melody: [
        [67, 1.5], [69, 0.5], [67, 1], [64, 3], [67, 1.5], [69, 0.5], [67, 1], [64, 3],
        [74, 2], [74, 1], [71, 3], [72, 2], [72, 1], [67, 3],
        [69, 2], [69, 1], [72, 1.5], [71, 0.5], [69, 1], [67, 1.5], [69, 0.5], [67, 1], [64, 3],
        [69, 2], [69, 1], [72, 1.5], [71, 0.5], [69, 1], [67, 1.5], [69, 0.5], [67, 1], [64, 3],
        [74, 2], [74, 1], [77, 1.5], [74, 0.5], [71, 1], [72, 3], [76, 3],
        [72, 1.5], [67, 0.5], [64, 1], [67, 1.5], [65, 0.5], [62, 1], [60, 6]
      ],
      // Per maat (6 achtsten) twee begeleidingstonen: grondtoon en kwint, op tel 1 en tel 2.
      bass: [[48, 55], [48, 55], [43, 50], [48, 55], [41, 48], [48, 55], [41, 48], [48, 55], [43, 50], [48, 55], [48, 43], [48, 55]],
      rest: 3
    },
    /* 'Carol of the Bells' (Sjtsjedryk, Mykola Leontovytsj, 1914) is publiek domein; deze zetting (celesta, strijkers,
       pizzicato en een kerkklok) en de klank zijn eigen werk. 3/4-maat, lengtes in achtsten; 0 = rust; een lijst = akkoord. */
    "carol-of-the-bells": (function () {
      var motif = [[70, 2], [69, 1], [70, 1], [67, 2]];
      function bars(n, notes, shift) {
        var out = [];
        for (var i = 0; i < n; i++) notes.forEach(function (x) { out.push([x[0] ? x[0] + (shift || 0) : 0, x[1]]); });
        return out;
      }
      var down = [43, 41, 39, 38]; // de dalende bas: G, F, Es, D
      var chords = [[55, 58, 62], [53, 58, 62], [51, 55, 58], [50, 54, 57]];
      function bass(times) {
        var out = [];
        for (var i = 0; i < times; i++) down.forEach(function (r) { out.push([r, 2], [0, 2], [r + 7, 2]); });
        return out;
      }
      function pad(times, up) {
        var out = [];
        for (var i = 0; i < times; i++) chords.forEach(function (c) { out.push([c.map(function (m) { return m + (up || 0); }), 6]); });
        return out;
      }
      return {
        eighth: 0.19,
        rest: 6,
        voices: [
          { inst: "celesta", gain: 0.15, notes: [].concat(bars(16, motif), bars(8, motif, 12), bars(7, motif), [[67, 6]]) },
          { inst: "pizz", gain: 0.2, notes: [].concat([[0, 24]], bass(7)) },
          { inst: "strijkers", gain: 0.02, notes: [].concat([[0, 48]], pad(5)) },
          { inst: "celesta", gain: 0.075, notes: [].concat([[0, 48]], bars(2, [[74, 6], [72, 6], [70, 6], [69, 6]]), bars(2, [[86, 6], [84, 6], [82, 6], [81, 6]])) },
          { inst: "klok", gain: 0.08, notes: [].concat([[0, 96]], [[55, 12], [55, 12], [55, 12], [55, 12]]) }
        ]
      };
    })(),
    /* 'Angels We Have Heard on High' / 'Les anges dans nos campagnes' (Frans kerstlied, 18e eeuw) is publiek domein;
       deze zetting (harp, engelenkoor en celesta) en de klank zijn eigen werk. 4/4-maat in F, lengtes in achtsten. */
    "gloria": (function () {
      var couplet = [[69, 2], [69, 2], [69, 2], [72, 2], [72, 3], [70, 1], [69, 4], [69, 2], [67, 2], [69, 2], [72, 2], [69, 3], [67, 1], [65, 4]];
      var refrein = [
        [72, 3], [74, 1], [72, 1], [70, 1], [69, 2], [70, 3], [72, 1], [70, 1], [69, 1], [67, 2],
        [69, 3], [70, 1], [69, 1], [67, 1], [65, 2], [67, 4], [60, 4],
        [65, 2], [67, 2], [69, 2], [70, 2], [69, 4], [67, 4], [65, 8]
      ];
      var F = [53, 57, 60], C = [52, 55, 60], Dm = [53, 57, 62], Bb = [53, 58, 62];
      var akkCouplet = [[F, 8], [F, 4], [C, 4], [Dm, 4], [C, 4], [C, 4], [F, 4]];
      var akkRefrein = [[F, 8], [C, 8], [Dm, 4], [Bb, 4], [C, 8], [F, 4], [Bb, 4], [F, 4], [C, 4], [F, 8]];
      var akkoorden = [].concat(akkCouplet, akkCouplet, akkRefrein, akkRefrein);
      // Harp: gebroken akkoorden in achtsten, met de grondtoon laag op elke eerste tel.
      var harp = [], bas = [], koor = [];
      akkoorden.forEach(function (a) {
        var c = a[0], patroon = [c[0] + 12, c[1] + 12, c[2] + 12, c[0] + 24, c[2] + 12, c[1] + 12, c[2] + 12, c[0] + 24];
        for (var i = 0; i < a[1]; i++) harp.push([patroon[i % 8], 1]);
        bas.push([c[0] - 12, a[1]]);
        koor.push([c, a[1]]);
      });
      var stil = function (n) { return [[0, n]]; };
      return {
        eighth: 0.26,
        rest: 4,
        voices: [
          { inst: "celesta", gain: 0.13, notes: [].concat(couplet, couplet, refrein, refrein) },
          { inst: "koor", gain: 0.11, notes: [].concat(stil(64), refrein, refrein) },
          { inst: "koor", gain: 0.05, notes: [].concat(stil(32), koor.slice(7)) },
          { inst: "harp", gain: 0.075, notes: harp },
          { inst: "harp", gain: 0.11, notes: bas },
          { inst: "klok", gain: 0.05, notes: [].concat(stil(64), [[65, 56]], [[65, 56]]) }
        ]
      };
    })(),
    /* 'We Wish You a Merry Christmas' (Engels, traditioneel) is publiek domein; deze zetting als gezellige wals
       (warme piano, contrabas en arrensleebellen) en de klank zijn eigen werk. 3/4-maat in G, lengtes in achtsten. */
    "we-wish-you": (function () {
      var melodie = [
        [0, 4], [62, 2],
        [67, 2], [67, 1], [69, 1], [67, 1], [66, 1], [64, 2], [60, 2], [64, 2],
        [69, 2], [69, 1], [71, 1], [69, 1], [67, 1], [66, 2], [62, 2], [62, 2],
        [71, 2], [71, 1], [72, 1], [71, 1], [69, 1], [67, 2], [64, 2], [62, 1], [62, 1],
        [64, 2], [69, 2], [66, 2], [67, 4], [62, 2],
        [67, 2], [67, 2], [67, 2], [66, 4], [66, 2], [67, 2], [66, 2], [64, 2], [62, 4], [69, 2],
        [71, 2], [69, 2], [67, 2], [74, 2], [62, 2], [62, 1], [62, 1], [64, 2], [69, 2], [66, 2], [67, 6]
      ];
      var A = { G: [55, 59, 62], C: [55, 60, 64], A7: [55, 61, 64], D: [54, 57, 62], B7: [54, 59, 63], Em: [55, 59, 64] };
      var grond = { G: 43, C: 48, A7: 45, D: 50, B7: 47, Em: 40 };
      // Per maat drie tellen: op tel 1 de bas, op tel 2 en 3 het akkoord (hoempapa).
      var maten = [null, ["G", "G", "G"], ["C", "C", "C"], ["A7", "A7", "A7"], ["D", "D", "D"], ["B7", "B7", "B7"], ["Em", "Em", "Em"],
        ["C", "D", "D"], ["G", "G", "G"], ["G", "G", "G"], ["D", "D", "D"], ["Em", "A7", "A7"], ["D", "D", "D"], ["G", "G", "G"],
        ["Em", "Em", "Em"], ["C", "D", "D"], ["G", "G", "G"]];
      var bas = [], akkoord = [], bellen = [];
      maten.forEach(function (m, i) {
        if (!m) { bas.push([0, 6]); akkoord.push([0, 6]); bellen.push([0, 6]); return; }
        bas.push([grond[m[0]], 2], [0, 4]);
        akkoord.push([0, 2], [A[m[1]], 2], [A[m[2]], 2]);
        // Arrensleebellen in het refrein (vanaf maat 9), op tel 2 en 3.
        if (i >= 9) bellen.push([0, 2], [96, 2], [96, 2]); else bellen.push([0, 6]);
      });
      return {
        eighth: 0.2,
        rest: 0,
        voices: [
          { inst: "piano", gain: 0.16, notes: melodie },
          { inst: "piano", gain: 0.05, notes: akkoord },
          { inst: "pizz", gain: 0.24, notes: bas },
          { inst: "bellen", gain: 0.05, notes: bellen },
          { inst: "strijkers", gain: 0.012, notes: [].concat([[0, 54]], maten.slice(9).map(function (m) { return [A[m[0]], 6]; })) }
        ]
      };
    })(),
    /* Canon in D (Johann Pachelbel, rond 1700) is publiek domein; deze zetting (harp, cello, strijkers en twee violen
       die elkaar naspelen) en de klank zijn eigen werk. 4/4 in D, per akkoord twee tellen (vier achtsten). */
    "canon": (function () {
      var akk = [[62, 66, 69], [61, 64, 69], [62, 66, 71], [61, 66, 69], [62, 67, 71], [62, 66, 69], [62, 67, 71], [61, 64, 69]];
      var grond = [50, 45, 47, 42, 43, 38, 43, 45]; // D A B Fis G D G A
      var stem1 = [78, 76, 74, 73, 71, 69, 71, 73]; // Fis E D Cis B A B Cis
      var stem2 = [74, 73, 71, 69, 67, 66, 67, 64]; // D Cis B A G Fis G E
      var variatie = [74, 78, 81, 79, 78, 74, 78, 76, 74, 71, 74, 69, 67, 71, 69, 67];
      function lang(noten) { return noten.map(function (m) { return [m, 4]; }); }
      function stil(n) { return [[0, n]]; }
      var CYCLI = 5, harp = [], bas = [], pad = [];
      for (var c = 0; c < CYCLI; c++) {
        akk.forEach(function (a, i) {
          [a[0], a[1], a[2], a[0] + 12].forEach(function (m) { harp.push([m, 1]); });
          bas.push([grond[i], 4]);
          pad.push([a.map(function (m) { return m - 12; }), 4]);
        });
      }
      return {
        eighth: 0.3,
        rest: 4,
        voices: [
          { inst: "harp", gain: 0.07, notes: harp },
          { inst: "harp", gain: 0.1, notes: lang(grond.concat(grond, grond, grond, grond).map(function (m) { return m - 12; })) },
          { inst: "strijkers", gain: 0.016, notes: bas },
          { inst: "strijkers", gain: 0.008, notes: [].concat(stil(32), pad.slice(8)) },
          // Viool 1: de bekende lijn, daarna de dalende lijn en de variatie in kwartnoten.
          { inst: "viool", gain: 0.05, notes: [].concat(stil(32), lang(stem1), lang(stem2), variatie.map(function (m) { return [m, 2]; }), lang(stem1)) },
          // Viool 2 speelt dezelfde lijn een ronde later na (de canon).
          { inst: "viool", gain: 0.035, notes: [].concat(stil(64), lang(stem1), lang(stem2), lang(stem1.map(function (m) { return m - 12; }))) }
        ]
      };
    })()
  };

  /* ---------- Muziek ---------- */
  var music = (function () {
    var root = document.querySelector("[data-music]");
    if (!root) return { play: function () {}, available: false };
    var toggle = root.querySelector("[data-music-toggle]");
    var label = root.querySelector("[data-music-label]");
    var audio = root.querySelector("[data-music-audio]");
    var melody = root.getAttribute("data-music-synth");
    var tune = MELODIES[melody];
    var synth = root.hasAttribute("data-music-synth") ? (tune ? (tune.voices ? createArrangement(tune) : createMusicBox(tune)) : createSynth()) : null;
    var playing = false;
    if (!audio && !synth) return { play: function () {}, available: false };
    toggle.hidden = false;

    function setState(on) {
      playing = on;
      toggle.setAttribute("aria-pressed", on ? "true" : "false");
      label.textContent = on ? "Muziek pauzeren" : "Muziek afspelen";
    }
    function play() {
      if (synth) { synth.start(); setState(true); return; }
      var attempt = audio.play();
      if (attempt && attempt.then) {
        attempt.then(function () { setState(true); }).catch(function () {
          setState(false);
          label.textContent = "Muziek kon niet starten";
        });
      } else { setState(true); }
    }
    function pause() {
      if (synth) synth.stop(); else audio.pause();
      setState(false);
    }
    if (audio) {
      audio.addEventListener("error", function () {
        toggle.disabled = true;
        label.textContent = "Muziek niet beschikbaar";
      });
    }
    toggle.addEventListener("click", function () { if (playing) pause(); else play(); });
    return { play: play, available: true };
  })();

  /* Speeldoosje met een melodie: klokjesklank (grondtoon plus boventonen) en een zachte galm. */
  function createMusicBox(tune) {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    var ctx = null, out = null, timer = null, nextTime = 0, index = 0, playing = false;
    var events = [];
    var t = 0;
    tune.melody.forEach(function (n) { events.push({ at: t, midi: n[0] + 12, len: n[1], gain: 0.16 }); t += n[1]; });
    tune.bass.forEach(function (pair, i) {
      events.push({ at: i * 6, midi: pair[0] + 12, len: 3, gain: 0.07 });
      events.push({ at: i * 6 + 3, midi: pair[1] + 12, len: 3, gain: 0.055 });
    });
    events.sort(function (a, b) { return a.at - b.at; });
    var loopLength = t + (tune.rest || 0);

    function setup() {
      ctx = new AC();
      var master = ctx.createGain();
      master.gain.value = 0.9;
      var soften = ctx.createBiquadFilter();
      soften.type = "lowpass";
      soften.frequency.value = 4200;
      // Galm: een korte, zelfgemaakte impulsrespons (ruis die wegsterft).
      var verb = ctx.createConvolver();
      var len = Math.round(ctx.sampleRate * 2.4);
      var ir = ctx.createBuffer(2, len, ctx.sampleRate);
      for (var c = 0; c < 2; c++) {
        var data = ir.getChannelData(c);
        for (var i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 3.2);
      }
      verb.buffer = ir;
      var wet = ctx.createGain();
      wet.gain.value = 0.32;
      out = ctx.createGain();
      out.connect(soften);
      soften.connect(master);
      out.connect(verb);
      verb.connect(wet);
      wet.connect(master);
      master.connect(ctx.destination);
    }

    function bell(midi, when, gain) {
      var f = 440 * Math.pow(2, (midi - 69) / 12);
      [[1, 1, 2.2], [2.01, 0.28, 0.9], [3.02, 0.1, 0.45], [4.2, 0.05, 0.25]].forEach(function (part) {
        var osc = ctx.createOscillator();
        var g = ctx.createGain();
        osc.type = "sine";
        osc.frequency.value = f * part[0];
        g.gain.setValueAtTime(0.0001, when);
        g.gain.exponentialRampToValueAtTime(gain * part[1], when + 0.006);
        g.gain.exponentialRampToValueAtTime(0.0001, when + part[2]);
        osc.connect(g);
        g.connect(out);
        osc.start(when);
        osc.stop(when + part[2] + 0.05);
      });
    }

    function schedule() {
      var ahead = ctx.currentTime + 0.35;
      while (nextTime < ahead) {
        var e = events[index];
        bell(e.midi, nextTime, e.gain);
        index++;
        var nextAt = index < events.length ? events[index].at : loopLength;
        var delta = nextAt - e.at;
        if (index >= events.length) { index = 0; }
        nextTime += delta * tune.eighth;
      }
    }

    return {
      start: function () {
        if (!ctx) setup();
        if (ctx.state === "suspended") ctx.resume();
        if (playing) return;
        playing = true;
        index = 0;
        nextTime = ctx.currentTime + 0.08;
        schedule();
        timer = setInterval(schedule, 100);
      },
      stop: function () {
        // Wat al klinkt, sterft vanzelf uit in de galm.
        playing = false;
        clearInterval(timer);
        timer = null;
      }
    };
  }

  /* Klein ensemble voor de voorbeelden: meerdere stemmen, elk met een eigen instrument (eigen synthese, geen bestand).
     celesta: heldere klokjes; pizz: getokkelde bas; strijkers: zacht aanzwellende akkoorden; klok: een diepe kerkklok. */
  function createArrangement(tune) {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    var ctx = null, out = null, timer = null, nextTime = 0, index = 0, playing = false;
    var events = [];
    var loopLength = 0;
    tune.voices.forEach(function (voice) {
      var t = 0;
      voice.notes.forEach(function (n) {
        if (n[0]) events.push({ at: t, midi: n[0], len: n[1], inst: voice.inst, gain: voice.gain });
        t += n[1];
      });
      loopLength = Math.max(loopLength, t);
    });
    events.sort(function (a, b) { return a.at - b.at; });
    loopLength += tune.rest || 0;

    function hz(midi) { return 440 * Math.pow(2, (midi - 69) / 12); }

    function setup() {
      ctx = new AC();
      var master = ctx.createGain();
      master.gain.value = 0.85;
      var comp = ctx.createDynamicsCompressor();
      comp.threshold.value = -18;
      comp.ratio.value = 3;
      var verb = ctx.createConvolver();
      var len = Math.round(ctx.sampleRate * 3.2);
      var ir = ctx.createBuffer(2, len, ctx.sampleRate);
      for (var c = 0; c < 2; c++) {
        var data = ir.getChannelData(c);
        for (var i = 0; i < len; i++) data[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2.8);
      }
      verb.buffer = ir;
      var wet = ctx.createGain();
      wet.gain.value = 0.36;
      out = ctx.createGain();
      out.connect(comp);
      out.connect(verb);
      verb.connect(wet);
      wet.connect(comp);
      comp.connect(master);
      master.connect(ctx.destination);
    }

    function partials(f, when, gain, list, type) {
      list.forEach(function (p) {
        var osc = ctx.createOscillator();
        var g = ctx.createGain();
        osc.type = type || "sine";
        osc.frequency.value = f * p[0];
        g.gain.setValueAtTime(0.0001, when);
        g.gain.exponentialRampToValueAtTime(gain * p[1], when + 0.004);
        g.gain.exponentialRampToValueAtTime(0.0001, when + p[2]);
        osc.connect(g);
        g.connect(out);
        osc.start(when);
        osc.stop(when + p[2] + 0.05);
      });
    }

    var play = {
      celesta: function (midi, when, gain) {
        partials(hz(midi + 12), when, gain, [[1, 1, 1.5], [2, 0.3, 0.7], [4, 0.1, 0.3], [7.1, 0.04, 0.08]]);
      },
      pizz: function (midi, when, gain) {
        var osc = ctx.createOscillator();
        var filter = ctx.createBiquadFilter();
        var g = ctx.createGain();
        osc.type = "triangle";
        osc.frequency.value = hz(midi);
        filter.type = "lowpass";
        filter.frequency.setValueAtTime(1600, when);
        filter.frequency.exponentialRampToValueAtTime(300, when + 0.4);
        g.gain.setValueAtTime(0.0001, when);
        g.gain.exponentialRampToValueAtTime(gain, when + 0.008);
        g.gain.exponentialRampToValueAtTime(0.0001, when + 0.7);
        osc.connect(filter);
        filter.connect(g);
        g.connect(out);
        osc.start(when);
        osc.stop(when + 0.75);
      },
      strijkers: function (midi, when, gain, dur) {
        (Array.isArray(midi) ? midi : [midi]).forEach(function (m) {
          var filter = ctx.createBiquadFilter();
          var g = ctx.createGain();
          filter.type = "lowpass";
          filter.frequency.value = 1500;
          g.gain.setValueAtTime(0.0001, when);
          g.gain.linearRampToValueAtTime(gain, when + Math.min(0.6, dur * 0.4));
          g.gain.setValueAtTime(gain, when + dur * 0.8);
          g.gain.exponentialRampToValueAtTime(0.0001, when + dur + 0.9);
          filter.connect(g);
          g.connect(out);
          [-7, 7].forEach(function (cents) {
            var osc = ctx.createOscillator();
            osc.type = "sawtooth";
            osc.frequency.value = hz(m);
            osc.detune.value = cents;
            osc.connect(filter);
            osc.start(when);
            osc.stop(when + dur + 1);
          });
        });
      },
      klok: function (midi, when, gain) {
        partials(hz(midi), when, gain, [[0.5, 0.6, 5], [1, 1, 4], [1.19, 0.45, 3], [1.5, 0.3, 2.4], [2, 0.35, 2], [2.74, 0.2, 1.4], [3.76, 0.1, 0.9]]);
      },
      // Warme piano: grondtoon met zachte boventonen, twee licht verstemde snaren (koor) en een lange uitklank.
      piano: function (midi, when, gain) {
        (Array.isArray(midi) ? midi : [midi]).forEach(function (m) {
          partials(hz(m) * 1.0006, when, gain * 0.6, [[1, 1, 2.6], [2, 0.32, 1.4], [3, 0.12, 0.8], [4, 0.05, 0.5]]);
          partials(hz(m) * 0.9994, when, gain * 0.6, [[1, 1, 2.4], [2, 0.28, 1.2]]);
        });
      },
      // Arrensleebellen: een paar korte, hoge rinkels van gefilterde ruis vlak na elkaar.
      bellen: function (midi, when, gain) {
        var len = Math.round(ctx.sampleRate * 0.25);
        var buf = ctx.createBuffer(1, len, ctx.sampleRate);
        var data = buf.getChannelData(0);
        for (var i = 0; i < len; i++) data[i] = Math.random() * 2 - 1;
        [0, 0.035, 0.07].forEach(function (d, k) {
          var src = ctx.createBufferSource();
          var hp = ctx.createBiquadFilter();
          var g = ctx.createGain();
          src.buffer = buf;
          hp.type = "bandpass";
          hp.frequency.value = 7000 + k * 900;
          hp.Q.value = 3;
          g.gain.setValueAtTime(0.0001, when + d);
          g.gain.exponentialRampToValueAtTime(gain * (1 - k * 0.2) * 4, when + d + 0.004);
          g.gain.exponentialRampToValueAtTime(0.0001, when + d + 0.16);
          src.connect(hp);
          hp.connect(g);
          g.connect(out);
          src.start(when + d);
          src.stop(when + d + 0.2);
        });
      },
      // Viool: twee zaagtanden door een zacht filter, met een trillende toon die pas na de inzet begint.
      viool: function (midi, when, gain, dur) {
        var filter = ctx.createBiquadFilter();
        var g = ctx.createGain();
        filter.type = "lowpass";
        filter.frequency.value = 2600;
        filter.Q.value = 0.8;
        g.gain.setValueAtTime(0.0001, when);
        g.gain.linearRampToValueAtTime(gain, when + Math.min(0.18, dur * 0.3));
        g.gain.setValueAtTime(gain, when + dur * 0.85);
        g.gain.exponentialRampToValueAtTime(0.0001, when + dur + 0.5);
        filter.connect(g);
        g.connect(out);
        [-4, 4].forEach(function (cents) {
          var osc = ctx.createOscillator();
          var lfo = ctx.createOscillator();
          var depth = ctx.createGain();
          osc.type = "sawtooth";
          osc.frequency.value = hz(midi);
          osc.detune.value = cents;
          lfo.frequency.value = 5.6;
          depth.gain.setValueAtTime(0, when);
          depth.gain.linearRampToValueAtTime(14, when + 0.35);
          lfo.connect(depth);
          depth.connect(osc.detune);
          osc.connect(filter);
          osc.start(when);
          lfo.start(when);
          osc.stop(when + dur + 0.6);
          lfo.stop(when + dur + 0.6);
        });
      },
      // Harp: een zachte tokkel met boventonen die snel wegsterven.
      harp: function (midi, when, gain) {
        partials(hz(midi), when, gain, [[1, 1, 2.2], [2, 0.4, 1.1], [3, 0.16, 0.6], [4, 0.06, 0.3]], "triangle");
      },
      // Koor: zaagtanden door twee klinkerfilters ('aah'), met trillende stem en een zachte inzet.
      koor: function (midi, when, gain, dur) {
        (Array.isArray(midi) ? midi : [midi]).forEach(function (m) {
          var g = ctx.createGain();
          g.gain.setValueAtTime(0.0001, when);
          g.gain.linearRampToValueAtTime(gain, when + Math.min(0.28, dur * 0.4));
          g.gain.setValueAtTime(gain, when + dur * 0.85);
          g.gain.exponentialRampToValueAtTime(0.0001, when + dur + 0.7);
          [[760, 7, 1], [1180, 9, 0.6], [2600, 10, 0.25]].forEach(function (f) {
            var bp = ctx.createBiquadFilter();
            var fg = ctx.createGain();
            bp.type = "bandpass";
            bp.frequency.value = f[0];
            bp.Q.value = f[1];
            fg.gain.value = f[2] * 3.2;
            bp.connect(fg);
            fg.connect(g);
            [-6, 6].forEach(function (cents) {
              var osc = ctx.createOscillator();
              var lfo = ctx.createOscillator();
              var depth = ctx.createGain();
              osc.type = "sawtooth";
              osc.frequency.value = hz(m);
              osc.detune.value = cents;
              lfo.frequency.value = 5.2 + cents / 20;
              depth.gain.value = 9;
              lfo.connect(depth);
              depth.connect(osc.detune);
              osc.connect(bp);
              osc.start(when);
              lfo.start(when);
              osc.stop(when + dur + 0.8);
              lfo.stop(when + dur + 0.8);
            });
          });
          g.connect(out);
        });
      }
    };

    function schedule() {
      var ahead = ctx.currentTime + 0.35;
      while (nextTime < ahead) {
        var e = events[index];
        play[e.inst](e.midi, nextTime, e.gain, e.len * tune.eighth);
        index++;
        var nextAt = index < events.length ? events[index].at : loopLength;
        if (index >= events.length) index = 0;
        nextTime += (nextAt - e.at) * tune.eighth;
      }
    }

    return {
      start: function () {
        if (!ctx) setup();
        if (ctx.state === "suspended") ctx.resume();
        if (playing) return;
        playing = true;
        index = 0;
        nextTime = ctx.currentTime + 0.08;
        schedule();
        timer = setInterval(schedule, 100);
      },
      stop: function () {
        playing = false;
        clearInterval(timer);
        timer = null;
      }
    };
  }

  /* Speeldoosje voor de voorbeelden (eigen synthese, geen bestand nodig).
     Melodie: canon-achtige akkoordenreeks (publiek domein). */
  function createSynth() {
    var AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    var ctx = null, timer = null, step = 0;
    var chords = [
      [62, 66, 69], [57, 61, 64], [59, 62, 66], [54, 57, 61],
      [55, 59, 62], [50, 54, 57], [55, 59, 62], [57, 61, 64]
    ];
    function note(midi, when, length, volume) {
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = 440 * Math.pow(2, (midi - 69) / 12);
      gain.gain.setValueAtTime(0.0001, when);
      gain.gain.exponentialRampToValueAtTime(volume, when + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, when + length);
      osc.connect(gain).connect(ctx.destination);
      osc.start(when);
      osc.stop(when + length + 0.05);
    }
    function tick() {
      var chord = chords[Math.floor(step / 4) % chords.length];
      var t = ctx.currentTime + 0.05;
      var pattern = [0, 1, 2, 1];
      note(chord[pattern[step % 4]] + 12, t, 1.4, 0.06);
      if (step % 4 === 0) note(chord[0] - 12, t, 2.4, 0.05);
      step++;
    }
    return {
      start: function () {
        if (!ctx) ctx = new AC();
        if (ctx.state === "suspended") ctx.resume();
        if (!timer) { tick(); timer = setInterval(tick, 420); }
      },
      stop: function () { clearInterval(timer); timer = null; }
    };
  }

  /* ---------- Openingsscherm ---------- */
  (function () {
    var cover = document.querySelector("[data-cover]");
    var main = document.getElementById("uitnodiging");
    if (!cover || !main) return;
    var key = "vierlief-open:" + location.pathname;
    var skip = /^#(aanmelden|aanmelden-formulier|uitnodiging)/.test(location.hash) || (html.hasAttribute("data-live") && html.getAttribute("data-live") !== "stijl") || html.hasAttribute("data-direct-open");  // bij Stijl: de envelop laten zien
    // De live kaart in de editor onthoudt niets: bij Stijl altijd de dichte envelop.
    if (!html.hasAttribute("data-live")) { try { if (sessionStorage.getItem(key)) skip = true; } catch (e) { /* privémodus */ } }
    if (skip) { finish(true); return; }

    html.classList.add("has-cover");
    main.inert = true;
    var opened = false;

    cover.querySelectorAll("[data-open]").forEach(function (el) {
      el.addEventListener("click", function (event) {
        event.preventDefault();
        if (el.hasAttribute("data-open-music")) music.play();
        open();
      });
      el.addEventListener("keydown", function (event) {
        if (event.key === " " || event.key === "Spacebar") { event.preventDefault(); el.click(); }
      });
    });

    function open() {
      if (opened) return;
      opened = true;
      /* Rustig openen bij 'minder beweging' of als de gast de beweging heeft stilgezet (effects.js). */
      var calm = reduceMotion || html.classList.contains("fx-paused");
      var duration = calm ? 250 : parseInt(cover.getAttribute("data-duration") || "2200", 10);
      html.classList.add("is-opening");
      if (calm) html.classList.add("is-opening-reduced");
      document.dispatchEvent(new CustomEvent("invite:opening", { detail: { reduceMotion: calm } }));
      window.setTimeout(function () { finish(false); }, duration);
    }

    function finish(instant) {
      html.classList.remove("has-cover", "is-opening", "is-opening-reduced");
      html.classList.add("is-open");
      cover.hidden = true;
      main.inert = false;
      // De kleine kaart op de bedankpagina (inv-embed) telt niet als 'al geopend' voor het echte bezoek.
      if (!html.classList.contains("inv-embed")) { try { sessionStorage.setItem(key, "1"); } catch (e) { /* privémodus */ } }
      if (!instant) {
        window.scrollTo(0, 0);
        var heading = main.querySelector("h1");
        if (heading) {
          heading.setAttribute("tabindex", "-1");
          heading.focus({ preventScroll: true });
        }
      }
      document.dispatchEvent(new CustomEvent("invite:opened", { detail: { instant: !!instant } }));
    }
  })();

  /* ---------- Onthullen bij scrollen ---------- */
  (function () {
    var items = document.querySelectorAll("[data-reveal]");
    if (!items.length) return;
    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    items.forEach(function (el) { observer.observe(el); });
  })();

  /* ---------- Afteller ---------- */
  document.querySelectorAll("[data-countdown]").forEach(function (el) {
    var target = Date.parse(el.getAttribute("data-countdown"));
    if (isNaN(target)) return;
    var parts = {};
    el.querySelectorAll("[data-unit]").forEach(function (n) { parts[n.getAttribute("data-unit")] = n; });
    var done = el.parentNode.querySelector("[data-countdown-done]");
    function pad(n) { return n < 10 ? "0" + n : String(n); }
    function show(node, value) {
      if (!node || node.textContent === value) return;
      node.textContent = value;
      /* Cijfer klapt om (alleen met beweging; zie effects.css). */
      if (html.classList.contains("fx-motion")) {
        node.classList.remove("is-tick");
        void node.offsetWidth;
        node.classList.add("is-tick");
      }
    }
    function update() {
      /* Stilgezet met de knop 'Beweging': de afteller loopt pas verder als de beweging weer aan staat. */
      if (html.classList.contains("fx-paused")) return true;
      var diff = Math.max(0, target - Date.now());
      if (diff <= 0) {
        el.hidden = true;
        if (done) done.hidden = false;
        return false;
      }
      var s = Math.floor(diff / 1000);
      var days = Math.floor(s / 86400);
      show(parts.days, String(days));
      show(parts.hours, pad(Math.floor((s % 86400) / 3600)));
      show(parts.minutes, pad(Math.floor((s % 3600) / 60)));
      show(parts.seconds, pad(s % 60));
      var dayLabel = parts.days && parts.days.nextElementSibling;
      if (dayLabel) dayLabel.textContent = days === 1 ? "dag" : "dagen";
      return true;
    }
    if (update()) {
      var timer = window.setInterval(function () { if (!update()) window.clearInterval(timer); }, 1000);
    }
  });

  /* ---------- Tijdzone-opmerking als de gast in een andere tijdzone zit ---------- */
  try {
    var guestZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    document.querySelectorAll("[data-tz-note]").forEach(function (el) {
      if (guestZone && guestZone !== el.getAttribute("data-tz-note")) el.hidden = false;
    });
  } catch (e) { /* oudere browser */ }

  /* ---------- Link kopiëren en delen ---------- */
  document.querySelectorAll("[data-copy]").forEach(function (btn) {
    btn.hidden = false;
    var status = btn.closest(".inv-share") && btn.closest(".inv-share").querySelector("[data-copy-status]");
    btn.addEventListener("click", function () {
      var text = btn.getAttribute("data-copy");
      function done(ok) {
        if (status) status.textContent = ok ? "Link gekopieerd." : "Kopiëren lukte niet. Selecteer de link handmatig: " + text;
      }
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(function () { done(true); }, function () { done(fallbackCopy(text)); });
      } else {
        done(fallbackCopy(text));
      }
    });
  });
  function fallbackCopy(text) {
    var area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.appendChild(area);
    area.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(area);
    return ok;
  }
  if (navigator.share) {
    document.querySelectorAll("[data-native-share]").forEach(function (btn) {
      btn.hidden = false;
      btn.addEventListener("click", function () {
        navigator.share({ title: btn.getAttribute("data-share-title"), url: btn.getAttribute("data-share-url") }).catch(function () {});
      });
    });
  }

  /* ---------- Aanmelden ---------- */
  document.querySelectorAll("[data-rsvp-form]").forEach(function (form) {
    var status = form.querySelector("[data-rsvp-status]");
    var submit = form.querySelector("[data-rsvp-submit]");
    var submitLabel = submit ? submit.textContent : "";
    var busy = false;
    var demo = form.hasAttribute("data-rsvp-demo");

    function syncAttending() {
      var checked = form.querySelector("input[name='attending']:checked");
      var attending = !checked || checked.value === "ja";
      form.querySelectorAll("[data-when-attending]").forEach(function (block) {
        block.hidden = !attending;
        block.querySelectorAll("input, select, textarea").forEach(function (input) { input.disabled = !attending; });
      });
    }
    form.querySelectorAll("input[name='attending']").forEach(function (r) { r.addEventListener("change", syncAttending); });
    syncAttending();

    function setStatus(message, isError) {
      if (!status) return;
      status.textContent = message || "";
      status.classList.toggle("is-error", !!isError);
    }
    function clearErrors() {
      form.querySelectorAll(".field__error[data-js]").forEach(function (n) { n.remove(); });
      form.querySelectorAll("[aria-invalid]").forEach(function (n) { n.removeAttribute("aria-invalid"); });
    }
    function showErrors(errors) {
      var first = null;
      Object.keys(errors).forEach(function (name) {
        var input = form.querySelector("[name='" + name + "']");
        var message = document.createElement("p");
        message.className = "field__error";
        message.setAttribute("data-js", "");
        message.textContent = errors[name];
        if (input) {
          input.setAttribute("aria-invalid", "true");
          var field = input.closest(".field") || input.parentNode;
          field.appendChild(message);
          if (!first) first = input;
        } else if (status) {
          setStatus(errors[name], true);
        }
      });
      if (first) first.focus();
    }
    function localCheck() {
      var errors = {};
      var name = form.querySelector("[name='name']");
      if (name && !name.value.trim()) errors.name = "Vul je naam in.";
      if (!form.querySelector("input[name='attending']:checked")) errors.attending = "Kies of je erbij bent.";
      form.querySelectorAll("[required]").forEach(function (input) {
        if (input.disabled || input.name === "name" || input.name === "attending") return;
        if (input.type === "radio") {
          if (!form.querySelector("input[name='" + input.name + "']:checked")) errors[input.name] = "Beantwoord deze vraag.";
        } else if (!String(input.value || "").trim()) {
          errors[input.name] = "Beantwoord deze vraag.";
        }
      });
      return errors;
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (busy) return;
      clearErrors();
      setStatus("");
      var errors = localCheck();
      if (Object.keys(errors).length) { showErrors(errors); setStatus("Controleer de gemarkeerde velden.", true); return; }
      var attending = !!form.querySelector("input[name='attending'][value='ja']:checked");
      if (demo) {
        setStatus("Dit is een voorbeeld: je antwoord is niet opgeslagen. In een echte uitnodiging komt het direct bij de organisator binnen.");
        /* Het feestje komt uit de verstuurknop: die is op dit moment in beeld. */
        document.dispatchEvent(new CustomEvent("invite:rsvp", { detail: { attending: attending, demo: true, target: form.querySelector("[data-rsvp-submit]") || form } }));
        return;
      }
      busy = true;
      submit.disabled = true;
      submit.textContent = "Bezig met versturen…";
      fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { "Accept": "application/json", "X-Requested-With": "fetch" },
        credentials: "same-origin"
      }).then(function (response) {
        return response.json().catch(function () { return { ok: false, message: "Er ging iets mis. Probeer het opnieuw." }; })
          .then(function (data) { data.status = response.status; return data; });
      }).then(function (data) {
        if (data.ok) {
          var box = document.createElement("div");
          box.className = "rsvp__thanks";
          box.setAttribute("tabindex", "-1");
          var title = document.createElement("h3");
          title.textContent = data.title || "Bedankt!";
          var text = document.createElement("p");
          text.textContent = data.message || "Je antwoord is opgeslagen.";
          box.appendChild(title);
          box.appendChild(text);
          if (data.edit_url) {
            var p = document.createElement("p");
            var a = document.createElement("a");
            a.className = "inv-link";
            a.href = data.edit_url;
            a.textContent = "Wijzig je antwoord";
            p.appendChild(a);
            box.appendChild(p);
          }
          form.replaceWith(box);
          box.focus();
          document.dispatchEvent(new CustomEvent("invite:rsvp", { detail: { attending: attending, demo: false, target: box } }));
          return;
        }
        busy = false;
        submit.disabled = false;
        submit.textContent = submitLabel;
        if (data.errors) showErrors(data.errors);
        setStatus(data.message || "Je antwoord is niet opgeslagen. Probeer het opnieuw.", true);
      }).catch(function () {
        busy = false;
        submit.disabled = false;
        submit.textContent = submitLabel;
        setStatus("Geen verbinding. Je antwoord is nog niet opgeslagen; probeer het opnieuw.", true);
      });
    });
  });
})();

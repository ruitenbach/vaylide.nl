"""Kerststad: een eigen VAYLIDE-arrangement van "O dennenboom" ("O Tannenbaum"), instrumentaal, vrij van rechten.

    python tools/kerststad/maak_muziek.py [--ffmpeg <pad>] [--wav-alleen]

De melodie is publiek domein (traditioneel, door Ernst Anschütz in 1824 van een tekst voorzien); de noten komen uit de publieke notatie op Wikipedia (G-groot, 3/4, opmaat van een
achtste). Alles daaromheen is eigen werk: het arrangement, de harmonie, de opbouw en de klank. Er is geen opname, geen sample en geen ander arrangement gebruikt: elke toon wordt met numpy
opgebouwd (celesta, piano, strijkers, cello, zachte belletjes) en door een eigen galm gehaald.

Vorm: 32 maten van 3/4 op 66 BPM (87,3 s) in vier rondes van "A B" (A = "O dennenboom ... wie treu sind deine Blätter", B = "du grünst nicht nur zur Sommerzeit ..."):
  ronde 1 (maat 1-8)   intiem: celesta en zachte piano; vanaf maat 5 een heel zachte strijkerslaag
  ronde 2 (maat 9-16)  uitzoomen naar het dorp: strijkers en cello komen erbij, de piano begint te stromen
  ronde 3 (maat 17-24) de stad ontwaakt: vollere strijkers met de melodie, celesta-glans, subtiele belletjes
  ronde 4 (maat 25-32) de bruisende kerstnacht (A, het rijkste moment) en daarna (B) weer tot rust, terug naar het begin
De lus is circulair: de galm loopt rond het eind heen naar het begin, het laatste akkoord (G) is het eerste, en de opmaat van de melodie (D) staat aan het eind van de lus, vlak voor de eerste
maat, zodat de herhaling muzikaal en ritmisch doorloopt. Het resultaat gaat als mp3 naar designs/kerststad/v1/media/muziek.mp3.
"""
import argparse
import subprocess
import wave
from pathlib import Path

import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("--ffmpeg", default="ffmpeg")
ap.add_argument("--wav-alleen", action="store_true")
args = ap.parse_args()

SR, BPM, MATEN = 44100, 66, 32
BEAT = 60 / BPM
MAAT = 3 * BEAT
N = round(MATEN * MAAT * SR)
rng = np.random.default_rng(1824)
L, R = np.zeros(N), np.zeros(N)


def freq(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tijd(lengte_s):
    return np.arange(round(lengte_s * SR)) / SR


def zacht(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def zet(sig_l, sig_r, start_s):
    """Telt een geluid op in de buffer; wat voorbij het einde valt (of vóór het begin) loopt circulair door, zodat de lus zonder naad aansluit."""
    i0 = round(start_s * SR) % N
    pos, n = 0, len(sig_l)
    while pos < n:
        stuk = min(n - pos, N - i0)
        L[i0:i0 + stuk] += sig_l[pos:pos + stuk]
        R[i0:i0 + stuk] += sig_r[pos:pos + stuk]
        pos += stuk
        i0 = 0


def paneer(sig, pan):
    hoek = (pan + 1) * np.pi / 4
    return sig * np.cos(hoek), sig * np.sin(hoek)


# ------------------------------------------------------------------ instrumenten
def celesta(m, vel):
    f, t = freq(m), tijd(3.4)
    delen = [(1, 1.0, 1.9), (2, 0.14, 0.8), (4, 0.22, 0.45), (6.05, 0.06, 0.22)]
    s = sum(a * np.exp(-t / d) * np.sin(2 * np.pi * f * r * t) for r, a, d in delen)
    return s * np.minimum(1, t / 0.004) * vel * 0.46


def piano(m, vel, lengte):
    f, t = freq(m), tijd(min(5.0, lengte + 1.8))
    basisverval = 3.4 * (1.9 - np.clip((m - 36) / 60, 0, 1) * 1.3)
    s = np.zeros_like(t)
    for korting in (0.9996, 1.0004):
        for n in range(1, 15):
            fn = n * f * korting * np.sqrt(1 + 0.00035 * n * n)
            if fn > 7500:
                break
            amp = (1.0 / n ** 1.05) * vel ** (0.15 * (n - 1))
            s += amp * np.exp(-t / (basisverval / (1 + 0.55 * (n - 1)))) * np.sin(2 * np.pi * fn * t + n * 0.3)
    loslaten = np.where(t > lengte, np.exp(-(t - lengte) / 0.55), 1.0)
    return s * np.minimum(1, t / 0.006) * loslaten * vel * 0.15


def strijkers(m, vel, lengte, aanzet=0.9, loslaten=1.5):
    f = freq(m)
    t = tijd(lengte + loslaten + 0.2)
    env = zacht(t / aanzet) * np.where(t > lengte, zacht(1 - (t - lengte) / loslaten), 1.0)
    uit_l, uit_r = np.zeros_like(t), np.zeros_like(t)
    for cent, pan in ((-9, -0.7), (0, 0.0), (9, 0.7)):
        fv = f * 2 ** (cent / 1200)
        vib = 1 + 0.0024 * zacht((t - 0.9) / 1.3) * np.sin(2 * np.pi * (5.0 + rng.random() * 0.5) * t)
        fase = 2 * np.pi * np.cumsum(fv * vib) / SR
        s = sum((1.0 / n) * np.exp(-n / 5.5) * np.sin(n * fase) for n in range(1, 13))     # warm: de hoge boventonen sterven snel uit
        uit_l += s * np.cos((pan + 1) * np.pi / 4)
        uit_r += s * np.sin((pan + 1) * np.pi / 4)
    return uit_l * env * vel * 0.085, uit_r * env * vel * 0.085


def cello(m, vel, lengte):
    f, t = freq(m), tijd(lengte + 1.4)
    env = zacht(t / 0.35) * np.where(t > lengte, zacht(1 - (t - lengte) / 1.3), 1.0)
    s = np.sin(2 * np.pi * f * t) + 0.40 * np.sin(4 * np.pi * f * t) + 0.16 * np.sin(6 * np.pi * f * t) + 0.05 * np.sin(8 * np.pi * f * t)
    return s * env * vel * 0.19


def belletje(m, vel):
    """Een zacht, laag belletje (hooguit rond 1,5 kHz): lange, warme uitklank, geen scherpe aanslag."""
    f, t = freq(m), tijd(3.4)
    delen = [(1, 1.0, 2.8), (2.0, 0.34, 2.0), (2.76, 0.16, 1.2), (4.07, 0.05, 0.6)]
    s = sum(a * np.exp(-t / d) * np.sin(2 * np.pi * f * r * t) for r, a, d in delen)
    return s * np.minimum(1, t / 0.006) * vel * 0.16


# ------------------------------------------------------------------ de melodie (publiek domein): G-groot, 3/4; (beat in de maat, midi, lengte in tellen)
MEL_A = [
    [(0, 67, .75), (.75, 67, .25), (1, 67, 1), (2, 69, 1)],
    [(0, 71, .75), (.75, 71, .25), (1, 71, 1.5), (2.5, 71, .5)],
    [(0, 69, .5), (.5, 71, .5), (1, 72, 1), (2, 66, 1)],
    [(0, 69, 1), (1, 67, 1)],
]
MEL_B = [
    [(0, 74, .5), (.5, 71, .5), (1, 76, 1.5), (2.5, 74, .5)],
    [(0, 74, .5), (.5, 72, .5), (1, 72, 1.5), (2.5, 72, .5)],
    [(0, 72, .5), (.5, 69, .5), (1, 74, 1.5), (2.5, 72, .5)],
    [(0, 72, .5), (.5, 71, .5), (1, 71, 1)],
]
OPMAAT_A = (62, .5)       # de D vóór "O dennenboom", op tel 2,5 van de maat ervoor
OPMAAT_B = (74, .5)       # de hoge D vóór "du grünst", op tel 2,5 van de laatste maat van A

# ------------------------------------------------------------------ de harmonie: (bastoon, stemmen voor strijkers/piano)
AKK = {
    "G": (43, [55, 59, 62, 66]),
    "G7": (43, [53, 59, 62, 67]),
    "C": (36, [55, 59, 64, 67]),
    "D": (38, [57, 62, 66, 69]),
    "D7": (38, [57, 60, 66, 69]),
    "D/F#": (42, [57, 62, 66, 69]),
    "Am7": (45, [55, 60, 64, 67]),
}
HARM_A = [[(0, 2, "G"), (2, 3, "D/F#")], [(0, 3, "G")], [(0, 2, "Am7"), (2, 3, "D7")], [(0, 1, "D7"), (1, 3, "G")]]
HARM_B = [[(0, 1, "G7"), (1, 3, "C")], [(0, 3, "D7")], [(0, 3, "D7")], [(0, 3, "G")]]

# hoe vol het is per maat (0 tot 1): intiem → dorp → stad ontwaakt → bruisende nacht → weer tot rust
BOOG = ([.22, .25, .28, .30, .34, .36, .38, .40] + [.46, .50, .54, .58, .62, .64, .66, .68]
        + [.74, .78, .82, .84, .88, .90, .92, .94] + [1.0, 1.0, 1.0, .98, .86, .72, .56, .40])


def t_op(maat, tel):
    return (maat * 3 + tel) * BEAT


def menselijk(s=0.010):
    return (rng.random() - 0.5) * 2 * s


for maat in range(MATEN):
    ronde, k = divmod(maat, 8)
    deel_b = k >= 4
    kk = k % 4
    o = BOOG[maat]
    harm = (HARM_B if deel_b else HARM_A)[kk]
    mel = (MEL_B if deel_b else MEL_A)[kk]
    t0 = t_op(maat, 0)

    # --- melodie ---
    for tel, m, lengte in mel:
        start = t0 + tel * BEAT + (menselijk(0.008) if maat > 0 else 0)
        dur = lengte * BEAT
        if ronde == 0:
            if not deel_b:
                zet(*paneer(celesta(m + 12, 0.60 + 0.2 * o), 0.2), start)
            else:
                zet(*paneer(piano(m, 0.46 + 0.2 * o, dur), 0.05), start)
                zet(*paneer(celesta(m + 12, 0.30), 0.25), start)
        elif ronde == 1:
            if not deel_b:
                zet(*paneer(celesta(m + 12, 0.62 + 0.2 * o), 0.2), start)
                zet(*paneer(piano(m, 0.30, dur), 0.0), start)
            else:
                l, r = strijkers(m, 0.42 + 0.25 * o, dur * 0.95, aanzet=0.25, loslaten=0.8)
                zet(l, r, start - 0.03)
                zet(*paneer(piano(m, 0.40 + 0.15 * o, dur), 0.05), start)
        elif ronde == 2:
            for extra, vel in ((0, 0.40 + 0.28 * o), (-12, 0.26 + 0.2 * o)):
                l, r = strijkers(m + extra, vel, dur * 0.97, aanzet=0.22, loslaten=0.9)
                zet(l, r, start - 0.03)
            zet(*paneer(celesta(m + 12, 0.46 + 0.14 * o), 0.25), start)
            zet(*paneer(piano(m, 0.38 + 0.12 * o, dur), 0.0), start)
        else:
            sterk = 0.52 + 0.3 * o
            for extra, vel in ((0, sterk), (-12, sterk * 0.62), (12, sterk * 0.28)):
                l, r = strijkers(m + extra, vel, dur * 0.98, aanzet=0.2, loslaten=1.1)
                zet(l, r, start - 0.03)
            zet(*paneer(celesta(m + 12, 0.56 + 0.12 * o), 0.3), start)
            zet(*paneer(celesta(m + 24, 0.26 * o), -0.3), start + 0.01)
            zet(*paneer(piano(m, 0.42 + 0.12 * o, dur), 0.0), start)

    # --- harmonie: een strijkerslaag, cello en de piano per akkoord ---
    for b0, b1, naam in harm:
        bas, stemmen = AKK[naam]
        lengte = (b1 - b0) * BEAT
        s0 = t0 + b0 * BEAT
        # strijkerslaag
        if (ronde == 0 and maat >= 4) or ronde >= 1:
            aantal = 3 if ronde <= 1 else 4
            vel = (0.20 + 0.20 * o) if ronde == 0 else (0.30 + 0.45 * o)
            for m in stemmen[:aantal]:
                l, r = strijkers(m, vel, lengte + 0.3, aanzet=1.3 if ronde == 0 else 0.9, loslaten=1.4)
                zet(l, r, s0 - 0.12)
        # cello: de grondtoon (vanaf het eind van de eerste ronde)
        if (ronde == 0 and maat >= 6) or ronde >= 1:
            zet(*paneer(cello(bas, 0.40 + 0.34 * o, lengte + 0.1), -0.25), s0)
        # piano: in de eerste ronde rustig (alleen accenten), later een stromend arpeggio
        if ronde == 0:
            if not deel_b:
                zet(*paneer(piano(bas + 12, 0.34 + 0.2 * o, lengte + 0.5), -0.25), s0)
                if b1 - b0 >= 2:
                    zet(*paneer(piano(stemmen[1], 0.26 + 0.16 * o, lengte), -0.15), s0 + 1 * BEAT)
        else:
            sterkte = 0.30 + 0.30 * o
            tellen = [b0 + x * 0.5 for x in range(int((b1 - b0) / 0.5))]
            patroon = [bas + 12, stemmen[1], stemmen[2], stemmen[3], stemmen[2], stemmen[1]]
            for x, tel in enumerate(tellen):
                pos = int(round(tel / 0.5)) % 6
                m = patroon[pos]
                zet(*paneer(piano(m, sterkte * (1.15 if pos == 0 else 0.85), 0.9), -0.3 + 0.1 * pos), t0 + tel * BEAT + menselijk(0.006))

    # --- belletjes: nooit scherp: laag, zacht en spaarzaam, pas vanaf de tweede ronde ---
    if ronde >= 1:
        aantal = (1 if maat % 2 == 0 else 0) if ronde == 1 else (1 + (maat % 2) if ronde == 2 else (3 if not deel_b else 1))
        bas, stemmen = AKK[harm[0][2]]
        toppen = [x + 24 for x in stemmen[1:]] + [x + 36 for x in stemmen[1:3]]
        toppen = [x for x in toppen if x <= 88]
        for _ in range(aantal):
            m = int(rng.choice(toppen))
            zet(*paneer(belletje(m, (0.30 + 0.30 * o) * (0.75 + 0.25 * rng.random())), rng.uniform(-0.8, 0.8)), t0 + rng.uniform(0.3, 2.6) * BEAT)

# --- de opmaten: de D vóór elke A en de hoge D vóór elke B; die vóór de eerste A staat aan het eind van de lus ---
for ronde in range(4):
    a_maat = ronde * 8
    zet(*paneer(celesta(OPMAAT_A[0] + 12, 0.46 + 0.1 * BOOG[a_maat]), 0.2), t_op(a_maat - 1, 2.5))     # a_maat - 1 = -1 voor ronde 1: aan het eind van de lus
    b_opmaat = t_op(a_maat + 3, 2.5)
    zet(*paneer(celesta(OPMAAT_B[0] + 12 - 12, 0.42 + 0.1 * BOOG[a_maat + 3]), 0.2), b_opmaat)
# het laatste akkoord (G) en het eerste (G) zijn hetzelfde: de laatste maat laat het akkoord uitklinken in de eerste maat

# ------------------------------------------------------------------ galm (circulair, zodat het eind naadloos in het begin overgaat) en afwerking
def galm(duur=3.6):
    n = round(duur * SR)
    t = np.arange(n) / SR
    uit = []
    for _ in range(2):
        ruis = rng.standard_normal(n)
        donker = np.convolve(ruis, np.ones(28) / 28, mode="same")
        ir = ruis * np.exp(-t / 0.50) * 0.45 + donker * np.exp(-t / 1.25) * 1.7
        ir *= np.minimum(1, t / 0.014)
        uit.append(ir / np.sqrt(np.sum(ir ** 2)))
    return uit


def conv_circulair(x, ir):
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)


irl, irr = galm()
natl, natr = conv_circulair(L, irl), conv_circulair(R, irr)
nat_mix = 0.36
uitl, uitr = L * (1 - 0.35 * nat_mix) + natl * nat_mix * 1.5, R * (1 - 0.35 * nat_mix) + natr * nat_mix * 1.5

# de boog over het hele stuk (circulair geïnterpoleerd), daarna een zachte begrenzer
boog_t = np.arange(MATEN) * MAAT + MAAT / 2
env = np.interp(np.arange(N) / SR, boog_t, 0.55 + 0.45 * np.array(BOOG), period=MATEN * MAAT)
uitl, uitr = uitl * env, uitr * env
piek = max(np.abs(uitl).max(), np.abs(uitr).max())
rms = np.sqrt((uitl ** 2 + uitr ** 2).mean() / 2)
winst = min(10 ** (-21 / 20) / rms, 0.89 / piek)
uitl, uitr = np.tanh(uitl * winst * 1.1) / 1.1, np.tanh(uitr * winst * 1.1) / 1.1
stereo = np.stack([uitl, uitr], axis=1)

print(f"duur {N / SR:.2f} s ({MATEN} maten van 3/4 op {BPM} BPM), piek {np.abs(stereo).max():.3f} ({20 * np.log10(np.abs(stereo).max()):.1f} dBFS), "
      f"gemiddeld (rms) {np.sqrt((stereo ** 2).mean()):.4f} ({20 * np.log10(np.sqrt((stereo ** 2).mean())):.1f} dBFS)")
print(f"naad: stap bij het omslaan van eind naar begin {np.abs(stereo[0] - stereo[-1]).max():.4f}")

UIT = Path(__file__).resolve().parents[2] / "designs/kerststad/v1/media"
UIT.mkdir(parents=True, exist_ok=True)
wav = UIT.parents[3] / "voorvertoning-hero" / "stad" / "muziek.wav"
wav.parent.mkdir(parents=True, exist_ok=True)
with wave.open(str(wav), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(stereo, -1, 1) * 32767).astype("<i2").tobytes())
if not args.wav_alleen:
    subprocess.run([args.ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav), "-c:a", "libmp3lame", "-q:a", "3", "-id3v2_version", "0", "-write_xing", "1",
                    str(UIT / "muziek.mp3")], check=True)
    print("mp3:", UIT / "muziek.mp3", round((UIT / "muziek.mp3").stat().st_size / 1e6, 2), "MB")

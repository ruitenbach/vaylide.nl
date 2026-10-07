"""Kerststad: een eigen kerstnummer, zelf gecomponeerd en gesynthetiseerd (geen bestaand lied, geen samples, geen zang) en dus vrij van rechten.

    python tools/kerststad/maak_muziek.py [--ffmpeg <pad>] [--wav-alleen]

Titel: "Kerststad (avondlicht)". D-groot, 66 BPM, 24 maten (87 s) die naadloos terugkeren naar het begin (de laatste maten lossen op in dezelfde akkoorden als de eerste, en de galm
loopt circulair, zodat er geen stilte of klik is bij het herhalen). De opbouw volgt de film: een rustig dorp (celesta en een zachte strijkerslaag, maten 1 tot 8), de stad ontwaakt (zachte piano,
cello en belletjes, 9 tot 16), een bruisende kerstnacht (strijkers in octaven, vollere piano, veel belletjes, 17 tot 22) en weer tot rust (23 en 24). Alles wordt met numpy opgebouwd:
celesta (metaalstaafklank), piano (inharmonische boventonen), strijkers (drie licht verstemde zaagtanden met een trage inzet), cello, kerstbelletjes (inharmonisch) en een eigen galm.
Het resultaat gaat als mp3 naar designs/kerststad/v1/media/muziek.mp3. De noten staan hieronder als gewone lijsten, zodat een component of toonaard makkelijk te wijzigen is.
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

SR, BPM, MATEN = 44100, 66, 24
BEAT = 60 / BPM
N = round(MATEN * 4 * BEAT * SR)
rng = np.random.default_rng(1224)
L, R = np.zeros(N), np.zeros(N)


def freq(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def zet(sig_l, sig_r, start_s):
    """Telt een geluid op in de buffer vanaf start_s; wat voorbij het einde valt, loopt door aan het begin (circulair)."""
    i0 = round(start_s * SR) % N
    n = len(sig_l)
    pos = 0
    while pos < n:
        stuk = min(n - pos, N - i0)
        L[i0:i0 + stuk] += sig_l[pos:pos + stuk]
        R[i0:i0 + stuk] += sig_r[pos:pos + stuk]
        pos += stuk
        i0 = 0


def paneer(sig, pan):
    hoek = (pan + 1) * np.pi / 4
    return sig * np.cos(hoek), sig * np.sin(hoek)


def tijd(lengte_s):
    return np.arange(round(lengte_s * SR)) / SR


def zacht(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ instrumenten
def celesta(m, vel):
    f, t = freq(m), tijd(3.6)
    delen = [(1, 1.0, 2.0), (2, 0.16, 0.9), (4, 0.30, 0.55), (6.05, 0.09, 0.28), (9.2, 0.03, 0.14)]
    s = sum(a * np.exp(-t / d) * np.sin(2 * np.pi * f * r * t) for r, a, d in delen)
    s *= np.minimum(1, t / 0.003)
    return s * vel * 0.5


def piano(m, vel, lengte):
    f, t = freq(m), tijd(min(5.0, lengte + 1.8))
    basisverval = 3.4 * (1.9 - np.clip((m - 36) / 60, 0, 1) * 1.3)
    s = np.zeros_like(t)
    for korting in (0.9996, 1.0004):                       # twee snaren, licht verstemd: een zachte zweving
        for n in range(1, 15):
            fn = n * f * korting * np.sqrt(1 + 0.00035 * n * n)
            if fn > 9000:
                break
            amp = (1.0 / n ** 0.95) * vel ** (0.15 * (n - 1))
            s += amp * np.exp(-t / (basisverval / (1 + 0.55 * (n - 1)))) * np.sin(2 * np.pi * fn * t + n * 0.3)
    aanzet = np.minimum(1, t / 0.005)
    loslaten = np.where(t > lengte, np.exp(-(t - lengte) / 0.5), 1.0)
    return s * aanzet * loslaten * vel * 0.16


def strijkers(m, vel, lengte, aanzet=0.8, loslaten=1.0):
    f = freq(m)
    t = tijd(lengte + loslaten + 0.2)
    env = zacht(t / aanzet) * np.where(t > lengte, zacht(1 - (t - lengte) / loslaten), 1.0)
    uit_l, uit_r = np.zeros_like(t), np.zeros_like(t)
    for cent, pan in ((-8, -0.7), (0, 0.0), (8, 0.7)):
        fv = f * 2 ** (cent / 1200)
        vib = 1 + 0.0025 * zacht((t - 0.8) / 1.2) * np.sin(2 * np.pi * (5.1 + rng.random() * 0.4) * t)
        fase = 2 * np.pi * np.cumsum(fv * vib) / SR
        s = sum((1.0 / n) * np.exp(-n / 7.0) * np.sin(n * fase) for n in range(1, 16))
        gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        uit_l += s * gl
        uit_r += s * gr
    return uit_l * env * vel * 0.085, uit_r * env * vel * 0.085


def cello(m, vel, lengte):
    f, t = freq(m), tijd(lengte + 1.2)
    env = zacht(t / 0.18) * np.where(t > lengte, zacht(1 - (t - lengte) / 1.1), 1.0)
    s = np.sin(2 * np.pi * f * t) + 0.42 * np.sin(4 * np.pi * f * t) + 0.2 * np.sin(6 * np.pi * f * t) + 0.08 * np.sin(8 * np.pi * f * t)
    return s * env * vel * 0.19


def belletje(m, vel):
    f, t = freq(m), tijd(3.0)
    delen = [(1, 1.0, 2.6), (2.0, 0.5, 2.0), (2.76, 0.35, 1.5), (4.07, 0.2, 1.0), (5.4, 0.1, 0.7), (6.8, 0.05, 0.4)]
    s = sum(a * np.exp(-t / d) * np.sin(2 * np.pi * f * r * t) for r, a, d in delen)
    return s * np.minimum(1, t / 0.002) * vel * 0.17


def sleebel(vel):
    """Een heel klein belletjesgeritsel: vier snelle, hoge tikjes."""
    uit = np.zeros(round(0.9 * SR))
    for k in range(4):
        t = tijd(0.22)
        f0 = 4200 + 900 * rng.random()
        s = sum(a * np.sin(2 * np.pi * f0 * r * t + rng.random() * 6) for r, a in ((1, 1), (1.51, .6), (2.37, .4), (3.1, .25))) * np.exp(-t / 0.05)
        i = round(k * (0.085 + 0.03 * rng.random()) * SR)
        uit[i:i + len(s)] += s * vel * 0.03 * (1 - 0.15 * k)
    return uit


# ------------------------------------------------------------------ muziek: akkoorden (bas, laag naar hoog), melodie en begeleiding
AKK = {
    "D9": (38, [57, 61, 64, 66, 69]),
    "Bm9": (35, [54, 57, 61, 62, 66]),
    "Gmaj7": (43, [54, 59, 62, 66, 69]),
    "G#11": (43, [54, 59, 61, 66, 69]),
    "Asus": (45, [52, 57, 62, 64, 69]),
    "A": (45, [52, 57, 61, 64, 69]),
    "D": (38, [57, 62, 66, 69, 74]),
    "A/C#": (49, [52, 57, 61, 64, 69]),
    "Bm": (35, [54, 59, 62, 66, 71]),
    "F#m": (42, [54, 57, 61, 66, 69]),
    "G": (43, [55, 59, 62, 67, 71]),
    "D/F#": (42, [57, 62, 66, 69, 74]),
    "Em7": (40, [55, 59, 62, 64, 67]),
}
VOLGORDE = ["D9", "D9", "Bm9", "Bm9", "Gmaj7", "G#11", "Asus", "A",
            "D", "A/C#", "Bm", "F#m", "G", "D/F#", "Em7", "A",
            "G", "D/F#", "Em7", "A", "Bm", "G", "Asus", "A"]
# melodie per maat: (slag, midi, lengte in slagen)
MELODIE = [
    [(0, 81, 2), (2, 78, 1), (3, 76, 1)], [(0, 78, 2), (2, 74, 2)], [(0, 74, 1), (1, 78, 1), (2, 83, 2)], [(0, 81, 3), (3, 78, 1)],
    [(0, 79, 1.5), (1.5, 78, .5), (2, 74, 1), (3, 71, 1)], [(0, 76, 1), (1, 79, 1), (2, 85, 2)], [(0, 81, 2), (2, 76, 1), (3, 74, 1)], [(0, 73, 3), (3, 76, 1)],
    [(0, 78, 1), (1, 81, 1), (2, 86, 1.5), (3.5, 85, .5)], [(0, 85, 1), (1, 81, 1), (2, 76, 2)], [(0, 83, 1), (1, 78, 1), (2, 74, 1), (3, 78, 1)], [(0, 81, 2), (2, 85, 1), (3, 81, 1)],
    [(0, 83, 1.5), (1.5, 79, .5), (2, 86, 2)], [(0, 85, 1), (1, 81, 1), (2, 78, 2)], [(0, 79, 1), (1, 83, 1), (2, 86, 1), (3, 83, 1)], [(0, 85, 2), (2, 81, 1), (3, 76, 1)],
    [(0, 86, 2), (2, 83, 2)], [(0, 85, 2), (2, 81, 2)], [(0, 86, 1), (1, 83, 1), (2, 79, 2)], [(0, 85, 3), (3, 88, 1)],
    [(0, 90, 2), (2, 86, 2)], [(0, 88, 2), (2, 86, 1), (3, 83, 1)], [(0, 81, 2), (2, 78, 1), (3, 76, 1)], [(0, 76, 2), (2, 73, 2)],
]
# hoe vol het is, per maat (0 tot 1): de boog van rustig dorp naar bruisende nacht en terug
BOOG = [0.30, 0.34, 0.40, 0.44, 0.48, 0.52, 0.55, 0.58,
        0.62, 0.66, 0.70, 0.74, 0.78, 0.82, 0.86, 0.90,
        0.94, 1.0, 1.0, 1.0, 1.0, 0.95, 0.60, 0.34]


def maat_start(maat):
    return maat * 4 * BEAT


def menselijk(s=0.012):
    return (rng.random() - 0.5) * 2 * s


for maat in range(MATEN):
    bas, noten = AKK[VOLGORDE[maat]]
    o = BOOG[maat]
    t0 = maat_start(maat)
    # strijkerslaag: de hele maat, zachter in het dorp, vol in de nacht
    for m in noten[:4 if maat < 8 else 5]:
        l, r = strijkers(m, 0.30 + 0.55 * o, 4 * BEAT + 0.2, aanzet=1.3 if maat < 8 else 0.8, loslaten=1.4)
        zet(l, r, t0 - 0.15)
    # cello: de grondtoon
    if maat >= 2:
        if maat < 8 or maat >= 22:
            zet(*paneer(cello(bas, 0.5 + 0.3 * o, 4 * BEAT), -0.2), t0)
        else:
            for s in (0, 2):
                zet(*paneer(cello(bas, 0.55 + 0.3 * o, 2 * BEAT - 0.05), -0.2), t0 + s * BEAT)
    # piano: een rustig arpeggio dat vanaf het derde stuk wat levendiger wordt
    if maat >= 2 and maat < 8:
        for slag, i in ((0, 0), (1.5, 2), (3, 3)):
            zet(*paneer(piano(noten[i] - 12 * (i == 0), 0.38 + 0.2 * o, 2.5), -0.25), t0 + slag * BEAT + menselijk())
    elif 8 <= maat < 16:
        for k, i in enumerate((0, 1, 2, 3, 2, 1, 2, 3)):
            zet(*paneer(piano(noten[i], 0.40 + 0.25 * o + 0.05 * (k % 2 == 0), 0.9), -0.2 + 0.05 * k), t0 + k * 0.5 * BEAT + menselijk(0.008))
    elif 16 <= maat < 22:
        for k, i in enumerate((0, 1, 2, 3, 4, 3, 2, 1)):
            zet(*paneer(piano(noten[i], 0.50 + 0.28 * o + 0.05 * (k % 2 == 0), 0.9), -0.3 + 0.08 * k), t0 + k * 0.5 * BEAT + menselijk(0.008))
    elif maat >= 22:
        for slag, i in ((0, 0), (2, 2)):
            zet(*paneer(piano(noten[i], 0.34, 2.6), -0.2), t0 + slag * BEAT)
    # melodie: celesta (dorp), celesta met piano (stad), strijkers in octaven met celesta (nacht)
    for slag, m, lengte in MELODIE[maat]:
        start = t0 + slag * BEAT + (menselijk(0.010) if maat > 0 else 0)
        zet(*paneer(celesta(m, 0.62 + 0.22 * o), 0.25), start)
        if 8 <= maat < 16:
            zet(*paneer(piano(m - 12, 0.5 + 0.2 * o, lengte * BEAT), 0.1), start)
        if 16 <= maat < 22:
            for extra in (0, -12):
                l, r = strijkers(m + extra, 0.5 + 0.35 * o, lengte * BEAT, aanzet=0.35, loslaten=0.9)
                zet(l, r, start - 0.04)
            zet(*paneer(celesta(m + 12, 0.35), -0.3), start + 0.02)
    # belletjes: heel spaarzaam in het dorp, vaker naarmate de stad ontwaakt, een glinstering in de nacht
    aantal = 0 if maat in (0, 1) else (1 if maat < 8 else (2 if maat < 16 else (4 if maat < 22 else 1)))
    toppen = [n + 24 for n in noten[1:]] + [n + 36 for n in noten[1:3]]
    for k in range(aantal):
        m = int(rng.choice(toppen))
        zet(*paneer(belletje(m, (0.32 + 0.25 * o) * (0.7 + 0.3 * rng.random())), rng.uniform(-0.8, 0.8)), t0 + rng.uniform(0.2, 3.7) * BEAT)
    if 16 <= maat < 22 and maat % 2 == 0:
        zet(*paneer(sleebel(0.6), 0.5), t0 + 1.5 * BEAT)
        zet(*paneer(sleebel(0.5), -0.5), t0 + 3.5 * BEAT)

# ------------------------------------------------------------------ galm (circulair, zodat het einde naadloos in het begin overgaat) en afwerking
def galm(duur=3.4):
    n = round(duur * SR)
    t = np.arange(n) / SR
    uit = []
    for _ in range(2):
        ruis = rng.standard_normal(n)
        donker = np.convolve(ruis, np.ones(24) / 24, mode="same")                      # lage frequenties
        ir = ruis * np.exp(-t / 0.55) * 0.55 + donker * np.exp(-t / 1.15) * 1.6          # hoge delen sterven eerder uit dan lage
        ir *= np.minimum(1, t / 0.012)
        uit.append(ir / np.sqrt(np.sum(ir ** 2)))
    return uit


def conv_circulair(x, ir):
    return np.fft.irfft(np.fft.rfft(x, N) * np.fft.rfft(ir, N), N)


irl, irr = galm()
natl, natr = conv_circulair(L, irl), conv_circulair(R, irr)
nat_mix = 0.34
uitl, uitr = L * (1 - 0.35 * nat_mix) + natl * nat_mix * 1.5, R * (1 - 0.35 * nat_mix) + natr * nat_mix * 1.5

# de boog over het hele stuk en een zachte begrenzer
maat_s = 4 * BEAT
boog_t = np.arange(MATEN) * maat_s + maat_s / 2
env = np.interp(np.arange(N) / SR, boog_t, 0.55 + 0.45 * np.array(BOOG), period=MATEN * maat_s)
uitl, uitr = uitl * env, uitr * env
piek = max(np.abs(uitl).max(), np.abs(uitr).max())
doel_rms = 10 ** (-21 / 20)
rms = np.sqrt((uitl ** 2 + uitr ** 2).mean() / 2)
winst = min(doel_rms / rms, 0.89 / piek)
uitl, uitr = np.tanh(uitl * winst * 1.1) / 1.1 * 1.0, np.tanh(uitr * winst * 1.1) / 1.1 * 1.0

# een heel zachte hoogdoorlaat tegen gelijkspanning en laagfrequente bonk
for kan in (uitl, uitr):
    kan -= np.convolve(kan, np.ones(2205) / 2205, mode="same") * 0.0  # (geen filter nodig: de gelijkspanning is nul)

stereo = np.stack([uitl, uitr], axis=1)
print(f"lengte {N / SR:.1f} s, piek {np.abs(stereo).max():.3f}, rms {np.sqrt((stereo ** 2).mean()):.4f} ({20 * np.log10(np.sqrt((stereo ** 2).mean())):.1f} dBFS)")
print(f"naad: laatste en eerste 20 ms: {np.sqrt((stereo[-882:] ** 2).mean()):.4f} / {np.sqrt((stereo[:882] ** 2).mean()):.4f}; stap bij het omslaan: {np.abs(stereo[0] - stereo[-1]).max():.4f}")

UIT = Path(__file__).resolve().parents[2] / "designs/kerststad/v1/media"
UIT.mkdir(parents=True, exist_ok=True)
wav = UIT.parent.parent.parent.parent / "voorvertoning-hero" / "stad" / "muziek.wav"
wav.parent.mkdir(parents=True, exist_ok=True)
pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
with wave.open(str(wav), "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
if not args.wav_alleen:
    subprocess.run([args.ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(wav), "-c:a", "libmp3lame", "-q:a", "3", "-id3v2_version", "0", "-write_xing", "1",
                    str(UIT / "muziek.mp3")], check=True)
    print("mp3:", UIT / "muziek.mp3", round((UIT / "muziek.mp3").stat().st_size / 1e6, 2), "MB")

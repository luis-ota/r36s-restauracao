import wave
import sys

import numpy as np

SR = 44100
BPM = 72
BEAT = 60.0 / BPM
BAR = 4 * BEAT
BARS = 32
N = int(round(BAR * BARS * SR))
TAU = 2 * np.pi
OUT = "/tmp/opencode/lain_chill/lain_menu_chill.wav"
rng = np.random.default_rng(1977)

CHORDS = [
    [53, 57, 60, 64],  # Fmaj7
    [50, 53, 57, 60],  # Dm7
    [46, 53, 57, 62],  # Bbmaj7
    [45, 52, 55, 60],  # Am7 (cor leve de menor, aconchegante)
    [43, 50, 53, 58],  # Gm7
    [48, 53, 55, 58],  # C7sus4
    [53, 57, 60, 64],  # Fmaj7
    [48, 52, 55, 62],  # Cadd9
]
BASS = [41, 38, 46, 45, 43, 36, 41, 36]

MELODY = [
    (69, 0.0, 1.5), (72, 1.5, 0.5), (74, 2.0, 1.5),
    (72, 4.0, 1.0), (69, 5.0, 0.5), (65, 5.5, 1.5),
    (62, 8.0, 2.0), (65, 10.0, 1.0), (69, 11.0, 1.0),
    (69, 12.0, 1.5), (72, 13.5, 0.5), (64, 14.0, 2.0),
    (67, 16.0, 1.0), (70, 17.0, 1.0), (74, 18.0, 2.0),
    (70, 20.0, 1.5), (67, 21.5, 0.5), (65, 22.0, 2.0),
    (69, 24.0, 1.5), (72, 25.5, 0.5), (76, 26.0, 2.0),
    (72, 28.0, 1.0), (67, 29.0, 1.0), (64, 30.0, 2.0),
]

pad = np.zeros(N)
bass = np.zeros(N)
bells = np.zeros(N)
lead = np.zeros(N)
rain = np.zeros(N)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tri(ph):
    return (2 / np.pi) * np.arcsin(np.sin(ph))


def env(n, a, r):
    e = np.ones(n)
    na = min(n, int(a * SR))
    if na:
        e[:na] = np.linspace(0, 1, na)
    nr = min(n, int(r * SR))
    if nr:
        e[n - nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def put(layer, start_s, sig):
    s = int(round(start_s * SR))
    idx = (np.arange(len(sig)) + s) % N
    layer[idx] += sig


def pad_note(m, start, dur, amp):
    n = int((dur + 1.6) * SR)
    t = np.arange(n) / SR
    f = mtof(m)
    sig = 0.0
    for d in (1.0, 1.0015):
        ph = TAU * f * d * t
        sig = sig + 0.55 * np.sin(ph) + 0.45 * tri(ph)
    sig = sig / 2 * env(n, 0.9, 1.6) * amp
    put(pad, start, sig)


def bass_note(m, start, dur, amp):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sig = tri(TAU * mtof(m) * t) * env(n, 0.015, 0.5) * amp
    put(bass, start, sig)


def bell(m, start, amp=0.10):
    n = int(2.2 * SR)
    t = np.arange(n) / SR
    f = mtof(m)
    sig = (
        1.0 * np.sin(TAU * f * t) * np.exp(-t / 0.45)
        + 0.22 * np.sin(TAU * 2 * f * t) * np.exp(-t / 0.25)
        + 0.07 * np.sin(TAU * 3.01 * f * t) * np.exp(-t / 0.12)
    )
    put(bells, start, sig * amp)


def pluck(m, start, amp):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = mtof(m)
    sig = (0.7 * tri(TAU * f * t) + 0.3 * np.sin(TAU * f * t)) * np.exp(-t / 0.09) * amp
    put(bells, start, sig)


def lead_note(m, start, dur, amp):
    n = int(dur * BEAT * 0.95 * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(TAU * 5.0 * t)
    f = mtof(m)
    ph = TAU * f * np.cumsum(vib) / SR
    sig = (0.6 * np.sin(ph) + 0.4 * tri(ph)) * env(n, 0.06, 0.35) * amp
    put(lead, start, sig)


for bar in range(BARS):
    t0 = bar * BAR
    chord = CHORDS[bar % 8]
    root = BASS[bar % 8]
    for m in chord:
        pad_note(m, t0, BAR, 0.07 / len(chord) * 2.2)

    bounce = [(0, root, 0.45, 0.20), (0.5, root + 12, 0.25, 0.09),
              (1, root + 7, 0.45, 0.13), (1.5, root + 12, 0.25, 0.09),
              (2, root, 0.45, 0.20), (2.5, root + 12, 0.25, 0.09),
              (3, root + 7, 0.45, 0.13), (3.5, root + 12, 0.25, 0.09)]
    for beat, m, dur, amp in bounce:
        bass_note(m, t0 + beat * BEAT, BEAT * dur * 2, amp)

    for beat in (0.5, 1.5, 2.5, 3.5):
        if rng.random() < 0.6:
            tone = int(rng.choice(chord)) + 12
            pluck(tone, t0 + beat * BEAT, 0.05 + 0.02 * rng.random())

    for beat in rng.choice([0, 1, 1.5, 2, 2.5, 3, 3.5], size=2, replace=False):
        if rng.random() < 0.85:
            tone = int(rng.choice(chord))
            while tone < 72:
                tone += 12
            while tone > 88:
                tone -= 12
            bell(tone, t0 + beat * BEAT, amp=0.10 + 0.03 * rng.random())

phrase = []
for rep in range(4):
    base = rep * 8 * BAR
    if rep == 2:
        notes = [x for x in MELODY if x[1] < 16.0]
    else:
        notes = MELODY
    for m, b, d in notes:
        amp = 0.10 if rep != 1 else 0.085
        lead_note(m, base + b * BEAT, d, amp)

main = pad * 1.0 + bass * 0.9 + bells * 0.45 + lead * 0.85
main_rms_target = 10 ** (-18.6 / 20)
main = main / np.sqrt(np.mean(main ** 2)) * main_rms_target

ceil = 10 ** (-6.5 / 20)
knee = ceil * 0.75
absx = np.abs(main)
over = absx > knee
sign = np.sign(main)
main = main.copy()
main[over] = sign[over] * (
    knee + (ceil - knee) * np.tanh((absx[over] - knee) / (ceil - knee))
)

final = main
peak = np.max(np.abs(final))
if peak > ceil:
    final = final * (ceil / peak)

rms = np.sqrt(np.mean(final ** 2))
print(f"duração: {N / SR:.3f} s, amostras: {N}")
print(f"RMS: {20 * np.log10(rms):.2f} dBFS")
print(f"pico: {20 * np.log10(np.max(np.abs(final))):.2f} dBFS")

seam = abs(final[0] - final[-1])
typical = np.median(np.abs(np.diff(final)))
print(f"emenda: salto={seam:.5f}, mediana |dx|={typical:.5f}")

pcm = np.clip(final * 32767, -32768, 32767).astype("<i2")
with wave.open(OUT, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    wf.writeframes(pcm.tobytes())
print("wav:", OUT)

"""Mouth shape for every frame, from the forced-aligned phones (build/timeline.json).

Shapes: the sheet's A, E, I, O, U and REST (REST also closes for M/B/P), plus FV, L and TH made to match them.
Rules: a shape shows one frame before its sound; M/B/P and F/V closures last at least two frames; weak consonants
never flash for a single frame; the mouth is closed whenever there is no sound. A loud sigh parts the lips; the
recordings have no laughter, so there is no laugh mouth anywhere.

-> build/visemes.json {"fps", "n", "track": [shape per frame], "amp": [0..1 loudness per frame]}"""
import json, numpy as np, librosa

LEAD = 0.035
# ARPAbet -> shape (diphthongs are two shapes); AH depends on its length: schwa / 'uh' / open 'ah'
PH = {"AA": "A", "AE": "A", "AO": "O", "AW": ("A", "U"), "AY": ("A", "I"), "EH": "E", "ER": "E",
      "EY": ("E", "I"), "IH": "I", "IY": "I", "OW": ("O", "U"), "OY": ("O", "I"), "UH": "U", "UW": "U",
      "B": "REST", "P": "REST", "M": "REST", "F": "FV", "V": "FV", "TH": "TH", "DH": "TH", "L": "L",
      "W": "U", "R": "U", "Y": "I", "S": "I", "Z": "I", "T": "I", "D": "I", "N": "I",
      "SH": "U", "ZH": "U", "CH": "U", "JH": "U"}
CARRY = {"K", "G", "NG", "HH"}          # back consonants / breathy onsets take the next vowel's shape
VOWEL = {"A", "E", "I", "O", "U"}
MUST = {"REST", "FV"}                   # visible closures that are never dropped

def shape_of(ph, k):
    p = ph[k]["p"]
    if p == "AH":
        d = ph[k]["e"] - ph[k]["s"]
        return "I" if d < 0.07 else ("E" if d < 0.14 else "A")
    if p in CARRY:
        for j in range(k + 1, min(k + 3, len(ph))):
            if ph[j]["w"] != ph[k]["w"] and p != "HH": break
            v = shape_of(ph, j)
            v = v[0] if isinstance(v, tuple) else v
            if v in VOWEL: return v
        return "E"
    return PH.get(p, "I")

def loudness(tl, n, fps):
    """per-frame loudness 0..1 of the voice on the scene timeline (for mouth size and the body's breathing)"""
    amp = np.zeros(n)
    for c in tl["clips"]:
        y, sr = librosa.load(c["file"], sr=16000)
        hop = sr // fps
        r = librosa.feature.rms(y=y, frame_length=hop * 2, hop_length=hop, center=True)[0]
        db = 20 * np.log10(r + 1e-6)
        a = np.clip((db + 50) / 35, 0, 1)
        i0 = int(round(c["at"] * fps))
        m = min(len(a), n - i0)
        amp[i0:i0 + m] = np.maximum(amp[i0:i0 + m], a[:m])
    return amp

def build():
    tl = json.load(open("build/timeline.json"))
    fps, n = tl["fps"], tl["n"]
    ph = tl["phones"]
    ev = []
    for k, x in enumerate(ph):
        v = shape_of(ph, k)
        if isinstance(v, tuple):
            mid = x["s"] + (x["e"] - x["s"]) * 0.55
            ev += [(x["s"], mid, v[0]), (mid, x["e"], v[1])]
        else:
            ev.append((x["s"], x["e"], v))
    for s in tl["sounds"]:
        if s["kind"] == "sigh": ev.append((s["s"] + 0.05, s["e"] - 0.05, "I"))
    ev.sort()
    # paint the events on a 1 ms grid (earlier events win where two overlap), then sample every frame
    grid = np.full(int((n / fps + 1) * 1000), "REST", dtype=object)
    for a, b, v in reversed(ev):
        grid[max(0, int(a * 1000)):max(0, int(b * 1000))] = v
    track = [grid[min(len(grid) - 1, int((i / fps + LEAD) * 1000))] for i in range(n)]
    # closures shorter than a frame still show, for two frames
    for a, b, v in ev:
        if v not in MUST: continue
        c = int(round(((a + b) / 2 - LEAD) * fps))
        if not 0 <= c < n or sum(1 for j in (c - 1, c, c + 1) if 0 <= j < n and track[j] == v) >= 2: continue
        track[c] = v
        track[c + 1 if c + 1 < n else c - 1] = v
    # a weak consonant between two equal shapes never flashes for one frame
    for i in range(1, n - 1):
        if track[i] not in MUST and track[i] != track[i - 1] and track[i - 1] == track[i + 1]:
            track[i] = track[i - 1]
    amp = loudness(tl, n, fps)
    json.dump({"fps": fps, "n": n, "track": track, "amp": [round(float(a), 3) for a in amp]},
              open("build/visemes.json", "w"))
    from collections import Counter
    print(Counter(track))
    W = tl["words"]
    for w in W[:12] + W[40:46]:
        a, b = int(w["s"] * fps), int(w["e"] * fps) + 1
        print(f"{w['w']:>14} {w['s']:7.2f} {' '.join(track[a:b])}")

if __name__ == "__main__":
    build()

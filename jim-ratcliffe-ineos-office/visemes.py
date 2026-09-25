"""Build a per-frame viseme track from the phone alignment + energy-based onset/offset refinement.
Clips are laid out on the scene timeline with an intro (walk-in), gaps between clips and an outro (exit)."""
import json, numpy as np, librosa

FPS = 30
CLIPS = ["src/audio1.mp3", "src/audio2.mp3", "src/audio3.mp3", "src/audio4.mp3"]
INTRO = 4.0                 # walk in, turn to camera, straighten the tie
GAPS = [1.0, 1.1, 0.9]      # silences between the clips
OUTRO = 4.8                 # turns and hurries off to the yacht, then the empty office

# the mouth sheet's 19 shapes
VIS = ["REST", "A", "E", "I", "O", "U", "FV", "L", "M", "B", "CDGK", "CHJ", "R", "TH", "W", "SZ", "T", "N", "Q"]

# ARPAbet phone -> viseme (diphthongs split into two parts); "AH" depends on its length (schwa vs 'but')
PH = {
 "AA": "A", "AE": "A", "AO": "O", "AW": ("A", "W"), "AY": ("A", "I"), "EH": "E", "ER": "R",
 "EY": ("E", "I"), "IH": "I", "IY": "E", "OW": ("O", "U"), "OY": ("O", "I"), "UH": "Q", "UW": "U",
 "B": "B", "P": "B", "M": "M", "F": "FV", "V": "FV", "TH": "TH", "DH": "TH", "L": "L",
 "S": "SZ", "Z": "SZ", "SH": "CHJ", "ZH": "CHJ", "CH": "CHJ", "JH": "CHJ", "R": "R", "W": "W", "Y": "I",
 "K": "CDGK", "G": "CDGK", "NG": "CDGK", "D": "CDGK", "T": "T", "N": "N",
}
VOWELS = {"A", "E", "I", "O", "U", "Q"}
MUST = {"M", "B", "FV"}          # visible closures that must never be dropped

def speech_segments(f):
    y, sr = librosa.load(f, sr=16000)
    r = librosa.feature.rms(y=y, frame_length=640, hop_length=160, center=True)[0]  # 10 ms hop
    db = 20 * np.log10(r + 1e-6)
    on = db > -42
    segs, s = [], None
    for i, v in enumerate(np.append(on, False)):
        if v and s is None: s = i
        if not v and s is not None: segs.append([s * 0.01, i * 0.01]); s = None
    merged = []
    for sg in segs:                              # close stop-closure gaps < 90 ms, drop blips < 40 ms
        if merged and sg[0] - merged[-1][1] < 0.09: merged[-1][1] = sg[1]
        else: merged.append(sg)
    return [sg for sg in merged if sg[1] - sg[0] >= 0.04], len(y) / 16000

def clip_track(f, ph):
    segs, dur = speech_segments(f)
    P = ph["phones"]
    pk = [((p["s"] + p["e"]) / 2) for p in P]
    def seg_of(t):
        best, bd = 0, 1e9
        for i, (a, b) in enumerate(segs):
            d = 0 if a <= t <= b else min(abs(t - a), abs(t - b))
            if d < bd: best, bd = i, d
        return best
    sid = [seg_of(t) for t in pk]
    iv = []
    for k, p in enumerate(P):
        a, b = segs[sid[k]]
        first = k == 0 or sid[k - 1] != sid[k]; last = k == len(P) - 1 or sid[k + 1] != sid[k]
        st = a if first else p["s"]
        en = b if last else p["e"]
        st, en = max(st, a), min(max(en, st + 0.01), b)
        iv.append({"p": p["p"], "s": st, "e": en, "w": p["w"]})
    used = set(sid)
    breaths = [(a, b) for i, (a, b) in enumerate(segs) if i not in used]
    return iv, segs, dur, breaths

def build():
    ph = json.load(open("phones.json"))
    offs, t = [], INTRO
    events, words, segs_all, durs = [], [], [], []
    for ci, f in enumerate(CLIPS):
        iv, segs, dur, breaths = clip_track(f, ph[f])
        events += [(t + a, t + b, "N", "breath") for a, b in breaths]
        for k, x in enumerate(iv):
            p = x["p"]
            if p == "HH":                        # breathy onset: mouth already shaped for the next vowel
                nxt = iv[k + 1]["p"] if k + 1 < len(iv) else "AH"
                v = PH.get(nxt, "N"); v = v[0] if isinstance(v, tuple) else v
            elif p == "AH":
                v = "CDGK" if x["e"] - x["s"] >= 0.09 else "N"
            else:
                v = PH.get(p, "N")
            if isinstance(v, tuple):
                mid = x["s"] + (x["e"] - x["s"]) * 0.55
                events += [(t + x["s"], t + mid, v[0], p), (t + mid, t + x["e"], v[1], p)]
            else:
                events.append((t + x["s"], t + x["e"], v, p))
        for i, w in enumerate(ph[f]["words"]):
            ws = [x for x in iv if x["w"] == i]
            words.append({"w": w["w"], "s": t + ws[0]["s"], "e": t + ws[-1]["e"], "clip": ci})
        segs_all += [[t + a, t + b] for a, b in segs]
        offs.append(t); durs.append(dur)
        t += dur + (GAPS[ci] if ci < len(GAPS) else 0)
    total = offs[-1] + durs[-1] + OUTRO
    n = int(round(total * FPS))
    LEAD = 0.035  # show the mouth shape ~1 frame before the sound (animation convention)
    events.sort()
    track = []
    for i in range(n):
        tt = i / FPS + LEAD
        v = "REST"
        for (a, b, vv, p) in events:
            if a <= tt < b: v = vv; break
        track.append(v)
    # every closure (M/B/P, F/V) is visible for >= 2 frames even if it fell between samples
    for (a, b, vv, p) in events:
        if vv in MUST:
            c = int(round(((a + b) / 2 - LEAD) * FPS))
            if 0 <= c < n and vv not in track[max(0, c - 1):c + 2]:
                track[c] = vv
            if 0 <= c < n:
                for j in (c, c + 1):
                    if j < n and track[j] != vv and sum(1 for x in track[max(0, c - 1):c + 2] if x == vv) < 2:
                        track[j] = vv
    # remove single-frame blips of weak consonants (smooth flicker)
    for i in range(1, n - 1):
        if track[i] not in MUST and track[i] not in VOWELS and track[i - 1] == track[i + 1] and track[i] != track[i - 1]:
            track[i] = track[i - 1]
    json.dump({"fps": FPS, "n": n, "total": total, "offsets": offs, "durs": durs, "track": track,
               "words": words, "segs": segs_all, "events": events}, open("timeline.json", "w"), indent=1)
    print("frames", n, "total %.2f" % total, "offsets", [round(o, 2) for o in offs])
    from collections import Counter; print(Counter(track))
    for w in words[:10]:
        a, b = int(w["s"] * FPS), int(w["e"] * FPS) + 1
        print(f"{w['w']:>12} {w['s']:6.2f} {' '.join(track[a:b])}")

if __name__ == "__main__":
    build()

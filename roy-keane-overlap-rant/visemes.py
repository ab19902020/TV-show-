"""Build a per-frame viseme track from phoneme alignment + energy-based onset/offset refinement."""
import json, numpy as np, librosa

FPS = 30
INTRO, GAP = 1.6, 0.6
CLIPS = ["src/audio1.mp3", "src/audio2.mp3"]
VIS = ["A", "E", "I", "O", "U", "FV", "L", "MBP", "SZ", "CDGK", "TH", "WQ", "REST"]

# phoneme -> viseme (diphthongs split into two parts)
PH = {
 "ɑː": "A", "ɑ": "A", "a": "A", "ʌ": "A", "ɐ": "A", "ɑːɹ": ("A", "WQ"),
 "æ": "E", "ɛ": "E", "e": "E", "ɛɹ": ("E", "WQ"),
 "ɪ": "I", "i": "I", "iː": "I", "ᵻ": "I", "j": "I", "ɪɹ": ("I", "WQ"),
 "ɔː": "O", "ɔ": "O", "ɒ": "O", "ɔːɹ": ("O", "WQ"), "o": "O", "oː": "O",
 "uː": "U", "u": "U", "ʊ": "U", "ʊɹ": ("U", "WQ"),
 "aɪ": ("A", "I"), "aʊ": ("A", "U"), "eɪ": ("E", "I"), "oʊ": ("O", "U"), "ɔɪ": ("O", "I"),
 "ə": "CDGK", "ɚ": "CDGK", "ɜː": "CDGK", "ɜ": "CDGK", "əl": ("CDGK", "L"),
 "m": "MBP", "b": "MBP", "p": "MBP",
 "f": "FV", "v": "FV",
 "θ": "TH", "ð": "TH",
 "l": "L", "ɫ": "L",
 "s": "SZ", "z": "SZ", "ʃ": "SZ", "ʒ": "SZ", "tʃ": "SZ", "dʒ": "SZ",
 "t": "CDGK", "d": "CDGK", "n": "CDGK", "k": "CDGK", "ɡ": "CDGK", "g": "CDGK", "ŋ": "CDGK",
 "ɾ": "CDGK", "ʔ": "CDGK", "h": "CDGK",
 "w": "WQ", "ʍ": "WQ", "ɹ": "WQ", "r": "WQ",
}
VOWELS = {"A", "E", "I", "O", "U"}
MUST = {"MBP", "FV"}          # visible closures that must never be dropped

def speech_segments(f):
    y, sr = librosa.load(f, sr=16000)
    r = librosa.feature.rms(y=y, frame_length=640, hop_length=160, center=True)[0]  # 10 ms hop
    db = 20 * np.log10(r + 1e-6)
    on = db > -42
    # close gaps < 90 ms (stop closures), drop blips < 40 ms
    segs, s = [], None
    for i, v in enumerate(np.append(on, False)):
        if v and s is None: s = i
        if not v and s is not None: segs.append([s * 0.01, i * 0.01]); s = None
    merged = []
    for sg in segs:
        if merged and sg[0] - merged[-1][1] < 0.09: merged[-1][1] = sg[1]
        else: merged.append(sg)
    return [sg for sg in merged if sg[1] - sg[0] >= 0.04], db, len(y) / 16000

def clip_track(f, ph):
    segs, db, dur = speech_segments(f)
    P = ph["phones"]
    pk = [((p["s"] + p["e"]) / 2) for p in P]
    # assign each phone to the speech segment nearest its peak
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
        st = a if (k == 0 or sid[k - 1] != sid[k]) else (P[k - 1]["e"] + p["s"]) / 2
        en = b if (k == len(P) - 1 or sid[k + 1] != sid[k]) else (p["e"] + P[k + 1]["s"]) / 2
        # CTC peaks lag onsets a little: bias interior boundaries earlier
        if not (k == 0 or sid[k - 1] != sid[k]): st -= 0.02
        if not (k == len(P) - 1 or sid[k + 1] != sid[k]): en -= 0.02
        st, en = max(st, a), min(max(en, st + 0.01), b)
        iv.append({"p": p["p"], "s": st, "e": en, "w": p["w"]})
    # speech-energy segments with no phoneme in them are breaths: lips slightly parted
    used = set(sid)
    breaths = [(a, b) for i, (a, b) in enumerate(segs) if i not in used]
    return iv, segs, db, dur, breaths

def build():
    ph = json.load(open("phones.json"))
    offs, t = [], INTRO
    events, words, segs_all = [], [], []
    durs = []
    for f in CLIPS:
        iv, segs, db, dur, breaths = clip_track(f, ph[f])
        events += [(t + a, t + b, "L", "breath") for a, b in breaths]
        for x in iv:
            v = PH.get(x["p"], "CDGK")
            if isinstance(v, tuple):
                mid = x["s"] + (x["e"] - x["s"]) * 0.55
                events += [(t + x["s"], t + mid, v[0], x["p"]), (t + mid, t + x["e"], v[1], x["p"])]
            else:
                events.append((t + x["s"], t + x["e"], v, x["p"]))
        for i, w in enumerate(ph[f]["words"]):
            ws = [x for x in iv if x["w"] == i]
            words.append({"w": w["w"], "s": t + ws[0]["s"], "e": t + ws[-1]["e"]})
        segs_all += [[t + a, t + b] for a, b in segs]
        offs.append(t); durs.append(dur)
        t += dur + GAP
    total = offs[-1] + durs[-1] + 2.2
    n = int(round(total * FPS))
    LEAD = 0.035  # show mouth shape ~1 frame before the sound (animation convention)
    track = []
    for i in range(n):
        tt = i / FPS + LEAD
        v = "REST"
        for (a, b, vv, p) in events:
            if a <= tt < b: v = vv; break
        track.append(v)
    # make sure every closure (M/B/P, F/V) is visible for >= 2 frames even if it fell between samples
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
    print("frames", n, "total", total, "offsets", offs)
    from collections import Counter; print(Counter(track))
    # print a word/viseme preview
    for w in words[:12]:
        a, b = int(w["s"] * FPS), int(w["e"] * FPS) + 1
        print(f"{w['w']:>12} {w['s']:6.2f} {' '.join(track[a:b])}")

if __name__ == "__main__":
    build()

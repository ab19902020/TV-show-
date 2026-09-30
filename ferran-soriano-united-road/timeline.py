"""Lay the five recordings end to end and time everything to the words: beats, phrases, caption cards, sighs.

The voice controls the timing. Inside a clip nothing is moved: every pause is the recording's own. Where one clip
ends and the next begins (beats 4|5, 9|10, 13|14, 17|18) the recordings have no pause of their own, so a pause the
length of the recording's pauses between beats (~0.65 s) goes in; clip 2 ends with its own second of room.
Speech is never sped up or cut.

-> build/timeline.json  (scene seconds everywhere)"""
import json, os, re, numpy as np, librosa
from script import BEATS, SAID

FPS = 30
LEAD = 0.35                  # picture before the first word: Soriano already there, hands clasped, eyes in the lens
# (file, silence before its first word, counted from the previous clip's last word)
CLIPS = [("src/audio1.mp3", None), ("src/audio2.mp3", 0.62), ("src/audio3.mp3", 0.98),
         ("src/audio4.mp3", 0.65), ("src/audio5.mp3", 0.69)]
HOLD = 1.1                   # after the last word: faint satisfied smile, mouth closed ... CUT
CARD = 1.0                   # end card: UNITED ROAD / SATIRE - FICTIONAL DIALOGUE

def norm_words(text):
    out = []
    for w in re.sub(r"[^a-z0-9' ]", " ", text.lower().replace("-", " ")).split():
        out += SAID.get(w, [w])
    return out

def gap_events(f, words, dur):
    """non-speech sounds between the words (sighs, breaths): runs above -48 dB of at least 0.12 s, with their peak"""
    y, sr = librosa.load(f, sr=16000)
    r = librosa.feature.rms(y=y, frame_length=640, hop_length=160, center=True)[0]
    db = 20 * np.log10(r + 1e-6)
    ev, prev = [], 0.0
    for w in words + [{"s": dur, "e": dur}]:
        a, b = prev, w["s"]
        prev = w["e"]
        if b - a <= 0.12: continue
        i0, i1 = int(a * 100), int(b * 100)
        on = np.append(db[i0:i1] > -48, False)
        s = None
        for k, v in enumerate(on):
            if v and s is None: s = k
            if not v and s is not None:
                if k - s >= 12:
                    pk = float(db[i0 + s:i0 + k].max())
                    ev.append({"s": (i0 + s) / 100, "e": (i0 + k) / 100, "peak": round(pk, 1),
                               "kind": "sigh" if pk > -30 else "breath"})
                s = None
    return ev

def build():
    ph = json.load(open("phones.json"))
    clips, words, phones, sounds = [], [], [], []
    t = LEAD
    for ci, (f, gap) in enumerate(CLIPS):
        P = ph[f]
        if gap is not None:
            last = words[-1]["e"]
            t = last + gap - P["words"][0]["s"]
        clips.append({"file": f, "at": round(t, 4), "dur": P["dur"]})
        base = len(words)
        for w in P["words"]:
            words.append({"w": w["w"], "s": round(t + w["s"], 4), "e": round(t + w["e"], 4), "clip": ci})
        for p in P["phones"]:
            phones.append({"p": p["p"], "s": round(t + p["s"], 4), "e": round(t + p["e"], 4), "w": base + p["w"]})
        for e in gap_events(f, P["words"], P["dur"]):
            sounds.append({**e, "s": round(t + e["s"], 3), "e": round(t + e["e"], 3), "clip": ci})
        t += P["dur"]
    speech_end = words[-1]["e"]
    # beats and phrases: match the script's words to the aligned words in order
    k = 0
    beats = []
    for n, phrases in BEATS:
        B = {"n": n, "phrases": []}
        for tag, text in phrases:
            ws = norm_words(text)
            got = [w["w"] for w in words[k:k + len(ws)]]
            assert got == ws, (n, text, got, ws)
            B["phrases"].append({"tag": tag, "text": text, "w0": k, "w1": k + len(ws) - 1,
                                 "s": words[k]["s"], "e": words[k + len(ws) - 1]["e"]})
            k += len(ws)
        B["s"], B["e"] = B["phrases"][0]["s"], B["phrases"][-1]["e"]
        beats.append(B)
    assert k == len(words), (k, len(words))
    # a beat owns the time from its first word (less the pause before it) to the next beat's
    for i, B in enumerate(beats):
        B["start"] = 0.0 if i == 0 else round((beats[i - 1]["e"] + B["s"]) / 2, 4)
    for i, B in enumerate(beats):
        B["end"] = beats[i + 1]["start"] if i + 1 < len(beats) else round(speech_end + HOLD, 4)
    total = speech_end + HOLD + CARD
    n = int(round(total * FPS))
    marks = {"speech_end": speech_end, "hold_end": speech_end + HOLD, "card": speech_end + HOLD, "end": n / FPS}
    tl = {"fps": FPS, "n": n, "total": n / FPS, "clips": clips, "words": words, "phones": phones, "beats": beats,
          "sounds": sounds, "marks": marks}
    os.makedirs("build", exist_ok=True)
    json.dump(tl, open("build/timeline.json", "w"), indent=1)
    print(f"{n} frames, {n / FPS:.2f} s; speech ends {speech_end:.2f}")
    for c in clips: print("  clip", c["file"], "at %.2f" % c["at"])
    for B in beats: print(f"  beat {B['n']:2d} {B['start']:7.2f}-{B['end']:7.2f}  {B['phrases'][0]['text'][:60]}")
    for s in sounds: print("  sound", s)

if __name__ == "__main__":
    build()

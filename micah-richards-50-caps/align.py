"""Word + phone timings for the original audio (one continuous 41.376 s recording).

The clip is cut into speaking turns at its pauses. Each turn is force-aligned (pocketsphinx) against its hand-corrected
transcript. The broadcast mix has laughter and fast speech under some lines, where the aligner can refuse; those turns fall
back to timing spread over the turn by phone count. Times are clip seconds. Speaker labels come from the original captions,
pitch (Gary ~117 Hz, Rooney ~118 Hz, Micah ~170 Hz) and who is moving their mouth in the original picture.

Output: phones.json {dur, turns:[{who, s, e, text, how, words:[{w,s,e,ph}], phones:[{p,w,s,e}]}]}"""
import json, re, numpy as np, librosa
from pocketsphinx import Decoder

AUDIO = "src/audio/rooney_micah_50_caps.mp3"
# (speaker, window start, window end, text)
# Who says what, read off the original BBC picture: the caption colours (Gary white, Micah yellow) and whose mouth moves in the
# wide two-shot (Micah, in profile, on "We did, didn't we? A couple of times"; Micah again on "Everything!"). In Micah's close-up
# his mouth stays shut through "pubs, clubs, what was it": that line is Alan Shearer's (the fourth pundit on the panel). Micah's voice sits higher (~170 Hz) than
# Gary's and Rooney's (~118 Hz). To change a speaker, edit the first field.
TURNS = [
    ("gary",   0.00,  4.85, "did you two ever bump into each other in manchester in those derby days and stuff"),
    ("micah",  4.85,  6.70, "we did didn't we a couple of times"),
    ("micah",  6.70,  9.30, "you were giving it the biggun in manchester back in those days"),
    ("shearer", 9.30, 11.90, "what was it pubs clubs what was it"),
    ("micah",  11.90, 12.45, "everything"),
    ("rooney", 13.10, 14.75, "i've actually seen micah"),
    ("rooney", 14.75, 16.85, "in wings chinese restaurant"),
    ("rooney", 16.85, 19.05, "and i was in there with my family"),
    ("rooney", 19.05, 20.60, "a quiet meal"),
    ("rooney", 20.60, 22.05, "micah comes in with"),
    ("rooney", 22.05, 23.30, "about twenty of his guys"),
    ("rooney", 23.30, 26.45, "walks in and they're celebrating"),
    ("rooney", 26.45, 27.65, "so i was thinking"),
    ("rooney", 27.65, 29.35, "what are they celebrating"),
    ("rooney", 29.35, 30.80, "it was micah has made his"),
    ("rooney", 30.80, 32.70, "fiftieth premier league appearance"),
    ("micah",  33.85, 35.55, "it's the premier league"),
    ("micah",  35.55, 36.95, "it's a big thing"),
    ("micah",  36.95, 38.05, "it was a big thing for me wayne"),
    ("micah",  38.50, 41.376, "why did you have to say that"),
]
EXTRA = {"biggun": "B IH G AH N", "wing's": "W IH NG Z", "micah": "M AY K AH", "premier": "P R IY M IH R"}
BEAMS = dict(beam=1e-120, wbeam=1e-100, pbeam=1e-120, maxhmmpf=-1)


def words_of(text):
    return re.sub(r"[^a-z' ]", " ", text.lower()).split()


def _decode(y, a, b, text, wide=False):
    seg = y[int(a * 16000):int(b * 16000)]
    pcm = (np.clip(seg, -1, 1) * 32767).astype(np.int16).tobytes()
    d = Decoder(samprate=16000, bestpath=False, loglevel="FATAL", **(BEAMS if wide else {}))
    for w, ph in EXTRA.items():
        if d.lookup_word(w) is None: d.add_word(w, ph, True)
    ws = words_of(text)
    d.set_align_text(" ".join(ws))
    d.start_utt(); d.process_raw(pcm, full_utt=True); d.end_utt()
    d.set_alignment()
    d.start_utt(); d.process_raw(pcm, full_utt=True); d.end_utt()
    words, phones = [], []
    for wseg in d.get_alignment():
        name = re.sub(r"\(\d+\)$", "", wseg.name)
        if name in ("<sil>", "<s>", "</s>", "[NOISE]"): continue
        i = len(words)
        ps = [(p.name, a + p.start / 100, a + (p.start + p.duration) / 100) for p in wseg]
        words.append({"w": name, "s": a + wseg.start / 100, "e": a + (wseg.start + wseg.duration) / 100, "ph": [p[0] for p in ps]})
        phones += [{"p": n, "w": i, "s": s, "e": e} for n, s, e in ps]
    assert [w["w"] for w in words] == ws, ([w["w"] for w in words], ws)
    return words, phones


def spread(y, a, b, text):
    """fallback: words spread over the voiced part of [a, b] by phone count (vowels weigh more)"""
    seg = y[int(a * 16000):int(b * 16000)]
    rms = librosa.feature.rms(y=seg, frame_length=400, hop_length=160)[0]
    on = np.nonzero(rms > rms.max() * 0.08)[0]
    s0, e0 = a + on[0] / 100, a + (on[-1] + 1) / 100
    dec = Decoder(samprate=16000, loglevel="FATAL")
    for w, ph in EXTRA.items():
        if dec.lookup_word(w) is None: dec.add_word(w, ph, True)
    ws = words_of(text)
    pl = [(dec.lookup_word(w) or "AH").split() for w in ws]
    vow = set("AA AE AH AO AW AY EH ER EY IH IY OW OY UH UW".split())
    wt = [[1.6 if re.sub(r"\d", "", p) in vow else 1.0 for p in ps] for ps in pl]
    tot = sum(sum(w) for w in wt)
    t = s0
    words, phones = [], []
    for i, (w, ps, ww) in enumerate(zip(ws, pl, wt)):
        w0 = t
        for p, x in zip(ps, ww):
            dt = (e0 - s0) * x / tot
            phones.append({"p": re.sub(r"\d", "", p), "w": i, "s": t, "e": t + dt}); t += dt
        words.append({"w": w, "s": w0, "e": t, "ph": [re.sub(r"\d", "", p) for p in ps]})
    return words, phones


def timed(y, a, b, text):
    for wide in (False, True):
        for pad in (0, 0.1, 0.2, 0.3, 0.45):
            try:
                return _decode(y, max(0, a - pad), min(len(y) / 16000, b + pad), text, wide) + ("pocketsphinx",)
            except (RuntimeError, AssertionError):
                continue
    return spread(y, a, b, text) + ("spread",)


if __name__ == "__main__":
    y, _ = librosa.load(AUDIO, sr=16000, mono=True)
    out = []
    for who, a, b, text in TURNS:
        words, phones, how = timed(y, a, b, text)
        out.append({"who": who, "s": a, "e": b, "text": text, "how": how, "words": words, "phones": phones})
        print(f"== {who} {a:.2f}-{b:.2f} [{how}]")
        print("  ".join(f"{w['w']}@{w['s']:.2f}-{w['e']:.2f}" for w in words))
    json.dump({"dur": len(y) / 16000, "turns": out}, open("phones.json", "w"), indent=1)

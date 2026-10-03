"""Word timings for the original recording (80.33 s), so every cue in direction.py can be keyed to a spoken word.

The recording is cut at its pauses; each piece was transcribed on its own (Whisper, transcribe.py) and hand-corrected here.
Each piece is force-aligned with pocketsphinx against its text; where the aligner refuses (fast speech, studio noise) the
words are spread over the voiced part of the piece by phone count. Times are recording seconds.
Output: words.json {dur, turns:[{who, s, e, text, how, words:[{w,s,e,ph}], phones:[{p,w,s,e}]}]}"""
import json, re, numpy as np, librosa
from pocketsphinx import Decoder

AUDIO = "src/audio/original.flac"
P, E = "presenter", "evra"
TURNS = [
    (P, 0.50, 7.80, "i know you did this on our podcast but you once went for lunch with him at manchester united thinking you were going to have a gentle lunch and it turned out to be a very competitive afternoon"),
    (E, 8.30, 10.45, "exactly i think we should stay at the training ground"),
    (E, 10.75, 11.15, "you know"),
    (E, 11.45, 13.55, "he said let's go and having a lunch after training"),
    (E, 14.15, 15.05, "go to his house"),
    (E, 15.35, 18.85, "you know it was few people on the table i look at it it was just some salad"),
    (E, 19.35, 20.35, "plain white chicken"),
    (E, 21.65, 23.30, "no juice just water"),
    (E, 23.85, 24.75, "so we have food"),
    (E, 25.00, 26.50, "quickly a lunch and after that"),
    (E, 26.75, 28.85, "he said let's go in the garden and play two touch"),
    (E, 29.25, 30.90, "i said cristiano we just finished"),
    (E, 31.15, 34.35, "so we go playing two touch after that let's go for swim"),
    (E, 35.05, 42.25, "after that let's have a sauna jacuzzi i was like cristiano why we didn't stay at the training so that's why i said cristiano deserve"),
    (E, 42.70, 44.45, "everything he got right now"),
    (E, 44.70, 47.10, "and also i saw the goal today you know i used to call him"),
    (E, 47.40, 47.95, "christian dior"),
    (E, 48.20, 49.15, "because of his playboy"),
    (E, 49.50, 52.10, "style and everything but i will say christian the warrior today"),
    (E, 52.40, 53.60, "so i'm really happy for him"),
    (E, 53.95, 56.70, "and he deserves it he deserves it because he works so hard and he's a machine"),
    (P, 57.00, 64.80, "and just quickly you said once he played table tennis with rio ferdinand who beat him and he was so close he was determined to beat him exactly and rio have to tell the truth"),
    (E, 65.55, 70.05, "rio beat him in front of everyone so we scream and cristiano was so angry"),
    (E, 70.35, 72.10, "he sent his cousin to buy a tennis table"),
    (E, 72.50, 73.60, "after two weeks he back"),
    (E, 73.85, 76.70, "and he beat cris he beat rio in front of all of us"),
    (E, 76.95, 80.05, "so that's cristiano ronaldo he don't want to lose any game"),
]
EXTRA = {"cristiano": "K R IH S T IY AA N OW", "jacuzzi": "JH AH K UW Z IY", "dior": "D IY AO R", "ferdinand": "F ER D IH N AE N D",
         "rio": "R IY OW", "podcast": "P AA D K AE S T", "playboy": "P L EY B OY", "cris": "K R IH S", "ronaldo": "R AH N AA L D OW"}
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
    tot = sum(sum(w) for w in wt); t = s0; words, phones = [], []
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
        if not text: continue
        words, phones, how = timed(y, a, b, text)
        out.append({"who": who, "s": a, "e": b, "text": text, "how": how, "words": words, "phones": phones})
        print(f"== {who} {a:.2f}-{b:.2f} [{how}]")
        print("  ".join(f"{w['w']}@{w['s']:.2f}" for w in words))
    json.dump({"dur": len(y) / 16000, "turns": out}, open("words.json", "w"), indent=1)

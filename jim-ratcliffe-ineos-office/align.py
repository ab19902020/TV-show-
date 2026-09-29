"""Word + phone forced alignment with pocketsphinx (CMU en-us acoustic model; ships inside the PyPI wheel).
Two passes per clip: word segmentation, then sub-word (phone) alignment of that word sequence."""
import json, re, numpy as np, librosa
from pocketsphinx import Decoder

EXTRA = {"yacht's": "Y AA T S", "licker": "L IH K ER"}          # words missing from cmudict

def words_of(text):
    return re.sub(r"[^a-z' ]", " ", text.lower().replace("-", " ")).split()

def align(f, text):
    y, _ = librosa.load(f, sr=16000, mono=True)
    pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
    d = Decoder(samprate=16000, bestpath=False, loglevel="FATAL")
    for w, ph in EXTRA.items(): d.add_word(w, ph, True)
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
        ps = [(p.name, p.start / 100, (p.start + p.duration) / 100) for p in wseg]
        words.append({"w": name, "s": wseg.start / 100, "e": (wseg.start + wseg.duration) / 100, "ph": [p[0] for p in ps]})
        phones += [{"p": n, "w": i, "s": s, "e": e} for n, s, e in ps]
    assert [w["w"] for w in words] == ws, ([w["w"] for w in words], ws)
    return {"dur": len(y) / 16000, "words": words, "phones": phones}

if __name__ == "__main__":
    tr = json.load(open("transcript.json"))
    out = {}
    for f, v in tr.items():
        out[f] = align(f, v["text"])
        for w in out[f]["words"]:
            print(f"{f[-10:]} {w['w']:>12} {w['s']:6.2f}-{w['e']:6.2f}  {' '.join(w['ph'])}")
    json.dump(out, open("phones.json", "w"), indent=1)

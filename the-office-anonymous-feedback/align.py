"""Force-align each character's recording to the script and cut it into the brief's line IDs -> phones.json.

Every line keeps its words and phones with times relative to its own start in the recording, plus the cut points
(`a0`, `a1`) in the recording, so the edit can place each line where the shot needs it.
"""
import json, re, numpy as np, librosa
from pocketsphinx import Decoder

CLIPS = {"brent": "src/brent.mp3", "gareth": "src/gareth.mp3", "tim": "src/tim.mp3"}
LINES = {
    "brent": [
        ("B01", "Little initiative. Anonymous suggestions. Anything you think management could improve."),
        ("B02", "People can be completely honest with me. That's the relationship. Obviously, if it's personal, "
                "that's not feedback. That's just having a go."),
        ("B03", "Right. First one. Fewer meetings. Fair enough. Constructive. Who put that?"),
        ("B04", "We aren't. I'm asking if anyone wants to take credit. It's a good suggestion."),
        ("B05", "Tell you what. Get everyone together after lunch. Discuss why people feel we're having too many meetings."),
        ("B06", "Not a meeting. A chance to speak freely."),
        ("B07", "Yes."),
        ("B08", "Yeah. Show of hands."),
    ],
    "gareth": [
        ("G01", "I've numbered the slips. And kept a list of who had which number."),
        ("G02", "No names on the actual slip."),
        ("G03", "Number four. Tim."),
        ("G04", "That'll need a separate slip."),
        ("G05", "Is it compulsory?"),
    ],
    "tim": [
        ("T01", "So what makes them anonymous?"),
        ("T02", "I thought we weren't meant to know."),
        ("T03", "Could you put stop Gareth keeping a list on mine as well?"),
        ("T04", "In a meeting?"),
        ("T05", "Can we vote on that anonymously?"),
    ],
}
EXTRA = {"gareth": "G EH R AH TH", "that'll": "DH AE T AH L", "aren't": "AA R N T"}


def words_of(text):
    return re.sub(r"[^a-z' ]", " ", text.lower().replace("-", " ")).split()


def align(y, text):
    pcm = (np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()
    d = Decoder(samprate=16000, bestpath=False, loglevel="FATAL")
    for w, ph in EXTRA.items():
        if d.lookup_word(w) is None:
            d.add_word(w, ph, True)
    ws = words_of(text)
    d.set_align_text(" ".join(ws))
    d.start_utt(); d.process_raw(pcm, full_utt=True); d.end_utt()
    d.set_alignment()
    d.start_utt(); d.process_raw(pcm, full_utt=True); d.end_utt()
    words = []
    for wseg in d.get_alignment():
        name = re.sub(r"\(\d+\)$", "", wseg.name)
        if name in ("<sil>", "<s>", "</s>", "[NOISE]"):
            continue
        words.append({"w": name, "s": wseg.start / 100, "e": (wseg.start + wseg.duration) / 100,
                      "ph": [(p.name, p.start / 100, (p.start + p.duration) / 100) for p in wseg]})
    assert [w["w"] for w in words] == ws, ([w["w"] for w in words], ws)
    return words


def voiced(y, sr=16000):
    """frame-level speech activity (10 ms), used to trim each line's cut to its real sound"""
    rms = librosa.feature.rms(y=y, frame_length=400, hop_length=160)[0]
    return rms, rms > max(0.006, np.percentile(rms, 30) * 1.5)


out = {}
for who, f in CLIPS.items():
    y, _ = librosa.load(f, sr=16000, mono=True)
    words = align(y, " ".join(t for _, t in LINES[who]))
    rms, act = voiced(y)
    i = 0
    starts = []
    for lid, text in LINES[who]:
        n = len(words_of(text))
        lw = words[i:i + n]
        i += n
        starts.append((lid, text, lw))
    for k, (lid, text, lw) in enumerate(starts):
        s, e = lw[0]["s"], lw[-1]["e"]
        prev_e = starts[k - 1][2][-1]["e"] if k else 0.0
        next_s = starts[k + 1][2][0]["s"] if k + 1 < len(starts) else len(y) / 16000
        # cut 0.35 s around the words, but never into the neighbouring line
        a0 = max(s - 0.35, (prev_e + s) / 2, 0.0)
        a1 = min(e + 0.35, (e + next_s) / 2, len(y) / 16000)
        out[lid] = {"who": who, "text": text, "a0": round(a0, 3), "a1": round(a1, 3),
                    "words": [{"w": w["w"], "s": round(w["s"] - a0, 3), "e": round(w["e"] - a0, 3)} for w in lw],
                    "phones": [{"p": p, "s": round(ps - a0, 3), "e": round(pe - a0, 3)}
                               for w in lw for p, ps, pe in w["ph"]]}
        print(f"{lid} {a0:6.2f}-{a1:6.2f} ({a1 - a0:4.2f}s)  " +
              " ".join(f"{w['w']}@{w['s'] - a0:.2f}" for w in lw))
json.dump(out, open("phones.json", "w"), indent=1)

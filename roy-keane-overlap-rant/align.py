"""Phoneme-level forced alignment: wav2vec2 espeak-phoneme CTC model + torchaudio forced_align."""
import json, re, numpy as np, torch, librosa
import torchaudio.functional as F
from transformers import AutoProcessor, Wav2Vec2ForCTC
torch.set_num_threads(4)
MID = "facebook/wav2vec2-lv-60-espeak-cv-ft"
proc = AutoProcessor.from_pretrained(MID); tok = proc.tokenizer
model = Wav2Vec2ForCTC.from_pretrained(MID).eval()
vocab = tok.get_vocab()
tr = json.load(open("transcript.json"))
out = {}
for f, segs in tr.items():
    wav, sr = librosa.load(f, sr=16000, mono=True)
    with torch.inference_mode():
        iv = proc(wav, sampling_rate=16000, return_tensors="pt").input_values
        logits = model(iv).logits
    lp = torch.log_softmax(logits, -1)
    T = lp.shape[1]; fdur = len(wav) / 16000 / T
    words = []
    for s in segs:
        for w in s["words"]:
            clean = re.sub(r"[^a-zA-Z']", "", w["w"]).lower()
            if clean: words.append({"w": clean, "ws": w["s"], "we": w["e"]})
    targets, owner = [], []
    for i, w in enumerate(words):
        ph = tok.phonemize(w["w"], phonemizer_lang="en-us").split()
        w["ph"] = []
        for p in ph:
            if p in vocab:
                targets.append(vocab[p]); owner.append(i); w["ph"].append(p)
            else:
                for c in p:
                    if c in vocab:
                        targets.append(vocab[c]); owner.append(i); w["ph"].append(c)
    tgt = torch.tensor([targets], dtype=torch.int32)
    ali, scores = F.forced_align(lp, tgt, blank=tok.pad_token_id)
    ali = ali[0].numpy(); sc = scores[0].exp().numpy()
    # token spans: frames where the aligned label == token index k (merge_tokens)
    spans = F.merge_tokens(torch.from_numpy(ali), torch.from_numpy(sc))
    assert len(spans) == len(targets), (len(spans), len(targets))
    inv = {v: k for k, v in vocab.items()}
    phones = []
    for k, sp in enumerate(spans):
        phones.append({"p": inv[targets[k]], "w": owner[k], "s": sp.start * fdur, "e": sp.end * fdur, "score": float(sp.score)})
    for i, w in enumerate(words):
        ps = [p for p in phones if p["w"] == i]
        w["as"], w["ae"] = ps[0]["s"], ps[-1]["e"]
    out[f] = {"dur": len(wav) / 16000, "words": words, "phones": phones}
    for w in words:
        print(f"{w['w']:>12} whisper {w['ws']:6.2f}-{w['we']:6.2f}  align {w['as']:6.2f}-{w['ae']:6.2f}  {' '.join(w['ph'])}")
json.dump(out, open("phones.json", "w"), indent=1)

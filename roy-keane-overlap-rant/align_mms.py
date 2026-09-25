import json, re, torch, librosa, torchaudio
from torchaudio.pipelines import MMS_FA as bundle
torch.set_num_threads(4)
model = bundle.get_model(); tokenizer = bundle.get_tokenizer(); aligner = bundle.get_aligner()
ph = json.load(open("phones.json"))
res = {}
for f, d in ph.items():
    wav, sr = librosa.load(f, sr=16000)
    w = torch.from_numpy(wav).unsqueeze(0)
    words = [x["w"].replace("'", "") for x in d["words"]]
    with torch.inference_mode():
        em, _ = model(w)
        spans = aligner(em[0], tokenizer(words))
    ratio = w.shape[1] / em.shape[1] / 16000
    res[f] = []
    for x, sp in zip(d["words"], spans):
        s, e = sp[0].start * ratio, sp[-1].end * ratio
        res[f].append({"w": x["w"], "s": s, "e": e, "chars": [(c.start*ratio, c.end*ratio) for c in sp]})
        print(f"{x['w']:>12} mms {s:6.2f}-{e:6.2f}   w2v-ph {x['as']:6.2f}-{x['ae']:6.2f}   diff {x['as']-s:+.2f}")
json.dump(res, open("mms.json", "w"), indent=1)

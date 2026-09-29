"""Split every raw voice clip at its pauses and transcribe each chunk (Whisper turbo via sherpa-onnx, offline)."""
import json, glob, os, numpy as np, librosa, sherpa_onnx
M = "models/sherpa-onnx-whisper-turbo/turbo-"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx",
                                                 tokens=M + "tokens.txt", language="en", task="transcribe", num_threads=4)
def chunks(y, sr=16000, hop=160, thr_db=-38, min_sil=0.28):
    rms = librosa.feature.rms(y=y, frame_length=640, hop_length=hop)[0]
    db = 20 * np.log10(rms + 1e-9); db -= db.max()
    voiced = db > thr_db
    segs, i, n = [], 0, len(voiced)
    while i < n:
        if voiced[i]:
            j = i
            while j < n and voiced[j]: j += 1
            segs.append([i, j]); i = j
        else: i += 1
    # merge segments separated by short silences
    out = []
    for s in segs:
        if out and (s[0] - out[-1][1]) * hop / sr < min_sil: out[-1][1] = s[1]
        else: out.append(s)
    return [(a * hop / sr, b * hop / sr) for a, b in out if (b - a) * hop / sr > 0.12]
res = {}
for f in sorted(glob.glob("audio_raw/show TV/*/*.mp3")):
    y, sr = librosa.load(f, sr=16000, mono=True)
    key = f.split("show TV/")[1]
    res[key] = []
    for a, b in chunks(y):
        seg = y[max(0, int((a - 0.05) * sr)):int((b + 0.05) * sr)]
        s = rec.create_stream(); s.accept_waveform(sr, np.concatenate([seg, np.zeros(sr // 2, np.float32)])); rec.decode_stream(s)
        res[key].append({"s": round(a, 3), "e": round(b, 3), "text": s.result.text.strip()})
        print(f"{key[:28]:28s} {a:6.2f}-{b:6.2f}  {s.result.text.strip()}", flush=True)
json.dump(res, open("chunks.json", "w"), indent=1)

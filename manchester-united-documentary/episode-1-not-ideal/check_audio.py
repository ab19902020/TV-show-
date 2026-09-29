"""Objective checks of the mix: (1) Whisper re-transcription of the mixed track around every line (is the dialogue
intelligible over music / ambience?), (2) a level plot with the scene marks -> build/audio_levels.png"""
import json, numpy as np, soundfile as sf, librosa, sherpa_onnx, cv2
TL = json.load(open("build/timeline.json"))
y, sr = sf.read("build/episode_audio.wav", dtype="float32")
mono = y.mean(1)
# level plot
hop = sr // 20
rms = np.array([np.sqrt(np.mean(mono[i:i + hop] ** 2) + 1e-10) for i in range(0, len(mono) - hop, hop)])
dbv = 20 * np.log10(rms)
W, H = 2400, 500
img = np.full((H, W, 3), 255, np.uint8)
for k, v in enumerate(dbv):
    x = int(k / len(dbv) * W); y0 = int(H - (v + 60) / 60 * H)
    cv2.line(img, (x, H), (x, max(0, y0)), (180, 120, 60), 1)
for e in TL["events"]:
    x0 = int(e["t"] / TL["total"] * W); x1 = int((e["t"] + e["dur"]) / TL["total"] * W)
    cv2.rectangle(img, (x0, 0), (x1, 12), (0, 0, 200), -1)
for k in ["music_cut", "chime", "s2", "black", "title", "s3", "dressing", "s4", "goal1_card", "goal2_card", "whistle"]:
    x = int(TL["marks"][k] / TL["total"] * W)
    cv2.line(img, (x, 0), (x, H), (0, 160, 0), 1); cv2.putText(img, k, (x + 2, 40 + (hash(k) % 5) * 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 120, 0), 1)
for d in (-10, -20, -30, -40, -50):
    yy = int(H - (d + 60) / 60 * H); cv2.line(img, (0, yy), (W, yy), (200, 200, 200), 1); cv2.putText(img, str(d), (2, yy - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (90, 90, 90), 1)
cv2.imwrite("build/audio_levels.png", img)
# intelligibility
M = "models/sherpa-onnx-whisper-turbo/turbo-"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx",
                                                 tokens=M + "tokens.txt", language="en", task="transcribe", num_threads=4)
L = json.load(open("build/lines.json"))
bad = 0
for e in TL["events"]:
    a, b = int((e["t"] - 0.1) * sr), int((e["t"] + e["dur"] + 0.1) * sr)
    seg = librosa.resample(mono[a:b], orig_sr=sr, target_sr=16000)
    s = rec.create_stream(); s.accept_waveform(16000, np.concatenate([np.zeros(4000, np.float32), seg, np.zeros(8000, np.float32)])); rec.decode_stream(s)
    got = s.result.text.strip()
    want = L[e["src"]]["text"]
    import re
    ww = set(re.sub(r"[^a-z' ]", " ", want.lower()).split()); gw = set(re.sub(r"[^a-z' ]", " ", got.lower()).split())
    ok = len(ww & gw) / max(1, len(ww))
    if ok < 0.6: bad += 1
    print(f"{e['t']:7.2f} {'OK ' if ok >= 0.6 else 'BAD'} {want:55s} | {got}", flush=True)
print("bad", bad)

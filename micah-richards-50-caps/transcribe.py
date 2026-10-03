"""Speech -> text (Whisper large-v3-turbo via sherpa-onnx; offline, CPU). Whisper reads at most 30 s, so the clip is read in
25 s windows; the hand-corrected words live in align.py TURNS."""
import json, sys, glob, librosa, sherpa_onnx
M = "models/sherpa-onnx-whisper-turbo/turbo-"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx",
                                                 tokens=M + "tokens.txt", language="en", task="transcribe", num_threads=4)
files = sys.argv[1:] or ["src/audio/rooney_micah_50_caps.mp3"]
out = {}
for f in files:
    y, sr = librosa.load(f, sr=16000, mono=True)
    parts = []
    for a in range(0, len(y), 16000 * 20):
        s = rec.create_stream(); s.accept_waveform(16000, y[a:a + 16000 * 25]); rec.decode_stream(s)
        parts.append(s.result.text.strip())
    out[f] = {"dur": len(y) / 16000, "text": " | ".join(parts)}
    print(f, round(len(y) / 16000, 2), out[f]["text"], flush=True)
json.dump(out, open("transcript.json", "w"), indent=1)

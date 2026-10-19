"""Speech -> text for the uploaded clips (Whisper large-v3-turbo via sherpa-onnx; runs offline on CPU)."""
import json, sys, glob, librosa, sherpa_onnx
M = "models/sherpa-onnx-whisper-turbo/turbo-"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx",
                                                 tokens=M + "tokens.txt", language="en", task="transcribe", num_threads=4)
files = sys.argv[1:] or sorted(glob.glob("src/audio*.mp3"))
out = {}
for f in files:
    y, sr = librosa.load(f, sr=16000, mono=True)
    s = rec.create_stream(); s.accept_waveform(16000, y); rec.decode_stream(s)
    out[f] = {"dur": len(y) / 16000, "text": s.result.text.strip()}
    print(f, round(len(y) / 16000, 2), out[f]["text"], flush=True)
json.dump(out, open("transcript.json", "w"), indent=1)

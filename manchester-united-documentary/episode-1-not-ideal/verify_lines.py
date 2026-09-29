"""Re-transcribe every cut line (Whisper) to prove each cut holds exactly its words."""
import json, numpy as np, librosa, sherpa_onnx
M = "models/sherpa-onnx-whisper-turbo/turbo-"
rec = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M + "encoder.int8.onnx", decoder=M + "decoder.int8.onnx",
                                                 tokens=M + "tokens.txt", language="en", task="transcribe", num_threads=2)
L = json.load(open("build/lines.json"))
for k, v in L.items():
    y, _ = librosa.load(f"build/lines/{k}.wav", sr=16000)
    s = rec.create_stream(); s.accept_waveform(16000, np.concatenate([np.zeros(4000, np.float32), y, np.zeros(8000, np.float32)])); rec.decode_stream(s)
    print(f"{k:22s} {v['dur']:5.2f}  want: {v['text']:60s} got: {s.result.text.strip()}", flush=True)

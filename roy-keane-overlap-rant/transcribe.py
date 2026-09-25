import json, sys
from faster_whisper import WhisperModel
m = WhisperModel("large-v3", device="cpu", compute_type="int8", cpu_threads=4)
out = {}
for f in ["src/audio1.mp3", "src/audio2.mp3"]:
    segs, info = m.transcribe(f, language="en", word_timestamps=True, beam_size=5, vad_filter=False)
    res = []
    for s in segs:
        res.append({"start": s.start, "end": s.end, "text": s.text,
                    "words": [{"w": w.word, "s": w.start, "e": w.end, "p": w.probability} for w in s.words]})
        print(f, f"{s.start:.2f}-{s.end:.2f}", s.text, flush=True)
    out[f] = res
json.dump(out, open("transcript.json", "w"), indent=1)

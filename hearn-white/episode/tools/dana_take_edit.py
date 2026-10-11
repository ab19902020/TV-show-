"""Dana's recording runs two lines together: "I've entered... premium towels" (9.35-10.79 s); "venues in worse ways" is
not in it. The words "I've entered" (9.35-9.77 s) belong to no usable line and bled into the cut of L010
("Premium towels"), so this writes voiceovers/01-dana-white-edit.wav: the delivered take, untouched except those
0.5 s faded to silence. The delivered mp3 stays as it came.
    python3 episodes/the-undercard/tools/dana_take_edit.py"""
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

VO = Path(__file__).resolve().parents[1] / "voiceovers"
y, sr = librosa.load(str(VO / "01-dana-white.mp3"), sr=48000, mono=True)
a, b, f = 9.24, 9.745, 0.012
g = np.ones(len(y), np.float32)
i0, i1, n = int(a * sr), int(b * sr), int(f * sr)
g[i0:i1] = 0.0
g[i0 - n:i0] = np.linspace(1, 0, n)
g[i1:i1 + n] = np.linspace(0, 1, n)
sf.write(str(VO / "01-dana-white-edit.wav"), y * g, sr, subtype="PCM_24")
print(VO / "01-dana-white-edit.wav")

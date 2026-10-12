"""Dana's voice-over came as two full takes. Take 1 (01-dana-white-take1.mp3) is the tighter read and is used for
every line except two, where take 2 is the cleaner read: L030 "It's boxing, Eddie." (take 1 says it twice) and L058
"I want a bigger bin for the rematch." (take 1's "bin" is heard as "bend"). This writes those two lines from take 2,
untouched, one file each (voiceovers/01-dana-white-take2-L030.wav, -L058.wav: a lone line is matched to the script
reliably), which lines.py reads ahead of take 1.
    python3 episodes/the-undercard/tools/dana_picks.py"""
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

VO = Path(__file__).resolve().parents[1] / "voiceovers"
PICKS = {"L030": (29.85, 31.75), "L058": (43.70, 45.95)}     # take 2, seconds (with their breath room)
y, sr = librosa.load(str(VO / "01-dana-white-take2.mp3"), sr=48000, mono=True)
pad = np.zeros(int(0.4 * sr), np.float32)
for lid, (a, b) in PICKS.items():
    seg = y[int(a * sr):int(b * sr)].copy()
    f = int(0.01 * sr)
    seg[:f] *= np.linspace(0, 1, f)
    seg[-f:] *= np.linspace(1, 0, f)
    out = VO / f"01-dana-white-take2-{lid}.wav"
    sf.write(str(out), np.concatenate([pad, seg, pad]), sr, subtype="PCM_24")
    print(out)

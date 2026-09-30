"""The sound: the five recordings at their places on the timeline (build/timeline.json), nothing else but a very
quiet room tone and one soft paper rustle on "A document has been published". No music, laugh track or effects.

The quietest whisper ("If a sponsor asks...") is lifted 4 dB so it survives a phone speaker; everything is then
brought to -16 LUFS integrated, -1 dBTP true peak, 48 kHz (two-pass ffmpeg loudnorm).

-> build/voice_raw.wav, soriano_audio.wav (48 kHz stereo, the film's full length)"""
import json, subprocess, numpy as np, librosa, soundfile as sf
import perf

SR = 48000

def main():
    tl = json.load(open("build/timeline.json"))
    n = int(round(tl["total"] * SR))
    mix = np.zeros(n, np.float32)
    for c in tl["clips"]:
        y, _ = librosa.load(c["file"], sr=SR, mono=True)
        y = y.copy()
        f = int(0.004 * SR); y[:f] *= np.linspace(0, 1, f); y[-f:] *= np.linspace(1, 0, f)   # no clicks at the cuts
        i = int(round(c["at"] * SR))
        mix[i:i + len(y)] += y[:n - i]
    # lift the quietest whisper
    t0, t1 = perf.W(17, "if", 3) - 0.1, perf.WE(17, "owner") + 0.35
    g = np.ones(n, np.float32)
    a, b = int(t0 * SR), int(t1 * SR); r = int(0.08 * SR)
    g[a:b] = 10 ** (4 / 20)
    g[a - r:a] = np.linspace(1, 10 ** (4 / 20), r); g[b:b + r] = np.linspace(10 ** (4 / 20), 1, r)
    mix *= g
    rng = np.random.default_rng(3)
    # room tone: soft, dark, steady (about -60 dBFS), fading out under the end card
    tone = rng.standard_normal(n).astype(np.float32)
    tone = librosa.effects.preemphasis(tone, coef=-0.97)          # tilt towards the lows
    tone *= 0.001 / (np.sqrt(np.mean(tone ** 2)) + 1e-9)
    card = int(tl["marks"]["card"] * SR)
    tone[card:] *= np.linspace(1, 0, n - card)
    mix += tone
    # a soft paper rustle: a few short bursts of band-passed noise
    for tt, kind in perf.SFX:
        if kind != "paper": continue
        L = int(0.55 * SR)
        burst = np.zeros(L, np.float32)
        for k in range(5):
            s = int((0.02 + 0.09 * k + rng.uniform(0, 0.03)) * SR); m = int(rng.uniform(0.04, 0.09) * SR)
            env = np.hanning(m).astype(np.float32) * rng.uniform(0.5, 1.0)
            burst[s:s + m] += rng.standard_normal(m).astype(np.float32) * env
        burst = librosa.effects.preemphasis(burst, coef=0.9)        # bright, papery
        burst *= 0.008 / (np.abs(burst).max() + 1e-9)
        i = int(tt * SR); mix[i:i + L] += burst[:n - i]
    sf.write("build/voice_raw.wav", mix, SR, subtype="FLOAT")
    # two-pass loudness normalisation
    p = subprocess.run(["ffmpeg", "-hide_banner", "-i", "build/voice_raw.wav", "-af",
                        "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = p.stderr[p.stderr.rindex("{"):p.stderr.rindex("}") + 1]
    m = json.loads(js)
    af = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:"
          f"linear=true,aresample=48000,alimiter=limit=0.89:level=false")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "build/voice_raw.wav", "-af", af, "-ac", "2",
                    "-ar", "48000", "soriano_audio.wav"], check=True)
    q = subprocess.run(["ffmpeg", "-hide_banner", "-i", "soriano_audio.wav", "-af",
                        "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True).stderr
    summ = q[q.rindex("Summary:"):]
    print(" ".join(summ.split()))

if __name__ == "__main__":
    main()

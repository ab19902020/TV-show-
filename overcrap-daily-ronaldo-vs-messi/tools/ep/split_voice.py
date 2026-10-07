"""Cut a voice clip that holds several consecutive lines into one file per line.

    python3 tools/ep/split_voice.py episode/raw/roy/Clony-AI-4v0Jv9v54BffO3oO.mp3 RK_01 RK_02 ... RK_08

The clip is force-aligned to the lines' text (in order); each line is cut from
just before its first word to just after its last, never past the middle of
the silence to the next line. Writes episode/audio/<ID>.mp3 and records the
source and cut times in audio/manifest.json (the renderer aligns the new files
on its next run).
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EP = os.path.join(ROOT, 'episode')
sys.path.insert(0, HERE)
sys.path.insert(0, EP)
import align as A        # noqa: E402
import script            # noqa: E402

LEAD, TAIL = 0.08, 0.18   # seconds kept before the first word and after the last


def split(src, ids):
    text = ' '.join(script.LINES[i] for i in ids)
    counts = [len(A.words_of(script.LINES[i])) for i in ids]
    with tempfile.TemporaryDirectory() as td:
        w16 = os.path.join(td, 'a.wav')
        A.to16k(src, w16)
        words = A.align(w16, text)
    if len(words) != sum(counts):
        sys.exit('alignment gave %d words for %d in the text' % (len(words), sum(counts)))
    dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0',
                                         src]).decode())
    spans, k = [], 0
    for n in counts:
        spans.append((words[k]['t0'], words[k + n - 1]['t1']))
        k += n
    # the boundary between two lines goes in the middle of the longest quiet stretch near the
    # aligned boundary (the aligner can end a word early or start the next late)
    import numpy as np
    import soundfile as sf
    with tempfile.TemporaryDirectory() as td:
        x, sr = sf.read(A.to16k(src, os.path.join(td, 'b.wav')), dtype='float32')
    hop = sr // 100
    rms = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, 'same')[::hop])
    quiet = rms < max(0.01, 0.06 * np.percentile(rms, 95))
    bounds = []
    for j in range(len(spans) - 1):
        c = (spans[j][1] + spans[j + 1][0]) / 2
        lo, hi = int(max(0, c - 0.7) * 100), int(min(dur, c + 0.7) * 100)
        best, k = None, lo
        while k < hi:
            if quiet[k]:
                e = k
                while e < len(quiet) and quiet[e]:
                    e += 1
                if best is None or e - k > best[1] - best[0]:
                    best = (k, e)
                k = e
            else:
                k += 1
        bounds.append((best[0] + best[1]) / 200 if best and best[1] - best[0] >= 6 else c)
    manual = getattr(script, 'CUTS', {}).get(os.path.basename(src))
    if manual:
        assert len(manual) == len(spans) - 1
        bounds = list(manual)
    edges = [0.0] + bounds + [dur]
    cuts = []
    for j in range(len(spans)):
        a, b = edges[j], edges[j + 1]
        loud = np.nonzero(~quiet[int(a * 100):int(b * 100)])[0]
        if len(loud):
            a2, b2 = a + loud[0] / 100 - LEAD, a + (loud[-1] + 1) / 100 + TAIL
            a, b = max(a, a2), min(b, b2)
        cuts.append((round(a, 3), round(b, 3)))
    mpath = os.path.join(EP, 'audio', 'manifest.json')
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {}
    for lid, (a, b) in zip(ids, cuts):
        out = os.path.join(EP, 'audio', lid + '.mp3')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-ss', '%.3f' % a, '-to', '%.3f' % b,
                        '-c:a', 'libmp3lame', '-q:a', '2', out], check=True)
        manifest[lid] = dict(source=os.path.basename(src), cut=[a, b])
        print('%s  %6.2f-%6.2f  %s' % (lid, a, b, script.LINES[lid]))
    with open(mpath, 'w') as f:
        json.dump(manifest, f, indent=1)


if __name__ == '__main__':
    split(sys.argv[1], sys.argv[2:])

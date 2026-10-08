"""Word and phone timing for The White Pelé, aligned stretch by stretch and checked by ear.

    PYTHONPATH=episodes/white-pele:. python3 -m film.align_song

The voice (build/stems/vocals.wav, Spleeter) is cut into the stretches the singer sings without a break (GROUPS: the
time span and the lyric lines it holds, worked out by listening with Whisper on short windows). Each stretch is
force-aligned against its own lines only (pocketsphinx), so a mistake can never drift into the next phrase. Every
line's aligned span is then heard again by Whisper and scored against the lyric (word error rate): the result is
written to build/alignment.json and ALIGNMENT.md lists every line with its score."""
import json
import re

import numpy as np

from film.analyse import WORDS
from studio.film import ep, song, voices
from studio.film.voices import words_of

# (start, end, first line, last line): the stretches, from the separated voice's pauses and short Whisper probes.
# A stretch the aligner can follow is aligned whole; the legato ones (no breath between lines) are split into one
# window per line (LINE_WINDOWS: from the breaths that are there, the lines' two-bar spacing, and choruses 1 and 2
# having the same internal timing), each aligned alone or, where singing defeats the aligner, its syllables snapped
# to the voice's own onsets (snap_line).
GROUPS = [
    (2.10, 5.20, 0, 0), (5.30, 11.10, 1, 2), (11.20, 14.10, 3, 3), (14.25, 16.20, 4, 4),
    (20.60, 25.10, 6, 6),
    (50.00, 62.30, 11, 14), (84.10, 85.60, 21, 21),
]
LINE_WINDOWS = {
    5: (17.15, 19.85),
    7: (37.85, 41.12), 8: (41.08, 43.95), 9: (43.80, 46.50), 10: (46.30, 49.85),
    15: (62.55, 68.05), 16: (67.95, 72.45), 17: (72.20, 75.30), 18: (75.20, 78.45), 19: (78.38, 81.10),
    20: (81.05, 83.95), 22: (87.00, 88.90), 23: (89.60, 94.50),
    24: (96.80, 99.60), 25: (99.60, 102.58), 26: (102.52, 104.75), 27: (104.60, 108.10),
    28: (108.25, 111.05), 29: (110.95, 113.75), 30: (113.85, 116.20), 31: (116.20, 119.95),
    32: (120.35, 123.30), 33: (123.10, 125.90), 34: (125.80, 128.80), 35: (128.80, 132.45),
    36: (132.90, 136.20), 37: (136.15, 139.32), 38: (139.32, 142.00), 39: (141.90, 145.25),
    40: (145.20, 147.30), 41: (147.60, 150.60), 42: (151.60, 156.30),
    43: (158.90, 163.20), 44: (163.20, 170.55),
}

# held names the aligner squeezes into a fraction of the note: their syllables go on the voice's onsets instead
FORCE_ONSETS = {22, 40}


def snap_line(v16, a, b, seg):
    """a sung line the aligner cannot follow: its syllables (by spelling) put on the voice's own syllable onsets
    inside [a, b], the strongest onsets first, in order -> [[s, e, word]]"""
    import librosa
    y = v16[int(a * 16000):int(b * 16000)]
    hop = 160
    env = librosa.onset.onset_strength(y=y, sr=16000, hop_length=hop)
    rms = librosa.feature.rms(y=y, frame_length=640, hop_length=hop)[0]
    db = 20 * np.log10(rms + 1e-9)
    voiced = db > np.percentile(db, 90) - 20
    vi = np.nonzero(voiced)[0]
    t0, t1 = (vi[0] * hop / 16000, vi[-1] * hop / 16000) if len(vi) else (0.0, b - a)
    syl = [max(1, len(re.findall(r"[aeiouy]+", w.rstrip("e") or w))) for w in seg]
    n = sum(syl)
    cand = librosa.onset.onset_detect(onset_envelope=env, sr=16000, hop_length=hop, units="time", backtrack=True)
    cand = [c for c in cand if t0 - 0.02 <= c <= t1 - 0.08]
    if len(cand) >= n:
        strength = {c: env[min(len(env) - 1, int(c * 16000 / hop))] for c in cand}
        keep = sorted(sorted(cand[1:], key=lambda c: -strength[c])[:n - 1])
        ons = [t0] + keep
    else:                                            # too few onsets: spread the rest evenly between them
        ons = list(np.linspace(t0, t1 - 0.12, n))
    out, k = [], 0
    for w, sy in zip(seg, syl):
        out.append([a + ons[k], None, w])
        k += sy
    for i in range(len(out)):
        out[i][1] = out[i + 1][0] - 0.02 if i + 1 < len(out) else a + t1
    return out


def refine(words, phones, v16):
    """every word's edges put on the voice itself: its start on the nearest syllable onset in the separated voice
    (within 0.12 s), and a word followed by a breath ends where the voice stops, so held notes and the closes after
    them land on the sound (the aligners place sung words loosely). A word's phones move with it (mapped from its
    old span into the new). Every word keeps at least MIN_WORD s and words never overlap"""
    import librosa
    MIN_WORD = 0.07
    hop = 160
    env = librosa.onset.onset_strength(y=v16, sr=16000, hop_length=hop)
    on = librosa.onset.onset_detect(onset_envelope=env, sr=16000, hop_length=hop, units="time", backtrack=True)
    rms = librosa.feature.rms(y=v16, frame_length=640, hop_length=hop)[0]
    db = 20 * np.log10(rms + 1e-9)
    ref = np.array([db[max(0, i - 100):i + 100].max() for i in range(0, len(db))])
    voiced = db > ref - 22
    words = sorted([list(w) for w in words])
    old = [(w[0], w[1]) for w in words]
    for w in words:
        near = on[np.abs(on - w[0]) <= 0.12]
        if len(near):
            w[0] = float(near[np.argmin(np.abs(near - w[0]))])
    for i in range(1, len(words)):                       # starts in order, each word room to exist
        words[i][0] = max(words[i][0], words[i - 1][0] + MIN_WORD)
    for i, w in enumerate(words):
        nxt = words[i + 1][0] if i + 1 < len(words) else w[1] + 1.0
        j = int(w[0] * 100) + 3                          # where the voice stops after this word (a breath)
        while j < len(voiced) and j < int(nxt * 100) and voiced[j]:
            j += 1
        stop = j / 100
        end = stop if stop < nxt - 0.08 else max(w[1], old[i][1])
        w[1] = min(max(end, w[0] + MIN_WORD), nxt - 0.01) if i + 1 < len(words) else max(end, w[0] + MIN_WORD)
    out_p = []
    for p_, ps, pe in phones:                            # each phone into its word's new span
        mid = (ps + pe) / 2
        k = next((i for i, (a, b) in enumerate(old) if a - 0.02 <= mid <= b + 0.02), None)
        if k is None:
            continue
        (a0, b0), (a1, b1) = old[k], (words[k][0], words[k][1])
        f = (b1 - a1) / max(1e-3, b0 - a0)
        out_p.append([p_, round(a1 + (max(ps, a0) - a0) * f, 3), round(a1 + (min(pe, b0) - a0) * f, 3)])
    for w in words:
        w[0], w[1] = round(w[0], 3), round(w[1], 3)
    return words, out_p


def main():
    import librosa
    from studio.episode.asr import recognizer, wer
    ep.use("white-pele")
    voices.EXTRA.update(WORDS)
    lines = song.lyric_lines(ep.DIR / "lyrics.md")
    v16, _ = librosa.load(str(ep.path("stems", "vocals.wav")), sr=16000, mono=True)
    words, phones, how = [], [], {}
    for k, (a, b) in sorted(LINE_WINDOWS.items()):
        seg = [song._norm(w) for w in words_of(lines[k])]
        try:
            if k in FORCE_ONSETS:
                raise ValueError("onsets")
            al = voices.align_samples(v16[int(a * 16000):int(b * 16000)], seg)
            assert len(al["words"]) == len(seg)
            words.extend([round(a + w["s"], 3), round(a + w["e"], 3), seg[i], k] for i, w in enumerate(al["words"]))
            phones.extend([p["p"], round(a + p["s"], 3), round(a + p["e"], 3)] for p in al["phones"])
            how[k] = "aligned"
        except Exception:
            words.extend([round(s_, 3), round(e_, 3), w, k] for s_, e_, w in snap_line(v16, a, b, seg))
            how[k] = "onsets"
    for a, b, l0, l1 in GROUPS:
        seg, lid = [], []
        for k in range(l0, l1 + 1):
            for w in words_of(lines[k]):
                seg.append(song._norm(w))
                lid.append(k)
        al = voices.align_samples(v16[int(a * 16000):int(b * 16000)], seg)
        if len(al["words"]) != len(seg):
            raise SystemExit(f"stretch {a}-{b}: aligned {len(al['words'])} of {len(seg)} words")
        for k, w in enumerate(al["words"]):
            words.append([round(a + w["s"], 3), round(a + w["e"], 3), seg[k], lid[k]])
            how[lid[k]] = "aligned"
        phones.extend([p["p"], round(a + p["s"], 3), round(a + p["e"], 3)] for p in al["phones"])

    def hear(s, e):
        x = np.concatenate([np.zeros(4000, np.float32), v16[int(s * 16000):int(e * 16000)], np.zeros(8000, np.float32)])
        st = recognizer().create_stream()
        st.accept_waveform(16000, x)
        recognizer().decode_stream(st)
        return st.result.text.strip()

    words, phones = refine(words, phones, v16)
    phones.sort(key=lambda p: p[1])
    out_lines, report = [], []
    for k, ln in enumerate(lines):
        ws = [w for w in words if w[3] == k]
        s, e = ws[0][0], ws[-1][1]
        out_lines.append([s, e, ln])
        heard = hear(max(0, s - 0.08), e + 0.12)
        report.append(dict(line=k, start=s, end=e, text=ln, heard=heard, wer=round(wer(ln, heard), 2), how=how[k]))
        print(f"{k:2d} {how[k]:7s} {s:7.2f} {e:7.2f} wer {report[-1]['wer']:.2f}  {ln}  | {heard}", flush=True)
    ep.path("alignment.json").write_text(json.dumps(dict(words=words, lines=out_lines, phones=phones,
                                                         report=report), indent=1))


if __name__ == "__main__":
    main()

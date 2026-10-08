"""song-timing.json: the song analysis (film/analyse.py -> build/song.json: beats, bars, drum hits, loudness, the
voice's own mouth shapes) with the checked lyric timing (film/align_song.py -> build/alignment.json) in place of
the analyser's own, and the lead singer's mouth track rebuilt from it.

    PYTHONPATH=episodes/white-pele:. python3 -m film.timing

The engine reads song-timing.json in preference to build/song.json (studio.film.ep.song_path), so the checked
timing is what the film uses; commit it."""
import json

import numpy as np

from studio.film import ep, song


# the instrumental after chorus 1: the separated voice holds only the lead guitar's bleed there (-35 dB against the
# band's -17 dB, a steady A at 442 Hz), which the mouth must not sing
MUTE = [(25.3, 37.7)]
TARGET = 2                       # frames the mouth leads the voice
SECTIONS = [(0.0, 30.0, "chorus 1"), (30.0, 68.3, "verse 1"), (68.3, 95.5, "chorus 2"), (95.5, 132.6, "verse 2"),
            (132.6, 177.6, "chorus 3")]


def lead_of(lead, voc, a, b):
    """how many frames the mouth's opening leads the voice's loudness inside [a, b] (cross-correlation, -6..6)"""
    n = len(lead)
    vis = np.array([0.0 if v in ("REST", "MBP") else 1.0 for v, _ in lead])
    on = (voc > np.median(voc[vis > 0]) - 12).astype(np.float32)
    f0, f1 = int(a * 30), min(n, int(b * 30))
    cc = {lag: float(np.corrcoef(vis[f0:f1], np.roll(on, -lag)[f0:f1])[0, 1]) for lag in range(-6, 7)}
    return max(cc, key=cc.get)


def main():
    ep.use("white-pele")
    S = json.loads(ep.path("song.json").read_text())
    A = json.loads(ep.path("alignment.json").read_text())
    S["words"], S["lines"], S["phones"] = A["words"], A["lines"], A["phones"]
    n = len(S["sing"])
    S["lead"] = song.lead_track(S, n)
    S["source"] = dict(song="song.mp3 (sha256 6d4c6237...e1c4)", analysis="film/analyse.py",
                       lyrics="film/align_song.py, checked line by line (ALIGNMENT.md)")
    # the mouth leads the voice by TARGET frames in every section, as an animator leads the sound: measured (the
    # mouth's opening against the voice's loudness) and the section's mouth track moved to match. The section
    # boundaries sit in the singer's breaths, so nothing is cut
    voc = np.asarray(S["vocal"], np.float32)[:n]
    S["lead_shift"] = {}
    for a, b, name in SECTIONS:
        lag0 = lead_of(S["lead"], voc, a, b)
        shift = int(np.clip(TARGET - lag0, -3, 3))
        f0, f1 = int(a * 30), min(n, int(b * 30))
        seg = S["lead"][f0:f1]
        if shift > 0:                                   # earlier
            seg = seg[shift:] + [["REST", 1.0]] * shift
        elif shift < 0:
            seg = [["REST", 1.0]] * -shift + seg[:shift]
        S["lead"][f0:f1] = seg
        S["lead_shift"][name] = shift
        print(f"{name:10s} {a:6.1f}-{b:6.1f}  mouth led the voice by {lag0:+d} frames, moved {shift:+d} -> "
              f"{lead_of(S['lead'], voc, a, b):+d}")
    for a, b in MUTE:
        for f in range(int(a * 30), min(n, int(b * 30))):
            S["lead"][f] = ["REST", 1.0]
    (ep.DIR / "song-timing.json").write_text(json.dumps(S))
    print(ep.DIR / "song-timing.json")


if __name__ == "__main__":
    main()

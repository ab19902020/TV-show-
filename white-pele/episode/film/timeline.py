"""The song's own timeline (song-timing.json, the checked timing): every bar and lyric line as marks. The film is
exactly as long as the song: it starts on the first sample and ends on the last (no title card, no tail)."""
import json

from studio.film import ep

S = json.loads(ep.song_path().read_text())
DOWN = S["downbeats"]


def bar(n):
    """the time of bar n's downbeat (bar 0 = 3.44 s; the first sung word is a pickup before it). Past the last
    downbeat the bars run on at the song's tempo; bar -1 is the pickup bar"""
    if 0 <= n < len(DOWN):
        return DOWN[n]
    per = (DOWN[-1] - DOWN[0]) / (len(DOWN) - 1)
    return DOWN[-1] + (n - len(DOWN) + 1) * per if n >= len(DOWN) else DOWN[0] + n * per


def b(n, frac=0.0):
    """a time inside bar n (frac of the bar)"""
    return bar(n) + frac * (bar(n + 1) - bar(n))


LINES = S["lines"]
WORDS = S["words"]
marks = {f"bar{n}": round(x, 3) for n, x in enumerate(DOWN)}
marks.update({f"line{n}": round(l[0], 3) for n, l in enumerate(LINES)})
marks.update({f"line{n}_end": round(l[1], 3) for n, l in enumerate(LINES)})
SONG_END = 177.52                                      # the decoded song's length (48 kHz: 8,520,960 samples)
marks["song_end"] = SONG_END
TL = dict(total=SONG_END, lines={}, marks=marks)


def word(line, k=0):
    """(start, end) of the k-th word of a lyric line"""
    ws = [w for w in WORDS if w[3] == line]
    return ws[k][0], ws[k][1]

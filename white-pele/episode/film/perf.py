"""Who sings what, how everyone moves, and the faces: keyed to the song's bars (timeline.bar) and lyric lines.

Singing (the song's checked mouth track, song-timing.json "lead", two frames ahead of the voice):
  Rooney sings every note: the lead vocal is his. Rio and Goldbridge belt the choruses and the outro along with him
  (off mic, a little less open); every supporter in a crowd shot sings every line back; the band joins the choruses
  off mic. Keane never sings. Nobody mouths in the instrumental (the separated voice there is the guitar's bleed,
  muted in song-timing.json) and every mouth closes in the singer's breaths.
Playing: the drums come in at bar 8 (15.2 s), exactly where the recording's drums do, and stop for the breakdown
  (bars 80-88), as the bass does; the guitar plays throughout.
Dancing: an arc. Restrained in the first chorus (Rooney sways, grins into the lens), a walk through the verses,
  bigger in chorus 2, everything in chorus 3 and the outro. Each has their own way: Rio a long-limbed skank,
  Goldbridge jumping far too high, the band as they played United Road. Keane stands still with his arms folded,
  breathing heavily, and the one thing that moves is a foot (direction.py's tap)."""
import zlib

from studio.film.perf import Performance
from studio.film.stage import Groove, sing
from film.direction import CROWDS, SHOTS
from film.timeline import LINES, TL, b, bar

END = TL["total"]
CROWD = sorted({p["who"] for v in CROWDS.values() for p in v})
WHO = ["rooney", "rio", "mark", "gary", "roy", "maguire", "sesko", "cunha", "kid"] + CROWD


def L(n):
    return LINES[n][0]


def Le(n):
    return LINES[n][1]


def sec(a, z):
    """bars a..z as times (past the last bar: the end of the film)"""
    return bar(a), (bar(z) if z < 116 else END)


CH1, V1, CH2, V2, BRK, CH3, OUT, TAIL = ((-1, 15), (23, 47), (47, 63), (63, 80), (80, 88), (88, 106), (106, 115),
                                        (115, 117))
CH1_FULL = (8, 15)                                       # the drums in: the room wakes up

# ---------------------------------------------------------------- playing
PLAYS = {"maguire": [(bar(8) - 0.05, bar(80)), (bar(88) - 0.05, 173.7)],
         "sesko": [(0.0, 173.7)],
         "cunha": [(bar(-1), bar(80)), (bar(88) - 0.05, 173.7)]}


# ---------------------------------------------------------------- dancing
def d(section, move, amount):
    return (*sec(*section), move, amount)


DANCE = {
    "rooney": [d(CH1, "sway", 0.55), d(CH1_FULL, "bounce", 0.55), d(V1, "bounce", 0.5), d(CH2, "bounce", 0.9),
               d(CH2, "hop", 0.35), d(V2, "strut", 0.8), d(V2, "bounce", 0.45), d(BRK, "sway", 0.7),
               d(CH3, "jump", 0.7), d(OUT, "jump", 0.9), d(TAIL, "bounce", 0.6)],
    "rio": [d(CH1, "nod", 0.6), d(CH1_FULL, "skank", 0.9), d(V1, "skank", 0.7), d(CH2, "skank", 1.1),
            d(CH2, "hop2", 0.5), d(V2, "skank", 0.9), d(BRK, "sway", 0.8), d(CH3, "jump", 1.0), d(CH3, "twist", 0.6),
            d(OUT, "jump", 1.1), d(TAIL, "bounce", 0.8)],
    "mark": [d(CH1, "bounce", 0.9), d(CH1_FULL, "pogo", 0.8), d(V1, "pump", 0.8), d(CH2, "pogo", 1.1),
             d(V2, "bounce", 1.0), d(BRK, "sway", 0.9), d(CH3, "pogo", 1.3), d(OUT, "pogo", 1.35), d(TAIL, "pump", 0.8)],
    "gary": [d(V1, "awkward", 0.5)],
    "roy": [d(CH3, "nod", 0.18)],
    "sesko": [d((-1, 80), "rock", 0.9), d(CH2, "hop", 0.4), d(BRK, "sway", 0.6), d((88, 117), "rock", 1.2)],
    "cunha": [d((-1, 80), "skank", 0.85), d(BRK, "sway", 0.5), d((88, 117), "jump", 0.7)],
    "maguire": [d((8, 80), "headbang", 0.6), d((88, 117), "headbang", 0.8)],
}
for c in CROWD:                                           # the supporters: every chorus, each their own way
    k = zlib.crc32(c.encode()) % 4
    verse_m, chorus_m = [("bounce", "jump"), ("sway", "pogo"), ("nod", "hop"), ("skank", "jump")][k]
    DANCE[c] = [d(CH1, verse_m, 0.6), d(CH2, chorus_m, 1.0), d(V2, verse_m, 0.8), d(BRK, "wave", 1.0),
                d(CH3, chorus_m, 1.2), d(OUT, chorus_m, 1.25)]
STYLE = {"rooney": dict(late=0.0, lag=0.06), "rio": dict(late=0.04, lag=0.09), "mark": dict(late=-0.02, lag=0.05),
         "roy": dict(breathe=1.6, lag=0.08), "gary": dict(breathe=0.8, lag=0.05), "sesko": dict(late=0.045, lag=0.10),
         "cunha": dict(late=0.025, lag=0.08), "maguire": dict(late=0.0, lag=0.05), "kid": dict(breathe=1.0)}
GROOVE = Groove(DANCE, style=STYLE)

# ---------------------------------------------------------------- faces
BASE = dict(rooney=(0.2, 0.5), rio=(0.35, 0.7), mark=(0.6, 0.7), gary=(-0.3, -0.1), roy=(-0.8, -0.5),
            maguire=(0.0, 0.3), sesko=(-0.1, 0.45), cunha=(0.25, 0.6), kid=(0.3, 0.6))
for c in CROWD:
    BASE[c] = (0.4, 0.7)
EXPR = {
    "rooney": [(bar(8), bar(15), 0.35, 0.75, 0.6), (bar(47), bar(63), 0.45, 0.8, 0.5),
               (bar(80), bar(88), 0.55, 0.45, 0.6), (bar(88), END, 0.5, 0.95, 0.5)],
    "rio": [(b(1, 0.2), b(2), 0.85, 0.95, 0.25)],              # the delighted grin when he hears it
    "roy": [(b(99, 0.6), b(100), -0.5, -0.2, 0.2)],            # the clap: almost a softening
}
GAZE = {"roy": [(b(16), b(17), "down")]}                       # judging the technique
LEFT, RIGHT = ("dir", -0.6, 0.04, -0.3), ("dir", 0.6, 0.04, 0.3)
GLANCE = {
    "rooney": [(L(14) + 1.6, L(14) + 3.2, LEFT),               # "...we lose our minds that day": to Rio, a smile
               (b(82, 0.4), b(83, 0.2), ("dir", 0.5, -0.5, 0.2)),   # the trophy over his head
               (175.6, 177.5, RIGHT)],                          # at Keane, broom in hand
    "rio": [(b(74, 0.1), b(74, 0.9), "roy"),                    # he spots the foot...
            (b(75, 0.0), b(75, 0.5), LEFT)],                    # ...and looks away, innocent
    "roy": [(b(74, 0.85), b(75, 0.45), "rio")],                 # the glare
    "mark": [(b(82, 0.3), b(83, 0.8), ("dir", -0.4, -0.3, -0.2))],
}
LIFE = {"roy": dict(eyes=0.4, head=0.3), "kid": dict(eyes=0.5)}
SHUT = {"rooney": [(b(86, 0.5), b(87, 0.2))]}
NOBLINK = {"rooney": [(b(5), b(7))], "mark": [(b(82), b(84))]}      # his small-eyed cheer drawing: no blinks

PERF = Performance(TL, {}, WHO, {w: w for w in WHO}, {}, lambda lid: None, base=BASE, gaze=GAZE, expr=EXPR,
                   rest_target={w: "cam" for w in WHO}, cuts=[s["t"] for s in SHOTS], shut=SHUT, noblink=NOBLINK)

ALL = [(L(0) - 0.15, Le(len(LINES) - 1) + 0.3)]
CHORUS_SPANS = [(L(0) - 0.15, Le(6) + 0.3), (L(17) - 0.15, Le(23) + 0.3), (L(36) - 0.15, Le(44) + 0.3)]
sing(PERF, "rooney", [(0.0, END)], gain=1.1)
for _w in ("rio", "mark"):
    sing(PERF, _w, CHORUS_SPANS, gain=0.85)
for _w in ("sesko", "cunha", "maguire"):
    sing(PERF, _w, CHORUS_SPANS, gain=0.7)
for _c in CROWD:
    sing(PERF, _c, ALL, gain=0.8)
    sing(PERF, _c, CHORUS_SPANS, gain=1.0)

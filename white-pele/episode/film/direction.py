"""The shot list of The White Pelé: Rooney's matchday takeover, cut on the song's bars (timeline.b(n, frac): bar n,
a fraction into it; bar 0 is at 3.44 s, the first sung word a pickup before it) and its lyric lines.

  chorus 1 (bars -1..15)   the United pub: a ball rolls to a stop against Rooney's trainer and the camera tilts up to
                           find him already singing; Rio notices; the room (Goldbridge's scarf, Keane's folded arms);
                           the drums come in; Rio rallies the room; the first scarves go up
  instrumental (15..23)    toe-taps on the stage; a scarf wipes into the memory: the younger Rooney in a red 10
                           receives, runs, strikes, scores, and spreads his arms
  verse 1 (23..47)         the match cut back to the pub; out into the street ("From Croxteth streets"), the
                           procession, the mural, Goldbridge posing on Sir Matt Busby Way, Old Trafford ahead, the
                           stadium at dusk
  chorus 2 (47..63)        the tunnel; the pitch, the stage and the crowd; Rooney takes the front of the stage
  verse 2 (63..80)         the bicycle kick in silhouette under the floodlights ("City stunned by that bicycle
                           strike"); the scarves sweep ("Old Trafford shaking left and right"); Keane's foot tap
  breakdown (80..88)       the drums stop, a follow spot, phones up; Goldbridge's tiny trophy ("worth more than gold")
  chorus 3 (88..106)       the crowd in layers; everybody on bar 95; Keane's one clap on the crash; the scarf wave
  outro (106..115)         "White Pele": confetti at the last peak, the held smile
  tail (115..)             the closing stabs, then Keane hands Rooney a broom; Rio laughs

Plates (props.plate_image): F/FC the pub stage, PUB the room seen from the stage, ST the street at dusk, MW the
mural wall, EXT/EXT2 the stadium outside, TUN/TUNP the tunnel, OT/OTS the stadium at night (OTS with the stage on
the pitch), MEM the memory's sunny ground. Actors are dicts (film/actors.py), placed by their feet and height in
plate px. Every cut lands half a frame early, on the frame nearest its beat (as United Road's)."""
import math

import numpy as np

from studio.film.shots import finish, shot_at as _shot_at, stage
from film import actors
from film.timeline import LINES, SONG_END, TL, b, bar

actors.install()

PLATES = {"F": "pub-and-restaurant/united-pub-stage", "FC": "pub-and-restaurant/united-pub-stage-crowd",
          "PUB": "pub-and-restaurant/pub", "S": "pub-and-restaurant/united-pub-stage-side-crowd",
          "ST": "street/manchester-matchday", "MW": "street/manchester-matchday",
          "EXT": "stadiums/old-trafford-exterior-dusk", "EXT2": "stadiums/old-trafford-exterior-red-lit",
          "TUN": "stadiums/tunnel-corridor", "TUNP": "stadiums/tunnel-to-pitch",
          "OT": "stadiums/old-trafford", "OTS": "stadiums/old-trafford", "MEM": "stadiums/red-seated"}


def L(n):
    return LINES[n][0]


def Le(n):
    return LINES[n][1]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def stand(x, y0, y1, w=2.2):
    return rect(x - w, y0, x + w, y1)


# ---------------------------------------------------------------- the pub stage (United Road's measurements)
KIT = [
    [(717, 333), (735, 326), (760, 323), (785, 329), (805, 341), (809, 352), (795, 358), (770, 356), (745, 350), (724, 343)],
    [(741, 393), (760, 386), (800, 386), (813, 393), (813, 463), (800, 471), (752, 471), (741, 463)],
    [(883, 359), (895, 353), (935, 353), (946, 360), (946, 404), (935, 413), (895, 413), (883, 405)],
    [(904, 401), (960, 397), (967, 405), (967, 423), (955, 429), (912, 429), (904, 421)],
    [(925, 330), (945, 319), (975, 315), (1000, 319), (1011, 327), (995, 338), (965, 344), (940, 343)],
    [(959, 372), (990, 365), (1031, 369), (1036, 377), (1010, 385), (975, 386), (959, 380)],
    stand(742, 355, 500), stand(965, 342, 500), stand(990, 384, 500), stand(948, 428, 500),
    [(688, 520), (742, 470), (790, 518), (782, 522), (742, 482), (696, 524)],
    [(915, 515), (965, 468), (1012, 512), (1004, 516), (965, 480), (922, 518)],
    [(955, 512), (990, 470), (1030, 508), (1022, 512), (990, 482), (962, 515)],
    [(850 + 62 * math.cos(a / 20 * 2 * math.pi), 455 + 62 * math.sin(a / 20 * 2 * math.pi)) for a in range(20)],
]
MONITORS = [[(372, 556), (398, 500), (470, 486), (512, 490), (529, 540), (521, 561), (470, 567), (380, 567)],
            [(1145, 541), (1166, 490), (1212, 485), (1281, 491), (1301, 555), (1291, 567), (1200, 567), (1150, 561)]]
OCCL = {"F": {"kit": KIT, "monitors": MONITORS}, "FC": {"kit": KIT, "monitors": MONITORS}}

RED, WHITE, AMBER = (1.0, 0.16, 0.10), (1.0, 0.92, 0.82), (1.0, 0.55, 0.15)
BLUE, MAGENTA, CYAN = (0.20, 0.42, 1.0), (1.0, 0.18, 0.66), (0.12, 0.95, 1.0)
PUB_LAMPS = [
    dict(at=(527, 112), aim=75, colors=[WHITE, RED, AMBER, RED], swing=18, power=0.20),
    dict(at=(672, 112), aim=100, colors=[RED, AMBER, WHITE, RED], swing=20, power=0.20),
    dict(at=(836, 112), aim=90, colors=[WHITE, RED, AMBER, WHITE], swing=22, power=0.22),
    dict(at=(1002, 112), aim=80, colors=[AMBER, WHITE, RED, RED], swing=20, power=0.20),
    dict(at=(1143, 112), aim=105, colors=[RED, WHITE, AMBER, RED], swing=18, power=0.20)]
OT_LAMPS = [dict(at=(540 + k * 590 / 6, 334), aim=90 + (k - 3) * 9, colors=[WHITE, RED, WHITE, RED, MAGENTA, WHITE],
                 swing=26, power=0.26) for k in range(7)]
LAMPS = {"F": PUB_LAMPS, "FC": PUB_LAMPS, "OTS": OT_LAMPS}

# the drummer's kit relative to his feet and height (measured on the pub stage: Maguire at (880, 516), h 322), so he
# plays the same kit anywhere: film/actors.py turns these into plate px for each placement
KIT_REL = {k: ((x - 880) / 322.0, (y - 516) / 322.0) for k, (x, y) in
           {"hat": (995, 372), "snare": (935, 402), "tom": (778, 394), "crash_l": (765, 338),
            "crash_r": (968, 326)}.items()}
DRUMS = dict(grips={"R": (846, 388), "L": (916, 386)}, len=0.31, h=322, fist=None,
             drums={"hat": (995, 372), "snare": (935, 402), "tom": (778, 394), "crash_l": (765, 338),
                    "crash_r": (968, 326)})


# ---------------------------------------------------------------- the cast
def A(who, draw, feet, h, **kw):
    d = dict(who=who, draw=draw, feet=feet, h=h)
    d.update(kw)
    return d


R_MIC = "wayne-rooney:mic"


def rooney(feet, h, up=False, **kw):
    """Rooney with his handheld microphone in his right hand (the raised one drawn over his face rigidly, so it
    never moves with the jaw)"""
    if up:
        return A("rooney", "wayne-rooney:micup", feet, h, ref=R_MIC, over=["wayne-rooney:micup-fg"], **kw)
    return A("rooney", R_MIC, feet, h, ref=R_MIC, **kw)


STRIDE = 0.42                                # a step is this share of the walker's height


def walker(who, keys, path, h, period=0.5, stride=True, **kw):
    """someone walking: the walk keys in order, one per half beat (a step on every beat: a terrace march), along a
    path of feet. With stride=True the path's end is moved so they cover exactly a step's length (STRIDE x height)
    per step: the planted foot stays put on the ground instead of skating"""
    if stride and len(path) == 2:
        from studio.film.stage import SONG
        (t0, (x0, y0)), (t1, (x1, y1)) = path
        steps = (t1 - t0) / (2 * period * SONG().period)          # two keys to a step
        d = STRIDE * h * steps * (1 if x1 >= x0 else -1)
        path = [(t0, (x0, y0)), (t1, (x0 + d, y1))]
    return A(who, keys[0], path[0][1], h, walk=dict(keys=keys, period=period), path=path, ref=keys[0], **kw)


WALK = {"rooney": ["wayne-rooney:walk1", "wayne-rooney:walk2", "wayne-rooney:walk3", "wayne-rooney:walk2"],
        "rio": ["rio-ferdinand:walk1", "rio-ferdinand:walk2", "rio-ferdinand:walk3", "rio-ferdinand:walk2"],
        "mark": [f"mark-goldbridge:walk{k}" for k in (1, 2, 3, 4)],
        "gary": [f"gary-neville:walk{k}" for k in (1, 2, 3, 4)],
        "roy": [f"roy-keane:walk{k}" for k in (1, 2, 3, 4)],
        "kid": ["wayne-rooney:kit-run1", "wayne-rooney:kit-run2", "wayne-rooney:kit-run3", "wayne-rooney:kit-run2"]}


def band_at(maguire, sesko, cunha, scale=1.0, kit=False, **over):
    """the band: (feet, h) each; kit=True brings the pub's drum kit with the drummer (any other stage)"""
    out = [A("maguire", "harry-maguire:drumming", maguire[0], maguire[1], inst="drums", kit=kit),
           A("sesko", "benjamin-sesko:guitar", sesko[0], sesko[1], inst="guitar"),
           A("cunha", "matheus-cunha:bass", cunha[0], cunha[1], inst="bass")]
    for a in out:
        a.update(over.get(a["who"], {}))
    return out


PUB_BAND = band_at(((880, 516), 322), ((545, 552), 368), ((1112, 552), 358))
ROO_PUB = ((676, 578), 340)                         # Rooney at the front of the pub stage


def pub(front=(), fans=False, extra=(), hide=(), blur=None):
    """the pub stage: the drummer behind his kit, the guitarists and whoever is at the front, the monitors, the
    fans; blur: {who: px} for the players the lens is not on"""
    band = [dict(a, blur=(blur or {}).get(a["who"], 0.0)) for a in PUB_BAND if a["who"] not in hide]
    lay = [("actors", [a for a in band if a["who"] == "maguire"]), ("occl", "kit"),
           ("actors", [a for a in band if a["who"] != "maguire"] + list(front)), ("occl", "monitors")]
    if fans:
        lay.append(("fans", "FC"))
    return lay + list(extra)


def frame(feet, h, size, dx=0.0, dy=0.0):
    """a camera on someone (United Road's frame()): cu / mcu / ms / full / wide -> (cx, cy, zoom), plate px"""
    k, span = {"cu": (0.17, 0.36), "mcu": (0.27, 0.62), "ms": (0.45, 0.98), "full": (0.55, 1.28),
               "wide": (0.6, 2.4)}[size]
    cy = feet[1] - h + k * h + dy * h
    return (feet[0] + dx * h, cy, 940.0 / (span * h))


def push(cam, f, dx=0.0, dy=0.0):
    return (cam[0] + dx, cam[1] + dy, cam[2] * f) + tuple(cam[3:])


CALM = dict(lights=0.85, beams=0.7, flash=0.4, punch=0.15, haze=0.22)
VERSE = dict(lights=1.05, beams=1.05, flash=0.8, punch=0.7, haze=0.3)
CHORUS = dict(lights=1.35, beams=1.45, flash=1.3, punch=1.2, shake=0.3, haze=0.42)
ANTHEM = dict(lights=1.55, beams=1.7, flash=1.6, punch=1.5, shake=0.5, haze=0.5, fans_jump=1.4)
QUIET = dict(lights=0.0, beams=0.0, flash=0.0, punch=0.0, haze=0.0)


# ================================================================ the shots
SH = []


def add(*shots):
    SH.extend(shots)


def S_(t0, plate, cams, layers, **kw):
    """a shot: cams [(t, (cx, cy, zoom[, roll]))] or (cam0, cam1) spread over the shot (end filled in by finish)"""
    return stage(t0, plate, cams, layers, **kw)


def move(t0, t1, c0, c1):
    return [(t0, c0), (t1, c1)]


# ---------------------------------------------------------------- the pub: who is where (plate F/FC px)
RIO_FLOOR = ((402, 818), 470)               # Rio on the floor, stage left, in front of the stage
MARK_FLOOR = ((205, 880), 520)              # Goldbridge at the left-hand table
ROY_FLOOR = ((1440, 880), 520)              # Keane by the pillar, stage right
RIO_STAGE = ((500, 582), 368)               # Rio up on the stage beside Rooney (bar 9)
BALL_R = 20.0                               # the football's radius beside a 340 px Rooney (22 cm against 1.76 m)
FLOOR_Y = 578                               # the stage floor at the front (plate F)


def roo_pub(**kw):
    return rooney(*ROO_PUB, **kw)


# ---- chorus 1 ---------------------------------------------------------------------------------------------------
# 0.00: the ball rolls in across the stage floor and stops against his trainer; the camera tilts up his body and
# finds him already singing at the first word (2.26 s). Lights come up with the song's fade-in
ROLL = dict(keys=[(0.15, 900, FLOOR_Y - BALL_R), (1.45, ROO_PUB[0][0] + 56, FLOOR_Y - BALL_R, 0.0, "out")],
            r=BALL_R, floor=FLOOR_Y, t1=b(3))
add(S_(0.0, "F", [(0.0, (ROO_PUB[0][0] + 60, 560, 7.0)), (1.55, (ROO_PUB[0][0] + 40, 552, 6.6)),
                   (2.30, frame(*ROO_PUB, "mcu")), (b(1), push(frame(*ROO_PUB, "mcu"), 1.05))],
       pub([roo_pub(look_cam=True)], blur={"sesko": 4.0, "cunha": 4.0, "maguire": 3.0},
           extra=[("props", "ball")]),
       ball=ROLL, blur=3.0, dark=lambda t: max(0.0, 0.7 * (1 - t / 2.2)), **CALM))
# 4.9 (bar 1): Rio, on the floor, hears it and turns to the stage with a delighted grin
add(S_(b(1), "F", move(b(1), b(2), frame(*RIO_FLOOR, "ms", dx=0.12), push(frame(*RIO_FLOOR, "ms", dx=0.12), 1.06)),
       pub([A("rio", "rio-ferdinand:front", *RIO_FLOOR, face=(0.75, 0.9)), roo_pub(blur=5.0)],
           blur={"sesko": 6.0, "cunha": 6.0, "maguire": 6.0}), blur=5.0, **CALM))
# 6.4 (bar 2): the room: Goldbridge with his scarf up, Keane with his arms folded, the fans, the band
add(S_(b(2), "FC", move(b(2), b(4), (836, 470, 1.0), (836, 455, 1.08)),
       pub([roo_pub(), A("rio", "rio-ferdinand:front", *RIO_FLOOR),
            A("mark", "mark-goldbridge:cheer", *MARK_FLOOR, ref="mark-goldbridge:stand", still_face=True,
              hold=[dict(prop="scarf", at=(573, 846), to=(692, 846), size=7, kind="bars", behind=True)]),
            A("roy", "roy-keane:crossed", *ROY_FLOOR)], fans=True),
       blur=1.2, **CALM))
# 9.3 (bar 4): Keane, unmoved
add(S_(b(4), "F", move(b(4), b(5), (1150, 330, 2.2), (1150, 330, 2.3)),
       [("actors", [A("roy", "roy-keane:crossed-cu", (960, 1640), 1600, screen=True, dance=0.3)])],
       blur=7.0, **CALM))
# 10.8 (bar 5): Rooney into the lens, "He goes by the name of Wayne Rooney"
add(S_(b(5), "F", move(b(5), b(7), frame(*ROO_PUB, "mcu", dx=0.04), push(frame(*ROO_PUB, "mcu", dx=0.04), 1.08)),
       pub([roo_pub(look_cam=True)], blur={"sesko": 5.0, "cunha": 5.0, "maguire": 4.0}), blur=4.0, **CALM))
# 13.7 (bar 7): closer, the mic up for the name
add(S_(b(7), "F", move(b(7), b(8), frame(*ROO_PUB, "cu", dx=0.05), push(frame(*ROO_PUB, "cu", dx=0.05), 1.05)),
       pub([roo_pub(up=True, look_cam=True)], blur={"sesko": 7.0, "cunha": 7.0, "maguire": 6.0}), blur=5.0, **CALM))
# 15.2 (bar 8): the drums come in
add(S_(b(8), "F", move(b(8), b(9), (880, 360, 2.9), (880, 356, 3.1)),
       pub([roo_pub(blur=6.0)], blur={"sesko": 5.0, "cunha": 5.0}), blur=3.0, **VERSE))
# 16.7 (bar 9): Rio up beside him, rallying the room; Goldbridge's trophy wobbles on the table and he saves it
add(S_(b(9), "F", move(b(9), b(11), (600, 380, 2.0), (600, 370, 2.12)),
       pub([A("rio", "rio-ferdinand:rally", *RIO_STAGE, ref="rio-ferdinand:front", look_cam=True), roo_pub()],
           blur={"sesko": 3.0, "cunha": 3.0, "maguire": 3.0},
           extra=[("props", "trophy_table"),
                  ("actors", [A("mark", "mark-goldbridge:shocked", (330, 1210), 900, screen=True, blur=3.0,
                                keys=[(b(9), "mark-goldbridge:shocked"), (b(10, 0.55), "mark-goldbridge:smug")],
                                ref="mark-goldbridge:stand")])]),
       blur=1.5, **VERSE))
# 19.6 (bar 11): the first response: the room sings it back, scarves going up along the rows
add(S_(b(11), "PUB", move(b(11), b(13), (940, 300, 2.0), (940, 300, 2.08)),
       [("actors", "CROWD_A"), ("props", "scarves_rise"),
        ("stage_edge", dict(y=0.9, monitor=-1, mic=None, blur=9.0))],
       blur=7.0, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=3, amount=0.3), rim=0.3,
       rim_color=(1.0, 0.72, 0.45), scarves_t=b(11, 0.15)))
# 22.5 (bar 13): Rooney plants his feet and leads the room: the stage from the floor, the fans' fists up
add(S_(b(13), "F", move(b(13), b(15), (760, 400, 1.6), (740, 392, 1.75)),
       pub([roo_pub(look_cam=True), A("rio", "rio-ferdinand:rally", *RIO_STAGE, ref="rio-ferdinand:front")],
           extra=[("fg_fans", dict(y=0.83, n=13, seed=7, blur=5.0, arms=0.9, scale=0.95, rim=0.75))]), **CHORUS))

# ---- the instrumental: toe-taps, then the memory -------------------------------------------------------------------
# 25.5 (bar 15): low on the stage floor: he keeps the ball up between his feet on the beat, the front foot tapping it
# (the toe lifts to meet it); the ball's bottom is at the toe's highest, half a beat after each beat
def keepy_uppy(t0, t1, foot_x, floor, r):
    from studio.film.stage import SONG
    S = SONG()
    ks, t = [], t0
    i = S.beat_index(t0) + 1
    while S.B[i] < t1:
        tb = S.B[i] + 0.5 * S.period
        ks.append((tb, foot_x + 6 * (-1) ** i, floor - r - 8))                     # on the toe
        if i + 1 < len(S.B):
            ks.append(((S.B[i + 1] + 0.5 * S.period + tb) / 2, foot_x + 3 * (-1) ** i, floor - r - 8, 64.0))
        i += 1
    return ks


TOE = (ROO_PUB[0][0] + 26, FLOOR_Y)
add(S_(b(15), "F", move(b(15), b(16), (ROO_PUB[0][0] - 20, 412, 2.2), (ROO_PUB[0][0] - 20, 408, 2.32)),
       pub([roo_pub(tap=dict(at=(612, 1440), r=60, lift=40, spans=[(b(15), b(17))], toe=-1)),
            A("rio", "rio-ferdinand:folded", (480, 582), 368, ref="rio-ferdinand:front", face=(0.5, 0.7))],
           blur={"sesko": 4.0, "cunha": 4.0, "maguire": 4.0}, extra=[("props", "ball")]),
       ball=dict(keys=keepy_uppy(b(15) - 0.4, b(17), *TOE, BALL_R), r=BALL_R, floor=FLOOR_Y), blur=2.0,
       **VERSE))
# 26.9 (bar 16): Keane, looking down at the technique
add(S_(b(16), "F", move(b(16), b(17), frame(*ROY_FLOOR, "ms", dx=-0.1), push(frame(*ROY_FLOOR, "ms", dx=-0.1), 1.05)),
       pub([A("roy", "roy-keane:crossed", *ROY_FLOOR, dance=0.3)], blur={"sesko": 6, "cunha": 6, "maguire": 6}),
       blur=6.0, wipe_out=b(17), **VERSE))

# 28.4 (bar 17): a scarf wipes across the lens into the memory: a sunny afternoon at the ground, the younger Rooney
# in a red 10. The ball comes in along the grass and he stops it under his sole
KID = ((960, 1010), 720)                     # screen px: the young Rooney in medium shots
MEMCAM = (836, 520, 2.2)
add(S_(b(17), "MEM", move(b(17), b(19), MEMCAM, push(MEMCAM, 1.05, dx=-20)),
       [("props", "stands"), ("props", "ball_screen"),
        ("actors", [A("kid", "wayne-rooney:kit-front", *KID, screen=True, ref="wayne-rooney:kit-front",
                      face=(0.2, 0.55))])],
       blur=4.0, grade="crowd", wipe_in=b(17), ball_screen=dict(
           keys=[(b(17) + 0.1, 1980, 980), (b(17) + 1.2, 1032, 980, 0.0, "out")], r=40, floor=1018),
       crowd_jump=0.6, **QUIET))
# 31.3 (bar 19): side on, tracking with him: he runs with it at his feet, a defender a step behind, the stands
# streaming past (the camera pans the plate; he stays in frame)
RUN_PATH = [(b(19), (760, 1015)), (b(21), (1100, 1015))]
add(S_(b(19), "MEM", move(b(19), b(21), (300, 540, 2.2), (1350, 540, 2.2)),
       [("props", "stands"),
        ("actors", [A("def", "rio-ferdinand:run1", (520, 1012), 690, screen=True, ref="rio-ferdinand:run1",
                      walk=dict(keys=["rio-ferdinand:run1", "rio-ferdinand:run2"], period=0.5, phase=1),
                      path=[(b(19), (420, 1012)), (b(21), (760, 1012))], tint=(0.10, 0.12, 0.22, 0.9),
                      blur=6.0, dance=0.0)]),
        ("props", "dribble"),
        ("actors", [A("kid", "wayne-rooney:kit-run1", RUN_PATH[0][1], 700, screen=True, ref="wayne-rooney:kit-run1",
                      walk=dict(keys=WALK["kid"], period=0.5), path=RUN_PATH, dance=0.0)])],
       blur=5.0, grade="crowd", crowd_jump=0.8, motion=28.0, **QUIET))
# 34.3 (bar 21): the strike: the plant, the swing, the ball away
add(S_(b(21), "MEM", move(b(21), b(21, 0.5), (1350, 560, 2.6), (1380, 560, 2.7)),
       [("props", "stands"),
        ("actors", [A("kid", "wayne-rooney:kit-run2", (900, 1015), 760, screen=True, ref="wayne-rooney:kit-run2",
                      keys=[(b(21), "wayne-rooney:kit-run2"), (b(21, 0.22), "wayne-rooney:kit-run1")], dance=0.0)]),
        ("props", "ball_screen"), ("props", "strike_flash")],
       blur=5.0, grade="crowd", crowd_jump=0.8, strike=b(21, 0.22), ball_screen=dict(
           keys=[(b(21), 1080, 985), (b(21, 0.22), 1080, 985), (b(21, 0.5), 2150, 260, 60.0)], r=42, floor=1018,
           blur_v=46), **QUIET))
# 35.0: into the net
add(S_(b(21, 0.5), "MEM", move(b(21, 0.5), b(22), (857, 560, 5.4), (857, 562, 6.0)),
       [("props", "stands"), ("props", "goal_net")], blur=6.0, grade="crowd", crowd_jump=1.4,
       net=dict(t=b(21, 0.5) + 0.33, at=(857, 572)), **QUIET))
# 35.7 (bar 22): arms spread, the stands going up behind him, cameras flashing
add(S_(b(22), "MEM", move(b(22), b(23), (836, 430, 2.4), (836, 420, 2.7)),
       [("props", "stands"), ("props", "flashes"),
        ("actors", [A("kid", "wayne-rooney:kit-shrug", (960, 1330), 1250, screen=True, ref="wayne-rooney:kit-front",
                      face=(0.8, 1.0), look_cam=True)])],
       blur=6.0, grade="crowd", crowd_jump=1.6, scarves=[(b(22), b(23) + 1)], **QUIET))

# ---- verse 1: back to the pub, out into the street ------------------------------------------------------------------
# 37.1 (bar 23): the match cut: the same spread arms, now in the pub in his own clothes
add(S_(b(23), "F", move(b(23), b(23, 0.58), (676, 300, 2.2), (676, 300, 2.3)),
       pub([A("rooney", "wayne-rooney:shrug", (676, 640), 420, ref="wayne-rooney:mic", face=(0.7, 1.0),
              look_cam=True)], blur={"sesko": 4, "cunha": 4, "maguire": 4}), blur=3.5, **VERSE))
# 37.9: "From Croxteth streets to theatre dreams": the mic back up, and he heads for the door
add(S_(b(23, 0.58), "F", move(b(23, 0.58), b(25), frame(*ROO_PUB, "mcu", dx=0.05),
                              push(frame(*ROO_PUB, "mcu", dx=0.05), 1.06, dx=-30)),
       pub([roo_pub()], blur={"sesko": 5, "cunha": 5, "maguire": 4}), blur=4.0, **VERSE))


# ---------------------------------------------------------------- the street (plate ST: a person's height grows
# with their distance below the horizon, h = 2.5 (y - 505) plate px)
def st_h(y):
    return 2.5 * (y - 505)


def st_walk(who, x0, x1, y, t0, t1, period=0.5, **kw):
    return walker(who, WALK[who], [(t0, (x0, y)), (t1, (x0 + 1, y))], st_h(y), period=period, **kw)


# 40.0 (bar 25): out of the pub (the cafe on the corner) and down the street: Rooney and Rio in front, the supporters
# behind them, the camera panning with them
add(S_(b(25), "ST", move(b(25), b(28), (430, 520, 1.6), (1080, 530, 1.6)),
       [("actors", [st_walk("gary", 30, 0, 574, b(25), b(28)), st_walk("roy", 120, 0, 580, b(25), b(28)),
                    st_walk("mark", 70, 0, 588, b(25), b(28)),
                    st_walk("rio", 200, 0, 594, b(25), b(28)), st_walk("rooney", 270, 0, 600, b(25), b(28))]),
        ("props", "passers")],
       passers=dict(n=9, y=0.86, speed=0.07, seed=3), blur=0.0, grade="crowd", **QUIET))
# 44.4 (bar 28): with Rooney, singing as he walks; Rio beside him
add(S_(b(28), "ST", move(b(28), b(30), (700, 470, 2.6), (760, 466, 2.7)),
       [("actors", [A("rio", "rio-ferdinand:q34", (610, 905), 560, ref="rio-ferdinand:q34", bob=dict(), blur=1.5),
                    rooney((800, 930), 560, mirror=True, bob=dict(phase=0.5), look_cam=False)]),
        ("props", "passers")], passers=dict(n=7, y=0.9, speed=0.05, seed=8, blur=7.0),
       blur=4.0, grade="crowd", **QUIET))
# 47.3 (bar 30): Neville checks his clipboard while Goldbridge marches past far too keenly
add(S_(b(30), "ST", move(b(30), b(31), (980, 470, 2.4), (1010, 470, 2.5)),
       [("actors", [walker("mark", WALK["mark"], [(b(30), (760, 860)), (b(31), (1300, 860))], 520, period=0.35,
                           blur=0.0),
                    A("gary", "gary-neville:clipboard", (1090, 1180), 900, ref="gary-neville:stand",
                      face=(-0.4, -0.2))])],
       blur=4.0, grade="crowd", **QUIET))
# 48.8 (bar 31): the mural: THE WHITE PELE painted on the gable; supporters stream past with scarves and flags
add(S_(b(31), "MW", move(b(31), b(35), (700, 470, 1.3), (640, 470, 1.45)),
       [("props", "mural_text"), ("actors", [rooney((300, 805), 560, look_cam=True)]), ("props", "passers")],
       passers=dict(n=8, y=0.88, speed=0.06, seed=11, scarves=True), grade="crowd", **QUIET))
# 54.6 (bar 35): on Sir Matt Busby Way Goldbridge poses for a camera that isn't there; Rio drags him on
add(S_(b(35), "ST", move(b(35), b(37), (520, 470, 2.0), (560, 470, 2.06)),
       [("props", "street_sign"),
        ("actors", [A("mark", "mark-goldbridge:pointing", (540, 1180), 840, ref="mark-goldbridge:stand",
                      look_cam=True, face=(0.5, 0.9),
                      path=[(b(35), (540, 1180)), (b(36, 0.5), (540, 1180)), (b(37), (980, 1180))]),
                    walker("rio", WALK["rio"], [(b(35, 0.2), (20, 980)), (b(36, 0.5), (360, 980)),
                                                (b(37), (820, 980))], 700, period=0.5)])],
       blur=2.5, grade="crowd", **QUIET))
# 57.5 (bar 37): Old Trafford at the end of the road: they stop and look; Rooney looks up at it
add(S_(b(37), "ST", move(b(37), b(39), (900, 470, 1.25), (900, 420, 1.55)),
       [("actors", [A("mark", "mark-goldbridge:back", (700, 700), st_h(700) * 0.98),
                    A("rio", "rio-ferdinand:back", (780, 735), st_h(735)),
                    A("rooney", "wayne-rooney:back", (900, 745), st_h(745) * 0.92)]),
        ("props", "passers")], passers=dict(n=6, y=0.92, speed=0.04, seed=4), grade="crowd", **QUIET))
# 60.5 (bar 39): "...we lose our minds that day": he turns from the stadium to Rio and smiles
add(S_(b(39), "ST", move(b(39), b(41), frame((870, 940), 600, "mcu", dx=-0.05), push(frame((870, 940), 600, "mcu", dx=-0.05), 1.05)),
       [("actors", [rooney((870, 940), 600, look_cam=False), A("rio", "rio-ferdinand:q34", (520, 960), 640,
                                                                 ref="rio-ferdinand:q34", blur=3.0)])],
       blur=6.0, grade="crowd", **QUIET))
# 63.4 (bar 41): Old Trafford at dusk, the crowd arriving; "When he turns and lets one fly"
add(S_(b(41), "EXT", move(b(41), b(44), (836, 560, 1.0), (836, 520, 1.25)),
       [("actors", [walker("mark", WALK["mark"], [(b(41), (240, 780)), (b(44), (241, 780))], 120),
                    walker("roy", WALK["roy"], [(b(41), (300, 790)), (b(44), (301, 790))], 128),
                    walker("rio", WALK["rio"], [(b(41), (380, 800)), (b(44), (381, 800))], 140),
                    walker("rooney", WALK["rooney"], [(b(41), (460, 812)), (b(44), (461, 812))], 128)]),
        ("props", "passers")], passers=dict(n=12, y=0.95, speed=0.05, seed=21, scarves=True),
       grade="crowd", **QUIET))
# 67.6 (bar 44): the concourse, red light, flags going in; "You just know it's top bin time"
add(S_(b(44), "EXT2", move(b(44), b(47), (836, 520, 1.3), (836, 560, 1.7)),
       [("actors", [A("mark", "mark-goldbridge:back", (760, 720), 120), A("rio", "rio-ferdinand:back", (840, 735), 150),
                    A("rooney", "wayne-rooney:back", (920, 740), 128), A("roy", "roy-keane:stand", (1000, 730), 140,
                                                                          dance=0.2)]),
        ("props", "passers")], passers=dict(n=10, y=0.95, speed=0.03, seed=5, scarves=True, flags=True),
       grade="crowd", **QUIET))


# ---------------------------------------------------------------- the stadium (plate OTS: the stage on the pitch)
ROO_ST = ((835, 702), 80)
RIO_ST = ((600, 700), 88)
MARK_ST = ((1040, 700), 82)
ROY_ST = ((1100, 703), 84)
OT_BAND = band_at(((835, 668), 75), ((715, 690), 86), ((955, 690), 84), kit=True)


def ots(front=(), extra=(), blur=None, band=True, hide=()):
    """the stage: the band (the drummer with his kit), whoever is at the front, the crowd in the stands"""
    bl = blur or {}
    bnd = [dict(a, blur=bl.get(a["who"], 0.0)) for a in OT_BAND if band and a["who"] not in hide]
    fr = [dict(a, blur=bl.get(a["who"], a.get("blur", 0.0))) for a in front if a["who"] not in hide]
    return [("props", "stands"), ("actors", bnd + fr)] + list(extra)


def roo_st(**kw):
    return rooney(*ROO_ST, **kw)


SIDE = lambda: [A("rio", "rio-ferdinand:front", *RIO_ST),                                # noqa: E731
                A("mark", "mark-goldbridge:stand", *MARK_ST, look_cam=False),
                A("roy", "roy-keane:crossed", *ROY_ST, dance=0.25)]
FG = lambda t0, n=15: ("fg_fans", dict(y=0.82, n=n, seed=int(t0 * 7) % 97, blur=5.0, arms=0.9, scale=0.9,   # noqa
                                         rim=0.8))
STAGE_WIDE = (835, 560, 2.3)
STAGE_CU = lambda size, up=False: frame(*ROO_ST, size, dx=0.05)                          # noqa: E731


# ---- chorus 2 ----------------------------------------------------------------------------------------------------
# 71.9 (bar 47): the tunnel, walking out towards the light: Rooney, Rio and Keane, the camera backing away in front
TUN_CAM = (836, 470, 1.4)
add(S_(b(47), "TUN", move(b(47), b(50), push(TUN_CAM, 1.25), TUN_CAM),
       [("actors", [A("rio", "rio-ferdinand:front", (560, 1500), 1100, screen=True, bob=dict(phase=0.5)),
                    A("roy", "roy-keane:stand", (1390, 1480), 1060, screen=True, bob=dict(phase=0.25)),
                    rooney((960, 1560), 1180, screen=True, bob=dict(), look_cam=True)])],
       blur=5.0, grade="crowd", light_end=dict(color=(1.0, 0.95, 0.86), amount=0.35), **QUIET))
# 76.3 (bar 50): from behind them, the mouth of the tunnel and the pitch
add(S_(b(50), "TUNP", move(b(50), b(51), (836, 560, 1.15), (836, 520, 1.4)),
       [("actors", [A("rio", "rio-ferdinand:back", (700, 935), 520, bob=dict(phase=0.5)),
                    A("rooney", "wayne-rooney:back", (880, 945), 470, bob=dict())])], grade="crowd", **QUIET))
# 77.8 (bar 51): the stadium: the stage on the pitch, the band playing, the stands full
add(S_(b(51), "OTS", move(b(51), b(52), (836, 330, 1.0), (836, 470, 1.15)),
       ots(extra=[FG(b(51))]), **CHORUS))
# 79.2 (bar 52): Rooney walks out to the front of the stage
add(S_(b(52), "OTS", move(b(52), b(53), (760, 600, 4.0), (820, 610, 4.4)),
       ots([walker("rooney", WALK["rooney"], [(b(52), (707, 702)), (b(53), (835, 702))], 78, period=0.5),
            *SIDE()], blur={"maguire": 2.0, "sesko": 2.0, "cunha": 2.0}), blur=2.0, **CHORUS))
# 80.7 (bar 53): "He goes by the name of Wayne Rooney"
add(S_(b(53), "OTS", move(b(53), b(55), STAGE_CU("mcu"), push(STAGE_CU("mcu"), 1.06)),
       ots([roo_st(look_cam=True)], blur={"maguire": 6.0, "sesko": 6.0, "cunha": 6.0}), blur=6.0, **CHORUS))
# 83.6 (bar 55): the name, the mic up
add(S_(b(55), "OTS", move(b(55), b(57), STAGE_CU("cu"), push(STAGE_CU("cu"), 1.05)),
       ots([roo_st(up=True, look_cam=True)], blur={"maguire": 8.0, "sesko": 8.0, "cunha": 8.0}), blur=7.0, **CHORUS))
# 86.6 (bar 57): the crowd sings his name back and shouts "Hey!"
add(S_(b(57), "OT", move(b(57), b(59), (836, 380, 1.4), (836, 380, 1.47)),
       [("props", "stands"), ("actors", "CROWD_B"),
        ("stage_edge", dict(y=0.88, monitor=1, mic=None, blur=9.0)), ("pyro_near", None)],
       blur=5.0, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=3, amount=0.4), rim=0.35,
       rim_color=(1.0, 0.85, 0.75), **{k: v for k, v in CHORUS.items() if k not in ("lights", "beams")}))
# 89.5 (bar 59): the stage, everyone on it
add(S_(b(59), "OTS", move(b(59), b(61), STAGE_WIDE, push(STAGE_WIDE, 1.08)),
       ots([roo_st(), *SIDE()], extra=[FG(b(59))]), **CHORUS))
# 92.4 (bar 61): side of the stage: Rio and Goldbridge firing up the front rows
add(S_(b(61), "OTS", move(b(61), b(63), (835, 640, 11.0), (840, 640, 11.5)),
       ots([A("rio", "rio-ferdinand:rally", (790, 704), 90, ref="rio-ferdinand:front", look_cam=True),
            A("mark", "mark-goldbridge:stand", (880, 704), 84, look_cam=True)],
           band=False, extra=[("fg_fans", dict(y=0.6, n=8, seed=5, blur=6.0, arms=0.9, scale=1.5, rim=0.8))]),
       blur=6.0, **CHORUS))

# ---- verse 2 -----------------------------------------------------------------------------------------------------
# 95.3 (bar 63): "Hey!" and "Volley smash in the derby night"
add(S_(b(63), "OTS", move(b(63), b(65), STAGE_CU("ms"), push(STAGE_CU("ms"), 1.08)),
       ots([roo_st(look_cam=True)], blur={"maguire": 5.0, "sesko": 5.0, "cunha": 5.0}), blur=5.0, **VERSE))
# 98.2 (bar 65): the bicycle kick, in silhouette against the floodlights: the run, the leap, the strike upside down,
# hanging in the air, the landing (props.bicycle draws it)
add(S_(b(65), "OT", move(b(65), b(69), (836, 300, 1.6), (836, 280, 1.75)),
       [("props", "stands"), ("props", "bicycle")], blur=6.0, grade="crowd", lights=0.0, beams=0.0,
       crowd_tone=0.45, flash=0.0, **{k: v for k, v in CALM.items() if k not in ("lights", "beams", "flash")}))
# 104.1 (bar 69): the ball's arc becomes the camera's sweep across the scarves: "Old Trafford shaking left and right"
add(S_(b(69), "OT", [(b(69), (300, 400, 2.4)), (b(70), (1350, 410, 2.4)), (b(71), (700, 400, 2.3))],
       [("props", "stands")], blur=1.5, grade="crowd", lights=0.0, beams=0.0, scarves=[(b(69) - 1, b(71) + 1)],
       crowd_jump=1.6, motion=30.0))
# 107.0 (bar 71): "Captain's armband on his sleeve"
add(S_(b(71), "OTS", move(b(71), b(73), STAGE_CU("cu"), push(STAGE_CU("cu"), 1.05)),
       ots([roo_st(look_cam=True)], blur={"maguire": 8.0, "sesko": 8.0, "cunha": 8.0}), blur=7.0, **VERSE))
# 109.9 (bar 73): under Keane's folded arms, a foot is tapping...
KEANE_FEET = (ROY_ST[0][0], ROY_ST[0][1] - 14, 13.0)
TAP = dict(at=(250, 1830), r=110, lift=120, spans=[(b(73), b(74, 0.45)), (b(75, 0.55), b(76))], toe=-1)
add(S_(b(73), "OTS", move(b(73), b(74), KEANE_FEET, push(KEANE_FEET, 1.04)),
       ots([A("roy", "roy-keane:crossed", *ROY_ST, tap=TAP, dance=0.0)], band=False), blur=4.0, **VERSE))
# 111.4 (bar 74): ...Rio spots it; Keane stops dead and glares at him; Rio looks away
add(S_(b(74), "OTS", move(b(74), b(75, 0.5), (1060, 652, 9.0), (1060, 652, 9.4)),
       ots([A("rio", "rio-ferdinand:front", (1015, 702), 88),
            A("roy", "roy-keane:crossed", *ROY_ST, dance=0.0, tap=TAP)], band=False), blur=7.0, **VERSE))
# 113.6: the moment Rio looks away, the foot goes again
add(S_(b(75, 0.5), "OTS", move(b(75, 0.5), b(76), KEANE_FEET, push(KEANE_FEET, 1.03)),
       ots([A("roy", "roy-keane:crossed", *ROY_ST, tap=TAP, dance=0.0)], band=False), blur=4.0, **VERSE))
# 114.4 (bar 76): from behind him, the crowd singing it back: "England's hope and United's pride"
add(S_(b(76), "OT", move(b(76), b(78), (836, 420, 1.3), (836, 410, 1.38)),
       [("props", "stands"), ("actors", "CROWD_C"),
        ("actors", [A("rooney", "wayne-rooney:back", (960, 1500), 1100, screen=True, blur=2.0)])],
       blur=4.0, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=3, amount=0.35)))
# 117.3 (bar 78): "Goals and glory side by side": Rooney and the band
add(S_(b(78), "OTS", move(b(78), b(80), (835, 640, 6.5), (835, 640, 6.9)),
       ots([roo_st(look_cam=True)]), blur=3.0, **VERSE))

# ---- the breakdown: the drums stop -----------------------------------------------------------------------------
SPOT = dict(at="rooney", r=60, dark=0.62, tall=1.6)
add(S_(b(80), "OTS", move(b(80), b(82), (835, 600, 3.2), (835, 610, 3.6)),
       ots([roo_st(), *SIDE()], extra=[("props", "phones")]), spot=SPOT, **CALM))
# 123.1 (bar 82): Goldbridge comes up with his tiny trophy to crown him; Rooney eyes it and sings on
add(S_(b(82), "OTS", move(b(82), b(84), (872, 638, 11.0), (870, 638, 11.6)),
       ots([roo_st(), A("mark", "mark-goldbridge:cheer", (905, 718), 84, ref="mark-goldbridge:stand", still_face=True,
                         hold=[dict(prop="trophy", at=(690, 846), size=34, behind=True, wobble=4.0)],
                         look_cam=False)], band=False), blur=7.0, spot=dict(SPOT, r=110), **CALM))
# 126.0 (bar 84): the crowd swaying, phones up
add(S_(b(84), "OT", move(b(84), b(86), (836, 380, 1.5), (836, 375, 1.56)),
       [("props", "stands"), ("props", "phones"), ("actors", "CROWD_D"),
        ("stage_edge", dict(y=0.9, monitor=-1, mic=None, blur=9.0))],
       blur=5.0, grade="crowd", lights=0.0, beams=0.0, crowd_tone=0.55, crowd_jump=0.4))
# 128.9 (bar 86): "He led the line and forged ahead"
add(S_(b(86), "OTS", move(b(86), b(88), STAGE_CU("mcu"), push(STAGE_CU("mcu"), 1.1)),
       ots([roo_st(look_cam=True)], blur={"maguire": 7, "sesko": 7, "cunha": 7}), blur=7.0, spot=SPOT, **CALM))

# ---- chorus 3 ----------------------------------------------------------------------------------------------------
# 132.0 (bar 88): from behind Rooney: the crowd in layers, the front singing, the stands pulsing
add(S_(b(88), "OT", move(b(88), b(91), (836, 400, 1.15), (836, 410, 1.3)),
       [("props", "stands"), ("actors", "CROWD_E"),
        ("actors", [A("rooney", "wayne-rooney:back", (960, 1560), 1180, screen=True, blur=1.5)])],
       blur=3.5, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=4, amount=0.4)))
add(S_(b(91), "OTS", move(b(91), b(93), STAGE_CU("mcu"), push(STAGE_CU("mcu"), 1.06)),
       ots([roo_st(look_cam=True)], blur={"maguire": 6, "sesko": 6, "cunha": 6}), blur=6.0, **CHORUS))
add(S_(b(93), "OTS", move(b(93), b(95), (800, 650, 8.0), (805, 650, 8.4)),
       ots([roo_st(), A("rio", "rio-ferdinand:front", (765, 704), 88)], band=False), blur=6.0, **CHORUS))
# 142.3 (bar 95): everything
add(S_(b(95), "OTS", move(b(95), b(96), (835, 520, 1.7), (835, 540, 2.0)), ots([roo_st(), *SIDE()],
       extra=[FG(b(95))]), **ANTHEM))
add(S_(b(96), "OTS", move(b(96), b(97), STAGE_CU("cu"), push(STAGE_CU("cu"), 1.05)),
       ots([roo_st(up=True, look_cam=True)], blur={"maguire": 8, "sesko": 8, "cunha": 8}), blur=7.0, **ANTHEM))
add(S_(b(97), "OTS", move(b(97), b(98), (600, 624, 12.5), (600, 624, 13.0)),
       ots([A("rio", "rio-ferdinand:shrug", *RIO_ST, ref="rio-ferdinand:front", face=(0.9, 1.0), look_cam=True)],
           band=False), blur=7.0, **ANTHEM))
add(S_(b(98), "OTS", move(b(98), b(99), frame((1040, 702), 84, "cu", dy=0.02), push(frame((1040, 702), 84, "cu", dy=0.02), 1.06)),
       ots([A("mark", "mark-goldbridge:shouting", (1040, 702), 84, ref="mark-goldbridge:stand")], band=False),
       blur=7.0, **ANTHEM))
add(S_(b(99), "OTS", move(b(99), b(99, 0.62), (1100, 650, 10.0), (1100, 650, 10.4)),
       ots([A("roy", "roy-keane:crossed", *ROY_ST, dance=0.0)], band=False), blur=7.0, **ANTHEM))
# 149.1: and Keane claps. Once. On the crash
add(S_(b(99, 0.62), "OTS", move(b(99, 0.62), b(100, 0.2), (1100, 650, 10.0), (1100, 650, 10.2)),
       [("props", "stands"), ("props", "clap")], blur=9.0, clap=dict(t=149.243), **ANTHEM))
add(S_(b(100, 0.2), "OT", move(b(100, 0.2), b(101), (836, 380, 1.4), (836, 375, 1.5)),
       [("props", "stands"), ("actors", "CROWD_B"), ("stage_edge", dict(y=0.88, monitor=-1, mic=None, blur=9.0)),
        ("pyro_near", None)], blur=5.0, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=4, amount=0.45)))
# 151.1 (bar 101): the scarf wave goes round the ground; Rooney turns the mic and the credit to the fans
add(S_(b(101), "OTS", move(b(101), b(104), (835, 470, 1.15), (835, 520, 1.5)),
       ots([roo_st(), *SIDE()], extra=[FG(b(101))]), wave=(b(101), b(104)), **ANTHEM))
# 155.5 (bar 104): "Hey! Hey!": fists and flags
add(S_(b(104), "OT", move(b(104), b(106), (836, 380, 1.45), (836, 370, 1.55)),
       [("props", "stands"), ("actors", "CROWD_E"), ("stage_edge", dict(y=0.88, monitor=1, mic=None, blur=9.0)),
        ("pyro_near", None)], blur=5.0, grade="crowd", lights=0.0, beams=0.0, scarves=[(b(104), b(106) + 1)],
       sweep=dict(n=4, amount=0.5)))

# ---- outro and the end ---------------------------------------------------------------------------------------------
add(S_(b(106), "OTS", move(b(106), b(109), (835, 560, 2.2), (835, 580, 2.6)), ots([roo_st(), *SIDE()],
       extra=[FG(b(106))]), **ANTHEM))
# 162.8 (bar 109): the hero shot: low, his mates behind him, confetti coming down on the last peak
add(S_(b(109), "OTS", move(b(109), b(113), (830, 655, 6.0), (832, 652, 6.6)),
       ots([A("rio", "rio-ferdinand:shrug", (760, 696), 90, ref="rio-ferdinand:front", blur=2.5, face=(0.9, 1.0)),
            A("mark", "mark-goldbridge:stand", (912, 694), 82, blur=2.5),
            roo_st(look_cam=True)], band=False), blur=5.0, **ANTHEM))
# 168.6 (bar 113): the last word; the smile held
add(S_(b(113), "OTS", move(b(113), b(115), STAGE_CU("mcu"), push(STAGE_CU("mcu"), 1.04)),
       ots([roo_st(look_cam=True, face=(0.5, 1.0))], blur={"maguire": 7, "sesko": 7, "cunha": 7}), blur=6.0,
       **ANTHEM))
# 171.5 (bar 115): the closing stabs: everybody, a hit of light on each
add(S_(b(115), "OTS", move(b(115), 173.70, (835, 580, 2.6), (835, 590, 2.75)), ots([roo_st(), *SIDE()]),
       **ANTHEM))
# 173.7: the button: Keane, a broom in his fist, offers it to Rooney and points him at the confetti; Rio laughs
add(S_(173.70, "OTS", move(173.70, 175.30, (878, 655, 8.0), (878, 655, 8.3)),
       ots([roo_st(face=(0.2, 0.6)),
            A("roy", "roy-keane:stand", (925, 703), 84, dance=0.0,
              hold=[dict(prop="broom", at=(112, 1150), size=1650, behind=True, deg=-6)])],
           band=False, extra=[("props", "floor_confetti")]), blur=6.0, **CALM))
add(S_(175.30, "OTS", move(175.30, SONG_END, (875, 638, 9.5), (875, 637, 9.8)),
       ots([A("rio", "rio-ferdinand:laugh", (815, 704), 92, blur=1.5),
            A("rooney", "wayne-rooney:q34", (875, 703), 82, face=(0.75, -0.6),
              hold=[dict(prop="broom", at=(489, 352), size=300, behind=False, deg=-3)]),
            A("roy", "roy-keane:crossed", (938, 703), 84, dance=0.0)],
           band=False, extra=[("props", "floor_confetti")]), blur=6.0, fade_out=(SONG_END - 0.7, SONG_END),
       **CALM))


# ---------------------------------------------------------------- the crowd shots' people (United Road's helpers)
DR = {"evra": "patrice-evra:front", "carrick": "michael-carrick:front", "bruno": "bruno-fernandes:front",
      "lammens": "senne-lammens:front", "tielemans": "youri-tielemans:front", "amad": "amad-diallo:squad",
      "mount": "mason-mount:squad", "ugarte": "manuel-ugarte:squad", "zirkzee": "joshua-zirkzee:squad",
      "mbeumo": "bryan-mbeumo:squad", "dalot": "diogo-dalot:squad", "martinez": "lisandro-martinez:squad",
      "yoro": "leny-yoro:squad", "dorgu": "patrick-dorgu:squad", "mazraoui": "noussair-mazraoui:squad",
      "holland": "steve-holland:front", "shaw": "luke-shaw:front", "mainoo": "kobbie-mainoo:front",
      "deligt": "matthijs-de-ligt:squad", "neville": "gary-neville:front"}
STAGE_EYES = (960, -260)


def person(who, x, ed, eye_y=430, **kw):
    d = dict(who=who, draw=DR[who], eye=(x, eye_y), ed=ed, screen=True, look_at=STAGE_EYES)
    d.update(kw)
    return d


ROW_X = {1: [960], 2: [620, 1300], 3: [380, 960, 1540], 4: [250, 730, 1190, 1670], 5: [170, 560, 960, 1360, 1750]}


def packed(front, middle=(), back=(), far=()):
    """a crowd shot from the stage: big faces in front, rows behind them, smaller and out of focus"""
    out = [person(w, x, 34, eye_y=270, blur=4.0) for w, x in zip(far, np.linspace(120, 1800, max(1, len(far))))]
    out += [person(w, x, 58, eye_y=322, blur=3.0) for w, x in zip(back, ROW_X.get(len(back), []))]
    out += [person(w, x, 82, eye_y=392, blur=1.6) for w, x in zip(middle, ROW_X.get(len(middle), []))]
    out += [person(w, x, 116, eye_y=472) for w, x in zip(front, ROW_X.get(len(front), []))]
    return out


CROWDS = {
    "CROWD_A": packed(("evra", "carrick"), ("amad", "tielemans", "mount"), ("dalot", "zirkzee", "ugarte", "mbeumo"),
                      ("holland", "lammens", "dorgu", "yoro", "mazraoui", "martinez")),
    "CROWD_B": packed(("bruno", "amad", "evra"), ("mount", "dalot", "zirkzee"), ("ugarte", "carrick", "tielemans", "mbeumo"),
                      ("lammens", "yoro", "mazraoui", "martinez", "dorgu", "holland")),
    "CROWD_C": packed(("tielemans", "mbeumo"), ("evra", "carrick", "amad"), ("bruno", "mount", "dalot", "zirkzee")),
    "CROWD_D": packed(("carrick", "lammens"), ("tielemans", "holland", "evra"), ("dalot", "mount", "amad", "ugarte")),
    "CROWD_E": packed(("evra", "bruno", "amad"), ("mbeumo", "carrick", "dalot", "mount"),
                      ("tielemans", "zirkzee", "ugarte", "lammens", "yoro"),
                      ("holland", "mazraoui", "martinez", "dorgu", "shaw", "mainoo")),
}
for _s in SH:
    _s["layers"] = [(k, CROWDS[v] if k == "actors" and isinstance(v, str) else v) for k, v in _s["layers"]]

# ---------------------------------------------------------------- the show
FOUNTAINS = [(500, 704), (1170, 704)]
FOUNTAINS_BIG = [(700, 704), (970, 704)]
PYRO_H = 120
PYRO = [(b(51), 2.2, 1.0), (b(95), 3.0, 1.3), (b(106), 2.4, 1.0), (b(115), 2.4, 1.3)]
FLAGS = [(b(11, 0.3), b(13))]                       # the pub: flags up at the back of the room
CONFETTI = (b(109, 0.3), 172.6)
STROBE = [(b(94, 0.72), b(95)), (b(114, 0.6), b(115))]
WHIPS = [b(69) - 0.5 / 30]
CAPTIONS = []
STABS = [170.396, 171.139, 171.674, 172.208, 172.951, 173.682]

for _s in SH[1:]:                                    # every cut half a frame early: on the frame nearest its beat
    _s["t"] -= 0.5 / 30
SHOTS = finish(SH, TL["total"])
DRAW = {}
for _s in SHOTS:
    for _k, _v in _s["layers"]:
        if _k == "actors":
            for _a in _v:
                for _key in actors.keys_of(_a):
                    DRAW[_key] = _key


def shot_at(t):
    return _shot_at(SHOTS, t)


actors.install_render()

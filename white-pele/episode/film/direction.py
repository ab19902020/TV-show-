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

PLATES = {**{k: v for k, v in __import__("film.props", fromlist=["UP"]).UP.items()},
          "F": "pub-and-restaurant/united-pub-stage", "FC": "pub-and-restaurant/united-pub-stage-crowd",
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
B01_LAMPS = [dict(at=xy, aim=90 + (xy[0] - 836) / 30, colors=c, swing=18, power=0.20) for xy, c in
             [((390, 56), [WHITE, AMBER, RED]), ((620, 56), [RED, WHITE, AMBER]), ((843, 56), [RED, RED, WHITE]),
              ((1066, 56), [AMBER, RED, WHITE]), ((1282, 56), [WHITE, RED, AMBER])]]
B02_LAMPS = [dict(at=xy, aim=80 + k * 6, colors=[RED, AMBER, WHITE, RED], swing=16, power=0.18) for k, xy in
             enumerate([(404, 63), (634, 111), (731, 77), (1024, 35), (1288, 14)])]
B08_LAMPS = [dict(at=(x, 135), aim=90 + (x - 836) / 25, colors=[WHITE, RED, WHITE, RED, MAGENTA, WHITE], swing=26,
                  power=0.26) for x in (432, 592, 745, 926, 1084, 1240)]
LAMPS = {"F": PUB_LAMPS, "FC": PUB_LAMPS, "OTS": OT_LAMPS, "B01": B01_LAMPS, "B02": B02_LAMPS, "B08": B08_LAMPS}

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
        "rio": ["rio-ferdinand:walk1", "rio-ferdinand:walk3"],     # (walk2's back shoe is cut off on the sheet)
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
    kw.setdefault("drift", 0.9 if str(plate).startswith("B") else 0.5)    # handheld: the operator is there
    if plate == "OT":                                  # the crowd shots: phones flash back at the lens
        kw.setdefault("rec_flash", [t0 + 0.55, t0 + 1.6, t0 + 2.75])
    return stage(t0, plate, cams, layers, **kw)


def wayne(t0, t1):
    """the onsets of "Wayne" sung inside a stretch: where the crash zooms land"""
    from film.timeline import WORDS
    return [w[0] for w in WORDS if w[2] == "wayne" and t0 <= w[0] < t1]


def crash_cams(t0, t1, wide, tight):
    """hold wide, then snap in to tight on each "Wayne" (a crash zoom), easing back out a little between them"""
    hits = wayne(t0, t1)
    ks = [(t0, wide)]
    for i, h in enumerate(hits):
        ks += [(h - 0.04, push(wide, 1.0 + 0.04 * i)), (h + 0.07, push(tight, 1.0 + 0.04 * i))]
    ks.append((t1, push(tight, 1.06 + 0.04 * len(hits))))
    return ks


def move(t0, t1, c0, c1):
    return [(t0, c0), (t1, c1)]


# ================================================================ the upgrade: the pack's sets (props.UP, B01..B10)
# Every set's floor, measured on the plate (1x px): a person's height in plate px where their feet are.
def st_h(y):                                 # ST the matchday street (eye level 505)
    return 2.5 * (y - 505)


def h3(y):                                   # B03 the pub from the stage (eye level 211, the bar stools 0.75 m)
    return 0.98 * (y - 211)


def h4(y):                                   # B04 the courtyard pitch (eye level 375)
    return 1.76 * (y - 375)


def h5(y):                                   # B05 the street outside the pub (eye level 473, the door 2.2 m)
    return 1.104 * (y - 473)


def h6(y):                                   # B06 the tunnel (eye level 400)
    return 0.95 * (y - 400)


def h7(y):                                   # B07 the pitch from low down (eye level 612, the far goal 2.44 m)
    return 3.5 * (y - 612)


def h8(y):                                   # B08 the concert stage (eye level 450; deck 610 at the riser, 806 front)
    return 0.66 * (y - 450)


def h10(y):                                  # B10 the rooftop (eye level 400, the parapet 1.1 m)
    return 1.1 * (y - 400)


R_STAND, R_REACH, R_POINT = "wayne-rooney:perf-stand", "wayne-rooney:perf-reach", "wayne-rooney:perf-point"
R_LEAN, R_BACK, R_KNEEL = "wayne-rooney:perf-lean", "wayne-rooney:perf-back", "wayne-rooney:perf-kneel"
PWALK = ["wayne-rooney:pwalk1", "wayne-rooney:pwalk2", "wayne-rooney:pwalk3", "wayne-rooney:pwalk4"]
BACKWALK = ["wayne-rooney:pwalk-back", "wayne-rooney:pwalk-back-m"]
KIDRUN = ["wayne-rooney:ball-run", "wayne-rooney:ball-ready"]


def roo(draw, feet, h, **kw):
    """Rooney in one of the pack's poses, sized like his standing pose (the same face size in every drawing)"""
    return A("rooney", draw, feet, h, ref=R_STAND, **kw)


# ---------------------------------------------------------------- B01/B02: the pub stage, front and side
ROO1 = ((760, 606), 360)                     # the singer's lane: forward, left of centre
BAND1 = band_at(((930, 548), 300), ((470, 580), 332), ((1232, 580), 332), kit=True)
RIO1_FLOOR = ((300, 935), 560)               # Rio on the pub floor in front of the stage
RIO1_STAGE = ((560, 594), 340)               # Rio up on the stage beside him
ROO2 = ((800, 830), 470)                     # the side view: the singer downstage
BAND2 = band_at(((1180, 552), 290), ((470, 676), 390), ((1395, 640), 370), kit=True)
FLOOR1 = 606                                 # the stage floor at the singer's feet (B01)
BALL1 = 0.0625 * ROO1[1]                     # the ball's radius beside him (22 cm against 1.76 m)


def pub1(front=(), blur=None, extra=(), band=True, hide=()):
    """B01: the band (drummer behind his kit, rear right of centre; guitars wide), whoever is at the front"""
    bl = blur or {}
    bnd = [dict(a, blur=bl.get(a["who"], 0.0)) for a in BAND1 if band and a["who"] not in hide]
    fr = [dict(a, blur=bl.get(a["who"], a.get("blur", 0.0))) for a in front if a["who"] not in hide]
    return [("actors", bnd + fr)] + list(extra)


def pub2(front=(), blur=None, extra=()):
    bl = blur or {}
    bnd = [dict(a, blur=bl.get(a["who"], 0.0)) for a in BAND2]
    return [("actors", bnd + [dict(a, blur=bl.get(a["who"], a.get("blur", 0.0))) for a in front])] + list(extra)


# ---- chorus 1 ---------------------------------------------------------------------------------------------------
# 0.00: the ball rolls in along the boards and stops against his trainer; lights come up with the fade-in
ROLL = dict(keys=[(0.15, 1180, FLOOR1 - BALL1), (1.6, ROO1[0][0] + 108, FLOOR1 - BALL1, 0.0, "out")],
            r=BALL1, floor=FLOOR1, t1=2.5)
add(S_(0.0, "B01", [(0.0, (ROO1[0][0] + 110, 585, 7.5)), (2.2, (ROO1[0][0] + 60, 572, 6.8))],
       pub1([roo(R_STAND, *ROO1)], blur={"sesko": 5.0, "cunha": 5.0, "maguire": 4.0}, extra=[("props", "ball")]),
       ball=ROLL, blur=3.0, dark=lambda t: max(0.0, 0.7 * (1 - t / 2.2)), **CALM))
# 2.2: cut on the first word: he has the mic up and leans into the room, his other hand open to it
add(S_(2.2, "B01", move(2.2, b(1), frame(*ROO1, "mcu", dx=0.05), push(frame(*ROO1, "mcu", dx=0.05), 1.05)),
       pub1([roo(R_REACH, *ROO1, look_cam=True)], blur={"sesko": 6.0, "cunha": 6.0, "maguire": 5.0}),
       blur=4.0, **CALM))
# 4.9 (bar 1): Rio, on the pub floor, hears it and turns to the stage with a delighted grin
add(S_(b(1), "B01", move(b(1), b(2), frame(*RIO1_FLOOR, "ms", dx=0.1), push(frame(*RIO1_FLOOR, "ms", dx=0.1), 1.06)),
       pub1([A("rio", "rio-ferdinand:palms", *RIO1_FLOOR, face=(0.75, 0.9)), roo(R_STAND, *ROO1, blur=5.0)],
            blur={"sesko": 6.0, "cunha": 6.0, "maguire": 6.0}), blur=5.0, **CALM))
# 6.4 (bar 2): the room from the stage: supporters at three depths, a scarf held up, Keane unmoved at the back
add(S_(b(2), "B03", move(b(2), b(4), (836, 480, 1.05), (836, 476, 1.1)),
       [("actors", "CROWD_PUB"),
        ("actors", [A("roy", "roy-keane:folded", (1400, 640), h3(640), dance=0.0)]),
        ("actors", [roo(R_BACK, (230, 1380), 1200, blur=4.0)])],
       blur=1.0, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=3, amount=0.25), rim=0.3,
       rim_color=(1.0, 0.72, 0.45)))
# 9.3 (bar 4): Keane, unmoved
add(S_(b(4), "B03", move(b(4), b(5), frame((1400, 640), h3(640), "mcu"), push(frame((1400, 640), h3(640), "mcu"), 1.04)),
       [("actors", [A("roy", "roy-keane:folded", (1400, 640), h3(640), dance=0.25)])],
       blur=6.0, grade="crowd", lights=0.0, beams=0.0))
# 10.8 (bar 5): Rooney into the lens, "He goes by the name of Wayne Rooney"
add(S_(b(5), "B01", move(b(5), b(7), frame(*ROO1, "mcu", dx=0.03), push(frame(*ROO1, "mcu", dx=0.03), 1.08)),
       pub1([roo(R_STAND, *ROO1, look_cam=True)], blur={"sesko": 5.0, "cunha": 5.0, "maguire": 4.0}),
       blur=4.0, **CALM))
# 13.7 (bar 7): the side of the stage: the singer downstage, the band behind him
add(S_(b(7), "B02", crash_cams(b(7), b(8), (900, 560, 1.45), frame(*ROO2, "mcu", dx=0.03)),
       pub2([roo(R_STAND, *ROO2, look_cam=True)]), blur=0.0, crash=wayne(b(7), b(8)), **CALM))
# 15.2 (bar 8): the drums come in: Maguire's sticks on the kit
add(S_(b(8), "B02", move(b(8), b(9), (1180, 445, 4.4), (1180, 440, 4.7)),
       pub2([roo(R_STAND, *ROO2, blur=8.0)], blur={"sesko": 6.0, "cunha": 4.0}), blur=2.0, **VERSE))
# 16.7 (bar 9): Rio up beside him, palms out to the room: "come on!"
add(S_(b(9), "B01", move(b(9), b(11), (700, 420, 2.0), (690, 412, 2.12)),
       pub1([A("rio", "rio-ferdinand:palms", *RIO1_STAGE, look_cam=True), roo(R_STAND, *ROO1)],
            blur={"sesko": 3.0, "cunha": 3.0, "maguire": 3.0}), blur=1.5, **VERSE))
# 19.6 (bar 11): the room sings it back, scarves going up along the rows
add(S_(b(11), "B03", move(b(11), b(13), (836, 520, 1.22), (836, 516, 1.28)),
       [("actors", "CROWD_PUB")],
       blur=2.0, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=3, amount=0.3), rim=0.3,
       rim_color=(1.0, 0.72, 0.45), scarves_t=b(11, 0.15), vf=dict(label="GOLDBRIDGE  •  THE PUB"),
       drift=1.8))
# 22.5 (bar 13): Rooney plants his feet and leads the room: the side of the stage, the room's fists in front
add(S_(b(13), "B02", move(b(13), b(15), (860, 560, 1.35), (850, 556, 1.45)),
       pub2([roo(R_POINT, *ROO2, look_cam=True)],
            extra=[("fg_fans", dict(y=0.84, n=13, seed=7, blur=5.0, arms=0.9, scale=0.95, rim=0.75))]), **CHORUS))


# ---- the instrumental: toe-taps, then the memory -------------------------------------------------------------------
# 25.5 (bar 15): low on the boards: he keeps the ball up on his right toe on the beat
def keepy_uppy(t0, t1, foot_x, floor, r):
    from studio.film.stage import SONG
    S = SONG()
    ks, t = [], t0
    i = S.beat_index(t0) + 1
    while S.B[i] < t1:
        tb = S.B[i] + 0.5 * S.period
        ks.append((tb, foot_x + 3 * (-1) ** i, floor - r - 4))                     # on the toe
        if i + 1 < len(S.B):
            ks.append(((S.B[i + 1] + 0.5 * S.period + tb) / 2, foot_x + 2 * (-1) ** i, floor - r - 4, 36.0))
        i += 1
    return ks


TOE1 = (ROO1[0][0] + 0.19 * ROO1[1], FLOOR1)        # his right toe (perf-stand's foot at 990, 2010 of 2136 px)
add(S_(b(15), "B01", move(b(15), b(16), (ROO1[0][0] + 20, 520, 3.4), (ROO1[0][0] + 20, 516, 3.6)),
       pub1([roo(R_STAND, *ROO1, tap=dict(at=(830, 2000), r=200, lift=70, spans=[(b(15), b(17))], toe=1))],
            blur={"sesko": 5.0, "cunha": 5.0, "maguire": 5.0}, extra=[("props", "ball")]),
       ball=dict(keys=keepy_uppy(b(15) - 0.4, b(17), *TOE1, BALL1), r=BALL1, floor=FLOOR1), blur=2.0, **VERSE))
# 26.9 (bar 16): Keane, looking down at the technique
add(S_(b(16), "B03", move(b(16), b(17), frame((1400, 640), h3(640), "ms"), push(frame((1400, 640), h3(640), "ms"), 1.05)),
       [("actors", [A("roy", "roy-keane:folded", (1400, 640), h3(640), dance=0.3)])],
       blur=6.0, grade="crowd", lights=0.0, beams=0.0, wipe_out=b(17)))

# 28.4 (bar 17): a scarf wipes across the lens into the memory: the terrace courtyard at dusk, the younger Rooney in
# the red kit (labelled in SOURCES.md: a stylised tribute, not a particular match). The ball comes in off the wall
# and he traps it under his sole
KID4 = ((610, 760), h4(760))
add(S_(b(17), "B04", move(b(17), b(19), (760, 470, 1.2), (740, 470, 1.26)),
       [("actors", [A("kid", "wayne-rooney:ball-ready", *KID4, dance=0.0)]), ("props", "ball")],
       blur=1.0, grade="crowd", wipe_in=b(17),
       ball=dict(keys=[(b(17), 1700, KID4[0][1] - 0.0625 * KID4[1]), (b(17) + 1.1, KID4[0][0] + 0.21 * KID4[1], KID4[0][1] - 0.06 * KID4[1],
                                                 0.0, "out")], r=0.0625 * KID4[1], floor=KID4[0][1]), **QUIET))
# 31.3 (bar 19): side on, tracking with him: he runs with it at his feet across the yard
RUN4 = [(b(19), (150, 700)), (b(21), (1050, 700))]
add(S_(b(19), "B04", move(b(19), b(21), (420, 480, 1.3), (1120, 480, 1.3)),
       [("actors", [A("kid", KIDRUN[0], RUN4[0][1], h4(700), walk=dict(keys=KIDRUN, period=0.5), path=RUN4,
                      ref=KIDRUN[0], dance=0.0)]),
        ("props", "dribble")], blur=1.5, grade="crowd", motion=18.0, **QUIET))
# 34.3 (bar 21): the strike at the chalk goal: the plant, the swing, the ball away to the wall
STRIKE4 = ((1000, 720), h4(720))
add(S_(b(21), "B04", move(b(21), b(21, 0.5), (980, 470, 1.2), (960, 460, 1.26)),
       [("actors", [A("kid", "wayne-rooney:ball-strike", *STRIKE4, dance=0.0,
                      keys=[(b(21), "wayne-rooney:ball-ready"), (b(21, 0.2), "wayne-rooney:ball-strike")],
                      ref="wayne-rooney:ball-ready")]),
        ("props", "ball"), ("props", "strike_flash")],
       blur=1.0, grade="crowd", strike=b(21, 0.2), strike_at=(1000 + 0.36 * STRIKE4[1], 720 - 0.33 * STRIKE4[1]),
       ball=dict(keys=[(b(21), 1000 + 0.3 * STRIKE4[1], 720 - 0.0625 * STRIKE4[1]),
                       (b(21, 0.2), 1000 + 0.3 * STRIKE4[1], 720 - 0.0625 * STRIKE4[1]),
                       (b(21, 0.5), 860, 390, 60.0)], r=0.0625 * STRIKE4[1], floor=720, blur_v=30), **QUIET))
# 35.0: in off the wall, inside the chalk goal
add(S_(b(21, 0.5), "B04", move(b(21, 0.5), b(22), (845, 400, 3.0), (845, 400, 3.3)),
       [("props", "ball")], blur=0.0, grade="crowd",
       ball=dict(keys=[(b(21, 0.5) - 0.2, 760, 520), (b(21, 0.5) + 0.12, 860, 392), (b(22) - 0.05, 930, 452 - 13, 0.0,
                                                                                   "out")],
                 r=13.0, floor=455), **QUIET))
# 35.7 (bar 22): arms spread wide in the yard
CEL4 = ((836, 860), h4(860))
add(S_(b(22), "B04", move(b(22), b(23), frame(*CEL4, "ms"), push(frame(*CEL4, "ms"), 1.08)),
       [("actors", [A("kid", "wayne-rooney:ball-celebrate", *CEL4, look_cam=True, face=(0.8, 1.0))])],
       blur=2.0, grade="crowd", **QUIET))

# ---- verse 1: back to the pub, out into the street ------------------------------------------------------------------
# 37.1 (bar 23): the swing of the boot becomes Šeško's strum: back in the pub
add(S_(b(23), "B01", move(b(23), b(23, 0.58), frame(((470, 580)), 332, "mcu", dy=0.12),
                      push(frame(((470, 580)), 332, "mcu", dy=0.12), 1.06)),
       pub1([roo(R_STAND, *ROO1, blur=7.0)], blur={"cunha": 7, "maguire": 7}), blur=3.0, **VERSE))
# 37.9: "From Croxteth streets to theatre dreams": he points the way to the door
add(S_(b(23, 0.58), "B01", move(b(23, 0.58), b(25), frame(*ROO1, "ms", dx=0.05), push(frame(*ROO1, "ms", dx=0.05), 1.06)),
       pub1([roo(R_POINT, *ROO1, look_cam=True)], blur={"sesko": 5, "cunha": 5, "maguire": 4}), blur=3.0, **VERSE))


def walk5(who, x0, y, t0, t1, period=0.5, keys=None, **kw):
    """walking left along the street (B05), mirrored side-view keys, a step a beat, stride-matched"""
    return walker(who, keys or WALK5[who], [(t0, (x0, y)), (t1, (x0 - 1, y))], h5(y), period=period, mirror=True, **kw)


WALK5 = dict(WALK, rooney=PWALK)
# 40.0 (bar 25): out of the corner pub and along the street: Rooney leading, Rio at his shoulder, the others behind
add(S_(b(25), "B05", move(b(25), b(28), (1150, 560, 1.5), (650, 570, 1.5)),
       [("actors", [walk5("roy", 1520, 690, b(25, 0.9), b(28)), walk5("gary", 1460, 694, b(25, 0.65), b(28)),
                    walk5("mark", 1400, 698, b(25, 0.4), b(28)), walk5("rio", 1330, 702, b(25, 0.15), b(28)),
                    walk5("rooney", 1270, 708, b(25), b(28))])],
       blur=0.0, grade="crowd", **QUIET))
# 44.4 (bar 28): with Rooney and Rio, walking and singing ("Number ten with fire inside")
TWO5 = [(b(28), (1450, 905)), (b(30), (1449, 905))]
add(S_(b(28), "B05", [(b(28), (1330, 650, 2.0)), (b(30), (700, 650, 2.0))],
       [("actors", [walker("rio", WALK["rio"], [(b(28), (1700, 858)), (b(30), (1699, 858))], h5(858), period=1.0,
                           mirror=True, blur=1.0),
                    walker("rooney", PWALK, TWO5, h5(905), period=1.0, mirror=True)])],
       blur=3.0, grade="crowd", **QUIET))
# 47.3 (bar 30): Neville checks his clipboard while Goldbridge marches past far too keenly
add(S_(b(30), "B05", move(b(30), b(31), (900, 560, 2.4), (930, 560, 2.5)),
       [("actors", [walker("mark", WALK["mark"], [(b(30), (1300, 712)), (b(31), (1299, 712))], h5(712), period=0.35,
                           mirror=True),
                    A("gary", "gary-neville:clipboard", (900, 1260), 900, ref="gary-neville:stand",
                      face=(-0.4, -0.2))])],
       blur=4.0, grade="crowd", **QUIET))
# 48.8 (bar 31): the mural: THE WHITE PELE painted on the gable (one phrase)
add(S_(b(31), "MW", move(b(31), b(33), (700, 470, 1.3), (640, 470, 1.4)),
       [("props", "mural_text"), ("actors", [roo(R_STAND, (300, 805), 560, look_cam=True)])],
       grade="crowd", **QUIET))
# 51.6 (bar 33): supporters outside the pub cheer them on as they pass ("First time strike, no second thought")
add(S_(b(33), "B05", move(b(33), b(35), (520, 560, 1.6), (440, 560, 1.66)),
       [("actors", "CROWD_ST"),
        ("actors", [walk5("rio", 1000, 716, b(33), b(35)), walk5("rooney", 900, 724, b(33), b(35))])],
       blur=0.0, grade="crowd", vf=dict(label="GOLDBRIDGE  •  MATCHDAY"), drift=1.8, **QUIET))
# 54.6 (bar 35): on Sir Matt Busby Way Goldbridge poses under the street sign for a camera that isn't there; Rio
# walks in to fetch him...
MARK_SIGN = (600, 700)
add(S_(b(35), "ST", move(b(35), b(36, 0.5), (520, 520, 1.5), (540, 520, 1.56)),
       [("props", "street_sign"),
        ("actors", [A("mark", "mark-goldbridge:front", MARK_SIGN, st_h(700), look_cam=True, face=(0.6, 1.0)),
                    walker("rio", WALK["rio"], [(b(35, 0.1), (-260, 712)), (b(36, 0.5), (230, 712))], st_h(712),
                           period=1.0)])],
       blur=1.5, grade="crowd", **QUIET))
# 56.7: ...and they head off up the road together, both walking
add(S_(b(36, 0.5), "ST", move(b(36, 0.5), b(37), (600, 520, 1.5), (760, 520, 1.5)),
       [("props", "street_sign"),
        ("actors", [walker("mark", WALK["mark"], [(b(36, 0.5), MARK_SIGN), (b(37), (601, 700))], st_h(700)),
                    walker("rio", WALK["rio"], [(b(36, 0.5), (330, 712)), (b(37), (331, 712))], st_h(712))])],
       blur=1.5, grade="crowd", **QUIET))
# 57.4 (bar 37): above the city: a rooftop, the stadium glowing beyond; he sings to it alone
ROOF = ((640, 790), h10(790))
add(S_(b(37), "B10", move(b(37), b(39), (836, 520, 1.25), (800, 540, 1.4)),
       [("actors", [roo(R_REACH, *ROOF)])], blur=0.0, grade="crowd", **QUIET))
# 60.4 (bar 39): "...we lose our minds that day": closer, turned to the stadium
add(S_(b(39), "B10", move(b(39), b(41), frame(*ROOF, "mcu", dx=0.12), push(frame(*ROOF, "mcu", dx=0.12), 1.05)),
       [("actors", [roo(R_LEAN, *ROOF)])], blur=5.0, grade="crowd", **QUIET))
# 63.3 (bar 41): Old Trafford at dusk, the crowd arriving; "When he turns and lets one fly"
add(S_(b(41), "EXT", move(b(41), b(44), (836, 560, 1.0), (836, 520, 1.25)),
       [("actors", [walker("mark", WALK["mark"], [(b(41), (240, 780)), (b(44), (241, 780))], 120),
                    walker("roy", WALK["roy"], [(b(41), (300, 790)), (b(44), (301, 790))], 128),
                    walker("rio", WALK["rio"], [(b(41), (380, 800)), (b(44), (381, 800))], 140),
                    walker("rooney", PWALK, [(b(41), (460, 812)), (b(44), (461, 812))], 128)]),
        ("props", "passers")], passers=dict(n=12, y=0.95, speed=0.05, seed=21, scarves=True),
       grade="crowd", **QUIET))
# 67.6 (bar 44): the concourse, red light, flags going in; "You just know it's top bin time"
add(S_(b(44), "EXT2", move(b(44), b(47), (836, 520, 1.3), (836, 560, 1.7)),
       [("actors", [A("mark", "mark-goldbridge:back", (760, 720), 120), A("rio", "rio-ferdinand:back", (840, 735), 150),
                    A("rooney", "wayne-rooney:pwalk-back", (920, 740), 128, ref="wayne-rooney:pwalk-back"),
                    A("roy", "roy-keane:folded", (1000, 730), 140, dance=0.2)]),
        ("props", "passers")], passers=dict(n=10, y=0.95, speed=0.03, seed=5, scarves=True, flags=True),
       grade="crowd", **QUIET))


# ---------------------------------------------------------------- the stadium: B06 tunnel, B08 stage, B09 reverse
ROO8 = ((836, 772), h8(772))                 # the singer's mark, front centre
RIO8 = ((440, 712), h8(712))                 # the wings: Rio stage left, Goldbridge and Keane stage right
MARK8 = ((1170, 706), h8(706))
ROY8 = ((1275, 724), h8(724))
BAND8 = band_at(((836, 612), h8(612)), ((560, 664), h8(664)), ((1112, 664), h8(664)), kit=True)


def st8(front=(), extra=(), blur=None, band=True, hide=()):
    """B08: the band (the drummer on the riser with his kit, guitars either side), the front, the full stands"""
    bl = blur or {}
    bnd = [dict(a, blur=bl.get(a["who"], 0.0)) for a in BAND8 if band and a["who"] not in hide]
    fr = [dict(a, blur=bl.get(a["who"], a.get("blur", 0.0))) for a in front if a["who"] not in hide]
    return [("props", "stands"), ("actors", bnd + fr)] + list(extra)


def wings():
    return [A("rio", "rio-ferdinand:palms", *RIO8), A("mark", "mark-goldbridge:stand", *MARK8, look_cam=False),
            A("roy", "roy-keane:folded", *ROY8, dance=0.2)]


FG = lambda t0, n=15: ("fg_fans", dict(y=0.82, n=n, seed=int(t0 * 7) % 97, blur=5.0, arms=0.9, scale=0.9,   # noqa
                                         rim=0.8))
WIDE8 = (836, 600, 1.42)
CU8 = lambda size, dx=0.04: frame(*ROO8, size, dx=dx)                                    # noqa: E731

# ---- chorus 2 ----------------------------------------------------------------------------------------------------
# 71.9 (bar 47): the tunnel from behind them: walking away towards the light and the pitch (smaller as they go)
TUN6 = [(b(47), (760, 935)), (b(50), (790, 700))]
add(S_(b(47), "B06", move(b(47), b(50), (836, 560, 1.12), (836, 545, 1.25)),
       [("actors", [A("rio", "rio-ferdinand:back", (930, 940), h6(940), bob=dict(phase=0.5),
                      path=[(b(47), (930, 940)), (b(50), (900, 712))], hpath=[(b(47), h6(940)), (b(50), h6(712))]),
                    A("rooney", BACKWALK[0], TUN6[0][1], h6(935), ref=BACKWALK[0], walk=dict(keys=BACKWALK, period=1.0),
                      path=TUN6, hpath=[(b(47), h6(935)), (b(50), h6(700))])])],
       blur=0.0, grade="crowd", light_end=dict(color=(1.0, 0.95, 0.86), amount=0.3), **QUIET))
# 76.3 (bar 50): out on the stage from behind him: the mic up to the stands, the whole ground in front of him
add(S_(b(50), "B09", move(b(50), b(51), (836, 470, 1.15), (836, 480, 1.25)),
       [("props", "stands"), ("actors", [roo(R_BACK, (700, 1330), 1080)])], blur=0.0, grade="crowd",
       lights=0.0, beams=0.0, crowd_jump=1.2))
# 77.8 (bar 51): the front of the stage: the band playing, the stands full
add(S_(b(51), "B08", move(b(51), b(52), (836, 470, 1.0), (836, 520, 1.12)), st8(extra=[FG(b(51)), ("pyro", None)]), **CHORUS))
# 79.2 (bar 52): Rooney walks out to his mark at the front of the stage
add(S_(b(52), "B08", move(b(52), b(53), (760, 640, 3.0), (820, 650, 3.3)),
       st8([walker("rooney", PWALK, [(b(52), (560, 772)), (b(53), (836, 772))], h8(772), period=0.5), *wings()],
           blur={"maguire": 2.0, "sesko": 2.0, "cunha": 2.0}), blur=2.0, **CHORUS))
# 80.7 (bar 53): "He goes by the name of Wayne Rooney"
add(S_(b(53), "B08", move(b(53), b(55), CU8("mcu"), push(CU8("mcu"), 1.06)),
       st8([roo(R_STAND, *ROO8, look_cam=True)], blur={"maguire": 6.0, "sesko": 6.0, "cunha": 6.0}), blur=6.0,
       lower=dict(t0=b(53, 0.15), t1=b(55) - 0.1, top="WAYNE ROONEY", sub="THE WHITE PELÉ  •  LIVE AT OLD TRAFFORD"),
       **CHORUS))
# 83.6 (bar 55): the name, close
add(S_(b(55), "B08", crash_cams(b(55), b(57), CU8("mcu"), CU8("cu")),
       st8([roo(R_STAND, *ROO8, look_cam=True)], blur={"maguire": 8.0, "sesko": 8.0, "cunha": 8.0}), blur=7.0,
       crash=wayne(b(55), b(57)), **CHORUS))
# 86.6 (bar 57): the crowd sings his name back and shouts "Hey!"
add(S_(b(57), "OT", move(b(57), b(59), (836, 380, 1.4), (836, 380, 1.47)),
       [("props", "stands"), ("actors", "CROWD_B"),
        ("stage_edge", dict(y=0.88, monitor=1, mic=None, blur=9.0)), ("pyro_near", None)],
       blur=5.0, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=3, amount=0.4), rim=0.35,
       rim_color=(1.0, 0.85, 0.75), **{k: v for k, v in CHORUS.items() if k not in ("lights", "beams")}))
# 89.5 (bar 59): the stage, everyone on it
add(S_(b(59), "B08", move(b(59), b(61), WIDE8, push(WIDE8, 1.08)), st8([roo(R_STAND, *ROO8), *wings()],
       extra=[FG(b(59))]), **CHORUS))
# 92.4 (bar 61): stage left: Rio's scarf up, Goldbridge beside him, firing up the front rows
add(S_(b(61), "B08", move(b(61), b(63), frame(*RIO8, "ms", dx=0.05), push(frame(*RIO8, "ms", dx=0.05), 1.12)),
       st8([A("rio", "rio-ferdinand:scarf", *RIO8, look_cam=True, face=(0.8, 1.0))], band=False),
       blur=3.0, vf=dict(label="GOLDBRIDGE  •  ON THE STAGE"), drift=1.8, **CHORUS))

# ---- verse 2 -----------------------------------------------------------------------------------------------------
# 95.3 (bar 63): "Hey!" and "Volley smash in the derby night": he points out over them
add(S_(b(63), "B08", move(b(63), b(65), CU8("ms"), push(CU8("ms"), 1.08)),
       st8([roo(R_POINT, *ROO8, look_cam=True)], blur={"maguire": 5.0, "sesko": 5.0, "cunha": 5.0}), blur=4.0,
       **VERSE))
# 98.2 (bar 65): the overhead kick, under the floodlights (the red kit: the tribute again). The run in, eyes on the
# ball dropping from the right
KICK7 = 1015.0                               # where he takes off (x); the ground under him at y 760
G7 = 760


def kid7(draw, x, y=G7, **kw):
    return A("kid", draw, (x, y), h7(G7), ref="wayne-rooney:ball-ready", dance=0.0, **kw)


add(S_(b(65), "B07", move(b(65), b(66, 0.6), (760, 520, 1.3), (860, 520, 1.38)),
       [("props", "stands"),
        ("actors", [A("kid", KIDRUN[0], (300, G7), h7(G7), walk=dict(keys=KIDRUN, period=0.5),
                      path=[(b(65), (300, G7)), (b(66, 0.4), (KICK7 - 60, G7)), (b(66, 0.6), (KICK7, G7))],
                      ref="wayne-rooney:ball-ready", dance=0.0,
                      keys=[(b(65), KIDRUN[0]), (b(66, 0.4), "wayne-rooney:ball-ready")])]),
        ("props", "ball")],
       blur=1.0, grade="crowd", crowd_jump=0.8,
       ball=dict(keys=[(b(65), 1900, 60), (b(66, 0.6), 1720, -10, 0.0)], r=0.0625 * h7(G7), floor=G7), **QUIET))
# 100.4: takeoff, over, the strike upside down (102.0), the landing on his hands, up to celebrate
AIR = b(66, 0.6)                             # off the ground
HIT = 102.0                                  # boot meets ball (the line's "strike")
BOOT7 = (1470, 130)                          # where his raised boot is, upside down, at the strike
add(S_(AIR, "B07", [(AIR, (920, 470, 1.3)), (HIT, (950, 380, 1.15)), (b(68), (960, 430, 1.22))],
       [("props", "stands"),
        ("actors", [kid7("wayne-rooney:ball-strike", KICK7,
                         keys=[(AIR, "wayne-rooney:ball-strike"), (AIR + 0.45, "wayne-rooney:ball-bicycle"),
                               (HIT + 0.32, "wayne-rooney:ball-land")],
                         path=[(AIR, (KICK7, G7)), (AIR + 0.45, (KICK7 + 20, G7 - 150)), (HIT, (KICK7 + 30, G7 - 200)),
                               (HIT + 0.32, (KICK7 + 60, G7))],
                         ground=G7)]),
        ("props", "ball"), ("props", "strike_flash")],
       blur=0.8, grade="crowd", crowd_jump=1.0, strike=HIT, strike_at=BOOT7,
       ball=dict(keys=[(AIR - 0.4, 1760, -60), (HIT, BOOT7[0] - 20, BOOT7[1] + 10, 30.0),
                       (HIT + 0.6, 1160, 600, 0.0)], r=0.0625 * h7(G7), floor=G7, blur_v=40), **QUIET))
# 102.6 (bar 68): the far net bulges; the ground goes up; arms out
add(S_(b(68), "B07", move(b(68), b(68, 0.45), (1150, 560, 2.8), (1152, 560, 3.05)),
       [("props", "stands"), ("props", "goal_net")], blur=2.5, grade="crowd", crowd_jump=1.8,
       net=dict(t=b(68) + 0.2, at=(1157, 618)), **QUIET))
add(S_(b(68, 0.45), "B07", move(b(68, 0.45), b(69), frame((900, 800), h7(800), "ms"),
                              push(frame((900, 800), h7(800), "ms"), 1.08)),
       [("props", "stands"), ("actors", [A("kid", "wayne-rooney:ball-celebrate", (900, 800), h7(800),
                                          look_cam=True, face=(0.8, 1.0))])],
       blur=3.0, grade="crowd", crowd_jump=1.8, scarves=[(b(68, 0.45), b(69) + 1)], **QUIET))
# 104.1 (bar 69): the ball's arc becomes the camera's sweep across the scarves: "Old Trafford shaking left and right"
add(S_(b(69), "OT", [(b(69), (300, 400, 2.4)), (b(70), (1350, 410, 2.4)), (b(71), (700, 400, 2.3))],
       [("props", "stands")], blur=1.5, grade="crowd", lights=0.0, beams=0.0, scarves=[(b(69) - 1, b(71) + 1)],
       crowd_jump=1.6, motion=30.0))
# 107.0 (bar 71): "Captain's armband on his sleeve"
add(S_(b(71), "B08", move(b(71), b(73), CU8("cu"), push(CU8("cu"), 1.05)),
       st8([roo(R_STAND, *ROO8, look_cam=True)], blur={"maguire": 8.0, "sesko": 8.0, "cunha": 8.0}), blur=7.0,
       **VERSE))
# 109.9 (bar 73): stage right, under Keane's folded arms, a foot is tapping...
TAP8 = dict(at=(230, 1950), r=190, lift=160, spans=[(b(73), b(74, 0.45)), (b(75, 0.55), b(76))], toe=-1)
KEANE_FEET = (ROY8[0][0], ROY8[0][1] - 0.16 * ROY8[1], 12.0)
add(S_(b(73), "B08", move(b(73), b(74), KEANE_FEET, push(KEANE_FEET, 1.04)),
       st8([A("roy", "roy-keane:folded", *ROY8, tap=TAP8, dance=0.0)], band=False), blur=3.0, **VERSE))
# 111.4 (bar 74): ...Rio spots it; Keane stops dead and glares at him; Rio looks away
add(S_(b(74), "B08", move(b(74), b(75, 0.5), (1210, 640, 4.6), (1210, 640, 4.8)),
       st8([A("rio", "rio-ferdinand:palms", (1130, 718), h8(718)),
            A("roy", "roy-keane:folded", *ROY8, dance=0.0, tap=TAP8)], band=False), blur=4.0, **VERSE))
# 113.6: the moment Rio looks away, the foot goes again
add(S_(b(75, 0.5), "B08", move(b(75, 0.5), b(76), KEANE_FEET, push(KEANE_FEET, 1.03)),
       st8([A("roy", "roy-keane:folded", *ROY8, tap=TAP8, dance=0.0)], band=False), blur=3.0, **VERSE))
# 114.4 (bar 76): from behind him, the crowd singing it back: "England's hope and United's pride"
add(S_(b(76), "OT", move(b(76), b(78), (836, 420, 1.3), (836, 410, 1.38)),
       [("props", "stands"), ("actors", "CROWD_C")],
       blur=4.0, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=3, amount=0.35)))
# 117.3 (bar 78): "Goals and glory side by side": Rooney and the band
add(S_(b(78), "B08", move(b(78), b(80), (836, 640, 3.0), (836, 640, 3.25)), st8([roo(R_STAND, *ROO8, look_cam=True)]),
       blur=1.0, **VERSE))

# ---- the breakdown: the drums stop -----------------------------------------------------------------------------
SPOT = dict(at="rooney", r=60, dark=0.62, tall=1.6)
add(S_(b(80), "B08", move(b(80), b(82), (836, 600, 1.9), (836, 610, 2.15)),
       st8([roo(R_STAND, *ROO8)], extra=[("props", "phones")]), spot=SPOT, **CALM))
# 123.1 (bar 82): Goldbridge comes up with his tiny trophy to crown him; Rooney eyes it and sings on
add(S_(b(82), "B08", move(b(82), b(84), frame(*ROO8, "ms", dx=0.22), push(frame(*ROO8, "ms", dx=0.22), 1.05)),
       st8([roo(R_STAND, *ROO8, look_cam=True)], band=False,
           extra=[("actors", [A("mark", "mark-goldbridge:cheer", (1390, 1250), 600, screen=True, still_face=True,
                                blur=1.0, hold=[dict(prop="trophy", at=(690, 846), size=34, behind=True,
                                                     wobble=4.0)])])]),
       blur=3.0, spot=dict(SPOT, r=240, dark=0.4), **CALM))
# 126.0 (bar 84): the crowd swaying, phones up
add(S_(b(84), "OT", move(b(84), b(86), (836, 380, 1.5), (836, 375, 1.56)),
       [("props", "stands"), ("props", "phones"), ("actors", "CROWD_D"),
        ("stage_edge", dict(y=0.9, monitor=-1, mic=None, blur=9.0))],
       blur=5.0, grade="crowd", lights=0.0, beams=0.0, crowd_tone=0.55, crowd_jump=0.4))
# 128.9 (bar 86): "He led the line and forged ahead": down on one knee at the edge of the stage
add(S_(b(86), "B08", move(b(86), b(88), frame(*ROO8, "ms", dx=0.05), push(frame(*ROO8, "ms", dx=0.05), 1.1)),
       st8([roo(R_KNEEL, *ROO8)], blur={"maguire": 6, "sesko": 6, "cunha": 6}), blur=5.0, spot=SPOT, **CALM))

# ---- chorus 3 ----------------------------------------------------------------------------------------------------
# 132.0 (bar 88): from behind Rooney: the crowd in layers, the front singing, the stands pulsing
add(S_(b(88), "OT", move(b(88), b(91), (836, 400, 1.15), (836, 410, 1.3)),
       [("props", "stands"), ("actors", "CROWD_E")],
       blur=3.5, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=4, amount=0.4)))
add(S_(b(91), "B08", move(b(91), b(93), CU8("mcu"), push(CU8("mcu"), 1.06)),
       st8([roo(R_STAND, *ROO8, look_cam=True)], blur={"maguire": 6, "sesko": 6, "cunha": 6}), blur=6.0, **CHORUS))
# 139.3 (bar 93): the reverse: him and Rio from behind, the whole ground singing at them
add(S_(b(93), "B09", move(b(93), b(95), (836, 520, 1.25), (836, 520, 1.32)),
       [("props", "stands"),
        ("actors", [A("rio", "rio-ferdinand:back", (1150, 1150), 680, blur=1.0), roo(R_BACK, (720, 1180), 860)])],
       blur=0.0, grade="crowd", lights=0.0, beams=0.0, crowd_jump=1.4))
# 142.3 (bar 95): everything
add(S_(b(95), "B08", move(b(95), b(96), (836, 590, 1.3), (836, 605, 1.48)), st8([roo(R_STAND, *ROO8), *wings()],
       extra=[FG(b(95)), ("pyro", None)]), **ANTHEM))
add(S_(b(96), "B08", crash_cams(b(96), b(97), CU8("mcu"), CU8("cu")),
       st8([roo(R_STAND, *ROO8, look_cam=True)], blur={"maguire": 8, "sesko": 8, "cunha": 8}), blur=7.0,
       crash=wayne(b(96), b(97)), **ANTHEM))
add(S_(b(97), "B08", move(b(97), b(98), frame(*RIO8, "full", dx=0.1), push(frame(*RIO8, "full", dx=0.1), 1.06)),
       st8([A("rio", "rio-ferdinand:palms", *RIO8, face=(0.9, 1.0), look_cam=True)], band=False), blur=4.0,
       **ANTHEM))
add(S_(b(98), "B08", move(b(98), b(99), frame(MARK8[0], MARK8[1], "cu", dy=-0.04),
                         push(frame(MARK8[0], MARK8[1], "cu", dy=-0.04), 1.06)),
       st8([A("mark", "mark-goldbridge:shouting", *MARK8, ref="mark-goldbridge:stand", look_cam=True)], band=False),
       blur=6.0, vf=dict(label="GOLDBRIDGE  •  SELFIE CAM"), drift=2.2, **ANTHEM))
# 146.8 (bar 99): Keane, arms folded... and on the crash he claps. Once. Then the arms fold again
CLAP = 149.243
add(S_(b(99), "B08", move(b(99), b(100, 0.2), frame(*ROY8, "ms"), push(frame(*ROY8, "ms"), 1.08)),
       st8([A("roy", "roy-keane:folded", *ROY8, dance=0.0,
              keys=[(b(99), "roy-keane:folded"), (CLAP - 0.12, "roy-keane:clap"), (CLAP + 0.45, "roy-keane:folded")],
              look_cam=True)],
               band=False, extra=[("props", "strike_flash")]), blur=5.0, strike=CLAP,
       strike_at=(ROY8[0][0] + 0.05 * ROY8[1], ROY8[0][1] - 0.62 * ROY8[1]), **ANTHEM))
add(S_(b(100, 0.2), "OT", move(b(100, 0.2), b(101), (836, 380, 1.4), (836, 375, 1.5)),
       [("props", "stands"), ("actors", "CROWD_B"), ("stage_edge", dict(y=0.88, monitor=-1, mic=None, blur=9.0)),
        ("pyro_near", None)], blur=5.0, grade="crowd", lights=0.0, beams=0.0, sweep=dict(n=4, amount=0.45)))
# 151.1 (bar 101): the scarf wave goes round the ground; Rooney turns the mic and the credit to the fans
add(S_(b(101), "B08", move(b(101), b(104), (836, 540, 1.12), (836, 590, 1.38)),
       st8([roo(R_POINT, *ROO8), *wings()], extra=[FG(b(101))]), wave=(b(101), b(104)), **dict(ANTHEM, haze=0.25)))
# 155.5 (bar 104): "Hey! Hey!": fists and flags
add(S_(b(104), "OT", move(b(104), b(106), (836, 380, 1.45), (836, 370, 1.55)),
       [("props", "stands"), ("actors", "CROWD_E"), ("stage_edge", dict(y=0.88, monitor=1, mic=None, blur=9.0)),
        ("pyro_near", None)], blur=5.0, grade="crowd", lights=0.0, beams=0.0, scarves=[(b(104), b(106) + 1)],
       sweep=dict(n=4, amount=0.5)))

# ---- outro and the end ---------------------------------------------------------------------------------------------
add(S_(b(106), "B08", move(b(106), b(109), (836, 600, 1.38), (836, 612, 1.56)), st8([roo(R_STAND, *ROO8), *wings()],
       extra=[FG(b(106)), ("pyro", None)]), **ANTHEM))
# 162.8 (bar 109): the hero shot: from behind him, mic up to the whole ground on the last big phrase; Rio beside him
# with his scarf up; the confetti comes down on the stands
add(S_(b(109), "B09", move(b(109), b(113), (836, 500, 1.15), (836, 470, 1.3)),
       [("props", "stands"),
        ("actors", [A("rio", "rio-ferdinand:back", (1190, 1140), 660, blur=0.8), roo(R_BACK, (720, 1190), 880)])],
       blur=0.0, grade="crowd", lights=0.0, beams=0.0, crowd_jump=1.8, scarves=[(b(110), b(113))]))
# 168.6 (bar 113): the last word; the smile held
add(S_(b(113), "B08", move(b(113), b(115), CU8("mcu"), push(CU8("mcu"), 1.04)),
       st8([roo(R_STAND, *ROO8, look_cam=True, face=(0.5, 1.0))], blur={"maguire": 7, "sesko": 7, "cunha": 7}),
       blur=6.0, confetti=False, **ANTHEM))
# 171.5 (bar 115): the closing stabs: everybody, a hit of light on each
add(S_(b(115), "B08", move(b(115), 173.70, (836, 600, 1.42), (836, 606, 1.52)), st8([roo(R_STAND, *ROO8), *wings()], extra=[("pyro", None)]),
       **ANTHEM))
# 173.7: the button: Keane looks at the confetti on the floor, and sweeps. A short, determined patch
BROOM = dict(prop="cut:broom", at=(1000, 830), behind=True, sweep=(9.0, 1.6, 173.95))
SWEPT = (ROY8[0][0] + 0.10 * ROY8[1], ROY8[0][0] - 0.65 * ROY8[1], ROY8[0][1] - 18, ROY8[0][1] + 20, 173.95, 175.3)
add(S_(173.70, "B08", move(173.70, 175.30, frame(*ROY8, "ms", dx=-0.1), push(frame(*ROY8, "ms", dx=-0.1), 1.04)),
       st8([A("roy", "roy-keane:broom-hand", *ROY8, dance=0.0, hold=[BROOM])], band=False,
           extra=[("props", "floor_confetti")]), blur=3.0, swept=SWEPT, confetti=False, **CALM))
# 175.3: Rooney gives him a sideways look, Rio is bent double laughing; Keane stares down the lens... and puts
# his hand over it. Black
add(S_(175.30, "B08", move(175.30, SONG_END, (1110, 650, 3.3), (1110, 648, 3.42)),
       st8([A("rio", "rio-ferdinand:laughbent2", (935, 728), h8(728), blur=0.8),
            roo(R_STAND, (1095, 742), h8(742)),
            A("roy", "roy-keane:broom-hand", *ROY8, dance=0.0, look_cam=True, hold=[dict(BROOM, sweep=(9.0, 1.6, 175.3))])],
           band=False, extra=[("props", "floor_confetti")]), blur=2.0, swept=SWEPT, confetti=False,
       lens_hand=(SONG_END - 1.0, SONG_END - 0.15), **CALM))


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


FAN = "white-pele-supporters:fan"


def fans(spec, hf):
    """the pack's supporters on a plate: (who, n, x, y[, mirror]) each, sized by the set's height-for-depth hf"""
    return [A(w, f"{FAN}{n}", (x, y), hf(y), mirror=bool(m[0]) if m else False) for w, n, x, y, *m in spec]


CROWDS = {
    # the pub from the stage (B03): three depths, each supporter their own gesture and timing
    "CROWD_PUB": fans([("fan4", 4, 560, 520), ("fan3b", 3, 900, 516, 1), ("fan6", 6, 1240, 522),
                       ("fan5", 5, 720, 616), ("fan2b", 2, 1080, 612, 1),
                       ("fan1", 1, 920, 730)], h3),
    # outside the pub (B05): on the back of the pavement as the group goes by
    "CROWD_ST": fans([("fan2", 2, 140, 668), ("fan5", 5, 330, 664), ("fan3", 3, 520, 668), ("fan6", 6, 690, 662)], h5),
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
FOUNTAINS = [(250, 802), (1420, 802)]               # B08: the front corners of the stage
FOUNTAINS_BIG = [(620, 802), (1050, 802)]
PYRO_H = 260
PYRO = [(b(51), 2.2, 1.0), (b(95), 3.0, 1.3), (b(106), 2.4, 1.0), (b(115), 2.4, 1.3)]
FLAGS = [(b(11, 0.3), b(13))]                       # the pub: flags up at the back of the room
CONFETTI = (b(109, 0.3), 172.6)
STROBE = [(b(94, 0.72), b(95)), (b(114, 0.6), b(115))]
WHIPS = [b(69) - 0.5 / 30]
CAPTIONS = []
STABS = [170.396, 171.139, 171.674, 172.208, 172.951, 173.682]

# Optional director upgrade, kept separate from Claude's original shot design.
# Adds five short band close-ups, Goldbridge's more animated selfie, and light cues.
from film import upgrade as director_upgrade
director_upgrade.apply(globals())

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

"""The shot list of The Undercard. Every shot is a camera in one of the pack's seven sets (1x plate px) with the
people and props of that moment drawn at true scale (film/actors.py: s["cast"]); times come from the dialogue
edit's marks (film/timeline.py), so the picture follows the voices.

Cameras: cam = (cx, cy, zoom), zoom 1 = the set's full width. on(x, y, who) frames a person standing at (x, y): frac
is how much of their height fills the frame (0.5 a medium close-up, 0.9 a full figure), up shifts the frame up.
Sets: P press area, B loading bay, C corridor, D dressing room, A arena wide, R inside the ring, S ringside seats."""
import hashlib
import json
import os
from pathlib import Path

from studio.film import ep
from studio.film.shots import Marks, card, finish, shot_at as _shot_at, world

from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt, we = T.m, T.ls, T.le, T.wt, T.we

PLATES = {"P": "boxing/press-area", "B": "boxing/loading-bay", "C": "boxing/corridor", "D": "boxing/dressing-room",
          "A": "boxing/arena-wide", "R": "boxing/ring-side", "S": "boxing/ringside",
          "E": "boxing/dressing-room"}                  # E: Dana's blue-corner room (film/props.py plate_image)
# perspective of each set: plate px per cm = (y - horizon) * k at floor height y
PPC = {"P": (400, 0.0100), "B": (470, 0.0204), "C": (356, 0.0082), "D": (350, 0.0113), "A": (514, 0.0097),
       "R": (289, 0.0065), "S": (640, 0.0113), "E": (350, 0.0113)}
# what stands in front of the people: the arena's near ring rope and corner posts
OCCL = {"A": {"ropes": [[(150, 646), (1530, 646), (1530, 664), (150, 664)],
                        [(146, 466), (190, 466), (190, 702), (146, 702)], [(262, 486), (306, 486), (306, 674), (262, 674)],
                        [(1368, 486), (1414, 486), (1414, 674), (1368, 674)],
                        [(1486, 466), (1532, 466), (1532, 702), (1486, 702)]]}}
CM = {"eddie": 191, "dana": 170, "tyson": 206, "joshua": 198, "announcer": 175, "referee": 180, "attendant": 160,
      "security": 183}
# press camera flashes popping in the crowd: (region in 1x plate px, flashes a second, seed)
CROWD_FLASH = {"A": [((20, 40, 1650, 470), 9.0, 2)], "S": [((0, 0, 1672, 210), 3.0, 5)]}
TITLE = (("THE UNDERCARD", "BEBAS", 190, None, 16, 330, (255, 255, 255)),)
TAGLINE = (("HEARN  v  WHITE", "BEBAS", 70, None, 12, 735, (225, 40, 40)),)
EYES = {}
WHIPS = []


def h_of(p, who, y):
    hz, k = PPC[p]
    return CM[who] * (y - hz) * k


class OnCam(tuple):
    """a camera framed on one person (on()): the framing pass recomposes it from the drawing they are really in"""
    who = frac = dx = up = None


def on(p, x, y, who, frac=0.55, up=0.0, dx=0.0):
    """a camera on a person standing at (x, y) in set p: their top `frac` of height fills the frame"""
    h = h_of(p, who, y)
    vis = frac * h
    c = OnCam((x + dx, y - h + vis / 2 - up * h, 941.0 / vis))
    c.who, c.frac, c.dx, c.up = who, frac, dx, up
    return c


def W(t, p, cams, cast, blur=0.0, drift=0.35, extra_layers=(), **kw):
    cams = cams if isinstance(cams, list) else [(t, cams)]
    first = cams[0][1]
    if isinstance(first, OnCam):
        kw.setdefault("subject", dict(who=first.who, frac=first.frac, dx=first.dx, up=first.up))
    layers = [("props", "scene")] + list(extra_layers)
    if p in CROWD_FLASH:
        kw.setdefault("flashes", CROWD_FLASH[p])
    if p in OCCL:
        layers += [("occl", k) for k in OCCL[p]]
    return world(t, PLATES[p], cams[0][1], cams=cams, layers=layers, cast=cast, ppc=PPC[p], blur=blur,
                 drift=drift, **kw) | {"plate": p}


def P(who, pose, at, **kw):
    return dict(who=who, pose=pose, at=at, **kw)


def keys(*kv):
    return list(kv)


# ====================================================================== 1. the ban: press area
ED_P, SEC_P, BOARD = (800, 722), (1150, 705), (520, 715)
ed_press = P("eddie", keys((0, "front"), (wt("L001", "not") - 0.15, "point"), (le("L001") + 0.4, "front"),
                           (wt("L003", "no") - 0.1, "stop"), (le("L003") + 0.3, "front"),
                           (ls("L005") - 0.1, "hips")), ED_P)
sec_press = P("security", keys((0, "crossed"), (ls("L004") - 0.1, "gesture"), (le("L004") + 0.3, "crossed")), SEC_P)
board = dict(fn="board", at=BOARD, h=480)
press = [ed_press, sec_press, board]
t_not = wt("L001", "not") - 0.25
S1 = [
    card(m("title"), "title"),
    # the establishing wide, easing in, then Eddie and his board: the point lands just after the cut
    W(m("open"), "P", [(m("open"), (836, 470, 1.0)), (t_not, (810, 455, 1.14))], press),
    W(t_not, "P", [(t_not, (625, 345, 1.9)), (m("c_sec1"), (632, 340, 2.0))], press, blur=1.5),
    W(m("c_sec1"), "P", [(m("c_sec1"), on("P", *SEC_P, "security", 0.5)),
                         (m("c_ed2"), on("P", *SEC_P, "security", 0.47))], press, blur=2.0),
    W(m("c_ed2"), "P", [(m("c_ed2"), on("P", *ED_P, "eddie", 0.62)), (m("c_sec2"), on("P", *ED_P, "eddie", 0.58))],
      press, blur=2.0),
    W(m("c_sec2"), "P", (980, 500, 1.55), press, blur=1.0),
    W(m("c_ed3"), "P", [(m("c_ed3"), on("P", *ED_P, "eddie", 0.62)), (m("c_bay"), on("P", *ED_P, "eddie", 0.5))],
      press, blur=2.0),
]

# ---------------------------------------------------------------------- 1b. the loading bay
DA_B = (560, 585)
tro_b0, tro_b1 = m("trolley") - 0.3, m("look_cam") + 0.6


def trolley_group(t0, t1, x0, x1, y, p, att=True, side="trolley-side", towels=True, rot=None, tail=230):
    """the attendant pushing the laundry trolley from x0 to x1 (plate px, at floor y) between t0 and t1"""
    h = 90 * (y - PPC[p][0]) * PPC[p][1]
    path = [(t0, (x0, y)), (t1, (x1, y))]
    out = [dict(prop=side, at=path, h=h, z=y + 1, rot=rot or 0.0)]
    if towels:
        out.append(dict(prop="towel-pile", at=[(a, (x, yy - 0.86 * h)) for a, (x, yy) in path], h=0.55 * h, z=y + 0.5,
                        rot=rot or 0.0))
    if att:
        out.append(P("attendant", "push", [(a, (x - tail * h / 287.0, yy)) for a, (x, yy) in path], z=y + 2, steps=True))
    return out


# the trolley passes well behind him (further up the bay), so the attendant never crosses his body
bay = [P("dana", keys((0, "q34"), (ls("L006") - 0.1, "front"), (wt("L006", "half") - 0.1, "shrug"),
                      (wt("L006", "they're") - 0.1, "palms"), (le("L006") + 0.3, "q34"), (m("look_cam") - 0.05, "front")),
         DA_B)] + trolley_group(tro_b0, tro_b1, -350, 1950, 532, "B", tail=200)
shoe = [P("dana", "climb", (1000, 600), dy=[(m("c_shoe"), 150.0), (m("c_shoe") + 0.35, 140.0),
                                             (m("c_shoe") + 0.95, -330.0)], z=1, shadow=False,
           clip=600 - 0.22 * 250),
        dict(prop="towel-pile", at=(1000, 600 - 0.86 * 250), h=150, z=2,
             dy=[(m("c_shoe") + 0.8, 300.0), (m("c_shoe") + 1.1, 0.0)]),
        dict(prop="trolley-side", at=(1000, 600), h=250, z=3)]
t_rant = ls("L006") + 0.9
S1b = [
    W(m("c_bay"), "B", [(m("c_bay"), (836, 470, 1.0)), (t_rant, (770, 455, 1.12))], bay,
      caption=("LOADING BAY", "Same night · outside")),
    # the rant in a medium shot, pushing in a little
    W(t_rant, "B", [(t_rant, on("B", *DA_B, "dana", 0.80)), (m("trolley"), on("B", *DA_B, "dana", 0.70))], bay,
      blur=2.0),
    # wider again: the trolley crossing behind him, his head turning with it
    W(m("trolley"), "B", [(m("trolley"), (720, 425, 1.4)), (m("look_cam"), (700, 430, 1.48))], bay, blur=0.8),
    W(m("look_cam"), "B", [(m("look_cam"), on("B", *DA_B, "dana", 0.55)), (m("c_shoe"), on("B", *DA_B, "dana", 0.47))],
      bay, blur=2.5),
    W(m("c_shoe"), "B", [(m("c_shoe"), (1000, 420, 2.2)), (m("c_track"), (1000, 430, 2.4))], shoe, blur=3.0),
]

# ====================================================================== 2. the corridor
# the corridor, left to right: the security checkpoint, the cable protector on the floor further down, and Fury
# beyond it. The trolley comes in from the left, is stopped at the checkpoint, rolls on, hits the protector.
SEC_C, Y_C = (700, 680), 700
TH_C = 90 * (Y_C - 356) * 0.0082                         # the trolley's height in the corridor
RIM = Y_C - 0.928 * TH_C                                 # the top of its rim (row 20 of the 276 px trolley-side)
TR_X = 930                                               # where the cable protector stops it
CHK = 500                                                # where security stops it


def corridor_trolley():
    """the trolley's journey to the checkpoint and on past it"""
    stop = m("c_track") + 1.7
    return [(m("c_track"), (-350, Y_C)), (stop, (CHK, Y_C)), (m("aside"), (CHK, Y_C)),
            (m("aside") + 1.5, (CHK + 520, Y_C))]


SEC_CAST = P("security", keys((0, "stop"), (m("c_track") + 1.75, "front"), (ls("L012") - 0.1, "gesture"),
                              (le("L012") + 0.2, "front"), (m("aside"), "gesture"), (m("aside") + 1.2, "crossed")),
             [(0, SEC_C), (m("aside") + 0.1, SEC_C), (m("aside") + 0.6, (790, 645))], look=None, steps=True)


def corridor_a():
    path = corridor_trolley()
    tw = [(a, (x, y - 0.86 * TH_C)) for a, (x, y) in path]
    lid_on = m("lid") + 0.35
    return [SEC_CAST,
            dict(prop="trolley-side", at=path, h=TH_C, z=Y_C + 1),
            dict(prop="towel-pile", at=tw, h=0.55 * TH_C, z=Y_C + 0.5, show=[(0, lid_on - 0.05)],
                 rot=[(ls("L010"), 0.0), (ls("L010") + 0.15, 4.0), (ls("L010") + 0.35, -3.0), (le("L010"), 2.0),
                      (le("L010") + 0.2, 0.0)]),
            dict(fn="lid", at=[(a, (x, y - 0.93 * TH_C)) for a, (x, y) in path], w=1.08 * TH_C, z=Y_C + 1.5,
                 show=[(lid_on - 0.3, 1e9)], rot=[(lid_on - 0.3, 75.0), (lid_on, 0.0)]),
            P("attendant", "push", [(a, (x - 0.8 * TH_C, y)) for a, (x, y) in path], z=Y_C + 2, steps=True)]


def arc(t0, t1, p0, p1, height, n=8):
    """keys along a thrown arc from p0 to p1 (plate px), `height` px above the straight line at the top"""
    out = []
    for i in range(n + 1):
        u = i / n
        out.append((t0 + (t1 - t0) * u, (p0[0] + (p1[0] - p0[0]) * u,
                                        p0[1] + (p1[1] - p0[1]) * u - height * 4 * u * (1 - u))))
    return out


DA_LAND, FU_C, AJ_C = (1205, 718), (1430, 708), (1585, 696)
FU_BACK, AJ_BACK = (1395, 655), (1548, 646)              # where they stand for the negotiations: upstage
SEC_C3 = (470, 668)                                      # security back at his post, up the corridor
ED_IN, ED_NEG = (290, 728), (965, 732)


def corridor_b():
    """the trolley rolls on with Dana inside; his dome rises out of the towels and lifts the lid; the cable
    protector stops it dead; a freeze on his eyes; he is thrown out in an arc over the front and lands at Fury's
    feet, a towel landing on his head"""
    t0, tb, ft = m("c_inside"), m("bump"), m("tumble")
    path = [(t0, (300, Y_C)), (tb, (TR_X, Y_C))]
    jolt = [(tb, 0.0), (tb + 0.08, 9.0), (tb + 0.35, 4.0), (tb + 0.7, 0.0)]
    fluff = [(t0 + 1.2, -44.0), (t0 + 2.2, 0.0)]                       # the towels lift with the lid
    # inside: the peek drawing (head and hands) sits behind the trolley's canvas; its bottom edge is always below
    # the rim, so the bin hides where the drawing ends; it only ever rises as far as the hands on the rim
    peek = P("dana", "peek", [(a, (x + 62, RIM + 16)) for a, (x, y) in path] + [(ft, (TR_X + 62, RIM + 16))],
             z=Y_C + 0.7, shadow=False, floor=Y_C, show=[(t0, ft)],
             dy=[(t0, -150.0), (t0 + 0.8, -150.0), (t0 + 1.9, -48.0), (t0 + 2.6, 0.0), (tb, 0.0), (tb + 0.08, 6.0),
                 (ft, 6.0)])
    land = ft + 0.9
    fly_path = arc(ft, land, (TR_X + 70, RIM + 60), DA_LAND, 70)
    fly = P("dana", keys((ft, "tumble1"), (ft + 0.3, "tumble2"), (ft + 0.6, "tumble3")), fly_path,
            rot=[(ft, 0.0), (ft + 0.3, -22.0), (ft + 0.6, 14.0), (land, 0.0)], mirror=True,
            z=Y_C + 40, shadow=False, floor=DA_LAND[1], show=[(ft, land)])
    towel_fly = dict(prop="towel", at=arc(ft + 0.05, land + 0.12, (TR_X + 40, RIM - 20),
                                          (DA_LAND[0] + 35, DA_LAND[1] - 108), 360),
                     h=95, z=Y_C + 41, rot=[(ft, 0.0), (land + 0.12, 380.0)], show=[(ft + 0.05, m("landed") + 0.55)])
    spare = [dict(prop="towel", at=arc(ft + 0.02, ft + 0.75, (TR_X - 20, RIM - 10), (TR_X + 210 + 140 * k, Y_C + 30), 260),
                  h=70, z=Y_C + 30, rot=[(ft, 0.0), (ft + 0.75, 200.0 + 90 * k)], mirror=bool(k),
                  show=[(ft + 0.02, m("c_eddie"))]) for k in range(2)]
    return [dict(prop="cable-ramp", at=(1000, Y_C + 6), h=55, z=Y_C - 5),
            dict(prop="towel-pile", at=[(a, (x - 70, RIM + 44)) for a, (x, y) in path], h=0.46 * TH_C, z=Y_C + 0.5,
                 rot=jolt, dy=fluff, show=[(t0, ft + 0.02)]),
            dict(prop="towel-pile", at=[(a, (x + 100, RIM + 48)) for a, (x, y) in path], h=0.44 * TH_C, z=Y_C + 0.55,
                 rot=jolt, dy=fluff, mirror=True, show=[(t0, ft + 0.02)]),
            peek,
            dict(prop="trolley-side", at=path, h=TH_C, z=Y_C + 1, rot=jolt, pivot=1.0),
            dict(fn="lid", at=[(a, (x, y - 0.93 * TH_C)) for a, (x, y) in path], w=1.08 * TH_C, z=Y_C + 1.5,
                 rot=[(t0 + 1.4, 0.0), (t0 + 2.6, 38.0), (tb, 38.0), (tb + 0.12, 85.0), (ft + 0.3, 118.0)]),
            P("attendant", "push", [(a, (x - 0.8 * TH_C, y)) for a, (x, y) in path], z=Y_C + 2, steps=True,
              rot=[(tb, 0.0), (tb + 0.1, 6.0), (tb + 0.5, 0.0)]),
            fly, towel_fly] + spare


S2 = [
    W(m("c_track"), "C", [(m("c_track"), (390, 425, 1.9)), (m("c_track") + 1.7, (560, 450, 1.55))], corridor_a(),
      caption=("BACKSTAGE", "Security checkpoint")),
    W(ls("L009"), "C", (560, 540, 1.55), corridor_a()),
    W(m("c_bin1"), "C", (CHK + 40, 395, 2.35), corridor_a(), blur=2.0),
    W(m("lid"), "C", (560, 520, 1.5), corridor_a()),
    W(ls("L011") + 0.05, "C", on("C", CHK - 0.8 * TH_C, Y_C, "attendant", 0.8, dx=40), corridor_a(), blur=2.0),
    W(m("c_sec3"), "C", on("C", *SEC_C, "security", 0.55), corridor_a(), blur=2.0),
    W(m("c_att3"), "C", on("C", CHK - 0.8 * TH_C, Y_C, "attendant", 0.78, dx=40), corridor_a(), blur=2.0),
    W(m("aside"), "C", [(m("aside"), (640, 520, 1.45)), (m("c_inside"), (760, 520, 1.5))], corridor_a()),
]


def fury_corridor():
    fury = P("tyson", keys((0, "front"), (ls("L015") - 0.1, "point_down"), (le("L015") + 0.3, "front"),
                           (ls("L017") - 0.1, "crossed"), (le("L017") + 0.2, "front"),
                           (ls("L019") - 0.1, "point_down"), (le("L019") + 0.3, "front"), (m("c_eddie"), "crossed")),
             keys((0, FU_C), (m("c_ed4") + 0.02, FU_C), (m("c_ed4") + 0.03, FU_BACK)), look="dana")
    return [fury]


# ====================================================================== 3. Fury finds a promoter


def dana_corr():
    return P("dana", keys((0, "prone"), (m("landed") + 0.55, "towel_head"), (m("c_dana3") - 0.03, "towel_shoulder"),
                          (m("c_neg") + 0.55, "front"), (ls("L027") - 0.1, "point"), (le("L027") + 0.3, "front"),
                          (ls("L030") - 0.1, "shrug"), (le("L030") + 0.4, "crossed")), DA_LAND, look=None,
             mirror=keys((0, True), (m("landed") + 0.55, False)), show=[(m("tumble") + 0.9, 1e9)])


def joshua_corr():
    """Joshua walks in from the right with a water bottle, stops, looks down at Dana"""
    tw0 = m("c_aj") - 0.75
    return P("joshua", keys((0, "walk"), (tw0 + 0.9, "front"), (m("c_fj1") - 0.5, "crossed")),
             keys((tw0, (1830, AJ_C[1])), (tw0 + 0.9, AJ_C), (m("c_ed4") + 0.02, AJ_C), (m("c_ed4") + 0.03, AJ_BACK)),
             steps=True, mirror=keys((0, True), (tw0 + 0.95, False)), show=[(tw0, 1e9)])


def eddie_corr():
    walk_t0, walk_t1 = m("c_eddie"), m("c_eddie") + 1.6
    w2_t0, w2_t1 = ls("L025") - 0.15, m("c_neg") + 0.3
    W8 = [f"w{i}" for i in range(8)]
    return P("eddie", keys((0, "q34"), (ls("L024") - 0.1, "point"), (le("L024") + 0.3, "q34"),
                           (m("c_neg") + 0.32, "point"), (m("c_neg") + 1.0, "front"),
                           (m("c_list"), "palms"), (wt("L029", "medicals") - 0.1, "point"),
                           (wt("L029", "no") - 0.1, "stop"), (wt("L029", "wrestling") - 0.1, "shrug"),
                           (le("L029") + 0.2, "front"), (ls("L031") - 0.1, "hips")),
             [(walk_t0, (-130, ED_IN[1])), (walk_t1, ED_IN), (w2_t0, ED_IN), (w2_t1, ED_NEG)],
             walk=[dict(frames=W8, cycle=1.0, t0=walk_t0, t1=walk_t1), dict(frames=W8, cycle=0.9, t0=w2_t0, t1=w2_t1)],
             mirror=keys((0, False), (ls("L024") - 0.1, True), (le("L024") + 0.3, False), (m("c_neg") + 0.32, True),
                         (m("c_neg") + 1.0, False), (wt("L029", "medicals") - 0.1, True), (wt("L029", "no") - 0.1, False)),
             show=[(m("c_eddie"), 1e9)],
             holds=[dict(t0=m("c_neg") + 0.42, t1=m("c_neg") + 1.0, prop="towel", at=(75, 470), h=95, grip=(0.3, 0.05))])


def corridor_c():
    """after the landing: the stopped trolley and the attendant (who wheels it away while we are on Dana), security
    at his post, Dana at Fury's feet, Joshua, Eddie"""
    gone = m("c_dana3")
    return [dict(prop="cable-ramp", at=(1000, Y_C + 6), h=55, z=Y_C - 5),
            dict(prop="trolley-side", at=(TR_X, Y_C), h=TH_C, z=Y_C + 1, show=[(0, gone)]),
            dict(fn="lid", at=(TR_X, Y_C - 0.93 * TH_C), w=1.08 * TH_C, z=Y_C + 1.5, rot=118.0, show=[(0, gone)]),
            P("attendant", keys((0, "push"), (m("landed") + 0.4, "point"), (m("landed") + 2.6, "towel")),
              (TR_X - 0.8 * TH_C, Y_C), z=Y_C + 2, show=[(0, gone)]),
            P("security", keys((0, "front"), (m("dart") + 0.3, "startled"), (m("dart") + 1.3, "crossed")), SEC_C3,
              look=None),
            dana_corr(), joshua_corr(), eddie_corr(),
            dict(prop="towel", at=(ED_NEG[0] + 120, 772), h=60, show=[(m("c_neg") + 1.0, 1e9)], z=771,
                 dy=[(m("c_neg") + 1.0, 120.0), (m("c_neg") + 1.25, 0.0)])] + fury_corridor()


S2b = [
    # inside: low and close on the bin as it rolls, the dome coming up out of the towels
    W(m("c_inside"), "C", [(m("c_inside"), (300 + 40, RIM - 80, 2.3)), (m("bump"), (TR_X + 40, RIM - 80, 2.3))],
      corridor_b(), blur=2.0, linear=True),
    # the freeze: his eyes, the whole head in frame (its box is 947-1035 x 380-473 plate px here)
    W(m("bump"), "C", [(m("bump"), (TR_X + 61, 432, 6.6)), (m("tumble"), (TR_X + 61, 434, 7.3))],
      corridor_b(), blur=3.0, drift=0.0, locked=True),
    W(m("tumble"), "C", [(m("tumble"), (1080, 470, 1.02)), (m("landed"), (1110, 470, 1.1))],
      corridor_b() + fury_corridor() + [dana_corr()]),
]

CC = corridor_c()
mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
S3 = [
    W(m("landed"), "C", [(m("landed"), (1290, 440, 1.45)), (m("c_dana1"), (1300, 446, 1.55))], CC),
    W(m("c_dana1"), "C", on("C", *DA_LAND, "dana", 0.9), CC, blur=2.0),
    W(m("c_fury2"), "C", on("C", *FU_C, "tyson", 0.5), CC, blur=2.0),
    W(m("c_dana2"), "C", on("C", *DA_LAND, "dana", 0.85), CC, blur=2.0),
    W(m("c_fury3"), "C", [(m("c_fury3"), on("C", *FU_C, "tyson", 0.62)), (m("c_aj"), on("C", *FU_C, "tyson", 0.56))],
      CC, blur=2.0),
    W(m("c_aj") - 0.2, "C", (1400, 500, 1.5), CC),
    W(ls("L020") - 0.1, "C", on("C", *AJ_C, "joshua", 0.5), CC, blur=2.0),
    W(m("c_fury4"), "C", (1400, 500, 1.5), CC),
    W(m("c_eddie"), "C", [(m("c_eddie"), (836, 470, 1.0)), (m("dart") + 0.6, (840, 476, 1.06))], CC),
    W(ls("L022") - 0.05, "C", [(ls("L022") - 0.05, on("C", *ED_IN, "eddie", 0.55)),
                               (le("L022") + 0.2, on("C", *ED_IN, "eddie", 0.5))], CC, blur=2.0),
    W(m("c_dana3"), "C", on("C", *DA_LAND, "dana", 0.66, up=0.1), CC, blur=2.0),
    W(m("c_ed4"), "C", on("C", *ED_IN, "eddie", 0.62), CC, blur=2.0),
    W(m("c_dana4"), "C", on("C", *DA_LAND, "dana", 0.64, up=0.1), CC, blur=2.0),
]

# ====================================================================== 4. negotiations
two = mid(ED_NEG, DA_LAND)
S4 = [
    # the two promoters face to face downstage, Fury and Joshua watching from up the corridor
    W(m("c_neg"), "C", [(m("c_neg"), (two[0] + 30, 470, 1.6)), (m("c_fine"), (two[0] + 30, 478, 1.72))], CC),
    W(m("c_fine"), "C", on("C", *ED_NEG, "eddie", 0.5), CC, blur=2.0),
    W(m("surprise"), "C", (two[0], 468, 1.95), CC, blur=1.0),
    W(m("c_list"), "C", [(m("c_list"), on("C", *ED_NEG, "eddie", 0.8)), (le("L029"), on("C", *ED_NEG, "eddie", 0.68))],
      CC, blur=1.5),
    W(m("c_dana5"), "C", on("C", *DA_LAND, "dana", 0.66, up=0.06), CC, blur=2.0),
    W(m("c_ed5"), "C", [(m("c_ed5"), on("C", *ED_NEG, "eddie", 0.6)), (m("c_fj1"), on("C", *ED_NEG, "eddie", 0.48))],
      CC, blur=2.0),
    W(m("c_fj1"), "C", [(m("c_fj1"), on("C", 1470, 652, "tyson", 0.62)), (m("c_prep"), on("C", 1470, 652, "tyson", 0.56))],
      CC, blur=1.0),
]

# ---------------------------------------------------------------------- 4b. two dressing rooms
# Eddie's (the red corner) and, down the hall, Dana's (the blue corner: plate E)
from film.fight import Fighter                                              # noqa: E402

ED_D, DA_E = (820, 598), (900, 642)
tp, tp2 = m("c_prep"), m("c_prep2")
prep_ed = [P("eddie", keys((0, "front"), (tp + 0.78, "tired")), ED_D, look=keys((0, "down"), (tp + 0.5, "cam")),
             rot=[(tp + 0.78, 0.0), (tp + 1.0, 2.5), (tp2, 2.0)]),
           dict(fn="puff", t0=tp + 0.6, dur=0.42, at=(ED_D[0], ED_D[1] - 0.52 * 191 * (ED_D[1] - 350) * 0.0113),
                size=0.80 * 191 * (ED_D[1] - 350) * 0.0113, z=2000)]
H_DE = 170 * (DA_E[1] - 350) * 0.0113
SB = Fighter("dana", DA_E[0], -1, DA_E[1], H_DE)
for i, (dt, pose, reach) in enumerate([(0.25, "jab", 40), (0.55, "jab2", 45), (0.8, "jab3", 40), (1.02, "jab", 35),
                                      (1.2, "jab4", 45), (1.38, "jab2", 40)]):
    SB.punch(tp2 + dt, pose, reach, wind="guard", wind_t=0.07, hold=0.06, back=0.1, lean=5, lines=False,
             sound="whoosh")
SB.pose(tp2 + 1.55, "tired").hold(tp2 + 1.55).lean(tp2 + 1.6, 6.0).lean(tp2 + 1.9, 3.0)
prep_da = [SB.item(P, look=keys((0, None), (tp2 + 1.6, "down")))]
S4b = [W(tp, "D", [(tp, on("D", *ED_D, "eddie", 1.12, up=0.06)), (tp2, on("D", *ED_D, "eddie", 1.02, up=0.06))],
         prep_ed, caption=("RED CORNER", "Ten minutes later")),
       W(tp2, "E", [(tp2, on("E", *DA_E, "dana", 1.25, up=0.08)), (m("c_arena"), on("E", *DA_E, "dana", 1.15, up=0.08))],
         prep_da, caption=("BLUE CORNER", "Down the hall"))]

# ====================================================================== 5. the special announcement
ED_A, DA_A, AN_A, RF_A = (440, 655), (1240, 655), (836, 650), (1010, 598)
ann = [P("eddie", "guard", ED_A, face=[(m("c_ed_in"), m("c_ann3"), 0.95, 0.55)]),
       P("dana", keys((0, "guard"), (m("c_da_in") + 0.3, "arms_up")), DA_A),
       P("announcer", keys((0, "mic"), (wt("L035", "red") - 0.1, "mic_gesture"), (le("L035"), "mic"),
                           (wt("L036", "blue") - 0.1, "mic_gesture"), (le("L036"), "mic")), AN_A,
         mirror=keys((0, False), (wt("L035", "red") - 0.1, True), (le("L035"), False)),
         show=[(0, m("c_ref"))]),
       P("referee", keys((0, "stop"),), keys((0, RF_A), (m("c_ref") - 0.06, RF_A), (m("c_ref") - 0.05, (836, 640))), look="cam"),
       dict(prop="towel", at=(1262, 655 - 0.80 * 176 * (655 - 514) * 0.0097), h=40, z=700,
            show=[(0, m("c_da_in") + 1.25)]),
       P("attendant", "towel", keys((m("c_da_in") + 0.5, (1640, 668)), (m("c_da_in") + 0.95, (1400, 668)),
                                    (m("c_da_in") + 1.6, (1400, 668)), (m("c_da_in") + 2.2, (1680, 668))),
         show=[(m("c_da_in") + 0.5, m("c_ref"))], z=800)]
ann_ref = [P("eddie", "guard", (650, 652)), P("dana", "guard", (1030, 652)),
           P("referee", "stop", (836, 640), look="cam")]
SEATED = [P("tyson", "seated", (520, 945), z=946), P("joshua", "seated", (1120, 945), z=946),
          dict(prop="folding-chair", at=(520, 925), h=420, z=900), dict(prop="folding-chair", at=(1120, 925), h=420, z=900)]


def ringside(face=None, looks=None):
    out = []
    for it in SEATED:
        it = dict(it)
        if "who" in it and face:
            it["face"] = face
        if "who" in it and looks:
            it["look"] = looks
        out.append(it)
    return out


S5 = [
    W(m("c_arena"), "A", [(m("c_arena"), (836, 470, 1.0)), (ls("L034") + 2.0, (836, 500, 1.15)),
                          (m("c_fj2"), (836, 560, 1.75))], ann, caption=("THE ARENA", "Special announcement")),
    W(m("c_fj2"), "S", (836, 700, 1.5), ringside(face=[(m("c_fj2"), m("c_ann2"), 0.75, 0.75)], looks="cam")),
    W(m("c_ann2"), "A", [(m("c_ann2"), on("A", *AN_A, "announcer", 0.7)), (m("c_ed_in"), on("A", *AN_A, "announcer", 0.6))],
      ann, blur=1.5),
    W(m("c_ed_in"), "A", on("A", *ED_A, "eddie", 0.55), ann, blur=2.0),
    W(m("c_ann3"), "A", [(m("c_ann3"), on("A", *AN_A, "announcer", 0.65)), (m("c_da_in"), on("A", *AN_A, "announcer", 0.58))],
      ann, blur=1.5),
    W(m("c_da_in"), "A", on("A", *DA_A, "dana", 1.05, dx=40), ann, blur=1.5),
    W(m("c_ref"), "A", (836, 560, 2.3), ann_ref, blur=1.0),
    W(m("c_ed6"), "A", on("A", 650, 652, "eddie", 0.5), ann_ref, blur=2.0),
]

# ====================================================================== 6. the fight
# (film/fight.py: each fighter's moves on the edit's marks; the effects and camera shakes they make)
from film.fight import Fighter                                              # noqa: E402

ED_R, DA_R, RF_R = (560, 785), (1110, 785), (1390, 640)
H_ED, H_DA = 191 * (785 - PPC["R"][0]) * PPC["R"][1], 170 * (785 - PPC["R"][0]) * PPC["R"][1]
tb, tf = m("bell"), m("faceoff")
e1, e2, e3a, e3b, e3c, e3d, e3e = (m(k) for k in ("ex1", "ex2", "ex3a", "ex3b", "ex3c", "ex3d", "ex3e"))
ts, tbell2 = m("sep"), m("bell2")
CL_E, CL_D = (585, 785), (1088, 785)          # the clinch: heads together over the middle
E = Fighter("eddie", ED_R[0], +1, ED_R[1], H_ED)
Dn = Fighter("dana", DA_R[0], -1, DA_R[1], H_DA)
HEAD_E, HEAD_D = ED_R[1] - 0.86 * H_ED, DA_R[1] - 0.84 * H_DA

# the face-off: bouncing, circling a little, nobody throwing anything
E.hold(tf).to(tf + 0.7, 595).to(tf + 1.5, 570).to(tf + 2.3, 600).pose(tf + 1.1, "guard2").pose(tf + 2.0, "guard")
Dn.hold(tf).to(tf + 0.8, 1080).to(tf + 1.6, 1100).to(tf + 2.4, 1070)
# 1: Eddie's long jab; Dana leans back much too far and windmills, then recovers
E.punch(e1 + 0.35, "jab_long", 120, wind="wind", wind_t=0.25, hold=0.35, back=0.4, lean=8)
Dn.windmill(e1 + 0.33, dur=1.15)
# 2: Dana's little jab taps Eddie's guard: the squeak (and Eddie's outrage)
Dn.punch(e2 + 0.3, "jab", 70, wind="guard_high", wind_t=0.15, hold=0.2, back=0.35, lean=4)
E.hit(e2 + 0.36, pose="block", knock=22, lean=6, settle=0.5, at=(E.x + 0.30 * H_ED, ED_R[1] - 0.62 * H_ED), size=48,
      sweat=False)
E.pose(m("c_ed7") + 0.05, "guard")
# 3: Eddie's flurry, jab jab jab; Dana bobs under every one
for k, dt in enumerate((0.2, 0.62, 1.04)):
    E.punch(e3a + dt, "jab" if k != 1 else "jab_long", 55, wind="guard", wind_t=0.08, hold=0.1, back=0.16, lean=5)
    Dn.duck(e3a + dt - 0.03, dur=0.26, dx=18 if k % 2 else -18)
# 4: Dana's counter to the body: Eddie covers, is knocked back and stumbles
Dn.punch(e3b + 0.35, "jab3", 95, wind="guard_high", wind_t=0.2, hold=0.22, back=0.4, lean=6, height=0.55)
E.hit(e3b + 0.43, pose="cover", knock=80, lean=12, settle=0.8, at=(E.x + 0.26 * H_ED, ED_R[1] - 0.55 * H_ED), size=120)
E.stumble(e3b + 0.62, 0.45, -35).guard(e3b + 1.15, x=560)
# 5: Eddie comes back with a wild lunging cross; Dana ducks; Eddie's momentum spins him round
E.punch(e3c + 0.35, "cross", 150, wind="wind", wind_t=0.25, hold=0.12, back=0.75, lean=14, home=560)
E.spin(e3c + 0.6, dur=0.42)
Dn.duck(e3c + 0.3, dur=0.5, dx=12)
# 6: slow motion: both back off, wind up enormous haymakers and throw them from much too far away
E.hold(e3d).to(e3d + 0.3, 330).pose(e3d + 0.1, "wind")
Dn.hold(e3d).to(e3d + 0.3, 1350).pose(e3d + 0.1, "guard_high")
E.punch(e3d + 0.85, "cross", 25, wind="wind", wind_t=0.5, hold=0.3, back=0.4, lean=16, swing=0.35, sound="whoosh_slow")
Dn.punch(e3d + 0.85, "jab4", 25, wind="guard_high", wind_t=0.5, hold=0.3, back=0.4, lean=16, swing=0.35,
         sound="whoosh_slow")
E.spin(e3d + 1.4, dur=0.45)
Dn.spin(e3d + 1.42, dur=0.45)
# 7: exhausted, they stagger into each other: the clinch
E.pose(e3e + 0.05, "tired").hold(e3e + 0.05).to(e3e + 1.0, CL_E[0]).lean(e3e + 1.0, 5.0)
Dn.pose(e3e + 0.05, "tired").hold(e3e + 0.05).to(e3e + 1.0, CL_D[0]).lean(e3e + 1.0, -5.0)
E.hold(ts + 0.05).lean(ts + 0.05, 5.0).to(ts + 0.45, 500).lean(ts + 0.4, -6.0).lean(ts + 0.65, 5.0).lean(ts + 0.85, -4.0)
E.lean(ts + 1.0, 0.0).hold(ts + 1.05).to(ts + 1.45, CL_E[0]).lean(ts + 1.45, 5.0)
Dn.hold(ts + 0.05).lean(ts + 0.05, -5.0).to(ts + 0.45, 1170).lean(ts + 0.4, 6.0).lean(ts + 0.65, -5.0).lean(ts + 0.85, 4.0)
Dn.lean(ts + 1.0, 0.0).hold(ts + 1.05).to(ts + 1.45, CL_D[0]).lean(ts + 1.45, -5.0)
Dn.pose(ts + 0.3, "guard").pose(ts + 1.05, "tired")
E.pose(ts + 0.3, "guard").pose(ts + 1.05, "tired")
# 8: "...and sold the fight": they shove apart and slug it out, every punch landing, faster and faster
tsl, tdk, tim, tfa = m("slug"), m("dko"), m("impact"), m("fall")
BASE = {E: 615, Dn: 1095}
HEADS = {E: (-2, 489), Dn: (-11, 445)}                         # the head in guard, from the feet (ring px)
TIPS = {"jab": 327, "jab_long": 350, "cross": 372, "jab2": 345, "jab4": 340}   # glove tip ahead of the feet
TIPS_D = {"jab": 281, "jab2": 345, "jab4": 340}
for F_ in (E, Dn):
    F_.pose(tsl, "guard").hold(tsl).to(tsl + 0.25, BASE[F_]).lean(tsl + 0.2, 0.0)
SLUG = [(0.42, E, "jab", 0.12), (0.95, Dn, "jab2", 0.12), (1.40, E, "cross", 0.12), (1.82, Dn, "jab4", 0.10),
        (2.18, E, "jab", 0.08), (2.48, Dn, "jab", 0.08), (2.72, E, "jab_long", 0.07), (2.94, Dn, "jab2", 0.07)]
for dt, A_, pose, wind in SLUG:
    V = Dn if A_ is E else E
    t = tsl + dt
    x0 = A_.x
    A_.punch(t, pose, 55, wind="guard", wind_t=wind, hold=0.07, back=0.13, lean=7, swing=0.06)
    tip = x0 + 55 * A_.facing + (TIPS if A_ is E else TIPS_D)[pose] * A_.facing      # where the glove lands
    hy = V.y - HEADS[V][1]
    V.hit(t + 0.06, pose="lean_back" if V is Dn else "block", knock=38, lean=13, settle=0.3,
          at=(tip - 25 * A_.facing, hy + 10), size=105)
    V.pose(t + 0.34, "guard").hold(t + 0.24).to(t + 0.36, BASE[V])
# 9: both load up an enormous one, trembling; the cross-counter lands on both at once; a freeze
E.pose(tdk, "wind").hold(tdk).to(tdk + 0.25, 595).lean(tdk + 0.25, -9.0).tremble(tdk + 0.3, tim - 0.02, -9.0)
Dn.pose(tdk, "lean_back").hold(tdk).to(tdk + 0.25, 1175).lean(tdk + 0.25, 9.0).tremble(tdk + 0.3, tim - 0.02, 9.0)
E.pose(tim, "jab_long").hold(tim).to(tim + 0.06, 630).lean(tim + 0.06, 8.0)
Dn.pose(tim, "jab4").hold(tim).to(tim + 0.06, 1140).lean(tim + 0.06, -8.0)
for F_ in (E, Dn):
    F_.hold(tfa).lean(tfa, F_.rots[-1][1])
E.sfx.append((tim - 0.01, "whoosh", 120))
Dn.sfx.append((tim - 0.01, "whoosh", 120))
DKO_FX = [dict(fn="impact", t0=tim + 0.06, at=(818, 322), size=230, z=6010),         # Dana's glove on Eddie's face
          dict(fn="impact", t0=tim + 0.06, at=(982, 362), size=230, z=6010),         # Eddie's on Dana's
          dict(fn="sweat", t0=tim + 0.06, at=(760, 290), n=9, dir=-1, size=200, z=6011),
          dict(fn="sweat", t0=tim + 0.06, at=(1030, 330), n=9, dir=1, size=200, z=6011)]
# 10: both go over backwards like felled trees and hit the canvas on the same frame; stars circle their heads
E.knockout(tfa, lift=0.29 * H_ED, slide=85)
Dn.knockout(tfa, lift=0.29 * H_DA, slide=85)
STARS = [dict(fn="stars", follow=w, t0=tfa + 0.75, t1=m("bell2") + 0.1, z=6020) for w in ("eddie", "dana")]
# 11: saved by the bell: both spring up and raise their arms as if they had won
E.popup(tbell2)
Dn.popup(tbell2)
for F_, home in ((E, 560), (Dn, 1110)):
    F_.hold(tbell2 + 0.3).to(tbell2 + 0.8, home)
    F_.pose(m("c_ann4"), "guard" if F_ is E else "tired")       # Dana, spent, hands on his knees for the decision
E.hold(m("c_ann4") - 0.01).to(m("c_ann4"), 500)
E.pose(m("glance") + 0.2, "jab_long").pose(m("climb") + 0.6, "guard")       # points Dana at the exit
# the exit: Dana steps round to the side of the bin, crouches, springs up over the rim and drops in out of sight
# (behind its canvas: nothing of him is ever cut in the air); he rides out inside it
tcl = m("climb")
Dn.pose(m("glance") + 0.5, "guard").hold(m("glance") + 0.1).to(tcl + 0.35, 1240).pose(tcl + 0.3, "crouch_guard")
Dn.hold(tcl + 0.5).to(tcl + 1.0, 995).lift(tcl + 0.5, 0.0).lift(tcl + 0.78, 270.0).lift(tcl + 1.0, 215.0)
Dn.lift(tcl + 1.32, -470.0).lean(tcl + 0.5, 0.0).lean(tcl + 0.8, -12.0).lean(tcl + 1.2, 4.0)
Dn.hold(m("rollout")).to(m("rollout") + 1.8, 995 + 1260)

Dn.pose(ls("L041") - 0.12, "guard_high").pose(le("L041") + 0.25, "guard")
eddie_fight = E.item(P)
TH_R = 90 * (812 - 289) * 0.0065                              # the trolley's height in the ring
dana_fight = Dn.item(P, clip=keys((0, None), (tcl + 0.8, 812 - 0.22 * TH_R)))     # its canvas' bottom edge
FIGHT_FX = E.fx + Dn.fx + DKO_FX + STARS
SHAKES = E.shakes + Dn.shakes + [(e3b + 0.43, 12.0, 0.4), (tim + 0.06, 18.0, 0.55)]
KICKS = [(e2 + 0.36, 1.05, 0.5), (e3b + 0.43, 1.10, 0.6), (e3d + 1.0, 1.04, 0.9)] + \
    [(tsl + dt + 0.06, 1.035, 0.3) for dt, *_ in SLUG] + [(tim + 0.06, 1.14, 0.7)]
FLASHES = [(tim + 0.06, 0.14), (tfa + 0.75, 0.06)]                # white impact frames
tdn = m("down")
RF_MID = (885, 655)                                             # between the two of them, upstage
ref_fight = P("referee", keys((0, "stop"), (ls("L045") - 0.1, "break"), (ls("L045") + 1.2, "stop"),
                              (m("c_ref3") + 0.1, "break"), (tbell2 + 0.05, "stop"), (tbell2 + 0.6, "card")),
              keys((0, RF_R), (ls("L045") - 0.45, RF_R), (ls("L045") - 0.1, (1345, 640)), (ls("L045") + 1.2, (1345, 640)),
                   (ls("L045") + 1.7, RF_R), (tdn + 0.15, RF_R), (tdn + 0.75, RF_MID)), look=None, ease=True,
              steps=True, show=[(0, m("c_ann4"))])
NEAR = dict(fn="near_ropes", ys=[850, 975], z=5000, w=20, blur=3.5)
RING_FLASH = [((40, 20, 1630, 300), 5.0, 3)]


def ring(extra=()):
    return [eddie_fight, dana_fight, ref_fight, NEAR] + FIGHT_FX + list(extra)


def RW(t, cams, cast=None, **kw):
    """a shot inside the ring: the fight's shakes and snap zooms, the press flashes in the crowd"""
    return W(t, "R", cams, cast if cast is not None else ring(), shakes=SHAKES, kicks=KICKS, flashes=RING_FLASH,
             white=FLASHES, **kw)


# 7: the announcer back in, then the trolley
tt0 = m("c_trolley")
RING_TROLLEY = trolley_group(tt0, tt0 + 2.0, -400, 990, 812, "R", tail=230)
# the trolley group's own items stop at its last key: carry them on for the roll-out
for it in RING_TROLLEY[:3]:
    it["at"] = it["at"] + [(m("rollout"), it["at"][-1][1]),
                           (m("rollout") + 1.8, (it["at"][-1][1][0] + 1260, it["at"][-1][1][1]))]
    it["show"] = [(tt0, 1e9)]
RING_TROLLEY = RING_TROLLEY[:3]
RING_TROLLEY[1]["dy"] = [(tcl + 1.22, 0.0), (tcl + 1.32, 38.0), (tcl + 1.6, 0.0)]          # the towels puff up
RING_TROLLEY.append(dict(fn="lid", at=[(a, (x, y - 0.93 * TH_R)) for a, (x, y) in RING_TROLLEY[0]["at"]],
                         w=1.08 * TH_R, z=813.5, show=[(tt0, 1e9)],
                         rot=[(tt0, 112.0), (tcl + 1.5, 112.0), (tcl + 1.8, 0.0), (tcl + 1.86, 5.0), (tcl + 1.95, 0.0)]))
ann_ring = P("announcer", "mic", (835, 700), show=[(m("c_ann4"), m("c_trolley"))])


def ring_end(close=False):
    """the ring after the bell; the close-ups cheat the announcer out (half his face at the frame edge reads badly)"""
    return [eddie_fight, dana_fight, ref_fight] + ([] if close else [ann_ring]) + [NEAR] + RING_TROLLEY


wince = [(m("c_wince"), m("ex3e"), 0.9, -0.45)]
S6 = [
    W(tb, "A", [(tb, (836, 300, 2.4)), (tf, (836, 320, 2.6))], [dict(prop="boxing-bell", at=(836, 420), h=230)],
      blur=10.0, shakes=[(tb + 0.05, 10.0, 0.5), (tb + 0.33, 8.0, 0.4)]),
    RW(tf, [(tf, (836, 520, 1.12)), (m("cough"), (836, 500, 1.32))]),
    W(m("c_ty1"), "S", (650, 700, 1.9), ringside(face=[(m("c_ty1"), m("c_fight"), -0.6, -0.3)])),
    RW(m("c_fight"), (836, 520, 1.12)),
    RW(e2, [(e2, (850, 470, 1.55)), (m("c_ed7"), (850, 470, 1.62))]),
    RW(m("c_ed7"), on("R", ED_R[0], ED_R[1], "eddie", 0.55, dx=40), blur=2.0),
    RW(m("c_da7"), on("R", *DA_R, "dana", 0.55, dx=-40), blur=2.0),
    RW(m("c_ed8"), on("R", ED_R[0], ED_R[1], "eddie", 0.55, dx=40), blur=2.0),
    RW(m("c_ex3"), (836, 520, 1.12)),
    RW(e3b, [(e3b, (760, 480, 1.45)), (e3c, (760, 480, 1.5))]),
    RW(e3c, (836, 520, 1.12)),
    RW(e3d, [(e3d, (836, 530, 1.05)), (m("c_wince"), (836, 510, 1.18))]),
    W(m("c_wince"), "S", (836, 700, 1.5), ringside(face=wince, looks=("dir", 0.0, -0.35, 0.0))),
    RW(e3e, [(e3e, (836, 500, 1.3)), (m("c_cl1"), (836, 480, 1.45))]),
    RW(m("c_cl1"), [(m("c_cl1"), (840, 420, 2.0)), (m("c_ref2"), (840, 420, 2.15))], blur=1.5),
    RW(m("c_ref2"), (900, 520, 1.15)),
    W(m("c_fj3"), "S", (836, 700, 1.5), ringside()),
    RW(m("c_cl2"), [(m("c_cl2"), (840, 400, 2.3)), (tsl, (840, 400, 2.5))], blur=2.0),
    # the slugfest: a two-shot, snapping in on every punch; Fury and Joshua wincing; the last flurry
    RW(tsl, [(tsl, (870, 470, 1.35)), (tsl + 1.62, (870, 462, 1.45))]),
    W(tsl + 1.62, "S", (836, 700, 1.5), ringside(face=[(tsl + 1.62, tsl + 2.12, 0.9, -0.45)],
                                                  looks=("dir", 0.0, -0.35, 0.0))),
    RW(tsl + 2.12, [(tsl + 2.12, (870, 462, 1.45)), (tdk, (870, 455, 1.55))]),
    # the wind-up: a slow push in on the two of them; the impact and the freeze
    RW(tdk, [(tdk, (900, 470, 1.3)), (tim, (905, 440, 1.62))], locked=True),
    RW(tim, [(tim, (905, 440, 1.62)), (tfa, (905, 436, 1.68))], locked=True),
    # the fall: the whole ring; flat out; the stars, close; the referee
    RW(tfa, [(tfa, (836, 470, 1.0)), (tdn, (836, 470, 1.0))], locked=True),
    RW(tdn, [(tdn, (836, 520, 1.0)), (m("c_dstars"), (836, 530, 1.06))], locked=True),
    RW(m("c_dstars"), [(m("c_dstars"), (1500, 650, 2.6)), (m("c_estars"), (1500, 650, 2.75))], locked=True, blur=1.5),
    RW(m("c_estars"), [(m("c_estars"), (200, 650, 2.6)), (m("c_ref3"), (200, 650, 2.75))], locked=True, blur=1.5),
    RW(m("c_ref3"), [(m("c_ref3"), (885, 470, 2.0)), (tbell2, (885, 470, 2.1))], blur=1.5),
    RW(tbell2, [(tbell2, (836, 500, 1.05)), (m("c_ann4"), (836, 510, 1.18))]),
]
S7 = [
    RW(m("c_ann4"), (836, 500, 1.3), ring_end()),
    RW(m("c_ed9"), on("R", 500, ED_R[1], "eddie", 0.55, dx=40), ring_end(close=True), blur=2.0),
    RW(m("c_da9"), on("R", *DA_R, "dana", 0.55, dx=-40), ring_end(close=True), blur=2.0),
    W(m("c_fj4"), "S", (836, 700, 1.5), ringside()),
    RW(tt0, [(tt0, (836, 520, 1.12)), (m("glance"), (836, 520, 1.2))], ring_end()),
    RW(m("climb"), (840, 500, 1.3), ring_end()),
    RW(m("rollout"), [(m("rollout"), (836, 520, 1.12)), (m("c_end"), (980, 520, 1.12))], ring_end()),
    W(m("c_end"), "S", [(m("c_end"), (836, 690, 1.35)), (m("black"), (836, 700, 1.55))],
      ringside(face=[(m("c_end"), 1e9, -0.15, -0.05)], looks=("dir", 0.9, 0.0, 0.25))),
    card(m("black"), "black"),
]

SHOTS = finish(sorted(S1 + S1b + S2 + S2b + S3 + S4 + S4b + S5 + S6 + S7, key=lambda s: s["t"]), TL["total"])
# the framing pass (tools/framing.py): per shot a camera correction (move x, move y, zoom) that keeps every head
# wholly in frame; keyed by the shot's signature, so an edited shot simply goes uncorrected until it is re-fitted
FRAMING_FILE = Path(__file__).with_name("framing.json")


def signature(s):
    items = [sorted((k, repr(v)) for k, v in it.items()) for it in s.get("cast", [])]
    return hashlib.md5(repr((s.get("plate"), round(s["t"], 2), round(s["end"], 2), s.get("cams"), items)).encode()
                       ).hexdigest()[:12]


if not os.environ.get("FRAMING_RAW") and FRAMING_FILE.exists():
    _fits = json.loads(FRAMING_FILE.read_text())
    for _s in SHOTS:
        _c = _fits.get(signature(_s)) if _s.get("kind") == "world" else None
        if _c:
            _s["corr"] = tuple(_c)
            _s["cams"] = [(tk, (c[0] + _c[0], c[1] + _c[1], c[2] * _c[2])) for tk, c in _s["cams"]]

CAPTIONS = [(s["t"] + 0.3, min(s["end"], s["t"] + 3.3), "place", *s["caption"]) for s in SHOTS if s.get("caption")]


def shot_at(t):
    from film.actors import _install_camera
    _install_camera()                    # the fight's camera shakes and snap zooms (render is loaded by now)
    return _shot_at(SHOTS, t)


# every drawing the film uses (built before a render)
DRAW = {}
for s in SHOTS:
    for it in s.get("cast", []):
        if "who" in it:
            from film.actors import key_of
            names = {v for _, v in it["pose"]} if isinstance(it["pose"], list) else {it["pose"]}
            ws = it.get("walk") or []
            for w in (ws if isinstance(ws, list) else [ws]):
                names |= set(w.get("frames", []))
            for n in names:
                DRAW[key_of(it["who"], n)] = key_of(it["who"], n)

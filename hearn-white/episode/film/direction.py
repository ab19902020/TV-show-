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
          "A": "boxing/arena-wide", "R": "boxing/ring-side", "S": "boxing/ringside"}
# perspective of each set: plate px per cm = (y - horizon) * k at floor height y
PPC = {"P": (400, 0.0100), "B": (470, 0.0204), "C": (356, 0.0082), "D": (350, 0.0113), "A": (514, 0.0097),
       "R": (289, 0.0065), "S": (640, 0.0113)}
# what stands in front of the people: the arena's near ring rope and corner posts
OCCL = {"A": {"ropes": [[(150, 646), (1530, 646), (1530, 664), (150, 664)],
                        [(146, 466), (190, 466), (190, 702), (146, 702)], [(262, 486), (306, 486), (306, 674), (262, 674)],
                        [(1368, 486), (1414, 486), (1414, 674), (1368, 674)],
                        [(1486, 466), (1532, 466), (1532, 702), (1486, 702)]]}}
CM = {"eddie": 191, "dana": 170, "tyson": 206, "joshua": 198, "announcer": 175, "referee": 180, "attendant": 160,
      "security": 183}
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
S1 = [
    card(m("title"), "title"),
    W(m("open"), "P", [(m("open"), (836, 470, 1.0)), (m("c_sec1"), (760, 455, 1.18))], press),
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


bay = [P("dana", keys((0, "q34"), (ls("L006") - 0.1, "front"), (wt("L006", "half") - 0.1, "shrug"),
                      (wt("L006", "they're") - 0.1, "palms"), (le("L006") + 0.3, "q34"), (m("look_cam") - 0.05, "front")),
         DA_B)] + trolley_group(tro_b0, tro_b1, -350, 1900, 560, "B", tail=200)
shoe = [P("dana", "climb", (1000, 600), dy=[(m("c_shoe"), 150.0), (m("c_shoe") + 0.35, 140.0),
                                             (m("c_shoe") + 0.95, -330.0)], z=1, shadow=False,
           clip=600 - 0.9 * 250),
        dict(prop="towel-pile", at=(1000, 600 - 0.86 * 250), h=150, z=2,
             dy=[(m("c_shoe") + 0.8, 300.0), (m("c_shoe") + 1.1, 0.0)]),
        dict(prop="trolley-side", at=(1000, 600), h=250, z=3)]
S1b = [
    W(m("c_bay"), "B", [(m("c_bay"), (836, 470, 1.0)), (m("trolley"), (790, 440, 1.12))], bay,
      caption=("LOADING BAY", "Same night · outside")),
    W(m("trolley"), "B", (780, 420, 1.15), bay),
    W(m("look_cam"), "B", [(m("look_cam"), on("B", *DA_B, "dana", 0.55)), (m("c_shoe"), on("B", *DA_B, "dana", 0.47))],
      bay, blur=2.5),
    W(m("c_shoe"), "B", [(m("c_shoe"), (1000, 420, 2.2)), (m("c_track"), (1000, 430, 2.4))], shoe, blur=3.0),
]

# ====================================================================== 2. the corridor
SEC_C, Y_C = (1000, 680), 700
TH_C = 90 * (Y_C - 356) * 0.0082                         # the trolley's height in the corridor


def corridor_trolley():
    """the trolley's whole journey down the corridor: in, stopped at security, on past him, the bump"""
    stop = m("c_track") + 1.7
    path = [(m("c_track"), (-350, Y_C)), (stop, (760, Y_C)), (m("aside"), (760, Y_C)),
            (m("aside") + 1.5, (1200, Y_C))]
    return path


SEC_CAST = P("security", keys((0, "stop"), (m("c_track") + 1.75, "front"), (ls("L012") - 0.1, "gesture"),
                              (le("L012") + 0.2, "front"), (m("aside"), "gesture"), (m("aside") + 1.2, "crossed")),
             SEC_C, look=None)


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


TROLLEY_TOP = Y_C - 0.86 * TH_C


def corridor_b():
    """the second half: the trolley rolls on, the dome rises, the cable protector, the tumble"""
    t0, tb = m("c_inside"), m("bump")
    path = [(t0, (300, Y_C)), (tb, (930, Y_C))]
    jolt = [(tb, 0.0), (tb + 0.08, 9.0), (tb + 0.35, 4.0), (tb + 0.7, 0.0)]
    tw = [(a, (x, y - 0.86 * TH_C)) for a, (x, y) in path]
    ft = m("tumble")
    dana_path = [(t0, (path[0][1][0] + 105, TROLLEY_TOP + 18)), (tb, (930 + 105, TROLLEY_TOP + 18)),
                 (ft, (1035, TROLLEY_TOP + 10)), (ft + 0.35, (1040, TROLLEY_TOP - 40)),
                 (ft + 0.8, (1080, Y_C - 60)), (ft + 1.1, (DA_LAND[0], DA_LAND[1])), (ft + 1.4, DA_LAND)]
    dana = P("dana", keys((t0, "peek"), (ft, "tumble1"), (ft + 0.35, "tumble2"), (ft + 0.8, "tumble3"),
                          (ft + 1.1, "prone"), (m("landed") + 0.6, "towel_head")),
             dana_path, z=Y_C + 1.6, clip=[(0, TROLLEY_TOP + 10), (ft, None)],
             dy=[(t0, -120.0), (t0 + 0.9, -70.0), (t0 + 1.5, 33.0), (tb, 33.0), (tb + 0.1, 41.0), (ft, 41.0),
                 (ft + 0.01, 0.0)],
             rot=[(ft, 0.0), (ft + 0.35, -25.0), (ft + 0.8, 15.0), (ft + 1.1, 0.0)],
             shadow=False, scale=1.0, floor=Y_C)
    return [dict(prop="cable-ramp", at=(1000, Y_C + 6), h=55, z=Y_C - 5),
            dict(prop="trolley-side", at=path, h=TH_C, z=Y_C + 1, rot=jolt, pivot=1.0),
            dict(prop="towel-pile", at=tw, h=0.42 * TH_C, z=Y_C + 0.5, rot=jolt, show=[(m("tumble"), 1e9)]),
            dict(fn="lid", at=[(a, (x, y - 0.93 * TH_C)) for a, (x, y) in path], w=1.08 * TH_C, z=Y_C + 1.5,
                 rot=[(t0 + 0.6, 0.0), (t0 + 1.4, 21.0), (tb, 21.0), (tb + 0.12, 80.0), (m("tumble") + 0.3, 110.0)]),
            P("attendant", "push", [(a, (x - 0.8 * TH_C, y)) for a, (x, y) in path], z=Y_C + 2, steps=True,
              rot=[(tb, 0.0), (tb + 0.1, 6.0), (tb + 0.5, 0.0)]),
            dana]


FU_C, AJ_C, DA_LAND, ED_C = (1300, 705), (1490, 690), (1090, 712), (540, 706)
S2 = [
    W(m("c_track"), "C", [(m("c_track"), (330, 560, 1.7)), (m("c_track") + 1.7, (840, 540, 1.55))], corridor_a(),
      caption=("BACKSTAGE", "Security checkpoint")),
    W(ls("L009"), "C", (840, 540, 1.55), corridor_a()),
    W(m("c_bin1"), "C", (790, 470, 3.0), corridor_a(), blur=2.0),
    W(m("lid"), "C", (840, 520, 1.5), corridor_a()),
    W(ls("L011") + 0.05, "C", on("C", 760 - 0.8 * TH_C, Y_C, "attendant", 0.8, dx=40), corridor_a(), blur=2.0),
    W(m("c_sec3"), "C", on("C", *SEC_C, "security", 0.55), corridor_a(), blur=2.0),
    W(m("c_att3"), "C", on("C", 760 - 0.8 * TH_C, Y_C, "attendant", 0.78, dx=40), corridor_a(), blur=2.0),
    W(m("aside"), "C", [(m("aside"), (860, 520, 1.45)), (m("c_inside"), (960, 520, 1.5))], corridor_a()),
]


def fury_corridor(extra=()):
    fury = P("tyson", keys((0, "front"), (ls("L017") - 0.1, "crossed"), (le("L017") + 0.2, "front"),
                           (m("c_eddie"), "crossed")), FU_C, look="dana")
    return [fury]


S2b = [
    W(m("c_inside"), "C", [(m("c_inside"), (470, 560, 2.3)), (m("bump"), (900, 560, 2.3))], corridor_b(), blur=1.5),
    W(m("bump"), "C", [(m("bump"), (1000, TROLLEY_TOP - 40, 6.5)), (m("tumble"), (1000, TROLLEY_TOP - 40, 7.0))],
      corridor_b(), blur=3.0, subject=dict(who="dana", frac=1.0, dx=0.0, up=0.0, hmax=0.62)),
    W(m("tumble"), "C", (1080, 520, 1.25), corridor_b() + fury_corridor()),
]

# ====================================================================== 3. Fury finds a promoter


def dana_corr():
    return P("dana", keys((0, "towel_head"), (m("c_eddie") + 1.2, "towel_shoulder"), (m("c_neg") + 0.55, "front"),
                          (ls("L027") - 0.1, "point"), (le("L027") + 0.3, "front"),
                          (ls("L030") - 0.1, "shrug"), (le("L030") + 0.4, "crossed")), DA_LAND, look=None)


def joshua_corr():
    return P("joshua", keys((0, "front"), (m("c_fj1") - 0.5, "crossed")), AJ_C, show=[(m("c_aj") - 0.2, 1e9)])


def eddie_corr():
    walk_t0, walk_t1 = m("c_eddie"), m("c_eddie") + 1.8
    return P("eddie", keys((0, "q34"), (ls("L024") - 0.1, "point"), (le("L024") + 0.3, "q34"),
                           (m("c_neg") + 0.05, "point"), (m("c_neg") + 1.0, "front"),
                           (m("c_list"), "palms"), (wt("L029", "medicals") - 0.1, "point"),
                           (wt("L029", "no") - 0.1, "stop"), (wt("L029", "wrestling") - 0.1, "shrug"),
                           (le("L029") + 0.2, "front"), (ls("L031") - 0.1, "hips")),
             [(walk_t0, (180, ED_C[1])), (walk_t1, ED_C)],
             walk=dict(frames=[f"w{i}" for i in range(8)], cycle=1.0, t0=walk_t0, t1=walk_t1),
             mirror=keys((0, False), (ls("L024") - 0.1, True), (le("L024") + 0.3, False), (m("c_neg") + 0.05, True),
                         (m("c_neg") + 1.0, False), (wt("L029", "medicals") - 0.1, True), (wt("L029", "no") - 0.1, False)),
             show=[(m("c_eddie"), 1e9)],
             holds=[dict(t0=m("c_neg") + 0.35, t1=m("c_neg") + 1.0, prop="towel", at=(75, 470), h=95, grip=(0.3, 0.05))])


def corridor_c():
    """after the landing: the tipped trolley, the ramp, everyone"""
    xt = 930
    return [dict(prop="cable-ramp", at=(1000, Y_C + 6), h=55, z=Y_C - 5),
            dict(prop="trolley-side", at=(xt, Y_C), h=TH_C, z=Y_C + 1),
            dict(fn="lid", at=(xt, Y_C - 0.93 * TH_C), w=1.08 * TH_C, z=Y_C + 1.5, rot=110.0),
            P("attendant", "push", (xt - 0.8 * TH_C, Y_C), z=Y_C + 2, show=[(0, m("c_eddie"))]),
            SEC_CAST | dict(at=(870, 660)),
            dana_corr(), joshua_corr(), eddie_corr(),
            dict(prop="towel", at=(1050, 772), h=60, show=[(m("c_neg") + 1.0, 1e9)], z=771,
                 dy=[(m("c_neg") + 1.0, 120.0), (m("c_neg") + 1.25, 0.0)])] + fury_corridor()


CC = corridor_c()
mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
S3 = [
    W(m("landed"), "C", [(m("landed"), (1220, 520, 1.6)), (m("c_dana1"), (1230, 520, 1.7))], CC),
    W(m("c_dana1"), "C", on("C", DA_LAND[0], DA_LAND[1], "dana", 0.9, dx=0), CC, blur=2.0),
    W(m("c_fury2"), "C", on("C", *FU_C, "tyson", 0.5), CC, blur=2.0),
    W(m("c_dana2"), "C", on("C", DA_LAND[0], DA_LAND[1], "dana", 0.85), CC, blur=2.0),
    W(m("c_fury3"), "C", [(m("c_fury3"), on("C", *FU_C, "tyson", 0.55)), (m("c_aj"), on("C", *FU_C, "tyson", 0.5))],
      CC, blur=2.0),
    W(m("c_aj") - 0.2, "C", (1330, 500, 1.5), CC),
    W(ls("L020") - 0.1, "C", on("C", *AJ_C, "joshua", 0.5), CC, blur=2.0),
    W(m("c_fury4"), "C", (1330, 500, 1.5), CC),
    W(m("c_eddie"), "C", [(m("c_eddie"), (836, 470, 1.0)), (m("dart") + 0.6, (900, 480, 1.08))], CC),
    W(ls("L022") - 0.05, "C", [(ls("L022") - 0.05, on("C", *ED_C, "eddie", 0.55)),
                               (le("L022") + 0.2, on("C", *ED_C, "eddie", 0.5))], CC, blur=2.0),
    W(m("c_dana3"), "C", on("C", *DA_LAND, "dana", 0.66, up=0.1), CC, blur=2.0),
    W(m("c_ed4"), "C", on("C", *ED_C, "eddie", 0.62), CC, blur=2.0),
    W(m("c_dana4"), "C", on("C", *DA_LAND, "dana", 0.64, up=0.1), CC, blur=2.0),
]

# ====================================================================== 4. negotiations
two = mid(ED_C, DA_LAND)
S4 = [
    W(m("c_neg"), "C", [(m("c_neg"), (two[0], 500, 1.55)), (m("c_fine"), (two[0], 510, 1.7))], CC),
    W(m("c_fine"), "C", on("C", *ED_C, "eddie", 0.5), CC, blur=2.0),
    W(m("surprise"), "C", (two[0], 480, 1.8), CC, blur=1.0),
    W(m("c_list"), "C", [(m("c_list"), on("C", *ED_C, "eddie", 0.8)), (le("L029"), on("C", *ED_C, "eddie", 0.68))],
      CC, blur=1.5),
    W(m("c_dana5"), "C", on("C", *DA_LAND, "dana", 0.66, up=0.06), CC, blur=2.0),
    W(m("c_ed5"), "C", [(m("c_ed5"), on("C", *ED_C, "eddie", 0.6)), (m("c_fj1"), on("C", *ED_C, "eddie", 0.48))],
      CC, blur=2.0),
    W(m("c_fj1"), "C", [(m("c_fj1"), on("C", 1430, 768, "tyson", 0.62)), (m("c_prep"), on("C", 1430, 768, "tyson", 0.56))],
      CC, blur=1.0),
]
ED_D, DA_D = (600, 612), (1080, 618)
SHADOW = ["jab", "guard", "jab2", "guard_high", "jab3", "guard", "jab4", "guard"]
tp = m("c_prep")
prep = [P("eddie", "tired", ED_D),
        P("dana", keys(*[(tp + 0.15 + 0.2 * i, SHADOW[i % len(SHADOW)]) for i in range(13)],
                       (tp + 2.8, "tired")), DA_D, look="down",
          rot=[(tp + 2.6, 0.0), (tp + 2.9, 4.0), (tp + 3.4, 2.0)])]
S4b = [W(tp, "D", [(tp, (836, 470, 1.0)), (m("c_arena"), (840, 480, 1.1))], prep,
         caption=("DRESSING ROOM", "Ten minutes later"))]

# ====================================================================== 5. the special announcement
ED_A, DA_A, AN_A, RF_A = (440, 655), (1240, 655), (836, 650), (1190, 612)
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
ED_R, DA_R, RF_R = (560, 785), (1110, 785), (1390, 640)
GUARD_FACE = None


def shuffle(x0, t0, t1, amp=18, rate=1.4, ph=0.0):
    import math
    out, t = [], t0
    while t < t1:
        out.append((t, (x0 + amp * math.sin(2 * math.pi * rate * (t - t0) + ph), ED_R[1])))
        t += 0.12
    return out


tb, tf = m("bell"), m("faceoff")
e1, e2, e3a, e3b, e3c = m("ex1"), m("ex2"), m("ex3a"), m("ex3b"), m("ex3c")
ts, tbell2 = m("sep"), m("bell2")
CL_E, CL_D = (600, 785), (1075, 785)          # the clinch: heads together over the middle
eddie_fight = P("eddie",
                keys((0, "guard"), (e1 + 0.35, "wind"), (e1 + 0.55, "jab_long"), (e1 + 1.15, "guard"),
                     (e2 + 0.35, "block"), (m("c_ed7") + 0.1, "guard"),
                     (e3a + 0.3, "jab"), (e3a + 0.8, "guard"), (e3b + 0.35, "cross"), (e3b + 1.1, "guard"),
                     (ts + 0.05, "tired"), (ts + 1.2, "guard"), (tbell2 + 0.3, "arms_up"), (m("c_ann4"), "guard"),
                     (m("c_trolley") + 2.6 + (le("L057") - ls("L057")), "jab_long"), (m("climb") + 0.4, "guard")),
                keys(*shuffle(ED_R[0], 0, e1 + 0.35, 14, 1.1), (e1 + 0.55, (ED_R[0] + 110, ED_R[1])),
                     (e1 + 1.3, ED_R), (e3a + 0.3, (ED_R[0] + 60, ED_R[1])), (e3a + 0.8, ED_R),
                     (e3b + 0.35, (ED_R[0] + 95, ED_R[1])), (e3b + 1.2, (ED_R[0] + 80, ED_R[1])),
                     (e3c + 0.9, CL_E), (ts + 0.05, CL_E), (ts + 0.5, (600, ED_R[1])), (ts + 1.2, (600, ED_R[1])),
                     (ts + 1.65, CL_E), (tbell2 + 0.3, CL_E), (tbell2 + 0.8, (560, ED_R[1])), (m("c_ann4") - 0.01, (560, ED_R[1])),
                     (m("c_ann4"), (500, ED_R[1]))),
                rot=keys((0, 0.0), (e3b + 0.35, 0.0), (e3b + 0.6, 9.0), (e3b + 1.1, 5.0), (e3c + 0.9, 9.0),
                         (ts + 0.05, 9.0), (ts + 0.4, 0.0), (ts + 0.6, -6.0), (ts + 0.85, 5.0), (ts + 1.05, -4.0),
                         (ts + 1.2, 0.0), (ts + 1.65, 9.0), (tbell2 + 0.3, 9.0), (tbell2 + 0.5, 0.0)),
                ease=True)
dana_fight = P("dana",
               keys((0, "guard"), (e1 + 0.5, "lean_back"), (e1 + 0.8, "guard_high"), (e1 + 0.95, "lean_back"),
                    (e1 + 1.1, "guard_high"), (e1 + 1.25, "lean_back"), (e1 + 1.6, "guard"),
                    (e2 + 0.25, "jab"), (e2 + 0.75, "guard"),
                    (e3a + 0.35, "crouch_guard"), (e3a + 0.95, "guard"), (e3b + 0.35, "jab4"), (e3b + 1.1, "guard"),
                    (e3c + 0.6, "tired"), (ts + 1.2, "guard"), (ts + 1.55, "tired"), (tbell2 + 0.3, "arms_up"),
                    (m("c_ann4"), "guard"),
                    (m("climb"), "crouch_guard")),
               keys(*shuffle(DA_R[0], 0, e1 + 0.5, 14, 1.25, 1.3), (e1 + 0.5, (DA_R[0] + 30, DA_R[1])),
                    (e1 + 1.6, DA_R), (e2 + 0.25, (DA_R[0] - 120, DA_R[1])), (e2 + 0.8, DA_R),
                    (e3b + 0.35, (DA_R[0] - 95, DA_R[1])), (e3b + 1.2, (DA_R[0] - 80, DA_R[1])),
                    (e3c + 0.9, CL_D), (ts + 0.05, CL_D), (ts + 0.5, (1070, DA_R[1])), (ts + 1.2, (1070, DA_R[1])),
                    (ts + 1.65, CL_D), (tbell2 + 0.3, CL_D), (tbell2 + 0.8, (1110, DA_R[1])),
                    (m("glance") + 0.1, (1110, DA_R[1])), (m("climb") + 0.35, (1080, DA_R[1])), (m("climb") + 0.75, (995, DA_R[1] - 4))),
               rot=keys((0, 0.0), (e1 + 0.5, 0.0), (e1 + 0.7, 16.0), (e1 + 0.85, 24.0), (e1 + 1.0, 12.0),
                        (e1 + 1.15, 22.0), (e1 + 1.3, 10.0), (e1 + 1.6, 0.0), (e3b + 0.35, 0.0), (e3b + 0.6, -9.0),
                        (e3b + 1.1, -5.0), (e3c + 0.9, -9.0), (ts + 0.05, -9.0), (ts + 0.4, 0.0),
                        (ts + 0.6, 6.0), (ts + 0.85, -5.0), (ts + 1.05, 4.0), (ts + 1.2, 0.0), (ts + 1.65, -9.0),
                        (tbell2 + 0.3, -9.0), (tbell2 + 0.5, 0.0)),
               dy=keys((0, 0.0), (m("climb") + 0.35, 0.0), (m("climb") + 0.7, 190.0), (m("climb") + 1.4, -440.0)),
               ease=True, clip=keys((0, None), (m("climb") + 0.72, 812 - 0.9 * 90 * (812 - 289) * 0.0065)))
ref_fight = P("referee", keys((0, "stop"), (ls("L045") - 0.1, "break"), (ls("L045") + 1.2, "stop"),
                              (tbell2 + 0.6, "card")), RF_R, look=None,
              show=[(0, m("c_ann4"))])
NEAR = dict(fn="near_ropes", ys=[850, 975], z=5000, w=20, blur=3.5)


def ring(extra=()):
    return [eddie_fight, dana_fight, ref_fight, NEAR] + list(extra)


# 7: the announcer back in, then the trolley
tt0 = m("c_trolley")
RING_TROLLEY = trolley_group(tt0, tt0 + 2.0, -400, 990, 812, "R", tail=230)
# the trolley group's own items stop at its last key: carry them on for the roll-out
for it in RING_TROLLEY[:3]:
    it["at"] = it["at"] + [(m("rollout"), it["at"][-1][1]),
                           (m("rollout") + 1.8, (it["at"][-1][1][0] + 1260, it["at"][-1][1][1]))]
    it["show"] = [(tt0, 1e9)]
RING_TROLLEY = RING_TROLLEY[:3]
ann_ring = P("announcer", "mic", (835, 700), show=[(m("c_ann4"), m("c_trolley"))])
# Dana into the bin: behind the trolley (drawn first), sinking out of sight below its rim
cut_climb = m("climb")


def ring_end():
    d = dict(dana_fight)
    return [eddie_fight, d, ref_fight, ann_ring, NEAR] + RING_TROLLEY


S6 = [
    W(tb, "A", [(tb, (836, 300, 2.4)), (tf, (836, 320, 2.6))], [dict(prop="boxing-bell", at=(836, 420), h=230)],
      blur=10.0, shake=True),
    W(tf, "R", [(tf, (836, 520, 1.12)), (m("cough"), (836, 520, 1.25))], ring()),
    W(m("c_ty1"), "S", (650, 700, 1.9), ringside(face=[(m("c_ty1"), m("c_fight"), -0.6, -0.3)])),
    W(m("c_fight"), "R", (836, 520, 1.12), ring()),
    W(m("c_ed7"), "R", on("R", ED_R[0], ED_R[1], "eddie", 0.55, dx=40), ring(), blur=2.0),
    W(m("c_da7"), "R", on("R", *DA_R, "dana", 0.55, dx=-40), ring(), blur=2.0),
    W(m("c_ed8"), "R", on("R", ED_R[0], ED_R[1], "eddie", 0.55, dx=40), ring(), blur=2.0),
    W(m("c_ex3"), "R", [(m("c_ex3"), (836, 520, 1.12)), (m("c_cl1"), (836, 500, 1.3))], ring()),
    W(m("c_cl1"), "R", [(m("c_cl1"), (840, 420, 2.0)), (m("c_ref2"), (840, 420, 2.15))], ring(), blur=1.5),
    W(m("c_ref2"), "R", (836, 520, 1.15), ring()),
    W(m("c_fj3"), "S", (836, 700, 1.5), ringside()),
    W(m("c_cl2"), "R", [(m("c_cl2"), (840, 400, 2.3)), (m("bell2"), (840, 400, 2.6))], ring(), blur=2.0),
    W(tbell2, "R", [(tbell2, (836, 520, 1.12)), (m("c_ann4"), (836, 510, 1.18))], ring()),
]
S7 = [
    W(m("c_ann4"), "R", (836, 500, 1.3), ring_end()),
    W(m("c_ed9"), "R", on("R", *ED_R, "eddie", 0.55, dx=40), ring_end(), blur=2.0),
    W(m("c_da9"), "R", on("R", *DA_R, "dana", 0.55, dx=-40), ring_end(), blur=2.0),
    W(m("c_fj4"), "S", (836, 700, 1.5), ringside()),
    W(tt0, "R", [(tt0, (836, 520, 1.12)), (m("glance"), (836, 520, 1.2))], ring_end()),
    W(m("climb"), "R", (840, 500, 1.3), ring_end()),
    W(m("rollout"), "R", [(m("rollout"), (836, 520, 1.12)), (m("c_end"), (980, 520, 1.12))], ring_end()),
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
    return _shot_at(SHOTS, t)


# every drawing the film uses (built before a render)
DRAW = {}
for s in SHOTS:
    for it in s.get("cast", []):
        if "who" in it:
            from film.actors import key_of
            names = {v for _, v in it["pose"]} if isinstance(it["pose"], list) else {it["pose"]}
            names |= set(it.get("walk", {}).get("frames", []))
            for n in names:
                DRAW[key_of(it["who"], n)] = key_of(it["who"], n)

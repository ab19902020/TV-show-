"""The shot list of The Undercard (v5). Every shot is a camera in one of the sets (1x plate px) with the people and
props of that moment drawn at true scale (film/actors.py: s["cast"]); times come from the dialogue edit's marks
(film/timeline.py), so the picture follows the voices. The pack's plan (pack/v5/SHOT_AND_ANIMATION_PLAN.md) shot by
shot: a held camera while people act, a cut when the story moves, close-ups on the acting heads (bust_*), the
fall as a chain of causes, five fight beats with real contact (the paired drawings, pair_*), one impact graphic.

Cameras: cam = (cx, cy, zoom), zoom 1 = the set's full width. on(x, y, who) frames a person standing at (x, y): frac
is how much of their height fills the frame (0.5 a medium close-up, 0.9 a full figure, ~0.3 a close-up on a bust),
up shifts the frame up. Sets: P press area, B loading bay, C corridor, Q the corridor's reverse angle, I inside the
bin, A arena wide, R inside the ring, K the red corner, S ringside seats."""
import hashlib
import json
import math
import os
from pathlib import Path

import cv2
import numpy as np

from studio.film import ep
from studio.film.shots import Marks, card, finish, shot_at as _shot_at, world
from studio.paths import LIBRARY

from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt, we = T.m, T.ls, T.le, T.wt, T.we

PLATES = {"P": "boxing/press-area", "B": "boxing/loading-bay", "C": "boxing/corridor", "Q": "boxing/corridor-reverse",
          "I": "boxing/inside-bin", "A": "boxing/arena-wide", "R": "boxing/ring-side", "K": "boxing/ring-corner",
          "S": "boxing/ringside"}
# perspective of each set: plate px per cm = (y - horizon) * k at floor height y
PPC = {"P": (400, 0.0100), "B": (470, 0.0204), "C": (356, 0.0082), "Q": (330, 0.0068), "I": (0, 0.00502),
       "A": (514, 0.0097), "R": (289, 0.0065), "K": (470, 0.0206), "S": (640, 0.0113)}


def _towel_front():
    """inside the bin: the towels heaped at the bottom of the frame are in front of Dana. Their outline, from the
    painting itself (the bright cloth against the dark liner), a little inside the cloth's ink"""
    im = cv2.imread(str(LIBRARY / "backgrounds" / "boxing" / "inside-bin.png"))
    v = im.max(2)
    bright = (v > 150).astype(np.uint8)
    bright[:330] = 0
    bright = cv2.morphologyEx(bright, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(bright, 8)
    keep = np.zeros_like(bright)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] > 20000:
            keep[lab == k] = 1
    keep = cv2.erode(keep, np.ones((7, 7), np.uint8))
    cs, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [[(float(x), float(y)) for x, y in cv2.approxPolyDP(c, 2.0, True)[:, 0]] for c in cs]


def _rail():
    """the arena wide: the red rail of the front seats at the foot of the ring steps, in front of anyone on them"""
    im = cv2.imread(str(LIBRARY / "backgrounds" / "boxing" / "arena-wide.png")).astype(np.int16)
    b, g, r = im[..., 0], im[..., 1], im[..., 2]
    red = ((r > 120) & (r > g + 60) & (r > b + 50)).astype(np.uint8)
    red[:790] = 0
    red[:, 470:] = 0
    red = cv2.morphologyEx(red, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(red, 8)
    keep = np.zeros_like(red)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] > 400:
            keep[lab == k] = 1
    cs, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [[(float(x), float(y)) for x, y in cv2.approxPolyDP(c, 1.5, True)[:, 0]] for c in cs]


# what stands in front of the people: the arena's near ring rope and corner posts (and the seat rail at the foot of
# the steps, used on its own); the towels in the bin
OCCL = {"A": {"rail": _rail()},
        "I": {"towels": _towel_front()}}
CM = {"eddie": 191, "dana": 170, "tyson": 206, "joshua": 198, "announcer": 175, "referee": 180, "attendant": 160,
      "security": 183}
CROWD_FLASH = {"A": [((20, 40, 1650, 470), 9.0, 2)], "S": [((0, 0, 1672, 210), 3.0, 5)],
               "K": [((0, 0, 1672, 380), 6.0, 7)]}
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
    if any(str(it.get("pose", "")).startswith(("bust_", "close_")) for it in cast):
        kw.setdefault("locked", True)                 # a close-up on an acting head is framed by hand
    first = cams[0][1]
    if isinstance(first, OnCam):
        kw.setdefault("subject", dict(who=first.who, frac=first.frac, dx=first.dx, up=first.up))
    layers = [("props", "scene")] + list(extra_layers)
    if p in CROWD_FLASH:
        kw.setdefault("flashes", CROWD_FLASH[p])
    occl = kw.pop("occl", True)
    if p in OCCL and occl:
        layers += [("occl", k) for k in OCCL[p] if occl is True or k in occl]
    return world(t, PLATES[p], cams[0][1], cams=cams, layers=layers, cast=cast, ppc=PPC[p], blur=blur,
                 drift=drift, **kw) | {"plate": p}


def P(who, pose, at, **kw):
    return dict(who=who, pose=pose, at=at, **kw)


# Eddie's and Dana's acting heads on their own bodies (tools/make_closeups.py): a close-up is a whole person
CLOSE = {("eddie", "smug"): "close_smug_front", ("eddie", "glare"): "close_glare_front",
         ("eddie", "profile"): "close_glare_front", ("eddie", "up"): "close_up_front",
         ("eddie", "sweat"): "close_sweat_front", ("dana", "smug"): "close_smug_front",
         ("dana", "side"): "close_side_q34", ("dana", "blush"): "close_blush_front",
         ("dana", "panic"): "close_panic_front"}


def B(who, name, at, **kw):
    """a close-up on an acting head: Eddie and Dana on their own bodies (CLOSE), Fury and Joshua's busts (drawn
    with their shoulders) standing where their bodies would"""
    kw.setdefault("shadow", False)
    return dict(who=who, pose=CLOSE.get((who, name), f"bust_{name}"), at=at, **kw)


def bust_cam(p, who, name, at, mirror=False, dx=0.0, room=0.12):
    """the close-up on a bust: from a little above the head to just above the drawing's cut-off bottom edge (that
    edge is never in shot), centred on the head"""
    from film.actors import CAST, PEOPLE, feet_mid, sheet_fac
    pose = B(who, name, at)["pose"]
    key = f"{PEOPLE[who][0]}:{pose}"
    d, _ = CAST.get(key)
    x, y = at
    k = h_of(p, who, y) / PEOPLE[who][2] * sheet_fac(key)          # plate px per sheet px
    fx, fy = feet_mid(key)
    w_, h_ = d.size(1.0)
    by1 = d.oy + h_ / d.S
    hx0, hy0, hx1, hy1 = d.spec["head"]
    top = y + (hy0 - fy) * k - room * (hy1 - hy0) * k
    if pose.startswith("close_"):                                  # a whole person: head and shoulders, the chest
        bot = y + (hy1 - fy) * k + 0.62 * (hy1 - hy0) * k
    else:
        bot = y + (by1 - fy) * k - 0.07 * (by1 - hy0) * k
    hx = ((hx0 + hx1) / 2 - fx) * k
    return (x + (-hx if mirror else hx) + dx, (top + bot) / 2, 941.0 / (bot - top))


def BW(t, p, who, name, at, mirror=False, others=(), dx=0.0, **kw):
    """a close-up shot on an acting head, framed by bust_cam"""
    kw.setdefault("blur", 3.0)
    kw.setdefault("drift", 0.0)
    return W(t, p, bust_cam(p, who, name, at, mirror, dx), [B(who, name, at, mirror=mirror)] + list(others), **kw)


def hand_at(p, who, pose, at, side):
    """where a person's hand is (the far end of their reach towards `side`) in plate px, standing at `at`"""
    from film.actors import PEOPLE, feet_mid, sheet_fac
    from film.things import hand_tip
    key = f"{PEOPLE[who][0]}:{pose}"
    hx, hy = hand_tip(key, side)
    fx, fy = feet_mid(key)
    k = h_of(p, who, at[1]) / PEOPLE[who][2] * sheet_fac(key)
    return (at[0] + (hx - fx) * k, at[1] - (fy - hy) * k)


def keys(*kv):
    return list(kv)


def wob(t0, dur, amp, n=3, base=0.0):
    """a wobble: rot keys swinging amp, -amp... dying out over dur"""
    out = [(t0, base)]
    for i in range(1, n + 1):
        out.append((t0 + dur * i / (n + 1), base + amp * (1 - i / (n + 1)) * (-1) ** (i + 1)))
    out.append((t0 + dur, base))
    return out


def arc(t0, t1, p0, p1, height, n=8):
    """keys along a thrown arc from p0 to p1 (plate px), `height` px above the straight line at the top; falling
    under gravity (time runs even, the drop speeds up)"""
    out = []
    for i in range(n + 1):
        u = i / n
        out.append((t0 + (t1 - t0) * u, (p0[0] + (p1[0] - p0[0]) * u,
                                        p0[1] + (p1[1] - p0[1]) * u - height * 4 * u * (1 - u))))
    return out


def slide(t0, t1, p0, p1, n=6):
    """keys for something sliding to a stop (friction: fast, then slower)"""
    return [(t0 + (t1 - t0) * i / n, (p0[0] + (p1[0] - p0[0]) * (1 - (1 - i / n) ** 2),
                                      p0[1] + (p1[1] - p0[1]) * (1 - (1 - i / n) ** 2))) for i in range(n + 1)]


# ---------------------------------------------------------------------- the attendant and her trolley
TROLLEY_W = 326 / 276                                    # the trolley-side drawing's width per height
ATT_STEPS = ("step_a", "step_b", "step_c", "step_b")


def _reach(pose):
    """how far ahead of her feet her hands are in the pushing drawings (her heights)"""
    from film.actors import feet_mid, sheet_fac, PEOPLE
    from film.things import hand_tip
    key = f"laundry-attendant:{pose}"
    hx, _ = hand_tip(key, 1)
    fx, _ = feet_mid(key)
    return (hx - fx) * sheet_fac(key) / PEOPLE["attendant"][2]


def push(p, t0, t1, x0, x1, y, mirror=False, step=0.5, stop="brace", tail_pose=None, carry=()):
    """the attendant pushing the trolley from x0 to x1 (the trolley's middle, plate px, floor y) between t0 and t1:
    a step every `step` s with her weight on the planted foot (contact: the body holds; passing and push-off: it
    moves on), her hands locked on the handle (the trolley moves with her body), braking into `stop` at the end.
    -> (attendant item, trolley item, its path)"""
    th = 90 * (y - PPC[p][0]) * PPC[p][1]
    ha = CM["attendant"] * (y - PPC[p][0]) * PPC[p][1]
    sgn = -1 if mirror else 1
    n = max(1, int(round((t1 - t0) / step)))
    st = (t1 - t0) / n
    path, poses = [(t0, (x0, y))], [(t0 - 0.01, "step_a")]
    for i in range(n):
        a = t0 + i * st
        u0 = i / n
        u1 = (i + 1) / n
        xa = x0 + (x1 - x0) * u0
        xb = x0 + (x1 - x0) * u1
        path += [(a + 0.35 * st, (xa + 0.06 * (xb - xa), y)), (a + st, (xb, y))]
        poses += [(a, ATT_STEPS[i % 4]), (a + 0.45 * st, "step_b"), (a + 0.72 * st, "step_c")]
    poses.append((t1, stop))
    poses += list(carry)
    off = sgn * (0.5 * TROLLEY_W * th + _reach("step_a") * ha * 0.94)
    att = P("attendant", poses, [(t, (x - off, yy)) for t, (x, yy) in path], z=y + 2, ease=False,
            mirror=mirror)
    tro = dict(prop="trolley-side", at=path, h=th, z=y + 1, mirror=mirror)
    return att, tro, path


def towels_on(path, th, z, **kw):
    return dict(prop="towel-pile", at=[(a, (x, yy - 0.86 * th)) for a, (x, yy) in path], h=0.55 * th, z=z, **kw)


# ====================================================================== 1. Eddie's ban: press area
BOARD, ED_TAPE, ED_P, SEC_P = (520, 715), (705, 722), (905, 722), (1310, 705)
t_peel, t_drop = m("tape") + 0.2, m("admire") - 0.15
ed_press = P("eddie", keys((0, "stop"), (t_peel, "point"), (m("admire") + 0.05, "hips"), (ls("L001") - 0.05, "front"),
                           (wt("L001", "biggest") - 0.1, "palms"), (wt("L001", "improved") - 0.1, "point"),
                           (le("L001") + 0.3, "front"), (wt("L003", "nobody") - 0.1, "stop"),
                           (wt("L003", "banned") - 0.1, "point"), (le("L003") + 0.3, "front"),
                           (ls("L005") - 0.05, "shrug"), (wt("L005", "looks") - 0.1, "palms"),
                           (wt("L005", "you'll") - 0.1, "hips")),
             keys((0, ED_TAPE), (m("admire"), ED_TAPE), (m("admire") + 0.9, ED_P)), ease=True, steps=True,
             mirror=keys((0, False), (ls("L001") - 0.05, False), (wt("L001", "improved") - 0.1, False),
                         (le("L001") + 0.3, True), (wt("L003", "banned") - 0.1, False), (le("L003") + 0.3, True)),
             rot=keys((t_peel + 0.05, 0.0), (t_peel + 0.15, 3.0), (t_peel + 0.25, -3.0), (t_peel + 0.35, 3.0),
                      (t_peel + 0.45, -2.0), (t_peel + 0.6, 0.0)))
sec_press = P("security", keys((0, "crossed"), (ls("L004") - 0.1, "gesture"), (le("L004") + 0.3, "crossed")), SEC_P)
board = dict(fn="board", at=BOARD, h=480)
TAPE_AT = hand_at("P", "eddie", "stop", ED_TAPE, -1)
tape = dict(fn="tape", at=(TAPE_AT[0] + 20, TAPE_AT[1] + 10), w=92, t_peel=t_peel, t_drop=t_drop, follow="eddie", side=-1,
            drop_at=(640, 440), floor=724, drop_dx=-40, z=2000, show=[(t_peel, 1e9)])
tape_on_board = dict(tape, z=716, show=[(0, t_peel)])        # pressed on the board, under his arm
press = [ed_press, sec_press, board, tape_on_board, tape]
press_b = [P("eddie", "bust_smug", ED_P, mirror=True, shadow=False), sec_press, board, tape]
S1 = [
    # close on the poster and his hand; he peels away with the tape stuck to his cuff, shakes it off
    W(m("open"), "P", [(m("open"), (640, 420, 1.55)), (m("admire"), (646, 422, 1.6))], press, drift=0.0),
    # he steps back to admire it, then sells it to us
    W(m("admire"), "P", [(m("admire"), (720, 455, 1.4)), (le("L001"), (800, 452, 1.5)), (m("c_ed2"), (820, 450, 1.55))],
      press),
    BW(m("c_ed2"), "P", "eddie", "smug", ED_P, mirror=True),
    W(m("c_sec2"), "P", (990, 500, 1.55), press, blur=1.0),
    W(m("c_ed3"), "P", [(m("c_ed3"), on("P", *ED_P, "eddie", 0.66)), (m("c_secreact"), on("P", *ED_P, "eddie", 0.6))],
      press, blur=2.0),
    W(m("c_secreact"), "P", on("P", *SEC_P, "security", 0.42, dx=90), press, blur=2.5),
]

# ---------------------------------------------------------------------- 1b. the loading bay
DA_B = (560, 585)
bay_dana = P("dana", keys((0, "q34"), (ls("L006") - 0.05, "palms"), (wt("L006", "wasn't") - 0.1, "shrug"),
                          (wt("L006", "now") - 0.1, "point"), (le("L006") + 0.3, "q34")), DA_B,
             mirror=keys((0, False), (wt("L006", "now") - 0.1, True), (le("L006") + 0.3, False)))
S1b = [
    W(m("c_bay"), "B", [(m("c_bay"), (836, 470, 1.0)), (m("collar"), (760, 455, 1.12))], [bay_dana],
      caption=("LOADING BAY", "Same night · outside")),
    # the disguise idea: a shifty look; then embarrassment
    BW(m("collar"), "B", "dana", "side", DA_B),
    BW(m("collar") + 0.65, "B", "dana", "blush", DA_B),
    W(ls("L006"), "B", [(ls("L006"), on("B", *DA_B, "dana", 0.80)), (m("trolley_in"), on("B", *DA_B, "dana", 0.72))],
      [bay_dana], blur=2.0),
]

# ====================================================================== 2. laundry infiltration: the bay
Y_B = 610
TB_STOP = 980                                              # the trolley's middle when she brakes
tb0, tb1 = m("trolley_in") + 0.1, m("c_wheels") + 0.45
ATT_B, TRO_B, PATH_B = push("B", tb0, tb1, -260, TB_STOP, Y_B, step=0.48,
                            carry=[(m("c_two"), "hip")])
TH_B = TRO_B["h"]
ATT_XB = ATT_B["at"][-1][1][0]
DA_IN = (TB_STOP + 0.62 * TROLLEY_W * TH_B + 120, Y_B + 6)             # beside the bin's front end
W8 = [f"w{i}" for i in range(8)]
t_sh = m("shoes")
SHOE1, SHOE2 = (DA_IN[0] - 40, DA_IN[1]), (DA_IN[0] + 20, DA_IN[1])
RIM_B = (TB_STOP, Y_B - 0.93 * TH_B)
ATT_B["pose"] = ATT_B["pose"] + [(m("c_pivot") - 0.05, "point2"), (wt("L012", "don't") - 0.1, "stop2"),
                                 (le("L012") + 0.3, "hip"), (t_sh + 2.2, "hip")]
ATT_B["mirror"] = keys((0, False), (m("c_two"), True), (m("c_pivot") - 0.05, False))
dana_bay2 = P("dana", keys((0, "w0"), (tb1 + 0.05, "q34"), (ls("L007") - 0.05, "front"), (le("L007") + 0.2, "q34"),
                           (ls("L009") - 0.05, "palms"), (le("L009") + 0.2, "q34"), (m("c_insult"), "palms"),
                           (le("L013") + 0.2, "q34"), (t_sh, "crouch"), (t_sh + 0.45, "stop"), (t_sh + 1.05, "crouch"),
                           (t_sh + 1.5, "stop"), (m("climb_in"), "climb")),
              keys((tb0, (DA_IN[0] - 1250, DA_IN[1])), (tb1, DA_IN), (m("climb_in"), DA_IN),
                   (m("climb_in") + 0.5, (TB_STOP + 70, Y_B - 4))),
              walk=dict(frames=W8, cycle=0.95, t0=tb0, t1=tb1), mirror=keys((0, False), (tb1 + 0.05, True)),
              rot=wob(t_sh + 0.45, 0.6, 9.0, 3) + wob(t_sh + 1.5, 0.45, 6.0, 2),
              dy=keys((m("climb_in") + 0.25, 0.0), (m("climb_in") + 0.55, 0.42 * h_of("B", "dana", Y_B)),
                      (m("climb_in") + 1.0, -120.0)),
              clip=keys((0, None), (m("climb_in") + 0.45, Y_B - 0.25 * TH_B)), ease=True, z=Y_B + 3,
              show=[(0, m("climb_in") + 0.42)])
dana_in = dict(dana_bay2, z=Y_B + 0.4, show=[(m("climb_in") + 0.42, m("climb_in") + 0.68)])
SHOE_HAND = (DA_IN[0] - 150, DA_IN[1] - 150)
shoes_b = [dict(fn="shoe", at=keys((t_sh + 0.12, SHOE_HAND), (t_sh + 0.2, SHOE_HAND)) + arc(t_sh + 0.25, t_sh + 0.7,
                SHOE_HAND, (RIM_B[0] + 40, RIM_B[1] + 30), 170, 8),
                rot=keys((t_sh + 0.25, 0.0), (t_sh + 0.7, 260.0)), w=82, show=[(t_sh + 0.12, t_sh + 0.68)], z=Y_B + 4),
           dict(fn="shoe", at=keys((t_sh + 1.17, SHOE_HAND), (t_sh + 1.25, SHOE_HAND)) + arc(t_sh + 1.3, t_sh + 1.75,
                SHOE_HAND, (RIM_B[0] - 30, RIM_B[1] + 30), 190, 8),
                rot=keys((t_sh + 1.3, 0.0), (t_sh + 1.75, -250.0)), w=82, show=[(t_sh + 1.17, t_sh + 1.73)], z=Y_B + 4)]
WHEELS_B = dict(fn="wheels", trolley=TRO_B, z=Y_B + 1.2)
bay2 = [ATT_B, TRO_B, WHEELS_B, towels_on(PATH_B, TH_B, Y_B + 0.5), dana_bay2, dana_in,
        dict(fn="lid", at=(TB_STOP, Y_B - 0.93 * TH_B), w=1.08 * TH_B, z=Y_B + 1.5,
             show=[(m("climb_in") + 0.9, 1e9)], rot=keys((m("climb_in") + 0.9, 80.0), (m("climb_in") + 1.25, 0.0)))] + shoes_b
mid_b = ((ATT_XB + DA_IN[0]) / 2, Y_B)
S2 = [
    W(m("trolley_in"), "B", [(m("trolley_in"), (700, 450, 1.25)), (m("c_wheels"), (840, 455, 1.3))], bay2),
    # low: the wheels and her feet; the brake
    W(m("c_wheels"), "B", [(m("c_wheels"), (TB_STOP - 60, Y_B - 90, 3.4)), (m("c_two"), (TB_STOP - 40, Y_B - 90, 3.5))],
      bay2, blur=2.0, drift=0.0, locked=True),
    W(m("c_two"), "B", [(m("c_two"), (mid_b[0], 455, 1.65)), (m("c_offer"), (mid_b[0], 452, 1.75))], bay2, blur=1.0),
    BW(m("c_offer"), "B", "dana", "smug", DA_IN, others=bay2[:4]),
    W(m("c_pivot"), "B", [(m("c_pivot"), (mid_b[0], 455, 1.5)), (m("shoes"), (mid_b[0], 452, 1.58))], bay2, blur=1.0),
    # the shoes: one off, a hop, the other; in he goes
    W(m("shoes"), "B", [(m("shoes"), (DA_IN[0] - 140, 420, 1.3)), (m("c_inbin"), (DA_IN[0] - 160, 425, 1.36))],
      bay2, blur=1.0),
]

# ---------------------------------------------------------------------- 2a. inside the bin
DA_I = (836, 1563)
inbin_light = dict(fn="dark", alpha=keys((m("c_inbin") + 0.6, 0.0), (m("c_inbin") + 1.25, 0.6)),
                   panel=keys((m("c_inbin") + 0.6, -120.0), (m("c_inbin") + 1.25, 185.0)), z=5000)
inbin_shoes = [dict(fn="shoe", at=(540, 700), rot=-32.0, w=210, z=3000),
               dict(fn="shoe", at=(1130, 706), rot=34.0, w=210, mirror=True, z=3000)]
inbin = [B("dana", "blush", DA_I, look=("dir", 0.0, -0.6, 0.0)), inbin_light]
inbin_dark = [B("dana", "smug", DA_I), dict(fn="dark", alpha=0.5, panel=185.0, z=5000)]
S2a = [W(m("c_inbin"), "I", [(m("c_inbin"), (836, 470, 1.0)), (m("c_check"), (836, 490, 1.08))], inbin, drift=0.0)]

# ---------------------------------------------------------------------- 2b. the checkpoint: reverse corridor
Y_Q = 800
SEC_Q, TQ_STOP = (560, 770), 860
tq0, tq1 = m("c_check") - 0.1, m("c_check") + 1.2
ATT_Q, TRO_Q, PATH_Q = push("Q", tq0, tq1, 2050, TQ_STOP, Y_Q, mirror=True, step=0.5, stop="hip")
TH_Q = TRO_Q["h"]
tg = m("giveway") + 0.65
ATT_Q2, TRO_Q2, PATH_Q2 = push("Q", tg, tg + 2.0, TQ_STOP, -350, Y_Q, mirror=True, step=0.5)
# one attendant and one trolley through the scene: the stop, the lid, the stare, then on her way
ATT_Q["pose"] = ATT_Q["pose"] + [(ls("L016") - 0.1, "hip"), (m("c_lid"), "brace"), (le("L018") + 0.3, "hip")] + \
    [kv for kv in ATT_Q2["pose"] if kv[0] >= tg - 0.02]
ATT_Q["at"] = ATT_Q["at"] + [kv for kv in ATT_Q2["at"] if kv[0] > tg]
TRO_Q["at"] = TRO_Q["at"] + [kv for kv in TRO_Q2["at"] if kv[0] > tg]
PATH_Q = TRO_Q["at"]
ATT_XQ = [x for t_, (x, _) in ATT_Q["at"] if t_ <= tq1 + 1e-6][-1]
sec_q = P("security", keys((0, "front"), (ls("L015") - 0.1, "front"), (le("L015") + 0.4, "front"),
                           (m("c_stare") + 0.2, "crossed"), (tg - 0.2, "gesture"), (tg + 0.6, "crossed")),
          keys((0, SEC_Q), (tg - 0.3, SEC_Q), (tg + 0.5, (390, 760))), steps=True, ease=True,
          look=None)
checkpoint = [ATT_Q, TRO_Q, dict(fn="wheels", trolley=TRO_Q, z=Y_Q + 1.2), towels_on(PATH_Q, TH_Q, Y_Q + 0.5,
              mirror=True), dict(fn="lid", at=[(a, (x, y - 0.93 * TH_Q)) for a, (x, y) in PATH_Q], w=1.08 * TH_Q,
                                 z=Y_Q + 1.5), sec_q]
S2b = [
    W(m("c_check"), "Q", [(m("c_check"), (980, 520, 1.12)), (ls("L016"), (900, 540, 1.3))], checkpoint),
    W(m("c_bintalk"), "I", (836, 470, 1.0), inbin_dark, drift=0.0),
    W(m("c_lid"), "Q", on("Q", ATT_XQ, Y_Q, "attendant", 0.7, dx=-60), checkpoint, blur=2.0),
    W(m("c_stare"), "Q", on("Q", *SEC_Q, "security", 0.42), checkpoint, blur=2.5, drift=0.0),
    W(m("giveway"), "Q", on("Q", ATT_XQ, Y_Q, "attendant", 0.45), checkpoint, blur=2.5, drift=0.0),
    W(m("giveway") + 0.55, "Q", [(m("giveway") + 0.55, (760, 520, 1.15)), (m("c_roll"), (640, 530, 1.2))], checkpoint),
]

# ====================================================================== 3. the delivery: the corridor
# the corridor, left to right: the cable ramp on the floor, Fury beyond it. The trolley comes in from the left,
# its front wheel hits the ramp; her front foot braces; the towels lurch; the lid flips; Dana grabs for the rim,
# misses, and goes over the front in one arc to Fury's feet; his shoes skid on after him.
Y_C = 700
TR_X = 930
DA_LAND, FU_C, AJ_C = (1205, 718), (1340, 708), (1585, 690)
FU_BACK = (1405, 700)
SEC_C3 = (250, 655)
ED_IN, ED_NEG = (110, 728), (800, 732)                     # (he stops at the corner, clear of the attendant)
tr0, t_hit = m("c_roll"), m("c_ramp") + 0.12
ATT_C, TRO_C, PATH_C = push("C", tr0 - 0.2, t_hit, -300, TR_X, Y_C, step=0.45, stop="brace")
TH_C = TRO_C["h"]
RIM = Y_C - 0.928 * TH_C
t_br, t_gr, t_tu, t_la = m("brace"), m("grab"), m("tumble"), m("land")
jolt = [(t_hit, 0.0), (t_hit + 0.08, 8.0), (t_br + 0.2, 5.0), (t_tu + 0.3, 2.0), (t_la + 0.3, 0.0)]
TRO_C["rot"], TRO_C["pivot"] = jolt, 1.0
ATT_C["rot"] = [(t_hit, 0.0), (t_hit + 0.1, -5.0), (t_br + 0.3, -2.0), (t_la, 0.0)]
ATT_C["pose"] = ATT_C["pose"] + [(t_la + 0.6, "hip"), (m("c_pay"), "point"), (m("pays") + 1.3, "hip")]   # until the money is in her hand
# paid, she steps back out of the promoters' way (two steps, facing where she goes), then turns to watch
# after the crash she lets go of the handle and steps back out of the promoters' way
ATT_C["at"] = ATT_C["at"] + [(t_la + 0.6, ATT_C["at"][-1][1]), (t_la + 1.2, (400, 700))]
_tb = m("pays") + 1.4
_xa = ATT_C["at"][-1][1]
ATT_C["at"] = ATT_C["at"] + [(_tb, _xa), (_tb + 1.6, (-260, 690))]
ATT_C["pose"] = ATT_C["pose"] + [(_tb + 0.4 * i, ("step_a", "step_b", "step_c", "step_b")[i % 4]) for i in range(5)]
ATT_C["mirror"] = keys((0, False), (_tb, True))
ATT_C["show"] = [(0, _tb + 1.6)]
peek = P("dana", "peek", (TR_X + 62, RIM + 16), z=Y_C + 0.7, shadow=False, floor=Y_C, show=[(t_br, t_tu)],
         dy=[(t_br, -150.0), (t_br + 0.25, -150.0), (t_gr, -40.0), (t_gr + 0.2, 6.0), (t_gr + 0.4, -10.0), (t_tu, 0.0)])
fly = P("dana", keys((t_tu, "tumble1"), (t_tu + 0.28, "tumble2"), (t_tu + 0.56, "tumble3")),
        arc(t_tu, t_la, (TR_X + 70, RIM + 40), DA_LAND, 90), rot=[(t_tu, 0.0), (t_tu + 0.3, -24.0),
                                                                   (t_tu + 0.6, 16.0), (t_la, 0.0)],
        mirror=True, z=Y_C + 40, shadow=False, floor=DA_LAND[1], show=[(t_tu, t_la)])
towel_fly = dict(prop="towel", at=arc(t_tu + 0.15, t_la + 0.35, (TR_X + 40, RIM - 20),
                                      (DA_LAND[0] + 35, DA_LAND[1] - 108), 330),
                 h=95, z=Y_C + 41, rot=[(t_tu, 0.0), (t_la + 0.35, 380.0)], show=[(t_tu + 0.15, t_la + 0.9)])
SHOE_C1, SHOE_C2 = (1320, 724), (262, 738)                  # the second bounces back up the corridor
shoes_c = [dict(fn="shoe", at=arc(t_tu + 0.1, t_la + 0.05, (TR_X + 60, RIM + 20), (1230, 724), 120, 6) +
                slide(t_la + 0.05, t_la + 0.6, (1230, 724), SHOE_C1)[1:],
                rot=keys((t_tu + 0.1, 0.0), (t_la + 0.05, 200.0), (t_la + 0.6, 180.0)), w=44, z=Y_C + 42),
           dict(fn="shoe", at=arc(t_tu + 0.15, t_la + 0.1, (TR_X + 50, RIM + 20), (1090, 730), 150, 6) +
                slide(t_la + 0.1, t_la + 0.95, (1090, 730), SHOE_C2)[1:],
                rot=keys((t_tu + 0.15, 0.0), (t_la + 0.1, -160.0), (t_la + 0.95, -180.0)), w=44, mirror=True,
                z=Y_C + 42)]
lid_c = dict(fn="lid", at=[(a, (x, y - 0.93 * TH_C)) for a, (x, y) in PATH_C], w=1.08 * TH_C, z=Y_C + 1.5,
             rot=[(t_hit, 0.0), (t_br, 6.0), (t_br + 0.2, 92.0), (t_gr, 112.0), (t_tu + 0.3, 118.0)])
fury_c = P("tyson", keys((0, "front"), (t_la - 0.05, "walk"), (t_la + 0.3, "front"), (ls("L019") - 0.1, "point_down"),
                         (le("L019") + 0.3, "front"), (ls("L023") - 0.1, "point_down"), (le("L023") + 0.3, "crossed")),
           keys((0, FU_C), (t_la - 0.05, FU_C), (t_la + 0.3, FU_BACK)), rot=wob(t_la - 0.05, 0.5, -5.0, 2),
           look="dana", ease=True)
aj_t0 = m("c_aj") - 0.6
joshua_c = P("joshua", keys((0, "walk"), (aj_t0 + 0.8, "front"), (le("L023") + 0.4, "crossed")),
             keys((aj_t0, (1850, AJ_C[1])), (aj_t0 + 0.8, AJ_C), (m("c_eddie") - 0.01, AJ_C),
                  (m("c_eddie"), (1590, 650))), steps=True, ease=True,
             mirror=keys((0, True), (aj_t0 + 0.85, False)), show=[(aj_t0, 1e9)], look="dana")


def dana_floor():
    return P("dana", keys((0, "prone"), (ls("L020") - 0.1, "towel_head"), (m("c_up") + 0.05, "front"),
                          (wt("L025", "security's") - 0.1, "point"), (le("L025") + 0.2, "front"),
                          (ls("L027") - 0.05, "crossed"), (m("c_pay") + 0.4, "palms"), (m("pays") + 1.2, "crossed")),
             keys((0, DA_LAND), (m("c_up"), DA_LAND), (m("c_up") + 0.05, (DA_LAND[0], DA_LAND[1] - 2))),
             look=None, mirror=keys((0, True), (ls("L020") - 0.1, False), (wt("L025", "security's") - 0.1, True),
                                    (le("L025") + 0.2, False)), show=[(t_la, 1e9)],
             rot=keys((m("c_up"), 0.0), (m("c_up") + 0.1, -12.0), (m("c_up") + 0.3, 8.0), (m("c_up") + 0.5, -5.0),
                      (m("c_up") + 0.7, 2.0), (m("c_up") + 0.9, 0.0)),
             dy=keys((m("c_up"), 0.0), (m("c_up") + 0.12, 40.0), (m("c_up") + 0.3, 0.0)))


def eddie_c():
    w0, w1 = m("c_eddie") + 0.05, m("c_eddie") + 1.25
    v0, v1 = ls("L025") + 0.1, ls("L026") - 0.15
    return P("eddie", keys((0, "q34"), (m("recog") + 0.5, "front"), (ls("L026") - 0.1, "point"),
                           (le("L026") + 0.3, "q34"), (m("c_pay") - 0.3, "crossed"), (ls("L031") - 0.05, "point"),
                           (le("L031") + 0.3, "front"), (m("c_fine"), "palms"), (le("L033") + 0.25, "front")),
             [(w0, (-140, ED_IN[1])), (w1, ED_IN), (v0, ED_IN), (v1, ED_NEG)],
             walk=[dict(frames=W8, cycle=1.0, t0=w0, t1=w1), dict(frames=W8, cycle=0.9, t0=v0, t1=v1)],
             mirror=keys((0, False), (ls("L026") - 0.1, True), (le("L026") + 0.3, False), (ls("L028") - 0.2, True),
                         (le("L029") + 0.3, False)),
             show=[(m("c_eddie"), 1e9)], look=keys((0, None), (m("c_eddie") + 1.0, ("dir", 0.3, 0.8, 0.0)),
                                                    (m("recog"), None)))


# the notes: out of Dana's hand, held a moment, then tossed over Eddie's head (behind it) into her outstretched hand
_n0 = hand_at("C", "dana", "palms", DA_LAND, -1)
_n1 = hand_at("C", "attendant", "point", (400, 700), 1)
notes_c = dict(fn="notes", at=keys((m("pays") + 0.15, _n0), (m("pays") + 0.4, _n0)) +
               arc(m("pays") + 0.4, m("pays") + 0.85, _n0, _n1, 340)[1:],
               w=46, show=[(m("pays") + 0.15, m("pays") + 1.3)], z=DA_LAND[1] + 1)   # behind Eddie (over his head), in front of the others


def corridor_c():
    return [dict(prop="cable-ramp", at=(1000, Y_C + 6), h=55, z=Y_C - 5), ATT_C, TRO_C,
            dict(fn="wheels", trolley=TRO_C, z=Y_C + 1.2),
            towels_on(PATH_C, TH_C, Y_C + 0.5, rot=jolt, pivot=1.0,
                      dy=[(t_br, 0.0), (t_br + 0.15, 28.0), (t_br + 0.4, 8.0), (t_la, 0.0)]),
            lid_c, peek, fly, towel_fly, fury_c, joshua_c, dana_floor(), eddie_c(), notes_c,
            P("security", keys((0, "front"), (ls("L028") - 0.1, "gesture"), (le("L028") + 0.4, "crossed")),
              keys((m("c_dana4"), (-160, SEC_C3[1])), (m("c_sec4") - 0.1, SEC_C3)), look=None, steps=True,
              show=[(m("c_dana4"), 1e9)])] + shoes_c


CC = corridor_c()
two = ((ED_NEG[0] + DA_LAND[0]) / 2, Y_C)
S3 = [
    # low, tracking with the trolley; the ramp; the chain: brace, the lid, the grab, the fall, the landing
    W(m("c_roll"), "C", [(t_, (max(250.0, x_ - 240), 560, 1.9)) for t_, (x_, _) in PATH_C if m("c_roll") <= t_ <= m("c_ramp")] +
      [(m("c_ramp"), (TR_X - 240, 560, 1.9))], CC, linear=True, blur=1.0),
    W(m("c_ramp"), "C", [(m("c_ramp"), (960, 640, 4.2)), (m("brace"), (960, 640, 4.4))], CC, blur=2.0, drift=0.0),
    W(m("brace"), "C", [(m("brace"), (1000, 470, 1.25)), (m("land") + 0.5, (1060, 475, 1.25))], CC, drift=0.0),
    # from the floor: Fury very tall
    W(m("c_pov"), "C", on("C", *FU_BACK, "tyson", 1.02, up=-0.02, dx=-60), CC, blur=1.5),
    W(m("c_dana1"), "C", on("C", *DA_LAND, "dana", 0.9, dx=40), CC, blur=2.0),
    BW(m("c_fury2"), "C", "tyson", "side", FU_BACK, mirror=True),
    W(m("c_aj"), "C", [(m("c_aj"), (1500, 480, 1.4)), (m("c_fury3"), (1500, 478, 1.45))], CC, blur=1.0),
    BW(m("c_fury3"), "C", "tyson", "lean", FU_BACK, mirror=True),
    # Eddie comes round the corner, stops at the shoe, finds the towel, the bin, Dana
    W(m("c_eddie"), "C", [(m("c_eddie"), (836, 470, 1.0)), (m("recog"), (836, 470, 1.02))], CC),   # the whole tableau
    BW(m("recog"), "C", "eddie", "glare", ED_IN),
    W(m("c_up"), "C", [(m("c_up"), (DA_LAND[0] - 120, 470, 1.6)), (m("c_ed4"), (DA_LAND[0] - 160, 470, 1.65))], CC,
      blur=1.0),
    W(m("c_ed4"), "C", on("C", *ED_NEG, "eddie", 0.62, dx=40), CC, blur=2.0),
    BW(m("c_dana4"), "C", "dana", "smug", DA_LAND),
    W(m("c_sec4"), "C", on("C", *SEC_C3, "security", 0.55, dx=-70), CC, blur=2.0),
    BW(m("c_ed5"), "C", "eddie", "profile", ED_NEG, mirror=True),
    # her hand out, Dana paying, Eddie between them watching the money go past
    W(m("c_pay"), "C", [(m("c_pay"), (905, 455, 1.4)), (m("pays") + 1.0, (905, 457, 1.45))], CC, blur=1.0),
    BW(m("pays") + 1.0, "C", "eddie", "up", ED_NEG),
]

# ====================================================================== 4. the challenge
S4 = [
    W(m("c_out"), "C", on("C", *ED_NEG, "eddie", 0.62, dx=-30), CC, blur=2.0),
    W(m("c_close"), "C", [(m("c_close"), (two[0] + 20, 440, 1.9)), (m("silence") + 0.6, (two[0] + 20, 430, 2.05))], CC,
      blur=1.5),
    BW(m("c_reg_e"), "C", "eddie", "sweat", ED_NEG),
    BW(m("c_reg_d"), "C", "dana", "panic", (1215, 726)),
]
# Dana steps right up to him for "Put me in the ring"
for it in CC:
    if it.get("who") == "dana" and isinstance(it["pose"], list) and any(v == "prone" for _, v in it["pose"]):
        it["at"] = it["at"] + [(ls("L032") - 0.2, (DA_LAND[0], DA_LAND[1] - 2)), (ls("L032") + 0.2, (1215, 726))]
        it["pose"] = it["pose"] + [(ls("L032") - 0.05, "point"), (le("L032") + 0.2, "front"), (m("c_fine"), "crossed"),
                                   (le("L033") + 0.3, "front")]
        it["mirror"] = keys((0, True), (ls("L020") - 0.1, False))

# ---------------------------------------------------------------------- 4b. preparation: the corridor, in kit
ED_Q, DA_Q = (520, 840), (1180, 840)
FU_Q, AJ_Q = (860, 600), (1010, 596)
tj, ts_, tph = m("c_jacket"), m("c_strap"), m("c_phone")
ed_kit = P("eddie", keys((0, "front"), (tj + 0.3, "guard"), (ls("L034") - 0.05, "guard2"),
                         (wt("L034", "elbows") - 0.1, "guard"), (wt("L034", "wrestling") - 0.1, "guard2"),
                         (tph - 0.02, "guard"), (le("L036") + 0.2, "guard"), (m("c_kit"), "guard"),
                         (ls("L038") - 0.05, "guard2"), (le("L038") + 0.2, "guard"), (ls("L040") - 0.05, "guard2"),
                         (le("L040") + 0.3, "guard")), ED_Q,
           look=keys((0, None), (tph, ("dir", 0.3, 0.7, 0.0)), (le("L036") - 0.4, None)))
da_kit = P("dana", keys((0, "guard"), (ts_ - 0.02, "cover"), (ls("L035") - 0.03, "guard"), (m("c_kit"), "guard"),
                        (ls("L037") - 0.05, "guard_high"), (le("L037") + 0.2, "guard"), (ls("L039") - 0.05, "jab"),
                        (le("L039") + 0.2, "guard")), DA_Q,
           rot=keys((ts_ + 0.1, 0.0), (ts_ + 0.16, -7.0), (ts_ + 0.32, 3.0), (ts_ + 0.5, 0.0)))
puff = dict(fn="puff", t0=tj + 0.1, dur=0.42, at=(ED_Q[0], ED_Q[1] - 0.52 * h_of("Q", "eddie", ED_Q[1])),
            size=0.80 * h_of("Q", "eddie", ED_Q[1]), z=2000)
PH = (ED_Q[0] + 70, ED_Q[1] - 0.6 * h_of("Q", "eddie", ED_Q[1]))
phone_q = dict(fn="phone", at=keys((tph, PH), (wt("L036", "both") - 0.05, PH))
               + arc(wt("L036", "both"), wt("L036", "both") + 0.45, PH, (ED_Q[0] + 210, ED_Q[1] + 4), 60, 5),
               rot=keys((tph, -15.0), (wt("L036", "both"), -10.0), (wt("L036", "both") + 0.45, 95.0)), w=70,
               show=[(tph, 1e9)], z=3000)
watchers = [P("tyson", "crossed", FU_Q, look="dana"), P("joshua", "crossed", AJ_Q, look="eddie")]
kit = [ed_kit, da_kit, puff, phone_q] + watchers
fj_busts = [B("tyson", "side", FU_Q, mirror=True), B("joshua", "left", AJ_Q)]
S4b = [
    W(tj, "Q", on("Q", *ED_Q, "eddie", 0.8, dx=40), kit, blur=1.5, caption=("THE CORRIDOR", "Ten minutes later")),
    W(ts_, "Q", on("Q", *DA_Q, "dana", 0.7, dx=-40), kit, blur=2.0),
    W(tph, "Q", on("Q", *ED_Q, "eddie", 0.62, dx=60), kit, blur=2.0),
    W(m("c_kit"), "Q", [(m("c_kit"), (850, 520, 1.12)), (m("c_fj"), (850, 512, 1.2))], kit, blur=0.5),
    BW(m("c_fj"), "Q", "joshua", "left", AJ_Q, blur=3.5),
    BW(ls("L042") - 0.1, "Q", "tyson", "side", FU_Q, mirror=True, blur=3.5),
]

# ====================================================================== 5. the additional contest: the arena
ED_A, DA_A, AN_A = (440, 655), (1240, 655), (836, 650)
tr_ = m("ropes")
ED_ROPE, DA_ROPE = (250, 668), (1420, 668)
arena_e = P("eddie", keys((0, "crouch_guard"), (tr_ + 0.75, "guard"), (m("c_ed_conf") + 0.15, "arms_up"),
                          (m("c_ann3"), "guard")),
            keys((0, ED_ROPE), (tr_ + 0.1, ED_ROPE), (tr_ + 0.8, ED_A)), ease=True, steps=True,
            face=[(m("c_ed_conf"), m("c_ann3"), 0.95, 0.6)])
arena_d = P("dana", keys((0, "crouch_guard"), (tr_ + 0.85, "guard"), (m("c_da_in") + 0.1, "arms_up"),
                         (m("towel") + 0.6, "guard_high"), (m("towel") + 0.85, "guard"), (m("towel") + 1.05, "guard_high"),
                         (m("towel") + 1.3, "guard")),
            keys((0, DA_ROPE), (tr_ + 0.2, DA_ROPE), (tr_ + 0.9, DA_A)), ease=True, steps=True)
ann = P("announcer", keys((0, "mic"), (wt("L044", "red") - 0.1, "mic_gesture"), (le("L044"), "mic"),
                          (wt("L045", "blue") - 0.1, "mic_gesture"), (le("L045"), "mic")), AN_A,
        mirror=keys((0, False), (wt("L044", "red") - 0.1, True), (le("L044"), False)), show=[(0, m("c_ref"))])
towel_sh = dict(fn="drape", on="dana", prop="towel", at=(0.55, 0.75), h=1.5, side=1, rot=-20.0, z=10000,
                show=[(0, m("towel") + 0.4)])
_hd = hand_at("A", "attendant", "towel2", (0.0, 662), 1)            # her reach in towel2 (facing right)
_sh = (DA_A[0] + 0.12 * h_of("A", "dana", DA_A[1]), DA_A[1] - 0.72 * h_of("A", "dana", DA_A[1]))   # his shoulder
ATT_TW = (_sh[0] + _hd[0], 662)                                     # mirrored: the hand reaches left onto it
att_a = P("attendant", keys((0, "hip"), (m("towel") + 0.05, "towel2"), (m("towel") + 0.45, "towel")),
          keys((m("towel") - 0.4, (1690, 662)), (m("towel"), ATT_TW), (m("towel") + 1.3, ATT_TW),
               (m("towel") + 1.9, (1720, 662))), show=[(m("towel") - 0.4, m("c_ref"))], z=650, steps=True,
          mirror=keys((0, True), (m("towel") + 1.3, False)))
arena = [arena_e, arena_d, ann, towel_sh, att_a]
S5 = [
    W(m("c_arena"), "A", [(m("c_arena"), (836, 470, 1.0)), (m("c_ann1"), (836, 480, 1.06))], arena,
      caption=("THE ARENA", "One additional contest")),
    W(m("c_ann1"), "A", [(m("c_ann1"), on("A", *AN_A, "announcer", 0.7)), (m("c_ann2"), on("A", *AN_A, "announcer", 0.62))],
      arena, blur=1.5),
    W(m("c_ann2"), "A", [(m("c_ann2"), (680, 520, 1.6)), (m("c_ed_conf"), (640, 520, 1.7))], arena, blur=1.0),
    W(m("c_ed_conf"), "A", on("A", *ED_A, "eddie", 0.55), arena, blur=2.0),
    W(m("c_ann3"), "A", [(m("c_ann3"), (1000, 520, 1.6)), (m("c_da_in"), (1040, 520, 1.7))], arena, blur=1.0),
    W(m("c_da_in"), "A", [(m("c_da_in"), on("A", *DA_A, "dana", 0.95, dx=60)),
                          (m("c_ref"), on("A", *DA_A, "dana", 0.9, dx=80))], arena, blur=1.5),
]

# ---------------------------------------------------------------------- 5b. the referee's instructions (in the ring)
from film.fight import Fighter                                              # noqa: E402

RF_T, ED_T, DA_T = (836, 640), (480, 830), (1190, 830)
ref_talk = [P("referee", keys((0, "stop"), (wt("L046", "wrestling") - 0.1, "break"), (le("L046") + 0.2, "stop")), RF_T,
              look=keys((0, "cam"), (ls("L047"), "eddie"))),
            P("eddie", keys((0, "guard"), (ls("L047") - 0.05, "guard2")), ED_T, bounce=dict(amp=0.01, hz=2.0, poses={"guard"})),
            P("dana", "guard", DA_T, bounce=dict(amp=0.01, hz=2.2, poses={"guard"}))]
S5b = [
    W(m("c_ref"), "R", [(m("c_ref"), (836, 500, 1.25)), (m("c_ed_q"), (836, 492, 1.32))], ref_talk, blur=0.5),
    W(m("c_ed_q"), "R", on("R", *ED_T, "eddie", 0.5, dx=-50), ref_talk, blur=2.0),
]

# ====================================================================== 6. one disastrous round
ED_R, DA_R, RF_R = (560, 785), (1110, 785), (1760, 640)      # the referee waits out of shot
H_ED, H_DA = h_of("R", "eddie", 785), h_of("R", "dana", 785)
E = Fighter("eddie", ED_R[0], +1, ED_R[1], H_ED)
Dn = Fighter("dana", DA_R[0], -1, DA_R[1], H_DA)
PK = 0.92 * H_ED / 357                                    # plate px per pair px in the ring
PAIR_X = 836
tb, tbo, tsl, tsi = m("bell"), m("bounce"), m("slow"), m("silence2")


def bounces(F, t0, t1, t_stop, amp, hz=2.0):
    """confident bouncing on the toes from t0, dying away from t_stop to nothing by t1"""
    t = t0
    while t < t1:
        a = amp * (1.0 if t < t_stop else max(0.0, 1 - (t - t_stop) / max(1e-3, t1 - t_stop)))
        F.lift(t, 0.0).lift(t + 0.25 / hz, a)
        t += 1.0 / hz
    F.lift(t1, 0.0)


# the bell; both bounce, full of it; Dana slows first; Eddie notices and stops too; nothing happens
E.hold(tb).pose(tb, "guard")
Dn.hold(tb).pose(tb, "guard")
bounces(E, tbo, tsl + 0.9, tsl + 0.45, 0.035 * H_ED, 2.1)
bounces(Dn, tbo, tsl + 0.5, tsl, 0.035 * H_DA, 2.0)
E.to(tbo + 0.8, 600).to(tbo + 1.5, 590)
Dn.to(tbo + 0.8, 1075).to(tbo + 1.5, 1090)
# 1. the probe: a long, slow, tentative jab; Dana overreacts: a deep duck, and peers up from under his gloves
tp = m("probe")
E.punch(tp + 0.35, "jab_long", 70, wind="guard2", wind_t=0.4, hold=0.35, back=0.5, lean=5)
Dn.duck(tp + 0.42, dur=1.1, dx=10).lift(tp + 1.0, 0.0)
Dn.pose(m("c_da2") - 0.05, "crouch_guard").pose(ls("L049") - 0.02, "guard_high").pose(le("L049") + 0.15, "guard")
E.pose(ls("L050") - 0.05, "guard2").pose(le("L050") + 0.2, "guard")


def glove(F, pose):
    """where a fighter's lead glove is in a drawing: (x ahead of the feet along his facing, y above them), ring px"""
    from film.actors import PEOPLE, feet_mid, sheet_fac
    from film.things import hand_tip
    key = f"{PEOPLE[F.who][0]}:{pose}"
    fx, fy = feet_mid(key)
    tx, ty = hand_tip(key, F.facing)
    k = F.h / PEOPLE[F.who][2] * sheet_fac(key)
    return abs(tx - fx) * k, (fy - ty) * k


def land(A, a_pose, V, v_pose, into=8.0):
    """the lunge that puts A's glove in `a_pose` onto V's lead glove in `v_pose` (`into` px into it)"""
    ga, gv = glove(A, a_pose)[0], glove(V, v_pose)[0]
    return abs(V.x - A.x) - ga - gv + into


# 2. the touch: Eddie's second jab taps Dana's guard (the glove really meets the glove); Dana counters into the red
# gloves. Contact is shown with each fighter's own drawings, the jab reaching exactly to the guard: no swapping to
# another drawing mid-shot
tt = m("tap")
CONTACT = []                                               # (t0, t1, pair) the pair drawing replaces both fighters
E.pose(tt, "guard2")
E.punch(tt + 0.22, "jab", land(E, "jab", Dn, "guard"), wind="guard2", wind_t=0.14, hold=0.18, back=0.3, lean=3,
        lines=False)
Dn.hit(tt + 0.29, pose="guard", knock=12, lean=4, settle=0.35, sweat=False)
Dn.punch(tt + 0.82, "jab", land(Dn, "jab", E, "block"), wind="guard_high", wind_t=0.14, hold=0.18, back=0.32, lean=3,
         lines=False)
E.hit(tt + 0.89, pose="block", knock=18, lean=6, settle=0.45, sweat=False)
E.pose(tt + 1.4, "guard")
# the exchange: chin talk
E.pose(ls("L052") - 0.05, "guard2").pose(le("L052") + 0.1, "guard")
Dn.pose(ls("L053") - 0.05, "guard_high").pose(le("L053") + 0.1, "guard")
# Dana talks with his face clear of the gloves (in guard a glove covers his chin)
for _l in ("L051", "L056"):
    Dn.pose(ls(_l) - 0.05, "guard_high").pose(le(_l) + 0.15, "guard")
E.pose(ls("L054") - 0.05, "guard").pose(le("L054") + 0.2, "guard")
# 3. indignation: Dana's counter lands on Eddie's raised gloves; any contact is an insult
tc = m("counter")
Dn.punch(tc + 0.24, "jab2", land(Dn, "jab2", E, "block"), wind="guard_high", wind_t=0.18, hold=0.2, back=0.35, lean=4,
         lines=False)
E.pose(tc + 0.2, "block")
E.hit(tc + 0.31, pose="block", knock=30, lean=8, settle=0.6, sweat=False)
E.pose(tc + 0.95, "guard")
E.pose(ls("L055") - 0.05, "guard2").pose(le("L055") + 0.1, "guard")
E.pose(ls("L057") - 0.05, "arms_up").pose(le("L057") + 0.25, "guard")      # strikes a pose for the photos
# 4. (the red corner, K) Dana comes forward; Eddie backpedals onto the ropes; they throw him back: the clinch
tad, tro, trc, tcl = m("advance"), m("ropes2"), m("recoil"), m("clinch")
EK0, DK0 = (800, 600), (1100, 600)
EK_ROPE, CL_K = (430, 592), (640, 600)
K_FAC = (h_of("K", "eddie", 650) / H_ED)                  # the red corner's scale against the ring's
EK = Fighter("eddie", EK0[0], +1, EK0[1], h_of("K", "eddie", EK0[1]))
DK = Fighter("dana", DK0[0], -1, DK0[1], h_of("K", "dana", DK0[1]))
EK.pose(tad, "guard").hold(tad)
DK.pose(tad, "guard").hold(tad)
for i in range(3):                                         # three short steps, two of them with a punch
    a = tad + 0.1 + i * 0.55
    DK.to(a + 0.3, DK0[0] - 110 * (i + 1)).lift(a, 0.0).lift(a + 0.15, 14.0).lift(a + 0.3, 0.0)
    EK.to(a + 0.35, EK0[0] - 115 * (i + 1)).lean(a + 0.2, -6.0)
    if i < 2:
        DK.punch(a + 0.3, "jab" if i == 0 else "jab2", 40, wind="guard", wind_t=0.12, hold=0.1, back=0.18, lean=4,
                 sound="whoosh")
        EK.pose(a + 0.38, "cover")
EK.to(tro, EK_ROPE[0]).lean(tro, -14.0).lean(tro + 0.25, -20.0).lean(tro + 0.55, 6.0)     # the ropes take him...
EK.pose(trc, "cross").to(trc + 0.35, CL_K[0] - 60).lean(trc + 0.3, 14.0)                    # ...and throw him back
DK.duck(trc + 0.15, dur=0.4, dx=8)
CONTACT_K = []                                             # (the clinch starts on the cut to the ring)
ROPE_HIT = tro
# 5. the clinch (dialogue), the break, the big finish, the glove clash, the sit-down, the help up
tlf, tsep, twu, tcs, twb, tsit, tlk, tbl2, thu = (m(k) for k in ("lift", "sep", "windup", "clash", "wobble", "sit", "look",
                                                                 "bell2", "helpup"))
# the clinch in the ring (side on): from the cut into the ring to the cut out of it, held whole (a cut in and a cut
# out: never a swap between drawings in the middle of a shot)
CONTACT.append((tcl, tsep, "clinch"))
# the referee prises them apart; each staggers back
E.pose(tsep, "tired").hold(tsep).to(tsep + 0.01, 700).to(tsep + 0.5, 560).lean(tsep + 0.15, -6.0).lean(tsep + 0.5, 0.0)
Dn.pose(tsep, "tired").hold(tsep).to(tsep + 0.01, 980).to(tsep + 0.5, 1110).lean(tsep + 0.15, 6.0).lean(tsep + 0.5, 0.0)
# both load up an enormous finish, backing off and trembling with effort; then both throw: glove meets glove in the
# middle of the ring
E.pose(twu + 0.3, "wind").hold(twu + 0.3).to(twu + 0.6, 440).lean(twu + 0.5, -8.0).tremble(twu + 0.55, tcs - 0.12, -8.0)
Dn.pose(twu + 0.3, "guard_high").hold(twu + 0.3).to(twu + 0.6, 1230).lean(twu + 0.5, 8.0).tremble(twu + 0.55, tcs - 0.12, 8.0)
GE, GD = glove(E, "jab_long"), glove(Dn, "jab4")
MEET = PAIR_X
E.pose(tcs - 0.06, "jab_long").hold(tcs - 0.06).to(tcs, MEET - GE[0] + 6).lean(tcs, 3.0)
Dn.pose(tcs - 0.06, "jab4").hold(tcs - 0.06).to(tcs, MEET + GD[0] - 6).lean(tcs, -3.0)
E.hold(tcs + 0.12).to(tcs + 0.3, MEET - GE[0] - 60).lean(tcs + 0.3, -7.0)          # the jolt back up the arms
Dn.hold(tcs + 0.12).to(tcs + 0.3, MEET + GD[0] + 60).lean(tcs + 0.3, 7.0)
CLASH_AT = (MEET, ED_R[1] - 0.5 * (GE[1] + GD[1]))
# they wobble, the knees go, and both sit down on the same beat
for F_, x, s in ((E, 520, -1), (Dn, 1150, 1)):
    F_.pose(twb, "tired").hold(twb).to(twb + 0.05, x).lean(twb, 0.0)
    for i, d in enumerate((0.1, 0.3, 0.5, 0.68)):
        F_.lean(twb + d, s * (9.0 - 2 * i) * (-1) ** i)
    F_.lean(tsit, 0.0).lift(tsit, 0.0).lift(tsit + 0.22, -0.43 * F_.h).lift(tsit + 0.3, -0.40 * F_.h)
    F_.lift(thu + 0.35, -0.40 * F_.h).lift(thu + 0.95, 0.0).lean(thu + 0.95, 0.0)
    F_.pose(thu + 0.9, "guard" if F_ is E else "tired")
FIGHT_FX = [dict(fn="impact", t0=tcs, at=CLASH_AT, size=150, z=6010)]
SHAKES = [(tcs, 14.0, 0.45)]
KICKS = [(tt + 0.29, 1.04, 0.4), (tt + 0.89, 1.04, 0.4), (tc + 0.31, 1.06, 0.5), (tcs, 1.08, 0.6)]
FLASHES = [(tcs, 0.07)]                              # a 2-frame white emphasis on the one impact


def pair_items(spans, x, y, scale_of):
    """the two layers of each pair drawing, shown over `spans` [(t0, t1, pair)] at (x, y)"""
    out = []
    spans = sorted(spans)
    for who in ("eddie", "dana"):
        out.append(P(who, [(0, "pair_tap_e")] + [(a, f"pair_{k}") for a, b, k in spans], (x, y), still=True,
                     show=[(a, b) for a, b, k in spans], z=y + 0.3, shadow=(who == "eddie")))
    return out


def gaps(spans):
    """the times a fighter is drawn on his own: everything outside the pair drawings"""
    sp = sorted((a, b) for a, b, _ in spans if b > a)
    out, t = [], -1e9
    for a, b in sp:
        if a > t:
            out.append((t, a))
        t = max(t, b)
    out.append((t, 1e9))
    return out


SPANS = [c for c in CONTACT if c[1] > c[0] and c[0] > 0]
for F_, x in ((E, 600), (Dn, 1070)):
    F_.pose(m("c_ann4"), "tired").hold(m("c_ann4")).to(m("c_ann4") + 0.01, x)
E.pose(ls("L070") - 0.05, "guard2").pose(le("L070") + 0.3, "tired")
Dn.pose(ls("L071") - 0.05, "guard_high").pose(le("L071") + 0.2, "tired")
eddie_fight = E.item(P, show=gaps(SPANS))
dana_fight = Dn.item(P, show=gaps(SPANS))
PAIR_R = pair_items(SPANS, PAIR_X, ED_R[1], None)
ref_fight = P("referee", keys((0, "stop"), (ls("L065") - 0.15, "break"), (tsep + 0.9, "stop"), (thu, "break"),
                              (thu + 1.0, "stop")),
              keys((0, RF_R), (m("c_ref2") - 0.5, RF_R), (m("c_ref2") - 0.05, (1195, 700)), (tsep + 0.1, (1195, 700)),
                   (tsep + 0.6, (1820, 650)), (tbl2 - 0.4, (1820, 650)), (thu + 0.1, (836, 690))), look=None, ease=True,
              steps=True,
              mirror=keys((0, False), (m("c_ref2") - 0.3, True), (tsep + 0.2, False)))
NEAR = dict(fn="near_ropes", ys=[850, 975], z=5000, w=20, blur=3.5)
RING_FLASH = [((40, 20, 1630, 300), 5.0, 3)]


def ring(extra=()):
    return [eddie_fight, dana_fight, ref_fight, NEAR] + PAIR_R + FIGHT_FX + list(extra)


def RW(t, cams, cast=None, **kw):
    """a shot inside the ring: the fight's shakes and snap zooms, the press flashes in the crowd"""
    return W(t, "R", cams, cast if cast is not None else ring(), shakes=SHAKES, kicks=KICKS, flashes=RING_FLASH,
             white=FLASHES, **kw)


eddie_k = EK.item(P, show=[(0, tcl)])
dana_k = DK.item(P, show=[(0, tcl)])
PAIR_K = []
corner = [eddie_k, dana_k] + PAIR_K
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


# the clinch close-ups: each face in the pair drawing (pair px of the clinch -> ring px)
CL_EF = (PAIR_X + (185 - 208) * PK, ED_R[1] - (496 - 128) * PK)
CL_DF = (PAIR_X + (214 - 208) * PK, ED_R[1] - (496 - 178) * PK)
ROPE = dict(fn="rope_wobble", t0=ROPE_HIT, x=(80, 1200), ys=[(250, 410), (335, 455), (440, 535)],
            cols=[(0.80, 0.12, 0.12), (0.93, 0.93, 0.95), (0.16, 0.32, 0.80)], hit_x=EK_ROPE[0], amp=10.0, w=18,
            z=1)
S6 = [
    W(tb, "A", [(tb, (836, 300, 2.4)), (tbo, (836, 320, 2.6))], [dict(prop="boxing-bell", at=(836, 420), h=230)],
      blur=10.0, shakes=[(tb + 0.05, 10.0, 0.5), (tb + 0.33, 8.0, 0.4)]),
    # held wide: the bounce, the slowing, the nothing
    RW(tbo, [(tbo, (836, 510, 1.12)), (m("c_ty1"), (836, 505, 1.16))]),
    W(m("c_ty1"), "S", (650, 700, 1.9), ringside(face=[(m("c_ty1"), m("c_probe"), -0.6, -0.3)])),
    RW(m("c_probe"), [(m("c_probe"), (850, 500, 1.3)), (m("c_da2"), (860, 500, 1.36))]),
    RW(m("c_da2"), on("R", *DA_R, "dana", 0.6, dx=-40), blur=2.0),
    RW(m("c_ed2b"), on("R", *ED_R, "eddie", 0.55, dx=40), blur=2.0),
    RW(tt, [(tt, (836, 480, 1.4)), (m("c_da3"), (836, 476, 1.45))]),
    RW(m("c_da3"), [(m("c_da3"), (836, 470, 1.5)), (m("counter"), (836, 462, 1.6))], blur=1.0),
    RW(m("counter"), [(m("counter"), (836, 480, 1.4)), (m("c_ed_ind"), (836, 476, 1.45))]),
    RW(m("c_ed_ind"), on("R", *ED_R, "eddie", 0.55, dx=40), blur=2.0),
    RW(m("c_da4"), [(m("c_da4"), (836, 480, 1.4)), (m("advance"), (836, 470, 1.48))], blur=1.0),
    # the red corner: the advance, the ropes, the recoil into the clinch
    W(tad, "K", [(tad, (800, 420, 1.12)), (tro, (720, 410, 1.18))], corner, shakes=[(tro + 0.05, 9.0, 0.35)]),
    W(tro, "K", [(tro, (480, 340, 1.8)), (trc, (480, 340, 1.9))], corner, blur=1.0, shakes=[(tro + 0.05, 9.0, 0.35)]),
    W(trc, "K", [(trc, (660, 410, 1.2)), (tcl, (650, 400, 1.26))], corner),
    # the clinch: side on, tight; each face; the referee
    RW(tcl, [(tcl, (836, 360, 2.0)), (ls("L060"), (836, 350, 2.15))], blur=1.0),
    RW(ls("L060"), [(ls("L060"), ((CL_DF[0] + CL_EF[0]) / 2, (CL_DF[1] + CL_EF[1]) / 2 + 10, 2.35)),
                    (le("L062"), ((CL_DF[0] + CL_EF[0]) / 2, (CL_DF[1] + CL_EF[1]) / 2 + 10, 2.5))], blur=2.5, locked=True),
    RW(ls("L063"), [(ls("L063"), (836, 380, 1.9)), (ls("L064"), (836, 372, 2.0))], blur=1.0),
    RW(m("c_ref2"), [(m("c_ref2"), (900, 400, 1.7)), (m("c_aj2"), (900, 395, 1.78))], blur=1.0),
    BW(m("c_aj2"), "S", "joshua", "mid", (1120, 1000), blur=3.5),
    BW(m("c_ty2"), "S", "tyson", "lean", (520, 1000), blur=3.5),
    # apart; the wind-up; glove meets glove; the wobble; both sit; the look; the bell; up they come
    RW(tsep, [(tsep, (836, 480, 1.2)), (tcs, (836, 470, 1.25))]),
    RW(tcs, [(tcs, (836, 470, 1.05)), (twb + 0.6, (836, 480, 1.1))]),
    RW(tsit - 0.15, (836, ED_R[1] - 941 / (2 * 1.75), 1.75), locked=True, drift=0.0),
]

# ====================================================================== 7. the decision and the series button
ann_ring = P("announcer", keys((0, "mic"), (wt("L069", "draw") - 0.1, "mic_gesture"), (le("L069") + 0.2, "mic")), (1360, 620),
             show=[(m("c_ann4"), m("c_steps"))])
decision = [eddie_fight, dana_fight, ann_ring, NEAR]
decision_close = [eddie_fight, dana_fight, NEAR]
# out through the ropes at the near-left corner and down the ring steps (the arena wide); then ringside, on the floor
# in front of the apron, where the bin is waiting (the ringside set: its floor is the arena floor)
tst, tbn, tcd = m("c_steps"), m("c_bin"), m("card")
TREADS = [(250, 724), (190, 746), (152, 786), (122, 824), (40, 868)]    # the rope line, the three treads, the floor


def down_steps(who, t0, mirror=False, wait=(400, 690)):
    """waiting in the ring, ducking out under the ropes, then one tread at a time, each foot landing (a little dip
    on each tread)"""
    xs = [(0, wait), (t0 - 0.3, wait), (t0, TREADS[0])]
    for i, p in enumerate(TREADS[1:]):
        xs.append((t0 + 0.36 + 0.32 * i, p))
    xs.append((xs[-1][0] + 0.5, (-260, 880)))                # and on, out of shot towards the bin
    # the steps run down the side of the ring, at its corner's depth: a person on them stays that size
    return P(who, keys((0, "tired"), (t0 - 0.2, "crouch_guard"), (t0 + 0.3, "tired")), xs, ease=True, steps=True,
             mirror=mirror, floor=680,
             dy=keys(*[(t0 + 0.36 + 0.32 * i + d, v) for i in range(4) for d, v in ((0.0, 0.0), (0.12, 10.0), (0.3, 0.0))]))


steps_cast = [down_steps("eddie", tst, mirror=True), down_steps("dana", tst + 1.55)]          # both heading left
Y_S = 868                                                    # the floor in front of the apron
TB_S = 800
ATT_S, TRO_S, PATH_S = push("S", m("depart") - 0.1, m("depart") + 2.7, TB_S, 260, Y_S, mirror=True, step=0.55)
TH_S = TRO_S["h"]
ATT_S["pose"] = [(0, "hip"), (tcd - 0.25, "point2"), (tcd + 0.2, "hip"), (ls("L076") - 0.05, "point2"),
                 (le("L076") + 0.3, "hip")] + [kv for kv in ATT_S["pose"] if kv[0] >= m("depart") - 0.1]
ATT_S["mirror"] = True
ATT_S["at"] = [(0, ATT_S["at"][0][1])] + ATT_S["at"]
TRO_S["at"] = [(0, TRO_S["at"][0][1])] + TRO_S["at"]
PATH_S = TRO_S["at"]
ATT_XS = PATH_S[0][1][0] + (ATT_S["at"][0][1][0] - PATH_S[0][1][0])
tcb = m("climb2")
DA_S, ED_S = (610, Y_S + 4), (1530, 838)
dana_s = P("dana", keys((0, "tired"), (tbn + 1.1, "guard"), (ls("L075") - 0.05, "guard_high"), (le("L075") + 0.2, "guard"),
                        (tcb, "crouch_guard"), (tcb + 0.42, "guard")),
           keys((tbn, (-160, 850)), (tbn + 1.1, DA_S), (tcb + 0.45, DA_S), (tcb + 0.85, (TB_S - 20, Y_S + 2))),
           steps=True, ease=True, mirror=True,
           dy=keys((tcb + 0.4, 0.0), (tcb + 0.65, 0.55 * h_of("S", "dana", Y_S)), (tcb + 0.9, 0.32 * h_of("S", "dana", Y_S)),
                   (tcb + 1.25, -160.0)),
           clip=keys((0, None), (tcb + 0.78, Y_S - 0.25 * TH_S)), z=Y_S - 3, show=[(tbn, tcb + 1.28)])
eddie_s = P("eddie", keys((0, "tired"), (tbn + 1.2, "guard"), (m("c_eddie10"), "arms_up")),
            ED_S, mirror=True,                                   # (already over by the bin at the cut)
            face=[(m("c_eddie10"), 1e9, 0.7, 0.85)], z=ED_S[1], show=[(tbn, 1e9)])
fare_s = dict(fn="fare", t0=tcd + 0.05, at=[(a, (x + 0.1 * TH_S, y - 0.48 * TH_S)) for a, (x, y) in PATH_S],
              h=0.36 * TH_S, rot=5.0, z=Y_S + 2.4)
lid_s = dict(fn="lid", at=[(a, (x, y - 0.93 * TH_S)) for a, (x, y) in PATH_S], w=1.08 * TH_S, z=Y_S + 2.5,
             rot=keys((0, 0.0), (tcb + 0.05, 0.0), (tcb + 0.3, 85.0), (tcb + 1.1, 85.0), (tcb + 1.35, 0.0)))
outside = [eddie_s, dana_s, ATT_S, TRO_S, dict(fn="wheels", trolley=TRO_S, z=Y_S + 2.2),
           towels_on(PATH_S, TH_S, Y_S + 1.5, mirror=True,
                     dy=keys((tcb + 1.05, 0.0), (tcb + 1.15, 26.0), (tcb + 1.4, 0.0))), fare_s, lid_s]
CAPTIONS_EXTRA = [(m("admire") + 0.1, m("admire") + 2.3, "series", "THE UNDERCARD", "HEARN  v  WHITE"),
                  (m("depart") + 0.4, m("black") + 0.4, "end", "THE UNDERCARD", "HEARN  v  WHITE  ·  THE REMATCH")]
S7 = [
    RW(m("c_ann4"), [(m("c_ann4"), (836, 500, 1.3)), (m("c_ed9"), (836, 495, 1.35))], decision),
    RW(m("c_ed9"), on("R", 600, ED_R[1], "eddie", 0.55, dx=-60), decision_close, blur=2.0),
    RW(m("c_da9"), on("R", 1070, DA_R[1], "dana", 0.55, dx=60), decision_close, blur=2.0),
    W(m("c_fj4"), "S", (836, 700, 1.5), ringside()),
    W(tst, "A", [(tst, (643, 545, 1.3)), (tbn, (643, 548, 1.3))], steps_cast, occl=("rail",), locked=True, drift=0.0),
    W(tbn, "S", [(tbn, (950, 640, 1.1)), (m("c_da10"), (950, 636, 1.13))], outside, blur=0.5),
    W(m("c_da10"), "S", on("S", *DA_S, "dana", 0.62, dx=40), outside, blur=2.0),
    W(m("c_att10"), "S", on("S", ATT_XS, Y_S, "attendant", 0.62, dx=-40), outside, blur=2.0),
    W(m("c_eddie10"), "S", on("S", *ED_S, "eddie", 0.5, dx=30), outside, blur=2.5),
    W(m("climb2"), "S", [(m("climb2"), (950, 640, 1.1)), (m("black"), (900, 640, 1.12))], outside),
    card(m("black"), "black"),
]

SHOTS = finish(sorted(S1 + S1b + S2 + S2a + S2b + S3 + S4 + S4b + S5 + S5b + S6 + S7, key=lambda s: s["t"]),
               TL["total"])
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

CAPTIONS = [(s["t"] + 0.3, min(s["end"], s["t"] + 3.3), "place", *s["caption"]) for s in SHOTS if s.get("caption")] + \
    CAPTIONS_EXTRA


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

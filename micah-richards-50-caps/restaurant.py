"""The flashback: Wing's, Wilmslow. Setups registered into direction.EXTRA_SETUPS.

  exterior   the Rooneys walk in (walk cycles from the sheets, bob + stride matched to the ground speed)
  table      the Rooney family at their round table: Wayne, Coleen and the four boys (busts at the table)
  party      Micah's 50 CAPS party (see party.py)
All coordinates are 1x plate px of the 941 x 1672 portrait plates (the engine scales them x4 to the upscaled plate)."""
import math, numpy as np, cv2
import perf, cast
from perf import W
from render_util import *

# ---------------------------------------------------------------- walking family
FAMILY = ["wr", "cr", "b1", "b2", "b3", "b4"]
WALK_ORDER = {"wr": [0, 1, 2, 1], "cr": [0, 1, 2, 3], "b1": [0, 1, 2, 3], "b2": [0, 1, 2, 3], "b3": [0, 1, 2, 3], "b4": [0, 1, 2, 3]}
WALK_SCALE = {"wr": 3.45, "cr": 3.3, "b1": 2.75, "b2": 2.7, "b3": 2.65, "b4": 2.6}


def walker(ch, t, t0, x0, vx, y, flip=True, scale=None, cycle=0.92, stop_x=None):
    """one walk-cycle actor moving vx px/s on average from x0. The ground is covered in steps: each drawing's hold starts with a
    quick push forward (the new foot lands) and then the body stays put while the foot is planted, so the feet do not glide."""
    order = WALK_ORDER[ch]
    hold = cycle / len(order)
    k, frac = divmod(max(0.0, t - t0), hold)
    u = min(1.0, frac / (0.45 * hold)); u = u * u * (3 - 2 * u)
    x = x0 + vx * hold * (k + u)
    moving = True
    if stop_x is not None and ((vx < 0 and x <= stop_x) or (vx > 0 and x >= stop_x)):
        x, moving = stop_x, False
    fr = order[int(k) % len(order)] if moving else order[0]
    name = f"{ch}_w{fr}"
    sc = scale or WALK_SCALE[ch]
    a = Actor(name, x, y, sc, flip=flip, anchor="upper", z=y)
    bob = -math.sin(u * math.pi) * 3.0 * (1 if moving else 0)          # a small lift during the push, down when the foot plants
    Bm = body_matrix(a.anchor, dy=bob * 4)
    return (a, None, Bm, 1.0)


END_X = {"wr": 215, "cr": 350, "b1": 478, "b2": 580, "b3": 680, "b4": 775}      # where each stands when the shot ends
T_EXT_END = 16.65
VX = -330.0


def render_exterior(s, t, cam):
    st = plate("w_exterior")
    acts = []
    for ch in FAMILY:
        x0 = END_X[ch] - VX * (T_EXT_END - (s["t0"] - 0.4)) * (-1)       # start right of the door, walk left
        y = 1300 + (10 if ch.startswith("b") else 0)
        acts.append(walker(ch, t, s["t0"] - 0.4, END_X[ch] + 330.0 * (T_EXT_END - (s["t0"] - 0.4)), VX, y))
    return st.render(cam, acts, dof=0.0)


# ---------------------------------------------------------------- the family at the round table
TABLE = [(0, 906), (0, 1672), (941, 1672), (941, 884), (900, 868), (700, 850), (520, 846), (300, 843), (100, 851)]
LAMP = [(384, 928), (392, 776), (420, 764), (456, 776), (466, 928)]
VASE = [(452, 928), (468, 832), (480, 742), (520, 726), (552, 752), (560, 832), (548, 928)]
SIT = {            # x, scale (right-facing views are native; flip=True looks left)
    "wr": (140, 1.18), "cr": (292, 1.06), "b1": (432, 0.94), "b2": (550, 0.92), "b3": (668, 0.94), "b4": (786, 0.90),
}
BASE_Y = 958
FAM_DEFAULT = {c: f"{c}_b_front" for c in FAMILY}


def table_actors(t):
    acts = []
    for ch in FAMILY:
        x, sc = SIT[ch]
        name, flip = pose_of(ch, t, FAM_DEFAULT[ch])
        acts.append(bust(ch, name, x, BASE_Y, sc, t, flip=flip, z=1.0, talks=False))
    return acts


def render_table(s, t, cam):
    st = plate("w_round", occluders=[TABLE, LAMP, VASE])
    return st.render(cam, table_actors(t), dof=s.get("dof", 0.0))


EXTRA = {"exterior": render_exterior, "table": render_table}

"""The flashback: Wing's, Wilmslow - the walk-in and the Rooney family's table. Registered into direction.EXTRA_SETUPS.

  exterior   the Rooneys walk in along the pavement: rigged walks (walkrig.py), feet planted, the children smaller and quicker
  table      the family seated behind their round table in their SEATED poses (arms on the table); kids clearly smaller
All coordinates are 1x plate px of the 941 x 1672 portrait plates."""
import math, numpy as np, cv2
import perf, cast
from perf import W
from render_util import *
import walkrig as WR

FAMILY = ["wr", "cr", "b1", "b2", "b3", "b4"]

# ---------------------------------------------------------------- the walk-in
# (turnaround drawing facing screen-left, mirror?, scale plate px per sheet px, start x at T_WALK0, floor y, step fraction of the leg)
WALKERS = {
    "wr": ("wr_t_q34R", False, 1.62, 730, 1330, 0.52),
    "cr": ("cr_t_q34R", False, 1.62, 850, 1318, 0.50),
    "b1": ("b1_t_q34L", True, 1.20, 965, 1336, 0.50),
    "b2": ("b2_t_q34L", True, 1.16, 1062, 1322, 0.50),
    "b3": ("b3_t_q34L", True, 1.12, 1158, 1340, 0.50),
    "b4": ("b4_t_q34L", True, 1.04, 1250, 1326, 0.50),
}
WALK_SPEED = 150.0                       # plate px / s for the whole group
MENU = [(0, 860), (30, 830), (205, 860), (225, 1000), (200, 1040), (110, 1060), (110, 1330), (185, 1340), (185, 1395), (0, 1395)]


def render_exterior(s, t, cam):
    st = plate("w_exterior", occluders=[MENU])
    t0 = s["t0"] - 0.6
    fg = []
    for ch in FAMILY:
        d, mir, sc, x0, fy, stepf = WALKERS[ch]
        fg += [(a, None, None, 1.0) for a in WR.walker(d, mir, x0, fy, sc, t, t0, WALK_SPEED, step_frac=stepf, z=fy)]
    fg.sort(key=lambda a: a[0].z)
    return st.render(cam, fg, dof=0.0)


# ---------------------------------------------------------------- the family at the round table
TABLE = [(0, 905), (60, 893), (150, 886), (300, 881), (450, 879), (600, 880), (750, 883), (900, 890), (941, 896), (941, 1672), (0, 1672)]
GLASS_L = [(166, 1000), (170, 900), (175, 850), (190, 830), (215, 840), (222, 880), (210, 925), (200, 1000)]
GLASS_M = [(305, 880), (300, 835), (310, 800), (345, 800), (355, 840), (350, 880)]
LAMP = [(402, 990), (420, 860), (405, 857), (420, 805), (480, 805), (493, 857), (478, 860), (470, 990)]
FLOWERS = [(480, 990), (492, 900), (488, 830), (512, 780), (560, 770), (600, 800), (612, 860), (606, 990)]
GLASS_R = [(668, 1000), (672, 880), (680, 830), (700, 822), (720, 840), (722, 900), (712, 1000)]
EDGE_Y = 883
# head centre (plate px), head height (plate px); the children are clearly smaller than Wayne and Coleen
SEATS = {"wr": (110, 80), "cr": (245, 76), "b1": (360, 60), "b2": (650, 58), "b3": (765, 60), "b4": (870, 56)}
# sheet y of the top of the table drawn under each seated pose (so our tablecloth's edge takes its place)
TABLE_TOP = {"wr_p_seated": 1077, "cr_p_seated": 1149, "cr_p_reaction": 1149, "cr_p_laughing": 1150, "b1_p_seated": 1181, "b2_p_seated": 1172,
             "b3_p_seated": 1178, "b4_p_seated": 1157, "wr_e_laughing": 850}


def seated(ch, name, flip, t, x, hpx, edge_y, talks=False, z=1.0):
    hx, hy = cast.head_c(name)
    sc = hpx / cast.head_h(name)
    top = TABLE_TOP.get(name, cast.bottom_y(name) - 6)
    y = edge_y + 3 - (top - hy) * sc                   # the drawing's table (or its flat cut) goes just under our tablecloth
    a = Actor(name, x, y, sc, flip=flip, anchor=(hx, hy), z=z)
    st, b = face_state(ch, t, flip=flip, talks=talks)
    bx, by = a.d.P(hx, cast.bottom_y(name))
    fwd = b.get("fwd", 0.0)
    Bm = body_matrix((bx, by), breath=b["breath"], lean=b["lean"] + 4 * fwd, sx=1 + 0.03 * fwd, sy=1 + 0.03 * fwd)
    return (a, st, Bm, 1.0)


def table_actors(t, seats=SEATS, edge_y=EDGE_Y):
    acts = []
    for ch in FAMILY:
        x, hpx = seats[ch]
        name, flip = pose_of(ch, t, f"{ch}_p_seated")
        acts.append(seated(ch, name, flip, t, x, hpx, edge_y))
    return acts


def render_table(s, t, cam):
    st = plate("w_round", occluders=[TABLE, GLASS_L, GLASS_M, LAMP, FLOWERS, GLASS_R])
    st.rim = (-0.9, -0.4, 0.22, (1.0, 0.78, 0.45))       # warm lamp light from camera-right
    return st.render(cam, table_actors(t), dof=s.get("dof", 0.0))


EXTRA = {"exterior": render_exterior, "table": render_table}

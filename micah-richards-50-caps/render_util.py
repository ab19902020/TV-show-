"""Shared rendering helpers: plates, camera, pose lookup, face state, busts. (No shots live here.)"""
import os, math, numpy as np, cv2
os.environ.setdefault("EP_RES", "1080x1920")
import engine as E
import perf, cast, stage
from stage import Actor, Stage, body_matrix

FPS, OW, OH, RS = 30, E.OW, E.OH, E.RS


def smooth(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def ease(u, kind="smooth"):
    u = min(max(u, 0.0), 1.0)
    if kind == "linear": return u
    if kind == "out": return 1 - (1 - u) ** 3
    if kind == "in": return u ** 2
    return 0.5 - 0.5 * math.cos(math.pi * u)


# ---------------------------------------------------------------- stages (loaded lazily, a few kept)
_ST = {}


def plate(name, occluders=()):
    if name not in _ST:
        if len(_ST) >= 3: _ST.pop(next(iter(_ST)))
        _ST[name] = Stage(f"build/bg/{name}.png", occluders=occluders, name=name)
    return _ST[name]


# ---------------------------------------------------------------- camera
def camera(s, t):
    """(cx, cy, w) in 1x plate px: eased move between c0 and c1 plus a little hand-held drift (restaurant) / none (studio)"""
    u = ease((t - s["t0"]) / max(1e-3, s["t1"] - s["t0"]), s.get("ease", "smooth"))
    cx, cy, w = [a + (b - a) * u for a, b in zip(s["c0"], s["c1"])]
    if s.get("punch"):                                   # a quick push-in that settles
        k = math.exp(-(t - s["t0"]) / 0.10); w *= 1 - 0.09 * k
    a = 0.006 * s.get("shake", 0.0)
    cx += w * a * (math.sin(2 * math.pi * 0.7 * t + 1.3) + 0.6 * math.sin(2 * math.pi * 1.9 * t + 0.2))
    cy += w * a * 0.8 * (math.sin(2 * math.pi * 0.6 * t + 2.1) + 0.5 * math.sin(2 * math.pi * 1.7 * t + 0.9))
    return cx, cy, w


# ---------------------------------------------------------------- characters
def pose_of(ch, t, default):
    p = perf.pose_at(ch, t, default)
    flip = p.endswith("|f")
    return (p[:-2] if flip else p), flip


def face_state(ch, t, flip=False, talks=True, **over):
    s, b = perf.state(ch, t, talks=talks)
    s.update(over)
    if flip:
        s["lookx"], s["turn"], s["tilt"] = -s["lookx"], -s["turn"], -s["tilt"]
    return s, b


def body_for(actor, b, extra=None):
    """breathing + lean about the anchor; fwd = leaning towards camera (scale up, drop a little)"""
    ax, ay = actor.anchor
    fwd = b.get("fwd", 0.0)
    k = 1 + 0.045 * fwd
    shr = b.get("shrug", 0.0)
    Bm = body_matrix((ax, ay), breath=b["breath"], lean=b["lean"], sx=k, sy=k, dy=0.02 * fwd * 400 - shr * 26)
    if extra is not None: Bm = Bm @ extra
    return Bm


def bust(ch, drawing, x, y, scale, t, flip=False, z=1.0, talks=True, **over):
    """one head-and-shoulders bust drawn at (x, y) = bottom centre of its torso extension; returns an actor tuple for Stage.render.
    The `_x` version (extend.py) is used when it exists, so the desk / table hides a torso, not a cut."""
    if not drawing.endswith("_x") and (drawing + "_x") in E.META: drawing += "_x"
    a = Actor(drawing, x, y, scale, flip=flip, anchor="base", z=z)
    s, b = face_state(ch, t, flip=flip, talks=talks and cast.can_talk(drawing), **over)
    return (a, s, body_for(a, b), 1.0)




# ---------------------------------------------------------------- the studio set (1x plate px of the extended studio plate)
STUDIO_EXT = 160
STUDIO_SEAT = dict(gary=(735, 742), rooney=(980, 730), micah=(1225, 730))
STUDIO_SCALE = dict(gary=1.30, rooney=1.30, micah=1.38)


def collar_world(drawing, x, y, scale, flip=False):
    """plate position of a bust's neck pivot when its bottom centre is at (x, y)"""
    if not drawing.endswith("_x") and (drawing + "_x") in E.META: drawing += "_x"
    d = cast.get(drawing)
    bx, by = d.anchors["base"]; cx, cy = d.anchors["collar"]
    return x + (cx - bx) * scale / 4 * (-1 if flip else 1), y + (cy - by) * scale / 4      # part px are 4x px; x, y are 1x plate px


def cam_for_collar(drawing, x, y, scale, u, v, app, flip=False):
    """camera (cx, cy, w) that puts the bust's neck at screen fraction (u, v) with `app` screen px per sheet px.
    Used twice, with the same (u, v, app), for a match cut between two different plates."""
    w = scale * OW / app
    h = w * OH / OW
    px, py = collar_world(drawing, x, y, scale, flip)
    return px - (u - 0.5) * w, py - (v - 0.5) * h, w

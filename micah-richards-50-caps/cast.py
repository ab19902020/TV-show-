"""Every drawing the film uses: a cut part (build/parts) + its face landmarks (sheet coordinates) + anchors.

Faces:   mouth = (left corner x, y, right corner x, y, centre x, y) of the closed mouth line, chin = y of the chin, eyes from
         eyes.py. Only Gary, Rooney and Micah ever talk, so only their lip-sync busts (and a few more) carry a mouth.
Heads:   head box, chin and neck pivot come from the part's alpha (heads.json), so tilt / nod / turn work on every bust.
Anchors: base = bottom centre of the part, mid, top; collar = the neck pivot.

Facing: nearly every 3/4 and side drawing on the sheets turns to SCREEN-RIGHT (checked with measure_facing). To look left, flip
the actor."""
import json, os
import numpy as np
from PIL import Image
from engine import Drawing, META

EYES = json.load(open("build/eyes.json")) if os.path.exists("build/eyes.json") else {}

# hand-measured mouth landmarks of the speaking busts (read off 4x grids of the sheets)
MARKS = {
    "wr_b_front": dict(mouth=(358, 626, 418, 621, 388, 628), chin=667),
    "wr_b_q34L":  dict(mouth=(541, 627, 590, 622, 565, 629), chin=665),
    "wr_b_q34R":  dict(mouth=(848, 624, 913, 621, 880, 627), chin=666),
    "mr_b_front": dict(mouth=(337, 645, 396, 645, 366, 650), chin=686),
    "mr_b_q34R":  dict(mouth=(856, 646, 909, 633, 880, 651), chin=677),
    "gy_b_front": dict(mouth=(348, 652, 394, 653, 371, 658), chin=679),
    "gy_b_q34L":  dict(mouth=(533, 651, 569, 649, 551, 655), chin=682),
    "gy_b_q34R":  dict(mouth=(854, 652, 890, 649, 872, 656), chin=684),
}

_heads = json.load(open("build/heads.json")) if os.path.exists("build/heads.json") else {}
_built = {}


def head_geometry(name):
    """head box (x0, y0, x1, y1), chin y and neck pivot, in sheet coordinates, from the part's alpha"""
    if name in _heads: return _heads[name]
    kind = name.split("_")[1] if "_" in name else ""
    ox, oy = META[name]["off"]
    a = np.asarray(Image.open(f"build/parts/{name}.png"))[..., 3] > 128
    ys, xs = np.nonzero(a)
    top, bot = ys.min(), ys.max()
    chin_f, neck_f = {"b": (0.89, 0.985), "e": (0.80, 0.93)}.get(kind, (0.30, 0.34))
    chin = top + chin_f * (bot - top)
    rows = a[top:int(chin) + 1]
    cols = np.nonzero(rows.any(0))[0]
    g = dict(head=[ox + cols.min() / 4, oy + top / 4, ox + cols.max() / 4, oy + chin / 4], chin=oy + chin / 4,
             neck=[ox + (cols.min() + cols.max()) / 8, oy + (top + neck_f * (bot - top)) / 4])
    _heads[name] = g
    return g


_anch = json.load(open("build/anchors.json")) if os.path.exists("build/anchors.json") else {}


def anchors_of(name):
    """feet / base = the body's own bottom centre (centre of mass of the bottom rows, so a swinging leg or a pointing arm does not
    move it), mid, top, bottom-left / right"""
    if name in _anch: return {k: tuple(v) for k, v in _anch[name].items()}
    m = META[name]
    ox, oy = m["off"]
    a = np.asarray(Image.open(f"build/parts/{name}.png"))[..., 3] > 128
    ys, xs = np.nonzero(a)
    top, bot = ys.min(), ys.max()
    band = a[max(top, int(bot - 0.18 * (bot - top))):bot + 1]
    bx = np.nonzero(band)[1]
    cxb = bx.mean() if len(bx) else xs.mean()
    upper = a[top:top + max(2, int(0.5 * (bot - top)))]
    ux = np.nonzero(upper)[1]
    cxu = ux.mean() if len(ux) else xs.mean()
    mid = (xs.min() + xs.max()) / 2
    r = dict(feet=(ox + cxb / 4, oy + bot / 4), base=(ox + cxb / 4, oy + bot / 4), upper=(ox + cxu / 4, oy + bot / 4),
             mid=(ox + mid / 4, oy + (top + bot) / 8), top=(ox + mid / 4, oy + top / 4))
    _anch[name] = {k: list(v) for k, v in r.items()}
    return r


def save_anchors():
    json.dump(_anch, open("build/anchors.json", "w"))
    json.dump(_heads, open("build/heads.json", "w"))


def get(name):
    if name not in _built:
        base = name[:-2] if name.endswith("_x") else name          # `_x` = the bust with a torso (extend.py): same face, same head
        kw = dict(MARKS.get(base, {}))
        eyes = [tuple(e) for e in EYES.get(base, [])]
        anchors = anchors_of(name)
        kind = base.split("_")[1] if "_" in base else ""
        if kind in ("b", "e"):
            g = head_geometry(base)
            kw.setdefault("chin", g["chin"])
            kw["head"] = tuple(g["head"]); kw["neck"] = tuple(g["neck"])
            anchors["collar"] = tuple(g["neck"])
        _built[name] = Drawing(name, name, eyes=eyes, anchors=anchors, **kw)
    return _built[name]


def can_talk(name):
    return (name[:-2] if name.endswith("_x") else name) in MARKS


def size(name):
    """(width, height) of the part in sheet px"""
    w, h = META[name]["size"]
    return w / 4, h / 4


def build_cache(kind=None):
    """measure and save head geometry (busts) and anchors (every part); kind 'heads' runs before extend.py, 'anchors' after it"""
    for n in META:
        k = n.split("_")[1] if "_" in n else ""
        if kind in (None, "heads") and k in ("b", "e") and not n.endswith("_x"): head_geometry(n)
        if kind in (None, "anchors"): anchors_of(n)
    save_anchors()

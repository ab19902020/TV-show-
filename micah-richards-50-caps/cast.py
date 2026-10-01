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
    # waist-up poses (8x parts). grin=True: the drawn mouth is an open grin, so the lip sync opens it further without painting
    # extra teeth (the drawn teeth part)
    "as_p_listening": dict(mouth=(500, 1042, 530, 1035, 514, 1041), chin=1062),
    "gy_p_talking1":  dict(mouth=(598, 1111, 618, 1108, 608, 1112), chin=1121, grin=True),
    "wr_p_talking":   dict(mouth=(662, 993, 702, 990, 682, 998), chin=1010, grin=True),
    "wr_p_shrug":     dict(mouth=(835, 1003, 867, 997, 852, 1003), chin=1013),
    "m2_p_seated":    dict(mouth=(800, 1115, 840, 1113, 820, 1121), chin=1138, grin=True),
    "m2_p_talking":   dict(mouth=(98, 1116, 127, 1112, 112, 1119), chin=1132, grin=True),
    "m2_p_pointing":  dict(mouth=(440, 1117, 468, 1113, 453, 1120), chin=1133, grin=True),
    "m2_p_handsup":   dict(mouth=(600, 1112, 640, 1111, 620, 1117), chin=1132, grin=True),
    "m2_p_shrug":     dict(mouth=(270, 1117, 298, 1112, 284, 1120), chin=1133, grin=True),
    "as_p_talking":   dict(mouth=(285, 1036, 330, 1031, 308, 1042), chin=1065, grin=True),
    "as_p_pointing":  dict(mouth=(100, 1031, 138, 1042, 120, 1043), chin=1060, grin=True),
    "wr_p_seated":    dict(mouth=(1042, 1000, 1075, 996, 1058, 1003), chin=1014, grin=True),
    "gy_p_talking2":  dict(mouth=(695, 1110, 715, 1106, 705, 1112), chin=1121, grin=True),
}

_heads = json.load(open("build/heads.json")) if os.path.exists("build/heads.json") else {}
# head box and neck pivot of the waist-up poses (sheet coords), for head tilt / nod / turn
POSE_HEADS = {
    "as_p_listening": ((455, 965, 543, 1062), (505, 1070)), "gy_p_talking1": ((575, 1065, 625, 1121), (603, 1128)),
    "wr_p_talking": ((640, 940, 722, 1010), (688, 1015)), "wr_p_shrug": ((790, 945, 875, 1013), (845, 1018)),
    "m2_p_seated": ((785, 1052, 848, 1138), (818, 1142)), "m2_p_talking": ((60, 1052, 135, 1132), (105, 1137)),
    "m2_p_pointing": ((400, 1055, 475, 1133), (440, 1138)), "m2_p_handsup": ((585, 1052, 655, 1132), (620, 1137)),
    "m2_p_shrug": ((235, 1052, 310, 1133), (275, 1138)),
    "as_p_talking": ((260, 965, 345, 1065), (305, 1072)), "as_p_pointing": ((62, 965, 150, 1062), (105, 1070)),
    "as_p_thinking": ((630, 965, 712, 1062), (668, 1070)), "wr_p_seated": ((1012, 945, 1095, 1014), (1055, 1018)),
    "wr_p_handsup": ((905, 945, 985, 1012), (948, 1016)), "gy_p_talking2": ((665, 1065, 718, 1121), (692, 1128)),
    "gy_p_pointing": ((757, 1065, 810, 1121), (783, 1128)), "gy_p_amused": ((875, 1065, 925, 1121), (900, 1128)),
    "m2_p_placard": ((968, 1065, 1035, 1135), (1000, 1140)),
}
_built = {}


def head_geometry(name):
    """head box (x0, y0, x1, y1), chin y and neck pivot, in sheet coordinates, from the part's alpha"""
    if name in _heads: return _heads[name]
    kind = name.split("_")[1] if "_" in name else ""
    ox, oy = META[name]["off"]
    q = float(META[name].get("scale", 4))
    a = np.asarray(Image.open(f"build/parts/{name}.png"))[..., 3] > 128
    ys, xs = np.nonzero(a)
    top, bot = ys.min(), ys.max()
    chin_f, neck_f = {"b": (0.89, 0.985), "e": (0.80, 0.93)}.get(kind, (0.30, 0.34))
    chin = top + chin_f * (bot - top)
    rows = a[top:int(chin) + 1]
    cols = np.nonzero(rows.any(0))[0]
    g = dict(head=[ox + cols.min() / q, oy + top / q, ox + cols.max() / q, oy + chin / q], chin=oy + chin / q,
             neck=[ox + (cols.min() + cols.max()) / (2 * q), oy + (top + neck_f * (bot - top)) / q])
    _heads[name] = g
    return g


_anch = json.load(open("build/anchors.json")) if os.path.exists("build/anchors.json") else {}


def anchors_of(name):
    """feet / base = the body's own bottom centre (centre of mass of the bottom rows, so a swinging leg or a pointing arm does not
    move it), mid, top, bottom-left / right"""
    if name in _anch: return {k: tuple(v) for k, v in _anch[name].items()}
    m = META[name]
    ox, oy = m["off"]
    q = float(m.get("scale", 4))
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
    r = dict(feet=(ox + cxb / q, oy + bot / q), base=(ox + cxb / q, oy + bot / q), upper=(ox + cxu / q, oy + bot / q),
             mid=(ox + mid / q, oy + (top + bot) / (2 * q)), top=(ox + mid / q, oy + top / q))
    _anch[name] = {k: list(v) for k, v in r.items()}
    return r


def save_anchors():
    json.dump(_anch, open("build/anchors.json", "w"))
    json.dump(_heads, open("build/heads.json", "w"))


def get(name):
    if name not in _built:
        base = name
        kw = dict(MARKS.get(base, {}))
        eyes = [tuple(e) for e in EYES.get(base, [])]
        anchors = anchors_of(name)
        kind = base.split("_")[1] if "_" in base else ""
        if base in POSE_HEADS:
            kw["head"], kw["neck"] = POSE_HEADS[base]
            anchors["collar"] = tuple(POSE_HEADS[base][1])
        elif kind in ("b", "e"):
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
    q = float(META[name].get("scale", 4))
    return w / q, h / q


def build_cache(kind=None):
    """measure and save head geometry (busts) and anchors (every part); kind 'heads' runs before extend.py, 'anchors' after it"""
    for n in META:
        k = n.split("_")[1] if "_" in n else ""
        if kind in (None, "heads") and k in ("b", "e") and not n.endswith("_x"): head_geometry(n)
        if kind in (None, "anchors"): anchors_of(n)
    save_anchors()


# seated / laughing poses without hand-measured heads: the head is the top ~half of the drawing (sheet coords, estimated)
def head_box(name):
    """head box (x0, y0, x1, y1) in sheet coords: hand-measured for the talking poses, measured from the alpha for busts,
    estimated (top 52 % of the drawing, the widest run there) otherwise"""
    base = name[:-2] if name.endswith("_x") else name
    if base in POSE_HEADS: return tuple(POSE_HEADS[base][0])
    kind = base.split("_")[1] if "_" in base else ""
    if kind in ("b", "e"): return tuple(head_geometry(base)["head"])
    if base in _HB: return _HB[base]
    m = META[base]; ox, oy = m["off"]; q = float(m.get("scale", 4))
    a = np.asarray(Image.open(f"build/parts/{base}.png"))[..., 3] > 128
    ys, xs = np.nonzero(a)
    top, bot = ys.min(), ys.max()
    frac = 0.52 if kind == "p" else 0.27
    yb = int(top + frac * (bot - top))
    # the head's columns: the run around the centre of mass of the top 30 % of the head band
    band = a[top:yb]
    cx = np.nonzero(band[: max(2, int(0.3 * (yb - top)))])[1].mean()
    cols = np.nonzero(band.any(0))[0]
    # narrow to the run containing cx in the middle row of the band
    row = band[int(0.6 * (yb - top))]
    xs_ = np.nonzero(row)[0]
    if len(xs_):
        br = np.nonzero(np.diff(xs_) > 1)[0]
        runs = list(zip([xs_[0]] + list(xs_[br + 1]), list(xs_[br]) + [xs_[-1]]))
        run = min(runs, key=lambda r: 0 if r[0] <= cx <= r[1] else min(abs(r[0] - cx), abs(r[1] - cx)))
        x0, x1 = run
    else:
        x0, x1 = cols.min(), cols.max()
    _HB[base] = (ox + x0 / q, oy + top / q, ox + x1 / q, oy + yb / q)
    return _HB[base]


_HB = {}


def head_h(name):
    b = head_box(name); return b[3] - b[1]


def head_c(name):
    b = head_box(name); return ((b[0] + b[2]) / 2, (b[1] + b[3]) / 2)


def bottom_y(name):
    """sheet y of the drawing's lowest solid row"""
    m = META[name]; q = float(m.get("scale", 4))
    return m["off"][1] + anchors_of(name)["base"][1] - m["off"][1]

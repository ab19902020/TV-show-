"""The Undercard's people and props in a set: the engine's "world" shot with one ("props", "scene") layer that draws
everything a shot lists in s["cast"], in depth order. Whole drawings only (studio.film.art): poses change on a beat,
walks cycle the sheet's eight walk drawings while the feet move along a path, a tumble rotates a whole drawing
through the air; faces act through the engine (perf.py: lip sync, blinks, eyes, brows, head).

A cast item is a dict. People:
  who        perf name (eddie, dana, tyson, joshua, announcer, referee, attendant, security)
  pose       a drawing name, or [(t, name), ...] (the drawing from that time on)
  at         feet in 1x plate px, or [(t, (x, y)), ...] (linear between keys; ease=True eases them)
  walk       dict(frames=[...], cycle=s, t0, t1): the walk drawings cycled while t0 <= t < t1
  mirror     flipped (a right-facing drawing walking left), or [(t, bool), ...]
  rot        degrees about the feet, or [(t, deg), ...] (eased): leans, the tumble, a wobble
  scale      x the true size; dy: [(t, plate px)] lift (eased) for a hop or a sink
  clip       plate y below which the drawing fades out (into the trolley); show: [(t0, t1)] visible spans
  look       a fixed gaze target for this shot (else perf.py's)
Props: prop=<library/props/hearn-white name>, at (bottom centre), h (plate px), rot, mirror, dy, clip, show.
Code-drawn things: fn=<things.py function>, called with (layer, item, t, M, sc).
z orders the items (default: feet y; larger is nearer)."""
import functools
import importlib
import math

import cv2
import numpy as np

from studio.film import engine as E
from studio.film.cast import CAST
from studio.film.engine import OH, OW, RS
from studio.paths import BUILD, LIBRARY

# who -> (character id, height cm, standing height of the reference drawing in sheet px)
PEOPLE = {"eddie": ("eddie-hearn", 191, 357), "dana": ("dana-white", 170, 347), "tyson": ("tyson-fury", 206, 431),
          "joshua": ("anthony-joshua", 198, 513), "announcer": ("ring-announcer", 175, 347),
          "referee": ("boxing-referee", 180, 336), "attendant": ("laundry-attendant", 160, 376),
          "security": ("security-guard", 183, 429)}
# the sheets draw a character at different sizes: sheet px of the casual sheet per sheet px of this one
SHEET = {"eddie_boxing": 1.02, "eddie_walk": 0.768, "dana_boxing": 1.0, "dana_laundry": 0.87, "dana_walk": 0.737}


def sm(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def at_time(v, t, ease=True):
    """a value or [(t, value), ...]: the keyed value at t (numbers and tuples interpolate, others step)"""
    if not isinstance(v, list):
        return v
    if t <= v[0][0]:
        return v[0][1]
    for (t0, a), (t1, b) in zip(v, v[1:]):
        if t0 <= t < t1:
            if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)):
                u = (t - t0) / max(1e-6, t1 - t0)
                return a + (b - a) * (sm(u) if ease else u)
            if isinstance(a, tuple) and isinstance(b, tuple):
                u = (t - t0) / max(1e-6, t1 - t0)
                u = sm(u) if ease else u
                return tuple(p + (q - p) * u for p, q in zip(a, b))
            return a
    return v[-1][1]


def visible(it, t):
    sh = it.get("show")
    return sh is None or any(a <= t < b for a, b in sh)


def key_of(who, name):
    return f"{PEOPLE[who][0]}:{name}"


# single drawings drawn at their own size (the peek is a close-up of the head over the trolley's rim)
DRAWING = {"dana-white:peek": 0.40}


def sheet_fac(key):
    if key in DRAWING:
        return DRAWING[key]
    cid, name = key.split(":")
    stem = CAST.spec(cid)["drawings"][name].get("sheet", "").split("/")[-1].replace("-clean.png", "")
    return SHEET.get(stem, 1.0)


@functools.lru_cache(maxsize=512)
def feet_mid(key):
    """where a drawing stands (sheet px): halfway between its feet (the middle of the bottom 12 % of the figure)
    and its lowest point. The engine's foot finder takes the lowest sole only, which in a boxing stance (one boot
    lower than the other) puts the anchor on one foot and makes the body jump sideways between poses"""
    d, _ = CAST.get(key)
    a = d.u8[1.0][..., 3] > 128
    ys, xs = np.nonzero(a)
    top, bot = ys.min(), ys.max()
    band = ys > bot - 0.12 * (bot - top)
    x = (xs[band].min() + xs[band].max()) / 2.0
    return (float(x / d.S + d.ox), float(bot / d.S + d.oy))


def ppc(s, y):
    """plate px per cm at floor height y (the shot's perspective: s["ppc"] = (horizon y, k))"""
    hz, k = s["ppc"]
    return max(0.05, (y - hz) * k)


def pose_at(it, t):
    w = it.get("walk")
    if w and w.get("t0", -1e9) <= t < w.get("t1", 1e9):
        fr = w["frames"]
        i = int(math.floor((t - w.get("t0", 0.0)) / w["cycle"] * len(fr))) % len(fr)
        return fr[i]
    return at_time(it["pose"], t)


def resolver(s, who, pos):
    def res(g):
        if g == "cam":
            return (0.0, 0.0, 0.0)
        if g == "down":
            return (0.05, 0.85, 0.0)
        if isinstance(g, tuple) and g[0] == "dir":
            return g[1:]
        if g in pos and who in pos:
            dx = pos[g][0] - pos[who][0]
            dy = pos[g][1] - pos[who][1]
            if abs(dx) < 1:
                return (0.0, 0.05, 0.0)
            sgn = 1.0 if dx > 0 else -1.0
            return (0.85 * sgn, float(np.clip(dy / (abs(dx) + 200.0), -0.3, 0.7)), 0.3 * sgn)
        return (0.0, 0.05, 0.0)
    return res


def person_matrix(s, it, key, t, M, sc):
    who = it["who"]
    cm, stand = PEOPLE[who][1], PEOPLE[who][2]
    x, y = at_time(it["at"], t, it.get("ease", False))
    dy = at_time(it.get("dy", 0.0), t)
    h = cm * ppc(s, it.get("floor", y)) * it.get("scale", 1.0)               # plate px tall
    k = h * sc / stand * sheet_fac(key)                                      # screen px per sheet px
    fx, fy = feet_mid(key)
    Fx, Fy = M[0, 0] * x + M[0, 2], M[1, 1] * (y - dy) + M[1, 2]
    mir = at_time(it.get("mirror", False), t)
    sx = -k if mir else k
    th = math.radians(at_time(it.get("rot", 0.0), t))
    c, sn = math.cos(th), math.sin(th)
    A = np.array([[c * sx, -sn * k], [sn * sx, c * k]])
    off = np.array([Fx, Fy]) - A @ np.array([fx, fy])
    return np.hstack([A, off[:, None]]), mir, (Fx, Fy), h * sc


@functools.lru_cache(maxsize=64)
def prop_rgba(name):
    """a prop from the pack (library/props/hearn-white), upscaled 4x once (build/props/), premultiplied float"""
    out = BUILD / "props" / f"{name}.png"
    if not out.exists():
        from studio.film.art import upscale_rgba
        src = cv2.cvtColor(cv2.imread(str(LIBRARY / "props" / "hearn-white" / f"{name}.png"), cv2.IMREAD_UNCHANGED),
                           cv2.COLOR_BGRA2RGBA)
        out.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out), cv2.cvtColor(upscale_rgba(src), cv2.COLOR_RGBA2BGRA))
    im = cv2.cvtColor(cv2.imread(str(out), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA).astype(np.float32) / 255.0
    im[..., :3] *= im[..., 3:4]
    return im


def place_rgba(lay, im, A, clip_rows=None):
    """premultiplied RGBA image through A (image px -> screen px), over lay"""
    if clip_rows is not None:
        im = im.copy()
        yy = np.arange(im.shape[0], dtype=np.float32)[:, None]
        im *= np.clip(1 - (yy - clip_rows) / 6.0, 0, 1)[..., None]
    E.warp_into(lay, im, np.float32(A))


def draw_prop(lay, s, it, t, M, sc):
    im = prop_rgba(it["prop"])
    ih, iw = im.shape[:2]
    x, y = at_time(it["at"], t, it.get("ease", False))
    y = y - at_time(it.get("dy", 0.0), t)
    h = at_time(it["h"], t) * sc
    k = h / ih
    mir = it.get("mirror", False)
    sx = -k if mir else k
    th = math.radians(at_time(it.get("rot", 0.0), t))
    c, sn = math.cos(th), math.sin(th)
    A = np.array([[c * sx, -sn * k], [sn * sx, c * k]])
    piv = np.array([iw / 2, ih * it.get("pivot", 1.0)])
    S = np.array([M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]]) - np.array([0, h * (1 - it.get("pivot", 1.0))])
    off = S - A @ piv
    clip = None
    if it.get("clip") is not None:
        clip = (it["clip"] - (y - h / sc)) / (h / sc) * ih
    place_rgba(lay, im, np.hstack([A, off[:, None]]), clip)


def scene(img, s, t, M, sc):
    """("props", "scene"): everything in s["cast"] at time t, far to near"""
    from studio.film import render as R
    perf = importlib.import_module("film.perf")
    things = importlib.import_module("film.things")
    items = [it for it in s["cast"] if visible(it, t)]
    pos = {}
    for it in items:
        if "who" in it:
            x, y = at_time(it["at"], t, it.get("ease", False))
            h = PEOPLE[it["who"]][1] * ppc(s, y)
            pos[it["who"]] = (M[0, 0] * x + M[0, 2], M[1, 1] * (y - 0.93 * h) + M[1, 2])
    items.sort(key=lambda it: it.get("z", at_time(it["at"], t)[1] if "at" in it else 0.0))
    lay = np.zeros((OH, OW, 4), np.float32)
    for it in items:
        if "fn" in it:
            getattr(things, it["fn"])(lay, s, it, t, M, sc)
        elif "prop" in it:
            draw_prop(lay, s, it, t, M, sc)
        else:
            key = key_of(it["who"], pose_at(it, t))
            d, info = CAST.get(key)
            Ms, mir, F, Hs = person_matrix(s, it, key, t, M, sc)
            st = {}
            if d.has_face and not CAST.spec(key.split(":")[0])["drawings"][key.split(":")[1]].get("plain"):
                look = it.get("look")
                res = resolver(s, it["who"], pos)
                st = perf.PERF.state(it["who"], t, (lambda g, r=res, lk=look: r(lk if lk is not None else g)),
                                     s["t"])
                for kf in it.get("face", []):                    # this shot's own face: (t0, t1, brow, smile)
                    if kf[0] <= t < kf[1]:
                        st["brow"], st["smile"] = kf[2], kf[3]
                st = R.face_state(st, info, mir)
            clip = None
            cl = at_time(it.get("clip"), t)
            if cl is not None:                                     # plate y -> sheet y (no rotation assumed)
                cy_screen = M[1, 1] * cl + M[1, 2]
                clip = (cy_screen - Ms[1, 2]) / Ms[1, 1]
            if it.get("shadow", True) and cl is None:
                things.contact_shadow(lay, s, it, t, M, sc, F, Hs, at_time(it.get("dy", 0.0), t))
            E.place(lay, d, st, Ms, clip=clip, alpha=it.get("alpha", 1.0))
            for hd in it.get("holds", ()):                             # a prop in the hand: its grip at a sheet point
                if hd["t0"] <= t < hd["t1"]:
                    gx = Ms[0, 0] * hd["at"][0] + Ms[0, 1] * hd["at"][1] + Ms[0, 2]
                    gy = Ms[1, 0] * hd["at"][0] + Ms[1, 1] * hd["at"][1] + Ms[1, 2]
                    im = prop_rgba(hd["prop"])
                    k = hd["h"] * sc / im.shape[0]
                    gp = hd.get("grip", (0.5, 0.08))
                    th = math.radians(hd.get("rot", 0.0))
                    c, sn = math.cos(th), math.sin(th)
                    A = np.array([[c * k, -sn * k], [sn * k, c * k]])
                    off = np.array([gx, gy]) - A @ np.array([gp[0] * im.shape[1], gp[1] * im.shape[0]])
                    place_rgba(lay, im, np.hstack([A, off[:, None]]))
    return img * (1 - lay[..., 3:4]) + lay[..., :3]

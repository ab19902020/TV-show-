"""Noses for The Undercard. The pack draws the ring announcer with no nose at all, and Dana's nose as a soft skin
shape with a hair-thin line at its tip: at the size a face is on screen, both read as no nose. Here a cartoon nose is
inked into those drawings once, when a drawing is loaded, so it is part of the art: it moves, scales and is lit with
the face, and the eyes and mouths are animated over it.

The nose (in units of the eye distance u, from the tip's underside T):
  * a soft shadow under the tip and down the shaded side of the bridge, in the face's own skin darkened;
  * a highlight on the top of the tip;
  * the ink: the underside of the tip with a nostril wing curling up each side (the far wing smaller on a turned
    face), and one stroke down the bridge on the side the face turns to, fading out towards the eyes; in the
    drawing's own inner-line colour (taken from its mouth line), as thick as its other inner lines.

Where it goes: between the eyes and the mouth (68 % of the way down), over the mouth centre and pushed a little
further towards the side a turned face looks to; where the drawing has a dark tip line already, the drawn nose sits
on it. NOSE overrides it per drawing: (dx, dy, scale) in units of u.

install() hooks studio.film.cast.Cast.get (called once from film/actors.py)."""
import json
import math
from pathlib import Path

import cv2
import numpy as np

from studio.film import cast as C

WHO = {"dana-white", "ring-announcer"}
SKIP = set()                                            # drawings whose own nose reads (none so far)
NOSE = {                                                # per drawing: (dx, dy, scale) in eye distances
    "ring-announcer:mic": (0.0, 0.07, 1.0), "ring-announcer:mic_gesture": (0.0, 0.07, 1.0),
}
SS = 4
# drawings with no face marks (lying on the floor, climbing, walking, ducking): the nose placed by hand
# (film/nose_marks.json: {name: {tip: [x, y] sheet px, u: eye distance, turn: -1/0/1} or {skip: true}})
_NM = Path(__file__).with_name("nose_marks.json")
MARKED = {"dana-white": json.loads(_NM.read_text())} if _NM.exists() else {}


def _skin(img, a, x0, y0, x1, y1):
    sub, al = img[y0:y1, x0:x1, :3].reshape(-1, 3), a[y0:y1, x0:x1].reshape(-1)
    v = sub.max(1)
    ok = (al > 0.9) & (v > 0.45) & (sub[:, 0] > sub[:, 2])
    return np.median(sub[ok], 0) if ok.sum() > 20 else np.float32([0.93, 0.62, 0.48])


def _inkcol(img, mouth):
    xl, yl, xr, yr, xc, yc = mouth
    xs = np.linspace(xl, xr, 15)
    ys = np.interp(xs, [xl, xc, xr], [yl, yc, yr])
    H, W = img.shape[:2]
    pts = [img[int(np.clip(y + dy, 0, H - 1)), int(np.clip(x, 0, W - 1)), :3] for x, y in zip(xs, ys) for dy in (-2, -1, 0, 1, 2)]
    pts = np.float32(pts)
    v = pts.max(1)
    dark = pts[v <= np.percentile(v, 15)]
    c = dark.mean(0) if len(dark) else np.float32([0.18, 0.08, 0.07])
    return np.clip(c, 0, 0.35)


def geometry(d, faces, key):
    """-> tip (x, y) full-res px, u (eye distance px), turn (-1 left, 0 front, +1 right), line width px"""
    sp = d.spec
    eyes = [d.P(e[0], e[1]) for e in sp["eyes"]]
    if not eyes or not sp["mouth"]:
        return None
    m = sp["mouth"]
    (mxl, myl), (mxr, myr), (mxc, myc) = d.P(m[0], m[1]), d.P(m[2], m[3]), d.P(m[4], m[5])
    ex = float(np.mean([e[0] for e in eyes]))
    ey = float(np.mean([e[1] for e in eyes]))
    my = (myl + myr + myc) / 3
    if len(eyes) == 2:
        u = abs(eyes[1][0] - eyes[0][0])
    else:
        u = 1.6 * abs(mxr - mxl)
    u = max(u, 1.3 * abs(mxr - mxl))
    turn = {"L": -1, "R": 1}.get(faces, 0)
    tx = mxc + (0.12 * u * turn if turn else 0.0)
    ty = ey + 0.68 * (my - ey)
    # sit on the drawing's own tip line where it has one: the darkest short stroke in the window over the mouth
    img = d.u8[1.0].astype(np.float32) / 255
    H, W = img.shape[:2]
    x0, x1 = int(max(0, tx - 0.42 * u)), int(min(W, tx + 0.42 * u))
    y0, y1 = int(max(0, ey + 0.38 * (my - ey))), int(min(H, my - 0.16 * (my - ey)))
    if x1 > x0 + 4 and y1 > y0 + 4:
        sub = img[y0:y1, x0:x1]
        v = sub[..., :3].max(2)
        dark = (v < 0.40) & (sub[..., 3] > 0.9)
        if dark.sum() > 0.02 * u * u / 16:
            ys, xs = np.nonzero(dark)
            tx, ty = 0.5 * tx + 0.5 * (xs.mean() + x0), ys.max() + y0 - 0.02 * u
    dx, dy, sc = NOSE.get(key, (0.0, 0.0, 1.0))
    tx, ty, u = tx + dx * u, ty + dy * u, u * sc
    lw = max(1.6, 0.034 * u)
    return (tx, ty), u, turn, lw, ey


def _stroke(canvas, pts, w0, w1, off, val=1.0):
    """a tapered polyline (width w0 -> w1) on a supersampled float canvas"""
    pts = np.float32(pts)
    n = len(pts)
    for i in range(n - 1):
        w = w0 + (w1 - w0) * (i + 0.5) / (n - 1)
        a = tuple(int(round((p - o) * SS * 8)) for p, o in zip(pts[i], off))
        b = tuple(int(round((p - o) * SS * 8)) for p, o in zip(pts[i + 1], off))
        cv2.line(canvas, a, b, val, max(1, int(round(w * SS))), cv2.LINE_AA, 3)


def _curve(p0, p1, p2, n=10):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2 = (np.float32(p) for p in (p0, p1, p2))
    return (1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2


def marked(d, key):
    """the hand-placed nose of a drawing with no face marks -> geometry() tuple, or None"""
    cid, name = key.split(":")
    mk = MARKED.get(cid, {}).get(name)
    if not mk or mk.get("skip"):
        return None
    tx, ty = d.P(*mk["tip"])
    u = mk["u"] * d.S
    return (tx, ty), u, int(mk.get("turn", 0)), max(1.6, 0.034 * u), ty - 0.62 * u


def draw(full, d, faces, key, g=None):
    g = g or geometry(d, faces, key)
    if g is None:
        return full
    (tx, ty), u, turn, lw, ey = g
    bt = min(0.62 * u, 0.62 * (ty - ey))                      # the bridge stops short of the eyes
    img = full.astype(np.float32) / 255
    a = img[..., 3]
    H, W = img.shape[:2]
    x0, y0 = int(max(0, tx - 0.8 * u)), int(max(0, ty - 0.9 * u))
    x1, y1 = int(min(W, tx + 0.8 * u)), int(min(H, ty + 0.5 * u))
    if x1 <= x0 or y1 <= y0:
        return full
    skin = _skin(img, a, x0, y0, x1, y1)
    ink = _inkcol(img, [c for i in range(0, 6, 2) for c in d.P(d.spec["mouth"][i], d.spec["mouth"][i + 1])]) \
        if d.spec.get("mouth") else np.float32([0.16, 0.08, 0.07])
    hh, ww = (y1 - y0) * SS, (x1 - x0) * SS
    off = (x0, y0)
    yy, xx = np.mgrid[0:hh, 0:ww].astype(np.float32) / SS
    xx += x0
    yy += y0
    s = turn if turn else 1                                   # the shaded side of the bridge: away from the turn
    # shadow under the tip and down the shaded side
    sh = np.exp(-(((xx - tx) / (0.22 * u)) ** 2 + ((yy - (ty + 0.05 * u)) / (0.05 * u)) ** 2))
    side_x = tx + s * 0.17 * u
    band = np.exp(-((xx - side_x) / (0.07 * u)) ** 2) * np.clip((yy - (ty - bt)) / (0.7 * bt), 0, 1) \
        * (yy < ty + 0.02 * u)
    shadow = np.clip(0.30 * sh + 0.30 * band, 0, 0.4)
    hl = 0.35 * np.exp(-(((xx - (tx - s * 0.06 * u)) / (0.08 * u)) ** 2 + ((yy - (ty - 0.13 * u)) / (0.055 * u)) ** 2))
    # the ink: tip underside, the nostril wings, the bridge stroke
    canvas = np.zeros((hh, ww), np.float32)
    far = 0.55 if turn else 1.0
    wl, wr = (far, 1.0) if turn > 0 else ((1.0, far) if turn < 0 else (1.0, 1.0))
    bottom = _curve((tx - 0.15 * u * wl, ty - 0.035 * u), (tx, ty + 0.03 * u), (tx + 0.15 * u * wr, ty - 0.035 * u), 12)
    _stroke(canvas, bottom, lw * 0.9, lw * 0.9, off)
    for side, k in ((-1, wl), (1, wr)):
        wing = np.concatenate([
            _curve((tx + side * 0.15 * u * k, ty - 0.035 * u), (tx + side * 0.27 * u * k, ty + 0.01 * u),
                   (tx + side * 0.31 * u * k, ty - 0.07 * u), 8),
            _curve((tx + side * 0.31 * u * k, ty - 0.07 * u), (tx + side * 0.33 * u * k, ty - 0.14 * u),
                   (tx + side * 0.25 * u * k, ty - 0.17 * u), 8)])
        _stroke(canvas, wing, lw * 0.95, lw * 0.35, off)
    bridge = _curve((tx + s * 0.20 * u, ty - 0.32 * bt), (tx + s * 0.24 * u, ty - 0.68 * bt),
                    (tx + s * 0.13 * u, ty - bt), 10)
    bc = np.zeros_like(canvas)
    _stroke(bc, bridge, lw * 0.75, lw * 0.25, off)
    fade = np.clip((yy - (ty - 1.05 * bt)) / (0.65 * bt), 0, 1)
    canvas = np.maximum(canvas, bc * fade * 0.8)
    v, mn = img[y0:y1, x0:x1, :3].max(2), img[y0:y1, x0:x1, :3].min(2)
    white = cv2.dilate(((v > 0.80) & (v - mn < 0.18)).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0   # eye whites
    ok = (a[y0:y1, x0:x1] > 0.9) & ~white
    inside = cv2.resize(ok.astype(np.uint8), (ww, hh), interpolation=cv2.INTER_NEAREST) > 0
    sub = cv2.resize(img[y0:y1, x0:x1, :3], (ww, hh), interpolation=cv2.INTER_LINEAR)
    shadow_col = skin * np.float32([0.86, 0.74, 0.70])
    out = sub * (1 - shadow[..., None]) + shadow_col * shadow[..., None]
    out = out + (np.float32([1.0, 0.92, 0.85]) - out) * hl[..., None]
    out = out * (1 - canvas[..., None]) + ink * canvas[..., None]
    out = np.where(inside[..., None], out, sub)
    small = cv2.resize(out, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    res = full.copy()
    res[y0:y1, x0:x1, :3] = (np.clip(small, 0, 1) * 255).astype(np.uint8)
    return res


def install():
    if getattr(C.Cast, "_noses", False):
        return
    orig = C.Cast.get

    def get(self, key):
        fresh = key not in self.d
        d, info = orig(self, key)
        hand = marked(d, key) if fresh and key.split(":")[0] in WHO else None
        if fresh and key.split(":")[0] in WHO and key not in SKIP and (hand or (d.spec.get("mouth") and d.spec.get("eyes")
                and not key.split(":")[1].startswith(("bust_", "pair_")))):    # the busts and pairs draw their own
            from studio.film.engine import LEVELS
            full = draw(d.u8[1.0], d, info.get("faces", "F"), key, hand)
            d.u8 = {1.0: full}
            for L in LEVELS[1:]:
                d.u8[L] = cv2.resize(full, None, fx=L, fy=L, interpolation=cv2.INTER_AREA)
            d._base, d._face, d._patch = {}, {}, {}
        return d, info

    C.Cast.get = get
    C.Cast._noses = True

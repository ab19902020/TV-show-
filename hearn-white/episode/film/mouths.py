"""Drawn mouths for The Undercard, cartoon-show style: the engine's lip sync picks the mouth shape (a viseme) for every
frame from the recordings; here each open shape is drawn on the character's own mouth, in the art's look (the
drawing's own ink for a bold outline, a dark mouth, teeth, a tongue), placed and angled by the drawing's marked mouth
corners. The engine's own method (dropping the jaw by warping the chin and painting a hole) smeared beards and,
on a mis-marked drawing, opened a hole in a cheek; nothing is warped here.

  * rest and M / B / P: the drawing's own closed mouth, untouched
  * any open shape: the drawn mouth line is painted out (inpainted from the skin or beard round it) and the shape is
    drawn over it, its height following the loudness of the voice
  * blinks, gaze and brows are the engine's, unchanged

install() swaps this in for studio.film.face.Face.render (called once from film/actors.py)."""
import math

import cv2
import numpy as np

from studio.film import face as F

# viseme -> (width, open height, top teeth, bottom teeth, tongue, shape) in mouth widths; shape D = flat top lip,
# round jaw; O = oval
SHAPES = {
    "AI": (1.00, 0.60, 1.0, 0.0, 1.0, "D"),
    "E": (1.06, 0.36, 1.0, 0.7, 0.4, "D"),
    "I": (1.04, 0.24, 1.0, 1.0, 0.0, "D"),
    "O": (0.70, 0.56, 0.5, 0.0, 0.8, "O"),
    "U": (0.56, 0.38, 0.0, 0.0, 0.3, "O"),
    "FV": (0.90, 0.22, 1.0, 0.0, 0.0, "F"),
    "L": (0.86, 0.44, 1.0, 0.0, 1.0, "L"),
    "CDG": (0.94, 0.28, 1.0, 0.8, 0.2, "D"),
    "R": (0.70, 0.36, 0.6, 0.0, 0.4, "O"),
    "BREATH": (0.64, 0.12, 0.0, 0.0, 0.0, "O"),
}
DARK_T = np.float32([0.17, 0.02, 0.03])
DARK_B = np.float32([0.36, 0.07, 0.08])
TEETH = np.float32([0.98, 0.97, 0.93])
TONGUE = np.float32([0.86, 0.37, 0.40])
SS = 4                                              # supersampling of the drawn shape


def _contour(W, H, shape):
    u = np.linspace(-W / 2, W / 2, 40)
    k = np.clip(1 - (2 * u / W) ** 2, 0, 1)
    if shape == "O":
        top = -0.42 * H * np.sqrt(k)
        bot = 0.58 * H * np.sqrt(k)
    else:                                            # D, F, L: the upper lip nearly straight, the jaw round
        top = -0.10 * H * k
        bot = H * k ** 0.6
    return u, top, bot


def _shape_rgba(W, H, shape, tt, tb, tg, lw, ink):
    """the mouth drawn in its own frame (u along the lips, v down), supersampled -> premultiplied RGBA, origin"""
    pad = lw * 2 + 2
    u0, v0 = -W / 2 - pad, -0.5 * H - pad
    cw, ch = int((W + 2 * pad) * SS) + 2, int((1.6 * H + 2 * pad) * SS) + 2

    def P(uu, vv):
        return np.int32(np.round(np.stack([(uu - u0) * SS, (vv - v0) * SS], 1) * 8))

    u, top, bot = _contour(W, H, shape)
    poly = np.concatenate([P(u, top), P(u[::-1], bot[::-1])])
    inside = np.zeros((ch, cw), np.uint8)
    cv2.fillPoly(inside, [poly], 255, cv2.LINE_AA, 3)
    m = inside.astype(np.float32) / 255
    yy = (np.arange(ch, dtype=np.float32)[:, None] / SS + v0)
    depth = np.clip((yy + 0.1 * H) / max(1.0, 1.1 * H), 0, 1)[..., None]
    col = np.broadcast_to(DARK_T * (1 - depth) + DARK_B * depth, (ch, cw, 3)).copy()
    xx = (np.arange(cw, dtype=np.float32)[None, :] / SS + u0)
    if tg > 0 and shape != "F":                     # the tongue: a mound at the bottom (raised at the front for L)
        ty = 0.25 * H if shape == "L" else (0.72 * H if shape == "D" else 0.40 * H)
        r = ((xx / (0.33 * W)) ** 2 + ((yy - ty) / (0.34 * H)) ** 2)
        tm = np.clip((1 - r) * 3, 0, 1)[..., None] * tg
        col = col * (1 - tm) + TONGUE * tm
    if tt > 0:                                      # the top teeth hang from the upper lip
        depth_t = (0.62 if shape == "F" else 0.26) * H * tt
        topv = np.interp(xx[0], u, top)[None, :]
        tm = ((yy - topv) < depth_t) & (np.abs(xx) < (0.44 if shape != "O" else 0.32) * W)
        tm = cv2.GaussianBlur(tm.astype(np.float32), (0, 0), 0.6 * SS)[..., None] * tt
        sh = np.clip((yy - topv) / max(1e-3, depth_t), 0, 1)[..., None]
        col = col * (1 - tm) + TEETH * (1 - 0.10 * sh) * tm
    if tb > 0 and shape == "D":                     # the bottom teeth sit on the lower lip
        botv = np.interp(xx[0], u, bot)[None, :]
        tm = ((botv - yy) < 0.20 * H * tb) & (np.abs(xx) < 0.30 * W)
        tm = cv2.GaussianBlur(tm.astype(np.float32), (0, 0), 0.6 * SS)[..., None] * tb
        col = col * (1 - tm) + TEETH * 0.92 * tm
    rgba = np.dstack([col * m[..., None], m])
    edge = np.zeros((ch, cw), np.uint8)
    cv2.polylines(edge, [poly], True, 255, max(1, int(round(lw * SS))), cv2.LINE_AA, 3)
    e = edge.astype(np.float32)[..., None] / 255
    rgba = np.dstack([rgba[..., :3] * (1 - e) + np.float32(ink) * e, np.maximum(m, e[..., 0])])
    small = cv2.resize(rgba, (cw // SS, ch // SS), interpolation=cv2.INTER_AREA)
    return small, (u0, v0)


def _nomouth(self):
    """the face with its drawn mouth line painted out (from the skin / beard round it), made once"""
    if getattr(self, "_nm", None) is not None:
        return self._nm
    xl, yl, xr, yr, xc, yc = self.mouth
    mw = math.hypot(xr - xl, yr - yl)
    ext = 0.10 * mw
    dx, dy = (xr - xl) / max(1e-6, mw), (yr - yl) / max(1e-6, mw)
    X = np.linspace(xl - ext * dx, xr + ext * dx, 24)
    Y = self._lipline(X.astype(np.float32))
    rgb = (np.clip(self.img[..., :3], 0, 1) * 255).astype(np.uint8)
    msk = np.zeros(rgb.shape[:2], np.uint8)
    cv2.polylines(msk, [np.int32(np.stack([X, Y], 1))], False, 255, max(3, int(0.20 * mw)), cv2.LINE_AA)
    msk = cv2.dilate(msk, np.ones((3, 3), np.uint8))
    fill = cv2.inpaint(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), msk, max(3, int(0.12 * mw)), cv2.INPAINT_TELEA)
    nm = self.img.copy()
    nm[..., :3] = cv2.cvtColor(fill, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    self._nm = nm
    self._fm = _facemask(self, nm, mw, xc, yc)
    return nm


def _facemask(self, nm, mw, xc, yc):
    """where a mouth may be drawn: the face round the mouth, inside its ink outline. A glove held up to the chin, a
    hand or a microphone is outlined in ink too, so it falls outside; the mouth is clipped to the face and never
    drawn over them. None (no clipping) if the region found is too small to be the face."""
    h, w = nm.shape[:2]
    R = int(3.2 * mw) + 4
    x0, y0, x1, y1 = max(0, int(xc) - R), max(0, int(yc) - R), min(w, int(xc) + R), min(h, int(yc) + R)
    sub = nm[y0:y1, x0:x1]
    v = sub[..., :3].max(2)
    free = ((v >= 0.17) & (sub[..., 3] > 0.5)).astype(np.uint8)
    n, lab = cv2.connectedComponents(free, connectivity=4)
    cx, cy = int(round(xc)) - x0, int(round(yc)) - y0
    if not (0 <= cx < lab.shape[1] and 0 <= cy < lab.shape[0]):
        return None
    k = lab[cy, cx]
    if k == 0:                                   # on a dark pixel (beard, shadow): the biggest region close by
        win = lab[max(0, cy - 3):cy + 4, max(0, cx - 3):cx + 4]
        ks, cs = np.unique(win[win > 0], return_counts=True)
        if len(ks) == 0:
            return None
        k = ks[np.argmax(cs)]
    reg = (lab == k).astype(np.uint8)
    if reg.sum() < 2.0 * mw * mw:
        return None
    reg = cv2.dilate(reg, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    full = np.zeros((h, w), np.float32)
    full[y0:y1, x0:x1] = cv2.GaussianBlur(reg.astype(np.float32), (0, 0), 0.7)
    full[:y0] = full[y1:] = 0
    return full


def _draw(self, img, vis, amp, smile):
    W0, H0, tt, tb, tg, shape = SHAPES[vis]
    xl, yl, xr, yr, xc, yc = self.mouth
    mw = math.hypot(xr - xl, yr - yl)
    th = math.atan2(yr - yl, xr - xl)
    mx, my = (xl + xr) / 2, (yl + yr) / 2
    nx, ny = -math.sin(th), math.cos(th)
    off = 0.5 * ((xc - mx) * nx + (yc - my) * ny)
    cx, cy = mx + off * nx, my + off * ny
    a = float(np.clip(amp, 0.5, 1.2))
    W = W0 * mw * (1 + 0.03 * smile)
    H = H0 * mw * (0.55 + 0.45 * a) * getattr(self, "jaw", 1.0) ** 0.5
    lw = max(1.4, 0.075 * mw)
    rgba, (u0, v0) = _shape_rgba(W, H, shape, tt, tb, tg, lw, self.ink)
    c, s = math.cos(th), math.sin(th)
    # shape px (p, q) -> image: u = p + u0, v = q + v0; x = cx + u c - v s, y = cy + u s + v c
    A = np.float32([[c, -s, cx + u0 * c - v0 * s], [s, c, cy + u0 * s + v0 * c]])
    h, w = img.shape[:2]
    lay = cv2.warpAffine(rgba, A, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    al = lay[..., 3:4] * (img[..., 3:4] > 0.5)
    fm = getattr(self, "_fm", None)
    if fm is not None and fm.shape == al.shape[:2]:
        al = al * fm[..., None]
    out = img.copy()
    out[..., :3] = out[..., :3] * (1 - al) + lay[..., :3] * (al / np.maximum(lay[..., 3:4], 1e-4))
    return out


def install():
    if getattr(F.Face, "_drawn_mouths", False):
        return
    orig = F.Face.render

    def render(self, vis="REST", amp=1.0, blink=0.0, look=(0.0, 0.0), brow=0.0, smile=0.0):
        if not self.mouth or vis not in SHAPES:
            return orig(self, "REST", amp, blink, look, brow, smile)
        img0 = self.img
        self.img = _nomouth(self)
        try:
            res = orig(self, "REST", amp, blink, look, brow, 0.0)
        finally:
            self.img = img0
        return _draw(self, res, vis, amp, smile)

    F.Face.render = render
    F.Face._drawn_mouths = True

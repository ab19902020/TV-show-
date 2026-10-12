"""Clean moving pupils for The Undercard. The engine's gaze lifted the drawn pupil out by a darkness threshold and
pasted it elsewhere; its anti-aliased rim and any bit of eye outline or lash it caught stayed behind or travelled with
it (the "black bits" in the eyes). Here, once per eye:

  * the eye white is found from the art (the bright, colourless pixels round the marked eye), and its convex hull
    is the eye opening the pupil may move in;
  * the drawn pupil (every dark pixel inside the opening, rim included) is painted out with the colour of the
    nearest eye-white pixel, so the white keeps its own shading;
  * a new pupil is drawn: a round disc in the art's ink, the size of the drawn one, with a white highlight.

At rest (looking where the drawing looks) the eye is left exactly as drawn; a look moves the new pupil from the drawn
pupil's place, never out of the opening. Eyes where no clean white and pupil are found (a far eye drawn as a dark
sliver) keep their drawing and only blink.

install() swaps these in for studio.film.face.Face._find_pupil / _pupils (called once from film/actors.py)."""
import cv2
import numpy as np
from scipy import ndimage

from studio.film import face as F

SS = 4


def _find(self, e):
    cx, cy, rx, ry = e
    H, W = self.img.shape[:2]
    pad = 1.7
    x0, x1 = int(max(0, cx - pad * rx - 2)), int(min(W, cx + pad * rx + 3))
    y0, y1 = int(max(0, cy - pad * ry - 2)), int(min(H, cy + pad * ry + 3))
    if x1 - x0 < 6 or y1 - y0 < 6:
        return dict(skip=True)
    sub = self.img[y0:y1, x0:x1]
    rgb, a = sub[..., :3], sub[..., 3]
    v, mn = rgb.max(2), rgb.min(2)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    ell = ((xx - cx) / (rx * 1.35)) ** 2 + ((yy - cy) / (ry * 1.35)) ** 2 <= 1
    core = ((xx - cx) / max(1.0, rx)) ** 2 + ((yy - cy) / max(1.0, ry)) ** 2 <= 1
    white = ((v > 0.72) & (v - mn < 0.20) & (a > 0.9) & ell).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(white, 8)
    best, area = 0, 0
    for i in range(1, n):
        if (core & (lab == i)).any() and st[i, 4] > area:
            best, area = i, st[i, 4]
    if area < 20:
        return dict(skip=True)
    wm = (lab == best).astype(np.uint8)
    hull = cv2.convexHull(cv2.findNonZero(wm))
    R = np.zeros_like(wm)
    cv2.fillConvexPoly(R, hull, 1)
    R = cv2.erode(R, np.ones((3, 3), np.uint8))
    dark = (v < 0.62) & (R > 0) & (a > 0.5)
    lab2, n2 = ndimage.label(dark)
    if n2 == 0:
        return dict(skip=True)
    sizes = ndimage.sum(dark, lab2, range(1, n2 + 1))
    k = 1 + int(np.argmax(sizes))
    pm = lab2 == k
    if pm.sum() < 6 or pm.sum() > 0.85 * R.sum():
        return dict(skip=True)
    ys, xs = np.nonzero(pm)
    px, py = xs.mean() + x0, ys.mean() + y0
    pr = max(np.sqrt(pm.sum() / np.pi), 0.5 * min(np.ptp(xs) + 1, np.ptp(ys) + 1))
    Rys, Rxs = np.nonzero(R)
    pr = float(min(pr, 0.46 * min(np.ptp(Rxs) + 1, np.ptp(Rys) + 1)))
    # the opening without its pupil: every dark pixel in it takes the colour of the nearest eye-white pixel
    paint = cv2.dilate(dark.astype(np.uint8), np.ones((3, 3), np.uint8)) & R
    _, (iy, ix) = ndimage.distance_transform_edt(wm == 0, return_indices=True)
    clean = sub.copy()
    pmask = paint > 0
    clean[..., :3][pmask] = rgb[iy[pmask], ix[pmask]]
    # where the new pupil's centre may go: inside the opening, a pupil's width from its edge
    allow = cv2.erode(R, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(1, int(1.3 * pr)) | 1,) * 2))
    if allow.sum() == 0:
        allow = R.copy()
    _, (ay, ax) = ndimage.distance_transform_edt(allow == 0, return_indices=True)
    # the new pupil, supersampled: ink disc + highlight (premultiplied RGBA), centred in its sprite
    s = int(np.ceil(pr + 2))
    sz = 2 * s + 1
    big = np.zeros((sz * SS, sz * SS, 4), np.float32)
    c = (s + 0.5) * SS
    ink = np.float32(self.ink) * 0.6
    cv2.circle(big, (int(c * 8), int(c * 8)), int(pr * SS * 8), tuple(float(q) for q in ink) + (1.0,), -1, cv2.LINE_AA, 3)
    hr = max(0.9, 0.28 * pr)
    hc = (c - 0.38 * pr * SS, c - 0.40 * pr * SS)
    cv2.circle(big, (int(hc[0] * 8), int(hc[1] * 8)), int(hr * SS * 8), (1.0, 1.0, 1.0, 1.0), -1, cv2.LINE_AA, 3)
    spr = cv2.resize(big, (sz, sz), interpolation=cv2.INTER_AREA)
    spr[..., :3] *= spr[..., 3:4]
    Rf = cv2.GaussianBlur(R.astype(np.float32), (0, 0), 0.6)
    span = (max(0.0, (np.ptp(Rxs) + 1) / 2 - pr) * 0.85, max(0.0, (np.ptp(Rys) + 1) / 2 - pr) * 0.6)
    return dict(skip=False, box=(x0, y0, x1, y1), R=Rf, paint=pmask, clean=clean, px=px, py=py, pr=pr, span=span,
                ax=ax, ay=ay, allow=allow, sprite=spr, s=s)


def _pupils(self, img, look):
    lx, ly = float(np.clip(look[0], -1.2, 1.2)), float(np.clip(look[1], -1.0, 1.0))
    for p in self.pupils:
        if not p or p.get("skip"):
            continue
        dx, dy = lx * p["span"][0], ly * p["span"][1]
        if abs(dx) < 0.5 and abs(dy) < 0.5:
            continue                                    # where the drawing looks: the eye as drawn
        x0, y0, x1, y1 = p["box"]
        tx, ty = p["px"] + dx - x0, p["py"] + dy - y0
        ix, iy = int(round(np.clip(tx, 0, x1 - x0 - 1))), int(round(np.clip(ty, 0, y1 - y0 - 1)))
        if not p["allow"][iy, ix]:                       # keep the pupil inside the opening
            tx, ty = float(p["ax"][iy, ix]), float(p["ay"][iy, ix])
        reg = img[y0:y1, x0:x1]
        out = reg.copy()
        out[..., :3][p["paint"]] = p["clean"][..., :3][p["paint"]]
        s = p["s"]
        A = np.float32([[1, 0, tx - s], [0, 1, ty - s]])
        sp = cv2.warpAffine(p["sprite"], A, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderValue=0)
        al = sp[..., 3:4] * p["R"][..., None]
        out[..., :3] = out[..., :3] * (1 - al) + sp[..., :3] * p["R"][..., None]
        img[y0:y1, x0:x1] = out
    return img


def install():
    if getattr(F.Face, "_clean_eyes", False):
        return
    F.Face._find_pupil = _find
    F.Face._pupils = _pupils
    F.Face._clean_eyes = True

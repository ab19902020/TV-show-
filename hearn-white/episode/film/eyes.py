"""Clean moving pupils for The Undercard: when an eye looks somewhere other than where it was drawn looking, the drawn
pupil is painted out completely and one round pupil is drawn where the look puts it. Nothing of the old pupil may be
left (no black bits in the corners), and there is only ever one pupil.

The pack draws most pupils off-centre, many of them pressed into the corner of the eye and merged with the eye's ink
outline (a character looking sideways), so a pupil cannot be found as "the dark pixels inside the white". Once per
eye:

  * the eye white: every bright, colourless region touching the marked eye (a pupil in the middle can split it);
  * the drawn pupil: the fattest dark blob that the white wraps round. Every dark pixel is scored by the largest
    disc that fits in the dark there and by how much of the ring just outside that disc is eye white: a pupil is
    fat and white-rimmed; the outline is thin, the brow and a heavy upper lid are rimmed by skin. The pupil is then
    the dark round that disc (its highlight included), grown back over its anti-aliased rim;
  * the eye opening: the convex hull of the white and the pupil's disc. Everything in it that is not clean eye white
    (the pupil, and the black wedges many of the pack's eyes have drawn in their corners) is painted out, short of
    the outline by half the outline's width so the outline stays, with the white's own shading: a smooth average
    of the clean white round it (no streaks pulled from grey edge pixels);
  * the new pupil: an ink disc the size of the drawn one with a highlight, kept inside the opening and clipped to
    it, so at the edges it tucks under the lids.

An eye drawn mostly dark (a far eye in shadow, a squint) or with no clear pupil keeps its drawing and only blinks.
Every animated eye shows the redrawn pupil all the time (at rest it sits where the drawn one was), so an eye never
pops between the drawing and the redraw.

install() swaps these in for studio.film.face.Face._find_pupil / _pupils (called once from film/actors.py)."""
import cv2
import numpy as np
from scipy import ndimage

from studio.film import face as F

SS = 4
SKIP = dict(skip=True)
STATS = {}


def _disc(shape, cx, cy, r):
    yy, xx = np.mgrid[0:shape[0], 0:shape[1]]
    return (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r


def _find(self, e):
    cx, cy, rx, ry = e
    H, W = self.img.shape[:2]
    R0 = 2.0 * max(rx, ry) + 8
    x0, x1 = int(max(0, cx - R0)), int(min(W, cx + R0 + 1))
    y0, y1 = int(max(0, cy - R0)), int(min(H, cy + R0 + 1))
    if x1 - x0 < 10 or y1 - y0 < 10:
        return SKIP
    sub = self.img[y0:y1, x0:x1]
    rgb, a = sub[..., :3], sub[..., 3]
    v, mn = rgb.max(2), rgb.min(2)
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    ell = ((xx - cx) / (1.5 * rx + 4)) ** 2 + ((yy - cy) / (1.5 * ry + 4)) ** 2 <= 1
    core = ((xx - cx) / (rx + 3)) ** 2 + ((yy - cy) / (ry + 3)) ** 2 <= 1

    # the eye white (all of it: a pupil in the middle splits it in two)
    white = (v > 0.70) & (v - mn < 0.22) & (a > 0.9)
    n, lab, st, _ = cv2.connectedComponentsWithStats(white.astype(np.uint8), connectivity=8)
    keep = []
    for i in range(1, n):
        m = lab == i
        if st[i, 4] < 6 or not (core & m).any() or not (ell[m].mean() > 0.6):
            continue
        if (v[m] > 0.85).mean() < 0.5:                      # grey hair, a shirt collar: not an eye white
            continue
        keep.append(i)
    if not keep:
        return SKIP
    near = ((xx - cx) / (1.35 * rx + 3)) ** 2 + ((yy - cy) / (1.35 * ry + 3)) ** 2 <= 1
    Wm = np.isin(lab, keep) & near                      # (a white cuff or a shirt beside the eye is not the eye)
    if Wm.sum() < 30:
        return SKIP

    # the dark, with the pupil's highlights filled in (small bright holes)
    D = (v < 0.45) & (a > 0.5)
    holes = ndimage.binary_fill_holes(D) & ~D
    hl, hn = ndimage.label(holes)
    Df = D.copy()
    if hn:
        sizes = ndimage.sum(np.ones_like(hl), hl, range(1, hn + 1))
        means = ndimage.mean(v, hl, range(1, hn + 1))
        for k in range(hn):
            if sizes[k] < 0.10 * Wm.sum() and means[k] > 0.7:
                Df |= hl == k + 1
    dt = ndimage.distance_transform_edt(Df)
    dW = ndimage.distance_transform_edt(~Wm)

    # the pupil: the biggest dark shape inside the white's outline (a pupil in a corner sits in a bay of the white);
    # if there is none, the fattest dark disc rimmed by eye white
    HW = np.zeros(Wm.shape, np.uint8)
    cv2.fillConvexPoly(HW, cv2.convexHull(cv2.findNonZero(Wm.astype(np.uint8))), 1)
    rim = (cv2.dilate(Wm.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & D
    t0 = float(np.clip(2 * np.median(dt[rim]) if rim.any() else 3.0, 2.0, 0.5 * min(rx, ry) + 2))
    ke = int(round(0.5 * t0 + 1))
    HWe = cv2.erode(HW, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ke + 1,) * 2)) > 0   # inside the outline
    HW = cv2.dilate(HW, np.ones((3, 3), np.uint8)) > 0
    il, inn = ndimage.label(Df & HWe)
    best = None
    if inn:
        kr = max(3, int(0.25 * min(rx, ry))) | 1
        Hd = cv2.dilate(HW.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * kr + 1,) * 2)) > 0
        dtd = ndimage.distance_transform_edt(Df & Hd)
        ang = np.linspace(0, 2 * np.pi, 28, endpoint=False)
        top = -1.0
        for kb in range(1, inn + 1):
            m = il == kb
            if m.sum() < 6:
                continue
            comp = cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            dtc = dtd * comp
            iy, ix = np.unravel_index(int(np.argmax(dtc)), dtc.shape)
            ri = float(dtc[iy, ix])
            if ri < 1.5:
                continue
            ry_ = np.clip(np.round(iy + (ri + 2.5) * np.sin(ang)).astype(int), 0, Wm.shape[0] - 1)
            rx_ = np.clip(np.round(ix + (ri + 2.5) * np.cos(ang)).astype(int), 0, Wm.shape[1] - 1)
            sc_ = ri * (0.5 + Wm[ry_, rx_].mean())
            if sc_ > top:
                top, best = sc_, (int(iy), int(ix), ri)
    cand = (dt >= 2) & ell & (dW <= dt + 3)
    ys, xs = np.nonzero(cand)
    if len(ys) == 0:
        return SKIP
    r = dt[ys, xs]
    ang = np.linspace(0, 2 * np.pi, 28, endpoint=False)
    rr = r[:, None] + 2.5
    sy = np.clip(np.round(ys[:, None] + rr * np.sin(ang)[None]).astype(int), 0, Wm.shape[0] - 1)
    sx = np.clip(np.round(xs[:, None] + rr * np.cos(ang)[None]).astype(int), 0, Wm.shape[1] - 1)
    frac = Wm[sy, sx].mean(1)
    far = np.hypot((xs + x0 - cx) / (rx + 1), (ys + y0 - cy) / (ry + 1))
    score = np.where(frac >= 0.25, r * frac / (1 + 0.15 * far), -1)
    k = int(np.argmax(score))
    if best is not None:
        py, px, pr0 = best
    elif score[k] > 0:                                  # a pupil pressed wholly into the corner, outside the white
        py, px, pr0 = int(ys[k]), int(xs[k]), float(r[k])
    else:
        return SKIP

    # the drawn pupil: its fat body (connected to the disc), grown back over its rim
    body = Df & (dt >= 0.4 * pr0) & _disc(Df.shape, px, py, 1.8 * pr0 + 2)
    bl, _ = ndimage.label(body)
    body = bl == bl[py, px]
    grow = cv2.dilate(body.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE,
                      (2 * int(0.4 * pr0 + 2) + 1,) * 2)) > 0
    Pm = grow & (((v < 0.80) & (a > 0.5)) | Df)

    # the outline's width: twice the dark's depth just outside the white, away from the pupil
    ring = (cv2.dilate(Wm.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & D & ~grow
    t = float(np.clip(2 * np.median(dt[ring]) if ring.any() else 0.3 * pr0, 2.0, 0.8 * pr0 + 1))

    # the opening, and the paint: the pupil inside it, short of the outline
    hull_pts = np.concatenate([cv2.findNonZero(Wm.astype(np.uint8)).reshape(-1, 2),
                               cv2.findNonZero(_disc(Df.shape, px, py, 1.05 * pr0).astype(np.uint8)).reshape(-1, 2)])
    Hm = np.zeros(Wm.shape, np.uint8)
    cv2.fillConvexPoly(Hm, cv2.convexHull(hull_pts), 1)
    STATS[id(self), round(cx), round(cy)] = dict(white_ell=float(Wm.sum() / (np.pi * rx * ry)),
                                                 white_hull=float(Wm.sum() / max(1, Hm.sum())), pr0=pr0)
    if Wm.sum() < 0.42 * Hm.sum():                      # an eye drawn mostly dark: keep it as drawn
        return dict(skip=True, why="dark")
    e_px = max(1, int(round(0.5 * t)))
    inner = cv2.erode(Hm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * e_px + 1,) * 2)) > 0
    # everything inside the opening that is not clean eye white goes: the pupil, and the dark wedges the pack's
    # drawings put in the corners of many eyes (a lid shadow drawn as a black blob)
    darkaa = (cv2.dilate(D.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & (v < 0.85)
    paint = (Pm | darkaa) & inner & near
    if paint.sum() < 4:
        return SKIP
    # the paint's edge: soft against the white, hard (no grey seam) against the outline it stops short of
    pa = cv2.GaussianBlur(paint.astype(np.float32), (0, 0), 0.8)
    pa = np.where(paint, 1.0, np.clip(pa * 1.4, 0, 1)) * (cv2.dilate(inner.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
    pa = pa.astype(np.float32)

    # the white's own shading over the painted pupil: a smooth average of the clean white round it
    Sm = ((v > 0.85) & (v - mn < 0.15) & (a > 0.9) & (Hm > 0)).astype(np.float32)
    sig = max(2.0, 0.7 * pr0)
    num = cv2.GaussianBlur(rgb * Sm[..., None], (0, 0), sig)
    den = cv2.GaussianBlur(Sm, (0, 0), sig)[..., None]
    base = np.median(rgb[Sm > 0], 0) if Sm.sum() > 0 else np.float32([0.97, 0.97, 0.97])
    fill = np.where(den > 0.02, num / np.maximum(den, 1e-4), base).astype(np.float32)
    clean = sub.copy()
    clean[..., :3] = fill

    # the opening the new pupil lives in (the white once the pupil is gone), and where its centre may go
    Ro = ((Wm | paint) & (Hm > 0)).astype(np.uint8)
    Ro = cv2.morphologyEx(Ro, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    Rys, Rxs = np.nonzero(Ro)
    if len(Rys) < 20:
        return SKIP
    STATS[id(self), round(cx), round(cy)]["pupil_ratio"] = float((Pm & inner).sum() / max(1, Ro.sum()))
    if (Pm & inner).sum() > 0.55 * Ro.sum():             # an eye drawn almost all pupil: keep it as drawn
        return dict(skip=True, why="pupil")
    ext = min(np.ptp(Rxs) + 1, np.ptp(Rys) + 1)
    area_r = np.sqrt((Pm & (Hm > 0)).sum() / np.pi)
    pr = float(np.clip(area_r, 0.9 * pr0, 1.3 * pr0 + 1))
    pr = float(min(pr, 0.48 * ext))
    allow = cv2.erode(Ro, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(1, int(1.2 * pr)) | 1,) * 2))
    if allow.sum() == 0:
        allow = Ro.copy()
    _, (ay, ax) = ndimage.distance_transform_edt(allow == 0, return_indices=True)
    Rf = cv2.GaussianBlur(Ro.astype(np.float32), (0, 0), 0.7)

    s, spr = _sprite(pr, self.ink)
    span = (max(0.0, (np.ptp(Rxs) + 1) / 2 - pr) * 0.85, max(0.0, (np.ptp(Rys) + 1) / 2 - pr) * 0.6)
    return dict(skip=False, box=(x0, y0, x1, y1), R=Rf, pa=pa, clean=clean, px=px + x0, py=py + y0, pr=pr,
                span=span, ax=ax, ay=ay, allow=allow, sprite=spr, s=s, size=float(np.sqrt(Ro.sum())),
                prmax=float(0.48 * ext), Ro=Ro)


def _sprite(pr, ink):
    """the new pupil: an ink disc and a highlight, supersampled (premultiplied RGBA), centred in its sprite"""
    s = int(np.ceil(pr + 2))
    sz = 2 * s + 1
    big = np.zeros((sz * SS, sz * SS, 4), np.float32)
    c = (s + 0.5) * SS
    ink = np.float32(ink) * 0.6
    cv2.circle(big, (int(c * 8), int(c * 8)), int(pr * SS * 8), tuple(float(q) for q in ink) + (1.0,), -1, cv2.LINE_AA, 3)
    hr = max(0.9, 0.26 * pr)
    hc = (c - 0.36 * pr * SS, c - 0.38 * pr * SS)
    cv2.circle(big, (int(hc[0] * 8), int(hc[1] * 8)), int(hr * SS * 8), (1.0, 1.0, 1.0, 1.0), -1, cv2.LINE_AA, 3)
    spr = cv2.resize(big, (sz, sz), interpolation=cv2.INTER_AREA)
    spr[..., :3] *= spr[..., 3:4]
    return s, spr


def _match(self):
    """one face, one pupil size: the two pupils are sized alike for their eyes (the pack sometimes draws one pupil
    half the size of the other), the smaller brought up to the larger's share of its eye. The far eye of a
    three-quarter face (marked at under half its partner's size: a dark sliver past the nose) keeps its drawing."""
    if len(self.eyes) == 2:
        a0, a1 = (e[2] * e[3] for e in self.eyes)
        for i, (ai, aj) in enumerate(((a0, a1), (a1, a0))):
            if ai < 0.45 * aj and self.pupils[i] and not self.pupils[i].get("skip"):
                self.pupils[i] = dict(skip=True, why="far")
    ps = [p for p in self.pupils if p and not p.get("skip")]
    if len(ps) < 2:
        return
    k = max(p["pr"] / max(1.0, p["size"]) for p in ps)
    for p in ps:
        pr = min(p["prmax"], k * p["size"])
        if pr > p["pr"] * 1.12:
            p["pr"] = pr
            p["s"], p["sprite"] = _sprite(pr, self.ink)
            allow = cv2.erode(p["Ro"], cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (max(1, int(1.2 * pr)) | 1,) * 2))
            if allow.sum() > 0:
                p["allow"] = allow
                _, (p["ay"], p["ax"]) = ndimage.distance_transform_edt(allow == 0, return_indices=True)
            Rys, Rxs = np.nonzero(p["Ro"])
            p["span"] = (max(0.0, (np.ptp(Rxs) + 1) / 2 - pr) * 0.85, max(0.0, (np.ptp(Rys) + 1) / 2 - pr) * 0.6)


def _pupils(self, img, look):
    if not getattr(self, "_matched", False):
        _match(self)
        self._matched = True
    lx, ly = float(np.clip(look[0], -1.2, 1.2)), float(np.clip(look[1], -1.0, 1.0))
    for p in self.pupils:
        if not p or p.get("skip"):
            continue
        dx, dy = lx * p["span"][0], ly * p["span"][1]      # (at rest too: the eye never pops between the drawn
        x0, y0, x1, y1 = p["box"]                           # pupil and the redrawn one)
        tx, ty = p["px"] + dx - x0, p["py"] + dy - y0
        ix, iy = int(round(np.clip(tx, 0, x1 - x0 - 1))), int(round(np.clip(ty, 0, y1 - y0 - 1)))
        if not p["allow"][iy, ix]:                       # keep the pupil inside the opening
            tx, ty = float(p["ax"][iy, ix]), float(p["ay"][iy, ix])
        reg = img[y0:y1, x0:x1]
        out = reg.copy()
        pa = p["pa"][..., None]
        out[..., :3] = out[..., :3] * (1 - pa) + p["clean"][..., :3] * pa
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

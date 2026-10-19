"""Faces on the whole-body pose drawings: eyes that look, blink and narrow, and drawn mouths for the lip sync.

The drawings come with open eyes (white with a black pupil) and a closed mouth line. Everything here works on the
4x upscaled drawing; the mouth positions were measured on the native drawing (`cast.py`).

- Eyes are found from the drawing: the two big white blobs in the head. The pupil is painted out and redrawn where
  the eyes should look, so a character can glance at someone, at the box, or into the lens.
- Lids: a skin-coloured lid comes down from the top of the eye with a dark edge; fully down is a closed eye.
- Mouths: the drawn line is painted out and a cartoon mouth is drawn in the house style (black outline, dark mouth,
  tongue, top teeth), shaped by the sound being made.
"""
import numpy as np, cv2

SS = 4  # supersampling for drawn shapes


def _blobs_white(rgb, a, roi):
    x0, y0, x1, y1 = roi
    sub = rgb[y0:y1, x0:x1].astype(np.int16)
    m = ((sub.min(2) > 200) & (a[y0:y1, x0:x1] > 128)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 4)
    if n < 2:
        return None
    i = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    full = np.zeros(a.shape, np.uint8)
    full[y0:y1, x0:x1] = (lab == i)
    return full


def _fill_holes(m):
    h, w = m.shape
    ff = m.copy() * 255
    pad = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(ff, pad, (0, 0), 128)
    return ((ff == 255) | (ff == 0)).astype(np.uint8)


class Eye:
    def __init__(self, rgb, a, box_native):
        bx, by, bw, bh = box_native
        roi = (max(bx * 4 - 10, 0), max(by * 4 - 10, 0), bx * 4 + bw * 4 + 10, by * 4 + bh * 4 + 10)
        white = _blobs_white(rgb, a, roi)
        # the eye: white plus the pupil inside it
        x0, y0, x1, y1 = roi
        sub = np.zeros((y1 - y0 + 2, x1 - x0 + 2), np.uint8)
        sub[1:-1, 1:-1] = white[y0:y1, x0:x1]
        filled = _fill_holes(sub)[1:-1, 1:-1]
        # pupils that touch the white's edge are not enclosed: close the shape
        hull = cv2.convexHull(cv2.findNonZero(sub[1:-1, 1:-1]))
        hullm = np.zeros_like(filled)
        cv2.fillConvexPoly(hullm, hull, 1)
        inner = np.zeros(a.shape, np.uint8)
        inner[y0:y1, x0:x1] = np.maximum(filled, hullm)
        self.inner = inner
        ys, xs = np.where(inner > 0)
        self.box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
        self.c = np.array([(xs.min() + xs.max()) / 2, (ys.min() + ys.max()) / 2])
        self.r = np.array([(xs.max() - xs.min()) / 2, (ys.max() - ys.min()) / 2])
        lum = rgb[..., :3].astype(np.int16).mean(2)
        core = cv2.erode(inner, np.ones((7, 7), np.uint8))
        dark = ((core > 0) & (lum < 90)).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(dark, 8)
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        pup = cv2.dilate((lab == k).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool) & (lum < 140) & (inner > 0)
        pys, pxs = np.where(pup)
        self.pc = np.array([pxs.mean(), pys.mean()])
        self.pr = np.array([(pxs.max() - pxs.min() + 1) / 2, (pys.max() - pys.min() + 1) / 2])
        self.pupil = pup
        self.pcol = np.median(rgb[pup], 0)
        self.wcol = np.median(rgb[(inner > 0) & (lum > 220)], 0)
        # skin just outside the eye's outline
        ring = cv2.dilate(inner, np.ones((25, 25), np.uint8)) - cv2.dilate(inner, np.ones((11, 11), np.uint8))
        cand = rgb[(ring > 0) & (a > 200)].astype(np.float32)
        sat = cand.max(1) - cand.min(1)
        cand = cand[(cand.mean(1) > 120) & (sat > 40)]
        self.skin = np.median(cand, 0) if len(cand) else np.array([240, 180, 130.])
        # where the pupil sits now, in eye units
        self.g0 = (self.pc - self.c) / np.maximum(self.r - self.pr, 1)


def _ss_canvas(shape_hw):
    return np.zeros((shape_hw[0] * SS, shape_hw[1] * SS), np.uint8)


def _down(m, shape_hw):
    return cv2.resize(m, (shape_hw[1], shape_hw[0]), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


def draw_eye(rgb, eye, gaze=None, lid=0.0, lid_col=(25, 20, 20)):
    """gaze: (gx, gy) in -1..1 eye units, None = as drawn. lid: 0 open .. 1 closed."""
    x0, y0, x1, y1 = eye.box
    pad = 14
    X0, Y0, X1, Y1 = x0 - pad, y0 - pad, x1 + pad, y1 + pad
    H, W = Y1 - Y0, X1 - X0
    inner = eye.inner[Y0:Y1, X0:X1]
    patch = rgb[Y0:Y1, X0:X1].astype(np.float32)
    if gaze is not None and np.abs(np.array(gaze) - eye.g0).max() > 0.04:
        pm = cv2.dilate(eye.pupil[Y0:Y1, X0:X1].astype(np.uint8), np.ones((5, 5), np.uint8)) & inner
        patch[pm > 0] = eye.wcol
        c = eye.c + np.array(gaze) * np.maximum(eye.r - eye.pr - 2, 1)
        cv = _ss_canvas((H, W))
        cv2.ellipse(cv, (int((c[0] - X0) * SS), int((c[1] - Y0) * SS)),
                    (int(eye.pr[0] * SS), int(eye.pr[1] * SS)), 0, 0, 360, 255, -1, cv2.LINE_AA)
        pa = _down(cv, (H, W)) * cv2.erode(inner, np.ones((3, 3), np.uint8))
        patch = patch * (1 - pa[..., None]) + eye.pcol * pa[..., None]
    if lid > 0.86:
        # closed: lid over the whole eye (outline too), and a lash line curving down
        cover = cv2.GaussianBlur(cv2.dilate(inner, np.ones((13, 13), np.uint8)).astype(np.float32), (0, 0), 1.5)
        patch = patch * (1 - cover[..., None]) + eye.skin * cover[..., None]
        cv = _ss_canvas((H, W))
        cxl, cyl = eye.c[0] - X0, eye.c[1] - Y0 + eye.r[1] * 0.25
        rx, ry = eye.r[0] * 1.02, eye.r[1] * 0.38
        cv2.ellipse(cv, (int(cxl * SS), int(cyl * SS)), (int(rx * SS), int(ry * SS)), 0, 10, 170, 255,
                    int(max(4, eye.r[1] * 0.17) * SS), cv2.LINE_AA)
        lm = _down(cv, (H, W))
        patch = patch * (1 - lm[..., None]) + np.array(lid_col, np.float32) * lm[..., None]
    elif lid > 0.01:
        ey0, ey1 = y0 - Y0, y1 - Y0
        yl = ey0 + lid * (ey1 - ey0 + 2)
        # lid edge curves down in the middle a little
        cv = _ss_canvas((H, W))
        xs = np.arange(W * SS) / SS
        mid = (x0 + x1) / 2 - X0
        curve = yl + (1 - ((xs - mid) / max((x1 - x0) / 2, 1)) ** 2).clip(0) * 0.10 * (ey1 - ey0) * min(lid * 3, 1)
        yy = np.arange(H * SS)[:, None] / SS
        cover = (yy < curve[None, :]).astype(np.uint8) * 255
        cov = _down(cover, (H, W))
        grow = cv2.dilate(inner, np.ones((5, 5), np.uint8)).astype(np.float32)
        cov = cov * grow
        patch = patch * (1 - cov[..., None]) + eye.skin * cov[..., None]
        # the lid's edge
        line = np.zeros((H * SS, W * SS), np.uint8)
        pts = np.stack([np.arange(W * SS), curve * SS], 1).astype(np.int32)
        thick = int(max(3, (eye.r[1] * 0.16)) * SS)
        cv2.polylines(line, [pts], False, 255, thick, cv2.LINE_AA)
        lm = _down(line, (H, W)) * cv2.dilate(inner, np.ones((3, 3), np.uint8))
        patch = patch * (1 - lm[..., None]) + np.array(lid_col, np.float32) * lm[..., None]
    rgb[Y0:Y1, X0:X1] = np.clip(patch, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- mouths
# shape: (width factor, open height in mouth widths, roundness 0..1, teeth, tongue)
VIS = {
    "rest": None,
    "MBP": None,
    "small": (0.88, 0.28, 0.2, True, False),
    "E": (1.10, 0.36, 0.1, True, False),
    "A": (1.05, 0.66, 0.35, True, True),
    "AH": (1.0, 0.48, 0.30, True, True),
    "O": (0.70, 0.60, 1.0, False, True),
    "U": (0.50, 0.40, 1.0, False, False),
    "FV": (0.90, 0.18, 0.1, True, False),
    "L": (0.95, 0.40, 0.3, True, True),
}
PH = {"AA": "A", "AE": "A", "AY": "A", "AW": "A", "AH": "AH", "EH": "E", "EY": "E", "IH": "E", "IY": "E", "Y": "E",
      "AO": "O", "OW": "O", "OY": "O", "UH": "U", "UW": "U", "W": "U", "ER": "U", "R": "U",
      "M": "MBP", "B": "MBP", "P": "MBP", "F": "FV", "V": "FV", "TH": "L", "DH": "L", "L": "L",
      "S": "small", "Z": "small", "SH": "small", "ZH": "small", "CH": "small", "JH": "small", "T": "small",
      "D": "small", "N": "small", "K": "small", "G": "small", "NG": "small", "HH": "AH", "SIL": "rest"}


class Mouth:
    def __init__(self, rgb, a, centre_native, width_native, skin):
        cx, cy = centre_native
        self.c = np.array([cx * 4 + 1.5, cy * 4 + 1.5])
        self.w = width_native * 4
        x0, x1 = int(self.c[0] - self.w * 0.62), int(self.c[0] + self.w * 0.62)
        y0, y1 = int(self.c[1] - 9), int(self.c[1] + 9)
        sub = rgb[y0:y1, x0:x1].astype(np.float32)
        d = np.abs(sub - skin).sum(2)
        m = (d > 55).astype(np.uint8)
        # only the line itself: the rows nearest the centre, not the beard ring around it
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        keep = np.zeros_like(m)
        for i in range(1, n):
            x, y, w, h, ar = st[i]
            if w > 0.35 * (x1 - x0) and h < 14:
                keep[lab == i] = 1
        self.line = np.zeros(a.shape, np.uint8)
        self.line[y0:y1, x0:x1] = cv2.dilate(keep, np.ones((5, 5), np.uint8))
        lc = sub[keep > 0]
        self.lcol = np.median(lc, 0) if len(lc) else np.array([150, 70, 50.])
        self.skin = skin


def erase_line(rgb, mouth):
    ys, xs = np.where(mouth.line > 0)
    if not len(ys):
        return
    y0, y1, x0, x1 = ys.min() - 6, ys.max() + 7, xs.min() - 6, xs.max() + 7
    sub = np.ascontiguousarray(rgb[y0:y1, x0:x1])
    rgb[y0:y1, x0:x1] = cv2.inpaint(sub, mouth.line[y0:y1, x0:x1], 5, cv2.INPAINT_TELEA)


def draw_mouth(rgb, mouth, vis, amt=1.0, smile=0.0, skew=0.0):
    """vis: key of VIS. amt scales the opening (loudness). smile lifts the corners (half smile with skew)."""
    shape = VIS.get(vis)
    if shape is None and abs(smile) < 0.05:
        return
    erase_line(rgb, mouth)
    c, w = mouth.c, mouth.w
    pad = int(w * 0.9)
    X0, Y0 = int(c[0] - pad), int(c[1] - pad)
    H = W = 2 * pad
    patch = rgb[Y0:Y0 + H, X0:X0 + W].astype(np.float32)
    lx, ly = c[0] - X0, c[1] - Y0
    if shape is None:
        # closed, smiling line: corners lifted, one more than the other
        cv = _ss_canvas((H, W))
        xs = np.linspace(-w / 2, w / 2, 40)
        lift = smile * w * 0.16
        ys = -lift * (xs / (w / 2)) ** 2 - skew * lift * (xs / (w / 2))
        pts = np.stack([(lx + xs) * SS, (ly + ys) * SS], 1).astype(np.int32)
        cv2.polylines(cv, [pts], False, 255, int(w * 0.075 * SS), cv2.LINE_AA)
        m = _down(cv, (H, W))
        patch = patch * (1 - m[..., None]) + mouth.lcol * m[..., None]
        rgb[Y0:Y0 + H, X0:X0 + W] = np.clip(patch, 0, 255).astype(np.uint8)
        return
    fw, fh, rnd, teeth, tongue = shape
    mw = w * fw * (0.85 + 0.15 * amt)
    mh = max(w * fh * amt, w * 0.07)
    # outline shape: flat-ish top, round bottom (cartoon "D"), more oval when round
    t = np.linspace(0, 2 * np.pi, 80)
    px = np.cos(t) * mw / 2
    py = np.sin(t) * mh / 2
    top = py < 0
    py[top] *= (0.35 + 0.65 * rnd)
    sm = smile * w * 0.10
    py -= sm * (px / (mw / 2)) ** 2
    py += mh * 0.12
    pts = np.stack([(lx + px) * SS, (ly + py) * SS], 1).astype(np.int32)
    fill = _ss_canvas((H, W))
    cv2.fillPoly(fill, [pts], 255, cv2.LINE_AA)
    fm = _down(fill, (H, W))
    inside = np.array([75, 22, 28], np.float32)
    col = np.zeros((H, W, 3), np.float32) + inside
    if tongue:
        tg = _ss_canvas((H, W))
        cv2.ellipse(tg, (int(lx * SS), int((ly + mh * 0.55) * SS)), (int(mw * 0.30 * SS), int(mh * 0.40 * SS)),
                    0, 0, 360, 255, -1, cv2.LINE_AA)
        tm = _down(tg, (H, W))[..., None]
        col = col * (1 - tm) + np.array([205, 95, 100], np.float32) * tm
    if teeth:
        th = _ss_canvas((H, W))
        ty = ly + py.min() + mh * 0.05
        cv2.rectangle(th, (int((lx - mw * 0.40) * SS), int((ty - 4) * SS)),
                      (int((lx + mw * 0.40) * SS), int((ty + max(mh * 0.22, 2.5)) * SS)), 255, -1)
        tm = _down(th, (H, W))[..., None]
        col = col * (1 - tm) + np.array([250, 248, 240], np.float32) * tm
    patch = patch * (1 - fm[..., None]) + col * fm[..., None]
    ol = _ss_canvas((H, W))
    cv2.polylines(ol, [pts], True, 255, int(max(w * 0.07, 3) * SS), cv2.LINE_AA)
    om = _down(ol, (H, W))
    patch = patch * (1 - om[..., None]) + np.array([30, 18, 18], np.float32) * om[..., None]
    rgb[Y0:Y0 + H, X0:X0 + W] = np.clip(patch, 0, 255).astype(np.uint8)

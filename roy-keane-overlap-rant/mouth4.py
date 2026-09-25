"""Precision lip-sync mouths, layered like a cut-out rig:
   head drawing -> swapped mouth area (lips/teeth/skin/soul patch from the sheet cell) -> head's own mustache.
The head's mustache is always the one on top, so it never changes between mouth shapes, and the whole of
the head's original mouth is covered, so nothing of it ghosts through."""
import numpy as np, cv2
from mouthcomp import MR, REG, mouths, to3, h0, w0

K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
YY, XX = np.mgrid[0:h0, 0:w0]
ROI = (((XX - 0.5 * w0) / (0.40 * w0)) ** 2 + ((YY - 0.36 * h0) / (0.33 * h0)) ** 2) <= 1

def fill(m):
    m8 = m.astype(np.uint8); cnts, _ = cv2.findContours(m8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    f = np.zeros_like(m8); cv2.drawContours(f, cnts, -1, 1, -1); return f.astype(bool)

def mustache(img):
    """grey mustache hair only (not the black mouth opening or teeth under it)."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); s, v = hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    g = v.astype(np.float32)
    flat_black = cv2.blur(g, (9, 9)) < 50                               # mouth interior, not hair
    hair = (v < 150) & (s < 120) & ~flat_black
    band = cv2.morphologyEx(hair.astype(np.uint8), cv2.MORPH_CLOSE, K(4)).astype(bool)
    band &= (YY < 0.42 * h0) & (XX > 0.06 * w0) & (XX < 0.94 * w0) & ~flat_black
    band = cv2.morphologyEx(band.astype(np.uint8), cv2.MORPH_OPEN, K(3)).astype(bool)
    n, lab, st, _ = cv2.connectedComponentsWithStats(band.astype(np.uint8), connectivity=8)
    if n < 2: return np.zeros((h0, w0), bool)
    m = lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    teeth = (s < 40) & (v > 190)
    return fill(m) & ~flat_black & ~teeth

def mouth_area(img, mus):
    """everything that is 'mouth' below the mustache: skin window, lips, teeth, inside, soul patch."""
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV); s, v = hsv[..., 1].astype(int), hsv[..., 2].astype(int)
    below = np.zeros((h0, w0), bool)
    cols = mus.any(0)
    top = np.where(cols, np.argmax(mus[::-1], 0), 0)
    top = np.where(cols, h0 - 1 - top, int(0.2 * h0))              # mustache lower edge per column
    below = YY > (top[None, :] - 2)
    sat = ((s > 95) & (v > 60)) | (v < 70)                          # skin/lips + mouth interior
    m = sat & ROI & below
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, K(2))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m, connectivity=8)
    keep = np.zeros((h0, w0), bool)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 300: continue
        if abs(cen[i][0] - 0.5 * w0) > 0.25 * w0: continue
        keep |= lab == i
    keep = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_CLOSE, K(12)).astype(bool)
    return fill(keep | (mus & False))

_vis = {v: cv2.warpAffine(mouths[v], REG[v], (w0, h0), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE) for v in mouths}
_vis_mus = {v: mustache(_vis[v]) for v in mouths}
_vis_area = {v: mouth_area(_vis[v], _vis_mus[v]) for v in mouths}
_H = {}

def head_info(name, head_bgr):
    if name not in _H:
        hr = cv2.warpAffine(head_bgr, cv2.invertAffineTransform(MR[name]), (w0, h0), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
        mus = mustache(hr)
        _H[name] = (hr, mus, mouth_area(hr, mus))
    return _H[name]

def composite4(head_bgr, head_name, vis, grow=10, feather=4.0):
    H, W = head_bgr.shape[:2]
    hr, hmus, harea = head_info(head_name, head_bgr)
    core = harea | _vis_area[vis]
    # close any gap between the head's mustache and the mouth area (old teeth / lip line hiding there)
    cols = core.any(0) & hmus.any(0)
    mb = h0 - 1 - np.argmax(hmus[::-1], 0)
    cb = h0 - 1 - np.argmax(core[::-1], 0)
    for x in np.where(cols)[0]:
        core[max(0, mb[x] - 6):cb[x] + 1, x] = True
    core &= ~hmus
    core8 = core.astype(np.uint8)
    a = np.maximum(cv2.GaussianBlur(cv2.dilate(core8, K(grow)).astype(np.float32), (0, 0), feather), core.astype(np.float32))
    ring = cv2.dilate(core8, K(grow + 12)).astype(bool) & ~cv2.dilate(core8, K(4)).astype(bool) & ~hmus
    src = _vis[vis].astype(np.float32); hf = hr.astype(np.float32)
    mu_s, mu_h = src[ring].mean(0), hf[ring].mean(0)
    g = np.clip((hf[ring].std(0) + 1) / (src[ring].std(0) + 1), 0.85, 1.15)
    src = np.clip((src - mu_s) * g + mu_h, 0, 255)
    # head's mustache back on top (soft 1.5px edge)
    ma = cv2.GaussianBlur(hmus.astype(np.float32), (0, 0), 1.5)
    a = a * (1 - ma)
    M = MR[head_name]
    patch = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    A = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
    return np.clip(head_bgr * (1 - A) + patch * A, 0, 255).astype(np.uint8)

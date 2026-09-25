"""Precision cut-outs from a (4x) character sheet on a white background: soft anti-aliased matte, colour
decontamination of edge pixels, no stray sheet lines or neighbouring parts, no see-through enclosed pockets."""
import numpy as np, cv2
S = 4
K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def nearest(sheet, box, pt, pred):
    """sheet point (1x) nearest to pt inside box where pred(pixels) holds - a robust seed."""
    x0, y0, x1, y1 = box
    c = sheet[y0 * S:y1 * S:S, x0 * S:x1 * S:S].astype(np.int32)
    ys, xs = np.where(pred(c))
    i = np.argmin((xs + x0 - pt[0]) ** 2 + (ys + y0 - pt[1]) ** 2)
    return (xs[i] + x0, ys[i] + y0)

def matte(sheet, box, seed, bgc=(254, 254, 254), t0=12.0, t1=60.0, open_r=6, keep_r=14, extra=None, keep_hole=None):
    """keep_hole(hole_mask, crop) -> True for enclosed background-coloured pockets that must stay see-through
    (e.g. the gap between the legs).  Every other enclosed pocket is filled."""
    x0, y0, x1, y1 = [int(v * S) for v in box]
    crop = sheet[y0:y1, x0:x1].astype(np.float32)
    B = np.float32(bgc)
    diff = np.sqrt(((crop - B) ** 2).sum(2))
    h, w = diff.shape
    fg = (diff > (t0 + t1) / 2).astype(np.uint8)
    if extra is not None: fg &= extra(crop).astype(np.uint8)
    inv = np.pad(1 - fg, 1, constant_values=1)
    ff = inv.copy(); cv2.floodFill(ff, np.zeros((h + 4, w + 4), np.uint8), (0, 0), 2)
    obj = (ff[1:-1, 1:-1] != 2).astype(np.uint8)
    released = np.zeros((h, w), bool)
    if keep_hole is not None:           # enclosed pockets of pure sheet background that must stay see-through
        pockets = obj & (1 - fg)
        n, lab, st, _ = cv2.connectedComponentsWithStats(pockets, connectivity=4)
        for i in range(1, n):
            hm = lab == i
            if st[i, cv2.CC_STAT_AREA] > 300 and diff[hm].mean() < 14 and keep_hole(hm, crop):
                obj[hm] = 0; released |= hm
    # drop thin stray lines / touching neighbours: opening-by-reconstruction around the seed blob
    op = cv2.morphologyEx(obj, cv2.MORPH_OPEN, K(open_r))
    n, lab = cv2.connectedComponents(op, connectivity=8)
    sx, sy = int(seed[0] * S) - x0, int(seed[1] * S) - y0
    core = (lab == lab[sy, sx]).astype(np.uint8)
    obj = obj & cv2.dilate(core, K(keep_r))
    n, lab = cv2.connectedComponents(obj, connectivity=8)
    obj = (lab == lab[sy, sx]).astype(np.uint8)
    cnts, _ = cv2.findContours(obj, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(obj); cv2.drawContours(filled, cnts, -1, 1, -1)
    if keep_hole is not None:
        filled &= (obj | ~released).astype(np.uint8)
    band = cv2.dilate(filled, np.ones((5, 5), np.uint8)).astype(bool) & ~cv2.erode(filled, np.ones((5, 5), np.uint8)).astype(bool)
    soft = np.clip((diff - t0) / (t1 - t0), 0, 1)
    alpha = np.where(band, soft, filled.astype(np.float32))
    alpha = np.where(cv2.dilate(filled, np.ones((5, 5), np.uint8)).astype(bool), alpha, 0)
    a = np.clip(alpha, 1e-3, 1)[..., None]
    col = np.clip((crop - (1 - a) * B) / a, 0, 255)
    col = np.where(alpha[..., None] > 0.02, col, crop)
    rgba = np.dstack([col.astype(np.uint8), (alpha * 255 + 0.5).astype(np.uint8)])
    # trim to content
    ys, xs = np.where(rgba[..., 3] > 0)
    ty0, ty1, tx0, tx1 = max(0, ys.min() - 4), min(h, ys.max() + 5), max(0, xs.min() - 4), min(w, xs.max() + 5)
    return rgba[ty0:ty1, tx0:tx1].copy(), (x0 + tx0, y0 + ty0)

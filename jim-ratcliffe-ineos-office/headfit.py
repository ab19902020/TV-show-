"""The shirt collar + tie knot drawn under each head cell's chin (collar_mask): rig.py uses it to find where the
head drawing's own collar is, so the head can be layered behind the arm-pose torso's collar."""
import numpy as np, cv2

K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def classes(rgba):
    c = rgba[..., :3].astype(np.int32); b, g, r = c[..., 0], c[..., 1], c[..., 2]
    v = c.max(2); sat = v - c.min(2); a = rgba[..., 3] > 100
    red = a & (r > 130) & (g < 85) & (b < 90) & (r > g + 90)          # the tie's crimson, never orange skin
    skin = a & (r > b + 40) & (r > 120) & ~red
    white = a & (v > 200) & (sat < 30)
    return red, skin, white

def knot_of(rgba, lo=0.0, hi=1.0, span=110):
    """top-centre of the tie knot (the red blob nearest the top of the given height band, centre columns)"""
    red, _, _ = classes(rgba)
    H, W = red.shape
    m = red.copy(); m[:int(lo * H)] = False; m[int(hi * H):] = False
    m[:, :int(W / 2 - span)] = False; m[:, int(W / 2 + span):] = False
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8))
    if n < 2: return None
    i = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    ys, xs = np.where(lab == i); yk = ys.min()
    return float(xs[ys < yk + 25].mean()), float(yk)

def collar_mask(head):
    """head px: the collar + knot + their outlines (what the collar layer shows).  The collar is the white that
    wraps round the neck *below the chin*: white areas touching the knot or lying beside the neck column, never
    the (also pale) beard above."""
    red, skin, white = classes(head)
    H, W = red.shape
    kx, ky = knot_of(head, 0.75)
    yy, xx = np.mgrid[0:H, 0:W]
    dark = (head[..., :3].max(2) < 70) & (head[..., 3] > 100)
    # the chin: lowest skin/beard row in the column band above the knot
    face = (skin | ((head[..., :3].max(2) > 120) & ~white & ~red)) & (head[..., 3] > 100)
    band = face[:, int(kx - 30):int(kx + 30)] & (yy[:, int(kx - 30):int(kx + 30)] < ky)
    rows = np.where(band.sum(1) > 20)[0]
    chin = rows.max() if len(rows) else ky - 30
    near = (np.abs(xx - kx) < 150) & (yy > ky - 100)
    m = (white & near) | (red & (yy >= ky - 4) & near)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    keep = np.zeros_like(m)
    kd = cv2.dilate((red & (yy >= ky - 4)).astype(np.uint8), K(14)).astype(bool)
    for i in range(1, n):
        comp = lab == i
        if st[i, cv2.CC_STAT_AREA] < 150: continue
        cyi = np.where(comp)[0].mean()
        centre = abs(np.where(comp)[1].mean() - kx) < 45
        if centre and cyi < chin: continue                                  # beard highlights
        if (comp & kd).any() or cyi > chin - 40: keep |= comp
    keep |= red & (yy >= ky - 4) & near
    keep = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_CLOSE, K(4)).astype(bool) & ~(face & (yy < chin + 4))
    keep |= dark & cv2.dilate(keep.astype(np.uint8), K(5)).astype(bool) & ~(yy < chin)
    return keep, (kx, ky)

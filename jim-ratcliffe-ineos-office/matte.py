"""Precision cut-outs from a (4x) character sheet on a pure-white background.

The hard part: his shirt, collar and cuffs are white too (the highlights are pure 255, the same as the sheet),
so a plain "flood the background in from the edges" leaks through every opening and leaves the shirt
see-through.  This cutter
  1. seals the shape before flooding: small openings (cuff ends) are closed morphologically, explicit seal lines
     close the neck opening of the headless torsos, and edges where the sheet cell cuts through the drawing
     (the bottom of the head cells, the hips of the torsos) are not flooded from at all;
  2. classifies every enclosed white area: shirt (touches the tie), cuffs (small, touch skin), highlights (tiny)
     are filled; big pockets that touch neither (between an arm and the body, between the legs) stay open;
  3. gives the result a soft, colour-decontaminated edge, and drops stray lines / neighbouring parts."""
import numpy as np, cv2
S = 4
LAST_WHY = None
LAST_STATS = []
K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def nearest(sheet, box, pt, pred):
    """sheet point (1x) nearest to pt inside box where pred(pixels) holds - a robust seed."""
    x0, y0, x1, y1 = box
    c = sheet[y0 * S:y1 * S:S, x0 * S:x1 * S:S].astype(np.int32)
    ys, xs = np.where(pred(c))
    i = np.argmin((xs + x0 - pt[0]) ** 2 + (ys + y0 - pt[1]) ** 2)
    return (xs[i] + x0, ys[i] + y0)

def colour_masks(crop):
    c = crop.astype(np.int32); b, g, r = c[..., 0], c[..., 1], c[..., 2]
    red = (r > 120) & (r > g + 70) & (r > b + 60)
    skin = (r > 170) & (g > 105) & (r > b + 60) & ~red          # lit skin (hands, face) - not brown hair
    return red, skin

def exterior_of(passable, sides):
    """pixels of `passable` connected to the crop border on the given sides ('t','b','l','r')."""
    h, w = passable.shape
    p = np.pad(passable.astype(np.uint8), 1, constant_values=0)
    if "t" in sides: p[0, :] = 1
    if "b" in sides: p[-1, :] = 1
    if "l" in sides: p[:, 0] = 1
    if "r" in sides: p[:, -1] = 1
    n, lab = cv2.connectedComponents(p, connectivity=4)
    border = set(np.unique(np.concatenate([lab[0, :] if "t" in sides else [], lab[-1, :] if "b" in sides else [],
                                           lab[:, 0] if "l" in sides else [], lab[:, -1] if "r" in sides else []]).astype(int)))
    border.discard(0)
    ext = np.isin(lab, list(border))
    return ext[1:-1, 1:-1]

def matte(sheet, box, seed, bgc=(255, 255, 255), t0=12.0, t1=60.0, open_r=6, keep_r=14, extra=None,
          sides="tblr", seal_r=10, cuff_seal=True, seal_fn=None, cuff_area=6000, cuff_r=13, tiny=300,
          fill_enclosed=False, fill_fn=None, drop=None, others=()):
    """box, seed in 1x sheet coords.  sides: which crop edges are real background (flooded from).
    seal_fn(crop, ink, red, skin) -> polylines (crop px) that close openings.  drop(mask_dict) -> extra pixels to
    force transparent.  Returns (rgba crop, (x0, y0) 4x offset)."""
    x0, y0, x1, y1 = [int(v * S) for v in box]
    crop = sheet[y0:y1, x0:x1].astype(np.float32)
    B = np.float32(bgc)
    diff = np.sqrt(((crop - B) ** 2).sum(2))
    h, w = diff.shape
    ink = diff > (t0 + t1) / 2
    if extra is not None: ink &= extra(crop).astype(bool)
    red, skin = colour_masks(crop)
    # ---- 0. drop thin stray sheet lines (opening by reconstruction); neighbours are separated at the end
    ink8 = ink.astype(np.uint8)
    op = cv2.morphologyEx(ink8, cv2.MORPH_OPEN, K(open_r))
    ink = (ink8 & cv2.dilate(op, K(keep_r))).astype(bool)
    sx, sy = int(seed[0] * S) - x0, int(seed[1] * S) - y0
    dropm = None
    if drop is not None:                               # the neighbour's side: open background from the start
        dropm = drop(dict(crop=crop, ink=ink, red=red, skin=skin)).astype(bool)
        ink &= ~dropm
    red &= ink; skin &= ink
    # ---- 1. seal and flood
    barrier = ink.astype(np.uint8)
    for line in (seal_fn(crop, ink, red, skin) if seal_fn else []):
        cv2.polylines(barrier, [np.array(line, np.int32)], False, 1, 5)
    c = crop.astype(np.int32); v = c.max(2); sat = v - c.min(2)
    grey = ink & (v > 30) & (v < 180) & (sat < 50) & ~skin & ~red
    sealed = barrier
    if cuff_seal:          # close the open ends of the cuffs only: where a hand meets a sleeve
        near = cv2.dilate(skin.astype(np.uint8), K(18)).astype(bool) & cv2.dilate(grey.astype(np.uint8), K(18)).astype(bool)
        sealed = barrier | (cv2.morphologyEx(barrier, cv2.MORPH_CLOSE, K(seal_r)) & near.astype(np.uint8))
    passable = sealed == 0
    if dropm is not None: passable |= dropm
    ext0 = exterior_of(passable, sides)
    if dropm is not None:                              # anything connected to the neighbour's side is outside too
        n_, lab_ = cv2.connectedComponents(passable.astype(np.uint8), connectivity=4)
        ext0 |= np.isin(lab_, np.unique(lab_[dropm & passable])) & (lab_ > 0)
    fig = ~ext0
    # ---- 2. classify the white areas inside the figure
    white_in = fig & ~ink
    n, lab, st, _ = cv2.connectedComponentsWithStats(white_in.astype(np.uint8), connectivity=4)
    near_red = cv2.dilate(red.astype(np.uint8), K(5)).astype(bool)
    near_skin = cv2.dilate(skin.astype(np.uint8), K(6)).astype(bool)
    near_grey = cv2.dilate(grey.astype(np.uint8), K(6)).astype(bool)
    thick = cv2.distanceTransform(white_in.astype(np.uint8), cv2.DIST_L2, 5)
    grown_ext = cv2.dilate(ext0.astype(np.uint8), K(seal_r + 2)).astype(bool)
    keep = ink.copy()
    pure_bg = crop.min(2) >= 251                        # the sheet's own paper white (shirt whites are shaded)
    why = np.zeros((h, w), np.uint8)                   # debug: which rule filled what
    for i in range(1, n):
        m = lab == i; area = st[i, cv2.CC_STAT_AREA]
        paper = pure_bg[m].mean() > 0.45
        if (m & near_red).any(): keep |= m; why[m] = 1                         # shirt / collar
        elif area <= tiny and (not paper or area < 40): keep |= m; why[m] = 2   # highlights, specks
        elif (area <= cuff_area and (m & near_skin).any() and (m & near_grey).any() and thick[m].max() <= cuff_r
              and not paper):
            keep |= m; why[m] = 3                                              # cuffs: thin bands, sleeve to hand
        elif fill_enclosed and not (m & grown_ext).any(): keep |= m; why[m] = 4       # e.g. the paper he holds
        elif (not (m & grown_ext).any() and area <= 700 and thick[m].max() <= 6.5
              and np.where(m)[0].mean() < 0.55 * h): keep |= m; why[m] = 4          # pocket squares, seam glints
        else: why[m] = 5
        # else: a real gap (between an arm and the body, between the legs) stays see-through
    if fill_fn is not None:
        f = fill_fn(dict(crop=crop, ink=ink, red=red, skin=skin, grey=grey, seed=(sx, sy))).astype(bool)
        why[f & ~keep] = 6; keep |= f
    if dropm is not None: keep &= ~dropm
    # ---- 3. this drawing only: the connected piece (ink + filled white) under the seed, after cutting thin bridges
    k8 = keep.astype(np.uint8)
    op = cv2.morphologyEx(k8, cv2.MORPH_OPEN, K(open_r))
    nn, lab2 = cv2.connectedComponents(op, connectivity=8)
    if lab2[sy, sx] == 0:
        ys, xs = np.where(lab2 > 0); j = np.argmin((xs - sx) ** 2 + (ys - sy) ** 2); sx, sy = xs[j], ys[j]
    core = (lab2 == lab2[sy, sx]).astype(np.uint8)
    k8 = k8 & cv2.dilate(core, K(keep_r))
    nn, lab2 = cv2.connectedComponents(k8, connectivity=8)
    region = lab2 == lab2[sy, sx]
    # neighbouring drawings that touch this one on the sheet: split at the narrowest point (watershed on the
    # distance transform, one marker per drawing's seed)
    oth = [(int(ox * S) - x0, int(oy * S) - y0) for ox, oy in others]
    oth = [(x, y) for x, y in oth if 0 <= x < w and 0 <= y < h and region[y, x]]
    if oth:
        from skimage.segmentation import watershed
        dist = cv2.distanceTransform(region.astype(np.uint8), cv2.DIST_L2, 5)
        mk = np.zeros((h, w), np.int32)
        cv2.circle(mk, (int(sx), int(sy)), 12, 1, -1)
        for k, (x, y) in enumerate(oth): cv2.circle(mk, (x, y), 12, 2 + k, -1)
        lab3 = watershed(-dist, mk, mask=region)
        region = lab3 == 1
    global LAST_WHY, LAST_STATS
    LAST_WHY = (why, (x0, y0))
    pure = (crop.min(2) >= 252)
    LAST_STATS = [(int(why[lab == i].max()), int(st[i, cv2.CC_STAT_AREA]), round(float(thick[lab == i].max()), 1),
                   round(float(pure[lab == i].mean()), 2),
                   bool(((lab == i) & near_skin).any()), bool(((lab == i) & near_grey).any()),
                   int(st[i, 0]), int(st[i, 1])) for i in range(1, n) if st[i, cv2.CC_STAT_AREA] > 120 and why[lab == i].max() >= 2]
    # ---- 4. soft edge: colour-based on inked edges, geometric on sealed white edges
    soft = np.clip((diff - t0) / (t1 - t0), 0, 1)
    geo = cv2.GaussianBlur(region.astype(np.float32), (0, 0), 0.8)
    edge = cv2.dilate(region.astype(np.uint8), K(2)).astype(bool) & ~cv2.erode(region.astype(np.uint8), K(2)).astype(bool)
    alpha = np.where(region, 1.0, 0.0).astype(np.float32)
    alpha = np.where(edge, np.clip(np.maximum(np.minimum(soft, 1.0) * cv2.dilate(region.astype(np.uint8), K(2)), geo), 0, 1), alpha)
    alpha = np.where(region & ~edge, 1.0, alpha)
    a = np.clip(alpha, 1e-3, 1)[..., None]
    col = np.clip((crop - (1 - a) * B) / a, 0, 255)
    col = np.where(alpha[..., None] > 0.02, col, crop)
    rgba = np.dstack([col.astype(np.uint8), (alpha * 255 + 0.5).astype(np.uint8)])
    ys, xs = np.where(rgba[..., 3] > 0)
    ty0, ty1, tx0, tx1 = max(0, ys.min() - 4), min(h, ys.max() + 5), max(0, xs.min() - 4), min(w, xs.max() + 5)
    return rgba[ty0:ty1, tx0:tx1].copy(), (x0 + tx0, y0 + ty0)

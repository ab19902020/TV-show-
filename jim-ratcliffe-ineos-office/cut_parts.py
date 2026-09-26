"""Cut every part out of the 4x character sheet -> parts.pkl  {group: {name: (rgba, (x0, y0) 4x offset)}}."""
import numpy as np, cv2, pickle
from layout import *
from matte import matte, nearest

dark = lambda c: c.sum(2) < 560
red = lambda c: (c[..., 2] > 150) & (c[..., 1] < 90) & (c[..., 0] < 90)
skin = lambda c: (c[..., 2] > c[..., 0] + 50) & (c[..., 2] > 150) & (c[..., 1] > 90)

def no_floor_shadow(frac):
    """drop the light-grey floor shadow under the shoes (bottom part of the box only)."""
    def f(crop):
        v = crop.max(2); sat = v - crop.min(2)
        yy = np.arange(crop.shape[0])[:, None]
        return ~((v > 140) & (sat < 30) & (yy > frac * crop.shape[0]))
    return f

def neck_seal(crop, ink, red_m, skin_m):
    """headless torso: a seal line across the neck opening, from the top of the left jacket collar, over the top
    of the tie knot, to the top of the right jacket collar - so the shirt below it is enclosed."""
    h, w = red_m.shape
    rows = np.where(red_m.sum(1) >= 12)[0]
    if not len(rows): return []
    yk = rows[0]
    xs = np.where(red_m[yk:yk + 30].any(0))[0]; xk = (xs.min() + xs.max()) / 2; kw = max(20, (xs.max() - xs.min()) / 2)
    c = crop.astype(np.int32); v = c.max(2); sat = v - c.min(2)
    grey = ink & (v > 35) & (v < 175) & (sat < 45) & ~skin_m & ~red_m
    def top_of(xa, xb):
        xa, xb = int(max(0, xa)), int(min(w, xb))
        y0, y1 = int(max(0, yk - 40)), int(min(h, yk + 110))
        sub = grey[y0:y1, xa:xb]
        rr = np.where(sub.sum(1) >= 4)[0]
        if not len(rr): return None
        y = rr[0]; x = np.where(sub[y])[0]
        return (float(xa + x.mean()), float(y0 + y))
    L = top_of(xk - 110, xk - kw - 4); R = top_of(xk + kw + 4, xk + 110)
    if L is None or R is None: return []
    line = [[(L[0], L[1]), (xk - kw, yk - 2), (xk + kw, yk - 2), (R[0], R[1])]]
    SEALS.append(line)
    return line
SEALS = []

def shirt_fill(m):
    """torsos: the shirt V under the knot - every pixel between the jacket's two lapels (in the rows of the upper
    chest, around the tie) is shirt or tie, never background."""
    ink = m["ink"]
    c = m["crop"].astype(np.int32)
    red_m = ink & (c[..., 2] > 130) & (c[..., 1] < 85) & (c[..., 0] < 90) & (c[..., 2] > c[..., 1] + 90)   # the tie only
    n, lab = cv2.connectedComponents(red_m.astype(np.uint8))
    sx, sy = m["seed"]
    if lab[sy, sx]: red_m = lab == lab[sy, sx]                    # this drawing's tie, not a neighbour's
    h, w = ink.shape
    rows = np.where(red_m.sum(1) >= 12)[0]
    if not len(rows): return np.zeros((h, w), bool)
    yk = rows[0]
    out = np.zeros((h, w), bool)
    for y in range(max(0, yk - 25), min(h, yk + int(0.45 * h))):
        xr = np.where(red_m[y])[0]
        if len(xr) < 6 or xr.max() - xr.min() > 70: continue          # a tie row: one narrow red run
        cx = int(xr.mean())
        row = ink[y]
        L = np.where(row[max(0, cx - 95):cx - 6])[0]; R = np.where(row[cx + 6:min(w, cx + 95)])[0]
        if len(L) and len(R):
            out[y, max(0, cx - 95) + L.min():cx + 6 + R.max() + 1] = True
    return out

def collar_fill(m):
    """head cells: below the jaw, everything between the outer edges of the jacket on each row is shirt/collar/neck
    (the collar wraps round the back of the neck, so it is open to the background beside the neck)."""
    crop, grey = m["crop"], m["grey"]
    h, w = grey.shape
    c = crop.astype(np.int32); v = c.max(2); sat = v - c.min(2)
    jk = grey & (v > 55) & (sat < 32)
    jk[:int(0.70 * h)] = False
    n, lab, st, _ = cv2.connectedComponentsWithStats(jk.astype(np.uint8))
    big = np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 2000])
    out = np.zeros((h, w), bool)
    for y in range(int(0.70 * h), h):
        xs = np.where(big[y])[0]
        if len(xs) and xs.min() < w / 2 - 40 and xs.max() > w / 2 + 40: out[y, xs.min():xs.max() + 1] = True
    return out

def drop_line(rule, box):
    """rule(x1, y1) -> True where a pixel (1x sheet coords) belongs to the neighbouring drawing"""
    if rule is None: return None
    def f(m):
        h, w = m["ink"].shape
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        return rule(box[0] + xx / 4, box[1] + yy / 4)
    return f

def build(sheet):
    P = {"turn": {}, "head": {}, "arm": {}, "hand": {}, "leg": {}}
    for n, box in TURN.items():
        seed = nearest(sheet, box, ((box[0] + box[2]) / 2, 250), dark)
        P["turn"][n] = matte(sheet, box, seed, extra=no_floor_shadow(0.88))
    for n, (cx, r) in HEADS.items():
        y0, y1 = HEAD_ROWS[r]; box = (cx - 60, y0, min(1536, cx + 60), y1)
        seed = nearest(sheet, box, (cx, (y0 + y1) / 2 - 10), dark)
        others = [nearest(sheet, (ox - 60, y0, min(1536, ox + 60), y1), (ox, (y0 + y1) / 2 - 10), dark)
                  for m_, (ox, orow) in HEADS.items() if orow == r and m_ != n and abs(ox - cx) < 160]
        P["head"][n] = matte(sheet, box, seed, open_r=5, sides="tlr", cuff_seal=(n == "THINKING"),   # cell cuts his chest
                             fill_fn=collar_fill, others=others)
    for n, (cx, r) in ARMS.items():
        if n == "FINGER UP": continue          # only half a torso is drawn on the sheet
        y0, y1 = ARM_ROWS[r]
        if r == 0 and cx < 250: y0 = ARM_TOP_UNDER_HEADER
        box = (max(0, cx - 118), y0, min(1536, cx + 118), y1)
        lo, hi = ARM_X_LIMIT.get(n, (None, None))
        box = (lo or box[0], y0, hi or box[2], y1)
        seed = nearest(sheet, box, (cx, (y0 + y1) / 2), red)
        others = [nearest(sheet, (max(0, ox - 118), y0, min(1536, ox + 118), y1), (ox, (y0 + y1) / 2), red)
                  for m_, (ox, orow) in ARMS.items() if orow == r and m_ != n and abs(ox - cx) < 160 and m_ != "FINGER UP"]
        P["arm"][n] = matte(sheet, box, seed, open_r=4, keep_r=12, sides="tlr", seal_fn=neck_seal,   # cut at the hips
                            fill_enclosed=n in ("HOLDING PAPER", "HOLDING CUP"), others=others, fill_fn=shirt_fill,
                            drop=drop_line(ARM_SPLIT.get(n), box))
    for n, (x0, x1) in HANDS.items():
        box = (x0, HAND_ROW[0], x1, HAND_ROW[1])
        seed = nearest(sheet, box, ((x0 + x1) / 2, sum(HAND_ROW) / 2), skin)
        P["hand"][n] = matte(sheet, box, seed, open_r=3, fill_enclosed=n in ("HOLD PAPER", "HOLD CUP"))
    for n, (x0, x1) in LEGS.items():
        box = (x0, LEG_ROW[0], x1, LEG_ROW[1])
        seed = nearest(sheet, box, ((x0 + x1) / 2, 905), dark)
        nored = lambda c: ~((c[..., 2] > 150) & (c[..., 1] < 110) & (c[..., 0] < 110))      # the red header bar
        P["leg"][n] = matte(sheet, box, seed, open_r=4, extra=lambda c: no_floor_shadow(0.80)(c) & nored(c))
    return P

def contact(P, path, bg=(90, 150, 90)):
    tiles = []
    for g, d in P.items():
        row = []
        for n, (rgba, off) in d.items():
            a = rgba[..., 3:4] / 255.0
            im = (rgba[..., :3] * a + np.float32(bg) * (1 - a)).astype(np.uint8)
            h = 260; w = max(1, int(im.shape[1] * h / im.shape[0]))
            im = cv2.resize(im, (w, h), interpolation=cv2.INTER_AREA)
            im = cv2.copyMakeBorder(im, 0, 22, 4, 4, cv2.BORDER_CONSTANT, value=(40, 40, 40))
            cv2.putText(im, n[:14], (4, h + 16), 0, 0.45, (255, 255, 255), 1)
            row.append(im)
        tiles.append(row)
    W = 3000
    lines = []
    for row in tiles:
        cur, cw = [], 0
        for t in row:
            if cw + t.shape[1] > W: lines.append(cur); cur, cw = [], 0
            cur.append(t); cw += t.shape[1]
        lines.append(cur)
    out = [cv2.copyMakeBorder(np.hstack(l), 0, 6, 0, W - sum(t.shape[1] for t in l), cv2.BORDER_CONSTANT, value=(40, 40, 40)) for l in lines]
    cv2.imwrite(path, np.vstack(out))

if __name__ == "__main__":
    sheet = cv2.imread("src/sheet_x4.png")
    P = build(sheet)
    pickle.dump(P, open("parts.pkl", "wb"))
    contact(P, "parts_check.png")
    print({g: len(d) for g, d in P.items()})

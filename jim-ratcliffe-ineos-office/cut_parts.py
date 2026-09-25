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

def build(sheet):
    P = {"turn": {}, "head": {}, "arm": {}, "hand": {}, "leg": {}}
    for n, box in TURN.items():
        seed = nearest(sheet, box, ((box[0] + box[2]) / 2, 250), dark)
        # white pockets in the lower half are the gaps between the legs / arms, not shirt
        low = lambda hm, c: np.where(hm)[0].mean() > 0.55 * c.shape[0]
        P["turn"][n] = matte(sheet, box, seed, extra=no_floor_shadow(0.88), keep_hole=low)
    for n, (cx, r) in HEADS.items():
        y0, y1 = HEAD_ROWS[r]; box = (cx - 60, y0, min(1536, cx + 60), y1)
        seed = nearest(sheet, box, (cx, (y0 + y1) / 2 - 10), dark)
        P["head"][n] = matte(sheet, box, seed, open_r=5)
    for n, (cx, r) in ARMS.items():
        if n == "FINGER UP": continue          # only half a torso is drawn on the sheet
        y0, y1 = ARM_ROWS[r]
        if r == 0 and cx < 250: y0 = ARM_TOP_UNDER_HEADER
        box = (max(0, cx - 118), y0, min(1536, cx + 118), y1)
        seed = nearest(sheet, box, (cx, (y0 + y1) / 2), red)
        def away_from_shirt(hm, c):       # arm/body gaps are background; the shirt hugs the tie
            ys, xs = np.where(red(c.astype(np.int32)))
            return abs(np.where(hm)[1].mean() - np.median(xs)) > 110
        P["arm"][n] = matte(sheet, box, seed, open_r=4, keep_r=12, keep_hole=away_from_shirt)
    for n, (x0, x1) in HANDS.items():
        box = (x0, HAND_ROW[0], x1, HAND_ROW[1])
        seed = nearest(sheet, box, ((x0 + x1) / 2, sum(HAND_ROW) / 2), skin)
        P["hand"][n] = matte(sheet, box, seed, open_r=3)
    for n, (x0, x1) in LEGS.items():
        box = (x0, LEG_ROW[0], x1, LEG_ROW[1])
        seed = nearest(sheet, box, ((x0 + x1) / 2, 905), dark)
        P["leg"][n] = matte(sheet, box, seed, open_r=4, extra=no_floor_shadow(0.80), keep_hole=lambda hm, c: True)
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

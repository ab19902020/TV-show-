"""cut the six heads of a 3x2 acting-head sheet (alpha with haze) into separate clean RGBA drawings"""
import sys, cv2, numpy as np, json
from pathlib import Path
src, outdir, names = sys.argv[1], Path(sys.argv[2]), sys.argv[3].split(",")
im = cv2.imread(src, cv2.IMREAD_UNCHANGED)
H, W = im.shape[:2]
a = im[..., 3]
solid = (a > 160).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(solid, 8)
big = [k for k in range(1, n) if st[k, cv2.CC_STAT_AREA] > 0.01 * H * W]
cells = []
for k in big:
    x, y, w, h, ar = st[k]
    cells.append((round((y + h / 2) / (H / 2) - 0.5), (x + w / 2), k))
cells.sort(key=lambda c: (c[0], c[1]))
outdir.mkdir(parents=True, exist_ok=True)
info = {}
for (row, cx, k), name in zip(cells, names):
    if name == "-":
        continue
    m = (lab == k).astype(np.uint8)
    # holes inside the figure stay solid (eye whites with soft alpha)
    inv = 1 - m
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
    for q in range(1, n2):
        xx, yy, ww, hh, ar = st2[q]
        if xx > 0 and yy > 0 and xx + ww < W and yy + hh < H and ar < 0.002 * H * W:
            m[lab2 == q] = 1
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    af = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.7)
    af = np.clip((af - 0.2) / 0.6, 0, 1) * (a.astype(np.float32) / 255 > 0.05)
    x, y, w, h = cv2.boundingRect(m)
    pad = 6
    x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(W, x + w + pad), min(H, y + h + pad)
    out = im[y0:y1, x0:x1].copy()
    out[..., 3] = (np.maximum(af[y0:y1, x0:x1], 0) * 255).astype(np.uint8)
    # bleed colour under the (now zero) haze so edges stay clean when scaled
    cv2.imwrite(str(outdir / f"{name}.png"), out)
    info[name] = [int(x0), int(y0), int(x1), int(y1)]
print(json.dumps(info))

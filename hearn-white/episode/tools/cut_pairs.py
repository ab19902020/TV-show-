"""split the paired-fight cells (cut out by the anime matting model) into an Eddie layer and a Dana layer on the
same canvas: drawn at the same place and scale they rebuild the drawing exactly; each has its own face"""
import cv2, numpy as np, json
from pathlib import Path
SP = Path(__file__).resolve().parent.parent
C = SP / "engine/library/characters"
SEEDS = {
    "tap_e": ([(110, 280), (170, 130), (60, 460), (290, 165)], [(430, 300), (390, 165), (480, 460), (340, 150)]),
    "tap_d": ([(100, 300), (110, 120), (60, 460)], [(420, 300), (400, 130), (470, 460)]),
    "clash": ([(120, 300), (160, 120), (300, 40)], [(420, 300), (440, 170), (290, 40)]),
    "clinch": ([(60, 300), (190, 40), (60, 470), (165, 125), (300, 140)], [(330, 320), (380, 470), (250, 150), (215, 200), (100, 225)]),
}
out = {}
for k, (se, sd) in SEEDS.items():
    rgba = cv2.imread(str(SP / f"rembg_work/cell_{k}.png"), cv2.IMREAD_UNCHANGED)
    a = rgba[..., 3]
    m = (a > 100).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    H, W = m.shape
    keep = [q for q in range(1, n) if st[q, cv2.CC_STAT_AREA] > 4000 and
            st[q, cv2.CC_STAT_LEFT] < 0.8 * W and st[q, cv2.CC_STAT_LEFT] + st[q, cv2.CC_STAT_WIDTH] > 0.2 * W]
    body = np.isin(lab, keep)
    alpha = np.where(cv2.dilate(body.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0, a, 0)
    mk = np.zeros((H, W), np.int32)
    pass
    for x, y in se:
        cv2.circle(mk, (x, y), 6, 1, -1)
    for x, y in sd:
        cv2.circle(mk, (x, y), 6, 2, -1)
    ws = cv2.watershed(np.ascontiguousarray(rgba[..., :3]), mk)
    if k == "clash":                         # two separate figures: split by which one each piece belongs to
        n2, lab2, st2, cen = cv2.connectedComponentsWithStats(body.astype(np.uint8), 8)
        near = cv2.distanceTransformWithLabels((lab2 == 0).astype(np.uint8), cv2.DIST_L2, 5,
                                               labelType=cv2.DIST_LABEL_PIXEL)[1]
        ys, xs = np.nonzero(lab2 > 0)
        owner = np.zeros_like(lab2)
        owner[ys, xs] = lab2[ys, xs]
        idx = np.zeros(near.max() + 1, np.int32)
        idx[near[ys, xs]] = lab2[ys, xs]
        full = idx[near]
        ws = np.where(cen[full][..., 0] < W / 2, 1, 2).astype(np.int32)
    for who, lb, cid in (("e", 1, "eddie-hearn"), ("d", 2, "dana-white")):
        part = (ws == lb) | (ws == -1)
        part = cv2.dilate(part.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0     # 2 px overlap: no seam
        o = rgba.copy()
        o[..., 3] = np.where(part, alpha, 0)
        d = C / cid / "reference/cuts/pairs"
        d.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(d / f"{k}.png"), o)
    ys, xs = np.nonzero(alpha > 128)
    out[k] = dict(size=[W, H], bottom=int(ys.max()), xmid=float((xs.min() + xs.max()) / 2))
    vis = rgba[..., :3].copy()
    vis[ws == 1] = (vis[ws == 1] * 0.6 + np.array([0, 0, 255]) * 0.4).astype(np.uint8)
    vis[ws == 2] = (vis[ws == 2] * 0.6 + np.array([255, 0, 0]) * 0.4).astype(np.uint8)
    vis[alpha < 100] = (0, 160, 0)
    cv2.imwrite(str(SP / f"view/split_{k}.jpg"), vis)
print(json.dumps(out))

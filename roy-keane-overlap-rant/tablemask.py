"""Occlusion mask for the table top + mug in front of Roy (in 4x world coords)."""
import numpy as np, cv2
S = 4
bg = cv2.imread("src/studio_x4.png")
H, W = bg.shape[:2]
mask = np.zeros((H, W), np.uint8)
X0, X1 = 520, 840
lum = bg.astype(np.int32).sum(2)
edge = {}
for x in range(X0 * S, X1 * S):
    col = lum[576 * S:596 * S, x]
    idx = np.where(col < 110)[0]
    edge[x] = 576 * S + (idx[0] if len(idx) else 10 * S)
xs = np.arange(X0 * S, X1 * S)
ys = np.array([edge[x] for x in xs], np.float32)
# robust smoothing: running median then mean
k = 41
pad = np.pad(ys, k // 2, mode="edge")
med = np.array([np.median(pad[i:i + k]) for i in range(len(ys))])
sm = np.convolve(np.pad(med, 15, mode="edge"), np.ones(31) / 31, mode="valid")
for x, y in zip(xs, sm):
    mask[int(round(y)) - 2:, x] = 255      # include the dark rim of the table top
# fade the mask sides out (Roy never goes there, avoid hard vertical cut)
# mug in front of Roy's left arm: body hull + handles
mx0, my0, mx1, my1 = 733 * S, 551 * S, 797 * S, 603 * S
sub = bg[my0:my1, mx0:mx1].astype(np.int32)
bright = (sub.min(2) > 150).astype(np.uint8)
n, lab, st, _ = cv2.connectedComponentsWithStats(bright)
m = np.zeros_like(bright)
for i in range(1, n):
    if st[i, cv2.CC_STAT_AREA] > 60: m[lab == i] = 1
body = m.copy(); body[:, :int((747 - 733) * S)] = 0; body[:, int((782 - 733) * S):] = 0
pts = cv2.findNonZero(body)
hull = cv2.convexHull(pts)
mm = np.zeros_like(m); cv2.fillConvexPoly(mm, hull, 1)
mm = np.maximum(mm, m)
mm = cv2.dilate(mm, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
mask[my0:my1, mx0:mx1] = np.maximum(mask[my0:my1, mx0:mx1], mm * 255)
mask = cv2.GaussianBlur(mask, (0, 0), 1.2)
cv2.imwrite("src/table_mask_x4.png", mask)
vis = bg[520 * S:620 * S, 540 * S:820 * S].copy()
red = np.zeros_like(vis); red[..., 2] = 255
a = (mask[520 * S:620 * S, 540 * S:820 * S] / 255.0)[..., None] * 0.5
vis = (vis * (1 - a) + red * a).astype(np.uint8)
cv2.imwrite("tablemask_vis.png", cv2.resize(vis, (vis.shape[1] // 2, vis.shape[0] // 2), interpolation=cv2.INTER_AREA))
print("edge range", sm.min() / S, sm.max() / S)

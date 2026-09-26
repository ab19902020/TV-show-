"""Audit the walk rig: consecutive frames of a walk drawn in world space on a floor line, both directions.
For scenes with walker.py (Walker.walk_layers) + legrig.py.

  python3 tools/walkcheck.py <scene dir> <out.jpg> [place A] [place B]      places are names in perf.py
Check: both shoes point the way he walks, knees bend forward, the planted foot stays exactly still from frame
to frame (it is drawn in world space, so any slide shows), legs / torso / head all face the same way."""
import sys, os, argparse, numpy as np, cv2

a = argparse.ArgumentParser()
a.add_argument("scene"); a.add_argument("out"); a.add_argument("a", nargs="?"); a.add_argument("b", nargs="?")
a.add_argument("--dur", type=float, default=1.3); a.add_argument("--n", type=int, default=14)
o = a.parse_args()
out = os.path.abspath(o.out)
os.chdir(o.scene); sys.path.insert(0, ".")
import pickle, perf
from rig import render_layers
from walker import build
W, _ = build(pickle.load(open("parts.pkl", "rb")))
A = getattr(perf, o.a) if o.a else perf.BLOCK[0]["a"]
B = getattr(perf, o.b) if o.b else next(b["b"] for b in perf.BLOCK if b["kind"] == "walk")
rows = []
for d, p0, p1 in (("L", A, B) if A[0] > B[0] else ("L", B, A), ("R", A, B) if A[0] < B[0] else ("R", B, A)):
    blk = dict(t0=0, t1=o.dur, d=d, a=p0, b=p1); w = W[d]; tiles = []
    for j in range(o.n):
        p = perf.progress(o.dur * j / (o.n - 1), blk)
        x, f, k = (p0[q] + (p1[q] - p0[q]) * p for q in range(3))
        Mw = np.array([[k, 0, x - k * w.hip_x], [0, k, f - k * w.floor], [0, 0, 1]])
        x0 = min(p0[0], p1[0]) - 150; y0 = f - 300
        im = render_layers(w.walk_layers(p, blk), np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]]) @ Mw,
                           (int(abs(p1[0] - p0[0]) + 300), 340))
        img = (im[..., :3] + np.float32([200, 215, 200]) * (1 - im[..., 3:4])).astype(np.uint8)
        cv2.line(img, (0, int(f - y0)), (img.shape[1], int(f - y0)), (0, 0, 200), 1)
        cv2.putText(img, "%s %.2f" % (d, p), (4, 14), 0, 0.45, (0, 0, 0), 1); tiles.append(img)
    h = (o.n + 1) // 2
    rows.append(np.vstack([np.hstack(tiles[:h]), np.hstack(tiles[h:] + [np.zeros_like(tiles[0])] * (2 * h - o.n))]))
img = np.vstack(rows)
if img.shape[1] > 2400: img = cv2.resize(img, None, fx=2400 / img.shape[1], fy=2400 / img.shape[1], interpolation=cv2.INTER_AREA)
cv2.imwrite(out, img, [cv2.IMWRITE_JPEG_QUALITY, 90]); print(out)

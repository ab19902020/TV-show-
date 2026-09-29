"""Audit the head / collar / shoulder join of every arm pose, on magenta (anything see-through shows pink).
For scenes built on the full-body rig (rig.py with Rig, render_layers, NECK_PIVOT, F_KNOT).

  python3 tools/joins.py <scene dir> <out.jpg> [head] [tilt deg] [nod px] [--zoom knot]
Check: one knot and the same collar on every pose, the neck tucked into the collar, no second shoulder line,
no pink inside the figure; then again with a tilt and a nod (e.g. -3 6) so a moving head never opens a gap."""
import sys, os, argparse, numpy as np, cv2

a = argparse.ArgumentParser()
a.add_argument("scene"); a.add_argument("out"); a.add_argument("head", nargs="?", default="NEUTRAL")
a.add_argument("tilt", nargs="?", type=float, default=0.0); a.add_argument("nod", nargs="?", type=float, default=0.0)
a.add_argument("--zoom", choices=["body", "knot"], default="body")
o = a.parse_args()
out = os.path.abspath(o.out)
os.chdir(o.scene); sys.path.insert(0, ".")
from rig import Rig, render_layers, NECK_PIVOT, F_KNOT
r = Rig()
if o.head not in r.head: sys.exit("heads: %s" % ", ".join(r.head))
Z, box, cols = (0.62, (520, 420, 260, 230), 6) if o.zoom == "body" else (2.2, (130, 95, 65, 55), 6)
tiles = []
for n in r.torso:
    hm = cv2.getRotationMatrix2D(NECK_PIVOT, o.tilt, 1.0); hm[1, 2] += o.nod
    V = np.array([[Z, 0, -Z * (F_KNOT[0] - box[2])], [0, Z, -Z * (F_KNOT[1] - box[3])], [0, 0, 1]], float)
    im = render_layers(r.layers(n, o.head, head_M=hm), V, (int(box[0] * Z), int(box[1] * Z)))
    img = (im[..., :3] + np.float32([255, 0, 255]) * (1 - im[..., 3:4])).astype(np.uint8)
    cv2.putText(img, n[:16], (4, 16), 0, 0.5, (0, 0, 0), 2); tiles.append(img)
rows = [np.hstack(tiles[i:i + cols] + [np.zeros_like(tiles[0])] * (cols - len(tiles[i:i + cols])))
        for i in range(0, len(tiles), cols)]
img = np.vstack(rows)
if img.shape[1] > 2400: img = cv2.resize(img, None, fx=2400 / img.shape[1], fy=2400 / img.shape[1], interpolation=cv2.INTER_AREA)
cv2.imwrite(out, img, [cv2.IMWRITE_JPEG_QUALITY, 90]); print(out)

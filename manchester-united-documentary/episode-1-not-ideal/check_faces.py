"""Every drawing's face at REST / AI / O / blink / look / brow / tilt, cropped to its head -> build/faces_check.jpg
python3 check_faces.py name [name ...]"""
import sys, os, numpy as np, cv2
from PIL import Image
import cast
names = sys.argv[1:]
rows = []
for n in names:
    d = cast.get(n)
    spec = cast.D[n]
    tiles = []
    for st in [dict(), dict(vis="AI"), dict(vis="O"), dict(blink=1.0), dict(lookx=1.0), dict(brow=-1.0, smile=-0.9), dict(tilt=6, nod=3)]:
        base = d.base(1.0).copy()
        p = d.patch(1.0, st)
        x0, y0, pm = p
        h, w = pm.shape[:2]
        base[y0:y0 + h, x0:x0 + w] = pm
        c = base[y0:y0 + h, x0:x0 + w]
        bg = np.zeros_like(c[..., :3]); bg[...] = (1, 0, 1)
        im = c[..., :3] + bg * (1 - c[..., 3:4])
        im = (np.clip(im, 0, 1) * 255).astype(np.uint8)
        k = 220 / im.shape[0]; im = cv2.resize(im, None, fx=k, fy=k, interpolation=cv2.INTER_AREA)
        tiles.append(im)
    row = np.hstack([np.pad(t, ((0, 0), (0, 6), (0, 0))) for t in tiles])
    cv2.putText(row, n, (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    rows.append(row)
W = max(r.shape[1] for r in rows)
rows = [np.pad(r, ((0, 6), (0, W - r.shape[1]), (0, 0))) for r in rows]
out = np.vstack(rows)
Image.fromarray(out).save("build/faces_check.jpg", quality=85)
print(out.shape)

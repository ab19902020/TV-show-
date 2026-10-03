"""contact.py OUT.jpg T [T ...] [--cols N] : a labelled contact sheet of stills (render.py still first)"""
import sys, cv2, numpy as np, os
a = sys.argv[1:]; out = a[0]; cols = 6
ts = []
i = 1
while i < len(a):
    if a[i] == "--cols": cols = int(a[i + 1]); i += 2; continue
    ts.append(float(a[i])); i += 1
tiles = []
for t in ts:
    f = f"build/stills/still_{t:06.2f}.jpg"
    if not os.path.exists(f): os.system(f"python3 render.py still {t} > /dev/null")
    im = cv2.resize(cv2.imread(f), (360, 640))
    cv2.putText(im, f"{t:.2f}", (8, 28), 0, 0.8, (0, 255, 255), 2); tiles.append(im)
while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
cv2.imwrite(out, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(out)

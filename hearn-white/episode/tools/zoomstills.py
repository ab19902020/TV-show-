"""zoomstills.py OUT.jpg t1:x0,y0,x1,y1 t2:... : 1280x720 stills, each cropped (in 1280x720 px) and enlarged to a
480 px tall tile, tiled 3 across"""
import sys, os, glob, subprocess, cv2, numpy as np
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = os.path.join(SP, "engine")
out, specs = os.path.abspath(sys.argv[1]), sys.argv[2:]
ts = [s.split(":")[0] for s in specs]
d = os.path.join(E, "episodes/the-undercard/build/stills")
subprocess.run(["rm", "-rf", d])
r = subprocess.run([sys.executable, "-m", "studio.film", "the-undercard", "still"] + ts, cwd=E,
                   env=dict(os.environ, EP_RES="1280x720"), capture_output=True, text=True)
if r.returncode:
    print(r.stderr[-2000:]); sys.exit(1)
tiles = []
for s in specs:
    t, box = s.split(":") if ":" in s else (s, "0,0,1280,720")
    p = os.path.join(d, f"still_{float(t):06.2f}.jpg")
    im = cv2.imread(p)
    x0, y0, x1, y1 = (int(v) for v in box.split(","))
    c = im[y0:y1, x0:x1]
    c = cv2.resize(c, (int(c.shape[1] * 480 / c.shape[0]), 480), interpolation=cv2.INTER_CUBIC)
    c = cv2.resize(c, (640, 480)) if c.shape[1] > 900 else c
    cv2.putText(c, t, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 4)
    cv2.putText(c, t, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    tiles.append(c)
w = max(t.shape[1] for t in tiles)
tiles = [np.pad(t, ((0, 0), (0, w - t.shape[1]), (0, 0))) for t in tiles]
while len(tiles) % 3:
    tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(out, np.vstack([np.hstack(tiles[i:i + 3]) for i in range(0, len(tiles), 3)]), [cv2.IMWRITE_JPEG_QUALITY, 88])
print(out, len(specs))

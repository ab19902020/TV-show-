"""render two stills per shot at 960x540 and tile them 3x3 (640x360 tiles) into view/qa/qa_NN.jpg"""
import sys, os, glob, subprocess, cv2, numpy as np
SP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = os.path.join(SP, "engine")
sys.path.insert(0, E)
os.chdir(E)
from studio.film import ep
ep.use("the-undercard")
sys.path.insert(0, str(ep.DIR))
from film import direction as D
first = int(sys.argv[1]) if len(sys.argv) > 1 else 0
last = int(sys.argv[2]) if len(sys.argv) > 2 else len(D.SHOTS)
ts, lab = [], {}
for s in D.SHOTS[first:last]:
    a, b = s["t"], s["end"]
    for t in sorted({round(a + min(0.25, (b - a) * 0.2), 2), round(a + (b - a) * 0.65, 2)}):
        ts.append(t)
        lab[f"{t:06.2f}"] = f"#{s['i'] + 1} {s.get('plate', s['kind'])} {t:.2f}"
out = os.path.join(E, "episodes/the-undercard/build/stills")
subprocess.run(["rm", "-rf", out])
env = dict(os.environ, EP_RES="960x540")
r = subprocess.run([sys.executable, "-m", "studio.film", "the-undercard", "still"] + [str(t) for t in ts], env=env,
                   capture_output=True, text=True)
if r.returncode:
    print(r.stderr[-3000:]); sys.exit(1)
ps = sorted(glob.glob(out + "/*.jpg"), key=lambda p: float(p.split("_")[-1][:-4]))
os.makedirs(os.path.join(SP, "view/qa"), exist_ok=True)
tiles = []
for p in ps:
    im = cv2.resize(cv2.imread(p), (640, 360), interpolation=cv2.INTER_AREA)
    k = p.split("_")[-1][:-4]
    t = lab.get(k, k)
    cv2.putText(im, t, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
    cv2.putText(im, t, (6, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    tiles.append(im)
n0 = first
for i in range(0, len(tiles), 9):
    g = tiles[i:i + 9]
    while len(g) < 9:
        g.append(np.zeros_like(tiles[0]))
    sheet = np.vstack([np.hstack(g[r * 3:r * 3 + 3]) for r in range(3)])
    cv2.imwrite(os.path.join(SP, f"view/qa/qa_{first:03d}_{i // 9:02d}.jpg"), sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])
print(len(tiles), "stills")

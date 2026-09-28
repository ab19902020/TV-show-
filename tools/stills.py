"""Contact sheets of rendered frames, to review a scene before a full render.

  python3 tools/stills.py <scene dir> <out.jpg> 3.4 9.2 27 ...          beats: 2 x 2 per sheet, labelled
  python3 tools/stills.py <scene dir> <out.jpg> --run 20.9 21.5 [--step 1] [--crop x0,y0,x1,y1]
                                                                        consecutive frames (walks, gestures)
Frames come from the scene's own `render.py still` (both scenes share that command), rendered in parallel.
Several sheets are written as out_0.jpg, out_1.jpg ... when there are more than --per frames."""
import sys, os, glob, subprocess, argparse, numpy as np, cv2

a = argparse.ArgumentParser()
a.add_argument("scene"); a.add_argument("out"); a.add_argument("t", nargs="+", type=float)
a.add_argument("--run", action="store_true"); a.add_argument("--step", type=int, default=1)
a.add_argument("--crop"); a.add_argument("--jobs", type=int, default=4); a.add_argument("--per", type=int, default=0)
o = a.parse_args()
FPS = 30
if o.run:
    i0, i1 = int(round(o.t[0] * FPS)), int(round(o.t[1] * FPS))
    frames = list(range(i0, i1 + 1, o.step))
else:
    frames = [int(round(t * FPS)) for t in o.t]
names = ["%.5f" % ((i + 0.02) / FPS) for i in frames]               # both renderers map this back to frame i
scene = os.path.abspath(o.scene)
for f in glob.glob(os.path.join(scene, "still_*.png")): os.remove(f)
ps = [subprocess.Popen(["python3", "render.py", "still"] + names[k::o.jobs], cwd=scene,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) for k in range(min(o.jobs, len(names)))]
for p in ps:
    err = p.communicate()[1]
    if p.returncode: sys.exit(err.decode()[-2000:])
tiles = []
for i, n in zip(frames, names):
    f = os.path.join(scene, "still_%s.png" % n)
    im = cv2.imread(f); os.remove(f)
    if o.crop:
        x0, y0, x1, y1 = [int(v) for v in o.crop.split(",")]; im = im[y0:y1, x0:x1]
    h = 360 if o.run else 540
    im = cv2.resize(im, (im.shape[1] * h // im.shape[0], h), interpolation=cv2.INTER_AREA)
    cv2.putText(im, "%.2f" % (i / FPS), (8, 28), 0, 0.8, (0, 255, 255), 2)
    tiles.append(im)
cols = 6 if o.run else 2
per = o.per or (cols * 4 if o.run else 4)
root, ext = os.path.splitext(o.out)
for s in range(0, len(tiles), per):
    chunk = tiles[s:s + per]
    rows = [np.hstack(chunk[r:r + cols] + [np.zeros_like(chunk[0])] * (cols - len(chunk[r:r + cols])))
            for r in range(0, len(chunk), cols)]
    path = o.out if len(tiles) <= per else "%s_%d%s" % (root, s // per, ext)
    cv2.imwrite(path, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(path)

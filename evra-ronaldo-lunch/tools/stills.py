"""Frames of the film at the given times, as one contact sheet: python3 tools/stills.py out.jpg T [T ...] [--width 540] [--cols 6]
--run T0 T1 [--step N]: every Nth frame between T0 and T1 instead. --crop x0,y0,x1,y1 (output px at --width)."""
import sys, os, argparse, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
OUT = os.path.abspath(sys.argv[1]); os.chdir(ROOT)
import numpy as np, cv2
from PIL import Image, ImageDraw
p = argparse.ArgumentParser(); p.add_argument('out'); p.add_argument('t', nargs='*', type=float)
p.add_argument('--width', type=int, default=540); p.add_argument('--cols', type=int, default=6); p.add_argument('--run', nargs=2, type=float)
p.add_argument('--step', type=int, default=1); p.add_argument('--crop'); p.add_argument('--cell', type=int, default=0)
a = p.parse_args()
cv2.setNumThreads(4)
from direction import Film
f = Film(a.width)
ts = a.t if not a.run else [i / 30 for i in range(int(round(a.run[0] * 30)), int(round(a.run[1] * 30)) + 1, a.step)]
ims = []
for t in ts:
    im = f.render(t)
    if a.crop: x0, y0, x1, y1 = map(int, a.crop.split(',')); im = im[y0:y1, x0:x1]
    ims.append(Image.fromarray(im))
cw = a.cell or ims[0].width; ch = int(round(ims[0].height * cw / ims[0].width)); cols = min(a.cols, len(ims))
out = Image.new('RGB', (cw * cols, (ch + 18) * math.ceil(len(ims) / cols)), '#111'); d = ImageDraw.Draw(out)
for i, (t, im) in enumerate(zip(ts, ims)):
    x, y = (i % cols) * cw, (i // cols) * (ch + 18); out.paste(im.resize((cw, ch), Image.Resampling.LANCZOS), (x, y))
    d.text((x + 4, y + ch + 3), f'{t:.2f}', fill='white')
out.save(OUT, quality=90); print(OUT, len(ims))

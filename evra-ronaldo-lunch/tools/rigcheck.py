"""Every rigged drawing on magenta, posed three ways (rest | head tilted and nodded + blink | limbs swung), with the head
layer box drawn: check the head sits on the neck with no gap and nothing is see-through.  python3 tools/rigcheck.py out.jpg [names]"""
import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
OUT = os.path.abspath(sys.argv[1]); os.chdir(ROOT)
import numpy as np, cv2
from PIL import Image, ImageDraw
import engine as E, performance as perf
from cast import CAST, actor
names = sys.argv[2:] or list(CAST)
cells = []
for n in names:
    a = actor(n); hh = 400; W = 330
    row = []
    for mode in range(3):
        d = np.zeros((hh + 20, W, 3), np.float32); d[:] = (1, 0, 1)
        cam = np.eye(3); s = hh / a.hh
        h = hh * .95
        kw = {}
        if mode == 1: kw = dict(tilt=3, nod=2, life=0)
        if mode == 2: kw = dict(limbs={k: 10 for k in a.limbs}, lean=3, life=0)
        if mode == 0: kw = dict(life=0)
        perf.EXTRA_BLINKS[a.who] = [(0.0, 10.)] if mode == 1 else []
        a.draw(d, cam, W / 2, hh + 5, h, 0.05, **kw)
        row.append(np.uint8(np.clip(d * 255, 0, 255)))
    im = Image.fromarray(np.hstack(row)); dr = ImageDraw.Draw(im)
    dr.text((4, 4), f'{n} span={a.span and round(a.span,1)} ref={a.ref:.2f} eyes={len(a.eyes0)} limbs={list(a.limbs)}', fill='white')
    cells.append(im)
cols = 2; w, h0 = cells[0].size
out = Image.new('RGB', (w * cols, h0 * ((len(cells) + cols - 1) // cols)), 'black')
for i, c in enumerate(cells): out.paste(c, ((i % cols) * w, (i // cols) * h0))
out.save(OUT, quality=88); print(OUT, out.size)

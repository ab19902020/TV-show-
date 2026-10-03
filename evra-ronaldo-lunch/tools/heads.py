"""Detect the eyes of every part and propose the head layer box (sheet px); draw both for checking.
python3 tools/heads.py out.jpg [parts...]  -> prints  name: eyes [(x, y, r)], box"""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ROOT)
OUT = os.path.abspath(sys.argv[1]); os.chdir(ROOT)
import numpy as np, cv2
from PIL import Image, ImageDraw
from engine import META, part, eyes_in
names = sys.argv[2:] or [n for n in META if not META[n]['sheet'] == 'props']
cells = []
for n in names:
    a = part(n); h, w = a.shape[:2]; k = META[n]['scale']; ox, oy = META[n]['off']
    e = eyes_in(a, 0, h * (0.62 if n.startswith(('eb_', 'rb_')) else 0.42))
    E = [((x / k + ox), (y / k + oy), max(rx, ry) / k) for x, y, rx, ry in e]
    if len(E) >= 2:
        span = abs(E[1][0] - E[0][0]); cy = (E[0][1] + E[1][1]) / 2
        box = (min(p[0] for p in E) - 1.45 * span, oy, max(p[0] for p in E) + 1.25 * span, cy + 1.7 * span)
    else: box = None
    print(n, [tuple(round(v) for v in p) for p in E], None if box is None else tuple(round(v) for v in box))
    bg = Image.new('RGBA', (w, h), (255, 0, 255, 255)); bg.alpha_composite(Image.fromarray(a)); im = bg.convert('RGB'); d = ImageDraw.Draw(im)
    for x, y, rx, ry in e: d.ellipse([x - rx, y - ry, x + rx, y + ry], outline=(0, 255, 0), width=6)
    if box: d.rectangle([(box[0] - ox) * k, (box[1] - oy) * k, (box[2] - ox) * k, (box[3] - oy) * k], outline=(0, 255, 255), width=8)
    im.thumbnail((300, 420)); cells.append((n, im))
cols = 8; out = Image.new('RGB', (cols * 300, ((len(cells) + cols - 1) // cols) * 440), 'white'); d = ImageDraw.Draw(out)
for i, (n, im) in enumerate(cells):
    x, y = (i % cols) * 300, (i // cols) * 440; out.paste(im, (x, y)); d.text((x + 4, y + 424), n, fill='black')
out.save(OUT, quality=88)

"""Zoom into a part around a sheet box with a sheet-coordinate grid every `step` px (labels every 5 steps).
python3 tools/zoom.py out.png part x0 y0 x1 y1 [step] [px per sheet px]"""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
out, n = sys.argv[1], sys.argv[2]; x0, y0, x1, y1 = map(float, sys.argv[3:7])
step = float(sys.argv[7]) if len(sys.argv) > 7 else 5; z = float(sys.argv[8]) if len(sys.argv) > 8 else 6
m = json.load(open(os.path.join(ROOT, 'build/parts/meta.json')))[n]; k = m['scale']; ox, oy = m['off']
a = Image.open(os.path.join(ROOT, 'build/parts', n + '.png')); bg = Image.new('RGBA', a.size, (255, 0, 255, 255)); bg.alpha_composite(a)
im = bg.convert('RGB').crop((int((x0 - ox) * k), int((y0 - oy) * k), int((x1 - ox) * k), int((y1 - oy) * k)))
im = im.resize((int((x1 - x0) * z), int((y1 - y0) * z)), Image.Resampling.LANCZOS); d = ImageDraw.Draw(im)
x = (x0 // step + 1) * step
while x < x1:
    X = (x - x0) * z; big = abs(x / (5 * step) - round(x / (5 * step))) < 1e-6
    d.line([(X, 0), (X, im.height)], fill=(0, 0, 255) if big else (0, 200, 0)); 
    if big: d.text((X + 2, 2), f'{x:g}', fill=(255, 255, 0))
    x += step
y = (y0 // step + 1) * step
while y < y1:
    Y = (y - y0) * z; big = abs(y / (5 * step) - round(y / (5 * step))) < 1e-6
    d.line([(0, Y), (im.width, Y)], fill=(0, 0, 255) if big else (0, 200, 0))
    if big: d.text((2, Y + 2), f'{y:g}', fill=(255, 255, 0))
    y += step
im.save(out); print(out, im.size)

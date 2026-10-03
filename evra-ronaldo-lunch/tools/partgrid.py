"""A cut part on magenta with its sheet-coordinate grid (every 10 px, labels every 50): find seed points and landmarks.
python3 tools/partgrid.py out.png part [zoom]"""
import sys, os, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
out, n = sys.argv[1], sys.argv[2]; z = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5
meta = json.load(open(os.path.join(ROOT, 'build/parts/meta.json')))[n]; k = meta['scale']; ox, oy = meta['off']
a = Image.open(os.path.join(ROOT, 'build/parts', n + '.png')); bg = Image.new('RGBA', a.size, (255, 0, 255, 255)); bg.alpha_composite(a)
im = bg.convert('RGB').resize((int(a.width * z), int(a.height * z)), Image.Resampling.LANCZOS); d = ImageDraw.Draw(im)
f = k * z
for x in range(int(ox) // 10 * 10 + 10, int(ox + a.width / k) + 1, 10):
    X = (x - ox) * f; d.line([(X, 0), (X, im.height)], fill=(0, 0, 255) if x % 50 == 0 else (0, 190, 0), width=1)
    if x % 50 == 0: d.text((X + 2, 2), str(x), fill=(255, 255, 0))
for y in range(int(oy) // 10 * 10 + 10, int(oy + a.height / k) + 1, 10):
    Y = (y - oy) * f; d.line([(0, Y), (im.width, Y)], fill=(0, 0, 255) if y % 50 == 0 else (0, 190, 0), width=1)
    if y % 50 == 0: d.text((2, Y + 2), str(y), fill=(255, 255, 0))
im.save(out); print(out, im.size)

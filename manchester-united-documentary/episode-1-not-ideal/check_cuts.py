"""Contact sheet of every part's 1x cut on magenta (before upscaling) -> build/cuts_check_<n>.jpg"""
import sys, numpy as np
from PIL import Image, ImageDraw
import parts
names = [n for n in parts.SPEC if not sys.argv[1:] or any(n.startswith(p) for p in sys.argv[1:])]
sheets = {}
tiles = []
for n in names:
    sp = parts.SPEC[n]
    if sp["src"] not in sheets: sheets[sp["src"]] = parts.load(sp["src"])[0]
    rgb, a, off = parts.cut(n, sp, sheets)
    mag = np.zeros_like(rgb); mag[...] = (255, 0, 255)
    im = (rgb * a[..., None] + mag * (1 - a[..., None])).astype(np.uint8)
    t = Image.fromarray(im); t.thumbnail((260, 260)); tiles.append((n, t))
W = 270; cols = 7
for k in range(0, len(tiles), 42):
    chunk = tiles[k:k + 42]
    rows = (len(chunk) + cols - 1) // cols
    s = Image.new("RGB", (W * cols, 285 * rows), (40, 40, 40)); d = ImageDraw.Draw(s)
    for i, (n, t) in enumerate(chunk):
        x, y = (i % cols) * W, (i // cols) * 285
        s.paste(t, (x + 5, y + 20)); d.text((x + 5, y + 4), n, fill=(255, 255, 0))
    s.save(f"build/cuts_check_{k // 42}.jpg", quality=85); print(f"build/cuts_check_{k // 42}.jpg", len(chunk))

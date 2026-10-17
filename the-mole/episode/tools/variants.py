"""The costume changes, painted onto the characters' own pose drawings (1x, before they are upscaled):

  Jason Wilcox in a Leeds top: his black United zip top turned white (its shading kept, the ink kept), the red
  sleeve stripes royal blue, the United badge swapped for a little blue-and-yellow Leeds shield, the adidas mark
  gone. The back view gets WILCOX across the shoulders and a signature in marker ("To Jason. Love, Jason. x").
  -> library/characters/jason-wilcox/reference/variants/leeds-<pose>.png

  Lisandro Martinez in camouflage paint: two dark green-brown stripes under each eye.
  -> library/characters/lisandro-martinez/reference/variants/camo-<pose>.png

  Omar Berrada in a sky-blue Manchester City scarf (his hero drawing, arms folded, cut from his model sheet).
  -> library/characters/omar-berrada/reference/variants/city-hero.png

python3 episodes/the-mole/tools/variants.py"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[3]
CH = ROOT / "library" / "characters"
FONTS = ROOT / "library" / "fonts"

# the zip top's rows on each pose (1x px): from under the chin to the hem
TOP = {"pockets": (113, 241), "shrug": (114, 240), "shrug2": (114, 236), "point": (113, 240), "crossarms": (114, 240),
       "back": (100, 236)}
BLUE = np.array([29, 66, 138], np.float32)
YELLOW = np.array([255, 205, 0], np.float32)


def lum(a):
    return a[..., 0] * 0.3 + a[..., 1] * 0.59 + a[..., 2] * 0.11


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def leeds(pose):
    im = np.asarray(Image.open(CH / "jason-wilcox/reference/poses" / f"{pose}.png").convert("RGBA")).astype(np.float32)
    rgb, al = im[..., :3], im[..., 3]
    y0, y1 = TOP[pose]
    band = np.zeros(al.shape, bool)
    band[y0:y1] = True
    band &= al > 20
    l = lum(rgb)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    # the United badge (orange, yellow, red, in a small cluster on the chest) and the red stripes
    warm = band & (r > 150) & (r - b > 70)
    red = warm & (g < 60) & (b < 60)
    # the United badge and the adidas mark: the biggest saturated warm blob (most yellow) and the biggest white blob
    # on the chest. Skin has blue in it; neither mark does.
    from scipy import ndimage
    chest = np.zeros(al.shape, bool)
    chest[y0 + 8:y0 + 70] = True

    def blob(mask, score):
        lab, n = ndimage.label(ndimage.binary_dilation(mask & chest, iterations=2))
        if not n or pose == "back":
            return None
        best = max(range(1, n + 1), key=lambda i: score[lab == i].sum())
        ys, xs = np.nonzero(lab == best)
        return xs.min() - 1, ys.min() - 1, xs.max() + 2, ys.max() + 2

    sat = (r - b > 110) & (b < 70) & (r > 170)
    badge_box = blob(sat, ((r > 200) & (g > 140) & (b < 70)).astype(float))
    greyish = (np.abs(r - b) < 30) & (np.abs(r - g) < 30)
    logo_box = blob(greyish & (l > 165), np.ones(l.shape))
    # black cloth -> white cloth: the ink (darkest) stays, the fill turns white with its folds kept as soft grey
    dark = band & (l < 75) & ~warm
    t = smooth(l, 9.0, 22.0)                                   # 0 on the ink, 1 on the cloth
    white = np.clip(224 + (l - 28) * 1.1, 196, 250)
    shade = white[..., None] * np.array([1.0, 1.0, 1.02])
    out = rgb.copy()
    m = dark[..., None]
    out = np.where(m, rgb * (1 - t[..., None]) + shade * t[..., None], out)
    hole = np.zeros(al.shape, np.uint8)                        # both painted over with the cloth round them
    for bx in (logo_box, badge_box):
        if bx:
            x0, y0b, x1, y1b = bx
            hole[y0b:y1b, x0:x1] = 255
    if hole.any():
        import cv2
        out = cv2.inpaint(np.clip(out, 0, 255).astype(np.uint8), hole, 4, cv2.INPAINT_TELEA).astype(np.float32)
    # red stripes -> royal blue, shaded as they were
    k = (lum(rgb) / 110.0)[..., None]
    out = np.where(red[..., None], np.clip(BLUE * (0.55 + 0.6 * k), 0, 255), out)
    # the badge -> a Leeds shield where the United one was
    img = Image.fromarray(np.dstack([out, al]).astype(np.uint8))
    if badge_box:
        x0, ya, x1, yb = badge_box
        cx, cy = (x0 + x1) / 2, (ya + yb) / 2
        w = min(16, max(10, x1 - x0))
        d = ImageDraw.Draw(img)
        x0, x1, ya, yb = cx - w / 2, cx + w / 2, cy - w / 2, cy + w / 2
        d.polygon([(x0, ya), (x1, ya), (x1, cy + w * 0.1), (cx, yb + 1), (x0, cy + w * 0.1)], fill=(29, 66, 138, 255),
                  outline=(255, 205, 0, 255))
        d.ellipse([cx - w * 0.22, cy - w * 0.28, cx + w * 0.22, cy + w * 0.16], fill=(250, 250, 250, 255))
    if pose == "back":
        img = name_on_back(img, y0)
    out_dir = CH / "jason-wilcox/reference/variants"
    out_dir.mkdir(parents=True, exist_ok=True)
    img.save(out_dir / f"leeds-{pose}.png")
    return img


def name_on_back(img, y0):
    """WILCOX across the shoulders, and his own autograph to himself in black marker"""
    W, H = img.size
    a = np.asarray(img)[..., 3]
    cols = np.nonzero(a[y0 + 30] > 20)[0]
    cx = (cols.min() + cols.max()) / 2
    big = Image.new("RGBA", (W * 4, H * 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    f = ImageFont.truetype(str(FONTS / "BebasNeue-Regular.ttf"), 120)
    d.text((cx * 4, (y0 + 36) * 4), "WILCOX", font=f, fill=(29, 66, 138, 255), anchor="mm")
    hand = ImageFont.truetype(str(next(FONTS.glob("Inter*.ttf"))), 46)
    for i, line in enumerate(["To Jason.", "Love, Jason. x"]):
        d.text((cx * 4 + 6, (y0 + 66 + 15 * i) * 4), line, font=hand, fill=(20, 20, 20, 255), anchor="mm")
    d.line([(cx * 4 - 150, (y0 + 98) * 4), (cx * 4 + 10, (y0 + 92) * 4), (cx * 4 + 160, (y0 + 100) * 4)],
           fill=(20, 20, 20, 255), width=6)
    small = big.resize((W, H), Image.LANCZOS)
    out = img.copy()
    out.alpha_composite(small)
    out.putalpha(img.getchannel("A"))
    return out


def eyes_of(im):
    """the two eye whites of a front-facing drawing (1x): [(cx, cy, w, h)] left to right"""
    from scipy import ndimage
    a = np.asarray(im).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3]
    ys = np.nonzero(al.max(1) > 20)[0]
    top, h = ys.min(), ys.max() - ys.min()
    mx, mn = rgb.max(2), rgb.min(2)
    white = (mn > 205) & (mx - mn < 30) & (al > 200)
    white[:top] = False
    white[int(top + 0.36 * h):] = False
    lab, n = ndimage.label(white)
    blobs = []
    for i in range(1, n + 1):
        yy, xx = np.nonzero(lab == i)
        if len(xx) > 12:
            blobs.append((len(xx), xx.mean(), yy.mean(), np.ptp(xx) + 1, np.ptp(yy) + 1))
    blobs = sorted(blobs, reverse=True)[:2]
    return sorted([(b[1], b[2], b[3], b[4]) for b in blobs])


CAMO = ["crouch", "crossarms", "point", "shrug", "facepalm", "stand"]


def camo(pose):
    """two stripes of camouflage paint under each eye, olive over brown, in rough brush strokes"""
    im = Image.open(CH / "lisandro-martinez/reference/poses" / f"{pose}.png").convert("RGBA")
    W, H = im.size
    K = 6
    big = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    ey = eyes_of(im)
    if pose == "facepalm":                       # eyes behind his hand: the stripes go on the cheek below it
        ey = [(79.0, 96.0, 14, 10), (111.0, 96.0, 14, 10)]
    mid = sum(e[0] for e in ey) / len(ey)
    for cx, cy, w, h in ey:
        out_ = 1.0 if cx > mid else -1.0                      # each cheek's stripes run out from under the eye
        for j, col in enumerate([(52, 82, 26, 245), (66, 46, 26, 245)]):
            y = cy + h * 0.5 + 2.5 + j * 5.0
            xa, xb = cx - out_ * w * 0.05, cx + out_ * w * 0.8
            pts = [(xa * K, (y + 0.4) * K), (xb * K, (y - 1.2) * K), (xb * K, (y + 2.0) * K), (xa * K, (y + 3.6) * K)]
            d.polygon(pts, fill=col)
    big = big.filter(ImageFilter.GaussianBlur(K * 0.35))
    paint = big.resize((W, H), Image.LANCZOS)
    pa = np.asarray(paint).astype(np.float32)
    base = np.asarray(im).astype(np.float32)
    skin = (base[..., 0] > 170) & (base[..., 0] - base[..., 2] > 40) & (base[..., 3] > 200)   # only on his skin
    a = pa[..., 3:4] / 255.0 * skin[..., None]
    out = base.copy()
    out[..., :3] = base[..., :3] * (1 - a) + pa[..., :3] * a
    od = CH / "lisandro-martinez/reference/variants"
    od.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out.astype(np.uint8)).save(od / f"camo-{pose}.png")
    return ey


def city():
    """Omar's hero drawing cut off his sheet (the paper flood-filled away) with a sky-blue City scarf round his neck"""
    import cv2
    sheet = np.asarray(Image.open(CH / "omar-berrada/reference/model-sheet.png").convert("RGB"))
    x0, y0, x1, y1 = 18, 98, 292, 864
    c = sheet[y0:y1, x0:x1].copy()
    paper = np.zeros((c.shape[0] + 2, c.shape[1] + 2), np.uint8)
    flood = c.copy()
    for seed in [(0, 0), (c.shape[1] - 1, 0), (0, c.shape[0] - 1), (c.shape[1] - 1, c.shape[0] - 1), (5, 300)]:
        cv2.floodFill(flood, paper, seed, (255, 0, 255), (14, 14, 14), (14, 14, 14),
                      cv2.FLOODFILL_FIXED_RANGE | cv2.FLOODFILL_MASK_ONLY | (255 << 8))
    al = np.where(paper[1:-1, 1:-1] > 0, 0, 255).astype(np.uint8)
    al = cv2.morphologyEx(al, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    im = Image.fromarray(np.dstack([c, al]))
    K = 4
    big = Image.new("RGBA", (im.width * K, im.height * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    sky, ink, wh = (108, 171, 221, 255), (25, 25, 30, 255), (250, 250, 250, 255)

    def poly(pts, fill):
        q = [(x * K, y * K) for x, y in pts]
        d.polygon(q, fill=fill)
        d.line(q + [q[0]], fill=ink, width=int(2.2 * K), joint="curve")
    # the wrap round his collar, then two tails down his front over the folded arms
    poly([(112, 248), (150, 262), (190, 250), (214, 262), (200, 292), (150, 300), (100, 290), (92, 262)], sky)
    poly([(118, 284), (146, 292), (140, 372), (110, 366)], sky)
    poly([(160, 292), (188, 286), (196, 360), (166, 368)], sky)
    for y in (318, 342):
        poly([(114, y - 3), (143, y), (142, y + 7), (113, y + 4)], wh)
        poly([(162, y + 2), (191, y - 1), (192, y + 6), (163, y + 9)], wh)
    for xs in range(112, 142, 6):                           # fringe
        d.line([(xs * K, 368 * K), (xs * K - 4, 378 * K)], fill=sky, width=int(2.4 * K))
    for xs in range(168, 196, 6):
        d.line([(xs * K, 368 * K), (xs * K + 4, 378 * K)], fill=sky, width=int(2.4 * K))
    small = big.resize(im.size, Image.LANCZOS)
    out = im.copy()
    out.alpha_composite(small)
    od = CH / "omar-berrada/reference/variants"
    od.mkdir(parents=True, exist_ok=True)
    out.save(od / "city-hero.png")


def scream(src, dst, mouth, ed):
    """the same drawing with its mouth wide open in a scream: a dark oval, the top teeth, the tongue"""
    im = Image.open(src).convert("RGBA")
    K = 8
    W, H = im.size
    big = Image.new("RGBA", (W * K, H * K), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    cx, cy = mouth
    rx, ry = 0.36 * ed, 0.42 * ed
    box = [(cx - rx) * K, (cy - ry * 0.55) * K, (cx + rx) * K, (cy + ry * 1.45) * K]
    d.ellipse(box, fill=(60, 14, 18, 255), outline=(20, 12, 10, 255), width=int(2.2 * K))
    d.chord([box[0] + 2 * K, box[1] + 2 * K, box[2] - 2 * K, box[1] + (box[3] - box[1]) * 0.55], 200, 340,
            fill=(250, 250, 248, 255))
    d.ellipse([(cx - rx * 0.62) * K, (cy + ry * 0.7) * K, (cx + rx * 0.62) * K, (cy + ry * 1.35) * K],
              fill=(214, 92, 104, 255))
    small = big.resize((W, H), Image.LANCZOS)
    out = im.copy()
    out.alpha_composite(small)
    out.putalpha(im.getchannel("A"))
    out.save(dst)


def main():
    scream(CH / "jason-wilcox/reference/variants/leeds-pockets.png",
           CH / "jason-wilcox/reference/variants/leeds-scream.png", (77.7, 118.0), 30.6)
    scream(CH / "lisandro-martinez/reference/poses/stand.png",
           CH / "lisandro-martinez/reference/variants/scream-stand.png", (95.0, 127.0), 38.7)
    for pose in TOP:
        leeds(pose)
        print("leeds", pose)
    for pose in CAMO:
        print("camo", pose, camo(pose))
    scream(CH / "lisandro-martinez/reference/variants/camo-stand.png",
           CH / "lisandro-martinez/reference/variants/camo-scream.png", (95.0, 127.0), 38.7)
    city()
    print("city scarf")


if __name__ == "__main__":
    main()

"""The four small props, drawn flat in the house style (bold black outline, flat colour, soft shade):
the suggestions shoebox with its slot and STAFF SUGGESTIONS label, the slip, Gareth's notebook and his biro.

Each prop is drawn once at R pixels per world pixel and returned as (rgb float, alpha float, anchor) where the anchor
is the point that is placed (the box's bottom centre, the slip's held corner, the pen's grip...).
"""
import numpy as np, cv2
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

R = 4
INK = (24, 20, 22)
MARKER = "fonts/PermanentMarker-Regular.ttf"
HAND = "fonts/ReenieBeanie.ttf"


def _canvas(w, h):
    return Image.new("RGBA", (int(w * R), int(h * R)), (0, 0, 0, 0))


def _out(im, anchor):
    a = np.asarray(im).astype(np.float32)
    return a[..., :3].copy(), a[..., 3] / 255.0, np.array(anchor, np.float64) * R


def _poly(d, pts, fill, lw=2.6):
    P = [(x * R, y * R) for x, y in pts]
    d.polygon(P, fill=fill)
    d.line(P + [P[0]], fill=INK, width=int(lw * R), joint="curve")


@lru_cache(maxsize=None)
def box():
    """shoebox seen from the front and a little above: 116 x 70 world px, anchor = bottom centre"""
    W, H = 124, 76
    im = _canvas(W, H)
    d = ImageDraw.Draw(im)
    x0, x1 = 6, 118
    top0, top1, front0, bot = 8, 22, 22, 70
    # soft shadow on the desk
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).ellipse([(x0 - 2) * R, (bot - 5) * R, (x1 + 4) * R, (bot + 4) * R], fill=90)
    sh = sh.resize(im.size)
    shadow = Image.new("RGBA", im.size, (40, 25, 15, 0))
    shadow.putalpha(sh.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(3 * R)))
    im.alpha_composite(shadow)
    d = ImageDraw.Draw(im)
    kraft, kraft_top, kraft_band = (206, 164, 112), (224, 188, 140), (188, 146, 96)
    # box body (front face) and the lid's top
    _poly(d, [(x0 + 1, front0), (x1 - 1, front0), (x1 - 1, bot), (x0 + 1, bot)], kraft)
    _poly(d, [(x0 + 7, top0), (x1 - 7, top0), (x1, top1), (x0, top1)], kraft_top)
    # lid's front band
    _poly(d, [(x0, top1), (x1, top1), (x1, top1 + 9), (x0, top1 + 9)], kraft_band)
    # slot
    cx = (x0 + x1) / 2
    d.rounded_rectangle([(cx - 22) * R, (top0 + 4.2) * R, (cx + 22) * R, (top0 + 8.4) * R], radius=2 * R, fill=INK)
    # shading toward the bottom of the front
    g = Image.new("RGBA", im.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for i in range(12):
        y = bot - 12 + i
        gd.line([(x0 + 3) * R, y * R, (x1 - 3) * R, y * R], fill=(60, 35, 10, int(4 + i * 3.2)), width=R)
    im.alpha_composite(g)
    # paper label, slightly crooked, hand lettered
    lab = Image.new("RGBA", (int(78 * R), int(30 * R)), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lab)
    ld.rectangle([R, R, 77 * R, 29 * R], fill=(250, 248, 238), outline=INK, width=int(1.6 * R))
    f1 = ImageFont.truetype(MARKER, int(9.5 * R))
    f2 = ImageFont.truetype(MARKER, int(7.6 * R))
    for txt, f, y in (("STAFF", f1, 3.0), ("SUGGESTIONS", f2, 15.0)):
        tw = ld.textlength(txt, font=f)
        ld.text(((78 * R - tw) / 2, y * R), txt, font=f, fill=(28, 36, 92))
    lab = lab.rotate(-2.2, resample=Image.BICUBIC, expand=True)
    im.alpha_composite(lab, (int((cx - lab.width / R / 2) * R), int(35 * R)))
    return _out(im, (cx, bot))


@lru_cache(maxsize=None)
def slip(fold=0.0):
    """the suggestion: open (fold=0) or folded once (fold=1). 38 x 24 world px open; anchor = middle of the
    bottom edge (where the fingers hold it)"""
    W, H = 44, 30
    im = _canvas(W, H)
    d = ImageDraw.Draw(im)
    x0, x1, y0, y1 = 3, 41, 3, 27
    # folding: the top half comes down over the bottom half
    hy = y0 + (y1 - y0) * 0.5 * fold
    paper = (252, 252, 246)
    _poly(d, [(x0, hy), (x1, hy), (x1, y1), (x0, y1)], paper, lw=1.8)
    if fold < 0.5:
        f = ImageFont.truetype(HAND, int(10 * R))
        txt = Image.new("RGBA", im.size, (0, 0, 0, 0))
        td = ImageDraw.Draw(txt)
        td.text(((x0 + 4) * R, (hy + 1.5) * R), "Fewer", font=f, fill=(30, 40, 110))
        td.text(((x0 + 9) * R, (hy + 10.5) * R), "meetings", font=f, fill=(30, 40, 110))
        im.alpha_composite(txt)
        d = ImageDraw.Draw(im)
        # the crease from being folded in the box
        cy = (y0 + y1) / 2
        d.line([(x0 + 1) * R, cy * R, (x1 - 1) * R, cy * R], fill=(200, 200, 196), width=int(0.8 * R))
    else:
        d.line([(x0 + 2) * R, (hy + 1.5) * R, (x1 - 2) * R, (hy + 1.5) * R], fill=(215, 215, 208), width=int(1.0 * R))
    return _out(im, ((x0 + x1) / 2, y1))


@lru_cache(maxsize=None)
def notebook():
    """Gareth's reporter's pad lying on the desk, seen from the front at a low angle: 64 x 22 world px,
    anchor = bottom centre"""
    W, H = 70, 26
    im = _canvas(W, H)
    d = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([4 * R, 20 * R, 68 * R, 25 * R], fill=(50, 30, 10, 70))
    im.alpha_composite(sh)
    d = ImageDraw.Draw(im)
    # cover edge (navy) under the page, page in perspective (narrower at the back)
    _poly(d, [(9, 4), (61, 4), (67, 22), (3, 22)], (44, 58, 110), lw=2.0)
    _poly(d, [(10, 4.5), (60, 4.5), (65, 20), (5, 20)], (250, 250, 242), lw=1.6)
    # ruled lines and Gareth's list
    for i, y in enumerate((9, 12.5, 16)):
        k = (y - 4.5) / 15.5
        xa, xb = 10 - 5 * k + 2, 60 + 5 * k - 2
        d.line([xa * R, y * R, xb * R, y * R], fill=(150, 185, 225), width=int(0.6 * R))
        d.line([(xa + 2) * R, (y - 1.1) * R, (xa + 2 + 18 + 7 * (i % 2)) * R, (y - 1.4) * R],
               fill=(40, 50, 120), width=int(0.9 * R))
    # spiral along the back edge
    for x in np.arange(13, 58, 4.2):
        d.ellipse([(x - 1.2) * R, 2.6 * R, (x + 1.2) * R, 6.0 * R], outline=INK, width=int(0.8 * R))
    return _out(im, (35, 22))


@lru_cache(maxsize=None)
def pen():
    """a clear biro with a blue cap, horizontal, 36 x 5 world px; anchor = grip point (40% from the tip)"""
    W, H = 40, 8
    im = _canvas(W, H)
    d = ImageDraw.Draw(im)
    # barrel
    d.rounded_rectangle([3 * R, 2.4 * R, 34 * R, 5.6 * R], radius=1.5 * R, fill=(236, 240, 246), outline=INK,
                        width=int(1.1 * R))
    # ink tube
    d.line([6 * R, 4 * R, 31 * R, 4 * R], fill=(60, 90, 170), width=int(0.7 * R))
    # cap end and tip
    d.rounded_rectangle([30 * R, 2.0 * R, 37 * R, 6.0 * R], radius=1.2 * R, fill=(40, 70, 170), outline=INK,
                        width=int(1.0 * R))
    d.polygon([(3 * R, 2.6 * R), (0.6 * R, 4 * R), (3 * R, 5.4 * R)], fill=(200, 200, 200), outline=INK)
    return _out(im, (14, 4))

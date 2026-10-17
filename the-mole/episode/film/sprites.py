"""The props, drawn in the house look (flat colours, a dark ink outline, a little shading): the pot plant Licho
hides in (and its football boots), the hedge, the binoculars, the white mug, the laptop, soil and pot shards.
Every sprite is an RGBA uint8 array with its anchor; they are drawn once and cached."""
import functools
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

INK = (24, 30, 22, 255)


def _outline(rgba, width, colour=INK):
    """an ink line round the sprite's silhouette, under its edge"""
    a = rgba[..., 3]
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * width + 1, 2 * width + 1))
    ring = cv2.dilate(a, k)
    out = np.zeros_like(rgba)
    out[..., :3] = colour[:3]
    out[..., 3] = ring
    fa = rgba[..., 3:4].astype(np.float32) / 255.0
    res = out.astype(np.float32)
    res[..., :3] = rgba[..., :3] * fa + res[..., :3] * (1 - fa)
    res[..., 3] = np.maximum(ring, rgba[..., 3])
    return res.astype(np.uint8)


def leaf(draw, base, ang, length, width, fill, rib, ink=INK, ink_w=5):
    """one long tropical leaf from base, pointing at ang degrees (0 = up, + = clockwise)"""
    bx, by = base
    a = math.radians(ang)
    ux, uy = math.sin(a), -math.cos(a)                 # along the leaf
    nx, ny = -uy, ux                                  # across it
    pts_l, pts_r, mid = [], [], []
    for i in range(25):
        u = i / 24
        bend = 0.18 * length * u * u                   # leaves droop towards their tips
        cx = bx + ux * length * u + (0.0 if abs(ang) < 8 else math.copysign(1, ang)) * bend * 0.6
        cy = by + uy * length * u + bend * (0.5 + 0.5 * abs(math.sin(a)))
        w = width * math.sin(math.pi * min(1.0, u * 1.08)) ** 0.8 * (1 - 0.15 * u)
        pts_l.append((cx + nx * w / 2, cy + ny * w / 2))
        pts_r.append((cx - nx * w / 2, cy - ny * w / 2))
        mid.append((cx, cy))
    poly = pts_l + pts_r[::-1]
    draw.polygon(poly, fill=fill, outline=ink)
    draw.line(poly + [poly[0]], fill=ink, width=ink_w, joint="curve")
    draw.line(mid[1:-2], fill=rib, width=max(2, ink_w // 2))


@functools.lru_cache(maxsize=2)
def plant(boots=False):
    """the pot plant: {"back": the back fronds, "pot": the pot (and the boots under it), "fl" / "fr": the front
    fronds, left and right, that part to show who is inside, "pivot": where they part from, "base": the foot of it
    all}, all on one 1200 x 2100 canvas. Drawn back, (whoever hides in it), pot, front fronds."""
    W, H = 1400, 2100
    greens = [(46, 120, 52), (62, 146, 60), (84, 170, 70), (38, 100, 44)]
    rib = (150, 200, 110)
    stem = (700, 1390)

    def layer(leaves):
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for ang, ln, wd, gi in leaves:
            leaf(d, stem, ang, ln, wd, greens[gi] + (255,), rib + (255,))
        return np.asarray(im).copy()
    back = layer([(-75, 560, 150, 3), (75, 560, 150, 3), (-50, 700, 180, 0), (50, 700, 180, 0), (-24, 860, 200, 1),
                  (26, 840, 190, 1), (0, 960, 210, 2), (-12, 900, 190, 3), (12, 900, 190, 3), (-95, 470, 130, 0),
                  (95, 470, 130, 0)])
    fl = layer([(-36, 680, 210, 2), (-62, 560, 190, 1), (-16, 820, 230, 0), (-5, 760, 200, 1)])
    fr = layer([(36, 680, 210, 2), (62, 560, 190, 1), (16, 820, 230, 0), (5, 760, 200, 1)])
    # the pot: terracotta, a rim, shading on its right
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    body = [(500, 1450), (900, 1450), (860, 1830), (540, 1830)]
    d.polygon(body, fill=(196, 104, 64, 255))
    d.polygon([(790, 1450), (900, 1450), (860, 1830), (780, 1830)], fill=(170, 86, 52, 255))
    d.line(body + [body[0]], fill=INK, width=9, joint="curve")
    d.rounded_rectangle([470, 1380, 930, 1470], radius=18, fill=(212, 120, 76, 255), outline=INK, width=9)
    d.ellipse([500, 1385, 900, 1425], fill=(70, 46, 30, 255))                   # soil
    pot = np.asarray(im).copy()
    if boots:                                                                # his boots under the pot
        bp = boot_pair()
        bh, bw = bp.shape[:2]
        s = 430 / bw
        bb = cv2.resize(bp, (int(bw * s), int(bh * s)), interpolation=cv2.INTER_AREA)
        y0, x0 = 1800, 700 - bb.shape[1] // 2
        reg = pot[y0:y0 + bb.shape[0], x0:x0 + bb.shape[1]].astype(np.float32)
        a = bb[..., 3:4].astype(np.float32) / 255.0
        reg[..., :3] = reg[..., :3] * (1 - a) + bb[..., :3] * a
        reg[..., 3] = np.maximum(reg[..., 3], bb[..., 3])
        pot[y0:y0 + bb.shape[0], x0:x0 + bb.shape[1]] = reg.astype(np.uint8)
    return dict(back=back, pot=pot, fl=fl, fr=fr, pivot=stem, base=(700, 1830 if not boots else 2000),
                size=(W, H))


@functools.lru_cache(maxsize=2)
def hedge(seed=3, W=2600, H=900):
    """a long clipped hedge: overlapping leafy clumps, three greens, darker underneath, ink round the top"""
    rng = np.random.default_rng(seed)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    top = 170
    d.rectangle([0, top + 120, W, H], fill=(44, 102, 44, 255))
    for i in range(int(W / 70) + 4):                                         # the clumps along its top
        x = i * 70 + rng.uniform(-20, 20)
        r = rng.uniform(90, 140)
        y = top + 90 + rng.uniform(-30, 25)
        d.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=(58, 128, 54, 255))
    arr = np.asarray(im).copy()
    arr = _outline(arr, 7)
    im = Image.fromarray(arr)
    d = ImageDraw.Draw(im)
    for _ in range(int(W * H / 1400)):                                        # leaf texture: little light and dark
        x, y = rng.uniform(0, W), rng.uniform(top, H)                         # arcs
        if np.asarray(im)[int(min(H - 1, y)), int(min(W - 1, x)), 3] < 250:
            continue
        r = rng.uniform(10, 22)
        light = rng.random() < 0.55 - 0.35 * (y - top) / (H - top)
        col = (96, 168, 74, 255) if light else (30, 78, 34, 255)
        a0 = rng.uniform(180, 300) if light else rng.uniform(0, 120)
        d.arc([x - r, y - r, x + r, y + r], a0, a0 + 110, fill=col, width=5)
    arr = np.asarray(im).astype(np.float32)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    arr[..., :3] *= 1.0 - 0.35 * np.clip((yy - 0.45) / 0.55, 0, 1)            # the shade under it
    return arr.astype(np.uint8)


@functools.lru_cache(maxsize=2)
def binoculars(view="front"):
    """black binoculars: "front" (lenses at us) or "side" (poking out of the hedge, pointing right)"""
    W, H = 700, 360
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if view == "front":
        for cx in (200, 500):
            d.ellipse([cx - 150, 30, cx + 150, 330], fill=(30, 32, 36, 255), outline=INK, width=10)
            d.ellipse([cx - 105, 75, cx + 105, 285], fill=(58, 92, 140, 255), outline=(10, 10, 12, 255), width=8)
            d.ellipse([cx - 60, 105, cx - 10, 150], fill=(230, 240, 255, 230))
        d.rectangle([330, 140, 370, 220], fill=(30, 32, 36, 255), outline=INK, width=6)
    else:
        for y0 in (40, 190):
            d.rounded_rectangle([60, y0, 640, y0 + 130], radius=30, fill=(30, 32, 36, 255), outline=INK, width=10)
            d.rectangle([560, y0 + 10, 650, y0 + 120], fill=(50, 54, 60, 255), outline=INK, width=8)
            d.ellipse([610, y0 + 25, 660, y0 + 105], fill=(58, 92, 140, 255), outline=INK, width=6)
    return np.asarray(im).copy()


@functools.lru_cache(maxsize=4)
def mug(colour=(246, 246, 246)):
    """a plain mug, handle on the right"""
    W, H = 420, 420
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([250, 110, 400, 300], fill=None, outline=INK, width=34)
    d.ellipse([250, 110, 400, 300], fill=None, outline=colour + (255,), width=18)
    d.rounded_rectangle([40, 60, 300, 400], radius=26, fill=colour + (255,), outline=INK, width=10)
    d.ellipse([40, 30, 300, 100], fill=(int(colour[0] * 0.8), int(colour[1] * 0.8), int(colour[2] * 0.8), 255),
              outline=INK, width=10)
    d.ellipse([60, 42, 280, 90], fill=(110, 70, 40, 255))                   # tea
    d.rectangle([220, 110, 280, 380], fill=(int(colour[0] * 0.88), int(colour[1] * 0.88), int(colour[2] * 0.9), 255))
    return np.asarray(im).copy()


def paste(img, spr, x, y, s=1.0, ang=0.0, anchor=None, alpha=1.0, flip=False):
    """composite an RGBA uint8 sprite into a float RGB frame: the sprite's anchor (sprite px; default its bottom
    centre) lands at screen (x, y), scaled by s, rotated by ang degrees (clockwise) about the anchor"""
    h, w = spr.shape[:2]
    ax, ay = anchor if anchor is not None else (w / 2, h)
    if flip:
        spr = spr[:, ::-1]
        ax = w - ax
    H, W = img.shape[:2]
    c, si = math.cos(math.radians(ang)) * s, math.sin(math.radians(ang)) * s
    A = np.float32([[c, -si, x - c * ax + si * ay], [si, c, y - si * ax - c * ay]])
    corners = np.float32([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]]) @ A.T
    x0, y0 = np.floor(corners.min(0)).astype(int)
    x1, y1 = np.ceil(corners.max(0)).astype(int)
    x0, y0, x1, y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if x1 <= x0 or y1 <= y0:
        return img
    A2 = A.copy()
    A2[0, 2] -= x0
    A2[1, 2] -= y0
    src = spr
    if s < 0.5:
        src = cv2.GaussianBlur(spr, (0, 0), 0.4 / s)
    f = cv2.warpAffine(src, A2, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                       borderValue=(0, 0, 0, 0)).astype(np.float32) / 255.0
    a = f[..., 3:4] * alpha
    img[y0:y1, x0:x1] = img[y0:y1, x0:x1] * (1 - a) + f[..., :3] * a
    return img


@functools.lru_cache(maxsize=1)
def boot_pair():
    """Licho's two football boots, cut from the bottom of his standing drawing"""
    from studio.paths import BUILD
    im = np.asarray(Image.open(BUILD / "film" / "lisandro-martinez" / "stand.png").convert("RGBA"))
    a = im[..., 3] > 20
    ys = np.nonzero(a.any(1))[0]
    y1 = ys.max()
    y0 = int(y1 - 0.105 * (ys.max() - ys.min()))
    c = im[y0:y1 + 1]
    xs = np.nonzero((c[..., 3] > 20).any(0))[0]
    return c[:, xs.min():xs.max() + 1].copy()

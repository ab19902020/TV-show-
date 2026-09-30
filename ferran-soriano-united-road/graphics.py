"""Everything drawn over the picture: the permanent UNITED ROAD / SATIRE - FICTIONAL DIALOGUE identifiers, the
opening ID card, the captions, the optional gag graphics named in the production sheet, and the end card.

House look (no broadcaster styling, no logos): white type, near-black cards, one red accent.
Portrait captions sit 70-82 % down the frame (clear of the bottom 15 % and the right edge); landscape captions
sit in the lower third. Gag cards in portrait go above his head in shot A (lots of headroom) and on the upper
chest in B/C; in landscape they sit in the empty left third of the frame."""
import functools, math, numpy as np
from PIL import Image, ImageDraw, ImageFont

RED = (200, 16, 46)
WHITE = (255, 255, 255)
CARD = (16, 18, 24)

@functools.lru_cache(maxsize=96)
def font(name, size, weight=700):
    f = ImageFont.truetype(f"fonts/{name}.ttf", int(round(size)))
    try:
        axes = f.get_variation_axes()
        vals = []
        for ax in axes:
            n = ax["name"]
            if n in (b"Weight", "Weight"): vals.append(weight)
            elif n in (b"Optical size", "Optical size"): vals.append(max(ax["minimum"], min(ax["maximum"], size / 2)))
            else: vals.append(ax["default"])
        f.set_variation_by_axes(vals)
    except Exception:
        pass
    return f

def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)

class Layout:
    def __init__(self, W, H):
        self.W, self.H = W, H
        self.portrait = H > W
        self.u = W / 1080 if self.portrait else H / 1080       # type scale

def text_size(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1], b

@functools.lru_cache(maxsize=16)
def identifiers(W, H):
    """the permanent top-left block: UNITED ROAD bug + SATIRE - FICTIONAL DIALOGUE"""
    L = Layout(W, H); u = L.u
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    x, y = int(44 * u), int((70 if L.portrait else 40) * u)
    f1 = font("Montserrat", 34 * u, 900); f2 = font("Inter", 21 * u, 700)
    w1, h1, b1 = text_size(d, "UNITED ROAD", f1)
    d.rectangle((x, y + 3 * u, x + 9 * u, y + h1 + 3 * u), fill=RED)
    d.text((x + 18 * u - b1[0], y - b1[1] + 2 * u), "UNITED ROAD", font=f1, fill=WHITE, stroke_width=max(1, int(2 * u)),
           stroke_fill=(0, 0, 0))
    s2 = "SATIRE — FICTIONAL DIALOGUE"
    w2, h2, b2 = text_size(d, s2, f2)
    px, py = x, y + h1 + 16 * u
    d.rounded_rectangle((px, py, px + w2 + 22 * u, py + h2 + 16 * u), radius=int(6 * u), fill=(10, 10, 14, 196))
    d.text((px + 11 * u - b2[0], py + 8 * u - b2[1]), s2, font=f2, fill=WHITE)
    return img

@functools.lru_cache(maxsize=8)
def id_card(W, H):
    L = Layout(W, H); u = L.u
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    f1 = font("Montserrat", 58 * u, 900); f2 = font("Inter", 30 * u, 700)
    s1, s2 = "CARTOON SORIANO", "A UNITED ROAD PARODY"
    w1, h1, b1 = text_size(d, s1, f1); w2, h2, b2 = text_size(d, s2, f2)
    pad = 26 * u
    cw = max(w1, w2) + 2 * pad + 14 * u
    ch = h1 + h2 + 2 * pad + 16 * u
    x = int(44 * u)
    y = int(H * (0.715 if L.portrait else 0.715))
    d.rounded_rectangle((x, y, x + cw, y + ch), radius=int(10 * u), fill=CARD + (226,))
    d.rectangle((x, y, x + 12 * u, y + ch), fill=RED)
    d.text((x + 14 * u + pad - b1[0], y + pad - b1[1]), s1, font=f1, fill=WHITE)
    d.text((x + 14 * u + pad - b2[0], y + pad + h1 + 16 * u - b2[1]), s2, font=f2, fill=(222, 222, 228))
    return img

@functools.lru_cache(maxsize=8)
def end_card(W, H):
    L = Layout(W, H); u = L.u
    img = Image.new("RGBA", (W, H), (0, 0, 0, 255)); d = ImageDraw.Draw(img)
    yy = np.linspace(0, 1, H)[:, None, None]
    grad = (np.float32([20, 22, 28]) * (1 - yy) + np.float32([8, 9, 12]) * yy) * np.ones((1, W, 1))
    img = Image.fromarray(np.dstack([grad.astype(np.uint8), np.full((H, W, 1), 255, np.uint8)]))
    d = ImageDraw.Draw(img)
    f1 = font("Montserrat", (120 if L.portrait else 128) * u, 900); f2 = font("Inter", 40 * u, 700)
    s1, s2 = "UNITED ROAD", "SATIRE — FICTIONAL DIALOGUE"
    w1, h1, b1 = text_size(d, s1, f1); w2, h2, b2 = text_size(d, s2, f2)
    if w1 > W * 0.86:
        f1 = font("Montserrat", 120 * u * W * 0.86 / w1, 900); w1, h1, b1 = text_size(d, s1, f1)
    cy = H * 0.46
    d.text(((W - w1) / 2 - b1[0], cy - h1 - 20 * u - b1[1]), s1, font=f1, fill=WHITE)
    d.rectangle(((W - 120 * u) / 2, cy, (W + 120 * u) / 2, cy + 10 * u), fill=RED)
    d.text(((W - w2) / 2 - b2[0], cy + 40 * u - b2[1]), s2, font=f2, fill=(226, 226, 232))
    return img

def wrap(d, text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_size(d, t, f)[0] <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

@functools.lru_cache(maxsize=512)
def caption(W, H, text):
    """a caption card: at most two lines, high contrast"""
    L = Layout(W, H); u = L.u
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(img)
    size = 50 if L.portrait else 44
    maxw = (W * 0.80) if L.portrait else (W * 0.62)
    f = font("Inter", size * u, 800)
    lines = wrap(d, text, f, maxw)
    while len(lines) > 2 and size > 34:
        size -= 2; f = font("Inter", size * u, 800); lines = wrap(d, text, f, maxw)
    lh = int(size * u * 1.24)
    widths = [text_size(d, s, f)[0] for s in lines]
    bw = max(widths) + 2 * 26 * u
    bh = lh * len(lines) + 2 * 16 * u
    if L.portrait:
        cy = H * 0.76                                     # the 70-82 % band
        x0 = (W - bw) / 2 - 10 * u                        # nudged off the right edge
    else:
        cy = H * 0.845
        x0 = (W - bw) / 2
    y0 = cy - bh / 2
    d.rounded_rectangle((x0, y0, x0 + bw, y0 + bh), radius=int(12 * u), fill=(6, 6, 10, 176))
    for i, s in enumerate(lines):
        w_, h_, b_ = text_size(d, s, f)
        tx = x0 + (bw - w_) / 2 - b_[0]
        ty = y0 + 16 * u + i * lh + (lh - size * u) / 2 - b_[1] * 0.35
        d.text((tx, ty), s, font=f, fill=WHITE, stroke_width=max(1, int(2 * u)), stroke_fill=(0, 0, 0))
    return img

# ---------------------------------------------------------------- the optional gag graphics
GAGS = {
    "accurate": [("ACCURATE", CARD, 0.0), ("UNHELPFUL", RED, 0.35)],
    "ongoing": [("CASE ONGOING", CARD, 0.0), ("METER RUNNING", RED, 0.3)],
    "organisation": [("ORGANISATION: 10/10", CARD, 0.0)],
    "115": [("115", RED, 0.0)],
    "efficiency": [("115", CARD, 0.0), ("EFFICIENCY", RED, 0.3)],
    "lpf": [("LAW", CARD, 0.0), ("PRINCIPLES", CARD, None), ("FACTS", RED, None)],     # None: timed by build_times
    "supporter": [("SUPPORTER → INNOCENT", CARD, 0.0)],
    "journalist": [("JOURNALIST → APPEALING", RED, 0.0)],
}
STAMPS = {"cas1": (-9, 0.28), "cas2": (7, 0.72)}     # CAS rubber stamps: angle, horizontal position

@functools.lru_cache(maxsize=64)
def tag(W, H, text, color, big=False):
    L = Layout(W, H); u = L.u
    size = (84 if text == "115" else 38) * u * (1.0 if L.portrait else 0.9)
    f = font("Montserrat", size, 900)
    tmp = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    w, h, b = text_size(tmp, text, f)
    pad_x, pad_y = 24 * u, 14 * u
    img = Image.new("RGBA", (int(w + 2 * pad_x + 10 * u), int(h + 2 * pad_y)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=int(8 * u), fill=color + (236,))
    if color == CARD:
        d.rectangle((0, 0, 8 * u, img.height), fill=RED)
    d.text((pad_x + 8 * u - b[0], pad_y - b[1]), text, font=f, fill=WHITE)
    return img

@functools.lru_cache(maxsize=8)
def stamp(W, H, angle):
    L = Layout(W, H); u = L.u
    f = font("BebasNeue-Regular", 104 * u, 400)
    tmp = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
    w, h, b = text_size(tmp, "CAS", f)
    pad = 22 * u
    img = Image.new("RGBA", (int(w + 2 * pad), int(h + 2 * pad)), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = (214, 28, 44, 235)
    d.rounded_rectangle((4 * u, 4 * u, img.width - 4 * u, img.height - 4 * u), radius=int(10 * u), outline=col, width=int(9 * u))
    d.text((pad - b[0], pad - b[1]), "CAS", font=f, fill=col)
    # worn ink: knock a few speckles out of the stamp
    a = np.asarray(img).copy()
    rng = np.random.default_rng(5)
    holes = rng.random(a.shape[:2]) < 0.05
    a[..., 3] = np.where(holes, (a[..., 3] * 0.35).astype(np.uint8), a[..., 3])
    return Image.fromarray(a).rotate(angle, resample=Image.BICUBIC, expand=True)

def gag_layer(W, H, name, age, left, shot, build_times=()):
    """RGBA overlay for a gag graphic `age` s after it appeared and `left` s before it goes: small tags in the lower
    third (where a TV name strap would be), fading in and out, nothing flying across the frame"""
    L = Layout(W, H); u = L.u
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0 = 44 * u if L.portrait else W * 0.045
    right = L.portrait                         # portrait: lower right, clear of his gesturing (frame-left) hand
    if name in STAMPS:
        ang, fx = STAMPS[name]
        st = stamp(W, H, ang)
        k = 1.0 + 0.06 * (1 - smooth(age / 0.2))
        a = smooth(age / 0.14) * smooth(left / 0.2)
        s = st.resize((max(1, int(st.width * k)), max(1, int(st.height * k))), Image.BICUBIC)
        n = int(name[-1])
        cx = x0 + s.width / 2 + (n - 1) * (s.width + 24 * u)
        if right: cx = W - 96 * u - s.width / 2 - (2 - n) * (s.width + 24 * u)
        cy = H * (0.765 if L.portrait else 0.76)
        s = Image.fromarray((np.asarray(s).astype(np.float32) * [1, 1, 1, a]).astype(np.uint8))
        out.alpha_composite(s, (int(cx - s.width / 2), int(cy - s.height / 2)))
        return out
    items = GAGS[name]
    tags = [tag(W, H, t, c) for t, c, _ in items]
    gap = 12 * u
    y = H * ((0.60 if shot == "A" else 0.715) if L.portrait else 0.70)   # portrait A: on the chest, above his hands
    if name == "journalist":                  # stacks under the SUPPORTER tag
        y += tags[0].height + gap
    for i, ((t, c, delay), im) in enumerate(zip(items, tags)):
        d = delay if delay is not None else (build_times[i] if i < len(build_times) else 0.0)
        a_age = age - d
        if a_age < 0: y += im.height + gap; continue
        a = smooth(a_age / 0.22) * smooth(left / 0.22)
        arr = np.asarray(im).astype(np.float32); arr[..., 3] *= a
        xx = (W - 96 * u - im.width) if right else x0
        out.alpha_composite(Image.fromarray(arr.astype(np.uint8)), (int(xx), int(y)))
        y += im.height + gap
    return out

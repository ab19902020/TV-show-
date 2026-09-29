"""Graphics for Episode 1: boardroom presentation slides, the tablet, the video-call UI, documentary lower thirds,
the title card, match score cards / score bug, and the set-piece analysis (telestration) sequences.
Everything is drawn here (PIL / OpenCV) in the club palette; fonts are open-licence Google Fonts in fonts/."""
import math, os, functools, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# output resolution: every graphic is laid out in 1080p units and drawn Z times larger (Z = 2 for 4K)
Z = int(os.environ.get("EP_RES", "3840x2160").split("x")[0]) / 1920.0


def _sc(v):
    return v * Z


class SD:
    """ImageDraw proxy: coordinates, widths and radii in 1080p layout units, drawn at Z x resolution"""

    def __init__(self, im):
        self.d = ImageDraw.Draw(im)

    @staticmethod
    def _xy(xy):
        if isinstance(xy, (list, tuple)) and xy and isinstance(xy[0], (list, tuple)):
            return [(p[0] * Z, p[1] * Z) for p in xy]
        return [v * Z for v in xy]

    def _kw(self, kw):
        if "width" in kw: kw["width"] = max(1, int(round(kw["width"] * Z)))
        if "radius" in kw: kw["radius"] = kw["radius"] * Z
        return kw

    def rectangle(self, xy, **kw): self.d.rectangle(self._xy(xy), **self._kw(kw))
    def rounded_rectangle(self, xy, **kw): self.d.rounded_rectangle(self._xy(xy), **self._kw(kw))
    def ellipse(self, xy, **kw): self.d.ellipse(self._xy(xy), **self._kw(kw))
    def line(self, xy, **kw): self.d.line(self._xy(xy), **self._kw(kw))
    def polygon(self, xy, **kw): self.d.polygon(self._xy(xy), **self._kw(kw))
    def arc(self, xy, start, end, **kw): self.d.arc(self._xy(xy), start, end, **self._kw(kw))
    def text(self, xy, s, **kw): self.d.text((xy[0] * Z, xy[1] * Z), s, **kw)

    def textbbox(self, xy, s, **kw):
        b = self.d.textbbox((xy[0] * Z, xy[1] * Z), s, **kw)
        return tuple(v / Z for v in b)


def new(mode, size, color=0):
    return Image.new(mode, (int(round(size[0] * Z)), int(round(size[1] * Z))), color)


def grid(h, w):
    """layout-unit coordinates of every pixel of a (h, w) layout-unit image"""
    yy, xx = np.mgrid[0:int(round(h * Z)), 0:int(round(w * Z))].astype(np.float32)
    return yy / Z, xx / Z

RED = (200, 16, 46)
DARKRED = (96, 8, 22)
GOLD = (251, 225, 34)
WHITE = (255, 255, 255)
INK = (18, 18, 20)


@functools.lru_cache(maxsize=64)
def font(name, size, weight=None):
    f = ImageFont.truetype(f"fonts/{name}.ttf", int(round(size * Z)))
    if weight is not None:
        axes = f.get_variation_axes()
        vals = []
        for ax in axes:
            n = ax["name"]
            if n in (b"Weight", "Weight"): vals.append(weight)
            elif n in (b"Optical size", "Optical size"): vals.append(max(ax["minimum"], min(ax["maximum"], size / 2)))
            else: vals.append(ax["default"])
        f.set_variation_by_axes(vals)
    return f


def smooth(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def text_w(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1], b[1]


def centered(d, cx, y, s, f, fill, spacing=0):
    w, h, oy = text_w(d, s, f)
    d.text((cx - w / 2, y - oy), s, font=f, fill=fill)
    return w, h


def to_np(im):
    return np.asarray(im.convert("RGB")).astype(np.float32) / 255.0


# ---------------------------------------------------------------- boardroom slides (TV content, 1280x720)
SW, SH = 1280, 720


def slide_base(title="STRATEGY 2026/27", page=None):
    im = new("RGB", (SW, SH), (20, 20, 24))
    yy, xx = grid(SH, SW)
    a = np.zeros(yy.shape + (3,), np.float32)
    g = np.clip(1 - np.sqrt(((xx - SW * 0.78) / (SW * 0.9)) ** 2 + ((yy - SH * 0.2) / (SH * 1.1)) ** 2), 0, 1)
    a[...] = np.float32([22, 20, 24]) / 255
    a += g[..., None] * np.float32([120, 10, 25]) / 255 * 0.9
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    d = SD(im)
    d.rectangle([0, 0, SW, 62], fill=(12, 12, 14))
    d.rectangle([0, 62, SW, 66], fill=RED)
    d.text((34, 14), "MANCHESTER UNITED", font=font("Oswald", 30, 600), fill=WHITE)
    d.text((340, 20), "|  " + title, font=font("Oswald", 24, 400), fill=(210, 210, 210))
    if page:
        w, _, _ = text_w(d, page, font("Inter", 20, 500))
        d.text((SW - 34 - w, 22), page, font=font("Inter", 20, 500), fill=(170, 170, 170))
    d.rectangle([34, SH - 40, SW - 34, SH - 39], fill=(90, 90, 96))
    d.text((34, SH - 32), "CONFIDENTIAL  -  BOARD USE ONLY", font=font("Inter", 14, 600), fill=(150, 150, 150))
    return im


def slide_word(word, k, page):
    """one buzzword, k = 0..1 progress of its entrance"""
    im = slide_base("OUR CLEAR PLAN", page)
    d = SD(im)
    e = ease_out(k * 2.2)
    f = font("Oswald", int(150 + 20 * (1 - e)), 700)
    w, h, oy = text_w(d, word, f)
    x = SW / 2 - w / 2 + (1 - e) * 60
    y = SH / 2 - h / 2 - 20
    col = tuple(int(c * e + 30 * (1 - e)) for c in WHITE)
    d.text((x, y - oy), word, font=f, fill=col)
    lw = int(w * smooth(k * 2.2 - 0.3))
    d.rectangle([SW / 2 - w / 2, y + h + 26, SW / 2 - w / 2 + lw, y + h + 34], fill=RED)
    return im


def slide_title(k):
    im = slide_base("BOARD MEETING", "1 / 47")
    d = SD(im)
    centered(d, SW / 2, 250, "OUR CLEAR PLAN", font("Oswald", 120, 700), WHITE)
    centered(d, SW / 2, 420, "2026/27  -  A NEW CHAPTER", font("Oswald", 44, 400), (230, 200, 200))
    return im


def slide_connecting(t):
    im = new("RGB", (SW, SH), (8, 8, 10))
    d = SD(im)
    centered(d, SW / 2, 420, "Connecting to Boardroom Display...", font("Inter", 34, 500), (200, 200, 205))
    for i in range(12):
        a = 2 * math.pi * i / 12 - t * 7
        r0, r1 = 34, 58
        c = int(60 + 190 * ((i / 12 + t * 1.1) % 1.0))
        d.line([(SW / 2 + r0 * math.cos(a), 300 + r0 * math.sin(a)), (SW / 2 + r1 * math.cos(a), 300 + r1 * math.sin(a))],
               fill=(c, c, c), width=9)
    return im


def slide_options(k):
    im = slide_base("SQUAD PLANNING", "12 / 47")
    d = SD(im)
    d.text((70, 100), "OPTIONS", font=font("Oswald", 80, 700), fill=WHITE)
    rows = [("Option A", "Continue"), ("Option B", "Continue, but with alignment"), ("Option C", "Player trading"),
            ("Option D", "See Option A")]
    for i, (a, b) in enumerate(rows):
        v = smooth(k * 3 - i * 0.35)
        y = 230 + i * 92
        d.rectangle([70, y, 70 + 10, y + 60], fill=RED)
        d.text((100 + 40 * (1 - v), y + 4), a, font=font("Oswald", 40, 600), fill=tuple(int(255 * v) for _ in range(3)))
        d.text((330 + 40 * (1 - v), y + 10), b, font=font("Inter", 32, 400), fill=tuple(int(200 * v) for _ in range(3)))
    return im


def slide_sales(k):
    im = slide_base("PLAYER TRADING", "13 / 47")
    d = SD(im)
    d.text((70, 96), "SALES  >  REINVESTMENT", font=font("Oswald", 64, 700), fill=WHITE)
    d.text((72, 180), "Projected outgoings (EUR m)", font=font("Inter", 24, 500), fill=(200, 200, 200))
    bars = [("SUMMER", 0.55), ("JANUARY", 0.8), ("SUMMER 2", 1.0)]
    base = 610
    for i, (lab, h) in enumerate(bars):
        v = ease_out(k * 2.0 - i * 0.25)
        x = 170 + i * 330
        top = base - int(330 * h * v)
        d.rectangle([x, top, x + 180, base], fill=RED)
        d.text((x + 20, base + 12), lab, font=font("Oswald", 26, 500), fill=(220, 220, 220))
    d.line([(120, base), (SW - 120, base)], fill=(160, 160, 160), width=3)
    a = ease_out(k * 1.6 - 0.5)
    if a > 0:
        d.line([(200, 560), (200 + 780 * a, 560 - 330 * a)], fill=GOLD, width=10)
        if a > 0.95:
            d.polygon([(980, 230), (1010, 262), (960, 262)], fill=GOLD)
    return im


TARGETS = ["Win the Premier League", "Top four (minimum)", "Win the Champions League", "Win the FA Cup",
           "Win the League Cup", "Win the Community Shield", "Record commercial revenue", "Net spend: zero",
           "Develop three academy stars", "Sell three academy stars", "Improve the vibes", "Clarity",
           "Alignment", "Sustainability", "Agility", "Stadium: 100,000 seats", "Beat City (twice)",
           "Win the Europa League (if needed)", "Grow social engagement +400%", "Fewer injuries",
           "More wins", "No draws", "Entertain", "Compete on every front", "Don't complain"]


def slide_targets(scroll, page):
    im = slide_base("OBJECTIVES 2026/27", page)
    d = SD(im)
    body = new("RGB", (SW, SH - 110), (0, 0, 0))
    bd = SD(body)
    for i, s in enumerate(TARGETS * 2):
        y = 20 + i * 64 - scroll
        if y < -70 or y > SH: continue
        bd.rectangle([70, y + 12, 70 + 26, y + 38], outline=WHITE, width=3)
        bd.line([(76, y + 26), (83, y + 34), (96, y + 14)], fill=GOLD, width=4)
        bd.text((120, y + 2), f"{i + 1:02d}.  {s}", font=font("Inter", 34, 500), fill=WHITE)
    bh = body.height
    ramp = np.clip(np.minimum(np.arange(bh), bh - 1 - np.arange(bh)) / (40 * Z), 0, 1)
    mask = Image.fromarray((np.repeat(ramp[:, None], body.width, 1) * 255).astype(np.uint8), "L")
    im.paste(body, (0, int(70 * Z)), mask)
    return im


def tv_slide(name, t_local, t_abs=0.0):
    if name == "connecting": return slide_connecting(t_abs)
    if name == "title": return slide_title(t_local)
    if name.startswith("word:"):
        w, page = name[5:].split("|")
        return slide_word(w, t_local, page)
    if name == "options": return slide_options(t_local)
    if name == "sales": return slide_sales(t_local)
    if name.startswith("targets"):
        page = "21 / 47" if name == "targets" else "22 / 47"
        base = 0 if name == "targets" else 900
        return slide_targets(base + 520 * smooth(t_local / 1.8), page)
    return None


# ---------------------------------------------------------------- the tablet (insert)
def tablet_insert(t_local, taps, working_at):
    """full-frame close-up of Jason's tablet: a spinner that won't connect; taps show ripples"""
    W, H = 1920, 1080
    im = new("RGB", (W, H), (0, 0, 0))
    yy, xx = grid(H, W)
    a = np.zeros(yy.shape + (3,), np.float32)
    # wood table blurred behind
    a[...] = np.float32([96, 52, 28]) / 255
    a *= (0.75 + 0.25 * np.sin(xx / 90 + yy / 400))[..., None]
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18 * Z))
    d = SD(im)
    x0, y0, x1, y1 = 330, 150, 1590, 950
    d.rounded_rectangle([x0 - 34, y0 - 34, x1 + 34, y1 + 34], radius=60, fill=(14, 14, 16))
    scr = slide_connecting(t_local) if t_local < working_at else slide_title(1.0)
    scr = scr.resize((int((x1 - x0) * Z), int((y1 - y0) * Z)), Image.LANCZOS)
    im.paste(scr, (int(x0 * Z), int(y0 * Z)))
    for tp in taps:
        k = (t_local - tp) / 0.45
        if 0 <= k <= 1:
            r = int(20 + 90 * k)
            c = int(255 * (1 - k))
            d.ellipse([W / 2 - r + 120, 560 - r, W / 2 + r + 120, 560 + r], outline=(c, c, c), width=6)
    return to_np(im)


# ---------------------------------------------------------------- documentary lower third
def lower_third(frame, t_local, dur, line1, line2):
    """white type + thin red rule, bottom left; slides in / fades out"""
    if t_local < 0 or t_local > dur: return frame
    k_in = ease_out(t_local / 0.6); k_out = smooth((dur - t_local) / 0.5)
    k = min(k_in, k_out)
    H, W = frame.shape[0] / Z, frame.shape[1] / Z
    im = new("RGBA", (W, H), (0, 0, 0, 0))
    d = SD(im)
    x = 120 - 30 * (1 - k_in)
    y = H - 240
    f1, f2 = font("Oswald", 64, 600), font("Inter", 30, 500)
    w1, h1, o1 = text_w(d, line1, f1)
    d.rectangle([x, y + 86, x + max(w1, 260) * k_in, y + 90], fill=RED + (255,))
    d.text((x + 3, y - o1 + 3), line1, font=f1, fill=(0, 0, 0, 150))
    d.text((x, y - o1), line1, font=f1, fill=WHITE + (255,))
    d.text((x + 2, y + 104 + 2), line2, font=f2, fill=(0, 0, 0, 150))
    d.text((x, y + 104), line2, font=f2, fill=(235, 235, 235, 255))
    a = np.asarray(im).astype(np.float32) / 255
    al = a[..., 3:4] * k
    return frame * (1 - al) + a[..., :3] * al


# ---------------------------------------------------------------- title card
def title_card(t_local, dur):
    W, H = 1920, 1080
    k = smooth(t_local / 0.8) * smooth((dur - t_local) / 0.7)
    im = new("RGB", (W, H), (0, 0, 0))
    d = SD(im)
    s = 1.0 + 0.03 * (t_local / dur)
    f1 = font("BebasNeue-Regular", int(230 * s))
    w, h, oy = text_w(d, "THE CLEAR PLAN", f1)
    y = 380
    d.text((W / 2 - w / 2, y - oy), "THE CLEAR PLAN", font=f1, fill=WHITE)
    lw = w * ease_out((t_local - 0.35) / 1.0)
    d.rectangle([W / 2 - lw / 2, y + h + 34, W / 2 + lw / 2, y + h + 44], fill=RED)
    f2 = font("Oswald", 46, 400)
    centered(d, W / 2, y + h + 90, "EPISODE ONE  -  NOT IDEAL", f2, (220, 220, 220))
    a = to_np(im) * k
    g = np.random.default_rng(int(t_local * 30)).normal(0, 0.02, a.shape[:2] + (1,)).astype(np.float32)
    return np.clip(a + g * 0.6, 0, 1)


# ---------------------------------------------------------------- match graphics
def score_card(t_local, dur, home, hs, away, as_, minute):
    W, H = 1920, 1080
    k = ease_out(t_local / 0.25)
    im = new("RGB", (W, H), (0, 0, 0))
    yy, xx = grid(H, W)
    a = np.zeros(yy.shape + (3,), np.float32)
    a[...] = np.float32([14, 14, 18]) / 255
    a += np.clip(1 - np.abs(yy - H / 2) / 420, 0, 1)[..., None] * np.float32([70, 6, 16]) / 255
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    d = SD(im)
    cy = H / 2
    bw = int(1500 * k)
    d.rectangle([W / 2 - bw / 2, cy - 120, W / 2 + bw / 2, cy + 120], fill=(24, 24, 28))
    d.rectangle([W / 2 - bw / 2, cy + 114, W / 2 + bw / 2, cy + 120], fill=RED)
    if k > 0.6:
        f = font("Oswald", 110, 700)
        fh = font("Oswald", 150, 700)
        w1, h1, o1 = text_w(d, home, f)
        d.text((W / 2 - 230 - w1, cy - h1 / 2 - o1), home, font=f, fill=WHITE)
        d.text((W / 2 + 230, cy - h1 / 2 - o1), away, font=f, fill=WHITE)
        sc = f"{hs}  -  {as_}"
        w2, h2, o2 = text_w(d, sc, fh)
        d.rectangle([W / 2 - 180, cy - 105, W / 2 + 180, cy + 105], fill=(240, 240, 240))
        d.text((W / 2 - w2 / 2, cy - h2 / 2 - o2), sc, font=fh, fill=INK)
        centered(d, W / 2, cy + 160, minute, font("Oswald", 44, 500), (200, 200, 200))
    return to_np(im)


def score_bug(frame, home, hs, away, as_, clock, k=1.0):
    H, W = frame.shape[0] / Z, frame.shape[1] / Z
    im = new("RGBA", (W, H), (0, 0, 0, 0))
    d = SD(im)
    x, y = 70, 60
    d.rectangle([x, y, x + 470, y + 58], fill=(16, 16, 20, 235))
    d.rectangle([x, y + 58, x + 470, y + 62], fill=RED + (255,))
    f = font("Oswald", 36, 600)
    d.text((x + 16, y + 6), home, font=f, fill=WHITE)
    d.rectangle([x + 118, y + 6, x + 218, y + 52], fill=(240, 240, 240, 255))
    centered(d, x + 168, y + 12, f"{hs}-{as_}", f, INK)
    d.text((x + 234, y + 6), away, font=f, fill=WHITE)
    d.text((x + 350, y + 8), clock, font=font("Inter", 30, 600), fill=(220, 220, 220))
    a = np.asarray(im).astype(np.float32) / 255
    al = a[..., 3:4] * k
    return frame * (1 - al) + a[..., :3] * al


def telestration(t_local, dur, kind):
    """broadcast set-piece analysis: top-down half pitch; the ball comes in and it goes in the net.
    kind 'corner' or 'chaos'"""
    W, H = 1920, 1080
    im = new("RGB", (W, H), (0, 0, 0))
    yy, xx = grid(H, W)
    a = np.zeros(yy.shape + (3,), np.float32)
    stripes = (np.floor(xx / 160) % 2)[..., None]
    a[...] = np.float32([18, 86, 38]) / 255 * (0.92 + 0.08 * stripes)
    a *= (1 - 0.35 * np.clip(np.sqrt(((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2), 0, 1))[..., None]
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    d = SD(im)
    L = (235, 245, 235)
    # goal line along the right, penalty area, six-yard box, goal
    gx = 1700
    d.line([(gx, 90), (gx, 990)], fill=L, width=5)
    d.rectangle([gx - 470, 250, gx, 830], outline=L, width=5)
    d.rectangle([gx - 160, 400, gx, 680], outline=L, width=5)
    d.rectangle([gx, 470, gx + 50, 610], outline=L, width=5)
    d.arc([gx - 560, 440, gx - 380, 640], 115, 245, fill=L, width=5)
    d.ellipse([gx - 330, 532, gx - 318, 544], fill=L)
    d.line([(160, 90), (gx, 90)], fill=L, width=5)
    d.arc([gx - 30, 60, gx + 30, 120], 90, 180, fill=L, width=4)
    title = "SET PIECE" if kind == "corner" else "SET PIECE (AGAIN)"
    d.rectangle([70, 950, 70 + 560, 1030], fill=(16, 16, 20))
    d.rectangle([70, 1026, 70 + 560, 1030], fill=RED)
    d.text((92, 956), title, font=font("Oswald", 52, 600), fill=WHITE)
    u = t_local / dur
    rng = np.random.default_rng(3 if kind == "corner" else 9)
    hull = [(gx - 250, 460), (gx - 200, 560), (gx - 300, 640), (gx - 120, 520), (gx - 380, 540), (gx - 90, 600)]
    utd = [(gx - 230, 480), (gx - 180, 590), (gx - 280, 620), (gx - 140, 500), (gx - 60, 540), (gx - 350, 580)]
    ball0 = (gx - 12, 104) if kind == "corner" else (gx - 700, 300)
    target = (gx - 150, 545)
    # movement
    k1 = smooth((u - 0.10) / 0.45)            # ball flight
    k2 = smooth((u - 0.55) / 0.2)             # header / scramble into the net
    if kind == "corner":
        hull_m = [(x + (target[0] - x) * 0.5 * k1 if i == 3 else x, y + (target[1] - y) * 0.5 * k1 if i == 3 else y) for i, (x, y) in enumerate(hull)]
        utd_m = [(x - 25 * k1 if i in (0, 3) else x, y + 10 * k1) for i, (x, y) in enumerate(utd)]
    else:
        wob = lambda i: (math.sin(u * 30 + i) * 28 * k1, math.cos(u * 26 + 2 * i) * 28 * k1)
        hull_m = [(x + wob(i)[0], y + wob(i)[1]) for i, (x, y) in enumerate(hull)]
        utd_m = [(x - wob(i)[1], y + wob(i)[0]) for i, (x, y) in enumerate(utd)]
    for x, y in utd_m:
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=RED, outline=WHITE, width=4)
    for x, y in hull_m:
        d.ellipse([x - 22, y - 22, x + 22, y + 22], fill=(242, 160, 0), outline=INK, width=4)
    # ball path
    def bezier(p0, p1, p2, s): return ((1 - s) ** 2 * p0[0] + 2 * (1 - s) * s * p1[0] + s * s * p2[0],
                                        (1 - s) ** 2 * p0[1] + 2 * (1 - s) * s * p1[1] + s * s * p2[1])
    ctrl = (gx - 520, 260) if kind == "corner" else (gx - 330, 180)
    pts = [bezier(ball0, ctrl, target, s * k1) for s in np.linspace(0, 1, 40)]
    if kind == "chaos" and k1 > 0.2:
        extra = [target, (gx - 90, 470), (gx - 230, 610), (gx - 60, 640), (gx - 170, 500)]
        n = int(len(extra) * min(1.0, k2 * 1.2 + 0.3 * k1))
        pts += extra[:n]
    if len(pts) > 1:
        for i in range(len(pts) - 1):
            d.line([pts[i], pts[i + 1]], fill=(255, 255, 255), width=4)
    bx, by = pts[-1]
    if k2 > 0:
        bx, by = bx + (gx + 25 - bx) * k2, by + (540 - by) * k2
        d.line([pts[-1], (bx, by)], fill=GOLD, width=6)
    d.ellipse([bx - 13, by - 13, bx + 13, by + 13], fill=WHITE, outline=INK, width=3)
    if u > 0.78:
        f = font("Oswald", 140, 700)
        k3 = ease_out((u - 0.78) / 0.1)
        w, h, oy = text_w(d, "GOAL", f)
        d.text((W / 2 - w / 2 - 200, 380 - oy), "GOAL", font=f, fill=(255, 255, 255))
        d.text((W / 2 - w / 2 - 200 + 330, 420 - oy), "HULL", font=font("Oswald", 60, 500), fill=(242, 160, 0))
    return to_np(im)


# ---------------------------------------------------------------- the video call (TV content)
def call_frame(tiles, labels, state, t_local):
    """tiles: list of HxWx3 float images already rendered for each participant (same size);
    state: 'ringing' | 'call' | 'left' | 'ended'"""
    im = new("RGB", (SW, SH), (32, 32, 38))
    d = SD(im)
    if state == "ringing":
        d.rectangle([0, 0, SW, SH], fill=(28, 28, 34))
        r = 70 + 8 * math.sin(t_local * 12)
        d.ellipse([SW / 2 - r, 250 - r, SW / 2 + r, 250 + r], fill=(98, 100, 167))
        centered(d, SW / 2, 222, "JG", font("Inter", 56, 700), WHITE)
        centered(d, SW / 2, 370, "Joel Glazer, Avram Glazer", font("Inter", 40, 600), WHITE)
        centered(d, SW / 2, 430, "Incoming video call...", font("Inter", 28, 400), (190, 190, 200))
        d.ellipse([SW / 2 - 150, 500, SW / 2 - 60, 590], fill=(196, 49, 75))
        d.ellipse([SW / 2 + 60, 500, SW / 2 + 150, 590], fill=(92, 184, 92))
        return to_np(im)
    if state == "ended":
        d.rectangle([0, 0, SW, SH], fill=(20, 20, 24))
        centered(d, SW / 2, 320, "Call ended", font("Inter", 48, 600), (220, 220, 225))
        centered(d, SW / 2, 395, "Duration 00:19", font("Inter", 26, 400), (150, 150, 160))
        return to_np(im)
    n = len(tiles)
    gap = 14
    tw = (SW - gap * (n + 1)) // n
    th = SH - 2 * gap - 60
    out = to_np(im)
    for i, tile in enumerate(tiles):
        x0 = int((gap + i * (tw + gap)) * Z); y0 = int(gap * Z); rw, rh = int(tw * Z), int(th * Z)
        tl = cv2.resize(tile, (rw, rh), interpolation=cv2.INTER_AREA)
        out[y0:y0 + rh, x0:x0 + rw] = tl
    im = Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))
    d = SD(im)
    for i, lab in enumerate(labels):
        x0 = gap + i * (tw + gap)
        f = font("Inter", 24, 600)
        w, h, oy = text_w(d, lab, f)
        d.rounded_rectangle([x0 + 12, th - 40, x0 + 34 + w, th - 4], radius=6, fill=(0, 0, 0, 170))
        d.text((x0 + 22, th - 36 - oy + 4), lab, font=f, fill=WHITE)
    # bottom bar
    d.rectangle([0, SH - 60, SW, SH], fill=(24, 24, 28))
    for j, c in enumerate([(80, 80, 90), (80, 80, 90), (80, 80, 90), (196, 49, 75)]):
        cx = SW / 2 - 150 + j * 100
        d.rounded_rectangle([cx - 36, SH - 50, cx + 36, SH - 10], radius=10, fill=c)
    return to_np(im)

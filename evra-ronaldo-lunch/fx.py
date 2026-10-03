"""Cartoon effects drawn in the house style (black ink outlines, flat colour): text, thought bubbles, speed lines,
sparkles, steam, sweat drops, dust clouds, confetti, battery icons, water ripples and splashes, and the props that are
not in the atlas (table-tennis table, paddles, ball, a delivery box, a tumbleweed). Positions are plate px through the
shot's camera unless the name says otherwise (`*_out`: output px)."""
import math, os
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from engine import over, T, S, R

INK = (.04, .03, .03)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
_fonts = {}
SH = 2                       # sub-pixel shift for anti-aliased cv2 drawing
F = 1 << SH


def font(px):
    px = int(px)
    if px not in _fonts: _fonts[px] = ImageFont.truetype(FONT, px)
    return _fonts[px]


def cpt(cam, x, y):
    q = cam @ np.array([x, y, 1.]); return float(q[0]), float(q[1])


def ck(cam): return float(cam[0, 0])


def ipts(pts): return np.int32(np.round(np.array(pts) * F))


def poly(d, pts, fill, ink=INK, lw=3., closed=True):
    p = ipts(pts)
    if fill is not None: cv2.fillPoly(d, [p], fill, cv2.LINE_AA, SH)
    if ink is not None and lw > 0: cv2.polylines(d, [p], closed, ink, max(1, int(round(lw))), cv2.LINE_AA, SH)


def ellipse(d, c, ax, ang, fill, ink=INK, lw=3.):
    cc = (int(round(c[0] * F)), int(round(c[1] * F))); aa = (max(1, int(round(ax[0] * F))), max(1, int(round(ax[1] * F))))
    if fill is not None: cv2.ellipse(d, cc, aa, ang, 0, 360, fill, -1, cv2.LINE_AA, SH)
    if ink is not None and lw > 0: cv2.ellipse(d, cc, aa, ang, 0, 360, ink, max(1, int(round(lw))), cv2.LINE_AA, SH)


def blend(d, layer, alpha):
    """layer: RGB float, alpha: HxW float"""
    a = alpha[..., None]; d[:] = d * (1 - a) + layer * a


# ---------------------------------------------------------------------------------------------------- text
def text_out(d, s, x, y, px, fill=(1, .85, .1), stroke=INK, sw=None, anchor='mm', rot=0., alpha=1., scale=1.):
    """bold cartoon lettering with an ink outline, centred on (x, y) output px"""
    if alpha <= .01 or scale <= .01: return
    px = max(6, px * scale); sw = int(round(px * .09)) if sw is None else sw
    f = font(px); bb = f.getbbox(s, stroke_width=sw)
    w, h = bb[2] - bb[0] + 8, bb[3] - bb[1] + 8
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.text((4 - bb[0], 4 - bb[1]), s, font=f, fill=tuple(int(c * 255) for c in fill) + (255,), stroke_width=sw,
            stroke_fill=tuple(int(c * 255) for c in stroke) + (255,))
    if rot: im = im.rotate(rot, resample=Image.Resampling.BICUBIC, expand=True)
    a = np.asarray(im).astype(np.float32) / 255; a[..., :3] *= a[..., 3:4]; a *= alpha
    over(d, a, T(x - im.width / 2, y - im.height / 2))


# ---------------------------------------------------------------------------------------------------- bubbles and lines
def thought_bubble(d, cam, x, y, w, h, tail, grow=1.):
    """a cloud bubble centred (x, y) plate px, w x h, with three small puffs trailing to `tail` (plate px)"""
    if grow <= .01: return
    k = ck(cam); cx, cy = cpt(cam, x, y); W, Hh = w * k * grow / 2, h * k * grow / 2
    lw = max(2., 3.2 * k)
    lobes = 11
    pts = []
    for i in range(lobes):
        a = 2 * math.pi * i / lobes
        pts.append((cx + W * .82 * math.cos(a), cy + Hh * .78 * math.sin(a), W * .34, Hh * .36))
    for px_, py_, rx, ry in pts: ellipse(d, (px_, py_), (rx, ry), 0, (1, 1, 1), INK, lw)
    for px_, py_, rx, ry in pts: ellipse(d, (px_, py_), (rx - lw, ry - lw), 0, (1, 1, 1), None, 0)
    ellipse(d, (cx, cy), (W * .86, Hh * .8), 0, (1, 1, 1), None, 0)
    tx, ty = cpt(cam, *tail)
    for i, f in enumerate((.35, .62, .85)):
        r = (10 - i * 3) * k * grow
        ellipse(d, (cx + (tx - cx) * f, cy + Hh * .8 + (ty - cy - Hh * .8) * f), (r * 1.3, r), 0, (1, 1, 1), INK, lw)


def speed_lines(d, cx, cy, t, n=48, color=(1, 1, 1), alpha=.6, r0=.35, seed=1):
    """radial anime focus lines around output point (cx, cy); they flicker each frame"""
    H, W = d.shape[:2]; rng = np.random.default_rng(int(t * 30) * 7 + seed)
    layer = np.zeros((H, W), np.float32); R_ = math.hypot(W, H)
    for i in range(n):
        a = 2 * math.pi * (i + rng.uniform(-.4, .4)) / n
        r1 = R_ * (r0 + rng.uniform(0, .18)); wdt = rng.uniform(.004, .014)
        p = [(cx + math.cos(a) * r1, cy + math.sin(a) * r1),
             (cx + math.cos(a + wdt) * R_, cy + math.sin(a + wdt) * R_), (cx + math.cos(a - wdt) * R_, cy + math.sin(a - wdt) * R_)]
        cv2.fillPoly(layer, [ipts(p)], 1., cv2.LINE_AA, SH)
    blend(d, np.ones_like(d) * np.float32(color), layer * alpha)


def motion_lines(d, cam, x0, y0, x1, y1, n=4, spread=30, lw=3, alpha=.8):
    """short streaks trailing a fast object, from (x1, y1) back to (x0, y0) plate px"""
    k = ck(cam)
    for i in range(n):
        o = (i - (n - 1) / 2) * spread / max(1, n - 1)
        dx, dy = x1 - x0, y1 - y0; L = math.hypot(dx, dy) or 1; nx, ny = -dy / L, dx / L
        a = cpt(cam, x0 + nx * o + dx * .2 * (i % 2), y0 + ny * o + dy * .2 * (i % 2)); b = cpt(cam, x1 + nx * o, y1 + ny * o)
        cv2.line(d, (int(a[0] * F), int(a[1] * F)), (int(b[0] * F), int(b[1] * F)), INK, max(1, int(lw * k)), cv2.LINE_AA, SH)


def vignette(d, color=(0, 0, 0), strength=.5, r=.75):
    H, W = d.shape[:2]
    Y, X = np.ogrid[:H, :W]; q = np.sqrt(((X - W / 2) / (W * .5)) ** 2 + ((Y - H / 2) / (H * .5)) ** 2)
    a = np.clip((q - r) / (1.25 - r), 0, 1) ** 1.5 * strength
    blend(d, np.ones_like(d) * np.float32(color), a.astype(np.float32))


def tint(d, color, amount):
    d[:] = d * (1 - amount) + d * np.float32(color) * amount


def radial_bg(d, c1, c2, t, rays=14, cx=None, cy=None, spin=.4):
    """a cartoon sunburst background (output px)"""
    H, W = d.shape[:2]; cx = W / 2 if cx is None else cx; cy = H * .45 if cy is None else cy
    Y, X = np.mgrid[:H, :W].astype(np.float32)
    a = np.arctan2(Y - cy, X - cx) + t * spin
    m = (np.sin(a * rays) > 0).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 1.)
    d[:] = np.float32(c1) * (1 - m[..., None]) + np.float32(c2) * m[..., None]


# ---------------------------------------------------------------------------------------------------- small cartoon bits
def sparkle(d, x, y, size, t, phase=0., color=(1, 1, .85)):
    """a four-point twinkle at output px"""
    s = size * (.55 + .45 * math.sin(t * 9 + phase)) ** 2
    if s < 1: return
    for a in (0, math.pi / 2):
        pts = [(x + s * math.cos(a), y + s * math.sin(a)), (x + s * .18 * math.cos(a + math.pi / 2), y + s * .18 * math.sin(a + math.pi / 2)),
               (x - s * math.cos(a), y - s * math.sin(a)), (x - s * .18 * math.cos(a + math.pi / 2), y - s * .18 * math.sin(a + math.pi / 2))]
        cv2.fillPoly(d, [ipts(pts)], color, cv2.LINE_AA, SH)
    ellipse(d, (x, y), (s * .22, s * .22), 0, (1, 1, 1), None, 0)


def sweat(d, cam, x, y, size, t0, t, slide=40):
    """a cartoon sweat drop that appears at plate (x, y) and slides down"""
    a = t - t0
    if a < 0: return
    k = ck(cam); g = min(1, a / .15); cx, cy = cpt(cam, x, y + slide * min(1, max(0, a - .2) / 1.2))
    r = size * k * g
    if r < 1: return
    ta = -1.95; tip = (cx + 2.1 * r * math.cos(ta), cy + 2.1 * r * math.sin(ta))
    pts = [tip] + [(cx + r * math.cos(th), cy + r * math.sin(th)) for th in np.linspace(ta + 1.05, ta + 2 * math.pi - 1.05, 28)]
    poly(d, pts, (.62, .84, 1.), INK, max(1.5, 1.6 * k))
    ellipse(d, (cx + .3 * r, cy + .1 * r), (.25 * r, .42 * r), -30, (1, 1, 1), None, 0)


def puff(d, cx, cy, r, color=(1, 1, 1), alpha=1., ink=True, seed=0):
    """a round cartoon cloud (output px): steam, dust, smoke"""
    if r < 1 or alpha <= .01: return
    rng = np.random.default_rng(seed); layer = d.copy()
    blobs = [(cx + r * .55 * math.cos(a), cy + r * .45 * math.sin(a), r * rng.uniform(.45, .62)) for a in np.linspace(0, 2 * math.pi, 7)[:-1]]
    blobs.append((cx, cy, r * .6))
    if ink:
        for x, y, rr in blobs: ellipse(layer, (x, y), (rr, rr), 0, None, INK, max(1.5, r * .07))
    for x, y, rr in blobs: ellipse(layer, (x, y), (rr, rr), 0, color, None, 0)
    d[:] = d * (1 - alpha) + layer * alpha


def steam(d, cam, x, y, t, scale=1., n=3, seed=0, color=(1, 1, 1), alpha=.75):
    """wisps rising from a plate point (hot sauna, angry ears)"""
    k = ck(cam)
    for i in range(n):
        ph = (t * .9 + i / n + seed * .37) % 1
        cx, cy = cpt(cam, x + 12 * math.sin(ph * 6 + i) * scale, y - ph * 90 * scale)
        puff(d, cx, cy, (10 + 16 * ph) * scale * k, color, alpha * (1 - ph) * min(1, ph * 4), ink=False, seed=i + seed)


def dust(d, cam, x, y, t0, t, size=1., n=6, seed=0):
    """a dust cloud bursting from a plate point at t0"""
    a = t - t0
    if a < 0 or a > .7: return
    k = ck(cam); rng = np.random.default_rng(seed)
    for i in range(n):
        ang = rng.uniform(math.pi * .9, math.pi * 2.1); sp = rng.uniform(40, 110) * size
        cx, cy = cpt(cam, x + math.cos(ang) * sp * a * 1.8, y + math.sin(ang) * sp * a * .7)
        puff(d, cx, cy, (14 + 26 * a) * size * k, (.86, .82, .74), 1 - a / .7, ink=True, seed=i + seed)


def confetti(d, t, t0, n=90, seed=5, area=None, colors=None):
    """confetti falling over the whole frame from t0 (output px)"""
    a = t - t0
    if a < 0: return
    H, W = d.shape[:2]; rng = np.random.default_rng(seed)
    cols = colors or [(1, .2, .2), (1, .85, .1), (.2, .6, 1), (.2, .85, .4), (1, 1, 1), (1, .4, .8)]
    for i in range(n):
        x0 = rng.uniform(0, W); v = rng.uniform(.22, .45) * H; delay = rng.uniform(0, .6)
        b = a - delay
        if b < 0: continue
        y = -30 + v * b; x = x0 + 30 * math.sin(b * 3 + i)
        if y > H + 20: continue
        ang = b * rng.uniform(4, 9) + i; s = W * .012
        c = cols[i % len(cols)]
        p = [(x + s * math.cos(ang), y + s * .5 * math.sin(ang)), (x - s * math.cos(ang), y - s * .5 * math.sin(ang))]
        cv2.line(d, (int(p[0][0] * F), int(p[0][1] * F)), (int(p[1][0] * F), int(p[1][1] * F)), c, max(2, int(W * .009)), cv2.LINE_AA, SH)


def battery(d, x, y, w, level, label=None, t=0., blink=False):
    """a phone-style battery icon at output (x, y) centre, width w; level 0..1 (green > amber > red)"""
    h = w * .48
    col = (.25, .85, .3) if level > .5 else ((1, .7, .1) if level > .2 else (1, .15, .15))
    if blink and math.sin(t * 14) < 0: col = (.45, .05, .05)
    poly(d, [(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)], (1, 1, 1), INK, w * .06)
    poly(d, [(x + w / 2, y - h * .2), (x + w / 2 + w * .08, y - h * .2), (x + w / 2 + w * .08, y + h * .2), (x + w / 2, y + h * .2)], INK, None, 0)
    m = w * .08; L = (w - 2 * m) * max(.02, min(1, level))
    poly(d, [(x - w / 2 + m, y - h / 2 + m), (x - w / 2 + m + L, y - h / 2 + m), (x - w / 2 + m + L, y + h / 2 - m), (x - w / 2 + m, y + h / 2 - m)], col, None, 0)
    if label: text_out(d, label, x, y + h * .95, w * .3, fill=col, stroke=INK)


# ---------------------------------------------------------------------------------------------------- water
def ripples(d, cam, x, y, w, t, n=3, alpha=.8):
    """rings spreading on the water around a plate point (an ellipse of width w)"""
    k = ck(cam)
    for i in range(n):
        ph = (t * .8 + i / n) % 1
        cx, cy = cpt(cam, x, y); rx = w * (.55 + .7 * ph) * k / 2; ry = rx * .22
        layer = d.copy(); ellipse(layer, (cx, cy), (rx, ry), 0, None, (1, 1, 1), max(1.5, 3 * k * (1 - ph)))
        a = alpha * (1 - ph); d[:] = d * (1 - a) + layer * a


def splash(d, cam, x, y, t0, t, size=1., n=10, seed=0):
    """drops thrown up from a plate point at t0"""
    a = t - t0
    if a < 0 or a > .8: return
    k = ck(cam); rng = np.random.default_rng(seed)
    for i in range(n):
        vx = rng.uniform(-160, 160) * size; vy = -rng.uniform(220, 420) * size
        px, py = x + vx * a, y + vy * a + 700 * size * a * a
        if py > y + 5: continue
        cx, cy = cpt(cam, px, py); r = rng.uniform(4, 8) * size * k
        ellipse(d, (cx, cy), (r * .8, r), 0, (.75, .92, 1.), INK, max(1, 1.2 * k))


def waterline_mask(H, W, cam, y, t, amp=5., wl=60., x0=None, x1=None):
    """1 above a wavy waterline at plate y (output px mask)"""
    k = ck(cam)
    Y, X = np.mgrid[:H, :W].astype(np.float32)
    px = (X - cam[0, 2]) / k
    wave = y + amp * np.sin(px / wl + t * 4) + amp * .5 * np.sin(px / (wl * .43) - t * 5.3)
    yy = cam[1, 1] * wave + cam[1, 2]
    return np.clip((yy - Y) / 1.5 + .5, 0, 1)


# ---------------------------------------------------------------------------------------------------- props drawn here
def pp_ball(d, cam, x, y, r, t=0.):
    k = ck(cam); cx, cy = cpt(cam, x, y); rr = r * k
    ellipse(d, (cx, cy), (rr, rr), 0, (1, 1, 1), INK, max(1, rr * .18))
    ellipse(d, (cx - rr * .3, cy - rr * .3), (rr * .28, rr * .28), 0, (1, 1, 1), None, 0)
    ellipse(d, (cx + rr * .2, cy + rr * .25), (rr * .5, rr * .35), 30, (.85, .85, .9), None, 0)


def paddle(d, cam, x, y, size, rot=0., flip=False):
    """a table-tennis bat: red rubber, wooden handle; (x, y) = the grip, plate px"""
    k = ck(cam); cx, cy = cpt(cam, x, y); s = size * k
    a = math.radians(rot - 90)
    hx, hy = cx + math.cos(a) * s * .55, cy + math.sin(a) * s * .55
    # handle
    px, py = -math.sin(a), math.cos(a)
    poly(d, [(cx + px * s * .12, cy + py * s * .12), (hx + px * s * .1, hy + py * s * .1), (hx - px * s * .1, hy - py * s * .1),
             (cx - px * s * .12, cy - py * s * .12)], (.78, .55, .3), INK, max(1.5, s * .05))
    bx, by = cx + math.cos(a) * s * 1.05, cy + math.sin(a) * s * 1.05
    ellipse(d, (bx, by), (s * .55, s * .62), math.degrees(a) + 90, (.86, .12, .14), INK, max(1.5, s * .06))
    ellipse(d, (bx - s * .12, by - s * .14), (s * .18, s * .12), math.degrees(a) + 60, (1, .45, .45), None, 0)


TABLE = dict(near=((150, 1500), (790, 1500)), far=((330, 1180), (610, 1180)), top=26, leg=170)


def tt_table(d, cam, tbl=TABLE, front=False):
    """a table-tennis table seen from behind one end: green top in perspective, white lines, net; dark underneath.
    front=False draws the whole table; front=True only the near end's edge (drawn again over a player behind it)"""
    k = ck(cam)
    (nl, nr), (fl, fr) = tbl['near'], tbl['far']
    P_ = lambda x, y: cpt(cam, x, y)
    th = tbl['top']
    if not front:
        # shadow/undercarriage
        poly(d, [P_(fl[0] + 10, fl[1] + 4), P_(fr[0] - 10, fr[1] + 4), P_(nr[0] - 40, nr[1] + tbl['leg']), P_(nl[0] + 40, nl[1] + tbl['leg'])],
             (.06, .12, .09), None, 0)
        for (ax, ay), (bx, by) in [((nl[0] + 40, nl[1]), (nl[0] + 40, nl[1] + tbl['leg'])), ((nr[0] - 40, nr[1]), (nr[0] - 40, nr[1] + tbl['leg']))]:
            poly(d, [P_(ax - 9, ay), P_(ax + 9, ay), P_(bx + 9, by), P_(bx - 9, by)], (.15, .15, .17), INK, 2.5 * k)
        # far end face
        poly(d, [P_(*fl), P_(*fr), P_(fr[0], fr[1] + th * .55), P_(fl[0], fl[1] + th * .55)], (.07, .27, .18), INK, 3 * k)
        poly(d, [P_(*nl), P_(*nr), P_(*fr), P_(*fl)], (.12, .45, .3), INK, 3.5 * k)
        # white lines: border and centre line
        lw = 4 * k
        for a, b in [(nl, fl), (nr, fr), (fl, fr)]:
            cv2.line(d, tuple(int(v * F) for v in P_(*a)), tuple(int(v * F) for v in P_(*b)), (1, 1, 1), max(1, int(lw)), cv2.LINE_AA, SH)
        m0 = ((nl[0] + nr[0]) / 2, nl[1]); m1 = ((fl[0] + fr[0]) / 2, fl[1])
        cv2.line(d, tuple(int(v * F) for v in P_(*m0)), tuple(int(v * F) for v in P_(*m1)), (1, 1, 1), max(1, int(lw * .7)), cv2.LINE_AA, SH)
        # net: across the middle
        u = .42; ml = (nl[0] + (fl[0] - nl[0]) * u, nl[1] + (fl[1] - nl[1]) * u); mr = (nr[0] + (fr[0] - nr[0]) * u, nr[1] + (fr[1] - nr[1]) * u)
        nh = 42
        poly(d, [P_(*ml), P_(*mr), P_(mr[0], mr[1] - nh), P_(ml[0], ml[1] - nh)], (.92, .92, .95), INK, 2.5 * k)
        for i in range(1, 16):
            xa = ml[0] + (mr[0] - ml[0]) * i / 16
            cv2.line(d, tuple(int(v * F) for v in P_(xa, ml[1])), tuple(int(v * F) for v in P_(xa, ml[1] - nh)), (.55, .55, .6), 1, cv2.LINE_AA, SH)
        cv2.line(d, tuple(int(v * F) for v in P_(ml[0], ml[1] - nh)), tuple(int(v * F) for v in P_(mr[0], mr[1] - nh)), (1, 1, 1), max(2, int(5 * k)), cv2.LINE_AA, SH)
    # near end's thickness
    poly(d, [P_(*nl), P_(*nr), P_(nr[0], nr[1] + th), P_(nl[0], nl[1] + th)], (.07, .3, .2), INK, 3.5 * k)
    cv2.line(d, tuple(int(v * F) for v in P_(*nl)), tuple(int(v * F) for v in P_(*nr)), (1, 1, 1), max(1, int(4 * k)), cv2.LINE_AA, SH)


def tt_point(tbl, u, v):
    """a point on the table top: u 0 (near end) .. 1 (far end), v 0 (left) .. 1 (right)"""
    (nl, nr), (fl, fr) = tbl['near'], tbl['far']
    a = (nl[0] + (nr[0] - nl[0]) * v, nl[1]); b = (fl[0] + (fr[0] - fl[0]) * v, fl[1])
    # perspective: depth compresses towards the far end
    w = u / (u + (1 - u) * 1.9) if 0 <= u <= 1 else u
    return a[0] + (b[0] - a[0]) * w, a[1] + (b[1] - a[1]) * w


def tt_scale(tbl, u):
    (nl, nr), (fl, fr) = tbl['near'], tbl['far']
    w = u / (u + (1 - u) * 1.9)
    return 1 + ((fr[0] - fl[0]) / (nr[0] - nl[0]) - 1) * w


def box(d, cam, x, y, w, h, rot=0., label='TABLE TENNIS'):
    """a cardboard delivery box, bottom centre (x, y) plate px"""
    k = ck(cam)
    M = cam @ T(x, y) @ R(rot)
    P_ = lambda a, b: tuple((M @ [a, b, 1])[:2])
    dp = w * .28
    front = [P_(-w / 2, 0), P_(w / 2, 0), P_(w / 2, -h), P_(-w / 2, -h)]
    side = [P_(w / 2, 0), P_(w / 2 + dp * .6, -dp * .5), P_(w / 2 + dp * .6, -h - dp * .5), P_(w / 2, -h)]
    top = [P_(-w / 2, -h), P_(w / 2, -h), P_(w / 2 + dp * .6, -h - dp * .5), P_(-w / 2 + dp * .6, -h - dp * .5)]
    poly(d, side, (.62, .44, .26), INK, 3 * k); poly(d, front, (.80, .60, .38), INK, 3 * k); poly(d, top, (.88, .70, .47), INK, 3 * k)
    poly(d, [P_(-w * .06, -h), P_(w * .06, -h), P_(w * .06 + dp * .6, -h - dp * .5), P_(-w * .06 + dp * .6, -h - dp * .5)], (.93, .86, .6), None, 0)
    cx, cy = P_(0, -h * .55)
    text_out(d, label, cx, cy, w * k * .1, fill=(.15, .1, .08), stroke=(.80, .60, .38), sw=1, rot=-rot)
    fx_, fy_ = P_(0, -h * .25)
    text_out(d, 'FRAGILE', fx_, fy_, w * k * .09, fill=(.8, .1, .1), stroke=(.80, .60, .38), sw=1, rot=-rot)


def tumbleweed(d, cam, x, y, r, rot, seed=7):
    k = ck(cam); rng = np.random.default_rng(seed); cx, cy = cpt(cam, x, y); R_ = r * k
    strokes = []
    for i in range(26):
        a0, rr, span, ph = rng.uniform(0, 6.3), rng.uniform(.45, 1.), rng.uniform(.4, 1.1), rng.uniform(0, 6.3)
        a = a0 + rot; c = (cx + .3 * R_ * math.cos(a + ph), cy + .3 * R_ * math.sin(a + ph))
        strokes.append(ipts([(c[0] + rr * R_ * math.cos(a + v), c[1] + rr * R_ * .92 * math.sin(a + v)) for v in np.linspace(0, span * math.pi, 9)]))
    for p in strokes: cv2.polylines(d, [p], False, (.16, .11, .06), max(1, int(round(2.2 * k))), cv2.LINE_AA, SH)
    for i, p in enumerate(strokes): cv2.polylines(d, [p], False, (.86, .72, .47) if i % 2 else (.74, .58, .35), max(1, int(round(1.1 * k))), cv2.LINE_AA, SH)


def wave(d, cam, x, y, t0, t, height, curl=-1., seed=0):
    """a cartoon wave crashing up from the water at plate (x, y): tongues of water rising `height` plate px, curling
    towards `curl` (-1 left, +1 right), throwing drops off their tips; it rises and falls in half a second"""
    a = t - t0
    if a < 0 or a > .6: return
    k = ck(cam); g = math.sin(math.pi * min(1., a / .55)) ** .8
    bx, by = cpt(cam, x, y); H = height * k * g
    if H < 2: return
    rng = np.random.default_rng(seed)
    lw = max(1.5, 3.2 * k)
    for ang, frac in [(-58, .5), (-34, .82), (-12, 1.), (8, .92), (30, .74), (52, .48)]:
        A = math.radians(ang + 22 * curl * g)
        L = H * frac; w = height * k * .12 * (.7 + .3 * frac)
        tip = (bx + L * math.sin(A), by - L * math.cos(A))
        nx, ny = math.cos(A), math.sin(A)
        pts = [(bx - nx * w, by - ny * w)]
        for v in np.linspace(.15, .92, 6):                              # the tongue tapers towards its tip...
            cx_, cy_ = bx + (tip[0] - bx) * v, by + (tip[1] - by) * v; ww = w * (1 - v * .55)
            pts.append((cx_ - nx * ww, cy_ - ny * ww))
        for th in np.linspace(math.pi, 0, 9):                           # ...which is a round drop
            pts.append((tip[0] + w * .45 * (math.cos(th) * nx - math.sin(th) * math.sin(A)),
                        tip[1] + w * .45 * (math.cos(th) * ny + math.sin(th) * math.cos(A))))
        for v in np.linspace(.92, .15, 6):
            cx_, cy_ = bx + (tip[0] - bx) * v, by + (tip[1] - by) * v; ww = w * (1 - v * .55)
            pts.append((cx_ + nx * ww, cy_ + ny * ww))
        pts.append((bx + nx * w, by + ny * w))
        poly(d, pts, (.6, .85, 1.), INK, lw)
        hl = [(bx + (tip[0] - bx) * v - nx * w * .35 * (1 - v * .5), by + (tip[1] - by) * v - ny * w * .35 * (1 - v * .5)) for v in np.linspace(.25, .85, 5)]
        cv2.polylines(d, [ipts(hl)], False, (.92, .98, 1.), max(1, int(w * .22)), cv2.LINE_AA, SH)
    if a > .18:                                                         # drops flung off the top
        for i in range(10):
            ang = rng.uniform(-1.2, 1.2) + .4 * curl; sp = rng.uniform(.7, 1.2) * height * k
            b = a - .18; px = bx + math.sin(ang) * sp * b * 1.6; py = by - H * .9 - math.cos(ang) * sp * b * 1.2 + 900 * k * b * b
            r = rng.uniform(5, 10) * k
            ellipse(d, (px, py), (r * .8, r), 0, (.65, .88, 1.), INK, max(1, 1.4 * k))
    puff(d, bx, by, height * k * .22 * (.6 + .4 * g), (.93, .97, 1.), 1., True, seed)


def whip(d, strength, direction):
    """a whip-pan smear: horizontal motion blur, the picture sliding in `direction` (-1 left, +1 right)"""
    if strength <= .01: return d
    W_ = d.shape[1]; L = int(W_ * .3 * strength) | 1
    k = np.ones((1, L), np.float32) / L
    out = cv2.filter2D(d, -1, k, borderType=cv2.BORDER_REFLECT)
    sh = direction * W_ * .12 * strength
    return cv2.warpAffine(out, np.float32([[1, 0, sh], [0, 1, 0]]), (W_, d.shape[0]), borderMode=cv2.BORDER_REFLECT)


# ---------------------------------------------------------------------------------------------------- table tennis
def bat(d, M, G, u, br, hl):
    """a table-tennis bat held in a hand. G: the grip, u: the direction of the blade from it, br: blade radius, hl: handle
    length, all in the drawing's part px; M maps part px to output px. Drawn before the hand, so the fist covers the
    handle. Returns the blade centre (output px)."""
    G = np.asarray(G, float); u = np.asarray(u, float); u = u / np.linalg.norm(u); v = np.array([-u[1], u[0]])
    P = lambda p: tuple((M @ [p[0], p[1], 1.])[:2])
    s = float(np.linalg.norm(M[:2, 0]))
    a0 = G - u * hl * .7; a1 = G + u * hl * .6; hw = br * .17           # the handle's end shows below the fist
    handle = [P(a0 + v * hw * 1.25), P(a1 + v * hw), P(a1 - v * hw), P(a0 - v * hw * 1.25)]
    C = G + u * (hl * .6 + br * .92)
    ring = lambda r1, r2, c=C: [P(c + u * r1 * math.cos(th) + v * r2 * math.sin(th)) for th in np.linspace(0, 2 * math.pi, 44)]
    lw = max(1.5, s * br * .09)
    poly(d, ring(br * 1.05, br * .96), (.12, .1, .1), INK, lw)               # the dark edge band
    poly(d, ring(br * .88, br * .8), (.84, .1, .12), None, 0)               # red rubber
    poly(d, ring(br * .26, br * .15, C - u * br * .35 + v * br * .3), (.98, .48, .48), None, 0)
    poly(d, handle, (.82, .6, .35), INK, lw)
    cv2.line(d, tuple(int(c * F) for c in P(G + v * hw * .3)), tuple(int(c * F) for c in P(a1 + v * hw * .3)),
             (.95, .78, .52), max(1, int(lw * .7)), cv2.LINE_AA, SH)
    return P(C)


def tt_side(d, cam, x0, x1, y_near, depth=30, thick=16, floor=None, half_up=False, net=True):
    """a table-tennis table seen side-on and a little from above: green top from x0 to x1 (plate px), its near edge at
    y_near, the far edge `depth` px higher; legs to the floor. half_up: the right half folded up for practising alone"""
    k = ck(cam); P = lambda x, y: cpt(cam, x, y); floor = floor or y_near + 170
    lw = max(1.5, 3. * k); sk = depth * .35                               # the far edge is offset a little (perspective)
    xm = (x0 + x1) / 2; X0 = x0
    shadow_pts = [P(x0 + 30, floor), P(x1 - 30, floor), P(x1 - 50, floor + 18), P(x0 + 50, floor + 18)]
    layer = d.copy(); poly(layer, shadow_pts, (0, 0, 0), None, 0); cv2.GaussianBlur(layer, (0, 0), 6 * k, dst=layer)
    d[:] = d * .75 + layer * .25
    # legs: far pair darker, then the near pair
    for lx, dark in [(X0 + 45 + sk, True), (x1 - 45 + sk, True), (X0 + 45, False), (x1 - 45, False)]:
        yy = y_near - (depth if dark else 0)
        poly(d, [P(lx - 7, yy), P(lx + 7, yy), P(lx + 7, floor - (depth * .6 if dark else 0)), P(lx - 7, floor - (depth * .6 if dark else 0))],
             (.12, .12, .14) if dark else (.22, .22, .25), INK, lw * .8)
    poly(d, [P(x0 + 45, (y_near + floor) / 2), P(x1 - 45, (y_near + floor) / 2), P(x1 - 45, (y_near + floor) / 2 + 9),
             P(x0 + 45, (y_near + floor) / 2 + 9)], (.2, .2, .23), INK, lw * .7)
    xr = x1
    if half_up: x0 = xm
    top = [P(x0, y_near), P(xr, y_near), P(xr + sk, y_near - depth), P(x0 + sk, y_near - depth)]
    poly(d, top, (.1, .45, .3), INK, lw)
    poly(d, [P(x0, y_near), P(xr, y_near), P(xr, y_near + thick), P(x0, y_near + thick)], (.06, .3, .2), INK, lw)
    for a_, b_ in [((x0 + 3, y_near - 2), (xr - 3, y_near - 2)), ((x0 + sk + 3, y_near - depth + 2), (xr + sk - 3, y_near - depth + 2)),
                   ((x0 + 4, y_near - 2), (x0 + sk + 4, y_near - depth + 2))]:
        cv2.line(d, tuple(int(c * F) for c in P(*a_)), tuple(int(c * F) for c in P(*b_)), (1, 1, 1), max(1, int(2.6 * k)), cv2.LINE_AA, SH)
    cv2.line(d, tuple(int(c * F) for c in P(x0 + 4, y_near - depth / 2)), tuple(int(c * F) for c in P(xr, y_near - depth / 2)),
             (1, 1, 1), max(1, int(1.6 * k)), cv2.LINE_AA, SH)
    if half_up:                                                             # the left half stands up like a wall
        hh = xm - X0
        poly(d, [P(xm, y_near), P(xm + sk, y_near - depth), P(xm + sk, y_near - depth - hh), P(xm, y_near - hh)], (.08, .38, .26), INK, lw)
        poly(d, [P(xm - 10, y_near), P(xm, y_near), P(xm, y_near - hh), P(xm - 10, y_near - hh)], (.05, .25, .17), INK, lw * .8)
        cv2.line(d, tuple(int(c * F) for c in P(xm + 3, y_near - 4)), tuple(int(c * F) for c in P(xm + 3, y_near - hh + 4)), (1, 1, 1),
                 max(1, int(2.4 * k)), cv2.LINE_AA, SH)
    elif net:
        nh = 30
        poly(d, [P(xm, y_near), P(xm + sk, y_near - depth), P(xm + sk, y_near - depth - nh), P(xm, y_near - nh)], (.93, .93, .96), INK, lw * .8)
        for i in range(1, 6):
            yy = y_near - nh * i / 6
            cv2.line(d, tuple(int(c * F) for c in P(xm, yy)), tuple(int(c * F) for c in P(xm + sk, yy - depth)), (.6, .6, .66), 1, cv2.LINE_AA, SH)
        cv2.line(d, tuple(int(c * F) for c in P(xm, y_near - nh)), tuple(int(c * F) for c in P(xm + sk, y_near - depth - nh)), (1, 1, 1),
                 max(2, int(4 * k)), cv2.LINE_AA, SH)


def tt_ball(d, cam, x, y, r, trail=()):
    """the ball, with a fading trail of where it has just been (plate px)"""
    k = ck(cam)
    for i, (tx, ty) in enumerate(trail):
        f = (i + 1) / (len(trail) + 1)
        layer = d.copy(); q = cpt(cam, tx, ty); ellipse(layer, q, (r * k * (.5 + .4 * f),) * 2, 0, (1, 1, 1), None, 0)
        d[:] = d * (1 - .45 * f) + layer * .45 * f
    q = cpt(cam, x, y)
    ellipse(d, q, (r * k, r * k), 0, (1, .99, .95), INK, max(1.2, r * k * .2))
    ellipse(d, (q[0] - r * k * .3, q[1] - r * k * .3), (r * k * .3, r * k * .25), 0, (1, 1, 1), None, 0)


# ---------------------------------------------------------------------------------------------------- perspective table
class Persp:
    """a pinhole camera over the pitch: metres (X right, Y up, Z away) -> plate px. f: focal length in plate px, yh: the
    horizon's plate y, h: camera height (m)"""
    def __init__(self, f=2200., yh=280., h=3.6, cx=470.):
        self.f, self.yh, self.h, self.cx = f, yh, h, cx

    def p(self, X, Y, Z): return (self.cx + self.f * X / Z, self.yh + self.f * (self.h - Y) / Z)

    def k(self, Z): return self.f / Z                                   # plate px per metre at depth Z


def tt_table3(d, cam, pc, C, ax, half_up=False, L=2.74, Wd=1.525, Ht=.76):
    """a regulation table centred at C = (X, Z) with its long axis ax (unit, in the X-Z plane), seen through pc"""
    k = ck(cam); C = np.array(C, float); ax = np.array(ax, float); ax /= np.linalg.norm(ax); pr = np.array([ax[1], -ax[0]])
    def P(v, Y): return cpt(cam, *pc.p(v[0], Y, v[1]))
    n0 = C - ax * L / 2; n1 = C + ax * L / 2; mid = C
    corners = lambda e: (e - pr * Wd / 2, e + pr * Wd / 2)              # (left, right) looking from the near end
    nl, nr = corners(n0); fl, fr = corners(n1); ml, mr = corners(mid)
    lw = max(1.5, 3 * k); th = .04
    # shadow
    sh = d.copy(); poly(sh, [P(nl, 0), P(nr, 0), P(fr, 0), P(fl, 0)], (0, 0, 0), None, 0); sh = cv2.GaussianBlur(sh, (0, 0), 8 * k)
    d[:] = d * .72 + sh * .28
    # legs (inset from the corners), the far ones first
    ins = lambda a, b, c_: a + (b - a) * .12 + (c_ - a) * .1
    legs = [ins(fl, fr, nl), ins(fr, fl, nr), ins(nl, nr, fl), ins(nr, nl, fr)]
    for i, lg in enumerate(legs):
        a_, b_ = P(lg, Ht - th), P(lg, 0)
        w_ = .035 * pc.k(lg[1]) * k
        poly(d, [(a_[0] - w_, a_[1]), (a_[0] + w_, a_[1]), (b_[0] + w_, b_[1]), (b_[0] - w_, b_[1])], (.14, .14, .16) if i < 2 else (.24, .24, .27), INK, lw * .7)
    green, dark = (.1, .45, .3), (.05, .28, .19)
    far_top = (fl, fr) if not half_up else (ml, mr)
    # the visible sides: the near end and the right-hand side
    poly(d, [P(nl, Ht), P(nr, Ht), P(nr, Ht - th), P(nl, Ht - th)], dark, INK, lw)
    poly(d, [P(nr, Ht), P(far_top[1], Ht), P(far_top[1], Ht - th), P(nr, Ht - th)], dark, INK, lw)
    poly(d, [P(nl, Ht), P(nr, Ht), P(far_top[1], Ht), P(far_top[0], Ht)], green, INK, lw)
    def line(a, b, Y=Ht, w=2.6):
        cv2.line(d, tuple(int(c * F) for c in P(a, Y)), tuple(int(c * F) for c in P(b, Y)), (1, 1, 1), max(1, int(w * k)), cv2.LINE_AA, SH)
    e = .025
    for a, b in [(nl, nr), (nl, far_top[0]), (nr, far_top[1])] + ([] if half_up else [(fl, fr)]):
        line(a + (C - a) * .0 + (mid - a) * 0, b)
    line(n0, mid if half_up else n1, w=1.6)
    if half_up:                                                         # the far half folded up into a wall
        hh = L / 2
        wl = [P(ml, Ht), P(mr, Ht), P(mr, Ht + hh), P(ml, Ht + hh)]
        poly(d, wl, (.08, .38, .26), INK, lw)
        line(ml, mr, Ht + hh - .02); line(ml, ml, Ht)
    else:                                                               # the net across the middle
        nh = .1525
        poly(d, [P(ml, Ht), P(mr, Ht), P(mr, Ht + nh), P(ml, Ht + nh)], (.92, .92, .96), INK, lw * .7)
        for i in range(1, 9):
            v = ml + (mr - ml) * i / 9
            cv2.line(d, tuple(int(c * F) for c in P(v, Ht)), tuple(int(c * F) for c in P(v, Ht + nh)), (.6, .6, .66), 1, cv2.LINE_AA, SH)
        cv2.line(d, tuple(int(c * F) for c in P(ml, Ht + nh)), tuple(int(c * F) for c in P(mr, Ht + nh)), (1, 1, 1), max(2, int(4 * k)), cv2.LINE_AA, SH)


def ball_machine(d, cam, x, y, s, t, fired=0.):
    """a cartoon table-tennis robot standing on the table at plate (x, y) (bottom centre), s plate px per unit (~ its width);
    `fired` (0..1) kicks the nozzle back after each shot"""
    k = ck(cam); P = lambda a, b: cpt(cam, x + a * s, y - b * s); lw = max(1.5, 2.6 * k)
    poly(d, [P(-.5, 0), P(.5, 0), P(.42, .9), P(-.42, .9)], (.9, .32, .12), INK, lw)          # body
    poly(d, [P(-.38, .78), P(.38, .78), P(.3, .9), P(-.3, .9)], (1, .55, .3), None, 0)
    for i in range(3):                                                                      # vents
        poly(d, [P(-.3, .2 + .14 * i), P(.1, .2 + .14 * i), P(.1, .26 + .14 * i), P(-.3, .26 + .14 * i)], (.45, .12, .05), None, 0)
    kick = .12 * fired
    poly(d, [P(.35 - kick, .55), P(.9 - kick, .62), P(.9 - kick, .78), P(.35 - kick, .78)], (.25, .25, .28), INK, lw)  # nozzle
    poly(d, [P(-.42, .9), P(.42, .9), P(.6, 1.45), P(-.6, 1.45)], (.75, .85, .95), INK, lw)  # the hopper
    for i, (bx, by) in enumerate([(-.38, 1.05), (-.13, 1.08), (.12, 1.06), (.37, 1.07), (-.25, 1.28), (0, 1.3), (.25, 1.28)]):
        q = P(bx, by); ellipse(d, q, (.13 * s * k,) * 2, 0, (1, 1, 1), INK, max(1, lw * .6))
    q = P(-.2, .55); ellipse(d, q, (.09 * s * k,) * 2, 0, (.3, 1, .4) if math.sin(t * 20) > 0 else (.1, .4, .15), INK, max(1, lw * .5))


def cardboard(a, pad=10):
    """a drawing (RGBA uint8) turned into a cardboard cut-out: the figure on a cardboard backing with a cut edge"""
    al = a[..., 3]
    k_ = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * pad + 1, 2 * pad + 1))
    m = np.pad(al, pad + 4); big = cv2.dilate((m > 40).astype(np.uint8), k_)
    edge = cv2.dilate(big, np.ones((5, 5), np.uint8)) - big
    out = np.zeros(m.shape + (4,), np.uint8)
    out[big > 0] = (205, 168, 112, 255)                                    # cardboard
    out[edge > 0] = (40, 28, 20, 255)                                      # its cut, inked edge
    fig = np.pad(a, ((pad + 4, pad + 4), (pad + 4, pad + 4), (0, 0)))
    fa = fig[..., 3:4].astype(np.float32) / 255
    out[..., :3] = np.uint8(fig[..., :3] * fa + out[..., :3] * (1 - fa))
    return out

"""Everything over and around the characters.

comp(s, t) draws most shots: it renders the inner single or world (studio.film.render), switching drawings on cue
(keys), and puts the gags on it: the unzip wipe and its glow, the plant going off (soil, a white flash, the rise),
crash zooms, shakes, confetti, sweat, the Zs, the freeze frames, the night grade.

The inserts: the conspiracy board (and the white mug in its evidence bag), the 2019 back page, the door lock, the
clock, the laptop (the live page, the goal, the penalty), the plant's remains, the tablet, the end card.

The props the shots draw in place: the hedge (and the binoculars), the plant (and the boots under it), the blinds,
the door sign, the slides, Omar's desk (a City mug, his monitor). All layout in 1920 x 1080 px, scaled by RS."""
import functools
import json
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from studio.film import ep
from studio.film.engine import OH, OW, RS
from film import sprites as SP

BEBAS = "library/fonts/BebasNeue-Regular.ttf"
INTER = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
INTER_R = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
INTER_X = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
YELLOW = (255, 205, 0)
LBLUE = (29, 66, 138)


@functools.lru_cache(maxsize=64)
def F(size, kind="b"):
    from studio.paths import ROOT
    path = {"b": INTER, "r": INTER_R, "x": INTER_X, "bebas": str(ROOT / BEBAS)}[kind]
    try:
        return ImageFont.truetype(path, max(8, int(size * RS)))
    except OSError:
        return ImageFont.truetype(str(ROOT / BEBAS), max(8, int(size * RS)))


def P(v):
    return int(round(v * RS))


def sm(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def over(img, lay):
    a = np.asarray(lay).astype(np.float32) / 255.0
    return img * (1 - a[..., 3:4]) + a[..., :3] * a[..., 3:4]


TLD = json.loads(ep.path("lines.json").read_text())


@functools.lru_cache(maxsize=1)
def marks():
    from film.timeline import TL
    from studio.film.shots import Marks
    return Marks(TL, TLD)


def to_lay(lay, spr, x, y, s, ang=0.0, anchor=None, flip=False):
    """a sprite onto a premultiplied RGBA layer (the actors' layer of a single)"""
    tmp = np.zeros((lay.shape[0], lay.shape[1], 3), np.float32)
    a = np.zeros((lay.shape[0], lay.shape[1], 3), np.float32)
    SP.paste(tmp, spr, x, y, s, ang, anchor, flip=flip)
    white = np.concatenate([spr[..., :3] * 0 + 255, spr[..., 3:4]], 2).astype(np.uint8)
    SP.paste(a, white, x, y, s, ang, anchor, flip=flip)
    al = a[..., :1]
    lay[..., :3] = lay[..., :3] * (1 - al) + tmp
    lay[..., 3:4] = lay[..., 3:4] * (1 - al) + al
    return lay


# ---------------------------------------------------------------- the inner shot
def _render(sh, t):
    from studio.film import render as R
    if sh["kind"] == "world":
        return R.render_world(sh, t)
    return R.render_single(sh, t)


def _keyed(s, t):
    sh = dict(s["inner"])
    for tk, dk in s.get("keys", []):
        if t >= tk:
            sh["draw"] = dk
    return sh


def comp(s, t):
    tt = s["freeze"] if s.get("freeze") is not None and t >= s["freeze"] else t
    sh = _keyed(s, tt)
    if s.get("rise"):                                       # rising out of the plant: up from below the frame
        t0, d = s["rise"]
        u = sm((tt - t0) / d)
        sh = dict(sh, eye=(sh["eye"][0], sh["eye"][1] + (1 - u) * 700))
    img = _render(sh, tt)
    if s.get("wipe"):
        img = _wipe(img, s, sh, tt)
    if s.get("glow"):
        a, b = s["glow"]
        if a <= t <= b:
            k = sm((t - a) / 0.6) * (1 - sm((t - (b - 0.3)) / 0.3))
            img = _glow(img, k, t)
    if s.get("soil") is not None:
        img = _soil(img, t, s["soil"])
    if s.get("confetti") is not None:
        img = _confetti(img, t, s["confetti"])
    if s.get("sweat"):
        img = _sweat(img, t, s)
    if s.get("zzz"):
        img = _zzz(img, t, s["zzz"])
    if s.get("night"):
        img = night(img)
    if s.get("flash") is not None:
        k = t - s["flash"]
        if 0 <= k < 0.25:
            img = img + (1 - img) * (1 - k / 0.25)
    if s.get("crash") is not None:
        img = _crash(img, t, s["crash"])
    if s.get("shake"):
        img = _shake(img, t, s["shake"])
    if s.get("whoosh_in") is not None and t - s["whoosh_in"] < 0.18:
        img = _blur_x(img, 1 - (t - s["whoosh_in"]) / 0.18)
    if s.get("freeze") is not None and t >= s["freeze"]:
        img = _frozen(img, t - s["freeze"])
    return img


def night(img):
    """night: the lights off, a blue cast, one lamp's warmth left in the middle"""
    l = img.mean(2, keepdims=True)
    img = l + (img - l) * 0.55
    img = img * np.float32([0.55, 0.62, 0.9]) * 0.82
    X = np.linspace(-1, 1, OW, dtype=np.float32)[None, :, None]
    Y = np.linspace(-1, 1, OH, dtype=np.float32)[:, None, None]
    pool = np.exp(-(X ** 2 / 0.5 + (Y + 0.1) ** 2 / 0.9))
    return img * (0.75 + 0.45 * pool)


def _frozen(img, k):
    """freeze frame: drained of colour, a punch-in, a white edge"""
    l = img.mean(2, keepdims=True)
    img = l + (img - l) * 0.35
    img = (img - 0.5) * 1.12 + 0.5
    z = 1.0 + 0.04 * sm(k / 0.2)
    M = cv2.getRotationMatrix2D((OW / 2, OH / 2), 0, z)
    img = cv2.warpAffine(img, M, (OW, OH), borderMode=cv2.BORDER_REFLECT)
    if k < 0.12:
        img = img + (1 - img) * 0.5 * (1 - k / 0.12)
    return img


def _blur_x(img, k):
    n = max(1, int(60 * k * RS))
    return cv2.blur(img, (n, 1))


def _crash(img, t, tc):
    k = t - tc
    if -0.04 <= k < 0.3:
        img = img + (1 - img) * 0.35 * math.exp(-max(0.0, k) / 0.06)
        if k < 0.12:
            acc = img.copy()
            for i in range(1, 5):
                M = cv2.getRotationMatrix2D((OW / 2, OH / 2), 0, 1 + 0.015 * i * (1 - k / 0.12))
                acc += cv2.warpAffine(img, M, (OW, OH), borderMode=cv2.BORDER_REFLECT)
            img = acc / 5
    return img


def _shake(img, t, spec):
    a, b, amp0 = spec
    if a <= t <= b:
        amp = amp0 * RS * (1 - 0.6 * (t - a) / max(1e-3, b - a))
        dx, dy = amp * math.sin(t * 91), amp * math.cos(t * 77)
        img = cv2.warpAffine(img, np.float32([[1.03, 0, dx - 0.015 * OW], [0, 1.03, dy - 0.015 * OH]]), (OW, OH),
                             borderMode=cv2.BORDER_REFLECT)
    return img


def _glow(img, k, t):
    """the reveal: a soft heavenly bloom and a lens flare streak across"""
    b = cv2.GaussianBlur(img, (0, 0), 24 * RS)
    img = img + b * 0.45 * k
    X = np.linspace(0, 1, OW, dtype=np.float32)[None, :, None]
    Y = np.linspace(0, 1, OH, dtype=np.float32)[:, None, None]
    streak = np.exp(-((Y - 0.32) / 0.012) ** 2) * (0.6 + 0.4 * np.sin(X * 9 + t * 2))
    img = img + streak * np.float32([1.0, 0.95, 0.75]) * 0.5 * k
    return np.clip(img, 0, 1)


def _wipe(img, s, sh, t):
    """the unzip: the Leeds top revealed from the collar down, the opening widening as the zip goes"""
    a, b, draw2 = s["wipe"]
    if t < a:
        return img
    other = _render(dict(sh, draw=draw2), t)
    u = sm((t - a) / (b - a))
    ex, ey = sh["eye"][0] * RS, sh["eye"][1] * RS
    ed = sh["ed"] * RS * (sh["push"][0] + (sh["push"][1] - sh["push"][0]) * sm((t - sh["t"]) / max(1e-3, sh["end"] - sh["t"])))
    y0, y1 = ey + 0.9 * ed, ey + 5.2 * ed
    yw = y0 + (y1 - y0) * u
    Y, X = np.mgrid[0:OH, 0:OW].astype(np.float32)
    half = 0.25 * ed + 3.2 * ed * np.clip((yw - Y) / max(1.0, yw - y0 + 1e-3), 0, 1) ** 0.6
    m = ((np.abs(X - ex) < half) & (Y < yw)) | (Y < y0)
    if u >= 0.999:
        m[:] = True
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 3 * RS)[..., None]
    return img * (1 - m) + other * m


@functools.lru_cache(maxsize=1)
def _particles():
    rng = np.random.default_rng(7)
    n = 140
    return dict(ang=rng.uniform(-math.pi * 0.95, -math.pi * 0.05, n), v=rng.uniform(700, 1900, n),
                r=rng.uniform(6, 22, n), kind=rng.choice([0, 0, 0, 1, 2], n), spin=rng.uniform(-8, 8, n),
                col=rng.uniform(0.75, 1.15, n))


def _soil(img, t, t0):
    """the plant going off: soil, leaves and bits of pot flying out and falling"""
    k = t - t0
    if k < 0 or k > 2.2:
        return img
    p = _particles()
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy = OW * 0.52, OH * 0.95
    for a, v, r, kind, spin, c in zip(p["ang"], p["v"], p["r"], p["kind"], p["spin"], p["col"]):
        x = cx + math.cos(a) * v * k * RS
        y = cy + (math.sin(a) * v * k + 1900 * k * k) * RS
        if not (-50 < x < OW + 50 and -50 < y < OH + 50):
            continue
        rr = r * RS
        if kind == 0:
            col = tuple(int(min(255, ch * c)) for ch in (92, 60, 36)) + (255,)
            d.ellipse([x - rr, y - rr * 0.8, x + rr, y + rr * 0.8], fill=col, outline=(30, 20, 12, 255))
        elif kind == 1:
            ang = spin * k
            pts = [(x + math.cos(ang + q) * rr * 2.2 * (1 if i % 2 == 0 else 0.35),
                    y + math.sin(ang + q) * rr * 2.2 * (1 if i % 2 == 0 else 0.35))
                   for i, q in enumerate(np.linspace(0, 2 * math.pi, 9)[:-1])]
            d.polygon(pts, fill=(70, 150, 62, 255), outline=(24, 40, 20, 255))
        else:
            ang = spin * k
            pts = [(x + math.cos(ang + q) * rr * 1.3, y + math.sin(ang + q) * rr) for q in (0, 2.1, 4.0)]
            d.polygon(pts, fill=(196, 104, 64, 255), outline=(40, 20, 10, 255))
    return over(img, lay)


def _confetti(img, t, t0):
    """Leeds-coloured confetti: yellow, blue and white, falling and fluttering"""
    k = t - t0
    if k < 0:
        return img
    rng = np.random.default_rng(11)
    n = 160
    xs, v0 = rng.uniform(0, 1920, n), rng.uniform(-900, -300, n)
    ph, cols = rng.uniform(0, 6.3, n), rng.integers(0, 3, n)
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for x0, v, p_, c in zip(xs, v0, ph, cols):
        y = 1080 + v * k + 520 * k * k - 40
        if not -20 < y < 1100:
            continue
        x = x0 + 30 * math.sin(k * 5 + p_)
        w = 14 * abs(math.cos(k * 7 + p_)) + 3
        col = (YELLOW, LBLUE, (250, 250, 250))[c] + (255,)
        d.rectangle([P(x - w), P(y - 9), P(x + w), P(y + 9)], fill=col)
    return over(img, lay)


def _sweat(img, t, s):
    a, b = s["sweat"]
    if not a <= t <= b:
        return img
    sh = s["inner"]
    ex, ey = sh["eye"][0], sh["eye"][1]
    ed = sh["ed"] * (sh["push"][0] + (sh["push"][1] - sh["push"][0]) * sm((t - sh["t"]) / max(1e-3, sh["end"] - sh["t"])))
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i, (dx, dy0, sp) in enumerate([(-1.3, -1.6, 0.55), (1.2, -1.9, 0.7), (-0.2, -2.2, 0.45), (1.5, -1.2, 0.6)]):
        k = ((t - a) * sp + i * 0.37) % 1.0
        x = ex + dx * ed
        y = ey + (dy0 + 1.2 * k) * ed
        r = 0.16 * ed
        pts = [(P(x), P(y - 1.8 * r)), (P(x + r), P(y)), (P(x), P(y + r)), (P(x - r), P(y))]
        d.polygon(pts, fill=(180, 220, 255, 230), outline=(40, 70, 110, 255))
        d.ellipse([P(x - r), P(y - r * 0.2), P(x + r), P(y + r)], fill=(180, 220, 255, 230), outline=(40, 70, 110, 255))
    return over(img, lay)


def _zzz(img, t, span):
    a, b = span
    if not a <= t <= b:
        return img
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for i in range(3):
        k = ((t - a) * 0.6 + i / 3) % 1.0
        x, y = 470 - 90 * k + 20 * math.sin(k * 9), 420 - 250 * k
        f = F(60 + 50 * k, "bebas")
        d.text((P(x), P(y)), "Z", font=f, fill=(255, 255, 255, int(255 * (1 - k))), stroke_width=P(3),
               stroke_fill=(20, 20, 20, int(255 * (1 - k))))
    return over(img, lay)


# ---------------------------------------------------------------- props on a single (the actors' layer)
def _parted(s, t):
    v = 0.0
    for tk, val in s.get("part", []):
        if t >= tk:
            v0, t0 = v, tk
            v = val
            v = v0 + (val - v0) * sm((t - t0) / 0.35)
    return v


def _plant_geom(ex, ey, ed):
    """the plant round a face: its scale and where its pivot (the top of the pot) sits on screen"""
    p = SP.plant(True)
    s = ed * 11.0 / p["size"][0]
    px, py = ex, ey + 2.9 * ed
    return p, s, px, py


def plant_back(lay, s, t, ex, ey, ed, st):
    p, sc, px, py = _plant_geom(ex, ey, ed)
    return to_lay(lay, p["back"], px, py, sc, 0.0, anchor=p["pivot"])


def plant_front(lay, s, t, ex, ey, ed, st):
    p, sc, px, py = _plant_geom(ex, ey, ed)
    to_lay(lay, p["pot"], px, py, sc, 0.0, anchor=p["pivot"])
    a = 30 * _parted(s, t)
    wob = 1.5 * math.sin(t * 3.1)
    to_lay(lay, p["fl"], px, py, sc, -a + wob, anchor=p["pivot"])
    to_lay(lay, p["fr"], px, py, sc, a + wob, anchor=p["pivot"])
    return lay


def hedge_cu(lay, s, t, ex, ey, ed, st):
    """he is in the hedge: the hedge in front up to his chin; the binoculars over his eyes until his line"""
    M = marks()
    h = SP.hedge()
    sc = ed * 22.0 / h.shape[1]
    rustle = 3 * math.sin(t * 17) if M.m("slurp") <= t <= M.m("slurp") + 1.1 else 0.0
    to_lay(lay, h, ex + rustle, ey + 1.45 * ed + (h.shape[0] - 120) * sc, sc)
    down = sm((t - (M.ls("L004") - 0.45)) / 0.3)
    if down < 1:
        b = SP.binoculars("front")
        bs = ed * 2.6 / b.shape[1]
        to_lay(lay, b, ex, ey + 0.3 * ed * 1.7 + down * 2.5 * ed, bs, anchor=(350, 180 + 0.3 * 0))
        to_lay(lay, h, ex + rustle, ey + 1.45 * ed + (h.shape[0] - 120) * sc, sc)
    return lay


def laptop_lid(lay, s, t, ex, ey, ed, st):
    """the back of his open laptop at the bottom of the frame, a little Leeds sticker on it"""
    im = _lid()
    to_lay(lay, im, ex, OH / RS * RS + 40 * RS, ed * 6.0 / im.shape[1])
    return lay


@functools.lru_cache(maxsize=1)
def _lid():
    W, H = 1400, 620
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(80, 40), (1320, 40), (1360, 620), (40, 620)], fill=(70, 72, 78, 255), outline=(15, 15, 18, 255))
    d.line([(80, 40), (1320, 40), (1360, 620), (40, 620), (80, 40)], fill=(15, 15, 18, 255), width=14)
    d.polygon([(110, 60), (1290, 60), (1300, 110), (100, 110)], fill=(96, 98, 106, 255))
    cx, cy = 1040, 300                                                       # the sticker
    d.ellipse([cx - 70, cy - 70, cx + 70, cy + 70], fill=(250, 250, 250, 255), outline=(15, 15, 18, 255), width=6)
    d.polygon([(cx - 42, cy - 40), (cx + 42, cy - 40), (cx + 42, cy + 8), (cx, cy + 46), (cx - 42, cy + 8)],
              fill=LBLUE + (255,), outline=YELLOW + (255,))
    d.ellipse([cx - 14, cy - 22, cx + 14, cy + 4], fill=(255, 255, 255, 255))
    return np.asarray(im).copy()


# ---------------------------------------------------------------- props in a world (plate px -> screen)
def _feet_paste(img, spr, M, x, y, h_plate, anchor=None, ang=0.0, flip=False):
    sc = M[0, 0]
    s = h_plate * sc / spr.shape[0]
    return SP.paste(img, spr, M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2], s, ang, anchor, flip=flip)


@functools.lru_cache(maxsize=2)
def plant_whole(boots=True, open_=0.0):
    """the whole plant flattened into one sprite (for the wides)"""
    p = SP.plant(boots)
    W, H = p["size"]
    img = np.zeros((H, W, 3), np.float32)
    al = np.zeros((H, W, 3), np.float32)
    for k in ("back", "pot", "fl", "fr"):
        a = -26 * open_ if k == "fl" else 26 * open_ if k == "fr" else 0.0
        SP.paste(img, p[k], p["pivot"][0], p["pivot"][1], 1.0, a, anchor=p["pivot"])
        white = np.concatenate([p[k][..., :3] * 0 + 255, p[k][..., 3:4]], 2).astype(np.uint8)
        SP.paste(al, white, p["pivot"][0], p["pivot"][1], 1.0, a, anchor=p["pivot"])
    out = np.dstack([np.clip(img / np.maximum(al, 1e-3), 0, 1) * 255, al[..., :1] * 255]).astype(np.uint8)
    ys = np.nonzero(out[..., 3].max(1) > 0)[0]
    return out[ys.min():ys.max() + 1]


def corridor_plant(img, s, t, M, sc):
    from film.direction import CORR_PLANT
    x, y, h = CORR_PLANT
    k = t - s["t"]
    steps = [0.7, 1.5, 2.4, 3.1]
    dx = sum(sm((k - a) / 0.12) for a in steps) * 16
    hop = sum(math.sin(math.pi * min(1, max(0, (k - a) / 0.12))) for a in steps) * 6
    return _feet_paste(img, plant_whole(True), M, x + dx, y - hop, h)


def office_plant(img, s, t, M, sc):
    from film.direction import OFFICE_PLANT
    x, y, h = OFFICE_PLANT
    return _feet_paste(img, plant_whole(True), M, x, y, h)


def locker_plant(img, s, t, M, sc):
    from film.direction import LOCKER_PLANT
    x, y, h = LOCKER_PLANT
    return _feet_paste(img, plant_whole(False), M, x, y, h)


def hedge_wide(img, s, t, M, sc):
    """the hedge across the bottom of the frame; the binoculars poking out of its front, sweeping slowly"""
    h = SP.hedge()
    SP.paste(img, h, OW * 0.5, OH + 160 * RS, OW * 1.15 / h.shape[1])
    b = SP.binoculars("side")
    k = t - s["t"]
    ang = -6 + 9 * math.sin(k * 0.9)
    SP.paste(img, b, OW * 0.50, OH * 0.70, 0.5 * RS, ang, anchor=(60, 180))
    SP.paste(img, _hedge_bump(), OW * 0.47, OH * 0.80, 0.55 * RS)
    return img


@functools.lru_cache(maxsize=1)
def _hedge_bump():
    h = SP.hedge(seed=9, W=600, H=300)
    return h


def two_hedges(img, s, t, M, sc):
    """outside Sir Jim's office: two hedges and a little sign. Licho in the left one (his line), a white mug rising
    out of the right one (the sip)"""
    from studio.film import render as R
    M_ = marks()
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, y0 = P(890), P(560)                                               # the sign on its post
    d.rectangle([x0 - P(8), y0, x0 + P(8), y0 + P(330)], fill=(60, 60, 64, 255))
    d.rounded_rectangle([x0 - P(190), y0 - P(110), x0 + P(190), y0 + P(10)], radius=P(10), fill=(250, 250, 250, 255),
                        outline=(20, 20, 20, 255), width=P(5))
    d.text((x0, y0 - P(78)), "SIR JIM RATCLIFFE", font=F(38, "bebas"), fill=(200, 16, 30, 255), anchor="mm")
    d.text((x0, y0 - P(30)), "PRIVATE OFFICE", font=F(30, "bebas"), fill=(30, 30, 30, 255), anchor="mm")
    img = over(img, lay)
    # Licho in the left hedge
    sh = dict(s, kind="single", who="licho", draw="lisandro-martinez:c-crouch", bg=None, fg=None)
    lay2 = np.zeros((OH, OW, 4), np.float32)
    from studio.film import engine as E
    from studio.film.cast import CAST
    d_, info = CAST.get("lisandro-martinez:c-crouch")
    st = R.PERF.state("licho", t, lambda g: (0.25, 0.0, 0.1) if g != "cam" else (0, 0, 0), s["t"])
    ex, ey, ed = 470 * RS, 520 * RS, 92 * RS
    Ms = R.actor_matrix(info, ex, ey, ed / info["ed"], False, st["lean"], st["sink"])
    E.place(lay2, d_, R.face_state(st, info, False), Ms)
    img = img * (1 - lay2[..., 3:4]) + lay2[..., :3]
    h = SP.hedge(seed=5, W=900, H=700)
    SP.paste(img, h, P(440), P(1080), 0.8 * RS)
    # the mug from the right hedge
    k = t - M_.m("sip")
    up = sm(k / 0.4) * (1 - sm((k - 1.6) / 0.4))
    tilt = 28 * sm((k - 0.5) / 0.3) * (1 - sm((k - 1.3) / 0.3))
    SP.paste(img, SP.mug(), P(1430), P(880) - up * P(260), 0.42 * RS, -tilt, anchor=(170, 400))
    h2 = SP.hedge(seed=8, W=900, H=700)
    SP.paste(img, h2, P(1430), P(1080), 0.8 * RS)
    return img


def blinds(img, s, t, M, sc):
    """the office window's blinds coming down on his line"""
    M_ = marks()
    u = sm((t - (M_.ls("L022") + 0.4)) / 1.0)
    x0, x1, y0, y1 = 8, 392, 18, 410                                       # the window (1x plate px)
    yb = y0 + (y1 - y0) * u
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    S = lambda x, y: (M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2])
    xa, ya = S(x0, y0)
    xb, yb_ = S(x1, yb)
    n = max(1, int((yb - y0) / 14))
    for i in range(n):
        yy = ya + (yb_ - ya) * (i / n)
        d.rectangle([xa, yy, xb, yy + (yb_ - ya) / n * 0.85], fill=(226, 222, 210, 255), outline=(150, 145, 130, 255))
    if u > 0:
        d.rectangle([xa, yb_ - 6 * RS, xb, yb_ + 2 * RS], fill=(180, 175, 160, 255))
    return over(img, lay)


def door_sign(img, s, t, M, sc):
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    S = lambda x, y: (M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2])
    xa, ya = S(1385, 300)
    xb, yb = S(1575, 345)
    d.rectangle([xa, ya, xb, yb], fill=(235, 235, 235, 255), outline=(20, 20, 20, 255), width=max(1, int(2 * RS)))
    f = ImageFont.truetype(F(10, "bebas").path, max(8, int((yb - ya) * 0.62)))
    d.text(((xa + xb) / 2, (ya + yb) / 2), "DIRECTOR OF FOOTBALL", font=f, fill=(20, 20, 20, 255), anchor="mm")
    return over(img, lay)


# the tactics room screen's corners (1x plate px): top-left, top-right, bottom-right, bottom-left
SCREEN = [(828, 32), (1478, 18), (1476, 492), (830, 468)]


def slides(img, s, t, M, sc):
    """the PowerPoint on the big screen: slide 1, the chart with one bar and no axis, slide 213"""
    M_ = marks()
    if t >= M_.m("cut_asleep"):
        page = _slide(3)
    elif t >= M_.wt("L044", "commitment") - 0.1:
        page = _slide(2)
    else:
        page = _slide(1)
    src = np.float32([[0, 0], [page.shape[1], 0], [page.shape[1], page.shape[0]], [0, page.shape[0]]])
    dst = np.float32([[M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]] for x, y in SCREEN])
    H = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(page, H, (OW, OH), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
    a = warped[..., 3:4].astype(np.float32) / 255.0
    return img * (1 - a) + warped[..., :3].astype(np.float32) / 255.0 * a


@functools.lru_cache(maxsize=4)
def _slide(n):
    W, H = 1600, 1100
    im = Image.new("RGBA", (W, H), (250, 250, 252, 255))
    d = ImageDraw.Draw(im)
    fb = lambda sz: ImageFont.truetype(INTER_X, sz)
    fr = lambda sz: ImageFont.truetype(INTER_R, sz)
    d.rectangle([0, 0, W, 26], fill=(200, 16, 30, 255))
    if n == 1:
        d.text((W / 2, 380), "WHY I AM DEFINITELY", font=fb(104), fill=(20, 20, 24, 255), anchor="mm")
        d.text((W / 2, 510), "NOT A LEEDS FAN", font=fb(130), fill=(200, 16, 30, 255), anchor="mm")
        d.text((W / 2, 680), "Jason Wilcox, Director of Football", font=fr(56), fill=(60, 60, 64, 255), anchor="mm")
        d.text((W - 60, H - 60), "1 / 214", font=fr(52), fill=(120, 120, 124, 255), anchor="rm")
    elif n == 2:
        d.text((80, 90), "MY COMMITMENT TO", font=fb(72), fill=(20, 20, 24, 255))
        d.text((80, 180), "MANCHESTER UNITED (%)", font=fb(72), fill=(200, 16, 30, 255))
        d.rectangle([620, 420, 980, 960], fill=(200, 16, 30, 255), outline=(20, 20, 24, 255), width=6)
        d.text((800, 360), "+11%", font=fb(96), fill=(30, 140, 60, 255), anchor="mm")
        d.text((800, 1010), "This season", font=fr(48), fill=(60, 60, 64, 255), anchor="mm")
        d.text((W - 60, H - 60), "2 / 214", font=fr(52), fill=(120, 120, 124, 255), anchor="rm")
    else:
        d.text((W / 2, 420), "AND ANOTHER THING", font=fb(120), fill=(20, 20, 24, 255), anchor="mm")
        d.text((W / 2, 600), "(continued from slide 212)", font=fr(60), fill=(90, 90, 94, 255), anchor="mm")
        d.text((W - 60, H - 60), "213 / 214", font=fr(52), fill=(120, 120, 124, 255), anchor="rm")
    return np.asarray(im).copy()


def omar_desk_back(img, s, t, M, sc):
    return img


def omar_desk_front(img, s, t, M, sc):
    """on Omar's desk: a sky-blue mug, and his monitor glowing sky blue with City on it"""
    S = lambda x, y: (M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2])
    x, y = S(1060, 482)
    img = SP.paste(img, SP.mug((108, 171, 221)), x, y, M[0, 0] * 70 / 420)
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    xa, ya = S(560, 380)
    xb, yb = S(760, 482)
    d.rectangle([xa, ya, xb, yb], fill=(30, 30, 34, 255), outline=(10, 10, 12, 255), width=max(1, int(3 * RS)))
    d.rectangle([xa + 6 * RS, ya + 6 * RS, xb - 6 * RS, yb - 14 * RS], fill=(108, 171, 221, 255))
    fz = max(8, int((yb - ya) * 0.2))
    f = ImageFont.truetype(F(10, "bebas").path, fz)
    d.text(((xa + xb) / 2, (ya + yb) / 2 - 6 * RS), "CITY TV", font=f, fill=(255, 255, 255, 255), anchor="mm")
    return over(img, lay)


def soil_floor(img, s, t, M, sc):
    """what is left on the floor: soil, leaves, a bit of pot"""
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(4)
    for _ in range(60):
        x, y = rng.uniform(0.05, 0.95) * OW, rng.uniform(0.9, 1.0) * OH
        r = rng.uniform(8, 24) * RS
        d.ellipse([x - r, y - r * 0.5, x + r, y + r * 0.5], fill=(92, 60, 36, 255), outline=(30, 20, 12, 255))
    return over(img, lay)


# ---------------------------------------------------------------- inserts
def _paper(W, H, base=(242, 236, 222), seed=1):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (H // 4, W // 4)).astype(np.float32)
    n = cv2.resize(cv2.GaussianBlur(n, (0, 0), 2), (W, H))
    arr = np.float32(base)[None, None] + n[..., None] * 5
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")


@functools.lru_cache(maxsize=1)
def _head():
    """Wilcox's front head from his model sheet, for the photos on the board"""
    from studio.paths import CHARACTERS
    sh = Image.open(CHARACTERS / "jason-wilcox" / "reference" / "model-sheet.png").convert("RGB")
    c = np.asarray(sh.crop((322, 540, 458, 722))).copy()
    paper = (c.min(2) > 225)
    a = np.where(paper, 0, 255).astype(np.uint8)
    from scipy import ndimage
    lab, n = ndimage.label(a > 0)
    if n:
        big = 1 + int(np.argmax(ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))))
        a = np.where(lab == big, 255, 0).astype(np.uint8)
        a = ndimage.binary_fill_holes(a > 0).astype(np.uint8) * 255
    return np.dstack([c, a])


KITS = {"BLACKBURN": [(30, 80, 170), (250, 250, 250)], "LEEDS": [(250, 250, 250)], "CITY": [(108, 171, 221)],
        "SOUTHAMPTON": [(210, 20, 30), (250, 250, 250)], "UNITED": [(200, 16, 30)]}
PHOTOS = [  # (club, caption, centre x, y, angle) on the 2400 x 1500 board
    ("UNITED", "DIRECTOR OF FOOTBALL", 1200, 520, -2),
    ("BLACKBURN", "1995: WON THE LEAGUE (AGAINST US)", 420, 420, 4),
    ("LEEDS", "LEEDS 1999-2004 !!!", 1980, 400, -5),
    ("CITY", "MAN CITY ACADEMY", 520, 1080, -3),
    ("SOUTHAMPTON", "SOUTHAMPTON (fine)", 1900, 1060, 3),
]


@functools.lru_cache(maxsize=1)
def _board():
    W, H = 2400, 1500
    rng = np.random.default_rng(5)
    n = rng.normal(0, 1, (H // 3, W // 3)).astype(np.float32)
    n = cv2.resize(cv2.GaussianBlur(n, (0, 0), 1.2), (W, H))
    cork = np.clip(np.float32([182, 136, 86])[None, None] + n[..., None] * 18, 0, 255).astype(np.uint8)
    im = Image.fromarray(cork).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W - 1, H - 1], outline=(90, 60, 30, 255), width=40)
    head = Image.fromarray(_head())
    pins = []
    for club, cap, cx, cy, ang in PHOTOS:
        ph = Image.new("RGBA", (420, 500), (250, 250, 248, 255))
        pd = ImageDraw.Draw(ph)
        cols = KITS[club]
        for i in range(8):                                             # the kit behind him (stripes / halves)
            col = cols[i % len(cols)] if club != "BLACKBURN" else cols[0 if i < 4 else 1]
            pd.rectangle([20 + i * 47.5, 20, 20 + (i + 1) * 47.5, 400], fill=col + (255,))
        hd = head.resize((300, int(300 * head.height / head.width)), Image.LANCZOS)
        ph.alpha_composite(hd, (60, 400 - hd.height + 40))
        pd = ImageDraw.Draw(ph)
        pd.rectangle([20, 400, 400, 480], fill=(250, 250, 248, 255))
        f = ImageFont.truetype(INTER_X, 30 if len(cap) < 22 else 22)
        pd.text((210, 440), cap, font=f, fill=(30, 30, 30, 255), anchor="mm")
        if club == "LEEDS":
            pd.ellipse([8, 8, 412, 412], outline=(220, 20, 20, 255), width=10)
        ph = ph.rotate(ang, expand=True, resample=Image.BICUBIC)
        im.alpha_composite(ph, (int(cx - ph.width / 2), int(cy - ph.height / 2)))
        pins.append((cx, cy - 220))
    # the white mug in its evidence bag, and the map of Yorkshire
    bag = Image.new("RGBA", (420, 520), (230, 236, 240, 150))
    bd = ImageDraw.Draw(bag)
    bd.rectangle([0, 0, 419, 519], outline=(160, 170, 180, 255), width=6)
    bd.rectangle([0, 0, 419, 60], fill=(220, 30, 30, 230))
    bd.text((210, 30), "EVIDENCE", font=ImageFont.truetype(INTER_X, 34), fill=(255, 255, 255, 255), anchor="mm")
    mg = Image.fromarray(SP.mug()).resize((300, 300), Image.LANCZOS)
    bag.alpha_composite(mg, (50, 120))
    bd = ImageDraw.Draw(bag)
    bd.text((210, 470), "EXHIBIT A: WHITE MUG", font=ImageFont.truetype(INTER_X, 26), fill=(30, 30, 30, 255),
            anchor="mm")
    im.alpha_composite(bag, (1000, 940))
    pins.append((1210, 950))
    mp = Image.new("RGBA", (300, 230), (238, 232, 200, 255))
    md = ImageDraw.Draw(mp)
    md.polygon([(40, 60), (150, 30), (260, 70), (240, 190), (120, 210), (50, 160)], fill=(190, 210, 160, 255),
               outline=(80, 80, 60, 255))
    md.text((150, 25), "YORKSHIRE", font=ImageFont.truetype(INTER_X, 24), fill=(60, 60, 40, 255), anchor="mm")
    md.ellipse([140, 90, 210, 150], outline=(220, 20, 20, 255), width=6)
    md.text((175, 170), "LEEDS", font=ImageFont.truetype(INTER_X, 20), fill=(220, 20, 20, 255), anchor="mm")
    mp = mp.rotate(6, expand=True)
    im.alpha_composite(mp, (1560, 640))
    pins.append((1700, 650))
    d = ImageDraw.Draw(im)
    order = [0, 1, 2, 0, 3, 4, 0, 5, 2, 6]
    for a, b in zip(order, order[1:]):                                   # the red string
        d.line([pins[a], pins[b]], fill=(200, 20, 20, 255), width=8)
    for x, y in pins:
        d.ellipse([x - 16, y - 16, x + 16, y + 16], fill=(230, 40, 40, 255), outline=(60, 10, 10, 255), width=4)
    return np.asarray(im.convert("RGB")).copy()


def board(s, t):
    """the conspiracy board: an overview, then the camera snaps to each photo as he names the club. With
    focus="mug", close on the white mug in its evidence bag."""
    M = marks()
    b = _board()
    H, W = b.shape[:2]
    views = {"all": (1200, 750, 1.05), "UNITED": (1200, 560, 2.1), "BLACKBURN": (430, 450, 2.2),
             "LEEDS": (1980, 430, 2.2), "CITY": (520, 1100, 2.2), "mug": (1210, 1200, 2.6)}
    if s.get("focus") == "mug":
        keys = [(s["t"], views["mug"])]
    else:
        keys = [(s["t"], views["all"]), (M.wt("L007", "jason") - 0.05, views["UNITED"]),
                (M.ls("L008") - 0.05, views["BLACKBURN"]), (M.ls("L009") - 0.05, views["LEEDS"]),
                (M.ls("L010") - 0.05, views["CITY"])]
    i = max(j for j, (tk, _) in enumerate(keys) if tk <= t + 1e-6) if t >= keys[0][0] else 0
    cx, cy, z = keys[i][1]
    k = t - keys[i][0]
    blur = 0.0
    if i > 0 and k < 0.14:                                             # the whip from the last one
        u = sm(k / 0.14)
        px, py, pz = keys[i - 1][1]
        cx, cy, z = px + (cx - px) * u, py + (cy - py) * u, pz + (z - pz) * u
        blur = 1 - u
    z *= 1 + 0.03 * k
    s_ = OW / W * z
    A = np.float32([[s_, 0, OW / 2 - s_ * cx], [0, s_, OH / 2 - s_ * cy]])
    img = cv2.warpAffine(b, A, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    img = img.astype(np.float32) / 255.0
    if blur > 0:
        img = cv2.blur(img, (max(1, int(80 * blur * RS)), max(1, int(20 * blur * RS))))
    return img


def spygate(s, t):
    """the 2019 back page spinning in"""
    k = t - s["t"]
    pg = _spy_page()
    u = sm(k / 0.7)
    ang = (1 - u) * 720 - 3
    sc = (0.15 + 0.85 * u) * 1.0 * RS * (1 + 0.03 * k)
    img = np.ones((OH, OW, 3), np.float32) * np.float32([0.12, 0.12, 0.14])
    return SP.paste(img, pg, OW / 2, OH / 2, sc, ang, anchor=(pg.shape[1] / 2, pg.shape[0] / 2))


@functools.lru_cache(maxsize=1)
def _spy_page():
    W, H = 1500, 1000
    im = _paper(W, H, seed=3)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 130], fill=(20, 20, 20, 255))
    d.text((40, 65), "THE BACK PAGE", font=ImageFont.truetype(INTER_X, 64), fill=(255, 255, 255, 255), anchor="lm")
    d.text((W - 40, 65), "JANUARY 2019", font=ImageFont.truetype(INTER_R, 44), fill=(220, 220, 220, 255), anchor="rm")
    d.text((40, 160), "SPYGATE!", font=ImageFont.truetype(INTER_X, 210), fill=(200, 16, 30, 255))
    d.text((44, 400), "LEEDS CAUGHT SPYING ON", font=ImageFont.truetype(INTER_X, 70), fill=(20, 20, 20, 255))
    d.text((44, 480), "A RIVAL'S TRAINING GROUND", font=ImageFont.truetype(INTER_X, 70), fill=(20, 20, 20, 255))
    pic = np.zeros((380, 560, 3), np.float32) + np.float32([0.62, 0.78, 0.95])     # a bush with binoculars
    hh = SP.hedge(seed=2, W=900, H=400)
    SP.paste(pic, hh, 280, 380, 0.62)
    SP.paste(pic, SP.binoculars("side"), 330, 190, 0.3, -8, anchor=(80, 180))
    im.paste(Image.fromarray((pic * 255).astype(np.uint8)), (900, 600))
    d = ImageDraw.Draw(im)
    d.rectangle([900, 600, 1460, 980], outline=(20, 20, 20, 255), width=6)
    for i in range(7):
        y = 600 + i * 52
        d.rectangle([44, y, 860, y + 22], fill=(150, 150, 150, 255))
    return np.asarray(im).copy()


def lock(s, t):
    """his door's thumb-turn lock: click"""
    M = marks()
    img = np.zeros((OH, OW, 3), np.float32)
    wood = _paper(OW, OH, base=(120, 74, 42), seed=8)
    img[:] = np.asarray(wood.convert("RGB")).astype(np.float32) / 255.0
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    k = t - s["t"]
    z = 1 + 0.04 * k
    cx, cy = OW / 2, OH / 2
    d.rounded_rectangle([cx - P(160 * z), cy - P(330 * z), cx + P(160 * z), cy + P(330 * z)], radius=P(40),
                        fill=(196, 198, 204, 255), outline=(40, 40, 44, 255), width=P(8))
    d.ellipse([cx - P(110 * z), cy - P(110 * z) - P(120 * z), cx + P(110 * z), cy + P(110 * z) - P(120 * z)],
              fill=(176, 178, 186, 255), outline=(40, 40, 44, 255), width=P(8))
    img = over(img, lay)
    u = sm((t - M.m("click")) / 0.12)
    ang = 90 * u
    bar = np.zeros((60, 240, 4), np.uint8)
    cv2.rectangle(bar, (0, 0), (239, 59), (40, 40, 44, 255), -1)
    cv2.rectangle(bar, (8, 8), (231, 51), (150, 152, 160, 255), -1)
    SP.paste(img, bar, cx, cy - P(120 * z), 1.1 * z * RS, ang, anchor=(120, 30))
    d2 = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    dd = ImageDraw.Draw(d2)
    dd.ellipse([cx - P(40 * z), cy + P(140 * z), cx + P(40 * z), cy + P(220 * z)], fill=(40, 40, 44, 255))
    if t >= M.m("click"):
        dd.text((cx + P(260), cy - P(260)), "CLICK", font=F(120, "bebas"), fill=(255, 255, 255, int(255 * (1 - sm((t - M.m("click") - 0.3) / 0.3)))),
                anchor="mm")
    return over(img, d2)


def clock(s, t):
    """the wall clock: 2:59... 3:00"""
    M = marks()
    img = np.ones((OH, OW, 3), np.float32) * np.float32([0.86, 0.8, 0.68])
    k = t - s["t"]
    z = 1.0 + 0.25 * sm(k / 2.0)
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx, cy, r = OW / 2, OH / 2, P(420 * z)
    d.ellipse([cx - r - P(30), cy - r - P(30), cx + r + P(30), cy + r + P(30)], fill=(40, 40, 44, 255))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(250, 250, 246, 255))
    for i in range(12):
        a = math.radians(i * 30)
        d.text((cx + math.sin(a) * r * 0.8, cy - math.cos(a) * r * 0.8), str(12 if i == 0 else i),
               font=F(80 * z, "bebas"), fill=(30, 30, 30, 255), anchor="mm")
    tick = M.wt("L023", "three") - 0.05
    minute = 59 if t < tick else 60
    mins = minute + (0.0 if t < tick else 0)
    am = math.radians(mins * 6 - (4 * math.exp(-max(0, t - tick) * 20) if t >= tick else 0))
    ah = math.radians((2 + mins / 60) * 30)
    d.line([(cx, cy), (cx + math.sin(ah) * r * 0.5, cy - math.cos(ah) * r * 0.5)], fill=(20, 20, 20, 255), width=P(22))
    d.line([(cx, cy), (cx + math.sin(am) * r * 0.78, cy - math.cos(am) * r * 0.78)], fill=(20, 20, 20, 255), width=P(14))
    sa = math.radians(((t * 6) % 60) * 6)
    d.line([(cx, cy), (cx + math.sin(sa) * r * 0.85, cy - math.cos(sa) * r * 0.85)], fill=(200, 16, 30, 255), width=P(5))
    d.ellipse([cx - P(20), cy - P(20), cx + P(20), cy + P(20)], fill=(200, 16, 30, 255))
    return over(img, lay)


def laptop(s, t):
    """his laptop: the BBC Sport live page on Leeds, refreshed and refreshed; the goal; the penalty"""
    M = marks()
    mode = s.get("mode", "live")
    k = t - s["t"]
    img = np.ones((OH, OW, 3), np.float32) * np.float32([0.08, 0.08, 0.09])
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    z = 1 + 0.02 * k
    x0, y0, x1, y1 = P(960 - 880 * z), P(540 - 480 * z), P(960 + 880 * z), P(540 + 480 * z)
    d.rectangle([x0, y0, x1, y1], fill=(250, 250, 250, 255))
    d.rectangle([x0, y0, x1, y0 + P(120)], fill=(16, 16, 16, 255))
    for i, ch in enumerate("BBC"):
        bx = x0 + P(40) + i * P(70)
        d.rectangle([bx, y0 + P(30), bx + P(60), y0 + P(90)], fill=(250, 250, 250, 255))
        d.text((bx + P(30), y0 + P(60)), ch, font=F(46, "x"), fill=(16, 16, 16, 255), anchor="mm")
    d.text((x0 + P(270), y0 + P(60)), "SPORT", font=F(56, "x"), fill=(255, 210, 0, 255), anchor="lm")
    d.text((x0 + P(60), y0 + P(190)), "LIVE: LEEDS UNITED", font=F(84, "x"), fill=(16, 16, 16, 255), anchor="lm")
    d.rectangle([x0 + P(60), y0 + P(250), x0 + P(200), y0 + P(300)], fill=(200, 16, 30, 255))
    d.text((x0 + P(130), y0 + P(275)), "LIVE", font=F(34, "x"), fill=(255, 255, 255, 255), anchor="mm")
    entries = [("14:58", "Leeds pressing high. Big crowd in."), ("14:56", "Corner to Leeds. Cleared."),
               ("14:51", "Leeds 0-0. Lively start.")]
    if mode == "goal" or (mode == "live" and False):
        entries = [("15:01", "GOAL! LEEDS 1-0!")] + entries
    if mode == "penalty":
        entries = [("15:09", "PENALTY to the opposition."), ("15:01", "GOAL! LEEDS 1-0!")] + entries
    for i, (tm, txt) in enumerate(entries):
        y = y0 + P(370) + i * P(150)
        big = txt.startswith("GOAL") or txt.startswith("PENALTY")
        pop = 1.0
        if i == 0 and big:
            pop = 1 + 0.4 * math.exp(-k / 0.1)
            d.rectangle([x0 + P(40), y - P(60), x1 - P(40), y + P(70)], fill=(255, 236, 140, 255) if txt.startswith("GOAL")
                        else (255, 210, 210, 255))
        d.text((x0 + P(70), y), tm, font=F(44, "x"), fill=(200, 16, 30, 255), anchor="lm")
        d.text((x0 + P(260), y), txt, font=F(int((70 if big else 46) * pop), "x" if big else "b"),
               fill=(16, 16, 16, 255), anchor="lm")
    img = over(img, lay)
    if mode == "live":                                    # refresh, refresh: the page blinks and a spinner turns
        for r0 in (0.35, 0.95):
            if r0 <= k < r0 + 0.3:
                img = img * 0.55 + 0.45
                lay2 = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
                d2 = ImageDraw.Draw(lay2)
                a0 = (k - r0) * 900
                d2.arc([P(900), P(480), P(1020), P(600)], a0, a0 + 270, fill=(30, 30, 30, 255), width=P(12))
                img = over(img, lay2)
        # the cursor on refresh
        cur = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
        dc = ImageDraw.Draw(cur)
        cx_, cy_ = P(180), P(120)
        dc.polygon([(cx_, cy_), (cx_, cy_ + P(60)), (cx_ + P(16), cy_ + P(46)), (cx_ + P(40), cy_ + P(44))],
                   fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
        img = over(img, cur)
    return img


def pot_rip(s, t):
    """what's left of the plant: the pot on its side in the soil, one leaf drooping. R.I.P."""
    k = t - s["t"]
    img = np.ones((OH, OW, 3), np.float32) * np.float32([0.64, 0.6, 0.56])
    l = img.mean(2, keepdims=True)
    p = SP.plant(False)
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(12)
    for _ in range(140):                                                  # the soil, spilt across the carpet
        x, y = rng.normal(820, 300) * RS, rng.normal(800, 55) * RS
        r = rng.uniform(14, 42) * RS
        d.ellipse([x - r, y - r * 0.5, x + r, y + r * 0.5], fill=(92, 60, 36, 255), outline=(30, 20, 12, 255))
    img = over(img, lay)
    SP.paste(img, p["fr"], P(640), P(760), 0.55 * RS, -100 + 4 * math.sin(k * 1.5), anchor=p["pivot"])
    SP.paste(img, p["fl"], P(700), P(800), 0.5 * RS, -70, anchor=p["pivot"])
    SP.paste(img, p["pot"], P(780), P(770), 0.95 * RS, -84, anchor=p["pivot"])        # the pot, on its side
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = sm((k - 0.6) / 0.4)
    d.text((P(1450), P(300)), "R.I.P.", font=F(150, "bebas"), fill=(255, 255, 255, int(230 * a)), anchor="mm")
    d.text((P(1450), P(410)), "PLANT, 2023-2026", font=F(60, "bebas"), fill=(255, 255, 255, int(230 * a)), anchor="mm")
    img = over(img, lay)
    l = img.mean(2, keepdims=True)
    return l + (img - l) * 0.4


def tablet(s, t):
    """his tablet at night: Liverpool score, Mac Allister"""
    k = t - s["t"]
    img = np.ones((OH, OW, 3), np.float32) * np.float32([0.03, 0.04, 0.07])
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    z = 1 + 0.03 * k
    x0, y0, x1, y1 = P(960 - 760 * z), P(540 - 470 * z), P(960 + 760 * z), P(540 + 470 * z)
    d.rounded_rectangle([x0 - P(30), y0 - P(30), x1 + P(30), y1 + P(30)], radius=P(60), fill=(20, 20, 22, 255))
    d.rectangle([x0, y0, x1, y1], fill=(28, 120, 56, 255))
    for i in range(8):
        if i % 2:
            d.rectangle([x0 + i * (x1 - x0) / 8, y0, x0 + (i + 1) * (x1 - x0) / 8, y1], fill=(34, 132, 62, 255))
    d.rectangle([x0, y0, x1, y0 + P(140)], fill=(200, 16, 30, 255))
    d.text(((x0 + x1) / 2, y0 + P(70)), "GOAL!  LIVERPOOL 1-0", font=F(80, "x"), fill=(255, 255, 255, 255), anchor="mm")
    pop = 1 + 0.3 * math.exp(-k / 0.15)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2 + P(20)), "MAC ALLISTER", font=F(int(170 * pop), "bebas"),
           fill=(255, 255, 255, 255), anchor="mm", stroke_width=P(6), stroke_fill=(20, 20, 20, 255))
    d.text(((x0 + x1) / 2, (y0 + y1) / 2 + P(170)), "34'", font=F(80, "bebas"), fill=(255, 236, 140, 255), anchor="mm")
    img = over(img, lay)
    glow = np.exp(-((np.linspace(-1, 1, OW)[None, :] ** 2) / 0.6 + (np.linspace(-1, 1, OH)[:, None] ** 2) / 0.6))
    return img * (0.85 + 0.25 * glow[..., None].astype(np.float32))


def end_card(s, t):
    from studio.film import graphics as G
    from film.direction import TITLE
    tag = (("NEXT TIME: SIR JIM, AND HIS OTHER FOOTBALL CLUB", "BEBAS", 50, None, 5, 760, (225, 225, 225)),)
    return G.title_card(t, s["t"], TITLE, tag)


# ---------------------------------------------------------------- plates
def plate_image(k):
    return None

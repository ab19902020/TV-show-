"""Things The Undercard draws in code, in the pack's look (flat colour, dark ink outline): the BANNED board with
Dana's face crossed out, contact shadows, the near ring ropes that pass in front of the fighters, the stray towel,
a ring-card. Each is called by actors.scene as fn(layer, shot, item, t, M, scale) in 1x plate px."""
import functools
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw

from studio.film import engine as E
from studio.film.graphics import BEBAS, font
from studio.paths import CHARACTERS

from film.actors import at_time, place_rgba, ppc, prop_rgba

INK = (22, 18, 20)


def contact_shadow(lay, s, it, t, M, sc, F, Hs, lift):
    """a soft shadow on the floor under a person (it shrinks and fades as they leave the floor)"""
    if s.get("shadows") is False:
        return
    w = 0.30 * Hs * (1 - min(0.6, lift / 300.0))
    h = 0.045 * Hs
    a = 0.42 * (1 - min(0.8, lift / 200.0))
    x0, y0 = int(F[0] - w), int(F[1] - h * 2)
    x1, y1 = int(F[0] + w), int(F[1] + h * 2)
    x0c, y0c, x1c, y1c = max(0, x0), max(0, y0), min(lay.shape[1], x1), min(lay.shape[0], y1)
    if x1c <= x0c or y1c <= y0c:
        return
    yy, xx = np.mgrid[y0c:y1c, x0c:x1c].astype(np.float32)
    r = ((xx - F[0]) / w) ** 2 + ((yy - F[1]) / h) ** 2
    m = (np.clip(1 - r, 0, 1) ** 1.5 * a)[..., None]
    reg = lay[y0c:y1c, x0c:x1c]
    sh = np.concatenate([np.zeros_like(m.repeat(3, 2)), m], 2)
    lay[y0c:y1c, x0c:x1c] = sh + reg * (1 - m)


@functools.lru_cache(maxsize=1)
def board_image():
    """the press-area board: a white foam board on a black easel, Dana's angry face, a red cross, BANNED"""
    W, H = 900, 1500
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    lw = 14
    # easel legs and the ledge
    for x0, x1 in ((250, 120), (650, 780)):
        dr.line((x0, 700, x1, H - 10), fill=INK + (255,), width=34)
    dr.line((450, 700, 450, H - 60), fill=INK + (255,), width=26)
    dr.rectangle((70, 1040, 830, 1080), fill=(40, 34, 36, 255), outline=INK + (255,), width=lw)
    # the board
    dr.rounded_rectangle((60, 20, 840, 1050), 18, fill=(246, 244, 238, 255), outline=INK + (255,), width=lw)
    dr.rectangle((60, 20, 840, 150), fill=(18, 30, 72, 255), outline=INK + (255,), width=lw)
    f = font(BEBAS, 120)
    tw = dr.textlength("BANNED", font=f)
    dr.text(((W - tw) / 2, 25), "BANNED", font=f, fill=(255, 255, 255, 255))
    # Dana's face (the angry head from the expressions sheet)
    ex = Image.open(CHARACTERS / "eddie-hearn" / "reference" / "expressions.png").convert("RGBA")
    head = ex.crop((385, 581, 557, 797))
    head = head.resize((int(head.width * 3.6), int(head.height * 3.6)), Image.LANCZOS)
    im.alpha_composite(head, ((W - head.width) // 2, 200))
    # the red cross, hand-painted
    for (a, b) in (((150, 220), (750, 980)), ((750, 220), (150, 980))):
        dr.line((a, b), fill=(205, 22, 26, 235), width=58)
    fs = font(BEBAS, 64)
    t2 = "NO TICKET · NO GUEST LIST"
    dr.text(((W - dr.textlength(t2, font=fs)) / 2, 965), t2, font=fs, fill=(30, 30, 30, 255))
    a = np.asarray(im).astype(np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a


def board(lay, s, it, t, M, sc):
    im = board_image()
    x, y = it["at"]
    h = it["h"] * sc
    k = h / im.shape[0]
    Fx, Fy = M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]
    A = np.float32([[k, 0, Fx - k * im.shape[1] / 2], [0, k, Fy - h]])
    place_rgba(lay, im, A)


def near_ropes(lay, s, it, t, M, sc):
    """the ring's near ropes, between the lens and the fighters: thick, a little soft, red / white / blue, each with
    a dark outline and a highlight along its top"""
    cols = [(0.78, 0.08, 0.08), (0.92, 0.92, 0.94), (0.10, 0.25, 0.80)]
    H, Wd = lay.shape[:2]
    rgb = np.zeros((H, Wd, 3), np.float32)
    al = np.zeros((H, Wd), np.float32)
    for k, y in enumerate(it["ys"]):
        Y = int(M[1, 1] * y + M[1, 2])
        th = max(3, int(it.get("w", 16) * sc))
        if Y - th > H:
            continue
        ink = np.zeros((H, Wd), np.float32)
        cv2.line(ink, (-50, Y), (Wd + 50, Y), 1.0, th + max(2, th // 4), cv2.LINE_AA)
        body = np.zeros((H, Wd), np.float32)
        cv2.line(body, (-50, Y), (Wd + 50, Y), 1.0, th, cv2.LINE_AA)
        hi = np.zeros((H, Wd), np.float32)
        cv2.line(hi, (-50, Y - th // 4), (Wd + 50, Y - th // 4), 1.0, max(1, th // 5), cv2.LINE_AA)
        c = np.float32(cols[k % 3])
        layer = np.float32(INK)[None, None] / 255.0 * ink[..., None]
        layer = layer * (1 - body[..., None]) + c * body[..., None]
        layer = layer * (1 - 0.5 * hi[..., None]) + 0.5 * hi[..., None]
        rgb = rgb * (1 - ink[..., None]) + layer * ink[..., None]
        al = np.maximum(al, ink)
    b = it.get("blur", 3.0) * sc
    if b > 0:
        rgb = cv2.GaussianBlur(rgb * al[..., None], (0, 0), b)
        al = cv2.GaussianBlur(al, (0, 0), b)
    else:
        rgb = rgb * al[..., None]
    lay[:] = np.dstack([rgb, al]) + lay * (1 - al[..., None])


def bottle(lay, s, it, t, M, sc):
    """a clear water bottle in Joshua's hand"""
    x, y = it["at"]
    h = it["h"] * sc
    X, Y = M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]
    w = h * 0.34
    im = np.zeros((int(h) + 8, int(w) + 8, 4), np.float32)
    c = (int(w / 2) + 4, 0)
    body = np.zeros(im.shape[:2], np.uint8)
    cv2.rectangle(body, (4, int(h * 0.22)), (int(w) + 4, int(h)), 255, -1)
    cv2.rectangle(body, (int(w * 0.3) + 4, 2), (int(w * 0.7) + 4, int(h * 0.24)), 255, -1)
    m = body.astype(np.float32) / 255
    im[..., 0], im[..., 1], im[..., 2] = 0.55 * m, 0.75 * m, 0.92 * m
    im[..., 3] = 0.75 * m
    cv2.rectangle(im, (int(w * 0.3) + 4, 2), (int(w * 0.7) + 4, int(h * 0.1)), (0.1, 0.35, 0.85, 1.0), -1)
    cv2.rectangle(im, (4, int(h * 0.45)), (int(w) + 4, int(h * 0.65)), (0.85, 0.85, 0.9, 1.0), -1)
    edge = cv2.morphologyEx(body, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    im[edge] = (0.07, 0.06, 0.06, 1.0)
    im[..., :3] *= im[..., 3:4]
    E.warp_into(lay, im, np.float32([[1, 0, X - w / 2], [0, 1, Y - h]]))


def lid(lay, s, it, t, M, sc):
    """the trolley's lid seen from the side: a steel slab on the rim, hinged at the back (the attendant's end), its
    handle at the front; rot opens it (degrees, the front end up)"""
    x, y = at_time(it["at"], t, it.get("ease", False))         # keyed like the trolley it sits on
    w, th = it["w"], it["w"] * 0.10
    ang = math.radians(-at_time(it.get("rot", 0.0), t))
    hx, hy = x - w / 2, y                                   # the hinge
    pts = np.float32([[0, -th], [w, -th], [w, 0], [0, 0]])
    c, sn = math.cos(ang), math.sin(ang)
    R = np.float32([[c, -sn], [sn, c]])
    P = pts @ R.T + np.float32([hx, hy])
    S = np.stack([M[0, 0] * P[:, 0] + M[0, 2], M[1, 1] * P[:, 1] + M[1, 2]], 1)
    hp_ = (np.float32([[w * 0.82, -th], [w * 0.82, -th * 2.6], [w * 0.96, -th * 2.6], [w * 0.96, -th]]) @ R.T
           + np.float32([hx, hy]))
    Hs = np.stack([M[0, 0] * hp_[:, 0] + M[0, 2], M[1, 1] * hp_[:, 1] + M[1, 2]], 1)
    x0, y0 = np.floor(np.minimum(S.min(0), Hs.min(0))) - 6
    x1, y1 = np.ceil(np.maximum(S.max(0), Hs.max(0))) + 6
    x0, y0 = int(max(0, x0)), int(max(0, y0))
    x1, y1 = int(min(lay.shape[1], x1)), int(min(lay.shape[0], y1))
    if x1 <= x0 or y1 <= y0:
        return
    K = 4
    hh, ww = (y1 - y0) * K, (x1 - x0) * K
    img = np.zeros((hh, ww, 3), np.float32)
    al = np.zeros((hh, ww), np.float32)
    lw = max(2, int(2.2 * sc * K))
    for poly, col in ((Hs, (0.50, 0.52, 0.55)), (S, (0.66, 0.68, 0.71))):
        q = np.int32(np.round((poly - [x0, y0]) * K))
        m = np.zeros((hh, ww), np.uint8)
        cv2.fillPoly(m, [q], 255)
        mm = m.astype(np.float32)[..., None] / 255
        img = img * (1 - mm) + np.float32(col) * mm
        al = np.maximum(al, mm[..., 0])
        e = np.zeros((hh, ww), np.uint8)
        cv2.polylines(e, [q], True, 255, lw, cv2.LINE_AA)
        em = e.astype(np.float32)[..., None] / 255
        img = img * (1 - em) + np.float32(INK) / 255 * em
        al = np.maximum(al, em[..., 0])
    img = cv2.resize(img * al[..., None], (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    al = cv2.resize(al, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    reg = lay[y0:y1, x0:x1]
    lay[y0:y1, x0:x1] = np.dstack([img, al]) + reg * (1 - al[..., None])


# ---------------------------------------------------------------- fight effects (house look: flat colour, ink outline)
def _canvas(lay, X, Y, R):
    x0, y0 = int(max(0, X - R - 4)), int(max(0, Y - R - 4))
    x1, y1 = int(min(lay.shape[1], X + R + 5)), int(min(lay.shape[0], Y + R + 5))
    return x0, y0, x1, y1


def _over(lay, x0, y0, rgb, al):
    h, w = al.shape
    reg = lay[y0:y0 + h, x0:x0 + w]
    lay[y0:y0 + h, x0:x0 + w] = np.dstack([rgb * al[..., None], al]) + reg * (1 - al[..., None])


def impact(lay, s, it, t, M, sc):
    """an impact burst: a spiky star, white in the middle, yellow round it, inked; it pops out in 2 frames and is
    gone in 6"""
    u = (t - it["t0"]) * 30.0
    if u < 0 or u > 7:
        return
    grow = min(1.0, 0.45 + 0.3 * u)
    fade = 1.0 if u < 3 else max(0.0, 1 - (u - 3) / 4)
    X, Y = M[0, 0] * it["at"][0] + M[0, 2], M[1, 1] * it["at"][1] + M[1, 2]
    R = it["size"] * sc * grow
    x0, y0, x1, y1 = _canvas(lay, X, Y, R)
    if x1 <= x0 or y1 <= y0:
        return
    K = 4
    h, w = (y1 - y0) * K, (x1 - x0) * K
    rng = np.random.default_rng(int(it["t0"] * 1000) % 99991)
    n = 11
    ang = np.linspace(0, 2 * np.pi, 2 * n, endpoint=False) + rng.uniform(0, 0.3)
    rad = np.where(np.arange(2 * n) % 2 == 0, 1.0, 0.45) * rng.uniform(0.8, 1.05, 2 * n)
    cx, cy = (X - x0) * K, (Y - y0) * K

    def poly(scale):
        return np.int32(np.stack([cx + np.cos(ang) * rad * R * K * scale, cy + np.sin(ang) * rad * R * K * scale], 1))
    rgb = np.zeros((h, w, 3), np.float32)
    al = np.zeros((h, w), np.float32)
    for scale, col in ((1.0, None), (0.92, (1.0, 0.86, 0.15)), (0.55, (1.0, 1.0, 0.96))):
        m = np.zeros((h, w), np.uint8)
        cv2.fillPoly(m, [poly(scale)], 255, cv2.LINE_AA)
        mm = m.astype(np.float32) / 255
        c = np.float32(INK) / 255 if col is None else np.float32(col)
        rgb = rgb * (1 - mm[..., None]) + c * mm[..., None]
        al = np.maximum(al, mm)
    rgb = cv2.resize(rgb, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    al = cv2.resize(al, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA) * fade
    _over(lay, x0, y0, rgb, al)


def sweat(lay, s, it, t, M, sc):
    """drops of sweat flung off on a hit: each on its own arc, gone in half a second"""
    u = t - it["t0"]
    if u < 0 or u > 0.55:
        return
    rng = np.random.default_rng(int(it["t0"] * 977) % 99991)
    for i in range(it["n"]):
        vx = it["dir"] * rng.uniform(0.6, 1.4) * it["size"] * 3.2
        vy = -rng.uniform(0.6, 1.5) * it["size"] * 3.0
        x = it["at"][0] + vx * u + rng.uniform(-0.2, 0.2) * it["size"]
        y = it["at"][1] + vy * u + 0.5 * 2600 * u * u * it["size"] / 110
        X, Y = M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]
        r = rng.uniform(0.05, 0.09) * it["size"] * sc
        x0, y0, x1, y1 = _canvas(lay, X, Y, 2 * r)
        if x1 <= x0 or y1 <= y0:
            continue
        K = 4
        h, w = (y1 - y0) * K, (x1 - x0) * K
        m = np.zeros((h, w), np.uint8)
        ink = np.zeros((h, w), np.uint8)
        c = (int((X - x0) * K), int((Y - y0) * K))
        ang = np.degrees(np.arctan2(vy + 2600 * u * it["size"] / 110, vx)) + 180
        pts = cv2.ellipse2Poly(c, (int(r * K * 1.5), int(r * K)), int(ang), 0, 360, 10)
        cv2.fillPoly(ink, [pts], 255, cv2.LINE_AA)
        pts2 = cv2.ellipse2Poly(c, (int(r * K * 1.2), int(r * K * 0.72)), int(ang), 0, 360, 10)
        cv2.fillPoly(m, [pts2], 255, cv2.LINE_AA)
        mi, mm = ink.astype(np.float32) / 255, m.astype(np.float32) / 255
        rgb = np.float32(INK)[None, None] / 255 * (1 - mm[..., None]) + np.float32([0.72, 0.88, 1.0]) * mm[..., None]
        rgb = cv2.resize(rgb, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
        al = cv2.resize(mi, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA) * (1 - max(0, u - 0.35) / 0.2)
        _over(lay, x0, y0, rgb, np.clip(al, 0, 1))


def speed(lay, s, it, t, M, sc):
    """speed lines trailing a fast move: a few white streaks, there for a few frames"""
    u = (t - it["t0"]) / max(1e-3, it["dur"])
    if u < 0 or u > 1:
        return
    rng = np.random.default_rng(int(it["t0"] * 733) % 99991)
    a = (1 - u) * 0.8
    for i in range(it.get("n", 5)):
        oy = rng.uniform(-0.5, 0.5) * it["spread"]
        L = it["len"] * rng.uniform(0.6, 1.0)
        xa = it["at"][0] - it["dir"] * L * (0.3 + 0.7 * u)
        xb = it["at"][0] - it["dir"] * L * (1.0 + 0.4 * u)
        Xa, Ya = M[0, 0] * xa + M[0, 2], M[1, 1] * (it["at"][1] + oy) + M[1, 2]
        Xb = M[0, 0] * xb + M[0, 2]
        x0, x1 = int(max(0, min(Xa, Xb) - 4)), int(min(lay.shape[1], max(Xa, Xb) + 4))
        y0, y1 = int(max(0, Ya - 6)), int(min(lay.shape[0], Ya + 6))
        if x1 <= x0 or y1 <= y0:
            continue
        m = np.zeros((y1 - y0, x1 - x0), np.float32)
        cv2.line(m, (int(Xa - x0), int(Ya - y0)), (int(Xb - x0), int(Ya - y0)), 1.0, max(1, int(3 * sc)), cv2.LINE_AA)
        _over(lay, x0, y0, np.ones(m.shape + (3,), np.float32), m * a)


def flashes(img, s, t, M, sc, region, rate=6.0, seed=1):
    """press camera flashes popping in the crowd: (x0, y0, x1, y1) plate px, `rate` a second, 2 frames each"""
    f = int(t * 30)
    out = img
    for k in (f, f - 1):
        rng = np.random.default_rng(k * 7919 + seed)
        n = rng.poisson(rate / 30.0 * 2)
        for _ in range(n):
            x = rng.uniform(region[0], region[2])
            y = rng.uniform(region[1], region[3])
            X, Y = M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]
            r = rng.uniform(6, 14) * sc * (1.0 if k == f else 0.6)
            x0, y0 = int(max(0, X - 3 * r)), int(max(0, Y - 3 * r))
            x1, y1 = int(min(out.shape[1], X + 3 * r)), int(min(out.shape[0], Y + 3 * r))
            if x1 <= x0 or y1 <= y0:
                continue
            yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            g = np.exp(-(((xx - X) ** 2 + (yy - Y) ** 2) / (r * r)))[..., None]
            out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - 0.85 * g) + 0.98 * g
    return out


def puff(lay, s, it, t, M, sc):
    """a cartoon puff of smoke (a quick change behind it): a cluster of round clouds that bursts out over a few
    frames and thins away, with a ring of little ones flying off"""
    u = (t - it["t0"]) / max(1e-3, it["dur"])
    if u < 0 or u > 1:
        return
    x, y = it["at"]
    X, Y = M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]
    R = it["size"] * sc / 2
    grow = 1 - (1 - min(1.0, u / 0.3)) ** 2
    fade = 1.0                                                          # solid smoke, never see-through:
    if u > 0.55:                                                        # it breaks up and shrinks away instead
        grow *= max(0.0, 1 - (u - 0.55) / 0.45) ** 0.7
    rng = np.random.default_rng(int(it["t0"] * 977) % 9973)
    blobs = [(0.0, 0.0, 0.62)] + [(np.cos(a) * 0.48, np.sin(a) * 0.62, rng.uniform(0.34, 0.46))
                                   for a in np.linspace(0, 2 * np.pi, 9, endpoint=False) + rng.uniform(0, 0.6)]
    blobs += [(np.cos(a) * (0.9 + 0.6 * u), np.sin(a) * (1.0 + 0.6 * u), 0.14 * (1 - u))
              for a in np.linspace(0.3, 2 * np.pi + 0.3, 7, endpoint=False)]
    pad = int(R * 2.2) + 8
    x0, y0 = int(X - pad), int(Y - pad)
    x1, y1 = int(X + pad), int(Y + pad)
    cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(lay.shape[1], x1), min(lay.shape[0], y1)
    if cx1 <= cx0 or cy1 <= cy0:
        return
    K = 2
    hh, ww = (y1 - y0) * K, (x1 - x0) * K
    fill = np.zeros((hh, ww), np.uint8)
    for bx, by, br in blobs:
        cv2.circle(fill, (int((X - x0 + bx * R * grow) * K), int((Y - y0 + by * R * grow) * K)),
                   max(1, int(br * R * grow * K)), 255, -1, cv2.LINE_AA)
    m = fill.astype(np.float32) / 255
    ink = cv2.morphologyEx(fill, cv2.MORPH_GRADIENT, np.ones((max(3, int(3 * sc * K)),) * 2, np.uint8)).astype(np.float32) / 255
    shade = cv2.GaussianBlur(m, (0, 0), R * K * 0.25)
    tint = np.float32([0.92, 0.86, 0.78]) if it.get("dust") else np.float32([0.97, 0.97, 1.0])
    rgb = np.ones((hh, ww, 3), np.float32) * (0.80 + 0.17 * shade)[..., None] * tint
    rgb = rgb * (1 - ink[..., None]) + np.float32(INK) / 255 * ink[..., None]
    al = np.maximum(m, ink) * fade
    rgb = cv2.resize(rgb * al[..., None], (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    al = cv2.resize(al, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    rgb, al = rgb[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0], al[cy0 - y0:cy1 - y0, cx0 - x0:cx1 - x0]
    reg = lay[cy0:cy1, cx0:cx1]
    reg[..., :3] = reg[..., :3] * (1 - al[..., None]) + rgb
    reg[..., 3] = reg[..., 3] * (1 - al) + al


def _star5(r):
    a = np.linspace(-np.pi / 2, 1.5 * np.pi, 11)[:-1]
    rad = np.where(np.arange(10) % 2 == 0, r, 0.45 * r)
    return np.stack([np.cos(a) * rad, np.sin(a) * rad], 1)


def stars(lay, s, it, t, M, sc):
    """cartoon stars circling a knocked-out head: four yellow stars on a tilted ring above it, the near ones bigger,
    one turn every 0.9 s; follows the head (s["_heads"], filled as the people are drawn)"""
    if not (it["t0"] <= t < it["t1"]):
        return
    hd = s.get("_heads", {}).get(it["follow"])
    if hd is None:
        return
    X, Y, R, (ax, ay) = hd
    rx, ry = 0.85 * R, 0.26 * R
    d = 1.05 * R + rx * abs(ax)                                 # just past the top of the head, along the body,
    cx, cy = X + d * ax, Y + d * ay - 0.45 * R                  # floating a little above it
    fade = min(1.0, (t - it["t0"]) / 0.15)
    ph = 2 * np.pi * (t - it["t0"]) / 0.9
    for k in range(5):
        a = ph + k * 2 * np.pi / 5
        depth = 0.5 + 0.5 * np.sin(a)                               # 1 = in front
        x, y = cx + rx * np.cos(a), cy + ry * np.sin(a)
        r = R * (0.22 + 0.12 * depth)
        P = _star5(r)
        rot = np.array([[np.cos(a * 0.7), -np.sin(a * 0.7)], [np.sin(a * 0.7), np.cos(a * 0.7)]])
        P = P @ rot.T + [x, y]
        x0, y0 = int(max(0, P[:, 0].min() - 4)), int(max(0, P[:, 1].min() - 4))
        x1, y1 = int(min(lay.shape[1], P[:, 0].max() + 5)), int(min(lay.shape[0], P[:, 1].max() + 5))
        if x1 <= x0 or y1 <= y0:
            continue
        K = 4
        m = np.zeros(((y1 - y0) * K, (x1 - x0) * K), np.uint8)
        q = np.int32(np.round((P - [x0, y0]) * K * 8))
        cv2.fillPoly(m, [q], 255, cv2.LINE_AA, 3)
        e = np.zeros_like(m)
        cv2.polylines(e, [q], True, 255, max(2, int(0.09 * r * K)), cv2.LINE_AA, 3)
        m = cv2.resize(m.astype(np.float32) / 255, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
        e = cv2.resize(e.astype(np.float32) / 255, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
        col = np.ones((y1 - y0, x1 - x0, 3), np.float32) * np.float32([1.0, 0.86, 0.15]) * (0.75 + 0.25 * depth)
        col = col * (1 - e[..., None]) + np.float32(INK) / 255 * e[..., None]
        al = np.maximum(m, e) * fade
        _over(lay, x0, y0, col, al)

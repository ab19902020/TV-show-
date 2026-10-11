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
    x, y = at_time(it["at"], t)
    w, th = it["w"], it["w"] * 0.07
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

"""The props this film draws itself, in the house style (a bold dark outline, flat colour with one shade and one
highlight), as RGBA images at any size: the tiny trophy, the broom, United scarves (three patterns) and the
clipboard. Each is drawn at 4x and reduced, so the outline stays clean at every size. The football and the
handheld microphone are the library's own (library/props/lunch/football, music/microphone).

    img, grip = trophy(height_px)      grip: (x, y) in the image where a hand holds it
"""
import functools

import cv2
import numpy as np
from PIL import Image

from studio.paths import PROPS

INK = (22, 18, 20)
SS = 4                                                   # supersampling


def _canvas(w, h):
    return np.zeros((int(h * SS), int(w * SS), 4), np.uint8)


def _poly(img, pts, col, ink_w):
    p = np.int32(np.round(np.float32(pts) * SS))
    cv2.fillPoly(img, [p], (*col, 255), cv2.LINE_AA)
    if ink_w:
        cv2.polylines(img, [p], True, (*INK, 255), max(1, int(ink_w * SS)), cv2.LINE_AA)


def _down(img):
    h, w = img.shape[:2]
    out = cv2.resize(img, (w // SS, h // SS), interpolation=cv2.INTER_AREA)
    return out


def _ellipse(img, c, ax, col, ink_w, ang=0.0, a0=0, a1=360):
    cv2.ellipse(img, (int(c[0] * SS), int(c[1] * SS)), (int(ax[0] * SS), int(ax[1] * SS)), ang, a0, a1,
                (*col, 255), -1, cv2.LINE_AA)
    if ink_w:
        cv2.ellipse(img, (int(c[0] * SS), int(c[1] * SS)), (int(ax[0] * SS), int(ax[1] * SS)), ang, a0, a1,
                    (*INK, 255), max(1, int(ink_w * SS)), cv2.LINE_AA)


@functools.lru_cache(maxsize=16)
def trophy(h):
    """a tiny gold cup on a stem and a black plinth -> (RGBA, grip at the stem)"""
    w = h * 0.78
    img = _canvas(w, h)
    ink = max(1.2, h * 0.035)
    G, G2, GH = (232, 176, 40), (196, 132, 24), (255, 232, 140)
    cx = w / 2
    # handles
    for s in (-1, 1):
        _ellipse(img, (cx + s * w * 0.33, h * 0.26), (w * 0.14, h * 0.11), G2, ink)
        _ellipse(img, (cx + s * w * 0.33, h * 0.26), (w * 0.07, h * 0.055), (0, 0, 0), 0)
    img[..., 3] = np.where((img[..., :3] == 0).all(-1), 0, img[..., 3])
    # cup
    cup = [(cx - w * 0.30, h * 0.08)] + [(cx + w * 0.30 * np.cos(a), h * 0.08 + h * 0.36 * np.sin(a))
                                          for a in np.linspace(np.pi, 0, 24)][::-1] + [(cx + w * 0.30, h * 0.08)]
    cup = [(cx - w * 0.30, h * 0.08), (cx + w * 0.30, h * 0.08)] + \
          [(cx + w * 0.30 * np.cos(a), h * 0.10 + h * 0.34 * np.sin(a)) for a in np.linspace(0, np.pi, 24)]
    _poly(img, cup, G, ink)
    _poly(img, [(cx - w * 0.16, h * 0.14), (cx - w * 0.06, h * 0.14), (cx - w * 0.09, h * 0.36),
                (cx - w * 0.15, h * 0.32)], GH, 0)
    _ellipse(img, (cx, h * 0.08), (w * 0.30, h * 0.035), G2, ink)
    # stem and knot
    _poly(img, [(cx - w * 0.05, h * 0.43), (cx + w * 0.05, h * 0.43), (cx + w * 0.07, h * 0.66),
                (cx - w * 0.07, h * 0.66)], G2, ink)
    _ellipse(img, (cx, h * 0.53), (w * 0.09, h * 0.035), G, ink)
    # plinth
    _poly(img, [(cx - w * 0.22, h * 0.66), (cx + w * 0.22, h * 0.66), (cx + w * 0.27, h * 0.96),
                (cx - w * 0.27, h * 0.96)], (38, 30, 32), ink)
    _poly(img, [(cx - w * 0.12, h * 0.75), (cx + w * 0.12, h * 0.75), (cx + w * 0.12, h * 0.83),
                (cx - w * 0.12, h * 0.83)], G, 0)
    return _down(img), (w / 2, h * 0.72)


@functools.lru_cache(maxsize=16)
def broom(h):
    """a yard broom standing up: a long wooden handle, a red-bound head of straw bristles -> (RGBA, grip 40 % up)"""
    w = h * 0.30
    img = _canvas(w, h)
    ink = max(1.2, h * 0.008)
    cx = w / 2
    hw = h * 0.016
    _poly(img, [(cx - hw, h * 0.02), (cx + hw, h * 0.02), (cx + hw, h * 0.80), (cx - hw, h * 0.80)], (196, 140, 82), ink)
    _poly(img, [(cx - hw * 0.4, h * 0.03), (cx + hw * 0.1, h * 0.03), (cx + hw * 0.1, h * 0.79),
                (cx - hw * 0.4, h * 0.79)], (226, 176, 116), 0)
    # the bristles: a fan of straw strokes, then the binding
    br = [(cx - w * 0.15, h * 0.80), (cx + w * 0.15, h * 0.80), (cx + w * 0.46, h * 0.99), (cx - w * 0.46, h * 0.99)]
    _poly(img, br, (236, 196, 92), ink)
    for k in np.linspace(-0.40, 0.40, 13):
        x0, x1 = cx + k * w * 0.32, cx + k * w * 1.05
        cv2.line(img, (int(x0 * SS), int(h * 0.82 * SS)), (int(x1 * SS), int(h * 0.985 * SS)), (*(176, 132, 52), 255),
                 max(1, int(h * 0.004 * SS)), cv2.LINE_AA)
    _poly(img, [(cx - w * 0.17, h * 0.78), (cx + w * 0.17, h * 0.78), (cx + w * 0.19, h * 0.84),
                (cx - w * 0.19, h * 0.84)], (200, 24, 32), ink)
    return _down(img), (cx, h * 0.40)


SCARVES = {   # stripe colours, repeated along the length
    "bars": [(206, 18, 28), (206, 18, 28), (246, 244, 238), (24, 20, 22), (246, 244, 238)],
    "red": [(206, 18, 28), (206, 18, 28), (206, 18, 28), (246, 244, 238)],
    "black": [(24, 20, 22), (206, 18, 28), (24, 20, 22), (246, 244, 238)],
}


@functools.lru_cache(maxsize=64)
def scarf_cloth(kind, w, h):
    """a knitted bar scarf laid flat (RGBA, w along its length x h), stripes across it, tassels at both ends, the
    knit drawn as faint ribs, a dark outline"""
    img = np.zeros((h, w, 4), np.uint8)
    cols = SCARVES[kind]
    tas = max(3, int(0.12 * h))
    body = (tas, w - tas)
    n = max(4, int((body[1] - body[0]) / (h * 0.55)))
    xs = np.linspace(body[0], body[1], n + 1)
    for k in range(n):
        c = cols[k % len(cols)]
        img[:, int(xs[k]):int(xs[k + 1]) + 1, :3] = c
    img[:, body[0]:body[1], 3] = 255
    rib = (np.arange(h) % max(2, h // 7) == 0)
    img[rib, body[0]:body[1], :3] = (img[rib, body[0]:body[1], :3] * 0.82).astype(np.uint8)
    for x0, x1 in ((0, body[0]), (body[1], w)):                  # tassels in the end stripe's colour
        c = cols[0]
        for y in range(1, h, max(2, h // 8)):
            cv2.line(img, (x0, y), (x1, y), (*c, 255), 1, cv2.LINE_AA)
    lw = max(1, h // 14)
    cv2.rectangle(img, (body[0], 0), (body[1], h - 1), (*INK, 255), lw)
    return img


def football():
    im = np.asarray(Image.open(PROPS / "lunch" / "football.png").convert("RGBA"))
    return im


def microphone():
    return np.asarray(Image.open(PROPS / "music" / "microphone.png").convert("RGBA"))

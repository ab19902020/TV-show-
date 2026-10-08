"""The film knows it is being filmed: overlays a shot can ask for in direction.py (drawn by actors.post on the
finished frame, all in 1920 x 1080 layout px scaled by RS).

  vf=dict(label, live)        Goldbridge's phone camera: a vertical-video safe frame, corner brackets, a blinking
                              REC dot, a running timecode, a battery, a LIVE badge with a viewer count ticking up
  lower=dict(t0, t1, top, sub) a broadcast lower third that slides in and out
  crash=[t, ...]              a crash zoom lands at each time: a white flash and a short streak blur
  lens_hand=(t0, t1)          a hand comes up over the lens (the last shot: Keane has had enough)
  rec_flash=[t, ...]          a phone flash goes off in front of the lens
"""
import functools
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from studio.film.engine import OH, OW, RS


@functools.lru_cache(maxsize=1)
def _fonts():
    from studio.film.graphics import BEBAS
    return BEBAS


def _font(size):
    return ImageFont.truetype(_fonts(), max(8, int(size * RS)))


def _over(img, rgba):
    """premultiplied-free RGBA uint8 layer over a float frame"""
    a = rgba[..., 3:4].astype(np.float32) / 255.0
    return img * (1 - a) + rgba[..., :3].astype(np.float32) / 255.0 * a


def viewfinder(img, t, s, o):
    """Goldbridge filming on his phone"""
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    W, H = OW, OH
    m = int(46 * RS)
    L = int(90 * RS)
    w = max(2, int(6 * RS))
    for (x, y, dx, dy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, H - m, 1, -1), (W - m, H - m, -1, -1)):
        d.line([(x, y), (x + dx * L, y)], fill=(255, 255, 255, 235), width=w)
        d.line([(x, y), (x, y + dy * L)], fill=(255, 255, 255, 235), width=w)
    # REC dot (blinks once a second) and timecode
    if (t % 1.0) < 0.62:
        r = int(15 * RS)
        d.ellipse([m + 30 * RS - r, m + 52 * RS - r, m + 30 * RS + r, m + 52 * RS + r], fill=(235, 30, 30, 255))
    f = _font(46)
    d.text((m + 56 * RS, m + 28 * RS), "REC", font=f, fill=(255, 255, 255, 240))
    tc = 734.0 + t                                   # he has been filming since before the pub filled up
    d.text((m + 150 * RS, m + 28 * RS), f"{int(tc // 3600):02d}:{int(tc // 60) % 60:02d}:{int(tc) % 60:02d}",
           font=f, fill=(255, 255, 255, 240))
    # LIVE badge and viewers (right)
    if o.get("live", True):
        f2 = _font(40)
        x1 = W - m - 30 * RS
        views = int(18400 + 2600 * (t - s["t"]) + 37 * math.sin(t * 7))
        txt = f"{views:,} watching"
        bx = d.textbbox((0, 0), txt, font=f2)
        tw = bx[2] - bx[0]
        y = m + 30 * RS
        d.rounded_rectangle([x1 - tw - 150 * RS, y - 4 * RS, x1 - tw - 40 * RS, y + 46 * RS], radius=int(8 * RS),
                            fill=(225, 20, 30, 240))
        d.text((x1 - tw - 136 * RS, y - 2 * RS), "LIVE", font=f2, fill=(255, 255, 255, 255))
        d.text((x1 - tw - 20 * RS, y - 2 * RS), txt, font=f2, fill=(255, 255, 255, 235))
    # battery (bottom right) and the channel's name (bottom left)
    bx0, by0 = W - m - 120 * RS, H - m - 66 * RS
    d.rectangle([bx0, by0, bx0 + 84 * RS, by0 + 38 * RS], outline=(255, 255, 255, 230), width=max(2, int(4 * RS)))
    d.rectangle([bx0 + 84 * RS, by0 + 11 * RS, bx0 + 92 * RS, by0 + 27 * RS], fill=(255, 255, 255, 230))
    d.rectangle([bx0 + 7 * RS, by0 + 7 * RS, bx0 + 22 * RS, by0 + 31 * RS], fill=(235, 60, 40, 240))
    d.text((m + 30 * RS, H - m - 74 * RS), o.get("label", "GOLDBRIDGE CAM"), font=_font(44),
           fill=(255, 255, 255, 235))
    img = img * 0.96 + 0.02                          # a phone's flatter, lifted picture
    return _over(img, np.asarray(lay))


def lower_third(img, t, o):
    t0, t1 = o["t0"], o["t1"]
    if not (t0 <= t <= t1):
        return img
    u = min(1.0, (t - t0) / 0.35, (t1 - t) / 0.3)
    u = u * u * (3 - 2 * u)
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x = int((120 - 900 * (1 - u)) * RS)
    y = int(820 * RS)
    f1, f2 = _font(96), _font(46)
    top, sub = o["top"], o["sub"]
    w1 = d.textbbox((0, 0), top, font=f1)[2]
    d.rectangle([x - 30 * RS, y - 10 * RS, x + w1 + 40 * RS, y + 100 * RS], fill=(200, 16, 32, 235))
    d.rectangle([x - 30 * RS, y - 10 * RS, x - 14 * RS, y + 100 * RS], fill=(255, 210, 60, 255))
    d.text((x, y - 6 * RS), top, font=f1, fill=(255, 255, 255, 255))
    w2 = d.textbbox((0, 0), sub, font=f2)[2]
    d.rectangle([x - 30 * RS, y + 100 * RS, x + w2 + 40 * RS, y + 160 * RS], fill=(16, 12, 14, 230))
    d.text((x, y + 104 * RS), sub, font=f2, fill=(255, 220, 120, 255))
    return _over(img, np.asarray(lay))


def crash(img, t, times):
    for tc in times:
        k = t - tc
        if -0.05 <= k < 0.28:
            a = math.exp(-max(0.0, k) / 0.06)
            img = img + (1 - img) * 0.35 * a
            if k < 0.12:                                 # the zoom's streak, radial from the centre
                n = 5
                acc = img.copy()
                for i in range(1, n):
                    z = 1 + 0.012 * i * (1 - k / 0.12)
                    M = cv2.getRotationMatrix2D((OW / 2, OH / 2), 0, z)
                    acc += cv2.warpAffine(img, M, (OW, OH), borderMode=cv2.BORDER_REFLECT)
                img = acc / n
    return img


def flash_pop(img, t, times):
    for tc in times:
        k = t - tc
        if 0 <= k < 0.18:
            a = math.exp(-k / 0.05)
            Y, X = np.mgrid[0:OH, 0:OW].astype(np.float32)
            g = np.exp(-(((X - 0.78 * OW) / (0.5 * OW)) ** 2 + ((Y - 0.35 * OH) / (0.5 * OH)) ** 2))
            img = img + (1 - img) * (0.75 * a * g)[..., None]
    return img


def lens_hand(img, t, span):
    """a big open hand (palm to the lens, fingers together: the house's mitten hand, as in Keane's clap) comes up
    from the bottom of the frame and covers the lens, out of focus; then black"""
    t0, t1 = span
    if t < t0:
        return img
    u = min(1.0, (t - t0) / (t1 - t0))
    u = u * u * (3 - 2 * u)
    S2 = 2 * RS
    H2, W2 = OH * 2, OW * 2
    sc = 1.3 + 2.2 * u
    cx, cy = 1060 - 60 * u, 1500 - 980 * u
    P = lambda pts: np.int32(np.float32(pts) * S2)   # noqa: E731
    m = np.zeros((H2, W2), np.uint8)
    cv2.fillPoly(m, [P(cv2.ellipse2Poly((int(cx), int(cy)), (int(150 * sc), int(250 * sc)), 6, 0, 360, 4))], 255,
                 cv2.LINE_AA)
    cv2.fillPoly(m, [P(cv2.ellipse2Poly((int(cx - 140 * sc), int(cy + 40 * sc)), (int(58 * sc), int(140 * sc)), 34,
                                        0, 360, 6))], 255, cv2.LINE_AA)
    sleeve = np.zeros_like(m)
    cv2.fillPoly(sleeve, [P([(cx - 140 * sc, cy + 200 * sc), (cx + 150 * sc, cy + 200 * sc),
                             (cx + 230 * sc, cy + 800 * sc), (cx - 230 * sc, cy + 800 * sc)])], 255, cv2.LINE_AA)
    lay = np.zeros((H2, W2, 4), np.float32)
    lay[..., :3] = np.float32([0.94, 0.70, 0.55])
    shade = np.zeros_like(m)
    cv2.fillPoly(shade, [P(cv2.ellipse2Poly((int(cx + 60 * sc), int(cy + 90 * sc)), (int(80 * sc), int(150 * sc)),
                                            6, 0, 360, 6))], 255, cv2.LINE_AA)
    sh = (np.minimum(shade, m).astype(np.float32) / 255)[..., None]
    lay[..., :3] = lay[..., :3] * (1 - sh) + np.float32([0.80, 0.54, 0.42]) * sh
    sl = (sleeve.astype(np.float32) / 255)[..., None]
    lay[..., :3] = lay[..., :3] * (1 - sl) + np.float32([0.07, 0.06, 0.08]) * sl
    a = np.maximum(m, sleeve).astype(np.float32) / 255
    lay[..., 3] = a
    ink = (0.09, 0.07, 0.08, 1.0)
    cs, _ = cv2.findContours((a > 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.polylines(lay, [c.reshape(-1, 2) for c in cs], True, ink, max(2, int(9 * S2 * sc / 2)), cv2.LINE_AA)
    for k in range(3):                                 # the fingers: three creases down from the top
        x = cx + (-60 + k * 52) * sc
        y0 = cy - (238 - 18 * abs(k - 1)) * sc
        cv2.line(lay, (int(x * S2), int(y0 * S2)), (int(x * S2), int((y0 + 110 * sc) * S2)), ink,
                 max(2, int(6 * S2 * sc / 2)), cv2.LINE_AA)
    lay = cv2.resize(lay, (OW, OH), interpolation=cv2.INTER_AREA)
    lay = cv2.GaussianBlur(lay, (0, 0), (0.6 + 14 * u * u) * RS)
    al = np.clip(lay[..., 3:4], 0, 1)
    out = img * (1 - al) + lay[..., :3] * al
    dark = max(0.0, (u - 0.7) / 0.3)
    return out * (1 - 0.92 * dark) * (1 - dark * dark * 0.08)


def concert_pulse(img, t, s):
    """Subtle beat-reactive wash, restrained to preserve facial detail.

    Only used on selected pub/stadium stage shots. Not a strobe and never
    applied to the crowd, the quiet outro button or Keane's lens ending.
    """
    from studio.film.stage import SONG
    phase = float(SONG().phase(t))
    attack = math.exp(-min(phase, 1.0 - phase) ** 2 / 0.011)
    level = min(1.0, max(0.0, float(s.get("lights", 1.0)) / 1.7))
    lift = level * (0.018 + 0.028 * attack)
    return np.clip(img + (1.0 - img) * lift, 0.0, 1.0)


def apply(img, s, t):
    if s.get("polish_lights"):
        img = concert_pulse(img, t, s)
    if s.get("rec_flash"):
        img = flash_pop(img, t, s["rec_flash"])
    if s.get("crash"):
        img = crash(img, t, s["crash"])
    if s.get("lower"):
        img = lower_third(img, t, s["lower"])
    if s.get("vf"):
        img = viewfinder(img, t, s, s["vf"])
    if s.get("lens_hand"):
        img = lens_hand(img, t, s["lens_hand"])
    return img

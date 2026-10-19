"""Every shot: props.scene draws the office at true scale with the actors placed by their feet (studio.film.render
world), the desk in front, the tea once served; then the gags and the portrait graphics: floating hearts, the title
strip, word-by-word captions, the BEST MATES end card. Layout in output px (portrait 1080 x 1920 at full size)."""
import functools
import json
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from studio.film import ep
from studio.film.engine import OH, OW
from studio.paths import ROOT

BEBAS = str(ROOT / "library/fonts/BebasNeue-Regular.ttf")
U = OW / 1080.0                                        # output px per layout px


@functools.lru_cache(maxsize=32)
def F(size):
    return ImageFont.truetype(BEBAS, max(8, int(size * U)))


def sm(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def over(img, lay):
    a = np.asarray(lay).astype(np.float32) / 255.0
    return img * (1 - a[..., 3:4]) + a[..., :3] * a[..., 3:4]


LD = json.loads(ep.path("lines.json").read_text())


@functools.lru_cache(maxsize=1)
def TLm():
    from film.timeline import TL
    return TL


def _at(keys, t):
    v = keys[0][1]
    for tk, val in keys:
        if t >= tk:
            v = val
    return v


def _lerp(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, a), (t1, b) in zip(keys, keys[1:]):
        if t < t1:
            u = sm((t - t0) / max(1e-3, t1 - t0))
            return a + (b - a) * u if not isinstance(a, tuple) else tuple(x + (y - x) * u for x, y in zip(a, b))
    return keys[-1][1]


@functools.lru_cache(maxsize=64)
def _size(draw):
    from studio.paths import CHARACTERS
    import yaml
    cid, name = draw.split(":")
    sp = yaml.safe_load((CHARACTERS / cid / "film.yaml").read_text())["drawings"][name]
    return Image.open(CHARACTERS / cid / sp["image"]).size


def _actor(a, t, s):
    from studio.film.cast import CAST
    from film.direction import K
    draw = _at(a["keys"], t)
    _, info = CAST.get(draw)
    w, h = _size(draw)
    bx, by = _lerp(a["x"], t), a["y"]
    if a.get("walk") and a["walk"][0] <= t < a["walk"][1]:
        by -= abs(math.sin((t - a["walk"][0]) * 7.5)) * 9           # the bounce of his steps
    ax, ay = info["anchor"]
    sg = -1 if a.get("mirror") else 1
    return (a["who"], draw, (bx + sg * (ax - w / 2) * K, by + (ay - h) * K), info["ed"] * K, bool(a.get("mirror")))


def scene(s, t):
    from studio.film import render as R
    from studio.film.shots import world
    tl = [(s["t"] + dt if dt < s["t"] else dt, c) for dt, c in s["cams"]]
    layers = [("actors", [_actor(a, t, s) for a in s["acts"]]), ("occl", "desk")]
    if s.get("tea") is not None and t >= s["tea"]:
        layers.append(("props", "tea"))
    w = world(s["t"], "O", tl[0][1], cams=tl, layers=layers, drift=0.5)
    w.update(end=s["end"], i=s["i"])
    img = R.render_world(w, t)
    if s.get("hearts"):
        img = hearts(img, t, s["hearts"])
    if s.get("title") and t < s["end"]:
        img = title(img, t, s)
    img = captions(img, t)
    if s.get("best") is not None and t >= s["best"]:
        img = best(img, t - s["best"])
    return img


@functools.lru_cache(maxsize=1)
def _tea():
    return Image.open(ep.DIR / "reference" / "tea_biscuits.png").convert("RGBA")


def tea(img, s, t, M, sc):
    """the tea and biscuits, on the desk beside him"""
    from film.direction import CHAIR_X, K
    im = _tea()
    wpx = 208 * K * 0.42 * M[0, 0]
    sp = im.resize((max(2, int(wpx)), max(2, int(wpx * im.height / im.width))), Image.LANCZOS)
    x = M[0, 0] * (CHAIR_X - 150) + M[0, 2]
    y = M[1, 1] * 1000 + M[1, 2]
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    lay.alpha_composite(sp, (int(x - sp.width / 2), int(y - sp.height)))
    return over(img, lay)


def hearts(img, t, span):
    a, b = span
    if not a <= t <= b + 1.0:
        return img
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(4)
    for i in range(10):
        t0 = a + rng.uniform(0, max(0.1, b - a))
        k = t - t0
        if not 0 <= k <= 2.2:
            continue
        x = (rng.uniform(250, 830) + 30 * math.sin(k * 3 + i)) * U
        y = (rng.uniform(700, 1050) - 260 * k) * U
        r = rng.uniform(26, 44) * U * (0.6 + 0.4 * min(1, k * 3))
        al = int(255 * (1 - sm((k - 1.4) / 0.8)))
        col = (235, 40, 70, al)
        d.ellipse([x - r, y - r, x, y], fill=col)
        d.ellipse([x, y - r, x + r, y], fill=col)
        d.polygon([(x - r * 0.97, y - r * 0.35), (x + r * 0.97, y - r * 0.35), (x, y + r * 0.95)], fill=col)
    return over(img, lay)


def _strip(d, text, y, size, fill, bg):
    f = F(size)
    tw = d.textlength(text, font=f)
    pad = 26 * U
    d.rounded_rectangle([OW / 2 - tw / 2 - pad, y - size * 0.62 * U, OW / 2 + tw / 2 + pad, y + size * 0.62 * U],
                        radius=18 * U, fill=bg)
    d.text((OW / 2, y), text, font=f, fill=fill, anchor="mm")


def title(img, t, s):
    k = sm((t - 0.3) / 0.4) * (1 - sm((t - (s["end"] - 0.4)) / 0.4))
    if k <= 0:
        return img
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    _strip(d, "RIO ON HIS 'MATE' JASON WILCOX", 150 * U, 70, (255, 255, 255, int(255 * k)), (200, 16, 30, int(235 * k)))
    return over(img, lay)


@functools.lru_cache(maxsize=1)
def _words():
    """every spoken word with its time, in chunks of up to three for the captions"""
    TL = TLm()
    out = []
    for lid, v in TL["lines"].items():
        ws = LD[lid]["words"]
        disp = LD[lid]["text"].replace("—", " ").split()
        chunk = []
        for i, w in enumerate(ws):
            label = disp[i] if len(disp) == len(ws) else w["w"]
            chunk.append((v["start"] + w["s"], v["start"] + w["e"], label.upper().strip(",.")))
            if len(chunk) == 3 or label[-1:] in ",." or i == len(ws) - 1:
                out.append(chunk)
                chunk = []
    return out


def captions(img, t):
    cur = None
    for ch in _words():
        if ch[0][0] - 0.05 <= t <= ch[-1][1] + 0.25:
            cur = ch
    if cur is None:
        return img
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = F(92)
    parts = [w for _, _, w in cur]
    sizes = [d.textlength(p, font=f) for p in parts]
    gap = 22 * U
    x = OW / 2 - (sum(sizes) + gap * (len(parts) - 1)) / 2
    y = 1460 * U
    for (s0, e0, w), sz in zip(cur, sizes):
        on = s0 - 0.02 <= t < e0
        pop = 1.08 if on else 1.0
        ff = F(int(92 * pop))
        d.text((x + sz / 2, y), w, font=ff, fill=(255, 225, 40) if on else (255, 255, 255), anchor="mm",
               stroke_width=int(9 * U), stroke_fill=(0, 0, 0))
        x += sz + gap
    return over(img, lay)


def best(img, k):
    a = sm(k / 0.35)
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    s = 1 + 0.25 * math.exp(-k / 0.12)
    _strip(d, "BEST MATES", 1200 * U, int(150 * s), (255, 255, 255, int(255 * a)), (200, 16, 30, int(240 * a)))
    _strip(d, "(ONE OF THEM KNOWS IT)", 1330 * U, 54, (255, 225, 40, int(255 * a)), (0, 0, 0, int(200 * a)))
    return over(img, lay)


def plate_image(k):
    return None

"""Everything over the characters: Saeed's live stream (player chrome, LIVE badge, viewer count, a live chat that
reacts), Rio's clip in the corner of it, Rio's video reply badge, the posts that type themselves out, the split
screen, and the gags (Old Trafford at 2-0 down, the crash zooms, the sirens, the plates piling up).

compose(s, t) is the episode's shot: it renders the inner single (studio.film.render) and draws the rest on it.
All layout in 1920 x 1080 px, scaled by RS."""
import functools
import json
import math

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from studio.film import ep
from studio.film.engine import OH, OW, RS
from studio.paths import BUILD

INTER = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
INTER_R = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
INTER_X = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"


@functools.lru_cache(maxsize=64)
def F(size, kind="b"):
    from studio.film.graphics import BEBAS
    path = {"b": INTER, "r": INTER_R, "x": INTER_X, "bebas": BEBAS}[kind]
    try:
        return ImageFont.truetype(path, max(8, int(size * RS)))
    except OSError:
        return ImageFont.truetype(BEBAS, max(8, int(size * RS)))


def P(v):
    return int(round(v * RS))


def over(img, lay):
    """an RGBA uint8 PIL layer (OW x OH) over a float frame"""
    a = np.asarray(lay).astype(np.float32) / 255.0
    return img * (1 - a[..., 3:4]) + a[..., :3] * a[..., 3:4]


def sm(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


TLD = json.loads(ep.path("lines.json").read_text())


@functools.lru_cache(maxsize=1)
def marks():
    from film.timeline import TL
    from studio.film.shots import Marks
    return Marks(TL, TLD)


# ---------------------------------------------------------------- avatars (round crops of their faces)
@functools.lru_cache(maxsize=8)
def avatar(who, d):
    f, box = {"saeed": ("saeed-the-lecher/neutral.png", (0.08, 0.02, 0.92, 0.86)),
              "rio": ("rio-ferdinand/mic.png", (0.20, 0.0, 0.80, 0.30))}[who]
    im = Image.open(BUILD / "film" / f).convert("RGBA")
    W, H = im.size
    x0, y0, x1, y1 = box
    c = im.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    s = min(c.size)
    c = c.crop(((c.size[0] - s) // 2, 0, (c.size[0] - s) // 2 + s, s)).resize((d, d), Image.LANCZOS)
    bg = Image.new("RGBA", (d, d), (200, 30, 40, 255) if who == "saeed" else (40, 44, 52, 255))
    bg.alpha_composite(c)
    mask = Image.new("L", (d, d), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, d - 1, d - 1], fill=255)
    out = Image.new("RGBA", (d, d), (0, 0, 0, 0))
    out.paste(bg, (0, 0), mask)
    return out


# ---------------------------------------------------------------- the live chat
CHAT = [  # (time key, user, colour, message): time keys are (line, word) or marks
    (("open", 0.3), "united_til_i_die", (255, 120, 120), "WE'RE LIVE LADS"),
    (("L001", "ferdinand"), "glazersout99", (130, 200, 255), "oh here we go"),
    (("L001", "microphone"), "salfordred", (255, 205, 90), "he's going for rio 💀"),
    (("L001", "followers"), "stretty_kev", (150, 255, 160), "RIO WILL SEE THIS"),
    (("L002", "glazers"), "theholmesbaby", (255, 160, 220), "GLAZERS OUT"),
    (("L002", "quieter"), "red_dev_jay", (130, 200, 255), "quieter than old trafford LMAO"),
    (("L002", "down"), "mufc_mo", (255, 205, 90), "so... every week then"),
    (("L004", "timber"), "salfordred", (255, 205, 90), "NOT THE MIRROR 😭"),
    (("L004", "timber"), "glazersout99", (130, 200, 255), "rio cooked him"),
    (("L005", "tits"), "stretty_kev", (150, 255, 160), "AHAHAHAHA"),
    (("L006", "tits"), "united_til_i_die", (255, 120, 120), "TITS 💀💀💀"),
    (("L006", "tits"), "theholmesbaby", (255, 160, 220), "TITS"),
    (("L006", "tits"), "red_dev_jay", (130, 200, 255), "TITSSSSS"),
    (("L007", "visible"), "mufc_mo", (255, 205, 90), "AT LEAST MINE ARE VISIBLE 😭😭"),
    (("L007", "visible"), "big_dunc", (180, 255, 255), "he's not wrong tbf"),
    (("L008", "glazers"), "glazersout99", (130, 200, 255), "20 YEARS 😤"),
    (("L008", "body"), "salfordred", (255, 205, 90), "body checks 💀"),
    (("L009", "police"), "stretty_kev", (150, 255, 160), "WEE WOO WEE WOO"),
    (("L009", "police"), "theholmesbaby", (255, 160, 220), "fashion police lmaooo"),
    (("L011", "decade"), "united_til_i_die", (255, 120, 120), "the last decade is a lot of plates"),
    (("L011", "feelings"), "big_dunc", (180, 255, 255), "eat my feelings is crazy"),
    (("L011", "feelings"), "red_dev_jay", (130, 200, 255), "💀💀💀"),
    (("L012", "fault"), "mufc_mo", (255, 205, 90), "rio's not having it"),
    (("L013", "glazers"), "glazersout99", (130, 200, 255), "OHHHHHH"),
]


@functools.lru_cache(maxsize=1)
def chat_times():
    M = marks()
    out = []
    for key, user, col, msg in CHAT:
        if key[0].startswith("L"):
            t = M.wt(key[0], key[1]) + 0.25
        else:
            t = M.m(key[0]) + key[1]
        out.append((t, user, col, msg.encode("ascii", "ignore").decode().strip() or "lol"))
    return sorted(out)


def emoji_free(s):
    return s


def draw_chat(d, t, x0, y0, x1, y1):
    """the chat panel: newest at the bottom, each message sliding up as the next arrives"""
    d.rounded_rectangle([x0, y0, x1, y1], radius=P(14), fill=(14, 14, 16, 205))
    d.rectangle([x0, y0, x1, y0 + P(54)], fill=(24, 24, 28, 230))
    d.text((x0 + P(18), y0 + P(14)), "Live chat", font=F(26), fill=(240, 240, 240, 255))
    d.text((x1 - P(130), y0 + P(16)), "Top chat ▾".replace("▾", ""), font=F(20, "r"), fill=(170, 170, 170, 255))
    msgs = [c for c in chat_times() if c[0] <= t]
    y = y1 - P(18)
    lh = P(64)
    for i, (tm, user, col, msg) in enumerate(reversed(msgs[-9:])):
        slide = 1 - sm((t - tm) / 0.18) if i == 0 else 0.0
        yy = y - lh * (i + 1) + slide * lh
        if yy < y0 + P(60):
            break
        a = int(255 * (sm((t - tm) / 0.12) if i == 0 else 1))
        d.ellipse([x0 + P(16), yy + P(6), x0 + P(48), yy + P(38)], fill=col + (a,))
        d.text((x0 + P(58), yy + P(2)), user, font=F(19), fill=col + (a,))
        d.text((x0 + P(58), yy + P(26)), msg[:30], font=F(22, "r"), fill=(245, 245, 245, a))


# ---------------------------------------------------------------- the stream's chrome
def viewers(t):
    M = marks()
    v = 3800 + 260 * t
    for key, jump in (("L005", 4200), ("L006", 9000), ("L009", 3000), ("L013", 6000)):
        ts = M.ls(key)
        v += jump * sm((t - ts) / 1.2)
    return int(v + 23 * math.sin(t * 3.1))


def draw_stream(img, s, t):
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # the live chat down the right
    draw_chat(d, t, P(1440), P(130), P(1890), P(900))
    # LIVE badge and viewers (top left)
    d.rounded_rectangle([P(36), P(34), P(132), P(76)], radius=P(6), fill=(230, 33, 23, 255))
    d.text((P(50), P(37)), "LIVE", font=F(30, "x"), fill=(255, 255, 255, 255))
    d.rounded_rectangle([P(142), P(34), P(400), P(76)], radius=P(6), fill=(0, 0, 0, 150))
    d.text((P(156), P(39)), f"{viewers(t):,} watching", font=F(26), fill=(255, 255, 255, 255))
    # the channel bar along the bottom: avatar, name, subscribe, the stream's title
    d.rectangle([0, P(930), OW, OH], fill=(10, 10, 12, 215))
    lay.alpha_composite(avatar("saeed", P(88)), (P(30), P(962)))
    d.text((P(136), P(950)), "RIO, WE NEED TO TALK (GLAZERS OUT)", font=F(36, "x"), fill=(255, 255, 255, 255))
    d.text((P(136), P(1004)), "The Lecher", font=F(26), fill=(220, 220, 220, 255))
    d.text((P(300), P(1004)), "1.4M subscribers", font=F(24, "r"), fill=(160, 160, 160, 255))
    d.rounded_rectangle([P(1640), P(966), P(1880), P(1034)], radius=P(34), fill=(255, 255, 255, 255))
    d.text((P(1676), P(980)), "Subscribe", font=F(30), fill=(15, 15, 15, 255))
    # the progress bar: live, all red
    d.rectangle([0, P(924), OW, P(930)], fill=(230, 33, 23, 255))
    return over(img, lay)


def draw_reply(img, s, t):
    """Rio's video reply: the badge saying what he is replying to, and its likes climbing"""
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle([P(40), P(40), P(720), P(130)], radius=P(16), fill=(255, 255, 255, 235))
    lay.alpha_composite(avatar("rio", P(70)), (P(52), P(50)))
    d.text((P(138), P(46)), "Rio Ferdinand", font=F(30, "x"), fill=(15, 15, 15, 255))
    d.text((P(138), P(86)), "Replying to The Lecher's live", font=F(24, "r"), fill=(90, 90, 90, 255))
    likes = int(12000 + 41000 * (t - marks().m("cut_reply")))
    d.rounded_rectangle([P(1580), P(960), P(1880), P(1040)], radius=P(40), fill=(0, 0, 0, 170))
    d.text((P(1610), P(976)), f"♥ {likes:,}".replace("♥", "LIKES"), font=F(30), fill=(255, 255, 255, 255))
    return over(img, lay)


# ---------------------------------------------------------------- the inner shots
def _inner(s, t, key="inner"):
    from studio.film import render as R
    sh = dict(s[key])
    for tk, dk in sh.get("keys", s.get("keys", []) if key == "inner" else []):
        if t >= tk:
            sh["draw"] = dk if ":" in dk else "saeed-the-lecher:" + dk
    return R.render_single(sh, t)


def _crash(img, t, tc):
    k = t - tc
    if -0.04 <= k < 0.3:
        img = img + (1 - img) * 0.4 * math.exp(-max(0.0, k) / 0.06)
        if k < 0.12:
            acc = img.copy()
            for i in range(1, 5):
                M = cv2.getRotationMatrix2D((OW / 2, OH / 2), 0, 1 + 0.015 * i * (1 - k / 0.12))
                acc += cv2.warpAffine(img, M, (OW, OH), borderMode=cv2.BORDER_REFLECT)
            img = acc / 5
    return img


def _shake(img, t, span):
    a, b = span
    if a <= t <= b:
        amp = 26 * RS * (1 - (t - a) / (b - a))
        dx, dy = amp * math.sin(t * 91), amp * math.cos(t * 77)
        img = cv2.warpAffine(img, np.float32([[1.04, 0, dx - 0.02 * OW], [0, 1.04, dy - 0.02 * OH]]), (OW, OH),
                             borderMode=cv2.BORDER_REFLECT)
    return img


def _siren(img, t, span):
    a, b = span
    if not (a <= t <= b):
        return img
    u = (t - a) * 4.0
    red = (int(u) % 2) == 0
    col = np.float32([1.0, 0.1, 0.1]) if red else np.float32([0.15, 0.3, 1.0])
    X = np.linspace(0, 1, OW, dtype=np.float32)[None, :, None]
    side = X if red else (1 - X)
    g = (0.55 * side ** 2.5) * (1 - abs((u % 1) - 0.5) * 1.2)
    return np.clip(img + g * col, 0, 1)


def _counter(img, t, spec):
    """a number that spins up over the shot: (start time, label)"""
    t0, label = spec
    if t < t0:
        return img
    u = sm((t - t0) / 0.9)
    val = {"RIO'S FOLLOWERS": 14_300_000, "YEARS OF THE GLAZERS": 20}[label]
    v = int(val * u)
    txt = f"{v:,}"
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    pop = 1 + 0.25 * math.exp(-(t - t0) / 0.12)
    f = F(int(110 * pop), "bebas")
    d.rounded_rectangle([P(80), P(640), P(820), P(880)], radius=P(20), fill=(230, 33, 23, 225))
    d.text((P(110), P(650)), txt, font=f, fill=(255, 255, 255, 255))
    d.text((P(114), P(800)), label, font=F(54, "bebas"), fill=(255, 225, 120, 255))
    return over(img, lay)


@functools.lru_cache(maxsize=2)
def plate_sprite():
    from studio.paths import PROPS
    im = Image.open(PROPS / "lunch" / "plate-empty.png").convert("RGBA")
    return im


def _plates(img, t, span):
    """empty plates stacking up on the desk in front of him, one on every beat, the tower leaning"""
    a, b = span
    if t < a:
        return img
    from studio.film.stage import SONG  # noqa: F401 (no song here: plates on a steady count)
    n = min(12, int((t - a) / ((b - a) / 12)) + 1)
    spr = plate_sprite()
    w = P(230)
    h = int(spr.size[1] * w / spr.size[0])
    pl = spr.resize((w, h), Image.LANCZOS)
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    for side, x in ((0, P(130)), (1, P(1190))):
        for i in range(n if side == 0 else max(0, n - 3)):
            lean = (i ** 1.6) * 0.8 * (1 if side == 0 else -1) * (1 + 0.15 * math.sin(t * 7))
            y = P(905) - i * int(h * 0.38)
            tm = a + i * (b - a) / 12
            if t - tm < 0.12:
                y -= int(P(60) * (1 - (t - tm) / 0.12))
            lay.alpha_composite(pl, (int(x + lean * RS), int(y)))
    return over(img, lay)


def compose(s, t):
    img = _inner(s, t)
    if s.get("crash") is not None:
        img = _crash(img, t, s["crash"])
    if s.get("shake"):
        img = _shake(img, t, s["shake"])
    if s.get("plates"):
        img = _plates(img, t, s["plates"])
    if s.get("pip"):
        sub = _inner(s, t, "pip")
        w, h = P(560), P(315)
        sub = cv2.resize(sub, (w, h), interpolation=cv2.INTER_AREA)
        x0, y0 = P(40), P(110)
        img = img.copy()
        img[y0 - P(6):y0 + h + P(6), x0 - P(6):x0 + w + P(6)] = (0.95, 0.95, 0.95)
        img[y0:y0 + h, x0:x0 + w] = sub
        lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        d.rounded_rectangle([x0 + P(10), y0 + h - P(48), x0 + P(330), y0 + h - P(10)], radius=P(8),
                            fill=(0, 0, 0, 190))
        d.text((x0 + P(22), y0 + h - P(45)), "RIO'S REPLY  ▶".replace("▶", ""), font=F(24, "x"),
               fill=(255, 255, 255, 255))
        img = over(img, lay)
    if s.get("siren"):
        img = _siren(img, t, s["siren"])
    if s.get("counter"):
        img = _counter(img, t, s["counter"])
    if s.get("yt"):
        img = draw_stream(img, s, t)
    if s.get("reply"):
        img = draw_reply(img, s, t)
    if s.get("live_in") is not None and t - s["live_in"] < 0.6:      # the stream starting: a white flash in
        img = img + (1 - img) * (1 - sm((t - s["live_in"]) / 0.6))
    return img


# ---------------------------------------------------------------- Old Trafford, 2-0 down
def old_trafford(s, t):
    from studio.film import render as R
    P_ = R.plate("OT")
    u = sm((t - s["t"]) / max(1e-3, s["end"] - s["t"]))
    img = P_.render(836, 430, 1.25 + 0.06 * u)
    lum = img.mean(2, keepdims=True)
    img = lum * 0.75 + img * 0.25                       # drained of colour
    img = img * 0.8
    # the tumbleweed rolls across the pitch, bouncing
    k = (t - s["t"]) / (s["end"] - s["t"])
    x = -200 + 2300 * k
    y = 870 - abs(math.sin(k * math.pi * 3)) * 60
    r = 115
    y = 820 - abs(math.sin(k * math.pi * 3)) * 90
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rng = np.random.default_rng(4)
    rot = k * 14
    for i in range(80):
        a0 = rng.uniform(0, 6.28) + rot
        a1 = a0 + rng.uniform(1.0, 2.6)
        rr = r * rng.uniform(0.5, 1.0)
        pts = [(P(x + rr * math.cos(a0 + (a1 - a0) * q / 8)), P(y + rr * math.sin(a0 + (a1 - a0) * q / 8)))
               for q in range(9)]
        d.line(pts, fill=(96, 70, 38, 255), width=max(3, P(8)))
        d.line(pts, fill=(170, 130, 80, 255), width=max(1, P(3)))
    d.ellipse([P(x - r * 1.1), P(y + r * 0.95), P(x + r * 1.1), P(y + r * 1.15)], fill=(0, 0, 0, 90))
    d.text((P(60), P(60)), "OLD TRAFFORD.", font=F(110, "bebas"), fill=(255, 255, 255, 255))
    d.text((P(64), P(170)), "2-0 DOWN.", font=F(80, "bebas"), fill=(230, 60, 60, 255))
    return over(img, lay)


# ---------------------------------------------------------------- the posts
def _post(d, lay, x0, y0, w, who, name, handle, text, n_chars, counts, extra=None):
    d.rounded_rectangle([x0, y0, x0 + w, y0 + P(560)], radius=P(28), fill=(255, 255, 255, 255))
    lay.alpha_composite(avatar(who, P(110)), (x0 + P(36), y0 + P(36)))
    d.text((x0 + P(166), y0 + P(44)), name, font=F(44, "x"), fill=(15, 20, 25, 255))
    d.text((x0 + P(166), y0 + P(98)), handle, font=F(32, "r"), fill=(110, 118, 125, 255))
    shown = text[:n_chars]
    lines, cur = [], ""
    for wd in shown.split(" "):
        test = (cur + " " + wd).strip()
        if d.textlength(test, font=F(52, "b")) > w - P(80):
            lines.append(cur)
            cur = wd
        else:
            cur = test
    lines.append(cur)
    for i, ln in enumerate(lines):
        d.text((x0 + P(40), y0 + P(180) + i * P(70)), ln, font=F(52, "b"), fill=(15, 20, 25, 255))
    if n_chars < len(text) and (int(n_chars) % 2 == 0):
        lx = x0 + P(40) + int(d.textlength(lines[-1], font=F(52, "b"))) + P(6)
        ly = y0 + P(180) + (len(lines) - 1) * P(70)
        d.rectangle([lx, ly + P(6), lx + P(5), ly + P(60)], fill=(29, 155, 240, 255))
    d.line([x0 + P(36), y0 + P(470), x0 + w - P(36), y0 + P(470)], fill=(225, 230, 235, 255), width=P(2))
    cx = x0 + P(50)
    for label, v in counts:
        d.text((cx, y0 + P(490)), f"{v:,} {label}", font=F(30, "b"), fill=(83, 100, 113, 255))
        cx += P(330)
    if extra:
        d.text((x0 + P(40), y0 + P(580)), extra, font=F(30, "b"), fill=(240, 240, 240, 255))


def _desk_blur_bg(t):
    from studio.film import render as R
    P_ = R.plate("P")
    img = P_.render(836, 360, 1.3)
    img = cv2.GaussianBlur(img, (0, 0), 14 * RS)
    return img * 0.55


def post_rio(s, t):
    """Rio's post: the words type out as he says them (L003); the counts go mad"""
    M = marks()
    img = _desk_blur_bg(t)
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    text = "Saeed mate. Before you start lecturing me, have you looked in a mirror?"
    words = TLD["L003"]["words"]
    t0 = M.ls("L003")
    n = 0
    acc = 0
    parts = text.split(" ")
    for i, wdd in enumerate(words):
        if t >= t0 + wdd["s"]:
            n = sum(len(p) + 1 for p in parts[:i + 1])
    if t >= M.le("L003"):
        n = len(text)
    k = max(0.0, t - s["t"])
    counts = [("Replies", int(800 + 4000 * k)), ("Reposts", int(2100 + 9000 * k)), ("Likes", int(9000 + 31000 * k))]
    pop = sm(k / 0.3)
    x0 = P(260)
    y0 = int(P(250) + (1 - pop) * P(80))
    _post(d, lay, x0, y0, P(1400), "rio", "Rio Ferdinand", "replying to @TheLecher", text, n, counts)
    img = over(img, lay)
    return img


def post_end(s, t):
    """the post that ends it: Saeed's last word, and Rio's reply settings"""
    img = np.zeros((OH, OW, 3), np.float32) + np.float32([0.05, 0.05, 0.07])
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    k = max(0.0, t - s["t"])
    text = "Funny how we're both avoiding responsibility, eh Rio?"
    n = min(len(text), int(k * 60))
    counts = [("Replies", 0), ("Reposts", int(31000 * sm(k / 2.5))), ("Likes", int(212000 * sm(k / 2.5)))]
    _post(d, lay, P(260), P(150), P(1400), "saeed", "The Lecher", "@TheLecher", text, n, counts)
    if k > 1.4:
        a = int(255 * sm((k - 1.4) / 0.3))
        d.rounded_rectangle([P(260), P(760), P(1660), P(860)], radius=P(20), fill=(29, 155, 240, a))
        d.text((P(300), P(782)), "Rio Ferdinand has limited who can reply", font=F(44, "x"), fill=(255, 255, 255, a))
    if k > 2.2:
        a = int(255 * sm((k - 2.2) / 0.3))
        d.text((P(560), P(900)), "THE LECHER  vs  RIO", font=F(110, "bebas"), fill=(230, 40, 40, a))
    img = over(img, lay)
    fade = sm((t - (s["end"] - 0.5)) / 0.5)
    return img * (1 - fade)


# ---------------------------------------------------------------- the split screen
def split(s, t):
    from studio.film import render as R
    a = R.render_single(s["left"], t)
    b = R.render_single(s["right"], t)
    h = OW // 4
    img = np.concatenate([a[:, h:h + OW // 2], b[:, h:h + OW // 2]], axis=1).copy()
    img[:, OW // 2 - P(4):OW // 2 + P(4)] = (0.96, 0.96, 0.96)
    lay = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for x, label in ((P(40), "THE LECHER  •  LIVE"), (OW // 2 + P(40), "RIO FERDINAND  •  REPLY")):
        d.rounded_rectangle([x, P(40), x + P(520), P(104)], radius=P(10), fill=(0, 0, 0, 170))
        d.text((x + P(20), P(50)), label.replace("•", "|"), font=F(36, "x"), fill=(255, 255, 255, 255))
    M = marks()
    if t >= M.m("silence") + 0.6:                     # the silence: a tiny "..." typing bubble, then nothing
        k = t - M.m("silence") - 0.6
        dots = int(k * 3) % 4
        d.rounded_rectangle([OW // 2 - P(90), P(940), OW // 2 + P(90), P(1010)], radius=P(34), fill=(255, 255, 255, 220))
        for i in range(3):
            c = 60 if i < dots else 180
            d.ellipse([OW // 2 - P(52) + i * P(36), P(962), OW // 2 - P(28) + i * P(36), P(986)], fill=(c, c, c, 255))
    return over(img, lay)

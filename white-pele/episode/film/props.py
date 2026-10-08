"""The sets and props of The White Pelé (the plates are cached in build/ the first time they are needed):

  the pub (from United Road's props.py, unchanged): F the stage front view with its mic stand painted out (Rooney
      sings into his own handheld), FC the same with the fans in the foreground (cut out so they jump), PUB the back
      of the pub at night, seen from the stage; S the stage from the side
  ST the matchday street at dusk, red-and-white bunting strung across it; MW a painted mural wall on the same street
  EXT, EXT2 Old Trafford at dusk; TUN the tunnel looking back to the dressing rooms, TUNP looking out to the pitch
  OT Old Trafford at night under the floodlights; OTS the same with the performance stage built on the pitch
  MEM the football memory: a sunlit stadium in the warmer, nostalgic grade

The stands are filled with a crowd drawn as its own layer (crowd_layer), so it bounces on the beat and a scarf
wave can travel round the ground (stands). Held props (hold), the ball (ball), typography (mural lettering, the
street sign) and the inserts are drawn here too."""
import functools

import cv2
import numpy as np
from PIL import Image

from studio.film import ep

STAGE = "pub-and-restaurant/united-pub-stage"
CROWD = "pub-and-restaurant/united-pub-stage-crowd"
SIDE = "pub-and-restaurant/united-pub-stage-side-crowd"

# the mic stand in the middle of the front view (1x plate px): its head, pole and base
MIC = [[(805, 256), (838, 256), (838, 304), (805, 304)],
       [(811, 298), (830, 298), (830, 541), (811, 541)]]
MIC_BASE = ((822, 547), (37, 12))
# the table with bottles and a candle among the fans of the crowd view: it stays put when the fans jump
TABLE = [(318, 752), (360, 728), (450, 716), (560, 706), (560, 660), (600, 660), (605, 700), (640, 706), (650, 712),
         (700, 704), (712, 710), (800, 742), (808, 790), (770, 820), (690, 836), (560, 842), (430, 838), (350, 822),
         (318, 795)]


def _x4(name):
    from studio.episode.upscale import upscaled
    from studio.paths import BACKGROUNDS
    return upscaled(BACKGROUNDS / f"{name}.png", 4.0)[..., ::-1].copy()          # RGB


def _mic_mask(shape, scale):
    m = np.zeros(shape[:2], np.uint8)
    for poly in MIC:
        cv2.fillPoly(m, [np.int32(np.float32(poly) * scale)], 255)
    (cx, cy), (rx, ry) = MIC_BASE
    cv2.ellipse(m, (int(cx * scale), int(cy * scale)), (int(rx * scale), int(ry * scale)), 0, 0, 360, 255, -1)
    return cv2.dilate(m, np.ones((int(3 * scale) | 1, int(3 * scale) | 1), np.uint8))


def _no_mic(big):
    """the mic stand painted out: inpainted from the curtain, the bass drum's head and the rug round it"""
    m = _mic_mask(big.shape, 4)
    x0, y0, x1, y1 = 760 * 4, 240 * 4, 880 * 4, 570 * 4
    sub = cv2.cvtColor(np.ascontiguousarray(big[y0:y1, x0:x1]), cv2.COLOR_RGB2BGR)
    fixed = cv2.inpaint(sub, m[y0:y1, x0:x1], 9, cv2.INPAINT_TELEA)
    out = big.copy()
    out[y0:y1, x0:x1] = cv2.cvtColor(fixed, cv2.COLOR_BGR2RGB)
    return out


@functools.lru_cache(maxsize=4)
def _plate(k):
    cache = ep.path(f"plate_{k}.png")
    if cache.exists():
        return cv2.cvtColor(cv2.imread(str(cache)), cv2.COLOR_BGR2RGB)
    big = _no_mic(_x4(STAGE if k == "F" else CROWD))
    cv2.imwrite(str(cache), cv2.cvtColor(big, cv2.COLOR_RGB2BGR))
    return big


# the back of the pub (what the crowd has behind them, seen from the stage): the windows' glass (1x px)
PUB = "pub-and-restaurant/pub"
WINDOWS = [[(1416, 158), (1492, 158), (1492, 382), (1416, 382)], [(1610, 92), (1672, 92), (1672, 384), (1610, 384)]]


def _pub():
    """the pub at night, the gig on: the windows dark (lit windows across the street), the room dim and warm with
    its own lamps glowing, the stage's red light spilling over the floor and the booths"""
    big = _x4(PUB).astype(np.float32) / 255.0
    H, W = big.shape[:2]
    s1 = cv2.resize(big, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    lum = s1.max(2)
    # the room's own lights: its brightest warm parts (the lamps, the sconces, the fire)
    warm = ((s1[..., 0] > s1[..., 2] + 0.10) & (lum > 0.80)) | (s1.min(2) > 0.93)     # the bulbs burn white
    warm[540:] = False                                       # the floor's sunlight is not a lamp
    warm = cv2.morphologyEx(warm.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    lamps = cv2.GaussianBlur(cv2.dilate(warm.astype(np.float32), np.ones((3, 3), np.uint8)), (0, 0), 1.5)
    win = np.zeros((H // 4, W // 4), np.float32)
    for poly in WINDOWS:
        cv2.fillPoly(win, [np.int32(poly)], 1.0)
    win = cv2.GaussianBlur(win, (0, 0), 1.0)
    up = lambda m: cv2.resize(m, (W, H), interpolation=cv2.INTER_LINEAR)[..., None]   # noqa: E731
    lamps, win = up(lamps), up(win)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    # no sun on the floor at night: the floor's patches of light flattened into the boards around them
    fl = np.clip((yy - 0.55) / 0.05, 0, 1)
    soft = cv2.resize(cv2.GaussianBlur(s1, (0, 0), 15), (W, H), interpolation=cv2.INTER_LINEAR)
    big = big * (1 - fl) + (soft + 0.35 * (big - soft)) * fl
    # dim and warm, a little brighter low down where the stage light reaches
    room = big * (0.30 + 0.16 * yy) * np.float32([1.0, 0.80, 0.72])
    room += (0.10 * yy ** 1.5) * np.float32([0.85, 0.12, 0.08])                    # the stage's red spill
    out = room * (1 - lamps) + big * np.float32([1.0, 0.93, 0.82]) * lamps
    # night outside: the street dark blue, its white window frames lit warm
    L = big.mean(2, keepdims=True)
    night = L * np.float32([0.10, 0.13, 0.28]) + np.clip(L - 0.82, 0, 1) * 4.0 * np.float32([0.95, 0.70, 0.30])
    out = out * (1 - win) + night * win
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def plate_image(k):
    """F: the front view, empty; FC: the same with the fans in the foreground (both without the mic stand); PUB:
    the back of the pub at night, behind the crowd"""
    if k in ("F", "FC"):
        return _plate(k)
    if k == "PUB":
        cache = ep.path("plate_PUB.png")
        if cache.exists():
            return cv2.cvtColor(cv2.imread(str(cache)), cv2.COLOR_BGR2RGB)
        img = _pub()
        cv2.imwrite(str(cache), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        return img
    return None


@functools.lru_cache(maxsize=2)
def fans_image(k="FC"):
    """the fans in the front of the crowd view (where it differs from the empty view, below the stage), without
    the table among them -> RGBA uint8 at 4x"""
    cache = ep.path("fans_FC.png")
    big = _plate("FC")
    if cache.exists():
        a4 = cv2.imread(str(cache), cv2.IMREAD_GRAYSCALE)
    else:
        f1 = cv2.resize(_plate("F"), None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA).astype(np.float32)
        c1 = cv2.resize(big, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA).astype(np.float32)
        d = np.abs(c1 - f1).max(2)
        d = cv2.GaussianBlur(d, (0, 0), 2.0)
        m = (d > 38).astype(np.uint8)
        H, W = m.shape
        zone = np.zeros_like(m)
        cv2.fillPoly(zone, [np.int32([(0, 640), (300, 655), (560, 650), (560, 941), (0, 941)])], 1)
        cv2.fillPoly(zone, [np.int32([(560, 700), (1100, 690), (1250, 640), (1540, 600), (1540, 505), (1672, 505),
                                      (1672, 941), (560, 941)])], 1)
        m &= zone
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        keep = np.zeros_like(m)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] > 1500 and st[i, cv2.CC_STAT_TOP] + st[i, cv2.CC_STAT_HEIGHT] >= H - 3:
                keep[lab == i] = 1                               # only what reaches the bottom of the frame: people
        # fill holes (between arms and heads)
        inv = 1 - keep
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
        for i in range(1, n2):
            x, y, w, h, a = st2[i]
            if a < 6000 and y > 0 and x > 0 and x + w < W:
                keep[lab2 == i] = 1
        t = np.zeros_like(keep)
        cv2.fillPoly(t, [np.int32(TABLE)], 1)
        keep[t > 0] = 0
        a1 = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.6)
        a4 = (cv2.resize(a1, (big.shape[1], big.shape[0]), interpolation=cv2.INTER_LINEAR) * 255).astype(np.uint8)
        cv2.imwrite(str(cache), a4)
    return np.dstack([big, a4])




# ================================================================ The White Pelé's own sets
import math

from studio.film.engine import OH, OW, RS

PLATE_SRC = {
    "S": "pub-and-restaurant/united-pub-stage-side-crowd",
    "ST": "street/manchester-matchday",
    "OT": "stadiums/old-trafford",
    "MEM": "stadiums/red-seated",
}
# the documentary's Old Trafford exteriors and tunnels (TV-show- repo, manchester-united-documentary/assets/
# backgrounds, copied into library/backgrounds/stadiums/ by this production)
# the upgrade pack's ten empty sets (library/backgrounds/white-pele/), B01..B10, used as drawn (upscaled 4x)
UP = {"B01": "white-pele/bg01-pub-stage-front", "B02": "white-pele/bg02-pub-stage-side",
      "B03": "white-pele/bg03-pub-audience-reverse", "B04": "white-pele/bg04-backstreet-pitch",
      "B05": "white-pele/bg05-pub-street", "B06": "white-pele/bg06-stadium-tunnel", "B07": "white-pele/bg07-pitch-low",
      "B08": "white-pele/bg08-stadium-concert-front", "B09": "white-pele/bg09-stadium-stage-reverse",
      "B10": "white-pele/bg10-rooftop-performance"}
DOC = {"EXT": "stadiums/old-trafford-exterior-dusk", "EXT2": "stadiums/old-trafford-exterior-red-lit",
       "TUN": "stadiums/tunnel-corridor", "TUNP": "stadiums/tunnel-to-pitch"}


def _cached(k, make):
    cache = ep.path(f"plate_{k}.png")
    if cache.exists():
        return cv2.cvtColor(cv2.imread(str(cache)), cv2.COLOR_BGR2RGB)
    img = make()
    cv2.imwrite(str(cache), cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    return img


def _f(img):
    return img.astype(np.float32) / 255.0


def _u8(img):
    return (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)


def sky_mask(big, top=0.62):
    """the sky of a plate (RGB uint8 at 4x): the bright blue-and-white region joined to the top edge"""
    s1 = cv2.resize(big, (big.shape[1] // 4, big.shape[0] // 4), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(s1, cv2.COLOR_RGB2HSV).astype(np.int16)
    blue = (hsv[..., 0] >= 90) & (hsv[..., 0] <= 130) & (hsv[..., 2] > 120)
    white = (hsv[..., 1] < 40) & (hsv[..., 2] > 185)
    m = (blue | white).astype(np.uint8)
    m[int(top * m.shape[0]):] = 0
    n, lab = cv2.connectedComponents(m, connectivity=4)
    keep = np.isin(lab, [k for k in np.unique(lab[0]) if k])
    keep = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)).astype(np.float32)
    keep = cv2.GaussianBlur(keep, (0, 0), 0.8)
    return cv2.resize(keep, (big.shape[1], big.shape[0]), interpolation=cv2.INTER_LINEAR)[..., None]


def lamps_mask(big, warm_only=False):
    """the plate's own lights: its brightest warm or white small blobs"""
    f = _f(big)
    lum = f.max(2)
    m = (lum > 0.9) & ((f[..., 0] > f[..., 2] + 0.05) | (f.min(2) > 0.9))
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)).astype(np.float32)
    return cv2.GaussianBlur(m, (0, 0), 3.0)[..., None]


# ---------------------------------------------------------------- the street at dusk, with bunting
BUNTING = [  # strings across the street (1x plate px): from, to, sag, flag size
    ((455, 118), (1312, 205), 70, 22), ((548, 232), (1240, 300), 46, 16), ((640, 300), (1195, 345), 28, 11),
    ((0, 262), (452, 214), 30, 20)]


def bunting(img, strings, K=4, seed=5):
    """red-and-white pennants on a sagging string, house outline"""
    rng = np.random.default_rng(seed)
    out = img.copy()
    for (x0, y0), (x1, y1), sag, size in strings:
        n = int(math.hypot(x1 - x0, y1 - y0) / (size * 1.25))
        pts = []
        for i in range(n + 1):
            u = i / n
            pts.append((x0 + (x1 - x0) * u, y0 + (y1 - y0) * u + sag * 4 * u * (1 - u)))
        P = np.int32(np.float32(pts) * K)
        cv2.polylines(out, [P], False, (40, 34, 36), max(2, int(0.08 * size * K / 4)), cv2.LINE_AA)
        for i in range(n):
            a, b = np.float32(pts[i]), np.float32(pts[i + 1])
            m = (a + b) / 2
            d = b - a
            nrm = np.float32([-d[1], d[0]]) / (np.linalg.norm(d) + 1e-6)
            if nrm[1] < 0:
                nrm = -nrm
            tip = m + nrm * size * (0.95 + 0.1 * rng.uniform())
            tri = np.int32(np.float32([a + d * 0.06, b - d * 0.06, tip]) * K)
            col = (205, 22, 30) if i % 2 == 0 else (244, 242, 236)
            cv2.fillPoly(out, [tri], col, cv2.LINE_AA)
            cv2.polylines(out, [tri], True, (40, 34, 36), max(2, int(0.06 * size * K / 4)), cv2.LINE_AA)
    return out


def street():
    """the matchday street at dusk: the sky a deep evening blue going warm over the city, the buildings cooler and
    darker, the cafe windows, the street lamp and the stadium glowing; bunting across the road"""
    big = _x4(PLATE_SRC["ST"])
    sky = sky_mask(big, 0.45)
    f = _f(big)
    H, W = f.shape[:2]
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    dusk = (np.float32([0.10, 0.13, 0.32]) * (1 - yy * 1.6) + np.float32([0.95, 0.52, 0.30]) * np.clip(yy * 2.2 - 0.25, 0, 1))
    clouds = (f.mean(2, keepdims=True) - 0.7) * 0.5
    sky_col = np.clip(dusk + clouds * np.float32([0.6, 0.45, 0.5]), 0, 1)
    lit = lamps_mask(big)
    cool = f * np.float32([0.62, 0.66, 0.84]) * 0.92
    out = cool * (1 - sky) + sky_col * sky
    win = (f[..., 0:1] > 0.75) & (f[..., 1:2] > 0.55) & (f[..., 2:3] < 0.55)      # the cafe's warm lit windows
    win = cv2.GaussianBlur(win.astype(np.float32)[..., 0], (0, 0), 2.0)[..., None]
    out = out * (1 - np.clip(lit + win, 0, 1)) + f * np.float32([1.05, 0.95, 0.80]) * np.clip(lit + win, 0, 1)
    # the floodlights of the stadium in the distance (its roof truss), and their glow in the sky
    glow = np.zeros((H, W), np.float32)
    cv2.ellipse(glow, (int(900 * 4), int(285 * 4)), (int(240 * 4), int(80 * 4)), 0, 0, 360, 1.0, -1)
    glow = cv2.GaussianBlur(glow, (0, 0), 60)[..., None]
    out = out + glow * 0.35 * np.float32([1.0, 0.85, 0.7]) * sky + glow * 0.12
    return bunting(_u8(out), BUNTING)


# ---------------------------------------------------------------- the mural wall (drawn)
def mural_wall():
    """an empty brick gable on the same street at dusk, for the White Pele mural: bricks in courses with mortar, a
    painted red-and-white field for the lettering (the lettering itself is drawn live, mural_text), a stone sill,
    the pavement and kerb at its foot, a down-pipe; the house outline throughout. 1672 x 941 at 4x"""
    K = 4
    W, H = 1672 * K, 941 * K
    img = np.zeros((H, W, 3), np.uint8)
    rng = np.random.default_rng(23)
    base = np.float32([170, 74, 50])
    bh, bw = 22 * K, 62 * K
    ground = 760 * K
    img[:] = (92, 46, 38)                                          # mortar
    for r in range(0, ground // bh + 1):
        y0 = r * bh
        off = (r % 2) * bw // 2
        for c in range(-1, W // bw + 2):
            x0 = c * bw - off
            v = rng.uniform(-0.12, 0.12)
            col = np.clip(base * (1 + v) + rng.uniform(-6, 6, 3), 0, 255)
            cv2.rectangle(img, (x0 + 3 * K // 2, y0 + 3 * K // 2), (x0 + bw - 3 * K // 2, y0 + bh - 3 * K // 2),
                          tuple(int(x) for x in col), -1)
            cv2.line(img, (x0 + 2 * K, y0 + 2 * K + 1), (x0 + bw - 3 * K, y0 + 2 * K + 1),
                     tuple(int(min(255, x * 1.12)) for x in col), K)
    # the painted field: a red panel with a white border and black trim, slightly weathered
    fx0, fy0, fx1, fy1 = 300 * K, 90 * K, 1372 * K, 560 * K
    panel = img.copy()
    cv2.rectangle(panel, (fx0, fy0), (fx1, fy1), (24, 20, 22), -1)
    cv2.rectangle(panel, (fx0 + 14 * K, fy0 + 14 * K), (fx1 - 14 * K, fy1 - 14 * K), (244, 240, 232), -1)
    cv2.rectangle(panel, (fx0 + 30 * K, fy0 + 30 * K), (fx1 - 30 * K, fy1 - 30 * K), (200, 20, 30), -1)
    for k in range(9):                                             # painted stars
        cx, cy = fx0 + (60 + 120 * k) * K, fy1 - 60 * K
        pts = [(cx + (14 if j % 2 == 0 else 6) * K * math.sin(j * math.pi / 5),
                cy - (14 if j % 2 == 0 else 6) * K * math.cos(j * math.pi / 5)) for j in range(10)]
        cv2.fillPoly(panel, [np.int32(pts)], (250, 214, 60), cv2.LINE_AA)
    # the bricks show through the paint a little: mortar lines darken it
    mortar = (img.astype(np.int16).sum(2) < 200).astype(np.float32)
    panel = (panel.astype(np.float32) * (1 - 0.25 * mortar[..., None])).astype(np.uint8)
    img = panel
    cv2.rectangle(img, (fx0, fy0), (fx1, fy1), (22, 18, 20), 3 * K)
    # a down-pipe
    cv2.rectangle(img, (1500 * K, 0), (1522 * K, ground), (40, 44, 46), -1)
    cv2.rectangle(img, (1500 * K, 0), (1522 * K, ground), (16, 14, 16), 2 * K)
    for y in range(60, 760, 140):
        cv2.rectangle(img, (1494 * K, y * K), (1528 * K, (y + 10) * K), (30, 32, 34), -1)
    # pavement and kerb, the road beyond
    cv2.rectangle(img, (0, ground), (W, 900 * K), (178, 170, 160), -1)
    for x in range(0, 1672, 120):
        cv2.line(img, (x * K, ground), ((x - 60) * K, 900 * K), (140, 132, 124), K)
    cv2.line(img, (0, (ground + 900 * K) // 2), (W, (ground + 900 * K) // 2), (140, 132, 124), K)
    cv2.rectangle(img, (0, 900 * K), (W, H), (78, 78, 84), -1)
    cv2.rectangle(img, (0, 892 * K), (W, 904 * K), (200, 194, 186), -1)
    cv2.line(img, (0, ground), (W, ground), (22, 18, 20), 3 * K)
    cv2.line(img, (0, 900 * K), (W, 900 * K), (22, 18, 20), 2 * K)
    # dusk: cooler, a lamp's warm pool from the left, darker towards the top
    f = _f(img)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    xx = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
    light = 0.55 + 0.35 * yy + 0.25 * np.exp(-((xx - 0.15) ** 2 + (yy - 0.55) ** 2) / 0.08)
    f = f * light * np.float32([0.92, 0.88, 0.98])
    return _u8(f)


# ---------------------------------------------------------------- Old Trafford at night, and its stage
def ot_night():
    """the stadium under the floodlights: the sky a night blue with the lights' haze rising into it, the stands
    and the pitch lit hard and white from above, the roof lights burning"""
    big = _x4(PLATE_SRC["OT"])
    sky = sky_mask(big, 0.4)
    f = _f(big)
    H, W = f.shape[:2]
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    night = np.float32([0.03, 0.04, 0.10]) + np.float32([0.10, 0.10, 0.18]) * np.clip(yy * 3.0, 0, 1)
    clouds = np.clip(f.mean(2, keepdims=True) - 0.75, 0, 1) * np.float32([0.25, 0.25, 0.32])
    lit = lamps_mask(big) * (1 - sky)                     # (white clouds are not lamps)
    out = f * np.float32([0.86, 0.86, 0.92])
    out = out * (1 - sky) + (night + clouds) * sky
    out = out * (1 - lit) + np.clip(f * 1.25, 0, 1) * lit
    haze = cv2.GaussianBlur(lit[..., 0], (0, 0), 90)[..., None]
    out = out + haze * 2.2 * np.float32([0.9, 0.92, 1.0]) * (0.4 + 0.6 * sky)
    return _u8(out)


STAGE_DECK = (470, 640, 1200, 704)            # the performance stage on the pitch (1x px): x0, deck top y, x1, front y


def stage_platform(img, K=4):
    """the compact stage built on the pitch: a black deck with a lit red front and a strip of LEDs, steps, a truss
    tower each side with a roof truss between them, lamp cans hung on it (their beams are LAMPS in direction.py)"""
    x0, ytop, x1, yfront = STAGE_DECK
    out = img.copy()
    deck = np.int32(np.float32([(x0 + 26, ytop), (x1 - 26, ytop), (x1, yfront), (x0, yfront)]) * K)
    cv2.fillPoly(out, [deck], (34, 30, 34), cv2.LINE_AA)
    front = np.int32(np.float32([(x0, yfront), (x1, yfront), (x1, yfront + 46), (x0, yfront + 46)]) * K)
    cv2.fillPoly(out, [front], (120, 14, 22), cv2.LINE_AA)
    for k in range(int((x1 - x0) / 9)):                           # the LED strip
        x = x0 + 5 + k * 9
        cv2.circle(out, (int(x * K), int((yfront + 8) * K)), int(1.6 * K), (255, 236, 220), -1, cv2.LINE_AA)
    cv2.polylines(out, [deck], True, (16, 14, 16), 2 * K, cv2.LINE_AA)
    cv2.polylines(out, [front], True, (16, 14, 16), 2 * K, cv2.LINE_AA)
    def truss(xa, ya, xb, yb, w):
        d = np.float32([xb - xa, yb - ya])
        L = float(np.linalg.norm(d))
        u = d / L
        n = np.float32([-u[1], u[0]]) * w / 2
        A, B = np.float32([xa, ya]), np.float32([xb, yb])
        for s_ in (-1, 1):
            cv2.line(out, tuple(np.int32((A + s_ * n) * K)), tuple(np.int32((B + s_ * n) * K)), (168, 172, 180), int(1.6 * K), cv2.LINE_AA)
        k = 0
        while k * w < L:
            p = A + u * k * w
            q = A + u * min(L, (k + 1) * w)
            cv2.line(out, tuple(np.int32((p - n) * K)), tuple(np.int32((q + n) * K)), (140, 144, 152), int(1.0 * K), cv2.LINE_AA)
            cv2.line(out, tuple(np.int32((p + n) * K)), tuple(np.int32((p - n) * K)), (140, 144, 152), int(1.0 * K), cv2.LINE_AA)
            k += 1
    # the LED wall behind the band, between the towers: dark, a red glow rising from the stage, a grid of pixels,
    # a white rim of light round it (the performers always have the stage behind them, never the pitch)
    wx0, wx1, wy0, wy1 = x0 + 12, x1 - 12, 312, ytop + 4
    W_, H_ = int((wx1 - wx0) * K), int((wy1 - wy0) * K)
    yy = np.linspace(0, 1, H_, dtype=np.float32)[:, None]
    xx = np.linspace(-1, 1, W_, dtype=np.float32)[None, :]
    glow = np.exp(-((xx / 0.75) ** 2 + ((1 - yy) / 0.65) ** 2))
    wall = np.zeros((H_, W_, 3), np.float32)
    wall[:] = (16, 12, 18)
    wall += glow[..., None] * np.float32([150, 18, 30])
    ring = np.exp(-((np.sqrt((xx / 0.42) ** 2 + ((yy - 0.48) / 0.62) ** 2) - 1.0) / 0.05) ** 2)
    wall += ring[..., None] * np.float32([90, 70, 70])
    dots = ((np.arange(W_)[None, :] % (3 * K)) < K) & ((np.arange(H_)[:, None] % (3 * K)) < K)
    wall *= np.where(dots[..., None], 1.0, 0.72)
    out[int(wy0 * K):int(wy0 * K) + H_, int(wx0 * K):int(wx0 * K) + W_] = np.clip(wall, 0, 255).astype(np.uint8)
    cv2.rectangle(out, (int(wx0 * K), int(wy0 * K)), (int(wx1 * K), int(wy1 * K)), (16, 14, 16), 2 * K)
    cv2.polylines(out, [deck], True, (16, 14, 16), 2 * K, cv2.LINE_AA)
    truss(x0 + 20, ytop + 6, x0 + 20, 300, 22)
    truss(x1 - 20, ytop + 6, x1 - 20, 300, 22)
    truss(x0 + 8, 300, x1 - 8, 300, 22)
    for k in range(7):                                            # lamp cans
        x = x0 + 70 + k * (x1 - x0 - 140) / 6
        cv2.rectangle(out, (int((x - 9) * K), int(312 * K)), (int((x + 9) * K), int(334 * K)), (28, 26, 30), -1)
        cv2.circle(out, (int(x * K), int(334 * K)), int(7 * K), (255, 246, 230), -1, cv2.LINE_AA)
    return out


# ---------------------------------------------------------------- the football memory's stadium (day)
def memory():
    """a sunlit afternoon at the ground, warmer and a touch hazier than the present (the nostalgia is in the light,
    not a change of style)"""
    f = _f(_x4(PLATE_SRC["MEM"]))
    f = f * np.float32([1.06, 0.98, 0.84]) + np.float32([0.05, 0.03, 0.0])
    lum = f.mean(2, keepdims=True)
    f = lum + (f - lum) * 0.92
    return _u8(f)


# ---------------------------------------------------------------- crowds in the stands
CROWD_ZONES = {
    # plate: [(polygon in 1x px where the seats are, head radius at the polygon's top, at its bottom)]
    "OT": [([(0, 300), (350, 300), (350, 410), (0, 400)], 2.6, 3.4),
           ([(350, 318), (1310, 318), (1310, 420), (350, 420)], 2.6, 3.3),
           ([(1310, 300), (1672, 300), (1672, 400), (1310, 410)], 2.6, 3.4),
           ([(0, 428), (1672, 428), (1672, 548), (0, 548)], 3.4, 4.6)],
    "MEM": [([(0, 60), (1672, 60), (1672, 420), (0, 420)], 2.4, 4.4),
            ([(0, 430), (1672, 430), (1672, 560), (0, 560)], 4.4, 5.4)],
    # the upgrade pack's stadium sets: their seats are empty, so they are filled the same way
    "B07": [([(0, 170), (1672, 170), (1672, 420), (0, 420)], 2.4, 3.6),
            ([(0, 420), (1672, 420), (1672, 650), (0, 650)], 3.6, 5.6)],
    "B08": [([(0, 140), (1672, 140), (1672, 330), (0, 330)], 2.2, 3.0),
            ([(0, 330), (1672, 330), (1672, 565), (0, 565)], 3.0, 4.0)],
    "B09": [([(60, 220), (1610, 220), (1610, 400), (60, 400)], 2.4, 3.2),
            ([(30, 400), (1640, 400), (1640, 540), (30, 540)], 3.2, 4.2),
            ([(20, 540), (1650, 540), (1650, 700), (20, 700)], 4.2, 6.0)],
}
SHIRTS = [(206, 20, 30)] * 6 + [(240, 238, 232)] * 2 + [(28, 24, 26)] * 2 + [(30, 50, 140), (230, 200, 40)]
SKIN = [(246, 200, 168), (224, 168, 128), (190, 130, 90), (140, 92, 60), (98, 64, 44)]
HAIR = [(40, 30, 26), (90, 60, 36), (20, 18, 18), (150, 110, 60), (200, 170, 110)]


SEAT_DARK = {"B08": 28, "B09": 40}          # night sets: seats in shadow still count as seats
SEAT_NOT = {"B08": [(110, 40, 385, 660), (1290, 40, 1560, 660)]}    # its truss towers and speaker stacks (1x px)


def seat_mask(big, poly, K=4, dark=70):
    """the seats inside a zone (red, or the empty grey of a stand) at 4x"""
    m = np.zeros(big.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.int32(np.float32(poly) * K)], 1)
    hsv = cv2.cvtColor(big, cv2.COLOR_RGB2HSV)
    red = ((hsv[..., 0] < 10) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 90) & (hsv[..., 2] > dark)
    return (m > 0) & red


def crowd_layer(k, up):
    """the crowd for plate k as an RGBA layer at 4x (cached): people in rows on the seats, heads and shoulders,
    each a shirt, a skin tone and a head of hair; `up`: their scarves held up over their heads"""
    cache = ep.path(f"crowd_{k}_{int(up)}.png")
    if cache.exists():
        im = cv2.imread(str(cache), cv2.IMREAD_UNCHANGED)
        return cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA)
    K = 4
    base = _x4(PLATE_SRC[k] if k in PLATE_SRC else UP[k])
    H, W = base.shape[:2]
    lay = np.zeros((H, W, 4), np.uint8)
    rng = np.random.default_rng(31)
    for poly, r0, r1 in CROWD_ZONES[k]:
        seats = seat_mask(base, poly, dark=SEAT_DARK.get(k, 70))
        for x0, y0, x1, y1 in SEAT_NOT.get(k, ()):
            seats[y0 * K:y1 * K, x0 * K:x1 * K] = False
        ys = [p[1] for p in poly]
        top, bot = min(ys), max(ys)
        y = float(top)
        row = 0
        while y < bot:
            r = r0 + (r1 - r0) * (y - top) / max(1, bot - top)
            x = rng.uniform(0, 2 * r)
            while x < W / K:
                X, Y = int(x * K), int(y * K)
                if 0 <= Y < H and 0 <= X < W and seats[Y, X]:
                    rr = r * rng.uniform(0.9, 1.1)
                    sh = SHIRTS[rng.integers(len(SHIRTS))]
                    sk = SKIN[rng.integers(len(SKIN))]
                    hr = HAIR[rng.integers(len(HAIR))]
                    cy = Y + int(rng.uniform(-0.3, 0.3) * rr * K)
                    cv2.ellipse(lay, (X, cy + int(1.6 * rr * K)), (int(1.25 * rr * K), int(1.0 * rr * K)), 0, 180, 360,
                                (*sh, 255), -1, cv2.LINE_AA)
                    cv2.circle(lay, (X, cy), int(rr * K), (*sk, 255), -1, cv2.LINE_AA)
                    cv2.ellipse(lay, (X, cy - int(0.15 * rr * K)), (int(rr * K), int(0.8 * rr * K)), 0, 180, 360,
                                (*hr, 255), -1, cv2.LINE_AA)
                    cv2.circle(lay, (X, cy), int(rr * K), (30, 24, 26, 255), max(1, int(0.18 * rr * K)), cv2.LINE_AA)
                    if up and rng.uniform() < 0.62:                    # a scarf held up, arms to its ends
                        sw, shh = int(2.6 * rr * K), max(2, int(0.55 * rr * K))
                        sy = cy - int(1.7 * rr * K)
                        cols = [(206, 20, 30), (244, 242, 236), (24, 20, 22)]
                        nseg = 5
                        for j in range(nseg):
                            xa = X - sw // 2 + j * sw // nseg
                            cv2.rectangle(lay, (xa, sy), (xa + sw // nseg, sy + shh), (*cols[(j + row) % 3], 255), -1)
                        cv2.rectangle(lay, (X - sw // 2, sy), (X + sw // 2, sy + shh), (30, 24, 26, 255),
                                      max(1, int(0.12 * rr * K)))
                        for s_ in (-1, 1):
                            cv2.line(lay, (X + s_ * int(0.8 * rr * K), cy + int(0.8 * rr * K)),
                                     (X + s_ * sw // 2, sy + shh), (*sk, 255), max(1, int(0.35 * rr * K)), cv2.LINE_AA)
                x += 2.2 * r * rng.uniform(0.9, 1.15)
            y += 2.5 * r
            row += 1
    cv2.imwrite(str(cache), cv2.cvtColor(lay, cv2.COLOR_RGBA2BGRA))
    return lay


def _crowd_view(k, up, M):
    """the crowd layer through the plate's camera (M: 1x plate px -> screen), premultiplied float RGBA"""
    lay = crowd_layer(k, up)
    A = np.float32(M).copy()
    A[:, :2] /= 4.0
    v = cv2.warpAffine(lay, A, (OW, OH), flags=cv2.INTER_AREA if A[0, 0] < 1 else cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_CONSTANT).astype(np.float32) / 255.0
    v[..., :3] *= v[..., 3:4]
    return v


def stands(img, s, t, M, sc):
    """the crowd in the stands: everyone bouncing on the beat (each column of people its own phase and height, so
    no two neighbours move together), lit by the floodlights (dimmed at night); a scarf wave runs round the ground
    when the shot asks (s["wave"]: (t0, t1)) and scarves go up all together for s["scarves"] spans"""
    from studio.film.stage import SONG
    k = s["plate"] if s["plate"] in CROWD_ZONES else "OT"
    S = SONG()
    down = _crowd_view(k, False, M)
    upl = _crowd_view(k, True, M)
    X = np.arange(OW, dtype=np.float32) / RS
    mix = np.zeros(OW, np.float32)
    for a, b in s.get("scarves", ()):
        mix = np.maximum(mix, float(np.clip(min((t - a) / 0.4, (b - t) / 0.4), 0, 1)))
    if s.get("wave"):
        a, b = s["wave"]
        if a <= t <= b:
            front = (t - a) / (b - a) * (1920 + 900) - 450              # the wave's crest crossing the frame
            mix = np.maximum(mix, np.clip(1 - np.abs(X - front) / 420.0, 0, 1) ** 0.7)
    layer = down * (1 - mix[None, :, None]) + upl * mix[None, :, None]
    # bounce: a column's people jump on the beat with their own phase
    energy = s.get("energy", S.energy(t))
    amp = s.get("crowd_jump", 1.0) * (1.5 + 3.5 * energy) * RS * max(0.4, sc / (OW / 1672.0))
    ph = S.phase(t)
    col = (np.sin(X * 0.11) * 0.5 + np.sin(X * 0.037 + 1.3) * 0.5)
    dy = -amp * np.maximum(0, np.sin(math.pi * ((ph + 0.35 * col) % 1.0))) ** 1.5
    mapx, mapy = np.meshgrid(np.arange(OW, dtype=np.float32), np.arange(OH, dtype=np.float32))
    layer = cv2.remap(layer, mapx, mapy - dy[None, :], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    tone = s.get("crowd_tone", 1.0 if k == "MEM" else 0.82)
    layer[..., :3] *= tone
    if s.get("blur", 0) > 0:                       # in the shot's depth of field, as the plate behind it is
        layer = cv2.GaussianBlur(layer, (0, 0), s["blur"] * RS)
    return img * (1 - layer[..., 3:4]) + layer[..., :3]


# ---------------------------------------------------------------- every plate
def plate_image(k):
    if k in ("F", "FC"):
        return _plate(k)
    if k == "PUB":
        return _cached("PUB", _pub)
    if k == "S":
        return _cached("S", lambda: _x4(PLATE_SRC["S"]))
    if k == "ST":
        return _cached("ST", street)
    if k == "MW":
        return _cached("MW", mural_wall)
    if k == "OT":
        return _cached("OT", ot_night)
    if k == "OTS":
        return _cached("OTS", lambda: stage_platform(plate_image("OT")))
    if k == "MEM":
        return _cached("MEM", memory)
    if k in DOC:
        return _cached(k, lambda: _x4(DOC[k]))
    if k in UP:
        return _cached(k, lambda: _x4(UP[k]))
    return None


# ---------------------------------------------------------------- props in hands
def _paste(lay, img_rgba, A):
    """warp an RGBA uint8 prop into a premultiplied float layer through A (2x3: prop px -> screen px), over"""
    src = img_rgba.astype(np.float32) / 255.0
    src[..., :3] *= src[..., 3:4]
    w = cv2.warpAffine(src, np.float32(A), (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    lay[:] = w + lay * (1 - w[..., 3:4])


def prop_image(name, size_px):
    """(RGBA uint8, grip (x, y)) of a prop drawn about size_px tall"""
    from film import things as T
    if name == "trophy":
        return T.trophy(max(16, int(size_px)))
    if name == "broom":
        return T.broom(max(40, int(size_px)))
    if name == "football":
        im = T.football()
        return im, (im.shape[1] / 2, im.shape[0] / 2)
    if name == "mic":
        im = T.microphone()
        return im, (im.shape[1] / 2, im.shape[0] * 0.62)
    raise KeyError(name)


def hold(lay, item, Ms2, t, a):
    """a prop in an actor's hand: item = dict(prop, at=(x, y) sheet px of the grip, deg, size (sheet px tall),
    [to=(x, y)] for a scarf held between two hands, [wobble] degrees of a nervous wobble (the trophy))"""
    from film import things as T
    from studio.film.stage import apply
    k = math.sqrt(abs(Ms2[0, 0] * Ms2[1, 1] - Ms2[0, 1] * Ms2[1, 0]))
    mir = Ms2[0, 0] < 0
    if item["prop"] == "scarf":                         # stretched between two fists, the cloth rippling
        p0, p1 = np.float32(apply(Ms2, *item["at"])), np.float32(apply(Ms2, *item["to"]))
        L = float(np.linalg.norm(p1 - p0))
        if L < 4:
            return
        h = max(4, int(item["size"] * k))
        cloth = T.scarf_cloth(item.get("kind", "bars"), max(8, int(L * 1.1)), h)
        H2, W2 = cloth.shape[:2]
        pad = int(h * 1.2)
        big = np.zeros((H2 + 2 * pad, W2, 4), np.uint8)
        big[pad:pad + H2] = cloth
        xs = np.arange(W2, dtype=np.float32)
        u = xs / W2
        sag = item.get("sag", 0.18) * h * 4 * u * (1 - u)
        wave = 0.22 * h * np.sin(6.28 * (u * 1.6 - 1.8 * t)) * (4 * u * (1 - u))
        Y, Xg = np.mgrid[0:big.shape[0], 0:W2].astype(np.float32)
        big = cv2.remap(big, Xg, Y - (sag + wave)[None, :], cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        d = (p1 - p0) / L
        n = np.float32([-d[1], d[0]])
        sx = L / (W2 * 0.92)
        A = np.float32([[d[0] * sx, n[0], 0], [d[1] * sx, n[1], 0]])
        c0 = np.float32([W2 * 0.04, pad + H2 / 2])
        A[:, 2] = p0 - A[:, :2] @ c0
        _paste(lay, big, A)
        return
    if item["prop"].startswith("cut:"):                # a prop cut from this drawing (tools/make_art.py): same px
        img, grip = cut_prop(item["prop"][4:])
        s_ = k
    else:
        img, grip = prop_image(item["prop"], item["size"] * k * (4 if item["prop"] in ("trophy", "broom") else 1))
        if item["prop"] in ("football", "mic"):
            s_ = item["size"] * k / img.shape[0]
        else:
            s_ = 0.25
    deg = item.get("deg", 0.0) + item.get("wobble", 0.0) * math.sin(t * 9.0)
    if item.get("sweep"):                               # a broom swept to and fro: (degrees, strokes a second, from)
        amp, hz, t0 = item["sweep"]
        if t >= t0:
            deg += amp * math.sin(2 * math.pi * hz * (t - t0)) * min(1.0, (t - t0) / 0.25)
    if mir:
        img = img[:, ::-1]
        grip = (img.shape[1] - grip[0], grip[1])
        deg = -deg
    th = math.radians(deg)
    c, s2 = math.cos(th) * s_, math.sin(th) * s_
    gx, gy = apply(Ms2, *item["at"])
    A = np.float32([[c, -s2, 0], [s2, c, 0]])
    A[:, 2] = np.float32([gx, gy]) - A[:, :2] @ np.float32(grip)
    _paste(lay, img, A)


@functools.lru_cache(maxsize=4)
def cut_prop(name):
    """(RGBA uint8, grip) of a prop cut out of a character drawing by tools/make_art.py (cut-props.json)"""
    import json
    from studio.paths import CHARACTERS
    meta = json.loads((CHARACTERS / "roy-keane" / "reference" / "upgrade" / "cut-props.json").read_text())[name]
    im = np.asarray(Image.open(CHARACTERS / meta["image"]).convert("RGBA"))
    return im, tuple(meta["grip"])


# ---------------------------------------------------------------- the ball
def ball_state(spec, t):
    """where the ball is: spec = dict(keys=[(t, x, y)] plate px, r plate px, floor=y (its shadow), spin=1).
    Between keys it moves straight (a roll) or in a parabola (an arc: the key has a fourth value, the height)"""
    ks = spec["keys"]
    if t <= ks[0][0]:
        x, y = ks[0][1], ks[0][2]
        return x, y, 0.0
    dist = 0.0
    for i, (k0, k1) in enumerate(zip(ks, ks[1:])):
        t0, x0, y0 = k0[:3]
        t1, x1, y1 = k1[:3]
        seg = math.hypot(x1 - x0, y1 - y0)
        if t < t1:
            u = (t - t0) / max(1e-6, t1 - t0)
            ease = k1[4] if len(k1) > 4 else "lin"
            if ease == "out":                              # rolling to a stop
                u = 1 - (1 - u) ** 2
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * u
            lift = (k1[3] if len(k1) > 3 else 0.0) * 4 * u * (1 - u)
            return x, y - lift, dist + seg * u
        dist += seg
    return ks[-1][1], ks[-1][2], dist


def ball(img, s, t, M, sc):
    """the football: rolling, bouncing or flying along its keys, turning as it travels, with its contact shadow on
    the floor (darker and smaller as it touches down)"""
    from film import things as T
    spec = s.get("ball")
    if not spec or not (spec.get("t0", -1e9) <= t <= spec.get("t1", 1e9)):
        return img
    x, y, d = ball_state(spec, t)
    r = spec["r"]
    floor = spec.get("floor", y)
    X, Y = M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]
    R = r * sc
    lay = np.zeros((OH, OW, 4), np.float32)
    h = max(0.0, floor - y) / max(1e-3, r)
    fy = M[1, 1] * floor + M[1, 2]
    sh = np.zeros((OH, OW), np.float32)
    cv2.ellipse(sh, (int(X), int(fy + 0.1 * R)), (max(1, int(R * (1.0 - 0.08 * min(h, 6)))), max(1, int(R * 0.28))),
                0, 0, 360, 1.0, -1, cv2.LINE_AA)
    sh = cv2.GaussianBlur(sh, (0, 0), max(1.0, R * 0.25)) * (0.45 / (1 + 0.4 * h))
    img = img * (1 - sh[..., None])
    im = T.football()
    ang = -math.degrees(d / max(1e-3, r)) * spec.get("spin", 1.0)
    A = cv2.getRotationMatrix2D((im.shape[1] / 2, im.shape[0] / 2), ang, 2 * R / im.shape[0])
    A[:, 2] += np.float32([X - im.shape[1] / 2, Y - im.shape[0] / 2])
    _paste(lay, im, A)
    if spec.get("blur_v"):                                    # a struck ball: a streak behind it
        v = spec["blur_v"]
        k = max(3, int(abs(v) * RS)) | 1
        ker = np.zeros((k, k), np.float32)
        ker[k // 2, :] = 1.0 / k
        lay = cv2.filter2D(lay, -1, ker)
    return img * (1 - lay[..., 3:4]) + lay[..., :3]


# ---------------------------------------------------------------- typography (editable: the words live here)
MURAL_TEXT = ("THE WHITE", "PELÉ")
SIGN_TEXT = "SIR MATT BUSBY WAY"
MURAL_BOX = (340, 125, 1332, 520)            # MW plate px: where the lettering is painted
SIGN_BOX = ((402, 400), (520, 386), (520, 414), (402, 428))   # ST plate px: the street sign on the corner house


@functools.lru_cache(maxsize=2)
def mural_lettering(w, h):
    """THE WHITE / PELÉ as a painted mural: white letters with a black outline and a red-black drop shadow, at
    w x h px (RGBA float premultiplied)"""
    from PIL import Image as I, ImageDraw, ImageFont
    from studio.film.graphics import BEBAS
    im = I.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sizes = (int(h * 0.36), int(h * 0.58))
    ys = (int(h * 0.04), int(h * 0.38))
    for line, size, y in zip(MURAL_TEXT, sizes, ys):
        f = ImageFont.truetype(BEBAS, size)
        bx = d.textbbox((0, 0), line, font=f)
        x = (w - (bx[2] - bx[0])) / 2 - bx[0]
        sw = max(2, size // 22)
        d.text((x + size * 0.05, y + size * 0.05), line, font=f, fill=(20, 16, 18, 235), stroke_width=sw,
               stroke_fill=(20, 16, 18, 235))
        d.text((x, y), line, font=f, fill=(250, 248, 240, 255), stroke_width=sw, stroke_fill=(20, 16, 18, 255))
    a = np.asarray(im).astype(np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a


def mural_text(img, s, t, M, sc):
    x0, y0, x1, y1 = MURAL_BOX
    W, H = int((x1 - x0) * 2), int((y1 - y0) * 2)
    lay = mural_lettering(W, H)
    A = np.float32([[M[0, 0] / 2, 0, M[0, 0] * x0 + M[0, 2]], [0, M[1, 1] / 2, M[1, 1] * y0 + M[1, 2]]])
    w = cv2.warpAffine(lay, A, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    w[..., :3] *= 0.86                                          # paint on brick at dusk, not a glowing sign
    return img * (1 - w[..., 3:4]) + w[..., :3]


@functools.lru_cache(maxsize=1)
def sign_face():
    from PIL import Image as I, ImageDraw, ImageFont
    from studio.film.graphics import BEBAS
    w, h = 640, 120
    im = I.new("RGBA", (w, h), (246, 244, 238, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], outline=(20, 16, 18, 255), width=8)
    d.rectangle([10, 10, w - 11, h - 11], outline=(200, 20, 30, 255), width=6)
    f = ImageFont.truetype(BEBAS, 84)
    bx = d.textbbox((0, 0), SIGN_TEXT, font=f)
    d.text(((w - (bx[2] - bx[0])) / 2 - bx[0], (h - (bx[3] - bx[1])) / 2 - bx[1]), SIGN_TEXT, font=f,
           fill=(20, 16, 18, 255))
    a = np.asarray(im).astype(np.float32) / 255.0
    a[..., :3] *= a[..., 3:4]
    return a


def street_sign(img, s, t, M, sc):
    face = sign_face()
    h, w = face.shape[:2]
    dst = np.float32([[M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]] for x, y in SIGN_BOX[:3]])
    A = cv2.getAffineTransform(np.float32([[0, 0], [w, 0], [w, h]]), dst)
    wv = cv2.warpAffine(face, A, (OW, OH), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT)
    wv[..., :3] *= 0.8
    return img * (1 - wv[..., 3:4]) + wv[..., :3]


# ---------------------------------------------------------------- the drum kit, for stages other than the pub's
@functools.lru_cache(maxsize=1)
def kit_sprite():
    """the pub stage's drum kit cut from its plate (United Road's kit polygons): RGBA float premultiplied at 4x, and
    its top-left corner in 1x px of the pub plate"""
    from film.direction import KIT
    big = _plate("F")
    m = np.zeros(big.shape[:2], np.uint8)
    for poly in KIT:
        cv2.fillPoly(m, [np.int32(np.float32(poly) * 4)], 255, cv2.LINE_AA)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    ys, xs = np.nonzero(m > 8)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    rgba = np.dstack([big[y0:y1, x0:x1], m[y0:y1, x0:x1]]).astype(np.float32) / 255.0
    rgba[..., :3] *= rgba[..., 3:4]
    return rgba, (x0 / 4.0, y0 / 4.0)


def drum_kit(lay, a, M, sc):
    """the kit in front of the drummer wherever he sits: placed as it stood relative to him on the pub stage
    (Maguire at (880, 516), h 322), lit like the stage it is on"""
    spr, (kx, ky) = kit_sprite()
    k = a["h"] / 322.0
    fx, fy = a["feet"]
    x = fx + (kx - 880) * k
    y = fy + (ky - 516) * k
    s = sc * k / 4.0
    A = np.float32([[s, 0, M[0, 0] * x + M[0, 2]], [0, s, M[1, 1] * y + M[1, 2]]])
    w = cv2.warpAffine(spr, A, (OW, OH), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR,
                       borderMode=cv2.BORDER_CONSTANT)
    w[..., :3] *= a.get("kit_tone", 0.85)
    lay[:] = w + lay * (1 - w[..., 3:4])


# ---------------------------------------------------------------- the ball in screen space, and the dribble
def ball_screen(img, s, t, M, sc):
    """the ball in a shot whose actors are placed in screen px (the memory): keys in 1920 x 1080 layout px"""
    spec = s.get("ball_screen")
    if not spec:
        return img
    Mi = np.float32([[RS, 0, 0], [0, RS, 0]])
    return ball(img, dict(ball=spec), t, Mi, RS)


def dribble(img, s, t, M, sc):
    """the ball at his feet as he runs: pushed ahead on every other step and running on, caught up with; its spin
    from the distance it rolls (screen px)"""
    from studio.film.stage import SONG
    from film.actors import resolve
    kid = next(a for k, v in s["layers"] if k == "actors" for a in v if a["who"] == "kid")
    x, y = resolve(kid, t)["feet"]
    S = SONG()
    beats = S.beat_index(t) + S.phase(t)
    u = beats % 1.0                                              # a touch on every beat
    if not kid.get("screen"):                                    # on a plate: everything in proportion to him
        k = kid["h"] / 700.0
        d = -1 if kid.get("mirror") else 1
        ahead = (70 + 120 * (1 - (1 - u) ** 2) - 40 * u) * k * d
        r = 0.0625 * kid["h"]
        spec = dict(keys=[(t - 1, x + ahead - 200 * k * d, y - r), (t, x + ahead, y - r)], r=r, floor=y)
        return ball(img, dict(ball=spec), t, M, sc)
    ahead = 70 + 120 * (1 - (1 - u) ** 2) - 40 * u
    r = 30
    spec = dict(keys=[(t - 1, x + ahead - 200, y - r), (t, x + ahead, y - r)], r=r, floor=y)
    return ball_screen(img, dict(ball_screen=spec), t, M, sc)


# ---------------------------------------------------------------- the goal: the ball into the net, the net bulging
def goal_net(img, s, t, M, sc):
    net = s["net"]
    gx, gy = net["at"]
    tn = net["t"]
    if t < tn:                                                   # the ball arrives from the right, dipping in
        u = 1 - max(0.0, (tn - t) / 0.33)
        x = gx + 160 * (1 - u)
        y = gy - 22 - 40 * u * (1 - u) + 6 * u
        spec = dict(keys=[(t - 1, x + 60, y), (t, x, y)], r=2.4, floor=gy + 14, blur_v=18)
        return ball(img, dict(ball=spec), t, M, sc)
    # the net bulges back and shivers; the ball drops inside it
    k = t - tn
    amp = 9.0 * math.exp(-k / 0.35) * math.cos(k * 18)
    X, Y = M[0, 0] * gx + M[0, 2], M[1, 1] * (gy - 8) + M[1, 2]
    R = 40 * sc / 4
    m = int(R * 3)
    x0, y0, x1, y1 = int(X - m), int(Y - m), int(X + m), int(Y + m)
    Yg, Xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    w = np.exp(-(((Xg - X) / R) ** 2 + ((Yg - Y) / (0.8 * R)) ** 2))
    from studio.film.stage import warp_region
    img = img.copy()
    warp_region(img, x0, y0, x1, y1, (w * amp * sc / 4 * 0.6).astype(np.float32), (-w * amp * sc / 4).astype(np.float32))
    spec = dict(keys=[(tn, gx - 4, gy - 14), (tn + 0.5, gx - 6, gy + 2, 3.0)], r=2.4, floor=gy + 6)
    return ball(img, dict(ball=spec), t, M, sc)


# ---------------------------------------------------------------- camera flashes and phones in the stands
def flashes(img, s, t, M, sc):
    rng = np.random.default_rng(int(t * 30))
    out = img.copy()
    for _ in range(14):
        x, y = rng.uniform(0, OW), rng.uniform(0.08 * OH, 0.55 * OH)
        r = rng.uniform(4, 12) * RS
        cv2.circle(out, (int(x), int(y)), int(r), (1.0, 1.0, 1.0), -1, cv2.LINE_AA)
    glow = cv2.GaussianBlur(np.clip(out - img, 0, 1), (0, 0), 8 * RS)
    return np.clip(out + glow * 1.5, 0, 1.5)


def phones(img, s, t, M, sc):
    """phone torches held up all round the stands, swaying slowly"""
    rng = np.random.default_rng(77)
    pts = rng.uniform([0, 300], [1672, 560], (900, 2))
    ph = rng.uniform(0, 6.28, 900)
    lay = np.zeros((OH, OW), np.float32)
    for (x, y), p in zip(pts, ph):
        xx = x + 3.0 * math.sin(0.9 * t + p)
        X, Y = M[0, 0] * xx + M[0, 2], M[1, 1] * y + M[1, 2]
        if 0 <= X < OW and 0 <= Y < OH:
            cv2.circle(lay, (int(X), int(Y)), max(1, int(0.9 * sc / 4)), 1.0, -1, cv2.LINE_AA)
    glow = cv2.GaussianBlur(lay, (0, 0), 3 * RS)
    return img + (lay * 0.9 + glow * 1.8)[..., None] * np.float32([0.85, 0.92, 1.0])


# ---------------------------------------------------------------- passers-by in the foreground (the street)
def passers(img, s, t, M, sc):
    """supporters walking past between the lens and the action: heads and shoulders in silhouette against the
    light, bobbing as they step, a scarf held up or a flag over a shoulder; out of focus"""
    o = s.get("passers", {})
    rng = np.random.default_rng(o.get("seed", 1))
    n = o.get("n", 8)
    lay = np.zeros((OH, OW, 4), np.float32)
    span = 1920 + 600
    speed = o.get("speed", 0.05) * 1920
    for i in range(n):
        x = (rng.uniform(0, span) + speed * t) % span - 300
        h = rng.uniform(0.9, 1.15)
        y = o.get("y", 0.88) * 1080 + 40 * (1 - h) + 10 * abs(math.sin(math.pi * (t * 1.9 + i * 0.37)))
        r = 62 * h
        X, Y, R = x * RS, y * RS, r * RS
        col = (0.06, 0.05, 0.07, 1.0)
        cv2.ellipse(lay, (int(X), int(Y + 2.2 * R)), (int(2.0 * R), int(1.7 * R)), 0, 180, 360, col, -1, cv2.LINE_AA)
        cv2.circle(lay, (int(X), int(Y)), int(R), col, -1, cv2.LINE_AA)
        if o.get("scarves") and i % 3 == 0:
            p0 = (X - 1.6 * R, Y - 1.4 * R)
            p1 = (X + 1.6 * R, Y - 1.5 * R)
            cl = 0.5 + 0.5 * math.sin(t * 3 + i)
            for k in range(6):
                xa = p0[0] + (p1[0] - p0[0]) * k / 6
                c = [(0.80, 0.07, 0.11, 1.0), (0.95, 0.94, 0.90, 1.0), (0.06, 0.05, 0.07, 1.0)][k % 3]
                cv2.rectangle(lay, (int(xa), int(p0[1] + 4 * cl)), (int(xa + (p1[0] - p0[0]) / 6), int(p0[1] + 0.45 * R + 4 * cl)),
                              c, -1)
            for p in (p0, p1):
                cv2.line(lay, (int(p[0]), int(p[1])), (int(p[0]), int(Y + R)), col, int(0.35 * R), cv2.LINE_AA)
        if o.get("flags") and i % 4 == 1:
            px = X + 0.8 * R
            cv2.line(lay, (int(px), int(Y + R)), (int(px + 0.6 * R), int(Y - 4 * R)), col, max(2, int(0.12 * R)), cv2.LINE_AA)
            sw = math.sin(t * 2.5 + i) * 0.3 * R
            fl = np.int32([(px + 0.6 * R, Y - 4 * R), (px + 3.4 * R, Y - 3.6 * R + sw), (px + 0.5 * R, Y - 2.4 * R)])
            cv2.fillPoly(lay, [fl], (0.80, 0.07, 0.11, 1.0), cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), o.get("blur", 5.0) * RS)
    return img * (1 - lay[..., 3:4]) + lay[..., :3]


# ---------------------------------------------------------------- the bicycle kick, in silhouette
def _place_rot(lay, key, cx, cy, h, deg, mirror=False):
    """a drawing put at screen (cx, cy) (its middle), h px tall, turned deg degrees: the key poses of the kick"""
    from studio.film import engine as E
    from studio.film.cast import CAST
    from studio.film.stage import top_of
    from studio.film.cast import feet as feet_of
    d, info = CAST.get(key)
    fx, fy = feet_of(key)
    top = top_of(key)
    mx, my = fx, (top + fy) / 2
    k = h / (fy - top)
    th = math.radians(deg)
    c, s_ = math.cos(th) * k, math.sin(th) * k
    sx = -1 if mirror else 1
    Ms = np.array([[c * sx, -s_, 0.0], [s_ * sx, c, 0.0]])
    Ms[:, 2] = np.array([cx, cy]) - Ms[:, :2] @ np.array([mx, my])
    E.place(lay, d, {}, Ms)


BICYCLE = [   # (t, drawing, centre x, y (layout px), height, degrees): the run, the leap, over, the strike, the fall
    (98.20, "wayne-rooney:kit-run1", 260, 760, 520, 0), (98.45, "wayne-rooney:kit-run2", 420, 760, 520, 0),
    (98.70, "wayne-rooney:kit-run3", 580, 760, 520, 0), (98.95, "wayne-rooney:kit-run1", 740, 760, 520, 0),
    (99.25, "wayne-rooney:kit-run2", 860, 700, 520, -18), (99.70, "wayne-rooney:kit-front", 940, 560, 500, -70),
    (100.30, "wayne-rooney:kit-run3", 960, 470, 500, -150), (101.10, "wayne-rooney:kit-run1", 960, 450, 500, -195),
    (102.10, "wayne-rooney:kit-run1", 965, 455, 500, -205), (102.60, "wayne-rooney:kit-front", 975, 560, 500, -250),
    (103.20, "wayne-rooney:kit-shrug", 980, 760, 560, -350),
]
KICK_T = 102.0                                                   # boot meets ball: on "bicycle", into "strike"


def bicycle(img, s, t, M, sc):
    """the overhead kick against the floodlights: the run in, the leap, turning over, the strike upside down (held,
    as if time stopped), the ball away, the fall and the arms out; black against the glare, a rim of white light"""
    from studio.film import engine as E
    ks = BICYCLE
    i = max(0, max(j for j, k in enumerate(ks) if k[0] <= t) if t >= ks[0][0] else 0)
    k0 = ks[i]
    k1 = ks[min(i + 1, len(ks) - 1)]
    u = 0.0 if k1[0] == k0[0] else min(1.0, (t - k0[0]) / (k1[0] - k0[0]))
    u = u * u * (3 - 2 * u)
    cx, cy = k0[2] + (k1[2] - k0[2]) * u, k0[3] + (k1[3] - k0[3]) * u
    deg = k0[5] + (k1[5] - k0[5]) * u
    h = k0[4] + (k1[4] - k0[4]) * u
    # the floodlight's glare behind him
    Y, X = np.ogrid[0:OH, 0:OW]
    g = np.exp(-(((X - 980 * RS) / (420 * RS)) ** 2 + ((Y - 430 * RS) / (300 * RS)) ** 2))
    img = img * 0.55 + g[..., None] * np.float32([1.0, 0.97, 0.9]) * 0.95
    lay = np.zeros((OH, OW, 4), np.float32)
    _place_rot(lay, k0[1], cx * RS, cy * RS, h * RS, deg)
    lay[..., :3] = lay[..., 3:4] * np.float32([0.02, 0.02, 0.04])            # in silhouette
    lay = E.rim(lay, -0.3, -1.0, 1.4, (1.0, 0.96, 0.9), 4 * RS)
    img = img * (1 - lay[..., 3:4]) + lay[..., :3]
    # the ball: dropping in from the top left to his boot, then struck away to the right
    if t < KICK_T:
        u = max(0.0, (t - (KICK_T - 1.6)) / 1.6)
        bx, by = 620 + 300 * u, 120 + 300 * u - 120 * math.sin(math.pi * u)
    else:
        u = (t - KICK_T) / 1.5
        bx, by = 920 + 1300 * u, 420 - 900 * u + 300 * u * u
    if t > KICK_T - 1.6:
        bspec = dict(keys=[(t - 1, bx - 1, by), (t, bx, by)], r=22, floor=by + 5000,
                     blur_v=60 if t > KICK_T else 0)
        img = ball(img, dict(ball=bspec), t, np.float32([[RS, 0, 0], [0, RS, 0]]), RS)
    if 0 <= t - KICK_T < 0.2:                                    # the contact: a flash
        img = img + (1 - img) * 0.6 * (1 - (t - KICK_T) / 0.2)
    return img


# ---------------------------------------------------------------- Keane's one clap
def clap(img, s, t, M, sc):
    """two hands in black sleeves (his arms unfolding from his chest) meeting once, on the crash: a hand drawn as
    the house draws one: a rounded palm, the fingers together, a bold outline; impact lines on the clap"""
    tc = s["clap"]["t"]
    u = (t - (tc - 0.30)) / 0.30
    gap = 420 * (1 - min(1.0, max(0.0, u)) ** 2) if t < tc else 30 * math.exp(-(t - tc) / 0.08)
    img = img * 0.75
    lay = np.zeros((OH * 2, OW * 2, 4), np.float32)
    S2 = 2 * RS
    skin, sh, ink = (0.96, 0.72, 0.56, 1.0), (0.84, 0.56, 0.42, 1.0), (0.09, 0.07, 0.08, 1.0)
    H2, W2 = lay.shape[:2]
    for side in (-1, 1):                                           # side -1: his right hand, on screen left
        cx, cy = 960 + side * (gap / 2 + 135), 470                 # the palm's centre; fingers up, palms facing
        P = lambda pts: np.int32(np.float32(pts) * S2)             # noqa: E731
        sleeve = P([(cx - side * 20, cy + 230), (cx + side * 160, cy + 190), (cx + side * 640, cy + 640),
                    (cx + side * 260, cy + 700)])
        cv2.fillPoly(lay, [sleeve], (0.10, 0.08, 0.10, 1.0), cv2.LINE_AA)
        cv2.polylines(lay, [sleeve], True, (0.55, 0.12, 0.14, 1.0), int(7 * S2), cv2.LINE_AA)   # stage-light rim
        m = np.zeros((H2, W2), np.uint8)                           # the hand: a mitten with the thumb out the side
        cv2.fillPoly(m, [P(cv2.ellipse2Poly((int(cx), int(cy)), (128, 270), int(side * 6), 0, 360, 4))], 255,
                     cv2.LINE_AA)
        cv2.fillPoly(m, [P(cv2.ellipse2Poly((int(cx + side * 105), int(cy + 20)), (55, 140), int(side * 30), 0, 360,
                                            6))], 255, cv2.LINE_AA)
        a = (m.astype(np.float32) / 255.0)[..., None]
        lay[:] = lay * (1 - a) + np.float32(skin) * a
        sh_m = np.zeros((H2, W2), np.uint8)
        cv2.fillPoly(sh_m, [P(cv2.ellipse2Poly((int(cx + side * 60), int(cy + 120)), (60, 150), int(side * 6), 0, 360,
                                               6))], 255, cv2.LINE_AA)
        a2 = (np.minimum(sh_m, m).astype(np.float32) / 255.0)[..., None]
        lay[:] = lay * (1 - a2) + np.float32(sh) * a2
        cs, _ = cv2.findContours((m > 127).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        cv2.polylines(lay, [c.reshape(-1, 2) for c in cs], True, ink, int(11 * S2), cv2.LINE_AA)
        thumb_line = P([(cx + side * 70, cy - 60), (cx + side * 95, cy + 40), (cx + side * 80, cy + 140)])
        cv2.polylines(lay, [thumb_line], False, ink, int(6 * S2), cv2.LINE_AA)
        for k in range(3):                                         # the fingers: three creases at the top
            x = cx + side * (-60 + k * 40)
            y0 = cy - 262 + 22 * abs(k - 1)
            cv2.line(lay, (int(x * S2), int(y0 * S2)), (int(x * S2), int((y0 + 95) * S2)), ink, int(6 * S2),
                     cv2.LINE_AA)
    lay = cv2.resize(lay, (OW, OH), interpolation=cv2.INTER_AREA)
    img = img * (1 - lay[..., 3:4]) + lay[..., :3]
    if 0 <= t - tc < 0.25:                                        # the impact
        a = 1 - (t - tc) / 0.25
        for k in range(8):
            ang = k * math.pi / 4
            p0 = (960 + 330 * math.cos(ang), 470 + 330 * math.sin(ang))
            p1 = (960 + (420 + 140 * (1 - a)) * math.cos(ang), 470 + (420 + 140 * (1 - a)) * math.sin(ang))
            cv2.line(img, (int(p0[0] * RS), int(p0[1] * RS)), (int(p1[0] * RS), int(p1[1] * RS)), (1.0, 0.95, 0.7),
                     max(2, int(12 * RS * a)), cv2.LINE_AA)
    return img


# ---------------------------------------------------------------- confetti lying on the stage
DECKS = {"OTS": STAGE_DECK, "B08": (40, 618, 1630, 806)}     # where confetti settles (1x px)


@functools.lru_cache(maxsize=4)
def _floor_bits(plate="OTS"):
    rng = np.random.default_rng(9)
    x0, ytop, x1, yfront = DECKS.get(plate, STAGE_DECK)
    n = 520 if plate == "OTS" else 1400
    xs = rng.uniform(x0 + 20, x1 - 20, n)
    ys = rng.uniform(ytop + 2, yfront - 1, n)
    cols = np.float32([[0.86, 0.06, 0.09], [0.97, 0.96, 0.94], [1.0, 0.80, 0.22]])[rng.integers(0, 3, n)]
    return xs, ys, rng.uniform(0, 3.14, n), cols


def floor_confetti(img, s, t, M, sc):
    """the confetti lying on the stage; s["swept"] = (x0, x1, y0, y1, t0, t1): a patch the broom pushes the confetti
    out of, from x0 towards x1, between t0 and t1 (a ridge of it moving ahead of the broom)"""
    xs, ys, ang, cols = _floor_bits(s["plate"])
    if s.get("swept"):
        sx0, sx1, sy0, sy1, t0, t1 = s["swept"]
        u = float(np.clip((t - t0) / (t1 - t0), 0, 1))
        front = sx0 + (sx1 - sx0) * u
        inside = (ys >= sy0) & (ys <= sy1) & (xs >= min(sx0, sx1)) & (xs <= max(sx0, sx1))
        behind = inside & ((xs < front) if sx1 > sx0 else (xs > front))
        jitter = (np.sin(xs * 12.9898 + ys * 78.233) * 0.5 + 0.5) * 6.0
        xs = np.where(behind, front + np.sign(sx1 - sx0) * jitter, xs)
    out = img.copy()
    k = sc / 4.0
    for x, y, a, c in zip(xs, ys, ang, cols):
        X, Y = M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]
        if -10 < X < OW + 10 and -10 < Y < OH + 10:
            w, h = 1.6 * k, 0.7 * k
            pts = np.float32([[-w, -h], [w, -h], [w, h], [-w, h]]) @ np.float32([[math.cos(a), math.sin(a) * 0.4],
                                                                            [-math.sin(a), math.cos(a) * 0.4]])
            cv2.fillConvexPoly(out, np.int32((pts + (X, Y)) * 4), tuple(float(v) * 0.8 for v in c), cv2.LINE_AA, 2)
    return out


# ---------------------------------------------------------------- the scarf wipe (into and out of the memory)
def scarf_wipe(img, t, tc, entering):
    """a United scarf swept past the lens: it covers the frame at tc (the cut) and has gone a quarter of a second
    either side. entering=False: the shot before the cut (the scarf coming in), True: the shot after"""
    from film import things as T
    d = (t - tc) / 0.28
    if (not entering and not -1 <= d <= 0) or (entering and not 0 <= d <= 1):
        return img
    cloth = T.scarf_cloth("bars", 1400, 220)
    H2, W2 = cloth.shape[:2]
    lay = cv2.resize(cloth, (int(W2 * 1.9 * RS), int(H2 * 6.2 * RS)), interpolation=cv2.INTER_LINEAR)
    lay = lay.astype(np.float32) / 255.0
    lay[..., :3] *= lay[..., 3:4]
    lay = cv2.GaussianBlur(lay, (0, 0), 6 * RS)
    x = (-lay.shape[1] + d * (lay.shape[1] + OW) * 0.5 + (lay.shape[1] + OW) * 0.5)
    A = np.float32([[1, 0, x], [0, 1, (OH - lay.shape[0]) / 2]])
    w = cv2.warpAffine(lay, A, (OW, OH), borderMode=cv2.BORDER_CONSTANT)
    return img * (1 - w[..., 3:4]) + w[..., :3]


# ---------------------------------------------------------------- the pub: the trophy on the table, scarves going up
TROPHY_AT = (446, 489)                      # plate F: on top of the left-hand stage monitor


def trophy_table(img, s, t, M, sc):
    """Goldbridge's tiny trophy, nudged: it rocks over towards the edge, teeters, and settles back"""
    from film import things as T
    from film.timeline import b
    t0, t1 = b(9, 0.55), b(10, 0.75)
    u = min(1.0, max(0.0, (t - t0) / (t1 - t0)))
    ang = 28 * math.sin(math.pi * u) * math.exp(-1.2 * u) + 6 * math.sin(14 * u) * (1 - u) if 0 < u < 1 else 0
    im, grip = T.trophy(160)
    k = 44 * sc / 160.0 / 4
    th = math.radians(ang)
    piv = (im.shape[1] * (0.5 + 0.3 * np.sign(ang)), im.shape[0] * 0.96)
    c, s_ = math.cos(th) * k, math.sin(th) * k
    X, Y = M[0, 0] * TROPHY_AT[0] + M[0, 2], M[1, 1] * TROPHY_AT[1] + M[1, 2]
    A = np.float32([[c, -s_, 0], [s_, c, 0]])
    A[:, 2] = np.float32([X + (piv[0] - im.shape[1] / 2) * k, Y]) - A[:, :2] @ np.float32(piv)
    lay = np.zeros((OH, OW, 4), np.float32)
    _paste(lay, im, A)
    return img * (1 - lay[..., 3:4]) + lay[..., :3]


def scarves_rise(img, s, t, M, sc):
    """along the rows, scarves going up one after another, held between two fists, each a beat behind the last"""
    from film import things as T
    t0 = s.get("scarves_t", s["t"])
    lay = np.zeros((OH, OW, 4), np.float32)
    xs = [230, 560, 860, 1180, 1500, 1760, 400, 1020, 1640]
    for k, x in enumerate(xs):
        st = t0 + 0.18 * k
        u = min(1.0, max(0.0, (t - st) / 0.45))
        if u <= 0:
            continue
        u = 1 - (1 - u) ** 3
        back = k >= 6
        w = (300 if not back else 220) * RS
        y = OH + 60 * RS - u * ((520 if not back else 610) * RS)
        sway = 18 * RS * math.sin(2.4 * t + k)
        p0 = np.float32([x * RS - w / 2 + sway, y])
        p1 = np.float32([x * RS + w / 2 + sway, y - 8 * RS * math.sin(t * 3 + k)])
        h = int((52 if not back else 38) * RS)
        cloth = T.scarf_cloth(["bars", "red", "black"][k % 3], int(w * 1.1), max(8, h))
        L = float(np.linalg.norm(p1 - p0))
        d = (p1 - p0) / L
        n = np.float32([-d[1], d[0]])
        A = np.float32([[d[0] * L / cloth.shape[1], n[0], 0], [d[1] * L / cloth.shape[1], n[1], 0]])
        A[:, 2] = p0 - A[:, :2] @ np.float32([0, cloth.shape[0] / 2])
        _paste(lay, cloth, A)
        for p in (p0, p1):                                          # the fists, the arms down out of frame
            col = (0.95, 0.74, 0.58, 1.0)
            cv2.line(lay, (int(p[0]), int(p[1])), (int(p[0] + 10 * RS), int(OH + 50)), (0.62, 0.06, 0.09, 1.0),
                     int(46 * RS), cv2.LINE_AA)
            cv2.circle(lay, (int(p[0]), int(p[1])), int(26 * RS), col, -1, cv2.LINE_AA)
            cv2.circle(lay, (int(p[0]), int(p[1])), int(26 * RS), (0.09, 0.07, 0.08, 1.0), max(2, int(5 * RS)), cv2.LINE_AA)
    if s.get("blur_fg", 2.0):
        lay = cv2.GaussianBlur(lay, (0, 0), s.get("blur_fg", 2.0) * RS)
    return img * (1 - lay[..., 3:4]) + lay[..., :3]


def strike_flash(img, s, t, M, sc):
    """the boot meets the ball: a white star of impact lines off the toe for a few frames"""
    tc = s.get("strike")
    if tc is None or not 0 <= t - tc < 0.2:
        return img
    a = 1 - (t - tc) / 0.2
    out = img.copy()
    cx, cy = 1090 * RS, 975 * RS
    if s.get("strike_at"):                                        # plate px
        cx, cy = M[0, 0] * s["strike_at"][0] + M[0, 2], M[1, 1] * s["strike_at"][1] + M[1, 2]
    for k in range(7):
        ang = -0.6 + k * 0.32
        r0, r1 = 50 * RS, (110 + 90 * (1 - a)) * RS
        cv2.line(out, (int(cx + r0 * math.cos(ang)), int(cy - r0 * math.sin(ang))),
                 (int(cx + r1 * math.cos(ang)), int(cy - r1 * math.sin(ang))), (1.0, 1.0, 0.9), max(2, int(9 * RS * a)),
                 cv2.LINE_AA)
    return out

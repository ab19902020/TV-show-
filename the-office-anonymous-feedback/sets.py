"""The five sets: plates (4x upscaled backgrounds), small set changes, and what stands in front of the actors.

All coordinates are in the 1x background pixels (1672 x 941) and scaled by 4 for the plates.

- desks (02): the modesty panels are carried down to the floor (a full-front office desk), so a seated character's
  legs are hidden by the desk instead of being cut off; the in-tray, papers, keyboard, pen pot and mouse on the
  corner of Gareth's desk are cleared for the suggestions box and his notebook, and the spare mouse under Tim's hand.
- every set lists `objects`: the things on the desks that are in front of a seated character (monitors, phones,
  pen pots...). They are cut out of the plate with GrabCut and laid back over the actors.
- `cut`: the far edge of the desk top. A seated character is hidden below it, except for his hands, which rest on
  the desk.
"""
import os, numpy as np, cv2
from functools import lru_cache

UPDIR = "build/up"
CACHE = "build/sets"

SETS = {
    "desks": dict(
        plate="02_tim_gareth_desks_front", cut=497,
        # (x0, y0, x1, y1) of each object on the desk; GrabCut finds its outline in the box
        objects=[(25, 310, 300, 548), (283, 440, 345, 546), (330, 480, 478, 524), (338, 510, 382, 536),
                 (625, 455, 762, 534), (1335, 446, 1392, 543)],
        # Gareth's monitor and mouse come off the desk so Brent, standing there, is not hidden behind them
        remove=[(1386, 306, 1663, 549)],
        clear=[(890, 496, 1354, 549, (828, 890)), (556, 496, 630, 532, (765, 815))],
        inpaint=[(1218, 481, 1356, 496), (1114, 486, 1135, 496)],
        vfill=[(888, 448, 1100, 496)],
        panels=[(270, 600, 745, 800), (905, 600, 1400, 800)],
    ),
    "tim": dict(
        plate="03_tim_seat_close", cut=745,
        mid=[(540, 382, 1158, 752)],
        objects=[(0, 325, 300, 941), (140, 675, 302, 930), (240, 730, 552, 835), (1300, 540, 1672, 941)],
        clear=[], panels=[],
    ),
    "gareth": dict(
        plate="04_gareth_seat_close", cut=668,
        mid=[(636, 390, 1163, 674)],
        objects=[(0, 575, 275, 830), (322, 620, 455, 808), (430, 725, 515, 805), (505, 755, 592, 795),
                 (1040, 680, 1155, 740), (1145, 650, 1405, 735), (1325, 690, 1672, 835), (1360, 335, 1672, 712)],
        clear=[], panels=[],
    ),
    "interview": dict(plate="14_interview_wall", cut=None, objects=[], clear=[], panels=[]),
    "wide": dict(
        plate="01_open_office_wide", cut=None,
        # the two desk islands the walkers pass behind
        objects=[(0, 330, 645, 880), (1040, 300, 1672, 941)],
        clear=[], panels=[],
    ),
    "carpark": dict(plate="22_car_park", cut=None, objects=[], clear=[], panels=[]),
}


def _plate(name):
    im = cv2.imread(f"{UPDIR}/{name}.png", cv2.IMREAD_COLOR)
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB)


def _desk_fill(pl, rect):
    """re-lay a cleared patch of desk top row by row from clean desk on the same desk (the desk is seen
    square-on, so every row of the top has one colour: back edge line, top, front edge highlight)"""
    x0, y0, x1, y1 = [v * 4 for v in rect[:4]]
    sx0, sx1 = rect[4][0] * 4, rect[4][1] * 4
    prof = np.median(pl[y0:y1, sx0:sx1].astype(np.float32), 1)
    grain = np.random.default_rng(5).normal(0, 1.5, (y1 - y0, x1 - x0, 1))
    grain = cv2.GaussianBlur(grain, (0, 0), sigmaX=9, sigmaY=0.7)[..., None] * 3
    out = prof[:, None, :] + grain
    # feather into the plate
    m = np.ones((y1 - y0, x1 - x0), np.float32)
    f = 10
    m[:, :f] *= np.linspace(0, 1, f)[None]
    m[:, -f:] *= np.linspace(1, 0, f)[None]
    region = pl[y0:y1, x0:x1].astype(np.float32)
    pl[y0:y1, x0:x1] = (region * (1 - m[..., None]) + out * m[..., None]).astype(np.uint8)


def _panel(pl, rect):
    """carry the desk's dark modesty panel down to just above the carpet"""
    x0, y0, x1, y1 = [v * 4 for v in rect]
    ref = pl[y0:y0 + 120, x0 + 60:x1 - 60].astype(np.float32)
    col = np.median(ref.reshape(-1, 3), 0)
    h = y1 - y0
    grad = np.linspace(1.0, 0.86, h)[:, None, None]
    noise = cv2.GaussianBlur(np.random.default_rng(3).normal(0, 2.0, (h, x1 - x0)), (0, 0), 3)[..., None]
    fill = np.clip(col * grad + noise, 0, 255)
    # the existing top of the panel (its shadow band) stays; fade the new panel in below it
    a = np.clip((np.arange(h) - 100) / 60, 0, 1)[:, None, None]
    cur = pl[y0:y1, x0:x1].astype(np.float32)
    pl[y0:y1, x0:x1] = (cur * (1 - a) + fill * a).astype(np.uint8)
    # bottom edge: a dark line like the drawing's outlines, and a soft shadow on the carpet
    cv2.rectangle(pl, (x0, y1 - 12), (x1, y1), (22, 22, 24), -1)
    sh = pl[y1:y1 + 60, x0:x1].astype(np.float32)
    fade = np.linspace(0.55, 1.0, 60)[:, None, None]
    pl[y1:y1 + 60, x0:x1] = (sh * fade).astype(np.uint8)


def _grabcut(pl1, rect):
    x0, y0, x1, y1 = rect
    pad = 12
    X0, Y0 = max(x0 - pad, 0), max(y0 - pad, 0)
    X1, Y1 = min(x1 + pad, pl1.shape[1]), min(y1 + pad, pl1.shape[0])
    sub = np.ascontiguousarray(pl1[Y0:Y1, X0:X1, ::-1])
    mask = np.zeros(sub.shape[:2], np.uint8)
    r = (x0 - X0, y0 - Y0, x1 - x0, y1 - y0)
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(sub, mask, r, bgd, fgd, 6, cv2.GC_INIT_WITH_RECT)
    m = ((mask == 1) | (mask == 3)).astype(np.uint8)
    full = np.zeros(pl1.shape[:2], np.uint8)
    full[Y0:Y1, X0:X1] = m
    return full


@lru_cache(maxsize=None)
def build(name):
    """-> (plate rgb uint8 4x, front mask float32 4x, mid mask float32 4x)"""
    s = SETS[name]
    os.makedirs(CACHE, exist_ok=True)
    pf, mf, df = f"{CACHE}/{name}.png", f"{CACHE}/{name}_front.png", f"{CACHE}/{name}_mid.png"
    if os.path.exists(pf) and os.path.exists(mf) and os.path.exists(df):
        pl = cv2.cvtColor(cv2.imread(pf), cv2.COLOR_BGR2RGB)
        fm = cv2.imread(mf, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
        mm = cv2.imread(df, cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
        return pl, fm, mm
    pl0 = _plate(s["plate"])
    H, W = pl0.shape[:2]
    small = cv2.resize(pl0, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    fm = np.zeros((H // 4, W // 4), np.uint8)
    for r in s["objects"]:
        fm |= _grabcut(small, r)
    fm = cv2.morphologyEx(fm, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    big = cv2.resize(fm.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    big = cv2.GaussianBlur(big, (0, 0), 2.0)
    big = np.clip((big - 0.5) * 3 + 0.5, 0, 1)
    pl = pl0.copy()
    for r in s["clear"]:
        _desk_fill(pl, r)
    for x0, y0, x1, y1 in s.get("inpaint", []):
        m = np.zeros(pl.shape[:2], np.uint8)
        m[y0 * 4:y1 * 4, x0 * 4:x1 * 4] = 1
        X0, Y0, X1, Y1 = x0 * 4 - 40, y0 * 4 - 40, x1 * 4 + 40, y1 * 4 + 4
        pl[Y0:Y1, X0:X1] = cv2.inpaint(np.ascontiguousarray(pl[Y0:Y1, X0:X1]), m[Y0:Y1, X0:X1], 9, cv2.INPAINT_TELEA)
    for x0, y0, x1, y1 in s.get("vfill", []):
        # carry the wall / cabinet straight down behind removed things (their edges are vertical)
        src = pl[y0 * 4 - 6:y0 * 4 - 2, x0 * 4:x1 * 4].astype(np.float32).mean(0)
        n = (y1 - y0) * 4
        noise = np.random.default_rng(9).normal(0, 1.0, (n, x1 * 4 - x0 * 4, 1))
        pl[y0 * 4:y1 * 4, x0 * 4:x1 * 4] = np.clip(src[None] + noise, 0, 255).astype(np.uint8)
    for x0, y0, x1, y1 in s.get("remove", []):
        # rebuild what is behind Gareth's monitor and mouse, layer by layer (all 1x rows):
        X0, X1 = x0 * 4, x1 * 4
        reb = pl.copy()
        # 306-345: the two-level tray / wall above the cabinet: repeat the band just above it
        band = pl0[268 * 4:306 * 4, X0:X1]
        reb[306 * 4:344 * 4, X0:X1] = band[: 38 * 4]
        # 344-496: the cabinet front, row by row from its visible right end, with its top lip
        for y in range(344 * 4, 496 * 4):
            reb[y, X0:X1] = np.median(pl0[y, 1652 * 4:1670 * 4].astype(np.float32), 0)
        cv2.line(reb, (1392 * 4, 344 * 4), (1392 * 4, 496 * 4), (40, 30, 24), 10)
        # 496-549: the desk top, row by row from clean desk on the same desk
        for y in range(496 * 4, 549 * 4):
            reb[y, X0:X1] = np.median(pl0[y, 828 * 4:890 * 4].astype(np.float32), 0)
        m = np.zeros(pl.shape[:2], np.float32)
        m[y0 * 4:y1 * 4, X0:X1] = 1
        m = cv2.GaussianBlur(m, (0, 0), 5)[..., None]
        pl = (pl * (1 - m) + reb * m).astype(np.uint8)
    for r in s["panels"]:
        _panel(pl, r)
    # the objects on the desks stay whole where a cleared patch touched them
    k = cv2.dilate((big > 0.02).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32)
    k = cv2.GaussianBlur(k, (0, 0), 2)[..., None]
    pl = (pl * (1 - k) + pl0 * k).astype(np.uint8)
    # the chair the walkers pass behind (single shots)
    mm = np.zeros((H // 4, W // 4), np.uint8)
    for r in s.get("mid", []):
        mm |= _grabcut(small, r)
    mm = cv2.morphologyEx(mm, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    mid = cv2.resize(mm.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    mid = np.clip((cv2.GaussianBlur(mid, (0, 0), 2.0) - 0.5) * 3 + 0.5, 0, 1)
    cv2.imwrite(pf, cv2.cvtColor(pl, cv2.COLOR_RGB2BGR))
    cv2.imwrite(mf, (big * 255).astype(np.uint8))
    cv2.imwrite(df, (mid * 255).astype(np.uint8))
    return pl, big, mid


if __name__ == "__main__":
    import sys
    for n in sys.argv[1:] or SETS:
        if os.path.exists(f"{UPDIR}/{SETS[n]['plate']}.png"):
            build(n)
            print("built", n)

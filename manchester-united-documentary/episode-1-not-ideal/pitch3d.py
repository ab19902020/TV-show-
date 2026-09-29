"""A small broadcast-camera renderer for the Hull match (scene 4).

The pitch is a real 105 x 68 m ground plane (grass stripes, every marking, goals with nets). The one painted stand we
have (the view through the tunnel mouth, relit for a night game and filled with a drawn crowd) is mapped onto three
billboard stands: the far side and both ends. A pinhole camera looks at it all, so pans, zooms, a high broadcast
wide and a pitch-level telephoto all come from the same place with correct perspective and parallax.

World: metres. x along the pitch (0 = United's... the left goal line, 105 = the right), y across (0 = the near touchline,
68 = the far one), z up. Players are billboards (drawings, cut from the sheets and scaled to 1.8 m), the ball a sphere.

render(cam, t, players, ball, crowd) -> float32 RGB frame (OH x OW)."""
import math, functools, json, numpy as np, cv2
import engine as E

OW, OH = E.OW, E.OH
L_, W_ = 105.0, 68.0
STAND = dict(far=74.0, left=-9.0, right=114.0)     # billboard planes (far: y = ..., ends: x = ...)
STAND_H = 24.0                                     # height of the painted strip (ad boards -> gantry), m
TILE_M = 42.0                                      # one painted strip section, m wide


# ---------------------------------------------------------------- the stand texture (relit strip + crowd)
SRC = "build/bg/tunnel_view.png"
X0, X1, Y0, Y1 = 850, 1160, 318, 497               # the clean part of the painted stand (1x)
# seat areas in the strip (1x strip px, y from the strip top): (y0, y1) upper tier / lower tier
TIERS = [(73, 116, 0.95), (128, 172, 1.0)]
HULL = [(0.97, 0.63, 0.05), (0.95, 0.58, 0.04), (0.10, 0.10, 0.11), (0.14, 0.14, 0.16), (0.93, 0.93, 0.93),
        (0.20, 0.24, 0.40), (0.55, 0.55, 0.58), (0.97, 0.70, 0.10)]
AWAY = [(0.80, 0.08, 0.10), (0.85, 0.10, 0.12), (0.10, 0.10, 0.11), (0.93, 0.93, 0.93)]
SKIN = [(0.93, 0.74, 0.60), (0.86, 0.64, 0.50), (0.62, 0.43, 0.30), (0.42, 0.28, 0.20), (0.95, 0.80, 0.68)]


@functools.lru_cache(maxsize=1)
def strip():
    a = cv2.imread(SRC)[..., ::-1].astype(np.float32) / 255
    s = a[Y0 * 4:Y1 * 4, X0 * 4:X1 * 4].copy()
    lum = s.mean(2, keepdims=True)
    s = s * 0.60 + 0.02
    s[..., 0:1] *= 1.05; s[..., 2:3] *= 0.9
    hot = np.clip((lum - 0.78) / 0.2, 0, 1) * (np.arange(s.shape[0])[:, None, None] < 18 * 4)
    s = s * (1 - hot) + np.float32([1.0, 0.97, 0.9]) * hot
    return s


@functools.lru_cache(maxsize=16)
def stand_tex(variant, away_side=False):
    """the strip with a crowd drawn on the seat rows (cached in build/). variant: 0/1 = watching, swaying;
    2/3 = arms up (a goal)"""
    import os
    fn = f"build/stand_tex_{variant}_{int(away_side)}.npy"
    if os.path.exists(fn):
        return np.load(fn)
    out = _stand_tex(variant, away_side)
    np.save(fn, out)
    return out


SS = 2                                             # the crowd texture is drawn at 2x the strip for telephoto shots


def _stand_tex(variant, away_side):
    s = cv2.resize(strip(), None, fx=SS, fy=SS, interpolation=cv2.INTER_CUBIC)
    H, W = s.shape[:2]
    rng = np.random.default_rng(11 + (1 if away_side else 0))
    lay = np.zeros_like(s); al = np.zeros(s.shape[:2], np.float32)
    cheer = variant >= 2
    F = 8                                          # sub-pixel drawing (shift = 3)
    q = lambda v: int(round(v * F))
    def ell(c, x, y, rx, ry, col, a_=1.0):
        cv2.ellipse(lay, (q(x), q(y)), (q(rx), q(ry)), 0, 0, 360, col, -1, cv2.LINE_AA, 3)
        cv2.ellipse(al, (q(x), q(y)), (q(rx), q(ry)), 0, 0, 360, a_, -1, cv2.LINE_AA, 3)
    def seg(x0, y0, x1, y1, col, w):
        cv2.line(lay, (q(x0), q(y0)), (q(x1), q(y1)), col, max(1, int(round(w))), cv2.LINE_AA, 3)
        cv2.line(al, (q(x0), q(y0)), (q(x1), q(y1)), 1.0, max(1, int(round(w))), cv2.LINE_AA, 3)
    u = 4 * SS                                     # texture px per 1x strip px
    for (ty0, ty1, dens) in TIERS:
        rows = int((ty1 - ty0) / 3.0)
        for r in range(rows):
            y = (ty0 + (r + 0.8) * (ty1 - ty0) / rows) * u
            n = int(W / (u * 2.6) * dens)
            xs = np.sort(rng.uniform(0, W, n))
            for k, x in enumerate(xs):
                ph = rng.uniform(0, 1)
                pal = AWAY if (away_side and x < W * 0.45) else HULL
                c = pal[rng.integers(len(pal))]
                sk = SKIN[rng.integers(len(SKIN))]
                hair = [(0.12, 0.09, 0.07), (0.35, 0.22, 0.12), (0.8, 0.65, 0.4), (0.5, 0.5, 0.5)][rng.integers(4)]
                bob = 0.4 * math.sin(2 * math.pi * (ph + variant * 0.5))
                hy = y + (bob - (0.6 if cheer and rng.random() < 0.7 else 0)) * u
                sc = rng.uniform(0.9, 1.15) * u / 4
                ell(0, x, hy + 6 * sc, 5.2 * sc, 6.2 * sc, tuple(v * 0.9 for v in c))       # shoulders
                ell(0, x, hy, 3.2 * sc, 3.4 * sc, sk)                                        # head
                if rng.random() < 0.8:
                    ell(0, x, hy - 1.4 * sc, 3.3 * sc, 2.0 * sc, hair)                       # hair / hat
                if cheer and rng.random() < 0.65:                                            # arms up
                    for side in (-1, 1):
                        x2 = x + side * (4 + 2 * math.sin(variant * 3 + ph * 6)) * sc
                        seg(x + side * 3.5 * sc, hy + 4 * sc, x2, hy - 8 * sc, c, 1.8 * sc)
                        ell(0, x2, hy - 8.5 * sc, 1.3 * sc, 1.3 * sc, sk)
                elif rng.random() < 0.05:                                                    # a scarf held up
                    seg(x - 6 * sc, hy - 6 * sc, x + 6 * sc, hy - 7 * sc, c, 2.0 * sc)
    al = np.clip(al, 0, 1)[..., None] * 0.95
    out = s * (1 - al) + lay * 0.8 * al
    yy = np.arange(H, dtype=np.float32)[:, None, None]
    out = out + np.exp(-((yy - 8 * u) / (10 * u)) ** 2) * np.float32([0.10, 0.09, 0.08])    # floodlight gantry glow
    return np.clip(out, 0, 1).astype(np.float32)


# ---------------------------------------------------------------- camera
class Cam:
    """pinhole: position p, looking at target, horizontal field of view (deg)"""

    def __init__(self, p, target, fov):
        self.p = np.float64(p)
        f = np.float64(target) - self.p; f /= np.linalg.norm(f)
        r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r)
        u = np.cross(r, f)
        self.f, self.r, self.u = f, r, u
        self.fpx = (OW / 2) / math.tan(math.radians(fov) / 2)

    def project(self, X):
        """world points (N, 3) -> screen (N, 2), depth (N,)"""
        X = np.atleast_2d(np.float64(X)) - self.p
        z = X @ self.f
        x = X @ self.r; y = X @ self.u
        return np.stack([OW / 2 + self.fpx * x / z, OH / 2 - self.fpx * y / z], 1), z


def lerp_cam(a, b, u):
    return Cam(np.float64(a[0]) + (np.float64(b[0]) - a[0]) * u, np.float64(a[1]) + (np.float64(b[1]) - a[1]) * u,
               a[2] + (b[2] - a[2]) * u)


# ---------------------------------------------------------------- per-pixel rays (cached per camera)
def rays(cam, step=1):
    ys, xs = np.mgrid[0:OH:step, 0:OW:step].astype(np.float32)
    u = (xs - OW / 2) / cam.fpx; v = (OH / 2 - ys) / cam.fpx
    d = cam.f[None, None, :].astype(np.float32) + u[..., None] * cam.r.astype(np.float32) + v[..., None] * cam.u.astype(np.float32)
    return d


def pitch_lines(X, Y, fp):
    """anti-aliased line coverage on the ground, fp = world size of a pixel"""
    hw = 0.06
    def band(dist):
        return np.clip((hw + 0.5 * fp - np.abs(dist)) / np.maximum(fp, 1e-3), 0, 1)
    inx = (X > -0.1) & (X < L_ + 0.1); iny = (Y > -0.1) & (Y < W_ + 0.1)
    m = np.zeros(X.shape, np.float32)
    m = np.maximum(m, band(Y) * inx); m = np.maximum(m, band(Y - W_) * inx)
    m = np.maximum(m, band(X) * iny); m = np.maximum(m, band(X - L_) * iny)
    m = np.maximum(m, band(X - L_ / 2) * iny)
    r = np.sqrt((X - L_ / 2) ** 2 + (Y - W_ / 2) ** 2)
    m = np.maximum(m, band(r - 9.15))
    m = np.maximum(m, np.clip((0.2 - r) / np.maximum(fp, 1e-3) + 0.5, 0, 1))
    for gx, sgn in ((0.0, 1), (L_, -1)):
        dx = (X - gx) * sgn
        for depth, half in ((16.5, 20.16), (5.5, 9.16)):
            iny2 = np.abs(Y - W_ / 2) < half + hw
            m = np.maximum(m, band(dx - depth) * iny2 * (dx > -0.1))
            m = np.maximum(m, band(np.abs(Y - W_ / 2) - half) * (dx > -0.1) * (dx < depth + hw))
        rs = np.sqrt((dx - 11) ** 2 + (Y - W_ / 2) ** 2)
        m = np.maximum(m, np.clip((0.15 - rs) / np.maximum(fp, 1e-3) + 0.5, 0, 1))
        m = np.maximum(m, band(rs - 9.15) * (dx > 16.5))
    for cx, cy in ((0, 0), (0, W_), (L_, 0), (L_, W_)):
        rc = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        m = np.maximum(m, band(rc - 1.0) * inx * iny)
    return m


def background(cam, t=0.0, crowd_state=0.0, dof=0.0):
    """sky + three billboard stands + the pitch; crowd_state 0 = watching, 1 = goal (arms up)"""
    d = rays(cam)
    p = cam.p.astype(np.float32)
    H, W = d.shape[:2]
    img = np.zeros((H, W, 3), np.float32)
    # sky
    vy = np.clip((d[..., 2] / np.linalg.norm(d, axis=2) + 0.05) / 0.5, 0, 1)[..., None]
    img[:] = np.float32([0.14, 0.07, 0.12]) * (1 - vy) + np.float32([0.02, 0.025, 0.06]) * vy
    tbest = np.full((H, W), np.inf, np.float32)
    # stands (billboards): far side y = STAND.far, ends x = left / right
    var = int(t * 5) % 2 + (2 if crowd_state > 0.5 else 0)
    for name, axis, val in (("far", 1, STAND["far"]), ("left", 0, STAND["left"]), ("right", 0, STAND["right"])):
        dd = d[..., axis]
        with np.errstate(divide="ignore", invalid="ignore"):
            tt = (val - p[axis]) / dd
        hit = (tt > 0) & np.isfinite(tt)
        Pz = p[2] + tt * d[..., 2]
        other = 0 if axis == 1 else 1
        Po = p[other] + tt * d[..., other]
        lo, hi = (-12.0, L_ + 12) if axis == 1 else (-12.0, W_ + 12)
        hit &= (Pz >= 0) & (Pz <= STAND_H) & (Po >= lo) & (Po <= hi) & (tt < tbest)
        if not hit.any(): continue
        tex = stand_tex(var, away_side=(name == "left"))
        th, tw = tex.shape[:2]
        s = (Po - lo) / TILE_M
        k = np.floor(s); fr = s - k
        fr = np.where((k % 2) == 1, 1 - fr, fr)                # mirror every other section
        if name == "right": fr = 1 - fr
        mx = (fr * (tw - 1)).astype(np.float32)
        my = ((1 - Pz / STAND_H) * (th - 1)).astype(np.float32)
        smp = cv2.remap(tex, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        fog = np.clip(tt / 160, 0, 0.25)[..., None]
        smp = smp * (1 - fog) + np.float32([0.05, 0.04, 0.07]) * fog
        img = np.where(hit[..., None], smp, img)
        tbest = np.where(hit, tt, tbest)
    # the ground
    with np.errstate(divide="ignore", invalid="ignore"):
        tg = -p[2] / d[..., 2]
    hitg = (d[..., 2] < 0) & (tg < tbest)
    tg = np.where(hitg, tg, 1e4).astype(np.float32)
    X = p[0] + tg * d[..., 0]; Y = p[1] + tg * d[..., 1]
    dn = np.linalg.norm(d, axis=2)
    graze = np.clip(-d[..., 2] / dn, 0.03, 1)
    fp = tg * dn / cam.fpx / np.sqrt(graze)
    stripe = (np.floor(X / 5.25) % 2).astype(np.float32)
    grass = np.float32([0.17, 0.43, 0.12])[None, None, :] * (0.93 + 0.12 * stripe)[..., None]
    # surround (off the pitch): darker, worn
    off = ((X < -2) | (X > L_ + 2) | (Y < -3) | (Y > W_ + 3)).astype(np.float32)[..., None]
    grass = grass * (1 - 0.35 * off)
    # floodlight pools: brighter in four soft pools
    pool = 0.9 + 0.12 * np.exp(-(((X - 26) / 30) ** 2 + ((Y - 34) / 40) ** 2)) + 0.12 * np.exp(-(((X - 79) / 30) ** 2 + ((Y - 34) / 40) ** 2))
    grass = grass * pool[..., None]
    ln = pitch_lines(X, Y, fp)[..., None]
    grass = grass * (1 - ln) + np.float32([0.9, 0.93, 0.88]) * ln
    # ad boards along the far touchline and behind the goals: a thin lit band just in front of the stands
    img = np.where(hitg[..., None], grass, img)
    if dof > 0.3:
        img = cv2.GaussianBlur(img, (0, 0), dof * E.RS)
    return img


# ---------------------------------------------------------------- goals, players, ball (drawn on top)
def goal_segments(gx, sgn):
    y0, y1, h, dep = W_ / 2 - 3.66, W_ / 2 + 3.66, 2.44, 1.6
    back = gx + sgn * dep
    posts = [((gx, y0, 0), (gx, y0, h)), ((gx, y1, 0), (gx, y1, h)), ((gx, y0, h), (gx, y1, h))]
    net = []
    for k in range(13):
        yy = y0 + (y1 - y0) * k / 12
        net += [((gx, yy, h), (back, yy, h * 0.75)), ((back, yy, h * 0.75), (back, yy, 0))]
    for k in range(1, 6):
        z = h * k / 6
        net += [((back, y0, z * 0.75), (back, y1, z * 0.75))]
    for k in range(1, 5):
        xx = gx + sgn * dep * k / 5
        net += [((xx, y0, h * (1 - 0.25 * k / 5)), (xx, y1, h * (1 - 0.25 * k / 5)))]
    for yy in (y0, y1):
        net += [((gx, yy, h), (back, yy, h * 0.75)), ((back, yy, h * 0.75), (back, yy, 0))]
    return posts, net


def draw_goal(img, cam, gx, sgn, bulge=0.0, by=34.0):
    posts, net = goal_segments(gx, sgn)
    lay = np.zeros(img.shape[:2], np.float32); col = np.zeros_like(img)
    def seg(a, b, w, c, alpha):
        pts, z = cam.project(np.float64([a, b]))
        if (z <= 0.5).any(): return
        k = cam.fpx / z.mean()
        th = max(1, int(round(w * k)))
        pa, pb = tuple(int(v * 4) for v in pts[0]), tuple(int(v * 4) for v in pts[1])
        cv2.line(lay, pa, pb, alpha, th, cv2.LINE_AA, 2)
        cv2.line(col, pa, pb, c, th, cv2.LINE_AA, 2)
    for a, b in net:
        if bulge > 0:        # the net billows where the ball hit
            def push(q):
                w_ = math.exp(-((q[1] - by) / 2.2) ** 2) * (q[2] / 2.44 + 0.3)
                return (q[0] + sgn * bulge * w_, q[1], q[2])
            a, b = push(a), push(b)
        seg(a, b, 0.025, (0.85, 0.86, 0.88), 0.55)
    for a, b in posts:
        seg(a, b, 0.12, (0.97, 0.97, 0.97), 1.0)
    al = np.clip(lay, 0, 1)[..., None]
    col = np.where(al > 0, col / np.maximum(lay[..., None], 1e-3), 0)
    return img * (1 - al) + np.clip(col, 0, 1) * al


HAIR = [(0.10, 0.08, 0.07), (0.86, 0.68, 0.36), (0.56, 0.27, 0.11), (0.27, 0.17, 0.10), (0.18, 0.12, 0.08)]
SKIN_K = [1.0, 0.86, 0.62, 0.45, 0.95]


@functools.lru_cache(maxsize=64)
def sprite(part, kit="home", h_px=140, look=-1):
    """a player drawing (cut part) scaled to h_px tall, recoloured for the kit: 'home' (United red), 'hull' (amber
    shirt, black shorts), 'gk_utd' (green), 'gk_hull' (blue). look >= 0 gives a generic player a hair colour and
    skin tone of his own (the Hull players are Maguire's flat drawings, so nobody recognisable plays for Hull).
    Returns premultiplied RGBA float, feet at the bottom."""
    a = cv2.imread(f"build/parts/{part}.png", cv2.IMREAD_UNCHANGED)
    a = cv2.cvtColor(a, cv2.COLOR_BGRA2RGBA).astype(np.float32) / 255
    ys, xs = np.nonzero(a[..., 3] > 0.3)
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    rgb = a[..., :3]; al = a[..., 3]
    hsv = cv2.cvtColor((rgb * 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    if look >= 0:
        Hh0 = al.shape[0]
        yr = np.arange(Hh0, dtype=np.float32)[:, None] / Hh0
        hair = (h >= 4) & (h <= 26) & (s > 70) & (v > 25) & (v < 165) & (yr < 0.2)
        skin = (h >= 4) & (h <= 26) & (s > 40) & (s < 175) & (v >= 150)
        hc = np.float32(HAIR[look % len(HAIR)])
        shade = (v / 120.0)[..., None]
        rgb = np.where(hair[..., None], np.clip(hc * shade, 0, 1), rgb)
        kk = SKIN_K[(look * 3 + 1) % len(SKIN_K)]
        tone = np.float32([1.0, 0.93, 0.88]) if kk < 0.7 else np.float32([1, 1, 1])
        rgb = np.where(skin[..., None], rgb * kk * tone, rgb)
    red = ((h < 8) | (h > 170)) & (s > 150) & (v > 90)
    white = (s < 40) & (v > 170)
    Hh = al.shape[0]
    yrel = np.arange(Hh, dtype=np.float32)[:, None] / Hh * np.ones((1, al.shape[1]), np.float32)
    shorts = white & (yrel > 0.45) & (yrel < 0.72)
    shirt = red & (yrel < 0.6)
    lum = (v / 255.0)[..., None]
    if kit == "hull":
        stripes = ((np.arange(al.shape[1])[None, :] // max(2, al.shape[1] // 10)) % 2).astype(np.float32)[..., None]
        amber = np.float32([0.98, 0.62, 0.04]) * (1 - 0.8 * stripes) + np.float32([0.08, 0.08, 0.09]) * 0.8 * stripes
        rgb = np.where(shirt[..., None], amber * (0.55 + 0.6 * lum), rgb)
        rgb = np.where(shorts[..., None], np.float32([0.09, 0.09, 0.1]) * (0.6 + 0.6 * lum), rgb)
    elif kit == "gk_utd":
        rgb = np.where(shirt[..., None], np.float32([0.15, 0.7, 0.35]) * (0.55 + 0.6 * lum), rgb)
    elif kit == "gk_hull":
        rgb = np.where(shirt[..., None], np.float32([0.2, 0.35, 0.85]) * (0.55 + 0.6 * lum), rgb)
    k = h_px / al.shape[0]
    img = np.dstack([rgb * al[..., None], al]).astype(np.float32)
    img = cv2.resize(img, (max(2, int(round(al.shape[1] * k))), int(h_px)), interpolation=cv2.INTER_AREA)
    return img


def draw_players(img, cam, players, t, dof_players=0.0):
    """players: list of dict(x, y, part, kit, flip, jump=0, lean=0). Far ones first."""
    items = []
    for pl in players:
        pts, z = cam.project([(pl["x"], pl["y"], pl.get("z", 0.0)), (pl["x"], pl["y"], pl.get("z", 0.0) + 1.85)])
        if z[0] <= 1: continue
        items.append((z[0], pl, pts))
    items.sort(key=lambda q: -q[0])
    H, W = img.shape[:2]
    for z, pl, pts in items:
        foot, head = pts
        hpx = foot[1] - head[1]
        if hpx < 4 or foot[0] < -200 or foot[0] > W + 200: continue
        hq = int(max(8, min(900, round(hpx / 4) * 4)))
        spr = sprite(pl["part"], pl.get("kit", "home"), hq, pl.get("look", -1))
        sc = hpx / hq
        if pl.get("flip"): spr = spr[:, ::-1]
        sh, sw = spr.shape[:2]
        # shadow on the grass (floodlights: soft, slightly offset)
        gpts, _ = cam.project([(pl["x"] + 0.3, pl["y"] + 0.35, 0.0)])
        sx, sy = gpts[0]
        rr = max(2, int(0.33 * sw * sc))
        sh_l = np.zeros((H, W), np.float32)
        cv2.ellipse(sh_l, (int(sx), int(sy)), (rr, max(1, rr // 3)), 0, 0, 360, 0.45, -1, cv2.LINE_AA)
        img = img * (1 - sh_l[..., None])
        A = np.float32([[sc, 0, foot[0] - sc * sw / 2], [0, sc, foot[1] - sc * sh]])
        if pl.get("lean"):
            R = cv2.getRotationMatrix2D((float(foot[0]), float(foot[1])), pl["lean"], 1.0)
            A = (np.vstack([R, [0, 0, 1]]) @ np.vstack([A, [0, 0, 1]]))[:2].astype(np.float32)
        lay = np.zeros((H, W, 4), np.float32)
        E.warp_into(lay, spr, A)
        img = img * (1 - lay[..., 3:4]) + lay[..., :3]
    return img


def draw_ball(img, cam, pos, trail=()):
    pts, z = cam.project([pos, (pos[0], pos[1], 0.0)])
    if z[0] <= 0.5: return img
    r = max(2.0, 0.11 * cam.fpx / z[0])
    H, W = img.shape[:2]
    lay = np.zeros((H, W), np.float32); sh = np.zeros((H, W), np.float32)
    cv2.ellipse(sh, (int(pts[1][0] * 4), int(pts[1][1] * 4)), (int(r * 4), int(r * 1.3)), 0, 0, 360, 0.4, -1, cv2.LINE_AA, 2)
    for k, q in enumerate(trail):                      # a faint motion trail
        tp, tz = cam.project([q])
        if tz[0] > 0.5:
            cv2.circle(lay, (int(tp[0][0] * 4), int(tp[0][1] * 4)), int(r * 4 * (0.4 + 0.5 * k / max(1, len(trail)))),
                       0.12 + 0.25 * k / max(1, len(trail)), -1, cv2.LINE_AA, 2)
    cv2.circle(lay, (int(pts[0][0] * 4), int(pts[0][1] * 4)), int(r * 4), 1.0, -1, cv2.LINE_AA, 2)
    img = img * (1 - sh[..., None])
    a = np.clip(lay, 0, 1)[..., None]
    return img * (1 - a) + np.float32([0.97, 0.97, 0.95]) * a


def render(cam, t, players=(), ball=None, trail=(), crowd=0.0, bulge=0.0, bulge_y=34.0, dof=0.0):
    img = background(cam, t, crowd, dof=dof)
    for gx, sgn in ((0.0, -1), (L_, 1)):
        img = draw_goal(img, cam, gx, sgn, bulge if gx == L_ else 0.0, bulge_y)
    img = draw_players(img, cam, players, t)
    if ball is not None:
        img = draw_ball(img, cam, ball, trail)
    return img

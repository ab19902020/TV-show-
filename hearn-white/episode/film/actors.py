"""The Undercard's people and props in a set: the engine's "world" shot with one ("props", "scene") layer that draws
everything a shot lists in s["cast"], in depth order. Whole drawings only (studio.film.art): poses change on a beat,
walks cycle the sheet's eight walk drawings while the feet move along a path, a tumble rotates a whole drawing
through the air; faces act through the engine (perf.py: lip sync, blinks, eyes, brows, head).

A cast item is a dict. People:
  who        perf name (eddie, dana, tyson, joshua, announcer, referee, attendant, security)
  pose       a drawing name, or [(t, name), ...] (the drawing from that time on)
  at         feet in 1x plate px, or [(t, (x, y)), ...] (linear between keys; ease=True eases them)
  walk       dict(frames=[...], cycle=s, t0, t1): the walk drawings cycled while t0 <= t < t1
  mirror     flipped (a right-facing drawing walking left), or [(t, bool), ...]
  rot        degrees about the feet, or [(t, deg), ...] (eased): leans, the tumble, a wobble
  scale      x the true size; dy: [(t, plate px)] lift (eased) for a hop or a sink
  clip       plate y below which the drawing fades out (into the trolley); show: [(t0, t1)] visible spans
  look       a fixed gaze target for this shot (else perf.py's)
Props: prop=<library/props/hearn-white name>, at (bottom centre), h (plate px), rot, mirror, dy, clip, show.
Code-drawn things: fn=<things.py function>, called with (layer, item, t, M, sc).
z orders the items (default: feet y; larger is nearer)."""
import functools
import importlib
import math

import cv2
import numpy as np

from studio.film import engine as E
from studio.film.cast import CAST
from studio.film.engine import OH, OW, RS
from studio.paths import BUILD, LIBRARY

from film import eyes, mouths, noses

eyes.install()
mouths.install()
noses.install()


def _install_camera():
    """camera shake and snap zooms for the fight: a shot's "shakes" [(t, px, s)] shake the camera (screen px,
    decaying), its "kicks" [(t, factor, s)] snap the camera in and ease it back"""
    from studio.film import render as R
    if getattr(R, "_undercard_cam", False):
        return
    orig = R.cam_at

    def cam_at(s, t):
        ks = s.get("cams")
        if s.get("linear") and ks and len(ks) > 1:              # a tracking shot keeping pace with a move
            k = max([i for i, (tk, _) in enumerate(ks) if tk <= t] or [0])
            if k + 1 < len(ks) and t >= ks[0][0]:
                u = min(1.0, max(0.0, (t - ks[k][0]) / max(1e-3, ks[k + 1][0] - ks[k][0])))
                cx, cy, z = (a + (b - a) * u for a, b in zip(ks[k][1], ks[k + 1][1]))
            else:
                cx, cy, z = ks[k][1] if t >= ks[0][0] else ks[0][1]
        else:
            cx, cy, z = orig(s, t)
        for t0, amp, dur in s.get("shakes", ()):
            u = (t - t0) / dur
            if 0 <= u < 1:
                rng = np.random.default_rng(int(t * 30) + int(t0 * 1000))
                k = amp * (1 - u) ** 1.5 / (OW / 1672.0 * z)
                cx += rng.uniform(-1, 1) * k
                cy += rng.uniform(-1, 1) * k
        for t0, f, dur in s.get("kicks", ()):
            u = (t - t0) / dur
            if 0 <= u < 1:
                z *= 1 + (f - 1) * (min(1.0, u * 8) * (1 - u) ** 2)
        return cx, cy, z

    R.cam_at = cam_at
    R._undercard_cam = True

# who -> (character id, height cm, standing height of the reference drawing in sheet px)
PEOPLE = {"eddie": ("eddie-hearn", 191, 357), "dana": ("dana-white", 170, 347), "tyson": ("tyson-fury", 206, 431),
          "joshua": ("anthony-joshua", 198, 513), "announcer": ("ring-announcer", 175, 347),
          "referee": ("boxing-referee", 180, 336), "attendant": ("laundry-attendant", 160, 376),
          "security": ("security-guard", 183, 429)}
# the sheets draw a character at different sizes: sheet px of the casual sheet per sheet px of this one
SHEET = {"eddie_boxing": 1.02, "eddie_walk": 0.768, "dana_boxing": 1.0, "dana_laundry": 0.87, "dana_walk": 0.737}


def sm(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def at_time(v, t, ease=True):
    """a value or [(t, value), ...]: the keyed value at t (numbers and tuples interpolate, others step)"""
    if not isinstance(v, list):
        return v
    if t <= v[0][0]:
        return v[0][1]
    for (t0, a), (t1, b) in zip(v, v[1:]):
        if t0 <= t < t1:
            if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)):
                u = (t - t0) / max(1e-6, t1 - t0)
                return a + (b - a) * (sm(u) if ease else u)
            if isinstance(a, tuple) and isinstance(b, tuple):
                u = (t - t0) / max(1e-6, t1 - t0)
                u = sm(u) if ease else u
                return tuple(p + (q - p) * u for p, q in zip(a, b))
            return a
    return v[-1][1]


def visible(it, t):
    sh = it.get("show")
    return sh is None or any(a <= t < b for a, b in sh)


def key_of(who, name):
    return f"{PEOPLE[who][0]}:{name}"


# single drawings drawn at their own size (the peek is a close-up of the head over the trolley's rim)
DRAWING = {"dana-white:peek": 0.40}


def sheet_fac(key):
    if key in DRAWING:
        return DRAWING[key]
    cid, name = key.split(":")
    if name.startswith("bust_"):
        return bust_geom(key)[0]
    if name.startswith("pair_"):
        return PAIR_FAC * (PAIR_WHO[cid] if cid in PAIR_WHO else 1.0)
    sheet = CAST.spec(cid)["drawings"][name].get("sheet", "")
    stem = sheet.split("/")[-2] if "/cuts/" in sheet else sheet.split("/")[-1].replace("-clean.png", "")
    return SHEET.get(stem, 1.0)


@functools.lru_cache(maxsize=512)
def feet_mid(key):
    """where a drawing stands (sheet px): halfway between its feet (the middle of the bottom 12 % of the figure)
    and its lowest point. The engine's foot finder takes the lowest sole only, which in a boxing stance (one boot
    lower than the other) puts the anchor on one foot and makes the body jump sideways between poses.
    A close-up bust stands on the feet its body would have; both halves of a two-person drawing on one point"""
    name = key.split(":")[1]
    if name.startswith("bust_"):
        return bust_geom(key)[1]
    if name.startswith("pair_"):
        return PAIRS[name[5:]]
    d, _ = CAST.get(key)
    a = d.u8[1.0][..., 3] > 128
    ys, xs = np.nonzero(a)
    top, bot = ys.min(), ys.max()
    band = ys > bot - 0.12 * (bot - top)
    x = (xs[band].min() + xs[band].max()) / 2.0
    return (float(x / d.S + d.ox), float(bot / d.S + d.oy))


# ---------------------------------------------------------------- v5: busts and two-person drawings
# The acting heads (reference/cuts/acting_heads, bust_*) are drawn far larger than the full figures' heads: in a
# close-up a bust stands in for its character, its head the size and in the place the standing figure's head would
# be (from the head marks of the bust and of the figure's "front" drawing), so a cut from a medium shot to a
# close-up keeps the eyeline and the screen position.
BUST_REF = {}                                   # character -> the standing drawing a bust is matched to


@functools.lru_cache(maxsize=64)
def bust_geom(key):
    """-> (sheet factor, feet (bust px)) of a bust drawing"""
    cid, name = key.split(":")
    rk = f"{cid}:{BUST_REF.get(cid, 'front')}"
    rd, _ = CAST.get(rk)
    bd, _ = CAST.get(key)
    rh, bh = rd.spec["head"], bd.spec["head"]
    sf = sheet_fac(rk)
    f = (rh[3] - rh[1]) * sf / (bh[3] - bh[1])
    rfx, rfy = feet_mid(rk)
    rcx, rcy = (rh[0] + rh[2]) / 2, (rh[1] + rh[3]) / 2
    bcx, bcy = (bh[0] + bh[2]) / 2, (bh[1] + bh[3]) / 2
    return f, (bcx + (rfx - rcx) * sf / f, bcy + (rfy - rcy) * sf / f)


# The paired fight drawings (reference/cuts/pairs, pair_*: a jab landing on a guard each way, the glove clash, the
# clinch) are split into an Eddie layer and a Dana layer on one canvas; both are drawn on the same point at the
# same scale, so together they are the drawing, and each speaks with its own face. PAIRS: that point (canvas px,
# the middle of the pair's feet); PAIR_FAC: canvas px -> Eddie's casual-sheet px (the pair sheet draws them a
# little less big-headed than the boxing sheet: matched between head size and height); Dana's layer is drawn by
# Dana's height, so his factor carries the ratio of their heights back out.
PAIRS = {"tap_e": (264.5, 485.0), "tap_d": (261.5, 480.0), "clash": (299.0, 501.0), "clinch": (208.0, 496.0)}
PAIR_FAC = 0.92
PAIR_WHO = {"dana-white": (191 / 357) / (170 / 347)}


def ppc(s, y):
    """plate px per cm at floor height y (the shot's perspective: s["ppc"] = (horizon y, k))"""
    hz, k = s["ppc"]
    return max(0.05, (y - hz) * k)


def walk_at(it, t):
    """the walk (a dict, or one of a list of them) going on at t, or None"""
    ws = it.get("walk")
    for w in (ws if isinstance(ws, list) else [ws] if ws else []):
        if w.get("t0", -1e9) <= t < w.get("t1", 1e9):
            return w
    return None


def pose_at(it, t):
    w = walk_at(it, t)
    if w:
        fr = w["frames"]
        i = int(math.floor((t - w.get("t0", 0.0)) / w["cycle"] * len(fr))) % len(fr)
        return fr[i]
    return at_time(it["pose"], t)


def resolver(s, who, pos):
    def res(g):
        if g == "cam":
            return (0.0, 0.0, 0.0)
        if g == "down":
            return (0.05, 0.85, 0.0)
        if isinstance(g, tuple) and g[0] == "dir":
            return g[1:]
        if g in pos and who in pos:
            dx = pos[g][0] - pos[who][0]
            dy = pos[g][1] - pos[who][1]
            if abs(dx) < 1:
                return (0.0, 0.05, 0.0)
            sgn = 1.0 if dx > 0 else -1.0
            return (0.85 * sgn, float(np.clip(dy / (abs(dx) + 200.0), -0.3, 0.7)), 0.3 * sgn)
        return (0.0, 0.05, 0.0)
    return res


PHASE = {w: i * 1.618 for i, w in enumerate(PEOPLE)}
STILL_POSES = {"seated", "prone", "tumble1", "tumble2", "tumble3", "hug", "hug2", "crawl"}


def life(it, key, t):
    """what keeps a standing person alive between their poses -> (degrees, x scale, y scale) about the feet:
    breathing (a 0.7 % rise every 3.4 s, each on their own rhythm), a slow shift of weight from foot to foot, and
    the settle when a pose lands: a quick stretch that overshoots once and comes to rest in a quarter second"""
    if it.get("still") or key.split(":")[1] in STILL_POSES or key.split(":")[1].startswith("pair_"):
        return 0.0, 1.0, 1.0
    ph = PHASE[it["who"]]
    b = math.sin(2 * math.pi * t / 3.4 + ph)
    rot = 0.45 * math.sin(2 * math.pi * t / 5.3 + 2 * ph)
    sy, sx = 1 + 0.007 * b, 1 - 0.0025 * b
    pose = it.get("pose")
    walking = walk_at(it, t) is not None
    if isinstance(pose, list) and not walking:
        past = [k for (k, v), (_, pv) in zip(pose[1:], pose[:-1]) if k <= t and v != pv]
        if past and t - max(past) < 0.3:
            u = t - max(past)
            st = 0.035 * math.exp(-u / 0.075) * math.cos(u * 2 * math.pi / 0.24)
            sy *= 1 + st
            sx *= 1 - 0.5 * st
    try:                                                  # talking: the body rides the voice a little (a cartoon
        perf = importlib.import_module("film.perf").PERF  # show's talking bounce), more on the open sounds
        f = int(round(t * 30))
        if 0 <= f < len(perf.TALK[it["who"]]) and perf.TALK[it["who"]][f] and perf.VIS[it["who"]][f] not in ("REST", "MBP"):
            a = float(perf.AMP[it["who"]][f])
            sy *= 1 + 0.010 * (a - 0.4)
            rot += 0.35 * math.sin(t * 9.0 + ph)
    except (KeyError, ImportError, AttributeError):
        pass
    if it.get("steps"):                                   # walking in one drawing (pushing the trolley): a step
        x0, _ = at_time(it["at"], t - 0.05, it.get("ease", False))     # every 0.42 s while the feet are moving,
        x1, _ = at_time(it["at"], t + 0.05, it.get("ease", False))     # the body rising and rocking with it
        if abs(x1 - x0) > 0.5:
            u = t / 0.42
            rot += 1.6 * math.sin(math.pi * u)
            sy *= 1 + 0.018 * abs(math.sin(math.pi * u))
    return rot, sx, sy


def person_matrix(s, it, key, t, M, sc):
    who = it["who"]
    cm, stand = PEOPLE[who][1], PEOPLE[who][2]
    x, y = at_time(it["at"], t, it.get("ease", False))
    dy = at_time(it.get("dy", 0.0), t)
    h = cm * ppc(s, it.get("floor", y)) * it.get("scale", 1.0)               # plate px tall
    b = it.get("bounce")
    if b and key.split(":")[1] in b["poses"]:                                # a boxer's bounce on his toes
        ph = PHASE[who]
        dy += b["amp"] * h * abs(math.sin(math.pi * b["hz"] * t + ph))
    k = h * sc / stand * sheet_fac(key)                                      # screen px per sheet px
    fx, fy = feet_mid(key)
    Fx, Fy = M[0, 0] * x + M[0, 2], M[1, 1] * (y - dy) + M[1, 2]
    mir = at_time(it.get("mirror", False), t)
    sx = -k if mir else k
    lr, lx, ly = life(it, key, t)
    th = math.radians(at_time(it.get("rot", 0.0), t) + lr)
    c, sn = math.cos(th), math.sin(th)
    A = np.array([[c * sx * lx, -sn * k * ly], [sn * sx * lx, c * k * ly]])
    off = np.array([Fx, Fy]) - A @ np.array([fx, fy])
    return np.hstack([A, off[:, None]]), mir, (Fx, Fy), h * sc


@functools.lru_cache(maxsize=64)
def prop_rgba(name):
    """a prop from the pack (library/props/hearn-white), upscaled 4x once (build/props/), premultiplied float"""
    out = BUILD / "props" / f"{name}.png"
    if not out.exists():
        from studio.film.art import upscale_rgba
        src = cv2.cvtColor(cv2.imread(str(LIBRARY / "props" / "hearn-white" / f"{name}.png"), cv2.IMREAD_UNCHANGED),
                           cv2.COLOR_BGRA2RGBA)
        out.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(out), cv2.cvtColor(upscale_rgba(src), cv2.COLOR_RGBA2BGRA))
    im = cv2.cvtColor(cv2.imread(str(out), cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA).astype(np.float32) / 255.0
    im[..., :3] *= im[..., 3:4]
    return im


def place_rgba(lay, im, A, clip_rows=None):
    """premultiplied RGBA image through A (image px -> screen px), over lay"""
    if clip_rows is not None:
        im = im.copy()
        yy = np.arange(im.shape[0], dtype=np.float32)[:, None]
        im *= np.clip(1 - (yy - clip_rows) / 6.0, 0, 1)[..., None]
    E.warp_into(lay, im, np.float32(A))


def draw_prop(lay, s, it, t, M, sc):
    im = prop_rgba(it["prop"])
    ih, iw = im.shape[:2]
    x, y = at_time(it["at"], t, it.get("ease", False))
    y = y - at_time(it.get("dy", 0.0), t)
    if isinstance(it["at"], list) and it["prop"].startswith(("trolley", "towel-pile")):   # rolling: the wobbly
        xa = at_time(it["at"], t - 0.05, it.get("ease", False))[0]                          # wheel rattles it
        xb = at_time(it["at"], t + 0.05, it.get("ease", False))[0]
        if abs(xb - xa) > 0.5:
            y -= 0.006 * it["h"] * (math.sin(2 * math.pi * 7.3 * t) + 0.5 * math.sin(2 * math.pi * 11.1 * t))
    h = at_time(it["h"], t) * sc
    k = h / ih
    mir = it.get("mirror", False)
    sx = -k if mir else k
    th = math.radians(at_time(it.get("rot", 0.0), t))
    c, sn = math.cos(th), math.sin(th)
    A = np.array([[c * sx, -sn * k], [sn * sx, c * k]])
    piv = np.array([iw / 2, ih * it.get("pivot", 1.0)])
    S = np.array([M[0, 0] * x + M[0, 2], M[1, 1] * y + M[1, 2]]) - np.array([0, h * (1 - it.get("pivot", 1.0))])
    off = S - A @ piv
    clip = None
    if it.get("clip") is not None:
        clip = (it["clip"] - (y - h / sc)) / (h / sc) * ih
    place_rgba(lay, im, np.hstack([A, off[:, None]]), clip)


@functools.lru_cache(maxsize=16)
def front_layer(key):
    """the part of a drawing that is in front of its own face (a microphone held at the lips), cut from the
    drawing itself: film.yaml front_poly (sheet px) -> (premultiplied RGBA at part px, its corner in sheet px)"""
    cid, name = key.split(":")
    poly = CAST.spec(cid)["drawings"][name].get("front_poly")
    if not poly:
        return None
    d, _ = CAST.get(key)
    im = d.u8[1.0]
    P = (np.float32(poly) - [d.ox, d.oy]) * d.S
    x0, y0 = np.floor(P.min(0)).astype(int) - 2
    x1, y1 = np.ceil(P.max(0)).astype(int) + 2
    x0, y0 = max(0, x0), max(0, y0)
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillPoly(m, [np.int32(np.round((P - [x0, y0]) * 4))], 255, cv2.LINE_AA, 2)
    m = cv2.GaussianBlur(m, (0, 0), 1.0).astype(np.float32) / 255
    c = im[y0:y1, x0:x1].astype(np.float32) / 255
    c[..., 3] *= m[:c.shape[0], :c.shape[1]]
    c[..., :3] *= c[..., 3:4]
    return c, (x0 / d.S + d.ox, y0 / d.S + d.oy), d.S


@functools.lru_cache(maxsize=256)
def head_point(key):
    """the head of a drawing (sheet px): its marked head box's centre and radius, or, for a drawing with no face
    marks (arms up), the top of the figure's middle third"""
    d, _ = CAST.get(key)
    hb = d.spec.get("head")
    if hb:
        return ((hb[0] + hb[2]) / 2, (hb[1] + hb[3]) / 2, 0.5 * max(hb[2] - hb[0], hb[3] - hb[1]))
    a = d.u8[1.0][..., 3] > 128
    ys, xs = np.nonzero(a)
    fx, _ = feet_mid(key)
    cx = (fx - d.ox) * d.S
    band = np.abs(xs - cx) < 0.08 * (xs.max() - xs.min())
    top = ys[band].min()
    hgt = ys.max() - ys.min()
    r = 0.085 * hgt
    return (cx / d.S + d.ox, (top + r) / d.S + d.oy, r / d.S)


def scene(img, s, t, M, sc):
    """("props", "scene"): everything in s["cast"] at time t, far to near"""
    from studio.film import render as R
    _install_camera()                    # (render is fully loaded by the first frame; the patch is for the next one)
    perf = importlib.import_module("film.perf")
    things = importlib.import_module("film.things")
    items = [it for it in s["cast"] if visible(it, t)]
    pos = {}
    for it in items:
        if "who" in it:
            x, y = at_time(it["at"], t, it.get("ease", False))
            h = PEOPLE[it["who"]][1] * ppc(s, y)
            pos[it["who"]] = (M[0, 0] * x + M[0, 2], M[1, 1] * (y - 0.93 * h) + M[1, 2])
    items.sort(key=lambda it: it.get("z", at_time(it["at"], t)[1] if "at" in it else 0.0))
    for fl in s.get("flashes", ()):                                     # press camera flashes in the crowd
        img = things.flashes(img, s, t, M, sc, fl[0], fl[1], seed=fl[2] if len(fl) > 2 else 1)
    lay = np.zeros((OH, OW, 4), np.float32)
    s["_heads"] = {}
    s["_M"] = M
    for it in items:
        if "fn" in it:
            getattr(things, it["fn"])(lay, s, it, t, M, sc)
        elif "prop" in it:
            draw_prop(lay, s, it, t, M, sc)
        else:
            key = key_of(it["who"], pose_at(it, t))
            d, info = CAST.get(key)
            Ms, mir, F, Hs = person_matrix(s, it, key, t, M, sc)
            st = {}
            if d.has_face and not CAST.spec(key.split(":")[0])["drawings"][key.split(":")[1]].get("plain"):
                look = at_time(it.get("look"), t)
                res = resolver(s, it["who"], pos)
                st = perf.PERF.state(it["who"], t, (lambda g, r=res, lk=look: r(lk if lk is not None else g)),
                                     s["t"])
                for kf in it.get("face", []):                    # this shot's own face: (t0, t1, brow, smile)
                    if kf[0] <= t < kf[1]:
                        st["brow"], st["smile"] = kf[2], kf[3]
                st = R.face_state(st, info, mir)
            clip = None
            cl = at_time(it.get("clip"), t)
            if cl is not None:                                     # plate y -> sheet y (no rotation assumed)
                cy_screen = M[1, 1] * cl + M[1, 2]
                clip = (cy_screen - Ms[1, 2]) / Ms[1, 1]
            if it.get("shadow", True) and cl is None:
                things.contact_shadow(lay, s, it, t, M, sc, F, Hs, at_time(it.get("dy", 0.0), t))
            E.place(lay, d, st, Ms, clip=clip, alpha=it.get("alpha", 1.0))
            hx, hy, hr = head_point(key)
            fx_, fy_ = feet_mid(key)
            T_ = lambda x, y: (Ms[0, 0] * x + Ms[0, 1] * y + Ms[0, 2], Ms[1, 0] * x + Ms[1, 1] * y + Ms[1, 2])
            (HX, HY), (FX, FY) = T_(hx, hy), T_(fx_, fy_)
            n_ = max(1e-3, float(np.hypot(HX - FX, HY - FY)))
            s["_heads"][it["who"]] = (HX, HY, hr * float(np.hypot(Ms[0, 0], Ms[1, 0])), ((HX - FX) / n_, (HY - FY) / n_))
            s.setdefault("_mats", {})[it["who"]] = (Ms, key)
            fr = front_layer(key)
            if fr is not None:                                     # the mic back over the moving mouth
                c, (sx0, sy0), S_ = fr
                Af = np.hstack([Ms[:, :2] / S_, (Ms[:, :2] @ np.float64([sx0, sy0]) + Ms[:, 2])[:, None]])
                E.warp_into(lay, c, np.float32(Af))
            for hd in it.get("holds", ()):                             # a prop in the hand: its grip at a sheet point
                if hd["t0"] <= t < hd["t1"]:
                    gx = Ms[0, 0] * hd["at"][0] + Ms[0, 1] * hd["at"][1] + Ms[0, 2]
                    gy = Ms[1, 0] * hd["at"][0] + Ms[1, 1] * hd["at"][1] + Ms[1, 2]
                    im = prop_rgba(hd["prop"])
                    k = hd["h"] * sc / im.shape[0]
                    gp = hd.get("grip", (0.5, 0.08))
                    th = math.radians(hd.get("rot", 0.0))
                    c, sn = math.cos(th), math.sin(th)
                    A = np.array([[c * k, -sn * k], [sn * k, c * k]])
                    off = np.array([gx, gy]) - A @ np.array([gp[0] * im.shape[1], gp[1] * im.shape[0]])
                    place_rgba(lay, im, np.hstack([A, off[:, None]]))
    lay = light(lay, s, sc)
    img = img * (1 - lay[..., 3:4]) + lay[..., :3]
    img = stage_light(img, s, t, M, sc)
    for t0, dur in s.get("white", ()):                          # a white impact frame, gone in a few frames
        u = (t - t0) / dur
        if 0 <= u < 1:
            img = img + (1 - img) * (0.85 * (1 - u) ** 1.5)
    return img


# ---------------------------------------------------------------- the people lit by the set they stand in
# Each set's light falls on the people and props in it, so they sit in the painting instead of on top of it:
#   amb   the room's colour over everything (rgb multiplier mixed in by `amt`) and its exposure `exp`
#   rims  light from the set's lamps catching the edges that face them: (direction the light comes from (x, y),
#         colour, strength); the band runs inside the ink outline (dark ink stays ink)
LIGHT = {
    "P": dict(amb=(0.97, 0.98, 1.05), amt=0.35, exp=1.0,
              rims=[((-0.4, -1.0), (1.0, 0.93, 0.80), 0.30), ((1.0, -0.2), (0.45, 0.58, 1.0), 0.28)]),
    "B": dict(amb=(0.80, 0.90, 1.14), amt=0.45, exp=0.86,
              rims=[((1.0, -0.35), (1.0, 0.62, 0.28), 0.55), ((-1.0, -0.6), (0.40, 0.55, 1.0), 0.40)]),
    "C": dict(amb=(1.10, 0.96, 0.84), amt=0.38, exp=0.97,
              rims=[((0.25, -1.0), (1.0, 0.84, 0.58), 0.38), ((1.0, 0.0), (1.0, 0.42, 0.25), 0.26),
                    ((-1.0, -0.3), (1.0, 0.70, 0.40), 0.18)]),
    "D": dict(amb=(1.12, 0.93, 0.86), amt=0.38, exp=0.95,
              rims=[((0.0, -1.0), (1.0, 0.80, 0.55), 0.40), ((-1.0, -0.2), (1.0, 0.32, 0.25), 0.30)]),
    "E": dict(amb=(0.90, 0.95, 1.12), amt=0.38, exp=0.95,
              rims=[((0.0, -1.0), (1.0, 0.85, 0.65), 0.38), ((1.0, -0.2), (0.35, 0.50, 1.0), 0.34)]),
    "A": dict(amb=(0.96, 0.95, 1.06), amt=0.25, exp=1.0,
              rims=[((-1.0, -0.4), (1.0, 0.28, 0.25), 0.50), ((1.0, -0.4), (0.30, 0.45, 1.0), 0.50),
                    ((0.0, -1.0), (1.0, 1.0, 1.0), 0.22)]),
    "R": dict(amb=(0.96, 0.95, 1.06), amt=0.25, exp=1.0,
              rims=[((-1.0, -0.4), (1.0, 0.28, 0.25), 0.45), ((1.0, -0.4), (0.30, 0.45, 1.0), 0.45),
                    ((0.0, -1.0), (1.0, 1.0, 1.0), 0.22)]),
    "S": dict(amb=(0.97, 0.95, 1.05), amt=0.25, exp=0.98,
              rims=[((-1.0, -0.5), (1.0, 0.30, 0.28), 0.40), ((1.0, -0.5), (0.30, 0.45, 1.0), 0.40),
                    ((0.0, -1.0), (1.0, 1.0, 1.0), 0.20)]),
    # v5: the service hall (sodium lamps on red walls), the red corner (the rig white, red left, blue right), and
    # inside the bin (dark, the light only from the lid's gap above)
    "Q": dict(amb=(1.12, 0.94, 0.82), amt=0.40, exp=0.96,
              rims=[((0.0, -1.0), (1.0, 0.86, 0.62), 0.40), ((-1.0, -0.3), (1.0, 0.38, 0.22), 0.30),
                    ((1.0, -0.3), (1.0, 0.55, 0.30), 0.24)]),
    "K": dict(amb=(0.94, 0.96, 1.08), amt=0.25, exp=1.0,
              rims=[((-1.0, -0.4), (1.0, 0.28, 0.25), 0.50), ((1.0, -0.4), (0.30, 0.45, 1.0), 0.45),
                    ((0.0, -1.0), (1.0, 1.0, 1.0), 0.24)]),
    "I": dict(amb=(0.72, 0.70, 0.78), amt=0.55, exp=0.72,
              rims=[((0.0, -1.0), (1.0, 0.86, 0.60), 0.55)]),
}


def _shift(a, dx, dy):
    return cv2.warpAffine(a, np.float32([[1, 0, -dx], [0, 1, -dy]]), (a.shape[1], a.shape[0]),
                          flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def light(lay, s, sc):
    g = LIGHT.get(s.get("plate"))
    a = lay[..., 3]
    if not g or a.max() <= 0.0:
        return lay
    ys, xs = np.nonzero(a > 0.002)
    y0, y1, x0, x1 = max(0, ys.min() - 2), min(a.shape[0], ys.max() + 3), max(0, xs.min() - 2), min(a.shape[1], xs.max() + 3)
    sub = lay[y0:y1, x0:x1]
    al = sub[..., 3].copy()
    rgb = sub[..., :3] * ((1 - g["amt"]) + g["amt"] * np.float32(g["amb"])) * g["exp"]
    col = rgb / np.maximum(al, 1e-4)[..., None]                          # straight colour: ink is dark
    lit = np.clip((col.max(2) - 0.09) / 0.14, 0, 1)
    k = OH / 1080.0 * float(np.clip(9.0 * sc / (OW / 1672.0), 5.0, 22.0))   # the band, screen px
    for (dx, dy), c, st in g["rims"]:
        n = math.hypot(dx, dy)
        sh = _shift(al, dx / n * k, dy / n * k)
        rim = np.clip(al - sh, 0, 1)
        rim = cv2.GaussianBlur(rim, (0, 0), 0.3 * k) * lit * al
        add = rim[..., None] * np.float32(c) * min(1.0, st * 1.6)
        rgb = rgb + add * (al[..., None] - rgb)                         # screen, premultiplied
    lay[y0:y1, x0:x1, :3] = np.clip(rgb, 0, al[..., None])
    return lay



# ---------------------------------------------------------------- arena lighting: dramatic lights over pathetic action
# pool: (centre x, y, radius x, y in plate px, brighten, darken outside); beams: (top x, floor x, floor y, width at
# the floor) from the rig above; haze: glow added under the rig; bloom: the brights glowing
STAGE = {
    "R": dict(pool=(836, 800, 820, 240, 0.16, 0.30), haze=0.06, bloom=0.22,
              beams=[(260, 520, 880, 360), (620, 760, 880, 300), (1060, 920, 880, 300), (1420, 1160, 880, 360)]),
    "A": dict(pool=(836, 640, 560, 120, 0.14, 0.24), haze=0.05, bloom=0.20,
              beams=[(420, 640, 650, 200), (836, 836, 650, 220), (1250, 1030, 650, 200)]),
    "S": dict(pool=(836, 900, 900, 320, 0.08, 0.16), haze=0.03, bloom=0.16, beams=[]),
    "K": dict(pool=(760, 760, 760, 260, 0.14, 0.26), haze=0.05, bloom=0.20,
              beams=[(380, 520, 900, 380), (900, 860, 900, 340), (1400, 1180, 900, 380)]),
}


def _cone(h, w, pts, blur):
    m = np.zeros((h, w), np.float32)
    cv2.fillPoly(m, [np.int32(np.round(pts))], 1.0, cv2.LINE_AA)
    return cv2.GaussianBlur(m, (0, 0), blur)


def stage_light(img, s, t, M, sc):
    g = STAGE.get(s.get("plate"))
    if not g:
        return img
    H, W = img.shape[:2]
    q = 4                                                       # light computed at a quarter of the frame size
    h, w = H // q, W // q
    P = lambda x, y: ((M[0, 0] * x + M[0, 2]) / q, (M[1, 1] * y + M[1, 2]) / q)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy, rx, ry, up, down = g["pool"]
    (X, Y), k = P(cx, cy), M[0, 0] / q
    r2 = ((xx - X) / (rx * k)) ** 2 + ((yy - Y) / (ry * k)) ** 2
    pool = np.exp(-r2 * 1.2)
    lit = 1 - down + (down + up) * pool                          # brighter in the pool, darker away from it
    beams = np.zeros((h, w), np.float32)
    for i, (tx, fx, fy, fw) in enumerate(g["beams"]):
        sway = 18 * math.sin(0.35 * t + 1.7 * i)
        a, b = P(tx, -80), P(fx + sway, fy)
        hw = 0.5 * fw * k
        pts = [(a[0] - 0.08 * hw, a[1]), (a[0] + 0.08 * hw, a[1]), (b[0] + hw, b[1]), (b[0] - hw, b[1])]
        fade = np.clip(1 - (yy - a[1]) / max(1.0, b[1] - a[1]), 0, 1) ** 0.6
        beams += _cone(h, w, pts, max(2.0, 0.25 * hw)) * fade * (0.8 + 0.2 * math.sin(1.3 * t + i))
    beams = np.clip(beams, 0, 1.2)
    haze = g["haze"] * np.clip(1 - yy / (0.55 * h), 0, 1)
    up_ = lambda a: cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)
    img = img * up_(lit)[..., None]
    img = img + (1 - img) * (0.16 * up_(beams) + up_(haze))[..., None] * np.float32([1.0, 0.97, 0.92])
    small = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    bright = np.clip((small.max(2, keepdims=True) - 0.78) / 0.22, 0, 1) * small
    bloom = cv2.GaussianBlur(bright, (0, 0), 6)
    img = img + (1 - img) * up_(bloom) * g["bloom"]
    return np.clip(img, 0, 1)


# ---------------------------------------------------------------- v5: the series title over the first moving shot
def _install_titles():
    """caption kinds "series" (the title and tagline over the opening action) and "end" (the end title over the
    departing trolley): drawn like the title card's lettering, with a soft shadow, over the picture"""
    from PIL import Image, ImageDraw
    from studio.film import graphics as G
    if getattr(G, "_undercard_titles", False):
        return
    orig = G.caption_layer

    def caption_layer(kind, a, b):
        if kind not in ("series", "end"):
            return orig(kind, a, b)
        im = Image.new("RGBA", (OW, OH), (0, 0, 0, 0))
        dr = ImageDraw.Draw(im)
        S = RS
        big, small = (150, 62) if kind == "series" else (120, 54)
        y = int((760 if kind == "series" else 90) * S)
        fa, fb = G.font(G.BEBAS, big * S), G.font(G.BEBAS, small * S)
        wa, wb = dr.textlength(a, font=fa), dr.textlength(b, font=fb)
        dr.text(((OW - wa) / 2, y), a, font=fa, fill=(255, 255, 255, 255))
        ry = y + int((big + 18) * S)
        dr.rectangle((OW / 2 - 230 * S, ry, OW / 2 + 230 * S, ry + 7 * S), fill=G.RED + (255,))
        dr.text(((OW - wb) / 2, ry + int(20 * S)), b, font=fb, fill=(255, 236, 200, 255) if kind == "end" else G.RED + (255,))
        return G.premult(im)

    G.caption_layer = functools.lru_cache(maxsize=32)(caption_layer)
    orig_caps = G.captions

    def captions(img, t, caps):
        out = []
        for c in caps:
            if c[2] in ("series", "end") and c[0] <= t < c[1]:
                lay = G.caption_layer(c[2], c[3], c[4])
                k = G.sm((t - c[0]) / 0.3) * (1 - G.sm((t - (c[1] - 0.3)) / 0.3))
                sh = G.shadow_of(lay, 10, (0, 5), 0.55)
                img = img * (1 - sh[..., None] * k)
                img = img * (1 - lay[..., 3:4] * k) + lay[..., :3] * k
            elif c[2] not in ("series", "end"):
                out.append(c)
        return orig_caps(img, t, out)

    G.captions = captions
    G._undercard_titles = True


_install_titles()

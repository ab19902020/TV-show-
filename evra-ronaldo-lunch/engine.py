"""Core of the Evra / Ronaldo film: plates, cameras, layered cut-out actors with face animation, props.

Coordinates:
  * plate px: the 941 x 1672 portrait backgrounds (the cameras frame these; output is 1080 x 1920);
  * sheet px: the 1x model sheets; parts are cut at 4x (build/parts, meta.json gives each part's sheet origin).
An actor is placed by (x, y, height): the bottom centre of the drawing at plate (x, y), the drawing `height` plate px
tall. Everything moves as rigid pieces (affine maps of the drawing), never by stretching it."""
import os, json, math
from functools import lru_cache
import numpy as np, cv2
from PIL import Image
from face import Face, viseme_events, track
import performance as perf

ROOT = os.path.dirname(os.path.abspath(__file__))
W, H = 941, 1672
FPS = 30
META = json.load(open(os.path.join(ROOT, "build/parts/meta.json")))


def T(x, y): return np.array([[1., 0, x], [0, 1., y], [0, 0, 1.]])
def S(sx, sy=None): return np.diag([sx, sx if sy is None else sy, 1.])
def R(a):
    c, s = math.cos(math.radians(a)), math.sin(math.radians(a)); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1.]])
def pivot(x, y, a): return T(x, y) @ R(a) @ T(-x, -y)
def smooth(u): u = min(max(u, 0.), 1.); return u * u * (3 - 2 * u)
def ease(t, a, b): return smooth((t - a) / (b - a)) if b > a else float(t >= a)
def bump(t, c, w): return math.exp(-((t - c) / w) ** 2)


def pm(a):
    x = a.astype(np.float32) / (255 if a.dtype == np.uint8 else 1); x = x.copy(); x[..., :3] *= x[..., 3:4]; return x


@lru_cache(None)
def part(n): return np.asarray(Image.open(os.path.join(ROOT, "build/parts", n + ".png")).convert("RGBA")).copy()


def P(n, x, y):
    """sheet coords -> part px"""
    m = META[n]; return ((x - m['off'][0]) * m['scale'], (y - m['off'][1]) * m['scale'])


def over(dst, src, M, opacity=1.):
    """composite a premultiplied RGBA float image through the 3x3 map M (src px -> dst px)"""
    h, w = src.shape[:2]; oh, ow = dst.shape[:2]
    q = M @ np.array([[0, w, w, 0], [0, 0, h, h], [1, 1, 1, 1.]])
    x0 = max(0, int(np.floor(q[0].min())) - 2); x1 = min(ow, int(np.ceil(q[0].max())) + 2)
    y0 = max(0, int(np.floor(q[1].min())) - 2); y1 = min(oh, int(np.ceil(q[1].max())) + 2)
    if x1 <= x0 or y1 <= y0: return
    a = cv2.warpAffine(src, (T(-x0, -y0) @ M)[:2], (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)
    if opacity < 1: a *= opacity
    roi = dst[y0:y1, x0:x1]; roi[:] = a[..., :dst.shape[2]] + roi * (1 - a[..., 3:4])   # dst RGB, or an RGBA layer


class Sprite:
    """premultiplied float image with a mip pyramid (sampling from the right level keeps edges clean when small)"""
    def __init__(self, a):
        self.im = pm(a) if a.dtype == np.uint8 or a.max() > 1.001 else a.astype(np.float32)
        self.h, self.w = self.im.shape[:2]; self.levels = {1.: self.im}
        for k in (.5, .25, .125): self.levels[k] = cv2.resize(self.levels[k * 2], None, fx=.5, fy=.5, interpolation=cv2.INTER_AREA)

    def draw(self, dst, M, opacity=1.):
        k = float(np.linalg.norm(M[:2, 0])); L = 1. if k >= .5 else (.5 if k >= .25 else (.25 if k >= .125 else .125))
        over(dst, self.levels[L], M @ S(1 / L), opacity)


def eyes_in(a, y0, y1, x0=0, x1=None):
    """the two eye whites in a band of a drawing: [(cx, cy, rx, ry)] left to right"""
    h, w = a.shape[:2]; x1 = w if x1 is None else x1
    rgb = a[..., :3] if a.dtype == np.uint8 else (a[..., :3] * 255)
    al = a[..., 3] if a.dtype == np.uint8 else a[..., 3] * 255
    mask = ((rgb.min(2) > 205) & (rgb.max(2).astype(int) - rgb.min(2) < 40) & (al > 200)).astype(np.uint8)
    band = np.zeros_like(mask); band[max(0, int(y0)):min(h, int(y1)), max(0, int(x0)):min(w, int(x1))] = 1; mask &= band
    n, l, st, c = cv2.connectedComponentsWithStats(mask)
    cand = [i for i in range(1, n) if st[i, 4] > max(30, w * h * .0004) and st[i, 2] < w * .4 and st[i, 3] < h * .25]
    cand = sorted(cand, key=lambda i: st[i, 4], reverse=True)[:5]
    # the two eyes are the pair that sit side by side at about the same height and size (a white sock, a shoe or a robe
    # further down is never paired with an eye)
    best, score = cand[:2], None
    for ii in range(len(cand)):
        for jj in range(ii + 1, len(cand)):
            i, j = cand[ii], cand[jj]
            dx = abs(c[i][0] - c[j][0]); dy = abs(c[i][1] - c[j][1]); hi, hj = st[i, 3], st[j, 3]
            if dx < 1 or dy > .45 * dx or dx > 6 * max(hi, hj) or max(hi, hj) > 2.2 * min(hi, hj): continue
            sc = -(st[i, 4] + st[j, 4]) * (1 - dy / dx)
            if score is None or sc < score: best, score = [i, j], sc
    return [(float(st[i, 0] + st[i, 2] / 2), float(st[i, 1] + st[i, 3] / 2), float(st[i, 2] / 2), float(st[i, 3] / 2))
            for i in sorted(best, key=lambda i: c[i][0])]


# ---------------------------------------------------------------------------------------------------- lip sync
_WORDS = json.load(open(os.path.join(ROOT, "words.json")))
LIPSYNC = []             # (who, t0, t1): which recorded lines a flashback character visibly speaks (direction.py)


@lru_cache(None)
def vis_track(who, t0, t1):
    ev = []
    for turn in _WORDS['turns']:
        for p in turn['phones']:
            if t0 - .01 <= p['s'] and p['e'] <= t1 + .01: ev.append(p)
    n = int(math.ceil(_WORDS['dur'] * FPS)) + 2
    return tuple(track(viseme_events(ev), n))


def viseme(who, t):
    for w, a, b in LIPSYNC:
        if w == who and a - .05 <= t <= b + .05: return vis_track(w, a, b)[min(int(round(t * FPS)), len(vis_track(w, a, b)) - 1)]
    return 'REST'


def speech_amp(t):
    """loudness of the recording around t (0..~1.2), so louder syllables open the jaw further"""
    return float(_env()[min(len(_env()) - 1, max(0, int(t * FPS)))])


@lru_cache(None)
def _env():
    import soundfile as sf
    y, sr = sf.read(os.path.join(ROOT, "src/audio/original.flac"), dtype='float32')
    if y.ndim > 1: y = y.mean(1)
    hop = sr // FPS; n = len(y) // hop
    e = np.sqrt(np.mean(y[:n * hop].reshape(n, hop) ** 2, 1))
    return np.clip(e / max(np.percentile(e, 92), 1e-6), 0, 1.25)


# ---------------------------------------------------------------------------------------------------- actors
class Actor:
    """one drawing, rigged for acting.
    head: sheet box of the face layer (eyes, brows, mouth animate; the head tilts and nods about `neck`);
    waist: sheet y about which the upper body leans and breathes (None: the whole drawing moves as one);
    mouth: (xl, yl, xr, yr, xc, yc) sheet px of the closed mouth line, chin: sheet y (for lip sync);
    limbs: {name: (polygon sheet px, pivot sheet px)} pieces that rotate on their own (a beckoning hand, a fork arm)."""

    def __init__(self, name, who, band=None, head=None, neck=None, waist=None, mouth=None, chin=None, limbs=None,
                 facing='front', face=True, ref_span=None, numbers=None, mirrored=False, size=1., erase=None, nohead=None,
                 inpaint=None, height1=None):
        self.n, self.who = name, who; a = part(name).copy()
        for poly in inpaint or ():
            # a drawn prop the film replaces (Rio's microphone becomes a table-tennis bat): painted over from around it
            k_ = META[name]['scale']
            m = np.zeros(a.shape[:2], np.uint8); cv2.fillPoly(m, [np.int32([P(name, *q) for q in poly])], 255)
            a[..., :3] = cv2.inpaint(np.ascontiguousarray(a[..., :3]), m, 5 * k_, cv2.INPAINT_TELEA)
        for poly in erase or ():
            # drawn details that the film animates itself (the food on a fork is eaten): taken out of the drawing
            m = np.zeros(a.shape[:2], np.uint8); cv2.fillPoly(m, [np.int32([P(name, *q) for q in poly])], 255)
            a[..., 3] = np.uint8(a[..., 3] * (1 - cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 1.)))
        if mirrored:
            # this copy is drawn mirrored: flip the shirt numbers in place first, so they still read the right way
            for bx in numbers or ():
                x0, y0 = map(int, P(name, bx[0], bx[1])); x1, y1 = map(int, P(name, bx[2], bx[3]))
                a[y0:y1, x0:x1] = a[y0:y1, x0:x1, :][:, ::-1]
        self.a = a; self.hh, self.ww = a.shape[:2]
        k = META[name]['scale']; self.k = k; ox, oy = META[name]['off']
        Y, X = np.mgrid[:self.hh, :self.ww]
        body = a.copy()
        self.limbs = {}; limbmask = np.zeros((self.hh, self.ww), np.float32)
        for ln, (poly, pv) in (limbs or {}).items():
            m = np.zeros((self.hh, self.ww), np.uint8); cv2.fillPoly(m, [np.int32([P(name, *q) for q in poly])], 255)
            m = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 1.2)
            piece = a.copy(); piece[..., 3] = np.uint8(piece[..., 3] * m)
            px, py = P(name, *pv); disk = ((X - px) ** 2 + (Y - py) ** 2) < (10 * k) ** 2
            body[..., 3] = np.uint8(body[..., 3] * np.where(disk, 1, 1 - m))
            self.limbs[ln] = (Sprite(piece), (px, py)); limbmask = np.maximum(limbmask, m)
        if self.limbs:
            # what was behind a moved arm: the body around it, painted in (an arm in the air leaves air behind it; an arm
            # in front of the chest leaves shirt), so moving it never opens a see-through hole
            hole = (limbmask > .02).astype(np.uint8)
            rest = body[..., 3].astype(np.float32) / 255
            fill_a = cv2.GaussianBlur(rest * (1 - limbmask), (0, 0), 7 * k) / np.maximum(cv2.GaussianBlur(1 - limbmask, (0, 0), 7 * k), 1e-3)
            fill_a = np.clip((fill_a - .45) / .2, 0, 1) * limbmask
            rgb = cv2.inpaint(np.ascontiguousarray(body[..., :3]), hole * 255, 6 * k, cv2.INPAINT_TELEA)
            body[..., :3] = np.where(hole[..., None] > 0, rgb, body[..., :3])
            body[..., 3] = np.uint8(np.clip(np.maximum(rest, fill_a) * 255, 0, 255))
        # eyes, and from them the head layer's box: the whole head with both ears, down to just under the chin
        b0, b1 = band or ((0, .7) if name[:3] in ('eb_', 'rb_') or name in ('rio_warning', 'rio_shrug', 'rio_laugh', 'rio_folded') else (0, .42))
        self.eyes0 = eyes_in(a, self.hh * b0, self.hh * b1) if face else []
        self.span = abs(self.eyes0[1][0] - self.eyes0[0][0]) / k if len(self.eyes0) == 2 else None
        if head is None and self.span:
            (lx, ly), (rx, ry) = [(e[0] / k + ox, e[1] / k + oy) for e in self.eyes0]
            sp = self.span; ey = (ly + ry) / 2
            head = (lx - 2.6 * sp, oy, rx + 1.9 * sp, ey + 1.85 * sp)
            if neck is None: neck = ((lx + rx) / 2 - .2 * sp, ey + 1.85 * sp)
        if head is not None and chin:
            # a talking face: the layer reaches well under the chin, so the dropped jaw is never cut off
            head = (head[0], head[1], head[2], max(head[3], chin + 30)); neck = (neck[0], chin + 14) if neck else neck
        self.ref = ((ref_span / self.span) if (ref_span and self.span) else 1.) * size
        if height1: self.ref = height1 * k / self.hh                     # drawings with no eyes to measure (a laugh)
        self.head = None
        if head:
            x0, y0 = P(name, head[0], head[1]); x1, y1 = P(name, head[2], head[3])
            x0, y0, x1, y1 = max(0, int(x0)), max(0, int(y0)), min(self.ww, int(x1)), min(self.hh, int(y1))
            fade = 10 * k
            mask = np.clip((y1 - Y) / fade, 0, 1) * (Y >= y0) * (X >= x0) * (X < x1)
            mask = mask * (1 - limbmask)                                  # a hand near the face moves with its arm
            for poly in nohead or ():                                       # ...or stays with the body (a fork by the mouth)
                m = np.zeros((self.hh, self.ww), np.uint8); cv2.fillPoly(m, [np.int32([P(name, *q) for q in poly])], 255)
                mask = mask * (1 - cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 1.2))
            hd = a[y0:y1, x0:x1].copy(); hd[..., 3] = np.uint8(hd[..., 3] * mask[y0:y1, x0:x1])
            # the body keeps its own pixels in a band above the head layer's soft bottom edge, so a tilt never opens a gap
            hole = (mask >= .999) & (Y < y1 - fade - 6 * k)
            # ...and keeps the head's own outline under the head layer's edge, so a small tilt never shows a gap
            hole = cv2.erode(hole.astype(np.uint8), np.ones((int(5 * k) | 1, int(5 * k) | 1), np.uint8)) > 0
            body[..., 3] = np.uint8(body[..., 3] * ~hole)
            self.hoff = (x0, y0)
            eyes = [(e[0] - x0, e[1] - y0, e[2], e[3]) for e in self.eyes0]
            marks = {}
            if mouth:
                q = [P(name, mouth[i], mouth[i + 1]) for i in (0, 2, 4)]
                marks['mouth'] = (q[0][0] - x0, q[0][1] - y0, q[1][0] - x0, q[1][1] - y0, q[2][0] - x0, q[2][1] - y0)
                marks['chin'] = P(name, 0, chin)[1] - y0 if chin else None
            self.face = Face(hd, eyes=eyes, ink=[.03, .02, .02], facing=facing, **marks)
            self.eyes = eyes; self.head = (x0, y0, x1, y1)
            self.neck = P(name, *neck) if neck else ((x0 + x1) / 2, y1)
        self.waist = P(name, 0, waist)[1] if waist else None
        if self.waist is not None:
            m = np.clip((self.waist + 8 * k - Y) / (16 * k), 0, 1)
            # the lower body reaches well up under the torso, so leaning never opens a gap at the sides of the waist
            lm = np.clip((Y - (self.waist - 34 * k)) / (4 * k), 0, 1)
            up = body.copy(); up[..., 3] = np.uint8(up[..., 3] * m); lo = body.copy(); lo[..., 3] = np.uint8(lo[..., 3] * lm)
            self.upper, self.lower = Sprite(up), Sprite(lo)
        else:
            self.upper, self.lower = Sprite(body), None

    def height(self, scale):
        """plate px tall at `scale` (plate px per sheet px of the character's model-sheet front view)"""
        return scale * self.ref * self.hh / self.k

    def put(self, dst, cam, x, y, scale, t, **kw):
        return self.draw(dst, cam, x, y, self.height(scale), t, **kw)

    def place(self, x, y, height, mirror=False):
        s = height / self.hh
        return T(x, y) @ S(-s if mirror else s, s) @ T(-self.ww / 2, -self.hh)

    def to_plate(self, x, y, height, sx, sy, mirror=False):
        """a sheet point of this drawing -> plate px when placed at (x, y, height)"""
        return (self.place(x, y, height, mirror) @ [*P(self.n, sx, sy), 1])[:2]

    def head_image(self, t, vis='REST', amp=1., look=None, brow=0., smile=0., blink=None, blush=0.):
        st = perf.state(self.who, t)
        if blink is not None and not isinstance(blink, (list, tuple)): blink = max(blink, st['blink'])
        lk = (float(st['look'] + (look[0] if look else 0)), float(st['looky'] + (look[1] if look else 0)))
        return self.face.render(vis=vis, amp=amp, blink=st['blink'] if blink is None else blink, look=lk,
                                brow=st['brow'] + brow, smile=0 if vis != 'REST' else st['smile'] + smile, blush=st['blush'] + blush)

    def draw(self, dst, cam, x, y, height, t, mirror=False, lean=0., tilt=0., nod=0., hop=0., life=1., limbs=None,
             look=None, brow=0., smile=0., speak=True, opacity=1., blush=0., squash=0., blink=None, vis=None, amp=None,
             holds=None):
        st = perf.state(self.who, t); L = perf.life(self.who, t)
        tilt += st['tilt'] + L['tilt'] * life; lean += L['lean'] * life
        nodpx = (nod + st['nod']) * self.hh / 160 + L['nod'] * life * self.hh
        M = cam @ T(0, -hop) @ self.place(x, y, height, mirror)
        if squash: M = M @ T(self.ww / 2, self.hh) @ S(1 + squash * .5, 1 - squash) @ T(-self.ww / 2, -self.hh)
        if self.lower is not None:
            B = T(0, (L['dip'] - L['breath']) * life * self.hh) @ pivot(self.ww / 2, self.waist, lean)
            self.lower.draw(dst, M, opacity)
        else:
            B = pivot(self.ww / 2, self.hh, lean * .5)
        self.upper.draw(dst, M @ B, opacity)
        self.limbM = {}
        for ln, (spr, pv) in self.limbs.items():
            ang = (limbs or {}).get(ln, 0.)
            LM = M @ B @ pivot(pv[0], pv[1], ang); self.limbM[ln] = LM
            if holds and ln in holds: holds[ln](dst, LM)               # a held thing goes under the hand that grips it
            spr.draw(dst, LM, opacity)
        if self.head is not None:
            if vis is None:
                vis = viseme(self.who, t) if speak else 'REST'
                amp = .55 + .45 * speech_amp(t) if vis != 'REST' else 1.
            elif amp is None: amp = 1.
            hd = self.head_image(t, vis, amp, look, brow, smile, blink=blink, blush=blush)
            HM = B @ T(0, nodpx) @ pivot(self.neck[0], self.neck[1], tilt * (-1 if mirror else 1)) @ T(*self.hoff)
            over(dst, pm(hd), M @ HM, opacity)
        return M @ B


class Prop:
    """a prop cut from the atlas, placed by its centre (plate px) and width"""
    def __init__(self, name, a=None):
        self.n = name; self.spr = Sprite(part(name) if a is None else a); self.w, self.h = self.spr.w, self.spr.h

    def draw(self, dst, cam, x, y, width, rot=0., opacity=1., flip=False, sy=1.):
        s = width / self.w
        M = cam @ T(x, y) @ R(rot) @ S(-s if flip else s, s * sy) @ T(-self.w / 2, -self.h / 2)
        self.spr.draw(dst, M, opacity)


# ---------------------------------------------------------------------------------------------------- plates and cameras
class Plates:
    def __init__(self, names):
        self.p = {}
        for n in names:
            a = np.asarray(Image.open(os.path.join(ROOT, "build/up", n + ".png")).convert("RGB"))
            self.p[n] = cv2.resize(a, (W * 2, H * 2), interpolation=cv2.INTER_AREA)       # 2x: sharp up to ~1.7x zoom

    def warp(self, n, cam, ow, oh):
        M = cam @ S(.5)
        out = cv2.warpAffine(self.p[n], M[:2], (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        return out.astype(np.float32) / 255

    def region(self, n, cam, ow, oh, poly, feather=1.5):
        """the plate inside a polygon (plate px) as a premultiplied RGBA layer, for things that stand in front of people"""
        m = np.zeros((H * 2, W * 2), np.uint8); cv2.fillPoly(m, [np.int32(np.array(poly) * 2)], 255)
        if feather: m = cv2.GaussianBlur(m, (0, 0), feather * 2)
        M = (cam @ S(.5))[:2]
        rgb = cv2.warpAffine(self.p[n], M, (ow, oh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101).astype(np.float32) / 255
        a = cv2.warpAffine(m, M, (ow, oh), flags=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255
        return rgb, a


def camera(ow, zoom, cx, cy, oh=None, rot=0.):
    oh = oh or ow * 16 // 9
    return T(ow / 2, oh / 2) @ R(rot) @ S(zoom * ow / W) @ T(-cx, -cy)


def shadow(dst, cam, x, y, width, alpha=.32):
    a = np.zeros((40, 240, 4), np.float32); cv2.ellipse(a, (120, 20), (110, 11), 0, 0, 360, (0, 0, 0, alpha), -1, cv2.LINE_AA)
    a = cv2.GaussianBlur(a, (0, 0), 3.5); over(dst, a, cam @ T(x - width / 2, y - width * .083) @ S(width / 240))

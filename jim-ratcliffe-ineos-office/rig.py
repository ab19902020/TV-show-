"""Cut-out rig for Jim, built from the character sheet's replacement drawings.

Rig frame = the FRONT turnaround body (4x crop px).  Front-facing layers, back to front:
    neck filler -> hanging forearms (FRONT body, only for poses with an arm down) -> lower body (FRONT legs +
    jacket flaps) -> arm-pose torso -> head (face/hair/beard/neck, clothes stripped) + lip-sync mouth ->
    hands that come up in front of the face (chin / tie / wave / OK poses)
Every drawing is registered into the rig frame once (register.py / landmarks.py); the renderer warps each layer
straight from its source pixels to the screen, so nothing is resampled twice."""
import numpy as np, cv2, pickle
from landmarks import all_landmarks

K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
def to3(M): return np.vstack([M, [0, 0, 1]])

# FRONT body anchors (read off the gridded FRONT drawing)
F_KNOT = (272.0, 402.0)
F_BELT = (265.0, 780.0)
F_FLOOR = 1520.0
LOWER_Y = 715            # lower body = FRONT drawing below this line (legs + jacket flaps)
SLEEVE_X = (108, 440)    # FRONT sleeves/hands hang outside this column band (above y=1030)
HANG_TOP = 690
NECK_PIVOT = (272.0, 395.0)       # head rotates about the base of the neck

# poses with an arm hanging straight down: the drawing cuts that sleeve at its bottom edge, so the FRONT
# body's forearm + hand continues it (screen-left 'L' / screen-right 'R')
HANGING = {"ARMS DOWN": "LR", "POINT LEFT": "R", "POINT RIGHT": "L", "PALM OUT STOP": "R", "THUMBS UP": "R",
           "THUMBS DOWN": "R", "FIST PUMP": "R", "PHONE HOLD": "R", "WAVE": "R", "HOLDING CUP": "R", "OK SIGN": "R"}

NO_STUB_CUT = {"HAND ON CHIN"}   # the 'neck stub' there is the hand itself

# poses whose hand/arm comes up in front of the chin / face -> drawn over the head
FRONT_HANDS = {"HAND ON CHIN", "ADJUST TIE", "WAVE", "OK SIGN", "FIST PUMP", "PHONE HOLD", "PALM OUT STOP", "THUMBS UP"}

def classes(rgba):
    c = rgba[..., :3].astype(np.int32); b, g, r = c[..., 0], c[..., 1], c[..., 2]
    v = c.max(2); sat = v - c.min(2); a = rgba[..., 3] > 100
    red = a & (r > 130) & (g < 95) & (b < 95) & (r > g + 80)
    skin = a & (r > b + 45) & (r > 120) & ~red
    white = a & (v > 185) & (sat < 45)
    grey = a & (sat < 40) & (v <= 185) & (v > 35)
    return red, skin, white, grey

def premul(rgba):
    a = rgba[..., 3:4].astype(np.float32) / 255
    return np.dstack([rgba[..., :3].astype(np.float32) * a, a])

def grade(bgr):
    """match the sheet's flat studio lighting to the warm, sunlit office"""
    f = bgr.astype(np.float32) / 255
    f = f ** 1.04 * np.float32([0.95, 0.99, 1.04])
    return np.clip(f * 255, 0, 255).astype(np.uint8)

def graded_premul(rgba):
    out = rgba.copy(); out[..., :3] = grade(rgba[..., :3]); return premul(out)

def two_point(src_a, src_b, dst_a, dst_b, rot_gain=0.0, smin=0.88, smax=1.14):
    """similarity mapping a->a, b->b (scale from the a-b distance, rotation damped)."""
    sa, sb, da, db = map(np.float64, (src_a, src_b, dst_a, dst_b))
    s = np.clip(np.linalg.norm(db - da) / max(np.linalg.norm(sb - sa), 1e-6), smin, smax)
    ang = (np.arctan2(*(db - da)[::-1]) - np.arctan2(*(sb - sa)[::-1])) * rot_gain
    ca, sn = np.cos(ang) * s, np.sin(ang) * s
    R = np.array([[ca, -sn], [sn, ca]])
    t = da - R @ sa
    return np.hstack([R, t[:, None]])

HEAD_DROP = 28.0      # rig px: the chin tucks just into the collar

def head_knot(img):
    """top-centre of the tie knot drawn under the chin (head crop px)"""
    c = img[..., :3].astype(np.int32); H, W = c.shape[:2]
    red = ((img[..., 3] > 128) & (c[..., 2] > 130) & (c[..., 2] > c[..., 1] + 90) & (c[..., 2] > c[..., 0] + 70)).astype(np.uint8)
    red[:int(H * 0.84)] = 0; red[:, :int(W / 2 - 110)] = 0; red[:, int(W / 2 + 110):] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(red)
    if n < 2: return None
    i = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    ys, xs = np.where(lab == i); yk = ys.min()
    return (float(xs[ys < yk + 25].mean()), float(yk))

def neck_fade(pm, kn, band=90, span=34):
    """fade the head drawing's neck (below the chin, centre band) into the torso collar underneath."""
    H, W = pm.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    f = np.clip((kn[1] + 4 - yy) / span, 0, 1)
    f = np.where(np.abs(xx - kn[0]) < band, f, 1.0)
    f = cv2.GaussianBlur(f.astype(np.float32), (0, 0), 6)
    return pm * f[..., None]

class Rig:
    def __init__(self, parts="parts.pkl", reg="reg.pkl"):
        P = pickle.load(open(parts, "rb")); R = pickle.load(open(reg, "rb"))
        self.P = P
        front = P["turn"]["FRONT"][0]
        H, W = front.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        # ---- lower body: FRONT drawing below the belt, minus the hanging sleeves / hands
        side = ((xx < SLEEVE_X[0]) | (xx > SLEEVE_X[1])) & (yy < 1030)
        low = front.copy()
        keep = (yy >= LOWER_Y) & ~side
        low[..., 3] = (low[..., 3] * keep).astype(np.uint8)
        low[..., 3] = (low[..., 3] * np.clip((yy - LOWER_Y) / 14.0, 0, 1)).astype(np.uint8)   # soft top edge
        self.lower = (graded_premul(low), np.eye(3)[:2])
        # ---- hanging forearms (screen-left 'L', screen-right 'R') from the FRONT body
        self.hang = {}
        for k, m in (("L", (xx < SLEEVE_X[0] + 6)), ("R", (xx > SLEEVE_X[1] - 6))):
            p = front.copy(); msk = m & (yy >= HANG_TOP) & (yy < 1040)
            p[..., 3] = (p[..., 3] * msk).astype(np.uint8)
            p[..., 3] = (p[..., 3] * np.clip((yy - HANG_TOP) / 20.0, 0, 1)).astype(np.uint8)
            self.hang[k] = graded_premul(p)
        # ---- torsos (arm poses): knot->knot, belt->belt
        L = all_landmarks(P)
        base = L["ARMS DOWN"]
        M_base = two_point(base["knot"], base["belt"], F_KNOT, F_BELT, smin=0.1, smax=10)   # ARMS DOWN -> FRONT
        self.torso = {}
        for n, (img, _) in P["arm"].items():
            d = L[n]
            # pose -> ARMS DOWN (drawings vary a little in size: clamp) -> FRONT
            M = (to3(M_base) @ to3(two_point(d["knot"], d["belt"], base["knot"], base["belt"], smin=0.74, smax=1.26)))[:2]
            t = img.copy()
            red, skin, white, grey = classes(t)
            Ht, Wt = t.shape[:2]
            ty, tx = np.mgrid[0:Ht, 0:Wt]
            kx, ky = d["knot"]
            # neck stub (skin above the collar at the centre) is replaced by the head's own neck
            stub = skin & (ty < ky + 30) & (np.abs(tx - kx) < 70)
            n_, lab, st, _ = cv2.connectedComponentsWithStats(stub.astype(np.uint8))
            stub_m = np.zeros_like(stub)
            for i in range(1, n_):
                if st[i, cv2.CC_STAT_TOP] < ky + 6 and st[i, cv2.CC_STAT_AREA] < 9000: stub_m |= lab == i
            stub_m = cv2.dilate(stub_m.astype(np.uint8), K(2)).astype(bool) & (ty < ky + 34)
            if n not in NO_STUB_CUT: t[..., 3] = np.where(stub_m, 0, t[..., 3])
            # bottom edge: melt into the FRONT jacket flaps below
            bot = np.where((t[..., 3] > 0).any(1))[0].max()
            t[..., 3] = (t[..., 3] * np.clip((bot - ty) / 18.0, 0, 1)).astype(np.uint8)
            # hands in front of the face
            front_m = None
            if n in FRONT_HANDS:
                up = (ty < ky + 0.42 * (d["belt"][1] - ky))
                hm = cv2.dilate((skin & up & ~stub_m).astype(np.uint8), K(10)).astype(bool) & (t[..., 3] > 0) & up
                n_, lab, st, _ = cv2.connectedComponentsWithStats(hm.astype(np.uint8))
                front_m = np.zeros_like(hm)
                for i in range(1, n_):
                    if st[i, cv2.CC_STAT_AREA] > 1500: front_m |= lab == i
                fr = t.copy(); fr[..., 3] = (fr[..., 3] * cv2.GaussianBlur(front_m.astype(np.float32), (0, 0), 1.5)).astype(np.uint8)
                front_m = graded_premul(fr)
            self.torso[n] = dict(img=graded_premul(t), M=M, front=front_m,
                                 hang={k: self.hang_dx(t, M, k) for k in HANGING.get(n, "")})
        # ---- heads: expression head -> rig (SIFT chain), clothes stripped
        self.head = {}
        for n, (img, _) in P["head"].items():
            M = R["head"][n].copy()
            kn = head_knot(img)
            if kn is not None and n != "THINKING":        # THINKING's knot is behind its hand: keep SIFT
                p = M @ np.array([kn[0], kn[1], 1.0])
                M[:, 2] += np.array([F_KNOT[0], F_KNOT[1] + HEAD_DROP]) - p
            stripped = self.strip_clothes(img)
            if kn is not None: stripped = neck_fade(stripped, kn)
            self.head[n] = dict(img=stripped, M=M, knot=kn, raw=img)
        # ---- neck filler (skin, behind everything) sized from the FRONT neck
        self.neck_fill = self.make_neck(front, P["head"]["NEUTRAL"][0])

    def hang_dx(self, t, M, side):
        """x shift that lines the FRONT forearm up with the torso drawing's own sleeve at its bottom edge."""
        a = t[..., 3] > 128
        bot = np.where(a.any(1))[0].max() - 26
        xs = np.where(a[bot])[0]
        p = cv2.transform(np.float32([[[xs.min(), bot], [xs.max(), bot]]]), M)[0]
        y = int(p[0][1])
        fa = self.P["turn"]["FRONT"][0][..., 3] > 128
        fx = np.where(fa[y])[0]
        return float(p[0][0] - fx.min()) if side == "L" else float(p[1][0] - fx.max())

    def strip_clothes(self, img):
        """keep face / hair / beard / ears / neck; drop the drawing's own collar, tie knot and jacket."""
        red, skin, white, grey = classes(img)
        H, W = img.shape[:2]
        yy = np.arange(H)[:, None]
        clothes = (red | white | grey) & (yy > H * 0.62)
        n, lab, st, _ = cv2.connectedComponentsWithStats(clothes.astype(np.uint8), connectivity=8)
        cl = np.zeros_like(clothes)
        for i in range(1, n):
            y0, h = st[i, cv2.CC_STAT_TOP], st[i, cv2.CC_STAT_HEIGHT]
            if y0 + h >= H - 12 and st[i, cv2.CC_STAT_AREA] > 300: cl |= lab == i       # touches the bottom
        cl |= red & (yy > H * 0.75)
        # dark outline pixels sandwiched between clothes pieces go too
        dark = (img[..., :3].max(2) < 70) & (yy > H * 0.75)
        cl |= dark & cv2.dilate(cl.astype(np.uint8), K(6)).astype(bool)
        cl = cv2.morphologyEx(cl.astype(np.uint8), cv2.MORPH_CLOSE, K(3)).astype(bool)
        out = img.copy()
        a = out[..., 3].astype(np.float32) * (1 - cv2.GaussianBlur(cl.astype(np.float32), (0, 0), 1.2))
        out[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
        # jacket shards low at the sides (not hair) and thin leftover outline strokes
        c = img[..., :3].astype(np.int32); v = c.max(2); sat = v - c.min(2)
        hair = (c[..., 2] > c[..., 1]) & (c[..., 1] > c[..., 0]) & (sat > 35) & (v < 215)
        skin_ = (c[..., 2] > c[..., 0] + 45) & (c[..., 2] > 120)
        xx = np.arange(W)[None, :]
        shard = (yy > 0.76 * H) & (np.abs(xx - W / 2) > 0.24 * W) & ~hair & ~skin_
        a2 = out[..., 3].astype(np.float32) * (1 - cv2.GaussianBlur(shard.astype(np.float32), (0, 0), 1.5))
        body = cv2.morphologyEx((a2 > 60).astype(np.uint8), cv2.MORPH_OPEN, K(4))
        a2 *= cv2.GaussianBlur(cv2.dilate(body, K(1)).astype(np.float32), (0, 0), 0.8)
        out[..., 3] = np.clip(a2, 0, 255).astype(np.uint8)
        # keep only the main blob (drops stray jacket slivers)
        m = (out[..., 3] > 60).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
        main = lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
        out[..., 3] = (out[..., 3] * cv2.dilate(main.astype(np.uint8), K(2))).astype(np.uint8)
        return graded_premul(out)

    def make_neck(self, front, head):
        """a shaded neck behind the collar: fills the collar V and anything the chin doesn't cover."""
        red, skin, white, grey = classes(head)
        kx, ky = head_knot(head)
        y0, y1, x0, x1 = int(ky - 45), int(ky - 5), int(kx - 45), int(kx + 45)
        band = head[y0:y1, x0:x1][..., :3][skin[y0:y1, x0:x1]]
        col = np.median(band, axis=0).astype(np.float32) * 0.92
        col = grade(col.reshape(1, 1, 3).astype(np.uint8)).reshape(3).astype(np.float32)
        H, W = front.shape[:2]
        cx, cy = F_KNOT
        m = np.zeros((H, W), np.float32)
        pts = np.array([[cx - 44, cy - 90], [cx + 44, cy - 90], [cx + 52, cy + 40], [cx - 52, cy + 40]], np.int32)
        cv2.fillConvexPoly(m, pts, 1.0, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), 1.5)
        yy, xx = np.mgrid[0:H, 0:W]
        rel = np.clip(np.abs(xx - cx) / (44 + 8 * np.clip((yy - (cy - 90)) / 130.0, 0, 1)), 0, 1)
        shade = 0.72 + 0.28 * (1 - rel ** 2.5)                                            # round neck
        shade *= np.clip(0.74 + 0.26 * (yy - (cy - 90)) / 70.0, 0.74, 1.0)               # chin shadow
        c = col[None, None, :] * shade[..., None]
        # drawn outline down both sides, like the rest of the artwork
        side = ((m > 0.5) & (rel > 0.90)).astype(np.float32)
        side = cv2.GaussianBlur(side, (0, 0), 1.0)
        c = c * (1 - side[..., None]) + np.float32([34, 30, 38]) * side[..., None]
        return np.dstack([c * m[..., None], m]).astype(np.float32)

    # ------------------------------------------------------------------ assembling a pose
    def layers(self, torso, head, mouth=None, head_M=None, torso_M=None, hang=None):
        """ordered list of (premultiplied RGBA float32, 3x3 matrix source->rig).  head_M: extra head motion
        (rotation about the neck), torso_M: torso lean/bounce (rig frame), applied to everything above the legs."""
        T = to3(torso_M) if torso_M is not None else np.eye(3)
        Hm = T @ (to3(head_M) if head_M is not None else np.eye(3))
        d = self.torso[torso]
        out = [(self.neck_fill, Hm)]
        sides = d["hang"] if hang is None else hang
        for k, dx in sides.items():
            out.append((self.hang[k], T @ np.array([[1, 0, dx], [0, 1, 0], [0, 0, 1]], np.float64)))
        out.append((self.lower[0], np.eye(3)))
        out.append((d["img"], T @ to3(d["M"])))
        hd = self.head[head]
        himg = hd["img"] if mouth is None else self.mouth_head(head, mouth)
        out.append((himg, Hm @ to3(hd["M"])))
        if d["front"] is not None:
            out.append((d["front"], T @ to3(d["M"])))
        return out

    def mouth_head(self, head, mouth):
        return self.head[head]["img"]          # replaced by the lip-sync compositor (mouths.py)

def over(dst, src):
    return src + dst * (1 - src[..., 3:4])

def render_layers(layers, M_view, size):
    """composite layers into an image of `size` (w, h) with view matrix M_view (3x3: rig -> image)."""
    w, h = size
    out = np.zeros((h, w, 4), np.float32)
    for img, M in layers:
        A = (M_view @ M)[:2].astype(np.float32)
        # warp only the destination bounding box of this layer
        hh, ww = img.shape[:2]
        c = cv2.transform(np.float32([[[0, 0], [ww, 0], [0, hh], [ww, hh]]]), A)[0]
        x0, y0 = int(max(0, np.floor(c[:, 0].min()) - 2)), int(max(0, np.floor(c[:, 1].min()) - 2))
        x1, y1 = int(min(w, np.ceil(c[:, 0].max()) + 2)), int(min(h, np.ceil(c[:, 1].max()) + 2))
        if x1 <= x0 or y1 <= y0: continue
        A2 = A.copy(); A2[0, 2] -= x0; A2[1, 2] -= y0
        interp = cv2.INTER_AREA if abs(np.linalg.det(A[:, :2])) < 0.6 else cv2.INTER_LINEAR
        if interp == cv2.INTER_AREA:          # warpAffine has no true area filter: pre-shrink the source
            f = float(np.sqrt(abs(np.linalg.det(A[:, :2]))) * 1.25)
            img = cv2.resize(img, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
            A2 = A2 @ np.array([[1 / f, 0, 0], [0, 1 / f, 0], [0, 0, 1]], np.float32)
        wl = cv2.warpAffine(img, A2[:2].astype(np.float32), (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR)
        out[y0:y1, x0:x1] = over(out[y0:y1, x0:x1], wl)
    return out

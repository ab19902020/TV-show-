"""Cut-out rig for Jim, built from the character sheet's replacement drawings.

Rig frame = the FRONT turnaround body (4x crop px).  Front-facing layers, back to front:
    lower body (FRONT legs + jacket flaps, the waist band warped per pose) -> hanging forearms (FRONT body, only for
    poses with an arm down) -> head (face / hair / neck, moves; its neck tucks into the collar) + lip-sync mouth ->
    FRONT's collar, knot and shoulders (scaled per side to the pose) -> arm-pose torso (knot on FRONT's knot, belt on
    FRONT's belt, its neck opening cut to FRONT's collar V) -> hands in front -> a moving hand (chop / jab)
Every drawing is registered into the rig frame once (register.py / landmarks.py); the renderer warps each layer
straight from its source pixels to the screen, so nothing is resampled twice."""
import numpy as np, cv2, pickle
from landmarks import all_landmarks
import extras

K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
def to3(M): return np.vstack([M, [0, 0, 1]])

# FRONT body anchors (read off the gridded FRONT drawing)
F_KNOT = (272.0, 402.0)
F_BELT = (268.0, 774.0)        # top edge of the belt, at the buckle
HEM_Y = 958.0                   # FRONT's jacket hem
THIGH_Y = 1030.0                # FRONT's hanging hands end above here
TROUSER_X = (116, 433)          # FRONT's trouser outer edges just below the hands (continued up under them)
F_FLOOR = 1520.0
LOWER_Y = 715            # lower body = FRONT drawing below this line (legs + jacket flaps)
SLEEVE_X = (108, 440)    # FRONT sleeves/hands hang outside this column band (above y=1030)
HANG_TOP = 690
NECK_PIVOT = (272.0, 395.0)       # head rotates about the base of the neck

# poses with an arm hanging straight down: the drawing cuts that sleeve at its bottom edge, so the FRONT
# body's forearm + hand continues it (screen-left 'L' / screen-right 'R')
HANGING = {"ARMS DOWN": "LR", "POINT LEFT": "R", "POINT RIGHT": "L", "PALM OUT STOP": "R", "THUMBS UP": "R",
           "THUMBS DOWN": "R", "FIST PUMP": "R", "PHONE HOLD": "R", "WAVE": "R", "HOLDING CUP": "R", "OK SIGN": "R",
           "FINGER UP": "R", "TALK RIGHT": "R"}

NO_STUB_CUT = {"HAND ON CHIN", "ADJUST TIE"}   # the 'neck stub' there is the hand itself

# poses whose hand/arm comes up in front of the chin / face -> drawn over the head
FRONT_HANDS = {"HAND ON CHIN", "ADJUST TIE", "WAVE", "OK SIGN", "FIST PUMP", "PHONE HOLD", "PALM OUT STOP", "THUMBS UP",
               "FINGER UP"}

def classes(rgba):
    c = rgba[..., :3].astype(np.int32); b, g, r = c[..., 0], c[..., 1], c[..., 2]
    v = c.max(2); sat = v - c.min(2); a = rgba[..., 3] > 100
    red = a & (r > 130) & (g < 95) & (b < 95) & (r > g + 80)
    skin = a & (r > b + 45) & (r > 120) & ~red
    white = a & (v > 185) & (sat < 45)
    grey = a & (sat < 40) & (v <= 185) & (v > 35)
    return red, skin, white, grey

def knot_top(rgba, guess):
    """top-centre of the tie knot: the first solid row of the crimson piece that runs down into the tie
    (never the orange-red neck shadow above it).  guess: a rough knot point (same px)."""
    c = rgba[..., :3].astype(np.int32); b, g, r = c[..., 0], c[..., 1], c[..., 2]
    H, W = rgba.shape[:2]
    gx, gy = guess
    crim = (rgba[..., 3] > 128) & (r > 130) & (g < 90) & (r > g + 80) & (g < b + 25)
    win = np.zeros((H, W), bool)
    win[max(0, int(gy) - 30):min(H, int(gy) + 110), max(0, int(gx) - 70):min(W, int(gx) + 70)] = True
    n, lab, st, cen = cv2.connectedComponentsWithStats((crim & win).astype(np.uint8), connectivity=8)
    # the knot: the topmost solid crimson piece on the tie's column (its outline can split it from the blade)
    best = None
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 200 or st[i, cv2.CC_STAT_WIDTH] < 12 or abs(cen[i][0] - gx) > 45: continue
        rows = np.where((lab == i).sum(1) >= 12)[0]
        if len(rows) and (best is None or rows[0] < best[1]): best = (i, int(rows[0]))
    if best is None: return guess
    m = lab == best[0]
    yk = best[1]
    xk = float(np.where(m[yk:yk + 16].any(0))[0].mean())
    if abs(xk - gx) > 45 or abs(yk - gy) > 60: return guess
    return (xk, float(yk))

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

HEAD_EXT = 110       # px the head drawing's bottom rows are continued downwards (behind the torso)
# the head's own jacket shows only inside FRONT's collar V (beside the neck); outside it FRONT's collar and
# shoulders (behind every pose) are the silhouette, with a short soft slope between the two
NECK_ZONE = 62.0    # rig px either side of the neck where the head's jacket collar is always kept
SLOPE_END = 92.0    # rig px from the neck where the allowance above the shoulders has sloped down to JACKET_UP
SLOPE_UP = 40.0     # rig px allowed above the shoulders at the edge of the neck zone
JACKET_UP = 4.0     # rig px the head's jacket collar may rise above the shoulders further out
SEAT = 0.0           # rig px: the head drawing's knot sits this far below the rig knot (chin into the collar)

def cm_knot(cm):
    ys, xs = np.where(cm)
    return float(np.median(xs)), float(ys.min())

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
        self.head_sift = R["head"]
        P["arm"]["FINGER UP"] = (extras.finger_up(P), None)
        P["arm"]["WATCH"] = (extras.watch(P), None)
        self.P = P
        front = P["turn"]["FRONT"][0]
        H, W = front.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        # ---- lower body: FRONT drawing below the belt, minus the hanging sleeves / hands
        side = ((xx < SLEEVE_X[0]) | (xx > SLEEVE_X[1])) & (yy < THIGH_Y)
        low = front.copy()
        # FRONT's own hanging hands and cuffs reach inside the band: remove them and paint jacket in their place
        red, skin, white, grey = classes(front)
        hands = (skin | white) & ((xx < SLEEVE_X[0] + 45) | (xx > SLEEVE_X[1] - 45)) & (yy > 820) & (yy < THIGH_Y)
        hands = cv2.dilate(hands.astype(np.uint8), K(5)).astype(bool) & ~side
        low[..., :3] = cv2.inpaint(np.ascontiguousarray(front[..., :3]), hands.astype(np.uint8) * 255, 12, cv2.INPAINT_TELEA)
        # under the hands: jacket above the hem; below it the trouser legs continue straight down to their outline
        trouser = (xx >= TROUSER_X[0]) & (xx <= TROUSER_X[1])
        low[..., 3] = np.where(hands & ((yy < HEM_Y + 4) | trouser), 255, np.where(hands, 0, low[..., 3]))
        tline = hands & (yy >= HEM_Y) & ((np.abs(xx - TROUSER_X[0]) <= 2) | (np.abs(xx - TROUSER_X[1]) <= 2))
        low[..., :3][tline] = (22, 18, 20)
        keep = (yy >= F_BELT[1] - 26) & ~side                              # starts under the torso's belt
        low[..., 3] = (low[..., 3] * keep).astype(np.uint8)
        low[..., 3] = (low[..., 3] * np.clip((yy - F_BELT[1] + 26) / 6.0, 0, 1)).astype(np.uint8)   # soft top edge
        self.low_rgba = low
        base_low = low.copy(); base_low[..., 3] = (base_low[..., 3] * (yy >= HEM_Y + 12)).astype(np.uint8)
        base_low[..., 3] = np.where(yy >= THIGH_Y, front[..., 3], base_low[..., 3])
        base_low[..., :3] = np.where((yy >= THIGH_Y)[..., None], front[..., :3], base_low[..., :3])
        self.lower = (graded_premul(base_low), np.eye(3)[:2])      # below the hem (shared by every pose)
        self._band = {}
        # ---- hanging forearms (screen-left 'L', screen-right 'R') from the FRONT body
        self.hang = {}
        for k, m in (("L", (xx < SLEEVE_X[0] + 6)), ("R", (xx > SLEEVE_X[1] - 6))):
            p = front.copy(); msk = m & (yy >= HANG_TOP) & (yy < 1040)
            cc = front[..., :3].astype(np.int32)
            paper = (cc.min(2) > 175) & ((cc.max(2) - cc.min(2)) < 30) & (yy > 900)     # sheet seen between fingers
            msk &= ~cv2.dilate(paper.astype(np.uint8), K(1)).astype(bool)
            p[..., 3] = (p[..., 3] * msk).astype(np.uint8)
            p[..., 3] = (p[..., 3] * np.clip((yy - HANG_TOP) / 20.0, 0, 1)).astype(np.uint8)
            self.hang[k] = graded_premul(p)
        # ---- torsos (arm poses): knot->knot, belt->belt
        from belts import all_belts
        L = all_landmarks(P)
        BL = all_belts(P)
        for n_ in L: L[n_]["belt"] = BL[n_]
        # the knot anchor is the top of the red knot itself (the landmark finder can stop on the orange neck
        # shadow above it); every pose's knot top goes exactly onto FRONT's knot top
        for n_ in L:
            if n_ not in NO_STUB_CUT: L[n_]["knot"] = knot_top(P["arm"][n_][0], L[n_]["knot"])
        FK = knot_top(front, F_KNOT)
        self.fknot = FK
        base = L["ARMS DOWN"]
        M_base = two_point(base["knot"], base["belt"], F_KNOT, F_BELT, smin=0.1, smax=10)   # ARMS DOWN -> FRONT
        self.torso = {}
        fc = self.front_clothes(front)
        self._fc = fc
        # FRONT's clothes, 2 px inside their edge (so FRONT's own outline shows where a pose is cut to it)
        self._fc_core = cv2.GaussianBlur(cv2.erode((fc[..., 3] > 128).astype(np.uint8), K(2)).astype(np.float32), (0, 0), 0.7)
        for n, (img, _) in P["arm"].items():
            d = L[n]
            # pose -> ARMS DOWN (drawings vary a little in size: clamp) -> FRONT
            M = (to3(M_base) @ to3(two_point(d["knot"], d["belt"], base["knot"], base["belt"], smin=0.74, smax=1.26)))[:2]
            # then exactly: knot on the rig knot, belt on the FRONT belt (shear + vertical scale about the knot),
            # so the torso always meets the legs at the same belt, with its body axis over the hips
            pk = M @ np.array([d["knot"][0], d["knot"][1], 1.0]); pb = M @ np.array([d["belt"][0], d["belt"][1], 1.0])
            sy = (F_BELT[1] - FK[1]) / (pb[1] - pk[1]); sh = (F_BELT[0] - pb[0]) / (F_BELT[1] - FK[1])
            C = np.array([[1, sh, -sh * FK[1]], [0, sy, FK[1] * (1 - sy)], [0, 0, 1]]) @ \
                np.array([[1, 0, FK[0] - pk[0]], [0, 1, FK[1] - pk[1]], [0, 0, 1]])
            M = (C @ to3(M))[:2]
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
            # the neck opening: nothing of the torso above the knot top between the collar points (the head's own
            # neck and collar band show there); hands are kept (they are drawn again in front anyway)
            # stub remnants: small skin / orange bits right above the knot
            orange = skin & (ty < ky + 12) & (np.abs(tx - kx) < 60)
            if n not in NO_STUB_CUT: t[..., 3] = np.where(cv2.dilate(orange.astype(np.uint8), K(2)).astype(bool), 0, t[..., 3])
            # ---- the collar and shoulders are FRONT's on every pose.  FRONT's collar, knot and shoulders lie right
            # behind this drawing (graft_for); here the drawing's neck opening is cut to FRONT's own V between the
            # collar wings (so the neck always enters the same collar), stub scraps go, and its top edge melts into
            # FRONT's shoulders wherever they are behind it (never on hands, never where nothing is behind)
            sc_ = float(M[0, 0])
            rx = M[0, 0] * tx + M[0, 1] * ty + M[0, 2]; ry = M[1, 0] * tx + M[1, 1] * ty + M[1, 2]
            Mi = np.linalg.inv(to3(M))[:2].astype(np.float32)
            cs_ = t[..., :3].astype(np.int32)
            skin_ = (t[..., 3] > 100) & (cs_[..., 2] > cs_[..., 0] + 45) & (cs_[..., 2] > 150) & (cs_[..., 1] > 90)
            n_, lab_, st_, _ = cv2.connectedComponentsWithStats(skin_.astype(np.uint8))
            hand_m = cv2.dilate(np.isin(lab_, [i for i in range(1, n_) if st_[i, cv2.CC_STAT_AREA] >= 900]).astype(np.uint8), K(3)).astype(bool)
            gr, gM, gs = self._graft_for(n, t, M, fc)
            ga = cv2.warpAffine(gr[..., 3], (np.linalg.inv(to3(M)) @ gM)[:2].astype(np.float32), (Wt, Ht)) / 255.0
            if n not in NO_STUB_CUT:
                czone = (ry < F_KNOT[1] + 14) & (np.abs(rx - F_KNOT[0]) < 78)
                cc_ = t[..., :3].astype(np.int32)
                crim = (cc_[..., 2] > 130) & (cc_[..., 1] < 90) & (cc_[..., 2] > cc_[..., 1] + 80) & (cc_[..., 1] < cc_[..., 0] + 25)
                warm = (cc_[..., 2] > cc_[..., 0] + 40) & ~crim & czone & ~hand_m
                t[..., 3] = np.where(cv2.dilate(warm.astype(np.uint8), K(2)).astype(bool), 0, t[..., 3])
                fca = cv2.warpAffine(self._fc_core, Mi, (Wt, Ht))
                t[..., 3] = np.where(czone & ~hand_m, t[..., 3] * fca, t[..., 3]).astype(np.uint8)
            ta = t[..., 3] > 128
            topy = np.where(ta.any(0), np.argmax(ta, axis=0), Ht)
            dxr = np.abs(rx - F_KNOT[0])
            zone = np.clip((dxr - 34) / 12, 0, 1) * np.clip(ga * 1.5 - 0.5, 0, 1) * ~hand_m
            fe = np.clip((ty - topy[None, :]) / (30 / sc_), 0, 1)
            t[..., 3] = (t[..., 3] * (1 - zone * (1 - fe))).astype(np.uint8)
            # bottom edge: melt into the FRONT jacket flaps below
            bot = np.where((t[..., 3] > 0).any(1))[0].max()
            t[..., 3] = (t[..., 3] * np.clip((bot - ty) / 34.0, 0, 1) ** 0.7).astype(np.uint8)
            # hands (and their cuffs) are always in front of the bust / head: a layer of hands only
            front_m = graded_premul(self.hands_only(t, d["knot"]))
            ent = dict(img=graded_premul(t), M=M, front=front_m, knot=d["knot"], hang={k: self.hang_dx(t, M, k) for k in HANGING.get(n, "")},
                       graft=graded_premul(gr), graft_M=gM, gscale=gs)
            if n in extras.MOVERS:
                mv = extras.MOVERS[n]
                mm = extras.mover_mask(img, mv["box"]).astype(np.float32)
                mmb = cv2.GaussianBlur(mm, (0, 0), 1.0)
                bimg = t.copy(); bimg[..., 3] = (bimg[..., 3] * (1 - mmb)).astype(np.uint8)
                mover = t.copy(); mover[..., 3] = (mover[..., 3] * mmb).astype(np.uint8)
                ent.update(img=graded_premul(bimg), mover=graded_premul(mover), pivot=mv["pivot"],
                           front=graded_premul(self.hands_only(bimg, d["knot"])),
                           hole=cv2.dilate(mm, K(10)), mirror=self._mirror_chest(bimg, d["knot"][0], mm), bimg_u8=bimg)
            self.torso[n] = ent
        self._win = {}
        # ARMS DOWN (and POINT LEFT) are cut straight across at the knot by the sheet's red header bar: their collar
        # and shoulders were never drawn.  ARMS DOWN is the FRONT turnaround's own pose, so it becomes the FRONT
        # drawing's clothes (face, beard and neck removed); POINT LEFT gets FRONT's collar + shoulders behind it.
        yyF, xxF = np.mgrid[0:H, 0:W]
        arms_down = fc.copy()
        body_part = (yyF < F_BELT[1] + 30)
        sleeves = ((xxF < SLEEVE_X[0] + 6) | (xxF > SLEEVE_X[1] - 6)) & (yyF < 1040)
        keep = body_part | sleeves
        fade = np.where(sleeves, 1.0, np.clip((F_BELT[1] + 30 - yyF) / 34.0, 0, 1) ** 0.7)
        arms_down[..., 3] = (arms_down[..., 3] * keep * fade).astype(np.uint8)
        kx0, ky0 = F_KNOT
        self.torso["ARMS DOWN"] = dict(img=graded_premul(arms_down), M=np.eye(3)[:2], knot=(kx0, ky0), hang={},
                                       front=graded_premul(self.hands_only(arms_down, (kx0, ky0))))
        # the chest behind a moving hand, inside that hand's (grown) area: the arm-pose drawing whose chest there is
        # clear of hands and matches this pose best around the hole (all poses share the knot/belt frame, so tie
        # and lapels line up); under it the pose's own chest mirrored across the tie, inpainted where that is empty
        ad = self.torso["ARMS DOWN"]
        for n, ent in self.torso.items():
            if "hole" not in ent: continue
            Ht_, Wt_ = ent["hole"].shape[:2]
            A = (np.linalg.inv(to3(ent["M"])) @ to3(ad["M"]))[:2].astype(np.float32)      # FRONT px -> pose px
            fr = cv2.warpAffine(ad["img"], A, (Wt_, Ht_))
            mi = ent.pop("mirror"); bim = ent.pop("bimg_u8")
            ma = mi[..., 3] > 128
            known = ma | (bim[..., 3] > 128)
            src = np.where(ma[..., None], mi[..., :3], bim[..., :3])
            rgb = cv2.inpaint(np.ascontiguousarray(src), (~known).astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA)
            body = np.maximum(mi[..., 3].astype(np.float32) / 255, fr[..., 3])            # the chest's extent
            u = graded_premul(np.dstack([rgb, (np.clip(body, 0, 1) * 255).astype(np.uint8)]))
            hole = ent["hole"] > 0.5
            ring = cv2.dilate(hole.astype(np.uint8), K(22)).astype(bool) & ~hole & (ent["img"][..., 3] > 0.95)
            best = None
            for cn, c in self.torso.items():
                if cn in (n, "ARMS DOWN") or "hole" in c: continue
                Ac = (np.linalg.inv(to3(ent["M"])) @ to3(c["M"]))[:2].astype(np.float32)
                ci = cv2.warpAffine(c["img"], Ac, (Wt_, Ht_)); cf = cv2.warpAffine(c["front"], Ac, (Wt_, Ht_))
                if (cf[..., 3][hole] > 0.3).mean() > 0.02: continue          # its own hands are in the way
                diff = float(np.abs(ci[..., :3][ring] - ent["img"][..., :3][ring]).mean())
                if best is None or diff < best[0]: best = (diff, cn, ci)
            if best is not None:
                ent["plate"] = best[1]
                u = best[2] + u * (1 - best[2][..., 3:4])
            hm = cv2.GaussianBlur(ent["hole"], (0, 0), 2)
            ent["under"] = u * hm[..., None]
            ent["under_M"] = ent["M"]
        # ---- heads: face/hair/neck layer (moves) + the drawing's own collar, knot and lapels = the bust (fixed)
        from headfit import collar_mask
        self.head = {}
        for n, (img, _) in P["head"].items():
            if n == "THINKING": continue                    # its hand covers the collar: not used
            # the head cell stops just under the knot; continue its bottom rows (suit, shirt) downwards so that
            # behind the torso there is always suit - whatever height a pose drawing's shoulders are at
            rows = np.where((img[..., 3] > 200).sum(1) > 0.5 * img.shape[1])[0]
            last = int(rows.max()) - 2                                  # last solid row (above the soft bottom edge)
            ext = cv2.copyMakeBorder(img[:last + 1], 0, HEAD_EXT, 0, 0, cv2.BORDER_REPLICATE)
            ext[last + 1:, :, :3] = cv2.blur(ext[last + 1:, :, :3], (9, 1))
            # the continued rows: only the suit itself, and the shirt/tie in the middle (never edge pixels)
            lr = ext[last, :, :3].astype(np.int32); lv = lr.max(1); ls = lv - lr.min(1)
            kxe = float(np.median(np.where((lr[:, 2] > 130) & (lr[:, 1] < 90))[0])) if ((lr[:, 2] > 130) & (lr[:, 1] < 90)).any() else img.shape[1] / 2
            okc = ((ls < 30) & (lv > 55) & (lv < 180)) | (np.abs(np.arange(img.shape[1]) - kxe) < 70)
            okc = cv2.erode(okc.astype(np.uint8)[None, :], np.ones((1, 9), np.uint8))[0].astype(bool)
            ext[last + 1:, :, 3] = (ext[last + 1:, :, 3] * okc[None, :]).astype(np.uint8)
            img = ext
            last_row = last
            cm, kn = collar_mask(img)
            base, alpha = self.head_layer(img, cm)
            und = self._last_under
            neck = np.dstack([base, (und * alpha.astype(np.float32) / 255 * 255).astype(np.uint8)])
            alpha = (alpha * ~und).astype(np.uint8)                       # the neck fill goes behind the collar
            H_, W_ = img.shape[:2]
            yy_ = np.arange(H_)[:, None]
            # bust = the drawing's jacket collar / lapel tops (everything that is not head and not collar); per torso
            # it is kept only above that torso's shoulder line (bust_for), so the torso's own lapels run on below
            ha = alpha.astype(np.float32) / 255
            ba = img[..., 3].astype(np.float32) / 255 * np.clip(1 - ha * 1.5, 0, 1) * (1 - cm.astype(np.float32))
            ba[:int(kn[1] - 140)] = 0
            bust = img.copy(); bust[..., 3] = (np.clip(ba, 0, 1) * 255).astype(np.uint8)
            cs = cv2.GaussianBlur(cv2.dilate(cm.astype(np.uint8), K(1)).astype(np.float32), (0, 0), 1.2)
            red_ = classes(img)[0]
            botk = np.where((red_ & cm).any(1))[0].max() if (red_ & cm).any() else H_
            cs *= np.clip((botk + 2 - yy_) / 6.0, 0, 1)                      # soft bottom edge on the knot
            col = img.copy(); col[..., 3] = (col[..., 3] * cs).astype(np.uint8)
            full = img.copy()
            fy = np.clip((H_ - 4 - yy_) / 10.0, 0, 1)
            full[..., 3] = (full[..., 3] * fy).astype(np.uint8)
            c_ = img[..., :3].astype(np.int32); v_ = c_.max(2); sat_ = v_ - c_.min(2)
            xx_ = np.arange(W_)[None, :]
            jk = (img[..., 3] > 30) & (sat_ < 34) & (v_ < 190) & (yy_ > kn[1] - 170)      # jacket / its outline
            jk &= ~((c_[..., 2] > c_[..., 0] + 25) & (sat_ > 20))                         # not hair / skin
            core = cv2.morphologyEx(jk.astype(np.uint8), cv2.MORPH_OPEN, K(3))
            jk = cv2.dilate(core, K(4)).astype(bool) & (img[..., 3] > 0) & ~((c_[..., 2] > c_[..., 0] + 25) & (sat_ > 40))
            self.head[n] = dict(raw=img, base=img[..., :3].copy(), alpha=full[..., 3],
                                img=graded_premul(full), jacket=jk, neck=np.zeros((2, 2, 4), np.float32), last=last_row,
                                bust=graded_premul(bust), bust_a=ba, knot=kn, collar=graded_premul(col), cm=cm,
                                s=float(np.sqrt(abs(np.linalg.det(R["head"][n][:, :2])))))

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

    def head_layer(self, img, cm):
        """-> (colour, alpha) of the moving head: hair, face, ears, beard and neck, cut column by column at the
        top edge of the collar.  Under the collar the neck is continued downwards (inside the neck's own width
        only), so a nod shows neck, never a gap; any enclosed pocket is filled so nothing is see-through."""
        red, skin, white, grey = classes(img)
        H, W = img.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        kx, ky = [float(v) for v in cm_knot(cm)]
        col = img[..., :3].copy()
        c = img[..., :3].astype(np.int32); v = c.max(2); sat = v - c.min(2)
        a = img[..., 3].astype(np.float32) / 255
        has = cm.any(0)
        ctop = np.where(has, np.argmax(cm, axis=0), H)                    # collar top edge per column
        hx = np.where(has)[0]
        # the collar's top edge only climbs from the knot out to the tips (its shaded outer edge is grey, not
        # white): running minimum outward from the centre, then continued flat past the tips
        xc = int(round(kx))
        cext = ctop.astype(np.int64).copy()
        cext[xc:] = np.minimum.accumulate(cext[xc:])
        cext[:xc + 1] = np.minimum.accumulate(cext[:xc + 1][::-1])[::-1]
        keep = yy < cext[None, :]
        # beyond the collar: the jacket (low-saturation grey / dark, below the jaw) is not head
        jacket = (sat < 32) & (v < 205) & (yy > ky - 120) & ~has[None, :]
        n, lab, st, _ = cv2.connectedComponentsWithStats(jacket.astype(np.uint8))
        jk = np.zeros((H, W), bool)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_TOP] + st[i, cv2.CC_STAT_HEIGHT] >= H - 18 and st[i, cv2.CC_STAT_AREA] > 200: jk |= lab == i
        keep &= ~cv2.dilate(jk.astype(np.uint8), K(2)).astype(bool)
        # neck under the collar: columns where there is skin just above the collar edge
        neck_cols = np.zeros(W, bool)
        for x in np.where(has)[0]:
            y0 = ctop[x]
            if skin[max(0, y0 - 12):y0, x].sum() >= 3: neck_cols[x] = True
        nc = np.where(neck_cols)[0]
        under = np.zeros((H, W), bool)
        if len(nc):
            span = np.zeros(W, bool); span[nc.min() + 4:nc.max() - 3] = True
            under = span[None, :] & (yy >= ctop[None, :] - 2) & (yy < ctop[None, :] + 46)
            under &= cv2.dilate(cm.astype(np.uint8), K(2)).astype(bool) & (yy < ky + 6)     # never past the collar
            for x in np.where(span)[0]:
                y0 = ctop[x]
                src = np.where(skin[max(0, y0 - 25):y0, x])[0]
                cc = col[max(0, y0 - 25) + src[-1], x] if len(src) else col[max(0, y0 - 3), x]
                col[y0 - 2:y0 + 46, x] = (np.float32(cc) * np.linspace(1.0, 0.82, len(range(y0 - 2, min(H, y0 + 46))))[:, None]).astype(np.uint8)
            col = np.where(under[..., None], cv2.GaussianBlur(col, (0, 0), 1.5), col)
        m = (keep & (a > 0.02)) | under
        # main piece only, all enclosed pockets filled
        n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8))
        main = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
        cnts, _ = cv2.findContours(main, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        filled = np.zeros_like(main); cv2.drawContours(filled, cnts, -1, 1, -1)
        holes = filled.astype(bool) & ~main.astype(bool)
        n, lab, st, _ = cv2.connectedComponentsWithStats(holes.astype(np.uint8))
        holes = np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] < 1500])      # small pockets only
        filled = (main.astype(bool) | holes).astype(np.uint8)
        alpha = np.where(filled.astype(bool), np.where(holes | under, 1.0, a), 0.0)
        alpha = np.where(main.astype(bool) & ~under & keep, a, alpha)
        edge = cv2.GaussianBlur(filled.astype(np.float32), (0, 0), 0.7)
        alpha = np.minimum(alpha, np.maximum(edge, alpha * (filled > 0)))
        self._last_under = under
        return col, (np.clip(alpha, 0, 1) * 255).astype(np.uint8)

    def _mirror_chest(self, bimg, kx, mm):
        """premul: the pose drawing (moving hand removed) mirrored across the tie's axis, its own hand's mirror
        and small white marks (the pocket square) painted out."""
        H, W = bimg.shape[:2]
        # mirror axis = the tie's centre line (it leans): a line fitted through the visible tie rows
        c = bimg[..., :3].astype(np.int32)
        crim = (bimg[..., 3] > 128) & (c[..., 2] > 130) & (c[..., 1] < 90) & (c[..., 2] > c[..., 1] + 80)
        crim &= (np.abs(np.arange(W)[None, :] - kx) < 90)
        ys, xs = [], []
        for y in range(H):
            r_ = np.where(crim[y])[0]
            if 8 <= len(r_) and r_.max() - r_.min() < 90: ys.append(y); xs.append((r_.min() + r_.max()) / 2)
        if len(ys) > 20:
            p = np.polyfit(ys, xs, 1)
            axis = np.polyval(p, np.arange(H)).astype(np.float32)
        else:
            axis = np.full(H, kx, np.float32)
        mapx = (2 * axis[:, None] - np.arange(W, dtype=np.float32)[None, :]).astype(np.float32)
        mapy = np.repeat(np.arange(H, dtype=np.float32)[:, None], W, 1)
        f = cv2.remap(bimg, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        c = f[..., :3].astype(np.int32); v = c.max(2); sat = v - c.min(2)
        wm = (f[..., 3] > 128) & (v > 200) & (sat < 30)
        n, lab, st, _ = cv2.connectedComponentsWithStats(wm.astype(np.uint8))
        small = np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] < 2500])
        small = cv2.dilate(small.astype(np.uint8), K(4))
        f[..., :3] = np.where(small[..., None] > 0, cv2.inpaint(np.ascontiguousarray(f[..., :3]), small * 255, 7, cv2.INPAINT_TELEA), f[..., :3])
        mh = cv2.remap(mm, mapx, mapy, cv2.INTER_LINEAR)                             # where the hand was, mirrored
        f[..., 3] = (f[..., 3] * np.clip(1 - cv2.dilate(mh, K(6)), 0, 1)).astype(np.uint8)
        return f

    def _graft_for(self, n, t, M, fc):
        """FRONT's collar, knot and shoulders to go behind pose n -> (rgba, 3x3 crop->rig).  Beyond the collar each
        side is scaled to this drawing's own shoulder width; each column stays solid down to where the drawing's
        feathered top edge is solid, then fades out."""
        H, W = fc.shape[:2]
        KX, KY = F_KNOT
        ka = cv2.warpAffine((t[..., 3] > 128).astype(np.uint8), M.astype(np.float32), (W, H), flags=cv2.INTER_NEAREST) > 0
        fa = fc[..., 3] > 128
        band = slice(int(KY + 40), int(KY + 80))                          # below the shoulder slope
        def ext(m, side):
            cols = np.where(m[band].any(0))[0]
            return KX - cols.min() if side < 0 else cols.max() - KX
        s = {side: float(np.clip((ext(ka, side) - 60) / max(1.0, ext(fa, side) - 60), 0.3, 1.08)) for side in (-1, 1)}
        xd = np.arange(W, dtype=np.float32) - KX
        src = np.where(xd < -60, -60 + (xd + 60) / s[-1], np.where(xd > 60, 60 + (xd - 60) / s[1], xd)) + KX
        y0, y1 = int(KY - 150), int(KY + 130)
        mapx = np.repeat(src[None, :], y1 - y0, 0).astype(np.float32)
        mapy = np.repeat(np.arange(y0, y1, dtype=np.float32)[:, None], W, 1)
        g = cv2.remap(fc, mapx, mapy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        has = ka.any(0)
        top = np.where(has, np.argmax(ka, 0), 0).astype(np.float32)
        lim = np.clip(np.where(has, top + 50, KY + 62), KY + 62, KY + 110)
        lim = cv2.GaussianBlur(lim[None, :].astype(np.float32), (0, 0), 6)[0]
        yy = np.arange(y0, y1, dtype=np.float32)[:, None]
        g[..., 3] = (g[..., 3] * np.clip((lim[None, :] - yy) / 16.0, 0, 1)).astype(np.uint8)
        return g, np.array([[1, 0, 0], [0, 1, y0], [0, 0, 1]], np.float64), (s[-1], s[1])

    def torso_top(self, torso):
        """rig x -> top edge y of the torso drawing, FRONT's shoulders behind it included (in the rig frame)"""
        d = self.torso[torso]
        if "top" not in d:
            a = cv2.warpAffine(d["img"][..., 3], d["M"].astype(np.float32), (900, 1200))
            if "graft" in d:
                a = np.maximum(a, cv2.warpAffine(d["graft"][..., 3], d["graft_M"][:2].astype(np.float32), (900, 1200)))
            top = np.full(900, np.inf)
            has = (a > 0.6).any(0)
            top[has] = np.argmax(a[:, has] > 0.6, axis=0)
            d["top"] = top
        return d["top"]

    def band_for(self, torso):
        """FRONT's belt-to-hem band (jacket flaps + trouser tops), warped sideways so that its outer edges meet this
        torso's outer edges where the torso ends, relaxing back to FRONT's own shape by the hem."""
        if torso in self._band: return self._band[torso]
        d = self.torso[torso]
        low = self.low_rgba
        H, W = low.shape[:2]
        ta = cv2.warpAffine(d["img"][..., 3], d["M"].astype(np.float32), (W, H))
        la = low[..., 3] > 128
        cx = int(F_BELT[0])
        rows = np.where((ta[:, cx - 60:cx + 60] > 0.5).any(1))[0]
        ym = int(min(rows.max() - 22, HEM_Y - 20)) if len(rows) else int(F_BELT[1] + 30)
        ym = max(ym, int(F_BELT[1] + 18))                                  # inside the legs layer
        def edges(mask, y, gap=10):
            """outer edges of the body run around the centre (gaps under `gap` px are bridged)"""
            r = mask[y]
            if not r[max(0, cx - 30):cx + 30].any(): return cx, cx
            L = cx
            while L > 0:
                seg = r[max(0, L - gap):L]
                if not seg.any(): break
                L = max(0, L - gap) + int(np.where(seg)[0].min())
                if L == 0 or not r[L - 1]:
                    if not r[max(0, L - gap):L].any(): break
                else:
                    while L > 0 and r[L - 1]: L -= 1
            R = cx
            while R < W - 1:
                seg = r[R + 1:R + 1 + gap]
                if not seg.any(): break
                R = R + 1 + int(np.where(seg)[0].max())
                while R < W - 1 and r[R + 1]: R += 1
            return L, R
        fl, fr = edges(la, ym)
        tl, tr = edges(ta > 0.5, ym); raw_t = (tl, tr)
        if fr - fl < 100: tl, tr = fl, fr = int(SLEEVE_X[0]), int(SLEEVE_X[1])
        hang = HANGING.get(torso, "")
        if "L" in hang or cx - tl > 262 or cx - tl < 40: tl = fl        # a hanging arm / no body there: FRONT edge
        if "R" in hang or tr - cx > 262 or tr - cx < 40: tr = fr
        self.band_dbg = getattr(self, "band_dbg", {}); self.band_dbg[torso] = (ym, raw_t, (tl, tr), (fl, fr))
        fl, fr = float(SLEEVE_X[0]), float(SLEEVE_X[1])
        if "L" in hang: tl = fl
        if "R" in hang: tr = fr
        tl = min(tl, TROUSER_X[0] - 8); tr = max(tr, TROUSER_X[1] + 8)   # the jacket is never narrower than the legs
        y0, y1 = int(F_BELT[1] - 26), int(HEM_Y + 20)
        yy = np.arange(y0, y1)[:, None].astype(np.float32)
        u = np.clip((yy - HEM_Y) / 12.0, 0, 1)                             # jacket rows: torso width; ends at the hem
        Lo = tl + (fl - tl) * u; Ro = tr + (fr - tr) * u
        ci = 60.0                                                          # the trouser front between the flaps stays put
        xo = np.arange(W)[None, :].astype(np.float32)
        mapx = xo + 0 * yy
        lft = xo < cx - ci; rgt = xo > cx + ci
        mapx = np.where(lft, (cx - ci) - ((cx - ci) - xo) * ((cx - ci) - fl) / np.maximum((cx - ci) - Lo, 1), mapx)
        mapx = np.where(rgt, (cx + ci) + (xo - (cx + ci)) * (fr - (cx + ci)) / np.maximum(Ro - (cx + ci), 1), mapx)
        mapx = mapx.astype(np.float32)
        mapy = np.broadcast_to(yy, mapx.shape).astype(np.float32)
        band = cv2.remap(low, mapx, mapy, cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))
        band[..., 3] = (band[..., 3] * np.clip((y1 - yy[:, 0:1]) / 8.0, 0, 1)).astype(np.uint8)
        # a drawn outline down the jacket's new sides (FRONT's cut there has none)
        ba = band[..., 3] > 128
        edge = ba & ~cv2.erode(ba.astype(np.uint8), np.ones((1, 7), np.uint8)).astype(bool)
        edge[int(HEM_Y - y0 + 2):] = False
        band[..., :3][edge] = (band[..., :3][edge] * 0.25 + np.array([22, 18, 20]) * 0.75).astype(np.uint8)
        out = graded_premul(band)
        self._band[torso] = (out, np.array([[1, 0, 0], [0, 1, y0], [0, 0, 1]], np.float64))
        return self._band[torso]

    def windowed(self, pm, M, head):
        """premultiplied torso image with its shirt V / knot cut away wherever this head's collar layer (or the
        head itself) covers it: the head drawing's collar and knot show there instead."""
        key = (id(pm), head)
        if key in self._win: return self._win[key]
        hd = self.head[head]
        A = (np.linalg.inv(to3(M)) @ self.head_to_rig(head))[:2].astype(np.float32)     # head px -> torso px
        H, W = pm.shape[:2]
        cov = np.maximum(hd["collar"][..., 3], hd["img"][..., 3] * (hd["img"][..., 3] > 0.9))
        cov = cv2.warpAffine(cov.astype(np.float32), A, (W, H))
        cov = cv2.erode((cov > 0.6).astype(np.uint8), K(2)).astype(bool)
        a = pm[..., 3]
        c = pm[..., :3] / np.maximum(a[..., None], 1e-3)
        v = c.max(2); sat = v - c.min(2)
        shirt = (v > 175) & (sat < 45)
        tie = (c[..., 2] > 120) & (c[..., 1] < 90) & (c[..., 2] > c[..., 1] + 80)
        win = (shirt | tie | (v < 70)) & cov & (a > 0.05)
        f = 1 - cv2.GaussianBlur(win.astype(np.float32), (0, 0), 0.8)
        out = (pm * f[..., None]).astype(np.float32)
        self._win[key] = out
        return out

    def front_clothes(self, front):
        """the FRONT turnaround with its face, hair, beard and neck removed: collar, knot, jacket, arms remain."""
        H, W = front.shape[:2]
        yy, xx = np.mgrid[0:H, 0:W]
        c = front[..., :3].astype(np.int32); b, g, r = c[..., 0], c[..., 1], c[..., 2]
        v = c.max(2); sat = v - c.min(2); a = front[..., 3] > 30
        red = (r > 130) & (g < 90) & (r > g + 80) & (g < b + 25)         # the tie's crimson (not the orange neck shadow)
        grey = (sat < 30) & (v >= 45) & (v <= 190)
        white = (v > 190) & (sat < 30) & (b >= r - 8)
        clothes = a & (red | grey | white)
        n, lab, st, _ = cv2.connectedComponentsWithStats((clothes & (yy > 320)).astype(np.uint8))
        keep = np.zeros((H, W), bool)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] > 400 and st[i, cv2.CC_STAT_TOP] + st[i, cv2.CC_STAT_HEIGHT] > 400: keep |= lab == i
        warm = (r > b + 18) & ~red
        dark = a & (v < 60) & (yy > 320) & ~(warm & (yy < F_KNOT[1] - 20))     # outlines, never hair strands
        keep |= dark & cv2.dilate(keep.astype(np.uint8), K(4)).astype(bool)
        keep = cv2.morphologyEx(keep.astype(np.uint8), cv2.MORPH_CLOSE, K(2)).astype(bool)
        # enclosed holes (the knot's highlight) are clothes too
        n, lab = cv2.connectedComponents((~keep).astype(np.uint8), connectivity=4)
        border = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        keep |= ~np.isin(lab, border) & a
        # above the collar points only solid cloth (+ its outline): thin hair strands go
        solid = cv2.dilate(cv2.morphologyEx((keep & (grey | white)).astype(np.uint8), cv2.MORPH_OPEN, K(4)), K(3)).astype(bool)
        keep &= ~(yy < F_KNOT[1] - 50) | solid
        keep |= (yy >= F_KNOT[1] + 30) & a                                 # everything from the chest down
        n, lab, st, _ = cv2.connectedComponentsWithStats(keep.astype(np.uint8), connectivity=4)
        keep &= np.isin(lab, [i for i in range(1, n) if st[i, cv2.CC_STAT_AREA] >= 500])     # no loose specks
        out = front.copy()
        out[..., 3] = (front[..., 3] * cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 0.8)).astype(np.uint8)
        return out

    def hands_only(self, t, knot):
        """rgba: just the hands and cuffs of a torso drawing (never its collar, knot, shirt or neck stub)."""
        c = t[..., :3].astype(np.int32); b, g, r = c[..., 0], c[..., 1], c[..., 2]
        a = t[..., 3] > 100
        H, W = a.shape
        yy, xx = np.mgrid[0:H, 0:W]
        skin = a & (r > b + 45) & (r > 150) & (g > 90) & ~((g < 85) & (r > g + 90))
        n, lab, st, cen = cv2.connectedComponentsWithStats(skin.astype(np.uint8))
        hands = np.zeros((H, W), bool)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < 900: continue
            if st[i, cv2.CC_STAT_TOP] < knot[1] + 25 and abs(cen[i][0] - knot[0]) < 70: continue    # neck stub
            hands |= lab == i
        hands = cv2.morphologyEx(hands.astype(np.uint8), cv2.MORPH_CLOSE, K(3)).astype(bool)
        v = c.max(2); sat = v - c.min(2)
        cuff = a & (v > 185) & (sat < 40) & cv2.dilate(hands.astype(np.uint8), K(16)).astype(bool)
        red = a & (g < 85) & (r > g + 90)
        m = (cv2.dilate(hands.astype(np.uint8), K(5)).astype(bool) | cuff) & a & ~red
        out = t.copy(); out[..., 3] = (t[..., 3] * cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.8)).astype(np.uint8)
        return out

    def head_mask(self, head, torso):
        """per head+torso alpha multiplier: the head drawing's jacket only where it fills the space between the
        neck and this torso's shoulders (at most JACKET_UP px above the torso's top edge), never a second shoulder."""
        key = (head, torso)
        if not hasattr(self, "_hmask"): self._hmask = {}
        if key in self._hmask: return self._hmask[key]
        hd = self.head[head]; A = self.head_to_rig(head, torso)
        d = self.torso[torso]
        H, W = hd["raw"].shape[:2]
        top = self.torso_top(torso)
        xs = np.clip((A[0, 0] * np.arange(W) + A[0, 2]).round().astype(int), 0, len(top) - 1)
        t = top[xs]
        ry = A[1, 1] * np.arange(H) + A[1, 2]
        above = t[None, :] - ry[:, None]                                  # rig px above the torso top (inf: no torso)
        rx = A[0, 0] * np.arange(W) + A[0, 2]
        # distance from the neck measured on FRONT's shoulders (a pose's shoulders are FRONT's, scaled per side)
        sl, sr = d.get("gscale", (1.0, 1.0))
        rxs = rx - F_KNOT[0]
        dx = np.where(rxs < -60, 60 + (-rxs - 60) / sl, np.where(rxs > 60, 60 + (rxs - 60) / sr, np.abs(rxs)))[None, :]
        # the jacket collar may rise above the torso's shoulders beside the neck, sloping down to them outward
        hmax = np.clip((SLOPE_END - dx) / (SLOPE_END - NECK_ZONE), 0, 1) * SLOPE_UP + JACKET_UP
        hmax = np.where(dx <= NECK_ZONE, 1e9, hmax)
        inside = np.where(np.isfinite(above), above <= hmax, dx <= NECK_ZONE)
        raw = hd["raw"][..., :3].astype(np.int32)
        neutral = (raw.max(2) - raw.min(2)) < 34
        jk = hd["jacket"] | (neutral & (dx > NECK_ZONE) & (ry[:, None] > F_KNOT[1] - 90) & (hd["raw"][..., 3] > 0))
        keep = ~jk | inside
        # the continued rows below the drawing's own bottom only ever fill in behind the torso
        extrow = (np.arange(H) > hd["last"])[:, None]
        hidden = np.where(np.isfinite(above), above <= -2, False)
        keep &= ~extrow | hidden | (dx <= NECK_ZONE)
        m = keep.astype(np.float32)
        m = cv2.GaussianBlur(m, (0, 0), 0.7)
        # a drawn outline where the jacket was trimmed (not along its own outline)
        fin = cv2.erode(np.isfinite(above).astype(np.uint8), np.ones((1, 9), np.uint8)).astype(bool)   # not at a side edge
        cut = jk & inside & ~cv2.erode(inside.astype(np.uint8), K(3)).astype(bool) & (hd["raw"][..., 3] > 200) & fin
        ol = np.zeros((H, W, 4), np.float32)
        ol[cut] = (22.0, 18.0, 20.0, 1.0)
        ol = cv2.GaussianBlur(ol, (0, 0), 0.6)
        self._houtline = getattr(self, "_houtline", {}); self._houtline[key] = ol
        self._hmask[key] = m[..., None]
        return self._hmask[key]

    def bust_for(self, head, torso):
        """the head drawing's jacket collar, kept above this torso's top edge (+ a short fade below it)."""
        key = (head, torso)
        if not hasattr(self, "_bust"): self._bust = {}
        if key in self._bust: return self._bust[key]
        hd = self.head[head]; A = self.head_to_rig(head, torso)
        H, W = hd["bust"].shape[:2]
        top = self.torso_top(torso)
        xs = np.clip((A[0, 0] * np.arange(W) + A[0, 2]).round().astype(int), 0, len(top) - 1)
        t = top[xs]
        kyr = F_KNOT[1]
        shoulder = np.isfinite(t) & (t < kyr + 70)                        # columns where the torso has shoulders
        t = np.where(shoulder, t, -1e9)
        # rig y of each head row, and how far below the torso top it is (rig px)
        ry = A[1, 1] * np.arange(H) + A[1, 2]
        below = ry[:, None] - t[None, :]
        f = np.clip(1 - (below - 6) / 16.0, 0, 1)                         # opaque to 6 px below, gone by 22 px
        f = cv2.GaussianBlur(f.astype(np.float32), (0, 0), 2.0)            # soft sides where the shoulders end
        b = hd["bust"] * f[..., None]
        self._bust[key] = b.astype(np.float32)
        return self._bust[key]

    def shoulder_y(self, torso):
        """median height of the torso's top edge beside the collar (rig px)"""
        top = self.torso_top(torso); d = self.torso[torso]
        kx, ky = (d["M"] @ np.array([d["knot"][0], d["knot"][1], 1.0]))
        v = [top[int(kx + dx)] for dx in (-120, -105, -90, -75, -60, 60, 75, 90, 105, 120)]
        v = [y for y in v if np.isfinite(y) and y < ky + 60]
        return float(np.median(v)) if v else float(ky)

    def head_to_rig(self, head, torso=None):
        """3x3 head px -> rig px: the face scale (the head matches the turnaround's head size), the drawing's tie
        knot centred at the rig's knot and SEAT px lower, so the bust's lapels overlap the (shoulder-aligned)
        torsos.  Identical for every torso: the head never jumps when the arm pose changes."""
        hd = self.head[head]
        s_ = hd["s"]; hkx, hky = hd["knot"]
        return np.array([[s_, 0, F_KNOT[0] - s_ * hkx], [0, s_, F_KNOT[1] + SEAT - s_ * hky], [0, 0, 1]])

    # ------------------------------------------------------------------ assembling a pose
    def layers(self, torso, head, head_img=None, head_M=None, torso_M=None, hang=None, hand_M=None):
        """ordered list of (premultiplied RGBA float32, 3x3 matrix source->rig).
        head_M: head motion in rig px (rotation about the collar), torso_M: torso lean/bounce (rig frame), applied
        to everything above the legs.  hand_M: motion of a MOVER hand in its pose's own coords."""
        T = to3(torso_M) if torso_M is not None else np.eye(3)
        Hm = to3(head_M) if head_M is not None else np.eye(3)
        d = self.torso[torso]; hd = self.head[head]
        Mh = T @ self.head_to_rig(head, torso)
        out = []
        out.append((self.lower[0], np.eye(3)))
        bimg, bM = self.band_for(torso)
        out.append((bimg, bM))
        sides = d["hang"] if hang is None else hang
        for k, dx in sides.items():
            out.append((self.hang[k], T @ np.array([[1, 0, dx], [0, 1, 0], [0, 0, 1]], np.float64)))
        Mm = T @ Hm @ np.linalg.inv(T) @ Mh                              # the head's motion
        # the head (face, hair, neck) goes BEHIND the torso: its neck tucks down into the torso's own collar, so
        # the collar, the knot and the tie are always the torso drawing's own and always match
        out.append(((hd["img"] if head_img is None else head_img) * self.head_mask(head, torso), Mm))
        out.append((self._houtline[(head, torso)], Mm))
        if "graft" in d: out.append((d["graft"], T @ d["graft_M"]))      # FRONT's collar + shoulders behind
        if "under" in d: out.append((d["under"], T @ to3(d["under_M"])))
        out.append((d["img"], T @ to3(d["M"])))
        out.append((d["front"], T @ to3(d["M"])))
        if "mover" in d:
            out.append((d["mover"], T @ to3(d["M"]) @ (hand_M if hand_M is not None else np.eye(3))))
        return out

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

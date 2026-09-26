"""Walking legs: a cut-out leg rig (thigh / shin / shoe) with planted feet.

The sheet's WALK drawings can't be swapped in as a cycle: in WALK 1 and WALK 2 the planted shoe points backwards
while the other points forwards, and the four drawings don't line up with each other.  So the walk is rigged:
  - one leg (the front leg of WALK 3: straight, shoe flat, pointing the way he walks) is cut into thigh, shin and
    shoe, with rounded overlaps at the knee and the trouser cuff over the shoe;
  - the near leg uses it as drawn, the far leg is the same leg a little darker, behind and higher (3/4 depth);
  - each foot is locked to its spot on the floor (in world space, so it holds while he walks into depth), rolls
    heel -> flat -> toe, swings forward, and lands heel first; the knees are solved from hip and ankle (2-bone IK)
    and the hips drop just enough for the standing leg to reach, which gives the natural walk bob;
  - every walk starts and ends in the passing position (feet together), so it joins the standing turn frames.
Both shoes always point the way he walks: a leftward walk mirrors the whole rig."""
import numpy as np, cv2
from rig import graded_premul, K, to3

SRC = "WALK 3"
PAD = 60                    # rows added above the drawing (the thigh continues up under the jacket)
LEG_SCALE = 1.45            # sheet legs -> turnaround body px
LAT = 55.0                  # rig px: each hip either side of the body's centre line
FAR_DY = 20.0               # rig px: the far leg stands this much higher (further from camera)
FAR_SHADE = 0.80
# cycle: phase 0 = heel strike; stance until TOE_OFF; the hips pass over the planted foot at MID
TOE_OFF = 0.62
MID = 0.31
STEP = 380.0                # rig px per step, about 0.7 x leg length (a full cycle is two steps)
LIFT = 38.0                 # rig px the swinging ankle rises above its straight path
PSI_STRIKE = 16.0           # deg toe up at heel strike
PSI_OFF = 32.0              # deg heel up at toe off

def rot(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s], [s, c]])

def smooth(u):
    u = np.clip(u, 0.0, 1.0); return u * u * (3 - 2 * u)

def T3(x, y): return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], np.float64)

def R3(a):
    M = np.eye(3); M[:2, :2] = rot(a); return M

def S3(s): return np.array([[s, 0, 0], [0, s, 0], [0, 0, 1]], np.float64)

class LegSprites:
    """the leg cut into thigh / shin / foot, in the source drawing's px (padded), facing screen-right."""
    def __init__(self, P):
        img = P["leg"][SRC][0]
        a = img[..., 3] > 128
        H, W = a.shape
        runs = []
        for y in range(H):
            xs = np.where(a[y])[0]
            if not len(xs): runs.append([]); continue
            br = np.where(np.diff(xs) > 1)[0]
            runs.append(list(zip([xs[0]] + list(xs[br + 1]), list(xs[br]) + [xs[-1]])))
        two = [y for y in range(H) if len(runs[y]) >= 2 and runs[y][-1][1] - runs[y][-1][0] > 40]
        crotch = min(y for y in two if y < H * 0.6)
        # the front leg: right of the gap below the crotch; above it, right of its inner edge carried straight up
        ys = np.array([y for y in range(crotch + 2, crotch + 90) if len(runs[y]) >= 2])
        le = np.array([runs[y][-1][0] for y in ys], np.float64)
        kx, bx = np.polyfit(ys, le, 1)
        split = np.zeros(H)
        for y in range(H):
            if y >= crotch and len(runs[y]) >= 2: split[y] = (runs[y][-2][1] + runs[y][-1][0]) / 2
            else: split[y] = kx * y + bx - 2
        yy, xx = np.mgrid[0:H, 0:W]
        front = a & (xx >= split[:, None])
        # axis: centre line of the leg between the crotch and the cuff
        cy = np.arange(crotch + 10, int(H * 0.80))
        cx = np.array([(np.where(front[y])[0].min() + np.where(front[y])[0].max()) / 2 for y in cy])
        ka, ba = np.polyfit(cy, cx, 1)
        axis_x = lambda y: ka * y + ba
        # shoe: the black leather (and its glints) below the trouser cuff
        c = img[..., :3].astype(np.int32); v = c.max(2); sat = v - c.min(2)
        trouser = (v >= 62) & (v <= 175) & (sat < 32)
        low = yy > H * 0.76
        shoe = front & low & ~trouser
        n, lab, st, _ = cv2.connectedComponentsWithStats(shoe.astype(np.uint8))
        shoe = lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        shoe = cv2.morphologyEx(shoe.astype(np.uint8), cv2.MORPH_CLOSE, K(3)).astype(bool) & front
        sy, sx = np.where(shoe)
        sole = float(sy.max())
        cuff = float(np.percentile(sy, 3))                                      # top of the visible shoe
        heel = float(sx[sy > sole - 12].min()); toe = float(sx.max())
        # joints (source px, before padding)
        hip = np.array([axis_x(crotch - 90.0), crotch - 90.0])
        ank_y = cuff + 0.35 * (sole - cuff)
        ank = np.array([axis_x(ank_y), ank_y])
        knee = (hip + ank) / 2
        # pad the top: the thigh continues upwards under the jacket
        img = np.vstack([np.repeat(img[:1] * 0, PAD, 0), img]).copy()
        front = np.vstack([np.zeros((PAD, W), bool), front]); shoe = np.vstack([np.zeros((PAD, W), bool), shoe])
        top = np.where(front.any(1))[0].min() + 14                              # a solid row of the thigh
        for y in range(0, top):
            dx = int(round(ka * (y - top)))
            img[y] = np.roll(img[top], dx, axis=0); front[y] = np.roll(front[top], dx)
        img[:top, :, 3] = np.where(front[:top], 255, 0)
        H += PAD
        yy, xx = np.mgrid[0:H, 0:W]
        off = np.array([0.0, PAD])
        self.hip, self.knee, self.ank = hip + off, knee + off, ank + off
        self.sole, self.heel_x, self.toe_x = sole + PAD, heel, toe
        # distance along the leg from the hip, and the knee disk
        u = (self.ank - self.hip) / np.linalg.norm(self.ank - self.hip)
        s = (xx - self.hip[0]) * u[0] + (yy - self.hip[1]) * u[1]
        sk = float((self.knee - self.hip) @ u)
        width = np.array([front[int(y)].sum() for y in range(int(self.knee[1]) - 3, int(self.knee[1]) + 4)]).mean()
        r = 0.5 * width * 1.02
        disk = (xx - self.knee[0]) ** 2 + (yy - self.knee[1]) ** 2 <= r * r
        feather = lambda m: cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.9)
        # the lower leg's two side edges (straight lines fitted below the knee): the cuff is clipped to them
        ry = np.arange(int(self.knee[1]) + 20, int(cuff + PAD) - 8)
        lx_ = np.array([np.where(front[y])[0].min() for y in ry]); rx_ = np.array([np.where(front[y])[0].max() for y in ry])
        pl, pr = np.polyfit(ry, lx_, 1), np.polyfit(ry, rx_, 1)
        inside = (xx >= np.polyval(pl, yy) - 1) & (xx <= np.polyval(pr, yy) + 1)
        thigh = front & ((s <= sk) | disk)
        shin = front & ((s >= sk) | disk) & ~shoe & (inside | (yy < self.knee[1] + 20))
        n, lab, st, _ = cv2.connectedComponentsWithStats(shin.astype(np.uint8), connectivity=4)
        shin = lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))              # not the sole's glints
        low_ = yy > self.knee[1] + 40                                           # the cuff's ragged back edge goes
        shin &= ~low_ | cv2.dilate(cv2.morphologyEx(shin.astype(np.uint8), cv2.MORPH_OPEN, K(5)), K(1)).astype(bool)
        sa = float((self.ank - self.hip) @ u)
        # the shoe (without the pale floor line under the sole), and under the trouser cuff its hidden top: a clean
        # sock-black band between the leg's edges, so a pitched foot never shows a hole or a ragged scrap
        c2 = img[..., :3].astype(np.int32); v2 = c2.max(2)
        shoe &= ~((yy > self.sole - 7) & (v2 > 120))
        shoe &= cv2.dilate(cv2.morphologyEx(shoe.astype(np.uint8), cv2.MORPH_OPEN, K(6)), K(2)).astype(bool)
        sock = inside & (s >= sa - 16) & ~shoe & (yy < self.sole - 8)
        sock &= (xx >= np.polyval(pl, yy) + 1) & (xx <= np.polyval(pr, yy) - 1)
        img[..., :3][sock] = (24, 21, 23); img[..., 3][sock] = 255
        foot = shoe | sock
        n, lab, st, _ = cv2.connectedComponentsWithStats(foot.astype(np.uint8), connectivity=8)
        foot = lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))              # no loose scraps
        # the sheet's thin white rim round the trousers -> the dark outline (it would show where one leg crosses the
        # other); within 3 px of the edge, light pixels only
        edge = front & ~cv2.erode(front.astype(np.uint8), K(3)).astype(bool)
        c3 = img[..., :3].astype(np.int32)
        rim = edge & (c3.max(2) > 135) & ~shoe
        img[..., :3][rim] = (30, 27, 29)
        self.L1 = float(np.linalg.norm(self.knee - self.hip)); self.L2 = float(np.linalg.norm(self.ank - self.knee))
        self.W = W
        self.parts = {}
        for name, m in (("thigh", thigh), ("shin", shin), ("foot", foot)):
            rgba = img.copy(); rgba[..., 3] = (img[..., 3] * feather(m)).astype(np.uint8)
            near = graded_premul(rgba)
            far = near.copy(); far[..., :3] *= FAR_SHADE
            self.parts[name] = (near, far, near[:, ::-1].copy(), far[:, ::-1].copy())

class Legs:
    """the leg rig under one walker body: hips at (hip_x, ...), near foot on `floor` (walker rig px)."""
    def __init__(self, sprites, hip_x, floor, facing):
        self.sp, self.hip_x, self.floor, self.s = sprites, hip_x, floor, facing
        sp = sprites; sc = LEG_SCALE
        self.L1, self.L2 = sp.L1 * sc, sp.L2 * sc
        self.ank_h = (sp.sole - sp.ank[1]) * sc                               # ankle height over the sole
        self.heel_b = (sp.ank[0] - sp.heel_x) * sc                            # heel behind the ankle
        self.ball_f = (0.72 * sp.toe_x + 0.28 * sp.heel_x - sp.ank[0]) * sc   # ball of the foot ahead of it
        self.Lmax = (self.L1 + self.L2) * 0.995
        self.hip_rest = floor - self.ank_h - (self.L1 + self.L2) * 0.985
        # per leg: lateral hip offset (rig px, + = facing direction) and floor offset
        self.leg = {"far": (+LAT, -FAR_DY), "near": (-LAT, 0.0)}

    # ---- local frame: facing right, mirrored about hip_x for a leftward walker
    def loc(self, p): return np.array([self.hip_x + self.s * (p[0] - self.hip_x), p[1]])

    def hip_of(self, leg, hip_y):
        lx, dy = self.leg[leg]
        return np.array([self.hip_x + lx, hip_y + dy])                        # local frame

    def ankle_from(self, F, psi):
        """F: local floor point under the ankle of the flat foot; psi deg (+ toe up about the heel, - heel up about
        the ball) -> ankle (local)"""
        A = F + np.array([0.0, -self.ank_h])
        if psi >= 0: piv = F + np.array([-self.heel_b, 0.0])
        else: piv = F + np.array([self.ball_f, 0.0])
        return piv + rot(-np.radians(psi)) @ (A - piv)

    def solve(self, target, hip_y=None):
        """target: {leg: (ankle local, psi)} -> {leg: (hip, knee, ankle, psi)} local, and the hip drop (rig px).
        The hips sit at their rest height unless a leg can't reach: then they drop just enough."""
        if hip_y is None:
            hip_y = self.hip_rest
            for leg, (A, _) in target.items():
                lx, dy = self.leg[leg]
                dx = A[0] - (self.hip_x + lx)
                hip_y = max(hip_y, A[1] - np.sqrt(max(self.Lmax ** 2 - dx * dx, 1.0)) - dy)
        out = {}
        for leg, (A, psi) in target.items():
            H = self.hip_of(leg, hip_y)
            d = A - H; L = float(np.linalg.norm(d))
            Lc = np.clip(L, abs(self.L1 - self.L2) + 1, self.L1 + self.L2 - 0.01)
            cosa = (self.L1 ** 2 + Lc ** 2 - self.L2 ** 2) / (2 * self.L1 * Lc)
            al = np.arccos(np.clip(cosa, -1, 1))
            Kp = H + self.L1 * (rot(-al) @ (d / max(L, 1e-6)))                  # the knee bends forward (+x local)
            out[leg] = (H, Kp, A, psi)
        return out, hip_y - self.hip_rest

    def layers(self, joints, slope=0.0):
        """joints (local) -> [(img, 3x3 source -> walker rig)], far leg first.  slope: the floor's slant on screen
        (local frame) when he walks into depth: the legs are solved on a flat floor and sheared onto it"""
        sp = self.sp; sc = LEG_SCALE
        out = []
        Sh = np.array([[1, 0, 0], [slope, 1, -slope * self.hip_x], [0, 0, 1]], np.float64)
        Fr = np.array([[-1, 0, 2 * self.hip_x], [0, 1, 0], [0, 0, 1]], np.float64)
        Fs = np.array([[-1, 0, sp.W - 1], [0, 1, 0], [0, 0, 1]], np.float64)
        ang = lambda v: np.arctan2(v[1], v[0])
        src_dir = ang(sp.knee - sp.hip)
        for leg in ("far", "near"):
            H, Kp, A, psi = joints[leg]
            M = {"thigh": T3(*H) @ R3(ang(Kp - H) - src_dir) @ S3(sc) @ T3(*-sp.hip),
                 "shin": T3(*Kp) @ R3(ang(A - Kp) - src_dir) @ S3(sc) @ T3(*-sp.knee),
                 "foot": T3(*A) @ R3(-np.radians(psi)) @ S3(sc) @ T3(*-sp.ank)}
            k = (1 if leg == "far" else 0) + (2 if self.s < 0 else 0)
            for part in ("foot", "shin", "thigh"):
                Mp = Sh @ M[part] if self.s > 0 else Fr @ Sh @ M[part] @ Fs
                out.append((sp.parts[part][k], Mp))
        return out

    # ---- poses
    def standing(self):
        tgt = {leg: (self.ankle_from(np.array([self.hip_x + lx, self.floor + dy]), 0.0), 0.0)
               for leg, (lx, dy) in self.leg.items()}
        return self.solve(tgt, hip_y=self.hip_rest)

    def walking(self, p, walk):
        """p: progress along the walk block (0..1, eased like place_at); walk: WalkPath -> joints (local), hip drop"""
        D, S = walk.D, walk.S
        u = p * D
        e = float(smooth(min(u, D - u) / (0.20 * S)))                      # start / stop from the passing position
        sl = walk.slope * self.s * e                                          # floor slant, local frame
        flat = lambda F: F - np.array([0.0, sl * (F[0] - self.hip_x)])
        tgt = {}
        for leg, o in (("near", 0.0), ("far", 0.5)):
            lx, dy = self.leg[leg]
            c = u / S + MID + o                                               # at u = 0 the near leg is at mid stance
            n = np.floor(c); ph = c - n
            # step n's planted spot: the floor under this leg's hip when the hips pass over it, locked in world space
            spot = lambda m: flat(self.loc(walk.to_rig(p, (m - o) * S / D, self.hip_x + self.s * lx, self.floor + dy)))
            if ph < TOE_OFF:
                if ph < 0.10: psi = PSI_STRIKE * (1 - smooth(ph / 0.10))
                elif ph < 0.40: psi = 0.0
                else: psi = -PSI_OFF * smooth((ph - 0.40) / (TOE_OFF - 0.40)) ** 1.3
                psi *= e
                tgt[leg] = (self.ankle_from(spot(n), psi), psi)
            else:
                v = (ph - TOE_OFF) / (1 - TOE_OFF)
                A0 = self.ankle_from(spot(n), -PSI_OFF * e); A1 = self.ankle_from(spot(n + 1), PSI_STRIKE * e)
                w = 0.5 * v + 0.5 * smooth(v)
                A = A0 + (A1 - A0) * w - np.array([0.0, LIFT * np.sin(np.pi * v) ** 1.2 * e])
                psi = (-PSI_OFF + (PSI_STRIKE + PSI_OFF) * smooth(v)) * e
                tgt[leg] = (A, psi)
        joints, drop = self.solve(tgt)
        return joints, drop, sl

class WalkPath:
    """one walk block in world space: place a -> b (x, floor, scale), progress p eased like perf.place_at;
    the stride is fitted so the walk is a whole number of steps (starts and ends in the passing position)."""
    def __init__(self, a, b, cx, frig):
        self.a, self.b, self.cx, self.frig = np.array(a, float), np.array(b, float), cx, frig
        ps = np.linspace(0, 1, 61)
        pts = [self.place(p) for p in ps]
        D = 0.0
        for (x0, f0, k0), (x1, f1, k1) in zip(pts[:-1], pts[1:]):
            D += np.hypot(x1 - x0, 0.6 * (f1 - f0)) / (0.5 * (k0 + k1))
        self.D = max(D, 1.0)
        dx, df = self.b[0] - self.a[0], self.b[1] - self.a[1]
        self.slope = float(np.clip(df / dx, -0.6, 0.6)) if abs(dx) > 1 else 0.0   # the floor line's slant on screen
        m = max(1, int(round(self.D / STEP)))
        self.S = 2 * self.D / m

    def place(self, p): return self.a + (self.b - self.a) * p

    def to_rig(self, p_now, p_at, x_rig, y_rig):
        """walker rig point (x_rig, y_rig) as it was at progress p_at, seen in the rig frame at progress p_now"""
        x0, f0, k0 = self.place(p_at); x1, f1, k1 = self.place(p_now)
        wx = x0 + k0 * (x_rig - self.cx); wy = f0 + k0 * (y_rig - self.frig)
        return np.array([(wx - x1) / k1 + self.cx, (wy - f1) / k1 + self.frig])

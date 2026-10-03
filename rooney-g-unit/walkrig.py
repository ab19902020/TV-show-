"""A real walk for the cut-out characters: legs rigged under the 3/4 turnaround body, feet planted on the floor.

The sheets' WALK drawings are three or four key poses, which can only be swapped (the body slides or jumps). So, like the Jim
Ratcliffe scene, each walker is rigged:
  * upper body: the 3/4 turnaround drawing above the crotch (jacket hem and hands-in-pockets kept);
  * one leg: cut from the same drawing (the leg whose shoe points the way he walks), split into thigh / shin / foot with a
    rounded overlap at the knee; the thigh is carried up under the jacket so it never shows a cut when it swings;
  * the far leg is the same leg, a little darker, behind, at the other leg's hip;
  * the feet are locked to their spots on the ground (world space) for the whole stance, roll heel -> flat -> toe, swing
    forward with a lift and land heel first; the knees are solved from hip and ankle (2-bone IK) and the hips drop just
    enough for the standing leg to reach, which gives the walk its natural bob;
  * a small group walks at one speed, so the children (shorter legs, shorter steps) take quicker steps.
Everything is computed in part px of the 4x drawing, facing screen-LEFT (drawings that face right are mirrored)."""
import math, numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
import engine as E

STANCE = 0.60           # fraction of the cycle a foot is on the ground
LIFT = 0.10             # swing-foot lift, x leg length
PSI_STRIKE = 9.0        # deg toe up at heel strike (a chunky cartoon trainer reads better with a small roll)
PSI_OFF = 15.0          # deg heel up at toe off
FAR_SHADE = 0.80        # the far leg's trousers
FAR_SHADE_SHOE = 0.92   # the far leg's white trainer (0.80 turned it grey: it read as a different shoe)


def smooth(u):
    u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)


def rot(a):
    c, s = math.cos(a), math.sin(a); return np.array([[c, -s], [s, c]])


def T3(x, y): return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], np.float64)


def R3(a):
    M = np.eye(3); M[:2, :2] = rot(a); return M


def runs_of(row):
    xs = np.nonzero(row)[0]
    if not len(xs): return []
    br = np.nonzero(np.diff(xs) > 1)[0]
    return [r for r in zip([xs[0]] + list(xs[br + 1]), list(xs[br]) + [xs[-1]]) if r[1] - r[0] >= 6]


class Sprite:
    """a Drawing-like image for Stage.draw_actor: premultiplied float levels, no face"""
    has_face = False

    def __init__(self, name, rgba_u8, k=4.0):
        self.name, self.k = name, k
        self.u8 = {1.0: rgba_u8}
        for L in E.LEVELS[1:]:
            self.u8[L] = cv2.resize(rgba_u8, None, fx=L, fy=L, interpolation=cv2.INTER_AREA)
        self._b = {}
        self.anchors = {}

    def base(self, L, clip=None):
        if L not in self._b:
            a = self.u8[L].astype(np.float32) / 255.0
            a[..., :3] *= a[..., 3:4]
            self._b[L] = a
        return self._b[L]

    def patch(self, *a, **k):
        return None

    def P(self, x, y):
        """sheet coords -> part px (for sprites made from a cut part: ox, oy set by the caller)"""
        return ((x - getattr(self, "ox", 0.0)) * self.k, (y - getattr(self, "oy", 0.0)) * self.k)


class Placed:
    """an actor with a ready-made matrix (part px -> world px)"""
    def __init__(self, sprite, M, z):
        self.d, self.M, self.z = sprite, M, z
        self.clip, self.shade, self.rim, self.light, self.flip, self.name = None, 0.0, None, 1.0, False, sprite.name

    def matrix(self, body=None):
        return self.M if body is None else self.M @ body


class WalkRig:
    def __init__(self, drawing, mirror, cut_dy=2, which=None):
        """drawing: the 4x turnaround part; mirror: True when the drawing faces right (it is flipped to face left)"""
        img = np.asarray(Image.open(f"build/parts/{drawing}.png")).copy()
        if mirror: img = img[:, ::-1].copy()
        self.extra_upper=None
        if drawing in getattr(E,'ARM_GUARDS',{}):
            guard=np.zeros(img.shape[:2],np.uint8)
            for poly in E.ARM_GUARDS[drawing]:
                pts=np.float32([E.pxy(drawing,*p) for p in poly])
                if mirror:pts[:,0]=img.shape[1]-1-pts[:,0]
                cv2.fillPoly(guard,[np.int32(pts)],255)
            keep=cv2.GaussianBlur(guard.astype(np.float32)/255,(0,0),.55)
            arm=img.copy();arm[...,3]=np.uint8(arm[...,3]*keep)
            self.extra_upper=Sprite(f'{drawing}:free-hand',arm)
            img[...,3]=np.uint8(img[...,3]*(1-keep))
        self.name = drawing
        a = img[..., 3] > 128
        H, W = a.shape
        ys = np.nonzero(a.any(1))[0]
        top, sole = int(ys.min()), int(ys.max())
        # crotch: going up from the feet, the first row where the two legs merge into one run
        crotch = None
        y = sole - int(0.15 * (sole - top))
        legs_seen = False
        while y > top + 0.4 * (sole - top):
            r = runs_of(a[y])
            if len(r) >= 2: legs_seen = True
            elif legs_seen and len(r) == 1:
                crotch = y; break
            y -= 1
        assert crotch is not None, drawing
        L = sole - crotch                      # crotch to sole
        # the split line between the legs: gap midpoints below the crotch, fitted and extrapolated upwards
        gy, gx = [], []
        for y in range(crotch + 3, crotch + int(0.75 * L)):
            r = runs_of(a[y])
            if len(r) >= 2:
                gy.append(y); gx.append((r[0][1] + r[1][0]) / 2)
        kx, bx = np.polyfit(gy, gx, 1)
        split = lambda y: kx * y + bx
        yy, xx = np.mgrid[0:H, 0:W]
        left = a & (xx < split(yy)); right = a & (xx >= split(yy))
        # which leg: the one whose shoe reaches further forward (left), i.e. the profile shoe
        bot = yy > sole - 0.12 * L
        lmin = xx[left & bot].min() if (left & bot).any() else W; rmin = xx[right & bot].min() if (right & bot).any() else W
        side = which or ("L" if lmin <= rmin else "R")
        leg = left if side == "L" else right
        other = right if side == "L" else left
        # the leg's centre axis between crotch and cuff
        cy = np.arange(crotch + 6, sole - int(0.25 * L))
        cx = np.array([(np.nonzero(leg[y])[0].min() + np.nonzero(leg[y])[0].max()) / 2 for y in cy])
        ka, ba = np.polyfit(cy, cx, 1)
        axis = lambda y: ka * y + ba
        ocx = np.array([(np.nonzero(other[y])[0].min() + np.nonzero(other[y])[0].max()) / 2 for y in cy if other[y].any()])
        self.leg_gap = float(np.mean(ocx) - np.mean(cx)) if len(ocx) else 0.25 * L
        # the far leg is a copy of this one moved across to the other hip: no further out than the drawn far leg's outer
        # edge at the top, or the copy pokes out of the hip
        r0 = int(crotch + 0.05 * L)
        if leg[r0].any() and other[r0].any():
            nl, nr = np.nonzero(leg[r0])[0][[0, -1]]; ol, orr = np.nonzero(other[r0])[0][[0, -1]]
            self.leg_gap = min(self.leg_gap, float(orr - nr)) if self.leg_gap > 0 else max(self.leg_gap, float(ol - nl))
        # The whole trainer is one rigid piece. (Cutting the foot at a fixed height split these tall cartoon trainers in
        # two: the upper half rode on the shin and only the sole on the foot, so the shoe broke apart and the toe went
        # through the floor whenever the foot rolled.) The trainer's white panels are merged, the inked outline added.
        rgb = img[..., :3].astype(np.int16); mn, mxc = rgb.min(2), rgb.max(2)
        ink = max(3, int(round(0.016 * L)))
        bright = (mn > 150) & ((mxc - mn) < 60) & (img[..., 3] > 200) & (yy > sole - 0.42 * L)
        bright = cv2.morphologyEx(bright.astype(np.uint8), cv2.MORPH_CLOSE,
                                  cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ink + 1, 2 * ink + 1))) > 0
        count, labels, stats, _ = cv2.connectedComponentsWithStats(bright.astype(np.uint8))
        zone = leg & (yy > sole - 0.15 * L)
        best = max(range(1, count), key=lambda i: int((zone & (labels == i)).sum()))
        shoe_fill = ndi.binary_fill_holes(labels == best)
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * ink + 1, 2 * ink + 1))
        shoe = (cv2.dilate(shoe_fill.astype(np.uint8), k) > 0) & (img[..., 3] > 40)
        shoe = (cv2.dilate(shoe.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0) & (img[..., 3] > 8)   # + the soft edge
        cols = np.nonzero(shoe_fill.any(0))[0]
        ytop = np.full(W, H, np.int32)
        for x in cols: ytop[x] = int(np.nonzero(shoe_fill[:, x])[0].min())
        shoe_top = int(ytop[cols].min())
        # the trouser hem sits on the shoe: the leg's run just above the trainer
        row = leg[max(0, shoe_top - 2 * ink)]
        hx = np.nonzero(row)[0]
        hx0, hx1 = (int(hx.min()), int(hx.max())) if len(hx) else (int(cols.min()), int(cols.max()))
        hemcols = (xx >= hx0) & (xx <= hx1)
        above_shoe = yy < ytop[None, :]
        # joints: the ankle sits inside the trainer, right under the middle of the hem, so a rolling foot stays tucked
        # into the trouser leg
        hip_y = crotch - 0.12 * L
        acx = int(round((hx0 + hx1) / 2)); acx = min(max(acx, int(cols.min())), int(cols.max()))
        ank_y = ytop[acx] + 0.30 * (sole - ytop[acx])
        self.hip = np.array([axis(hip_y), hip_y]); self.ank = np.array([float(acx), float(ank_y)])
        self.knee = (self.hip + self.ank) / 2 + np.array([0.0, -0.02 * L])
        foot_top = float(shoe_top)
        self.toe_x, self.heel_x = float(xx[shoe].min()), float(xx[shoe].max())     # facing left: toe = min x
        self.sole = float(yy[shoe].max())
        # where the sole meets the floor, front and back: the foot rolls about these, so no part of it goes under
        band = shoe & (yy >= self.sole - 0.035 * L)
        self.toe_c, self.heel_c = float(xx[band].min()), float(xx[band].max())
        # the leg image: the thigh carried up under the jacket (a clean row repeated with the leg's slope)
        rgba = img.copy()
        clean = crotch + 5
        legm = leg.copy()
        for y in range(int(hip_y) - int(0.18 * L), clean):
            dx = int(round(ka * (y - clean)))
            rgba[y] = np.roll(img[clean], dx, axis=0); legm[y] = np.roll(leg[clean], dx)
        legm[:int(hip_y) - int(0.18 * L)] = False
        # pieces: thigh / shin with a disk at the knee and at the hip (so neither sweeps a corner out of the silhouette
        # when it turns), the shin down to the hem, the foot = the trainer + a strip of trouser hidden under the hem
        kxs = np.nonzero(legm[int(self.knee[1])])[0]
        self.knee[0] = 0.5 * (kxs.min() + kxs.max())                 # the knee in the middle of the trouser leg
        u = (self.ank - self.hip) / np.linalg.norm(self.ank - self.hip)
        s = (xx - self.hip[0]) * u[0] + (yy - self.hip[1]) * u[1]
        sk = float((self.knee - self.hip) @ u)
        kr = 0.5 * (kxs.max() - kxs.min()) * 0.97
        disk = (xx - self.knee[0]) ** 2 + (yy - self.knee[1]) ** 2 <= kr * kr
        # round the knee: near it neither piece is wider than the knee disk (a trouser crease sticking out there
        # turned into a flap behind the bent knee)
        t = (xx - self.knee[0]) * -u[1] + (yy - self.knee[1]) * u[0]
        legm = legm & ~((np.abs(s - sk) < 1.1 * kr) & (np.abs(t) > kr))
        hr = 0.5 * legm[int(crotch + 0.05 * L)].sum() * 0.96
        hipdisk = (yy >= crotch) | ((xx - self.hip[0]) ** 2 + (yy - self.hip[1]) ** 2 <= hr * hr)
        thigh = legm & ((s <= sk) | disk) & hipdisk
        trouser_end = shoe & ~(hemcols & above_shoe)
        trouser_end = cv2.dilate(trouser_end.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0     # no ghost of the shoe's edge
        shin = legm & ((s >= sk) | disk) & ~trouser_end & (yy < self.sole)
        foot = shoe | (legm & hemcols & above_shoe & (yy >= ytop[None, :] - 0.09 * L) & (s >= sk))
        def largest(m):          # a sliver of the other leg caught by the split line would turn into a flying speck
            n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8))
            return lab == (1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))) if n > 2 else m
        thigh, shin, foot = largest(thigh), largest(shin), largest(foot)
        feather = lambda m: cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0)
        whiteish = ((mn > 150) & ((mxc - mn) < 60))[..., None]
        shade = np.where(whiteish, FAR_SHADE_SHOE, FAR_SHADE)
        # above the crotch a thigh is only ever seen through the hip's soft lower edge: keep it inside the drawn hip
        # outline there (the far copy at the far hip's), or its top shows as a smudge outside the hip
        fdx = int(round(self.far_dx if hasattr(self, 'far_dx') else self.leg_gap))
        drawn = np.zeros_like(a); drawn[:, max(0, -fdx):W - max(0, fdx)] = a[:, max(0, fdx):W - max(0, -fdx)]
        hips_in = {"": a | (yy > crotch + 0.03 * L), ":far": drawn | (yy > crotch + 0.03 * L)}
        self.pieces = {}
        for nm, m in (("thigh", thigh), ("shin", shin), ("foot", foot)):
            sp = []
            for which, mm in (("", m & hips_in[""] if nm == "thigh" else m), (":far", m & hips_in[":far"] if nm == "thigh" else m)):
                weight = feather(mm)
                if nm == 'thigh': weight *= np.clip((yy - (hip_y - .10 * L)) / (.06 * L), 0, 1)   # opaque above the hip joint
                q = rgba.copy(); q[..., 3] = (rgba[..., 3] * weight).astype(np.uint8)
                if which: q[..., :3] = (q[..., :3] * shade).astype(np.uint8)
                sp.append(Sprite(f"{drawing}:{nm}{which}", q))
            self.pieces[nm] = tuple(sp)
        # outline of the foot piece (for keeping the rolled foot above the floor)
        cs, _ = cv2.findContours(shoe.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        self.foot_pts = np.vstack([c[:, 0, :] for c in cs]).astype(np.float64)
        # upper body: everything above the crotch (+ a soft edge), hands kept
        up = img.copy()
        # A soft hip overlap covers the articulated thighs without rectangular
        # patches projecting beyond the original trouser silhouette.
        # (a long fade left see-through ghosts of the drawn legs between the swinging ones)
        keep = np.clip((crotch+.02*L-yy)/(.035*L),0,1)
        up[..., 3] = (up[..., 3] * keep).astype(np.uint8)
        self.upper = Sprite(f"{drawing}:upper", up)
        self.L1 = float(np.linalg.norm(self.knee - self.hip)); self.L2 = float(np.linalg.norm(self.ank - self.knee))
        self.ank_h = self.sole - self.ank[1]
        self.heel_b = self.heel_c - self.ank[0]                        # heel contact behind the ankle (+x, facing left)
        self.ball_f = self.ank[0] - self.toe_c                         # toe contact in front of it
        self.leglen = self.L1 + self.L2
        self.hip_rest = self.sole - self.ank_h - self.leglen * 0.985
        self.src_dir = math.atan2(*(self.knee - self.hip)[::-1])
        # in the drawing, where the other (far) leg's hip sits relative to the drawn one
        self.far_dx = self.leg_gap

    # ------------------------------------------------------------------ gait (rig frame = part px, facing -x)
    def ankle_from(self, F, psi):
        """F: floor point under the ankle; psi deg (+ toe up about the heel, - heel up about the ball)"""
        A = F + np.array([0.0, -self.ank_h])
        piv = F + (np.array([self.heel_b, 0.0]) if psi >= 0 else np.array([-self.ball_f, 0.0]))
        # facing left: toe-up = clockwise on screen
        return piv + rot(math.radians(psi)) @ (A - piv)

    def solve(self, hips, targets):
        out = {}
        for leg, (A, psi) in targets.items():
            Hh = hips[leg]
            d = A - Hh; L = float(np.linalg.norm(d))
            Lc = min(max(L, abs(self.L1 - self.L2) + 1), self.L1 + self.L2 - 0.01)
            ca = (self.L1 ** 2 + Lc ** 2 - self.L2 ** 2) / (2 * self.L1 * Lc)
            al = math.acos(min(1.0, max(-1.0, ca)))
            Kp = Hh + self.L1 * (rot(al) @ (d / max(L, 1e-6)))             # knee bends forward (-x)
            out[leg] = (Hh, Kp, A, psi)
        return out

    def pose(self, u_hip, step, phase0, moving=1.0, far_lift=0.0):
        """u_hip: distance walked (part px, along -x); step: step length (part px). -> joints in the rig frame where the hips
        are at x = hip.x - u_hip... returns (joints, hip_y)"""
        S = step
        hipx = self.hip[0]
        tg = {}
        for leg, off in (("near", 0.0), ("far", 0.5)):
            hx = hipx + (self.far_dx if leg == "far" else 0.0)
            c = u_hip / (2 * S) + phase0 + off
            n = math.floor(c); ph = c - n
            # step n: the foot is planted where the hip is at mid-stance (c = n + STANCE / 2)
            spot = lambda m: hx - ((m + STANCE / 2 - phase0 - off) * 2 * S - u_hip)
            if ph < STANCE or moving < 0.5:
                if ph < 0.12: psi = PSI_STRIKE * (1 - smooth(ph / 0.12))
                elif ph < 0.40: psi = 0.0
                else: psi = -PSI_OFF * smooth((ph - 0.40) / (STANCE - 0.40)) ** 1.3
                F = np.array([spot(n), self.sole + (far_lift if leg == "far" else 0.0)])
                tg[leg] = (self.ankle_from(F, psi * moving), psi * moving)
            else:
                v = (ph - STANCE) / (1 - STANCE)
                F0 = np.array([spot(n), self.sole + (far_lift if leg == "far" else 0.0)]); F1 = np.array([spot(n + 1), F0[1]])
                A0 = self.ankle_from(F0, -PSI_OFF); A1 = self.ankle_from(F1, PSI_STRIKE)
                w = 0.5 * v + 0.5 * smooth(v)
                A = A0 + (A1 - A0) * w - np.array([0.0, LIFT * self.leglen * math.sin(math.pi * v) ** 1.2])
                psi = -PSI_OFF + (PSI_STRIKE + PSI_OFF) * smooth(v)
                tg[leg] = (A, psi)
        # no part of a trainer ever goes through the floor: lift the ankle by whatever the rolled outline dips under
        for leg, (A, psi) in list(tg.items()):
            floor = self.sole + (far_lift if leg == "far" else 0.0)
            P = (self.foot_pts - self.ank) @ rot(math.radians(psi)).T + A
            dip = float(P[:, 1].max()) - floor
            if dip > 0: tg[leg] = (A - np.array([0.0, dip]), psi)
        # hips: rest height unless a leg can't reach -> drop just enough
        Lmax = (self.L1 + self.L2) * 0.995
        hip_y = self.hip_rest
        hips_x = {"near": hipx, "far": hipx + self.far_dx}
        for leg, (A, _) in tg.items():
            dx = A[0] - hips_x[leg]
            hip_y = max(hip_y, A[1] - math.sqrt(max(Lmax ** 2 - dx * dx, 1.0)) - (far_lift if leg == "far" else 0.0))
        hips = {"near": np.array([hipx, hip_y]), "far": np.array([hipx + self.far_dx, hip_y + far_lift])}
        return self.solve(hips, tg), hip_y - self.hip_rest

    def layers(self, joints, drop, M_world, z, lean=0.0):
        """-> list of Placed actors (far leg, near leg, upper body). M_world: rig part px -> world px (3x3)"""
        out = []
        ang = lambda v: math.atan2(v[1], v[0])
        for leg in ("far", "near"):
            Hh, Kp, A, psi = joints[leg]
            idx = 1 if leg == "far" else 0
            Ms = {"thigh": T3(*Hh) @ R3(ang(Kp - Hh) - self.src_dir) @ T3(*-self.hip),
                  "shin": T3(*Kp) @ R3(ang(A - Kp) - self.src_dir) @ T3(*-self.knee),
                  "foot": T3(*A) @ R3(math.radians(psi)) @ T3(*-self.ank)}
            dz = -0.02 if leg == "far" else 0.0
            for part in ("foot", "shin", "thigh"):
                out.append(Placed(self.pieces[part][idx], M_world @ Ms[part], z + dz))
        Rl = np.vstack([cv2.getRotationMatrix2D((float(self.hip[0]), float(self.hip[1])), lean, 1.0), [0, 0, 1]])
        out.append(Placed(self.upper, M_world @ T3(0, drop) @ Rl, z + 0.01))
        if self.extra_upper is not None:
            out.append(Placed(self.extra_upper,M_world @ T3(0,drop) @ Rl,z+.012))
        return out


_RIGS = {}


def rig(drawing, mirror):
    k = (drawing, mirror)
    if k not in _RIGS: _RIGS[k] = WalkRig(drawing, mirror)
    return _RIGS[k]


def walker(drawing, mirror, x0, floor_y, scale, t, t0, speed, step_frac=0.62, phase0=0.0, stop_t=None, z=None, lean=2.0):
    """a walking figure moving LEFT from plate x0 at `speed` plate px / s, feet on plate y floor_y.
    scale: plate px per sheet px. Returns a list of Placed actors for Stage.render (fg list)."""
    R = rig(drawing, mirror)
    w = scale * 4.0 / 4.0                                          # world px per part px (4x parts)
    tt = max(0.0, t - t0) if stop_t is None else min(max(0.0, t - t0), stop_t - t0)
    dist_plate = speed * tt
    u = dist_plate * 4 / w                                         # part px walked
    step = step_frac * R.leglen
    moving = 1.0 if (stop_t is None or t < stop_t) else 0.0
    joints, drop = R.pose(u, step, phase0, moving)
    # rig frame -> world: the rig's hip x moves left by u; its sole sits on the floor
    Mw = T3(x0 * 4, floor_y * 4) @ np.array([[w, 0, 0], [0, w, 0], [0, 0, 1]]) @ T3(-R.hip[0] - u, -R.sole)
    # the rig was solved with feet at spots relative to the walked hip: shift the whole rig by -u in x so feet stay put
    return R.layers(joints, drop, Mw @ T3(0, 0), (floor_y if z is None else z), lean=lean)

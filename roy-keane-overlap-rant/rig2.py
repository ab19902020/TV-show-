"""Full-body cut-out rig: torso lean, head (expressions + lip sync), and two 3-joint arms."""
import numpy as np, cv2
from rig import Rig, HX0, HY0, grade, to3
from arms import build as build_arms

def R(center, ang):
    return to3(cv2.getRotationMatrix2D((float(center[0]), float(center[1])), float(ang), 1.0))

PAD = 420            # horizontal canvas padding so arms can swing outward

class Rig2(Rig):
    def __init__(self):
        super().__init__()
        from rig import P
        arms, _, _, arm_all_full = build_arms(P["body"][0])          # full height: forearms + hands
        arm_all = arm_all_full[:self.l3.shape[0]]
        self.l3 = self.l3 * (~arm_all)
        # clean torso side edges: remove thin slivers left along the arm cut, then smooth the side contour
        K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
        m = (self.l3 > 0.5).astype(np.uint8)
        near = cv2.dilate(arm_all.astype(np.uint8), K(40)).astype(bool)
        mo = cv2.morphologyEx(m, cv2.MORPH_OPEN, K(16))
        mo = cv2.morphologyEx(mo, cv2.MORPH_CLOSE, K(10))
        m2 = np.where(near, mo, m).astype(np.uint8)
        soft = cv2.GaussianBlur(m2.astype(np.float32), (0, 0), 1.2)
        self.l3 = np.where(near, np.minimum(np.maximum(self.l3, soft * (self.l3 > 0.02)), soft), self.l3)
        self.l3 = np.where(near, soft * (m2 > 0) + soft * 0, self.l3) * np.where(near, 1.0, 1.0)
        # outline stroke along the new side edges (in graded colour)
        inner = cv2.erode(m2, K(4)).astype(bool)
        edge = near & (m2 > 0) & ~inner
        bc = self.body_col.copy()
        bc[edge] = (bc[edge] * 0.2 + np.array([22, 18, 20]) * 0.8).astype(np.uint8)
        self.body_col = bc
        # where the torso covers: the upper-arm seam band may only show there
        self.l3_cover = cv2.dilate((self.l3 > 0.05).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))).astype(np.float32)
        # original body silhouette (arms included) - shoulder caps may never poke outside it
        from rig import P as _P
        sil = (_P["body"][0][:self.l3.shape[0], :, 3] > 128).astype(np.uint8)
        self.sil = cv2.erode(sil, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))).astype(np.float32)
        self.sil_soft = _P["body"][0][:self.l3.shape[0], :, 3].astype(np.float32) / 255
        self.arms = {}
        for k, d in arms.items():
            g = {}
            for pn in ("upper", "upper_top", "upper_band", "fore", "hand", "elbow_cap", "shoulder_cap"):
                p = d[pn]
                c = grade(np.clip(p[..., :3], 0, 255).astype(np.uint8)).astype(np.float32)
                g[pn] = np.dstack([c * p[..., 3:4], p[..., 3:4]])        # premultiplied
            g.update(shoulder=d["shoulder"], elbow=d["elbow"], wrist=d["wrist"], side=d["side"])
            self.arms[k] = g
        up = self.arms["R"]["upper"]; al = up[..., 3] > 0.9
        self.navy = np.median(up[..., :3][al] / up[..., 3:4][al], axis=0)
        # shoulder cap only where the torso hides it


    def arm_mats(self, k, pose, body_M3):
        """pose = (shoulder_out, elbow_in, wrist) degrees -> 3x3 matrices for upper, fore, hand."""
        a = self.arms[k]; s = a["side"]
        so, ei, wr = pose
        Mu = body_M3 @ R(a["shoulder"], s * so)
        Mf = Mu @ R(a["elbow"], -s * ei)
        Mh = Mf @ R(a["wrist"], -s * wr)
        return Mu, Mf, Mh

    def shoulder_filler(self, k, Mu, ups, L3w, Hc, Wc, R0=150):
        """navy 'webbing' bridging torso shoulder and rotated sleeve (convex hull in a local window)."""
        a = self.arms[k]
        p = (Mu @ np.array([a["shoulder"][0], a["shoulder"][1], 1.0]))[:2]
        x0, y0 = int(max(0, p[0] - R0)), int(max(0, p[1] - R0))
        x1, y1 = int(min(Wc, p[0] + R0)), int(min(Hc, p[1] + R0 * 0.3))
        m = np.zeros((y1 - y0, x1 - x0), np.uint8)
        for q in (ups[1], ups[2], L3w):
            m |= (q[y0:y1, x0:x1, 3] > 0.5)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        m &= (((xx - p[0]) ** 2 + (yy - p[1]) ** 2) < R0 * R0).astype(np.uint8)
        pts = cv2.findNonZero(m)
        out = np.zeros((Hc, Wc, 4), np.float32)
        if pts is None: return out
        hull = cv2.convexHull(pts) + np.array([x0, y0])
        fill = np.zeros((Hc, Wc), np.float32); cv2.fillConvexPoly(fill, hull.astype(np.int32), 1.0, cv2.LINE_AA)
        col = np.zeros((Hc, Wc, 3), np.float32); col[:] = self.navy
        ring = np.zeros((Hc, Wc), np.float32); cv2.polylines(ring, [hull.astype(np.int32)], True, 1.0, 7, cv2.LINE_AA)
        col = col * (1 - ring[..., None]) + np.float32([20, 16, 18]) * ring[..., None]
        return np.dstack([col * fill[..., None], fill])

    def compose(self, head, vis, head_M=None, body_M=None, arms=None):
        """arms = {'R': (so, ei, wr), 'L': (...)}.  body_M: 2x3 torso transform (lean/bounce).
        head_M: 2x3 head motion relative to the torso (it rides on body_M)."""
        Hc, Wc = self.l3.shape[0], self.l3.shape[1] + 2 * PAD
        Tp = np.array([[1, 0, PAD], [0, 1, 0], [0, 0, 1]], np.float64)
        B3 = Tp @ (to3(body_M) if body_M is not None else np.eye(3))
        arms = arms or {"R": (0, 0, 0), "L": (0, 0, 0)}
        def warp(p, M3):
            return cv2.warpAffine(p, M3[:2].astype(np.float32), (Wc, Hc), flags=cv2.INTER_LINEAR)
        bc = self.body_col.astype(np.float32)
        def lay(a, c): return np.dstack([c * a[..., None], a])
        out = np.zeros((Hc, Wc, 4), np.float32)
        def over(o, L): return L + o * (1 - L[..., 3:4])
        mats = {k: self.arm_mats(k, arms[k], B3) for k in self.arms}
        SIL = cv2.warpAffine(self.sil_soft, B3[:2].astype(np.float32), (Wc, Hc))[..., None]
        # back: shoulder fillers, upper arms, behind the torso
        L3w = warp(lay(self.l3, bc), B3)
        ups = {}
        for k in self.arms:
            Mu = mats[k][0]
            ups[k] = (warp(self.arms[k]["upper_band"], Mu) * warp(self.l3_cover, B3)[..., None],
                      warp(self.arms[k]["upper"], Mu), warp(self.arms[k]["upper_top"], Mu) * SIL)
        for k in self.arms:
            if abs(arms[k][0]) > 2:
                out = over(out, self.shoulder_filler(k, mats[k][0], ups[k], L3w, Hc, Wc))
            for p in ups[k]: out = over(out, p)
        out = over(out, warp(lay(self.l1, bc), B3))
        hc = self.head_img(head, vis)
        up, nk = self.split[head]
        Mh = np.array([[1, 0, HX0], [0, 1, HY0], [0, 0, 1]], np.float64)
        if head_M is not None: Mh = to3(head_M) @ Mh
        Mh = B3 @ Mh
        out = over(out, warp(lay(nk, hc), Mh))
        out = over(out, L3w)
        out = over(out, warp(lay(up, hc), Mh))
        # front: hands, elbow caps (faded in with elbow bend), forearms
        for k in self.arms:
            Mu, Mf, Mhd = mats[k]
            out = over(out, warp(self.arms[k]["hand"], Mhd))
            capw = float(np.clip(abs(arms[k][1]) / 25.0, 0, 1))
            if capw > 0: out = over(out, warp(self.arms[k]["elbow_cap"], Mf) * capw)
            out = over(out, warp(self.arms[k]["fore"], Mf))
        return out

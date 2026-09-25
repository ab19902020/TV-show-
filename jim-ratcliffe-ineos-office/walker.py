"""Walking rig and turnaround views.
Walker: a 3/4 turnaround body (cut at the jacket hem, hands kept) over the sheet's WALK leg drawings; the legs
are planted on the body's floor line and the body bobs over them.  'L' walks screen-left (3/4 LEFT body,
mirrored legs), 'R' walks screen-right (3/4 RIGHT body).
View: a whole turnaround drawing, for the in-between frames of a turn (and the back view at the window)."""
import numpy as np, cv2
from rig import graded_premul, classes, K, to3

def floor_of(img):
    return float(np.where((img[..., 3] > 128).any(1))[0].max()) - 4

def centre_of(img, y=1000):
    xs = np.where(img[y, :, 3] > 128)[0]
    return float((xs.min() + xs.max()) / 2)

class Walker:
    def __init__(self, P, view, legs, mirror_legs, cut_y=922, leg_scale=1.52):
        body = P["turn"][view][0]
        H, W = body.shape[:2]
        self.floor = floor_of(body)
        yy, xx = np.mgrid[0:H, 0:W]
        red, skin, white, grey = classes(body)
        hands = cv2.dilate((skin & (yy > cut_y - 120) & (yy < 1060)).astype(np.uint8), K(9)).astype(bool)
        n, lab, st, _ = cv2.connectedComponentsWithStats(hands.astype(np.uint8))
        hk = np.zeros_like(hands)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] > 2500: hk |= lab == i
        keep = np.clip((cut_y + 12 - yy) / 24.0, 0, 1)
        keep = np.maximum(keep, cv2.GaussianBlur(hk.astype(np.float32), (0, 0), 2) * (yy < 1060))
        up = body.copy(); up[..., 3] = (up[..., 3] * keep).astype(np.uint8)
        self.upper = graded_premul(up)
        a = body[..., 3] > 128
        row = np.where(a[cut_y + 60] & ~hands[cut_y + 60])[0]
        self.hip_x = float((row.min() + row.max()) / 2)
        self.cx = self.hip_x
        self.legs = {}
        for ln in legs:
            img = P["leg"][ln][0]
            if mirror_legs: img = img[:, ::-1].copy()
            la = img[..., 3] > 128
            ys = np.where(la.any(1))[0]
            top_row = np.where(la[ys.min() + 8])[0]
            tcx = (top_row.min() + top_row.max()) / 2
            s = leg_scale
            M = np.array([[s, 0, self.hip_x - s * tcx], [0, s, self.floor - s * ys.max()]], np.float64)
            self.legs[ln] = (graded_premul(img), M)

    def layers(self, leg, bob=0.0, lean=0.0):
        img, M = self.legs[leg]
        R = to3(cv2.getRotationMatrix2D((self.hip_x, 900.0), lean, 1.0))
        T = np.array([[1, 0, 0], [0, 1, bob], [0, 0, 1]], np.float64)
        return [(img, to3(M)), (self.upper, T @ R)]

class View:
    def __init__(self, P, view, mirror=False):
        img = P["turn"][view][0]
        if mirror: img = img[:, ::-1].copy()
        self.img = graded_premul(img)
        self.floor = floor_of(img); self.cx = centre_of(img)

    def layers(self, bob=0.0):
        return [(self.img, np.array([[1, 0, 0], [0, 1, bob], [0, 0, 1]], np.float64))]

WALK = ["WALK 1", "WALK 2", "WALK 3", "WALK 4", "STANDING"]

def build(P):
    walkers = {"L": Walker(P, "3/4 LEFT", WALK, True), "R": Walker(P, "3/4 RIGHT", WALK, False)}
    views = {n: View(P, n) for n in ("FRONT", "3/4 LEFT", "3/4 RIGHT", "BACK")}
    views["PROFILE L"] = View(P, "LEFT", mirror=True)
    return walkers, views

if __name__ == "__main__":
    import pickle
    from rig import render_layers
    P = pickle.load(open("parts.pkl", "rb"))
    W, V = build(P)
    S = "/tmp/claude-0/-home-user-TV-show-/17c2eb03-f7c3-5c18-9c9e-6908366e9c0f/scratchpad/"
    tiles = []
    for key in "LR":
        for ln in WALK[:4]:
            Vm = np.array([[0.4, 0, 110], [0, 0.4, 10], [0, 0, 1]], float)
            im = render_layers(W[key].layers(ln, -6), Vm, (380, 640))
            tiles.append((im[..., :3] + np.float32([150, 175, 150]) * (1 - im[..., 3:4])).astype(np.uint8))
    cv2.imwrite(S + "walkers.png", np.hstack(tiles))

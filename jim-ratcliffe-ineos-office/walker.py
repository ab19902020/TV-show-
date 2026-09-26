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

# mouth line on the 3/4 turnaround heads (4x crop px): (x0, y0, x1, y1), read off gridded close-ups
MOUTH_LINE = {"3/4 LEFT": (80, 290, 145, 287), "3/4 RIGHT": (377, 284, 430, 281)}
# viseme -> (openness 0..1, roundness 0..1, teeth)
OPEN = {"REST": (0, 0, 0), "M": (0, 0, 0), "B": (0, 0, 0), "FV": (0.12, 0, 1), "A": (1.0, 0.1, 1), "E": (0.65, 0, 1),
        "I": (0.45, 0, 1), "O": (0.8, 0.8, 0), "U": (0.45, 1.0, 0), "Q": (0.5, 0.8, 0), "W": (0.35, 1.0, 0),
        "L": (0.45, 0.2, 1), "CDGK": (0.4, 0.2, 1), "CHJ": (0.35, 0.6, 1), "R": (0.35, 0.6, 0), "TH": (0.3, 0.1, 1),
        "SZ": (0.2, 0.1, 1), "T": (0.3, 0.1, 1), "N": (0.3, 0.1, 1)}

REST_LIP = ((311.0, 655.0), (475.0, 655.0))          # lip corners on the mouth sheet's REST shape (4x px)
_MOUTHS = None

def talk(rgba, line, vis):
    """the mouth sheet's painted mouth shape for `vis`, squashed to the 3/4 mouth line (corners onto corners)
    and colour-matched onto the face; kept inside the face so the profile outline is never touched."""
    global _MOUTHS
    if _MOUTHS is None:
        import pickle
        _MOUTHS = pickle.load(open("mouths.pkl", "rb"))
    shapes = _MOUTHS["shapes"]
    if vis not in shapes: vis = {"REST": "REST"}.get(vis, "CDGK")
    src = shapes[vis].astype(np.float32)
    (ax, ay), (bx, by) = REST_LIP
    x0, y0, x1, y1 = line
    sx = (x1 - x0) / (bx - ax); sy = 0.45                                 # vertical: REST -> turnaround head scale
    ang = np.arctan2(y1 - y0, x1 - x0)
    M = np.array([[sx * np.cos(ang), -sy * np.sin(ang), 0], [sx * np.sin(ang), sy * np.cos(ang), 0]], np.float64)
    c = M[:, :2] @ np.array([(ax + bx) / 2, ay])
    M[:, 2] = np.array([(x0 + x1) / 2, (y0 + y1) / 2]) - c
    H, W = rgba.shape[:2]
    hs, ws = src.shape[:2]
    m = np.zeros((hs, ws), np.float32)
    cv2.ellipse(m, (int((ax + bx) / 2), int(ay + 22)), (118, 88), 0, 0, 360, 1, -1)
    m = cv2.GaussianBlur(m, (0, 0), 16); m = np.clip(m * 1.4, 0, 1)
    ring = np.zeros((hs, ws), np.uint8)
    cv2.ellipse(ring, (int((ax + bx) / 2), int(ay + 22)), (150, 118), 0, 0, 360, 1, 26)
    patch = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_AREA)
    A = cv2.warpAffine(m, M, (W, H))
    R = cv2.warpAffine(ring.astype(np.float32), M, (W, H)) > 0.5
    face = (rgba[..., 3] > 250)
    face = cv2.erode(face.astype(np.uint8), np.ones((15, 15), np.uint8)).astype(bool)
    R &= face
    col = rgba[..., :3].astype(np.float32)
    if R.sum() > 30:
        ps, hs_ = patch[R].mean(0), col[R].mean(0)
        g = np.clip((col[R].std(0) + 1) / (patch[R].std(0) + 1), 0.8, 1.2)
        patch = np.clip((patch - ps) * g + hs_, 0, 255)
    A = (A * cv2.GaussianBlur(face.astype(np.float32), (0, 0), 3))[..., None]
    out = rgba.copy()
    out[..., :3] = np.clip(col * (1 - A) + patch * A, 0, 255).astype(np.uint8)
    return out

class Walker:
    def __init__(self, P, view, legs, mirror_legs, cut_y=922, leg_scale=1.52):
        body = P["turn"][view][0]
        self.view = view; self._talk = {}
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
        self.up_rgba = up
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

    def upper_for(self, vis):
        if vis is None or self.view not in MOUTH_LINE: return self.upper
        if vis not in self._talk: self._talk[vis] = graded_premul(talk(self.up_rgba, MOUTH_LINE[self.view], vis))
        return self._talk[vis]

    def layers(self, leg, bob=0.0, lean=0.0, vis=None):
        img, M = self.legs[leg]
        R = to3(cv2.getRotationMatrix2D((self.hip_x, 900.0), lean, 1.0))
        T = np.array([[1, 0, 0], [0, 1, bob], [0, 0, 1]], np.float64)
        return [(img, to3(M)), (self.upper_for(vis), T @ R)]

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

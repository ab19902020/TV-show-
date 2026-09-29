"""Lip-sync mouths from the mouth sheet, composited onto the expression heads.

1. every mouth-sheet head is registered to the REST head (SIFT on eyes / nose / hair, mouth masked out) and
   its mouth area is cut out in the REST frame, so all 19 shapes line up exactly;
2. the REST head is registered onto each expression head (SIFT, then a local NCC refinement on the
   nose-to-chin area);
3. per frame, the mouth patch is warped onto the head with a feathered mask and colour-matched on a ring
   of beard around it."""
import numpy as np, cv2, pickle
from layout import MOUTH_ROW1, MOUTH_ROW2, MOUTH_CX, MOUTH_CY, MOUTH_BOX, S
from align_util import sift_similarity, to3

CELL = (92, 128)     # half size of a mouth-sheet head cell (1x)
TALKING = ["NEUTRAL", "SAD", "WORRIED", "SURPRISED", "CONFUSED", "DISGUSTED", "RAISED BROW", "SMILE", "THINKING"]

def cell(sheet, n):
    cx, cy = MOUTH_CX[n], MOUTH_CY[n]
    x0, y0 = int((cx - CELL[0]) * S), int((cy - CELL[1]) * S)
    return sheet[y0:y0 + 2 * CELL[1] * S, x0:x0 + 2 * CELL[0] * S].copy(), (x0, y0)

def build(P):
    sheet = cv2.imread("src/mouths_x4.png")
    ref, (rx0, ry0) = cell(sheet, "REST")
    h, w = ref.shape[:2]
    bx0, by0, bx1, by1 = [(v - o) for v, o in zip([MOUTH_BOX[0] * S, MOUTH_BOX[1] * S, MOUTH_BOX[2] * S, MOUTH_BOX[3] * S], [rx0, ry0, rx0, ry0])]
    face = np.full((h, w), 255, np.uint8); face[by0 - 40:, :] = 0          # eyes, nose, brows, hair only
    face[:int(h * 0.12)] = 0
    shapes = {}
    for n in MOUTH_ROW1 + MOUTH_ROW2:
        img, _ = cell(sheet, n)
        if n == "REST": M = np.eye(3)[:2]
        else:
            M, inl, good = sift_similarity(img, ref, face, face, reproj=4.0)
            print("mouth", n, inl, good, "s %.3f" % np.sqrt(abs(np.linalg.det(M[:, :2]))), "t", M[:, 2].round(1))
        shapes[n] = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    # REST head -> each expression head
    to_head = {}
    rest_g = ref
    for n in TALKING:
        himg = P["head"][n][0]
        a = himg[..., 3:4] / 255.0
        hb = (himg[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
        hm = (himg[..., 3] > 200).astype(np.uint8) * 255
        hm[int(hm.shape[0] * 0.80):] = 0
        rm = np.full((h, w), 255, np.uint8); rm[int(h * 0.86):] = 0
        M, inl, good = sift_similarity(rest_g, hb, rm, hm, reproj=8.0)
        M = refine(rest_g, hb, M, (bx0, by0, bx1, by1))
        print("REST ->", n, inl, good, "s %.3f" % np.sqrt(abs(np.linalg.det(M[:, :2]))))
        to_head[n] = M
    return {"shapes": shapes, "box": (bx0, by0, bx1, by1), "to_head": to_head, "size": (w, h)}

def refine(src, dst, M0, box, dt=24, ds=0.06, dr=4):
    """small scale / rotation / translation search maximising NCC of the nose-to-chin area."""
    bx0, by0, bx1, by1 = box
    g1 = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY).astype(np.float32)
    g2 = cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY).astype(np.float32)
    x0, x1, y0, y1 = bx0 - 30, bx1 + 30, by0 - 90, by1 + 10          # nose + mustache + mouth + chin
    tpl = g1[y0:y1, x0:x1]
    best = (-2, M0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for s in np.linspace(1 - ds, 1 + ds, 7):
        for r in np.linspace(-dr, dr, 5):
            Mc = (to3(M0) @ to3(cv2.getRotationMatrix2D((cx, cy), r, s)))[:2]
            inv = cv2.invertAffineTransform(Mc); inv[:, 2] += dt
            win = cv2.warpAffine(g2, inv, (g1.shape[1] + 2 * dt, g1.shape[0] + 2 * dt), borderValue=255)
            res = cv2.matchTemplate(win[y0:y1 + 2 * dt, x0:x1 + 2 * dt], tpl, cv2.TM_CCOEFF_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(res)
            if mv > best[0]:
                best = (mv, (to3(Mc) @ np.array([[1, 0, ml[0] - dt], [0, 1, ml[1] - dt], [0, 0, 1]]))[:2])
    return best[1]

class Mouths:
    def __init__(self, path="mouths.pkl"):
        d = pickle.load(open(path, "rb"))
        self.shapes, self.box, self.to_head, self.size = d["shapes"], d["box"], d["to_head"], d["size"]
        w, h = self.size
        bx0, by0, bx1, by1 = self.box
        m = np.zeros((h, w), np.float32)
        cv2.ellipse(m, (int((bx0 + bx1) / 2), int((by0 + by1) / 2 + 6)), (int((bx1 - bx0) / 2), int((by1 - by0) / 2 + 8)), 0, 0, 360, 1, -1)
        self.mask = cv2.GaussianBlur(m, (0, 0), 14)
        self.mask = np.clip(self.mask * 1.35, 0, 1)
        ring = np.zeros((h, w), np.float32)
        cv2.ellipse(ring, (int((bx0 + bx1) / 2), int((by0 + by1) / 2 + 6)), (int((bx1 - bx0) / 2 + 26), int((by1 - by0) / 2 + 30)), 0, 0, 360, 1, 22)
        self.ring = ring > 0.5

    def composite(self, head_name, head_bgr, alpha, vis):
        """head_bgr: HxWx3 (straight colour), alpha HxW; returns new colour with the mouth shape pasted."""
        if head_name not in self.to_head or vis is None: return head_bgr
        M = self.to_head[head_name]
        H, W = head_bgr.shape[:2]
        src = self.shapes[vis].astype(np.float32)
        # colour match on the ring (in the REST frame)
        hr = cv2.warpAffine(head_bgr, cv2.invertAffineTransform(M), self.size, flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        ms, mh = src[self.ring].mean(0), hr[self.ring].mean(0)
        g = np.clip((hr[self.ring].std(0) + 1) / (src[self.ring].std(0) + 1), 0.8, 1.2)
        src = np.clip((src - ms) * g + mh, 0, 255)
        patch = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        A = cv2.warpAffine(self.mask, M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
        return np.clip(head_bgr * (1 - A) + patch * A, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    P = pickle.load(open("parts.pkl", "rb"))
    d = build(P)
    pickle.dump(d, open("mouths.pkl", "wb"))
    mo = Mouths()
    S_ = "/tmp/claude-0/-home-user-TV-show-/17c2eb03-f7c3-5c18-9c9e-6908366e9c0f/scratchpad/"
    # the 19 aligned shapes
    bx0, by0, bx1, by1 = d["box"]
    strip = [cv2.resize(d["shapes"][n][by0 - 60:by1 + 30, bx0 - 40:bx1 + 40], None, fx=0.5, fy=0.5) for n in MOUTH_ROW1 + MOUTH_ROW2]
    cv2.imwrite(S_ + "mouth_shapes.png", np.vstack([np.hstack(strip[:10]), np.hstack(strip[10:] + [np.zeros_like(strip[0])])]))
    rows = []
    for hn in ["NEUTRAL", "SAD", "DISGUSTED", "RAISED BROW", "SURPRISED"]:
        img = P["head"][hn][0]
        tiles = []
        for v in ["REST", "A", "E", "O", "U", "M", "FV", "SZ"]:
            c = mo.composite(hn, np.ascontiguousarray(img[..., :3]), img[..., 3], v)
            H = c.shape[0]
            tiles.append(cv2.resize(c[int(H * 0.35):int(H * 0.95), 60:-60], None, fx=0.45, fy=0.45))
        hmin = min(t.shape[0] for t in tiles); wmin = min(t.shape[1] for t in tiles)
        rows.append(np.hstack([t[:hmin, :wmin] for t in tiles]))
    wmin = min(r.shape[1] for r in rows)
    cv2.imwrite(S_ + "mouth_test.png", np.vstack([r[:, :wmin] for r in rows]))

"""Profile rig (facing screen-left) for the window gag: the LEFT turnaround body mirrored, its near arm cut out
and rigged at the shoulder so it can extend towards the skyline, and the mouth sheet's four side-view heads
(closed / A / O / U) swapped in for lip sync."""
import numpy as np, cv2, pickle
from rig import graded_premul, classes, K, to3
from matte import matte, nearest

S = 4
SIDE = {"NEUTRAL": (1293, 1418), "A": (1416, 1540), "O": (1538, 1662), "U": (1660, 1774)}   # mouth sheet 1x x-ranges
SIDE_Y = (699, 846)
# viseme -> side-view mouth
SIDE_OF = {"A": "A", "E": "A", "I": "A", "CDGK": "A", "L": "A", "R": "O", "TH": "A", "CHJ": "O",
           "O": "O", "W": "U", "Q": "O", "U": "U"}
# the near arm (mirrored body, 4x crop px): sleeve + hand, and the shoulder pivot
ARM = [(236, 372), (300, 360), (340, 385), (358, 440), (360, 560), (352, 700), (345, 800), (332, 862), (290, 872),
       (282, 1004), (170, 1008), (164, 900), (186, 850), (198, 820), (202, 700), (197, 600), (202, 500), (210, 430)]
PIVOT = (290.0, 412.0)
# the mirrored body's jaw line (4x crop px): under the chin, up behind the jaw to the ear lobe, along the hair to
# the back collar.  Below it the body drawing's own neck and collar stay; above it the talking side head takes
# over, faded out across the same line (so the head always sits on the drawing's own neck)
JAW = [(0, 346), (75, 344), (138, 350), (152, 300), (165, 262), (200, 245), (262, 250), (310, 270), (345, 290),
       (385, 298)]
JAW_KEEP = 8          # px the body's neck reaches up above the line (under the side head's jaw)
JAW_FADE = (4, 12)    # the side head is solid to 4 px above the line and gone 12 px below it

def side_heads():
    sheet = cv2.imread("src/mouths_x4.png")
    dark = lambda c: c.sum(2) < 560
    out = {}
    for n, (x0, x1) in SIDE.items():
        box = (x0, SIDE_Y[0], x1, SIDE_Y[1])
        seed = nearest(sheet, box, ((x0 + x1) / 2, 760), dark)
        out[n] = matte(sheet, box, seed, open_r=4)
    return out

def on_gray(rgba, g=128):
    a = rgba[..., 3:4] / 255.0
    return (rgba[..., :3] * a + g * (1 - a)).astype(np.uint8)

def gray(rgba, g=235.0):
    a = rgba[..., 3:4] / 255.0
    return cv2.cvtColor((rgba[..., :3] * a + g * (1 - a)).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)

def search(head, body):
    """side head -> body head (similarity), matched on the FACE: gradient NCC over the side head's skin and its
    outlines (the two drawings' hair differs), scale kept to the body's face size.  Cached in profile_fit.pkl."""
    import os, hashlib
    key = hashlib.md5(head[..., 3].tobytes() + body[:420, :, 3].tobytes()).hexdigest()
    try:
        d = pickle.load(open("profile_fit.pkl", "rb"))
        if d.get("key") == key: return d["M"]
    except (OSError, EOFError, pickle.UnpicklingError):
        pass
    def feat(rgba):
        g = gray(rgba)
        gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
        return cv2.GaussianBlur(np.sqrt(gx * gx + gy * gy), (0, 0), 2.0)
    fb = feat(body[:420]); fh = feat(head)
    _, skin, _, _ = classes(head)
    mh = cv2.dilate(skin.astype(np.uint8), K(7)).astype(np.float32)
    mh[int(0.80 * head.shape[0]):] = 0                                  # the face, not the collar
    hh, hw = head.shape[:2]
    best = (-2, None)
    for s in np.arange(0.66, 0.801, 0.01):
        for r in np.arange(-8, 8.1, 1.0):
            Mr = cv2.getRotationMatrix2D((hw / 2, hh / 2), r, s)
            Mr[0, 2] += hw * s / 2 - hw / 2 + 20; Mr[1, 2] += hh * s / 2 - hh / 2 + 20
            size = (int(hw * s) + 40, int(hh * s) + 40)
            t = cv2.warpAffine(fh, Mr, size); m = cv2.warpAffine(mh, Mr, size)
            ys, xs = np.where(m > 0.5)
            t = t[ys.min():ys.max() + 1, xs.min():xs.max() + 1]; m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
            if t.shape[0] > fb.shape[0] or t.shape[1] > fb.shape[1]: continue
            res = cv2.matchTemplate(fb, t, cv2.TM_CCOEFF_NORMED, mask=m)
            res[~np.isfinite(res)] = -2
            _, mv, _, ml = cv2.minMaxLoc(res)
            if mv > best[0]:
                A = np.array([[1, 0, ml[0] - xs.min()], [0, 1, ml[1] - ys.min()], [0, 0, 1]]) @ to3(Mr)
                best = (mv, A[:2])
    print("side head -> body: score %.3f scale %.3f" % (best[0], np.sqrt(abs(np.linalg.det(best[1][:, :2])))))
    tmp = "profile_fit.%d.tmp" % os.getpid()                             # atomic: parallel renders may race
    pickle.dump({"key": key, "M": best[1]}, open(tmp, "wb")); os.replace(tmp, "profile_fit.pkl")
    return best[1]

def ecc_shift(img, ref):
    g1, g2 = gray(ref), gray(img)
    h, w = g1.shape; g2 = cv2.copyMakeBorder(g2, 0, max(0, h - g2.shape[0]), 0, max(0, w - g2.shape[1]), cv2.BORDER_REPLICATE)[:h, :w]
    m = np.zeros((h, w), np.uint8); m[:int(h * 0.45)] = 255          # hair + eyes (the mouth changes)
    W_ = np.eye(2, 3, dtype=np.float32)
    try:
        _, W_ = cv2.findTransformECC(g1, g2, W_, cv2.MOTION_TRANSLATION, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), m, 5)
    except cv2.error:
        pass
    return cv2.invertAffineTransform(W_)            # img -> ref

class Profile:
    def __init__(self, P):
        body = P["turn"]["LEFT"][0][:, ::-1].copy()
        H, W = body.shape[:2]
        self.floor = float(np.where((body[..., 3] > 128).any(1))[0].max()) - 4
        yy, xx = np.mgrid[0:H, 0:W]
        red, skin, white, grey = classes(body)
        # ---- arm layer
        am = np.zeros((H, W), np.uint8); cv2.fillPoly(am, [np.array(ARM, np.int32)], 1)
        am = am.astype(bool) & (body[..., 3] > 0)
        # below the cuff only the hand itself (skin + its outline), not the trouser leg behind it
        handm = cv2.dilate(skin.astype(np.uint8), K(5)).astype(bool)
        am &= (yy < 858) | handm
        arm = body.copy(); arm[..., 3] = (arm[..., 3] * cv2.GaussianBlur(am.astype(np.float32), (0, 0), 1.0)).astype(np.uint8)
        self.arm = graded_premul(arm)
        # ---- torso under the arm: jacket / trousers painted in from the surroundings
        hole = cv2.dilate(am.astype(np.uint8), K(3)).astype(bool)
        inside = (body[..., 3] > 128)
        col = body[..., :3].copy()
        known = inside & ~hole
        src = col.copy(); src[~inside] = np.median(col[grey & known], axis=0).astype(np.uint8)
        # bright marks next to the arm (the pocket flap's highlight, cuff) would smear white into the fill
        vv = col.max(2)
        glint = known & (vv > 165) & cv2.dilate(hole.astype(np.uint8), K(30)).astype(bool) & (yy > 600)
        fill = cv2.inpaint(src, (hole | glint).astype(np.uint8) * 255, 25, cv2.INPAINT_TELEA)
        fill = cv2.GaussianBlur(fill, (0, 0), 6)
        tor = body.copy()
        tor[..., :3] = np.where((hole | (glint & (vv > 190)))[..., None], fill, col)
        # the torso silhouette behind the arm: back edge = arm's back edge; the hanging hand's area is leg
        sil = inside | hole
        tor[..., 3] = np.where(hole, 255 * sil, tor[..., 3]).astype(np.uint8)
        # outline the new back contour where the arm used to be the silhouette edge
        edge = hole & ~cv2.erode(sil.astype(np.uint8), K(4)).astype(bool) & sil
        tor[..., :3][edge] = (tor[..., :3][edge] * 0.2 + np.array([22, 18, 20]) * 0.8).astype(np.uint8)
        # jacket hem continues under the old hand
        cv2.line(tor, (150, 914), (306, 906), (30, 26, 30, 255), 6, cv2.LINE_AA)
        # ---- remove the drawing's own face and hair (the side heads replace them): keep its neck and collar
        keep = np.zeros((H, W), np.uint8)
        jk = [(x, y - JAW_KEEP) for x, y in JAW]
        cv2.fillPoly(keep, [np.array(jk + [(W, H), (0, H)], np.int32)], 1)
        keep = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.5)
        tor[..., 3] = (tor[..., 3] * keep).astype(np.uint8)
        self.torso = graded_premul(tor)
        # shoulder cap: jacket disc hiding the seam when the arm swings
        gcol = np.median(col[grey & known & (yy > 380) & (yy < 520)], axis=0).astype(np.uint8)
        cap = np.zeros((H, W, 4), np.uint8); cap[..., :3] = gcol
        disc = np.zeros((H, W), np.uint8); cv2.circle(disc, (int(PIVOT[0]), int(PIVOT[1])), 58, 255, -1, cv2.LINE_AA)
        cap[..., 3] = disc * (tor[..., 3] > 0) + disc * 0
        cap[..., 3] = disc
        self.cap = graded_premul(cap)
        # ---- side-view talking heads, registered onto the body's head
        SH = side_heads()
        n0, _ = SH["NEUTRAL"]
        M0 = search(n0, body)
        self.heads = {}
        for n, (img, _) in SH.items():
            M = M0
            if n != "NEUTRAL":       # same drawing, a few px apart on the sheet: translation-only ECC
                M = (to3(M0) @ to3(ecc_shift(img, n0)))[:2]
            self.heads[n] = (self.strip(img, M), M)
        self.W, self.H = W, H
        self.hip_x = float(np.median(np.where(body[1000, :, 3] > 128)[0]))

    def strip(self, img, M):
        """side head: drop the jacket / shirt / tie at the bottom, and fade it out across the body's jaw line (M:
        side head px -> body px), so below the jaw the body drawing's own neck and collar show"""
        red, skin, white, grey = classes(img)
        H, W = img.shape[:2]
        yy = np.arange(H)[:, None]
        cl = (red | white | grey) & (yy > H * 0.60)
        n, lab, st, _ = cv2.connectedComponentsWithStats(cl.astype(np.uint8))
        keep = np.zeros_like(cl)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_TOP] + st[i, cv2.CC_STAT_HEIGHT] >= H - 10 and st[i, cv2.CC_STAT_AREA] > 200: keep |= lab == i
        dark = (img[..., :3].max(2) < 70) & (yy > H * 0.7)
        keep |= dark & cv2.dilate(keep.astype(np.uint8), K(6)).astype(bool)
        out = img.copy()
        out[..., 3] = (out[..., 3] * (1 - cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.2))).astype(np.uint8)
        m = (out[..., 3] > 60).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        main = lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
        out[..., 3] = (out[..., 3] * cv2.dilate(main.astype(np.uint8), K(2))).astype(np.uint8)
        # thin leftover outline strokes below the jaw
        low = yy > H * 0.62
        solid = cv2.morphologyEx((out[..., 3] > 60).astype(np.uint8), cv2.MORPH_OPEN, K(5)).astype(bool)
        out[..., 3] = np.where(low & ~cv2.dilate(solid.astype(np.uint8), K(1)).astype(bool), 0, out[..., 3]).astype(np.uint8)
        yy_, xx_ = np.mgrid[0:H, 0:W].astype(np.float32)
        bx = M[0, 0] * xx_ + M[0, 1] * yy_ + M[0, 2]; by = M[1, 0] * xx_ + M[1, 1] * yy_ + M[1, 2]
        jx, jy = np.array(JAW, np.float32).T
        line = np.interp(bx, jx, jy)
        f = np.clip((line + JAW_FADE[1] - by) / float(JAW_FADE[0] + JAW_FADE[1]), 0, 1)
        out[..., 3] = (out[..., 3] * f).astype(np.uint8)
        return graded_premul(out)

    def layers(self, vis=None, arm=0.0, head_M=None, body_M=None):
        """arm: degrees about the shoulder (negative swings the hand forward = screen-left, up)."""
        B = to3(body_M) if body_M is not None else np.eye(3)
        Hm = B @ (to3(head_M) if head_M is not None else np.eye(3))
        name = "NEUTRAL" if vis is None else SIDE_OF.get(vis, "NEUTRAL")
        img, M = self.heads[name]
        R = to3(cv2.getRotationMatrix2D(PIVOT, arm, 1.0))
        return [(self.torso, B), (img, Hm @ to3(M)), (self.cap, B), (self.arm, B @ R)]

if __name__ == "__main__":
    from rig import render_layers
    P = pickle.load(open("parts.pkl", "rb"))
    pr = Profile(P)
    tiles = []
    for vis, arm in ((None, 0), ("A", 0), ("O", -40), ("U", -80), (None, -95), ("A", -95)):
        V = np.array([[0.45, 0, 200], [0, 0.45, 10], [0, 0, 1]], float)
        im = render_layers(pr.layers(vis, arm), V, (420, 700))
        tiles.append((im[..., :3] + np.float32([150, 175, 150]) * (1 - im[..., 3:4])).astype(np.uint8))
    cv2.imwrite("profile_test.png", np.hstack(tiles))

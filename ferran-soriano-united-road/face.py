"""The master head, drawn for one frame: base head (mouth and brows painted out) + the frame's mouth + eyes (gaze,
lids) + the two brows, each a layer of the drawing's own brow that slides and bends (raise, arch, sad inner corners,
frown), + small smooth warps for a smile and a squint. Nothing else moves: the head outline, nose, hairline, eye line
and eyes stay exactly where they are, so the face never drifts between expressions.

His brows sit right on his upper lids (2-5 px of lid between), so a brow is not stretched upwards (that would
stretch the lid crease into a thick dark band): the brow layer moves and the lid skin painted in under it shows."""
import json, numpy as np, cv2
from PIL import Image
from scipy import ndimage
import eyes as eyemod

K = 4
MOUTH_CORNERS = [(395.0, 306.0), (478.0, 305.0)]
LOWER_LIDS = [(386.0, 206.0), (478.0, 200.0)]
# brow search boxes (main-sheet coords): x0, y0, x1, y1 and which end is the inner one
BROWBOX = {"R": ((338, 160, 428, 191), "right"),         # his right brow (frame left): inner end towards the nose
           "L": ((434, 150, 528, 181), "left")}          # his left brow (frame right)

def cut_brows(head):
    """-> {side: (box in head px, RGBA layer of the brow, x of inner end, x of outer end)}, browless head"""
    out = {}
    rgb = head[..., :3]
    gray = rgb.mean(2)
    hole = np.zeros(gray.shape, np.uint8)
    off = json.load(open("build/rig/head.json"))["off"]
    for side, ((x0, y0, x1, y1), inner) in BROWBOX.items():
        X0, Y0, X1, Y1 = [int(round(v)) for v in ((x0 - off[0]) * K, (y0 - off[1]) * K, (x1 - off[0]) * K, (y1 - off[1]) * K)]
        dark = gray[Y0:Y1, X0:X1] < 95
        lab, n = ndimage.label(dark)
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        m = lab == 1 + int(np.argmax(sizes))
        m = ndimage.binary_closing(m, iterations=3)
        m = ndimage.binary_fill_holes(m)
        mf = cv2.GaussianBlur(cv2.dilate(m.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 1.5)
        layer = np.zeros((Y1 - Y0, X1 - X0, 4), np.float32)
        layer[..., :3] = rgb[Y0:Y1, X0:X1]
        layer[..., 3] = np.clip(mf, 0, 1)
        xs = np.nonzero(m.any(0))[0]
        xi, xo = (xs.max(), xs.min()) if inner == "right" else (xs.min(), xs.max())
        out[side] = ((X0, Y0), layer, float(xi), float(xo))
        hole[Y0:Y1, X0:X1] |= (cv2.dilate(m.astype(np.uint8), np.ones((9, 9), np.uint8)) * 255)
    browless = head.copy()
    browless[..., :3] = cv2.inpaint(np.clip(rgb, 0, 255).astype(np.uint8), hole, 10, cv2.INPAINT_TELEA)
    return out, browless

class Face:
    def __init__(self):
        self.meta = json.load(open("build/rig/head.json"))
        self.off = self.meta["off"]
        base = np.asarray(Image.open("build/rig/head_nomouth.png")).astype(np.float32)
        self.brows, self.base = cut_brows(base)
        mj = json.load(open("build/rig/mouths.json"))
        self.mouth_xy = mj["origin"]
        self.mouths = {s: np.asarray(Image.open(f"build/rig/mouth_{s}.png")).astype(np.float32) for s in mj["shapes"]}
        self.E = json.load(open("build/rig/eyes.json"))
        self.L = {k: v.astype(np.float32) for k, v in np.load("build/rig/eyes.npz").items()}
        self.H, self.W = self.base.shape[:2]
        self._grid = {}

    def brow_layer(self, rgb, side, lift, inner, arch):
        """draw one brow: lift (main px, + up), inner (+ inner end up = sad, - down = frown), arch (+ outer-middle up)"""
        (X0, Y0), layer, xi, xo = self.brows[side]
        h, w = layer.shape[:2]
        pad = int(14 * K)
        big = np.zeros((h + 2 * pad, w, 4), np.float32); big[pad:pad + h] = layer
        xs = np.arange(w, dtype=np.float32)
        t = np.clip((xs - xi) / (xo - xi), -0.2, 1.2)                         # 0 inner end, 1 outer end
        prof = lift + inner * np.clip(1 - t, 0, 1) ** 1.4 + arch * np.exp(-0.5 * ((t - 0.6) / 0.28) ** 2)
        dyv = -prof * K                                                       # head px, + down
        dxv = (inner * 0.3 * np.sign(xi - xo) * np.clip(1 - t, 0, 1) * K) if inner < 0 else np.zeros_like(xs)
        H2 = big.shape[0]
        ys, xx = np.mgrid[0:H2, 0:w].astype(np.float32)
        mx_ = (xx - dxv[None, :]).astype(np.float32); my_ = (ys - dyv[None, :]).astype(np.float32)
        warped = cv2.remap(big, mx_, my_, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        y0 = Y0 - pad
        a = warped[..., 3:]
        reg = rgb[y0:y0 + H2, X0:X0 + w]
        reg[:] = warped[..., :3] * a + reg * (1 - a)

    def compose(self, st):
        """full-resolution head for state st (dict); returns RGBA float32"""
        img = self.base.copy()
        rgb = img[..., :3]
        p = self.mouths[st.get("vis", "REST")]
        x0, y0 = self.mouth_xy; h, w = p.shape[:2]
        a = p[..., 3:] / 255
        rgb[y0:y0 + h, x0:x0 + w] = p[..., :3] * a + rgb[y0:y0 + h, x0:x0 + w] * (1 - a)
        g = st.get("gaze", (0.0, 0.0)); lid = st.get("lid", 0.0)
        for i in range(2):
            eyemod.compose_eye(rgb, self.E, self.L, i, g, lid)
        bi = st.get("brow_in", 0.0)
        self.brow_layer(rgb, "R", st.get("brow_r", 0.0), bi, 0.0)
        self.brow_layer(rgb, "L", st.get("brow_l", 0.0), bi, st.get("arch", 0.0))
        return img

    def warp_field(self, st, level):
        """displacement (dx, dy) in level px for a smile / smirk / squint, or None"""
        sm = st.get("smile", 0.0); smirk = st.get("smirk", 0.0); sq = st.get("squint", 0.0)
        if abs(sm) < 1e-3 and abs(smirk) < 1e-3 and abs(sq) < 1e-3:
            return None
        s = K * level
        H, W = int(round(self.H * level)), int(round(self.W * level))
        key = (H, W)
        if key not in self._grid:
            ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
            self._grid[key] = (xs / s + self.off[0], ys / s + self.off[1])     # main-sheet coords per pixel
        X, Y = self._grid[key]
        dx = np.zeros((H, W), np.float32); dy = np.zeros((H, W), np.float32)
        for j, (cx, cy) in enumerate(MOUTH_CORNERS):
            amt = sm + (smirk if j == 1 else 0.0)                             # smirk: his left corner (frame right)
            if abs(amt) < 1e-3: continue
            g = np.exp(-0.5 * (((X - cx) / 15) ** 2 + ((Y - cy) / 10) ** 2))
            dy += -4.2 * amt * g * s
            dx += 1.6 * amt * np.sign(cx - 437) * g * s
        if abs(sq) > 1e-3:
            for cx, cy in LOWER_LIDS:
                g = np.exp(-0.5 * (((X - cx) / 20) ** 2 + ((Y - cy - 3) / 6) ** 2))
                dy += -2.2 * sq * g * s
        return dx, dy

    def render(self, st, level=1.0):
        """RGBA float32 head at `level` of full size, for state st"""
        img = self.compose(st)
        if level != 1.0:
            img = cv2.resize(img, (int(round(self.W * level)), int(round(self.H * level))), interpolation=cv2.INTER_AREA)
        f = self.warp_field(st, level)
        if f is not None:
            dx, dy = f
            H, W = img.shape[:2]
            ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
            img = cv2.remap(img, xs - dx, ys - dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        return img

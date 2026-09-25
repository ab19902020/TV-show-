"""Cut-out rig for Roy: neck piece -> head's neck -> body clothes (collar/suit) -> head (hair/face/beard).
All layers are precision mattes from the character sheet; the head is pinned on the neck column."""
import numpy as np, cv2, pickle
from collections import OrderedDict

P = pickle.load(open("parts2.pkl", "rb")); R = pickle.load(open("align.pkl", "rb"))
from mouth4 import composite4
def to3(M): return np.vstack([M, [0, 0, 1]])
HEADS = ["FRONT", "3/4 RIGHT", "SKEPTICAL", "DISGUSTED", "ANGRY", "SAD", "CONFUSED"]
HX0, HY0, HX1, HY1 = 100, 0, 1100, 900
CHAR_H = 1400
K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def classes(col, a):
    c = col.astype(np.int32); b, g, r = c[..., 0], c[..., 1], c[..., 2]
    v = c.max(2); mn = c.min(2)
    on = a > 0.5
    clothes = on & (b > r + 8)
    skin = on & (r > b + 40) & (r > 110)
    beard = on & (v > 150) & (r >= b) & ((v - mn) < 90)
    dark = on & (v < 80)
    return clothes, skin, beard, dark

def fill_holes(m):
    m8 = m.astype(np.uint8)
    cnts, _ = cv2.findContours(m8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    f = np.zeros_like(m8); cv2.drawContours(f, cnts, -1, 1, -1)
    return f.astype(bool)

def big_regions(m, min_area, touch=None):
    n, lab, st, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), connectivity=8)
    out = np.zeros(m.shape, bool)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < min_area: continue
        r = lab == i
        if touch is not None and not (r & touch).any(): continue
        out |= r
    return out

def grade(bgr):
    f = bgr.astype(np.float32) / 255
    f = f ** 1.06 * np.array([0.90, 0.95, 1.02]) * 0.97
    return np.clip(f * 255, 0, 255).astype(np.uint8)

def refs(name):
    """eye line / chin / neck column for a head drawing (crop coords)."""
    from headcenter import refs as _refs
    return _refs(name)

def split_head(name):
    """-> (upper_alpha, neck_alpha) in head-crop coords."""
    rgba = P[name][0]; col = rgba[..., :3]; a = rgba[..., 3].astype(np.float32) / 255
    clothes, skin, beard, dark = classes(col, a)
    r = refs(name)
    H, W = a.shape
    yy = np.arange(H)[:, None]
    y_jaw = r["eye_y"] + 0.45 * (r["chin_y"] - r["eye_y"])
    lower = np.broadcast_to(yy > y_jaw, a.shape)
    # the drawing's own suit + shirt: big bluish regions reaching the bottom of the crop
    bottom = np.zeros_like(clothes); bottom[int(H * 0.72):] = True
    cl = big_regions(clothes & lower, 1500, touch=bottom)
    cl = fill_holes(cv2.morphologyEx(cl.astype(np.uint8), cv2.MORPH_CLOSE, K(4)).astype(bool)) & (a > 0.02)
    beard_big = big_regions(beard & lower, 3000)
    beard_d = cv2.dilate(beard_big.astype(np.uint8), K(4)).astype(bool)
    cl_region = cl | (dark & cv2.dilate(cl.astype(np.uint8), K(7)).astype(bool) & ~beard_d)
    # its neck = whatever is below the head's core blob (upper face + beard, holes filled), column by column
    core = fill_holes((beard_big | ((a > 0.5) & ~lower)) & ~cl_region)
    n, lab, st, _ = cv2.connectedComponentsWithStats(core.astype(np.uint8), connectivity=8)
    core = lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    has = core.any(0)
    ybot = np.where(has, H - 1 - np.argmax(core[::-1], axis=0), -1)
    below = yy > (ybot[None, :] + 3)
    below &= has[None, :] | (yy > y_jaw)
    neck = below & (a > 0.02) & ~cl_region & lower
    neck = neck & ~cv2.dilate(core.astype(np.uint8), K(3)).astype(bool)
    # keep only the real neck: the biggest piece that touches the jaw, drop stray sheet lines
    touch = cv2.dilate(core.astype(np.uint8), K(6)).astype(bool)
    n, lab, st, _ = cv2.connectedComponentsWithStats(neck.astype(np.uint8), connectivity=8)
    best, area = 0, 0
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] > area and (lab == i)[touch].any(): best, area = i, st[i, cv2.CC_STAT_AREA]
    neck = lab == best if best else np.zeros_like(neck)
    upper = (a > 0.02) & ~cl_region & ~neck
    n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.morphologyEx(upper.astype(np.uint8), cv2.MORPH_OPEN, K(5)), connectivity=8)
    core = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    upper = upper & cv2.dilate(core, K(8)).astype(bool)
    upper = fill_holes(upper) & ~neck & ~cl_region          # nothing inside the face can become see-through
    up_a = a * upper
    cut = cv2.dilate((neck | cl_region).astype(np.uint8), K(2)).astype(bool) & upper
    up_a = np.where(cut, np.minimum(up_a, cv2.GaussianBlur(up_a, (0, 0), 1.2)), up_a)
    nk_a = a * cv2.GaussianBlur(neck.astype(np.float32), (0, 0), 1.0)
    return up_a.astype(np.float32), nk_a.astype(np.float32)

class Rig:
    def __init__(self):
        body = P["body"][0][:CHAR_H]
        ba = body[..., 3].astype(np.float32) / 255
        clothes, skin, beard, dark = classes(body[..., :3], ba)
        Hc, Wc = ba.shape
        yy = np.arange(Hc)[:, None]
        on = ba > 0.02
        cl = big_regions(clothes & (yy >= 540), 4000)
        cl = fill_holes(cv2.morphologyEx(cl.astype(np.uint8), cv2.MORPH_CLOSE, K(5)).astype(bool)) & on   # buttons etc.
        beard_d = cv2.dilate(big_regions(beard, 3000).astype(np.uint8), K(6)).astype(bool)
        near_cl = cv2.dilate(cl.astype(np.uint8), K(7)).astype(bool)
        l3m = (cl | (dark & near_cl & ~beard_d)) & (yy >= 540)
        l3m |= on & (yy >= 800)
        l3 = ba * l3m
        # L1: neck piece = the rest of the body between the beard bottom and row 800 (neck + chest V)
        neck = on & (yy >= 628) & (yy < 800) & ~l3m
        nk = neck.astype(np.float32) * ba
        col = body[..., :3].copy()
        # Under the head, the original drawing's beard hid part of the collar / neck. Rebuild that zone
        # (between the collar pieces) so nothing behind any head drawing can ever be see-through.
        nx = int(round(float(cv2.transform(np.float32([[[refs("FRONT")["neck_x"], 800]]]), R["M_fb"])[0, 0, 0])))
        under = np.zeros_like(on)
        for y in range(520, 700):
            xs = np.where(l3m[y, max(0, nx - 230):nx + 230])[0]
            if len(xs) < 2: continue
            xl, xr = xs.min() + max(0, nx - 230), xs.max() + max(0, nx - 230)
            under[y, xl:xr + 1] = True
        under &= ~l3m
        unknown = under & ~neck
        skin_med = np.median(col[neck & skin], axis=0).astype(np.uint8)
        src = col.copy()
        src[:520] = skin_med                                   # only neck/collar colours feed the rebuild
        col_in = cv2.inpaint(src, (unknown).astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA)
        col[unknown] = col_in[unknown]
        nk = np.maximum(nk, under.astype(np.float32))
        self.under = under
        self.body_col = grade(col)
        self.l1 = nk
        self.l3 = l3
        # head placement (neck-column anchoring)
        self.M_head, self.split = {}, {}
        rf = refs("FRONT"); mid_f = (rf["eye_y"] + rf["chin_y"]) / 2
        for h in HEADS:
            if h == "FRONT": M = R["M_fb"]
            else:
                r = refs(h)
                sc = float(np.sqrt(abs(np.linalg.det(R["M_" + h][:, :2]))))
                Mhf = np.array([[sc, 0, rf["neck_x"] - sc * r["neck_x"]], [0, sc, mid_f - sc * (r["eye_y"] + r["chin_y"]) / 2]])
                M = (to3(R["M_fb"]) @ to3(Mhf))[:2]
            M = M.copy(); M[0, 2] -= HX0; M[1, 2] -= HY0
            self.M_head[h] = M
            up, nkh = split_head(h)
            W, H = HX1 - HX0, HY1 - HY0
            upw = cv2.warpAffine(up, M, (W, H), flags=cv2.INTER_LINEAR)
            nkw = cv2.warpAffine(nkh, M, (W, H), flags=cv2.INTER_LINEAR)
            yb = np.arange(H)[:, None] + HY0
            nkw *= np.clip((668 - yb) / 26, 0, 1)          # head's neck melts into the neck piece (skin on skin)
            self.split[h] = (upw, nkw)
        nf = cv2.transform(np.float32([[[rf["neck_x"], rf["chin_y"] + 30]]]), R["M_fb"])[0, 0]
        self.neck_x = float(nf[0])
        self.cache = OrderedDict()

    def head_img(self, head, vis):
        key = (head, vis)
        if key in self.cache:
            self.cache.move_to_end(key); return self.cache[key]
        base = P[head][0][..., :3]
        img = base if vis is None else composite4(np.ascontiguousarray(base), head, vis)
        W, H = HX1 - HX0, HY1 - HY0
        out = cv2.warpAffine(grade(img), self.M_head[head], (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        self.cache[key] = out
        if len(self.cache) > 60: self.cache.popitem(last=False)
        return out

    def compose(self, head, vis, head_M=None, body_M=None):
        """premultiplied float RGBA in body-crop coords"""
        Hc, Wc = self.l3.shape
        bc = self.body_col.astype(np.float32)
        def lay(a, c): return np.dstack([c * a[..., None], a])
        L1 = lay(self.l1, bc)
        L3 = lay(self.l3, bc)
        if body_M is not None:
            L1 = cv2.warpAffine(L1, body_M, (Wc, Hc)); L3 = cv2.warpAffine(L3, body_M, (Wc, Hc))
        hc = self.head_img(head, vis)
        up, nk = self.split[head]
        M = np.array([[1, 0, HX0], [0, 1, HY0]], np.float32)
        if head_M is not None: M = (to3(head_M) @ to3(M))[:2]
        L2 = cv2.warpAffine(lay(nk, hc), M, (Wc, Hc)); L4 = cv2.warpAffine(lay(up, hc), M, (Wc, Hc))
        out = L1
        for L in (L2, L3, L4):
            out = L + out * (1 - L[..., 3:4])
        return out

"""Where every mouth piece sits on every talking head (sheet coordinates, 1x).

Carrick's and Jason's mouth pieces include the chin and beard around the lips, drawn at the heads' own scale, so
each piece is found on a head by template matching (edge images, over a range of scales). The outer ring of the
piece (beard / jaw line) drives the match, the lips in the middle are masked out because they differ per shape.

For the executives' lips-only pieces there is nothing around the lips to match, so their heads' mouths are given
by hand (MOUTH_HAND: centre and width of the closed lips) and each piece is scaled to that width.

Output: build/features.json {head: {piece: [scale, x, y]}} = piece pixel (u, v) lands on sheet point
(x + u * scale, y + v * scale) of the head, where (u, v) are the piece's 1x cut coordinates."""
import json, sys, numpy as np, cv2
from PIL import Image, ImageDraw
import parts

SHEETS = {}
def cut1(n):
    sp = parts.SPEC[n]
    if sp["src"] not in SHEETS: SHEETS[sp["src"]] = parts.load(sp["src"])[0]
    rgb, a, off = parts.cut(n, sp, SHEETS)
    return rgb.astype(np.uint8), a, off

def edges(rgb):
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    g = cv2.GaussianBlur(g, (0, 0), 1.0)
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)
    return np.sqrt(gx * gx + gy * gy)

def ring_mask(a):
    """piece alpha minus the central lips area"""
    h, w = a.shape
    m = (a > 0.5).astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    ys, xs = np.nonzero(m)
    cx, cy = xs.mean(), ys.min() + 0.33 * (ys.max() - ys.min())
    lips = ((xx - cx) / (0.30 * (xs.max() - xs.min()))) ** 2 + ((yy - cy) / (0.22 * (ys.max() - ys.min()))) ** 2 < 1
    m[lips] = 0
    return cv2.erode(m, np.ones((3, 3), np.uint8))

def locate(head, piece, scales, cbox):
    """best placement of the piece whose CENTRE lies inside cbox (sheet coords x0, y0, x1, y1)"""
    hr, ha, (hx, hy) = head
    pr, pa, _ = piece
    He = edges(hr) * (ha > 0.5)
    best = (-2, None)
    for s in scales:
        pe = cv2.resize(edges(pr), None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        pm = cv2.resize(ring_mask(pa), None, fx=s, fy=s, interpolation=cv2.INTER_NEAREST)
        ph, pw = pe.shape
        if ph >= He.shape[0] or pw >= He.shape[1]: continue
        r = cv2.matchTemplate(He, pe, cv2.TM_CCOEFF_NORMED, mask=pm)
        r = np.nan_to_num(r, nan=-2, posinf=-2, neginf=-2)
        # allowed top-left positions: centre inside cbox
        yy, xx = np.mgrid[0:r.shape[0], 0:r.shape[1]]
        cx, cy = xx + hx + pw / 2, yy + hy + ph / 2
        ok = (cx >= cbox[0]) & (cx <= cbox[2]) & (cy >= cbox[1]) & (cy <= cbox[3])
        r[~ok] = -2
        _, v, _, loc = cv2.minMaxLoc(r)
        if v > best[0]: best = (v, (s, loc[0], loc[1]))
    v, (s, x, y) = best
    return dict(score=float(v), scale=float(s), x=float(x + hx), y=float(y + hy))

# head -> (mouth piece prefix, search box for the piece centre (sheet coords), scale range)
TALKERS = {
    "ck_h_neutral": ("ck_m", (200, 590, 260, 650), (0.8, 1.2)), "ck_h_smile": ("ck_m", (195, 235, 265, 300), (0.8, 1.2)),
    "ck_h_frown": ("ck_m", (560, 590, 620, 650), (0.8, 1.2)), "ck_h_surprised": ("ck_m", (915, 590, 975, 655), (0.8, 1.2)),
    "ck_h_q34": ("ck_m", (560, 230, 640, 300), (0.7, 1.15)),
    "js_p_point": ("js_m", (80, 760, 105, 790), (0.28, 0.55)), "js_p_tablet": ("js_m", (250, 760, 275, 790), (0.28, 0.55)),
    "js_p_crossed": ("js_m", (405, 755, 432, 785), (0.28, 0.55)), "js_p_chin": ("js_m", (563, 758, 590, 788), (0.28, 0.55)),
    "js_p_present": ("js_m", (746, 755, 773, 785), (0.28, 0.55)), "js_p_phone": ("js_m", (1218, 752, 1245, 782), (0.28, 0.55)),
    "js_b_suit": ("js_m", (115, 110, 145, 140), (0.55, 1.0)),
}
# closed-lips centre and width (sheet px) for the lips-only mouth sets, read off zoomed grids
MOUTH_HAND = {}

def main(which=None):
    out = json.load(open("build/features.json")) if which else {}
    tiles = []
    for h, (pre, cbox, (s_lo, s_hi)) in TALKERS.items():
        if which and h not in which: continue
        head = cut1(h)
        pcs = sorted([n for n in parts.SPEC if n.startswith(pre) and n[len(pre):].isdigit()], key=lambda n: int(n[len(pre):]))
        hw = (head[1] > 0.5).any(0).sum()
        res = {}
        # the rest piece (index 0) fixes the scale, the other pieces search near it
        base = locate(head, cut1(pcs[0]), np.arange(s_lo, s_hi, 0.01), cbox)
        for p in pcs:
            pc = cut1(p)
            s0 = base["scale"]
            res[p] = locate(head, pc, np.arange(s0 * 0.95, s0 * 1.05, 0.005), cbox)
        out[h] = res
        print(h, "base", round(base["scale"], 2), round(base["score"], 3), [round(v["score"], 2) for v in res.values()], flush=True)
        # check image: the head with piece 1 (open) and the rest piece composited
        hr, ha, (hx, hy) = head
        for p in (pcs[0], pcs[1], pcs[3]):
            pr, pa, _ = cut1(p); f = res[p]
            M = np.float32([[f["scale"], 0, f["x"] - hx], [0, f["scale"], f["y"] - hy]])
            wr = cv2.warpAffine(pr.astype(np.float32), M, (hr.shape[1], hr.shape[0]))
            wa = cv2.warpAffine(pa, M, (hr.shape[1], hr.shape[0]))
            wa = cv2.GaussianBlur(wa, (0, 0), 0.8)[..., None]
            comp = (hr * (1 - wa) + wr * wa)
            bg = np.array([255, 0, 255])
            im = Image.fromarray((comp * ha[..., None] + bg * (1 - ha[..., None])).astype(np.uint8))
            im.thumbnail((240, 240)); d = ImageDraw.Draw(im); d.text((2, 2), f"{h} {p}", fill=(255, 255, 0))
            tiles.append(im)
    json.dump(out, open("build/features.json", "w"), indent=1)
    cols = 9
    s = Image.new("RGB", (245 * cols, 245 * ((len(tiles) + cols - 1) // cols)), (30, 30, 30))
    for i, t in enumerate(tiles): s.paste(t, ((i % cols) * 245, (i // cols) * 245))
    s.save("build/features_check.jpg", quality=85)

if __name__ == "__main__":
    main(sys.argv[1:] or None)

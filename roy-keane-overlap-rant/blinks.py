"""Blinks v2: eye opening mask -> inpainted closed lid + lash line (all precomputed per head)."""
import numpy as np, cv2, pickle
from cutout import *
P = pickle.load(open("parts.pkl", "rb")); R = pickle.load(open("align.pkl", "rb"))
FRONT_EYES = [(1002 * 4 - 3592, 151 * 4 - 152), (1041 * 4 - 3592, 151 * 4 - 152)]

def eye_masks(name):
    img = P[name][0][..., :3]
    M = np.eye(3)[:2] if name == "FRONT" else cv2.invertAffineTransform(R["M_" + name])
    s = np.sqrt(abs(np.linalg.det(M[:, :2])))
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    H, W = img.shape[:2]
    out = []
    for ex, ey in FRONT_EYES:
        cx, cy = cv2.transform(np.float32([[[ex, ey]]]), M)[0, 0]
        r = int(95 * s)
        x0, y0, x1, y1 = int(cx - r), int(cy - r * 0.6), int(cx + r), int(cy + r * 0.6)
        win = hsv[y0:y1, x0:x1]
        white = ((win[..., 2] > 195) & (win[..., 1] < 70)).astype(np.uint8)
        dark = (win[..., 2] < 90).astype(np.uint8)
        n, lab, st, cen = cv2.connectedComponentsWithStats(white)
        keep = np.zeros_like(white)
        for i in range(1, n):
            a = st[i, cv2.CC_STAT_AREA]; wid = st[i, cv2.CC_STAT_WIDTH]
            if a < 25 or wid > r * 1.1: continue
            if abs(cen[i][0] - (cx - x0)) < r * 0.8 and abs(cen[i][1] - (cy - y0)) < r * 0.4:
                keep[lab == i] = 1
        if keep.sum() < 20:
            out.append(None); continue
        pts = cv2.findNonZero(keep)
        hull = np.zeros_like(keep); cv2.fillConvexPoly(hull, cv2.convexHull(pts), 1)
        # opening = hull + iris (dark pixels inside the hull's horizontal span, near hull rows)
        opening = hull.copy()
        ys, xs = np.where(hull)
        band = np.zeros_like(hull); band[max(0, ys.min() - 6):ys.max() + 6, xs.min():xs.max() + 1] = 1
        opening |= (dark & band)
        opening = cv2.morphologyEx(opening, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
        full = np.zeros((H, W), np.uint8); full[y0:y1, x0:x1] = opening
        out.append(full)
    return out

def closed_eye_image(name):
    img = P[name][0][..., :3].copy()
    masks = eye_masks(name)
    lines = []
    inp_mask = np.zeros(img.shape[:2], np.uint8)
    for m in masks:
        if m is None: continue
        mm = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
        inp_mask |= mm
    # inpaint from skin only: neutralise dark (brow / outline) pixels around the hole first
    ring = cv2.dilate(inp_mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))) & (1 - inp_mask)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    skin = ring.astype(bool) & (hsv[..., 2] > 120) & (hsv[..., 1] > 70)
    tmp = img.copy()
    if skin.sum() > 20:
        med = np.median(img[skin], axis=0)
        bad = ring.astype(bool) & ~skin
        # replace non-skin ring pixels with a blurred skin estimate
        sk = img.astype(np.float32).copy(); sk[~skin] = med
        sk = cv2.GaussianBlur(sk, (0, 0), 6)
        tmp[bad] = sk[bad].astype(np.uint8)
    closed = cv2.inpaint(tmp, inp_mask * 255, 13, cv2.INPAINT_TELEA)
    blur = cv2.GaussianBlur(closed, (0, 0), 4)
    k = cv2.GaussianBlur(inp_mask.astype(np.float32), (0, 0), 1.5)[..., None]
    closed = (img * (1 - k) + blur * k).astype(np.uint8)
    for m in masks:
        if m is None: continue
        ys, xs = np.where(m)
        x0, x1, top, bot = xs.min(), xs.max(), ys.min(), ys.max()
        pts = []
        for x in np.linspace(x0 - 4, x1 + 4, 24):
            u = (x - (x0 + x1) / 2) / ((x1 - x0) / 2 + 6)
            y = top + (bot - top) * 0.55 + (bot - top) * 0.28 * (1 - u * u)
            pts.append((int(x), int(y)))
        cv2.polylines(closed, [np.array(pts, np.int32)], False, (30, 26, 28), 7, cv2.LINE_AA)
        # small crease above
    return closed, inp_mask

if __name__ == "__main__":
    tiles = []
    for name in ["FRONT", "3/4 RIGHT", "SKEPTICAL", "DISGUSTED", "ANGRY", "SAD", "CONFUSED"]:
        img = P[name][0][..., :3]
        closed, im = closed_eye_image(name)
        half = img.copy()
        ys, xs = np.where(im > 0)
        cy, cx = int(ys.mean()), int(xs.mean())
        row = [img, closed]
        row = [r[max(0, cy - 110):cy + 110, max(0, cx - 230):cx + 230] for r in row]
        tiles.append(np.hstack([cv2.resize(r, (460, 220)) for r in row]))
    cv2.imwrite("blink_check2.png", cv2.resize(np.vstack(tiles), None, fx=0.6, fy=0.6, interpolation=cv2.INTER_AREA))

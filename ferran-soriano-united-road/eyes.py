"""Eyes and brows on the master head.

Gaze: the iris (with its pupil and highlight) moves inside the eye opening; the eye white behind it is the drawing's
own white, painted across where the iris was; the lids and lashes never move, so the iris is always clipped by the
drawn lids. The iris's hidden top (under the upper lid) is completed by mirroring its lower half.
Blinks: fully closed = the closed-eye drawing from the main sheet, registered onto the face; half closed = the
upper lid drawn down to the middle of the opening in that drawing's lid colour, with the lash line on its edge.
One raised eyebrow = the raised-brow drawing's arched brow over his left eye (frame right), registered onto the face.
Other brow moves (both up, sad inner corners, a frown) are small smooth warps of the brow area in eyes_warp().

-> build/rig/eyes.npz (per-eye layers and masks), build/rig/eyes.json"""
import json, numpy as np, cv2
from PIL import Image
from scipy import ndimage

LASH = 16                        # head px: thickness of the drawn upper lash line above the eye white

def head_px():
    hm = json.load(open("build/rig/head.json"))
    return hm, np.asarray(Image.open("build/rig/head_nomouth.png")).astype(np.float32)

def fit_quadratic(xs, ys):
    A = np.stack([xs ** 2, xs, np.ones_like(xs)], 1)
    c, *_ = np.linalg.lstsq(A, ys, rcond=None)
    return c

def eye_geometry(rgb, ex, ey):
    """white mask, iris circle, lid curves for the eye around (ex, ey) (head px)"""
    x0, y0 = int(ex - 150), int(ey - 95)
    win = rgb[y0:y0 + 190, x0:x0 + 300]
    mx, mn = win.max(2), win.min(2)
    white = (mn > 185) & (mx - mn < 70)
    lab, n = ndimage.label(white)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    white = np.isin(lab, [1 + i for i in np.argsort(-sizes)[:2] if sizes[i] > 150])   # left + right of the iris
    white = ndimage.binary_closing(white, iterations=2)
    ys, xs = np.nonzero(white)
    wcount = white.sum(0)
    span = np.nonzero(wcount > 0)[0]
    lo, hi = span.min(), span.max()
    # iris: the dark blob inside the white's hull; diameter = its widest row, centre from that row and the width
    hull = np.zeros(white.shape, np.uint8)
    cv2.fillConvexPoly(hull, cv2.convexHull(np.int32(np.stack([xs, ys], 1))), 1)
    gray = cv2.GaussianBlur(win.mean(2), (0, 0), 1.5)
    dark = (gray < 120) & (hull > 0)
    lab2, n2 = ndimage.label(dark)
    sizes2 = ndimage.sum(np.ones_like(lab2), lab2, range(1, n2 + 1))
    blob = lab2 == 1 + int(np.argmax(sizes2))
    blob = ndimage.binary_fill_holes(ndimage.binary_closing(blob, iterations=3))
    widths = blob.sum(1)
    wy = int(np.argmax(widths))
    row = np.nonzero(blob[wy])[0]
    icx = (row.min() + row.max()) / 2; ir = (row.max() - row.min()) / 2 + 2
    by = np.nonzero(blob.any(1))[0]
    icy = by.max() - ir + 1                               # the iris's lower edge is fully visible
    mid = np.arange(int(icx - ir), int(icx + ir) + 1)
    # lid curves from the white's top and bottom edges (outside the iris columns), then across the iris
    tops, bots, px = [], [], []
    for c in span:
        if mid.min() - 6 <= c <= mid.max() + 6: continue
        col = np.nonzero(white[:, c])[0]
        if len(col) < 3: continue
        tops.append(col.min()); bots.append(col.max()); px.append(c)
    px, tops, bots = map(np.float32, (px, tops, bots))
    cu = fit_quadratic(px, tops); cl = fit_quadratic(px, bots)
    return dict(win=(x0, y0), white=white, iris=(x0 + icx, y0 + icy, ir), lids=(cu.tolist(), cl.tolist()),
                span=(x0 + lo, x0 + hi))

def build():
    hm, head = head_px()
    rgb = head[..., :3]
    out, meta = {}, {"eyes": []}
    for i, (ex, ey) in enumerate(hm["eyes"]):
        G = eye_geometry(rgb, ex, ey)
        (x0, y0) = G["win"]
        H, W = 190, 300
        cu, cl = G["lids"]
        xs = np.arange(W, dtype=np.float32)
        top = np.polyval(cu, xs); bot = np.polyval(cl, xs)
        lo, hi = G["span"][0] - x0, G["span"][1] - x0
        yy = np.arange(H, dtype=np.float32)[:, None]
        inside = (yy >= top[None, :] - 1) & (yy <= bot[None, :] + 1) & (xs[None, :] >= lo - 2) & (xs[None, :] <= hi + 2)
        opening = inside.astype(np.float32)
        opening = cv2.GaussianBlur(opening, (0, 0), 1.2)
        win = rgb[y0:y0 + H, x0:x0 + W].copy()
        icx, icy, ir = G["iris"][0] - x0, G["iris"][1] - y0, G["iris"][2]
        disk = np.zeros((H, W), np.uint8)
        cv2.circle(disk, (int(round(icx)), int(round(icy))), int(round(ir)), 255, -1, cv2.LINE_AA)
        diskf = disk.astype(np.float32) / 255
        # eyeball without the iris: inpaint the disk from the surrounding white (keeps the lid's shadow on top)
        hole = ((diskf > 0.02) & (opening > 0.05)).astype(np.uint8) * 255
        hole = cv2.dilate(hole, np.ones((5, 5), np.uint8))
        ball = cv2.inpaint(np.clip(win, 0, 255).astype(np.uint8), hole, 9, cv2.INPAINT_TELEA).astype(np.float32)
        # iris layer: the drawn iris inside the opening, its hidden top mirrored from the bottom half
        vis = (diskf > 0.5) & (opening > 0.5)
        iris = np.zeros((H, W, 4), np.float32)
        iris[..., :3] = win
        cy_i = int(round(icy))
        for yv in range(max(0, cy_i - int(ir) - 2), cy_i):
            ym = 2 * cy_i - yv
            if ym >= H: continue
            row_hidden = (diskf[yv] > 0.02) & ~vis[yv]
            iris[yv, row_hidden, :3] = win[ym, row_hidden]
        iris[..., 3] = diskf
        # half-blink lid colour: from the closed-eye drawing over this eye (filled in by blink patch below)
        out[f"e{i}_ball"] = ball; out[f"e{i}_iris"] = iris; out[f"e{i}_open"] = opening
        meta["eyes"].append({"win": [x0, y0], "size": [W, H], "iris": [float(icx), float(icy), float(ir)],
                             "lids": [cu, cl], "span": [float(lo), float(hi)]})
        print("eye", i, "iris centre %.1f,%.1f r %.1f" % (G["iris"][0], G["iris"][1], ir), "span", G["span"])
    # closed eyes: the eyes-shut drawing registered onto the head (build/rig/alt_faces.json), per-eye patch
    alt = json.load(open("build/rig/alt_faces.json"))
    shut = np.asarray(Image.open("build/parts/face_shut.png")).astype(np.float32)
    Ms = np.float32(alt["face_shut"])
    shut_w = cv2.warpAffine(shut, Ms, (head.shape[1], head.shape[0]), flags=cv2.INTER_CUBIC)
    for i, e in enumerate(meta["eyes"]):
        x0, y0 = e["win"]; W, H = e["size"]
        sw = shut_w[y0:y0 + H, x0:x0 + W, :3]
        win = rgb[y0:y0 + H, x0:x0 + W]
        # patch mask: an ellipse over the opening and lids, below the brow
        m = np.zeros((H, W), np.float32)
        cx = (e["span"][0] + e["span"][1]) / 2
        cv2.ellipse(m, (int(cx), int(e["iris"][1] + 4)), (int((e["span"][1] - e["span"][0]) / 2 + 22), 50), 0, 0, 360, 1, -1, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), 7)
        # colour-match the drawing's skin to the face around the eye
        ring = (m > 0.1) & (m < 0.6)
        diff = (win[ring].mean(0) - sw[ring].mean(0))
        sw = sw + diff
        out[f"e{i}_shut"] = np.dstack([np.clip(sw, 0, 255), m])
        # lid colour for half blinks: the closed lid's skin just above its lash line
        lidband = sw[int(e["iris"][1]) - 30:int(e["iris"][1]), int(cx) - 30:int(cx) + 30].reshape(-1, 3)
        e["lid_rgb"] = np.median(lidband[lidband.mean(1) > 120], axis=0).tolist()
        # ... and the face's own skin between the lid line and the brow (what the drawn lid is made of)
        cu = e["lids"][0]
        band = []
        for x in range(int(cx) - 40, int(cx) + 41, 2):
            t = np.polyval(cu, x)
            band += list(win[int(t - LASH - 22):int(t - LASH - 6), x])
        band = np.float32(band)
        band = band[(band.mean(1) > 110) & (band[:, 0] > band[:, 2] + 30)]
        e["lid_skin"] = np.median(band, axis=0).tolist()
    np.savez_compressed("build/rig/eyes.npz", **{k: v.astype(np.float16) for k, v in out.items()})
    json.dump(meta, open("build/rig/eyes.json", "w"), indent=1)

USE_DRAWN_SHUT = False          # the pasted closed-eye drawing shows its patch edge; the drawn lid reads cleaner

def compose_eye(img, E, L, i, gaze=(0.0, 0.0), lid=0.0):
    """draw eye i on img (head px, float RGB) in place. gaze in iris radii (dx, dy); lid: 0 open, 0.5 half, 1 shut"""
    e = E["eyes"][i]; x0, y0 = e["win"]; W, H = e["size"]
    reg = img[y0:y0 + H, x0:x0 + W]
    if lid >= 0.95 and USE_DRAWN_SHUT:
        p = L[f"e{i}_shut"].astype(np.float32)
        reg[:] = reg * (1 - p[..., 3:]) + p[..., :3] * p[..., 3:]
        return
    op = L[f"e{i}_open"].astype(np.float32)[..., None]
    if abs(gaze[0]) > 1e-3 or abs(gaze[1]) > 1e-3:
        ir = e["iris"][2]
        M = np.float32([[1, 0, gaze[0] * ir], [0, 1, gaze[1] * ir]])
        iris = cv2.warpAffine(L[f"e{i}_iris"].astype(np.float32), M, (W, H), flags=cv2.INTER_LINEAR)
        ball = L[f"e{i}_ball"].astype(np.float32)
        eye = ball * (1 - iris[..., 3:]) + iris[..., :3] * iris[..., 3:]
        reg[:] = reg * (1 - op) + eye * op
    if lid > 0.02:
        cu, cl = e["lids"]
        xs = np.arange(W, dtype=np.float32)
        top = np.polyval(cu, xs); bot = np.polyval(cl, xs)
        lo, hi = e["span"]
        edge = top + (bot - top + 4) * min(1.0, lid) * 0.94
        yy = np.arange(H, dtype=np.float32)[:, None]
        # the lid skin covers the drawn upper lash line too (it moves down with the lid)
        sides = np.clip(np.minimum(xs - (lo - 6), (hi + 6) - xs) / 10, 0, 1)[None, :]
        m = np.clip(edge[None, :] - yy + 0.5, 0, 1) * np.clip(yy - (top[None, :] - LASH) + 0.5, 0, 1) * sides
        # a lit, convex lid: the closed-eye drawing's lid tone, a little darker up by the fold
        lidc = np.minimum(np.float32(e["lid_rgb"]), 255) * 0.95
        shade = np.clip((yy - (top[None, :] - LASH)) / np.maximum(edge - top + LASH, 1)[None, :], 0, 1)
        col = lidc * (0.84 + 0.16 * shade[..., None])
        # the open eye just under the lid's edge falls into its shadow
        sh = np.clip(1 - (yy - edge[None, :]) / 14, 0, 1) * (yy > edge[None, :]) * op[..., 0] * sides * 0.25
        reg[:] = reg * (1 - sh[..., None])
        reg[:] = reg * (1 - m[..., None]) + col * m[..., None]
        # lash line along the lid's edge, following the drawn corners
        ln = np.zeros((H, W), np.float32)
        pts = np.int32([(x, edge[x]) for x in range(int(lo) - 4, int(hi) + 5)])
        if len(pts) > 1:
            cv2.polylines(ln, [pts], False, 1.0, 7 if lid > 0.8 else 6, cv2.LINE_AA)
            ln = cv2.GaussianBlur(ln, (0, 0), 0.9)
            reg[:] = reg * (1 - ln[..., None] * 0.92) + np.float32([30, 22, 20]) * (ln[..., None] * 0.92)

if __name__ == "__main__":
    build()

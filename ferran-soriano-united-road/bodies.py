"""The eight gesture drawings as bodies for the master head, all in one body frame.

Body frame ("world" units): the gesture sheet's pixels of pose G07 (clasped hands, the default), with the origin at
G07's collar point (1068, 678). Every other pose is registered to G07 by its collar and shoulders (SIFT similarity
on the band from the chin to below the crew neck), so the torso stays put when the pose changes and the one master
head sits on every collar the same way ("stable head anchor").

Each pose loses its own head: the skin + hair blob and its ink outline above the collar go; the collar and its top
outline stay (the master head is drawn behind the body, its neck tucked into the collar).

-> build/rig/body_<pose>.png (RGBA, WS px per world unit) + build/rig/bodies.json {pose: origin of the png in world
   units, the registration, the collar line}; build/rig/head_place.json (main-sheet -> world similarity)"""
import json, os, numpy as np, cv2
from PIL import Image
from scipy import ndimage
from align_util import sift_similarity

WS = 8                                  # body png px per world unit (the 8x gesture parts)
ORIGIN = (1068.0, 678.0)                # G07 sheet coords of the world origin (its collar point)
POSES = ["g01", "g02", "g03", "g04", "g05", "g06", "g07", "g08"]
COLTOP = dict(g01=171, g02=169, g03=173, g04=175, g05=627, g06=625, g07=628, g08=625)   # sheet y of each collar top

def sheet():
    return np.asarray(Image.open("src/gestures.png").convert("RGBA")).astype(np.float32)

def flat(c):
    a = c[..., 3:] / 255
    return np.clip(c[..., :3] * a + 128 * (1 - a), 0, 255).astype(np.uint8)

def register_all(G):
    """similarity (2x3) pose sheet -> G07 sheet for every pose, from the collar/shoulder band"""
    from parts import SPEC
    f = 4
    def band(n):
        x0, y0, x1, y1 = SPEC[n]["box"]
        t = COLTOP[n]
        Y0, Y1 = t - 25, t + 80
        c = cv2.resize(flat(G[Y0:Y1, x0:x1]), None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
        return c, (x0, Y0)
    ref, (rx, ry) = band("g07")
    out = {}
    for n in POSES:
        if n == "g07":
            out[n] = [[1, 0, 0], [0, 1, 0]]; continue
        src, (sx, sy) = band(n)
        M, nin, ng = sift_similarity(cv2.cvtColor(src, cv2.COLOR_RGB2BGR), cv2.cvtColor(ref, cv2.COLOR_RGB2BGR),
                                     ratio=0.8, reproj=6)
        T1 = np.array([[f, 0, -sx * f], [0, f, -sy * f], [0, 0, 1]])
        T2 = np.array([[1 / f, 0, rx], [0, 1 / f, ry], [0, 0, 1]])
        out[n] = (T2 @ np.vstack([M, [0, 0, 1]]) @ T1)[:2].tolist()
        print(f"  register {n}: {nin} inliers")
    return out

def head_place():
    """main-sheet -> world similarity for the master head: its face registered onto G07's face (SIFT)"""
    main = np.asarray(Image.open("src/main.png").convert("RGBA")).astype(np.float32)
    ges = sheet()
    f = 3
    mh = cv2.resize(flat(main[20:390, 280:610]), None, fx=f * 0.5, fy=f * 0.5, interpolation=cv2.INTER_AREA)
    gh = cv2.resize(flat(ges[480:650, 995:1145]), None, fx=f, fy=f, interpolation=cv2.INTER_CUBIC)
    M, nin, ng = sift_similarity(cv2.cvtColor(mh, cv2.COLOR_RGB2BGR), cv2.cvtColor(gh, cv2.COLOR_RGB2BGR), ratio=0.8, reproj=8)
    T1 = np.array([[f * 0.5, 0, -280 * f * 0.5], [0, f * 0.5, -20 * f * 0.5], [0, 0, 1]])
    T2 = np.array([[1 / f, 0, 995 - ORIGIN[0]], [0, 1 / f, 480 - ORIGIN[1]], [0, 0, 1]])
    Mw = (T2 @ np.vstack([M, [0, 0, 1]]) @ T1)[:2]
    # keep the head upright: drop the tiny rotation, keep scale and the chin position
    s = float(np.sqrt(abs(np.linalg.det(Mw[:, :2]))))
    chin = Mw @ np.array([440.0, 378.0, 1.0])
    Mu = np.array([[s, 0, chin[0] - s * 440.0], [0, s, chin[1] - s * 378.0]])
    print(f"  head: {nin} inliers, scale {s:.4f}")
    return Mu.tolist()

def remove_head(im, k, off, face_xy):
    """alpha-out the pose's own head: the skin/hair blob at face_xy (sheet coords) and its outline, above the
    collar's top outline"""
    rgb, A = im[..., :3], im[..., 3] / 255
    mx, mn = rgb.max(2), rgb.min(2)
    white = (mn > 175) & (mx - mn < 45) & (A > 0.5)
    dark = (mx < 75) & (A > 0.5)
    skinhair = (A > 0.5) & ~white & ~dark
    lab, _ = ndimage.label(skinhair)
    sx, sy = int((face_xy[0] - off[0]) * k), int((face_xy[1] - off[1]) * k)
    head = ndimage.binary_fill_holes(lab == lab[sy, sx])
    near = ndimage.distance_transform_edt(~head) < 3.2 * k
    grow = head | (dark & near)
    lab2, _ = ndimage.label(grow)
    head = ndimage.binary_fill_holes(lab2 == lab2[sy, sx])
    # the collar: white connected region under the chin; per column, its top edge less the outline's thickness
    wl, _ = ndimage.label(white)
    below = np.zeros_like(white)
    cy = sy + int(40 * k)                                   # well inside the collar, under the chin
    ids = set(np.unique(wl[cy - int(12 * k):cy + int(22 * k), sx - int(40 * k):sx + int(40 * k)])) - {0}
    collar = np.isin(wl, list(ids))
    keep = np.zeros_like(head)
    cols = np.nonzero(collar.any(0))[0]
    for c in cols:
        ys = np.nonzero(collar[:, c])[0]
        keep[max(0, ys.min() - int(2.6 * k)):, c] = True
    # outside the collar's columns nothing of the head reaches down to the shoulders, so no limit is needed
    rm = head & ~keep
    out = im.copy()
    out[rm, 3] = 0
    # soften the new edge along the cut (half a sheet px)
    a = out[..., 3] / 255
    soft = cv2.GaussianBlur(a, (0, 0), 0.5 * k)
    edge = rm | ndimage.binary_dilation(rm, iterations=int(k))
    a = np.where(edge, np.minimum(a, soft), a)
    out[..., 3] = a * 255
    return out, collar

EXTEND_TO = 300.0                       # world y the jumper continues to below the drawings' waist cut

def extend_down(res, wmin):
    """the drawings stop at the waist (a straight cut); the portrait shots, framed like the original interview,
    run past it, so every column that reaches the cut carries on straight down (jumper, sleeves and their outlines)"""
    a = res[..., 3]
    H, W = a.shape
    opaque = a > 10                     # soft silhouette edges carry on too
    rows = np.where((a > 128).any(1))[0]
    cut = rows.max()
    new_h = int(round((EXTEND_TO - wmin[1]) * WS))
    if new_h <= H: return res
    out = np.zeros((new_h, W, 4), np.float32)
    out[:H] = res
    # per column: its last opaque row; columns that reach within 12 units of the cut are continued (the cut is
    # not quite straight: elbows hang a few px below the torso)
    last = np.where(opaque, np.arange(H)[:, None], -1).max(0)
    reach = last >= cut - 12 * WS
    src_row = np.clip(last - 2 * WS, 0, H - 1)
    for x in np.nonzero(reach)[0]:
        out[last[x] - 2 * WS:, x] = res[src_row[x], x]
    # the columns just outside the silhouette keep their soft edge
    return out

def build():
    os.makedirs("build/rig", exist_ok=True)
    G = sheet()
    parts = json.load(open("build/parts/meta.json"))
    reg = register_all(G)
    hp = head_place()
    json.dump({"main_to_world": hp}, open("build/rig/head_place.json", "w"), indent=1)
    meta = {"ws": WS, "origin_sheet_g07": ORIGIN, "poses": {}}
    for n in POSES:
        if n not in parts: print("  (not cut yet)", n); continue
        pm = parts[n]
        im = np.asarray(Image.open(f"build/parts/{n}.png")).astype(np.float32)
        k, off = pm["scale"], pm["off"]
        M = np.vstack([np.float32(reg[n]), [0, 0, 1]])           # pose sheet -> g07 sheet
        Minv = np.linalg.inv(M)
        face = Minv @ np.array([1060.0, 585.0, 1.0])              # G07's face centre, in this pose's sheet coords
        im2, collar = remove_head(im, k, off, face[:2])
        # resample into the world grid: world = g07 - ORIGIN; png px = (world - wmin) * WS
        P2S = np.array([[1 / k, 0, off[0]], [0, 1 / k, off[1]], [0, 0, 1]])      # part px -> pose sheet
        W2 = np.array([[1, 0, -ORIGIN[0]], [0, 1, -ORIGIN[1]], [0, 0, 1]]) @ M @ P2S   # part px -> world
        h, w = im2.shape[:2]
        corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float64).T
        wc = W2 @ corners
        wmin = np.floor(wc[:2].min(1)) - 2; wmax = np.ceil(wc[:2].max(1)) + 2
        T = np.array([[WS, 0, -wmin[0] * WS], [0, WS, -wmin[1] * WS], [0, 0, 1]]) @ W2
        size = (int((wmax[0] - wmin[0]) * WS), int((wmax[1] - wmin[1]) * WS))
        # premultiplied resample so the edges don't pick up the transparent pixels' colour
        pre = im2.copy(); pre[..., :3] *= pre[..., 3:] / 255
        res = cv2.warpAffine(pre, T[:2], size, flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
        a = np.clip(res[..., 3:], 0, 255)
        res[..., :3] = np.where(a > 0.5, res[..., :3] / np.maximum(a, 1e-3) * 255, 0)
        res[..., 3:] = a
        res = extend_down(res, wmin)
        Image.fromarray(np.clip(res, 0, 255).astype(np.uint8)).save(f"build/rig/body_{n}.png")
        meta["poses"][n] = {"origin": wmin.tolist(), "size": list(size), "sheet_to_g07": reg[n]}
        print("  body", n, size)
    json.dump(meta, open("build/rig/bodies.json", "w"), indent=1)

if __name__ == "__main__":
    build()

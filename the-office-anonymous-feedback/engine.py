"""Frame compositing: plates, actors (whole-body drawings with live faces), props, extras, desk occlusion, camera.

World coordinates are the 1x pixels of each set's plate (1672 x 941). Drawings are 4x their native sheet size;
an actor's `scale` is world pixels per native drawing pixel.
"""
import numpy as np, cv2
from functools import lru_cache
import cast, sets

OW, OH = 1920, 1080


# ------------------------------------------------------------------ plates and camera
@lru_cache(maxsize=None)
def plate_levels(name):
    pl, front, mid = sets.build(name)
    fm = (np.dstack([front, mid]) * 255).astype(np.uint8)
    levels = [(4.0, pl, fm)]
    cur, f = pl, fm
    for k in (2.0, 1.0):
        cur = cv2.resize(cur, (cur.shape[1] // 2, cur.shape[0] // 2), interpolation=cv2.INTER_AREA)
        f = cv2.resize(f, (f.shape[1] // 2, f.shape[0] // 2), interpolation=cv2.INTER_AREA)
        levels.append((k, cur, f))
    return levels


def cam_matrix(cam):
    """cam = (cx, cy, w) in world px -> 2x3 world->output"""
    cx, cy, w = cam
    z = OW / w
    return np.array([[z, 0, OW / 2 - cx * z], [0, z, OH / 2 - cy * z]], np.float64), z


def render_plate(name, cam):
    M, z = cam_matrix(cam)
    # pick the plate level that is 1-2 plate px per output px
    for k, pl, front in plate_levels(name):
        if k / z < 2.05 or k == 1.0:
            break
    Mk = M.copy()
    Mk[:, :2] /= k
    img = cv2.warpAffine(pl, Mk, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    fm = cv2.warpAffine(front, Mk, (OW, OH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    fm = fm.astype(np.float32) / 255
    return img, fm[..., 0], fm[..., 1]


# ------------------------------------------------------------------ drawing placement
def place(dst, rgb, a, M, extra_mask=None):
    """composite an RGBA drawing (float rgb 0..255, alpha 0..1) with the 2x3 matrix M (drawing px -> output px)"""
    # downscale first with area filtering so thin lines don't sparkle
    s = np.sqrt(abs(np.linalg.det(M[:, :2])))
    if s < 0.95:
        h, w = a.shape
        nw, nh = max(int(round(w * s)), 1), max(int(round(h * s)), 1)
        rgb = cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA)
        a = cv2.resize(a, (nw, nh), interpolation=cv2.INTER_AREA)
        if extra_mask is not None:
            extra_mask = cv2.resize(extra_mask, (nw, nh), interpolation=cv2.INTER_AREA)
        S = np.array([[w / nw, 0, 0], [0, h / nh, 0], [0, 0, 1]])
        M = np.vstack([M, [0, 0, 1]]) @ S
        M = M[:2]
    # only warp the bounding box on screen
    h, w = a.shape
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float64) @ M.T
    x0, y0 = np.floor(corners.min(0)).astype(int) - 2
    x1, y1 = np.ceil(corners.max(0)).astype(int) + 2
    x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, OW), min(y1, OH)
    if x1 <= x0 or y1 <= y0:
        return None
    Mt = M.copy()
    Mt[0, 2] -= x0
    Mt[1, 2] -= y0
    pa = np.dstack([rgb * a[..., None], a])
    out = cv2.warpAffine(pa, Mt, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    em = None
    if extra_mask is not None:
        em = cv2.warpAffine(extra_mask, Mt, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return (x0, y0, x1, y1), out, em


def comp(dst, placed, alpha_mul=None):
    if placed is None:
        return
    (x0, y0, x1, y1), out, _ = placed
    a = out[..., 3]
    if alpha_mul is not None:
        a = a * alpha_mul
        rgbp = out[..., :3] * alpha_mul[..., None]
    else:
        rgbp = out[..., :3]
    reg = dst[y0:y1, x0:x1]
    reg *= (1 - a[..., None])
    reg += rgbp


def actor_matrix(anchor_px, pos, scale, z, Mcam, mirror=False, rot=0.0, w_px=None):
    """drawing px (4x) -> output px. anchor_px is the drawing point placed at world pos."""
    s = scale / 4.0
    c, sn = np.cos(np.radians(rot)), np.sin(np.radians(rot))
    mx = -1.0 if mirror else 1.0
    # drawing -> world: translate anchor to origin, mirror, rotate, scale, translate to pos
    A = np.array([[mx * s * c, -s * sn], [mx * s * sn, s * c]])
    t = np.array(pos, np.float64) - A @ np.array(anchor_px, np.float64)
    W = np.hstack([A, t[:, None]])
    W3 = np.vstack([W, [0, 0, 1]])
    return (np.vstack([Mcam, [0, 0, 1]]) @ W3)[:2]


# ------------------------------------------------------------------ hands (what stays visible on the desk)
@lru_cache(maxsize=None)
def hand_mask(char, pose):
    """the hands (and bare forearms) of a seated drawing, with their own black outline but none of the trousers
    they rest on: what stays visible in front of the desk top"""
    rgb, a = cast.drawing(char, pose)
    r = cast.rig(char, pose)
    skin = r["eyes"][0].skin if r["eyes"] else np.array([240, 180, 130.])
    d = np.abs(rgb.astype(np.float32) - skin).sum(2)
    H = a.shape[0]
    m = ((d < 95) & (a > 128)).astype(np.uint8)
    m[: int(r["eyes_mid"][1] + 0.55 * (H - r["eyes_mid"][1]) * 0.6)] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] > 900:
            keep[lab == i] = 1
    keep = cv2.morphologyEx(keep, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    # grow through the ink line only: near-black pixels (the trousers are a lighter charcoal)
    ink = ((rgb.max(2) < 21) & (a > 128)).astype(np.uint8)
    k3 = np.ones((3, 3), np.uint8)
    for _ in range(12):
        keep = keep | (cv2.dilate(keep, k3) & ink)
    keep = cv2.dilate(keep, k3)          # half a pixel past the line, for the anti-aliasing
    return cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 0.8)


# ------------------------------------------------------------------ finishing
@lru_cache(maxsize=None)
def vignette():
    y, x = np.mgrid[0:OH, 0:OW].astype(np.float32)
    r = np.sqrt(((x - OW / 2) / (OW / 2)) ** 2 + ((y - OH / 2) / (OH / 2)) ** 2)
    return (1 - 0.16 * np.clip(r - 0.55, 0, 1) ** 1.6)[..., None]


def finish(img, seed):
    rng = np.random.default_rng(seed)
    g = rng.normal(0, 2.2, (OH // 2, OW // 2)).astype(np.float32)
    g = cv2.resize(g, (OW, OH), interpolation=cv2.INTER_LINEAR)[..., None]
    img = img * vignette() + g
    return np.clip(img, 0, 255).astype(np.uint8)

"""Maguire's close-up lip sync: his 12 lip-sync busts are drawn separately, so the lines shift a little from bust to
bust. Swapping whole busts would make the drawing boil. Instead every viseme is the neutral bust with only its mouth
area replaced: each bust is registered onto the neutral one (translation, on the upper face), colour-matched on a
ring of skin, and its mouth pasted through a feathered ellipse that stays clear of the nose, jaw and chin lines.

Needs the upscaled mg_l_* parts (parts.py). Output: build/parts/mg_v_<viseme>.png + meta.json entries (same
offset as the neutral bust, so cast.py can use the neutral bust's sheet coordinates for every viseme)."""
import json, numpy as np, cv2
from PIL import Image

SHEET = "../assets/characters/harry-maguire/other-styles/harry-maguire__lip-sync-expressions__20260928T100945__0784fbdd.png"
COLS, ROWS = [12, 290, 563, 835], [8, 446, 884]
NAMES = ["rest", "A", "E", "I", "O", "U", "MBP", "FV", "L", "smile", "frown", "shout"]
# the mouth area on the neutral bust (sheet px): centre, radii, feather
MC, MR, FEATHER = (177.0, 214.0), (52.0, 31.0), 6.0


def sheet_shift(sheet, i):
    """integer (dx, dy) that takes neutral-bust sheet coords onto bust i (upper face, least squares)"""
    ref = sheet[90:200, 90:270]
    ox, oy = COLS[i % 4] - COLS[0], ROWS[i // 4] - ROWS[0]
    best = None
    for dy in range(-10, 11):
        for dx in range(-40, 41):
            c = sheet[oy + 90 + dy:oy + 200 + dy, ox + 90 + dx:ox + 270 + dx]
            if c.shape != ref.shape: continue
            e = float(np.mean((c - ref) ** 2))
            if best is None or e < best[0]: best = (e, ox + dx, oy + dy)
    return best[1], best[2]


def with_body(bust, meta):
    """The busts stop square at the cell edges (shoulders cut at the sides and bottom). Put his turnaround body
    (mg_t_front) under the bust: scaled 1.57x so its shoulder slope lies on the bust's own shoulder outline, the
    head cut off at the collar, the shirt colour matched; the bust fades out over its cut edges.
    Returns (RGBA float canvas, sheet offset of the canvas) in the neutral bust's sheet coordinates."""
    ox, oy = meta["mg_l_rest"]["off"]
    s, cx0, cy0, cx1, cy1 = 1.57, -45.0, ox, 372.0, 470.0
    Wc, Hc = int((cx1 - cx0) * 4), int((cy1 - cy0) * 4)
    body = np.asarray(Image.open("build/parts/mg_t_front.png").convert("RGBA")).astype(np.float32)
    bx, by = meta["mg_t_front"]["off"]
    # body part px -> turnaround sheet -> bust sheet -> canvas px
    # xb = 164 + s (xt - 160), yb = 285 + s (yt - 150)
    ax = s; bxx = (164 + s * (bx - 160) - cx0) * 4
    byy = (285 + s * (by - 150) - cy0) * 4
    A = np.float32([[ax, 0, bxx], [0, ax, byy]])
    bw = cv2.warpAffine(body, A, (Wc, Hc), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    bw = np.clip(bw, 0, 255)
    yy = np.arange(Hc, dtype=np.float32)[:, None] / 4 + cy0
    cut = np.clip((yy - 276) / 4, 0, 1)                   # no head: the body starts under the collar
    bw[..., 3] *= cut
    # the bust on the canvas, its cut edges faded
    H, W = bust.shape[:2]
    px, py = int(round((ox - cx0) * 4)), 0
    bc = np.zeros((Hc, Wc, 4), np.float32)
    bc[py:py + H, px:px + W] = bust
    xs = np.arange(Wc, dtype=np.float32)[None, :] / 4 + cx0
    fade = np.clip((372 - yy) / 16, 0, 1) * np.clip(1 - (yy > 300) * np.clip((40 - xs) / 14, 0, 1), 0, 1) \
        * np.clip(1 - (yy > 300) * np.clip((xs - 276) / 14, 0, 1), 0, 1)
    # shirt colour: body red -> bust red
    red_b = (bust[..., 0] > 150) & (bust[..., 1] < 90) & (bust[..., 3] > 200)
    red_w = (bw[..., 0] > 150) & (bw[..., 1] < 90) & (bw[..., 3] > 200)
    if red_b.any() and red_w.any():
        k = np.clip(np.median(bust[..., :3][red_b], 0) / np.maximum(np.median(bw[..., :3][red_w], 0), 1), 0.8, 1.25)
        bw[..., :3] = np.clip(bw[..., :3] * k, 0, 255)
    a_b = bc[..., 3:4] / 255 * fade[..., None]
    a_w = bw[..., 3:4] / 255
    rgb = bc[..., :3] * a_b + bw[..., :3] * a_w * (1 - a_b)
    al = a_b + a_w * (1 - a_b)
    out = np.dstack([np.where(al > 1e-3, rgb / np.maximum(al, 1e-3), 0), al * 255])
    return out, (cx0, cy0)


def main():
    meta = json.load(open("build/parts/meta.json"))
    sheet = np.asarray(Image.open(SHEET).convert("L")).astype(np.float32)
    rest = np.asarray(Image.open("build/parts/mg_l_rest.png").convert("RGBA")).astype(np.float32)
    orx, ory = meta["mg_l_rest"]["off"]
    H, W = rest.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # sheet coords of every neutral-bust pixel
    sx_, sy_ = xx / 4 + orx, yy / 4 + ory
    r = np.sqrt(((sx_ - MC[0]) / MR[0]) ** 2 + ((sy_ - MC[1]) / MR[1]) ** 2)
    feather = FEATHER / min(MR)
    mask = np.clip((1 - r) / feather, 0, 1)
    mask = mask * mask * (3 - 2 * mask)
    ring = (r > 1.05) & (r < 1.45) & (rest[..., 3] > 250)
    up = (sy_ > 92) & (sy_ < 198) & (sx_ > 92) & (sx_ < 268)
    ys, xs = np.nonzero(up)
    ua, ub, va, vb = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    for i, n in enumerate(NAMES):
        if n == "rest":
            out = rest
        else:
            dx, dy = sheet_shift(sheet, i)
            src = np.asarray(Image.open(f"build/parts/mg_l_{n}.png").convert("RGBA")).astype(np.float32)
            ovx, ovy = meta[f"mg_l_{n}"]["off"]
            T = np.float32([(orx - ovx + dx) * 4, (ory - ovy + dy) * 4])
            A = np.float32([[1, 0, T[0]], [0, 1, T[1]]])
            warped = cv2.warpAffine(src, A, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                    borderMode=cv2.BORDER_REPLICATE)
            # sub-pixel refinement on the upper face
            g0 = rest[ua:ub, va:vb, :3].mean(2); g1 = warped[ua:ub, va:vb, :3].mean(2)
            (rx, ry), _ = cv2.phaseCorrelate(g0, g1, cv2.createHanningWindow(g0.shape[::-1], cv2.CV_32F))
            if abs(rx) < 12 and abs(ry) < 12:
                A = np.float32([[1, 0, T[0] + rx], [0, 1, T[1] + ry]])
                warped = cv2.warpAffine(src, A, (W, H), flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                        borderMode=cv2.BORDER_REPLICATE)
            # colour match on a ring of skin just outside the patch
            k = np.clip(np.median(rest[..., :3][ring], 0) / np.maximum(np.median(warped[..., :3][ring], 0), 1), 0.9, 1.1)
            patch = np.clip(warped[..., :3] * k, 0, 255)
            out = rest.copy()
            out[..., :3] = rest[..., :3] * (1 - mask[..., None]) + patch * mask[..., None]
            print(f"mg_v_{n}: sheet shift ({dx}, {dy}) + ({rx:.2f}, {ry:.2f}) px, colour x{np.round(k, 3)}", flush=True)
        full, (cx0, cy0) = with_body(out, meta)
        Image.fromarray(np.clip(full + 0.5, 0, 255).astype(np.uint8)).save(f"build/parts/mg_v_{n}.png")
        meta[f"mg_v_{n}"] = dict(meta["mg_l_rest"], src="mgvis.py", key=f"mgvis:{n}", off=[cx0, cy0],
                                 size=[full.shape[1], full.shape[0]])
    json.dump(meta, open("build/parts/meta.json", "w"), indent=1)


if __name__ == "__main__":
    main()

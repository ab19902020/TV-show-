"""Precision cut-outs from the (4x) character sheet: soft matte, colour decontamination,
no stray sheet lines, no enclosed background pockets."""
import numpy as np, cv2
from cutout import S, load_sheet, bg_color

def matte(sheet, box, seed, bgc=None, t0=10.0, t1=48.0, keep_radius=14):
    if bgc is None: bgc = bg_color(sheet)
    x0, y0, x1, y1 = [int(v * S) for v in box]
    crop = sheet[y0:y1, x0:x1].astype(np.float32)
    B = bgc.astype(np.float32)
    diff = np.sqrt(((crop - B) ** 2).sum(2))
    h, w = diff.shape
    fg = (diff > (t0 + t1) / 2).astype(np.uint8)
    # background = non-fg connected to the border
    inv = np.pad(1 - fg, 1, constant_values=1)
    ff = inv.copy(); cv2.floodFill(ff, np.zeros((h + 4, w + 4), np.uint8), (0, 0), 2)
    outside = ff[1:-1, 1:-1] == 2
    obj = (~outside).astype(np.uint8)
    # drop thin stray lines / neighbour fragments: opening-by-reconstruction around the seed blob
    op = cv2.morphologyEx(obj, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13)))
    n, lab = cv2.connectedComponents(op, connectivity=8)
    sx, sy = int(seed[0] * S) - x0, int(seed[1] * S) - y0
    core = (lab == lab[sy, sx]).astype(np.uint8)
    reach = cv2.dilate(core, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * keep_radius + 1, 2 * keep_radius + 1)))
    obj = obj & reach
    n, lab = cv2.connectedComponents(obj, connectivity=8)
    obj = (lab == lab[sy, sx]).astype(np.uint8)
    # fill every enclosed hole: grey shading inside the beard/mustache must never turn see-through
    cnts, _ = cv2.findContours(obj, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(obj); cv2.drawContours(filled, cnts, -1, 1, -1)
    region = filled.astype(bool)
    # soft alpha on the boundary band, 1 inside
    band = cv2.dilate(filled, np.ones((5, 5), np.uint8)).astype(bool) & ~cv2.erode(filled, np.ones((5, 5), np.uint8)).astype(bool)
    soft = np.clip((diff - t0) / (t1 - t0), 0, 1)
    alpha = np.where(band, soft, region.astype(np.float32))
    alpha = np.where(cv2.dilate(filled, np.ones((5, 5), np.uint8)).astype(bool), alpha, 0)
    # colour decontamination: remove the grey sheet colour from partially transparent pixels
    a = np.clip(alpha, 1e-3, 1)[..., None]
    col = np.clip((crop - (1 - a) * B) / a, 0, 255)
    col = np.where(alpha[..., None] > 0.02, col, crop)
    rgba = np.dstack([col.astype(np.uint8), (alpha * 255 + 0.5).astype(np.uint8)])
    return rgba, (x0, y0)

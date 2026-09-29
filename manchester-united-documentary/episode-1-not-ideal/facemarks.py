"""Mouth line, chin and eyes of every talking / reacting head (sheet coordinates, 1x).

Semi-automatic: each head gets a rough mouth box and eye boxes (ROUGH, sheet coords). In the mouth box the lips
are the pink pixels (red high, green ~ blue; skin is orange with green well above blue); the mouth line is the
darkest row through the lips' middle, the corners are the lips' left / right extent. In each eye box the eye is the
bright sclera plus dark iris; its centre and size give the blink lid. Results are drawn on build/facemarks_check.jpg;
MANUAL overrides anything the detector misreads.

Output build/facemarks.json {head: {mouth: [xl, yl, xr, yr, xc, yc], lip_top, lip_bot, chin, eyes: [[cx, cy, rx, ry], ...]}}"""
import json, sys, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage
import parts

# rough boxes, sheet coords: mouth (x0, y0, x1, y1), eyes [(x0, y0, x1, y1), ...], chin y
ROUGH = {}
MANUAL = {}
SHEETS = {}

def sheet(src):
    if src not in SHEETS: SHEETS[src] = np.asarray(Image.open(src).convert("RGBA")).astype(np.int32)
    return SHEETS[src]

def mouth_of(img, box):
    x0, y0, x1, y1 = box
    c = img[y0:y1, x0:x1]
    r, g, b, a = c[..., 0], c[..., 1], c[..., 2], c[..., 3]
    pink = (a > 128) & (r > 120) & (r - g > 35) & (g - b < 12)
    pink = ndimage.binary_opening(pink, iterations=1)
    lab, n = ndimage.label(pink)
    if n == 0: return None
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= 0.25 * sizes.max()])
    ys, xs = np.nonzero(keep)
    xl, xr = xs.min(), xs.max()
    xc = int(round((xl + xr) / 2))
    # mouth line: darkest row in the lips' middle third
    lum = c[..., :3].sum(2).astype(np.float32)
    band = lum[:, max(0, xc - (xr - xl) // 6):xc + (xr - xl) // 6 + 1]
    rows = np.nonzero(keep[:, xc])[0]
    top, bot = (rows.min(), rows.max()) if len(rows) else (ys.min(), ys.max())
    prof = band.mean(1)
    lo, hi = max(0, top - 2), min(len(prof), bot + 3)
    yc = lo + int(np.argmin(prof[lo:hi]))
    # corner heights: darkest point near each end
    def corner(x):
        col = lum[:, max(0, x - 1):x + 2].mean(1)
        return int(np.argmin(col[max(0, yc - 6):yc + 7])) + max(0, yc - 6)
    yl, yr = corner(xl + 1), corner(xr - 1)
    return [xl + x0, yl + y0, xr + x0, yr + y0, xc + x0, yc + y0, top + y0, bot + y0]

def eye_of(img, box):
    x0, y0, x1, y1 = box
    c = img[y0:y1, x0:x1]
    r, g, b, a = c[..., 0], c[..., 1], c[..., 2], c[..., 3]
    mx, mn = np.maximum(np.maximum(r, g), b), np.minimum(np.minimum(r, g), b)
    scl = (a > 128) & (mn > 150) & (mx - mn < 60)
    dark = (a > 128) & (mx < 90)
    m = ndimage.binary_closing(scl | dark, iterations=1) & ((scl | dark))
    lab, n = ndimage.label(scl)
    if n == 0: return None
    ys, xs = np.nonzero(scl)
    # iris/pupil = dark pixels between the sclera extents
    xl, xr = xs.min(), xs.max()
    dys, dxs = np.nonzero(dark[:, xl:xr + 1])
    yt = min(ys.min(), (dys.min() if len(dys) else ys.min()))
    yb = max(ys.max(), (dys.max() if len(dys) else ys.max()))
    return [(xl + xr) / 2 + x0, (yt + yb) / 2 + y0, (xr - xl) / 2 + 1, (yb - yt) / 2 + 1]

def run():
    out = {}
    tiles = []
    for h, R in ROUGH.items():
        sp = parts.SPEC[h]; img = sheet(sp["src"])
        m = mouth_of(img, R["mouth"]) if R.get("mouth") else None
        eyes = [eye_of(img, e) for e in R.get("eyes", [])]
        res = dict(mouth=m[:6] if m else None, lip_top=m[6] if m else None, lip_bot=m[7] if m else None,
                   chin=R.get("chin"), eyes=[e for e in eyes if e])
        res.update(MANUAL.get(h, {}))
        out[h] = res
        # check tile
        x0, y0, x1, y1 = R["view"]
        c = img[y0:y1, x0:x1].astype(np.uint8)
        bg = np.zeros_like(c[..., :3]); bg[...] = (90, 90, 90)
        al = c[..., 3:4] / 255.0
        im = Image.fromarray((c[..., :3] * al + bg * (1 - al)).astype(np.uint8))
        k = 420 / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        P = lambda x, y: ((x - x0) * k, (y - y0) * k)
        if res["mouth"]:
            xl, yl, xr, yr, xc, yc = res["mouth"]
            d.line([P(xl, yl), P(xc, yc), P(xr, yr)], fill=(0, 255, 0), width=2)
            if res["chin"]: d.line([P(xc - 10, res["chin"]), P(xc + 10, res["chin"])], fill=(255, 255, 0), width=2)
        for cx, cy, rx, ry in res["eyes"]:
            d.ellipse([P(cx - rx, cy - ry), P(cx + rx, cy + ry)], outline=(0, 255, 255), width=2)
        d.text((4, 4), h, fill=(255, 255, 0))
        tiles.append(im)
    json.dump(out, open("build/facemarks.json", "w"), indent=1, default=float)
    cols = 6
    s = Image.new("RGB", (425 * cols, 425 * ((len(tiles) + cols - 1) // cols)), (30, 30, 30))
    for i, t in enumerate(tiles): s.paste(t, ((i % cols) * 425, (i // cols) * 425))
    s.save("build/facemarks_check.jpg", quality=88)
    return out

if __name__ == "__main__":
    from facemarks_data import ROUGH as R0, MANUAL as M0
    ROUGH.update(R0); MANUAL.update(M0)
    run()

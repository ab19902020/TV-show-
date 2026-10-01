"""Cut every drawing in layout.py out of its sheet.

  python3 cut_parts.py cut [prefix ...]   matte at 1x  -> build/cut1x/<name>.png (RGBA) + build/cut1x/meta.json
  python3 cut_parts.py up  [prefix ...]   4x Real-ESRGAN (anime 6B) of each 1x cut -> build/parts/<name>.png + meta.json

Matte: the paper (light, unsaturated colour connected to the strip's border) is flooded away; white shirts stay because
they are closed in by their own outlines (flat-cut busts get a dam row). The strip is split at the narrowest contacts with
a watershed seeded at each drawing's centre. The mixed edge pixels are eroded by 1 px and the colour bled outwards, so no
paper-coloured fringe survives the upscale."""
import json, os, sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage
from skimage.segmentation import watershed
import layout

ART = "src/art/"
OUT1, OUT4 = "build/cut1x/", "build/parts/"
_sheets = {}


def sheet(key):
    if key not in _sheets:
        _sheets[key] = np.asarray(Image.open(ART + layout.SHEETS[key] + ".png").convert("RGB")).copy()
    return _sheets[key]


def paper_like(rgb):
    mn, mx = rgb.min(2), rgb.max(2)
    return (mn > 178) & ((mx.astype(np.int16) - mn) < 45)


def _segment(crop, cents, dams):
    pl = paper_like(crop)
    for yb, xa, xb in dams:
        pl[yb + 1:yb + 3, xa:xb + 1] = False
    lab, n = ndimage.label(pl)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    fg = ndimage.binary_fill_holes(~bg)
    for yb, xa, xb in dams:                         # remove the dam rows again
        fg[yb + 1:, xa:xb + 1] = False
    fg = ndimage.binary_opening(fg, iterations=1)
    dist = ndimage.distance_transform_edt(fg)
    mk = np.zeros(fg.shape, np.int32)
    H, W = fg.shape
    for i, (n_, cx, cy) in enumerate(cents):
        cx, cy = int(cx), int(cy)
        R = 24
        y0_, y1_, x0_, x1_ = max(0, cy - R), min(H, cy + R + 1), max(0, cx - R), min(W, cx + R + 1)
        win = dist[y0_:y1_, x0_:x1_]
        if win.max() > 2:                           # a deep interior point close to the estimate
            yy, xx = np.mgrid[y0_:y1_, x0_:x1_]
            score = win - 0.12 * np.hypot(yy - cy, xx - cx)
            k = np.unravel_index(np.argmax(score), win.shape); cy, cx = y0_ + k[0], x0_ + k[1]
        else:
            idx = ndimage.distance_transform_edt(~fg, return_indices=True)[1]; cy, cx = idx[0][cy, cx], idx[1][cy, cx]
        cv2.circle(mk, (int(cx), int(cy)), 4, i + 1, -1)
    return watershed(-dist, mk, mask=fg)


def cut_strip(st):
    img = sheet(st["sheet"])
    H, W = img.shape[:2]
    xs = [c[1] for c in st["items"]]
    x0, x1 = max(0, min(xs) - 140), min(W, max(xs) + 140)
    y0, y1 = st["y0"], st["y1"]
    crop = img[y0:y1, x0:x1]
    cents = [(n, cx - x0, cy - y0) for n, cx, cy in st["items"]]
    ws = _segment(crop, cents, [])
    if st["flat"]:                                  # per-drawing dam from the first pass, then again
        dams = []
        for i in range(len(cents)):
            ys, xs_ = np.nonzero(ws == i + 1)
            if len(ys) == 0: continue
            yb = ys.max()
            band = (ws == i + 1)[max(0, yb - 4):yb + 1]
            cols = np.nonzero(band.any(0))[0]
            dams.append((yb, cols.min(), cols.max()))
        ws = _segment(crop, cents, dams)
    out = {}
    for i, (n_, cx, cy) in enumerate(cents):
        m = ws == i + 1
        if not m.any(): print("EMPTY", n_); continue
        ys, xs_ = np.nonzero(m)
        bx0, bx1, by0, by1 = max(0, xs_.min() - 4), min(m.shape[1], xs_.max() + 5), max(0, ys.min() - 4), min(m.shape[0], ys.max() + 5)
        mm = m[by0:by1, bx0:bx1]
        rgb = crop[by0:by1, bx0:bx1].copy()
        core = ndimage.binary_erosion(mm, iterations=1)
        idx = ndimage.distance_transform_edt(~core, return_indices=True)[1]
        rgb = rgb[idx[0], idx[1]]
        a = (core * 255).astype(np.uint8)
        out[n_] = (np.dstack([rgb, a]), (x0 + bx0, y0 + by0))
    return out


def main_cut(prefixes):
    os.makedirs(OUT1, exist_ok=True)
    meta = json.load(open(OUT1 + "meta.json")) if os.path.exists(OUT1 + "meta.json") else {}
    for st in layout.STRIPS:
        names = [c[0] for c in st["items"]]
        if prefixes and not any(n.startswith(p) for n in names for p in prefixes): continue
        for n, (rgba, off) in cut_strip(st).items():
            Image.fromarray(rgba).save(OUT1 + n + ".png")
            meta[n] = dict(off=[int(off[0]), int(off[1])], size=[int(rgba.shape[1]), int(rgba.shape[0])], sheet=st["sheet"])
        print("cut", names[0], "...", len(names), flush=True)
    json.dump(meta, open(OUT1 + "meta.json", "w"), indent=1)


def smooth(a, lo, hi):
    t = np.clip((a.astype(np.float32) - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


def main_up(prefixes):
    import upscale
    os.makedirs(OUT4, exist_ok=True)
    m1 = json.load(open(OUT1 + "meta.json"))
    m4 = json.load(open(OUT4 + "meta.json")) if os.path.exists(OUT4 + "meta.json") else {}
    for n, info in m1.items():
        if prefixes and not any(p in n for p in prefixes): continue
        src = OUT1 + n + ".png"
        key = f"{os.path.getmtime(src):.0f}"
        if os.path.exists(OUT4 + n + ".png") and m4.get(n, {}).get("key") == key: continue
        im = np.asarray(Image.open(src))
        rgb, a = np.ascontiguousarray(im[..., :3]), im[..., 3]
        big = upscale.upscale(rgb, "RealESRGAN_x4plus_anime_6B")
        A = cv2.resize(a.astype(np.float32) / 255, (a.shape[1] * 4, a.shape[0] * 4), interpolation=cv2.INTER_CUBIC)
        A = cv2.GaussianBlur(np.clip(A, 0, 1), (0, 0), 1.3)
        A = smooth(A * 255, 70, 185)
        out = np.dstack([big, (A * 255 + 0.5).astype(np.uint8)])
        ys, xs = np.nonzero(out[..., 3] > 0)
        t, b, l, r = max(0, ys.min() - 4), ys.max() + 5, max(0, xs.min() - 4), xs.max() + 5
        out = out[t:b, l:r]
        Image.fromarray(out).save(OUT4 + n + ".png")
        m4[n] = dict(off=[info["off"][0] + l / 4, info["off"][1] + t / 4], scale=4, size=[out.shape[1], out.shape[0]], key=key)
        json.dump(m4, open(OUT4 + "meta.json", "w"), indent=1)
        print("up", n, out.shape, flush=True)


def main_up8(prefixes):
    """8x for the parts shown big (waist-up poses in close shots): 1x -> bicubic 2x -> Real-ESRGAN 4x"""
    import upscale
    os.makedirs(OUT4, exist_ok=True)
    m1 = json.load(open(OUT1 + "meta.json"))
    m4 = json.load(open(OUT4 + "meta.json")) if os.path.exists(OUT4 + "meta.json") else {}
    for n, info in m1.items():
        if not any(n.startswith(p) for p in prefixes): continue
        src = OUT1 + n + ".png"
        key = f"8x:{os.path.getmtime(src):.0f}"
        if os.path.exists(OUT4 + n + ".png") and m4.get(n, {}).get("key") == key: continue
        im = np.asarray(Image.open(src))
        rgb, a = np.ascontiguousarray(im[..., :3]), im[..., 3]
        rgb2 = cv2.resize(rgb, (rgb.shape[1] * 2, rgb.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
        big = upscale.upscale(np.ascontiguousarray(rgb2), "RealESRGAN_x4plus_anime_6B")
        A = cv2.resize(a.astype(np.float32) / 255, (a.shape[1] * 8, a.shape[0] * 8), interpolation=cv2.INTER_CUBIC)
        A = cv2.GaussianBlur(np.clip(A, 0, 1), (0, 0), 2.4)
        A = smooth(A * 255, 70, 185)
        out = np.dstack([big, (A * 255 + 0.5).astype(np.uint8)])
        ys, xs = np.nonzero(out[..., 3] > 0)
        t, b, l, r = max(0, ys.min() - 8), ys.max() + 9, max(0, xs.min() - 8), xs.max() + 9
        out = out[t:b, l:r]
        Image.fromarray(out).save(OUT4 + n + ".png")
        m4[n] = dict(off=[info["off"][0] + l / 8, info["off"][1] + t / 8], scale=8, size=[out.shape[1], out.shape[0]], key=key)
        json.dump(m4, open(OUT4 + "meta.json", "w"), indent=1)
        print("up8", n, out.shape, flush=True)


if __name__ == "__main__":
    mode, pre = sys.argv[1], sys.argv[2:]
    {"cut": main_cut, "up": main_up, "up8": main_up8}[mode](pre)

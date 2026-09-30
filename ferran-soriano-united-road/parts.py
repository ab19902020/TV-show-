"""Cut every drawing out of the three Soriano sheets using the sheets' own transparency, and upscale it.

The sheets are RGBA: every drawing is already cut out (alpha ~253 inside, a soft rim of low-alpha glow pixels
around it). The matte is that alpha; nothing is keyed out of a background. Labels ("PALMS UP EXPLAINING", "A",
"REST" ...) are separate blobs outside each drawing's box and are dropped.

Edge pixels: the semi-transparent rim carries the dark glow painted behind the figures, so every pixel that is not
solid takes the colour of the nearest solid pixel before upscaling (no dark or reddish fringe on a light wall).

Upscaling: Real-ESRGAN x4plus (keeps the painted texture of skin and hair). The eight gesture drawings are small on
their sheet but seen close (camera C is a head-and-shoulders shot of a 1080x1920 frame), so they get a second pass
(16x) and an area downsample to 8x, which keeps the ink lines crisp.

Output: build/parts/<name>.png (RGBA) + build/parts/meta.json {name: {src, box, off, scale, size}}: sheet pixel
(x, y) maps to part pixel ((x - off_x) * scale, (y - off_y) * scale)."""
import json, os, sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage

GEN, ANI = "RealESRGAN_x4plus", "RealESRGAN_x4plus_anime_6B"
SPEC = {}
def part(name, src, box, x=4, model=GEN, model2=ANI):
    SPEC[name] = dict(src=src, box=box, x=x, model=model, model2=model2)

# ---- gesture sheet: the eight poses (G01-G08), boxes = each drawing's own blob, labels below are left out ----
G = "src/gestures.png"
for n, b in dict(g01=(31, 9, 420, 423), g02=(429, 8, 868, 421), g03=(878, 8, 1254, 429), g04=(1270, 9, 1653, 421),
                 g05=(25, 462, 404, 891), g06=(487, 462, 808, 890), g07=(878, 462, 1249, 891),
                 g08=(1284, 462, 1663, 891)).items():
    part(n, G, b, x=8)
# ---- main sheet: the big waist-up drawing (its head is the master head), two alternative faces, six mouths ----
M = "src/main.png"
part("main", M, (11, 8, 865, 941))
part("face_brow", M, (883, 37, 1176, 420))       # one brow raised, eyes up and to his right
part("face_shut", M, (1263, 37, 1553, 419))      # eyes closed
for n, b in dict(A=(916, 476, 1076, 630), E=(1146, 492, 1343, 629), I=(1409, 505, 1614, 609),
                 O=(924, 696, 1080, 861), U=(1177, 727, 1327, 852), REST=(1405, 727, 1621, 831)).items():
    part("mouth_" + n, M, b)
# ---- arms + hands sheet: 6 arms per side (hanging, palm up, index up, palm forward, pointing, flat hand) and 6
#      hands per side (relaxed, open palm, palm up, pointing, pinch, fist) ----
H = "src/arms.png"
ARMS = ["hang", "palmup", "index", "stop", "point", "flat"]
for side, row in (("a", [(97, 11, 209, 372), (305, 11, 532, 252), (569, 8, 742, 240), (868, 11, 1045, 242),
                         (1120, 9, 1389, 232), (1445, 9, 1623, 252)]),
                  ("b", [(182, 317, 276, 632), (314, 315, 549, 558), (593, 307, 761, 541), (843, 307, 1023, 546),
                         (1067, 307, 1351, 532), (1409, 307, 1593, 560)])):
    for n, b in zip(ARMS, row): part(f"arm{side}_{n}", H, b)
HANDS = ["relaxed", "open", "palmup", "point", "pinch", "fist"]
for side, row in (("a", [(108, 639, 257, 771), (366, 610, 523, 769), (609, 659, 818, 747), (887, 628, 1064, 753),
                         (1158, 634, 1300, 767), (1404, 638, 1573, 750)]),
                  ("b", [(98, 785, 254, 926), (346, 772, 502, 933), (595, 808, 807, 897), (880, 782, 1060, 908),
                         (1167, 788, 1315, 916), (1424, 793, 1596, 908)])):
    for n, b in zip(HANDS, row): part(f"hand{side}_{n}", H, b)

PAD = 6

def smooth(a, lo, hi):
    t = np.clip((a.astype(np.float32) - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)

def cut(sp, sheet):
    """-> rgb (edge-bled), alpha (0..1), sheet offset of the crop"""
    x0, y0, x1, y1 = sp["box"]
    H, W = sheet.shape[:2]
    X0, Y0, X1, Y1 = max(0, x0 - PAD), max(0, y0 - PAD), min(W, x1 + PAD), min(H, y1 + PAD)
    c = sheet[Y0:Y1, X0:X1].copy()
    a = smooth(c[..., 3], 40, 225)
    # keep the blobs that belong to this box (a label or a neighbour reaching into the padding is dropped)
    lab, n = ndimage.label(a > 0.35)
    inbox = np.zeros(a.shape, bool); inbox[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = np.zeros(a.shape, bool)
    big = sizes.max() if n else 0
    for i in range(1, n + 1):
        m = lab == i
        if sizes[i - 1] >= max(60, 0.02 * big) and (m & inbox).sum() > 0.6 * sizes[i - 1]:
            keep |= m
    keep = ndimage.binary_fill_holes(keep)
    grow = ndimage.binary_dilation(keep, iterations=2)
    a = np.where(grow, a, 0)
    a = np.where(keep, np.maximum(a, 1.0 * (c[..., 3] > 200)), a)       # holes inside a drawing stay solid
    solid = (c[..., 3] >= 235) & keep
    idx = ndimage.distance_transform_edt(~solid, return_distances=False, return_indices=True)
    rgb = c[..., :3][idx[0], idx[1]]
    return rgb, a, (X0, Y0)

def main(names=None):
    import upscale
    os.makedirs("build/parts", exist_ok=True)
    mp = "build/parts/meta.json"
    meta = json.load(open(mp)) if os.path.exists(mp) else {}
    sheets = {}
    todo = [n for n in SPEC if not names or any(n == p or n.startswith(p) for p in names)]
    for n in todo:
        sp = SPEC[n]
        key = json.dumps([sp["src"], sp["box"], sp["x"], sp["model"], sp["model2"] if sp["x"] == 8 else None, "v1"])
        out = f"build/parts/{n}.png"
        if os.path.exists(out) and meta.get(n, {}).get("key") == key:
            continue
        if sp["src"] not in sheets:
            sheets[sp["src"]] = np.asarray(Image.open(sp["src"]).convert("RGBA")).copy()
        rgb, a, off = cut(sp, sheets[sp["src"]])
        X = sp["x"]
        big = upscale.upscale(np.ascontiguousarray(rgb), sp["model"])
        if X == 8:
            big = upscale.upscale(np.ascontiguousarray(big), sp["model2"])
            big = cv2.resize(big, (a.shape[1] * 8, a.shape[0] * 8), interpolation=cv2.INTER_AREA)
        A = cv2.resize(a, (a.shape[1] * X, a.shape[0] * X), interpolation=cv2.INTER_CUBIC)
        A = smooth(np.clip(A, 0, 1) * 255, 70, 185)
        img = np.dstack([big, (np.clip(A, 0, 1) * 255 + 0.5).astype(np.uint8)])
        ys, xs = np.nonzero(img[..., 3] > 0)
        t, b, l, r = max(0, ys.min() - 8), ys.max() + 9, max(0, xs.min() - 8), xs.max() + 9
        img = img[t:b, l:r]
        Image.fromarray(img).save(out)
        meta[n] = dict(src=sp["src"], box=list(sp["box"]), off=[off[0] + l / X, off[1] + t / X], scale=X,
                       size=[img.shape[1], img.shape[0]], key=key)
        json.dump(meta, open(mp, "w"), indent=1)
        print("cut", n, img.shape, flush=True)

if __name__ == "__main__":
    main(sys.argv[1:] or None)

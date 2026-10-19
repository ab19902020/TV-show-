"""Clean every character sprite and upscale it 4x (Real-ESRGAN anime) -> build/up/<Character>/<Folder>/<name>.png (RGBA).

Cleaning, at native size:
- the drawings are stored at alpha ~253 inside, so they let the set show through: the alpha is re-levelled so the
  inside is solid and the faint outer haze (alpha < ~10) is dropped;
- the sheet labels ("DAVID BRENT", "VIEWS", frame numbers) that came along with some cut-outs are removed: only the
  drawing's own connected pieces are kept;
- the colour of see-through pixels is pushed out from the drawing so the upscaler does not pull a dark rim in.
"""
import sys, os, glob, numpy as np, cv2
from PIL import Image

ART = "src/art"
OUT = "build/up"
CHARS = ["David_Brent", "Gareth_Keenan", "Tim_Canterbury", "Dawn_Tinsley", "Finchy", "Neil_Godwin"]


def clean(rgba):
    rgb = rgba[..., :3].astype(np.float32)
    a = rgba[..., 3].astype(np.float32)
    a = np.clip((a - 10) / (240 - 10), 0, 1)
    # keep the drawing's own pieces: the largest blob plus anything big, or anything touching it
    solid = (a > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(solid, 8)
    if n > 1:
        areas = st[1:, cv2.CC_STAT_AREA]
        big = 1 + int(np.argmax(areas))
        keep = np.zeros(n, bool)
        keep[big] = True
        near = cv2.dilate((lab == big).astype(np.uint8), np.ones((5, 5), np.uint8))
        for i in range(1, n):
            if i == big:
                continue
            if areas[i - 1] > 0.04 * areas[big - 1] or (near[lab == i].any() and areas[i - 1] > 6):
                keep[i] = True
        km = keep[lab] .astype(np.uint8)
        # soft edge pixels belong to the kept piece next to them
        km = cv2.dilate(km, np.ones((3, 3), np.uint8))
        a = a * km
    # bleed colours outwards under transparent pixels
    m = (a > 0.6).astype(np.uint8)
    col = rgb.copy()
    for _ in range(6):
        k = cv2.dilate(m, np.ones((3, 3), np.uint8))
        acc = cv2.blur(col * m[..., None], (3, 3))
        cnt = cv2.blur(m.astype(np.float32), (3, 3))[..., None]
        grow = (k > 0) & (m == 0)
        col[grow] = (acc / np.maximum(cnt, 1e-6))[grow]
        m = k
    col[m == 0] = col[m > 0].mean(0) if m.any() else 0
    return np.clip(col, 0, 255).astype(np.uint8), (a * 255).astype(np.uint8)


def main(only=None):
    from upscale import upscale
    files = []
    for c in CHARS:
        for f in sorted(glob.glob(f"{ART}/{c}/*/*.png")):
            files.append(f)
    if only:
        files = [f for f in files if any(o in f for o in only)]
    for f in files:
        rel = os.path.relpath(f, ART)
        dst = os.path.join(OUT, rel)
        if os.path.exists(dst):
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        rgba = np.asarray(Image.open(f).convert("RGBA"))
        col, a = clean(rgba)
        big = upscale(col)
        al = upscale(np.repeat(a[..., None], 3, 2))[..., 1].astype(np.float32)
        # crisp, but anti-aliased, edge
        al = np.clip((al - 40) / (215 - 40), 0, 1)
        Image.fromarray(np.dstack([big, (al * 255).astype(np.uint8)])).save(dst)
        print(dst, flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or None)

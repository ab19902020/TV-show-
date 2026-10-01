"""Re-derive the alpha of the upscaled parts (4x and 8x), and re-ink their silhouettes: the edge sits ~0.6 sheet px outside the cut core, so the drawing's whole black outline is
kept (cutting through it leaves a dashed edge). The colours outside the core were bled from the outline, so the ring is solid ink."""
import json, sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage

def smooth(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1); return t * t * (3 - 2 * t)

M4 = json.load(open("build/parts/meta.json")); M1 = json.load(open("build/cut1x/meta.json"))
pats = sys.argv[1:]
SKIP = ("prop_",)
for n, m in M4.items():
    if n.startswith(SKIP) or n not in M1 or (pats and not any(n.startswith(p) for p in pats)): continue
    q = int(m.get("scale", 4))
    im = np.asarray(Image.open(f"build/parts/{n}.png")).copy()
    a1 = np.asarray(Image.open(f"build/cut1x/{n}.png"))[..., 3].astype(np.float32) / 255
    l = int(round((m["off"][0] - M1[n]["off"][0]) * q)); t = int(round((m["off"][1] - M1[n]["off"][1]) * q))
    A = cv2.resize(a1, (a1.shape[1] * q, a1.shape[0] * q), interpolation=cv2.INTER_LINEAR)
    A = cv2.GaussianBlur(A, (0, 0), 3.0 * q / 8)
    A = smooth(A, 0.10, 0.42)                       # 0.5 would be the core edge; lower = further out
    A = A[t:t + im.shape[0], l:l + im.shape[1]]
    pad = np.zeros(im.shape[:2], np.float32); pad[:A.shape[0], :A.shape[1]] = A
    im[..., 3] = (pad * 255 + 0.5).astype(np.uint8)
    # re-ink the silhouette: a solid dark line ~0.8 sheet px wide just inside the edge (the drawings' own outline weight)
    ks = 13 if q == 8 else 7
    inner = cv2.erode((pad > 0.5).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (ks, ks)))
    inner = cv2.GaussianBlur(inner.astype(np.float32), (0, 0), 1.6 * q / 8)
    ink = np.clip(pad * (1 - inner), 0, 1)[..., None]
    INK = np.float32([28, 24, 30])
    rgb = im[..., :3].astype(np.float32)
    im[..., :3] = np.clip(rgb * (1 - ink) + INK * ink, 0, 255).astype(np.uint8)
    Image.fromarray(im).save(f"build/parts/{n}.png")
    print("realpha", n)

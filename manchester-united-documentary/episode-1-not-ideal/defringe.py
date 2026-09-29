"""Remove the paper fringe from parts cut off the cream-paper sheets (Maguire's): the anti-aliased pixels between the
black outline and the paper are light and unsaturated, the flood matte keeps them and the upscaler turns them into a
speckled white rim. Peel them off the silhouette edge of the upscaled part (the ink outline becomes the edge again),
drop the paper's light drop shadows under the boots, then soften the edge by a pixel.
Runs once per part (meta.json records it): python3 defringe.py mg_"""
import json, sys, numpy as np, cv2
from PIL import Image


def defringe(rgba, passes=10):
    rgb = rgba[..., :3].astype(np.float32) / 255
    a = rgba[..., 3].astype(np.float32) / 255
    mx, mn = rgb.max(2), rgb.min(2)
    lum = rgb.mean(2)
    light = (lum > 0.52) & (mx - mn < 0.22)
    k = np.ones((3, 3), np.uint8)
    for _ in range(passes):
        bg = (a < 0.5).astype(np.uint8)
        edge = (cv2.dilate(bg, k) > 0) & (bg == 0)
        kill = edge & light
        if not kill.any(): break
        a[kill] = 0
    # isolated specks left behind
    solid = (a > 0.5).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(solid, 8)
    if n > 2:
        big = st[1:, cv2.CC_STAT_AREA].max()
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] < 0.004 * big: a[lab == i] = 0
    a = np.minimum(a, cv2.GaussianBlur(a, (0, 0), 0.9) * 1.15)
    out = rgba.copy()
    out[..., 3] = np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)
    return out


if __name__ == "__main__":
    meta = json.load(open("build/parts/meta.json"))
    for n in [k for k in meta if any(k.startswith(p) for p in sys.argv[1:])]:
        if meta[n].get("defringed"): continue
        im = np.asarray(Image.open(f"build/parts/{n}.png").convert("RGBA"))
        Image.fromarray(defringe(im)).save(f"build/parts/{n}.png")
        meta[n]["defringed"] = True
        print("defringed", n, flush=True)
    json.dump(meta, open("build/parts/meta.json", "w"), indent=1)

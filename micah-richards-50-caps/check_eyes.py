"""check_eyes.py PREFIX -> overlay of detected eyes on the 1x cuts"""
import os as _os
_os.makedirs('build/review', exist_ok=True)
import sys, glob, json, os, numpy as np, cv2
from PIL import Image
S = "build/review/"
E = json.load(open("build/eyes.json")); M = json.load(open("build/cut1x/meta.json"))
pre = sys.argv[1]; cols = int(sys.argv[2]) if len(sys.argv) > 2 else 7; cell = 190
names = [n for n in sorted(E) if pre in n]
rows = (len(names) + cols - 1) // cols
img = np.full((rows * (cell + 14), cols * cell, 3), 255, np.uint8)
for i, n in enumerate(names):
    im = np.asarray(Image.open(f"build/cut1x/{n}.png").convert("RGBA")).astype(np.float32)
    h, w = im.shape[:2]; k = min((cell - 6) / w, (cell - 6) / h)
    a = im[..., 3:4] / 255; rgb = (im[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
    rgb = cv2.resize(rgb, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
    ox, oy = M[n]["off"]
    for cx, cy, rx, ry in E[n]:
        cv2.ellipse(rgb, (int((cx - ox) * k), int((cy - oy) * k)), (max(1, int(rx * k)), max(1, int(ry * k))), 0, 0, 360, (255, 0, 255), 1)
    y0 = (i // cols) * (cell + 14); x0 = (i % cols) * cell
    img[y0 + 14:y0 + 14 + rgb.shape[0], x0 + 3:x0 + 3 + rgb.shape[1]] = rgb
    cv2.putText(img, n + f" {len(E[n])}", (x0 + 2, y0 + 11), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 0), 1, cv2.LINE_AA)
out = S + "eyes_" + pre.strip("_") + ".jpg"; cv2.imwrite(out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88]); print(out)

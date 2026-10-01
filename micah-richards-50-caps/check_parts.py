"""check_parts.py PREFIX [cols] [cell] -> build/review/parts_<prefix>.jpg : cut parts (1x) on magenta in a labelled grid"""
import os as _os
_os.makedirs('build/review', exist_ok=True)
import sys, glob, os, numpy as np, cv2
from PIL import Image
S = "build/review/"
def sheet(prefix, cols=6, cell=220, d="build/cut1x/", bg=(255, 0, 255)):
    files = sorted(f for f in glob.glob(d + prefix + "*.png"))
    rows = (len(files) + cols - 1) // cols
    img = np.zeros((rows * (cell + 16), cols * cell, 3), np.uint8); img[:] = bg
    for i, f in enumerate(files):
        im = np.asarray(Image.open(f).convert("RGBA")).astype(np.float32)
        h, w = im.shape[:2]; k = min((cell - 6) / w, (cell - 6) / h)
        im = cv2.resize(im, (max(1, int(w * k)), max(1, int(h * k))), interpolation=cv2.INTER_AREA)
        a = im[..., 3:4] / 255; rgb = im[..., :3] * a + np.float32(bg) * (1 - a)
        y0 = (i // cols) * (cell + 16); x0 = (i % cols) * cell
        img[y0 + 16:y0 + 16 + rgb.shape[0], x0 + 3:x0 + 3 + rgb.shape[1]] = rgb.astype(np.uint8)
        cv2.putText(img, os.path.basename(f)[:-4], (x0 + 2, y0 + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1, cv2.LINE_AA)
    out = S + f"parts_{prefix}.jpg"; cv2.imwrite(out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88]); return out
if __name__ == "__main__":
    a = sys.argv; print(sheet(a[1], int(a[2]) if len(a) > 2 else 6, int(a[3]) if len(a) > 3 else 220, d=a[4] if len(a) > 4 else "build/cut1x/"))

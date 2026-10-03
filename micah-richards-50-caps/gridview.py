"""gridview.py SHEET x0 y0 x1 y1 [zoom] [step] -> build/review/<name>.jpg : a zoomed crop with a labelled coordinate grid (sheet px)"""
import os as _os
_os.makedirs('build/review', exist_ok=True)
import sys, os, cv2, numpy as np
S = "build/review"
def grid(path, x0, y0, x1, y1, z=2.0, step=50, out=None, bg=None):
    im = cv2.imread(path)
    c = im[y0:y1, x0:x1]
    c = cv2.resize(c, None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC if z > 1 else cv2.INTER_AREA)
    for x in range((x0 // step + 1) * step, x1, step):
        X = int((x - x0) * z)
        cv2.line(c, (X, 0), (X, c.shape[0]), (0, 0, 255) if x % (step * 2) == 0 else (255, 0, 255), 1)
        cv2.putText(c, str(x), (X + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 200), 1, cv2.LINE_AA)
    for y in range((y0 // step + 1) * step, y1, step):
        Y = int((y - y0) * z)
        cv2.line(c, (0, Y), (c.shape[1], Y), (0, 0, 255) if y % (step * 2) == 0 else (255, 0, 255), 1)
        cv2.putText(c, str(y), (2, Y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 0, 200), 1, cv2.LINE_AA)
    out = out or f"{S}/{os.path.basename(path)[:-4]}_{x0}_{y0}.jpg"
    cv2.imwrite(out, c, [cv2.IMWRITE_JPEG_QUALITY, 88]); return out
if __name__ == "__main__":
    a = sys.argv
    p = a[1] if os.path.exists(a[1]) else f"src/art/{a[1]}.png"
    print(grid(p, int(a[2]), int(a[3]), int(a[4]), int(a[5]), float(a[6]) if len(a) > 6 else 2.0, int(a[7]) if len(a) > 7 else 50))

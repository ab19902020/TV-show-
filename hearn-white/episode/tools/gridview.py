"""gridview.py <png> <out.jpg> [x0 y0 x1 y1] [--marks json]: a crop of a drawing (its own px) zoomed so it is
~900 px wide, on grey, with a labelled grid every 10 px (bold every 50) and optional face marks drawn on it
(eyes as ellipses, mouth corners/centre as dots, head box, chin line, neck dot)"""
import sys, json, cv2, numpy as np
args = sys.argv[1:]
marks = None
if "--marks" in args:
    i = args.index("--marks"); marks = json.loads(args[i + 1]); args = args[:i] + args[i + 2:]
src, out = args[0], args[1]
im = cv2.imread(src, cv2.IMREAD_UNCHANGED)
if im.shape[2] == 3:
    im = np.dstack([im, np.full(im.shape[:2], 255, np.uint8)])
H, W = im.shape[:2]
x0, y0, x1, y1 = (int(v) for v in args[2:6]) if len(args) >= 6 else (0, 0, W, H)
c = im[y0:y1, x0:x1].astype(np.float32) / 255
a = c[..., 3:4]
c = c[..., :3] * a + np.float32((0.55, 0.55, 0.55)) * (1 - a)
z = max(1.0, 900.0 / (x1 - x0))
c = cv2.resize((c * 255).astype(np.uint8), None, fx=z, fy=z, interpolation=cv2.INTER_NEAREST if z > 3 else cv2.INTER_CUBIC)
def X(x): return int(round((x - x0) * z))
def Y(y): return int(round((y - y0) * z))
for gx in range((x0 // 10) * 10, x1 + 1, 10):
    if gx < x0: continue
    cv2.line(c, (X(gx), 0), (X(gx), c.shape[0]), (0, 200, 255) if gx % 50 == 0 else (90, 90, 90), 2 if gx % 50 == 0 else 1)
    if gx % 50 == 0: cv2.putText(c, str(gx), (X(gx) + 2, 14), 0, 0.45, (0, 255, 255), 1)
for gy in range((y0 // 10) * 10, y1 + 1, 10):
    if gy < y0: continue
    cv2.line(c, (0, Y(gy)), (c.shape[1], Y(gy)), (0, 200, 255) if gy % 50 == 0 else (90, 90, 90), 2 if gy % 50 == 0 else 1)
    if gy % 50 == 0: cv2.putText(c, str(gy), (2, Y(gy) - 3), 0, 0.45, (0, 255, 255), 1)
if marks:
    for e in marks.get("eyes", []):
        cv2.ellipse(c, (X(e[0]), Y(e[1])), (int(e[2] * z), int(e[3] * z)), 0, 0, 360, (0, 0, 255), 2)
    if marks.get("mouth"):
        m = marks["mouth"]
        for (px, py), col in (((m[0], m[1]), (255, 0, 0)), ((m[2], m[3]), (255, 0, 0)), ((m[4], m[5]), (0, 255, 0))):
            cv2.circle(c, (X(px), Y(py)), 5, col, -1)
    if marks.get("head"):
        h = marks["head"]; cv2.rectangle(c, (X(h[0]), Y(h[1])), (X(h[2]), Y(h[3])), (255, 0, 255), 2)
    if marks.get("chin") is not None:
        cv2.line(c, (0, Y(marks["chin"])), (c.shape[1], Y(marks["chin"])), (255, 255, 0), 1)
    if marks.get("neck"):
        cv2.circle(c, (X(marks["neck"][0]), Y(marks["neck"][1])), 6, (0, 255, 255), -1)
cv2.imwrite(out, c, [cv2.IMWRITE_JPEG_QUALITY, 85])
print(out, c.shape, "zoom", round(z, 2))

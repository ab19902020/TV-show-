"""finegrid.py OUT.jpg sheetkey:x0:y0:x1:y1 [...]  -> zoomed crops with a 5 px grid, stacked (for reading landmarks)"""
import sys, cv2, numpy as np
import layout
def fine(sheet, x0, y0, x1, y1, z=6, step=5):
    sh = cv2.imread(f"src/art/{layout.SHEETS[sheet]}.png")
    c = cv2.resize(sh[y0:y1, x0:x1], None, fx=z, fy=z, interpolation=cv2.INTER_CUBIC)
    for x in range((x0 // step + 1) * step, x1, step):
        X = (x - x0) * z; cv2.line(c, (X, 0), (X, c.shape[0]), (0, 0, 255) if x % 10 == 0 else (255, 0, 255), 1)
        if x % 10 == 0: cv2.putText(c, str(x), (X + 1, 11), 0, 0.36, (0, 0, 160), 1)
    for y in range((y0 // step + 1) * step, y1, step):
        Y = (y - y0) * z; cv2.line(c, (0, Y), (c.shape[1], Y), (0, 0, 255) if y % 10 == 0 else (255, 0, 255), 1)
        if y % 10 == 0: cv2.putText(c, str(y), (1, Y - 2), 0, 0.36, (0, 0, 160), 1)
    return c
tiles = [fine(a.split(":")[0], *map(int, a.split(":")[1:])) for a in sys.argv[2:]]
W = max(t.shape[1] for t in tiles)
tiles = [cv2.copyMakeBorder(t, 0, 6, 0, W - t.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for t in tiles]
cv2.imwrite(sys.argv[1], np.vstack(tiles))

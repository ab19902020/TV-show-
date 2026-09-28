"""Belt line of every torso drawing (the top edge of the belt, and its centre x = the tie tip / buckle):
the first solid dark band below the tie.  BELT_OVERRIDE fixes poses where a hand or arm covers the belt."""
import numpy as np, cv2

BELT_OVERRIDE = {       # name -> (x, y_top) in the drawing's 4x px, read off gridded crops (an arm covers it)
    "HAND ON CHIN": (190.0, 382.0), "ARMS CROSSED": (183.0, 370.0), "EXPLAINING 1": (188.0, 285.0)}

def belt_of(rgba, start=None):
    c = rgba[..., :3].astype(np.int32); a = rgba[..., 3] > 128
    H, W = a.shape
    red = a & (c[..., 2] > 130) & (c[..., 1] < 85) & (c[..., 0] < 90) & (c[..., 2] > c[..., 1] + 90)
    n, lab, st, cen = cv2.connectedComponentsWithStats(red.astype(np.uint8))
    i = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
    ys, xs = np.where(lab == i); ty = ys.max(); tx = float(np.median(xs[ys > ty - 25]))
    dark = a & (c.max(2) < 60)
    frac = dark[:, max(0, int(tx - 40)):int(tx + 40)].mean(1)
    y0 = int(ty - 30) if start is None else start
    for y in range(max(0, y0), H - 3):
        if frac[y:y + 10].min() > 0.5: return tx, float(y)          # a belt is a thick solid band
    return tx, float(H - 1)

def all_belts(P):
    out = {}
    for n, (img, _) in P["arm"].items():
        out[n] = BELT_OVERRIDE.get(n) or belt_of(img)
    return out

if __name__ == "__main__":
    import pickle
    P = pickle.load(open("parts.pkl", "rb"))
    B = all_belts(P)
    tiles = []
    for n, (x, y) in B.items():
        img = P["arm"][n][0]; a = img[..., 3:4] / 255.
        im = (img[..., :3] * a + 235 * (1 - a)).astype(np.uint8)
        cv2.line(im, (0, int(y)), (im.shape[1], int(y)), (0, 255, 0), 2); cv2.circle(im, (int(x), int(y)), 7, (255, 0, 0), -1)
        im = cv2.copyMakeBorder(im, 0, 440 - im.shape[0], 0, max(0, 800 - im.shape[1]), cv2.BORDER_CONSTANT, value=(40, 40, 40))[:, :800]
        cv2.putText(im, n, (5, 432), 0, 0.8, (255, 255, 255), 2); tiles.append(im)
    rows = [np.hstack(tiles[i:i + 6] + [np.full_like(tiles[0], 40)] * (6 - len(tiles[i:i + 6]))) for i in range(0, len(tiles), 6)]
    cv2.imwrite("/tmp/claude-0/-home-user-TV-show-/17c2eb03-f7c3-5c18-9c9e-6908366e9c0f/scratchpad/belts.png",
                cv2.resize(np.vstack(rows), None, fx=0.42, fy=0.42, interpolation=cv2.INTER_AREA))

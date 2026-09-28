"""Anchor points on every torso drawing (4x crop px): the collar point (top of the tie knot, where the head
sits) and the belt buckle (where the legs hang).  Detected automatically; OVERRIDE fixes the few poses where
a hand covers one of them."""
import numpy as np, cv2, pickle

OVERRIDE = {     # name -> {"knot": (x, y), "belt": (x, y)}  read off gridded crops
    "REACH FORWARD": {"knot": (196, 18), "belt": (190, 325)},
    "WAVE": {"knot": (215, 44), "belt": (220, 314)},
    "OK SIGN": {"knot": (190, 22), "belt": (205, 293)},
    "OPEN ARMS": {"knot": (347, 20), "belt": (350, 305)},
    "HAND ON CHIN": {"knot": (190, 25), "belt": (200, 395)},
    "HAND ON HIP": {"knot": (190, 18), "belt": (187, 263)},
    "FINGER UP": {"knot": (190, 22), "belt": (205, 293)},        # made from OK SIGN (extras.py)
}

def red_of(rgba):
    c = rgba[..., :3].astype(np.int32)
    return (rgba[..., 3] > 128) & (c[..., 2] > 130) & (c[..., 1] < 95) & (c[..., 0] < 95) & (c[..., 2] > c[..., 1] + 90)

def detect(rgba):
    H, W = rgba.shape[:2]
    red = red_of(rgba)
    ys, xs = np.where(red)
    # the tie is the red that lies on the torso's centre column; its top rows are the knot
    rows = [y for y in range(H) if red[y].sum() >= 10]
    yk = rows[0]
    xk = float(np.where(red[yk:yk + 40].any(0))[0].mean())
    c = rgba[..., :3].astype(np.int32)
    dark = (rgba[..., 3] > 128) & (c.max(2) < 55)
    # tie column: red pixels connected (loosely) below the knot; its tip x anchors the belt search
    tie = red & (np.abs(np.arange(W)[None, :] - xk) < 70)
    ty, tx = np.where(tie)
    tip_y = ty.max(); tip_x = float(np.median(tx[ty > tip_y - 40]))
    best, yb = -1, None
    for y in range(max(int(H * 0.6), tip_y - 25), H - 4):
        win = dark[y - 5:y + 6, int(tip_x - 45):int(tip_x + 46)]
        cols = win.any(0).sum()                  # a belt is a wide dark band, not a thin outline
        sc = win.sum() * (cols / 91.0) ** 2
        if sc > best: best, yb = sc, y
    band = dark[yb - 5:yb + 6, int(tip_x - 45):int(tip_x + 46)]
    xb = tip_x - 45 + float(np.where(band.any(0))[0].mean()) if band.any() else tip_x
    k = [best]
    return {"knot": (xk, float(yk)), "belt": (xb, float(yb)), "belt_strength": float(k[0]) / 10}

def all_landmarks(P):
    L = {}
    for n, (img, _) in P["arm"].items():
        d = detect(img); d.update(OVERRIDE.get(n, {})); L[n] = d
    return L

if __name__ == "__main__":
    P = pickle.load(open("parts.pkl", "rb"))
    L = all_landmarks(P)
    tiles = []
    for n, d in L.items():
        img = P["arm"][n][0]; a = img[..., 3:4] / 255.0
        im = (img[..., :3] * a + 235 * (1 - a)).astype(np.uint8)
        for key, col in (("knot", (255, 0, 0)), ("belt", (0, 200, 0))):
            x, y = d[key]; cv2.circle(im, (int(x), int(y)), 9, col, -1); cv2.circle(im, (int(x), int(y)), 9, (0, 0, 0), 2)
        im = cv2.copyMakeBorder(im, 0, 440 - im.shape[0], 0, 740 - im.shape[1], cv2.BORDER_CONSTANT, value=(235, 235, 235))
        cv2.putText(im, f"{n} {d['belt_strength']:.0f}", (5, 430), 0, 0.8, (0, 0, 0), 2)
        tiles.append(im)
        print(f"{n:15s} knot {d['knot'][0]:5.0f},{d['knot'][1]:4.0f}  belt {d['belt'][0]:5.0f},{d['belt'][1]:4.0f}  dist {d['belt'][1]-d['knot'][1]:4.0f} str {d['belt_strength']:.0f}")
    rows = [np.hstack(tiles[i:i + 6] + [np.full_like(tiles[0], 235)] * (6 - len(tiles[i:i + 6]))) for i in range(0, len(tiles), 6)]
    cv2.imwrite("landmarks_check.png", cv2.resize(np.vstack(rows), None, fx=0.45, fy=0.45, interpolation=cv2.INTER_AREA))

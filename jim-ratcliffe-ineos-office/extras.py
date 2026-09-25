"""Drawings the sheet doesn't have, made from the ones it does:
  FINGER UP : the OK SIGN arm with the sheet's separate FINGER UP hand swapped in (index raised)
  WATCH     : the FIST pose (forearm across the body) with a gold watch painted on the wrist
and the MOVERS: poses whose hand is cut free so it can chop down / jab at the camera."""
import numpy as np, cv2
K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def skin_of(rgba):
    c = rgba[..., :3].astype(np.int32)
    return (c[..., 2] > c[..., 0] + 45) & (c[..., 2] > 120) & (rgba[..., 3] > 100) & ~((c[..., 1] < 95) & (c[..., 2] > c[..., 1] + 80))

def blob(mask, pick):
    n, lab, st, cen = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    i = pick(st, cen)
    return lab == i

def finger_up(P):
    t = P["arm"]["OK SIGN"][0].copy(); H, W = t.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    sk = skin_of(t) & (yy < 200) & (xx < 140)
    ok = blob(sk, lambda st, c: 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]))
    okm = cv2.dilate(ok.astype(np.uint8), K(6)).astype(bool) & (yy < 200)
    oy, ox = np.where(ok); wy = oy.max(); wx = ox[oy > wy - 14].mean()            # wrist (bottom of the hand)
    # the torso behind the old hand: convex hull of what is left, painted in from the jacket around it
    rest = (t[..., 3] > 128) & ~okm
    hull = cv2.convexHull(cv2.findNonZero(rest.astype(np.uint8)))
    hm = np.zeros((H, W), np.uint8); cv2.fillConvexPoly(hm, hull, 1)
    fillm = okm & hm.astype(bool)
    rgb = cv2.inpaint(np.ascontiguousarray(t[..., :3]), fillm.astype(np.uint8) * 255, 9, cv2.INPAINT_TELEA)
    t[..., :3] = np.where(fillm[..., None], rgb, t[..., :3])
    t[..., 3] = np.where(okm, np.where(fillm, 255, 0), t[..., 3]).astype(np.uint8)
    # the new hand: skin + its outline only (no cuff / sleeve), wrist on the old wrist
    h = P["hand"]["FINGER UP"][0]
    hs = skin_of(h); hy, hx = np.where(hs)
    hmask = cv2.dilate(hs.astype(np.uint8), K(5)).astype(bool) & (h[..., 3] > 0)
    hwy = hy.max(); hwx = hx[hy > hwy - 20].mean()
    s = 0.60
    M = np.float32([[s, 0, wx - s * hwx], [0, s, wy + 8 - s * hwy]])
    hh = h.copy(); hh[..., 3] = (hh[..., 3] * hmask).astype(np.uint8)
    w = cv2.warpAffine(hh, M, (W, H), flags=cv2.INTER_AREA)
    a = w[..., 3:4].astype(np.float32) / 255
    t[..., :3] = (w[..., :3] * a + t[..., :3] * (1 - a)).astype(np.uint8)
    t[..., 3] = np.maximum(t[..., 3], w[..., 3])
    return t

WATCH_AT = (187, 222)        # FIST pose wrist, just past the shirt cuff (4x crop px)

def watch(P):
    t = P["arm"]["FIST"][0].copy()
    x, y = WATCH_AT
    gold, dark = (40, 165, 214), (20, 60, 90)
    band = cv2.boxPoints(((x, y), (20, 58), 0)).astype(np.int32)
    cv2.fillConvexPoly(t, band, (*gold, 255), cv2.LINE_AA)
    cv2.polylines(t, [band], True, (*dark, 255), 2, cv2.LINE_AA)
    cv2.circle(t, (x, y - 4), 17, (*gold, 255), -1, cv2.LINE_AA)
    cv2.circle(t, (x, y - 4), 17, (*dark, 255), 2, cv2.LINE_AA)
    cv2.circle(t, (x, y - 4), 12, (225, 240, 245, 255), -1, cv2.LINE_AA)
    cv2.line(t, (x, y - 4), (x, y - 13), (30, 30, 30, 255), 2, cv2.LINE_AA)
    cv2.line(t, (x, y - 4), (x + 7, y - 2), (30, 30, 30, 255), 2, cv2.LINE_AA)
    cv2.circle(t, (x - 6, y - 10), 3, (240, 250, 255, 255), -1, cv2.LINE_AA)     # glint
    return t

# hand cut free: region (4x crop px of that pose) and the pivot it moves about
MOVERS = {
    "PALM OUT STOP": dict(box=(70, 60, 250, 256), pivot=(105, 235)),      # palm-out hand: chops down
    "REACH FORWARD": dict(box=(255, 10, 400, 185), pivot=(330, 168)),     # pointing hand: jabs at camera
}

def mover_mask(t, box):
    H, W = t.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    x0, y0, x1, y1 = box
    inb = (xx >= x0) & (xx < x1) & (yy >= y0) & (yy < y1)
    sk = skin_of(t) & inb
    hand = blob(sk, lambda st, c: 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]))
    c = t[..., :3].astype(np.int32)
    cuff = (c.min(2) > 185) & inb & cv2.dilate(hand.astype(np.uint8), K(16)).astype(bool)
    m = cv2.dilate((hand | cuff).astype(np.uint8), K(5)).astype(bool) & (t[..., 3] > 0) & inb
    return m

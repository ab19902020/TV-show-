"""Arm hierarchies on the gesture bodies: every separable pose (G01 palms up, G02 shrug, G03 one point, G04 hold on,
G08 dismissive) gets its forearms cut free at the elbow, so a hand can beat, wave, sweep, lower or circle while the
upper arm, shoulder and torso stay put. The compound poses (G05 counting, G06 arms folded, G07 clasped hands) stay
complete drawings, except G05's pointing hand, which is cut free for the counting taps.

A forearm piece = the forearm sleeve from a disc round the elbow to the cuff, plus the cuff and hand (found by
colour: skin, white cuff and their outline, grown from a seed in the palm). It rotates about the elbow (the disc turns
in place, so the joint never opens) and the hand can also tilt about the wrist.

Behind a piece the body is refilled so a moving arm never shows a hole or a second arm: inside the torso and upper
arms the fill is the jumper from G02 (whose chest is all visible), registered into the same body frame; the rest is
painted in from the surrounding jumper. Outside the torso it stays transparent (the set shows between arm and body).

Pivots and polygons are in each pose's gesture-sheet coords.
-> build/rig/<pose>_base.png (body with the pieces removed and refilled), build/rig/<pose>_<side>.png (pieces),
   build/rig/arms.json (pivots in world units and piece origins)"""
import json, numpy as np, cv2
from PIL import Image
from scipy import ndimage

ARMS = {
 "g01": {"R": dict(elbow=(60, 396), wrist=(121, 381), hand=(118, 336),
                   sleeve=[(38, 352), (96, 340), (152, 370), (152, 402), (104, 420), (40, 424)]),
         "L": dict(elbow=(398, 398), wrist=(355, 384), hand=(348, 340),
                   sleeve=[(328, 366), (380, 345), (422, 356), (426, 424), (372, 426), (330, 402)])},
 "g02": {"R": dict(elbow=(468, 404), wrist=(506, 338), hand=(470, 318),
                   sleeve=[(452, 344), (526, 330), (532, 362), (506, 420), (448, 424), (438, 382)]),
         "L": dict(elbow=(832, 404), wrist=(778, 330), hand=(818, 306),
                   sleeve=[(762, 330), (842, 344), (862, 382), (856, 424), (796, 420), (768, 360)])},
 "g03": {"R": dict(elbow=(888, 404), wrist=(940, 283), hand=(957, 244),
                   sleeve=[(898, 270), (970, 278), (976, 330), (930, 420), (878, 426), (875, 380)]),
         "L": dict(elbow=(1230, 404), wrist=(1150, 390), hand=(1092, 386),
                   sleeve=[(1148, 360), (1202, 354), (1252, 386), (1256, 426), (1200, 428), (1148, 420)])},
 "g08": {"R": dict(elbow=(1292, 822), wrist=(1360, 692), hand=(1340, 630),     # the raised, waving hand
                   sleeve=[(1318, 690), (1388, 694), (1382, 740), (1330, 840), (1282, 848), (1284, 780)]),
         "L": dict(elbow=(1648, 862), wrist=(1597, 850), hand=(1545, 850),
                   sleeve=[(1590, 815), (1640, 805), (1668, 845), (1664, 892), (1610, 892), (1592, 870)])},
 "g05": {"R": dict(elbow=(48, 848), wrist=(156, 796), hand=(205, 778),        # the pointing hand (counting)
                   sleeve=[(138, 758), (178, 786), (172, 834), (110, 874), (36, 880), (22, 830), (58, 798)],
                   clip=[(120, 718), (256, 712), (253, 733), (240, 748), (236, 790), (215, 832), (120, 834)])},
 "g04": {"R": dict(elbow=(1300, 404), wrist=(1360, 345), hand=(1378, 292),
                   sleeve=[(1328, 330), (1392, 340), (1386, 382), (1340, 424), (1280, 424), (1284, 380)]),
         "L": dict(elbow=(1626, 404), wrist=(1576, 345), hand=(1556, 292),
                   sleeve=[(1538, 340), (1602, 330), (1642, 380), (1646, 424), (1586, 424), (1546, 382)])},
}
ELBOW_R = 17.0                 # sheet px: radius of the elbow disc (the piece's joint end)

WS = 8

def load_body(n):
    B = json.load(open("build/rig/bodies.json"))
    im = np.asarray(Image.open(f"build/rig/body_{n}.png")).astype(np.float32)
    p = B["poses"][n]
    M = np.vstack([np.float32(p["sheet_to_g07"]), [0, 0, 1]])
    org = np.float32(B["origin_sheet_g07"])
    def s2px(pt):
        """pose sheet -> body png px"""
        q = M @ np.array([pt[0], pt[1], 1.0])
        return ((q[0] - org[0] - p["origin"][0]) * WS, (q[1] - org[1] - p["origin"][1]) * WS)
    def px2w(pt):
        return (pt[0] / WS + p["origin"][0], pt[1] / WS + p["origin"][1])
    return im, s2px, px2w, p

def piece_mask(im, spec, s2px):
    """forearm piece in body png px: sleeve polygon + elbow disc + the hand/cuff component"""
    A = im[..., 3] / 255
    H, W = A.shape
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [np.int32([s2px(p) for p in spec["sleeve"]])], 1)
    ex, ey = s2px(spec["elbow"])
    cv2.circle(m, (int(ex), int(ey)), int(ELBOW_R * WS), 1, -1)
    rgb = im[..., :3]
    mx, mn = rgb.max(2), rgb.min(2)
    skin = (rgb[..., 0] > rgb[..., 2] + 35) & (mx > 90) & (A > 0.5)
    cuff = (mn > 170) & (mx - mn < 60) & (A > 0.5)
    hc = ndimage.binary_closing(skin | cuff, iterations=WS)
    lab, _ = ndimage.label(hc)
    hx, hy = s2px(spec["hand"])
    # the seed's own blob, or the nearest skin/cuff blob if the seed landed between fingers or on a line
    r = int(6 * WS)
    win = lab[int(hy) - r:int(hy) + r + 1, int(hx) - r:int(hx) + r + 1]
    ys, xs = np.nonzero(win)
    assert len(ys), ("no hand near the seed", spec["hand"])
    j = np.argmin((ys - r) ** 2 + (xs - r) ** 2)
    comp = ndimage.binary_fill_holes(lab == win[ys[j], xs[j]])
    if "clip" in spec:                         # the hand touches another drawing (G05's two hands): keep one side
        cm = np.zeros(comp.shape, np.uint8)
        cv2.fillPoly(cm, [np.int32([s2px(p) for p in spec["clip"]])], 1)
        comp &= cm > 0
    near = ndimage.distance_transform_edt(~comp) < 2.4 * WS
    comp = comp | ((mx < 90) & (A > 0.3) & near)
    if "clip" in spec: comp &= cm > 0
    mask = (m > 0) | comp
    return mask & (A > 0.01), comp

def build():
    B = json.load(open("build/rig/bodies.json"))
    out = {}
    # fill sources in world coords: G02 without its forearms, then G07 (for the envelope at the sides)
    srcs = {}
    for n in ("g02", "g07"):
        im, s2px, px2w, p = load_body(n)
        if n == "g02":
            rm = np.zeros(im.shape[:2], bool)
            for side, spec in ARMS["g02"].items():
                rm |= piece_mask(im, spec, s2px)[0]
            im = im.copy(); im[rm, 3] = 0
        srcs[n] = (im, p["origin"])
    for n, sides in ARMS.items():
        im, s2px, px2w, p = load_body(n)
        H, W = im.shape[:2]
        base = im.copy()
        info = {}
        allm = np.zeros((H, W), bool)
        for side, spec in sides.items():
            mask, hand = piece_mask(im, spec, s2px)
            allm |= mask
            piece = im.copy()
            soft = cv2.GaussianBlur(mask.astype(np.float32), (0, 0), 0.6 * WS / 4)
            piece[..., 3] = im[..., 3] * np.clip(soft * 1.2, 0, 1)
            ys, xs = np.nonzero(piece[..., 3] > 0)
            t, b, l, r = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
            Image.fromarray(np.clip(piece[t:b, l:r], 0, 255).astype(np.uint8)).save(f"build/rig/{n}_{side}.png")
            info[side] = {"origin": list(px2w((l, t))), "size": [int(r - l), int(b - t)],
                          "elbow": list(px2w(s2px(spec["elbow"]))), "wrist": list(px2w(s2px(spec["wrist"])))}
        # refill behind the pieces from the sources (resampled into this body's png grid)
        fill = np.zeros((H, W, 4), np.float32)
        for sname in ("g07", "g02"):                      # g02 last: it wins where both have torso
            sim, sorg = srcs[sname]
            T = np.float32([[1, 0, (sorg[0] - p["origin"][0]) * WS], [0, 1, (sorg[1] - p["origin"][1]) * WS]])
            s = cv2.warpAffine(sim, T, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            a = s[..., 3:] / 255
            fill[..., :3] = s[..., :3] * a + fill[..., :3] * (1 - a)
            fill[..., 3:] = np.maximum(fill[..., 3:], s[..., 3:])
        region = allm
        # inside the region: the fill; the envelope (g07's silhouette) decides what is body and what is background
        a_fill = fill[..., 3] / 255
        base[region, :3] = fill[region, :3]
        base[region, 3] = fill[region, 3]
        # any hole left inside the envelope (no source had torso there): paint it from the surrounding jumper
        env = srcs["g07"][0]
        T = np.float32([[1, 0, (srcs["g07"][1][0] - p["origin"][0]) * WS], [0, 1, (srcs["g07"][1][1] - p["origin"][1]) * WS]])
        envA = cv2.warpAffine(env[..., 3], T, (W, H), flags=cv2.INTER_LINEAR) / 255
        hole = region & (envA > 0.5) & (base[..., 3] < 128)
        if hole.any():
            rgb8 = np.clip(base[..., :3], 0, 255).astype(np.uint8)
            base[..., :3] = np.where(hole[..., None], cv2.inpaint(rgb8, hole.astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA), base[..., :3])
            base[hole, 3] = 255
        Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).save(f"build/rig/{n}_base.png")
        out[n] = info
        print("arms", n, {s: v["size"] for s, v in info.items()})
    json.dump(out, open("build/rig/arms.json", "w"), indent=1)

if __name__ == "__main__":
    build()

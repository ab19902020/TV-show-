"""Cut Roy's arms out of the front body drawing into rig pieces: upper arm, forearm, hand (per side),
with pivots and joint caps, and return the torso with the arms removed.  All coords: body crop (4x)."""
import numpy as np, cv2, pickle

BOFF = (48, 128)                          # body crop origin in 4x sheet coords
def B(x, y): return (4 * x - BOFF[0], 4 * y - BOFF[1])     # sheet 1x -> body crop
K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

# sheet-coordinate definitions (measured on the sheet)
ARMS = {
    # image-left arm = Roy's right arm
    "R": dict(side=-1,
              region=[(0, 195), (64, 200), (70, 230), (76, 265), (80, 298), (78, 322), (68, 340), (64, 370),
                      (63, 405), (70, 470), (0, 470)],
              shoulder=(62, 226), elbow=(54, 322), wrist=(42, 407), y_elbow=322, y_wrist=406, r_elbow=21, r_sh=15),
    # image-right arm = Roy's left arm
    "L": dict(side=+1,
              region=[(320, 195), (252, 200), (247, 230), (241, 262), (237, 298), (237, 322), (240, 340), (246, 370),
                      (250, 405), (245, 470), (320, 470)],
              shoulder=(258, 226), elbow=(267, 322), wrist=(271, 407), y_elbow=322, y_wrist=406, r_elbow=20, r_sh=15),
}

def build(body_rgba):
    H, W = body_rgba.shape[:2]
    col = body_rgba[..., :3]; a = body_rgba[..., 3].astype(np.float32) / 255
    out = {}
    arm_all = np.zeros((H, W), bool)
    yy = np.arange(H)[:, None]
    for k, d in ARMS.items():
        poly = np.array([B(x, y) for x, y in d["region"]], np.int32)
        reg = np.zeros((H, W), np.uint8); cv2.fillPoly(reg, [poly], 1)
        reg = reg.astype(bool) & (a > 0.01)
        # the whole hand: skin-coloured pixels around the hand box (plus its outline)
        hx = [x for x, y in d["region"]]
        wx, wy = d["wrist"]
        box = np.zeros((H, W), bool)
        x0, y0 = B(wx - 34, wy - 2); x1, y1 = B(wx + 34, wy + 66)
        box[max(0, y0):y1, max(0, x0):x1] = True
        c32 = col.astype(np.int32)
        skin = (c32[..., 2] > c32[..., 0] + 40) & (c32[..., 2] > 120) & box & (a > 0.2)
        skin = cv2.dilate(skin.astype(np.uint8), K(7)).astype(bool) & box & (a > 0.01)
        reg |= skin
        arm_all |= reg
        ye, yw = B(0, d["y_elbow"])[1], B(0, d["y_wrist"])[1]
        navy = np.median(col[reg & (yy > ye - 200) & (yy < ye) & (col.max(2) < 90)], axis=0)
        def piece(m):
            return np.dstack([col.astype(np.float32), a * m]).astype(np.float32)
        def cap(center, r, outline=True):
            cx, cy = center
            c = np.zeros((H, W, 3), np.float32); c[:] = navy
            disc = np.zeros((H, W), np.float32); cv2.circle(disc, (int(cx), int(cy)), int(r), 1.0, -1, cv2.LINE_AA)
            if outline:
                ring = np.zeros((H, W), np.float32); cv2.circle(ring, (int(cx), int(cy)), int(r) - 3, 1.0, 7, cv2.LINE_AA)
                c = c * (1 - ring[..., None]) + np.float32([22, 18, 20]) * ring[..., None]
            return np.dstack([c, disc]).astype(np.float32)
        # upper arm sits behind the torso: extend it 14px under the torso so the seam never opens
        up = reg & (yy < ye + 16)
        ys_sh = B(*d["shoulder"])[1] + 60
        up_top = up & (yy < ys_sh)                     # sleeve top: must stay inside the original shoulder line
        up = up & (yy >= ys_sh)
        band = cv2.dilate(reg.astype(np.uint8), K(14)).astype(bool) & (a > 0.5) & ~reg & (yy < ye - 40)
        fo = reg & (yy >= ye - 16) & (yy < yw + 4)
        ha = reg & (yy >= yw - 14)
        out[k] = dict(
            upper=piece(up), upper_top=piece(up_top), upper_band=piece(band), fore=piece(fo), hand=piece(ha),
            elbow_cap=cap(B(*d["elbow"]), 4 * d["r_elbow"]),
            shoulder_cap=cap(B(*d["shoulder"]), 4 * d["r_sh"], outline=False),
            shoulder=np.float32(B(*d["shoulder"])), elbow=np.float32(B(*d["elbow"])),
            wrist=np.float32(B(*d["wrist"])), side=d["side"])
    # torso: body minus arms, with a drawn outline along the new side edges
    ta = a * (~arm_all)
    cut = arm_all & ~cv2.erode((~arm_all).astype(np.uint8), K(1)).astype(bool)
    edge = cv2.dilate(arm_all.astype(np.uint8), K(4)).astype(bool) & ~arm_all & (a > 0.5)
    tcol = col.copy()
    tcol[edge] = (tcol[edge] * 0.25 + np.array([22, 18, 20]) * 0.75).astype(np.uint8)
    # arms: outline their inner cut edges too
    for k in out:
        for pn in ("upper", "fore"):
            p = out[k][pn]; al = p[..., 3] > 0.5
            e = al & ~cv2.erode(al.astype(np.uint8), K(4)).astype(bool) & cv2.dilate((ta > 0.5).astype(np.uint8), K(6)).astype(bool)
            p[..., :3][e] = p[..., :3][e] * 0.25 + np.array([22, 18, 20]) * 0.75
    return out, tcol, ta, arm_all

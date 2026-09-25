"""Walking / running rig: a turnaround body (cut at the jacket hem, hands kept) over swappable leg drawings.
Frame = that turnaround drawing's own 4x crop px; the legs are planted on its floor line."""
import numpy as np, cv2, pickle
from rig import graded_premul, classes, K, to3

class Walker:
    def __init__(self, P, view, legs, mirror_legs, cut_y=922, leg_scale=1.52):
        body = P["turn"][view][0]
        H, W = body.shape[:2]
        a = body[..., 3] > 128
        self.floor = float(np.where(a.any(1))[0].max()) - 4
        yy, xx = np.mgrid[0:H, 0:W]
        red, skin, white, grey = classes(body)
        # hands (+ cuffs) hang below the hem: keep them, drop the figure's own legs
        hands = cv2.dilate((skin & (yy > cut_y - 120) & (yy < 1060)).astype(np.uint8), K(9)).astype(bool)
        n, lab, st, _ = cv2.connectedComponentsWithStats(hands.astype(np.uint8))
        hk = np.zeros_like(hands)
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] > 2500: hk |= lab == i
        keep = np.clip((cut_y + 12 - yy) / 24.0, 0, 1)
        keep = np.maximum(keep, cv2.GaussianBlur(hk.astype(np.float32), (0, 0), 2) * (yy < 1060))
        up = body.copy(); up[..., 3] = (up[..., 3] * keep).astype(np.uint8)
        self.upper = graded_premul(up)
        # hip centre: middle of the legs just below the hem
        row = np.where(a[cut_y + 60] & ~hands[cut_y + 60])[0]
        self.hip_x = float((row.min() + row.max()) / 2)
        self.legs = {}
        for ln in legs:
            img = P["leg"][ln][0]
            if mirror_legs: img = img[:, ::-1].copy()
            la = img[..., 3] > 128
            ys = np.where(la.any(1))[0]
            top_row = np.where(la[ys.min() + 8])[0]
            tcx = (top_row.min() + top_row.max()) / 2
            s = leg_scale
            # bottom of the soles on the floor line, top centre under the hip
            M = np.array([[s, 0, self.hip_x - s * tcx], [0, s, self.floor - s * ys.max()]], np.float64)
            self.legs[ln] = (graded_premul(img), M)
        self.body_x = self.hip_x

    def layers(self, leg, bob=0.0, lean=0.0):
        """legs planted; the upper body bobs (rig px, +down) and leans (deg) about the hips."""
        img, M = self.legs[leg]
        hip = (self.hip_x, 900.0)
        R = to3(cv2.getRotationMatrix2D(hip, lean, 1.0))
        T = np.array([[1, 0, 0], [0, 1, bob], [0, 0, 1]], np.float64)
        return [(img, to3(M)), (self.upper, T @ R)]

def build(P):
    return {"in": Walker(P, "3/4 LEFT", ["WALK 1", "WALK 2", "WALK 3", "WALK 4", "STANDING", "TURN LEFT"], True),
            "out": Walker(P, "RIGHT", ["RUN 1", "RUN 2", "RUN 3", "TURN RIGHT", "STANDING"], False)}

if __name__ == "__main__":
    from rig import render_layers
    P = pickle.load(open("parts.pkl", "rb"))
    W = build(P)
    S = "/tmp/claude-0/-home-user-TV-show-/17c2eb03-f7c3-5c18-9c9e-6908366e9c0f/scratchpad/"
    tiles = []
    for key, legs in (("in", ["WALK 1", "WALK 2", "WALK 3", "WALK 4", "TURN LEFT"]), ("out", ["RUN 1", "RUN 2", "RUN 3", "TURN RIGHT"])):
        w = W[key]
        for ln in legs:
            V = np.array([[0.4, 0, 120], [0, 0.4, 10], [0, 0, 1]], float)
            im = render_layers(w.layers(ln), V, (420, 640))
            img = (im[..., :3] + np.float32([150, 175, 150]) * (1 - im[..., 3:4])).astype(np.uint8)
            cv2.line(img, (0, int(0.4 * w.floor + 10)), (420, int(0.4 * w.floor + 10)), (0, 0, 255), 1)
            cv2.putText(img, ln, (5, 630), 0, 0.6, (0, 0, 0), 2)
            tiles.append(img)
    cv2.imwrite(S + "walker.png", np.hstack(tiles))
    print("hip", W["in"].hip_x, W["out"].hip_x, "floor", W["in"].floor, W["out"].floor)

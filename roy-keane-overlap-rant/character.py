"""Roy puppet: body + swappable head drawings + lip-sync mouths + blinks, in body-crop 4x coordinates."""
import numpy as np, cv2, pickle
from collections import OrderedDict
from mouthcomp import composite
from blinks import closed_eye_image
from headcenter import refs

P = pickle.load(open("parts.pkl", "rb")); R = pickle.load(open("align.pkl", "rb"))
def to3(M): return np.vstack([M, [0, 0, 1]])

NECK_X, CHIN_Y, COLLAR_Y = 600, 628, 692       # body-crop 4x landmarks
HX0, HY0, HX1, HY1 = 100, 0, 1100, 860          # head canvas region in body-crop coords
HEADS = ["FRONT", "3/4 RIGHT", "SKEPTICAL", "DISGUSTED", "ANGRY", "SAD", "CONFUSED"]
CHAR_H = 1400                                   # rows of body crop we ever need (table hides the rest)

def _grade(bgr):
    """Match the flat-lit sheet art to the warm, moody studio."""
    f = bgr.astype(np.float32) / 255
    f = f ** 1.06                                # a touch more contrast in the mids
    f *= np.array([0.90, 0.95, 1.02])            # warm (BGR)
    return np.clip(f * 0.97 * 255, 0, 255).astype(np.uint8)

class Roy:
    def __init__(self):
        body, _ = P["body"]
        body = body[:CHAR_H].copy()
        a = body[..., 3].astype(np.float32) / 255
        yy = np.arange(body.shape[0])[:, None].astype(np.float32)
        a *= np.clip((yy - 585) / 14, 0, 1)      # drop the body's own head (new head goes on top)
        self.body = np.dstack([_grade(body[..., :3]), (a * 255).astype(np.uint8)])
        self.M_head = {}
        # Place every head drawing on the neck: its own neck column goes exactly on the FRONT/body neck
        # line (no rotation), its eye+chin lines at the FRONT drawing's height, scale from feature matching.
        rf = refs("FRONT"); self.refs = {"FRONT": rf}
        mid_f = (rf["eye_y"] + rf["chin_y"]) / 2
        for h in HEADS:
            if h == "FRONT":
                M = R["M_fb"]
            else:
                r = refs(h); self.refs[h] = r
                sc = float(np.sqrt(abs(np.linalg.det(R["M_" + h][:, :2]))))
                mid_h = (r["eye_y"] + r["chin_y"]) / 2
                Mhf = np.array([[sc, 0, rf["neck_x"] - sc * r["neck_x"]], [0, sc, mid_f - sc * mid_h]])
                M = (to3(R["M_fb"]) @ to3(Mhf))[:2]
            M = M.copy(); M[0, 2] -= HX0; M[1, 2] -= HY0
            self.M_head[h] = M
        nf = cv2.transform(np.float32([[[rf["neck_x"], rf["chin_y"] + 30]]]), R["M_fb"])[0, 0]
        self.neck_x = float(nf[0])
        # neck fade (in head-canvas coords)
        H, W = HY1 - HY0, HX1 - HX0
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        yb, xb = yy + HY0, xx + HX0
        vert = np.clip((705 - yb) / 60, 0, 1)
        horiz = np.clip((270 - np.abs(xb - NECK_X)) / 70, 0, 1)
        below = np.clip((yb - 600) / 30, 0, 1)
        self.fade = vert * (1 - below * (1 - horiz))
        self.closed = {h: closed_eye_image(h)[0] for h in HEADS}
        # per-head alpha: keep head/beard/neck skin, drop that drawing's own suit + shirt below the ears
        self.head_alpha = {}
        for h in HEADS:
            rgba = P[h][0]
            al = cv2.warpAffine(rgba[..., 3], self.M_head[h], (W, H)).astype(np.float32) / 255
            col = cv2.warpAffine(rgba[..., :3], self.M_head[h], (W, H)).astype(np.int32)
            b, g, r = col[..., 0], col[..., 1], col[..., 2]
            clothes = (b > r + 8)                                  # navy suit + light-blue shirt
            keep = ((~clothes) & (al > 0.5)).astype(np.uint8)
            keep[: 470 - HY0] = (al[: 470 - HY0] > 0.5)
            keep = cv2.morphologyEx(keep, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9)))
            n, lab, st, _ = cv2.connectedComponentsWithStats(keep, connectivity=4)
            big = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])
            keep = (lab == big).astype(np.uint8)
            cnts, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            keep = np.zeros_like(keep); cv2.drawContours(keep, cnts, -1, 1, -1)
            soft = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.6)
            if h == "FRONT":
                self.head_alpha[h] = al * self.fade          # FRONT's collar matches the body: keep it
            else:
                vert = np.clip((690 - (yy + HY0)) / 30, 0, 1)
                self.head_alpha[h] = np.minimum(al, soft) * vert
        self.cache = OrderedDict()

    def head_layer(self, head, vis, eye):
        """eye: 0 open, 1 closed, 0.5 half. Returns float32 RGBA premult canvas (head canvas coords)."""
        key = (head, vis, eye)
        if key in self.cache:
            self.cache.move_to_end(key); return self.cache[key]
        rgba = P[head][0]
        if eye == 0.5:
            o = self.head_layer(head, vis, 0.0); c = self.head_layer(head, vis, 1.0)
            out = o * 0.5 + c * 0.5
        else:
            base = self.closed[head] if eye == 1.0 else rgba[..., :3]
            img = base if vis is None else composite(base, head, vis)
            img = _grade(img)
            W, H = HX1 - HX0, HY1 - HY0
            M = self.M_head[head]
            col = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
            al = self.head_alpha[head]
            out = np.dstack([col * al[..., None], al])
        self.cache[key] = out
        if len(self.cache) > 60: self.cache.popitem(last=False)
        return out

    def compose(self, head, vis, eye, head_M=None, blend=None, body_M=None):
        """Compose full character (premultiplied float RGBA, body-crop coords, CHAR_H rows).
        head_M: 2x3 extra transform for the head canvas (motion), in body coords.
        blend: optional (head2, alpha) cross-dissolve to another head drawing."""
        Hc, Wc = self.body.shape[:2]
        b = self.body.astype(np.float32)
        body = np.dstack([b[..., :3] * (b[..., 3:] / 255), b[..., 3] / 255])
        if body_M is not None:
            body = cv2.warpAffine(body, body_M, (Wc, Hc), flags=cv2.INTER_LINEAR)
        hl = self.head_layer(head, vis, eye)
        if blend is not None:
            h2, t = blend
            hl = hl * (1 - t) + self.head_layer(h2, vis if h2 not in ("3/4 RIGHT",) else "REST" if vis else None, eye) * t
        M = np.array([[1, 0, HX0], [0, 1, HY0]], np.float32)
        if head_M is not None: M = (to3(head_M) @ to3(M))[:2]
        hw = cv2.warpAffine(hl, M, (Wc, Hc), flags=cv2.INTER_LINEAR)
        out = hw + body * (1 - hw[..., 3:4])
        return out

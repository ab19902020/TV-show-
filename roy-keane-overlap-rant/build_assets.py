"""Cut Roy's parts out of the 4x character sheet and register everything to one another.

Outputs:
  parts.pkl        body / head drawings as RGBA cut-outs
  align.pkl        similarity transforms: FRONT head -> body, every other head -> FRONT head
  mouth_align.pkl  the 13 lip-sync mouth crops + transform REST mouth -> each head
"""
import numpy as np, cv2, pickle
from cutout import *
from align_util import sift_similarity
from matte import matte

def on_gray(rgba):
    a = rgba[..., 3:4] / 255.0
    return (rgba[..., :3] * a + 128 * (1 - a)).astype(np.uint8)
def to3(M): return np.vstack([M, [0, 0, 1]])

sheet = load_sheet(); bgc = bg_color(sheet)

# ---------------------------------------------------------------- 1. cut-outs
P = {"body": cutout(sheet, (12, 32, 308, 614), (160, 300), bgc=bgc),
     "FRONT": cutout(sheet, (898, 38, 1124, 283), (1010, 160), bgc=bgc),
     "3/4 LEFT": cutout(sheet, (1122, 38, 1310, 283), (1215, 160), bgc=bgc),
     "3/4 RIGHT": cutout(sheet, (1310, 38, 1522, 283), (1410, 160), bgc=bgc)}
for name, cx in zip(EXPR, EXPR_CX):
    P[name] = cutout(sheet, (max(0, cx - 64), 646, min(1536, cx + 64), 829), (cx, 740), bgc=bgc)
pickle.dump(P, open("parts.pkl", "wb"))          # hard masks: used for registration only

# precision mattes (soft, colour-decontaminated edges, no stray sheet lines) used for rendering
P2 = {k: matte(sheet, box, seed, bgc) for k, (box, seed) in {
    "body": ((12, 32, 308, 614), (160, 300)), "FRONT": ((898, 38, 1124, 283), (1010, 160)),
    "3/4 LEFT": ((1122, 38, 1310, 283), (1215, 160)), "3/4 RIGHT": ((1310, 38, 1522, 283), (1410, 160))}.items()}
for name, cx in zip(EXPR, EXPR_CX):
    P2[name] = matte(sheet, (max(0, cx - 64), 646, min(1536, cx + 64), 829), (cx, 740), bgc)
pickle.dump(P2, open("parts2.pkl", "wb"))

# ---------------------------------------------------------------- 2. heads -> body
body, boff = P["body"]; front, foff = P["FRONT"]
bm = np.zeros(body.shape[:2], np.uint8); bm[:190 * S - boff[1]] = 255   # body head region
bm = (bm * (body[..., 3] > 200)).astype(np.uint8)
fm = np.zeros(front.shape[:2], np.uint8); fm[:215 * S - foff[1]] = 255
fm = (fm * (front[..., 3] > 200)).astype(np.uint8)
R = {"M_fb": sift_similarity(on_gray(front), on_gray(body), fm, bm)[0]}
for name in EXPR + ["3/4 RIGHT", "3/4 LEFT"]:
    img, _ = P[name]
    m1 = (img[..., 3] > 200).astype(np.uint8) * 255; m1[int(img.shape[0] * 0.80):] = 0
    m2 = (front[..., 3] > 200).astype(np.uint8) * 255; m2[230 * S - foff[1]:] = 0
    R["M_" + name] = sift_similarity(on_gray(img), on_gray(front), m1, m2, reproj=8.0)[0]
pickle.dump(R, open("align.pkl", "wb"))

# ---------------------------------------------------------------- 3. mouths
mouths = {n: sheet[(MOUTH_Y[0] + 2) * S:(MOUTH_Y[1] - 2) * S, (x0 + 2) * S:(x1 - 2) * S].copy()
          for n, (x0, x1) in zip(MOUTHS, MOUTH_X)}
rest = mouths["REST"]; h0, w0 = rest.shape[:2]
tg = cv2.cvtColor(rest, cv2.COLOR_BGR2GRAY).astype(np.float32)

def global_match(name, scales, rots, D=0.5):
    """Multi-scale/rotation NCC search of the REST mouth inside a head drawing."""
    tx0, tx1, ty0, ty1 = int(w0 * 0.12), int(w0 * 0.88), int(h0 * 0.02), int(h0 * 0.78)
    g = cv2.cvtColor(on_gray(P[name][0]), cv2.COLOR_BGR2GRAY).astype(np.float32)
    gs = cv2.resize(g, None, fx=D, fy=D, interpolation=cv2.INTER_AREA)
    best = (-2, None)
    for s in scales:
        for r in rots:
            cw, ch = int(w0 * s * D) + 2, int(h0 * s * D) + 2
            M2 = cv2.getRotationMatrix2D((w0 / 2, h0 / 2), r, s * D)
            M2[0, 2] += cw / 2 - w0 / 2; M2[1, 2] += ch / 2 - h0 / 2
            t = cv2.warpAffine(tg, M2, (cw, ch))
            sx0, sx1 = int(cw / 2 + (tx0 - w0 / 2) * s * D), int(cw / 2 + (tx1 - w0 / 2) * s * D)
            sy0, sy1 = int(ch / 2 + (ty0 - h0 / 2) * s * D), int(ch / 2 + (ty1 - h0 / 2) * s * D)
            res = cv2.matchTemplate(gs, t[sy0:sy1, sx0:sx1], cv2.TM_CCOEFF_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(res)
            if mv > best[0]:
                Tr = np.array([[1, 0, ml[0] - sx0], [0, 1, ml[1] - sy0], [0, 0, 1]])
                best = (mv, (np.diag([1 / D, 1 / D, 1]) @ Tr @ to3(M2))[:2])
    return best[1]

def local_refine(name, M0, dt=70, ds=0.10, dr=5):
    """Refine a REST-mouth -> head transform with a small scale/rotation/translation search."""
    tx0, tx1, ty0, ty1 = int(w0 * 0.10), int(w0 * 0.90), int(h0 * 0.02), int(h0 * 0.80)
    g = cv2.cvtColor(on_gray(P[name][0]), cv2.COLOR_BGR2GRAY).astype(np.float32)
    best = (-2, M0)
    for s in np.linspace(1 - ds, 1 + ds, 11):
        for r in np.linspace(-dr, dr, 9):
            Mc = (to3(M0) @ to3(cv2.getRotationMatrix2D((w0 / 2, h0 / 2), r, s)))[:2]
            inv = cv2.invertAffineTransform(Mc); inv[:, 2] += dt
            win = cv2.warpAffine(g, inv, (w0 + 2 * dt, h0 + 2 * dt), borderValue=128)
            res = cv2.matchTemplate(win[ty0:ty1 + 2 * dt, tx0:tx1 + 2 * dt], tg[ty0:ty1, tx0:tx1], cv2.TM_CCOEFF_NORMED)
            _, mv, _, ml = cv2.minMaxLoc(res)
            if mv > best[0]:
                best = (mv, (to3(Mc) @ np.array([[1, 0, ml[0] - dt], [0, 1, ml[1] - dt], [0, 0, 1]]))[:2])
    return best[1]

MR = {"FRONT": local_refine("FRONT", global_match("FRONT", np.arange(0.70, 0.95, 0.01), np.arange(-6, 6.1, 1.5)), dt=40, ds=0.06, dr=3)}
for name in [n for n in EXPR if n != "THINKING"] + ["3/4 RIGHT", "3/4 LEFT"]:
    # chain REST->FRONT with FRONT->head as the starting guess, then refine locally
    MR[name] = local_refine(name, (to3(cv2.invertAffineTransform(R["M_" + name])) @ to3(MR["FRONT"]))[:2])
pickle.dump({"mouths": mouths, "M_rest_to": MR}, open("mouth_align.pkl", "wb"))
print("assets built")

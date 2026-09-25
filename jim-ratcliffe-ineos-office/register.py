"""Register the expression heads into the rig frame (the FRONT turnaround body, 4x crop px) -> reg.pkl
  expression head -> NEUTRAL head -> FRONT head   (SIFT + RANSAC similarity: same face, different drawing)
The arm-pose torsos share almost no SIFT features, so they are registered by anchor points instead
(landmarks.py: tie knot + belt buckle), and the heads are finally pinned by their own tie knot (rig.py)."""
import numpy as np, cv2, pickle
from align_util import sift_similarity, to3

P = pickle.load(open("parts.pkl", "rb"))
def on_gray(rgba, g=128):
    a = rgba[..., 3:4] / 255.0
    return (rgba[..., :3] * a + g * (1 - a)).astype(np.uint8)
def solid(rgba): return (rgba[..., 3] > 200).astype(np.uint8) * 255
K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

FRONT = P["turn"]["FRONT"][0]
HEAD_Y1 = 400          # FRONT rig: head (with collar) is above this

def head_mask(rgba, frac=0.80):
    m = solid(rgba).copy(); m[int(rgba.shape[0] * frac):] = 0; return m

def reg_heads():
    R = {}
    ref = P["head"]["NEUTRAL"][0]
    for n, (img, _) in P["head"].items():
        if n == "NEUTRAL": R[n] = np.eye(3)[:2]; continue
        M, inl, good = sift_similarity(on_gray(img), on_gray(ref), head_mask(img), head_mask(ref), reproj=8.0)
        R[n] = M; print("head", n, inl, good, "scale %.3f" % np.sqrt(abs(np.linalg.det(M[:, :2]))))
    fm = solid(FRONT).copy(); fm[HEAD_Y1:] = 0
    M0, inl, good = sift_similarity(on_gray(ref), on_gray(FRONT), head_mask(ref), fm, reproj=8.0)
    print("NEUTRAL->FRONT", inl, good, "scale %.3f" % np.sqrt(abs(np.linalg.det(M0[:, :2]))))
    return {n: (to3(M0) @ to3(M))[:2] for n, M in R.items()}

if __name__ == "__main__":
    reg = {"head": reg_heads()}
    pickle.dump(reg, open("reg.pkl", "wb"))

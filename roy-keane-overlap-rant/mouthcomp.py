import numpy as np, cv2, pickle
from cutout import MOUTHS
MA = pickle.load(open("mouth_align.pkl", "rb")); mouths = MA["mouths"]; MR = MA["M_rest_to"]
def to3(M): return np.vstack([M, [0, 0, 1]])
REST = mouths["REST"]; h0, w0 = REST.shape[:2]

# per-crop registration to REST (crops come from a grid and may be offset by a few px)
def reg_to_rest(img):
    g1 = cv2.cvtColor(REST, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    g2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255
    m = np.zeros((h0, w0), np.uint8)
    m[: int(h0 * 0.14), int(w0 * 0.2):int(w0 * 0.8)] = 255     # under-nose band
    m[int(h0 * 0.70):int(h0 * 0.95), int(w0 * 0.1):int(w0 * 0.9)] = 255  # beard/chin band
    hh, ww = g2.shape
    g2p = cv2.copyMakeBorder(g2, 0, max(0, h0 - hh), 0, max(0, w0 - ww), cv2.BORDER_REPLICATE)[:h0, :w0]
    W = np.eye(2, 3, dtype=np.float32)
    try:
        _, W = cv2.findTransformECC(g1, g2p, W, cv2.MOTION_TRANSLATION,
                                    (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-6), m, 5)
    except cv2.error:
        pass
    # W maps REST coords -> img coords; we want img -> REST
    return cv2.invertAffineTransform(W)
REG = {k: reg_to_rest(v) for k, v in mouths.items()}

def mouth_mask(big=False):
    m = np.zeros((h0, w0), np.float32)
    ax = (0.36 * w0, 0.34 * h0) if big else (0.33 * w0, 0.29 * h0)
    cv2.ellipse(m, (int(0.5 * w0), int(0.40 * h0)), (int(ax[0]), int(ax[1])), 0, 0, 360, 1, -1)
    return cv2.GaussianBlur(m, (0, 0), 0.06 * w0)
MASK = mouth_mask(); MASK_BIG = mouth_mask(True)

def composite(head_bgr, head_name, vis, big=False, extra=None):
    """Paste mouth shape `vis` onto head image (BGR, head's own crop coords)."""
    H, W = head_bgr.shape[:2]
    M = to3(MR[head_name]) @ to3(REG[vis])
    if extra is not None: M = to3(extra) @ M
    M = M[:2]
    src = mouths[vis]
    patch = cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
    mk = cv2.warpAffine(MASK_BIG if big else MASK, (to3(MR[head_name]))[:2] if extra is None else (to3(extra) @ to3(MR[head_name]))[:2], (W, H))
    # colour match on the feather ring
    ring = (mk > 0.15) & (mk < 0.7)
    hb = head_bgr.astype(np.float32)
    if ring.sum() > 50:
        gain = (hb[ring].mean(0) + 1) / (patch[ring].mean(0) + 1)
        patch *= np.clip(gain, 0.85, 1.18)
    out = hb * (1 - mk[..., None]) + patch * mk[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)

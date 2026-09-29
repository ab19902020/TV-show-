"""Blinks for the expression heads (the sheet has no closed-eye drawings): a skin-coloured lid, sampled from
just above each eye, slides over it with the closed-lid line drawn in the artwork's outline colour."""
import numpy as np, cv2
from layout import MOUTH_CX, MOUTH_CY, S

_ox, _oy = MOUTH_CX["REST"] - 92, MOUTH_CY["REST"] - 128
REST_EYES = [((75 - _ox) * S, (167 - _oy) * S), ((125 - _ox) * S, (167 - _oy) * S)]

def eyes_of(raw, M):
    """eye centres + sizes in the head drawing: the mapped REST eye snapped to the dark lash/pupil blob."""
    out = []
    g = raw[..., :3].max(2).astype(np.float32)
    s = float(np.sqrt(abs(np.linalg.det(M[:, :2]))))
    for ex, ey in REST_EYES:
        x, y = M @ np.array([ex, ey, 1.0])
        r = int(34 * s / 0.6)
        x0, y0 = int(x - r), int(y - r * 0.5)
        win = g[y0:y0 + int(r * 1.5), x0:x0 + 2 * r]
        dark = win < np.percentile(win, 12)
        ys, xs = np.where(dark)
        cx, cy = x0 + xs.mean(), y0 + ys.mean()
        w = max(18.0, min(2.0 * r, np.percentile(xs, 95) - np.percentile(xs, 5) + 10))
        out.append((cx, cy, w * 0.55, w * 0.34))
    return out

def apply(col, eyes, amount):
    """amount: 0 open .. 1 closed.  col: HxWx3 uint8 (straight colour)."""
    if amount <= 0: return col
    out = col.astype(np.float32)
    H, W = col.shape[:2]
    for cx, cy, rx, ry in eyes:
        # lid colour: skin just above the eye
        y0, y1 = int(cy - ry * 3.2), int(cy + ry * 2.6); x0, x1 = int(cx - rx * 1.3), int(cx + rx * 1.3)
        patch = col[max(0, y0):y1, max(0, x0):x1].reshape(-1, 3).astype(np.int32)
        ok = (patch[:, 2] > patch[:, 0] + 45) & (patch.max(1) > 150)          # lit skin only (no brow / lashes)
        skin = np.median(patch[ok] if ok.sum() > 20 else patch, axis=0).astype(np.float32) * 0.94
        m = np.zeros((H, W), np.float32)
        top = cy - ry * 1.25
        bot = top + (ry * 2.35) * amount
        cv2.ellipse(m, (int(cx), int((top + bot) / 2)), (int(rx * 0.98), max(1, int((bot - top) / 2))), 0, 0, 360, 1, -1, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), 1.6)
        yy = np.arange(H, dtype=np.float32)[:, None]
        crease = np.clip(1 - (yy - top) / max(1.0, bot - top), 0, 1) ** 2 * 0.16      # shaded top of the lid
        lid = skin[None, None, :] * (1 - crease[..., None])
        out = out * (1 - m[..., None]) + lid * m[..., None]
        if amount > 0.6:          # closed-lid line
            ln = np.zeros((H, W), np.float32)
            cv2.ellipse(ln, (int(cx), int(bot - ry * 0.35)), (int(rx * 0.95), int(ry * 0.45)), 0, 10, 170, 1, max(2, int(ry * 0.22)), cv2.LINE_AA)
            ln = cv2.GaussianBlur(ln, (0, 0), 0.8)
            out = out * (1 - ln[..., None]) + np.float32([40, 34, 42]) * ln[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)

def schedule(total, fps=30, seed=7):
    """blink start frames: every 2.4-5.2 s"""
    rng = np.random.default_rng(seed); t = 1.2; out = []
    while t < total:
        out.append(int(t * fps)); t += rng.uniform(2.4, 5.2)
    return out

def amount_at(i, starts):
    for s in starts:
        d = i - s
        if 0 <= d < 4: return [0.55, 1.0, 1.0, 0.45][d]
    return 0.0

BLINKERS = {"NEUTRAL", "SMILE", "SAD", "WORRIED", "RAISED BROW", "DISGUSTED", "CONFUSED"}

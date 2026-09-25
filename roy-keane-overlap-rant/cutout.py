"""Cut character parts out of the (4x upscaled) character sheet."""
import numpy as np, cv2
S = 4
EXPR = ["NEUTRAL", "HAPPY", "LAUGHING", "SMILING", "ANGRY", "SPEAKING", "SHOUTING",
        "SURPRISED", "CONFUSED", "SKEPTICAL", "DISGUSTED", "THINKING", "SAD"]
EXPR_CX = [66, 180, 299, 414, 525, 647, 766, 887, 1008, 1122, 1236, 1359, 1472]
MOUTHS = ["A", "E", "I", "O", "U", "FV", "L", "MBP", "SZ", "CDGK", "TH", "WQ", "REST"]
MOUTH_X = [(10, 120), (126, 235), (242, 350), (356, 466), (472, 581), (588, 698), (704, 812),
           (818, 927), (933, 1044), (1050, 1164), (1170, 1284), (1291, 1405), (1411, 1526)]
MOUTH_Y = (895, 980)

def load_sheet():
    return cv2.imread("src/sheet_x4.png", cv2.IMREAD_COLOR)

def bg_color(sheet):
    reg = sheet[600 * S:640 * S, 320 * S:880 * S].reshape(-1, 3)
    return np.median(reg, axis=0)

def cutout(sheet, box, seed, thr=38, bgc=None):
    """box in 1x sheet coords; seed = (x, y) 1x point inside the wanted part.
    Returns (rgba crop at 4x, (x0, y0) offset in 4x coords)."""
    if bgc is None: bgc = bg_color(sheet)
    x0, y0, x1, y1 = [int(v * S) for v in box]
    crop = sheet[y0:y1, x0:x1]
    diff = np.abs(crop.astype(np.int32) - bgc.astype(np.int32)).sum(2)
    fg = (diff > thr).astype(np.uint8)
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # background = not-fg region connected to the crop border
    h, w = fg.shape
    inv = (1 - fg).astype(np.uint8)
    pad = np.pad(inv, 1, constant_values=1)
    ff = pad.copy()
    mask = np.zeros((h + 4, w + 4), np.uint8)
    cv2.floodFill(ff, mask, (0, 0), 2)
    bgm = (ff[1:-1, 1:-1] == 2)
    obj = (~bgm).astype(np.uint8)
    # keep component containing the seed
    n, lab = cv2.connectedComponents(obj, connectivity=4)
    sx, sy = int(seed[0] * S) - x0, int(seed[1] * S) - y0
    obj = (lab == lab[sy, sx]).astype(np.uint8)
    # fill interior holes
    cnts, _ = cv2.findContours(obj, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    filled = np.zeros_like(obj)
    cv2.drawContours(filled, cnts, -1, 1, -1)
    a = cv2.GaussianBlur(filled.astype(np.float32), (0, 0), 0.9)
    rgba = np.dstack([crop, np.clip(a * 255, 0, 255).astype(np.uint8)])
    return rgba, (x0, y0)

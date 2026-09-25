"""Foreground occlusion matte for the INEOS office (4x world coords): everything that must sit in FRONT of Jim.
Hand-traced polygons (1x background coords) are refined with GrabCut in a thin band around their outline,
so the matte edge snaps to the drawing's own black outlines."""
import numpy as np, cv2

S = 4
# the desk and everything on it (books, glass, pen pot, laptop, folder, gold box) + the left foreground armchair
DESK = [(0, 586), (265, 586), (268, 640), (262, 648), (340, 648), (352, 640), (357, 603), (382, 597), (405, 600),
        (420, 640), (440, 643), (700, 645), (760, 648), (850, 650), (950, 649), (1000, 650), (1100, 657),
        (1127, 659), (1160, 663), (1177, 672), (1200, 697), (1220, 727), (1237, 753), (1247, 773), (1253, 797),
        (1257, 817), (1261, 860), (1262, 941), (0, 941)]
# the round side table + book stack + flowers, and the right foreground armchair
SIDE = [(1343, 792), (1345, 772), (1360, 762), (1400, 752), (1440, 749), (1461, 748), (1462, 735), (1470, 713),
        (1482, 692), (1575, 690), (1568, 668), (1563, 645), (1567, 625), (1585, 600), (1610, 577), (1640, 563),
        (1672, 556), (1672, 941), (1330, 941), (1334, 880), (1340, 835)]

def refine(img, poly, band=6, D=2):
    """GrabCut at 1/D of the 4x image inside the polygon's bounding box; unknown = +-band (1x px) around it."""
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    pad = band + 6
    x0, y0 = max(0, min(xs) - pad), max(0, min(ys) - pad)
    x1, y1 = min(img.shape[1] // S, max(xs) + pad), min(img.shape[0] // S, max(ys) + pad)
    f = S / D
    crop = cv2.resize(img[y0 * S:y1 * S, x0 * S:x1 * S], None, fx=1 / D, fy=1 / D, interpolation=cv2.INTER_AREA)
    h, w = crop.shape[:2]
    m = np.zeros((h, w), np.uint8)
    pts = np.array([((x - x0) * f, (y - y0) * f) for x, y in poly], np.int32)
    cv2.fillPoly(m, [pts], 1)
    K = lambda r: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    r = int(band * f)
    gc = np.full((h, w), cv2.GC_BGD, np.uint8)
    gc[cv2.dilate(m, K(r)) > 0] = cv2.GC_PR_BGD
    gc[m > 0] = cv2.GC_PR_FGD
    gc[cv2.erode(m, K(r)) > 0] = cv2.GC_FGD
    # the polygon's straight image-border sides are true borders, not outlines to refine
    bgm, fgm = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(crop, gc, None, bgm, fgm, 6, cv2.GC_INIT_WITH_MASK)
    fg = ((gc == cv2.GC_FGD) | (gc == cv2.GC_PR_FGD)).astype(np.uint8)
    # keep the component(s) overlapping the polygon core, fill holes, smooth the contour
    n, lab = cv2.connectedComponents(fg)
    core = cv2.erode(m, K(r)) > 0
    keep = np.isin(lab, np.unique(lab[core & (fg > 0)]))
    keep &= lab > 0
    cnts, _ = cv2.findContours(keep.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    fill = np.zeros((h, w), np.uint8); cv2.drawContours(fill, cnts, -1, 1, -1)
    fill = cv2.morphologyEx(fill, cv2.MORPH_OPEN, K(2))
    big = cv2.resize(fill.astype(np.float32), ((x1 - x0) * S, (y1 - y0) * S), interpolation=cv2.INTER_LINEAR)
    big = cv2.GaussianBlur(big, (0, 0), 1.2)
    out = np.zeros(img.shape[:2], np.float32)
    out[y0 * S:y1 * S, x0 * S:x1 * S] = big
    return out

if __name__ == "__main__":
    bg = cv2.imread("src/office_x4.png")
    H, W = bg.shape[:2]
    occ = np.maximum(refine(bg, DESK), refine(bg, SIDE))
    # frame edges: the polygons' straight sides along the image border must stay fully opaque
    for poly in (DESK, SIDE):
        hard = np.zeros((H, W), np.uint8)
        cv2.fillPoly(hard, [np.array([(x * S, y * S) for x, y in poly], np.int32)], 1)
        hard = cv2.erode(hard, np.ones((61, 61), np.uint8))
        occ = np.maximum(occ, hard.astype(np.float32))
    cv2.imwrite("src/occlusion_x4.png", np.clip(occ * 255 + 0.5, 0, 255).astype(np.uint8))
    small = cv2.resize(bg, (W // 4, H // 4), interpolation=cv2.INTER_AREA).astype(np.float32)
    a = cv2.resize(occ, (W // 4, H // 4), interpolation=cv2.INTER_AREA)[..., None]
    red = np.zeros_like(small); red[..., 2] = 255
    cv2.imwrite("occlusion_vis.png", (small * (1 - 0.55 * a) + red * 0.55 * a).astype(np.uint8))
    print("occlusion matte built")

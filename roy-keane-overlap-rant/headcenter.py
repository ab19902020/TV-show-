"""Per-drawing anatomical references (crop coords, 4x): skull centre line, chin (beard bottom), neck column."""
import numpy as np, cv2, pickle
import os
P = pickle.load(open(os.environ.get("PARTS", "parts2.pkl"), "rb")); R = pickle.load(open("align.pkl", "rb"))
FRONT_EYES_Y = 151 * 4 - 152
def refs(name):
    img = P[name][0]
    M = np.eye(3)[:2] if name == "FRONT" else cv2.invertAffineTransform(R["M_" + name])
    s = np.sqrt(abs(np.linalg.det(M[:, :2])))
    a = img[..., 3] > 128
    col = img[..., :3].astype(np.int32); b, g, r = col[..., 0], col[..., 1], col[..., 2]
    v = col.max(2); mn = col.min(2)
    # eye line in this drawing
    ey = cv2.transform(np.float32([[[300, FRONT_EYES_Y]]]), M)[0, 0, 1]
    # skull: silhouette extents over rows from eye line down 1/3 of head (ears/cheeks)
    xs_c = []
    for y in range(int(ey - 20 * s), int(ey + 80 * s), 4):
        row = np.where(a[y])[0]
        if len(row): xs_c.append((row.min() + row.max()) / 2)
    skull_x = float(np.median(xs_c))
    # beard: light cream/grey pixels (not shirt-blue), below the eye line
    beard = a & (v > 150) & (r >= b) & ((v - mn) < 90)
    beard[: int(ey + 120 * s)] = False
    beard = cv2.morphologyEx(beard.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(beard)
    i = 1 + np.argmax(st[1:, cv2.CC_STAT_AREA]); bm = lab == i
    ys, xs = np.where(bm)
    chin_y = ys.max()
    low = ys > chin_y - 50 * s
    chin_x = float(xs[low].mean())
    # neck column: skin pixels in the rows just under the chin
    skin = a & (r > b + 45) & (r > 130)
    rows = range(int(chin_y + 5 * s), int(chin_y + 45 * s))
    nx = [np.where(skin[y])[0].mean() for y in rows if skin[y].sum() > 10]
    neck_x = float(np.median(nx)) if nx else chin_x
    return dict(skull_x=skull_x, chin_x=chin_x, chin_y=float(chin_y), neck_x=neck_x, eye_y=float(ey), s=float(s))
if __name__ == "__main__":
    out = {}
    tiles = []
    for name in ["FRONT", "3/4 RIGHT", "SKEPTICAL", "DISGUSTED", "ANGRY", "SAD", "CONFUSED"]:
        d = refs(name); out[name] = d
        print(name, {k: round(v, 1) for k, v in d.items()})
        vis = P[name][0][..., :3].copy()
        H = vis.shape[0]
        cv2.line(vis, (int(d["skull_x"]), 0), (int(d["skull_x"]), H), (0, 0, 255), 3)
        cv2.line(vis, (int(d["neck_x"]), int(d["chin_y"])), (int(d["neck_x"]), H), (0, 255, 0), 3)
        cv2.circle(vis, (int(d["chin_x"]), int(d["chin_y"])), 9, (255, 0, 255), -1)
        h = 400; w = int(vis.shape[1] * h / H)
        tiles.append(cv2.resize(vis, (w, h)))
    pickle.dump(out, open("headrefs.pkl", "wb"))
    cv2.imwrite("headrefs_check.png", np.hstack(tiles))

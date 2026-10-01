import os as _os
_os.makedirs('build/review', exist_ok=True)
import os, sys
os.environ["EP_RES"] = "1080x1920"
import numpy as np, cv2, json
import engine as E, cast, face
names = sys.argv[1:] or ["wr_b_front", "wr_b_q34R", "mr_b_front"]
S = "build/review/"
V = ["REST", "AI", "E", "I", "O", "U", "MBP", "FV", "L", "CDG"]
rows = []
for n in names:
    d = cast.get(n)
    tiles = []
    fa = d._face_at(1.0)
    for v in V:
        st = dict(vis=v, amp=1.0)
        p = d.patch(1.0, st)
        base = d.base(1.0)
        if p is None: img = base.copy()
        else:
            x0, y0, pm = p; img = base.copy()
            h, w = pm.shape[:2]
            reg = img[y0:y0 + h, x0:x0 + w]
            img[y0:y0 + h, x0:x0 + w] = pm + reg * (1 - pm[..., 3:4]) if False else np.where(pm[..., 3:4] > 0, pm, reg)
        rgb = img[..., :3] + (1 - img[..., 3:4]) * np.float32([0.2, 0.45, 0.8])
        # crop to the head
        hx0, hy0, hx1, hy1 = fa["rect"]
        rgb = rgb[hy0:hy1, hx0:hx1]
        rgb = cv2.resize(rgb, (300, int(300 * rgb.shape[0] / rgb.shape[1])), interpolation=cv2.INTER_AREA)
        rgb = np.ascontiguousarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
        cv2.putText(rgb, v, (6, 20), 0, 0.6, (255, 255, 255), 2)
        tiles.append(rgb)
    h = max(t.shape[0] for t in tiles)
    tiles = [np.pad(t, ((0, h - t.shape[0]), (0, 0), (0, 0))) for t in tiles]
    rows.append(np.hstack(tiles[:5])); rows.append(np.hstack(tiles[5:]))
out = np.vstack(rows)
cv2.imwrite(S + "visemes_test.jpg", cv2.cvtColor(out, cv2.COLOR_RGB2BGR))
print("ok", out.shape)

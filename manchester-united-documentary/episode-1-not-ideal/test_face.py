import json, numpy as np, cv2
from PIL import Image
from face import Face
meta = json.load(open("build/parts/meta.json"))
def P(name, x, y):
    ox, oy = meta[name]["off"]; return ((x - ox) * 4, (y - oy) * 4)
n = "ck_b_suit"
img = np.asarray(Image.open(f"build/parts/{n}.png")).astype(np.float32) / 255
L = P(n, 1248, 188); R = P(n, 1300, 183); C = P(n, 1272, 186.5)
e1 = P(n, 1242, 135); e2 = P(n, 1297, 131)
f = Face(img, mouth=(L[0], L[1], R[0], R[1], C[0], C[1]), chin=P(n, 0, 239)[1],
         eyes=[(e1[0], e1[1], 12.5 * 4, 5.5 * 4), (e2[0], e2[1], 12.5 * 4, 5.5 * 4)])
tiles = []
for vis, kw in [("REST", {}), ("AI", {}), ("E", {}), ("O", {}), ("U", {}), ("FV", {}), ("L", {}), ("CDG", {}),
                ("REST", dict(blink=0.6)), ("REST", dict(blink=1.0)), ("REST", dict(look=(1, 0))), ("REST", dict(look=(-1, 0.3))),
                ("REST", dict(brow=1.0)), ("REST", dict(brow=-1.0)), ("AI", dict(amp=1.3)), ("REST", dict(smile=1.0))]:
    out = f.render(vis, **kw)
    x0, y0, x1, y1 = [int(v) for v in (P(n, 1195, 70) + P(n, 1355, 250))]
    c = out[y0:y1, x0:x1]
    bg = np.zeros_like(c[..., :3]); bg[...] = (1, 0, 1)
    im = (c[..., :3] * c[..., 3:4] + bg * (1 - c[..., 3:4]))
    im = cv2.resize((im * 255).astype(np.uint8), None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    cv2.putText(im, f"{vis} {kw}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    tiles.append(im)
rows = [np.hstack(tiles[i:i + 4]) for i in range(0, 16, 4)]
Image.fromarray(np.vstack(rows)).save("build/face_test.jpg", quality=88)
print(np.vstack(rows).shape)

"""Small props that are not on the sheets, drawn here in the same bold-ink style, and the confetti.

  python3 props.py   -> build/parts/prop_phone.png (+ meta): the phone the filming friend holds up (a REC dot, a lens glint)

The film uses the sheets' own cake, 50 CAPS card, balloons, pint and football; only the phone and the confetti are made here."""
import json, math, numpy as np, cv2
from PIL import Image, ImageDraw

P = "build/parts/"


def phone_png():
    S = 4
    W, H = 70 * S, 128 * S
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([2, 2, W - 3, H - 3], radius=12 * S, fill=(18, 18, 22, 255), outline=(8, 8, 10, 255), width=3 * S // 2)
    d.rounded_rectangle([5 * S, 9 * S, W - 5 * S, H - 9 * S], radius=6 * S, fill=(52, 96, 150, 255))
    # screen: a sky-to-floor gradient, a tiny silhouette of people, a REC dot
    for y in range(9 * S, H - 9 * S):
        k = (y - 9 * S) / (H - 18 * S)
        d.line([(5 * S, y), (W - 5 * S, y)], fill=(int(70 + 90 * k), int(120 + 40 * k), int(190 - 40 * k), 255))
    d.ellipse([W // 2 - 9 * S, 60 * S, W // 2 + 9 * S, 78 * S], fill=(30, 30, 40, 255))
    d.rounded_rectangle([W // 2 - 14 * S, 76 * S, W // 2 + 14 * S, 100 * S], radius=6 * S, fill=(30, 30, 40, 255))
    d.ellipse([9 * S, 13 * S, 17 * S, 21 * S], fill=(235, 40, 40, 255))
    d.ellipse([W // 2 - 4 * S, 3 * S, W // 2 + 4 * S, 6 * S], fill=(60, 60, 70, 255))               # camera / speaker slot
    d.line([(9 * S, 24 * S), (W - 9 * S, 24 * S)], fill=(255, 255, 255, 70), width=S)
    # lens glint
    d.polygon([(W - 22 * S, 10 * S), (W - 8 * S, 10 * S), (W - 8 * S, 40 * S), (W - 30 * S, 40 * S)], fill=(255, 255, 255, 38))
    im.save(P + "prop_phone.png")
    meta = json.load(open(P + "meta.json"))
    meta["prop_phone"] = dict(off=[0.0, 0.0], scale=4, size=[W, H], key="x")
    json.dump(meta, open(P + "meta.json", "w"), indent=1)


def confetti(frame, t, seed=1, count=140, area=None, speed=(260, 520), density=1.0):
    """gold / black / cream paper pieces falling through the frame (screen space, float RGB 0..1). area = (x0, y0, x1, y1) px"""
    h, w = frame.shape[:2]
    x0, y0, x1, y1 = area or (0, 0, w, h)
    rng = np.random.default_rng(seed)
    n = int(count * density)
    xs = rng.uniform(x0, x1, n); ph = rng.uniform(0, 1, n); sp = rng.uniform(*speed, n)
    sz = rng.uniform(7, 17, n) * (w / 1080); rot0 = rng.uniform(0, 6.28, n); rv = rng.uniform(-9, 9, n)
    pal = np.float32([[0.93, 0.72, 0.22], [0.98, 0.84, 0.35], [0.08, 0.08, 0.09], [0.97, 0.93, 0.82], [0.80, 0.55, 0.12]])
    ci = rng.integers(0, len(pal), n)
    sway = rng.uniform(20, 60, n); swf = rng.uniform(1.5, 3.5, n)
    im = np.ascontiguousarray((np.clip(frame, 0, 1) * 255).astype(np.uint8))
    for i in range(n):
        y = y0 + ((ph[i] * (y1 - y0) + t * sp[i]) % (y1 - y0))
        x = xs[i] + sway[i] * math.sin(t * swf[i] + ph[i] * 9)
        a = rot0[i] + rv[i] * t
        c, s_ = math.cos(a), math.sin(a)
        wx, wy = sz[i] * (0.5 + 0.5 * abs(math.cos(a * 0.7))), sz[i] * 0.42
        pts = np.float32([[-wx, -wy], [wx, -wy], [wx, wy], [-wx, wy]])
        R = np.float32([[c, -s_], [s_, c]])
        pts = (pts @ R.T) + [x, y]
        col = tuple(int(v * 255) for v in pal[ci[i]])
        cv2.fillConvexPoly(im, pts.astype(np.int32), col, cv2.LINE_AA)
    return im.astype(np.float32) / 255


if __name__ == "__main__":
    phone_png()
    print("prop_phone ok")

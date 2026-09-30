"""The master head: one head for every pose and every camera, cut from the big waist-up drawing on the main sheet.

Using one head everywhere keeps the nose, hairline, head size, outline thickness and eye line identical in all
shots (the gesture drawings each have their own slightly different face; those are removed from the bodies).

The head is the skin + hair blob grown out to its own ink outline, with a neck plug added underneath: shadowed
skin that continues down behind the collar, so the collar of any pose can be drawn in front of it without a gap.
The original mouth is painted out (the mouth rig puts a mouth on every frame).

-> build/rig/head.png (RGBA, 4 px per main-sheet px), build/rig/head_nomouth.png, build/rig/head.json"""
import json, os, numpy as np, cv2
from PIL import Image
from scipy import ndimage

K = 4                                   # head.png px per main-sheet px
# main-sheet landmarks, measured on the 4x part with a coordinate grid
EYES = [(385.5, 196.5), (478.0, 190.5)]      # iris centres (his right eye is frame-left)
MOUTH = (437.0, 305.0)                       # centre of the closed mouth line
MOUTH_W = 83.0                               # corner to corner
CHIN = (440.0, 378.0)
SEED = (430, 230)

def load_main():
    m = json.load(open("build/parts/meta.json"))["main"]
    im = np.asarray(Image.open("build/parts/main.png")).astype(np.float32)
    return im, m["off"], m["scale"]

def classes(rgb, A):
    mx, mn = rgb.max(2), rgb.min(2)
    white = (mn > 170) & (mx - mn < 45) & (A > 0.5)
    dark = (mx < 75) & (A > 0.5)
    return white, dark

def build():
    im, (ox, oy), k = load_main()
    assert k == K
    rgb, A = im[..., :3], im[..., 3] / 255
    P = lambda x, y: (int(round((x - ox) * k)), int(round((y - oy) * k)))
    white, dark = classes(rgb, A)
    skinhair = (A > 0.5) & ~white & ~dark
    lab, _ = ndimage.label(skinhair)
    sx, sy = P(*SEED)
    head = ndimage.binary_fill_holes(lab == lab[sy, sx])
    # grow out to the ink outline (and the dark hair strands by the ears): dark pixels near the blob
    near = ndimage.distance_transform_edt(~head) < 12 * k
    ink = dark & near & ~white
    lab2, _ = ndimage.label(head | ink)
    head = ndimage.binary_fill_holes(lab2 == lab2[sy, sx])
    # the outline stops where the collar starts: nothing below the collar's top edge except the neck plug
    ys, xs = np.nonzero(head)
    # neck plug: under the jaw, down behind the collar, inside the collar's width
    plug = np.zeros(head.shape, np.uint8)
    poly = np.float32([(338, 330), (548, 330), (556, 392), (538, 452), (470, 478), (410, 478), (344, 452), (330, 392)])
    cv2.fillPoly(plug, [np.int32((poly - [ox, oy]) * k)], 1)
    plug = plug.astype(bool) & ~head
    out = np.zeros(im.shape, np.float32)
    out[head] = im[head]
    out[head, 3] = np.clip(A[head] * 255, 0, 255)
    # plug colour: the shadowed skin under the jaw, darker at the top
    yy = np.arange(im.shape[0], dtype=np.float32)[:, None]
    t = np.clip((yy - (330 - oy) * k) / (150 * k), 0, 1)
    top, bot = np.float32([120, 80, 64]), np.float32([176, 124, 96])
    col = top * (1 - t[..., None]) + bot * t[..., None]
    col = np.broadcast_to(col, im.shape[:2] + (3,))
    out[plug, :3] = col[plug]
    out[plug, 3] = 255
    # soft edge where the plug meets the jaw outline: the head's own alpha stays on top
    # crop to the head's box
    a = out[..., 3] > 0
    ys, xs = np.nonzero(a)
    t0, b0, l0, r0 = ys.min() - 8, ys.max() + 9, xs.min() - 8, xs.max() + 9
    out = out[t0:b0, l0:r0]
    off = [ox + l0 / k, oy + t0 / k]                  # main-sheet coords of head.png's (0, 0)
    os.makedirs("build/rig", exist_ok=True)
    Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save("build/rig/head.png")
    H = lambda x, y: [(x - off[0]) * k, (y - off[1]) * k]
    meta = {"k": k, "off": off, "size": [out.shape[1], out.shape[0]],
            "eyes": [H(*e) for e in EYES], "mouth": H(*MOUTH), "mouth_w": MOUTH_W * k, "chin": H(*CHIN),
            "neck_pivot": H(440, 400)}
    json.dump(meta, open("build/rig/head.json", "w"), indent=1)
    print("head", out.shape, "off", off)
    return out, meta

if __name__ == "__main__":
    build()

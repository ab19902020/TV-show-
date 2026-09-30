"""Lip-sync mouths on the master head: the sheet's six mouth drawings (A, E, I, O, U, REST) plus FV, L and TH
made from them, each turned into a patch that sits on the face exactly.

- The face's own mouth is painted out once (head_nomouth.png); every frame gets one of these patches, REST included,
  so the closed mouth looks the same as the talking ones.
- One scale for all six drawings (REST's corners = the face's mouth corners), so their sizes stay relative to each
  other. Each is placed by the top of its upper lip, which stays put while the jaw opens.
- The drawings carry a patch of clean skin around the lips. The face has stubble there, so skin pixels take the
  face's own colour, shaded by the drawing (its creases and the shadow under the lower lip). Lips, teeth, tongue and
  mouth interior keep the drawing's colours, with the lips toned to the face's lip colour.

-> build/rig/mouth_<shape>.png (RGBA patch in head px) + build/rig/mouths.json {shape: [x, y] of the patch's (0,0)}"""
import json, numpy as np, cv2
from PIL import Image
from scipy import ndimage

SHAPES = ["A", "E", "I", "O", "U", "REST"]
# sticker landmarks on the main sheet (its 1x coords): top of the upper lip at the centre, and the two corners
LIPTOP = {"REST": (1512, 752), "A": (1000, 483), "E": (1245, 510), "I": (1510, 525), "O": (1002, 712), "U": (1250, 758)}
CORNERS = {"REST": ((1420, 780), (1605, 780)), "A": ((935, 535), (1065, 535)), "E": ((1160, 548), (1330, 548)),
           "I": ((1422, 555), (1600, 552)), "O": ((935, 773), (1070, 770)), "U": ((1180, 790), (1318, 788))}
FACE_LIPTOP = (437.0, 292.5)            # main-sheet coords of the face's upper-lip top (centre)
FACE_MOUTH = ((395.0, 306.0), (478.0, 305.0))
PATCH = (150, 118)                      # patch size in main-sheet px (w, h), anchored around the mouth

def lab(rgb):
    return cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2LAB).astype(np.float32)

def paint_out_mouth(head, meta):
    """inpaint the original lips and mouth line (an ellipse around them), keeping the stubble tone around"""
    k, off = meta["k"], meta["off"]
    m = np.zeros(head.shape[:2], np.uint8)
    cx, cy = (437 - off[0]) * k, (307 - off[1]) * k
    cv2.ellipse(m, (int(cx), int(cy)), (int(50 * k), int(19 * k)), 0, 0, 360, 255, -1)
    rgb = np.ascontiguousarray(head[..., :3].astype(np.uint8))
    fill = cv2.inpaint(rgb, m, 12 * k, cv2.INPAINT_TELEA)
    # a light blur inside the hole hides the inpaint's streaks; blend it in softly
    blur = cv2.GaussianBlur(fill, (0, 0), 3 * k)
    w = cv2.GaussianBlur((m > 0).astype(np.float32), (0, 0), 2 * k)[..., None]
    out = head.copy()
    out[..., :3] = fill * (1 - w * 0.6) + blur * (w * 0.6)
    return out

def raw_sticker(shape):
    meta = json.load(open("build/parts/meta.json"))["mouth_" + shape]
    im = np.asarray(Image.open(f"build/parts/mouth_{shape}.png")).astype(np.float32)
    return im, meta["off"], meta["scale"]

# the three extra shapes, made from the drawings (main-sheet coords of the base drawing):
#   FV: the "I" mouth with the lower lip raised onto the upper teeth (rows from the lower lip's top line down move
#       up by the lower teeth's height)
#   TH: the "E" mouth with the tongue tip between the teeth, in front of the lower teeth
#   L:  the "E" mouth with the tongue tip raised behind the upper teeth
DERIVED = {"FV": "I", "TH": "E", "L": "E"}
TONGUE = {"TH": dict(cx=1245, top=539.5, bot=586, half=26, front=True),
          "L": dict(cx=1245, top=540.0, bot=590, half=17, front=False)}

def tongue_layer(shape, im, off, k):
    """a drawn tongue tip in the sticker's style: pink, lighter on top, a thin dark outline and a centre groove"""
    T = TONGUE[shape]
    H, W = im.shape[:2]
    X = lambda x: (x - off[0]) * k
    Y = lambda y: (y - off[1]) * k
    ss = 4
    m = np.zeros((H * ss // 2, W * ss // 2), np.uint8)
    f = ss / 2
    cx, top, bot, half = X(T["cx"]) * f, Y(T["top"]) * f, Y(T["bot"]) * f, T["half"] * k * f
    # a tapered tongue: round tip, sides curving out towards the root
    ts = np.linspace(0, 1, 60)
    wid = half * (0.72 + 0.5 * ts ** 0.8)                       # half-width along the tongue
    ys_ = top + (bot - top) * ts
    tip = [(cx + wid[0] * np.cos(a), top + wid[0] * 0.95 * (1 - np.sin(a))) for a in np.linspace(np.pi, 0, 30)]
    right = [(cx + w_, y_ + wid[0] * 0.95) for w_, y_ in zip(wid, ys_)]
    left = [(cx - w_, y_ + wid[0] * 0.95) for w_, y_ in zip(wid[::-1], ys_[::-1])]
    cv2.fillPoly(m, [np.int32(tip + right + left)], 255, cv2.LINE_AA)
    m = cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    yy = np.arange(H, dtype=np.float32)[:, None]
    solid = m.copy()                          # for the outline: the full shape
    # the root fades into the drawing's own tongue (no edge across it)
    m = m * np.clip((Y(T["bot"]) - yy) / (0.4 * (Y(T["bot"]) - Y(T["top"]))), 0, 1)
    t = np.clip((yy - Y(T["top"])) / max(1.0, Y(T["bot"]) - Y(T["top"])), 0, 1)
    col = np.float32([236, 138, 122]) * (1 - t[..., None]) + np.float32([204, 98, 88]) * t[..., None]
    col = np.broadcast_to(col, (H, W, 3)).copy()
    # highlight near the tip, a short groove down the middle
    hl = np.zeros((H, W), np.float32)
    cv2.ellipse(hl, (int(X(T["cx"] - T["half"] * 0.25)), int(Y(T["top"] + T["half"] * 0.55))),
                (int(T["half"] * 0.38 * k), int(T["half"] * 0.2 * k)), -8, 0, 360, 1, -1, cv2.LINE_AA)
    hl = cv2.GaussianBlur(hl, (0, 0), 1.2 * k)
    col += hl[..., None] * np.float32([28, 34, 30])
    gr = np.zeros((H, W), np.float32)
    cv2.line(gr, (int(X(T["cx"])), int(Y(T["top"] + T["half"] * 0.7))), (int(X(T["cx"])), int(Y(T["bot"] - 4))), 1,
             max(1, int(0.9 * k)), cv2.LINE_AA)
    gr = cv2.GaussianBlur(gr, (0, 0), 1.1 * k)
    col = col * (1 - gr[..., None] * 0.22)
    # soft darker rim just inside the shape's edge (the drawings' tongues have one)
    edge = np.clip(solid - cv2.GaussianBlur(cv2.erode(solid, np.ones((3, 3), np.uint8), iterations=max(1, int(1.2 * k))),
                                            (0, 0), 0.6 * k), 0, 1) * m
    col = col * (1 - edge[..., None] * 0.45) + np.float32([110, 40, 36]) * (edge[..., None] * 0.45)
    return col, m

def derived(shape):
    base = DERIVED[shape]
    im, off, k = raw_sticker(base)
    im = im.copy()
    if shape == "FV":
        # rows from the lower lip's top line (y 567.5) move up 8.5 px: the lip now rests under the upper teeth
        y0 = int(round((567.5 - off[1]) * k)); dy = int(round(8.5 * k))
        low = im[y0:].copy()
        out = im.copy()
        out[y0 - dy:y0 - dy + low.shape[0]] = low
        out[y0 - dy + low.shape[0]:] = 0
        a = out[..., 3:] / 255
        return out, off, k
    col, m = tongue_layer(shape, im, off, k)
    inside = im[..., 3] / 255 > 0.5
    teeth = (im[..., :3].min(2) > 190) & inside
    mouth_open = ndimage.binary_fill_holes(((im[..., :3].max(2) < 90) | teeth) & inside)
    m = m * mouth_open
    rgb = im[..., :3] * (1 - m[..., None]) + col * m[..., None]
    if not TONGUE[shape]["front"]:                     # behind the upper teeth: the teeth stay on top
        up = teeth & (np.arange(im.shape[0])[:, None] < (TONGUE[shape]["top"] + 12 - off[1]) * k)
        rgb[up] = im[..., :3][up]
    out = im.copy(); out[..., :3] = rgb
    return out, off, k

def sticker(shape):
    return derived(shape) if shape in DERIVED else raw_sticker(shape)

def face_lip_stats(head, meta):
    k, off = meta["k"], meta["off"]
    L = lab(head[..., :3])
    ys, xs = np.mgrid[0:head.shape[0], 0:head.shape[1]]
    sx, sy = xs / k + off[0], ys / k + off[1]
    lips = (((sx - 437) / 40) ** 2 + ((sy - 306) / 13) ** 2 < 1) & (L[..., 1] > 150) & (L[..., 0] > 90)
    return L[lips].mean(0)

def build():
    hmeta = json.load(open("build/rig/head.json"))
    head = np.asarray(Image.open("build/rig/head.png")).astype(np.float32)
    k, off = hmeta["k"], hmeta["off"]
    base = paint_out_mouth(head, hmeta)
    Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).save("build/rig/head_nomouth.png")
    face_lip = face_lip_stats(head, hmeta)
    (cl, cr) = CORNERS["REST"]
    scale = (FACE_MOUTH[1][0] - FACE_MOUTH[0][0]) / (cr[0] - cl[0])      # main px per sticker-sheet px
    pw, ph = int(PATCH[0] * k), int(PATCH[1] * k)
    px0 = int((FACE_LIPTOP[0] - PATCH[0] / 2 - off[0]) * k)
    py0 = int((FACE_LIPTOP[1] - 32 - off[1]) * k)
    face = base[py0:py0 + ph, px0:px0 + pw, :3]
    face_L = lab(face)
    out = {}
    for shape in SHAPES + list(DERIVED):
        im, soff, sk = sticker(shape)
        # sticker part px -> patch px
        lx, ly = LIPTOP[DERIVED.get(shape, shape)]
        g = scale * k / sk                              # patch px per sticker-part px
        tx = (FACE_LIPTOP[0] - off[0]) * k - px0 - ((lx - soff[0]) * sk) * g
        ty = (FACE_LIPTOP[1] - off[1]) * k - py0 - ((ly - soff[1]) * sk) * g
        M = np.float32([[g, 0, tx], [0, g, ty]])
        st = cv2.warpAffine(im, M, (pw, ph), flags=cv2.INTER_AREA if g < 1 else cv2.INTER_CUBIC,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
        a = np.clip(st[..., 3] / 255, 0, 1)
        rgb = st[..., :3]
        L = lab(rgb)
        inside = a > 0.9
        d = ndimage.distance_transform_edt(inside)
        ring = inside & (d > 3 * g * sk) & (d < 14 * g * sk)
        skin = np.median(L[ring], axis=0)
        # skin-likeness from chroma only (shading is handled separately)
        dc = np.sqrt((L[..., 1] - skin[1]) ** 2 + (L[..., 2] - skin[2]) ** 2)
        w = np.clip(1 - (dc - 4) / 7, 0, 1)
        w *= np.clip((L[..., 0] - 60) / 40, 0, 1)                         # dark interior is never skin
        w = cv2.GaussianBlur(w, (0, 0), 1.2)
        # skin: the face's colour, times the drawing's shading relative to its own skin
        ratio = np.clip((L[..., 0] + 8) / (skin[0] + 8), 0.55, 1.12)
        skin_out = face * ratio[..., None]
        # lips: move the drawing's lip colour to the face's lip colour (lip-like = redder than skin)
        lipw = np.clip((L[..., 1] - skin[1] - 3) / 8, 0, 1) * np.clip((L[..., 0] - 70) / 40, 0, 1)
        lip_px = lipw > 0.6
        if lip_px.sum() > 50:
            shift = face_lip - L[lip_px].mean(0)
            shift[0] *= 0.5
            L2 = L + lipw[..., None] * shift[None, None, :]
            rgb_g = cv2.cvtColor(np.clip(L2, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32)
        else:
            rgb_g = rgb
        col = skin_out * w[..., None] + rgb_g * (1 - w[..., None])
        # alpha: the drawing's own, but the skin margin fades into the face (no patch edge)
        edge = np.clip(d / (10 * g * sk), 0, 1)
        alpha = a * np.maximum(edge, 1 - w)
        alpha = cv2.GaussianBlur(alpha, (0, 0), 1.0)
        patch = np.dstack([np.clip(col, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
        Image.fromarray(patch).save(f"build/rig/mouth_{shape}.png")
        out[shape] = [px0, py0]
        print(shape, "scale %.3f" % g)
    json.dump({"origin": [px0, py0], "size": [pw, ph], "shapes": out}, open("build/rig/mouths.json", "w"), indent=1)

if __name__ == "__main__":
    build()

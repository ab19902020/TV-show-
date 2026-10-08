"""The drawings this production adds, made from the approved artwork (nothing is generated from scratch):

    python3 episodes/white-pele/tools/make_art.py [NAME ...]      (from the repository root)

Every output goes to library/characters/<id>/reference/white-pele/ and is listed in that character's film.yaml.
Each recipe below says what it starts from and what it changes:

  rooney: badge        the performance outfit's red United accent: a small red shield badge on the chest of every
                       present-day Rooney drawing (the brief: one casual outfit with a red accent)
  rooney: mic overlay  the raised microphone of rooney-mic-raised as its own layer (only the microphone's grey and
                       black pixels inside a box round it): drawn over the face after the lip sync warps the jaw, so
                       the mic never moves with the mouth
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
CH = ROOT / "library" / "characters"
INK = (22, 18, 20)


def load(path):
    return np.asarray(Image.open(path).convert("RGBA")).copy()


def save(rgba, cid, name):
    out = CH / cid / "reference" / "white-pele"
    out.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba).save(out / f"{name}.png", optimize=True)
    print(out / f"{name}.png", rgba.shape[1], "x", rgba.shape[0])


def over(dst, src, x, y):
    """premultiplied-free 'over' of an RGBA src at (x, y) (top-left) onto an RGBA dst, in place"""
    h, w = src.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(dst.shape[1], x + w), min(dst.shape[0], y + h)
    if x1 <= x0 or y1 <= y0:
        return dst
    s = src[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32) / 255
    d = dst[y0:y1, x0:x1].astype(np.float32) / 255
    a = s[..., 3:4]
    rgb = s[..., :3] * a + d[..., :3] * d[..., 3:4] * (1 - a)
    al = a + d[..., 3:4] * (1 - a)
    rgb = np.where(al > 1e-4, rgb / np.maximum(al, 1e-4), 0)
    dst[y0:y1, x0:x1] = (np.dstack([rgb, al]) * 255 + 0.5).astype(np.uint8)
    return dst


def badge(width, angle=0.0):
    """a small red shield badge in the house style: bold dark outline, a lighter red bevel, a white chevron and
    a gold rim (a generic United-red accent, not any club's crest). RGBA, drawn at 8x and reduced"""
    S = 8
    w = int(width * S)
    h = int(width * 1.18 * S)
    img = np.zeros((h + 8 * S, w + 8 * S, 4), np.uint8)
    cx = img.shape[1] / 2
    top, bot = 4 * S, h + 4 * S
    pts = []
    for u in np.linspace(0, 1, 40):                      # the shield: flat top, curved sides into a point
        x = cx - w / 2 + 0.04 * w * u
        y = top + 0.55 * (bot - top) * u
        pts.append((x, y))
    for u in np.linspace(0, 1, 40):
        a = u * np.pi / 2
        pts.append((cx - (w / 2 - 0.04 * w) * np.cos(a), top + 0.55 * (bot - top) + 0.45 * (bot - top) * np.sin(a)))
    right = [(2 * cx - x, y) for x, y in reversed(pts)]
    poly = np.int32(np.round(pts + right))
    ol = max(2, int(0.085 * w))
    cv2.fillPoly(img, [poly], (*INK, 255), cv2.LINE_AA)
    inner = np.int32(np.round(cx + (np.float32(pts + right)[:, 0] - cx) * 0.80)), \
        np.int32(np.round(top + (np.float32(pts + right)[:, 1] - top) * 0.82 + 0.06 * h))
    ip = np.stack(inner, 1)
    cv2.fillPoly(img, [ip], (226, 178, 52, 255), cv2.LINE_AA)            # gold rim
    ip2 = np.stack([np.int32(np.round(cx + (ip[:, 0] - cx) * 0.84)), np.int32(np.round(top + 0.07 * h + (ip[:, 1] - top - 0.06 * h) * 0.86))], 1)
    cv2.fillPoly(img, [ip2], (206, 22, 30, 255), cv2.LINE_AA)            # red field
    hl = ip2.copy()
    hl[:, 0] = np.int32(cx + (hl[:, 0] - cx) * 0.55 - 0.12 * w)
    cv2.fillPoly(img, [hl[: len(hl) // 2]], (232, 64, 60, 255), cv2.LINE_AA)   # the lit side
    chev = np.int32([[cx - 0.26 * w, top + 0.38 * h], [cx, top + 0.58 * h], [cx + 0.26 * w, top + 0.38 * h]])
    cv2.polylines(img, [chev], False, (250, 250, 250, 255), int(0.11 * w), cv2.LINE_AA)
    cv2.polylines(img, [np.int32(np.round(pts + right))], True, (*INK, 255), ol, cv2.LINE_AA)
    img = cv2.resize(img, (img.shape[1] // S, img.shape[0] // S), interpolation=cv2.INTER_AREA)
    if angle:
        M = cv2.getRotationMatrix2D((img.shape[1] / 2, img.shape[0] / 2), -angle, 1.0)
        img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_LINEAR)
    return img


def with_badge(rgba, at, width, angle=0.0):
    b = badge(width, angle)
    return over(rgba, b, int(at[0] - b.shape[1] / 2), int(at[1] - b.shape[0] / 2))


def masked(rgba, box, keep, seed=None, poly=None):
    """only the pixels inside box (x0, y0, x1, y1) where keep(rgb) is true (and, with a seed point, only the
    connected piece of them that holds it), everything else transparent"""
    out = np.zeros_like(rgba)
    x0, y0, x1, y1 = box
    sub = rgba[y0:y1, x0:x1].copy()
    m = keep(sub[..., :3]) & (sub[..., 3] > 0)
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0
    if seed is not None:
        n, lab = cv2.connectedComponents(m.astype(np.uint8), connectivity=4)
        m = lab == lab[seed[1] - y0, seed[0] - x0]
    if poly is not None:
        pm = np.zeros(m.shape, np.uint8)
        cv2.fillPoly(pm, [np.int32(poly) - np.int32([x0, y0])], 1)
        m &= pm > 0
    sub[..., 3] = np.where(m, sub[..., 3], 0)
    out[y0:y1, x0:x1] = sub
    return out


def grey(rgb):
    """the microphone: dark or grey, unsaturated (skin is a saturated orange)"""
    hsv = cv2.cvtColor(np.ascontiguousarray(rgb), cv2.COLOR_RGB2HSV)
    return (hsv[..., 1] < 70) | (hsv[..., 2] < 60)


# ---------------------------------------------------------------- recipes
def rooney():
    src = CH / "wayne-rooney" / "reference" / "poses"
    mic = load(src / "rooney-mic.png")
    save(with_badge(mic, (668, 630), 46, 6), "wayne-rooney", "mic")
    up = load(src / "rooney-mic-raised.png")
    save(with_badge(up, (668, 640), 46, 6), "wayne-rooney", "micup")
    # the raised mic, grille to grip, above the hand: its own layer over the face
    save(masked(up, (530, 355, 660, 470), grey, seed=(600, 400),
                 poly=[(552, 360), (648, 360), (652, 418), (618, 470), (556, 470), (545, 420)]), "wayne-rooney", "micup-fg")


RECIPES = {"rooney": rooney}



# ---------------------------------------------------------------- the football memory: younger Rooney in a red 10
# On a copy of the young model sheet, the black tee becomes a red shirt (its own shading kept: the black's light and
# dark become the red's), with a white collar edge and a small white 10 on the chest (the house kits put the number
# there, like Bruno's 8); the black trousers become white shorts down to the knee and black socks below it. The ink
# outline (darker than the cloth) stays. Per pose: its box on the sheet, the waist line, the knee line(s)
KIT10_POSES = {
    # name: (box x0, y0, x1, y1), waist y (the shirt's hem), the shorts (a polygon over the hips and thighs, sheet
    # px: the cloth inside it below the hem turns white), the 10's centre
    "neutral": ((45, 1225, 128, 1370), 1304, [(52, 1300), (122, 1300), (122, 1323), (52, 1323)], (86, 1285)),
    "run1": ((598, 1225, 740, 1372), 1306, [(625, 1300), (718, 1300), (716, 1331), (694, 1336), (676, 1326),
                                            (660, 1327), (640, 1334), (622, 1330)], (672, 1276)),
    "run2": ((768, 1225, 907, 1372), 1306, [(795, 1300), (890, 1300), (886, 1331), (864, 1336), (848, 1326),
                                            (832, 1327), (812, 1334), (792, 1330)], (842, 1276)),
    "run3": ((938, 1225, 1072, 1372), 1308, [(965, 1300), (1060, 1300), (1058, 1330), (1036, 1334), (1018, 1325),
                                             (1000, 1330), (984, 1342), (968, 1338)], (1010, 1276)),
    "shrug": ((562, 1040, 718, 1172), 1172, [], (640, 1135)),
    "nod": ((712, 1040, 830, 1172), 1172, [], (772, 1140)),
    "front": ((300, 160, 448, 470), 338, [(320, 330), (430, 330), (430, 377), (320, 377)], (373, 290)),
}


def kit10_sheet():
    from PIL import ImageDraw, ImageFont
    src = cv2.imread(str(CH / "wayne-rooney" / "reference" / "model-sheet.png"), cv2.IMREAD_COLOR)
    out = src.copy()
    hsv = cv2.cvtColor(src, cv2.COLOR_BGR2HSV)
    V = hsv[..., 2].astype(np.float32)
    S = hsv[..., 1].astype(np.float32)
    for name, ((x0, y0, x1, y1), waist, poly, num) in KIT10_POSES.items():
        sub = (slice(y0, y1), slice(x0, x1))
        v, s = V[sub], S[sub]
        cloth = (v > 19) & (v < 120) & (s < 70)              # the black cloth (not the ink, not skin, not paper)
        ink = v <= 19
        yy = np.arange(y0, y1)[:, None] + np.zeros((1, x1 - x0))
        shirt = cloth & (yy < waist)
        legs = cloth & (yy >= waist)
        pm = np.zeros(legs.shape, np.uint8)
        if poly:
            cv2.fillPoly(pm, [np.int32(poly) - np.int32([x0, y0])], 1)
        shorts = legs & (pm > 0)
        sh = np.clip((v - 19) / 70.0, 0, 1)                   # 0 dark .. 1 light
        blk = out[sub].astype(np.float32)
        red = np.stack([34 + 44 * sh, 30 + 34 * sh, 186 + 60 * sh], -1)        # BGR: United red, its own shading
        white = np.stack([200 + 50 * sh, 200 + 50 * sh, 205 + 48 * sh], -1)
        blk[shirt] = red[shirt]
        blk[shorts] = white[shorts]
        out[sub] = np.clip(blk, 0, 255).astype(np.uint8)
        # a white edge where the shirt meets the neck: the collar
        neck = (~cloth & ~ink & (s > 60))
        edge = cv2.dilate(neck.astype(np.uint8), np.ones((3, 3), np.uint8)) & shirt.astype(np.uint8)
        collar = edge & (yy < np.percentile(yy[shirt], 12) if shirt.any() else 0)
        o = out[sub]
        o[collar.astype(bool)] = (235, 235, 240)
        out[sub] = o
    img = Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))
    d = ImageDraw.Draw(img)
    font = ROOT / "library" / "fonts" / "BebasNeue-Regular.ttf"
    for name, ((x0, y0, x1, y1), waist, poly, (nx, ny)) in KIT10_POSES.items():
        size = max(9, int((y1 - y0) * (0.075 if name != "front" else 0.06)))
        f = ImageFont.truetype(str(font), size)
        d.text((nx, ny), "10", font=f, fill=(250, 250, 250), anchor="mm", stroke_width=1, stroke_fill=(120, 10, 16))
    out_dir = CH / "wayne-rooney" / "reference" / "white-pele"
    out_dir.mkdir(parents=True, exist_ok=True)
    img.save(out_dir / "model-sheet-kit10.png")
    print(out_dir / "model-sheet-kit10.png")


RECIPES["kit10"] = kit10_sheet


def rooney_sheet_badge():
    """the young model sheet's present-day poses with the performance outfit's badge (where the chest shows)"""
    img = np.asarray(Image.open(CH / "wayne-rooney" / "reference" / "model-sheet.png").convert("RGBA")).copy()
    for at, w, ang in (((655, 1118), 9, 4), ((398, 283), 12, 0), ((566, 287), 11, 8), ((99, 1283), 5, 0)):
        img = with_badge(img, at, w, ang)
    out = CH / "wayne-rooney" / "reference" / "white-pele" / "model-sheet-badge.png"
    Image.fromarray(img[..., :3]).save(out)
    print(out)


RECIPES["sheet-badge"] = rooney_sheet_badge


# ---------------------------------------------------------------- Roy Keane: the house cartoon head on Pass Mic's bodies
# The library's Roy (the cartoon head of his kit, the one United Road films) on Pass Mic's Style 1 bodies (arms
# folded, standing, walking): Pass Mic made these by putting a semi-realistic Roy head on Gary Neville's bodies; here
# that head is taken off (everything above the jacket's shoulder line) and the library head put on in its place,
# its beard's bottom on the old beard's bottom, as wide as the old head. The library head is cut from its built
# drawing (build/film/roy-keane/<view>.png, 4x) just under the beard.
def head_of(cid, view, cut_y):
    """the head of a built drawing above sheet y cut_y (feathered), RGBA, and its meta"""
    import json
    base = ROOT / "build" / "film" / cid
    meta = json.loads((base / "meta.json").read_text())[view]
    im = load(base / f"{view}.png")
    K, (ox, oy) = meta["scale"], meta["off"]
    yc = int((cut_y - oy) * K)
    out = im[:yc + 12].copy()
    ramp = np.clip((yc + 12 - np.arange(out.shape[0])) / 24.0, 0, 1)
    out[..., 3] = (out[..., 3] * ramp[:, None]).astype(np.uint8)
    return out, meta


def swap_head(body, erase, head, meta, src_anchor, dst_anchor, scale, flip=False):
    """body: RGBA; erase: polygon (body px) whose pixels are removed (the old head); head/meta: the new head and its
    drawing's meta; src_anchor: a sheet point on the new head (the beard's bottom centre); dst_anchor: where it goes
    on the body (px); scale: body px per sheet px"""
    out = body.copy()
    m = np.zeros(out.shape[:2], np.uint8)
    cv2.fillPoly(m, [np.int32(erase)], 1)
    out[m > 0, 3] = 0
    K, (ox, oy) = meta["scale"], meta["off"]
    k = scale / K
    if flip:
        head = head[:, ::-1].copy()
        ax = head.shape[1] - (src_anchor[0] - ox) * K
    else:
        ax = (src_anchor[0] - ox) * K
    ay = (src_anchor[1] - oy) * K
    h2 = cv2.resize(head, (int(head.shape[1] * k), int(head.shape[0] * k)), interpolation=cv2.INTER_AREA)
    pad = 400
    big = np.zeros((out.shape[0] + 2 * pad, out.shape[1] + 2 * pad, 4), np.uint8)
    big[pad:pad + out.shape[0], pad:pad + out.shape[1]] = out
    over(big, h2, int(dst_anchor[0] - ax * k) + pad, int(dst_anchor[1] - ay * k) + pad)
    ys, xs = np.nonzero(big[..., 3] > 0)
    return big[ys.min():ys.max() + 1, xs.min():xs.max() + 1]


def light_head(rgba, top_share=0.6):
    """the head of a drawing: the largest region of light pixels (skin, beard, hair: not the black clothes, not
    the ink) in its top part -> (mask, x0, y0, x1, y1, bottom-centre x, bottom y)"""
    hsv = cv2.cvtColor(np.ascontiguousarray(rgba[..., :3]), cv2.COLOR_RGB2HSV)
    m = (rgba[..., 3] > 128) & (hsv[..., 2] > 70)
    m[int(top_share * m.shape[0]):] = False
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    comp = lab == k
    ys, xs = np.nonzero(comp)
    low = ys > ys.max() - 0.03 * (ys.max() - ys.min())
    return comp, xs.min(), ys.min(), xs.max(), ys.max(), float(xs[low].mean()), float(ys.max())


ROY_BODIES = {
    # name: (Pass Mic file, the library view whose head goes on (walking: his profile), how far down the old head
    # can reach, as a share of the drawing's height)
    "crossed": ("body/stand_crossed.png", "front", 0.6),
    "stand": ("body/stand_neutral.png", "front", 0.6),
    "crossed-cu": ("closeup/crossed_arms.png", "front", 0.75),
    "walk1": ("body/walk_1.png", "side", 0.55), "walk2": ("body/walk_2.png", "side", 0.55),
    "walk3": ("body/walk_3.png", "side", 0.55), "walk4": ("body/walk_4.png", "side", 0.55),
}


def fill_holes(rgba, color=(30, 30, 33)):
    """see-through gaps left inside a figure (where an old part was taken off and the new one does not quite
    reach) filled with the cloth round them"""
    solid = (rgba[..., 3] > 128).astype(np.uint8)
    inv = 1 - solid
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    H, W = solid.shape
    out = rgba.copy()
    for k in range(1, n):
        x, y, w, h, a = st[k]
        if x > 0 and y > 0 and x + w < W and y + h < H:
            out[lab == k] = (*color, 255)
    return out


def ground_shadow(rgba, share=0.14):
    """a cut-out's drawn ground shadow (the sheet's paper-grey ellipse under the feet) made a soft dark contact
    shadow, so it grounds the figure on a dark set instead of showing as a pale puddle"""
    out = rgba.copy()
    h = out.shape[0]
    y0 = int((1 - share) * h)
    hsv = cv2.cvtColor(np.ascontiguousarray(out[y0:, :, :3]), cv2.COLOR_RGB2HSV).astype(np.int16)
    sh = (hsv[..., 1] < 28) & (hsv[..., 2] > 115) & (hsv[..., 2] < 246) & (out[y0:, :, 3] > 0)
    dark = (255 - hsv[..., 2]) / 140.0                           # the darker the grey, the deeper the shadow
    sub = out[y0:]
    sub[sh, :3] = 0
    sub[sh, 3] = np.clip(dark[sh] * 150, 30, 120).astype(np.uint8)
    out[y0:] = sub
    # paper the cut kept between the legs: tall pale regions in the lower half (the soles' white is a thin strip)
    y1 = int(0.5 * h)
    hsv = cv2.cvtColor(np.ascontiguousarray(out[y1:, :, :3]), cv2.COLOR_RGB2HSV).astype(np.int16)
    pale = ((hsv[..., 1] < 22) & (hsv[..., 2] > 200) & (out[y1:, :, 3] > 0)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(pale, 8)
    sub = out[y1:]
    for k in range(1, n):
        if st[k, cv2.CC_STAT_HEIGHT] > 0.06 * h and st[k, cv2.CC_STAT_HEIGHT] > 1.5 * st[k, cv2.CC_STAT_WIDTH]:
            m = cv2.dilate((lab == k).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
            sub[m & (sub[..., :3].min(2) > 150), 3] = 0
    out[y1:] = sub
    return out


def walk_shadows():
    """Pass Mic's walk keys for Goldbridge and Neville, their pale ground shadows made contact shadows"""
    for cid, c in (("mark-goldbridge", "walk"), ("gary-neville", "walk")):
        for k in (1, 2, 3, 4):
            im = load(CH / cid / "reference" / "passmic" / "walk" / f"walk_{k}.png")
            n, lab, st, _ = cv2.connectedComponentsWithStats((im[..., 3] > 20).astype(np.uint8), 8)
            main = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            near = cv2.dilate((lab == main).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
            im[~near, 3] = 0                                    # stray bits of the sheet (its header bar)
            save(ground_shadow(im), cid, f"walk{k}")


RECIPES["walk-shadows"] = walk_shadows


def roy():
    """the old head found (light_head) and erased with its outline (the region grown by 4 % of its width), the
    library head scaled to the old head's width and set with its beard's bottom on the old beard's bottom"""
    src = CH / "roy-keane" / "reference" / "passmic"
    heads = {"front": head_of("roy-keane", "front", 352), "side": head_of("roy-keane", "side", 372)}
    for name, (f, view, reach) in ROY_BODIES.items():
        body = load(src / f)
        comp, x0, y0, x1, y1, bx, by = light_head(body, reach)
        grow = int(0.04 * (x1 - x0)) | 1
        erase = cv2.dilate(comp.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grow, grow)))
        erase[:int(y0 + 0.6 * (y1 - y0))] = 1                     # the dark hair and its outline, all of it
        hsv = cv2.cvtColor(np.ascontiguousarray(body[..., :3]), cv2.COLOR_RGB2HSV)
        box = np.zeros_like(erase)
        box[y0:y1 + 3, max(0, x0 - grow):x1 + grow] = 1
        erase |= (box & (hsv[..., 2] > 70)).astype(erase.dtype)    # every bit of the old beard
        head, meta = heads[view]
        hc, hx0, hy0, hx1, hy1, hbx, hby = light_head(head, 1.0)
        K, (ox, oy) = meta["scale"], meta["off"]
        sc = (x1 - x0) / ((hx1 - hx0) / K)                     # body px per sheet px
        out = body.copy()
        out[erase > 0, 3] = 0
        img = swap_head(out, [(0, 0), (1, 0), (1, 1)], head, meta, (hbx / K + ox, hby / K + oy), (bx, by), sc)
        save(ground_shadow(fill_holes(img)), "roy-keane", name)


RECIPES["roy"] = roy


# ---------------------------------------------------------------- Gary Neville's clipboard
# Pass Mic's Gary looking at his phone (upper/holding_phone, 16x): the phone becomes the back of a clipboard (a brown
# board with a steel clip, the house outline), and his own fingers are put back over its edge (the skin of the hand
# from the original drawing, inside the hand's box)
def clipboard_img(w, h, ang):
    S = 4
    img = np.zeros((int(h * 1.5 * S), int(w * 1.5 * S), 4), np.uint8)
    cx, cy = img.shape[1] / 2, img.shape[0] / 2
    def R(pts):
        a = np.radians(ang)
        c, s_ = np.cos(a), np.sin(a)
        return np.int32([[cx + (x * c - y * s_) * S, cy + (x * s_ + y * c) * S] for x, y in pts])
    lw = int(0.03 * w * S)
    board = R([(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)])
    cv2.fillPoly(img, [board], (150, 96, 52, 255), cv2.LINE_AA)
    cv2.fillPoly(img, [R([(-w / 2 + 0.06 * w, -h / 2 + 0.05 * h), (-w / 2 + 0.16 * w, -h / 2 + 0.05 * h),
                          (-w / 2 + 0.16 * w, h / 2 - 0.05 * h), (-w / 2 + 0.06 * w, h / 2 - 0.05 * h)])],
                 (178, 124, 72, 255), cv2.LINE_AA)
    cv2.polylines(img, [board], True, (*INK, 255), lw, cv2.LINE_AA)
    clip = R([(-0.22 * w, -h / 2 - 0.07 * h), (0.22 * w, -h / 2 - 0.07 * h), (0.26 * w, -h / 2 + 0.06 * h),
              (-0.26 * w, -h / 2 + 0.06 * h)])
    cv2.fillPoly(img, [clip], (196, 200, 208, 255), cv2.LINE_AA)
    cv2.polylines(img, [clip], True, (*INK, 255), lw, cv2.LINE_AA)
    img = cv2.resize(img, (img.shape[1] // S, img.shape[0] // S), interpolation=cv2.INTER_AREA)
    return img


def gary():
    src = CH / "gary-neville" / "reference" / "passmic" / "upper" / "holding_phone.png"
    im = load(src)
    hsv = cv2.cvtColor(np.ascontiguousarray(im[..., :3]), cv2.COLOR_RGB2HSV)
    skin = (hsv[..., 0] >= 5) & (hsv[..., 0] <= 22) & (hsv[..., 1] > 70) & (hsv[..., 2] > 120) & (im[..., 3] > 0)
    hand = np.zeros(skin.shape, np.uint8)
    cv2.fillPoly(hand, [np.int32([(560, 1370), (1330, 1370), (1330, 1960), (560, 1960)])], 1)
    fingers = skin & (hand > 0)
    fingers = cv2.dilate(fingers.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0     # with their outline
    keep = im.copy()
    keep[..., 3] = np.where(fingers, im[..., 3], 0)
    cb = clipboard_img(400, 500, -12)
    out = over(im.copy(), cb, 1105 - cb.shape[1] // 2, 1470 - cb.shape[0] // 2)
    out = over(out, keep, 0, 0)
    save(out, "gary-neville", "clipboard")


RECIPES["gary"] = gary


def roy_point():
    """Roy pointing (at the confetti): his head on Pass Mic's Gary pointing (upper/pointing, 16x)"""
    body = load(CH / "gary-neville" / "reference" / "passmic" / "upper" / "pointing.png")
    comp, x0, y0, x1, y1, bx, by = light_head(body, 0.62)
    grow = int(0.10 * (x1 - x0)) | 1
    erase = cv2.dilate(comp.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (grow, grow)))
    erase[:int(y0 + 0.6 * (y1 - y0))] = 1
    head, meta = head_of("roy-keane", "front", 352)
    hc, hx0, hy0, hx1, hy1, hbx, hby = light_head(head, 1.0)
    K, (ox, oy) = meta["scale"], meta["off"]
    sc = (x1 - x0) / ((hx1 - hx0) / K)
    out = body.copy()
    out[erase > 0, 3] = 0
    img = swap_head(out, [(0, 0), (1, 0), (1, 1)], head, meta, (hbx / K + ox, hby / K + oy), (bx, by), sc)
    save(fill_holes(img), "roy-keane", "point")


RECIPES["roy-point"] = roy_point


def mark_stand():
    """Goldbridge standing (Pass Mic body/stand_neutral): the sheet's header strip over his head taken off, the paper
    between his legs cut away, his ground shadow made a contact shadow"""
    im = load(CH / "mark-goldbridge" / "reference" / "passmic" / "body" / "stand_neutral.png")
    n, lab, st, _ = cv2.connectedComponentsWithStats((im[..., 3] > 20).astype(np.uint8), 8)
    main = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    near = cv2.dilate((lab == main).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
    im[~near, 3] = 0
    save(ground_shadow(im), "mark-goldbridge", "stand")


RECIPES["mark-stand"] = mark_stand


# ---------------------------------------------------------------- the upgrade pack (episodes/white-pele/upgrade-pack)
PACK = Path(__file__).resolve().parents[1] / "upgrade-pack"
PACK_CUTS = {        # sheet: [(character folder, drawing name), ...] in reading order (rows top to bottom, left to right)
    "CH01_rooney_performance": [("wayne-rooney", n) for n in
                                ("perf-stand", "perf-reach", "perf-lean", "perf-point", "perf-back", "perf-kneel")],
    "CH02_rooney_walk": [("wayne-rooney", n) for n in
                         ("pwalk1", "pwalk2", "pwalk3", "pwalk4", "pwalk-back", "pwalk-back34")],
    "CH03_rooney_football": [("wayne-rooney", n) for n in
                             ("ball-ready", "ball-run", "ball-strike", "ball-bicycle", "ball-land", "ball-celebrate")],
    "CH04_reactions": [("rio-ferdinand", "palms"), ("rio-ferdinand", "laughbent2"), ("rio-ferdinand", "scarf"),
                       ("roy-keane", "folded"), ("roy-keane", "clap"), ("roy-keane", "broom")],
    "CH05_supporters": [("white-pele-supporters", f"fan{k}") for k in range(1, 7)],
}
PROP_CUTS = ["ball", "mic", "mic-side", "stick-a", "stick-b", "scarf", "guitar", "bass", "trophy"]


def pack_parts(sheet):
    """the figures on one of the pack's transparent sheets, each with the stray bits inside its box, in reading order"""
    im = load(PACK / f"{sheet}.png")
    n, lab, st, cen = cv2.connectedComponentsWithStats((im[..., 3] > 20).astype(np.uint8), 8)
    big = [k for k in range(1, n) if st[k][4] > 1500]
    rows = sorted(big, key=lambda k: st[k][1])
    order = sorted(big, key=lambda k: (0 if st[k][1] + st[k][3] / 2 < im.shape[0] / 2 or sheet.startswith("PR")
                                       and st[k][1] < 420 else 1, st[k][0]))
    out = []
    for k in order:
        x, y, w, h = st[k][:4]
        keep = lab == k
        for j in range(1, n):                       # small detached pieces (a highlight, a lace) inside the box
            if j not in big and x <= cen[j][0] <= x + w and y <= cen[j][1] <= y + h:
                keep |= lab == j
        part = im.copy()
        part[~keep, 3] = 0
        pad = 12
        out.append(part[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad])
    return out


def upgrade():
    """cut every figure and prop of the upgrade pack into the library, upscaled 4x with Real-ESRGAN (the engine's
    upscaler, as Pass Mic's cut-outs were): reference/upgrade/<drawing>.png"""
    sys.path.insert(0, str(ROOT))
    from studio.film.art import upscale_rgba
    for sheet, names in PACK_CUTS.items():
        parts = pack_parts(sheet)
        assert len(parts) == len(names), (sheet, len(parts))
        for (cid, name), part in zip(names, parts):
            d = CH / cid / "reference" / "upgrade"
            d.mkdir(parents=True, exist_ok=True)
            part = upscale_rgba(part)
            Image.fromarray(part).save(d / f"{name}.png")
            print(cid, name, part.shape[1], "x", part.shape[0])
    parts = pack_parts("PR01_music_football_props")
    props = CH.parent / "props" / "white-pele"
    props.mkdir(parents=True, exist_ok=True)
    for name, part in zip(PROP_CUTS, parts):
        Image.fromarray(upscale_rgba(part)).save(props / f"{name}.png")
        print("prop", name, part.shape[1], "x", part.shape[0])


RECIPES["upgrade"] = upgrade


def upgrade_derived():
    """from the pack's cuts: the back-view walk keys flipped (the other foot forward, so two keys make a step), and
    Keane's broom taken out of his hand as its own prop so it can sweep (his fist stays; cut-props.json says where)"""
    import json
    for cid, name in (("wayne-rooney", "pwalk-back"), ("rio-ferdinand", "back-walk")):
        d = CH / cid / "reference" / "upgrade"
        src = d / f"{name}.png" if (d / f"{name}.png").exists() else None
        if src is None:                                  # Rio's back view is his model sheet's (film.yaml "back")
            continue
        im = load(src)
        Image.fromarray(np.ascontiguousarray(im[:, ::-1])).save(d / f"{name}-m.png")
    d = CH / "roy-keane" / "reference" / "upgrade"
    im = load(d / "broom.png")
    H, W = im.shape[:2]
    m = np.zeros((H, W), bool)
    m[0:725, 940:1095] = True                           # the handle above his fist
    m[935:1745, 968:] = True                            # the handle below it (clear of his sleeve)
    m[1745:, 868:] = True                               # the head
    m[1868:, 868:915] = False                           # his shoe's toe
    m &= im[..., 3] > 0
    broom = np.zeros_like(im)
    broom[m] = im[m]
    hand = im.copy()
    hand[m, 3] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats((hand[..., 3] > 20).astype(np.uint8), 8)
    main = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    hand[(lab != main) & (lab > 0), 3] = 0               # the broom head's outline left behind
    ys, xs = np.nonzero(broom[..., 3] > 0)
    x0, y0 = xs.min(), ys.min()
    Image.fromarray(broom[y0:ys.max() + 1, x0:xs.max() + 1]).save(d / "broom-prop.png")
    Image.fromarray(hand).save(d / "broom-hand.png")
    grip = (1000 - int(x0), 830 - int(y0))              # the middle of his fist on the handle
    (d / "cut-props.json").write_text(json.dumps({"broom": {
        "image": "roy-keane/reference/upgrade/broom-prop.png", "grip": grip, "at": [1000, 830]}}, indent=1))
    print("broom prop", broom.shape, "grip", grip)


RECIPES["upgrade-derived"] = upgrade_derived


def leg_paper():
    """the sheet's paper the cut kept between walking legs (a pale triangle over the ground): a pale region in the
    lower half that borders the transparent ground or the contact shadow is paper, a white trainer is ringed by ink.
    Applied to the walk keys of Goldbridge, Neville and Keane after walk-shadows / roy"""
    for cid in ("mark-goldbridge", "gary-neville", "roy-keane"):
        for k in (1, 2, 3, 4):
            f = CH / cid / "reference" / "white-pele" / f"walk{k}.png"
            im = load(f)
            H = im.shape[0]
            rgb = im[..., :3].astype(np.int16)
            pale = (rgb.min(2) > 200) & (rgb.max(2) - rgb.min(2) < 28) & (im[..., 3] > 200)
            pale[:int(0.5 * H)] = False
            n, lab, st, _ = cv2.connectedComponentsWithStats(pale.astype(np.uint8), 8)
            soft = im[..., 3] < 200                      # the ground around the feet, the contact shadow
            gone = 0
            for j in range(1, n):
                if (st[j, cv2.CC_STAT_AREA] < 0.0004 * H * H
                        or st[j, cv2.CC_STAT_HEIGHT] < 0.8 * st[j, cv2.CC_STAT_WIDTH]):   # a trainer is wide
                    continue
                comp = (lab == j).astype(np.uint8)
                ring = cv2.dilate(comp, np.ones((7, 7), np.uint8)).astype(bool) & ~comp.astype(bool)
                if (soft & ring).sum() > 0.15 * ring.sum():
                    grow = cv2.dilate(comp, np.ones((3, 3), np.uint8)).astype(bool)
                    im[grow & (rgb.min(2) > 150), 3] = 0
                    gone += int(st[j, cv2.CC_STAT_AREA])
            # the sheet's header strip: anything not joined to the figure
            n2, lab2, st2, _ = cv2.connectedComponentsWithStats((im[..., 3] > 20).astype(np.uint8), 8)
            if n2 > 2:
                main = 1 + int(np.argmax(st2[1:, cv2.CC_STAT_AREA]))
                near = cv2.dilate((lab2 == main).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
                im[~near, 3] = 0
            Image.fromarray(im).save(f)
            print(cid, k, "paper px removed", gone)


RECIPES["leg-paper"] = leg_paper


if __name__ == "__main__":
    for name in sys.argv[1:] or RECIPES:
        RECIPES[name]()

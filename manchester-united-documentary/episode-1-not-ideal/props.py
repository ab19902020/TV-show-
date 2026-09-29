"""Props for the scene 3 inserts, drawn to sit with the inked art: the away team coach, the goalkeeper's gloves and
a roll of white tape. They are written as extra parts (build/parts/prop_*.png + meta.json, 4x, part px = sheet px x 4
with the sheet origin at 0, 0) so cast.py / Actor place them like any other drawing.

  prop_bus      side view of the team coach, facing left (it drives in from the right)
  prop_glove_L  a goalkeeper's glove drawn in the house style (bold ink, cel shading), and its mirror
  prop_glove_R
  prop_leg_mg   Bruno's sock-and-boot drawing with Maguire's white boots, for the lace-tying insert
  seat_*        seated players, from the standing house-style drawings
  prop_tape     a roll of white athletic tape, three-quarter view"""
import json, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont

INK = (22, 18, 20, 255)


def save(name, img, meta):
    img.save(f"build/parts/{name}.png")
    meta[name] = dict(src="props.py", box=[0, 0, img.width / 4, img.height / 4], off=[0.0, 0.0], scale=4,
                      size=[img.width, img.height], key="props:" + name)


def vgrad(w, h, top, bot):
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    return (np.float32(top) * (1 - t) + np.float32(bot) * t) * np.ones((1, w, 1), np.float32)


def bus():
    """2080 x 640 (4x): the coach. Dark body with a club-red sweep, tinted windows reflecting the red dusk sky."""
    W, H = 2080, 640
    body = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(body)
    # body silhouette: rounded box, the nose raked back at the windscreen
    poly = [(70, 70), (1990, 60), (2040, 100), (2045, 520), (2020, 555), (60, 560), (28, 520), (22, 170)]
    d.polygon(poly, fill=255)
    body = body.filter(ImageFilter.GaussianBlur(10)).point(lambda v: 255 if v > 128 else 0)
    m = np.asarray(body).astype(np.float32) / 255
    rgb = vgrad(W, H, (48, 34, 38), (16, 14, 16))
    img = np.dstack([rgb, m[..., None] * 255])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(im)
    # red sweep along the lower side, rising to the rear
    d.polygon([(40, 400), (1300, 400), (1700, 250), (2040, 230), (2042, 330), (1760, 350), (1420, 470), (40, 475)],
              fill=(196, 18, 32, 255))
    d.line([(40, 400), (1300, 400), (1700, 250), (2040, 230)], fill=(250, 190, 40, 255), width=6)
    # windows: one tinted band with pillars; the windscreen and the door at the front
    glass = vgrad(1800, 190, (170, 60, 40), (26, 16, 22))
    gl = Image.fromarray(np.clip(glass, 0, 255).astype(np.uint8)).convert("RGBA")
    im.alpha_composite(gl, (200, 110))
    for x in range(200, 2001, 225):
        d.rectangle([x - 7, 104, x + 7, 305], fill=(20, 16, 18, 255))
    d.rectangle([196, 104, 2004, 305], outline=INK, width=9)
    d.polygon([(40, 175), (72, 80), (180, 76), (180, 380), (40, 380)], fill=(120, 42, 36, 255), outline=INK)
    d.line([(40, 175), (72, 80), (180, 76), (180, 380), (40, 380), (40, 175)], fill=INK, width=9)
    d.rectangle([205, 320, 330, 548], fill=(34, 20, 24, 255), outline=INK, width=8)       # door
    d.line([(268, 322), (268, 546)], fill=INK, width=5)
    # reflections: a pale diagonal streak over the glass
    for x0 in (330, 980, 1550):
        d.polygon([(x0, 305), (x0 + 60, 110), (x0 + 110, 110), (x0 + 50, 305)], fill=(255, 200, 170, 60))
    # wordmark
    try:
        f = ImageFont.truetype("fonts/Oswald.ttf", 70)
        f.set_variation_by_axes([600])
    except Exception:
        f = ImageFont.load_default()
    d.text((520, 318), "MANCHESTER UNITED", font=f, fill=(245, 245, 245, 255))
    # lights: headlight (front), tail lights (rear)
    d.rounded_rectangle([34, 470, 110, 510], radius=12, fill=(255, 244, 200, 255), outline=INK, width=6)
    d.rounded_rectangle([2008, 420, 2040, 500], radius=8, fill=(230, 30, 30, 255), outline=INK, width=5)
    # skirt shadow and wheels
    d.rectangle([60, 540, 2030, 560], fill=(8, 8, 10, 255))
    for cx in (360, 1590, 1810):
        d.ellipse([cx - 118, 440, cx + 118, 676 - 36], fill=(10, 10, 12, 255))                  # arch
        d.ellipse([cx - 98, 452, cx + 98, 640], fill=(24, 24, 26, 255), outline=INK, width=8)   # tyre
        d.ellipse([cx - 52, 494, cx + 52, 598], fill=(150, 150, 156, 255), outline=INK, width=6)  # hub
        d.ellipse([cx - 16, 530, cx + 16, 562], fill=(70, 70, 74, 255))
    # the outline of the whole body
    a = np.asarray(im)[..., 3]
    edge = cv2.morphologyEx((a > 128).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((11, 11), np.uint8))
    out = np.asarray(im).copy()
    out[edge > 0] = INK
    return Image.fromarray(out, "RGBA")


def glove(right=False):
    """a goalkeeper's glove, drawn in the house style (bold ink, cel shading): back of the hand, fingers up. Lime
    backhand with a black finger-spine on each finger, grey latex showing at the palm edge, a black cuff with a lime
    strap. 480 x 680 part px (4x). right=True mirrors it."""
    W, H = 480, 680
    body = Image.new("L", (W, H), 0); d = ImageDraw.Draw(body)
    fingers = [(150, 62, 70), (228, 30, 72), (304, 44, 70), (372, 96, 60)]        # (centre x, top y, width)
    for cx, top, w in fingers:
        d.rounded_rectangle([cx - w / 2, top, cx + w / 2, 330], radius=w / 2, fill=255)
    d.rounded_rectangle([108, 250, 412, 520], radius=70, fill=255)                 # the hand
    thumb = Image.new("L", (W, H), 0); dt = ImageDraw.Draw(thumb)
    dt.rounded_rectangle([60, 250, 140, 470], radius=40, fill=255)
    thumb = thumb.rotate(28, center=(115, 440), resample=Image.BICUBIC)
    body = Image.fromarray(np.maximum(np.asarray(body), np.asarray(thumb)))
    d = ImageDraw.Draw(body)
    d.rounded_rectangle([118, 480, 402, 660], radius=26, fill=255)                 # cuff
    m = np.asarray(body).astype(np.float32) / 255
    lime = np.float32([196, 238, 30]); black = np.float32([26, 26, 30]); grey = np.float32([176, 180, 176])
    img = np.zeros((H, W, 3), np.float32) + lime
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # the finger spines (black stripes) and the backhand panel
    lay = Image.new("L", (W, H), 0); dl = ImageDraw.Draw(lay)
    for cx, top, w in fingers:
        dl.rounded_rectangle([cx - w * 0.18, top + 18, cx + w * 0.18, 300], radius=w * 0.18, fill=255)
    dl.polygon([(150, 330), (372, 330), (390, 400), (300, 470), (130, 440)], fill=255)
    k = np.asarray(lay).astype(np.float32)[..., None] / 255
    img = img * (1 - k) + black * k
    # white brand swoosh on the backhand
    sw = Image.new("L", (W, H), 0); ds = ImageDraw.Draw(sw)
    ds.line([(180, 420), (250, 405), (340, 360)], fill=255, width=22, joint="curve")
    k = np.asarray(sw).astype(np.float32)[..., None] / 255
    img = img * (1 - k) + np.float32([245, 245, 240]) * k
    # latex showing at the thumb and the palm edge
    k = (np.asarray(thumb).astype(np.float32)[..., None] / 255) * (xx < 150)[..., None] * 0.9
    img = img * (1 - k) + grey * k
    # the cuff: black with a lime strap and a white stripe
    cuff = (yy > 486)[..., None].astype(np.float32)
    img = img * (1 - cuff) + black * cuff
    strap = ((yy > 530) & (yy < 610) & (xx > 150) & (xx < 402))[..., None].astype(np.float32)
    img = img * (1 - strap) + lime * strap
    stripe = ((yy > 560) & (yy < 578) & (xx > 150) & (xx < 402))[..., None].astype(np.float32)
    img = img * (1 - stripe) + np.float32([245, 245, 240]) * stripe
    # cel shading: a darker band down the right of every shape, a highlight on the left
    shade = np.clip((xx - 300) / 140, 0, 1) * 0.28 + np.clip((yy - 380) / 300, 0, 1) * 0.1
    img = img * (1 - shade[..., None])
    hi = np.exp(-(((xx - 190) / 70) ** 2 + ((yy - 200) / 150) ** 2)) * 0.12
    img = np.clip(img + hi[..., None] * 255, 0, 255)
    # ink: the silhouette outline, the finger gaps, the cuff line
    sil = (m > 0.5).astype(np.uint8)
    edge = cv2.morphologyEx(sil, cv2.MORPH_GRADIENT, np.ones((13, 13), np.uint8)) > 0
    inner = Image.new("L", (W, H), 0); di = ImageDraw.Draw(inner)
    for (c0, _, w0), (c1, _, w1) in zip(fingers, fingers[1:]):
        xg = (c0 + w0 / 2 + c1 - w1 / 2) / 2
        di.line([(xg, 120), (xg, 320)], fill=255, width=9)
    di.line([(122, 486), (398, 486)], fill=255, width=9)
    di.arc([60, 300, 220, 520], 200, 300, fill=255, width=8)                        # the thumb's crease
    ink = edge | ((np.asarray(inner) > 128) & (sil > 0))
    img[ink] = np.float32(INK[:3])
    out = np.dstack([img, (m * 255)]).astype(np.uint8)
    im = Image.fromarray(out, "RGBA")
    return im.transpose(Image.FLIP_LEFT_RIGHT) if right else im


def white_boots(part):
    """Bruno's leg drawing (sock + boot) with Maguire's boots: white with red trim (as on his outfits sheet)"""
    a = np.asarray(Image.open(f"build/parts/{part}.png").convert("RGBA")).astype(np.float32)
    rgb = a[..., :3]
    hsv = cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    H = a.shape[0]
    boot = (np.arange(H)[:, None] > 0.72 * H) * np.ones((1, a.shape[1]))
    red = (((hsv[..., 0] < 10) | (hsv[..., 0] > 170)) & (hsv[..., 1] > 120)) & (boot > 0)
    white = ((hsv[..., 1] < 50) & (hsv[..., 2] > 170)) & (boot > 0)
    v = (hsv[..., 2] / 255.0)[..., None]
    out = rgb.copy()
    k = cv2.GaussianBlur(red.astype(np.float32), (0, 0), 1.0)[..., None]
    out = out * (1 - k) + np.float32([246, 244, 238]) * (0.55 + 0.5 * v) * k
    k = cv2.GaussianBlur(white.astype(np.float32), (0, 0), 1.0)[..., None]
    out = out * (1 - k) + np.float32([214, 26, 38]) * k
    return Image.fromarray(np.dstack([np.clip(out, 0, 255), a[..., 3]]).astype(np.uint8), "RGBA")


def tape():
    """a roll of white tape, 3/4 view: outer rim, the flat face with a cardboard core"""
    W, H = 520, 420
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([40, 150, 480, 400], fill=(205, 205, 200, 255), outline=INK, width=10)       # side (thickness)
    d.rectangle([40, 100, 480, 275], fill=(205, 205, 200, 255))
    d.line([(40, 100), (40, 275)], fill=INK, width=10); d.line([(480, 100), (480, 275)], fill=INK, width=10)
    d.ellipse([40, 20, 480, 250], fill=(248, 248, 244, 255), outline=INK, width=10)        # face
    d.ellipse([150, 80, 370, 190], fill=(176, 130, 80, 255), outline=INK, width=8)         # core
    d.ellipse([175, 95, 345, 175], fill=(40, 30, 26, 255))
    for r in (0.72, 0.86):
        d.arc([260 - 220 * r, 135 - 115 * r, 260 + 220 * r, 135 + 115 * r], 200, 340, fill=(200, 200, 196, 255), width=4)
    return im


# sheet rows (y) of each standing drawing: waist (shorts top), hem (shorts bottom), the knee, the feet
SEAT = {"br_b_match": (550, 688, 706, 995), "cu_b_match": (562, 690, 708, 985), "km_b_match": (572, 692, 712, 990),
        "mg2_b_match": (262, 306, 318, 412)}
SEAT_NAME = {"br_b_match": "seat_br", "cu_b_match": "seat_cu", "km_b_match": "seat_km", "mg2_b_match": "seat_mg"}
# the plain stretch of sock (sheet rows) that gets longer: these cartoon bodies have short shins, and a seated player's
# shin runs from the bench edge to the floor, about half as long as the torso and head
SOCK = {"br_b_match": (838, 896), "cu_b_match": (852, 886), "km_b_match": (838, 884), "mg2_b_match": (358, 384)}
SHIN = 0.5


def seated(part, meta):
    """a front-view seated pose from a standing drawing: seen from the front, a seated player's thighs point at
    the camera, so the shorts become a short lap and the knees sit right under the hem. Keep everything above the
    waist, squash the shorts to 60 %, drop the thighs down to the knee, keep the knees, socks and boots.
    Face landmarks (above the waist) keep their sheet coordinates. Returns (image, new feet y)."""
    waist, hem, knee, feet = SEAT[part]
    a = np.asarray(Image.open(f"build/parts/{part}.png").convert("RGBA")).astype(np.float32)
    oy = meta[part]["off"][1]
    K = meta[part].get("scale", 4)                          # part px per sheet px
    ov, pad = int(round(14 * K / 4)), int(round(6 * K / 4))
    r = lambda y: int(round((y - oy) * K))
    top = a[:r(waist)]
    shorts = a[r(waist):r(hem) + pad]
    sh = cv2.resize(shorts, (shorts.shape[1], int(shorts.shape[0] * 0.6)), interpolation=cv2.INTER_AREA)
    s0, s1 = SOCK[part]
    lap = waist + 0.6 * (hem - waist + 1.5) - 3.5
    shin_now = (feet - knee)
    extra = max(0.0, SHIN * (lap - oy) - shin_now)
    mid = a[r(s0):r(s1)]
    mid = cv2.resize(mid, (mid.shape[1], int(round(mid.shape[0] + extra * K))), interpolation=cv2.INTER_CUBIC)
    legs = np.concatenate([a[r(knee):r(s0)], mid, a[r(s1):]], 0)
    H = top.shape[0] + sh.shape[0] + legs.shape[0] - ov
    out = np.zeros((H, a.shape[1], 4), np.float32)
    y = 0
    out[:top.shape[0]] = top; y = top.shape[0]
    # the legs go in first, the lap (shorts) over their top edge
    ly = y + sh.shape[0] - ov
    out[ly:ly + legs.shape[0]] = legs
    pm = sh.copy(); pm[..., :3] *= pm[..., 3:4] / 255
    base = out[y:y + sh.shape[0]]
    bpm = base.copy(); bpm[..., :3] *= bpm[..., 3:4] / 255
    al = pm[..., 3:4] / 255
    comb = pm + bpm * (1 - al)
    ca = comb[..., 3:4] / 255
    comb[..., :3] = np.where(ca > 1e-3, comb[..., :3] / np.maximum(ca, 1e-3), 0)
    out[y:y + sh.shape[0]] = comb
    new_feet = feet - (knee - hem) - 0.4 * (hem - waist) - 14 / 4 + 6 / 4 * 0.6 + extra
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA"), new_feet


def main():
    meta = json.load(open("build/parts/meta.json"))
    for p in SEAT:
        im, fy = seated(p, meta)
        name = SEAT_NAME[p]
        im.save(f"build/parts/{name}.png")
        waist, hem = SEAT[p][:2]
        meta[name] = dict(meta[p], src="props.py", key="props:" + name, size=[im.width, im.height], feet=fy,
                          lap=waist + 0.6 * (hem - waist + 1.5) - 3.5)
        print(name, "feet", round(fy, 1), "lap", round(meta[name]["lap"], 1))
    save("prop_bus", bus(), meta)
    save("prop_glove_L", glove(), meta)
    save("prop_glove_R", glove(right=True), meta)
    im = white_boots("hs_leg_R")
    im.save("build/parts/prop_leg_mg.png")
    meta["prop_leg_mg"] = dict(meta["hs_leg_R"], src="props.py", key="props:prop_leg_mg")
    save("prop_tape", tape(), meta)
    json.dump(meta, open("build/parts/meta.json", "w"), indent=1)
    print("props", [k for k in meta if k.startswith("prop_")])


if __name__ == "__main__":
    main()

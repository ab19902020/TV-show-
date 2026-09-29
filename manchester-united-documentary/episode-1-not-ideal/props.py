"""Props for the scene 3 inserts, drawn to sit with the inked art: the away team coach, the goalkeeper's gloves and
a roll of white tape. They are written as extra parts (build/parts/prop_*.png + meta.json, 4x, part px = sheet px x 4
with the sheet origin at 0, 0) so cast.py / Actor place them like any other drawing.

  prop_bus      side view of the team coach, facing left (it drives in from the right)
  prop_glove_L  Maguire's open-hand drawings recoloured: grey latex palm, lime / black wrist strap
  prop_glove_R
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


def glove(src):
    """recolour an open-hand drawing into a goalkeeper glove: skin -> grey latex, the wrist -> a lime strap"""
    a = np.asarray(Image.open(src).convert("RGBA")).astype(np.float32)
    rgb, al = a[..., :3], a[..., 3]
    hsv = cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.float32)
    skin = (hsv[..., 1] > 40) & (hsv[..., 2] > 110) & (al > 10)
    lum = hsv[..., 2] / 255.0
    latex = np.stack([225 * lum, 228 * lum, 222 * lum], -1) + 18
    out = rgb.copy()
    k = cv2.GaussianBlur(skin.astype(np.float32), (0, 0), 1.2)[..., None]
    out = out * (1 - k) + latex * k
    H, W = al.shape
    ys = np.nonzero(al.max(1) > 10)[0]
    y0, y1 = ys.min(), ys.max()
    strap = (np.arange(H)[:, None] > y0 + 0.74 * (y1 - y0)) & (al > 10) & skin
    band = (np.arange(H)[:, None] > y0 + 0.83 * (y1 - y0)) & (np.arange(H)[:, None] < y0 + 0.88 * (y1 - y0))
    col = np.where(band[..., None], np.float32([20, 20, 22]), np.float32([196, 238, 30]) * (0.75 + 0.25 * lum[..., None]))
    s = cv2.GaussianBlur(strap.astype(np.float32), (0, 0), 1.0)[..., None]
    out = out * (1 - s) + col * s
    # the strap's top edge gets an ink line
    top = np.zeros((H, W), np.uint8)
    yl = int(y0 + 0.74 * (y1 - y0))
    top[yl - 4:yl + 4] = 1
    top &= (al > 200)
    out[top > 0] = INK[:3]
    return Image.fromarray(np.dstack([np.clip(out, 0, 255), al]).astype(np.uint8), "RGBA")


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
        "mg_t_front": (357, 448, 488, 655)}
# the plain stretch of sock (sheet rows) that gets longer: these cartoon bodies have short shins, and a seated player's
# shin runs from the bench edge to the floor, about half as long as the torso and head
SOCK = {"br_b_match": (838, 896), "cu_b_match": (852, 886), "km_b_match": (838, 884), "mg_t_front": (530, 600)}
SHIN = 0.5


def seated(part, meta):
    """a front-view seated pose from a standing drawing: seen from the front, a seated player's thighs point at
    the camera, so the shorts become a short lap and the knees sit right under the hem. Keep everything above the
    waist, squash the shorts to 60 %, drop the thighs down to the knee, keep the knees, socks and boots.
    Face landmarks (above the waist) keep their sheet coordinates. Returns (image, new feet y)."""
    waist, hem, knee, feet = SEAT[part]
    a = np.asarray(Image.open(f"build/parts/{part}.png").convert("RGBA")).astype(np.float32)
    oy = meta[part]["off"][1]
    r = lambda y: int(round((y - oy) * 4))
    top = a[:r(waist)]
    shorts = a[r(waist):r(hem) + 6]
    sh = cv2.resize(shorts, (shorts.shape[1], int(shorts.shape[0] * 0.6)), interpolation=cv2.INTER_AREA)
    s0, s1 = SOCK[part]
    lap = waist + 0.6 * (hem - waist + 1.5) - 3.5
    shin_now = (feet - knee)
    extra = max(0.0, SHIN * (lap - oy) - shin_now)
    mid = a[r(s0):r(s1)]
    mid = cv2.resize(mid, (mid.shape[1], int(round(mid.shape[0] + extra * 4))), interpolation=cv2.INTER_CUBIC)
    legs = np.concatenate([a[r(knee):r(s0)], mid, a[r(s1):]], 0)
    H = top.shape[0] + sh.shape[0] + legs.shape[0] - 14
    out = np.zeros((H, a.shape[1], 4), np.float32)
    y = 0
    out[:top.shape[0]] = top; y = top.shape[0]
    # the legs go in first, the lap (shorts) over their top edge
    ly = y + sh.shape[0] - 14
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
        name = "seat_" + p.split("_")[0]
        im.save(f"build/parts/{name}.png")
        waist, hem = SEAT[p][:2]
        meta[name] = dict(meta[p], src="props.py", key="props:" + name, size=[im.width, im.height], feet=fy,
                          lap=waist + 0.6 * (hem - waist + 1.5) - 3.5)
        print(name, "feet", round(fy, 1), "lap", round(meta[name]["lap"], 1))
    save("prop_bus", bus(), meta)
    save("prop_glove_L", glove("build/parts/mg_hand_L.png"), meta)
    save("prop_glove_R", glove("build/parts/mg_hand_R.png"), meta)
    save("prop_tape", tape(), meta)
    json.dump(meta, open("build/parts/meta.json", "w"), indent=1)
    print("props", [k for k in meta if k.startswith("prop_")])


if __name__ == "__main__":
    main()

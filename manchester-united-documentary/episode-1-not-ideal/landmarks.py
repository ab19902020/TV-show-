"""Eye and mouth landmarks of every head and body drawing, in SHEET coordinates (1x).

Detected from the artwork itself: the sclera (bright, unsaturated) blobs in the upper face give the eyes, the
lips (red-pink) blob in the lower face gives the mouth. Every result is drawn on build/landmarks_check.jpg and
anything the detector gets wrong is fixed in OVERRIDE. Output: build/landmarks.json
{part: {eyes: [[x, y, w, h], [x, y, w, h]] (left to right), mouth: [x, y, w, h], face: [x0, y0, x1, y1]}}"""
import json, sys, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage
import parts

# manual corrections (sheet coords), filled in after looking at landmarks_check.jpg
OVERRIDE = {}

def analyse(name, face_box=None):
    sp = parts.SPEC[name]
    rgba = SHEETS.setdefault(sp["src"], parts.load(sp["src"])[0])
    rgb, a, (X0, Y0) = parts.cut(name, sp, SHEETS)
    ys, xs = np.nonzero(a > 0.5)
    x0, y0, x1, y1 = xs.min(), ys.min(), xs.max(), ys.max()
    if face_box is not None:           # restrict to the head of a full-body drawing (sheet coords)
        fx0, fy0, fx1, fy1 = face_box
        x0, y0, x1, y1 = fx0 - X0, fy0 - Y0, fx1 - X0, fy1 - Y0
    h, w = y1 - y0, x1 - x0
    hsv = cv2.cvtColor(rgb.astype(np.uint8), cv2.COLOR_RGB2HSV).astype(np.int32)
    Hh, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    r, g, b = [rgb[..., i].astype(np.int32) for i in range(3)]
    sol = a > 0.5
    # eyes: sclera in the band 25-65 % down the head
    band = np.zeros_like(sol); band[y0 + int(0.25 * h):y0 + int(0.66 * h), x0:x1] = True
    scl = sol & band & (V > 175) & (S < 70)
    scl = ndimage.binary_opening(scl, iterations=1)
    lab, n = ndimage.label(scl)
    blobs = []
    for i, sl in enumerate(ndimage.find_objects(lab)):
        m = lab[sl] == i + 1
        sz = m.sum()
        if sz < max(4, 0.0006 * w * h): continue
        cy, cx = ndimage.center_of_mass(m)
        blobs.append((sz, sl[1].start + cx, sl[0].start + cy, sl[1].stop - sl[1].start, sl[0].stop - sl[0].start))
    blobs.sort(reverse=True)
    eyes = sorted(blobs[:2], key=lambda t: t[1])
    # mouth: lips = red-pink in the lower 45 % of the head, central 70 %
    band2 = np.zeros_like(sol); band2[y0 + int(0.55 * h):y1, x0 + int(0.15 * w):x1 - int(0.15 * w)] = True
    lips = sol & band2 & (r > 130) & (r - g > 45) & (r - b > 25) & (V > 110)
    lips = ndimage.binary_opening(lips, iterations=1)
    lab2, n2 = ndimage.label(lips)
    mouth = None
    if n2:
        sizes = ndimage.sum(np.ones_like(lab2), lab2, range(1, n2 + 1))
        k = int(np.argmax(sizes)) + 1
        yy, xx = np.nonzero(lab2 == k)
        mouth = [float(xx.mean() + X0), float(yy.mean() + Y0), float(xx.max() - xx.min() + 1), float(yy.max() - yy.min() + 1)]
    res = dict(eyes=[[float(e[1] + X0), float(e[2] + Y0), float(e[3]), float(e[4])] for e in eyes], mouth=mouth,
               face=[float(x0 + X0), float(y0 + Y0), float(x1 + X0), float(y1 + Y0)])
    res.update(OVERRIDE.get(name, {}))
    return res, rgb, a, (X0, Y0)

SHEETS = {}
# heads of full-body drawings: sheet box of the head only
BODY_FACE = {"ck_b_suit": (1165, 15, 1335, 250), "ck_b_track": (685, 15, 860, 250), "br_b_match": (1110, 10, 1300, 215),
             "cu_b_match": (1190, 20, 1385, 235), "js_b_suit": (60, 10, 200, 150),
             "jr_b_grey": (45, 48, 110, 110), "jr_b_suit": (170, 48, 235, 110), "av_b_suit": (430, 55, 500, 120),
             "av_b_jumper": (545, 55, 625, 120), "jg_b_suit": (805, 55, 875, 120), "jg_b_jumper": (925, 55, 995, 120),
             "om_b_suit": (1190, 55, 1260, 120)}
POSE_FACE = {"js_p_point": (60, 695, 125, 780), "js_p_tablet": (215, 695, 280, 780), "js_p_crossed": (390, 690, 455, 775),
             "js_p_chin": (540, 695, 605, 780), "js_p_present": (720, 692, 785, 777), "js_p_phone": (1195, 690, 1260, 775),
             "js_p_shrug": (1395, 690, 1460, 775), "js_p_clap": (1060, 690, 1125, 775)}

def targets():
    t = [n for n in parts.SPEC if "_h_" in n] + ["mg_t_front", "mg_t_q34"] + list(BODY_FACE) + list(POSE_FACE)
    return [n for n in t if n in parts.SPEC]

def main():
    out, tiles = {}, []
    for n in targets():
        fb = BODY_FACE.get(n) or POSE_FACE.get(n)
        if n == "mg_t_front": fb = (100, 12, 220, 150)
        if n == "mg_t_q34": fb = (905, 12, 1030, 150)
        res, rgb, a, (X0, Y0) = analyse(n, fb)
        out[n] = res
        im = Image.fromarray((rgb * a[..., None] + np.array([255, 0, 255]) * (1 - a[..., None])).astype(np.uint8))
        fx0, fy0, fx1, fy1 = [int(v) for v in res["face"]]
        im = im.crop((fx0 - X0 - 4, fy0 - Y0 - 4, fx1 - X0 + 4, fy1 - Y0 + 4))
        k = 300 / max(im.size); im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        ox, oy = fx0 - 4, fy0 - 4
        for (ex, ey, ew, eh) in res["eyes"]:
            d.ellipse([((ex - ew / 2) - ox) * k, ((ey - eh / 2) - oy) * k, ((ex + ew / 2) - ox) * k, ((ey + eh / 2) - oy) * k], outline=(0, 255, 0), width=2)
        if res["mouth"]:
            mx, my, mw, mh = res["mouth"]
            d.rectangle([((mx - mw / 2) - ox) * k, ((my - mh / 2) - oy) * k, ((mx + mw / 2) - ox) * k, ((my + mh / 2) - oy) * k], outline=(0, 255, 255), width=2)
        d.text((3, 3), n, fill=(255, 255, 0))
        tiles.append(im)
    json.dump(out, open("build/landmarks.json", "w"), indent=1)
    cols = 8
    s = Image.new("RGB", (310 * cols, 310 * ((len(tiles) + cols - 1) // cols)), (30, 30, 30))
    for i, t in enumerate(tiles): s.paste(t, ((i % cols) * 310, (i // cols) * 310))
    s.save("build/landmarks_check.jpg", quality=85)
    print(len(tiles), "heads")

if __name__ == "__main__":
    main()

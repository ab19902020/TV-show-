"""Cut every drawing out of the 4x upscaled sheets (build/up/<sheet>.png) -> build/parts/<name>.png (RGBA, 4x) + meta.json.

Each part is given by a rough box in 1x sheet coordinates (the sheets are 941 x 1672; Rio's is 1122 x 1402). Inside the
box the paper is found by its colour (light, unsaturated) and flood-filled from the box edge, which also removes the grey
floor shadows; paper trapped inside the figure (the gap between an arm and the body, hands in pockets) is removed when
it is the paper's own flat colour. The largest remaining piece is the drawing. Its edge is pulled in by a pixel so no
paper fringe is left outside the ink line.  python3 parts.py  ->  qa/parts.jpg (every part on magenta)"""
import os, json, numpy as np, cv2
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.abspath(__file__))
UP = os.path.join(ROOT, "build/up"); OUT = os.path.join(ROOT, "build/parts"); K = 4

# name: (sheet, (x0, y0, x1, y1) 1x box)
PARTS = {
    # Evra (model sheet, actions, face sheet)
    "e_front": ("evra", (18, 198, 264, 808)), "e_34": ("evra", (262, 198, 492, 808)),
    "e_side": ("evra", (494, 198, 670, 808)), "e_back": ("evra", (678, 198, 926, 808)),
    "e_casual": ("evra", (18, 925, 302, 1588)), "e_swim": ("evra", (322, 925, 612, 1588)), "e_robe": ("evra", (622, 925, 922, 1588)),
    "e_tired": ("evra-actions", (55, 100, 435, 612)), "e_optimism": ("evra-actions", (515, 100, 905, 604)),
    "e_tinylunch": ("evra-actions", (55, 655, 445, 1112)), "e_kick": ("evra-actions", (468, 655, 932, 1112)),
    "e_pool": ("evra-actions", (18, 1165, 468, 1612)), "e_sauna": ("evra-actions", (498, 1165, 905, 1622)),
    "eb_neutral": ("evra-face", (18, 124, 314, 470)), "eb_optimistic": ("evra-face", (324, 124, 619, 470)),
    "eb_suspicious": ("evra-face", (629, 124, 922, 470)), "eb_disappointed": ("evra-face", (18, 515, 314, 860)),
    "eb_exhausted": ("evra-face", (324, 515, 619, 860)), "eb_laugh": ("evra-face", (629, 515, 922, 860)),
    # Ronaldo
    "r_front": ("ronaldo", (16, 172, 264, 848)), "r_34": ("ronaldo", (262, 172, 490, 848)),
    "r_side": ("ronaldo", (498, 172, 670, 848)), "r_back": ("ronaldo", (688, 172, 927, 848)),
    "r_casual": ("ronaldo", (38, 985, 312, 1648)), "r_swim": ("ronaldo", (333, 985, 614, 1648)), "r_robe": ("ronaldo", (626, 985, 920, 1648)),
    "r_stance": ("ronaldo-actions", (22, 132, 468, 688)), "r_invite": ("ronaldo-actions", (476, 132, 928, 688)),
    "r_lunch": ("ronaldo-actions", (22, 692, 468, 1188)), "r_kick": ("ronaldo-actions", (476, 692, 928, 1188)),
    "r_laps": ("ronaldo-actions", (12, 1192, 472, 1660)), "r_exercise": ("ronaldo-actions", (476, 1192, 928, 1662)),
    "rb_neutral": ("ronaldo-face", (18, 172, 320, 574)), "rb_invite": ("ronaldo-face", (323, 172, 623, 574)),
    "rb_intense": ("ronaldo-face", (626, 172, 925, 574)), "rb_smug": ("ronaldo-face", (18, 637, 320, 1030)),
    "rb_eager": ("ronaldo-face", (323, 637, 623, 1030)), "rb_confused": ("ronaldo-face", (626, 637, 925, 1030)),
    # Rio (his approved sheet, from the G-Unit film)
    "rio_hero": ("rio", (8, 108, 292, 842)), "rio_front": ("rio", (300, 145, 440, 458)), "rio_34": ("rio", (465, 145, 600, 458)),
    "rio_34r": ("rio", (778, 145, 912, 458)), "rio_folded": ("rio", (603, 1058, 688, 1194)),
    "rio_warning": ("rio", (698, 1058, 812, 1194)), "rio_shrug": ("rio", (806, 1058, 970, 1194)),
    "rio_laugh": ("rio", (970, 1058, 1084, 1197)), "rio_back": ("rio", (935, 140, 1075, 462)),
}
HOLES = {"r_exercise": [(600, 1438), (770, 1425)], "e_casual": [(88, 1232)]}
# the prop atlas has its own alpha: (x0, y0, x1, y1) 1x
PROPS = {"plate_full": (12, 118, 348, 350), "plate_empty": (352, 118, 698, 350), "glass": (726, 106, 910, 360),
         "pitcher": (55, 410, 360, 780), "fork": (474, 408, 546, 790), "knife": (764, 400, 832, 795), "ball": (16, 846, 324, 1146),
         "towel": (326, 890, 646, 1130), "bucket": (626, 870, 941, 1150), "drops": (736, 1245, 905, 1505)}


def cut(sheet, box, name=''):
    up = np.asarray(Image.open(os.path.join(UP, sheet + ".png")).convert("RGB"))
    x0, y0, x1, y1 = box
    rgb = up[y0 * K:y1 * K, x0 * K:x1 * K].copy()
    mn = rgb.min(2).astype(int); mx = rgb.max(2).astype(int)
    paper = (mn > 186) & ((mx - mn) < 30)
    lab, n = ndi.label(paper)
    edge = np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]); edge = edge[edge > 0]
    bg = np.isin(lab, edge)
    pc = np.median(rgb[bg], axis=0) if bg.any() else np.float32([242, 246, 249])
    # trapped paper (the gap between an arm and the body): marked by hand with a seed point inside it (HOLES), because
    # on the white action sheets the paper is the same white as eyes, trainers and logos
    for sx, sy in HOLES.get(name, ()):
        i = lab[int((sy - y0) * K), int((sx - x0) * K)]
        if i: bg |= lab == i
    fg = ~bg
    l2, n2 = ndi.label(fg)
    if n2 == 0: raise ValueError(f"nothing in {sheet} {box}")
    sizes = np.bincount(l2.ravel()); sizes[0] = 0
    keep = l2 == np.argmax(sizes)
    keep = ndi.binary_erosion(keep, iterations=2)                      # off the paper fringe, onto the ink line
    ys, xs = np.nonzero(keep)
    a0, b0, a1, b1 = max(0, xs.min() - 4), max(0, ys.min() - 4), min(keep.shape[1], xs.max() + 5), min(keep.shape[0], ys.max() + 5)
    alpha = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 0.9)[b0:b1, a0:a1]
    # colour under the soft edge: pull the nearest inside colour outwards, so the edge is ink, never paper
    core = ndi.binary_erosion(keep, iterations=1)[b0:b1, a0:a1]
    idx = ndi.distance_transform_edt(~core, return_distances=False, return_indices=True)
    c = rgb[b0:b1, a0:a1][idx[0], idx[1]]
    return np.dstack((c, np.uint8(np.clip(alpha * 255, 0, 255)))), (x0 + a0 / K, y0 + b0 / K)


def cut_prop(box):
    src = np.asarray(Image.open(os.path.join(ROOT, "src/art/props.png")).convert("RGBA"))
    up = np.asarray(Image.open(os.path.join(UP, "props.png")).convert("RGB"))
    x0, y0, x1, y1 = box
    a = cv2.resize(src[y0:y1, x0:x1, 3], ((x1 - x0) * K, (y1 - y0) * K), interpolation=cv2.INTER_CUBIC)
    rgb = up[y0 * K:y1 * K, x0 * K:x1 * K]
    # keep the main object only (the atlas has stray specks between objects)
    lab, n = ndi.label(a > 40)
    if n > 1:
        sizes = np.bincount(lab.ravel()); sizes[0] = 0
        big = np.isin(lab, np.nonzero(sizes > sizes.max() * 0.04)[0])
        a = np.where(ndi.binary_dilation(big, iterations=3), a, 0).astype(np.uint8)
    ys, xs = np.nonzero(a > 10)
    a0, b0, a1, b1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
    return np.dstack((rgb[b0:b1, a0:a1], a[b0:b1, a0:a1])), (x0 + a0 / K, y0 + b0 / K)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True); os.makedirs(os.path.join(ROOT, "qa"), exist_ok=True)
    mp = os.path.join(OUT, "meta.json"); meta = json.load(open(mp)) if os.path.exists(mp) else {}
    have = lambda sh: os.path.exists(os.path.join(UP, sh + ".png"))
    for name, (sheet, box) in PARTS.items():
        if not have(sheet): continue
        rgba, off = cut(sheet, box, name)
        Image.fromarray(rgba).save(os.path.join(OUT, name + ".png"))
        meta[name] = {"sheet": sheet, "off": [float(off[0]), float(off[1])], "scale": K, "size": [rgba.shape[1], rgba.shape[0]]}
    for name, box in PROPS.items():
        if not have("props"): break
        rgba, off = cut_prop(box)
        Image.fromarray(rgba).save(os.path.join(OUT, name + ".png"))
        meta[name] = {"sheet": "props", "off": [float(off[0]), float(off[1])], "scale": K, "size": [rgba.shape[1], rgba.shape[0]]}
    json.dump(meta, open(os.path.join(OUT, "meta.json"), "w"), indent=1)
    names = list(meta); cw, ch = 220, 300
    sheet = Image.new("RGB", (cw * 8, ch * ((len(names) + 7) // 8)), "#ff00ff"); d = ImageDraw.Draw(sheet)
    for i, n in enumerate(names):
        a = Image.open(os.path.join(OUT, n + ".png")); a.thumbnail((cw - 8, ch - 22))
        x, y = (i % 8) * cw, (i // 8) * ch
        sheet.paste(a, (x + (cw - a.width) // 2, y + 2), a); d.text((x + 4, y + ch - 18), n, fill="black")
    sheet.save(os.path.join(ROOT, "qa/parts.jpg"), quality=90)
    print("cut", len(meta), "parts")

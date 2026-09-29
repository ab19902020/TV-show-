"""Cut every character part used in scenes 1-4 out of the source sheets and upscale it 4x.

Each part is a box on a sheet (sheet pixels). The matte comes from the sheet's own alpha (house-style sheets are
RGBA) or, for the cream-paper Maguire sheets, from a flood fill of the paper. Where two drawings touch on the
sheet (ears, hands) the box holds several markers and a watershed on the distance transform splits them at the
narrowest contact.

Output: build/parts/<name>.png (RGBA, 4x) and build/parts/meta.json {name: {src, box, off:[x,y], scale:4}} so a
sheet coordinate (x, y) maps to part pixel ((x - off_x) * 4, (y - off_y) * 4)."""
import json, os, sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage
from skimage.segmentation import watershed

CH = "../assets/characters/"
BG = "../assets/backgrounds/"
G = CH + "owners-and-executives/house-style/owners-and-executives__group-outfits-faces-actions__20260928T160124__75eb227c.png"
J = CH + "jason-wilcox/house-style/jason-wilcox__combined-outfits-faces-actions__20260928T155327__2ce63c58.png"
CK_F, CK_O, CK_M = (CH + "michael-carrick/" + n for n in ("face-visemes.png", "outfits.png", "movement.png"))
BR_F, BR_O = CH + "bruno-fernandes/face-visemes.png", CH + "bruno-fernandes/outfits.png"
CU_F, CU_O = CH + "matheus-cunha/face-visemes.png", CH + "matheus-cunha/outfits.png"
MG_L = CH + "harry-maguire/other-styles/harry-maguire__lip-sync-expressions__20260928T100945__0784fbdd.png"
MG_T = CH + "harry-maguire/other-styles/harry-maguire__turnaround-cutout-parts__20260928T100943__7710b02a.png"
GEN, ANI = "RealESRGAN_x4plus", "RealESRGAN_x4plus_anime_6B"

SPEC = {}
def part(name, src, box, mode="alpha", model=GEN, markers=None):
    SPEC[name] = dict(src=src, box=box, mode=mode, model=model, markers=markers)

def row(prefix, src, items, **kw):
    for i, b in enumerate(items): part(f"{prefix}{i}", src, b, **kw)

# --- Michael Carrick: face sheet heads, 9 mouths, suit + tracksuit bodies, tracksuit arms ---
for n, b in dict(smile=(92, 12, 369, 360), q34=(441, 10, 711, 358), profR=(786, 14, 1093, 363), profL=(1156, 13, 1462, 363),
                 neutral=(93, 365, 369, 712), frown=(454, 364, 728, 712), surprised=(806, 365, 1080, 714),
                 wink=(1171, 366, 1446, 714)).items():
    part("ck_h_" + n, CK_F, b)
row("ck_m", CK_F, [(10, 725, 191, 845), (193, 725, 362, 851), (365, 724, 535, 848), (538, 725, 699, 844), (702, 726, 856, 844),
                   (859, 727, 1027, 844), (1030, 728, 1192, 844), (1196, 727, 1368, 847), (1371, 725, 1531, 853)])
part("ck_b_suit", CK_O, (1055, 0, 1480, 1010))
part("ck_b_track", CK_O, (580, 0, 1000, 1005))
part("ck_arm_palm_t", CK_M, (522, 305, 684, 470))
part("ck_arm_reach_t", CK_M, (895, 300, 1015, 520))

# --- Bruno: 8 heads (touching at the ears -> watershed), 10 mouths, match kit ---
bh = [("smile", 110), ("front2", 318), ("q34", 510), ("profL", 690), ("angry", 878), ("surprised", 1068), ("wink", 1245), ("grin", 1432)]
for i, (n, cx) in enumerate(bh):
    x0 = 0 if i == 0 else (bh[i - 1][1] + cx) // 2 - 60
    x1 = 1536 if i == len(bh) - 1 else (bh[i + 1][1] + cx) // 2 + 60
    part("br_h_" + n, BR_F, (x0, 60, x1, 400), markers=[(c, 230) for _, c in bh])
row("br_m", BR_F, [(20, 468, 164, 575), (176, 467, 316, 580), (322, 467, 474, 576), (482, 467, 619, 568), (624, 466, 763, 574),
                   (770, 467, 903, 569), (911, 469, 1056, 573), (1064, 467, 1209, 569), (1216, 466, 1360, 573), (1373, 457, 1521, 576)])
part("br_b_match", BR_O, (1000, 0, 1445, 1005))

# --- Matheus Cunha ---
for n, b in dict(front=(70, 9, 363, 345), q34=(409, 7, 701, 345), profR=(751, 10, 1088, 345), profL=(1140, 10, 1484, 345),
                 neutral=(114, 360, 394, 705), frown=(465, 360, 747, 705), surprised=(782, 360, 1064, 705),
                 wink=(1130, 360, 1411, 705)).items():
    part("cu_h_" + n, CU_F, b)
part("cu_b_match", CU_O, (1065, 5, 1512, 1005))

# --- Jason Wilcox (suit sheet): waist-up action poses, full-body suit, 9 mouths ---
for n, b in dict(point=(8, 691, 175, 1015), tablet=(174, 693, 341, 1017), crossed=(352, 689, 488, 1018), chin=(505, 695, 641, 1019),
                 present=(664, 691, 842, 1018), sidepoint=(864, 690, 1021, 1016), clap=(1016, 688, 1160, 1016)).items():
    part("js_p_" + n, J, b)
part("js_p_phone", J, (1150, 689, 1330, 1018), markers=[(1235, 850), (1420, 850)])
part("js_p_shrug", J, (1285, 689, 1536, 1018), markers=[(1235, 850), (1420, 850)])
part("js_b_suit", J, (0, 0, 262, 692))
row("js_m", J, [(746, 482, 835, 550), (837, 482, 924, 552), (925, 482, 1016, 552), (1017, 482, 1102, 554), (1104, 481, 1184, 554),
                (1187, 483, 1272, 552), (1274, 482, 1360, 548), (1363, 483, 1450, 546), (1452, 481, 1529, 556)])

# --- Owners and executives (group sheet 160124): bodies, front / 3/4 / profile / expression heads, mouths ---
EX = dict(jr=dict(bodies=[("grey", (14, 45, 144, 402)), ("suit", (143, 45, 262, 402))],
                  headsA=[("front", (15, 402, 116, 524)), ("prof", (277, 402, 376, 524))],
                  headsB=[("e1", (12, 527, 104, 644)), ("e2", (103, 527, 196, 644)), ("e3", (195, 527, 288, 644)), ("e4", (285, 527, 380, 644))],
                  mouths=[(15, 650, 85, 696), (89, 650, 159, 698), (162, 649, 237, 700), (241, 650, 312, 700), (316, 649, 381, 705)]),
          av=dict(bodies=[("suit", (402, 50, 528, 402), [(465, 200), (585, 200)]), ("jumper", (522, 50, 648, 402), [(465, 200), (585, 200), (705, 200)])],
                  headsA=[("front", (412, 402, 508, 524)), ("prof", (665, 398, 766, 524))],
                  headsB=[("e1", (399, 527, 493, 644)), ("e2", (491, 527, 581, 644))],
                  mouths=[(407, 648, 476, 690), (479, 649, 547, 690), (551, 648, 622, 694), (626, 649, 685, 689), (690, 649, 753, 702)]),
          jg=dict(bodies=[("suit", (779, 50, 905, 402), [(840, 200), (955, 200)]), ("jumper", (896, 50, 1020, 402), [(840, 200), (955, 200), (1075, 200)])],
                  headsA=[("front", (782, 402, 881, 524)), ("prof", (1042, 402, 1147, 524))],
                  headsB=[("e1", (777, 527, 872, 644)), ("e2", (869, 527, 962, 644))],
                  mouths=[(783, 649, 853, 692), (856, 649, 924, 693), (927, 649, 998, 696), (1001, 649, 1066, 692), (1070, 648, 1134, 701)]),
          om=dict(bodies=[("suit", (1163, 50, 1290, 402), [(1225, 200), (1340, 200)])],
                  headsA=[("front", (1166, 402, 1265, 524)), ("prof", (1421, 402, 1526, 524))],
                  headsB=[("e1", (1161, 527, 1253, 644)), ("e2", (1252, 527, 1343, 644)), ("e3", (1341, 527, 1430, 644)), ("e4", (1428, 527, 1520, 644))],
                  mouths=[(1165, 650, 1235, 695), (1238, 650, 1307, 694), (1310, 650, 1381, 698), (1384, 650, 1452, 697), (1456, 648, 1520, 704)]))
for p, d in EX.items():
    for grp in ("bodies", "headsA", "headsB"):
        for it in d[grp]:
            n, b = it[0], it[1]
            part(f"{p}_{'b' if grp == 'bodies' else 'h'}_{n}", G, b, markers=it[2] if len(it) > 2 else None)
    row(f"{p}_m", G, d["mouths"])

# --- Harry Maguire (cream-paper flat style): 12 lip-sync busts + turnaround ---
MGL = ["rest", "A", "E", "I", "O", "U", "MBP", "FV", "L", "smile", "frown", "shout"]
cols, rows_ = [(12, 292), (290, 566), (563, 838), (835, 1112)], [(8, 374), (446, 812), (884, 1250)]
for i, n in enumerate(MGL):
    (x0, x1), (y0, y1) = cols[i % 4], rows_[i // 4]
    part("mg_l_" + n, MG_L, (x0, y0, x1, y1), mode="flood", model=ANI)
for n, b in dict(front=(28, 8, 296, 668), side=(348, 8, 508, 668), back=(552, 8, 812, 668), q34=(838, 8, 1098, 668)).items():
    part("mg_t_" + n, MG_T, b, mode="flood", model=ANI)
# scene 3 inserts: open hands (-> goalkeeper gloves), fists (tying the laces), boots with socks
for n, b in dict(hand_L=(608, 778, 721, 927), hand_R=(728, 778, 840, 927), fist_L=(885, 798, 973, 888),
                 fist_R=(998, 798, 1087, 888), boot_L=(572, 1082, 718, 1262), boot_R=(765, 1082, 912, 1262)).items():
    part("mg_" + n, MG_T, b, mode="flood", model=ANI)


# executives' action poses (group sheet, bottom row), Mainoo's match kit, Carrick's tracksuit pointing arm
for n, b in dict(jr_p_finger=(114, 790, 202, 1011), jr_p_tie=(215, 790, 291, 1011), jr_p_open=(298, 792, 391, 1011),
                 av_p_point=(513, 793, 639, 1007), av_p_open=(640, 793, 764, 1012),
                 jg_p_wave=(886, 793, 1011, 1008), jg_p_open=(999, 793, 1137, 1010),
                 om_p_finger=(1167, 793, 1271, 1011), om_p_explain=(1350, 794, 1449, 1009)).items():
    part(n, G, b)
part("km_b_match", CH + "kobbie-mainoo/house-style/kobbie-mainoo__outfits__20260928T091500__b46d99b6.png", (1027, 9, 1407, 1000))
part("ck_arm_point_t", CK_M, (683, 320, 787, 473))
part("jr_b_suit", G, (143, 45, 262, 402))
part("ck_arm_palm_s", CK_M, (1023, 313, 1182, 452))
part("cu_h_profL", CU_F, (1140, 10, 1484, 345))

# bodies and poses are large: the lighter anime model keeps the ink lines clean and is 3x faster
for _n, _sp in SPEC.items():
    if "_b_" in _n or "_p_" in _n: _sp["model"] = ANI

# what scenes 1-4 use, most important first (running with no arguments cuts these)
USED = ["ck_h_neutral", "ck_h_smile", "ck_h_frown", "ck_h_surprised", "ck_h_q34", "ck_h_profR", "ck_h_profL",
        "ck_m", "ck_b_suit", "js_p_tablet", "js_p_present", "js_m", "om_b_suit", "om_h_front", "om_h_e3", "om_h_prof", "om_m",
        "jr_b_grey", "jr_h_front", "jr_h_prof", "jr_h_e2", "jr_m", "js_p_point", "js_p_crossed", "js_p_chin", "js_b_suit",
        "jg_b_jumper", "jg_h_front", "jg_h_e1", "jg_m", "av_b_jumper", "av_h_front", "av_h_e1", "av_h_prof", "av_m",
        "ck_b_track", "ck_arm_reach_t", "br_b_match", "br_h_smile", "br_h_angry", "br_h_q34", "br_h_front2",
        "cu_b_match", "cu_h_neutral", "cu_h_q34", "cu_h_profR", "mg_l_", "mg_t_front", "mg_t_q34", "mg_t_side", "om_h_e2",
        # scenes 3-4
        "mg_t_back", "km_b_match", "cu_h_profL", "ck_arm_point_t", "ck_arm_palm_s", "mg_hand_", "mg_fist_", "mg_boot_"]

PAD = 6

def load(src):
    im = Image.open(src)
    return np.asarray(im.convert("RGBA")).copy(), im.mode

def smooth(a, lo, hi):
    t = np.clip((a.astype(np.float32) - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)

def matte_flood(rgb):
    """Paper background = pixels connected to the crop border that are light and unsaturated."""
    f = rgb.astype(np.float32)
    mx, mn = f.max(2), f.min(2)
    paper = (mn > 200) & (mx - mn < 40)
    lab, _ = ndimage.label(paper)
    border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    bg = np.isin(lab, list(border))
    fg = ~bg
    fg = ndimage.binary_fill_holes(ndimage.binary_opening(fg, iterations=1))
    return fg.astype(np.float32)

def cut(name, sp, sheets):
    src, (x0, y0, x1, y1) = sp["src"], sp["box"]
    rgba = sheets[src]
    H, W = rgba.shape[:2]
    X0, Y0, X1, Y1 = max(0, x0 - PAD), max(0, y0 - PAD), min(W, x1 + PAD), min(H, y1 + PAD)
    c = rgba[Y0:Y1, X0:X1].copy()
    if sp["mode"] == "alpha":
        a = smooth(c[..., 3], 40, 225)
    else:
        a = matte_flood(c[..., :3])
    # outside the declared box (the padding) nothing belongs to this part unless it is the same blob
    inbox = np.zeros(a.shape, bool); inbox[y0 - Y0:y1 - Y0, x0 - X0:x1 - X0] = True
    solid = a > 0.35
    lab, n = ndimage.label(solid)
    if sp["markers"]:
        # split touching drawings: watershed on the distance transform of a wider context seeded at every
        # drawing's centre, so neighbours outside the box claim their own pixels
        mxs = [m[0] for m in sp["markers"]] + [X0, X1]; mys = [m[1] for m in sp["markers"]] + [Y0, Y1]
        CX0, CY0 = max(0, min(mxs) - 250), max(0, min(mys) - 250)
        CX1, CY1 = min(W, max(mxs) + 250), min(H, max(mys) + 250)
        cc = rgba[CY0:CY1, CX0:CX1]
        ca = smooth(cc[..., 3], 40, 225) if sp["mode"] == "alpha" else matte_flood(cc[..., :3])
        csolid = ca > 0.35
        dist = ndimage.distance_transform_edt(csolid)
        mk = np.zeros(ca.shape, np.int32)
        for i, (mx_, my_) in enumerate(sp["markers"]):
            cv2.circle(mk, (int(mx_ - CX0), int(my_ - CY0)), 6, i + 1, -1)
        bc = ((x0 + x1) / 2, (y0 + y1) / 2)
        own = 1 + int(np.argmin([(mx_ - bc[0]) ** 2 + (my_ - bc[1]) ** 2 for mx_, my_ in sp["markers"]]))
        ws = watershed(-dist, mk, mask=csolid)
        keep = (ws == own)[Y0 - CY0:Y1 - CY0, X0 - CX0:X1 - CX0]
    else:
        sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
        # components mostly inside the box and not tiny
        keep = np.zeros(a.shape, bool)
        big = sizes.max() if n else 0
        for i in range(1, n + 1):
            m = lab == i
            if sizes[i - 1] >= max(60, 0.02 * big) and (m & inbox).sum() > 0.6 * sizes[i - 1]:
                keep |= m
    keep = ndimage.binary_fill_holes(keep) if sp["mode"] == "flood" else keep
    # soft edge: grow the kept mask a little so anti-aliased edge pixels stay, then take the soft alpha there
    grow = ndimage.binary_dilation(keep, iterations=2)
    a = np.where(grow, a, 0) if sp["mode"] == "alpha" else keep.astype(np.float32)
    # bleed colours into the transparent area so upscaling does not pull in the sheet background
    rgb = c[..., :3].copy()
    idx = ndimage.distance_transform_edt(a < 0.5, return_distances=False, return_indices=True)
    rgb = rgb[idx[0], idx[1]]
    return rgb, a, (X0, Y0)

def main(names=None):
    import upscale
    os.makedirs("build/parts", exist_ok=True)
    meta = json.load(open("build/parts/meta.json")) if os.path.exists("build/parts/meta.json") else {}
    sheets = {}
    pats = names or USED
    todo = []
    for p in pats:
        todo += [n for n in SPEC if (n == p or n.startswith(p)) and n not in todo]
    for n in todo:
        sp = SPEC[n]
        out = f"build/parts/{n}.png"
        key = json.dumps([sp["src"], sp["box"], sp["mode"], sp["model"], sp["markers"]])
        if os.path.exists(out) and meta.get(n, {}).get("key") == key:
            continue
        if sp["src"] not in sheets: sheets[sp["src"]] = load(sp["src"])[0]
        rgb, a, off = cut(n, sp, sheets)
        big = upscale.upscale(np.ascontiguousarray(rgb), sp["model"])
        A = cv2.resize(a, (a.shape[1] * 4, a.shape[0] * 4), interpolation=cv2.INTER_CUBIC)
        A = smooth(np.clip(A, 0, 1) * 255, 70, 185) if sp["mode"] == "alpha" else cv2.GaussianBlur(np.clip(A, 0, 1), (0, 0), 1.2)
        out_img = np.dstack([big, (np.clip(A, 0, 1) * 255 + 0.5).astype(np.uint8)])
        ys, xs = np.nonzero(out_img[..., 3] > 0)
        t, b, l, r = max(0, ys.min() - 8), ys.max() + 9, max(0, xs.min() - 8), xs.max() + 9
        out_img = out_img[t:b, l:r]
        Image.fromarray(out_img).save(out)
        meta[n] = dict(src=sp["src"], box=sp["box"], off=[off[0] + l / 4, off[1] + t / 4], scale=4, size=[out_img.shape[1], out_img.shape[0]], key=key)
        json.dump(meta, open("build/parts/meta.json", "w"), indent=1)
        print("cut", n, out_img.shape, flush=True)

if __name__ == "__main__":
    main(sys.argv[1:] or None)

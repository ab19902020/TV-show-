"""The cast for scenes 1-4: every drawing used, with its face landmarks (sheet coordinates, read off zoomed grids /
detected, see facemarks.py) and anchor points.

mouth = (left corner x, y, right corner x, y, centre x, y) of the closed mouth line; eyes = (cx, cy, rx, ry) of each eye
opening; chin = y of the chin; neck = base of the neck (collar centre, the head's pivot); head = head box (x0, y0, x1, y1).
A "bust" is a sheet head (bigger, sharper, other expressions) set on a body drawing cut at the collar: the head sits
behind the body, registered eye-to-eye onto the body's own head."""
import numpy as np, cv2
from engine import Drawing, META

D = {}


def add(name, part, **kw):
    D[name] = dict(part=part, **kw)


# ---- Michael Carrick (outfits sheet: suit for the boardroom, tracksuit for Hull)
add("ck_suit", "ck_b_suit", mouth=(1248, 188, 1300, 183, 1272, 186.5), chin=239,
    eyes=[(1242, 135, 12.5, 5.5), (1297, 131, 12.5, 5.5)], neck=(1275, 258), head=(1160, 10, 1362, 252),
    anchors=dict(collar=(1275, 258), feet=(1268, 990)))
add("ck_track", "ck_b_track", mouth=(769, 188, 820, 183, 792, 186.5), chin=239,
    eyes=[(762, 135, 12.5, 5.5), (817, 131, 12.5, 5.5)], neck=(795, 262), head=(680, 10, 882, 256),
    anchors=dict(collar=(795, 262), feet=(790, 995)))
# ---- Jason Wilcox: action poses with their own heads (thigh-length drawings)
add("js_tablet", "js_p_tablet", mouth=(263, 774, 285, 773, 274, 774), chin=790,
    eyes=[(259, 749, 3.6, 2.3), (284, 748, 4.5, 2.5)], neck=(268, 802), head=(228, 690, 305, 797),
    anchors=dict(collar=(268, 802)))
add("js_present", "js_p_present", mouth=(744, 768, 770, 767, 757, 768), chin=787,
    eyes=[(740, 746.5, 4.0, 2.3), (764, 742, 4.5, 2.5)], neck=(752, 798), head=(712, 689, 792, 794),
    anchors=dict(collar=(752, 798)))
add("js_crossed", "js_p_crossed", mouth=(404, 771, 430, 771, 417, 771), chin=791,
    eyes=[(402, 746, 4.5, 2.5), (430, 745, 4.5, 2.5)], neck=(415, 801), head=(377, 688, 457, 797),
    anchors=dict(collar=(415, 801)))
add("js_sidepoint", "js_p_sidepoint", mouth=(942, 765, 952, 764, 947, 765), chin=780, facing="right",
    eyes=[(936.5, 740.5, 3.0, 2.0)], neck=(925, 796), head=(880, 689, 966, 792),
    anchors=dict(collar=(925, 796)))
add("js_shrug", "js_p_shrug", mouth=(1404, 772, 1430, 772, 1417, 772), chin=790,
    eyes=[(1406, 743, 4.5, 2.5), (1432, 748, 4.5, 2.5)], neck=(1418, 801), head=(1379, 688, 1461, 797),
    anchors=dict(collar=(1418, 801)))
add("js_chin", "js_p_chin", eyes=[(564, 750, 3.6, 2.3), (591, 750, 4.5, 2.5)], chin=790, neck=(575, 800),
    head=(525, 690, 612, 794), anchors=dict(collar=(575, 800)))
# ---- executives (group sheet): bodies with their own heads
add("jr_suit", "jr_b_suit", mouth=(198, 117.5, 217, 117.5, 207.5, 118), chin=134,
    eyes=[(198.5, 94, 4.5, 2.5), (219, 94, 4.5, 2.5)], neck=(207, 141), head=(160, 46, 256, 139),
    anchors=dict(collar=(207, 141)))
add("om_suit", "om_b_suit", mouth=(1219, 119.5, 1239.5, 119.5, 1229, 120), chin=133,
    eyes=[(1218.5, 93.5, 4.0, 2.5), (1240.5, 93.5, 4.0, 2.5)], neck=(1229, 141), head=(1194, 52, 1263, 138),
    anchors=dict(collar=(1229, 141)))
add("jg_jumper", "jg_b_jumper", mouth=(950, 116, 970.5, 116, 960, 116.5), chin=131.5,
    eyes=[(948.5, 91, 4.0, 2.5), (972, 91, 4.0, 2.5)], neck=(960, 140), head=(925, 52, 996, 136),
    anchors=dict(collar=(960, 140)))
add("av_jumper", "av_b_jumper", mouth=(583, 114.5, 605, 114.5, 594, 115), chin=128,
    eyes=[(578.5, 90, 4.5, 2.5), (601, 89, 4.5, 2.5)], neck=(590, 138), head=(550, 52, 636, 133),
    anchors=dict(collar=(590, 138)))
# ---- executives: sheet heads (for busts)
add("jr_h_front", "jr_h_front", mouth=(49, 487, 87, 487, 68, 489), chin=512,
    eyes=[(48, 466, 5.0, 2.6), (79, 466, 4.5, 2.6)])
add("jr_h_e4", "jr_h_e4", mouth=(321, 614, 349, 614, 335, 614), chin=637,
    eyes=[(322, 586, 4.5, 2.5), (348, 587, 4.5, 2.5)])
add("jr_h_e1", "jr_h_e1", mouth=(41, 611, 79, 611, 60, 612), chin=637,
    eyes=[(41, 587, 4.5, 2.5), (70, 587, 4.5, 2.5)])
add("om_h_front", "om_h_front", mouth=(1203, 497, 1230, 497, 1216, 497), chin=515,
    eyes=[(1197.5, 462, 4.2, 2.6), (1230, 462, 4.2, 2.6)])
add("om_h_e1", "om_h_e1", mouth=(1201, 616, 1227, 616, 1214, 616), chin=635,
    eyes=[(1196, 583, 4.5, 2.5), (1226, 583, 4.5, 2.5)])
add("jg_h_front", "jg_h_front", mouth=(818, 492, 842, 492, 830, 492), chin=510,
    eyes=[(815, 456, 3.6, 2.5), (848, 456, 4.0, 2.5)])
add("av_h_front", "av_h_front", mouth=(448, 492, 475, 492, 461, 492), chin=515,
    eyes=[(445, 456, 5.0, 3.0), (475, 456, 4.5, 3.0)])
# ---- players (silent in scenes 1-4, blinks / looks only) and Maguire's lip-sync busts
add("br_match", "br_b_match", mouth=(1187, 166, 1235, 162, 1210, 167), eyes=[(1183.5, 118.5, 11.0, 5.5), (1237, 117, 11.0, 5.5)], chin=205, neck=(1212, 232),
    head=(1110, 10, 1305, 228), anchors=dict(collar=(1212, 232), feet=(1215, 990)))
add("cu_match", "cu_b_match", chin=222, neck=(1270, 245), head=(1185, 20, 1370, 240),
    anchors=dict(collar=(1270, 245), feet=(1270, 990)))
add("km_match", "km_b_match", chin=215, neck=(1217, 232), head=(1110, 9, 1320, 228),
    anchors=dict(collar=(1217, 232), feet=(1217, 990)))
_cols, _rows = [12, 290, 563, 835], [8, 446, 884]
for i, v in enumerate(["rest", "A", "E", "I", "O", "U", "MBP", "FV", "L", "smile", "frown", "shout"]):
    add("mg_" + v, "mg_l_" + v, anchors=dict(neck=(_cols[i % 4] + 140, _rows[i // 4] + 292)))
for n, x in (("q34", 968), ("side", 428), ("back", 682)):
    add("mg_" + n, "mg_t_" + n, anchors=dict(neck=(x, 150), feet=(x, 655)))
add("mg_front", "mg_t_front", mouth=(145, 100, 176, 100, 160, 102), chin=130, eyes=[(147.5, 79, 7.2, 5.2), (172.5, 79, 7.2, 5.2)],
    neck=(160, 150), head=(112, 18, 208, 140), anchors=dict(neck=(160, 150), feet=(162, 655)), ink=(0.08, 0.06, 0.06),
    lid=(0.96, 0.79, 0.64))
add("js_body", "js_b_suit")

# bust rigs: head drawing, body drawing, body cut line (sheet y; the body is kept below it)
BUSTS = {
    "jr_bust": ("jr_suit", 140.0), "om_bust": ("om_suit", 139.5), "jg_bust": ("jg_jumper", 137.5), "av_bust": ("av_jumper", 134.5),
}

_built = {}


def get(name):
    if name not in _built:
        spec = dict(D[name]); part = spec.pop("part")
        _built[name] = Drawing(name, part, **spec)
    return _built[name]


def bust_transform(head, body):
    """similarity (3x3, part px -> part px) taking the head drawing's eyes onto the body drawing's eyes"""
    hd, bd = D[head], D[body]
    he = np.float32([hd["eyes"][0][:2], hd["eyes"][1][:2]]); be = np.float32([bd["eyes"][0][:2], bd["eyes"][1][:2]])
    hm, bm = META[hd["part"]]["off"], META[bd["part"]]["off"]
    he = (he - np.float32(hm)) * 4; be = (be - np.float32(bm)) * 4
    s = np.linalg.norm(be[1] - be[0]) / np.linalg.norm(he[1] - he[0])
    t = be.mean(0) - s * he.mean(0)
    return np.array([[s, 0, t[0]], [0, s, t[1]], [0, 0, 1]], np.float64)


_cut = {}


def cut_body(body, cut_y):
    """the body drawing's image with everything above the collar line removed (premultiplied, full res)"""
    key = (body, cut_y)
    if key not in _cut:
        d = get(body)
        img = d.u8[1.0].astype(np.float32) / 255.0
        y = (cut_y - d.oy) * 4
        H = img.shape[0]
        yy = np.arange(H, dtype=np.float32)[:, None]
        k = np.clip((yy - y) / 6.0 + 0.5, 0, 1)
        img[..., 3] *= k
        img[..., :3] *= img[..., 3:4]
        _cut[key] = img
    return _cut[key]

# ---- scene 2: Joel's big wave (group sheet action pose) with his face landmarks
add("jg_wave", "jg_p_wave", mouth=(941, 828.5, 954, 828.5, 947.5, 828.5), chin=836,
    neck=(946, 842), head=(925, 795, 968, 838), anchors=dict(collar=(946, 842)))
add("av_point", "av_p_point", anchors=dict(collar=(574, 842)))
# ---- Carrick's hands
add("ck_hand_palm_s", "ck_arm_palm_s")
add("ck_hand_point_t", "ck_arm_point_t")
add("cu_prof", "cu_h_profL")

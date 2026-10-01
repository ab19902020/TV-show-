"""Micah's 50 CAPS party, as Rooney sees it. Setups registered into direction.EXTRA_SETUPS.

Micah dances ON the 50 CAPS table. He is one figure made of two drawings from his own sheet: the waist-up gesture pose (hands up /
the 50 CAPS card) over the legs of his front turnaround, registered at the neck. The dance is continuous motion, never a flicker of
drawings: a bounce on every beat (knees: the legs squash, the body drops), a hip sway every two beats (the torso rocks about the
hips, the legs shear with it), a head bob. Friends: Jamie raises his pint, Ravi holds up the 50 CAPS card, a friend films on his
phone; the crowd ("about twenty of his guys") fills in on the words and bounces in time. None of them looks like Rooney.
All positions are 1x plate px of the 941 x 1672 portrait plates."""
import math, json, numpy as np, cv2
from PIL import Image
import perf, cast, props
from perf import W
from render_util import *
import walkrig as WR

BPM = 122.0


def beat(t):
    return t * BPM / 60.0


def T3(x, y): return np.array([[1, 0, x], [0, 1, y], [0, 0, 1]], np.float64)


def S3(sx, sy=None): return np.array([[sx, 0, 0], [0, sx if sy is None else sy, 0], [0, 0, 1]], np.float64)


def R3(deg):
    a = math.radians(deg); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float64)


def sheet_to_part(name):
    m = E.META[name]; k = float(m.get("scale", 4)); ox, oy = m["off"]
    return np.array([[k, 0, -ox * k], [0, k, -oy * k], [0, 0, 1]], np.float64)


def pop(t, t_app, dur=0.28):
    """(visible, size multiplier with a little overshoot, alpha) for something that appears at t_app"""
    if t < t_app: return False, 1.0, 0.0
    u = min(1.0, (t - t_app) / dur)
    k = 1 + 0.12 * math.sin(u * math.pi) * (1 - u)
    return True, (0.6 + 0.4 * smooth(u)) * k, min(1.0, u * 2.5)


# ================================================================ Micah: two drawings, one dancer
LEGS_SRC = "m2_t_front"
T_NECK = (372.0, 250.0)                  # neck point on the front turnaround (sheet)
P_SCALE = 30.0 / 28.0                    # pose -> turnaround scale (eye spacing on the frontal faces)
TORSO_X = (331.0, 411.0)                 # the turnaround's torso between its arms (sheet x), above the jacket hem
HEM_Y = 352.0
_legs = {}


def legs_sprite(cut_y):
    """the front turnaround below cut_y, without its arms and pocketed hands (they would show as extra arms)"""
    if cut_y in _legs: return _legs[cut_y]
    m = E.META[LEGS_SRC]; k = float(m.get("scale", 4)); ox, oy = m["off"]
    im = np.asarray(Image.open(f"build/parts/{LEGS_SRC}.png")).copy()
    H, Wd = im.shape[:2]
    yy, xx = np.mgrid[0:H, 0:Wd]
    sy = yy / k + oy; sx = xx / k + ox
    keep = (sy >= cut_y).astype(np.float32)
    side = (sy < HEM_Y) & ((sx < TORSO_X[0]) | (sx > TORSO_X[1]))
    keep[side] = 0.0
    keep = cv2.GaussianBlur(keep, (0, 0), 1.2)
    a = im[..., 3].astype(np.float32) * keep
    # re-ink the new vertical side edges of the jacket
    edge = side.astype(np.uint8)
    edge = (cv2.dilate(edge, np.ones((7, 7), np.uint8)) > 0) & ~side & (sy >= cut_y) & (a > 128)
    im[..., :3][edge] = (28, 24, 30)
    im[..., 3] = a.astype(np.uint8)
    _legs[cut_y] = WR.Sprite(f"{LEGS_SRC}:legs{cut_y}", im, k)
    return _legs[cut_y]


POSES = {"dance": "m2_p_handsup", "placard": "m2_p_placard", "point": "m2_p_pointing", "freeze": "m2_p_handsup"}


class Placed(WR.Placed):
    pass


def micah_dancer(t, x, y, height, mode, t_mode, z=5.0, energy=1.0, look=None):
    """Micah standing at (x, y) = feet (plate px), `height` plate px tall. Returns actor tuples (legs, torso with face).
    modes: dance / placard (dances holding the card up) / freeze (stops dead) / cool (hands in pockets: the plain turnaround)"""
    tf = cast.get(LEGS_SRC)
    feet_y = cast.bottom_y(LEGS_SRC)
    top_y = cast.head_box(LEGS_SRC)[1]
    sc = height / (feet_y - top_y)                                  # plate px per turnaround sheet px
    Wm = T3(x * 4, y * 4) @ S3(sc * 4) @ T3(-T_NECK[0], -feet_y)     # turnaround sheet -> world px (feet at x, y)
    if mode == "cool":                                               # the innocent stance: hands in pockets, a tiny sway
        sway = 1.2 * math.sin(t * 2.0)
        Rb = T3(T_NECK[0], feet_y) @ R3(sway) @ T3(-T_NECK[0], -feet_y)
        a = Placed(tf, Wm @ Rb @ np.linalg.inv(sheet_to_part(LEGS_SRC)), z)
        st, _ = face_state("mi", t, talks=False)
        return [(a, st, None, 1.0)]
    pose_name = POSES.get(mode, "m2_p_handsup")
    pd = cast.get(pose_name)
    neck = cast.POSE_HEADS[pose_name][1]
    bottom = cast.bottom_y(pose_name)
    cut = T_NECK[1] + (bottom - neck[1]) * P_SCALE - 6               # turnaround y where the pose's flat cut lands (overlap)
    b = beat(t - t_mode) if mode != "freeze" else 0.0
    e = energy if mode != "freeze" else 0.0
    dip = abs(math.sin(math.pi * b)) ** 0.8 * e                      # 0 = up, 1 = down on the beat
    sway = math.sin(math.pi * b / 2.0) * e                           # one side per two beats
    hip_y = HEM_Y + 8
    squash = 1 - 0.055 * dip
    shear = 0.10 * sway
    # legs: feet planted; the knees "bend" (vertical squash) and the hips swing over the feet (shear)
    L = T3(T_NECK[0], feet_y) @ np.array([[1, shear, 0], [0, squash, 0], [0, 0, 1]], np.float64) @ T3(-T_NECK[0], -feet_y)
    hip_dx = shear * (hip_y - feet_y)
    hip_dy = (feet_y - hip_y) * (1 - squash)
    # torso: rides on the hips, rocks against the sway, leans into the beat
    U = T3(T_NECK[0] + hip_dx, hip_y + hip_dy) @ R3(-7.0 * sway) @ T3(-T_NECK[0], -hip_y)
    P = T3(T_NECK[0], T_NECK[1]) @ S3(P_SCALE) @ T3(-neck[0], -neck[1])          # pose sheet -> turnaround sheet
    legs = legs_sprite(round(cut, 1))
    la = Placed(legs, Wm @ L @ np.linalg.inv(sheet_to_part(LEGS_SRC)), z - 0.01)
    ta = Placed(pd, Wm @ U @ P @ np.linalg.inv(sheet_to_part(pose_name)), z)
    st, _ = face_state("mi", t, talks=False)
    st["tilt"] = st.get("tilt", 0.0) + 6.0 * math.sin(math.pi * b) * e    # head bob on the beat
    st["nod"] = st.get("nod", 0.0) + 3.0 * dip
    if look is not None: st["lookx"], st["looky"] = look
    return [(la, None, None, 1.0), (ta, st, None, 1.0)]


def micah_mode(s, t):
    m = s.get("mi_mode") or perf.pose_at("mi", t, "dance")
    return m, perf.mode_start("mi", t)


# ================================================================ friends and crowd (Jamie and Ravi; recoloured for the crowd)
def bounce_matrix(anchor, t, phase, amp, sway, size=1.0, wobble=0.0):
    b = beat(t) + phase
    h = abs(math.sin(math.pi * b)) ** 0.75
    lean = sway * math.cos(math.pi * b) + (wobble * math.sin(t * 2 * math.pi * 7.0) if wobble else 0.0)
    ax, ay = anchor
    return body_matrix((ax, ay), lean=lean, dy=-amp * h, sx=1 + 0.02 * (1 - h), sy=1 - 0.02 * (1 - h) + 0.008 * h)


_variants = {}
TINTS = [(0, 0.0), (95, 0.08), (0, 0.18), (12, 0.05), (95, 0.0), (172, 0.06), (0, 0.10), (12, 0.14)]


def variant(name, k):
    """a recoloured copy of a friend for the crowd: the clothes' hue is rotated, skin and hair are kept, a little darker"""
    key = (name, k)
    if key in _variants: return _variants[key]
    im = np.asarray(Image.open(f"build/parts/{name}.png")).copy()
    if k:
        hsv = cv2.cvtColor(im[..., :3], cv2.COLOR_RGB2HSV).astype(np.int32)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        skin = (h >= 5) & (h <= 22) & (s > 70) & (v > 110)
        cloth = ~skin & (s > 25) & (v > 25)
        dh, dv = TINTS[k % len(TINTS)]
        hsv[..., 0] = np.where(cloth, (h + dh) % 180, h)
        hsv[..., 1] = np.where(cloth, np.clip(s + 40, 0, 255), s)
        im[..., :3] = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        im[..., :3] = (im[..., :3].astype(np.float32) * (1 - dv)).astype(np.uint8)
    m = E.META[name]
    sp = WR.Sprite(f"{name}:v{k}", im, float(m.get("scale", 4)))
    sp.ox, sp.oy = m["off"]
    _variants[key] = sp
    return sp


CROWD_PARTS = ["fr_jamie_cheers", "fr_jamie_yes", "fr_ravi_pointing", "fr_jamie_banter", "fr_ravi_placard", "fr_jamie_yes", "fr_jamie_cheers",
               "fr_ravi_pointing", "fr_jamie_banter", "fr_jamie_yes", "fr_ravi_pointing", "fr_jamie_cheers"]


def crowd_spec(seed=11, n=9, xs=(70, 900), ys=(770, 800), hpx=(250, 280)):
    rng = np.random.default_rng(seed)
    order = np.argsort(rng.uniform(0, 1, n))
    out = []
    for i in range(n):
        y = rng.uniform(*ys)
        out.append(dict(part=CROWD_PARTS[i % len(CROWD_PARTS)], k=1 + i, x=float(xs[0] + (xs[1] - xs[0]) * (i + rng.uniform(-0.3, 0.3)) / (n - 1)),
                        y=float(y), h=float(rng.uniform(*hpx)), flip=bool(rng.random() < 0.5), ph=float(rng.uniform(0, 2)),
                        amp=float(rng.uniform(10, 18)), order=int(order[i])))
    return out


CROWD = crowd_spec()


def figure(name_or_sprite, x, y, height, t, flip=False, phase=0.0, amp=14.0, sway=3.0, size=1.0, z=None, wobble=0.0, k=0, light=1.0):
    """a full-figure friend with feet at (x, y), `height` plate px tall, bouncing in time (as an actor tuple)"""
    name = name_or_sprite
    m = E.META[name]; q = float(m.get("scale", 4))
    sp = variant(name, k) if k else None
    fy = cast.bottom_y(name); ty = m["off"][1] + 2
    sc = height * size / (fy - ty)
    fx = cast.anchors_of(name)["feet"][0]
    if sp is None:
        a = Actor(name, x, y, sc, flip=flip, anchor=(fx, fy), z=(y if z is None else z), light=light)
        st, _ = face_state(name, t, flip=flip, talks=False)
    else:
        class _A: pass
        a = Actor(cast.get(name), x, y, sc, flip=flip, anchor=(fx, fy), z=(y if z is None else z), light=light)
        a.d = sp; a.anchor = ((fx - sp.ox) * q, (fy - sp.oy) * q); st = None
    Bm = bounce_matrix(a.anchor, t, phase, amp * q / sc if sc else 0, sway, wobble=wobble)
    return (a, st, Bm, 1.0)


def crowd_actors(t, t_from, t_to, scale=1.0, dy=0.0, light=0.78, xshift=0.0, keep=None):
    acts = []
    for c in CROWD:
        if keep and not keep(c): continue
        t_app = t_from + (t_to - t_from) * (c["order"] / max(1, len(CROWD) - 1))
        vis, sz, al = pop(t, t_app)
        if not vis: continue
        a = figure(c["part"], c["x"] + xshift, c["y"] + dy, c["h"] * scale, t, flip=c["flip"], phase=c["ph"], amp=c["amp"], sway=3.5,
                   size=sz, k=c["k"], light=light, z=c["y"] - 1000)
        acts.append((a[0], a[1], a[2], al))
    return acts


def phone_actor(base, tip_sheet, t, size):
    """the filming phone held up at the friend's pointing fingertip"""
    a = base[0]
    px, py = a.d.P(*tip_sheet)
    M = a.matrix(base[2])
    wx = M[0, 0] * px + M[0, 1] * py + M[0, 2]; wy = M[1, 0] * px + M[1, 1] * py + M[1, 2]
    ph = Actor("prop_phone", wx / 4, wy / 4, size, anchor="mid", z=a.z + 0.5)
    Bm = body_matrix(ph.anchor, lean=-8 + 3 * math.sin(t * 5))
    return (ph, None, Bm, base[3])


# ================================================================ the 50 CAPS table (w_party)
PARTY_TABLE = [(232, 905), (262, 880), (310, 862), (400, 846), (500, 840), (600, 842), (700, 849), (800, 858), (941, 872), (941, 1200),
               (760, 1190), (600, 1200), (420, 1170), (300, 1140), (240, 1090)]
CHAIR_L = [(70, 1010), (110, 990), (280, 1000), (370, 1050), (420, 1290), (600, 1290), (590, 1350), (60, 1350), (40, 1200)]
CHAIR_R = [(700, 1150), (730, 1120), (941, 1110), (941, 1672), (690, 1672)]
SIGN = [(688, 838), (690, 690), (830, 688), (832, 838)]
MICAH_SPOT = (470, 905)          # feet on the tablecloth
MICAH_H = 470.0


def table_shadow(x, y, w):
    def fx(bg, Aw):
        c = cv2.transform(np.float32([[[x * 4, y * 4]]]), Aw)[0][0]
        sx = Aw[0, 0] * 4
        m = np.zeros(bg.shape[:2], np.float32)
        cv2.ellipse(m, (int(c[0]), int(c[1])), (int(w * sx * 0.5), int(w * sx * 0.12)), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
        m = cv2.GaussianBlur(m, (0, 0), max(1.0, w * sx * 0.06))[..., None]
        return bg * (1 - 0.45 * m)
    return fx


def party(s, t, cam):
    st = plate("w_party", occluders=[PARTY_TABLE, CHAIR_L, CHAIR_R])
    st.rim = (0.0, -1.0, 0.18, (1.0, 0.85, 0.55))
    acts, fg = [], []
    # the crowd behind the table, then the two friends at the back corners of the table
    crowd = crowd_actors(t, *perf.CROWD_WINDOW, scale=1.0, dy=0.0, light=0.72) if s.get("crowd") else []
    for key_, part, x, y, h, fl, ph in (("jamie", "fr_jamie_cheers", 205, 905, 430, False, 0.3), ("ravi", "fr_ravi_placard", 720, 880, 420, True, 1.1)):
        vis, sz, al = pop(t, perf.appear_time(key_, s["t0"] - 5))
        if vis:
            a = figure(part, x, y, h, t, flip=False, phase=ph, amp=16, sway=3, size=sz, z=y - 600)
            acts.append((a[0], a[1], a[2], al))
    vis, sz, al = pop(t, perf.appear_time("film", s["t0"] - 5))
    if vis:
        f = figure("fr_jamie_banter", 840, 900, 410, t, flip=True, phase=0.7, amp=8, sway=1.5, size=sz, k=5, z=300)
        acts.append((f[0], f[1], f[2], al))
        acts.append(phone_actor((f[0], f[1], f[2], al), (1009, 943), t, 0.95))
    # Micah on the table
    mode, tm = micah_mode(s, t)
    x, y = MICAH_SPOT
    fg += micah_dancer(t, x, y, MICAH_H, mode, tm, z=10)
    shadow = table_shadow(x, y + 2, 150)

    def plate_fx(bg, Aw):                        # the crowd goes into the background plate, so the depth of field softens it
        bg = shadow(bg, Aw)
        if crowd:
            C = np.vstack([Aw.astype(np.float64), [0, 0, 1]])
            lay = np.zeros(bg.shape[:2] + (4,), np.float32)
            for a_ in sorted(crowd, key=lambda q: q[0].z):
                st.draw_actor(lay, C, a_[0], a_[1], a_[2], a_[3])
            bg = lay[..., :3] + bg * (1 - lay[..., 3:4])
        return bg
    fr = st.render(cam, acts, dof=s.get("dof", 1.4), plate_fx=plate_fx, fg_actors=fg, occ_dof=0.0)
    if s.get("confetti"):
        fr = props.confetti(fr, t, seed=11, count=s.get("confetti_n", 120))
    return fr


# ================================================================ from Micah's side: the Rooneys laughing across the room (w_entrance)
BACK_TABLE = [(545, 705), (560, 698), (700, 694), (905, 700), (912, 770), (880, 800), (560, 800), (545, 760)]
CHAIR_A = [(468, 900), (470, 700), (480, 690), (620, 692), (632, 705), (630, 900)]
CHAIR_B = [(688, 910), (690, 712), (700, 703), (820, 706), (830, 720), (832, 910)]
CENTRE = [(680, 700), (690, 640), (680, 600), (700, 572), (790, 570), (830, 600), (830, 700)]
LAMP_A = [(622, 712), (626, 655), (662, 655), (664, 712)]
LAMP_B = [(848, 712), (850, 655), (884, 655), (886, 712)]
BACK_FAMILY = [("b1", 512, 34), ("cr", 553, 44), ("wr", 598, 52), ("b2", 846, 33), ("b3", 884, 33), ("b4", 920, 31)]


def party_side(s, t, cam):
    import restaurant
    st = plate("w_entrance", occluders=[BACK_TABLE, CHAIR_A, CHAIR_B, CENTRE, LAMP_A, LAMP_B])
    acts = []
    for ch, x, hpx in BACK_FAMILY:
        name, flip = pose_of(ch, t, f"{ch}_p_laughing")
        a = restaurant.seated(ch, name, flip, t, x, hpx, 700)
        # laughing: the whole body shakes with it
        k = math.sin(t * 2 * math.pi * 4.2 + hash(ch) % 7)
        Bm = a[2] @ body_matrix(a[0].anchor, dy=-2.0 * a[0].d.k * (0.5 + 0.5 * k))
        acts.append((a[0], a[1], Bm, 1.0))
    mode, tm = micah_mode(s, t)
    fg = micah_dancer(t, 590, 1580, 820, mode, tm, z=10, look=(1.0, -0.6) if mode == "freeze" else None)
    fr = st.render(cam, acts, dof=0.0, fg_actors=fg)
    return fr


# ================================================================ Micah's face, behind the party table (the match cut into the studio)
CU_EDGE = (560, 842)


def party_cu(s, t, cam):
    st = plate("w_party", occluders=[PARTY_TABLE, SIGN])
    name, flip = pose_of("mi_cu", t, "mr_e_embarrassed")
    a, cam2 = cu_on_edge("mi_cu", name, flip, t, *CU_EDGE)
    fr = st.render(cam2, [a], dof=1.6, occ_dof=0.0)
    return fr


MATCH = dict(u=0.50, v=0.44, head_frac=0.40, sink=0.30)


def cu_on_edge(ch, name, flip, t, x, edge_y):
    """a bust behind a table / desk edge, sunk so its flat cut is hidden, and the camera that frames its head for the match cut"""
    hx, hy = cast.head_c(name); hh = cast.head_h(name)
    hpx = 82.0
    sc = hpx / hh
    bottom = cast.bottom_y(name)
    y = edge_y + 6 - (bottom - hy) * sc + MATCH["sink"] * hpx * 0.0
    y = max(y, edge_y - (bottom - hy) * sc + 6)
    act = Actor(name, x, y, sc, flip=flip, anchor=(hx, hy), z=5)
    stf, b = face_state(ch, t, flip=flip, talks=False)
    w = hpx / MATCH["head_frac"]
    h = w * OH / OW
    cam = (x - (MATCH["u"] - 0.5) * w, y - (MATCH["v"] - 0.5) * h, w)
    return (act, stf, None, 1.0), cam


EXTRA = {"party": party, "party_side": party_side, "party_cu": party_cu}

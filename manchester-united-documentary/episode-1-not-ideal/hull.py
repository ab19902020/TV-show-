"""Scenes 3-4, Hull away: every setup the shot list uses for the pre-match and the match.

render.py binds its helpers in (bind(globals())) and merges SETUPS / GRADE / NO_GRADE into its own tables.

Scene 3  ext_stadium   dusk: fans walk to the ground, the United coach pulls in, lower third
         ins_*         eight fast inserts: boots, shirts, tape, goalkeeper gloves, Carrick walking, Bruno's captain
                       routine, Maguire tying his boots, Cunha staring at the tactics board
         dress_*       the team talk: the wide (Carrick centre, players seated around him), Carrick, Bruno, the
                       board, the SET PIECES tap, Maguire's close-up (drawn lip sync: mgvis.py)
Scene 4  match_*       the broadcast camera on the 3D pitch (pitch3d.py): kick-off, the home end, the corner, the
                       second dead ball; pitch-level shots of Carrick, Bruno and Maguire in front of the far stand"""
import math, os, functools, types, numpy as np, cv2
import engine as E, perf, direction as D, graphics as G, stage, cast, pitch3d as P
from stage import Actor, Stage, body_matrix

OW, OH, RS, FPS = E.OW, E.OH, E.RS, 30
m = perf.m
R = None


def bind(g):
    global R
    R = types.SimpleNamespace(**g)
    R.PLATES["tunnel_night"] = lambda: Stage(tunnel_night(), name="tunnel_night")


def smooth(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def ease_out(x):
    x = min(max(x, 0.0), 1.0); return 1 - (1 - x) ** 3


def W(lid, word, occ=1):
    return D.W(lid, word, occ)


# ---------------------------------------------------------------- drawing helpers
class _Dummy:
    pass


def paint_actors(bg, acts, C, rim=None, ambient=(1, 1, 1)):
    """composite actors [(Actor, face, body, alpha)] over an RGB frame; C = world (4x px) -> screen (3x3)"""
    d = Stage.__new__(Stage); d.rim = rim; d.ambient = np.float32(ambient)
    layer = np.zeros((OH, OW, 4), np.float32)
    for a, st_, b, al in sorted(acts, key=lambda q: q[0].z):
        Stage.draw_actor(d, layer, C, a, st_, b, al)
    return layer[..., :3] + bg * (1 - layer[..., 3:4])


def screen_C(cam):
    """world (4x px of a 960 x 540 'screen plate') -> screen, for shots with a rendered background"""
    cx, cy, w = [v * 4 for v in cam]
    z = OW / w
    h = w * OH / OW
    return np.array([[z, 0, -z * (cx - w / 2)], [0, z, -z * (cy - h / 2)], [0, 0, 1]], np.float64)


def blur(img, sigma):
    if sigma < 0.3: return img
    return stage.blur_half(img, sigma)


def fan(canvas, x, y, h, ph, col, scarf=None, face_right=True, alpha=1.0):
    """a walking fan at dusk: a dark silhouette with a warm rim; x, y = feet (screen px), h = height (px)"""
    s = h / 100.0
    sw = math.sin(ph)
    k = 1 if face_right else -1
    pts = lambda P_: np.int32(np.round(np.float32(P_) * 4))
    lay, al = canvas
    # legs (scissor), arms (opposite), torso, head
    for sgn, c_ in ((1, 0.7), (-1, 1.0)):
        a = sgn * sw * 14 * s
        leg = [(x - 4 * s, y - 50 * s), (x + 4 * s, y - 50 * s), (x + a + 3 * s, y), (x + a - 4 * s, y)]
        cv2.fillPoly(lay, [pts(leg)], tuple(v * c_ for v in col), cv2.LINE_AA, 2)
        cv2.fillPoly(al, [pts(leg)], alpha, cv2.LINE_AA, 2)
        arm = [(x - 3 * s + k * 2 * s, y - 80 * s), (x + 3 * s + k * 2 * s, y - 80 * s),
               (x - sgn * sw * 11 * s + 3 * s, y - 50 * s), (x - sgn * sw * 11 * s - 3 * s, y - 50 * s)]
        cv2.fillPoly(lay, [pts(arm)], tuple(v * c_ for v in col), cv2.LINE_AA, 2)
        cv2.fillPoly(al, [pts(arm)], alpha, cv2.LINE_AA, 2)
    torso = [(x - 10 * s, y - 84 * s), (x + 10 * s, y - 84 * s), (x + 8 * s, y - 46 * s), (x - 8 * s, y - 46 * s)]
    cv2.fillPoly(lay, [pts(torso)], col, cv2.LINE_AA, 2); cv2.fillPoly(al, [pts(torso)], alpha, cv2.LINE_AA, 2)
    hx, hy = x + k * 1.5 * s, y - 93 * s
    cv2.circle(lay, tuple(pts([(hx, hy)])[0]), int(9 * s * 4), col, -1, cv2.LINE_AA, 2)
    cv2.circle(al, tuple(pts([(hx, hy)])[0]), int(9 * s * 4), alpha, -1, cv2.LINE_AA, 2)
    if scarf is not None:
        sc = [(x - 10 * s, y - 86 * s), (x + 10 * s, y - 86 * s), (x + 9 * s, y - 80 * s), (x - 9 * s, y - 80 * s)]
        cv2.fillPoly(lay, [pts(sc)], scarf, cv2.LINE_AA, 2)
        tail = [(x - k * 6 * s, y - 82 * s), (x - k * 2 * s, y - 82 * s), (x - k * 3 * s, y - 62 * s), (x - k * 7 * s, y - 62 * s)]
        cv2.fillPoly(lay, [pts(tail)], scarf, cv2.LINE_AA, 2); cv2.fillPoly(al, [pts(tail)], alpha, cv2.LINE_AA, 2)


# ================================================================ SCENE 3: exterior
FANS = None


def fans_list():
    global FANS
    if FANS is None:
        rng = np.random.default_rng(31)
        FANS = []
        for i in range(34):
            y = rng.uniform(712, 800)                  # 1x plate: across the plaza, towards the turnstiles
            spd = rng.uniform(0.55, 0.8) * (1 if rng.random() < 0.55 else -1)
            FANS.append(dict(x0=rng.uniform(80, 1600), y=y, spd=spd, ph=rng.uniform(0, 6.3),
                             col=(0.05 + 0.03 * rng.random(), 0.04, 0.05),
                             scarf=[(0.96, 0.6, 0.05), (0.08, 0.08, 0.08), None, (0.96, 0.6, 0.05)][rng.integers(4)]))
        for i, (x0, y, spd) in enumerate(((260, 900, 0.7), (1450, 915, -0.75), (560, 930, 0.62), (1220, 888, -0.66))):
            FANS.append(dict(x0=x0, y=y, spd=spd, ph=rng.uniform(0, 6.3), col=(0.04, 0.03, 0.035),
                             scarf=(0.96, 0.6, 0.05) if i % 2 == 0 else (0.08, 0.08, 0.08), near=True))
    return FANS


def fans_layer(Aw, t, near):
    lay = np.zeros((OH, OW, 3), np.float32); al = np.zeros((OH, OW), np.float32)
    for f in fans_list():
        if bool(f.get("near")) != near: continue
        h1 = 26 + (f["y"] - 700) * 0.38                # height in 1x plate px (perspective on the plaza)
        x1 = f["x0"] + f["spd"] * h1 * t
        p = Aw @ np.float32([x1 * 4, f["y"] * 4, 1])
        hs = h1 * 4 * Aw[0, 0]
        if -200 < p[0] < OW + 200:
            fan((lay, al), p[0], p[1], hs, f["ph"] + t * 2 * math.pi * 1.9, f["col"], f["scarf"], f["spd"] > 0)
    return lay, al


def render_ext_stadium(s, t, cam):
    t0 = m("s3")
    u = t - t0
    # the coach: in from the right, decelerating to a stop; a small forward dip as it brakes
    k = ease_out(u / 3.0)
    x = 2150 - (2150 - 930) * k
    dip = 1.2 * math.exp(-((u - 3.05) / 0.22) ** 2)
    bus = Actor("bus", x, 852, 0.84, anchor="base", z=1, light=0.66, rim=(0.0, -1.0, 0.8, (1.0, 0.45, 0.25)))
    Bm = body_matrix(bus.anchor, lean=-dip)

    def plate_fx(bg, Aw):
        lay, al = fans_layer(Aw, u, near=False)
        a = al[..., None]
        edge = np.clip(a - cv2.GaussianBlur(a, (0, 0), 1.5 * RS)[..., None], 0, 1)          # warm rim from the ground
        return bg * (1 - a) + lay * a + edge * np.float32([0.8, 0.3, 0.1]) * 0.8

    def post_fx(fr, Aw):
        # headlights: a glow and a pool of light on the paving in front of the coach
        wpt = bus.matrix(Bm) @ np.float64([72, 490, 1])     # the headlight (bus part px) -> world -> screen
        hl = Aw.astype(np.float64) @ wpt
        yy, xx = np.mgrid[0:OH:4, 0:OW:4].astype(np.float32)
        g = np.exp(-(((xx - hl[0]) / (60 * RS)) ** 2 + ((yy - hl[1]) / (40 * RS)) ** 2))
        pool = np.exp(-(((xx - (hl[0] - 330 * RS)) / (330 * RS)) ** 2 + ((yy - (hl[1] + 60 * RS)) / (45 * RS)) ** 2)) * 0.5
        glow = cv2.resize(g + pool, (OW, OH), interpolation=cv2.INTER_LINEAR)[..., None]
        fr = fr + glow * np.float32([0.9, 0.8, 0.55]) * 0.55
        lay, al = fans_layer(Aw, u, near=True)            # fans walking past in front of the coach
        a = al[..., None]
        edge = np.clip(a - cv2.GaussianBlur(a, (0, 0), 1.5 * RS)[..., None], 0, 1)
        return fr * (1 - a) + lay * a + edge * np.float32([0.8, 0.3, 0.1]) * 0.8
    fr = R.st("stadium").render(cam, [(bus, None, Bm, 1.0)], dof=0, plate_fx=plate_fx, post_fx=post_fx)
    return R.lower3(fr, t, t0 + 0.5, 2.9, "HULL AWAY", "Premier League   |   Matchday 1   |   Kick-off 20:00")


# ================================================================ SCENE 3: inserts
def rack(t, t0, d0=6.0, dur=0.28):
    """a quick rack focus at the head of an insert"""
    return d0 * (1 - smooth((t - t0) / dur))


def render_ins_plate(s, t, cam, plate):
    return R.st(plate).render(cam, [], dof=rack(t, s["t0"], s.get("rack", 5.0)))


def sheet_px(cam, scale):
    """screen px per sheet px of an actor with this scale seen through a Stage camera"""
    return OW / cam[2] * scale


CID = np.array([[0.25, 0, 0], [0, 0.25, 0], [0, 0, 1]], np.float64)     # world = 4 x screen px


def screen_actor(name, x, y, k, anchor):
    """an actor placed straight in screen px (x, y) with k screen px per sheet px (drawn through CID)"""
    a = Actor(name, 0, 0, 1.0, anchor=anchor, z=2)
    a.x, a.y, a.scale = x * 4, y * 4, k
    return a


def render_ins_tape(s, t, cam):
    """close on a sock: white tape goes round the ankle, the roll in a fist sweeping across"""
    u = (t - s["t0"]) / (s["t1"] - s["t0"])
    boot = Actor("boot_L", 900, 760, 2.05, anchor="sole", z=1)
    C = screen_C(cam)
    fr = R.st("locker_board").render(cam, [(boot, None, None, 1.0)], dof=6.0)
    M = C @ boot.matrix()
    def S(x, y):                                           # sheet coords -> screen
        q = M @ np.float64([(x - boot.d.ox) * 4, (y - boot.d.oy) * 4, 1]); return q[0], q[1]
    lay = np.zeros((OH, OW, 3), np.float32); al = np.zeros((OH, OW), np.float32)
    ink = (0.07, 0.06, 0.06)
    wrap = min(1.0, max(0.0, (u - 0.05) / 0.6))
    for j, yb in enumerate((1146.0, 1161.0)):              # two turns of tape round the ankle; the second one goes on now
        kk = 1.0 if j == 0 else wrap
        if kk <= 0.01: continue
        x0, x1 = 639.5, 639.5 + 51 * kk                    # the sock at the ankle: sheet x 640-690
        top = [S(xx, yb - 5 + 3 * math.sin((xx - 639.5) / 51 * math.pi)) for xx in np.linspace(x0, x1, 16)]
        bot = [S(xx, yb + 5 + 3 * math.sin((xx - 639.5) / 51 * math.pi)) for xx in np.linspace(x1, x0, 16)]
        poly = np.int32(np.round(np.float32(top + bot) * 4))
        cv2.fillPoly(lay, [poly], (0.97, 0.97, 0.95), cv2.LINE_AA, 2); cv2.fillPoly(al, [poly], 1.0, cv2.LINE_AA, 2)
        cv2.polylines(lay, [poly], True, ink, max(2, int(3 * RS)), cv2.LINE_AA, 2)
    a = al[..., None]
    fr = fr * (1 - a) + lay * a
    k = sheet_px(cam, boot.scale)
    fx, fy = S(639.5 + 51 * wrap + 10, 1166)
    acts = [(screen_actor("tape", fx, fy, k * 0.42, "c"), None, None, 1.0),
            (screen_actor("fist_R", fx + 14 * k, fy - 4 * k, k * 0.5, "c"), None, None, 1.0)]
    return paint_actors(fr, acts, CID)


def render_ins_gloves(s, t, cam):
    """the goalkeeper's gloves come up into frame and clap together once"""
    u = t - s["t0"]
    rise = ease_out(u / 0.22)
    clap = math.exp(-((u - 0.42) / 0.07) ** 2)
    sep = 0.215 * OW - 0.075 * OW * smooth((u - 0.25) / 0.17) + 0.03 * OW * smooth((u - 0.5) / 0.2)
    fr = R.st("locker_wide").render(cam, [], dof=7.0)
    k = 0.62 * OH / 152.0                                   # a glove ~62 % of the frame high
    acts = []
    for nm, sg, rot in (("glove_L", -1, 8), ("glove_R", 1, -8)):
        cx = OW / 2 + sg * (sep - 0.02 * OW * clap)
        cy = OH * (1.30 - 0.36 * rise) - 0.01 * OH * clap
        a = screen_actor(nm, cx, cy, k, "wrist")
        rr = np.vstack([cv2.getRotationMatrix2D((float(a.anchor[0]), float(a.anchor[1])), rot * (1 - clap * 0.4), 1.0), [0, 0, 1]])
        acts.append((a, None, rr, 1.0))
    return paint_actors(fr, acts, CID, rim=(0.0, -1.0, 0.4, (1.0, 0.8, 0.55)))


def render_ins_laces(s, t, cam):
    """Maguire ties his boots: fists pull the laces tight, twice"""
    u = t - s["t0"]
    boot = Actor("boot_R", 800, 760, 1.55, anchor="sole", z=1)
    C = screen_C(cam)
    fr = R.st("locker_board").render(cam, [(boot, None, None, 1.0)], dof=5.5)
    M = C @ boot.matrix()
    def S(x, y):
        q = M @ np.float64([(x - boot.d.ox) * 4, (y - boot.d.oy) * 4, 1]); return q[0], q[1]
    k = sheet_px(cam, boot.scale)
    pull = 0.5 - 0.5 * math.cos(min(1.0, u / 0.75) * 2 * math.pi * 1.5)
    ex, ey = S(826, 1203)                                   # the top eyelets
    acts, lines = [], []
    for nm, sg in (("fist_L", -1), ("fist_R", 1)):
        fx = ex + sg * (16 + 20 * pull) * k
        fy = ey - (34 + 26 * pull) * k
        acts.append((screen_actor(nm, fx, fy, k * 0.5, "c"), None, None, 1.0))
        lines.append(((ex + sg * 3 * k, ey), (fx - sg * 5 * k, fy + 8 * k)))
    lay = np.zeros((OH, OW, 3), np.float32); al = np.zeros((OH, OW), np.float32)
    for (a_, b_) in lines:
        p0 = tuple(int(v * 4) for v in a_); p1 = tuple(int(v * 4) for v in b_)
        w = max(2, int(1.6 * k))
        cv2.line(lay, p0, p1, (0.07, 0.06, 0.06), w + max(2, int(0.8 * k)), cv2.LINE_AA, 2)
        cv2.line(al, p0, p1, 1.0, w + max(2, int(0.8 * k)), cv2.LINE_AA, 2)
        cv2.line(lay, p0, p1, (0.96, 0.95, 0.93), w, cv2.LINE_AA, 2)
    a = al[..., None]
    fr = fr * (1 - a) + lay * a
    return paint_actors(fr, acts, CID, rim=(0.0, -1.0, 0.3, (1.0, 0.8, 0.55)))


def render_ins_walk(s, t, cam):
    t0 = s["t0"]
    s_, b = R.face("carrick", t)
    a = Actor("ck_track", 1000, 560, 0.62, z=1, clip=600)
    Bm = R.walker(a, t, t0, s["t1"] + 1)
    return R.st("tunnel_night").render(cam, [(a, s_, Bm, 1.0)], dof=s["dof"])


def render_ins_captain(s, t, cam):
    """Bruno at the front of the line in the tunnel: up on his toes, armband on, a look back down the line"""
    u = t - s["t0"]
    s_, b = R.face("bruno", t)
    a = Actor("br_match", 1010, 470, 0.66, z=1, clip=700)
    bounce = abs(math.sin(u * math.pi * 2.6)) * 10
    Bm = R.body_for(a, b) @ body_matrix(a.anchor, dy=-bounce * 4)
    return R.st("tunnel_night").render(cam, [(a, s_, Bm, 1.0)], dof=s["dof"])


def render_carrick_board(s, t, cam):
    """Carrick beside the tactics board: he turns to it on "And most importantly" """
    s_, b = R.face("carrick", t)
    a = Actor("ck_track", 575, 425, 0.6, z=1, clip=640)
    return R.st("locker_board").render(cam, [(a, s_, R.body_for(a, b), 1.0)], dof=s["dof"], plate_fx=R.whiteboard_fx)


def render_ins_board(s, t, cam):
    s_, b = R.face("cunha", t)
    a = Actor("cu_prof", 545, 505, 0.86, anchor=(1330, 335), z=1)
    Bm = body_matrix(a.anchor, breath=b["breath"] * 0.5)
    return R.st("locker_board").render(cam, [(a, s_, Bm, 1.0)], dof=s["dof"], plate_fx=R.whiteboard_fx)


# ================================================================ SCENE 3: the dressing room
# seated on the benches (lap on the bench edge, feet on the floor). The painting's horizon is at y ~394 (the camera at
# seated eye level), so the scales follow the floor line: near-left, near-right, and two on the back bench.
SEATS = dict(maguire=("seat_mg", 252, 458, 0.74), bruno=("seat_br", 1442, 453, 0.475),
             mainoo=("seat_km", 700, 434, 0.274), cunha=("seat_cu", 1020, 434, 0.278))


def dressing_actors(t, who=None):
    acts = []
    for ch, (dr, x, y, sc) in SEATS.items():
        if who and ch not in who: continue
        a = Actor(dr, x, y, sc, anchor="lap", z=sc)
        s_, b = R.face(ch, t)
        acts.append((a, s_, R.body_for(a, b), 1.0))
    return acts


def carrick_centre(t):
    a = Actor("ck_track", 836, 600, 0.47, anchor="feet", z=0.45)
    s_, b = R.face("carrick", t)
    return (a, s_, R.body_for(a, b), 1.0)


def render_dress_wide(s, t, cam):
    return R.st("locker_wide").render(cam, dressing_actors(t) + [carrick_centre(t)], dof=0)


def behind(acts):
    """plate_fx that paints actors into the plate, so the depth of field blurs them with the room"""
    def fx(bg, Aw):
        return paint_actors(bg, acts, np.vstack([Aw.astype(np.float64), [0, 0, 1]]))
    return fx


def render_dress_carrick(s, t, cam):
    """Carrick centre; the two on the back bench are behind him, out of focus"""
    back = dressing_actors(t, ("mainoo", "cunha"))
    front = dressing_actors(t, ("maguire", "bruno")) + [carrick_centre(t)]
    return R.st("locker_wide").render(cam, front, dof=s["dof"], plate_fx=behind(back))


def render_dress_bruno(s, t, cam):
    return R.st("locker_wide").render(cam, dressing_actors(t, ("bruno", "cunha")), dof=s["dof"])


def render_dress_maguire(s, t, cam):
    """Maguire's close-up: the drawn visemes (neutral bust + mouth), procedural blinks / gaze / nod on top"""
    s_, b = R.face("maguire", t)
    v = cast.MG_VIS.get(s_["vis"], "rest")
    s_ = dict(s_, vis="REST")
    a = Actor("mg_v_" + v, 256, 262, 0.41, anchor="neck", z=1)
    return R.st("locker_wide").render(cam, [(a, s_, R.body_for(a, b), 1.0)], dof=s["dof"])


# ================================================================ SCENE 4: the match (3D pitch)
KIT = {"br": "br_b_match", "cu": "cu_b_match", "km": "km_b_match", "mg": "mg_t_front"}
UTD_PARTS = ["br_b_match", "cu_b_match", "km_b_match", "mg_t_front"]
HULL_PARTS = ["mg_t_front", "mg_t_q34"]                 # generic Hull players: Maguire's flat drawings, own hair and skin


def formation(side, rng):
    """kick-off shape: side -1 = United (left half), +1 = Hull (right half)"""
    xs = [4, 16, 16, 16, 16, 30, 30, 30, 44, 44, 51]
    ys = [34, 10, 26, 42, 58, 18, 34, 50, 22, 46, 34]
    out = []
    for i, (x, y) in enumerate(zip(xs, ys)):
        X = 52.5 + side * (52.5 - x) if side > 0 else x
        out.append((X + rng.uniform(-1.5, 1.5), y + rng.uniform(-2, 2), i == 0))
    return out


@functools.lru_cache(maxsize=1)
def kickoff_players():
    rng = np.random.default_rng(5)
    pl = []
    for i, (x, y, gk) in enumerate(formation(-1, rng)):
        pl.append(dict(x=x, y=y, part="mg_t_front" if gk else UTD_PARTS[i % 4], kit="gk_utd" if gk else "home",
                       flip=False, look=4 if gk else -1))
    for i, (x, y, gk) in enumerate(formation(1, rng)):
        pl.append(dict(x=x, y=y, part=HULL_PARTS[i % 2], kit="gk_hull" if gk else "hull", flip=True, look=i))
    return pl


def drift(players, t, amp=0.6, speed=1.0, seed=0):
    out = []
    for i, p in enumerate(players):
        q = dict(p)
        q["x"] += amp * math.sin(0.9 * t * speed + i * 1.7 + seed) + speed * 0.4 * t * (1 if i < 11 else -1) * 0.2
        q["y"] += amp * math.cos(0.7 * t * speed + i * 2.3 + seed)
        q["z"] = abs(math.sin(t * 7 + i)) * 0.03
        out.append(q)
    return out


def bug(fr, t, hs, as_, clock, k=1.0):
    return G.score_bug(fr, "HUL", hs, "MUN", as_, clock, k=k)


def handheld(c, t, amt=0.25):
    p, tg, fov = c
    j = (amt * math.sin(t * 1.3 + 0.4), amt * math.cos(t * 1.1), amt * 0.5 * math.sin(t * 1.7 + 1))
    return P.Cam(p, (tg[0] + j[0], tg[1] + j[1], tg[2] + j[2]), fov)


def lerp3(a, b, u):
    return tuple(x + (y - x) * u for x, y in zip(a, b))


def render_match_wide(s, t, cam):
    """broadcast wide at kick-off: the ball rolled back, the shape moves; the score bug comes on"""
    u = t - s["t0"]
    c = handheld(((52.5, -30 + 0.4 * u, 21), (52.5 - 1.2 * u, 30, 0), 50 - 1.0 * u), t, 0.15)
    pl = drift(kickoff_players(), u, 0.5)
    ko = 0.35
    if u < ko: ball = (52.5, 34, 0.11)
    else:
        k = ease_out((u - ko) / 0.9)
        ball = (52.5 - 9 * k, 34 + 3 * k, 0.11)
    img = P.render(c, t, pl, ball)
    return bug(img, t, 0, 0, "00:0%d" % min(9, int(u + 1)), k=smooth((u - 0.5) / 0.3))


def render_match_crowd(s, t, cam):
    """the home end: a telephoto on the stand behind the goal, the crowd bouncing"""
    u = t - s["t0"]
    c = handheld(((70, 12, 3.0), (118, 38 - 0.8 * u, 8.5), 24), t, 0.12)
    img = P.background(c, t * 2.2, 0.0)
    return img


# the corner (goal 1): Hull take it from the far corner flag; the United defender gets a weak head to it,
# it drops to a Hull player on the penalty spot, in off the post side.
CORNER = dict(flag=(104.6, 67.4), meet=(100.4, 37.0, 2.15), drop=(95.2, 31.2, 0.11), goal=(105.4, 36.4, 0.8))


@functools.lru_cache(maxsize=1)
def corner_setup():
    rng = np.random.default_rng(8)
    hull = [(99.5, 38.5), (97.5, 30.0), (98.8, 41.5), (95.0, 36.0), (101.5, 33.0), (92.0, 30.5)]
    utd = [(100.2, 36.2), (98.4, 32.0), (97.2, 39.5), (99.6, 42.0), (102.0, 30.5), (94.0, 33.5), (91.0, 38.0)]
    pl = []
    for i, (x, y) in enumerate(hull):
        pl.append(dict(x=x, y=y, part=HULL_PARTS[i % 2], kit="hull", flip=i % 2 == 0, role="hull%d" % i, look=i + 1))
    for i, (x, y) in enumerate(utd):
        pl.append(dict(x=x, y=y, part=UTD_PARTS[i % 4] if i else "mg_t_front", kit="home", flip=False, role="utd%d" % i))
    pl.append(dict(x=104.4, y=34.2, part="mg_t_front", kit="gk_utd", flip=True, role="gk", look=4))
    pl.append(dict(x=105.8, y=69.0, part="mg_t_q34", kit="hull", flip=False, role="taker", look=0))
    return pl


def bez(p0, p1, p2, u):
    return tuple((1 - u) ** 2 * a + 2 * (1 - u) * u * b + u * u * c for a, b, c in zip(p0, p1, p2))


def corner_ball(u):
    """ball position at shot time u (s) and the trail"""
    fl = (CORNER["flag"][0], CORNER["flag"][1], 0.11)
    kick, meet, drop, shot, net = 0.55, 1.35, 1.72, 1.95, 2.18
    def pos(v):
        if v < kick: return fl
        if v < meet:
            w = (v - kick) / (meet - kick)
            return bez(fl, (103.5, 49, 9.5), CORNER["meet"], w)
        if v < drop:
            w = (v - meet) / (drop - meet)
            p = lerp3(CORNER["meet"], CORNER["drop"], w)
            return (p[0], p[1], CORNER["meet"][2] * (1 - w) + 0.11 + 1.2 * math.sin(w * math.pi) * 0.5)
        if v < shot: return CORNER["drop"]
        if v < net:
            w = (v - shot) / (net - shot)
            return lerp3(CORNER["drop"], CORNER["goal"], w)
        w = min(1.0, (v - net) / 0.35)
        g = CORNER["goal"]
        return (g[0] + 0.5 * w, g[1], max(0.11, g[2] - 0.7 * w))
    trail = [pos(u - k * 0.025) for k in range(6, 0, -1)] if kick < u < net else []
    return pos(u), trail


def corner_players(u):
    out = []
    celebrate = max(0.0, u - 2.2)
    for p in corner_setup():
        q = dict(p); r = p["role"]
        jit = 0.25 * math.sin(u * 5 + hash(r) % 7)
        if r == "taker":
            run = smooth((u - 0.05) / 0.5)
            q["x"], q["y"] = 106.4 - 1.8 * run, 69.8 - 2.0 * run
        elif r == "utd0":                                  # the header that isn't a clearance
            q["z"] = 0.45 * math.exp(-((u - 1.33) / 0.12) ** 2)
            q["x"] += jit * 0.3
        elif r == "hull1":                                 # the scorer: onto the drop, shoots, wheels away
            k = smooth((u - 1.35) / 0.4)
            q["x"], q["y"] = 97.5 + (95.6 - 97.5) * k, 30.0 + (30.6 - 30.0) * k
            if celebrate > 0:
                q["x"] -= 3.5 * celebrate; q["y"] -= 4.5 * celebrate
        elif r == "gk":
            dive = smooth((u - 1.98) / 0.2)
            q["y"] = 34.2 + 1.6 * dive; q["lean"] = -60 * dive; q["z"] = 0.3 * math.sin(dive * math.pi)
        elif r.startswith("hull") and celebrate > 0:
            q["x"] -= 2.5 * celebrate; q["y"] -= 3.0 * celebrate
        else:
            q["x"] += jit; q["y"] += 0.3 * math.cos(u * 4 + hash(r) % 5)
        out.append(q)
    return out


def render_match_corner(s, t, cam):
    u = t - s["t0"]
    ball, trail = corner_ball(u)
    k = smooth(u / 3.4)
    c = handheld(((80 + 3 * k, -17, 14), (99.0 + 1.5 * k, 38.5 - 1.5 * k, 1.0), 25 - 4 * k), t, 0.1)
    bulge = 0.6 * math.exp(-((u - 2.3) / 0.25) ** 2)
    cheer = 1.0 if u > 2.25 else 0.0
    img = P.render(c, t, corner_players(u), ball, trail, crowd=cheer, bulge=bulge, bulge_y=36.4)
    return bug(img, t, 0, 0, "22:4%d" % min(9, int(u) + 6))


# the second dead ball: a free kick whipped in, ricochets round the six-yard box, over the line
CHAOS_PTS = [(78.0, 22.0, 0.11), (101.0, 31.5, 1.2), (99.5, 36.5, 0.4), (102.6, 34.5, 1.4), (100.8, 38.4, 0.3),
             (103.7, 36.6, 0.5), (105.3, 35.9, 0.2)]
CHAOS_T = [0.55, 1.35, 1.62, 1.9, 2.15, 2.42, 2.75]


def chaos_ball(u):
    def pos(v):
        if v < CHAOS_T[0]: return CHAOS_PTS[0]
        for i in range(len(CHAOS_T) - 1):
            if v < CHAOS_T[i + 1]:
                w = (v - CHAOS_T[i]) / (CHAOS_T[i + 1] - CHAOS_T[i])
                a, b = CHAOS_PTS[i], CHAOS_PTS[i + 1]
                hmax = 4.0 if i == 0 else 0.9
                p = lerp3(a, b, w)
                return (p[0], p[1], p[2] + hmax * math.sin(w * math.pi))
        return (105.6, 35.9, 0.11)
    trail = [pos(u - k * 0.022) for k in range(6, 0, -1)] if CHAOS_T[0] < u < CHAOS_T[-1] else []
    return pos(u), trail


@functools.lru_cache(maxsize=1)
def chaos_setup():
    rng = np.random.default_rng(12)
    pl = []
    spots = [(101.2, 31.0), (99.2, 36.0), (102.8, 34.0), (100.6, 38.8), (103.2, 37.4), (98.0, 33.0), (97.0, 40.0),
             (100.0, 29.0), (96.0, 35.0), (102.0, 41.5), (95.0, 31.5), (98.5, 42.5)]
    for i, (x, y) in enumerate(spots):
        hull = i % 2 == 1
        pl.append(dict(x=x, y=y, part=HULL_PARTS[i // 2 % 2] if hull else UTD_PARTS[i // 2 % 4],
                       kit="hull" if hull else "home", flip=hull, role="p%d" % i, look=i if hull else -1))
    pl.append(dict(x=104.5, y=34.5, part="mg_t_front", kit="gk_utd", flip=True, role="gk", look=4))
    pl.append(dict(x=77.0, y=21.2, part="mg_t_q34", kit="hull", flip=True, role="taker", look=2))
    return pl


def chaos_players(u):
    out = []
    for p in chaos_setup():
        q = dict(p)
        r = p["role"]
        if r == "taker":
            run = smooth((u - 0.1) / 0.45)
            q["x"], q["y"] = 75.4 + 2.2 * run, 20.0 + 1.6 * run
        elif r == "gk":                                      # flails at everything, reaches nothing
            q["y"] = 34.5 + 1.2 * math.sin(u * 7); q["lean"] = 35 * math.sin(u * 9) * smooth((u - 1.3) / 0.2)
        else:
            k = smooth((u - 1.2) / 0.3)
            q["x"] += k * 0.8 * math.sin(u * 8 + hash(r) % 9); q["y"] += k * 0.8 * math.cos(u * 7 + hash(r) % 5)
            for tt in CHAOS_T[1:-1]:                         # whoever the ball hits jumps
                bp, _ = chaos_ball(tt)
                if abs(bp[0] - p["x"]) < 1.6 and abs(bp[1] - p["y"]) < 1.6:
                    q["z"] = 0.35 * math.exp(-((u - tt) / 0.1) ** 2)
            if u > 2.95 and (hash(r) % 2 == 1) == (p["kit"] == "hull"):
                q["x"] -= 1.8 * (u - 2.95); q["y"] -= 2.2 * (u - 2.95)
        out.append(q)
    return out


def render_match_chaos(s, t, cam):
    u = t - s["t0"]
    ball, trail = chaos_ball(u)
    k = smooth(u / 4.0)
    c = handheld(((82, -12, 12), (97.5 + 3 * k, 34.5, 1.0), 27 - 5 * k), t, 0.14)
    bulge = 0.5 * math.exp(-((u - 2.85) / 0.25) ** 2)
    img = P.render(c, t, chaos_players(u), ball, trail, crowd=1.0 if u > 2.8 else 0.0, bulge=bulge, bulge_y=35.9)
    img = bug(img, t, 1, 0, "60:5%d" % min(9, int(u) + 2))
    # the broadcaster's caption
    return G.lower_third(img, u - 0.2, 3.6, "SET PIECE", "(again)")


# pitch-level shots in front of the far stand: a low telephoto, heavy depth of field
LOW = ((52.0, -3.0, 1.55), (52.0, 74.0, 7.0), 24)


@functools.lru_cache(maxsize=6)
def _low(var, cheer, dx):
    c = P.Cam(LOW[0], (LOW[1][0] + dx, LOW[1][1], LOW[1][2]), LOW[2])
    return blur(P.background(c, var / 5.0 + 1e-3, cheer), 6.0)


def low_plate(t, cheer=0.0, dx=0.0):
    """the far stand behind a pitch-level shot (blurred); the crowd sways between two drawings; a handheld drift
    returned as a screen offset so the characters move with it"""
    bg = _low(int(t * 5) % 2, cheer, dx)
    sx = RS * (5 * math.sin(1.3 * t + 0.4) + 2 * math.sin(2.9 * t))
    sy = RS * (3 * math.cos(1.1 * t) + 1.5 * math.sin(2.3 * t + 1))
    bg = cv2.warpAffine(bg, np.float32([[1, 0, sx], [0, 1, sy]]), (OW, OH), borderMode=cv2.BORDER_REFLECT)
    return bg, (sx, sy)


def shaken_C(cam, off):
    C = screen_C(cam); C[0, 2] += off[0]; C[1, 2] += off[1]; return C


RIM_FLOOD = (0.2, -1.0, 0.55, (0.85, 0.92, 1.0))


def render_match_touchline(s, t, cam):
    """Carrick on the touchline: completely still"""
    bg, off = low_plate(t, 0.0, -6.0)
    s_, b = perf.state("carrick", t, None, 1.0, 0.2)
    a = Actor("ck_track", 480, 330, 1.02, z=1, clip=620)
    Bm = body_matrix(a.anchor, breath=b["breath"] * 0.6)
    fr = paint_actors(bg, [(a, s_, Bm, 1.0)], shaken_C(cam, off), rim=RIM_FLOOD)
    return bug(fr, t, 1, 0, "24:1%d" % min(9, int(t - s["t0"])))


def render_match_bruno(s, t, cam):
    bg, off = low_plate(t, 0.0, 8.0)
    s_, b = R.face("bruno", t)
    a = Actor("br_match", 470, 340, 1.0, z=1, clip=640)
    fr = paint_actors(bg, [(a, s_, R.body_for(a, b), 1.0)], shaken_C(cam, off), rim=RIM_FLOOD)
    return bug(fr, t, 2, 0, "90+4")


def render_match_maguire(s, t, cam):
    """Maguire slowly turns away: front, three-quarter, side, back"""
    bg, off = low_plate(t, 0.0, 14.0)
    u = (t - s["t0"]) / 2.1
    seq = [("mg_front", False), ("mg_q34", True), ("mg_side", False), ("mg_back", False)]
    i = 0 if u < 0.30 else min(3, 1 + int((u - 0.30) / 0.2))
    nm, fl = seq[i]
    a = Actor(nm, 480, 405, 1.72, anchor="neck", z=1, flip=fl)
    if i == 0:
        s_, b = R.face("maguire", t)
        acts = [(a, s_, R.body_for(a, b), 1.0)]
    else:
        acts = [(a, None, body_matrix(a.anchor, breath=0.004 * math.sin(t * 1.9)), 1.0)]
    fr = paint_actors(bg, acts, shaken_C(cam, off), rim=RIM_FLOOD)
    return bug(fr, t, 2, 0, "90+4")


def render_black(s, t, cam):
    return np.zeros((OH, OW, 3), np.float32)


# ================================================================ the tunnel at night: the mouth shows our match
MOUTH = [(806, 300), (820, 287), (1186, 287), (1198, 300), (1198, 445), (1160, 492), (1160, 578), (850, 578),
         (850, 492), (806, 445)]


def tunnel_night():
    out = "build/bg/tunnel_night.png"
    if not os.path.exists(out):
        src = cv2.imread("build/bg/tunnel_view.png")[..., ::-1].astype(np.float32) / 255
        H, W = src.shape[:2]
        x0, y0, x1, y1 = 800 * 4, 280 * 4, 1204 * 4, 590 * 4
        # render the pitch view at the size of the mouth region (a separate, local camera)
        ow, oh = P.OW, P.OH
        P.OW, P.OH = x1 - x0, y1 - y0
        try:
            c = P.Cam((52.5, -9.0, 1.7), (52.5, 70.0, 6.5), 58)
            view = P.background(c, 0.0, 0.0)
            view = P.draw_goal(view, c, 0.0, -1); view = P.draw_goal(view, c, P.L_, 1)
        finally:
            P.OW, P.OH = ow, oh
        m_ = np.zeros((H // 4, W // 4), np.uint8)
        cv2.fillPoly(m_, [np.int32(MOUTH)], 255, cv2.LINE_AA)
        m4 = cv2.resize(m_, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255
        full = src.copy()
        full[y0:y1, x0:x1] = view
        img = src * (1 - m4) + full * m4
        # the corridor is lit by the floodlights through the mouth: a cool spill on the floor
        cv2.imwrite(out, (np.clip(img, 0, 1)[..., ::-1] * 255 + 0.5).astype(np.uint8))
    return out


SETUPS = {
    "ext_stadium": render_ext_stadium,
    "ins_boots": lambda s, t, c: render_ins_plate(s, t, c, "locker_board"),
    "ins_shirts": lambda s, t, c: render_ins_plate(s, t, c, "locker_wide"),
    "ins_tape": render_ins_tape,
    "ins_gloves": render_ins_gloves,
    "ins_walk": render_ins_walk,
    "ins_captain": render_ins_captain,
    "ins_laces": render_ins_laces,
    "ins_board": render_ins_board,
    "carrick_board": render_carrick_board,
    "dress_wide": render_dress_wide,
    "dress_carrick": render_dress_carrick,
    "dress_bruno": render_dress_bruno,
    "dress_maguire": render_dress_maguire,
    "match_wide": render_match_wide,
    "match_crowd": render_match_crowd,
    "match_corner": render_match_corner,
    "match_chaos": render_match_chaos,
    "match_touchline": render_match_touchline,
    "match_bruno": render_match_bruno,
    "match_maguire": render_match_maguire,
    "black34": render_black,
}
DRESS = (1.03, 0.99, 0.95)
NIGHT = (0.97, 1.0, 1.03)
GRADE = {"ext_stadium": (1.02, 0.98, 0.96), "ins_boots": DRESS, "ins_shirts": DRESS, "ins_tape": DRESS, "ins_gloves": DRESS,
         "ins_walk": (0.97, 0.99, 1.02), "ins_captain": (0.97, 0.99, 1.02), "ins_laces": DRESS, "ins_board": DRESS,
         "dress_wide": DRESS, "dress_carrick": DRESS, "dress_bruno": DRESS, "dress_maguire": DRESS,
         "match_wide": NIGHT, "match_crowd": NIGHT, "match_corner": NIGHT, "match_chaos": NIGHT, "match_touchline": NIGHT,
         "match_bruno": NIGHT, "match_maguire": NIGHT}
NO_GRADE = {"black34"}

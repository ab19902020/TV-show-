"""Render Episode 1, scenes 1-4.
  python3 render.py still T [T ...]        -> build/stills/still_<T>.jpg
  python3 render.py chunk A B out.mp4      -> frames [A, B) (1080p, x264 CRF 16, no audio)
Every frame: find the shot, evaluate its camera (ease + documentary handheld drift), build the setup (set, actors
with their face / body state, TV screen, graphics), then the grade (bloom, vignette, grain)."""
import sys, os, math, time, subprocess, functools, numpy as np, cv2
import engine as E
import perf, direction as D, graphics as G, stage
from stage import Actor, Stage, body_matrix
import sets

FPS, OW, OH, RS = 30, E.OW, E.OH, E.RS
TOTAL = perf.TL["total"]
NFR = int(round(TOTAL * FPS))
m, T_, E_, W_ = perf.m, D.T, D.E, D.W


def smooth(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)


def ease(u, kind):
    u = min(max(u, 0.0), 1.0)
    if kind == "linear": return u
    return 0.5 - 0.5 * math.cos(math.pi * u)


# ---------------------------------------------------------------- stages (loaded lazily, a few kept)
PLATES = {
    "board": lambda: sets.boardroom(),
    "training": lambda: Stage("build/bg/training.png", name="training"),
    "corridor": lambda: Stage("build/bg/corridor.png", name="corridor"),
    "corridor_doors": lambda: Stage("build/bg/corridor_doors.png", name="corridor_doors"),
    "stadium": lambda: Stage("build/bg/stadium_dusk.png", name="stadium"),
    "locker_wide": lambda: Stage("build/bg/locker_wide.png", name="locker_wide"),
    "locker_board": lambda: Stage("build/bg/locker_board.png", name="locker_board"),
    "tunnel": lambda: Stage("build/bg/tunnel_view.png", name="tunnel"),
}
_ST = {}


def st(name):
    if name not in _ST:
        if len(_ST) >= 3: _ST.pop(next(iter(_ST)))
        _ST[name] = PLATES[name]()
    return _ST[name]


# ---------------------------------------------------------------- camera
def camera(s, t):
    u = ease((t - s["t0"]) / max(1e-3, s["t1"] - s["t0"]), s["ease"])
    cx, cy, w = [a + (b - a) * u for a, b in zip(s["c0"], s["c1"])]
    if s.get("punch"):                                    # a quick push-in that settles
        k = math.exp(-(t - s["t0"]) / 0.09)
        w *= 1 + 0.07 * k
    if s.get("whip"):                                     # camera finds Omar: a fast settle from the left
        k = math.exp(-(t - s["t0"]) / 0.11)
        cx -= w * 0.18 * k
    a = 0.006 * s.get("shake", 1.0)
    cx += w * a * (math.sin(2 * math.pi * 0.23 * t + 1.3) + 0.6 * math.sin(2 * math.pi * 0.51 * t + 0.2))
    cy += w * a * 0.8 * (math.sin(2 * math.pi * 0.19 * t + 2.1) + 0.5 * math.sin(2 * math.pi * 0.57 * t + 0.9))
    return cx, cy, w


# ---------------------------------------------------------------- face state helpers
def face(ch, t, flip=False, speaker=None, **over):
    s, b = perf.state(ch, t, speaker)
    s.update(over)
    if flip:
        s["lookx"], s["turn"], s["tilt"] = -s["lookx"], -s["turn"], -s["tilt"]
    return s, b


def body_for(actor, b, extra=None):
    """breathing + lean about the anchor; fwd = leaning in towards camera (scale up, drop a little)"""
    ax, ay = actor.anchor
    fwd = b.get("fwd", 0.0)
    k = 1 + 0.045 * fwd
    Bm = body_matrix((ax, ay), breath=b["breath"], lean=b["lean"], sx=k, sy=k, dy=0.02 * fwd * 400)
    if extra is not None: Bm = Bm @ extra
    return Bm


# ---------------------------------------------------------------- the boardroom
TVQ = np.float32([(853, 215), (1160, 200), (1160, 370), (853, 370)]) * 4


def jason_actor(t):
    p = perf.pose_at("jason", t, "js_tablet")
    flip = p != "js_sidepoint"
    x = 450 if p != "js_sidepoint" else 452
    return Actor(p, x, 440, 0.9, flip=flip, z=2)


A_CK = None


def board_actors(t):
    global A_CK
    if A_CK is None:
        A_CK = dict(ck=Actor("ck_suit", 232, 470, 0.6, z=3, clip=600), om=Actor("om_suit", 640, 432, 1.12, z=1, clip=260),
                    jr=Actor("jr_suit", 995, 410, 0.8, z=0, clip=260))
    out = []
    for key_, ch in (("ck", "carrick"), ("om", "omar"), ("jr", "jim")):
        a = A_CK[key_]
        s, b = face(ch, t)
        out.append((a, s, body_for(a, b), 1.0))
    a = jason_actor(t)
    s, b = face("jason", t, flip=a.flip)
    out.append((a, s, body_for(a, b), 1.0))
    return out


def tv_content(t):
    """what the boardroom screen shows at time t: (rgb 720x1280 float) or None when it is off"""
    if m("tap1") <= t < m("tap_ok"):
        return G.to_np(G.slide_connecting(t))
    if t < m("tap_ok"):
        return None
    cl = W_("js_well", "clarity")
    words = [(cl, "CLARITY", "3 / 47"), (T_("js_alignment"), "ALIGNMENT", "4 / 47"), (T_("js_sustain"), "SUSTAINABILITY", "5 / 47"),
             (T_("js_agility"), "AGILITY", "6 / 47")]
    if t < cl - 0.05:
        return G.to_np(G.slide_title(t - m("tap_ok")))
    if t < m("cutaway_pres"):
        cur = words[0]
        for w in words:
            if t >= w[0] - 0.05: cur = w
        return slide_cached(f"word:{cur[1]}|{cur[2]}", min(1.0, (t - cur[0] + 0.05) / 0.5))
    if t < m("sale_graphic"):
        return slide_cached("options", min(1.0, (t - m("cutaway_pres")) / 1.2))
    if t < m("scroll1"):
        return slide_cached("sales", min(1.0, (t - m("sale_graphic")) / 1.4))
    if t < m("scroll2"):
        return G.to_np(G.tv_slide("targets", t - m("scroll1")))
    if t < m("chime"):
        return G.to_np(G.tv_slide("targets2", min(t - m("scroll2"), 2.0)))
    if t < m("screen_on"):
        return G.call_frame([], [], "ringing", t - m("chime"))
    if t < m("call_ends"):
        return call_feed(t)
    if t < m("call_ends") + 1.2:
        return G.call_frame([], [], "ended", 0)
    return None


@functools.lru_cache(maxsize=4)
def _slide(name, k):
    return G.to_np(G.tv_slide(name, k))


def slide_cached(name, k):
    return _slide(name, round(k * 20) / 20)


@functools.lru_cache(maxsize=1)
def glass_layer():
    yy = np.linspace(0, 1, OH, dtype=np.float32)[:, None, None]
    return 0.035 * np.clip(1 - np.abs(np.linspace(-1, 1, OW, dtype=np.float32)[None, :, None] + yy - 0.9) * 3, 0, 1)


def screen_fx(t):
    content = tv_content(t)
    if content is None: return None

    def fx(bg, Aw):
        q = cv2.transform(TVQ[None], Aw)[0]
        ch_, cw_ = content.shape[:2]
        H = cv2.getPerspectiveTransform(np.float32([(0, 0), (cw_, 0), (cw_, ch_), (0, ch_)]), q.astype(np.float32))
        img = cv2.warpPerspective(content, H, (OW, OH), flags=cv2.INTER_AREA if Aw[0, 0] < 1.2 else cv2.INTER_LINEAR)
        msk = cv2.warpPerspective(np.ones((ch_, cw_), np.float32), H, (OW, OH), flags=cv2.INTER_LINEAR)[..., None]
        # glass: a faint diagonal reflection, the screen a touch lifted
        scr = img * 0.93 + 0.02 + glass_layer()
        return bg * (1 - msk) + scr * msk
    return fx


def render_board(s, t, cam):
    fx = screen_fx(t)
    acts = board_actors(t)
    fg = []
    # Carrick's polite half-wave (scene 2): his forearm rises from below the frame, palm to the screen
    hw = m("half_wave")
    if hw - 0.1 < t < hw + 1.2 and s["c0"][0] < 400:
        k = smooth((t - hw) / 0.28) * smooth((hw + 1.15 - t) / 0.32)
        ang = -118 + 7 * math.sin((t - hw) * 10.5) * k
        hand = Actor("ck_hand_palm_s", 318, 612 - 62 * k, 0.6, anchor=(1158, 322), z=5)
        R = np.vstack([cv2.getRotationMatrix2D((float(hand.anchor[0]), float(hand.anchor[1])), ang, 1.0), [0, 0, 1]])
        fg.append((hand, None, R, 1.0))
    return st("board").render(cam, acts, dof=s["dof"] or 0.0, plate_fx=fx, occ_dof=(s["dof"] or 0) * 0.6, fg_actors=fg)


# ---------------------------------------------------------------- the video call
_MONACO = None


def monaco():
    global _MONACO
    if _MONACO is None:
        _MONACO = cv2.imread("../../jim-ratcliffe-ineos-office/src/office.png")[..., ::-1].astype(np.float32) / 255
    return _MONACO


def tile_bg(box, size, t, shimmer=True):
    x0, y0, x1, y1 = box
    c = monaco()[y0:y1, x0:x1]
    c = cv2.resize(c, size, interpolation=cv2.INTER_CUBIC)
    c = cv2.GaussianBlur(c, (0, 0), 2.2 * RS)
    if shimmer:     # sea light: a slow caustic shimmer
        h, w = c.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        s = 0.5 + 0.5 * np.sin(xx / (23 * RS) + t * 2.1) * np.sin(yy / (17 * RS) - t * 1.7)
        c = c * (1 + 0.05 * s[..., None]) + np.float32([0.04, 0.03, 0.0])
    return np.clip(c * 1.08, 0, 1)


def draw_into(buf, actor, st_, extra=None):
    """draw one actor into a small RGBA canvas where world px == canvas px x4 (actor x, y in canvas px / 4)"""
    H, W = buf.shape[:2]
    C = np.array([[0.25, 0, 0], [0, 0.25, 0], [0, 0, 1]], np.float64)     # world (x4) -> canvas px
    dummy = Stage.__new__(Stage); dummy.rim = None; dummy.ambient = np.float32([1, 1, 1])
    Stage.draw_actor(dummy, buf, C, actor, st_, extra, 1.0)


def joel_tile(t, size):
    w, h = size
    bg = tile_bg((1060, 250, 1560, 610), size, t)
    buf = np.zeros((h, w, 4), np.float32)
    waving = (T_("jg_hello") - 0.25 <= t < E_("jg_hello") + 0.5) or (T_("jg_go_united") - 0.3 <= t < m("call_ends"))
    if waving:
        s, b = face("joel", t)
        rock = 5 * math.sin((t - T_("jg_hello")) * 11)
        a = Actor("jg_wave", w * 0.5, h * 0.60, min(w, 620 * RS) / 177.0, anchor="collar")
        ax, ay = a.anchor
        R = np.vstack([cv2.getRotationMatrix2D((float(ax), float(ay + 400)), rock, 1.0), [0, 0, 1]])
        draw_into(buf, a, s, R)
    else:
        s, b = face("joel", t)
        a = Actor("jg_jumper", w * 0.5, h * 0.80, min(w, 620 * RS) / 245.0, anchor="collar")
        draw_into(buf, a, s, body_for(a, b))
    return bg * (1 - buf[..., 3:4]) + buf[..., :3]


def avram_tile(t, size):
    w, h = size
    bg = tile_bg((640, 330, 1000, 700), size, t)
    buf = np.zeros((h, w, 4), np.float32)
    s, b = face("avram", t)
    leave = smooth((t - (E_("av_need_to_run") + 0.15)) / 0.55)
    if T_("av_need_to_run") - 0.9 < t:
        s["lookx"], s["turn"] = -1.0, -0.4                 # someone is calling him away (off camera, left)
    a = Actor("av_jumper", w * 0.5 - leave * w * 1.1, h * 0.80, min(w, 620 * RS) / 245.0, anchor="collar")
    draw_into(buf, a, s, body_for(a, b))
    return bg * (1 - buf[..., 3:4]) + buf[..., :3]


def call_feed(t):
    one = t >= E_("av_need_to_run") + 0.9
    if one:
        tiles = [joel_tile(t, (int(1252 * RS), int(646 * RS)))]
        labels = ["Joel Glazer"]
    else:
        tiles = [joel_tile(t, (int(619 * RS), int(646 * RS))), avram_tile(t, (int(619 * RS), int(646 * RS)))]
        labels = ["Joel Glazer", "Avram Glazer"]
    img = G.call_frame(tiles, labels, "call", t)
    # connecting fade-in
    k = smooth((t - m("screen_on")) / 0.35)
    img = img * k + 0.12 * (1 - k)
    # someone adjusts the volume
    v = m("volume")
    if v <= t < v + 1.3:
        from PIL import Image, ImageDraw
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)); d = G.SD(im)
        lvl = 0.35 + 0.35 * smooth((t - v - 0.15) / 0.5)
        d.rounded_rectangle([1150, 180, 1210, 520], radius=18, fill=(20, 20, 24))
        d.rounded_rectangle([1172, 200, 1188, 500], radius=8, fill=(90, 90, 96))
        d.rounded_rectangle([1172, 500 - 300 * lvl, 1188, 500], radius=8, fill=(240, 240, 240))
        img = np.asarray(im).astype(np.float32) / 255
    return img


# ---------------------------------------------------------------- other setups
def lower3(frame, t, t0, dur, a, b):
    return G.lower_third(frame, t - t0, dur, a, b)


def render_ext_carrington(s, t, cam):
    fr = st("training").render(cam, [], dof=0)
    return lower3(fr, t, 0.5, 3.3, "CARRINGTON", "Manchester United training ground   |   Tuesday, 8:47 am")


def silhouette(frame, t, t0, t1, drawing, y, scale, direction):
    """a dark, out-of-focus figure crossing close to the lens"""
    if not t0 <= t <= t1: return frame
    u = (t - t0) / (t1 - t0)
    x = (-0.25 + 1.5 * u) * OW if direction > 0 else (1.25 - 1.5 * u) * OW
    d = stage.cast.get(drawing)
    img = d.base(0.25)
    sc = scale * RS / 0.25
    A = np.float32([[sc, 0, x - sc * img.shape[1] / 2], [0, sc, y - sc * img.shape[0] * 0.35]])
    lay = np.zeros((OH, OW, 4), np.float32)
    E.warp_into(lay, img, A)
    a = np.clip(cv2.GaussianBlur(lay[..., 3], (0, 0), 26 * RS) * 1.4, 0, 1)[..., None]
    col = cv2.GaussianBlur(lay[..., :3], (0, 0), 26 * RS) * 0.18
    return frame * (1 - a) + col


def render_corridor_staff(s, t, cam):
    fr = st("corridor").render(cam, [], dof=1.0)
    t0 = m("corridor")
    fr = silhouette(fr, t, t0 + 0.2, t0 + 1.2, "js_body", OH * 0.2, 0.55, +1)
    fr = silhouette(fr, t, t0 + 1.25, t0 + 2.35, "om_suit", OH * 0.25, 1.9, -1)
    return fr


def walker(actor, t, t0, t_stop, step=0.52, amp=6.0):
    """bob + sway for a walk towards camera (part-space body matrix), settling when he stops"""
    ax, ay = actor.anchor
    go = 1 - smooth((t - t_stop) / 0.45)
    ph = (t - t0) / step * math.pi
    bob = -abs(math.sin(ph)) * amp * go * 4
    sway = math.sin(ph) * 1.4 * go
    skew = 0.018 * math.sin(ph) * go
    return body_matrix((ax, ay + 600), lean=sway, dy=bob, skew=skew)


def render_corridor_walk(s, t, cam):
    """waist-up tracking shot: he walks towards the retreating camera, the corridor recedes behind him; he stops,
    straightens his jacket, takes a small breath, and the boardroom door (behind the camera) opens: warm light."""
    t0 = m("walk"); stop = t0 + 3.4
    s_, b = face("carrick", t)
    cx, cy, w = cam
    w0 = s["c0"][2]
    k = w / w0                                             # actor keeps his screen size while the set recedes
    a = Actor("ck_suit", cx + 0.02 * w, cy + 0.2 * w * 9 / 16, 0.6 * k, z=1, clip=640)
    Bm = walker(a, t, t0, stop)
    tug = math.exp(-((t - (stop + 0.55)) / 0.13) ** 2)
    br = 0.012 * math.exp(-((t - (stop + 1.45)) / 0.35) ** 2)
    Bm = Bm @ body_matrix(a.anchor, breath=br + b["breath"], dy=-9 * tug * 4)
    fr = st("corridor").render(cam, [(a, s_, Bm, 1.0)], dof=s["dof"])
    if t > t0 + 5.6:                                      # the door opens: warm light spills over him
        k2 = smooth((t - (t0 + 5.6)) / 0.45)
        fr = fr * (1 + 0.22 * k2) + np.float32([0.09, 0.05, 0.015]) * k2
    return fr


def render_title(s, t, cam):
    return G.title_card(t - m("title"), m("title_end") - m("title"))


_CROWD = {}


def crowd_layers(boxes, colors, seed_=3, n_var=3):
    """RGBA crowd crops (world px) for the stands: one speck per head, small, dense; n_var bounce variants"""
    key = (tuple(boxes), seed_)
    if key in _CROWD: return _CROWD[key]
    x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes)
    x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
    W, H = int((x1 - x0) * 4), int((y1 - y0) * 4)
    rng = np.random.default_rng(seed_)
    heads = []
    for (bx0, by0, bx1, by1, n) in boxes:
        xs = rng.uniform(bx0, bx1, n); ys = rng.uniform(by0, by1, n)
        cs = rng.integers(0, len(colors), n); ph = rng.uniform(0, 1, n)
        heads.append((xs, ys, cs, ph))
    out = []
    for v in range(n_var):
        lay = np.zeros((H, W, 3), np.float32); al = np.zeros((H, W), np.float32)
        for xs, ys, cs, ph in heads:
            for x_, y_, c_, p_ in zip(xs, ys, cs, ph):
                bob = 2.5 if (p_ * n_var + v) % n_var < 1 else 0.0
                X, Y = int((x_ - x0) * 4), int((y_ - y0) * 4 - bob)
                col = colors[c_]
                cv2.ellipse(lay, (X, Y + 5), (5, 7), 0, 0, 360, tuple(c * 0.8 for c in col), -1, cv2.LINE_AA)   # shoulders
                cv2.circle(lay, (X, Y), 3, (0.86, 0.66, 0.52), -1, cv2.LINE_AA)                                  # head
                cv2.ellipse(al, (X, Y + 5), (5, 7), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
                cv2.circle(al, (X, Y), 3, 1.0, -1, cv2.LINE_AA)
        pm = np.dstack([lay * al[..., None], al]).astype(np.float32)
        out.append(pm)
    _CROWD[key] = ((x0 * 4, y0 * 4), out)
    return _CROWD[key]


def crowd_fx(boxes, colors, t):
    (ox, oy), vars_ = crowd_layers(tuple(boxes), colors)
    img = vars_[int(t * 6) % len(vars_)]

    def fx(bg, Aw):
        A = Aw.copy().astype(np.float64)
        A = (np.vstack([A, [0, 0, 1]]) @ np.array([[1, 0, ox], [0, 1, oy], [0, 0, 1]]))[:2].astype(np.float32)
        lay = np.zeros((OH, OW, 4), np.float32)
        E.warp_into(lay, img, A)
        return bg * (1 - lay[..., 3:4] * 0.92) + lay[..., :3] * 0.92
    return fx


CROWD_COLS = [(0.95, 0.62, 0.05), (0.9, 0.55, 0.05), (0.1, 0.1, 0.1), (0.85, 0.7, 0.55), (0.35, 0.25, 0.18),
              (0.95, 0.95, 0.95), (0.75, 0.1, 0.12), (0.2, 0.2, 0.25)]
STANDS = ((858, 388, 1192, 438, 2300), (858, 456, 988, 490, 900), (1042, 456, 1192, 490, 1000))


def render_ext_stadium(s, t, cam):
    fr = st("stadium").render(cam, [], dof=0)
    return lower3(fr, t, m("s3") + 0.4, 2.3, "HULL AWAY", "Premier League   |   Matchday 1   |   Kick-off 17:30")


def render_insert(s, t, cam, plate):
    return st(plate).render(cam, [], dof=0)


def render_tunnel_walk(s, t, cam):
    t0 = s["t0"]
    s_, b = face("carrick", t)
    a = Actor("ck_track", 1000, 560, 0.62, z=1, clip=600)
    Bm = walker(a, t, t0, s["t1"] + 1)
    return st("tunnel").render(cam, [(a, s_, Bm, 1.0)], dof=s["dof"], plate_fx=crowd_fx(STANDS, CROWD_COLS, t))


def render_bruno_cu(s, t, cam):
    s_, b = face("bruno", t)
    a = Actor("br_match", 1480, 445, 0.63, z=1, clip=640)
    return st("locker_wide").render(cam, [(a, s_, body_for(a, b), 1.0)], dof=s["dof"])


def render_cunha_board(s, t, cam):
    s_, b = face("cunha", t)
    a = Actor("cu_prof", 478, 452, 0.62, anchor=(1330, 335), z=1)
    Bm = body_matrix(a.anchor, breath=b["breath"] * 0.5)
    return st("locker_board").render(cam, [(a, s_, Bm, 1.0)], dof=s["dof"], plate_fx=whiteboard_fx)


def whiteboard_fx(bg, Aw):
    """SET PIECES! written on the tactics board in red marker (1x plate coords -> screen)"""
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (300, 200), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.text((18, 22), "SET PIECES!", font=G.font("BebasNeue-Regular", 62), fill=(196, 22, 28, 235))
    d.line([(20, 96), (250, 90)], fill=(196, 22, 28, 220), width=5)
    d.line([(24, 106), (238, 101)], fill=(196, 22, 28, 200), width=4)
    d.ellipse([6, 8, 282, 118], outline=(196, 22, 28, 210), width=4)
    a = np.asarray(im).astype(np.float32) / 255
    # the board sits in perspective: map the 300x200 label onto a quad on the board (1x coords)
    quad = np.float32([(28, 150), (262, 170), (262, 262), (30, 250)]) * 4
    q = cv2.transform(quad[None], Aw)[0]
    H = cv2.getPerspectiveTransform(np.float32([(0, 0), (300, 0), (300, 200), (0, 200)]), q.astype(np.float32))
    w = cv2.warpPerspective(a, H, (OW, OH), flags=cv2.INTER_LINEAR)
    al = w[..., 3:4]
    return bg * (1 - al) + w[..., :3] * al


DRESS = None


def render_dressing_wide(s, t, cam):
    acts = []
    places = [("mainoo", "km_match", 560, 618, 0.36), ("cunha", "cu_match", 1500, 650, 0.40),
              ("maguire", "mg_front", 330, 712, 0.71), ("bruno", "br_match", 1255, 706, 0.45)]
    for ch, dr, x, y, sc in places:
        a = Actor(dr, x, y, sc, anchor="feet", z=y / 1000)
        s_, b = face(ch, t)
        acts.append((a, s_, body_for(a, b), 1.0))
    a = Actor("ck_track", 836, 752, 0.47, anchor="feet", z=0.9)
    s_, b = face("carrick", t)
    acts.append((a, s_, body_for(a, b), 1.0))
    return st("locker_wide").render(cam, acts, dof=0)


def render_carrick_board(s, t, cam):
    s_, b = face("carrick", t)
    a = Actor("ck_track", 585, 462, 0.6, z=1, clip=640)
    return st("locker_board").render(cam, [(a, s_, body_for(a, b), 1.0)], dof=s["dof"], plate_fx=whiteboard_fx)


def render_board_point(s, t, cam):
    """insert: his hand comes in and taps SET PIECES on the tactics board (twice, on the two words)"""
    t_in = s["t0"]
    k = smooth((t - t_in) / 0.25)
    tap = 0.0
    for w in ("set", "pieces"):
        tw = W_("ck_set_pieces", w)
        tap += math.exp(-((t - tw - 0.02) / 0.07) ** 2)
    hand = Actor("ck_hand_point_t", 238 + 160 * (1 - k) - 10 * tap, 206 + 60 * (1 - k) - 4 * tap, 1.25,
                 anchor=(700, 362), z=3)
    return st("locker_board").render(cam, [], dof=0, plate_fx=whiteboard_fx, fg_actors=[(hand, None, None, 1.0)])


MG_VIS = {"REST": "mg_rest", "AI": "mg_A", "E": "mg_E", "I": "mg_I", "O": "mg_O", "U": "mg_U", "MBP": "mg_MBP", "FV": "mg_FV",
          "L": "mg_L", "CDG": "mg_I", "R": "mg_U", "BREATH": "mg_rest"}


def render_maguire_cu(s, t, cam):
    s_, b = face("maguire", t)
    a = Actor("mg_front", 1300, 470, 1.35, anchor="neck", z=1, clip=330)
    return st("locker_wide").render(cam, [(a, s_, body_for(a, b), 1.0)], dof=s["dof"])


def render_pitch(s, t, cam):
    fr = st("tunnel").render(cam, [], dof=0, plate_fx=crowd_fx(STANDS, CROWD_COLS, t))
    bug = s.get("bug")
    if bug:
        fr = G.score_bug(fr, *bug, k=smooth((t - s["t0"] - 0.3) / 0.3))
    return fr


def render_touchline(s, t, cam, who):
    if who == "carrick":
        s_, b = face("carrick", t)
        a = Actor("ck_track", 1010, 552, 0.52, z=1, clip=640)
        acts = [(a, s_, body_for(a, b), 1.0)]
    elif who == "bruno":
        s_, b = face("bruno", t)
        a = Actor("br_match", 1000, 552, 0.52, z=1, clip=640)
        acts = [(a, s_, body_for(a, b), 1.0)]
    else:
        u = (t - s["t0"]) / 2.4
        seq = ["mg_front", "mg_q34", "mg_side", "mg_back"]
        i = 0 if u < 0.32 else min(3, 1 + int((u - 0.32) / 0.2))
        a = Actor(seq[i], 1030, 548, 1.02, anchor="neck", z=1, clip=330)
        if i == 0:
            s_, b = face("maguire", t)
            acts = [(a, s_, body_for(a, b), 1.0)]
        else:
            acts = [(a, None, body_matrix(a.anchor, breath=0.004 * math.sin(t * 1.9)), 1.0)]
    fr = st("tunnel").render(cam, acts, dof=s["dof"], plate_fx=crowd_fx(STANDS, CROWD_COLS, t))
    return G.score_bug(fr, "HUL", 1 if t < m("goal2_card") else 2, "MUN", 0, "71:12" if t > m("goal2_card") else "24:03")


SETUPS = {
    "ext_carrington": render_ext_carrington,
    "corridor_staff": render_corridor_staff,
    "corridor_walk": render_corridor_walk,
    "board": render_board,
    "tablet": lambda s, t, c: G.tablet_insert(t - s["t0"], [0.25, 0.95], 99),
    "black": lambda s, t, c: np.zeros((OH, OW, 3), np.float32),
    "title": render_title,
    "ext_stadium": render_ext_stadium,
    "insert_boots": lambda s, t, c: render_insert(s, t, c, "locker_board"),
    "insert_shirts": lambda s, t, c: render_insert(s, t, c, "locker_board"),
    "tunnel_walk": render_tunnel_walk,
    "bruno_cu": render_bruno_cu,
    "cunha_board": render_cunha_board,
    "dressing_wide": render_dressing_wide,
    "carrick_board": render_carrick_board,
    "board_point": render_board_point,
    "maguire_cu": render_maguire_cu,
    "pitch": render_pitch,
    "tele_corner": lambda s, t, c: G.telestration(t - s["t0"], s["t1"] - s["t0"], "corner"),
    "tele_chaos": lambda s, t, c: G.telestration(t - s["t0"], s["t1"] - s["t0"], "chaos"),
    "card": lambda s, t, c: G.score_card(t - s["t0"], s["t1"] - s["t0"], *s["card"]),
    "touchline": lambda s, t, c: render_touchline(s, t, c, "carrick"),
    "pitch_bruno": lambda s, t, c: render_touchline(s, t, c, "bruno"),
    "pitch_maguire": lambda s, t, c: render_touchline(s, t, c, "maguire"),
}
GRADE = {"board": (1.02, 0.99, 0.95), "ext_carrington": (1.0, 1.0, 1.0), "corridor_staff": (0.96, 0.98, 1.02),
         "corridor_walk": (0.97, 0.98, 1.02), "dressing_wide": (1.03, 0.99, 0.95), "carrick_board": (1.03, 0.99, 0.95),
         "bruno_cu": (1.03, 0.99, 0.95), "maguire_cu": (1.03, 0.99, 0.95), "cunha_board": (1.03, 0.99, 0.95),
         "pitch": (0.97, 1.0, 1.03), "touchline": (0.97, 1.0, 1.03), "pitch_bruno": (0.97, 1.0, 1.03),
         "pitch_maguire": (0.97, 1.0, 1.03), "tunnel_walk": (0.97, 0.99, 1.02), "ext_stadium": (1.02, 0.98, 0.96)}
NO_GRADE = {"black", "title", "card", "tele_corner", "tele_chaos", "tablet"}

# scenes 3-4 (Hull away) live in hull.py
import hull
hull.bind(globals())
SETUPS.update(hull.SETUPS); GRADE.update(hull.GRADE); NO_GRADE |= hull.NO_GRADE

YY, XX = np.mgrid[0:OH, 0:OW].astype(np.float32)
RR = np.sqrt(((XX - OW / 2) / (OW / 2)) ** 2 + ((YY - OH / 2) / (OH / 2)) ** 2)
VIGN = (1 - 0.26 * np.clip(RR / 1.35, 0, 1) ** 2.2)[..., None]


def shot_at(t):
    for s in D.SHOTS:
        if s["t0"] <= t < s["t1"]: return s
    return D.SHOTS[-1]


def render_frame(i):
    t = i / FPS
    s = shot_at(t)
    cam = camera(s, t) if s["c0"] is not None else None
    f = SETUPS[s["setup"]](s, t, cam)
    if s["setup"] not in NO_GRADE:
        small = cv2.resize(f, (OW // 4, OH // 4), interpolation=cv2.INTER_AREA)
        bloom = cv2.resize(cv2.GaussianBlur(np.clip(small - 0.72, 0, None), (0, 0), 8 * RS), (OW, OH), interpolation=cv2.INTER_LINEAR)
        f = f + bloom * np.float32([0.45, 0.4, 0.35])
        f = f * np.float32(GRADE.get(s["setup"], (1, 1, 1)))
        f = np.clip((f - 0.5) * 1.05 + 0.5, 0, 1) * VIGN
    f = f + np.random.default_rng(i).normal(0, 1.4 / 255, (OH, OW, 1)).astype(np.float32)
    return np.clip(f * 255 + 0.5, 0, 255).astype(np.uint8)


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still":
        os.makedirs("build/stills", exist_ok=True)
        for a in sys.argv[2:]:
            t0 = time.time()
            img = render_frame(int(round(float(a) * FPS)))
            cv2.imwrite(f"build/stills/still_{a}.jpg", img[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 90])
            print(a, shot_at(float(a))["setup"], round(time.time() - t0, 2), flush=True)
    elif mode == "chunk":
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                              "-x264-params", "rc-lookahead=12:threads=4",
                              "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        t0 = time.time()
        for i in range(a, b):
            p.stdin.write(render_frame(i).tobytes())
            if (i - a) % 100 == 0: print(out, i, round(time.time() - t0, 1), flush=True)
        p.stdin.close(); p.wait()

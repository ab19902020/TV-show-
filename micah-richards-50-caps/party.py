"""Micah's 50 CAPS party, as Rooney sees it. Setups registered into restaurant.EXTRA by direction.py.

Every background character has ONE repeating behaviour (the brief): Jamie raises his pint, Dan claps like a maniac, Ravi holds the
50 CAPS card behind Micah like a ring-card girl, a second Ravi films on a phone, the crowd bounces. Micah is the centre of it:
strut, dance (poses + run frames, big bounce), both hands up, the freeze, and "cool" (hands in pockets).
All positions are 1x plate px of the 941 x 1672 portrait plates."""
import math, numpy as np, cv2
import perf, cast, props
from perf import W
from render_util import *

BPM = 122.0


def beat(t, phase=0.0):
    return t * BPM / 60.0 + phase


def pop(t, t_app, dur=0.22):
    """(visible, size multiplier with a little overshoot, alpha) for something that appears at t_app"""
    if t < t_app: return False, 1.0, 0.0
    u = min(1.0, (t - t_app) / dur)
    k = 1 + 0.16 * math.sin(u * math.pi) * (1 - u)
    return True, (0.55 + 0.45 * smooth(u)) * k, min(1.0, u * 2.5)


def sprite(part, x, y, scale, t, flip=False, phase=0.0, amp=10.0, sway=4.0, squash=0.04, z=None, anchor="feet", light=1.0,
           lean_extra=0.0, size=1.0, alpha=1.0, wobble=0.0, bounce_pow=0.75):
    """one animated cut-out: bounces on the beat (hop + squash + lean), `size` pops it in, `wobble` shakes it fast (clapping)"""
    a = Actor(part, x, y, scale * size, flip=flip, anchor=anchor, z=(y if z is None else z), light=light)
    b = beat(t, phase)
    h = abs(math.sin(math.pi * b)) ** bounce_pow
    lean = sway * math.cos(math.pi * b) + lean_extra
    if wobble: lean += wobble * math.sin(t * 2 * math.pi * 7.5)
    dy = -amp * h * 4 / (scale * size)
    sy = 1 - squash * (1 - h) + 0.3 * squash * h
    sx = 1 + 0.5 * squash * (1 - h)
    Bm = body_matrix(a.anchor, lean=lean, dy=dy, sx=sx, sy=sy)
    return (a, None, Bm, alpha)


# ---------------------------------------------------------------- Micah
SIZEFIX = {"mr_run": 2.48, "mr_w": 2.48, "mr_hero": 0.44}      # run / walk frames are drawn ~2.5x smaller than the standing figure


def fix(part):
    for k, v in SIZEFIX.items():
        if part.startswith(k): return v
    return 1.0


DANCE = [("mr_t_q34R", False), ("mr_t_front", False), ("mr_t_q34R", True), ("mr_run2", False)]
RUN = ["mr_run0", "mr_run1", "mr_run2", "mr_run3"]


def micah(t, x, y, scale, mode, t_mode, z=None, flip=False):
    """Micah full-body at (x, y) = feet. modes: dance, run, strut, cool, freeze, front"""
    tt = t - t_mode
    if mode == "dance":
        name, fl = DANCE[int(beat(tt)) % 4]
        return sprite(name, x, y, scale * fix(name), t, flip=fl != flip, amp=20, sway=7.5, squash=0.05, z=z)
    if mode == "run":
        name = RUN[int(tt * 9) % 4]
        return sprite(name, x, y, scale * fix(name), t, flip=flip, amp=12, sway=2.5, squash=0.03, z=z, phase=0.0)
    if mode == "strut":
        name = f"mr_w{int(tt / 0.15) % 4}"
        return sprite(name, x, y, scale * fix(name), t, flip=flip, amp=8, sway=3, squash=0.02, z=z, anchor="upper", phase=0.25)
    if mode == "freeze":
        return sprite("mr_t_q34R", x, y, scale, t, flip=not flip, amp=0, sway=0, squash=0, z=z)
    if mode == "cool":
        return sprite("mr_hero", x, y, scale * fix("mr_hero"), t, flip=flip, amp=0, sway=0.8, squash=0.0, z=z, lean_extra=0.0)
    return sprite("mr_t_front", x, y, scale, t, flip=flip, amp=0, sway=0, squash=0, z=z)


# ---------------------------------------------------------------- the friends
def jamie(t, x, y, scale, mode="cheers", **kw):
    part = dict(cheers="fr_jamie_cheers", yes="fr_jamie_yes", banter="fr_jamie_banter")[mode]
    return sprite(part, x, y, scale, t, amp=kw.pop("amp", 14), sway=kw.pop("sway", 5), **kw)


def dan(t, x, y, scale, mode="clap", **kw):
    part = dict(clap="fr_dan_clap", armsup="fr_dan_armsup", cake="fr_dan_cake")[mode]
    return sprite(part, x, y, scale, t, wobble=(9 if mode == "clap" else 0), amp=kw.pop("amp", 10), sway=kw.pop("sway", 2.5), **kw)


def ravi(t, x, y, scale, mode="placard", **kw):
    part = dict(placard="fr_ravi_placard", pointing="fr_ravi_pointing")[mode]
    return sprite(part, x, y, scale, t, amp=kw.pop("amp", 9), sway=kw.pop("sway", 3), **kw)


def phone_overlay(base, tip_sheet, scale_phone, t, ang=0.0):
    """the phone held at a finger-tip: (Actor-like tuple) drawn at the tip of `base` (an actor tuple) in front of it"""
    a = base[0]
    # sheet -> part px -> world: use the actor's matrix with the body transform
    px, py = a.d.P(*tip_sheet)
    M = a.matrix(base[2])
    wx = M[0, 0] * px + M[0, 1] * py + M[0, 2]
    wy = M[1, 0] * px + M[1, 1] * py + M[1, 2]
    ph = Actor("prop_phone", wx / 4, wy / 4, scale_phone, anchor="mid", z=a.z + 0.5)
    Bm = body_matrix(ph.anchor, lean=ang + 5 * math.sin(t * 9))
    return (ph, None, Bm, base[3])


# ---------------------------------------------------------------- the crowd ("about twenty of his guys")
def crowd_spec(seed=7, n=18, x_range=(330, 930), y_range=(840, 905), s_range=(1.15, 1.5)):
    rng = np.random.default_rng(seed)
    parts = ["fr_jamie_cheers", "fr_dan_armsup", "fr_jamie_yes", "fr_dan_clap", "fr_ravi_pointing", "fr_dan_armsup", "fr_ravi_placard", "fr_jamie_banter"]
    out = []
    for i in range(n):
        y = rng.uniform(*y_range)
        k = (y - y_range[0]) / max(1, y_range[1] - y_range[0])
        out.append(dict(part=parts[i % len(parts)], x=float(rng.uniform(*x_range)), y=float(y), s=float(s_range[0] + (s_range[1] - s_range[0]) * k * rng.uniform(0.7, 1.0)),
                        flip=bool(rng.random() < 0.5), ph=float(rng.uniform(0, 2)), amp=float(rng.uniform(6, 13)), idx=i))
    return out


CROWD = crowd_spec()


def crowd_actors(t, t_from, t_to, n=None, light=0.82, y_shift=0.0, x_shift=0.0):
    acts = []
    cs = CROWD[: n or len(CROWD)]
    for c in cs:
        t_app = t_from + (t_to - t_from) * (c["idx"] / max(1, len(CROWD) - 1))
        vis, sz, al = pop(t, t_app)
        if not vis: continue
        wob = 9 if c["part"] == "fr_dan_clap" else 0
        acts.append(sprite(c["part"], c["x"] + x_shift, c["y"] + y_shift, c["s"], t, flip=c["flip"], phase=c["ph"], amp=c["amp"], sway=4,
                           squash=0.04, light=light, size=sz, alpha=al, wobble=wob))
    return acts


# ---------------------------------------------------------------- party setups
def party_wide(s, t, cam):
    """w_entrance: the floor in front of the 50 CAPS balloon letters"""
    st = plate("w_entrance", occluders=ENTRANCE_FG + ([BACK_TABLE] if s.get("family_bg") else []))
    acts = []
    mi_mode = perf.pose_at("mi", t, "dance")
    mi_t0 = perf.mode_start("mi", t)
    mx, my = s.get("micah_xy", (540, 1050))
    if mi_mode == "strut":
        u = min(1.0, (t - mi_t0) / 0.9)
        acts.append(micah(t, mx - 330 * (1 - ease(u, "out")), my, 1.9, "strut", mi_t0))
    else:
        acts.append(micah(t, mx, my, 1.95, mi_mode, mi_t0))
    # friends, each with one action
    for key_, fn, mode0, pos in FRIEND_SLOTS:
        mode = perf.pose_at(key_, t, mode0)
        vis, sz, al = pop(t, perf.appear_time(key_, s["t0"] - 5))
        if not vis: continue
        x, y, sc, fl = pos
        if s.get("family_bg") and x > 470: continue
        base = fn(t, x, y, sc, mode, flip=fl, size=sz, alpha=al)
        acts.append(base)
        if key_ == "film":
            acts.append(phone_overlay(base, (686, 905), 1.9 * sc / 2.0, t))
    if s.get("family_bg"):
        acts += [a_ for a_ in crowd_actors(t, *perf.CROWD_WINDOW) if a_[0].x / 4 < 470]
        acts += family_background(t)
    else:
        acts += crowd_actors(t, *perf.CROWD_WINDOW)
    fr = st.render(cam, acts, dof=s.get("dof", 0.0))
    return party_fx(fr, s, t)


def ravi_filming(t, x, y, sc, mode, flip=False, **kw):
    return ravi(t, x, y, sc, "pointing", flip=flip, amp=7, **kw)


FRIEND_SLOTS = [
    # key, builder, default mode, (x, y, scale, flip)    (the 50 CAPS card and the cake carry text: never flipped)
    ("ravi", lambda t, x, y, sc, mode, flip=False, **kw: ravi(t, x, y, sc, "placard", flip=False, amp=7, **kw), "placard", (455, 945, 1.7, False)),
    ("dan", lambda t, x, y, sc, mode, flip=False, **kw: dan(t, x, y, sc, mode, flip=flip, **kw), "clap", (775, 1030, 1.9, True)),
    ("jamie", lambda t, x, y, sc, mode, flip=False, **kw: jamie(t, x, y, sc, mode, flip=flip, **kw), "cheers", (385, 1010, 1.95, False)),
    ("film", ravi_filming, "pointing", (680, 960, 1.8, True)),
]

ENTRANCE_FG = []        # foreground occluders on w_entrance (red chairs / glass at the bottom left), traced in direction.py if needed


# the table where Rooney's family sits, seen across the room (back right of the entrance plate)
BACK_TABLE = [(515, 782), (540, 742), (620, 716), (760, 706), (880, 722), (902, 792), (868, 852), (660, 882), (560, 862)]
BACK_FAMILY = {"wr": (730, 1.00), "cr": (640, 0.84), "b1": (822, 0.74), "b2": (560, 0.70), "b3": (895, 0.70), "b4": (500, 0.66)}


def family_background(t):
    acts = []
    for ch, (x, sc) in BACK_FAMILY.items():
        name, flip = pose_of(ch, t, f"{ch}_b_front")
        acts.append(bust(ch, name, x, 772, sc * 0.62, t, flip=flip, z=1.0, talks=False))
    return acts


def party_fx(fr, s, t):
    if s.get("confetti"):
        fr = props.confetti(fr, t, seed=11, count=s.get("confetti_n", 120))
    return fr


# ---------------------------------------------------------------- the 50 CAPS table (w_party): Micah in upper-body poses
PARTY_TABLE = [(240, 905), (300, 872), (400, 849), (560, 837), (700, 833), (820, 839), (941, 872), (941, 1190), (700, 1182), (480, 1188), (300, 1146)]
PLACARD_ON_TABLE = [(480, 832), (486, 712), (656, 704), (664, 832)]
CHAMPAGNE = [(822, 842), (830, 752), (941, 744), (941, 850)]
UPPER = dict(hands="mr_p_handsup", point="mr_p_pointing", placard="mr_p_placard", laugh="mr_p_laughhard", talk="mr_p_talking", sofa="mr_p_sofa")


def party_table(s, t, cam):
    st = plate("w_party", occluders=[PARTY_TABLE, PLACARD_ON_TABLE, CHAMPAGNE])
    acts = []
    mode = perf.pose_at("mi_t", t, "hands")
    mx, my, msc = s.get("micah_pose", (400, 1030, 5.0))
    acts.append(sprite(UPPER[mode], mx, my, msc, t, anchor="base", amp=11, sway=3.5, squash=0.025, z=5))
    for key_, fn, mode0, (x, y, sc, fl) in s.get("friends", []):
        vis, sz, al = pop(t, perf.appear_time(key_, s["t0"] - 5))
        if not vis: continue
        acts.append(fn(t, x, y, sc, perf.pose_at(key_, t, mode0), flip=fl, size=sz, alpha=al, z=y - 50))
    fr = st.render(cam, acts, dof=s.get("dof", 0.0))
    return party_fx(fr, s, t)


# ---------------------------------------------------------------- Micah's face, close up (the match cut into the studio)
def party_cu(s, t, cam):
    st = plate(s.get("plate", "w_party"), occluders=s.get("occ", []))
    name, flip = pose_of("mi_cu", t, "mr_e_embarrassed")
    if (name + "_x") in E.META: name += "_x"
    x, y, sc = s["bust"]
    a = Actor(name, x, y, sc, flip=flip, anchor="base", z=5)
    st_, b = face_state("mi_cu", t, flip=flip, talks=False)
    acts = [(a, st_, body_for(a, b), 1.0)]
    for key_, fn, mode0, (fx, fy, fsc, fl) in s.get("behind", []):
        acts.append(fn(t, fx, fy, fsc, perf.pose_at(key_, t, mode0), flip=fl, z=fy - 80))
    fr = st.render(cam, acts, dof=s.get("dof", 0.0), occ_dof=s.get("dof", 0.0))
    return party_fx(fr, s, t)


EXTRA = {"party_wide": party_wide, "party_table": party_table, "party_cu": party_cu}

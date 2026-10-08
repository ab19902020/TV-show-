"""The actors of The White Pelé: studio.film.stage's draw_actor with what this film needs on top (installed over the
engine's own by `install()`, which direction.py calls; the engine itself is unchanged).

An actor dict (stage.py's keys: who, draw, feet, h, mirror, blur, dance, look_at, mic...) may also have:

  keys     [(t, "<id>:<drawing>"), ...]   which drawing from when: pose changes on a cut-free beat, walk cycles
  path     [(t, (x, y)), ...]             where the feet are (plate px; layout px for screen actors), eased between
  hpath    [(t, h), ...]                  the height over time (walking into depth)
  ref      "<id>:<drawing>"               the drawing that sets the size: every key is drawn at the same scale
                                          (a raised arm never shrinks the body), placed by its own feet
  over     ["<id>:<drawing>", ...]        drawn with the same transform after the actor (the raised microphone over
                                          the singing face: it never moves with the jaw)
  hold     [dict(prop, at, deg, size, behind, to)]  a prop in the drawing's hand (props.hold): its grip at `at`
                                          (sheet px), turned, `size` sheet px tall; behind=True draws it under
                                          the drawing (held in a fist that closes in front of it)
  tap      dict(at=(x, y), r, lift, spans=[(t0, t1)], every)  a foot tapping: the shoe at (x, y) (sheet px,
                                          radius r) lifts by `lift` sheet px on the off-beats inside the spans
  walk     dict(keys=[...], stride, period, t0)  a walk cycle: the keys in order, one per step-phase, swapped on the
                                          beat (period: beats per key); the body moves on along `path`
  fx       ["<props.py fn>", ...]          drawn on the actor's own layer (sheet-space), e.g. a sweat drop

Everything else is the engine's: the face acts (perf.py), the groove dances (perf.GROOVE), the head rides the body
rigidly."""
import importlib
import math
import types

import numpy as np

from studio.film import engine as E
from studio.film import stage as ST
from studio.film.cast import CAST, feet as feet_of
from studio.film.engine import OH, OW, RS
from studio.film.stage import apply, compose, groove_matrix, rigid_head, top_of


def _interp(keys, t):
    """eased interpolation of [(t, value)] (value a number or a tuple)"""
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t < t1:
            u = ST.sm((t - t0) / max(1e-6, t1 - t0))
            if isinstance(v0, (tuple, list)):
                return tuple(a + (b - a) * u for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * u
    return keys[-1][1]


def _linear(keys, t):
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t0 <= t < t1:
            u = (t - t0) / max(1e-6, t1 - t0)
            return tuple(a + (b - a) * u for a, b in zip(v0, v1))
    return keys[-1][1]


def resolve(a, t):
    """the actor as it is at time t: its drawing, its feet, its height"""
    b = dict(a)
    if a.get("keys"):
        k = a["keys"][0][1]
        for tk, key in a["keys"]:
            if t >= tk - 1e-6:
                k = key
        b["draw"] = k
    if a.get("walk"):
        w = a["walk"]
        S = ST.SONG()
        beats = S.beat_index(t) + S.phase(t) if w.get("beat", True) else (t - w.get("t0", 0.0)) / w["period_s"]
        n = len(w["keys"])
        i = int(math.floor(beats / w.get("period", 1.0) + w.get("phase", 0))) % n
        b["draw"] = w["keys"][i]
    if a.get("path"):
        b["feet"] = (_linear if a.get("linear", True) else _interp)(a["path"], t)
    if a.get("hpath"):
        b["h"] = _interp(a["hpath"], t)
    return b


def keys_of(a):
    """every drawing an actor can show (for the render's preparation step)"""
    ks = {a["draw"]} if a.get("draw") else set()
    ks.update(k for _, k in a.get("keys", ()))
    ks.update(a.get("walk", {}).get("keys", ()))
    ks.update(a.get("over", ()))
    if a.get("ref"):
        ks.add(a["ref"])
    return ks


def spec_of(key):
    cid, name = key.split(":")
    return CAST.spec(cid)["drawings"][name]


class _Still:
    """a drawing filmed exactly as drawn: no face patch over it (a face too small to rig, its expression fixed)"""
    def __init__(self, d):
        self._d = d

    def __getattr__(self, name):
        return getattr(self._d, name)

    def patch(self, *a, **k):
        return None


def draw_actor(shared, a, t, s, M, sc, pos):
    R = ST._R()
    a = resolve(a, t)
    key, who = a["draw"], a["who"]
    d, info = CAST.get(key)
    fx, fy = feet_of(key)
    ref = a.get("ref", key)
    rfx, rfy = feet_of(ref)
    Hd = rfy - top_of(ref)
    mirror = a.get("mirror", False)
    if a.get("eye") is not None:
        ax, ay = info["anchor"]
        k = a["ed"] * RS / info["ed"]
        sx = -k if mirror else k
        Ex, Ey = a["eye"][0] * RS, a["eye"][1] * RS
        Ms = np.array([[sx, 0.0, Ex - sx * ax], [0.0, k, Ey - k * ay]])
        Fx, Fy = apply(Ms, fx, fy)
    else:
        if a.get("screen"):
            Fx, Fy = a["feet"][0] * RS, a["feet"][1] * RS
            k = a["h"] * RS / Hd
        else:
            Fx, Fy = apply(M, *a["feet"])
            k = a["h"] * sc / Hd
        sx = -k if mirror else k
        Ms = np.array([[sx, 0.0, Fx - sx * fx], [0.0, k, Fy - k * fy]])
        rd, rinfo = CAST.get(ref)
        if ref != key and d.has_face and rd.has_face and not spec_of(key).get("plain"):
            # a waist-up or gesture drawing beside the character's full body: the same face size (eye distance)
            # and the eyes where the full body's eyes would be, so every drawing of a character is the same person
            Mr = np.array([[sx, 0.0, Fx - sx * rfx], [0.0, k, Fy - k * rfy]])
            ex, ey = apply(Mr, *rinfo["anchor"])
            k = k * rinfo["ed"] / info["ed"]
            sx = -k if mirror else k
            ax, ay = info["anchor"]
            Ms = np.array([[sx, 0.0, ex - sx * ax], [0.0, k, ey - k * ay]])
            Fx, Fy = apply(Ms, fx, fy)
            Hd = Hd * info["ed"] / rinfo["ed"]
    perf = importlib.import_module("film.perf")
    gv = getattr(perf, "GROOVE", None)
    g = gv.at(who, t) if gv is not None else dict(rot=0.0, sx=1.0, sy=1.0, jump=0.0, dx=0.0, nod=0.0, tilt=0.0)
    if hasattr(gv, "head"):
        g["nod"], g["tilt"], g["turn"] = gv.head(who, t)
    amt = a.get("dance", 1.0)
    if amt != 1.0:
        g = dict(rot=g["rot"] * amt, sx=1 + (g["sx"] - 1) * amt, sy=1 + (g["sy"] - 1) * amt, jump=g["jump"] * amt,
                 dx=g["dx"] * amt, nod=g["nod"] * amt, tilt=g["tilt"] * amt, turn=g.get("turn", 0.0) * amt)
    if a.get("walk") or a.get("path"):                 # walking: the steps carry the body, no dancing on top
        g = dict(g, sy=1.0, sx=1.0, jump=0.0, dx=0.0, rot=g["rot"] * 0.3)
    if a.get("bob") is not None:                       # walking seen from the waist up: a rise on every step
        S = ST.SONG()                                  # (a step on every beat) and the shoulders rocking
        u = S.beat_index(t) + S.phase(t) + a["bob"].get("phase", 0.0)
        g = dict(g, sy=1.0, sx=1.0, dx=0.0, rot=1.6 * math.sin(math.pi * u), jump=0.010 * abs(math.sin(math.pi * u)),
                 tilt=g.get("tilt", 0.0) + 1.2 * math.sin(math.pi * u))
    if (not a.get("screen") and a.get("eye") is None
            and a.get("shadow", s.get("shadows", str(s.get("plate", "")).startswith("B")))):
        contact_shadow(shared, a, g, M, sc)
    spec = CAST.spec(key.split(":")[0])["drawings"][key.split(":")[1]]
    st = R.PERF.state(who, t, R.world_resolver(s, who, pos), s["t"]) if d.has_face and not a.get("still_face") else {}
    native = spec.get("native_inst")
    if native == "drumming":
        g = dict(g, rot=0.0, sx=1.0, sy=1.0, jump=0.0, dx=0.0, nod=0.0)
    if st:
        st = dict(st)
        st["nod"] = 0.0
        st["tilt"] = st["tilt"] + g["tilt"]
        st["turn"] = st["turn"] + g.get("turn", 0.0)
        if a.get("look_at") is not None:
            ex, ey = a["eye"] if a.get("eye") is not None else (a["feet"][0], a["feet"][1] - a["h"])
            tx, ty = a["look_at"]
            wob = 0.04 * math.sin(t * 0.83 + (hash(who) % 17))
            st["lookx"] = float(np.clip((tx - ex) / 2400.0, -0.4, 0.4)) + wob
            st["looky"] = float(np.clip((ty - ey) / 2600.0, -0.24, 0.2))
        elif a.get("look_cam"):
            st["lookx"] = 0.0
            st["looky"] = -0.02
        ST.life(st, who, t, bool(a.get("look_cam")), getattr(perf, "LIFE", {}).get(who))
        ST.glance(st, who, t, pos, getattr(perf, "GLANCE", {}).get(who, ()))
        if a.get("face"):                               # the shot's own face for this actor: (brow, smile)
            st["brow"], st["smile"] = a["face"]
        fst = R.face_state(st, info, mirror)
        if not a.get("look_cam") and "look0" not in spec:
            fst["lookx"] = float(np.clip(fst["lookx"] + ST.turn_look(key), -1.2, 1.2))
    else:
        fst = {}
    B = groove_matrix(g, (fx, fy), Hd)
    Ms2 = compose(Ms, B)
    head = rigid_head(d, g, B, Ms, Hd)
    clip = None
    if a.get("clip") is not None:
        cy_scr = a["clip"] * RS if a.get("screen") else apply(M, 0.0, a["clip"])[1]
        clip = (cy_scr - Ms2[1, 2]) / Ms2[1, 1]
    H_screen = Hd * k
    inst = a.get("inst")
    playing = a.get("playing", 1.0)
    plays = getattr(perf, "PLAYS", {}).get(who)
    if plays is not None:
        playing = max([ST.ramp(t, t0, t1, 0.2, 0.25) for t0, t1 in plays] or [0.0])
    own = bool(inst or a.get("blur") or a.get("cloud") or a.get("tap") or a.get("hold") or a.get("over")
               or a.get("fx") or a.get("alpha", 1.0) < 1.0 or a.get("tint"))
    lay = np.zeros((OH, OW, 4), np.float32) if own else shared
    X = importlib.import_module("film.props")
    for item in a.get("hold", ()):                     # props held behind the hand (a broom handle, a trophy's
        if item.get("behind"):                          # foot in a raised fist, a scarf over the head)
            X.hold(lay, item, Ms2, t, a)
    E.place(lay, _Still(d) if a.get("still_face") else d, fst, Ms2, clip=clip, head=head)
    if native:
        from studio.film.concert import play_native
        D = R.D
        rel = getattr(D, "KIT_REL", None)
        if native == "drumming" and rel and not a.get("screen"):
            # the drums he plays, where they are for this placement (relative to his feet and height)
            fx_, fy_ = a["feet"]
            D = types.SimpleNamespace(DRUMS=dict(D.DRUMS, drums={kk: (fx_ + rx * a["h"], fy_ + ry * a["h"])
                                                                  for kk, (rx, ry) in rel.items()}))
        lay = play_native(lay, native, Ms2, key, t, H_screen, playing, M, D)
        if a.get("kit"):                                # the pub's kit, brought along to this stage
            X.drum_kit(lay, a, M, sc)
    elif inst in ("guitar", "bass"):
        lay = ST.play_strings(lay, inst, Ms2, key, t, mirror, H_screen, playing)
    for ok in a.get("over", ()):
        od, _ = CAST.get(ok)
        E.place(lay, od, {}, Ms2, clip=clip)
    for item in a.get("hold", ()):
        if not item.get("behind"):
            X.hold(lay, item, Ms2, t, a)
    if a.get("tap"):
        tap(lay, a["tap"], Ms2, t)
    for fn in a.get("fx", ()):
        getattr(X, fn)(lay, a, t, Ms2, k)
    if a.get("cloud"):
        ST.rain_cloud(lay, Ms2, key, t)
    if a.get("tint"):                                  # (r, g, b, amount): a silhouette, a memory's warm wash
        r_, g_, b_, amt_ = a["tint"]
        lay[..., :3] = lay[..., :3] * (1 - amt_) + lay[..., 3:4] * np.float32([r_, g_, b_]) * amt_
    if a.get("alpha", 1.0) < 1.0:
        lay *= a["alpha"]
    if own:
        E.over_sparse(shared, lay, a.get("blur", 0.0) * RS)
    if a.get("mic"):
        ST.mic_stand(shared, Ms2, key, (Fx, Fy), a["mic"])


def contact_shadow(shared, a, g, M, sc):
    """a soft dark contact shadow on the ground under the feet: smaller and fainter the higher they are off it
    (a jump on the beat, the overhead kick: a["ground"] is the floor's y when the feet leave it)"""
    import cv2
    x, y = a["feet"]
    h = a["h"]
    ground = a.get("ground", y)
    lift = max(0.0, ground - y) + g.get("jump", 0.0) * h
    f = float(np.clip(1.0 - lift / (0.9 * h), 0.25, 1.0))
    X, Y = apply(M, x, ground)
    rx, ry = 0.17 * h * sc * (0.6 + 0.4 * f), 0.028 * h * sc * (0.6 + 0.4 * f)
    if rx < 2 or not (-rx < X < OW + rx and -ry < Y < OH + ry):
        return
    m = int(rx * 1.6 + 6)
    x0, y0 = max(0, int(X - m)), max(0, int(Y - m))
    x1, y1 = min(OW, int(X + m)), min(OH, int(Y + m))
    if x1 <= x0 or y1 <= y0:
        return
    sub = np.zeros((y1 - y0, x1 - x0), np.float32)
    cv2.ellipse(sub, (int(X - x0), int(Y - y0)), (int(rx), max(1, int(ry))), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
    sub = cv2.GaussianBlur(sub, (0, 0), max(1.0, 0.35 * ry + 1)) * 0.42 * f
    roi = shared[y0:y1, x0:x1]
    roi[..., :3] *= (1 - sub[..., None])
    roi[..., 3] = roi[..., 3] + sub * (1 - roi[..., 3])


def tap(lay, spec, Ms2, t):
    """a foot tapping on the off-beats: the shoe lifts about its heel and comes down on the beat"""
    S = ST.SONG()
    on = max([ST.ramp(t, a, b, 0.05, 0.05) for a, b in spec["spans"]] or [0.0])
    if on <= 0:
        return
    p = S.phase(t)
    every = spec.get("every", 1)
    bi = S.beat_index(t)
    u = ((bi % every) + p) / every
    lift = spec["lift"] * on * max(0.0, math.sin(math.pi * u)) ** 1.5
    x, y = spec["at"]
    hx, hy = apply(Ms2, x, y)
    r = spec["r"] * abs(Ms2[0, 0])
    dy = -lift * abs(Ms2[1, 1])
    m = int(r * 2.2 + abs(dy) + 4)
    x0, y0, x1, y1 = int(hx - m), int(hy - m), int(hx + m), int(hy + m)
    Y, Xg = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    toe = spec.get("toe", 1.0)                          # +1: the toe to the screen's right lifts most
    w = np.exp(-(((Xg - hx) / (1.3 * r)) ** 2 + ((Y - hy) / (0.9 * r)) ** 2))
    w *= np.clip(0.5 + 0.5 * toe * (Xg - hx) / r, 0.15, 1.0)    # the heel stays down, the toe comes up
    w = w.astype(np.float32)
    ST.warp_region(lay, x0, y0, x1, y1, np.zeros_like(w), (w * dy).astype(np.float32))


def install():
    ST.draw_actor = draw_actor


def post(img, s, t):
    """what a shot asks for on top of the engine's stage render: motion blur on a fast pan, the light at the end of
    the tunnel growing, a scarf wiping across the lens out of one shot and into the next, the light hit on each of
    the closing stabs, and the fade at the very end"""
    import cv2
    X = importlib.import_module("film.props")
    if s.get("motion"):
        n = max(3, int(s["motion"] * RS)) | 1
        img = cv2.filter2D(img, -1, np.ones((1, n), np.float32) / n, borderType=cv2.BORDER_REFLECT)
    if s.get("light_end"):
        le = s["light_end"]
        u = ST.sm((t - s["t"]) / max(1e-3, s["end"] - s["t"]))
        img = img + (1 - img) * le["amount"] * u * np.float32(le["color"])
    for kind in ("wipe_in", "wipe_out"):
        if s.get(kind) is not None:
            img = X.scarf_wipe(img, t, s[kind], kind == "wipe_in")
    D = ST._R().D
    for ts in getattr(D, "STABS", ()):
        if 0 <= t - ts < 0.25 and s["kind"] == "stage":
            img = img + (1 - img) * 0.22 * math.exp(-(t - ts) / 0.07)
    if s.get("fade_out"):
        a, bb = s["fade_out"]
        img = img * (1 - ST.sm((t - a) / max(1e-3, bb - a)))
    img = importlib.import_module("film.camera").apply(img, s, t)
    return img


def install_render():
    """the stage render with post() after it"""
    if getattr(ST.render, "_white_pele", False):
        return
    base = ST.render

    def render(s, t):
        return post(base(s, t), s, t)
    render._white_pele = True
    ST.render = render

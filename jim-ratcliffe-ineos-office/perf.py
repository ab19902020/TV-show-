"""Performance: blocking + a cue sheet keyed to the spoken words -> per-frame animation state.

Blocking (where he is and which rig draws him) follows the director's notes:
  desk, facing camera -> "Glazer ball licker", dead-pan pause, walks across the office -> stops, chops on
  "going backwards" -> paces slowly, counting on his fingers -> walks to the windows, turns side-on and presents
  the Monaco view (held) -> turns back: jacket, belt tug, point + chop -> glance over the shoulder, shrug ->
  finger up on "SENSIBLE" -> walks back along the desk counting each word -> sits in the executive chair, crosses
  a leg, straight-faced -> stands for three hand beats -> paces -> four points at the camera -> checks his watch,
  looks out at the yachts, picks up his phone and walks out -> the empty office.
Acting is restrained: stern / raised-brow heads, small beats, understated head motion, natural blinks."""
import json, math, numpy as np

FPS = 30
TL = json.load(open("timeline.json"))
N = TL["n"]; WORDS = TL["words"]; TOTAL = TL["total"]

def W(word, nth=1, edge="s"):
    k = 0
    for w in WORDS:
        if w["w"] == word:
            k += 1
            if k == nth: return w[edge]
    raise KeyError((word, nth))

RIG_H = 1516.0                    # rig px from the top of the hair to the soles
# places: (world x, floor y, world px per rig px).  Depth: further back = higher floor line, smaller.
DESK = (1110.0, 870.0, 0.404)     # behind the desk, facing camera
ACROSS = (840.0, 870.0, 0.404)
PACE_B = (1000.0, 870.0, 0.404)   # pacing stops while he counts
PACE_END = (900.0, 870.0, 0.404)
WINDOW = (1310.0, 705.0, 0.307)   # on the marble in front of the windows, fully visible
MID = (900.0, 848.0, 0.392)       # half-way back from the window, counting
CHAIR = (455.0, 918.0, 0.480)     # at the executive chair
FRONT_DESK = (760.0, 885.0, 0.440)
EXIT = (1840.0, 880.0, 0.440)
SEAT_DROP = 160.0                 # world px he sinks when sitting
STRIDE_RIG = 290.0                # one step of the WALK drawings, in rig px (4 drawings per step)

def head_top(place, seated=0.0):
    x, f, k = place
    return f - k * RIG_H + seated

# ------------------------------------------------------------------ blocking
BLOCK = []
def front(t0, t1, a): BLOCK.append(dict(t0=t0, t1=t1, kind="front", a=a, b=a))
def walk(t0, t1, d, a, b): BLOCK.append(dict(t0=t0, t1=t1, kind="walk", d=d, a=a, b=b))
def view(t0, t1, name, a): BLOCK.append(dict(t0=t0, t1=t1, kind="view", name=name, a=a, b=a))
def profile(t0, t1, a): BLOCK.append(dict(t0=t0, t1=t1, kind="profile", a=a, b=a))
def turn(t0, names, a, fr=2):
    for k, n in enumerate(names): view(t0 + k * fr / FPS, t0 + (k + 1) * fr / FPS, n, a)
    return t0 + len(names) * fr / FPS

T_WALK1 = W("licker", 1, "e") + 0.65          # the dead-pan pause, then he strolls off
T_STOP1 = W("britain") - 0.22
T_PACE1 = W("we've") - 0.12                   # paces while listing: walks, stops to count
T_PACE1_STOP = W("benefits") - 0.12
T_PACE1B = W("immigration", 1, "e") + 0.08
T_PACE1B_STOP = W("spending") - 0.12
T_WIN = W("that", 1, "e") + 0.35              # after "...a country like that."
T_WIN_ARRIVE = W("i") - 0.22
T_BACK_TO_CAM = W("means", 1, "e") + 0.35
T_GLANCE = W("less", 1, "e") + 0.35           # after "...expect less."
T_LEAVE_WIN = W("decision", 1, "e") + 0.12
T_MID = W("sacrifice") - 0.14
T_TO_CHAIR = W("efficiency", 1, "e") + 0.06
T_SIT = W("sacrifices") - 0.30
T_STAND = W("absolutely", 1, "e") + 0.02
T_PACE2 = W("industry", 1, "e") + 0.35
T_PACE2_END = W("paperwork") - 0.14
T_LOOK_OUT = W("waiting", 1, "e") + 0.12
T_EXIT = T_LOOK_OUT + 2.25
T_GONE = T_EXIT + 4.2

def moveto(t0, t1, d, a, b):
    """turn to 3/4 in the direction of travel, walk, turn back to camera (turn frames included in [t0, t1])"""
    v = "3/4 LEFT" if d == "L" else "3/4 RIGHT"
    view(t0, t0 + 3 / FPS, v, a)
    walk(t0 + 3 / FPS, t1 - 3 / FPS, d, a, b)
    view(t1 - 3 / FPS, t1, v, b)

front(0.0, T_WALK1, DESK)
moveto(T_WALK1, T_STOP1, "L", DESK, ACROSS)
front(T_STOP1, T_PACE1, ACROSS)
moveto(T_PACE1, T_PACE1_STOP, "R", ACROSS, PACE_B)                             # "We've got too many people on..."
front(T_PACE1_STOP, T_PACE1B, PACE_B)                                          # counts: benefits, immigration
moveto(T_PACE1B, T_PACE1B_STOP, "L", PACE_B, PACE_END)                         # "...too much government..."
front(T_PACE1B_STOP, T_WIN, PACE_END)                                          # ...spending. You simply cannot...
t = T_WIN + 3 / FPS
view(T_WIN, t, "3/4 RIGHT", PACE_END)
walk(t, T_WIN_ARRIVE, "R", PACE_END, WINDOW)                                   # to the windows
t = turn(T_WIN_ARRIVE, ["3/4 RIGHT", "FRONT", "3/4 LEFT"], WINDOW)
profile(t, T_BACK_TO_CAM, WINDOW)                                              # presents Monaco
t = turn(T_BACK_TO_CAM, ["3/4 LEFT"], WINDOW, fr=3)
front(t, T_GLANCE, WINDOW)
t = turn(T_GLANCE, ["3/4 LEFT"], WINDOW, fr=22)                                 # glances back at Monaco
front(t, T_LEAVE_WIN, WINDOW)
moveto(T_LEAVE_WIN, T_MID, "L", WINDOW, MID)                                   # "What Britain needs is..."
front(T_MID, T_TO_CHAIR, MID)                                                  # counts each item
moveto(T_TO_CHAIR, T_SIT, "L", MID, CHAIR)                                     # "Preferably..."
front(T_SIT, T_PACE2, CHAIR)                                                   # sits / stands ('seat')
moveto(T_PACE2, T_PACE2_END, "R", CHAIR, FRONT_DESK)                           # "Now we seem to build..."
front(T_PACE2_END, T_LOOK_OUT, FRONT_DESK)
t = turn(T_LOOK_OUT, ["3/4 LEFT"], FRONT_DESK, fr=3)
view(t, t + 0.95, "BACK", FRONT_DESK)                                          # looks out at the yachts
t = turn(t + 0.95, ["3/4 LEFT"], FRONT_DESK, fr=3)
front(t, T_EXIT, FRONT_DESK)                                                   # picks up his phone
t = T_EXIT + 3 / FPS
view(T_EXIT, t, "3/4 RIGHT", FRONT_DESK)
walk(t, T_GONE, "R", FRONT_DESK, EXIT)
BLOCK.append(dict(t0=T_GONE, t1=999, kind="off", a=EXIT, b=EXIT))

def smooth(u): u = min(max(u, 0.0), 1.0); return u * u * (3 - 2 * u)

def block_at(t):
    for b in BLOCK:
        if b["t0"] <= t < b["t1"]: return b
    return BLOCK[-1]

def place_at(t):
    b = block_at(t)
    u = (t - b["t0"]) / max(b["t1"] - b["t0"], 1e-6)
    u = 0.15 * smooth(u) + 0.85 * u                                       # eases into / out of the walk a little
    return tuple(b["a"][j] + (b["b"][j] - b["a"][j]) * u for j in range(3)), b

# ------------------------------------------------------------------ cue sheet
def cues():
    P, H, B, CH, JAB = [], [], [], [], []
    def pose(t, n): P.append((t, n))
    def head(t, n): H.append((t, n))
    def beat(t, s=1.0): B.append((t, s))
    def chop(t, s=1.0): CH.append((t, s)); B.append((t, 0.6 * s))
    def jab(t, s=1.0): JAB.append((t, s)); B.append((t, 0.5 * s))
    # --- at the desk
    pose(0.0, "ARMS DOWN"); head(0.0, "NEUTRAL")
    pose(0.55, "ADJUST TIE")                                               # jacket and tie, calmly
    pose(W("co") - 0.2, "HAND ON HIP"); head(W("co") - 0.2, "SMILE")         # proud posture
    pose(W("and") - 0.15, "ARMS DOWN"); head(W("and") - 0.15, "NEUTRAL")     # completely serious
    # --- walks across; "Britain is going backwards" (chop)
    pose(T_STOP1 + 0.05, "ARMS DOWN"); head(T_STOP1 + 0.05, "DISGUSTED")
    pose(W("going") - 0.12, "PALM OUT STOP"); chop(W("backwards") + 0.04, 1.0)
    pose(W("it") - 0.1, "ARMS CROSSED"); head(W("it") - 0.1, "RAISED BROW"); beat(W("is", 2), 0.4)
    pose(W("somebody") - 0.12, "TALK RIGHT"); head(W("somebody") - 0.12, "NEUTRAL"); beat(W("say"), 0.5)
    # --- paces, counting: thumb (1), thumb + index (2), three fingers (3)
    pose(W("too") - 0.15, "THUMBS UP"); head(W("too") - 0.15, "DISGUSTED"); beat(W("benefits"), 0.5)
    pose(W("too", 2) - 0.15, "FINGER UP"); beat(W("immigration"), 0.5)
    pose(T_PACE1B_STOP, "OK SIGN"); beat(W("spending"), 0.6)
    pose(W("you") - 0.15, "CALM DOWN"); head(W("you") - 0.15, "NEUTRAL"); beat(W("cannot"), 0.8)
    pose(W("that", 1, "e") + 0.15, "ARMS DOWN")
    # --- the window (profile rig handles the arm); turns back
    head(T_BACK_TO_CAM, "NEUTRAL"); pose(T_BACK_TO_CAM, "ARMS DOWN")
    pose(W("ordinary") - 0.2, "ADJUST TIE")                                 # straightens his own suit
    pose(W("tighten") - 0.2, "HAND ON HIP"); head(W("tighten") - 0.2, "RAISED BROW")   # tugs his belt on "belts"
    pose(W("work") - 0.2, "REACH FORWARD"); head(W("work") - 0.2, "NEUTRAL"); jab(W("harder"), 1.0)
    pose(W("expect") - 0.12, "PALM OUT STOP"); chop(W("less") + 0.03, 1.0)
    pose(W("less", 1, "e") + 0.2, "ARMS DOWN")
    pose(W("obviously") - 0.12, "PALM UP"); head(W("obviously") - 0.12, "RAISED BROW")   # small shrug
    pose(W("i", 2) - 0.1, "ARMS DOWN"); head(W("moved") - 0.1, "NEUTRAL")
    pose(W("but") - 0.12, "ARMS CROSSED"); head(W("but") - 0.12, "RAISED BROW")
    pose(W("sensible") - 0.2, "FINGER UP"); head(W("that", 2) - 0.1, "SMILE"); beat(W("sensible"), 0.6)
    head(W("financial") - 0.1, "RAISED BROW"); beat(W("decision"), 0.4)
    # --- walks back along the desk, one gesture per item
    pose(T_LEAVE_WIN + 0.1, "ARMS DOWN"); head(T_LEAVE_WIN + 0.1, "NEUTRAL")
    pose(T_MID, "FINGER UP"); beat(W("sacrifice"), 0.5)
    pose(W("difficult") - 0.12, "EXPLAINING 1"); beat(W("decisions"), 0.5)
    pose(W("cuts") - 0.3, "PALM OUT STOP"); chop(W("cuts") + 0.03, 1.1)
    pose(W("efficiency") - 0.15, "OK SIGN"); beat(W("efficiency"), 0.5)
    # --- sits, crosses a leg: straight-faced
    pose(T_TO_CHAIR, "ARMS DOWN"); pose(T_SIT + 0.1, "HAND ON HIP"); head(T_SIT, "NEUTRAL")
    head(W("absolutely") - 0.1, "RAISED BROW"); beat(W("absolutely"), 0.5)
    # --- stands: three strong beats
    pose(T_STAND + 0.2, "PALM OUT STOP"); head(T_STAND + 0.2, "NEUTRAL")
    chop(W("factories") + 0.04, 1.1); chop(W("ships") + 0.04, 1.1)
    pose(W("industry") - 0.12, "CALM DOWN"); beat(W("industry") + 0.05, 1.1)
    # --- paces again, a little more animated
    head(T_PACE2, "DISGUSTED")
    pose(T_PACE2_END, "HOLDING PAPER"); beat(W("paperwork"), 0.7)
    pose(W("benefit") - 0.12, "THUMBS DOWN"); beat(W("claims"), 0.7)
    pose(W("and", 4) - 0.12, "PRESENT"); head(W("and", 4) - 0.12, "RAISED BROW")
    pose(W("what's") - 0.15, "WHAT"); beat(W("solution"), 0.4)
    pose(W("solution", 1, "e") + 0.2, "HAND ON CHIN"); head(W("solution", 1, "e") + 0.2, "RAISED BROW")
    # --- four points at the camera
    pose(W("simple") - 0.22, "REACH FORWARD"); head(W("simple") - 0.22, "NEUTRAL")
    jab(W("simple") + 0.02); jab(W("work", 2) + 0.02); jab(W("spend") + 0.02); jab(W("stop") + 0.02, 1.15)
    head(W("stop") - 0.1, "DISGUSTED")
    pose(W("complaining", 1, "e") + 0.35, "ARMS DOWN"); head(W("complaining", 1, "e") + 0.35, "NEUTRAL")
    # --- the watch; "the yacht's waiting"; phone
    pose(W("anyway") - 0.3, "WATCH")
    pose(W("i'd") - 0.15, "ARMS DOWN")
    head(W("the", 2) - 0.1, "SMILE")
    head(T_LOOK_OUT, "NEUTRAL"); pose(T_LOOK_OUT, "ARMS DOWN")
    pose(T_LOOK_OUT + 1.45, "PHONE HOLD")
    return sorted(P), sorted(H), sorted(B), sorted(CH), sorted(JAB)

POSES, HEADS, BEATS, CHOPS, JABS = cues()
WATCH_LOOK = (W("anyway") - 0.2, W("i'd") - 0.2)       # looks down at the watch
SHRUG = W("obviously") + 0.05
TUG = W("belts") + 0.05
LEG_CROSS = W("sacrifices") - 0.25
PICKUP = T_LOOK_OUT + 1.2                              # reaches down to the desk for the phone

def at(lst, t, default):
    cur = default
    for ct, v in lst:
        if ct <= t: cur = v
        else: break
    return cur

# ------------------------------------------------------------------ lip sync: closed mouth inside a phrase
PHRASES = []
for w in WORDS:
    if PHRASES and w["s"] - PHRASES[-1][1] < 0.32: PHRASES[-1][1] = w["e"]
    else: PHRASES.append([w["s"], w["e"]])

def viseme(i):
    t = i / FPS
    v = TL["track"][i]
    if v != "REST": return v
    return "REST" if any(a - 0.05 <= t <= b + 0.08 for a, b in PHRASES) else None

# ------------------------------------------------------------------ curves
def lp(x, sec):
    a = 1 - math.exp(-1 / (FPS * sec)); y = np.zeros_like(x); s = x[0]
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y

def spring(target, freq=2.2, zeta=0.6, sub=6):
    w = 2 * math.pi * freq; x, v = float(target[0]), 0.0; out = np.zeros(len(target)); dt = 1 / FPS / sub
    for i, tg in enumerate(target):
        for _ in range(sub):
            v += (w * w * (tg - x) - 2 * zeta * w * v) * dt; x += v * dt
        out[i] = x
    return out

def beat_curve(t, tb, tau=0.08):
    u = t - (tb - tau)
    if u < -0.16: return 0.0
    if u < 0: return -0.3 * math.sin(math.pi * (u + 0.16) / 0.16)
    return (u / tau) * math.exp(1 - u / tau)

def bump(t, t0, dur, rise=0.3):
    """0 -> 1 -> 0 over dur, with eased rise and fall"""
    u = (t - t0) / dur
    if u <= 0 or u >= 1: return 0.0
    return smooth(u / rise) if u < rise else smooth((1 - u) / (1 - rise))

def chop_dy(t):
    """moving hand: small lift, fast strike down (rig px), settles part-way back"""
    d = 0.0
    for tc, s in CHOPS:
        u = t - tc
        if -0.22 < u < 0: d += -14 * s * math.sin(math.pi * (u + 0.22) / 0.22 * 0.5)
        elif 0 <= u < 0.9: d += s * (52 * math.exp(-u / 0.10) * (1 if u > 0.035 else u / 0.035) + 10 * (1 - u / 0.9))
    return d

def jab_s(t):
    d = 0.0
    for tj, s in JABS:
        u = t - tj
        if -0.12 < u < 0: d += -0.04 * s * (u + 0.12) / 0.12
        elif 0 <= u < 0.6: d += 0.17 * s * (min(u / 0.05, 1.0)) * math.exp(-max(u - 0.05, 0) / 0.16)
    return d

def seat_at(t):
    """0 standing .. 1 seated"""
    if t < T_SIT or t > T_STAND + 0.6: return 0.0
    if t < T_SIT + 0.55: return smooth((t - T_SIT) / 0.55)
    if t > T_STAND: return 1 - smooth((t - T_STAND) / 0.55)
    return 1.0

def channels(audio_env):
    t = np.arange(N) / FPS
    dip = np.zeros(N)
    for tb, s in BEATS:
        m = (t > tb - 0.3) & (t < tb + 0.7)
        dip[m] += np.array([beat_curve(x, tb) for x in t[m]]) * s
    pop = np.zeros(N)
    for tp, _ in POSES:
        m = (t >= tp) & (t < tp + 0.35)
        u = t[m] - tp
        pop[m] += -np.exp(-u / 0.07) * np.cos(u * 30) * 0.5
    LEAN = {"PALM UP": -1.0, "PRESENT": -0.8, "WHAT": -1.4, "HAND ON HIP": -0.8, "ARMS CROSSED": -1.0,
            "REACH FORWARD": 1.8, "PALM OUT STOP": 1.2, "CALM DOWN": 0.8, "THUMBS DOWN": 0.6, "FINGER UP": 0.4}
    lean_t = np.array([LEAN.get(at(POSES, x, "ARMS DOWN"), 0.0) for x in t])
    lean_t += np.array([-2.4 * seat_at(x) for x in t])                # leans back in the chair
    lean = spring(lean_t, 1.4, 0.75)
    e = np.clip((20 * np.log10(audio_env + 1e-10) + 45) / 37, 0, 1)
    nod = np.clip(lp(e, 0.09) - lp(e, 0.55), 0, None); nod = lp(nod, 0.06); nod /= max(nod.max(), 1e-6)
    return dict(dip=dip, pop=pop, lean=lean, nod=nod)

SHAKES = [W("cannot")]
TILTS = [(W("obviously") - 0.1, 1.4, 1), (W("sensible") - 0.2, 2.0, -1), (W("solution") - 0.6, 1.6, 1)]

def head_motion(i, ch):
    """understated: head rotation (deg, about the base of the neck) and vertical offset (rig px)"""
    t = i / FPS
    th = 0.7 * math.sin(2 * math.pi * t / 5.1) + 0.3 * math.sin(2 * math.pi * t / 2.3 + 1.0)
    dy = 2.5 * math.sin(2 * math.pi * t / 4.0)
    th += 0.9 * ch["nod"][i] * (1 if int(t / 2.7) % 2 else -1)
    dy += 9 * ch["nod"][i] + 7 * ch["dip"][i]
    th += 1.0 * ch["dip"][i] * (1 if int(t / 3.3) % 2 else -1)
    for s in SHAKES:
        d = t - s
        if 0 <= d < 0.5: th += 1.8 * math.sin(2 * math.pi * 4.0 * d) * (1 - d / 0.5)
    for s, dur, sg in TILTS:
        d = t - s
        if 0 < d < dur: th += sg * 2.4 * math.sin(math.pi * min(d / 0.4, 1) / 2) * min(1, (dur - d) / 0.4)
    look = bump(t, WATCH_LOOK[0], WATCH_LOOK[1] - WATCH_LOOK[0], 0.2)
    dy += 16 * look; th += 3.0 * look                                    # looks down at the watch
    dy -= 7 * bump(t, W("co") - 0.2, W("united", 1, "e") - W("co") + 0.6, 0.25)   # chin up, proudly
    return th, dy, look

def body_motion(t, ch, i):
    """extra torso motion in rig px: (dy, x-scale, y-scale)"""
    dy = 7 * ch["dip"][i] + 6 * ch["pop"][i]
    dy += 14 * bump(t, TUG - 0.05, 0.4, 0.35)                            # tugs his belt
    dy -= 16 * bump(t, SHRUG, 0.55, 0.4)                                 # small shrug
    dy += 60 * bump(t, PICKUP, 0.6, 0.45)                                # reaches down for the phone
    dy -= 10 * bump(t, LEG_CROSS, 0.5, 0.4)                              # shifts in the seat to cross a leg
    proud = bump(t, W("co") - 0.2, W("united", 1, "e") - W("co") + 0.6, 0.25)
    return dy, 1.0 + 0.012 * proud, 1.0 + 0.025 * proud

def profile_arm(t):
    """window gag: arm swings up to present the view, is held, comes down"""
    up0, up1 = W("very") - 0.25, W("very") + 0.2
    dn0 = W("monaco", 1, "e") + 1.05
    if t < up0 or t > dn0 + 0.5: return 0.0
    if t < up1:
        u = (t - up0) / (up1 - up0)
        return -94 * (smooth(u) + 0.08 * math.sin(math.pi * u))
    if t < dn0: return -94 + 1.2 * math.sin(2 * math.pi * (t - up1) / 2.2)
    return -94 * (1 - smooth((t - dn0) / 0.5))

def walk_frame(t, b):
    """-> (leg drawing, bob rig px) for a walk block: the drawing follows the distance covered (4 drawings per
    step), so the feet travel with the ground instead of sliding"""
    (x, f, k), _ = place_at(t)
    dist = abs(x - b["a"][0]) + 0.6 * abs(f - b["a"][1])                  # world px covered (depth counts less)
    step = STRIDE_RIG * k
    ph = dist / (step / 4.0)
    leg = ["WALK 1", "WALK 2", "WALK 3", "WALK 4"][int(ph) % 4]
    bob = -7.0 * abs(math.sin(math.pi * (ph % 2) / 2))
    return leg, bob

if __name__ == "__main__":
    for b in BLOCK: print(f"{b['t0']:6.2f}-{b['t1']:6.2f} {b['kind']:8s} {b.get('name', b.get('d', ''))}")
    print(len(POSES), "poses", len(HEADS), "heads", len(BEATS), "beats", len(CHOPS), "chops", len(JABS), "jabs")

"""Performance: a cue sheet keyed to the spoken words -> per-frame animation state.

Replacement animation: the torso (arm pose) and the head (expression) are hard drawing swaps on the cues, and
each swap gets a small body 'pop' so it reads as a move rather than a cut.  On top of that: spring-damped
torso lean, emphasis beats (dip + nod), audio-driven head nods, head shakes, a question tilt, idle sway and
breathing.  The walk-in and the run-off use the turnaround rig with the leg-pose drawings."""
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

# ------------------------------------------------------------------ staging (world = background px)
MARK_X = 1110.0          # where he stands behind the desk to deliver the piece
ENTER_X = 1800.0         # walks in from behind the side table on the right
EXIT_X = 1900.0
WALK_START, WALK_END = 0.55, 2.95
TURN_AT = 3.25           # 3/4 view -> facing camera
RUN_TURN = W("waiting", 1, "e") + 0.95
RUN_START = RUN_TURN + 0.25
RUN_END = RUN_START + 1.15

def cues():
    P, H, B = [], [], []          # torso poses, heads, beats (t, strength)
    def pose(t, n): P.append((t, n))
    def head(t, n): H.append((t, n))
    def beat(t, s=1.0): B.append((t, s))
    # --- arrives, straightens the tie
    pose(TURN_AT, "ARMS DOWN"); head(TURN_AT, "NEUTRAL")
    pose(TURN_AT + 0.35, "ADJUST TIE"); head(TURN_AT + 0.35, "SMILE")
    # --- clip 1
    pose(W("hi") - 0.2, "WAVE"); beat(W("hi"), 0.5)
    pose(W("co") - 0.12, "THUMBS UP"); head(W("co") - 0.12, "RAISED BROW"); beat(W("manchester"), 0.6); beat(W("united"), 0.5)
    pose(W("and") - 0.1, "ADJUST TIE"); head(W("and") - 0.1, "SMILE")
    pose(W("britain") - 0.15, "THUMBS DOWN"); head(W("britain") - 0.15, "DISGUSTED"); beat(W("backwards"), 0.9)
    pose(W("it") - 0.12, "ARMS CROSSED"); head(W("it") - 0.12, "RAISED BROW"); beat(W("is", 2), 0.7)
    pose(W("and", 2) - 0.1, "REACH FORWARD"); beat(W("say"), 0.8)
    pose(W("we've") - 0.1, "EXPLAINING 1"); head(W("we've") - 0.1, "DISGUSTED"); beat(W("too"), 0.7); beat(W("benefits"), 0.8)
    pose(W("too", 2) - 0.12, "EXPLAINING 2"); beat(W("too", 2), 0.7); beat(W("immigration"), 0.8)
    pose(W("too", 3) - 0.12, "BOTH HANDS OUT"); beat(W("too", 3), 0.7)
    pose(W("spending") - 0.1, "FRUSTRATED"); beat(W("spending"), 1.0)
    pose(W("you") - 0.12, "PALM OUT STOP"); head(W("you") - 0.12, "SAD"); beat(W("cannot"), 1.0)
    pose(W("like") - 0.12, "PALM UP"); beat(W("that"), 0.5)
    pose(W("that", 1, "e") + 0.45, "ARMS DOWN"); head(W("that", 1, "e") + 0.45, "NEUTRAL")
    # --- clip 2
    pose(W("i") - 0.15, "PRESENT"); head(W("i") - 0.15, "SMILE")
    pose(W("from") - 0.15, "OPEN ARMS"); beat(W("monaco"), 0.7)
    pose(W("monaco", 1, "e") + 0.7, "ARMS DOWN")
    pose(W("britain", 2) - 0.15, "CALM DOWN"); head(W("britain", 2) - 0.15, "RAISED BROW"); beat(W("learn"), 0.6); beat(W("means"), 0.7)
    pose(W("ordinary") - 0.12, "TALK LEFT"); head(W("ordinary") - 0.12, "DISGUSTED"); beat(W("ordinary"), 0.5)
    pose(W("tighten") - 0.18, "HAND ON HIP"); beat(W("belts"), 0.8)
    pose(W("work") - 0.12, "FIST PUMP"); beat(W("work"), 0.9); beat(W("harder"), 1.0)
    pose(W("expect") - 0.12, "PALM OUT STOP"); beat(W("less"), 0.9)
    pose(W("less", 1, "e") + 0.5, "ARMS DOWN"); head(W("less", 1, "e") + 0.5, "NEUTRAL")
    pose(W("obviously") - 0.15, "PALM UP"); head(W("obviously") - 0.15, "WORRIED")
    head(W("moved") - 0.15, "SMILE")
    pose(W("moved") - 0.15, "POINT LEFT"); beat(W("monaco", 2), 0.6)
    pose(W("but") - 0.12, "PALM OUT STOP"); head(W("but") - 0.12, "RAISED BROW"); beat(W("different"), 0.7)
    pose(W("that", 2) - 0.12, "OK SIGN"); head(W("that", 2) - 0.12, "SMILE"); beat(W("sensible"), 0.6); beat(W("decision"), 0.7)
    pose(W("decision", 1, "e") + 0.4, "ARMS DOWN"); head(W("decision", 1, "e") + 0.4, "NEUTRAL")
    # --- clip 3
    pose(W("what") - 0.12, "FIST"); head(W("what") - 0.12, "DISGUSTED"); beat(W("needs", 2), 0.6); beat(W("sacrifice"), 0.9)
    pose(W("difficult") - 0.1, "EXPLAINING 1"); beat(W("decisions"), 0.7)
    pose(W("cuts") - 0.12, "FIST PUMP"); head(W("cuts") - 0.12, "ANGRY"); beat(W("cuts"), 1.2)
    pose(W("efficiency") - 0.12, "OK SIGN"); head(W("efficiency") - 0.12, "RAISED BROW"); beat(W("efficiency"), 0.6)
    pose(W("preferably") - 0.15, "PALM UP"); head(W("preferably") - 0.15, "SMILE")
    pose(W("somebody", 2) - 0.12, "POINT RIGHT"); beat(W("else"), 0.6)
    pose(W("people", 3) - 0.12, "TALK RIGHT"); head(W("people", 3) - 0.12, "NEUTRAL")
    pose(W("absolutely") - 0.12, "THUMBS UP"); head(W("absolutely") - 0.12, "RAISED BROW"); beat(W("absolutely"), 0.8)
    pose(W("factories") - 0.12, "EXPLAINING 2"); head(W("factories") - 0.12, "SAD"); beat(W("factories"), 0.6)
    pose(W("ships") - 0.1, "BOTH HANDS OUT"); beat(W("ships"), 0.6)
    pose(W("industry") - 0.12, "OPEN ARMS"); beat(W("industry"), 0.7)
    pose(W("now") - 0.12, "TALK LEFT"); head(W("now") - 0.12, "DISGUSTED")
    pose(W("paperwork") - 0.2, "HOLDING PAPER"); beat(W("paperwork"), 0.7)
    pose(W("benefit") - 0.12, "THUMBS DOWN"); beat(W("claims"), 0.9)
    pose(W("claims", 1, "e") + 0.4, "ARMS DOWN"); head(W("claims", 1, "e") + 0.4, "NEUTRAL")
    # --- clip 4
    pose(W("people", 4) - 0.12, "PRESENT"); head(W("and", 4) - 0.1, "RAISED BROW")
    pose(W("jim", 2) - 0.12, "WHAT"); head(W("jim", 2) - 0.12, "CONFUSED"); beat(W("solution"), 0.5)
    pose(W("solution", 1, "e") + 0.25, "HAND ON CHIN"); head(W("solution", 1, "e") + 0.25, "THINKING")
    pose(W("simple") - 0.15, "REACH FORWARD"); head(W("simple") - 0.15, "SMILE"); beat(W("simple"), 0.8)
    pose(W("work", 2) - 0.12, "FIST PUMP"); head(W("work", 2) - 0.12, "DISGUSTED"); beat(W("work", 2), 0.9); beat(W("harder", 2), 1.0)
    pose(W("spend") - 0.12, "PALM OUT STOP"); beat(W("spend"), 0.8); beat(W("less", 2), 0.9)
    pose(W("stop") - 0.12, "FRUSTRATED"); beat(W("stop"), 1.1); beat(W("complaining"), 0.8)
    pose(W("complaining", 1, "e") + 0.5, "ARMS DOWN"); head(W("complaining", 1, "e") + 0.5, "NEUTRAL")
    pose(W("anyway") - 0.2, "PHONE HOLD"); head(W("anyway") - 0.2, "RAISED BROW")
    pose(W("i'd") - 0.15, "PRESENT"); head(W("i'd") - 0.15, "SMILE")
    pose(W("yacht's") - 0.2, "POINT LEFT"); beat(W("yacht's"), 0.6)
    pose(W("waiting", 1, "e") + 0.25, "WAVE"); head(W("waiting", 1, "e") + 0.25, "HAPPY")
    return sorted(P), sorted(H), sorted(B)

POSES, HEADS, BEATS = cues()

def at(lst, t, default):
    cur = default
    for ct, v in lst:
        if ct <= t: cur = v
        else: break
    return cur

# ------------------------------------------------------------------ phrases: inside one, a closed mouth is the sheet's
# REST mouth; in the silences between phrases the head drawing keeps its own mouth
PHRASES = []
for w in WORDS:
    if PHRASES and w["s"] - PHRASES[-1][1] < 0.32: PHRASES[-1][1] = w["e"]
    else: PHRASES.append([w["s"], w["e"]])

def viseme(i):
    t = i / FPS
    v = TL["track"][i]
    if v != "REST": return v
    return "REST" if any(a - 0.05 <= t <= b + 0.08 for a, b in PHRASES) else None

# ------------------------------------------------------------------ solvers
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
    if u < 0: return -0.3 * math.sin(math.pi * (u + 0.16) / 0.16)        # small lift before the hit
    return (u / tau) * math.exp(1 - u / tau)

def channels(audio_env):
    t = np.arange(N) / FPS
    # beats: body dip (+down) and a head nod
    dip = np.zeros(N)
    for tb, s in BEATS:
        m = (t > tb - 0.3) & (t < tb + 0.7)
        dip[m] += np.array([beat_curve(x, tb) for x in t[m]]) * s
    # pose swaps: a quick settle 'pop' (arrives slightly high, drops into place)
    pop = np.zeros(N)
    for tp, _ in POSES:
        m = (t >= tp) & (t < tp + 0.4)
        u = t[m] - tp
        pop[m] += -np.exp(-u / 0.07) * np.cos(u * 30) * 1.0
    # lean: spring toward a per-pose lean target (open gestures lean back, chops lean in)
    LEAN = {"OPEN ARMS": -2.0, "WHAT": -2.2, "PALM UP": -1.5, "BOTH HANDS OUT": -1.2, "PRESENT": -1.0,
            "FIST PUMP": 1.8, "FRUSTRATED": 1.5, "PALM OUT STOP": 1.2, "REACH FORWARD": 2.0, "THUMBS DOWN": 0.8,
            "FIST": 1.2, "HAND ON HIP": -0.8, "ARMS CROSSED": -1.0, "POINT LEFT": 1.2, "POINT RIGHT": -1.2}
    lean_t = np.array([LEAN.get(at(POSES, x, "ARMS DOWN"), 0.0) for x in t])
    lean = spring(lean_t, 1.4, 0.75)
    # audio-driven nods on speech onsets
    e = np.clip((20 * np.log10(audio_env + 1e-10) + 45) / 37, 0, 1)
    nod = np.clip(lp(e, 0.09) - lp(e, 0.55), 0, None); nod = lp(nod, 0.06); nod /= max(nod.max(), 1e-6)
    return dict(dip=dip, pop=pop, lean=lean, nod=nod)

SHAKES = [W("backwards"), W("cannot"), W("different"), W("complaining")]
TILTS = [(W("solution") - 0.8, 2.2, 1), (W("obviously"), 1.6, -1), (W("preferably"), 2.5, 1), (W("anyway"), 1.4, -1)]

def head_motion(i, ch):
    """head rotation (deg, about the base of the neck) and vertical offset (rig px)"""
    t = i / FPS
    th = 1.0 * math.sin(2 * math.pi * t / 5.1) + 0.45 * math.sin(2 * math.pi * t / 2.3 + 1.0)
    dy = 3 * math.sin(2 * math.pi * t / 4.0)
    th += 1.4 * ch["nod"][i] * (1 if int(t / 2.7) % 2 else -1)
    dy += 14 * ch["nod"][i] + 10 * ch["dip"][i]
    th += 1.5 * ch["dip"][i] * (1 if int(t / 3.3) % 2 else -1)
    for s in SHAKES:
        d = t - s
        if 0 <= d < 0.5: th += 2.4 * math.sin(2 * math.pi * 4.2 * d) * (1 - d / 0.5)
    for s, dur, sg in TILTS:
        d = t - s
        if 0 < d < dur: th += sg * 3.2 * math.sin(math.pi * min(d / 0.4, 1) / 2) * min(1, (dur - d) / 0.4)
    return th, dy

def walk_state(t):
    """(mode, leg drawing, world x, bob rig px, lean deg) or None when he's in the front rig / off stage."""
    if t < WALK_START: return ("off",)
    if t < WALK_END:
        u = (t - WALK_START) / (WALK_END - WALK_START)
        u = u * u * (3 - 2 * u) * 0.25 + u * 0.75                    # eases in and out a little
        x = ENTER_X + (MARK_X - ENTER_X) * u
        f = int((t - WALK_START) * FPS)
        leg = ["WALK 1", "WALK 2", "WALK 3", "WALK 4"][(f // 6) % 4]
        bob = -10 * abs(math.sin(math.pi * (f % 12) / 12))             # rises on the passing positions
        return ("in", leg, x, bob, 1.5)
    if t < TURN_AT - 0.12: return ("in", "STANDING", MARK_X, 0.0, 0.0)
    if t < TURN_AT: return ("in", "TURN LEFT", MARK_X, -4.0, 0.0)
    if t < RUN_TURN: return None
    if t < RUN_START: return ("out", "TURN RIGHT", MARK_X, -4.0, 2.0)
    if t < RUN_END:
        u = (t - RUN_START) / (RUN_END - RUN_START)
        x = MARK_X + (EXIT_X - MARK_X) * (u ** 1.4)
        f = int((t - RUN_START) * FPS)
        leg = ["RUN 1", "RUN 2", "RUN 3"][(f // 3) % 3]
        bob = -16 * abs(math.sin(math.pi * (f % 9) / 9))
        return ("out", leg, x, bob, 7.0)
    return ("off",)

if __name__ == "__main__":
    print(len(POSES), "pose cues,", len(HEADS), "head cues,", len(BEATS), "beats,", len(PHRASES), "phrases")
    used = sorted(set(p for _, p in POSES)); print("torsos used:", len(used), used)
    print("heads used:", sorted(set(h for _, h in HEADS)))

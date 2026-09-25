"""Performance: turns a word-level cue sheet into per-frame animation channels.

Everything is keyed to words in the aligned transcript, so the same cue sheet style works for any clip.
Channels: head drawing, arm joint angles (spring-driven, with chop 'beats'), torso lean / forward / bounce,
head nods / shakes / tilts."""
import json, math, numpy as np

FPS = 30
TL = json.load(open("timeline.json"))
N = TL["n"]
WORDS = TL["words"]

def W(word, nth=1, edge="s"):
    """time of the nth occurrence of a word ('s' start / 'e' end)."""
    k = 0
    for w in WORDS:
        if w["w"] == word:
            k += 1
            if k == nth: return w[edge]
    raise KeyError(word)

# ------------------------------------------------------------------ arm poses (shoulder_out, elbow_in, wrist)
POSE = {
    "rest":    (0, 0, 0),
    "desk":    (6, 88, 25),       # forearm across at desk height, hand resting at the table edge
    "raise":   (10, 150, 0),      # hand up in front of the chest, ready to chop
    "high":    (14, 162, -8),
    "chest":   (0, 140, 30),      # hand on heart / badge
    "present": (25, -95, -15),    # open hand out to the side
    "shrug":   (35, -115, -20),   # palms-out 'what?'
    "up":      (60, -120, 0),     # arms thrown up
    "flick":   (30, -70, -35),    # dismissive wave out
    "dangle":  (8, 100, 45),      # limp hand (walking the dog)
}

# ------------------------------------------------------------------ the cue sheet
def cues():
    c = []   # (time, arm, pose)
    B = []   # beats: (time, arm, strength)   arm in "R","L","RL"
    T = []   # torso: (time, lean_deg, forward 0..1)
    H = []   # head drawing: (time, name)
    def arm(t, a, p):
        for x in a: c.append((t, x, p))
    # listening to the co-host, then turns to camera
    H += [(0.0, "3/4 RIGHT"), (0.95, "FRONT")]
    arm(0.0, "RL", "desk"); T += [(0.0, 3.0, 0.0), (0.9, 0.0, 0.1)]
    # Manchester United.
    H += [(W("manchester") - 0.2, "SKEPTICAL")]
    arm(W("manchester") - 0.35, "R", "present"); B += [(W("manchester"), "R", 0.5), (W("united"), "R", 0.6)]
    arm(W("united", 1, "e") + 0.35, "R", "desk")
    # It's the same rubbish every week.
    H += [(W("it's") - 0.25, "DISGUSTED")]
    T += [(W("it's") - 0.2, -1.5, 0.35)]
    arm(W("same") - 0.35, "RL", "shrug"); B += [(W("same"), "RL", 0.45), (W("rubbish"), "RL", 0.6)]
    arm(W("every") - 0.2, "R", "raise"); arm(W("every") - 0.1, "L", "desk"); B += [(W("week"), "R", 0.9)]
    arm(W("week", 1, "e") + 0.25, "R", "desk")
    # No urgency, no aggression, no standards.
    H += [(W("no") - 0.25, "ANGRY")]
    T += [(W("no") - 0.2, 1.0, 0.55), (W("no", 3), 0.0, 0.85)]
    arm(W("no") - 0.3, "R", "raise")
    B += [(W("no", 1), "R", 0.9), (W("urgency"), "R", 0.4), (W("no", 2), "R", 0.9), (W("aggression"), "R", 0.4)]
    arm(W("no", 3) - 0.3, "L", "raise")
    B += [(W("no", 3), "RL", 1.0), (W("standards"), "RL", 1.0)]
    arm(W("standards", 1, "e") + 0.2, "RL", "desk")
    # You lose the ball and stroll back like you're walking the dog.
    H += [(W("you") - 0.25, "SKEPTICAL"), (W("like") - 0.1, "3/4 LEFT"), (W("dog", 1, "e") + 0.15, "SKEPTICAL")]
    T += [(W("you") - 0.3, -3.0, 0.0)]
    arm(W("lose") - 0.2, "L", "present"); B += [(W("ball"), "L", 0.4)]
    arm(W("stroll") - 0.15, "L", "flick")
    arm(W("walking") - 0.25, "R", "dangle"); arm(W("walking") - 0.2, "L", "desk")
    arm(W("dog", 1, "e") + 0.3, "R", "desk")
    # That shirt used to mean something.
    H += [(W("that") - 0.3, "SAD")]
    T += [(W("that") - 0.3, 0.0, 0.15)]
    arm(W("that") - 0.2, "R", "chest")
    arm(W("something", 1, "e") + 0.2, "R", "desk")
    # Stop pointing fingers, stop making excuses and start playing like you actually want to.
    H += [(W("stop") - 0.2, "ANGRY")]
    T += [(W("stop") - 0.2, 1.5, 0.7)]
    arm(W("stop") - 0.3, "R", "raise"); B += [(W("stop"), "R", 1.0), (W("fingers"), "R", 0.6)]
    arm(W("stop", 2) - 0.3, "L", "raise"); B += [(W("stop", 2), "RL", 1.0), (W("excuses"), "RL", 0.8)]
    arm(W("start") - 0.25, "RL", "high"); B += [(W("start"), "RL", 0.8), (W("actually"), "RL", 0.7), (W("want"), "RL", 1.0)]
    arm(W("to", 2, "e") + 0.2, "RL", "desk")
    # And don't give me this nonsense about confidence.
    H += [(W("and", 3) - 0.2, "DISGUSTED")]
    T += [(W("and", 3) - 0.2, -2.0, 0.2)]
    arm(W("don't") - 0.1, "R", "raise"); arm(W("nonsense") - 0.08, "R", "flick")
    arm(W("confidence") - 0.1, "L", "present"); B += [(W("confidence"), "L", 0.4)]
    arm(W("confidence", 1, "e") + 0.15, "RL", "desk")
    # You're playing for Manchester United.
    H += [(W("you're", 2) - 0.2, "ANGRY")]
    T += [(W("you're", 2) - 0.2, 1.0, 0.8)]
    arm(W("you're", 2) - 0.3, "R", "raise")
    B += [(W("playing", 2), "R", 0.6), (W("manchester", 2), "R", 1.0), (W("united", 2), "R", 1.0)]
    # Run, tackle, compete.
    H += [(W("run") - 0.2, "SHOUTING")]
    arm(W("run") - 0.3, "R", "high"); B += [(W("run"), "R", 1.2)]
    arm(W("tackle") - 0.3, "L", "high"); B += [(W("tackle"), "L", 1.2)]
    B += [(W("compete"), "RL", 1.3)]
    T += [(W("run") - 0.1, 0.0, 1.0)]
    arm(W("compete", 1, "e") + 0.15, "RL", "desk")
    # Is that too much to ask?
    H += [(W("is") - 0.2, "CONFUSED")]
    T += [(W("is") - 0.2, -2.5, 0.1)]
    arm(W("is") - 0.1, "RL", "shrug"); B += [(W("ask"), "RL", -0.5)]
    arm(W("ask", 1, "e") + 0.9, "RL", "desk")
    # I see players losing the ball and throwing their arms up.
    H += [(W("i") - 0.35, "3/4 LEFT"), (W("and", 4) - 0.1, "DISGUSTED")]
    T += [(W("i") - 0.3, 2.5, 0.3)]
    arm(W("players") - 0.2, "L", "present"); B += [(W("losing"), "L", 0.4)]
    arm(W("their") - 0.25, "RL", "up")
    arm(W("up", 1, "e") + 0.15, "RL", "desk")
    # Get back and win it.
    H += [(W("get") - 0.2, "ANGRY"), (W("it", 1, "e") + 0.3, "FRONT")]
    T += [(W("get") - 0.2, 0.5, 0.9), (W("it", 1, "e") + 0.3, 0.0, 0.6)]
    arm(W("get") - 0.3, "R", "raise"); B += [(W("get"), "R", 0.9), (W("back", 2), "R", 1.0)]
    arm(W("win") - 0.3, "L", "raise"); B += [(W("win"), "RL", 1.2)]
    arm(W("it", 1, "e") + 0.35, "RL", "desk")
    c = sorted(c)
    # a 'go back to the desk' cue that lands within 0.6 s of that arm's next gesture is dropped,
    # so the arm flows straight from one gesture into the next instead of cancelling it
    keep = []
    for i, (t, a, p) in enumerate(c):
        if p == "desk" and any(ca == a and cp != "desk" and abs(ct - t) < 0.6 for (ct, ca, cp) in c):
            continue
        keep.append((t, a, p))
    return keep, sorted(B), sorted(T), sorted(H)

ARMCUES, BEATS, TORSO, HEADS = cues()

# ------------------------------------------------------------------ solvers
def spring_track(targets_at, n, freq=2.6, zeta=0.55, sub=8):
    """critically-under-damped spring following a piecewise-constant target (vector)."""
    w = 2 * math.pi * freq
    x = np.array(targets_at(0), float); v = np.zeros_like(x)
    out = np.zeros((n, len(x)))
    dt = 1.0 / FPS / sub
    for i in range(n):
        tgt = np.array(targets_at(i / FPS), float)
        for _ in range(sub):
            a = w * w * (tgt - x) - 2 * zeta * w * v
            v += a * dt; x += v * dt
        out[i] = x
    return out

def step_target(cuelist, default):
    def f(t):
        cur = default
        for ct, val in cuelist:
            if ct <= t: cur = val
            else: break
        return cur
    return f

def beat_curve(t, tb, tau=0.075):
    """chop offset: anticipation up, then snap down peaking at tb, then settle."""
    u = t - (tb - tau)
    if u < -0.16: return 0.0
    if u < 0: return 0.28 * math.sin(math.pi * (u + 0.16) / 0.16)       # small wind-up
    return -(u / tau) * math.exp(1 - u / tau)

def arm_channels():
    out = {}
    for arm in "RL":
        cl = [(t, POSE[p]) for (t, a, p) in ARMCUES if a == arm]
        tr = spring_track(step_target(cl, POSE["desk"]), N)
        # beats: elbow snaps down, wrist flicks
        for i in range(N):
            t = i / FPS
            for (tb, a, s) in BEATS:
                if arm in a and -0.3 < t - tb < 0.6:
                    b = beat_curve(t, tb) * s
                    sgn = 1 if tr[i, 1] >= 0 else -1        # chop toward 'down' for either flex direction
                    tr[i, 1] += 38 * b * sgn
                    tr[i, 2] += 18 * b
        out[arm] = tr
    return out

def torso_channels():
    tr = spring_track(step_target([(t, (l, f)) for t, l, f in TORSO], (0.0, 0.0)), N, freq=1.3, zeta=0.8)
    bounce = np.zeros(N)
    for i in range(N):
        t = i / FPS
        for (tb, a, s) in BEATS:
            if -0.3 < t - tb < 0.6: bounce[i] += -beat_curve(t, tb) * abs(s)
    return tr[:, 0], tr[:, 1], bounce

def head_at(t):
    cur = HEADS[0][1]
    for ht, h in HEADS:
        if ht <= t: cur = h
    return cur

if __name__ == "__main__":
    a = arm_channels(); lean, fwd, bounce = torso_channels()
    print("arm R range", a["R"].min(0).round(1), a["R"].max(0).round(1))
    print("beats", len(BEATS), "arm cues", len(ARMCUES), "head changes", len(HEADS))
    print("lean", lean.min().round(2), lean.max().round(2), "fwd", fwd.min().round(2), fwd.max().round(2), "bounce max", bounce.max().round(2))

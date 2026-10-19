"""The edit and the acting, keyed to the spoken words.

The film is built with a cursor: each shot starts where the last one ended, each line is placed a beat into its
shot, and the acting cues are tied to words (`w("B03", "meetings")`), so changing a pause moves everything after it.

Screen directions: Tim sits LEFT, Gareth RIGHT, Brent stands behind the desks at Gareth's right (screen right).
Gaze values are on screen: x -1 = looking screen-left, +1 = screen-right; y -1 up, +1 down; (0, 0) = into the lens.
"""
import json

FPS = 25
P = json.load(open("phones.json"))

SHOTS = []          # dict(set, t0, t1, cam=[(t, (cx, cy, w))], handheld)
LINES = {}          # lid -> time the clip's cut point (a0) is placed
TRACK = {}          # (char, attr) -> [(t, value)]
EVENTS = []         # sound and prop events: (t, kind, args)
EXTRAS = []         # walkers: dict(set, char, t0, x0, x1, y, scale, speed)
cursor = 0.0


def key(char, attr, t, v):
    TRACK.setdefault((char, attr), []).append((round(t, 3), v))


def shot(setname, dur, cam, handheld=True, moves=()):
    global cursor
    s = dict(set=setname, t0=cursor, t1=cursor + dur, cam=[(cursor, cam)] + [(cursor + dt, c) for dt, c in moves],
             handheld=handheld)
    SHOTS.append(s)
    cursor += dur
    return s


def say(lid, at):
    """place line `lid` so its first word starts at `at`; returns the time its last word ends"""
    L = P[lid]
    LINES[lid] = at - L["words"][0]["s"]
    return LINES[lid] + L["words"][-1]["e"]


def w(lid, word, k=1, end=False):
    n = 0
    for x in P[lid]["words"]:
        if x["w"] == word:
            n += 1
            if n == k:
                return LINES[lid] + (x["e"] if end else x["s"])
    raise KeyError((lid, word, k))


def ev(t, kind, **args):
    EVENTS.append((round(t, 3), kind, args))


# ------------------------------------------------------------------ cameras (world px of each plate)
TWO = (958, 376, 1380)          # Tim, Gareth and Brent
MED_BG = (1236, 392, 930)       # Brent and Gareth
BRENT_MED = (1340, 332, 700)    # Brent, Gareth's shoulder at frame left
TIM_1 = (862, 505, 1300)
GAR_1 = (915, 492, 1300)
INTERVIEW = (846, 448, 1000)

# ------------------------------------------------------------------ resting states
for c in ("tim", "gareth", "brent"):
    key(c, "lid", 0, 0.0)
    key(c, "smile", 0, 0.0)
    key(c, "rot", 0, 0.0)
    key(c, "dy", 0, 0.0)
key("tim", "pose", 0, "13_seated_front")
key("gareth", "pose", 0, "13_seated_front")
key("brent", "pose", 0, "02_talking_gesture")
key("brent", "smile", 0, 0.45)
LOOK = dict(
    tim=dict(brent=(0.9, -0.38), gareth=(0.78, 0.0), box=(0.8, 0.5), screen=(-0.7, 0.35), lens=(-0.04, 0.0)),
    gareth=dict(brent=(0.82, -0.5), tim=(-0.88, 0.0), pad=(0.25, 0.85), slip=(0.75, -0.2)),
    brent=dict(men=(-0.72, 0.38), tim=(-0.95, 0.28), gareth=(-0.6, 0.5), lens=(0.0, 0.0), slip=(-0.5, 0.8),
               interviewer=(0.42, -0.05), box=(-0.55, 0.85)),
)


def look(c, t, at):
    key(c, "gaze", t, LOOK[c][at] if isinstance(at, str) else at)


look("tim", 0, "screen")
look("gareth", 0, "brent")
look("brent", 0, "men")

# ================================================================== the film
# ---- cold open: the car park, then the office floor
s = shot("carpark", 3.0, (836, 470, 1672), handheld=False, moves=[(3.0, (836, 466, 1610))])
EXTRAS.append(dict(set="carpark", char="Neil_Godwin", t0=s["t0"] - 0.4, x0=330, x1=980, y=652, h=205, speed=112))
ev(s["t0"], "bed", room="carpark", t1=s["t1"])

s = shot("wide", 4.0, (836, 470, 1672), moves=[(4.0, (836, 470, 1630))])
EXTRAS.append(dict(set="wide", char="Dawn_Tinsley", t0=s["t0"] - 0.5, x0=600, x1=1760, y=432, h=210, speed=118))
EXTRAS.append(dict(set="wide", char="Finchy", t0=s["t0"] - 1.4, x0=1240, x1=-220, y=668, h=330, speed=170))
ev(s["t0"], "bed", room="office", t1=None)
ev(s["t0"] + 0.4, "phone")
ev(s["t0"] + 0.1, "typing", dur=3.6, distant=True)

# ---- SHOT 01: two-shot, already in progress
s = shot("desks", 6.6, TWO)
ev(s["t0"], "typing", dur=0.75, distant=False)          # Tim, until Brent starts
look("tim", s["t0"] + 0.85, "brent")
key("gareth", "dy", s["t0"], 5.0)                      # a little slumped...
e = say("B01", s["t0"] + 0.85)
key("gareth", "dy", s["t0"] + 1.05, 5.0)
key("gareth", "dy", s["t0"] + 1.35, 0.0)               # ...straightens as Brent starts
ev(s["t0"] + 1.1, "creak")
look("brent", w("B01", "management") - 0.05, "lens")   # the pleased glance at the crew
look("brent", w("B01", "could") + 0.15, "men")
key("brent", "smile", w("B01", "management"), 0.6)
key("brent", "smile", e + 0.6, 0.5)
# ---- SHOT 02: Brent's interview
s = shot("interview", 11.9, INTERVIEW, handheld=False)
key("brent", "pose", s["t0"], "13_seated_front")
look("brent", s["t0"], "interviewer")
key("brent", "smile", s["t0"], 0.45)
e = say("B02", s["t0"] + 0.9)
key("brent", "pose", w("B02", "obviously") - 0.3, "19_seated_folded_arms")
key("brent", "smile", w("B02", "obviously") - 0.2, 0.45)
key("brent", "smile", w("B02", "obviously") + 0.3, 0.15)
key("brent", "smile", w("B02", "just"), 0.1)
key("brent", "smile", w("B02", "go") + 0.25, 0.1)
key("brent", "smile", w("B02", "go") + 0.55, 0.6)      # the smile that asks for agreement
key("brent", "rot", w("B02", "go") + 0.4, 0.0)
key("brent", "rot", w("B02", "go") + 0.8, 0.8)         # a small hopeful tilt
look("brent", w("B02", "go") + 1.2, (0.3, -0.08))
# ---- SHOT 03: back at the desks
s = shot("desks", 6.2, TWO)
key("brent", "pose", s["t0"], "01_neutral")
key("brent", "rot", s["t0"], 0.0)
key("brent", "smile", s["t0"], 0.35)
look("brent", s["t0"], "gareth")
ev(s["t0"] + 0.4, "pen_tap", who="gareth")
look("gareth", s["t0"], "pad")
look("gareth", s["t0"] + 0.75, "brent")
e = say("G01", s["t0"] + 0.95)
look("tim", s["t0"] + 1.15, "gareth")                  # Tim turns only his eyes
key("gareth", "smile", e + 0.1, 0.0)
key("gareth", "smile", e + 0.35, 0.22)                 # watches Brent for approval
key("gareth", "dy", e + 0.2, 0.0)
key("gareth", "dy", e + 0.4, -3.0)
key("gareth", "dy", e + 0.7, 0.0)
# ---- SHOT 04: Tim single
s = shot("tim", 3.75, TIM_1)
e = say("T01", s["t0"] + 0.6)
key("tim", "lid", s["t0"], 0.05)
# ---- SHOT 05: Gareth single
s = shot("gareth", 5.9, GAR_1)
key("gareth", "smile", s["t0"], 0.0)
look("gareth", s["t0"], "tim")
e = say("G02", s["t0"] + 0.55)
look("gareth", e + 0.35, "pad")
key("gareth", "lid", e + 0.35, 0.0)
key("gareth", "lid", e + 0.5, 0.32)
key("gareth", "smile", e + 0.6, 0.15)
EXTRAS.append(dict(set="gareth", char="Dawn_Tinsley", t0=e + 0.4, x0=1700, x1=-180, y=574, h=430, speed=480))
# ---- SHOT 06: Brent and Gareth; Brent takes the slip
s = shot("desks", 7.9, MED_BG, moves=[])
key("gareth", "lid", s["t0"], 0.0)
look("gareth", s["t0"], "brent")
key("gareth", "smile", s["t0"], 0.0)
key("brent", "pose", s["t0"] + 0.25, "12_lean_forward")
ev(s["t0"] + 0.55, "paper", dur=0.5)
key("brent", "pose", s["t0"] + 1.15, "02_talking_gesture")
ev(s["t0"] + 1.15, "slip", state="hand")
look("brent", s["t0"] + 1.2, "slip")
look("gareth", s["t0"] + 1.3, "slip")
key("brent", "smile", s["t0"] + 1.2, 0.45)
e = say("B03", s["t0"] + 2.0)
key("brent", "smile", w("B03", "fewer") + 0.05, 0.45)
key("brent", "smile", w("B03", "fewer") + 0.35, 0.05)   # the smile drops a little...
key("brent", "smile", w("B03", "constructive") - 0.15, 0.05)
key("brent", "smile", w("B03", "constructive") + 0.15, 0.5)  # ...and is put back
look("brent", w("B03", "who") - 0.25, "men")
look("gareth", w("B03", "who"), "brent")
SHOTS[-1]["cam"].append((w("B03", "who") - 0.2, MED_BG))
SHOTS[-1]["cam"].append((w("B03", "that") + 0.6, (1252, 380, 860)))   # the small documentary reframe
SHOTS[-1]["t1"] = e + 1.0
cursor = SHOTS[-1]["t1"]
# ---- SHOT 07: Tim single
s = shot("tim", 4.5, TIM_1)
look("tim", s["t0"], "brent")
e = say("T02", s["t0"] + 0.6)
key("tim", "dy", e + 0.2, 0.0)
key("tim", "dy", e + 0.6, 2.5)                          # the hand settles on the desk
EXTRAS.append(dict(set="tim", char="Finchy", t0=e + 0.45, x0=-200, x1=1900, y=600, h=430, speed=540))
# ---- SHOT 08: Brent medium
s = shot("desks", 8.0, BRENT_MED)
key("brent", "smile", s["t0"], 0.2)
look("brent", s["t0"], "men")
e = say("B04", s["t0"] + 0.45)
key("brent", "pose", w("B04", "it's") - 0.25, "08_wave")     # holds the paper higher
key("brent", "smile", w("B04", "it's") - 0.1, 0.5)
look("brent", e + 0.35, "tim")
key("brent", "lid", e + 0.35, 0.0)
key("brent", "lid", e + 0.6, 0.3)                       # the smile stays, the eyes get suspicious
key("brent", "smile", e + 0.4, 0.5)
key("brent", "smile", e + 1.5, 0.35)
look("brent", e + 1.15, "gareth")
look("brent", e + 1.9, "tim")
SHOTS[-1]["t1"] = e + 2.55
cursor = SHOTS[-1]["t1"]
# ---- SHOT 09: Gareth, then Tim, then Gareth
s = shot("gareth", 2.9, GAR_1)
key("brent", "lid", s["t0"], 0.0)
look("gareth", s["t0"], "brent")
key("gareth", "smile", s["t0"], 0.0)
e = say("G03", s["t0"] + 0.5)
key("gareth", "smile", w("G03", "four", end=True), 0.18)
look("gareth", w("G03", "tim") - 0.1, "tim")            # cut on the turn
SHOTS[-1]["t1"] = w("G03", "tim") + 0.62
cursor = SHOTS[-1]["t1"]
s = shot("tim", 5.4, TIM_1)
look("tim", s["t0"], "gareth")
key("tim", "dy", s["t0"], 2.5)
e = say("T03", s["t0"] + 0.65)
SHOTS[-1]["t1"] = e + 0.55
cursor = SHOTS[-1]["t1"]
s = shot("gareth", 4.4, GAR_1)
key("gareth", "smile", s["t0"], 0.0)
look("gareth", s["t0"], "pad")
key("gareth", "lid", s["t0"], 0.3)
ev(s["t0"], "write", dur=1.2)                           # already writing
e = say("G04", s["t0"] + 1.4)
ev(e + 0.45, "exhale")                                  # Tim, off screen
SHOTS[-1]["t1"] = e + 1.45
cursor = SHOTS[-1]["t1"]
# ---- SHOT 10: Brent and the desks
s = shot("desks", 9.0, TWO)
key("gareth", "lid", s["t0"], 0.3)
look("gareth", s["t0"], "pad")
ev(s["t0"], "write", dur=0.75)
look("gareth", s["t0"] + 0.8, "brent")
key("gareth", "lid", s["t0"] + 0.8, 0.0)
key("brent", "pose", s["t0"], "02_talking_gesture")
key("brent", "lid", s["t0"], 0.0)
look("brent", s["t0"], "slip")
ev(s["t0"] + 0.35, "fold", dur=0.55)
ev(s["t0"] + 0.35, "paper", dur=0.45)
look("brent", s["t0"] + 1.0, "men")
key("brent", "smile", s["t0"] + 0.9, 0.42)
look("tim", s["t0"], "brent")
e = say("B05", s["t0"] + 1.45)
key("tim", "pose", w("B05", "lunch", end=True) + 0.12, "19_seated_folded_arms")
key("tim", "dy", w("B05", "lunch", end=True) + 0.12, 0.0)
SHOTS[-1]["t1"] = e + 1.0
cursor = SHOTS[-1]["t1"]
# ---- SHOT 11: Tim, then Brent
s = shot("tim", 2.6, TIM_1)
e = say("T04", s["t0"] + 0.55)
SHOTS[-1]["t1"] = e + 0.55
cursor = SHOTS[-1]["t1"]
s = shot("desks", 5.0, BRENT_MED)
ev(s["t0"], "slip", state="box")
key("brent", "pose", s["t0"], "07_hands_on_hips")
key("brent", "smile", s["t0"], 0.05)
look("brent", s["t0"], "tim")
e = say("B06", s["t0"] + 0.6)
key("brent", "rot", e + 0.1, 0.0)
key("brent", "rot", e + 0.45, -1.4)                     # chin up: settled
key("brent", "lid", e + 0.1, 0.0)
key("brent", "lid", e + 0.45, 0.22)
key("brent", "smile", e + 0.3, 0.05)
key("brent", "smile", e + 0.6, 0.3)
SHOTS[-1]["t1"] = e + 1.5
cursor = SHOTS[-1]["t1"]
# ---- SHOT 12: the vote
s = shot("desks", 9.0, TWO)
key("brent", "rot", s["t0"], -1.4)
key("brent", "rot", s["t0"] + 1.2, 0.0)
key("brent", "lid", s["t0"] + 1.0, 0.0)
look("brent", s["t0"], "men")
look("gareth", s["t0"], "brent")
key("gareth", "pen_up", s["t0"], 0.0)
key("gareth", "pen_up", s["t0"] + 0.3, 0.0)
key("gareth", "pen_up", s["t0"] + 0.55, 1.0)            # pen raised, ready to note attendance
e = say("G05", s["t0"] + 0.8)
look("brent", e + 0.05, "gareth")
e = say("B07", e + 0.28)
key("brent", "smile", e, 0.3)
look("tim", e + 0.55, "brent")
look("tim", e + 1.0, "box")
look("tim", e + 1.45, "brent")
e = say("T05", e + 1.55)
look("brent", w("T05", "vote"), "tim")
e = say("B08", e + 0.32)
key("brent", "smile", w("B08", "show"), 0.55)
key("gareth", "pen_up", e, 1.0)
SHOTS[-1]["t1"] = e + 1.0                               # hold the wide: nobody moves
cursor = SHOTS[-1]["t1"]
s = shot("tim", 3.6, TIM_1, handheld=True)
look("tim", s["t0"], "brent")
look("tim", s["t0"] + 0.45, "lens")                     # the one look into the lens
key("tim", "smile", s["t0"] + 0.9, 0.0)
key("tim", "smile", s["t0"] + 1.3, 0.75)                # very small, exhausted half-smile
key("tim", "lid", s["t0"] + 0.9, 0.0)
key("tim", "lid", s["t0"] + 1.3, 0.2)
END = cursor
ev(END, "cut_to_black")
TOTAL = END + 1.0

# blinks: natural, irregular, never during the looks that matter
NO_BLINK = {"tim": [(END - 3.2, END)], "brent": [], "gareth": []}

"""The performance: every cue of the 19 beats keyed to the recorded words (build/timeline.json).

Soriano never realises how bad the speech sounds: deadpan, calm, professional, occasionally smug; never a
screaming villain. Gestures start 4-6 frames before their word, hit the pose on the stressed word, then settle.
The camera and the body get stiller as the jokes get more absurd.

Camera shares (portrait): A ~65 %, B ~27 %, C ~8 %, cutting on changes of thought, never zooming constantly.
Poses: g01 palms up, g02 shrug, g03 one point, g04 hold on / palms forward, g05 counting, g06 arms folded,
g07 hands clasped (default), g08 dismissive; r1 = his right palm up (frame left) with the left hand resting,
l1 = the mirror (frame-right palm up, right hand resting).

state(t) -> everything the renderer needs for the frame at time t."""
import json, math, numpy as np

TL = json.load(open("build/timeline.json"))
FPS = TL["fps"]
WORDS = TL["words"]
BEATS = {b["n"]: b for b in TL["beats"]}
SPEECH_END = TL["marks"]["speech_end"]
HOLD_END = TL["marks"]["hold_end"]
TOTAL = TL["total"]

def _occ(beat, word, n):
    B = BEATS[beat]
    seen = 0
    for p in B["phrases"]:
        for i in range(p["w0"], p["w1"] + 1):
            if WORDS[i]["w"] == word:
                seen += 1
                if seen == n: return WORDS[i]
    raise KeyError((beat, word, n))
def W(beat, word, n=1): return _occ(beat, word, n)["s"]
def WE(beat, word, n=1): return _occ(beat, word, n)["e"]
LEAD = 5 / FPS                    # gestures begin 5 frames before their word

# ---------------------------------------------------------------- cue lists
POSE, ARM, KEYS, NODS, SHOULD, CUTS, PUSHES, GFX, STILL, GAZE, SFX = [], [], {}, [], [], [], [], [], [], [], []
def P(t, pose, lead=True): POSE.append((t - (LEAD if lead else 0.0), pose))
def ARMM(t0, t1, pose, side, kind, **kw): ARM.append(dict(t0=t0, t1=t1, pose=pose, side=side, kind=kind, **kw))
def EX(t, dur=0.25, **kv):
    for k, v in kv.items(): KEYS.setdefault(k, []).append((t, v, dur))
def NEUTRAL(t, dur=0.35, keep=()):
    for k in ("brow_l", "brow_r", "brow_in", "arch", "smile", "smirk", "squint"):
        if k not in keep: EX(t, dur, **{k: 0.0})
def NOD(t, amp=1.0): NODS.append((t, amp))
def SIGH(t, amp=1.0): SHOULD.append((t, amp))
def CAM(t, shot): CUTS.append((t, shot))
def PUSH(t0, t1, a, b): PUSHES.append((t0, t1, a, b))
def G(t0, t1, name): GFX.append((t0, t1, name))
def STILLW(t0, t1): STILL.append((t0, t1))
def LOOK(t, dx, dy, hold=0.4, go=0.12, back=0.2): GAZE.append((t, dx, dy, hold, go, back))

# ---------------------------------------------------------------- the 19 beats
# 01  A -> C, G07 -> G01: formal, clasped; one hand opens on "Essentially"; C just before "DID it"; second palm opens
CAM(0.0, "A"); P(0.0, "g07", lead=False)
SIGH(0.25, 0.8)                                            # shoulder drop on the (page's) sigh
NOD(W(1, "manchester"), 0.5); NOD(W(1, "premier"), 0.4)
P(W(1, "essentially"), "r1"); EX(W(1, "essentially"), brow_l=1.2, brow_r=1.2, smile=0.25)
CAM(W(1, "did") - 0.12, "C"); NOD(W(1, "did") + 0.05, 0.7)
EX(WE(1, "it"), 0.3, smirk=0.55, smile=0.3, squint=0.35)    # no laugh in the recording: a smug closed smile instead
CAM(W(1, "but") - 0.1, "A"); NEUTRAL(W(1, "but") - 0.1)
P(W(1, "people"), "g01"); EX(W(1, "people"), 0.3, brow_l=3.0, brow_r=3.0)
# 02  B, G01 -> G08: the imaginary document, disappointed nod, glance down on ACCURATE, small dismissive wave
CAM(13.9, "B"); NEUTRAL(13.9)
P(W(2, "document"), "r1"); ARMM(W(2, "document") - 0.15, W(2, "published") + 0.4, "r1", "R", "reach", deg=-9)
SFX.append((W(2, "document") + 0.05, "paper"))
EX(W(2, "negative"), 0.35, brow_in=-1.2); NOD(W(2, "negative") + 0.15, 1.0)
P(18.6, "g07"); SIGH(18.94, 1.3)
EX(W(2, "unfortunately"), 0.3, brow_in=-2.0, brow_l=0.6, brow_r=0.6)
LOOK(W(2, "accurate"), 0.0, 0.55, hold=0.35)
G(WE(2, "accurate") + 0.05, 24.45, "accurate")
P(W(2, "we"), "g08"); ARMM(W(2, "we"), W(2, "asked") + 0.3, "g08", "R", "wave", deg=6, n=1.5)
EX(W(2, "we"), 0.3, brow_in=-1.0, smirk=0.25)
P(W(2, "together") + 0.35, "g07"); NEUTRAL(26.6)
# 03  A -> B, G04 -> G07: palms forward on CONSEQUENCES; confident nod; the whisper leans in, slow push to B
CAM(26.92, "A")
NOD(W(3, "next"), 0.4); NOD(W(3, "club"), 0.5)
P(W(3, "consequences"), "g04"); EX(W(3, "consequences"), 0.3, brow_l=1.5, brow_r=1.5)
P(37.45, "g07"); NEUTRAL(37.4)
NOD(W(3, "lawyers") + 0.1, 0.8); EX(W(3, "lawyers"), 0.3, smile=0.2)
EX(W(3, "they're") - 0.2, 0.5, lean=1.0, chin=1.0, smirk=0.3, smile=0.1)
PUSH(W(3, "they're") - 0.2, W(3, "years"), "A", "B")
G(W(3, "years"), W(4, "the") + 0.25, "ongoing")
EX(WE(3, "years") + 0.15, 0.5, lean=0.0, chin=0.0); NEUTRAL(WE(3, "years") + 0.2)
# 04  A -> C, G03 -> G01: index up on "one accusation", lowered slowly; YES in C; one palm up on "secretly";
#     the whisper: a glance frame right and back, then a straight stare on STOPPED
CAM(43.19, "A"); SIGH(43.3, 0.7)
P(W(4, "one"), "g03"); ARMM(W(4, "accusation") + 0.45, W(4, "accusation") + 1.7, "g03", "R", "lower", deg=22)
P(W(4, "that") + 0.2, "g07")
CAM(W(4, "yes") - 0.2, "C"); NOD(W(4, "yes") + 0.03, 1.6); EX(W(4, "yes"), 0.2, brow_l=1.5, brow_r=1.5, smirk=0.3)
CAM(W(4, "but") - 0.1, "A"); NEUTRAL(W(4, "but") - 0.1)
P(W(4, "secretly", 2), "r1"); EX(W(4, "secretly", 2), 0.3, brow_l=2.0, brow_r=2.0, brow_in=0.8, smile=-0.25)
P(W(4, "we") - 0.2, "g07"); NEUTRAL(W(4, "we") - 0.1)
EX(W(4, "we") - 0.15, 0.4, lean=0.8, chin=0.6)
PUSH(W(4, "we") - 0.15, W(4, "stopped"), "A", "B")
LOOK(W(4, "simply"), 0.62, 0.0, hold=0.55)
EX(W(4, "stopped"), 0.15, brow_in=-0.8)
EX(WE(4, "us") + 0.2, 0.4, lean=0.0, chin=0.0); NEUTRAL(WE(4, "us") + 0.2)
# 05  A -> B, G01 -> G02: owner on one hand, sponsor on the other, smug nod, shrug; brows up on TROUSERS (chest-up)
CAM(60.09, "A")
P(W(5, "owner"), "r1"); ARMM(W(5, "owner") - 0.15, W(5, "owner") + 0.5, "r1", "R", "beat", deg=5)
P(W(5, "sponsor"), "l1"); ARMM(W(5, "sponsor") - 0.15, W(5, "sponsor") + 0.5, "l1", "L", "beat", deg=5)
EX(W(5, "completely"), 0.3, smile=0.5, squint=0.4); NOD(W(5, "completely") + 0.35, 0.8)
P(W(5, "pocket"), "g02"); EX(W(5, "pocket"), 0.3, shrug=1.0); EX(WE(5, "pocket") + 0.45, 0.4, shrug=0.0)
SIGH(69.74, 1.2); NEUTRAL(69.8)
CAM(69.95, "B"); P(70.1, "g07")
EX(W(5, "trousers") - 0.05, 0.25, brow_l=3.5, brow_r=3.5)
NEUTRAL(WE(5, "trousers") + 0.6)
# 06  A, G05 -> G07: brightens, counts 1-2-3, both hands open proudly on EXACTLY, back to the clasp, mock sadness
CAM(75.35, "A")
EX(W(6, "we"), 0.3, brow_l=2.0, brow_r=2.0, smile=0.4)
NOD(W(6, "irrefutable") + 0.1, 0.6)
P(W(6, "bank"), "g05")
for i, w in enumerate(("bank", "money", "witnesses")):
    ARMM(W(6, w) - 0.1, W(6, w) + 0.35, "g05", "R", "tap", step=i)
P(W(6, "exactly"), "g01"); EX(W(6, "exactly"), 0.3, brow_l=2.5, brow_r=2.5, smile=0.5, squint=0.3)
P(W(6, "we", 2) - 0.1, "g07")
EX(W(6, "we", 2), 0.4, brow_in=3.5, brow_l=-0.4, brow_r=-0.4, smile=-0.2, squint=0.0, chin=0.8)
EX(W(7, "instead") - 0.1, 0.4, chin=0.0); NEUTRAL(W(7, "instead") - 0.1)
# 07  B -> C, G07: stillness; eyes travel left to right; C and one raised eyebrow on ALL the way; mildly offended
CAM(92.30, "B"); STILLW(92.3, 100.6)
LOOK(W(7, "followed") - 0.05, -0.62, 0.0, hold=0.25, go=0.18, back=0.01)
LOOK(W(7, "the") + 0.02, 0.62, 0.0, hold=0.35, go=0.45, back=0.3)
CAM(W(7, "all") - 0.15, "C"); EX(W(7, "all") - 0.05, 0.3, brow_l=3.5, arch=8.0, brow_r=-1.0)
EX(W(7, "which"), 0.4, brow_l=1.2, brow_r=1.2, arch=0.0, brow_in=1.0, smile=-0.3)
EX(W(7, "obsessive"), 0.3, brow_in=-1.5, brow_l=1.8, brow_r=1.8, smile=-0.35)
# 08  A -> B, G03 -> G01: index on "one simple arrangement"; 115; hands apart on SEPARATE, together on "efficient"
CAM(100.66, "A"); NEUTRAL(100.66)
P(W(8, "one"), "g03"); P(W(8, "people") - 0.1, "g07")
G(WE(8, "fifteen") + 0.05, W(8, "and", 2) - 0.1, "115")
EX(W(8, "separate"), 0.3, brow_l=1.5, brow_r=1.5)
P(W(8, "separate"), "g01"); ARMM(W(8, "separate") - 0.15, W(8, "rules") + 0.3, "g01", "B", "apart", deg=7)
P(W(8, "efficient"), "g07")
PUSH(W(8, "we") - 0.1, W(8, "efficient") + 0.4, "A", "B")
EX(W(8, "we"), 0.3, smile=0.5, squint=0.4, brow_l=1.0, brow_r=1.0); NOD(W(8, "efficient") + 0.2, 1.0)
# 09  A, G08 -> G02: dismissive sweep; controlled side to side on the lists; a flash on "pay a fortune"; shrug
CAM(117.59, "A"); NEUTRAL(117.6)
P(W(9, "aggressively"), "g08"); ARMM(W(9, "aggressively") - 0.1, W(9, "promoted") + 0.5, "g08", "R", "sweep", deg=14)
EX(W(9, "aggressively"), 0.3, brow_in=-1.2)
P(W(9, "every"), "r1")
ARMM(W(9, "every") - 0.15, W(9, "channel") + 0.5, "r1", "R", "side", marks=[W(9, "newspaper"), W(9, "television")], deg=8)
SIGH(126.87, 1.1)
EX(W(9, "pay") - 0.05, 0.2, brow_l=3.0, brow_r=3.0, smile=0.5, brow_in=0.0)
EX(W(9, "coverage"), 0.4, brow_l=0.0, brow_r=0.0, smile=0.0)
EX(W(9, "suddenly"), 0.4, brow_in=3.5, smile=-0.25)
P(W(9, "nobody"), "g02"); EX(W(9, "nobody"), 0.3, shrug=0.7); EX(W(9, "logo"), 0.4, shrug=0.0)
# 10  B, G07 -> G02: slow eyebrow on "Apparently"; tiny nod on the second HAPPENED, then completely still; hands open
CAM(134.68, "B"); P(134.9, "g07"); NEUTRAL(134.9)
EX(W(10, "apparently"), 0.9, brow_l=3.0, arch=6.0, brow_r=0.5)
NOD(W(10, "happened", 2) + 0.05, 0.55); STILLW(W(10, "happened", 2) + 0.4, W(10, "nobody"))
P(W(10, "nobody"), "g02"); EX(W(10, "nobody"), 0.4, brow_l=0.0, arch=0.0, brow_r=0.0, brow_in=3.0, smile=-0.2)
# 11  A, G04 -> G01: "hold on" palms; LOVELY brightens; one elegant hand motion across "the passing"; deadpan "Surely"
CAM(149.0, "A"); NEUTRAL(149.0)
P(W(11, "wider"), "g04"); EX(W(11, "wider"), 0.3, brow_in=-0.8)
P(W(11, "lovely"), "g01"); EX(W(11, "lovely") - 0.05, 0.25, brow_l=2.5, brow_r=2.5, smile=0.7, squint=0.5, brow_in=0.0)
P(W(11, "you've"), "r1"); EX(W(11, "you've"), 0.4, smile=0.35, squint=0.2)
ARMM(W(11, "the", 2) - 0.1, WE(11, "passing") + 0.2, "r1", "R", "across", deg=26)
P(W(11, "surely") - 0.05, "g07"); NEUTRAL(W(11, "surely"), keep=())
# 12  A -> B, G05: counts law / principle / fact; LAW, PRINCIPLES, FACTS build; offended nods; clear, B, sincere
CAM(159.97, "A")
P(W(12, "law") - 0.3, "g05")
for i, w in enumerate(("law", "principle", "fact")):
    ARMM(W(12, w) - 0.1, W(12, w) + 0.35, "g05", "R", "tap", step=i)
P(W(12, "the", 2) - 0.1, "g07")
EX(W(12, "law", 2), 0.3, brow_l=2.0, brow_r=2.0, brow_in=-0.8, smile=-0.3); NOD(W(12, "law", 2) + 0.35, 0.8)
EX(W(12, "principles"), 0.3, brow_l=3.0, brow_r=3.0)
EX(W(12, "facts"), 0.3, brow_l=2.2, brow_r=2.2, smile=-0.45); NOD(W(12, "facts") + 0.25, 0.6)
SIGH(176.4, 0.9)
CAM(176.6, "B"); P(176.6, "g07", lead=False)
EX(176.6, 0.4, brow_l=0.0, brow_r=0.0, brow_in=1.8, smile=0.0)
# 13  A -> C, G03 -> G08: delighted; index on 2020; CAS beats with stamps; dead still on the dishwasher; C, smug nod
CAM(179.17, "A"); NEUTRAL(179.2)
EX(W(13, "remember"), 0.3, brow_l=2.0, brow_r=2.0, smile=0.5)
P(W(13, "twenty"), "g03")
P(W(13, "we", 2) - 0.1, "g07")
P(W(13, "cas", 2), "g08")
for n_ in (2, 3):
    ARMM(W(13, "cas", n_) - 0.12, W(13, "cas", n_) + 0.4, "g08", "R", "flick", deg=9)
    G(W(13, "cas", n_), W(13, "cas", n_) + 0.95, f"cas{n_ - 1}")
EX(W(13, "parking"), 0.3, smile=0.2, brow_l=1.0, brow_r=1.0)
P(W(13, "my") - 0.25, "g07"); NEUTRAL(W(13, "my") - 0.2)
STILLW(W(13, "my") - 0.2, W(13, "we've") - 0.12)
CAM(W(13, "we've") - 0.12, "C")
EX(W(13, "we've"), 0.3, smirk=0.6, smile=0.3, squint=0.4); NOD(W(13, "cleared") + 0.1, 0.8)
# 14  A, G01 -> G06: broad professional gesture; hands to his chest on KEEP; folded arms; hold the stare
CAM(198.28, "A"); NEUTRAL(198.3)
EX(W(14, "we"), 0.3, brow_l=1.5, brow_r=1.5, smile=0.3)
P(W(14, "pursue"), "g01"); ARMM(W(14, "every") - 0.12, W(14, "every") + 0.45, "g01", "B", "beat", deg=4)
P(W(14, "keep"), "g05"); EX(W(14, "keep"), 0.3, smile=0.0, brow_l=0.5, brow_r=0.5)
P(W(14, "everyone"), "g06"); EX(W(14, "stops"), 0.3, brow_l=0.0, brow_r=0.0)
STILLW(W(14, "fucking") - 0.1, 211.3)
# 15  B -> C, G06 -> G07: unfolds into the clasp, mock wounded; glance down on the whisper; C, irritated FINDING OUT
CAM(211.34, "B")
P(W(15, "compensation"), "g07"); EX(W(15, "we"), 0.4, brow_in=3.5, smile=-0.2)
LOOK(W(15, "yes") + 0.02, 0.0, 0.55, hold=0.7)
EX(W(15, "yes"), 0.4, chin=0.5); EX(W(15, "contributed"), 0.4, chin=0.0)
CAM(W(15, "people") - 0.15, "C"); STILLW(W(15, "but"), 225.6)
EX(W(15, "finding") - 0.05, 0.25, brow_in=-2.6, squint=0.45, smile=-0.2)
# 16  A, G07 -> G01: warm and paternal; a small circle of the hand on "round several relatives"; palms on GIFT
CAM(225.65, "A"); NEUTRAL(225.7)
EX(W(16, "i"), 0.5, smile=0.35, brow_in=1.0, brow_l=0.8, brow_r=0.8, tilt=1.4)
P(W(16, "money"), "r1")
ARMM(W(16, "round") - 0.1, WE(16, "relatives"), "r1", "R", "circle", deg=6, n=1)
P(W(16, "gift"), "g01"); EX(W(16, "gift"), 0.3, smile=0.45, brow_l=1.5, brow_r=1.5, tilt=0.0)
# 17  A -> B, G05 -> G07: brisk count; SUPPORTER / JOURNALIST cards; clasp, lean in, whisper, side-eye, back
CAM(244.53, "A"); NEUTRAL(244.6)
P(W(17, "if") - 0.1, "g05")
ARMM(W(17, "supporter") - 0.1, W(17, "supporter") + 0.35, "g05", "R", "tap", step=0)
ARMM(W(17, "journalist") - 0.1, W(17, "journalist") + 0.35, "g05", "R", "tap", step=1)
G(WE(17, "innocent") + 0.05, W(17, "if", 3) - 0.2, "supporter")
G(WE(17, "appealing") + 0.05, W(17, "if", 3) - 0.2, "journalist")
P(W(17, "if", 3) - 0.15, "g07")
EX(W(17, "if", 3) - 0.2, 0.5, lean=1.0, chin=0.7)
PUSH(W(17, "if", 3) - 0.2, W(17, "owner"), "A", "B")
LOOK(W(17, "check"), -0.7, 0.0, hold=0.5)
EX(WE(17, "owner") + 0.2, 0.4, lean=0.0, chin=0.0)
# 18  A -> B, G01 -> G07: triumphant, chest lifted, palms open; chin dip on the whisper; proud; push to POSITIVES
CAM(263.0, "A"); NEUTRAL(263.0)
EX(W(18, "very"), 0.4, chest=1.0, brow_l=2.0, brow_r=2.0, smile=0.55)
P(W(18, "look"), "g01")
P(W(18, "admittedly") - 0.15, "g07"); EX(W(18, "admittedly"), 0.35, chin=1.2, chest=0.0, smile=0.15, brow_l=0.5, brow_r=0.5)
EX(W(18, "but"), 0.35, chin=0.0, smile=0.5, brow_l=1.8, brow_r=1.8)
P(W(18, "sponsorship"), "g01")
P(W(18, "you") - 0.1, "g07")
PUSH(W(18, "you") - 0.1, W(18, "positives"), "A", "B")
EX(W(18, "positives"), 0.3, smile=0.55, squint=0.45); NOD(W(18, "positives") + 0.15, 1.0)
# 19  B -> C, G07: settles; "Thank you" like the end; sincere; closest C for the whisper; faint smile; hold; CUT
CAM(278.32, "B"); NEUTRAL(278.3); P(278.3, "g07", lead=False)
EX(W(19, "thank"), 0.3, smile=0.4); NOD(W(19, "thank") + 0.1, 0.6)
EX(W(19, "and"), 0.4, smile=0.0, brow_in=1.6)
CAM(W(19, "according") - 0.25, "C2"); STILLW(W(19, "according") - 0.25, TOTAL)
EX(W(19, "according") - 0.2, 0.4, brow_in=0.3)
EX(WE(19, "happens") + 0.05, 0.45, smirk=0.45, smile=0.25, squint=0.25, brow_in=0.0)

# ---------------------------------------------------------------- blinks: every 2-6 s, never on the key words
KEY = [(1, "did"), (4, "yes"), (5, "trousers"), (7, "all"), (10, "happened", 2), (13, "cleared"), (14, "keep"),
       (15, "finding"), (15, "out"), (16, "gift"), (18, "positives")]
KEYWIN = [(W(b, w, *(n[:1] or [1])) - 0.3, WE(b, w, *(n[:1] or [1])) + 0.2) for b, w, *n in KEY]
def _blinks():
    rng = np.random.default_rng(11)
    out, t = [], 1.3
    gz = [(g[0] - 0.2, g[0] + g[3] + 0.4) for g in GAZE]
    while t < HOLD_END - 0.4:
        ok = all(not (a <= t <= b) for a, b in KEYWIN + gz)
        if ok:
            out.append(t); t += rng.uniform(2.2, 5.6)
        else:
            t += 0.25
    return out
BLINKS = _blinks()

# ---------------------------------------------------------------- evaluation
def _smooth(u): u = min(1.0, max(0.0, u)); return u * u * (3 - 2 * u)
for k in KEYS: KEYS[k].sort(key=lambda x: x[0])
POSE.sort(); CUTS.sort()

def key(k, t, default=0.0):
    ks = KEYS.get(k)
    if not ks: return default
    v_prev, v = default, default
    for (tk, val, dur) in ks:
        if tk > t: break
        u = _smooth((t - tk) / max(dur, 1e-3))
        v_prev = v
        v = v + (val - v) * u if u < 1 else val
    return v

def pose_at(t):
    cur, since, prev = POSE[0][1], POSE[0][0], POSE[0][1]
    for tp, p in POSE:
        if tp <= t:
            prev, cur, since = cur, p, tp
    return cur, t - since, prev

def arm_offsets(t, pose):
    """-> {side: (elbow deg, wrist deg, dx, dy)} for the active arm moves on this pose"""
    out = {}
    for m in ARM:
        if not (m["t0"] <= t <= m["t1"]) or m["pose"] != pose: continue
        u = (t - m["t0"]) / max(m["t1"] - m["t0"], 1e-3)
        sides = ["R", "L"] if m["side"] == "B" else [m["side"]]
        k = m["kind"]; d = m.get("deg", 5)
        e = w = dx = dy = 0.0
        env = _smooth(u / 0.25) * _smooth((1 - u) / 0.25)
        if k == "beat":            # one accent: up and settle
            e = -d * math.sin(math.pi * min(1, u * 1.6)) * (1 - u * 0.3)
        elif k == "reach":         # presents the (imaginary) document out to the side, holds
            e = d * _smooth(u / 0.3) * (1 - _smooth((u - 0.8) / 0.2))
        elif k == "wave":          # a small dismissive wave of the raised hand
            e = d * math.sin(2 * math.pi * m.get("n", 1.5) * u) * env; w = e * 0.5
        elif k == "sweep":         # a dismissive sweep out and back
            e = -d * math.sin(math.pi * u) * env
        elif k == "flick":         # a quick dismissive flick on a word
            e = -d * math.sin(math.pi * min(1, u * 2.2)) * (1 if u < 0.46 else 0)
        elif k == "lower":         # the index finger comes down slowly
            e = d * _smooth(u)
        elif k == "side":          # controlled side to side, each mark a stop
            marks = m["marks"]; rel = [(x - m["t0"]) / (m["t1"] - m["t0"]) for x in marks]
            tgt = [-d, d]
            e = 0.0
            for i, r in enumerate(rel):
                e = e + (tgt[i] - e) * _smooth((u - r + 0.06) / 0.14)
            e *= _smooth((1 - u) / 0.15)
        elif k == "across":        # one elegant motion across: from out to in
            e = -d * 0.5 + d * _smooth(u); e *= _smooth(u / 0.12) if u < 0.12 else 1.0
            e *= _smooth((1 - u) / 0.12) if u > 0.88 else 1.0
        elif k == "circle":        # a small circle of the hand (elbow and wrist out of phase)
            a = 2 * math.pi * m.get("n", 1) * u
            e = d * math.sin(a) * env; w = d * 0.8 * math.cos(a) * env
        elif k == "apart":         # hands move apart a touch more on the word
            e = -d * math.sin(math.pi * u)
        elif k == "tap":           # counting: the pointing hand steps to the next finger and taps
            dx = m["step"] * 3.2
            dy = -1.8 * math.sin(math.pi * min(1, u * 2))
        for s in sides:
            ee = e if (s == "R" or m["side"] != "B") else -e
            o = out.get(s, (0, 0, 0, 0))
            out[s] = (o[0] + ee, o[1] + w, o[2] + dx, o[3] + dy)
    # the counting hand stays where the last tap left it until the pose changes
    return out

def tap_rest(t, pose):
    last = None
    for m in ARM:
        if m["kind"] == "tap" and m["pose"] == pose and m["t1"] < t:
            last = m
    if last is None: return 0.0
    # only within the same stretch of this pose
    cur, since, _ = pose_at(t)
    if last["t1"] < t - since: return 0.0
    return last["step"] * 3.2

def nod_at(t):
    y = 0.0
    for tn, a in NODS:
        d = t - tn
        if 0 <= d < 0.7:
            y += a * (math.sin(math.pi * min(1, d / 0.22)) if d < 0.22 else -0.25 * math.sin(math.pi * (d - 0.22) / 0.48))
    return y

def sigh_at(t):
    y = 0.0
    for ts, a in SHOULD:
        d = t - ts
        if 0 <= d < 1.4:
            y += a * (_smooth(d / 0.35) if d < 0.35 else 1 - _smooth((d - 0.35) / 1.05))
    return y

def still_amount(t):
    s = 1.0
    for a, b in STILL:
        if a - 0.3 <= t <= b + 0.3:
            s = min(s, 0.15 + 0.85 * (1 - _smooth(min((t - (a - 0.3)) / 0.3, ((b + 0.3) - t) / 0.3))))
    return s

def gaze_at(t):
    gx = gy = 0.0
    for (tg, dx, dy, hold, go, back) in GAZE:
        d = t - tg
        if d < 0 or d > go + hold + back: continue
        u = _smooth(d / go) if d < go else (1.0 if d < go + hold else 1 - _smooth((d - go - hold) / back))
        gx += dx * u; gy += dy * u
    return gx, gy

def blink_at(t):
    for tb in BLINKS:
        d = int(round((t - tb) * FPS))
        if 0 <= d < 4: return [0.5, 1.0, 1.0, 0.45][d]
    return 0.0

def _noise(t, seed, rate):
    """smooth value noise in -1..1"""
    x = t * rate + seed * 17.13
    i = math.floor(x); f = x - i
    def h(n): return ((math.sin(n * 12.9898 + seed * 78.233) * 43758.5453) % 1.0) * 2 - 1
    u = f * f * (3 - 2 * f)
    return h(i) * (1 - u) + h(i + 1) * u

def camera_at(t):
    shot = "A"
    for tc, s in CUTS:
        if tc <= t: shot = s
    for (t0, t1, a, b) in PUSHES:
        if t0 <= t <= t1 + 0.001 and shot == a:
            return (a, b, _smooth((t - t0) / (t1 - t0)))
        if t > t1 and shot == a and not any(tc > t1 and tc <= t for tc, _ in CUTS):
            return (a, b, 1.0)
    return (shot, shot, 0.0)

def state(t):
    pose, since, prev = pose_at(t)
    still = still_amount(t)
    amp = 1.0 if t < SPEECH_END + 0.2 else 0.3
    st = {"t": t, "pose": pose, "pose_since": since, "pose_prev": prev, "arms": arm_offsets(t, pose),
          "tap_rest": tap_rest(t, pose)}
    face = {k: key(k, t) for k in ("brow_l", "brow_r", "brow_in", "arch", "smile", "smirk", "squint")}
    g = gaze_at(t)
    face["gaze"] = g
    face["lid"] = blink_at(t)
    st["face"] = face
    # head: idle drift (+-1 deg, a px or two), nods, chin dips; body: breathing, sighs, shrugs, chest lift, lean
    idle = still * amp
    st["tilt"] = 0.9 * _noise(t, 1, 0.35) * idle + key("tilt", t)
    st["head_dx"] = 0.8 * _noise(t, 2, 0.3) * idle
    st["head_dy"] = 0.6 * _noise(t, 3, 0.4) * idle + 1.6 * nod_at(t) + 2.2 * key("chin", t)
    st["breath"] = math.sin(2 * math.pi * t / 4.3) * (0.35 + 0.65 * still)
    st["body_dy"] = 1.4 * sigh_at(t) - 2.0 * key("shrug", t) - 1.2 * key("chest", t)
    st["shrug"] = key("shrug", t)
    st["lean"] = key("lean", t)
    st["cam"] = camera_at(t)
    st["gfx"] = [(name, t - a, b - t) for a, b, name in GFX if a <= t <= b]
    return st

if __name__ == "__main__":
    print(len(POSE), "pose changes,", len(ARM), "arm moves,", len(NODS), "nods,", len(BLINKS), "blinks,", len(GFX), "graphics")
    for tt in (0.5, 8.6, 9.7, 21.5, 40.5, 51.8, 95.6, 196.5, 222.0, 285.0, 291.8):
        s = state(tt)
        print(f"{tt:6.1f} pose={s['pose']:4s} cam={s['cam']} face={ {k: round(v, 2) if isinstance(v, float) else v for k, v in s['face'].items()} }")

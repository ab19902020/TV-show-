"""Timeline + performance for the whole film (clip time == film time: the original audio is used as is).

* W("in wings") ... start time of a phrase in the spoken words (all cuts and cues hang off the words).
* Lip sync: per speaker, per frame, from the aligned phones (face.viseme_events / face.track): shapes change one frame early,
  closures last >= 2 frames, the mouth is shut in silence. Loudness drives mouth size and small head nods.
* Keyed channels per character (look, brow, smile, turn, tilt, nod, lean, fwd, blinkx) with smoothstep ramps, plus a `pose`
  channel that names the drawing. Natural blinks every 2.2-5.5 s, never in sync between characters."""
import json, math, bisect, numpy as np, librosa
from collections import defaultdict
import face
from engine import seed

FPS = 30
PH = json.load(open("phones.json"))
DUR = PH["dur"]
N = int(math.ceil(DUR * FPS)) + 1
SPEAKERS = ("gary", "rooney", "micah", "shearer")

# ---------------------------------------------------------------- the spoken words
WL = [dict(w=w["w"], s=w["s"], e=w["e"], who=t["who"]) for t in PH["turns"] for w in t["words"]]


def W(phrase, nth=0, end=False):
    """start time (or end time) of a phrase of consecutive words, e.g. W("in wings"), W("fiftieth", end=True)"""
    ws = phrase.lower().split()
    hits = []
    for i in range(len(WL) - len(ws) + 1):
        if all(WL[i + k]["w"] == ws[k] for k in range(len(ws))): hits.append(i)
    if not hits: raise KeyError(phrase)
    i = hits[nth]
    return WL[i + len(ws) - 1]["e"] if end else WL[i]["s"]


# ---------------------------------------------------------------- speech: lip sync + loudness
VIS, ENV, TURNS = {}, {}, defaultdict(list)


def _loudness():
    y, sr = librosa.load("src/audio/rooney_micah_50_caps.mp3", sr=16000, mono=True)
    env = np.zeros(N, np.float32)
    h = sr / FPS
    for i in range(N):
        a, b = int(i * h - h / 2), int(i * h + h / 2)
        seg = y[max(0, a):max(0, b)]
        env[i] = float(np.sqrt(np.mean(seg ** 2))) if len(seg) else 0.0
    return env


def build_speech():
    loud = _loudness()
    for sp in SPEAKERS:
        evs = []
        env = np.zeros(N, np.float32)
        for t in PH["turns"]:
            if t["who"] != sp: continue
            evs += face.viseme_events(t["phones"], 0.0)
            a, b = t["words"][0]["s"], t["words"][-1]["e"]
            TURNS[sp].append((a, b))
            i0, i1 = int(a * FPS), min(N, int(b * FPS) + 1)
            env[i0:i1] = loud[i0:i1]
        VIS[sp] = face.track(evs, N, FPS)
        pk = np.percentile(env[env > 0], 95) if (env > 0).any() else 1.0
        ENV[sp] = np.clip(env / max(pk, 1e-4), 0, 1.4)


build_speech()


def speaking(sp, t):
    return any(a - 0.06 <= t <= b + 0.06 for a, b in TURNS.get(sp, []))


# ---------------------------------------------------------------- keys
K = defaultdict(lambda: defaultdict(list))
POSE = defaultdict(list)
DEFAULT = dict(lookx=0.0, looky=0.0, brow=0.0, smile=0.0, turn=0.0, tilt=0.0, nod=0.0, lean=0.0, fwd=0.0, blinkx=0.0, shrug=0.0)


def key(ch, chan, t, v, ramp=0.3):
    if chan == "look":
        key(ch, "lookx", t, v[0], ramp); key(ch, "looky", t, v[1], ramp); return
    K[ch][chan].append((t, float(v), max(0.01, ramp)))


def pose(ch, t, name):
    POSE[ch].append((t, name))


def pulse(ch, chan, t, v, up=0.12, hold=0.1, down=0.3):
    """a quick excursion and back (a nod, a flinch, a blink-hold)"""
    base = value(ch, chan, t - 0.01)
    key(ch, chan, t, v, up); key(ch, chan, t + up + hold, base, down)


def value(ch, chan, t):
    ks = K[ch].get(chan)
    v = DEFAULT.get(chan, 0.0)
    if not ks: return v
    for tk, vk, rk in ks:
        if t <= tk: break
        u = min(1.0, (t - tk) / rk)
        u = u * u * (3 - 2 * u)
        v = v + (vk - v) * u
    return v


def pose_at(ch, t, default=None):
    cur = default
    for tk, nm in POSE.get(ch, []):
        if t >= tk: cur = nm
        else: break
    return cur


def mode_start(ch, t):
    """start time of the pose entry that is current at t"""
    cur = 0.0
    for tk, nm in POSE.get(ch, []):
        if t >= tk: cur = tk
        else: break
    return cur


BALLOON_T0 = 40.55
APPEAR = {}                       # name -> time it pops into the party
CROWD_WINDOW = (22.05, 23.25)     # "about twenty of his guys": the crowd fills in over these words


def appear_time(key, default):
    return APPEAR.get(key, default)


def finalize():
    for ch in K:
        for chan in K[ch]: K[ch][chan].sort(key=lambda x: x[0])
    for ch in POSE: POSE[ch].sort(key=lambda x: x[0])


# ---------------------------------------------------------------- blinks
_BL = {}
EXTRA_BLINKS = defaultdict(list)


def blink_times(ch):
    if ch not in _BL:
        rng = np.random.default_rng(seed(ch))
        t, out = rng.uniform(0.3, 2.5), []
        while t < DUR + 5:
            out.append(t); t += rng.uniform(2.2, 5.5)
            if rng.random() < 0.12: out.append(t - rng.uniform(2.0, 2.2) + 0.28)       # an occasional double blink
        _BL[ch] = sorted(out)
    return _BL[ch]


def blink_at(ch, t):
    b = 0.0
    for tb in blink_times(ch) + EXTRA_BLINKS[ch]:
        d = t - tb
        if 0 <= d < 0.16: b = max(b, [0.55, 1.0, 1.0, 0.7, 0.3][min(4, int(d * FPS))])
    return b


# ---------------------------------------------------------------- the face / body state of a character at time t
PHASE = {}


def state(ch, t, speaker=None, amp_gain=1.0, idle=1.0, talks=True):
    """-> (face state for Drawing.patch, body dict). speaker: the voice track of this character (default = ch)"""
    sp = speaker or ch
    i = min(N - 1, max(0, int(round(t * FPS))))
    ph = PHASE.setdefault(ch, (seed(ch) % 1000) / 1000 * 6.28)
    st = {c: value(ch, c, t) for c in DEFAULT}
    vis, amp = "REST", 1.0
    if talks and sp in VIS and speaking(sp, t):
        vis = VIS[sp][i]
        amp = amp_gain * (0.65 + 0.55 * float(ENV[sp][i]))
    e = float(ENV[sp][i]) if (talks and sp in ENV) else 0.0
    e_prev = float(ENV[sp][max(0, i - 3)]) if (talks and sp in ENV) else 0.0
    nod = 1.4 * max(0.0, e - e_prev) + 0.45 * e
    drift_t = idle * (0.8 * math.sin(0.41 * t + ph) + 0.4 * math.sin(0.93 * t + 2 * ph))
    drift_n = idle * 0.4 * math.sin(0.57 * t + 1.3 * ph)
    tilt = st["tilt"] + drift_t + (1.0 * e * math.sin(1.7 * t + ph) if e > 0.05 else 0.0)
    out = dict(vis=vis, amp=amp, blink=max(blink_at(ch, t), st["blinkx"]), lookx=st["lookx"], looky=st["looky"],
               brow=st["brow"], smile=st["smile"], tilt=tilt, nod=st["nod"] + nod + drift_n, turn=st["turn"])
    body = dict(breath=0.0045 * math.sin(2 * math.pi * t / 3.7 + ph), lean=st["lean"] + 0.3 * math.sin(0.33 * t + ph),
                fwd=st["fwd"], shrug=st["shrug"])
    return out, body

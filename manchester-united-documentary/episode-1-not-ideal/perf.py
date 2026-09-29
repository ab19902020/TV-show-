"""Character performance for scenes 1-4.

Every character has channels over the episode timeline:
  look (x, y)  gaze in screen space (-1..1; x > 0 = to screen right, y > 0 = down)
  brow         -1 (stern / annoyed) .. 1 (raised)
  smile        -1 .. 1
  turn         head turn in screen space (-1..1)
  tilt, nod    extra head tilt (deg) and nod (% of head height)
  lean         body lean (deg) ; fwd = lean in towards the table (scale / drop)
  blinkx       forced lid closure (0..1) on top of the natural blinks
  pose         the drawing (e.g. Jason's action poses)
Keys: key(char, channel, t, value, ramp) - the value is reached `ramp` s after t (smoothstep); it holds until the
next key. Speech adds its own head motion (nods on stressed syllables, small tilts) and the lip sync; idle adds a
slow drift and breathing. Natural blinks every 2.2-5.5 s, never in sync between characters."""
import json, math, bisect, numpy as np, soundfile as sf
from collections import defaultdict
import face
from engine import seed

FPS = 30
TL = json.load(open("build/timeline.json"))
LINES = json.load(open("build/lines.json"))
M = TL["marks"]
N = int(math.ceil(TL["total"] * FPS)) + 1


def m(k, d=0.0):
    return M[k] + d


# ---------------------------------------------------------------- keys
K = defaultdict(lambda: defaultdict(list))
POSE = defaultdict(list)
DEFAULT = dict(lookx=0.0, looky=0.0, brow=0.0, smile=0.0, turn=0.0, tilt=0.0, nod=0.0, lean=0.0, fwd=0.0, blinkx=0.0)


def key(ch, chan, t, v, ramp=0.3):
    if chan == "look":
        key(ch, "lookx", t, v[0], ramp); key(ch, "looky", t, v[1], ramp); return
    K[ch][chan].append((t, float(v), max(0.01, ramp)))


def pose(ch, t, name):
    POSE[ch].append((t, name))


def pulse(ch, chan, t, v, up=0.15, hold=0.1, down=0.3):
    """a quick excursion and back (a nod, a blink-hold, a flinch)"""
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
    ps = POSE.get(ch)
    cur = default
    if ps:
        for tk, nm in ps:
            if t >= tk: cur = nm
            else: break
    return cur


def finalize():
    for ch in K:
        for chan in K[ch]:
            K[ch][chan].sort(key=lambda x: x[0])
    for ch in POSE:
        POSE[ch].sort(key=lambda x: x[0])


# ---------------------------------------------------------------- speech: lip sync + loudness
SPEAKERS = sorted({e["speaker"] for e in TL["events"]})
VIS = {}
ENV = {}
SPEAKING = defaultdict(list)       # speaker -> [(t0, t1, line id)]


def build_speech():
    for sp in SPEAKERS:
        evs = []
        env = np.zeros(N, np.float32)
        for e in TL["events"]:
            if e["speaker"] != sp: continue
            ln = LINES[e["src"]]
            evs += face.viseme_events(ln["phones"], e["t"])
            SPEAKING[sp].append((e["t"], e["t"] + e["dur"], e["id"]))
            y, sr = sf.read(f"build/lines/{e['src']}.wav")
            hop = sr // FPS
            i0 = int(round(e["t"] * FPS))
            for k in range(len(y) // hop):
                if 0 <= i0 + k < N:
                    env[i0 + k] = max(env[i0 + k], float(np.sqrt(np.mean(y[k * hop:(k + 1) * hop] ** 2))))
        VIS[sp] = face.track(evs, N, FPS)
        pk = np.percentile(env[env > 0], 95) if (env > 0).any() else 1.0
        ENV[sp] = np.clip(env / max(pk, 1e-4), 0, 1.4)


build_speech()


def speaking(sp, t):
    for a, b, lid in SPEAKING.get(sp, []):
        if a - 0.05 <= t <= b + 0.05: return lid
    return None


# ---------------------------------------------------------------- blinks
_BL = {}


def blink_times(ch):
    if ch not in _BL:
        rng = np.random.default_rng(seed(ch))
        t, out = rng.uniform(0.3, 2.5), []
        while t < TL["total"] + 5:
            out.append(t); t += rng.uniform(2.2, 5.5)
            if rng.random() < 0.12: out.append(t - rng.uniform(2.0, 2.2) + 0.28)    # occasional double blink
        _BL[ch] = sorted(out)
    return _BL[ch]


EXTRA_BLINKS = defaultdict(list)


def blink_at(ch, t):
    b = 0.0
    for tb in blink_times(ch) + EXTRA_BLINKS[ch]:
        d = t - tb
        if 0 <= d < 0.16:
            b = max(b, [0.55, 1.0, 1.0, 0.7, 0.3][min(4, int(d * FPS))])
    return b


# ---------------------------------------------------------------- the face / body state of a character at time t
PHASE = {}


def state(ch, t, speaker=None, amp_gain=1.0, idle=1.0):
    """face state dict for Drawing.image + body params. speaker: name in the voice tracks (default = ch)"""
    sp = speaker or ch
    i = min(N - 1, max(0, int(round(t * FPS))))
    ph = PHASE.setdefault(ch, (seed(ch) % 1000) / 1000 * 6.28)
    st = {c: value(ch, c, t) for c in DEFAULT}
    vis = "REST"
    amp = 1.0
    if sp in VIS and speaking(sp, t):
        vis = VIS[sp][i]
        e = float(ENV[sp][i])
        amp = amp_gain * (0.65 + 0.55 * e)
    # speech-driven head motion: a small nod that follows the loudness, a slow tilt drift
    e = float(ENV[sp][i]) if sp in ENV else 0.0
    e_prev = float(ENV[sp][max(0, i - 3)]) if sp in ENV else 0.0
    onset = max(0.0, e - e_prev)
    nod = 1.6 * onset + 0.5 * e
    drift_t = idle * (0.9 * math.sin(0.41 * t + ph) + 0.5 * math.sin(0.93 * t + 2 * ph))
    drift_n = idle * (0.4 * math.sin(0.57 * t + 1.3 * ph))
    tilt = st["tilt"] + drift_t + (1.2 * e * math.sin(1.7 * t + ph) if e > 0.05 else 0.0)
    out = dict(vis=vis, amp=amp, blink=max(blink_at(ch, t), st["blinkx"]), lookx=st["lookx"], looky=st["looky"],
               brow=st["brow"], smile=st["smile"], tilt=tilt, nod=st["nod"] + nod + drift_n, turn=st["turn"])
    body = dict(breath=0.0045 * math.sin(2 * math.pi * t / 3.7 + ph), lean=st["lean"] + 0.35 * math.sin(0.33 * t + ph),
                fwd=st["fwd"])
    return out, body

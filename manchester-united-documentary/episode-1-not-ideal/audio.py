"""The soundtrack for scenes 1-4: the locked dialogue plus room tone, foley, crowd, whistles and the corporate score.

No sound library is used: every effect and the music is synthesised here (numpy / scipy), deterministically.
  - dialogue: every line at its timeline position; the Glazers go through a laptop-speaker EQ; a touch of room
    reverb matching the location (boardroom, dressing room, pitch)
  - room tone per location: HVAC, office murmur, birds, corridor, dressing room, tunnel / stadium crowd
  - foley: footsteps, door, tablet taps, slide whooshes, video-call ring / connect / hang-up, boots, tape, magnet tap
  - crowd: murmur, anticipation swells on the corners, goal eruptions, referee whistles
  - music: a restrained 'prestige documentary' corporate theme (piano pulse + string pad + low pulse) from the top,
    hard-cut on "Who are we signing?"; a title sting; a low percussive pulse for the pre-match montage
python3 audio.py -> build/episode_audio.wav (48 kHz stereo, 24 bit)"""
import json, math, numpy as np, soundfile as sf
from scipy import signal
import perf, direction as D

SR = 48000
TL = perf.TL
TOTAL = TL["total"]
N = int(TOTAL * SR) + SR
m, T_, E_, W_ = perf.m, D.T, D.E, D.W
RNG = np.random.default_rng(2026)


def db(x): return 10 ** (x / 20)


def at_level(x, target_db):
    """scale x so the RMS of its active part (above -50 dB of its peak) is target_db dBFS"""
    x = np.asarray(x, np.float32)
    a = np.abs(x.mean(1) if x.ndim == 2 else x)
    thr = a.max() * db(-50)
    act = (x.mean(1) if x.ndim == 2 else x)[a > thr]
    r = np.sqrt(np.mean(act ** 2)) if len(act) else 1.0
    return x * (db(target_db) / max(r, 1e-9))


def bp(x, lo, hi, order=4):
    sos = signal.butter(order, [lo, hi], btype="band", fs=SR, output="sos"); return signal.sosfilt(sos, x)


def lp(x, f, order=4):
    sos = signal.butter(order, f, btype="low", fs=SR, output="sos"); return signal.sosfilt(sos, x)


def hp(x, f, order=4):
    sos = signal.butter(order, f, btype="high", fs=SR, output="sos"); return signal.sosfilt(sos, x)


def noise(n, color="white", rng=RNG):
    w = rng.standard_normal(n).astype(np.float32)
    if color == "white": return w
    if color == "pink":
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]; a = [1, -2.494956002, 2.017265875, -0.522189400]
        p = signal.lfilter(b, a, w); return (p / (np.std(p) + 1e-9)).astype(np.float32)
    if color == "brown":
        b = np.cumsum(w); b = hp(b, 20, 2); return (b / (np.std(b) + 1e-9)).astype(np.float32)


def env_ad(n, a, d):
    """attack / exponential decay envelope, lengths in samples"""
    e = np.ones(n, np.float32)
    ai = max(1, int(a))
    e[:ai] = np.linspace(0, 1, ai)
    t = np.arange(n - ai) / max(1.0, d)
    e[ai:] = np.exp(-t)
    return e


def fade(n, fin, fout):
    e = np.ones(n, np.float32)
    fi, fo = int(fin * SR), int(fout * SR)
    if fi: e[:fi] = np.linspace(0, 1, fi)
    if fo: e[-fo:] = np.minimum(e[-fo:], np.linspace(1, 0, fo))
    return e


class Bus:
    def __init__(self):
        self.L = np.zeros(N, np.float32); self.R = np.zeros(N, np.float32)

    def add(self, x, t, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= N: return
        x = np.asarray(x, np.float32)
        if x.ndim == 2:
            l, r = x[:, 0], x[:, 1]
        else:
            l = r = x
        gl, gr = gain * math.cos((pan + 1) * math.pi / 4) * 1.4142, gain * math.sin((pan + 1) * math.pi / 4) * 1.4142
        j0 = max(0, i); k0 = j0 - i
        n = min(len(l) - k0, N - j0)
        if n <= 0: return
        self.L[j0:j0 + n] += l[k0:k0 + n] * gl
        self.R[j0:j0 + n] += r[k0:k0 + n] * gr

    def st(self):
        return np.stack([self.L, self.R], 1)


def reverb_ir(seconds, damp=6000, predelay=0.01, seed=1):
    rng = np.random.default_rng(seed)
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)).astype(np.float32) * np.exp(-6.9 * t / seconds)[:, None]
    ir[:, 0] = lp(ir[:, 0], damp, 2); ir[:, 1] = lp(ir[:, 1], damp, 2)
    pd = int(predelay * SR)
    ir = np.concatenate([np.zeros((pd, 2), np.float32), ir])
    return ir / np.sqrt((ir ** 2).sum(0).mean())


def convolve_st(x, ir):
    if x.ndim == 1: x = np.stack([x, x], 1)
    out = np.stack([signal.fftconvolve(x[:, 0], ir[:, 0]), signal.fftconvolve(x[:, 1], ir[:, 1])], 1)
    return out.astype(np.float32)


# ---------------------------------------------------------------- locations over time
def loc_at(t):
    if t < m("corridor"): return "exterior"
    if t < m("board_wide"): return "corridor"
    if t < m("black"): return "boardroom"
    if t < m("s3"): return "title"
    if t < m("inserts"): return "stadium_ext"
    if t < m("dressing"): return "montage"
    if t < m("s4"): return "dressing"
    return "pitch"


# ---------------------------------------------------------------- dialogue
def dialogue(bus_dry, bus_wet):
    lines = {e["id"]: e for e in TL["events"]}
    rms_target = db(-20)
    for e in TL["events"]:
        y, sr = sf.read(f"build/lines/{e['src']}.wav", dtype="float32")
        if y.ndim > 1: y = y.mean(1)
        # level: loud parts to a common RMS per line
        act = y[np.abs(y) > 0.02]
        r = np.sqrt(np.mean(act ** 2)) if len(act) else 0.1
        g = rms_target / max(r, 1e-4)
        g = min(g, 0.89 / max(1e-4, np.abs(y).max()))
        y = y * g
        sp = e["speaker"]
        loc = loc_at(e["t"] + 0.1)
        if sp in ("joel", "avram"):
            # laptop speakers on the boardroom screen: band-limited, a little boxy, slightly compressed
            y = bp(y, 320, 4200, 4) * 1.4
            y = np.tanh(y * 2.2) / 2.2
            y = y + 0.25 * bp(y, 900, 1400, 2)
            bus_dry.add(y, e["t"], 0.9, pan=0.25)
            bus_wet.add(y, e["t"], 0.35)
            continue
        pan = {"carrick": -0.12, "jason": -0.05, "omar": 0.05, "jim": 0.12, "maguire": 0.1}.get(sp, 0.0)
        bus_dry.add(y, e["t"], 1.0, pan=pan)
        bus_wet.add(y, e["t"], 1.0)


# ---------------------------------------------------------------- room tones
def room_tones(bus):
    # exterior Carrington: wind + birds + distant ball strikes and coaches
    t0, t1 = 0.0, m("corridor") + 0.4
    n = int((t1 - t0) * SR)
    wind = lp(noise(n, "pink"), 700, 2) * (1 + 0.4 * np.sin(np.arange(n) / SR * 0.7))
    bus.add(at_level(wind, -44) * fade(n, 0.8, 0.4), t0, 1.0)
    for k in range(9):
        tb = t0 + 0.4 + RNG.uniform(0, t1 - t0 - 0.8)
        bus.add(at_level(bird_chirp(), -36), tb, 1.0, pan=RNG.uniform(-0.8, 0.8))
    for tb in (1.3, 2.9):
        bus.add(at_level(ball_strike(far=True), -38), tb, 1.0, pan=0.4)
    # corridor: HVAC + distant office, footsteps of passing staff
    t0, t1 = m("corridor"), m("board_wide") + 0.3
    n = int((t1 - t0) * SR)
    hv = lp(noise(n, "brown"), 300, 2) + np.sin(2 * np.pi * 60 * np.arange(n) / SR) * 0.08
    bus.add(at_level(hv, -47) * fade(n, 0.3, 0.3), t0)
    for k in range(6):
        bus.add(at_level(footstep(hard=True), -34), t0 + 0.25 + k * 0.33, 1.0, pan=-0.3 + 0.1 * k)
    # boardroom: HVAC, a distant office murmur, occasional chair creak / paper
    t0, t1 = m("board_wide") - 0.1, m("black")
    n = int((t1 - t0) * SR)
    hv = at_level(lp(noise(n, "brown"), 220, 2), -50) + at_level(lp(noise(n, "pink"), 2500, 2), -62)
    murmur = at_level(bp(noise(n, "pink"), 250, 1400, 2) * (1 + 0.5 * np.sin(np.arange(n) / SR * 0.31)), -56)
    bus.add((hv + murmur) * fade(n, 0.4, 0.2), t0)
    for tc in np.arange(t0 + 7, t1 - 5, 11.3):
        bus.add(at_level(chair_creak(), -42), tc + RNG.uniform(-2, 2), 1.0, pan=RNG.uniform(-0.6, 0.6))
    # stadium exterior: crowd building, distant chants
    t0, t1 = m("s3"), m("inserts") + 0.2
    n = int((t1 - t0) * SR)
    bus.add(at_level(crowd_bed(n, 0.35, far=True), -34) * fade(n, 0.5, 0.2), t0, 1.0)
    # montage: tunnel rumble
    t0, t1 = m("inserts"), m("dressing") + 0.1
    n = int((t1 - t0) * SR)
    bus.add(at_level(lp(crowd_bed(n, 0.5, far=True), 900, 2), -36) * fade(n, 0.1, 0.1), t0, 1.0)
    # dressing room: tiled room tone, distant showers, muffled crowd through the walls
    t0, t1 = m("dressing") - 0.05, m("s4") + 0.05
    n = int((t1 - t0) * SR)
    room = at_level(lp(noise(n, "brown"), 250, 2), -50) + at_level(hp(noise(n, "white"), 4000, 2), -64)
    thru = at_level(lp(crowd_bed(n, 0.5, far=True), 350, 2), -42)
    bus.add((room + thru) * fade(n, 0.05, 0.05), t0)
    # pitch: the stadium
    t0, t1 = m("s4"), m("whistle") + 0.45
    n = int((t1 - t0) * SR)
    swell = np.ones(n, np.float32)
    tt = np.arange(n) / SR + t0
    for tc, tg in ((m("corner1"), m("goal1_card")), (m("corner2"), m("goal2_card"))):
        swell += 0.8 * np.clip((tt - tc) / (tg - tc - 0.35), 0, 1) ** 2 * (tt < tg)
    bus.add(at_level(crowd_bed(n, 1.0), -26) * swell * fade(n, 0.02, 0.05), t0, 1.0)


def bird_chirp():
    n = int(RNG.uniform(0.25, 0.6) * SR)
    t = np.arange(n) / SR
    f0 = RNG.uniform(2800, 4200)
    out = np.zeros(n, np.float32)
    k = RNG.integers(2, 5)
    for i in range(k):
        s = int(i * n / k); e = min(n, s + int(0.07 * SR))
        tt = t[s:e] - t[s]
        f = f0 * (1 + 0.35 * np.sin(2 * np.pi * 14 * tt)) * (1 - 0.3 * tt / 0.07)
        ph = 2 * np.pi * np.cumsum(f) / SR
        out[s:e] += np.sin(ph) * np.sin(np.pi * tt / 0.07) ** 2
    return out


def ball_strike(far=False):
    n = int(0.25 * SR)
    x = noise(n) * env_ad(n, 20, 0.012 * SR)
    x = bp(x, 150, 2500, 2) + np.sin(2 * np.pi * 110 * np.arange(n) / SR) * env_ad(n, 10, 0.03 * SR) * 0.8
    if far: x = lp(x, 1500, 2)
    return x * 0.8


def footstep(hard=True):
    n = int(0.18 * SR)
    heel = noise(n) * env_ad(n, 8, 0.006 * SR)
    body = np.sin(2 * np.pi * 95 * np.arange(n) / SR) * env_ad(n, 20, 0.025 * SR)
    x = bp(heel, 800, 7000, 2) * 0.9 + body * 0.5
    if hard: x = x + hp(noise(n) * env_ad(n, 5, 0.02 * SR), 3000, 2) * 0.15
    return x


def stud_step():
    n = int(0.12 * SR)
    x = noise(n) * env_ad(n, 4, 0.004 * SR)
    x = hp(x, 2500, 2) * 1.2 + np.sin(2 * np.pi * 2300 * np.arange(n) / SR) * env_ad(n, 2, 0.008 * SR) * 0.3
    return x


def chair_creak():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    f = 330 + 90 * np.sin(2 * np.pi * 3 * t)
    x = signal.sawtooth(2 * np.pi * np.cumsum(f) / SR) * (np.sin(np.pi * t / 0.5) ** 2)
    x = bp(x, 400, 2400, 2) * (0.5 + 0.5 * (noise(n) > 0.5))
    return x * 0.3


def crowd_bed(n, level, far=False):
    """a large crowd: dense babble (formant-filtered noise) with slow swells"""
    rng = np.random.default_rng(int(level * 1000) + n % 997)
    base = noise(n, "pink", rng)
    x = np.zeros(n, np.float32)
    for lo, hi, g in ((150, 450, 0.9), (500, 1100, 0.8), (1200, 2600, 0.45), (2700, 5000, 0.12)):
        band = bp(base * (1 + 0.6 * lp(noise(n, "white", rng), 6, 1)), lo, hi, 2)
        x += band * g
    t = np.arange(n) / SR
    x *= (1 + 0.18 * np.sin(2 * np.pi * 0.11 * t + 1.0) + 0.12 * np.sin(2 * np.pi * 0.23 * t))
    if far: x = lp(x, 1800, 2)
    return x / (np.std(x) + 1e-9) * 0.06 * level


def whistle(dur=0.45, n_blasts=1, gap=0.18):
    out = []
    for b in range(n_blasts):
        d = dur if b < n_blasts - 1 or n_blasts == 1 else dur * 1.8
        n = int(d * SR)
        t = np.arange(n) / SR
        f = 3100 + 180 * np.sin(2 * np.pi * 34 * t) * (1 + 0.3 * np.sin(2 * np.pi * 5 * t))
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.25 * np.sin(4 * np.pi * np.cumsum(f) / SR)
        x = x * (1 + 0.1 * noise(n))
        e = np.minimum(1, t / 0.015) * np.minimum(1, (d - t) / 0.04)
        out.append(x * e * 0.5)
        out.append(np.zeros(int(gap * SR), np.float32))
    return np.concatenate(out).astype(np.float32)


def goal_roar(dur=3.4):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = crowd_bed(n, 1.0) * 3.2
    e = np.minimum(1, t / 0.12) * np.exp(-np.maximum(0, t - 0.6) / 1.6)
    return (x * e).astype(np.float32)


def click(hi=True):
    n = int(0.03 * SR)
    x = noise(n) * env_ad(n, 2, 0.002 * SR)
    return hp(x, 3000 if hi else 1200, 2) * 0.7


def whoosh(dur=0.45, up=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = noise(n, "pink")
    f = np.linspace(400, 3500, n) if up else np.linspace(3500, 400, n)
    out = np.zeros(n, np.float32)
    # time-varying band-pass by blocks
    blk = 1024
    for i in range(0, n, blk):
        fc = f[i]
        sos = signal.butter(2, [fc * 0.6, min(SR / 2 - 100, fc * 1.6)], btype="band", fs=SR, output="sos")
        out[i:i + blk] = signal.sosfilt(sos, x[i:i + blk])
    return out * np.sin(np.pi * t / dur) ** 2 * 0.5


def door_open():
    n = int(1.2 * SR)
    latch = click(False) * 1.5
    x = np.zeros(n, np.float32)
    x[:len(latch)] += latch
    x[int(0.08 * SR):int(0.08 * SR) + len(latch)] += latch * 0.7
    sw = lp(noise(n - int(0.15 * SR), "pink"), 500, 2) * np.sin(np.linspace(0, np.pi, n - int(0.15 * SR))) * 0.25
    x[int(0.15 * SR):] += sw
    return x


def teams_ring(count=2):
    """a friendly two-bar ringtone (marimba-ish): the call notification before the Glazers"""
    notes = [(659.25, 0.0), (783.99, 0.16), (987.77, 0.32), (783.99, 0.48), (1318.5, 0.64)]
    one = np.zeros(int(1.1 * SR), np.float32)
    for f, st in notes:
        n = int(0.5 * SR); t = np.arange(n) / SR
        x = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t * 30)) * np.exp(-t * 9)
        i = int(st * SR); one[i:i + n] += x[:len(one) - i]
    return np.concatenate([one] * count) * 0.35


def call_connect():
    out = np.zeros(int(0.5 * SR), np.float32)
    for f, st in ((523.25, 0.0), (783.99, 0.12)):
        n = int(0.3 * SR); t = np.arange(n) / SR
        i = int(st * SR); out[i:i + n] += np.sin(2 * np.pi * f * t) * np.exp(-t * 12) * 0.4
    return out


def call_end():
    out = np.zeros(int(0.6 * SR), np.float32)
    for f, st in ((659.25, 0.0), (392.0, 0.14)):
        n = int(0.35 * SR); t = np.arange(n) / SR
        i = int(st * SR); out[i:i + n] += np.sin(2 * np.pi * f * t) * np.exp(-t * 10) * 0.4
    return out


def tape_rip():
    n = int(0.35 * SR)
    x = noise(n) * (0.5 + 0.5 * (noise(n) > 0.8)) * np.linspace(1, 0.2, n)
    return bp(x, 1500, 7000, 2) * 0.5


def foley(bus):
    # Carrick's corridor walk: hard-floor steps, the jacket, the door
    t0 = m("walk"); stop = t0 + 3.4
    for k, ts in enumerate(np.arange(t0 + 0.1, stop, 0.52)):
        bus.add(at_level(footstep(), -30), ts, 1.0, pan=-0.05 + 0.05 * (k % 2))
    bus.add(at_level(bp(noise(int(0.3 * SR)), 500, 3000, 2) * np.hanning(int(0.3 * SR)), -38), stop + 0.45, 1.0)    # jacket
    bus.add(at_level(lp(noise(int(0.8 * SR), "pink"), 800, 2) * np.hanning(int(0.8 * SR)), -40), stop + 1.3, 1.0)   # breath
    bus.add(at_level(door_open(), -32), t0 + 5.45, 1.0)
    # tablet taps: nothing; nothing; then it works
    for tt in (m("tap1") + 0.25, m("tap1") + 0.95, m("ck_watches") + 0.6, m("tap_ok") - 0.15):
        bus.add(at_level(click(), -30), tt, 1.0, pan=-0.1)
    # slide transitions (the presentation click + whoosh)
    for tt in (m("tap_ok") + 0.05, W_("js_well", "clarity") - 0.05, T_("js_alignment") - 0.05, T_("js_sustain") - 0.05,
               T_("js_agility") - 0.05, m("cutaway_pres") + 0.05, m("sale_graphic"), m("scroll1"), m("scroll2")):
        bus.add(at_level(click(), -33), tt, 1.0, pan=0.2)
        bus.add(at_level(whoosh(0.35), -36), tt + 0.01, 1.0, pan=0.25)
    # scrolling the absurd objectives list
    for tt in np.arange(m("scroll1") + 0.2, m("scroll1") + 1.8, 0.12):
        bus.add(at_level(click(), -40), tt, 1.0, pan=0.2)
    # notebook closing
    bus.add(at_level(bp(noise(int(0.25 * SR)), 300, 3000, 2) * np.hanning(int(0.25 * SR)), -36), m("notebook") + 0.2, 1.0)
    # the Glazers: notification ring, connect, volume blips, hang-up
    bus.add(at_level(teams_ring(1), -26), m("chime"), 1.0, pan=0.25)
    bus.add(at_level(call_connect(), -28), m("screen_on") - 0.05, 1.0, pan=0.25)
    for k in range(3):
        bus.add(at_level(click(), -34), m("volume") + 0.15 + k * 0.18, 1.0, pan=0.25)
    bus.add(at_level(call_end(), -28), m("call_ends") - 0.05, 1.0, pan=0.25)
    # Jim closes his folder
    bus.add(at_level(lp(noise(int(0.2 * SR)), 1500, 2) * env_ad(int(0.2 * SR), 30, 0.03 * SR), -30), m("folder") + 0.2, 1.0, pan=0.2)
    # the pre-match inserts: boots on a bench, tape, gloves; studs on the floor in the tunnel
    ins = m("inserts")
    bus.add(at_level(stud_step(), -28), ins + 0.1, 1.0); bus.add(at_level(stud_step(), -30), ins + 0.42, 1.0)
    bus.add(at_level(tape_rip(), -28), ins + 0.95, 1.0)
    for k in range(6):
        bus.add(at_level(stud_step(), -31), ins + 1.75 + k * 0.21, 1.0, pan=-0.2 + 0.08 * k)
    # the tactics board: marker tap / magnet click on the two words
    for w in ("set", "pieces"):
        bus.add(at_level(click(False), -26), W_("ck_set_pieces", w) + 0.01, 1.0, pan=-0.3)
    # the match: whistles, corners (ball strike), goals
    bus.add(at_level(whistle(0.35, 1), -24), m("s4") + 0.25, 1.0, pan=0.2)
    for tc, tg in ((m("corner1"), m("goal1_card")), (m("corner2"), m("goal2_card"))):
        bus.add(at_level(ball_strike(), -24), tc + 0.35, 1.0)
        bus.add(at_level(ball_strike(), -26), tg - 0.62, 1.0)
        bus.add(at_level(goal_roar(), -15), tg - 0.45, 1.0)
    bus.add(at_level(whistle(0.32, 3, 0.16), -21), m("whistle") - 0.25, 1.0, pan=0.15)


# ---------------------------------------------------------------- music
def piano_note(f, dur, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for h, (g, d) in enumerate([(1.0, 1.6), (0.45, 1.1), (0.22, 0.8), (0.12, 0.6), (0.06, 0.4)], 1):
        x += g * np.sin(2 * np.pi * f * h * t * (1 + 0.0004 * h * h)) * np.exp(-t * (1.0 + 0.9 * h) / d)
    x *= np.minimum(1, t / 0.004)
    return x * vel * 0.25


def pad_chord(freqs, dur, attack=1.2, release=1.5):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    for f in freqs:
        for det in (-0.12, 0.0, 0.13):
            ff = f * (2 ** (det / 12))
            x += signal.sawtooth(2 * np.pi * ff * t + RNG.uniform(0, 6.28)).astype(np.float32) * 0.18
    x = lp(x, 1400, 2)
    e = np.minimum(1, t / attack) * np.minimum(1, (dur - t) / release)
    return (x * e).astype(np.float32)


def note(nm):
    names = {"C": -9, "C#": -8, "D": -7, "D#": -6, "E": -5, "F": -4, "F#": -3, "G": -2, "G#": -1, "A": 0, "A#": 1, "B": 2}
    p, o = nm[:-1], int(nm[-1])
    return 440.0 * 2 ** ((names[p] + 12 * (o - 4)) / 12)


def corporate_theme(dur, key_bars=None):
    """earnest 'prestige documentary' corporate underscore: 80 bpm piano 8ths over a string pad, soft kick pulse.
    progression (bars of 4 beats): Am - F - C - G, repeated; builds a little over time."""
    bpm = 80; beat = 60 / bpm; bar = 4 * beat
    prog = [("A2", ["A3", "C4", "E4"], ["A4", "E5", "C5", "E5"]), ("F2", ["F3", "A3", "C4"], ["A4", "F5", "C5", "F5"]),
            ("C3", ["C4", "E4", "G4"], ["G4", "E5", "C5", "E5"]), ("G2", ["G3", "B3", "D4"], ["G4", "D5", "B4", "D5"])]
    n = int(dur * SR) + SR * 3
    L = np.zeros(n, np.float32); R = np.zeros(n, np.float32)
    nb = int(math.ceil(dur / bar)) + 1
    for b in range(nb):
        bass, chord, arp = prog[b % 4]
        t0 = b * bar
        i0 = int(t0 * SR)
        if i0 >= n: break
        build = min(1.0, 0.45 + b / 10)
        pad = pad_chord([note(x) for x in chord], bar + 1.6) * 0.5 * build
        j = min(n, i0 + len(pad)); L[i0:j] += pad[:j - i0] * 0.9; R[i0:j] += pad[:j - i0]
        bn = piano_note(note(bass), bar + 0.5, 0.9) * 0.9
        j = min(n, i0 + len(bn)); L[i0:j] += bn[:j - i0]; R[i0:j] += bn[:j - i0]
        for k in range(8):
            f = note(arp[k % 4])
            if k >= 4 and b % 2 == 1: f *= 2 ** (2 / 12) if k == 6 else 1
            x = piano_note(f, 1.4, 0.55 + 0.12 * (k % 2 == 0))
            i = int((t0 + k * beat / 2) * SR)
            if i >= n: continue
            j = min(n, i + len(x))
            pan = 0.3 * math.sin(k)
            L[i:j] += x[:j - i] * (1 - pan) * 0.8; R[i:j] += x[:j - i] * (1 + pan) * 0.8
        if b >= 2:                                         # a soft low pulse joins
            for k in range(4):
                kn = int(0.25 * SR); tt = np.arange(kn) / SR
                kick = np.sin(2 * np.pi * (55 + 40 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9) * 0.35 * build
                i = int((t0 + k * beat) * SR); j = min(n, i + kn)
                if i < n: L[i:j] += kick[:j - i]; R[i:j] += kick[:j - i]
    ir = reverb_ir(2.2, 5000, 0.02, 7)
    wet = convolve_st(np.stack([L, R], 1), ir)[:n]
    out = np.stack([L, R], 1) * 0.8 + wet * 0.22
    return out[:int(dur * SR)]


def title_sting():
    n = int(4.0 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (38 + 30 * np.exp(-t * 6)) * t) * np.exp(-t * 1.4) * 0.9
    hit = bp(noise(n), 200, 5000, 2) * np.exp(-t * 7) * 0.25
    chord = pad_chord([note("A2"), note("E3"), note("A3"), note("C4")], 4.0, 0.02, 2.5) * 0.5
    x = boom + hit + chord
    rev = convolve_st(x, reverb_ir(3.0, 4000, 0.03, 3))[:n]
    riser = np.zeros(n, np.float32)
    return np.stack([x, x], 1) * 0.7 + rev * 0.35, whoosh(0.9, True) * 0.9


def montage_pulse(dur):
    """pre-match: low drum pulse + drone (no melody), 100 bpm"""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    beat = 60 / 100
    for k in range(int(dur / beat) + 1):
        kn = int(0.3 * SR); tt = np.arange(kn) / SR
        kick = np.sin(2 * np.pi * (50 + 60 * np.exp(-tt * 35)) * tt) * np.exp(-tt * 8)
        i = int(k * beat * SR); j = min(n, i + kn)
        x[i:j] += kick[:j - i] * (0.8 if k % 2 == 0 else 0.5)
        if k % 2 == 1:
            sn = bp(noise(int(0.12 * SR)), 1500, 6000, 2) * np.exp(-np.arange(int(0.12 * SR)) / SR * 30) * 0.12
            j = min(n, i + len(sn)); x[i:j] += sn[:j - i]
    drone = lp(signal.sawtooth(2 * np.pi * 55 * t).astype(np.float32) + signal.sawtooth(2 * np.pi * 82.5 * t).astype(np.float32), 300, 2) * 0.12
    return (x + drone) * fade(n, 0.3, 0.2)


def music(bus):
    # the corporate theme: from the top, restrained; ducks under dialogue; HARD CUT at "Who are we signing?"
    cut = m("music_cut")
    th = corporate_theme(cut + 0.5)
    ncut = int(cut * SR)
    th = th[:ncut]
    th[-int(0.012 * SR):] *= np.linspace(1, 0, int(0.012 * SR))[:, None]
    th *= fade(len(th), 1.5, 0)[:, None]
    # ducking under dialogue
    duck = np.ones(len(th), np.float32)
    for e in TL["events"]:
        a, b = int((e["t"] - 0.15) * SR), int((e["t"] + e["dur"] + 0.25) * SR)
        if a < len(duck): duck[max(0, a):min(len(duck), b)] = db(-7)
    duck = lp(duck, 3, 1).astype(np.float32)
    bus.add(at_level(th, -27) * duck[:, None], 0.0, 1.0)
    # title sting
    st, rs = title_sting()
    bus.add(at_level(rs, -26), m("title") - 0.85, 1.0)
    bus.add(at_level(st, -17), m("title"), 1.0)
    # pre-match montage pulse (stadium exterior -> inserts), out as the dressing room starts
    d0, d1 = m("s3") + 0.3, m("dressing") + 0.3
    bus.add(at_level(montage_pulse(d1 - d0), -27), d0, 1.0)


def main():
    dry, wet, fx, mus = Bus(), Bus(), Bus(), Bus()
    dialogue(dry, wet)
    room_tones(fx)
    foley(fx)
    music(mus)
    # dialogue reverb by location: boardroom small, dressing room tiled, pitch open
    w = wet.st()
    out_w = np.zeros_like(w)
    for (a, b, sec, damp, g) in ((0, m("black"), 0.45, 5000, 0.10), (m("dressing") - 0.1, m("s4"), 0.9, 6000, 0.16),
                                 (m("s4"), TOTAL, 1.6, 4000, 0.18)):
        ia, ib = int(a * SR), int(b * SR)
        seg = w[ia:ib]
        if not len(seg): continue
        r = convolve_st(seg, reverb_ir(sec, damp, 0.012, 5))
        j = min(len(out_w), ia + len(r))
        out_w[ia:j] += r[:j - ia] * g
    mix = (dry.st() + out_w + fx.st() + mus.st()) * db(4)
    # limiter: smooth gain reduction above -3 dBFS, hard ceiling -1 dBFS
    lvl = np.maximum(np.abs(mix).max(1), 1e-6)
    env = np.maximum.accumulate(lvl[::-1])[::-1] if False else lvl
    k = int(0.005 * SR)
    peak = signal.convolve(lvl, np.ones(k) / k, mode="same")
    peak = np.maximum(peak, lvl * 0.7)
    gr = np.minimum(1.0, db(-3) / np.maximum(peak, 1e-6))
    gr = lp(gr, 30, 1).astype(np.float32)
    mix = mix * np.minimum(1.0, gr)[:, None]
    mix = np.clip(mix, -db(-1), db(-1))
    mix = mix[:int(TOTAL * SR)]
    sf.write("build/episode_audio.wav", mix.astype(np.float32), SR, subtype="PCM_24")
    print("audio", mix.shape, "peak", np.abs(mix).max(), "rms dB", 20 * np.log10(np.sqrt(np.mean(mix ** 2))))


if __name__ == "__main__":
    main()

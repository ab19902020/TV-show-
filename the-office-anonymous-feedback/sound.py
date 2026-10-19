"""Sound: the dialogue cut from the three recordings, plus a procedural office soundscape. No music, no laughs.

Everything is generated here from noise and tones, so it is all editable: the fluorescent/mains hum, the air
conditioning, distant keyboards, a phone ringing two desks away, paper, pen taps and scribbles, carpet footsteps for
the people walking past, a chair creak, Tim's exhale and the car park outside.
"""
import json, numpy as np, librosa, soundfile as sf
from scipy import signal

SR = 48000
rng = np.random.default_rng(7)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)


def db(v):
    return 10 ** (v / 20)


def env(n, a, r):
    e = np.ones(n)
    na, nr = int(a * SR), int(r * SR)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def pink(n):
    w = rng.standard_normal(n)
    b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
    return signal.lfilter(b, a, w) / 0.1


# ------------------------------------------------------------------ beds
def room_tone(dur, kind="office"):
    n = int(dur * SR)
    t = np.arange(n) / SR
    air = lp(pink(n), 900) * db(-46)
    hum = sum(db(l) * np.sin(2 * np.pi * f * t + p) for f, l, p in
              [(50, -54, 0), (100, -50, 1.3), (150, -60, 0.4), (200, -64, 2.1)])
    # fluorescent ballast: faint buzzing at 100 Hz with harmonics, slowly breathing
    buzz = bp(np.sign(np.sin(2 * np.pi * 100 * t)) * 0.3, 900, 3000) * db(-63) * (1 + 0.2 * np.sin(2 * np.pi * 0.13 * t))
    x = air + hum + buzz
    if kind == "interview":
        x = air * 0.7 + hum * 0.8
    return np.stack([x, np.roll(x, 211) * 0.97 + lp(pink(n), 700) * db(-52)], 1)


def car_park(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    traffic = lp(pink(n), 350) * db(-30) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.21 * t + 1))
    wind = bp(pink(n), 200, 1500) * db(-44) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.09 * t) ** 2)
    x = traffic + wind
    # a bird, far away
    for t0 in (0.55, 0.78, 1.6):
        m = int(0.09 * SR)
        tt = np.arange(m) / SR
        chirp = np.sin(2 * np.pi * (3800 + 1400 * np.sin(2 * np.pi * 22 * tt)) * tt) * np.hanning(m) * db(-44)
        i = int(t0 * SR)
        x[i:i + m] += chirp[: max(0, min(m, n - i))]
    return np.stack([x, np.roll(x, 300)], 1)


# ------------------------------------------------------------------ spot effects (mono)
def key_click(level=-30):
    m = int(0.035 * SR)
    tr = rng.standard_normal(m) * np.exp(-np.arange(m) / (0.003 * SR))
    body = bp(tr, 1800 + rng.uniform(-400, 600), 5200) + 0.5 * bp(tr, 400, 900)
    return body * db(level + rng.uniform(-3, 2))


def typing(dur, rate=7.5, level=-30, distant=False):
    n = int(dur * SR)
    x = np.zeros(n)
    t = 0.0
    while t < dur - 0.05:
        c = key_click(level)
        if rng.random() < 0.08:  # space bar: heavier
            c = lp(c, 1500) * 2
        i = int(t * SR)
        x[i:i + len(c)] += c[: n - i]
        t += rng.gamma(4, 1 / (rate * 4))
        if rng.random() < 0.06:
            t += rng.uniform(0.25, 0.7)
    if distant:
        x = lp(x, 2600)
    return x


def paper(dur=0.45, level=-28):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    crk = np.zeros(n)
    for _ in range(int(dur * 60)):
        i = rng.integers(0, n - 200)
        crk[i:i + 200] += rng.standard_normal(200) * np.exp(-np.arange(200) / 40) * rng.uniform(0.5, 2)
    x = bp(noise, 2500, 9000) * 0.25 + bp(crk, 1500, 8000)
    am = np.abs(lp(rng.standard_normal(n), 30)) * 6
    return x * am * env(n, 0.04, 0.12) * db(level)


def pen_tap(level=-24):
    m = int(0.09 * SR)
    t = np.arange(m) / SR
    tok = np.sin(2 * np.pi * 820 * t) * np.exp(-t / 0.012) + 0.5 * np.sin(2 * np.pi * 2300 * t) * np.exp(-t / 0.005)
    tok += bp(rng.standard_normal(m), 2000, 7000) * np.exp(-t / 0.002) * 0.6
    return tok * db(level)


def scribble(dur, level=-33):
    n = int(dur * SR)
    t = np.arange(n) / SR
    strokes = (0.5 + 0.5 * np.sin(2 * np.pi * (7 + 3 * np.sin(2 * np.pi * 0.7 * t)) * t)) ** 3
    gaps = (lp(rng.standard_normal(n), 3) > -0.02).astype(float)
    x = bp(rng.standard_normal(n), 2800, 8500) * strokes * lp(gaps, 40)
    return x * env(n, 0.03, 0.05) * db(level)


def footstep(level=-34):
    m = int(0.16 * SR)
    t = np.arange(m) / SR
    thump = np.sin(2 * np.pi * 85 * t) * np.exp(-t / 0.025)
    scuff = lp(rng.standard_normal(m), 900) * np.exp(-t / 0.03) * 0.6
    return (thump + scuff) * db(level + rng.uniform(-2, 2))


def steps(times, level=-34):
    """footsteps at the given times (seconds, relative)"""
    n = int((max(times) + 0.3) * SR)
    x = np.zeros(n)
    for tt in times:
        f = footstep(level)
        i = int(tt * SR)
        x[i:i + len(f)] += f[: n - i]
    return x


def phone_ring(rings=2, level=-36):
    """a UK office phone, two desks away: 400/450 Hz double ring"""
    cyc = 3.0
    n = int(rings * cyc * SR)
    t = np.arange(n) / SR
    tone = (np.sin(2 * np.pi * 400 * t) + np.sin(2 * np.pi * 450 * t)) * 0.5
    tone = np.sign(tone) * np.abs(tone) ** 0.6  # a bit of bell grit
    ph = t % cyc
    gate = ((ph < 0.4) | ((ph > 0.6) & (ph < 1.0))).astype(float)
    gate = lp(gate, 60)
    x = lp(bp(tone * gate, 300, 3500), 2200) * db(level)
    return x


def creak(level=-38):
    m = int(0.32 * SR)
    t = np.arange(m) / SR
    f = 260 + 120 * np.sin(2 * np.pi * 2.2 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    pulses = (np.sin(ph) > 0.92).astype(float)
    x = bp(pulses, 300, 2400) * np.hanning(m)
    return x * db(level + 12)


def exhale(level=-36):
    m = int(0.55 * SR)
    t = np.arange(m) / SR
    e = np.minimum(t / 0.06, 1) * np.exp(-np.maximum(t - 0.06, 0) / 0.16)
    x = bp(rng.standard_normal(m), 350, 2400) * e
    return x * db(level)


# ------------------------------------------------------------------ dialogue
def load_lines():
    P = json.load(open("phones.json"))
    rec = {}
    for who in ("brent", "gareth", "tim"):
        y, _ = librosa.load(f"src/{who}.mp3", sr=SR, mono=True)
        rec[who] = y
    lines = {}
    for lid, L in P.items():
        y = rec[L["who"]]
        seg = y[int(L["a0"] * SR):int(L["a1"] * SR)].copy()
        f = int(0.012 * SR)
        seg[:f] *= np.linspace(0, 1, f)
        seg[-f:] *= np.linspace(1, 0, f)
        lines[lid] = seg
    # one loudness per character (active speech RMS), so the three voices sit at the same level
    for who, target in (("brent", -21.0), ("gareth", -21.5), ("tim", -21.5)):
        segs = [lines[k] for k, L in P.items() if L["who"] == who]
        cat = np.concatenate(segs)
        fr = librosa.util.frame(cat, frame_length=2048, hop_length=1024)
        r = np.sqrt((fr ** 2).mean(0))
        act = r[r > r.max() * 0.08]
        g = db(target) / np.sqrt((act ** 2).mean())
        for k, L in P.items():
            if L["who"] == who:
                lines[k] = lines[k] * g
    return P, lines


def room_ir(rt=0.28, wet=-20):
    n = int(rt * SR)
    t = np.arange(n) / SR
    ir = rng.standard_normal(n) * np.exp(-t / (rt / 6.9))
    ir = lp(ir, 3500)
    ir[: int(0.006 * SR)] = 0
    ir /= np.sqrt((ir ** 2).sum())
    return ir * db(wet)


# ------------------------------------------------------------------ the mix
def mix(out="build/mix.wav"):
    import direction as D
    n = int(D.TOTAL * SR)
    amb = np.zeros((n, 2))
    dia = np.zeros(n)
    sfx = np.zeros((n, 2))

    def put(buf, t, x, pan=0.0, gain=1.0):
        i = int(t * SR)
        if i >= n:
            return
        x = x[: n - i] * gain
        if buf.ndim == 1:
            buf[i:i + len(x)] += x
        else:
            l, r = np.sqrt(0.5 * (1 - pan)), np.sqrt(0.5 * (1 + pan))
            buf[i:i + len(x), 0] += x * l * 1.41
            buf[i:i + len(x), 1] += x * r * 1.41

    # beds follow the cuts: car park, office floor, the quieter interview room
    def span_mask(sets_wanted):
        m = np.zeros(n)
        for s in D.SHOTS:
            if s["set"] in sets_wanted:
                m[int(s["t0"] * SR):int(s["t1"] * SR)] = 1
        k = int(0.012 * SR)
        return np.convolve(m, np.ones(k) / k, mode="same")
    office = room_tone(D.TOTAL, "office")
    inter = room_tone(D.TOTAL, "interview")
    cp = car_park(D.TOTAL)
    mo, mi, mc = span_mask({"desks", "tim", "gareth", "wide"}), span_mask({"interview"}), span_mask({"carpark"})
    amb += office * mo[:, None] * db(3) + inter * mi[:, None] * db(2) + cp * mc[:, None]
    # the rest of the office, off screen: keyboards, a drawer, papers - distant, never busy
    bg = np.zeros(n)
    t = 3.2
    r = np.random.default_rng(31)
    while t < D.END:
        kind = r.random()
        if kind < 0.7:
            d = r.uniform(0.8, 2.6)
            x = typing(d, rate=r.uniform(5, 8), level=-44, distant=True)
        elif kind < 0.85:
            x = lp(paper(0.4, -44), 3000)
        else:
            x = lp(creak(-50), 2000)
        put(bg, t, x)
        t += r.uniform(1.5, 4.5)
    amb += np.stack([bg * 0.9, np.roll(bg, 400) * 0.7], 1) * mo[:, None]

    for t, kind, a in D.EVENTS:
        if kind == "typing":
            put(sfx, t, typing(a["dur"], rate=8, level=-46 if a["distant"] else -31, distant=a["distant"]), pan=-0.3)
        elif kind == "phone":
            put(sfx, t, phone_ring(2, -39)[: int(4.6 * SR)] * env(int(4.6 * SR), 0.0, 0.03), pan=0.5)
        elif kind == "creak":
            put(sfx, t, creak(-40), pan=0.3)
        elif kind == "pen_tap":
            put(sfx, t, pen_tap(-27), pan=0.25)
        elif kind == "paper":
            put(sfx, t, paper(a["dur"], -29), pan=0.35)
        elif kind == "write":
            put(sfx, t, scribble(a["dur"], -35), pan=0.2)
        elif kind == "exhale":
            put(sfx, t, exhale(-38), pan=-0.3)
    # footsteps of the people walking past
    for wk in D.EXTRAS:
        stride = 0.42 * wk["h"]
        total = abs(wk["x1"] - wk["x0"])
        times = [wk["t0"] + k * stride / wk["speed"] for k in range(int(total / stride) + 1)]
        times = [tt for tt in times if any(s["set"] == wk["set"] and s["t0"] <= tt < s["t1"] for s in D.SHOTS)]
        if not times:
            continue
        lvl = -47 + 12 * np.log10(wk["h"] / 300)
        if wk["set"] == "carpark":
            lvl -= 2
        x = steps([tt - times[0] for tt in times], lvl)
        if wk["set"] == "carpark":
            x = x + hp(x, 1500) * 2
        put(sfx, times[0], x, pan=0.0)

    # dialogue, with a touch of the room
    P, lines = load_lines()
    ir_office, ir_int = room_ir(0.3, -21), room_ir(0.22, -27)
    trim = {"G03": 4.0}           # Gareth's quiet "Number four. Tim." sits a little under the others
    for lid, t0 in D.LINES.items():
        x = hp(lines[lid], 80) * db(trim.get(lid, 0.0))
        s = next(s for s in D.SHOTS if s["t0"] <= t0 + 0.4 < s["t1"])
        ir = ir_int if s["set"] == "interview" else ir_office
        wet = signal.fftconvolve(x, ir)[: len(x) + int(0.3 * SR)]
        y = np.zeros(len(wet))
        y[: len(x)] += x
        y += wet
        put(dia, t0, y)
    mixd = (amb + sfx + dia[:, None]) * db(3.0)
    # hard cut to black: sound stops with the picture
    e = int(D.END * SR)
    f = int(0.02 * SR)
    mixd[e - f:e] *= np.linspace(1, 0, f)[:, None]
    mixd[e:] = 0
    # soft limit at -1 dBFS
    peak = db(-1.5)
    mixd = np.where(np.abs(mixd) < peak * 0.8, mixd, np.sign(mixd) * (peak * 0.8 + peak * 0.2 * np.tanh(
        (np.abs(mixd) - peak * 0.8) / (peak * 0.2))))
    sf.write(out, mixd.astype(np.float32), SR, subtype="PCM_24")
    print("mix", out, len(mixd) / SR, "s, peak", 20 * np.log10(np.abs(mixd).max() + 1e-9))
    return out


if __name__ == "__main__":
    mix()

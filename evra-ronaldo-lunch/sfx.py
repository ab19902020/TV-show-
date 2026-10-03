"""Sound effects, all synthesised (numpy / scipy): no samples, no libraries, deterministic.
Every function returns a mono float32 array at 48 kHz with its peak at 1.0 (audio.py sets the level and the pan)."""
import numpy as np
from scipy import signal

SR = 48000


def db(x): return 10 ** (x / 20)


def T(d): return np.arange(int(d * SR), dtype=np.float64) / SR


def rng(seed): return np.random.default_rng(seed)


def noise(n, color="white", seed=1):
    w = rng(seed).standard_normal(n)
    if color == "pink":
        b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]; a = [1, -2.494956002, 2.017265875, -0.522189400]
        w = signal.lfilter(b, a, w); w /= np.std(w) + 1e-9
    return w


def bp(x, lo, hi, order=2):
    return signal.sosfilt(signal.butter(order, [lo, min(hi, SR / 2 - 200)], "band", fs=SR, output="sos"), x)


def lp(x, f, order=2): return signal.sosfilt(signal.butter(order, f, "low", fs=SR, output="sos"), x)


def hp(x, f, order=2): return signal.sosfilt(signal.butter(order, f, "high", fs=SR, output="sos"), x)


def ad(n, a, d):
    """attack a (s, linear) then exponential decay with time constant d (s)"""
    t = np.arange(n) / SR
    e = np.exp(-np.maximum(t - a, 0) / max(d, 1e-4))
    ai = max(1, int(a * SR)); e[:ai] = np.minimum(e[:ai], np.linspace(0, 1, ai))
    return e


def norm(x, peak=1.0):
    x = np.asarray(x, np.float64)
    return (x / (np.abs(x).max() + 1e-12) * peak).astype(np.float32)


def sweep(f0, f1, dur, shape="exp"):
    t = T(dur)
    f = f0 * (f1 / f0) ** (t / dur) if shape == "exp" else f0 + (f1 - f0) * t / dur
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def fade_edges(x, a=.004, b=.01):
    x = x.copy(); ia, ib = int(a * SR), int(b * SR)
    if ia: x[:ia] *= np.linspace(0, 1, ia)
    if ib: x[-ib:] *= np.linspace(1, 0, ib)
    return x


def swept_noise(dur, f0, f1, q=1.6, seed=3):
    """band-passed noise whose centre frequency moves f0 -> f1 (whooshes, hisses)"""
    n = int(dur * SR); x = noise(n, "pink", seed); out = np.zeros(n); blk = 1024
    fc = np.geomspace(f0, f1, n // blk + 1)
    for k, i in enumerate(range(0, n, blk)):
        f = fc[k]; sos = signal.butter(2, [f / q, min(f * q, SR / 2 - 300)], "band", fs=SR, output="sos")
        out[i:i + blk] = signal.sosfilt(sos, x[i:i + blk])
    return out


# ------------------------------------------------------------------ whooshes, pops, magic
def whoosh(dur=.4, up=True, lo=350, hi=4200, seed=3):
    x = swept_noise(dur, lo, hi, seed=seed) if up else swept_noise(dur, hi, lo, seed=seed)
    return norm(x * np.sin(np.pi * T(dur) / dur) ** 1.6)


def whip():
    """a whip-pan: a quick fat whoosh"""
    return whoosh(.3, True, 500, 6000, seed=11)


def pop():
    t = T(.12); x = sweep(380, 980, .12) * ad(len(t), .001, .03) + noise(len(t), seed=2) * ad(len(t), 0, .003) * .35
    return norm(lp(x, 5000))


def chime(f, dur=1.4, bright=1.0):
    t = T(dur)
    x = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (dur * d))
            for r, a, d in ((1, 1, .34), (2.76, .35 * bright, .16), (5.4, .12 * bright, .08), (8.9, .05 * bright, .04)))
    return x * np.minimum(1, t / .002)


def twinkle(base=1318.5, n=5, gap=.065, dur=1.1):
    """a rising run of bell notes (pentatonic)"""
    steps = [0, 2, 4, 7, 9, 12, 14, 16]
    out = np.zeros(int((n * gap + dur) * SR))
    for i in range(n):
        c = chime(base * 2 ** (steps[i] / 12), dur, 1.0) * (.6 + .4 * i / max(1, n - 1)); k = int(i * gap * SR); out[k:k + len(c)] += c
    return norm(out)


def ding(f=1568, dur=1.6): return norm(chime(f, dur))


def sparkle_hit():
    return norm(twinkle(2093, 3, .045, .6))


def boing(dur=.6, f0=230):
    t = T(dur)
    f = f0 * (1 + 1.6 * np.exp(-3.5 * t) * np.abs(np.sin(2 * np.pi * 7.5 * t)) + .4 * np.exp(-1.2 * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + .4 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return norm(lp(x, 3500) * np.exp(-t / .28) * np.minimum(1, t / .004))


def bonk():
    """a cartoon wooden bonk"""
    t = T(.4)
    f = 190 + 520 * np.exp(-t * 14)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / .1)
    x += .55 * np.sin(2 * np.pi * np.cumsum(f * 2.76) / SR) * np.exp(-t / .035)
    x += .35 * noise(len(t), seed=5) * np.exp(-t / .004)
    return norm(x * np.minimum(1, t / .0015))


def slide_whistle(f0=1900, f1=220, dur=.7):
    t = T(dur); f = f0 * (f1 / f0) ** (t / dur) * (1 + .018 * np.sin(2 * np.pi * 6.5 * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + .15 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    return norm(x * np.minimum(1, t / .03) * np.minimum(1, (dur - t) / .05))


def riser(dur=1.0, f0=300, f1=5000):
    x = swept_noise(dur, f0, f1, q=1.4, seed=6) * (T(dur) / dur) ** 2
    return norm(x * np.minimum(1, (dur - T(dur)) / .02 + 0))


def stinger(freqs, dur=.9, bright=1500):
    """a short brass-like stab on the given frequencies"""
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for f in freqs:
        for det in (-.07, .06):
            x += signal.sawtooth(2 * np.pi * f * 2 ** (det / 12) * t) * .2
    cut = bright * (.35 + .65 * np.minimum(1, t / .07))
    out = np.zeros(n); blk = 512
    for i in range(0, n, blk):
        out[i:i + blk] = signal.sosfilt(signal.butter(2, min(cut[i], 9000), "low", fs=SR, output="sos"), x[i:i + blk])
    return norm(out * ad(n, .012, dur * .38))


def sad_trombone(scale=1.0):
    notes = [(233.1, .5), (220.0, .5), (207.7, .5), (196.0, 1.2)]
    out = []
    for k, (f, d) in enumerate(notes):
        n = int(d * SR); t = np.arange(n) / SR
        fv = f * (1 + .012 * np.sin(2 * np.pi * 5.5 * t) * (t / d)) * (1 if k < 3 else 2 ** (-2.2 * np.maximum(t - .5, 0) / 12))
        x = signal.sawtooth(2 * np.pi * np.cumsum(fv) / SR)
        y = np.zeros(n); blk = 512
        for i in range(0, n, blk):
            u = i / n; cut = 450 + 1500 * np.sin(np.pi * min(1, u * 1.3)) ** 2     # the "wah"
            y[i:i + blk] = signal.sosfilt(signal.butter(2, cut, "low", fs=SR, output="sos"), x[i:i + blk])
        out.append(y * np.minimum(1, t / .05) * np.minimum(1, (d - t) / .08) * (1 if k < 3 else .9))
    return norm(np.concatenate(out) * scale)


def short_wah():
    """the first two notes of the sad trombone"""
    s = sad_trombone()
    return norm(fade_edges(s[:int(1.0 * SR)], .004, .08))


# ------------------------------------------------------------------ football
def ball_kick(power=1.0):
    n = int(.3 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(70 + 80 * np.exp(-t * 40)) / SR) * np.exp(-t / (.05 + .04 * power))
    skin = bp(noise(n, seed=7), 300, 2600) * np.exp(-t / .012) * (.6 + .6 * power)
    return norm(body * (.7 + .5 * power) + skin * .8)


def ball_tap():
    n = int(.14 * SR); t = np.arange(n) / SR
    return norm(np.sin(2 * np.pi * np.cumsum(120 + 90 * np.exp(-t * 50)) / SR) * np.exp(-t / .03) + bp(noise(n, seed=8), 400, 2200) * np.exp(-t / .008) * .6)


def ball_flick():
    return norm(np.concatenate([whoosh(.12, True, 500, 3000, seed=4)[:int(.1 * SR)] * .5, np.zeros(int(.02 * SR)), ball_tap() * .8]))


def thud(low=70, dur=.3):
    n = int(dur * SR); t = np.arange(n) / SR
    return norm(np.sin(2 * np.pi * np.cumsum(low + 60 * np.exp(-t * 35)) / SR) * np.exp(-t / .09) + lp(noise(n, seed=9), 500) * np.exp(-t / .03) * .5)


def footfall():
    n = int(.16 * SR); t = np.arange(n) / SR
    return norm(bp(noise(n, seed=10), 500, 5000) * np.exp(-t / .012) + np.sin(2 * np.pi * 90 * t) * np.exp(-t / .03) * .6)


def net_swish():
    n = int(.5 * SR)
    return norm(hp(noise(n, "pink", 12), 1800) * np.minimum(1, np.arange(n) / (.03 * SR)) * np.exp(-np.arange(n) / (.14 * SR)))


def crowd(dur=3.0, swell=.25, release=1.4, seed=3):
    """a stadium crowd cheering: formant-filtered noise with a swell and a long tail"""
    n = int(dur * SR); base = noise(n, "pink", seed); x = np.zeros(n)
    for lo, hi, g in ((200, 520, .9), (550, 1200, .85), (1300, 2800, .5), (2900, 5200, .14)):
        x += bp(base * (1 + .6 * lp(noise(n, "white", seed + int(lo)), 8, 1)), lo, hi) * g
    t = np.arange(n) / SR
    e = np.minimum(1, t / swell) * np.exp(-np.maximum(t - swell - .2, 0) / release)
    return norm(x * e * (1 + .15 * np.sin(2 * np.pi * 3.1 * t)))


def confetti():
    n = int(1.0 * SR); t = np.arange(n) / SR; x = np.zeros(n)
    x[:int(.1 * SR)] += lp(noise(int(.1 * SR), seed=13), 900) * np.exp(-np.arange(int(.1 * SR)) / (.02 * SR)) * 1.0
    x[:int(.1 * SR)] += np.sin(2 * np.pi * 85 * np.arange(int(.1 * SR)) / SR) * np.exp(-np.arange(int(.1 * SR)) / (.03 * SR)) * .6
    x += hp(noise(n, seed=14), 2500) * np.exp(-t / .2) * .22                                  # the air
    r = rng(15)
    for k in range(70):                                                                       # paper ticks falling
        s = int(r.uniform(.03, .9) ** 1.5 * SR); m = int(r.uniform(.002, .006) * SR)
        x[s:s + m] += hp(noise(m, seed=20 + k), 4000) * r.uniform(.05, .22) * np.exp(-np.arange(m) / (.002 * SR))
    return norm(x)


def whistle_ref():
    n = int(.55 * SR); t = np.arange(n) / SR
    f = 3000 + 160 * np.sin(2 * np.pi * 30 * t)
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / .02) * np.minimum(1, (.55 - t) / .05))


# ------------------------------------------------------------------ table tennis
def tok(f=2300, hard=1.0):
    n = int(.08 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / .006) + .5 * np.sin(2 * np.pi * f * 1.52 * t) * np.exp(-t / .004)
    x += bp(noise(n, seed=16), 2500, 8000) * np.exp(-t / .003) * (.5 * hard)
    return norm(x)


def tik():
    n = int(.05 * SR); t = np.arange(n) / SR
    return norm(np.sin(2 * np.pi * 1350 * t) * np.exp(-t / .004) + bp(noise(n, seed=17), 1500, 6000) * np.exp(-t / .002) * .4)


def swish(dur=.14):
    n = int(dur * SR)
    return norm(swept_noise(dur, 900, 3800, q=1.5, seed=18) * np.sin(np.pi * np.arange(n) / n) ** 1.5)


def smash_crack():
    n = int(.3 * SR); t = np.arange(n) / SR
    x = tok(1700, 1.6)[:int(.08 * SR)]; y = np.zeros(n); y[:len(x)] = x
    y += np.sin(2 * np.pi * np.cumsum(520 * np.exp(-t * 9) + 130) / SR) * np.exp(-t / .05) * .8
    y += bp(noise(n, seed=19), 800, 6000) * np.exp(-t / .02) * .7
    return norm(y)


def machine_fire():
    n = int(.25 * SR); t = np.arange(n) / SR
    x = lp(noise(n, seed=21), 1400) * np.exp(-t / .03) + sweep(260, 90, .25) * np.exp(-t / .06) * .9
    x += hp(noise(n, seed=22), 3000) * np.exp(-t / .012) * .3
    return norm(x)


def machine_hum(dur=1.5):
    t = T(dur); x = np.sin(2 * np.pi * 92 * t) + .5 * signal.sawtooth(2 * np.pi * 46 * t) * (1 + .3 * np.sin(2 * np.pi * 7 * t))
    return norm(lp(x, 400) * np.minimum(1, t / .1) * np.minimum(1, (dur - t) / .1))


def cardboard_hit():
    n = int(.6 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 130 * t) * np.exp(-t / .05) + bp(noise(n, seed=23), 250, 2400) * np.exp(-t / .045) * .8
    wob = np.sin(2 * np.pi * np.cumsum(215 * (1 + .12 * np.sin(2 * np.pi * 8 * t) * np.exp(-t * 5))) / SR) * np.exp(-t / .16) * .35
    return norm(x + wob)


# ------------------------------------------------------------------ water
def _bubbles(dur, density, seed, lo=500, hi=1800, amp=1.0):
    n = int(dur * SR); x = np.zeros(n); r = rng(seed)
    for k in range(int(dur * density)):
        s = int(r.uniform(0, dur - .12) * SR); m = int(r.uniform(.03, .09) * SR); f0 = r.uniform(lo, hi)
        t = np.arange(m) / SR
        x[s:s + m] += np.sin(2 * np.pi * np.cumsum(f0 * (1 + 1.2 * t / (m / SR))) / SR) * np.exp(-t / (.02 + r.uniform(0, .02))) * r.uniform(.2, 1) * amp
    return x


def splash(size=1.0, seed=24):
    dur = .35 + .55 * size; n = int(dur * SR)
    body = swept_noise(dur, 6500, 700, q=1.3, seed=seed) * ad(n, .004, .12 + .1 * size)
    return norm(body + _bubbles(dur, 14 + 18 * size, seed, 400, 1600, .35) + hp(noise(n, seed=seed + 1), 5000) * ad(n, 0, .04) * .25)


def wave_crash():
    """a whole wave landing on his face: a big splash, then a slosh"""
    a = splash(1.7, 30); n = int(1.3 * SR); x = np.zeros(n); x[:len(a)] += a
    x += lp(noise(n, "pink", 31), 900) * np.exp(-np.arange(n) / (.35 * SR)) * .5
    return norm(x)


def swim_swish(dur=.7):
    n = int(dur * SR)
    return norm(swept_noise(dur, 500, 2200, q=1.4, seed=32) * np.sin(np.pi * np.arange(n) / n) ** 1.2 + _bubbles(dur, 20, 33) * .3)


def water_bed(dur, density=16, seed=34):
    """bubbling jacuzzi: soft pink noise and bubbles"""
    n = int(dur * SR); x = lp(noise(n, "pink", seed), 1100) * .5 + _bubbles(dur, density, seed, 350, 1500, .6)
    t = np.arange(n) / SR
    return x * (1 + .2 * np.sin(2 * np.pi * .4 * t)) * np.minimum(1, t / .3) * np.minimum(1, (dur - t) / .4)


def drip():
    n = int(.15 * SR); t = np.arange(n) / SR
    return norm(sweep(1500, 650, .15) * np.exp(-t / .03) * np.minimum(1, t / .001))


def plip():
    n = int(.1 * SR); t = np.arange(n) / SR
    return norm(sweep(2100, 1100, .1) * np.exp(-t / .018))


def steam_bed(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return hp(noise(n, "pink", 35), 2500) * (.6 + .4 * np.sin(2 * np.pi * .23 * t)) * np.minimum(1, t / .4) * np.minimum(1, (dur - t) / .4)


def kettle(dur=1.5):
    t = T(dur); f = 2150 + 1000 * (t / dur) ** 1.6
    x = np.sin(2 * np.pi * np.cumsum(f * (1 + .01 * np.sin(2 * np.pi * 11 * t))) / SR) + .3 * np.sin(4 * np.pi * np.cumsum(f) / SR)
    x = x * (.4 + .6 * (t / dur) ** .8) + hp(noise(len(t), seed=36), 3500) * .12
    return norm(x * np.minimum(1, t / .15) * np.minimum(1, (dur - t) / .1))


def rain_bed(dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = bp(noise(n, "pink", 37), 900, 9000, 2)
    r = rng(38)
    for k in range(int(dur * 70)):
        s = int(r.uniform(0, dur - .02) * SR); m = int(.01 * SR)
        x[s:s + m] += hp(noise(m, seed=40 + k), 3000) * r.uniform(.2, .7) * np.exp(-np.arange(m) / (.003 * SR))
    return x * np.minimum(1, t / .2) * np.minimum(1, (dur - t) / .3)


# ------------------------------------------------------------------ the house
def chomp():
    n = int(.25 * SR); x = np.zeros(n); r = rng(41)
    for off, g in ((0, 1.0), (.04, .8), (.08, .55)):
        s = int(off * SR); m = int(.06 * SR)
        x[s:s + m] += bp(noise(m, seed=42 + int(off * 100)), 1200, 5200) * ad(m, .0008, .012) * g
    x[:int(.1 * SR)] += np.sin(2 * np.pi * 150 * np.arange(int(.1 * SR)) / SR) * ad(int(.1 * SR), .001, .02) * .45
    return norm(x)


def chew(dur=.9):
    n = int(dur * SR); x = np.zeros(n); r = rng(43)
    for k in range(int(dur / .16)):
        s = int((k * .16 + r.uniform(0, .03)) * SR); m = int(.05 * SR)
        x[s:s + m] += bp(noise(m, seed=60 + k), 700, 3200) * ad(m, .003, .014) * r.uniform(.4, 1)
    return norm(x * np.exp(-np.arange(n) / (.9 * SR)))


def fork_clink():
    t = T(.45)
    x = (np.sin(2 * np.pi * 3120 * t) * np.exp(-t / .07) + .6 * np.sin(2 * np.pi * 4710 * t) * np.exp(-t / .05)
         + .3 * np.sin(2 * np.pi * 6320 * t) * np.exp(-t / .03))
    return norm(x * np.minimum(1, t / .0008) + hp(noise(len(t), seed=44), 5000) * np.exp(-t / .002) * .3)


def glass_slide():
    """a glass of water slid across a table, then set down with a clink"""
    n = int(.4 * SR); t = np.arange(n) / SR
    s = bp(noise(n, "pink", 45), 500, 2200) * np.sin(np.pi * np.minimum(1, t / .4)) ** 0.7 * .7
    c = chime(2950, .6, .6)[:int(.6 * SR)] * .9
    out = np.zeros(n + len(c) - int(.02 * SR)); out[:n] += s; out[n - int(.02 * SR):] += c
    return norm(out)


def hand_rub(dur=.8):
    n = int(dur * SR); t = np.arange(n) / SR
    return norm(bp(noise(n, seed=46), 1500, 5000) * (.5 + .5 * np.sin(2 * np.pi * 13 * t)) * np.minimum(1, t / .05) * np.minimum(1, (dur - t) / .1))


def poof(dur=.5):
    n = int(dur * SR); t = np.arange(n) / SR
    return norm(lp(noise(n, "pink", 47), 2600) * ad(n, .02, dur * .3) + np.sin(2 * np.pi * 60 * t) * ad(n, .005, .08) * .4)


def zip_vanish():
    return norm(np.concatenate([sweep(300, 3600, .26) * np.sin(np.pi * T(.26) / .26) ** .5 * .7 + whoosh(.26, True, 600, 5000)[:int(.26 * SR)] * .5, pop()[:int(.1 * SR)] * .8]))


def ff_whirr(dur):
    """cartoon fast-forward: a chirpy tape scan rising in pitch"""
    n = int(dur * SR); t = np.arange(n) / SR
    f = 380 * 2.6 ** (t / dur) * (1 + .5 * (np.sin(2 * np.pi * 15 * t) > 0))
    x = signal.square(2 * np.pi * np.cumsum(f) / SR, .35) * .4 + bp(noise(n, seed=48), 1500, 6000) * .3
    return norm(lp(x, 4500) * np.minimum(1, t / .05) * np.minimum(1, (dur - t) / .05))


def twang_lonely():
    t = T(1.2); f = 196 * (1 + .03 * np.exp(-t * 3) * np.sin(2 * np.pi * 6 * t))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + .5 * np.sin(4 * np.pi * np.cumsum(f) / SR) + .25 * np.sin(6 * np.pi * np.cumsum(f) / SR)
    return norm(lp(x, 2200) * np.exp(-t / .35) * np.minimum(1, t / .003))


def cricket(dur=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for s in np.arange(0, dur - .12, .5):
        for k in range(4):
            i = int((s + k * .035) * SR); m = int(.022 * SR)
            x[i:i + m] += np.sin(2 * np.pi * 4300 * np.arange(m) / SR) * np.hanning(m)
    return x


def wind_bed(dur, seed=49):
    n = int(dur * SR); t = np.arange(n) / SR; x = noise(n, "pink", seed); y = np.zeros(n); blk = 2048
    for i in range(0, n, blk):
        f = 380 + 220 * np.sin(2 * np.pi * .35 * i / SR)
        y[i:i + blk] = signal.sosfilt(signal.butter(2, [f / 1.7, f * 1.7], "band", fs=SR, output="sos"), x[i:i + blk])
    return y * (.5 + .5 * np.sin(2 * np.pi * .21 * t + 1)) ** 1.2 * np.minimum(1, t / .3) * np.minimum(1, (dur - t) / .3)


def rustle(dur=1.0):
    n = int(dur * SR); x = np.zeros(n); r = rng(50)
    for k in range(int(dur * 9)):
        s = int(r.uniform(0, dur - .08) * SR); m = int(r.uniform(.03, .07) * SR)
        x[s:s + m] += hp(noise(m, seed=70 + k), 1800) * np.hanning(m) * r.uniform(.3, 1)
    return norm(x)


def paper_box_land():
    """a heavy cardboard box landing in the dust"""
    n = int(.7 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * np.cumsum(95 * np.exp(-t * 14) + 45) / SR) * np.exp(-t / .1)
    x += bp(noise(n, seed=51), 200, 2500) * np.exp(-t / .06) * .9 + lp(noise(n, seed=52), 1500) * ad(n, .02, .15) * .3
    return norm(x)


def falling_whistle(dur=.35):
    return slide_whistle(2100, 520, dur)


def battery_beep():
    t = T(.07); one = np.sin(2 * np.pi * 1760 * t) * np.minimum(1, t / .003) * np.minimum(1, (.07 - t) / .01)
    return norm(np.concatenate([one, np.zeros(int(.06 * SR)), one]))


def power_up():
    out = np.zeros(int(1.5 * SR))
    for i, s in enumerate((0, 4, 7, 12, 16, 19, 24)):
        f = 330 * 2 ** (s / 12); t = T(.16)
        n = signal.square(2 * np.pi * f * t, .4) * .25 * np.exp(-t / .09) + np.sin(2 * np.pi * f * t) * .25 * np.exp(-t / .1)
        k = int(i * .055 * SR); out[k:k + len(n)] += n
    d = chime(1980, .9)
    k = int(.45 * SR); out[k:k + len(d)] += d * .9
    return norm(out)


def taiko():
    t = T(1.2); n = len(t)
    body = np.sin(2 * np.pi * np.cumsum(46 + 70 * np.exp(-t * 16)) / SR) * np.exp(-t / .3)
    skin = lp(noise(n, seed=53), 700) * np.exp(-t / .04) * .7
    return norm(body + skin + lp(noise(n, "pink", 54), 300) * np.exp(-t / .5) * .15)


def shing():
    t = T(.9)
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in ((3720, 1, .25), (5110, .8, .18), (7330, .6, .12), (9100, .3, .08)))
    return norm(x * np.minimum(1, t / .001) + hp(noise(len(t), seed=55), 6000) * np.exp(-t / .05) * .4)


def heartbeat():
    n = int(.6 * SR); x = np.zeros(n)
    for off, g in ((0, 1.0), (.17, .75)):
        s = int(off * SR); t = np.arange(int(.2 * SR)) / SR
        x[s:s + len(t)] += np.sin(2 * np.pi * np.cumsum(58 + 30 * np.exp(-t * 30)) / SR) * np.exp(-t / .045) * g
    return norm(x)


def boxing_bell():
    t = T(1.8); x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d) for f, a, d in ((1180, 1, .8), (2360, .5, .55), (3260, .4, .35), (6370, .15, .2)))
    return norm(x * np.minimum(1, t / .001))


def camera_shutter():
    out = np.zeros(int(.25 * SR))
    for off, g in ((0, 1.0), (.065, .7)):
        s = int(off * SR); m = int(.02 * SR)
        out[s:s + m] += hp(noise(m, seed=56 + int(off * 100)), 2500) * ad(m, 0, .004) * g
        out[s:s + m] += np.sin(2 * np.pi * 220 * np.arange(m) / SR) * ad(m, 0, .006) * .4 * g
    return norm(out)


def huff():
    n = int(.4 * SR); t = np.arange(n) / SR
    return norm(bp(noise(n, "pink", 57), 350, 2600) * np.sin(np.pi * np.minimum(1, t / .4)) ** 1.5)


# ------------------------------------------------------------------ ambience
def birds(dur, density=.5, seed=60):
    """a few small birds somewhere in the trees"""
    n = int(dur * SR); x = np.zeros(n); r = rng(seed)
    for k in range(max(1, int(dur * density))):
        s = int(r.uniform(0, max(.1, dur - .6)) * SR); f0 = r.uniform(2800, 4300); reps = int(r.integers(2, 5))
        for j in range(reps):
            m = int(.07 * SR); i = s + int(j * .1 * SR)
            if i + m >= n: break
            tt = np.arange(m) / SR
            x[i:i + m] += np.sin(2 * np.pi * np.cumsum(f0 * (1 + .35 * np.sin(2 * np.pi * 14 * tt)) * (1 - .3 * tt / .07)) / SR) * np.sin(np.pi * tt / .07) ** 2 * r.uniform(.4, 1)
    return x


def air_bed(dur, seed=61):
    """outdoor air: a very soft, slowly moving low rush"""
    n = int(dur * SR); t = np.arange(n) / SR
    return lp(noise(n, "pink", seed), 900) * (.7 + .3 * np.sin(2 * np.pi * .13 * t + 1)) * np.minimum(1, t / .3) * np.minimum(1, (dur - t) / .3)


def room_bed(dur, seed=62):
    """indoors: a soft low hum and a little air"""
    n = int(dur * SR); t = np.arange(n) / SR
    return (lp(noise(n, "pink", seed), 350) + .25 * np.sin(2 * np.pi * 120 * t)) * np.minimum(1, t / .3) * np.minimum(1, (dur - t) / .3)

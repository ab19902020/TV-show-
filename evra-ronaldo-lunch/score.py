"""The music: a playful, warm comedy score, synthesised (marimba, pizzicato, vibes, bass, pads, brass stabs and a
small drum kit). One key family throughout (A minor / C major), so every cut between moods stays in tune.

Each section of the film (a shot or a run of shots) gets its own groove, and every section starts ON the picture cut,
so the downbeat lands where the edit does. audio.py gives the section start times from direction.SHOTS."""
import functools
import numpy as np
from scipy import signal
from sfx import SR, T, noise, bp, lp, hp, ad, norm, sweep, chime, stinger


def mtof(m): return 440.0 * 2 ** ((m - 69) / 12)


def _end(x, ms=8):
    n = min(len(x), int(ms * SR / 1000)); x = x.copy(); x[-n:] *= np.linspace(1, 0, n); return x


# ------------------------------------------------------------------ instruments (cached)
@functools.lru_cache(None)
def marimba(m, dur=.45):
    f = mtof(m); t = T(dur)
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / .34) + .33 * np.sin(2 * np.pi * f * 4.0 * t) * np.exp(-t / .055) + .07 * np.sin(2 * np.pi * f * 9.9 * t) * np.exp(-t / .02)
    return _end(x * np.minimum(1, t / .002)).astype(np.float32)


@functools.lru_cache(None)
def pluck(m, dur=.3):
    f = mtof(m); t = T(dur); x = np.zeros(len(t))
    for k in range(1, 7): x += (1 / k) * np.sin(2 * np.pi * f * k * t) * np.exp(-t / (.2 / k ** .55))
    return _end(x * np.minimum(1, t / .002)).astype(np.float32)


@functools.lru_cache(None)
def bass(m, dur=.3):
    f = mtof(m); t = T(dur)
    x = np.sin(2 * np.pi * f * t) + .4 * np.sin(4 * np.pi * f * t) * np.exp(-t / .12) + .18 * np.sin(6 * np.pi * f * t) * np.exp(-t / .06)
    return _end(x * ad(len(t), .004, dur * .55)).astype(np.float32)


@functools.lru_cache(None)
def vibes(m, dur=1.2):
    f = mtof(m); t = T(dur)
    x = (np.sin(2 * np.pi * f * t) + .22 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t / .1)) * (1 + .25 * np.sin(2 * np.pi * 5.2 * t))
    return _end(x * np.exp(-t / .8) * np.minimum(1, t / .003), 20).astype(np.float32)


@functools.lru_cache(None)
def pad(ms, dur, release=.5):
    n = int(dur * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for m in ms:
        for det in (-.1, 0, .1):
            x += signal.sawtooth(2 * np.pi * mtof(m) * 2 ** (det / 12) * t, .5) * .17 + np.sin(2 * np.pi * mtof(m) * t) * .08
    x = lp(x, 1500, 2)
    e = np.minimum(1, t / .5) * np.minimum(1, (dur - t) / release)
    return (x * e).astype(np.float32)


@functools.lru_cache(None)
def sq(m, dur=.12):
    t = T(dur)
    return _end(lp(signal.square(2 * np.pi * mtof(m) * t, .35), 2600) * ad(len(t), .002, .07)).astype(np.float32)


@functools.lru_cache(None)
def brass(ms, dur=.45):
    return stinger([mtof(m) for m in ms], dur, 1700)


@functools.lru_cache(None)
def kick():
    t = T(.28); x = np.sin(2 * np.pi * np.cumsum(46 + 96 * np.exp(-t * 28)) / SR) * np.exp(-t / .12)
    return (x + hp(noise(len(t), seed=71), 1500) * np.exp(-t / .004) * .25).astype(np.float32)


@functools.lru_cache(None)
def snare():
    n = int(.22 * SR); t = np.arange(n) / SR
    return (bp(noise(n, seed=72), 1200, 7500) * ad(n, .001, .07) + np.sin(2 * np.pi * 190 * t) * np.exp(-t / .06) * .55).astype(np.float32)


@functools.lru_cache(None)
def clap():
    n = int(.25 * SR); x = np.zeros(n)
    for off in (0, .011, .024):
        s = int(off * SR); m = n - s
        x[s:] += bp(noise(m, seed=73 + int(off * 1000)), 900, 3800) * ad(m, .0005, .045 if off == .024 else .008)
    return x.astype(np.float32)


@functools.lru_cache(None)
def hat(open_=False):
    n = int((.28 if open_ else .06) * SR)
    return (hp(noise(n, seed=75), 7000) * ad(n, .0005, .12 if open_ else .014)).astype(np.float32)


@functools.lru_cache(None)
def wood():
    t = T(.1)
    return (np.sin(2 * np.pi * 880 * t) * np.exp(-t / .02) + .5 * np.sin(2 * np.pi * 1330 * t) * np.exp(-t / .012)).astype(np.float32)


@functools.lru_cache(None)
def tom(f=110):
    t = T(.4)
    return (np.sin(2 * np.pi * np.cumsum(f * (1 + .6 * np.exp(-t * 20))) / SR) * np.exp(-t / .16)).astype(np.float32)


@functools.lru_cache(None)
def taiko():
    t = T(.9)
    return (np.sin(2 * np.pi * np.cumsum(44 + 62 * np.exp(-t * 14)) / SR) * np.exp(-t / .28) + lp(noise(len(t), seed=76), 600) * np.exp(-t / .04) * .6).astype(np.float32)


# ------------------------------------------------------------------ the bus
class Bus:
    def __init__(self, dur):
        self.n = int(dur * SR) + 1; self.L = np.zeros(self.n); self.R = np.zeros(self.n)

    def add(self, x, t, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= self.n or i + len(x) <= 0 or gain <= 0: return
        k0 = max(0, -i); j0 = max(0, i); m = min(len(x) - k0, self.n - j0)
        a = (pan + 1) * np.pi / 4
        self.L[j0:j0 + m] += x[k0:k0 + m] * gain * np.cos(a) * 1.4142
        self.R[j0:j0 + m] += x[k0:k0 + m] * gain * np.sin(a) * 1.4142

    def add_bus(self, o, t, gain=1.0):
        i = int(round(t * SR)); m = min(o.n, self.n - i)
        if m > 0: self.L[i:i + m] += o.L[:m] * gain; self.R[i:i + m] += o.R[:m] * gain


# ------------------------------------------------------------------ harmony (A minor / C major)
PROG_AM = [(45, [57, 60, 64]), (41, [53, 57, 60]), (48, [55, 60, 64]), (43, [55, 59, 62])]        # Am F C G
PROG_C = [(48, [55, 60, 64]), (43, [55, 59, 62]), (45, [57, 60, 64]), (41, [53, 57, 60])]         # C G Am F
PROG_FUNK = [(45, [57, 60, 64, 67]), (50, [57, 60, 62, 66]), (45, [57, 60, 64, 67]), (50, [57, 60, 62, 65])]
PROG_LOUNGE = [(41, [57, 60, 64, 67]), (40, [55, 59, 62, 64]), (38, [53, 57, 60, 64]), (43, [55, 59, 62, 65])]

BASS_FUNK = [(0, 0, 2), (3, 0, 1), (6, 12, 1), (7, 0, 1), (10, 0, 2), (13, 7, 1), (14, 5, 1)]
BASS_TIP = [(0, 0, 3), (6, 7, 2), (8, 0, 3), (14, 7, 2)]
BASS_TROP = [(0, 0, 2), (3, 0, 1), (6, 7, 1), (8, 0, 2), (11, 0, 1), (14, 5, 1)]
BASS_LONG = [(0, 0, 7), (8, 0, 6)]
BASS_8 = [(s, 0, 2) for s in range(0, 16, 2)]
BASS_16 = [(s, 0 if s % 4 else 0, 1) for s in range(16)]
ARP_8 = [(s, i) for s, i in zip(range(0, 16, 2), (0, 1, 2, 1, 0, 1, 2, 3))]
ARP_SYNC = [(0, 0), (3, 2), (6, 1), (8, 3), (11, 2), (14, 1)]
ARP_SLOW = [(0, 0), (4, 1), (8, 2), (12, 1)]
ARP_16 = [(s, (0, 1, 2, 3, 2, 1, 2, 3)[s % 8]) for s in range(16)]


def groove(B, dur, bpm, prog, g=1.0, kick_=(), snare_=(), clap_=(), hat_=None, open_=(), wood_=(), bass_=(), stab=(), arp=(),
           arp_inst="marimba", pad_=False, brass_=(), taiko_=(), tom_=(), arp_oct=12, arp_gain=.3, bass_gain=.8, pan_arp=-.25):
    sd = 60 / bpm / 4; k = 0
    while k * sd < dur - 1e-6:
        t = k * sd; s = k % 16; bar = k // 16
        root, tones = prog[bar % len(prog)]
        ext = tones + [x + 12 for x in tones]
        if s in kick_: B.add(kick(), t, .85 * g)
        if s in snare_: B.add(snare(), t, .55 * g)
        if s in clap_: B.add(clap(), t, .5 * g, .1)
        if hat_ == "8" and s % 2 == 0: B.add(hat(), t, (.26 if s % 4 == 0 else .15) * g, .3)
        if hat_ == "16": B.add(hat(), t, (.26 if s % 4 == 0 else (.15 if s % 2 == 0 else .08)) * g, .3)
        if s in open_: B.add(hat(True), t, .2 * g, .3)
        if s in wood_: B.add(wood(), t, .22 * g, -.15)
        if s in taiko_: B.add(taiko(), t, .8 * g)
        if s in tom_: B.add(tom(95 + 18 * (s % 3)), t, .45 * g, -.3 + .15 * (s % 3))
        for st, off, ln in bass_:
            if st == s: B.add(bass(root + off, ln * sd * .92), t, bass_gain * g)
        if s in stab:
            for nt in tones: B.add(pluck(nt + 12, .13), t, .16 * g, .22)
        for st, i in arp:
            if st == s:
                nt = ext[i % len(ext)] + (arp_oct - 12)
                if arp_inst == "marimba": B.add(marimba(nt + 12, .4), t, arp_gain * g, pan_arp)
                elif arp_inst == "vibes": B.add(vibes(nt + 12, 1.1), t, arp_gain * g, .2)
                elif arp_inst == "sq": B.add(sq(nt + 12, .11), t, arp_gain * .55 * g, .15)
                else: B.add(pluck(nt + 12, .25), t, arp_gain * g, pan_arp)
        if s in brass_: B.add(brass(tuple(x for x in tones), .42), t, .5 * g)
        if s == 0 and pad_ and bar * 16 * sd < dur - .2:
            B.add(pad(tuple(tones), min(16 * sd, dur - bar * 16 * sd) + .3, .45), t, .5 * g, 0)
        k += 1


STYLES = {
    # a gentle morning: pizzicato bass, tiny plucks, a woodblock tick
    "intro": dict(bpm=100, prog=PROG_AM, bass_=BASS_TIP, wood_=(4, 12), stab=(), arp=[(0, 0), (6, 1), (8, 2), (14, 1)], pad_=True, g=.8),
    "dream": dict(bpm=76, prog=PROG_C, arp=ARP_SLOW, arp_inst="vibes", pad_=True, g=.9, arp_gain=.28),
    "cheeky": dict(bpm=108, prog=PROG_AM, kick_=(0, 10), snare_=(), hat_="8", wood_=(4, 12), bass_=BASS_TIP, stab=(4, 12), arp=ARP_8, g=.85),
    "tiptoe": dict(bpm=112, prog=PROG_AM, bass_=[(0, 0, 3), (4, 7, 2), (8, 0, 3), (12, 7, 2)], stab=(2, 6, 10, 14), wood_=(0, 8), arp=[(0, 0), (3, 1), (6, 2), (9, 1), (12, 0)], arp_inst="pluck", g=.9),
    "run": dict(bpm=168, prog=PROG_AM, bass_=[(s, 0 if s % 8 < 4 else 7, 1) for s in range(0, 16, 2)], wood_=tuple(range(0, 16, 2)),
                arp=[(s, (0, 1, 2, 3, 4, 3, 2, 1)[s // 2]) for s in range(0, 16, 2)], arp_inst="pluck", hat_="8", g=.9, arp_gain=.34),
    "funk": dict(bpm=104, prog=PROG_FUNK, kick_=(0, 7, 10), snare_=(4, 12), hat_="16", bass_=BASS_FUNK, stab=(2, 6, 11), arp=ARP_8, g=1.0),
    "tropical": dict(bpm=100, prog=PROG_C, kick_=(0, 10), snare_=(4, 12), hat_="8", wood_=(2, 6, 10, 14), bass_=BASS_TROP, arp=ARP_SYNC, arp_gain=.33, g=.95),
    "hot": dict(bpm=76, prog=PROG_AM, kick_=(0, 10), snare_=(8,), hat_="8", bass_=BASS_LONG, arp=ARP_SLOW, arp_inst="vibes", pad_=True, g=.85),
    "lounge": dict(bpm=82, prog=PROG_LOUNGE, kick_=(0,), snare_=(8,), hat_="8", bass_=[(0, 0, 4), (6, 7, 2), (8, 0, 4), (14, 5, 2)], arp=ARP_SLOW,
                   arp_inst="vibes", pad_=True, g=.9),
    "hero": dict(bpm=112, prog=PROG_C, kick_=(0, 8), snare_=(4, 12), hat_="8", taiko_=(0,), brass_=(0, 6, 8, 14), bass_=[(0, 0, 4), (8, 0, 4)], pad_=True, g=1.0),
    "glam": dict(bpm=118, prog=PROG_AM, kick_=(0, 4, 8, 12), clap_=(4, 12), open_=(2, 6, 10, 14), bass_=[(2, 12, 1), (6, 12, 1), (10, 12, 1), (14, 12, 1)],
                 arp=ARP_16, arp_inst="vibes", arp_gain=.2, pad_=True, g=.9),
    "epic": dict(bpm=92, prog=PROG_AM, taiko_=(0, 8), tom_=(12, 14), bass_=[(0, 0, 7), (8, 0, 4)], brass_=(0, 6), pad_=True, g=1.0),
    "warm": dict(bpm=84, prog=PROG_C, bass_=[(0, 0, 8), (8, 7, 6)], arp=ARP_SLOW, arp_inst="vibes", pad_=True, g=.9, arp_gain=.28),
    "tech": dict(bpm=128, prog=PROG_AM, kick_=(0, 4, 8, 12), snare_=(4, 12), hat_="16", bass_=BASS_8, arp=ARP_16, arp_inst="sq", g=.9),
    "rally": dict(bpm=150, prog=PROG_AM, kick_=(0, 8), hat_="8", open_=(6, 14), bass_=[(0, 0, 3), (8, 7, 3)], wood_=(2, 10), stab=(4, 12), g=.8),
    "sly": dict(bpm=104, prog=PROG_AM, bass_=[(0, 0, 2), (3, 0, 1), (8, 7, 2), (11, 5, 1)], wood_=(4, 12), arp=[(2, 2), (5, 1), (10, 3), (13, 2)], arp_inst="pluck", g=.85),
    "comic": dict(bpm=122, prog=PROG_FUNK, kick_=(0, 8), snare_=(4, 12), hat_="8", brass_=(0, 3, 6, 10), bass_=BASS_FUNK, arp=ARP_8, g=1.0),
    "whimsy": dict(bpm=112, prog=PROG_C, bass_=BASS_TIP, wood_=(2, 6, 10, 14), arp=[(0, 0), (2, 1), (4, 2), (6, 3), (8, 2), (10, 1), (12, 0), (14, 1)], g=.9),
    "night": dict(bpm=93.75, prog=PROG_AM, bass_=[(s, 0, 1) for s in range(0, 16, 2)], arp=[(0, 4), (6, 3), (12, 5)], arp_inst="vibes", pad_=True, g=.95, bass_gain=.9),
    "triumph": dict(bpm=124, prog=PROG_C, kick_=(0, 4, 8, 12), snare_=(4, 12), clap_=(4, 12), hat_="8", brass_=(0, 3, 6, 8, 12), bass_=[(0, 0, 3), (4, 0, 3), (8, 7, 3), (12, 0, 3)], taiko_=(0,), pad_=True, g=1.05),
    "reprise": dict(bpm=100, prog=PROG_AM, bass_=BASS_TIP, wood_=(4, 12), arp=[(0, 0), (6, 1), (8, 2), (14, 1)], pad_=True, g=.85),
}


def tension(B, dur, g=1.0):
    """so close... / determined: a low pad, a slow heartbeat and a creeping marimba"""
    B.add(pad((45, 52, 57), dur + .3, .6), 0, .6 * g)
    t = 0.0
    while t < dur - .3:
        B.add(tom(60), t, .5 * g); B.add(tom(60), t + .17, .35 * g); t += .78 - .22 * (t / max(dur, 1))
    for i, m in enumerate((69, 68, 69, 71)):
        B.add(marimba(m, .4), .35 + i * .45, .2 * g, .2)


def boil(B, dur, g=1.0):
    """angry: a sub pulse that speeds up, a rising tone"""
    t = 0.0; k = 0
    while t < dur - .1:
        B.add(bass(33 + (k % 2) * 7, .2), t, .9 * g); t += max(.12, .42 - .02 * k); k += 1
    B.add(pad((45, 48, 52), dur + .2, .3), 0, .35 * g)


def dread(B, dur, g=1.0):
    """the wait for lunch, the empty doorway: almost nothing, one lonely low note"""
    B.add(pad((45, 52), dur + .4, .8), 0, .35 * g)
    for i, m in enumerate((57, 56)):
        if .4 + i * 1.3 < dur - .3: B.add(marimba(m, 1.0), .4 + i * 1.3, .3 * g, .1)


def button(B, g=1.0):
    """the last chord: A minor with a woodblock tick and a kick"""
    for m in (45, 57, 60, 64, 69): B.add(marimba(m, .6) if m > 50 else bass(m, .5), 0, (.5 if m > 50 else .9) * g, 0)
    B.add(pluck(72, .5), 0, .3 * g, .2); B.add(kick(), 0, .8 * g); B.add(clap(), 0, .4 * g)


def section(total, t0, dur, name, tail=.22, gain=1.0, **over):
    """render one section as its own little bus and return (bus, t0)"""
    B = Bus(dur + tail + .6)
    if name == "tension": tension(B, dur, gain)
    elif name == "boil": boil(B, dur, gain)
    elif name == "dread": dread(B, dur, gain)
    elif name == "button": button(B, gain)
    elif name == "silence": pass
    else:
        st = dict(STYLES[name]); st.update(over); st["g"] = st.get("g", 1.0) * gain
        groove(B, dur, **st)
    # the section's end: ring out for `tail`, then nothing (a hard cut for tail ~ 0)
    n = int((dur + tail) * SR); e = np.ones(B.n)
    e[n:] = 0; k = int(min(tail, .25) * SR)
    if k: e[n - k:n] = np.linspace(1, 0, k)
    B.L *= e; B.R *= e
    f = int(.003 * SR); B.L[:f] *= np.linspace(0, 1, f); B.R[:f] *= np.linspace(0, 1, f)
    return B, t0


def reverb_ir(seconds=1.3, damp=5500, seed=5):
    rng = np.random.default_rng(seed); n = int(seconds * SR); t = np.arange(n) / SR
    ir = rng.standard_normal((n, 2)) * np.exp(-6.9 * t / seconds)[:, None]
    ir[:, 0] = lp(ir[:, 0], damp); ir[:, 1] = lp(ir[:, 1], damp)
    ir = np.concatenate([np.zeros((int(.012 * SR), 2)), ir])
    return ir / np.sqrt((ir ** 2).sum(0).mean())


def with_reverb(L, R, wet=.14):
    ir = reverb_ir()
    wl = signal.fftconvolve(L, ir[:, 0])[:len(L)]; wr = signal.fftconvolve(R, ir[:, 1])[:len(R)]
    return L + wet * wl * 1.5, R + wet * wr * 1.5

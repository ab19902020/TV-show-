"""The soundtrack for scenes 3-4 (Hull away), added to audio.py's buses. Everything is synthesised (no library).

Scene 3  exterior: the crowd builds, a distant chant with claps, the coach's diesel rolls in right to left, slows,
         air brakes. Pre-match pulse at 80 bpm, a kick on every insert cut. Foley per insert: boots, the kit on its
         hanger, tape off the roll, the keeper's gloves, steps in the tunnel, Bruno's studs, laces pulled tight, the
         marker on the board. Dressing room: tiled room tone, the crowd muffled through the walls.
Scene 4  a smash cut into the full stadium; the kick-off whistle; the home end chanting; the corner (strike, header,
         shot, net, the roar); the free kick and the pinball in the six-yard box; full-time whistle, then a hard cut to
         silence."""
import math, numpy as np
from scipy import signal
import audio as A
import direction as D
import hull

SR = A.SR
m = A.m
T_, E_, W_ = D.T, D.E, D.W
RNG = np.random.default_rng(34)
at, bp, lp, hp, noise, env_ad, fade = A.at_level, A.bp, A.lp, A.hp, A.noise, A.env_ad, A.fade


def seg(t0, t1):
    return int(round((t1 - t0) * SR))


# ---------------------------------------------------------------- sounds
def diesel(dur, f0=42.0, f1=30.0):
    """a coach's diesel idling down: low firing pulses + rattle, pitch falling as it slows"""
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 + (f1 - f0) * np.clip(t / dur, 0, 1) ** 0.7
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = signal.sawtooth(ph).astype(np.float32) * 0.6 + np.sin(2 * ph) * 0.3 + np.sin(0.5 * ph) * 0.4
    x = lp(x, 400, 2) + 0.15 * bp(noise(n), 300, 1800, 2) * (0.6 + 0.4 * np.sin(ph))
    return x.astype(np.float32)


def air_brake():
    n = int(0.9 * SR); t = np.arange(n) / SR
    x = hp(noise(n), 2500, 2) * np.exp(-t * 4.5) * np.minimum(1, t / 0.01)
    return (x + 0.4 * bp(noise(n), 800, 2000, 2) * np.exp(-t * 12)).astype(np.float32)


def chant(dur, bpm=120, far=True):
    """a terrace chant: sung crowd vowel on a two-note tune, then three claps, repeating"""
    n = int(dur * SR); t = np.arange(n) / SR
    beat = 60 / bpm
    out = np.zeros(n, np.float32)
    base = A.crowd_bed(n, 0.6, far=far)
    for k in range(int(dur / (4 * beat)) + 1):
        t0 = k * 4 * beat
        for j, (a, b, f) in enumerate(((0.0, 0.9, 220), (1.0, 1.9, 262))):
            i0, i1 = int((t0 + a * beat) * SR), int((t0 + b * beat) * SR)
            if i0 >= n: break
            i1 = min(n, i1); m_ = i1 - i0
            env = np.sin(np.linspace(0, np.pi, m_)) ** 0.6
            voice = bp(base[i0:i1] * 8, f * 0.9, f * 4.5, 2) * env
            out[i0:i1] += voice
        for c in range(3):
            i = int((t0 + (2.2 + 0.45 * c) * beat) * SR)
            if i >= n: break
            m_ = min(int(0.08 * SR), n - i)
            clap = bp(noise(m_), 900, 4000, 2) * np.exp(-np.arange(m_) / SR * 60)
            out[i:i + m_] += clap * 1.4
    if far: out = lp(out, 2200, 2)
    return out


def glove_clap():
    n = int(0.25 * SR); t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * 140 * t) * np.exp(-t * 40)
    slap = bp(noise(n), 400, 2500, 2) * np.exp(-t * 55)
    return (thump * 0.8 + slap).astype(np.float32)


def rustle(dur=0.5):
    n = int(dur * SR)
    x = bp(noise(n), 1500, 7000, 2) * (0.4 + 0.6 * np.abs(lp(noise(n), 12, 1)) * 3)
    return (x * np.hanning(n)).astype(np.float32)


def hanger():
    n = int(0.4 * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((2300, 14), (3450, 18), (5200, 25)))
    return (x * 0.3).astype(np.float32)


def lace_zip(dur=0.22):
    n = int(dur * SR); t = np.arange(n) / SR
    x = bp(noise(n), 2000, 6000, 2) * (1 + 0.8 * np.sin(2 * np.pi * 90 * t)) * np.sin(np.pi * t / dur) ** 2
    return x.astype(np.float32)


def marker(dur=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 2600 + 400 * np.sin(2 * np.pi * 7 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + bp(noise(n), 3000, 8000, 2) * 0.5
    return (x * np.sin(np.pi * t / dur) ** 0.5).astype(np.float32)


def net_swish():
    n = int(0.5 * SR); t = np.arange(n) / SR
    return (bp(noise(n), 1500, 9000, 2) * np.exp(-t * 7) * np.minimum(1, t / 0.02)).astype(np.float32)


def thud():
    n = int(0.2 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 95 * t) * np.exp(-t * 35) + bp(noise(n), 200, 1500, 2) * np.exp(-t * 60) * 0.5).astype(np.float32)


def ooh(dur=1.0):
    """a crowd 'ooh': a vowel-coloured crowd swell"""
    n = int(dur * SR); t = np.arange(n) / SR
    x = A.crowd_bed(n, 1.0) * 3
    x = bp(x, 250, 900, 2) * 1.6 + x * 0.3
    return (x * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.8).astype(np.float32)


def kick(level=0.8):
    kn = int(0.3 * SR); tt = np.arange(kn) / SR
    return (np.sin(2 * np.pi * (48 + 60 * np.exp(-tt * 35)) * tt) * np.exp(-tt * 8) * level).astype(np.float32)


def pulse(dur, bpm=80):
    """the pre-match pulse: a kick on every beat (every insert cut), a tick between, a low drone"""
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.zeros(n, np.float32)
    beat = 60 / bpm
    for k in range(int(dur / beat) + 1):
        i = int(k * beat * SR)
        if i >= n: break
        kk = kick(0.9 if k % 2 == 0 else 0.7); j = min(n, i + len(kk)); x[i:j] += kk[:j - i]
        ih = int((k + 0.5) * beat * SR)
        if ih < n:
            m_ = min(int(0.05 * SR), n - ih)
            x[ih:ih + m_] += hp(noise(m_), 6000, 2) * np.exp(-np.arange(m_) / SR * 80) * 0.12
    drone = lp(signal.sawtooth(2 * np.pi * 41.2 * t).astype(np.float32) + signal.sawtooth(2 * np.pi * 61.7 * t).astype(np.float32), 260, 2) * 0.12
    drone *= np.clip(t / 2.5, 0, 1)
    return (x + drone) * fade(n, 0.05, 0.25)


# ---------------------------------------------------------------- scene 3
def scene3(fx, mus):
    s3, ins, dr, s4 = m("s3"), m("inserts"), m("dressing"), m("s4")
    # exterior: the crowd builds; a chant from inside the ground; the coach arrives
    n = seg(s3, ins + 0.1)
    build = np.linspace(0.45, 1.0, n) ** 1.5
    fx.add(at(A.crowd_bed(n, 0.5, far=True), -33) * build * fade(n, 0.4, 0.1), s3)
    ch = at(chant(ins - s3 + 0.1), -38)[:n]
    fx.add(ch * fade(len(ch), 0.6, 0.1) * build[:len(ch)], s3, pan=-0.2)
    d = diesel(3.4)
    pan = np.linspace(0.8, 0.0, len(d))
    lvl = np.clip(np.linspace(0.5, 1.0, len(d)), 0, 1)
    dd = at(d, -30) * lvl * fade(len(d), 0.5, 0.35)
    fx.L[int(s3 * SR):int(s3 * SR) + len(dd)] += dd * np.cos((pan + 1) * np.pi / 4) * 1.41
    fx.R[int(s3 * SR):int(s3 * SR) + len(dd)] += dd * np.sin((pan + 1) * np.pi / 4) * 1.41
    fx.add(at(air_brake(), -34), s3 + 3.02, pan=0.05)
    for k in range(5):                                           # fans' footsteps crossing near the lens
        fx.add(at(A.footstep(), -44), s3 + 0.6 + k * 0.55 + RNG.uniform(-0.1, 0.1), pan=RNG.uniform(-0.6, 0.6))
    # the pre-match pulse, kicks on the cuts: from the top of the scene to the dressing room
    mus.add(at(pulse(dr - s3 + 0.4), -27), s3)
    # inserts: the tunnel / dressing-room rumble under them
    n = seg(ins, dr + 0.05)
    fx.add(at(lp(A.crowd_bed(n, 0.6, far=True), 700, 2), -37) * fade(n, 0.05, 0.05), ins)
    b = m("ins_boots"); fx.add(at(A.stud_step(), -27), b + 0.12); fx.add(at(A.stud_step(), -29), b + 0.38, pan=0.2)
    s_ = m("ins_shirts"); fx.add(at(hanger(), -36), s_ + 0.05, pan=-0.3); fx.add(at(rustle(0.5), -38), s_ + 0.1)
    tp = m("ins_tape"); fx.add(at(A.tape_rip(), -27), tp + 0.05); fx.add(at(A.tape_rip(), -30), tp + 0.42)
    g = m("ins_gloves"); fx.add(at(glove_clap(), -22), g + 0.41); fx.add(at(rustle(0.25), -40), g + 0.02)
    w = m("ins_walk")
    for k in range(3):
        st = at(A.footstep(hard=False), -33)
        fx.add(st, w + 0.18 + k * 0.52, pan=0.04 * (-1) ** k)
    c = m("ins_captain")
    for k in range(4):                                           # up on his toes: studs on the tunnel floor
        fx.add(at(A.stud_step(), -32), c + 0.19 + k * 0.385, pan=0.1)
    lc = m("ins_laces"); fx.add(at(lace_zip(), -30), lc + 0.13); fx.add(at(lace_zip(), -31), lc + 0.5)
    bd = m("ins_board"); fx.add(at(marker(0.5), -38), bd + 0.3, pan=-0.3)
    # dressing room: tiles, the crowd through the walls, a shower somewhere
    n = seg(dr - 0.05, s4 + 0.02)
    room = at(lp(noise(n, "brown"), 250, 2), -50) + at(hp(noise(n, "white"), 4000, 2), -64)
    thru = at(lp(A.crowd_bed(n, 0.6, far=True), 330, 2), -41)
    shower = at(bp(noise(n, "pink"), 2000, 9000, 2), -60)
    fx.add((room + thru + shower) * fade(n, 0.03, 0.02), dr - 0.05)
    fx.add(at(A.click(False), -34), dr + 0.8, pan=-0.5)          # a locker door
    fx.add(at(rustle(0.4), -44), dr + 2.2, pan=0.5)
    for wd in ("set", "pieces"):                                  # his finger taps the board
        fx.add(at(A.click(False), -26), W_("ck_set_pieces", wd) + 0.01, pan=-0.3)


# ---------------------------------------------------------------- scene 4
def scene4(fx, mus):
    s4, wh, end = m("s4"), m("whistle"), m("end")
    cut = wh + 0.45                                              # the hard cut to black
    # the stadium: a continuous bed (through the score cards), swelling on the set pieces
    n = seg(s4, cut)
    tt = np.arange(n) / SR + s4
    swell = np.ones(n, np.float32)
    c1, c2 = m("corner1"), m("corner2")
    swell += 0.9 * np.clip((tt - c1) / 0.6, 0, 1) * (tt < c1 + 2.2)
    swell += 1.0 * np.clip((tt - c2) / 0.6, 0, 1) * (tt < c2 + 2.8)
    swell *= 1 - 0.25 * ((tt > m("ck_still")) & (tt < c2))          # Carrick's stillness: the ground settles
    bed = at(A.crowd_bed(n, 1.0), -25) * swell
    bed[-int(0.004 * SR):] *= np.linspace(1, 0, int(0.004 * SR))
    fx.add(bed, s4)
    ch = at(chant(m("corner1") - s4 + 1.0, 124, far=False), -30)
    fx.add(ch * fade(len(ch), 0.3, 0.6), s4, pan=0.15)
    # kick-off
    fx.add(at(A.whistle(0.35, 1), -23), s4 + 0.15, pan=0.2)
    fx.add(at(A.ball_strike(), -30), s4 + 0.35)
    # the corner: the kick, a weak header, the shot, the net, the roar
    fx.add(at(A.ball_strike(), -25), c1 + 0.55, pan=0.3)
    fx.add(at(thud(), -27), c1 + 1.35)
    fx.add(at(A.ball_strike(), -23), c1 + 1.95, pan=-0.1)
    fx.add(at(net_swish(), -26), c1 + 2.18, pan=0.1)
    fx.add(at(A.goal_roar(3.6), -13), c1 + 2.2)
    # the free kick: the whistle, the strike, the pinball, the ooh, over the line
    fx.add(at(A.whistle(0.28, 1), -26), c2 + 0.05, pan=0.2)
    fx.add(at(A.ball_strike(), -25), c2 + 0.55, pan=-0.3)
    for k, tk in enumerate(hull.CHAOS_T[1:-1]):
        fx.add(at(thud(), -26 - 2 * (k % 2)), c2 + tk, pan=RNG.uniform(-0.3, 0.3))
    fx.add(at(ooh(1.3), -21), c2 + 1.45)
    fx.add(at(net_swish(), -28), c2 + 2.75)
    fx.add(at(A.goal_roar(3.4), -13), c2 + 2.8)
    # full time: three blasts ending on the hard cut; the home end goes up
    ft = A.whistle(0.32, 3, 0.16)
    fx.add(at(ft, -20), cut - len(ft) / SR, pan=0.15)
    n2 = seg(cut - 1.4, cut)
    fx.add(at(A.crowd_bed(n2, 1.0), -22) * np.linspace(0.3, 1.2, n2).astype(np.float32), cut - 1.4)
    # the hard cut: nothing after it (scene 5 starts in silence)
    for bus in (fx, mus):
        i = int(cut * SR)
        bus.L[i:int(end * SR) + SR] = 0; bus.R[i:int(end * SR) + SR] = 0


def add(fx, mus):
    scene3(fx, mus)
    scene4(fx, mus)

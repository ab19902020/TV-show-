"""The Undercard's soundtrack: the voices (the two lines from inside the bin muffled), the room of each set (the
press area's hum, the loading bay's wet night, the corridor's machinery, the arena crowd dipping under every line),
the foley the picture asks for (trolley wheels squeaking with one wobbly wheel, towels, the lid, the bump and the
tumble, footsteps, the bell, the glove squeak, breathing in the clinch, a cough in the silent face-off), a two-second
sting before the announcer, and fight music that stops dead at the first embarrassing glove tap.
python3 -m studio.film the-undercard sound -> build/episode_audio.wav (-16 LUFS)"""
import json
import math

import numpy as np
import soundfile as sf

from studio.film import audio as A
from studio.film import ep
from studio.film.shots import Marks

from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le = T.m, T.ls, T.le
SR = A.SR
MUFFLED = {"L010": 900, "L058": 1100}           # from inside the bin: the towels take the top off
WHISPER = {"L014"}


def dialogue(bus):
    ir = A.reverb_ir(0.32, 5600, 0.006, 11)
    for lid, v in TL["lines"].items():
        y, _ = sf.read(str(ep.path("lines", f"{lid}.wav")), dtype="float32")
        if y.ndim > 1:
            y = y.mean(1)
        y = A.hp(y, 75, 2).astype(np.float32)
        lvl = -20.0
        if lid in MUFFLED:
            y = A.lp(y, MUFFLED[lid], 4).astype(np.float32)
            lvl = -24.0
        if lid in WHISPER:
            lvl = -23.0
        y = np.clip(A.at_level(y, lvl), -0.95, 0.95)
        bus.add(y, v["start"])
        bus.add(A.convolve_st(y, ir), v["start"], A.db(-23 if v["start"] < m("c_arena") else -17))


def tone(f, dur, decay, harm=((1, 1.0),), sr=SR):
    t = np.arange(int(dur * sr)) / sr
    y = sum(a * np.sin(2 * math.pi * f * k * t) * np.exp(-t * decay * (1 + 0.4 * k)) for k, a in harm)
    return (y * np.minimum(1, t / 0.002)).astype(np.float32)


def bell(n=3):
    """the ring bell: a struck brass bell, rung n times"""
    one = tone(1180, 1.6, 2.2, ((1, 1.0), (2.76, 0.55), (5.4, 0.3), (8.9, 0.12)))
    out = np.zeros(int((0.28 * (n - 1) + 1.7) * SR), np.float32)
    for i in range(n):
        a = int(0.28 * i * SR)
        out[a:a + len(one)] += one
    return A.room(out, 1.2, 0.3)


def cough():
    rng = np.random.default_rng(5)
    out = np.zeros(int(0.7 * SR), np.float32)
    for st, d, g in ((0.0, 0.16, 1.0), (0.24, 0.12, 0.7)):
        n = int(d * SR)
        x = rng.standard_normal(n).astype(np.float32)
        x = A.bp(x, 250, 1800, 2).astype(np.float32)
        env = np.exp(-np.arange(n) / (0.045 * SR)) * np.minimum(1, np.arange(n) / (0.004 * SR))
        out[int(st * SR):int(st * SR) + n] += x * env * g
    return A.room(out, 1.6, 0.45)


def squeaks(bus, t0, t1, level, every=0.42, pan=0.0, pan_to=None):
    """the trolley's wobbly wheel"""
    k, t = 0, t0
    while t < t1:
        p = pan if pan_to is None else pan + (pan_to - pan) * (t - t0) / max(1e-3, t1 - t0)
        A.ev(bus, "creaks/creak-small", t, level - (k % 3) * 1.5, pan=p, semis=9 + 2 * (k % 2), highpass=900, dur=0.18)
        k += 1
        t += every * (0.9 + 0.2 * ((k * 7) % 3) / 2)


def crowd_gain(a, b, base=1.0, dip=0.35):
    """the crowd: dips under every line inside [a, b]"""
    spans = [(v["start"] - 0.15, v["end"] + 0.2) for v in TL["lines"].values() if a <= v["start"] < b]

    def g(tt):
        out = np.full_like(tt, base, dtype=np.float32)
        for s0, s1 in spans:
            r = np.clip(np.minimum((tt - s0) / 0.25, (s1 - tt) / 0.35), 0, 1)
            out = out * (1 - (1 - dip) * r)
        return out
    return g


def ambience(bus):
    A.bed(bus, "ambience/room-tone-hvac", m("open"), m("c_bay"), -50, lowpass=3000, fin=0.3)
    A.bed(bus, "crowd/crowd-large", m("open"), m("c_bay"), -44, lowpass=900, fin=0.3)      # the arena, beyond the wall
    A.bed(bus, "ambience/rain-concrete", m("c_bay"), m("c_track"), -46, lowpass=5000)
    A.bed(bus, "ambience/street-distant", m("c_bay"), m("c_track"), -44)
    A.bed(bus, "ambience/room-tone-hvac", m("c_track"), m("c_arena"), -44, lowpass=2400)
    A.bed(bus, "crowd/crowd-large", m("c_track"), m("c_prep"), -48, lowpass=600)
    A.bed(bus, "crowd/crowd-large", m("c_prep"), m("c_arena"), -46, lowpass=700)
    # the arena: crowd swell under the sting, dips under every line, near silence for the face-off
    a, b = m("c_arena"), m("black")
    g0 = crowd_gain(a, b)

    def g(tt):
        out = g0(tt)
        out *= np.interp(tt, [a, a + 1.6, m("faceoff"), m("faceoff") + 0.3, m("c_ty1") - 0.1, m("c_ty1") + 0.6],
                         [0.3, 1.0, 1.0, 0.12, 0.12, 0.8])
        out *= np.interp(tt, [m("c_end"), m("black")], [1.0, 0.4])
        return out
    A.bed(bus, "crowd/crowd-large", a, b, -27, gain_fn=g, fin=0.6, fout=0.05)
    A.bed(bus, "crowd/applause-big", ls("L035") + 0.3, m("c_ref") - 0.2, -30, fin=0.4, fout=0.6,
          gain_fn=lambda tt: np.interp(tt, [le("L035") - 0.6, le("L035"), m("c_ann3") + 0.3, le("L036"), le("L036") + 1.5],
                                       [0.0, 1.0, 0.2, 0.0, 1.0]))


def foley(bus):
    # the press area: Eddie's shoes, a camera shutter-ish click
    A.ev(bus, "cloth/cloth-a", A_T("L001", "not") - 0.12, -44, pan=-0.1)
    # the loading bay: the trolley rolls past, left to right, and the attendant's steps
    squeaks(bus, m("trolley") - 0.3, m("look_cam") + 0.5, -36, pan=-0.8, pan_to=0.8)
    A.steps(bus, m("trolley") - 0.2, m("look_cam") + 0.4, -42, pace=0.42, pan=-0.7, pan_to=0.7)
    # the shoe under the towels
    A.ev(bus, "cloth/cloth-c", m("c_shoe") + 0.2, -34)
    A.ev(bus, "cloth/cloth-e", m("c_shoe") + 0.7, -32)
    A.ev(bus, "cloth/cloth-b", m("c_shoe") + 0.95, -34)
    # the corridor: in, stop at security; the lid; on past him
    squeaks(bus, m("c_track"), m("c_track") + 1.7, -33, pan=-0.6, pan_to=0.0)
    A.steps(bus, m("c_track"), m("c_track") + 1.7, -42, pace=0.4, pan=-0.5, pan_to=0.0)
    A.ev(bus, "cloth/cloth-d", ls("L010") + 0.05, -38)
    A.ev(bus, "cloth/cloth-f", le("L010") - 0.1, -40)
    A.ev(bus, "foley/cup-down", m("lid") + 0.6, -32, semis=-9, lowpass=3000)
    A.ev(bus, "foley/pen-click-b", m("lid") + 0.62, -38, semis=-12)
    squeaks(bus, m("aside"), m("bump"), -34, pan=0.0, pan_to=0.4)
    A.steps(bus, m("aside"), m("bump"), -43, pace=0.42, pan=-0.1, pan_to=0.3)
    # the cable protector: the bump, the freeze, the tumble, the landing
    A.ev(bus, "impacts/tom-hit", m("bump"), -24, semis=-5)
    A.ev(bus, "foley/cup-down", m("bump") + 0.02, -30, semis=-14)
    A.ev(bus, "cloth/cloth-a", m("tumble") + 0.05, -32)
    A.ev(bus, "cloth/cloth-e", m("tumble") + 0.5, -32)
    A.ev(bus, "impacts/tom-hit", m("tumble") + 1.1, -22, semis=-9)
    A.ev(bus, "cloth/cloth-b", m("tumble") + 1.15, -30)
    A.ev(bus, "cloth/cloth-c", m("landed") + 0.6, -36)
    # Eddie walks in, stops
    A.steps(bus, m("c_eddie"), m("c_eddie") + 1.8, -38, pace=0.5, pan=-0.6, pan_to=-0.2)
    A.ev(bus, "cloth/cloth-d", m("c_eddie") + 1.2, -40)                     # Dana gets up
    A.ev(bus, "cloth/cloth-f", m("c_neg") + 0.4, -38)                       # the towel taken off
    A.ev(bus, "cloth/cloth-a", m("c_neg") + 1.05, -40)                      # and dropped
    # the dressing room: shadowboxing, then catching his breath
    for i in range(12):
        A.ev(bus, "cloth/cloth-%s" % "abcdef"[i % 6], m("c_prep") + 0.18 + 0.2 * i, -42, pan=0.35, dur=0.15)
    # the fight
    bus.add(A.at_level(bell(3), -20), m("bell") + 0.05)
    bus.add(A.at_level(cough(), -33), m("cough") + 0.1, 1.0, 0.4)
    A.ev(bus, "footsteps/step-a", m("faceoff") + 0.5, -46, pan=-0.3)
    A.ev(bus, "footsteps/step-b", m("faceoff") + 1.4, -46, pan=0.3)
    A.ev(bus, "cloth/cloth-b", m("ex1") + 0.5, -36, pan=-0.2)
    A.ev(bus, "cloth/cloth-e", m("ex1") + 0.8, -36, pan=0.3)
    A.ev(bus, "cloth/cloth-a", m("ex2") + 0.25, -36, pan=0.2)
    A.ev(bus, "creaks/creak-small", m("ex2") + 0.42, -26, semis=14, highpass=1200, dur=0.2)   # the glove squeak
    A.ev(bus, "cloth/cloth-c", m("ex3a") + 0.3, -36)
    A.ev(bus, "cloth/cloth-d", m("ex3b") + 0.4, -34)
    A.ev(bus, "cloth/cloth-f", m("ex3c") + 0.6, -34)
    A.ev(bus, "cloth/cloth-a", m("sep") + 0.1, -36)
    A.ev(bus, "cloth/cloth-b", m("sep") + 1.4, -36)
    bus.add(A.at_level(bell(3), -20), m("bell2") + 0.05)
    # the exit: the trolley comes in, the climb, the roll-out, and the last squeak
    squeaks(bus, m("c_trolley"), m("c_trolley") + 2.0, -33, pan=-0.7, pan_to=0.0)
    A.ev(bus, "cloth/cloth-c", m("climb") + 0.6, -32)
    A.ev(bus, "cloth/cloth-e", m("climb") + 1.1, -32)
    squeaks(bus, m("rollout"), m("c_end") + 1.0, -32, pan=0.0, pan_to=0.9)
    A.ev(bus, "creaks/creak-small", m("c_end") + 1.2, -30, semis=11, highpass=900, dur=0.25, pan=0.9)


def A_T(lid, word):
    return T.wt(lid, word)


def music(bus):
    # the sting before the announcer: a swelling chord, two seconds
    y = A.title_sting(2.6)
    y *= A.fade(len(y), 0.25, 0.5)[:, None]
    bus.add(A.at_level(y, -22), m("c_arena"))
    # the title card
    y = A.title_sting(3.0)
    y *= A.fade(len(y), 0.05, 0.8)[:, None]
    bus.add(A.at_level(y, -24), 0.0)
    bus.add(A.at_level(A.big_boom(0.8), -18), 0.05)
    # fight music: a drum pulse from the bell to the first glove tap, then nothing
    a, b = m("bell") + 0.6, m("ex2") + 0.42
    t = a
    k = 0
    while t < b:
        A.ev(bus, "impacts/tom-hit", t, -30 if k % 2 == 0 else -36, semis=-3 if k % 4 else -1)
        k += 1
        t += 0.4


def main():
    dlg, amb, fx, mus = A.Bus(), A.Bus(), A.Bus(), A.Bus()
    dialogue(dlg)
    ambience(amb)
    foley(fx)
    music(mus)
    A.master(dlg, [amb, fx], [mus])

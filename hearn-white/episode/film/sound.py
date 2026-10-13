"""The Undercard's soundtrack (v5): the voices (Dana's boast from inside the bin muffled), each set's room, the foley
the picture asks for (the tape, the trolley's wheels and brake, the shoes, the lid, the fall told as a chain of
sounds: the wheel's knock, the lid, the cloth, the landing, the shoes skidding on), and an arena that reacts: the bed
dips under every line, swells for the entrance, laughs at the ducking and the towel, goes quiet when nobody throws
anything (one cough), and gives the glove clash and the sit-down their moment. A fanfare at the bell that stops
dead when the bouncing does; a sting under the title and the end title. Real boxing bells, punches, whooshes and
body falls (library/audio/sfx, CC0).
python3 -m studio.film the-undercard sound -> build/episode_audio.wav (-16 LUFS)"""
import json
import math

import numpy as np
import soundfile as sf

from studio.film import audio as A
from studio.film import ep
from studio.film.shots import Marks

from film import crowdfx as C
from film.direction import E, Dn, DK, EK
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt = T.m, T.ls, T.le, T.wt
SR = A.SR
MUFFLED = {"L017": 900}                      # from inside the bin: the towels take the top off
ARENA = m("c_arena")


def dialogue(bus):
    ir = A.reverb_ir(0.32, 5600, 0.006, 11)
    ir_big = A.reverb_ir(1.1, 4800, 0.015, 12)
    for lid, v in TL["lines"].items():
        y, _ = sf.read(str(ep.path("lines", f"{lid}.wav")), dtype="float32")
        if y.ndim > 1:
            y = y.mean(1)
        y = A.hp(y, 75, 2).astype(np.float32)
        lvl = -20.0
        if lid in MUFFLED:
            y = A.lp(y, MUFFLED[lid], 4).astype(np.float32)
            lvl = -23.0
        if lid in ("L060", "L018"):                  # whispered, hissed
            lvl = -22.0
        y = np.clip(A.at_level(y, lvl), -0.95, 0.95)
        bus.add(y, v["start"])
        arena = v["start"] >= ARENA
        bus.add(A.convolve_st(y, ir_big if v["speaker"] in ("announcer",) else ir), v["start"],
                A.db(-15 if v["speaker"] == "announcer" else (-19 if arena else -23)))


def put(bus, y, t, level, pan=0.0):
    if y.ndim == 2:
        y = y.mean(1) if pan else y
    bus.add(A.at_level(y, level), t, 1.0, pan)


def squeaks(bus, t0, t1, level, every=0.42, pan=0.0, pan_to=None):
    """the trolley's wobbly wheel"""
    k, t = 0, t0
    while t < t1:
        p = pan if pan_to is None else pan + (pan_to - pan) * (t - t0) / max(1e-3, t1 - t0)
        A.ev(bus, "creaks/creak-small", t, level - (k % 3) * 1.5, pan=p, semis=9 + 2 * (k % 2), highpass=900, dur=0.18)
        k += 1
        t += every * (0.9 + 0.2 * ((k * 7) % 3) / 2)


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


# ---------------------------------------------------------------- cartoon sounds (made here: the library has none)
def slide_whistle(f0, f1, dur, vib=5.5):
    """a slide whistle gliding from f0 to f1 Hz: breathy sine with a wobble"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur) * (1 + 0.012 * np.sin(2 * np.pi * vib * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    rng = np.random.default_rng(3)
    y = np.sin(ph) + 0.08 * np.sin(2 * ph) + 0.05 * A.bp(rng.standard_normal(n).astype(np.float32), 600, 4000, 2)
    return (y * A.fade(n, 0.03, 0.08)).astype(np.float32)


def tweets(dur, seed=4):
    """little birds circling a knocked-out head: quick rising chirps in pairs"""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    t = 0.05
    while t < dur - 0.2:
        for k in range(rng.integers(2, 4)):
            d = rng.uniform(0.06, 0.09)
            m_ = int(d * SR)
            tt = np.arange(m_) / SR
            f = rng.uniform(2600, 3400) * (1 + 0.5 * tt / d)
            ch = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * tt / d) ** 2
            i = int((t + k * 0.1) * SR)
            if i + m_ < n:
                out[i:i + m_] += ch.astype(np.float32) * rng.uniform(0.6, 1.0)
        t += rng.uniform(0.38, 0.55)
    return out


def boing(dur=0.6, f=180.0):
    """a cartoon spring: a twangy tone bending down with a fast wobble"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    fr = f * (1.6 - 0.6 * t / dur) * (1 + 0.18 * np.sin(2 * np.pi * 14 * t) * np.exp(-t / 0.25))
    ph = 2 * np.pi * np.cumsum(fr) / SR
    y = (np.sin(ph) + 0.35 * np.sin(2 * ph) + 0.15 * np.sin(3 * ph)) * np.exp(-t / (0.35 * dur))
    return (y * A.fade(n, 0.003, 0.05)).astype(np.float32)



def tape_peel(dur=0.38, seed=9):
    """parcel tape pulled off a board: a dense crackle that thins out"""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    out = np.zeros(n, np.float32)
    t = 0
    while t < n - 200:
        k = int(rng.integers(40, 160))
        burst = rng.standard_normal(k).astype(np.float32) * np.hanning(k).astype(np.float32)
        out[t:t + k] += burst * rng.uniform(0.4, 1.0)
        t += int(rng.integers(30, 90) * (1 + 2.5 * t / n))
    out = A.bp(out, 900, 7000, 2).astype(np.float32)
    return out * A.fade(n, 0.005, 0.08)


# ---------------------------------------------------------------- the arena crowd
LOUD = [("bounce", "slow"), ("probe", "c_da2"), ("tap", "c_da3"), ("counter", "c_ed_ind"), ("advance", "clinch"),
        ("windup", "look"), ("bell2", "c_ann4")]


def crowd_gain(a, b):
    """the bed: dips under every line, near silence when nobody throws anything, up for the action"""
    spans = [(v["start"] - 0.15, v["end"] + 0.2) for v in TL["lines"].values() if a <= v["start"] < b]
    action = [(m(x), m(y)) for x, y in LOUD]

    def g(tt):
        out = np.ones_like(tt)
        for s0, s1 in spans:
            out = np.minimum(out, np.interp(tt, [s0 - 0.25, s0, s1, s1 + 0.35], [1.0, 0.42, 0.42, 1.0]))
        for s0, s1 in action:
            out = np.maximum(out, np.interp(tt, [s0, s0 + 0.3, s1 - 0.2, s1], [0.0, 1.25, 1.25, 0.0]) * (out > 0))
        out *= np.interp(tt, [m("slow") + 0.3, m("silence2"), m("c_ty1"), m("c_ty1") + 0.8], [1.0, 0.18, 0.18, 1.0])
        out *= np.interp(tt, [m("clinch"), m("clinch") + 1.0, m("c_aj2"), m("sep")], [1.0, 0.55, 0.55, 1.0])
        out *= np.interp(tt, [m("look"), m("look") + 0.1, m("bell2"), m("bell2") + 0.1], [1.0, 0.35, 0.35, 1.0])
        out *= np.interp(tt, [m("c_steps"), m("c_bin") + 0.5, m("black")], [1.0, 0.55, 0.3])
        return out
    return g


def ambience(bus):
    A.bed(bus, "ambience/room-tone-hvac", m("open"), m("c_bay"), -50, lowpass=3000, fin=0.3)
    A.bed(bus, "crowd/crowd-large", m("open"), m("c_bay"), -44, lowpass=900, fin=0.3)      # the arena, beyond the wall
    A.bed(bus, "ambience/street-distant", m("c_bay"), m("c_inbin"), -44)
    A.bed(bus, "ambience/rain-concrete", m("c_bay"), m("c_inbin"), -47, lowpass=5000)
    A.bed(bus, "ambience/street-distant", m("c_inbin"), m("c_check"), -50, lowpass=500)     # heard through the bin
    A.bed(bus, "ambience/room-tone-hvac", m("c_check"), ARENA, -44, lowpass=2400)
    A.bed(bus, "crowd/crowd-large", m("c_check"), ARENA, -48, lowpass=650)
    A.bed(bus, "crowd/crowd-large", ARENA, m("black"), -26, gain_fn=crowd_gain(ARENA, m("black")), fin=0.8, fout=0.05)


def reactions(bus):
    put(bus, C.cheer(3.0, seed=40), ARENA + 0.3, -26)
    put(bus, C.laugh(2.0, seed=41), m("ropes") + 0.4, -30)               # ducking through the ropes, badly
    put(bus, C.cheer(2.2, seed=42), le("L044") + 0.05, -26)
    put(bus, C.laugh(2.4, seed=43), le("L045") - 0.4, -27)               # "...by laundry delivery"
    put(bus, C.laugh(1.8, seed=44), m("towel") + 0.9, -30)               # can't grab the towel in gloves
    put(bus, C.cheer(2.4, seed=45), m("bounce") + 0.1, -26)
    put(bus, C.laugh(2.4, seed=46), le("L048") + 0.05, -27)
    put(bus, C.roar(1.4, seed=47), m("probe") + 0.6, -28)
    put(bus, C.laugh(2.2, seed=48), m("probe") + 1.0, -28)               # the duck
    put(bus, C.laugh(1.6, seed=49), m("tap") + 1.25, -31)
    put(bus, C.laugh(2.0, seed=50), le("L054") + 0.1, -30)
    put(bus, C.laugh(2.4, seed=51), le("L057") + 0.05, -27)              # the photos
    put(bus, C.roar(2.0, seed=52, cheer=0.6), m("advance") + 0.4, -25)
    put(bus, C.roar(1.4, seed=53), m("ropes2") + 0.05, -26)
    put(bus, C.laugh(2.6, seed=54), m("clinch") + 0.2, -29)
    put(bus, C.laugh(2.4, seed=55), le("L068") + 0.05, -28)
    put(bus, C.roar(2.2, seed=56, cheer=0.9), m("windup") + 0.3, -24)
    put(bus, C.roar(1.6, seed=57, cheer=1.0), m("clash") + 0.05, -21)
    put(bus, C.laugh(3.2, people=24, seed=58), m("sit") + 0.35, -24)     # both sit down
    put(bus, C.cheer(2.6, seed=59), m("bell2") + 0.2, -27)
    put(bus, C.laugh(2.0, seed=60), le("L069") + 0.05, -29)
    put(bus, C.laugh(2.2, seed=61), le("L071") + 0.05, -29)


def fight(bus):
    bell = A.clip("sport/boxing-bell")
    bell = bell.mean(1) if bell.ndim == 2 else bell
    put(bus, A.room(bell, 1.2, 0.3), m("bell") + 0.03, -19)
    put(bus, A.room(bell, 1.2, 0.3), m("bell2") + 0.03, -19)
    whooshes = ["whoosh/whoosh-a", "whoosh/whoosh-b", "whoosh/whoosh-c", "whoosh/whoosh-d"]
    for k, (t, kind, reach) in enumerate(sorted(E.sfx + Dn.sfx + EK.sfx + DK.sfx)):
        name = whooshes[k % 4]
        if kind == "whoosh_slow":
            y = A.varispeed(A.clip(name).mean(1) if A.clip(name).ndim == 2 else A.clip(name), -9.0)
            put(bus, y, t - 0.15, -27, pan=-0.2 if k % 2 else 0.2)
        else:
            A.ev(bus, name, t, -29 if reach > 80 else -32, pan=-0.25 if k % 2 else 0.25,
                 semis=1.5 if reach < 70 else -1.0)
    A.steps(bus, m("bounce"), m("slow") + 0.8, -38, pace=0.48, lowpass=1800)     # bouncing on the canvas
    A.ev(bus, "cloth/cloth-c", m("probe") + 0.45, -33)                          # the duck
    # the glove contacts: a soft pop and a leather squeak, never a smack
    for t in (m("tap") + 0.29, m("tap") + 0.89, m("counter") + 0.31):
        A.ev(bus, "impacts/punch-c", t, -29, lowpass=2600)
        A.ev(bus, "creaks/creak-small", t + 0.01, -27, semis=14, highpass=1200, dur=0.18)
    A.steps(bus, m("advance") + 0.1, m("ropes2") - 0.1, -36, pace=0.28, lowpass=2000)
    A.ev(bus, "creaks/creak-long", m("ropes2") + 0.02, -24, semis=-3, dur=0.7)  # the ropes take his weight
    put(bus, boing(0.55, 150), m("ropes2") + 0.3, -27)
    A.ev(bus, "whoosh/whoosh-b", m("recoil") + 0.05, -27, semis=-2)
    A.ev(bus, "foley/body-fall-b", m("clinch") - 0.02, -30)
    A.ev(bus, "cloth/cloth-e", m("clinch") + 0.05, -32)
    A.ev(bus, "cloth/cloth-a", m("lift") + 0.02, -33)
    A.ev(bus, "cloth/cloth-b", m("lift") + 0.42, -33)
    A.ev(bus, "cloth/cloth-f", m("sep") + 0.3, -31)
    # the glove clash: the one big contact
    A.ev(bus, "impacts/punch-a", m("clash"), -17)
    A.ev(bus, "impacts/punch-d", m("clash") + 0.01, -22, semis=-4, lowpass=3000)
    A.ev(bus, "creaks/creak-short", m("wobble") + 0.1, -30, semis=-6)
    put(bus, slide_whistle(900, 260, 0.5), m("sit") - 0.05, -31)
    for d, nm, pn in ((0.22, "foley/body-fall-a", -0.3), (0.24, "foley/body-fall-b", 0.3)):
        A.ev(bus, nm, m("sit") + d, -21, pan=pn)                                 # two bottoms, one thump
    A.ev(bus, "cloth/cloth-c", m("helpup") + 0.3, -32)
    A.ev(bus, "cloth/cloth-d", m("helpup") + 0.6, -32)


def foley(bus):
    from film import direction as D
    # the press area: the tape, his shoes stepping back
    put(bus, tape_peel(), m("tape") + 0.2, -27)
    A.ev(bus, "paper/paper-short", m("admire") - 0.12, -36)
    A.steps(bus, m("admire"), m("admire") + 0.9, -38, pace=0.42)
    # the bay: the trolley in, her steps, the brake
    squeaks(bus, D.tb0, D.tb1, -35, pan=-0.8, pan_to=0.1)
    A.steps(bus, D.tb0, D.tb1, -41, pace=0.48, pan=-0.7, pan_to=0.0)
    A.steps(bus, D.tb0, D.tb1, -43, pace=0.47, pan=-0.8, pan_to=0.3)          # Dana alongside
    A.ev(bus, "impacts/tom-hit", D.tb1, -31, semis=-12, lowpass=900)          # the brake: clunk
    A.ev(bus, "foley/cup-down", D.tb1 + 0.02, -31, semis=-14)
    ts = m("shoes")
    for t in (ts + 0.1, ts + 1.15):
        A.ev(bus, "cloth/cloth-b", t, -36)
    for t in (ts + 0.68, ts + 1.73):
        A.ev(bus, "foley/cup-down", t, -30, semis=-10, lowpass=1500)          # a shoe into the towels
    A.ev(bus, "footsteps/step-a", ts + 0.55, -38)
    A.ev(bus, "footsteps/step-b", ts + 0.8, -38)
    A.ev(bus, "cloth/cloth-c", m("climb_in") + 0.3, -32)
    A.ev(bus, "foley/body-fall-b", m("climb_in") + 0.85, -33, lowpass=1500)
    A.ev(bus, "doors/door-shut", m("climb_in") + 1.25, -34, lowpass=2500)     # the lid
    # inside the bin
    A.ev(bus, "cloth/cloth-a", m("c_inbin") + 0.2, -30)
    A.ev(bus, "doors/door-shut", m("c_inbin") + 1.25, -28, lowpass=700)
    # the checkpoint
    squeaks(bus, D.tq0, D.tq1, -34, pan=0.8, pan_to=0.1)
    A.steps(bus, D.tq0, D.tq1, -41, pace=0.5, pan=0.7, pan_to=0.1)
    A.ev(bus, "creaks/creak-mid", m("c_lid") + 0.05, -31, semis=4)            # she leans on the lid
    A.steps(bus, D.tg - 0.3, D.tg + 0.5, -40, pace=0.45, pan=-0.2)            # he steps aside
    squeaks(bus, D.tg, D.tg + 2.0, -35, pan=0.1, pan_to=-0.8)
    A.steps(bus, D.tg, D.tg + 2.0, -42, pace=0.5, pan=0.1, pan_to=-0.7)
    # the delivery
    squeaks(bus, D.tr0 - 0.2, D.t_hit, -33, pan=-0.6, pan_to=0.0)
    A.steps(bus, D.tr0 - 0.2, D.t_hit, -41, pace=0.45, pan=-0.5, pan_to=0.0)
    A.ev(bus, "impacts/tom-hit", D.t_hit, -24, semis=-5)                      # the wheel hits the ramp
    A.ev(bus, "foley/cup-down", D.t_hit + 0.02, -29, semis=-14)
    A.ev(bus, "footsteps/step-b", D.t_br + 0.02, -33)                         # her braced foot
    A.ev(bus, "cloth/cloth-e", D.t_br + 0.1, -31)                             # the towels lurch
    A.ev(bus, "creaks/creak-short", D.t_br + 0.15, -30, semis=2)              # the lid flips
    A.ev(bus, "cloth/cloth-a", D.t_gr + 0.1, -32)                             # the grab
    A.ev(bus, "whoosh/whoosh-b", D.t_tu + 0.05, -30, semis=-3)
    A.ev(bus, "foley/body-fall-a", D.t_la, -25)
    A.ev(bus, "cloth/cloth-b", D.t_la + 0.06, -31)
    A.ev(bus, "foley/cup-down", D.t_la + 0.06, -31, semis=-8)                 # the shoes land and skid
    A.ev(bus, "paper/paper-short", D.t_la + 0.1, -37, semis=-6)
    A.ev(bus, "foley/cup-down", D.t_la + 0.11, -33, semis=-6)
    A.ev(bus, "paper/paper-short", D.t_la + 0.2, -38, semis=-8)
    A.ev(bus, "cloth/cloth-d", D.t_la + 0.36, -33)                            # the towel lands on his head
    A.ev(bus, "footsteps/step-a", D.t_la + 0.05, -36)                         # Fury steps back
    A.ev(bus, "footsteps/step-b", D.t_la + 0.25, -37)
    A.steps(bus, D.aj_t0, D.aj_t0 + 0.8, -41, pace=0.45, pan=0.8, pan_to=0.5)  # Joshua
    A.steps(bus, m("c_eddie") + 0.05, m("c_eddie") + 1.25, -38, pace=0.5, pan=-0.6, pan_to=-0.3)
    A.steps(bus, ls("L025") + 0.1, ls("L026") - 0.15, -40, pace=0.45, pan=-0.3, pan_to=0.0)
    A.ev(bus, "paper/paper-handle", m("pays") + 0.25, -33)                    # the notes
    A.ev(bus, "paper/paper-short", m("pays") + 1.2, -34)
    A.steps(bus, ls("L032") - 0.2, ls("L032") + 0.2, -39, pace=0.2)            # Dana steps in
    # preparation
    A.ev(bus, "whoosh/whoosh-a", m("c_jacket") + 0.1, -31, semis=4)
    A.ev(bus, "cloth/cloth-e", m("c_jacket") + 0.15, -33)
    A.ev(bus, "creaks/creak-small", m("c_strap") + 0.12, -28, semis=6, highpass=900, dur=0.2)   # the strap
    A.ev(bus, "cloth/cloth-b", m("c_strap") + 0.1, -33)
    t_ph = wt("L036", "both")
    A.ev(bus, "foley/cup-down", t_ph + 0.45, -32, semis=6)                    # the phone hits the floor
    # the arena: the ropes, the towel
    A.ev(bus, "cloth/cloth-c", m("ropes") + 0.2, -34)
    A.ev(bus, "cloth/cloth-a", m("ropes") + 0.35, -34)
    A.ev(bus, "cloth/cloth-d", m("towel") + 0.3, -33)
    bus.add(A.at_level(cough(), -30), m("silence2") + 0.45, 1.0, 0.4)
    # the exit: down the steps, the bin, the card, in he goes, off they go
    A.steps(bus, m("c_steps"), m("c_bin") + 0.5, -38, pace=0.32)
    A.ev(bus, "paper/paper-handle", m("card") + 0.03, -30)
    A.ev(bus, "foley/clap-single", m("card") + 0.05, -29)                     # the card slapped on
    A.ev(bus, "cloth/cloth-c", m("climb2") + 0.6, -32)
    A.ev(bus, "foley/body-fall-b", m("climb2") + 1.05, -33, lowpass=1500)
    A.ev(bus, "doors/door-shut", m("climb2") + 1.4, -33, lowpass=2500)
    squeaks(bus, m("depart") - 0.1, m("black") + 0.3, -32, pan=-0.2, pan_to=0.9)
    A.steps(bus, m("depart") - 0.1, m("black"), -41, pace=0.5, pan=-0.2, pan_to=0.8)


def music(bus):
    # under the series title
    y = A.title_sting(2.6)
    y *= A.fade(len(y), 0.05, 0.8)[:, None]
    bus.add(A.at_level(y, -27), m("open") + 0.3)
    # two seconds of sting before the announcer
    y = A.title_sting(2.4)
    y *= A.fade(len(y), 0.25, 0.5)[:, None]
    bus.add(A.at_level(y, -22), ARENA)
    # the fanfare at the bell: drums under the confident bouncing, gone the moment Dana slows
    t, k = m("bell") + 0.5, 0
    while t < m("slow") + 0.2:
        A.ev(bus, "impacts/tom-hit", t, -28 if k % 2 == 0 else -34, semis=-3 if k % 4 else -1)
        k += 1
        t += 0.36
    # the end title
    y = A.title_sting(2.8)
    y *= A.fade(len(y), 0.1, 0.9)[:, None]
    bus.add(A.at_level(y, -25), m("depart") + 0.4)


def main():
    dlg, amb, fx, mus = A.Bus(), A.Bus(), A.Bus(), A.Bus()
    dialogue(dlg)
    ambience(amb)
    reactions(amb)
    fight(fx)
    foley(fx)
    music(mus)
    A.master(dlg, [amb, fx], [mus])

"""The Undercard's soundtrack: the voices (the two lines from inside the bin muffled), each set's room, the foley the
picture asks for, and an arena that reacts: the crowd bed dips under every line, swells ("roars") on near misses and
the one real hit, cheers the introductions, laughs at the windmill, the spin and the slow-motion double miss, and goes
quiet for the face-off (one cough). Real boxing bells, punches, whooshes and body falls (library/audio/sfx, CC0), a
two-second sting before the announcer, and fight music that stops dead at the first embarrassing glove tap.
python3 -m studio.film the-undercard sound -> build/episode_audio.wav (-16 LUFS)"""
import json
import math

import numpy as np
import soundfile as sf

from studio.film import audio as A
from studio.film import ep
from studio.film.shots import Marks

from film import crowdfx as C
from film.direction import SB, SLUG, Dn, E
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt = T.m, T.ls, T.le, T.wt
SR = A.SR
MUFFLED = {"L010": 900, "L058": 1100}           # from inside the bin: the towels take the top off
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
            lvl = -24.0
        if lid == "L014":
            lvl = -22.5
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


# ---------------------------------------------------------------- the arena crowd
def crowd_gain(a, b):
    """the bed: dips under every line, near silence for the face-off, up for the action"""
    spans = [(v["start"] - 0.15, v["end"] + 0.2) for v in TL["lines"].values() if a <= v["start"] < b]
    action = [(m("ex1"), m("c_ed7")), (m("c_ex3"), m("c_cl1")), (m("slug"), m("dko")), (m("bell2"), m("c_ann4"))]

    def g(tt):
        out = np.ones_like(tt, dtype=np.float32)
        for s0, s1 in spans:
            r = np.clip(np.minimum((tt - s0) / 0.25, (s1 - tt) / 0.35), 0, 1)
            out = out * (1 - 0.62 * r)
        for s0, s1 in action:
            r = np.clip(np.minimum((tt - s0) / 0.3, (s1 - tt) / 0.4), 0, 1)
            out = out * (1 + 0.5 * r)
        out *= np.interp(tt, [a, a + 1.6, m("faceoff"), m("faceoff") + 0.3, m("c_ty1") - 0.1, m("c_ty1") + 0.6],
                         [0.3, 1.0, 1.0, 0.1, 0.1, 0.8])
        # slow motion: the room drops away while the haymakers swing
        out *= np.interp(tt, [m("ex3d"), m("ex3d") + 0.3, m("ex3d") + 1.5, m("ex3d") + 1.8], [1.0, 0.35, 0.35, 1.0])
        # the wind-up: the room holds its breath; the freeze on the impact; then it erupts
        out *= np.interp(tt, [m("dko"), m("dko") + 0.25, m("impact"), m("impact") + 0.05, m("impact") + 0.35,
                              m("fall") + 0.5], [1.0, 0.35, 0.35, 0.05, 0.05, 1.4])
        out *= np.interp(tt, [m("down") + 0.3, m("c_dstars"), m("c_ref3"), m("bell2")], [1.4, 0.8, 0.5, 0.5])
        out *= np.interp(tt, [m("c_end"), m("black")], [1.0, 0.4])
        return out
    return g


def ambience(bus):
    A.bed(bus, "ambience/room-tone-hvac", m("open"), m("c_bay"), -50, lowpass=3000, fin=0.3)
    A.bed(bus, "crowd/crowd-large", m("open"), m("c_bay"), -44, lowpass=900, fin=0.3)      # the arena, beyond the wall
    A.bed(bus, "ambience/rain-concrete", m("c_bay"), m("c_track"), -46, lowpass=5000)
    A.bed(bus, "ambience/street-distant", m("c_bay"), m("c_track"), -44)
    A.bed(bus, "ambience/room-tone-hvac", m("c_track"), ARENA, -44, lowpass=2400)
    A.bed(bus, "crowd/crowd-large", m("c_track"), m("c_prep"), -48, lowpass=600)
    A.bed(bus, "crowd/crowd-large", m("c_prep"), ARENA, -45, lowpass=700)
    A.bed(bus, "crowd/crowd-large", ARENA, m("black"), -26, gain_fn=crowd_gain(ARENA, m("black")), fin=0.6, fout=0.05)


def reactions(bus):
    """the arena reacting to what happens"""
    # the arena opens: air horns and a cheer
    A.ev(bus, "crowd/air-horn", ARENA + 0.25, -30, pan=-0.5)
    put(bus, C.cheer(3.5, seed=3), ARENA + 0.2, -27)
    # "EDDIE HEARN!": a mixed cheer and laugh;  "DANA WHITE!": the bigger cheer, horns
    put(bus, C.cheer(3.0, seed=4), le("L035") - 0.2, -26)
    put(bus, C.laugh(2.4, seed=5), le("L035") + 0.1, -31)
    put(bus, C.cheer(3.2, seed=6), le("L036") - 0.2, -25)
    A.ev(bus, "crowd/air-horn", le("L036") + 0.3, -31, pan=0.6)
    # the fight
    put(bus, C.roar(1.8, seed=11), m("ex1") + 0.42, -25)                 # Eddie's jab misses by a mile
    put(bus, C.laugh(2.2, seed=12), m("ex1") + 0.95, -28)               # the windmill
    put(bus, C.laugh(1.8, seed=13), m("ex2") + 0.55, -31)               # the tap
    put(bus, C.roar(1.6, seed=14, cheer=0.4), m("ex3a") + 0.6, -27)     # the flurry
    put(bus, C.roar(2.4, seed=15, cheer=1.0), m("ex3b") + 0.45, -22)    # the one that lands
    put(bus, C.cheer(2.5, seed=16), m("ex3b") + 0.6, -28)
    put(bus, C.roar(1.6, seed=17), m("ex3c") + 0.42, -25)               # the wild cross
    put(bus, C.laugh(2.2, seed=18), m("ex3c") + 0.75, -28)              # the spin
    # slow motion: the whole room pitched down and dulled, then it snaps back with a laugh
    slow = A.varispeed(C.roar(1.5, seed=19).astype(np.float32), -7.0)
    put(bus, A.lp(slow, 900, 2).astype(np.float32), m("ex3d") + 0.6, -26)
    put(bus, C.laugh(2.6, seed=20), m("ex3d") + 1.55, -26)
    put(bus, C.laugh(2.0, seed=21), m("sep") + 0.6, -30)                # they lean back in
    # the slugfest: the roar builds with every punch that lands
    put(bus, C.roar(3.2, seed=30, cheer=0.9), m("slug") + 0.4, -24)
    put(bus, C.roar(2.0, seed=31, cheer=1.0), m("slug") + 2.0, -23)
    # the double knockout: a huge roar a beat after the freeze, a laugh at the two of them flat out
    put(bus, C.roar(3.0, seed=32, cheer=1.0), m("impact") + 0.35, -20)
    put(bus, C.laugh(3.0, people=24, seed=33), m("down") + 0.3, -24)
    put(bus, C.cheer(3.5, seed=22), m("bell2") + 0.3, -25)
    put(bus, C.laugh(2.4, seed=23), m("arms") + 0.3, -29)
    put(bus, C.laugh(2.6, seed=24), le("L052") + 0.1, -27)              # "a draw!"
    put(bus, C.cheer(3.0, seed=25), le("L052") + 0.2, -29)
    put(bus, C.laugh(2.4, seed=26), m("climb") + 0.6, -29)              # Dana climbs into the bin


def fight(bus):
    bell = A.clip("sport/boxing-bell")
    put(bus, A.room(bell.mean(1) if bell.ndim == 2 else bell, 1.2, 0.3), m("bell") + 0.03, -19)
    put(bus, A.room(bell.mean(1) if bell.ndim == 2 else bell, 1.2, 0.3), m("bell2") + 0.03, -19)
    whooshes = ["whoosh/whoosh-a", "whoosh/whoosh-b", "whoosh/whoosh-c", "whoosh/whoosh-d"]
    for k, (t, kind, reach) in enumerate(sorted(E.sfx + Dn.sfx)):
        name = whooshes[k % 4]
        if kind == "whoosh_slow":
            y = A.varispeed(A.clip(name).mean(1) if A.clip(name).ndim == 2 else A.clip(name), -9.0)
            put(bus, y, t - 0.15, -27, pan=-0.2 if k % 2 else 0.2)
        else:
            A.ev(bus, name, t, -28 if reach > 80 else -31, pan=-0.25 if k % 2 else 0.25,
                 semis=1.5 if reach < 70 else -1.0)
    # the glove tap: a squeak and a tiny thud
    A.ev(bus, "creaks/creak-small", m("ex2") + 0.36, -24, semis=14, highpass=1200, dur=0.2)
    A.ev(bus, "impacts/punch-c", m("ex2") + 0.36, -33, lowpass=2500)
    # the one that lands: a real punch, the body thud under it
    A.ev(bus, "impacts/punch-a", m("ex3b") + 0.43, -17)
    A.ev(bus, "impacts/punch-d", m("ex3b") + 0.45, -22, semis=-4, lowpass=3000)
    A.ev(bus, "cloth/cloth-b", m("ex3b") + 0.47, -32)
    # ducks, stumbles, spins: cloth and feet
    for t in (m("ex3a") + 0.2, m("ex3a") + 0.62, m("ex3a") + 1.04, m("ex3c") + 0.3):
        A.ev(bus, "cloth/cloth-%s" % "acef"[int(t * 10) % 4], t, -34, pan=0.3)
    for t in (m("ex3b") + 0.62, m("ex3b") + 0.8, m("ex3b") + 0.98, m("ex3c") + 0.6, m("ex3c") + 0.72):
        A.ev(bus, "footsteps/step-%s" % "ab"[int(t * 10) % 2], t, -36, pan=-0.3)
    A.ev(bus, "foley/body-fall-b", m("ex3e") + 0.95, -32)                # they fall into each other
    A.ev(bus, "cloth/cloth-e", m("sep") + 0.1, -34)
    A.ev(bus, "cloth/cloth-a", m("sep") + 1.4, -34)
    A.ev(bus, "foley/body-fall-a", m("sep") + 1.45, -35)
    # the slugfest: every punch lands
    for k, (dt, A_, pose, wind) in enumerate(SLUG):
        t = m("slug") + dt + 0.06
        A.ev(bus, "impacts/punch-%s" % "abcdef"[k % 6], t, -19, pan=0.2 if A_ is E else -0.2, semis=(k % 3) - 1)
        A.ev(bus, "cloth/cloth-%s" % "bdf"[k % 3], t + 0.03, -33)
    # the wind-up: a slide whistle climbing with the trembling; the cross-counter: two punches on one frame
    put(bus, slide_whistle(300, 1300, m("impact") - m("dko") - 0.2), m("dko") + 0.2, -30)
    for nm, sm in (("impacts/punch-a", -2), ("impacts/punch-d", -5)):
        A.ev(bus, nm, m("impact") + 0.06, -14, semis=sm)
    A.ev(bus, "impacts/gong-big", m("impact") + 0.06, -26, semis=4)
    # the fall: a slide whistle down, both bodies hit the canvas together, the ring boards boom
    put(bus, slide_whistle(1400, 220, 0.75), m("fall"), -28)
    for nm, pn in (("foley/body-fall-a", -0.4), ("foley/body-fall-b", 0.4)):
        A.ev(bus, nm, m("fall") + 0.75, -17, pan=pn)
    A.ev(bus, "impacts/tom-hit", m("fall") + 0.75, -20, semis=-9)
    # out cold: birds tweeting round their heads until the bell; saved by it, they spring up: boing
    put(bus, A.room(tweets(m("bell2") - m("fall") - 0.8), 0.6, 0.2), m("fall") + 0.85, -31)
    put(bus, boing(0.6, 170), m("bell2") + 0.03, -25, pan=-0.3)
    put(bus, boing(0.6, 210), m("bell2") + 0.06, -25, pan=0.3)


def foley(bus):
    # the press area
    A.ev(bus, "cloth/cloth-a", wt("L001", "not") - 0.12, -44, pan=-0.1)
    # the loading bay: the trolley rolls past, left to right, and the attendant's steps
    squeaks(bus, m("trolley") - 0.3, m("look_cam") + 0.5, -36, pan=-0.8, pan_to=0.8)
    A.steps(bus, m("trolley") - 0.2, m("look_cam") + 0.4, -42, pace=0.42, pan=-0.7, pan_to=0.7)
    A.ev(bus, "cloth/cloth-c", m("c_shoe") + 0.2, -34)
    A.ev(bus, "cloth/cloth-e", m("c_shoe") + 0.7, -32)
    A.ev(bus, "cloth/cloth-b", m("c_shoe") + 0.95, -34)
    # the corridor
    squeaks(bus, m("c_track"), m("c_track") + 1.7, -33, pan=-0.6, pan_to=0.0)
    A.steps(bus, m("c_track"), m("c_track") + 1.7, -42, pace=0.4, pan=-0.5, pan_to=0.0)
    A.ev(bus, "cloth/cloth-d", ls("L010") + 0.05, -38)
    A.ev(bus, "cloth/cloth-f", le("L010") - 0.1, -40)
    A.ev(bus, "foley/cup-down", m("lid") + 0.3, -32, semis=-9, lowpass=3000)
    A.ev(bus, "foley/pen-click-b", m("lid") + 0.32, -38, semis=-12)
    squeaks(bus, m("aside"), m("bump"), -34, pan=0.0, pan_to=0.4)
    A.steps(bus, m("aside"), m("bump"), -43, pace=0.42, pan=-0.1, pan_to=0.3)
    # the cable protector: the bump, the freeze, the tumble, the landing
    A.ev(bus, "impacts/tom-hit", m("bump"), -24, semis=-5)
    A.ev(bus, "foley/cup-down", m("bump") + 0.02, -30, semis=-14)
    A.ev(bus, "whoosh/whoosh-b", m("tumble") + 0.05, -30, semis=-3)
    A.ev(bus, "cloth/cloth-a", m("tumble") + 0.05, -32)
    A.ev(bus, "cloth/cloth-e", m("tumble") + 0.5, -32)
    A.ev(bus, "foley/body-fall-a", m("tumble") + 0.9, -24)
    A.ev(bus, "cloth/cloth-b", m("tumble") + 0.97, -30)
    A.ev(bus, "cloth/cloth-d", m("tumble") + 1.02, -34)                 # the towel lands on his head
    A.ev(bus, "cloth/cloth-c", m("landed") + 0.6, -36)
    # Eddie walks in, stops
    A.steps(bus, m("c_eddie"), m("c_eddie") + 1.6, -38, pace=0.5, pan=-0.6, pan_to=-0.4)
    A.steps(bus, ls("L025") - 0.15, m("c_neg") + 0.3, -40, pace=0.45, pan=-0.4, pan_to=0.0)   # over to Dana
    A.steps(bus, m("c_aj") - 0.75, m("c_aj") + 0.15, -41, pace=0.45, pan=0.8, pan_to=0.5)     # Joshua
    A.ev(bus, "cloth/cloth-d", m("c_eddie") + 1.2, -40)
    A.ev(bus, "cloth/cloth-f", m("c_neg") + 0.4, -38)
    A.ev(bus, "cloth/cloth-a", m("c_neg") + 1.05, -40)
    # the red corner's room: Eddie's quick change in a puff;  the blue corner's: Dana's shadowboxing, then puffing
    A.ev(bus, "whoosh/whoosh-a", m("c_prep") + 0.6, -32, semis=4)
    A.ev(bus, "cloth/cloth-e", m("c_prep") + 0.66, -34)
    A.ev(bus, "cloth/cloth-b", m("c_prep") + 0.8, -36)
    for i, (t, kind, reach) in enumerate(sorted(SB.sfx)):
        A.ev(bus, "whoosh/whoosh-%s" % "cdab"[i % 4], t, -34, pan=0.1, semis=3)
        A.ev(bus, "cloth/cloth-%s" % "acef"[i % 4], t + 0.04, -42)
    A.ev(bus, "footsteps/step-a", m("c_prep2") + 1.55, -40)
    # the face-off: one cough in the silence
    bus.add(A.at_level(cough(), -31), m("cough") + 0.1, 1.0, 0.4)
    # the exit: the trolley comes in, the climb, the roll-out, and the last squeak
    squeaks(bus, m("c_trolley"), m("c_trolley") + 2.0, -33, pan=-0.7, pan_to=0.0)
    A.ev(bus, "cloth/cloth-c", m("climb") + 0.6, -32)
    A.ev(bus, "foley/body-fall-b", m("climb") + 1.2, -33, lowpass=1500)
    squeaks(bus, m("rollout"), m("c_end") + 1.0, -32, pan=0.0, pan_to=0.9)
    A.ev(bus, "creaks/creak-small", m("c_end") + 1.2, -30, semis=11, highpass=900, dur=0.25, pan=0.9)


def music(bus):
    # the title card: the sting and the boom
    y = A.title_sting(2.6)
    y *= A.fade(len(y), 0.05, 0.8)[:, None]
    bus.add(A.at_level(y, -24), 0.0)
    bus.add(A.at_level(A.big_boom(0.8), -18), 0.05)
    # two seconds of sting before the announcer
    y = A.title_sting(2.4)
    y *= A.fade(len(y), 0.25, 0.5)[:, None]
    bus.add(A.at_level(y, -22), ARENA)
    # the slugfest: the drums come back, faster and faster, and stop dead on the cross-counter
    t, k = m("slug") + 0.2, 0
    while t < m("impact"):
        A.ev(bus, "impacts/tom-hit", t, -28 if k % 2 == 0 else -33, semis=-3 + min(5, k // 4))
        k += 1
        t += max(0.12, 0.34 - 0.012 * k)
    # fight music: a drum pulse from the bell to the first embarrassing glove tap, then nothing
    a, b = m("bell") + 0.6, m("ex2") + 0.36
    t, k = a, 0
    while t < b:
        A.ev(bus, "impacts/tom-hit", t, -29 if k % 2 == 0 else -35, semis=-3 if k % 4 else -1)
        k += 1
        t += 0.4


def main():
    dlg, amb, fx, mus = A.Bus(), A.Bus(), A.Bus(), A.Bus()
    dialogue(dlg)
    ambience(amb)
    reactions(amb)
    fight(fx)
    foley(fx)
    music(mus)
    A.master(dlg, [amb, fx], [mus])

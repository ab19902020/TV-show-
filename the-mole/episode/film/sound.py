"""The soundtrack: the three recordings as delivered (every line cut word-exact, a little room on each), the room
tones of each place, and the comedy hung off the edit's marks: the documentary strings at the top, the slurp in the
hedge, the clap, the newspaper spin, the plant's shuffles, the lock's click, the blinds, the clock's tick, a cheesy
saxophone for the reveal, refresh clicks, the goal, the plant going off, the screams' stings and the freeze's record
scratch, the laptop's ping, the cricket in Omar's office, the tablet's crowd, the sip, the end card.
python3 -m studio.film the-mole sound -> build/episode_audio.wav"""
import json

import numpy as np

from studio.film import audio as A
from studio.film import ep
from studio.film.shots import Marks
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt = T.m, T.ls, T.le, T.wt
SR = A.SR


def st(y):
    y = np.asarray(y, np.float32)
    return np.stack([y, y], 1) if y.ndim == 1 else y


def env(n, a=0.005, r=0.08):
    e = np.ones(n, np.float32)
    na, nr = max(1, int(a * SR)), max(1, int(r * SR))
    e[:na] = np.linspace(0, 1, na)
    e[-nr:] *= np.linspace(1, 0, nr)
    return e


def tone(f, dur, harm=0.2):
    t = np.arange(int(dur * SR)) / SR
    return (np.sin(2 * np.pi * f * t) + harm * np.sin(4 * np.pi * f * t)).astype(np.float32)


def noise(dur, seed=3):
    return np.random.default_rng(seed).normal(0, 1, int(dur * SR)).astype(np.float32)


def whoosh(dur=0.35, lo=300, hi=3000, seed=3):
    n = int(dur * SR)
    y = A.bp(noise(dur, seed), lo, hi)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    return st(y * e * 0.5)


def hit():
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * (90 * np.exp(-t * 6)) * t) * np.exp(-t * 7)
    y += np.random.default_rng(5).normal(0, 1, n) * np.exp(-t * 40) * 0.5
    return st(y.astype(np.float32))


def ping():
    a = tone(1568, 0.09) * env(int(0.09 * SR), 0.003, 0.06)
    b = tone(2093, 0.16) * env(int(0.16 * SR), 0.003, 0.12)
    return st(np.concatenate([a, b]) * 0.6)


def cricket(n_chirps=3):
    out = []
    for i in range(n_chirps):
        c = tone(4300, 0.05, 0.0) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 60 * np.arange(int(0.05 * SR)) / SR)))
        out += [c * env(len(c), 0.002, 0.01), np.zeros(int(0.05 * SR), np.float32)]
        if i % 3 == 2:
            out.append(np.zeros(int(0.35 * SR), np.float32))
    return st(np.concatenate(out) * 0.25)


def slurp(dur=1.0):
    """a long wet slurp through a metal straw: gurgling bubbles of filtered noise"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = A.bp(noise(dur, 21), 500, 2600)
    gate = (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * (14 + 6 * np.sin(t * 5)) * t))) * (0.6 + 0.4 * np.random.default_rng(2).random(n))
    gate = A.lp(gate.astype(np.float32), 60)
    y = y * gate * np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 0.5
    return st(y * 0.6)


def sax(notes, step=0.42):
    """a cheesy smooth saxophone line: a reedy saw with vibrato, through a soft filter, in a big room"""
    out = []
    for f in notes:
        dur = step * (2 if f == notes[-1] else 1)
        t = np.arange(int(dur * SR)) / SR
        vib = 1 + 0.012 * np.sin(2 * np.pi * 5.5 * t) * np.clip(t / 0.2, 0, 1)
        ph = 2 * np.pi * np.cumsum(f * vib) / SR
        y = sum(np.sin(k * ph) / k ** 1.25 for k in range(1, 9))
        y = A.lp(y.astype(np.float32), 2400) * env(len(t), 0.05, 0.12)
        out.append(y)
    y = np.concatenate(out)
    return A.room(st(y * 0.35), seconds=2.0, mix=0.3)


def scratch():
    """a record scratch: a noisy fast down-up sweep"""
    dur = 0.35
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 900 + 2600 * np.abs(np.sin(2 * np.pi * 2.6 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sign(np.sin(ph)) * 0.3 + A.bp(noise(dur, 13), 800, 5000) * 0.6
    return st(y * env(n, 0.005, 0.06) * 0.6)


def sting(semis=0.0):
    """a dramatic orchestral stab: low brass-ish chord with a hit"""
    f0 = 98 * 2 ** (semis / 12)
    dur = 0.9
    t = np.arange(int(dur * SR)) / SR
    y = sum(np.sign(np.sin(2 * np.pi * f * t)) * 0.2 + np.sin(2 * np.pi * f * t) * 0.4 for f in (f0, f0 * 1.19, f0 * 1.5, f0 * 2))
    y = A.lp(y.astype(np.float32), 1800) * np.exp(-t * 2.5)
    h = np.zeros((len(t), 2), np.float32)
    hh = hit()
    h[:len(hh)] = hh[:len(t)]
    return A.room(st(y * 0.4) + h * 0.6, seconds=1.8, mix=0.25)


def snore(dur=1.2):
    n = int(dur * SR)
    t = np.arange(n) / SR
    y = A.lp(noise(dur, 17), 500) * (0.4 + 0.6 * np.sin(np.pi * t / dur) ** 2) * (1 + 0.5 * np.sin(2 * np.pi * 28 * t))
    return st(y * 0.5)


def add(bus, y, t, level):
    bus.add(A.at_level(y, level), t)


def tinny(name, dur, fout=0.7, start=0.0):
    """a recorded clip as it comes out of a laptop or tablet speaker: a short slice, band-limited, fading out"""
    y = A.clip(name)
    if y.ndim == 2:
        y = y.mean(1)
    y = y[int(start * SR):int((start + dur) * SR)].astype(np.float32)
    y = A.bp(y, 350, 4200).astype(np.float32)
    n = len(y)
    e = np.ones(n, np.float32)
    nf, nb = int(0.03 * SR), int(fout * SR)
    e[:nf] = np.linspace(0, 1, nf)
    e[-nb:] *= np.linspace(1, 0, nb) ** 1.5
    return st(y * e)


def main():
    dlg, amb, fx, mus = A.Bus(), A.Bus(), A.Bus(), A.Bus()
    A.dialogue(dlg, room_s=0.25, room_db=-26)
    # ---- rooms
    A.bed(amb, "ambience/wind", 0.0, m("cut_title"), -40, lowpass=2500, fin=0.5, fout=0.2)
    A.bed(amb, "ambience/room-tone-hvac", m("cut_int1"), m("cut_hedges"), -52, lowpass=3000)
    A.bed(amb, "ambience/wind", m("cut_hedges"), m("cut_end"), -42, lowpass=2500, fin=0.2, fout=0.4)
    # ---- 1: documentary strings under the opening, swelling to the title
    add(mus, A.strings([110, 165, 220, 277, 330], m("cut_hedge") + 1.0, attack=2.5, release=1.5), 0.0, -26)
    add(mus, A.strings([98, 147, 196, 247], m("cut_title") - m("cut_hedge"), attack=0.5, release=0.8, bright=900),
        m("cut_hedge"), -32)
    add(fx, whoosh(0.3, 600, 4000), m("cut_bino") - 0.1, -34)
    add(fx, slurp(1.0), m("slurp"), -24)
    add(mus, A.title_sting(3.0), m("cut_title"), -18)
    # ---- 2
    for i, key in enumerate(("L007", "L008", "L009", "L010")):     # the whips round the board
        t0 = wt("L007", "jason") if key == "L007" else ls(key)
        add(fx, whoosh(0.18, 900, 6000, seed=30 + i), t0 - 0.12, -32)
    add(fx, whoosh(0.2, 900, 6000), m("cut_board") - 0.1, -32)
    add(fx, A.clip("foley/clap-single"), m("clap") + 0.15, -24)
    add(fx, whoosh(0.7, 300, 3000), m("cut_spygate"), -30)
    add(fx, hit(), m("cut_spygate") + 0.68, -28)
    add(mus, A.strings([65, 98, 131, 156], 3.0, attack=1.5, release=1.0, bright=700), m("cut_tutorial"), -30)
    # ---- 3
    for k in (0.6, 1.3, 2.0, 2.7):                                 # the plant shuffles: a squeak each time
        add(fx, st(tone(1900 + 300 * k, 0.07, 0.4) * env(int(0.07 * SR), 0.003, 0.03)), m("cut_corr") + k, -36)
        add(fx, A.clip("footsteps/step-a"), m("cut_corr") + k, -36)
    add(fx, A.clip("foley/pen-click-a"), m("hangup"), -30)
    add(fx, A.clip("foley/pen-click-b"), m("click"), -22)
    add(fx, A.clip("creaks/creak-mid"), ls("L022") + 0.4, -32)
    for i in range(6):
        add(fx, A.clip("foley/pen-click-c"), m("cut_clock") + i * 1.0, -38)
    add(fx, hit(), wt("L023", "three") - 0.05, -30)
    add(mus, sax([466, 415, 349, 311, 349, 466], 0.42), wt("L023", "breathe") - 0.2, -22)
    add(fx, whoosh(0.4, 200, 1500), wt("L023", "breathe"), -34)
    for r in (0.35, 0.95):
        add(fx, A.clip("foley/pen-click-a"), m("cut_laptop") + r, -30)
    add(fx, ping(), m("cut_goal"), -24)
    add(fx, tinny("crowd/crowd-large", 2.2, 0.9, start=3.0), m("cut_goal") + 0.05, -40)   # the goal, from the laptop
    add(fx, A.big_boom(0.9), m("boom"), -16)
    add(fx, whoosh(0.5, 200, 3000), m("boom"), -26)
    add(mus, sting(0), m("scream1"), -24)
    add(mus, sting(3), m("scream2"), -24)
    add(mus, sting(6), m("scream3"), -22)
    add(fx, scratch(), m("freeze"), -20)
    # ---- 4
    add(fx, whoosh(0.3, 400, 3000), m("cut_back") - 0.1, -32)
    add(fx, ping(), m("ping"), -22)
    add(fx, tinny("sport/whistle-ref", 1.0, 0.3), m("ping") + 0.2, -36)
    add(mus, A.strings([82, 87], 1.5, attack=0.8, release=0.5, bright=600), m("cut_point"), -34)
    add(mus, A.strings([110, 117, 123], 1.6, attack=1.0, release=0.4, bright=900), m("cut_strain"), -30)
    # ---- 5
    add(fx, A.clip("paper/page-turn"), wt("L044", "commitment") - 0.1, -32)
    add(fx, snore(1.1), m("cut_asleep") + 0.6, -32)
    add(fx, snore(1.1), m("cut_asleep") + 2.0, -32)
    add(fx, A.clip("paper/page-turn"), m("cut_asleep") + 0.1, -34)
    # ---- 6
    add(fx, A.clip("doors/door-shut"), m("cut_ceo") - 0.05, -22)
    add(fx, cricket(3), m("cut_omar") + 0.5, -30)
    add(fx, A.clip("foley/cup-down"), m("cut_omar") + 1.9, -34)
    # ---- 7
    add(fx, tinny("crowd/crowd-large", 1.8, 0.8, start=3.0), m("cut_tablet") + 0.05, -42)  # the tablet's goal
    add(fx, A.clip("cloth/cloth-a"), m("cut_plant2") + 0.6, -30)
    add(fx, whoosh(0.35, 200, 2500, seed=41), m("cut_w057") - 0.3, -30)   # the plant bursts: a whoosh, his line clear
    add(fx, A.big_boom(0.5), le("L057") + 0.02, -26)                    # and the bits land
    add(mus, sting(5), m("scream"), -22)
    add(fx, scratch(), m("cut_spidey") + 0.5, -20)
    add(fx, slurp(0.8), m("sip") + 0.6, -28)
    add(mus, A.title_sting(4.0), m("cut_end"), -18)
    A.master(dlg, [amb, fx], [mus])

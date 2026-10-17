"""The soundtrack: the two recordings as delivered (each line cut word-exact), a little room on each, the stream's
pings and whooshes, Old Trafford's silence (wind, one cricket), the typing of the post, the crash-zoom hits, the
siren on "fashion police", the plates clinking down, and the end card's thud. Everything hangs off the dialogue
edit's marks. python3 -m studio.film lecher-vs-rio sound -> build/episode_audio.wav"""
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
KEY = np.random.default_rng(29)


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


def ping():
    """the notification: two quick bright notes"""
    a = tone(1568, 0.09) * env(int(0.09 * SR), 0.003, 0.06)
    b = tone(2093, 0.16) * env(int(0.16 * SR), 0.003, 0.12)
    return st(np.concatenate([a, b]) * 0.6)


def whoosh(dur=0.35, lo=300, hi=3000):
    n = int(dur * SR)
    y = np.random.default_rng(3).normal(0, 1, n).astype(np.float32)
    y = A.bp(y, lo, hi)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    return st(y * e * 0.5)


def cricket(n_chirps=3):
    out = []
    for i in range(n_chirps):
        c = tone(4300, 0.05, 0.0) * (0.5 + 0.5 * np.sign(np.sin(2 * np.pi * 60 * np.arange(int(0.05 * SR)) / SR)))
        out += [c * env(len(c), 0.002, 0.01), np.zeros(int(0.05 * SR), np.float32)]
        if i % 3 == 2:
            out.append(np.zeros(int(0.35 * SR), np.float32))
    return st(np.concatenate(out) * 0.25)


def siren(dur):
    t = np.arange(int(dur * SR)) / SR
    f = 720 + 260 * (np.floor(t * 4) % 2)
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sign(np.sin(ph)) * 0.35 + np.sin(ph) * 0.4
    y = A.lp(y.astype(np.float32), 3000)
    return st(y * env(len(y), 0.02, 0.15) * 0.5)


def hit():
    """the crash zoom: a low thump with a bright crack on it"""
    n = int(0.5 * SR)
    t = np.arange(n) / SR
    y = np.sin(2 * np.pi * (90 * np.exp(-t * 6)) * t) * np.exp(-t * 7)
    y += np.random.default_rng(5).normal(0, 1, n) * np.exp(-t * 40) * 0.5
    return st(y.astype(np.float32))


def clink(semis=0.0):
    f = 2400 * 2 ** (semis / 12)
    y = (tone(f, 0.25, 0.4) + 0.5 * tone(f * 2.7, 0.25, 0)) * np.exp(-np.arange(int(0.25 * SR)) / SR * 22)
    return st(y.astype(np.float32) * 0.35)


def key_click():
    n = int(0.03 * SR)
    y = np.random.default_rng(int(KEY.integers(1_000_000))).normal(0, 1, n) * np.exp(-np.arange(n) / SR * 260)
    return st(A.hp(y.astype(np.float32), 1500) * 0.5)


def add(bus, y, t, level):
    bus.add(A.at_level(y, level), t)


def main():
    dlg, amb, fx = A.Bus(), A.Bus(), A.Bus()
    A.dialogue(dlg, room_s=0.25, room_db=-26)
    # rooms: Saeed's bedroom-studio hum under his stream; Rio's studio is quieter
    A.bed(amb, "ambience/room-tone-hvac", 0.0, m("cut_ot"), -52, lowpass=3000)
    A.bed(amb, "ambience/wind", m("cut_ot"), m("cut_reply"), -36, lowpass=2500, fin=0.05, fout=0.1)
    A.bed(amb, "ambience/room-tone-hvac", m("cut_reply"), m("cut_end"), -55, lowpass=3000)
    # going live
    add(fx, whoosh(0.4, 600, 6000), 0.0, -30)
    add(fx, ping(), 0.12, -30)
    # the counters spinning up
    for key, word in (("L001", "millions"), ("L008", "twenty")):
        t0 = wt(key, word)
        for i in range(10):
            add(fx, st(tone(1200 + 90 * i, 0.03) * env(int(0.03 * SR), 0.002, 0.02)), t0 + i * 0.08, -40)
    # Old Trafford, two nil down: the wind, a cricket, one cough far off
    add(fx, whoosh(0.3), m("cut_ot") - 0.15, -34)
    add(fx, cricket(6), m("cut_ot") + 0.35, -30)
    # Rio's reply arrives: a ping, then his post typing itself out
    add(fx, whoosh(0.3), m("cut_reply") - 0.12, -32)
    add(fx, ping(), m("cut_reply") + 0.05, -26)
    t = ls("L003")
    rng = np.random.default_rng(11)
    while t < le("L003"):
        add(fx, key_click(), t, -38 + rng.uniform(-3, 2))
        t += rng.uniform(0.06, 0.13)
    # the pip slides in
    add(fx, whoosh(0.25, 800, 5000), m("cut_pip1") - 0.05, -36)
    # TITS!: the crash zoom
    add(fx, hit(), ls("L006") - 0.02, -20)
    add(fx, ping(), ls("L006") + 0.4, -34)
    # the ouch on Rio
    add(fx, whoosh(0.2, 200, 1500), m("cut_ouch") - 0.05, -34)
    # fashion police: the hit and the siren
    add(fx, hit(), wt("L009", "police") - 0.02, -22)
    add(fx, siren(le("L009") + 0.4 - wt("L009", "police")), wt("L009", "police"), -28)
    # the plates: a clink as each lands
    a, b = wt("L011", "watching"), wt("L011", "feelings") + 0.3
    for i in range(14):
        add(fx, clink(rng.uniform(-3, 3)), a + i * (b - a) / 14 + 0.1, -34)
    # side by side, then the silence: one cricket
    add(fx, whoosh(0.3), m("cut_split") - 0.12, -32)
    add(fx, cricket(3), m("silence") + 0.9, -32)
    # the end card: a ping, then the thud of "limited who can reply", then the title
    add(fx, ping(), m("cut_end") + 0.1, -28)
    add(fx, hit(), m("cut_end") + 1.4, -26)
    add(fx, A.big_boom(0.6), m("cut_end") + 2.2, -22)
    A.master(dlg, [amb, fx], [])

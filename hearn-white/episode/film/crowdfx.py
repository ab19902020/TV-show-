"""Crowd reactions for The Undercard, built from real recordings (library/audio/sfx, CC0) layered into an arena:

    laugh(dur)     audience laughter: two dozen laughs (13 takes of a man laughing, library voice/laugh-*), each
                   at its own pitch (men and women), start and loudness, rolling off over `dur`
    roar(dur)      a reaction swell: the arena crowd surging (crowd-large, filter opening), "yeah" shouts and
                   applause on top: a near miss, a hit, a big moment
    cheer(dur)     cheering and applause for an introduction
All in the arena's reverb; built once per signature and cached in build/crowdfx/."""
import hashlib

import numpy as np
import soundfile as sf

from studio.film import audio as A
from studio.film import ep

SR = A.SR
LAUGHS = [f"voice/laugh-{k:02d}" for k in range(1, 14)] + ["voice/laugh-man"]


def _mono(name):
    y = A.clip(name)
    return y.mean(1) if y.ndim == 2 else y


def _trim(y, floor=0.02):
    loud = np.nonzero(np.abs(y) > floor * np.abs(y).max())[0]
    return y[loud[0]:loud[-1] + 1] if len(loud) else y


def _space(st, wet=0.4, damp=4500):
    ir = A.reverb_ir(1.7, damp, 0.02, 5)
    rev = A.convolve_st(st.mean(1).astype(np.float32), ir)[:len(st)]
    return (st * (1 - wet) + rev * wet).astype(np.float32)


def _place(mix, y, t, gain, pan):
    i = int(t * SR)
    if i >= len(mix):
        return
    y = y[:len(mix) - i]
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    mix[i:i + len(y), 0] += y * gain * l
    mix[i:i + len(y), 1] += y * gain * r


def _cached(name, args, build):
    key = hashlib.md5(repr((name, args, 5)).encode()).hexdigest()[:10]
    p = ep.path("crowdfx", f"{name}_{key}.wav")
    if p.exists():
        return sf.read(str(p), dtype="float32")[0]
    p.parent.mkdir(parents=True, exist_ok=True)
    y = build()
    sf.write(str(p), y, SR, subtype="PCM_24")
    return y


def laugh(dur=2.6, people=16, seed=1):
    def build():
        rng = np.random.default_rng(seed)
        n = int(dur * SR)
        mix = np.zeros((n, 2), np.float32)
        for k in range(people):
            y = _trim(_mono(LAUGHS[rng.integers(len(LAUGHS))]))
            y = A.varispeed(y, rng.uniform(-2.0, 4.0))
            t0 = rng.uniform(0, 0.4)
            L = min(len(y), n - int(t0 * SR))
            if L <= 0:
                continue
            y = y[:L] * A.fade(L, 0.02, min(0.5, L / SR * 0.5))
            y = y / (np.sqrt(np.mean(y ** 2)) + 1e-6)
            _place(mix, y, t0, rng.uniform(0.3, 1.0) * (1 - 0.5 * t0 / dur), rng.uniform(-0.8, 0.8))
        mix *= A.fade(n, 0.05, 0.6 * dur)[:, None]
        out = _space(A.lp(A.hp(mix, 140, 2), 7000, 2), wet=0.25)
        return (out / (np.abs(out).max() + 1e-6) * 0.8).astype(np.float32)
    return _cached("laugh", (dur, people, seed), build)


def roar(dur=2.2, seed=2, cheer=0.7):
    def build():
        rng = np.random.default_rng(seed)
        n = int(dur * SR)
        mix = np.zeros((n, 2), np.float32)
        bed = A.clip("crowd/crowd-large")
        bed = bed if bed.ndim == 2 else np.stack([bed, bed], 1)
        off = int(rng.uniform(0, max(1, len(bed) - n - 1)))
        b = bed[off:off + n].astype(np.float32)
        t = np.arange(n) / SR
        env = np.clip(t / 0.25, 0, 1) ** 1.2 * np.clip((dur - t) / (0.7 * dur), 0, 1) ** 1.4
        b = b * (0.6 + 1.6 * env)[:, None]
        mix += b / (np.sqrt(np.mean(b ** 2)) + 1e-6) * 0.6
        for k in range(3):
            y = _mono("crowd/cheer-yeah-a" if k % 2 == 0 else "crowd/cheer-yeah-b")
            y = A.varispeed(y, rng.uniform(-3.0, -0.5))[:n]
            y = y * A.fade(len(y), 0.03, 0.6 * len(y) / SR)
            y = y / (np.sqrt(np.mean(y ** 2)) + 1e-6)
            _place(mix, y, rng.uniform(0, 0.15), cheer * rng.uniform(0.5, 0.8), rng.uniform(-0.6, 0.6))
        out = _space(A.hp(mix, 90, 2), wet=0.35)
        return (out / (np.abs(out).max() + 1e-6) * 0.8).astype(np.float32)
    return _cached("roar", (dur, seed, cheer), build)


def cheer(dur=3.5, seed=3):
    def build():
        rng = np.random.default_rng(seed)
        n = int(dur * SR)
        mix = np.zeros((n, 2), np.float32)
        for k, name in enumerate(["crowd/applause-big", "crowd/applause-40", "crowd/cheer-yeah-a", "crowd/cheer-yeah-b",
                                  "crowd/cheer-yeah-a"]):
            y = _mono(name)
            y = A.varispeed(y, rng.uniform(-2.5, 0.5))[:n]
            y = y * A.fade(len(y), 0.05, 0.4 * len(y) / SR)
            y = y / (np.sqrt(np.mean(y ** 2)) + 1e-6)
            _place(mix, y, rng.uniform(0, 0.25), (0.9, 0.6, 0.6, 0.5, 0.4)[k], rng.uniform(-0.7, 0.7))
        mix *= A.fade(n, 0.08, 0.5 * dur)[:, None]
        out = _space(A.hp(mix, 100, 2), wet=0.4)
        return (out / (np.abs(out).max() + 1e-6) * 0.8).astype(np.float32)
    return _cached("cheer", (dur, seed), build)

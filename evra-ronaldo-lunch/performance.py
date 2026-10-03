"""Keyed acting channels and the always-on life of every character (same approach as the G-Unit film).

Channels per character: look / looky (eyes), brow, smile, tilt / nod (head), lid (eyelids), blush, pant (heavy breathing),
groove (bobbing to a beat). Keys ease from the previous value over their ramp; direction.py writes the cue sheet.
life() is the movement nobody notices but everybody misses: breathing, a slow weight shift, head drift, eye darts and
irregular blinks. It is applied as small rigid moves of the cut-outs (never a warp of the drawing)."""
import math
import numpy as np
from collections import defaultdict

KEYS = defaultdict(lambda: defaultdict(list))
DEFAULT = dict(look=0., looky=0., brow=0., smile=0., tilt=0., nod=0., lid=0., blush=0., pant=0., groove=0.)
WHO = ('evra', 'ronaldo', 'rio')
BEAT = 60 / 100.0


def key(who, channel, t, value, ramp=.18):
    KEYS[who][channel].append((float(t), float(value), max(.01, ramp)))


def keys(who, channel, items, ramp=.18):
    for it in items:
        key(who, channel, it[0], it[1], it[2] if len(it) > 2 else ramp)


def done():
    for w in KEYS:
        for c in KEYS[w]: KEYS[w][c].sort()


def value(who, channel, t):
    v = DEFAULT[channel]
    for tk, vk, ramp in KEYS[who][channel]:
        if t <= tk: break
        u = min(1., (t - tk) / ramp); u = u * u * (3 - 2 * u); v += (vk - v) * u
    return v


_RNG = np.random.default_rng(3)
_SACC = {w: (np.cumsum(_RNG.uniform(.6, 1.6, 120)), _RNG.uniform(-1, 1, (120, 2))) for w in WHO}
_PH = {w: _RNG.uniform(0, 2 * math.pi, 8) for w in WHO}
_BLINK = {w: np.cumsum(_RNG.uniform(1.6, 4.6, 60)) + _RNG.uniform(0, 1.5) for w in WHO}
EXTRA_BLINKS = defaultdict(list)          # direction.py adds deliberate blinks (a slow disbelieving blink, a double take)


def saccade(who, t):
    ts, v = _SACC[who]; i = int(np.searchsorted(ts, t)); a = v[i % 120]; b = v[(i - 1) % 120]
    u = min(1., max(0., (t - (ts[i - 1] if i else 0.)) / .06))
    return (b + (a - b) * u) * np.array([.12, .06])


def blink(who, t):
    out = 0.
    for b in list(_BLINK.get(who, [])) + EXTRA_BLINKS[who]:
        d = t - (b if not isinstance(b, tuple) else b[0]); ln = .16 if not isinstance(b, tuple) else b[1]
        if 0 <= d < ln: out = max(out, math.sin(math.pi * d / ln) ** .7)
    return out


def state(who, t):
    st = {c: value(who, c, t) for c in DEFAULT}
    if who in _SACC:
        s = saccade(who, t); st['look'] += float(s[0]); st['looky'] += float(s[1])
    st['blink'] = max(blink(who, t), st['lid'])
    return st


def life(who, t):
    """breath (upper body rise, fraction of height), lean (deg), tilt (deg), nod (fraction of height), dip"""
    p = _PH.get(who, np.zeros(8)); tau = 2 * math.pi
    per = {'evra': 3.3, 'ronaldo': 2.7, 'rio': 3.8}.get(who, 3.2)
    breath = .0018 * (.5 + .5 * math.sin(tau * t / per + p[0]))
    lean = .5 * math.sin(tau * t / 4.7 + p[1]) + .22 * math.sin(tau * t / 2.4 + p[2])
    tilt = 1.0 * math.sin(tau * t / 3.9 + p[3]) + .5 * math.sin(tau * t / 2.1 + p[4])
    nod = 0.; dip = 0.
    pant = value(who, 'pant', t)
    if pant > .005:                       # puffed out: fast, deep breaths, the head bobbing with them
        ph = math.sin(tau * t / .55)
        breath += pant * .012 * (.5 + .5 * ph); nod += pant * .006 * (.5 + .5 * ph)
    g = value(who, 'groove', t)
    if g > .005:
        b = t / BEAT; ph = b % 1
        hit = math.exp(-(ph / .2) ** 2) + math.exp(-((ph - 1) / .2) ** 2)
        nod += g * .007 * hit; dip += g * .004 * hit
        tilt += g * (2.6 * hit + 1.8 * math.sin(math.pi * b)); lean += g * 1.1 * math.sin(math.pi * b + .4)
    return dict(breath=breath, lean=lean, tilt=tilt, nod=nod, dip=dip)

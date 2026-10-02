"""The painted crowds move: every person-sized slice of a crowd row bounces on the beat in its own way.

Each plate's crowd is split into rows by depth (far rows have small people, near rows big ones). Within a row, people
sit on a grid of slices one person wide; each slice has its own move (jump every beat, jump every other beat, or
sway with a phone up), its own timing (a crowd is never in step) and strength. Neighbouring slices blend smoothly, so
there are no seams; rows blend into each other the same way. The result is a vertical (and a little sideways)
displacement of the plate, applied in the same resample that places the plate in the shot, so nothing is resampled
twice. Lifts only move content up within the crowd, never stretch a drawing more than a few pixels.

How hard the crowd goes is energy(t): the show's on, 50 walks off, the awkward silence (still: the tumbleweed's
moment), the strut, the punchline and the party after it.
"""
import math
import numpy as np

BEAT = 60 / 92.0

# rows: (y0, y1, person width, lift, sway) in plate px; x0/x1 limit a row to part of the plate (the wings' opening)
CROWDS = {
    # one perspective grid for the whole standing crowd: people get wider and move more towards the camera, so no
    # row boundary ever cuts through someone (rows of separate bands put a kink in whoever stood across the join)
    'stage': [dict(y0=1040, y1=1720, fan=dict(vx=470, w=(46, 200), lift=(4.5, 15.), sway=(1.5, 4.5)))],
    'crowd': [dict(y0=255, y1=390, w=18, lift=1.5, sway=.6),
              dict(y0=395, y1=520, w=22, lift=2., sway=.8),
              dict(y0=540, y1=680, w=26, lift=2.5, sway=1.),
              dict(y0=690, y1=800, w=34, lift=4., sway=1.5),
              dict(y0=800, y1=960, w=48, lift=7., sway=2.5)],
    'wings': [dict(y0=430, y1=530, w=18, lift=1.8, sway=.6, x0=405, x1=810),
              dict(y0=560, y1=710, w=24, lift=2.6, sway=.8, x0=405, x1=810)],
}
FEATHER = 22.                                  # plate px over which rows blend


def smooth(u):
    u = np.clip(u, 0, 1); return u * u * (3 - 2 * u)


def ramp(t, a, b, v0, v1):
    return v0 + (v1 - v0) * float(smooth((t - a) / (b - a)))


def energy(t):
    if t < 1.25: return 0.
    if t < 19.95: return 1.
    if t < 21.5: return ramp(t, 19.95, 20.6, 1., .3)        # 50's gone: the crowd falters
    if t < 22.9: return .55                                  # the reverse: they're waiting, phones up
    if t < 26.3: return .1                                   # the awkward silence
    if t < 29.25: return ramp(t, 26.3, 29.2, .1, .3)
    if t < 31.6: return ramp(t, 29.25, 31.5, .35, .85)       # the strut: they're getting into it
    if t < 32.47: return .9
    return 1.45                                              # UNIT: they go wild


class Crowd:
    def __init__(self):
        rng = np.random.default_rng(91)
        self.people = {}
        for name, rows in CROWDS.items():
            ps = []
            for r in rows:
                n = int(941 / (r['fan']['w'][0] if 'fan' in r else r['w'])) + 6
                ps.append(dict(kind=rng.choice(3, n, p=[.55, .25, .2]),        # jump / every other beat / sway
                               off=rng.uniform(-.18, .22, n), gain=rng.uniform(.55, 1.15, n),
                               sph=rng.uniform(0, 2 * math.pi, n), shift=rng.uniform(0, 1)))
            self.people[name] = ps

    def _row(self, r, p, t, e, px):
        """lift and sway of one row along plate x (1D)"""
        beat = t / BEAT
        n = len(p['kind'])
        ph = beat + p['off']
        jump = np.abs(np.sin(math.pi * ph)) ** 1.4
        other = np.abs(np.sin(math.pi * ph / 2)) ** 1.6 * 1.15
        swayers = .35 * (.5 + .5 * np.sin(2 * math.pi * ph / 2))
        lift = np.select([p['kind'] == 0, p['kind'] == 1], [jump, other], swayers) * p['gain'] * r['lift'] * e
        sx = np.sin(2 * math.pi * beat / 4 + p['sph']) * r['sway'] * min(1., e + .25) * (1 + (p['kind'] == 2))
        # slice i is centred at (i + shift) * w; blend between the two nearest people
        u = px / r['w'] - p['shift']
        i0 = np.clip(np.floor(u).astype(int), 0, n - 2); f = smooth(u - np.floor(u))
        dy = lift[i0] * (1 - f) + lift[i0 + 1] * f
        dx = sx[i0] * (1 - f) + sx[i0 + 1] * f
        if 'x0' in r:
            m = smooth((px - r['x0']) / 12) * smooth((r['x1'] - px) / 12)
            dy, dx = dy * m, dx * m
        return dy, dx

    def _fan(self, r, p, t, e, px, py):
        """a row whose person width, lift and sway grow linearly with depth (y); slices fan out from vx"""
        F = r['fan']; a = np.clip((py - r['y0']) / (r['y1'] - r['y0']), 0, 1)
        w = F['w'][0] + (F['w'][1] - F['w'][0]) * a
        beat = t / BEAT; n = len(p['kind'])
        ph = beat + p['off']
        jump = np.abs(np.sin(math.pi * ph)) ** 1.4
        other = np.abs(np.sin(math.pi * ph / 2)) ** 1.6 * 1.15
        swayers = .35 * (.5 + .5 * np.sin(2 * math.pi * ph / 2))
        lift = np.select([p['kind'] == 0, p['kind'] == 1], [jump, other], swayers) * p['gain'] * e
        sx = np.sin(2 * math.pi * beat / 4 + p['sph']) * min(1., e + .25) * (1 + (p['kind'] == 2))
        u = (px - F['vx']) / w + n / 2 - p['shift']
        i0 = np.clip(np.floor(u).astype(int), 0, n - 2); f = smooth(u - np.floor(u))
        L = F['lift'][0] + (F['lift'][1] - F['lift'][0]) * a; Sw = F['sway'][0] + (F['sway'][1] - F['sway'][0]) * a
        dy = (lift[i0] * (1 - f) + lift[i0 + 1] * f) * L
        dx = (sx[i0] * (1 - f) + sx[i0 + 1] * f) * Sw
        top = smooth((py - r['y0'] + 6) / 30)                 # nothing moves above the crowd
        return (dx * top).astype(np.float32), (dy * top).astype(np.float32)

    def displace(self, name, px, py, t):
        """px, py: plate coords of each output pixel (2D). -> (dx, dy) to add to the sampling coords"""
        rows = CROWDS.get(name)
        e = energy(t)
        if not rows or e < .005: return None
        y0 = min(r['y0'] for r in rows) - FEATHER; y1 = max(r['y1'] for r in rows) + FEATHER + 2000 * any('fan' in r for r in rows)
        if py.max() < y0 or py.min() > y1: return None
        xs = px[0]                                           # the camera is a scale + shift: x depends on column only
        ys = py[:, 0]
        DX = np.zeros(px.shape, np.float32); DY = np.zeros(px.shape, np.float32)
        for r, p in zip(rows, self.people[name]):
            if 'fan' in r:
                m = (py[:, 0] > r['y0'] - FEATHER)
                if m.any():
                    dx, dy = self._fan(r, p, t, e, px[m], py[m]); DX[m] += dx; DY[m] += dy
                continue
            wy = (smooth((ys - r['y0'] + FEATHER / 2) / FEATHER) * smooth((r['y1'] + FEATHER / 2 - ys) / FEATHER))
            if wy.max() < 1e-3: continue
            dy, dx = self._row(r, p, t, e, xs)
            DY += np.outer(wy, dy).astype(np.float32); DX += np.outer(wy, dx).astype(np.float32)
        return DX, DY

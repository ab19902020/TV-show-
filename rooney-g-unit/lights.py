"""Hip-hop show lighting: moving coloured beams on the beat, a colour wash on the rig, floor spots, a follow-spot that
leaves with 50 Cent, a mirror ball and strobes for "G-G-G-G-G-UNIT", and spark fountains on "UNIT".

Everything is drawn in output pixels, placed from plate coordinates through the shot's camera (a uniform scale and a
shift). Beams, washes and floor light go on the background plate, under the characters. The follow-spot dimming and
the strobes are applied after the characters, because they light the whole stage.

The lighting tells the story: the show is on while 50 performs, it follows him off when he walks, Rooney and Rio are
left in one white spot ("what's going on here?"), the colour creeps back as Rooney gets his idea and struts to the
front, and the rig goes full disco on the punchline.
"""
import math
import numpy as np, cv2

Q = 4                      # beams and glows are computed at 1/4 resolution, then smoothly upscaled
BEAT = 60 / 92.0           # a 92 bpm hip-hop pulse (the recording has no music; the lights keep their own time)

MAGENTA, PURPLE, CYAN, RED = (1., .12, .78), (.58, .2, 1.), (.1, .82, 1.), (1., .1, .16)
AMBER, GREEN, WHITE, BLUE = (1., .62, .14), (.22, 1., .38), (1., .97, .92), (.2, .42, 1.)
PALETTE = [MAGENTA, CYAN, PURPLE, AMBER, RED, BLUE, GREEN, WHITE]
# the colour of the whole rig changes every bar: these pairs alternate between the left and right halves
BARS = [(MAGENTA, CYAN), (PURPLE, AMBER), (RED, BLUE), (CYAN, MAGENTA), (AMBER, PURPLE), (BLUE, RED)]

# moving heads on each plate (plate px): top truss, mid truss, towers. aim = resting angle (rad, + = to plate right)
RIGS = {
    'stage': dict(heads=[(220, 120), (400, 118), (538, 118), (718, 120), (238, 262), (700, 262),
                         (178, 390), (302, 390), (415, 390), (527, 390), (638, 390), (762, 390)],
                  towers=[(80, 405), (72, 545), (70, 695), (860, 405), (866, 545), (870, 695)],
                  stop=985, length=900, floor=(120, 935, 830, 985)),
    'crowd': dict(heads=[(25, 32), (105, 78), (250, 128), (315, 72), (428, 150), (512, 150), (625, 72),
                         (690, 128), (835, 78), (915, 32)],
                  towers=[], stop=1000, length=900, floor=None),
    'wings': dict(heads=[(535, 35), (470, 130), (540, 125), (615, 120), (690, 90), (790, 65)],
                  towers=[], stop=830, length=760, floor=(450, 735, 800, 830),
                  clip=[(452, 0), (806, 0), (806, 845), (425, 845), (404, 560), (430, 250)],
                  spill=[(380, 820), (840, 820), (941, 1300), (941, 1672), (200, 1672), (300, 1000)]),
}


def smooth(u):
    u = min(max(u, 0.), 1.); return u * u * (3 - 2 * u)


def ramp(t, a, b, v0, v1):
    return v0 + (v1 - v0) * smooth((t - a) / (b - a))


# ---------------------------------------------------------------- the lighting cue sheet (seconds of the recording)
G_HITS = [31.707, 31.817, 31.947, 32.067, 32.20]           # each "G" of "G-G-G-G-G-UNIT"
UNIT = 32.47


def show(t):
    """how much of the coloured show rig is running (1 = full concert, 0 = house lights off, one spot)"""
    if t < 1.25: return 0.
    if t < 20.2: return 1.
    if t < 25.85: return ramp(t, 19.95, 20.5, 1., .04)              # 50 walks off and takes the show with him
    if t < 29.25: return ramp(t, 26.3, 29.2, .06, .3)               # Rooney's idea: the rig wakes up
    if t < 31.6: return ramp(t, 29.25, 31.4, .3, .85)               # the strut: building
    return 1.


def party(t):
    """disco mode: faster sweeps, every head a different colour, mirror ball, strobes"""
    return ramp(t, 31.6, 31.75, 0., 1.)


def dim(t):
    """how dark the stage is outside the follow-spots (1 = no dimming)"""
    if t < 19.95 or t >= 31.5: return 1.
    if t < 29.25: return ramp(t, 19.95, 20.45, 1., .26) if t < 26.3 else ramp(t, 26.3, 29.2, .26, .5)
    return ramp(t, 29.25, 31.4, .5, 1.)


def strobe(t):
    """white strobe flashes: one on every G, a double on UNIT, then the party strobe"""
    f = 0.
    for g in G_HITS:
        if 0 <= t - g < .07: f = max(f, 1. - (t - g) / .07)
    for u in (UNIT, UNIT + .1):
        if 0 <= t - u < .09: f = max(f, 1. - (t - u) / .09)
    if t > 33.5 and t < 36.3:                                    # the party keeps flashing on the beat
        ph = (t / (BEAT / 2)) % 1.
        f = max(f, .35 * max(0., 1 - ph / .12))
    return f


class Lights:
    def __init__(self, ow, oh):
        self.ow, self.oh = ow, oh
        self.lw, self.lh = (ow + Q - 1) // Q, (oh + Q - 1) // Q
        yy, xx = np.mgrid[0:self.lh, 0:self.lw].astype(np.float32)
        self.X, self.Y = (xx + .5) * Q, (yy + .5) * Q
        rng = np.random.default_rng(50)
        n = cv2.GaussianBlur(rng.random((self.lh, self.lw)).astype(np.float32), (0, 0), 6)
        n = (n - n.min()) / (n.max() - n.min() + 1e-6)
        self.haze = np.tile(n, (2, 2))                               # scrolled with time: drifting smoke in the beams
        self.ball = [(rng.uniform(0, 941), rng.uniform(40, 1000), rng.uniform(.6, 1.4), rng.integers(0, 8))
                     for _ in range(170)]
        self.spark_list = self._sparks(np.random.default_rng(3))

    # ---------------------------------------------------------------- helpers
    @staticmethod
    def out(cam, x, y):
        q = cam @ np.array([x, y, 1.]); return float(q[0]), float(q[1])

    def _haze(self, t):
        ox = int(t * 9) % self.lw; oy = int(t * 4) % self.lh
        return self.haze[oy:oy + self.lh, ox:ox + self.lw]

    def _screen(self, d, buf, gain=1.):
        b = cv2.resize(buf, (self.ow, self.oh), interpolation=cv2.INTER_LINEAR)
        np.clip(b * gain, 0, 1, out=b)
        d[:] = 1 - (1 - d) * (1 - b)

    def _cone(self, buf, o, ang, spread, length, color, k, gain):
        dx, dy = math.sin(ang), math.cos(ang)
        vx, vy = self.X - o[0], self.Y - o[1]
        along = vx * dx + vy * dy
        across = np.abs(vx * dy - vy * dx)
        w = 5 * k + np.maximum(along, 0) * math.tan(spread)
        m = np.exp(-2.4 * (across / np.maximum(w, 1)) ** 2) + .5 * np.exp(-9 * (across / np.maximum(w, 1)) ** 2)
        m *= np.clip(along / (25 * k), 0, 1) * np.exp(-np.maximum(along, 0) / (length * k))
        r2 = (vx * vx + vy * vy) / (9 * k) ** 2                      # the lamp's own glow
        m += 1.6 * np.exp(-r2)
        buf += (m * gain)[..., None] * np.float32(color)

    # ---------------------------------------------------------------- plate lighting (before the characters)
    def plate(self, d, cam, name, t):
        """beams, wash and floor light for one plate. d: the warped plate (output px, float RGB), changed in place."""
        rig = RIGS.get(name)
        lv, pv = show(t), party(t)
        if rig is None or lv < .01: return
        k = float(cam[0, 0])                                         # output px per plate px
        haze = .55 + .9 * self._haze(t)
        self._wash(d, t, lv)
        buf = np.zeros((self.lh, self.lw, 3), np.float32)
        beat = t / BEAT; bar = int(beat // 4)
        pulse = .78 + .22 * max(0., 1 - (beat % 1) / .35)            # every beat kicks the rig a little
        c_l, c_r = BARS[bar % len(BARS)]
        heads = rig['heads']
        for i, (x, y) in enumerate(heads):
            left = x < 470
            side = -1 if left else 1
            sp = 1.0 + 1.6 * pv                                      # party mode sweeps faster
            ph = t * sp * 2 * math.pi / (BEAT * 4) + (i % 3) * .7
            # pairs mirror each other, so the rig crosses and opens like a real show
            ang = side * (.18 + .28 * math.sin(ph)) + (.25 * math.sin(t * 3.1 + i) * pv)
            if name == 'crowd': ang *= 1.3
            col = PALETTE[(i + bar * 3) % len(PALETTE)] if pv > .5 else (c_l if left else c_r)
            g = .42 * lv * pulse * (1 - .35 * (i % 2) * (1 - pv))
            self._cone(buf, self.out(cam, x, y), ang, .085 + .03 * (i % 2), rig['length'], col, k, g)
        for i, (x, y) in enumerate(rig['towers']):
            side = 1 if x < 470 else -1                              # towers point in across the stage
            ang = side * (.9 + .25 * math.sin(t * 1.3 + i * 1.9)) + side * .2 * pv * math.sin(t * 5 + i)
            col = (c_r if x < 470 else c_l) if pv < .5 else PALETTE[(i * 3 + bar) % 8]
            self._cone(buf, self.out(cam, x, y), ang, .07, rig['length'] * .8, col, k, .3 * lv * pulse)
        buf *= haze[..., None]
        # beams stop at the stage deck (the crowd in front of it stays in its own light)
        sy = self.out(cam, 0, rig['stop'])[1]
        buf *= np.clip((sy - self.Y) / (30 * k), 0, 1)[..., None]
        if rig.get('floor'):
            self._floor(buf, cam, rig['floor'], t, lv, pv, k, c_l, c_r)
        if rig.get('clip'):
            m = np.zeros((self.lh, self.lw), np.uint8)
            cv2.fillPoly(m, [np.int32([[(p[0] - .5 * Q) / Q, (p[1] - .5 * Q) / Q] for p in
                                       (self.out(cam, *q) for q in rig['clip'])])], 255)
            buf *= cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 1.2)[..., None]
        if rig.get('spill'):                                         # the show's colour spills into the wings
            m = np.zeros((self.lh, self.lw), np.uint8)
            cv2.fillPoly(m, [np.int32([[(p[0] - .5 * Q) / Q, (p[1] - .5 * Q) / Q] for p in
                                       (self.out(cam, *q) for q in rig['spill'])])], 255)
            m = cv2.GaussianBlur(m.astype(np.float32) / 255, (0, 0), 10 * k / Q + 1)
            mix = .5 + .5 * math.sin(beat * math.pi / 2)
            col = np.float32(c_l) * mix + np.float32(c_r) * (1 - mix)
            buf += (m * .16 * lv * pulse)[..., None] * col
        self._screen(d, buf)

    def _wash(self, d, t, lv):
        """recolour the drawn rig's blue light, a little: blue -> magenta / purple / red on the bars"""
        beat = t / BEAT
        target = [300, 275, 345, 190, 30, 230][int(beat // 4) % 6]
        shift = ((target - 225 + 180) % 360) - 180
        amt = .55 * lv * (1 if party(t) < .5 else .8)
        if amt < .02: return
        hsv = cv2.cvtColor(d, cv2.COLOR_RGB2HSV)
        h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
        blue = np.clip((s - .25) / .3, 0, 1) * np.clip(1 - np.abs(((h - 225 + 180) % 360) - 180) / 45, 0, 1)
        w = blue * amt
        hsv[..., 0] = (h + shift * w) % 360
        d[:] = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    def _floor(self, buf, cam, box, t, lv, pv, k, c_l, c_r):
        x0, y0, x1, y1 = box
        for i in range(4):
            u = .5 + .45 * math.sin(t * (.7 + .25 * i) * (1 + pv) + i * 1.7)
            x = x0 + (x1 - x0) * u; y = y0 + (y1 - y0) * (.35 + .5 * ((i * .37) % 1))
            cx, cy = self.out(cam, x, y)
            rx, ry = 70 * k, 16 * k
            m = np.exp(-(((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2) * 1.6)
            col = (c_l if i % 2 else c_r) if pv < .5 else PALETTE[(i + int(t / BEAT)) % 8]
            buf += (m * .55 * lv)[..., None] * np.float32(col)

    # ---------------------------------------------------------------- mirror ball (on the plate)
    def mirror_ball(self, d, cam, t, amount, ball=None):
        """reflections swept round the room; ball=(x, y, r) in plate px also draws the ball itself"""
        if amount < .01: return
        k = float(cam[0, 0]); layer = np.zeros_like(d)
        for i, (x0, y, sz, ci) in enumerate(self.ball):
            x = (x0 + t * 95) % 941
            tw = .55 + .45 * math.sin(t * 7 + i)
            px, py = self.out(cam, x, y)
            if -10 < px < self.ow + 10 and -10 < py < self.oh + 10:
                col = np.float32(PALETTE[ci]) * .35 + .65
                cv2.circle(layer, (int(px), int(py)), max(1, int(2.2 * sz * k)), tuple(float(v) for v in col * tw), -1,
                           cv2.LINE_AA)
        layer = cv2.GaussianBlur(layer, (0, 0), max(.6, .8 * k))
        d[:] = 1 - (1 - d) * (1 - np.clip(layer * amount * .9, 0, 1))
        if ball is not None:
            bx, by, br = ball
            cx, cy = self.out(cam, bx, by); r = br * k
            if -r < cx < self.ow + r and -r < cy < self.oh + r:
                top = self.out(cam, bx, 0)
                cv2.line(d, (int(cx), int(top[1])), (int(cx), int(cy - r)), (.1, .1, .12), max(1, int(1.5 * k)), cv2.LINE_AA)
                cv2.circle(d, (int(cx), int(cy)), int(r), (.03, .03, .05), -1, cv2.LINE_AA)
                cv2.circle(d, (int(cx), int(cy)), int(r * .93), (.55, .58, .66), -1, cv2.LINE_AA)
                rot = (t * 2.2) % 1
                for a in range(-4, 5):                               # facets: spinning meridians and parallels
                    yy = cy + r * .93 * a / 4.6
                    cv2.line(d, (int(cx - r), int(yy)), (int(cx + r), int(yy)), (.25, .27, .33), 1, cv2.LINE_AA)
                for m in range(8):
                    ph = (m / 8 + rot) % 1
                    xx = cx + r * .93 * math.cos(math.pi * ph)
                    cv2.ellipse(d, (int(cx), int(cy)), (max(1, int(abs(xx - cx))), int(r * .93)), 0, -90, 90,
                                (.25, .27, .33), 1, cv2.LINE_AA)
                for m in range(10):                                  # glints
                    a = m * 2.4 + t * 3
                    gx, gy = cx + r * .6 * math.cos(a), cy + r * .6 * math.sin(a * 1.3)
                    v = max(0., math.sin(t * 9 + m * 1.7))
                    cv2.circle(d, (int(gx), int(gy)), max(1, int(r * .12)), (v, v, v * .95), -1, cv2.LINE_AA)
                cv2.circle(d, (int(cx), int(cy)), int(r), (0, 0, 0), max(1, int(1.6 * k)), cv2.LINE_AA)

    # ---------------------------------------------------------------- spark fountains ("gerbs") on UNIT
    def _sparks(self, rng):
        out = []
        for gx in (130, 290, 420, 640, 810):
            for j in range(260):
                te = UNIT - .02 + 3.2 * rng.uniform(0, 1) ** 1.25
                ang = rng.normal(0, .12)
                v = rng.uniform(700, 1050)
                out.append((gx + rng.normal(0, 4), te, v * math.sin(ang), -v * math.cos(ang), rng.uniform(.45, .9),
                            rng.uniform(.6, 1.)))
        return out

    def sparks(self, d, cam, t, floor_y=930):
        if t < UNIT - .05 or t > UNIT + 4.2: return
        k = float(cam[0, 0]); layer = np.zeros_like(d)
        g = 1500.
        for (x0, te, vx, vy, life, b) in self.spark_list:
            a = t - te
            if a < 0 or a > life: continue
            def pos(a):
                return x0 + vx * a, floor_y + vy * a + .5 * g * a * a
            x1, y1 = pos(a); x2, y2 = pos(max(0, a - .03))
            p1, p2 = self.out(cam, x1, y1), self.out(cam, x2, y2)
            fade = (1 - a / life) * b
            col = (1. * fade, .85 * fade, .45 * fade)
            cv2.line(layer, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), col, max(1, int(1.4 * k)), cv2.LINE_AA)
        glow = cv2.GaussianBlur(layer, (0, 0), max(1., 2.5 * k))
        d[:] = 1 - (1 - d) * (1 - np.clip(layer + glow * 1.5, 0, 1))

    # ---------------------------------------------------------------- after the characters
    def spots(self, d, cam, t, targets, level=None):
        """dim the stage outside follow-spots. targets: [(x, floor_y, height)] plate px, one per lit person"""
        lv = dim(t) if level is None else level
        if lv > .995 or not targets: return
        k = float(cam[0, 0])
        m = np.zeros((self.lh, self.lw), np.float32)
        for tg in targets:
            x, fy, h = tg[:3]; w = tg[3] if len(tg) > 3 else 1.
            if w < .01: continue
            cx, cy = self.out(cam, x, fy - h * .48)
            rx, ry = .36 * h * k, .58 * h * k
            m = np.maximum(m, w * np.exp(-(((self.X - cx) / rx) ** 2 + ((self.Y - cy) / ry) ** 2) ** 1.6))
            fx, fy2 = self.out(cam, x, fy)                           # the pool of light on the floor
            m = np.maximum(m, w * np.exp(-(((self.X - fx) / (.36 * h * k)) ** 2 + ((self.Y - fy2) / (.07 * h * k)) ** 2)))
        m = cv2.resize(m, (self.ow, self.oh), interpolation=cv2.INTER_LINEAR)[..., None]
        d *= lv + (1 - lv) * m
        # the spot's own beam in the haze, from high above
        buf = np.zeros((self.lh, self.lw, 3), np.float32)
        for tg in targets:
            x, fy, h = tg[:3]; w = tg[3] if len(tg) > 3 else 1.
            top = self.out(cam, x + 120, fy - h * 3.2)
            bot = self.out(cam, x, fy)
            ang = math.atan2(bot[0] - top[0], bot[1] - top[1])
            self._cone(buf, top, ang, .11, 2000, WHITE, k, .09 * (1 - lv) * w)
        buf *= (.6 + .7 * self._haze(t))[..., None]
        self._screen(d, buf)

    def flash(self, d, t):
        """a strobe hit: everything jumps in brightness for a frame (a flat white veil read as fog)"""
        f = strobe(t)
        if f > .01:
            d *= 1 + .5 * f
            d += .05 * f
            np.clip(d, 0, 1, out=d)

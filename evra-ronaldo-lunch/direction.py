"""The film: every shot, keyed to the words of the recording (words.json), and how each is staged.

The recording is Evra on a TV panel telling the story; the presenter's two questions are part of it. The picture is the
flashback, acted silently under his narration, except for the lines he quotes, which the person who said them lip-syncs:
Ronaldo's invitations ("let's go and having a lunch after training", "let's go in the garden and play two touch",
"let's go for swim", "after that let's have a sauna, jacuzzi") and Evra's replies ("I said Cristiano, we just finished",
"Cristiano, why we didn't stay at the training"), plus Evra's opening aside to camera ("Exactly, I think we should stay
at the training ground").  Each shot is a method of Film; SHOTS gives its start time (it runs to the next one)."""
import math, json, os
import numpy as np, cv2
import engine as E
from engine import T, S, R, smooth, ease, bump, camera, Plates, Prop, shadow
import performance as perf
from cast import actor
import fx

OW, OH = 1080, 1920
DUR = 80.33
WORDS = [w for turn in json.load(open(os.path.join(E.ROOT, 'words.json')))['turns'] for w in turn['words']]


def W(phrase, nth=0, end=False):
    """time of a spoken word (or the first word of a phrase); nth picks a later occurrence"""
    ws = phrase.split(); hits = []
    for i in range(len(WORDS) - len(ws) + 1):
        if [WORDS[i + j]['w'] for j in range(len(ws))] == ws: hits.append(WORDS[i + len(ws) - 1]['e'] if end else WORDS[i]['s'])
    return hits[nth]


# who lip-syncs which quoted line: (character, from, to)
E.LIPSYNC[:] = [('evra', 8.25, 10.5), ('ronaldo', 11.4, 13.6), ('ronaldo', 26.7, 28.9), ('evra', 29.2, 30.95),
                ('ronaldo', 33.2, 34.4), ('ronaldo', 35.0, 36.95), ('evra', 36.96, 39.65)]

SHOTS = [
    (0.0, 'carrington_open'), (3.3, 'gentle_lunch'), (5.6, 'competitive'), (8.25, 'evra_aside'), (10.6, 'invite'),
    (14.1, 'arrive'), (15.3, 'table'), (19.3, 'chicken'), (20.4, 'hope'), (21.0, 'doorway'), (21.65, 'water'),
    (23.8, 'fast_forward'), (26.6, 'garden_invite'), (29.1, 'just_finished'), (31.05, 'two_touch'), (33.2, 'swim_invite'),
    (34.35, 'laps'), (35.05, 'pool_invite'), (36.95, 'sauna'), (40.25, 'jacuzzi'), (44.6, 'goal'), (47.35, 'dior'),
    (50.3, 'warrior'), (52.3, 'happy'), (53.9, 'machine'), (56.95, 'tt_rally'), (60.65, 'so_close'), (61.7, 'determined'),
    (62.85, 'exactly'), (63.35, 'truth'), (65.5, 'rio_wins'), (67.4, 'scream'), (68.6, 'angry'), (70.3, 'delivery'),
    (72.45, 'two_weeks'), (73.8, 'revenge'), (76.0, 'rio_sulks'), (76.85, 'thats_cristiano'), (78.1, 'any_game'),
    (DUR, 'black'),
]


def shot_at(t):
    for i in range(len(SHOTS) - 1):
        if SHOTS[i][0] <= t < SHOTS[i + 1][0]: return SHOTS[i][1], SHOTS[i][0], SHOTS[i + 1][0]
    return 'black', DUR, DUR + 1


# acting keys that span shots ------------------------------------------------------------------------------------
K = perf.keys
K('evra', 'pant', [(0, 1.), (3.3, .4), (10.6, 1.), (12.5, 0., .3), (31.05, .3), (33.0, .7), (34.35, .9), (36.0, .4),
                   (40.25, 0.), (78.1, 1.)])
K('evra', 'blush', [(0, 0), (12.5, .5, .4), (15.3, .2), (40.25, .6), (44.6, 0), (52.3, .9), (53.9, 0)])
K('ronaldo', 'groove', [(0, .6), (5.6, 0), (10.6, .5), (14.1, 0), (26.6, .5), (29.1, 0), (78.1, .5)])
perf.done()


class Film:
    def __init__(self, ow=OW):
        self.ow, self.oh = ow, ow * 16 // 9
        self.plates = Plates(['carrington', 'house', 'dining', 'garden', 'pool', 'jacuzzi', 'sauna'])
        self.props = {}; self.blur_cache = {}

    # ------------------------------------------------------------------ helpers
    def cam(self, zoom, cx, cy, shake=0., t=0., rot=0.):
        if shake:
            cx += shake * (math.sin(t * 71) + .5 * math.sin(t * 113)); cy += shake * (math.cos(t * 83) + .5 * math.sin(t * 97))
        return camera(self.ow, zoom, cx, cy, self.oh, rot)

    def plate(self, name, cam, blur=0.):
        d = self.plates.warp(name, cam, self.ow, self.oh)
        if blur: d = cv2.GaussianBlur(d, (0, 0), blur * self.ow / 1080)
        return d

    def front(self, d, name, cam, poly, feather=1.2):
        rgb, a = self.plates.region(name, cam, self.ow, self.oh, poly, feather); d[:] = d * (1 - a) + rgb * a

    def prop(self, n):
        if n not in self.props: self.props[n] = Prop(n)
        return self.props[n]

    def put(self, d, cam, n, x, y, s, t, shadow_w=None, **kw):
        a = actor(n, kw.get('mirror', False))
        if shadow_w: shadow(d, cam, x, y, shadow_w)
        return a.put(d, cam, x, y, s, t, **kw)

    def layer(self, cam, n, x, y, s, t, **kw):
        """the actor on its own premultiplied RGBA layer (for water, tints)"""
        L = np.zeros((self.oh, self.ow, 4), np.float32); actor(n, kw.get('mirror', False)).put(L, cam, x, y, s, t, **kw); return L

    @staticmethod
    def comp(d, L, mask=None, tintc=None):
        a = L[..., 3:4] * (1 if mask is None else mask[..., None]); rgb = L[..., :3] * (1 if mask is None else mask[..., None])
        if tintc is not None: rgb = rgb * np.float32(tintc)
        d[:] = rgb + d * (1 - a)

    def pt(self, n, x, y, s, sx, sy, mirror=False):
        """a sheet point of drawing n placed at (x, y, scale) -> plate px"""
        a = actor(n); return a.to_plate(x, y, a.height(s), sx, sy, mirror)

    def bust(self, d, cam, n, x, y, h, t, **kw):
        """a waist-up drawing whose straight bottom edge is off the bottom of the frame"""
        return actor(n).draw(d, cam, x, y, h, t, **kw)

    def hop(self, t, t0, dur=.32, height=60.):
        a = (t - t0) / dur
        return height * 4 * a * (1 - a) if 0 <= a <= 1 else 0.

    # ------------------------------------------------------------------ render
    def render(self, t):
        name, t0, t1 = shot_at(t)
        if name == 'black': return np.zeros((self.oh, self.ow, 3), np.uint8)
        d = getattr(self, name)(t, (t - t0) / (t1 - t0), t0, t1)
        return np.uint8(np.clip(d * 255, 0, 255))

    # ================================================================== 1. Carrington
    def carrington_open(self, t, u, t0, t1):
        c = self.cam(1.02 + .04 * smooth(u), 470, 930); d = self.plate('carrington', c)
        # Ronaldo, still going: keepy-ups, bouncing on his toes
        per = .46; ph = (t % per) / per
        bob = 10 * abs(math.sin(math.pi * ph))
        rx, ry = 700, 1260
        self.put(d, c, 'r_stance', rx, ry, .82, t, shadow_w=270, hop=bob * .4)
        fx_, fy_ = self.pt('r_stance', rx, ry, .82, 395, 630)
        by = fy_ - 30 - 170 * math.sin(math.pi * ph) ** .9
        self.prop('ball').draw(d, c, fx_, by, 40, rot=t * 400)
        # Evra, done: hands on knees, panting, sweating
        ex, ey = 300, 1570
        self.put(d, c, 'e_tired', ex, ey, 1.32, t, shadow_w=520, look=(.2 * math.sin(t * 2), 0))
        hx, hy = self.pt('e_tired', ex, ey, 1.32, 300, 160)
        for i, ts in enumerate((.3, 1.2, 2.1, 2.9)):
            fx.sweat(d, c, hx + (-60 if i % 2 else 70), hy + 40, 9, ts, t, slide=60)
        a = ease(t, .2, .7) * (1 - ease(t, 2.9, 3.25))
        fx.text_out(d, 'CARRINGTON, 2008', self.ow / 2, self.oh * .085, self.ow * .062, fill=(1, 1, 1), alpha=a)
        fx.text_out(d, 'after training...', self.ow / 2, self.oh * .135, self.ow * .04, fill=(1, .85, .1), alpha=a)
        return d

    def gentle_lunch(self, t, u, t0, t1):
        c = self.cam(1.25 + .06 * u, 470, 760); d = self.plate('carrington', c, blur=5)
        grow = smooth((t - W('thinking')) / .25)
        pop = t > t1 - .12
        self.bust(d, c, 'eb_optimistic', 330, 1500, 640, t, look=(.5 * grow, -.55 * grow), smile=.6 * grow, blush=.5 * grow,
                  tilt=-3 * grow)
        if grow > 0 and not pop:
            bx, by = 640, 460
            fx.thought_bubble(d, c, bx, by, 470, 360, (430, 900), grow)
            if grow > .6:
                g = min(1, (grow - .6) / .4)
                for i, (ox, oy, w) in enumerate([(-95, 40, 170), (95, 40, 170), (0, -40, 190)]):
                    self.prop('plate_full').draw(d, c, bx + ox, by + oy + 8 * math.sin(t * 5 + i), w * g)
                self.prop('pitcher').draw(d, c, bx + 165, by - 70, 70 * g)
                self.prop('glass').draw(d, c, bx - 170, by - 60, 52 * g)
                for i in range(6):
                    q = fx.cpt(c, bx - 200 + i * 80, by - 120 + 40 * math.sin(i * 2.3))
                    fx.sparkle(d, q[0], q[1], 22, t, i * 1.3)
        if pop:
            q = fx.cpt(c, 640, 460); fx.puff(d, q[0], q[1], 260, (1, 1, 1), 1., True, 3)
        return d

    def competitive(self, t, u, t0, t1):
        d = np.zeros((self.oh, self.ow, 3), np.float32)
        fx.radial_bg(d, (.55, .04, .04), (.85, .12, .06), t, rays=16, spin=.6)
        punch = ease(t, W('competitive') - .05, W('competitive') + .08)
        c = self.cam(1.0 + .08 * u + .12 * punch, 470, 836, shake=6 * bump(t, W('competitive') + .1, .12), t=t)
        self.bust(d, c, 'rb_intense', 470, 1720, 1250, t, brow=-.3 - .4 * punch, look=(-.25, 0))
        fx.speed_lines(d, self.ow / 2, self.oh * .4, t, n=60, alpha=.35 + .3 * punch)
        g = bump(t, W('afternoon') + .15, .12)
        if g > .05:
            q = fx.cpt(c, *actor('rb_intense').to_plate(470, 1720, 1250, 849, 318)); fx.sparkle(d, q[0] - 10, q[1] - 14, 90 * g, 0)
        fx.vignette(d, (0, 0, 0), .6)
        return d

    def evra_aside(self, t, u, t0, t1):
        c = self.cam(1.3 + .05 * u, 470, 800); d = self.plate('carrington', c, blur=6)
        nod = 3 * bump(t, W('exactly') + .15, .12) + 2 * bump(t, W('should') + .1, .1)
        self.bust(d, c, 'eb_neutral', 470, 1560, 700, t, nod=nod, look=(-.45, .05), brow=.5 * bump(t, W('stay', 0) + .1, .25),
                  tilt=2 * math.sin(t * 2.2))
        return d

    def invite(self, t, u, t0, t1):
        c = self.cam(1.06 + .03 * u, 470, 980); d = self.plate('carrington', c)
        lunch = W('lunch', 2)
        # Ronaldo: "let's go and having a lunch after training", thumb over his shoulder
        beck = 16 * max(0, math.sin((t - 11.45) * 7)) * (11.45 < t < 13.7)
        self.put(d, c, 'r_invite', 300, 1520, 1.3, t, shadow_w=330, limbs={'hand': beck}, look=(.3, 0))
        # Evra: still puffed out... until he hears "lunch"
        if t < lunch:
            self.put(d, c, 'e_tired', 690, 1560, 1.25, t, shadow_w=480, mirror=True, look=(-.3 + .6 * ease(t, 11.5, 11.7), 0))
        else:
            sp = ease(t, lunch, lunch + .1)
            rub = 7 * math.sin(t * 26)
            self.put(d, c, 'e_optimism', 690, 1560, 1.25, t, shadow_w=380, mirror=True, hop=self.hop(t, lunch, .3, 70),
                     limbs={'hands': rub}, smile=.6, look=(.4, -.3))
            hx, hy = self.pt('e_optimism', 690, 1560, 1.25, 700, 180, mirror=True)
            for i in range(5):
                q = fx.cpt(c, hx - 150 + i * 75, hy - 150 + 30 * math.sin(i * 2))
                fx.sparkle(d, q[0], q[1], 30 * sp, t, i)
        return d

    def arrive(self, t, u, t0, t1):
        c = self.cam(1.12 + .05 * u, 470, 1090); d = self.plate('house', c)
        self.put(d, c, 'r_invite', 650, 1048, .62, t, shadow_w=150, limbs={'hand': 14 * max(0, math.sin(t * 8))}, look=(-.4, .2))
        # Evra skips up the path, rubbing his hands
        hops = [14.18, 14.52, 14.86]; v = (t - 14.18) / 1.0
        k = min(1, max(0, v)); x = 300 + 260 * k; y = 1640 - 520 * k; s = 1.15 - .5 * k
        h = sum(self.hop(t, h0, .34, 90 * s) for h0 in hops)
        self.put(d, c, 'e_optimism', x, y, s, t, shadow_w=260 * s, hop=h, limbs={'hands': 7 * math.sin(t * 26)}, smile=.6, look=(.5, -.2))
        for h0 in hops: fx.dust(d, c, x, y, h0 + .34, t, .6 * s, seed=int(h0 * 10))
        return d

    # ================================================================== 2. Lunch
    TABLE_POLY = [(203, 826), (754, 826), (941, 1066), (941, 1672), (0, 1672), (0, 1066)]

    def dining(self, t, zoom=1.7, cx=478, cy=700, evra='e_tinylunch', ron='r_lunch', e_kw=None, r_kw=None,
               e_plate='plate_full', r_plate='plate_full', glass=0., ron_here=True, shake=0.):
        c = self.cam(zoom, cx, cy, shake, t); d = self.plate('dining', c)
        self.put(d, c, evra, 330, 990, .78, t, **(e_kw or {}))
        if ron_here: self.put(d, c, ron, 630, 1030, .78, t, **(r_kw or {}))
        self.front(d, 'dining', c, self.TABLE_POLY)
        self.prop(e_plate).draw(d, c, 330, 872, 150)
        self.prop(r_plate).draw(d, c, 630, 872, 150)
        if glass > 0: self.prop('glass').draw(d, c, 330 + 160 * (1 - glass) + 120, 838, 46)
        return c, d

    def table(self, t, u, t0, t1):
        look_plate = ease(t, W('look', 0) + .05, W('look', 0) + .2) * (1 - ease(t, 17.95, 18.1))
        at_ron = ease(t, 17.95, 18.1)
        chew = max(0, math.sin(t * 6.5))
        c, d = self.dining(t, 1.7 + .1 * u, e_kw=dict(look=(.6 * at_ron, .7 * look_plate), brow=-.5 * ease(t, W('salad'), W('salad') + .3),
                                                      limbs={'fork': -6 * look_plate}),
                           r_kw=dict(limbs={'fork': -22 * chew}, smile=.7, look=(-.3, .2), blink=.85 * chew if chew > .6 else None))
        return d

    def chicken(self, t, u, t0, t1):
        c = self.cam(4.0 + .3 * u, 330, 860)
        d = self.plate('dining', c)
        self.front(d, 'dining', c, self.TABLE_POLY)
        self.prop('plate_full').draw(d, c, 330, 872, 150)
        pk = bump(t, W('white') + .1, .12) + bump(t, W('chicken') + .15, .12)
        self.prop('fork').draw(d, c, 362 + 5 * pk, 812 + 22 * pk, 18, rot=-28)
        q = fx.cpt(c, 330, 805)
        fx.text_out(d, 'plain white chicken.', self.ow / 2, self.oh * .2, self.ow * .06, fill=(1, 1, 1), alpha=ease(t, 19.45, 19.6))
        return d

    def hope(self, t, u, t0, t1):
        c = self.cam(1.4, 470, 720); d = self.plate('dining', c, blur=6)
        self.bust(d, c, 'eb_optimistic', 420, 1560, 700, t, look=(.9, -.2), brow=.4, smile=.3)
        return d

    def doorway(self, t, u, t0, t1):
        c = self.cam(2.3, 660, 560); d = self.plate('dining', c)
        a = (t - t0) / (t1 - t0)
        fx.tumbleweed(d, c, 760 - 190 * a, 778 - 14 * abs(math.sin(a * 8)), 24, -a * 9)
        fx.text_out(d, '...', self.ow * .5, self.oh * .15, self.ow * .1, fill=(1, 1, 1))
        return d

    def water(self, t, u, t0, t1):
        g = ease(t, W('just', 1) - .1, W('just', 1) + .25)
        stare = ease(t, W('water') - .05, W('water') + .1)
        c, d = self.dining(t, 1.7 + .25 * stare, cy=700 + 40 * stare, cx=478 - 60 * stare, glass=g,
                           e_kw=dict(look=(.5 * stare, .7 * stare), brow=-.6 * stare, limbs={'fork': 0}),
                           r_kw=dict(limbs={'fork': -22 * max(0, math.sin(t * 6.5))}, smile=.7, look=(-.4, 0)))
        if t > W('water') + .5:
            hx, hy = self.pt('e_tinylunch', 330, 990, .78, 210, 720)
            fx.sweat(d, c, hx, hy, 6, W('water') + .5, t, 20)
        return d

    def fast_forward(self, t, u, t0, t1):
        quick = W('quickly'); gone = W('that', 0) + .05
        r_empty = t > quick + .25; e_empty = t > quick + .9
        ron_here = t < gone
        c, d = self.dining(t, 1.7, e_plate='plate_empty' if e_empty else 'plate_full', r_plate='plate_empty' if r_empty else 'plate_full',
                           glass=1., ron_here=ron_here,
                           e_kw=dict(limbs={'fork': -20 * max(0, math.sin(t * 22))} if t < quick + .9 else {'fork': -14},
                                     look=(.6 * (t > gone), 0)),
                           r_kw=dict(limbs={'fork': -24 * max(0, math.sin(t * 30))}, smile=.8, blink=.9))
        if not ron_here:
            fx.dust(d, c, 630, 700, gone, t, 1.5, n=8, seed=4)
            fx.motion_lines(d, c, 630, 640, 1000, 580, n=5, spread=140)
        # fast-forward badge
        x, y, s = self.ow * .82, self.oh * .08, self.ow * .045
        if t < gone and int(t * 3) % 2 == 0:
            for o in (0, s * 1.1):
                fx.poly(d, [(x - s + o, y - s * .8), (x + o, y), (x - s + o, y + s * .8)], (1, 1, 1), fx.INK, 3)
            fx.text_out(d, 'x8', x + s * 2, y, s * 1.2, fill=(1, 1, 1))
        return d

    # ================================================================== 3. Garden: two-touch
    def garden_invite(self, t, u, t0, t1):
        c = self.cam(1.12 + .04 * u, 470, 1030); d = self.plate('garden', c)
        beck = 14 * max(0, math.sin((t - 26.75) * 7)) * (26.75 < t < 28.9)
        self.put(d, c, 'r_invite', 320, 1500, 1.25, t, shadow_w=320, limbs={'hand': beck}, look=(.3, 0))
        fxp, fyp = self.pt('r_invite', 320, 1500, 1.25, 800, 640)
        flick = self.hop(t, W('two', 0) - .1, .5, 160)
        self.prop('ball').draw(d, c, fxp + 50, fyp - 18 - flick, 52, rot=t * 200 * (flick > 0))
        self.put(d, c, 'e_casual', 700, 1540, 1.22, t, shadow_w=330, mirror=True, look=(.3, .4), brow=-.4,
                 tilt=-2 * ease(t, W('garden'), W('garden') + .3))
        return d

    def just_finished(self, t, u, t0, t1):
        c = self.cam(1.4, 470, 860); d = self.plate('garden', c, blur=6)
        shake = 3 * math.sin(t * 12) * bump(t, 30.4, .35)
        self.bust(d, c, 'eb_disappointed', 470, 1580, 700, t, tilt=shake, look=(-.45, 0), brow=.6 * bump(t, W('cristiano', 0) + .1, .3))
        return d

    def two_touch(self, t, u, t0, t1):
        c = self.cam(1.1, 470, 1100); d = self.plate('garden', c)
        rx, ry, ex, ey = 230, 1480, 715, 1500
        # kicks: Ronaldo crisp, Evra slow; the ball rolls between their kicking feet
        rk = [31.15, 32.55]; ek = [31.95]
        def swing(t, kicks, back=-16, fwd=8, wind=.18):
            v = 0.
            for k0 in kicks:
                if k0 - wind <= t < k0: v = back * smooth((t - (k0 - wind)) / wind)
                elif k0 <= t < k0 + .25: v = back + (fwd - back) * smooth((t - k0) / .08) - fwd * smooth((t - k0 - .08) / .17)
            return v
        rs = swing(t, rk); es = swing(t, ek, -10, 4, .35)
        droop = 6 * ease(t, 32.0, 32.6) + 6 * ease(t, 33.0, 33.2)
        self.put(d, c, 'r_kick', rx, ry, 1.15, t, shadow_w=330, limbs={'leg': rs})
        self.put(d, c, 'e_kick', ex, ey + droop, .9, t, shadow_w=330, mirror=True, limbs={'leg': -es}, look=(.3, .5),
                 brow=-.5, tilt=-droop * .6)
        rf = self.pt('r_kick', rx, ry, 1.15, 880, 1070); ef = self.pt('e_kick', ex, ey, .9, 900, 950, mirror=True)
        legs = [(31.15, 31.75, rf, ef, 1.), (31.95, 32.5, ef, rf, .6), (32.55, 32.95, rf, ef, 1.)]
        bx, by = rf[0] + 30, rf[1]
        for a0, a1, p0, p1, power in legs:
            if t >= a0:
                v = min(1, (t - a0) / (a1 - a0)); v2 = v if power > .8 else 1 - (1 - v) ** 1.8
                bx = p0[0] + (p1[0] - p0[0]) * v2; by = p0[1] + (p1[1] - p0[1]) * v2 - (30 if power > .8 else 70) * math.sin(math.pi * v)
                if power < .8: by -= 0
        if t > 32.95: bx, by = ef[0] - 20, ef[1] - 10 + 6 * abs(math.sin(t * 15))   # it hits Evra's shin and dies there
        self.prop('ball').draw(d, c, bx, by - 22, 48, rot=-t * 600)
        if t > 32.95:
            q = fx.cpt(c, ef[0] - 20, ef[1] - 80); fx.text_out(d, 'BONK', q[0], q[1], self.ow * .05, fill=(1, .9, .2), alpha=1 - ease(t, 33.05, 33.2))
        if 31.15 < t < 31.6 or 32.55 < t < 32.9:
            fx.motion_lines(d, c, bx - 120, by - 22, bx - 40, by - 22, n=3, spread=26)
        return d

    def swim_invite(self, t, u, t0, t1):
        c = self.cam(1.35 + .1 * u, 470, 800); d = self.plate('garden', c, blur=6)
        self.bust(d, c, 'rb_smug', 470, 1580, 760, t, brow=.6 * math.sin(t * 16) * (33.25 < t < 33.7), look=(-.3, 0))
        return d

    # ================================================================== 4. Pool, sauna, jacuzzi
    def at_line(self, n, x, line_y, sheet_y, s):
        """the plate y to place drawing n at so its sheet row `sheet_y` lands on plate row `line_y` (a waterline, a rim)"""
        a = actor(n); h = a.height(s); oy = E.META[n]['off'][1]; k = a.k
        frac = ((sheet_y - oy) * k) / a.hh
        return line_y + (1 - frac) * h

    def swimmer(self, d, c, n, x, water_y, sheet_line, s, t, mirror=False, splashes=True, **kw):
        """a character in the water: drawn only above a wavy waterline, with rings round him"""
        y = self.at_line(n, x, water_y, sheet_line, s)
        L = self.layer(c, n, x, y, s, t, mirror=mirror, **kw)
        m = fx.waterline_mask(self.oh, self.ow, c, water_y, t, amp=4, wl=40)
        self.comp(d, L, m)
        if splashes: fx.ripples(d, c, x, water_y + 4, actor(n).height(s) * .55, t, n=2, alpha=.6)

    POOL_DECK = [(0, 1462), (941, 1462), (941, 1672), (0, 1672)]

    def laps(self, t, u, t0, t1):
        c = self.cam(1.12, 470, 1130); d = self.plate('pool', c)
        x = -160 + 1250 * u
        self.swimmer(d, c, 'r_laps', x, 1090, 1445, .62, t, mirror=True, look=(.4, 0))
        for i in range(4): fx.splash(d, c, x - 90 - i * 70, 1088, t0 + i * .15, t, .7, n=6, seed=i)
        fx.motion_lines(d, c, x - 420, 1020, x - 200, 1020, n=4, spread=90)
        ey = self.at_line('e_pool', 300, 1462, 1530, 1.25)
        self.put(d, c, 'e_pool', 300, ey, 1.25, t, look=(.5 * math.sin(math.pi * u * 2), 0))
        self.front(d, 'pool', c, self.POOL_DECK)
        return d

    def pool_invite(self, t, u, t0, t1):
        c = self.cam(1.25 + .06 * u, 470, 1120); d = self.plate('pool', c)
        rise = ease(t, t0, t0 + .25)
        self.swimmer(d, c, 'r_swim', 600, 1060 + 120 * (1 - rise), 1345, .78, t, look=(-.4, .1),
                     brow=.5 * bump(t, W('sauna') + .1, .2) + .5 * bump(t, W('jacuzzi') + .1, .2))
        if t < t0 + .4: fx.splash(d, c, 600, 1062, t0, t, 1.2, n=14, seed=9)
        ey = self.at_line('e_pool', 250, 1462, 1530, 1.3)
        self.put(d, c, 'e_pool', 250, ey, 1.3, t, look=(.6, -.1), brow=-.4 * ease(t, W('sauna'), W('sauna') + .3))
        self.front(d, 'pool', c, self.POOL_DECK)
        return d

    def sauna(self, t, u, t0, t1):
        c = self.cam(1.22 + .05 * u, 470, 1000); d = self.plate('sauna', c)
        fx.steam(d, c, 700, 900, t, 2.2, n=4, seed=1, alpha=.35); fx.steam(d, c, 250, 820, t, 2.0, n=3, seed=5, alpha=.3)
        # Ronaldo: jump squats, thumbs up, in the sauna
        per = .55; ph = ((t - t0) % per) / per
        hop = 70 * math.sin(math.pi * ph) ** 1.2
        self.put(d, c, 'r_exercise', 650, 1330, 1.0, t, shadow_w=300, hop=hop, squash=.06 * bump(ph, 0, .12) + .06 * bump(ph, 1, .12),
                 look=(-.5, 0), smile=.4)
        # Evra on the bench: "I was like, Cristiano, why we didn't stay at the training?"
        self.put(d, c, 'e_sauna', 300, 1150, 1.05, t, look=(.7, 0), brow=.4 * bump(t, W('why') + .1, .3) - .2,
                 tilt=-2 * ease(t, W('cristiano', 1), W('cristiano', 1) + .3), blink=.9 * bump(t, 39.85, .1))
        hx, hy = self.pt('e_sauna', 300, 1150, 1.05, 690, 1230)
        for i, ts in enumerate((37.3, 38.1, 38.9, 39.7)): fx.sweat(d, c, hx - 10 + 70 * (i % 2), hy + 20 * (i % 3), 9, ts, t, 70)
        if t > 39.62:
            q = fx.cpt(c, *self.pt('r_exercise', 650, 1330, 1.0, 600, 1300)); fx.sparkle(d, q[0], q[1] - 60, 50, t)
        return d

    def jacuzzi_front(self):
        pts = [(x, 960 + 178 * math.sqrt(max(0, 1 - ((x - 470) / 560) ** 2))) for x in range(0, 942, 20)]
        return pts + [(941, 1672), (0, 1672)]

    def jacuzzi(self, t, u, t0, t1):
        c = self.cam(1.3 + .05 * u, 470, 1010); d = self.plate('jacuzzi', c)
        # Ronaldo swims laps of a jacuzzi
        lap = 1.6; a = 2 * math.pi * ((t - t0) / lap) + math.pi
        x = 470 + 300 * math.cos(a); wy = 1028 + 50 * math.sin(a)
        moving_right = -math.sin(a) > 0
        self.swimmer(d, c, 'r_laps', x, wy, 1445, .42 + .04 * math.sin(a), t, mirror=moving_right, look=(.3, 0))
        fx.splash(d, c, x + (-60 if moving_right else 60), wy, t - (t - t0) % .3, t, .5, n=5, seed=int(t * 3))
        # Evra, finally relaxing... until the wave
        splash_t = [41.85, 43.45, W('right', 0) + .1]
        hit = max([bump(t, s + .1, .25) for s in splash_t] + [0])
        relax = ease(t, t0 + .2, t0 + .9) * (1 - hit)
        ey = self.at_line('e_pool', 300, 1132, 1530, .95)
        self.put(d, c, 'e_pool', 300, ey, .95, t, blink=.95 * relax, smile=.5 * relax, blush=.4 * relax, brow=-.6 * hit,
                 tilt=-3 * relax)
        self.front(d, 'jacuzzi', c, self.jacuzzi_front())
        hx, hy = self.pt('e_pool', 300, ey, .95, 260, 1260)
        for s in splash_t:
            fx.splash(d, c, hx, hy + 90, s, t, 1.4, n=16, seed=int(s * 10))
            if s <= t < s + .5: fx.text_out(d, 'SPLOSH', *fx.cpt(c, hx + 60, hy - 120), self.ow * .06, fill=(.5, .85, 1), alpha=1 - (t - s) / .5)
        return d

    # ================================================================== 5. What he became
    def goal(self, t, u, t0, t1):
        c = self.cam(1.05, 470, 950); d = self.plate('carrington', c)
        kick = 45.35; arrive = W('goal') + .02; siu = 46.15
        if t < siu:
            sw = -14 * ease(t, kick - .2, kick) + 22 * ease(t, kick, kick + .07) - 8 * ease(t, kick + .1, kick + .3)
            self.put(d, c, 'r_kick', 300, 1320, .95, t, shadow_w=280, limbs={'leg': sw}, look=(.4, -.2))
            fp = self.pt('r_kick', 300, 1320, .95, 880, 1070)
        else:
            j = self.hop(t, siu, .55, 220)
            self.put(d, c, 'r_stance', 330, 1330, .95, t, shadow_w=280, hop=j, squash=.1 * bump(t, siu + .56, .05), look=(-.3, 0))
            fx.dust(d, c, 330, 1330, siu + .55, t, 1.0, seed=3)
            if t > siu + .1:
                q = fx.cpt(c, 470, 470); fx.text_out(d, 'SIUUU!', q[0], q[1] - 40 * ease(t, siu, siu + .3), self.ow * .1,
                                                      fill=(1, .85, .1), scale=ease(t, siu + .05, siu + .2))
            fp = None
        if fp is not None and t < kick:
            self.prop('ball').draw(d, c, fp[0] + 25, fp[1] - 20, 44)
        elif t < arrive + .5:
            v = min(1, (t - kick) / (arrive - kick)); tx, ty = 800, 590
            k0 = self.pt('r_kick', 300, 1320, .95, 880, 1070); sx, sy = k0[0] + 25, k0[1] - 20
            bx = sx + (tx - sx) * v; by = sy + (ty - sy) * v - 160 * math.sin(math.pi * v)
            if t < arrive: self.prop('ball').draw(d, c, bx, by, 44 - 26 * v, rot=t * 900); fx.motion_lines(d, c, bx - 80, by + 30, bx - 20, by + 8, 3, 18)
            else: self.prop('ball').draw(d, c, tx + 6 * math.sin(t * 40), ty + 10, 18)
        if t >= arrive:
            fx.confetti(d, t, arrive, n=80)
            q = fx.cpt(c, 800, 520); fx.text_out(d, 'GOAL!', q[0] - 80, q[1] - 60, self.ow * .1, fill=(1, 1, 1), scale=ease(t, arrive, arrive + .15) * (1 - ease(t, siu, siu + .1)))
        return d

    def dior(self, t, u, t0, t1):
        d = np.zeros((self.oh, self.ow, 3), np.float32)
        H, Wd = self.oh, self.ow
        Y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        d[:] = np.float32((1., .62, .78)) * (1 - Y) + np.float32((.62, .32, .55)) * Y
        for i in range(26):                                                     # bokeh
            rng = np.random.default_rng(i); x = rng.uniform(0, Wd); y = (rng.uniform(0, H) - t * 40 * rng.uniform(.5, 1.5)) % H
            lay = d.copy(); fx.ellipse(lay, (x, y), (rng.uniform(20, 60),) * 2, 0, (1, .9, .75), None, 0); d[:] = d * .82 + lay * .18
        c = self.cam(2.25 + .15 * u, 470, 1060)
        wink = W('playboy') + .15
        self.put(d, c, 'r_robe', 470, 1600, 1.05, t, lean=-2 + 2 * math.sin(t * 1.4), tilt=3,
                 blink=[0., .95 * bump(t, wink, .18)], smile=.6, look=(-.35, 0), brow=.3)
        fx.confetti(d, t, t0, n=40, seed=8, colors=[(1, .4, .6), (1, 1, 1), (1, .8, .9)])
        for i, (px_, py_) in enumerate([(.3, .2), (.72, .17), (.2, .45), (.82, .4), (.5, .1), (.6, .55)]):
            fx.sparkle(d, px_ * Wd, py_ * H, 40, t, i * 1.7)
        q = fx.cpt(c, *self.pt('r_robe', 470, 1600, 1.05, 700, 1000)); fx.sparkle(d, q[0], q[1], 70, t * 1.3)
        fx.text_out(d, 'Christian Dior', Wd / 2, H * .09, Wd * .075, fill=(1, 1, 1), stroke=(.55, .25, .45), alpha=ease(t, W('christian') + .1, W('christian') + .4))
        fx.text_out(d, '...the playboy', Wd / 2, H * .145, Wd * .045, fill=(1, .9, .95), stroke=(.55, .25, .45), alpha=ease(t, W('playboy'), W('playboy') + .3))
        return d

    def warrior(self, t, u, t0, t1):
        hit = W('warrior')
        c = self.cam(1.35 + .1 * ease(t, hit - .05, hit + .08), 470, 1080, shake=8 * bump(t, hit + .1, .2), t=t)
        d = self.plate('carrington', c)
        fx.tint(d, (1.25, .55, .35), .75); fx.vignette(d, (.2, 0, 0), .7, .6)
        fx.speed_lines(d, self.ow / 2, self.oh * .4, t, n=50, color=(1, .9, .6), alpha=.25 + .3 * ease(t, hit - .05, hit + .1))
        for i in range(3): fx.dust(d, c, 200 + 280 * i, 1450, t0 + .25 * i + ((t - t0) // .75) * .75, t, 1.4, seed=i + int(t))
        self.put(d, c, 'r_stance', 470, 1500, 1.25, t, shadow_w=400, brow=-.8, look=(-.15, 0), hop=10 * bump(t, hit, .1))
        q = fx.cpt(c, *self.pt('r_stance', 470, 1500, 1.25, 342, 216))
        fx.sparkle(d, q[0], q[1], 80 * bump(t, hit + .2, .15), 0, color=(1, .95, .7))
        fx.text_out(d, 'CHRISTIAN THE WARRIOR', self.ow / 2, self.oh * .1, self.ow * .058, fill=(1, .85, .2),
                    scale=ease(t, hit - .1, hit + .1))
        return d

    def happy(self, t, u, t0, t1):
        c = self.cam(1.35, 470, 1000); d = self.plate('jacuzzi', c, blur=4)
        self.put(d, c, 'e_robe', 470, 1880, 1.6, t, smile=.9, nod=3 * bump(t, W('happy') + .1, .12), look=(-.2, 0), tilt=-3)
        for i in range(5):
            fx.sparkle(d, self.ow * (.2 + .15 * i), self.oh * (.2 + .05 * (i % 2)), 30, t, i)
        return d

    def machine(self, t, u, t0, t1):
        c = self.cam(1.1, 470, 1040); d = self.plate('garden', c)
        per = .42; n_rep = int((t - t0) / per); ph = ((t - t0) % per) / per
        self.put(d, c, 'r_exercise', 320, 1470, 1.12, t, shadow_w=330, hop=80 * math.sin(math.pi * ph) ** 1.2,
                 squash=.07 * bump(ph, 0, .12), look=(.3, 0), smile=.5)
        self.put(d, c, 'e_robe', 720, 1520, 1.05, t, shadow_w=300, mirror=True, look=(.4, .1), brow=-.4, nod=0)
        # batteries
        rq = fx.cpt(c, 320, 820); eq = fx.cpt(c, 720, 780)
        mach = W('machine')
        fx.battery(d, rq[0], rq[1] - 40, self.ow * .16, 1., '100%' if t < mach else '∞', t)
        fx.battery(d, eq[0], eq[1] - 110, self.ow * .16, .04, '2%', t, blink=True)
        fx.text_out(d, f'REPS: {997 + n_rep}', self.ow * .27, self.oh * .9, self.ow * .055, fill=(1, 1, 1))
        if t > mach:
            q = fx.cpt(c, *self.pt('r_exercise', 320, 1470, 1.12, 763, 1281)); fx.sparkle(d, q[0], q[1], 70 * bump(t, mach + .15, .15), 0)
            fx.text_out(d, 'MACHINE', self.ow / 2, self.oh * .1, self.ow * .1, fill=(.6, .9, 1), scale=ease(t, mach, mach + .12))
        return d

    # ================================================================== 6. Table tennis with Rio
    def tt_scene(self, t, c, d, rally, rio='rio_warning', far_kw=None, ron_kw=None):
        """from behind Ronaldo at the near end; Rio behind the far end. rally: list of (t_hit, from_end, to_end) with
        end 0 = Ronaldo (near), 1 = Rio (far); a smash past the player is (t, from, 'past')"""
        tb = fx.TABLE
        rio_x, rio_y, rio_h = 425, 1205, 225
        actor(rio).draw(d, c, rio_x, rio_y, rio_h, t, **(far_kw or {}))
        rp = actor(rio).to_plate(rio_x, rio_y, rio_h, 716, 1110)
        fx.paddle(d, c, rp[0], rp[1] + 6, 26, rot=-15)
        fx.tt_table(d, c, tb)
        # the ball
        ball = None
        for t_hit, a, b in rally:
            dur = .48 if b != 'past' else .32
            if t_hit <= t < t_hit + dur:
                v = (t - t_hit) / dur
                if b == 'past':                      # straight past the near player, growing
                    u0 = 1.; u1 = -.5; uu = u0 + (u1 - u0) * v; vv = .3 + .25 * v; hgt = 40 + 40 * v
                else:
                    u0, u1 = (.05, .97) if a == 0 else (.97, .05); uu = u0 + (u1 - u0) * v
                    vv = (.78 + (.3 - .78) * v) if a == 0 else (.3 + (.78 - .3) * v)
                    bounce = .72 if a == 0 else .28
                    hgt = 110 * abs(math.sin(math.pi * (v / bounce))) if v < bounce else 70 * math.sin(math.pi * (v - bounce) / (1 - bounce))
                bx, by = fx.tt_point(tb, uu, vv); sc = fx.tt_scale(tb, max(-.5, min(1, uu))) if uu >= 0 else 1 + -uu * 2.5
                ball = (bx, by - hgt * sc, 9 * sc)
        # Ronaldo from behind
        rx, ry, rh = 690, 1790, 900
        ra = actor('r_back'); ra.draw(d, c, rx, ry, rh, t, **(ron_kw or {}))
        hp = ra.to_plate(rx, ry, rh, 912, 562)
        fx.paddle(d, c, hp[0] + 6, hp[1] - 4, 52, rot=25)
        if ball:
            fx.pp_ball(d, c, *ball)
        return d

    def tt_rally(self, t, u, t0, t1):
        c = self.cam(1.12, 470, 1090); d = self.plate('carrington', c)
        rally = [(57.05 + .5 * i, i % 2, (i + 1) % 2) for i in range(6)] + [(60.15, 1, 'past')]
        lunge = 6 * ease(t, 60.2, 60.35)
        self.tt_scene(t, c, d, rally, far_kw=dict(look=(.3, .2)), ron_kw=dict(lean=-lunge, tilt=0))
        if t > 60.25:
            fx.text_out(d, 'RIO 11 - 9 CR7', self.ow / 2, self.oh * .1, self.ow * .07, fill=(1, 1, 1), scale=ease(t, 60.25, 60.4))
        return d

    def so_close(self, t, u, t0, t1):
        c = self.cam(1.35, 470, 820); d = self.plate('carrington', c, blur=6)
        self.bust(d, c, 'rb_confused', 470, 1560, 760, t, tilt=2 * math.sin(t * 9), look=(-.3, 0), brow=-.3)
        q = fx.cpt(c, 560, 730); fx.text_out(d, 'so close...', q[0], self.oh * .12, self.ow * .07, fill=(1, 1, 1))
        return d

    def determined(self, t, u, t0, t1):
        d = np.zeros((self.oh, self.ow, 3), np.float32); fx.radial_bg(d, (.5, .03, .03), (.95, .25, .05), t, 18, spin=1.2)
        c = self.cam(1.1 + .25 * u, 470, 700)
        self.bust(d, c, 'rb_intense', 470, 1600, 1150, t, brow=-.8, look=(-.2, 0))
        fx.speed_lines(d, self.ow / 2, self.oh * .38, t, 60, alpha=.45)
        fx.vignette(d, (0, 0, 0), .6)
        return d

    def exactly(self, t, u, t0, t1):
        c = self.cam(1.35, 470, 820); d = self.plate('carrington', c, blur=6)
        self.bust(d, c, 'eb_suspicious', 470, 1560, 720, t, nod=5 * bump(t, W('exactly', 1) + .12, .1), look=(-.5, 0))
        return d

    def truth(self, t, u, t0, t1):
        c = self.cam(1.4, 470, 820); d = self.plate('carrington', c, blur=6)
        sh = 40 * bump(t, W('truth') + .05, .18) + 30 * bump(t, W('rio', 1) + .1, .15)
        self.bust(d, c, 'rio_shrug', 470, 1580, 820, t, hop=sh, look=(.6 * math.sin(t * 2), 0), brow=.5)
        q = fx.cpt(c, 600, 720); fx.sweat(d, c, 560, 840, 10, 63.6, t, 50)
        return d

    def rio_wins(self, t, u, t0, t1):
        c = self.cam(1.12, 470, 1090); d = self.plate('carrington', c)
        smash = 66.1
        rally = [(65.55, 1, 0), (65.62 + .48, 0, 1)] if False else [(65.6, 0, 1), (smash, 1, 'past')]
        win = t > smash + .3
        self.tt_scene(t, c, d, rally, rio='rio_laugh' if win else 'rio_warning',
                      ron_kw=dict(lean=-8 * ease(t, smash + .1, smash + .25), tilt=0))
        if win:
            fx.confetti(d, t, smash + .3, n=50)
            fx.text_out(d, 'RIO WINS', self.ow / 2, self.oh * .1, self.ow * .1, fill=(1, .85, .1), scale=ease(t, smash + .3, smash + .45))
        return d

    def scream(self, t, u, t0, t1):
        c = self.cam(1.25, 470, 860); d = self.plate('carrington', c, blur=6)
        self.bust(d, c, 'rio_laugh', 700, 1500, 560, t, hop=15 * abs(math.sin(t * 18)))
        self.bust(d, c, 'eb_laugh', 300, 1620, 720, t, hop=18 * abs(math.sin(t * 20)), tilt=4 * math.sin(t * 20))
        for i, (x, y) in enumerate([(.2, .14), (.7, .2), (.45, .08)]):
            fx.text_out(d, 'HAHA', self.ow * x, self.oh * y + 10 * math.sin(t * 20 + i), self.ow * .08, fill=(1, 1, 1), rot=10 - 10 * i)
        return d

    def angry(self, t, u, t0, t1):
        c = self.cam(1.45 + .1 * u, 470, 800, shake=3 * u, t=t); d = self.plate('carrington', c, blur=6)
        fx.tint(d, (1.2, .6, .5), .5 * u)
        L = np.zeros((self.oh, self.ow, 4), np.float32)
        actor('rb_confused').draw(L, c, 470, 1560, 760, t, brow=-.9, look=(-.2, 0), tilt=1.5 * math.sin(t * 30) * u)
        r = .3 + .5 * ease(t, t0, t1 - .4)
        self.comp(d, L, tintc=(1., 1 - r * .55, 1 - r * .6))
        ears = [actor('rb_confused').to_plate(470, 1560, 760, sx, sy) for sx, sy in ((655, 810), (900, 790))]
        for i, (x, y) in enumerate(ears):
            fx.steam(d, c, x + (-20 if i == 0 else 20), y - 30, t * 1.6, 1.6, n=3, seed=i, alpha=.9 * ease(t, t0 + .2, t0 + .5))
        return d

    def delivery(self, t, u, t0, t1):
        c = self.cam(1.25, 540, 1090); d = self.plate('house', c)
        land = W('sent') + .2
        y = 1200 - max(0, 1 - (t - (land - .35)) / .35) * 900 if t < land else 1200
        sq = .15 * bump(t, land + .03, .05)
        self.put(d, c, 'r_invite', 330, 1300, .95, t, shadow_w=260, limbs={'hand': -10 * ease(t, W('tennis', 1), W('tennis', 1) + .15)},
                 look=(.6, .2), smile=.6)
        if t > land - .35:
            fx.box(d, c, 640, y, 260 * (1 + sq), 190 * (1 - sq), rot=0)
        fx.dust(d, c, 640, 1200, land, t, 1.3, seed=7)
        return d

    def two_weeks(self, t, u, t0, t1):
        c = self.cam(1.15, 470, 1080); d = self.plate('garden', c)
        fx.tint(d, (.35, .45, .85), .78); d *= .8
        q = fx.cpt(c, 760, 230); fx.ellipse(d, q, (60, 60), 0, (1, 1, .85), None, 0)
        tb = dict(near=((230, 1430), (710, 1430)), far=((360, 1180), (580, 1180)), top=20, leg=130)
        fx.tt_table(d, c, tb)
        per = .22; v = ((t - t0) % per) / per; go = int((t - t0) / per) % 2
        uu = v if go == 0 else 1 - v
        bx, by = fx.tt_point(tb, uu * .95, .55); sc = fx.tt_scale(tb, uu * .95)
        fx.pp_ball(d, c, bx, by - 50 * sc * math.sin(math.pi * v), 8 * sc)
        ra = actor('r_back'); ra.draw(d, c, 600, 1720, 720, t, lean=4 * math.sin(t * 28))
        hp = ra.to_plate(600, 1720, 720, 912, 562); fx.paddle(d, c, hp[0], hp[1], 44, rot=25 + 20 * math.sin(t * 28))
        fx.text_out(d, 'TWO WEEKS LATER...', self.ow / 2, self.oh * .12, self.ow * .075, fill=(1, .85, .1), scale=ease(t, t0, t0 + .15))
        return d

    def revenge(self, t, u, t0, t1):
        """from behind Rio now: Ronaldo at the far end smashes it straight past him"""
        c = self.cam(1.12, 470, 1090); d = self.plate('carrington', c)
        tb = fx.TABLE; smash = W('beat', 2) + .02; celebrate = W('rio', 3)
        # Evra watching from the side, applauding
        self.put(d, c, 'e_optimism', 860, 1180, .32, t, limbs={'hands': 8 * math.sin(t * 30) * (t > smash)}, mirror=True, smile=.6)
        rh = 420; ry = 1180 + .48 * rh
        j = self.hop(t, celebrate, .45, 120)
        actor('r_stance', True).draw(d, c, 520, ry, rh, t, hop=j, brow=-.6, look=(-.2, .1), mirror=True)
        hp = actor('r_stance', True).to_plate(520, ry, rh, 65, 398, mirror=True)
        fx.paddle(d, c, hp[0], hp[1] - j, 30, rot=40 * ease(t, smash - .1, smash) - 30 * ease(t, smash, smash + .1))
        fx.tt_table(d, c, tb)
        if smash <= t < smash + .3:
            v = (t - smash) / .3; uu = 1 - 1.5 * v
            bx, by = fx.tt_point(tb, min(1, max(0, uu)), .35 - .1 * v); sc = fx.tt_scale(tb, max(0, uu)) * (1 + max(0, -uu) * 3)
            fx.pp_ball(d, c, bx, by - 60 * sc, 9 * sc); fx.motion_lines(d, c, bx, by - 60 * sc - 60, bx, by - 60 * sc - 10, 3, 20 * sc)
        ba = actor('rio_back'); ba.draw(d, c, 270, 1810, 1010, t, lean=-6 * ease(t, smash + .05, smash + .2))
        if t > celebrate:
            fx.confetti(d, t, celebrate, n=60)
            fx.text_out(d, 'CR7 WINS', self.ow / 2, self.oh * .1, self.ow * .1, fill=(1, .85, .1), scale=ease(t, celebrate, celebrate + .15))
        return d

    def rio_sulks(self, t, u, t0, t1):
        c = self.cam(1.4, 470, 820); d = self.plate('carrington', c, blur=6)
        self.bust(d, c, 'rio_folded', 470, 1590, 800, t, look=(-.7, .3), brow=-.6)
        # a little rain cloud of his own
        q = fx.cpt(c, 470, 560); fx.puff(d, q[0], q[1], 110, (.55, .58, .65), 1., True, 2)
        for i in range(6):
            ph = (t * 2.2 + i / 6) % 1; x = q[0] - 80 + 32 * i; y = q[1] + 60 + 200 * ph
            cv2.line(d, (int(x * 4), int(y * 4)), (int((x - 6) * 4), int((y + 30) * 4)), (.55, .7, 1.), 4, cv2.LINE_AA, 2)
        return d

    def thats_cristiano(self, t, u, t0, t1):
        d = np.zeros((self.oh, self.ow, 3), np.float32); fx.radial_bg(d, (.75, .05, .08), (.95, .75, .15), t, 16, spin=.3)
        c = self.cam(1.15 + .15 * u, 470, 760)
        wink = W('ronaldo') + .1
        self.bust(d, c, 'rb_smug', 470, 1620, 1080, t, blink=[0., .95 * bump(t, wink, .15)], brow=.4, look=(-.3, 0))
        for i in range(6): fx.sparkle(d, self.ow * (.15 + .14 * i), self.oh * (.12 + .06 * (i % 3)), 40, t, i)
        fx.text_out(d, 'CR7', self.ow / 2, self.oh * .1, self.ow * .16, fill=(1, 1, 1), scale=ease(t, t0, t0 + .2))
        return d

    def any_game(self, t, u, t0, t1):
        c = self.cam(1.06, 470, 980); d = self.plate('carrington', c)
        self.put(d, c, 'r_invite', 300, 1520, 1.3, t, shadow_w=330, limbs={'hand': 16 * max(0, math.sin(t * 8))}, look=(.4, 0),
                 brow=.4 * bump(t, W('lose') + .1, .2))
        fp = self.pt('r_invite', 300, 1520, 1.3, 800, 640)
        per = .45; ph = (t % per) / per
        self.prop('ball').draw(d, c, fp[0] + 60, fp[1] - 25 - 120 * math.sin(math.pi * ph), 52, rot=t * 300)
        fall = 79.5; ang = 84 * ease(t, fall, fall + .42) ** 2
        ex, ey = 720, 1600
        cf = c @ T(ex - 60, ey) @ R(-ang) @ T(-(ex - 60), -ey)
        if ang < 1: shadow(d, c, ex, ey, 420)
        self.put(d, cf, 'e_tired', ex, ey, 1.1, t, mirror=True, look=(-.3, 0), blink=.95 * ease(t, fall - .2, fall))
        fx.dust(d, c, ex - 330, ey - 40, fall + .42, t, 1.8, n=9, seed=11)
        if t > fall + .5: fx.text_out(d, 'K.O.', self.ow * .7, self.oh * .55, self.ow * .1, fill=(1, .3, .2), scale=ease(t, fall + .5, fall + .6))
        return d

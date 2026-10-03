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
import cast
from cast import actor
import fx

OW, OH = 1080, 1920
BALL = 92.          # a football is about the size of a head: plate px per unit of character scale
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


# cuts where the story changes place (from -> to): these get a whip pan
WHIPS = [14.1, 15.3, 26.6, 34.35, 36.95, 40.25, 44.6, 47.35, 50.3, 52.3, 53.9, 56.95, 70.3, 72.45, 73.8, 76.85, 78.1]


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
        # a whip pan where the story moves to a new place: the old shot smears off to the left, the new one in
        for c_ in WHIPS:
            if -.1 <= t - c_ < .13:
                st = 1 - (c_ - t) / .1 if t < c_ else 1 - (t - c_) / .13
                d = fx.whip(d, st ** 1.5, -1 if t < c_ else 1)
        if not hasattr(self, '_vig'):
            Y, X = np.ogrid[:self.oh, :self.ow]
            q = np.sqrt(((X - self.ow / 2) / (self.ow * .5)) ** 2 + ((Y - self.oh * .47) / (self.oh * .5)) ** 2)
            self._vig = (1 - .2 * np.clip((q - .6) / .6, 0, 1) ** 1.6).astype(np.float32)[..., None]
        d = d * self._vig                                               # a soft vignette holds the eye on the middle
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
        bw = BALL * .82; by = fy_ - bw * .55 - 170 * math.sin(math.pi * ph) ** .9
        self.prop('ball').draw(d, c, fx_, by, bw, rot=t * 400)
        # Evra, done: hands on knees, panting, sweating
        ex, ey = 300, 1570
        self.put(d, c, 'e_tired', ex, ey, 1.32, t, shadow_w=520, look=(.2 * math.sin(t * 2), 0))
        hx, hy = self.pt('e_tired', ex, ey, 1.32, 300, 160)
        for i, ts in enumerate((.3, 1.2, 2.1, 2.9)):
            fx.sweat(d, c, hx + (-60 if i % 2 else 70), hy + 40, 9, ts, t, slide=60)
        a = ease(t, .2, .7) * (1 - ease(t, 2.9, 3.25))
        # Evra joined United in January 2006 and Ronaldo left in the summer of 2009: they overlapped 2006-2009
        fx.text_out(d, 'CARRINGTON, 2006-2009', self.ow / 2, self.oh * .085, self.ow * .058, fill=(1, 1, 1), alpha=a)
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
        self.put(d, c, 'r_invite', 300, 1540, 1.25, t, shadow_w=330, limbs={'hand': beck}, look=(.3, 0))
        # Evra: still puffed out... until he hears "lunch"
        if t < lunch:
            self.put(d, c, 'e_tired', 690, 1540, 1.25, t, shadow_w=480, mirror=True, look=(-.3 + .6 * ease(t, 11.5, 11.7), 0))
        else:
            sp = ease(t, lunch, lunch + .1)
            rub = 7 * math.sin(t * 26)
            self.put(d, c, 'e_optimism', 690, 1540, 1.25, t, shadow_w=380, mirror=True, hop=self.hop(t, lunch, .3, 70),
                     limbs={'hands': rub}, smile=.6, look=(.4, -.3))
            hx, hy = self.pt('e_optimism', 690, 1540, 1.25, 700, 180, mirror=True)
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

    # seated grown-ups: heads about halfway up the kitchen door frame, hands resting at the table's far edge, both
    # pairs of feet on the same floor (Ronaldo's longer legs put his head a little higher)
    E_SEAT = (300, 1088, 1.05); R_SEAT = (640, 1100, 1.02)

    # what each eater has on his fork, and where his mouth is (sheet px of his eating drawing)
    FOOD = {'r_lunch': dict(fork=(336, 812), mouth=(298, 806), kind='chicken'),
            'e_tinylunch': dict(fork=(368, 808), mouth=(253, 795), kind='floret')}

    @staticmethod
    def eating(t, bites, chew=.9, speed=1.):
        """a bite at each time in `bites`: lean in, mouth wide, chomp, then chew. -> dict of acting values and the food:
        food = 1 on the fork, (0..1) flying into the mouth, None eaten"""
        e = dict(vis=None, amp=None, tilt=0., lean=0., blink=None, food=1., looky=0.)
        last = max([b for b in bites if b <= t + .25 / speed], default=None)
        if last is None: return e
        a = (t - last) * speed
        if a < 0:                                                      # anticipation: lean towards the fork
            v = smooth((a + .25) / .25); e.update(lean=4. * v)
        elif a < .14:                                                  # mouth wide, the food goes in
            e.update(vis='AI', amp=.95, lean=4., food=a / .14)
        elif a < .24:                                                  # chomp
            e.update(vis='MBP', lean=4., food=None)
        elif a < .24 + chew:                                           # chewing, eyes half shut
            c = (a - .24) / chew; ph = (a - .24) * 9.5
            e.update(vis='E', amp=.42 * max(0., math.sin(math.pi * ph)) * (1 - .4 * c),
                     lean=4. * (1 - c), food=None, blink=.55 * (1 - c))
        else:                                                          # looks down at the plate: the next forkful
            e.update(food=None if a < .24 + chew + .3 else 1., looky=.6 * bump(a, .24 + chew + .25, .2))
        nxt = [b for b in bites if b > t + .25 / speed]
        if e['food'] is None and nxt and a > .24 + chew + .3: e['food'] = 1.
        if not nxt and a >= .14: e['food'] = None
        return e

    def draw_food(self, d, M, n, f, mouthM=None):
        """the forkful (plate output via the eater's body matrix M); f = 1 on the fork, < 1 on its way into the mouth"""
        if f is None: return
        sp = self.FOOD[n]; k = E.META[n]['scale']
        fx_, fy_ = (M @ [*E.P(n, *sp['fork']), 1])[:2]; mx, my = (M @ [*E.P(n, *sp['mouth']), 1])[:2]
        v = 1 - f if f < 1 else 0.; x = fx_ + (mx - fx_) * v; y = fy_ + (my - fy_) * v
        r = float(np.linalg.norm(M[:2, 0])) * k * 10 * (1 - .55 * v)
        if r < 1: return
        if sp['kind'] == 'chicken':
            # a slice of plain white chicken (the same pale tan as on the plates) with a leaf of salad stuck to it
            pts = [(x + r * 1.35 * math.cos(a) * (1 + .12 * math.sin(3 * a)), y + r * .85 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 24)]
            R_ = np.array([[math.cos(-.45), -math.sin(-.45)], [math.sin(-.45), math.cos(-.45)]])
            pts = [tuple(R_ @ (np.array(q) - (x, y)) + (x, y)) for q in pts]
            fx.poly(d, pts, (.93, .80, .64), fx.INK, max(1.5, r * .16))
            fx.ellipse(d, (x - r * .25, y - r * .3), (r * .7, r * .22), -25, (.99, .91, .78), None, 0)
            for o in (-.35, .15):
                cv2.line(d, (int((x - r * .7 + o * r) * 4), int((y + r * (.35 + o)) * 4)), (int((x + r * .5 + o * r) * 4), int((y + r * (-.05 + o)) * 4)),
                         (.8, .64, .47), max(1, int(r * .1)), cv2.LINE_AA, 2)
            fx.ellipse(d, (x + r * .75, y - r * .45), (r * .42, r * .26), 30, (.35, .68, .25), fx.INK, max(1., r * .1))
        else:
            for i, (ox, oy) in enumerate([(-.5, .1), (.45, .15), (0, -.35), (-.2, .3), (.25, -.05)]):
                fx.ellipse(d, (x + ox * r, y + oy * r), (r * .55, r * .5), 0, (.96, .95, .86), fx.INK, max(1.2, r * .12))
            for i, (ox, oy) in enumerate([(-.5, .1), (.45, .15), (0, -.35), (-.2, .3), (.25, -.05)]):
                fx.ellipse(d, (x + ox * r, y + oy * r), (r * .42, r * .37), 0, (.98, .97, .9), None, 0)
            cv2.line(d, (int(x * 4), int((y + r * .4) * 4)), (int(x * 4), int((y + r * 1.0) * 4)), (.45, .65, .3),
                     max(1, int(r * .25)), cv2.LINE_AA, 2)

    def eater(self, d, c, n, seat, t, bites, kw, speed=1., chew=.9):
        e = self.eating(t, bites, chew, speed) if bites else dict(vis=None, amp=None, tilt=0., lean=0., blink=None, food=1., looky=0.)
        kw = dict(kw or {})
        lk = kw.pop('look', (0., 0.)); kw.setdefault('blink', e['blink'])
        kw['tilt'] = kw.get('tilt', 0.) + e['tilt']; kw['lean'] = kw.get('lean', 0.) + e['lean']
        M = self.put(d, c, n, *seat, t, vis=e['vis'], amp=e['amp'], look=(lk[0], lk[1] + e['looky']), **kw)
        return M, e['food']

    def dining(self, t, zoom=1.3, cx=472, cy=700, evra='e_tinylunch', ron='r_lunch', e_kw=None, r_kw=None,
               e_plate='plate_full', r_plate='plate_full', glass=0., ron_here=True, shake=0., e_bites=(), r_bites=(),
               e_food=True, r_food=True, speed=1., chew=.9):
        c = self.cam(zoom, cx, cy, shake, t); d = self.plate('dining', c)
        Me, fe = self.eater(d, c, evra, self.E_SEAT, t, e_bites, e_kw, speed, chew)
        if ron_here: Mr, fr = self.eater(d, c, ron, self.R_SEAT, t, r_bites, r_kw, speed, chew)
        self.front(d, 'dining', c, self.TABLE_POLY)
        self.prop(e_plate).draw(d, c, self.E_SEAT[0], 895, 200)
        self.prop(r_plate).draw(d, c, self.R_SEAT[0], 895, 200)
        if glass > 0: self.prop('glass').draw(d, c, self.E_SEAT[0] + 200 * (1 - glass) + 150, 855, 60)
        if e_food: self.draw_food(d, Me, evra, fe)
        if ron_here and r_food: self.draw_food(d, Mr, ron, fr)
        return c, d

    def table(self, t, u, t0, t1):
        look_plate = ease(t, W('look', 0) + .05, W('look', 0) + .2) * (1 - ease(t, 17.95, 18.1))
        at_ron = ease(t, 17.95, 18.1)
        c, d = self.dining(t, 1.3 + .07 * u, e_kw=dict(look=(.6 * at_ron, .7 * look_plate), brow=-.5 * ease(t, W('salad'), W('salad') + .3)),
                           r_kw=dict(smile=.7, look=(-.3, .2)), r_bites=(15.75, 17.05, 18.35))
        return d

    def chicken(self, t, u, t0, t1):
        c = self.cam(3.4 + .3 * u, 300, 885)
        d = self.plate('dining', c)
        self.front(d, 'dining', c, self.TABLE_POLY)
        self.prop('plate_full').draw(d, c, 300, 895, 200)
        pk = bump(t, W('white') + .1, .12) + bump(t, W('chicken') + .15, .12)
        self.prop('fork').draw(d, c, 338 + 6 * pk, 826 + 28 * pk, 24, rot=-28)
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
        fx.tumbleweed(d, c, 790 - 240 * a, 790 - 22 * abs(math.sin(a * 8)), 42, -a * 9)
        fx.text_out(d, '...', self.ow * .5, self.oh * .15, self.ow * .1, fill=(1, 1, 1))
        return d

    def water(self, t, u, t0, t1):
        g = ease(t, W('just', 1) - .1, W('just', 1) + .25)
        stare = ease(t, W('water') - .05, W('water') + .1)
        c, d = self.dining(t, 1.3 + .3 * stare, cy=700 + 25 * stare, cx=472 - 70 * stare, glass=g,
                           e_kw=dict(look=(.5 * stare, .7 * stare), brow=-.6 * stare),
                           r_kw=dict(smile=.7, look=(-.4, 0)), r_bites=(21.9, 23.1))
        if t > W('water') + .5:
            hx, hy = self.pt('e_tinylunch', *self.E_SEAT, 210, 720)
            fx.sweat(d, c, hx, hy, 6, W('water') + .5, t, 20)
        return d

    def fast_forward(self, t, u, t0, t1):
        quick = W('quickly'); gone = W('that', 0) + .05
        r_empty = t > quick + .25; e_empty = t > quick + .9
        ron_here = t < gone
        c, d = self.dining(t, 1.3, e_plate='plate_empty' if e_empty else 'plate_full', r_plate='plate_empty' if r_empty else 'plate_full',
                           glass=1., ron_here=ron_here, speed=3.2, chew=.35,
                           e_bites=tuple(23.95 + .42 * i for i in range(int((quick + .9 - 23.95) / .42) + 1)),
                           r_bites=tuple(23.9 + .3 * i for i in range(int((quick + .25 - 23.9) / .3) + 1)),
                           e_food=t < quick + .9, r_food=t < quick + .25,
                           e_kw=dict(look=(.6 * (t > gone), 0)), r_kw=dict(smile=.8))
        if not ron_here:
            fx.dust(d, c, 640, 640, gone, t, 1.9, n=8, seed=4)
            fx.motion_lines(d, c, 640, 600, 1000, 540, n=5, spread=170)
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
        self.put(d, c, 'r_invite', 320, 1540, 1.22, t, shadow_w=320, limbs={'hand': beck}, look=(.3, 0))
        fxp, fyp = self.pt('r_invite', 320, 1540, 1.22, 800, 640)
        flick = self.hop(t, W('two', 0) - .1, .5, 220); bw = BALL * 1.22
        if not flick: shadow(d, c, fxp + 70, 1540, bw * 1.1)
        self.prop('ball').draw(d, c, fxp + 70, 1540 - bw / 2 - flick, bw, rot=t * 200 * (flick > 0))
        self.put(d, c, 'e_casual', 700, 1540, 1.22, t, shadow_w=330, mirror=True, look=(.3, .4), brow=-.4,
                 tilt=-2 * ease(t, W('garden'), W('garden') + .3))
        return d

    def just_finished(self, t, u, t0, t1):
        c = self.cam(1.4, 470, 860); d = self.plate('garden', c, blur=6)
        shake = 3 * math.sin(t * 12) * bump(t, 30.4, .35)
        self.bust(d, c, 'eb_disappointed', 470, 1580, 700, t, tilt=shake, look=(-.45, 0), brow=.6 * bump(t, W('cristiano', 0) + .1, .3))
        return d

    def two_touch(self, t, u, t0, t1):
        c = self.cam(1.05, 470, 1080); d = self.plate('garden', c)
        S2 = .8; rx, ry, ex, ey = 200, 1420, 755, 1420                  # a proper passing distance apart
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
        self.put(d, c, 'r_kick', rx, ry, S2, t, shadow_w=250, limbs={'leg': rs})
        self.put(d, c, 'e_kick', ex, ey + droop, S2, t, shadow_w=330, mirror=True, limbs={'leg': -es}, look=(.3, .5),
                 brow=-.5, tilt=-droop * .6)
        rf = self.pt('r_kick', rx, ry, S2, 880, 1070); ef = self.pt('e_kick', ex, ey, S2, 900, 950, mirror=True)
        bw = BALL * S2; ground = ry - bw / 2
        rx_ = rf[0] + bw * .35; ex_ = ef[0] - bw * .45                 # where each kicking foot meets the ball
        legs = [(31.15, 31.75, rx_, ex_, 1.), (31.95, 32.5, ex_, rx_, .6), (32.55, 32.95, rx_, ex_, 1.)]
        bx, hop_ = rx_, 0.
        for a0, a1, p0, p1, power in legs:
            if t >= a0:
                v = min(1, (t - a0) / (a1 - a0)); v2 = v if power > .8 else 1 - (1 - v) ** 1.8
                bx = p0 + (p1 - p0) * v2
                hop_ = (18 if power > .8 else 60) * abs(math.sin(math.pi * v * (1 if power > .8 else 2))) * (1 - v * .6)
        if t > 32.95: bx, hop_ = ex_ - 10 * smooth((t - 32.95) / .3), 30 * abs(math.sin((t - 32.95) * 12)) * math.exp(-(t - 32.95) * 5)
        shadow(d, c, bx, ry, bw * 1.05)
        self.prop('ball').draw(d, c, bx, ground - hop_, bw, rot=(bx - rx_) * 1.6)
        if t > 32.95:
            q = fx.cpt(c, ex_, ground - 120); fx.text_out(d, 'BONK!', q[0], q[1], self.ow * .07, fill=(1, .9, .2), alpha=1 - ease(t, 33.05, 33.2))
        if 31.15 < t < 31.6 or 32.55 < t < 32.9:
            fx.motion_lines(d, c, bx - 150, ground, bx - 60, ground, n=3, spread=bw * .6)
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
        x = 470 + 290 * math.cos(a); wy = 1035 + 45 * math.sin(a)
        moving_right = -math.sin(a) > 0
        self.swimmer(d, c, 'r_laps', x, wy, 1445, .58 + .06 * math.sin(a), t, mirror=moving_right, look=(.3, 0))
        fx.splash(d, c, x + (-60 if moving_right else 60), wy, t - (t - t0) % .3, t, .5, n=5, seed=int(t * 3))
        # Evra, finally relaxing... until the wave
        splash_t = [41.85, 43.45, W('right', 0) + .1]
        hit = max([bump(t, s + .15, .25) for s in splash_t] + [0])
        shut = max([bump(t, s + .2, .14) for s in splash_t] + [0])
        relax = ease(t, t0 + .2, t0 + .9) * (1 - hit)
        ey = self.at_line('e_pool', 300, 1132, 1530, .95)
        self.put(d, c, 'e_pool', 300, ey, .95, t, blink=max(.95 * relax, .98 * shut), smile=.5 * relax, blush=.4 * relax,
                 brow=-.7 * hit, tilt=-3 * relax)
        self.front(d, 'jacuzzi', c, self.jacuzzi_front())
        hx, hy = self.pt('e_pool', 300, ey, .95, 260, 1260)
        for i, s in enumerate(splash_t):
            fx.wave(d, c, hx + 95, 1128, s, t, 330, curl=-1, seed=i)
            if s + .1 <= t < s + .65:
                fx.text_out(d, 'SPLOSH!', *fx.cpt(c, hx + 150, hy - 210), self.ow * .075, fill=(.55, .87, 1),
                            scale=ease(t, s + .1, s + .2), alpha=1 - ease(t, s + .45, s + .65))
            for j, (ox, oy) in enumerate([(-40, -70), (35, -85), (5, -40)]):    # then the water runs down his face
                fx.sweat(d, c, hx + ox, hy + oy, 8, s + .45 + .08 * j, t, 60) if t < s + 1.5 else None
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
            self.prop('ball').draw(d, c, fp[0] + 30, 1320 - BALL * .95 / 2, BALL * .95)
        elif t < arrive + .5:
            v = min(1, (t - kick) / (arrive - kick)); tx, ty = 800, 590
            k0 = self.pt('r_kick', 300, 1320, .95, 880, 1070); sx, sy = k0[0] + 30, 1320 - BALL * .95 / 2
            bx = sx + (tx - sx) * v; by = sy + (ty - sy) * v - 160 * math.sin(math.pi * v)
            if t < arrive: self.prop('ball').draw(d, c, bx, by, BALL * .95 * (1 - .7 * v), rot=t * 900); fx.motion_lines(d, c, bx - 90, by + 34, bx - 25, by + 10, 3, 30)
            else: self.prop('ball').draw(d, c, tx + 6 * math.sin(t * 40), ty + 10, BALL * .95 * .3)
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
        self.put(d, c, 'r_exercise', 320, 1490, 1.08, t, shadow_w=330, hop=80 * math.sin(math.pi * ph) ** 1.2,
                 squash=.07 * bump(ph, 0, .12), look=(.3, 0), smile=.5)
        self.put(d, c, 'e_robe', 720, 1500, 1.08, t, shadow_w=300, mirror=True, look=(.4, .1), brow=-.4, nod=0)
        # batteries
        rq = fx.cpt(c, 320, 820); eq = fx.cpt(c, 720, 780)
        mach = W('machine')
        fx.battery(d, rq[0], rq[1] - 120, self.ow * .16, 1., '100%' if t < mach else '∞', t)
        fx.battery(d, eq[0], eq[1] - 230, self.ow * .16, .04, '2%', t, blink=True)
        fx.text_out(d, f'REPS: {997 + n_rep}', self.ow * .27, self.oh * .9, self.ow * .055, fill=(1, 1, 1))
        if t > mach:
            q = fx.cpt(c, *self.pt('r_exercise', 320, 1490, 1.08, 763, 1281)); fx.sparkle(d, q[0], q[1], 70 * bump(t, mach + .15, .15), 0)
            fx.text_out(d, 'MACHINE', self.ow / 2, self.oh * .1, self.ow * .1, fill=(.6, .9, 1), scale=ease(t, mach, mach + .12))
        return d

    # ================================================================== 6. Table tennis with Rio (side-on)
    # Rio at the left end (his microphone pose, the mic now a bat), Ronaldo at the right (his 3/4 view, mirrored, the
    # near arm raised with a bat). The table's ends are placed from where the bats meet the ball, so the ball always
    # meets a bat; the table is 0.4 of a man's height high and a little short of real length so all of it fits.
    TT_H = 550.; TT_FLOOR = 1330.
    PLAYERS = {0: ('rio_bat', False, 1.), 1: ('r_bat', True, 1.87 / 1.89)}
    SW = {'rio_bat': (0., 24., -40.), 'r_bat': (-38., -14., -88.)}        # (ready, wind-up, follow-through) degrees

    def tt_layout(self):
        if hasattr(self, '_tt'): return self._tt
        def contact_off(who):
            key, mir, hs = self.PLAYERS[who]; r, b, th = self.SW[key]
            return self._blade(key, 0., self.TT_FLOOR, self.TT_H * hs, mir, (b + th) / 2)
        cR = contact_off(0); cC = contact_off(1)
        xR = 128.; x0 = xR + cR[0] + 34; x1 = x0 + .74 * self.TT_H; xC = x1 + 34 - cC[0]
        self._tt = dict(x={0: xR, 1: xC}, x0=x0, x1=x1, top=self.TT_FLOOR - .4 * self.TT_H, depth=24)
        return self._tt

    @staticmethod
    def blade_part(key):
        a = actor(key, key == 'r_bat'); gx, gy, ux, uy, br, hl = cast.CAST[key]['bat']
        G = np.array(E.P(a.n, gx, gy)); u = np.array([ux, uy]) / math.hypot(ux, uy)
        return a, G, u, br * a.k, hl * a.k

    def _blade(self, key, x, y, h, mirror, ang):
        a, G, u, br, hl = self.blade_part(key)
        pv = next(iter(a.limbs.values()))[1]; Cb = G + u * (hl * .6 + br * .92)
        M = a.place(x, y, h, mirror) @ E.pivot(pv[0], pv[1], ang)
        return (M @ [Cb[0], Cb[1], 1])[:2]

    def holder(self, key):
        a, G, u, br, hl = self.blade_part(key)
        return {next(iter(a.limbs)): lambda dst, LM: fx.bat(dst, LM, G, u, br, hl)}

    @staticmethod
    def swing(t, hits, back, through, wind=.18, ret=.32):
        """degrees from the ready position: a wind-up, a quick swing through the ball centred on the hit, then back"""
        v = 0.
        for h in hits:
            if h - .035 - wind <= t < h - .035: v = back * smooth((t - (h - .035 - wind)) / wind)
            elif h - .035 <= t < h + .035: v = back + (through - back) * smooth((t - (h - .035)) / .07)
            elif h + .035 <= t < h + .035 + ret: v = through * (1 - smooth((t - h - .035) / ret))
        return v

    def player(self, who):
        key, mir, hs = self.PLAYERS[who]; L = self.tt_layout()
        return key, L['x'][who], self.TT_FLOOR, self.TT_H * hs, mir

    def contact(self, who):
        key, x, y, h, mir = self.player(who); r, b, th = self.SW[key]
        return self._blade(key, x, y, h, mir, (b + th) / 2)

    def bounce_pt(self, receiver):
        L = self.tt_layout(); xm = (L['x0'] + L['x1']) / 2
        x = xm - (xm - L['x0']) * .55 if receiver == 0 else xm + (L['x1'] - xm) * .55
        return np.array([x, L['top'] - L['depth'] * .5])

    def ball_at(self, t, hits, end=None):
        """hits: [(t, who)] (0 Rio, 1 Ronaldo); end = (t_end, (x, y), receiver) for a winner that does not come back.
        The ball flies from bat to bat over the net, bouncing once on the receiver's half. -> (x, y) or None"""
        segs = [(ta, tb, self.contact(wa), self.contact(wb), wb, 1.) for (ta, wa), (tb, wb) in zip(hits, hits[1:])]
        if end:
            ta, wa = hits[-1]; te, pe, rcv = end
            segs.append((ta, te, self.contact(wa), np.array(pe, float), rcv, .45))
        for ta, tb, pa, pb, rcv, lift in segs:
            if ta <= t <= tb:
                B = self.bounce_pt(rcv); fb = abs(B[0] - pa[0]) / max(1., abs(pb[0] - pa[0]))
                f = (t - ta) / (tb - ta)
                if f < fb:
                    s_ = f / fb; x = pa[0] + (B[0] - pa[0]) * s_; y = pa[1] + (B[1] - pa[1]) * s_ - lift * 120 * 4 * s_ * (1 - s_)
                else:
                    s_ = (f - fb) / (1 - fb); x = B[0] + (pb[0] - B[0]) * s_; y = B[1] + (pb[1] - B[1]) * s_ - lift * 75 * 4 * s_ * (1 - s_)
                return float(x), float(y)
        return None

    def tt_match(self, t, c, d, hits, end=None, rio='rio_bat', rio_kw=None, ron_kw=None, rio_ang=None, ron_ang=None, half_up=False,
                 ball=True, rio_here=True):
        L = self.tt_layout()
        b = self.ball_at(t, hits, end) if ball else None
        def look(x0, y0, mir=False):
            if b is None: return (0., 0.)
            lx = max(-1, min(1, (b[0] - x0) / 300)) * .85
            return (float(-lx if mir else lx), float(max(-1, min(1, (b[1] - y0) / 300)) * .55))
        if rio_here:
            key, x, y, h, mir = self.player(0)
            shadow(d, c, x, y, h * .45)
            rkw = dict(rio_kw or {})
            if rio == 'rio_bat':
                rkw.setdefault('look', look(x, y - h * .85))
                r0, bk, th = self.SW['rio_bat']
                ang = r0 + (self.swing(t, [hh for hh, w in hits if w == 0], bk - r0, th - r0) if rio_ang is None else rio_ang)
                actor('rio_bat').draw(d, c, x, y, h, t, limbs={'bat': ang}, holds=self.holder('rio_bat'), **rkw)
            else:
                actor(rio).draw(d, c, x + h * .06, y, actor(rio).height(1) / actor('rio_bat').height(1) * h, t, **rkw)
        fx.tt_side(d, c, L['x0'], L['x1'], L['top'], L['depth'], 14, self.TT_FLOOR, half_up=half_up)
        key, x, y, h, mir = self.player(1)
        shadow(d, c, x, y, h * .45)
        ckw = dict(ron_kw or {}); ckw.setdefault('look', look(x, y - h * .85, True))
        r0, bk, th = self.SW['r_bat']
        ang = r0 + (self.swing(t, [hh for hh, w in hits if w == 1], bk - r0, th - r0) if ron_ang is None else ron_ang)
        actor('r_bat', True).draw(d, c, x, y, h, t, mirror=True, limbs={'arm': ang}, holds=self.holder('r_bat'), **ckw)
        if b is not None:
            trail = [p for p in (self.ball_at(t - .018 * i, hits, end) for i in range(1, 5)) if p is not None]
            fx.tt_ball(d, c, b[0], b[1], 11, trail[::-1])
        return b

    def tt_cam(self, t, push=0.):
        return self.cam(1.0 + push, 470, 850)

    def tt_rally(self, t, u, t0, t1):
        c = self.tt_cam(t, .03 * u); d = self.plate('carrington', c)
        hits = [(57.2, 0), (57.6, 1), (58.0, 0), (58.4, 1), (58.8, 0), (59.2, 1), (59.62, 0)]
        past = (60.0, (1080, self.TT_FLOOR - .82 * self.TT_H), 1)              # Rio's winner flies past Ronaldo's ear
        whiff = self.swing(t, [60.02], 24, -60)
        late = t > 59.95
        b = self.tt_match(t, c, d, hits, past,
                          rio_kw=dict(brow=.5 * (t > 59.7), smile=.6 * (t > 59.8)),
                          ron_kw=dict(look=(1., -.2), brow=.6) if t > 60.05 else None,
                          ron_ang=whiff if late else None)
        for h, w in hits:                                                   # each hit: a little 'tok'
            if h <= t < h + .18:
                q = fx.cpt(c, *self.contact(w)); fx.text_out(d, 'PING!' if w == 0 else 'PONG!', q[0] + (120 if w == 0 else -120), q[1] - 30,
                                                             self.ow * .045, fill=(1, 1, 1), alpha=1 - (t - h) / .18)
        if t > 59.62 and t < 60.0 and b: fx.motion_lines(d, c, b[0] - 110, b[1] - 60, b[0] - 25, b[1] - 12, n=3, spread=26)
        if t > 60.1:
            fx.text_out(d, 'RIO 11 - 9 CR7', self.ow / 2, self.oh * .12, self.ow * .085, fill=(1, 1, 1), scale=ease(t, 60.1, 60.25))
        return d

    def truth(self, t, u, t0, t1):
        c = self.cam(1.35, 470, 840); d = self.plate('carrington', c, blur=6)
        nod = 3 * bump(t, W('truth') + .1, .12) + 3 * bump(t, W('exactly', 1) + .1, .1)
        a, G, u_, br, hl = self.blade_part('rio_bat')
        self.put(d, c, 'rio_bat', 470, 2120, 1.95, t, limbs={'bat': -14 * ease(t, t0, t0 + .3)}, holds=self.holder('rio_bat'),
                 brow=.55, smile=.7, nod=nod, look=(-.25, 0))
        for i in range(4):
            fx.sparkle(d, self.ow * (.2 + .2 * i), self.oh * (.16 + .05 * (i % 2)), 26, t, i)
        return d

    def rio_wins(self, t, u, t0, t1):
        c = self.tt_cam(t, .03 * u); d = self.plate('carrington', c)
        smash = 66.05; won = smash + .45
        hits = [(65.65, 1), (smash, 0)]
        past = (smash + .38, (1080, self.TT_FLOOR - .82 * self.TT_H), 1)
        self.tt_match(t, c, d, hits, past, rio='rio_bat' if t < won else 'rio_laughbig',
                      rio_kw=dict(smile=.5, brow=.3) if t < won else dict(hop=10 * abs(math.sin(t * 16))),
                      ron_kw=dict(look=(1., -.2), brow=.6) if t > smash + .3 else None,
                      ron_ang=self.swing(t, [smash + .3], 24, -60) if t > smash + .2 else None)
        if t > won:
            fx.confetti(d, t, won, n=60)
            fx.text_out(d, 'RIO WINS', self.ow / 2, self.oh * .12, self.ow * .11, fill=(1, .85, .1), scale=ease(t, won, won + .15))
        return d

    def scream(self, t, u, t0, t1):
        c = self.cam(1.25, 470, 860); d = self.plate('carrington', c, blur=6)
        self.put(d, c, 'rio_laughbig', 690, 1750, 1.55, t, hop=14 * abs(math.sin(t * 17)))
        self.bust(d, c, 'eb_laugh', 300, 1620, 720, t, hop=18 * abs(math.sin(t * 20)), tilt=4 * math.sin(t * 20))
        for i, (x, y) in enumerate([(.2, .14), (.7, .2), (.45, .08)]):
            fx.text_out(d, 'HAHA', self.ow * x, self.oh * y + 10 * math.sin(t * 20 + i), self.ow * .08, fill=(1, 1, 1), rot=10 - 10 * i)
        return d

    def two_weeks(self, t, u, t0, t1):
        """night, the garden: Ronaldo practising against a ball machine, and a cardboard Rio to aim at"""
        c = self.tt_cam(t); d = self.plate('garden', c)
        L = self.tt_layout(); per = .32
        n = int((t - t0) / per)
        # the cut-out: Rio's hero drawing on a cardboard backing, at Rio's end; it wobbles when a return hits it
        if not hasattr(self, '_cut'): self._cut = E.Sprite(fx.cardboard(E.part('rio_hero'), 70))
        key, x, y, h, mir = self.player(0)
        ret = [t0 + per * i + .09 + .26 for i in range(n + 1)]                 # when each return reaches the cut-out
        wob = sum(7 * math.sin((t - r) * 26) * math.exp(-(t - r) * 7) for r in ret if t >= r)
        sp = self._cut; sc = h * 1.1 / sp.h
        shadow(d, c, x, y, h * .4)
        q0, q1, q2 = fx.cpt(c, x + 10, y - h * .55), fx.cpt(c, x + 70, y), fx.cpt(c, x + 40, y)       # its wooden stand
        fx.poly(d, [q0, (q1[0], q1[1]), (q2[0], q2[1])], (.55, .38, .2), fx.INK, 3)
        CM = c @ T(x, y) @ R(wob) @ S(sc) @ T(-sp.w / 2, -sp.h)
        sp.draw(d, CM)
        bx, by = (CM @ [sp.w * .5, sp.h * .47, 1])[:2]                                            # a target on his chest
        for i, col in enumerate([(.85, .1, .1), (1, 1, 1), (.85, .1, .1), (1, 1, 1)]):
            fx.ellipse(d, (bx, by), (sp.w * sc * c[0, 0] * (.13 - .03 * i),) * 2, 0, col, fx.INK if i == 0 else None, 2)
        fx.tt_side(d, c, L['x0'], L['x1'], L['top'], L['depth'], 14, self.TT_FLOOR)
        mx, my = L['x0'] + 40, L['top'] - L['depth'] * .5
        noz = np.array(fx.cpt(np.eye(3), mx + .9 * 80, my - .7 * 80))
        hits = [(t0 + per * i + .09, 1) for i in range(n + 2)]
        fired = max([bump(t, t0 + per * i, .05) for i in range(n + 2)] + [0])
        fx.ball_machine(d, c, mx, my, 80, t, fired)
        r0, bk, th = self.SW['r_bat']
        key, x, y, h, mir = self.player(1); shadow(d, c, x, y, h * .45)
        actor('r_bat', True).draw(d, c, x, y, h, t, mirror=True, limbs={'arm': r0 + self.swing(t, [hh for hh, w in hits], (bk - r0) * .7, (th - r0) * .7, wind=.07, ret=.14)},
                                  holds=self.holder('r_bat'), brow=-.75, look=(.7, .25))
        p = self.contact(1); B = self.bounce_pt(1); head = np.array(actor('rio_bat').to_plate(*self.player(0)[1:4], 128, 40))
        for i in range(max(0, n - 1), n + 1):                               # every ball in the air
            f0 = t0 + per * i; a = t - f0
            if a < 0: continue
            if a < .09:                                                     # machine -> table -> bat
                s_ = a / .09; pos = noz + (p - noz) * s_; pos[1] -= 30 * math.sin(math.pi * s_)
            elif a < .35:                                                   # bat -> the cut-out's head
                s_ = (a - .09) / .26; pos = p + (head - p) * s_; pos[1] -= 70 * math.sin(math.pi * s_)
            elif a < .7:                                                    # and it drops off
                s_ = a - .35; pos = head + np.array([-90 * s_, 400 * s_ * s_ - 60 * s_])
            else: continue
            fx.tt_ball(d, c, pos[0], pos[1], 11)
        fx.tint(d, (.35, .45, .85), .7); d *= .82                          # night, over everything
        q = fx.cpt(c, 760, 230); fx.ellipse(d, q, (60, 60), 0, (1, 1, .85), None, 0)
        if n >= 1:
            qh = fx.cpt(c, *head); fx.text_out(d, 'TOK', qh[0] + 40, qh[1] - 60, self.ow * .045, fill=(1, 1, 1),
                                               alpha=max(0., 1 - (t - ret[-1]) / .2) if t >= ret[-1] else 0.)
        fx.text_out(d, 'TWO WEEKS LATER...', self.ow / 2, self.oh * .12, self.ow * .075, fill=(1, .85, .1), scale=ease(t, t0, t0 + .15))
        fx.text_out(d, f'x{1000 + n * 37}', self.ow * .8, self.oh * .2, self.ow * .05, fill=(1, 1, 1))
        return d

    def revenge(self, t, u, t0, t1):
        c = self.tt_cam(t, .03 * u); d = self.plate('carrington', c)
        # "and he beat Cris... he beat RIO": Ronaldo's smash hits Rio on his name, then he celebrates
        smash = W('rio', 3) - .38; bonk = smash + .3; celebrate = bonk + .45
        key, x, y, h, mir = self.player(0)
        face = actor('rio_bat').to_plate(x, y, h, 128, 40)
        hits = [(73.95, 1), (74.33, 0), (smash, 1)]
        dazed = ease(t, bonk, bonk + .1)
        self.tt_match(t, c, d, hits, (bonk, tuple(face), 0),
                      rio_kw=dict(lean=-9 * bump(t, bonk + .08, .12) - 4 * dazed, blink=.6 * dazed, brow=-.4 * dazed, look=(.6, -.4) if t > bonk else None),
                      ron_kw=dict(hop=self.hop(t, celebrate, .45, 110), brow=-.6, smile=.6 * (t > bonk)),
                      ron_ang=-90 * ease(t, celebrate - .05, celebrate + .1) if t > celebrate - .05 else None)
        if t > bonk:                                                        # the ball pops off his forehead
            a = t - bonk
            if a < .6: fx.tt_ball(d, c, face[0] + 120 * a, face[1] - 260 * a + 700 * a * a, 11)
            q = fx.cpt(c, *face)
            fx.text_out(d, 'BONK!', q[0] + 90, q[1] - 110 - 30 * min(a, .6), self.ow * .09, fill=(1, .9, .2),
                        scale=ease(t, bonk, bonk + .06), alpha=1 - ease(t, bonk + .9, bonk + 1.1))
            for i in range(5):
                an = t * 6 + i * 1.256; fx.sparkle(d, q[0] + 55 * math.cos(an), q[1] - 30 + 18 * math.sin(an), 20, t, i)
        if t > celebrate:
            fx.confetti(d, t, celebrate, n=60)
            fx.text_out(d, 'CR7 WINS', self.ow / 2, self.oh * .12, self.ow * .11, fill=(1, .85, .1), scale=ease(t, celebrate, celebrate + .15))
        return d

    def rio_sulks(self, t, u, t0, t1):
        c = self.cam(1.35, 470, 840); d = self.plate('carrington', c, blur=6)
        self.put(d, c, 'rio_hero', 470, 2100, 1.9, t, look=(-.7, .3), brow=-.7, smile=-.3)
        q = fx.cpt(c, 470, 610); fx.puff(d, q[0], q[1], 190, (.5, .53, .6), 1., True, 2)
        for i in range(9):
            ph = (t * 2.4 + i * .37) % 1; x = q[0] - 150 + 38 * i; y = q[1] + 90 + 300 * ph
            cv2.line(d, (int(x * 4), int(y * 4)), (int((x - 6) * 4), int((y + 30) * 4)), (.55, .7, 1.), 4, cv2.LINE_AA, 2)
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
        self.put(d, c, 'r_invite', 300, 1560, 1.2, t, shadow_w=330, limbs={'hand': 16 * max(0, math.sin(t * 8))}, look=(.4, 0),
                 brow=.4 * bump(t, W('lose') + .1, .2))
        fp = self.pt('r_invite', 300, 1560, 1.2, 800, 640)
        per = .45; ph = (t % per) / per
        bw = BALL * 1.2
        self.prop('ball').draw(d, c, fp[0] - 40, 1560 - bw * .6 - 130 * math.sin(math.pi * ph), bw, rot=t * 300)
        fall = 79.5; ang = 84 * ease(t, fall, fall + .42) ** 2
        ex, ey = 720, 1600
        cf = c @ T(ex - 60, ey) @ R(-ang) @ T(-(ex - 60), -ey)
        if ang < 1: shadow(d, c, ex, ey, 420)
        self.put(d, cf, 'e_tired', ex, ey, 1.2, t, mirror=True, look=(-.3, 0), blink=.95 * ease(t, fall - .2, fall))
        fx.dust(d, c, ex - 330, ey - 40, fall + .42, t, 1.8, n=9, seed=11)
        if t > fall + .5: fx.text_out(d, 'K.O.', self.ow * .7, self.oh * .55, self.ow * .1, fill=(1, .3, .2), scale=ease(t, fall + .5, fall + .6))
        return d

"""Fight choreography for The Undercard: a Fighter collects pose, position, lean and lift keys from readable moves
(guard, punch, duck, cover, stumble, spin...) and the effects each move makes (whoosh, impact burst, sweat, camera
shake, crowd reaction), so direction.py writes the fight as a list of moves on the dialogue edit's marks.

Every punch is staged the way a cartoon fight reads: a held anticipation (the arm drawn back, the body shifted back),
a 2-3 frame lunge into the punch drawing, a hold on the extension, then the recovery back to guard; the one hit takes
an impact burst, a camera shake, a knock-back and flying sweat. Guards bounce (actors.life: "bounce")."""

GUARDS = {"guard", "guard2", "guard_high"}


class Fighter:
    def __init__(self, who, home, facing, y, h):
        self.who, self.home, self.facing, self.y, self.h = who, home, facing, y, h
        self.poses, self.xs, self.rots, self.lifts, self.mirrors = [(0.0, "guard")], [(0.0, home)], [(0.0, 0.0)], \
            [(0.0, 0.0)], [(0.0, False)]
        self.fx, self.sfx, self.shakes = [], [], []
        self.x = home

    # ---------------------------------------------------------------- primitives
    def pose(self, t, name):
        self.poses.append((t, name))
        return self

    def to(self, t, x):
        self.xs.append((t, x))
        self.x = x
        return self

    def hold(self, t):
        self.xs.append((t, self.x))
        return self

    def lean(self, t, deg):
        self.rots.append((t, deg))
        return self

    def lift(self, t, px):
        self.lifts.append((t, px))
        return self

    def flip(self, t, on):
        self.mirrors.append((t, on))
        return self

    # ---------------------------------------------------------------- moves
    def guard(self, t, x=None, pose="guard"):
        self.pose(t, pose)
        if x is not None:
            self.hold(t)
            self.to(t + 0.22, x)
        self.lean(t, 0.0)
        return self

    def punch(self, t, pose, reach, wind="guard_high", wind_t=0.2, hold=0.16, back=0.3, lean=6.0, swing=0.07,
              sound="whoosh", home=None, height=0.56, lines=True):
        """anticipation from t - wind_t, the punch drawing at t (lunging `reach` px towards the opponent over
        `swing` s), held, then back to guard and home"""
        f = self.facing
        x0 = self.x
        self.pose(t - wind_t, wind).hold(t - wind_t).to(t - 0.03, x0 - 14 * f).lean(t - wind_t, -3.0 * f)
        self.pose(t, pose).to(t + swing, x0 + reach * f).lean(t + swing, lean * f)
        self.hold(t + swing + hold).lean(t + swing + hold, lean * f)
        self.pose(t + swing + hold + 0.05, "guard").to(t + swing + hold + back, x0 if home is None else home)
        self.lean(t + swing + hold + back, 0.0)
        if sound:
            self.sfx.append((t - 0.01, sound, abs(reach)))
        if lines:                                               # speed lines off the glove as it goes out
            gx = x0 + reach * f + 0.56 * self.h * f
            self.fx.append(dict(fn="speed", t0=t + swing * 0.3, dur=max(0.13, swing + 0.06), at=(gx, self.y - height * self.h),
                                dir=f, len=0.42 * self.h, spread=0.16 * self.h, n=5, z=5999))
        return self

    def duck(self, t, dur=0.32, dx=0.0, pose="crouch_guard"):
        self.pose(t, pose).hold(t).to(t + 0.08, self.x + dx).lean(t, -4.0 * self.facing)
        self.hold(t + dur)
        self.pose(t + dur, "guard").to(t + dur + 0.12, self.x - dx).lean(t + dur + 0.12, 0.0)
        return self

    def windmill(self, t, dur=1.1):
        """leaning back far too far, arms going round: lean_back and guard_high swapped every 4 frames while the
        whole body rocks between 14 and 30 degrees"""
        f = self.facing
        self.pose(t, "lean_back").hold(t).to(t + 0.12, self.x - 40 * f)
        k, tt = 0, t + 0.13
        while tt < t + dur:
            self.pose(tt, "guard_high" if k % 2 else "lean_back")
            self.lean(tt, -(14.0 if k % 2 else 30.0) * f)
            tt += 0.13
            k += 1
        self.pose(t + dur, "guard").lean(t + dur + 0.15, 0.0).hold(t + dur).to(t + dur + 0.3, self.x + 40 * f)
        return self

    def hit(self, t, pose="cover", knock=70.0, lean=12.0, settle=0.6, at=None, size=110.0, sweat=True):
        """taking a punch at t: the cover drawing, knocked back, tipped away, then wobbling back upright"""
        f = self.facing
        self.pose(t - 0.02, pose).hold(t).to(t + 0.14, self.x - knock * f)
        self.lean(t, 0.0).lean(t + 0.1, -lean * f).lean(t + 0.3, -lean * 0.4 * f).lean(t + 0.45, -lean * 0.7 * f)
        self.lean(t + settle, 0.0)
        if at is not None:
            self.fx.append(dict(fn="impact", t0=t, at=at, size=size, z=6000))
            if sweat:
                self.fx.append(dict(fn="sweat", t0=t, at=(at[0] - 0.2 * size * f, at[1] - 0.3 * size), n=7,
                                    dir=-f, size=size, z=6001))
        self.shakes.append((t, 9.0, 0.35))
        return self

    def stumble(self, t, dur, dx, wob=7.0):
        f = self.facing
        self.hold(t).to(t + dur, self.x + dx)
        n = 4
        for i in range(n):
            self.lean(t + dur * (i + 0.5) / n, wob * (1 if i % 2 else -1) * (1 - i / n))
        self.lean(t + dur, 0.0)
        return self

    def spin(self, t, dur=0.5, dx=0.0):
        """turned round by his own momentum: flipped to face away, a beat, flipped back"""
        f = self.facing
        self.lean(t, 14.0 * f).flip(t + 0.08, True).lean(t + 0.12, -6.0 * f)
        self.hold(t).to(t + 0.25, self.x + dx)
        self.flip(t + dur, False).lean(t + dur + 0.08, 0.0)
        return self

    # ---------------------------------------------------------------- the actor
    def item(self, P, extra_poses=(), extra_xs=(), **kw):
        def clean(keys):
            keys = sorted(keys, key=lambda kv: kv[0])
            out = []
            for k in keys:
                if out and abs(out[-1][0] - k[0]) < 1e-6:
                    out[-1] = k
                else:
                    out.append(k)
            return out
        poses = clean(self.poses + list(extra_poses))
        xs = clean(self.xs + list(extra_xs))
        return P(self.who, poses, [(t, (x, self.y)) for t, x in xs], rot=clean(self.rots), dy=clean(self.lifts),
                 mirror=clean(self.mirrors), ease=True,
                 bounce=dict(amp=0.012, hz=2.3, poses=GUARDS), **kw)

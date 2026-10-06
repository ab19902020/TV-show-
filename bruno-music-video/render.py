"""Procedural music video for "Bruno Bruno Bruno".

Everything is generated from the audio: tempo, beat grid, onsets and the
low/mid/high band energies drive a night-stadium scene with an original
dancing footballer, a bouncing crowd, floodlights, an LED board spectrum,
fireworks and confetti.  No source art is used.

    python3 render.py                 # full 1920x1080 30fps render
    python3 render.py --preview 20    # stills every 20 s into stills/
"""
import argparse
import math
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIO = os.path.join(HERE, "src", "bruno.mp3")
OUT = os.path.join(HERE, "bruno_bruno_bruno.mp4")
W, H, FPS = 1920, 1080, 30
FONT = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
GROUND = 955             # y of the dancer's feet
HORIZON = 640            # top of the pitch

# --------------------------------------------------------------------------
# Audio analysis
# --------------------------------------------------------------------------
SR, HOP, NFFT = 22050, 512, 2048


def analyse():
    raw = subprocess.run(["ffmpeg", "-v", "quiet", "-i", AUDIO, "-ac", "1",
                          "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32)
    frames = np.lib.stride_tricks.sliding_window_view(x, NFFT)[::HOP]
    S = np.abs(np.fft.rfft(frames * np.hanning(NFFT)))
    f = np.fft.rfftfreq(NFFT, 1 / SR)
    afps = SR / HOP
    dur = len(x) / SR

    def band(lo, hi):
        e = np.log1p(S[:, (f >= lo) & (f < hi)].mean(1) * 4)
        return e / np.percentile(e, 99)

    bass, mid, high = band(30, 150), band(300, 3000), band(3000, 10000)

    flux = np.maximum(np.diff(np.log1p(S), axis=0), 0).sum(1)
    flux = np.concatenate([[0], flux])
    flux = np.maximum(flux - np.convolve(flux, np.ones(24) / 24, "same"), 0)
    flux /= np.percentile(flux, 99.5)

    # tempo by autocorrelation, phase by grid alignment
    ac = np.correlate(flux, flux, "full")[len(flux) - 1:]
    lags = np.arange(1, len(ac))
    bpm = 60 * afps / lags
    ok = (bpm > 70) & (bpm < 180)
    period = lags[ok][np.argmax(ac[1:][ok])] / afps
    phases = np.linspace(0, period, 64, endpoint=False)
    t_af = np.arange(len(flux)) / afps
    score = [np.interp(np.arange(p, dur, period), t_af, flux).sum() for p in phases]
    t0 = phases[int(np.argmax(score))]

    # onsets: local maxima of flux above a threshold
    on = []
    for i in range(2, len(flux) - 2):
        if flux[i] > 0.35 and flux[i] == flux[i - 3:i + 4].max():
            on.append((i / afps, float(min(flux[i], 1.5))))

    # resample to video frames
    n = int(dur * FPS)
    tv = np.arange(n) / FPS

    def env(sig, attack=0.6, release=0.12):
        v = np.interp(tv, t_af, sig)
        out = np.zeros_like(v)
        acc = 0.0
        for i, s in enumerate(v):
            acc += (s - acc) * (attack if s > acc else release)
            out[i] = acc
        return np.clip(out, 0, 1.2)

    rms = np.sqrt((frames ** 2).mean(1))
    heat = np.convolve(np.interp(tv, t_af, bass), np.ones(FPS * 3) / (FPS * 3), "same")
    heat = np.clip((heat - np.percentile(heat, 15)) / (np.percentile(heat, 90) - np.percentile(heat, 15)), 0, 1)
    loud = np.interp(tv, t_af, rms)
    return dict(n=n, dur=dur, period=period, t0=t0, onsets=on,
                bass=env(bass), mid=env(mid), high=env(high, 0.7, 0.2),
                heat=heat, loud=loud / loud.max())


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t


def lerpc(a, b, t):
    return tuple(int(lerp(x, y, t)) for x, y in zip(a, b))


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


COOL = dict(sky_top=(8, 10, 38), sky_bot=(40, 26, 80), stand=(18, 16, 34),
            pitch_a=(22, 90, 48), pitch_b=(28, 104, 56), beam=(170, 200, 255))
HOT = dict(sky_top=(30, 0, 12), sky_bot=(150, 20, 40), stand=(34, 10, 16),
           pitch_a=(26, 96, 46), pitch_b=(34, 112, 54), beam=(255, 190, 160))
TEAM_RED, TEAM_DARK = (218, 32, 38), (120, 10, 18)


def build_background(pal):
    img = Image.new("RGB", (W, H))
    px = np.zeros((H, W, 3), np.float32)
    g = np.linspace(0, 1, HORIZON)[:, None]
    px[:HORIZON] = (np.array(pal["sky_top"]) * (1 - g) + np.array(pal["sky_bot"]) * g)[:, None, :]
    # pitch: perspective stripes
    ys = np.arange(HORIZON, H)
    depth = 1 / ((ys - HORIZON + 40) / 40.0)
    stripe = (np.floor(np.log(depth + 1e-6) * 3.2) % 2)[:, None]
    pa, pb = np.array(pal["pitch_a"]), np.array(pal["pitch_b"])
    shade = (0.55 + 0.45 * (ys - HORIZON) / (H - HORIZON))[:, None, None]
    px[HORIZON:] = (pa * (1 - stripe[..., None]) + pb * stripe[..., None]) * shade
    img = Image.fromarray(px.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)
    # stand bowl
    d.polygon([(0, 260), (W * .25, 300), (W * .5, 312), (W * .75, 300), (W, 260),
               (W, HORIZON), (0, HORIZON)], fill=pal["stand"])
    d.line([(0, 260), (W * .25, 300), (W * .5, 312), (W * .75, 300), (W, 260)],
           fill=lerpc(pal["stand"], (255, 255, 255), .25), width=6)
    # roof struts
    for i in range(13):
        x = i * W / 12
        d.line([(x, 0), (x + (W / 2 - x) * .05, 270)], fill=lerpc(pal["stand"], (0, 0, 0), .4), width=4)
    # pitch markings
    line = (210, 235, 210)
    d.line([(0, HORIZON + 2), (W, HORIZON + 2)], fill=line, width=3)
    d.ellipse([W / 2 - 520, 760, W / 2 + 520, 1060], outline=line, width=5)
    d.line([(W / 2, HORIZON), (W / 2, H)], fill=line, width=5)
    return img


rng = np.random.default_rng(8)
# crowd: rows on the bowl
CROWD = []
for row in range(26):
    y = 330 + row * 11.5
    count = int(150 + row * 4)
    for k in range(count):
        x = (k + rng.random() * .8) / count * (W + 40) - 20
        top = 260 + 52 * math.sin(math.pi * min(max(x / W, 0), 1)) ** .7
        if y < top + 18:
            continue
        r = rng.random()
        col = TEAM_RED if r < .55 else ((240, 240, 240) if r < .7 else (20, 20, 22) if r < .9 else (250, 200, 40))
        CROWD.append((x, y, 3.2 + row * .14, col, rng.random() * 6.28, rng.random()))
CROWD_A = np.array([(c[0], c[1], c[2], c[4], c[5]) for c in CROWD])
CROWD_COL = [c[3] for c in CROWD]
STARS = rng.random((160, 3)) * [W, 250, 1]
CONFETTI = rng.random((900, 6))
FW_COLS = [(255, 70, 70), (255, 220, 90), (255, 255, 255), (255, 120, 40), (120, 200, 255)]

FONTS = {}


def font(sz):
    if sz not in FONTS:
        FONTS[sz] = ImageFont.truetype(FONT, sz)
    return FONTS[sz]


# --------------------------------------------------------------------------
# The dancer (original character)
# --------------------------------------------------------------------------
MOVES = ["bounce", "wave", "point", "hop", "ears", "pump"]


def pose(move, ph, beat, e):
    """Return angles/offsets for a move. ph = beat phase 0..1."""
    kick = math.exp(-ph * 5)
    side = 1 if beat % 2 == 0 else -1
    sw = math.sin((beat + ph) * math.pi)          # half-speed sway
    p = dict(drop=0.0, lean=0.0, hop=0.0, sx=0.0, lsh=-.35, lel=-.25, rsh=.35, rel=.25,
             lfoot=-70, rfoot=70, lift_l=0.0, lift_r=0.0, head=0.0)
    if move == "bounce":
        p.update(drop=26 * kick * e, lean=.06 * sw, lsh=-.6 - .5 * kick, lel=-1.3,
                 rsh=.6 + .5 * kick, rel=1.3, head=.12 * sw)
    elif move == "wave":
        p.update(drop=12 * kick, lean=.14 * sw, sx=30 * sw, lsh=-2.6 + .35 * sw, lel=-.3 * sw,
                 rsh=2.6 + .35 * sw, rel=-.3 * sw, head=.2 * sw)
    elif move == "point":
        up = 1 if beat % 4 < 2 else -1
        p.update(drop=18 * kick, lean=-.08 * up, lsh=-2.9 if up > 0 else -.9, lel=0 if up > 0 else -2.2,
                 rsh=2.9 if up < 0 else .9, rel=0 if up < 0 else 2.2, head=-.15 * up)
    elif move == "hop":
        h = math.sin(ph * math.pi)
        p.update(hop=70 * h * e, sx=60 * side * (ph - .5), lean=.1 * side,
                 lift_l=50 * h if side > 0 else 0, lift_r=50 * h if side < 0 else 0,
                 lsh=-1.2 - .6 * h, lel=-1.0, rsh=1.2 + .6 * h, rel=1.0)
    elif move == "ears":
        p.update(drop=10 * kick, lean=.1 * sw, lsh=-2.0, lel=-2.4, rsh=2.0, rel=2.4,
                 head=.25 * sw)
    elif move == "pump":
        up = kick
        p.update(drop=20 * kick, lsh=-.7, lel=-1.6, rsh=2.3 + .5 * up, rel=.3 - .6 * up,
                 lean=-.05, lfoot=-90, rfoot=90)
    return p


def blend_pose(a, b, t):
    return {k: lerp(a[k], b[k], t) for k in a}


def ik(hip, foot, l1, l2, bend):
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = min(math.hypot(dx, dy), l1 + l2 - 1)
    a = math.atan2(dy, dx)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    k = a + bend * math.acos(max(-1, min(1, c)))
    return (hip[0] + l1 * math.cos(k), hip[1] + l1 * math.sin(k))


def limb(d, pts, col, w):
    d.line(pts, fill=(12, 8, 14), width=w + 10, joint="curve")
    for p in pts:
        d.ellipse([p[0] - (w + 10) / 2, p[1] - (w + 10) / 2, p[0] + (w + 10) / 2, p[1] + (w + 10) / 2], fill=(12, 8, 14))
    d.line(pts, fill=col, width=w, joint="curve")
    for p in pts:
        d.ellipse([p[0] - w / 2, p[1] - w / 2, p[0] + w / 2, p[1] + w / 2], fill=col)


def draw_dancer(img, cx, p, blink, s=1.0, shadow=True):
    d = ImageDraw.Draw(img)
    SK, HAIR, SHORT, SOCK, BOOT = (196, 140, 100), (30, 20, 16), (245, 245, 245), (20, 20, 24), (250, 210, 40)
    hipy = GROUND - 250 * s + p["drop"] - p["hop"]
    hip = (cx + p["sx"], hipy)
    if shadow:
        sw = 130 * s * (1 - p["hop"] / 200)
        d.ellipse([cx + p["sx"] - sw, GROUND - 14, cx + p["sx"] + sw, GROUND + 14], fill=(10, 40, 20))
    lean = p["lean"]
    torso = 175 * s
    chest = (hip[0] + math.sin(lean) * torso, hip[1] - math.cos(lean) * torso)
    # legs
    for sgn, foot_dx, lift, colr in ((-1, p["lfoot"], p["lift_l"], 0), (1, p["rfoot"], p["lift_r"], 0)):
        hp = (hip[0] + sgn * 34 * s, hip[1])
        ft = (cx + p["sx"] * .6 + foot_dx * s, GROUND - 10 - lift - p["hop"] * .9)
        kn = ik(hp, ft, 125 * s, 125 * s, -sgn)
        limb(d, [hp, kn], SK, int(40 * s))
        limb(d, [kn, ft], SOCK, int(36 * s))
        d.ellipse([ft[0] - 30 * s + sgn * 14 * s, ft[1] - 14 * s, ft[0] + 30 * s + sgn * 14 * s, ft[1] + 14 * s],
                  fill=BOOT, outline=(12, 8, 14), width=5)
        # shorts leg
        d.polygon([(hp[0] - 34 * s, hp[1] - 10), (hp[0] + 34 * s, hp[1] - 10),
                   (lerp(hp[0], kn[0], .45) + 30 * s, lerp(hp[1], kn[1], .45)),
                   (lerp(hp[0], kn[0], .45) - 30 * s, lerp(hp[1], kn[1], .45))],
                  fill=SHORT, outline=(12, 8, 14), width=5)
    # torso (shirt)
    ca, sa = math.cos(lean), math.sin(lean)

    def rot(x, y):  # local torso coords -> image, y up from hip
        return (hip[0] + x * ca + y * sa, hip[1] + x * sa - y * ca)
    shirt = [rot(-62 * s, -6), rot(62 * s, -6), rot(76 * s, torso), rot(-76 * s, torso)]
    d.polygon(shirt, fill=TEAM_RED, outline=(12, 8, 14), width=7)
    d.polygon([rot(-62 * s, -6), rot(62 * s, -6), rot(64 * s, 22 * s), rot(-64 * s, 22 * s)], fill=TEAM_DARK)
    d.text(rot(0, torso * .55), "8", font=font(int(70 * s)), fill=(255, 255, 255), anchor="mm",
           stroke_width=3, stroke_fill=(12, 8, 14))
    # arms (FK, angle 0 = straight down, positive = outwards right)
    for sgn, sh_a, el_a in ((-1, p["lsh"], p["lel"]), (1, p["rsh"], p["rel"])):
        sh = rot(sgn * 74 * s, torso - 14 * s)
        a1 = lean + sh_a
        el = (sh[0] + 105 * s * math.sin(a1), sh[1] + 105 * s * math.cos(a1))
        a2 = a1 + el_a
        hd = (el[0] + 95 * s * math.sin(a2), el[1] + 95 * s * math.cos(a2))
        limb(d, [sh, el], TEAM_RED, int(40 * s))
        limb(d, [el, hd], SK, int(32 * s))
        d.ellipse([hd[0] - 22 * s, hd[1] - 22 * s, hd[0] + 22 * s, hd[1] + 22 * s], fill=SK, outline=(12, 8, 14), width=5)
    # neck + head
    nk = rot(0, torso)
    limb(d, [nk, rot(0, torso + 26 * s)], SK, int(36 * s))
    ha = lean + p["head"]
    hc = (nk[0] + math.sin(ha) * 78 * s, nk[1] - math.cos(ha) * 78 * s)
    r = 62 * s
    d.ellipse([hc[0] - r, hc[1] - r * 1.08, hc[0] + r, hc[1] + r * 1.08], fill=SK, outline=(12, 8, 14), width=7)
    # hair: short dark crop with a little quiff
    d.chord([hc[0] - r - 2, hc[1] - r * 1.12, hc[0] + r + 2, hc[1] + r * .2], 180, 360, fill=HAIR)
    d.ellipse([hc[0] - r * .3, hc[1] - r * 1.35, hc[0] + r * .7, hc[1] - r * .7], fill=HAIR)
    d.ellipse([hc[0] - r * 1.04, hc[1] - r * .25, hc[0] - r * .76, hc[1] + r * .2], fill=SK, outline=(12, 8, 14), width=4)
    d.ellipse([hc[0] + r * .76, hc[1] - r * .25, hc[0] + r * 1.04, hc[1] + r * .2], fill=SK, outline=(12, 8, 14), width=4)
    # face
    ex = r * .36
    for sgn in (-1, 1):
        e = (hc[0] + sgn * ex, hc[1] - r * .02)
        if blink:
            d.line([e[0] - 10 * s, e[1], e[0] + 10 * s, e[1]], fill=(12, 8, 14), width=5)
        else:
            d.ellipse([e[0] - 9 * s, e[1] - 12 * s, e[0] + 9 * s, e[1] + 12 * s], fill=(12, 8, 14))
        d.line([e[0] - 16 * s, e[1] - 26 * s, e[0] + 14 * s, e[1] - 30 * s - sgn * 3], fill=HAIR, width=7)
    d.chord([hc[0] - r * .45, hc[1] + r * .2, hc[0] + r * .45, hc[1] + r * .75], 0, 180, fill=(120, 30, 30),
            outline=(12, 8, 14), width=4)
    d.chord([hc[0] - r * .38, hc[1] + r * .22, hc[0] + r * .38, hc[1] + r * .45], 0, 180, fill=(255, 255, 255))


# --------------------------------------------------------------------------
# Frame renderer
# --------------------------------------------------------------------------
A = None
BG_COOL = BG_HOT = None


def init_worker(a):
    global A, BG_COOL, BG_HOT
    A = a
    BG_COOL, BG_HOT = build_background(COOL), build_background(HOT)


def move_for(bar, heat):
    calm = ["wave", "ears", "bounce", "wave"]
    hot = ["bounce", "hop", "point", "pump", "hop", "wave"]
    seq = hot if heat > .5 else calm
    return seq[(bar * 7 + 3) % len(seq)]


def frame(i):
    t = i / FPS
    a = A
    bass, mid, high, heat = a["bass"][i], a["mid"][i], a["high"][i], a["heat"][i]
    P = a["period"]
    bt = (t - a["t0"]) / P
    beat = int(math.floor(bt))
    ph = bt - beat
    kick = math.exp(-ph * 6) * min(1, bass * 1.2)
    bar = beat // 8 if beat >= 0 else -1

    img = Image.blend(BG_COOL, BG_HOT, heat * .85)
    d = ImageDraw.Draw(img)
    pal = {k: lerpc(COOL[k], HOT[k], heat) for k in COOL}

    # stars
    for sx, sy, sb in STARS:
        tw = .5 + .5 * math.sin(t * 2 + sb * 40)
        v = int(120 + 135 * tw * (1 - heat * .6))
        d.point((sx, sy), fill=(v, v, v))

    # glow layer (half-res, additive)
    glow = Image.new("RGB", (W // 2, H // 2))
    g = ImageDraw.Draw(glow)
    # floodlights + beams
    for k, fx in enumerate((150, 640, 1280, 1770)):
        fy = 70
        swing = math.sin(t * .7 + k * 1.7) * 160 + (bass - .5) * 120
        inten = .35 + .65 * kick + .2 * heat
        col = lerpc((0, 0, 0), pal["beam"], min(1, inten * .55))
        tx = fx + swing + (W / 2 - fx) * .4
        g.polygon([(fx / 2 - 20, fy / 2), (fx / 2 + 20, fy / 2), ((tx + 220) / 2, GROUND / 2), ((tx - 220) / 2, GROUND / 2)], fill=col)
        lc = lerpc((60, 60, 60), (255, 255, 255), min(1, inten))
        g.rectangle([(fx - 70) / 2, (fy - 34) / 2, (fx + 70) / 2, (fy + 34) / 2], fill=lc)
        d.rectangle([fx - 74, fy - 38, fx + 74, fy + 38], fill=(30, 30, 40))
        for yy in range(3):
            for xx in range(6):
                d.rectangle([fx - 66 + xx * 23, fy - 30 + yy * 21, fx - 48 + xx * 23, fy - 14 + yy * 21], fill=lc)
        d.line([(fx, fy + 38), (fx, 270)], fill=(30, 30, 40), width=10)
    # coloured stage sweeps when hot
    if heat > .4:
        for k in range(6):
            ang = math.sin(t * 1.3 + k) * .6 + (k - 2.5) * .25
            ox = W / 2 + (k - 2.5) * 260
            c = FW_COLS[k % len(FW_COLS)]
            amt = (heat - .4) / .6 * (.25 + .5 * kick)
            col = lerpc((0, 0, 0), c, amt * .6)
            L = 1100
            g.polygon([(ox / 2, HORIZON / 2), ((ox + math.sin(ang - .05) * L) / 2, (HORIZON - math.cos(ang - .05) * L) / 2),
                       ((ox + math.sin(ang + .05) * L) / 2, (HORIZON - math.cos(ang + .05) * L) / 2)], fill=col)

    # crowd
    amp = 4 + 14 * bass * (.4 + heat)
    xs, ys, rs, phs, rnd = CROWD_A.T
    bob = np.abs(np.sin(bt * math.pi + phs * .3)) * amp
    arms = heat > .45
    for j in range(len(xs)):
        x, y, r = xs[j], ys[j] - bob[j], rs[j]
        c = CROWD_COL[j]
        d.rectangle([x - r, y + r * .6, x + r, y + r * 2.6], fill=lerpc(c, (0, 0, 0), .35))
        d.ellipse([x - r * .8, y - r * .8, x + r * .8, y + r * .8], fill=(150, 110, 90) if rnd[j] > .3 else (90, 60, 45))
        if arms and rnd[j] > .55:
            sway = math.sin(t * 3 + phs[j]) * r
            d.line([(x + r * .6, y + r), (x + r + sway, y - r * 2.6)], fill=c, width=2)
        elif not arms and rnd[j] > .93:  # phone lights in quiet parts
            fl = .5 + .5 * math.sin(t * 2 + phs[j] * 3)
            g.ellipse([x / 2 - 2, (y - r * 3) / 2 - 2, x / 2 + 2, (y - r * 3) / 2 + 2],
                      fill=lerpc((0, 0, 0), (255, 250, 210), fl * (.5 + high * .5)))

    # LED board: spectrum or scrolling name
    by0, by1 = HORIZON - 34, HORIZON - 4
    d.rectangle([0, by0 - 4, W, by1 + 4], fill=(8, 8, 12))
    if bar % 2 == 0:
        n = 64
        for k in range(n):
            v = (bass if k < 12 else mid if k < 44 else high)
            v *= .55 + .45 * math.sin(t * 7 + k * .9) ** 2
            v = min(1, v)
            cw = W / n
            col = lerpc((40, 0, 0), (255, 60 + int(150 * v), 40), v)
            hh = (by1 - by0) * v
            d.rectangle([k * cw + 2, by1 - hh, (k + 1) * cw - 2, by1], fill=col)
            g.rectangle([(k * cw) / 2, (by1 - hh) / 2, ((k + 1) * cw) / 2, by1 / 2], fill=lerpc((0, 0, 0), col, .35))
    else:
        txt = "BRUNO  BRUNO  BRUNO  " * 6
        off = -(t * 260) % 900
        d.text((off - 900, by0 - 3), txt, font=font(30), fill=(255, 220, 60))

    # fireworks on strong onsets during hot sections
    for (ot, os_) in a["fw"]:
        age = t - ot
        if 0 <= age < 1.6:
            seed = int(ot * 1000)
            rr = np.random.default_rng(seed)
            cx, cy = 200 + rr.random() * (W - 400), 80 + rr.random() * 200
            col = FW_COLS[seed % len(FW_COLS)]
            fade = (1 - age / 1.6) ** 1.5
            nn = 40
            R = 260 * (1 - math.exp(-age * 3)) * (.6 + os_ * .4)
            for k in range(nn):
                an = k / nn * 6.283 + rr.random() * .1
                px = cx + math.cos(an) * R
                py = cy + math.sin(an) * R + 60 * age * age
                cc = lerpc((0, 0, 0), col, fade)
                g.ellipse([px / 2 - 3, py / 2 - 3, px / 2 + 3, py / 2 + 3], fill=cc)
                d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=lerpc(pal["sky_bot"], (255, 255, 255), fade))

    # dancer
    move = move_for(bar, heat)
    nxt = move_for(bar + 1, a["heat"][min(i + int(P * 8 * FPS), a["n"] - 1)])
    p = pose(move, ph, beat, .5 + .5 * min(1, bass))
    beat_in_bar = (beat % 8) + ph
    if beat_in_bar > 7.5 and nxt != move:
        p = blend_pose(p, pose(nxt, ph, beat, .5 + .5 * min(1, bass)), smooth((beat_in_bar - 7.5) * 2))
    if beat_in_bar < .5 and bar > 0:
        prev = move_for(bar - 1, heat)
        if prev != move:
            p = blend_pose(pose(prev, ph, beat, .5), p, smooth(.5 + beat_in_bar))
    if t < 2.5:  # stand still for the title
        p = blend_pose(pose("ears", 0, 0, 0), p, smooth((t - 1.5)))
    blink = (i % 97) < 3
    # rim glow behind dancer
    g.ellipse([(W / 2 - 260) / 2, (GROUND - 640) / 2, (W / 2 + 260) / 2, (GROUND + 40) / 2],
              fill=lerpc((0, 0, 0), (255, 80, 60) if heat > .5 else (90, 110, 255), .25 + .35 * kick))
    draw_dancer(img, W / 2, p, blink)

    # confetti (hot sections)
    if heat > .3:
        cf = CONFETTI
        for k in range(0, len(cf), 4 if heat < .7 else 2):
            sp = 120 + cf[k, 2] * 200
            y = ((t * sp + cf[k, 1] * H * 1.5) % (H * 1.3)) - 100
            x = cf[k, 0] * W + math.sin(t * 2 + cf[k, 3] * 6) * 40
            c = FW_COLS[int(cf[k, 4] * 5)] if cf[k, 4] < .8 else TEAM_RED
            w = 5 + 4 * abs(math.sin(t * 6 + cf[k, 5] * 6))
            d.rectangle([x - w, y - 4, x + w, y + 4], fill=c)

    # additive glow composite
    glow = glow.filter(ImageFilter.GaussianBlur(10)).resize((W, H), Image.BILINEAR)
    arr = np.asarray(img, np.int16) + np.asarray(glow, np.int16)
    img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(img)

    # text
    if heat > .55 and beat % 4 == 0 and ph < .5:
        sz = int(220 + 60 * kick)
        al = 1 - ph * 2
        txt = Image.new("L", (W, H))
        ImageDraw.Draw(txt).text((W / 2, 260), "BRUNO!", font=font(sz), fill=int(255 * al), anchor="mm")
        img.paste((255, 230, 80), mask=txt)
    if t >= 2.5 and (heat > .45 or a["dur"] - t < 9):
        cap_a = smooth((heat - .45) * 6) if a["dur"] - t >= 9 else 1
        cap = "I'LL BE ALRIGHT"
        shown = cap[:max(0, int(((t * 8) % 40)))] if a["dur"] - t >= 9 else cap
        if cap_a > .02:
            layer = Image.new("L", (W, H))
            ImageDraw.Draw(layer).text((W / 2, H - 52), shown, font=font(56), fill=int(255 * cap_a), anchor="mm",
                                       stroke_width=6, stroke_fill=int(255 * cap_a))
            img.paste((12, 8, 14), mask=layer)
            layer2 = Image.new("L", (W, H))
            ImageDraw.Draw(layer2).text((W / 2, H - 52), shown, font=font(56), fill=int(255 * cap_a), anchor="mm")
            img.paste((255, 255, 255), mask=layer2)

    # title card
    if t < 4:
        al = smooth(1 - (t - 2.6) / 1.2) if t > 2.6 else 1
        ov = Image.new("L", (W, H), int(255 * al * (.85 if t > .3 else 1)))
        img.paste((6, 4, 10), mask=ov)
        lay = Image.new("L", (W, H))
        ld = ImageDraw.Draw(lay)
        for k in range(3):
            appear = smooth((t - .2 - k * .45) * 3)
            ld.text((W / 2, 340 + k * 200), "BRUNO", font=font(int(170 + 30 * appear)),
                    fill=int(255 * appear * al), anchor="mm")
        img.paste(TEAM_RED, mask=lay)

    # camera: beat zoom + shake + occasional close-up
    close = 0.0
    if heat > .5 and bar % 4 == 2:
        close = smooth(min(beat_in_bar, 8 - beat_in_bar) * 1.2)
    z = 1 + .025 * kick + .35 * close
    shake = a["shake"][i]
    cx = W / 2 + math.sin(t * 13) * shake * 14
    cy = H / 2 + math.cos(t * 17) * shake * 10 + close * (-60)
    if z > 1.001 or shake > .01:
        img = img.transform((W, H), Image.AFFINE,
                            (1 / z, 0, cx - W / 2 / z, 0, 1 / z, cy - H / 2 / z), Image.BILINEAR)
    # vignette + flash
    if kick > .6 and heat > .6:
        fl = Image.new("L", (W, H), int(40 * (kick - .6) / .4))
        img.paste((255, 255, 255), mask=fl)
    # outro fade
    rem = a["dur"] - t
    if rem < 2:
        img = Image.blend(Image.new("RGB", (W, H)), img, max(0, rem / 2))
    return img.tobytes()


def prepare():
    a = analyse()
    a["fw"] = [(t, s) for t, s in a["onsets"]
               if s > .8 and a["heat"][min(int(t * FPS), a["n"] - 1)] > .55]
    # thin out: at most one burst per 0.5 s
    fw, last = [], -9
    for t, s in a["fw"]:
        if t - last > .5:
            fw.append((t, s))
            last = t
    a["fw"] = fw
    shake = np.zeros(a["n"])
    for t, s in a["onsets"]:
        k = int(t * FPS)
        if s > 1.0 and k < a["n"]:
            shake[k:k + 6] = np.maximum(shake[k:k + 6], np.linspace(s - 1, 0, len(shake[k:k + 6])) * 2)
    a["shake"] = shake
    print(f"tempo {60 / a['period']:.1f} bpm, first beat {a['t0']:.2f}s, {len(a['onsets'])} onsets, "
          f"{len(a['fw'])} fireworks, {a['n']} frames", file=sys.stderr)
    return a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", type=float, help="write stills every N seconds instead")
    args = ap.parse_args()
    a = prepare()
    if args.preview:
        os.makedirs(os.path.join(HERE, "stills"), exist_ok=True)
        init_worker(a)
        for t in np.arange(0, a["dur"], args.preview):
            i = int(t * FPS)
            Image.frombytes("RGB", (W, H), frame(i)).save(os.path.join(HERE, "stills", f"t{int(t):03d}.jpg"), quality=85)
        return
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", AUDIO,
                           "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-maxrate", "3500k", "-bufsize", "7000k", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", OUT],
                          stdin=subprocess.PIPE)
    with Pool(os.cpu_count(), initializer=init_worker, initargs=(a,)) as pool:
        for k, buf in enumerate(pool.imap(frame, range(a["n"]), chunksize=8)):
            ff.stdin.write(buf)
            if k % 300 == 0:
                print(f"frame {k}/{a['n']}", file=sys.stderr)
    ff.stdin.close()
    ff.wait()
    print("wrote", OUT, file=sys.stderr)


if __name__ == "__main__":
    main()

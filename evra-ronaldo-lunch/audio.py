"""The soundtrack for "The Lunch": Evra's recording (kept whole: his voice is never edited, only given a steady overall
gain) with a synthesised score and sound effects laid under and around it.

  - music (score.py): a playful A-minor / C-major comedy score, a different groove for each part of the story, every
    one starting on the picture cut. It sits about 14 dB under his voice and lifts in his pauses (ducking).
  - effects (sfx.py): every gag in the picture has its sound, keyed to the same times direction.py draws it at:
    whip-pan whooshes, keepy-ups, chomps, the glass of water, the tumbleweed, kicks, the BONK, splashes, the goal,
    the table tennis (hit by hit), the delivery box, the ball machine and the cardboard Rio, the rain and the sad
    trombone, the K.O. bell.
  - ambience: birds and air outdoors, a room tone in the kitchen, the jacuzzi's bubbles, steam in the sauna,
    crickets at night.
Everything is synthesised (no samples, no libraries). Loudness: -16 LUFS integrated, -1.5 dBTP, 48 kHz.

python3 audio.py   -> build/audio/*.wav (voice, music, effects, mix) and the picture re-muxed with the new sound:
                      evra_ronaldo_lunch.mp4  (the picture is taken from build/picture.mp4: the render with the
                      original recording, kept from the first run)"""
import os, sys, json, shutil, subprocess
import numpy as np, soundfile as sf
from scipy import ndimage, signal

ROOT = os.path.dirname(os.path.abspath(__file__)); os.chdir(ROOT); sys.path.insert(0, ROOT)
import direction as D
import sfx, score
from sfx import SR, db

OUT = "evra_ronaldo_lunch.mp4"
TOTAL = D.DUR
N = int(round(TOTAL * SR))
SH = {n: t for t, n in D.SHOTS}
W, WE = D.W, lambda p, n=0: D.W(p, n, end=True)
LOG = []

# ------------------------------------------------------------------ levels (dBFS; his voice peaks at about -5)
MUSIC_UNDER = -42.0         # music RMS while he is speaking
MUSIC_FREE = -31.0          # ... in his pauses


def shot_end(name):
    names = [n for t, n in D.SHOTS]; return D.SHOTS[names.index(name) + 1][0]


def voice():
    y, sr = sf.read("src/audio/original.flac", always_2d=True)
    assert sr == SR
    y = y[:N]
    if len(y) < N: y = np.pad(y, ((0, N - len(y)), (0, 0)))
    return y.astype(np.float64)


def duck_curve(v):
    """0 where he speaks, 1 in his pauses (smooth), one value per sample"""
    hop = int(.02 * SR); m = v.mean(1)
    r = np.sqrt(np.convolve(m ** 2, np.ones(hop) / hop, "same"))[::hop]
    act = (20 * np.log10(r + 1e-9) > -46).astype(float)
    act = ndimage.maximum_filter1d(act, int(.3 / .02))                 # hold through short gaps
    free = ndimage.gaussian_filter1d(1 - act, 6)                       # fade the music up / down over ~0.2 s
    return np.interp(np.arange(N) / SR, np.arange(len(free)) * .02, free)


# ------------------------------------------------------------------ the music
SMASH = D.W("rio", 3) - .38          # the rematch: Ronaldo's smash, the BONK on Rio's forehead, then the celebration
BONK = SMASH + .3
CELEBRATE = BONK + .45
SECTIONS = [  # (start: shot name or seconds, style, end: shot name or seconds or None = next section, options)
    ("carrington_open", "intro", None, {}), ("gentle_lunch", "dream", None, {"gain": .9}), ("competitive", "cheeky", None, {}),
    ("arrive", "tiptoe", "hope", {}), ("hope", "dread", "fast_forward", {"gain": 1.0}), ("fast_forward", "run", None, {"gain": .95}),
    ("garden_invite", "funk", "laps", {}), ("laps", "tropical", None, {}), ("sauna", "hot", None, {}),
    ("jacuzzi", "lounge", None, {}), ("goal", "hero", None, {"gain": .95}), ("dior", "glam", None, {}),
    ("warrior", "epic", None, {"gain": .9}), ("happy", "warm", None, {}), ("machine", "tech", None, {"gain": .9}),
    (57.2, "rally", 60.0, {"tail": .02}), (60.65, "tension", "truth", {}), ("truth", "sly", "rio_wins", {}),
    ("rio_wins", "comic", "angry", {"gain": .95}), ("angry", "boil", None, {}), ("delivery", "whimsy", None, {}),
    ("two_weeks", "night", None, {}), (73.95, "rally", SMASH, {"bpm": 156, "tail": .02}), (CELEBRATE, "triumph", "rio_sulks", {}),
    ("thats_cristiano", "funk", None, {"gain": 1.0}), ("any_game", "reprise", 79.93, {}),
]


def t_of(x): return SH[x] if isinstance(x, str) else float(x)


def build_music():
    bus = score.Bus(TOTAL + 1)
    for i, (a, style, b, opt) in enumerate(SECTIONS):
        t0 = t_of(a)
        t1 = t_of(b) if b is not None else (t_of(SECTIONS[i + 1][0]) if i + 1 < len(SECTIONS) else TOTAL)
        opt = dict(opt); gain = opt.pop("gain", 1.0); tail = opt.pop("tail", .22)
        sec, _ = score.section(TOTAL, t0, t1 - t0, style, tail=tail, gain=gain, **opt)
        bus.add_bus(sec, t0)
    sec, _ = score.section(TOTAL, 79.93, .1, "button", tail=.3, gain=1.0)
    bus.add_bus(sec, 79.93)
    L, R = score.with_reverb(bus.L[:N], bus.R[:N], .13)
    return np.stack([L, R], 1)


# ------------------------------------------------------------------ effects and ambience
def fxbus(): return score.Bus(TOTAL + 2)


SFX = fxbus()
BEDS = fxbus()


# how far above (+) or below (-) his voice, in RMS at that moment, each kind of effect may go. Transients such as a kick
# have a high peak but little energy, so this is measured over 100 ms windows. "hero" = the big comedy hits.
ALLOW = {"hit": -3.0, "hero": 2.0, "soft": -10.0, "sustain": -10.0, "roar": -6.0}
KIND = {"whip pan": "soft", "riser": "sustain", "determined": "sustain", "fast-forward": "sustain", "chewing": "soft",
        "tumbleweed": "soft", "cricket": "soft", "rubbing hands": "soft", "swimming past": "soft", "sweat drop": "soft",
        "Evra pants": "soft", "water runs down his face": "soft", "steam from his ears": "sustain", "crowd erupts": "roar",
        "SIUUU crowd": "roar", "cheer": "roar", "crowd": "roar", "BONK": "hero", "BONK (Rio's forehead)": "hero", "SPLOSH": "hero",
        "taiko": "hero", "box lands": "hero", "Rio's winner": "hero", "Rio's smash": "hero", "Ronaldo's smash": "hero",
        "sad trombone": "hero", "K.O. bell": "hero", "thud": "hero", "ball hits his shin": "hero", "Ronaldo pops up": "hero",
        "confetti": "soft", "RIO WINS confetti": "soft", "CR7 WINS confetti": "soft", "a splash somewhere": "soft", "Ronaldo's laps": "soft",
        "fork on the plate": "soft", "plates down": "soft", "ball flies": "soft", "ball flies past": "soft", "ball arrives": "soft",
        "table bounce": "soft", "keepy-up": "soft", "glam sparkles": "soft", "sparkles": "soft", "so close...": "hit"}
CUES = []


def fx(t, snd, lvl, pan=0.0, name=""):
    CUES.append((t, np.asarray(snd, np.float64), lvl, pan, name))


def place_cues(voice_mono):
    """put every effect on the bus: its level as written, then capped so it never swamps his voice at that moment"""
    w = int(.1 * SR); vr = 20 * np.log10(np.sqrt(np.convolve(voice_mono ** 2, np.ones(w) / w, "same")) + 1e-9)
    capped = 0
    for t, snd, lvl, pan, name in CUES:
        x = snd * db(lvl); n = len(x)
        r = 20 * np.log10(np.sqrt(np.convolve(x ** 2, np.ones(w) / w, "valid")).max() + 1e-9) if n >= w else lvl - 6
        i0, i1 = int(max(0, t - .4) * SR), int(min(N, t + n / SR + .4) * SR)
        seg = vr[i0:i1:w // 2]
        loud = float(np.percentile(seg, 85)) if len(seg) else -60.0               # how loud he is around this moment
        local = loud if loud > -38 else -26.4 + 4                                   # a pause in his talking: more room
        kind = KIND.get(name, "hit"); cap = local + ALLOW[kind]
        g = 0.0
        if r > cap: g = cap - r; capped += 1
        SFX.add(snd, t, db(lvl + g), pan)
        LOG.append({"t": round(t, 2), "sound": name, "level": round(lvl + g, 1), "asked": lvl, "pan": pan, "kind": kind})
    print(f"{len(CUES)} effects placed, {capped} brought down to sit under his voice")


def bed(t0, t1, x, rms_db, name, fade=.35):
    n = int((t1 - t0) * SR); x = np.asarray(x[:n], np.float64)
    x = x * db(rms_db) / (np.sqrt(np.mean(x ** 2)) + 1e-9)
    f = int(fade * SR); e = np.ones(len(x)); e[:f] = np.linspace(0, 1, f); e[-f:] = np.linspace(1, 0, f)
    x *= e
    BEDS.add(x, t0, 1.0, -.15); BEDS.add(np.roll(x, int(.011 * SR)), t0, 1.0, .15)         # a little width
    LOG.append({"t": round(t0, 2), "sound": f"[bed] {name} until {t1:.1f}", "level": rms_db, "pan": 0})


def cues():
    S = SH
    # ---- whip pans (the cuts where the story changes place)
    for w in D.WHIPS: fx(w - .15, sfx.whip(), -18, 0, "whip pan")
    # ---- 1. Carrington: Evra done in, Ronaldo on keepy-ups
    k = 1
    while k * .46 < S["gentle_lunch"] - .2:
        fx(k * .46, sfx.ball_tap(), -22, .3, "keepy-up"); k += 1
    for ts in (.3, 1.2, 2.1, 2.9): fx(ts + .4, sfx.plip(), -31, -.4, "sweat drop")
    for ts in (.7, 1.6, 2.5): fx(ts, sfx.huff(), -32, -.4, "Evra pants")
    fx(S["gentle_lunch"], sfx.pop(), -17, 0, "thought bubble pop"); fx(S["gentle_lunch"] + .22, sfx.twinkle(1568, 5), -21, 0, "daydream sparkle")
    fx(S["competitive"] - .35, sfx.riser(.4, 400, 6000), -27, 0, "riser"); fx(S["competitive"], sfx.shing(), -20, 0, "sunburst shing")
    fx(S["competitive"] + .05, sfx.sparkle_hit(), -22, .1, "twinkle in his eye")
    # ---- 2. the invitation
    lunch = W("lunch", 2)
    fx(lunch, sfx.boing(), -14, .3, "Evra pops up"); fx(lunch + .05, sfx.twinkle(1760, 5), -21, .3, "sparkles"); fx(lunch + .15, sfx.hand_rub(.9), -28, .3, "rubbing hands")
    for ts in (14.52, 14.86, 15.2): fx(ts, sfx.footfall(), -23, -.2 + (ts - 14.52) * .5, "skipping up the path")
    # ---- 3. lunch
    fx(S["table"] + .08, sfx.fork_clink(), -25, -.35, "plates down")
    for b in (15.75, 17.05, 18.35):
        fx(b + .17, sfx.chomp(), -18, .35, "Ronaldo's bite"); fx(b + .26, sfx.chew(.9), -29, .35, "chewing")
    fx(W("white") + .1, sfx.fork_clink(), -21, -.1, "fork on the plate"); fx(W("chicken") + .15, sfx.fork_clink(), -21, -.1, "fork on the plate")
    fx(S["hope"] + .3, sfx.twang_lonely(), -23, .1, "lonely twang")
    fx(S["doorway"] - .05, sfx.rustle(.75), -25, .25, "tumbleweed"); fx(S["doorway"], sfx.cricket(1.0) * .6, -31, 0, "cricket")
    fx(W("just", 1) - .1, sfx.glass_slide(), -19, .2, "glass of water slides in"); fx(W("water") + .5, sfx.plip(), -27, -.4, "Evra sweats")
    quick = W("quickly"); gone = W("that", 0) + .05
    fx(S["fast_forward"], sfx.ff_whirr(gone - S["fast_forward"]), -27, 0, "fast-forward")
    for b in [23.9 + .3 * i for i in range(int((quick + .25 - 23.9) / .3) + 1)]: fx(b + .06, sfx.chomp(), -23, .35, "Ronaldo, fast")
    for b in [23.95 + .42 * i for i in range(int((quick + .9 - 23.95) / .42) + 1)]: fx(b + .06, sfx.chomp(), -25, -.35, "Evra, fast")
    fx(gone - .06, sfx.zip_vanish(), -13, .1, "Ronaldo vanishes"); fx(gone, sfx.poof(.6), -17, .1, "dust cloud")
    # ---- 4. the garden
    fx(W("two", 0) - .1, sfx.ball_flick(), -16, -.3, "ball flick"); fx(W("two", 0) + .42, sfx.ball_tap(), -21, -.3, "ball lands")
    fx(30.6, sfx.short_wah(), -22, .3, "Evra's sad wah")
    for tk, who, lv in ((31.15, 0, -11), (31.95, 1, -18), (32.55, 0, -11)):
        fx(tk, sfx.ball_kick(1.0 if who == 0 else .45), lv, -.5 if who == 0 else .45, "kick (Ronaldo)" if who == 0 else "kick (Evra, weak)")
    fx(31.8, sfx.ball_tap(), -23, .35, "ball arrives"); fx(32.55, sfx.ball_tap(), -23, .35, "ball arrives")
    fx(32.95, sfx.thud(95, .3), -13, .4, "ball hits his shin"); fx(32.95, sfx.bonk(), -9, .4, "BONK"); fx(33.1, sfx.boing(.5, 300), -23, .4, "wobble")
    fx(S["swim_invite"], sfx.splash(.6), -26, .1, "a splash somewhere")
    # ---- 5. pool, sauna, jacuzzi
    for i in range(4): fx(S["laps"] + i * .15, sfx.splash(.5, 24 + i), -18, -.7 + .5 * i, "Ronaldo's laps")
    fx(S["laps"] + .05, sfx.swim_swish(.8), -22, -.5, "swimming past"); fx(S["laps"] + .5, sfx.swim_swish(.7), -22, .5, "swimming past")
    fx(S["pool_invite"], sfx.splash(1.3), -11, .2, "Ronaldo pops up")
    t0 = S["sauna"]
    for k in range(1, 7):
        if t0 + .55 * k < S["jacuzzi"] - .05: fx(t0 + .55 * k, sfx.thud(85, .2), -21, .3, "jump squat lands")
    for ts in (37.3, 38.1, 38.9, 39.7): fx(ts + .45, sfx.plip(), -28, -.3, "sweat drop")
    fx(39.62, sfx.twinkle(1760, 4), -24, .3, "thumbs-up sparkle")
    for s_ in (41.85, 43.45, W("right", 0) + .1):
        fx(s_ + .12, sfx.wave_crash(), -8, -.3, "SPLOSH")
        for j in range(3): fx(s_ + .45 + .08 * j, sfx.plip(), -25, -.3, "water runs down his face")
    # ---- 6. what he became
    fx(45.35, sfx.ball_kick(1.2), -9, -.35, "the shot"); fx(45.38, sfx.whoosh(.25, False, 500, 4000), -27, 0, "ball flies")
    arrive = W("goal") + .02
    fx(arrive, sfx.net_swish(), -13, .3, "net"); fx(arrive - .05, sfx.crowd(3.3, .2, 1.3), -15, 0, "crowd erupts"); fx(arrive, sfx.confetti(), -14, 0, "confetti")
    siu = 46.15
    fx(siu - .05, sfx.whoosh(.3, True, 500, 3500), -24, -.3, "jump"); fx(siu + .05, sfx.crowd(2.4, .15, 1.0, seed=9), -12, 0, "SIUUU crowd")
    fx(siu + .56, sfx.thud(80, .3), -14, -.3, "lands"); fx(siu + .56, sfx.poof(.5), -25, -.3, "dust")
    fx(47.45, sfx.twinkle(1760, 6), -23, 0, "glam sparkles")
    for ts, pn in ((W("christian") + .1, -.4), (W("christian") + .32, .4), (W("playboy") - .05, -.3)): fx(ts, sfx.camera_shutter(), -19, pn, "camera flash")
    fx(W("playboy") + .15, sfx.sparkle_hit(), -17, .1, "wink"); fx(W("playboy") + .15, sfx.ding(2093, 1.2), -25, .1, "wink ting")
    hit = W("warrior")
    fx(hit - .75, sfx.riser(.75, 300, 5000), -26, 0, "riser"); fx(hit, sfx.taiko(), -8, 0, "taiko"); fx(hit + .02, sfx.shing(), -15, 0, "shing")
    fx(hit + .2, sfx.sparkle_hit(), -23, .1, "sparkle")
    fx(W("happy") + .1, sfx.twinkle(1318, 4), -25, 0, "happy sparkle")
    t0 = S["machine"]
    for k in range(1, 8):
        if t0 + .42 * k < S["tt_rally"] - .05: fx(t0 + .42 * k, sfx.thud(80, .2), -20, -.35, "rep lands")
    for k in range(0, 3): fx(t0 + .6 + 1.0 * k, sfx.battery_beep(), -27, .4, "low-battery beep")
    mach = W("machine"); fx(mach - .05, sfx.power_up(), -13, -.3, "battery: infinity")
    # ---- 7. table tennis with Rio
    rally = [(57.2, 0), (57.6, 1), (58.0, 0), (58.4, 1), (58.8, 0), (59.2, 1)]
    for h_, w_ in rally:
        fx(h_, sfx.tok(2000 if w_ == 0 else 2450), -13, -.45 if w_ == 0 else .45, "PING" if w_ == 0 else "PONG")
        fx(h_ + .2, sfx.tik(), -20, .2 if w_ == 0 else -.2, "table bounce")
    fx(59.62, sfx.smash_crack(), -9, -.45, "Rio's winner"); fx(59.9, sfx.whoosh(.25, True, 600, 5000), -22, .2, "ball flies past")
    fx(60.02, sfx.swish(), -17, .45, "Ronaldo swings and misses"); fx(60.1, sfx.ding(1175, 1.4), -18, 0, "score")
    fx(60.75, sfx.short_wah(), -19, 0, "so close...")
    fx(S["determined"], sfx.riser(1.1, 300, 4500), -24, 0, "determined")
    fx(63.45, sfx.twinkle(1760, 4), -24, 0, "Rio sparkles")
    fx(65.65, sfx.tok(2450), -13, .45, "PONG"); fx(65.85, sfx.tik(), -20, -.2, "table bounce")
    fx(66.0, sfx.swish(), -19, -.45, "Rio's swing"); fx(66.05, sfx.smash_crack(), -9, -.45, "Rio's smash"); fx(66.43, sfx.whoosh(.25, True, 600, 5000), -22, .2, "ball flies past")
    won = 66.5
    fx(won, sfx.confetti(), -15, 0, "RIO WINS confetti"); fx(won + .05, sfx.crowd(1.6, .15, .8, seed=21), -22, 0, "cheer")
    fx(S["angry"] + .2, sfx.kettle(S["delivery"] - S["angry"] - .25), -19, 0, "steam from his ears")
    land = W("sent") + .2
    fx(land - .35, sfx.falling_whistle(.35), -21, .3, "box falling"); fx(land, sfx.paper_box_land(), -8, .3, "box lands"); fx(land, sfx.poof(.6), -18, .3, "dust")
    fx(land + .3, sfx.boing(.5, 270), -19, -.4, "Ronaldo's delighted"); fx(land + .38, sfx.twinkle(1568, 4), -23, -.4, "sparkle")
    t0 = S["two_weeks"]; per = .32
    for i in range(0, 5):
        ti = t0 + per * i
        if ti + .35 > S["revenge"]: break
        fx(ti, sfx.machine_fire(), -15, -.65, "ball machine"); fx(ti + .09, sfx.tok(2300, 1.3), -13, .45, "Ronaldo returns it")
        fx(ti + .35, sfx.cardboard_hit(), -12, -.7, "hits the cardboard Rio")
    smash, bonk, cel = SMASH, BONK, CELEBRATE
    for h_, w_ in ((73.95, 1), (74.33, 0)):
        fx(h_, sfx.tok(2450 if w_ else 2000), -13, .45 if w_ else -.45, "PONG" if w_ else "PING"); fx(h_ + .18, sfx.tik(), -20, -.2 if w_ else .2, "table bounce")
    fx(smash, sfx.smash_crack(), -9, .45, "Ronaldo's smash")
    fx(bonk, sfx.bonk(), -6, -.45, "BONK (Rio's forehead)"); fx(bonk + .08, sfx.twinkle(2093, 4), -21, -.45, "stars"); fx(bonk + .12, sfx.ball_tap(), -22, -.3, "ball pops off")
    fx(cel, sfx.confetti(), -13, 0, "CR7 WINS confetti"); fx(cel, sfx.crowd(2.3, .15, 1.0, seed=33), -15, 0, "crowd")
    fx(S["rio_sulks"], sfx.sad_trombone(), -14, 0, "sad trombone")
    fx(S["thats_cristiano"] + .05, sfx.ding(1318, 1.8), -15, 0, "CR7"); fx(W("ronaldo") + .1, sfx.twinkle(1760, 5), -22, 0, "wink")
    k = int(np.ceil(S["any_game"] / .45))
    while k * .45 < 79.45:
        fx(k * .45, sfx.ball_tap(), -22, -.35, "keepy-up"); k += 1
    for ts in (78.55, 79.1): fx(ts, sfx.huff(), -32, .4, "Evra pants")
    fall = 79.5
    fx(fall, sfx.slide_whistle(1500, 200, .42), -17, .4, "Evra falls"); fx(fall + .42, sfx.thud(70, .4), -7, .4, "thud"); fx(fall + .42, sfx.poof(.6), -17, .4, "dust")
    fx(fall + .5, sfx.boxing_bell(), -14, 0, "K.O. bell")
    # ---- ambience beds
    def outdoor(t0, t1, level=-44): bed(t0, t1, sfx.air_bed(t1 - t0 + .5), level, "air"); bed(t0, t1, sfx.birds(t1 - t0 + .5, .45) * .5, level - 8, "birds")
    outdoor(0, S["table"]); outdoor(S["garden_invite"], S["laps"]); outdoor(S["goal"], S["dior"]); outdoor(S["warrior"], S["happy"])
    outdoor(S["machine"], S["two_weeks"]); outdoor(S["revenge"], TOTAL)
    bed(S["table"], S["garden_invite"], sfx.room_bed(S["garden_invite"] - S["table"] + .5), -45, "kitchen room tone")
    bed(S["hope"], S["hope"] + 2.2, sfx.wind_bed(2.7), -41, "wind through the doorway")
    bed(S["laps"], S["sauna"], sfx.room_bed(S["sauna"] - S["laps"] + .5) * 1.0 + sfx.water_bed(S["sauna"] - S["laps"] + .5, 6) * .4, -43, "pool hall")
    bed(S["sauna"], S["jacuzzi"], sfx.steam_bed(S["jacuzzi"] - S["sauna"] + .5), -42, "steam")
    bed(S["jacuzzi"], S["goal"], sfx.water_bed(S["goal"] - S["jacuzzi"] + .5, 18), -40, "jacuzzi bubbles")
    bed(S["happy"], S["machine"], sfx.water_bed(S["machine"] - S["happy"] + .5, 8), -46, "jacuzzi bubbles (far)")
    t0 = S["two_weeks"]; bed(t0, S["revenge"], sfx.cricket(S["revenge"] - t0 + .5) * 1.0 + sfx.air_bed(S["revenge"] - t0 + .5) * .6, -41, "night crickets")
    bed(S["rio_sulks"], S["thats_cristiano"], sfx.rain_bed(S["thats_cristiano"] - S["rio_sulks"] + .4), -41, "rain")
    bed(S["tt_rally"], 60.5, sfx.air_bed(60.5 - S["tt_rally"] + .5), -46, "air")


def loudnorm(src, dst):
    cmd = ["ffmpeg", "-hide_banner", "-i", src, "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"]
    err = subprocess.run(cmd, capture_output=True, text=True).stderr
    m = json.loads(err[err.rindex("{"):err.rindex("}") + 1])
    af = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-af", af, "-ar", "48000", dst], check=True)
    return m


def main():
    os.makedirs("build/audio", exist_ok=True)
    v = voice(); duck = duck_curve(v)
    music = build_music()
    act = np.abs(music).max(1) > 1e-4
    music = music / (np.sqrt(np.mean(music[act] ** 2)) + 1e-9)                  # RMS 1.0 over the parts that play
    under, free = db(MUSIC_UNDER), db(MUSIC_FREE)
    music = music * (under + (free - under) * duck)[:, None]
    cues(); place_cues(v.mean(1))
    sfxs = np.stack([SFX.L[:N], SFX.R[:N]], 1); beds = np.stack([BEDS.L[:N], BEDS.R[:N]], 1)
    for nm, a in (("voice", v), ("music", music), ("effects", sfxs + beds), ("sfx_only", sfxs), ("beds_only", beds)): sf.write(f"build/audio/{nm}.wav", a.astype(np.float32), SR, subtype="FLOAT")
    mix = v + music + sfxs + beds
    print("mix peak %.2f (%.1f dBFS)" % (np.abs(mix).max(), 20 * np.log10(np.abs(mix).max())))
    sf.write("build/audio/mix_raw.wav", mix.astype(np.float32), SR, subtype="FLOAT")
    m = loudnorm("build/audio/mix_raw.wav", "build/audio/mix.wav")
    print("before loudnorm: I %s LUFS, TP %s dBTP" % (m["input_i"], m["input_tp"]))
    pic = "build/picture.mp4"
    if not os.path.exists(pic): shutil.copy(OUT, pic)
    tmp = "build/_final.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", pic, "-i", "build/audio/mix.wav", "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "256k", "-ar", "48000", "-shortest", "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, OUT)
    json.dump(sorted(LOG, key=lambda c: c["t"]), open("soundtrack_cues.json", "w"), indent=1)
    print("done ->", OUT, len(LOG), "sound cues")


if __name__ == "__main__":
    main()

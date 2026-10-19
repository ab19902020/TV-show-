"""Render the film: every frame from direction.py, in parallel chunks, then the sound mix and the final MP4.

python3 render.py                       full film -> anonymous_feedback.mp4
python3 render.py --stills out.jpg T..  contact sheet of single frames
python3 render.py --run out.jpg T0 T1   consecutive frames (motion check)
"""
import os, sys, json, subprocess, numpy as np, cv2
from functools import lru_cache
import direction as D
import engine, stage, cast, props, sets, face
from engine import OW, OH

FPS = D.FPS
CH = {"tim": "Tim_Canterbury", "gareth": "Gareth_Keenan", "brent": "David_Brent"}
WHO = {"brent": "brent", "gareth": "gareth", "tim": "tim"}

# where each character is on each set (world px of that plate)
PLACE = {
    "desks": dict(
        tim=dict(pos=(530, 300), scale=2.25, anchor="eyes"),
        gareth=dict(pos=(1080, 312), scale=2.25, anchor="eyes"),
        brent=dict(pos=(1432, 656), scale=2.25, anchor="feet", mirror=True, nudge={"12_lean_forward": (-21, 0)}),
    ),
    "tim": dict(tim=dict(pos=(858, 478), scale=3.0, anchor="eyes")),
    "gareth": dict(gareth=dict(pos=(905, 443), scale=3.0, anchor="eyes")),
    "interview": dict(brent=dict(pos=(842, 818), scale=2.2, anchor="feet", mirror=True,
                                 nudge={"19_seated_folded_arms": (-29, 2)})),
}
DESK = {"desks": (497, 548), "tim": (745, 2000), "gareth": (668, 2000)}
SEATED = {"tim", "gareth"}
# prop placement per set
BOX = {"desks": ((1326, 540), 1.32), "gareth": ((1272, 708), 1.75)}
PAD = {"desks": ((1104, 541), 1.55), "gareth": ((948, 728), 2.05)}
PEN = {"desks": 1.55, "gareth": 2.05}
# hand points on the drawings (native px, as drawn): where a held prop sits
HAND = {
    ("David_Brent", "02_talking_gesture"): (238, 133),
    ("David_Brent", "08_wave"): (66, 101),
    ("Gareth_Keenan", "16_typing"): (163, 146),
    ("Gareth_Keenan", "13_seated_front"): (112, 166),
}
SLIP_ON_BOX = (1330, 452)

# ------------------------------------------------------------------ tracks
TR = dict(smile=0.28, lid=0.12, rot=0.45, dy=0.3, pen_up=0.25)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def value(c, attr, t, default=0.0):
    ks = D.TRACK.get((c, attr))
    if not ks:
        return default
    v = ks[0][1]
    for tk, vk in ks:
        if tk > t:
            break
        prev = v
        v = prev + (vk - prev) * ease((t - tk) / TR.get(attr, 0.2)) if t - tk < TR.get(attr, 0.2) else vk
    return v


def pose_at(c, t):
    """-> (current pose, previous pose, seconds since the swap). Poses swap on a frame (no see-through
    dissolve); the body then settles into the new drawing (see settle())."""
    ks = D.TRACK[(c, "pose")]
    cur, prev, tk = ks[0][1], None, -9.0
    for t0, p in ks:
        if t0 > t:
            break
        if p != cur:
            prev, cur, tk = cur, p, t0
    return cur, prev, t - tk


def settle(c, t, setname):
    """after a pose swap the head starts where it was and eases into the new drawing's place (0.2 s)"""
    cur, prev, dt = pose_at(c, t)
    if prev is None or dt > 0.2:
        return np.zeros(2)
    pl = PLACE[setname][c]

    def head(pose):
        r = cast.rig(CH[c], pose)
        anchor = r["eyes_mid"] if pl.get("anchor", "eyes") == "eyes" else r["feet"]
        anchor = anchor + np.array(pl.get("nudge", {}).get(pose, (0, 0))) * 4
        top = np.array([r["eyes_mid"][0], r["top"]], float) if r["eyes"] else np.array([anchor[0], r["top"]], float)
        d = (top - anchor) / 4 * pl["scale"]
        if pl.get("mirror"):
            d[0] = -d[0]
        return d
    off = (head(prev) - head(cur)) * 0.55
    return off * (1 - ease(dt / 0.2))


def gaze_at(c, t, sac=0.09):
    ks = D.TRACK[(c, "gaze")]
    g = np.array(ks[0][1], float)
    for tk, gk in ks:
        if tk > t:
            break
        k = ease((t - tk) / sac)
        g = g + (np.array(gk, float) - g) * k
    return g


def blink_times(c):
    rng = np.random.default_rng({"tim": 11, "gareth": 23, "brent": 5}[c])
    out, t = [], rng.uniform(0.5, 2.0)
    while t < D.TOTAL:
        out.append(t)
        t += rng.uniform(2.2, 5.2)
    # blink with the bigger eye moves, sometimes
    ks = D.TRACK.get((c, "gaze"), [])
    for (t0, g0), (t1, g1) in zip(ks, ks[1:]):
        if abs(g1[0] - g0[0]) + abs(g1[1] - g0[1]) > 1.0 and rng.random() < 0.45:
            out.append(t1 - 0.02)
    out = sorted(out)
    return [b for b in out if not any(a <= b <= z for a, z in D.NO_BLINK[c])]


BLINKS = {c: blink_times(c) for c in CH}


def blink_lid(c, t):
    for b in BLINKS[c]:
        f = (t - b) * FPS
        if 0 <= f < 5:
            return [0.55, 1.0, 1.0, 0.6, 0.2][int(f)]
    return 0.0


# ------------------------------------------------------------------ speech
@lru_cache(maxsize=None)
def line_env(lid):
    import librosa
    L = D.P[lid]
    y, sr = librosa.load(f"src/{L['who']}.mp3", sr=16000, mono=True, offset=L["a0"], duration=L["a1"] - L["a0"])
    r = librosa.feature.rms(y=y, frame_length=640, hop_length=160)[0]
    return r / (np.percentile(r, 95) + 1e-6)


def speech(c, t):
    """-> (viseme, amount)"""
    for lid, t0 in D.LINES.items():
        L = D.P[lid]
        if L["who"] != c:
            continue
        rt = t - t0
        if rt < 0 or rt > L["a1"] - L["a0"]:
            continue
        tl = rt + 0.04        # the mouth leads the sound by a frame
        vis = None
        for ph in L["phones"]:
            if ph["s"] <= tl < ph["e"]:
                vis = face.PH.get(ph["p"], "small")
                break
        # closures last at least two frames
        for ph in L["phones"]:
            if ph["p"] in ("M", "B", "P") and ph["s"] - 0.04 <= tl < max(ph["e"], ph["s"] + 2.0 / FPS):
                vis = "MBP"
        if vis is None:
            return "rest", 0.0
        env = line_env(lid)
        i = min(int(rt * 100), len(env) - 1)
        amt = float(np.clip(0.55 + 0.6 * env[max(i - 2, 0):i + 3].mean(), 0.55, 1.15))
        return vis, amt
    return "rest", 0.0


# ------------------------------------------------------------------ helpers
def shot_at(t):
    for s in D.SHOTS:
        if s["t0"] <= t < s["t1"]:
            return s
    return None


def cam_at(s, t):
    ks = s["cam"]
    c = np.array(ks[0][1], float)
    for (t0, c0), (t1, c1) in zip(ks, ks[1:]):
        if t >= t1:
            c = np.array(c1, float)
        elif t > t0:
            c = np.array(c0, float) + (np.array(c1, float) - np.array(c0, float)) * ease((t - t0) / (t1 - t0))
    if len(ks) == 1:
        c = np.array(ks[0][1], float)
    if s["handheld"]:
        # documentary operator: slow, small drift, never shake
        ph = s["t0"] * 1.7
        a = c[2] * 0.0016
        c[0] += a * (np.sin(0.61 * t + ph) + 0.6 * np.sin(1.37 * t + 2 * ph))
        c[1] += a * 0.7 * (np.sin(0.83 * t + 1.3 + ph) + 0.5 * np.sin(1.91 * t + ph))
        c[2] *= 1 + 0.0012 * np.sin(0.37 * t + ph)
    return tuple(c)


def facekey(c, t, mirror):
    g = gaze_at(c, t)
    if mirror:
        g = np.array([-g[0], g[1]])
    lid = max(value(c, "lid", t), blink_lid(c, t))
    vis, amt = speech(c, t)
    sm = value(c, "smile", t)
    skew = 0.7 if c == "tim" else 0.0
    return ((round(g[0], 2), round(g[1], 2)), round(lid * 20) / 20, vis, round(amt, 1), round(sm * 20) / 20, skew)


def actor_M(c, pose, t, pl, Mcam, z, setname):
    r = cast.rig(CH[c], pose)
    anchor = r["eyes_mid"] if pl.get("anchor", "eyes") == "eyes" else r["feet"]
    dy = value(c, "dy", t)
    breath = 0.9 * np.sin(2 * np.pi * t / {"tim": 4.1, "gareth": 3.6, "brent": 4.6}[c] + len(c))
    pos = (pl["pos"][0], pl["pos"][1] + dy + breath * (0.4 if c in SEATED else 0.0))
    rot = value(c, "rot", t)
    if pl.get("mirror"):
        rot = -rot
    return engine.actor_matrix(anchor, pos, pl["scale"], z, Mcam, pl.get("mirror", False), rot), pos, rot


def draw_actor(frame, c, t, setname, Mcam, z):
    pl = PLACE[setname][c]
    cur, prev, dt = pose_at(c, t)
    fk = facekey(c, t, pl.get("mirror", False))
    desk = DESK.get(setname) if (c in SEATED or (setname == "desks" and c == "brent")) else None
    M, pos, rot = actor_M(c, cur, t, pl, Mcam, z, setname)
    off = settle(c, t, setname)
    stage_draw(frame, Mcam, z, CH[c], cur, fk, pl, (pos[0] + off[0], pos[1] + off[1]), rot, desk, 1.0)
    return cur


def stage_draw(frame, Mcam, z, char, pose, fk, pl, pos, rot, desk, alpha):
    p2 = dict(pl)
    p2["pos"] = pos
    # only the seated men rest their hands on the desk; Brent stands behind it
    stage.draw(frame, Mcam, z, char, pose, fk, p2, desk=desk, alpha=alpha, rot=rot, hands=char != "David_Brent")


def draw_prop(frame, prop, Mcam, world_pos, scale, rot=0.0):
    """props are drawn at props.R px per world px; scale 1 = their drawn world size"""
    rgb, a, anc = prop
    M = engine.actor_matrix(anc, world_pos, scale * 4.0 / props.R, None, Mcam, False, rot)
    engine.comp(frame, engine.place(frame, rgb, a, M))


def hand_world(c, pose, t, setname, Mcam, z):
    """world position of the hand point on the drawing"""
    pl = PLACE[setname][c]
    r = cast.rig(CH[c], pose)
    anchor = r["eyes_mid"] if pl.get("anchor", "eyes") == "eyes" else r["feet"]
    _, pos, rot = actor_M(c, pose, t, pl, Mcam, z, setname)
    M = engine.actor_matrix(anchor, pos, pl["scale"], None, np.array([[1.0, 0, 0], [0, 1.0, 0]]),
                            pl.get("mirror", False), rot)
    h = np.array(HAND[(CH[c], pose)], float) * 4 + 1.5
    return M @ np.array([h[0], h[1], 1.0])


def events(kind):
    return [(t, a) for t, k, a in D.EVENTS if k == kind]


def slip_state(t):
    """-> (where, fold): where in {'box', 'hand', 'lid'}"""
    where = "box"
    for t0, a in events("slip"):
        if t >= t0:
            where = {"hand": "hand", "box": "lid"}[a["state"]]
    fold = 0.0
    for t0, a in events("fold"):
        if t >= t0:
            fold = ease((t - t0) / a["dur"])
    if where == "lid":
        fold = 1.0
    return where, fold


def pen_pose(t):
    """Gareth's pen: offset of the tip wiggle while writing, tap dip, raise"""
    rot, dx, dy = 0.0, 0.0, 0.0
    for t0, a in events("write"):
        if t0 <= t < t0 + a["dur"]:
            k = t - t0
            dx += 2.2 * np.sin(2 * np.pi * 6.5 * k) + 6 * (k / a["dur"])
            dy += 1.2 * np.sin(2 * np.pi * 9.1 * k + 1)
            rot += 4 * np.sin(2 * np.pi * 6.5 * k)
    for t0, a in events("pen_tap"):
        if t0 - 0.12 <= t < t0 + 0.18:
            k = (t - (t0 - 0.12)) / 0.3
            dy += 6 * np.sin(np.pi * k)
    dy -= 9 * value("gareth", "pen_up", t)
    return rot, dx, dy


# ------------------------------------------------------------------ walkers
@lru_cache(maxsize=None)
def walk_frames(char):
    """the 8 walk drawings, cleaned to one size: (rgb, a, foot anchor, height) each"""
    out = []
    hs = []
    raw = []
    for i in range(1, 9):
        rgb, a = cast.drawing(char, f"{i:02d}_frame_{i:02d}", "Walk")
        ys, xs = np.where(a > 128)
        raw.append((rgb, a, ys.min(), ys.max(), xs))
        hs.append(ys.max() - ys.min())
    H = np.median(hs)
    for rgb, a, y0, y1, xs in raw:
        s = H / (y1 - y0)
        # anchor: bottom of the shoes, horizontally the middle of the torso (hips/belly band)
        band = a[y0 + int(0.42 * (y1 - y0)):y0 + int(0.62 * (y1 - y0))] > 128
        hx = np.where(band)[1].mean()
        out.append((rgb.astype(np.float32), a.astype(np.float32) / 255, np.array([hx, y1], float), s, y1 - y0))
    return out


def draw_walkers(frame, setname, t, Mcam, z):
    for wk in D.EXTRAS:
        if wk["set"] != setname or not os.path.exists(f"{cast.UP}/{wk['char']}/Walk/08_frame_08.png"):
            continue
        dist = (t - wk["t0"]) * wk["speed"]
        if dist < 0:
            continue
        total = abs(wk["x1"] - wk["x0"])
        if dist > total:
            continue
        d = 1 if wk["x1"] > wk["x0"] else -1
        x = wk["x0"] + d * dist
        frames = walk_frames(wk["char"])
        # one step per ~0.42 of the walker's height; 8 drawings per two steps
        stride = 0.42 * wk["h"]
        fi = int(dist / (2 * stride) * 8) % 8
        rgb, a, anc, s_norm, hpx = frames[fi]
        scale = wk["h"] / (hpx * s_norm) * 4 * s_norm
        bob = -abs(np.sin(np.pi * dist / stride)) * wk["h"] * 0.012
        M = engine.actor_matrix(anc, (x, wk["y"] + bob), scale, z, Mcam, d < 0, 0.0)
        engine.comp(frame, engine.place(frame, rgb, a, M))


# ------------------------------------------------------------------ one frame
def render_frame(t):
    s = shot_at(t)
    if s is None or t >= D.END:
        return np.zeros((OH, OW, 3), np.uint8)
    name = s["set"]
    cam = cam_at(s, t)
    img, front, mid = engine.render_plate(name, cam)
    Mcam, z = engine.cam_matrix(cam)
    frame = img.copy()
    draw_walkers(frame, name, t, Mcam, z)
    if mid.any():
        frame = frame * (1 - mid[..., None]) + img * mid[..., None]
    where, fold = slip_state(t)
    if name in PAD:
        (px, py), ps = PAD[name]
        draw_prop(frame, props.notebook(), Mcam, (px, py), ps)
    actors = PLACE.get(name, {})
    poses = {}
    for c in ("tim", "gareth", "brent"):
        if c in actors:
            poses[c] = draw_actor(frame, c, t, name, Mcam, z)
    # what is on the desks stands in front of the seated people
    frame = frame * (1 - front[..., None]) + img * front[..., None]
    if name in BOX:
        (bx, by), bs = BOX[name]
        draw_prop(frame, props.box(), Mcam, (bx, by), bs)
        if where == "lid" and name == "desks":
            draw_prop(frame, props.slip(1.0), Mcam, SLIP_ON_BOX, 1.0, rot=-8)
    # Gareth's pen: in his hand when he is writing (16), otherwise on the pad
    if "gareth" in poses:
        pose = poses["gareth"]
        sc = PLACE[name]["gareth"]["scale"] / 2.25
        prot, pdx, pdy = pen_pose(t)
        if pose == "16_typing":
            hx, hy = hand_world("gareth", pose, t, name, Mcam, z)
            draw_prop(frame, props.pen(), Mcam, (hx + pdx * sc - 4 * sc, hy + pdy * sc + 3 * sc), PEN[name],
                      rot=-55 + prot)
        elif name in PAD:
            (px, py), ps = PAD[name]
            draw_prop(frame, props.pen(), Mcam, (px + 8 * ps, py - 8 * ps), PEN[name], rot=-12)
    # the slip in Brent's hand
    if "brent" in poses and where == "hand" and (CH["brent"], poses["brent"]) in HAND:
        hx, hy = hand_world("brent", poses["brent"], t, name, Mcam, z)
        sl = props.slip(round(fold * 10) / 10)
        tilt = 8 if poses["brent"] == "02_talking_gesture" else -6
        draw_prop(frame, sl, Mcam, (hx, hy + 6), 1.0, rot=tilt)
    return engine.finish(frame, int(t * FPS))


# ------------------------------------------------------------------ output
def stills(out, times, w=640):
    tiles = []
    for t in times:
        f = render_frame(t)
        f = cv2.resize(f, (w, w * 9 // 16), interpolation=cv2.INTER_AREA)
        cv2.putText(f, f"{t:.2f}", (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        tiles.append(f)
    cols = 3 if len(tiles) > 4 else len(tiles)
    while len(tiles) % cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.hstack(tiles[i:i + cols]) for i in range(0, len(tiles), cols)]
    cv2.imwrite(out, cv2.cvtColor(np.vstack(rows), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 90])


def render_chunk(i0, i1, path):
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
           "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(i0, i1):
        p.stdin.write(render_frame(i / FPS).tobytes())
        if (i - i0) % 100 == 0:
            print(path, i, "/", i1, flush=True)
    p.stdin.close()
    p.wait()


if __name__ == "__main__":
    a = sys.argv[1:]
    if a and a[0] == "--stills":
        stills(a[1], [float(x) for x in a[2:]])
    elif a and a[0] == "--run":
        t0, t1 = float(a[2]), float(a[3])
        step = float(a[4]) if len(a) > 4 else 1.0 / FPS
        stills(a[1], list(np.arange(t0, t1, step)), w=480)
    elif a and a[0] == "--chunk":
        render_chunk(int(a[1]), int(a[2]), a[3])
    else:
        print("use render.sh for the full film")

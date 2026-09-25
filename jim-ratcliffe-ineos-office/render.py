"""Render the Jim Ratcliffe INEOS-office scene: camera, performance, lip sync, compositing, grade.
  python3 render.py still 12.5 30 ...     -> still_<t>.png
  python3 render.py chunk A B out.mp4     -> frames [A, B)
  python3 render.py audio                 -> scene_audio.wav"""
import numpy as np, cv2, json, sys, subprocess, math, pickle
from collections import OrderedDict
import perf, direction as D
from rig import Rig, render_layers, to3, grade, over, F_KNOT, F_FLOOR, NECK_PIVOT
from walker import build as build_walkers
from profile import Profile
from mouths import Mouths
from occlusion import S as OS
import blink

FPS, OW, OH = 30, 1920, 1080
TL = perf.TL; N = TL["n"]
BGW, BGH = 1672, 941
# glossy desk top (world px) where he is reflected, minus the objects standing on it
DESKTOP = [(700, 652), (1160, 662), (1185, 675), (1215, 715), (1235, 755), (1243, 790), (1225, 798), (700, 800)]
DESK_OBJECTS = [(700, 648, 978, 730), (946, 681, 1094, 800)]

# ---------------------------------------------------------------- audio
import librosa
def build_audio():
    sr = 44100
    out = np.zeros(int(TL["total"] * sr) + sr, np.float32)
    for sg in TL["segments"]:                      # clips (or parts of them) at their scene times
        y, _ = librosa.load(sg["file"], sr=sr, mono=True)
        y = y[int(round(sg["a"] * sr)):int(round(sg["b"] * sr))]
        n = min(len(y), 1600)                          # 36 ms fades at the cut points (no clicks)
        y[:n] *= np.linspace(0, 1, n); y[-n:] *= np.linspace(1, 0, n)
        a = int(round(sg["at"] * sr)); out[a:a + len(y)] += y
    return out[: int(TL["total"] * sr)], sr
AUDIO, ASR = build_audio()
hop = ASR // FPS
ENV = np.array([np.sqrt(np.mean(AUDIO[i * hop:(i + 1) * hop] ** 2) + 1e-10) for i in range(N)])
CH = perf.channels(ENV)

# ---------------------------------------------------------------- camera
def ease(u): return 0.5 - 0.5 * math.cos(math.pi * min(max(u, 0), 1))
def camera(t):
    for (s, e, a, b, punch) in D.SHOTS:
        if s <= t < e: break
    u = ease((t - s) / max(min(e, TL["total"]) - s, 1e-3))
    cx, cy, w = [a[j] + (b[j] - a[j]) * u for j in range(3)]
    if punch:                                   # snap zoom into the beat + a short jolt
        k = math.exp(-(t - s) / 0.07)
        w *= 1 + 0.10 * k
        cx += w * 0.004 * k * math.sin((t - s) * 60); cy += w * 0.003 * k * math.cos((t - s) * 55)
    cx += w * 0.0020 * (math.sin(2 * math.pi * 0.21 * t + 1.3) + 0.6 * math.sin(2 * math.pi * 0.47 * t + 0.2))
    cy += w * 0.0016 * (math.sin(2 * math.pi * 0.17 * t + 2.1) + 0.5 * math.sin(2 * math.pi * 0.53 * t + 0.9))
    w = min(w, BGW); h = w * OH / OW
    cx = min(max(cx, w / 2), BGW - w / 2); cy = min(max(cy, h / 2), BGH - h / 2)
    return cx, cy, w

# ---------------------------------------------------------------- character
class Actor:
    def __init__(self):
        self.rig = Rig()
        self.walkers, self.views = build_walkers(self.rig.P)
        self.profile = Profile(self.rig.P)
        self.mouths = Mouths()
        self.cache = OrderedDict()
        self.eyes = {h: blink.eyes_of(self.rig.head[h]["raw"], self.mouths.to_head[h])
                     for h in blink.BLINKERS if h in self.mouths.to_head}
        self.blinks = blink.schedule(TL["total"])

    def head_img(self, head, vis, bl=0.0):
        hd = self.rig.head[head]
        if vis is not None and (head not in self.mouths.to_head or head == "THINKING"): vis = None
        if head not in self.eyes: bl = 0.0
        bl = round(bl, 2)
        if vis is None and bl == 0: return hd["img"]
        key = (head, vis, bl)
        if key in self.cache: self.cache.move_to_end(key); return self.cache[key]
        raw = hd["raw"]
        col = np.ascontiguousarray(raw[..., :3])
        if vis is not None: col = self.mouths.composite(head, col, raw[..., 3], vis)
        if bl > 0: col = blink.apply(col, self.eyes[head], bl)
        a = hd["img"][..., 3:4]
        img = np.dstack([grade(col).astype(np.float32) * a, a]).astype(np.float32)
        self.cache[key] = img
        if len(self.cache) > 120: self.cache.popitem(last=False)
        return img

    def layers(self, i):
        """-> dict(layers, Mw (3x3 rig->world), x, floor, k, seat) or None when he is off stage"""
        t = i / FPS
        (x, floor, k), b = perf.place_at(t)
        if b["kind"] == "off": return None
        seat = perf.SEAT_DROP * perf.seat_at(t)
        def Mw_for(cx, frig): return np.array([[k, 0, x - k * cx], [0, k, floor + seat - k * frig], [0, 0, 1]])
        out = dict(x=x, floor=floor, k=k, seat=seat)
        breath = 1 + 0.006 * math.sin(2 * math.pi * t / 3.7)
        if b["kind"] == "walk":
            w = self.walkers[b["d"]]
            u = t - b["t0"]; half = b["period"] / 2
            leg = ["WALK 1", "WALK 2", "WALK 3", "WALK 4"][int(u / half) % 4]
            bob = -10 * abs(math.sin(math.pi * u / b["period"]))
            out.update(layers=w.layers(leg, bob, 1.5), Mw=Mw_for(w.hip_x, w.floor)); return out
        if b["kind"] == "view":
            v = self.views[b["name"]]
            out.update(layers=v.layers(), Mw=Mw_for(v.cx, v.floor)); return out
        th, dy, look = perf.head_motion(i, CH)
        if b["kind"] == "profile":
            pr = self.profile
            head_M = cv2.getRotationMatrix2D((170.0, 330.0), 0.6 * th, 1.0); head_M[1, 2] += dy * 0.25
            Br = np.array([[1, 0, 0], [0, breath, (1 - breath) * 1400]], np.float64)
            out.update(layers=pr.layers(perf.viseme(i), perf.profile_arm(t), head_M, Br), Mw=Mw_for(pr.hip_x, pr.floor))
            return out
        # ---- front rig
        torso = perf.at(perf.POSES, t, "ARMS DOWN")
        head = perf.at(perf.HEADS, t, "NEUTRAL")
        vis = perf.viseme(i)
        head_M = cv2.getRotationMatrix2D(NECK_PIVOT, th, 1.0); head_M[1, 2] += dy * 0.35
        legs, step_bob = perf.pacing_legs(t, b)
        bdy, sx, sy = perf.body_motion(t, CH, i)
        hip = (F_KNOT[0], 900.0)
        lean = CH["lean"][i] + 0.6 * math.sin(2 * math.pi * t / 6.1) + 0.5 * (legs[0] - legs[1]) / 22.0
        R = to3(cv2.getRotationMatrix2D(hip, -lean, 1.0))
        Tb = np.array([[1, 0, 0], [0, 1, bdy + step_bob], [0, 0, 1]], np.float64)
        Sc = np.array([[sx, 0, (1 - sx) * hip[0]], [0, sy * breath, (1 - sy * breath) * 900], [0, 0, 1]], np.float64)
        torso_M = (Tb @ R @ Sc)[:2]
        hand_M = None
        if torso in self.rig.torso and "pivot" in self.rig.torso[torso]:
            px, py = self.rig.torso[torso]["pivot"]
            if torso == "PALM OUT STOP":
                d = perf.chop_dy(t); s_ = 1 + 0.0012 * max(d, 0)
                hand_M = np.array([[s_, 0, px * (1 - s_)], [0, s_, py * (1 - s_) + d], [0, 0, 1]])
            else:
                s_ = 1 + perf.jab_s(t)
                hand_M = np.array([[s_, 0, px * (1 - s_) - 60 * (s_ - 1)], [0, s_, py * (1 - s_) + 30 * (s_ - 1)], [0, 0, 1]])
        L = self.rig.layers(torso, head, head_M=head_M, torso_M=torso_M, hand_M=hand_M,
                            legs=legs if seat == 0 else (0.0, 0.0))
        hd = self.rig.head[head]
        bl = max(blink.amount_at(i, self.blinks), 0.5 * look)            # lids lowered = looking down at the watch
        L = [(self.head_img(head, vis, bl) if img is hd["img"] else img, M) for img, M in L]
        out.update(layers=L, Mw=Mw_for(F_KNOT[0], F_FLOOR)); return out

# ---------------------------------------------------------------- plates
def load_plates():
    bg4 = cv2.imread("src/office_x4.png")
    oc4 = cv2.imread("src/occlusion_x4.png", 0)
    dt = np.zeros(oc4.shape, np.uint8)
    cv2.fillPoly(dt, [np.array([(x * OS, y * OS) for x, y in DESKTOP], np.int32)], 255)
    for x0, y0, x1, y1 in DESK_OBJECTS: dt[y0 * OS:y1 * OS, x0 * OS:x1 * OS] = 0
    dt = cv2.GaussianBlur(dt, (0, 0), 6)
    lv = {4: (bg4, oc4, dt)}
    for L in (2, 1):
        f = L / 4
        lv[L] = tuple(cv2.resize(p, None, fx=f, fy=f, interpolation=cv2.INTER_AREA) for p in (bg4, oc4, dt))
    return lv

YY, XX = np.mgrid[0:OH, 0:OW].astype(np.float32)
RR = np.sqrt(((XX - OW / 2) / (OW / 2)) ** 2 + ((YY - OH / 2) / (OH / 2)) ** 2)
VIGN = (1 - 0.28 * np.clip(RR / 1.35, 0, 1) ** 2.2)[..., None]

def rim_light(ch, z):
    """warm window light catching his top/right edges (the sun is behind him, screen right)."""
    a = ch[..., 3]
    if a.max() <= 0: return ch
    d = max(1.5, 2.2 * z)
    sh = cv2.warpAffine(a, np.float32([[1, 0, -d], [0, 1, d * 0.8]]), (a.shape[1], a.shape[0]))
    rim = np.clip(a - sh, 0, 1)
    rim = cv2.GaussianBlur(rim, (0, 0), max(0.8, 0.6 * z)) * a
    out = ch.copy()
    out[..., :3] += rim[..., None] * np.float32([150, 190, 225]) * 0.42
    return out

def render_frame(i, actor, lv):
    t = i / FPS
    cx, cy, w = camera(t)
    z = OW / w; h = w * OH / OW
    ox, oy = cx - w / 2, cy - h / 2
    L = 1 if z <= 1.5 else (2 if z <= 3.0 else 4)
    bgL, ocL, dtL = lv[L]
    A = np.float32([[z / L, 0, -z * ox], [0, z / L, -z * oy]])
    interp = cv2.INTER_CUBIC if z / L > 1 else cv2.INTER_LINEAR
    bg = cv2.warpAffine(bgL, A, (OW, OH), flags=interp, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    oc = cv2.warpAffine(ocL, A, (OW, OH), flags=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255
    dtm = cv2.warpAffine(dtL, A, (OW, OH), flags=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255
    # depth of field: he is in focus, the set behind him (and the desk in front) soften in close shots
    sig = max(0.0, (z - 1.9)) * 0.8
    if sig > 0.3:
        small = cv2.resize(bg, (OW // 2, OH // 2), interpolation=cv2.INTER_AREA)
        bg = cv2.resize(cv2.GaussianBlur(small, (0, 0), sig / 2), (OW, OH), interpolation=cv2.INTER_LINEAR)
    frame = bg
    C = np.array([[z, 0, -z * ox], [0, z, -z * oy], [0, 0, 1]])
    res = actor.layers(i)
    if res is not None:
        ch = render_layers(res["layers"], C @ res["Mw"], (OW, OH))
        ch = rim_light(ch, z)
        x, floor, k, seat = res["x"], res["floor"], res["k"], res["seat"]
        # contact shadow on the floor (visible only where the floor is: in front of the windows, the rug lane)
        if seat == 0:
            sh = np.zeros((OH, OW), np.float32)
            cv2.ellipse(sh, (int(z * (x - ox)), int(z * (floor + 2 - oy))), (max(1, int(z * 175 * k)), max(1, int(z * 27 * k))), 0, 0, 360, 1, -1)
            sh = cv2.GaussianBlur(sh, (0, 0), max(1, 15 * z * k))[..., None] * 0.45
            frame = frame * (1 - sh)
        ca = np.clip(ch[..., 3:4], 0, 1)
        frame = ch[..., :3] + frame * (1 - ca)
        # soft reflection in the glossy black desk top when he stands behind it (mirrored about the desk plane)
        if x < 1235 and seat == 0:
            sy = z * (floor - 0.75 / 1.8 * k * 1516 - oy)
            refl = cv2.warpAffine(ch, np.float32([[1, 0, 0], [0, -1, 2 * sy]]), (OW, OH), flags=cv2.INTER_LINEAR)
            fade = np.clip(1 - (YY[..., None] - sy) / (z * 150), 0, 1)
            ra = np.clip(refl[..., 3:4], 0, 1) * dtm * 0.20 * fade
            rc = refl[..., :3] / np.maximum(refl[..., 3:4], 1e-3)
            frame = frame * (1 - ra) + rc * ra
        # everything in front of him: desk, things on it, side table, flowers, armchairs
        frame = bg * oc + frame * (1 - oc)
    # ---- grade
    f = frame / 255
    small = cv2.resize(f, (OW // 4, OH // 4), interpolation=cv2.INTER_AREA)
    bloom = cv2.resize(cv2.GaussianBlur(np.clip(small - 0.74, 0, None), (0, 0), 9), (OW, OH), interpolation=cv2.INTER_LINEAR)
    f = f + bloom * np.float32([0.40, 0.55, 0.70])
    f = np.clip((f - 0.5) * 1.04 + 0.5, 0, 1) * VIGN
    fade = min(1.0, t / D.FADE_IN, (TL["total"] - t) / D.FADE_OUT)
    f *= max(0.0, fade)
    f = f + np.random.default_rng(i).normal(0, 1.6 / 255, (OH, OW, 1)).astype(np.float32)
    return np.clip(f * 255 + 0.5, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "audio":
        import soundfile as sf
        sf.write("scene_audio.wav", AUDIO, ASR, subtype="PCM_24"); sys.exit()
    lv = load_plates(); actor = Actor()
    if mode == "still":
        for s in sys.argv[2:]:
            cv2.imwrite(f"still_{s}.png", render_frame(int(round(float(s) * FPS)), actor, lv))
    elif mode == "chunk":
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                              "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        import time; t0 = time.time()
        for i in range(a, b):
            p.stdin.write(render_frame(i, actor, lv).tobytes())
            if (i - a) % 50 == 0: print(out, i, round(time.time() - t0, 1), flush=True)
        p.stdin.close(); p.wait()

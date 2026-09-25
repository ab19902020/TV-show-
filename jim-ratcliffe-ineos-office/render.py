"""Render the Jim Ratcliffe INEOS-office scene: camera, performance, lip sync, compositing, grade.
  python3 render.py still 12.5 30 ...     -> still_<t>.png
  python3 render.py chunk A B out.mp4     -> frames [A, B)
  python3 render.py audio                 -> scene_audio.wav"""
import numpy as np, cv2, json, sys, subprocess, math, pickle
from collections import OrderedDict
import perf, direction as D
from rig import Rig, render_layers, to3, grade, over, F_KNOT, F_FLOOR, NECK_PIVOT
from walker import build as build_walkers
from mouths import Mouths
from occlusion import S as OS
import blink

FPS, OW, OH = 30, 1920, 1080
TL = perf.TL; N = TL["n"]
BGW, BGH = 1672, 941
FLOOR_Y = 870.0                    # world y of his feet (between the desk and the window)
K = 612.0 / 1516.0                 # world px per rig px (he is ~612 px tall at that depth)
DESK_PLANE_Y = FLOOR_Y - 0.75 / 1.8 * 612      # the desk-top plane seen at his depth (mirror line)
CLIPS = ["src/audio1.mp3", "src/audio2.mp3", "src/audio3.mp3", "src/audio4.mp3"]
# glossy desk top (world px) where he is reflected, minus the objects standing on it
DESKTOP = [(700, 652), (1160, 662), (1185, 675), (1215, 715), (1235, 755), (1243, 790), (1225, 798), (700, 800)]
DESK_OBJECTS = [(700, 648, 978, 730), (946, 681, 1094, 800)]

# ---------------------------------------------------------------- audio
import librosa
def build_audio():
    sr = 44100
    out = np.zeros(int(TL["total"] * sr) + sr, np.float32)
    for f, off in zip(CLIPS, TL["offsets"]):
        y, _ = librosa.load(f, sr=sr, mono=True)
        a = int(round(off * sr)); out[a:a + len(y)] += y
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
        self.walk = build_walkers(self.rig.P)
        self.mouths = Mouths()
        self.cache = OrderedDict()
        self.eyes = {h: blink.eyes_of(self.rig.head[h]["raw"], self.mouths.to_head[h])
                     for h in blink.BLINKERS if h in self.mouths.to_head}
        self.blinks = blink.schedule(TL["total"])

    def head_img(self, head, vis, bl=0.0):
        hd = self.rig.head[head]
        if vis is not None and (head not in self.mouths.to_head or head == "THINKING"): vis = None
        if head not in self.eyes: bl = 0.0
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
        if len(self.cache) > 80: self.cache.popitem(last=False)
        return img

    def layers(self, i):
        """-> (layers, 3x3 rig->world) or None"""
        t = i / FPS
        ws = perf.walk_state(t)
        if ws is not None:
            if ws[0] == "off": return None
            mode, leg, x, bob, lean = ws
            w = self.walk[mode]
            Mw = np.array([[K, 0, x - K * w.hip_x], [0, K, FLOOR_Y - K * w.floor], [0, 0, 1]])
            return w.layers(leg, bob, lean), Mw
        torso = perf.at(perf.POSES, t, "ARMS DOWN")
        head = perf.at(perf.HEADS, t, "NEUTRAL")
        vis = perf.viseme(i)
        th, dy = perf.head_motion(i, CH)
        head_M = cv2.getRotationMatrix2D(NECK_PIVOT, th, 1.0); head_M[1, 2] += dy * 0.35
        # torso: lean about the hips, dip on beats, settle 'pop' on swaps, breathing
        hip = (F_KNOT[0], 900.0)
        breath = 1 + 0.006 * math.sin(2 * math.pi * t / 3.7)
        lean = CH["lean"][i] + 0.6 * math.sin(2 * math.pi * t / 6.1)
        R = to3(cv2.getRotationMatrix2D(hip, -lean, 1.0))
        Tb = np.array([[1, 0, 0], [0, 1, 7 * CH["dip"][i] + 6 * CH["pop"][i]], [0, 0, 1]], np.float64)
        Br = np.array([[1, 0, 0], [0, breath, (1 - breath) * 900], [0, 0, 1]], np.float64)
        torso_M = (Tb @ R @ Br)[:2]
        L = self.rig.layers(torso, head, head_M=head_M, torso_M=torso_M)
        # swap in the lip-synced head drawing (the head layer is the one using the head's matrix)
        hd = self.rig.head[head]
        bl = blink.amount_at(i, self.blinks)
        L = [(self.head_img(head, vis, bl) if img is hd["img"] else img, M) for img, M in L]
        Mw = np.array([[K, 0, perf.MARK_X - K * F_KNOT[0]], [0, K, FLOOR_Y - K * F_FLOOR], [0, 0, 1]])
        return L, Mw

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
        layers, Mw = res
        ch = render_layers(layers, C @ Mw, (OW, OH))
        ch = rim_light(ch, z)
        # contact shadow on the floor (only visible where the floor is: the rug lane)
        ws = perf.walk_state(t)
        fx = ws[2] if ws is not None and ws[0] != "off" else perf.MARK_X
        sh = np.zeros((OH, OW), np.float32)
        cv2.ellipse(sh, (int(z * (fx - ox)), int(z * (FLOOR_Y + 2 - oy))), (max(1, int(z * 70)), max(1, int(z * 11))), 0, 0, 360, 1, -1)
        sh = cv2.GaussianBlur(sh, (0, 0), max(1, 6 * z))[..., None] * 0.45
        frame = frame * (1 - sh)
        # soft reflection in the glossy black desk top (mirrored about the desk plane at his depth)
        sy = z * (DESK_PLANE_Y - oy)
        refl = cv2.warpAffine(ch, np.float32([[1, 0, 0], [0, -1, 2 * sy]]), (OW, OH), flags=cv2.INTER_LINEAR)
        ca = np.clip(ch[..., 3:4], 0, 1)
        frame = ch[..., :3] + frame * (1 - ca)
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

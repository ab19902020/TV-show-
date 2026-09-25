"""Render the Roy Keane studio scene with the full-body rig: camera, performance, lip sync, compositing, grade."""
import numpy as np, cv2, json, sys, subprocess, math, random
import direction as D
from rig2 import Rig2, PAD
import perf
NECK_X = 600
FPS, OW, OH = 30, 1920, 1080
TL = json.load(open("timeline.json"))
N = TL["n"]
BGW, BGH = 1672, 941
K4 = 0.16                                # world px per body-crop (4x sheet) px
T0 = np.array([668 - K4 * NECK_X - K4 * PAD, 489 - K4 * 692])   # world position of rig-canvas origin

# ---------------------------------------------------------------- audio-driven signals
import librosa
def build_audio():
    sr = 44100
    total = int(TL["total"] * sr) + sr
    out = np.zeros(total, np.float32)
    for f, off in zip(["src/audio1.mp3", "src/audio2.mp3"], TL["offsets"]):
        y, _ = librosa.load(f, sr=sr, mono=True)
        a = int(round(off * sr)); out[a:a + len(y)] += y
    return out[: int(TL["total"] * sr)], sr
AUDIO, ASR = build_audio()
hop = ASR // FPS
env = np.array([np.sqrt(np.mean(AUDIO[i * hop:(i + 1) * hop] ** 2) + 1e-10) for i in range(N)])
edb = 20 * np.log10(env)
e01 = np.clip((edb + 45) / 37, 0, 1)
def lp(x, sec):
    a = 1 - math.exp(-1 / (FPS * sec)); y = np.zeros_like(x); s = 0
    for i, v in enumerate(x): s += a * (v - s); y[i] = s
    return y
NOD = np.clip(lp(e01, 0.09) - lp(e01, 0.55), 0, None)          # onsets / emphasis
NOD = lp(NOD, 0.06)
NOD /= max(NOD.max(), 1e-6)

# head shakes on each "no", tilt on the question
SHAKES = [w["s"] for w in TL["words"] if w["w"] == "no"]
QUESTION = next(w["s"] for w in TL["words"] if w["w"] == "ask") - 0.9

# ---------------------------------------------------------------- camera
def ease(u): return 0.5 - 0.5 * math.cos(math.pi * min(max(u, 0), 1))
def camera(t):
    for idx, (s, e, a, b) in enumerate(D.SHOTS):
        if s <= t < e: break
    u = ease((t - s) / (min(e, TL["total"]) - s))
    cx, cy, w = [a[j] + (b[j] - a[j]) * u for j in range(3)]
    punch = idx in (9, 10, 11)
    if punch:   # snap zoom into the beat + a short jolt
        k = math.exp(-(t - s) / 0.07)
        w *= 1 + 0.10 * k
        cx += w * 0.004 * k * math.sin((t - s) * 60); cy += w * 0.003 * k * math.cos((t - s) * 55)
    cx += w * 0.0022 * (math.sin(2 * math.pi * 0.21 * t + 1.3) + 0.6 * math.sin(2 * math.pi * 0.47 * t + 0.2))
    cy += w * 0.0018 * (math.sin(2 * math.pi * 0.17 * t + 2.1) + 0.5 * math.sin(2 * math.pi * 0.53 * t + 0.9))
    w = min(w, BGW); h = w * OH / OW
    cx = min(max(cx, w / 2), BGW - w / 2); cy = min(max(cy, h / 2), BGH - h / 2)
    return cx, cy, w, idx

# ---------------------------------------------------------------- performance (head/body motion)
TILTS = {}
def phrase_tilt(t):
    segs = TL["segs"]
    k = sum(1 for a, b in segs if a <= t)
    if k not in TILTS: TILTS[k] = random.Random(k * 13 + 1).uniform(-1.6, 1.6)
    return TILTS[k]
_tilt_s = [0.0]
def motion(i):
    """Head motion is rotation about the base of the neck (+ a small vertical settle), never a sideways
    slide, so the head always stays locked on the neck."""
    t = i / FPS
    th = 0.9 * math.sin(2 * math.pi * t / 5.3) + 0.4 * math.sin(2 * math.pi * t / 2.7 + 1.0)
    dx = 0.0
    dy = 1.5 * math.sin(2 * math.pi * t / 4.2)
    nod = NOD[i]
    dy += 10 * nod
    th += 1.3 * nod * (1 if int(t / 2.5) % 2 else -1)
    for s in SHAKES:                      # "no ..." -> quick disapproving head shake
        d = t - s
        if 0 <= d < 0.45: th += 2.2 * math.sin(2 * math.pi * 4.5 * d) * (1 - d / 0.45)
    dq = t - QUESTION
    if 0 < dq < 2.4: th += 3.0 * math.sin(math.pi * min(dq / 0.5, 1) / 2) * (1 if dq < 1.9 else (2.4 - dq) / 0.5)
    return th, dx, dy

SM_T = None
def smooth_tilt():
    global SM_T
    vals = np.array([phrase_tilt(i / FPS) for i in range(N)])
    SM_T = lp(lp(vals, 0.35), 0.35)

PIVOT = [NECK_X, 700]
def head_matrix(th, dx, dy):
    piv = tuple(PIVOT)
    M = cv2.getRotationMatrix2D(piv, th, 1.0)
    M[0, 2] += dx; M[1, 2] += dy
    return M

# ---------------------------------------------------------------- assets
ARMS = perf.arm_channels()
LEAN, FWD, BOUNCE = perf.torso_channels()

def load_assets():
    bg4 = cv2.imread("src/studio_x4.png")
    tm4 = cv2.imread("src/table_mask_x4.png", 0)
    lv = {4: (bg4, tm4)}
    lv[2] = (cv2.resize(bg4, None, fx=.5, fy=.5, interpolation=cv2.INTER_AREA), cv2.resize(tm4, None, fx=.5, fy=.5, interpolation=cv2.INTER_AREA))
    lv[1] = (cv2.resize(bg4, None, fx=.25, fy=.25, interpolation=cv2.INTER_AREA), cv2.resize(tm4, None, fx=.25, fy=.25, interpolation=cv2.INTER_AREA))
    return lv

YY, XX = np.mgrid[0:OH, 0:OW].astype(np.float32)
RR = np.sqrt(((XX - OW / 2) / (OW / 2)) ** 2 + ((YY - OH / 2) / (OH / 2)) ** 2)
VIGN = (1 - 0.30 * np.clip(RR / 1.35, 0, 1) ** 2.2)[..., None]

def render_frame(i, roy, lv):
    t = i / FPS
    cx, cy, w, shot = camera(t)
    z = OW / w; h = w * OH / OW
    ox, oy = cx - w / 2, cy - h / 2
    L = 1 if z <= 1.5 else (2 if z <= 3.0 else 4)
    bgL, tmL = lv[L]
    A = np.float32([[z / L, 0, -z * ox], [0, z / L, -z * oy]])
    interp = cv2.INTER_CUBIC if z / L > 1 else cv2.INTER_LINEAR
    bg = cv2.warpAffine(bgL, A, (OW, OH), flags=interp, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    tm = cv2.warpAffine(tmL, A, (OW, OH), flags=cv2.INTER_LINEAR).astype(np.float32)[..., None] / 255
    # depth of field on the set behind him
    sig = max(0.0, (z - 1.9)) * 0.85
    if sig > 0.3:
        small = cv2.resize(bg, (OW // 2, OH // 2), interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), sig / 2)
        bg = cv2.resize(small, (OW, OH), interpolation=cv2.INTER_LINEAR)
    # ---- character
    head = perf.head_at(t)
    vis = TL["track"][i]
    th, dx, dy = motion(i)
    th += SM_T[i]
    # head dips with the chops
    th += 2.0 * BOUNCE[i] * (1 if int(t / 3.1) % 2 else -1); dy += 14 * BOUNCE[i]
    hm = head_matrix(th, dx, dy)
    # torso: lean about the hips, lean in toward camera, bounce on beats, breathing
    hip = (NECK_X, 1390)
    breath = 1 + 0.005 * math.sin(2 * math.pi * t / 3.6)
    fwd = 1 + 0.05 * FWD[i]
    Tb = np.float64([[1, 0, 0], [0, 1, 10 * BOUNCE[i] + 18 * FWD[i]], [0, 0, 1]])
    Rl = np.vstack([cv2.getRotationMatrix2D(hip, LEAN[i] + 0.8 * math.sin(2 * math.pi * t / 6.3), fwd), [0, 0, 1]])
    Br = np.float64([[1, 0, 0], [0, breath, (1 - breath) * 1300], [0, 0, 1]])
    bm = (Tb @ Rl @ Br)[:2]
    arms = {k: tuple(ARMS[k][i]) for k in "RL"}
    char = roy.compose(head, vis, head_M=hm, body_M=bm, arms=arms)
    sc = z * K4
    Mw = np.float32([[sc, 0, z * (T0[0] - ox)], [0, sc, z * (T0[1] - oy)]])
    if sc < 0.7:
        f = min(1.0, sc * 1.5)
        char = cv2.resize(char, None, fx=f, fy=f, interpolation=cv2.INTER_AREA)
        Mw[:, :2] /= f
    ch = cv2.warpAffine(char, Mw, (OW, OH), flags=cv2.INTER_LINEAR)   # no overshoot -> no edge rings
    ca = np.clip(ch[..., 3:4], 0, 1)
    cc = np.clip(ch[..., :3], 0, 255 * ca)
    frame = cc + bg * (1 - ca)
    frame = bg * tm + frame * (1 - tm)          # table + mug in front of him
    # ---- grade
    f = frame / 255
    small = cv2.resize(f, (OW // 4, OH // 4), interpolation=cv2.INTER_AREA)
    bright = np.clip(small - 0.72, 0, None)
    bloom = cv2.resize(cv2.GaussianBlur(bright, (0, 0), 9), (OW, OH), interpolation=cv2.INTER_LINEAR)
    f = f + bloom * np.float32([0.45, 0.6, 0.8])
    f = np.clip((f - 0.5) * 1.05 + 0.5, 0, 1)
    f = f * VIGN
    fade = min(1.0, t / 0.4, (TL["total"] - t) / D.FADE_OUT)
    f *= max(0.0, fade)
    rngf = np.random.default_rng(i)
    grain = rngf.normal(0, 1.8 / 255, (OH, OW, 1)).astype(np.float32)
    f = f + grain
    return np.clip(f * 255 + 0.5, 0, 255).astype(np.uint8)

if __name__ == "__main__":
    mode = sys.argv[1]
    smooth_tilt()
    lv = load_assets(); roy = Rig2(); PIVOT[0] = roy.neck_x
    if mode == "still":
        for s in sys.argv[2:]:
            i = int(float(s) * FPS)
            cv2.imwrite(f"still_{s}.png", render_frame(i, roy, lv))
    elif mode == "chunk":
        a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{OW}x{OH}",
                              "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "14",
                              "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
        import time; t0 = time.time()
        for i in range(a, b):
            p.stdin.write(render_frame(i, roy, lv).tobytes())
            if (i - a) % 50 == 0: print(out, i, round(time.time() - t0, 1), flush=True)
        p.stdin.close(); p.wait()
    elif mode == "audio":
        import soundfile as sf
        sf.write("scene_audio.wav", AUDIO, ASR, subtype="PCM_24")

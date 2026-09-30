"""Draw the film, frame by frame, in either format (the portrait master is composed first; the landscape version
has its own shot windows and its own room, it is never a stretched portrait).

  python3 render.py still portrait 12.5 out.png          one frame
  python3 render.py chunk portrait 0 300 part.mp4        frames [0, 300) to an H.264 chunk (no audio)

Layers, back to front: the room (lens blur by shot) -> the master head -> the body (pose drawing, its forearms as
pieces on their elbows) -> light (soft key from above camera left, cool rim from camera right, the same in every
shot) -> gag graphics -> UNITED ROAD / SATIRE identifiers -> captions -> opening ID card; the last second is the end
card. Everything is placed in world units (the body frame of bodies.py) and seen through the shot's window."""
import json, math, os, subprocess, sys, numpy as np, cv2
from PIL import Image
import perf, graphics as GR
from face import Face

FPS = 30
SIZE = {"portrait": (1080, 1920), "landscape": (1920, 1080)}
# shot windows (world units): centre x, centre y, width. Portrait: eyes ~37-44 % down; landscape: him a little
# right of centre, so the gag cards have the empty left third
def _shot(w, eyes_at, aspect, cx=0.0):
    """window of width w (world units) with his eyes (world y -124.5) `eyes_at` of the way down the frame"""
    h = w * aspect
    top = -124.5 - eyes_at * h
    return (cx, top + h / 2, w)
SHOTS = {"portrait": {"A": _shot(296, 0.28, 16 / 9), "B": _shot(219, 0.30, 16 / 9), "C": _shot(179, 0.33, 16 / 9),
                      "C2": _shot(160, 0.35, 16 / 9)},
         "landscape": {"A": _shot(782, 0.32, 9 / 16, -47.0), "B": _shot(587, 0.33, 9 / 16, -35.0),
                       "C": _shot(444, 0.35, 9 / 16, -20.0), "C2": _shot(400, 0.36, 9 / 16, -15.0)}}
BLUR = {"A": 2.2, "B": 3.2, "C": 4.5, "C2": 5.0}      # lens blur of the room, px per 1080 px of frame width/height
# portrait is composed on its own: a raised hand drawn far out to the side is brought in from its elbow so the
# gesture happens inside the narrow frame (degrees, + = clockwise on screen)
ARM_FRAME = {"portrait": {("g08", "R"): 30.0, ("g02", "R"): 26.0, ("g02", "L"): -26.0,
                          ("g01", "R"): 9.0, ("g01", "L"): -9.0}, "landscape": {}}
BURN_CAPTIONS = False    # the dialogue is not subtitled in the picture (the .srt / .vtt ship alongside)
WS = 8
LEVELS = (1.0, 0.75, 0.5, 0.375, 0.25, 0.1875, 0.125)

def premul(rgba):
    a = rgba[..., 3:4].astype(np.float32) / 255
    out = rgba.astype(np.float32)
    out[..., :3] *= a
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)

class Sprite:
    """an RGBA image (stored premultiplied) with its px -> world transform, and cached smaller copies"""
    def __init__(self, img, T):
        self.lv = {1.0: premul(img)}
        self.T = np.asarray(T, np.float64)
    def level(self, L):
        if L not in self.lv:
            b = self.lv[1.0]
            self.lv[L] = cv2.resize(b, (max(1, int(round(b.shape[1] * L))), max(1, int(round(b.shape[0] * L)))),
                                    interpolation=cv2.INTER_AREA)
        return self.lv[L]

def pick(e, target=0.9):
    """the stored size to warp from: screen scale about `target` of it, never enlarging it more than 1.25x"""
    ok = [L for L in LEVELS if e / L <= 1.25]
    if not ok: return 1.0
    return min(ok, key=lambda L: abs(math.log((e / L) / target)))

def draw(canvas, spr, M):
    """premultiplied over: sprite with px->screen affine M (3x3) onto canvas (H, W, 4) float32"""
    H, W = canvas.shape[:2]
    e = math.sqrt(abs(np.linalg.det(M[:2, :2])))
    L = pick(e)
    img = spr.level(L)
    Ml = M @ np.diag([1 / L, 1 / L, 1.0])
    h, w = img.shape[:2]
    pts = Ml @ np.array([[0, w, 0, w], [0, 0, h, h], [1, 1, 1, 1]], np.float64)
    x0, y0 = max(0, int(math.floor(pts[0].min())) - 2), max(0, int(math.floor(pts[1].min())) - 2)
    x1, y1 = min(W, int(math.ceil(pts[0].max())) + 2), min(H, int(math.ceil(pts[1].max())) + 2)
    if x1 <= x0 or y1 <= y0: return
    Ms = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]], np.float64) @ Ml
    out = cv2.warpAffine(img, Ms[:2], (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    src = out.astype(np.float32)
    dst = canvas[y0:y1, x0:x1]
    dst *= (1 - src[..., 3:4] / 255)
    dst += src

def T_trs(tx=0.0, ty=0.0, s=1.0, rot=0.0, cx=0.0, cy=0.0):
    """rotate by rot degrees and scale by s about (cx, cy), then translate"""
    c, sn = math.cos(math.radians(rot)) * s, math.sin(math.radians(rot)) * s
    return np.array([[c, -sn, cx - c * cx + sn * cy + tx], [sn, c, cy - sn * cx - c * cy + ty], [0, 0, 1]])

class Rig:
    def __init__(self):
        self.face = Face()
        hp = np.float64(json.load(open("build/rig/head_place.json"))["main_to_world"])
        k = self.face.meta["k"]; off = self.face.off
        self.head_T = np.vstack([hp, [0, 0, 1]]) @ np.array([[1 / k, 0, off[0]], [0, 1 / k, off[1]], [0, 0, 1]])
        self.neck = np.vstack([hp, [0, 0, 1]]) @ np.array([440.0, 392.0, 1.0])     # head pivot (world)
        B = json.load(open("build/rig/bodies.json"))
        A = json.load(open("build/rig/arms.json"))
        self.arms = A
        self.bodies = {}
        px2w = lambda o: np.array([[1 / WS, 0, o[0]], [0, 1 / WS, o[1]], [0, 0, 1]])
        for n, p in B["poses"].items():
            f = f"build/rig/{n}_base.png" if n in A else f"build/rig/body_{n}.png"
            self.bodies[n] = Sprite(np.asarray(Image.open(f)), px2w(p["origin"]))
        self.pieces = {}
        for n, sides in A.items():
            for s, info in sides.items():
                img = np.asarray(Image.open(f"build/rig/{n}_{s}.png"))
                self.pieces[(n, s)] = (Sprite(img, px2w(info["origin"])), info)
        # the mirrored resting forearm (his right hand resting, for l1)
        if ("g03", "L") in self.pieces:
            spr, info = self.pieces[("g03", "L")]
            img = np.asarray(Image.open("build/rig/g03_L.png"))[:, ::-1].copy()
            ox, oy = info["origin"]; w = info["size"][0] / WS
            ex, ey = info["elbow"]; wx, wy = info["wrist"]
            mo = [-(ox + w), oy]
            self.pieces[("g03m", "R")] = (Sprite(img, px2w(mo)), {"origin": mo, "elbow": [-ex, ey], "wrist": [-wx, wy]})
        # body bottom (world y) per pose, for the lean / breathing pivot
        self.combos = {"r1": ("g01", [("g01", "R", None), ("g03", "L", "L")]),
                       "l1": ("g01", [("g03m", "R", "R"), ("g01", "L", None)])}

    def pose_parts(self, pose):
        """-> base body key, [(piece key, side, attach side or None)]"""
        if pose in self.combos: return self.combos[pose]
        if pose in self.arms: return pose, [(pose, s, None) for s in self.arms[pose]]
        return pose, []

def piece_T(info, rot, attach=None, wrist_d=(0.0, 0.0)):
    """piece px -> world: its own place, moved so its elbow sits on `attach` (world) if given, turned `rot` deg
    about the elbow; wrist_d moves the wrist (a similarity about the elbow: taps)"""
    ex, ey = info["elbow"]
    T = np.array([[1 / WS, 0, info["origin"][0]], [0, 1 / WS, info["origin"][1]], [0, 0, 1]])
    if attach is not None:
        T = T_trs(attach[0] - ex, attach[1] - ey) @ T
        ex, ey = attach
    if wrist_d[0] or wrist_d[1]:
        wx, wy = info["wrist"]
        if attach is not None: wx, wy = wx + (attach[0] - info["elbow"][0]), wy + (attach[1] - info["elbow"][1])
        v = np.array([wx - ex, wy - ey]); v2 = v + np.array(wrist_d)
        s = np.linalg.norm(v2) / max(np.linalg.norm(v), 1e-6)
        a = math.degrees(math.atan2(v2[1], v2[0]) - math.atan2(v[1], v[0]))
        T = T_trs(s=s, rot=a, cx=ex, cy=ey) @ T
    if rot:
        T = T_trs(rot=rot, cx=ex, cy=ey) @ T
    return T

_RIG = None
def rig():
    global _RIG
    if _RIG is None: _RIG = Rig()
    return _RIG

_SET = {}
def set_plate(orient):
    if orient not in _SET:
        meta = json.load(open("build/set.json"))
        img = np.ascontiguousarray(cv2.imread(f"build/set_{orient}.png")[..., ::-1])
        x0, y0, x1, y1 = meta[orient]["rect"]; px = meta[orient]["px"]
        _SET[orient] = (img, np.array([[1 / px, 0, x0], [0, 1 / px, y0], [0, 0, 1]], np.float64))
    return _SET[orient]

def cam_window(orient, cam):
    a, b, u = cam
    A = SHOTS[orient][a]; B = SHOTS[orient][b]
    return tuple(A[i] + (B[i] - A[i]) * u for i in range(3)), (a if u < 0.5 else b)

def world_to_screen(orient, win):
    W, H = SIZE[orient]
    cx, cy, w = win
    h = w * H / W
    s = W / w
    return np.array([[s, 0, -(cx - w / 2) * s], [0, s, -(cy - h / 2) * s], [0, 0, 1]], np.float64)

_CAPS = None
def captions():
    global _CAPS
    if _CAPS is None: _CAPS = json.load(open("build/captions.json"))
    return _CAPS

def frame(i, orient):
    W, H = SIZE[orient]
    t = i / FPS
    card_t = perf.TL["marks"]["card"]
    if t >= card_t:
        return np.asarray(GR.end_card(W, H).convert("RGB"))
    st = perf.state(t)
    R = rig()
    win, shot = cam_window(orient, st["cam"])
    S = world_to_screen(orient, win)
    pxu = S[0, 0]
    # ---- the room
    plate, Tp = set_plate(orient)
    Mb = S @ Tp
    bg = cv2.warpAffine(plate, Mb[:2], (W, H), flags=cv2.INTER_LINEAR if Mb[0, 0] > 0.8 else cv2.INTER_AREA,
                        borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    sig = BLUR[shot] * H / 1080 if orient == "landscape" else BLUR[shot] * W / 1080 * 1.0
    bg = cv2.GaussianBlur(bg, (0, 0), sig)
    # ---- the character (premultiplied RGBA canvas)
    ch = np.zeros((H, W, 4), np.float32)
    body_y = 210.0
    lean = st["lean"]
    C = T_trs(0, st["body_dy"]) @ T_trs(s=1 + 0.035 * lean, cx=0, cy=body_y)
    Cb = C @ np.array([[1, 0, 0], [0, 1 + 0.0012 * st["breath"], -body_y * 0.0012 * st["breath"]], [0, 0, 1]])
    # settle after a pose change: the new pose eases in over 6 frames
    since = st["pose_since"]
    u = min(1.0, since / (6 / FPS))
    settle = (1 - u) ** 2
    # head: behind the body
    face_st = dict(st["face"]); face_st["vis"] = VIS[i] if i < len(VIS) else "REST"
    hd = T_trs(st["head_dx"], st["head_dy"] + 1.2 * lean + 0.6 * settle, rot=st["tilt"], cx=R.neck[0], cy=R.neck[1])
    Mh = S @ C @ hd @ R.head_T
    e = math.sqrt(abs(np.linalg.det(Mh[:2, :2])))
    hl = min((1.0, 0.75, 0.5, 0.375, 0.25), key=lambda L: abs(math.log(max(e / L, 1e-6) / 0.9)) if e / L <= 1.2 else 9)
    head = R.face.render(face_st, hl)
    hs = Sprite(np.clip(head, 0, 255).astype(np.uint8), np.diag([1 / hl, 1 / hl, 1.0]))
    draw(ch, hs, Mh @ np.diag([1 / hl, 1 / hl, 1.0]))
    # body + forearm pieces
    base, pieces = R.pose_parts(st["pose"])
    bump = T_trs(0, 1.2 * settle, s=1 - 0.004 * settle, cx=0, cy=body_y)
    draw(ch, R.bodies[base], S @ Cb @ bump @ R.bodies[base].T)
    arms = st["arms"]
    for key, side, attach_side in pieces:
        spr, info = R.pieces[(key, side)]
        attach = R.arms[base][attach_side]["elbow"] if attach_side else None
        rot, wrist, dx, dy = arms.get(side, (0.0, 0.0, 0.0, 0.0))
        rot += ARM_FRAME[orient].get((key, side), 0.0)
        rot = rot + (8.0 if side == "R" else -8.0) * settle - 1.5 * math.sin(math.pi * u) * (1 - u) * (1 if side == "R" else -1)
        if key == "g05": dx += st["tap_rest"] if not arms.get(side) else 0.0
        Tpc = piece_T(info, rot, attach, (dx, dy))
        draw(ch, spr, S @ Cb @ bump @ Tpc)
    # ---- light: soft key from above camera left, cool rim from camera right
    a = ch[..., 3] / 255
    if a.max() > 0:
        yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]; xx = np.linspace(0, 1, W, dtype=np.float32)[None, :]
        key = 1.035 - 0.07 * (0.55 * xx + 0.45 * yy)
        ch[..., :3] *= key[..., None]
        k = max(2, int(round(3.2 * pxu / 3.65)))
        sh = np.zeros_like(a); sh[:, :-k] = a[:, k:]
        rim = np.clip(a - sh, 0, 1)
        rim = cv2.GaussianBlur(rim, (0, 0), max(0.8, k * 0.45)) * a
        ch[..., :3] += rim[..., None] * np.float32([150, 185, 245]) * 0.42
    out = bg * (1 - ch[..., 3:4] / 255) + ch[..., :3]
    # a gentle vignette
    yy = np.linspace(-1, 1, H, dtype=np.float32)[:, None]; xx = np.linspace(-1, 1, W, dtype=np.float32)[None, :]
    out *= (1 - 0.16 * np.clip((xx ** 2 + yy ** 2) - 0.35, 0, 1))[..., None]
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")
    # ---- graphics
    for name, age, left in st["gfx"]:
        bt = ()
        if name == "lpf":
            bt = (0.0, perf.W(12, "principles") - perf.W(12, "law", 2), perf.W(12, "facts") - perf.W(12, "law", 2))
        gshot = gag_shot(name, orient)
        img.alpha_composite(GR.gag_layer(W, H, name, age, left, gshot, bt))
    img.alpha_composite(GR.identifiers(W, H))
    if BURN_CAPTIONS:
        for c in captions():
            if c["show"] <= t < c["hide"]:
                img.alpha_composite(GR.caption(W, H, c["text"]))
                break
    if t < 3.4:
        a_id = GR.smooth((t - 0.15) / 0.3) * (1 - GR.smooth((t - 2.9) / 0.5))
        if a_id > 0:
            idc = np.asarray(GR.id_card(W, H)).astype(np.float32); idc[..., 3] *= a_id
            img.alpha_composite(Image.fromarray(idc.astype(np.uint8)))
    return np.asarray(img.convert("RGB"))

_GAGSHOT = {}
def gag_shot(name, orient):
    """the shot a gag card appears in decides where it goes (portrait: over the head in A, on the chest in B/C)"""
    if name not in _GAGSHOT:
        t0 = min(a for a, b, n in perf.GFX if n == name)
        _GAGSHOT[name] = cam_window(orient, perf.camera_at(t0 + 0.05))[1]
    s = _GAGSHOT[name]
    return "A" if s == "A" else "B"

VIS = json.load(open("build/visemes.json"))["track"] if os.path.exists("build/visemes.json") else []

def chunk(orient, f0, f1, out):
    W, H = SIZE[orient]
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16",
                          "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(f0, f1):
        p.stdin.write(frame(i, orient).tobytes())
        if (i - f0) % 150 == 0: print(f"{orient} frame {i}", flush=True)
    p.stdin.close(); p.wait()

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "still":
        orient, t, out = sys.argv[2], float(sys.argv[3]), sys.argv[4]
        Image.fromarray(frame(int(round(t * FPS)), orient)).save(out)
    elif cmd == "chunk":
        chunk(sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5])

"""Render the film.
  python3 render.py still T [T ...]      -> build/stills/still_<T>.jpg   (1080x1920)
  python3 render.py chunk A B out.mp4    -> frames [A, B)  (x264 CRF 16, no audio; the original audio is muxed afterwards)
Per frame: find the shot, evaluate its camera, build the setup (plate + actors + props), then the grade."""
import os, sys, math, subprocess, numpy as np, cv2
os.environ.setdefault("EP_RES", "1080x1920")
import engine as E
import perf, cast, stage
from stage import Actor, Stage, body_matrix
from render_util import *

FPS, OW, OH, RS = 30, E.OW, E.OH, E.RS
DUR = perf.DUR
NFR = int(round(DUR * FPS))


# ================================================================ STUDIO
EXT = 160
DESK = [(422, 525), (485, 504), (601, 483), (675, 469), (748, 462), (901, 452), (1012, 450), (1170, 447), (1275, 449), (1322, 460),
        (1334, 480), (1312, 506), (1275, 646), (1248, 650), (900, 700), (560, 700), (485, 684), (459, 561)]
DESK = [(x, y + EXT) for x, y in DESK]
SEAT, SCALE = STUDIO_SEAT, STUDIO_SCALE

STUDIO_DEFAULT = dict(gary="gy_b_q34L", rooney="wr_b_front", micah="mr_b_front|f")


def studio_actors(t):
    acts = []
    for ch in ("gary", "rooney", "micah"):
        name, flip = pose_of(ch, t, STUDIO_DEFAULT[ch])
        x, y = SEAT[ch]
        talks = ch in perf.SPEAKERS
        acts.append(bust(ch, name, x, y, SCALE[ch], t, flip=flip, z={"gary": 1, "rooney": 2, "micah": 1}[ch], talks=talks))
    return acts


def studio_props(t):
    """the last gag: a tiny 50 balloon drifts up behind Micah for a fraction of a second"""
    out = []
    t0 = perf.BALLOON_T0
    if t0 <= t < t0 + 0.8:
        k = (t - t0) / 0.8
        x, y = SEAT["micah"]
        a = Actor("fr_balloons", x + 92 - 14 * k + 8 * math.sin(k * 5), y - 240 - 230 * k, 0.55, anchor="base", z=0.5)
        out.append((a, None, body_matrix(a.anchor, lean=6 * math.sin(k * 7)), 1.0))
    return out


def render_studio(s, t, cam):
    st = plate("studio", occluders=[DESK])
    return st.render(cam, studio_props(t) + studio_actors(t), dof=s.get("dof", 0.0), occ_dof=s.get("dof", 0.0) * 0.6)


# ================================================================ shots -> frames
import direction as D

SETUPS = {"studio": render_studio}
for _name in getattr(D, "EXTRA_SETUPS", {}):
    SETUPS[_name] = D.EXTRA_SETUPS[_name]


def shot_at(t):
    cur = D.SHOTS[0]
    for s in D.SHOTS:
        if t >= s["t0"] - 1e-6: cur = s
        else: break
    return cur


def grade(fr, s, t):
    """vignette + a little grain; the restaurant (flashback) is warmer and punchier than the studio"""
    h, w = fr.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.sqrt(((xx - w / 2) / (w * 0.62)) ** 2 + ((yy - h / 2) / (h * 0.62)) ** 2)
    v = 1 - 0.16 * np.clip(r - 0.55, 0, 1) ** 1.5
    fr = fr * v[..., None]
    if s.get("warm"):
        fr = fr * np.float32([1.03, 1.0, 0.95]) + 0.0
        fr = np.clip((fr - 0.5) * 1.06 + 0.5, 0, 1)
    rng = np.random.default_rng(int(t * FPS) + 1234)
    fr = fr + (rng.standard_normal((h, w, 1)).astype(np.float32) * 0.012)
    return np.clip(fr, 0, 1)


def render_frame(t):
    if t >= DUR - 0.10: return np.zeros((OH, OW, 3), np.float32)       # cut to black on the last frames
    s = shot_at(t)
    cam = camera(s, t)
    fr = SETUPS[s["setup"]](s, t, cam)
    fr = grade(fr, s, t)
    if os.environ.get("GRID"): fr = grid_overlay(fr, cam)
    return fr


def grid_overlay(fr, cam, step=100):
    """plate-coordinate grid (1x plate px) over the frame, for placing things"""
    cx, cy, w = cam
    k = OW / w
    ox, oy = cx - w / 2, cy - w * OH / OW / 2
    im = np.ascontiguousarray((np.clip(fr, 0, 1) * 255).astype(np.uint8))
    for x in range(int(ox // step) * step, int(ox + w) + step, step):
        X = int((x - ox) * k); cv2.line(im, (X, 0), (X, OH), (255, 0, 255), 1); cv2.putText(im, str(x), (X + 3, 18), 0, 0.55, (255, 255, 0), 1)
    for y in range(int(oy // step) * step, int(oy + w * OH / OW) + step, step):
        Y = int((y - oy) * k); cv2.line(im, (0, Y), (OW, Y), (255, 0, 255), 1); cv2.putText(im, str(y), (3, Y - 3), 0, 0.55, (255, 255, 0), 1)
    return im.astype(np.float32) / 255


def to_u8(fr):
    return (np.clip(fr, 0, 1) * 255 + 0.5).astype(np.uint8)


def stills(times):
    os.makedirs("build/stills", exist_ok=True)
    for t in times:
        fr = render_frame(t)
        cv2.imwrite(f"build/stills/still_{t:06.2f}.jpg", cv2.cvtColor(to_u8(fr), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
        print("still", t, "shot", shot_at(t).get("name"), flush=True)


def chunk(a, b, out):
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "16", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(a, b):
        p.stdin.write(to_u8(render_frame(i / FPS)).tobytes())
        if (i - a) % 30 == 0: print("frame", i, flush=True)
    p.stdin.close(); p.wait()


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "still": stills([float(x) for x in sys.argv[2:]])
    elif mode == "chunk": chunk(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])

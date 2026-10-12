"""Every animated eye, close up, in the states the film puts it through: at rest, looking left / right / up / down,
half shut -> build/eyes_<n>.jpg (one row per eye of every drawing that is on screen with a face). Look at every tile:
one round pupil, nothing dark left in the corners or along the lids, the white clean.
    FILM_EPISODE=the-undercard PYTHONPATH=episodes/the-undercard:. python3 episodes/the-undercard/tools/eyesheet.py [CHARACTER ...]"""
import sys

import cv2
import numpy as np
import yaml

from studio.film import ep
from studio.film.cast import CAST
from studio.paths import CHARACTERS

import film.actors  # noqa: F401  (installs the drawn mouths and the clean pupils)
import film.direction as D

STATES = [("rest", dict()), ("L", dict(lookx=-1.0)), ("R", dict(lookx=1.0)), ("up", dict(looky=-0.8)),
          ("down", dict(looky=0.8)), ("UL", dict(lookx=-1.0, looky=-0.6)), ("DR", dict(lookx=1.0, looky=0.7)),
          ("half", dict(blink=0.5))]
T = 150


def frame(d, st):
    img = d.u8[1.0].astype(np.float32) / 255.0
    img[..., :3] *= img[..., 3:4]
    p = d.patch(1.0, st)
    if p is not None:
        x0, y0, pm = p
        h, w = pm.shape[:2]
        img[y0:y0 + h, x0:x0 + w] = pm + img[y0:y0 + h, x0:x0 + w] * (1 - pm[..., 3:4])
    return img


def rows(key):
    d, info = CAST.get(key)
    out = []
    for k, e in enumerate(d.spec["eyes"] or []):
        (cx, cy) = d.P(e[0], e[1])
        r = 2.6 * max(e[2], e[3], 4) * d.S
        tiles = []
        for name, st in STATES:
            s = dict(vis="REST", amp=1.0, blink=0.0, lookx=0.0, looky=0.0, brow=0.0, smile=0.0)
            s.update(st)
            img = frame(d, s)
            H, W = img.shape[:2]
            a, b = int(max(0, cx - r)), int(min(W, cx + r))
            c, f = int(max(0, cy - r)), int(min(H, cy + r))
            crop = img[c:f, a:b]
            comp = crop[..., :3] + np.float32([0.78, 0.0, 0.78]) * (1 - crop[..., 3:4])
            t = cv2.resize(comp, (T, T), interpolation=cv2.INTER_CUBIC)
            t = (np.clip(t, 0, 1) * 255).astype(np.uint8)
            cv2.putText(t, name, (3, 13), 0, 0.4, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(t, name, (3, 13), 0, 0.4, (0, 255, 255), 1, cv2.LINE_AA)
            tiles.append(t)
        lab = np.zeros((T, 170, 3), np.uint8)
        cv2.putText(lab, key.split(":")[0][:10], (4, T // 2 - 10), 0, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(lab, f"{key.split(':')[1]} eye{k}", (4, T // 2 + 12), 0, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        out.append(np.hstack([lab] + tiles))
    return out


def main():
    only = set(sys.argv[1:])
    keys = sorted(k for k in D.DRAW.values() if not only or k.split(":")[0] in only)
    allrows = []
    for key in keys:
        cid, n = key.split(":")
        sp = yaml.safe_load((CHARACTERS / cid / "film.yaml").read_text())["drawings"][n]
        if sp.get("plain"):
            continue
        d, _ = CAST.get(key)
        if not d.has_face or not d.spec.get("eyes"):
            continue
        allrows += rows(key)
    for i in range(0, len(allrows), 12):
        p = ep.path(f"eyes_{i // 12}.jpg")
        cv2.imwrite(str(p), np.ascontiguousarray(np.vstack(allrows[i:i + 12])[..., ::-1]), [cv2.IMWRITE_JPEG_QUALITY, 90])
        print(p)
    print(len(allrows), "eyes")


if __name__ == "__main__":
    main()

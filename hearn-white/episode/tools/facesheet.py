"""Every face the film animates, in the states it is animated through: at rest, the open shapes (AI, E, O), a closed
M/B/P, a full blink, and the eyes looking left and right -> build/faces_<character>.jpg (one row per drawing).
Look at every row: the mouth must open on the drawn mouth, the lids must cover the whole eye, the pupils must stay
round and inside the eye.
    FILM_EPISODE=the-undercard PYTHONPATH=episodes/the-undercard:. python3 episodes/the-undercard/tools/facesheet.py [CHARACTER ...] [--only drawing,...]"""
import sys

import cv2
import numpy as np
import yaml

from studio.film import ep
from studio.film.cast import CAST
from studio.paths import CHARACTERS

import film.actors  # noqa: F401  (installs the drawn mouths)

STATES = [("rest", dict()), ("AI", dict(vis="AI", amp=1.15)), ("E", dict(vis="E", amp=1.1)),
          ("O", dict(vis="O", amp=1.1)), ("MBP", dict(vis="MBP")), ("blink", dict(blink=1.0)),
          ("half", dict(blink=0.5)), ("look L", dict(lookx=-1.0)), ("look R", dict(lookx=1.0)),
          ("look up", dict(looky=-0.6))]
T = int(__import__("os").environ.get("FACE_T", 200))


def frame(d, st):
    img = d.u8[1.0].astype(np.float32) / 255.0
    img[..., :3] *= img[..., 3:4]
    p = d.patch(1.0, st)
    if p is not None:
        x0, y0, pm = p
        h, w = pm.shape[:2]
        img[y0:y0 + h, x0:x0 + w] = pm + img[y0:y0 + h, x0:x0 + w] * (1 - pm[..., 3:4])
    return img


def row(key):
    d, info = CAST.get(key)
    hx0, hy0, hx1, hy1 = d.spec["head"]
    (X0, Y0), (X1, Y1) = d.P(hx0, hy0), d.P(hx1, hy1)
    cx, cy = (X0 + X1) / 2, (Y0 + Y1) / 2 + 0.08 * (Y1 - Y0)
    r = 0.6 * max(X1 - X0, Y1 - Y0)
    tiles = []
    for name, st in STATES:
        s = dict(vis="REST", amp=1.0, blink=0.0, lookx=0.0, looky=0.0, brow=0.0, smile=0.0)
        s.update(st)
        img = frame(d, s)
        H, W = img.shape[:2]
        a, b = int(max(0, cx - r)), int(min(W, cx + r))
        c, e = int(max(0, cy - r)), int(min(H, cy + r))
        crop = img[c:e, a:b]
        bg = np.float32([0.78, 0.0, 0.78])
        comp = crop[..., :3] + bg * (1 - crop[..., 3:4])
        t = cv2.resize(comp, (T, T), interpolation=cv2.INTER_AREA)
        t = (np.clip(t, 0, 1) * 255).astype(np.uint8)
        cv2.putText(t, name, (4, 14), 0, 0.42, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(t, name, (4, 14), 0, 0.42, (255, 255, 0), 1, cv2.LINE_AA)
        tiles.append(t)
    lab = np.zeros((T, 150, 3), np.uint8)
    cv2.putText(lab, key.split(":")[1], (4, T // 2), 0, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
    return np.hstack([lab] + tiles)


def main():
    args = sys.argv[1:]
    only = None
    if "--only" in args:
        i = args.index("--only")
        only = set(args[i + 1].split(","))
        args = args[:i] + args[i + 2:]
    cids = args or ["eddie-hearn", "dana-white", "tyson-fury", "anthony-joshua", "ring-announcer", "boxing-referee",
                    "laundry-attendant", "security-guard"]
    for cid in cids:
        spec = yaml.safe_load((CHARACTERS / cid / "film.yaml").read_text())["drawings"]
        rows = []
        for n, sp in spec.items():
            if sp.get("plain") or (only and n not in only):
                continue
            d, _ = CAST.get(f"{cid}:{n}")
            if not (d.spec.get("mouth") or d.spec.get("eyes")):
                continue
            rows.append(row(f"{cid}:{n}"))
        if rows:
            out = ep.path(f"faces_{cid}.jpg")
            cv2.imwrite(str(out), np.vstack(rows)[..., ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
            print(out, len(rows))


if __name__ == "__main__":
    main()

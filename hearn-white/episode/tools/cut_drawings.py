"""Every drawing The Undercard films, as its own clean cut-out: the pack's sheets are packed tight, so a drawing's
box also holds slivers of its neighbours (a hand, a shoe, a foot from the row below) and the sheets carry motion
accents (puffs, speed lines). For each drawing in a character's film.yaml that cuts from a sheet, this keeps the
figure (its largest piece, plus any piece of it that is inside the box and at least 1 % of its size) and drops
everything else, then writes reference/cuts/<sheet>/<drawing>.png and points film.yaml at it, moving any hand-set
marks / head box into the cut's coordinates.
    python3 episodes/the-undercard/tools/cut_drawings.py CHARACTER ...   (then python3 -m studio.film.art CHARACTER --force)"""
import re
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml
from PIL import Image

from studio.paths import CHARACTERS

KEEP_FRAC = 0.01        # a separate piece inside the box is kept if it is at least this share of the figure
PAD = 6


def cut(sheet, box):
    im = np.array(Image.open(sheet).convert("RGBA"))
    x0, y0, x1, y1 = box
    c = im[y0:y1, x0:x1].copy()
    a = c[..., 3]
    m = (a > 40).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        return c, (x0, y0)
    main = 1 + int(np.argmax(st[1:, 4]))
    H, W = m.shape
    keep = np.zeros(n, bool)
    keep[main] = True
    for i in range(1, n):
        if i == main:
            continue
        x, y, w, h, ar = st[i]
        touches = x <= 0 or y <= 0 or x + w >= W or y + h >= H
        if not touches and ar >= KEEP_FRAC * st[main, 4]:
            keep[i] = True
    km = keep[lab]
    km = cv2.dilate(km.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    c[..., 3] = np.where(km, a, 0)
    ys, xs = np.nonzero(c[..., 3] > 0)
    bx0, by0 = max(0, xs.min() - PAD), max(0, ys.min() - PAD)
    bx1, by1 = min(W, xs.max() + PAD + 1), min(H, ys.max() + PAD + 1)
    return c[by0:by1, bx0:bx1], (x0 + bx0, y0 + by0)


def shift_marks(mk, ox, oy):
    out = {}
    for k, v in mk.items():
        if k == "eyes":
            out[k] = [[e[0] - ox, e[1] - oy] + list(e[2:]) for e in v]
        elif k == "mouth":
            out[k] = [v[0] - ox, v[1] - oy, v[2] - ox, v[3] - oy, v[4] - ox, v[5] - oy]
        elif k == "chin":
            out[k] = v - oy if not isinstance(v, list) else [v[0] - ox, v[1] - oy]
        elif k == "neck":
            out[k] = [v[0] - ox, v[1] - oy]
        elif k == "head":
            out[k] = [v[0] - ox, v[1] - oy, v[2] - ox, v[3] - oy]
        else:
            out[k] = v
    return out


def main(cids):
    for cid in cids:
        d = CHARACTERS / cid
        f = d / "film.yaml"
        spec = yaml.safe_load(f.read_text())
        lines = f.read_text().splitlines()
        out = []
        for ln in lines:
            m = re.match(r"^  (\w+): (\{.*\})$", ln)
            if not m:
                out.append(ln)
                continue
            name = m.group(1)
            sp = spec["drawings"][name]
            src = sp.get("sheet", "")
            if "/cuts/" in src or "box" not in sp:
                out.append(ln)
                continue
            stem = Path(src).stem.replace("-clean", "")
            rgba, (ox, oy) = cut(d / src, sp["box"])
            dst = d / "reference" / "cuts" / stem / f"{name}.png"
            dst.parent.mkdir(parents=True, exist_ok=True)
            Image.fromarray(rgba).save(dst, optimize=True)
            sp = dict(sp)
            sp["sheet"] = f"reference/cuts/{stem}/{name}.png"
            sp["box"] = [0, 0, rgba.shape[1], rgba.shape[0]]
            for k in ("marks",):
                if k in sp:
                    sp[k] = shift_marks(sp[k], ox, oy)
            if "head" in sp:
                h = sp["head"]
                sp["head"] = [h[0] - ox, h[1] - oy, h[2] - ox, h[3] - oy]
            sp["from"] = f"{stem}.png {list(map(int, (ox, oy, ox + rgba.shape[1], oy + rgba.shape[0])))}"
            out.append(f"  {name}: " + yaml.safe_dump(sp, default_flow_style=True, width=1000, sort_keys=False).strip())
        f.write_text("\n".join(out) + "\n")
        yaml.safe_load(f.read_text())
        print(cid, "ok")


if __name__ == "__main__":
    main(sys.argv[1:])

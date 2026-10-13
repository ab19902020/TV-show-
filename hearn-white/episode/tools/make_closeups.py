"""The close-up drawings: an acting head (bust_*) on its character's own body, so a close-up shows the shoulders,
chest and arms of a whole person rather than a head on a sliver of collar.

For each close-up: the body drawing (a full figure, e.g. "front") is scaled up until its head (crown to chin) is
the size of the acting head's, the body's own head is taken off above the chin, and the acting head is set on in
its place (its chin on the body's chin, centred on the body's neck), its own collar fading into the body's
clothes. The result is a full figure (it stands on its feet like any other drawing) written to
library/characters/<id>/reference/cuts/closeups/close_<head>_<body>.png, with its face marks (from the acting
head) and its size against the casual sheet (close_fac) in film.yaml.

    FILM_EPISODE=the-undercard PYTHONPATH=. python3 episodes/the-undercard/tools/make_closeups.py
then build the drawings: python3 -m studio.film.art <character> close_..."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import yaml

from studio.paths import BUILD, CHARACTERS

CLOSE = {
    "eddie-hearn": [("smug", "front"), ("glare", "front"), ("up", "front"), ("sweat", "front")],
    "dana-white": [("smug", "front"), ("side", "q34"), ("blush", "front"), ("panic", "front")],
}
# (Fury's and Joshua's acting heads are drawn with their hoodies' full shoulders: their close-ups use them as they are)


OUT_K = 0.6                                       # the close-ups kept at 0.6 of the busts' resolution (the head ~1000 px)


def load(cid, name):
    b = BUILD / "film" / cid
    im = cv2.imread(str(b / f"{name}.png"), cv2.IMREAD_UNCHANGED)
    meta = json.loads((b / "meta.json").read_text())[name]
    mk = json.loads((b / "marks.json").read_text())[name]
    return im, meta, mk


def make(cid, head, body):
    bim, bmeta, bmk = load(cid, f"bust_{head}")
    fim, fmeta, fmk = load(cid, body)
    bS, (box, boy) = bmeta["scale"], bmeta["off"]
    fS, (fox, foy) = fmeta["scale"], fmeta["off"]
    B = lambda x, y: ((x - box) * bS, (y - boy) * bS)            # bust sheet px -> bust image px
    F = lambda x, y: ((x - fox) * fS, (y - foy) * fS)            # body sheet px -> body image px
    # scale: crown to chin
    bh = (bmk["chin"] - bmk["head"][1]) * bS
    fh = (fmk["chin"] - fmk["head"][1]) * fS
    g = bh / fh
    fim = cv2.resize(fim, None, fx=g, fy=g, interpolation=cv2.INTER_CUBIC)
    fchin = np.float64(F(fmk["neck"][0], fmk["chin"])) * g
    bchin = np.float64(B(bmk["neck"][0], bmk["chin"]))
    # the body's own head off: the oval of its head (crown to chin, ear to ear) and its neck down to the collar,
    # never the shoulders round it
    hx0, hy0, hx1, hy1 = fmk["head"]
    (x0, y0), (x1, _) = F(hx0, hy0), F(hx1, hy1)
    x0, x1, y0 = x0 * g, x1 * g, y0 * g
    cx, cy = (x0 + x1) / 2, (y0 + fchin[1]) / 2
    rx, ry = 0.64 * (x1 - x0), 0.60 * (fchin[1] - y0)
    neck_y = np.float64(F(0, fmk["neck"][1]))[1] * g
    a = fim[..., 3].astype(np.float32)
    H, W = a.shape
    yy, xx = np.mgrid[0:H, 0:W]
    hmask = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 < 1
    a[hmask] = 0
    fim[..., 3] = a.astype(np.uint8)
    # the canvas: both, the bust placed with its chin on the body's chin
    off = fchin - bchin                                          # bust image px -> body image px
    bh_, bw_ = bim.shape[:2]
    X0, Y0 = int(np.floor(min(0, off[0]))), int(np.floor(min(0, off[1])))
    X1, Y1 = int(np.ceil(max(W, off[0] + bw_))), int(np.ceil(max(H, off[1] + bh_)))
    can = np.zeros((Y1 - Y0, X1 - X0, 4), np.float32)

    def over(img, ox, oy, alpha_mul=None):
        im = img.astype(np.float32) / 255
        if alpha_mul is not None:
            im[..., 3] *= alpha_mul
        h, w = im.shape[:2]
        M = np.float32([[1, 0, ox - X0], [0, 1, oy - Y0]])
        warped = cv2.warpAffine(im, M, (can.shape[1], can.shape[0]), flags=cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        al = warped[..., 3:4]
        can[..., :3] = warped[..., :3] * al + can[..., :3] * (1 - al)
        can[..., 3:4] = al + can[..., 3:4] * (1 - al)

    over(fim, 0, 0)
    # the bust's own collar fades into the body's clothes below its neck
    bneck_y = B(0, bmk["neck"][1])[1]
    ys = np.arange(bh_, dtype=np.float32)[:, None]
    bot = bh_ - 1
    f0 = bneck_y + 0.45 * (bot - bneck_y)
    fade = np.clip(1 - (ys - f0) / max(1.0, 0.9 * (bot - f0)), 0, 1)
    # only the acting head itself (the sheet's neighbours leave slivers at the edges of its cut)
    ba = (bim[..., 3] > 40).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(ba, 8)
    if n > 2:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        keep = cv2.dilate((lab == k).astype(np.uint8), np.ones((5, 5), np.uint8))
        bim = bim.copy()
        bim[..., 3] = np.where(keep > 0, bim[..., 3], 0)
    over(bim, off[0], off[1], fade)
    out = can.copy()
    out[..., :3] = np.clip(out[..., :3], 0, 1)
    img = (out * 255 + 0.5).astype(np.uint8)
    ys_, xs_ = np.nonzero(img[..., 3] > 5)
    cx0, cy0, cx1, cy1 = xs_.min(), ys_.min(), xs_.max() + 1, ys_.max() + 1
    img = img[cy0:cy1, cx0:cx1]
    sh = np.float64([off[0] - X0 - cx0, off[1] - Y0 - cy0])     # bust image px -> close-up px
    img = cv2.resize(img, None, fx=OUT_K, fy=OUT_K, interpolation=cv2.INTER_AREA)

    def T(x, y):
        bx, by = B(x, y)
        return [round(float((bx + sh[0]) * OUT_K), 1), round(float((by + sh[1]) * OUT_K), 1)]
    m = bmk
    marks = dict(eyes=[T(e[0], e[1]) + [round(e[2] * bS * OUT_K, 1), round(e[3] * bS * OUT_K, 1)] for e in m["eyes"]],
                 mouth=T(m["mouth"][0], m["mouth"][1]) + T(m["mouth"][2], m["mouth"][3]) + T(m["mouth"][4], m["mouth"][5]),
                 chin=T(0, m["chin"])[1], neck=T(m["neck"][0], m["neck"][1]),
                 head=T(m["head"][0], m["head"][1]) + T(m["head"][2], m["head"][3]))
    name = f"close_{head}_{body}"
    rel = f"reference/cuts/closeups/{name}.png"
    out_p = CHARACTERS / cid / rel
    out_p.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_p), img)
    # size: one close-up px is 1 / (fS * g) body sheet px (bodies are on their casual sheets: factor 1)
    spec = yaml.safe_load((CHARACTERS / cid / "film.yaml").read_text())["drawings"]
    faces = spec[f"bust_{head}"].get("faces", "F")
    entry = dict(image=rel, faces=faces, drawn_pupils=True, jaw=1.3, marks=marks, close_fac=round(1.0 / (fS * g * OUT_K), 6),
                 **{"from": f"bust_{head} on {body}"})
    print(cid, name, img.shape, "g", round(g, 3))
    return name, entry


def main():
    for cid, pairs in CLOSE.items():
        p = CHARACTERS / cid / "film.yaml"
        d = yaml.safe_load(p.read_text())
        for head, body in pairs:
            name, entry = make(cid, head, body)
            d["drawings"][name] = entry
        p.write_text(yaml.safe_dump(d, sort_keys=False, default_flow_style=None))


if __name__ == "__main__":
    sys.exit(main())

"""Snap face marks onto the drawing: for each drawing, a search box round its mouth (and round any eye to add or
refit) in sheet px of its cut; the mouth is the darkest wide stroke in its box (its two ends are the corners), an eye is
the eye white plus its pupil (or, for a far eye drawn almost all dark, the dark eye shape). Writes the marks into
film.yaml and draws them for checking -> build/markfit_<character>.jpg.
    FILM_EPISODE=the-undercard PYTHONPATH=episodes/the-undercard:. python3 episodes/the-undercard/tools/markfit.py BOXES.json"""
import json
import re
import sys

import cv2
import numpy as np
import yaml
from PIL import Image

from studio.film import ep
from studio.paths import BUILD, CHARACTERS


def load(cid, sp):
    im = np.array(Image.open(CHARACTERS / cid / sp["sheet"]).convert("RGBA")).astype(np.float32) / 255
    return im


def fit_mouth(im, box):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    c = im[y0:y1, x0:x1]
    v = c[..., :3].max(2)
    a = c[..., 3] > 0.5
    vals = v[a]
    thr = min(0.62, float(np.percentile(vals, 6)) + 0.10) if vals.size else 0.3
    dark = ((v < thr) & a).astype(np.uint8)
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((1, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(dark, 8)
    best, score = None, -1
    for i in range(1, n):
        w, h, ar = st[i, 2], st[i, 3], st[i, 4]
        if w < 4 or ar < 4:
            continue
        s = w * min(3.0, w / max(1, h))
        if s > score:
            best, score = i, s
    if best is None:
        return None
    ys, xs = np.nonzero(lab == best)
    xl, xr = xs.min(), xs.max()
    yl = ys[xs <= xl + 1].mean()
    yr = ys[xs >= xr - 1].mean()
    xc = (xl + xr) / 2
    mid = np.abs(xs - xc) <= max(1, 0.12 * (xr - xl))
    yc = ys[mid].min() if mid.any() else (yl + yr) / 2            # the top of the stroke at its middle
    return [float(xl + x0), float(yl + y0), float(xr + x0), float(yr + y0), float(xc + x0), float(yc + y0)]


def fit_eye(im, box):
    x0, y0, x1, y1 = [int(round(v)) for v in box]
    c = im[y0:y1, x0:x1]
    rgb = c[..., :3]
    v, mn = rgb.max(2), rgb.min(2)
    a = c[..., 3] > 0.5
    white = ((v > 0.78) & (v - mn < 0.18) & a).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(white, 8)
    if n > 1:
        k = 1 + int(np.argmax(st[1:, 4]))
        wm = (lab == k).astype(np.uint8)
    else:
        wm = np.zeros_like(white)
    dark = ((v < 0.30) & a).astype(np.uint8)
    if wm.sum() >= 6:
        hull = cv2.convexHull(cv2.findNonZero(wm))
        reg = np.zeros_like(wm)
        cv2.fillConvexPoly(reg, hull, 1)
        # the pupil may sit at the edge of the white: take the dark pixels touching it
        near = cv2.dilate(reg, np.ones((5, 5), np.uint8)) & dark
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(near, 8)
        for i in range(1, n2):
            if st2[i, 4] < 0.8 * max(1, wm.sum()):
                reg |= (lab2 == i).astype(np.uint8)
        kind = "white"
    else:
        n2, lab2, st2, _ = cv2.connectedComponentsWithStats(dark, 8)
        if n2 < 2:
            return None
        k = 1 + int(np.argmax(st2[1:, 4]))
        reg = (lab2 == k).astype(np.uint8)
        kind = "dark"
    ys, xs = np.nonzero(reg)
    cx, cy = (xs.min() + xs.max()) / 2 + x0, (ys.min() + ys.max()) / 2 + y0
    rx, ry = (xs.max() - xs.min() + 1) / 2, (ys.max() - ys.min() + 1) / 2
    return [round(float(cx), 1), round(float(cy), 1), round(float(rx), 2), round(float(ry), 2)], kind


def draw(im, mk, boxes):
    pts = [(e[0] - 1.6 * e[2], e[1] - 1.6 * e[3]) for e in mk.get("eyes", [])]
    pts += [(e[0] + 1.6 * e[2], e[1] + 1.6 * e[3]) for e in mk.get("eyes", [])]
    if mk.get("mouth"):
        m = mk["mouth"]
        pts += [(m[0] - 8, m[1] - 8), (m[2] + 8, m[3] + 12)]
    for b in boxes:
        pts += [(b[0], b[1]), (b[2], b[3])]
    p = np.float32(pts)
    x0, y0 = np.floor(p.min(0)).astype(int) - 4
    x1, y1 = np.ceil(p.max(0)).astype(int) + 4
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(im.shape[1], x1), min(im.shape[0], y1)
    c = im[y0:y1, x0:x1]
    comp = (c[..., :3] * c[..., 3:] + (1 - c[..., 3:]) * np.float32([0.8, 0.8, 0.8]))
    K = 480 / max(1, max(x1 - x0, y1 - y0))
    big = cv2.resize((comp * 255).astype(np.uint8), (int((x1 - x0) * K), int((y1 - y0) * K)), interpolation=cv2.INTER_CUBIC)
    P = lambda x, y: (int((x - x0) * K), int((y - y0) * K))
    for gx in range((x0 // 5 + 1) * 5, x1, 5):
        X = P(gx, 0)[0]
        cv2.line(big, (X, 0), (X, big.shape[0]), (255, 255, 255) if gx % 10 == 0 else (200, 200, 200), 1)
        if gx % 10 == 0:
            cv2.putText(big, str(gx), (X + 2, 11), 0, 0.36, (0, 0, 160), 1)
    for gy in range((y0 // 5 + 1) * 5, y1, 5):
        Y = P(0, gy)[1]
        cv2.line(big, (0, Y), (big.shape[1], Y), (255, 255, 255) if gy % 10 == 0 else (200, 200, 200), 1)
        if gy % 10 == 0:
            cv2.putText(big, str(gy), (2, Y - 2), 0, 0.36, (0, 0, 160), 1)
    for b in boxes:
        cv2.rectangle(big, P(b[0], b[1]), P(b[2], b[3]), (0, 120, 255), 1)
    for e in mk.get("eyes", []):
        cv2.ellipse(big, P(e[0], e[1]), (max(1, int(e[2] * K)), max(1, int(e[3] * K))), 0, 0, 360, (0, 200, 0), 2)
    m = mk.get("mouth")
    if m:
        cv2.line(big, P(m[0], m[1]), P(m[4], m[5]), (255, 0, 0), 2)
        cv2.line(big, P(m[4], m[5]), P(m[2], m[3]), (255, 0, 0), 2)
        for q in ((m[0], m[1]), (m[2], m[3])):
            cv2.circle(big, P(*q), 4, (255, 0, 0), 2)
    t = np.full((500, 480, 3), 40, np.uint8)
    t[:min(480, big.shape[0]), :min(480, big.shape[1])] = big[:480, :480]
    return t


def main():
    boxes = json.loads(open(sys.argv[1]).read())
    for cid, items in boxes.items():
        f = CHARACTERS / cid / "film.yaml"
        spec = yaml.safe_load(f.read_text())["drawings"]
        built = json.loads((BUILD / "film" / cid / "marks.json").read_text())
        new, tiles = {}, []
        for name, b in items.items():
            sp = dict(spec[name])
            im = load(cid, sp)
            mk = dict(sp.get("marks") or {k: v for k, v in built[name].items()})
            mk.setdefault("head", built[name]["head"])
            if b.get("mouth_set"):
                m = b["mouth_set"]
                mk["mouth"] = m
                mk["chin"] = b.get("chin", round(m[5] + 0.6 * (m[2] - m[0]) + 4, 1))
                mk.setdefault("neck", built[name].get("neck") or [m[4], m[5] + 30])
            elif b.get("mouth"):
                m = fit_mouth(im, b["mouth"])
                if m:
                    mk["mouth"] = [round(v, 1) for v in m]
                    mk["chin"] = b.get("chin", mk.get("chin") or round(m[5] + 0.9 * (m[2] - m[0]), 1))
                    if mk["chin"] <= m[5] + 3:
                        mk["chin"] = round(m[5] + 0.6 * (m[2] - m[0]) + 4, 1)
                    mk.setdefault("neck", built[name].get("neck") or [m[4], m[5] + 30])
                else:
                    print(f"{cid}:{name}: no mouth stroke in {b['mouth']}")
            eyes = [] if b.get("eyes_replace") else list(mk.get("eyes") or built[name].get("eyes") or [])
            for eb in b.get("eyes", []):
                r = fit_eye(im, eb)
                if r:
                    eyes.append(r[0])
                else:
                    print(f"{cid}:{name}: no eye in {eb}")
            eyes.sort(key=lambda e: e[0])
            ded = []
            for e in eyes:                                  # one mark per eye
                if not any(abs(e[0] - q[0]) < 5 and abs(e[1] - q[1]) < 5 for q in ded):
                    ded.append(e)
            eyes = ded
            mk["eyes"] = eyes
            sp["marks"] = mk
            sp.pop("plain", None)
            new[name] = sp
            tl = draw(im, mk, ([b["mouth"]] if b.get("mouth") else []) + list(b.get("eyes", [])))
            cv2.putText(tl, name, (4, 494), 0, 0.55, (255, 255, 0), 1)
            tiles.append(tl)
        out = []
        for ln in f.read_text().splitlines():
            mm = re.match(r"^  (\w+): \{", ln)
            if mm and mm.group(1) in new:
                ln = f"  {mm.group(1)}: " + yaml.safe_dump(new[mm.group(1)], default_flow_style=True, width=3000,
                                                          sort_keys=False).strip()
            out.append(ln)
        f.write_text("\n".join(out) + "\n")
        yaml.safe_load(f.read_text())
        while len(tiles) % 4:
            tiles.append(np.full((500, 480, 3), 40, np.uint8))
        sheet = np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)])
        p = ep.path(f"markfit_{cid}.jpg")
        Image.fromarray(sheet).save(p, quality=90)
        print(p, ", ".join(new))


if __name__ == "__main__":
    main()

"""Saeed's expression heads put on his full-body drawing, so every close-up has his body under it (the sheet's
expression cells are heads with a stub of shoulder: filmed alone they float).

For each expression: the head (its 8x part, mouth already painted shut where film.yaml says close_mouth) is scaled
so its eyes-to-chin length matches the body's, placed chin on chin, centred on the body's face; below the jaw only
the face itself is kept (the bust's shoulders and collar are cut away, the body's own collar and shirt show); the
body's own head is taken off first. The result is a drawing in library/characters/saeed-the-lecher/reference/
composite/<name>.png with its eye / mouth / chin / head / neck landmarks written into film.yaml (as image px).

    python3 episodes/lecher-vs-rio/tools/heads_on_body.py   (after studio.film.art has built the parts)"""
import json
import re
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
CID = "saeed-the-lecher"
PARTS = ROOT / "build" / "film" / CID
CH = ROOT / "library" / "characters" / CID
OUT = CH / "reference" / "composite"
BODY = "front"
HEADS = ["head", "neutral", "angry", "confused", "shouting", "scared", "happy", "suspicious", "disgusted", "silly"]
SPEAKS = {"head", "neutral", "angry"}          # heads whose mouth the lip sync opens (the rest keep their drawn mouth)


def load(name):
    return np.asarray(Image.open(PARTS / f"{name}.png").convert("RGBA")).copy()


META = json.loads((PARTS / "meta.json").read_text())
MARKS = json.loads((PARTS / "marks.json").read_text())


def to_part(name, x, y):
    m = META[name]
    return (x - m["off"][0]) * m["scale"], (y - m["off"][1]) * m["scale"]


def eyes(name):
    (a, b) = MARKS[name]["eyes"][:2]
    p, q = to_part(name, a[0], a[1]), to_part(name, b[0], b[1])
    return np.float32(p), np.float32(q)


BODY_CHIN = 765.0                              # the body's jaw line (part px): its auto landmark found the mouth


def chin(name, e0, e1):
    ed = float(np.linalg.norm(e1 - e0))
    if name == BODY:
        return BODY_CHIN
    if MARKS[name].get("chin"):
        return to_part(name, 0, MARKS[name]["chin"])[1]
    return float((e0[1] + e1[1]) / 2 + 1.95 * ed)


def skin(rgb):
    hsv = cv2.cvtColor(np.ascontiguousarray(rgb), cv2.COLOR_RGB2HSV).astype(np.int16)
    return (hsv[..., 0] >= 3) & (hsv[..., 0] <= 25) & (hsv[..., 1] > 70) & (hsv[..., 2] > 70)


def face_keep(part, e0, e1, cy):
    """the head without its bust: above the ears' bottom, the head (as wide as it is at the eyes); below it, the
    face itself (its skin, connected to the eyes, grown a little to take in the jaw's ink outline) down to wherever
    the jaw ends: the double chin is kept whole, the collar and shoulders go"""
    H, W = part.shape[:2]
    ed = float(np.linalg.norm(e1 - e0))
    ey = float((e0[1] + e1[1]) / 2)
    cx = float((e0[0] + e1[0]) / 2)
    a = part[..., 3] > 20
    row = np.nonzero(a[int(ey)])[0]
    xl, xr = row.min() - 0.1 * ed, row.max() + 0.1 * ed
    keep = np.zeros((H, W), np.float32)
    y_ear = int(ey + 0.6 * ed)
    xx = np.arange(W)[None, :]
    keep[:y_ear] = a[:y_ear] & (xx >= xl) & (xx <= xr)
    sk = (skin(part[..., :3]) & a).astype(np.uint8)
    sk[:int(ey)] = 0
    n, lab, st, _ = cv2.connectedComponentsWithStats(sk, 8)
    k = lab[int(ey + 0.9 * ed), int(cx)]                       # the face: the skin under the nose
    if k == 0:
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
    face = (lab == k).astype(np.uint8)
    for j in range(1, n):                                      # and the ears (skin of their own, beside it)
        x0, y0, w, h, area = st[j]
        if j != k and area > 0.02 * ed * ed and xl <= x0 and x0 + w <= xr and y0 < ey + 1.2 * ed:
            face |= (lab == j).astype(np.uint8)
    face = cv2.morphologyEx(face, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
    r = max(3, int(0.09 * ed)) | 1
    face = cv2.dilate(face, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1)))
    cs, _ = cv2.findContours(face, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)      # an open mouth is part of the face
    face = np.zeros_like(face)
    cv2.drawContours(face, cs, -1, 1, -1)
    lower = (face > 0) & a
    lower[:y_ear] = False
    keep[lower] = 1.0
    return cv2.GaussianBlur(keep, (0, 0), 1.5)


def build(name):
    body = load(BODY).astype(np.float32)
    head = load(name).astype(np.float32)
    be0, be1 = eyes(BODY)
    he0, he1 = eyes(name)
    bey = float((be0[1] + be1[1]) / 2)
    bcx = float((be0[0] + be1[0]) / 2)
    bchin = chin(BODY, be0, be1)
    hey = float((he0[1] + he1[1]) / 2)
    hcx = float((he0[0] + he1[0]) / 2)
    hchin = chin(name, he0, he1)
    s = (bchin - bey) / (hchin - hey) * 1.04                     # a touch bigger: a cartoon head
    bed = float(np.linalg.norm(be1 - be0))
    # where the head goes (body px): its eye centre over the body's, its chin on the body's chin
    tx = bcx - s * hcx
    ty = bchin - s * hchin
    Hh, Wh = head.shape[:2]
    top = min(0, int(np.floor(ty)))
    pad_top = -top + 20
    Hb, Wb = body.shape[:2]
    left = min(0, int(np.floor(tx)))
    right = max(Wb, int(np.ceil(tx + s * Wh)))
    pad_l = -left + 20
    W = right - left + 40
    H = Hb + pad_top
    canvas = np.zeros((H, W, 4), np.float32)
    # the body, its own head taken off: above its chin everything but the shirt's shoulders
    b = body.copy()
    yy, xx = np.mgrid[0:Hb, 0:Wb]
    lum = b[..., :3].mean(2)
    shirt = (lum < 75) & (yy > bey + 0.95 * bed)
    off = (yy < bchin + 0.02 * bed) & (np.abs(xx - bcx) < 2.1 * bed) & ~shirt
    b[off, 3] = 0
    canvas[pad_top:pad_top + Hb, pad_l:pad_l + Wb] = b
    # the head, its bust cut away
    keep = face_keep(head.astype(np.uint8), he0, he1, hchin)
    hh = head.copy()
    hh[..., 3] *= keep
    M = np.float32([[s, 0, tx + pad_l], [0, s, ty + pad_top]])
    hw = cv2.warpAffine(hh, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_CONSTANT)
    a = hw[..., 3:4] / 255.0
    cb = canvas[..., :3] * (canvas[..., 3:4] / 255.0)
    rgb = hw[..., :3] * a + cb * (1 - a)
    alpha = a + canvas[..., 3:4] / 255.0 * (1 - a)
    out = np.dstack([np.where(alpha > 1e-4, rgb / np.maximum(alpha, 1e-4), 0), alpha * 255])
    out = np.clip(out, 0, 255).astype(np.uint8)
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray(out).save(OUT / f"{name}.png")

    def P(x, y):                                               # head-part px -> composite px
        return round(s * x + tx + pad_l, 1), round(s * y + ty + pad_top, 1)

    mk = MARKS[name]
    m = META[name]
    K = m["scale"]
    ev = []
    for e in mk["eyes"][:2]:
        x, y = P(*to_part(name, e[0], e[1]))
        ev.append([x, y, round(e[2] * K * s, 1), round(e[3] * K * s, 1)])
    marks = {"eyes": ev}
    if name in SPEAKS and mk.get("mouth"):
        q = mk["mouth"]
        p0, p1, pc = P(*to_part(name, q[0], q[1])), P(*to_part(name, q[2], q[3])), P(*to_part(name, q[4], q[5]))
        marks["mouth"] = [p0[0], p0[1], p1[0], p1[1], pc[0], pc[1]]
        marks["chin"] = P(0, hchin)[1]
    ex = (ev[0][0] + ev[1][0]) / 2
    hed = abs(ev[1][0] - ev[0][0])
    cyc = P(0, hchin)[1]
    marks["head"] = [round(ex - 2.3 * hed, 1), round(cyc - 4.6 * hed, 1), round(ex + 2.3 * hed, 1), round(cyc + 0.2 * hed, 1)]
    marks["neck"] = [round(ex, 1), round(cyc + 0.15 * hed, 1)]
    print(name, out.shape[1], "x", out.shape[0], "scale", round(s, 3))
    return marks


def main():
    fy = CH / "film.yaml"
    txt = fy.read_text()
    txt = re.sub(r"\n  # composites.*", "", txt, flags=re.S)
    lines = ["\n  # composites: the expression heads on the full body (episodes/lecher-vs-rio/tools/heads_on_body.py)"]
    for n in HEADS:
        mk = build(n)
        faces = "R" if n in ("confused", "suspicious", "disgusted") else "F"
        jaw = ", jaw: 1.6" if n in SPEAKS else ""
        lines.append(f"  b-{n}: {{image: reference/composite/{n}.png, faces: {faces}{jaw}, marks: {json.dumps(mk)}}}")
    fy.write_text(txt.rstrip("\n") + "\n".join(lines) + "\n")


main()

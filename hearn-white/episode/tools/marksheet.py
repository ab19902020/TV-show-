"""Every face drawing's marks over the art, on a grid in sheet px, two heads to a row -> build/marks_<character>_<k>.jpg.
Eyes green, mouth red (corners and centre), chin blue.
    FILM_EPISODE=the-undercard PYTHONPATH=episodes/the-undercard:. python3 episodes/the-undercard/tools/marksheet.py CHARACTER [drawing,...]"""
import json
import sys

import cv2
import numpy as np
import yaml
from PIL import Image

from studio.film import ep
from studio.paths import BUILD, CHARACTERS

K = 5
CELL = 760


def view(cid, n, sp, mk):
    im = np.array(Image.open(CHARACTERS / cid / sp["sheet"]).convert("RGBA")).astype(np.float32)
    h = mk["head"]
    cx, cy = (h[0] + h[2]) / 2, (h[1] + h[3]) / 2 + 10
    r = CELL / K / 2
    x0, y0 = int(max(0, cx - r)), int(max(0, cy - r))
    x1, y1 = int(min(im.shape[1], cx + r)), int(min(im.shape[0], cy + r))
    c = im[y0:y1, x0:x1]
    a = c[..., 3:] / 255
    c = (c[..., :3] * a + 255 * (1 - a)).astype(np.uint8)
    c = cv2.resize(c, None, fx=K, fy=K, interpolation=cv2.INTER_CUBIC)
    P = lambda x, y: (int((x - x0) * K), int((y - y0) * K))
    for x in range((x0 // 5 + 1) * 5, x1, 5):
        X = P(x, 0)[0]
        cv2.line(c, (X, 0), (X, c.shape[0]), (255, 60, 60) if x % 25 == 0 else (150, 200, 255), 1)
        if x % 25 == 0:
            cv2.putText(c, str(x), (X + 2, 12), 0, 0.42, (220, 0, 0), 1)
    for y in range((y0 // 5 + 1) * 5, y1, 5):
        Y = P(0, y)[1]
        cv2.line(c, (0, Y), (c.shape[1], Y), (255, 60, 60) if y % 25 == 0 else (150, 200, 255), 1)
        if y % 25 == 0:
            cv2.putText(c, str(y), (2, Y - 2), 0, 0.42, (220, 0, 0), 1)
    for e in mk.get("eyes", []):
        cv2.ellipse(c, P(e[0], e[1]), (max(1, int(e[2] * K)), max(1, int(e[3] * K))), 0, 0, 360, (0, 190, 0), 2)
    if mk.get("mouth"):
        m = mk["mouth"]
        cv2.line(c, P(m[0], m[1]), P(m[4], m[5]), (255, 0, 0), 2)
        cv2.line(c, P(m[4], m[5]), P(m[2], m[3]), (255, 0, 0), 2)
        for q in ((m[0], m[1]), (m[2], m[3])):
            cv2.circle(c, P(*q), 5, (255, 0, 0), 2)
    if mk.get("chin"):
        x = mk["mouth"][4] if mk.get("mouth") else cx
        cv2.circle(c, P(x, mk["chin"]), 5, (0, 0, 255), -1)
    out = np.full((CELL + 30, CELL, 3), 30, np.uint8)
    out[30:30 + c.shape[0], :c.shape[1]] = c[:CELL, :CELL]
    cv2.putText(out, f"{n}", (6, 22), 0, 0.7, (255, 255, 0), 2)
    return out


def main():
    cid = sys.argv[1]
    only = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else None
    spec = yaml.safe_load((CHARACTERS / cid / "film.yaml").read_text())["drawings"]
    marks = json.loads((BUILD / "film" / cid / "marks.json").read_text())
    tiles = [view(cid, n, spec[n], marks[n]) for n in spec if (only is None or n in only) and n in marks
             and (marks[n].get("eyes") or marks[n].get("mouth") or only)]
    k = 0
    for i in range(0, len(tiles), 2):
        row = tiles[i:i + 2]
        if len(row) < 2:
            row.append(np.full_like(row[0], 30))
        out = ep.path(f"marks_{cid}_{k}.jpg")
        Image.fromarray(np.hstack(row)).save(out, quality=88)
        print(out)
        k += 1


if __name__ == "__main__":
    main()

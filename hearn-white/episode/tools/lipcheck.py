"""The mouths against the words: for every line, the speaker's face (wherever they stand in the shot) at its stressed
words (open shapes) and its first M / B / P (a closed mouth), rendered and cropped to the head -> build/lipcheck.jpg.
    FILM_EPISODE=the-undercard PYTHONPATH=episodes/the-undercard:. python3 episodes/the-undercard/tools/lipcheck.py [L001 ...]"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import framing as FR                                     # noqa: E402  (layout px, uncorrected cameras + corrections)
from film import actors as A                             # noqa: E402
import film.direction as D                               # noqa: E402
import film.perf as PF                                   # noqa: E402
from film.timeline import TL                             # noqa: E402

fits = json.loads(D.FRAMING_FILE.read_text()) if D.FRAMING_FILE.exists() else {}
for s in D.SHOTS:                                         # the corrected cameras, as the render uses them
    c = fits.get(D.signature(s)) if s.get("kind") == "world" else None
    if c:
        s["cams"] = [(tk, (k[0] + c[0], k[1] + c[1], k[2] * c[2])) for tk, k in s["cams"]]
    s["corr"] = (0, 0, 1)
L = json.loads(D.ep.path("lines.json").read_text())
only = set(sys.argv[1:])
tiles = []
for lid, v in TL["lines"].items():
    if only and lid not in only:
        continue
    stressed = set(PF.META[lid][2])
    ws = L[lid]["words"]
    pick = [(w, "s") for w in ws if w["w"] in stressed][:2] + [(w, "c") for w in ws if w["w"][0] in "mbp"][:1]
    for w, kind in pick:
        t = v["start"] + ((w["s"] + w["e"]) / 2 if kind == "s" else w["s"] + 0.04)
        s = D.shot_at(t)
        if s.get("kind") != "world":
            continue
        M, sc = FR.view(s, t, s["corr"])
        it = next((i for i in s["cast"] if i.get("who") == v["speaker"] and A.visible(i, t)), None)
        if it is None:
            continue
        hb, fb, key = FR.boxes(s, it, t, M, sc)
        if hb is None or FR.frac_in(hb) < 0.9:
            continue
        img = FR.R.render_frame(int(round(t * 30)))
        x0, y0, x1, y1 = hb
        cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2 + 0.1 * (y1 - y0), 0.62 * max(x1 - x0, y1 - y0)
        X0, Y0 = int(max(0, cx - r)), int(max(0, cy - r))
        X1, Y1 = int(min(img.shape[1], cx + r)), int(min(img.shape[0], cy + r))
        TS = int(__import__("os").environ.get("TILE", "220")); crop = cv2.resize(img[Y0:Y1, X0:X1], (TS, TS), interpolation=cv2.INTER_AREA)
        lab = f"{lid} {w['w']}"
        cv2.putText(crop, lab, (4, TS - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(crop, lab, (4, TS - 8), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 230, 0), 1, cv2.LINE_AA)
        tiles.append(crop)
        print(lab, key, f"{t:.2f}", flush=True)
while len(tiles) % 10:
    tiles.append(np.zeros((TS, TS, 3), np.uint8))
out = D.ep.path("lipcheck.jpg")
cv2.imwrite(str(out), np.vstack([np.hstack(tiles[i:i + 10]) for i in range(0, len(tiles), 10)])[..., ::-1],
            [cv2.IMWRITE_JPEG_QUALITY, 88])
print(out)

"""Nobody sliced by the frame. For every shot (its cameras as corrected by the framing pass), six times a second,
each person drawn is either wholly in the frame or wholly out of it at the sides; a body whose feet alone are cut
off at the bottom of a wide is listed too. People walking in or out of shot are allowed to cross the edge. Lists
(shot, time span, who, edge, how much of them is in).

    FILM_EPISODE=the-undercard PYTHONPATH=episodes/the-undercard:. python3 episodes/the-undercard/tools/cutoffs.py"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import framing as F                                     # noqa: E402  (direction.py's cameras uncorrected)

D, A, OW, OH = F.D, F.A, F.OW, F.OH
FITS = json.loads(D.FRAMING_FILE.read_text()) if D.FRAMING_FILE.exists() else {}
SLACK = 0.03                                            # 3 % of a figure's width over the edge is still "in"
figure_box = F.figure_box


def cuts(s):
    c = FITS.get(D.signature(s), (0, 0, 1)) if not s.get("locked") else (0, 0, 1)
    corr, hide = tuple(c[:3]), (c[3] if len(c) > 3 else [])
    out = []
    times = list(np.arange(s["t"] + 0.02, s["end"] - 0.02, 1 / 6)) + [s["end"] - 0.03]
    for t in times:
        M, sc = F.view(s, t, corr)
        for it in s["cast"]:
            if "who" not in it or not A.visible(it, t) or it["who"] in hide:
                continue
            fb, key = figure_box(s, it, t, M, sc)
            x0, y0, x1, y1 = fb
            w, h = max(1e-6, x1 - x0), max(1e-6, y1 - y0)
            hin = max(0.0, min(x1, OW) - max(x0, 0.0)) / w
            vin = max(0.0, min(y1, OH) - max(y0, 0.0)) / h
            if hin <= 0.0 or vin <= 0.0:
                continue
            mv = F.moving(it, t)
            if hin < 1 - SLACK and not mv:
                out.append((t, it["who"], "left" if x0 < 0 else "right", hin, key))
            if 0.80 < vin < 1 - SLACK and y1 > OH:
                out.append((t, it["who"], "feet", vin, key))
            if y0 < 0 and vin < 1 - SLACK:
                out.append((t, it["who"], "top", vin, key))
    return out


def main():
    n = 0
    for s in D.SHOTS:
        if s.get("kind") != "world":
            continue
        rows = cuts(s)
        if not rows:
            continue
        groups = {}
        for t, who, edge, f, key in rows:
            groups.setdefault((who, edge), []).append((t, f, key))
        for (who, edge), v in groups.items():
            ts = [a for a, _, _ in v]
            fs = [f for _, f, _ in v]
            keys = sorted({k.split(":")[1] for _, _, k in v})
            print(f"shot {s['i'] + 1:02d} {s['t']:7.2f}-{s['end']:7.2f} {D.PLATES[s['plate']]:24s} {who:9s} {edge:5s} "
                  f"{min(ts):7.2f}-{max(ts):7.2f}  in {min(fs):.2f}-{max(fs):.2f}  {','.join(keys)}")
            n += 1
    print(f"cut-offs: {n}")


if __name__ == "__main__":
    main()

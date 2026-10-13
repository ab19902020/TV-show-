"""No head is ever cut by the frame. For every shot this finds where each person's head (the head box of the drawing
they are in at that moment, through their placement, lean and the handheld drift) lands on screen, six times a
second, and moves the camera (up, sideways, then wider if it has to) until every head that is on screen is wholly
inside it, with headroom. Nobody is filmed headless either: anyone more than a sliver in shot keeps their head.
The corrections are written to film/framing.json, which direction.py applies to the shots' cameras (each keyed to
the shot's own camera and times, so a changed shot is re-fitted, never mis-corrected).

Bodies too: nobody is sliced by the side of the frame (a hand, an elbow, a shoulder, a sliver of someone at the edge):
each person standing in the shot is brought wholly in or taken wholly out, and a figure whose feet alone would be
cut off at the bottom is brought down into the frame (people walking in or out of shot may cross the edge).

It also checks the lip sync can be seen: for every line, whether the speaker is on screen while saying it and
whether the drawing they are in then has a mouth the engine can animate.

    FILM_EPISODE=the-undercard PYTHONPATH=episodes/the-undercard:. python3 episodes/the-undercard/tools/framing.py [--report]"""
import json
import math
import os
import sys

import numpy as np

os.environ.pop("EP_RES", None)                         # layout px (1920 x 1080)
os.environ["FRAMING_RAW"] = "1"                         # direction.py: the cameras as written, uncorrected

from studio.film import render as R                     # noqa: E402
from studio.film.cast import CAST                        # noqa: E402
from studio.film.engine import OH, OW                    # noqa: E402
from studio.paths import BUILD                           # noqa: E402

import film.direction as D                               # noqa: E402
from film import actors as A                             # noqa: E402

A._install_camera()                                      # the shots' shakes, snap zooms and tracking moves

W1, H1 = 1672.0, 941.0
TOP, SIDE = 0.035 * OH, 0.012 * OW                       # headroom above, room at the sides
OUT = D.FRAMING_FILE


def scale(z):
    return OW / W1 * z


def clamp(cx, cy, z):
    s = scale(z)
    hw, hh = OW / (2 * s), OH / (2 * s)
    cx = W1 / 2 if hw * 2 >= W1 else min(max(cx, hw), W1 - hw)
    cy = H1 / 2 if hh * 2 >= H1 else min(max(cy, hh), H1 - hh)
    return cx, cy


def view(s, t, corr):
    dx_, dy_, zf = corr
    cx, cy, z = R.cam_at(s, t)
    cx, cy, z = cx + dx_, cy + dy_, z * zf
    ddx, ddy = R.drift(t, s, s["drift"])
    sc = scale(z)
    cx, cy = clamp(cx - ddx / sc, cy - ddy / sc, z)
    return np.float32([[sc, 0, OW / 2 - sc * cx], [0, sc, OH / 2 - sc * cy]]), sc


def boxes(s, it, t, M, sc):
    """screen boxes of a person at t: (head x0, y0, x1, y1), (figure x0, y0, x1, y1), drawing key"""
    key = A.key_of(it["who"], A.pose_at(it, t))
    d, info = CAST.get(key)
    Ms, mir, F, Hs = A.person_matrix(s, it, key, t, M, sc)
    hx0, hy0, hx1, hy1 = d.spec["head"] or head_box(key)
    w, h = d.size(1.0)
    fx0, fy0, fx1, fy1 = d.ox, d.oy, d.ox + w / d.S, d.oy + h / d.S

    def tb(x0, y0, x1, y1):
        P = np.float64([[x0, y0], [x1, y0], [x0, y1], [x1, y1]])
        Q = P @ Ms[:, :2].T + Ms[:, 2]
        return [Q[:, 0].min(), Q[:, 1].min(), Q[:, 0].max(), Q[:, 1].max()]
    hb, fb = tb(hx0, hy0, hx1, hy1), tb(fx0, fy0, fx1, fy1)
    cl = A.at_time(it.get("clip"), t)
    if cl is not None:
        cy_ = M[1, 1] * cl + M[1, 2]
        fb[3] = min(fb[3], cy_)
        if hb[1] >= cy_:                                  # the head is down in the bin
            hb = None
    return hb, fb, key


_HEADS = {}


def head_box(key):
    """the head box of a drawing with no face to animate (build/film/<id>/marks.json)"""
    cid, name = key.split(":")
    if cid not in _HEADS:
        _HEADS[cid] = json.loads((BUILD / "film" / cid / "marks.json").read_text())
    return _HEADS[cid][name]["head"]


_AB = {}


def alpha_box(key):
    """the drawing's inked extent in its own sheet px (its image box can be much bigger: the split pair drawings keep
    the pair's canvas)"""
    if key not in _AB:
        d, _ = CAST.get(key)
        a = d.u8[1.0][..., 3] > 50
        ys, xs = np.nonzero(a)
        w, _h = d.size(1.0)
        k = d.S * a.shape[1] / w
        _AB[key] = (d.ox + xs.min() / k, d.oy + ys.min() / k, d.ox + (xs.max() + 1) / k, d.oy + (ys.max() + 1) / k)
    return _AB[key]


def figure_box(s, it, t, M, sc):
    """the screen box of what is inked of a person at t"""
    key = A.key_of(it["who"], A.pose_at(it, t))
    Ms, *_ = A.person_matrix(s, it, key, t, M, sc)
    x0, y0, x1, y1 = alpha_box(key)
    P = np.float64([[x0, y0], [x1, y0], [x0, y1], [x1, y1]])
    Q = P @ Ms[:, :2].T + Ms[:, 2]
    fb = [Q[:, 0].min(), Q[:, 1].min(), Q[:, 0].max(), Q[:, 1].max()]
    cl = A.at_time(it.get("clip"), t)
    if cl is not None:
        fb[3] = min(fb[3], M[1, 1] * cl + M[1, 2])
    return fb, key


BODY_SLACK = 0.03                                       # 3 % of a figure's width over the edge still counts as in


def moving(it, t):
    """walking (or carried) across the frame at t: entering and leaving the frame at its sides is allowed"""
    if not isinstance(it.get("at"), list):
        return False
    a = A.at_time(it["at"], t - 0.08, it.get("ease", False))
    b = A.at_time(it["at"], t + 0.08, it.get("ease", False))
    return abs(b[0] - a[0]) > 1.0


def frac_in(b):
    x0, y0, x1, y1 = b
    a = max(1e-6, (x1 - x0) * (y1 - y0))
    ix = max(0.0, min(x1, OW) - max(x0, 0.0))
    iy = max(0.0, min(y1, OH) - max(y0, 0.0))
    return ix * iy / a


def problems(s, corr, step=1 / 6, hide=()):
    """every head the frame cuts, six times a second: [(t, who, edge, include, exclude, head visible share)] where
    include / exclude are the camera moves (screen px, + = the camera moves right / down) that bring the head
    wholly in or take it wholly out of that edge (None: not allowed - a head is never cut off at the top)"""
    out = []
    times = list(np.arange(s["t"] + 0.01, s["end"] - 0.01, step)) + [s["end"] - 0.02]
    sub = (s.get("subject") or {}).get("who")
    for t in times:
        M, sc = view(s, t, corr)
        for it in s["cast"]:
            if "who" not in it or not A.visible(it, t) or it["who"] in hide:
                continue
            hb, fb, key = boxes(s, it, t, M, sc)
            out += body_problems(s, it, t, M, sc, sub)
            if hb is None:
                continue
            hin, fin = frac_in(hb), frac_in(fb)
            if hin <= 0.02:
                if hb[3] < 0 and fin > 0.10:                  # a body in shot with its head cut off above
                    out.append((t, it["who"], "top", hb[1] - TOP, None, 0.0))
                continue
            keep = it["who"] == sub
            side_ok = moving(it, t)
            if hb[1] < TOP:
                out.append((t, it["who"], "top", hb[1] - TOP, None, hin))
            if hb[3] > OH - 4:
                out.append((t, it["who"], "bottom", hb[3] - (OH - 4), None if keep else hb[1] - OH, hin))
            if hb[0] < SIDE and not side_ok:
                out.append((t, it["who"], "left", hb[0] - SIDE, None if keep else hb[2], hin))
            if hb[2] > OW - SIDE and not side_ok:
                out.append((t, it["who"], "right", hb[2] - (OW - SIDE), None if keep else hb[0] - OW, hin))
    return out


def body_problems(s, it, t, M, sc, sub):
    """a figure sliced by a side of the frame, or with only its feet cut off at the bottom (same tuples as problems)"""
    mv = moving(it, t)                                 # walking in or out: only the sides may cut them
    (x0, y0, x1, y1), _ = figure_box(s, it, t, M, sc)
    w, h = max(1e-6, x1 - x0), max(1e-6, y1 - y0)
    hin = max(0.0, min(x1, OW) - max(x0, 0.0)) / w
    vin = max(0.0, min(y1, OH) - max(y0, 0.0)) / h
    if hin <= 0.0 or vin <= 0.0:
        return []
    keep = it["who"] == sub
    out = []
    if hin < 1 - BODY_SLACK and not mv:
        if x0 < 0:
            out.append((t, it["who"], "left", x0 - 2, None if keep else x1 + 2, hin))
        if x1 > OW:
            out.append((t, it["who"], "right", x1 - OW + 2, None if keep else x0 - OW - 2, hin))
    if y1 > OH and 0.80 < vin < 1 - BODY_SLACK:
        out.append((t, it["who"], "bottom", y1 - OH + 2, None, vin))
    if y0 < 0 and vin < 1 - BODY_SLACK and y1 > 0.3 * OH:
        out.append((t, it["who"], "top", y0 - 2, None, vin))
    return out


def bounds(s, zf):
    """the range of camera moves (plate px) that keep at least one of the shot's camera keys off the set's edge"""
    xs, ys = [], []
    for _, (cx, cy, z) in s["cams"]:
        sc_ = scale(z * zf)
        hw, hh = OW / (2 * sc_), OH / (2 * sc_)
        xs.append((hw - cx, W1 - hw - cx) if 2 * hw < W1 else (0.0, 0.0))
        ys.append((hh - cy, H1 - hh - cy) if 2 * hh < H1 else (0.0, 0.0))
    return (min(a for a, _ in xs), max(b for _, b in xs)), (min(a for a, _ in ys), max(b for _, b in ys))


HEADROOM = 0.09


def compose(s):
    """a shot framed on one person, recomposed from the drawing they are really in at that moment (kneeling,
    crouched, standing): the top of their head 9 % below the top of the frame, `frac` of their figure in frame,
    the head never more than 42 % of the frame's height -> the correction to the shot's cameras"""
    sub = s.get("subject")
    if not sub:
        return 0.0, 0.0, 1.0
    t = min(s["t"] + 0.35, (s["t"] + s["end"]) / 2)
    it = next((i for i in s["cast"] if i.get("who") == sub["who"] and A.visible(i, t)), None)
    if it is None:
        return 0.0, 0.0, 1.0
    M, sc = view(s, t, (0, 0, 1))
    hb, fb, key = boxes(s, it, t, M, sc)
    if hb is None:
        return 0.0, 0.0, 1.0
    P = lambda X, Y: ((X - M[0, 2]) / sc, (Y - M[1, 2]) / sc)
    hx0, htop = P(hb[0], hb[1])
    hx1, hbot = P(hb[2], hb[3])
    _, fbot = P(fb[2], fb[3])
    Vh = max(sub["frac"] * (fbot - htop) / (1 - HEADROOM), (hbot - htop) / sub.get("hmax", 0.34))
    z = (OH / (OW / W1)) / Vh
    cy = htop - HEADROOM * Vh + Vh / 2
    cx = (hx0 + hx1) / 2 + (sub.get("dx") or 0.0)
    raw = s["cams"][0][1]
    return cx - raw[0], cy - raw[1], z / raw[2]


def speakers(s):
    """who speaks during the shot (they are never left out of it)"""
    from film.timeline import TL
    return {v["speaker"] for v in TL["lines"].values() if v["start"] < s["end"] and v["end"] > s["t"]}


def actors(s, step=0.1):
    """who acts in the shot - moves, changes drawing, comes into view, or is half of a paired drawing - and so is
    never left out of it"""
    out = set()
    times = list(np.arange(s["t"] + 0.01, s["end"] - 0.01, step)) + [s["end"] - 0.02]
    for it in s["cast"]:
        if "who" not in it:
            continue
        seen = [t for t in times if A.visible(it, t)]
        if not seen:
            continue
        poses = {A.pose_at(it, t) for t in seen}
        if any(str(p).startswith("pair_") for p in poses) or len(poses) > 1 or len(seen) < len(times):
            out.add(it["who"])
            continue
        if isinstance(it.get("at"), list):
            xs = [A.at_time(it["at"], t, it.get("ease", False)) for t in seen]
            if max(abs(a[0] - xs[0][0]) + abs(a[1] - xs[0][1]) for a in xs) > 4.0:
                out.add(it["who"])
    return out


def most_in(s, corr, step=1 / 6):
    """per person, the most of their figure the frame ever shows during the shot"""
    best = {}
    times = list(np.arange(s["t"] + 0.01, s["end"] - 0.01, step)) + [s["end"] - 0.02]
    for t in times:
        M, sc = view(s, t, corr)
        for it in s["cast"]:
            if "who" not in it or not A.visible(it, t):
                continue
            (x0, y0, x1, y1), _ = figure_box(s, it, t, M, sc)
            f = frac_in((x0, y0, x1, y1))
            best[it["who"]] = max(best.get(it["who"], 0.0), f)
    return best


def fit(s):
    """the smallest camera correction that keeps every head and body whole. The shot's subject and whoever speaks
    in it are always kept wholly in shot (the camera moves, then goes wider if it must, never wider than the whole
    set). Anyone else the frame would slice is brought in by a small move or left out of the shot: someone mostly out
    of frame anyway, or once the camera has gone as wide as the shot can take without losing its framing (a
    medium shot stays a medium shot). A shot marked `locked` (an extreme close-up framed by hand: the freeze on
    Dana's eyes) is left as written. -> ((dx, dy, zoom factor), problems left, people left out)"""
    if s.get("locked"):
        return (0.0, 0.0, 1.0), [], []
    dx, dy, zf = compose(s)
    zmin = 1.0 / min(z for _, (_, _, z) in s["cams"])
    zf = max(zf, zmin)
    sub = (s.get("subject") or {}).get("who")
    keep = speakers(s) | actors(s) | ({sub} if sub else set()) | set(s.get("keep", ()))
    zlo = max(zmin, zf * (0.92 if sub else 0.8))
    (bx0, bx1), (by0, by1) = bounds(s, zf)
    dx, dy = min(max(dx, bx0), bx1), min(max(dy, by0), by1)
    hide = set()
    seen = most_in(s, (dx, dy, zf))
    last = {}
    for _ in range(120):
        pr = problems(s, (dx, dy, zf), hide=hide)
        if not pr:
            return (dx, dy, zf), [], sorted(hide)
        # leave out whoever is barely in shot, or anyone (but the subject and the speakers) once the shot is as wide
        # as it may go
        out = {p[1] for p in pr if p[1] not in keep and (seen.get(p[1], 0.0) < 0.5 or zf <= zlo + 1e-6)}
        if out:
            hide |= out
            continue
        sc = scale(min(z for _, (_, _, z) in s["cams"]) * zf)
        want = {"x": [], "y": []}
        for t, who, edge, inc, exc, hin in pr:
            mv = inc if (exc is None or hin >= 0.5) else exc
            want["x" if edge in ("left", "right") else "y"].append(mv)
        moves = {}
        conflict = False
        for ax, v in want.items():
            if not v:
                continue
            lo, hi = min(v), max(v)
            if lo < 0 < hi:
                conflict = True
            moves[ax] = (lo - 3) if abs(lo) >= abs(hi) else (hi + 3)
            if last.get(ax) is not None and last[ax] * moves[ax] < 0:
                conflict = True                               # two people take turns pushing the camera: go wider
        last = dict(moves)
        (bx0, bx1), (by0, by1) = bounds(s, zf)
        ndx = min(max(dx + moves.get("x", 0.0) / sc, bx0), bx1)
        ndy = min(max(dy + moves.get("y", 0.0) / sc, by0), by1)
        moved = abs(ndx - dx) > 0.5 or abs(ndy - dy) > 0.5
        dx, dy = ndx, ndy
        if conflict or not moved:
            lo_ = zlo if any(p[1] not in keep for p in pr) else zmin
            if zf * 0.95 >= lo_ - 1e-6:
                zf *= 0.95
            elif zf > lo_ + 1e-6:
                zf = lo_
            elif lo_ > zmin + 1e-6:
                hide |= {p[1] for p in pr if p[1] not in keep}
                if not any(p[1] not in keep for p in pr):
                    zlo = zmin
            elif not moved:
                break
    return (dx, dy, zf), problems(s, (dx, dy, zf), hide=hide), sorted(hide)


def lips(shots):
    """lines whose speaker is on screen in a drawing with no mouth, and lines said off screen"""
    from film.timeline import TL
    L = json.loads((D.ep.path("lines.json")).read_text())
    who_of = {"eddie", "dana", "tyson", "joshua", "announcer", "referee", "attendant", "security"}
    bad, off = [], []
    for lid, v in TL["lines"].items():
        spk = v["speaker"]
        seen = mouthless = n = 0
        for w in L[lid]["words"]:
            t = v["start"] + (w["s"] + w["e"]) / 2
            s = D.shot_at(t)
            if s.get("kind") != "world":
                continue
            n += 1
            M, sc = view(s, t, s.get("corr", (0, 0, 1)))
            for it in s["cast"]:
                if it.get("who") != spk or not A.visible(it, t):
                    continue
                hb, fb, key = boxes(s, it, t, M, sc)
                if hb is None or frac_in(hb) < 0.9:
                    continue
                seen += 1
                d, info = CAST.get(key)
                cid, name = key.split(":")
                if CAST.spec(cid)["drawings"][name].get("plain") or not d.spec.get("mouth"):
                    mouthless += 1
        if n and mouthless:
            bad.append((lid, spk, mouthless, n))
        if n and seen < 0.5 * n:
            off.append((lid, spk, seen, n))
    return bad, off


def main():
    report_only = "--report" in sys.argv
    fits = {}
    total_bad = 0
    for s in D.SHOTS:
        if s.get("kind") != "world":
            continue
        hide = []
        if report_only:
            pr = problems(s, s.get("corr", (0, 0, 1)))
            corr = s.get("corr", (0, 0, 1))
        else:
            corr, pr, hide = fit(s)
        if pr:
            print(f"shot {s['i'] + 1:02d} {s['t']:7.2f}s  {D.PLATES[s['plate']]:22s} move ({corr[0]:+.0f}, {corr[1]:+.0f}) "
                  f"zoom x{corr[2]:.3f}  STILL {len(pr)}: " + ", ".join(sorted({f'{p[1]} {p[2]}' for p in pr})))
        total_bad += len(pr)
        fits[D.signature(s)] = [round(c, 4) for c in corr] + ([hide] if hide else [])
        if hide:
            print(f"shot {s['i'] + 1:02d} {s['t']:7.2f}s  {D.PLATES[s['plate']]:22s} left out: {', '.join(hide)}")
    if not report_only:
        OUT.write_text(json.dumps(fits, indent=1))
        print(f"wrote {OUT}")
    for s in D.SHOTS:
        c = fits.get(D.signature(s), (0, 0, 1)) if not report_only else s.get("corr", (0, 0, 1))
        s["corr"] = tuple(c[:3])
        if len(c) > 3:
            s["cast"] = [it for it in s["cast"] if it.get("who") not in c[3]]
    bad, off = lips(D.SHOTS)
    for lid, spk, k, n in bad:
        print(f"lip sync: {lid} {spk} on screen in a mouthless drawing at {k}/{n} words")
    for lid, spk, k, n in off:
        print(f"off screen: {lid} {spk} seen at {k}/{n} words")
    print(f"head problems left: {total_bad}")


if __name__ == "__main__":
    main()

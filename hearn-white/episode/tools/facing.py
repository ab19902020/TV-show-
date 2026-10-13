"""Who faces the wrong way: at every line and at the middle of every shot, each person drawn turned to one side
(film.yaml faces L / R, flipped when mirrored) is checked against where the one they should be facing stands (the
one they are talking to, or the one talking to them, or the speaker): a turned back is listed.

    FILM_EPISODE=the-undercard PYTHONPATH=episodes/the-undercard:. python3 episodes/the-undercard/tools/facing.py"""
import json

from studio.film import ep
from studio.film.cast import CAST

import film.direction as D
from film import actors as A
from film.perf import META
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
SIDE = {"R": 1, "L": -1}


def facing(it, t):
    key = A.key_of(it["who"], A.pose_at(it, t))
    cid, name = key.split(":")
    f = CAST.spec(cid)["drawings"][name].get("faces", "F")
    s = SIDE.get(f, 0)
    if A.at_time(it.get("mirror", False), t):
        s = -s
    return s, name


def check():
    out = []
    lines = sorted(TL["lines"].items(), key=lambda kv: kv[1]["start"])
    for s in D.SHOTS:
        if s.get("kind") != "world":
            continue
        ts = {round((s["t"] + s["end"]) / 2, 2)}
        for lid, v in lines:
            if s["t"] <= v["start"] + 0.3 < s["end"]:
                ts.add(round(v["start"] + 0.3, 2))
        for t in sorted(ts):
            spk = next((v["speaker"] for lid, v in lines if v["start"] <= t < v["end"] + 0.4), None)
            lid = next((lid for lid, v in lines if v["start"] <= t < v["end"] + 0.4), None)
            to = META.get(lid, (None, None))[1] if lid else None
            people = {it["who"]: it for it in s["cast"] if "who" in it and A.visible(it, t)}
            pos = {w: A.at_time(it["at"], t, it.get("ease", False))[0] for w, it in people.items()}
            for w, it in people.items():
                if str(A.pose_at(it, t)).startswith(("pair_",)):
                    continue
                f, name = facing(it, t)
                if not f:
                    continue
                target = to if w == spk else spk if to == w else spk
                if target in (None, "cam", w) or target not in pos:
                    continue
                dx = pos[target] - pos[w]
                if abs(dx) > 20 and (dx > 0) != (f > 0):
                    out.append((t, w, name, target, round(dx)))
    return out


if __name__ == "__main__":
    for t, w, name, target, dx in check():
        print(f"{t:7.2f}  {w:9s} {name:22s} faces away from {target} ({dx:+d} px)")

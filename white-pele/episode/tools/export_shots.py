"""Export the shot table (film/direction.py SHOTS) as shots.json and SHOTS.md: start/end, location, cast, the lyric
under it, the action (direction.py's beat comments), camera moves, props/effects and the cut in.

    EP_RES=1280x720 FILM_EPISODE=white-pele PYTHONPATH=episodes/white-pele:. python3 episodes/white-pele/tools/export_shots.py
"""
import json
import re
from pathlib import Path

from film.direction import SHOTS, WHIPS
from film.timeline import WORDS

EP = Path(__file__).resolve().parents[1]
PLACE = {"B01": "pub stage, front", "B02": "pub stage, side", "B03": "the pub from the stage",
         "B04": "terrace courtyard pitch (memory)", "B05": "street outside the pub", "B06": "players' tunnel",
         "B07": "the pitch, floodlit (memory)", "B08": "stadium concert stage", "B09": "stage looking out to the stands",
         "B10": "rooftop above the city", "F": "pub stage", "FC": "pub stage (crowd)", "PUB": "the pub floor", "ST": "Manchester street at dusk",
         "MW": "the mural wall", "S": "Sir Matt Busby Way", "EXT": "Old Trafford exterior, dusk",
         "EXT2": "Old Trafford exterior, red-lit", "TUN": "the tunnel", "TUNP": "tunnel mouth to the pitch",
         "OT": "Old Trafford, floodlit", "OTS": "Old Trafford, stage on the pitch", "MEM": "memory: afternoon match"}
NAMES = {**{f"fan{k}{x}": "supporters" for k in range(1, 7) for x in ("", "b")}, "rooney": "Rooney", "rio": "Rio", "mark": "Goldbridge", "gary": "Neville", "roy": "Keane",
         "maguire": "Maguire (drums)", "sesko": "Šeško (guitar)", "cunha": "Cunha (bass)", "kid": "young Rooney (red 10)"}


def beats():
    """direction.py's '# 12.3 (bar 4): what happens' comments, as (t, text)"""
    out, cur = [], None
    for line in (EP / "film/direction.py").read_text().splitlines():
        m = re.match(r"# (\d+\.\d+)(?: \(bar \d+\))?: (.*)", line)
        if m:
            cur = [float(m[1]), m[2]]
            out.append(cur)
        elif cur and re.match(r"# \S", line) and not line.startswith("# --"):
            cur[1] += " " + line[2:]
        else:
            cur = None
    return out


def cast(s):
    who = []
    for kind, v in s.get("layers", []):
        if kind == "actors":
            for a in v:
                w = a.get("who", "")
                if w in NAMES and NAMES[w] not in who:
                    who.append(NAMES[w])
    if any(k in ("fans", "fg_fans", "crowd") for k, _ in s.get("layers", [])) or s.get("crowd"):
        who.append("supporters")
    return who


def props(s):
    out = []
    for kind, v in s.get("layers", []):
        if kind == "props":
            out.append(v if isinstance(v, str) else str(v))
        elif kind == "actors":
            for a in v:
                for h in a.get("hold", []) or []:
                    h = h[0] if isinstance(h, (list, tuple)) else h
                    out.append(h.get("prop", "?") + (f" ({h['kind']})" if "kind" in h else "") if isinstance(h, dict)
                               else str(h))
    return sorted(set(out))


def main():
    bt = beats()
    rows = []
    for s in SHOTS:
        t0, t1 = s["t"], s["end"]
        act = [txt for t, txt in bt if t0 - 0.3 <= t < t1 - 0.05] or [txt for t, txt in bt if t <= t0][-1:]
        words = " ".join(w[2] for w in WORDS if t0 <= w[0] < t1)
        cams = [(round(t, 3), [round(float(x), 1) for x in c]) for t, c in s.get("cams", [])]
        cut = "whip" if any(abs(w - t0) < 0.3 for w in (x if isinstance(x, (int, float)) else x[0] for x in WHIPS)) \
            else ("open" if t0 == 0 else "cut")
        rows.append(dict(shot=s["i"] + 1, start=round(t0, 3), end=round(t1, 3), location=PLACE.get(s.get("plate"),
                    s.get("plate")), plate=s.get("plate"), cast=cast(s), lyric=words, action=" / ".join(act),
                    camera=cams, props=props(s), lighting=dict(grade=s.get("grade"), haze=s.get("haze"),
                    beams=s.get("beams"), lights=s.get("lights"), flash=s.get("flash"), blur=s.get("blur")),
                    transition_in=cut))
    (EP / "shots.json").write_text(json.dumps(rows, indent=1, ensure_ascii=False, default=str))
    md = ["# The White Pelé — shot table", "", "Exported from `film/direction.py` by `tools/export_shots.py`. Camera: "
          "(time s, [centre x, centre y, zoom(, roll)]) in plate pixels. Times are the song's (177.520 s).", "",
          "| # | start | end | location | cast | lyric | action | camera | props/effects | in |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        cam = "; ".join(f"{t}: {c}" for t, c in r["camera"])
        md.append(f"| {r['shot']} | {r['start']:.2f} | {r['end']:.2f} | {r['location']} | {', '.join(r['cast'])} | "
                  f"{r['lyric']} | {r['action']} | {cam} | {', '.join(r['props'])} | {r['transition_in']} |")
    (EP / "SHOTS.md").write_text("\n".join(md) + "\n")
    print(len(rows), "shots")


main()

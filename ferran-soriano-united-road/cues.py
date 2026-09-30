"""The timeline / cue track: one row per spoken phrase with its beat, start, end, the phrase, and what the picture
does over it (cameras, gestures, expressions, overlays), sampled from the performance (perf.py).

-> soriano_cues.csv, soriano_cues.json"""
import csv, json
import perf

GESTURE = {"g01": "G01 palms up", "g02": "G02 shrug", "g03": "G03 index finger", "g04": "G04 palms forward",
           "g05": "G05 counting", "g06": "G06 arms folded", "g07": "G07 hands clasped", "g08": "G08 dismissive wave",
           "r1": "G01 one palm (his right)", "l1": "G01 one palm (his left)"}
OVERLAY = {"accurate": "ACCURATE / UNHELPFUL", "ongoing": "CASE ONGOING / METER RUNNING", "115": "115",
           "cas1": "CAS", "cas2": "CAS", "supporter": "SUPPORTER -> INNOCENT", "journalist": "JOURNALIST -> APPEALING"}

def expression(f):
    if f["lid"] > 0.9: return None
    if f["arch"] > 3: return "one eyebrow raised"
    if f["smirk"] > 0.3 or (f["smile"] > 0.3 and f["squint"] > 0.3): return "smug smile"
    if f["smile"] > 0.35: return "delighted"
    if f["brow_in"] > 2: return "mock sadness"
    if f["brow_in"] < -1: return "mildly offended"
    if f["brow_l"] > 2 and f["brow_r"] > 2: return "brows raised"
    if abs(f["gaze"][0]) > 0.3 or abs(f["gaze"][1]) > 0.3: return "glance"
    return "neutral corporate"

def seq(vals):
    out = []
    for v in vals:
        if v and (not out or out[-1] != v): out.append(v)
    return out

def main():
    rows, n = [], 0
    for B in perf.TL["beats"]:
        for p in B["phrases"]:
            n += 1
            ts = [p["s"] + (p["e"] - p["s"]) * k / 20 for k in range(21)]
            sts = [perf.state(t) for t in ts]
            cams = seq([s["cam"][1] if s["cam"][2] > 0.5 else s["cam"][0] for s in sts])
            push = any(0.0 < s["cam"][2] < 1.0 for s in sts)
            rows.append({"sequence": n, "beat": B["n"], "start": round(p["s"], 2), "end": round(p["e"], 2),
                         "phrase": p["text"], "tag": p["tag"] or "",
                         "camera": " > ".join(cams) + (" (push)" if push else ""),
                         "gesture": " > ".join(seq([GESTURE[s["pose"]] for s in sts])),
                         "expression": " > ".join(seq([expression(s["face"]) for s in sts])),
                         "overlay": " / ".join(seq([OVERLAY[g[0]] for s in sts for g in s["gfx"]]))})
    with open("soriano_cues.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    json.dump(rows, open("soriano_cues.json", "w"), indent=1)
    print(len(rows), "cues")
    for r in rows[:6]: print(r)

if __name__ == "__main__":
    main()

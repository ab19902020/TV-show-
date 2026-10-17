"""The acting: each line's delivery and stressed words, and the reactions between them. Saeed plays everything to
his webcam (the lens), except where he checks himself out; Rio plays to his camera too. See studio/film/perf.py."""
import json

from studio.film import ep
from studio.film.perf import Performance
from studio.film.shots import Marks
from film.direction import SHOTS
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt = T.m, T.ls, T.le, T.wt

WHO = ["saeed", "rio"]
SPK = {w: w for w in WHO}

META = {
    "L001": ("confident", "cam", ["ferdinand", "microphone", "massive", "millions"]),
    "L002": ("sarcastic", "cam", ["glazers", "quieter", "two", "nil"]),
    "L003": ("smug", "cam", ["saeed", "lecturing", "mirror"]),
    "L004": ("dry", "cam", ["timber"]),
    "L005": ("pleased", "cam", ["tits", "sake"]),
    "L006": ("stunned", "cam", ["tits"]),
    "L007": ("smug", "cam", ["brilliant", "mine", "visible"]),
    "L008": ("indignant", "cam", ["twenty", "glazers", "piss", "body", "checks"]),
    "L009": ("angry", "cam", ["pundit", "bloody", "fashion", "police"]),
    "L010": ("honest", "cam", ["wondering", "fat"]),
    "L011": ("resigned", "cam", ["united", "decade", "eat", "feelings"]),
    "L012": ("innocent", "cam", ["not", "fault"]),
    "L013": ("deadpan", "cam", ["neither", "glazers"]),
    "L014": ("smug", "cam", ["funny", "both", "responsibility", "eh"]),
}
BASE = dict(saeed=(0.1, 0.0), rio=(0.1, 0.15))
DOWN = ("dir", 0.0, 0.9, 0.0)                     # down at his own belly
GAZE = {
    "saeed": [(wt("L004", "timber") - 0.1, m("cut_rio2"), DOWN),
              (m("silence") + 0.5, m("silence") + 1.4, ("dir", -0.8, 0.05, -0.3)),   # the silence: he looks away
              (m("silence") + 1.4, m("cut_end"), "cam")],
    "rio": [(m("silence") + 0.8, m("silence") + 1.7, ("dir", 0.8, 0.05, 0.3)),
            (m("silence") + 1.7, m("cut_end"), "cam")],
}
EXPR = {
    "saeed": [(m("cut_pip1"), wt("L004", "timber"), 0.5, -0.1, 0.2),
              (le("L013"), m("cut_split"), -0.4, -0.1, 0.2),
              (le("L014"), m("silence") + 0.5, -0.3, 0.55, 0.15),          # pleased with himself...
              (m("silence") + 0.5, m("cut_end"), 0.5, -0.1, 0.4)],         # ...then less so
    "rio": [(le("L005"), m("cut_tits"), 0.4, 0.8, 0.1),
            (m("cut_ouch"), m("cut_rant"), -0.6, -0.4, 0.08),
            (m("cut_split"), le("L014"), -0.2, -0.15, 0.3),
            (le("L014"), m("cut_end"), 0.55, -0.1, 0.3)],
}
NODS = {"saeed": [(wt("L007", "visible"), 2, 2.5)], "rio": [(wt("L005", "sake") + 0.15, 3, 3.0)]}
TURN = {"saeed": [(ls("L013"), le("L013"), 0.0, -2.0)]}
FORCED = {"saeed": [le("L013") + 0.25, m("silence") + 0.3], "rio": [le("L012") + 0.1, m("silence") + 0.9]}
NOBLINK = {"saeed": [(m("cut_tits"), le("L006"))]}
REST = dict(saeed="cam", rio="cam")

def _pumps(who, amt=0.55):
    """a forward pump of the body on every stressed word of his lines (his weight going into it)"""
    out = []
    for lid, (tag, _, words) in META.items():
        if L[lid]["speaker"] != who:
            continue
        seen = {}
        for wd in words:
            seen[wd] = seen.get(wd, 0) + 1
            try:
                t = wt(lid, wd, seen[wd])
            except KeyError:
                continue
            out.append((t - 0.06, t + 0.10, amt, 0.0, 0.07))
    return out


BODY = {
    "saeed": _pumps("saeed") + [
        (wt("L004", "timber") - 0.05, m("cut_rio2"), -0.2, 0.9, 0.2),          # he sinks, looking down at himself
        (ls("L008"), le("L009"), 0.45, 0.0, 0.4),                             # leaning into the rant
        (ls("L011"), le("L011") + 0.6, -0.1, 0.55, 0.6),                       # slumping as he eats his feelings
        (le("L014"), m("silence") + 0.4, -0.25, 0.0, 0.3)],                    # sitting back, pleased
    "rio": _pumps("rio", 0.4) + [(m("rio_laugh") - 0.1, m("cut_tits"), 0.3, 0.6, 0.12)],
}
TURN.update({"saeed": TURN.get("saeed", []) + [
    (wt("L013", "neither") - 0.05, wt("L013", "neither") + 0.25, -0.12, 0.0),   # a little head shake...
    (wt("L013", "neither") + 0.25, wt("L013", "are") + 0.05, 0.12, 0.0),
    (wt("L014", "funny") - 0.1, wt("L014", "eh"), 0.0, 6.0),                     # head on one side: "funny how..."
    (wt("L007", "brilliant") - 0.05, wt("L007", "at"), 0.0, -5.0),
    (wt("L010", "why"), le("L010"), 0.0, 4.0),
    (ls("L006") - 0.05, le("L006"), 0.0, -3.0)]})
NODS.update({"saeed": NODS.get("saeed", []) + [(wt("L009", "pundit"), 1, 4.0), (wt("L002", "nil"), 2, 3.5),
                                               (wt("L011", "eat"), 2, 3.0)]})

PERF = Performance(TL, L, WHO, SPK, META, lambda lid: ep.path("lines", f"{lid}.wav"), base=BASE, gaze=GAZE,
                   expr=EXPR, nods=NODS, turn=TURN, body=BODY, forced=FORCED, noblink=NOBLINK, rest_target=REST,
                   cuts=[s["t"] for s in SHOTS])

"""The acting: Rio talks to us with the grin of a man who has just made his best mate a cup of tea; Wilcox basks."""
import json

from studio.film import ep
from studio.film.perf import Performance
from studio.film.shots import Marks
from film.direction import SHOTS
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt = T.m, T.ls, T.le, T.wt

WHO = ["rio", "wilcox"]
SPK = {"rio": "rio"}
META = {
    "L001": ("pleased", "cam", ["jason", "wilcox", "leeds", "eighteen", "what", "guy"]),
    "L002": ("proud", "wilcox", ["closest", "friends"]),
    "L003": ("encouraging", "cam", ["wonderful", "great", "human", "trustworthy"]),
    "L004": ("explaining", "cam", ["straight", "knee", "jerk", "decision", "little", "detail", "way"]),
    "L005": ("honest", "cam", ["culmination", "ruben", "time", "expected"]),
    "L006": ("pleased", "cam", ["whenever", "complete", "understanding", "united"]),
    "L007": ("firm", "cam", ["longer", "forget", "results"]),
    "L008": ("explaining", "cam", ["true", "reflection", "big", "part", "decision", "manager's"]),
}
BASE = dict(rio=(0.2, 0.3), wilcox=(0.1, 0.4))
GAZE = {"wilcox": [(0, TL["total"], "cam")]}
NODS = {"rio": [(wt("L001", "guy"), 2, 3.0), (wt("L003", "trustworthy"), 2, 3.0), (wt("L008", "well"), 2, 3.0)],
        "wilcox": [(wt("L003", "wonderful"), 2, 2.5), (wt("L006", "complete"), 2, 2.5), (wt("L008", "true"), 3, 2.5)]}
TURN = {"rio": [(ls("L005"), wt("L005", "i", 2), 0.0, 5.0)], "wilcox": [(wt("L004", "decision"), wt("L004", "or"), 0.0, -5.0)]}
REST = dict(rio="cam", wilcox="cam")

PERF = Performance(TL, L, WHO, SPK, META, lambda lid: ep.path("lines", f"{lid}.wav"), base=BASE, gaze=GAZE,
                   nods=NODS, turn=TURN, rest_target=REST, cuts=[s["t"] for s in SHOTS])

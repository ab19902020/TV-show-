"""The acting of The Undercard: whom each line is said to, its delivery (studio/film/perf.py TAGS), the words that
get a nod, and the script's looks and reactions: Dana watching the trolley then looking into the lens for 12 frames,
the freeze on his eyes, Eddie's four-frame eye dart, both surprised at "Fine.", Eddie's smile with panicking brows,
Fury and Joshua's disbelieving joy. Mouths come from the recordings (lip sync a frame ahead)."""
import json

from studio.film import ep
from studio.film.perf import Performance
from studio.film.shots import Marks

from film.direction import SHOTS
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le = T.m, T.ls, T.le
WHO = ["eddie", "dana", "tyson", "joshua", "announcer", "referee", "attendant", "security"]
SPK = {w: w for w in WHO}
META = {
    "L001": ("smug", "cam", ["elite", "bald", "pussy"]), "L002": ("dry", "eddie", ["banned"]),
    "L003": ("firm", "security", ["completely", "ticket", "list", "exceptions"]),
    "L004": ("dry", "eddie", ["buys"]), "L005": ("smug", "security", ["especially", "expense"]),
    "L006": ("irritated", "cam", ["banned", "boxing", "half", "twelve"]),
    "L007": ("matter", "cam", ["worse"]),
    "L008": ("dry", "attendant", ["bin"]), "L009": ("flat", "security", ["towels"]),
    "L010": ("indignant", "cam", ["premium"]), "L011": ("flat", "security", ["american", "noise"]),
    "L012": ("dry", "attendant", ["pass"]), "L013": ("flat", "security", ["bin", "mate"]),
    "L014": ("smug", "cam", ["easy", "easiest"]),
    "L015": ("casual", "dana", ["little", "heavyweight"]), "L016": ("indignant", "tyson", ["dana", "white"]),
    "L017": ("casual", "dana", ["taller", "washing"]), "L018": ("annoyed", "tyson", ["help"]),
    "L019": ("casual", "dana", ["label", "forty", "tumble"]), "L020": ("deadpan", "dana", ["undercard"]),
    "L021": ("deadpan", "joshua", ["towels"]), "L022": ("quiet", "dana", ["american", "laundry"]),
    "L023": ("smug", "eddie", ["terrible"]), "L024": ("disbelieving", "dana", ["pillowcase"]),
    "L025": ("smug", "eddie", ["still"]), "L026": ("firm", "dana", ["banned"]),
    "L027": ("smug", "eddie", ["ring", "yourself"]), "L028": ("confident", "dana", ["fine"]),
    "L029": ("explaining", "dana", ["two", "bigger", "medicals", "kicking", "elbows", "wrestling"]),
    "L030": ("obvious", "eddie", ["boxing", "eddie"]), "L031": ("frustrated", "dana", ["establishing", "geography"]),
    "L032": ("deadpan", "tyson", ["stop"]), "L033": ("deadpan_happy", "joshua", ["absolutely", "years", "invoice"]),
    "L034": ("proud", "cam", ["ladies", "special", "additional"]),
    "L035": ("proud", "cam", ["red", "everything", "eddie", "hearn"]),
    "L036": ("proud", "cam", ["blue", "laundry", "dana", "white"]),
    "L037": ("serious", "cam", ["protect", "holding", "biting", "negotiating"]),
    "L038": ("resigned", "cam", ["half"]), "L039": ("frustrated", "cam", ["go", "podcast"]),
    "L040": ("indignant", "dana", ["actually", "hit"]), "L041": ("deadpan", "eddie", ["think"]),
    "L042": ("salesman", "dana", ["commercial"]), "L043": ("exhausted", "eddie", ["tired"]),
    "L044": ("exhausted", "dana", ["breathe", "demand"]), "L045": ("serious", "cam", ["break"]),
    "L046": ("deadpan", "tyson", ["hugging", "fighting"]), "L047": ("deadpan_happy", "joshua", ["first", "deal"]),
    "L048": ("salesman", "dana", ["rematch", "fifty"]), "L049": ("smug", "eddie", ["sixty"]),
    "L050": ("indignant", "dana", ["bin"]), "L051": ("smug", "eddie", ["sold", "fight"]),
    "L052": ("proud", "cam", ["round", "draw"]), "L053": ("salesman", "dana", ["unfinished", "immediate"]),
    "L054": ("smug", "eddie", ["pay", "view"]), "L055": ("deadpan", "tyson", ["still"]),
    "L056": ("resigned", "joshua", ["supporting", "towels"]), "L057": ("flat", "dana", ["back", "normal"]),
    "L058": ("annoyed", "eddie", ["bigger"]), "L059": ("salesman", "dana", ["premium", "sponsor"]),
}
BASE = {"eddie": (-0.1, 0.1), "dana": (-0.45, -0.1), "tyson": (0.1, 0.25), "joshua": (-0.05, 0.0),
        "announcer": (0.1, 0.0), "referee": (-0.2, 0.0), "attendant": (-0.25, -0.2), "security": (-0.35, -0.05)}
bin_dir = ("dir", -0.6, 0.45, -0.15)
GAZE = {
    "dana": [(m("faceoff"), m("bell2"), "eddie"),
             (m("trolley"), m("look_cam") - 0.05, "attendant"), (m("look_cam"), le("L007") + 0.3, "cam"),
             (m("bump"), m("tumble"), "cam"), (m("glance"), m("glance") + 0.5, "eddie")],
    "eddie": [(m("faceoff"), m("bell2"), "dana"),
              (m("dart"), m("dart") + 0.14, bin_dir), (m("dart") + 0.14, m("dart") + 0.28, "dana"),
              (m("dart") + 0.28, m("dart") + 0.42, "security"), (m("dart") + 0.42, ls("L022"), "dana"),
              (m("surprise"), m("c_list"), ("dir", 0.0, -0.1, 0.0)), (le("L038") - 1.4, le("L038"), "cam")],
    "security": [(m("lid"), ls("L011"), "down")],
    "joshua": [(m("c_aj") - 0.2, m("c_fury4"), "down")],
    "referee": [(m("bell"), m("c_ann4"), "eddie")],
    "tyson": [(m("landed"), m("c_aj"), "down")],
}
EXPR = {
    "dana": [(m("faceoff"), m("ex1"), -0.9, -0.35, 0.2), (m("ex1") + 0.3, m("ex1") + 1.5, 1.0, -0.4, 0.05),
             (m("ex3a"), m("ex3b"), 0.7, -0.2, 0.05), (m("ex3d"), m("ex3d") + 1.4, -1.0, -0.5, 0.2),
             (m("ex3d") + 1.4, m("ex3e") + 1.0, 0.9, -0.3, 0.1), (m("ex3e"), m("c_cl1"), 0.2, -0.4, 0.3),
             (m("bell2") + 0.3, m("arms") + 1.8, 0.4, 0.8, 0.2),(m("bump"), m("tumble") + 0.6, 1.0, -0.3, 0.1), (m("surprise"), m("c_list"), 0.95, -0.15, 0.2),
             (m("c_trolley"), m("climb"), -0.4, -0.2, 0.3)],
    "eddie": [(m("faceoff"), m("ex1"), -0.9, -0.3, 0.2), (m("ex2") + 0.3, ls("L040"), 1.0, -0.45, 0.05),
              (m("ex3b") + 0.4, m("ex3b") + 1.2, 0.85, -0.55, 0.05), (m("ex3c") + 0.6, m("ex3c") + 1.2, 0.9, -0.2, 0.05),
              (m("ex3d"), m("ex3d") + 1.4, -1.0, -0.5, 0.2), (m("ex3d") + 1.4, m("ex3e") + 1.0, 0.9, -0.3, 0.1),
              (m("ex3e"), m("c_cl1"), 0.2, -0.4, 0.3), (m("bell2") + 0.3, m("arms") + 1.8, 0.4, 0.8, 0.2),
              (m("surprise"), m("c_list"), 1.0, -0.2, 0.3), (m("c_eddie"), m("dart") + 0.4, -0.7, -0.3, 0.3)],
    "security": [(m("lid"), ls("L011"), 0.4, -0.15, 0.3)],
}
NOBLINK = {"dana": [(m("look_cam"), le("L007") + 0.2), (m("bump"), m("tumble"))],
           "eddie": [(m("dart"), ls("L022"))]}
NODS = {"tyson": [(ls("L033") + 0.2, 1, 3.0)], "attendant": [(le("L013") - 0.2, 1, 2.0)]}


def hold_shapes(track, must=("MBP", "FV")):
    """cartoon lip sync: every mouth shape held at least 2 frames (a 1-frame shape takes its neighbour's), and a
    mouth that would snap shut for 1-2 frames between two open shapes stays open (no chatter)"""
    tr = list(track)
    n = len(tr)
    i = 0
    while i < n:
        j = i
        while j + 1 < n and tr[j + 1] == tr[i]:
            j += 1
        L = j - i + 1
        if tr[i] == "REST" and L <= 2 and 0 < i and j + 1 < n and tr[i - 1] != "REST" and tr[j + 1] != "REST":
            for q in range(i, j + 1):
                tr[q] = tr[i - 1] if tr[i - 1] not in must else tr[j + 1]
        elif L == 1 and tr[i] not in must and 0 < i < n - 1 and tr[i] != "REST":
            tr[i] = tr[i - 1] if tr[i - 1] != "REST" else tr[i + 1]
        i = j + 1
    return tr


PERF = Performance(TL, L, WHO, SPK, META, lambda lid: ep.path("lines", f"{lid}.wav"), base=BASE, gaze=GAZE,
                   expr=EXPR, nods=NODS, noblink=NOBLINK, cuts=[s["t"] for s in SHOTS],
                   rest_target={"announcer": "cam", "referee": "cam"})
for _w in WHO:
    PERF.VIS[_w] = hold_shapes(PERF.VIS[_w])

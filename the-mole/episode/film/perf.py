"""The acting: each line's delivery, who it is said to and its stressed words; the reactions between lines (the
hedge, the slurp, the stare, the hang-up, the sigh, the shock, the long hold, the strain, the sleep, Omar frozen).
Talking heads play to the lens; the rows in the office play across to each other. See studio/film/perf.py."""
import json

from studio.film import ep
from studio.film.perf import Performance
from studio.film.shots import Marks
from film.direction import SHOTS
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt = T.m, T.ls, T.le, T.wt

WHO = ["licho", "wilcox", "omar"]
SPK = {"licho": "licho", "wilcox": "wilcox"}
TAGS = dict(whisper=(0.2, -0.05), triumphant=(-0.5, 0.35), shocked=(1.0, -0.3), straining=(-0.9, -0.5),
            panicking=(0.9, -0.2), sincere=(0.4, 0.15), sad=(0.55, -0.45), tender=(0.4, 0.5))

META = {
    "L004": ("whisper", "cam", ["shhh", "not"]),
    "L005": ("proud", "cam", ["defender", "smell", "danger"]),
    "L006": ("whisper", "cam", ["building", "leeds"]),
    "L007": ("serious", "cam", ["jason", "wilcox", "career"]),
    "L008": ("indignant", "cam", ["blackburn", "won", "united"]),
    "L009": ("cold", "cam", ["leeds", "explain"]),
    "L010": ("frustrated", "cam", ["city"]),
    "L011": ("casual", "cam", ["southampton", "fine"]),
    "L012": ("serious", "cam", ["not", "criminal", "record"]),
    "L013": ("disbelieving", "cam", ["white", "why", "jason", "always"]),
    "L014": ("deadpan", "cam", ["united", "claps"]),
    "L015": ("whisper", "cam", ["leeds", "toilet", "screaming"]),
    "L019": ("whisper", "cam", ["target", "office", "white", "course"]),
    "L020": ("salesman", "cam", ["absolutely", "aligned", "red", "one", "vision", "process"]),
    "L024": ("tender", "cam", ["leeds", "lads"]),
    "L025": ("shocked", "cam", ["madre"]),
    "L026": ("energised", "cam", ["yes", "get", "marching", "together"]),
    "L027": ("triumphant", "wilcox", ["knew"]),
    "L029": ("panicking", "licho", ["lisandro", "isn't", "looks"]),
    "L030": ("deadpan", "wilcox", ["leeds"]),
    "L031": ("salesman", "licho", ["scouting", "data", "opposition", "immersing", "enemy"]),
    "L032": ("sarcastic", "wilcox", ["their", "shirt"]),
    "L033": ("defensive", "licho", ["method", "modern", "plant"]),
    "L034": ("cold", "wilcox", ["turn", "around"]),
    "L035": ("disbelieving", "wilcox", ["signed", "own"]),
    "L036": ("sad", "licho", ["difficult", "me"]),
    "L037": ("angry", "down", ["never", "penalty", "ref"]),
    "L038": ("cold", "wilcox", ["say"]),
    "L039": ("innocent", "licho", ["what"]),
    "L040": ("firm", "wilcox", ["leeds", "are", "rubbish"]),
    "L041": ("straining", "licho", ["leeds", "really", "coached", "fair"]),
    "L042": ("sad", "cam", ["cannot", "sick"]),
    "L044": ("confident", "cam", ["slide", "commitment", "percentage", "eleven", "season"]),
    "L045": ("dry", "wilcox", ["what"]),
    "L046": ("awkward", "licho", ["don't", "baseline"]),
    "L048": ("triumphant", "cam", ["seventy", "powerpoint", "bielsa", "leeds", "case", "closed"]),
    "L049": ("sincere", "cam", ["bleed", "red", "always"]),
    "L050": ("awkward", "cam", ["white", "medical"]),
    "L051": ("proud", "cam", ["top", "omar", "know"]),
    "L052": ("energised", "omar", ["omar", "mole"]),
    "L053": ("resigned", "omar", ["knew"]),
    "L056": ("tender", "down", ["vamos", "alexis", "hermano"]),
    "L057": ("triumphant", "licho", ["knew"]),
    "L058": ("panicking", "wilcox", ["argentina", "different"]),
    "L059": ("indignant", "licho", ["liverpool", "lisandro"]),
    "L060": ("innocent", "wilcox", ["red", "shirt"]),
    "L062": ("whisper", "cam", ["shhh", "not"]),
}
BASE = dict(licho=(-0.35, -0.1), wilcox=(0.05, 0.0), omar=(0.0, 0.0))
DOWN = ("dir", 0.0, 0.85, 0.0)
SIDE_L = ("dir", -0.9, 0.0, -0.35)
SIDE_R = ("dir", 0.9, 0.0, 0.35)
GAZE = {
    "licho": [(m("slurp"), m("slurp") + 0.5, SIDE_L), (m("slurp") + 0.5, m("cut_title"), SIDE_R),
              (m("cut_compose"), m("cut_compose") + 1.0, DOWN),
              (m("cut_plantcu"), le("L019"), SIDE_R),                    # watching the office door
              (m("cut_eyes"), m("cut_goal"), SIDE_L),                    # watching him
              (m("cut_l056") - 0.3, le("L056") + 0.4, DOWN),             # the tablet
              (m("cut_night"), m("cut_night") + 1.2, SIDE_L), (m("cut_night") + 1.2, m("cut_night") + 2.4, SIDE_R),
              (m("cut_hedges"), ls("L062") - 0.2, SIDE_R)],
    "wilcox": [(m("hangup") + 0.2, m("cut_lock"), SIDE_L),                # the door
               (m("cut_blinds"), m("cut_clock"), SIDE_L),
               (le("L023"), m("cut_laptop"), ("dir", 0.0, -0.3, 0.0)),    # eyes to heaven: relief
               (m("cut_pray"), le("L024") + 0.3, DOWN),
               (m("cut_w037") - 0.2, le("L037") + 0.2, ("dir", -0.6, 0.6, -0.2)),
               (m("cut_w044"), le("L044"), ("dir", 0.5, 0.5, 0.2)),       # reading his clipboard
               (m("cut_plant2"), m("cut_w057"), SIDE_R)],
    "omar": [(m("cut_omar"), m("cut_omar") + 0.9, "cam"), (m("cut_omar") + 0.9, m("cut_omar") + 1.6, SIDE_L),
             (m("cut_omar") + 1.6, m("cut_l053"), "cam"), (m("cut_omar2"), m("cut_night"), SIDE_L)],
}
EXPR = {
    "licho": [(m("cut_bino"), le("L004"), -0.6, -0.1, 0.2),
              (m("cut_compose"), ls("L011"), 0.3, -0.4, 0.2),              # composing himself
              (le("L011"), ls("L012"), 0.3, 0.45, 0.1),                     # Southampton is fine
              (le("L017"), m("cut_corr"), -0.8, -0.15, 0.3),                # the stare
              (le("L025"), m("cut_goal"), 1.0, -0.3, 0.05),
              (m("scream2"), m("scream3"), 1.0, -0.5, 0.03),
              (m("cut_point"), ls("L038"), -0.9, -0.2, 0.2),                # the long hold
              (m("cut_ceo") - 0.1, le("L052") + 0.1, 0.9, 0.6, 0.05),       # bursting in, delighted
              (le("L056"), m("cut_plant2") + 0.8, 0.4, 0.7, 0.2),           # loving it
              (m("scream"), m("cut_l058"), 1.0, -0.5, 0.03),
              (le("L060"), m("cut_hedges"), 0.4, 0.2, 0.1)],
    "wilcox": [(m("hangup"), m("cut_lock"), -0.4, -0.1, 0.2),
               (wt("L023", "breathe") + 1.0, m("cut_laptop"), 0.4, 0.9, 0.6),   # bliss
               (m("scream1"), m("freeze"), 1.0, -0.5, 0.03),
               (m("cut_back"), m("cut_l035"), 0.3, 0.3, 0.2),
               (m("cut_strain"), ls("L041") + 0.9, -0.9, -0.6, 0.2),
               (ls("L041") + 0.9, le("L041") + 0.2, 0.6, 0.75, 0.15),         # "...really well coached": relief
               (m("scream"), m("cut_l058"), 1.0, -0.5, 0.03),
               (m("cut_spidey"), m("cut_hedges"), -0.6, -0.2, 0.05)],
    "omar": [(m("cut_omar"), m("cut_night"), 0.9, -0.15, 0.05)],
}
NODS = {"licho": [(wt("L012", "record"), 2, 3.0), (wt("L048", "closed"), 2, 3.5), (le("L030") - 0.2, 1, 3.0)],
        "wilcox": [(wt("L020", "absolutely"), 2, 2.5), (wt("L049", "always"), 1, 2.5)]}
TURN = {"licho": [(wt("L013", "why") - 0.05, le("L013"), 0.0, 6.0), (ls("L042"), le("L042"), -0.15, -4.0),
                  (ls("L060"), le("L060"), 0.0, 7.0)],
        "wilcox": [(ls("L036"), le("L036"), 0.0, -6.0), (ls("L050"), le("L050"), 0.2, 4.0),
                   (m("cut_strain"), ls("L041") + 0.9, 0.0, -3.0)]}
SHUT = {"licho": [(m("cut_compose") + 0.1, m("cut_compose") + 0.9),
                  (m("cut_asleep") + 0.2, m("cut_int2") + 0.05)],
        "wilcox": [(wt("L023", "breathe") + 1.2, wt("L023", "breathe") + 2.3)]}
FORCED = {"wilcox": [m("cut_strain") + 0.5, m("cut_strain") + 0.8, m("cut_strain") + 1.05, ls("L041") + 0.5],
          "licho": [le("L030") + 0.2, le("L017") + 0.9]}
NOBLINK = {"licho": [(m("cut_tutorial"), m("cut_corr")), (m("cut_point"), le("L038") + 0.2),
                     (m("clap"), ls("L015"))],
           "omar": [(m("cut_omar"), m("cut_l053"))]}
BODY = {
    "licho": [(ls("L015") - 0.1, le("L015"), 0.6, 0.0, 0.3),               # leaning in to whisper
              (m("cut_asleep") + 0.2, m("cut_int2"), -0.2, 0.7, 0.8),     # slumped asleep
              (ls("L053") - 0.2, le("L053") + 0.4, -0.2, 0.5, 0.3)],
    "wilcox": [(wt("L023", "breathe") + 1.0, m("cut_laptop"), -0.15, 0.3, 0.5),   # the sigh
               (m("cut_pray"), le("L024"), 0.6, 0.0, 0.3),
               (ls("L026"), le("L026"), -0.3, -0.6, 0.1),                  # up on his toes
               (ls("L036"), le("L036"), -0.1, 0.5, 0.3)],
}
REST = dict(licho="cam", wilcox="cam", omar="cam")

PERF = Performance(TL, L, WHO, SPK, META, lambda lid: ep.path("lines", f"{lid}.wav"), base=BASE, gaze=GAZE,
                   expr=EXPR, nods=NODS, turn=TURN, body=BODY, forced=FORCED, noblink=NOBLINK, rest_target=REST,
                   tags=TAGS, shut=SHUT, cuts=[s["t"] for s in SHOTS])

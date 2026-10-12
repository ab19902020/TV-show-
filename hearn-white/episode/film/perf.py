"""The acting of The Undercard (v5): whom each line is said to, its delivery (studio/film/perf.py TAGS) and the words
that get a nod; the listeners' attention moves on an event, not at random (eye dart, then the head): the guard
looking from the trolley to her face, Eddie finding the shoe, the towel, the bin and then Dana, the two promoters
realising what they agreed to, Dana peering up from his over-the-top duck, the exhausted look after the sit-down.
Mouths come from the recordings (lip sync a frame ahead)."""
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
    "L001": ("proud", "cam", ["fury", "joshua", "biggest", "improved"]), "L002": ("flat", "eddie", ["added"]),
    "L003": ("pleased", "security", ["nobody", "banned"]), "L004": ("dry", "eddie", ["disguise"]),
    "L005": ("smug", "security", ["bald", "furious", "parking", "know"]),
    "L006": ("indignant", "cam", ["banned", "wasn't", "fucking"]),
    "L007": ("matter", "attendant", ["inside"]), "L008": ("flat", "dana", ["staff"]),
    "L009": ("flat", "attendant", ["banned"]), "L010": ("flat", "dana", ["no"]),
    "L011": ("quiet", "attendant", ["five"]), "L012": ("matter", "dana", ["shoes", "clean"]),
    "L013": ("indignant", "attendant", ["who"]), "L014": ("dry", "dana", ["yes", "five", "free"]),
    "L015": ("flat", "attendant", ["there"]), "L016": ("flat", "security", ["towels"]),
    "L017": ("smug", "cam", ["best", "fucking", "business"]), "L018": ("irritated", "dana", ["shut", "towel"]),
    "L019": ("casual", "dana", ["fuck", "delivered", "promoter"]), "L020": ("resigned", "tyson", ["help"]),
    "L021": ("deadpan", "dana", ["forty", "tumble"]), "L022": ("deadpan", "dana", ["card"]),
    "L023": ("deadpan", "joshua", ["no", "floor"]), "L024": ("disbelieving", "dana", ["why", "laundry"]),
    "L025": ("indignant", "eddie", ["security's", "shit"]), "L026": ("dry", "dana", ["pillowcase"]),
    "L027": ("smug", "eddie", ["still", "inside"]), "L028": ("defensive", "eddie", ["defence", "laundry"]),
    "L029": ("cold", "security", ["fucking", "parachutes"]), "L030": ("flat", "dana", ["five"]),
    "L031": ("firm", "dana", ["out", "main", "cage"]), "L032": ("firm", "eddie", ["ring", "yourself"]),
    "L033": ("confident", "dana", ["fine"]), "L034": ("awkward", "dana", ["bigger", "shorter", "elbows", "wrestling"]),
    "L035": ("obvious", "eddie", ["boxing", "eddie"]), "L036": ("pleased", "dana", ["good", "equally"]),
    "L037": ("sarcastic", "eddie", ["biggest", "boxing"]), "L038": ("salesman", "dana", ["still", "punched", "evening"]),
    "L039": ("dry", "eddie", ["you"]), "L040": ("awkward", "dana", ["reconsidering"]),
    "L041": ("quiet", "tyson", ["stop"]), "L042": ("deadpan_happy", "eddie", ["miss", "promoters", "money"]),
    "L043": ("proud", "cam", ["ladies", "special", "additional"]),
    "L044": ("proud", "cam", ["red", "expenses", "eddie", "hearn"]),
    "L045": ("proud", "cam", ["blue", "laundry", "dana", "white"]),
    "L046": ("serious", "cam", ["holding", "wrestling", "negotiating"]), "L047": ("concerned", "referee", ["generally"]),
    "L048": ("frustrated", "cam", ["go", "podcast"]), "L049": ("sarcastic", "eddie", ["jab's", "shit"]),
    "L050": ("defensive", "dana", ["opening"]), "L051": ("annoyed", "eddie", ["hands"]),
    "L052": ("indignant", "dana", ["are"]), "L053": ("obvious", "eddie", ["chin"]),
    "L054": ("proud", "dana", ["very", "important"]), "L055": ("indignant", "dana", ["actually", "hit"]),
    "L056": ("obvious", "eddie", ["fight"]), "L057": ("indignant", "dana", ["photos"]),
    "L058": ("exhausted", "eddie", ["tired"]), "L059": ("exhausted", "dana", ["building", "anticipation"]),
    "L060": ("quiet", "eddie", ["draw", "sixty"]), "L061": ("exhausted", "dana", ["sixty"]),
    "L062": ("smug", "eddie", ["me"]), "L063": ("firm", "dana", ["rather", "punch"]),
    "L064": ("salesman", "dana", ["fifty", "final"]), "L065": ("serious", "eddie", ["break"]),
    "L066": ("concerned", "referee", ["load"]), "L067": ("deadpan", "tyson", ["holding"]),
    "L068": ("deadpan_happy", "joshua", ["partnership", "lawyer"]),
    "L069": ("proud", "cam", ["round", "draw"]), "L070": ("salesman", "cam", ["unfinished", "rematch"]),
    "L071": ("salesman", "cam", ["pay", "view"]), "L072": ("deadpan", "tyson", ["still", "fighting"]),
    "L073": ("resigned", "joshua", ["supporting", "towels"]), "L074": ("flat", "dana", ["return", "grand"]),
    "L075": ("indignant", "attendant", ["five"]), "L076": ("dry", "dana", ["pay", "view"]),
}
BASE = {"eddie": (-0.1, 0.1), "dana": (-0.45, -0.1), "tyson": (0.1, 0.25), "joshua": (-0.05, 0.0),
        "announcer": (0.1, 0.0), "referee": (-0.2, 0.0), "attendant": (-0.25, -0.2), "security": (-0.35, -0.05)}
bin_dir = ("dir", 0.6, 0.6, 0.15)
shoe_dir = ("dir", 0.15, 0.85, 0.05)
towel_dir = ("dir", 0.5, 0.5, 0.15)
rec = m("recog")
GAZE = {
    "security": [(m("c_stare") - 0.1, m("c_stare") + 0.35, "down"), (m("c_stare") + 0.35, m("giveway") + 0.4, "attendant"),
                 (ls("L015") - 0.2, le("L015") + 0.3, "down")],
    "attendant": [(m("c_two"), m("c_pivot") - 0.05, ("dir", -0.8, 0.1, -0.3)), (m("c_stare"), m("giveway") + 0.4, "security"),
                  (m("c_lid"), le("L018"), "down")],
    "eddie": [(m("c_eddie") + 0.9, rec, shoe_dir), (rec, rec + 0.2, towel_dir), (rec + 0.2, rec + 0.4, bin_dir),
              (rec + 0.4, ls("L024"), "dana"), (m("silence"), m("c_reg_e") + 0.6, ("dir", 0.0, -0.1, 0.0)),
              (m("bounce"), m("probe"), "dana"), (m("look"), m("bell2") + 0.3, "dana"),
              (m("tape") + 0.1, m("admire"), ("dir", -0.6, 0.0, -0.2)), (m("pays") + 0.3, m("pays") + 1.6, "attendant")],
    "dana": [(m("collar"), ls("L006"), ("dir", 0.7, 0.0, 0.2)), (m("probe") + 0.6, m("probe") + 1.6, ("dir", -0.6, -0.8, -0.2)),
             (m("silence"), m("c_reg_d") + 0.6, ("dir", 0.0, -0.1, 0.0)), (m("bounce"), m("probe"), "eddie"),
             (m("look"), m("bell2") + 0.3, "eddie"), (m("c_inbin"), m("c_inbin") + 0.9, ("dir", 0.0, -0.7, 0.0))],
    "joshua": [(m("c_aj") - 0.2, le("L023"), "down")],
    "tyson": [(m("land"), m("c_aj"), "down")],
    "referee": [(m("bell"), m("c_ann4"), "eddie"), (m("look"), m("helpup") + 0.5, "down")],
}
EXPR = {
    "eddie": [(m("c_eddie") + 1.0, ls("L024"), 0.75, -0.35, 0.2), (m("silence"), m("c_reg_e") + 0.6, 0.95, -0.4, 0.3),
              (m("pays") + 0.2, m("pays") + 1.6, -0.6, -0.4, 0.2), (m("tap") + 1.2, ls("L051"), 0.8, -0.45, 0.1),
              (m("counter") + 0.6, ls("L055"), 0.95, -0.5, 0.1), (m("windup"), m("clash"), -0.9, -0.5, 0.1),
              (m("clash"), m("sit"), 0.9, -0.3, 0.1), (m("sit"), m("helpup"), 0.3, -0.4, 0.3),
              (m("ropes2"), m("clinch"), 0.95, -0.4, 0.1)],
    "dana": [(m("silence"), m("c_reg_d") + 0.6, 0.9, -0.35, 0.3), (m("probe") + 0.4, m("c_da2"), 0.95, -0.3, 0.1),
             (m("windup"), m("clash"), -0.9, -0.5, 0.1), (m("clash"), m("sit"), 0.9, -0.3, 0.1),
             (m("sit"), m("helpup"), 0.3, -0.4, 0.3), (m("card"), ls("L075"), 0.9, -0.4, 0.2)],
    "security": [(m("c_stare"), m("giveway") + 0.4, 0.3, -0.15, 0.3)],
    "attendant": [(m("c_stare"), m("giveway") + 0.4, -0.3, -0.1, 0.3)],
}
NOBLINK = {"eddie": [(rec, ls("L024"))], "attendant": [(m("c_stare"), m("giveway"))],
           "security": [(m("c_stare") + 0.35, m("giveway"))], "dana": [(m("look"), m("bell2"))]}
NODS = {"tyson": [(le("L021") - 0.2, 1, 2.0)], "attendant": [(le("L014") - 0.2, 1, 2.0), (le("L076") - 0.2, 1, 2.0)],
        "joshua": [(le("L067") - 0.2, 1, 2.0)]}


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
        L_ = j - i + 1
        if tr[i] == "REST" and L_ <= 2 and 0 < i and j + 1 < n and tr[i - 1] != "REST" and tr[j + 1] != "REST":
            for q in range(i, j + 1):
                tr[q] = tr[i - 1] if tr[i - 1] not in must else tr[j + 1]
        elif L_ == 1 and tr[i] not in must and 0 < i < n - 1 and tr[i] != "REST":
            tr[i] = tr[i - 1] if tr[i - 1] != "REST" else tr[i + 1]
        i = j + 1
    return tr


PERF = Performance(TL, L, WHO, SPK, META, lambda lid: ep.path("lines", f"{lid}.wav"), base=BASE, gaze=GAZE,
                   expr=EXPR, nods=NODS, noblink=NOBLINK, cuts=[s["t"] for s in SHOTS],
                   rest_target={"announcer": "cam", "referee": "cam"})
for _w in WHO:
    PERF.VIS[_w] = hold_shapes(PERF.VIS[_w])

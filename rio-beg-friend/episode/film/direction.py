"""The shot list, portrait 9:16 (EP_RES=1080x1920). One set: the director of football's office (plate O), Wilcox in
his chair behind the desk, Rio fussing round him. Every shot is props.scene: the office at true scale with the
actors placed by their feet (all the drawings come off one sheet, so one scale k fits all), drawings switching on the
words, the desk in front, the tea once it is served, then hearts, the title and word-by-word captions."""
import json

from studio.film import ep
from studio.film.shots import Marks, finish, insert, shot_at as _shot_at
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt = T.m, T.ls, T.le, T.wt

PLATES = {"O": "club/wilcox-office-portrait"}
DESK = [(0, 952), (941, 952), (941, 1672), (0, 1672)]
OCCL = {"O": {"desk": [DESK]}}
EYES = {}
K = 2.1                                   # plate px per sheet px
CHAIR_X, LAP_Y = 588, 960                 # the office chair; the desk top his lap sits at
RIO, WIL = "rio-ferdinand:bf-", "jason-wilcox:bf-"
W_BASE = (CHAIR_X, LAP_Y + (340 - 232) * K)        # Wilcox's chair wheels (hidden by the desk)
R_BASE_Y = LAP_Y + (404 - 215) * K                 # Rio standing behind the desk, waist at the desk top
RUB_BASE = (CHAIR_X + 22, LAP_Y + (594 - 470) * K)


def wil(keys, x=None):
    return dict(who="wilcox", keys=[(t, WIL + d) for t, d in keys], x=[(0, x or W_BASE[0])], y=W_BASE[1])


def rio(keys, x, y=None, mirror=False, walk=None):
    return dict(who="rio", keys=[(t, RIO + d) for t, d in keys], x=x if isinstance(x, list) else [(0, x)],
                y=y or R_BASE_Y, mirror=mirror, walk=walk)


def rub(keys):
    return dict(who="rio", keys=[(t, RIO + d) for t, d in keys], x=[(0, RUB_BASE[0])], y=RUB_BASE[1])


def S(t, cams, acts, **kw):
    return insert(t, "scene", cams=cams, acts=acts, **kw)


SHOTS = finish([
    # Wilcox, king of his office. Rio arrives with tea and biscuits: "I played with Jason Wilcox at Leeds..."
    S(0.0, [(0.0, (470, 836, 1.0)), (ls("L002"), (520, 780, 1.12))],
      [rio([(0, "tray"), (wt("L001", "what") - 0.1, "tray-present")], [(0.0, 1250), (1.7, 800)], walk=(0.0, 1.7)),
       wil([(0, "smug")])], title=True),
    # "Became one of my closest friends at Leeds." Serving it, bowing
    S(ls("L002") - 0.08, [(ls("L002"), (640, 720, 1.4)), (le("L002"), (630, 730, 1.48))],
      [rio([(0, "serve")], 790, mirror=True), wil([(0, "eyesup")])], tea=le("L002") - 0.35),
    # "...wonderful person, great human being, trustworthy." The shoulder rub
    S(ls("L003") - 0.1, [(ls("L003"), (600, 660, 1.25)), (le("L003"), (600, 620, 1.42))],
      [rub([(0, "rub1"), (wt("L003", "wonderful") - 0.08, "rub2"), (wt("L003", "trustworthy") - 0.08, "rub3")])],
      hearts=(wt("L003", "wonderful"), le("L003") + 0.4), tea=0),
    # "Straight as you like..." Rio to us, Wilcox beaming beside him
    S(ls("L004") - 0.1, [(ls("L004"), (720, 720, 1.8)), (wt("L004", "decision") - 0.1, (730, 700, 1.9))],
      [wil([(0, "smug")]), rio([(0, "explain"), (wt("L004", "knee") - 0.08, "point"), (wt("L004", "we'll") - 0.08, "open")], 820)],
      tea=0),
    # "...I'm gonna make a decision just based on one little, simple little detail" - Wilcox: me? never
    S(wt("L004", "decision") - 0.1, [(0, (588, 690, 2.1)), (wt("L004", "or"), (588, 680, 2.25))],
      [wil([(0, "shrug")])], tea=0),
    # "...or, this hasn't gone our way, so that's it."
    S(wt("L004", "or") - 0.05, [(0, (760, 720, 1.9)), (le("L004"), (760, 710, 1.98))],
      [wil([(0, "smug")]), rio([(0, "open")], 820)], tea=0),
    # "I think it would have been a culmination of things..." chin in hand; "...given Ruben time." explaining
    S(ls("L005") - 0.1, [(0, (650, 760, 1.35)), (le("L005"), (660, 730, 1.5))],
      [wil([(0, "eyesup")]), rio([(0, "think"), (wt("L005", "i", 2) - 0.08, "explain")], 830)], tea=0),
    # "But he's somebody, whenever I spoke to him..." back on the shoulders, thumbs up
    S(ls("L006") - 0.1, [(0, (600, 640, 1.35)), (le("L006"), (600, 600, 1.55))],
      [rub([(0, "rub2"), (wt("L006", "complete") - 0.08, "rub1")])],
      hearts=(ls("L006") + 0.3, le("L006")), tea=0),
    # "And I think the longer this went on, forget results, he wasn't seeing"
    S(ls("L007") - 0.1, [(0, (790, 720, 2.0)), (le("L007"), (790, 710, 2.1))],
      [rio([(0, "pockets"), (wt("L007", "forget") - 0.08, "point")], 820)], tea=0),
    # "...a true reflection of what he feels Man United should be playing like." Wilcox, blissful
    S(ls("L008") - 0.1, [(0, (588, 700, 2.1)), (wt("L008", "and"), (588, 680, 2.3))], [wil([(0, "bliss")])], tea=0),
    # "And I think that's a big part of the decision why the manager's gone as well." The rub, to the end card
    S(wt("L008", "and") - 0.08, [(0, (590, 640, 1.3)), (m("end_card"), (560, 640, 1.15))],
      [rub([(0, "rub3")])], hearts=(wt("L008", "and") + 0.4, TL["total"]), tea=0, best=m("end_card")),
], TL["total"])

TITLE = ()
TAGLINE = ()
CAPTIONS = []
WHIPS = []
DRAW = {d: d for s in SHOTS for a in s["acts"] for _, d in a["keys"]}


def shot_at(t):
    return _shot_at(SHOTS, t)

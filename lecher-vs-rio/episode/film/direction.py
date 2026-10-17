"""The shot list: a YouTube beef, cut on the dialogue edit (timeline.py).

Saeed is live on his channel at his fan-channel desk (plate Y): every shot of him is his stream, with the live
chat down the right and the player chrome round it (props.compose). Rio replies from his podcast studio (plate
P): first as a post that types itself out while he reads it, then as a video reply; while Saeed reacts, Rio's
clip plays in the corner of the stream. The last line is the two of them side by side, then a silence that goes
on too long, then the post that ends it.

Every shot is an insert drawn by props.compose: it renders the inner shot(s) (studio.film.render singles) and puts
the stream, the post, the split screen and the gags over them."""
import json

from studio.film import ep
from studio.film.shots import Marks, finish, insert, shot_at as _shot_at, single
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt = T.m, T.ls, T.le, T.wt

PLATES = {"Y": "lecher-vs-rio/fan-channel-desk", "P": "tv-and-media/podcast-studio", "OT": "stadiums/old-trafford"}
# what is in front of Saeed on his desk (1x plate px of Y): the desk top and its front, the mug, the pen pot
DESK = [(180, 642), (230, 609), (400, 593), (640, 586), (900, 581), (1150, 584), (1400, 596), (1470, 616),
        (1476, 650), (1462, 800), (1450, 830), (200, 840), (182, 700)]
MUG = [(1125, 560), (1170, 556), (1172, 612), (1126, 612)]
RED_MUG = [(646, 548), (722, 546), (724, 614), (646, 614), (628, 600), (626, 562)]   # his United mug, in front of him
PENS = [(1172, 548), (1228, 548), (1228, 614), (1172, 614)]
OCCL = {"Y": {"desk": [DESK, MUG, PENS]}}
EYES = {"saeed": dict(rio=(0.0, -0.02, 0.0)), "rio": dict(saeed=(0.0, -0.02, 0.0))}

S = "saeed-the-lecher:"
DESK_EDGE = 588                       # the desk's back rim under him (plate y)
CHAIR_X, CHAIR_TOP, ROOM_DESK = 705, 360, 590   # his gaming chair's centre and headrest top, the room's desk front


def room(ed, eye, table):
    """the room behind him and the desk in front, framed so he sits IN his chair: the chair centred behind him,
    its headrest just above his head, and the room's own desk exactly under the desk in front of him (one view of
    the plate for both, so they line up)"""
    top = eye[1] - 2.75 * ed                          # the headrest's top on screen (layout px)
    desk = eye[1] + table * ed                         # the desk's front edge on screen
    sc = (desk - top) / (ROOM_DESK - CHAIR_TOP)        # screen px per plate px
    z = sc / (1920 / 1672)
    cy = CHAIR_TOP + (540 - top) / sc
    cx = CHAIR_X - (eye[0] - 960) / sc
    return ("Y", cx, cy, z, 2.2), ("Y", "desk", cx, DESK_EDGE, z, 0.8)


def saeed(t, draw, ed=150.0, eye=(960, 430), table=2.55, push=(1.0, 1.04), **kw):
    """Saeed in his chair at his desk, on his webcam"""
    bg, fg = room(ed, eye, table)
    return single(t, "saeed", S + draw, bg, fg, ed=ed, eye=eye, table=table, push=push, drift=1.1, **kw)


def rio(t, draw="rio-ferdinand:mic", ed=96.0, eye=(960, 360), push=(1.0, 1.04), **kw):
    """Rio in his podcast studio, the chairs and shelves soft behind him"""
    return single(t, "rio", draw, ("P", 836, 330, 2.3, 4.2), None, ed=ed, eye=eye, table=0, push=push,
                  drift=0.8, **kw)


def C(t, inner, **kw):
    """a shot drawn by props.compose over its inner shot"""
    return insert(t, "compose", inner=inner, **kw)


def w(lid, word, k=1):
    return wt(lid, word, k)


MED = dict(ed=80, eye=(900, 390), table=4.1)        # a medium: the desk across his belly
CU = dict(ed=150, eye=(960, 430), table=2.55)        # close: the desk across his chest
SHOTS = finish([
    # the stream goes live; he leans into the webcam; "Rio Ferdinand mate..."
    C(0.0, saeed(0.0, "b-neutral", push=(1.25, 1.0), **CU), yt=True, live_in=0.0, chat="open",
      keys=[(0.0, "b-neutral"), (ls("L001") - 0.05, "b-head")]),
    # "...a microphone, a massive platform": jabbing at the lens; "...and millions of followers": palms up
    C(w("L001", "you've"), saeed(w("L001", "you've"), "pointing", push=(1.0, 1.05), **MED), yt=True,
      counter=(w("L001", "millions"), "RIO'S FOLLOWERS"),
      keys=[(w("L001", "you've"), "pointing"), (w("L001", "and") - 0.05, "explaining")]),
    # "But when it comes to the Glazers..." arms folded
    C(ls("L002"), saeed(ls("L002"), "crossarms", push=(1.0, 1.04), **MED), yt=True),
    # "...quieter than Old Trafford when we're two nil down." the angry face, pushing in
    C(w("L002", "quieter"), saeed(w("L002", "quieter"), "b-angry", push=(1.0, 1.1), **CU), yt=True),
    # Old Trafford, 2-0 down
    insert(m("cut_ot"), "old_trafford"),
    # Rio's reply: a post that types itself out as he reads it
    insert(m("cut_reply"), "post_rio"),
    # back on the stream, Rio's video in the corner: Saeed side-eyes it... "a bit of timber" - horror, a look down
    C(m("cut_pip1"), saeed(m("cut_pip1"), "b-confused", push=(1.0, 1.03), **CU), yt=True,
      pip=rio(m("cut_pip1")), keys=[(m("cut_pip1"), "b-confused"), (w("L004", "timber"), "b-scared")]),
    # Rio, full screen: "You've got tits for God's sake." - and he cracks up at his own joke
    C(m("cut_rio2"), rio(m("cut_rio2"), ed=104, push=(1.0, 1.1)), reply=True,
      keys=[(m("cut_rio2"), "rio-ferdinand:mic"), (m("rio_laugh") - 0.1, "rio-ferdinand:laugh")]),
    # "TITS!"
    C(m("cut_tits"), saeed(m("cut_tits"), "b-shouting", ed=165, eye=(960, 420), table=2.5, push=(1.0, 1.12)),
      yt=True, crash=ls("L006"), shake=(ls("L006"), le("L006") + 0.1), chat="tits"),
    # "Brilliant Rio, at least mine are visible." - and the smug side-eye
    C(m("cut_smug"), saeed(m("cut_smug"), "b-head", push=(1.0, 1.04), **CU), yt=True,
      pip=rio(m("cut_smug"), "rio-ferdinand:folded", ed=96),
      keys=[(m("cut_smug"), "b-head"), (le("L007") + 0.05, "b-suspicious")]),
    # Rio, stung
    C(m("cut_ouch"), rio(m("cut_ouch"), "rio-ferdinand:folded", ed=110, push=(1.0, 1.06)), reply=True),
    # "We've had twenty years of the Glazers" (jabbing) "taking the piss" (the angry face)
    C(m("cut_rant"), saeed(m("cut_rant"), "pointing", push=(1.0, 1.04), **MED), yt=True,
      counter=(w("L008", "twenty"), "YEARS OF THE GLAZERS"),
      keys=[(m("cut_rant"), "pointing"), (w("L008", "taking") - 0.05, "explaining")]),
    # "...and you're doing body checks on me." - arms across the chest
    C(w("L008", "body") - 0.05, saeed(w("L008", "body") - 0.05, "crossarms", ed=88, eye=(910, 390), table=4.1,
                                       push=(1.06, 1.1)), yt=True, chat="body"),
    # "You're a pundit, not the bloody fashion police." - sirens on "police", then he glares
    C(m("cut_police"), saeed(m("cut_police"), "pointing", ed=84, eye=(880, 385), table=4.1, push=(1.0, 1.08)),
      yt=True, crash=w("L009", "police"), siren=(w("L009", "police") - 0.05, le("L009") + 0.4),
      keys=[(m("cut_police"), "pointing"), (le("L009") + 0.05, "crossarms")]),
    # "And if you're wondering" (chin in hand) "why I'm fat Rio," (straight to the lens)
    C(m("cut_fat"), saeed(m("cut_fat"), "thinking", push=(1.0, 1.04), **MED), yt=True,
      keys=[(m("cut_fat"), "thinking"), (w("L010", "why") - 0.05, "explaining")]),
    # "...watching United for the last decade has made me eat my feelings." - the plates pile up; then the sad face
    C(ls("L011") - 0.05, saeed(ls("L011") - 0.05, "b-neutral", ed=112, eye=(900, 410), table=3.0, push=(1.0, 1.03)),
      yt=True, plates=(w("L011", "watching"), w("L011", "feelings") + 0.3), chat="feelings",
      keys=[(ls("L011") - 0.05, "b-neutral"), (le("L011") + 0.1, "b-disgusted")]),
    # Rio: "That's not my fault."
    C(m("cut_rio3"), rio(m("cut_rio3"), "rio-ferdinand:shrug", ed=104, eye=(960, 380), push=(1.0, 1.05)), reply=True),
    # "Neither are the Glazers." - dead flat, slow push
    C(m("cut_deadpan"), saeed(m("cut_deadpan"), "b-angry", push=(1.0, 1.14), **CU), yt=True),
    # side by side: "Funny how we're both avoiding responsibility, eh, Rio?" - pleased with himself; the silence
    insert(m("cut_split"), "split", left=saeed(m("cut_split"), "b-head", ed=128, eye=(960, 450), table=2.7),
           right=rio(m("cut_split"), ed=92, eye=(960, 380)),
           lkeys=[(m("cut_split"), "b-head"), (le("L014") + 0.08, "b-happy"), (m("silence") + 0.5, "b-suspicious")]),
    # the post that ends it
    insert(m("cut_end"), "post_end"),
], TL["total"])
for _s in SHOTS:                                    # the inner shots run to the end of their outer shot
    for k in ("inner", "pip", "left", "right"):
        if _s.get(k):
            _s[k]["end"] = _s["end"]
            _s[k]["t"] = _s["t"]
            _s[k]["i"] = _s["i"] * 10 + ("inner", "pip", "left", "right").index(k)

TITLE = ()
TAGLINE = ()
CAPTIONS = []
WHIPS = []
DRAW = {}


def shot_at(t):
    return _shot_at(SHOTS, t)

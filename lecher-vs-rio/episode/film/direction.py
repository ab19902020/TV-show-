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
PENS = [(1172, 548), (1228, 548), (1228, 614), (1172, 614)]
OCCL = {"Y": {"desk": [DESK, MUG, PENS]}}
EYES = {"saeed": dict(rio=(0.0, -0.02, 0.0)), "rio": dict(saeed=(0.0, -0.02, 0.0))}

S = "saeed-the-lecher:"
DESK_EDGE = 588                       # the desk's back rim under him (plate y)
YBG = ("Y", 960, 420, 2.1, 3.2)       # his room behind him, a little soft (a webcam's depth of field)


def desk_fg(fz=2.6):
    return ("Y", "desk", 960, DESK_EDGE, fz, 1.0)


def saeed(t, draw, ed=150.0, eye=(960, 430), table=2.55, push=(1.0, 1.04), **kw):
    """Saeed at his desk on his webcam: the room behind him, the desk's edge across his chest"""
    return single(t, "saeed", S + draw, YBG, desk_fg(), ed=ed, eye=eye, table=table, push=push, drift=1.1, **kw)


def rio(t, draw="rio-ferdinand:mic", ed=96.0, eye=(960, 360), push=(1.0, 1.04), **kw):
    """Rio in his podcast studio, the chairs and shelves soft behind him"""
    return single(t, "rio", draw, ("P", 836, 330, 2.3, 4.2), None, ed=ed, eye=eye, table=0, push=push,
                  drift=0.8, **kw)


def C(t, inner, **kw):
    """a shot drawn by props.compose over its inner shot"""
    return insert(t, "compose", inner=inner, **kw)


def w(lid, word, k=1):
    return wt(lid, word, k)


HEAD = dict(draw="head", ed=150, table=2.6)
SHOTS = finish([
    # the stream goes live; he leans in; "Rio Ferdinand mate..."
    C(0.0, saeed(0.0, "head", ed=150, push=(1.25, 1.0)), yt=True, live_in=0.0, chat="open"),
    # "...you've got a microphone, a massive platform and millions of followers": pointing at the lens
    C(w("L001", "you've"), saeed(w("L001", "you've"), "pointing", ed=78, eye=(880, 370), table=5.8,
                                  push=(1.0, 1.05)), yt=True, counter=(w("L001", "millions"), "RIO'S FOLLOWERS")),
    # "But when it comes to the Glazers..." arms folded, the face of a man about to be proved right
    C(ls("L002"), saeed(ls("L002"), "crossarms", ed=78, eye=(910, 380), table=5.8, push=(1.0, 1.04)), yt=True),
    # "...quieter than Old Trafford when we're two nil down." push in on the angry face
    C(w("L002", "quieter"), saeed(w("L002", "quieter"), "angry", ed=150, push=(1.0, 1.08)), yt=True),
    # Old Trafford, 2-0 down
    insert(m("cut_ot"), "old_trafford"),
    # Rio's reply: a post that types itself out as he reads it
    insert(m("cut_reply"), "post_rio"),
    # back on the stream, Rio's video in the corner: Saeed checks himself out... "a bit of timber" - he looks down
    C(m("cut_pip1"), saeed(m("cut_pip1"), "confused", ed=150, push=(1.0, 1.03)), yt=True,
      pip=rio(m("cut_pip1")), keys=[(m("cut_pip1"), "confused"), (w("L004", "timber"), "scared")]),
    # Rio, full screen: "You've got tits for God's sake." - and he cracks up at his own joke
    C(m("cut_rio2"), rio(m("cut_rio2"), ed=104, push=(1.0, 1.1)), reply=True,
      keys=[(m("cut_rio2"), "rio-ferdinand:mic"), (m("rio_laugh") - 0.1, "rio-ferdinand:laugh")]),
    # "TITS!"
    C(m("cut_tits"), saeed(m("cut_tits"), "shouting", ed=165, push=(1.0, 1.12)), yt=True, crash=ls("L006"),
      shake=(ls("L006"), le("L006") + 0.1), chat="tits"),
    # "Brilliant Rio, at least mine are visible."
    C(m("cut_smug"), saeed(m("cut_smug"), "head", ed=150, push=(1.0, 1.04)), yt=True, pip=rio(m("cut_smug"),
                                                                                             "rio-ferdinand:folded",
                                                                                             ed=96)),
    # Rio, stung
    C(m("cut_ouch"), rio(m("cut_ouch"), "rio-ferdinand:folded", ed=110, push=(1.0, 1.06)), reply=True),
    # "We've had twenty years of the Glazers taking the piss..." - pointing
    C(m("cut_rant"), saeed(m("cut_rant"), "pointing", ed=78, eye=(880, 370), table=5.8, push=(1.0, 1.04)), yt=True,
      counter=(w("L008", "twenty"), "YEARS OF THE GLAZERS")),
    # "...and you're doing body checks on me." - arms across the chest
    C(w("L008", "body") - 0.05, saeed(w("L008", "body") - 0.05, "crossarms", ed=86, eye=(910, 370), table=5.8,
                                       push=(1.06, 1.1)), yt=True, chat="body"),
    # "You're a pundit, not the bloody fashion police." - sirens on "police"
    C(m("cut_police"), saeed(m("cut_police"), "pointing", ed=82, eye=(870, 360), table=5.8, push=(1.0, 1.08)),
      yt=True, crash=w("L009", "police"), siren=(w("L009", "police") - 0.05, le("L009") + 0.4)),
    # "And if you're wondering why I'm fat Rio," - thinking about it
    C(m("cut_fat"), saeed(m("cut_fat"), "thinking", ed=80, eye=(900, 380), table=5.8, push=(1.0, 1.04)), yt=True),
    # "...watching United for the last decade has made me eat my feelings." - the plates pile up on the desk
    C(ls("L011") - 0.05, saeed(ls("L011") - 0.05, "neutral", ed=112, eye=(900, 420), table=2.55, push=(1.0, 1.02)),
      yt=True, plates=(w("L011", "watching"), w("L011", "feelings") + 0.3), chat="feelings"),
    # Rio: "That's not my fault."
    C(m("cut_rio3"), rio(m("cut_rio3"), "rio-ferdinand:shrug", ed=104, eye=(960, 380), push=(1.0, 1.05)), reply=True),
    # "Neither are the Glazers." - dead flat, slow push
    C(m("cut_deadpan"), saeed(m("cut_deadpan"), "angry", ed=150, push=(1.0, 1.12)), yt=True),
    # side by side: "Funny how we're both avoiding responsibility, eh, Rio?" ... and nobody says anything
    insert(m("cut_split"), "split", left=saeed(m("cut_split"), "head", ed=128, eye=(960, 450)),
           right=rio(m("cut_split"), ed=92, eye=(960, 380))),
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

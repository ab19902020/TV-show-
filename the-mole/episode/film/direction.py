"""The shot list, cut on the dialogue edit (timeline.py). A fake fly-on-the-wall documentary: drone shots and
location slugs, talking heads in the interview chair with lower thirds, handheld singles, inserts on the evidence.

Where everyone is:
  Carrington (plate C): the building across the training pitch; the hedge in the foreground.
  The interview room (I): one black chair, softboxes, the stadium through the window.
  The corridor (K): the double doors on the right are the director of football's office; the plant waits beside them.
  Wilcox's office (O): his desk faces us, the window (and its blinds) on the left, the shelves and the corner the plant
      stands in on the right. Licho, once he is out of the plant, stands on our side of the desk: in singles he
      looks screen left to Wilcox, Wilcox looks screen right to him.
  The tactics room (TR): the big screen on the right wall carries the PowerPoint.
  The CEO's office (E): Omar behind his desk, the window behind him.
  The locker room at night (LR): the plant in the corner by the tactics board, Licho by the benches.

Shots are singles and worlds (studio.film.shots), most wrapped in props.comp, which switches drawings on cue (keys)
and adds the gags over them (flash, shake, crash zoom, wipe, freeze, soil, confetti, sweat, Zs, night)."""
import json

from studio.film import ep
from studio.film.shots import Marks, card, finish, insert, shot_at as _shot_at, single, world
from film.timeline import TL

L = json.loads(ep.path("lines.json").read_text())
T = Marks(TL, L)
m, ls, le, wt = T.m, T.ls, T.le, T.wt

PLATES = {"C": "training-ground/carrington-quiet", "I": "documentary/interview-chair", "K": "documentary/corridor",
          "O": "club/managers-office", "TR": "documentary/tactics-room", "E": "documentary/ceo-office",
          "LR": "documentary/locker-room"}
# furniture in front of the actors (1x plate px)
O_DESK = [(348, 482), (600, 472), (1190, 478), (1196, 500), (1186, 742), (1100, 748), (350, 712), (340, 500)]
E_DESK = [(268, 520), (330, 480), (860, 470), (1300, 478), (1400, 500), (1396, 560), (1300, 740), (300, 760)]
TR_CHAIRS = [(0, 520), (120, 520), (330, 600), (560, 640), (760, 700), (900, 760), (930, 941), (0, 941)]
OCCL = {"O": {"desk": [O_DESK]}, "E": {"desk": [E_DESK]}, "TR": {"chairs": [TR_CHAIRS]}}
EYES = {"licho": dict(wilcox=(-0.75, 0.03, -0.3), omar=(0.7, 0.05, 0.25)),
        "wilcox": dict(licho=(0.75, 0.03, 0.3)), "omar": dict(licho=(-0.6, 0.0, -0.25))}

LI, WI, OM = "lisandro-martinez:", "jason-wilcox:", "omar-berrada:"


def C(t, inner, **kw):
    """a shot drawn by props.comp over its inner shot (keys switch the drawing, fx add the gags)"""
    return insert(t, "comp", inner=inner, **kw)


def lic(t, draw, bg, ed=118.0, eye=(960, 420), push=(1.0, 1.04), **kw):
    """Licho close, nothing in front of him (his body runs off the bottom of the frame)"""
    return single(t, "licho", LI + draw, bg, None, ed=ed, eye=eye, table=0, push=push, drift=1.0, **kw)


def wil(t, draw, bg, fg=None, ed=118.0, eye=(960, 420), table=4.4, push=(1.0, 1.04), **kw):
    """Wilcox close; at his desk the desk's edge hides him from the hem of his top down"""
    return single(t, "wilcox", WI + draw, bg, fg, ed=ed, eye=eye, table=table, push=push, drift=1.0, **kw)


# the sets behind the singles: (plate, cx, cy, zoom, blur)
INT = ("I", 830, 420, 2.3, 6.0)                  # the interview chair, softly lit, the window beyond
INT2 = ("I", 760, 400, 2.5, 7.0)
OFF_W = ("O", 700, 260, 2.3, 4.5)                 # behind Wilcox: the tactics board, his chair
DESK = ("O", "desk", 700, 478, 2.7, 1.2)          # his desk's edge in front of him
OFF_L = ("O", 1430, 300, 2.3, 6.0)                # behind Licho: the trophy shelves
CORNER = ("O", 1540, 420, 2.6, 6.0)               # the corner the plant stands in (by the shelves)
KOR = ("K", 1360, 380, 2.4, 6.0)                  # the corridor by the office doors
TR_L = ("TR", 260, 330, 2.4, 6.0)                 # the tactics room's back wall, behind Licho in the audience
LR_B = ("LR", 1180, 330, 2.3, 6.0)                # the locker room's shirts on their pegs
LR_C = ("LR", 330, 420, 2.4, 6.0)                 # the locker room's corner by the tactics board
CEO_DOOR = ("K", 1460, 420, 2.6, 7.0)

# where the plants stand in the wides (1x plate px of the pot's foot, height of the whole plant in plate px)
CORR_PLANT = (1180, 640, 330)
OFFICE_PLANT = (1560, 690, 400)
LOCKER_PLANT = (330, 770, 360)

SHOTS = finish([
    # ================================================================ 1. the hedge
    # Carrington at dawn: the drone drifts in over the pitch towards the building
    world(0.0, "C", (836, 420, 1.0), cams=[(0.0, (836, 430, 1.0)), (m("cut_hedge"), (720, 400, 1.32))],
          drift=0.25, grade="sunny"),
    # the hedge by the car park; binoculars poking out of it, sweeping
    C(m("cut_hedge"), world(m("cut_hedge"), "C", (560, 450, 1.7), cams=[(m("cut_hedge"), (560, 450, 1.7)),
                                                                        (m("cut_bino"), (570, 455, 1.8))],
                            blur=2.5, layers=[("props", "hedge_wide")], grade="sunny")),
    # the binoculars turn to the lens; then they come down and he is in there: "Shhh. I am not here." The slurp.
    C(m("cut_bino"), lic(m("cut_bino"), "c-crouch", ("C", 560, 430, 2.3, 7.0), ed=150, eye=(960, 450),
                         push=(1.0, 1.06), props=["hedge_cu"], grade="sunny")),
    card(m("cut_title"), "title"),
    # ================================================================ 2. the evidence
    C(m("cut_int1"), lic(m("cut_int1"), "c-crossarms", INT, ed=112, eye=(930, 410), push=(1.0, 1.06))),
    insert(m("cut_board"), "board"),
    # "Manchester City." He has to compose himself.
    C(m("cut_compose"), lic(m("cut_compose"), "c-crossarms", INT, ed=126, eye=(940, 420), push=(1.04, 1.1),
                            punch=(wt("L012", "criminal") - 0.05, 1.12))),
    insert(m("cut_mug"), "board", focus="mug"),
    # "Why white, Jason? Why always white?" - palms up at the ceiling
    C(wt("L013", "why") - 0.05, lic(wt("L013", "why") - 0.05, "c-shrug", INT2, ed=96, eye=(960, 400),
                                    push=(1.0, 1.08))),
    # the clap; "When Leeds score..." - leaning in - "...Screaming."
    C(m("cut_clap"), lic(m("cut_clap"), "c-crossarms", INT, ed=118, eye=(930, 410), push=(1.0, 1.03),
                         punch=(wt("L015", "screaming") - 0.08, 1.15))),
    insert(m("cut_spygate"), "spygate"),
    # "Lisandro considers this... a tutorial." He stares into the lens.
    C(m("cut_tutorial"), lic(m("cut_tutorial"), "c-crossarms", INT, ed=150, eye=(960, 430), push=(1.0, 1.12))),
    # ================================================================ 3. the operation
    # the corridor: the plant by the office door shuffles closer whenever nobody is looking
    C(m("cut_corr"), world(m("cut_corr"), "K", (1340, 430, 1.6), cams=[(m("cut_corr"), (1340, 430, 1.6)),
                                                                       (m("cut_plantcu"), (1350, 440, 1.7))],
                           layers=[("props", "door_sign"), ("props", "corridor_plant")])),
    # inside the plant: "Target is in the office..."
    C(m("cut_plantcu"), lic(m("cut_plantcu"), "c-crouch", KOR, ed=118, eye=(960, 440), push=(1.0, 1.05),
                            behind=["plant_back"], props=["plant_front"], part=[(m("cut_plantcu"), 0.95)])),
    # Wilcox at his desk, on the phone: "Absolutely. We're fully aligned..." He hangs up. Looks at the door.
    C(m("cut_office"), wil(m("cut_office"), "phone", OFF_W, DESK, ed=112, eye=(930, 400), table=4.3,
                           push=(1.0, 1.05)),
      keys=[(m("hangup"), WI + "pockets")]),
    insert(m("cut_lock"), "lock"),
    # the blinds come down. In the corner: the plant. Already in. Nobody knows how.
    C(m("cut_blinds"), world(m("cut_blinds"), "O", (836, 470, 1.0), cams=[(m("cut_blinds"), (836, 470, 1.0)),
                                                                          (m("cut_clock"), (880, 470, 1.08))],
                             layers=[("props", "blinds"), ("props", "office_plant"),
                                     ("actors", [("wilcox", WI + "pockets", (700, 300), 45, False)]),
                                     ("occl", "desk")])),
    insert(m("cut_clock"), "clock"),
    # "...he let it breathe." The unzip, in slow motion: a Leeds top. A sigh of relief.
    C(wt("L023", "he") - 0.1, wil(wt("L023", "he") - 0.1, "pockets", OFF_W, DESK, ed=92, eye=(960, 330),
                                  table=5.0, push=(1.0, 1.08)),
      wipe=(wt("L023", "breathe"), wt("L023", "breathe") + 1.9, WI + "l-pockets"), glow=(wt("L023", "breathe") + 1.2,
                                                                                        m("cut_laptop"))),
    insert(m("cut_laptop"), "laptop", mode="live"),
    # "Come on, Leeds. Come on, lads." - leaning into the laptop
    C(m("cut_pray"), wil(m("cut_pray"), "l-pockets", OFF_W, None, ed=150, eye=(960, 430), push=(1.0, 1.06),
                         props=["laptop_lid"])),
    # the plant's leaves part: two eyes. "Madre mia."
    C(m("cut_eyes"), lic(m("cut_eyes"), "c-crouch", CORNER, ed=150, eye=(960, 450), push=(1.0, 1.06),
                         behind=["plant_back"], props=["plant_front"],
                         part=[(m("cut_eyes"), 0.25), (m("cut_eyes") + 0.25, 1.15)])),
    insert(m("cut_goal"), "laptop", mode="goal"),
    # "Yes! Get in! Marching on together!" - arms out; yellow and blue confetti
    C(m("cut_celebrate"), wil(m("cut_celebrate"), "l-shrug", OFF_W, DESK, ed=92, eye=(960, 380), table=4.3,
                              push=(1.0, 1.06)),
      confetti=wt("L026", "get"), shake=(wt("L026", "yes"), wt("L026", "in") + 0.3, 8)),
    # BOOM: the plant goes off. Licho rises out of it, pointing: "I KNEW IT!"
    C(m("boom"), lic(m("boom"), "c-point", CORNER, ed=124, eye=(1000, 400), push=(1.12, 1.0), mirror=True),
      soil=m("boom"), flash=m("boom"), shake=(m("boom"), m("boom") + 0.6, 26), rise=(m("boom"), 0.22),
      crash=ls("L027")),
    # the screams: Wilcox, Licho, Wilcox again because Licho screamed
    C(m("scream1"), wil(m("scream1"), "l-scream", OFF_W, DESK, ed=128, eye=(960, 400), table=4.3, push=(1.0, 1.1)),
      shake=(m("scream1"), m("scream2"), 10)),
    C(m("scream2"), lic(m("scream2"), "c-scream", CORNER, ed=128, eye=(960, 410), push=(1.0, 1.1), mirror=True),
      shake=(m("scream2"), m("scream3"), 10)),
    C(m("scream3"), wil(m("scream3"), "l-scream", OFF_W, DESK, ed=150, eye=(960, 420), table=4.3, push=(1.0, 1.14)),
      shake=(m("scream3"), m("freeze"), 14)),
    # FREEZE FRAME. "The mole had been found."
    C(m("freeze"), world(m("freeze"), "O", (900, 420, 1.35),
                         layers=[("actors", [("wilcox", WI + "l-scream", (700, 300), 45, False),
                                             ("licho", LI + "c-point", (1240, 330), 44, True)]),
                                 ("occl", "desk"), ("props", "soil_floor")]),
      freeze=m("freeze") + 0.05),
    # "The plant did not survive."
    insert(wt("L028", "the", 2) - 0.05, "pot_rip"),
    # ================================================================ 4. busted
    C(m("cut_s4"), wil(m("cut_s4"), "l-shrug", OFF_W, DESK, ed=100, eye=(960, 390), table=4.3)),
    C(m("cut_l030"), lic(m("cut_l030"), "c-crossarms", OFF_L, ed=112, eye=(1000, 420))),
    C(m("cut_w031"), wil(m("cut_w031"), "l-shrug2", OFF_W, DESK, ed=100, eye=(960, 390), table=4.3,
                         push=(1.0, 1.07))),
    C(m("cut_l032"), lic(m("cut_l032"), "c-shrug", OFF_L, ed=100, eye=(1000, 410))),
    C(m("cut_w033"), wil(m("cut_w033"), "l-shrug", OFF_W, DESK, ed=104, eye=(960, 390), table=4.3,
                         push=(1.0, 1.05))),
    C(m("cut_l034"), lic(m("cut_l034"), "c-crossarms", OFF_L, ed=126, eye=(1000, 420), push=(1.0, 1.06))),
    # he turns round: WILCOX across the shoulders, and his own autograph: "To Jason. Love, Jason. x"
    C(m("cut_back"), wil(m("cut_back"), "l-back", OFF_W, None, ed=150, eye=(960, 120), push=(1.0, 1.15))),
    C(m("cut_l035"), lic(m("cut_l035"), "c-shrug", OFF_L, ed=104, eye=(1000, 410), push=(1.0, 1.05))),
    C(m("cut_w036"), wil(m("cut_w036"), "l-pockets", OFF_W, DESK, ed=118, eye=(960, 400), table=4.3)),
    insert(m("ping"), "laptop", mode="penalty"),
    # "Oh, that's never a penalty, ref!"
    C(m("cut_w037"), wil(m("cut_w037"), "l-shrug2", OFF_W, DESK, ed=104, eye=(960, 390), table=4.3, push=(1.0, 1.08),
                         punch=(wt("L037", "never") - 0.05, 1.1))),
    # Licho, pointing. A long hold. "Say it."
    C(m("cut_point"), lic(m("cut_point"), "c-point", OFF_L, ed=104, eye=(1080, 410), push=(1.0, 1.06), mirror=True)),
    C(m("cut_w039"), wil(m("cut_w039"), "l-pockets", OFF_W, DESK, ed=118, eye=(960, 400), table=4.3)),
    C(m("cut_l040"), lic(m("cut_l040"), "c-crossarms", OFF_L, ed=126, eye=(1000, 420), push=(1.0, 1.08))),
    # he tries. Sweat. The eye twitches. "Leeds are... really well coached, to be fair."
    C(m("cut_strain"), wil(m("cut_strain"), "l-pockets", OFF_W, None, ed=160, eye=(960, 430), push=(1.0, 1.16)),
      sweat=(m("cut_strain") + 0.4, le("L041")), shake=(m("cut_strain") + 0.3, ls("L041") + 0.8, 3)),
    # to the documentary camera: "He cannot say it. He is sick."
    C(m("cut_l042"), lic(m("cut_l042"), "c-facepalm", OFF_L, ed=104, eye=(990, 420), push=(1.0, 1.06))),
    # ================================================================ 5. the right of reply
    C(m("cut_pp"), world(m("cut_pp"), "TR", (1060, 380, 1.15), cams=[(m("cut_pp"), (1060, 380, 1.15)),
                                                                     (m("cut_w044"), (1120, 360, 1.25))],
                         layers=[("props", "slides"),
                                 ("actors", [("wilcox", WI + "clipboard", (760, 330), 33, False)]),
                                 ("occl", "chairs")])),
    C(m("cut_w044"), world(m("cut_w044"), "TR", (1000, 290, 1.7), cams=[(m("cut_w044"), (1000, 290, 1.7)),
                                                                        (m("cut_l045"), (990, 285, 1.8))],
                           blur=1.5, layers=[("props", "slides"),
                                             ("actors", [("wilcox", WI + "clipboard", (760, 330), 33, False)])])),
    C(m("cut_l045"), lic(m("cut_l045"), "c-crossarms", TR_L, ed=112, eye=(960, 420))),
    C(m("cut_w046"), world(m("cut_w046"), "TR", (900, 300, 2.1), blur=1.5,
                           layers=[("props", "slides"),
                                   ("actors", [("wilcox", WI + "clipboard", (760, 330), 33, False)])])),
    # seventy minutes later: slide 213. Licho asleep.
    C(m("cut_asleep"), world(m("cut_asleep"), "TR", (960, 400, 1.2), cams=[(m("cut_asleep"), (960, 400, 1.2)),
                                                                           (m("cut_int2"), (880, 420, 1.35))],
                             layers=[("props", "slides"),
                                     ("actors", [("wilcox", WI + "clipboard", (760, 330), 33, False),
                                                 ("licho", LI + "c-crossarms", (650, 455), 56, False)]),
                                     ("occl", "chairs")]),
      zzz=(m("cut_asleep") + 0.3, m("cut_int2"))),
    C(m("cut_int2"), lic(m("cut_int2"), "crossarms", INT, ed=112, eye=(930, 410), push=(1.0, 1.05),
                         punch=(wt("L048", "case") - 0.05, 1.1))),
    # Wilcox's own talking head, zipped to the chin
    C(m("cut_wth"), wil(m("cut_wth"), "crossarms", OFF_L, None, ed=112, eye=(960, 410), push=(1.0, 1.05))),
    # ================================================================ 6. going to the top
    C(m("cut_int3"), lic(m("cut_int3"), "crossarms", INT, ed=118, eye=(930, 410))),
    # he bursts in: "Omar! We have a mole!"
    C(m("cut_ceo"), lic(m("cut_ceo"), "stand", CEO_DOOR, ed=104, eye=(960, 400), push=(1.12, 1.0)),
      whoosh_in=m("cut_ceo")),
    # Omar, in a City scarf. Frozen mid-sip. One cricket.
    C(m("cut_omar"), world(m("cut_omar"), "E", (880, 380, 1.55), cams=[(m("cut_omar"), (880, 380, 1.55)),
                                                                       (m("cut_l053"), (880, 360, 1.75))],
                           blur=1.0, layers=[("props", "omar_desk_back"),
                                             ("actors", [("omar", OM + "city", (900, 300), 34, False)]),
                                             ("occl", "desk"), ("props", "omar_desk_front")])),
    C(m("cut_l053"), lic(m("cut_l053"), "facepalm", CEO_DOOR, ed=110, eye=(960, 410), push=(1.0, 1.04))),
    C(m("cut_omar2"), world(m("cut_omar2"), "E", (860, 420, 1.2), cams=[(m("cut_omar2"), (860, 420, 1.2)),
                                                                        (m("cut_night"), (880, 380, 1.4))],
                            layers=[("props", "omar_desk_back"),
                                    ("actors", [("omar", OM + "city", (900, 300), 34, False)]),
                                    ("occl", "desk"), ("props", "omar_desk_front")])),
    # ================================================================ 7. the spy who spied me
    C(m("cut_night"), world(m("cut_night"), "LR", (760, 520, 1.12), cams=[(m("cut_night"), (760, 520, 1.12)),
                                                                          (m("cut_tablet"), (800, 500, 1.22))],
                            layers=[("props", "locker_plant"),
                                    ("actors", [("licho", LI + "tablet", (980, 450), 42, False)])]),
      night=True),
    insert(m("cut_tablet"), "tablet"),
    C(m("cut_l056"), lic(m("cut_l056"), "tablet", LR_B, ed=118, eye=(960, 420), push=(1.0, 1.05)), night=True),
    # the plant in the corner that wasn't there before: the leaves part
    C(m("cut_plant2"), wil(m("cut_plant2"), "l-pockets", LR_C, None, ed=130, eye=(960, 440), push=(1.0, 1.05),
                           behind=["plant_back"], props=["plant_front"],
                           part=[(m("cut_plant2"), 0.2), (m("cut_plant2") + 0.7, 1.1)]), night=True),
    # "I KNEW IT!"
    C(m("cut_w057"), wil(m("cut_w057"), "l-point", LR_C, None, ed=118, eye=(900, 410), push=(1.12, 1.0)),
      soil=m("cut_w057"), flash=m("cut_w057"), shake=(m("cut_w057"), m("scream"), 20), night=True,
      crash=ls("L057")),
    # both scream
    C(m("scream"), world(m("scream"), "LR", (800, 470, 1.5),
                         layers=[("actors", [("wilcox", WI + "l-scream", (560, 420), 40, False),
                                             ("licho", LI + "scream", (1010, 440), 40, True)]),
                                 ("props", "soil_floor")]),
      shake=(m("scream"), m("cut_l058"), 16), night=True),
    C(m("cut_l058"), lic(m("cut_l058"), "shrug2", LR_B, ed=100, eye=(990, 400), push=(1.0, 1.06)), night=True),
    C(m("cut_w059"), wil(m("cut_w059"), "l-shrug", LR_C, None, ed=100, eye=(940, 390), push=(1.0, 1.06)),
      night=True),
    C(m("cut_l060"), lic(m("cut_l060"), "stand", LR_B, ed=132, eye=(980, 430), push=(1.0, 1.08)), night=True),
    # the two of them pointing at each other. Freeze.
    C(m("cut_spidey"), world(m("cut_spidey"), "LR", (780, 470, 1.45),
                             layers=[("actors", [("wilcox", WI + "l-point", (520, 420), 40, False),
                                                 ("licho", LI + "point", (1060, 440), 40, True)]),
                                     ("props", "soil_floor")]),
      night=True, freeze=m("cut_spidey") + 0.5),
    # outside Sir Jim's office: two hedges. "Shhh. We are not here." The other hedge raises a white mug.
    C(m("cut_hedges"), world(m("cut_hedges"), "C", (600, 420, 1.9), blur=3.0,
                             layers=[("props", "two_hedges")], grade="sunny")),
    insert(m("cut_end"), "end_card"),
], TL["total"])
for _s in SHOTS:                                    # the inner shots run to the end of their outer shot
    if _s.get("inner"):
        _s["inner"]["end"] = _s["end"]
        _s["inner"]["t"] = _s["t"]
        _s["inner"]["i"] = _s["i"] * 10

TITLE = (("ALL OR SOMETHING", "BEBAS", 150, None, 16, 360, (255, 255, 255)),
         ("THE MOLE", "BEBAS", 110, None, 10, 520, (255, 255, 255)))
TAGLINE = (("A MANCHESTER UNITED DOCUMENTARY. SORT OF.", "BEBAS", 48, None, 5, 760, (225, 225, 225)),)

# documentary captions: (start, end, kind, text 1, text 2)
CAPTIONS = [
    (m("open") + 1.2, m("cut_hedge") - 0.4, "place", "CARRINGTON", "Manchester United training ground. 06:12"),
    (m("cut_int1") + 0.3, m("cut_board") - 0.1, "name", "LISANDRO MARTINEZ", "Defender. Amateur detective."),
    (m("cut_corr") + 0.2, m("cut_plantcu") - 0.1, "place", "DAY ONE", "The surveillance operation. 14:52"),
    (m("cut_office") + 0.4, m("hangup") - 0.1, "name", "JASON WILCOX", "Director of Football"),
    (m("cut_pp") + 0.2, m("cut_w044") - 0.1, "place", "THE RIGHT OF REPLY", "Tactics room. 16:00"),
    (m("cut_asleep") + 0.2, m("cut_int2") - 0.1, "place", "70 MINUTES LATER", "Slide 213 of 214"),
    (m("cut_wth") + 0.3, ls("L050") - 0.1, "name", "JASON WILCOX", "Director of Football. Red through and through.*"),
    (ls("L050"), m("cut_int3") - 0.1, "name", "JASON WILCOX", "*Mostly."),
    (m("cut_omar") + 0.4, m("cut_l053") - 0.1, "name", "OMAR BERRADA", "Chief Executive"),
    (m("cut_night") + 0.2, m("cut_tablet") - 0.1, "place", "THAT NIGHT", "Carrington. 23:47"),
    (m("cut_hedges") + 0.3, ls("L062") - 0.1, "place", "NEXT WEEK", "Outside Sir Jim's office"),
]
WHIPS = []


def _drawings():
    """every drawing the shots use (inside props.comp too), so `prepare` builds them all before a render"""
    out = set()
    for s_ in SHOTS:
        for sh in (s_, s_.get("inner") or {}):
            if ":" in str(sh.get("draw", "")):
                out.add(sh["draw"])
            for kind, val in sh.get("layers", []):
                if kind == "actors":
                    out.update(a[1] for a in val)
        out.update(d for _, d in s_.get("keys", []))
        if s_.get("wipe"):
            out.add(s_["wipe"][2])
    out.add("lisandro-martinez:c-crouch")
    return {k: k for k in sorted(out)}


DRAW = _drawings()


def shot_at(t):
    return _shot_at(SHOTS, t)

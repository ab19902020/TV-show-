"""Direction: the shot list (cuts hang off the spoken words) and the acting cues (keys on the performance channels).

Studio = controlled, steady, conventional TV framing. Restaurant (the flashback) = energetic: quicker cuts, hand-held drift,
punch-ins. Everything is keyed to W("words") so the picture follows Rooney's words as he says them: nothing is illustrated
before it is mentioned. The hard cut studio -> restaurant lands on "in Wing's" (the first mention of the restaurant), mid-sentence.

Characters (perf channel names):  gary, rooney, micah = the studio heads;  wr cr b1 b2 b3 b4 = the Rooney family in the flashback;
mi = Micah at the party (modes: strut, dance, run, freeze, cool);  mi_t = Micah at the party table (poses);  mi_cu = the face close-up;
jamie dan ravi film = the friends (each has ONE repeating action)."""
import math
import perf
from perf import W, key, pose, pulse, EXTRA_BLINKS

T_CUT_IN = W("in wings")                      # 15.02: HARD CUT into the restaurant, mid-sentence
T_CUT_OUT = 32.70                             # the story is told: back to the studio (laughter in the audio)
T_FIFTIETH = W("fiftieth")                    # 30.70: the punchline word
T_END = perf.DUR
perf.BALLOON_T0 = 40.55

SHOTS = []


def shot(name, t0, t1, setup, c0, c1=None, **kw):
    SHOTS.append(dict(name=name, t0=t0, t1=t1, setup=setup, c0=c0, c1=c1 or c0, **kw))


import restaurant, party
from render_util import cam_for_collar, STUDIO_SEAT, STUDIO_SCALE
EXTRA_SETUPS = dict(restaurant.EXTRA)
EXTRA_SETUPS.update(party.EXTRA)

# ================================================================ SHOT LIST
# ---- studio, before the story
shot("S1 wide, Gary's question", 0.00, 4.88, "studio", (980, 690, 760), (985, 680, 690))
shot("S2 two-shot: Micah teases Rooney", 4.88, 9.30, "studio", (1100, 636, 480), (1135, 630, 420))
shot("S2b Rooney MCU, Micah over shoulder: pubs? clubs?", 9.30, 11.90, "studio", (1045, 600, 345), (1040, 598, 310))
shot("S2c two-shot: Everything!", 11.90, 13.10, "studio", (1100, 650, 500), (1100, 646, 470))
shot("S3 Rooney CU: I've actually seen Micah", 13.10, T_CUT_IN, "studio", (980, 572, 275), (980, 570, 240))

# ---- the flashback (hard cut on "in Wing's"): the restaurant looks like a normal smart restaurant
shot("R1 exterior, the Rooneys walk in", T_CUT_IN, 16.65, "exterior", (470, 836, 941), (470, 836, 900), warm=True, shake=1.0)
shot("R2 the family table: a quiet meal", 16.65, 20.78, "table", (470, 836, 941), (330, 800, 650), warm=True, shake=0.7)
shot("R3 Rooney notices something", 20.78, 22.05, "table", (170, 790, 340), (165, 780, 235), warm=True, shake=1.0, punch=True)

# ---- Rooney's POV: the party (escalating)
shot("R4 POV reveal: about twenty of his guys", 22.05, 23.30, "party_wide", (470, 880, 941), (500, 850, 790), warm=True, shake=1.6, confetti=True)
shot("R5a Micah walks in and dances", 23.30, 24.10, "party_wide", (500, 860, 840), (520, 850, 780), warm=True, shake=1.8, confetti=True, confetti_n=170)
shot("R5b Micah points", 24.10, 24.65, "party_table", (560, 700, 560), (560, 705, 520), warm=True, shake=1.4, confetti=True,
     micah_pose=(470, 1045, 5.2))
shot("R5c both hands up", 24.65, 25.20, "party_table", (560, 720, 640), (560, 715, 600), warm=True, shake=1.4, confetti=True,
     micah_pose=(470, 1045, 5.2))
shot("R5d friends: pint, clapping", 25.20, 25.80, "party_wide", (420, 900, 600), (440, 900, 560), warm=True, shake=1.8, confetti=True, confetti_n=170)
shot("R5e a friend presents Micah", 25.80, 26.45, "party_wide", (560, 890, 700), (560, 880, 640), warm=True, shake=1.6, confetti=True, confetti_n=170)
shot("R6 the family stares", 26.45, 28.15, "table", (470, 760, 900), (330, 730, 600), warm=True, shake=0.5, ease="in")
shot("R7 back to Micah: even bigger", 28.15, 29.30, "party_wide", (520, 860, 900), (540, 860, 760), warm=True, shake=2.0, confetti=True, confetti_n=190)
shot("R8 Micah's side: Rooney is staring", 29.30, T_FIFTIETH, "party_wide", (560, 800, 780), (565, 800, 720), warm=True, shake=1.0, family_bg=True,
     micah_xy=(380, 1090), confetti=True, confetti_n=90)
shot("R8b Rooney raises his eyebrows", T_FIFTIETH, 31.25, "table", (170, 790, 300), (168, 788, 280), warm=True, shake=0.5)
shot("R9a Micah plays it cool", 31.25, 32.05, "party_wide", (480, 880, 720), (470, 880, 680), warm=True, shake=0.8, confetti=True, confetti_n=60,
     micah_xy=(520, 1060))
MATCH = dict(u=0.50, v=0.60, app=7.0)           # the match cut: Micah's neck at the same place, at the same size, in both plates
PARTY_BUST = (560, 1060, 3.4)
_pc = cam_for_collar("mr_e_embarrassed", *PARTY_BUST, **MATCH)
shot("R9b Micah's face", 32.05, T_CUT_OUT, "party_cu", _pc, _pc, warm=True, shake=0.0, plate="w_party", bust=PARTY_BUST)

# ---- back to the studio
_sc = cam_for_collar("mr_e_embarrassed", *STUDIO_SEAT["micah"][:2], STUDIO_SCALE["micah"], **MATCH)
shot("S10 match cut: studio Micah", T_CUT_OUT, 33.30, "studio", _sc, _sc)
shot("S10b Gary looks, then laughs", 33.30, 33.85, "studio", (735, 582, 300), (735, 580, 280))
shot("S11 two-shot, Micah protests", 33.85, 38.05, "studio", (1105, 640, 480), (1100, 638, 440))
shot("S12 final wide", 38.05, T_END, "studio", (1000, 690, 760), (1000, 684, 730))

# ================================================================ ACTING CUES
# ---------------------------------------------------------------- Gary
pose("gary", 0.0, "gy_b_q34L")
key("gary", "smile", 0.0, 0.1, 0.2)
key("gary", "look", 4.2, (0.9, 0.0), 0.4)                 # turns his eyes to the guests as the question ends
key("gary", "smile", 4.7, 0.3, 0.5)
pose("gary", T_CUT_OUT + 0.05, "gy_e_neutral")
key("gary", "smile", 33.0, 0.2, 0.2)
pose("gary", 33.30, "gy_e_amused")                          # looks at Micah...
pose("gary", 33.62, "gy_e_laughing")                        # ...then goes
pose("gary", 34.5, "gy_e_smiling")
pose("gary", 36.9, "gy_e_laughing")
pose("gary", 38.05, "gy_b_front")                           # final wide: amused
key("gary", "smile", 38.05, 0.8, 0.5)
pulse("gary", "tilt", 39.0, 5.0, up=0.2, hold=0.4, down=0.4)
pose("gary", 40.0, "gy_e_laughing")

# ---------------------------------------------------------------- Rooney (studio)
pose("rooney", 0.0, "wr_b_front")
key("rooney", "look", 0.0, (-0.6, 0.0), 0.1)               # listening to Gary
key("rooney", "smile", 0.0, 0.05, 0.1)
pose("rooney", 4.88, "wr_b_q34R")                          # Micah starts on him: he turns to listen, deadpan, a slight grin
key("rooney", "look", 4.95, (0.7, 0.0), 0.25)
key("rooney", "smile", 4.95, 0.25, 0.4)
pulse("rooney", "nod", W("biggun"), 3.0, up=0.15, hold=0.15, down=0.35)
key("rooney", "look", 8.4, (0.4, -0.5), 0.3)               # a little eye-roll at "back in those days"
key("rooney", "look", 9.0, (0.7, 0.0), 0.3)
pose("rooney", 9.28, "wr_b_front")                         # "What was it? Pubs? Clubs?" - casual, nothing special
key("rooney", "look", 9.30, (0.6, 0.0), 0.2)
pulse("rooney", "brow", W("pubs"), 0.6, up=0.1, hold=0.15, down=0.25)
pulse("rooney", "brow", W("clubs"), 0.7, up=0.1, hold=0.15, down=0.25)
pulse("rooney", "tilt", W("what was it", 1), 3.0, up=0.15, hold=0.2, down=0.3)
key("rooney", "brow", W("everything") - 0.05, 0.8, 0.12)    # Micah: "Everything!" - brows up, a grin to Gary
key("rooney", "smile", W("everything"), 0.6, 0.2)
key("rooney", "look", W("everything") + 0.2, (-0.7, 0.0), 0.25)
key("rooney", "brow", 12.7, 0.0, 0.4)
key("rooney", "look", 13.0, (0.0, 0.0), 0.2)               # then, calmly, the story
key("rooney", "smile", 13.0, 0.15, 0.3)
key("rooney", "look", W("micah"), (0.9, 0.0), 0.25)         # "...seen Micah" - a glance at the man himself
key("rooney", "smile", W("micah"), 0.5, 0.3)
key("rooney", "look", 14.6, (0.0, 0.0), 0.3)
# after the flashback
pose("rooney", T_CUT_OUT, "wr_e_smug")
pose("rooney", 33.30, "wr_e_laughing")
pose("rooney", 33.85, "wr_b_q34R")                         # delighted, looking across at Micah
key("rooney", "smile", 33.85, 0.9, 0.3)
key("rooney", "look", 33.9, (0.8, 0.0), 0.3)
pulse("rooney", "tilt", 35.0, -5.0, up=0.15, hold=0.3, down=0.4)
pose("rooney", 36.8, "wr_e_happy")
pose("rooney", 38.0, "wr_b_front")
key("rooney", "smile", 38.0, 0.9, 0.3)

# ---------------------------------------------------------------- Micah (studio)
pose("micah", 0.0, "mr_b_q34R|f")                          # facing Rooney and Gary, over the desk
key("micah", "smile", 0.0, 0.35, 0.5)
key("micah", "brow", 0.0, -0.25, 0.3)                       # a knowing look: he has stories about Rooney
key("micah", "look", 2.6, (-0.55, 0.0), 0.3)
key("micah", "look", 4.0, (0.0, 0.0), 0.3)
key("micah", "smile", 4.85, 0.7, 0.3)                      # "We did, didn't we?" - cocky, teasing Rooney
key("micah", "brow", 4.85, 0.3, 0.3)
pulse("micah", "nod", W("couple"), 3.0, up=0.12, hold=0.1, down=0.3)
key("micah", "brow", W("biggun") - 0.1, 0.9, 0.12)          # "the biggun"
key("micah", "brow", W("biggun") + 0.6, 0.3, 0.4)
key("micah", "look", W("back in"), (-1.0, 0.0), 0.2)        # a tiny sideways look towards Gary
key("micah", "look", 9.25, (0.0, 0.0), 0.3)
key("micah", "smile", 9.3, 0.55, 0.3)                      # Rooney's question: a smirk, mouth shut
pulse("micah", "nod", 10.6, 2.5, up=0.15, hold=0.15, down=0.3)
key("micah", "brow", W("everything") - 0.08, 1.0, 0.1)     # "Everything!"
pulse("micah", "tilt", W("everything"), -6.0, up=0.12, hold=0.25, down=0.4)
key("micah", "smile", 12.5, 0.8, 0.2)
key("micah", "brow", 12.6, 0.2, 0.4)
key("micah", "look", 12.7, (-0.6, 0.0), 0.3)
key("micah", "smile", 13.3, 0.3, 0.6)                      # "I've actually seen Micah..." - the grin starts to go
key("micah", "brow", 13.6, -0.4, 0.4)
pose("micah", T_CUT_OUT, "mr_e_embarrassed")               # the match cut from the restaurant
pose("micah", 33.85, "mr_b_q34R|f")                        # "It's the Premier League."
key("micah", "smile", 33.85, 0.8, 0.2)
key("micah", "brow", 33.85, 0.5, 0.2)
key("micah", "tilt", W("big thing"), -4.0, 0.2)            # shakes his head
key("micah", "tilt", W("big thing") + 0.5, 4.0, 0.3)
key("micah", "tilt", W("big thing") + 1.0, -2.0, 0.3)
key("micah", "look", W("for me"), (0.0, 1.0), 0.25)        # looks down
key("micah", "nod", W("for me"), 4.0, 0.3)
key("micah", "look", W("wayne"), (-1.0, 0.0), 0.2)         # ...and back at Rooney: "you've stitched me up"
key("micah", "nod", W("wayne"), 0.0, 0.3)
pose("micah", W("why did"), "mr_b_front")
key("micah", "look", W("why did"), (0.0, 0.0), 0.2)
key("micah", "smile", W("why did"), 0.9, 0.3)
key("micah", "look", 40.95, (0.0, -1.0), 0.15)                    # ...and notices the little 50 balloon behind him
pulse("micah", "shrug", 40.55, 1.0, up=0.18, hold=0.25, down=0.3)    # one final little shrug
pulse("micah", "tilt", 40.55, 5.0, up=0.18, hold=0.25, down=0.3)

# ---------------------------------------------------------------- the family at the table (flashback)
for c in ("wr", "cr", "b1", "b2", "b3", "b4"):
    pose(c, 0.0, f"{c}_b_front")
    key(c, "smile", 16.0, 0.3, 0.5)
# R2: a quiet meal - a few small sips and nods
for tt, c in ((17.4, "wr"), (18.2, "cr"), (19.0, "b3"), (19.9, "wr")):
    pulse(c, "nod", tt, 3.0, up=0.25, hold=0.25, down=0.4)
key("b2", "look", 18.0, (0.0, 1.0), 0.3)
key("b2", "look", 19.2, (0.0, 0.0), 0.3)
# R3: Rooney notices something off camera: brow down, eyes narrow, a slow turn to the right
key("wr", "look", W("micah comes"), (1.0, 0.0), 0.25)
key("wr", "brow", W("micah comes") + 0.1, -0.9, 0.3)
key("wr", "blinkx", W("micah comes") + 0.15, 0.42, 0.3)             # eyes narrow
key("wr", "smile", W("micah comes"), 0.0, 0.2)
pose("wr", 21.30, "wr_b_q34R")
pose("wr", 21.75, "wr_b_side")
# R6: the stare; the family turns to look; a tiny amused shake of the head
T_SO = W("so i was")
pose("wr", T_SO - 0.05, "wr_b_side")
key("wr", "blinkx", T_SO, 0.18, 0.2)
key("wr", "brow", T_SO, -0.5, 0.2)
pose("wr", 27.95, "wr_b_q34R")
key("wr", "smile", 27.95, 0.6, 0.25)
key("wr", "tilt", 27.95, 4.0, 0.12)
key("wr", "tilt", 28.12, -4.0, 0.15)
key("wr", "tilt", 28.30, 3.0, 0.15)
key("wr", "tilt", 28.5, 0.0, 0.25)
pose("cr", T_SO + 0.12, "cr_b_q34R")                                 # Coleen looks at the party...
pose("cr", T_SO + 0.95, "cr_b_q34R|f")                               # ...then at Rooney
key("cr", "brow", T_SO + 0.95, 0.6, 0.2)
pose("b1", T_SO + 0.05, "b1_b_q34R")
pose("b2", T_SO + 0.18, "b2_b_q34R")
key("b2", "fwd", T_SO + 0.5, 1.0, 0.45)                               # one boy leans in to see
pose("b3", T_SO + 0.10, "b3_b_q34R")
pose("b3", T_SO + 0.9, "b3_e_confused")                               # another is just confused
pose("b4", T_SO + 0.25, "b4_b_q34R")
# R8 / R9: the family in the background keeps staring at the camera
for c in ("wr", "cr", "b1", "b2", "b3", "b4"):
    pose(c, 29.25, f"{c}_b_front")
key("wr", "brow", 29.3, -0.5, 0.2)
key("wr", "blinkx", 29.3, 0.18, 0.2)
key("b2", "fwd", 29.3, 0.0, 0.2)
# R8b: eyebrows up on "fiftieth"
pose("wr", T_FIFTIETH - 0.02, "wr_b_front")
key("wr", "blinkx", T_FIFTIETH - 0.02, 0.0, 0.08)
key("wr", "brow", T_FIFTIETH - 0.02, 1.0, 0.1)
key("wr", "smile", T_FIFTIETH, 0.35, 0.3)

# ---------------------------------------------------------------- Micah at the party
perf.APPEAR.update(ravi=W("twenty"), dan=W("his"), jamie=W("about"), film=W("guys"))
perf.CROWD_WINDOW = (W("about"), W("guys") + 0.1)
pose("mi", 22.0, "dance")
pose("mi", 23.30, "strut")
pose("mi", 24.05, "dance")
pose("mi", 28.15, "run")
pose("mi", 29.30, "dance")
pose("mi", 30.15, "freeze")                                         # he has seen Rooney
pose("mi", 31.30, "cool")                                           # hands in pockets, nothing to see here
pose("mi_t", 24.10, "point")
pose("mi_t", 24.65, "hands")
pose("jamie", 22.0, "cheers")
pose("jamie", 25.20, "yes")
pose("jamie", 28.15, "cheers")
pose("dan", 22.0, "clap")
pose("dan", 25.20, "armsup")
pose("dan", 28.15, "clap")
pose("ravi", 22.0, "placard")
pose("film", 22.0, "pointing")
# R9: Micah's face: embarrassed, a friend still celebrating behind him
pose("mi_cu", 32.05, "mr_e_embarrassed")

perf.finalize()

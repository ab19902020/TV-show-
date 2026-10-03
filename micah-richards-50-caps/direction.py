"""Direction: the shot list (cuts hang off the spoken words) and the acting cues (keys on the performance channels).

Studio = controlled, steady, conventional TV framing; faces fill the portrait frame. Restaurant (the flashback) = warmer, a little
hand-held, slow pushes. Everything is keyed to W("words"), so nothing is shown before Rooney mentions it. The hard cut studio ->
restaurant lands on "in Wing's", mid-sentence; the match cut back is on Micah's embarrassed face.

Perf channel names: shearer, gary, rooney, micah = the studio panel;  wr cr b1 b2 b3 b4 = the Rooney family in the flashback;
mi = Micah at the party (modes: dance, placard, freeze, cool); mi_cu = his face close-up; jamie, ravi, film = his friends."""
import perf
from perf import W, key, pose, pulse
from render_util import OW, OH

T_CUT_IN = W("in wings")                      # 15.02: HARD CUT into the restaurant, mid-sentence
T_CUT_OUT = 32.70                             # the story is told: back to the studio (laughter in the audio)
T_FIFTIETH = W("fiftieth")                    # 30.70
T_END = perf.DUR
perf.BALLOON_T0 = 40.45

SHOTS = []


def shot(name, t0, t1, setup, c0, c1=None, **kw):
    SHOTS.append(dict(name=name, t0=t0, t1=t1, setup=setup, c0=c0, c1=c1 or c0, **kw))


import restaurant, party
EXTRA_SETUPS = dict(restaurant.EXTRA)
EXTRA_SETUPS.update(party.EXTRA)

# studio framing helpers: (cx, cy, w) with the head at screen height fraction v
HEADS = dict(shearer=(640, 445), gary=(820, 482), rooney=(1000, 455), micah=(1180, 482))


def on(x, y, w, v=0.40, dx=0.0):
    h = w * OH / OW
    return (x + dx, y + (0.5 - v) * h, w)


def two(a, b, w, v=0.42):
    (xa, ya), (xb, yb) = HEADS[a], HEADS[b]
    return on((xa + xb) / 2, (ya + yb) / 2, w, v)


# ================================================================ SHOT LIST
# ---- studio, before the story
shot("S1 wide: the panel", 0.00, 2.55, "studio", (905, 662, 700), (915, 650, 650))
shot("S1b Gary asks", 2.55, 4.88, "studio", on(*HEADS["gary"], 260, 0.37, 18), on(*HEADS["gary"], 235, 0.37, 18))
shot("S2 two-shot: Micah teases Rooney", 4.88, 9.30, "studio", two("rooney", "micah", 430, 0.37), two("rooney", "micah", 390, 0.37))
shot("S3 Shearer: pubs? clubs?", 9.30, 11.90, "studio", on(*HEADS["shearer"], 270, 0.37, 26), on(*HEADS["shearer"], 245, 0.37, 26))
shot("S4 Micah: Everything!", 11.90, 13.10, "studio", on(*HEADS["micah"], 300, 0.38, -22), on(*HEADS["micah"], 280, 0.38, -22), punch=True)
shot("S5 Rooney: I've actually seen Micah", 13.10, T_CUT_IN, "studio", on(*HEADS["rooney"], 260, 0.37, -16), on(*HEADS["rooney"], 215, 0.37, -8))

# ---- the flashback (hard cut on "in Wing's")
shot("R1 exterior: the Rooneys walk in", T_CUT_IN, 16.65, "exterior", (600, 990, 760), (500, 1000, 720), warm=True, shake=0.4)
shot("R2 the family table: a quiet meal", 16.65, 20.78, "table", (470, 760, 760), (470, 760, 640), warm=True, shake=0.4)
shot("R3 Rooney notices something", 20.78, 22.05, "table", (180, 720, 330), (175, 716, 250), warm=True, shake=0.5)
shot("R4 POV: Micah on the table", 22.05, 24.40, "party", (470, 760, 900), (480, 740, 780), warm=True, shake=0.8, confetti=True, crowd=True)
shot("R5 the 50 CAPS card", 24.40, 26.45, "party", (520, 640, 560), (520, 630, 500), warm=True, shake=0.8, confetti=True, crowd=True,
     mi_mode="placard")
shot("R6 the family stares", 26.45, 28.15, "table", (470, 760, 700), (430, 750, 560), warm=True, shake=0.3)
shot("R7 even bigger", 28.15, 29.30, "party", (480, 700, 700), (480, 690, 620), warm=True, shake=1.2, confetti=True, crowd=True, confetti_n=220)
shot("R8 from Micah's side: Rooney laughing", 29.30, T_FIFTIETH, "party_side", (705, 650, 500), (712, 640, 450), warm=True, shake=0.4)
shot("R9 Rooney: eyebrows up", T_FIFTIETH, 31.40, "table", (180, 716, 270), (178, 714, 250), warm=True, shake=0.3)
shot("R10 Micah plays it cool", 31.40, 32.07, "party", (520, 640, 560), (520, 640, 540), warm=True, shake=0.4, confetti=True, crowd=True,
     confetti_n=40, mi_mode="cool")
shot("R11 Micah's face", 32.07, T_CUT_OUT, "party_cu", None, None, warm=True)

# ---- back to the studio
shot("S10 match cut: studio Micah", T_CUT_OUT, 33.30, "studio", None, None, match=True)
shot("S11 Gary laughs", 33.30, 33.87, "studio", on(*HEADS["gary"], 240, 0.38, 18), on(*HEADS["gary"], 228, 0.38, 18))
shot("S12 Micah protests", 33.87, 38.05, "studio", two("rooney", "micah", 430, 0.37), two("rooney", "micah", 380, 0.37))
shot("S13 final wide", 38.05, T_END, "studio", (912, 640, 650), (916, 634, 610))

# ================================================================ ACTING CUES (studio)
# ---------------------------------------------------------------- Gary (host): professional, then more and more amused
pose("gary", 0.0, "gy_p_talking1")
key("gary", "look", 0.0, (0.6, 0.0), 0.2)
pose("gary", W("derby"), "gy_p_talking2")
key("gary", "look", 4.3, (0.8, 0.0), 0.3)
pose("gary", 9.25, "gy_p_talking1")
pose("gary", W("everything") + 0.15, "gy_p_amused")         # starts to laugh at "Everything!"
pose("gary", 13.0, "gy_p_talking1")
pose("gary", T_CUT_OUT, "gy_p_talking1")
pose("gary", 33.30, "gy_p_amused")                          # the big laugh after the flashback
pose("gary", 33.87, "gy_p_amused")
pose("gary", 38.05, "gy_p_amused")

# ---------------------------------------------------------------- Shearer: arms folded, then "pubs? clubs?", then pointing and laughing
pose("shearer", 0.0, "as_p_listening")
key("shearer", "look", 0.0, (0.5, 0.0), 0.2)
pose("shearer", 9.27, "as_p_talking")
pulse("shearer", "nod", W("pubs"), 4.0, up=0.10, hold=0.10, down=0.25)
pulse("shearer", "nod", W("clubs"), 4.0, up=0.10, hold=0.10, down=0.25)
pose("shearer", W("what was it", 1), "as_p_pointing")      # "what was it?" - points at Micah, laughing
pose("shearer", 12.6, "as_p_listening")
pose("shearer", 33.3, "as_p_pointing")
pose("shearer", 34.6, "as_p_listening")
pose("shearer", 38.05, "as_p_pointing")                    # final wide: pointing at Micah, laughing

# ---------------------------------------------------------------- Rooney: underplayed, dead-pan, then delighted
pose("rooney", 0.0, "wr_p_seated")
key("rooney", "look", 0.0, (-0.6, 0.0), 0.1)               # listening to Gary
key("rooney", "look", 4.95, (0.8, 0.0), 0.25)              # Micah starts on him
key("rooney", "smile", 4.95, 0.2, 0.4)
pulse("rooney", "nod", W("biggun"), 3.0, up=0.15, hold=0.15, down=0.35)
key("rooney", "look", 8.4, (0.4, -0.6), 0.3)               # a little eye-roll at "back in those days"
key("rooney", "look", 9.0, (0.8, 0.0), 0.3)
key("rooney", "look", 9.4, (-0.8, 0.0), 0.3)               # Shearer's turn
pose("rooney", 11.85, "wr_p_shrug")                        # "Everything!" - a shrug and a grin
key("rooney", "look", 11.9, (0.8, 0.0), 0.2)
pose("rooney", 13.05, "wr_p_talking")                      # then, calmly, the story
key("rooney", "look", 13.05, (0.0, 0.0), 0.2)
key("rooney", "look", W("micah"), (0.9, 0.0), 0.2)          # "...seen Micah" - a glance at the man himself
key("rooney", "look", 14.6, (0.0, 0.0), 0.3)
pose("rooney", T_CUT_OUT, "wr_p_seated")
key("rooney", "look", T_CUT_OUT, (0.9, 0.0), 0.1)
pose("rooney", 33.87, "wr_p_seated")
pulse("rooney", "tilt", 35.0, -5.0, up=0.15, hold=0.3, down=0.4)
pose("rooney", 38.05, "wr_p_handsup")                     # "why did you have to say that?" - innocent hands up
key("rooney", "look", 38.05, (0.9, 0.0), 0.2)

# ---------------------------------------------------------------- Micah: cocky, then caught out
pose("micah", 0.0, "m2_p_seated|f")
key("micah", "brow", 0.0, -0.3, 0.3)                        # already suspicious: he knows which story is coming
key("micah", "look", 2.6, (0.6, 0.0), 0.3)
key("micah", "look", 4.0, (0.0, 0.0), 0.3)
pose("micah", 4.85, "m2_p_talking|f")                      # "We did, didn't we?" - teasing Rooney
key("micah", "look", 4.85, (0.0, 0.0), 0.2)
key("micah", "brow", 4.85, 0.3, 0.3)
pose("micah", W("giving it"), "m2_p_pointing|f")           # "you were giving it the biggun" - points at him
key("micah", "brow", W("biggun") - 0.1, 0.9, 0.12)
key("micah", "brow", W("biggun") + 0.6, 0.3, 0.4)
key("micah", "look", W("back in"), (0.8, 0.0), 0.2)         # a tiny sideways look towards Gary
pose("micah", 9.25, "m2_p_seated|f")
key("micah", "look", 9.3, (0.9, 0.0), 0.3)
pose("micah", W("everything") - 0.08, "m2_p_handsup|f")    # "Everything!"
key("micah", "brow", W("everything") - 0.08, 1.0, 0.1)
pose("micah", 12.75, "m2_p_seated|f")
key("micah", "look", 13.2, (0.6, 0.0), 0.3)
key("micah", "brow", 13.6, -0.5, 0.4)                       # "I've actually seen Micah..." - the grin starts to go
pose("micah", T_CUT_OUT, "mr_e_embarrassed")              # the match cut from the restaurant
pose("micah", 33.87, "m2_p_talking|f")                     # "It's the Premier League!"
key("micah", "brow", 33.87, 0.7, 0.2)
pose("micah", W("big thing"), "m2_p_shrug|f")              # "it's a big thing"
pulse("micah", "tilt", W("big thing") + 0.2, -6.0, up=0.18, hold=0.2, down=0.3)
pose("micah", W("for me"), "m2_p_pointing|f")              # "...for me, Wayne"
pose("micah", W("why did"), "m2_p_shrug|f")                # "Why did you have to say that?"
key("micah", "look", 40.75, (0.0, -1.0), 0.15)             # ...and notices the little 50 balloon behind him
pulse("micah", "shrug", 40.0, 1.0, up=0.18, hold=0.25, down=0.3)

# ================================================================ ACTING CUES (flashback)
FAM = ("wr", "cr", "b1", "b2", "b3", "b4")
for c in FAM:
    pose(c, 0.0, f"{c}_p_seated")
# R2: a quiet meal
for tt, c in ((17.4, "wr"), (18.2, "cr"), (19.0, "b3"), (19.9, "b1")):
    pulse(c, "nod", tt, 3.0, up=0.25, hold=0.25, down=0.4)
# R3: Rooney notices something off camera: brows down, eyes narrow, the eyes slide right
key("wr", "look", W("micah comes"), (1.0, 0.0), 0.35)
key("wr", "brow", W("micah comes") + 0.1, -0.9, 0.3)
key("wr", "blinkx", W("micah comes") + 0.2, 0.42, 0.3)
key("wr", "turn", W("micah comes") + 0.3, 0.6, 0.6)
# R6: the stare, held too long; Coleen looks at the party, then at Rooney; one boy leans in, one is confused;
#     then Rooney's tiny amused shake of the head
T_SO = W("so i was")
for c in FAM:
    key(c, "look", T_SO, (1.0, 0.0), 0.3)
key("wr", "blinkx", T_SO, 0.25, 0.2)
key("wr", "turn", T_SO, 0.6, 0.2)
pose("cr", T_SO, "cr_p_reaction")
key("cr", "look", T_SO + 0.9, (-1.0, 0.0), 0.2)              # ...then at Rooney
key("b2", "fwd", T_SO + 0.4, 1.4, 0.5)                        # leans in to see
pose("b3", T_SO + 0.6, "b3_e_confused")
key("wr", "smile", 27.6, 0.6, 0.25)
key("wr", "tilt", 27.6, 4.0, 0.12)
key("wr", "tilt", 27.76, -4.0, 0.15)
key("wr", "tilt", 27.92, 3.0, 0.15)
key("wr", "tilt", 28.1, 0.0, 0.2)
# R8: seen from Micah's side, the family is laughing at the far table
for c in FAM:
    pose(c, 29.25, f"{c}_p_laughing" if c != "wr" else "wr_e_laughing")
# R9: Rooney: eyebrows up on "fiftieth"
pose("wr", T_FIFTIETH - 0.02, "wr_p_seated")
key("wr", "look", T_FIFTIETH - 0.02, (1.0, 0.0), 0.05)
key("wr", "blinkx", T_FIFTIETH - 0.02, 0.0, 0.05)
key("wr", "brow", T_FIFTIETH - 0.02, 1.0, 0.12)
key("wr", "smile", T_FIFTIETH, 0.4, 0.3)
key("wr", "turn", T_FIFTIETH - 0.02, 0.3, 0.1)

# ---------------------------------------------------------------- Micah at the party
perf.APPEAR.update(ravi=W("twenty"), jamie=W("about"), film=W("guys"))
perf.CROWD_WINDOW = (W("about"), W("guys") + 0.1)
pose("mi", 22.0, "dance")
pose("mi", 24.40, "placard")
pose("mi", 26.40, "dance")
pose("mi", 30.15, "freeze")                                 # he has seen Rooney
pose("mi", 31.40, "cool")                                   # hands in pockets on the table: nothing to see here
pose("mi_cu", 32.07, "mr_e_embarrassed")

perf.finalize()

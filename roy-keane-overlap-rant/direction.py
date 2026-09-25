"""Performance + camera direction for the scene (all times global, seconds)."""

# Which head drawing is used when (swapped on a hard cut, like cut-out animation)
EXPRESSIONS = [
    (0.00, "FRONT"),       # stern resting face before he starts
    (1.45, "SKEPTICAL"),   # "Manchester United."
    (3.30, "DISGUSTED"),   # "It's the same rubbish every week."
    (7.10, "ANGRY"),       # "No urgency, no aggression, no standards."
    (11.80, "SKEPTICAL"),  # "You lose the ball and stroll back like you're walking the dog."
    (16.05, "SAD"),        # "That shirt used to mean something."
    (18.55, "ANGRY"),      # "Stop pointing fingers, stop making excuses..."
    (25.35, "DISGUSTED"),  # "And don't give me this nonsense about confidence."
    (28.15, "ANGRY"),      # "You're playing for Manchester United."
    (30.55, "SHOUTING"),   # "Run, tackle, compete."
    (33.25, "CONFUSED"),   # "Is that too much to ask?"
    (35.00, "SKEPTICAL"),
    (36.10, "DISGUSTED"),  # "I see players losing the ball and throwing their arms up."
    (39.75, "ANGRY"),      # "Get back and win it."
    (42.10, "FRONT"),      # the stare
]

# Head turns during silences (full drawing swaps, no lip sync needed)
HEAD_TURNS = [
    (0.00, "3/4 RIGHT"),   # looking across the table at a co-host...
    (0.95, None),          # ...then turns to camera
]

# Shots: (start, end, (cx0, cy0, w0), (cx1, cy1, w1))  world = background pixels (1672x941)
HEAD = (668, 437)
SHOTS = [
    (0.00, 3.20, (836, 470, 1560), (730, 470, 1120)),     # wide establishing push-in
    (3.20, 7.05, (668, 492, 700), (668, 490, 640)),       # medium: the shrug
    (7.05, 11.75, (668, 478, 560), (668, 474, 480)),      # medium close: the chops, slow push
    (11.75, 16.00, (700, 488, 860), (690, 486, 760)),     # medium-wide: strolling / walking the dog
    (16.00, 18.55, (668, 468, 470), (668, 462, 400)),     # close: hand on heart
    (18.55, 21.71, (668, 490, 660), (668, 488, 600)),     # medium
    (21.71, 25.30, (668, 480, 540), (668, 476, 480)),     # medium close
    (25.30, 28.10, (675, 492, 700), (672, 490, 640)),     # medium: the flick
    (28.10, 30.50, (668, 474, 500), (668, 470, 450)),     # medium close
    (30.50, 31.37, (668, 488, 640), (668, 488, 620)),     # "Run"      punch-in 1
    (31.37, 32.16, (668, 470, 470), (668, 470, 450)),     # "tackle"   punch-in 2
    (32.16, 33.22, (668, 452, 330), (668, 452, 310)),     # "compete"  punch-in 3
    (33.22, 35.50, (668, 490, 720), (668, 488, 660)),     # medium: big shrug
    (35.50, 39.70, (720, 480, 1150), (700, 480, 960)),    # wide-ish: arms thrown up
    (39.70, 99.00, (668, 478, 560), (668, 458, 380)),     # push in to the final stare
]
FADE_OUT = 0.6

"""The dialogue edit of The Undercard, cut tight: lines follow each other a few frames apart (sitcom pace), the jokes
keep the pause they need and no more, and the fight gets the room: a face-off, five exchanges, a slow-motion double
miss and the clinch. Every shot, look, pose and sound hangs off these marks, so a re-recorded line retimes the film.
A ("gap", s, "mark") mark names the START of the gap."""
import json

from studio.film import ep
from studio.film.timeline import build

L = json.loads(ep.path("lines.json").read_text())

SEQ = [
    ("gap", 2.4, "title"),                    # title card
    # ---- 1. the ban: press area
    ("gap", 0.9, "open"),
    ("line", "L001"),
    ("gap", 0.16, "c_sec1"), ("line", "L002"),
    ("gap", 0.12, "c_ed2"), ("line", "L003"),
    ("gap", 0.14, "c_sec2"), ("line", "L004"),
    ("gap", 0.16, "c_ed3"), ("line", "L005"),
    ("gap", 0.45),
    ("gap", 1.1, "c_bay"),                    # loading bay: Dana studying the building
    ("line", "L006"),
    ("gap", 0.2), ("gap", 2.0, "trolley"),    # the laundry trolley rolls past
    ("gap", 0.4, "look_cam"),                 # Dana looks at it, then at us: 12 frames
    ("line", "L007"),
    ("gap", 0.3),
    ("gap", 1.3, "c_shoe"),                   # smash cut: his shoe disappears under towels
    # ---- 2. the world's angriest towel: corridor
    ("gap", 1.7, "c_track"),                  # low tracking shot beside the trolley; security steps in
    ("line", "L008"),
    ("gap", 0.12), ("line", "L009"),
    ("gap", 0.25, "c_bin1"), ("line", "L010"),
    ("gap", 0.2), ("gap", 0.6, "lid"),        # security looks down; the attendant presses the lid shut
    ("line", "L011"),
    ("gap", 0.2, "c_sec3"), ("line", "L012"),
    ("gap", 0.18, "c_att3"), ("line", "L013"),
    ("gap", 0.2), ("gap", 1.2, "aside"),      # security steps aside, the trolley rolls on
    ("gap", 1.0, "c_inside"),                 # a bald dome slowly rises above the linen
    ("line", "L014"),
    ("gap", 0.0, "bump"),                     # the trolley hits the cable protector
    ("gap", 0.4, "freeze"),                   # freeze on his eyes
    ("gap", 1.25, "tumble"),                  # three tumble poses: he lands at Fury's feet
    ("gap", 0.55, "landed"),
    # ---- 3. Fury finds a promoter
    ("line", "L015"),
    ("gap", 0.18, "c_dana1"), ("line", "L016"),
    ("gap", 0.18, "c_fury2"), ("line", "L017"),
    ("gap", 0.15, "c_dana2"), ("line", "L018"),
    ("gap", 0.18, "c_fury3"), ("line", "L019"),
    ("gap", 0.3, "c_aj"),                     # Joshua appears, deadpan eyeline down
    ("line", "L020"),
    ("gap", 0.15, "c_fury4"), ("line", "L021"),
    ("gap", 0.25), ("gap", 1.6, "c_eddie"),   # Eddie walks in, stops; eye dart bin, Dana, security
    ("gap", 0.5, "dart"),
    ("line", "L022"),
    ("gap", 0.2, "c_dana3"), ("line", "L023"),
    ("gap", 0.15, "c_ed4"), ("line", "L024"),
    ("gap", 0.15, "c_dana4"), ("line", "L025"),
    # ---- 4. negotiations
    ("gap", 0.25), ("gap", 0.9, "c_neg"),     # two-shot: Eddie takes the towel off with his fingertips
    ("line", "L026"),
    ("gap", 0.15), ("line", "L027"),
    ("gap", 0.25, "c_fine"), ("line", "L028"),
    ("gap", 1.0, "surprise"),                 # both surprised Eddie said yes
    ("gap", 0.1, "c_list"), ("line", "L029"),
    ("gap", 0.18, "c_dana5"), ("line", "L030"),
    ("gap", 0.15, "c_ed5"), ("line", "L031"),
    ("gap", 0.25, "c_fj1"), ("line", "L032"),
    ("gap", 0.15), ("line", "L033"),
    ("gap", 0.4),
    ("gap", 3.2, "c_prep"),                   # dressing room: Eddie reluctant, Dana shadowboxes too hard
    # ---- 5. special announcement
    ("gap", 2.0, "c_arena"),                  # arena wide, crowd swell, the sting
    ("line", "L034"),
    ("gap", 0.2, "c_fj2"), ("gap", 1.0),      # ringside: disbelieving joy
    ("gap", 0.1, "c_ann2"), ("line", "L035"),
    ("gap", 0.12, "c_ed_in"), ("gap", 1.2),   # Eddie tries smiling, brows panic; mixed cheer
    ("gap", 0.1, "c_ann3"), ("line", "L036"),
    ("gap", 0.12, "c_da_in"), ("gap", 1.8),   # Dana raises gloves; boos; the attendant takes the towel
    ("gap", 0.1, "c_ref"), ("line", "L037"),
    ("gap", 0.18, "c_ed6"), ("line", "L038"),
    ("gap", 0.35),
    # ---- 6. the fight
    ("gap", 0.7, "bell"),
    ("gap", 2.4, "faceoff"),                  # silent face-off: both bounce, nobody punches
    ("gap", 0.5, "cough"),
    ("gap", 0.1, "c_ty1"), ("line", "L039"),
    ("gap", 0.2, "c_fight"),
    ("gap", 2.2, "ex1"),                      # Eddie's long jab; Dana leans back too far, windmills
    ("gap", 1.3, "ex2"),                      # Dana's short jab taps Eddie's guard: the squeak; the music stops
    ("gap", 0.15, "c_ed7"), ("line", "L040"),
    ("gap", 0.15, "c_da7"), ("line", "L041"),
    ("gap", 0.15, "c_ed8"), ("line", "L042"),
    ("gap", 0.25, "c_ex3"),
    ("gap", 1.6, "ex3a"),                     # Eddie's flurry: jab, jab, jab; Dana bobs under all three
    ("gap", 1.4, "ex3b"),                     # Dana's counter: a body jab; Eddie covers up and stumbles back
    ("gap", 1.4, "ex3c"),                     # Eddie lunges back with a wild cross; Dana ducks; Eddie spins past
    ("gap", 2.0, "ex3d"),                     # slow motion: both throw haymakers, both miss, the crowd: oooh
    ("gap", 0.9, "c_wince"),                  # ringside: Fury and Joshua wince
    ("gap", 1.2, "ex3e"),                     # exhausted, they fall into a clinch
    ("gap", 0.1, "c_cl1"), ("line", "L043"),
    ("gap", 0.15), ("line", "L044"),
    ("gap", 0.15, "c_ref2"), ("line", "L045"),
    ("gap", 1.5, "sep"),                      # they separate, wobble, lean together again
    ("gap", 0.1, "c_fj3"), ("line", "L046"),
    ("gap", 0.15), ("line", "L047"),
    ("gap", 0.2, "c_cl2"), ("line", "L048"),
    ("gap", 0.18), ("line", "L049"),
    ("gap", 0.18), ("line", "L050"),
    ("gap", 0.18), ("line", "L051"),
    ("gap", 0.3, "bell2"),
    ("gap", 2.0, "arms"),                     # both raise their arms; the ref looks at a blank card
    # ---- 7. decision and callback
    ("gap", 0.1, "c_ann4"), ("line", "L052"),
    ("gap", 0.3, "c_ed9"), ("line", "L053"),
    ("gap", 0.15, "c_da9"), ("line", "L054"),
    ("gap", 0.25, "c_fj4"), ("line", "L055"),
    ("gap", 0.15), ("line", "L056"),
    ("gap", 0.3), ("gap", 1.8, "c_trolley"),  # the attendant pushes the trolley in between them
    ("line", "L057"),
    ("gap", 0.4, "glance"),                   # Dana glances at Eddie; Eddie points at the exit
    ("gap", 1.4, "climb"),                    # Dana climbs into the bin
    ("line", "L058"),
    ("gap", 0.12), ("line", "L059"),
    ("gap", 1.4, "rollout"),                  # rolled off, still bickering
    ("gap", 1.7, "c_end"),                    # Fury and Joshua staring; the wheel squeak
    ("gap", 1.0, "black"),
]

TL = build(SEQ, L)

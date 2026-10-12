"""The dialogue edit of The Undercard (v5, about 228 s). The pack's director's plan (pack/v5/SHOT_AND_ANIMATION_PLAN.md)
in edit marks: the physical beats get their own time (the tape, the trolley and its brake, the shoes, the inside
of the bin, the stare-down, the fall as a chain of causes, the recognition, the payment, the silence after "Fine",
the preparation inserts, the ropes, the bell and the two confident bounces that fizzle out, five fight beats, the
sit-down, the exit down the steps, the fare card), and the jokes keep the pause they need and no more. Every shot,
look, pose and sound hangs off these marks, so a re-recorded line retimes the film. A ("gap", s, "mark") mark names
the START of the gap."""
import json

from studio.film import ep
from studio.film.timeline import build

L = json.loads(ep.path("lines.json").read_text())

SEQ = [
    # ---- 1. Eddie's ban: press area
    ("gap", 0.3, "open"),                     # close on the poster: his hand presses the last strip of tape
    ("gap", 1.4, "tape"),                     # the tape clings to his cuff; he shakes it off, still grand
    ("gap", 1.2, "admire"),                   # he steps back to admire it (the title over the action, 2 s)
    ("line", "L001"),
    ("gap", 0.3, "c_sec1"), ("line", "L002"),
    ("gap", 0.15, "c_ed2"), ("line", "L003"),
    ("gap", 0.35, "c_sec2"), ("line", "L004"),
    ("gap", 0.25, "c_ed3"), ("line", "L005"),
    ("gap", 0.75, "c_secreact"),              # the guard, deadpan: one blink
    ("gap", 0.35),
    # ---- 1b. the loading bay
    ("gap", 1.3, "c_bay"),                    # Dana studies the staff door
    ("gap", 1.3, "collar"),                   # turns his collar up for a disguise; turns it down again
    ("line", "L006"),
    ("gap", 0.5),
    # ---- 2. laundry infiltration
    ("gap", 1.8, "trolley_in"),               # the attendant pushes the trolley in; Dana falls in alongside
    ("gap", 0.8, "c_wheels"),                 # low: wheels and feet; she brakes (clunk)
    ("gap", 0.25, "c_two"), ("line", "L007"),
    ("gap", 0.2), ("line", "L008"),
    ("gap", 0.25), ("line", "L009"),
    ("gap", 0.3), ("line", "L010"),
    ("gap", 0.55, "c_offer"), ("line", "L011"),
    ("gap", 0.35, "c_pivot"), ("line", "L012"),       # she turns on the offer
    ("gap", 0.25, "c_insult"), ("line", "L013"),
    ("gap", 0.3, "c_att2"), ("line", "L014"),
    ("gap", 1.9, "shoes"),                   # one shoe off, a hop, the other; both into the bin
    ("gap", 1.6, "climb_in"),                 # in he goes, shoes and all
    ("gap", 1.4, "c_inbin"),                  # inside: Dana between the towels with his shoes; the lid shuts
    ("gap", 0.3),
    # ---- 2b. the checkpoint: the reverse corridor
    ("gap", 1.3, "c_check"),                  # the trolley arrives at the guard
    ("line", "L015"),
    ("gap", 0.3), ("line", "L016"),
    ("gap", 0.25, "c_bintalk"), ("line", "L017"),     # from inside
    ("gap", 0.2, "c_lid"), ("line", "L018"),          # she leans on the lid
    ("gap", 0.45, "c_stare"),                 # the guard looks from the trolley to her face; she holds it
    ("gap", 1.1, "giveway"),                  # the pause; he gives way
    ("gap", 0.4),
    # ---- 3. the delivery: the corridor
    ("gap", 1.2, "c_roll"),                   # low, tracking with the trolley
    ("gap", 0.45, "c_ramp"),                  # the wheel hits the cable ramp
    ("gap", 0.45, "brace"),                   # her front foot braces; the towels shift; the lid flips open
    ("gap", 0.55, "grab"),                    # his hands come up for the rim and miss
    ("gap", 0.85, "tumble"),                  # over the front
    ("gap", 0.5, "land"),                     # down at Fury's feet; the shoes slide on; Fury steps back
    ("gap", 0.5, "c_pov"),                    # low, from the floor: Fury very tall
    ("line", "L019"),
    ("gap", 0.25, "c_dana1"), ("line", "L020"),
    ("gap", 0.25, "c_fury2"), ("line", "L021"),
    ("gap", 0.35, "c_aj"), ("line", "L022"),          # Joshua walks into the eyeline
    ("gap", 0.2, "c_fury3"), ("line", "L023"),
    ("gap", 0.35),
    ("gap", 1.2, "c_eddie"),                  # Eddie comes round the corner, stops at a shoe
    ("gap", 0.9, "recog"),                    # the towel, the bin, then Dana: held
    ("line", "L024"),
    ("gap", 0.25, "c_up"), ("line", "L025"),          # Dana stands too fast
    ("gap", 0.2, "c_ed4"), ("line", "L026"),
    ("gap", 0.2, "c_dana4"), ("line", "L027"),
    ("gap", 0.3, "c_sec4"), ("line", "L028"),
    ("gap", 0.25, "c_ed5"), ("line", "L029"),
    ("gap", 0.35, "c_pay"), ("line", "L030"),         # her hand out
    ("gap", 1.3, "pays"),                     # Dana pays, slowly; Eddie watches, offended someone else made money
    # ---- 4. the challenge
    ("gap", 0.25, "c_out"), ("line", "L031"),
    ("gap", 0.25, "c_close"), ("line", "L032"),
    ("gap", 0.3, "c_fine"), ("line", "L033"),
    ("gap", 0.7, "silence"),                  # room tone
    ("gap", 0.6, "c_reg_e"),                 # Eddie realises
    ("gap", 0.6, "c_reg_d"),                 # Dana realises
    ("gap", 0.2),
    # ---- 4b. preparation (the corridor, in kit), Fury and Joshua watching
    ("gap", 0.8, "c_jacket"),                 # insert: Eddie's jacket comes off
    ("line", "L034"),
    ("gap", 0.3, "c_strap"),                  # insert: Dana's glove strap yanked much too tight
    ("line", "L035"),
    ("gap", 0.3, "c_phone"),                  # insert: Eddie cannot work his phone in gloves
    ("line", "L036"),
    ("gap", 0.3, "c_kit"), ("line", "L037"),
    ("gap", 0.2), ("line", "L038"),
    ("gap", 0.3), ("line", "L039"),
    ("gap", 0.2), ("line", "L040"),
    ("gap", 0.35, "c_fj"), ("line", "L041"),
    ("gap", 0.3), ("line", "L042"),
    ("gap", 0.4),
    # ---- 5. the additional contest: the arena
    ("gap", 1.4, "c_arena"),                  # the crowd swells into the arena wide
    ("gap", 1.1, "ropes"),                    # the two promoters duck through the ropes, badly
    ("gap", 0.2, "c_ann1"), ("line", "L043"),
    ("gap", 0.4, "c_ann2"), ("line", "L044"),
    ("gap", 0.25, "c_ed_conf"),               # Eddie's confident smile, panicking brows
    ("gap", 0.7),
    ("gap", 0.1, "c_ann3"), ("line", "L045"),
    ("gap", 0.2, "c_da_in"),                  # Dana lifts the gloves; the attendant takes the towel off his shoulder
    ("gap", 1.6, "towel"),
    ("gap", 0.3, "c_ref"), ("line", "L046"),
    ("gap", 0.25, "c_ed_q"), ("line", "L047"),
    ("gap", 0.45),
    # ---- 6. one disastrous round
    ("gap", 0.8, "bell"),
    ("gap", 1.5, "bounce"),                   # both bounce, full of it, two beats
    ("gap", 1.0, "slow"),                     # Dana slows first; Eddie notices and stops too
    ("gap", 1.0, "silence2"),                 # nothing happens; one cough
    ("gap", 0.2, "c_ty1"), ("line", "L048"),
    ("gap", 0.3, "c_probe"),
    ("gap", 1.6, "probe"),                    # Eddie's long probing jab; Dana overreacts, ducks, peers up
    ("gap", 0.15, "c_da2"), ("line", "L049"),
    ("gap", 0.2, "c_ed2b"), ("line", "L050"),
    ("gap", 0.3, "tap"),                      # the second jab taps Dana's guard; Dana counters into the red gloves
    ("gap", 1.1),
    ("gap", 0.1, "c_da3"), ("line", "L051"),
    ("gap", 0.2, "c_ed3b"), ("line", "L052"),
    ("gap", 0.2, "c_da3b"), ("line", "L053"),
    ("gap", 0.2, "c_ed3c"), ("line", "L054"),
    ("gap", 0.3, "counter"),                  # Dana's counter lands on Eddie's raised gloves
    ("gap", 0.7),
    ("gap", 0.1, "c_ed_ind"), ("line", "L055"),
    ("gap", 0.2, "c_da4"), ("line", "L056"),
    ("gap", 0.2, "c_ed4b"), ("line", "L057"),
    ("gap", 1.7, "advance"),                  # Dana comes forward: three steps, two punches; Eddie backpedals
    ("gap", 0.5, "ropes2"),                   # Eddie's back hits the ropes in the red corner
    ("gap", 0.85, "recoil"),                   # his counter misses; the ropes throw him into Dana: a clinch
    ("gap", 0.8, "clinch"),
    ("line", "L058"),
    ("gap", 0.25), ("line", "L059"),
    ("gap", 0.35), ("line", "L060"),
    ("gap", 0.25), ("line", "L061"),
    ("gap", 0.25), ("line", "L062"),
    ("gap", 0.4), ("line", "L063"),
    ("gap", 0.45, "lift"),                    # Dana lifts a glove an inch; Eddie dives back into the clinch
    ("gap", 0.45),
    ("line", "L064"),
    ("gap", 0.3, "c_ref2"), ("line", "L065"),
    ("gap", 0.15), ("line", "L066"),
    ("gap", 0.8, "c_aj2"), ("line", "L067"),          # the silence after the joke, then Joshua
    ("gap", 0.25, "c_ty2"), ("line", "L068"),
    ("gap", 0.4, "sep"),                      # the referee prises them apart
    ("gap", 1.1, "windup"),                   # both load up an enormous finish
    ("gap", 0.5, "clash"),                    # glove meets glove
    ("gap", 0.8, "wobble"),
    ("gap", 0.7, "sit"),                      # knees go; both sit down on the same beat
    ("gap", 0.75, "look"),                    # the exhausted look, held
    ("gap", 0.5, "bell2"),
    ("gap", 1.4, "helpup"),                   # the referee hauls them up
    # ---- 7. the decision and the series button
    ("gap", 0.2, "c_ann4"), ("line", "L069"),
    ("gap", 0.25, "c_ed9"), ("line", "L070"),
    ("gap", 0.15, "c_da9"), ("line", "L071"),
    ("gap", 0.35, "c_fj4"), ("line", "L072"),
    ("gap", 0.2), ("line", "L073"),
    ("gap", 2.2, "c_steps"),                  # the promoters come down the ring steps
    ("gap", 0.7, "c_bin"),                    # the bin waits by the apron; Dana's hand on the rim
    ("gap", 0.6, "card"),                     # she slaps a fare card on it
    ("line", "L074"),
    ("gap", 0.25, "c_da10"), ("line", "L075"),
    ("gap", 0.3, "c_att10"), ("line", "L076"),
    ("gap", 0.75, "c_eddie10"),               # Eddie, delighted: she out-negotiated both of them
    ("gap", 1.3, "climb2"),                   # Dana climbs into the bin
    ("gap", 1.9, "depart"),                   # the wheel squeak; the end title over the departing trolley
    ("gap", 0.3, "black"),
]

TL = build(SEQ, L)

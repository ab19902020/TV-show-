"""Camera direction: shots cut on the pauses (world = background px, 1672x941).
Full-body wides for every walk, medium shots for the talking, and slow pushes / punch-ins on the key lines.
Each shot: (start, end, (cx, cy, width) at start, (cx, cy, width) at end, punch-in?)"""
import perf
from perf import W, DESK, ACROSS, PACE_END, WINDOW, CHAIR, FRONT_DESK, SEAT_DROP, head_top
FADE_IN, FADE_OUT = 0.6, 0.9

def on(place, w, seated=0.0, dx=0.0, room=0.08):
    """frame of width w on him: his head just below the top of frame (headroom = room x frame height)"""
    h = w * 9 / 16
    return (place[0] + dx, head_top(place, seated) - room * h + h / 2, w)

def shots():
    S = []
    def shot(t0, t1, a, b, punch=False): S.append((t0, t1, a, b, punch))
    c = lambda w, n=1: W(w, n) - 0.3                        # cut a beat before the word
    shot(0.0, c("co"), on(DESK, 900), on(DESK, 780))                                       # "Hi, I'm Jim Ratcliffe"
    shot(c("co"), c("and"), on(DESK, 620), on(DESK, 580))                                 # proud posture
    shot(c("and"), perf.T_WALK1 - 0.1, on(DESK, 520), on(DESK, 440))                      # dead-pan push-in
    shot(perf.T_WALK1 - 0.1, c("britain"), (980, 468, 1480), (960, 468, 1420))             # wide: strolls across
    shot(c("britain"), c("we've"), on(ACROSS, 620), on(ACROSS, 560))                      # the chop
    shot(c("we've"), c("you"), on(ACROSS, 900, dx=110), on(PACE_END, 880, dx=-40))        # pacing, counting
    shot(c("you"), perf.T_WIN - 0.05, on(PACE_END, 500), on(PACE_END, 440))              # "simply cannot"
    shot(perf.T_WIN - 0.05, c("britain", 2), (1120, 452, 1180), (1110, 450, 1080))        # wide: to the window, the view
    shot(c("britain", 2), c("ordinary"), on(WINDOW, 560, dx=-60), on(WINDOW, 520, dx=-60))  # side-on, lecturing the view
    shot(c("ordinary"), c("work"), on(WINDOW, 600), on(WINDOW, 560))                      # jacket, belt tug
    shot(c("work"), perf.T_GLANCE - 0.1, on(WINDOW, 470), on(WINDOW, 450))                # point + chop
    shot(perf.T_GLANCE - 0.1, c("but"), on(WINDOW, 820, dx=-80), on(WINDOW, 760, dx=-80)) # glance back at Monaco, shrug
    shot(c("but"), perf.T_LEAVE_WIN, on(WINDOW, 450), on(WINDOW, 380))                   # "SENSIBLE financial decision"
    shot(perf.T_LEAVE_WIN, perf.T_SIT - 0.2, (840, 470, 1672), (760, 470, 1500))          # wide: back along the desk
    shot(perf.T_SIT - 0.2, c("people", 3), on(CHAIR, 980), on(CHAIR, 660, SEAT_DROP))       # sits (camera settles with him)
    shot(c("people", 3), perf.T_STAND - 0.1, on(CHAIR, 640, SEAT_DROP), on(CHAIR, 600, SEAT_DROP))
    shot(perf.T_STAND - 0.1, c("ships"), on(CHAIR, 760), on(CHAIR, 720))                 # stands: "Factories"
    shot(c("ships"), c("industry"), on(CHAIR, 680), on(CHAIR, 670), True)                 # "Ships"
    shot(c("industry"), perf.T_PACE2, on(CHAIR, 600), on(CHAIR, 590), True)               # "Industry"
    shot(perf.T_PACE2, c("and", 4), on(CHAIR, 1000, dx=180), on(FRONT_DESK, 960, dx=-60))  # paces
    shot(c("and", 4), c("simple"), on(FRONT_DESK, 640), on(FRONT_DESK, 590))             # "what's the solution?"
    shot(c("simple"), c("work", 2), on(FRONT_DESK, 660), on(FRONT_DESK, 650), True)       # four points at camera
    shot(c("work", 2), c("spend"), on(FRONT_DESK, 600), on(FRONT_DESK, 590), True)
    shot(c("spend"), c("stop"), on(FRONT_DESK, 550, dx=30), on(FRONT_DESK, 540, dx=30), True)
    shot(c("stop"), W("complaining", 1, "e") + 0.6, on(FRONT_DESK, 500, dx=40), on(FRONT_DESK, 490, dx=40), True)
    shot(W("complaining", 1, "e") + 0.6, perf.T_LOOK_OUT - 0.05, on(FRONT_DESK, 640), on(FRONT_DESK, 600))  # watch
    shot(perf.T_LOOK_OUT - 0.05, 999, (880, 470, 1560), (840, 470, 1672))                  # wide: leaves; empty office
    return S

SHOTS = shots()

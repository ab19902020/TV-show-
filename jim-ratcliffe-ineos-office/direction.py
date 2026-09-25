"""Camera direction: TV-style shot list cut on the pauses (world = background px, 1672x941).
Each shot: (start, end, (cx, cy, width) at start, (cx, cy, width) at end, punch-in?)"""
import perf
W = perf.W
X = perf.MARK_X
FADE_IN, FADE_OUT = 0.5, 0.9

TOP = 226          # world y of the frame top in shots on him: keeps headroom above his hair

def shots():
    S = []
    def fix(v):                      # (cx, None, w) -> cy from the headroom rule
        cx, cy, w = v
        return (cx, TOP + w * 9 / 32 if cy is None else cy, w)
    def shot(t0, t1, a, b, punch=False): S.append((t0, t1, fix(a), fix(b), punch))
    b = lambda w, n=1: W(w, n) - 0.25          # cut a beat before the word
    shot(0.0, b("hi"), (836, 470, 1672), (930, 468, 1420))                                  # establishing: he walks in
    shot(b("hi"), b("britain"), (1085, 452, 900), (1095, 448, 820))                         # "Hi, I'm Jim Ratcliffe..."
    shot(b("britain"), b("we've"), (X, None, 640), (X, None, 560))                            # "Britain is going backwards"
    shot(b("we've"), b("you"), (1090, 452, 820), (1095, 450, 760))                          # the list
    shot(b("you"), b("i"), (X, None, 470), (X, None, 420))                                    # close: "You simply cannot..."
    shot(b("i"), b("britain", 2), (990, 445, 1300), (1020, 442, 1140))                     # wide with the view
    shot(b("britain", 2), b("ordinary"), (X, None, 640), (X, None, 590))
    shot(b("ordinary"), b("work"), (X, 460, 840), (X, 458, 800))                            # hands on hips
    shot(b("work"), b("obviously"), (X, None, 560), (X, None, 520))
    shot(b("obviously"), b("but"), (1160, 450, 920), (1150, 448, 860))                     # points at the harbour
    shot(b("but"), b("what"), (X, None, 480), (X, None, 420))                                 # close: "sensible decision"
    shot(b("what"), b("cuts"), (X, None, 640), (X, None, 600))
    shot(b("cuts"), b("efficiency"), (X, None, 470), (X, None, 450), True)                   # punch-in on "cuts"
    shot(b("efficiency"), b("preferably"), (X, None, 640), (X, None, 620))
    shot(b("preferably"), b("people", 3), (1080, 452, 880), (1085, 450, 820))
    shot(b("people", 3), b("factories"), (X, None, 640), (X, None, 600))
    shot(b("factories"), b("now"), (1060, 450, 1020), (1070, 448, 940))                    # arms wide
    shot(b("now"), b("and", 4), (X, None, 580), (X, None, 500))                              # paperwork: slow push
    shot(b("and", 4), b("simple"), (X, None, 660), (X, None, 610))                           # "what's the solution?"
    shot(b("simple"), b("work", 2), (X, None, 620), (X, None, 600))
    shot(b("work", 2), b("spend"), (X, None, 540), (X, None, 520), True)                     # punch-ins
    shot(b("spend"), b("stop"), (X, None, 470), (X, None, 455), True)
    shot(b("stop"), b("anyway"), (X, None, 420), (X, None, 410), True)
    shot(b("anyway"), perf.RUN_TURN - 0.1, (1160, 450, 940), (1150, 448, 880))             # "the yacht's waiting"
    shot(perf.RUN_TURN - 0.1, 999, (1000, 468, 1400), (880, 470, 1600))                    # he scurries off
    return S

SHOTS = shots()

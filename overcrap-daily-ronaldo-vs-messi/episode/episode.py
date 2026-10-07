"""The Overcrap Daily - "Ronaldo vs Messi": staging.

Mark Goldbridge's studio. Mark and Rooney at the desk (front_a, wide), Roy
standing by the sofa with his arms crossed (reverse, wide). Rio is not there:
he bursts in through the door halfway through (wide), then argues from beside
Roy (reverse). Lines, delivery tags and order come from script.py; the
production pack's director notes drive the shots, faces and reaction beats.
"""
import math, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'tools', 'ep'))
import script as S                    # noqa: E402
import epengine as E                  # noqa: E402

# Mark's shouted lines: on their open vowels his shouting drawings show their own drawn shout
S.LOUD = {'MG_12', 'MG_21', 'MG_22', 'MG_26', 'MG_32', 'MG_34'}

# ------------------------------------------------------------------ cameras
FA_WIDE = (0, 0, 1672)
FA_TWO = (400, 190, 1130)
SW_THREE = (300, 150, 1080)
SW_FOUR = (90, 110, 1360)
SW_WIDE = (0, 0, 1672)
RV_WIDE = (0, 0, 1672)
RV_TWO = (420, 150, 880)


def _bg(name):
    import json
    return json.load(open(os.path.join(HERE, 'backgrounds', name + '.json')))


def single(bg, who, frac, xpos, ypos=0.40):
    """Framing with the seated face `frac` of the frame width, at `xpos` across."""
    s = _bg(bg)['seats'][who]
    fx, fy, fw = s['face'][0], s['face'][1], s['face_w']
    w = fw / frac
    h = w * 9 / 16
    return (fx - xpos * w, fy - ypos * h, w)


_EYE = {}


def eye_height(who):
    """Feet to eyes of a standing character, in face widths (from the full-body drawing)."""
    if who not in _EYE:
        rig = E.Rig(who)
        key = 'body/arms_crossed' if who == 'roy' else 'turnaround/front'
        info = rig.face(key)
        _EYE[who] = (info['feet'][1] - info['center'][1]) / info['width']
    return _EYE[who]


def standing(who, spot, frac, xpos=0.5, ypos=0.38, bg='reverse'):
    sp = _bg(bg)['spots'][spot]
    fw = sp['face_w']
    fx = sp['feet'][0]
    fy = sp['feet'][1] - eye_height(who) * fw
    w = fw / frac
    h = w * 9 / 16
    return (fx - xpos * w, fy - ypos * h, w)


M_MED = single('front_a', 'mark', 0.15, 0.42)
M_CU = single('front_a', 'mark', 0.30, 0.45)
M_XCU = single('front_a', 'mark', 0.40, 0.5, 0.42)
N_MED = single('front_a', 'rooney', 0.15, 0.58)
N_CU = single('front_a', 'rooney', 0.30, 0.55)


def _lazy(fn, *a, **k):
    """Standing framings need the rigs: work them out on first use."""
    box = {}

    def rect(R, t):
        if 'r' not in box:
            box['r'] = fn(*a, **k)
        return box['r']
    return rect


R_MED = _lazy(standing, 'roy', 'roy_stand', 0.13)
R_CU = _lazy(standing, 'roy', 'roy_stand', 0.22)
R_TIGHT = _lazy(standing, 'roy', 'roy_stand', 0.34)
I_MED = _lazy(standing, 'rio', 'rio_stand', 0.20, 0.5, 0.40)
I_CU = _lazy(standing, 'rio', 'rio_stand', 0.21, 0.5, 0.40)
I_TIGHT = _lazy(standing, 'rio', 'rio_stand', 0.29, 0.5, 0.42)

SHOTS = {
    'W': ('front_a', FA_WIDE, {}), '2': ('front_a', FA_TWO, {}),
    'M': ('front_a', M_MED, dict(dof=2.0, order=('mark',))), 'Mc': ('front_a', M_CU, dict(dof=5.0, order=('mark',))),
    'Mx': ('front_a', M_XCU, dict(dof=7.0, order=('mark',))),
    'N': ('front_a', N_MED, dict(dof=2.0, order=('rooney',))), 'Nc': ('front_a', N_CU, dict(dof=5.0, order=('rooney',))),
    'SW': ('wide', SW_THREE, {}), 'SW4': ('wide', SW_FOUR, {}), 'SWf': ('wide', SW_WIDE, {}),
    'R': ('reverse', R_MED, dict(dof=2.5, order=('roy',))), 'Rc': ('reverse', R_CU, dict(dof=6.0, order=('roy',))),
    'Rx': ('reverse', R_TIGHT, dict(dof=8.0, order=('roy',))),
    'I': ('reverse', I_MED, dict(dof=2.5, order=('rio',))), 'Ic': ('reverse', I_CU, dict(dof=6.0, order=('rio',))),
    'Ix': ('reverse', I_TIGHT, dict(dof=8.0, order=('rio',))),
    'RR': ('reverse', RV_TWO, dict(dof=1.5)), 'RW': ('reverse', RV_WIDE, {}),
}

# ------------------------------------------------------------------ staging
# line id -> (shot, body, face, [(word, change)...]); bodies are full drawing keys
# (Mark 'upper/..', Rooney 'upper/..', Roy 'body/..', Rio 'upper/..' or 'turnaround/front').
# change: a shot code cuts the camera at that word; 'body=...'/'face=...' swaps a drawing.
MU, NU, RB, IU = 'upper/', 'upper/', 'body/', 'upper/'
RIO_STAND = 'turnaround/front'
STAGE = {
    # cold open: Mark already mid-rant, Rooney curious, Roy motionless
    'MG_01': ('SW', MU + 'both_hands_out', 'smug', [("messi's", 'M'), ('hugged', 'body=shrug'), ('ordered', 'body=pointing'),
                                                     ('waving', 'body=both_hands_out')]),
    'MG_02': ('M', MU + 'both_hands_out', 'angry_rant', [('arguing', 'Mc'), ('arguing', 'face=shouting'),
                                                         ('telling', 'M'), ('telling', 'body=pointing'),
                                                         ('telling', 'face=angry_rant')]),
    'WR_01': ('Nc', NU + 'seated', 'confused', []),
    'MG_03': ('Mc', MU + 'arms_down', 'angry_rant', []),
    'RK_01': ('R', RB + 'arms_crossed', 'dry_humour', []),
    'MG_04': ('M', MU + 'both_hands_out', 'smug', [("other's", 'body=pointing'), ('darren', 'Mc')]),
    'WR_02': ('Nc', NU + 'seated', 'smug', []),
    'RK_02': ('Rc', RB + 'arms_crossed', 'thinking', []),
    'MG_05': ('M', MU + 'both_hands_out', 'angry_rant', [('imaginary', 'Mc')]),
    # Ronaldo / Portugal
    'MG_06': ('2', MU + 'arms_down', 'neutral', [('messi', 'M'), ('ronaldo', 'body=both_hands_out'), ('emergency', 'Mc')]),
    'RK_03': ('R', RB + 'palm_down', 'neutral', []),
    'MG_07': ('Mc', MU + 'pointing', 'smug', []),
    'WR_03': ('N', NU + 'explaining', 'neutral', []),
    'RK_04': ('Rc', RB + 'palm_down', 'annoyed', []),
    'MG_08': ('M', MU + 'both_hands_out', 'angry_rant', [("doesn't", 'body=shrug'), ('portugal', 'Mc'),
                                                         ('defcon', '!Mx'), ('defcon', 'face=shouting')]),
    'WR_04': ('N', NU + 'seated', 'neutral', []),
    'RK_05': ('R', RB + 'arms_crossed', 'neutral', []),
    'MG_09': ('M', MU + 'both_hands_out', 'neutral', [('cristiano', 'body=pointing'), ('without', 'Mc'),
                                                      ('army', 'face=angry_rant')]),
    'WR_05': ('Nc', NU + 'seated', 'smug', []),
    'RK_06': ('!Rx', RB + 'arms_crossed', 'disgust', []),
    'WR_06': ('N', NU + 'talking', 'smug', []),
    'RK_07': ('Rx', RB + 'pointing', 'neutral', []),
    'MG_10': ('Mc', MU + 'arms_down', 'sad', []),
    # Messi send-off
    'MG_11': ('M', MU + 'both_hands_out', 'smug', [('state', 'body=shrug'), ('alive', 'Mc')]),
    'RK_08': ('Rc', RB + 'arms_crossed', 'confused', []),
    'MG_12': ('Mc', MU + 'arms_down', 'shouting', []),
    'RK_09': ('R', RB + 'arms_crossed', 'neutral', []),
    'MG_13': ('M', MU + 'both_hands_out', 'angry_rant', [('emotion', 'Mc')]),
    'RK_10': ('Rx', RB + 'arms_crossed', 'neutral', []),
    'WR_07': ('Nc', NU + 'seated', 'smug', []),
    # Rio
    'RF_01': ('SWf', IU + 'warning', 'neutral', []),         # shouted as he comes through the door
    'MG_14': ('Mc', MU + 'arms_down', 'sad', []),
    'RF_02': ('I', RIO_STAND, 'neutral', []),
    'WR_08': ('Nc', NU + 'seated', 'confused', []),
    'RF_03': ('Ic', RIO_STAND, 'neutral', []),
    'MG_15': ('Mc', MU + 'arms_down', 'smug', []),
    'RF_04': ('Ic', IU + 'folded_arms', 'neutral', []),
    'MG_16': ('M', MU + 'pointing', 'smug', [('alarm', 'Mc')]),
    'RF_05': ('I', IU + 'shrug', 'neutral', [('greatest', 'Ic')]),
    'MG_17': ('M', MU + 'both_hands_out', 'confused', []),
    'RF_06': ('Ic', IU + 'folded_arms', 'side_eye', []),
    'RK_11': ('Rc', RB + 'arms_crossed', 'sarcastic', []),
    'RF_07': ('Ix', IU + 'folded_arms', 'head/front', []),
    # Forest
    'MG_18': ('M', MU + 'both_hands_out', 'neutral', []),
    'RF_08': ('I', IU + 'warning', 'neutral', []),
    'MG_19': ('Mc', MU + 'arms_down', 'angry_rant', []),
    'RF_09': ('Ic', IU + 'warning', 'neutral', []),
    'MG_20': ('Mc', MU + 'arms_down', 'angry_rant', []),
    'RF_10': ('Ic', IU + 'folded_arms', 'side_eye', [('forest', 'Ix')]),
    'MG_21': ('!Mx', MU + 'desk_rant', 'shouting', []),
    'MG_22': ('M', MU + 'desk_rant', 'shouting', [('forest', 'Mc')]),
    'RF_11': ('Ic', RIO_STAND, 'neutral', []),
    'MG_23': ('M', MU + 'both_hands_out', 'angry_rant', []),
    'RK_12': ('Rc', RB + 'arms_crossed', 'dry_humour', []),
    'RF_12': ('Ic', IU + 'folded_arms', 'side_eye', []),
    # Rio defends Ronaldo / ham
    'RF_13': ('Ic', RIO_STAND, 'neutral', []),                # the list ticks up beside him
    'MG_24': ('M', MU + 'both_hands_out', 'angry_rant', []),
    'RF_14': ('Ic', RIO_STAND, 'neutral', []),
    'MG_25': ('M', MU + 'shrug', 'smug', [('moon', 'Mc')]),
    'RF_15': ('Ix', IU + 'folded_arms', 'head/front', []),
    'WR_09': ('Nc', NU + 'seated', 'confused', []),
    'MG_26': ('!Mx', MU + 'desk_rant', 'shouting', []),
    'RF_16': ('Ic', IU + 'folded_arms', 'side_eye', []),
    'MG_27': ('M', MU + 'both_hands_out', 'confused', [('lunar', 'Mc'), ('lunar', 'face=angry_rant')]),
    # ending: a touch faster
    'MG_28': ('M', MU + 'pointing', 'smug', [('could', 'Mc')]),
    'RF_17': ('Ic', RIO_STAND, 'neutral', []),
    'MG_29': ('Mc', MU + 'arms_down', 'smug', []),
    'RF_18': ('Ic', IU + 'folded_arms', 'side_eye', []),
    'MG_30': ('!Mx', MU + 'arms_down', 'angry_rant', []),
    'RK_13': ('Rc', RB + 'arms_crossed', 'dry_humour', []),
    'MG_31': ('M', MU + 'arms_down', 'sad', [('apparently', 'Mc')]),
    'RF_19': ('Ic', IU + 'folded_arms', 'side_eye', []),
    'MG_32': ('Mc', MU + 'pointing', 'angry_rant', []),
    'RF_20': ('Ix', IU + 'folded_arms', 'side_eye', []),
    'MG_33': ('M', MU + 'crossed_arms', 'angry_rant', []),
    'WR_10': ('N', NU + 'seated', 'confused', []),
    'RK_14': ('R', RB + 'arms_crossed', 'neutral', []),
    'RF_21': ('RR', IU + 'folded_arms', 'neutral', []),
    'MG_34': ('!Mx', MU + 'desk_rant', 'shouting', []),
}

# a silent reaction shot held after a line: line id -> (shot, who, face, hold)
REACT = {
    'MG_04': ('Nc', 'rooney', 'confused', 0.7),          # "...a bloke called Darren in a high vis jacket."
    'RK_02': ('2', 'mark', 'confused', 1.0),             # "Depends on Darren."
    'RK_07': ('Mc', 'mark', 'sad', 0.6),                 # "I would."
    'RK_09': ('Mc', 'mark', 'shocked', 1.6),             # "They'll see him again." - the silence
    'RK_10': ('Mc', 'mark', 'facepalm', 0.9),            # "No."
    'RF_03': ('2', 'mark', 'confused', 0.6),             # "I wasn't booked."
    'RK_12': ('Mc', 'mark', 'shocked', 0.5),             # "You're very defensive."
    'MG_29': ('Ic', 'rio', 'neutral', 0.45),             # Mark thinks he has won
    'RF_18': ('Mc', 'mark', 'shocked', 1.75),            # "Just not about football." - VAR, sad trombone
    'RK_14': ('Nc', 'rooney', 'embarrassed', 0.5),       # "Still trying to get Ronaldo out the wedding."
}
# a deadpan beat before a line: the cut to the speaker comes first, the line after the pause
BEAT = {
    'MG_03': 0.25, 'RK_01': 0.3, 'WR_02': 0.45, 'RK_02': 0.6, 'RK_04': 0.3, 'RK_06': 0.35, 'RK_07': 0.35, 'MG_10': 0.4,
    'RK_08': 0.3, 'RK_09': 0.5, 'RK_10': 0.6, 'WR_07': 0.45, 'MG_14': 0.3, 'WR_08': 0.25, 'MG_15': 0.35, 'RK_11': 0.3,
    'RF_07': 0.35, 'RF_11': 0.25, 'RK_12': 0.3, 'RF_15': 0.5, 'WR_09': 0.35, 'RF_16': 0.6, 'RF_18': 0.3, 'MG_30': 0.1,
    'RK_13': 0.35, 'RF_20': 0.3, 'WR_10': 0.5, 'RK_14': 0.3,
}
# a slow push in over a line's opening shot (the fraction the frame narrows by)
PUSH = {
    'RK_01': 0.06, 'RK_02': 0.08, 'RK_05': 0.06, 'MG_09': 0.05, 'RK_09': 0.08, 'MG_13': 0.07, 'RF_05': 0.07,
    'RF_07': 0.12, 'RF_13': 0.05, 'RF_14': 0.06, 'RF_15': 0.10, 'WR_09': 0.08, 'RF_16': 0.10, 'MG_31': 0.10,
    'WR_10': 0.08, 'RK_14': 0.06, 'RF_21': 0.06,
}
REACT_PUSH = 0.08
# crash zooms ('!' shot codes) come in from the same subject's wider framing
CRASH_FROM = {'Mx': 'Mc', 'Rx': 'R', 'Ix': 'Ic', 'Nc': 'N'}
# shouts: a camera shake and comic speed lines at the word (line id -> words)
SHOUTS = {'MG_08': ['defcon'], 'MG_12': ['leaving'], 'MG_21': ['god'], 'MG_22': ['not', 'forest'], 'MG_26': ['wayne'],
          'MG_30': ['piss'], 'MG_32': ['rio'], 'MG_34': ['goodnight']}
SPEED = {'MG_21', 'MG_26', 'MG_34', 'MG_08'}
# the running score (Rio v Mark): line id -> (when, (rio, mark), sound); when = 'end' or a word
SCORE = {
    'RF_12': ('end', (2, 0), 'whistle'),
    'MG_29': ('thank', (2, 1), 'ding'),
    'RF_20': ('end', (3, 0), 'whistle'),
}
CASE = ['CHAMPIONS LEAGUES', "BALLON D'ORS", 'RECORDS', 'GOALS', 'STANDARDS']
CASE_WORDS = ['champions', 'ballon', 'records', 'goals', 'standards']
GAP = 0.2                                   # the next line comes straight in
GAP_FAST = 0.12                             # the ending, and the interruptions
FAST = {'MG_18', 'RF_08', 'MG_19', 'RF_09', 'MG_20', 'MG_28', 'RF_17', 'MG_29', 'RF_18', 'MG_30', 'RK_13', 'MG_31',
        'RF_19', 'MG_32', 'RF_20', 'MG_33', 'WR_10', 'RK_14', 'RF_21'}
REACT_HOLD = 0.9

# name straps (lower thirds): line id -> (name, caption); shown as the line starts
STRAPS = {
    'MG_01': ('MARK GOLDBRIDGE', 'THE OVERCRAP DAILY'),
    'WR_01': ('WAYNE ROONEY', 'ASKING THE IMPORTANT QUESTIONS'),
    'RK_01': ('ROY KEANE', 'HAS NOT MOVED SINCE 1993'),
    'RF_02': ('RIO FERDINAND', 'NOT BOOKED'),
    'RF_04': ('RIO FERDINAND', 'STILL NOT BOOKED'),
    'MG_24': ('MARK GOLDBRIDGE', 'NOT A FOREST FAN (HE SAYS)'),
    'RF_16': ('BREAKING', 'MOON: POSSIBLY IBERICO'),
}


def word_time(ln, word, nth=1):
    k = 0
    for w in ln['words']:
        if w['word'].split('(')[0] == word.lower():
            k += 1
            if k == nth:
                return ln['start'] + w['t0']
    return None


def perform(tl, ln):
    """The delivery on top of the lip sync: a small nod on each emphasised word,
    eyes closed through a [sigh], and a blink in each pause."""
    who, lid, t_line = ln['who'], ln['id'], ln['start']
    words = ln['words']
    caps = S.emphasised(lid)
    for w in words:
        name = w['word'].split('(')[0]
        if name in caps:
            caps.remove(name)
            t0, t1 = t_line + w['t0'], t_line + w['t1']
            tl.key(t0 - 0.1, who, nod=0.0)
            tl.key(t0 + 0.08, who, nod=1.0, e='ease')
            tl.key(max(t1, t0 + 0.2) + 0.12, who, nod=0.0, e='ease')
    if S.tag(lid) == 'sigh' and words and words[0]['t0'] > 0.15:
        a, b = t_line + 0.02, t_line + words[0]['t0'] - 0.04
        tl.key(a, who, eyes_shut=True)
        tl.key(b, who, eyes_shut=False)
    for w0, w1 in zip(words, words[1:]):
        if w1['t0'] - w0['t1'] > 0.3:
            tl.blinks.setdefault(who, []).append(t_line + (w0['t1'] + w1['t0']) / 2 - 0.05)


def face_key(f):
    return f if '/' in f else 'expressions/' + f


def build():
    E.load_alignment()
    tl = E.Timeline(S)
    key, shot = tl.key, tl.shot

    def cut(t, code, **kw):
        bg, rect, extra = SHOTS[code]
        shot(t, bg, rect, **dict(extra, **kw))

    def crash(t, code):
        """A crash zoom: in from the subject's wider framing in a few frames, with a hit."""
        cut(t, code, crash_from=SHOTS[CRASH_FROM[code]][1], crash=0.13)
        tl.sfx(t, 'impact', 0.55)
        tl.shakes.append((t + 0.1, 7.0, 0.35))

    def look(t, who, face):
        key(t, who, face=face_key(face))

    def gfx(t, **kv):
        key(t, 'gfx', **kv)

    def score(t, sc, sound):
        gfx(t, score=sc, score_t=t)
        tl.sfx(t, sound, 0.7 if sound == 'whistle' else 0.8)

    # everyone's starting state: Mark and Rooney at the desk, Roy standing, Rio not here
    key(0, 'mark', loc='seat', body='upper/both_hands_out', face='expressions/smug', flip=False)
    key(0, 'rooney', loc='seat', body='upper/seated', face='expressions/neutral', flip=True)
    key(0, 'roy', loc='stand', path=('roy_stand', 'roy_stand'), body='body/arms_crossed', face='expressions/neutral',
        flip=False)
    key(0, 'rio', loc='off', body=RIO_STAND, face='expressions/neutral', flip=False)
    gfx(0, score=None)
    tl.wait(0.15)

    last_code = None
    rio_stops = 0.0
    for item in S.ORDER:
        if item == '@rio_enters':
            # the episode's biggest change: a record scratch, the door, the shot goes wide and Rio
            # strides in already talking
            t = tl.wait(0.3)
            cut(t, 'SWf', push=0.07, focus=(0.18, 0.55))
            tl.sfx(t, 'record_scratch', 0.9)
            tl.sfx(t + 0.1, 'door_open', 1.2)
            look(t + 0.12, 'mark', 'shocked')
            key(t + 0.12, 'mark', body='upper/arms_down')
            look(t + 0.2, 'rooney', 'shocked')
            key(t + 0.15, 'rio', loc='walk', path=('rio_door', 'rio_stand'), u=0.0, flip=False,
                cycle=['body/walk_1', 'body/walk_2', 'body/walk_3', 'body/walk_2'])
            key(t + 2.05, 'rio', u=1.0, e='linear')
            key(t + 2.05, 'rio', loc='stand', path=('rio_stand', 'rio_stand'), body=RIO_STAND, flip=False)
            look(t + 2.05, 'rio', 'neutral')
            rio_stops = t + 2.05
            tl.wait(0.45)                           # "Whoa, whoa, whoa" comes in as he crosses the floor
            last_code = 'SWf'
            continue
        if item == '@forest_beat':
            # "...You're a Forest fan anyway." - dun... dun... DUNNN on Mark's face, then he goes
            t = tl.wait(0.05)
            cut(t, 'Mc', push=0.06)
            key(t, 'mark', body='upper/arms_down')
            look(t, 'mark', 'shocked')
            tl.sfx(t, 'dun_dun', 0.75)
            tl.wait(0.95)
            last_code = 'Mc'
            continue
        if item == '@rooney_laughs':
            t = tl.wait(0.05)
            cut(t, 'Nc', push=0.05)
            look(t, 'rooney', 'laughing')
            for j in range(8):                       # shoulders going
                key(t + j * 0.16, 'rooney', nod=0.0)
                key(t + j * 0.16 + 0.08, 'rooney', nod=1.8, e='ease')
            key(t + 8 * 0.16, 'rooney', nod=0.0, e='ease')
            score(t + 0.25, (1, 0), 'whistle')
            tl.wait(1.35)
            look(tl.t, 'rooney', 'happy')
            last_code = 'Nc'
            continue
        if item == '@rooney_satisfied':
            t = tl.wait(0.1)
            cut(t, 'Nc', push=0.04)
            look(t, 'rooney', 'happy')
            key(t + 0.15, 'rooney', nod=0.0)
            key(t + 0.35, 'rooney', nod=1.2, e='ease')
            key(t + 0.6, 'rooney', nod=0.0, e='ease')
            tl.wait(0.95)
            last_code = 'Nc'
            continue
        if item == '@end':
            # hard cut straight after GOODNIGHT: no outro
            t = tl.wait(0.0)
            key(t, 'world', fade=1.0)
            tl.wait(0.8)
            continue

        # ------------------------------------------ a line of dialogue
        lid = item
        code, body, face, changes = STAGE[lid]
        who = S.SPEAKER[lid[:2]]
        gap = GAP_FAST if lid in FAST else GAP
        lead = BEAT.get(lid, 0.0)
        if lid == 'MG_14':                        # Mark only gets in once Rio has stopped
            tl.t = max(tl.t, rio_stops - lead - 0.1)
        ln = tl.say(lid, gap=gap, lead=lead)
        perform(tl, ln)
        t0 = ln['start']
        tc = t0 - lead                    # the cut (and the pose) land before the beat
        key(tc, who, body=body)
        if face:
            look(tc, who, face)
        if code.startswith('!'):
            crash(tc, code[1:])
            last_code = code[1:]
        elif code != last_code or lid in PUSH:
            cut(tc, code, push=PUSH.get(lid))
            last_code = code
        for word, ch in changes:
            tw = word_time(ln, word)
            if tw is None:
                print('  (no word %r in %s)' % (word, lid))
                continue
            if ch.startswith('body='):
                key(tw, who, body=MU + ch[5:] if '/' not in ch[5:] else ch[5:])
            elif ch.startswith('face='):
                look(tw, who, ch[5:])
            elif ch.startswith('!'):
                crash(tw - 0.04, ch[1:])
                last_code = ch[1:]
            else:
                cut(tw, ch)
                last_code = ch
        for w in SHOUTS.get(lid, []):
            tw = word_time(ln, w)
            if tw is not None:
                tl.shakes.append((tw, 5.0, 0.45))
                if lid in SPEED:
                    gfx(tw - 0.03, speed=tw - 0.03)
                    gfx(tw + 0.75, speed=None)
        if lid in STRAPS:
            ts = tc + 0.15
            hold = max(1.8, min(3.4, ln['start'] + ln['dur'] + 0.5 - ts))
            key(ts, 'gfx', strap=STRAPS[lid], strap_t=ts, strap_hold=hold)
            key(ts + hold, 'gfx', strap=None)
            tl.sfx(ts, 'strap', 0.6)
        if lid == 'MG_08':                         # DEFCON ONE
            tw = word_time(ln, 'defcon')
            key(tw, 'gfx', alert='DEFCON 1', alert_t=tw)
            key(tw + 2.0, 'gfx', alert=None)
            tl.sfx(tw, 'alarm', 0.8)
        if lid == 'MG_16':                         # the Ronaldo alarm
            tw = word_time(ln, 'alarm')
            key(tw, 'gfx', alert='RONALDO ALARM', alert_t=tw)
            key(tw + 1.6, 'gfx', alert=None)
            tl.sfx(tw, 'alarm', 0.6)
        if lid == 'RF_13':                         # the case for Cristiano, ticked off as he lists it
            for k, w in enumerate(CASE_WORDS):
                tw = word_time(ln, w)
                if tw is not None:
                    gfx(tw, case=k + 1, case_t=tw)
                    tl.sfx(tw, 'ding', 0.45)
        if lid == 'MG_24':
            gfx(tc, case=None)
        if lid == 'RK_09':
            tl.sfx(ln['start'] + ln['dur'] + 0.3, 'crickets', 0.7)
        if lid in SCORE:
            when, sc, sound = SCORE[lid]
            tw = ln['start'] + ln['dur'] + 0.05 if when == 'end' else word_time(ln, when)
            score(tw, sc, sound)
        if lid in REACT:
            rc, rwho, rface, hold = REACT[lid]
            t = tl.wait(0.0)
            cut(t, rc, push=REACT_PUSH)
            last_code = rc
            if rwho:
                look(t, rwho, rface)
            if lid == 'RF_18':                     # VAR rules Mark's point out
                gfx(t + 0.05, var='VAR CHECK', var_t=t + 0.05)
                gfx(t + 0.55, var='NO GOAL', var_t=t + 0.55, score=(2, 0), score_t=t + 0.55)
                gfx(t + hold + 0.1, var=None)
                tl.sfx(t + 0.55, 'sad_trombone', 0.75, cut=hold + 0.05 - 0.55 + 0.25)
            tl.wait(hold)
    return tl


# ------------------------------------------------------------------ on-screen graphics
_GFX = {}


def _font(name):
    import skia
    if name not in _GFX:
        _GFX[name] = skia.Typeface.MakeFromFile(os.path.join(HERE, '..', 'fonts', name))
    return _GFX[name]


def _rgba_layer(w, h, draw):
    sys.path.insert(0, os.path.join(HERE, '..', 'tools', 'vec'))
    import draw as D
    surf, c = D.surface(w, h)
    draw(D.Pen(c), D)
    return D.to_rgba(surf)


def _blend(frame, rgba, x, y, alpha=1.0):
    import numpy as np
    h, w = rgba.shape[:2]
    H, W = frame.shape[:2]
    xa, ya, xb, yb = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if xa >= xb or ya >= yb:
        return
    s = rgba[ya - y:yb - y, xa - x:xb - x]
    a = s[..., 3:4].astype(np.float32) / 255 * alpha
    d = frame[ya:yb, xa:xb]
    frame[ya:yb, xa:xb] = (s[..., 2::-1] * a + d * (1 - a)).astype(np.uint8)


def _bug():
    """The channel bug, top left: THE OVERCRAP DAILY with a red LIVE dot."""
    if 'bug' not in _GFX:
        def draw(pen, D):
            pen.rect(0, 0, 760, 120, (14, 12, 16), r=22, alpha=200)
            pen.rect(0, 0, 150, 120, (205, 22, 34), r=22)
            pen.rect(110, 0, 150, 120, (205, 22, 34))
            pen.text('LIVE', 75, 78, 44, (255, 255, 255), font=_font('Poppins-Bold.ttf'))
            pen.text('THE OVERCRAP DAILY', 182, 80, 50, (245, 245, 245), font=_font('Poppins-BoldItalic.ttf'), align='left')
        _GFX['bug'] = _rgba_layer(760, 120, draw)
    return _GFX['bug']


def _strap(name, caption):
    k = ('strap', name, caption)
    if k not in _GFX:
        def draw(pen, D):
            pen.rect(0, 0, 1700, 170, (205, 22, 34), r=14)
            pen.rect(0, 170, 1700, 260, (245, 245, 242), r=14)
            pen.rect(0, 150, 1700, 190, (245, 245, 242))
            pen.text(name, 48, 125, 104, (255, 255, 255), font=_font('Poppins-Bold.ttf'), align='left')
            pen.text(caption, 50, 236, 58, (20, 18, 22), font=_font('Poppins-BoldItalic.ttf'), align='left')
        _GFX[k] = _rgba_layer(1700, 260, draw)
    return _GFX[k]


def _alert(text):
    k = ('alert', text)
    if k not in _GFX:
        W = 3840

        def draw(pen, D):
            pen.rect(0, 0, W, 330, (180, 10, 20), alpha=235)
            pen.rect(0, 0, W, 26, (255, 205, 0))
            pen.rect(0, 304, W, 330, (255, 205, 0))
            pen.text('!  ' + text + '  !', W / 2, 228, 190, (255, 255, 255), font=_font('Poppins-Bold.ttf'))
        _GFX[k] = _rgba_layer(W, 330, draw)
    return _GFX[k]


def _scorebug(rio, mark, hi=None):
    """Top-right score bug: RIO n - n MARK. hi: the side that just scored (highlighted)."""
    k = ('score', rio, mark, hi)
    if k not in _GFX:
        def draw(pen, D):
            pen.rect(0, 0, 1040, 132, (14, 12, 16), r=20, alpha=225)
            pen.rect(0, 0, 330, 132, (30, 30, 34), r=20)
            pen.rect(300, 0, 330, 132, (30, 30, 34))
            pen.rect(710, 0, 1040, 132, (205, 22, 34), r=20)
            pen.rect(710, 0, 740, 132, (205, 22, 34))
            f = _font('Poppins-Bold.ttf')
            pen.text('RIO', 165, 92, 70, (245, 245, 245), font=f)
            pen.text('MARK', 875, 92, 70, (255, 255, 255), font=f)
            for x, v, side in ((420, rio, 'rio'), (620, mark, 'mark')):
                if hi == side:
                    pen.rect(x - 62, 14, x + 62, 118, (255, 205, 0), r=12)
                pen.text(str(v), x, 98, 92, (20, 18, 22) if hi == side else (255, 255, 255), font=f)
            pen.text('-', 520, 92, 70, (200, 200, 200), font=f)
        _GFX[k] = _rgba_layer(1040, 132, draw)
    return _GFX[k]


def _banner(text, bg, fg=(255, 255, 255), edge=(255, 205, 0)):
    k = ('banner', text, bg)
    if k not in _GFX:
        W = 3840

        def draw(pen, D):
            pen.rect(0, 0, W, 300, bg, alpha=235)
            pen.rect(0, 0, W, 22, edge)
            pen.rect(0, 278, W, 300, edge)
            pen.text(text, W / 2, 210, 180, fg, font=_font('Poppins-Bold.ttf'))
        _GFX[k] = _rgba_layer(W, 300, draw)
    return _GFX[k]


def _case(n):
    """The case for Cristiano: a sports-TV list panel with the first n items ticked."""
    k = ('case', n)
    if k not in _GFX:
        def draw(pen, D):
            pen.rect(0, 0, 1180, 170, (205, 22, 34), r=18)
            pen.rect(0, 150, 1180, 170, (205, 22, 34))
            pen.text('THE CASE FOR CRISTIANO', 50, 112, 74, (255, 255, 255), font=_font('Poppins-Bold.ttf'),
                     align='left')
            for i in range(n):
                y = 170 + i * 150
                pen.rect(0, y, 1180, y + 150, (16, 14, 18) if i % 2 == 0 else (26, 24, 30), alpha=235)
                pen.text(CASE[i], 60, y + 100, 72, (245, 245, 245), font=_font('Poppins-BoldItalic.ttf'), align='left')
                pen.ellipse(1080, y + 75, 46, 46, (40, 170, 70))
                pen.line([(1056, y + 77), (1074, y + 97), (1106, y + 55)], (255, 255, 255), 14)
        _GFX[k] = _rgba_layer(1180, 170 + 150 * max(n, 0), draw)
    return _GFX[k]


def _speed_lines(W, H, seed):
    """Comic speed lines rushing in from the frame edges (redrawn every frame so they flicker)."""
    import numpy as np
    rng = np.random.RandomState(seed)

    def draw(pen, D):
        import skia
        cx, cy = W / 2, H * 0.45
        R = math.hypot(W, H) * 0.6
        for _ in range(70):
            a = rng.uniform(0, 2 * math.pi)
            inner = R * rng.uniform(0.42, 0.62)
            wid = rng.uniform(0.004, 0.012)
            p = skia.Path()
            p.moveTo(cx + math.cos(a) * inner, cy + math.sin(a) * inner)
            p.lineTo(cx + math.cos(a - wid) * R, cy + math.sin(a - wid) * R)
            p.lineTo(cx + math.cos(a + wid) * R, cy + math.sin(a + wid) * R)
            p.close()
            pen.fill(p, (255, 255, 255), alpha=int(rng.uniform(120, 210)))
    return _rgba_layer(W, H, draw)


def overlays(R, t, frame):
    import numpy as np
    tl = R.tl
    W, H = frame.shape[1], frame.shape[0]
    sc = W / 3840.0
    if (tl.get('world', 'fade', t, 0.0) or 0.0) > 0.99:
        return frame
    # alert: the frame pulses red, a banner flashes across the middle
    alert = tl.get('gfx', 'alert', t)
    if alert:
        u = t - tl.get('gfx', 'alert_t', t, t)
        pulse = 0.5 + 0.5 * np.cos(u * 2 * np.pi * 2.4)
        red = np.zeros_like(frame)
        red[..., 2] = 255
        a = 0.28 * pulse
        frame[:] = (frame * (1 - a) + red * a).astype(np.uint8)
        if pulse > 0.25 or u < 0.2:
            ban = _alert(alert)
            if sc != 1:
                import cv2
                ban = cv2.resize(ban, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
            _blend(frame, ban, 0, int(H * 0.80 - ban.shape[0] / 2))
    # speed lines on Mark's explosions
    sp = tl.get('gfx', 'speed', t)
    if sp is not None and t - sp < 0.75:
        k = 1.0 - max(0.0, (t - sp - 0.45) / 0.3)
        _blend(frame, _speed_lines(W, H, int(t * 24)), 0, 0, 0.85 * k)
    # VAR
    var = tl.get('gfx', 'var', t)
    if var:
        u = t - tl.get('gfx', 'var_t', t, t)
        txt = var + '.' * (int(u * 6) % 4) if var == 'VAR CHECK' else var
        ban = _banner(txt, (60, 30, 110) if var == 'VAR CHECK' else (180, 10, 20))
        if sc != 1:
            import cv2
            ban = cv2.resize(ban, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
        _blend(frame, ban, 0, int(H * 0.80 - ban.shape[0] / 2), min(1.0, u / 0.08))
    # the case for Cristiano
    n = tl.get('gfx', 'case', t)
    if n:
        u = t - tl.get('gfx', 'case_t', t, t)
        img = _case(n)
        if sc != 1:
            import cv2
            img = cv2.resize(img, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
        _blend(frame, img, int(110 * sc), int(330 * sc))
    # the running score
    scr = tl.get('gfx', 'score', t)
    if scr:
        u = t - tl.get('gfx', 'score_t', t, t)
        prev = tl.get('gfx', 'score', tl.get('gfx', 'score_t', t, t) - 0.01)
        hi = None
        if u < 1.6 and prev != scr:
            hi = 'rio' if (not prev or scr[0] > prev[0]) else ('mark' if scr[1] > prev[1] else None)
        img = _scorebug(scr[0], scr[1], hi)
        pop = 1.0 + 0.18 * max(0.0, 1 - u / 0.25) if u < 0.25 else 1.0
        import cv2
        img = cv2.resize(img, None, fx=sc * pop, fy=sc * pop, interpolation=cv2.INTER_AREA if sc * pop < 1 else cv2.INTER_CUBIC)
        _blend(frame, img, int(W - 90 * sc - img.shape[1]), int(80 * sc), min(1.0, u / 0.15) if not prev else 1.0)
    # the channel bug
    bug = _bug()
    if sc != 1:
        import cv2
        bug = cv2.resize(bug, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
    _blend(frame, bug, int(90 * sc), int(80 * sc), 0.92)
    # the name strap slides in from the left, holds, fades
    strap = tl.get('gfx', 'strap', t)
    if strap:
        u = t - tl.get('gfx', 'strap_t', t, t)
        img = _strap(*strap)
        if sc != 1:
            import cv2
            img = cv2.resize(img, None, fx=sc, fy=sc, interpolation=cv2.INTER_AREA)
        k = min(1.0, u / 0.35)
        k = 1 - (1 - k) ** 3
        x = int(-img.shape[1] + (img.shape[1] + 150 * sc) * k)
        fade = min(1.0, max(0.0, (tl.get('gfx', 'strap_hold', t, 3.4) - u) / 0.3))
        _blend(frame, img, x, int(H - 200 * sc - img.shape[0]), fade)
    return frame


E.OVERLAYS.append(overlays)

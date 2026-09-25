"""Where every part lives on the two character sheets (1x sheet coords), measured from the sheets."""
S = 4   # the sheets are used 4x upscaled

TURN = {  # full-body turnaround: box
    "FRONT": (4, 48, 147, 440), "3/4 LEFT": (155, 48, 280, 440), "LEFT": (287, 48, 394, 440),
    "BACK": (399, 48, 550, 440), "RIGHT": (558, 48, 664, 440), "3/4 RIGHT": (674, 48, 810, 440)}

HEADS = {  # head expressions: centre x, row
    "NEUTRAL": (890, 0), "HAPPY": (1006, 0), "SMILE": (1122, 0), "ANGRY": (1236, 0), "SHOUT": (1352, 0), "SAD": (1478, 0),
    "WORRIED": (890, 1), "SURPRISED": (1009, 1), "CONFUSED": (1128, 1), "DISGUSTED": (1243, 1), "THINKING": (1360, 1),
    "RAISED BROW": (1478, 1)}
HEAD_ROWS = [(44, 196), (212, 368)]

ARMS = {  # arm poses (headless torsos): label centre x, row
    "ARMS DOWN": (56, 0), "POINT LEFT": (157, 0), "POINT RIGHT": (262, 0), "REACH FORWARD": (375, 0),
    "PRESENT": (478, 0), "PALM UP": (578, 0), "PALM OUT STOP": (675, 0), "THUMBS UP": (767, 0),
    "THUMBS DOWN": (880, 0), "FIST": (978, 0), "FIST PUMP": (1080, 0), "PHONE HOLD": (1186, 0),
    "ADJUST TIE": (1282, 0), "HAND ON CHIN": (1385, 0), "ARMS CROSSED": (1478, 0),
    "WAVE": (54, 1), "TALK LEFT": (148, 1), "TALK RIGHT": (246, 1), "BOTH HANDS OUT": (345, 1),
    "EXPLAINING 1": (445, 1), "EXPLAINING 2": (553, 1), "FRUSTRATED": (661, 1), "WHAT": (755, 1),
    "CALM DOWN": (876, 1), "HOLDING PAPER": (978, 1), "HOLDING CUP": (1070, 1), "OPEN ARMS": (1190, 1),
    "FINGER UP": (1298, 1), "OK SIGN": (1387, 1), "HAND ON HIP": (1482, 1)}
ARM_ROWS = [(476, 586), (597, 701)]
ARM_TOP_UNDER_HEADER = 495     # the red "ARM POSES" header sits over the first two poses

HANDS = {  # separate hands: box x range
    "OPEN": (14, 106), "FIST": (110, 192), "POINT": (199, 284), "THUMBS UP": (298, 366), "THUMBS DOWN": (387, 457),
    "PALM UP": (478, 576), "PALM OUT": (587, 657), "OK SIGN": (679, 741), "PINCH": (756, 825), "GRAB": (833, 905),
    "HOLD CUP": (921, 1001), "HOLD PAPER": (1020, 1115), "PHONE HAND": (1131, 1214), "HAND ON CHIN": (1229, 1313),
    "FINGER UP": (1333, 1396)}
HAND_ROW = (742, 825)

LEGS = {  # leg poses: box x range
    "STANDING": (10, 90), "WALK 1": (95, 187), "WALK 2": (178, 252), "WALK 3": (256, 344), "WALK 4": (343, 442),
    "STEP FORWARD": (431, 537), "STEP BACK": (535, 607), "TURN LEFT": (616, 680), "TURN RIGHT": (684, 773),
    "RUN 1": (788, 890), "RUN 2": (889, 982), "RUN 3": (980, 1070), "KICK": (1068, 1196), "SIT 1": (1190, 1276),
    "SIT 2": (1277, 1354), "CROUCH": (1368, 1448), "KNEEL": (1442, 1526)}
LEG_ROW = (862, 990)

# mouth sheet: 19 front heads (all the same stern face, one mouth shape each)
MOUTH_ROW1 = ["REST", "A", "E", "I", "O", "U", "FV", "L", "M", "B"]
MOUTH_ROW2 = ["CDGK", "CHJ", "R", "TH", "W", "SZ", "T", "N", "Q"]
MOUTH_CX = {**{n: 100 + 175.2 * i for i, n in enumerate(MOUTH_ROW1)},
            **{n: 120 + 191.0 * i for i, n in enumerate(MOUTH_ROW2)}}
MOUTH_CY = {**{n: 190 for n in MOUTH_ROW1}, **{n: 510 for n in MOUTH_ROW2}}
MOUTH_BOX = (54, 203, 146, 266)     # the swapped area in the REST head's frame (1x)

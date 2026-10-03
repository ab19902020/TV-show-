"""Every drawing used in the film, rigged: which character it is, where the waist is (the upper body leans and breathes
about it), the closed mouth line (only for the drawings that lip-sync a quoted line), and the limbs that move on their own.
All coordinates are 1x sheet px (see tools/partgrid.py and tools/zoom.py). The head layer is found from the eyes.

Size: `ref` makes every drawing of a character the same size on screen. A drawing is placed with a scale in
"plate px per sheet px of that character's model-sheet front view"; the eye spacing of each drawing converts it."""
from functools import lru_cache
from engine import Actor

# eye spacing on the model-sheet front views; Ronaldo's is 3% smaller so that, standing side by side at the same scale,
# he is ~7% taller than Evra (1.87 m against 1.75 m)
REF = {'evra': 48.0, 'ronaldo': 40.2, 'rio': 24.0}
# Rio's sheet draws his poses at different scales, so his drawings are sized by height instead: standing, as tall as
# Ronaldo (1.89 m against 1.87 m)
RIO_H = 675.

CAST = {
    # ---- Evra
    'e_front': dict(who='evra', waist=590),
    'e_34': dict(who='evra', waist=590),
    'e_casual': dict(who='evra', waist=1290, numbers=[(128, 1169, 148, 1197)], mouth=(165.5, 1058.8, 228.8, 1051.3, 197.5, 1063.8), chin=1101),
    'e_swim': dict(who='evra', waist=1290),
    'e_robe': dict(who='evra', band=(.04, .25), waist=1300),
    'e_tired': dict(who='evra', waist=385, numbers=[(229, 306, 250, 327)]),
    'e_optimism': dict(who='evra', waist=398, numbers=[(678, 298, 694, 322)], limbs={'hands': ([(700, 266), (788, 258), (803, 350), (772, 378), (703, 370)], (737, 352))}),
    # eating: the arm and fork stay in the drawing (moving the arm left a smear by the face); the drawn food is taken
    # off the fork (the film draws the bites), the fork stays on the body when the head moves, and the mouth chews
    'e_tinylunch': dict(who='evra', waist=935, mouth=(226, 792, 283, 786, 252, 793), chin=828,
                        erase=[[(350, 812), (354, 800), (366, 795), (380, 797), (390, 806), (386, 820), (374, 823), (360, 822)]],
                        nohead=[[(342, 790), (420, 790), (420, 930), (342, 930)]]),
    'e_kick': dict(who='evra', numbers=[(630, 841, 650, 865)], fill='inpaint', limbs={'leg': ([(698, 888), (758, 896), (828, 926), (908, 906), (915, 941), (868, 1008),
                                               (828, 983), (758, 963), (713, 958), (693, 931)], (702, 915))}),
    'e_pool': dict(who='evra'),
    'e_sauna': dict(who='evra', waist=1500, mouth=(745, 1308.8, 792.5, 1301.3, 770, 1307.5), chin=1341),
    'eb_neutral': dict(who='evra', mouth=(161.7, 310, 248.3, 293.3, 205, 313.3), chin=366.7),
    'eb_optimistic': dict(who='evra'), 'eb_suspicious': dict(who='evra'),
    'eb_disappointed': dict(who='evra', mouth=(198.3, 725, 255, 710, 226.7, 703.3), chin=760),
    'eb_exhausted': dict(who='evra'), 'eb_laugh': dict(who='evra', face=False),
    # ---- Ronaldo
    'r_front': dict(who='ronaldo', waist=520), 'r_casual': dict(who='ronaldo', waist=1350),
    'r_back': dict(who='ronaldo', face=False, waist=520),
    'r_swim': dict(who='ronaldo', mouth=(475, 1098.3, 520.8, 1097.5, 500, 1104.2), chin=1126.7),
    'r_robe': dict(who='ronaldo', band=(.04, .22), waist=1335),
    'r_stance': dict(who='ronaldo', waist=430, numbers=[(255, 341, 279, 369), (313, 451, 336, 479)]),
    'r_invite': dict(who='ronaldo', waist=420, mouth=(738.3, 225, 775, 234.2, 758.3, 235.8), chin=258.3,
                     limbs={'hand': ([(594, 262), (640, 248), (670, 278), (680, 318), (670, 348), (640, 354), (606, 336)], (662, 330))}),
    'r_lunch': dict(who='ronaldo', waist=960, mouth=(276, 797, 322, 797, 298, 804), chin=838,
                    erase=[[(322, 812), (328, 802), (342, 798), (350, 803), (348, 815), (338, 826), (326, 826)]],
                    nohead=[[(337, 790), (345, 800), (334, 828), (326, 842), (330, 920), (420, 920), (420, 790)]]),
    'r_kick': dict(who='ronaldo', fill='inpaint', limbs={'leg': ([(709, 936), (764, 931), (804, 991), (824, 1036), (899, 1051), (894, 1091), (844, 1121),
                                                 (799, 1091), (759, 1041), (719, 1001)], (735, 945))}),
    'r_laps': dict(who='ronaldo'), 'r_exercise': dict(who='ronaldo', waist=1470),
    'rb_neutral': dict(who='ronaldo'), 'rb_smug': dict(who='ronaldo', mouth=(177.1, 825.7, 255.7, 824.3, 220, 836.6), chin=881.4),
    'rb_intense': dict(who='ronaldo'), 'rb_confused': dict(who='ronaldo'), 'rb_eager': dict(who='ronaldo'), 'rb_invite': dict(who='ronaldo'),
    # ---- Rio
    'rio_hero': dict(who='rio', waist=540, height1=RIO_H),
    # table tennis: Rio's microphone pose with the mic painted out and a bat in his fist (the forearm swings at the elbow);
    # Ronaldo's ready stance with a bat in his reaching hand (the arm swings at the shoulder). bat = (grip x, y, direction
    # x, y, blade radius, handle length) in sheet px of the drawing
    'rio_bat': dict(who='rio', waist=205, height1=RIO_H,
                    inpaint=[[(138, 127), (158, 129), (159, 152), (151, 156), (140, 152)], [(119, 176), (133, 176), (133, 190), (119, 190)]],
                    limbs={'bat': ([(80, 150), (98, 156), (110, 153), (124, 149), (140, 148), (153, 149), (156, 158), (152, 174),
                                    (136, 181), (120, 184), (100, 192), (80, 194)], (86, 172))},
                    nohead=[[(100, 120), (170, 120), (170, 200), (100, 200)]], bat=(131, 164, .58, -.81, 21, 26)),
    'rio_laughbig': dict(who='rio', face=False, height1=RIO_H * .787),        # bent double
    # Ronaldo at the table: his side profile drawn mirrored (facing left, at the table), the near arm raised with a bat
    'r_bat': dict(who='ronaldo', part='r_side', waist=560,
                  limbs={'arm': ([(526, 394), (545, 383), (565, 382), (583, 392), (590, 420), (590, 460), (593, 500), (599, 540),
                                  (605, 565), (605, 596), (596, 607), (575, 608), (558, 601), (555, 570), (547, 535), (537, 505),
                                  (529, 470), (523, 440), (522, 410)], (556, 405))},
                  bat=(581, 585, .6, .8, 36, 26)),
    'r_tt': dict(who='ronaldo', part='r_stance', waist=430,
                 limbs={'arm': ([(160, 262), (146, 272), (128, 292), (110, 318), (95, 340), (64, 355), (44, 372), (44, 408),
                                 (62, 412), (78, 398), (90, 398), (104, 410), (106, 380), (104, 362), (120, 348), (140, 334),
                                 (166, 326)], (156, 294))},
                 bat=(78, 380, -.86, .5, 25, 18)), 'rio_front': dict(who='rio', waist=330), 'rio_back': dict(who='rio', face=False),
    'rio_warning': dict(who='rio'), 'rio_shrug': dict(who='rio'), 'rio_laugh': dict(who='rio', face=False), 'rio_folded': dict(who='rio'),
}


@lru_cache(None)
def actor(name, mirror=False):
    """the rigged drawing; mirror=True gives the copy whose shirt numbers are pre-flipped for drawing mirrored.
    An entry may rig a drawing a second way under its own name ('part' names the drawing)."""
    c = dict(CAST[name]); who = c.pop('who'); pname = c.pop('part', name)
    c.pop('bat', None)
    if not mirror: c.pop('numbers', None)
    return Actor(pname, who, ref_span=REF[who], mirrored=mirror and 'numbers' in CAST[name], **c)

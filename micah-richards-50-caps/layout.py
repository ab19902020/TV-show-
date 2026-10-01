"""Where every drawing sits on every character sheet (sheet px, 1122 x 1402).

A STRIP is one row of drawings: (sheet, y0, y1, [(name, centre x, centre y), ...], options). The cutter floods the paper
away, then splits the row at the narrowest contacts with a watershed seeded at each drawing's centre, so a centre only has
to land inside its drawing. Text labels and neighbouring rows are never reached, so y0 / y1 can be generous.
flat=True: the drawings are cut off flat at the bottom (busts, upper-body poses): a dam is drawn there so a white shirt does
not leak into the paper, and the dam row is removed again.
"""

SHEETS = {
    "wr": "wayne-rooney-sheet", "mr": "micah-richards-sheet-1-suit", "cr": "coleen-rooney-sheet",
    "b1": "rooney-boy-1-sheet", "b2": "rooney-boy-2-sheet", "b3": "rooney-boy-3-sheet", "b4": "rooney-boy-4-sheet",
    "fr": "micahs-friends-sheet", "gy": "gary-lineker-sheet", "m2": "micah-richards-sheet-2-suit", "as": "alan-shearer-sheet",
}

STRIPS = []


def strip(sheet, y0, y1, items, flat=False, tag=""):
    STRIPS.append(dict(sheet=sheet, y0=y0, y1=y1, items=items, flat=flat, tag=tag))


# ------------------------------------------------------------------ Wayne Rooney (wr)
strip("wr", 115, 830, [("wr_hero", 150, 450)], tag="hero")
strip("wr", 140, 455, [("wr_t_front", 365, 300), ("wr_t_q34L", 520, 300), ("wr_t_side", 690, 300), ("wr_t_q34R", 855, 300),
                       ("wr_t_back", 1010, 300)])
strip("wr", 515, 690, [("wr_b_front", 370, 610), ("wr_b_q34L", 535, 610), ("wr_b_side", 690, 610), ("wr_b_q34R", 850, 610),
                       ("wr_b_back", 1015, 610)], flat=True)
strip("wr", 745, 880, [("wr_e_neutral", 337, 810), ("wr_e_happy", 450, 810), ("wr_e_smug", 566, 810), ("wr_e_confused", 680, 810),
                       ("wr_e_laughing", 798, 810), ("wr_e_embarrassed", 924, 810), ("wr_e_shocked", 1044, 810)], flat=True)
strip("wr", 1205, 1360, [("wr_w_neutral", 87, 1290), ("wr_w0", 245, 1290), ("wr_w1", 380, 1290), ("wr_w2", 513, 1290)])

# ------------------------------------------------------------------ Micah Richards, sheet 1 (mr)
strip("mr", 115, 840, [("mr_hero", 150, 450)], tag="hero")
strip("mr", 140, 470, [("mr_t_front", 370, 310), ("mr_t_q34L", 530, 310), ("mr_t_side", 693, 310), ("mr_t_q34R", 855, 310),
                       ("mr_t_back", 1010, 310)])
strip("mr", 525, 710, [("mr_b_front", 368, 625), ("mr_b_q34L", 525, 625), ("mr_b_side", 690, 625), ("mr_b_q34R", 850, 625),
                       ("mr_b_back", 1015, 625)], flat=True)
strip("mr", 760, 895, [("mr_e_neutral", 340, 830), ("mr_e_happy", 445, 830), ("mr_e_laughing", 560, 830), ("mr_e_smug", 665, 830),
                       ("mr_e_confused", 775, 830), ("mr_e_shocked", 885, 830), ("mr_e_embarrassed", 1030, 830)], flat=True)
strip("mr", 1055, 1180, [("mr_p_talking", 572, 1120), ("mr_p_laughhard", 665, 1120), ("mr_p_handsup", 762, 1120),
                         ("mr_p_sofa", 858, 1120), ("mr_p_pointing", 965, 1120), ("mr_p_placard", 1058, 1120)], flat=True)
strip("mr", 1225, 1375, [("mr_w_neutral", 88, 1300), ("mr_w0", 222, 1300), ("mr_w1", 307, 1300), ("mr_w2", 385, 1300),
                         ("mr_w3", 470, 1300)])

strip("mr", 1225, 1380, [("mr_run0", 630, 1310), ("mr_run1", 765, 1310), ("mr_run2", 902, 1310), ("mr_run3", 1022, 1310)])

# ------------------------------------------------------------------ Coleen (cr)
strip("cr", 100, 840, [("cr_hero", 150, 450)], tag="hero")
strip("cr", 130, 425, [("cr_t_front", 375, 280), ("cr_t_q34L", 528, 280), ("cr_t_side", 680, 280), ("cr_t_q34R", 853, 280),
                       ("cr_t_back", 1016, 280)])
strip("cr", 470, 665, [("cr_b_front", 366, 570), ("cr_b_q34L", 519, 570), ("cr_b_side", 683, 570), ("cr_b_q34R", 863, 570),
                       ("cr_b_back", 1019, 570)], flat=True)
strip("cr", 712, 860, [("cr_e_neutral", 345, 790), ("cr_e_happy", 458, 790), ("cr_e_laughing", 575, 790), ("cr_e_amused", 690, 790),
                       ("cr_e_confused", 808, 790), ("cr_e_shocked", 926, 790), ("cr_e_smirking", 1044, 790)], flat=True)
strip("cr", 1020, 1160, [("cr_p_seated", 582, 1095), ("cr_p_laughing", 698, 1095), ("cr_p_reaction", 810, 1095),
                         ("cr_p_shrug", 926, 1095), ("cr_p_pointing", 1048, 1095)], flat=True)
strip("cr", 1205, 1355, [("cr_w_neutral", 82, 1280), ("cr_w0", 223, 1280), ("cr_w1", 307, 1280), ("cr_w2", 392, 1280),
                         ("cr_w3", 484, 1280), ("cr_hb0", 638, 1280), ("cr_hb1", 754, 1280), ("cr_hb2", 891, 1280),
                         ("cr_hb3", 1018, 1280)])

# ------------------------------------------------------------------ the Rooney boys: one template, four sheets
for b in ("b1", "b2", "b3", "b4"):
    strip(b, 100, 830, [(b + "_hero", 150, 450)], tag="hero")
    strip(b, 140, 468, [(b + "_t_front", 370, 300), (b + "_t_q34L", 532, 300), (b + "_t_side", 690, 300), (b + "_t_q34R", 845, 300),
                        (b + "_t_back", 1006, 300)])
    strip(b, 525, 710, [(b + "_b_front", 372, 625), (b + "_b_q34L", 527, 625), (b + "_b_side", 685, 625), (b + "_b_q34R", 847, 625),
                        (b + "_b_back", 1015, 625)], flat=True)
    strip(b, 758, 898, [(b + "_e_neutral", 355, 830), (b + "_e_happy", 485, 830), (b + "_e_laughing", 623, 830),
                        (b + "_e_confused", 759, 830), (b + "_e_shocked", 894, 830), (b + "_e_cheeky", 1030, 830)], flat=True)
    strip(b, 1030, 1195, [(b + "_p_seated", 600, 1125), (b + "_p_laughing", 717, 1125), (b + "_p_handsup", 822, 1125),
                          (b + "_p_pointing", 952, 1125), (b + "_p_cheering", 1053, 1125)], flat=True)
    strip(b, 1225, 1370, [(b + "_w_neutral", 80, 1290), (b + "_w0", 212, 1290), (b + "_w1", 294, 1290), (b + "_w2", 380, 1290),
                          (b + "_w3", 475, 1290)])

# ------------------------------------------------------------------ Micah's friends (fr): celebration poses + props
strip("fr", 800, 1105, [("fr_jamie_cheers", 72, 960), ("fr_jamie_yes", 198, 960), ("fr_jamie_banter", 338, 960),
                        ("fr_dan_cake", 470, 960), ("fr_dan_clap", 582, 960), ("fr_dan_armsup", 690, 960),
                        ("fr_ravi_placard", 820, 960), ("fr_ravi_pointing", 960, 960),
                        ("fr_balloons", 1060, 880)])
strip("fr", 1160, 1320, [("fr_p_cake", 108, 1240), ("fr_p_placard", 285, 1240), ("fr_p_balloons", 438, 1240),
                         ("fr_p_pint", 583, 1250), ("fr_p_confetti", 705, 1250), ("fr_p_sign", 865, 1250),
                         ("fr_p_football", 1045, 1250)])

# ------------------------------------------------------------------ Gary Lineker (gy)
strip("gy", 110, 860, [("gy_hero", 140, 450)], tag="hero")
strip("gy", 140, 470, [("gy_t_front", 370, 300), ("gy_t_q34L", 530, 300), ("gy_t_side", 683, 300), ("gy_t_q34R", 846, 300),
                       ("gy_t_back", 1006, 300)])
strip("gy", 525, 712, [("gy_b_front", 370, 625), ("gy_b_q34L", 525, 625), ("gy_b_side", 680, 625), ("gy_b_q34R", 845, 625),
                       ("gy_b_back", 1015, 625)], flat=True)
strip("gy", 762, 900, [("gy_e_neutral", 345, 840), ("gy_e_happy", 452, 840), ("gy_e_amused", 560, 840), ("gy_e_surprised", 680, 840),
                       ("gy_e_confused", 793, 840), ("gy_e_laughing", 920, 840), ("gy_e_smiling", 1040, 840)], flat=True)
strip("gy", 1058, 1182, [("gy_p_talking1", 595, 1120), ("gy_p_talking2", 700, 1120), ("gy_p_pointing", 805, 1120),
                         ("gy_p_amused", 915, 1120), ("gy_p_sofa", 1035, 1120)], flat=True)

# ------------------------------------------------------------------ Wayne: upper-body gesture poses (waist-up, real torso + hands)
strip("wr", 936, 1108, [("wr_p_talking", 680, 1045), ("wr_p_shrug", 830, 1045), ("wr_p_handsup", 950, 1050),
                        ("wr_p_seated", 1060, 1040)], flat=True)

# ------------------------------------------------------------------ Micah, sheet 2 (m2): bigger drawings
strip("m2", 100, 770, [("m2_hero", 150, 450)], tag="hero")
strip("m2", 138, 452, [("m2_t_front", 372, 300), ("m2_t_q34L", 534, 300), ("m2_t_side", 689, 300), ("m2_t_q34R", 851, 300),
                       ("m2_t_back", 1016, 300)])
strip("m2", 500, 690, [("m2_b_front", 372, 600), ("m2_b_q34L", 533, 600), ("m2_b_side", 690, 600), ("m2_b_q34R", 855, 600),
                       ("m2_b_back", 1018, 600)], flat=True)
strip("m2", 738, 868, [("m2_e_neutral", 350, 800), ("m2_e_happy", 456, 800), ("m2_e_smug", 572, 800), ("m2_e_laughing", 688, 800),
                       ("m2_e_confused", 803, 800), ("m2_e_shocked", 925, 800), ("m2_e_proud", 1040, 800)], flat=True)
strip("m2", 1048, 1202, [("m2_p_talking", 100, 1140), ("m2_p_shrug", 275, 1140), ("m2_p_pointing", 445, 1140),
                         ("m2_p_handsup", 620, 1130), ("m2_p_seated", 810, 1140), ("m2_p_placard", 1005, 1140)], flat=True)
strip("m2", 1252, 1388, [("m2_w_neutral", 80, 1320), ("m2_w0", 200, 1320), ("m2_w1", 287, 1320), ("m2_w2", 375, 1320),
                         ("m2_w3", 469, 1320), ("m2_run0", 625, 1320), ("m2_run1", 762, 1320), ("m2_run2", 900, 1320),
                         ("m2_run3", 1025, 1320)])

# ------------------------------------------------------------------ Alan Shearer (as)
strip("as", 106, 690, [("as_t_front", 110, 400), ("as_t_q34", 300, 400), ("as_t_side", 462, 400), ("as_t_back", 640, 400)])
strip("as", 128, 308, [("as_e_neutral", 820, 225), ("as_e_smile", 975, 225), ("as_e_laugh", 1135, 225)], flat=True)
strip("as", 335, 508, [("as_e_surprised", 820, 425), ("as_e_serious", 975, 425), ("as_e_confused", 1135, 425)], flat=True)
strip("as", 530, 708, [("as_e_disapproving", 820, 625), ("as_e_amused", 975, 625), ("as_e_thinking", 1135, 625)], flat=True)
strip("as", 955, 1243, [("as_p_pointing", 100, 1110), ("as_p_talking", 290, 1110), ("as_p_listening", 470, 1110),
                        ("as_p_thinking", 640, 1110)], flat=True)

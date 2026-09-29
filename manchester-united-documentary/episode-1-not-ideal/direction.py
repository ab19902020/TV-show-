"""Direction for scenes 1-4: the shot list (coverage per the script) and every character's acting cues.

A shot is (start, end, setup, cam from, cam to, options). Cameras are (centre x, centre y, width) in the set's 1x
plate px; the move between them is a slow documentary push / drift with an ease. Setups are drawn by render.py.
Acting cues are keyed to the dialogue marks / words (timeline.py), so a change of pause moves the acting with it."""
import json
import perf
from perf import key, pose, pulse, m, EXTRA_BLINKS

L = perf.LINES
EV = {e["id"]: e for e in perf.TL["events"]}


def W(lid, word, occ=1):
    """absolute time of a word in a placed line"""
    e = EV[lid]
    k = 0
    for w in L[e["src"]]["words"]:
        if w["w"] == word:
            k += 1
            if k == occ: return e["t"] + w["s"]
    raise KeyError((lid, word))


def E(lid):
    e = EV[lid]; return e["t"] + e["dur"]


def T(lid):
    return EV[lid]["t"]


# ---------------------------------------------------------------- cameras (1x plate px: cx, cy, w)
WIDE = (836, 470.5, 1672)
WIDE_IN = (812, 462, 1540)
WIDE2 = (690, 440, 1260)
CK2JS = (370, 440, 610)
CK_MCU = (238, 424, 470)
CK_CU = (234, 410, 330)
CK_XCU = (233, 402, 250)
JS_MS = (452, 414, 380)
JS_CU = (452, 392, 270)
OM_MS = (652, 418, 360)
OM_CU = (642, 398, 250)
JR_MS = (995, 392, 320)
JR_CU = (995, 380, 230)
JS_OM = (545, 418, 450)
PRES = (770, 352, 900)
TVC = (1006, 300, 430)


def cam_push(c, k):
    """the same framing k times tighter"""
    return (c[0], c[1], c[2] / k)


SHOTS = []


def shot(t0, t1, setup, c0, c1=None, dof=None, ease="inout", shake=1.0, **kw):
    SHOTS.append(dict(t0=t0, t1=t1, setup=setup, c0=c0, c1=c1 or c0, dof=dof, ease=ease, shake=shake, **kw))


# ================================================================ SCENE 1
shot(0.0, m("corridor"), "ext_carrington", (836, 470, 1672), (860, 452, 1480), dof=0, shake=0.4)
shot(m("corridor"), m("walk"), "corridor_staff", (800, 440, 1400), (860, 440, 1300), dof=0, shake=0.8)
shot(m("walk"), m("board_wide"), "corridor_walk", (440, 360, 560), (440, 360, 660), dof=3.2, shake=1.2, ease="linear")
shot(m("board_wide"), 17.0, "board", WIDE, WIDE_IN, dof=0, shake=0.5)
shot(17.0, 21.25, "board", CK2JS, cam_push(CK2JS, 1.04), dof=2.4)
shot(21.25, 25.0, "board", CK_MCU, cam_push(CK_MCU, 1.05), dof=3.5)
shot(25.0, m("tap1"), "board", JS_MS, cam_push(JS_MS, 1.03), dof=3.5)
shot(m("tap1"), m("omar_down"), "tablet", None)
shot(m("omar_down"), m("ck_watches"), "board", OM_MS, cam_push(OM_MS, 1.03), dof=3.5)
shot(m("ck_watches"), m("tap_ok"), "board", CK_MCU, cam_push(CK_MCU, 1.02), dof=3.5)
shot(m("tap_ok"), W("js_well", "clarity") - 0.12, "board", JS_MS, cam_push(JS_MS, 1.06), dof=3.5)
shot(W("js_well", "clarity") - 0.12, T("js_yeah") - 0.08, "board", TVC, cam_push(TVC, 1.06), dof=0, shake=0.6)
shot(T("js_yeah") - 0.08, T("ck_right") - 0.45, "board", JS_MS, cam_push(JS_MS, 1.02), dof=3.5)
shot(T("ck_right") - 0.45, E("ck_jason") + 0.2, "board", CK_CU, cam_push(CK_CU, 1.07), dof=4.5)
shot(E("ck_jason") + 0.2, T("ck_who_signing") - 0.1, "board", JS_MS, cam_push(JS_MS, 1.02), dof=3.5)
shot(T("ck_who_signing") - 0.1, m("music_cut"), "board", CK_CU, cam_push(CK_CU, 1.03), dof=4.5)
shot(m("music_cut"), T("ck_i_know") - 0.35, "board", OM_MS, cam_push(OM_MS, 1.04), dof=3.5)
shot(T("ck_i_know") - 0.35, T("js_options_a") - 0.2, "board", CK_MCU, cam_push(CK_MCU, 1.05), dof=3.5)
shot(T("js_options_a") - 0.2, T("ck_no") - 0.12, "board", JS_MS, cam_push(JS_MS, 1.04), dof=3.5)
shot(T("ck_no") - 0.12, T("jr_no1") - 0.3, "board", CK_MCU, dof=3.5)
shot(T("jr_no1") - 0.3, m("ck_stares") - 0.6, "board", JR_MS, cam_push(JR_MS, 1.02), dof=3.5)
shot(m("ck_stares") - 0.6, m("closer_ck") - 0.05, "board", CK_MCU, cam_push(CK_MCU, 1.03), dof=3.5)
shot(m("closer_ck") - 0.05, m("jim_looks") - 0.9, "board", CK_XCU, cam_push(CK_XCU, 1.02), dof=5.0, punch=True)
shot(m("jim_looks") - 0.9, T("ck_left_back") - 0.15, "board", JR_MS, cam_push(JR_MS, 1.02), dof=3.5)
# the tennis rally down the table
shot(T("ck_left_back") - 0.15, T("jr_no2") - 0.12, "board", CK_CU, dof=4.5)
shot(T("jr_no2") - 0.12, T("ck_centre_back") - 0.12, "board", JR_MS, dof=3.5)
shot(T("ck_centre_back") - 0.12, m("jim_expression") - 0.35, "board", CK_CU, dof=4.5)
shot(m("jim_expression") - 0.35, T("ck_another_forward") - 0.12, "board", JR_CU, cam_push(JR_CU, 1.03), dof=4.0)
shot(T("ck_another_forward") - 0.12, T("jr_already_asked") - 0.12, "board", CK_CU, dof=4.5)
shot(T("jr_already_asked") - 0.12, m("ck_blinks") - 0.05, "board", JR_MS, dof=3.5)
shot(m("ck_blinks") - 0.05, T("jr_got_one") - 0.12, "board", CK_CU, dof=4.5)
shot(T("jr_got_one") - 0.12, m("look_camera") - 0.3, "board", JR_MS, cam_push(JR_MS, 1.02), dof=3.5)
shot(m("look_camera") - 0.3, m("cutaway_pres"), "board", CK_MCU, cam_push(CK_MCU, 1.06), dof=3.5)
# cutaway: the corporate presentation
shot(m("cutaway_pres"), m("sale_graphic"), "board", PRES, cam_push(PRES, 1.04), dof=1.2)
shot(m("sale_graphic"), m("sale_graphic") + 0.9, "board", TVC, cam_push(TVC, 1.05), dof=0, shake=0.6)
shot(m("sale_graphic") + 0.9, m("exchange_look"), "board", CK_MCU, cam_push(CK_MCU, 1.04), dof=3.5)
shot(m("exchange_look"), T("js_at_moment") - 0.12, "board", JS_OM, cam_push(JS_OM, 1.02), dof=2.5)
shot(T("js_at_moment") - 0.12, T("ck_how_much_lot") - 0.15, "board", JS_MS, cam_push(JS_MS, 1.03), dof=3.5)
shot(T("ck_how_much_lot") - 0.15, T("js_enough") - 0.15, "board", CK_MCU, cam_push(CK_MCU, 1.06), dof=3.5)
shot(T("js_enough") - 0.15, E("js_enough") + 0.25, "board", JS_MS, cam_push(JS_MS, 1.02), dof=3.5)
shot(E("js_enough") + 0.25, T("js_long_term") - 0.12, "board", CK_MCU, cam_push(CK_MCU, 1.04), dof=3.5)
shot(T("js_long_term") - 0.12, T("om_describe") - 0.15, "board", JS_MS, dof=3.5)
shot(T("om_describe") - 0.15, T("ck_sell_to_buy") - 0.25, "board", OM_MS, cam_push(OM_MS, 1.05), dof=3.5)
shot(T("ck_sell_to_buy") - 0.25, E("ck_sell_to_buy") + 0.45, "board", CK_MCU, dof=3.5)
shot(E("ck_sell_to_buy") + 0.45, m("objectives") - 0.1, "board", WIDE2, cam_push(WIDE2, 1.02), dof=0.8)
shot(m("objectives") - 0.1, m("scroll1") - 0.1, "board", CK_MCU, dof=3.5)
shot(m("scroll1") - 0.1, T("ck_anything_else") - 0.3, "board", TVC, cam_push(TVC, 1.03), dof=0, shake=0.6)
shot(T("ck_anything_else") - 0.3, m("scroll2") - 0.05, "board", CK_MCU, cam_push(CK_MCU, 1.02), dof=3.5)
shot(m("scroll2") - 0.05, T("ck_everything_i_need") - 0.25, "board", TVC, cam_push(TVC, 1.03), dof=0, shake=0.6)
shot(T("ck_everything_i_need") - 0.25, T("jr_dont_complain") - 0.15, "board", CK_MCU, dof=3.5)
shot(T("jr_dont_complain") - 0.15, E("jr_dont_complain") + 0.45, "board", JR_MS, cam_push(JR_MS, 1.03), dof=3.5)
shot(E("jr_dont_complain") + 0.45, m("push_ck"), "board", CK_MCU, dof=3.5)
shot(m("push_ck"), E("ck_where_money") + 0.2, "board", CK_MCU, CK_XCU, dof=4.5, ease="linear")
shot(E("ck_where_money") + 0.2, T("jr_debt") - 0.2, "board", OM_MS, cam_push(OM_MS, 1.03), dof=3.5)
shot(T("jr_debt") - 0.2, T("ck_glazer_dividends") - 0.15, "board", JR_MS, dof=3.5)
shot(T("ck_glazer_dividends") - 0.15, m("find_omar"), "board", CK_MCU, dof=3.5)
shot(m("find_omar"), T("jr_funny") - 0.2, "board", OM_CU, cam_push(OM_CU, 1.05), dof=4.5, whip=True)
shot(T("jr_funny") - 0.2, m("chime") + 0.2, "board", JR_MS, cam_push(JR_MS, 1.02), dof=3.5)
shot(m("chime") + 0.2, m("screen_on"), "board", WIDE2, cam_push(WIDE2, 1.02), dof=0.6)
# ================================================================ SCENE 2: THE GLAZERS CALL
shot(m("screen_on"), T("jg_michael") - 0.1, "board", TVC, cam_push(TVC, 1.04), dof=0, shake=0.5)
shot(T("jg_michael") - 0.1, T("av_michael_good_luck") - 0.1, "board", CK_MCU, cam_push(CK_MCU, 1.03), dof=3.5)
shot(T("av_michael_good_luck") - 0.1, m("half_wave"), "board", TVC, (1060, 300, 390), dof=0, shake=0.5)
shot(m("half_wave"), T("jg_excited") - 0.1, "board", CK_MCU, dof=3.5)
shot(T("jg_excited") - 0.1, m("call_ends") + 0.15, "board", TVC, cam_push(TVC, 1.05), dof=0, shake=0.5)
shot(m("call_ends") + 0.15, T("jr_unfortunately") - 0.2, "board", CK_MCU, cam_push(CK_MCU, 1.05), dof=3.5)
shot(T("jr_unfortunately") - 0.2, T("ck_cheers") - 0.2, "board", JR_MS, cam_push(JR_MS, 1.03), dof=3.5)
shot(T("ck_cheers") - 0.2, m("folder") - 0.1, "board", CK_MCU, cam_push(CK_MCU, 1.06), dof=3.5)
shot(m("folder") - 0.1, m("ck_looks_jim") - 0.25, "board", JR_MS, cam_push(JR_MS, 1.03), dof=3.5)
shot(m("ck_looks_jim") - 0.25, T("jr_dont_lose") - 0.12, "board", CK_CU, dof=4.5)
shot(T("jr_dont_lose") - 0.12, m("black"), "board", JR_CU, cam_push(JR_CU, 1.04), dof=4.0)
shot(m("black"), m("title"), "black", None)
shot(m("title"), m("title_end"), "title", None)
# ================================================================ SCENE 3: HULL AWAY, PRE-MATCH (setups in hull.py)
shot(m("s3"), m("inserts"), "ext_stadium", (836, 470, 1672), (858, 492, 1470), dof=0, shake=0.5)
# the fast inserts, one or two beats each (timeline.py: 80 bpm)
shot(m("ins_boots"), m("ins_shirts"), "ins_boots", (760, 705, 400), (815, 708, 380), dof=0, shake=0.8, rack=5.0)
shot(m("ins_shirts"), m("ins_tape"), "ins_shirts", (232, 288, 420), (236, 296, 392), dof=0, shake=0.8, rack=4.0)
shot(m("ins_tape"), m("ins_gloves"), "ins_tape", (900, 602, 630), (900, 606, 610), dof=0, shake=0.9)
shot(m("ins_gloves"), m("ins_walk"), "ins_gloves", (836, 330, 900), (836, 330, 880), dof=0, shake=1.0)
shot(m("ins_walk"), m("ins_captain"), "ins_walk", (1000, 430, 620), (1000, 440, 660), dof=3.0, shake=1.3, ease="linear")
shot(m("ins_captain"), m("ins_laces"), "ins_captain", (1010, 500, 660), (1012, 494, 620), dof=4.0, shake=1.1)
shot(m("ins_laces"), m("ins_board"), "ins_laces", (800, 642, 490), (800, 640, 470), dof=0, shake=0.9)
shot(m("ins_board"), m("dressing"), "ins_board", (320, 250, 620), (330, 252, 580), dof=1.5, shake=0.7)
# the team talk
shot(m("dressing"), W("ck_newly_promoted", "crowd") - 0.1, "dress_wide", (836, 470, 1672), (836, 478, 1580), dof=0, shake=0.5)
shot(W("ck_newly_promoted", "crowd") - 0.1, W("ck_newly_promoted", "do") - 0.12, "dress_carrick", (836, 262, 520),
     (836, 258, 490), dof=3.0)
shot(W("ck_newly_promoted", "do") - 0.12, E("ck_newly_promoted") + 0.3, "dress_bruno", (1440, 228, 380), (1440, 226, 350), dof=4.0)
shot(E("ck_newly_promoted") + 0.3, W("ck_set_pieces", "set") - 0.3, "carrick_board", (440, 318, 690), (448, 320, 640), dof=2.5)
shot(W("ck_set_pieces", "set") - 0.3, E("ck_set_pieces") + 0.2, "board_point", (175, 215, 360), (178, 214, 320), dof=0, punch=True)
shot(E("ck_set_pieces") + 0.2, E("mg_set_pieces") + 0.28, "dress_maguire", (258, 237, 533), (258, 240, 500), dof=4.5)
shot(E("mg_set_pieces") + 0.28, m("s4"), "dress_carrick", (836, 262, 520), (836, 260, 505), dof=3.0)
# ================================================================ SCENE 4: HULL MATCH (the 3D pitch, hull.py)
shot(m("s4"), m("crowd"), "match_wide", None)
shot(m("crowd"), m("corner1"), "match_crowd", None)
shot(m("corner1"), m("goal1_card"), "match_corner", None)
shot(m("goal1_card"), m("ck_still"), "card", None, card=("HULL", 1, "UNITED", 0, "23'"))
shot(m("ck_still"), m("corner2"), "match_touchline", (480, 270, 960), (480, 262, 900), dof=0)
shot(m("corner2"), m("goal2_card"), "match_chaos", None)
shot(m("goal2_card"), m("bruno_looks"), "card", None, card=("HULL", 2, "UNITED", 0, "61'"))
shot(m("bruno_looks"), m("maguire_turns"), "match_bruno", (480, 270, 960), (480, 266, 925), dof=0)
shot(m("maguire_turns"), m("whistle") + 0.45, "match_maguire", (480, 270, 960), (480, 270, 935), dof=0)
shot(m("whistle") + 0.45, m("end") + 0.01, "black34", None)


# ================================================================ ACTING
C, J, O, R = "carrick", "jason", "omar", "jim"
# --- defaults: who looks at whom (screen space; Jason is mirrored in the drawing, handled at render)
key(C, "look", 0, (0.55, 0.02), 0.01); key(C, "turn", 0, 0.12, 0.01)
key(J, "look", 0, (-0.45, 0.05), 0.01); key(J, "turn", 0, -0.08, 0.01)
key(O, "look", 0, (-0.55, 0.02), 0.01)
key(R, "look", 0, (-0.15, 0.75), 0.01); key(R, "brow", 0, -0.15, 0.01)
pose(J, 0, "js_tablet")
# corridor walk (Carrick): looks ahead, glances down at his jacket, small breath
walk = m("walk")
key(C, "look", walk, (0.0, -0.05), 0.01); key(C, "turn", walk, 0.0, 0.01)
key(C, "look", walk + 3.7, (0.0, 0.8), 0.25); key(C, "look", walk + 4.3, (0.05, 0.0), 0.3)
key(C, "brow", walk + 4.5, 0.25, 0.3); key(C, "brow", walk + 5.2, 0.0, 0.4)
EXTRA_BLINKS[C] += [walk + 4.5]
# boardroom: everyone settled; Jason energised
bw = m("board_wide")
key(C, "look", bw, (0.55, 0.02), 0.01); key(C, "turn", bw, 0.12, 0.01)
key(J, "smile", bw + 0.4, 0.55, 0.5); key(J, "brow", bw + 0.4, 0.35, 0.5)
key(J, "look", T("js_new_season"), (-0.6, 0.0), 0.3)
pulse(C, "nod", W("js_new_season", "plan") + 0.1, 4.0, 0.18, 0.05, 0.3)
key(J, "smile", E("js_new_season") + 0.1, 0.7, 0.4)
# Carrick expects more... nothing comes
key(C, "brow", m("expects_more") - 1.6, 0.35, 0.5)
pulse(C, "nod", m("expects_more") - 1.9, 3.0, 0.2, 0.05, 0.35)
key(C, "brow", T("ck_whats_plan") + 0.1, 0.5, 0.2); key(C, "brow", E("ck_whats_plan") + 0.4, 0.15, 0.5)
# Jason: "One second" - glances down at the tablet, taps
key(J, "smile", T("js_one_second"), 0.2, 0.3); key(J, "look", T("js_one_second") + 0.15, (0.15, 0.85), 0.25)
key(J, "brow", T("js_one_second"), 0.0, 0.3)
key(O, "look", m("omar_down") + 0.3, (-0.1, 0.8), 0.5); key(O, "brow", m("omar_down") + 0.3, -0.2, 0.5)
key(C, "look", m("ck_watches") - 0.2, (0.6, 0.35), 0.4)
key(J, "brow", m("tap_ok") + 0.3, 0.5, 0.2); key(J, "smile", m("tap_ok") + 0.3, 0.8, 0.25)
key(J, "look", m("tap_ok") + 0.5, (-0.55, -0.05), 0.3)
key(O, "look", m("tap_ok") + 0.4, (0.9, -0.5), 0.5); key(O, "brow", m("tap_ok") + 0.4, 0.0, 0.5)
key(C, "look", m("tap_ok") + 0.4, (0.9, -0.45), 0.4)
# SHOT 3: the buzzwords - Jason presents
pose(J, T("js_well") - 0.05, "js_present")
key(J, "look", T("js_well"), (-0.6, 0.0), 0.2)
for w_ in ("js_alignment", "js_sustain", "js_agility"):
    pulse(J, "nod", T(w_) + 0.05, 5.0, 0.12, 0.08, 0.3)
    pulse(J, "brow", T(w_) + 0.02, 0.8, 0.1, 0.2, 0.3)
key(C, "look", W("js_well", "clarity") - 0.3, (0.95, -0.5), 0.4)
# "Yeah?" - turns to Carrick expectantly
pose(J, T("js_yeah") - 0.35, "js_shrug")
key(J, "look", T("js_yeah") - 0.3, (-0.9, 0.0), 0.2); key(J, "turn", T("js_yeah") - 0.3, -0.35, 0.25)
key(J, "brow", T("js_yeah"), 0.95, 0.15); key(J, "smile", T("js_yeah"), 0.85, 0.2)
# Carrick close-up: the tiniest nod; beats
key(C, "look", T("ck_right") - 0.4, (0.5, 0.0), 0.35); key(C, "brow", T("ck_right") - 0.4, 0.0, 0.4)
pulse(C, "nod", T("ck_right") + 0.05, 2.2, 0.18, 0.02, 0.3)
pulse(C, "nod", T("ck_yep") + 0.05, 1.6, 0.15, 0.02, 0.3)
key(C, "look", E("ck_okay") + 0.3, (0.35, 0.15), 0.4)
key(C, "look", T("ck_jason") - 0.2, (0.55, 0.0), 0.2)
key(C, "brow", T("ck_jason") - 0.2, 0.2, 0.3)
EXTRA_BLINKS[C] += [E("ck_okay") + 0.9]
pose(J, E("ck_jason") + 0.05, "js_tablet")
key(J, "turn", E("ck_jason") + 0.05, -0.15, 0.3); key(J, "smile", E("ck_jason") + 0.3, 1.0, 0.3); key(J, "brow", E("ck_jason") + 0.3, 0.4, 0.3)
key(C, "brow", T("ck_who_signing"), 0.35, 0.2); key(C, "look", T("ck_who_signing"), (0.55, 0.0), 0.2)
# music cut: Omar
key(J, "smile", m("music_cut") + 0.3, 0.25, 0.8); key(J, "brow", m("music_cut") + 0.3, 0.0, 0.8)
key(O, "look", m("music_cut") - 0.1, (-0.65, 0.0), 0.3); key(O, "smile", m("music_cut"), 0.25, 0.4); key(O, "brow", m("music_cut"), 0.15, 0.4)
key(C, "look", T("om_invested"), (0.8, 0.0), 0.3)
pulse(C, "nod", T("ck_i_know") + 0.05, 3.0, 0.2, 0.05, 0.35)
key(C, "brow", T("ck_just_thinking"), 0.25, 0.3)
key(C, "look", T("ck_another_striker") - 0.2, (0.8, -0.05), 0.2); key(O, "smile", T("ck_another_striker"), 0.1, 0.5)
# Jason leans forward
pose(J, T("js_options_a") - 0.25, "js_present")
key(J, "fwd", T("js_options_a") - 0.25, 1.0, 0.35); key(J, "smile", T("js_options_a"), 0.7, 0.3); key(J, "brow", T("js_options_a"), 0.4, 0.3)
key(J, "fwd", E("js_options_a") + 0.8, 0.0, 0.6)
pose(J, E("js_options_a") + 0.9, "js_tablet")
# Carrick nods toward him: "No?"
key(C, "look", T("ck_no") - 0.15, (0.6, 0.0), 0.2); key(C, "brow", T("ck_no"), 0.45, 0.2)
pulse(C, "nod", T("ck_no"), 3.0, 0.15, 0.05, 0.3)
# Jim: doesn't even look up
key(R, "look", T("jr_no1") - 0.5, (-0.1, 0.85), 0.3); key(R, "brow", T("jr_no1") - 0.5, -0.25, 0.3)
# Carrick stares; "Benjamin's injured"; closer: "He's INJURED"
key(C, "look", m("ck_stares") - 0.5, (0.95, -0.02), 0.3); key(C, "brow", m("ck_stares") - 0.5, 0.1, 0.4)
key(C, "brow", T("ck_hes_injured"), 0.7, 0.12); key(C, "brow", E("ck_hes_injured") + 0.5, 0.3, 0.5)
# Jim finally looks at him
key(R, "look", m("jim_looks") - 0.7, (-0.9, 0.0), 0.4); key(R, "brow", m("jim_looks") - 0.7, 0.0, 0.4)
key(R, "turn", m("jim_looks") - 0.7, -0.2, 0.5)
key(C, "look", T("ck_left_back") - 0.3, (0.95, 0.0), 0.2); key(C, "brow", T("ck_left_back") - 0.2, 0.35, 0.25)
key(R, "brow", m("jim_expression") - 0.3, -0.55, 0.25); key(R, "blinkx", m("jim_expression") - 0.3, 0.35, 0.25)
key(R, "blinkx", E("jr_no3") + 0.2, 0.0, 0.3); key(R, "brow", E("jr_no3") + 0.4, -0.2, 0.4)
key(R, "brow", T("jr_already_asked"), -0.35, 0.2)
# Carrick blinks
EXTRA_BLINKS[C] += [m("ck_blinks") + 0.05, m("ck_blinks") + 0.33]
key(C, "brow", m("ck_blinks"), 0.0, 0.2)
key(C, "brow", T("ck_goalkeeper"), 0.55, 0.2)
key(R, "brow", T("jr_got_one"), -0.1, 0.3)
# pause; Carrick looks straight down the lens
key(C, "look", m("look_camera") - 0.1, (0.0, 0.0), 0.35); key(C, "turn", m("look_camera") - 0.1, 0.0, 0.4)
key(C, "brow", m("look_camera") - 0.1, 0.15, 0.4); key(C, "smile", T("ck_fair_enough") + 0.6, 0.2, 0.4)
# cutaway: Jason points at the screen
pose(J, m("cutaway_pres") - 0.05, "js_sidepoint")
key(J, "smile", m("cutaway_pres"), 0.8, 0.3); key(J, "brow", m("cutaway_pres"), 0.5, 0.3)
key(C, "look", m("cutaway_pres"), (0.95, -0.45), 0.3); key(C, "turn", m("cutaway_pres"), 0.2, 0.4); key(C, "smile", m("cutaway_pres"), 0.0, 0.3)
key(O, "look", m("cutaway_pres"), (0.9, -0.5), 0.4); key(R, "look", m("cutaway_pres"), (-0.2, 0.8), 0.4)
# Carrick notices the player-sale graphic
key(C, "brow", m("sale_graphic") + 0.7, -0.35, 0.3); key(C, "look", m("sale_graphic") + 0.7, (1.0, -0.55), 0.25)
pose(J, E("js_one_of_options") + 0.2, "js_tablet")
key(C, "look", T("ck_how_much") - 0.1, (0.6, 0.0), 0.2); key(C, "brow", T("ck_how_much"), 0.3, 0.2)
# Jason and Omar exchange a look
key(J, "look", m("exchange_look") - 0.05, (0.9, 0.0), 0.2); key(J, "turn", m("exchange_look"), 0.3, 0.3); key(J, "smile", m("exchange_look"), 0.3, 0.3)
key(O, "look", m("exchange_look") + 0.1, (-0.9, 0.05), 0.2); key(O, "brow", m("exchange_look") + 0.1, 0.35, 0.3)
key(J, "look", T("js_at_moment") - 0.2, (-0.55, 0.05), 0.25); key(J, "turn", T("js_at_moment") - 0.2, -0.1, 0.3)
key(O, "look", T("js_at_moment") + 0.2, (-0.55, 0.05), 0.4); key(O, "brow", T("js_at_moment"), 0.0, 0.4)
key(J, "brow", T("js_a_lot") - 0.3, 0.6, 0.2); key(J, "smile", T("js_a_lot"), 0.55, 0.2)
# Carrick leans slightly forward
key(C, "fwd", T("ck_how_much_lot") - 0.2, 1.0, 0.4); key(C, "brow", T("ck_how_much_lot"), 0.2, 0.3)
key(J, "smile", T("js_enough"), 0.7, 0.3); key(J, "brow", T("js_enough"), 0.3, 0.3)
# silence; Carrick reclines
key(C, "fwd", m("ck_reclines") - 1.2, -0.9, 0.9); key(C, "brow", m("ck_reclines") - 1.2, -0.05, 0.6)
key(C, "look", m("ck_reclines") - 1.2, (0.4, 0.1), 0.6)
key(C, "look", T("ck_sell_to_buy_q") - 0.1, (0.6, 0.0), 0.3)
# Jason straight into corporate mode; Omar joins in
pose(J, T("js_long_term") - 0.15, "js_present")
key(J, "brow", T("js_long_term"), 0.4, 0.2); key(J, "smile", T("js_long_term"), 0.6, 0.2)
key(O, "smile", T("om_describe"), 0.3, 0.4); key(O, "brow", T("om_describe"), 0.2, 0.4)
pose(J, E("js_long_term") + 0.6, "js_tablet")
key(C, "look", T("ck_sell_to_buy") - 0.2, (0.65, 0.0), 0.25); key(C, "fwd", T("ck_sell_to_buy") - 0.3, 0.0, 0.5)
key(C, "brow", T("ck_sell_to_buy"), 0.0, 0.3)
key(O, "smile", E("ck_sell_to_buy") + 0.2, 0.0, 0.6); key(J, "smile", E("ck_sell_to_buy") + 0.2, 0.15, 0.6)
key(J, "look", E("ck_sell_to_buy") + 0.6, (0.3, 0.6), 0.5); key(O, "look", E("ck_sell_to_buy") + 0.9, (-0.2, 0.6), 0.5)
# objectives: the list scrolls, Carrick's eyes follow
key(C, "look", m("objectives") + 0.2, (0.9, -0.5), 0.3)
key(J, "look", m("objectives") + 0.3, (0.1, 0.8), 0.3)
for i in range(4):
    key(C, "look", m("scroll1") + 0.3 + i * 0.45, (0.95, -0.55 + 0.25 * (i % 2)), 0.2)
key(C, "look", T("ck_anything_else") - 0.1, (0.9, -0.45), 0.2)
for i in range(3):
    key(C, "look", m("scroll2") + 0.2 + i * 0.4, (0.95, -0.55 + 0.25 * (i % 2)), 0.2)
key(C, "look", T("ck_everything_i_need") - 0.3, (1.0, -0.02), 0.3); key(C, "turn", T("ck_everything_i_need") - 0.3, 0.3, 0.4)
key(R, "look", T("jr_dont_complain") - 0.3, (-0.9, 0.0), 0.3); key(R, "brow", T("jr_dont_complain"), -0.3, 0.3)
# two-second silence; Carrick nods; "Brilliant"; the push
key(C, "look", E("jr_dont_complain") + 0.6, (0.6, 0.1), 0.6); key(C, "turn", E("jr_dont_complain") + 0.6, 0.1, 0.6)
pulse(C, "nod", m("ck_nods"), 4.0, 0.25, 0.1, 0.4)
key(C, "smile", T("ck_brilliant"), 0.2, 0.3)
key(C, "look", T("ck_good_meeting") - 0.1, (0.45, 0.1), 0.3)
pulse(C, "nod", T("ck_positive"), 2.0, 0.2, 0.05, 0.3)
key(C, "smile", E("ck_good_meeting2"), 0.0, 0.5)
key(C, "look", m("notebook") + 0.1, (0.05, 0.9), 0.35)          # begins closing his notebook
key(C, "look", m("notebook") + 0.9, (0.1, 0.9), 0.3)
key(C, "look", T("ck_where_money") - 0.35, (0.75, 0.0), 0.25)   # stops. looks back up
key(C, "brow", T("ck_where_money") - 0.35, 0.3, 0.3)
key(O, "look", T("om_cash_flow") - 0.3, (-0.7, 0.0), 0.3); key(O, "smile", T("om_cash_flow"), 0.15, 0.4)
key(R, "look", T("jr_debt") - 0.2, (-0.8, 0.1), 0.3)
key(C, "look", T("ck_glazer_dividends") - 0.2, (0.8, 0.0), 0.2); key(C, "brow", T("ck_glazer_dividends"), 0.5, 0.2)
# the camera finds Omar: his expression changes by about 3 %
key(O, "look", m("find_omar") + 0.45, (-0.75, 0.08), 0.12); key(O, "smile", m("find_omar") + 0.45, 0.05, 0.12)
key(O, "brow", m("find_omar") + 0.45, 0.28, 0.12)
EXTRA_BLINKS[O] += [m("find_omar") + 0.7]
key(O, "smile", T("om_technically"), -0.1, 0.4)
key(R, "look", T("jr_funny") - 0.3, (-0.6, 0.1), 0.3); key(R, "smile", T("jr_funny") + 0.3, 0.15, 0.4)
# chime: everyone looks at the screen (Jim, under it, does not)
ch = m("chime")
key(C, "look", ch + 0.25, (1.0, -0.6), 0.25); key(C, "turn", ch + 0.25, 0.3, 0.35)
key(J, "look", ch + 0.35, (1.0, -0.6), 0.25); key(J, "turn", ch + 0.35, 0.3, 0.35)
key(O, "look", ch + 0.3, (1.0, -0.55), 0.25); key(O, "brow", ch + 0.3, 0.2, 0.3)
key(R, "look", ch + 0.2, (0.0, 0.3), 0.4); key(R, "smile", ch, 0.0, 0.4)
# ================================================================ SCENE 2 acting
key(C, "smile", T("jg_michael"), 0.25, 0.3); key(C, "brow", T("jg_michael"), 0.25, 0.3)
key(C, "smile", m("half_wave"), 0.35, 0.3)
key(C, "smile", T("jg_excited"), 0.1, 0.8)
# the call ends: the camera doesn't cut - the blank screen, then Jason, then Jim
key(C, "smile", m("call_ends"), 0.0, 0.4); key(C, "brow", m("call_ends"), 0.0, 0.4)
key(C, "look", m("look_screen"), (1.0, -0.6), 0.35)
key(C, "look", m("look_jason"), (0.55, 0.0), 0.3); key(C, "turn", m("look_jason"), 0.12, 0.3)
key(C, "look", m("look_jim"), (1.0, 0.0), 0.3); key(C, "turn", m("look_jim"), 0.3, 0.3)
key(J, "look", m("call_ends") + 0.3, (-0.5, 0.2), 0.4); key(J, "turn", m("call_ends") + 0.3, 0.0, 0.4); key(J, "smile", m("call_ends"), 0.3, 0.4)
key(O, "look", m("call_ends") + 0.4, (-0.2, 0.6), 0.5)
key(R, "look", T("jr_unfortunately") - 0.4, (-0.9, 0.0), 0.3); key(R, "brow", T("jr_unfortunately"), -0.2, 0.3)
key(C, "look", T("ck_cheers") - 0.2, (0.7, 0.05), 0.3); key(C, "turn", T("ck_cheers") - 0.2, 0.15, 0.3)
key(C, "smile", T("ck_brilliant_yep"), 0.15, 0.3)
key(C, "look", T("ck_sigh_good_input") + 0.2, (0.2, 0.45), 0.5); key(C, "smile", T("ck_sigh_good_input"), -0.05, 0.4)
pulse(C, "nod", T("ck_sigh_good_input") + 0.5, 5.0, 0.5, 0.3, 0.6)                 # the exhale
key(R, "look", m("folder"), (-0.05, 0.85), 0.3)                                      # closes his folder
pulse(R, "nod", m("folder") + 0.15, 4.0, 0.15, 0.1, 0.3)
key(R, "look", T("jr_right") + 0.1, (-0.85, 0.0), 0.35)
key(C, "look", m("ck_looks_jim") - 0.2, (1.0, 0.0), 0.25); key(C, "brow", m("ck_looks_jim"), 0.45, 0.25)
key(R, "brow", T("jr_dont_lose"), -0.35, 0.2)
# ================================================================ SCENE 3 acting
BR, CU, KM, MG = "bruno", "cunha", "mainoo", "maguire"
s3 = m("s3")
key(C, "look", s3, (0.0, -0.05), 0.01); key(C, "turn", s3, 0.0, 0.01); key(C, "brow", s3, 0.1, 0.01)
key(C, "smile", s3, 0.0, 0.01); key(C, "fwd", s3, 0.0, 0.01)
# Bruno: the captain routine in the tunnel - eyes front, a nod to himself, a look back down the line
cap = m("ins_captain")
key(BR, "look", 0, (-0.2, 0.0), 0.01); key(BR, "brow", 0, -0.7, 0.01); key(BR, "smile", 0, -0.9, 0.01)
pulse(BR, "nod", cap + 0.2, 5.0, 0.12, 0.05, 0.25); pulse(BR, "nod", cap + 0.55, 4.0, 0.12, 0.05, 0.25)
key(BR, "look", cap + 0.85, (0.95, 0.0), 0.15); key(BR, "turn", cap + 0.85, 0.35, 0.2)
key(BR, "look", cap + 1.35, (0.1, 0.0), 0.12); key(BR, "turn", cap + 1.35, 0.0, 0.15)
# Cunha stares at the board (profile, facing left)
key(CU, "look", 0, (-0.9, -0.1), 0.01)
EXTRA_BLINKS[CU] += [m("ins_board") + 0.9]
# the dressing room: everyone watches Carrick, centre
dr = m("dressing")
key(CU, "look", dr - 0.05, (-0.7, 0.0), 0.01); key(KM, "look", dr - 0.05, (0.7, 0.0), 0.01)
key(MG, "look", dr - 0.05, (0.75, 0.0), 0.01); key(MG, "brow", dr - 0.05, 0.25, 0.01)
key(BR, "look", dr - 0.05, (-0.75, 0.0), 0.01); key(BR, "turn", dr - 0.05, -0.15, 0.01)
key(BR, "brow", dr - 0.05, -0.9, 0.01); key(BR, "smile", dr - 0.05, -1.0, 0.01); key(BR, "blinkx", dr - 0.05, 0.12, 0.01)
key(C, "look", dr, (-0.35, 0.0), 0.3)
key(C, "look", W("ck_newly_promoted", "crowd"), (0.45, 0.0), 0.3); key(C, "turn", W("ck_newly_promoted", "crowd"), 0.1, 0.3)
key(C, "look", W("ck_newly_promoted", "do"), (-0.3, 0.05), 0.3); key(C, "turn", W("ck_newly_promoted", "do"), -0.05, 0.3)
pulse(C, "nod", W("ck_newly_promoted", "basics"), 3.0, 0.15, 0.05, 0.3)
pulse(BR, "nod", W("ck_newly_promoted", "basics") + 0.1, 4.0, 0.2, 0.1, 0.35)
pulse(MG, "nod", W("ck_newly_promoted", "team"), 5.0, 0.2, 0.1, 0.35)          # Maguire nodding
pulse(MG, "nod", W("ck_newly_promoted", "basics"), 5.0, 0.2, 0.1, 0.35)
# "And most importantly": he turns to the tactics board
key(C, "look", W("ck_set_pieces", "and") - 0.15, (-0.95, -0.05), 0.25); key(C, "turn", W("ck_set_pieces", "and") - 0.15, -0.35, 0.3)
key(C, "brow", W("ck_set_pieces", "set") - 0.1, 0.5, 0.2)
key(C, "look", E("ck_set_pieces") + 0.3, (0.4, 0.0), 0.3); key(C, "turn", E("ck_set_pieces") + 0.3, 0.05, 0.3)
# Maguire: dead serious. "Set pieces. Got it."
key(MG, "look", E("ck_set_pieces") + 0.1, (0.55, -0.05), 0.2); key(MG, "brow", E("ck_set_pieces") + 0.1, 0.35, 0.2)
pulse(MG, "nod", W("mg_set_pieces", "got") + 0.05, 5.5, 0.15, 0.08, 0.3)
EXTRA_BLINKS[MG] += [E("mg_set_pieces") + 0.12]
# "Right."
key(C, "look", T("ck_right3") - 0.3, (0.1, 0.0), 0.25); key(C, "brow", T("ck_right3") - 0.3, 0.15, 0.3)
pulse(C, "nod", T("ck_right3") + 0.05, 3.5, 0.15, 0.05, 0.3)
# ================================================================ SCENE 4 acting
# Carrick after the first goal: no reaction, just stillness (one blink, a long look)
cs = m("ck_still")
key(C, "look", cs - 0.5, (0.12, -0.08), 0.01); key(C, "brow", cs - 0.5, 0.05, 0.01); key(C, "turn", cs - 0.5, 0.05, 0.01)
key(C, "smile", cs - 0.5, 0.0, 0.01); key(C, "blinkx", cs - 0.5, 0.0, 0.01)
EXTRA_BLINKS[C] += [cs + 1.25]
# Bruno looks toward Maguire (screen right); Maguire slowly turns away
bl = m("bruno_looks")
key(BR, "look", bl - 0.5, (0.0, 0.0), 0.01); key(BR, "brow", bl - 0.5, -0.8, 0.01); key(BR, "blinkx", bl - 0.5, 0.0, 0.01)
key(BR, "turn", bl - 0.5, 0.0, 0.01); key(BR, "smile", bl - 0.5, -1.0, 0.01)
key(BR, "look", bl + 0.55, (1.0, 0.0), 0.28); key(BR, "turn", bl + 0.55, 0.35, 0.4)
key(BR, "brow", bl + 0.6, -1.0, 0.3)
mt = m("maguire_turns")
key(MG, "look", mt - 0.5, (-0.7, 0.0), 0.01); key(MG, "brow", mt - 0.5, 0.2, 0.01)
key(MG, "look", mt + 0.35, (0.4, 0.1), 0.25)             # his eyes leave Bruno's...
key(MG, "turn", mt + 0.75, 0.45, 0.45); key(MG, "look", mt + 0.75, (0.9, 0.05), 0.3)   # ...then the head goes
key(MG, "brow", mt + 0.35, 0.05, 0.3)

perf.finalize()
SHOTS.sort(key=lambda s: s["t0"])

if __name__ == "__main__":
    tot = 0
    for s in SHOTS:
        print(f"{s['t0']:7.2f}-{s['t1']:7.2f} {s['t1'] - s['t0']:5.2f}  {s['setup']:16s} {s['c0']}")
    for a, b in zip(SHOTS, SHOTS[1:]):
        if abs(a["t1"] - b["t0"]) > 0.02: print("GAP/OVERLAP", a["t1"], b["t0"], a["setup"], b["setup"])
    print(len(SHOTS), "shots")

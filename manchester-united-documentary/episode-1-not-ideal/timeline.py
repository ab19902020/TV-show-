"""The dialogue edit for scenes 1-4: every recorded line at its time on the episode timeline.

The lines are locked (build/lines/<id>.wav, cut word-exact by lines.py); only the silences between them are
directed here. `run` places several lines from one recording with the actor's own recorded rhythm (their original
gaps), optionally stretched; `say` places one line after a pause. Marks name the moments shots and actions hang off.

python3 timeline.py  -> build/timeline.json {events: [{id, speaker, t, dur}], marks: {name: t}, total}"""
import json

L = json.load(open("build/lines.json"))
EV, MARK = [], {}
T = [0.0]


def mark(name, t=None):
    MARK[name] = T[0] if t is None else t


def beat(s):
    T[0] += s


def say(lid, pause=0.0, as_id=None, name=None):
    """line after `pause` s; as_id = the same recording reused under another id (Jim's third "No")"""
    T[0] += pause
    ln = L[lid]
    e = dict(id=as_id or lid, src=lid, speaker=ln["speaker"], t=round(T[0], 3), dur=ln["dur"])
    EV.append(e)
    MARK[name or (as_id or lid)] = T[0]
    MARK[(name or (as_id or lid)) + ".end"] = T[0] + ln["dur"]
    T[0] += ln["dur"]
    return e


def run(ids, pause=0.0, stretch=1.0, extra=None):
    """consecutive lines of one clip with their recorded gaps (x stretch, + extra[i] s before line i)"""
    T[0] += pause
    first = L[ids[0]]
    base = first["s"]
    prev_end_clip = None
    for i, lid in enumerate(ids):
        ln = L[lid]
        if i:
            gap = max(0.0, ln["s"] - prev_end_clip) * stretch + (extra[i] if extra else 0.0)
            T[0] += gap
        say(lid)
        prev_end_clip = ln["e"]


# ================================================================ SCENE 1: CARRINGTON BOARDROOM
mark("s1")
beat(4.0); mark("corridor")            # exterior Carrington, then the corridor
beat(2.6); mark("walk")                # Carrick walks to the meeting room
beat(6.2); mark("board_wide")          # door opens: boardroom wide, hold two seconds
beat(2.2)
say("js_new_season")                   # "Right Michael. New season. New chapter. We've got a very clear plan."
beat(2.3); mark("expects_more")        # Carrick nods. Waits. Nothing comes.
say("ck_whats_plan")
say("js_one_second", 0.55)
beat(0.5); mark("tap1")                # Jason taps the tablet: nothing
beat(1.4); mark("omar_down")           # Omar subtly looks down
beat(1.3); mark("ck_watches")          # Carrick watches
beat(1.2); mark("tap_ok")              # it works
beat(1.0)
run(["js_well", "js_alignment", "js_sustain", "js_agility"], stretch=1.35)   # clarity / alignment / sustainability / agility
say("js_yeah", 0.55)                   # turns to Carrick expectantly
run(["ck_right", "ck_yep", "ck_okay", "ck_jason"], pause=0.9, stretch=1.0)  # the tiniest nod, beats, longer beat
beat(1.35); mark("jason_smiles")
say("ck_who_signing", 0.0)
mark("music_cut", MARK["ck_who_signing.end"] + 0.05)
say("om_invested", 0.75)
run(["ck_i_know", "ck_just_thinking", "ck_another_striker"], pause=0.6, stretch=0.85)
say("js_options", 0.6, as_id="js_options_a")          # Jason leans forward
say("ck_no", 0.45)                                     # Carrick nods toward him: "No?"
say("jr_no1", 0.7)                                     # Jim doesn't even look up
beat(1.1); mark("ck_stares")
say("ck_benjamins_injured")
beat(1.2); mark("closer_ck")
say("ck_hes_injured")
beat(1.1); mark("jim_looks")                           # Jim finally looks at him
say("ck_left_back", 0.5)
say("jr_no2", 0.5)
say("ck_centre_back", 0.45)
beat(0.7); mark("jim_expression")                      # the answer is on his face before he speaks
say("jr_no1", 0.0, as_id="jr_no3")
say("ck_another_forward", 0.55)
say("jr_already_asked", 0.5)
beat(0.5); mark("ck_blinks")
say("ck_goalkeeper", 0.35)
say("jr_got_one", 0.45)
beat(1.4); mark("look_camera")
say("ck_fair_enough", 0.25)
beat(0.7); mark("cutaway_pres")                        # corporate presentation: Jason scrolls
say("js_options", 0.5, as_id="js_options_b")
beat(0.35); mark("sale_graphic")                       # Carrick notices a player-sale graphic
say("js_one_of_options", 0.9)
say("ck_how_much", 0.45)
beat(0.35); mark("exchange_look")                      # Jason and Omar exchange a look
say("js_at_moment", 1.25)
say("js_a_lot", 0.75)
say("ck_how_much_lot", 0.6)                            # leans slightly forward
say("js_enough", 0.45)
beat(1.6); mark("ck_reclines")
run(["ck_right2", "ck_so", "ck_sell_to_buy_q"], pause=0.0, stretch=0.9)
say("js_long_term", 0.3)                               # straight into corporate mode
say("om_describe", 0.45)
say("ck_sell_to_buy", 0.7)
beat(2.0); mark("objectives")                          # hold: nobody contradicts him
say("ck_objectives", 0.0)
beat(0.5); mark("scroll1")                             # an absurd number of targets
say("ck_anything_else", 1.9)
beat(0.35); mark("scroll2")                            # another page
say("ck_everything_i_need", 1.6)                       # looks toward Jim
say("jr_dont_complain", 0.6)
beat(2.0); mark("ck_nods")
say("ck_brilliant", 0.3)
mark("push_ck")
say("ck_good_meeting", 0.55)
say("ck_positive", 0.75)
say("ck_good_meeting2", 0.95)
beat(0.55); mark("notebook")                           # closes his notebook... stops... looks back up
say("ck_where_money", 1.35)
say("om_cash_flow", 0.5)
say("om_infrastructure", 0.75)
say("jr_debt", 0.5)
say("ck_glazer_dividends", 0.55)
beat(0.15); mark("find_omar")                          # camera immediately finds Omar: a 3% change
say("om_technically", 1.15)
say("jr_funny", 0.55)
beat(0.45); mark("chime")                              # laptop chime: everyone looks at the screen
beat(1.5)
# ================================================================ SCENE 2: THE GLAZERS CALL
mark("s2")
beat(0.6); mark("screen_on")
say("om_morning_joel", 0.9)
say("jg_hello", 0.45)                                  # waves too enthusiastically
say("jg_hear_us", 0.8)
beat(0.25); mark("volume")                             # someone adjusts the laptop volume
say("jg_michael", 0.85)
say("jg_good_luck", 0.35)
say("av_michael_good_luck", 0.3)                       # Avram immediately repeats it
beat(0.3); mark("half_wave")                           # Carrick: a polite half-wave
say("jg_excited", 1.2)
say("jg_big_season", 0.65)
beat(0.35); mark("avram_away")                         # someone is calling Avram away
say("av_need_to_run", 0.8)
say("jg_go_united", 0.4)
beat(0.35); mark("call_ends")
beat(0.9); mark("look_screen")                         # the camera doesn't cut: the blank screen
beat(1.1); mark("look_jason")                           # ... then Jason
beat(1.0); mark("look_jim")                             # ... then Jim
say("jr_unfortunately", 0.9)
say("ck_cheers", 0.9)
say("ck_brilliant_yep", 0.6)
say("ck_sigh_good_input", 0.35)                        # exhales: "[sigh] Good input"
beat(0.5); mark("folder")                              # Jim closes his folder
say("jr_right", 0.5)
say("jr_hull", 1.05)
beat(0.3); mark("ck_looks_jim")                        # Carrick looks at him
say("jr_dont_lose", 1.2)
beat(0.9); mark("black")
beat(0.8); mark("title")
beat(4.4); mark("title_end")
# ================================================================ SCENE 3: HULL AWAY, PRE-MATCH
mark("s3")
beat(3.75); mark("inserts")                            # stadium exterior: crowd building, the away coach pulls in
# fast documentary inserts, cut on the pre-match pulse (80 bpm: one beat = 0.75 s)
BEAT = 0.75
for name, n in (("ins_boots", 1), ("ins_shirts", 1), ("ins_tape", 1), ("ins_gloves", 1), ("ins_walk", 2),
                ("ins_captain", 2), ("ins_laces", 1), ("ins_board", 2)):
    mark(name); beat(BEAT * n)
mark("dressing")                                       # the dressing room wide: Carrick centre, players seated
beat(1.5)
say("ck_newly_promoted")                               # "Newly promoted team. Crowd'll be up for it. Do the basics."
say("ck_set_pieces", 0.55)                             # turns to the tactics board: "And most importantly... SET PIECES"
say("mg_set_pieces", 0.45)                             # quick close-up Maguire
say("ck_right3", 0.5)
beat(0.45); mark("s4")                                 # smash cut to the pitch
# ================================================================ SCENE 4: HULL MATCH
beat(2.3); mark("crowd")                               # broadcast wide: kick-off; then the home end
beat(1.2); mark("corner1")                             # the corner: in, not cleared, in
beat(3.6); mark("goal1_card")
beat(1.3); mark("ck_still")                            # Carrick: no reaction. Stillness.
beat(2.7); mark("corner2")                             # later: another dead ball. Chaos.
beat(4.0); mark("goal2_card")
beat(1.4); mark("bruno_looks")                         # Bruno looks toward Maguire...
beat(2.1); mark("maguire_turns")                       # ...Maguire slowly turns away
beat(2.9); mark("whistle")                             # full time
beat(0.9); mark("end")
TOTAL = T[0]

if __name__ == "__main__":
    json.dump(dict(events=EV, marks=MARK, total=TOTAL), open("build/timeline.json", "w"), indent=1)
    print("total %.1f s, %d lines" % (TOTAL, len(EV)))
    for k in ["s1", "board_wide", "music_cut", "chime", "s2", "black", "title", "s3", "dressing", "s4", "end"]:
        print(f"{k:12s} {MARK[k]:7.2f}")

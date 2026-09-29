"""Every recorded line used in scenes 1-4, cut word-exact from the raw voice clips.

The dialogue is locked: each line below is the script's line, taken from the actor's clip at the aligned word
boundaries (phones.json). Nothing is re-ordered inside a line. Cuts are snapped to the quietest point in the gap
next to the first / last word so no breath or neighbouring word leaks in.

Output: build/lines/<id>.wav (48 kHz mono) and build/lines.json {id: {speaker, clip, s, e, dur, text, phones}}
with phone times relative to the start of the cut (for the lip-sync)."""
import json, os, re, numpy as np, librosa, soundfile as sf

RAW = "audio_raw/show TV/"
CLIP = dict(jason1="jason/Clony-AI-jOUZbRL3oERxwWzo.mp3", jason2="jason/Clony-AI-rkUcZyntNsdrtWiq.mp3",
            ck1="Carrick/Clony-AI-MbfWqpLIZh9ThTuk.mp3", ck2="Carrick/Clony-AI-FigW3R4wGa7AVJWL.mp3",
            ck3="Carrick/Clony-AI-nCbSTDErPKHckMCM.mp3", omar="omar/Clony-AI-gpqmga8px6et6YNx.mp3",
            jim="jim/Clony-AI-N1Fxua8QKhHIuO2y.mp3", joel="j glazer/Clony-AI-ecyktuuXcVQCHNGa.mp3",
            avram="a glazer/Clony-AI-VGllzn0mfCmq0W7T.mp3", maguire="harry m/Clony-AI-Kzk4F3tsMBLpnbPz.mp3")
SPK = dict(jason1="jason", jason2="jason", ck1="carrick", ck2="carrick", ck3="carrick", omar="omar", jim="jim",
           joel="joel", avram="avram", maguire="maguire")

# (id, clip, words, occurrence)  - in script order
LINES = [
    # ---- scene 1: boardroom ----
    ("js_new_season", "jason1", "right michael new season new chapter we've got a very clear plan", 1),
    ("ck_whats_plan", "ck1", "what's the plan", 1),
    ("js_one_second", "jason1", "one second", 1),
    ("js_well", "jason1", "well first and foremost clarity", 1),
    ("js_alignment", "jason1", "alignment", 1),
    ("js_sustain", "jason1", "sustainability", 1),
    ("js_agility", "jason1", "agility", 1),
    ("js_yeah", "jason1", "yeah", 1),
    ("ck_right", "ck1", "right", 1),
    ("ck_yep", "ck1", "yep", 1),
    ("ck_okay", "ck1", "okay", 1),
    ("ck_jason", "ck1", "jason", 1),
    ("ck_who_signing", "ck1", "who are we signing", 1),
    ("om_invested", "omar", "michael we've invested significantly", 1),
    ("ck_i_know", "ck1", "i know", 1),
    ("ck_just_thinking", "ck1", "i'm just thinking", 1),
    ("ck_another_striker", "ck1", "another striker", 1),
    ("js_options", "jason1", "we've got options", 1),
    ("ck_no", "ck1", "no", 1),
    ("jr_no1", "jim", "no", 1),
    ("ck_benjamins_injured", "ck1", "benjamin's injured", 1),
    ("ck_hes_injured", "ck1", "he's injured", 1),
    ("ck_left_back", "ck1", "left back", 1),
    ("jr_no2", "jim", "no", 2),
    ("ck_centre_back", "ck1", "centre back", 1),
    ("ck_another_forward", "ck1", "another forward", 1),
    ("jr_already_asked", "jim", "you already asked that", 1),
    ("ck_goalkeeper", "ck1", "goalkeeper", 1),
    ("jr_got_one", "jim", "we've got one", 1),
    ("ck_fair_enough", "ck1", "fair enough", 1),
    ("js_one_of_options", "jason1", "that's one of the options", 1),
    ("ck_how_much", "ck1", "how much", 1),
    ("js_at_moment", "jason1", "at the moment", 1),
    ("js_a_lot", "jason1", "a lot", 1),
    ("ck_how_much_lot", "ck2", "how much is a lot", 1),
    ("js_enough", "jason2", "enough that we're not buying a striker", 1),
    ("ck_right2", "ck2", "right", 1),
    ("ck_so", "ck2", "so", 1),
    ("ck_sell_to_buy_q", "ck2", "sell to buy", 1),
    ("js_long_term", "jason2", "long term sustainability", 1),
    ("om_describe", "omar", "i would describe it as responsive squad optimization", 1),
    ("ck_sell_to_buy", "ck2", "sell to buy", 2),
    ("ck_objectives", "ck2", "and the objectives", 1),
    ("ck_anything_else", "ck2", "anything else", 1),
    ("ck_everything_i_need", "ck2", "and i've got everything i need", 1),
    ("jr_dont_complain", "jim", "don't complain about the squad", 1),
    ("ck_brilliant", "ck2", "brilliant", 1),
    ("ck_good_meeting", "ck2", "good meeting", 1),
    ("ck_positive", "ck2", "positive", 1),
    ("ck_good_meeting2", "ck2", "good meeting", 2),
    ("ck_where_money", "ck2", "so where's the money actually going", 1),
    ("om_cash_flow", "omar", "cash flow", 1),
    ("om_infrastructure", "omar", "infrastructure", 1),
    ("jr_debt", "jim", "debt", 1),
    ("ck_glazer_dividends", "ck2", "glazer dividends", 1),
    ("om_technically", "omar", "technically there weren't any dividends paid this year", 1),
    ("jr_funny", "jim", "funny you should mention them", 1),
    # ---- scene 2: the Glazers call ----
    ("om_morning_joel", "omar", "morning joel", 1),
    ("jg_hello", "joel", "hello everybody", 1),
    ("jg_hear_us", "joel", "can you hear us", 1),
    ("jg_michael", "joel", "michael", 1),
    ("jg_good_luck", "joel", "good luck this season", 1),
    ("av_michael_good_luck", "avram", "michael good luck this season", 1),
    ("jg_excited", "joel", "we're all really excited", 1),
    ("jg_big_season", "joel", "big season", 1),
    ("av_need_to_run", "avram", "need to run", 1),
    ("jg_go_united", "joel", "go united", 1),
    ("jr_unfortunately", "jim", "unfortunately", 1),
    ("ck_cheers", "ck2", "cheers", 1),
    ("ck_brilliant_yep", "ck3", "brilliant yep", 1),
    ("ck_sigh_good_input", "ck3", "good input", 1),        # the sigh before it is kept (see PRE)
    ("jr_right", "jim", "right", 1),
    ("jr_hull", "jim", "hull", 1),
    ("jr_dont_lose", "jim", "don't lose", 1),
    # ---- scene 3: Hull pre-match ----
    ("ck_newly_promoted", "ck3", "newly promoted team crowd will be up for it do the basics", 1),
    ("ck_set_pieces", "ck3", "and most importantly set pieces", 1),
    ("mg_set_pieces", "maguire", "set pieces got it", 1),
    ("ck_right3", "ck3", "right", 1),
]
# extra audio kept before the first word (s): the sigh before "Good input"
PRE = {"ck_sigh_good_input": 1.30}
# lines whose cut must end before a word that follows with no pause (the aligner's boundary is used, not a gap)
SR = 48000

def words_of(t):
    return re.sub(r"[^a-z' ]", " ", t.lower()).split()

def find(words, seq, occ):
    n, k = len(seq), 0
    for i in range(len(words) - n + 1):
        if [w["w"] for w in words[i:i + n]] == seq:
            k += 1
            if k == occ: return i, i + n - 1
    raise KeyError(" ".join(seq))

def quiet_point(y, sr, a, b):
    """time of the lowest-energy 20 ms window between a and b (seconds)"""
    if b - a < 0.03: return (a + b) / 2
    i0, i1 = int(a * sr), int(b * sr)
    seg = y[i0:i1] ** 2
    w = int(0.02 * sr)
    if len(seg) <= w: return (a + b) / 2
    e = np.convolve(seg, np.ones(w) / w, mode="valid")
    return (i0 + int(np.argmin(e)) + w // 2) / sr

def main():
    ph = json.load(open("phones.json"))
    os.makedirs("build/lines", exist_ok=True)
    out = {}
    cache = {}
    for lid, clip, text, occ in LINES:
        key = CLIP[clip]
        if key not in cache: cache[key] = librosa.load(RAW + key, sr=SR, mono=True)[0]
        y = cache[key]
        W = ph[key]["words"]; P = ph[key]["phones"]
        i, j = find(W, words_of(text), occ)
        s, e = W[i]["s"], W[j]["e"]
        prev_e = W[i - 1]["e"] if i > 0 else 0.0
        next_s = W[j + 1]["s"] if j + 1 < len(W) else len(y) / SR
        # start: quietest point in the gap before (at most 0.25 s before the word); end: same after
        s0 = s - PRE.get(lid, 0.0)
        cs = quiet_point(y, SR, max(prev_e, s0 - 0.25), s0) if s0 - prev_e > 0.04 else s0
        ce = quiet_point(y, SR, e, min(next_s, e + 0.35)) if next_s - e > 0.04 else e
        a, b = int(cs * SR), int(ce * SR)
        seg = y[a:b].copy()
        f = int(0.008 * SR)
        seg[:f] *= np.linspace(0, 1, f); seg[-f:] *= np.linspace(1, 0, f)
        sf.write(f"build/lines/{lid}.wav", seg.astype(np.float32), SR)
        phones = [dict(p=p["p"], s=round(p["s"] - cs, 3), e=round(p["e"] - cs, 3)) for p in P if i <= p["w"] <= j]
        words = [dict(w=w["w"], s=round(w["s"] - cs, 3), e=round(w["e"] - cs, 3)) for w in W[i:j + 1]]
        out[lid] = dict(speaker=SPK[clip], clip=key, s=round(cs, 3), e=round(ce, 3), dur=round(ce - cs, 3),
                        text=text, words=words, phones=phones)
        print(f"{lid:22s} {cs:6.2f}-{ce:6.2f} ({ce - cs:4.2f}s) {text}")
    json.dump(out, open("build/lines.json", "w"), indent=1)

if __name__ == "__main__":
    main()

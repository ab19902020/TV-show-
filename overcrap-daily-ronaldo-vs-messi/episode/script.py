"""The Overcrap Daily - "Ronaldo vs Messi": the dialogue.

Each character's lines are numbered on their own (MG_nn Mark Goldbridge,
WR_nn Wayne Rooney, RK_nn Roy Keane, RF_nn Rio Ferdinand), matching the voice
files in episode/audio/<ID>.mp3 (cut from the supplied takes in episode/raw/
by tools/ep/split_voice.py). LINES holds the words as recorded, DELIVERY the
production pack's emotion tag for each, ORDER the conversation with its stage
beats ('@rio_enters', ...).
"""

LINES = {
    # ---------------------------------------------------------------- Mark Goldbridge
    'MG_01': "Messi and Ronaldo right now are like two blokes leaving the same wedding. Messi's gone at half eleven, "
             "hugged the bride's nan, thanked the parents, ordered an Uber and everyone's waving him off.",
    'MG_02': "Ronaldo's still there at four in the morning, shirt unbuttoned, arguing with the DJ because he's stopped "
             "playing his song, telling the best man the wedding wouldn't have happened without him.",
    'MG_03': "That's not the point, Wayne.",
    'MG_04': "One's left like a national treasure. The other's thirty seconds from being removed by a bloke called "
             "Darren in a high vis jacket.",
    'MG_05': "Can we stop scouting the imaginary bouncer?",
    'MG_06': "Messi gets this huge emotional goodbye. Ronaldo falls out with Portugal and suddenly it's a national "
             "emergency.",
    'MG_07': "Exactly.",
    'MG_08': "That's the thing with Ronaldo. He doesn't get dropped. Portugal goes to DEFCON one.",
    'MG_09': "Fine, but somebody has to be able to say, Cristiano, you're on the bench, without calling in the army.",
    'MG_10': "Of course you bloody would.",
    'MG_11': "Then Messi gets what looks like a state funeral while he's still alive.",
    'MG_12': "Because he's leaving!",
    'MG_13': "Roy, could you allow one emotion into the programme?",
    'MG_14': "Oh, here we go.",
    'MG_15': "You're still not.",
    'MG_16': "And your Ronaldo alarm went off.",
    'MG_17': "Nobody said he wasn't.",
    'MG_18': "Rio, all I said was the manager has to be allowed to",
    'MG_19': "But",
    'MG_20': "Rio",
    'MG_21': "Oh, for God's sake.",
    'MG_22': "I am not a Forest fan.",
    'MG_23': "That doesn't make me a Forest fan!",
    'MG_24': "Yes, Rio, we know who Ronaldo is!",
    'MG_25': "You'd listen if Cristiano told you the moon was made of ham.",
    'MG_26': "Wayne.",
    'MG_27': "Why are we discussing lunar meat?",
    'MG_28': "Simple question. Could Ronaldo ever be wrong?",
    'MG_29': "Thank you.",
    'MG_30': "Oh, piss off.",
    'MG_31': "So Messi gets the perfect goodbye, Ronaldo gets chaos, and apparently I support Nottingham Forest.",
    'MG_32': "Rio.",
    'MG_33': "We're done.",
    'MG_34': "Goodnight.",
    # ---------------------------------------------------------------- Wayne Rooney
    'WR_01': "What song's he asking for?",
    'WR_02': "I reckon Darren struggles.",
    'WR_03': "If Ronaldo thinks he's been promised something, he's going to be annoyed.",
    'WR_04': "He's always wanted to play every minute.",
    'WR_05': "I'd let someone else tell him.",
    'WR_06': "You tell him.",
    'WR_07': "Fair.",
    'WR_08': "Why were you outside?",
    'WR_09': "What kind of ham?",
    'WR_10': "What happened to Darren?",
    # ---------------------------------------------------------------- Roy Keane
    'RK_01': "It probably is if he's been arguing for four hours.",
    'RK_02': "Depends on Darren.",
    'RK_03': "The manager picks the team.",
    'RK_04': "Be annoyed. Get on with it.",
    'RK_05': "That mentality made him great.",
    'RK_06': "Coward.",
    'RK_07': "I would.",
    'RK_08': "Why are people crying?",
    'RK_09': "They'll see him again.",
    'RK_10': "No.",
    'RK_11': "What tone?",
    'RK_12': "You're very defensive.",
    'RK_13': "He walked into that.",
    'RK_14': "Still trying to get Ronaldo out the wedding.",
    # ---------------------------------------------------------------- Rio Ferdinand
    'RF_01': "Whoa, whoa, whoa. Hold on.",
    'RF_02': "I've been listening outside.",
    'RF_03': "I wasn't booked.",
    'RF_04': "I heard Cristiano's name.",
    'RF_05': "You lot are talking about one of the greatest players ever.",
    'RF_06': "I heard the tone.",
    'RF_07': "The tone.",
    'RF_08': "Mark, hold on.",
    'RF_09': "Hold on.",
    'RF_10': "Shut up. You're a Forest fan anyway.",
    'RF_11': "You're from Nottingham.",
    'RF_12': "Exactly what a Forest fan would say.",
    'RF_13': "Cristiano's won everything. Champions Leagues. Ballon d'Ors. Records. Goals. Standards.",
    'RF_14': "If Cristiano tells me he should be playing, I'm listening.",
    'RF_15': "I'd check.",
    'RF_16': "Iberico.",
    'RF_17': "Of course.",
    'RF_18': "Just not about football.",
    'RF_19': "Finally, some facts.",
    'RF_20': "Forest.",
    'RF_21': "He's not getting Cristiano out.",
}

# Rooney's '[laughs]' after 'OH, FOR GOD'S SAKE' was not in his take: it is played as a silent
# laugh on screen ('@rooney_laughs').

# The production pack's delivery tags (and CAPS where the pack shouts).
DELIVERY = {
    'MG_01': '[animated]', 'MG_02': '[building]', 'MG_03': '[annoyed]', 'MG_04': '[animated]', 'MG_05': '[frustrated]',
    'MG_06': '[serious]', 'MG_07': '[agreeing]', 'MG_08': '[animated] DEFCON', 'MG_09': '[emphatic]', 'MG_10': '[dry]',
    'MG_11': '[animated]', 'MG_12': '[frustrated]', 'MG_13': '[exasperated]', 'MG_14': '[sigh]', 'MG_15': '[dry]',
    'MG_16': '[teasing]', 'MG_17': '[defensive]', 'MG_18': '[trying to interrupt]', 'MG_19': '[interrupting]',
    'MG_20': '[frustrated]', 'MG_21': '[angry] GOD\'S SAKE', 'MG_22': '[shouting] NOT FOREST', 'MG_23': '[frustrated]',
    'MG_24': '[exasperated]', 'MG_25': '[sarcastic]', 'MG_26': '[shouting] WAYNE', 'MG_27': '[baffled]',
    'MG_28': '[calm, challenging]', 'MG_29': '[relieved]', 'MG_30': '[immediately annoyed]', 'MG_31': '[defeated]',
    'MG_32': '[warning] RIO', 'MG_33': '[frustrated]', 'MG_34': '[shouting] GOODNIGHT',
    'WR_01': '[curious]', 'WR_02': '[thoughtful]', 'WR_03': '[serious]', 'WR_04': '[matter-of-fact]', 'WR_05': '[dry]',
    'WR_06': '[challenging]', 'WR_07': '[agreeing]', 'WR_08': '[curious]', 'WR_09': '[genuinely curious]',
    'WR_10': '[innocent]',
    'RK_01': '[dry]', 'RK_02': '[serious]', 'RK_03': '[firm]', 'RK_04': '[blunt]', 'RK_05': '[serious]', 'RK_06': '[dry]',
    'RK_07': '[firm]', 'RK_08': '[confused]', 'RK_09': '[matter-of-fact]', 'RK_10': '[flat]', 'RK_11': '[suspicious]',
    'RK_12': '[dry]', 'RK_13': '[amused]', 'RK_14': '[deadpan]',
    'RF_01': '[interrupting, animated]', 'RF_02': '[animated]', 'RF_03': '[matter-of-fact]', 'RF_04': '[serious]',
    'RF_05': '[passionate] EVER', 'RF_06': '[accusing]', 'RF_07': '[serious]', 'RF_08': '[interrupting]', 'RF_09': '[firm]',
    'RF_10': '[annoyed]', 'RF_11': '[matter-of-fact]', 'RF_12': '[teasing]', 'RF_13': '[passionate]', 'RF_14': '[serious]',
    'RF_15': '[completely serious]', 'RF_16': '[thinking]', 'RF_17': '[calm]', 'RF_18': '[confident]', 'RF_19': '[smug]',
    'RF_20': '[teasing]', 'RF_21': '[firm]',
}


def tag(lid):
    t = DELIVERY.get(lid, '')
    return t[1:t.index(']')] if t.startswith('[') else ''


def emphasised(lid):
    """Words the pack writes in CAPS (lower-cased, as in the alignment)."""
    import re
    body = re.sub(r'^\[[^\]]*\]', ' ', DELIVERY.get(lid, ''))
    return [w.lower() for w in re.findall(r"[A-Za-z']+", body) if len(w) > 1 and w.isupper()]


SPEAKER = {'MG': 'mark', 'WR': 'rooney', 'RK': 'roy', 'RF': 'rio'}

# The voice takes in episode/raw/ and the lines each holds, in order (for split_voice.py).
TAKES = {
    'mark_1.mp3': ['MG_01', 'MG_02', 'MG_03', 'MG_04', 'MG_05', 'MG_06'],
    'mark_2.mp3': ['MG_07', 'MG_08', 'MG_09', 'MG_10', 'MG_11', 'MG_12', 'MG_13', 'MG_14', 'MG_15', 'MG_16', 'MG_17',
                   'MG_18', 'MG_19', 'MG_20', 'MG_21', 'MG_22'],
    'mark_3.mp3': ['MG_23', 'MG_24', 'MG_25', 'MG_26', 'MG_27', 'MG_28', 'MG_29', 'MG_30', 'MG_31', 'MG_32', 'MG_33',
                   'MG_34'],
    'rooney.mp3': ['WR_%02d' % i for i in range(1, 11)],
    'roy.mp3': ['RK_%02d' % i for i in range(1, 15)],
    'rio.mp3': ['RF_%02d' % i for i in range(1, 22)],
}

# Where the takes that run lines close together are cut (seconds; the quiet between lines,
# measured on the waveform). Takes not listed are cut by forced alignment.
CUTS = {
    'mark_2.mp3': [0.98, 6.2, 12.18, 13.82, 18.06, 19.87, 23.25, 25.24, 26.66, 29.02, 31.04, 34.27, 34.72, 35.5, 37.05],
    'rooney.mp3': [1.83, 3.62, 7.03, 8.98, 10.56, 11.59, 12.57, 14.6, 16.16],
    'rio.mp3': [1.45, 3.25, 4.75, 6.8, 10.28, 11.92, 13.3, 14.64, 15.64, 18.22, 19.62, 22.15, 29.12, 32.47, 33.84, 35.22,
                36.62, 38.53, 40.62, 41.9],
}

# The conversation, in order.
ORDER = [
    # cold open - Mark already mid-rant
    'MG_01', 'MG_02', 'WR_01', 'MG_03', 'RK_01', 'MG_04', 'WR_02', 'RK_02', 'MG_05',
    # Ronaldo / Portugal
    'MG_06', 'RK_03', 'MG_07', 'WR_03', 'RK_04', 'MG_08', 'WR_04', 'RK_05', 'MG_09', 'WR_05', 'RK_06', 'WR_06', 'RK_07',
    'MG_10',
    # Messi send-off
    'MG_11', 'RK_08', 'MG_12', 'RK_09', 'MG_13', 'RK_10', 'WR_07',
    # Rio enters
    '@rio_enters',
    'RF_01', 'MG_14', 'RF_02', 'WR_08', 'RF_03', 'MG_15', 'RF_04', 'MG_16', 'RF_05', 'MG_17', 'RF_06', 'RK_11', 'RF_07',
    # Forest
    'MG_18', 'RF_08', 'MG_19', 'RF_09', 'MG_20', 'RF_10', '@forest_beat', 'MG_21', '@rooney_laughs', 'MG_22', 'RF_11', 'MG_23',
    'RK_12', 'RF_12',
    # Ham
    'RF_13', 'MG_24', 'RF_14', 'MG_25', 'RF_15', 'WR_09', 'MG_26', 'RF_16', '@rooney_satisfied', 'MG_27',
    # Ending
    'MG_28', 'RF_17', 'MG_29', 'RF_18', 'MG_30', 'RK_13', 'MG_31', 'RF_19', 'MG_32', 'RF_20', 'MG_33', 'WR_10', 'RK_14',
    'RF_21', 'MG_34',
    '@end',
]

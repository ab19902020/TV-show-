# The Undercard — Hearn v White

Original fictional satire from the *Hearn v White* production pack (`pack/`): Eddie bans Dana, Dana gets in by
laundry trolley and tumbles out at Tyson Fury's feet, the two promoters negotiate themselves into a fight, and the
fight is a draw. 1920 x 1080 master, 30 fps, 3 min 53 s. The preview is rendered at 1280 x 720; the 4K final waits
for approval of the preview.

## What's on screen, by time

| Time | Scene | Set | What happens |
|---|---|---|---|
| 0:00 | Title | — | THE UNDERCARD / HEARN v WHITE |
| 0:03 | 1. The ban | press area | Eddie beside a BANNED board with Dana's face crossed out (drawn in code); points at it on "Not a bald American"; security, arms crossed; the stop hand on "No ticket..." |
| 0:24 | | loading bay | Dana's rant; the laundry trolley rolls past behind him; he watches it, then looks into the lens (12 frames) and says it to us; smash cut: he climbs in, the towels drop on top |
| 0:40 | 2. The angriest towel | corridor | Low tracking shot: the attendant pushes the trolley to security's raised hand; the towels twitch on "Premium towels"; she shuts the lid; he waves it through; the lid lifts on Dana's dome; the cable protector; a freeze on his eyes; three tumble drawings through the air; he lands at Fury's feet |
| 1:01 | 3. Fury finds a promoter | corridor | Dana kneeling under a towel; Fury, then Joshua (eyeline down); Eddie walks in, stops, a four-frame eye dart (bin, Dana, security) |
| 1:28 | 4. Negotiations | corridor | Eddie takes the towel off with his fingertips and drops it; "Fine." and both surprised; the list with a gesture per item; Fury and Joshua watching |
| 1:55 | | dressing room | Eddie slumped in his kit; Dana shadowboxes too hard, then stops to catch his breath, looking at his glove |
| 1:59 | 5. Special announcement | arena | A two-second sting and crowd swell; the announcer in the ring; Fury and Joshua ringside; Eddie smiles with panicking brows; Dana raises his gloves and the attendant takes the stray towel off his shoulder; the referee's rules |
| 2:42 | 6. The fight | ring | The bell; a silent face-off (a cough); Fury's "It's not a podcast"; Eddie's long jab misses as Dana leans back too far and windmills; Dana's short jab lands on Eddie's guard (the glove squeak; the fight music stops there); jab and duck; both overcommit and miss; the clinch, heads together; "Break!", they wobble apart and lean back in; the bell; both raise their arms; the referee scratches his head at a blank card |
| 3:23 | 7. Decision and callback | ring, ringside | "a draw"; the attendant pushes the trolley in; Dana glances at Eddie, Eddie points, Dana hops into the bin; rolled off still bickering; Fury and Joshua staring; the last wheel squeak; black |

## Voices

The delivered voice-overs, one file per character (`voiceovers/01-...08-`): every line is found in its recording by
Whisper, force-aligned word by word and cut (`film/lines.py`). The announcer's take was delivered twice (two
identical uploads); one copy is kept. **One line is a stand-in:** Dana's L007, "I've entered venues in worse
ways." His recording runs "I've entered... premium towels" (9.3-10.8 s); the words "venues in worse ways" are not
in it, so L007 is spoken by Kokoro (`voiceovers/L007-dana-stand-in.wav`, `tools/stand_in_voices.py`) until it is
recorded. Drop the recording into `voiceovers/` ahead of the stand-in in `RECORDINGS` and re-run `lines`: the film
retimes itself. The leftover "I've entered" in that stretch bled into the cut of L010 ("Premium towels"), so Dana's
lines are cut from `voiceovers/01-dana-white-edit.wav`: his take with those 0.5 s faded to silence
(`tools/dana_take_edit.py`). The delivered mp3 is kept as it came.

Whisper re-hears every line in the finished mix (`check`): 55 of 59 match the script exactly. The other four are
"banned" heard as "band" (as in the take itself), "security is" for "security's", a lone "Fine." heard as "Fun",
and "Premium towels" before the fix above.

## How it is made

The engine is `ab19902020/AnimnationStuido-` (the film engine, `studio/film`), unchanged except one line in
`tools/index_library.py` (the boxing sets folder). The pack's sheets are filed in the library as eight characters
(`library/characters/<id>/`: `film.yaml` lists every drawing cut whole from the sheets, with hand-set face marks
where detection could not see the face, and `plain: true` where a face is hidden or too small to act), seven sets
(`library/backgrounds/boxing/`) and twelve props (`library/props/hearn-white/`). The sheets are kept as
delivered, and a `-clean` copy of each (alpha noise and stray strokes such as motion accents removed) is what the
film cuts from.

| File | What it does |
|---|---|
| `film/lines.py` | which recording each line comes from |
| `film/timeline.py` | the dialogue edit: every line in order with the beats the script asks for, as named marks |
| `film/direction.py` | 72 shots: each a camera in one of the seven sets with the people and props of that moment, every move keyed to the marks; the perspective of each set (`PPC`: plate px per cm by floor height), the arena's near rope and posts in front of the people (`OCCL`) |
| `film/actors.py` | the people and props in a set at true scale: poses on a beat, the eight-drawing walk cycle, tumbles and leans rotating a whole drawing about its feet, a lift, a clip at the trolley's rim, props held in a hand; faces through the engine's lip sync, blinks, eyes and brows |
| `film/things.py` | drawn in code: the BANNED board, the trolley lid on its hinge, the near ring ropes, contact shadows |
| `film/perf.py` | the acting: whom each line is said to, its delivery, the stressed words, the looks and reactions |
| `film/sound.py` | the mix: voices (the bin lines muffled), each set's room, crowd dipping under every line, foley on the marks, the bell, the sting, fight music that stops at the glove tap |
| `tools/stand_in_voices.py` | Kokoro stand-in takes for lines with no recording |

Sizes: the pack's sheets draw the characters at different scales (the walk sheets about 1.3x the casual sheets,
the laundry sheet 1.15x), corrected in `actors.SHEET`; the peek over the rim is a close-up head (`actors.DRAWING`).
Every person stands on the floor at the size their height and their depth in the set give.

## Render

From the engine's root (dependencies: `pip install -r requirements.txt`, ffmpeg, libegl1; `tools/fetch_models.sh
whisper` for `lines` and `check`):

```sh
python3 -m studio.film the-undercard lines        # cut every line from the recordings
python3 -m studio.film the-undercard sound        # build/episode_audio.wav (-16 LUFS)
EP_RES=960x540 python3 -m studio.film the-undercard still 7.2 60.2 183.9   # spot stills
EP_RES=1280x720 FILM_MEM_GB=12 python3 -m studio.film the-undercard render --jobs 4 --chunks 24 --resume
python3 -m studio.film the-undercard sheet        # build/contact.jpg
```

The 4K final (after approval): `EP_RES=3840x2160 FILM_MEM_GB=12 FILM_CRF=18 python3 -m studio.film the-undercard
render --jobs 2 --chunks 48` (move the 720p `build/part*` away first: `--resume` matches frame ranges, not
resolution).

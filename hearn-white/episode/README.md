# The Undercard — Hearn v White

Original fictional satire from the *Hearn v White* production pack (`pack/`): Eddie bans Dana, Dana gets in by
laundry trolley and tumbles out at Tyson Fury's feet, the two promoters negotiate themselves into a fight, and the
fight is a draw. 1920 x 1080 master, 30 fps, 3 min 38 s, 81 shots. The preview is rendered at 1280 x 720; the 4K
final waits for approval of the preview.

## What's on screen, by time

| Time | Scene | Set | What happens |
|---|---|---|---|
| 0:00 | Title | — | THE UNDERCARD / HEARN v WHITE |
| 0:02 | 1. The ban | press area | Eddie beside a BANNED board with Dana's face crossed out (drawn in code); points at it on "Not a bald American"; security, arms crossed; the stop hand on "No ticket..." |
| 0:22 | | loading bay | Dana's rant (wide, then a medium shot pushing in); the laundry trolley crosses well behind him; he watches it, then looks into the lens and says "I've entered venues in worse ways" to us; smash cut: his shoe disappears under the towels |
| 0:36 | 2. The angriest towel | corridor | Low tracking shot: the attendant pushes the trolley to security's raised hand at the checkpoint; the towels twitch on "Premium towels"; she shuts the lid; he steps aside and waves it through. Inside, a close shot tracking with the bin: Dana's dome rises out of the towels and lifts the lid, his fingers on the rim; the cable protector stops the bin dead; a freeze on his eyes over the rim; he is thrown out over the front in an arc (three tumble drawings, towels flying) and lands face down at Fury's feet, a towel landing on his head |
| 0:54 | 3. Fury finds a promoter | corridor | Dana kneeling under a towel; Fury points down at him; Joshua walks in and looks down; Eddie walks in, stops, a four-frame eye dart (bin, Dana, security) |
| 1:20 | 4. Negotiations | corridor | Eddie walks over to Dana, takes the towel off with his fingertips and drops it; "Fine." and both surprised; the list with a gesture per item; Fury and Joshua watching from up the corridor |
| 1:45 | | the red corner's dressing room | Eddie in his suit, reluctant; a puff of smoke and he's in his kit, slumped |
| 1:47 | | the blue corner's dressing room | Dana alone, shadowboxing far too hard, then bent double catching his breath |
| 1:49 | 5. Special announcement | arena | A sting and crowd swell with air horns and press flashes; the announcer in the ring; Fury and Joshua ringside; Eddie smiles with panicking brows (a mixed cheer, a laugh); Dana raises his gloves (the bigger cheer) and the attendant takes the stray towel; the referee's rules |
| 2:29 | 6. The fight | ring | The bell (the camera shaking with it); a silent face-off, both bouncing, circling, one cough; Fury's "It's not a podcast". **Exchange 1:** Eddie winds up a long jab; Dana leans back far too far and windmills, the crowd laughs. **2:** Dana's little jab taps Eddie's guard: the squeak, a snap zoom, the fight music stops dead, Eddie's outrage ("You actually hit me!"; Dana drops his guard to answer). **3:** Eddie's flurry, jab jab jab, Dana bobbing under each. **4:** Dana's counter to the body lands: impact burst, flying sweat, a camera shake, Eddie knocked back and stumbling, the crowd roars. **5:** Eddie lunges with a wild cross, Dana ducks, Eddie's momentum spins him round. **6:** slow motion: both back off and throw enormous haymakers from much too far away, both miss, both spin; the whole room pitched down, then it snaps back. Fury and Joshua wince. **7:** exhausted, they stagger into a clinch, heads together and both faces in shot; "Break!" (the referee steps in); they wobble apart and lean back in; the bell; both raise their arms; the referee scratches his head at a blank card |
| 3:11 | 7. Decision and callback | ring, ringside | "a draw" (Dana bent double, spent); the attendant pushes the trolley in; Dana glances at Eddie, Eddie points, Dana steps round to the side of the bin, crouches, springs over the rim and drops in out of sight (the towels puff up, the lid slams); rolled off still bickering; Fury and Joshua staring; the last wheel squeak; black |

## Voices

The delivered voice-overs, one file per character (`voiceovers/01-...08-`): every line is found in its recording by
Whisper, force-aligned word by word and cut (`film/lines.py`). Every line is a real recording; there are no
stand-ins.

- **Dana** came as two takes (`01-dana-white-take1.mp3`, `01-dana-white-take2.mp3`). Take 1 has every line,
  "I've entered venues in worse ways" (L007) included. Two lines come from take 2, the cleaner reads:
  L030 ("It's boxing, Eddie.": take 1 says it twice) and L058 ("I want a bigger bin for the rematch.": take 1's
  "bin" is heard as "bend"). `tools/dana_picks.py` cuts each
  of them out of take 2 (`01-dana-white-take2-L030.wav`, `-L058.wav`) so the matcher finds them there first. The
  mp3s are kept as delivered.
- **Tyson Fury** and **the laundry attendant**: the new recordings replace the earlier ones.
- **The others** (Eddie, the announcer, security, the referee, Joshua) are unchanged. The announcer's take was
  delivered twice (two identical uploads); one copy is kept.

The edit is cut tight: lines follow each other a few frames apart (about 0.12-0.2 s), the jokes keep the pause
they need and no more.

Whisper re-hears every line in the finished mix (`check`): CHECK_RESULT

## How it is made

The engine is `ab19902020/AnimnationStuido-` (the film engine, `studio/film`), unchanged except one line in
`tools/index_library.py` (the boxing sets folder). The pack's sheets are filed in the library as eight characters
(`library/characters/<id>/`), seven sets (`library/backgrounds/boxing/`) and twelve props
(`library/props/hearn-white/`). The sheets are kept as delivered.

**Cut-outs.** The pack's sheets are packed tight, so a drawing's box also holds slivers of its neighbours (a hand,
a shoe, a foot from the row below) and motion accents. `tools/cut_drawings.py` cuts every drawing the film uses
as its own clean PNG (`reference/cuts/<sheet>/<drawing>.png`: the figure kept whole, every stray piece dropped)
and `film.yaml` points at those. Each is upscaled 4x and checked on magenta.

**Mouths (`film/mouths.py`).** The engine's lip sync stretched the drawing's own mouth with a jaw warp: through a
beard it smeared, on a turned face it opened off to the side. Now each face's drawn mouth is painted out once
(inpainted from the skin and beard round it) and a cartoon mouth is drawn on in its place for every sound: closed
for M/B/P, a wide open mouth with top teeth and tongue for "ah", a round "oh"/"oo", teeth on the lip for F/V, the
tongue up for L, ten shapes in all. Each is drawn at the face's mouth marks, tilted with the face, sized to
it, in the drawing's own ink. At rest the face is exactly as drawn. Shapes are held at least two frames, and a
one- or two-frame closure between two open shapes is filled, so the mouth never flickers. Every drawing a line is
spoken in has its eyes and mouth marked (`film.yaml` `marks`), checked and refitted with `tools/marksheet.py` and
`tools/markfit.py`. The announcer's microphone is redrawn over his mouth (`front_poly`).

**Eyes (`film/eyes.py`).** The engine moved a pupil by cutting out the dark pixels and pasting them elsewhere,
which left its rim and bits of the eye outline behind (the black specks in the eyes). Now, once per eye, the eye
white is found in the art, the drawn pupil is painted out with the white's own shading, and a clean round pupil
(the drawing's ink, the drawn pupil's size, a highlight) is drawn where the look puts it, never outside the eye
opening. Looking where the drawing looks, the eye is left exactly as drawn. Far eyes drawn as a dark sliver keep
their drawing and only blink. `tools/facesheet.py` renders every face's drawings with their looks and mouths
(`build/faces_<id>.jpg`).

**The fight (`film/fight.py`).** Each fighter's moves are written as readable moves on the edit's marks (`guard`,
`punch`, `duck`, `windmill`, `hit`, `stumble`, `spin`) that make pose, position, lean and flip keys. Every punch is
staged the way a cartoon fight reads: an anticipation (the arm drawn back, the body shifting back), a two- or
three-frame lunge into the punch drawing, a hold on the extension, the recovery to guard. Speed lines trail the
glove; the hit takes an impact star, flying sweat, a knock-back and a camera shake; big moments take a snap zoom.
Guards bounce on the balls of the feet. The fighters watch each other from the face-off to the bell.

**No head cut by the frame.** `tools/framing.py` follows every person's head through every shot, six times a
second, and corrects the shot's camera until every head on screen is whole with headroom. Heads at the side of a
shot are brought fully in or taken fully out, never left half in. The corrections are `film/framing.json`, keyed to
each shot, so an edited shot is re-fitted by running the tool again (a shot framed by hand, like the freeze on Dana's
eyes, is marked `locked` and left alone). Current result: 0 heads cut in 81 shots.
`tools/lipcheck.py` renders every speaker's face at each line's stressed words and first M/B/P
(`build/lipcheck.jpg`); every line is spoken on screen except the two from inside the bin.

**The look: people lit by the set they stand in (`film/actors.py` `light`).** Characters drawn on white sheets look
pasted onto a painted set. Each set now lights the people and props in it: the room's colour over them (cool blue
night in the loading bay, warm practicals in the corridor and the red corner's room, the arena's red and blue) and
rim light from the set's lamps catching the edges that face them (sodium orange and floodlight blue outside, red and
blue from the arena's corners, white from the rig overhead), inside the ink outline, so the ink stays ink.

**Two dressing rooms.** Eddie's is the pack's room (the red corner). Dana's is its own set, the blue corner down the
hall: the same room seen the other way round, its red lockers, wall and poster turned blue, the lamps' warm light
kept (`film/props.py`).

**The bin, rebuilt.** Inside the bin Dana is the peek drawing behind the trolley's canvas, so the bin itself hides
where his drawing ends, never a straight cut through his body; the towels sit either side of him and lift with the
lid. He is thrown out over the front on an arc and lands at Fury's feet. At the end he climbs back in the same way:
over the rim and down behind the canvas, which is the only thing that hides him.

**Mouths stay on faces.** A drawn mouth is clipped to the face it belongs to (the region inside the face's ink
outline round the mouth), so with a glove held at the chin the mouth opens behind the glove, never on it; and in
the ring the lines are said in drawings with the face clear (Dana drops his guard to answer, says "Pay-per-view"
bent double; the clinch keeps both faces in shot).

**Life.** Everyone standing breathes on their own rhythm and shifts their weight; a pose change lands with a quick
settle; the talker's head bobs with the stress of their words; the attendant's steps bob her as she pushes; the
trolley's wobbly wheel rattles it as it rolls; press flashes pop in the arena crowd.

**Sound (`film/sound.py`, `film/crowdfx.py`).** The crowd is built from real recordings (`library/audio/sfx`, CC0):
audience laughter layered from many laughs at their own pitch, timing and loudness; roars from an arena crowd surge
with "yeah" shouts on top; cheers and applause for the introductions; all in the arena's reverb. The crowd dips under
every line and reacts to every beat: air horns and a cheer as the arena opens, a mixed cheer and laugh for Eddie,
the bigger cheer for Dana, a laugh at the windmill, the spin and the double miss, a roar at the hit, silence for the
face-off (one cough). Real boxing bells, punches, whooshes on every punch, cloth and footwork on the ducks, body
falls; the slow motion pitches the whole room down and dulls it, then it snaps back.

| File | What it does |
|---|---|
| `film/lines.py` | which recording each line comes from |
| `film/timeline.py` | the dialogue edit: every line in order with the beats the script asks for, as named marks |
| `film/direction.py` | 81 shots: each a camera in one of the seven sets with the people and props of that moment, every move keyed to the marks; the perspective of each set (`PPC`), the near rope and posts in front of the people, the fight written as moves |
| `film/fight.py` | the fighters' moves and the effects they make |
| `film/actors.py` | the people and props in a set at true scale: poses on a beat, the walk cycle, tumbles and leans about the feet, lifts, clips, props in hands, the guard bounce, the camera shakes and snap zooms; faces through the engine's blinks, brows and looks, with the mouths and eyes below |
| `film/mouths.py` | the drawn cartoon mouths |
| `film/eyes.py` | the clean moving pupils |
| `film/things.py` | drawn in code: the BANNED board, the trolley lid, the near ring ropes, contact shadows, impact stars, sweat, speed lines, press flashes, the puff of smoke |
| `film/props.py` | the engine's props hook, and the blue corner's dressing room (plate E) |
| `film/perf.py` | the acting: whom each line is said to, its delivery, the stressed words, the looks and reactions, the mouth-shape smoothing |
| `film/sound.py`, `film/crowdfx.py` | the mix and the crowd |
| `film/framing.json` | the per-shot camera corrections from `tools/framing.py` |
| `tools/dana_picks.py` | the two lines taken from Dana's second take |
| `tools/stand_in_voices.py` | Kokoro stand-in takes for a line with no recording (none used now) |
| `tools/cut_drawings.py` | every drawing cut clean from its sheet |
| `tools/framing.py`, `tools/lipcheck.py` | the head-framing fit and the lip-sync sheet |
| `tools/facesheet.py`, `tools/marksheet.py`, `tools/markfit.py` | face sheets; the eye and mouth marks drawn on every drawing and refitted |

Sizes: the pack's sheets draw the characters at different scales (the walk sheets about 1.3x the casual sheets,
the laundry sheet 1.15x), corrected in `actors.SHEET`; the peek over the rim is a close-up head (`actors.DRAWING`).
Every person stands on the floor at the size their height and their depth in the set give.

## Render

From the engine's root (dependencies: `pip install -r requirements.txt`, ffmpeg, libegl1; `tools/fetch_models.sh
whisper` for `lines` and `check`):

```sh
python3 episodes/the-undercard/tools/dana_picks.py # Dana's two take-2 lines as their own files
python3 -m studio.film the-undercard lines        # cut every line from the recordings
python3 -m studio.film the-undercard sound        # build/episode_audio.wav (-16 LUFS)
FILM_EPISODE=the-undercard PYTHONPATH=episodes/the-undercard:. python3 episodes/the-undercard/tools/framing.py
EP_RES=960x540 FILM_EPISODE=the-undercard PYTHONPATH=episodes/the-undercard:. python3 episodes/the-undercard/tools/lipcheck.py
EP_RES=960x540 python3 -m studio.film the-undercard still 7.2 60.2 166.6   # spot stills
EP_RES=1280x720 FILM_MEM_GB=12 python3 -m studio.film the-undercard render --jobs 4 --chunks 24 --resume
python3 -m studio.film the-undercard check        # Whisper re-hears every line in the mix
python3 -m studio.film the-undercard sheet        # build/contact.jpg
```

The 4K final (after approval): `EP_RES=3840x2160 FILM_MEM_GB=12 FILM_CRF=18 python3 -m studio.film the-undercard
render --jobs 2 --chunks 48` (move the 720p `build/part*` away first: `--resume` matches frame ranges, not
resolution).

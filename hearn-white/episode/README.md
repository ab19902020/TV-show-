# The Undercard — Hearn v White (v5)

Original fictional satire from the *Hearn v White* production pack (`pack/`), upgraded with the v5 pack
(`pack/v5/`: the revised script, the shot and animation plan, the new art): Eddie bans Dana, Dana bribes his way in
inside a laundry bin and is delivered at Tyson Fury's feet, the two promoters bluff themselves into a fight, and
the fight is a draw that both of them immediately sell as a rematch. 1920 x 1080 master, 30 fps, 3 min 50 s,
92 shots. The preview is rendered at 1280 x 720; the 4K final waits for approval of the preview.

## What's on screen, by time

| Time | Scene | Set | What happens |
|---|---|---|---|
| 0:00 | 1. Eddie's ban | press area | Eddie presses the last strip of tape onto Dana's BANNED poster; the tape sticks to his hand, he shakes it off (it flutters to the floor); he steps back to admire it, and the series title comes up over the action. Security, arms crossed, asks the questions; Eddie's close-up on "I've banned Dana White"; the guard's deadpan blink |
| 0:19 | | loading bay | Dana studies the staff door; a shifty look, a blush (the disguise idea, abandoned); "Now I'm fucking coming" |
| 0:25 | 2. Laundry infiltration | loading bay | The attendant pushes the trolley in, step by step, her hands on the handle, the wheels turning; Dana falls in alongside; a low shot of the wheels and her feet as she brakes. The negotiation in a two-shot; "Five hundred" in his close-up; she turns on the offer. One shoe off (a hop), the other, both thrown into the bin, then Dana climbs in |
| 0:44 | | inside the bin | Dana crouched between the towels, embarrassed; the lid slides shut and the light narrows to a slit |
| 0:46 | | service hall (reverse) | The trolley stops at the guard. "What's in there?" "Towels." From inside, in the dark: "The best towels in the fucking business." She leans on the lid. The guard looks at the bin, then at her; she holds his stare; the pause; he gives way |
| 0:56 | 3. The delivery | corridor | Low, tracking with the trolley. The front wheel hits the cable ramp; her front foot braces; the towels lurch; the lid flips open; Dana's hands come up for the rim and miss; he goes over the front in one arc and lands at Fury's feet, a towel following him down, his shoes skidding on after him; Fury steps back. Fury's close-ups; Joshua walks into the eyeline. Eddie comes round the corner, stops at a shoe, finds the towel, the bin, then Dana (his close-up, held). Dana stands too fast and wobbles. The guard's defence; Eddie's profile; her hand out: Dana pays, slowly, and Eddie's face says someone else made money |
| 1:28 | 4. The challenge | corridor | "Out." Dana steps right up to him. "Fine." Silence. Eddie realises (a sweat bead), Dana realises |
| 1:37 | | corridor, in kit | Preparation: Eddie's jacket off (a puff); Dana's glove strap yanked too tight; Eddie can't work his phone in gloves and drops it; the two of them bickering in their kit while Fury and Joshua watch. Joshua: "Shall we stop this?" Fury: "And miss two promoters working for their money?" |
| 1:59 | 5. The additional contest | arena | The crowd swells into the arena; the promoters duck through the ropes, badly; the announcer's introductions, played straight; Eddie's confident smile with panicking brows; Dana raises his gloves; the attendant reaches through the ropes and takes the towel off his shoulder. In the ring, the referee's rules; "During the round, or generally?" |
| 2:31 | 6. One disastrous round | ring, red corner | **1. Ceremony:** the bell; both bounce on their toes, full of it; Dana slows first, Eddie notices and stops too; nothing happens; one cough. Fury: "It's not a fucking podcast!" **2. Probing:** Eddie's long, slow, tentative jab; Dana ducks much too deep and peers up from under his gloves ("Your jab's shit." "It's an opening offer."). **3. Indignation:** Eddie's second jab taps Dana's guard; Dana counters into the red gloves (the paired drawings: real glove contact); the chin argument; Dana's counter lands on Eddie's raised gloves: "You actually fucking hit me!" "It's a fight!" "I thought we'd do the photos first!" (he strikes a pose). **4. The ropes:** at the red corner, Dana comes forward, three steps and two punches; Eddie backpedals onto the ropes, which throw him back into Dana: a real clinch (the paired clinch drawing: Eddie taller, leaning down, Dana braced). The whispered negotiation in a tight two-shot; Dana lifts a glove an inch and Eddie dives back in; "Break!" "Don't. He's load-bearing." Joshua and Fury, each in close-up. **5. The finish:** the referee prises them apart; both load up an enormous finish, trembling; glove meets glove (the one impact graphic, a two-frame flash); they wobble, the knees go, and both sit down on the same beat; the exhausted look, held; the bell; the referee hauls them up |
| 3:30 | 7. Decision and button | ring, ringside | "After one round... a draw!" "Unfinished business. Immediate rematch." "Pay-per-view." Fury and Joshua. The promoters come down the ring steps; on the floor by the apron the bin is waiting; she slaps a fare card on it (RETURN JOURNEY £1,000, lettered in the engine); "You said five hundred!" "That was before you were pay-per-view."; Eddie, delighted (and a little impressed); Dana climbs in; the lid shuts; the wheel squeak; the end title over the departing trolley |

## Voices

Every line is a real recording except one (below). `film/lines.py` finds each line in its recording with Whisper,
force-aligns it word by word and cuts it; the order of preference is:

1. **The v5 recordings** (`voiceovers/v5/`, one file per character, named by character; `09-tyson-fury-v5.mp3` for
   Fury). These are read with little silence between lines, so each file is heard in pieces of at most 8 s split at
   its quietest moments. The announcer read both wordings of his two changed lines with a spoken note between them;
   `TAKES` names the reading used (the v5 wording: "entering by laundry delivery", "After one round... a draw!"),
   and Dana's "Your security's shit" (heard by Whisper as "you security shit") is placed the same way.
2. **Lines whose words did not change** (`REUSE`), cut from the earlier takes (`voiceovers/01-...08-`, found with
   the old script, `voiceovers/v4-script.md`): "Help me up.", "You're wearing a pillowcase.", "Fine.", "It's
   boxing, Eddie.", "Towels.", "Pay-per-view.", "Are we still fighting?", "Break!", the announcer's opening, and
   Eddie's "You actually fucking hit me!" and "Unfinished business. Immediate rematch." (the optional rewordings
   were not recorded, so the script keeps these wordings).
3. **A stand-in** for a line with no recording: only **L066, Eddie's "Don't. He's load-bearing."**, which is not
   in Eddie's v5 file. It is a synthetic voice (`voiceovers/stand-in/L066.wav`) and must be replaced before the
   final: drop a recording of the line into `voiceovers/v5/` (any file name with "eddie" in it, or append it to
   Eddie's file) and re-run `lines`.

Whisper re-hears every cut line: the misses are mishearings of short isolated clips ("Who've you added?" as
"review added", "Then no." as "and no", "Break!" as "brake"), not wrong cuts.

## How it is made

The engine is `ab19902020/AnimnationStuido-` (the film engine, `studio/film`), unchanged except one line in
`tools/index_library.py` (the boxing sets folder). The pack's sheets are filed in the library as eight characters
(`library/characters/<id>/`), ten sets (`library/backgrounds/boxing/`, three of them from the v5 pack) and twelve props
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
which left its rim and bits of the eye outline behind (the black specks in the eyes). Many of the pack's eyes are
drawn looking sideways, the pupil pressed into the corner and merged with the outline, and many have black wedges
drawn in their corners. Now, once per eye: the eye white is found in the art; the drawn pupil is found as the
round dark shape the white wraps around; everything dark inside the eye opening (the pupil and the corner wedges)
is painted out with the white's own shading, short of the outline so the outline stays; and one clean round pupil
(the drawing's ink, a highlight) is drawn where the look puts it, always inside the opening. Every animated eye
shows that one pupil all the time, so an eye never pops between the drawing and the redraw, and the two pupils of
a face are matched in size. A far eye drawn as a dark sliver past the nose keeps its drawing and only blinks.
`tools/eyesheet.py` renders every animated eye close up, at rest, looking left, right, up and down, and half shut
(`build/eyes_<n>.jpg`, 93 eyes); `tools/facesheet.py` renders whole faces with their mouths.

**The v5 art.** The acting heads (`reference/cuts/acting_heads/bust_*.png`: six each for Eddie and Dana, three
each for Fury and Joshua) are cut from their sheets with the haze dropped, and every one has its eyes and mouth
marked, so close-ups are on the big heads and still lip-sync. A bust stands where its character stands: its head
the size and in the place the full figure's head would be (`actors.bust_geom`), so a cut from a medium shot to a
close-up keeps the eyeline; the close-up is framed from the drawing itself so its cut-off bottom edge is never in
shot (`direction.bust_cam`). The paired fight reference was cut from its dark backdrop with an anime matting
model (rembg, isnet-anime) and each pair split into an Eddie layer and a Dana layer on one canvas
(`tools/cut_pairs.py`): drawn on the same point they are the drawing, and each speaks with his own face; the
clinch, a jab landing on a guard each way, and the glove clash. The attendant's eight new full-figure drawings
(steps, brace, gestures, towel) have their faces marked; her walk with the trolley alternates the step drawings
with the body holding on the planted foot and moving on through the passing and push-off, her hands fixed on the
handle so the trolley moves with her, braking into the brace drawing. The three new sets: the service hall
seen the other way (the checkpoint and the preparation), inside the bin (Dana with the towels in front of him,
the lid sliding over), and the oblique red corner (the retreat to the ropes). Drawn in code (`film/things.py`):
the parcel tape, Dana's shoes, the banknotes, the phone, the fare card, the turning wheels, the towel on a
shoulder, the lid's shadow inside the bin.

**The fight (`film/fight.py`, `direction.py` section 6).** Each fighter's moves are written as readable moves on
the edit's marks (`guard`, `punch`, `duck`, `hit`, `lean`, `lift`) that make pose, position, lean and lift keys, in
the five beats of the plan: the confident bounce that dies away (Dana's first, then Eddie's); the slow probing jab
and the over-deep duck; glove contact each way, shown with the paired drawings (`CONTACT`: while a pair is on
screen it replaces both fighters); the advance, the ropes giving and throwing Eddie back (the ropes in the red
corner shiver, `things.rope_wobble`), the paired clinch; the separation, the trembling wind-up, the glove clash
(the one impact graphic and a two-frame white emphasis), the wobble and the simultaneous sit-down, framed waist-up,
and the referee hauling them up. The crowd, the bounce on the canvas, the soft glove pops and leather squeaks, the
ropes' creak and spring follow the same keys.

**No head cut by the frame.** `tools/framing.py` follows every person's head through every shot, six times a
second, and corrects the shot's camera until every head on screen is whole with headroom. Heads at the side of a
shot are brought fully in or taken fully out, never left half in. The corrections are `film/framing.json`, keyed to
each shot, so an edited shot is re-fitted by running the tool again (a shot framed by hand, like the freeze on Dana's
eyes, every close-up on an acting head, is marked `locked` and left alone).
`tools/lipcheck.py` renders every speaker's face at each line's stressed words and first M/B/P
(`build/lipcheck.jpg`); every line is spoken on screen except the two from inside the bin.

**The look: people lit by the set they stand in (`film/actors.py` `light`).** Characters drawn on white sheets look
pasted onto a painted set. Each set now lights the people and props in it: the room's colour over them (cool blue
night in the loading bay, warm practicals in the corridor and the red corner's room, the arena's red and blue) and
rim light from the set's lamps catching the edges that face them (sodium orange and floodlight blue outside, red and
blue from the arena's corners, white from the rig overhead), inside the ink outline, so the ink stays ink.

**The bin and the fall.** Dana climbs in over the rim and down behind the trolley's canvas, which is the only thing
that hides him. The fall is told as a chain of causes, in one wide held shot after the ramp insert: the wheel hits
the cable ramp (the trolley tips on its front wheels), her front foot braces, the towels lurch, the lid flips, his
head and hands come up over the rim, grab and miss, and he goes over the front on one arc that speeds up as it
falls, a towel following later, his shoes landing and skidding to a stop. At the end the bin waits on the floor
by the ring apron (the ringside set) and he climbs back in the same way.

**Mouths stay on faces.** A drawn mouth is clipped to the face it belongs to (the region inside the face's ink
outline round the mouth), so with a glove held at the chin the mouth opens behind the glove, never on it; and in
the ring the lines are said in drawings with the face clear (Dana drops his guard to answer, says "Pay-per-view"
bent double; the clinch keeps both faces in shot).

**Noses (`film/noses.py`).** The pack draws the ring announcer with no nose at all, and Dana's nose as a soft skin
shape with a hair-thin tip line; at screen size both read as no nose. Each of their drawings (and Dana lying on the
floor, climbing and tumbling, placed by hand in `film/nose_marks.json`) gets a cartoon nose
inked in when it is loaded (the underside of the tip, a nostril wing each side, the bridge on the side the face
turns to, a soft shadow and a highlight), in the drawing's own line colour, so it moves, scales and is lit with
the face.

**Arena lighting (`film/actors.py` `stage_light`).** Dramatic lights over pathetic action: in the arena, the ring
and at ringside the canvas sits in a pool of light with the edges falling away into the dark, soft beams come down
from the rig and sway slowly, haze glows under it, and the brights bloom.

**Life.** Everyone standing breathes on their own rhythm and shifts their weight; a pose change lands with a quick
settle; the talker's head bobs with the stress of their words; the attendant's steps bob her as she pushes; the
trolley's wobbly wheel rattles it as it rolls; press flashes pop in the arena crowd.

**Sound (`film/sound.py`, `film/crowdfx.py`).** The crowd is built from real recordings (`library/audio/sfx`,
CC0): audience laughter layered from many laughs at their own pitch, timing and loudness; roars with "yeah" shouts;
cheers and applause; all in the arena's reverb. It dips under every line and reacts to the beats: a swell into the
arena, a laugh at the promoters ducking through the ropes and at "laundry delivery", a cheer at the bell, near
silence when nobody throws anything (one cough), a roar at the ropes and the clash, a big laugh as they both sit
down, and it falls away for the ending. Foley follows the picture: the tape peeling, footsteps, the trolley's
squeaking wheel and its brake, the shoes into the towels, the lid, the wheel hitting the ramp, the fall and the
skidding shoes, the notes changing hands, the strap, the phone hitting the floor, the bounce on the canvas, glove
pops and leather squeaks, the ropes' creak and spring, the bell, the two bottoms landing as one, the fare card
slapped on. Dana's boast from inside the bin is muffled. A sting under the series title, the arena reveal and the
end title; drums under the confident bouncing that stop the moment Dana slows.

| File | What it does |
|---|---|
| `film/lines.py` | which recording each line comes from |
| `film/timeline.py` | the dialogue edit: every line in order with the beats the script asks for, as named marks |
| `film/direction.py` | 92 shots: each a camera in one of the ten sets with the people and props of that moment, every move keyed to the marks; the perspective of each set (`PPC`), the near rope and posts in front of the people, the fight written as moves |
| `film/fight.py` | the fighters' moves and the effects they make |
| `film/actors.py` | the people and props in a set at true scale: poses on a beat, the walk cycle, tumbles and leans about the feet, lifts, clips, props in hands, the guard bounce, the camera shakes and snap zooms; faces through the engine's blinks, brows and looks, with the mouths and eyes below |
| `film/mouths.py` | the drawn cartoon mouths |
| `film/eyes.py` | the clean moving pupils |
| `film/noses.py` | the inked noses for Dana and the announcer |
| `film/things.py` | drawn in code: the BANNED board, the trolley lid, the near ring ropes, contact shadows, impact stars, sweat, speed lines, press flashes, the puff of smoke |
| `film/props.py` | the engine's props hook, and the blue corner's dressing room (plate E) |
| `film/perf.py` | the acting: whom each line is said to, its delivery, the stressed words, the looks and reactions, the mouth-shape smoothing |
| `film/sound.py`, `film/crowdfx.py` | the mix and the crowd |
| `film/framing.json` | the per-shot camera corrections from `tools/framing.py` |
| `tools/dana_picks.py` | the two lines taken from Dana's second take (one is still used: "It's boxing, Eddie.") |
| `tools/stand_in_voices.py` | Kokoro stand-in takes for a line with no recording (L066 only) |
| `tools/cut_busts.py`, `tools/cut_pairs.py`, `tools/gridview.py` | how the acting heads and the paired drawings were cut (the cuts are in the library), and the grid viewer used to place face marks |
| `tools/cut_drawings.py` | every drawing cut clean from its sheet |
| `tools/framing.py`, `tools/lipcheck.py` | the head-framing fit and the lip-sync sheet |
| `tools/facesheet.py`, `tools/eyesheet.py`, `tools/marksheet.py`, `tools/markfit.py` | face sheets; every eye close up; the eye and mouth marks drawn on every drawing and refitted |

Sizes: the pack's sheets draw the characters at different scales (the walk sheets about 1.3x the casual sheets,
the laundry sheet 1.15x), corrected in `actors.SHEET`; the peek over the rim is a close-up head (`actors.DRAWING`).
Every person stands on the floor at the size their height and their depth in the set give.

## Render

From the engine's root (dependencies: `pip install -r requirements.txt`, ffmpeg, libegl1; `tools/fetch_models.sh
whisper` for `lines` and `check`):

```sh
python3 episodes/the-undercard/tools/dana_picks.py # Dana's take-2 lines as their own files
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

# The Clear Plan: Episode 1, "Not Ideal" (Scenes 1–2)

An animated football mockumentary, rendered in 4K (3840×2160, 30 fps) with the recorded voices. Scenes 1 and 2
run 3 min 17 s and end on the title card.

- **4K master:** delivered separately. At about 180 MB it is too big for GitHub's 100 MB file limit.
- **In the repo:** [`episode1_scenes1-2_1080p.mp4`](episode1_scenes1-2_1080p.mp4), a 1080p copy of the same cut.

## What's in it

| Time | Scene | What happens |
|---|---|---|
| 0:00 | Carrington | Establishing shot of the training ground with a documentary lower third. The corporate "prestige documentary" score begins. |
| 0:04 | Corridor | A member of staff passes the lens. Carrick walks towards the camera, stops, straightens his jacket and takes a breath. The door opens and warm light spills out. |
| 0:13 | Boardroom wide | Carrick at one end, Jason with his tablet, Omar composed, and Jim set apart at the far end under the screen. Held for two seconds. |
| 0:15 | "We've got a very clear plan" | Jason is energised. Carrick nods, waits for more, and asks "What's the plan?" |
| 0:25 | The tablet | An insert shows "Connecting to Boardroom Display..." while Jason taps twice. Omar looks down and Carrick watches. Then it works. |
| 0:31 | The buzzwords | CLARITY / ALIGNMENT / SUSTAINABILITY / AGILITY fill the big screen, with Jim unimpressed underneath. Jason turns: "Yeah?" |
| 0:41 | Carrick close-up | "Right... Yep... Okay... Jason... Who are we signing?" The music hard-cuts on the question. |
| 0:50 | The rally | Omar: "We've invested significantly". Carrick runs through striker, left-back, centre-back, forward and goalkeeper, and Jim answers "No" each time. Carrick looks straight down the lens: "Fair enough." |
| 1:25 | The presentation | Options and player trading ("Sell to buy"). Jason and Omar exchange a look. The absurd objectives list scrolls. |
| 2:08 | "Brilliant... Good meeting... Positive..." | A slow push-in on Carrick. He starts closing his notebook, stops, and asks where the money is going. |
| 2:25 | Omar's 3 % | The camera snaps to Omar for "Technically there weren't any dividends..." Jim: "Funny you should mention them." A video-call chime. |
| 2:33 | The Glazers call | Joel waves from a sunny Monaco terrace and Avram from a lounge, heard through tinny laptop speakers. Someone adjusts the volume. Carrick gives a polite half-wave. Avram is called away, "Go United!", and the call ends. |
| 2:54 | The silence | The camera stays on Carrick as he looks at the blank screen, then at Jason, then at Jim. "Unfortunately." "Cheers. Brilliant, yeah. [sigh] Good input." |
| 3:05 | "Right. Hull. Don't lose." | Jim closes his folder. Cut to black. |
| 3:13 | Title card | **THE CLEAR PLAN**, *Episode One – Not Ideal*, with a sting. |

All dialogue is the recorded audio, used word for word. Jim's clip has only two "No"s and the script needs three,
so his first "No" is used again for the third.

## How it's made

This follows the same approach as the Roy Keane and Jim Ratcliffe scenes: recorded voices, word-level alignment,
and characters cut from the sheets, upscaled and animated. The difference is that this is a multi-character,
multi-location edit with a shot list.

1. **Voices** (`transcribe_chunks.py`, `align_clips.py`, `lines.py`, `verify_lines.py`):
   - Every clip in `show TV.zip` is transcribed with Whisper, so each scripted line can be found in it.
   - pocketsphinx gives word and phone timings.
   - Each scripted line is cut at its exact word boundaries, at the quietest point in the gap. Every cut is
     re-transcribed to prove it holds exactly its words.
2. **Dialogue edit** (`timeline.py`): the script's beats (pauses, holds, reaction time) placed between the locked
   lines. The marks the shots and acting hang off are named here.
3. **Art** (`parts.py`, `bg_upscale.py`):
   - Every drawing used is cut from the character sheets. Touching drawings are split with a watershed.
   - The drawings and backgrounds are upscaled 4× with Real-ESRGAN.
4. **Faces** (`face.py`, `cast.py`): each character keeps the head drawn on their own body or pose drawing, so
   there are no head swaps and no seams. On that head:
   - The jaw drops per phone, with a painted mouth interior (teeth and tongue), purse and stretch.
   - Eyelids blink, and characters never blink in sync.
   - Gaze, brows, smile or frown, and head tilt, nod and turn are all warps.
   - Landmarks were read off zoomed grids of each sheet.
5. **Acting and shots** (`perf.py`, `direction.py`):
   - Keyed cues per character: who looks at whom, nods, brows, poses (Jason's tablet, presenting, shrug and
     pointing drawings) and forced blinks.
   - A shot list with documentary coverage: wide → two-shot → singles → reactions → inserts, with slow pushes,
     handheld drift, a punch-in and a whip.
6. **Sets and graphics** (`stage.py`, `sets.py`, `graphics.py`):
   - The boardroom table is re-composited from the painting over the seated characters, and each shot has depth
     of field.
   - The slides and the video call are drawn and mapped onto the screen in perspective.
   - Lower thirds, the tablet insert and the title card are drawn natively at 4K.
7. **Sound** (`audio.py`): everything is synthesised, with no sound library.
   - Room tone for each location, footsteps, the door, tablet taps and slide whooshes.
   - A video-call ring, connect and hang-up, and a laptop-speaker EQ on the Glazers.
   - A corporate piano and strings theme that ducks under dialogue and hard-cuts on "Who are we signing?", plus
     the title sting.
   - `check_audio.py` re-transcribes the finished mix to confirm every line is intelligible.
8. **Render** (`render.py`): 4K frames in parallel chunks, muxed with the mix.

`make_episode.sh` runs the whole pipeline.

# Scenes 3–4: "Hull away" (pre-match and the match)

Rendered on their own in 4K (3840×2160, 30 fps) with the recorded voices and the full sound mix: 47 s, from the
end of the title card to the hard cut after the final whistle. `./render34.sh` renders just this stretch.

- **4K master:** not rendered yet. A full-resolution check of every cut-out comes first, then the 4K render.

## What's in it

| Time | Shot | What happens |
|---|---|---|
| 0:00 | Stadium exterior, dusk | The crowd builds and a chant drifts out of the ground. Fans in amber scarves cross the plaza, and the United coach rolls in and stops with a hiss of air brakes. Lower third: **HULL AWAY**, *Premier League, Matchday 1, Kick-off 20:00*. A low pre-match pulse starts at 80 bpm. |
| 0:03.75 | Eight fast inserts, one cut on every beat or two of the pulse | Boots under the bench (a rack focus). Shirts on their hangers. White tape wound round a sock at the ankle. The goalkeeper's gloves come up and clap. Carrick walking down the tunnel, the floodlit pitch behind him. Bruno's captain routine at the front of the line: up on his toes, armband on, a nod, a look back down the line. Maguire's fists pull his laces tight. Cunha staring at the tactics board: **SET PIECES!** |
| 0:12 | The dressing room wide | Carrick stands in the middle of the room. The players sit round him on the benches: Maguire and Bruno on the side benches, Mainoo and Cunha on the back bench. Bruno is intensely focused. Maguire nods along. |
| 0:13.5 | "Newly promoted team. Crowd'll be up for it. Do the basics." | The wide, then Carrick (the two on the back bench out of focus behind him), then Bruno's close-up on "Do the basics". |
| 0:18 | "And most importantly..." | Carrick turns to the tactics board. On "SET PIECES" his finger taps the writing twice (a punch-in). |
| 0:21.4 | "Set pieces. Got it." | A quick close-up of Maguire, dead serious, with drawn lip sync and a nod on "Got it". |
| 0:23.5 | "Right." | Carrick, a small nod. Smash cut to the pitch. |
| 0:24.7 | The broadcast wide | The full stadium noise, the kick-off whistle, the score bug (HUL 0–0 MUN), 22 players in shape, the ball rolled back. |
| 0:27 | The home end | A telephoto on the stand behind the goal, the crowd bouncing. |
| 0:28.2 | The corner | Hull's corner from the far flag. The United defender gets a weak head to it, it drops on the penalty spot and goes in. The net bulges, the keeper is late and the home end goes up. |
| 0:31.8 | **HULL 1 – 0 UNITED** (23') | The score card, the crowd still roaring underneath. |
| 0:33.1 | Carrick on the touchline | No reaction. Just stillness: one blink, a long look. The ground settles around him. |
| 0:35.8 | Later: another dead ball | A free kick whipped in pinballs around the six-yard box (off four players) and over the line. Broadcast caption: **SET PIECE** *(again)*. |
| 0:39.8 | **HULL 2 – 0 UNITED** (61') | |
| 0:41.2 | Bruno | 90+4 on the clock. Bruno looks across toward Maguire. |
| 0:43.3 | Maguire | ...who slowly turns away: front, three-quarter, side, back. |
| 0:46.2 | Full time | Three blasts of the whistle, and a hard cut to black and silence. |

All four spoken lines are the recorded audio, word for word, cut at the quietest point between words and
re-transcribed from the finished mix to confirm them. Nobody else speaks. Bruno, Cunha, Mainoo and the Hull
players act without dialogue.

## How scenes 3–4 are made

Everything specific to scenes 3–4 is in its own files, so it doesn't touch scenes 1–2:
`hull.py` (every setup), `hull_audio.py` (the sound), `pitch3d.py` (the match), `mgvis.py`, `props.py` and
`defringe.py` (extra art). `timeline.py` and `direction.py` hold the beats, shots and acting as for scenes 1–2.

- **The match is 3D** (`pitch3d.py`): a real 105 × 68 m pitch (stripes, every marking, goals with nets that
  bulge) seen through a pinhole broadcast camera. The one painted stand we have (the view out of the tunnel mouth)
  is relit for a night game, filled with a drawn crowd (Hull amber and black, with a red away end; arms up for the
  goals) and mapped onto three billboard stands. So the broadcast wide, the corner, the free kick, the home-end
  telephoto and the blurred backgrounds behind Carrick, Bruno and Maguire all come from the same stadium, with
  correct perspective. The tunnel shots show the same floodlit pitch through the tunnel mouth.
- **Players on the pitch** are the character drawings scaled to 1.85 m. United wear the house-style drawings. The
  Hull players are Maguire's flat drawings recoloured into amber stripes and black shorts, each with his own hair
  colour and skin tone, so nobody recognisable plays for Hull.
- **Maguire's close-up** (`mgvis.py`): his 12 lip-sync busts are separately drawn and shift from bust to bust, so
  every viseme is the neutral bust with only the mouth swapped in. Each bust is registered onto the neutral one
  (sub-pixel), colour-matched and pasted through a feathered ellipse. The busts stop square at the shoulders, so
  his turnaround body goes underneath, scaled so its shoulder slope lies on the bust's own outline. Blinks, gaze,
  brows and the nod are procedural on top.
- **Seated players** (`props.py`): the sheets only have standing poses. Seen from the front, a seated player's
  thighs point at the camera, so the shorts become a short lap and the knees sit under the hem. The plain part of
  the socks is lengthened so the shin is half the torso's height. They're placed with the lap on the bench edge
  and the feet on the floor, at scales that follow the painting's perspective (its horizon is at seated eye level).
- **Props**: the team coach is drawn in the inked style. The goalkeeper's gloves are Maguire's open-hand drawings
  recoloured (latex palm, lime strap). The tape roll and the lace pulls use his fists and boots. `defringe.py`
  peels the cream-paper fringe off every part cut from his sheets.
- **Sound** (`hull_audio.py`): the crowd building outside, a terrace chant with claps, the coach's diesel and air
  brakes, the 80 bpm pulse (a kick on every insert cut), foley for each insert (studs, hanger, tape, glove clap,
  laces, marker), the dressing room with the crowd muffled through the walls, the stadium, the kick-off whistle,
  the corner (strike, header, shot, net, roar), the free-kick pinball with an "ooh", full time and a hard cut.

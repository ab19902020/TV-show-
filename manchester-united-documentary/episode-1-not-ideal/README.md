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

- **In the repo:** [`episode1_scenes3-4_4k.mp4`](episode1_scenes3-4_4k.mp4), 3840×2160, 30 fps, 47 s, 68 MB (x264 CRF 21).
- **Full-quality master:** `episode1_scenes3-4_4k_master.mp4` (CRF 18, 140 MB) is over GitHub's 100 MB limit, so
  it's delivered separately; `./render34.sh` rebuilds it.

## What's in it

| Time | Shot | What happens |
|---|---|---|
| 0:00 | Stadium exterior, dusk | The crowd builds and a chant drifts out of the ground. Fans in amber scarves cross the plaza, and the United coach rolls in and stops with a hiss of air brakes. Lower third: **HULL AWAY**, *Premier League, Matchday 1, Kick-off 20:00*. A low pre-match pulse starts at 80 bpm. |
| 0:03.75 | Eight fast inserts, one cut on every beat or two of the pulse | Boots under the bench (a rack focus). Shirts on their hangers. White tape wound round a sock at the ankle. The goalkeeper's gloves come up and clap. Carrick walking down the tunnel, the floodlit pitch behind him. Bruno's captain routine at the front of the line: up on his toes, armband on, a nod, a look back down the line. Maguire's hands pull the laces of his white boots tight. Cunha staring at the tactics board: **SET PIECES!** |
| 0:12 | The dressing room wide | Carrick stands in the middle of the room. The players sit round him on the benches: Maguire and Bruno on the side benches, Mainoo and Cunha on the back bench. Bruno is intensely focused. Maguire nods along. |
| 0:13.5 | "Newly promoted team. Crowd'll be up for it. Do the basics." | The wide, then Carrick (the two on the back bench out of focus behind him), then Bruno's close-up on "Do the basics". |
| 0:18 | "And most importantly..." | Carrick turns to the tactics board. On "SET PIECES" his finger taps the writing twice (a punch-in). |
| 0:21.7 | "Set pieces. Got it." | A quick close-up of Maguire, dead serious, with drawn lip sync and a nod on "Got it". |
| 0:23.7 | "Right." | Carrick, a small nod. Smash cut to the pitch. |
| 0:24.7 | The broadcast wide | The full stadium noise, the kick-off whistle, the score bug (HUL 0–0 MUN), 22 players in shape, the ball rolled back. |
| 0:27 | The home end | A telephoto on the stand behind the goal, the crowd bouncing. |
| 0:28.2 | The corner | Hull's corner from the far flag. The United defender gets a weak head to it, it drops on the penalty spot and goes in. The net bulges, the keeper is late and the home end goes up. |
| 0:31.8 | **HULL 1 – 0 UNITED** (23') | The score card, the crowd still roaring underneath. |
| 0:33.1 | Carrick on the touchline | No reaction. Just stillness: one blink, a long look. The ground settles around him. |
| 0:35.8 | Later: another dead ball | A free kick whipped in pinballs around the six-yard box (off four players) and over the line. Broadcast caption: **SET PIECE** *(again)*. |
| 0:39.8 | **HULL 2 – 0 UNITED** (61') | |
| 0:41.2 | Bruno | 90+4 on the clock. Bruno looks across toward Maguire. |
| 0:43.3 | Maguire | ...who slowly turns away. He holds the look, his eyes slide off, his head goes, then he turns his back. |
| 0:46.2 | Full time | Three blasts of the whistle, and a hard cut to black and silence. |

All four spoken lines are the recorded audio, word for word, cut at the quietest point between words and
re-transcribed from the finished mix to confirm them. Nobody else speaks. Bruno, Cunha, Mainoo and the Hull
players act without dialogue.

## How scenes 3–4 are made

Everything on screen is in the house style (the Bruno / Cunha / Mainoo / Carrick sheets, and the house-style players
sheet with Maguire, Martínez, Rashford and Mainoo, stored as
[`players-group/house-style/`](../assets/characters/players-group/house-style/)).

Everything specific to scenes 3–4 is in its own files, so it doesn't touch scenes 1–2: `hull.py` (every setup),
`hull_audio.py` (the sound), `pitch3d.py` (the match) and `props.py` (props and seated players). `timeline.py` and
`direction.py` hold the beats, shots and acting as for scenes 1–2.

- **Clean cut-outs** (`parts.py`):
  - On the Bruno / Cunha / Mainoo / Carrick sheets, the half-transparent edge pixels carry the glow painted
    behind the figures, which gave a washed-out rim. Every edge pixel now takes the colour of the nearest solid
    pixel, so the ink line is the edge.
  - On the players sheet the transparency was cut 1–3 px inside the drawn ink outline, so arms and boots lost
    their outline. That sheet is re-matted from the drawing (`ink` mode). The mask grows outwards, at most 4 px,
    through every pixel that doesn't match the local background glow. The final edge goes through the same
    upscaler as the art, so the curves are smooth.
  - Every part used was checked at full resolution on dark, light and magenta backdrops.
- **Maguire** comes from the players sheet. That sheet packs four players on a page, so his drawings are half the
  size of Bruno's. They are upscaled 8× (two upscaler passes, then an area downsample) so his close-up stays as
  crisp as everyone else's.
  - His lip sync, blinks, gaze, brows and nod are procedural on his own drawn head, as for Bruno and Cunha.
  - For the turn-away, the front view narrows edge-on and opens out as the back view. The small back-view drawing
    has its silhouette smoothed and an even ink line drawn just inside the edge.
- **The match is 3D** (`pitch3d.py`): a real 105 × 68 m pitch (stripes, every marking, goals with nets that
  bulge) seen through a pinhole broadcast camera.
  - The one painted stand we have (the view out of the tunnel mouth) is relit for a night game. It's filled with
    a drawn crowd (Hull amber and black, with a red away end; arms up for the goals) and mapped onto three
    billboard stands.
  - So the broadcast wide, the corner, the free kick, the home-end telephoto and the blurred backgrounds behind
    Carrick, Bruno and Maguire all come from the same stadium, with correct perspective.
- **Players on the pitch** are the house-style drawings scaled to 1.85 m. United are Bruno, Cunha, Mainoo, Maguire
  and Martínez. Maguire is the one who gets the weak header on the corner. The Hull players are house-style
  bodies recoloured into amber stripes and black shorts, mostly Rashford's (he isn't in United's squad here).
- **Seated players** (`props.py`): the sheets only have standing poses. Seen from the front, a seated player's
  thighs point at the camera, so the shorts become a short lap and the knees sit under the hem. The plain part of
  the socks is lengthened so the shin is half the torso's height. They're placed with the lap on the bench edge
  and the feet on the floor, at scales that follow the painting's perspective (its horizon is at seated eye level).
- **Props and inserts**:
  - The team coach and the goalkeeper's gloves are drawn in the inked house style.
  - The tape and lace inserts use Bruno's sock-and-boot drawing (with Maguire's white boots for the laces) and
    Cunha's hand.
- **Sound** (`hull_audio.py`):
  - The crowd building outside, a terrace chant with claps, and the coach's diesel and air brakes.
  - The 80 bpm pulse, with a kick on every insert cut, and foley for each insert (studs, hanger, tape, glove
    clap, laces, marker).
  - The dressing room, with the crowd muffled through the walls.
  - The stadium: the kick-off whistle, the corner (strike, header, shot, net, roar), and the free-kick pinball
    with an "ooh".
  - Full time, then a hard cut to silence.

If you have a house-style sheet for a generic Hull player or for Senne Lammens, send it: they'd replace the
recoloured bodies in the match shots.

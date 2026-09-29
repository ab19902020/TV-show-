# The Clear Plan: Episode 1, "Not Ideal" (Scenes 1–2)

An animated football mockumentary, rendered in 4K (3840×2160, 30 fps) with the recorded voices. Scenes 1 and 2
run 3 min 17 s and end on the title card.

- **4K master** (3840×2160, 472 MB): stored in [`4k/`](4k/) as five pieces, because GitHub files must be under
  100 MB. Join them back into the exact file with
  `cat 4k/episode1_scenes1-2_4k.mp4.part* > episode1_scenes1-2_4k.mp4` (checksum in `4k/SHA256SUM`).
- **1080p:** [`episode1_scenes1-2_1080p.mp4`](episode1_scenes1-2_1080p.mp4) (93 MB).
- **720p preview:** [`episode1_scenes1-2_720p.mp4`](episode1_scenes1-2_720p.mp4) (30 MB).

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

The code also directs Scenes 3–4 (Hull pre-match and the match). Only Scenes 1–2 have been rendered for now.
`make_episode.sh` runs the whole pipeline.

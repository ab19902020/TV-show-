# Micah Richards: "50 Caps" (BBC panel → Wing's, Wilmslow)

**Final video:** [`micah_richards_50_caps.mp4`](micah_richards_50_caps.mp4) (1080×1920 portrait, 30 fps, 41.3 s, with
the original audio)

A football-panel comedy skit built on the real BBC clip "Micah's regretting Wayne Rooney being on the panel". The sound
is the original clip's audio: every word, laugh and pause. Nothing is replaced, shortened or added. The picture
starts as a straight TV studio interview. When Rooney mentions Wing's, it **hard-cuts** into his memory of the
restaurant, which escalates into Micah's absurd 50 CAPS party. It returns to the studio on a match cut of Micah's
embarrassed face.

## Who says what

Speakers come from the original picture: the caption colours, and whose mouth moves in the wide two-shot. Only the
person speaking is lip-synced. Everyone else blinks, glances and reacts with their mouth shut.

| Time | Speaker | Line |
|---|---|---|
| 0.0 | Gary | "Did you two ever bump into each other in Manchester in those derby days and stuff?" |
| 4.9 | Micah | "We did, didn't we? A couple of times. You were giving it the biggun in Manchester back in those days." |
| 9.3 | Rooney | "What was it? Pubs? Clubs? What was it?" |
| 11.9 | Micah | "Everything!" |
| 13.1 | Rooney | "I've actually seen Micah in Wing's Chinese restaurant, and I was in there with my family, a quiet meal. Micah comes in with about twenty of his guys, walks in and they're celebrating. So I was thinking, what are they celebrating? It was Micah has made his fiftieth Premier League appearance." |
| 32.7 | (the panel laughs) | |
| 33.9 | Micah | "It's the Premier League. It's a big thing. It was a big thing for me, Wayne… Why did you have to say that?" |

## What's in it

| Time | Shot | What happens |
|---|---|---|
| 0.0 | Studio wide | Gary, Rooney and Micah at the desk. It is still and conventional, with a slow push towards Rooney. Micah already looks knowing. |
| 4.9 | Two-shot | Micah teases Rooney, cocky, with a tiny sideways look at Gary. Rooney listens dead-pan and rolls his eyes at "back in those days". |
| 9.3 | Rooney MCU, Micah over his shoulder | Rooney: "Pubs? Clubs?", casual, with small brow beats. Micah smirks. |
| 11.9 | Two-shot | Micah: "Everything!" Rooney's brows go up and he grins at Gary. |
| 13.1 | Rooney close-up | "I've actually seen Micah…", with a glance at the man himself. Micah's grin starts to drain. |
| **15.0** | **HARD CUT: Wing's exterior** | On "in Wing's": Rooney, Coleen and the four boys walk in. The restaurant is still a normal smart restaurant. |
| 16.7 | The family table | A quiet family meal. All six sit together at one round table. |
| 20.8 | Push-in on Rooney | "Micah comes in…": Rooney's eyes narrow and his head slowly turns. |
| 22.1 | Rooney's POV | "…about twenty of his guys": the party fills in around Micah on the words. There are confetti and 50 CAPS balloons, and Micah is dancing in the middle. |
| 23.3 | Escalation | Micah struts in and dances. Quick cuts show him pointing at himself on the 50 CAPS table and holding up both hands. Each friend has one action: Jamie raises his pint, Dan claps like a maniac, Ravi holds the 50 CAPS card behind Micah like a boxing ring card, and a friend films it all on a phone. |
| 26.5 | The family stares | Held longer than is comfortable. Coleen looks at the party, then at Rooney. One boy leans in to see and another is just confused. Rooney gives a tiny amused shake of the head. |
| 28.2 | Back to Micah | Even bigger: he runs across the frame. |
| 29.3 | From Micah's side | The family is in the background, staring. Micah notices and freezes mid-celebration. |
| 30.7 | Rooney | On "fiftieth": he just raises his eyebrows. |
| 31.3 | Micah | Plays it cool: hands in pockets, nothing to see here. |
| 32.1 | Micah's face | Embarrassed, hand behind his head. |
| **32.7** | **MATCH CUT: studio Micah** | Same face, same place, same size, now in the studio, as the laughter starts. Gary looks at him, holds a beat, then laughs. |
| 33.9 | Two-shot | Micah protests ("It's the Premier League!"), shakes his head, looks down, then back at Rooney: you've stitched me up. Rooney is delighted. |
| 38.1 | Final wide | Gary laughs, Rooney smiles and Micah gives a little shrug. A tiny 50 balloon drifts up behind him, he glances up at it, and it cuts to black. |

## The cast and sets

- **Characters:** the sheets in `src/art/`. These are Gary Lineker, Wayne Rooney, Micah Richards (sheet 1),
  Coleen Rooney, the four Rooney boys, and Micah's friends with the props (cake, 50 CAPS card, balloons, pint).
  - Each drawing is cut out by flooding the sheet's paper. Drawings that touch are split with a watershed, and a
    dam at the bottom of every head-and-shoulders drawing keeps white shirts solid.
  - Every part is upscaled 4× with Real-ESRGAN.
- **Studio:** no BBC studio art was supplied. It uses the repo's red-and-black football studio
  (`manchester-united-documentary/assets/backgrounds/tv-studio/`), extended at the top and bottom for portrait.
- **Wing's:** the supplied portrait backgrounds (exterior, round table, 50 CAPS table, balloon entrance).
  Tables, lamps and flowers are re-composited in front of the characters.
- **Seated bodies:** the head-and-shoulders drawings end in a cut across the chest, so `extend.py` continues each
  torso from the drawing's own last rows. The lapels close into a V, a tie keeps its width, and an open collar
  closes over a shirt. Behind the desk and the table everyone reads as seated.

## How it's made (`make_scene.sh`)

1. **Words:**
   - `transcribe.py` (Whisper) for a first transcript.
   - `align.py`: the hand-corrected speaking turns, with speakers, force-aligned with pocketsphinx to word and
     phone timings (`phones.json`).
   - The film's clock is the original audio's clock (zero offset, checked by cross-correlation).
2. **Art:**
   - `cut_parts.py` (sheet layouts in `layout.py`).
   - `eyes.py`: eyes for blinks and gaze. Gary's are hand-placed because of his glasses.
   - `extend.py`: torsos.
   - `props.py`: the filming phone and the confetti.
   - `plates.py`: backgrounds.
3. **Faces** (`engine.py`, `face.py`, from Episode 1):
   - Lip sync on each speaking head is a jaw drop with a painted mouth interior. It follows the phones, changes
     one frame early and holds closures for at least two frames.
   - Blinks, gaze, brows, smile, head tilt, nod and turn are warps on the drawing's own head.
4. **Acting and shots:**
   - `direction.py` is the shot list and cue sheet, keyed to the spoken words (`W("in wings")`), so nothing is
     shown before Rooney mentions it.
   - `party.py`: the party (beat-synced bounce, pop-ins, the crowd).
   - `restaurant.py`: the walk-in, with stepped strides so planted feet do not slide, and the family table.
   - `render.py`: the studio and the frame loop.
5. **Render** (`render_film.sh`): 4 parallel chunks, x264 CRF 20. The original clip's audio track is encoded once
   to AAC 320 kb/s, with no edits and no re-timing.

Review a stretch with `python3 contact.py out.jpg 1.5 6 10.5 …` (a contact sheet at those times). `GRID=1 python3
render.py still T` overlays plate coordinates.

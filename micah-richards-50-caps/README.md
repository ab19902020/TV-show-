# Micah Richards: "50 Caps" (BBC panel → Wing's, Wilmslow)

**Final video:** [`micah_richards_50_caps.mp4`](micah_richards_50_caps.mp4) (1080×1920 portrait for Shorts/Reels, 30 fps,
41.3 s, with the original audio)

A football-panel comedy skit built on the real BBC clip "Micah's regretting Wayne Rooney being on the panel". The sound
is the original clip's audio: every word, laugh and pause. Nothing is replaced, shortened or added. The picture
starts as a straight TV studio panel. When Rooney mentions Wing's, it **hard-cuts** into his memory of the restaurant:
the family's quiet meal, then Micah dancing on the table at his own 50 CAPS party. It returns to the studio on a
match cut of Micah's embarrassed face.

## Who says what

Speakers come from the original picture: the caption colours, and whose mouth moves. Only the speaker is lip-synced.
Everyone else blinks, glances and reacts with their mouth shut.

| Time | Speaker | Line |
|---|---|---|
| 0.0 | Gary Lineker | "Did you two ever bump into each other in Manchester in those derby days and stuff?" |
| 4.9 | Micah | "We did, didn't we? A couple of times. You were giving it the biggun in Manchester back in those days." |
| 9.3 | Alan Shearer | "What was it? Pubs? Clubs? What was it?" |
| 11.9 | Micah | "Everything!" |
| 13.1 | Rooney | "I've actually seen Micah in Wing's Chinese restaurant, and I was in there with my family, a quiet meal. Micah comes in with about twenty of his guys, walks in and they're celebrating. So I was thinking, what are they celebrating? It was Micah has made his fiftieth Premier League appearance." |
| 32.7 | (the panel laughs) | |
| 33.9 | Micah | "It's the Premier League. It's a big thing. It was a big thing for me, Wayne… Why did you have to say that?" |

## What's in it

| Time | Shot | What happens |
|---|---|---|
| 0.0 | Studio wide | The panel: Shearer, Gary, Rooney and Micah at the desk. Micah already looks knowing. |
| 2.6 | Gary | The question, host to camera-left. |
| 4.9 | Rooney and Micah | Micah teases him and points at him on "the biggun". Rooney listens dead-pan and rolls his eyes. |
| 9.3 | Shearer | "Pubs? Clubs?", then points at Micah, laughing, on "what was it?" |
| 11.9 | Micah | "Everything!" Both hands up. |
| 13.1 | Rooney | "I've actually seen Micah…", with a glance at him. |
| **15.0** | **HARD CUT: Wing's** | Rooney, Coleen and the four boys walk in along the pavement. The walks are rigged: feet planted, knees bending, and the boys smaller with quicker steps. |
| 16.7 | The family table | A quiet meal. All six are seated at their round table in their own seated poses (arms on the table). The children are clearly smaller than Wayne and Coleen. |
| 20.8 | Rooney | "Micah comes in…": his eyes narrow and slide right. |
| 22.1 | Rooney's POV | Micah is dancing ON the 50 CAPS table. The crowd fills in on "about twenty of his guys". Jamie raises his pint, Ravi holds up the 50 CAPS card, and a friend films it all. |
| 24.4 | Closer | Micah dances holding his own 50 CAPS card. |
| 26.5 | The family stares | Held too long. Coleen looks over, then at Wayne. One boy leans in and another is confused. Rooney gives a tiny shake of the head. |
| 28.2 | Even bigger | More confetti, a bigger dance. |
| 29.3 | From Micah's side | Across the room, Rooney and his family are crying with laughter. Micah sees them and freezes, hands still in the air. |
| 30.7 | Rooney | On "fiftieth", eyebrows up. Coleen is still laughing. |
| 31.4 | Micah | Hands in pockets, standing on the table: nothing to see here. |
| 32.1 | Micah's face | Embarrassed, behind the party table. |
| **32.7** | **MATCH CUT** | Same face, same place, same size, now behind the studio desk, as the laughter starts. |
| 33.3 | Gary | Laughing. |
| 33.9 | Rooney and Micah | Micah protests, shrugs ("it's a big thing") and points at Rooney ("for me, Wayne"). Rooney is delighted. |
| 38.1 | Final wide | Shearer points and laughs, Gary laughs and Rooney puts his hands up innocently. Micah: "Why did you have to say that?" A tiny 50 balloon drifts up behind him, he glances at it, and it cuts to black. |

## The cast and sets

- **Characters** (all in `src/art/`): Gary Lineker, Alan Shearer, Wayne Rooney, Micah Richards (both sheets),
  Coleen, all four Rooney boys, and Micah's friends Jamie and Ravi. The friends sheet's ginger-bearded Dan looked
  like Rooney at the party, so he isn't used.
- **Bodies, never stretched:**
  - The panel uses each pundit's own waist-up gesture drawings (Talking, Shrug, Pointing, Hands Up, Seated at
    Table). Each is placed by its head, so a pose change never moves the head, and the flat cut always sits behind
    the desk (`python3 render.py seats` checks every pose).
  - The family uses their SEATED AT TABLE drawings. The table drawn under each one sits exactly under our
    tablecloth's edge, so their arms rest on the real table.
- **Walking** (`walkrig.py`): each walker's 3/4 turnaround drawing is split at the hips. The leg is cut into
  thigh, shin and foot and rigged with 2-bone IK. The feet are locked to the pavement and roll heel → toe, and the
  hips drop with each step.
- **Micah dancing on the table** (`party.py`): the waist-up Hands Up (or 50 CAPS card) drawing over the legs of
  his front turnaround, joined at the neck. The motion is continuous, not swapped drawings: a knee bounce on every
  beat, a hip sway every two beats, the torso rocking against it, and a head bob. The crowd sits in the background
  plate and is softened by depth of field. Confetti falls throughout.
- **Sets:**
  - The studio is the repo's red-and-black set (no BBC studio art was supplied), extended for portrait.
  - Wing's uses the supplied portrait backgrounds. Tables, glasses, lamps, flowers and chairs are re-composited
    in front of the characters.
- **Upscaling:** 4× Real-ESRGAN for most parts. The waist-up drawings seen in close-up get 8×, and every
  silhouette is re-inked (`realpha.py`), so cut edges are a clean outline, never dashed.

## How it's made (`make_scene.sh`)

1. **Words:**
   - `transcribe.py` (Whisper).
   - `align.py`: the hand-corrected speaking turns with speakers, force-aligned to word and phone timings
     (`phones.json`). The film's clock is the original audio's clock, with zero offset (checked by
     cross-correlation).
2. **Art:**
   - `cut_parts.py` (layouts in `layout.py`) and `realpha.py`.
   - `eyes.py`: blinks and gaze, hand-placed for Gary's glasses and the poses.
   - `cast.py`: mouth landmarks of every talking drawing, head boxes and anchors.
   - `props.py`: the phone and confetti.
   - `plates.py`: backgrounds.
3. **Faces** (`engine.py`, `face.py`):
   - Lip sync is a jaw drop with a painted mouth interior. On drawings already grinning, the drawn grin opens
     wider instead.
   - Blinks, gaze, brows, smile and head tilt, nod and turn are warps on the drawing's own head.
4. **Acting and shots:**
   - `direction.py` is the shot list and cue sheet, keyed to the spoken words (`W("in wings")`), so nothing is
     shown before Rooney mentions it.
   - `render.py` is the studio, `restaurant.py` the walk-in and table, `party.py` the party.
5. **Render** (`render_film.sh`): 4 parallel chunks, x264. The original clip's audio track is encoded once to AAC
   320 kb/s, with no edits and no re-timing.

Review a stretch with `python3 contact.py out.jpg 1.5 6 10.5 …` (a contact sheet at those times).
`GRID=1 python3 render.py still T` overlays plate coordinates.

# Roy Keane: "Same rubbish every week" (The Overlap studio scene)

**Final video:** [`roy_keane_overlap_rant.mp4`](roy_keane_overlap_rant.mp4) (1920×1080, 30 fps, ~44 s, with the voice track)

Roy sits at the far side of The Overlap desk and delivers the rant. The lip sync is driven by the
phonemes in the audio, and it uses the character sheet's 13 mouth shapes (A, E, I, O, U, F/V, L, M/B/P,
S/Z, C/D/G/K, TH, W/Q, REST).

## What's in the scene

| Time | Line | Face | Shot |
|---|---|---|---|
| 0.0 | *(looks across at a co-host, then turns to camera)* | 3/4 RIGHT → FRONT | wide push-in |
| 1.7 | "Manchester United." | Skeptical | wide |
| 3.6 | "It's the same rubbish every week." | Disgusted | medium |
| 7.3 | "No urgency, no aggression, no standards." | Angry, a head shake on every "no" | close-up |
| 12.0 | "You lose the ball and stroll back like you're walking the dog." | Skeptical | medium-wide |
| 16.3 | "That shirt used to mean something." | Sad | slow close-up push |
| 18.8 | "Stop pointing fingers, stop making excuses…" | Angry | medium → close-up |
| 25.6 | "And don't give me this nonsense about confidence." | Disgusted | medium |
| 28.3 | "You're playing for Manchester United." | Angry | close-up |
| 30.7 | "Run, tackle, compete." | Angry | three snap punch-ins, one per word |
| 33.4 | "Is that too much to ask?" | Confused, head tilt | medium |
| 36.3 | "I see players losing the ball and throwing their arms up." | Disgusted | wide push |
| 39.9 | "Get back and win it." | Angry → stare | close-up to the end |

Voice clip 1 starts at 1.6 s and clip 2 starts at 25.48 s, with a 0.6 s pause between them.

## How it's made (`make_scene.sh` runs the whole pipeline)

1. **Upscale:** the studio and the character sheet are upscaled 4× with the 4x-AnimeSharp model
   (`upscale.py`) so close-ups stay sharp.
2. **Transcribe:** Whisper large-v3 turns the speech into words (`transcribe.py`).
3. **Phoneme timing:** a wav2vec2 espeak-phoneme model does CTC forced alignment of each phoneme
   (`align.py`). An independent MMS aligner agreed within about 20 ms. Word edges are then snapped to the
   actual start and end of the sound in the audio.
4. **Visemes:** each phoneme maps to one of the sheet's mouth shapes (`visemes.py`). Mouths change one
   frame ahead of the sound, which is the usual animation convention. M/B/P and F/V closures always get at
   least 2 frames. Single-frame flicker is removed, and breaths show slightly parted lips.
5. **Cut-outs and rig** (`build_assets.py`, `matte.py`, `rig.py`):
   - Every part is cut from the 4× sheet with a precision matte. Edges are soft and anti-aliased, and the
     grey sheet colour is removed from the edge pixels, so there's no halo. Stray sheet lines are dropped,
     and every enclosed area (beard shading, soul patch) stays solid.
   - Roy is built as layers, like a cut-out rig: neck piece, then the head drawing's own neck, then the
     body's collar and suit, then the head. The collar zone hidden under the original head drawing is
     rebuilt, so nothing behind any head can ever show through.
   - Each head drawing is pinned to the body by its own neck column (`headcenter.py`), so it sits dead
     centre on the neck. Head motion is rotation around the base of the neck.
   - Expression changes are hard drawing swaps, as in real cut-out animation, so there's no
     double-exposure ghosting.
   - **Mouths** (`mouth4.py`): each sheet mouth shape is registered onto each head. The swapped area is
     the whole mouth: lips, teeth, skin and soul patch, covering all of the head drawing's original mouth.
     It's feathered only inside the beard, and colour-matched on a ring of beard. The head's own mustache
     is always layered back on top, so it never changes shape between mouth shapes.
6. **Performance and camera** (`direction.py`, `render.py`):
   - head nods follow the loudness of the speech, with idle sway and breathing
   - the camera uses TV-style shot cuts on pauses, with handheld drift
   - the background gets depth of field in close-ups
   - the table and mug are masked to sit in front of him
   - final grade: bloom, vignette and grain

To change the acting or the edit, edit the expression and shot lists in `direction.py`, then re-run
`make_scene.sh`.

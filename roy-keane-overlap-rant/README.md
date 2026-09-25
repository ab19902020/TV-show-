# Roy Keane: "Same rubbish every week" (The Overlap studio scene)

**Final video:** [`roy_keane_overlap_rant.mp4`](roy_keane_overlap_rant.mp4) (1920×1080, 30 fps, ~44 s, with the voice track)

Roy sits at the far side of The Overlap desk and delivers the rant. The lip sync is driven by the
phonemes in the audio, and it uses the character sheet's 13 mouth shapes (A, E, I, O, U, F/V, L, M/B/P,
S/Z, C/D/G/K, TH, W/Q, REST).

## What's in the scene

| Time | Line | Face | Body |
|---|---|---|---|
| 0.0 | *(listening to a co-host, turns to camera)* | 3/4 right → front | hands on desk, slight lean |
| 1.7 | "Manchester United." | Skeptical | open hand presenting, two small beats |
| 3.6 | "It's the same rubbish every week." | Disgusted | both-hands shrug, then a chop on "week" |
| 7.3 | "No urgency, no aggression, no standards." | Angry | leans in, right-hand chops on each "no", both hands on "standards", head shakes |
| 12.0 | "You lose the ball and stroll back like you're walking the dog." | Skeptical → 3/4 left | leans back, dismissive flick, limp "dog lead" hand |
| 16.3 | "That shirt used to mean something." | Sad | hand on heart |
| 18.8 | "Stop pointing fingers, stop making excuses…" | Angry | leans in, one hand then both, hard chops |
| 25.6 | "And don't give me this nonsense about confidence." | Disgusted | flicks it away, open hand on "confidence" |
| 28.3 | "You're playing for Manchester United." | Angry | chops on "Manchester" and "United" |
| 30.7 | "Run, tackle, compete." | Shouting | right, left, both-hands chops with three camera punch-ins |
| 33.4 | "Is that too much to ask?" | Confused | big shrug, leans back |
| 36.3 | "I see players losing the ball and throwing their arms up." | 3/4 left → disgusted | presents, then throws both arms up |
| 39.9 | "Get back and win it." | Angry → the stare | chops, both hands on "win", settles to the stare |

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
6. **Body rig** (`arms.py`, `rig2.py`): the arms are cut from the front body drawing into upper arm,
   forearm and hand for each side, each with its own pivot (shoulder, elbow, wrist).
   - The upper arms sit behind the torso and the forearms and hands in front, so hands can come across the
     chest.
   - A shoulder filler piece bridges the torso and the sleeve when an arm lifts, so the shoulder line stays
     smooth.
   - Elbow and shoulder caps fade in as the joints bend.
   - The torso leans from the hips, and the head rides on the torso.
7. **Performance** (`perf.py`): a cue sheet keyed to the spoken words drives everything.
   - Arm poses: desk, raise, high, chest, present, shrug, arms up, flick and dangle.
   - Chop beats on stressed words: a small wind-up, then a snap down that settles.
   - Torso lean and lean-in toward camera, plus head drawing changes.
   - Arms follow their targets through damped springs, so every move has follow-through and overshoot
     instead of snapping.
   - Head nods follow the loudness of the speech and dip with each chop. There's also idle sway and
     breathing.
8. **Camera and finish** (`direction.py`, `render.py`):
   - TV-style shot cuts on the pauses, with handheld drift and three snap punch-ins on "Run, tackle,
     compete"
   - the background gets depth of field in close-ups
   - the table and mug are masked to sit in front of him
   - final grade: bloom, vignette and grain

To change the acting, edit the cue sheet in `perf.py` (gestures are tied to words, e.g.
`arm(W("stop") - 0.3, "R", "raise")` and `B += [(W("stop"), "R", 1.0)]`). To change the edit, edit the shot
list in `direction.py`. Then re-run `make_scene.sh`.

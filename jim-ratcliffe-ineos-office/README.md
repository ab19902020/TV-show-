# Jim Ratcliffe: "Britain needs to tighten its belt" (INEOS office, Monaco)

**Final video:** [`jim_ratcliffe_ineos_office.mp4`](jim_ratcliffe_ineos_office.mp4) (1920×1080, 30 fps, ~88 s, with the voice track)

Jim walks into his INEOS office overlooking Monaco harbour, stops behind the desk, turns to camera and delivers
the piece, then hurries off to his yacht. He is built entirely from the two character sheets: the turnaround
bodies, 12 head expressions, 28 of the 30 arm poses, the walk/turn/run leg poses and the 19 speaking mouth shapes.

## What's in the scene

| Time | Line | Face | Arm pose / body |
|---|---|---|---|
| 0.5 | *(walks in from the right, behind the side table)* | 3/4 left | turnaround body over WALK 1-4 legs |
| 3.0 | *(stops, turns to camera, straightens his tie)* | neutral → smile | TURN LEFT legs, ADJUST TIE |
| 4.0 | "Hi, I'm Jim Ratcliffe, co-owner of Manchester United…" | smile → raised brow | WAVE, THUMBS UP |
| 9.2 | "Britain is going backwards. It is." | disgusted → raised brow | THUMBS DOWN, ARMS CROSSED, head shake |
| 11.8 | "And somebody has to say it." | raised brow | REACH FORWARD |
| 13.1 | "We've got too many people on benefits, too much immigration, too much government spending." | disgusted | EXPLAINING 1 → EXPLAINING 2 → BOTH HANDS OUT → FRUSTRATED |
| 18.4 | "You simply cannot run a country like that." | sad | PALM OUT STOP, PALM UP (close-up) |
| 21.4 | "I can see it very clearly from here in Monaco." | smile | PRESENT → OPEN ARMS at the view (wide) |
| 26.2 | "Britain needs to learn to live within its means." | raised brow | CALM DOWN |
| 30.3 | "Ordinary people need to tighten their belts, work harder, expect less." | disgusted | TALK LEFT → HAND ON HIP → FIST PUMP → PALM OUT STOP |
| 37.6 | "Obviously, I moved to Monaco." | worried → smile | PALM UP, POINT LEFT at the harbour |
| 41.6 | "But that's different. That was a sensible financial decision." | raised brow → smile | PALM OUT STOP, OK SIGN (close-up) |
| 47.0 | "What Britain needs is sacrifice, difficult decisions, cuts, efficiency…" | disgusted → angry → raised brow | FIST, EXPLAINING 1, FIST PUMP (punch-in on "cuts"), OK SIGN |
| 53.9 | "…preferably sacrifices made by somebody else." | smile | PALM UP, POINT RIGHT off to someone else |
| 57.9 | "People say Britain used to build things. Absolutely." | neutral → raised brow | TALK RIGHT, THUMBS UP |
| 61.5 | "Factories, ships, industry." | sad | EXPLAINING 2 → BOTH HANDS OUT → OPEN ARMS |
| 64.6 | "Now we seem to build paperwork and benefit claims." | disgusted | TALK LEFT, HOLDING PAPER, THUMBS DOWN |
| 70.4 | "And people ask me, 'Jim, what's the solution?'" | raised brow → confused → thinking | PRESENT, WHAT, HAND ON CHIN |
| 73.9 | "Simple. Work harder, spend less, stop complaining." | smile → disgusted | REACH FORWARD, FIST PUMP, PALM OUT STOP, FRUSTRATED (three punch-ins) |
| 79.5 | "Anyway, I'd say more, but the yacht's waiting." | raised brow → smile | PHONE HOLD, PRESENT, POINT LEFT at the yachts |
| 83.7 | *(waves goodbye, turns and scurries off right)* | happy | WAVE, then the profile body over RUN 1-3 legs |

The four uploaded clips were in reverse order; played back to front they make the monologue above
(`src/audio1-4.mp3` are stored in speaking order).

## Staging (so nothing overlaps wrongly)

- Jim stands on the floor between the desk and the windows (feet at y≈870 in the 1672×941 background), so the
  **desk, everything on it, the glass side table, the book stack, the flowers and both foreground armchairs are
  in front of him**, and the executive chair, windows, flag and back armchair are behind him.
- `occlusion.py` builds that foreground matte: hand-traced polygons refined with GrabCut in a thin band, so the
  edge snaps to the artwork's own black outlines.
- On the way in he passes in front of the back armchair and behind the side table and flowers. His legs show only
  in the gap between the desk and the side table, with a soft contact shadow on the rug.
- He is reflected faintly in the glossy black desk top, lit by a warm rim light from the window behind him, and
  the set behind him (and the desk in front) softens in close shots.

## How it's made (`make_scene.sh` runs the whole pipeline)

This follows the Roy Keane scene's workflow. This environment can't reach HuggingFace, so every model comes from
GitHub releases or ships inside its PyPI wheel.

1. **Upscale** (`upscale.py`): 4× Real-ESRGAN. The painterly character sheets use the general model, which keeps
   the stubble and skin texture. The clean-line office uses the anime model.
2. **Transcribe** (`transcribe.py`): Whisper large-v3-turbo through sherpa-onnx.
3. **Phone timing** (`align.py`): pocketsphinx forced alignment gives word and phone timings. They agree with
   the audio's energy pauses to within about 50 ms.
4. **Visemes** (`visemes.py`): each phone maps to one of the mouth sheet's 19 shapes (A, E, I, O, U, F/V, L, M, B,
   C/D/G/K, CH/J/SH, R, TH, W, S/Z, T, N, Q, closed).
   - Mouths change one frame before the sound.
   - M/B/P and F/V closures always get at least 2 frames.
   - Breaths show slightly parted lips.
5. **Cut-outs** (`layout.py`, `matte.py`, `cut_parts.py`): 80 parts cut from the 4× sheet with soft,
   colour-decontaminated mattes.
   - The red header and floor shadows are dropped.
   - Gaps between legs and between arm and body stay see-through.
6. **Rig** (`landmarks.py`, `register.py`, `rig.py`): replacement animation in one rig frame, the FRONT turnaround
   body. Layers, back to front:
   - A shaded, outlined **neck**.
   - The FRONT body's **hanging forearm + hand**, only for poses where the drawing cuts a hanging sleeve at its
     bottom edge.
   - The FRONT **lower body** (legs + jacket flaps).
   - The **arm-pose torso**. It is registered tie-knot-to-knot and belt-to-belt, because different drawings share
     almost no SIFT features.
   - The **head**, with its own collar, tie knot and jacket stripped. It is pinned by the tie knot drawn under its
     chin, then its neck is faded into the torso's collar.
   - **Hands that come up in front of the face** (chin, tie, wave, OK sign).
7. **Lip sync** (`mouths.py`): all 19 mouth-sheet heads are registered to the closed-mouth head, so the shapes
   line up exactly. The closed-mouth head is registered onto each expression head (SIFT, then a local NCC search).
   Each frame's mouth is pasted with a feathered mask and colour-matched on a ring of beard.
8. **Blinks** (`blink.py`): the sheet has no closed-eye drawings, so a lid sampled from the skin above each eye
   closes over it every 2.4-5.2 s.
9. **Walk and run** (`walker.py`):
   - The walk-in uses the 3/4-left turnaround body, cut at the jacket hem with its hands kept, over mirrored
     WALK 1-4 legs.
   - The exit uses the right-profile body over RUN 1-3 legs, leaning into it.
   - The legs are planted on the floor and the body bobs over them.
10. **Performance** (`perf.py`): a cue sheet keyed to the spoken words drives everything, e.g.
    `pose(W("tighten") - 0.18, "HAND ON HIP")` and `beat(W("belts"), 0.8)`.
    - Hard drawing swaps, each with a small settle "pop".
    - Emphasis beats (a dip and a nod).
    - A spring-damped lean per pose.
    - Head nods driven by the speech's loudness, head shakes, question tilts, idle sway and breathing.
11. **Camera and finish** (`direction.py`, `render.py`):
    - TV-style shots cut on the pauses, with a headroom rule and handheld drift.
    - Snap punch-ins on "cuts" and on "work harder, spend less, stop complaining".
    - Every layer is warped straight from its source pixels to the screen, so nothing is resampled twice.
    - Grade: bloom, vignette and grain.

To change the acting, edit the cue sheet in `perf.py`. To change the edit, edit the shot list in `direction.py`.
Then re-run `make_scene.sh`.

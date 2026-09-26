# Jim Ratcliffe: "Britain needs to tighten its belt" (INEOS office, Monaco)

**Final video:** [`jim_ratcliffe_ineos_office.mp4`](jim_ratcliffe_ineos_office.mp4) (1920×1080, 30 fps, ~93 s, with the voice track)

A dry, straight-faced monologue in his INEOS office overlooking Monaco harbour. The comedy comes from the gap
between what he says, where he is saying it, and what he does. The acting is restrained businessman: stern and
raised-brow faces, small beats, understated head movement and natural blinks. He moves around the whole office:
behind the desk, to the windows, into the executive chair, and out of the door.

Everything is built from the two character sheets:
- the turnaround views (front, 3/4, profile, back)
- the head expressions and the arm poses
- a leg from the WALK drawings, cut into thigh, shin and shoe and rigged for the walks
- the 19 front and 4 side-view mouth shapes
- two drawings made from those parts: a raised-finger hand swapped onto the OK-sign arm, and a gold watch on the
  wrist-across pose

## What's in the scene

| Time | Line | Face | Body |
|---|---|---|---|
| 0.0 | *(stands behind the desk, facing camera)* | neutral | adjusts his jacket and tie (ADJUST TIE) |
| 1.3 | "Hi, I'm Jim Ratcliffe…" | neutral | still at the tie, calmly |
| 2.7 | "…co-owner of Manchester United…" | smug | straightens up proudly: chin up, chest out, hands on hips |
| 4.6 | "…and a Glazer ball licker." | completely serious | arms down, dead still; slow push-in |
| 6.8 | *(pause, then strolls across the office)* | 3/4 view | turnaround body over the rigged walking legs (wide shot) |
| 8.3 | "Britain is going backwards. It is." | disgusted → raised brow | stops, turns to camera, one-hand downward chop; arms folded on "It is." |
| 12.2 | "We've got too many people on benefits, too much immigration, too much government spending." | disgusted | paces slowly, counting on his fingers: thumb, thumb + index, three fingers |
| 17.5 | "You simply cannot run a country like that." | neutral | palms down, small head shake (close-up) |
| 19.8 | *(walks to the windows)* | 3/4 view | walking legs, visible on the marble in front of the glass |
| 21.7 | "I can see it VERY clearly from here in Monaco." | side view | turns side-on and extends his arm at the skyline and yachts, held after the line (wide) |
| 26.5 | "Britain needs to learn to live within its means." | side view | lectures the view, lip-synced with the side-view mouths |
| 30.6 | "Ordinary people need to tighten their belts…" | neutral → raised brow | turns back, straightens his jacket, hands to the belt and tugs it |
| 33.9 | "…work harder, expect less." | neutral | a point jabbed at camera, then a chop |
| 37.0 | "Obviously… I moved to Monaco." | raised brow | glances back over his shoulder at Monaco, small shrug |
| 41.9 | "But that's different. That was a SENSIBLE financial decision." | raised brow → smug | arms folded, then one finger raised (close-up) |
| 46.3 | "What Britain needs is sacrifice, difficult decisions, cuts, efficiency…" | neutral | walks back along the desk, one gesture per word: finger, weighing hands, chop, OK sign |
| 54.1 | "…preferably sacrifices made by somebody else." | straight-faced | sits back in the executive chair, crosses a leg |
| 58.1 | "People say Britain used to build things. Absolutely." | neutral → raised brow | seated |
| 61.7 | "Factories. Ships. Industry." | neutral | stands; three strong hand beats with punch-ins |
| 64.8 | "Now we seem to build paperwork and benefit claims." | disgusted | paces in front of the window, a little more animated |
| 70.6 | "And people ask me, 'Jim, what's the solution?'" | raised brow → thinking | palm up, 'what', hand on chin |
| 74.1 | "Simple. Work harder. Spend less. Stop complaining." | neutral → disgusted | points straight at camera on each one (four punch-ins) |
| 79.7 | "Anyway…" | neutral | checks his gold watch (lids lowered, head down) |
| 81.0 | "I'd say more — but the yacht's waiting." | smug |  |
| 83.8 | *(turns to look out at the yachts, picks up his phone, walks out)* | back view → 3/4 | BACK turnaround, PHONE HOLD, walks out past the side table |
| 90.3 | *(the empty office for 2 s, fade out)* |  |  |

The four uploaded clips were in reverse order; played back to front they make the monologue above
(`src/audio1-4.mp3` are stored in speaking order). Pauses are inserted where the direction needs time
(`visemes.py` `SEGMENTS`): a dead-pan beat after "Glazer ball licker" to start walking, the walk to the windows
before "I can see it", and the exit plus 2 s of empty office at the end.

## Staging (so nothing overlaps wrongly)

- **Places** (`perf.py`): behind the desk, across the office, the marble floor in front of the windows, the
  executive chair and the exit past the side table. Each place sets his position and depth. Further back means a
  higher floor line and a smaller figure, so he is smaller at the windows and larger in the big chair.
- **In front of him:** the desk, everything on it, the glass side table, the book stack, the flowers and both
  foreground armchairs. `occlusion.py` builds that matte from hand-traced polygons refined with GrabCut, so its
  edge snaps to the artwork's own outlines.
- **Behind him:** the executive chair, the windows, the flag and the back armchair.
- **Legs:** they show where the floor is open, in front of the windows and in the lane between the desk and the
  side table, with a soft contact shadow.
- **Sitting:** he sinks behind the desk into the chair with the chair back behind him, so the desk hides the
  crossed leg.
- **Finish:** a faint reflection in the glossy desk top, a warm rim light from the window, and depth of field on
  the set in close shots.

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
   colour-decontaminated mattes. His shirt, collar and cuffs are as white as the paper, so a plain background
   flood would leave them see-through. Instead the cutter:
   - seals the shape first (the neck opening of each headless torso, the cuff ends) and floods only from the
     sides where the cell edge is real background;
   - classifies every enclosed white area: shirt next to the tie, cuffs, highlights and pocket squares are
     filled; true gaps (between an arm and the body, between the legs) stay open;
   - splits drawings that touch on the sheet at their narrowest point (watershed), with explicit split lines
     where a hand from one pose reaches into the next (`ARM_SPLIT`);
   - drops the red header and floor shadows.
6. **Rig** (`landmarks.py`, `belts.py`, `register.py`, `rig.py`): replacement animation in one rig frame, the FRONT
   turnaround body. Every pose has the same collar, knot and shoulders. Layers, back to front:
   - The FRONT **lower body** (legs + jacket flaps), with the belt-to-hem band warped per pose to meet that
     pose's jacket edges.
   - The FRONT body's **hanging forearm + hand**, only for poses whose drawing cuts a hanging sleeve.
   - The **head** (face, hair, neck), *behind* the clothes. It is placed knot-to-knot at face scale; its neck
     tucks down into the collar, so it can nod and tilt without ever opening a gap.
   - **FRONT's collar, knot and shoulders**, per pose, with each side scaled to that pose's shoulder width. The
     arm-pose drawings are cut flat just above the collar; this gives every pose the same rounded shoulders
     and the same collar round the neck.
   - The **arm-pose torso**. Its knot top (the first solid row of the crimson knot, never the orange neck shadow)
     goes exactly onto FRONT's knot, its belt onto FRONT's belt. Its neck opening is cut to FRONT's collar V and
     its top edge melts into FRONT's shoulders, so knot and collar never double up. ARMS DOWN *is* FRONT's
     clothes.
   - **Hands in front** (chin, tie, wave, OK sign, raised finger).
   - **Moving hands** (the chop and the camera point) are cut free. The chest behind them comes from the other
     arm-pose drawing that is clear of hands there and matches best around the hole (picked automatically),
     with the pose's own chest mirrored across the tie as a fallback.
7. **Lip sync** (`mouths.py`, `walker.py`): all 19 mouth-sheet heads are registered to the closed-mouth head, so
   the shapes line up exactly. The closed-mouth head is registered onto each expression head (SIFT, then a local
   NCC search).
   - Each frame's mouth is pasted with a feathered mask and colour-matched on a ring of beard.
   - When he talks in a 3/4 view, the same painted mouth shapes are squashed onto the 3/4 head's measured mouth
     line.
8. **Blinks** (`blink.py`): the sheet has no closed-eye drawings, so a lid sampled from the skin above each eye
   closes over it every 2.4-5.2 s.
9. **Walking and turning** (`walker.py`, `legrig.py`): the sheet's WALK 1-4 drawings can't be swapped in as a cycle.
   In two of them the planted shoe points backwards, and the four don't line up. So the walk is rigged:
   - One straight leg from WALK 3 (shoe pointing the way he walks) is cut into thigh, shin and shoe, with rounded
     overlaps at the knee and the trouser cuff over the shoe. The far leg is the same leg, darker and set back.
   - Each foot is locked to its spot on the floor in world space (so it holds while he walks into depth). It lands
     heel first, rolls flat, lifts at the heel and swings forward. The knees are solved from hips and ankles
     (2-bone IK), and the hips drop just enough for the standing leg to reach, which gives the walk its bob.
   - Every walk is a whole number of steps and starts and ends with the feet together, so it joins the standing
     3/4 frames of the turns.
   - Walking into the room, the stride is solved on a flat floor and sheared onto the floor's slant on screen, so
     it stays a stride instead of turning into a lunge.
   - A leftward walk mirrors the whole rig: legs, torso and head always face the way he walks.
   - Turns step through the turnaround drawings (front → 3/4 → profile), 2-3 frames each.
   - He looks out at the yachts in the BACK view.
10. **The window gag** (`profile.py`):
    - The profile body is mirrored to face the harbour.
    - Its near arm is cut out and rotated at the shoulder; the jacket behind it is painted in.
    - The mouth sheet's four side-view heads (closed / A / O / U) are registered face-to-face onto the
      turnaround's own head (gradient NCC on the face, cached in `profile_fit.pkl`) and lip-synced.
    - Below the jaw line the turnaround's own neck and collar show, so the head sits on the drawing's real neck.
11. **Hand moves and extra drawings** (`extras.py`):
    - The chop drops and foreshortens toward camera; the point jabs at the lens.
    - The raised finger (the OK-sign arm with the finger hand, the old hand painted out from the jacket) and the
      gold watch are composited once.
12. **Performance** (`perf.py`): the blocking plus a cue sheet keyed to the spoken words drives everything, e.g.
    `pose(W("tighten") - 0.2, "HAND ON HIP")`, `chop(W("less") + 0.03)` and `jab(W("simple") + 0.02)`.
    - Hard drawing swaps, each with a small settle.
    - Emphasis beats, a spring-damped lean per pose, and the belt tug, shrug, leg-cross shift and phone pickup.
    - Loudness-driven nods, question tilts, breathing and blinks. When he looks down at the watch, his lids lower.
13. **Camera and finish** (`direction.py`, `render.py`):
    - Wides for every walk, so his movement is always shown. Medium shots for the talking.
    - Slow pushes on the dead-pan lines. Punch-ins on "Factories. Ships. Industry." and on the four points at
      camera.
    - A headroom rule and handheld drift.
    - Every layer is warped straight from its source pixels to the screen, so nothing is resampled twice.
    - Grade: bloom, vignette and grain.

To change the acting, edit the cue sheet in `perf.py`. To change the edit, edit the shot list in `direction.py`.
Then re-run `make_scene.sh`.

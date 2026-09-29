---
name: new-scene
description: Make a new animated, lip-synced character scene (video) in this repo from uploaded files - a character sheet (and mouth sheet), a background, voice clips and the user's director's notes. Use when the user asks for a new scene / video / episode / character, or sends new character art and audio to animate.
---

# Make a new scene

The user sends new art and voice clips plus director's notes; you turn them into a finished 1080p video in a new
scene folder, the same way `jim-ratcliffe-ineos-office/` and `roy-keane-overlap-rant/` were made. Read the
README of the scene you base the new one on before changing its code: it explains every stage.

The user judges the result frame by frame. The quality bar at the bottom is what they have asked for so far;
check every item yourself before you show them anything.

## 1. Collect the inputs

- Uploaded files land in `/root/.claude/uploads/<session id>/` with random names
  (`ls -t /root/.claude/uploads/*/`). Look at every image and identify it: the character sheet, a separate
  mouth sheet if there is one, and the background.
- Voice clips: transcribe them all first (step 3). The upload order is not the speaking order (Jim's four clips
  came in reverse), so order them by what is said.
- Director's notes come in the user's message. If there are none, write a short plan in the same style (where he
  stands, what he does on which line, where he walks, the camera) and show it before building.
- Ask only for what is truly missing: e.g. no background, or clips whose order you can't tell from the words.

## 2. Start the scene folder

```bash
pip install -r jim-ratcliffe-ineos-office/requirements.txt     # fresh containers don't have them
tools/new_scene.sh <firstname-lastname-place>                   # copies Jim's pipeline code, no art / builds
```

Base on `jim-ratcliffe-ineos-office` (full body: arm-pose torsos, walks, sitting, turnaround views, separate
mouth sheet) unless the sheet looks like Roy's (head angles + expressions + mouth row, no arm poses): then pass
`roy-keane-overlap-rant` as the base (seated, arms rigged from the front body drawing). Roy's pipeline fetches its
models from HuggingFace, which cloud sessions can't reach: keep Jim's `upscale.py`, `transcribe.py`, `align.py`
and the model downloads in `make_scene.sh` (GitHub releases) whichever base you use.
Copy the files into `<scene>/src/` as `sheet.png`, `mouths.png` (if separate), `office.png` or the
background's own name (update `upscale.py` calls in `make_scene.sh` and `load_plates()` in `render.py` to
match), and `audio1.mp3 ... audioN.mp3` in speaking order. Remove Jim-specific leftovers you don't use
(e.g. `extras.py` watch/finger drawings, the INEOS occlusion polygons) as you replace them.

## 3. Audio -> words -> mouth shapes

- `python3 transcribe.py` (Whisper turbo, offline) -> `transcript.json`. Fix misheard words by hand.
- `python3 align.py` -> `phones.json`. Words missing from the dictionary go in `align.py` `EXTRA`
  (ARPAbet), e.g. names, slang.
- `visemes.py` `SEGMENTS`: the clips in speaking order, each with the pause before it; split a clip where the
  direction needs a silence (a dead-pan beat, time to walk somewhere). `OUTRO` = time after the last word.
- Mouth shapes: map each phone to the sheet's shapes; mouths change 1 frame before the sound, M/B/P and F/V
  closures last at least 2 frames.

## 4. Cut out the parts

- Upscale the sheets and background 4x (`make_scene.sh` step 1).
- Measure the sheet layout: view the 1x sheet with a coordinate grid and fill `layout.py` (turnaround boxes,
  head cells, arm-pose cells, hands, legs, header rows). Every sheet differs; never reuse Jim's numbers.
- `python3 cut_parts.py` and look at `parts_check.png`, then check suspicious parts on **magenta** (not green,
  not white): white shirts, collars and cuffs are the same white as the paper and must be solid.
- Where two drawings touch on the sheet, add a split rule in `layout.py` `ARM_SPLIT` (sheet coordinates) and
  re-cut; where the sheet's header bar cuts a drawing, handle it like ARMS DOWN / POINT LEFT in `rig.py`.

## 5. Rig

- `python3 register.py`, `python3 mouths.py`, then build the rig and audit it:
  - `python3 tools/joins.py <scene> out.jpg NEUTRAL` and again with a tilt and nod (`SMILE -3 6`), plus
    `--zoom knot`. One knot, the same collar on every pose, the neck inside the collar, no pink.
  - Knot anchors come from the crimson of the knot (`rig.knot_top`), belts from `belts.py`; add overrides in
    `landmarks.py` / `belts.py` only for poses where a hand covers them. A tie that isn't red, or an open collar,
    needs those detectors adapted: check with the knot zoom.
- Walks: `python3 tools/walkcheck.py <scene> out.jpg PLACE_A PLACE_B`. The leg rig (`legrig.py`) cuts one
  straight leg from the sheet's walk drawings (`SRC`): pick the one whose front shoe points the way he walks.

## 6. Set and direction

- `occlusion.py`: trace polygons (1x background coords) around everything that must be in FRONT of him (desk,
  foreground furniture); GrabCut snaps them to the outlines. Check `occlusion_vis.png`.
- `perf.py` places: `(world x, floor y, scale)` per spot he stands, measured on the 4x background (feet on the
  floor, size consistent with the furniture, smaller further back).
- Blocking and cue sheet in `perf.py`, keyed to the words (`W("word")`): walks with `moveto`, poses, heads,
  chops, jabs, beats. Restrained, deliberate acting reads best; the comedy comes from the words.
- `direction.py`: wides for every walk (the legs must be seen), mediums for talking, pushes on dead-pan lines,
  punch-ins on lists and punchlines.

## 7. Review before rendering

- `python3 tools/stills.py <scene> beats.jpg <one time per beat...>` and look at every sheet at full size.
- `python3 tools/stills.py <scene> walk.jpg <t0> <t1> --run [--crop x0,y0,x1,y1]` for every walk and every
  fast gesture (chops, points): consecutive frames show sliding feet, popping and flicker.
- Fix, re-check, and only then render.

## 8. Render and deliver

```bash
tools/render.sh <scene> <scene>/<video name>.mp4          # ~10-15 min for 90 s; CRF 22 stays under 100 MB
tools/preview.sh <scene>/<video name>.mp4 <scratchpad>/preview_720p.mp4
```

- Pull a few frames from the finished file (`ffmpeg -ss T -i video -frames:v 1`) and check them.
- Write the scene README (like Jim's: what's in the scene by time, staging, how it's made), add the scene to the
  root README table, set `.gitignore` for build products, commit and push to the session's branch.
- Send the 720p preview with SendUserFile and say what changed, briefly, in plain words.

## Quality bar (the user's notes so far - check all of them every time)

- **Nothing see-through**: shirt, collar, cuffs, the gap by the tie. Check cut-outs and rig on magenta.
- **Head sits on the neck**: the neck tucks into the collar; no gap when the head nods or tilts.
- **Collar and tie identical on every pose**: one clean knot, never a doubled or pinched knot, no second
  shoulder line, no flat crop across the shoulders.
- **No free-floating or extra hands**: every hand belongs to an arm; the chest behind a moving hand is filled.
- **Walks**: legs, torso and head face the same way; both shoes point the way he walks; planted feet never
  slide; no lunges when walking into depth.
- **Lip sync** matches the audio at full resolution, including 3/4 and side views.
- **Staging**: furniture in front of / behind him correctly, feet on the floor, consistent size.
- **Restrained acting**: natural blinks, small head movement, gestures on the words the notes name.

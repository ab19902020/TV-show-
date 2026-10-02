# Rooney & Rio at the 50 Cent Concert — cartoon remake

The complete portrait short, rebuilt from the selected Rooney, Rio Ferdinand and 50 Cent character sheets. Five new arena backgrounds match their ink outlines, compact caricatures and cel shading. This project uses Python cutout animation and FFmpeg; Runway is not used.

## Render

Python 3.12 and FFmpeg with libx264 are required. From this directory:

```sh
python -m pip install -r requirements.txt
python prepare_assets.py
python render.py --width 1080
```

The finished file is `output/Rooney-G-Unit-Cartoon-1080x1920.mp4`, 1080 × 1920 at 30 fps. The render has 1,095 frames, including the final black frame. For a smaller preview, use `--width 540`. To render a single frame, use `--width 720 --frame 31.833`. Use `--contact` to generate an overview of the complete scene.

## Editable sources

- `src/art/` contains the three selected character sheets, five matching backgrounds, and complete microphone-holding, beckoning, walking-off and laughing poses.
- `src/audio/original.webm` contains the original Rooney recording. The render maps its entire audio stream, preserving the source start offset, and encodes AAC for MP4 playback. No speech, music or effects are added.
- `prepare_assets.py` extracts transparent character parts, expression drawings and mouth shapes. Its outputs are regenerated in `build/parts/`.
- `engine.py` contains all shot timing, camera positions, expressions, blinks, gaze, rigid cutout acting and the hand-held microphone staging.
- `walkrig.py` provides articulated legs and grounded step cycles.
- `reference_face.py` handles eye movement and blinking.
- `render.py` renders frames in parallel and combines the picture with the original audio.
- `DIRECTOR.md` records the story and staging brief. Its broad timeline is adapted to the actual recording: the quoted punchline begins at approximately 31.7 seconds.

Only the recorded on-stage G-Unit punchline is lip-synced. The other shots use silent reactions beneath the original narration. The final composition holds briefly on Rooney holding his microphone and Rio laughing while keeping his own microphone, then cuts to black at the recording's end.

The first build and output directories are created by the preparation and rendering scripts. Intermediate parts, render chunks and previews are omitted from this source archive because they can be regenerated.

## Version 2: shoes, show lights, more gags

**Final video:** `output/Rooney-G-Unit-Cartoon-1080x1920.mp4` is rebuilt by `render.py`. The copy in the repo is
[`Rooney-G-Unit-Cartoon-1080x1920.mp4`](Rooney-G-Unit-Cartoon-1080x1920.mp4).

**The trainers stay on (`walkrig.py`).** The rig used to cut each foot at a fixed height. These chunky trainers are
taller than that cut, so the top of the shoe moved with the shin and only the sole moved with the foot. The shoe
split in two and the toe went through the stage on every roll. Now:
- Each trainer is cut out whole, with its outline, plus a strip of trouser tucked under the hem.
- The ankle sits inside the shoe, under the middle of the hem.
- The foot rolls about its real heel and toe, and less than before (9° and 15°).
- It is lifted whenever any part of the shoe would go under the floor.
- The far trainer stays white instead of grey.
- Hips and knees are round joints, with no flaps or see-through ghosts.

Check a walk with:
- `python3 tools/walkview.py out.jpg rooney_mic_right --feet`
- `python3 tools/legs_tinted.py out.png fifty_exit` (far leg red, near leg green)
- `python3 tools/strip.py out.jpg 29.3 31.2 --step 2 --crop 100,700,1080,1920`

**Hip-hop show lights (`lights.py`).** The lights are drawn on the set, under the characters. The cue sheet is the
`show()`, `party()`, `dim()` and `strobe()` functions at the top of the file.

| Time | Lighting |
|---|---|
| 1.25 | The show is on. Moving heads sweep on a 92 bpm pulse, the rig changes colour every bar, coloured spots run over the stage floor, and the colour spills into the wings. |
| 19.95 | 50 walks off and takes the show with him: the rig dies and his follow-spot leaves with him. |
| 21.0 | Rooney and Rio are left in the dark until their spot flickers on, late. |
| 26.3 | The idea: the colour creeps back. |
| 29.25 | The strut: building. |
| 31.7 | Every "G" gets a strobe hit and a camera punch-in. |
| 32.47 | "UNIT": a camera jolt and spark fountains. |
| 33.5 | Full disco: every head a different colour, a mirror ball and a party strobe. |

**Gags.** All of them are silent, under the original audio:
- Rooney and Rio go rosy-cheeked on "a few drinks" and stay that way. Rooney hiccups during the wobble.
- The front rows jump on the beat, freeze during the awkward silence, then go wild after UNIT.
- A tumbleweed rolls across the stage in the silence. Rooney and Rio both get sweat drops.
- Rooney waggles his eyebrows on the idea, the microphone gives a "ting" glint, and he swaggers on the strut.
- 50 Cent shakes his head, amused, from the wing.

## Approved-version polish

Rio’s face is animated on its own native head, without a second expression-face overlay. `performance.py` uses the episode 1 keyed reaction approach for gaze, brows, blinks, nods and closed-mouth acting. Rooney’s selected phoneme drawings remain the lip-sync artwork, with a small audio-driven jaw movement from the episode 1 face engine. Both characters receive a visible handheld microphone before their stage entrance; all props stay in their drawn hand grips, including the laugh reaction. The stage crossing uses a rear lane for 50 Cent, and close-up framing removes partial neighbouring faces.

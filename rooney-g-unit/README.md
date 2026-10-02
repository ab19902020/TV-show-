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

## Approved-version polish

Rio’s face is animated on its own native head, without a second expression-face overlay. `performance.py` uses the episode 1 keyed reaction approach for gaze, brows, blinks, nods and closed-mouth acting. Rooney’s selected phoneme drawings remain the lip-sync artwork, with a small audio-driven jaw movement from the episode 1 face engine. Both characters receive a visible handheld microphone before their stage entrance; all props stay in their drawn hand grips, including the laugh reaction. The stage crossing uses a rear lane for 50 Cent, and close-up framing removes partial neighbouring faces.

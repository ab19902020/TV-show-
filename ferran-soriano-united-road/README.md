# Essentially, We Did It: a United Road parody (Cartoon Soriano)

**SATIRE: FICTIONAL DIALOGUE.** Every line is invented parody. None of it is a genuine statement, confession,
quotation or factual admission by Ferran Soriano or Manchester City. The original interview's audio is not used.
The film carries no broadcaster graphics, club crests or sponsor logos.

| File | What it is |
|---|---|
| `soriano_parody_portrait.mp4` | the master: 1080×1920, 30 fps, H.264 + AAC 48 kHz, −16 LUFS / −1 dBTP |
| `soriano_parody_landscape.mp4` | not rendered yet: the 1920×1080 version is set up with its own framing and room (`./render_all.sh landscape`) |
| `preview.html` | browser preview: play/pause, seek, restart, portrait/landscape switch, optional subtitles, click-to-jump cue list |
| `soriano_cues.csv` / `.json` | timeline / cue track: sequence, beat, start, end, spoken phrase, camera, gesture, expression, overlay |
| `soriano_parody.srt` / `.vtt` | subtitles (not burned into the picture) |
| `sprite_manifest.json` | every sprite: source image and rectangle, pivots, scale, z-order, gesture, mouth/expression identity |
| `script.py` | the 19 beats word for word, with their performance tags |

The picture is 4:53: the dialogue, a 1.1 s hold on his faint smile, then a 1 s end card
(UNITED ROAD / SATIRE — FICTIONAL DIALOGUE). It opens straight on him, hands clasped, with the
"CARTOON SORIANO / A UNITED ROAD PARODY" card fading out. UNITED ROAD and SATIRE — FICTIONAL DIALOGUE stay
on screen throughout.

## How it follows the sheet

- **The voice sets the timing.** The five recordings play end to end in speaking order. Every pause inside a clip is the recording's
  own. Where one clip ends and the next begins, a pause the length of the recording's own beat pauses (~0.65 s)
  goes in. Nothing is sped up or cut. The recordings voice the performance tags ([laughs], [whispers]) as delivery
  rather than as separate sounds. There are four audible sighs, which get the shoulder drops, and no laughs, so
  there is no laughing mouth anywhere: the [laughs] lines get smug smiles instead.
- **Lip sync** from pocketsphinx forced alignment of the words to phones. Shapes are the sheet's A, E, I, O, U and REST
  (REST also covers M/B/P), plus FV, L and TH made from them. Each shape shows one frame before its sound;
  closures last at least two frames; the mouth closes in silence.
- **Cameras:** A (eye-level medium, ~65 %), B (chest-up, ~27 %), C (head and shoulders, ~8 %). Cuts land on changes
  of thought; slow pushes on the whispers and on "the POSITIVES". Portrait framing follows the original interview:
  head near the top, the jumper running out of the bottom of frame.
- **Gestures** G01–G08 are the gesture sheet's own drawings. Each changes 5 frames before its word and settles onto
  it. The forearms are cut free at the elbow, for the beats, waves, sweeps, the slowly lowered index finger, the
  counting taps and the small circle. The compound poses (arms folded, hands clasped) stay complete drawings.
- **One head everywhere:** the big head from the main sheet sits on every pose, so the nose, hairline, head size,
  outline and eye line never change. The expressions are small movements of the brows (one raised, both raised,
  sad inner corners, a frown), a smile or smirk, a squint and the gaze, over the same fixed face. **He never blinks**,
  just like the real interview (the rig can blink; `perf.py` keeps the schedule it would use, switched off).
- **Graphics** are kept few and small, as asked: ACCURATE / UNHELPFUL, CASE ONGOING / METER RUNNING, 115, two CAS
  stamps, and SUPPORTER → INNOCENT / JOURNALIST → APPEALING. They are tags in the lower third that fade in and
  out. Each goes before the next beat.
- **Room:** the two supplied backgrounds (`src/rooms.png`), one per format, softly lens-blurred like the original.
  Light matches in every shot: a soft key from above camera-left and a cool rim from camera-right.

## How it's made (`make_scene.sh`)

1. `transcribe.py` (Whisper, fixed by hand in `transcript.json`), `align.py` (pocketsphinx), `timeline.py`
   (clips, beats, phrases, sighs), `visemes.py`, `captions.py`, `audio.py` (mix and loudness).
2. `parts.py`: cuts every drawing using the sheets' own alpha (no keying) and bleeds the colour of the
   non-solid edge pixels so no glow fringe remains. It upscales with Real-ESRGAN: the gesture poses to 8×, everything
   else to 4×. `set.py` places the two rooms.
3. `head.py`, `mouths.py`, `alt_faces.py`, `eyes.py`, `face.py`: the master head and its face rig.
   `bodies.py`: registers every pose to the clasped-hands pose by its collar and shoulders, removes its own head,
   and carries the jumper on below the waist cut. `arms.py`: forearm pieces with elbow and wrist pivots, the
   torso refilled behind them.
4. `perf.py` is the cue sheet: poses, arm moves, expressions, gaze, nods, sighs, cameras and graphics, keyed to
   the words. `render.py` draws a frame. `render_all.sh portrait|landscape` renders in parallel chunks and muxes
   the sound.

Review a stretch with `python3 tools_sheet.py portrait out.jpg 8.8 9.8 23.4` (a contact sheet at those times).

The arms + hands sheet (`src/arms.png`) is cut too (`build/parts/arm*`, `hand*`), but the film doesn't use it:
the gesture sheet's own forearms match its torsos in scale and shading exactly.

# Bruno Bruno Bruno: procedural music video

[`bruno_bruno_bruno.mp4`](bruno_bruno_bruno.mp4): 1920×1080, 30 fps, 1:36.

Everything is generated in code from the audio in `src/bruno.mp3`. There is no source art.

- **Audio analysis** (`analyse()` in `render.py`): an FFT gives bass, mid and high band energy, spectral flux
  gives onsets, and autocorrelation gives the tempo (~86 BPM) and the beat grid. A slow bass average, the
  "heat", picks out the big sections.
- **Scene**: a night stadium with a sky that shifts from cool blue to hot red as the heat rises, floodlights
  that pulse and sweep on the kick, coloured stage beams, about 6,000 crowd figures who bounce to the beat
  (phone lights in the quiet parts, arms up in the big parts), and an LED board that alternates between a
  spectrum analyser and a scrolling "BRUNO" banner.
- **Dancer**: an original cartoon footballer in a red #8 shirt, built from a 2D skeleton with leg IK. He
  switches between six moves (bounce, wave, point, hop, cupped ears, fist pump) every 8 beats, picked by
  section energy, and blends smoothly from one to the next. He blinks too.
- **Big moments**: fireworks on strong onsets, confetti, a "BRUNO!" stamp every 4 beats, camera shake on
  hits, zoom pulses on the kick, and close-up pushes in the choruses.
- **Text**: a "BRUNO / BRUNO / BRUNO" title card, then an "I'LL BE ALRIGHT" caption in the high-energy
  sections and over the outro.

## Render

```
pip install numpy pillow        # plus ffmpeg on PATH
python3 render.py               # full video (about 3 minutes on 4 cores)
python3 render.py --preview 8   # a still every 8 s into stills/
```

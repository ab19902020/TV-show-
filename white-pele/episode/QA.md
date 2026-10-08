# QA — White_Pele_PREVIEW_720p.mp4 (v2: the upgrade pack)

## v2 (this render)

The video was restaged on the client's upgrade pack. That covers the ten new sets and Rooney's performance, walk
and football poses. It also covers the Rio and Keane reactions, six supporters and the props, in 72 shots. The full
render passed the same checks as v1: H.264 1280x720 30 fps, 5325 frames, timestamps continuous (no gaps), a full
decode with no errors, and **0.00 ms audio offset at all 31 check points** (start, middle, the clap, the finale and
all 23 chunk joins; correlation 0.984 or better). See `qa720.txt`.

New since v1:
- Contact shadows under every figure on the new sets.
- The overhead kick on the floodlit pitch from the pack's key poses: run in, takeoff, the strike with the ball
  meeting the boot (impact flash), the landing, then the net and the celebration.
- Keane's clap is now his own drawing, on the crash at 149.243 s, then his arms fold again.
- The broom button: Keane sweeps a visible patch, and the confetti is pushed ahead of the broom. Rooney looks over
  at him and Rio laughs.
- Separate supporters at three depths in the pub, a rooftop cutaway, a rear view into the tunnel and a reverse
  view of the stage. Paper left between the walking legs is removed.
- Rooney is on screen about 70% of the time (78% with young Rooney).

Known, for the review:
- The pack's walk sheet has four side keys and is played as the cycle. It is not an in-betweened contact, down,
  passing and up cycle.
- The pack's poses are whole drawings, so pose changes are cuts or swaps on the beat, not rigged in-betweens.

## v1

Render: `EP_RES=1280x720 ... render --jobs 4 --chunks 24 --resume` (24 chunks of 222 frames; 12 re-rendered after the
fixes below). Encoded 125 MB, refitted by the engine to 92 MB (two-pass) for the repository; the full-quality master
stays in `build/master.mp4`.

## File checks (`build/qa720.txt`)

| Check | Result |
|---|---|
| Streams | H.264 1280x720 30 fps, AAC 48 kHz stereo 256k |
| Full decode (`ffmpeg -f null`) | no errors |
| Frames | 5325 video frames, 0.000–177.467 s, every step exactly 1/30 s, no gaps. The 24 parts hold 5326; the mux's `-shortest` drops the last one, which starts after the song ends (177.500 s) and is black from the fade-out |
| Audio | 177.536 s (the decoded song is 177.520 s plus AAC priming), packets continuous |
| Sync against the untouched song (cross-correlation of 0.1 s windows, ±50 ms search) | **0.00 ms offset** at the start (3.0, 15.2), the middle (60, 88.9, 120), the clap's crash (149.24), the finale (165, 172) and **every chunk join** (7.4 s steps, 23 joins); correlation 0.984–1.000 |

## Picture checks

The contact sheet (`build/contact.jpg`) has three frames of each of the 68 shots. Every chunk was reviewed in 12-frame
strips. Close-ups and the opening were checked at full size.

Fixed after the first pass, then re-rendered:
- Goldbridge standing: Pass Mic's cut-out kept a strip of the sheet's header over his head and the paper between
  his legs (`tools/make_art.py mark-stand`).
- Goldbridge's cheer: his eyes are too small on the sheet for the eye rig, which drew a ghost eye. He is now filmed
  exactly as drawn (`still_face`), and his trophy shot is reframed so the waist-up drawing's edge is off frame.
- Rio's rally at the side of the stage (92.4 s): the waist-up drawing's extension showed. The front rows are now in
  the foreground, which is what the beat is about.
- Rio's shrug (145.2 s): reframed.
- Keane's clap insert (149.24 s): new house-style hands meeting on the crash, in his black sleeves.
- The button (175.3 s): the broom is in Rooney's fist, and Keane has his arms folded again (his waist-up pointing
  drawing showed its edge).

Known and left for the review:
- In the hero shot (162.8 s), Rio's shrug is the model sheet's waist-up drawing continued down, so he reads as
  wearing a long coat.
- The defender in the memory run is a dark silhouette. No defender drawing in the house style exists, so this is
  deliberate.
- The young Rooney (red 10, memory only) is the cartoon model sheet recoloured. He is labelled in SOURCES.md.

## Story checks

- Rooney leads and sings every note. He is on screen in about 72% of the running time (76% counting the young
  Rooney), from `shots.json`.
- The drums come in at bar 8 (15.19 s) as the recording's do, and stop with the bass for the breakdown (bars 80–88).
- Keane never sings. His foot taps (110–114 s), he claps once on the crash (149.243 s), and he hands over the broom
  at 173.7 s.
- No narration and no dialogue. The soundtrack is the song decoded untouched (`film/sound.py`).
- Lip sync follows `song-timing.json`: the mouths lead the voice by 2 frames, the guitar bleed at 25.3–37.7 s is
  muted, and mouths close in the rests. See ALIGNMENT.md for the lines timed from onsets.

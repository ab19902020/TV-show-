# The Overcrap Daily — "Ronaldo vs Messi"

Mark Goldbridge, Wayne Rooney and Roy Keane in Mark's studio, arguing about Messi's perfect goodbye and
Ronaldo's chaos, until Rio Ferdinand (not booked) bursts in. 1920×1080, 24 fps, about 3 min 27 s,
the original voice takes from the production pack.

**Video:** [`overcrap_ronaldo_vs_messi.mp4`](overcrap_ronaldo_vs_messi.mp4)

## What happens

| Time | Beat | On screen |
|---|---|---|
| 0:00 | Cold open: Mark's wedding analogy | Wide three-shot (Mark and Rooney at the desk, Roy standing), push in to Mark; name straps |
| 0:20 | "What song's he asking for?" / Darren | Rooney close-ups, Roy dead-pan in the reverse, held reactions after "Darren" and "Depends on Darren" |
| 0:44 | Ronaldo and Portugal | Mark gets bigger; **DEFCON 1**: red alert banner, the frame pulses red, klaxon |
| 1:02 | "Coward." / "I would." | Snap-in on Roy |
| 1:22 | Messi's state funeral | "They'll see him again." then silence on Mark's face (crickets); "No." / "Fair." |
| 1:41 | **Rio enters** | The door goes, full wide shot, Rio strides in from the Man United door and stands next to Roy |
| 1:45 | "I wasn't booked." | Straps: RIO FERDINAND — NOT BOOKED, then STILL NOT BOOKED; the **Ronaldo alarm** goes off |
| 2:07 | Forest | Rapid interruptions, "You're a Forest fan anyway", a beat, crash zoom on Mark, Rooney in fits (silent: the take has no laugh), "I AM NOT A FOREST FAN" |
| 2:31 | Ham | "Iberico." — strap: BREAKING / MOON: POSSIBLY IBERICO — Rooney satisfied, "Why are we discussing lunar meat?!" |
| 2:56 | Ending, faster | Mark thinks he's won ("Of course." / "Thank you."), "Just not about football." … "GOODNIGHT" and a hard cut to black |

## Cast and set

* **Mark Goldbridge** and **Roy Keane**, and the studio (five views: front, wide, reverse and two
  alternates) come from Pass Mic's Episode 1 "International Break Emergency" (`ab19902020/Passmic`,
  `series/ep01`), cut-outs and upscales as they were.
* **Wayne Rooney** (suit model sheet) and **Rio Ferdinand** (model sheet) come from the AnimnationStuido
  character library (`library/characters/*/reference/`), drawn in the same bold style as Mark. They are
  cut here: `episode/sheets/layout.json` → `tools/ep/cut_sheet.py` → `episode/characters/<name>/`, then a
  second 4× pass for anything seen large (`tools/ep/upscale_parts.py` → `characters_x16/`).
* Rooney sits in Gary Neville's old chair (flipped to face Mark). Roy stands by the sofa, arms crossed,
  the whole episode. Rio enters through the door on the left of the wide shot (the same door is on the
  right of the reverse view) and stands to Roy's side.

## How it's made

```bash
pip install -r requirements.txt                 # + apt-get install libegl1 (skia) in a fresh container
python3 tools/ep/render.py timings              # every line's start and length
python3 tools/ep/render.py still 63.6 138.6     # -> out/still_<t>.jpg (4K)
python3 tools/ep/render.py sheet 0 207 3 out/sheet.jpg
python3 tools/ep/render.py 1080p                # -> out/overcrap_1080p.mp4 (resumable segments)
```

* `episode/script.py` — every line as recorded (`MG_` Mark, `WR_` Rooney, `RK_` Roy, `RF_` Rio), the pack's
  delivery tags, which raw take holds which lines (`TAKES`), hand-measured cut points for takes that run
  lines together (`CUTS`) and the conversation `ORDER` with its stage beats.
* `episode/raw/` — the six supplied takes (one voice each; Mark's in three parts).
  `tools/ep/split_voice.py raw/<take> <ids...>` cuts them into `episode/audio/<ID>.mp3`; pocketsphinx forced
  alignment (`tools/ep/align.py`) gives word and phone timings (`audio/alignment.json`).
* `episode/episode.py` — the staging: cameras, per-line shot / pose / face and word-timed cuts (`STAGE`), held
  reaction shots (`REACT`), dead-pan beats (`BEAT`), Rio's entrance, the Forest and ham beats, the name
  straps, the alert graphics and the channel bug.
* `tools/ep/epengine.py` — rigs, lip sync, timeline and the 4K compositor (Pass Mic's engine, extended to four
  characters). Mark's mouths are swapped from his phoneme sheet; Roy's, Rooney's and Rio's are patches from
  their sheets' mouth rows (lips and beard), placed by the `mouth` entries in `characters/<name>/rig.json`
  and colour-matched to the drawing. Close-ups put the expression bust over a body drawing; Rio's
  waist-length gesture drawings switch to his full-body drawing whenever the frame shows below the waist.
* `tools/vec/sfx.py` — synthesised foley: door, footsteps, whoosh, the klaxon, crickets, the strap chime and
  room tone under everything. The audio cuts with the picture after "GOODNIGHT".

The production pack's scripts and director notes are in `episode/pack/`.

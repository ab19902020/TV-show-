# Wayne Rooney — The White Pelé: director upgrade handoff

**For Claude / continuation of the existing video**  
**8 October 2026**  
**Working branch:** `chatgpt/white-pele-upgrade-handoff-20261008`  
**Claude v3 baseline:** `9d40ccf11b87ff5e97d4ee3ea0d9e369a7307ac7`

## What this is

Continue this branch: it inherits the **full Claude v3 editable project** (all sources, songs, drawings, sets, overlays and the old preview). Do not remake from scratch. The user specifically wanted the ChatGPT upgrade saved into GitHub, plus a README and ZIP that Claude could build on.

**Honest provenance:** the separate ChatGPT render attempted earlier on 8 October was never recovered. The code changes below are a reproducible reconstruction of the requested director upgrades. Do not mistake the older `White_Pele_PREVIEW_720p.mp4` for a render of the new edits. This new branch has not had a complete visual render/approval pass.

## Committed source upgrades

- `episode/film/upgrade.py` adds **eight** short live-band closeups while preserving the 177.520 s song and restoring the underlying shots after the inserts: Šeško/guitar at 14.38, 137.65 and 159.12 s; Maguire/drums at 15.82, 79.70 and 118.18 s; Cunha/bass at 90.68 and 93.64 s. Each cutaway uses an existing drawn instrument/player and returns to the previous story shot.
- `episode/film/direction.py` invokes the upgrade before finalising shots. The **Goldbridge phone selfie around bar 98** now cycles through five actual shouting/cheering drawing keys, more responsive camera motion and flash/crash accents. The `vf.chat` flag enables livestream reactions. Three short **animated 'WHITE PELÉ' chorus title** moments are cued at bars 51, 95 and 106.
- `episode/film/camera.py` adds the **Goldbridge live-chat overlay, floating reaction sparks and animated chorus title**, alongside subtle beat-reactive concert lighting. These overlays must be verified at both 720p and final intended aspect ratio. No full-screen epilepsy-risk strobing is introduced.
- `episode/film/actors.py` clamps Rio's pupil-gaze offsets and adds a conservative **Roy Keane brow/gaze safeguard**. These procedural guards cannot prove the underlying image eyes and eyebrows are clean; visually inspect frame-level source art and Keane's clap.
- `episode/tests/test_director_upgrade.py` now checks eight insert/restore pairs, selfie pose keys, live-chat flag, three title cues and Python source-module syntax without requiring the render engine.

The original soundtrack, timings, artistic style and scene structure remain. Preserve Rooney as the full-time lead singer, proper instrument playing, coherent handheld microphones, cast and visual jokes.

## Claude's next steps

1. Check out this branch and read `white-pele/README.md`, `white-pele/episode/README.md`, `white-pele/episode/QA.md`, and this handoff. Check source imports, missing keys and the additional camera cuts.
2. **Visually inspect Rio's eyes/eyebrows**, the Keane eyebrow repair, Rooney's mouth, Goldbridge's hands/phone staging, chat overlays, animated titles, stage lighting and all eight band inserts. Fix any remaining double eye, floating hand, clipping, badly held mic, incorrect drum strike, lip-sync or foot-contact defects.
3. Verify Goldbridge's five drawing-key poses are all present in the library, expressive, and correctly composited with his existing phone framing. Use genuine pose/rig adjustments rather than sliding a static drawing; keep the established art style and continuity.
4. Run `python3 -m unittest discover -s episodes/white-pele/tests -p 'test_director_upgrade.py'` from the engine workspace (or the equivalent episode path). Verify musical attack alignment, 177.520 seconds, unchanged audio, 5325 frames at 30 fps for a 720p preview, continuous timestamps and mouth cues. Regenerate `shots.json` / `SHOTS.md` with the existing exporter after changing cuts. Update QA.
5. **Clear stale render checkpoints** (`episodes/white-pele/build/part*` and `.done` markers) before rendering; `--resume` can reuse old footage if part files remain.
6. Render only a **1280×720 preview** and show it to the user. Do not render 4K until the user approves the preview.

## Engine and preview commands

Use the original `white-pele/setup.sh` and the pinned animation engine `ab19902020/AnimnationStuido-` at `9b9412663640847ff4adf3ca3381414e016eef38`. Follow the original episode README for dependencies. From the engine root:

```sh
export FILM_EPISODE=white-pele PYTHONPATH=episodes/white-pele:.
EP_RES=1280x720 python3 -m studio.film white-pele still 14.5 16.0 90.9 118.5 159.4
EP_RES=1280x720 FILM_MEM_GB=12 python3 -m studio.film white-pele render --jobs 4 --chunks 24 --resume
```

The ZIP supplied separately is an **upgrade pack** (updated overlay module, portable patch script, test and handoff), not a copy of every original image/video asset. This GitHub branch is the complete authoritative editable project with the original assets inherited.

**Do not claim that this upgrade is already rendered or verified to be better on screen.** Continue from the upgraded source and verify it visually.

## 8 October — later-session reconstruction status

The user's **later** 8 October rendering session stopped near one-third of a preview and did **not** leave a recoverable render or separately checked-in code. The additional source improvements above were rebuilt against the earlier ChatGPT/Claude handoff branch and committed directly to this same branch for Claude to render. They should **not** be described as recovered finished frames, a verified visual result, or a completed 1080p/4K master.

**Review windows in the 720p preview:** 14.38–16.60, 79.70–80.26, 90.68–94.29, 118.18–118.96, 137.65–138.30, 145–149 (Goldbridge selfie and Keane clap), 159.12–160.00, plus chorus title beats at bars 51, 95 and 106. Inspect every cut-return for camera mismatch, lip-sync jumps, misleading phone props and overlaid graphics hiding faces.

**Deliver to user first:** a new 720p MP4 and, if practical, side-by-side before/after extract of the updated windows; then wait for user approval before any 4K final. Do not use the older v3 preview as proof these source edits render correctly.

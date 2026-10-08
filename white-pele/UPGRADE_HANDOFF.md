# Wayne Rooney — The White Pelé: director upgrade handoff

**For Claude / continuation of the existing video**  
**8 October 2026**  
**Working branch:** `chatgpt/white-pele-upgrade-handoff-20261008`  
**Claude v3 baseline:** `9d40ccf11b87ff5e97d4ee3ea0d9e369a7307ac7`

## What this is

Continue this branch: it inherits the **full Claude v3 editable project** (all sources, songs, drawings, sets, overlays and the old preview). Do not remake from scratch. The user specifically wanted the ChatGPT upgrade saved into GitHub, plus a README and ZIP that Claude could build on.

**Honest provenance:** the separate ChatGPT render attempted earlier on 8 October was never recovered. The code changes below are a reproducible reconstruction of the requested director upgrades. Do not mistake the older `White_Pele_PREVIEW_720p.mp4` for a render of the new edits. This new branch has not had a complete visual render/approval pass.

## Committed source upgrades

- `episode/film/upgrade.py` adds **five** short live-band closeups while preserving the 177.520 s song and restoring the underlying shots after the inserts: Šeško/guitar 14.38 s and 159.12 s; Maguire/drums 15.82 s and 118.18 s; Cunha/bass 90.68 s.
- `episode/film/direction.py` applies the upgrade before finalizing shots. Goldbridge gets new performance key changes in the existing selfie shot around bar 98; extra camera drift and phone-flash effects; and moderated stronger beams in active concert shots.
- `episode/film/camera.py` adds subtle **beat-reactive lighting** on selected stage shots, avoiding indiscriminate full-screen strobes.
- `episode/film/actors.py` clamps Rio's pupil-gaze offsets for closeups. **This is a conservative guard, not proof his underlying eye drawing is repaired**; inspect the artwork and all expressions.

The original soundtrack, timings, artistic style and scene structure remain. Preserve Rooney as the full-time lead singer, proper instrument playing, coherent handheld microphones, cast and visual jokes.

## Claude's next steps

1. Check out this branch and read `white-pele/README.md`, `white-pele/episode/README.md`, `white-pele/episode/QA.md`, and this handoff. Check source imports, missing keys and the additional camera cuts.
2. **Visually inspect Rio's eyes/eyebrows**, the Keane eyebrow repair, Rooney's mouth, Goldbridge's hands/phone staging, stage lighting and all five new band shots. Fix any remaining double eye, floating hand, clipping, badly held mic, incorrect drum strike, lip-sync or foot-contact defects.
3. Make Goldbridge truly more energetic without treating a static drawing as a sliding puppet. Upgrade genuine poses/rigs when needed; keep the established style and continuity.
4. Verify musical attack alignment, all 177.520 seconds, unchanged audio, 5325 frames at 30 fps for a 720p preview, timestamp continuity, and mouth cues. Regenerate `shots.json` / `SHOTS.md` with the existing exporter after changing cuts. Update QA.
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
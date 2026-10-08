# CLAUDE — Render the updated White Pelé music video

**Working branch:** `chatgpt/white-pele-upgrade-handoff-20261008`
**PR:** https://github.com/ab19902020/TV-show-/pull/8
**Detailed handoff:** [white-pele/UPGRADE_HANDOFF.md](white-pele/UPGRADE_HANDOFF.md)
**Source episode:** `white-pele/episode/`

## What to do

Continue the EXISTING Claude v3 Rooney music video with these newly committed ChatGPT director changes. Do **not** remake the song, redesign characters, or discard the original backgrounds. The user's interrupted later-session render was **not recovered**; this branch contains the reproducible reconstruction of its described improvements, layered on the earlier director upgrade.

### Changes that should appear in the NEW preview

- Goldbridge's **phone selfie** at bar 98: five real pose keys (cheer/shout), livelier drift, reaction flashes, chat message bubbles, floating reaction sparks and red LIVE-viewfinder UI.
- **Roy Keane:** additional brow-height and gaze clamps intended to stop eyebrow/eye intrusion. Inspect the source drawings as well: these are procedural guards, not proof every expression is fixed.
- **Eight** instrumental closeups: 14.38, 15.82, 79.70, 90.68, 93.64, 118.18, 137.65, 159.12 seconds. The original shot must return cleanly after each insert.
- Three brief **WHITE PELÉ** kinetic titles on the stage choruses (bars 51, 95, 106).
- Existing beat-reactive, restrained lighting; no distracting full-screen strobes.
- Keep Rooney lip-synced as main singer, Maguire's real drumstick hits and guitars correctly placed.

### Build and test

Use `white-pele/setup.sh` and the pinned `ab19902020/AnimnationStuido-` engine, at commit `9b9412663640847ff4adf3ca3381414e016eef38`. Follow [white-pele/episode/README.md](white-pele/episode/README.md) for full dependencies. From the engine root, with the updated episode installed at `episodes/white-pele/`:

```sh
export FILM_EPISODE=white-pele PYTHONPATH=episodes/white-pele:.
python3 -m unittest discover -s episodes/white-pele/tests -p 'test_director_upgrade.py'
EP_RES=1280x720 python3 -m studio.film white-pele still 14.5 15.9 79.9 90.9 93.8 118.5 137.8 146.9 149.3 159.4
```

**Important:** delete or invalidate stale `episodes/white-pele/build/part*` chunks and their `.done` markers **before** the render. A render with `--resume` against old chunks may silently show Claude v3 instead of these edits.

```sh
EP_RES=1280x720 FILM_MEM_GB=12 python3 -m studio.film white-pele render --jobs 4 --chunks 24 --resume
```

### QA and delivery

Review each rendered shot: Goldbridge hands and phone, graphics not covering faces, proper instrument playing, both eyes aligned, Keane eyebrow separation, exact beat cuts and mouths throughout choruses. Keep the 177.520-second source audio unchanged. At 30 fps, the 720p review has **5325 frames**.

Give the user a **new 720p MP4 preview** (and if feasible, a synchronised before/after excerpt using the *old v3* versus the *new rendered branch*). Do **not** claim the preview is already rendered, and do **not** create a 4K master until the user has approved it.

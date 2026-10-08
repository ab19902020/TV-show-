# Wayne Rooney — The White Pelé (music video)

**ROONEY'S MATCHDAY TAKEOVER.** The supplied song, untouched and at its full length (177.520 s), animated in the
studio's house style. The film opens with the pub singalong and moves through a matchday procession across Manchester
to a floodlit celebration on a stage at Old Trafford. Rooney leads and sings every note. Rio is his hype man.
Goldbridge is overexcited, with a scarf and a tiny trophy. Neville has a clipboard. Keane stands with his arms folded
throughout; his foot taps, he claps once on the crash, and he hands Rooney a broom at the end. The band plays only
where the recording does.

| File | What it is |
|---|---|
| `song.mp3` | the supplied song, byte for byte (sha256 in SOURCES.md) |
| `lyrics.md` | the corrected lyrics |
| `alignment.json`, `ALIGNMENT.md` | every word and phone timed against the recording, with a per-line report |
| `song-timing.json` | the beat grid, sections, hits and the checked mouth track the film is cut and sung to |
| `film/` | the production: `timeline.py` (bars, lines), `direction.py` (68 shots: plates, cast, camera, lights, props, show effects), `perf.py` (who sings, plays and dances where; faces), `actors.py` (drawing placement, walks, holds, foot tap, post effects), `props.py` (plates, crowds, props, effects), `things.py` (house-style props drawn in code), `sound.py` (the soundtrack), `align_song.py`, `timing.py`, `analyse.py` |
| `tools/make_art.py` | builds every derived drawing (badge, red 10 kit, Keane's head swap, Neville's clipboard, mic overlay, contact shadows) |
| `tools/export_shots.py` | exports the shot table: `shots.json`, `SHOTS.md` (start/end, location, cast, lyric, action, camera, props, lighting, transition) |
| `SOURCES.md` | the source and asset manifest: repositories with exact commits, the song, every drawing and plate and how it was treated |

## Render

The engine is `ab19902020/AnimnationStuido-` at `9b9412663640847ff4adf3ca3381414e016eef38`, with this episode in
`episodes/white-pele/` and the library overlay (`../library-overlay/` in the delivery) copied over its `library/`.
`../setup.sh` does both steps. You also need `pip install -r requirements.txt`, ffmpeg, libegl1, and the
Real-ESRGAN model in `models/` (the engine's README covers this). Run everything from the engine's root:

```sh
export FILM_EPISODE=white-pele PYTHONPATH=episodes/white-pele:.
python3 episodes/white-pele/tools/make_art.py           # derived drawings (the overlay already holds them)
for c in wayne-rooney rio-ferdinand mark-goldbridge gary-neville roy-keane; do python3 -m studio.film.art $c; done
python3 -m studio.film white-pele sound                  # build/episode_audio.wav: the song decoded, untouched
EP_RES=1280x720 python3 -m studio.film white-pele still 12.0 98.5 149.3   # spot stills -> build/stills/
EP_RES=1280x720 FILM_MEM_GB=12 python3 -m studio.film white-pele render --jobs 4 --chunks 24 --resume
#   -> episodes/white-pele/white-pele.mp4 (delivered as White_Pele_PREVIEW_720p.mp4)
python3 -m studio.film white-pele sheet    # build/contact.jpg: three frames of every shot
python3 -m studio.film white-pele lips     # build/lips.jpg: the mouths against the words
```

**Checkpoints and resume.** The render splits the film into chunks (`build/partK.mp4`). A chunk that finishes writes
`build/partK.done` with its frame range. If the render is stopped (a crash, a restart, a killed container), run the
same command with `--resume` and only the chunks without a `.done` render again. Each chunk logs to
`build/renderK.log`. To re-render one stretch after a fix, delete that chunk's `partK.mp4` and `partK.done` and
resume. The parts are joined and the untouched soundtrack is muxed onto them in one pass, so there is no audio
seam at a chunk join.

**The 4K final (only after the preview is approved).** The drawings (4x and 8x Real-ESRGAN) and the plates (4x)
are built once at a resolution above 4K, so the same build serves both. Do not resume 4K over the 720p parts: `--resume` matches frame ranges only,
not resolution, so move `build/part*` away first.

```sh
mkdir -p build720 && mv episodes/white-pele/build/part* build720/
EP_RES=3840x2160 FILM_MEM_GB=12 FILM_CRF=18 python3 -m studio.film white-pele render --jobs 2 --chunks 48 --resume
```

If the 4K encode comes out over 95 MB, the engine keeps the full-quality master as `build/master.mp4` and re-encodes
the committed copy to fit. Deliver the master.

## QA (720p preview)

See `QA.md` for this render's checks: decode, frame count and timestamps, sync at the start, the middle, the
finale and every chunk join, and the defects found and fixed.

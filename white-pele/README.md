# Wayne Rooney — The White Pelé (animated music video)

Delivery for the brief "ROONEY'S MATCHDAY TAKEOVER": the supplied song, untouched and at full length (177.520 s).

| Path | What |
|---|---|
| `episode/` | the editable project (copy into the engine as `episodes/white-pele/`): direction, performance, props, timing, the song, lyrics, alignment, the shot table, the manifest. `episode/README.md` has the render, resume and 4K steps |
| `library-overlay/` | the new and changed library files (characters, derived drawings, backgrounds), copied over the engine's `library/` |
| `setup.sh` | rebuilds the project: AnimnationStuido- at `9b9412663640847ff4adf3ca3381414e016eef38`, plus the overlay and the episode |

| `White_Pele_PREVIEW_720p.mp4` | the preview: 1280x720, 30 fps, 177.5 s, the full song. QA in `episode/QA.md` (decode, frame timestamps, sample-exact sync at the start, middle, finale and all 23 chunk joins) |
| `stills/contact_sheet.jpg` | three frames of each of the 68 shots |
| `zip/` | the production ZIP (episode, library overlay, setup, stills) in 7 parts under 25 MB, with checksums; see `zip/REASSEMBLE.md` |

**The 4K final has not been rendered.** It waits for approval of the preview (steps in `episode/README.md`).

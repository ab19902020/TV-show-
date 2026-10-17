# The Lecher vs Rio

Saeed ("The Lecher", a United fan-channel YouTuber) goes live to call Rio Ferdinand out over the Glazers. Rio
replies, and it goes downhill from there. 54.5 s, 1080p, 30 fps, with both voiceovers as supplied.

| Path | What |
|---|---|
| `The_Lecher_vs_Rio_1080p.mp4` | the finished video |
| `The_Lecher_vs_Rio_share.mp4` | the same at a lower bitrate (26.5 MiB) for sending |
| `episode/` | the editable episode for the AnimnationStuido- film engine (`episodes/lecher-vs-rio/`): script, the two voiceovers, timeline, shot list, acting, overlays/gags, sound. `episode/README.md` has the beat-by-beat breakdown and the render commands |
| `library-overlay/` | Saeed as a new library character (`characters/saeed-the-lecher/`: his model sheet and every drawing's box and face landmarks), his room (`backgrounds/lecher-vs-rio/`, from Pass Mic's fan-channel studio), and Rio's `film.yaml` with mouth landmarks on his handheld-mic drawing |

To rebuild: run `../white-pele/setup.sh` (the engine at the exact commit plus the White Pelé overlay), copy
`library-overlay/` over the engine's `library/` and `episode/` to `episodes/lecher-vs-rio/`, then follow
`episode/README.md`.

QA: the full file decodes cleanly, 1634 frames with continuous 1/30 s timestamps, and the soundtrack is muxed from
the episode's mix at 0 ms offset.

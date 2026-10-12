# The Undercard — Hearn v White (mini episode)

Original fictional satire from the *Hearn v White* production pack: Eddie Hearn bans Dana White, Dana gets in by
laundry trolley and tumbles out at Tyson Fury's feet, the two promoters negotiate themselves into a fight, and the
fight is a draw. Seven scenes, eight characters, seven sets, 78 shots, 3 min 38 s, with the delivered voice-overs.

| Path | What |
|---|---|
| `The_Undercard_PREVIEW_720p.mp4` | the preview: 1280 x 720, 30 fps, 3:38, the full mix |
| `episode/` | the editable project (copied into the engine as `episodes/the-undercard/`): the script with numbered lines, the pack as delivered (`pack/`), the voice-overs, the production (`film/`: the edit, the shots, the fight, the drawn mouths and eyes, the sound), and `README.md` with what is on screen by time, how it is made and the render steps |
| `library-overlay/` | the new library files: the eight characters (`characters/<id>/`: the pack's sheets as delivered, a cleaned copy the film cuts from, `film.yaml` listing every drawing), the seven sets (`backgrounds/boxing/`), the twelve props (`props/hearn-white/`), the new sound effects (`audio/sfx/`: boxing bells, punches, whooshes, body falls, crowd cheers and air horn, audience laughs; CC0, credited in `manifest.json`) and the updated indexes |
| `engine-overlay/` | one engine file changed: `tools/index_library.py` (the boxing sets folder) |
| `setup.sh` | rebuilds the project: AnimnationStuido- at `1213ed0aa2c79bd2da19b4a2230171296a6a67a6`, plus the overlays and the episode |

**Voices.** The delivered recordings are used for every line; there are no stand-ins. Dana's new takes replace his
first recording (take 1 for every line, "I've entered venues in worse ways" included; take 2 for the cleaner reads
of "It's boxing, Eddie." and "I want a bigger bin for the rematch."). Tyson Fury's and the attendant's new
recordings replace the old ones. Details in `episode/README.md`, "Voices".

**This version.** Every mouth is now a drawn cartoon mouth (ten shapes, from the recordings' sounds, placed on the
face, tilted and sized with it) instead of a stretched drawing; every moving pupil is a clean drawn pupil (no more
black specks). The edit is tighter (3:53 to 3:38). The crowd is built from real recordings and reacts to every beat.
The fight is choreographed: a face-off, five exchanges with anticipation and follow-through, a real hit (impact,
sweat, camera shake), ducks, a windmill, a spin, a slow-motion double miss, and the clinch.

**The 4K final has not been rendered.** It waits for approval of this preview (steps in `episode/README.md`).

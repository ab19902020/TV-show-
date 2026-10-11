# The Undercard — Hearn v White (mini episode)

Original fictional satire from the *Hearn v White* production pack: Eddie Hearn bans Dana White, Dana gets in by
laundry trolley and tumbles out at Tyson Fury's feet, the two promoters negotiate themselves into a fight, and the
fight is a draw. Seven scenes, eight characters, seven sets, 3 min 53 s, with the delivered voice-overs.

| Path | What |
|---|---|
| `The_Undercard_PREVIEW_720p.mp4` | the preview: 1280 x 720, 30 fps, 3:53, the full mix |
| `episode/` | the editable project (copied into the engine as `episodes/the-undercard/`): the script with numbered lines, the pack as delivered (`pack/`), the voice-overs, the production (`film/`), and `README.md` with what is on screen by time, how it is made and the render steps |
| `library-overlay/` | the new library files: the eight characters (`characters/<id>/`: the pack's sheets as delivered, a cleaned copy the film cuts from, `film.yaml` listing every drawing), the seven sets (`backgrounds/boxing/`), the twelve props (`props/hearn-white/`) and the updated indexes |
| `engine-overlay/` | one engine file changed: `tools/index_library.py` (the boxing sets folder) |
| `setup.sh` | rebuilds the project: AnimnationStuido- at `1213ed0aa2c79bd2da19b4a2230171296a6a67a6`, plus the overlays and the episode |

**Voices.** The delivered recordings are used for every character. The announcer's file came twice (byte-identical);
one copy is kept. One line is a stand-in voice: Dana's "I've entered venues in worse ways" (L007). His recording
says "I've entered... premium towels" at 9.3-10.8 s, and "venues in worse ways" is not in it. Send that line and it
drops in; the film retimes itself (`episode/README.md`, "Voices"). The stray "I've entered" is faded out of a
working copy of his take (`episode/voiceovers/01-dana-white-edit.wav`, made by `episode/tools/dana_take_edit.py`), so
it does not bleed into "Premium towels". The delivered mp3 is kept untouched.

**The 4K final has not been rendered.** It waits for approval of this preview (steps in `episode/README.md`).

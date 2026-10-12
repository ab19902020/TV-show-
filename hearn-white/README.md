# The Undercard — Hearn v White (mini episode)

Original fictional satire from the *Hearn v White* production pack: Eddie Hearn bans Dana White, Dana gets in by
laundry trolley and tumbles out at Tyson Fury's feet, the two promoters negotiate themselves into a fight, and the
fight is a draw. Seven scenes, eight characters, seven sets (and a second dressing room made from one), 91 shots,
3 min 48 s, with the delivered voice-overs.

| Path | What |
|---|---|
| `The_Undercard_PREVIEW_720p.mp4` | the preview: 1280 x 720, 30 fps, 3:48, the full mix |
| `episode/` | the editable project (copied into the engine as `episodes/the-undercard/`): the script with numbered lines, the pack as delivered (`pack/`), the voice-overs, the production (`film/`: the edit, the shots, the fight, the drawn mouths and eyes, the sound), and `README.md` with what is on screen by time, how it is made and the render steps |
| `library-overlay/` | the new library files: the eight characters (`characters/<id>/`: the pack's sheets as delivered, a cleaned copy the film cuts from, `film.yaml` listing every drawing), the seven sets (`backgrounds/boxing/`), the twelve props (`props/hearn-white/`), the new sound effects (`audio/sfx/`: boxing bells, punches, whooshes, body falls, crowd cheers and air horn, audience laughs; CC0, credited in `manifest.json`) and the updated indexes |
| `engine-overlay/` | one engine file changed: `tools/index_library.py` (the boxing sets folder) |
| `setup.sh` | rebuilds the project: AnimnationStuido- at `1213ed0aa2c79bd2da19b4a2230171296a6a67a6`, plus the overlays and the episode |

**Voices.** The delivered recordings are used for every line; there are no stand-ins. Dana's new takes replace his
first recording (take 1 for every line, "I've entered venues in worse ways" included; take 2 for the cleaner reads
of "It's boxing, Eddie." and "I want a bigger bin for the rematch."). Tyson Fury's and the attendant's new
recordings replace the old ones. Details in `episode/README.md`, "Voices".

**This version.**
- **A real fight ending.** After the clinch they slug it out, and every punch lands: impact stars, flying sweat,
  heads snapping back, drums speeding up. Then a double knockout: both throw an enormous cross-counter that lands
  on the same frame (white flash, freeze), and both go over like felled trees, hitting the canvas together. Stars
  circle their heads, birds tweet and their eyes roll. Saved by the bell, they spring up with their arms raised.
- **Noses.** Dana and the announcer have proper noses in every drawing (the art had none, or a hairline one).
- **Arena lighting.** A pool of light on the canvas, beams from the rig, haze and bloom.
- **Cartoon sound.** Slide whistles, the gong, the spring, the birds, a crowd that holds its breath and erupts.

The visual overhaul before it (still in):
- **Lighting.** The people are lit by the set they stand in: the room's colour, plus rim light from its lamps on the
  edges that face them. They no longer look pasted on.
- **The bin, rebuilt.** Dana rises out of the towels and is thrown out over the front. He lands at Fury's feet and
  later climbs back in. The bin's canvas is the only thing that ever hides him, so no part of him is cut off or
  see-through.
- **Mouths stay on faces.** A drawn mouth is clipped to the face, so it never opens on a glove. The boxing lines are
  said with the face clear, and the clinch shows both faces.
- **Two dressing rooms.** Eddie changes in the red corner's room, with a puff of smoke. Dana shadowboxes alone in
  the blue corner's room down the hall.
- **Eyes.** Every moving pupil is one clean round pupil. The drawn pupil, and the black wedges the art has in
  many eye corners, are painted out completely, so there are no black bits. Far eyes in shadow keep their drawing.
- **Restaged shots.** The trolley passes behind Dana, not through him. Fury points at Dana. Joshua and Eddie walk
  in. A slow tilt that crept into Dana's stance is gone. The arena referee no longer stands right behind Dana.

Earlier passes (still in): drawn cartoon mouths, clean drawn pupils, the tighter edit, the real-recording crowd, and
the choreographed fight.

**The 4K final has not been rendered.** It waits for approval of this preview (steps in `episode/README.md`).

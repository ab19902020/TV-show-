# The Undercard — Hearn v White (mini episode, v5)

Original fictional satire from the *Hearn v White* production pack, upgraded with the v5 pack: Eddie Hearn bans
Dana White, Dana bribes the laundry attendant and is delivered at Tyson Fury's feet, the two promoters bluff
themselves into a fight, and one disastrous round ends in a draw that both of them sell as a rematch. Seven scenes,
eight characters, ten sets, 92 shots, 3 min 50 s, with the recordings you supplied.

| Path | What |
|---|---|
| `The_Undercard_PREVIEW_720p.mp4` | the preview: 1280 x 720, 30 fps, 3:50, the full mix |
| `episode/` | the editable project (copied into the engine as `episodes/the-undercard/`): the v5 script, the packs as delivered (`pack/`, `pack/v5/`), the voice-overs (`voiceovers/v5/`: your new recordings, named by character), the production (`film/`: the edit, the shots, the fight, the mouths, eyes and noses, the sound), and `README.md` with what is on screen by time, how it is made and the render steps |
| `library-overlay/` | the library files: the eight characters (`characters/<id>/`: the sheets as delivered, the cut drawings, `film.yaml` listing every drawing with its face marks; new in v5: the acting heads, the attendant's steps, the paired fight drawings), the ten sets (`backgrounds/boxing/`: new in v5, the service hall's reverse angle, inside the bin, the red corner), the props, the sound effects and the indexes |
| `engine-overlay/` | one engine file changed: `tools/index_library.py` (the boxing sets folder) |
| `setup.sh` | rebuilds the project: AnimnationStuido- at `1213ed0aa2c79bd2da19b4a2230171296a6a67a6`, plus the overlays and the episode |

**Whisper check.** 68 of 76 lines are heard word for word in the finished mix; the rest are mishearings of short clips (one to listen to: the attendant's "Then no." at 0:31 is heard as "And no").

**Voices.** Your v5 recordings are used for every new or changed line; lines whose words did not change come from
the earlier takes. **One line is still a synthetic stand-in: L066, Eddie's "Don't. He's load-bearing."**, which
is not in Eddie's new file. Send that one line and it drops straight in (details in `episode/README.md`, "Voices").

**This version (the fine polish).**
- **No more stitched heads**: the acting-head close-ups (heads glued onto bodies, and Fury's and Joshua's heads with
  their shoulders cut off flat) are gone; every close-up uses the person's complete drawing.
- **Nobody cut off by the frame**: every shot is checked six times a second, and anyone a side of the frame would
  slice (a hand, an elbow, a shoulder, a sliver of someone at the edge, feet chopped off) is brought wholly in or
  left out of that shot; the speaker and whoever acts are always kept whole. The ring shots' framing is applied now
  (it was being skipped).
- **The sit-down**: both fighters drop into a crouch as whole figures with their feet on the canvas (no more torsos
  sunk below the frame), and the referee steps in between them to haul them up.
- The payment: the attendant in shot with her hand out and the notes tossed over Eddie's head into it; Eddie stops
  clear of her when he arrives; Dana folds his arms at "Fine"; Eddie's arms go up at the end.

**The v5 upgrade.**
- **The revised script** and the plan's beats: the tape on Eddie's cuff, the abandoned disguise, the shoes, the
  inside of the bin, the stare-down at the checkpoint, the payment, the silence after "Fine", the preparation, the
  promoters ducking through the ropes, the exit down the ring steps, the fare card, the end title over the
  departing trolley.
- **Close-ups on the characters' own complete drawings**: each close-up is the very drawing, pose and place the
  person has in the wide shot, framed head to chest and lip-synced; nobody's head is ever stitched onto a body.
- **The attendant walks**: step drawings with the weight on the planted foot, her hands on the handle, the
  trolley's wheels turning, a brake.
- **The fall as a chain of causes**: the wheel hits the ramp, her foot braces, the towels lurch, the lid flips,
  Dana grabs and misses, one arc to the floor, the shoes skid in after him.
- **Five fight beats** with real contact, using the paired drawings: the ceremony that fizzles out, the probe and
  the over-deep duck, glove contact each way, the ropes throwing Eddie into a real clinch, and the glove clash,
  the wobble and both going down together before the referee hauls them up. One impact graphic.
- **The ending on the floor**: they come down the ring steps and the bin waits at ringside, on the arena floor in
  front of the apron (no more hovering beside the ring), and no ring rope is ever drawn across anyone.
- **Dana's nose**: one nose, his own drawn one made clearer, instead of a second nose inked over it.
- **Checked shot by shot**: every shot was rendered and inspected for noses, mouths, eyes, feet on the floor,
  scale and framing. Noses were added to Dana lying on the floor and climbing, the referee kept clear of the
  close-ups, the red corner's fighters set at one depth, the announcer kept out of the decision close-ups, and the
  close-ups framed so their edges never show.

Earlier passes (still in): drawn cartoon mouths clipped to faces, clean single pupils, inked noses, set lighting
and arena lighting, the real-recording crowd and cartoon sound.

**The 4K final has not been rendered.** It waits for approval of this preview and the one missing line (steps in
`episode/README.md`).

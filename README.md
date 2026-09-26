# TV show scenes

Animated TV-studio scenes with lip-synced characters.

| Scene | Video |
|---|---|
| [Roy Keane rant: The Overlap studio](roy-keane-overlap-rant/) | [`roy_keane_overlap_rant.mp4`](roy-keane-overlap-rant/roy_keane_overlap_rant.mp4) |
| [Jim Ratcliffe: INEOS office, Monaco](jim-ratcliffe-ineos-office/) | [`jim_ratcliffe_ineos_office.mp4`](jim-ratcliffe-ineos-office/jim_ratcliffe_ineos_office.mp4) |

## Make a new video

Open a Claude Code session on this repo, attach the files, and type `/new-scene` followed by your notes.

**Send:**
- **Character sheet**: the full-body turnaround, head expressions, arm poses and leg/walk poses on a plain
  background (like Jim's `src/sheet.png`). A separate mouth-shape sheet if you have one (like Jim's
  `src/mouths.png`).
- **Background**: the set, 1672×941 or similar.
- **Voice clips**: any number, in any order. The order is worked out from what's said.
- **Director's notes**: what he does on which line, where he walks, where he sits, how he exits, and anything
  special (props, a camera push). Leave it out and Claude writes a plan for you to approve first.

Example: `/new-scene This is Gary Neville in the Sky studio. Stands at the touchscreen for the intro, walks to
the desk on "anyway", points at camera on the last line and storms off.`

Claude builds the scene in a new folder, checks it against the quality notes in
`.claude/skills/new-scene/SKILL.md` (no see-through parts, head on the neck, matching collar, correct walks,
lip sync), renders it, pushes it and sends you a preview. The review tools it uses are in `tools/`.

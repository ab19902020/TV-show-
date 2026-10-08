# The White Pelé — source and asset manifest

Every input this production uses, where it came from, and what it is used for. Runway is not used, and this
production generated no images itself. The upgrade pack below was supplied by the client: its notes say it was made
with built-in image generation from reference frames of the first preview. It is used as supplied (cut out and
upscaled only). Every other drawing is a recomposition or recolour of the approved artwork below, or is drawn in code
in the house style (`film/things.py`, `film/props.py`, `tools/make_art.py`).

## Repositories (exact commits)

| Repository | Branch | Commit | Used for |
|---|---|---|---|
| `ab19902020/AnimnationStuido-` | `ccr-703a2362-lbr343` | `9b9412663640847ff4adf3ca3381414e016eef38` | The film engine (`studio/film`), the character library, backgrounds, United Road's pub-stage production (`episodes/united-road-take-me-home/film/`) whose measurements, plate cleaning, kit occlusion and connected instrument poses are reused |
| `ab19902020/TV-show-` | `claude/animated-episode-production-yvajlc` | `01a2dc13f52a2abcba66390968bcb39035ad5a8a` | The Overcrap episode (Goldbridge, Roy, Rooney, Rio cast — checked; Goldbridge and Roy are Pass Mic's art, see below); the Manchester United documentary backgrounds (stadium exteriors, tunnels) |
| `ab19902020/TV-show-` | `claude/new-session-ow0mwl` (from `a6ad4f7a`) | — | The `rooney-g-unit` scene's approved handheld-microphone drawings of Rooney and Rio; this production's delivery branch |
| `ab19902020/Passmic` | `main` | `745870f7dde0910d762374a272e53098076390f9` | Mark Goldbridge, Gary Neville (Style 1 sheets and their cut-outs) and Pass Mic's Roy bodies (`series/ep01`) |

## The song

| File | sha256 | Notes |
|---|---|---|
| `song.mp3` (supplied as `ChorusTerraceStyleKeepItSimpleRemasteredx2Remix (3).mp3`) | `6d4c6237517ce0e1307872bd963d90481729db29812bcfdc99c50a3c7c35e1c4` | 48 kHz stereo MP3, container 177.552 s; decoded 8,520,968 samples = **177.520 s** (ffmpeg and librosa decode it identically, 0-sample offset). Used untouched. |

## Characters (identity confirmed from each `character.yaml`, model sheet and the drawings themselves)

| Character | Drawings used | Source |
|---|---|---|
| **Wayne Rooney (identity master)** | `mic`, `micup` (+ `micup-fg`, the raised mic as its own layer) | `TV-show-/rooney-g-unit/src/art/rooney-mic.png`, `rooney-mic-raised.png` (the approved handheld-mic drawings), copied to `library/characters/wayne-rooney/reference/poses/`; the performance outfit's red badge added by `tools/make_art.py rooney` |
| | `walk1-3`, `back`, `q34`, `shrug`, `lean` | the young cartoon model sheet `library/characters/wayne-rooney/reference/model-sheet.png`, with the badge (`reference/white-pele/model-sheet-badge.png`) |
| | `kit-front`, `kit-run1-3`, `kit-shrug`, `kit-nod` (**younger Rooney, red number 10 kit — football memory only**) | the same model sheet recoloured: shirt red with a white 10, white shorts, black socks (`reference/white-pele/model-sheet-kit10.png`, `tools/make_art.py kit10`) |
| Rio Ferdinand | `mic`, `laugh` | `TV-show-/rooney-g-unit/src/art/` (approved) |
| | `front` (kit), `folded`, `rally` (the sheet's "warning" hand), `shrug`, `laughbent`, `walk1-3`, `run1-2`, `back`, `q34` | `library/characters/rio-ferdinand/` kit and model sheet |
| Mark Goldbridge (new to the library: `library/characters/mark-goldbridge/`) | `stand` (the sheet's header strip and the paper between the legs cut away: `tools/make_art.py mark-stand`), `pointing`, `fistpump`, `shrug`, `armsdown`, `shouting`, `laughing`, `shocked`, `smug`, `walk1-4`, `front`, `q34`, `back`, `cheer` | Pass Mic `series/ep01/sheets/mark.png` and its cut-outs (`characters_x16/mark/*`, `characters/mark/*`) |
| Gary Neville | `stand`, `walk1-4`, `armsdown`, `pointing`, `clipboard` (his phone made a clipboard) | Pass Mic `series/ep01/sheets/gary.png` and cut-outs (the library's own Neville kit is an off-style stand-in) |
| Roy Keane | `crossed`, `stand`, `crossed-cu`, `walk1-4`, `point` | Pass Mic's Roy bodies (his head on Gary's Style 1 bodies) **with the library's own cartoon Roy head** put on in place of Pass Mic's semi-realistic one (`tools/make_art.py roy`, `roy-point`), so Keane matches the house style United Road used |
| Harry Maguire, Benjamin Šeško, Matheus Cunha | `drumming`, `guitar`, `bass` | the approved connected-hand concert poses in the library (United Road) |
| Supporters | Evra, Carrick, Bruno, Tielemans, Lammens, Holland, Shaw, Mainoo and the squad sheet's players | `library/characters/*/film.yaml` (as United Road's crowd) |

## Backgrounds

| Plate | Source | Treatment (`film/props.py`) |
|---|---|---|
| F, FC, PUB | `library/backgrounds/pub-and-restaurant/united-pub-stage(-crowd).png`, `pub.png` | United Road's: mic stand painted out, fans cut out, the room at night |
| ST | `library/backgrounds/street/manchester-matchday.png` | graded to dusk, lamps and windows lit, stadium glow, red-and-white bunting drawn across the road |
| MW | drawn | a brick gable with a painted panel; the lettering THE WHITE PELÉ is live type (`MURAL_TEXT`) |
| EXT, EXT2, TUN, TUNP | `TV-show-` documentary backgrounds `stadium-exterior/cinematic-stadium-at-crimson-dusk.png`, `dusk-at-the-red-lit-stadium.png`, `stadium-tunnel/cinematic-red-stadium-tunnel.png`, `stadium-tunnel-to-the-pitch.png` (copied to `library/backgrounds/stadiums/`) | upscaled 4x |
| OT, OTS | `library/backgrounds/stadiums/old-trafford.png` | night under floodlights; the stands filled with a drawn crowd layer (bounces, scarves, a travelling scarf wave); OTS adds the stage and truss on the pitch |
| MEM | `library/backgrounds/stadiums/red-seated.png` | a warmer afternoon grade for the memory; drawn crowd |

## Props

Library: `props/lunch/football.png`, `props/music/microphone.png`, the pub's drum kit (cut from the pub plate for the
stadium stage). Drawn here in the house style: Keane's clapping hands (`props.clap`), the tiny trophy, the broom, three United scarf patterns, the clipboard,
flags, confetti (engine), the street sign (live type `SIGN_TEXT`).

## The upgrade pack (supplied with the second round of direction)

`White_Pele_Backgrounds.zip` and `White_Pele_Characters_Props_Direction.zip`, merged into `upgrade-pack/` (the sheets,
`ASSET_PROMPTS.json` and `CLAUDE_DIRECTOR_NOTES.md` as delivered). Plates are about 1672 x 941, so they are not native 4K.

| Asset | Where it went | Treatment |
|---|---|---|
| BG01–BG10 | `library/backgrounds/white-pele/bg01…bg10-*.png`, plates B01–B10 (`film/props.py` UP) | upscaled 4x; empty stands on B07–B09 filled with the drawn crowd layer (`CROWD_ZONES`) |
| CH01 Rooney performance | `wayne-rooney` drawings `perf-stand/reach/lean/point/back/kneel` | cut whole, Real-ESRGAN 4x (`tools/make_art.py upgrade`); perf-stand has hand-set face marks for lip sync |
| CH02 Rooney walk | `pwalk1-4` (side cycle), `pwalk-back`, its mirror `pwalk-back-m`, `pwalk-back34` | as above; the back key mirrored for the other step |
| CH03 Rooney football (**young Rooney, red kit: memory/tribute only, not a specific match**) | `ball-ready/run/strike/bicycle/land/celebrate` | as above |
| CH04 reactions | Rio `palms`, `laughbent2`, `scarf`; Keane `folded`, `clap`, `broom` (+ `broom-hand` and the broom as its own prop, `upgrade-derived`) | as above |
| CH05 supporters | new library character `white-pele-supporters` (`fan1-6`) | as above; two smiles closed for lip sync (`close_mouth`) |
| PR01 props | `library/props/white-pele/*` (ball, mics, sticks, scarf, guitar, bass, trophy) | cut and 4x; the football replaces the lunch ball |

# All or Something: The Mole

Lisandro Martinez is sure Manchester United has a mole, and that it is the director of football, Jason Wilcox. He
goes undercover in a hedge, then in a pot plant. At three o'clock Wilcox locks his door, closes the blinds and unzips
his United top: a Leeds top underneath, the Leeds live page on BBC Sport. Leeds score, Wilcox sings, the plant
explodes: "I KNEW IT!" Then come the excuses, a seventy-minute PowerPoint, the CEO in a City scarf, and the spy
getting spied on. 3:49, 1080p. The voices are the user's Clony AI recordings.

## What happens

| Time | Scene | Gags |
|---|---|---|
| 0:00 | **The hedge.** Drone push over Carrington (CARRINGTON, 06:12). The hedge has binoculars. They turn to the lens, come down: Licho, in camouflage paint, "Shhh. I am not here." A long slurp of mate. | title card |
| 0:23 | **The evidence.** Talking head (LISANDRO MARTINEZ, Defender. Amateur detective.). The conspiracy board: the camera whips to each photo as he names the club (Blackburn, 1995: WON THE LEAGUE (AGAINST US); LEEDS 1999-2004 !!!; MAN CITY ACADEMY; SOUTHAMPTON (fine)). He has to compose himself after "Manchester City". Exhibit A: the white mug. The 2019 Spygate back page spins in. | one limp clap |
| 1:07 | **The operation.** The plant (with Licho's boots) shuffles towards the DIRECTOR OF FOOTBALL door. Inside the plant: eyes. Wilcox on the phone ("fully aligned... one process"), hangs up, the lock clicks, the blinds come down, and the plant is already in the corner. 2:59... 3:00: he unzips. Slow motion, a glow, a sigh, a saxophone: a white Leeds top. BBC Sport, Leeds live, refresh, refresh. "Come on, Leeds." The leaves part: "Madre mia." GOAL. Confetti. The plant explodes and Licho rises out of it: "I KNEW IT!" | three screams, the freeze frame, R.I.P. PLANT |
| 1:55 | **Busted.** Scouting, method scouting, "you were in a plant". "Turn around": WILCOX across the back, signed "To Jason. Love, Jason. x". The laptop pings a penalty: "Oh, that's never a penalty, ref!" "Say it." He physically can't: sweat, the eye twitches, "...really well coached, to be fair." | Licho's facepalm |
| 2:34 | **The right of reply.** WHY I AM DEFINITELY NOT A LEEDS FAN, 1 / 214. Commitment up 11 % (one bar, no axis). "Up from what?" 70 MINUTES LATER: slide 213, Licho asleep. "You know who else does this? Bielsa." Wilcox's own talking head: "Red through and through.*" / "*Mostly." | the Zs |
| 3:04 | **Going to the top.** "Omar! We have a mole!" Omar Berrada in a sky-blue City scarf, a City mug, CITY TV on his monitor. Frozen. One cricket. "...I knew it." | |
| 3:19 | **The spy who spied me.** THAT NIGHT. Licho cheers Mac Allister scoring for Liverpool on his tablet. A plant in the corner that wasn't there before: Wilcox, "I KNEW IT!" "It's Argentina! It's different!" "He plays for Liverpool, Lisandro!" "...It's a red shirt." Pointing at each other: freeze. NEXT WEEK, outside Sir Jim's office: two hedges, one with Licho in it, one raising a white mug. | the end card |

The script's two unrecorded lines (L061, the narrator's "Next time..."; L063, Wilcox's "We're not here.") are left out:
the end card and the NEXT WEEK caption carry them.

## How it's made (studio/film)

- `voiceovers/`: the four Clony AI files (narrator, Lisandro in two parts, Wilcox), identified by transcription.
  `film/lines.py` cuts every line out of them word-exact.
- `film/timeline.py`: the dialogue edit and its marks. `film/direction.py`: 63 shots; most are wrapped in
  `props.comp`, which switches drawings on cue and adds the gags (the unzip wipe and glow, the soil burst and rise,
  crash zooms, shakes, confetti, sweat, Zs, freeze frames, the night grade). `film/perf.py`: the acting.
  `film/props.py` and `film/sprites.py`: the hedge, the plant (its front fronds part to show who is inside), the
  binoculars, the mug, the blinds, the door sign, the slides, the inserts. `film/sound.py`: the mix (strings,
  slurps, the cheesy sax, stings, record scratches, the cricket).
- **Cast.** The user's cut-out poses in the house 2.5D style: Wilcox (pockets, arms crossed, phone, clipboard, walk,
  back, shrug, point) and Licho (stand, arms crossed, point, facepalm, shrug, tablet, crouch), upscaled 8x for close-ups
  (`up: true` in film.yaml, new in studio/film/art.py). `tools/variants.py` paints the costume changes onto them:
  Wilcox's white Leeds top (the ink and folds kept, blue stripes, a Leeds shield for the United badge, WILCOX and his
  own autograph on the back), Licho's camouflage paint, the screams, and Omar's City scarf.
- **Sets:** Carrington (training-ground/carrington-quiet), the manager's office (club/managers-office) as Wilcox's
  office, and five documentary sets added to the library under `documentary/`: the interview chair, the corridor,
  the tactics room, the CEO's office and the locker room.

```sh
python3 -m studio.film the-mole lines
python3 -m studio.film the-mole sound
EP_RES=960x540 python3 -m studio.film the-mole still 25 72 96 108.6 133 155.5 190 219
python3 -m studio.film the-mole render --jobs 4 --chunks 16 --resume   # -> the-mole.mp4
```

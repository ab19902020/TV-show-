# The Lecher vs Rio

Saeed ("The Lecher", a Manchester United fan-channel YouTuber) goes live to call Rio Ferdinand out over the
Glazers. Rio replies, first as a post and then as a video from his podcast studio. It goes downhill from there.
54.5 s, 1080p, both voices as recorded by the user.

## What happens, by time

| Time | Shot | Gag |
|---|---|---|
| 0.0 | Saeed's stream goes LIVE: he leans into his webcam | the live chat starts: "WE'RE LIVE LADS" |
| 1.6 | "...a microphone, a massive platform and millions of followers" (pointing at the lens) | a follower count spins up to 14,300,000 |
| 6.0 | "But when it comes to the Glazers..." arms folded, then a push in on his angry face | chat: "GLAZERS OUT", "so... every week then" |
| 10.2 | **Old Trafford, 2-0 down**: a drained, empty stadium, wind, a cricket, a tumbleweed | |
| 11.9 | **Rio's reply**: a post that types itself out while he reads it, its replies and likes going mad | keyboard clicks |
| 16.4 | Back on the stream with Rio's clip in the corner: Saeed checks himself out; on "timber" he looks down at his belly | chat: "NOT THE MIRROR", "rio cooked him" |
| 18.2 | Rio, full screen: "You've got tits for God's sake," and he cracks up at his own joke | |
| 20.7 | **"TITS!"**: crash zoom, screen shake | the chat explodes |
| 21.8 | "Brilliant Rio, at least mine are visible." (Rio, arms folded, in the corner) | |
| 24.9 | Rio, stung | |
| 25.4 | "Twenty years of the Glazers..." (counter: 20 YEARS OF THE GLAZERS), then arms across his chest on "body checks" | |
| 30.8 | "You're a pundit, not the bloody fashion police." | crash zoom and red/blue sirens on "police" |
| 34.1 | "And if you're wondering why I'm fat Rio..." (thinking) | |
| 36.4 | "...eat my feelings." | empty plates stack up on the desk, one a beat, clinking |
| 41.3 | Rio: "That's not my fault." (shrug) | |
| 43.2 | "Neither are the Glazers." dead flat, slow push | |
| 45.4 | **Split screen**: "Funny how we're both avoiding responsibility, eh, Rio?" | |
| 48.9 | The silence: they both look away, look back, a typing bubble... and nothing | one cricket |
| 51.3 | **End card**: Saeed's post. "Rio Ferdinand has limited who can reply." THE LECHER vs RIO | |

## How it's made (studio/film)

- `voiceovers/saeed.mp3`, `voiceovers/rio.mp3`: the two uploaded recordings. `film/lines.py` cuts every line of
  `script.md` out of them word-exact (Whisper + forced alignment) -> `build/lines/`.
- `film/timeline.py`: the dialogue edit, with room left for the gags.
- `film/direction.py`: the shot list. Every shot is drawn by `props.compose`, which renders an inner close single
  (Saeed at his desk on plate Y, Rio in his podcast studio on plate P) and puts the stream on it: the player
  chrome, the LIVE badge and viewer count, a live chat that reacts to the words, Rio's clip in a corner, counters,
  crash zooms, sirens, the plates. Inserts: Old Trafford, the two posts, the split screen.
- `film/perf.py`: the acting: each line's delivery (brows and smile), stressed words, looks to the lens, the glance
  down at his belly, the looks away in the silence. The lip sync opens the mouth on each drawing (procedural
  mouth on the character's own face, studio/film/face.py).
- `film/sound.py`: the lines, room tone, and synthesised pings, whooshes, keyboard clicks, cricket, siren, crash
  hits and plate clinks.

**Saeed's body.** His sheet's expression cells are heads with a stub of shoulder, so filmed alone the head floats.
`tools/heads_on_body.py` puts every expression head on his full-body front drawing. Each head is scaled chin to chin
and centred on the body's face. Below the cheekbones only the face is kept (skin, ears, the open mouth's inside, and
the jaw's outline): the bust's shoulders and collar go, and his own collar and shirt show under the double chin. This
gives `b-head`, `b-neutral`, `b-angry`, `b-confused`, `b-shouting`, `b-scared`, `b-happy`, `b-suspicious`,
`b-disgusted` and `b-silly`, each with eye, mouth, head-box and neck landmarks. The head nods and tilts on the body,
the mouth lip-syncs on head, neutral and angry, and the drawn expressions swap on the words.

**His chair.** `direction.room()` frames his room per shot from the framing: his gaming chair is centred behind him,
its headrest just above his head, and the room's own desk lines up exactly under the desk in front of him. He sits
in his chair at every size. The United mug that sat in front of the chair (and covered his chin) is painted out of
the plate, its reflection too (`props.plate_image`).

**Acting.** He pumps forward on every stressed word, sinks when Rio calls him out, leans into the rant, slumps on
"eat my feelings" and sits back pleased at the end. He shakes his head on "Neither", and tilts it on "Brilliant
Rio", "why I'm fat" and "Funny how...". Gestures change on the words: jabbing at the lens, palms up, arms folded,
chin in hand.

Saeed (`library/characters/saeed-the-lecher/`) is filmed from whole drawings cut from his model sheet and upscaled
8x: front, three-quarter and side heads, nine expressions, five upper-body gestures, legs and outfits. His
open-mouth drawings (`head`, `neutral`, `pointing`) have the mouth painted shut (`close_mouth`) so the lip sync
can open it on the voice. Eye and mouth landmarks are set by hand. Rio's handheld-mic drawing got mouth landmarks
too.

Sets: `library/backgrounds/lecher-vs-rio/fan-channel-desk.png` (Pass Mic's fan-channel studio, Saeed's room), the
library's podcast studio (Rio) and Old Trafford.

```sh
python3 -m studio.film lecher-vs-rio lines
python3 -m studio.film lecher-vs-rio sound
EP_RES=960x540 python3 -m studio.film lecher-vs-rio still 0.4 20.9 36.9
python3 -m studio.film lecher-vs-rio render --jobs 4 --chunks 16 --resume   # -> lecher-vs-rio.mp4
```

# Evra and Ronaldo: "The Lunch"

**Final video:** [`evra_ronaldo_lunch.mp4`](evra_ronaldo_lunch.mp4) (1080×1920 portrait, 30 fps, 80.3 s, the original
recording with music and sound effects)

Patrice Evra tells the story of going to Cristiano Ronaldo's house for "a gentle lunch" after training (they were team-mates at United from 2006 to 2009), which
turned into a garden two-touch session, a swim, a sauna and a jacuzzi. Then he tells how Rio Ferdinand beat Ronaldo at
table tennis and Ronaldo practised for two weeks to beat him back. The sound is Evra's original recording, whole (his
voice is never cut or edited), with a comedy score and sound effects under and around it. The picture is the flashback in
the house cartoon style.

## Who speaks on screen

The characters act silently under Evra's narration. They only lip-sync the lines he quotes:

| Time | Who moves their mouth | Line |
|---|---|---|
| 8.3 | Evra, to camera | "Exactly, I think we should stay at the training ground." |
| 11.5 | Ronaldo | "Let's go and having a lunch after training." |
| 26.8 | Ronaldo | "Let's go in the garden and play two-touch." |
| 29.3 | Evra | "I said, Cristiano, we just finished." |
| 33.3 | Ronaldo, from the pool | "Let's go for swim." |
| 35.1 | Ronaldo | "After that, let's have a sauna, jacuzzi." |
| 37.0 | Evra, in the sauna | "Cristiano, why we didn't stay at the training?" |

## What happens

| Time | Shot | What you see |
|---|---|---|
| 0.0 | Carrington, 2006–2009 | Evra is bent double, tongue out and sweating, while Ronaldo does keepy-ups behind him. |
| 3.3 | "a gentle lunch" | Evra daydreams: a thought bubble full of plates of food and a jug, sparkling. |
| 5.6 | "very competitive" | Ronaldo in close-up on a red sunburst, with speed lines and a twinkle in his eye. |
| 8.3 | Evra to camera | "I think we should stay at the training ground." |
| 10.6 | The invite | Ronaldo thumbs over his shoulder. Evra is dead on his feet until he hears "lunch", then pops up rubbing his hands. |
| 14.1 | The house | Evra skips up the path. |
| 15.3 | The table | A few plates. Evra looks at his food, then at Ronaldo, who eats with relish: he leans in, takes a bite, chomps and chews. |
| 19.3 | "Plain white chicken." | Close-up on the plate. |
| 20.4 | Waiting | Evra looks hopefully at the kitchen door. A tumbleweed rolls past the doorway. |
| 21.7 | "No juice, just water." | A glass of water slides in. Evra stares at it and sweats. |
| 23.8 | "Quickly a lunch" | Fast-forward ×8: Ronaldo clears his plate and vanishes in a cloud of dust. |
| 26.6 | The garden | "Let's play two-touch." Ronaldo flicks the ball up. |
| 29.1 | "We just finished." | Evra pleads. |
| 31.1 | Two-touch | A proper passing distance apart, with a full-size ball. Crisp passes from Ronaldo, a weak one back from Evra. The last ball BONKs off Evra's shin. |
| 34.4 | The pool | Ronaldo swims laps past Evra, who clings to the edge. Then Ronaldo pops up: "sauna, jacuzzi". |
| 37.0 | The sauna | Ronaldo does jump squats with a thumbs up. Evra sweats on the bench: "why didn't we stay at training?" |
| 40.3 | The jacuzzi | Evra finally relaxes, eyes closed, while Ronaldo swims laps of the jacuzzi. Every time he passes, a wave crashes over Evra's face: SPLOSH!, then water runs down it. |
| 44.6 | "I saw the goal today" | Ronaldo scores at Carrington: GOAL, confetti, and a "SIUUU!" jump. |
| 47.4 | "Christian Dior" | Ronaldo in a bathrobe, on pink with sparkles. He winks on "playboy". |
| 50.3 | "Christian the warrior" | He is in the ready stance in red light, with dust and speed lines. |
| 52.3 | "really happy for him" | Evra in a robe, beaming. |
| 53.9 | "He's a machine" | Ronaldo does jump squats while Evra watches. Ronaldo's battery reads 100%, then "∞" on "machine". Evra's is at 2% and blinking. A rep counter runs past 997. |
| 57.0 | Table tennis | Side-on, real-size bats: a proper rally (PING! PONG!) with both swinging, then Rio smashes the winner past Ronaldo's ear. RIO 11 - 9 CR7. |
| 60.7 | "so close" | Ronaldo is confused. |
| 61.7 | "determined" | Ronaldo, intense, on a sunburst. |
| 63.4 | "Rio has to tell the truth" | Rio, smug, holding his bat up. |
| 65.5 | "Rio beat him" | The smash goes past again. Rio folds over laughing: RIO WINS. |
| 67.4 | "we scream" | Evra and Rio crying with laughter: HAHA. |
| 68.6 | "so angry" | Ronaldo turns red, with steam coming out of his ears. |
| 70.3 | The cousin | A box marked TABLE TENNIS / FRAGILE drops on the path. Ronaldo is delighted. |
| 72.5 | "Two weeks later" | At night in his garden, Ronaldo against a ball machine, hammering every return into a cardboard Rio with a target on his chest. |
| 73.8 | The rematch | On "he beat Rio", Ronaldo's smash hits Rio on the forehead: BONK!, stars, CR7 WINS. |
| 76.0 | Rio | Arms folded, with a rain cloud of his own. |
| 76.9 | "That's Cristiano Ronaldo" | Ronaldo winks on a red-and-gold sunburst: CR7. |
| 78.1 | "He don't want to lose any game" | Back at Carrington, Ronaldo is still doing keepy-ups and beckoning. Evra keels over flat: K.O. |

## Sound

Everything is synthesised from numpy/scipy (no samples, no libraries), deterministically, and every cue is keyed to the same
times `direction.py` draws it at, so a change to a shot's timing moves its sound with it.

- **Music** (`score.py`): a playful comedy score in A minor / C major, a different groove for each part of the story, and
  every section starts on the picture cut. Morning-training marimba and pizzicato; a tiptoe for the house; a lonely nothing for
  the empty doorway and glass of water; a speeded-up chase for the fast-forward; funk for the garden; steel-drum-ish marimba for
  the pool; slow and hot for the sauna; lounge vibes for the jacuzzi; brass and a roar for the goal; disco shimmer for "Christian
  Dior"; taiko for the warrior; a pulsing machine for "He's a machine"; a 150 bpm tick for the table-tennis rally (then it
  cuts dead on the winner); a heartbeat for "determined"; a rising boil for "so angry"; a night-time pulse locked to the ball
  machine (one ball every 0.32 s); a triumph on the rematch; and back to the morning theme with a last chord on the K.O.
  It sits about 16 dB under his voice and lifts in his pauses.
- **Effects** (`sfx.py`, cued in `audio.py`): a whoosh on every whip pan, the keepy-ups, panting and sweat drops, the thought
  bubble pop, "lunch" boing and hand-rubbing, the skip up the path, plates, every bite and chew, the glass of water sliding
  in, the tumbleweed and a cricket, the fast-forward whirr with rapid chomps, the vanish and dust cloud, the ball flick, each
  kick, the BONK on his shin, splashes, laps and the sauna thumps, the SPLOSH waves (and the water running off his face), the
  goal (kick, net, crowd, confetti, SIUUU and the landing), camera flashes on "Christian Dior", the warrior's taiko and shing, the
  battery beeps and the power-up on "machine", every table-tennis PING / PONG / bounce / smash / miss, the kettle whistling
  from his ears, the box falling and landing, the ball machine and the cardboard Rio, the BONK on Rio's forehead, the sad
  trombone, the keepy-ups again, the fall and the K.O. bell. The full list with times is in `soundtrack_cues.json`.
- **Ambience** under each place: air and birds outdoors, room tone in the kitchen, the pool hall, steam in the sauna, jacuzzi
  bubbles, night crickets, rain on Rio.
- **Mix**: each effect is set against how loud his voice is at that moment (it can never swamp a word; the big comedy hits
  may reach slightly above it), then the whole mix is normalised to -16 LUFS integrated / -1.5 dBTP, 48 kHz, AAC 256k.
  Stems are written to `build/audio/` (voice, music, effects, ambience).

## How it's made

- `align.py`: the hand-corrected transcript, force-aligned to word and phone timings (`words.json`, pocketsphinx).
  Every cue in `direction.py` is keyed to a spoken word, for example `W("lunch", 2)`.
- `upscale.py`: 4× Real-ESRGAN (anime) for every sheet and background (`build/up/`).
- `parts.py`: every drawing is cut out of the sheets by its box. Its paper is flood-filled from the edge, and trapped
  gaps are marked by hand. You can check the cut-outs on magenta (`qa/parts.jpg`).
- `engine.py` and `cast.py`: rigged cut-outs.
  - The head layer is found from the eyes, so heads tilt and nod on the neck with no gap.
  - The upper body leans and breathes about the waist.
  - Arms and legs swing as solid pieces: the fork arm, the beckoning hand, the kicking leg. What was behind them is
    painted in.
  - Shirt numbers are flipped back when a drawing is mirrored, so "3" and "7" always read the right way.
  - Lip sync is the house jaw-drop face engine (`face.py`), driven by the aligned phones and the recording's loudness.
- `performance.py`: keyed eyes, brows, smiles and blushes, plus always-on life: breathing, weight shift, head drift,
  eye darts, irregular blinks and Evra's panting.
- `direction.py`: the 39 shots. `fx.py` draws the cartoon effects in the house ink style: thought bubbles, sparkles,
  sweat, steam, dust, confetti, speed lines, batteries, splashes and ripples, the table-tennis table and paddles, and
  the delivery box.
  - Occlusion: the dining table and the pool deck are cut from their own plates and laid over the characters.
  - Swimmers are drawn only above a moving waterline.
- Eating (`direction.py` `eating()`): the fork arm stays in the drawing. A bite is a lean in, a wide mouth, the
  forkful going in and a chomp, then chewing with the jaw. The drawn food is taken off the fork and the film draws
  the bites.
- Table tennis: Rio is the approved Rio from the G-Unit film holding a bat (his microphone painted out), and Ronaldo is
  his 3/4 view with the near arm rigged. Each bat is drawn under the hand that grips it, and each arm swings through
  the ball. The table's ends are placed from where the bats meet the ball, so every hit lands on a bat. Rio's
  close-ups use his large hero drawing and the high-res laughing pose.
- Footballs are real size (`BALL`, about a head across). Cuts to a new place get a whip pan, and every shot has a soft
  vignette.
- `render.py`: renders in parallel chunks, then adds the original recording, encoded once to AAC 320k, with no edits.
- `audio.py` (with `sfx.py` and `score.py`): the music and sound effects, mixed with the recording and muxed onto the picture
  (see "Sound" below). Run it after `render.py`.

To rebuild from scratch:

```sh
pip install -r ../micah-richards-50-caps/requirements.txt pocketsphinx
python3 upscale.py && python3 parts.py && python3 align.py && python3 render.py
```

The model comes from GitHub releases: `models/RealESRGAN_x4plus_anime_6B.pth`.

To review:
- `python3 tools/stills.py out.jpg 12.5 31.5 66.8` gives frames at those times.
- `--run T0 T1 --step 2` gives consecutive frames.
- `python3 tools/rigcheck.py out.jpg e_tinylunch` shows a rig posed three ways on magenta.

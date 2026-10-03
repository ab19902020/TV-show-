# Evra and Ronaldo: "The Lunch"

**Final video:** [`evra_ronaldo_lunch.mp4`](evra_ronaldo_lunch.mp4) (1080×1920 portrait, 30 fps, 80.3 s, the original
recording)

Patrice Evra tells the story of going to Cristiano Ronaldo's house for "a gentle lunch" after training in 2008, which
turned into a garden two-touch session, a swim, a sauna and a jacuzzi. Then he tells how Rio Ferdinand beat Ronaldo at
table tennis and Ronaldo practised for two weeks to beat him back. The sound is the original recording, whole and
untouched. The picture is the flashback in the house cartoon style.

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
| 0.0 | Carrington, 2008 | Evra is bent double, tongue out and sweating, while Ronaldo does keepy-ups behind him. |
| 3.3 | "a gentle lunch" | Evra daydreams: a thought bubble full of plates of food and a jug, sparkling. |
| 5.6 | "very competitive" | Ronaldo in close-up on a red sunburst, with speed lines and a twinkle in his eye. |
| 8.3 | Evra to camera | "I think we should stay at the training ground." |
| 10.6 | The invite | Ronaldo thumbs over his shoulder. Evra is dead on his feet until he hears "lunch", then pops up rubbing his hands. |
| 14.1 | The house | Evra skips up the path. |
| 15.3 | The table | A few plates. Evra looks at his food, then at Ronaldo, who is happily eating. |
| 19.3 | "Plain white chicken." | Close-up on the plate. |
| 20.4 | Waiting | Evra looks hopefully at the kitchen door. A tumbleweed rolls past the doorway. |
| 21.7 | "No juice, just water." | A glass of water slides in. Evra stares at it and sweats. |
| 23.8 | "Quickly a lunch" | Fast-forward ×8: Ronaldo clears his plate and vanishes in a cloud of dust. |
| 26.6 | The garden | "Let's play two-touch." Ronaldo flicks the ball up. |
| 29.1 | "We just finished." | Evra pleads. |
| 31.1 | Two-touch | Crisp passes from Ronaldo, a weak one back from Evra. The last ball BONKs off Evra's shin. |
| 34.4 | The pool | Ronaldo swims laps past Evra, who clings to the edge. Then Ronaldo pops up: "sauna, jacuzzi". |
| 37.0 | The sauna | Ronaldo does jump squats with a thumbs up. Evra sweats on the bench: "why didn't we stay at training?" |
| 40.3 | The jacuzzi | Evra finally relaxes, eyes closed, while Ronaldo swims laps of the jacuzzi. He splashes Evra in the face every time he passes. |
| 44.6 | "I saw the goal today" | Ronaldo scores at Carrington: GOAL, confetti, and a "SIUUU!" jump. |
| 47.4 | "Christian Dior" | Ronaldo in a bathrobe, on pink with sparkles. He winks on "playboy". |
| 50.3 | "Christian the warrior" | He is in the ready stance in red light, with dust and speed lines. |
| 52.3 | "really happy for him" | Evra in a robe, beaming. |
| 53.9 | "He's a machine" | Ronaldo does jump squats while Evra watches. Ronaldo's battery reads 100%, then "∞" on "machine". Evra's is at 2% and blinking. A rep counter runs past 997. |
| 57.0 | Table tennis | A rally with Rio, who smashes the winner past Ronaldo's ear. RIO 11 - 9 CR7. |
| 60.7 | "so close" | Ronaldo is confused. |
| 61.7 | "determined" | Ronaldo, intense, on a sunburst. |
| 63.4 | "Rio has to tell the truth" | Rio shrugs and sweats. |
| 65.5 | "Rio beat him" | The smash goes past again. Rio folds over laughing: RIO WINS. |
| 67.4 | "we scream" | Evra and Rio crying with laughter: HAHA. |
| 68.6 | "so angry" | Ronaldo turns red, with steam coming out of his ears. |
| 70.3 | The cousin | A box marked TABLE TENNIS / FRAGILE drops on the path. Ronaldo is delighted. |
| 72.5 | "Two weeks later" | At night, Ronaldo practises alone, very fast. |
| 73.8 | The rematch | From behind Rio: Ronaldo smashes it into the back of Rio's head. BONK! CR7 WINS. |
| 76.0 | Rio | Arms folded, with a rain cloud of his own. |
| 76.9 | "That's Cristiano Ronaldo" | Ronaldo winks on a red-and-gold sunburst: CR7. |
| 78.1 | "He don't want to lose any game" | Back at Carrington, Ronaldo is still doing keepy-ups and beckoning. Evra keels over flat: K.O. |

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
- `render.py`: renders in parallel chunks, then adds the original recording, encoded once to AAC 320k, with no edits.

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

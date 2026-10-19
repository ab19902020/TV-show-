# The Office: "Anonymous Feedback"

**Final video:** [`anonymous_feedback.mp4`](anonymous_feedback.mp4) (1920×1080, 25 fps, about 1:40, the Clony AI voices)

An original fan sketch with David Brent, Gareth Keenan and Tim Canterbury, made from [`BRIEF.md`](BRIEF.md). Brent brings in
an anonymous suggestions box to look approachable on camera. Gareth has numbered the slips and kept a list of who had
which number. The first suggestion is "Fewer meetings". Dawn, Finchy and Neil are silent extras walking past.

The voice scripts for Clony AI are in [`voiceovers/`](voiceovers/): one file per line, and one per character with all
of that character's lines. The three recordings are `src/brent.mp3`, `src/gareth.mp3` and `src/tim.mp3`.

## What happens

| Time | Shot | What you see |
|---|---|---|
| 0.0 | Car park | The office block from the car park. Neil walks in to work. |
| 3.0 | The office floor | Dawn crosses at the back, Finchy walks through the middle, and a phone rings two desks away. |
| 7.0 | 01 Two-shot | Tim stops typing. Brent presents the box on Gareth's desk (B01), with a pleased glance at the crew on "management". Gareth straightens. |
| 13.6 | 02 Interview | Brent: "People can be completely honest with me…" On "Obviously" he folds his arms. After "having a go" he smiles for agreement, and nobody gives it. |
| 25.5 | 03 Two-shot | Gareth taps his notebook: "I've numbered the slips." Tim turns only his eyes. |
| 31.7 | 04 Tim | "So what makes them anonymous?" |
| 35.5 | 05 Gareth | "No names on the actual slip." He looks down at the pad, satisfied. Dawn walks past behind him. |
| 41.4 | 06 Brent and Gareth | Brent leans into the box and comes up with the slip. "Right. First one. 'Fewer meetings.'" His smile drops, then comes back on "Constructive". The camera creeps in on "Who put that?" |
| 49.1 | 07 Tim | "I thought we weren't meant to know." Finchy passes behind him. |
| 53.6 | 08 Brent | "We aren't…" He holds the slip up for "It's a good suggestion", then looks from Tim to Gareth with suspicious eyes. |
| 60.6 | 09 Gareth, Tim, Gareth | "Number four. Tim." The cut comes on the turn. Tim: "Could you put 'stop Gareth keeping a list' on mine as well?" Gareth is already writing: "That'll need a separate slip." Tim exhales off screen. |
| 72.4 | 10 Two-shot | Brent folds the slip once, neatly. Gareth stops writing. Tim folds his arms during "Tell you what… after lunch…" |
| 80.1 | 11 Tim, then Brent | "In a meeting?" Then Brent: "Not a meeting. A chance to speak freely." His chin goes up. |
| 87.0 | 12 Two-shot | Gareth raises the pen: "Is it compulsory?" "Yes." Tim looks at Brent, then at the box: "Can we vote on that anonymously?" "Yeah. Show of hands." Nobody moves. |
| 95.6 | Tim | His eyes go to the lens, with a very small, exhausted half-smile. Hard cut to black. |

## Staging

- Tim sits LEFT and Gareth sits RIGHT. Brent stands behind the desks at Gareth's right, mirrored so that he faces in
  towards them. He is mirrored in every shot, so his hair never flips between cuts.
- Tim and Gareth sit squarely in their chairs. Each one is placed by the middle of his body, set on the middle of his
  chair (measured from the blue upholstery), so every drawing of him stays in the seat. Gareth stays in the upright
  seated drawing throughout, with his biro in his right hand.
- The seated men are hidden by the desk below the desk top's far edge, except for their hands, which rest on the desk.
  The hand cut-out follows the hand's own ink line, so none of the trousers the hands rest on in the drawing shows.
  Brent stands, so he is hidden below the desk edge.
- Set changes (in `sets.py`):
  - The two-shot desks have full modesty panels, so seated legs are hidden by the desk, not cut off.
  - Gareth's desk is cleared for the box and his notebook. His monitor came off it, so it does not hide Brent; the
    cabinet and tray behind it are rebuilt.
- The documentary camera drifts slowly by hand and never shakes. The interview is on a tripod. There is one small
  push-in, on "Who put that?".

## How it's made

| File | What it does |
|---|---|
| `prep.py` | Cleans every drawing from the Office Animation Collection and upscales it 4× (Real-ESRGAN anime). The drawings come in at 99% opacity, so it makes them solid, drops the sheet labels that came with the walk and view cut-outs, and stops dark edges forming. |
| `align.py` | Force-aligns each recording to the script with pocketsphinx and cuts it into the brief's line IDs, B01–B08, G01–G05 and T01–T05 (`phones.json`). |
| `face.py`, `cast.py` | Live faces on the whole-body pose drawings. The pupils are repainted wherever a character looks (at Brent, at the box, into the lens). Lids drop for blinks and for suspicion. The drawn mouth line is replaced by a cartoon mouth shaped by each sound, opening wider when the voice is louder. Closed sounds (M, B, P) stay shut for at least two frames. |
| `sets.py` | The plates, the set changes, and GrabCut masks for everything in front of the actors: monitors, phones, pen pots, the chairs the extras pass behind. |
| `props.py` | The shoebox with its slot and hand-lettered label, the slip ("Fewer meetings", in handwriting), Gareth's pad and biro. They are drawn flat in the house style and held at the drawings' hand points. |
| `direction.py` | The edit and the acting, keyed to spoken words, for example `w("B03", "constructive")`. A cursor places each shot after the last, so changing a pause moves everything after it. |
| `render.py` | Composites each frame: the plate, the extras, the actors, the desk objects, the props, then grain and a soft vignette. Poses swap on a frame and the body eases into the new drawing, so nothing is ever see-through. The extras walk the 8-frame cycles, sized for where they are in the room. |
| `sound.py` | The dialogue from the three recordings, levelled per character and given a touch of room. All other sound is procedural: mains hum and air conditioning, distant keyboards, a phone, paper, pen taps and scribbles, a chair creak, carpet footsteps, Tim's exhale, and the car park. There is no music and no laugh track. The sound stops dead with the cut to black. |

To rebuild:

```sh
pip install -r ../jim-ratcliffe-ineos-office/requirements.txt pocketsphinx scipy
mkdir -p models && curl -sSL -o models/RealESRGAN_x4plus_anime_6B.pth \
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth
for b in src/art/bg/*.png; do python3 upscale.py $b build/up/$(basename $b) RealESRGAN_x4plus_anime_6B; done
python3 prep.py && python3 align.py && ./render.sh
```

To review:
- `python3 render.py --stills out.jpg 9.5 44 97` gives frames at those times.
- `python3 render.py --run out.jpg T0 T1 [step]` gives consecutive frames.
- `./render.sh clip 13.6 25.5 out.mp4` renders a section with its sound.

Fonts: Permanent Marker (Apache 2.0) for the box label, and Reenie Beanie (SIL OFL) for the handwriting. Both are in
`fonts/` with their licences.

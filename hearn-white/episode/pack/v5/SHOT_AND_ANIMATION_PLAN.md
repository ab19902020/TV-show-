# Shot and movement plan — 228-second target

Use this as the director's blocking plan. Convert to final frame cues after audio alignment. Each row contains multiple shots; do not render it as a single static panel. Speaker timing comes from REVISED_SCRIPT.md and actual voices, not these approximate bounds.

| New time | Shot sequence and physical acting | Camera / asset use | Sound / edit purpose |
|---|---|---|---|
| 000–007 | Tape closeup -> Eddie steps back admiring ban poster; tape clings to cuff | Existing press plate; hand insert, then medium Eddie | Tape peel; title over action 2 sec |
| 007–020 | Guard looks poster-to-Eddie; Eddie demonstrates banned person's appearance, guard deadpan | Motivated two-shot, single guard reaction | Hold guard's question, Eddie dismissive reply |
| 020–026 | Dana studies staff door; attempts collar adjustment as disguise, gives up | Loading bay medium; one eye closeup | Low distant crowd and loading hum |
| 026–040 | Dana follows trolley, attendant brakes; offer -> she turns -> he removes shoes | Low wheel/feet insert; medium attendant/Dana | Brake/clunk; pivot on five-hundred offer |
| 040–048 | Cramped bin interior, shoes and linen; lid closes; guard approaches | Construct inside-bin insert from old trolley/towels/Dana; use dark backing | Muffled dialogue perspective; cloth rustle |
| 048–054 | Guard question; Dana interruption; attendant presses lid and stares guard down | Reverse corridor; close eye reaction | Leave uncomfortable pause before permission |
| 054–061 | Wheel/ramp -> brace -> hand slip -> tumble -> landing -> shoes slide | Low tracking, ramp insert, wide readable fall; avoid mid-trajectory axis change | Wheel knock, lid, cloth, shoe, restrained impact |
| 061–073 | Fury steps back then leans down; Dana searches shoes, Joshua walks into eyeline | Low Dana POV makes Fury tall; reaction cut Joshua | No extra music over Fury punchlines |
| 073–088 | Eddie stops at loose shoe -> sees bin -> recognises Dana; Dana gets up -> attendant asks payment | Alternate corridor view, Eddie closeup with new head, medium transaction | Payment cue and Eddie silent resentment |
| 088–103 | Eddie points exit, Dana steps close, Eddie bluffs; both regret it | Two-shot; individual 0.6-second reactions | Silence after Fine; audible room tone |
| 103–123 | Jacket removal, glove strap, failed phone use; Fury/Joshua watch | 3 preparation inserts then spectator two-shot | Strap tightening; don't turn all dialogue into montage narration |
| 123–131 | Crowd bridge -> arena wide -> promoters awkwardly duck under ropes | Existing arena plate and new corner angle; rope mask layers | Fanfare, crowd swell, canvas steps |
| 131–145 | Announcer foreground; Eddie false confidence; Dana towel retrieval; ref checks gloves | Announcer medium; Eddie reaction; Dana+attendant insert | Ceremonial delivery straight; towel rustle |
| 145–150 | Ref instructions, Eddie genuinely concerned | Tight triangular staging, no line of waiting characters | Ref stern, Eddie quick response |
| 150–156 | Bell; both bounce -> Dana tires -> Eddie quietly stops too | Medium wide held camera, characters moving | Fanfare cuts; a cough in crowd |
| 156–165 | Fury shout -> jab probe -> overduck -> glove tap -> outraged Eddie | Side view establishes; one dodge closeup then wide contact | Foot scuff, soft glove pop; no star on every jab |
| 165–181 | Dana advances with real steps; Eddie backpedals; rope catches back; recoil into clinch | New oblique corner, side view contact, rope insert | Rope creak, shorter breath; eyelines follow |
| 181–194 | Clinch sags; Dana accusation; Eddie excuse; ref pulls at shoulders; load-bearing line | Tight two-shot plus referee hands, spectator response | Breath and cloth; silence after load-bearing joke |
| 194–205 | Separate, overcommit simultaneously, gloves collide, knees buckle, both sit; hold look; bell; ref helps | Wide for geography; 2-frame impact emphasis; close exhausted look | One graphic impact, seated thump, bell |
| 205–219 | Decision; both instantly pitch rematch; Joshua/Fury reaction; promoters exit down steps | Announcer/contenders; seated reaction; steps insert | Arena bed reduced for final spectator line |
| 219–228 | Bin outside apron; fare card; Dana stunned; attendant deadpan; Eddie impressed; Dana climbs in | Attendant/Dana medium with bin contact, exit tracking | Wheel squeak; title final 2 sec |

## Movement construction details

### Walk and trolley
Use roughly 12–16 animation frames per step at this comic pace, adjusted to travel distance. Contact/down/passing/up are meaningful body positions, not arbitrary asset indices. The new attendant sheet still has similar first contact extremes; use its crouch/brace and arm positions to build a rig rather than loop all cells uncorrected. Foot lock requires world-space anchor during stance. Raise toes before heel contact; push off trailing foot before it lifts. Pelvis/torso follow the feet with small delay. Hands are inverse-kinematic targets at trolley handle; fixed target means wrists cannot drift when shoulders bob. Trolley and Dana sway independently with cloth settling after turns.

### Fall trajectory
Show ramp before tumble. Keep Dana centre moving along one arc across shots. Gravity accelerates downward travel; don't ease to a stop in mid-air. He reaches out before impact, crumples through knees/elbows and settles. Use old airborne/sprawled illustrations as extremes, new rig for linking frames. Do not scale Dana arbitrarily between airborne and floor pose. Shoe slides to a stop on floor; shadow travels beneath it. Towel follows later than body, catches head, then settles. Fury's weight moves away from collision; his reaction is embodied.

### Jab and counter
Working starting timings at 24 fps: anticipation 4–6 frames, extension 3–5, contact 1–2, recoil 4–6, recovery 6–10. Vary timings by character and gag; do not hardcode one duration for every attack. One jab may be tentative and much slower. Red glove taps blue guard; reaction begins after visible contact. Shoulder/hip rotate but head remains believable. Dana ducks by bending knees/hips, not sliding head downward through torso. Eddie retreat uses steps plus a lean; feet remain above canvas.

### Clinch
Use two-person support silhouette, Eddie taller and leaning down, Dana braced. Left/right forearms need explicit front/back order. Red glove can sit across Dana's upper back; blue glove against Eddie's shoulder. Avoid invisible hands inside necks. Do not show both men leaning away from one another while claiming load-bearing support. Ref separates shoulders slowly; both try to remain close. Body sag sells exhaustion beneath speaking heads.

### Final collapse
Double punch is a mutual miss/glove clash, not unexplained knockout. Each fighter's knees buckle and hips land. Sit with legs planted forward, arms hanging. Dust/impact optional, subtle. Hold their awkward look about 12–18 frames. Ref helps them stand across an insert, then decision scene. No gore, flashing collision or violent head compression.

## Face and secondary movement checklist

Listener attention changes on an actual event, not randomly. Use eye dart -> head turn -> torso follow. Smugness becomes embarrassment as shoulders drop. Animate a breath in chest/shoulders while mouth remains still. Blinks can punctuate disbelief but not cover every punchline. A sweat bead is one small layered accessory, not permanently painted across all heads. Mouth rotation and scale follow head; pupils remain inside eyelids; brows above eyes. Empty speech pauses use closed slit mouths.

## Internal acceptance checks before final preview

| Check | Pass condition |
|---|---|
| Runtime | 223–233 sec, preferably ~228; voices natural speed |
| Trolley | Feet step, hands contact handles, wheels rotate and stop coherently |
| Fall | Cause shown, arc continuous, floor impact/recovery readable |
| Fight | Five distinct beats; actual footwork, contact, recoil and mutual support |
| Faces | Stable proportions, no double heads, tracked eyelines, synced mouths |
| Ring | Correct rope layering, planted feet, bin outside apron, steps on exit |
| Camera | Purposeful composition changes, held camera during acting, no constant drift |
| Audio | All spoken words audible, cues not spoken, Foley on contact |
| Render | No black/opaque portrait rectangles, missing assets, unintended sheet margins |

Do not treat these as unit tests that mirror implementation. Inspect movement tests and the whole rendered preview visually and audibly.

# Boxing Toon pilot — v5 upgrade handoff

Claude: improve the EXISTING project that produced The_Undercard_PREVIEW_720p_v5_share.mp4. This is an upgrade pack, not a replacement engine. Do not start a new generic slideshow. Keep the established 2D caricature style, identities and central story: Hearn bans White from the fictional Fury–Joshua event, White enters by laundry trolley, the promoters become the extra fight. Treat all dialogue/event claims as invented satire.

Baseline duration is 227.776 seconds. Revised target is 228 seconds, with 223–233 seconds acceptable after real performance timing. The user wants the same approximate length. More speech must replace weak holds and repetition; it must not erase physical comedy. Deliver a visibly better pilot, not a cosmetic upscale.

## Read these in order

1. PREVIEW_REVIEW.md — visible problems grounded in the supplied preview.
2. REVISED_SCRIPT.md — replacement dialogue and action, with performance cues.
3. SHOT_AND_ANIMATION_PLAN.md — timed scene/shot intentions and physical execution.
4. ASSET_INVENTORY.md — actual new artwork, constraints and use.
5. VOICE_LINES/ — separate revised actor texts.

The new PNGs were generated with built-in image generation using the original episode character sheets and venue plates as references. Exact prompts are included in IMAGE_PROMPTS.json. New parts are illustration sources; inspect, register and prepare them before rigging. They are not already rigged or automatically fitted to your engine.

## Full instruction to Claude

You are the episode director and animation implementer. Inspect the existing source project and the v5 render before modifying it. Find its scene timeline, renderer, character asset loader, mouth system, camera system, sound mix, video encoding and current render command. Preserve working code and assets; extend them. Record the exact baseline revision before changing it. Do not assume assets are missing until you inspect the project. Do not claim you inspected a repository you cannot access. This ZIP does not contain the user's repository or rendered project.

Create one central timeline in seconds/frames, with scene IDs and actor/action cues. Use recorded dialogue durations to set events. Keep the revised scene order and budget; retime action around delivery, not by stretching voices. Reuse unchanged recorded words only if performance fits. Changed wording needs fresh recording; never splice mismatched old speech under new mouth timing. If final voices are unavailable, generate a clearly labelled temporary animatic with the existing permitted voice workflow, then provide the exact revised lines for replacement.

### Make characters act

Every character needs intention, eyeline and physical response. Eddie controls the room until he loses control; Dana wants to look powerful even while climbing into linen; the attendant sees an inconvenient customer; Fury and Joshua watch increasingly absurd behaviour. Write actions for the listener as well as the speaker. Small listening actions include eye shifts, head turns, breathing, posture change, glove adjustment, checking a shoe, leaning back and suppressing amusement. Do not make everybody bounce or blink together. Stillness is allowed when motivated; a held pose plus camera drift is not sufficient acting for an entire exchange.

Prefer articulated puppet animation for repeat movement, with pose replacements for strong comic extremes. Separate head, eyes, brows, torso, pelvis, upper/lower arms, gloves/hands, thighs, shins and boots. Use rounded hidden joint coverage and pivots derived from artwork. Fit new boxing parts to the existing character model before replacing anything. The generated parts are starting points; labels/layout alone do not guarantee compatible scale or joint shapes. Finish overlap seams and clean residual paint. Preserve original likeness. Do not squash a complete head to represent reaction. Do not rotate the full figure to imitate walking.

For dialogue, torso weight shifts precede gestures; wrists trail elbows; gestures settle and remain readable. Use three or four purposeful gesture changes over a sentence, not random swaps on every syllable. Hand-to-prop contacts stay fixed in prop space: trolley handles, gloves, microphone, towel, payment. Move both the actor and object through their shared contact constraint. Fingers must not float next to a mic.

### Solve locomotion

The attendant/trolley sequence is a priority. Match travel distance to step length. Contact foot holds world position until lift; knee and hip absorb weight. Opposite foot passes through before next contact. Animate pelvis rise/fall mildly, not head compression. Wheel rotation uses travel distance divided by wheel radius; caster angle follows direction. When trolley stops, attendant braces, body overshoots slightly, towels settle and Dana shifts inside. Don't translate a permanent pushing pose for ten seconds. The new attendant poses are reference extremes; rig/interpolate and create additional frames as needed.

Dana's fall is a causal chain: front caster catches cable ramp -> trolley tilts -> towels shift -> lid opens -> Dana reaches rim -> hand slips -> body rotates -> shoulder/hip lands -> towel follows -> shoe skids -> recovery. Allocate readable screen time to cause, anticipation and reaction. Floor contact shadows remain under the grounded body. Each extreme follows a continuous trajectory. Do not switch from standing to sprawled with no path. Dana may exaggerate body motion, but head proportions and identity stay stable.

### Choreograph the boxing

Use a shared ring coordinate space with known corner and rope positions. Eddie generally left/red, Dana right/blue. Keep screen direction through the primary action; reverse only with an establishing view. Don't let a closeup silently swap fighters' positions. Each punch has guard, anticipation, planted weight transfer, extension, contact/miss, recoil and recovery. Hips/shoulders rotate before or with extension; glove follows an arc rather than constant-speed straight slide. Retract the arm after contact. Back foot may pivot but does not drift through canvas. Backpedalling needs actual steps.

Design the round as five different beats: ceremonial confidence; tentative probing; indignation at harmless glove contact; retreat/rope recoil into clinch; simultaneous failed finish. They become tired because they have moved, not because the sprite suddenly changes. Accumulate smaller stance, slower recovery and heavier breath. The clinch is two people physically supporting each other: forearms overlap shoulders, bodies lean into shared centre, feet resist collapse. Draw a connecting clinch if new parts cannot produce it cleanly. Referee approaches with hands ready and separates them by contact. Rope recoil deforms the touched rope locally and returns after Eddie leaves it.

Avoid covering poor contact with constant starbursts. One small graphic impact at the final glove collision is enough. Use one- or two-frame impact holds where useful; maintain readable movement before/after. No gore or injury fetish. Boxing boots and glove colours remain consistent. End seated collapse should show knees buckling, hips descending, feet stabilising and bodies settling. Recovery uses referee assistance, not an offscreen teleport to victorious standing.

### Direct camera and staging

Aim for approximately 40–50 purposeful shots across 228 seconds, including short inserts. This is a planning range, not a quota. Longer acted two-shots are better than arbitrary cutting. Establish room geography once, then use distinct compositions: wheel insert, inside-bin POV, Dana over-shoulder, Eddie reaction, low floor reveal, oblique ring corner, rope detail, Fury/Joshua reaction. A cropped wide is useful occasionally; it is not a substitute for every closeup. Keep each face large enough for eyes to read. In dialogue two-shots, separate silhouettes and avoid background actors sitting on the speaker's shoulder.

Default camera holds while actors move. Track only when motivated by travel or discovery. Put jokes in the framing: a tiny Dana below a massive Fury; a ceremonious announcer while Dana loses the towel behind him; exhausted promoters with disappointed crowd beyond. Use the new oblique ring background to break side-on sameness, matched by character body turns/scale/perspective. Never place side-profile standing figures at a contradictory angle. Flat plates can be split into wall/floor/foreground layers for small parallax; do not animate a single flattened crowd plate as if individual people are alive.

Fix ring depth: far ropes behind fighters, near ropes in front, separate posts, canvas under feet. When outside ring, put fighters below apron height and use steps. The laundry trolley waits on venue floor, not on canvas, for the final price gag. Preserve chair contacts for seated Fury/Joshua: hips on seat, boots on floor, elbows on thighs. Clean unused chairs from sprites if necessary.

### Faces and mouths

All supplied character source faces have closed mouths/slits, per user request. Mask the resting slit and replace during speech with the existing phoneme system. Use actual word/phoneme timings from recorded voices, ideally existing Whisper alignment. Never toggle vowels uniformly. Mouths close during pauses, have consonant closures and do not open on silent reactions. Retain beard around Eddie/Fury's lower face; anchor mouth to head transform. Check side and three-quarter view anchors independently. Enlarged expression heads give better closeups; register them at the same neck/head pivot and preserve scale. Eyes must track partners, trolley, money, ref and audience as appropriate. Blink lids replace/cover eyeballs rather than shrink eyes into brows. Avoid identical eyelid states at every cut.

### Finish the sound and light

Inspect the original mix; this review does not claim an audio audit. Keep dialogue clear and performances distinct. Foley follows contact: wheel squeak, caster/ramp knock, lid hinge, towel rustle, shoe landing, tape peel, glove straps, ring canvas steps, bell, rope creak and breaths. Use clean room tone between lines. Arena sound should change with location and camera perspective; under dialogue it remains low. No repeated whoosh on every transition. Fight fanfare stops when awkward reality becomes clear. Crowd reacts to specific surprises, then settles. Don't place canned laughter after every sentence.

Moving arena beams and mild crowd motion can add life, but don't obscure faces or change mouth colours. Characters inherit a subtle edge light from red/blue corners and a canvas contact shadow. Backstage is warmer, arena cooler. Layer haze sparsely. No global strobing or constant camera shake. Two-frame impact movement is enough for a boxing gag.

### Build and review

1. Build revised animatic and time real voices against the 228-second target. Remove redundant lines before compressing action.
2. Finish the hardest movement tests in project: 8–12 seconds of attendant/trolley/fall, and 10–15 seconds of attack/retreat/clinch. Inspect internally, then reuse validated rigs in full episode. Don't complete a full expensive render around broken movement.
3. Render full 720p preview. Watch every frame transition and listen to every line. Check missing assets, doubled heads, foot sliding, inconsistent scale, detached mouths, props, rope order and joke pauses.
4. Deliver preview plus exact source revision, assets, timing data and render instructions. Final 4K follows user approval. A 4K canvas does not increase detail in small source cells; use the larger head assets for closeups.

The user authorised major improvement, extra assets, dialogue changes and small edits to length. Proceed with implementation inside that scope. Do not stop after writing a plan or simply adding effects. Do not use Runway. Do not declare the pilot world-class without a rendered result that demonstrates the movement and acting. This pack itself supplies direction and assets; it does not claim to be the upgraded MP4.


---

# Visual review of the supplied v5 preview

Reference file: The_Undercard_PREVIEW_720p_v5_share.mp4. Container duration 227.776 seconds; 1280×720 H.264 video with AAC audio. Review used frames across the episode and denser temporal sampling of the fall and fight. This is a visual review; existing spoken wording and audio mix were not independently transcribed or audited here. Use the source audio/project for exact voice and sync assessment. Times below are approximate locations in v5, not new edit timecodes.

| v5 location | Visible issue / opportunity | Required change |
|---|---|---|
| 00:00 | Static title precedes story | Open on Eddie physically taping ban poster; title over action |
| 00:08–00:20 | Pose/hand changes communicate dialogue but torso/feet remain presentation-like | Eddie fights tape, guard checks poster, varied eyelines; action continues under speech |
| 00:24–00:35 | Dana alone in repeated standing composition | Make his decision visible: staff door observation, aborted disguise, trolley approach |
| 00:40–00:53 | Attendant is a pushing illustration travelling with trolley; feet remain in a strong held pose over substantial movement | Independent walk cycle, hand locks, wheel rotation, stop/start weight transfer |
| 00:53–00:58 | Dana emerges and fall moves quickly between extreme poses | Show ramp/wheel contact, hand slip, airborne turn, ground impact, recovery; keep blocking consistent |
| 00:58–01:15 | Towel/floor reaction uses static poses and closeups | Dana retrieves shoes, Fury steps back then leans in, Joshua arrives into scene |
| 01:16–01:48 | Characters arranged together in corridor; limited action changes while conversation continues | New reverse corridor angle, Eddie crosses floor, physical towel/payment business and moving eyelines |
| 01:52–02:23 | Arena reveal / introductions use familiar wide and zoomed compositions | Rope entrance, glove check, practical lights, announcer blocking, towel removal; red-corner angle |
| 02:24–02:55 | Guard stances recur between small groups of pose changes | Design distinct attacks with anticipation, hip transfer, foot planting and recoil; stop idle repetition |
| 02:56–03:09 | Exhausted pair mostly lean alongside one another | Actual interlocked clinch with load-bearing gag, correct arm occlusion and referee approach |
| About 03:12–03:20 | Punch/star effects and fall extremes can carry stronger spatial continuity | Glove-to-glove final collision, knee buckling, matched seated landing, grounded recovery |
| 03:20–03:47 | Result and trolley callback occur around ring composition; opportunity to clarify how trolley reaches characters | Promoters leave through ropes/down steps; bin waits outside apron; end on attendant's new price |

The strengths worth keeping: recognisable consistent caricatures, red/blue gloves, readable ban poster, laundry premise, Fury/Joshua as spectators, arena lighting palette, a complete beginning/middle/end. Upgrade the animation and shot design around these rather than replace the style.

Priority order: (1) physically coherent acting and fight; (2) shot-specific compositions/reactions; (3) sharper script recorded with distinct performances; (4) precise mouths/eyes/props; (5) sound and light finishing. A higher-resolution export alone will not solve held-pose acting.


---

# BOXING TOON 01: THE UNDERCARD — revised performance script

Fictional satire; invented event and dialogue. Target 228 seconds, matching the supplied 227.776-second v5 preview. Keep landscape composition and existing cast. Re-record changed lines; existing recordings may be reused only where wording matches. Brackets are performance direction, not spoken words. Never speed voices up to cram the script in. Timing blocks include action and pauses and must be checked against actual recordings.

## 00:00–00:26 — Eddie's ban

Start on Eddie firmly taping Dana's ban poster to a wall. Tape sticks to his cuff; he quietly fights it while maintaining his grand manner. No long opening title. Series title overlays the first moving shot for two seconds.

EDDIE [confident, presenting]: Fury. Joshua. The biggest night in boxing. And I've already improved the undercard.
SECURITY [flat]: Who've you added?
EDDIE [pleased]: Nobody. I've banned Dana White.
SECURITY: What if he comes in disguise?
EDDIE [dismissive]: Bald head. Furious. Looks like he's arguing with a parking meter. You'll know.

Cut to outside. Dana watches a staff member pass through the service door. He adjusts polo as if it is a disguise, immediately abandons this idea.
DANA [offended]: He banned me? I wasn't even coming. Now I'm fucking coming.

## 00:26–00:54 — Laundry infiltration

Attendant pushes trolley into shot; Dana sidesteps alongside it. Show wheels and feet in a tracking insert. She brakes the trolley before he can climb in.

DANA [businesslike]: Can you get me inside?
ATTENDANT [without looking]: Staff entrance.
DANA: I'm banned.
ATTENDANT: Then no.
DANA [quiet offer]: Five hundred.
ATTENDANT [instant decision]: Shoes off. Don't sit on the clean ones.
DANA [insulted]: Do you know who I am?
ATTENDANT: Yes. That's why it's five hundred. Towels go in free.

Dana lifts one shoe; balances badly; hurriedly takes both off then retrieves them into bin. Brief inside-bin insert: cramped Dana between towels, holding shoes. Close lid.

SECURITY [looking down]: What's in there?
ATTENDANT: Towels.
DANA [muffled, unable to resist]: The best towels in the fucking business.
ATTENDANT [hissed through lid]: Shut up. You're a towel.

Security looks from trolley to her face. She holds stare. He gives way.

## 00:54–01:28 — The delivery

Trolley wheel catches cable ramp. Show the cause BEFORE the fall: wheel hits, attendant's planted foot braces, towels shift, lid opens, Dana tries grabbing rim, misses, tumbles and lands. No instant pose teleport. Shoes spill beside him. Fury steps back to avoid collision. Dana retrieves shoes while dialogue plays.

TYSON [casual surprise]: Fuck me. They've delivered a promoter.
DANA [dignity dented]: Help me up.
TYSON [reading imaginary label on towel]: Forty degrees. No tumble drying.
JOSHUA [arriving, looking down]: Is he on the card?
TYSON: No. He's on the floor.

Eddie enters, sees shoe, towel, bin, then Dana. Hold the recognition before speaking.

EDDIE [low disbelief]: Why is Dana White in my laundry?
DANA [stands too fast, regains balance]: Your security's shit.
EDDIE: You're wearing a pillowcase.
DANA: And I'm still inside.
SECURITY [offering explanation]: In my defence, the poster didn't mention laundry.
EDDIE [staring]: It didn't mention fucking parachutes either.
ATTENDANT [hand out]: Five hundred.

Dana pays reluctantly. Eddie watches, offended that someone else made money.

## 01:28–02:03 — The challenge and preparation

EDDIE [controlled]: Out. Before you turn my main event into an argument about cage sizes.
DANA [steps close]: Put me in the ring. Throw me out yourself.
EDDIE [blurts bluff]: Fine.

Both realise what they agreed. Two short reaction cuts, then glove-prep montage under dialogue: jacket off; Dana's glove strap tightened too hard; Eddie discovers he cannot use phone in gloves.

EDDIE [rapid, covering panic]: Bigger gloves. Shorter rounds. No elbows. No wrestling.
DANA: It's boxing, Eddie.
EDDIE: Good. We're both equally unqualified.
DANA [mocking]: What happened to the biggest night in boxing?
EDDIE [fast recovery]: Still is. You being punched improves any evening.
DANA: By you?
EDDIE: That's the part I'm reconsidering.
JOSHUA [quiet, to Fury]: Shall we stop this?
TYSON [eyes still on them]: And miss two promoters working for their money?

## 02:03–02:30 — The additional contest

Sound bridge crowd into arena reveal. Announcer enters foreground; promoters duck through ropes awkwardly in background, referee checks gloves. Never stand everyone in a line waiting for dialogue.

ANNOUNCER [serious sports ceremony]: Ladies and gentlemen! A special announcement! One additional contest has been added to tonight's card!
ANNOUNCER: In the red corner… a man desperately checking whether this counts as expenses… Eddie Hearn!
ANNOUNCER: And in the blue corner… entering by laundry delivery… Dana White!

Dana lifts blue gloves. Attendant reaches through ropes to remove a towel from his shoulder; he tries to wave her away, but cannot grasp it with gloves.

REFEREE [stern]: No holding. No wrestling. No negotiating.
EDDIE [genuine concern]: During the round, or generally?

## 02:30–03:25 — One disastrous round

Bell. Both bounce confidently for two beats. Dana slows first; Eddie notices and also stops. Crowd expectation, then silence. Camera must observe this, not fill it with dialogue.

TYSON [shouting from seat]: Go on! It's not a fucking podcast!

Eddie probes with a long jab. Dana overreacts, ducks and peers up. Eddie's second jab taps blue glove guard; Dana counters into red gloves. Eddie is insulted by any contact.

DANA [mocking, after the missed probe]: Your jab's shit.
EDDIE [defensive]: It's an opening offer.
DANA: Put your hands up!
EDDIE: They are up!
DANA: That's your chin.
EDDIE: It's a very important chin.

Dana's counter meets Eddie's raised gloves; Eddie still takes it personally.

EDDIE [indignant]: You actually hit me!
DANA [obvious]: It's a fight!
EDDIE: I thought we'd do the photos first!

Dana advances with three short steps and two distinct punches; Eddie backpedals and catches himself on ropes. His attempted counter misses; elastic recoil pushes him forward into accidental clinch. They remain visibly holding each other up, not merely leaning side by side. Ref approaches to separate them.

DANA [breathing hard]: You're tired.
EDDIE [breathing hard, inventing excuse]: I'm building anticipation.
DANA [whisper, proposing]: Call it a draw. Sixty-forty.
EDDIE: Who gets sixty?
DANA: Me.
EDDIE [summons last energy]: I'd rather take another punch.

Dana lifts glove an inch. Eddie immediately retreats into clinch.

EDDIE [quick correction]: Fifty-fifty. That's my final offer.
REFEREE: Break!
EDDIE [urgent, to ref]: Don't. He's load-bearing.

Cut Joshua then Fury; one small body reaction each.

JOSHUA: They're holding each other up.
TYSON: First partnership either of them's made without a lawyer.

Separated, they both attempt an enormous finish, collide glove-to-glove, wobble and sit down at the same time. Hold exhausted eye contact. Bell. Ref helps them up in quick insert rather than teleport to standing.

## 03:25–03:48 — Decision and series button

ANNOUNCER [trying to stay professional]: After one round… a draw!
EDDIE [immediate sales mode despite exhaustion]: Unfinished business. Rematch.
DANA: Pay-per-view.
JOSHUA [to Fury]: Are we still fighting?
TYSON: Apparently we're supporting the towels.

Attendant rolls bin up outside ring apron as promoters exit down steps, not directly into ring. Dana puts a hand on rim. She slaps a handwritten fare card onto bin; add lettering in engine, not image.

ATTENDANT [deadpan]: Return journey's a grand.
DANA [outraged]: You said five hundred!
ATTENDANT: That was before you were pay-per-view.

Hold Eddie's delighted recognition: she negotiated better than both of them. Dana crawls into bin. Wheel squeak. End title over departing trolley for final two seconds; no extra verbal gag.

## Recording and edit notes

Eddie: polished pitch turning into brittle offence and quick improvisation. Dana: clipped confidence interrupted by physical embarrassment. Fury: relaxed amusement, not constant shouting. Joshua: grounded disbelief. Attendant: no wink at audience; she wants payment and clean towels. Referee: professional impatience. Announcer: treats ridiculous contest as real ceremony.

Do not give every line the same pause. Leave recognition beats before punchlines and room after them. Cut redundant dialogue if actual voices exceed scene targets; preserve physical beats and the ending. First trim candidates: Eddie's expense introduction, Joshua's partnership setup, or one negotiation condition. Final runtime target 223–233 seconds; 228 preferred.


---

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


---

# New assets and integration notes

Nine new PNG source sheets/plates supplement the existing v5 project. Original assets are not duplicated in this ZIP; Claude must use the project it already rendered. Keep all originals available for comparisons. No completed animation is included.

| Asset | Actual contents | Use / preparation |
|---|---|---|
| eddie_boxing_parts.png | 4×4 construction atlas: 3 head angles, white vest torso, navy pelvis, arm segments, red gloves, thighs/shins and boots | Extract parts; register proportions; cover visible tube ends with overlapping joints. Boots/shins need fitted ankle seams |
| dana_boxing_parts.png | 4×4 construction atlas: 3 head angles, black torso/pelvis, bare arm segments, closed blue boxing gloves, shin pieces, one thigh and boots | Corrected from fingerless draft; use standalone gloves rather than forearm+glove variant. One thigh source only: duplicate/mirror and repair to fit the two legs; do not mistake extra forearm for thigh |
| eddie_acting_heads.png | 3×2, six larger Eddie portraits with closed mouths, including panic/sweat and blink | Has alpha but residual coloured haze/soft background remains around some silhouettes; mask cleanly before compositing. Suit collar included: remove collar for boxing closeups |
| dana_acting_heads.png | 3×2, six larger Dana portraits with closed mouths, embarrassment/panic/tired/blink | Has alpha but residual coloured haze remains; clean masks, preserve ear outline. Polo collar included: remove collar for boxing |
| ringside_reaction_heads.png | 3×2, Fury top row and Joshua bottom row, three head/shoulder reactions each | Has alpha with residual haze; clean edges and register on existing seated rigs; Joshua mouth is closed but fuller lips, mask for speech |
| laundry_attendant_steps.png | 4×2, eight full-body pushing/brace/gesture/towel illustrations | Transparent source extremes. First two contact poses remain similar; complete walk with rig/inbetweens, not raw cell loop |
| bg_ring_red_corner.png | Empty oblique ring angle, red post at left, broad canvas | Use to stage retreat/rope action; match character perspective and preserve near/far layering |
| bg_corridor_reverse.png | Empty reverse service hall with lift/loading door/chute | Alternate dialogue/reaction composition and exit plate |
| bg_inside_laundry.png | Empty inside-trolley POV with towels, liner and lid opening | Insert Dana/shoes centrally; foreground towels mask body; lid light narrows on closure |

This is source art, not a finished puppet kit export for a particular engine. The separated parts improve the available material, but joint overlaps, cropping, pivots, matching scale, expression registration and hidden-paint repairs remain implementation work. Do not claim sheets provide every camera angle. Side/profile reuse needs turning poses where perspective changes significantly. Generated source faces use closed mouths; lip sync is supplied by Claude's existing engine.

Resolution: construction sheets 1448×1086, portrait sheets 1536×1024, attendant 1774×887, venue plates 1672×941. Use larger portraits for closeups after masking; small fullbody-cell heads are insufficient for extreme close crops. Metadata captures source alpha mode/extrema; alpha presence alone does not certify a clean cutout. Confirm on both light and dark compositing backdrops.

The rejected fingerless Dana draft is not in this pack. Original v5 remains the identity reference. References to new visual assets in the shot plan mean these exact files; additional acting must be created with rig motion or matching drawn parts in the existing project, not falsely described as extra delivered images.

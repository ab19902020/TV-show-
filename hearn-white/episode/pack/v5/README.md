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

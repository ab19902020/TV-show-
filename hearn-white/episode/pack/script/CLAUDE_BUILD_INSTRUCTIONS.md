# Instructions to Claude — build THE UNDERCARD

Read README_FIRST.md, DIRECTORS_SCRIPT.md and IMAGE_INVENTORY.md before coding. Use the user's existing animation repository engine; ask for repository access if absent. Do not claim this ZIP contains an engine. Do not remake the visual style. All dialogue is original invented satire.

## Asset ingestion
Retain the original sheets. Extract cells to individual PNGs with transparent gutters. Inspect alpha before trimming. Normalize characters against a common body height and foot baseline; preserve cast height differences. Generated pose sheets may contain imperfect cycle continuity, so repair registration before interpolating. Do not auto-grid crop blindly if a hand crosses a boundary. Each pose needs visual inspection.

Prefer an articulated puppet for walks and boxing. Split a neutral pose into torso/head/limbs, draw hidden joints and overlapping seams, and pivot at shoulder/elbow/wrist/hip/knee/ankle. Sheets are pose references, not pre-separated puppet kits. Do not claim otherwise. Retarget expression heads onto exact head pivot. Eyes and brows should animate independently where feasible.

## Suggested assets by shot
| Scene | Background | Characters/props |
|---|---|---|
| Ban | Press area | Eddie casual, security, Dana photo graphic |
| Sneak | Loading bay | Dana casual/walk, laundry attendant, trolley and lid |
| Checkpoint | Corridor | security, trolley, towels, Dana peeking |
| Spill | Corridor low angle | Dana laundry poses, cable protector, Fury |
| Confrontation | Dressing room approach | Eddie, Dana, Fury, Joshua |
| Prep | Dressing room | Eddie/Dana boxing, gloves, bench |
| Announcement | Arena wide / ring medium | announcer, referee, both promoters |
| Fight | Ring side view | boxing poses/rigs, near/far rope layers |
| Reactions | Ringside angle | Fury/Joshua seated, separate chairs |
| Exit | Corridor | attendant, trolley, Dana laundry, Eddie |

## Source cleanup
Some generated background plates may inherit small decorative symbols or signage from the reference. Cover incidental trident/football marks with plain venue wall or equipment panels before use; this skit has no football branding. A security pose includes a trolley; use clean poses for independent trolley interaction or separate the prop. Preserve closed mouths and replace them locally during lip sync.

## Timing and motion
24 fps animation, 48 kHz audio. Align actual voices first; script durations are targets. Walks use left/right contact, down, passing and up. Feet remain on floor and slide only during intentional stumble. Keep trolley wheels on floor, rotate by travel distance and preserve handle contact. Dana's fall uses anticipation, tipping, tumble, impact and recovery with pauses at readable extremes.

Boxing at close distance: guard -> weight transfer -> extension -> contact or miss -> recoil -> guard. Use 2–3 frames for impact emphasis, but 6–12 frames for windup and 8–16 for recovery depending joke. Don't show gloves passing through faces. Blocking jab contacts gloves; no blood, injury details or aggressive head deformation. Clinch requires pair-specific arm occlusion, not two sprites pasted over each other. Draw that connecting pose if needed.

Camera: establishment, medium banter, close reaction, low trolley tracking, wide fall, medium discovery, arena reveal, fight side view, ringside reaction. Limit simulated handheld shake; fight impacts can add two-frame 3-pixel shake. Avoid continuously zooming every shot. Parallax background slightly, keep character grounds stable.

## Speech and expressions
User specifically requests slit mouth source artwork. Replace the slit only during speech; no full head swapping for phonemes. Mouth anchor follows head rotation, not torso. Use the existing AEIOU/phoneme system, create extra consonant closures if needed, and retain beard outline. Listen to the complete render to confirm every line and expression. Separate dialogue files include performance cues in brackets; remove cues from spoken words.

## Required outputs
1. Reviewable 720p MP4 with accurate voices, sound, action and all scenes.
2. Renderable project and documentation listing exact commands/dependencies.
3. Final 4K only once preview approved.

Quality gate: mouths follow audio, feet grounded, faces aligned, no duplicate heads, no accidental labels, no checkerboard baked into sprites, no missing mic, no rope-through-body, glove colours stable, main joke pauses survive edit. This asset pack is illustration plus direction; completed animation remains to be built.

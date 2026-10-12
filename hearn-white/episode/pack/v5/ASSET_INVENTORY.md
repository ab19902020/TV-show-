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

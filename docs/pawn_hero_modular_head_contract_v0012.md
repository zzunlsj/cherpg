# Pawn Hero modular head — locked modeling contract (v0.0.12)

## Source of truth
Use the PAWN HERO illustrated character sheet provided in the CheRPG chat, plus the user's later approved neutral-expression **3 parts breakdown** and **10-angle** reference sheets for items 1, 2, 3-1, 3-2. These supersede earlier human-looking sculpt experiments (v0.0.1–v0.0.10). The original illustration, not a generic photoreal human, is the design target.

## Three top-level parts
1. `PART_01_HELMET`: open and truly hollow on its underside, bilateral symmetry, no off-center ornaments, ivory stone two-band silhouette and centered pawn orb.
2. `PART_02_HAIR`: intact matching full-size pale layered/shard-like hair cap with sweeping front bang, side and rear tufts; no helmet chunks or face chunks baked into it.
3. `PART_03_FACE`: full-size bald crown, cheeks, angular chin and broad neck connector. Has detachable groups `SUB_03_01_FACE_SHAPE`, `SUB_03_02_EARS_L_R`, `SUB_03_03_EYES_FLAT_INLAYS`, `SUB_03_04_EYEBROWS`, `SUB_03_05_NOSE`, `SUB_03_06_MOUTH`.

## User constraints
- Every isolated piece retains its original assembled coordinates, not rescaled for the presentation.
- Ears belong to the face part, not to the helmet or hair, and are low-detail, symmetric, stylized.
- Face shape alone has **no** nose or ears attached; the full face assembly includes its detachable features.
- Neutral facial expression; no stern frown or grin.
- No gold crack/highlight in stone; no arbitrary decorative clipping at the hat brim.
- No realistic human ear folds or eyeball spheres. Eye details are thin colored surface plaques on the stylized stone face.
- The fitted 3-part assembly must return to the same helmet/hair/face silhouette in all directions; don't rebuild or resize modules differently for separate render views.

## Exports and review
- File naming: `pawn-head-<module>-v0.0.12.glb`, Blender source `pawn-head-parts-v0.0.12.blend`.
- Orthographic azimuth 0, 45, 90, 135, 180, 225, 270, 315 degrees, plus top and bottom, each for helmet, hair, face shape, ears and complete assembly.
- A passing build establishes geometry and export correctness **only**. Final silhouette, face likeness, collision clearance, material fidelity and Godot-ready LOD/topology require artistic review.
- The source model is independent of previous rejected human-head checkpoints. Preserve previous work for history rather than silently deleting it.
